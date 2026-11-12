#!/usr/bin/env python3
# Cyan Eclipse Routeseal — fixture capture builder.
# Copyright © 2026 Cyan Eclipse Technologies LLC · cetech.ai
"""Builds dispatch captures the way the buyer-side dispatch-point
adapter presents them: core routing facts + the adapter's HMAC
attestation over (binding_ref | canonical core)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
import routeseal  # noqa: E402

KEY = "fixture-adapter-key-dp-alpha"

CANDIDATES = [
    {"id": "alpha", "affiliated": False, "capabilities": ["code"],
     "cost": 4.0, "latency_ms": 120},
    {"id": "beta", "affiliated": True, "capabilities": ["code"],
     "cost": 3.0, "latency_ms": 90},
    {"id": "gamma", "affiliated": False, "capabilities": ["chat"],
     "cost": 2.0, "latency_ms": 60},
]


def capture(selected="alpha", candidates=None, binding="evt-0001",
            policy_version="op-policy/1", source="dispatch-point-adapter",
            key=KEY, **overrides):
    cap = {
        "task_digest": "sha256:" + "ab" * 32,
        "candidate_set": CANDIDATES if candidates is None else candidates,
        "selected_target": selected,
        "stated_reason": "best fit per stated policy",
        "policy_version": policy_version,
        "affiliation_flags": {},
        "dispatch_point_id": "dp-alpha",
        "dispatch_timestamp": "2026-11-11T12:00:00Z",
        "binding_ref": binding,
        "source": source,
    }
    cap.update(overrides)
    core = {k: cap.get(k) for k in
            ("task_digest", "candidate_set", "selected_target",
             "stated_reason", "policy_version", "dispatch_point_id",
             "dispatch_timestamp")}
    cap["adapter_attestation"] = routeseal.Store.make_attestation(
        key, cap["binding_ref"], core)
    return cap
