# Ganymede5 Architecture — the separation of layers

Written after SIT v0.4. This records a structure that emerged from the
experiment rather than being designed into it up front. Several of these
layers were added because an earlier version failed, and the failure is part of
the rationale.

## The three questions

The central structural property, and the one that took the longest to see
clearly. These are three different questions belonging to three different
parties:

| Question | Answered by | Artifact |
|---|---|---|
| What observations were supposed to exist? | the neutral corpus | `corpus_export.json` |
| What does an implementation derive from the corpus? | each implementation | `impl_b/c/d.json`, `run_defeasible()` |
| Did we actually observe and compare all of them? | the instrument | `compare_impls.py` |

`corpus_export.json` is not a fixture. It is the **epistemic boundary** of the
experiment: the neutral statement of what was supposed to be observed, owned by
neither A nor any independent implementation.

This mirrors the separation the project was aiming at from the beginning,
between an evaluator and the thing being evaluated — applied, recursively, to
the evaluator itself.

### Why the boundary has to be neutral

The coverage invariant reads expected ids from `corpus_export.json`, never from
A's case list. This is not tidiness. If the expected set were derived from A,
then any case A failed to register would be invisible to the check, and the
instrument would inherit exactly the blind spot it exists to detect.

That is not hypothetical. `compare_impls.py` once compared 36 of 41 cases and
printed `VERDICT: A and B agree on every case where the spec is decisive` — and
the five it dropped were Family H, the adversarial family added specifically to
test the newest specification text. It reported success while excluding the
cases most likely to disagree.

A harness that drops cases cannot find disagreement in them. So coverage is now
verified against a source the implementations do not control, and any mismatch
is fatal:

```python
expected_ids == A_ids == B_ids == compared_ids      # fatal on any difference
```

## The layers

```
                    SPECIFICATION  (SEMANTICS.md, CORPUS_FORMAT.md)
                         │          pinned by digest in SPEC-FREEZE.json
                         │          a change requires a recorded decision
                         ↓
       NEUTRAL CORPUS ──→ IMPLEMENTATION  (A, B, C, D — independent contexts,
        (corpus_export)      four languages, four representations)
                    │              │
                    └──────┬───────┘
                           ↓
                     OBSERVATION  (result records)
                           ↓
                INDEPENDENT MEASURE  (compare_impls.py, adversarial_measure.py,
                           │            spec_freeze.py — none of which may
                           ↓            redefine the terms of evaluation)
              DISAGREEMENT / PASS / NO-FINDING
```

The critical asymmetry: **the thing evaluating the loop cannot silently redefine
the terms under which it is being evaluated.** A disagreement routes outward to a
recorded semantic decision or an implementation fix. It never routes
automatically back into the specification.

## The rule, and why it is mechanical

> **Do not modify the specification to make the measurement apparatus pass.**

Without a check, that is a sentence. And this project has already established
that documented intent is not enforcement: `SEMANTICS.md` declared a governing
constraint while the implementation enforced five invariants the document never
mentioned — SPECIFICATION FAILURE, invisible because the rule existed only in
prose.

So `SPEC-FREEZE.json` pins a SHA-256 digest of every normative file, and
`spec_freeze.py` fails on any unrecorded change:

```
FATAL -- SPECIFICATION DRIFT. A pinned normative file changed
without a recorded semantic decision.

  SEMANTICS.md   expected 91e25e7fe40a7f95, found 343bfa9c8f5f7a06
```

Three decisions are currently recorded (v0.1 ratified, v0.2 corpus-integrity
chapters, v0.3 Family H and the budget distinction). Each names the evidence
that surfaced the change, because a spec edit with no evidence of provenance is
how the loop closes.

`adversarial_measure.py` includes the drift detector, so the freeze cannot
quietly degrade into a check nobody runs.

### The closed loop this prevents

```
specification → implementation → measurement → specification modification → ↺
```

Under that loop the system converges by optimising itself against its own
evaluator, and every convergence point is a place where the terms of evaluation
were quietly rewritten. The v0.2 and v0.3 spec revisions were both *warranted* —
each closed a documented gap surfaced by an independent implementation — and
both are recorded with their evidence. The distinction being preserved is not
between good and bad spec edits. It is between an edit that **says what it is
doing and why** and one that a later reader cannot distinguish from ordinary
bug-fixing.

## The epistemic failure stack

Six categories, from `FAILURE-TAXONOMY.md`. They are layered — a defect in
layer N is invisible to layer N-1 unless N-1 was built to look for it:

```
CORPUS FAILURE              the intended case is malformed
SPECIFICATION FAILURE       a rule exists in code, not in the specification
IMPLEMENTATION FAILURE      code violates the specification
TEST FAILURE                a test exists but does not execute
MEASUREMENT FAILURE         the instrument silently excludes observations
```

`VACUOUS` cuts across the layers rather than sitting in the stack: something can
technically satisfy a requirement without ever exercising the condition that
requirement governs. D satisfied §6.3 structurally — it has no budget to exhaust,
so it never faced the choice. D was correct, and its agreement proved nothing
about the clause.

`MEASUREMENT FAILURE` is qualitatively different from the rest: the others
produce visible red. This one produces green while the system is wrong, which
makes the instrument an *amplifier* of false confidence rather than merely a
weak check.

The taxonomy also caught the measurement system itself. The first adversarial
detector dropped a case from B's output — the easy direction, which the old
`missing` check would have caught anyway. The historical bug was the opposite:
A never registered Family H, so those ids existed in neither comparison set. The
detector was fixed against the historical failure rather than made green:

```
measurement target → adversarial test → wrong failure model → false confidence
```

That is the same layered structure, one level up, and it is the reason the
negative control exists: a detector that has only ever passed cannot be
distinguished from one that cannot fail.

## What the instrument reports, and what it does not

Measurement vocabulary in place of pass/fail, because the informative states are
not failures:

| State | Meaning |
|---|---|
| `DERIVED` | follows from the specification, with a quotable section |
| `EXERCISED` | a corpus case actually drives this path |
| `VACUOUS` | clause satisfied, governing condition never occurred |
| `UNEXERCISED` | specified, but nothing reaches it |
| `COINCIDENTAL` | implementations agree because the spec is silent |
| `DISAGREEMENT` | they differ; attribution requires reading the spec |

Current honest state, preserved rather than smoothed:

- 41/41 agreement across four implementations — **agreement**, not correctness.
- 16 of 18 tracked fields `DERIVED`; **6.3 is `VACUOUS`**; `SEMANTIC` rests on a
  single corpus case.
- Whether an operational limit is epistemically inert is **implementation-
  dependent**. A specification can constrain how a limit is *reported*; it
  cannot stop one engine inventing a limit another never needed.
- Seven adversarial detectors fire, one of which is a negative control proving
  the others can fail. **This is not completeness.** It is a sample of modes
  found, not an enumeration of all modes.

## The gate

No governance-decomposition corpus until the observability layer demonstrates
that it can detect failures introduced independently of the semantic and
implementation layers.

That bar is met for the classes enumerated, with a negative control, and *not
claimed* to be met in general. What has actually been established is narrower
and more useful:

> **Ganymede5 can now detect several ways in which Ganymede5 could falsely
> conclude that Ganymede5 worked.**

The project began by asking whether governance can be modelled formally and
evaluated. It has turned into a study of the layers *underneath* that question —
specification, implementation, test suite, measurement apparatus — each capable of
manufacturing a conclusion the layer beneath it never established. An evaluator
whose own observational limits are represented as first-class objects is the
precondition for the original question being worth asking.