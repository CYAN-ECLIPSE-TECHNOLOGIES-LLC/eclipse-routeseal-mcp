PROPRIETARY — CYAN ECLIPSE TECHNOLOGIES LLC · COMPANY INTELLECTUAL PROPERTY

# (IP — PROPRIETARY IP) SPEC — Cyan Eclipse Routeseal v0.1 (DRAFT — spec only)

- Gate: argus-gate-routeseal-20261111.md — PASS-WITH-CONDITIONS (RT-C1…RT-C9 · kill criteria RT-K1…RT-K4 · counsel queue RT-CQ-1…RT-CQ-3). Every gate condition is carried into §3 as a numbered requirement, verbatim in force; the gate's FAIL shapes are carried into §5 as spec-level prohibitions. Where the suggestion text (Argus daily batch 2026-11-11, entry 5) conflicts with the gate, the GATE wins and the conflict is noted (§1, §9).
- Commissioned: owner tap 2026-11-11 16:57 PT ("Commission specs for all three, gate conditions as spec requirements").
- Status: SPEC ONLY. No build, no listing, no external contact is authorized by this document. Build slot: P-2 — builds serialize behind the current flagship, on the owner's build word (RTE-REQ-001).
- Requirements: RTE-REQ-001…016, filed as Loom CANDIDATEs (Loom project "Cyan Eclipse Routeseal") with verifications at filing, verdicts not-run, NOT baselined — ratification is the owner's act.
- Name: "Cyan Eclipse Routeseal" is a PROVISIONAL working name, internal until the TM screen rides the counsel package (RT-CQ-3); composite form mandatory on every surface.

## (IP — PROPRIETARY IP) 1. Purpose and product definition

- **Buyer:** multi-agent platform buyers, Procure desks, and agent operators auditing the orchestration layers they rent — the seat that answers when a principal's work was quietly routed to the platform's own tools or paid partners instead of the best-fit candidate.
- **Job:** at a dispatch point the buyer/operator controls (their own gateway, proxy, or orchestration harness through which agent tasks are routed), seal the routing decision, the candidate set as presented to the router, and the stated selection reason at the moment of dispatch, with a witness that is neither the orchestration platform nor the operator; and mint a verdict judging the sealed decision against the operator's *own stated routing policy*.
- **Vantage — the gate's narrowing binds (RT-C4):** v1 operates only at buyer-controlled or buyer-instrumented dispatch points. A closed platform's internal routing is out of vantage: Routeseal claims the *dispatch record* only, never a platform's internals or intent. **Conflict noted:** the suggestion's unqualified phrasing ("the orchestrator's internal dispatch choice") reads wider than this; the gate narrowed it, the gate wins, and this spec specifies only the dispatch-point shape.
- **Adoption shape:** the buyer instruments their own side of the seam — one buyer's decision, no platform cooperation required (the Handoffseal adoption thesis, applied to dispatch).
- **Sibling separation:** distinct from Rankseal (what a search result *showed* the agent — Routeseal's object is the dispatch *choice*) and from Handoffseal (whether context *survived* an authorized transfer — Routeseal witnesses which agent/tool/vendor received the task at all).

## (IP — PROPRIETARY IP) 2. Sealed-record data model

- **Routing-policy grammar:** the operator's stated routing policy is expressed in a published grammar — clause classes (preference order · affiliation flagging/exclusion · capability match · cost/latency bounds) and the verdict rules over them. The grammar is published with the product (RTE-REQ-010). Verdicts name their verdict-grammar version and the routing-policy version in force at dispatch (RT-C7).
- **Dispatch seal record — the minimum sealed bundle (RT-C4):** task digest (SHA-256 over the task's canonical serialization; task bodies are digested transiently and never retained) · candidate set as presented to the router (identifiers as presented — or an explicit ABSENT marker where the dispatch point presented none) · selected target · stated selection reason as declared at dispatch · routing-policy version digest · declared affiliation flags on the selected target · dispatch timestamp · dispatch-point identity · seal. The bundle is sealed at dispatch by the dispatch-point adapter (RTE-REQ-012).
- **Store field set — the whole store (RT-C5):** task digests · candidate identifiers as presented · selected target · stated selection reason as declared · routing-policy version digest · declared affiliation flags · timestamps · seals · verdict + named grammar basis. No task bodies, no tool outputs, no principal data beyond the routing facts the grammar names, no cross-operator aggregation.
- **Verdict classes — fixed, exhaustive:** AS-DECLARED (the selection conforms to the stated routing policy in force) · DEVIATION (names the policy clause diverged from, the selected target, and the policy-preferred candidate passed over) · CANDIDATE-SET-ABSENT (decision sealed; no candidate set was presented at dispatch — no steering verdict is mintable) · UNVERIFIABLE (capture below the RT-C4 standard; a state of the evidence, never a platform's fault).
- **Candidate-set discipline:** steering is provable only against the road not taken. Where no candidate set is presented, the only steering-related verdict is CANDIDATE-SET-ABSENT; a candidate set is never inferred (RTE-REQ-011).
- **Versioning:** verdicts name their grammar version and the routing-policy version in force; a grammar or policy revision never retro-alters a minted verdict.

## (IP — PROPRIETARY IP) 3. Requirements

- **RTE-REQ-001 (P-2 sequence — RT-C1):** this spec confers no build slot. Any build of Routeseal serializes behind the current flagship and starts only on the owner's build word.
  *Verification:* inspection — the spec, gate, and Slate records state no build authorization; PASS iff no build artefact claims authority from this spec.
- **RTE-REQ-002 (three-part mechanism — RT-C2):** the product shall hold jointly (i) dispatch-point sealing of the decision bundle at dispatch, (ii) a steering verdict under the published routing-policy grammar, (iii) third-party recomputability of the verdict from the sealed bundle + the grammar. Dropping (ii) or (iii) re-gates the product.
  *Verification:* test — fixtures mint verdicts under the grammar; an independent verifier reproduces them from the sealed bundles alone (bench claims RT-B1/RT-B2).
- **RTE-REQ-003 (K6 / review-first + pricing boundary — RT-C3):** no listing, quote, or external pilot shall occur until the Assert written answers are filed and read and the listing passes owner review. Metering boundaries bind: the charge event is the dispatch seal; re-verification and counterparty recomputation of an existing verdict are unmetered; CANDIDATE-SET-ABSENT and UNVERIFIABLE captures do not meter.
  *Verification:* inspection — listing/quote artefacts (none may exist pre-clearance) + metering configuration against §4.3.
- **RTE-REQ-004 (capture standard + vantage — RT-C4):** the minimum sealed bundle is the §2 bundle. Below it, UNVERIFIABLE is the only mintable verdict; where no candidate set is presented, CANDIDATE-SET-ABSENT is the only steering-related verdict. The product shall operate only at buyer-controlled or buyer-instrumented dispatch points, and every surface shall claim the dispatch record only — never a closed platform's internal routing or intent.
  *Verification:* test — below-standard fixtures verdict UNVERIFIABLE and decision-only fixtures verdict CANDIDATE-SET-ABSENT, in 100% of cases (bench claim RT-B3).
- **RTE-REQ-005 (hash-only custody — RT-C5):** the store shall contain only the §2 field set. Task bodies are digested transiently and never retained; no tool outputs; no cross-operator aggregation.
  *Verification:* inspection — direct store inspection (bench claim RT-B4): PASS iff the store contains only the §2 field set.
- **RTE-REQ-006 (aggregation fence — RT-C6):** no platform-aggregate statistics, feeds, dossiers, or insights surface shall be produced from Routeseal records without the Friction counsel posture applying in full (re-gate). Per-operator records for the operator are the only aggregation.
  *Verification:* inspection — product surface and data-model review finds no cross-operator aggregate artefact or code path.
- **RTE-REQ-007 (grammar + policy versioning — RT-C7):** every verdict shall name its verdict-grammar version and the routing-policy version in force at dispatch; a grammar or policy revision shall never retro-alter a minted verdict.
  *Verification:* test — verdicts carry both versions; a post-verdict grammar/policy revision leaves minted verdicts byte-identical (bench claim RT-B5).
- **RTE-REQ-008 (incumbent + absorption watch — RT-C8):** if a major orchestration platform ships non-party-verifiable routing-decision records natively (candidate set + reason, recomputable by the buyer), the product shall be re-gated before any further build or launch step. Party-kept "transparency logs" do not trigger this.
  *Verification:* inspection — a watch record naming the trigger class exists and is reviewed at each gate event.
- **RTE-REQ-009 (claim line + verdict grammar + bench — RT-C9):** the honest claim line binds every surface: *"Routeseal seals the routing decision at the moment of dispatch — the task, the candidates the router passed over, the target it chose, and the reason it stated. If the choice diverged from your stated routing policy, or picked an affiliated target over the policy's preferred candidate, the sealed record says so, and anyone can recompute the verdict from the record itself."* The verdict grammar is the §2 fixed set. An independent Verity bench (§6) shall pass before any external pilot; builder tests are not evidence. The name remains provisional + internal until the TM screen; composite form mandatory.
  *Verification:* inspection — every product surface carries only the claim line and the §2 vocabulary; no §5 banned term appears.
- **RTE-REQ-010 (routing-policy grammar + clause classes):** the routing-policy grammar's clause classes and verdict rules shall be published with the product, and every DEVIATION verdict shall name the policy clause diverged from, the selected target, and the policy-preferred candidate passed over.
  *Verification:* test — policy-violating fixtures verdict DEVIATION naming clause, selected target, and passed-over preferred candidate; policy-conformant controls verdict AS-DECLARED, in 100% of fixtures (bench claim RT-B1).
- **RTE-REQ-011 (candidate-set discipline, structural):** the verdict engine shall be structurally incapable of minting DEVIATION without a sealed candidate set: a steering verdict shall require a sealed candidate-set field of dispatch-point provenance (RTE-REQ-012); a candidate set reconstructed or supplied after the fact shall be refused as capture material.
  *Verification:* test — decision-only fixtures verdict CANDIDATE-SET-ABSENT in 100% of cases, including adversarial attempts to attach a later candidate list (bench claim RT-B3; bench ADV-2).
- **RTE-REQ-012 (capture provenance — the RT-K1 guard):** a dispatch capture shall be accepted only if it arrives through the buyer-side dispatch-point adapter channel carrying the adapter's own attestation and a binding reference to the dispatch event. Platform-produced traces, logs, or observability exports — and any relay of them — shall be rejected as capture material, the rejection receipted, and the dispatch capped at UNVERIFIABLE.
  *Verification:* test — a platform-log-derived "capture" fixture is rejected and receipted in 100% of attempts; no AS-DECLARED or DEVIATION verdict is mintable in that configuration (bench ADV-1).
- **RTE-REQ-013 (MCP interface conformance):** the MCP surface shall be exactly the tools of §4.1. `routeseal_check` shall reveal the verdict class and named clause only; `routeseal_recompute` shall accept the sealed capture + grammar/policy versions and return the recomputed verdict with no service state. All outputs shall carry only the §2 verdict vocabulary and no §5 banned term.
  *Verification:* test — tool inventory equals §4.1 exactly; recompute runs offline against exported captures; output scan finds no banned term.
- **RTE-REQ-014 (receipt-chain integration):** every dispatch seal and verdict shall append exactly one record to the product's hash-chained receipt journal (sequence · timestamp · record kind · payload digest · previous-hash link · record hash), and the chain shall verify end-to-end. Exports shall carry the chain head.
  *Verification:* test — chain verification passes on a populated journal; tampered-record and truncated-export fixtures are both detected.
- **RTE-REQ-015 (pricing hooks — PC-8):** metering shall implement the PC-8 Episodic-ops (Keyhold) pattern exactly as gate-confirmed: one charge per dispatch seal ($0.25 pattern) covering the sealed bundle + verdict as a single op; re-verification and recomputation are unmetered; CANDIDATE-SET-ABSENT and UNVERIFIABLE captures do not meter. Priced-row adoption is a separate owner act at listing time; this spec adopts no price row.
  *Verification:* test — metering fixtures per event class produce exactly the §4.3 charges and no others.
- **RTE-REQ-016 (branding baseline):** the product shall ship with Cyan Eclipse branding applied completely at creation, as baseline scope: icon · name/wordmark · theme tokens (eclipse-brand-system) · splash/launch surfaces · about/identity surfaces, in the Apple-look × Cyan Eclipse theme and plain, obvious labelling. The icon is subject to individual owner approval before it ships; that approval is the owner's gate at build time and is not discharged by this spec.
  *Verification:* inspection — at build, the brand checklist (icon · wordmark · theme tokens · splash/launch · about/identity) is checked against the brand application standard, with the icon-approval record present.

## (IP — PROPRIETARY IP) 4. Interfaces

### 4.1 MCP tool surface (server: `eclipse-routeseal`)

| Tool | Inputs | Outputs |
|---|---|---|
| `routeseal_seal_dispatch` | task_digest · candidate_set[] (identifiers as presented, or ABSENT) · selected_target · stated_reason · policy_version · affiliation_flags · dispatch_point_id · adapter_attestation | dispatch_seal_id · receipt_ref · verdict |
| `routeseal_get_verdict` | dispatch_seal_id | verdict · clause (DEVIATION) · selected_target · passed_over_preferred (DEVIATION) · grammar_version · policy_version · receipt_refs |
| `routeseal_check` | dispatch_seal_id | verdict · clause name only — counterparty view |
| `routeseal_recompute` | dispatch_capture · grammar_version · policy_version | verdict — unmetered; runs with no service state |
| `routeseal_export_captures` | dispatch_seal_id | capture (digests + seals) · chain_head · grammar_version · policy_version |

### 4.2 Receipt chain

Append-only, hash-chained receipt journal in the firm's seal/journal pattern: one receipt per dispatch seal and verdict (RTE-REQ-014). Exports carry the chain head. Recomputation (RTE-REQ-002) is defined over the exported capture + the published grammar and the sealed policy version, and requires no service access. The bundle may ride OpenTelemetry-shaped fields (a spec input per the gate); the seal is the evidence, not the span.

### 4.3 Pricing hooks (PC-8 Episodic ops / Keyhold — pattern fit gate-confirmed; no price row adopted)

Metering event: **one dispatch seal** (sealed bundle + verdict as a single op), charged once per dispatch. Non-events (never metered): re-verification · `routeseal_recompute` · `routeseal_check` · CANDIDATE-SET-ABSENT captures · UNVERIFIABLE captures. The metering ledger records event class + count only.

## (IP — PROPRIETARY IP) 5. Prohibitions (gate FAIL shapes — spec-level)

- **P1.** No DEVIATION verdict from a decision-only capture, and no candidate set inferred, reconstructed, or attached after the fact (gate §1; RTE-REQ-004/011).
- **P2.** No shape claiming to witness an orchestrator's internal routing from outside a dispatch point it transits (gate §0 FAIL (a); RT-C4).
- **P3.** No verdict or surface claiming intent or motive — the record names a deviation from a stated policy, never why anyone wanted it (gate §0 FAIL (b); RT-C9).
- **P4.** No aggregation of sealed routing records into platform-behaviour statistics, feeds, or dossiers (gate §0 FAIL (c); RT-C6) without the Friction counsel posture in full.
- **P5.** Banned on every surface (RT-C9): "proves steering / self-preferencing" as a motive claim · "the platform's algorithm chose X because…" beyond the stated reason as declared · any legal conclusion (antitrust, fiduciary, or otherwise) · any claim about a platform's routing behaviour in aggregate.

## (IP — PROPRIETARY IP) 6. Bench plan (future Verity bench — claim-by-claim; builder tests are not evidence)

Starting set = the gate's bench-claim drafts (RT-B1…RT-B5), finalized by Verity, restated as acceptance criteria:

- **RT-B1 — Deviation detection:** fixtures where the sealed selection violates the stated routing policy verdict DEVIATION naming the clause, the selected target, and the passed-over preferred candidate; policy-conformant controls verdict AS-DECLARED — 100% of fixtures.
- **RT-B2 — Independent recomputation:** a verifier holding only the sealed bundle + the policy grammar reproduces the verdict with no service access.
- **RT-B3 — Candidate-set discipline:** decision-only fixtures verdict CANDIDATE-SET-ABSENT and below-standard fixtures verdict UNVERIFIABLE in 100% of cases; no DEVIATION verdict is mintable from either.
- **RT-B4 — Custody negative test:** the store, inspected directly, contains only the §2 field set — no task bodies, no tool outputs, no cross-operator tables.
- **RT-B5 — Versioning:** verdicts name their grammar version and the routing-policy version in force; a later revision of either never retro-alters a minted verdict.
- **ADV-1 (adversarial — RT-K1, log-shipping collapse):** the dispatch-point adapter is replaced by a relay forwarding the platform's own trace/log export (party-kept records of the path taken) as "captures." PASS iff the product detects the provenance failure (the material lacks the adapter's attestation/binding), rejects and receipts it, and no AS-DECLARED or DEVIATION verdict is mintable in this configuration across all API paths — the dispatch caps at UNVERIFIABLE.
- **ADV-2 (adversarial — inferred candidate set):** a decision-only dispatch fixture is accompanied, after the fact, by a candidate list reconstructed from a later task. PASS iff the record seals decision-only, verdicts CANDIDATE-SET-ABSENT, and the after-the-fact list is refused as capture material with the refusal receipted.

## (IP — PROPRIETARY IP) 7. Non-goals (v0.1)

No witnessing of closed-platform internal routing · no motive or intent determination · no legal conclusions · no platform surveillance or aggregate statistics · no enforcement (Routeseal witnesses dispatch decisions; it does not route, block, or re-route tasks) · no task-content custody · no platform-side shape (an orchestrator sealing *its own* dispatch for its buyers is a different vantage and would re-gate — gate §11).

## (IP — PROPRIETARY IP) 8. Branding baseline (standing default — also RTE-REQ-016)

Icon · name/wordmark · theme tokens · splash/launch · about/identity surfaces, applied completely at creation in the Apple-look × Cyan Eclipse theme. The icon-program gate is preserved: the owner approves the Routeseal icon individually before it ships.

## (IP — PROPRIETARY IP) 9. Open items — carried, not resolved

- **TM screen** for "Cyan Eclipse Routeseal" (RT-CQ-3 — counsel; name provisional until cleared).
- **Evidentiary weight** of a sealed DEVIATION record in a procurement dispute or platform-contract claim (RT-CQ-1 — counsel).
- **Capture posture** at buyer-instrumented dispatch points — platform ToS / trade-secret posture (RT-CQ-2 — counsel).
- **Priced-row adoption** at listing (owner act; §4.3 is pattern fit only).
- **K6 / Assert posture** (RTE-REQ-003): no listing, quote, or external pilot until the Assert written answers are filed and read and the listing passes owner review.
- **V1 dispatch classes** (spec scope call at build time, driven by dispatch-point feasibility — the RT-K2 evidence question) — deliberately left open by the gate (§11).
- **Conflict carried:** the suggestion's pitch ("an orchestrator routed an agent's task… so a platform quietly steering work… is provable") is retained as the buyer-facing problem statement only in the narrowed sense of §1 — the sealed record proves a *deviation from the operator's stated policy at a witnessed dispatch point*, nothing wider (gate wins; §5 P2/P3 enforce).

© Cyan Eclipse Technologies LLC — Proprietary · Company Intellectual Property
