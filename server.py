#!/usr/bin/env python3
# Cyan Eclipse Routeseal MCP server (spec: SPEC-ROUTESEAL section 4.1).
# Copyright © 2026 Cyan Eclipse Technologies LLC · cetech.ai
"""MCP over stdio (newline-delimited JSON-RPC 2.0), stdlib only.

Exactly the five section 4.1 tools. There is no aggregation tool,
no candidate-set amendment tool, and no routing tool — such names
return the identical NO_SUCH_TOOL refusal as nonsense names, by
absence (RT-C6, RTE-REQ-011, spec section 7 non-goals).
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import routeseal  # noqa: E402

SERVER_NAME = "eclipse-routeseal"
SERVER_VERSION = routeseal.TOOL_VERSION
_STR = {"type": "string"}
_OBJ = {"type": "object"}


def _obj(props, required):
    return {"type": "object", "properties": props,
            "required": required, "additionalProperties": False}


DESCRIPTIONS = {
    "routeseal_seal_dispatch":
        "Seal a routing decision at a buyer-controlled dispatch "
        "point, through the dispatch-point adapter channel with "
        "the adapter's attestation, and mint the verdict under the "
        "operator's stated routing policy. One metered op per "
        "dispatch seal; decision-only and below-standard captures "
        "do not meter. " + routeseal.CLAIM,
    "routeseal_get_verdict":
        "The full verdict record for a dispatch seal: verdict, "
        "named clause, selected target, policy-preferred candidate "
        "passed over, grammar and policy versions, receipt refs. "
        "Unmetered.",
    "routeseal_check":
        "Counterparty view: the verdict class and the named clause "
        "only. Unmetered.",
    "routeseal_recompute":
        "Recompute a verdict from an exported capture plus the "
        "grammar and policy versions, with no service state. "
        "Unmetered.",
    "routeseal_export_captures":
        "Export a sealed capture with the receipt chain head and "
        "the grammar and policy versions, for independent "
        "recomputation. Unmetered.",
}

_CAND = _obj({"id": _STR,
              "affiliated": {"type": "boolean"},
              "capabilities": {"type": "array",
                               "items": _STR},
              "cost": {"type": "number"},
              "latency_ms": {"type": "number"}}, ["id"])

SCHEMAS = {
    "routeseal_seal_dispatch": _obj({
        "task_digest": _STR,
        "candidate_set": {"type": ["array", "string"],
                          "items": _CAND},
        "selected_target": _STR,
        "stated_reason": _STR,
        "policy_version": _STR,
        "affiliation_flags": _OBJ,
        "dispatch_point_id": _STR,
        "dispatch_timestamp": _STR,
        "binding_ref": _STR,
        "source": _STR,
        "adapter_attestation": _STR},
        ["task_digest", "selected_target", "stated_reason",
         "policy_version", "dispatch_point_id", "dispatch_timestamp",
         "binding_ref", "source", "adapter_attestation"]),
    "routeseal_get_verdict": _obj({"dispatch_seal_id": _STR},
                                  ["dispatch_seal_id"]),
    "routeseal_check": _obj({"dispatch_seal_id": _STR},
                            ["dispatch_seal_id"]),
    "routeseal_recompute": _obj({
        "dispatch_capture": _OBJ, "grammar_version": _STR,
        "policy_version": _STR},
        ["dispatch_capture", "grammar_version", "policy_version"]),
    "routeseal_export_captures": _obj({"dispatch_seal_id": _STR},
                                      ["dispatch_seal_id"]),
}

_store = None
_policies = {}


def store() -> routeseal.Store:
    global _store
    if _store is None:
        base = os.path.dirname(os.path.abspath(__file__))
        state = os.environ.get(
            "ECLIPSE_ROUTESEAL_STATE",
            os.path.join(base, "data", "routeseal-state.json"))
        os.makedirs(os.path.dirname(state), exist_ok=True)
        policies_path = os.environ.get(
            "ECLIPSE_ROUTESEAL_POLICIES",
            os.path.join(base, "fixtures", "policies.json"))
        keys_path = os.environ.get(
            "ECLIPSE_ROUTESEAL_ADAPTER_KEYS",
            os.path.join(base, "keys", "adapter-keys.json"))
        global _policies
        _policies = routeseal.load_policies(policies_path)
        _store = routeseal.Store(
            state, _policies, routeseal.load_adapter_keys(keys_path))
    return _store


def call_tool(name: str, args: dict):
    if name not in SCHEMAS:
        return {"error": "NO_SUCH_TOOL"}
    st = store()
    if name == "routeseal_seal_dispatch":
        return st.seal_dispatch(args)
    if name == "routeseal_get_verdict":
        return st.get_verdict(args["dispatch_seal_id"])
    if name == "routeseal_check":
        return st.check(args["dispatch_seal_id"])
    if name == "routeseal_recompute":
        return routeseal.recompute(args["dispatch_capture"],
                                   args["grammar_version"],
                                   args["policy_version"], _policies)
    if name == "routeseal_export_captures":
        return st.export_capture(args["dispatch_seal_id"])
    return {"error": "NO_SUCH_TOOL"}


def handle(msg: dict):
    method = msg.get("method")
    if method == "initialize":
        return {"protocolVersion": "2024-11-05",
                "capabilities": {"tools": {}},
                "serverInfo": {"name": SERVER_NAME,
                               "version": SERVER_VERSION}}
    if method == "tools/list":
        return {"tools": [{"name": n, "description": DESCRIPTIONS[n],
                           "inputSchema": SCHEMAS[n]}
                          for n in SCHEMAS]}
    if method == "tools/call":
        params = msg.get("params", {})
        result = call_tool(params.get("name"), params.get("arguments", {}))
        return {"content": [{"type": "text",
                             "text": json.dumps(result,
                                                sort_keys=True)}],
                "isError": "error" in result}
    if method and method.startswith("notifications/"):
        return None
    return {"error": "NO_SUCH_METHOD"}


def main():
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        result = handle(msg)
        if result is not None and "id" in msg:
            sys.stdout.write(json.dumps(
                {"jsonrpc": "2.0", "id": msg["id"],
                 "result": result}) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
