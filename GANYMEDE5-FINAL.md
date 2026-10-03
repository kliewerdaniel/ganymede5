# Ganymede5 — Final State Record

**Status: FROZEN.** Date of freeze: 2026-10-03. Spec `SEMANTICS.md` v0.3, digest
`91e25e7fe40a7f95…`. Corpus 41 cases / 8 families, digest `1d47d997ebcc17da…`.

This document records the boundary of what Ganymede5 demonstrated. It is written once,
at closure, and is not edited to improve a number. Where a claim below is weaker than
the project's earlier README implied, the weaker claim is the true one.

---

## What Ganymede5 is

A research artifact testing whether a normative computational system can keep
**specification**, **implementation**, **observation**, and **evaluation** distinct from
one another while reasoning over defeasible structures. It is a measurement-integrity
laboratory that happens to contain a small defeasible-reasoning engine.

## The question it investigated

> When normative reasoning cannot be settled by a single answer, and something must
> return the system's own guess in the shape of an answer — can every place a guess
> could acquire authority be made a named, isolated, mechanically checkable layer?

## What was actually demonstrated

- A **neutral, label-free corpus** of 41 synthetic cases in 8 families. Independently
  enumerated: the comparison harness derives its expected case set from
  `corpus_export.json`, never from any implementation's own output.
- **Three independent implementations** (Python, Node, Rust×2 lineages) reaching 41/41
  agreement against the frozen specification, written from the three public normative
  files alone.
- **Agreement separated from derivation.** `DERIVATION-SCORECARD.md` records 16 of 18
  tracked fields as `derived` — the implementer quoted the section that compels the
  value — rather than merely coincident.
- **Mechanical specification-drift detection.** `SPEC-FREEZE.json` pins a digest of
  every normative file; `spec_freeze.py` fails loudly on any unrecorded change.
- **Seven adversarial measurement detectors**, all firing, including a **negative
  control** that removes the coverage invariant and reproduces the historical silent
  success — proving the detectors can fail rather than merely always pass.
- **A frozen failure taxonomy** of five layered categories, each with observed
  instances, including the `MEASUREMENT FAILURE` class that produces *green while the
  system is wrong*.
- **VACUOUS as a third evidentiary state**, distinct from both pass and fail: a clause
  can be satisfied by an implementation that never enters the region the clause governs.
- **A reproduced stale-artifact failure**: the 36/41 omission incident, and a stale
  result file caught refusing to score.

## What was NOT demonstrated

- That the seven failure modes are **exhaustive**. They are a sample of modes found.
- That the specification is **semantically correct**. It is pinned and determinate, not
  validated. It is a frozen decision, not a verified truth.
- That the engine reaches **any legal conclusion**. The corpus is synthetic. No real
  statute, case, or constitution is encoded.
- That **agreement is capability**. One author wrote the semantics, the corpus, and the
  expected-output manifest. **No external human domain-expert validation occurred.**
- That the **fourth implementation agrees**. `impl_b` is frozen at spec v0.1 and
  disagrees on 6 of 41 cases (see below). "4 implementations, 0 disagreements" was
  asserted in earlier revisions of the README and was **not reproducible**; the closure
  audit corrected it.
- That the **governance model works**. It does not exist and was deliberately not built.

## Implementation identities

| | Language | Representation | Result at closure |
|---|---|---|---|
| A | Python | set-based grounded fixpoint | reference |
| B | Rust | `u64` bitwords + Warshall closure | **35/41**, frozen at spec v0.1 |
| C | Node | BigInt masks + Tarjan SCC | 41/41 |
| D | Rust | labelled attack graph, attacker-count propagation | 41/41 |

`impl_b.json` (36 cases, v0.1) is preserved unmodified. The current-spec run is
versioned separately as `impl_b-v0.3.json`. B was **not** advanced to v0.3, because
doing so would destroy the only surviving record of what the specification failed to
say — the evidence that produced the v0.2 decision.

## Derivation status

16 of 18 fields `derived`. `budget exhaustion ≠ SEMANTIC` (§6.3) is **`VACUOUS`** for D,
not derived: D's propagation is monotone within a round, so it never allocates a budget
and never faces the choice. Correct, and evidentially empty.

## Mutation status

19/19 mutants killed, reproduced from a clean checkout.

## Measurement-detector status

7/7 detectors fire, including the negative control.

## Known limitations (frozen deliberately, not repaired)

1. **§6.3 is vacuously satisfied.** An implementation with no iteration budget cannot
   violate a rule about budget exhaustion. Whether an operational limit is epistemically
   inert is therefore **implementation-dependent and not settled by a specification**.
2. **`SEMANTIC` rests on a single case** (G4, the mutual cycle). One case cannot
   distinguish "the spec determines this" from "the implementer had one worked example."
3. **`DEFEATED` is reserved, never reached** (0 cases). Grounded/oscillation semantics
   cannot produce it. It was reserved rather than fabricated into an invalid fixture,
   because fabricating one would have been CORPUS FAILURE.
4. **Single-author corpus and manifest.** The largest limitation. Unpapered.
5. **Implementation B is stale** at spec v0.1; see above.

These are **bounded limitations of a complete artifact**, not defects blocking closure.
Each was left frozen on purpose. Repairing 1 or 2 to improve a coverage number would be
cosmetic semantic expansion, which the project's own rules forbid.

## Why development stopped

The closure gate was evaluated against the frozen specification, the neutral corpus, all
four implementations, the mutation suite, the digest freeze, and the adversarial
detectors. Every gate reproduces from a clean checkout. The one discrepancy found —
B's 6 disagreements against an overstated README — was a **documentation defect, not a
semantic one**, and was corrected without touching the specification, the corpus, or any
implementation.

Development stopped because the next question cannot be asked inside this repository.

## The open research question

> Given an independently specified governance corpus, can Ganymede decompose
> institutional tasks while preserving the distinction between authorization,
> delegation, execution, evaluation, and normative judgment, without allowing the
> evaluator to rewrite the criteria by which its own decomposition is judged?

This is blocked **structurally**, not by scheduling: authoring that corpus here and
evaluating it here would make the author the evaluator — precisely the arrangement this
repository exists to separate out. It requires an independently specified corpus, the
same requirement already applied to `SEMANTICS.md`.

## What Ganymede6 may inherit

- The measurement-integrity layer as a reusable component: specification freeze, corpus
  boundary, artifact identity, coverage invariant, derivation record, negative control,
  failure classification.
- The **VACUOUS** evidentiary state and the agreement/derivation distinction.
- Defeasible reasoning with a written, ratifiable semantics.
- The three-layer separation that stopped self-measurement: independent implementation,
  neutral corpus, digest-pinned specification.
- The compiled lineage as empirical failure evidence.

## What Ganymede6 must NOT do

- Must not retroactively change Ganymede5's specification, corpus, or results.
- Must not repair Ganymede5's known limitations in order to make Ganymede6 look stronger.
- Must not treat Ganymede5's 41/41 as evidence of semantic correctness.
- Must not inherit the assumption that four implementations agreeing proves determinacy
  — three agree, and the fourth's disagreement was informative precisely because it was
  a stale vintage rather than a silent fit.

---

**Ganymede6 is a new research experiment.**

**Ganymede5 is historical evidence.**

**Ganymede6 may learn from Ganymede5.**

**Ganymede6 must not silently rewrite Ganymede5.**