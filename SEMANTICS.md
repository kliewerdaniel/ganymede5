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
| `CORPUS` | the corpus is the obstacle: it lacks a relation needed to settle the question, **or it is itself defective** | engine |
| `IMPLEMENTATION` | the semantics determine the answer; the engine got it wrong | **grader only** |

The engine must additionally report `NONE` when no unresolved question remains
**and** the corpus is well-formed. These are the only three engine-emittable
values.

> **2.1 Uncertainty for a defective corpus.** A corpus that violates a validity
> invariant (§5) is reported `INVALID` with `uncertainty=CORPUS`. It is *not*
> `NONE`. `NONE` asserts two things: that the semantics determined an answer,
> and that nothing is wrong with the corpus. A malformed corpus satisfies
> neither, and `NONE` would let a broken corpus be read as a clean query that
> simply found nothing. `INVALID/CORPUS` is what distinguishes "your corpus is
> broken" from `NONFINDING/NONE`, which means "your corpus is fine; nothing
> triggered". Collapsing those two is the exact error this section exists to
> prevent.

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
must never be reported the same way. Reported `uncertainty=CORPUS` per §2.1.
Same for cycles *within a single
self-referential rule set* — those are `INVALID`; cycles *between distinct
rules* are `CONTESTED` per 4.2.

### 4.5 Non-convergence → `CONTESTED`, `SEMANTIC`

If iteration exceeds the convergence bound the operator is treated as having no
stable fixpoint. The bound is `2·|Θ| + 2`, which is ample for finite acyclic
frameworks and terminates the cyclic oscillation in 4.2. Fail closed.

### 4.6 Absent values have no implied meaning

Every quantity that can alter a semantic ordering has **explicit ordering
semantics for its own absence**. `None`, `null`, missing, and empty are not
values that a host language may silently order. This rule exists because two
independent implementations chose two different readings and reached two
different verdicts on the same case.

- **Temporal (`effective_from`, `effective_to`).** A basis that requires a
  comparison is **unsatisfied when an operand is absent**. Absent is not −∞,
  not "always", not "the default". If the corpus does not state the temporal
  position a `explicit_lex_posterior` relation needs, the corpus has not
  asserted that relation, and an unasserted relation is not a warrant.
- **Precedence (`authority`, `rank`).** Absent authority is unsatisfied for any
  basis requiring authority ordering. Absent `rank` is unsatisfied for
  `explicit_rank_precedence`.
- **Dates gate triggers separately.** An absent date does not make a rule
  in-force or out-of-force; triggering is governed by the corpus's own state and
  is a separate question from precedence.

Fail closed, uniformly: **an unverifiable basis is an unsatisfied basis.**

### 4.7 What is never a tiebreak

`rank`, `specificity`, `recency`, `confidence`, `order_index`,
`text_similarity`, `length`, and corpus ordering are **not** consulted to
resolve a contest under any circumstances. `rank` is read only where the corpus
explicitly states rank precedence as the *basis*. An AST test enforces that the
defeat module never reads these fields.

### 4.8 What counts as a represented reason

`represented_reason` is a claim about provenance, so it is specified, not
inferred. It is `true` **only if** at least one enabled, basis-satisfying
defeat relation was applied, **and** every rule excluded from the grounded set
was excluded by such a relation. Specifically:

- The warrant must **originate in the corpus** as a declared relation. It is
  never an explanation the engine generated about why an outcome seemed right.
- An **authoring-time assertion** that a rule is justified does not qualify; it
  is a claim, not a relation.
- A relation whose basis is unsatisfied, or whose truth the implementation
  *inferred* where the corpus was silent, does not qualify.
- `false` is a substantive finding, not a default. It means the outcome is
  decisive **without** a represented warrant, which is the single most important
  thing this system measures.

An implementation that cannot distinguish "the corpus stated the reason" from
"the engine explained the reason" must report `false`.

## 5. Corpus validity: what makes a corpus defective

Defectiveness is **structural**, checked before any semantic reasoning, and is
distinct from indeterminacy. An indeterminate corpus is well-formed and
genuinely open; a defective corpus is not a corpus that argumentation can be run
on at all. Both are reported, neither is a contest, and neither may be reported
as a decision.

A corpus is **defective** (`INVALID`) if any of the following holds. Each is a
property of the corpus as written, decidable without argumentation:

| id | condition | why it is a defect |
|---|---|---|
| `F1_GENERALITY` | a defeat relation names a rule that does not exist | a relation to nothing cannot warrant anything |
| `F2_PROMULGATION` | a rule is unpromulgated | an unpublished rule is not in force, so it cannot defeat anything |
| `F3_NON_RETROACTIVITY` | a rule is retroactive **and** carries an `effective_from` | the rule claims to govern a period it postdates |
| `F5_NON_CONTRADICTION` | two rules share an id | identity is what defeat relations refer to; a repeated id collapses two arguments into one |
| `F7_CONSTANCY` | `effective_from >= effective_to` | an empty validity interval is a rule that is in force at no time |

**Precedence.** The validity check runs **first**, before triggering, before
precedence, and before iteration. A defective corpus has no Θ to ground, so a
semantic answer computed on it would be an answer about a corpus that does not
exist.

**These are not contestable.** `INVALID` is not `CONTESTED`. Nothing in the
defect depends on which rule wins, so there is no contest to report and no
extension to admit. This is the whole content of the distinction: `CONTESTED`
says *your corpus is fine and genuinely open*; `INVALID` says *your corpus is
malformed*. Reporting the second as the first tells a well-intentioned author
to keep arguing with a corpus that cannot be argued with.

## 5a. Proposition-level selection after grounding

Grounded consequence fixes **which arguments survive**. It does not by itself
fix **which single proposition is reported**.

> **5a.1.** If the surviving arguments of the grounded extension assert a single
> conclusion atom, that atom is the reported `conclusion`.
>
> **5a.2.** If the surviving arguments assert **two or more distinct conclusion
> atoms**, the extension is grounded and determinate but yields **no unique
> proposition-level conclusion**. `conclusion` is `null`.
>
> **5a.3.** If the surviving arguments assert contradictory conclusions (per
> `CONTRADICTS`) and no represented relation separates them, the result is
> `CONTESTED` with `uncertainty=CORPUS` — a genuine open contest.

5a.2 is **not** `CONTESTED`. Nothing is contested: no argument defeats another,
the extension is unique, and the grounding is determinate. Declaring a contest
would manufacture a conflict out of two compatible findings. The status remains
`DECIDED` — the semantics did determine the argument set — while `conclusion`
is `null`, because the semantics did not determine a proposition.

> **5a.4. Declaration order is not a selection rule.** The order in which rules
> appear in the corpus may be used to *present* a choice to a reader, never to
> *make* one. Naming the first-declared atom as *the* conclusion is a
> substantive preference relation wearing a formatting costume, and §4.6
> forbids it. An implementation that finds itself indexing a list to choose
> what to believe is performing an undeclared preference.

Where a display convention is wanted, report the full conclusion set alongside
`conclusion: null`. Showing the reader every surviving atom does not require
preferring one.

## 6. Status vocabulary

### 6.1 Every status has a defined meaning, or is declared reserved

A status that cannot be produced is worse than an absent one: it advertises a
capability the system does not have. Each status below therefore carries either
a production rule or an explicit reservation.

| status | produced when | uncertainty |
|---|---|---|
| `DECIDED` | a grounded extension exists and yields 0 or 1 unique conclusion | `NONE` |
| `CONTESTED` | a represented contradiction, or unresolved cyclic structure | `CORPUS` / `SEMANTIC` |
| `REFUSED` | the query requires a construct the representation cannot express | `NONE` |
| `NONFINDING` | the corpus is sound and no rule's condition holds | `NONE` |
| `INVALID` | a §5 validity invariant is violated | `CORPUS` |

**`DEFEATED` is RESERVED.** It is specified, implemented, and unreachable.

The reason is not that empty extensions are impossible — 27 of the 64
three-node defeat graphs do yield one. The reason is that every such graph also
oscillates, so §4.5 returns `CONTESTED/SEMANTIC` before the empty-extension
branch is reached. Emptying the extension destroys the fixpoint that defines
it. The state is therefore reserved pending a semantics under which a grounded
extension can be empty without being undefined — for example a defeasible
*query* whose support is wholly defeated while the framework remains well
founded. Do not remove this reservation by constructing a case; construct the
semantics first.

### 6.2 Precedence when conditions compete

Both conditions in this table can hold on one corpus. The order is normative.

1. **`INVALID` beats `REFUSED`.** A corpus that is structurally defective and
   unrepresentable reports `INVALID/CORPUS` (§5). The defect is knowable
   without the representation, so reporting `REFUSED` would let a malformed
   corpus hide behind a capability limit. Corpus H3 pins this.
2. **`INVALID` beats `NONFINDING`.** Nothing triggering is not evidence that a
   defective corpus is merely quiet.
3. **`REFUSED` beats `NONFINDING`.** An inexpressible query is not an absent
   answer.
4. **`NONFINDING` beats `DEFEATED`**, vacuously: `DEFEATED` is reserved (§6.1).

### 6.3 Operational limits are not epistemic results

`SEMANTIC` means *this framework has no well-founded extension*. It may be
returned only on a demonstrated oscillation.

An exhausted iteration bound is a fact about the caller's loop, not about the
corpus. An implementation that returns `SEMANTIC` when its budget runs out has
learned nothing and asserted everything. Implementations **must** raise or
report an operational error instead. The default bound is derived from |θ| and
provably suffices for a well-founded framework, so exhaustion indicates a
programming error.

This is the general rule the project keeps re-learning, now stated once:

> **Absence has no semantic meaning unless this specification explicitly
> assigns one.** A value a language or framework supplies by default — a null,
> an absent date, a missing branch, an exhausted bound, an unset field — must
> never acquire meaning because an implementation needed one.

Observed five times: absent `effective_from` read as `-inf`; absent
uncertainty defaulted to `NONE`; declaration order used as an atom preference;
an exhausted bound read as indeterminacy; and a status advertised that no
corpus could reach.

### 6.4 Specification completeness criterion

Every externally observable field must have: an enumerated domain; a semantic
definition for each permitted value; defined behaviour for absence; defined
behaviour for conflicting conditions; and defined precedence where conditions
compete. A field missing any of the five is underspecified, and agreement
between implementations on it is coincidence rather than derivation.
