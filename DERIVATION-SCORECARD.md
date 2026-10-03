# Derivation Scorecard — SIT v0.3

Baseline commit: `bf59d14` · Spec version: v0.3 · Corpus: 41 cases

## Why this file exists

Four implementations agreeing on an output does **not** establish that a
specification determines that output. Two systems can converge on `NONE` for
`REFUSED` because the spec is silent and `NONE` is the only plausible-looking
value — that is coincidence wearing the costume of a result.

So agreement is recorded in two columns, never one:

- **Derived** — the implementer reached the value *because the spec says so*,
  and can quote the sentence that compelled it.
- **Coincident** — the implementer reached the right value but the spec did not
  compel it; the agreement is luck and will not survive a fifth implementation.

The headline is not the agreement rate. The headline is the count of fields
where derivation and agreement coincide.

## The scorecard

Fill `A`, `B`, `C`, `D` from each implementation's own reported reasoning. A cell
may only be `derived` if that implementation's report quotes or paraphrases the
governing section **before** describing its value.

| Field | Explicitly specified? | Spec section | A | B | C | D | Verdict |
|---|---|---|---|---|---|---|---|
| `status` DECIDED | yes | 6.1 | derived | — | derived | **derived** | derived |
| `status` CONTESTED (corpus) | yes | 4.x / 6.1 | derived | — | derived | **derived** | derived | |
| `status` CONTESTED (semantic) | yes | 4.2, 4.3, 4.5 | derived | — | derived | **derived** | derived | |
| `status` INVALID | yes | 5 | derived | — | derived | **derived** | derived | |
| `status` REFUSED | yes | 6.1 | derived | — | derived | **derived** | derived | |
| `status` NONFINDING | yes | 6.1 | derived | — | derived | **derived** | derived | |
| `status` DEFEATED (reserved) | yes | 6.1 | derived | — | derived | **derived** | derived | |
| `uncertainty` NONE | yes | 2 | derived | — | derived | **derived** | derived | |
| `uncertainty` CORPUS | yes | 2.1 | derived | — | derived | **derived** | derived | |
| `uncertainty` SEMANTIC | yes | 4.5 / 6.3 | derived | — | derived | **weak** | weak — 1 case | |
| `uncertainty` for REFUSED | **silent in v0.2** | 6.1 | — | — | chose | **derived** | now derived |
| absent temporal values | yes | 4.6 | derived | — | derived | **derived** | derived | |
| INVALID over REFUSED precedence | yes (new) | 6.2 | derived | — | — | **derived** | derived | |
| multi-atom → `conclusion: null` | yes | 5a | derived | — | derived | **derived** | derived | |
| budget exhaustion ≠ SEMANTIC | yes (new) | 6.3 | derived | — | — | **vacuous** | see below | |
| `represented_reason` semantics | yes (new) | 4.8 | derived | — | — | **derived** | derived | |
| unsupported basis rejected | yes | 4.6 | derived | — | derived | **derived** | derived | |
| self-defeat → INVALID | yes | 4.4 | derived | — | derived | **derived** | derived | |

Fields D was specifically asked to adjudicate are marked *(new)* — those are
where v0.2 was known-incomplete and v0.3 is being tested.

## Three-way state ledger

Adopted to prevent "we have a field for this" from decaying into "we have
implemented this semantics."

| Status | Category | Evidence |
|---|---|---|
| `DECIDED` | **reachable** | 15 of 41 cases; 57 across all three regimes |
| `CONTESTED` | **reachable** | 15 of 41 cases; both CORPUS and SEMANTIC variants |
| `INVALID` | **reachable** | 7 of 41 cases; five distinct invariants |
| `REFUSED` | **reachable** | 6 of 41 defeasible-path refusals |
| `NONFINDING` | **reachable (new in v0.3)** | 2 of 41 cases (H1, H4) |
| `DEFEATED` | **reserved** | 0 cases. Implemented as a schema value; grounded/oscillation semantics cannot reach it. All 27 empty-extension graphs also oscillate, so 4.5 fires before the empty-extension branch. |

`SEMANTIC` is exercised by exactly **one** case (G4, the mutual cycle). That is
thin. A single case cannot distinguish "the spec determines this" from "the
implementer had one worked example." Treat single-case coverage as
unverified regardless of agreement.

## The one field that did NOT transfer: §6.3

D's engine says, in its own words, that it *discharges* the §6.3 obligation
"structurally rather than by a counter" — its propagation loop is monotone
within a round, so it cannot run out of budget and never faces the choice.

That is a legitimate reading of the spec, and it is also **not a
corroboration**. F-1 exists because A *did* have a budget and *did* convert
exhaustion into `SEMANTIC`. A different implementation that never allocates a
budget cannot confirm the rule is specified; it can only decline to violate
it. The field is marked `vacuous`, not `derived`.

Consequence for the research question: whether an operational limit is
epistemically inert is **implementation-dependent and therefore not settled by
a specification**. The spec constrains the *reporting*; it cannot prevent one
engine from inventing a limit another has no reason to have. This is a real
limit on transfer and it is recorded rather than scored as a pass.

The same logic applies to `SEMANTIC`: one exercising case (G4) and one
implementation that finds it by a structurally different route is better than
nothing and is not sufficient.

## Rules for using this file

1. A `derived` mark requires a quoted section. A mark with no quote is `guessed`.
2. Any field where every implementation agrees but at least one is `guessed`
   is **unverified**, and must be reported as such in the frozen milestone.
3. A field where implementations disagree is *not* automatically a defect.
   Classify it as: underspecified / implementation bug / defensible alternate
   reading / hidden preference leakage / invalid experiment.
4. Do not edit this file to improve a number. It is filled once, from
   implementer reports, and frozen with the milestone it describes.
