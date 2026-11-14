#!/usr/bin/env python3
# Cyan Eclipse Routeseal — requirement-mapped test suite.
# Copyright © 2026 Cyan Eclipse Technologies LLC · cetech.ai
"""Every test names the requirement it verifies (SPEC-ROUTESEAL
section 3) and, where the bench plan restates it, the bench claim
(section 6). Builder tests are not bench evidence; they are the
build's own verification that the bench can later re-run.
"""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "fixtures"))

import logic  # noqa: E402
import routeseal  # noqa: E402
import server  # noqa: E402
import captures  # noqa: E402

POLICIES = routeseal.load_policies(
    os.path.join(ROOT, "fixtures", "policies.json"))
KEYS = routeseal.load_adapter_keys(
    os.path.join(ROOT, "keys", "adapter-keys.json"))

BANNED = ("proves steering", "self-preferencing",
          "chose this because it wanted", "antitrust",
          "fiduciary breach")


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, "state.json")
        self.store = routeseal.Store(self.path, POLICIES, KEYS)

    def seal(self, **kw):
        return self.store.seal_dispatch(captures.capture(**kw))


class TestDeviationDetection(Base):
    """RTE-REQ-010 / RT-B1: policy-violating fixtures verdict
    DEVIATION naming clause, selected, passed-over preferred;
    conformant controls verdict AS-DECLARED."""

    def test_conformant_control(self):
        out = self.seal(selected="alpha")
        self.assertEqual(out["verdict"], "AS-DECLARED")
        self.assertIsNone(out["clause"])

    def test_preference_deviation(self):
        out = self.seal(selected="beta", binding="evt-pref")
        self.assertEqual(out["verdict"], "DEVIATION")
        self.assertEqual(out["clause"], "preference_order")
        self.assertEqual(out["passed_over_preferred"], "alpha")

    def test_capability_deviation(self):
        out = self.seal(selected="gamma", binding="evt-cap")
        self.assertEqual(out["verdict"], "DEVIATION")
        self.assertEqual(out["clause"], "capability_match")
        self.assertEqual(out["passed_over_preferred"], "alpha")

    def test_bounds_deviation(self):
        cands = [dict(c) for c in captures.CANDIDATES]
        cands[0] = {**cands[0], "cost": 99.0}
        out = self.seal(selected="alpha", candidates=cands,
                        binding="evt-bounds")
        self.assertEqual(out["verdict"], "DEVIATION")
        self.assertEqual(out["clause"], "cost_latency_bounds")

    def test_exclusion_clause(self):
        out = self.seal(selected="beta", policy_version="op-policy/2",
                        binding="evt-excl")
        self.assertEqual(out["verdict"], "DEVIATION")
        self.assertEqual(out["clause"], "affiliation_exclusion")

    def test_flagging_clause(self):
        policies = {"p-flag": {"version": "p-flag", "clauses": [
            {"class": "affiliation_flagging"},
            {"class": "capability_match",
             "required_capabilities": ["code"]}]}}
        store = routeseal.Store(self.path, policies, KEYS)
        cap = captures.capture(selected="beta",
                               policy_version="p-flag",
                               binding="evt-flag")
        out = store.seal_dispatch(cap)
        self.assertEqual(out["verdict"], "DEVIATION")
        self.assertEqual(out["clause"], "affiliation_flagging")
        self.assertEqual(out["passed_over_preferred"], "alpha")


class TestCandidateSetDiscipline(Base):
    """RTE-REQ-004 / RTE-REQ-011 / RT-B3 + ADV-2: decision-only
    captures verdict CANDIDATE-SET-ABSENT in 100% of cases; a
    candidate set is never inferred or attached after the fact."""

    def test_decision_only_absent_marker(self):
        out = self.seal(candidates="ABSENT", binding="evt-abs1")
        self.assertEqual(out["verdict"], "CANDIDATE-SET-ABSENT")

    def test_decision_only_null(self):
        cap = captures.capture(binding="evt-abs2")
        cap["candidate_set"] = None
        # attestation was computed over the original set; rebuild
        core = {k: cap.get(k) for k in
                ("task_digest", "candidate_set", "selected_target",
                 "stated_reason", "policy_version",
                 "dispatch_point_id", "dispatch_timestamp")}
        cap["adapter_attestation"] = routeseal.Store.make_attestation(
            captures.KEY, cap["binding_ref"], core)
        out = self.store.seal_dispatch(cap)
        self.assertEqual(out["verdict"], "CANDIDATE-SET-ABSENT")

    def test_after_the_fact_attach_refused(self):
        out = self.seal(candidates="ABSENT", binding="evt-adv2")
        seal_id = out["dispatch_seal_id"]
        before = dict(self.store.records[seal_id])
        refusal = self.store.attach_candidate_set(
            seal_id, captures.CANDIDATES)
        self.assertFalse(refusal["accepted"])
        self.assertEqual(self.store.records[seal_id], before)
        self.assertEqual(self.store.records[seal_id]["verdict"],
                         "CANDIDATE-SET-ABSENT")
        kinds = [e["kind"] for e in self.store.journal]
        self.assertIn("candidate_set_refused", kinds)

    def test_no_deviation_without_candidate_set(self):
        for marker in ("ABSENT",):
            out = self.seal(candidates=marker, selected="beta",
                            binding="evt-nd-" + marker)
            self.assertNotEqual(out["verdict"], "DEVIATION")


class TestBelowStandard(Base):
    """RTE-REQ-004 / RT-B3: below-standard captures cap at
    UNVERIFIABLE."""

    def test_missing_stated_reason(self):
        cap = captures.capture(binding="evt-below")
        cap["stated_reason"] = ""
        core = {k: cap.get(k) for k in
                ("task_digest", "candidate_set", "selected_target",
                 "stated_reason", "policy_version",
                 "dispatch_point_id", "dispatch_timestamp")}
        cap["adapter_attestation"] = routeseal.Store.make_attestation(
            captures.KEY, cap["binding_ref"], core)
        out = self.store.seal_dispatch(cap)
        self.assertEqual(out["verdict"], "UNVERIFIABLE")

    def test_unknown_policy_version(self):
        out = self.seal(policy_version="op-policy/99",
                        binding="evt-nopol")
        self.assertEqual(out["verdict"], "UNVERIFIABLE")


class TestProvenance(Base):
    """RTE-REQ-012 / ADV-1 (the RT-K1 guard): platform-produced
    traces/logs, and any relay of them, are rejected and receipted;
    no AS-DECLARED or DEVIATION verdict is mintable."""

    def test_platform_log_rejected(self):
        cap = captures.capture(source="platform-log-export",
                               binding="evt-adv1")
        out = self.store.seal_dispatch(cap)
        self.assertFalse(out["accepted"])
        self.assertEqual(out["verdict"], "UNVERIFIABLE")
        kinds = [e["kind"] for e in self.store.journal]
        self.assertIn("capture_rejected", kinds)
        self.assertEqual(self.store.records, {})

    def test_relayed_log_rejected(self):
        cap = captures.capture(source="adapter-relay",
                               binding="evt-adv1b")
        out = self.store.seal_dispatch(cap)
        self.assertFalse(out["accepted"])

    def test_forged_attestation_rejected(self):
        cap = captures.capture(binding="evt-forge")
        cap["adapter_attestation"] = "00" * 32
        out = self.store.seal_dispatch(cap)
        self.assertFalse(out["accepted"])
        self.assertEqual(self.store.records, {})

    def test_wrong_point_key_rejected(self):
        cap = captures.capture(binding="evt-wrongkey",
                               key="fixture-adapter-key-dp-beta")
        out = self.store.seal_dispatch(cap)
        self.assertFalse(out["accepted"])


class TestRecompute(Base):
    """RTE-REQ-002(iii) / RTE-REQ-013 / RT-B2: an independent
    verifier reproduces the verdict from the exported capture +
    grammar alone, with no service state."""

    def test_recompute_matches(self):
        out = self.seal(selected="beta", binding="evt-rc1")
        export = self.store.export_capture(out["dispatch_seal_id"])
        fresh = routeseal.recompute(export, logic.GRAMMAR_VERSION,
                                    "op-policy/1", POLICIES)
        self.assertEqual(fresh["verdict"], "DEVIATION")
        self.assertEqual(fresh["clause"], "preference_order")
        self.assertEqual(fresh["passed_over_preferred"], "alpha")

    def test_recompute_conformant(self):
        out = self.seal(selected="alpha", binding="evt-rc2")
        export = self.store.export_capture(out["dispatch_seal_id"])
        fresh = routeseal.recompute(export, logic.GRAMMAR_VERSION,
                                    "op-policy/1", POLICIES)
        self.assertEqual(fresh["verdict"], "AS-DECLARED")

    def test_recompute_absent(self):
        out = self.seal(candidates="ABSENT", binding="evt-rc3")
        export = self.store.export_capture(out["dispatch_seal_id"])
        fresh = routeseal.recompute(export, logic.GRAMMAR_VERSION,
                                    "op-policy/1", POLICIES)
        self.assertEqual(fresh["verdict"], "CANDIDATE-SET-ABSENT")


class TestCustody(Base):
    """RTE-REQ-005 / RT-B4: the store contains only the section 2
    field set; no task bodies anywhere."""

    def test_record_field_set_exact(self):
        out = self.seal(binding="evt-cust")
        record = self.store.records[out["dispatch_seal_id"]]
        self.assertEqual(set(record.keys()),
                         set(routeseal.RECORD_FIELDS))

    def test_state_file_has_no_task_body(self):
        self.seal(binding="evt-cust2")
        with open(self.path, encoding="utf-8") as fh:
            text = fh.read()
        self.assertNotIn("task_body", text)
        self.assertNotIn("prompt", text)
        record = next(iter(self.store.records.values()))
        cand = record["candidate_set"][0]
        self.assertTrue(set(cand.keys()) <=
                        set(routeseal.CANDIDATE_FIELDS))


class TestVersioning(Base):
    """RTE-REQ-007 / RT-B5: verdicts name grammar + policy versions;
    a later revision never retro-alters a minted verdict."""

    def test_versions_named(self):
        out = self.seal(binding="evt-ver")
        self.assertEqual(out["grammar_version"],
                         logic.GRAMMAR_VERSION)
        self.assertEqual(out["policy_version"], "op-policy/1")

    def test_revision_does_not_rewrite(self):
        out = self.seal(selected="beta", binding="evt-ver2")
        seal_id = out["dispatch_seal_id"]
        snapshot = json.dumps(self.store.records[seal_id],
                              sort_keys=True)
        self.seal(selected="beta", policy_version="op-policy/2",
                  binding="evt-ver3")
        self.assertEqual(
            json.dumps(self.store.records[seal_id], sort_keys=True),
            snapshot)


class TestReceiptChain(Base):
    """RTE-REQ-014: one receipt per seal/verdict event; the chain
    verifies end-to-end; tampering and truncation are detected."""

    def test_chain_verifies(self):
        self.seal(binding="evt-chain1")
        self.seal(selected="beta", binding="evt-chain2")
        ok, head = self.store.verify_chain()
        self.assertTrue(ok)
        self.assertEqual(head, self.store.chain_head())

    def test_tamper_detected(self):
        self.seal(binding="evt-chain3")
        journal = json.loads(json.dumps(self.store.journal))
        journal[0]["payload_digest"] = "00" * 32
        ok, _ = self.store.verify_chain(journal)
        self.assertFalse(ok)

    def test_truncated_export_detected(self):
        self.seal(binding="evt-chain4")
        export = self.store.export_capture(
            next(iter(self.store.records)))
        ok, head = self.store.verify_chain(self.store.journal[:-0])
        self.assertTrue(ok)
        truncated = self.store.journal[:-1]
        ok2, head2 = self.store.verify_chain(truncated)
        self.assertTrue(ok2)  # a prefix verifies as a chain…
        self.assertNotEqual(head2, export["chain_head"])  # …but its
        # head no longer matches the export's chain head.

    def test_store_fails_closed_on_tampered_journal(self):
        self.seal(binding="evt-chain5")
        with open(self.path, encoding="utf-8") as fh:
            data = json.load(fh)
        data["journal"][0]["payload_digest"] = "ff" * 32
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(data, fh)
        with self.assertRaises(ValueError):
            routeseal.Store(self.path, POLICIES, KEYS)


class TestRecordTamperRefusal(Base):
    """C8 cure (VERDICT-DELTA-20261113 F1) / QA-PATTERNS P6 shape:
    a store record tampered in the state file is refused at load —
    never loaded silently, never served. At load each record must
    agree with its own seal and with the payload_digest of the
    dispatch_seal receipt its receipt_ref names."""

    def _tamper(self, seal_id, field, value):
        with open(self.path, encoding="utf-8") as fh:
            data = json.load(fh)
        data["records"][seal_id][field] = value
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(data, fh)

    def test_tampered_verdict_field_refused_at_load(self):
        out = self.seal(selected="beta", binding="evt-t1")
        self.assertEqual(out["verdict"], "DEVIATION")
        self._tamper(out["dispatch_seal_id"], "verdict",
                     "AS-DECLARED")
        with self.assertRaises(ValueError):
            routeseal.Store(self.path, POLICIES, KEYS)

    def test_tampered_bundle_field_refused_at_load(self):
        out = self.seal(selected="beta", binding="evt-t2")
        self._tamper(out["dispatch_seal_id"], "selected_target",
                     "alpha")
        with self.assertRaises(ValueError):
            routeseal.Store(self.path, POLICIES, KEYS)

    def test_tampered_seal_field_refused_at_load(self):
        out = self.seal(binding="evt-t3")
        self._tamper(out["dispatch_seal_id"], "seal", "00" * 32)
        with self.assertRaises(ValueError):
            routeseal.Store(self.path, POLICIES, KEYS)

    def test_genuine_store_reloads_and_serves(self):
        out = self.seal(selected="beta", binding="evt-t4")
        store2 = routeseal.Store(self.path, POLICIES, KEYS)
        served = store2.get_verdict(out["dispatch_seal_id"])
        self.assertEqual(served["verdict"], "DEVIATION")
        self.assertEqual(served["clause"], "preference_order")


class TestMetering(Base):
    """RTE-REQ-015 / spec 4.3: one charge per dispatch seal;
    CANDIDATE-SET-ABSENT and UNVERIFIABLE never meter; recompute
    and check never meter."""

    def test_metering_by_class(self):
        self.seal(binding="evt-m1")                       # AS-DECLARED
        self.seal(selected="beta", binding="evt-m2")      # DEVIATION
        self.seal(candidates="ABSENT", binding="evt-m3")  # ABSENT
        cap = captures.capture(source="platform-log-export",
                               binding="evt-m4")
        self.store.seal_dispatch(cap)                     # rejected
        self.assertEqual(self.store.metering,
                         {"dispatch_seal": 2})

    def test_ledger_records_class_and_count_only(self):
        self.seal(binding="evt-m5")
        self.assertEqual(set(self.store.metering.keys()),
                         {"dispatch_seal"})
        self.assertIsInstance(self.store.metering["dispatch_seal"],
                              int)


class TestMcpSurface(Base):
    """RTE-REQ-013: the MCP surface is exactly section 4.1;
    routeseal_check reveals verdict + clause only; outputs carry
    only the section 2 verdict vocabulary."""

    def test_tool_inventory_exact(self):
        names = set(server.SCHEMAS.keys())
        self.assertEqual(names, {
            "routeseal_seal_dispatch", "routeseal_get_verdict",
            "routeseal_check", "routeseal_recompute",
            "routeseal_export_captures"})

    def test_no_such_tool_for_aggregation_or_amendment(self):
        for name in ("routeseal_platform_stats",
                     "routeseal_attach_candidate_set",
                     "routeseal_route_task", "routeseal_list_all"):
            self.assertEqual(server.call_tool(name, {}),
                             {"error": "NO_SUCH_TOOL"})

    def test_check_reveals_clause_only(self):
        st = server.store()
        out = st.seal_dispatch(captures.capture(
            selected="beta", binding="evt-mcp1"))
        view = server.call_tool(
            "routeseal_check",
            {"dispatch_seal_id": out["dispatch_seal_id"]})
        self.assertEqual(set(view.keys()), {"verdict", "clause"})
        self.assertEqual(view["verdict"], "DEVIATION")

    def test_banned_terms_absent_from_surfaces(self):
        blob = json.dumps(server.DESCRIPTIONS) + routeseal.CLAIM
        for term in BANNED:
            self.assertNotIn(term, blob)


class TestAggregationFence(Base):
    """RTE-REQ-006: no cross-operator aggregation code path or
    surface exists in the build."""

    def test_no_aggregation_surface(self):
        names = [n for n in dir(routeseal.Store) if not n.startswith("_")]
        names += list(server.SCHEMAS.keys())
        for token in ("aggregat", "stats", "dossier", "feed"):
            self.assertFalse(any(token in n for n in names),
                             f"aggregation surface present: {token}")


if __name__ == "__main__":
    unittest.main()
