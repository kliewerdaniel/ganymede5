#!/usr/bin/env python3
"""
The six-family corpus. Each case declares what it tests BEFORE it is run, so
an unexpected result is visible rather than reinterpreted afterwards.
"""
from corpus import Case, Rule, Defeat, X, Y, NOT_Y

C = []


def add(cid, family, note, **kw):
    C.append(Case(cid, family, note, **kw))


# =====================================================================  FAMILY A
# Deterministically resolvable. Precedence is explicit AND unambiguous, so
# every regime may legitimately converge. If defeasible reasoning adds nothing
# here, that is a finding, not a failure.

add("A1", "A", "explicit precedence, no real dispute",
    state={X}, at=10,
    rules=[
        Rule("A", "statute_01", "legislature", "statute_01 §1", X, Y, rank=2),
        Rule("B", "regulation_07", "agency", "regulation_07 §14", X, NOT_Y, rank=1),
    ],
    defeats=[Defeat("B", "A", "explicit_authority_precedence", "statute_01 §1")],
    expect_defeasible="DECIDED", refusal_is_correct=False)

add("A2", "A", "no conflict at all — single applicable rule",
    state={X}, at=10,
    rules=[Rule("A", "statute_01", "legislature", "statute_01 §1", X, Y, rank=1)],
    defeats=[],
    expect_defeasible="DECIDED", refusal_is_correct=False)

add("A3", "A", "precedence encoded but both rules same authority tier",
    state={X}, at=10,
    rules=[
        Rule("A", "statute_01", "agency", "statute_01 §1", X, Y, rank=3),
        Rule("B", "regulation_07", "agency", "regulation_07 §14", X, NOT_Y, rank=1),
    ],
    defeats=[Defeat("B", "A", "explicit_rank_precedence", "statute_01 §1")],
    expect_defeasible="DECIDED", refusal_is_correct=False)

# =====================================================================  FAMILY B
# Genuine defeaters. Argument-level defeat exists. This is the capability
# hypothesis: defeasible resolves where refusal cannot.

add("B1", "B", "genuine defeater, authority precedence",
    state={X}, at=10,
    rules=[
        Rule("A", "statute_01", "legislature", "statute_01 §1", X, Y, rank=2),
        Rule("B", "regulation_07", "agency", "regulation_07 §14", X, NOT_Y, rank=1),
    ],
    defeats=[Defeat("B", "A", "explicit_authority_precedence", "statute_01 §1")],
    expect_defeasible="DECIDED", refusal_is_correct=False)

add("B2", "B", "genuine defeater, temporal — the later rule defeats the earlier",
    state={X}, at=20,
    rules=[
        Rule("A", "statute_01", "agency", "statute_01 §1", X, Y,
             effective_from=0, effective_to=15, rank=2),
        Rule("B", "regulation_07", "agency", "regulation_07 §14", X, NOT_Y,
             effective_from=15, effective_to=None, rank=1),
    ],
    defeats=[Defeat("A", "B", "explicit_lex_posterior", "regulation_07 §14")],
    expect_defeasible="DECIDED", refusal_is_correct=False)

add("B3", "B", "genuine defeater by constitutional supremacy",
    state={X}, at=10,
    rules=[
        Rule("A", "statute_01", "agency", "statute_01 §1", X, Y, rank=1),
        Rule("B", "charter_00", "constitution", "charter_00 art.3", X, NOT_Y, rank=1),
    ],
    defeats=[Defeat("A", "B", "explicit_constitutional_supremacy", "charter_00 art.3")],
    expect_defeasible="DECIDED", refusal_is_correct=False)

add("B4", "B", "genuine defeater, but the defeater is itself out of temporal scope",
    state={X}, at=10,
    rules=[
        Rule("A", "statute_01", "agency", "statute_01 §1", X, Y,
             effective_from=0, effective_to=None, rank=2),
        Rule("B", "regulation_07", "agency", "regulation_07 §14", X, NOT_Y,
             effective_from=50, effective_to=None, rank=1),
    ],
    defeats=[Defeat("A", "B", "explicit_lex_posterior", "regulation_07 §14")],
    expect_defeasible="DECIDED", refusal_is_correct=False)

add("B5", "B", "temporal supersession where BOTH are in force and conflict",
    state={X}, at=25,
    rules=[
        Rule("A", "statute_01", "agency", "statute_01 §1", X, Y,
             effective_from=0, effective_to=None, rank=2),
        Rule("B", "regulation_07", "agency", "regulation_07 §14", X, NOT_Y,
             effective_from=15, effective_to=None, rank=1),
    ],
    defeats=[Defeat("A", "B", "explicit_lex_posterior", "regulation_07 §14")],
    expect_defeasible="DECIDED", refusal_is_correct=False)

# =====================================================================  FAMILY C
# Apparent defeaters. A plausible reason exists but is NOT encoded. These are
# the cases that catch an engine inventing an interpretation.

add("C1", "C", "plausible precedence, NOT encoded",
    state={X}, at=10,
    rules=[
        Rule("A", "statute_01", "legislature", "statute_01 §1", X, Y, rank=1),
        Rule("B", "regulation_07", "agency", "regulation_07 §14", X, NOT_Y, rank=1),
    ],
    defeats=[],
    expect_defeasible="CONTESTED", refusal_is_correct=True)

add("C2", "C", "defeater encoded but DISABLED",
    state={X}, at=10,
    rules=[
        Rule("A", "statute_01", "legislature", "statute_01 §1", X, Y, rank=2),
        Rule("B", "regulation_07", "agency", "regulation_07 §14", X, NOT_Y, rank=1),
    ],
    defeats=[Defeat("B", "A", "explicit_authority_precedence", "statute_01 §1", enabled=False)],
    expect_defeasible="CONTESTED", refusal_is_correct=True)

add("C3", "C", "defeater asserts authority precedence that does not hold",
    state={X}, at=10,
    rules=[
        Rule("A", "statute_01", "legislature", "statute_01 §1", X, Y, rank=1),
        Rule("B", "memo_03", "memo", "memo_03 §2", X, NOT_Y, rank=9),
    ],
    defeats=[Defeat("A", "B", "explicit_authority_precedence", "memo_03 §2")],
    expect_defeasible="CONTESTED", refusal_is_correct=True)

add("C4", "C", "a memo claiming supremacy, carrying every signal it can legally use",
    state={X}, at=10,
    rules=[
        Rule("A", "statute_01", "legislature", "statute_01 §1", X, Y, rank=1),
        Rule("B", "memo_03", "memo", "memo_03 §2", X, NOT_Y,
             rank=99, specificity=99, recency=99, confidence=0.99,
             text_similarity=0.99, length=999, order_index=0),
    ],
    defeats=[Defeat("A", "B", "explicit_rank_precedence", "memo_03 §2")],
    expect_defeasible="DECIDED", refusal_is_correct=False)

# =====================================================================  FAMILY D
# Unexpressible constructs. "We cannot represent this" must never become
# "therefore false".

add("D1", "D", "rule requires an operation outside the set",
    state={X}, at=10,
    rules=[
        Rule("A", "statute_01", "legislature", "statute_01 §1", X, Y, rank=2),
        Rule("B", "regulation_07", "agency", "regulation_07 §14", X, NOT_Y,
             requires_construct="ROUND", rank=1),
    ],
    defeats=[Defeat("B", "A", "explicit_authority_precedence", "statute_01 §1")],
    expect_defeasible="REFUSED", refusal_is_correct=True)

add("D2", "D", "unexpressible construct on the WINNING side",
    state={X}, at=10,
    rules=[
        Rule("A", "statute_01", "legislature", "statute_01 §1", X, Y,
             requires_construct="DISCRETIONARY_BALANCE", rank=2),
        Rule("B", "regulation_07", "agency", "regulation_07 §14", X, NOT_Y, rank=1),
    ],
    defeats=[Defeat("B", "A", "explicit_authority_precedence", "statute_01 §1")],
    expect_defeasible="REFUSED", refusal_is_correct=True)

# =====================================================================  FAMILY E
# Invalid corpus. Argumentation must NOT be able to rescue a procedurally
# invalid corpus. This is the test of F2/F3 and of the whole INVALID state.

add("E1", "E", "unpromulgated rule attempts to defeat a statute",
    state={X}, at=10,
    rules=[
        Rule("A", "statute_01", "legislature", "statute_01 §1", X, Y, rank=1),
        Rule("B", "decree_09", "agency", "decree_09 §1", X, NOT_Y, rank=9,
             promulgated=False),
    ],
    defeats=[Defeat("A", "B", "explicit_authority_precedence", "decree_09 §1")],
    expect_defeasible="INVALID", refusal_is_correct=False)

add("E2", "E", "retroactive operation",
    state={X}, at=10,
    rules=[
        Rule("A", "statute_01", "agency", "statute_01 §1", X, Y, rank=2),
        Rule("B", "regulation_07", "agency", "regulation_07 §14", X, NOT_Y, rank=1,
             effective_from=5, retroactive=True),
    ],
    defeats=[Defeat("A", "B", "explicit_lex_posterior", "regulation_07 §14")],
    expect_defeasible="INVALID", refusal_is_correct=False)

add("E3", "E", "impossible temporal relation — empty validity interval",
    state={X}, at=10,
    rules=[
        Rule("A", "statute_01", "legislature", "statute_01 §1", X, Y,
             effective_from=20, effective_to=20, rank=2),
        Rule("B", "regulation_07", "agency", "regulation_07 §14", X, NOT_Y, rank=1),
    ],
    defeats=[],
    expect_defeasible="INVALID", refusal_is_correct=False)

add("E4", "E", "defeater references a rule that does not exist",
    state={X}, at=10,
    rules=[
        Rule("A", "statute_01", "legislature", "statute_01 §1", X, Y, rank=1),
        Rule("B", "regulation_07", "agency", "regulation_07 §14", X, NOT_Y, rank=1),
    ],
    defeats=[Defeat("A", "GHOST", "explicit_authority_precedence", "ghost §1")],
    expect_defeasible="INVALID", refusal_is_correct=False)

add("E5", "E", "duplicate rule id",
    state={X}, at=10,
    rules=[
        Rule("A", "statute_01", "legislature", "statute_01 §1", X, Y, rank=1),
        Rule("A", "statute_01", "legislature", "statute_01 §1", X, Y, rank=1),
        Rule("B", "regulation_07", "agency", "regulation_07 §14", X, NOT_Y, rank=1),
    ],
    defeats=[],
    expect_defeasible="INVALID", refusal_is_correct=False)

# =====================================================================  FAMILY F
# Adversarial irrelevant features. Every signal here would "help" a heuristic
# and is semantically inert unless explicitly represented as a defeat relation.
# Expected: the signal has no effect whatever on the result.

add("F1", "F", "specificity: the losing side is 99x more specific",
    state={X}, at=10,
    rules=[
        Rule("A", "statute_01", "legislature", "statute_01 §1", X, Y,
             rank=1, specificity=1),
        Rule("B", "memo_03", "memo", "memo_03 §2", X, NOT_Y,
             rank=1, specificity=99),
    ],
    defeats=[],
    expect_defeasible="CONTESTED", refusal_is_correct=True)

add("F2", "F", "recency: the losing side is the newer instrument",
    state={X}, at=10,
    rules=[
        Rule("A", "statute_01", "legislature", "statute_01 §1", X, Y,
             rank=1, recency=1),
        Rule("B", "regulation_07", "agency", "regulation_07 §14", X, NOT_Y,
             rank=1, recency=99),
    ],
    defeats=[],
    expect_defeasible="CONTESTED", refusal_is_correct=True)

add("F3", "F", "confidence: the losing side is 99% confident",
    state={X}, at=10,
    rules=[
        Rule("A", "statute_01", "legislature", "statute_01 §1", X, Y,
             rank=1, confidence=0.01),
        Rule("B", "regulation_07", "agency", "regulation_07 §14", X, NOT_Y,
             rank=1, confidence=0.99),
    ],
    defeats=[],
    expect_defeasible="CONTESTED", refusal_is_correct=True)

add("F4", "F", "order: the attractive rule is listed first",
    state={X}, at=10,
    rules=[
        Rule("B", "regulation_07", "memo", "regulation_07 §14", X, NOT_Y,
             rank=1, order_index=0, specificity=50),
        Rule("A", "statute_01", "legislature", "statute_01 §1", X, Y,
             rank=1, order_index=1, specificity=1),
    ],
    defeats=[],
    expect_defeasible="CONTESTED", refusal_is_correct=True)

add("F5", "F", "textual similarity: the losing side reads more like the condition",
    state={X}, at=10,
    rules=[
        Rule("A", "statute_01", "legislature", "statute_01 §1", X, Y,
             rank=1, text_similarity=0.1, length=40),
        Rule("B", "regulation_07", "agency", "regulation_07 §14", X, NOT_Y,
             rank=1, text_similarity=0.99, length=900),
    ],
    defeats=[],
    expect_defeasible="CONTESTED", refusal_is_correct=True)

add("F6", "F", "all attractive signals stacked on one side",
    state={X}, at=10,
    rules=[
        Rule("A", "statute_01", "legislature", "statute_01 §1", X, Y,
             rank=1, specificity=1, recency=1, confidence=0.01,
             text_similarity=0.05, length=30, order_index=1),
        Rule("B", "memo_03", "memo", "memo_03 §2", X, NOT_Y,
             rank=1, specificity=99, recency=99, confidence=0.99,
             text_similarity=0.99, length=999, order_index=0),
    ],
    defeats=[],
    expect_defeasible="CONTESTED", refusal_is_correct=True)

add("F7", "F", "attractive signals on a side that genuinely IS defeated",
    state={X}, at=10,
    rules=[
        Rule("A", "statute_01", "legislature", "statute_01 §1", X, Y,
             rank=2, specificity=1, confidence=0.01),
        Rule("B", "regulation_07", "agency", "regulation_07 §14", X, NOT_Y,
             rank=1, specificity=99, confidence=0.99),
    ],
    defeats=[Defeat("B", "A", "explicit_authority_precedence", "statute_01 §1")],
    expect_defeasible="DECIDED", refusal_is_correct=False)

CASES = C
