#!/usr/bin/env python3
"""
Family G — nested defeat chains.

The question this family asks is narrow and falsifiable:

  Can the defeasible representation preserve a defeat STRUCTURE, or does it
  collapse to "the highest numeric rank wins"?

Every case is built so that the two answers differ. Numeric ranks are set so
that a rank-based tiebreak and a structure-preserving result DISAGREE. If the
engine collapses, the disagreement shows up immediately.
"""
from corpus import Case, Rule, Defeat, X, Y, NOT_Y, CONTRADICTS

# Family G needs a second pair of contradictory atoms, because G6 carries two
# independent contests in one corpus.
Q, Q1, NOT_Q = "Q", "Q1", "NOT-Q"
CONTRADICTS[Q1] = NOT_Q
CONTRADICTS[NOT_Q] = Q1

G = []


def add(cid, note, **kw):
    G.append(Case(cid, "G", note, **kw))


# A defeats nothing; B defeats A; C defeats B; D defeats C.
# Ranks DESCEND along the chain, so "highest rank wins" picks A — the wrong
# end of the chain. A structure-preserving engine must reach D.
add("G1", "linear chain, ranks point the wrong way",
    state={X}, at=10,
    rules=[
        # The admitted set is {B, D}. B is the operative rule and must assert
        # the contested atom, otherwise the case cannot discriminate.
        # A(rank 9) says Y; B(rank 8) says NOT-Y. A rank collapse answers Y;
        # the grounded structure answers NOT-Y.
        Rule("A", "r_a", "agency", "r_a §1", X, Y, rank=9),
        Rule("B", "r_b", "agency", "r_b §1", X, NOT_Y, rank=8),
        Rule("C", "r_c", "agency", "r_c §1", X, "B1", rank=7),
        # B is the ADMITTED rule and must assert the contested atom, otherwise
        # the case cannot discriminate. B asserting A1 (a derived atom) while
        # D asserts NOT-Y meant the survivors never contradicted, so G1 could
        # not test the thing it was built to test. FOURTH case-design error,
        # found when the grounded fixpoint made the surviving set visible.
        Rule("D", "r_d", "agency", "r_d §1", X, NOT_Y, rank=6),
    ],
    defeats=[
        Defeat("A", "B", "explicit_chain_succession", "r_b §1"),
        Defeat("B", "C", "explicit_chain_succession", "r_c §1"),
        Defeat("C", "D", "explicit_chain_succession", "r_d §1"),
    ])

# Two chains that both terminate at B and neither dominates.
# D > C > B and E > F > B. Nothing defeats D or E, so two arguments survive.
# Ranks put E above D so that a rank tiebreak would pick the wrong branch.
add("G2", "two chains terminate without a dominant argument",
    state={X}, at=10,
    rules=[
        Rule("B", "r_b", "agency", "r_b §1", X, Y, rank=1),
        Rule("C", "r_c", "agency", "r_c §1", X, "B1", rank=5),
        Rule("D", "r_d", "agency", "r_d §1", X, NOT_Y, rank=6),
        Rule("E", "r_e", "agency", "r_e §1", X, "Z1", rank=9),
        Rule("F", "r_f", "agency", "r_f §1", X, "E1", rank=8),
    ],
    defeats=[
        Defeat("B", "C", "explicit_chain_succession", "r_c §1"),
        Defeat("C", "D", "explicit_chain_succession", "r_d §1"),
        Defeat("E", "F", "explicit_chain_succession", "r_f §1"),
    ])

# The middle of a chain is switched off. B beats A; C's defeat of B is off.
# C and A both survive and contradict.
add("G3", "chain broken in the middle",
    state={X}, at=10,
    rules=[
        Rule("A", "r_a", "agency", "r_a §1", X, Y, rank=9),
        Rule("B", "r_b", "agency", "r_b §1", X, "A1", rank=8),
        Rule("C", "r_c", "agency", "r_c §1", X, NOT_Y, rank=7),
    ],
    defeats=[
        Defeat("A", "B", "explicit_chain_succession", "r_b §1"),
        Defeat("B", "C", "explicit_chain_succession", "r_c §1", enabled=False),
    ])

# A cycle. C defeats B and B defeats C. There is no well-founded argument
# set, so no winner may be reported. Ranks are set so a rank tiebreak would
# confidently name one of them.
add("G4", "defeat cycle — no well-founded argument set",
    state={X}, at=10,
    rules=[
        Rule("B", "r_b", "agency", "r_b §1", X, Y, rank=2),
        Rule("C", "r_c", "agency", "r_c §1", X, NOT_Y, rank=7),
    ],
    defeats=[
        Defeat("B", "C", "explicit_chain_succession", "r_c §1"),
        Defeat("C", "B", "explicit_chain_succession", "r_b §1"),
    ])

# An exception to an exception. B beats A; C beats B; D is an exception to C.
# With D present, C's defeat of B is defeated, so B's defeat of A stands.
add("G5", "exception to an exception — the reversal must be visible",
    state={X}, at=10,
    rules=[
        # Same admitted set {B, D} as G1. B is operative; D is the
        # constitution asserting the opposite atom at a higher rank, so
        # "prefer the terminal/higher-authority rule" is visible as wrong.
        Rule("A", "r_a", "agency", "r_a §1", X, Y, rank=1),
        Rule("B", "r_b", "agency", "r_b §1", X, NOT_Y, rank=2),
        Rule("C", "r_c", "agency", "r_c §1", X, "B1", rank=3),
        Rule("D", "r_d", "constitution", "r_d art.1", X, Y, rank=4),
    ],
    defeats=[
        Defeat("A", "B", "explicit_chain_succession", "r_b §1"),
        Defeat("B", "C", "explicit_chain_succession", "r_c §1"),
        Defeat("C", "D", "explicit_exception", "r_d art.1"),
    ])

# Two independent contests in one case. The engine must not let resolving the
# first license a conclusion about the second.
add("G6", "two independent contests in one corpus",
    state={X, "P"}, at=10,
    rules=[
        Rule("A", "r_a", "agency", "r_a §1", X, Y, rank=2),
        Rule("B", "r_b", "memo", "r_b §1", X, NOT_Y, rank=1),
        Rule("C", "r_c", "agency", "r_c §1", "P", "Q1", rank=2),
        Rule("D", "r_d", "memo", "r_d §1", "P", NOT_Q, rank=1),
    ],
    defeats=[
        Defeat("A", "C", "explicit_authority_precedence", "r_c §1"),
    ])


# G2b — the corrected G2. Two independent chains, each terminating in a rule
# that asserts a contradictory conclusion, with NOTHING relating the two
# branches. This is the case a rank-based tiebreak cannot get right: E and D
# are unrelated, so no transitive order exists between them.
add("G2b", "two unrelated branches reach contradictory conclusions",
    state={X}, at=10,
    rules=[
        Rule("B", "r_b", "agency", "r_b §1", X, Y, rank=1),
        Rule("C", "r_c", "agency", "r_c §1", X, "B1", rank=5),
        Rule("D", "r_d", "agency", "r_d §1", X, NOT_Y, rank=6),
        Rule("E", "r_e", "agency", "r_e §1", X, NOT_Y, rank=9),
        Rule("F", "r_f", "agency", "r_f §1", X, "E1", rank=8),
    ],
    defeats=[
        Defeat("B", "C", "explicit_chain_succession", "r_c §1"),
        Defeat("C", "D", "explicit_chain_succession", "r_d §1"),
        Defeat("E", "F", "explicit_chain_succession", "r_f §1"),
    ])

# G2c — the sharpest version. Identical to G2b except the survivors assert
# OPPOSITE conclusions and carry equal authority and equal rank. Nothing but a
# tiebreak could separate them, and no tiebreak is licensed. If the engine
# names a winner here it has invented one.
add("G2c", "survivors contradict, identical authority and rank",
    state={X}, at=10,
    rules=[
        Rule("B", "r_b", "agency", "r_b §1", X, Y, rank=1),
        Rule("C", "r_c", "agency", "r_c §1", X, "B1", rank=5),
        Rule("D", "r_d", "memo", "r_d §1", X, NOT_Y, rank=3),
        Rule("E", "r_e", "memo", "r_e §1", X, Y, rank=3),
    ],
    defeats=[
        Defeat("B", "C", "explicit_chain_succession", "r_c §1"),
        Defeat("C", "D", "explicit_chain_succession", "r_d §1"),
        Defeat("E", "C", "explicit_chain_succession", "r_c §1"),
    ])


# --- Cases added to close mutation survivors. Each exists because a ratified
# commitment was NOT actually being tested, and the mutation run proved it.

# G7: two admitted rules assert the SAME atom but carry different authority.
# Any preference for the higher-authority rule is then unobservable, because a
# correct engine and a preference-driven engine agree on the conclusion. This
# is the case that makes M4 and M11 detectable: the difference must show in the
# TRACE (which rule is named), not in the conclusion.
add("G7", "equal-atom survivors differing only in authority",
    state={X}, at=10,
    rules=[
        Rule("M", "r_m", "memo", "r_m §1", X, Y, rank=1),
        Rule("N", "r_n", "agency", "r_n §1", X, Y, rank=2),
    ],
    defeats=[])

# G8: a rule defeats itself. This is a CORPUS defect (SEMANTICS.md 4.4) and
# must be INVALID -- a state deliberately different from CONTESTED.
add("G8", "self-defeating rule",
    state={X}, at=10,
    rules=[
        Rule("A", "r_a", "agency", "r_a §1", X, Y, rank=3),
    ],
    defeats=[
        Defeat("A", "A", "explicit_chain_succession", "r_a §1"),
    ])
