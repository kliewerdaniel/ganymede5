# Ganymede5 — Experiment 0

The smallest corpus in which refusal-only execution and defeasible execution
necessarily diverge. No compiler, no institution, no authority graph, no
corpus of 80 clauses. Just the semantics, and one case that could break them.

    python3 proto.py      # print the full outcome matrix with traces
    python3 test_proto.py # 19 assertions over that matrix

**Result: 19/19 pass. The probe did not break the engine.**

---

## The three regimes

| Regime | What it is |
|---|---|
| `refusal` | Hotting/Schuth discipline. The operation set has no precedence operator. Anything it cannot determinately resolve → `REFUSED` or a non-decisive `AUDIT` mark. |
| `refusal+prec` | Same, but a human translator **pre-encoded** the conflict as a deterministic branch. This is what "resolve the conflict at authoring time" actually buys. |
| `defeasible` | ASPIC+-lite. Strict rules, explicit attack rules, explicit precedence. Defeat is a *relation*, never a condition. |

The middle regime exists because without it the comparison is dishonest. A
control that refuses everything looks good against a system that answers
everything. The middle arm shows what the *usual* practical answer looks like —
and its trace is the finding: it decides confidently while admitting in the
same breath that no reason exists in the corpus.

## The outcome matrix

| Case | `refusal` | `refusal+prec` | `defeasible` |
|---|---|---|---|
| **C1** A vs B, statute defeats regulation | `REFUSED` | `DECIDED Y` (no reason) | **`DECIDED Y`, defeated: B** |
| **C2** defeater removed | `REFUSED` | `DECIDED Y` (no reason) | **`CONTESTED`** |
| **C3** rule needs `ROUND` | `REFUSED` + AUDIT | `REFUSED` + AUDIT | `REFUSED` + AUDIT |
| **C4** probe: attractive, unrepresented | `REFUSED` | `DECIDED Y` (no reason) | **`CONTESTED`** |
| **C5** unpromulgated + retroactive decree | `REFUSED` | `DECIDED` | **`INVALID`** |

C1 is the divergence. C2 is the same conflict with the defeater removed, and
the engine now refuses to answer — which is the property that makes the whole
thing an experiment rather than a lookup table. C3 shows all three regimes
agree when the format genuinely cannot express the case. C5 shows `INVALID`
never collapses into `CONTESTED`.

## The trace is the artifact

C1, defeasible:

```
status: DECIDED   conclusion: Y   defeated: B
  | defeat  B  A  explicit_authority_precedence  statute_01 §1
  | result  A  Y  defeated: B
```

C2, same corpus, defeater removed:

```
status: CONTESTED
  | defeat_disabled  B  A  explicit_authority_precedence
  | argument  A  statute_01  legislature  statute_01 §1  Y
  | argument  B  regulation_07  agency  regulation_07 §14  NOT-Y
```

Both arguments preserved, with sources, authorities, and citations. The
difference between the two runs is one field: whether the defeat relation is
`enabled`. That is the whole mechanism, and it is auditable.

## The probe (C4)

Rule B carries `specificity=99` against A's `1` — an attractive signal that
would settle the conflict if anything consulted it. **No represented defeat
relation exists.** If the engine returns `DECIDED` it has not reasoned; it has
invented a legal interpretation.

It returns `CONTESTED`. The corpus is semantically artificial on purpose: `X`,
`Y`, `NOT-Y`, and a legislature that outranks an agency. The question is
whether the machinery works before real law's ambiguity is introduced.

`specificity` is present in the dataclass and **never read by the defeasible
engine** — enforced by an AST check, not a comment.

## The test suite bites

19 assertions, but a passing suite proves nothing unless the tests can fail.
Five mutants, each a real failure mode this project exists to prevent:

| Mutant | Result |
|---|---|
| M1 — tiebreak on `specificity` (the invention failure) | **killed**, 5 tests |
| M2 — never return `CONTESTED` | **killed**, 3 tests |
| M3 — collapse `INVALID` into `CONTESTED` | **killed**, 1 test |
| M4 — silently approximate an unexpressible construct | **killed**, 2 tests |
| M5 — defeasible drops its refusal gate | **killed**, 2 tests |

5/5 killed. The suite is not vacuous.

## Two bugs this found

**In the corpus, not the engine.** C1 originally asserted that an *agency
regulation defeats a legislature statute* on grounds of
`explicit_authority_precedence`. That is backwards. The engine rejected the
defeat, logged `defeat_rejected: precedence does not hold`, and returned
`CONTESTED` — which was the correct response to an incoherent corpus. The
defeater direction was fixed to `statute defeats regulation`.

Worth recording: the first version of the "divergent case" was not merely
wrong but *incoherent*, and only a semantics that checks precedence catches it.

**In the tests.** `test_c4_translator_encoded_arm_does_decide` asserted on a
string I had written to be true rather than on the engine's behaviour, and the
`specificity` guard was matching its own docstring. Both fixed; the second now
walks the AST and fails on any `Attribute` access.

## What this does and does not show

**Shows:** the three-way distinction between `DECIDED` / `CONTESTED` /
`REFUSED` is implementable, and the traces are inspectable enough to tell a
represented defeat from an invented one.

**Does not show:** anything about real law, temporal rules, jurisdiction,
delegation, exceptions, or competing authorities. Deliberately artificial, as
instructed — the sequence is *one divergence → prove the semantics → expand the
corpus → test failure modes → introduce institutional structure.*

**Does not show** that the defeasible arm is *worth it*. C1 is one case where
the control refuses and the defeasible engine answers. Whether that is a real
capability gain or just this harness's structure is the actual experiment, and
it needs a corpus wide enough that the answer can come out either way.

## Layout

    proto.py      engine + the five cases + the printed matrix
    test_proto.py 19 assertions
    run.txt       last full run
    tests.txt     last test run
