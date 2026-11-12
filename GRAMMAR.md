# Cyan Eclipse Routeseal — routing-policy grammar (published)

**Grammar version:** `routeseal-grammar/1`

Routeseal judges a sealed routing decision against the operator's
*own stated routing policy*. This document is the published grammar
(RTE-REQ-010): the clause classes a policy may state, and the
verdict rules over them. Any holder of a sealed capture, this
grammar, and the stated policy can recompute the verdict with no
service access.

## Policy shape

A routing policy is a versioned document:

```json
{
  "version": "op-policy/1",
  "clauses": [
    {"class": "preference_order", "order": ["alpha", "beta"]},
    {"class": "affiliation_flagging"},
    {"class": "capability_match", "required_capabilities": ["code"]},
    {"class": "cost_latency_bounds", "max_cost": 10.0, "max_latency_ms": 500}
  ]
}
```

The policy's digest (SHA-256 over its canonical serialization) is
sealed into every dispatch record; a verdict names the policy
version and this grammar version (RT-C7).

## Clause classes

| Class | Kind | Rule |
|---|---|---|
| `affiliation_exclusion` | hard | An affiliated target must never be selected while this clause stands. |
| `capability_match` | hard | The selected target must carry every `required_capabilities` entry. Candidates carry their capabilities as presented at the dispatch point. |
| `cost_latency_bounds` | hard | The selected target's stated `cost` / `latency_ms` must not exceed the stated bounds. |
| `preference_order` | preference | Where a conforming candidate ranks earlier in `order` than the selected target, the selection diverged from the stated preference. |
| `affiliation_flagging` | preference | Selecting an affiliated target over a non-affiliated candidate the policy otherwise prefers is a divergence from the flagging clause. |

Clauses are evaluated in the fixed order listed above; the first
diverged clause is the named clause. The **policy-preferred
candidate** named in a DEVIATION verdict is the candidate that
satisfies every hard clause and ranks first under the policy
(preference order where stated, else presentation order).

## Candidate facts

A candidate, as presented to the router at the dispatch point,
carries only the facts this grammar names: `id` · `affiliated`
(declared affiliation flag) · `capabilities` · `cost` ·
`latency_ms`. The sealed record retains exactly these.

## Verdicts (fixed, exhaustive)

- **AS-DECLARED** — the selection conforms to the stated routing
  policy in force at dispatch.
- **DEVIATION** — names the policy clause diverged from, the
  selected target, and the policy-preferred candidate passed over.
  A verdict names a divergence from a stated policy; it states
  nothing about why the selection was made.
- **CANDIDATE-SET-ABSENT** — the dispatch was sealed and no
  candidate set was presented at the dispatch point. No steering
  verdict is mintable from a decision-only capture, and a candidate
  set is never inferred, reconstructed, or attached after the fact.
- **UNVERIFIABLE** — the capture is below the minimum sealed-bundle
  standard, or its provenance is not the buyer-side dispatch-point
  adapter channel. A state of the evidence, never a platform's
  fault.

## Capture standard

The minimum sealed bundle: task digest (SHA-256 over the task's
canonical serialization; task bodies are digested transiently and
never retained) · candidate set as presented (or the explicit
ABSENT marker) · selected target · stated selection reason as
declared at dispatch · routing-policy version + digest · declared
affiliation flags · dispatch timestamp · dispatch-point identity ·
a binding reference to the dispatch event · the adapter's
attestation. Captures arrive only through the buyer-side
dispatch-point adapter channel; platform-produced traces, logs, or
observability exports — and any relay of them — are rejected and
receipted.
