PROPRIETARY — CYAN ECLIPSE TECHNOLOGIES LLC · COMPANY INTELLECTUAL PROPERTY

# (INT — INTERNAL) BENCH REQUEST — Cyan Eclipse Routeseal cure delta (F1/F2/F3) for VERDICT-DELTA-20261113 FAIL

- Subject: Cyan Eclipse Routeseal v0.1.0 — cure delta against VERDICT-DELTA-20261113.md (CONTRACT: FAIL, fixture scope; F1 HIGH (C8) + F2 HIGH (C6) + F3 MED (C9/RTE-REQ-014) blocking; C1–C5/C7/C10 passed and are not re-claimed beyond regression)
- Filed: 2026-11-13 · Lane: Routeseal bench-FAIL cure lane (main-seat commission)
- Subject build / artefact: repo `CYAN-ECLIPSE-TECHNOLOGIES-LLC/eclipse-routeseal-mcp`, maintenance home Shard E `/home/witness/app-family/cyan-eclipse-routeseal`, HEAD a3d1d9e (GitHub main == Shard E == cure clone). Cure commits: fd4dfcf (F1) · 2c22e83 (F2) · a3d1d9e (F3), on top of the judged HEAD e81d323. routeseal.py sha256 2d79a8319025478db75f36a82788c65fda21bb7ecd6a5c2b6268dad9819870e2 · logic.py sha256 aa3daf3bb47eb05a5fb249214b4e9311787a70d1a206defdd0a2c515d346e6d8 (unchanged from judged build) · server.py sha256 03e92c6afa114417257a3e1ef363d6ed6bb663c4ecb681f51f3d74e2e3848f14.
- Claims: 4 (claim sheet appended below, standard form)
- User-facing surface: YES — MCP tools (five tools, SPEC §4.1 inventory unchanged)

## What is being benched

Three cure claims, each reproduced first-hand before curing (the verdict's probes re-run by the cure lane against judged HEAD e81d323 via probe_verdict.py in the repo root; all three CONFIRMED pre-cure, all three REFUSED post-cure):

- F1 (was C8 FAIL) — a store record tampered in the state file (verdict field flipped DEVIATION → AS-DECLARED, journal untouched) loaded silently and get_verdict served the tampered verdict. Cure: Store load, after the journal chain check, cross-verifies every record — the record's seal is recomputed over the bundle fields rebuilt from the record itself, and the payload_digest of the dispatch_seal receipt the record's receipt_ref names is checked against the record's seal + verdict. Any mismatch raises at load; the store fails closed and serves nothing.
- F2 (was C6 FAIL) — routeseal_recompute minted a full DEVIATION verdict from a fabricated, never-sealed capture dict. Cure: recompute recomputes the record's seal from the bundle fields it carries (and the seal_id's derivation from that seal) before evaluating; a capture whose seal does not verify caps at UNVERIFIABLE with the named reason seal_verification_failed. The seal-basis language now rides every recompute result and the tool description, plainly: the seal is an unkeyed digest binding the record's internal consistency only; provenance rests on the dispatch-point adapter channel at ingestion.
- F3 (was C9 + RTE-REQ-014 FAIL) — re-submitting the identical capture appended a second dispatch_seal receipt and metered a second op. Cure: idempotent seal — when the capture's seal_id already exists, seal_dispatch returns the existing record (flagged idempotent_replay); no new receipt, no meter event.

A PASS unblocks nothing beyond a re-sitting of C6/C8/C9 as re-filed below; fixture scope stays fixture scope — no arming, listing, or external claim rides this delta. Fences held: buyer-side dispatch-point witnessing only; price PC-8 $0.25/op unchanged (metering semantics narrowed only by the F3 idempotency cure — one op per dispatch seal, as C9 always claimed); no banned verdict language on any surface.

## Re-filed claims (superseding the C6/C8/C9 wording that failed)

- C6′ / ADV-1 (RTE-REQ-012, RT-K1 guard): no AS-DECLARED or DEVIATION verdict is mintable from relayed or fabricated capture material across all API paths — the ingestion paths reject and receipt provenance failures, and routeseal_recompute verifies the record's seal against its bundle fields before minting anything, capping at UNVERIFIABLE (reason seal_verification_failed) on any capture whose seal does not recompute from the fields it carries.
- C8′ (RTE-REQ-014): the receipt journal verifies end-to-end; a tampered journal record and a truncated export are detected; and a tampered store record — a flipped verdict field, a flipped bundle field, or a flipped seal — fails closed at load, because every record is cross-checked against its own recomputed seal and its seal receipt's payload_digest before anything is served.
- C9′ (RTE-REQ-015): metering charges exactly one op per dispatch seal — including under replay: re-submitting the identical capture returns the existing record with no second dispatch_seal receipt (RTE-REQ-014: exactly one receipt record per dispatch seal) and no second meter event. CANDIDATE-SET-ABSENT, UNVERIFIABLE, rejections, recompute, and check never meter; the ledger records event class + count only.

## Evidence pack

- Verdict cured against: VERDICT-DELTA-20261113.md (this home + Shard E build home).
- Cure-lane reproduction + post-cure probe: probe_verdict.py (repo root, committed with the F1 cure) — F1 judge probe (state-file verdict flip), F2 judge probe (fabricated capture dict, garbage seal), F3 judge probe (identical capture submitted twice). Pre-cure vs e81d323: F1/F2/F3 CONFIRMED. Post-cure vs a3d1d9e: F1 REFUSED at load (record/receipt binding) · F2 REFUSED (UNVERIFIABLE, seal_verification_failed) · F3 REFUSED (1 receipt, 1 metered op).
- Product suite at a3d1d9e: 44/44 OK (34 pre-existing + 10 new: TestRecordTamperRefusal ×4, TestRecompute seal legs ×3, replay idempotency ×3 in TestMetering), including regression of the C1–C5/C7/C10 behaviours.
- MCP smoke at a3d1d9e: PASS.
- Commits fd4dfcf + 2c22e83 + a3d1d9e in the repo of record (diff = routeseal.py + server.py (description only) + tests/test_routeseal.py + probe_verdict.py; logic.py byte-identical to the judged build).
- Parity note: the FAIL verdict recorded Shard E parity as UNVERIFIED (SSH proxy resets during that sitting). The cure lane verified it directly: the Shard E maintenance home was at judged HEAD e81d323 before the cure and is fast-forwarded to a3d1d9e after the push — GitHub main == Shard E == cure clone at filing.

## (INT — INTERNAL) QA-pattern conformance

| Pattern | Verdict (CLEAR / HIT / N-A) | Evidence or N-A reason |
|---|---|---|
| P1 — Content-free modes close every ingress | N-A | No content-free mode, tier, or setting exists. Custody is the §2 field-set reduction at the single seal ingress (candidates reduced to the five grammar facts at the door), covered by TestCustody, unchanged by this delta. |
| P2 — Disclosure matches build | CLEAR | This delta's claims are restated to the cured behaviour only (C6′/C8′/C9′ above), each probe-proven pre/post cure. The recompute surface now states its own basis (SEAL_BASIS in every recompute result + the routeseal_recompute tool description): an unkeyed digest binding internal consistency, provenance on the adapter channel — the disclosure the F2 verdict required. |
| P3 — Save/close basics | N-A | No save concept and no window: headless MCP server; state persists atomically per operation (os.replace in _save). |
| P4 — AI-applied content is attributed | N-A | The product applies no content — it seals routing facts presented at the dispatch point and evaluates them against the operator's stated policy; there is no AI-applied content surface. |
| P5 — Version discipline | HIT | The cure changes the shipped code (routeseal.py, server.py) with no version bump: TOOL_VERSION and VERSION still read 0.1.0, as the judged build did. Stated plainly: this is a bench-pending cure delta, no artefact is released under it; the bump belongs to the next release cut, not hidden here. |
| P6 — Integrity warnings are prominent | CLEAR | This delta is the P6 test shape applied to a headless surface: divergence is refused at the point of use, by name — load raises naming the record and the failed binding and serves nothing (probe F1 post-cure); recompute returns the named seal_verification_failed refusal capped at UNVERIFIABLE (probe F2 post-cure). Tests: TestRecordTamperRefusal, TestRecompute.test_recompute_fabricated_capture_unverifiable / _tampered_export_unverifiable / _unsealed_record_unverifiable. |
| P7 — Erasure-class operations | N-A | No erasure story: the product makes no history-erasure claim and offers no erasure operation; nothing in its copy credits any action with erasure. |
| P8 — Preview equals apply | N-A | No preview, dry-run, plan, or proposal surface exists. Recompute is a verification path over the sealed record, not a preview of an apply — and after this cure it verifies the seal before it verifies the verdict. |

## Claim sheet (standard form, added 2026-11-04 — bench efficiency lever 1)

Form only: statements extracted from this request; no claim substance changed.

```claims
[
  {"id": "RC1", "statement": "Store load cross-verifies every record: the seal is recomputed over the bundle fields rebuilt from the record, and the payload_digest of the dispatch_seal receipt named by receipt_ref is checked against the record's seal and verdict; a tampered record (flipped verdict, bundle field, or seal) fails closed at load and is never served", "evidence": "routeseal.py Store._verify_records/record_seal_valid at a3d1d9e; tests TestRecordTamperRefusal x4; cure-lane probe F1 pre/post cure", "verify": "recompute", "class": "chain"},
  {"id": "RC2", "statement": "routeseal_recompute verifies the record's seal against its bundle fields (and the seal_id derivation) before minting; a fabricated or tampered capture caps at UNVERIFIABLE with reason seal_verification_failed, a genuine sealed export recomputes exactly as before, and the seal basis (unkeyed digest, internal consistency only, provenance on the adapter channel) is stated on the recompute surface", "evidence": "routeseal.py recompute + SEAL_BASIS at a3d1d9e; server.py routeseal_recompute description; tests TestRecompute seal legs x3 + genuine-export regressions; cure-lane probe F2 pre/post cure", "verify": "recompute", "class": "chain"},
  {"id": "RC3", "statement": "Sealing is idempotent: re-submitting the identical capture returns the existing record with exactly one dispatch_seal receipt and exactly one metered op per dispatch seal; distinct captures still seal and meter separately", "evidence": "routeseal.py seal_dispatch idempotent-replay branch at a3d1d9e; tests TestMetering.test_replay_is_idempotent/_of_absent_capture_idempotent/test_distinct_captures_still_seal_separately; cure-lane probe F3 pre/post cure", "verify": "recompute", "class": "chain"},
  {"id": "RC4", "statement": "No regression: C1-C5/C7/C10 behaviours of the judged build are unchanged; product suite 44/44 and MCP smoke PASS at HEAD a3d1d9e, logic.py byte-identical to the judged build", "evidence": "tests/test_routeseal.py full run at a3d1d9e; smoke.py output; logic.py sha256 aa3daf3b... equals the judged build's hash in VERDICT-DELTA-20261113.md", "verify": "read", "class": "methodology"}
]
```

© Cyan Eclipse Technologies LLC — Proprietary · Company Intellectual Property
