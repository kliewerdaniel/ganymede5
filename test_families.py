#!/usr/bin/env python3
"""
Assertions over the six-family corpus.

Three things are checked, in increasing order of importance:

  1. Every case produces its declared outcome.
  2. Family F's adversarial signals have zero effect.
  3. Mutants are killed (run separately, see README).

Printing a status table is not verification.
"""
import sys
import unittest

from corpus import (run_refusal, run_defeasible, check_invariants,
                    DECIDED, REFUSED, CONTESTED, INVALID, NONFINDING, DEFEATED)
from families import CASES
from run_families import measure, REGIMES

BY_ID = {c.cid: c for c in CASES}
FAMILY_F = [c for c in CASES if c.family == "F"]


def d(cid):
    return run_defeasible(BY_ID[cid])


class DeclaredOutcomes(unittest.TestCase):
    """Each case declared what it tests before it ran. Hold it to that."""

    def test_every_case_matches_its_declaration(self):
        bad = []
        for c in CASES:
            got = run_defeasible(c)["status"]
            if got != c.expect_defeasible:
                bad.append("%s expected %s got %s" % (c.cid, c.expect_defeasible, got))
        self.assertEqual(bad, [], "\n".join(bad))

    def test_corpus_is_not_empty_per_family(self):
        fams = {}
        for c in CASES:
            fams[c.family] = fams.get(c.family, 0) + 1
        self.assertEqual(sorted(fams), ["A", "B", "C", "D", "E", "F"])
        for f, n in fams.items():
            self.assertGreaterEqual(n, 2, "family %s is too thin to mean anything" % f)


class FamilyE_ArgumentationCannotRescue(unittest.TestCase):
    """The core of the INVALID state: a procedurally invalid corpus stays
    invalid no matter how attractive the argumentation is."""

    def test_all_family_e_are_invalid(self):
        for c in [x for x in CASES if x.family == "E"]:
            r = run_defeasible(c)
            self.assertEqual(r["status"], INVALID, c.cid)

    def test_no_family_e_case_is_ever_contested(self):
        """INVALID and CONTESTED are different epistemic claims. An unpromulgated
        decree is not an open dispute; it is a corpus defect."""
        for c in [x for x in CASES if x.family == "E"]:
            self.assertNotEqual(run_defeasible(c)["status"], CONTESTED, c.cid)

    def test_argumentation_does_not_rescue_an_unpromulgated_decree(self):
        """E1's decree outranks the statute on every heuristic and still fails."""
        c = BY_ID["E1"]
        b = [r for r in c.rules if r.id == "B"][0]
        self.assertEqual(b.promulgated, False)
        self.assertEqual(b.rank, 9)
        self.assertTrue(c.defeats, "E1 must carry a defeater, or it tests nothing")
        self.assertEqual(d("E1")["status"], INVALID)

    def test_every_arm_validates_the_corpus_before_answering(self):
        """v0.3 6.2, first clause, enforced in EVERY regime.

        This was previously a known limitation of the refusal arms, and the
        limitation was worse than it looked: on E3 the refusal arm returned
        DECIDED. Rule B still applies, so the corpus looked decidable and the
        empty-validity-interval defect was completely invisible -- a silently
        malformed corpus producing a confident answer. Restraint is not a
        substitute for validation; refusing to answer a malformed corpus is
        the one answer the corpus cannot earn.

        The invariant layer now runs first in all three arms. What remains
        regime-specific is only how a VALID corpus with nothing to say is
        handled, which is the genuine subject of the experiment.
        """
        for cid in ("E1", "E2", "E3", "E4", "E5"):
            case = [c for c in CASES if c.cid == cid][0]
            for arm, fn in (("refusal", lambda c: run_refusal(c, False)),
                            ("refusal+prec", lambda c: run_refusal(c, True)),
                            ("defeasible", run_defeasible)):
                self.assertEqual(fn(case)["status"], INVALID,
                                 "%s/%s answered a defective corpus" % (arm, cid))

    def test_defeasible_arm_catches_every_family_e_defect(self):
        for c in [x for x in CASES if x.family == "E"]:
            self.assertEqual(run_defeasible(c)["status"], INVALID, c.cid)


class FamilyF_NoHiddenHeuristicLayer(unittest.TestCase):
    """The most important family. These signals would all 'help' a heuristic
    and are semantically inert unless explicitly represented as a defeat
    relation. If any of them changes an outcome, the engine has crossed the
    boundary from formal reasoning into invented interpretation."""

    def test_all_inert_signal_cases_are_contested(self):
        for c in FAMILY_F:
            if c.cid == "F7":
                continue  # F7 has a real defeater; signals must not change it
            self.assertEqual(run_defeasible(c)["status"], CONTESTED, c.cid)

    def test_a_defeater_may_not_exceed_its_stated_basis(self):
        """C3: a memo claims `explicit_authority_precedence` over a statute and
        carries rank=9. Authority order beats it, the defeat must be REJECTED,
        and the case must remain contested. A numeric rank must never substitute
        for authority precedence — that substitution is the heuristic failure
        wearing a formalism's clothes, and it is the exact bug found here."""
        c = BY_ID["C3"]
        b = [r for r in c.rules if r.id == "B"][0]
        self.assertEqual(b.authority, "memo")
        self.assertEqual(b.rank, 9)
        r = run_defeasible(c)
        self.assertEqual(r["status"], CONTESTED)
        self.assertEqual(r["defeated"], [], "the unsupported defeat must not apply")
        rejected = [t for t in r["trace"] if t[0] == "defeat_rejected"]
        self.assertEqual(len(rejected), 1, "the rejection must appear in the trace")
        self.assertIn("explicit_authority_precedence", rejected[0][3])

    def test_an_explicitly_ranked_basis_still_works(self):
        """C4 is the control for C3: the same memo, but the corpus states
        `explicit_rank_precedence`, where rank IS the basis. The defeat must
        then hold. Without this, C3 could be satisfied by breaking rank entirely."""
        c = BY_ID["C4"]
        r = run_defeasible(c)
        self.assertEqual(r["status"], DECIDED)
        self.assertEqual(r["defeated"], ["A"])

    def test_signals_do_not_override_a_real_defeater(self):
        """F7 carries every attractive signal on the losing side AND a genuine
        defeat relation. The defeat must still hold."""
        r = d("F7")
        self.assertEqual(r["status"], DECIDED)
        self.assertEqual(r["conclusion"], "Y")
        self.assertEqual(r["defeated"], ["B"])

    def test_stacked_signals_change_nothing(self):
        """F6 stacks specificity, recency, confidence, similarity, length and
        ordering all onto one side. Every one of them together must be inert."""
        r = d("F6")
        self.assertEqual(r["status"], CONTESTED)
        self.assertIsNone(r["conclusion"])

    def test_perturbing_signals_does_not_change_any_outcome(self):
        """Structural test, independent of the case list: for every case, the
        outcome must be identical when every Family-F signal is permuted."""
        import dataclasses
        for c in CASES:
            base = run_defeasible(c)["status"]
            flipped = []
            for r in c.rules:
                kw = dict(specificity=1000 - r.specificity,
                          recency=1000 - r.recency,
                          confidence=1.0 - r.confidence,
                          text_similarity=1.0 - r.text_similarity,
                          length=1000 - r.length,
                          order_index=-r.order_index)
                flipped.append(dataclasses.replace(r, **kw))
            mirrored = dataclasses.replace(c, rules=list(reversed(flipped)))
            self.assertEqual(run_defeasible(mirrored)["status"], base,
                             "%s changed when its adversarial signals were permuted"
                             % c.cid)

    def test_engine_source_never_reads_a_forbidden_signal(self):
        """Structural, and it must cover every function the defeasible path
        actually calls — not just the entry point. An earlier version checked
        `run_defeasible` only, and three signal-tiebreak mutants survived by
        hiding the comparison in a helper."""
        import ast, inspect, textwrap
        import corpus as corpus_mod
        banned = {"specificity", "recency", "confidence", "order_index",
                  "text_similarity", "length"}
        checked = 0
        for fname in ("run_defeasible", "_pick", "check_invariants", "out"):
            fn = getattr(corpus_mod, fname, None)
            if fn is None:
                continue
            checked += 1
            tree = ast.parse(textwrap.dedent(inspect.getsource(fn)))
            for node in ast.walk(tree):
                if isinstance(node, ast.Attribute) and node.attr in banned:
                    self.fail("%s reads the inert signal %r at line %d"
                              % (fname, node.attr, node.lineno))
        self.assertGreaterEqual(checked, 3, "the structural check covered too little")

    def test_refusal_arm_has_no_hidden_heuristic_either(self):
        """The pre-encoded arm DOES use authority rank to pick a winner. That is
        legitimate for a translator, but it must never be presented as having
        a represented reason — and its trace must admit that."""
        r = run_refusal(BY_ID["F1"], True)
        self.assertEqual(r["status"], DECIDED)
        self.assertFalse(r["represented_reason"])
        self.assertIn("no represented defeat relation", r["trace"][0][1])


class TwoAxes(unittest.TestCase):
    def test_refusal_is_correct_on_a_substantial_minority(self):
        """If refusal were almost always wrong, the whole control would be
        strawmanned and the experiment meaningless."""
        n = sum(1 for c in CASES if c.refusal_is_correct)
        self.assertGreater(n, len(CASES) * 0.25)
        self.assertLess(n, len(CASES) * 0.75)

    def test_precedence_arm_decides_without_justifying(self):
        """The headline finding, restated after v0.3.

        This arm used to score decisiveness 1.00 with zero represented
        reasons -- maximum decisiveness purchased by having no reason for any
        of it. That number was partly fraudulent: it included E1-E5, where
        the arm confidently answered a corpus it never validated. Once it
        validates first, it scores 0.73, and every point it loses is one it
        was inventing.

        The finding survives and is better for the loss. What the arm still
        demonstrates is the thing that matters: it reaches its decisions
        without a single represented reason. Decisiveness and justification
        are separate axes, and a precedence rule buys the first with the
        corpus's money.
        """
        t = measure(CASES)
        m = t["refusal+prec"]
        self.assertGreater(m["decisiveness"], 0.70)
        self.assertEqual(m["justified"], 0)
        # it must not claim more than it can show for itself
        self.assertGreater(m["decisiveness"], t["defeasible"]["decisiveness"])

    def test_defeasible_arm_is_lower_decisive_but_fully_justified(self):
        t = measure(CASES)
        d_, p_ = t["defeasible"], t["refusal+prec"]
        self.assertLess(d_["decisiveness"], p_["decisiveness"])
        self.assertGreater(d_["justification"], 0.9)

    def test_no_regime_returns_an_out_of_vocabulary_status(self):
        allowed = {DECIDED, DEFEATED, REFUSED, CONTESTED, NONFINDING, INVALID}
        for c in CASES:
            for name, fn in REGIMES:
                self.assertIn(fn(c)["status"], allowed, "%s/%s" % (c.cid, name))

    def test_every_outcome_states_a_conclusion_or_a_reason(self):
        for c in CASES:
            for name, fn in REGIMES:
                r = fn(c)
                self.assertTrue(r["conclusion"] or r["reason"],
                                "%s/%s was silent" % (c.cid, name))

    def test_decided_contested_cases_preserve_both_arguments(self):
        for c in CASES:
            r = run_defeasible(c)
            if r["status"] == CONTESTED:
                args = [t for t in r["trace"] if t[0] == "argument"]
                self.assertEqual(len(args), 2, c.cid)


if __name__ == "__main__":
    unittest.main(verbosity=2)
