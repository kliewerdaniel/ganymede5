# Family G — nested defeat chains. WORK IN PROGRESS, SHIPPED FAILING.

**Status: the baseline corpus (A–F) passes 40/40. Family G does not, and
this file records why. The G engine is not enabled in `corpus.py`.**

Run `python3 -m unittest test_family_g` to see the failures. They are real and
they are the most interesting result so far.

## What Family G asks

Can the defeasible representation preserve a defeat **structure**, or does it
collapse to "the highest numeric rank wins"?

Every case is built so the two answers differ. Ranks are deliberately set to
favour the wrong answer, so a rank collapse is visible rather than lucky.

## What the independent manifest found immediately

`expected.py` — a manifest importing no engine code, authored from ASPIC+-lite
semantics — was the single most valuable artifact of this round. It found
**three engine failures and two errors in my own case design** on first contact.

| id | expected | what happened |
|---|---|---|
| G1 | DECIDED at D | `CONTESTED` — engine could not follow a chain |
| G2 | CONTESTED | my *case* was malformed, not the engine |
| G3 | CONTESTED | my *manifest* was wrong; engine right |
| G4 | CONTESTED | `DECIDED` — a defeat **cycle** produced a confident winner |

G4 is the alarming one. C defeats B and B defeats C. The engine resolved it by
rank. That is precisely the invented interpretation this project exists to
detect, appearing in my own code.

## The underlying problem: defeat is not a one-pass computation

Defeat must be a fixpoint, because a defeat can itself be defeated.

Four implementations, three wrong:

1. **Single pass.** Applied defeats independently. Ignores defeats of
   defeats. Wrong on every chain.
2. **Monotone growth from the unattacked set.** Order-dependent: in
   A←B←C←D, A was admitted before B was, so a rule about to be defeated
   survived. No such order should exist.
3. **Antitone removal with an `r ∈ S` guard.** Collapses the whole chain —
   B is removed using C, while C is being removed using D.
4. **Grounded operator `S(n+1) = {r : no s ∈ S(n) attacks r}`.**
   Converges on acyclic chains, **oscillates forever on a cycle**:
   `{B,C} → {} → {B,C} → …`. It has no stable fixpoint there.

Attempt 4 hung the process before I bounded it. Bounded, it now fails closed
and returns `CONTESTED` on oscillation — the safe direction — but it still
gives the wrong answer on the linear chain G1 (answers at A rather than D).

**The correct fix is well-founded semantics** (van Gelder's *well-founded*
operator, or the Gnu/alternating fixpoint for a fair, finitely-grounded
argmentation framework). Neither is implemented. Naive iteration is provably
insufficient here, and the oscillation in attempt 4 is the textbook symptom.

This is a real result, not a nuisance: it shows that "add defeasible
reasoning" is not a matter of applying defeats in sequence, and that the
guarantee G1–G5 are meant to demonstrate depends on getting the fixpoint
theory right.

## Case-design errors found (kept, not deleted)

- **G2**: I described "two chains without a dominant argument" but the two
  surviving branches did not assert contradictory conclusions, so no contest
  was posed. Rebuilt as **G2b** (survivors agree → DECIDED) and **G2c**
  (survivors contradict, identical authority and rank → CONTESTED).
- **G2c**, first version: I gave both branches the *same* conclusion while
  intending opposite ones. The engine was right to decide it.
- **G3**: I expected CONTESTED on the reasoning that a broken chain leaves a
  contest. Wrong: breaking a chain stops the defeater, it does not resurrect
  the defeated. B still defeats A, so exactly one argument survives.

Each correction is annotated in `expected.py` with what I originally claimed
and why it was wrong.

## A methodological note worth more than the results

Three of the five findings were bugs in **my own** corpus, not in the engine:
the inverted authority direction in C1 (Experiment 0), G2, and G2c. The engine
rejected each one correctly and said why.

That is the first empirical evidence for a claim the proposal has been
asserting on theoretical grounds: a semantics with genuine procedural
validity *does* catch errors in the specification rather than the other way
round — provided the semantics refuses to guess when the specification is
silent.

## What is needed to finish

1. Implement the well-founded operator for the acyclic case.
2. Decide and document the semantics for **cycles** — `CONTESTED` is safe and
   current, but it is a choice, not a derivation, and it should be defended.
3. Re-run G1–G6. G1 and G4 are the acceptance tests.
4. Only then re-grade the two axes.

Until 1 and 2 are done, the two-axis result quoted from Experiment 0b rests on
a **single-pass** defeat application. It was accurate for A–F, all of which are
depth-1, but it should not be quoted for chain reasoning.
