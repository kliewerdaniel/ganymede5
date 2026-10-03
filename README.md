# Ganymede5

**An experiment in whether a normative computational system can preserve the distinction between specification, implementation, observation, and evaluation — while reasoning over defeasible structures.**

This is a research artifact, not a product and not a governance tool. Nothing here evaluates a real law, government, or person. The corpus is synthetic and the domain is deliberately narrow. What it studies is the *epistemic plumbing* underneath normative reasoning — because that plumbing failed repeatedly, and in instructive ways.

Current state: **SIT v0.4, frozen.** For what that means, and more importantly what it does not mean, see [The boundary](#the-boundary-what-this-repository-is-and-is-not).

---

## The question

Ask a system something that normative reasoning cannot settle with a single answer, and something must return *the system's own guess* in the shape of an answer.

The usual defences are procedural: a confidence score, a refusal flag, a hedge. This project took a different route — **make every place a guess could acquire authority a named, isolated, and checkable layer.**

What emerged is not a governance model. It is a demonstration that these layers can be separated, plus an account of the ways they were caught quietly failing.

---

## Status

| | |
|---|---|
| Specification | `SEMANTICS.md` v0.3, 330 lines, **digest-pinned** |
| Corpus | 41 synthetic cases, 8 families |
| Implementations | 4 independent — Python, Rust (×2), Node — **3 at 41/41, B at 35/41** |
| Test suite | 78 tests |
| Mutation testing | 19/19 mutants killed |
| Measurement checks | 7/7 adversarial detectors, incl. a negative control |
| Licence | MIT |

```
$ python3 -m unittest test_proto test_families test_family_g
Ran 78 tests in 0.010s
OK

$ python3 mutate_g.py
19/19 mutants killed

$ python3 spec_freeze.py
all pinned files match their recorded digests.

$ python3 adversarial_measure.py
7/7 detectors fired
```

**Read the number, then read the caveat.** 41/41 is *agreement* — not correctness, not legal validity, not external validation. [Why it is not more](#what-is-not-claimed) is the most important section here.

---

## What this is and is not

**Is**

- A **defeasible-reasoning engine** with a written, ratifiable semantics: recursive defeat, cycles that refuse to resolve, and a distinction between *no answer exists* and *the answer was never permitted*.
- A **transfer experiment** — four implementations written from the same specification alone, measuring whether the specification *determines* behaviour rather than merely permitting one implementation.
- A **measurement-integrity laboratory**: the largest body of work here is about how an evaluation apparatus fails while reporting success.
- A **handoff**. The next research question is deliberately unimplemented.

**Is not**

- **Not a governance model.** No institutions, delegation chains, jurisdiction, or separation of powers. Those are the next question, not this answer.
- **Not a legal system.** No real statute, case, or constitution is encoded. It has no opinion about any real government.
- **Not validated by domain experts.** The same author wrote the semantics, the corpus, and the expected-output manifest. This is the largest limitation and it is not papered over.
- **Not finished.** Two known gaps are documented and deliberately unrepaired (§6.3 is vacuously satisfied; `SEMANTIC` rests on a single case).

---

## The interesting part: four implementations, one specification

Four independent implementations were written against `SEMANTICS.md` and `CORPUS_FORMAT.md` alone — each forbidden from reading the others, the manifest, or the tests.

| | Language | Representation | Verdict |
|---|---|---|---|
| **A** | Python | set-based grounded fixpoint | reference |
| **B** | Rust | `u64` bitwords + Warshall closure | **35/41** — see below |
| **C** | Node | BigInt masks + Tarjan SCC | 41/41 |
| **D** | Rust | labelled attack graph, attacker-count propagation | 41/41 |

Three of four reach 41/41. That is a real result about specification determinacy — and the derivation scorecard is what makes it real rather than lucky.

### B is stale, and that is a finding rather than a defect in the specification

`impl_b` was written against **spec v0.1** and was never advanced. Its source contains no
reference to any of the five §5 corpus-validity invariants (`F1_GENERALITY`,
`F2_PROMULGATION`, `F3_NON_RETROACTIVITY`, `F5_NON_CONTRADICTION`, `F7_CONSTANCY`),
which spec v0.2 introduced. Run against the current 41-case corpus it disagrees with A
on exactly six cases, and every one is a §5 invariant B never learned:

| case | invariant A enforces | B's answer |
|---|---|---|
| E1 | `F2_PROMULGATION` — rule B is unpromulgated | `CONTESTED/CORPUS` |
| E2 | `F3_NON_RETROACTIVITY` — retroactive **and** carries `effective_from` | `DECIDED/NONE` |
| E3 | `F7_CONSTANCY` — `effective_from >= effective_to` | `DECIDED/NONE` |
| E4 | `F1_GENERALITY` — defeat names `GHOST`, which does not exist | `CONTESTED/CORPUS` |
| E5 | `F5_NON_CONTRADICTION` — two rules share id `A` | `CONTESTED/CORPUS` |
| H3 | `F7_CONSTANCY` | `REFUSED/NONE` |

C and D implement all five invariants and agree with A on all 41. So the disagreement
is **localised to B's vintage, not to the specification**: the semantics compels
`INVALID/CORPUS` here (§2.1, §5), B simply predates the clause.

This is left unrepaired on purpose. B is the frozen v0.1 artifact, and rewriting it to
match v0.3 would destroy the only surviving record of *what the specification failed to
say* — the exact evidence that produced the v0.2 decision. A stale implementation that
disagrees loudly is worth more than a refreshed one that agrees quietly. `impl_b.json`
(36 cases, v0.1) is preserved unchanged; the regenerated run is versioned separately as
`impl_b-v0.3.json`.

### Agreement is not derivation

`DERIVATION-SCORECARD.md` tracks **agreement** and **derivation** as separate columns. A field is `DERIVED` only if the implementer can quote the section of `SEMANTICS.md` that compels their value.

This distinction did real work immediately. Implementation D cited §6.2(1) as the reason a malformed-but-unrepresentable case resolves to `INVALID` rather than `REFUSED`. It was *correct* — and it also showed the rule had transferred, rather than the answer being guessed.

The same discipline is why D's agreement on §6.3 is recorded as **`VACUOUS`**, not as a pass. D's algorithm cannot exhaust an iteration budget, so it never faced the choice the clause governs. It satisfied the rule by never entering the region where the rule could distinguish anything. Correct, and evidentially empty.

> **A clause can be satisfied without ever exercising the condition it governs.** That is a third state, distinct from both pass and fail, and this project needed it.

---

## How the evaluation apparatus caught itself lying

The largest and least expected body of work.

### The incident

`compare_impls.py` compared **36 of the corpus's 41 cases** and printed:

```
VERDICT: A and B agree on every case where the spec is decisive.
```

The five omitted cases were **Family H** — the adversarial family added in v0.3 *specifically to test the newest specification text*. Not a random sample: the cases most likely to disagree were the ones being dropped.

The harness reproduced, while testing for it, the exact failure the whole experiment exists to detect. A harness that drops cases cannot find disagreement in them.

### The fix

```python
expected_ids == A_ids == B_ids == compared_ids      # fatal on any difference
```

The subtlety that makes it real: expected ids come from **`corpus_export.json`** — a neutral file no implementation writes — and **never** from implementation A's case list.

Had the population been derived from A, any case A failed to register would be invisible to the check, and the instrument would have inherited precisely the blind spot it exists to detect. That is the project's second invariant:

> **Neither implementation may define the population against which its own correctness is measured.**

### And it is tested — with a test that can fail

`adversarial_measure.py` seeds seven defects and asserts the apparatus **refuses** to report success:

| # | Failure mode | What it proves |
|---|---|---|
| 1 | specification drift | an unrecorded spec edit is fatal |
| 2 | detector can fail | *negative control* — remove the invariant, the detector stops firing |
| 3 | omitted case | A omitting Family H is fatal and named |
| 4 | uncollected test | a planted module-level test is provably never collected |
| 5 | unreachable branch | the reserved `DEFEATED` status is never emitted |
| 6 | vacuous satisfaction | starved budget → operational error; real cycle → `SEMANTIC` |
| 7 | silent disagreement | an injected adversarial disagreement is detected *and localised* |

The negative control (row 2) is load-bearing. A detector that has only ever passed cannot be distinguished from one that cannot fail. Removing the coverage invariant reproduces the historical 36/41 silent success exactly — so the detector is known to do the work, not merely coincide with it.

### It immediately caught a stale artifact in this repository

`impl_b.json` is the frozen v0.1 result — 36 cases. After v0.3 extended the corpus to 41, the file was out of date, and the invariant refused to score it:

```
FATAL -- MEASUREMENT FAILURE. Refusing to report agreement.
  B        is MISSING 5 case(s): H1, H2, H3, H4, H5
```

A stale result file looks exactly like a correct one to any reader skimming a table of numbers. **If you see that error, it usually means the comparison input predates the corpus — not that the harness is broken.** The fix is to regenerate the output from an implementation built against the current specification, and to version the result file (`impl_c-v0.2.json`, `impl_d.json`); do not overwrite frozen evidence.

Writing the detectors also caught a mistake worth keeping: the first version dropped a case from implementation **B**, which the old `missing` check would have caught anyway. The real bug was that **A** never registered Family H, so those ids existed in neither comparison set. An adversarial test aimed at the wrong failure model is a passing test that proves nothing.

---

## The failure taxonomy

Six categories, each with observed instances — none hypothetical. They are *layered*: a defect in layer N is invisible to layer N−1 unless layer N−1 was built to look for it.

```
CORPUS FAILURE          the intended case is malformed
      ↓
SPECIFICATION FAILURE   a rule exists in code, not in the specification
      ↓
IMPLEMENTATION FAILURE  code violates the specification
      ↓
TEST FAILURE            a test exists but does not execute
      ↓
MEASUREMENT FAILURE     the instrument silently excludes observations
```

`VACUOUS` cuts across the layers rather than sitting in the stack: it describes a relationship between an implementation and a condition it never entered.

**`MEASUREMENT FAILURE` is qualitatively different from the rest.** Every other category produces visible red. This one produces green while the system is wrong — making an instrument an *amplifier* of false confidence rather than merely a weak check. Full detail, including modes never caught: [`FAILURE-TAXONOMY.md`](FAILURE-TAXONOMY.md).

---

## The red line

> **Do not let the system manufacture the corpus against which it will later claim to have succeeded.**

Not designed in — found, repeatedly, after each layer proved capable of quietly widening what counts as evidence:

- the implementation enforced five invariants the specification never mentioned;
- the harness compared 36 of 41 cases and reported success;
- the specification was available for edit to accommodate either one.

Three separate places now stop the system grading its own homework: an **independent implementation**, a **neutral corpus**, and a **digest-pinned specification**.

### The specification cannot be edited to make tests pass

`SPEC-FREEZE.json` pins a SHA-256 digest of every normative file. `spec_freeze.py` fails on any unrecorded change:

```
FATAL -- SPECIFICATION DRIFT. A pinned normative file changed
without a recorded semantic decision.
  SEMANTICS.md   expected 91e25e7fe40a7f95, found 343bfa9c8f5f7a06
```

Legitimate revisions remain entirely available — v0.2 and v0.3 were both warranted. What is prohibited is a *semantic change masquerading as an implementation fix*. Every recorded decision names the evidence that surfaced it, so an edit can never be mistaken for ordinary bug-fixing. That is the first invariant:

> **A change in what the system means must be observable as a change in the specification, not merely as a change in the program that implements it.**

---

## Running it

```bash
# Python 3.11+, no dependencies. Rust and Node only needed for B/C/D.
python3 -m unittest test_proto test_families test_family_g   # 78 tests
python3 mutate_g.py                                          # 19/19 killed
python3 run_graded.py                                        # regime comparison
python3 spec_freeze.py                                       # digest pin
python3 adversarial_measure.py                               # 7/7 detectors

# Compare an implementation's JSON output against A.
# Refuses to report agreement if the case sets differ.
python3 compare_impls.py impl_d.json

# impl_c takes a FILE PATH in and a FILE PATH out
cd impl_c && node engine.js ../corpus_export.json ../impl_c.json
# impl_b also takes FILE PATHS (corpus in, results out) -- NOT a base directory
cd impl_b && cargo build --release --offline && ./target/release/impl_b ../corpus_export.json ../impl_b-v0.3.json
# impl_d alone takes a BASE DIRECTORY (it derives both corpus and output paths from it)
cd impl_d && cargo build --release --offline && ./target/release/impl_d ..
```

### Writing a new independent implementation

The experiment is only meaningful if the implementation is genuinely independent. To take part:

1. Read **only** `SEMANTICS.md`, `CORPUS_FORMAT.md`, `corpus_export.json`.
2. Read **nothing** else — not the other implementations, not `expected.py`, not the tests, not the milestones.
3. Do not hardcode case ids. `corpus_export.json` carries no labels, no expected statuses, no hint of which cases are traps.
4. Emit JSON with `id`, `status`, `conclusion`, `uncertainty`, `accepted`, `defeated`, `represented_reason`, `trace`.
5. Work in a fresh directory.

Then run `compare_impls.py` against your output. **Disagreement is a better result than agreement** — it is evidence about where the specification is underspecified, which is the thing the project is actually trying to find.

---

## The boundary: what this repository is and is not *claiming*

Stated plainly, because the temptation to overclaim is the exact failure mode this project exists to detect.

**Established**

- An independently enumerated observation boundary, verified against a neutral corpus no implementation controls.
- Mechanical detection of specification drift.
- Three independent implementations agreeing on 41/41 cases, with 16 of 18 tracked fields **derived** from quoted specification sections. The fourth (`B`) agrees on 35/41 and is frozen at spec v0.1; its six disagreements all trace to §5 clauses added in v0.2.
- Adversarial detection of seven classes of measurement failure, including a negative control proving the detectors can fail.

**Not established**

- That those seven classes are **exhaustive**. They are a sample of modes found, not an enumeration. An eighth may exist.
- That the specification is **semantically correct**. It is pinned and determinate, not validated.
- That the engine reaches **any legal conclusion**. It reasons over synthetic clauses and has no authority about real law.
- That agreement is **capability**. The corpus was authored around the ratified semantics, and one author wrote both corpus and manifest. **No external human-domain-author validation has occurred.**
- That the **governance model works.** It does not exist.

The honest summary of v0.4:

> Ganymede5 can now detect several ways in which Ganymede5 could falsely conclude that Ganymede5 worked.

Narrower than what the project set out to do. Arguably the most useful thing it has produced.

---

## The open research question

Preserved as a question. **Not implemented. Not in the backlog.**

> Given an independently specified governance corpus, can Ganymede decompose institutional tasks while preserving the distinction between authorization, delegation, execution, evaluation, and normative judgment, without allowing the evaluator to rewrite the criteria by which its own decomposition is judged?

This is where the political-science portion begins. It is blocked for a structural reason, not a scheduling one: authoring that corpus here and evaluating it here would make the author the evaluator — the exact arrangement this repository exists to separate out. It requires an **independently specified** corpus, the same requirement already applied to `SEMANTICS.md`, and the reason four implementations were written instead of one.

The self-reference is deliberate. It is the same question as the rest of the project, one level up.

---

## Repository map

| Path | Role |
|---|---|
| `SEMANTICS.md` | **normative source of truth.** v0.3, digest-pinned |
| `CORPUS_FORMAT.md` | language-neutral input contract for independent implementations |
| `SPEC-FREEZE.json` | pinned digests + every recorded semantic decision |
| `ARCHITECTURE.md` | layer separation, the two invariants, the red line |
| `FAILURE-TAXONOMY.md` | six categories of epistemic failure, with observed instances |
| `DERIVATION-SCORECARD.md` | agreement vs derivation, per field, per implementation |
| `MILESTONE-SIT-V0.*.md` | frozen results in order, including the failures |
| `corpus.py`, `semantics.py` | implementation A |
| `families.py`, `family_g.py`, `family_h.py` | the 41 synthetic cases |
| `export_corpus.py` | writes the neutral, label-free corpus |
| `compare_impls.py` | A/B comparison with the fatal coverage invariant |
| `spec_freeze.py` | specification drift detector |
| `adversarial_measure.py` | seven detectors, incl. the negative control |
| `mutate_g.py` | 19 mutants |
| `expected.py` | manifest — **same author, not externally validated** |
| `impl_b/`, `impl_c/`, `impl_d/` | independent implementations |
| `README-v0.0-experiment0.md` | the original Experiment 0 README, preserved |

Milestone documents are frozen records of what happened, **including what failed**. Do not edit them to reflect later work.

---

## Attribution

Research and specification by the Ganymede5 author. Implementations B, C, and D were written by isolated agent contexts given only the three public normative files; their independence was verified by inspection (`impl_c/engine.js` contains zero case-id literals; `impl_d/src/engine.rs` contains no reference to A). Their creator is the same author, which bounds what the experiment proves.

The corpus is synthetic. No real legal instrument, political actor, or identifiable person is represented.

MIT licensed. See [`LICENSE`](LICENSE).