# SIT v0.3 — Implementation Interoperability

Date: 2026-10-03
Spec: `SEMANTICS.md` v0.3 · Corpus: `corpus_export.json`, 41 cases
A baseline: `9e110b1` · Status: **FROZEN** — do not edit; this records the result.

## Result

```
cases compared: 41
  AGREE            41
  DISAGREE          0
  REPORTING only    0
```

Four implementations, four languages, four representations:

| | Impl | Language | Defeat-graph representation |
|---|---|---|---|
| A | reference | Python | set-based grounded fixpoint |
| B | v0.1 | Rust | `u64` bitwords + Warshall closure |
| C | v0.2 | Node | BigInt masks + Tarjan SCC |
| D | v0.3 | Rust | labelled attack graph + attacker-count propagation |

D is the first to reach 41/41. C reached 35/36 with one reporting-only
difference (`G4.defeated`), B was tested against v0.1 and disagreed on 7 cases
in five distinct ways — every one of which turned out to be a specification
gap rather than an implementation error.

## The number that is NOT the result

41/41 agreement does not establish that v0.3 is a good specification. It
establishes only that **no disagreement was produced** by this corpus. Two
implementations can agree on everything because the spec determines everything,
or because the corpus never reaches the places where it does not.

`DERIVATION-SCORECARD.md` separates these. D was asked to quote the section
that compels each value. It does: §6.1 for status vocabulary, §6.2(1) for
precedence, §4.8 for `represented_reason`, §5a.2 for the null conclusion. On 16
of 18 tracked fields, agreement is backed by derivation. That is the result.

## What did NOT transfer

**§6.3 is vacuous, not corroborated.** D's engine states that it discharges the
budget-exhaustion obligation "structurally rather than by a counter" — its
propagation is monotone within a round, so it never allocates a budget and never
faces the choice between `SEMANTIC` and an operational error.

This is a correct reading of the spec. It is not evidence the spec settles the
question. F-1 arose because **A** had a budget and converted exhaustion into an
epistemic claim. An implementation that never allocates one cannot confirm the
rule is determined; it can only decline to break it.

The honest conclusion: *whether an operational limit is epistemically inert is
implementation-dependent.* A specification can constrain how a limit is
**reported**. It cannot prevent one engine from inventing a limit that another
has no reason to have. This is a genuine limit on transfer, recorded as such.

**`SEMANTIC` remains single-case.** Only G4 (the mutual cycle) exercises it.
D reaches it by a different route than C, which is weak corroboration, not
enough. One case cannot distinguish "the spec determines this" from "the
implementer saw the example."

## v0.3 findings, in order of how much they cost

1. **§6.2 clause 1 was specified and not enforced.** Both refusal arms answered
   five defective corpora; on E3 the refusal arm returned `DECIDED`, because
   rule B still applied and the empty validity interval was invisible behind a
   confident answer. The old test *recorded this as a known limitation* — a
   test pinning a defect and calling it documentation. Now all three arms
   validate first (mutant M19).

2. **The precedence arm lost 0.27 decisiveness, correctly.** 1.00 → 0.73.
   Every point lost was one it was inventing on a corpus it never read.
   Justification stayed 0, so the finding survives and is better stated: a
   precedence rule buys decisiveness with the corpus's money.

3. **`DEFEATED` is reserved, not removed and not faked.** Corrected twice: first
   claimed unreachable because grounded extensions cannot be empty (false — 27
   of 64 graphs yield empty extensions), then found unreachable because every
   empty-extension graph also oscillates, so §4.5 fires before the
   empty-extension branch. The test enumerates all 64 graphs and pins that
   reasoning.

4. **The comparison harness silently compared 36 of 41 cases** and still printed
   "agree on every case where the spec is decisive." A harness that drops
   cases cannot detect disagreement in them. Fixed; Family H now compares.

## State at freeze

```
78 tests, OK
19/19 mutants killed
41 cases, 4 implementations, 4 languages, 4 representations
0 disagreements
16 of 18 fields derived rather than coincident
2 fields not transferred: 6.3 (vacuous), SEMANTIC (single-case)
```

## What is explicitly NOT claimed

- Not a capability result. The corpus was authored around this specification by
  the specification's author.
- Not legal validity. No human domain expert has validated any case.
- Not specification completeness. Two known gaps above, plus fields
  `CORPUS_FORMAT.md` does not fix (`defeated` on non-contested paths).
- Not that 41/41 will survive a fifth implementation or a different corpus.

## The question this now supports

> Can a normative computational specification remain stable when its
> implementation, language, representation, corpus, execution limits, and
> interpretation all change?

Four implementations agree on every case the corpus reaches, and 16 of 18
tracked fields were independently derived rather than coincidentally matched.
That is evidence the machinery is not an artifact of one Python program and one
carefully built corpus. It is not evidence the semantics are right.
