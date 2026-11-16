#!/usr/bin/env python3
# Cyan Eclipse Routeseal — MCP smoke transcript.
# Copyright © 2026 Cyan Eclipse Technologies LLC · cetech.ai
"""Drives the real server over stdio JSON-RPC: tools/list, a
conformant seal, a deviation seal, a decision-only seal, a
platform-log rejection, check, export, and an offline recompute.
Exits non-zero on any mismatch."""
import json
import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "fixtures"))
import captures  # noqa: E402


def rpc(proc, mid, method, params=None):
    msg = {"jsonrpc": "2.0", "id": mid, "method": method}
    if params is not None:
        msg["params"] = params
    proc.stdin.write(json.dumps(msg) + "\n")
    proc.stdin.flush()
    return json.loads(proc.stdout.readline())


def call(proc, mid, name, args):
    out = rpc(proc, mid, "tools/call",
              {"name": name, "arguments": args})
    return json.loads(out["result"]["content"][0]["text"])


def main():
    tmp = tempfile.mkdtemp()
    env = dict(os.environ,
               ECLIPSE_ROUTESEAL_STATE=os.path.join(tmp, "s.json"),
               # F-ETO44-2: the server face is licence-gated by
               # default; the smoke runs ungated only via the
               # explicit fixture bypass opt-in.
               ROUTESEAL_LICENCE_FIXTURE_BYPASS="1")
    proc = subprocess.Popen(
        [sys.executable, os.path.join(HERE, "server.py")],
        stdin=subprocess.PIPE, stdout=subprocess.PIPE,
        text=True, env=env)
    try:
        init = rpc(proc, 1, "initialize")
        assert init["result"]["serverInfo"]["name"] == \
            "eclipse-routeseal", init
        tools = rpc(proc, 2, "tools/list")
        names = [t["name"] for t in tools["result"]["tools"]]
        assert names == ["routeseal_seal_dispatch",
                         "routeseal_get_verdict", "routeseal_check",
                         "routeseal_recompute",
                         "routeseal_export_captures"], names
        ok = call(proc, 3, "routeseal_seal_dispatch",
                  captures.capture(binding="smoke-1"))
        assert ok["verdict"] == "AS-DECLARED", ok
        dev = call(proc, 4, "routeseal_seal_dispatch",
                   captures.capture(selected="beta",
                                    binding="smoke-2"))
        assert dev["verdict"] == "DEVIATION", dev
        absent = call(proc, 5, "routeseal_seal_dispatch",
                      captures.capture(candidates="ABSENT",
                                       binding="smoke-3"))
        assert absent["verdict"] == "CANDIDATE-SET-ABSENT", absent
        rej = call(proc, 6, "routeseal_seal_dispatch",
                   captures.capture(source="platform-log-export",
                                    binding="smoke-4"))
        assert rej["accepted"] is False and \
            rej["verdict"] == "UNVERIFIABLE", rej
        view = call(proc, 7, "routeseal_check",
                    {"dispatch_seal_id": dev["dispatch_seal_id"]})
        assert view == {"clause": "preference_order",
                        "verdict": "DEVIATION"}, view
        export = call(proc, 8, "routeseal_export_captures",
                      {"dispatch_seal_id": dev["dispatch_seal_id"]})
        assert export["chain_head"], export
        fresh = call(proc, 9, "routeseal_recompute",
                     {"dispatch_capture": export,
                      "grammar_version": export["grammar_version"],
                      "policy_version": "op-policy/1"})
        assert fresh["verdict"] == "DEVIATION", fresh
        print("SMOKE PASS: 5 tools · AS-DECLARED · DEVIATION · "
              "CANDIDATE-SET-ABSENT · platform-log rejected · "
              "check · export · recompute reproduced")
        return 0
    finally:
        proc.stdin.close()
        proc.wait(timeout=10)


if __name__ == "__main__":
    sys.exit(main())
