# Family G — nested defeat. STATUS: resolved under a ratified semantics.

**Superseded by `SEMANTICS.md`.** This file records how the semantics was
reached, including the parts that were wrong on the way. Kept deliberately;
the earlier "shipped failing" version is preserved in git history.

Baseline A–F corpus: **40/40**. Full suite: **67/67**. Mutants: **11/11 killed**.

## What changed

Defeat is now a **grounded fixpoint** (Dung) rather than a single pass, and the
cycle question is a ratified position rather than an open problem. See
`SEMANTICS.md` for the normative statement; `semantics.py` implements it.

| | before | after |
|---|---|---|
| cases | 34 | 36 |
| `defeasible` accuracy | 0.94 | **1.00** (0 disagreements) |
| suppression of contested cases | 8% | **0%** |
| justification on decided contested | 0.86 | 0.82 (9/11) |

Suppression 8% → **0%** is the number that matters: two contested cases were
being closed without warrant, and neither is now.

## Four engine defects, found by the spec rather than by tests

**1. Single-pass defeat.** Applied defeats in sequence, so a defeat could not
be itself defeated. Correct for depth-1, which is all of A–F. That is why the
0.94 was only ever a depth-1 result.

**2. `explicit_chain_succession` fell through to the rank branch.** Succession
is stated in the corpus, but the dispatch had no branch for it, so it hit the
`else` and was validated by `rank`. In G4 that meant C (rank 7) beat B
(rank 2), which **destroyed the defeat cycle by rank** and made G4 report
`DECIDED`.

That is the precise failure G4 was built to detect — a rank heuristic wearing
a formalism's clothes — hiding in my own basis dispatch. Now mutant M2; the
cycle is correctly `CONTESTED`.

**3. `CONTESTED` dropped the record of what *had* been defeated.** Status and
trace were both right, but the returned `defeated` list was empty, so a correct
case looked like nothing had been decided. Now M10.

**4. `_pick` ordered survivors by authority.** Unobservable in the conclusion
— only reached when survivors do not contradict — so it looked harmless. It is
not: it is an authority preference, and it *is* observable in the trace.
Replaced with deterministic declaration order. Case G7 exists solely to make
this detectable.

## Five errors in my own corpus, not the engine

This is the finding I would keep if I could keep only one.

| case | error | who was right |
|---|---|---|
| G2 | survivors never contradicted, so no contest was posed | engine |
| G2b | meant as a DECIDED "control"; its survivors *do* contradict | engine |
| G2c, v1 | both branches asserted the *same* conclusion | engine |
| G1 | "resolves transitively at D" — assumes succession propagates through a defeated defeater | engine |
| G1/G5 | identical defeat graphs carrying **opposite** manifest labels | neither; both were suspect |

**G1 and G5 are the same graph**, verified mechanically as identical frozensets
of active defeat edges. No deterministic semantics can honour labels that
contradict each other. That contradiction, not the cycle, is what made this
round's work necessary.

Three further corpus defects: the chain rules asserted derived atoms `A1`/`B1`
rather than `Y`/`NOT-Y`, so G1 and G5 never discriminated on the contested atom
at all — and returned *different* answers purely because `_pick` sorted by
rank. Family G was partly measuring the tiebreak it claimed to forbid.

## Two claims withdrawn

**"The chain resolves at D."** Withdrawn. Grounded semantics admits `{B, D}`:
C is out, so C's defeat of B does not stand, so B survives, so B's defeat of A
stands. Succession does **not** propagate end-to-end.

**"G5 is the exception-to-an-exception reversal reaching A."** Withdrawn. It
required a defeated defeater to restore a rule it cannot legitimately affect.

## The substantive result

**G5 is now `CONTESTED`, and that is the interesting answer.** A chain ending
in a constitutional exception leaves both the agency rule and the constitution
admitted, asserting opposite atoms. Preferring the constitution would be the
authority-preference tiebreak the spec removes. Whether the exception reaches
*this* case is a question of **applicability**, and applicability is not
represented in the corpus.

So the honest output is an open contest — which is also how a general rule and
its exception actually coexist in law.

## Three uncertainties, kept apart

| kind | who reports it | example |
|---|---|---|
| `SEMANTIC` | engine | G4 cycle — the formalism is indeterminate |
| `CORPUS` | engine | G2c — the corpus lacks a relation |
| `IMPLEMENTATION` | **grader only** | any mutant above |

`IMPLEMENTATION` is deliberately not emittable by the engine, guarded by test.
A system that can diagnose its own implementation errors is not being audited.

## What the mutation run added

The first run killed 7/11. The four survivors were all *untested commitments*:

- M4/M11 → case G7, two survivors asserting the same atom, so preference is
  only visible in the trace.
- M7 → case G8, a self-defeating rule, proving `INVALID` is distinct from
  `CONTESTED`.
- M9 → a test that reads the reversal out of the trace.

A stated commitment with no test enforcing it is the same as an unwritten one.

## Limits, stated plainly

- The manifest is independent of the engine but **not of me**: same author,
  cases and labels.
- Everything here is **synthetic and depth-2**. No claim about real law.
- 1.00 accuracy is against 36 cases on a corpus I designed *to make the
  ratified semantics work*. It is a consistency result, not a capability
  result, and it is **not comparable** to the earlier 0.94 — the corpus
  changed underneath it.
- What would actually falsify this is a second implementation of
  `SEMANTICS.md` by a different author. That is the independence the manifest
  still lacks, and it is the next thing to build.
