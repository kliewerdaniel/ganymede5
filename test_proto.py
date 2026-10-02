#!/usr/bin/env python3
"""
Assertions for the Ganymede5 Experiment-0 prototype.

Printing a status table is not verification. This file states the expected
outcome matrix and fails loudly if the engine deviates from it.

Run: python3 test_proto.py
"""
import sys
import unittest

from proto import (
    corpus_c1, corpus_c2, corpus_c3, corpus_c4, corpus_c5,
    run_refusal, run_defeasible, check_invariants,
    DECIDED, DEFEATED, REFUSED, CONTESTED, NONFINDING, INVALID,
)


class OutcomeMatrix(unittest.TestCase):

    def status(self, corpus, regime):
        if regime == "refusal":
            return run_refusal(corpus, False)
        if regime == "refusal+prec":
            return run_refusal(corpus, True)
        return run_defeasible(corpus)

    # ---------------------------------------------------------------- C1
    def test_c1_refusal_cannot_represent_the_conflict(self):
        """The control must refuse. This is the whole experimental premise."""
        r = self.status(corpus_c1(), "refusal")
        self.assertEqual(r["status"], REFUSED)
        self.assertIsNone(r["conclusion"])

    def test_c1_defeasible_resolves_through_a_represented_defeat(self):
        r = self.status(corpus_c1(), "defeasible")
        self.assertEqual(r["status"], DECIDED)
        self.assertEqual(r["conclusion"], "Y")
        self.assertEqual(r["defeated"], ["B"])

    def test_c1_they_diverge(self):
        """THE assertion. Refusal and defeasible must necessarily differ here."""
        a = self.status(corpus_c1(), "refusal")["status"]
        b = self.status(corpus_c1(), "defeasible")["status"]
        self.assertNotEqual(a, b, "the two regimes did not diverge on C1")

    def test_c1_trace_exposes_why(self):
        """The trace must carry the defeat, its basis, and its provenance."""
        r = self.status(corpus_c1(), "defeasible")
        defeats = [t for t in r["trace"] if t and t[0] == "defeat"]
        self.assertEqual(len(defeats), 1)
        self.assertEqual(defeats[0][1], "B")     # defeated
        self.assertEqual(defeats[0][2], "A")     # defeater
        self.assertEqual(defeats[0][3], "explicit_authority_precedence")
        self.assertEqual(defeats[0][4], "statute_01 §1")

    # ---------------------------------------------------------------- C2
    def test_c2_removing_the_defeater_yields_contested(self):
        """Same conflict, no represented reason. Must NOT silently decide."""
        r = self.status(corpus_c2(), "defeasible")
        self.assertEqual(r["status"], CONTESTED)
        self.assertIsNone(r["conclusion"])

    def test_c2_both_arguments_are_preserved(self):
        r = self.status(corpus_c2(), "defeasible")
        args = [t for t in r["trace"] if t and t[0] == "argument"]
        self.assertEqual(len(args), 2)
        self.assertEqual({a[1] for a in args}, {"A", "B"})

    def test_c2_refusal_also_refuses(self):
        self.assertEqual(self.status(corpus_c2(), "refusal")["status"], REFUSED)

    # ---------------------------------------------------------------- C3
    def test_c3_unexpressible_construct_refuses_everywhere(self):
        """No regime may decide a case the operation set cannot express."""
        for regime in ("refusal", "refusal+prec", "defeasible"):
            r = self.status(corpus_c3(), regime)
            self.assertEqual(r["status"], REFUSED, regime)
            self.assertIn("ROUND", r["reason"], regime)

    def test_c3_audit_mode_never_produces_a_case_decision(self):
        for regime in ("refusal", "defeasible"):
            r = self.status(corpus_c3(), regime)
            self.assertIsNotNone(r["audit"], regime)
            self.assertIsNone(r["conclusion"], regime)

    # ---------------------------------------------------------------- C4
    def test_c4_probe_the_engine_does_not_invent_an_interpretation(self):
        """THE PROBE. B is highly specific but has no represented defeat relation.
        A very high specificity score (99 vs 1) is present in the corpus and
        must never be consulted. Returning DECIDED here means the engine
        invented a legal interpretation. Returning CONTESTED means it didn't."""
        c = corpus_c4()
        r = self.status(c, "defeasible")
        self.assertEqual(r["status"], CONTESTED,
                         "engine invented an interpretation on an unrepresented defeater")
        self.assertIsNone(r["conclusion"])

    def test_c4_the_attractive_signal_is_actually_present(self):
        """Guard against a vacuous pass: the trap must be real for the test
        to mean anything."""
        c = corpus_c4()
        scores = {x.id: x.specificity for x in c.rules}
        self.assertGreater(scores["B"], scores["A"] * 10)
        self.assertEqual(len(c.defeats), 0)

    def test_c4_translator_encoded_arm_does_decide(self):
        """This is the hazard in its purest form: the arm that pre-encodes
        precedence produces a confident answer from nothing in the corpus."""
        r = self.status(corpus_c4(), "refusal+prec")
        self.assertEqual(r["status"], DECIDED)
        # The decision is confident, and the trace's only entry is an admission
        # that no reason exists in the corpus. That admission is the finding.
        self.assertIn("no defeat relation exists", r["trace"][0][1])

    # ---------------------------------------------------------------- C5
    def test_c5_procedural_violation_is_invalid_not_contested(self):
        """INVALID and CONTESTED must never be conflated. An unpromulgated,
        retroactive decree is a validity failure, not an open normative dispute."""
        r = self.status(corpus_c5(), "defeasible")
        self.assertEqual(r["status"], INVALID)
        self.assertNotEqual(r["status"], CONTESTED)

    def test_c5_both_invariants_are_reported(self):
        v = check_invariants(corpus_c5())
        self.assertEqual(len(v), 2)
        self.assertTrue(any("PROMULGATION" in x for x in v))
        self.assertTrue(any("NON_RETROACTIVITY" in x for x in v))

    def test_c5_refusal_arm_cannot_detect_it(self):
        """The refusal regime has no invariant layer, so it refuses on other
        grounds and misses the procedural violation entirely. Recorded as a
        known limitation, not a pass."""
        r = self.status(corpus_c5(), "refusal")
        self.assertEqual(r["status"], REFUSED)
        self.assertNotEqual(r["status"], INVALID)

    # ------------------------------------------------------- cross-cutting
    def test_no_regime_ever_returns_a_verdict_outside_the_vocabulary(self):
        allowed = {DECIDED, DEFEATED, REFUSED, CONTESTED, NONFINDING, INVALID}
        for fn in (corpus_c1, corpus_c2, corpus_c3, corpus_c4, corpus_c5):
            c = fn()
            for regime in ("refusal", "refusal+prec", "defeasible"):
                r = self.status(c, regime)
                self.assertIn(r["status"], allowed, "%s/%s" % (c.name, regime))

    def test_no_answered_case_omits_a_trace(self):
        for fn in (corpus_c1, corpus_c2, corpus_c3, corpus_c4, corpus_c5):
            c = fn()
            for regime in ("refusal", "refusal+prec", "defeasible"):
                r = self.status(c, regime)
                self.assertTrue(r["trace"] is not None, "%s/%s" % (c.name, regime))

    def test_every_decision_states_its_conclusion_or_its_reason(self):
        """Silence is not an acceptable output."""
        for fn in (corpus_c1, corpus_c2, corpus_c3, corpus_c4, corpus_c5):
            c = fn()
            for regime in ("refusal", "refusal+prec", "defeasible"):
                r = self.status(c, regime)
                self.assertTrue(r["conclusion"] or r["reason"],
                                "%s/%s produced neither" % (c.name, regime))

    def test_defeasible_regime_never_reads_specificity(self):
        """Structural check, not a behavioural one: the forbidden signal must
        not appear in any comparison the defeasible engine performs."""
        import inspect
        src = inspect.getsource(run_defeasible)
        # The Rule dataclass legitimately declares the field, and the docstring
        # names it while forbidding it. What must not appear is a *read* of it
        # in the body, so only non-comment, non-docstring lines are checked.
        import ast, textwrap
        tree = ast.parse(textwrap.dedent(src))
        for node in ast.walk(tree):
            if isinstance(node, ast.Attribute) and node.attr == "specificity":
                self.fail("the defeasible engine reads the forbidden signal at line %d"
                          % node.lineno)


if __name__ == "__main__":
    unittest.main(verbosity=2)
