# SIT v0.3 candidate findings — recorded, NOT applied

**Date:** 2026-10-03
**State:** findings only. No code changed. Deliberately unfixed while
independent implementation C is in flight, because editing A's semantics now
would move A's outputs mid-comparison.
**Rule:** where code and this file disagree, this file records what is wrong.

These came from the representation critique B raised in SIT v0.1, which was
correct and had not been acted on.

---

## F-1. `SEMANTIC` is emitted from a resource limit, not from a finding

`semantics.py::accepted` has two distinct exits returning `SEMANTIC`:

- line ~85: the operator oscillated — a genuine property of the framework.
- line ~90: `max_rounds` was exhausted — a property of the *budget*.

Reproduced against the real implementation:

```text
3-chain D→C→B→A, max_rounds=2
  → ({B,A,D}, 'SEMANTIC', ...)      # a well-founded, determinate chain
mutual cycle B↔A,  max_rounds=2
  → ({C,D},    'SEMANTIC', ...)      # a genuinely indeterminate framework
```

Two epistemically different objects — "this formalism has no well-founded
extension" and "my loop stopped early" — return the same value. §4.2 states
that indeterminacy is a *finding*. Budget exhaustion is not a finding; it is an
engine failing to look. Reporting it as `SEMANTIC` lets the engine assert
indeterminacy it has not established, which is the same class of error as A
declaring `INVALID/NONE` in v0.1 and as declaration-order selection in G3: a
representation artifact acquiring semantic meaning.

This is the general principle, stated once:

> **Absence has no semantic meaning unless the specification explicitly assigns
> one.** A value a language or framework supplies by default — `null`, an absent
> date, an exhausted loop bound, a missing default branch, an unset field — must
> never acquire meaning because the implementation needed one. Every default is
> a place where representation leaks into semantics unless the spec forecloses
> it.

Note this is the *fourth* instance of that one principle in this project:
absent `effective_from` (M14), absent uncertainty for `INVALID` (§2.1),
declaration order as an implicit atom preference (§5a.2), and now an exhausted
bound. Four defects, one root cause. That is worth more than four fixes.

**Candidate resolution.** Separate the two exits:

- `SEMANTIC` only on demonstrated oscillation / structural non-well-foundedness.
- Bound exhaustion becomes a distinct, non-semantic signal — `IMPLEMENTATION` is
  already reserved for exactly this (§2.1 forbids an engine *emitting* it, so
  it needs a different channel) or an explicit `assert`/raise, since in
  production `max_rounds` is computed from |θ| and provably suffices for a DAG.

**Not applied** pending C.

---

## F-2. Cycle detection is computed but not consulted

`semantics.py` computes `cycle_members()` structurally and independently — the
right representation, and better than inferring a cycle from iteration failure.
But its result never feeds the status decision. It is reported in the trace as
decoration.

Consequence: A asserts `CONTESTED/SEMANTIC` ("I know there is a cycle") when
what it has actually established is "my chosen operator did not stabilise."

This happens not to be *unsound* under grounded semantics, where
cycle ⟺ non-well-foundedness is a theorem — but it is unsound as a stated
claim, and it is fragile: it depends on a theorem the code neither cites nor
tests. Two different formalisms (preferred, stable) would break the inference
while leaving the code unchanged and silently wrong.

**Candidate resolution.** §4.2 should say which is which: name the cycle
structurally, and treat `SEMANTIC` as "a cycle exists in the defeat relation"
rather than "iteration failed." B's approach (adjacency matrix + separate
closure) is the right one and should be adopted in A.

**Not applied** pending C — this changes observable status in general, though
not on the current corpus.

---

## Sequencing

Per the standing plan, the order is unchanged:

```text
C returns → compare A/B/C → attribute disagreements to the spec
          → freeze v0.2 → rerun A/B/C → freeze v0.3 with F-1, F-2
          → expand corpus → only then delegation / jurisdiction / institutions
```

F-1 and F-2 are recorded as v0.3 inputs. Fixing them before the A/B/C
convergence is measured would destroy the measurement they came from.