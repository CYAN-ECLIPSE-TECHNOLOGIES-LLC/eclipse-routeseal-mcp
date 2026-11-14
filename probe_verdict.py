#!/usr/bin/env python3
"""Judge-probe reproduction for VERDICT-DELTA-20261113 F1/F2/F3.
Run pre-cure: all three findings should reproduce (exit prints
CONFIRMED lines). Run post-cure: all three should print REFUSED."""
import json
import os
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "fixtures"))

import logic  # noqa: E402
import routeseal  # noqa: E402
import captures  # noqa: E402

POLICIES = routeseal.load_policies(
    os.path.join(HERE, "fixtures", "policies.json"))
KEYS = routeseal.load_adapter_keys(
    os.path.join(HERE, "keys", "adapter-keys.json"))

tmp = tempfile.mkdtemp()
path = os.path.join(tmp, "state.json")
store = routeseal.Store(path, POLICIES, KEYS)

# ---- F1: tampered store record loads silently -------------------
out = store.seal_dispatch(captures.capture(selected="beta",
                                           binding="evt-probe-f1"))
seal_id = out["dispatch_seal_id"]
assert out["verdict"] == "DEVIATION", out
with open(path, encoding="utf-8") as fh:
    data = json.load(fh)
data["records"][seal_id]["verdict"] = "AS-DECLARED"
data["records"][seal_id]["clause"] = None
with open(path, "w", encoding="utf-8") as fh:
    json.dump(data, fh)
try:
    store2 = routeseal.Store(path, POLICIES, KEYS)
    served = store2.get_verdict(seal_id)
    if served.get("verdict") == "AS-DECLARED":
        print("F1 CONFIRMED: tampered record loaded silently, "
              "get_verdict served AS-DECLARED")
    else:
        print("F1 NOT-REPRODUCED: served", served)
except ValueError as exc:
    print("F1 REFUSED at load:", exc)

# ---- F2: recompute mints DEVIATION from fabricated capture ------
policy = POLICIES["op-policy/1"]
fabricated = {
    "task_digest": "sha256:" + "ab" * 32,
    "candidate_set": captures.CANDIDATES,
    "selected_target": "beta",
    "stated_reason": "best fit per stated policy",
    "policy_version": "op-policy/1",
    "policy_digest": logic.policy_digest(policy),
    "dispatch_point_id": "dp-alpha",
    "dispatch_timestamp": "2026-11-11T12:00:00Z",
    "binding_ref": "evt-fabricated",
    "seal": "00" * 32,
    "verdict": "DEVIATION",
}
fresh = routeseal.recompute(fabricated, logic.GRAMMAR_VERSION,
                            "op-policy/1", POLICIES)
if fresh.get("verdict") == "DEVIATION":
    print("F2 CONFIRMED: recompute minted DEVIATION from a "
          "fabricated, never-sealed capture")
elif fresh.get("verdict") == "UNVERIFIABLE":
    print("F2 REFUSED: recompute capped UNVERIFIABLE:", fresh)
else:
    print("F2 NOT-REPRODUCED:", fresh)

# ---- F3: replay double-receipts + double-meters -----------------
path3 = os.path.join(tmp, "state3.json")
store3 = routeseal.Store(path3, POLICIES, KEYS)
cap = captures.capture(selected="beta", binding="evt-probe-f3")
r1 = store3.seal_dispatch(cap)
r2 = store3.seal_dispatch(dict(cap))
receipts = [e for e in store3.journal if e["kind"] == "dispatch_seal"]
meter = store3.metering.get("dispatch_seal", 0)
if len(receipts) == 2 and meter == 2:
    print("F3 CONFIRMED: identical capture replayed -> 2 dispatch_seal "
          "receipts, 2 metered ops for one dispatch")
elif len(receipts) == 1 and meter == 1:
    print("F3 REFUSED: replay idempotent -> 1 receipt, 1 metered op; "
          "second call returned", r2.get("dispatch_seal_id"))
else:
    print("F3 NOT-REPRODUCED: receipts", len(receipts), "meter", meter)
