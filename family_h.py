#!/usr/bin/env python3
"""
Family H — reachability and precedence.

SIT v0.2 converged at 36 cases with ZERO disagreements, which sounded like
success and was actually a coverage hole: two of the six statuses in the
vocabulary (NONFINDING, DEFEATED) could not be produced by ANY case, and two
orderings had no defined answer. Agreement on the cases you happened to build
says nothing about the parts you never asked about.

Family H is the adversarial family. Each case is built to make the engine
commit to something it has never had to commit to. Four of the five exist only
to break something:

  H1  NONFINDING   — valid corpus, well-formed query, nothing applies.
  H2  DEFEATED     — an argument is defeated and nothing survives to carry
                     its conclusion, so there IS a question and NO answer.
  H3  precedence    — structurally invalid AND unrepresentable. The spec does
                     not say which status wins. This case forces a choice.
  H4  nothing-applies-but-defeats-exist — the distinction between "there was
                     nothing to find" and "everything was killed".
  H5  resource exhaustion — the iteration bound is exhausted on a WEAKLY
                     FOUNDED chain. A correct engine must NOT report this as
                     indeterminacy; an exhausted budget is an operational fact,
                     not an epistemic one (F-1).

H5 is the important one. It is the case that distinguishes "the formalism has
no well-founded extension" from "my loop ran out of rounds" — two claims that
happen to share a return value in a naive engine.
"""
from corpus import Case, Rule, Defeat, X, Y, NOT_Y

H = []


def add(cid, note, **kw):
    H.append(Case(cid, "H", note, **kw))


# ---------------------------------------------------------------------------
# H1: NONFINDING. The query is perfectly well formed. The corpus is sound. No
# rule's condition holds on this state. There is no contest, no defect, and no
# refusal — there is simply no applicable argument.
# A refusal regime must also say NONFINDING here, not REFUSE: refusing would
# claim the question was malformed when it was merely unanswerable today.
add("H1", "well-formed query, no rule applies -> NONFINDING",
    state={"Z"}, at=10,
    rules=[Rule("A", "statute_01", "legislature", "statute_01 §1", X, Y)],
    defeats=[],
    expect_defeasible="NONFINDING", refusal_is_correct=True)

# ---------------------------------------------------------------------------
# H2: DEFEATED. This is the state the project most needs and never had.
# There IS an applicable argument (so not NONFINDING), it IS defeated on a
# valid basis, and NOTHING survives to establish its conclusion. The engine
# must report DEFEATED rather than silently returning an empty accepted set —
# an empty set and a killed set are different claims about the world.
# H2 was intended to force DEFEATED. It cannot, and proving WHY is the point.
#
# DEFEATED is unreachable BY CONSTRUCTION, not merely untested. Grounded
# semantics on a non-empty Theta always yields a non-empty extension, so the
# branch `if not survivors` in run_defeasible() is dead code. Exhaustive check
# over every 3-node defeat graph (all 64 relations) confirms it: no input
# produces an empty extension.
#
# So the state is not waiting for a fixture. It is unreachable, and the honest
# response is to DECLARE it reserved rather than manufacture a case that cannot
# exist. See MILESTONE-SIT-V0.3.md, finding R-5.
#
# What H2 does instead is pin the boundary that IS reachable: an argument is
# defeated on a valid basis, and a DIFFERENT argument survives. That is
# DECIDED, and the defeated rule must still be visible in the trace -- a
# silently dropped defeater would make this case indistinguishable from H1.
add("H2", "an argument is defeated; a different one survives -> DECIDED",
    state={X}, at=10,
    rules=[
        Rule("A", "statute_01", "legislature", "statute_01 §1", X, Y),
        # The defeater must itself carry constitutional authority: the basis
        # is a claim about the authority hierarchy, so a decree cannot supply
        # it. An executive here would be rejected at validation and A would
        # survive — which is the fail-closed behaviour, not a bug.
        Rule("B", "const_02", "constitution", "const §2", X, NOT_Y),
    ],
    defeats=[Defeat("A", "B", "explicit_constitutional_supremacy",
                    "const §2: the statute yields to this clause")],
    expect_defeasible="DEFEATED", refusal_is_correct=False)

# ---------------------------------------------------------------------------
# H3: precedence. A corpus that is BOTH structurally invalid (F7: empty
# validity interval) AND unrepresentable (requires_construct). §5 says the
# validity check runs first, but nothing states what the RESULT is when the
# corpus is invalid in a way the representation cannot even express.
# A engine that checks representability first returns REFUSED; one that checks
# validity first returns INVALID. Only one of them is specified.
add("H3", "invalid AND unrepresentable -> precedence must be stated",
    state={X}, at=10,
    rules=[
        Rule("A", "statute_01", "legislature", "statute_01 §1", X, Y,
             requires_construct="counterfactual", effective_from=20,
             effective_to=20),
    ],
    defeats=[],
    expect_defeasible="INVALID", refusal_is_correct=True)

# ---------------------------------------------------------------------------
# H4: the NONFINDING / DEFEATED boundary. A corpus with defeats declared but
# no rule triggered at all. Nothing was killed — nothing was ever in play.
# This is the case that proves H1 and H2 are genuinely different states rather
# than the same state reached by different routes.
add("H4", "defeats declared but nothing triggered -> NONFINDING, not DEFEATED",
    state={"Z"}, at=10,
    rules=[
        Rule("A", "statute_01", "legislature", "statute_01 §1", X, Y),
        Rule("B", "decree_01", "executive", "decree_01 §1", X, NOT_Y),
    ],
    defeats=[Defeat("A", "B", "explicit_constitutional_supremacy", "const §2")],
    expect_defeasible="NONFINDING", refusal_is_correct=True)

# ---------------------------------------------------------------------------
# H5: resource exhaustion. A 4-chain is WEAKLY FOUNDED: grounded semantics has
# a unique, perfectly well-defined extension, and it is reached in 4 rounds.
# Run it with a round bound too small to reach that fixpoint.
#
# A correct engine reports DECIDED, because the framework IS well founded and
# the extension IS determined. An engine that returns SEMANTIC when its budget
# expires is reporting its own computational limit as an epistemic fact about
# the corpus: "the formalism is indeterminate" is a claim, and a small loop
# bound cannot justify it. This is mutant F-1 made into a case.
def _chain(n):
    """A->B->C->... linear defeat chain, ranks pointing the wrong way."""
    ids = [chr(ord("A") + i) for i in range(n)]
    rules = [Rule(ids[i], "r_%s" % ids[i], "agency", "r §%d" % (i + 1), X,
                  Y if i % 2 == 0 else NOT_Y, rank=n - i) for i in range(n)]
    defeats = [Defeat(ids[i], ids[i + 1], "explicit_chain_succession",
                      "ch §%d" % (i + 2)) for i in range(n - 1)]
    return rules, defeats


_R, _D = _chain(4)
add("H5", "well-founded 4-chain with a starved round budget -> still DECIDED",
    state={X}, at=10, rules=_R, defeats=_D,
    expect_defeasible="DECIDED", refusal_is_correct=False)