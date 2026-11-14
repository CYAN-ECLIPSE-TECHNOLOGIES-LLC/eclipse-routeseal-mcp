#!/usr/bin/env python3
"""Routeseal fixture proof - ETO-44 licence-checked metering.

Drives the DEPLOYED Cyan Eclipse License Server (Shard E loopback,
tenant cet, fixture scope only) through its MCP stdio face:
product_register + tier_define + issuer mandate + license_issue,
then, against the deployed server's HTTP runtime face via the real
client library (ActivationClient, Folio L-3 pattern):
  1. priced op with NO licence state -> refused LICENSE_NOT_CONFIGURED
  2. priced ops with the fixture licence -> succeed, metering
     journal records reconcile with the store's metering counts
  3. license_revoke -> next priced op refused LICENSE_REVOKED at
     check-in; reads still served
Evidence JSON to argv[1]. No real licences, no charges: metering
records are fixture counts at the adopted $0.25/op (PC-8)."""
import json
import os
import subprocess
import sys
import tempfile
import uuid

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "fixtures"))
LS_HOME = "/home/witness/app-family/cyan-eclipse-license-server"
LS_RUNTIME = "/home/witness/app-family/cyan-eclipse-license-server-runtime"
PRODUCT = "routeseal"
OUT = sys.argv[1] if len(sys.argv) > 1 else "/tmp/routeseal-licence-evidence.json"
EVID = {"product": PRODUCT, "fixture": True, "unit_price_minor": 25,
        "license_server": "Shard E 127.0.0.1:8799, tenant cet"}


class Mcp:
    def __init__(self):
        env = dict(os.environ, PYTHONPATH=os.path.join(LS_HOME, "src"),
                   CETLIC_RUNTIME_DIR=LS_RUNTIME,
                   PYTHONDONTWRITEBYTECODE="1")
        self.p = subprocess.Popen([sys.executable, "-m", "license_server"],
                                  stdin=subprocess.PIPE,
                                  stdout=subprocess.PIPE, text=True,
                                  env=env, cwd=LS_HOME)
        self.n = 0
        self.call("initialize", {"protocolVersion": "2025-03-26",
                                 "capabilities": {}, "clientInfo": {
                                     "name": "routeseal-eto44-proof",
                                     "version": "0.1.0"}})

    def call(self, method, params):
        self.n += 1
        self.p.stdin.write(json.dumps({"jsonrpc": "2.0", "id": self.n,
                                       "method": method,
                                       "params": params}) + "\n")
        self.p.stdin.flush()
        return json.loads(self.p.stdout.readline())

    def tool(self, name, args, tenant="cet", principal="cet-owner"):
        r = self.call("tools/call", {"name": name, "arguments": {
            **args, "_tenant_id": tenant, "_principal_id": principal}})
        res = r.get("result") or {}
        sc = res.get("structuredContent")
        if sc is None:
            sc = json.loads((res.get("content") or [{}])[0].get("text", "{}"))
        return sc, bool(res.get("isError"))

    def journal_count(self):
        out, _ = self.tool("journal_info", {})
        return out.get("count") or out.get("receipts") or out

    def close(self):
        self.p.terminate()


def propose_run(mcp, propose_tool, args, exec_tool, verb, principal):
    prop, err = mcp.tool(propose_tool, args, principal=principal)
    assert not err and "proposal_id" in prop, prop
    tok = f"confirm-{prop.get('kind', verb)}-{prop['proposal_id']}-{prop['proposal_hash'][:12]}"
    out, err = mcp.tool(exec_tool, {"proposal_id": prop["proposal_id"],
                                    "confirm_token": tok},
                        principal=principal)
    assert not err, out
    return out


def main():
    import captures
    import routeseal
    from licence_gate import LicenceGate

    policies = routeseal.load_policies(
        os.path.join(ROOT, "fixtures", "policies.json"))
    keys = routeseal.load_adapter_keys(
        os.path.join(ROOT, "keys", "adapter-keys.json"))
    tmp = tempfile.mkdtemp(prefix="routeseal-eto44-")
    mcp = Mcp()
    try:
        EVID["ls_journal_count_start"] = mcp.journal_count()
        reg, err = mcp.tool("product_register", {
            "product_id": PRODUCT, "name": "Cyan Eclipse Routeseal",
            "custody": "witness"})
        EVID["product_register"] = {"is_error": err, "result": reg}
        tier, err = mcp.tool("tier_define", {
            "product_id": PRODUCT, "tier_id": "fixture",
            "features": ["dispatch_seal"], "seats": 1, "perpetual": True})
        EVID["tier_define"] = {"is_error": err, "result": tier}
        mand, err = mcp.tool("principal_manage", {
            "action": "grant_mandate", "principal_id": "cet-issuer",
            "products": [PRODUCT],
            "op_classes": ["issue", "renew", "revoke", "supersede",
                           "transfer", "deactivate", "reclaim"],
            "expires_at": "2027-11-13T00:00:00Z"})
        EVID["issuer_mandate_grant"] = {"is_error": err, "result": mand}
        mint = propose_run(mcp, "license_issue_propose", {
            "product_id": PRODUCT, "tier_id": "fixture",
            "licensee": {"name": "Routeseal Fixture Desk",
                         "email": "fixtures@cetech.ai"},
            "seats": 1, "perpetual": True},
            "license_issue", "issue", "cet-issuer")
        artefact = mint["artefact"]
        license_id = mint["license_id"]
        EVID["license_issue"] = {"license_id": license_id,
                                 "has_artefact": bool(artefact)}
        EVID["ls_journal_count_after_issue"] = mcp.journal_count()

        # 1. no licence -> refused, unmetered
        absent_gate = LicenceGate(state_path=os.path.join(tmp, "none.json"))
        st0 = routeseal.Store(os.path.join(tmp, "s0.json"), policies,
                              keys, licence_gate=absent_gate)
        out0 = st0.seal_dispatch(captures.capture(binding="eto44-none"))
        EVID["op_without_licence"] = out0
        EVID["without_licence_metering"] = st0.metering_reconcile()

        # 2. valid licence -> ops succeed, metering reconciles
        state_path = os.path.join(tmp, "licence-state.json")
        with open(state_path, "w") as f:
            json.dump({"artefact": artefact,
                       "install_id": str(uuid.uuid4()),
                       "install_label": "routeseal-eto44-proof"}, f)
        gate = LicenceGate(state_path=state_path)
        st = routeseal.Store(os.path.join(tmp, "s1.json"), policies,
                             keys, licence_gate=gate)
        r1 = st.seal_dispatch(captures.capture(binding="eto44-1"))
        r2 = st.seal_dispatch(captures.capture(
            selected="beta", binding="eto44-2"))
        EVID["ops_with_valid_licence"] = [
            {"accepted": r1.get("accepted"), "verdict": r1.get("verdict"),
             "dispatch_seal_id": r1.get("dispatch_seal_id")},
            {"accepted": r2.get("accepted"), "verdict": r2.get("verdict"),
             "dispatch_seal_id": r2.get("dispatch_seal_id")}]
        EVID["gate_state_after_ops"] = gate.state.get("license_id")
        EVID["metering_reconcile"] = st.metering_reconcile()
        EVID["metering_journal_records"] = [
            {"seq": r["seq"], "kind": r["kind"], "subject": r["subject"],
             "payload": r["payload"], "hash": r["hash"]}
            for r in st.metering_journal.read_all()]
        seal_id = r1.get("dispatch_seal_id")

        # 3. revoke -> next priced op refused; reads still served
        rev = propose_run(mcp, "license_revoke_propose", {
            "license_id": license_id,
            "reason": "routeseal eto44 fixture proof complete"},
            "license_revoke", "revoke", "cet-issuer")
        EVID["license_revoke"] = rev
        EVID["ls_journal_count_after_revoke"] = mcp.journal_count()
        out3 = st.seal_dispatch(captures.capture(binding="eto44-3"))
        EVID["op_after_revoke"] = out3
        EVID["metering_after_revoke"] = st.metering_reconcile()
        EVID["read_after_revoke"] = st.get_verdict(seal_id)
    finally:
        mcp.close()
    EVID["assertions"] = {
        "without_licence_refused": EVID["op_without_licence"].get(
            "error") == "LICENSE_NOT_CONFIGURED",
        "valid_ops_accepted": all(
            o["accepted"] for o in EVID["ops_with_valid_licence"]),
        "ops_counted_eq_journal_records":
            EVID["metering_reconcile"]["ops_counted"] ==
            EVID["metering_reconcile"]["journal_records"] == 2,
        "after_revoke_refused": EVID["op_after_revoke"].get(
            "error") == "LICENSE_REVOKED",
        "no_metering_for_refused_ops":
            EVID["metering_after_revoke"]["ops_counted"] == 2,
        "read_after_revoke_served": EVID["read_after_revoke"].get(
            "verdict") == "AS-DECLARED"}
    with open(OUT, "w") as f:
        json.dump(EVID, f, indent=1, default=str)
    print(json.dumps(EVID["assertions"], indent=1))


if __name__ == "__main__":
    main()
