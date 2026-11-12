PROPRIETARY — CYAN ECLIPSE TECHNOLOGIES LLC · COMPANY INTELLECTUAL PROPERTY

# (INT — INTERNAL) BENCH REQUEST — Cyan Eclipse Routeseal v0.1.0 (build delta)

- Filed: 2026-11-11 · Seat: builder lane (Routeseal build 1 of the Argus trio)
- Subject: Cyan Eclipse Routeseal v0.1.0 — repo `CYAN-ECLIPSE-TECHNOLOGIES-LLC/eclipse-routeseal-mcp`, maintenance home Shard E `/home/witness/app-family/cyan-eclipse-routeseal`
- Spec of record: SPEC-ROUTESEAL.md (RTE-REQ-001…016; Loom project 32, req ids 1777–1792, CANDIDATE, verdicts not-run)
- Gate: argus-gate-routeseal-20261111.md — PASS-WITH-CONDITIONS (RT-C1…RT-C9)
- Builder evidence (NOT a verdict): unit suite 34/34 on the droplet + MCP smoke PASS; transcript `evidence/TRANSCRIPT-20261111.txt`

## Claims for independent verification (spec §6, restated)

- **C1 / RT-B1 (RTE-REQ-010, RTE-REQ-002):** fixtures whose sealed selection violates the stated routing policy verdict DEVIATION naming the clause, the selected target, and the passed-over preferred candidate; policy-conformant controls verdict AS-DECLARED — 100% of fixtures, across all five clause classes (preference order · affiliation flagging · affiliation exclusion · capability match · cost/latency bounds).
- **C2 / RT-B2 (RTE-REQ-002(iii), RTE-REQ-013):** a verifier holding only the sealed bundle + the published grammar (GRAMMAR.md) + the stated policy reproduces the verdict with no service access.
- **C3 / RT-B3 (RTE-REQ-004, RTE-REQ-011):** decision-only fixtures verdict CANDIDATE-SET-ABSENT and below-standard fixtures verdict UNVERIFIABLE in 100% of cases; no DEVIATION is mintable from either.
- **C4 / RT-B4 (RTE-REQ-005):** the store, inspected directly, contains only the §2 field set — no task bodies, no tool outputs, no cross-operator tables or code paths (RTE-REQ-006).
- **C5 / RT-B5 (RTE-REQ-007):** verdicts name their grammar version and the routing-policy version in force; a later revision of either never retro-alters a minted verdict (byte-identical records).
- **C6 / ADV-1 (RTE-REQ-012, RT-K1 guard):** a capture relayed from a platform's own trace/log export is detected as a provenance failure, rejected, and receipted; no AS-DECLARED or DEVIATION verdict is mintable in that configuration across all API paths; the dispatch caps at UNVERIFIABLE.
- **C7 / ADV-2 (RTE-REQ-011):** a candidate list reconstructed after the fact and attached to a decision-only seal is refused as capture material, the refusal receipted, and the sealed record stands unchanged at CANDIDATE-SET-ABSENT.
- **C8 (RTE-REQ-014):** the receipt journal verifies end-to-end; a tampered record and a truncated export (chain-head mismatch) are both detected; a tampered store fails closed at load.
- **C9 (RTE-REQ-015):** metering charges exactly one op per dispatch seal (AS-DECLARED / DEVIATION); CANDIDATE-SET-ABSENT, UNVERIFIABLE, rejections, recompute, and check never meter; the ledger records event class + count only.
- **C10 (RTE-REQ-013, RTE-REQ-009):** the MCP tool inventory equals SPEC §4.1 exactly; `routeseal_check` reveals verdict class + named clause only; no §5 banned term appears on any output surface.

## Fences the bench is asked to hold the build to

Buyer-side dispatch-point witnessing only — no claim over any closed platform's internal routing, no motive or intent language anywhere, no cross-operator aggregation surface. Claims stay **bench-pending** until Verity's verdict lands; builder tests are not evidence.

© Cyan Eclipse Technologies LLC — Proprietary · Company Intellectual Property
