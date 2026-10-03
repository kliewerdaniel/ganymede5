#!/usr/bin/env python3
"""
Family G — the structural tests.

Family G asks one question: does the defeat STRUCTURE survive, or does the
engine collapse it to "the highest rank wins"?

Every case is built so those two answers differ. Numeric ranks are set to
favour the WRONG answer, so a rank collapse is visible rather than lucky.
"""
import unittest

from corpus import run_defeasible, run_refusal, DECIDED, CONTESTED, INVALID
from family_g import G
from expected import MANIFEST

BY = {c.cid: c for c in G}


class CommitmentObservability(unittest.TestCase):
    """Cases that make ratified commitments actually OBSERVABLE.

    Each of these was added after a mutant survived: the commitment was stated
    in SEMANTICS.md and simply not tested, which is the same failure as never
    having written it down.
    """

    def test_g7_representative_is_not_chosen_by_authority(self):
        """M4/M11 guard. Two survivors assert the SAME atom, so a preference
        for the higher-authority rule is invisible in the conclusion and can
        only be caught in the trace: a correct engine names the first
        declared survivor, not the agency rule over the memo."""
        r = run_defeasible(BY["G7"])
        self.assertEqual(r["status"], DECIDED)
        self.assertEqual(r["conclusion"], "Y")
        named = [t for t in r["trace"] if t[0] == "result"]
        self.assertTrue(named)
        self.assertEqual(named[0][1], "M",
                         "the memo is named first in declaration order; an "
                         "authority-preferring engine would name N")

    def test_g8_self_defeat_is_invalid_not_contested(self):
        """M7 guard. SEMANTICS.md 4.4: a self-defeating rule is a corpus
        defect. It must be INVALID, and it must never be reported as the
        open contest of 4.2 -- those are different claims about the world."""
        r = run_defeasible(BY["G8"])
        self.assertEqual(r["status"], INVALID)
        self.assertNotEqual(r["status"], CONTESTED,
                            "a malformed norm is not an unresolved norm")
        self.assertTrue([t for t in r["trace"] if t[0] == "self_defeat"],
                        "the self-defeat must be named in the trace")

    def test_reversal_is_recorded_in_the_trace(self):
        """M9 guard. The witness property: which validated defeats the
        fixpoint did NOT apply is the record that shows a reversal happened.
        Silently dropping it is the defect that let a wrong answer look
        clean."""
        r = run_defeasible(BY["G1"])
        eff = {t[1]: t[2] for t in r["trace"] if t[0] == "defeat_effective"}
        self.assertEqual(eff.get("A"), "B", "A falls to B")
        self.assertEqual(eff.get("C"), "D", "C falls to D")
        self.assertNotIn("B", eff,
                         "B's defeat of A is the reversal: C is out, so C's "
                         "defeat of B does not stand. It must be absent from "
                         "the effective relation, and its absence is the record")


class RatifiedProhibitions(unittest.TestCase):
    """SEMANTICS.md section 4.6, enforced mechanically.

    The spec removes tiebreaks rather than trusting the code to decline them.
    That claim is only credible if it is tested, so these are AST/source
    guards, not behavioural ones.
    """

    def test_defeat_path_never_reads_an_inert_signal(self):
        import inspect
        import semantics as sem
        src = inspect.getsource(sem.accepted)
        for field in ("rank", "specificity", "recency", "confidence",
                      "order_index", "text_similarity", "length"):
            self.assertNotIn(field, src,
                             "the SEMANTIC layer must not read %s" % field)

    def test_no_preference_or_stable_semantics_is_available(self):
        """SEMANTICS.md 4.3: no preference relation may be consulted.

        Ganymede5 has no priority ordering, so the ACCEPTANCE function may not
        order arguments by authority, rank, or anything else.

        The guard is deliberately scoped to `accepted` and not to the module.
        `cycle_members` uses `sorted` so that the cycle NAMES are reported in
        a deterministic order -- that is stable reporting of an unresolved
        structure, not a preference over it. A module-wide ban would have
        flagged that, which would be a wrong test rather than a strict one.
        """
        import inspect
        import semantics as sem
        src = inspect.getsource(sem.accepted)
        for banned in ("AUTH_RANK", "preference", "sorted", "sort(", "max("):
            self.assertNotIn(banned, src,
                             "the acceptance fixpoint must not offer %s" % banned)

    def test_engine_cannot_report_implementation_uncertainty(self):
        """The engine has no vocabulary for its own defects."""
        import inspect
        import semantics as sem
        self.assertFalse(hasattr(sem, "IMPLEMENTATION"),
                         "IMPLEMENTATION uncertainty is a grader-only finding")


class ManifestAgreement(unittest.TestCase):
    def test_every_family_g_case_matches_the_independent_manifest(self):
        bad = ["%s: expected %s got %s"
               % (c.cid, MANIFEST[c.cid]["status"], run_defeasible(c)["status"])
               for c in G if run_defeasible(c)["status"] != MANIFEST[c.cid]["status"]]
        self.assertEqual([b for b in bad if not b.startswith("G2:")], [],
                         "\n".join(bad))

    def test_g2_disagreement_is_now_resolved_and_recorded(self):
        """G2 used to be the corpus's one permanent disagreement.

        Its manifest label was CONTESTED on the grounds that no contest was
        actually posed. Once the grounded fixpoint made the surviving set
        visible, the engine reached the same answer for a different reason:
        the survivors DO contradict. The label and the engine now agree, so
        the disagreement is closed rather than tolerated.
        """
        self.assertEqual(run_defeasible(BY["G2"])["status"],
                         MANIFEST["G2"]["status"])
        self.assertEqual(run_defeasible(BY["G2"])["status"], CONTESTED)

    def test_no_family_g_case_disagrees_with_the_manifest(self):
        bad = ["%s: manifest %s, engine %s"
               % (c.cid, MANIFEST[c.cid]["status"], run_defeasible(c)["status"])
               for c in G if run_defeasible(c)["status"] != MANIFEST[c.cid]["status"]]
        self.assertEqual(bad, [], "\n".join(bad))

    def test_g1_chain_admits_the_grounded_extension(self):
        """Ganymede5's chain semantics is GROUNDED, not transitive succession.

        A defeated defeater propagates nothing. D defeats C, so C is out, so
        C's defeat of B does not stand, so B survives, so B's defeat of A
        stands. Admitted set is {B, D}.

        The withdrawn claim -- that the chain resolves *transitively* at D --
        is exactly the invention this project exists to detect, and it was in
        my own manifest. See SEMANTICS.md section 3.
        """
        r = run_defeasible(BY["G1"])
        self.assertEqual(set(r["defeated"]), {"A", "C"},
                         "A must fall to B and C must fall to D")
        self.assertNotIn("B", r["defeated"],
                         "B is admitted because its defeater C is itself out")
        self.assertNotIn("D", r["defeated"], "D is unattacked")

    def test_g1_and_g5_have_the_identical_defeat_graph(self):
        """The duplication is asserted, not hidden.

        G1 and G5 are the same structure and their original manifest labels
        contradicted each other. Keeping them as one case would hide the
        error; keeping both makes it permanently checkable.
        """
        g1 = frozenset(frozenset((d.defeater, d.defeated))
                       for d in BY["G1"].defeats if d.enabled)
        g5 = frozenset(frozenset((d.defeater, d.defeated))
                       for d in BY["G5"].defeats if d.enabled)
        self.assertEqual(g1, g5, "G1 and G5 must remain the same graph")
        self.assertEqual(set(run_defeasible(BY["G1"])["defeated"]),
                         set(run_defeasible(BY["G5"])["defeated"]),
                         "identical defeat graphs must yield identical defeats")

    def test_g1_never_resolves_at_the_highest_rank(self):
        r = run_defeasible(BY["G1"])
        self.assertEqual(r["status"], DECIDED)
        self.assertEqual(r["conclusion"], "NOT-Y", "must resolve at D, not at A")

    def test_g1_does_not_resolve_at_the_highest_rank(self):
        """A has rank 9, D has rank 6. A rank collapse would answer Y. This
        is the test that distinguishes a structure from a sort."""
        c = BY["G1"]
        a = [r for r in c.rules if r.id == "A"][0]
        d = [r for r in c.rules if r.id == "D"][0]
        self.assertGreater(a.rank, d.rank, "G1's ranks must favour the wrong answer")
        self.assertEqual(run_defeasible(c)["conclusion"], d.conclusion)

    def test_g3_broken_middle_stops_the_defeater_only(self):
        """B still defeats A even though C's defeat of B is disabled. Breaking
        a chain stops the defeater; it does not resurrect the defeated."""
        r = run_defeasible(BY["G3"])
        self.assertEqual(r["status"], DECIDED)
        self.assertEqual(r["defeated"], ["A"])
        absent = [t for t in r["trace"] if t[0] == "defeat_absent"]
        self.assertEqual(len(absent), 1, "the disabled relation must appear in the trace")

    def test_g4_cycle_is_never_resolved(self):
        """SEMANTICS.md 4.2, ratified: Ganymede5 does not resolve cyclic
        defeat by default. This is a positive commitment, not a known gap.

        The case is load-bearing in a specific way: B(rank 2) and C(rank 7)
        defeat each other, so a rank tiebreak would confidently name C. The
        whole point is that the engine must not.
        """
        r = run_defeasible(BY["G4"])
        self.assertEqual(r["status"], CONTESTED)
        self.assertIsNone(r["conclusion"], "a cycle may not yield a conclusion")
        self.assertEqual(r["uncertainty"], "SEMANTIC")
        self.assertFalse(r["represented_reason"],
                         "an unresolved cycle is not a represented reason")
        cycles = [t for t in r["trace"] if t[0] == "defeat_cycle"]
        self.assertTrue(cycles,
                        "the cycle members must be named, so the contest is "
                        "contestable rather than merely withheld")

    def test_g4_cycle_survives_basis_validation(self):
        """Regression guard for a real defect found this round.

        `explicit_chain_succession` fell through to the rank branch, where C
        (rank 7) beat B (rank 2). That DESTROYED the cycle by rank and made
        G4 report DECIDED -- the precise heuristic failure G4 was built to
        detect, hiding inside the formalism. Succession is stated in the
        corpus, so it must be honoured as stated.
        """
        r = run_defeasible(BY["G4"])
        validated = [t for t in r["trace"] if t[0] == "defeat_validated"]
        self.assertEqual(len(validated), 2,
                         "both directions of the cycle must survive validation")

    def test_g5_is_not_a_chain_reversal_and_does_not_claim_to_be(self):
        """G5 was named "the reversal must reach A". That claim is WITHDRAWN.

        The engine must not report that a defeated defeater's defeat reversed
        a chain it never propagated. The admitted set is {B, D} -- identical to
        G1, because the defeat graphs are identical.

        With B (agency) and D (constitution) both admitted and asserting
        opposite atoms, the honest answer is CONTESTED, not DECIDED. A
        constitutional exception that ends a chain does not by itself decide
        the case; whether the exception reaches THIS case is a question of
        applicability, and applicability is not represented in the corpus.
        Preferring D because it is constitutional is precisely the
        authority-preference tiebreak SEMANTICS.md removes.
        """
        r = run_defeasible(BY["G5"])
        self.assertEqual(set(r["defeated"]), {"A", "C"})
        self.assertEqual(r["status"], CONTESTED)
        self.assertEqual(r["uncertainty"], "CORPUS")
        self.assertIsNone(r["conclusion"],
                          "a chain ending in a constitutional exception does "
                          "not decide the case by itself")

    def test_g5_now_does_pose_a_contest_on_the_merged_atoms(self):
        """FOURTH case-design error, found by grading.

        The chain rules assert the derived atoms A1 and B1, so the surviving
        rules B (A1) and D (NOT-Y) do not contradict each other and the case
        never posed a conflict on Y. The engine returns different answers for
        G1 and G5 only because _pick orders equal-authority survivors by
        rank -- i.e. this family was partially measuring the tiebreak it
        claims to forbid.

        This test documents the defect rather than hiding it. The corpus fix
        (terminal rules must assert opposite atoms) is NOT yet applied, so
        this is an xfail-shaped assertion, not a passing guarantee.
        """
        r5 = run_defeasible(BY["G5"])
        concls = {x.conclusion for x in BY["G5"].rules
                  if x.id not in r5["defeated"]}
        self.assertIn("Y", concls,
                      "a survivor must assert Y for the case to discriminate")
        self.assertIn("NOT-Y", concls,
                      "and the survivors must contradict, or G5 cannot test "
                      "whether a constitutional exception decides the case")

    def test_uncertainty_kinds_stay_distinct(self):
        """SEMANTIC and CORPUS must never collapse into one state.

        A cycle is SEMANTIC (the formalism is indeterminate). Two surviving
        arguments that contradict are CORPUS (the corpus lacks a relation).
        Reporting them identically would hide whether the system or the law is
        at fault.
        """
        cyc = run_defeasible(BY["G4"])
        self.assertEqual(cyc["status"], CONTESTED)
        self.assertEqual(cyc["uncertainty"], "SEMANTIC",
                         "a defeat cycle is indeterminate in the FORMALISM")

        cor = run_defeasible(BY["G2c"])
        self.assertEqual(cor["status"], CONTESTED)
        self.assertEqual(cor["uncertainty"], "CORPUS",
                         "a well-founded contest is underdetermined in the CORPUS")

    def test_engine_never_claims_implementation_uncertainty(self):
        """IMPLEMENTATION uncertainty is a grader finding, never an outcome.

        A system that can diagnose its own implementation errors is not being
        audited. This test is the mechanical guard on that boundary.
        """
        for c in G:
            self.assertNotIn(run_defeasible(c)["uncertainty"],
                             ("IMPLEMENTATION", None))

    def test_g2c_unrelated_survivors_stay_contested(self):
        r = run_defeasible(BY["G2c"])
        self.assertEqual(r["status"], CONTESTED)
        self.assertIsNone(r["conclusion"])

    def test_g2c_survivors_are_genuinely_indistinguishable(self):
        c = BY["G2c"]
        d = [r for r in c.rules if r.id == "D"][0]
        e = [r for r in c.rules if r.id == "E"][0]
        self.assertEqual(d.authority, e.authority)
        self.assertEqual(d.rank, e.rank)
        self.assertNotEqual(d.conclusion, e.conclusion, "they must contradict")

    def test_g2b_is_not_the_control_i_intended(self):
        """G2b was meant to be a DECIDED control. It is the same as G2c.

        With C removed from the admitted set, survivors are B (Y) and D
        (NOT-Y) -- a contradiction. The engine is right; my label was wrong.
        Kept as a test so the mistaken "control" cannot be silently revived.
        """
        r = run_defeasible(BY["G2b"])
        self.assertEqual(r["status"], CONTESTED)
        survivors = {x.conclusion for x in BY["G2b"].rules
                     if x.id not in r["defeated"]}
        self.assertIn("Y", survivors)
        self.assertIn("NOT-Y", survivors,
                      "G2b's survivors DO contradict; it is not a control")

    def test_g6_one_contested_pair_does_not_license_the_other(self):
        r = run_defeasible(BY["G6"])
        self.assertEqual(r["status"], CONTESTED)
        self.assertIsNone(r["conclusion"])


class RegimeContrast(unittest.TestCase):
    def test_authoring_time_suppresses_every_contested_case(self):
        """The control's defining behaviour. Recorded so that a future change
        to the control cannot quietly improve its numbers."""
        must_open = [c for c in G if MANIFEST[c.cid]["status"] == CONTESTED]
        closed = [c.cid for c in must_open
                  if run_refusal(c, True)["status"] == DECIDED]
        self.assertEqual(closed, [c.cid for c in must_open])

    def test_defeasible_preserves_g2c(self):
        self.assertEqual(run_defeasible(BY["G2c"])["status"], CONTESTED)
        self.assertEqual(run_refusal(BY["G2c"], True)["status"], DECIDED,
                         "the control should confidently close G2c")

    def test_only_the_malformed_case_is_invalid(self):
        """G8 is deliberately INVALID, so the old blanket claim that no
        Family G case is INVALID no longer holds. The meaningful invariant is
        that INVALID appears ONLY for a corpus defect (G8), never for a case
        whose defeat structure is merely unresolved."""
        invalid = [c.cid for c in G
                   if run_defeasible(c)["status"] == INVALID]
        self.assertEqual(invalid, ["G8"],
                         "only the self-defeating corpus may be INVALID")
        for cid in ("G1", "G2", "G2b", "G2c", "G3", "G4", "G5", "G6", "G7"):
            self.assertNotEqual(run_defeasible(BY[cid])["status"], INVALID, cid)


    """Rules the SIT v0.1 disagreements forced into writing (SEMANTICS.md v0.2).

    Each test corresponds to a clause that did not exist when the two
    independent implementations disagreed. Collected as methods because a
    module-level function is invisible to unittest.
    """

    def run_g(self, cid):
        return run_defeasible(BY[cid])

    def test_invalid_is_corpus_never_none(self):
        """SEMANTICS.md 2.1. A defective corpus is INVALID/CORPUS.

        NONE would assert both that the semantics decided and that the corpus
        is sound, which would let a malformed corpus read as a clean query
        that simply found nothing.
        """
        r = self.run_g("G8")
        self.assertEqual(r["status"], "INVALID")
        self.assertEqual(
            r["uncertainty"], "CORPUS",
            "2.1: a malformed corpus is not a clean NONFINDING")

    def test_multi_atom_grounded_set_has_no_unique_conclusion(self):
        """SEMANTICS.md 5a.2 / 5a.4.

        G3 grounds to {B,C}, asserting A1 and NOT-Y. Reporting A1 required
        indexing declaration order -- a substantive preference in disguise.
        Status stays DECIDED because nothing is contested.
        """
        r = self.run_g("G3")
        self.assertEqual(r["status"], "DECIDED")
        self.assertIsNone(r["conclusion"], "5a.4: order is not a selection rule")
        self.assertEqual(sorted(r["accepted"]), ["B", "C"])
        shown = {t[2] for t in r["trace"] if t[0] == "surviving_conclusion"}
        self.assertEqual(shown, {"A1", "NOT-Y"},
                         "every surviving atom stays visible to the reader")

    def test_single_atom_grounded_set_still_reports_it(self):
        """5a.1 must survive 5a.2 -- a null conclusion is not the default."""
        self.assertEqual(self.run_g("G1")["conclusion"], "NOT-Y")

    def test_absent_date_does_not_satisfy_a_temporal_basis(self):
        """SEMANTICS.md 4.6. An absent effective_from is NOT -inf.

        Built here rather than added to the corpus, because the SIT v0.2
        instruction was to leave the corpus untouched. Before this test the
        rule was written in the spec and implemented in code but enforced by
        nothing -- mutant M14 survived.
        """
        from corpus import Case, Rule, Defeat
        r = Rule("L", "ch_01", "LEGISLATURE", "ch_01 SS2", "on_state",
                 "Y", effective_from=1900)          # dated
        d = Rule("D", "decree_01", "EXECUTIVE", "dec_01 SS1", "on_state",
                 "NOT-Y")                        # NO date at all
        c = Case(cid="TMP-DATE", family="tmp", note="4.6 probe",
                 state={"on_state"},
                 rules=[r, d],
                 defeats=[Defeat("L", "D", "explicit_lex_posterior",
                                 "dec_01 SS1")])
        out = run_defeasible(c)
        # D cannot defeat L on a temporal basis it cannot state, so L survives
        # and D's claim does not become the outcome.
        self.assertNotEqual(
            out["conclusion"], "NOT-Y",
            "4.6: an absent operand is unsatisfied, not -inf")
        rejected = [t for t in out["trace"]
                    if t[0] == "defeat_rejected" and "4.6" in str(t)]
        self.assertTrue(
            rejected,
            "the rejection must be recorded with its reason (4.6 fail-closed)")

    def test_manifest_agrees_with_revised_g3(self):
        """The independent manifest must encode the v0.2 rule, not the old
        declaration-order answer."""
        self.assertIsNone(MANIFEST["G3"].get("conclusion"))
