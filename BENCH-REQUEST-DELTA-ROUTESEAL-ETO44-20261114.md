PROPRIETARY — CYAN ECLIPSE TECHNOLOGIES LLC · COMPANY INTELLECTUAL PROPERTY

# (INT — INTERNAL) BENCH REQUEST DELTA — Cyan Eclipse Routeseal, ETO-44 licence-checked metering

- Filed: 2026-11-14 · Seat: ETO-44 metering lane (Leg 3) · Slate: ETO-44 tkt-b24d8dbdffd3 (Routeseal parent ETO-11 tkt-7b2d3a042eb4)
- Subject: Routeseal per-op licence-checked metering ($0.25/op, PC-8), repo CYAN-ECLIPSE-TECHNOLOGIES-LLC/eclipse-routeseal-mcp, maintenance home Shard E /home/witness/app-family/cyan-eclipse-routeseal
- Commits: 5316633 (metering leg) · 502d6c6 (legacy-baseline fix) · 7cb2eaa (proof re-run tolerance), all pushed to main
- Scope: fixture/test only. No real customer licences, no Stripe, no real charges. Nothing is claimed production, live-for-customers, or certified. Builder evidence below is NOT a verdict.

## What changed

- licence_gate.py (new): ACT/Folio L-3 pattern gate vs the deployed License Server (Shard E 127.0.0.1:8799, tenant cet fixture scope). Activation-once with install_id binding, check-in per priced op, LICENSE_VALID/LICENSE_GRACE only; check-in presents activation token + artefact hash only.
- metering_journal.py (new): ACT/SCA-pattern append-only hash-chained JSONL. One record per priced op that meters under the pre-existing classes (dispatch_seal with verdict AS-DECLARED/DEVIATION), payload {product, op, subject, unit_price_minor 25, currency USD, fixture true, licence_state}.
- routeseal.py: Store takes optional licence_gate; seal_dispatch checks the gate before any record/receipt/metering is made (refusal returns {accepted False, error <licence state>, reason licence_gate_refused}); existing metering counts now also append metering-journal records at the exact pre-existing increment point (idempotent replay, CANDIDATE-SET-ABSENT, UNVERIFIABLE and rejections still never meter). Metering journal is a separate file: it never feeds record seals or verdicts; seal/journal tamper cures (VERDICT-DELTA-20261113 F1/F2/F3) untouched.
- Load behaviour: metering journal chain is verified at load and fails closed on tamper (new test). Pre-ETO-44 counts (legacy data state) become a persisted metering_baseline at load: reconciled == (journal counts + baseline == store counts); a journal recording ops the store never counted fails closed.
- server.py: wires a gate whenever ROUTESEAL_LICENCE_STATE is configured or ROUTESEAL_LICENCE_REQUIRED=1 (then an absent licence state refuses with LICENSE_NOT_CONFIGURED). GAP, stated plainly: an MCP process started with neither env set runs in unconfigured fixture mode (gate absent; metering journal still written) — the ACT core pattern. The bench is asked to judge whether that wiring satisfies ETO-44 or whether default-enforced is required.
- tests/test_licence_metering.py (new, 9 tests): fake-transport gate — valid op succeeds + reconciles · no licence refused + unmetered · revoked refused at check-in · reads never gated · idempotent replay = 1 record · unmetered verdict = 0 records · metering-journal tamper fails closed at load · legacy baseline · reload reconciles. No existing test was modified.
- fixtures/licence_proof.py (new): live proof driver vs the deployed server (see evidence).

## Builder evidence (not a verdict)

- Suite: 53/53 unittest OK on Shard E, run twice consecutively (44 pre-existing + 9 new); smoke.py PASS.
- Live fixture proof (evidence/routeseal-licence-evidence.json in the ETO-44 leg folder; driver in repo fixtures/): all 6 assertions true — op without licence refused LICENSE_NOT_CONFIGURED · 2 ops with valid fixture licence accepted (AS-DECLARED + DEVIATION) · reconcile ops_counted 2 == journal_records 2 (metering journal seqs 1–2, chain head in evidence) · after revoke, next op refused LICENSE_REVOKED · refused ops unmetered · read after revoke served.
- License Server journal (tenant cet): first proof run counts 138 → 142 (register/tier/mandate/issue) → 144 (revoke propose+exec); filed evidence is the clean re-run, counts 150 → 152 → 154, fixture licence 52add9bf-5c34-437c-af4a-d1e78d76a894 (revoked in the proof). First-run licence 19006938-b3a0-49f3-9c6e-e5c224df86c2 also revoked in its proof.

## Claims for independent verification

- M1: a priced op with no licence state is refused, creates no record/receipt, and writes no metering record.
- M2: a priced op with a valid fixture licence succeeds; metering counts == metering journal records, per op class, with the chain verifying.
- M3: after licence revocation, the next priced op is refused LICENSE_REVOKED at check-in; reads/check/export/recompute remain served.
- M4: pre-existing metering classes are unchanged (replay, ABSENT, UNVERIFIABLE, rejections unmetered) and the F1/F2/F3 tamper cures still refuse tampered records at load and in recompute.
- M5: a tampered metering journal fails closed at load; legacy pre-journal counts reconcile via the persisted baseline and cannot hide journal-recorded ops.
- M6: the gate presents only activation token + artefact hash at check-in (no usage/content data), per the Folio L-3 pattern.

© Cyan Eclipse Technologies LLC — Proprietary · Company Intellectual Property
