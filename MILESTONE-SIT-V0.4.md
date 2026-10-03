# SIT v0.4 — Measurement Integrity and Observability

Date: 2026-10-03
Baseline: v0.3 frozen at `9e110b1` · Status: **FROZEN**

## Scope

No new semantics. No new corpus families. No delegation, jurisdiction, Fuller
conditions, or governance decomposition. v0.4 exists to close the
instrumentation loop, because the apparatus was found to be able to report
success while measuring the wrong thing.

Every semantic result from v0.3 stands unchanged and is not re-litigated here.

## The finding that motivated this milestone

`compare_impls.py` compared **36 of the corpus's 41 cases** and printed:

```
VERDICT: A and B agree on every case where the spec is decisive.
```

The five omitted cases were Family H — the adversarial family added in v0.3
*specifically to test the newest specification text*. They were not a random
sample. They were the cases most likely to disagree.

So the harness had produced the exact failure mode the v0.3 experiment exists
to detect, and it reported it as success. The 36/41 figure was real; the
inference drawn from it was not.

## Change 1 — the coverage invariant, enforced rather than documented

```python
expected_ids == A_ids == B_ids == compared_ids      # fatal on any difference
```

Expected ids are read from `corpus_export.json`, the neutral interchange file
that every independent implementation reads. They are **not** derived from A's
case list. That distinction is load-bearing: if the expected set came from A,
any case A failed to register would be invisible to the check, and the
instrument would inherit precisely the blind spot it exists to detect. Duplicate
ids in the export are also fatal.

The harness now exits non-zero and prints no agreement figure when the sets
differ:

```
FATAL -- MEASUREMENT FAILURE. Refusing to report agreement.
  A        is MISSING 5 case(s): H1, H2, H3, H4, H5

Nothing below is reported, because nothing below would mean anything.
```

## Change 2 — the adversarial measurement run

`adversarial_measure.py` seeds five defects, each of which has previously
reproduced a successful run in this project, and asserts the apparatus refuses
to report success.

| # | Failure mode | Historical evidence | Detector asserts |
|---|---|---|---|
| 1 | **Omitted case** | harness reported 36/41 agreement | A omitting Family H is fatal and named |
| 2 | **Uncollected test** | M12–M14 survived while the suite printed OK | a planted module-level test is provably ignored |
| 3 | **Unreachable branch** | H5 passed trivially; nothing could starve the budget | `DEFEATED` is never emitted across 41 cases |
| 4 | **Vacuous satisfaction** | D satisfied §6.3 structurally, proving nothing | starved budget → operational error; real cycle → `SEMANTIC` |
| 5 | **Silent disagreement** | aggregates can hide a single adversarial defect | corrupting H3 is detected *and localised* |

Result: **5/5 detected.**

## Change 3 — a negative control, because detectors that only pass prove nothing

An assertion that cannot fail is indistinguishable from a broken one. So the
sixth check **removes the coverage invariant and requires the omitted-case
detector to stop firing**:

```
detector can fail   DETECTED
    with the invariant removed the harness reported SUCCESS over 36 of 41
    cases -- exactly the v0.2 defect -- so the detector is testing the
    invariant and not something else
```

This also caught a mistake in the detector itself. The first version dropped a
case from **B's** output — the easy direction, which the original harness's
`missing` check would have caught anyway. The historical bug was the opposite:
**A** never registered Family H, so those ids existed in neither comparison set
and `missing` never saw them. The detector now reproduces the real defect. An
adversarial test that tests the easy direction is a passing test that proves
nothing, which is TEST FAILURE wearing a different hat.

**6/6 detectors fired.**

## Change 4 — the no-self-modification rule, made mechanical

`SPEC-FREEZE.json` pins a digest of every normative file; `spec_freeze.py`
fails on any unrecorded change; `adversarial_measure.py` seeds a silent
spec edit and requires the freeze check to catch it (detector 6).

Written because documented intent is not enforcement. `SEMANTICS.md` once
declared a governing constraint while the implementation enforced five
invariants the document never mentioned. A rule nobody can fail is not a rule.

Three decisions are recorded (v0.1 ratified, v0.2 corpus-integrity chapters,
v0.3 Family H and the budget distinction), each naming the evidence that
surfaced it. Both v0.2 and v0.3 edits were *warranted*; what is preserved is
that an edit cannot be mistaken for ordinary bug-fixing.

`ARCHITECTURE.md` records the resulting separation: the neutral corpus owns
what was supposed to be observed, the implementations own what they derive, and
the instrument owns whether all of it was actually observed. Three questions,
three parties.

## State at freeze

```
78 tests, OK
19/19 mutants killed
41/41 cases, coverage invariant verified against the neutral corpus
7/7 adversarial detectors fired, including the negative control
spec freeze v0.3 verified; an unrecorded spec edit is fatal
4 implementations, 4 languages, 4 representations, 0 disagreements
2 fields known not to transfer: 6.3 (vacuous), SEMANTIC (single-case)
```

`FAILURE-TAXONOMY.md` records the six categories with their observed
instances, including the cross-layer case where a defect in one layer is
invisible to the layer beneath it because the layer above reports success.

## What is NOT claimed

- **Not detector completeness.** Seven checks fire. `adversarial_measure.py`
  says so in its own output. An eighth may exist, and the honest position is
  that the list is a sample of modes found, not an enumeration of all modes.
- **Not that the taxonomy is stable.** The cross-layer category (`VACUOUS`) was
  added only because D's result forced it. It did not exist as a category before
  an implementation made it necessary.
- **Not a semantic result.** Nothing about defeat, grounding, or legal
  reasoning changed. `SEMANTICS.md` was not edited in this milestone, by design:
  a specification rewritten to satisfy its own instrument is no longer evidence
  of anything.
- **Not governance progress.** The decomposition corpus remains deferred. This
  milestone is the precondition, not the work.

## Why vertical before horizontal

The apparatus was able to report success while comparing 36 of 41 cases. Every
further capability — delegation, jurisdiction, institutional decomposition —
would have been measured by that apparatus. Adding horizontal scope before the
instrument is verified does not produce more evidence; it produces more
confidently-reported measurements of a system that may be silently wrong in six
distinct ways.

That is the project's own recurring lesson, applied to itself: an implementation
needs a value for an absent situation, and the placeholder acquires normative
meaning unless something explicitly denies it. A measurement apparatus is an
implementation. It needs the same discipline.