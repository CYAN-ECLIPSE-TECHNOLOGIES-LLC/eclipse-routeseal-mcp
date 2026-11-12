# Cyan Eclipse Routeseal

**Powered by Cyan Eclipse Technologies** — https://cetech.ai

![Cyan Eclipse Routeseal icon](branding/icon.svg)

*Icon: `branding/icon.svg` — v3, owner-elected 2026-11-12 (Tap 45). Icongate PASS: legible at 48 px and 32 px (cap 4.94 px @48 · 3.29 px @32).*

Routeseal seals the routing decision at the moment of dispatch —
the task, the candidates the router passed over, the target it
chose, and the reason it stated. If the choice diverged from your
stated routing policy, or picked an affiliated target over the
policy's preferred candidate, the sealed record says so, and
anyone can recompute the verdict from the record itself.

Cyan Eclipse Routeseal is a Model Context Protocol (MCP) server.
It operates at a dispatch point the buyer or operator controls —
their own gateway, proxy, or orchestration harness through which
agent tasks are routed. At dispatch, the buyer's dispatch-point
adapter presents the routing decision: the task digest, the
candidate set as presented to the router, the selected target, the
stated selection reason, and the routing-policy version in force.
Routeseal seals that bundle and mints a verdict under the
published routing-policy grammar (`GRAMMAR.md`): **AS-DECLARED**
(the selection conforms to the stated policy), **DEVIATION**
(naming the clause diverged from, the selected target, and the
policy-preferred candidate passed over),
**CANDIDATE-SET-ABSENT** (decision sealed; no candidate set was
presented — no steering verdict is mintable), or **UNVERIFIABLE**
(capture below the sealed-bundle standard).

Routeseal claims the dispatch record only. It does not witness
any platform's internal routing, and its verdicts state a
divergence from a stated policy — never a reason anyone acted.
Captures are accepted only through the buyer-side dispatch-point
adapter channel, carrying the adapter's attestation and a binding
reference to the dispatch event; platform-produced traces, logs,
or observability exports are rejected as capture material and the
rejection is receipted.

## Tools

| Tool | What it does |
|---|---|
| `routeseal_seal_dispatch` | Present a dispatch capture through the adapter channel; seal the bundle and mint the verdict. Metered: one op per dispatch seal (PC-8 pattern); CANDIDATE-SET-ABSENT and UNVERIFIABLE captures do not meter. |
| `routeseal_get_verdict` | The full verdict record: verdict, named clause, selected target, passed-over preferred candidate, grammar + policy versions, receipt refs. Unmetered. |
| `routeseal_check` | Counterparty view: verdict class and named clause only. Unmetered. |
| `routeseal_recompute` | Recompute a verdict from an exported capture + grammar/policy versions, with no service state. Unmetered. |
| `routeseal_export_captures` | Export a sealed capture with the receipt-chain head for independent recomputation. Unmetered. |

## Custody

The store carries only the sealed routing field set: task digests
(task bodies are digested transiently and never retained),
candidate identifiers as presented, the selected target, the
stated selection reason as declared, the routing-policy version
digest, declared affiliation flags, timestamps, seals, and the
verdict with its named grammar basis. No tool outputs, no
principal data beyond the routing facts the grammar names. Records
serve the operator whose dispatch point sealed them; there is no
cross-operator aggregation surface. Every seal and verdict appends
one record to a hash-chained receipt journal, verified at load; a
store that fails verification fails closed.

## Status

v0.1.0 · built · **bench-pending** (independent bench requested;
builder tests are not a bench verdict) · name "Cyan Eclipse
Routeseal" is provisional pending trademark screen · not listed,
not offered for sale — review-first standing posture.

## Run

```sh
python3 server.py   # MCP over stdio
```

Environment: `ECLIPSE_ROUTESEAL_STATE` (record store path),
`ECLIPSE_ROUTESEAL_POLICIES` (operator's stated routing policies,
JSON), `ECLIPSE_ROUTESEAL_ADAPTER_KEYS` (dispatch-point adapter
keys, JSON — operator-held in production; the keys in `keys/` are
test fixtures only).

## License

MIT — see `LICENSE`.
