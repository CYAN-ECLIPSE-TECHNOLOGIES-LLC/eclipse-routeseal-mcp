PROPRIETARY — CYAN ECLIPSE TECHNOLOGIES LLC · COMPANY INTELLECTUAL PROPERTY

# (INT — INTERNAL) BUILD RECORD — Cyan Eclipse Routeseal v0.1.0

- Built: 2026-11-11 · Build authority: owner commission 2026-11-11 17:08 PT (Argus trio builds, serial per P-2, Routeseal first, starting after the Loom Windows demo shipped — installer built + staged 2026-11-11). RTE-REQ-001 is satisfied by that commission; the SPEC itself conferred no build slot.
- Spec of record: SPEC-ROUTESEAL.md (this repo) · Gate: argus-gate-routeseal-20261111.md, PASS-WITH-CONDITIONS, narrowings binding.
- Estate: maintenance home Shard E `/home/witness/app-family/cyan-eclipse-routeseal` · GitHub `CYAN-ECLIPSE-TECHNOLOGIES-LLC/eclipse-routeseal-mcp` (MIT LICENSE in first commit).
- Shape: stdlib-only Python MCP server over stdio (`server.py`), pure verdict engine (`logic.py`), store/provenance/receipt/metering layer (`routeseal.py`). Exactly the five §4.1 tools.

## What was built, per requirement

- RTE-REQ-002 — three-part mechanism held jointly: adapter-channel sealing at dispatch · verdict under the published grammar (GRAMMAR.md, `routeseal-grammar/1`) · stateless third-party recomputation (`routeseal_recompute`).
- RTE-REQ-003 — no listing, quote, pilot, or checkout artefact exists; metering is event-class counts only (no price row adopted; PC-8 pattern fit is a gate fact, not a build feature).
- RTE-REQ-004 — minimum sealed bundle enforced; below-standard → UNVERIFIABLE; decision-only → CANDIDATE-SET-ABSENT; surfaces claim the dispatch record only.
- RTE-REQ-005 — record store field set is exactly the §2 set (asserted in code + test); candidates reduced at the door to the grammar's five routing facts; task bodies never enter the module.
- RTE-REQ-006 — no aggregation code path or tool exists (inventory test).
- RTE-REQ-007 — verdicts name grammar + policy versions; revision non-retroactivity tested byte-identical.
- RTE-REQ-008 — WATCH.md records the RT-C8 trigger class; reviewed at build, no triggering shipment known.
- RTE-REQ-009 — claim line verbatim in README + seal tool description; §2 verdict vocabulary only; banned-term scan in the suite.
- RTE-REQ-010 — grammar published (GRAMMAR.md) with all five clause classes; DEVIATION names clause + selected + passed-over preferred.
- RTE-REQ-011 — DEVIATION is structurally unreachable without a sealed candidate set; after-the-fact candidate attach refused + receipted (ADV-2).
- RTE-REQ-012 — captures accepted only via the dispatch-point adapter channel (source + per-point HMAC attestation + binding ref); platform-log and relay captures rejected + receipted (ADV-1).
- RTE-REQ-013 — tool inventory == §4.1 exactly; `routeseal_check` returns verdict + clause only; recompute runs with no service state.
- RTE-REQ-014 — hash-chained receipt journal, one receipt per seal/verdict event and per rejection/refusal; exports carry the chain head; tamper + truncation detected; tampered store fails closed at load.
- RTE-REQ-015 — one metered op per dispatch seal (AS-DECLARED / DEVIATION); CANDIDATE-SET-ABSENT / UNVERIFIABLE / rejections / recompute / check unmetered; ledger = class + count only.
- RTE-REQ-016 — branding applied at creation (branding/BRANDING.md): composite wordmark, canonical theme tokens, server identity surfaces. **Icon: DRAFT candidate only (branding/icon-candidate.svg), NOT approved, NOT shipped, NOT public — builds carry a placeholder posture; owner approval is the outstanding gate.**

## Verification (builder-side; bench verdict is Verity's)

- Unit suite: **34/34 PASS** on the droplet (python3 -m unittest, tests/test_routeseal.py; each test names its requirement / bench claim).
- MCP smoke over real stdio JSON-RPC: **PASS** (tools list · AS-DECLARED · DEVIATION · CANDIDATE-SET-ABSENT · platform-log rejection · check · export · recompute reproduced). Transcript: evidence/TRANSCRIPT-20261111.txt.
- Bench: BENCH-REQUEST-DELTA.md filed with this record (claims C1–C10 ← RT-B1…B5, ADV-1/2, RTE-REQ-014/015/013). Claims are **bench-pending**.

## What this build does NOT do (gate narrowings, honored by construction)

No witnessing of closed-platform internal routing · no intent/motive verdicts or language · decision-only captures mint CANDIDATE-SET-ABSENT only (candidate sets never inferred/reconstructed/attached later) · no cross-operator aggregation, statistics, feeds, or dossiers · no task-body or tool-output custody · no routing/enforcement (it witnesses dispatch; it never routes) · no listing, directory submission, public launch, or pricing/checkout wiring.

## Open items / gaps

- Icon owner approval outstanding (draft candidate only).
- TM screen for the name (RT-CQ-3) and counsel queue RT-CQ-1/2 remain open; name stays provisional.
- Slate ETO-11: this seat's Slate API route returns "no valid directory session" (same limitation recorded by sibling lanes), so the progress/completion comments could not be posted from the build seat. Comment text for ETO-11, ready for the main seat to post verbatim:
  - Progress: "Routeseal build started 2026-11-11 under owner commission 17:08 PT (post-Loom-demo sequence). Building to SPEC-ROUTESEAL RTE-REQ-001…016 on Shard E; GitHub repo eclipse-routeseal-mcp."
  - Completion: "Routeseal v0.1.0 build complete 2026-11-11: suite 34/34 + MCP smoke PASS on droplet; GitHub == droplet; BENCH-REQUEST-DELTA filed (claims C1–C10), bench-pending; icon draft candidate only (owner approval outstanding); no listing/launch. Record: BUILD-RECORD.md in repo."
- Loom verifications for req 1777–1792 remain not-run (bench will move them; nothing fabricated here).

© Cyan Eclipse Technologies LLC — Proprietary · Company Intellectual Property
