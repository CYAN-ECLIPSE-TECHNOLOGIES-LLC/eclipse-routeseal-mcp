#!/usr/bin/env python3
# Cyan Eclipse Routeseal — routing-policy grammar + verdict engine
# (SPEC-ROUTESEAL sections 2, 3; gate RT-C4/C7).
# Copyright © 2026 Cyan Eclipse Technologies LLC · cetech.ai
"""Pure verdict logic. Holds no state and reads no store: given a
sealed dispatch bundle's routing facts and the operator's stated
routing policy, it mints exactly one verdict from the fixed grammar:

  AS-DECLARED · DEVIATION · CANDIDATE-SET-ABSENT · UNVERIFIABLE

The engine is structurally incapable of minting DEVIATION without a
sealed candidate set (RTE-REQ-011): evaluate() receives the candidate
set only as sealed at dispatch, and the ABSENT marker short-circuits
every steering clause. Verdicts name facts only — the clause
diverged from, the selected target, the policy-preferred candidate
passed over. No verdict, field, or string in this module speaks to
intent or motive (gate RT-C9 / spec P3).
"""
import hashlib
import json

GRAMMAR_VERSION = "routeseal-grammar/1"

VERDICTS = ("AS-DECLARED", "DEVIATION", "CANDIDATE-SET-ABSENT",
            "UNVERIFIABLE")

# Clause classes of the published routing-policy grammar (SPEC §2,
# RTE-REQ-010). Evaluation order is fixed and part of the grammar:
# hard clauses first, preference last.
CLAUSE_CLASSES = ("affiliation_exclusion", "capability_match",
                  "cost_latency_bounds", "preference_order",
                  "affiliation_flagging")

# The minimum sealed bundle (SPEC §2 / RT-C4). A capture missing any
# of these fields is below standard and caps at UNVERIFIABLE.
REQUIRED_BUNDLE_FIELDS = ("task_digest", "selected_target",
                          "stated_reason", "policy_version",
                          "policy_digest", "dispatch_point_id",
                          "dispatch_timestamp", "binding_ref")


class LogicError(Exception):
    pass


def sha(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def canon(obj) -> str:
    return json.dumps(obj, sort_keys=True, separators=(",", ":"))


def digest_obj(obj) -> str:
    return sha(canon(obj))


def policy_digest(policy: dict) -> str:
    return digest_obj(policy)


def _clauses(policy: dict) -> dict:
    """Index a policy's clauses by class. A policy is
    {"version": str, "clauses": [{"class": ..., ...}, ...]}."""
    out = {}
    for clause in policy.get("clauses", []):
        out[clause.get("class")] = clause
    return out


def _candidate(candidates, target_id):
    for cand in candidates:
        if cand.get("id") == target_id:
            return cand
    return None


def preferred_candidate(policy: dict, candidates):
    """The policy-preferred candidate: the candidate that satisfies
    every hard clause and ranks first under the policy (preference
    order where stated, else presentation order). None when no
    candidate satisfies the hard clauses."""
    clauses = _clauses(policy)
    pool = list(candidates)

    excl = clauses.get("affiliation_exclusion")
    if excl is not None:
        pool = [c for c in pool if not c.get("affiliated", False)]

    cap = clauses.get("capability_match")
    if cap is not None:
        required = set(cap.get("required_capabilities", []))
        pool = [c for c in pool
                if required.issubset(set(c.get("capabilities", [])))]

    bounds = clauses.get("cost_latency_bounds")
    if bounds is not None:
        max_cost = bounds.get("max_cost")
        max_lat = bounds.get("max_latency_ms")
        def within(c):
            if max_cost is not None and c.get("cost") is not None \
                    and c["cost"] > max_cost:
                return False
            if max_lat is not None and c.get("latency_ms") is not None \
                    and c["latency_ms"] > max_lat:
                return False
            return True
        pool = [c for c in pool if within(c)]

    pref = clauses.get("preference_order")
    if pref is not None and pool:
        order = pref.get("order", [])
        pool.sort(key=lambda c: order.index(c["id"])
                  if c["id"] in order else len(order))
    return pool[0] if pool else None


def evaluate(bundle: dict, policy: dict) -> dict:
    """Mint the verdict for a sealed bundle under a stated policy.

    bundle keys: candidate_set (list of candidate dicts, or the
    string "ABSENT"), selected_target, plus the §2 routing facts.
    Returns the verdict record fields (verdict, clause,
    selected_target, passed_over_preferred)."""
    base = {"grammar_version": GRAMMAR_VERSION,
            "policy_version": bundle.get("policy_version"),
            "selected_target": bundle.get("selected_target"),
            "clause": None, "passed_over_preferred": None}

    missing = [f for f in REQUIRED_BUNDLE_FIELDS
               if bundle.get(f) in (None, "")]
    if missing:
        return {**base, "verdict": "UNVERIFIABLE",
                "missing_fields": missing}

    candidates = bundle.get("candidate_set")
    if candidates == "ABSENT" or candidates is None:
        return {**base, "verdict": "CANDIDATE-SET-ABSENT"}

    if policy is None or bundle.get("policy_digest") != \
            policy_digest(policy):
        return {**base, "verdict": "UNVERIFIABLE",
                "missing_fields": ["policy_unresolvable"]}

    selected = _candidate(candidates, bundle["selected_target"])
    if selected is None:
        # The selected target was not among the candidates as
        # presented: the capture does not meet the standard.
        return {**base, "verdict": "UNVERIFIABLE",
                "missing_fields": ["selected_not_in_candidate_set"]}

    clauses = _clauses(policy)
    preferred = preferred_candidate(policy, candidates)
    preferred_id = preferred["id"] if preferred else None

    def deviation(clause_class):
        return {**base, "verdict": "DEVIATION",
                "clause": clause_class,
                "passed_over_preferred":
                    preferred_id if preferred_id !=
                    bundle["selected_target"] else None}

    # affiliation_exclusion (hard): an affiliated target must never
    # be selected while this clause stands.
    if "affiliation_exclusion" in clauses and \
            selected.get("affiliated", False):
        return deviation("affiliation_exclusion")

    # capability_match (hard): the selected target must carry every
    # required capability.
    cap = clauses.get("capability_match")
    if cap is not None:
        required = set(cap.get("required_capabilities", []))
        if not required.issubset(set(selected.get("capabilities", []))):
            return deviation("capability_match")

    # cost_latency_bounds (hard): the selected target must sit
    # within the stated bounds.
    bounds = clauses.get("cost_latency_bounds")
    if bounds is not None:
        max_cost = bounds.get("max_cost")
        max_lat = bounds.get("max_latency_ms")
        if (max_cost is not None and selected.get("cost") is not None
                and selected["cost"] > max_cost) or \
           (max_lat is not None and selected.get("latency_ms")
                is not None and selected["latency_ms"] > max_lat):
            return deviation("cost_latency_bounds")

    # preference_order: where a conforming preferred candidate
    # exists and a different target was selected, the selection
    # diverged from the stated preference.
    if "preference_order" in clauses and preferred_id is not None \
            and preferred_id != bundle["selected_target"]:
        return deviation("preference_order")

    # affiliation_flagging: selecting an affiliated target over a
    # non-affiliated candidate the policy otherwise prefers is a
    # divergence from the flagging clause.
    if "affiliation_flagging" in clauses and \
            selected.get("affiliated", False) and \
            preferred is not None and \
            not preferred.get("affiliated", False) and \
            preferred_id != bundle["selected_target"]:
        return deviation("affiliation_flagging")

    return {**base, "verdict": "AS-DECLARED"}
