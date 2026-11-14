#!/usr/bin/env python3
# Cyan Eclipse Routeseal - ETO-44 licence metering tests.
# Copyright © 2026 Cyan Eclipse Technologies LLC · cetech.ai
"""ETO-44: per-op licence-checked metering. Fake transport with the
ActivationClient shape; the live deployed-server proof is
fixtures/licence_proof.py (evidence, not a unit test)."""
import json
import os
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "fixtures"))

import routeseal  # noqa: E402
import captures  # noqa: E402
from licence_gate import LicenceGate  # noqa: E402
import metering_journal  # noqa: E402

POLICIES = routeseal.load_policies(
    os.path.join(ROOT, "fixtures", "policies.json"))
KEYS = routeseal.load_adapter_keys(
    os.path.join(ROOT, "keys", "adapter-keys.json"))


class FakeClient:
    def __init__(self, checkin_state="LICENSE_VALID"):
        self.checkin_state = checkin_state
        self.activations = 0
        self.checkins = 0

    def activate(self, artefact, install_id, label=""):
        self.activations += 1
        return {"state": "LICENSE_VALID", "activation_token": "tok-1",
                "license_id": "lic-fixture-1"}

    def checkin(self, token, artefact_hash):
        self.checkins += 1
        return {"state": self.checkin_state}


def make_gate(tmp, client):
    import base64
    artefact = base64.urlsafe_b64encode(
        json.dumps({"license_id": "lic-fixture-1"}).encode()
    ).decode().rstrip("=") + ".sig"
    path = os.path.join(tmp, "licence-state.json")
    with open(path, "w") as f:
        json.dump({"artefact": artefact, "install_id": "inst-1",
                   "install_label": "routeseal-test"}, f)
    return LicenceGate(state_path=path, client=client)


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, "state.json")


class TestLicenceMetering(Base):
    def test_valid_licence_op_succeeds_and_meters(self):
        gate = make_gate(self.tmp, FakeClient())
        st = routeseal.Store(self.path, POLICIES, KEYS,
                             licence_gate=gate)
        out = st.seal_dispatch(captures.capture())
        self.assertTrue(out["accepted"])
        self.assertEqual(st.metering, {"dispatch_seal": 1})
        rec = st.metering_reconcile()
        self.assertTrue(rec["reconciled"], rec)
        self.assertEqual(rec["ops_counted"], 1)
        self.assertEqual(rec["journal_records"], 1)
        j = metering_journal.MeteringJournal(
            self.path + ".metering.jsonl")
        self.assertEqual(j.read_all()[0]["payload"]["unit_price_minor"],
                         25)
        self.assertEqual(
            j.read_all()[0]["payload"]["licence_state"], "LICENSE_VALID")

    def test_no_licence_op_refused_and_unmetered(self):
        gate = LicenceGate(state_path=os.path.join(
            self.tmp, "absent.json"), client=FakeClient())
        st = routeseal.Store(self.path, POLICIES, KEYS,
                             licence_gate=gate)
        out = st.seal_dispatch(captures.capture())
        self.assertFalse(out["accepted"])
        self.assertEqual(out["error"], "LICENSE_NOT_CONFIGURED")
        self.assertEqual(st.metering, {})
        self.assertEqual(st.records, {})
        self.assertTrue(st.metering_reconcile()["reconciled"])

    def test_revoked_licence_refused_at_checkin(self):
        client = FakeClient()
        gate = make_gate(self.tmp, client)
        st = routeseal.Store(self.path, POLICIES, KEYS,
                             licence_gate=gate)
        self.assertTrue(st.seal_dispatch(captures.capture())["accepted"])
        client.checkin_state = "LICENSE_REVOKED"
        out = st.seal_dispatch(captures.capture(binding="evt-2"))
        self.assertFalse(out["accepted"])
        self.assertEqual(out["error"], "LICENSE_REVOKED")
        self.assertEqual(st.metering, {"dispatch_seal": 1})

    def test_reads_never_gated(self):
        client = FakeClient()
        gate = make_gate(self.tmp, client)
        st = routeseal.Store(self.path, POLICIES, KEYS,
                             licence_gate=gate)
        out = st.seal_dispatch(captures.capture())
        client.checkin_state = "LICENSE_REVOKED"
        view = st.get_verdict(out["dispatch_seal_id"])
        self.assertEqual(view["verdict"], "AS-DECLARED")
        self.assertEqual(st.check(out["dispatch_seal_id"])["verdict"],
                         "AS-DECLARED")

    def test_idempotent_replay_single_metering_record(self):
        gate = make_gate(self.tmp, FakeClient())
        st = routeseal.Store(self.path, POLICIES, KEYS,
                             licence_gate=gate)
        cap = captures.capture()
        st.seal_dispatch(cap)
        st.seal_dispatch(dict(cap))
        rec = st.metering_reconcile()
        self.assertEqual(rec["ops_counted"], 1)
        self.assertEqual(rec["journal_records"], 1)
        self.assertTrue(rec["reconciled"])

    def test_unmetered_verdict_writes_no_record(self):
        gate = make_gate(self.tmp, FakeClient())
        st = routeseal.Store(self.path, POLICIES, KEYS,
                             licence_gate=gate)
        out = st.seal_dispatch(captures.capture(candidates="ABSENT"))
        self.assertTrue(out["accepted"])
        self.assertEqual(st.metering, {})
        self.assertEqual(st.metering_reconcile()["journal_records"], 0)

    def test_metering_journal_tamper_fails_closed_at_load(self):
        gate = make_gate(self.tmp, FakeClient())
        st = routeseal.Store(self.path, POLICIES, KEYS,
                             licence_gate=gate)
        st.seal_dispatch(captures.capture())
        jpath = self.path + ".metering.jsonl"
        with open(jpath) as f:
            lines = f.readlines()
        rec = json.loads(lines[0])
        rec["payload"]["unit_price_minor"] = 1
        with open(jpath, "w") as f:
            f.write(json.dumps(rec) + "\n")
        with self.assertRaises(ValueError):
            routeseal.Store(self.path, POLICIES, KEYS,
                            licence_gate=gate)

    def test_legacy_counts_become_baseline_not_failure(self):
        gate = make_gate(self.tmp, FakeClient())
        st = routeseal.Store(self.path, POLICIES, KEYS,
                             licence_gate=gate)
        st.seal_dispatch(captures.capture())
        os.remove(self.path + ".metering.jsonl")
        st2 = routeseal.Store(self.path, POLICIES, KEYS,
                              licence_gate=gate)
        rec = st2.metering_reconcile()
        self.assertTrue(rec["reconciled"], rec)
        self.assertEqual(rec["baseline_by_op"], {"dispatch_seal": 1})
        self.assertEqual(rec["journal_records"], 0)

    def test_reload_reconciles(self):
        gate = make_gate(self.tmp, FakeClient())
        st = routeseal.Store(self.path, POLICIES, KEYS,
                             licence_gate=gate)
        st.seal_dispatch(captures.capture())
        st2 = routeseal.Store(self.path, POLICIES, KEYS,
                              licence_gate=gate)
        self.assertTrue(st2.metering_reconcile()["reconciled"])


if __name__ == "__main__":
    unittest.main()
