#!/usr/bin/env python3
"""
INDEPENDENT EXPECTED-SEMANTICS MANIFEST.

This file is the evaluator boundary for Experiment 0c. It is deliberately
separated from the engine:

  * It imports NOTHING from corpus.py, families.py, or any regime.
  * It is authored from ASPIC+-lite semantics, by reasoning about what each
    case MEANS, not by observing what the engines DO.
  * Each label carries a stated justification, so a wrong label is
    arguable rather than invisible.

WHY THIS EXISTS

The previous experiment annotated each case with `refusal_is_correct` — a
field on the case itself, written by the same person who wrote the case. That
is circular in the way that matters: "refusal says it should refuse, therefore
refusal was correct." This manifest is the fix. A case's expected status is a
property of the case, and the regimes are graded against it.

THE RESIDUAL LIMITATION, STATED PLAINLY

The manifest is independent of the ENGINE. It is not independent of the
AUTHOR — the same person wrote the cases and the labels, and could label a
case to fit the outcome they want. What this buys is real but partial:

  * a wrong label now has to be argued for in writing, and
  * a regime cannot change its own grade by changing its code.

It does not buy independence of judgment. A genuinely independent author, or a
domain reader, would be required for that. Treat every label below as a
*claim under dispute* rather than a ground truth.

SEMANTIC GROUNDS USED (ASPIC+-lite)

  DECIDED    the rules entail an outcome; any defeat applied rests on a
             represented, basis-satisfying relation
  CONTESTED  arguments for contradictory conclusions all survive defeat
  REFUSED    the case needs a construct the representation cannot express
  NONFINDING  no rule is triggered by the state at the relevant time
  INVALID    the corpus violates a procedural invariant, so no amount of
             argumentation can license an outcome
"""

MANIFEST = {
    # ------------------------------------------------------------- family A
    # Explicit, basis-satisfying precedence. Nothing is in dispute, so
    # DECIDED is right and both arms should agree.
    "A1": dict(status="DECIDED", conflict=True, valid_defeat=True,
               representable=True, defeat=("B", "A"),
               why="statute expressly displaces the conflicting regulation; "
                   "precedence is represented and satisfied"),
    "A2": dict(status="DECIDED", conflict=False, valid_defeat=False,
               representable=True, defeat=None,
               why="only one rule applies; there is nothing to contest"),

    "A3": dict(status="DECIDED", conflict=True, valid_defeat=True,
               representable=True, defeat=("B", "A"),
               why="same authority tier, so precedence rests on the encoded "
                   "rank, which is stated explicitly and holds"),

    # ------------------------------------------------------------- family B
    "B1": dict(status="DECIDED", conflict=True, valid_defeat=True,
               representable=True, defeat=("B", "A"),
               why="authority precedence: legislature over agency"),
    "B2": dict(status="DECIDED", conflict=True, valid_defeat=True,
               representable=True, defeat=("A", "B"),
               why="at t=20 A has expired; B is the later instrument and "
                   "expressly supersedes"),
    "B3": dict(status="DECIDED", conflict=True, valid_defeat=True,
               representable=True, defeat=("A", "B"),
               why="constitutional supremacy is represented and satisfied"),
    "B4": dict(status="DECIDED", conflict=True, valid_defeat=False,
               representable=True, defeat=None,
               why="B is not in force until t=50, so at t=10 it is not an "
                   "argument at all; only A applies. No conflict exists. A "
                   "defeat that names a non-triggered rule is INAPPLICABLE, "
                   "not satisfied"),
    "B5": dict(status="DECIDED", conflict=True, valid_defeat=True,
               representable=True, defeat=("A", "B"),
               why="both instruments are live at t=25; B is later and "
                   "expressly supersedes A"),

    # ------------------------------------------------------------- family C
    # The heart of the matter. A plausible reason exists in the world but the
    # corpus does not represent it, so the case must remain contested.
    "C1": dict(status="CONTESTED", conflict=True, valid_defeat=False,
               representable=True, defeat=None,
               why="a reader may believe the statute prevails, but no defeat "
                   "relation says so. Under a formalism that admits only "
                   "represented relations, the arguments stand together"),
    "C2": dict(status="CONTESTED", conflict=True, valid_defeat=False,
               representable=True, defeat=None,
               why="the relation is present in the corpus but disabled; a "
                   "disabled relation is not a warrant"),
    "C3": dict(status="CONTESTED", conflict=True, valid_defeat=False,
               representable=True, defeat=None,
               why="the memo claims authority precedence over a statute. The "
                   "claim exceeds its basis: a memo sits below the "
                   "legislature whatever numeric rank it carries. The defeat "
                   "is REJECTED and both arguments survive"),
    "C4": dict(status="DECIDED", conflict=True, valid_defeat=True,
               representable=True, defeat=("A", "B"),
               why="control for C3: the corpus states RANK precedence, where "
                   "rank is the basis rather than a substitute for one. The "
                   "defeat holds. The inert signals remain inert"),

    # ------------------------------------------------------------- family D
    "D1": dict(status="REFUSED", conflict=True, valid_defeat=True,
               representable=False, defeat=("B", "A"),
               why="B requires ROUND, which the operation set does not "
                   "contain. The defeat would hold, but the case cannot be "
                   "run at all; non-representability precedes the contest"),
    "D2": dict(status="REFUSED", conflict=True, valid_defeat=True,
               representable=False, defeat=("B", "A"),
               why="same defect on the winning side. Refusal must not depend "
                   "on which side is unexpressible"),

    # ------------------------------------------------------------- family E
    # No amount of argumentation licenses an outcome on a defective corpus.
    "E1": dict(status="INVALID", conflict=True, valid_defeat=True,
               representable=True, defeat=("A", "B"),
               why="B is unpromulgated. The defeat it asserts is real and "
                   "satisfied, but an unpublished instrument cannot be the "
                   "ground of a legal conclusion. INVALID, not DECIDED"),
    "E2": dict(status="INVALID", conflict=True, valid_defeat=True,
               representable=True, defeat=("A", "B"),
               why="B operates retroactively against a defined start, which "
                   "is precisely the non-retroactivity defect"),
    "E3": dict(status="INVALID", conflict=True, valid_defeat=False,
               representable=True, defeat=None,
               why="A's validity interval is empty. The corpus asserts a rule "
                   "that was never in force at any time"),
    "E4": dict(status="INVALID", conflict=True, valid_defeat=False,
               representable=True, defeat=None,
               why="the defeat relation references a rule that does not "
                   "exist; the relation is ill-formed, not merely unsatisfied"),
    "E5": dict(status="INVALID", conflict=True, valid_defeat=False,
               representable=True, defeat=None,
               why="duplicate rule id: the corpus asserts the same rule twice, "
                   "so what it asserts is not determinate"),

    # ------------------------------------------------------------- family F
    # Inert signals. Every one of these has a represented reason to be
    # CONTESTED: no defeat relation exists.
    "F1": dict(status="CONTESTED", conflict=True, valid_defeat=False,
               representable=True, defeat=None,
               why="specificity is a salience signal, not a defeater"),
    "F2": dict(status="CONTESTED", conflict=True, valid_defeat=False,
               representable=True, defeat=None,
               why="recency alone is not a defeater; supersession must be "
                   "expressed as a relation"),
    "F3": dict(status="CONTESTED", conflict=True, valid_defeat=False,
               representable=True, defeat=None,
               why="confidence is a property of a speaker, not of a norm"),
    "F4": dict(status="CONTESTED", conflict=True, valid_defeat=False,
               representable=True, defeat=None,
               why="corpus ordering carries no weight"),
    "F5": dict(status="CONTESTED", conflict=True, valid_defeat=False,
               representable=True, defeat=None,
               why="surface overlap between a rule and a condition is not "
                   "authority"),
    "F6": dict(status="CONTESTED", conflict=True, valid_defeat=False,
               representable=True, defeat=None,
               why="six inert signals stacked on one side remain six inert "
                   "signals"),
    "F7": dict(status="DECIDED", conflict=True, valid_defeat=True,
               representable=True, defeat=("B", "A"),
               why="control: the attractive signals sit on the side that is "
                   "genuinely defeated. Inert signals must not overturn a "
                   "represented defeat either"),

    # ------------------------------------------------------------- family G
    # Nested defeat chains. The question is whether the structure survives
    # or collapses to "the highest number wins".
    # G1 and G5 ARE THE SAME DEFEAT GRAPH: D defeats C, C defeats B, B
    # defeats A. Verified mechanically (identical frozenset of active defeat
    # edges). Their labels here ORIGINALLY CONTRADICTED EACH OTHER -- G1 said
    # "resolves at D", G5 said "resolves at A" -- and no deterministic
    # semantics can honour both. That contradiction, not the cycle, is the
    # primary finding of Family G.
    #
    # Grounded semantics admits {B, D}: C is out, so C's defeat of B does not
    # stand, so B survives, so B's defeat of A stands. The chain does NOT
    # resolve transitively to D, because a defeated defeater propagates
    # nothing. My original G1 label encoded the intuition that succession
    # runs end-to-end; that is a different (and unlicensed) semantics.
    "G1": dict(status="DECIDED", conflict=True, valid_defeat=True,
               representable=True, defeat=("B", "A"),
               why="linear chain B defeats A, C defeats B, D defeats C. "
                   "Grounded: D is unattacked; C is therefore out; C's defeat "
                   "of B does not stand, so B survives; B's defeat of A does "
                   "stand. Admitted set is {B, D}. CORRECTED -- I originally "
                   "claimed the structure resolves transitively to D, which "
                   "assumes succession propagates through a defeated "
                   "defeater. It does not. See SEMANTICS.md section 3"),
    "G2": dict(status="CONTESTED", conflict=True, valid_defeat=False,
               representable=True, defeat=None,
               why="D defeats C and C defeats B; F defeats E. B is eliminated "
                   "by the first chain and E by the second, leaving D and F "
                   "as unrelated survivors. D asserts NOT-Y. F's conclusion "
                   "is E1, which is not in the corpus, so the two survivors do "
                   "not contradict each other directly and the case does not "
                   "actually pose a contest. RELABELLED: the corpus was built "
                   "wrong. See G2b for the corrected version, in which the "
                   "two surviving branches assert contradictory conclusions "
                   "with nothing to choose between them. This entry is left "
                   "as a record of the error rather than deleted"),
    # REVISED v0.2. The grounded set is {B,C} and it is unique and
    # determinate, but B asserts A1 and C asserts NOT-Y: two distinct atoms.
    # SEMANTICS.md 5a.2 makes that DECIDED with conclusion=null. I originally
    # expected DECIDED with conclusion "A1", which required picking one atom
    # by declaration order -- 5a.4 forbids exactly that. Implementation B
    # refused to guess and was more spec-faithful than this manifest.
    "G3": dict(status="DECIDED", conclusion=None, conflict=True,
               valid_defeat=True,
               representable=True, defeat=("A", "B"),
               why="the middle of a chain is disabled: C's defeat of B is off. "
                   "B therefore survives and its defeat of A still holds, so "
                   "exactly one argument remains. I originally expected "
                   "CONTESTED here, on the reasoning that a broken chain "
                   "leaves a contest. That was wrong: breaking the chain "
                   "stops the defeater, it does not resurrect the defeated. "
                   "Corrected after the first run."),
    # SEMANTIC uncertainty per SEMANTICS.md 4.2: Ganymede5 does not resolve
    # cyclic defeat by default. This is a ratified position, not a gap.
    "G4": dict(status="CONTESTED", conflict=True, valid_defeat=False,
               representable=True, defeat=None, uncertainty="SEMANTIC",
               why="C defeats B and B defeats C. A cycle has no well-founded "
                   "argument set, so the formalism must not report a winner. "
                   "Reporting the higher-ranked member of the cycle would be "
                   "exactly the invention this project exists to detect"),
    # G5 is a DUPLICATE of G1 in defeat structure. It is retained rather than
    # deleted because its label is where the error was found, and the case
    # still exercises a different BASIS (explicit_exception) and a different
    # authority tier for the terminal rule.
    #
    # A fourth case-design error, found last: the chain rules assert the
    # derived atoms A1/B1, not Y and NOT-Y. So the surviving rules B (A1) and
    # D (NOT-Y) do not contradict one another, and the case never posed a
    # contest on Y at all. The engine returned different answers for G1 and
    # G5 ONLY because _pick sorts equal-authority survivors by rank -- i.e.
    # the family was partially measuring the tiebreak it claims to forbid.
    # The fix is a corpus fix: terminal rules must assert opposite atoms.
    # CORRECTED from DECIDED. The admitted set is {B, D} -- identical to G1,
    # because the defeat graph is identical. With the corpus fixed so the
    # admitted rules assert opposite atoms, B (agency, NOT-Y) and D
    # (constitution, Y) now genuinely contradict, so CONTESTED is correct.
    #
    # This is the substantive outcome of Family G. A chain ending in a
    # constitutional exception does NOT decide the case. Preferring D because
    # it is constitutional is exactly the authority-preference tiebreak that
    # SEMANTICS.md section 4.1 removes. Whether the exception reaches this
    # case is a question of APPLICABILITY, and applicability is not
    # represented in the corpus -- so the honest answer is an open contest.
    #
    # Two withdrawn claims are recorded here rather than deleted: that the
    # chain "resolves at A" (which would require a defeated defeater to
    # restore a rule it cannot legitimately affect), and that this case is
    # distinguishable from G1.
    "G5": dict(status="CONTESTED", conflict=True, valid_defeat=False,
               representable=True, defeat=None,
               why="an exception to an exception, and the admitted set is "
                   "{B, D} exactly as in G1 because the defeat graph is "
                   "identical. The admitted rules contradict: B asserts NOT-Y "
                   "and D, the constitution, asserts Y. No represented relation "
                   "separates them, and preferring the constitution would be "
                   "the authority-preference tiebreak the spec removes. "
                   "CORRECTED from DECIDED and from the withdrawn "
                   "'resolves at A' claim"),
    # FIFTH case-design error. G2b was intended as a "control" in which the
    # survivors agree, so that DECIDED would follow from absence of contest.
    # But B is defeated through C, leaving B and D; B asserts Y and D asserts
    # NOT-Y, which DO contradict. G2b is therefore the same case as G2c and
    # is correctly CONTESTED. Verified: with C removed from the admitted set,
    # survivors are B(Y) and D(NOT-Y).
    #
    # The engine was right and my label was wrong. Corrected after the
    # grounded fixpoint made the surviving set visible.
    "G2b": dict(status="CONTESTED", conflict=True, valid_defeat=False,
                representable=True, defeat=None,
                why="CORRECTED from DECIDED. I intended a control whose "
                    "survivors agree, but the chain removes C and leaves B and "
                    "D, and B asserts Y while D asserts NOT-Y. The survivors "
                    "contradict, so CONTESTED is correct and this is not a "
                    "distinct control from G2c"),
    "G2c": dict(status="CONTESTED", conflict=True, valid_defeat=False,
                representable=True, defeat=None,
                why="the case G2 was meant to be. D and E both survive, both "
                    "are memos of identical rank, and D defeats C while E "
                    "defeats C as well, so neither branch is related to the "
                    "other. They assert contradictory conclusions. No "
                    "represented relation separates them, and the only thing "
                    "that could is a tiebreak, which is not licensed. Naming "
                    "either branch would be an invented interpretation"),

    # G7 exists to make the preference tiebreaks OBSERVABLE. Two admitted
    # rules assert the SAME atom, so conclusion-level tests cannot tell a
    # correct engine from one that prefers authority. The check must be on the
    # trace: which rule is named as the representative.
    "G7": dict(status="DECIDED", conflict=False, valid_defeat=False,
               representable=True, defeat=None,
               why="memo and agency rules both assert Y and neither defeats "
                   "the other, so nothing is contested. Any authority "
                   "preference is only visible in the trace, not the outcome"),

    # G8 is a corpus defect, not an open question. INVALID is deliberately a
    # different state from CONTESTED: a malformed norm is not an open norm.
    "G8": dict(status="INVALID", conflict=False, valid_defeat=True,
               representable=True, defeat=("A", "A"),
               why="a rule that defeats itself asserts something incoherent. "
                   "No amount of argumentation licenses an outcome on it"),

    "G6": dict(status="CONTESTED", conflict=True, valid_defeat=False,
               representable=True, defeat=None,
               why="two independent contests in one case. Resolving the first "
                   "must not license a conclusion about the second"),
}
