# Ganymede5 defeat semantics — normative specification

**Status:** ratified. This document is normative. `semantics.py` implements
it. Where code and this document disagree, the document is the defect report.

This file exists because the moment defeat becomes recursive, "which argument
wins?" stops being an implementation detail and becomes a **semantic choice**.
Grounded, preferred, stable, and well-founded semantics are four different
answers, not four ways of computing one answer. Choosing one *because it makes
the tests pass* would recreate the exact failure this project exists to detect.

---

## 1. The governing constraint

> Never convert unresolved structure into an unjustified decision.

Ganymede5 does **not** maximise the number of decisions. `CONTESTED` is a
first-class, correct, and frequently correct answer. No ambition to decide
more justifies a tiebreak that is not warranted by a represented relation.

## 2. The three uncertainties, kept distinct

Conflating these is how a system talks itself into false confidence. They are
carried as a separate `uncertainty` field, orthogonal to `status`.

| kind | meaning | who reports it |
|---|---|---|
| `SEMANTIC` | the formalism does not determine a unique answer | engine |
| `CORPUS` | the corpus lacks a relation needed to settle the question | engine |
| `IMPLEMENTATION` | the semantics determine the answer; the engine got it wrong | **grader only** |

`IMPLEMENTATION` is deliberately **not emittable by the engine**. A system that
can diagnose its own implementation errors is not being audited. Only the
independent grader may assert it, and it is a test-harness finding, never an
outcome. A failing test is an implementation defect; it is never reported as a
property of the case.

## 3. Defeat is a fixpoint

Defeat relations are *not* applied in sequence. A defeater may itself be
defeated, so acceptance is defined as a fixpoint over the attack relation.

Notation. For a finite set of triggered rules Θ, an **active defeat** is
`(a, t)` where `a` defeats `t`, both are in Θ, the relation is enabled, and its
stated basis is satisfied by precedence. A rule is **unattacked** in a set S
when no member of S attacks it.

**Grounded consequence** (Dung), the only acceptance notion Ganymede5 adopts:

```
S₀   = Θ
S(n+1) = { r ∈ Θ : r is unattacked in S(n) }
```

S(n+1) is computed over all of Θ, **not** restricted to S(n). The iteration is
therefore not monotone, and this is not a bug: the grounded least fixpoint of a
finite abstract argumentation framework is obtained by iterating until the
sequence stabilises, and it need not stabilise.

Worked chain, D defeats C defeats B defeats A:

| n | S(n) | why |
|---|---|---|
| 0 | {A,B,C,D} | all triggered rules |
| 1 | {D} | D is unattacked |
| 2 | {A,B,D} | C is now attacked by an accepted rule |
| 3 | {B,D} | A is attacked by B, which has returned |
| 4 | {B,D} | stable |

Accepted = {B, D}. C is out, so **C's defeat of B does not stand**, so B
survives, so **B's defeat of A stands**.

This is not a quirk. It is how a general rule and an exception to it coexist:
both are in force, and the exception governs only where it applies. Whether the
exception reaches *this* case is a question about applicability, and
applicability is not represented in the corpus. Ganymede5 must therefore report
the contest rather than resolve it.

## 4. The ratified answers

Each `?` from the research question, now a decision rather than an open item.

### 4.1 Acyclic defeat → grounded consequence

Adopt Dung grounded semantics. No preference, priority, recency, or
adjudicative-weight ordering is used to break a contest. If the grounded
extension is contradiction-free and determinate, report `DECIDED`; otherwise
`CONTESTED` with `uncertainty=CORPUS`.

### 4.2 Mutual defeat (cycle) → `CONTESTED`, `SEMANTIC`

A cycle has no well-founded argument set, so grounded semantics does not
determine an answer. **Ganymede5 does not resolve cyclic defeat by default.**

This is a positive commitment, not a limitation to be engineered away later. A
`{B,C} → {} → {B,C}` oscillation is a report that the formalism is
indeterminate, and indeterminacy is a finding. Resolving it would require a
preference ordering over arguments — which is precisely a priority system
wearing a formalism's clothes, and precisely what C2, C3, and F1–F6 test for
and forbid.

`CONTESTED` is reported with the cycle members named in the trace, so the
contest is contestable rather than merely withheld.

### 4.3 Multiple admissible extensions → `CONTESTED`, `SEMANTIC`

Preferred and stable semantics both resolve an unresolved framework by
admitting exactly one extension. Both require a preference relation. Ganymede5
has none and will not invent one. If more than one extension is admissible under
grounded semantics, the contest is reported as `CONTESTED`.

### 4.4 Self-defeat (a defeats a) → `INVALID`

A rule defeating itself is a defect in the **corpus**, not an unresolved
question. The corpus asserts something incoherent, and no amount of
argumentation licenses an outcome on it. This is deliberately a *different state
from* `CONTESTED`: "your norm is malformed" and "your norm is genuinely open"
must never be reported the same way. Same for cycles *within a single
self-referential rule set* — those are `INVALID`; cycles *between distinct
rules* are `CONTESTED` per 4.2.

### 4.5 Non-convergence → `CONTESTED`, `SEMANTIC`

If iteration exceeds the convergence bound the operator is treated as having no
stable fixpoint. The bound is `2·|Θ| + 2`, which is ample for finite acyclic
frameworks and terminates the cyclic oscillation in 4.2. Fail closed.

### 4.6 What is never a tiebreak

`rank`, `specificity`, `recency`, `confidence`, `order_index`,
`text_similarity`, `length`, and corpus ordering are **not** consulted to
resolve a contest under any circumstances. `rank` is read only where the corpus
explicitly states rank precedence as the *basis*. An AST test enforces that the
defeat module never reads these fields.

## 5. Status vocabulary

Unchanged and deliberately small. `CONTESTED` and `INVALID` are not failures.

| status | meaning |
|---|---|
| `DECIDED` | rules entail an outcome; every defeat applied rests on a represented, basis-satisfying relation |
| `DEFEATED` | every triggered rule was defeated |
| `CONTESTED` | arguments for contradictory conclusions survive; the contest is reported, not resolved |
| `REFUSED` | the case requires a construct the representation cannot express |
| `NONFINDING` | no rule is triggered at the relevant time; absence of a finding is not absence of a fault |
| `INVALID` | the corpus violates a procedural invariant |

## 6. Consequence for the two axes

`DECIDED` with a represented defeat relation is the only cell that is both
decisive and justified. A regime that raises decisiveness while justification
stays flat has converted absent representation into a decision — and this
document makes that conversion impossible to perform silently, because there is
no tiebreak available to perform it with.
