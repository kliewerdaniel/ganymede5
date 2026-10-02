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


class ManifestAgreement(unittest.TestCase):
    def test_every_family_g_case_matches_the_independent_manifest(self):
        bad = ["%s: expected %s got %s"
               % (c.cid, MANIFEST[c.cid]["status"], run_defeasible(c)["status"])
               for c in G if run_defeasible(c)["status"] != MANIFEST[c.cid]["status"]]
        self.assertEqual([b for b in bad if not b.startswith("G2:")], [],
                         "\n".join(bad))

    def test_g2_is_a_known_broken_case_kept_as_a_record(self):
        """G2 is retained in the corpus precisely because it is malformed: its
        two survivors do not contradict. It must be the ONLY disagreement, so
        that any new one is immediately visible."""
        bad = [c.cid for c in G if run_defeasible(c)["status"] != MANIFEST[c.cid]["status"]]
        self.assertEqual(bad, ["G2"])


class ChainStructure(unittest.TestCase):
    def test_g1_transitive_chain_resolves_at_the_top(self):
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

    def test_g4_cycle_is_refused_not_resolved(self):
        r = run_defeasible(BY["G4"])
        self.assertEqual(r["status"], CONTESTED)
        self.assertIsNone(r["conclusion"])
        self.assertIn("cycle", r["reason"])

    def test_g5_exception_to_an_exception_reverses_the_chain(self):
        """D defeats C, so C's defeat of B fails, so B's defeat of A stands."""
        r = run_defeasible(BY["G5"])
        self.assertEqual(r["status"], DECIDED)
        self.assertEqual(r["conclusion"], "Y", "the reversal must reach A")
        self.assertIn("C", r["defeated"])

    def test_g5_reversal_is_visible_in_the_trace(self):
        """The point of a fixpoint is that the reversal is inspectable."""
        trace = run_defeasible(BY["G5"])["trace"]
        applied = [(t[1], t[2]) for t in trace if t[0] == "defeat"]
        self.assertIn(("A", "B"), applied)
        self.assertIn(("C", "D"), applied)
        self.assertNotIn(("B", "C"), applied,
                         "a defeated rule cannot itself defeat")


class UnrelatedBranches(unittest.TestCase):
    """The sharpest cases. Nothing relates the survivors, so nothing may
    choose between them."""

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

    def test_g2b_control_agrees_with_g2c_structure(self):
        """G2b differs from G2c only in that the survivors do not contradict.
        One decides, the other must not. If both behave the same, the engine
        is not reading the contradiction at all."""
        self.assertEqual(run_defeasible(BY["G2b"])["status"], DECIDED)
        self.assertEqual(run_defeasible(BY["G2c"])["status"], CONTESTED)

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

    def test_no_family_g_case_is_ever_invalid(self):
        for c in G:
            self.assertNotEqual(run_defeasible(c)["status"], INVALID, c.cid)


if __name__ == "__main__":
    unittest.main(verbosity=2)
