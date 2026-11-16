#!/usr/bin/env python3
# Cyan Eclipse Routeseal — seal store, adapter provenance, receipt
# chain, metering (SPEC-ROUTESEAL sections 2-4).
# Copyright © 2026 Cyan Eclipse Technologies LLC · cetech.ai
"""State layer for the Routeseal MCP server.

Custody (RT-C5): the record store carries ONLY the section 2 field
set — task digests, candidate identifiers as presented, selected
target, stated selection reason as declared, routing-policy version
digest, declared affiliation flags, timestamps, seals, verdict +
named grammar basis. Task bodies are digested by the caller and
never enter this module. Candidate records are reduced at the door
to exactly the grammar's routing facts (id, affiliation flag,
capabilities, cost, latency) — nothing else a dispatch point
presents is retained.

Provenance (RT-C4 / RTE-REQ-012, the RT-K1 guard): a capture is
accepted only through the buyer-side dispatch-point adapter channel:
source == "dispatch-point-adapter", an HMAC attestation from the
adapter registered for that dispatch point, and a binding reference
to the dispatch event. Platform-produced traces, logs, or
observability exports — and any relay of them — are rejected, the
rejection receipted, and the dispatch caps at UNVERIFIABLE.

Aggregation fence (RT-C6): this module exposes per-record reads
only. There is no cross-operator aggregation code path.
"""
import hashlib
import hmac
import json
import os
import sys
from datetime import datetime, timezone

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import logic  # noqa: E402
import metering_journal as _mj  # noqa: E402
from licence_gate import LicenceGate  # noqa: E402

TOOL_VERSION = "0.1.0"
SERVER_ID = "eclipse-routeseal"

CLAIM = ("Routeseal seals the routing decision at the moment of "
         "dispatch — the task, the candidates the router passed "
         "over, the target it chose, and the reason it stated. If "
         "the choice diverged from your stated routing policy, or "
         "picked an affiliated target over the policy's preferred "
         "candidate, the sealed record says so, and anyone can "
         "recompute the verdict from the record itself.")

# The whole record-store field set (SPEC section 2). Nothing else is
# written into a record. (RT-C5 / RTE-REQ-005.)
RECORD_FIELDS = ("dispatch_seal_id", "task_digest", "candidate_set",
                 "candidate_set_absent", "selected_target",
                 "stated_reason", "policy_version", "policy_digest",
                 "affiliation_flags", "dispatch_timestamp",
                 "dispatch_point_id", "binding_ref", "seal",
                 "verdict", "clause", "passed_over_preferred",
                 "grammar_version", "receipt_ref")

# Candidate facts the grammar names — the only per-candidate fields
# retained (RT-C5).
CANDIDATE_FIELDS = ("id", "affiliated", "capabilities", "cost",
                    "latency_ms")

METERED_VERDICTS = ("AS-DECLARED", "DEVIATION")  # PC-8: one charge
# per dispatch seal; CANDIDATE-SET-ABSENT / UNVERIFIABLE never meter
# (RTE-REQ-015).

SEAL_BASIS = ("The record seal is an unkeyed digest over the "
              "bundle fields: it binds the record's internal "
              "consistency only. Provenance rests on the "
              "dispatch-point adapter channel at ingestion.")


def _now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def _reduce_candidate(cand: dict) -> dict:
    return {k: cand.get(k) for k in CANDIDATE_FIELDS
            if cand.get(k) is not None}


class Store:
    """JSON record store + hash-chained receipt journal + metering
    ledger (event class + count only). Fails closed: a journal that
    does not verify at load raises, and so does any record that
    disagrees with its own seal or its seal receipt."""

    def __init__(self, state_path: str, policies: dict,
                 adapter_keys: dict, licence_gate=None,
                 metering_journal_path: str = None):
        self.state_path = state_path
        self.policies = policies          # version -> policy object
        self.adapter_keys = adapter_keys  # dispatch_point_id -> key
        # ETO-44: licence gate. None is a tests-only mode: the
        # shipped server face wires a gate unconditionally
        # (F-ETO44-2 cure), with gate-absent reachable only via the
        # explicit ROUTESEAL_LICENCE_FIXTURE_BYPASS=1 opt-in.
        self.licence_gate = licence_gate
        self._last_licence_state = None
        self.records = {}
        self.journal = []
        self.metering = {}
        self._metering_baseline = {}
        # F-ETO44-1 cure: the metering journal's chain head and
        # record count as persisted in the state file at the last
        # save (None = no head ever recorded: pre-cure state).
        self._metering_head_recorded = None
        self._metering_records_recorded = None
        # ETO-44: metering journal (ACT pattern, separate file; it
        # never feeds seals or verdicts). Always written alongside
        # the existing metering counts.
        self.metering_journal = _mj.MeteringJournal(
            metering_journal_path or (state_path + ".metering.jsonl"))
        if os.path.exists(state_path):
            with open(state_path, encoding="utf-8") as fh:
                data = json.load(fh)
            self.records = data.get("records", {})
            self.journal = data.get("journal", [])
            self.metering = data.get("metering", {})
            self._metering_baseline = data.get(
                "metering_baseline", {})
            self._metering_head_recorded = data.get("metering_head")
            self._metering_records_recorded = data.get(
                "metering_records")
            ok, _ = self.verify_chain()
            if not ok:
                raise ValueError("receipt journal failed verification "
                                 "at load; store fails closed")
            self._verify_records()
            self._verify_metering_journal()

    # ------------------------------------------------- ETO-44 leg
    def _verify_metering_journal(self):
        """A metering journal that does not verify, or whose counts
        disagree with the store's metering counts, fails closed at
        load (same posture as the seal journal).

        F-ETO44-1 cure (VERDICT-DELTA-ROUTESEAL-ETO44-20261114):
        the state file persists the metering chain head and record
        count at every save. Once a head/count has been recorded,
        ANY mismatch at load fails closed — a truncated journal, a
        deleted journal, and a state-file count inflated against
        the journal are all refusals, never silent re-baselines.

        Migration, exactly once: a state carrying NO recorded head
        is pre-cure. If its journal file holds records, the counts
        must already reconcile exactly (journal + persisted
        baseline == store counts) — no baseline is invented for
        journal-era ops, so a pre-cure journal truncated before
        migration still fails closed; the journal's head/count are
        adopted at the next save. Only a state with counts and NO
        journal records at all is the genuine pre-ETO-44 legacy
        case: its shortfall becomes the persisted baseline."""
        v = self.metering_journal.verify()
        if not v["ok"]:
            raise ValueError("metering journal failed verification "
                             "at load; store fails closed")
        journal_counts = self.metering_journal.counts_by_op()
        journal_records = sum(journal_counts.values())
        for op, n in journal_counts.items():
            if n > self.metering.get(op, 0) + \
                    self._metering_baseline.get(op, 0):
                raise ValueError("metering journal records ops the "
                                 "store never counted at load; store "
                                 "fails closed")
        if self._metering_records_recorded is not None:
            # Recorded-head state: exact reconciliation only.
            if journal_records != self._metering_records_recorded \
                    or v.get("head") != \
                    self._metering_head_recorded:
                raise ValueError(
                    "metering journal head/count disagree with "
                    "the state file's recorded metering head/count "
                    "at load; store fails closed")
            for op in set(self.metering) | set(journal_counts) | \
                    set(self._metering_baseline):
                if journal_counts.get(op, 0) + \
                        self._metering_baseline.get(op, 0) != \
                        self.metering.get(op, 0):
                    raise ValueError(
                        "metering counts disagree with metering "
                        "journal + baseline at load; store fails "
                        "closed")
            return
        if journal_records > 0:
            # Pre-cure state with a journal: exact reconciliation
            # or refusal — no baseline adoption for journal-era ops.
            for op in set(self.metering) | set(journal_counts) | \
                    set(self._metering_baseline):
                if journal_counts.get(op, 0) + \
                        self._metering_baseline.get(op, 0) != \
                        self.metering.get(op, 0):
                    raise ValueError(
                        "pre-cure metering journal does not "
                        "reconcile exactly with store counts at "
                        "load; store fails closed")
            return
        # Genuine legacy counts predating the journal become its
        # baseline, persisted at the next save; reconciliation is
        # then exact: journal + baseline == store counts.
        for op, n in self.metering.items():
            short = n - journal_counts.get(op, 0) - \
                self._metering_baseline.get(op, 0)
            if short > 0:
                self._metering_baseline[op] = \
                    self._metering_baseline.get(op, 0) + short

    def _licence_check(self):
        """Returns None when the priced op may proceed, else the
        refusal dict. No record, receipt or metering entry is made
        for a licence refusal."""
        if self.licence_gate is None:
            self._last_licence_state = "UNCONFIGURED_FIXTURE"
            return None
        allowed, state = self.licence_gate.check()
        self._last_licence_state = state
        if allowed:
            return None
        return {"accepted": False, "error": state,
                "licence_state": state,
                "reason": "licence_gate_refused"}

    def _meter(self, op: str, subject: str):
        self.metering[op] = self.metering.get(op, 0) + 1
        self.metering_journal.append(subject, {
            "product": "routeseal", "op": op, "subject": subject,
            "unit_price_minor": 25, "currency": "USD",
            "fixture": True,
            "licence_state": self._last_licence_state})

    def metering_reconcile(self) -> dict:
        v = self.metering_journal.verify()
        journal_counts = self.metering_journal.counts_by_op()
        counted = sum(self.metering.values())
        recorded = sum(journal_counts.values())
        effective = {op: journal_counts.get(op, 0) +
                     self._metering_baseline.get(op, 0)
                     for op in set(journal_counts) |
                     set(self._metering_baseline)}
        recorded_ok = (
            self._metering_records_recorded is None
            or (recorded == self._metering_records_recorded
                and v.get("head") == self._metering_head_recorded))
        return {"ops_counted": counted,
                "journal_records": recorded,
                "counted_by_op": dict(self.metering),
                "journal_by_op": journal_counts,
                "baseline_by_op": dict(self._metering_baseline),
                "recorded_head": self._metering_head_recorded,
                "recorded_records": self._metering_records_recorded,
                "chain_ok": v["ok"], "chain_head": v.get("head"),
                "reconciled": bool(v["ok"])
                and effective == self.metering and recorded_ok}

    @staticmethod
    def _bundle_of(record: dict) -> dict:
        """The seal bundle (SPEC section 2) rebuilt from a stored
        record's own fields — the exact dict the record's seal
        digests at mint time."""
        return {
            "task_digest": record.get("task_digest"),
            "candidate_set": record.get("candidate_set"),
            "selected_target": record.get("selected_target"),
            "stated_reason": record.get("stated_reason"),
            "policy_version": record.get("policy_version"),
            "policy_digest": record.get("policy_digest"),
            "dispatch_point_id": record.get("dispatch_point_id"),
            "dispatch_timestamp": record.get("dispatch_timestamp"),
            "binding_ref": record.get("binding_ref"),
        }

    @classmethod
    def record_seal_valid(cls, record: dict) -> bool:
        """A record's seal is an unkeyed digest over its bundle
        fields; it binds the record's internal consistency (any
        post-seal edit to a bundle field breaks it). Provenance
        rests on the adapter channel at ingestion, not on the
        seal."""
        return logic.digest_obj(cls._bundle_of(record)) == \
            record.get("seal")

    def _verify_records(self):
        """C8 cure (VERDICT-DELTA-20261113 F1): journal
        self-consistency is not enough. Every stored record must
        agree with its own seal AND with the payload_digest of the
        dispatch_seal receipt its receipt_ref names (the receipt
        payload covers seal + verdict). Any mismatch fails closed
        at load — a tampered record is never served."""
        by_hash = {e.get("record_hash"): e for e in self.journal}
        for seal_id, record in self.records.items():
            if not self.record_seal_valid(record):
                raise ValueError(
                    "record seal verification failed at load for "
                    f"{seal_id}; store fails closed")
            receipt = by_hash.get(record.get("receipt_ref"))
            payload = {"dispatch_seal_id": seal_id,
                       "seal": record.get("seal"),
                       "verdict": record.get("verdict")}
            if receipt is None \
                    or receipt.get("kind") != "dispatch_seal" \
                    or receipt.get("payload_digest") != \
                    logic.digest_obj(payload):
                raise ValueError(
                    "record/receipt binding failed at load for "
                    f"{seal_id}; store fails closed")

    # ---------------------------------------------------------- io
    def _save(self):
        tmp = self.state_path + ".tmp"
        with open(tmp, "w", encoding="utf-8") as fh:
            json.dump({"records": self.records,
                       "journal": self.journal,
                       "metering": self.metering,
                       "metering_baseline": self._metering_baseline,
                       "metering_head": self.metering_journal.head,
                       "metering_records": self.metering_journal.seq},
                      fh, indent=1, sort_keys=True)
        os.replace(tmp, self.state_path)
        self._metering_head_recorded = self.metering_journal.head
        self._metering_records_recorded = self.metering_journal.seq

    # --------------------------------------------------- receipts
    def _append_receipt(self, kind: str, payload: dict) -> dict:
        prev = self.journal[-1]["record_hash"] if self.journal \
            else "GENESIS"
        entry = {"seq": len(self.journal) + 1, "timestamp": _now(),
                 "kind": kind,
                 "payload_digest": logic.digest_obj(payload),
                 "prev_hash": prev}
        entry["record_hash"] = logic.digest_obj(
            {k: entry[k] for k in
             ("seq", "timestamp", "kind", "payload_digest",
              "prev_hash")})
        self.journal.append(entry)
        return entry

    def verify_chain(self, journal=None):
        journal = self.journal if journal is None else journal
        prev = "GENESIS"
        for i, entry in enumerate(journal):
            if entry.get("prev_hash") != prev:
                return False, f"link broken at seq {entry.get('seq')}"
            expect = logic.digest_obj(
                {k: entry.get(k) for k in
                 ("seq", "timestamp", "kind", "payload_digest",
                  "prev_hash")})
            if entry.get("record_hash") != expect:
                return False, f"hash mismatch at seq {entry.get('seq')}"
            prev = entry["record_hash"]
        return True, prev

    def chain_head(self) -> str:
        return self.journal[-1]["record_hash"] if self.journal \
            else "GENESIS"

    # ------------------------------------------------- provenance
    def _attestation_valid(self, dispatch_point_id, binding_ref,
                           core: dict, attestation) -> bool:
        key = self.adapter_keys.get(dispatch_point_id)
        if not key or not attestation:
            return False
        msg = (binding_ref + "|" + logic.canon(core)).encode()
        expect = hmac.new(key.encode(), msg,
                          hashlib.sha256).hexdigest()
        return hmac.compare_digest(expect, attestation)

    @staticmethod
    def make_attestation(key: str, binding_ref: str,
                         core: dict) -> str:
        """The adapter side of the channel: an adapter holding its
        registered key attests a capture core + binding reference."""
        msg = (binding_ref + "|" + logic.canon(core)).encode()
        return hmac.new(key.encode(), msg,
                        hashlib.sha256).hexdigest()

    # ------------------------------------------------------- seal
    def seal_dispatch(self, capture: dict) -> dict:
        """Accept or reject a dispatch capture (RTE-REQ-012) and,
        on acceptance, seal the bundle and mint its verdict."""
        refusal = self._licence_check()  # ETO-44 priced boundary
        if refusal is not None:
            return refusal
        core = {k: capture.get(k) for k in
                ("task_digest", "candidate_set", "selected_target",
                 "stated_reason", "policy_version",
                 "dispatch_point_id", "dispatch_timestamp")}
        provenance_ok = (
            capture.get("source") == "dispatch-point-adapter"
            and self._attestation_valid(
                capture.get("dispatch_point_id"),
                capture.get("binding_ref"), core,
                capture.get("adapter_attestation")))

        if not provenance_ok:
            receipt = self._append_receipt(
                "capture_rejected",
                {"dispatch_point_id": capture.get("dispatch_point_id"),
                 "binding_ref": capture.get("binding_ref"),
                 "source": capture.get("source"),
                 "reason": "provenance_failure"})
            self._save()
            return {"accepted": False, "verdict": "UNVERIFIABLE",
                    "reason": "provenance_failure",
                    "receipt_ref": receipt["record_hash"]}

        policy = self.policies.get(capture.get("policy_version"))
        absent = capture.get("candidate_set") in (None, "ABSENT")
        candidates = None if absent else [
            _reduce_candidate(c) for c in capture["candidate_set"]]
        selected_cand = None
        if candidates:
            for c in candidates:
                if c["id"] == capture.get("selected_target"):
                    selected_cand = c
        bundle = {
            "task_digest": capture.get("task_digest"),
            "candidate_set": "ABSENT" if absent else candidates,
            "selected_target": capture.get("selected_target"),
            "stated_reason": capture.get("stated_reason"),
            "policy_version": capture.get("policy_version"),
            "policy_digest": logic.policy_digest(policy)
            if policy else None,
            "dispatch_point_id": capture.get("dispatch_point_id"),
            "dispatch_timestamp": capture.get("dispatch_timestamp"),
            "binding_ref": capture.get("binding_ref"),
        }
        verdict = logic.evaluate(bundle, policy)
        seal_id = "rts-" + logic.digest_obj(
            {**bundle, "binding_ref": bundle["binding_ref"]})[:16]
        existing = self.records.get(seal_id)
        if existing is not None:
            # C9 / RTE-REQ-014 cure (VERDICT-DELTA-20261113 F3):
            # idempotent seal — a replay of the identical capture
            # returns the existing record. No second receipt, no
            # second meter event: one dispatch, one seal, one op.
            return {"accepted": True,
                    "dispatch_seal_id": seal_id,
                    "receipt_ref": existing["receipt_ref"],
                    "verdict": existing["verdict"],
                    "clause": existing["clause"],
                    "passed_over_preferred":
                        existing["passed_over_preferred"],
                    "grammar_version": existing["grammar_version"],
                    "policy_version": existing["policy_version"],
                    "idempotent_replay": True}
        record = {
            "dispatch_seal_id": seal_id,
            "task_digest": bundle["task_digest"],
            "candidate_set": bundle["candidate_set"],
            "candidate_set_absent": absent,
            "selected_target": bundle["selected_target"],
            "stated_reason": bundle["stated_reason"],
            "policy_version": bundle["policy_version"],
            "policy_digest": bundle["policy_digest"],
            "affiliation_flags": {
                "selected_affiliated":
                    bool(selected_cand and
                         selected_cand.get("affiliated", False))},
            "dispatch_timestamp": bundle["dispatch_timestamp"],
            "dispatch_point_id": bundle["dispatch_point_id"],
            "binding_ref": bundle["binding_ref"],
            "seal": logic.digest_obj(bundle),
            "verdict": verdict["verdict"],
            "clause": verdict["clause"],
            "passed_over_preferred":
                verdict["passed_over_preferred"],
            "grammar_version": verdict["grammar_version"],
            "receipt_ref": None,
        }
        receipt = self._append_receipt(
            "dispatch_seal",
            {"dispatch_seal_id": seal_id, "seal": record["seal"],
             "verdict": record["verdict"]})
        record["receipt_ref"] = receipt["record_hash"]
        assert set(record.keys()) == set(RECORD_FIELDS)
        self.records[seal_id] = record
        if record["verdict"] in METERED_VERDICTS:
            self._meter("dispatch_seal", seal_id)
        self._save()
        return {"accepted": True, "dispatch_seal_id": seal_id,
                "receipt_ref": record["receipt_ref"],
                "verdict": record["verdict"],
                "clause": record["clause"],
                "passed_over_preferred":
                    record["passed_over_preferred"],
                "grammar_version": record["grammar_version"],
                "policy_version": record["policy_version"]}

    # ----------------------------------------------------- reads
    def get_verdict(self, seal_id: str) -> dict:
        record = self.records.get(seal_id)
        if record is None:
            return {"error": "NO_SUCH_SEAL"}
        return {"dispatch_seal_id": seal_id,
                "verdict": record["verdict"],
                "clause": record["clause"],
                "selected_target": record["selected_target"],
                "passed_over_preferred":
                    record["passed_over_preferred"],
                "grammar_version": record["grammar_version"],
                "policy_version": record["policy_version"],
                "receipt_refs": [record["receipt_ref"]]}

    def check(self, seal_id: str) -> dict:
        """Counterparty view (RTE-REQ-013): verdict class and named
        clause only."""
        record = self.records.get(seal_id)
        if record is None:
            return {"error": "NO_SUCH_SEAL"}
        return {"verdict": record["verdict"],
                "clause": record["clause"]}

    def export_capture(self, seal_id: str) -> dict:
        record = self.records.get(seal_id)
        if record is None:
            return {"error": "NO_SUCH_SEAL"}
        return {"capture": dict(record),
                "chain_head": self.chain_head(),
                "grammar_version": record["grammar_version"],
                "policy_version": record["policy_version"]}

    # --------------------------------------- after-the-fact guard
    def attach_candidate_set(self, seal_id: str, candidates) -> dict:
        """ADV-2 guard: a candidate set reconstructed or supplied
        after the fact is refused as capture material, and the
        refusal is receipted (RTE-REQ-011, spec P1). A sealed record
        is never mutated."""
        receipt = self._append_receipt(
            "candidate_set_refused",
            {"dispatch_seal_id": seal_id,
             "reason": "after_the_fact_candidate_set"})
        self._save()
        return {"accepted": False,
                "reason": "after_the_fact_candidate_set_refused",
                "receipt_ref": receipt["record_hash"]}


def recompute(capture: dict, grammar_version: str,
              policy_version: str, policies: dict) -> dict:
    """Third-party recomputation (RTE-REQ-002(iii)): verdict from
    the exported capture + the published grammar + the stated
    policy alone. Reads no service state (RTE-REQ-013)."""
    if grammar_version != logic.GRAMMAR_VERSION:
        return {"verdict": "UNVERIFIABLE",
                "reason": "unknown_grammar_version"}
    record = capture.get("capture", capture)
    # C6 cure (VERDICT-DELTA-20261113 F2): the record's seal is
    # verified against its bundle fields BEFORE any verdict is
    # minted. A fabricated or tampered capture — anything whose
    # seal does not recompute from the fields it carries — caps at
    # UNVERIFIABLE on this path exactly as on the ingestion paths.
    if not Store.record_seal_valid(record):
        return {"verdict": "UNVERIFIABLE",
                "reason": "seal_verification_failed",
                "seal_basis": SEAL_BASIS}
    seal_id = record.get("dispatch_seal_id")
    if seal_id is not None and \
            seal_id != "rts-" + record["seal"][:16]:
        return {"verdict": "UNVERIFIABLE",
                "reason": "seal_verification_failed",
                "seal_basis": SEAL_BASIS}
    policy = policies.get(policy_version)
    bundle = Store._bundle_of(record)
    verdict = logic.evaluate(bundle, policy)
    return {"verdict": verdict["verdict"],
            "clause": verdict["clause"],
            "selected_target": verdict["selected_target"],
            "passed_over_preferred":
                verdict["passed_over_preferred"],
            "grammar_version": logic.GRAMMAR_VERSION,
            "policy_version": policy_version,
            "seal_basis": SEAL_BASIS}


def load_policies(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        data = json.load(fh)
    return {p["version"]: p for p in data.get("policies", [])}


def load_adapter_keys(path: str) -> dict:
    with open(path, encoding="utf-8") as fh:
        return json.load(fh).get("adapter_keys", {})
