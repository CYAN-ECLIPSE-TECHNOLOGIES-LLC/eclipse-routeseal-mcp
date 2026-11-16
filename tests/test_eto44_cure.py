#!/usr/bin/env python3
# Cyan Eclipse Routeseal - ETO-44 cure regression tests (OPS-74).
# Copyright © 2026 Cyan Eclipse Technologies LLC · cetech.ai
"""Cure-delta regression tests for VERDICT-DELTA-ROUTESEAL-ETO44-
20261114 findings F-ETO44-1 (HIGH, metering re-baseline) and
F-ETO44-2 (MED, server-face gate wiring), plus COND-1 version
discipline. Each test names the finding leg it pins."""
import json
import os
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "fixtures"))

import routeseal  # noqa: E402
import captures  # noqa: E402

POLICIES = routeseal.load_policies(
    os.path.join(ROOT, "fixtures", "policies.json"))
KEYS = routeseal.load_adapter_keys(
    os.path.join(ROOT, "keys", "adapter-keys.json"))


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.path = os.path.join(self.tmp, "state.json")
        self.jpath = self.path + ".metering.jsonl"

    def build_two_ops(self):
        st = routeseal.Store(self.path, POLICIES, KEYS,
                             licence_gate=None)
        st.seal_dispatch(captures.capture(binding="evt-1"))
        st.seal_dispatch(captures.capture(binding="evt-2"))
        self.assertEqual(st.metering, {"dispatch_seal": 2})
        return st

    def strip_recorded_head(self):
        """Simulate a pre-cure (ETO-44-era) state file: metering
        counts + baseline keys as the old code wrote them, but no
        persisted metering head / record count."""
        with open(self.path, encoding="utf-8") as fh:
            data = json.load(fh)
        data.pop("metering_head", None)
        data.pop("metering_records", None)
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=1, sort_keys=True)


class TestF1MeteringRebaseline(Base):
    def test_f1_truncated_journal_fails_closed(self):
        self.build_two_ops()
        with open(self.jpath) as fh:
            lines = fh.readlines()
        self.assertEqual(len(lines), 2)
        with open(self.jpath, "w") as fh:
            fh.writelines(lines[:1])
        with self.assertRaises(ValueError):
            routeseal.Store(self.path, POLICIES, KEYS,
                            licence_gate=None)

    def test_f1_deleted_journal_fails_closed(self):
        self.build_two_ops()
        os.remove(self.jpath)
        with self.assertRaises(ValueError):
            routeseal.Store(self.path, POLICIES, KEYS,
                            licence_gate=None)

    def test_f1_inflated_state_count_fails_closed(self):
        self.build_two_ops()
        with open(self.path, encoding="utf-8") as fh:
            data = json.load(fh)
        data["metering"]["dispatch_seal"] = 5
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=1, sort_keys=True)
        with self.assertRaises(ValueError):
            routeseal.Store(self.path, POLICIES, KEYS,
                            licence_gate=None)

    def test_f1_state_file_persists_metering_head_and_count(self):
        self.build_two_ops()
        with open(self.path, encoding="utf-8") as fh:
            data = json.load(fh)
        self.assertEqual(data.get("metering_records"), 2)
        self.assertTrue(data.get("metering_head"))
        self.assertNotEqual(data["metering_head"], "0" * 64)

    def test_f1_genuine_legacy_state_baselines(self):
        """Pre-ETO-44 state: metering counts, NO journal file, NO
        recorded head. Must reconcile via the persisted baseline
        (the genuine legacy case the cure must keep working)."""
        self.build_two_ops()
        self.strip_recorded_head()
        with open(self.path, encoding="utf-8") as fh:
            data = json.load(fh)
        data.pop("metering_baseline", None)
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=1, sort_keys=True)
        os.remove(self.jpath)
        st = routeseal.Store(self.path, POLICIES, KEYS,
                             licence_gate=None)
        rec = st.metering_reconcile()
        self.assertTrue(rec["reconciled"], rec)
        self.assertEqual(rec["baseline_by_op"], {"dispatch_seal": 2})
        self.assertEqual(rec["journal_records"], 0)

    def test_f1_legacy_migration_is_once_only(self):
        """After a legacy state migrates (a further op saves the
        recorded head), deleting the journal must fail closed —
        the baseline cannot be re-adopted a second time."""
        self.build_two_ops()
        self.strip_recorded_head()
        with open(self.path, encoding="utf-8") as fh:
            data = json.load(fh)
        data.pop("metering_baseline", None)
        with open(self.path, "w", encoding="utf-8") as fh:
            json.dump(data, fh, indent=1, sort_keys=True)
        os.remove(self.jpath)
        st = routeseal.Store(self.path, POLICIES, KEYS,
                             licence_gate=None)
        st.seal_dispatch(captures.capture(binding="evt-3"))
        os.remove(self.jpath)
        with self.assertRaises(ValueError):
            routeseal.Store(self.path, POLICIES, KEYS,
                            licence_gate=None)

    def test_f1_precure_journal_migrates_and_truncation_fails(self):
        """Pre-cure state WITH an intact journal: migration adopts
        the journal's head/count once and reconciles exactly. The
        same state with the journal truncated by one record must
        fail closed — no baseline may be invented for journal-era
        ops."""
        self.build_two_ops()
        self.strip_recorded_head()
        st = routeseal.Store(self.path, POLICIES, KEYS,
                             licence_gate=None)
        self.assertTrue(st.metering_reconcile()["reconciled"])
        self.strip_recorded_head()
        with open(self.jpath) as fh:
            lines = fh.readlines()
        with open(self.jpath, "w") as fh:
            fh.writelines(lines[:1])
        with self.assertRaises(ValueError):
            routeseal.Store(self.path, POLICIES, KEYS,
                            licence_gate=None)


def run_server(tmp, extra_env):
    env = {k: v for k, v in os.environ.items()
           if not k.startswith("ROUTESEAL_LICENCE")}
    env["ECLIPSE_ROUTESEAL_STATE"] = os.path.join(tmp, "s.json")
    env.update(extra_env)
    proc = subprocess.Popen(
        [sys.executable, os.path.join(ROOT, "server.py")],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, text=True, env=env)

    def rpc(mid, method, params=None):
        msg = {"jsonrpc": "2.0", "id": mid, "method": method}
        if params is not None:
            msg["params"] = params
        proc.stdin.write(json.dumps(msg) + "\n")
        proc.stdin.flush()
        return json.loads(proc.stdout.readline())

    try:
        rpc(1, "initialize")
        out = rpc(2, "tools/call",
                  {"name": "routeseal_seal_dispatch",
                   "arguments": captures.capture(binding="wire-1")})
        return json.loads(out["result"]["content"][0]["text"])
    finally:
        proc.stdin.close()
        proc.wait(timeout=10)


class TestF2ServerWiring(unittest.TestCase):
    def test_f2_default_face_refuses_priced_op_unconfigured(self):
        res = run_server(tempfile.mkdtemp(), {})
        self.assertFalse(res["accepted"], res)
        self.assertEqual(res["error"], "LICENSE_NOT_CONFIGURED")

    def test_f2_fixture_bypass_is_explicit_opt_in(self):
        res = run_server(tempfile.mkdtemp(),
                         {"ROUTESEAL_LICENCE_FIXTURE_BYPASS": "1"})
        self.assertTrue(res["accepted"], res)
        self.assertEqual(res["verdict"], "AS-DECLARED")


class TestCond1Version(unittest.TestCase):
    def test_cond1_version_bumped_past_010_and_agrees(self):
        with open(os.path.join(ROOT, "VERSION"),
                  encoding="utf-8") as fh:
            version = fh.read().strip()
        self.assertNotEqual(version, "0.1.0")
        self.assertEqual(routeseal.TOOL_VERSION, version)


if __name__ == "__main__":
    unittest.main()
