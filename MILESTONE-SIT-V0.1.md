# Semantic Interoperability Test v0.1 — frozen result

**Date:** 2026-10-03
**Baseline commit:** `1a746a7` (spec v0.1)
**Status:** FROZEN. Do not edit. This file is the record of what was observed
*before* the specification was revised.

## The statement

> Two independently implemented interpreters of the same normative
> specification agreed on **29 of 36** cases. The seven disagreements exposed
> **five undocumented corpus-integrity invariants**, **one underspecified
> uncertainty classification**, and **one underspecified proposition-selection
> rule**, plus additional ambiguities concerning **null temporal values** and
> **represented reasons**.

Not "the engines achieved 81% agreement." The seven disagreements are the
result; the 29 agreements only establish that the disagreements are localised
rather than diffuse.

## Implementations

| | A | B |
|---|---|---|
| language | Python | Rust (std-only, hand-rolled JSON) |
| graph | dict-based fixpoint | `u64` bitword adjacency matrix + Warshall closure |
| cycle detection | derived from fixpoint failure | explicit SCC, independent of convergence |
| provenance | author | author |

B read only `SEMANTICS.md`, `CORPUS_FORMAT.md`, `corpus_export.json`.
Verified from B's transcript: no reference to `corpus.py`, `semantics.py`,
`expected.py`, `compare_impls.py`, or any `test_*.py`; zero case-id literals in
B's source; no `IMPLEMENTATION` uncertainty emitted.

## The seven disagreements

| case | A | B | diagnosis |
|---|---|---|---|
| E1 | `INVALID/NONE` | `CONTESTED/CORPUS` accepted={A,B} | **spec omission** — F2_PROMULGATION undocumented |
| E2 | `INVALID/NONE` | `DECIDED/NOT-Y` accepted={B} | spec omission (F3) **+** null-date ambiguity |
| E3 | `INVALID/NONE` | `DECIDED/NOT-Y` accepted={B} | **spec omission** — F7_CONSTANCY undocumented |
| E4 | `INVALID/NONE` | `CONTESTED/CORPUS` | **spec omission** — F1_GENERALITY undocumented |
| E5 | `INVALID/NONE` | `CONTESTED/CORPUS` | **spec omission** — F5_NON_CONTRADICTION undocumented |
| G3 | `DECIDED` conclusion `A1` | `DECIDED` conclusion `null` | **real fork** — multi-atom grounded set unspecified |
| G8 | `INVALID/NONE` | `INVALID/CORPUS` | **real fork** — uncertainty for INVALID unspecified |

## The finding that mattered

A enforced five corpus-integrity invariants that existed **only in
`check_invariants()`**, in neither specification document. The architecture
contained a hidden layer:

```
SEMANTICS.md
      ↓
actual semantic engine
      ↓
check_invariants()      ← normative rules, unwritten
```

B was instructed to implement the written specification and did. Five of seven
disagreements were not differences in reasoning: they were A enforcing rules B
had no legitimate way to know existed.

This is a worse defect than an ambiguous clause. "Unpromulgated rules cannot
defeat anything" is *substantive legal content*, and it was living in code.

## Additional ambiguities found by B

- `explicit_lex_posterior` with a null date — comparison undefined. B read null
  as −∞; that reading flips E2.
- `uncertainty` for `INVALID` — required by the format, assigned by no table.
- `accepted` when no stable fixpoint exists — field mandated, contents undefined.
- `promulgated` / `retroactive` present in schema, absent from the
  triggered-rule definition.
- `represented_reason` — defined nowhere; B invented a definition.
- B self-reported a real mid-run bug: it initially rejected *unrecognized*
  bases but not *unsatisfied* ones, letting a memo beat a legislature on
  `explicit_authority_precedence`. The class M6 guards.

## Why this is not a capability result

Both implementations were written by the same author. The corpus was authored
around the ratified semantics. No external legal-domain reviewer has confirmed
that any of this describes law.

**This measures whether a written specification determines an implementation. It
does not measure whether the semantics are correct, and it is not a
justification or authority result.**

## What revision v0.2 changed

Specification only, at `SEMANTICS.md`: new §2.1 (uncertainty for a defective
corpus), §4.6 (absent values), §4.8 (represented reason), §5 (corpus validity —
the five invariants, now written down), §5a (proposition-level selection).

**The corpus was not changed.** Both implementations were then re-run against
v0.2. Convergence after revision is the next experiment; see
`SIT-V0.2-RESULTS.md`.