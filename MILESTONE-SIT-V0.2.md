# MILESTONE — Semantic Interoperability Test v0.2

**Date:** 2026-10-03
**Status:** FROZEN
**Question under test:** is Ganymede5's written semantics sufficient for an
independent implementer, denied access to the reference implementation, to
reconstruct the same observable behaviour?

**Answer: yes, on this corpus, for every field the specification fixes.**

---

## Result

```text
cases compared:   36
AGREE             35
DISAGREE           0
REPORTING only     1   (G4, on `defeated`)
```

Three implementations, three languages, three defeat-graph representations:

| | language | representation | access to A |
|---|---|---|---|
| A | Python | fixpoint over a dict index | reference |
| B | Rust | `u64` adjacency bitwords + Warshall closure | none |
| C | Node.js | BigInt adjacency masks + Tarjan SCC | none |

B and C were each denied `corpus.py`, `semantics.py`, `expected.py`, the tests,
the manifest, and the other implementation. Verified, not assumed:

```text
case-id literals in C/engine.js:  []        (present only in selftest.js, as disclosed)
references to A / tests / manifest in engine.js:  []
uncertainty value IMPLEMENTATION emitted by C:  False  (only CORPUS, NONE, SEMANTIC)
```

## The two transfers, and what each one changed

**v0.1 → B: 29/36.** Seven disagreements. All seven traced to specification
gaps, not to B:

- 5 (E1–E5) — corpus-integrity invariants enforced in A's `check_invariants()`
  and documented nowhere. B had no way to know them.
- 1 (G8) — uncertainty value for `INVALID` unassigned by the old table.
- 1 (G3) — declaration order silently used as an atom-preference rule.

**v0.2 → C: 36/36.** After §5 (corpus validity), §4.6 (absent values), §4.8
(`represented_reason`), §5a (proposition-level selection), and §2.1 (INVALID ⇒
CORPUS) were written down, a second independent implementer reached A's answers
on every case. C independently reproduced the five E-defects from the written
rules and derived each one's invariant by name — `F2_PROMULGATION`,
`F3_NON_RETROACTIVITY`, `F7_CONSTANCY`, `F1_GENERALITY`,
`F5_NON_CONTRADICTION` — without ever seeing A's list.

C's `D1`/`D2` `REFUSED` uncertainty and all `CONTESTED`/`represented_reason`
values also match A, chosen on spec grounds rather than by majority.

## What this result is not

This is **implementation interoperability**, not capability, and not legal
validity. It says the written semantics determine an implementation. It does not
say the semantics are *correct*, *complete*, or *externally validated*. The
corpus was authored by the same author as the spec and the manifest, and no
domain expert has reviewed either.

The claim is also **corpus-relative**: 36 synthetic cases. It does not establish
that the spec determines behaviour on real legal material.

## Residual findings, carried forward not fixed

### R-1. `defeated` is unspecified, and it shows

The single remaining difference. G4 (mutual cycle): A reports `defeated=[]`,
C reports `['B','C']`. Both agree on `status`, `uncertainty`, and `accepted`.

C's convention is `triggered − accepted`. A's leaves it empty when no grounded
set exists. `CORPUS_FORMAT.md` explicitly declines to compare the field — which
is why the harness classed it reporting-only rather than a disagreement. The
field is now *known* to be unfixed by the spec; it is no longer silent.

### R-2. `REFUSED` uncertainty is genuinely under-specified

C flagged this as its least confident field, unprompted: §2.1 fixes `CORPUS`
for `INVALID` and `NONE` for `NONFINDING`, but is silent on `REFUSED`. C chose
`NONE` and reached the same answer as A and B — but by coincidence of a
reasonable reading, not because the spec compelled it. A future implementer
could defensibly choose `CORPUS` and be equally right. **Not resolved by this
milestone; agreement here is luck, not derivation.**

### R-3. Two status paths are implemented but never exercised

`NONFINDING` and `DEFEATED` appear in `SEMANTICS.md`, `CORPUS_FORMAT.md`, and the
code, but **no case in the 36-case export produces either.** They are
implemented from prose and untested by the corpus. C reached the same conclusion
independently.

This is the project's fourth instance of one pattern (see below), and the most
serious: *a capability the system claims and the corpus cannot reach.*

### R-4. `REFUSED` vs `INVALID` precedence is unspecified

A corpus that is both defective under §5 and requires an unexpressible construct
has no defined outcome. C runs the validity check first, following §5's "runs
first" language. Untestable on the current corpus — no case is both.

## The governing pattern

Five defects found so far, one root cause — **a value acquiring semantic
meaning because an implementation needed one:**

| # | site | default that leaked |
|---|---|---|
| 1 | §4.6 | absent `effective_from` read as `-inf` (M14) |
| 2 | §2.1 | absent `uncertainty` defaulted to `NONE` |
| 3 | §5a.2 | declaration order used as atom preference (G3) |
| 4 | `accepted()` | exhausted loop bound reported as `SEMANTIC` |
| 5 | R-3 | unreachable status paths present as implemented capabilities |

The first three were specification gaps; they are now closed. #4 is a live code
defect recorded in `MILESTONE-SIT-V0.3-CANDIDATES.md` (F-1) — a well-founded
chain and a genuine cycle both return `SEMANTIC` when the iteration budget is
small. #5 is a coverage gap. Neither was fixed here, deliberately: both were
found while C was in flight and fixing them would have moved A's outputs
mid-comparison.

## Recommended sequence

```text
resolve R-2 (REFUSED uncertainty) + R-4 (precedence) in the spec
add corpus cases for NONFINDING and DEFEATED, then R-3 closes
fix F-1 (budget exhaustion ≠ indeterminacy) and F-2 (consult the cycle)
freeze v0.3, rerun A/B/C
only then expand the corpus
```

Corpus expansion, delegation, jurisdiction, and institutional structure stay
deferred until v0.3 converges. The 36/36 result is the argument for that
ordering, not a reason to skip it: three of six status values have never been
exercised by any corpus, so the semantics is verified only where it has been
asked a question.