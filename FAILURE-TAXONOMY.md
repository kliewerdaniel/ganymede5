# Ganymede5 Failure Taxonomy

Each entry is a way a layer of this system converts a defect into an apparent
result. Every one of these has actually occurred here; none is hypothetical.

The taxonomy is layered. A failure in layer N is invisible to layer N-1 unless
layer N-1 has been built to look for it — which is the entire argument for
treating the measurement apparatus as part of the epistemic system.

## SPECIFICATION FAILURE

A rule exists in the implementation but not in the specification.

- **Observed:** A enforced five corpus-integrity invariants that appeared in
  neither `SEMANTICS.md` nor `CORPUS_FORMAT.md`. Implementation B, reading only
  the specification, disagreed on E1–E5 — five cases, one cause. The invariant
  layer had never been written down.
- **Also observed:** absent values acquiring normative meaning. Absent
  `effective_from` silently became `-inf`; an exhausted iteration bound
  silently became `SEMANTIC`; declaration order silently became an atom
  preference.
- **Signature:** an implementation behaves sensibly and the specification gives
  no reason for it. Nobody is wrong; the rule simply is not there.
- **Detection:** an independent implementation, from the written text alone,
  disagrees in ways that are individually defensible.

## IMPLEMENTATION FAILURE

The implementation violates specified semantics.

- **Observed:** B's first version rejected *unrecognized* defeat bases but not
  *recognized-and-unsatisfied* ones, letting an invalid authority-precedence
  defeat through. B found and fixed it itself.
- **Observed:** A's `chain_succession` relation falling through to generic rank
  validation. In a cyclic case rank destroyed the cycle and the engine reported
  a decision with no represented basis. M2 guards it.
- **Signature:** the specification is clear and the code still diverges. The
  offending case IS the diagnosis.
- **Detection:** mutation testing, and disagreement on a case where the
  specification is not ambiguous.

## TEST FAILURE

A test exists but does not execute.

- **Observed:** M12, M13 and M14 all survived. The suite reported `Ran 67 tests
  ... OK`. The new tests were module-level functions that `unittest` never
  collected. Moving them into a `TestCase` raised the count to 71.
- **Signature:** a guarantee with a test that never runs. The suite is green
  and the property is unguarded.
- **Durable rule:** *a test that does not increase the collected count is not a
  test.*
- **Detection:** compare the collected test count against the number of test
  definitions. `adversarial_measure.py` demonstrates the failure directly by
  planting a module-level test that would fail if collected, and observing that
  the suite passes.

## CORPUS FAILURE

The intended semantic case is malformed.

- **Observed:** the original G2 fixture was supposed to test contradictory
  terminal rules, but both asserted the same conclusion. G1 and G5 appeared to
  share a graph with opposite expected labels, which was really a confound
  between defeat structure, rule conclusions, and post-grounding conflict.
- **Observed:** H2's first fixture used an executive rule as a defeater under
  `explicit_constitutional_supremacy`, which validation correctly rejected. The
  fixture was wrong, not the engine.
- **Signature:** an expected result that cannot be derived from the case as
  written. The temptation is to "fix" the engine.
- **Detection:** construct the case and check whether the specification alone
  licenses the expectation.

## MEASUREMENT FAILURE

The instrument silently excludes relevant observations.

This is the most dangerous category, because the other four all produce visible
red. This one produces green.

- **Observed:** `compare_impls.py` compared 36 of the corpus's 41 cases and
  printed "VERDICT: A and B agree on every case where the spec is decisive." The
  five omitted cases were Family H — the entire adversarial family, introduced
  specifically to test the newest specification text.
- **Why it matters:** the omitted cases were not a random sample. They were
  precisely the cases most likely to disagree. A harness that drops cases
  cannot detect disagreement in them, and coverage inferred from a successful
  run is not coverage at all.
- **Signature:** an aggregate figure with no independently verified denominator.
- **Detection:** enforce the invariant rather than document it.
  `expected_ids == A_ids == B_ids == compared_ids`, fatal on any difference,
  with the expected set read from the **neutral corpus export** and never from
  A — otherwise the instrument inherits the blind spot it exists to detect.

## CROSS-LAYER FAILURE

A defect in one layer is invisible to the layer beneath it because the layer
above reports success.

- **Observed:** B satisfied §6.3 *structurally* — its propagation cannot
  exhaust a budget, so it never faced the choice between `SEMANTIC` and an
  operational error. B was correct and its agreement proved nothing about the
  clause. F-1 existed because A *did* have a budget and converted exhaustion
  into an epistemic claim.
- **Signature:** a specification clause satisfied by an implementation that
  never encounters the condition the clause governs. Reported as a pass.
- **Detection:** the `vacuous` state in the measurement vocabulary. Different
  from `pass`, different from `fail`.
- **Consequence for the research question:** whether an operational limit is
  epistemically inert is *implementation-dependent*. A specification can
  constrain how a limit is **reported**. It cannot prevent one engine from
  inventing a limit another has no reason to have.

## Measurement vocabulary

Binary pass/fail is inadequate. The state that matters is usually not a failure.

| State | Meaning |
|---|---|
| `DERIVED` | the value follows from the specification, and the implementer can quote the section that compels it |
| `EXERCISED` | a corpus case actually drives this code path |
| `VACUOUS` | the clause is satisfied, but the governing condition never occurred |
| `UNEXERCISED` | specified, but no case reaches it |
| `COINCIDENTAL` | implementations agree because the specification is silent, not because it determined the value |
| `DISAGREEMENT` | they differ; attribution requires reading the specification |

`COINCIDENTAL` is the one that has historically been mistaken for a result. C
independently chose `NONE` for `REFUSED` uncertainty while v0.2 was silent
there; it happened to match A and B. That was luck. v0.3 makes it derivable.

## The pattern

Each layer can manufacture an apparent conclusion that the layer beneath it
never established:

```
measurement apparatus  -- may drop cases, or hide a defect in an aggregate
        ^
test suite             -- may not collect a test that exists
        ^
implementation         -- may violate a rule, or satisfy one vacuously
        ^
specification          -- may omit a rule the implementation enforces
        ^
corpus                 -- may be malformed such that the expected result is unfounded
```

This is the project's actual research question, and it arrived by accident:

> Can we construct a computational governance model in which the system cannot
> silently transform uncertainty, absence, implementation behaviour, or
> measurement failure into apparent knowledge?

The governance decomposition corpus is not blocked by lack of time. It is
blocked until the measurement apparatus can be shown to detect its own failure
modes — which is what SIT v0.4 does, for five of the six categories above.