#!/usr/bin/env python3
"""
Ganymede5 defeat semantics. Implements SEMANTICS.md.

Separation of concerns, and it is the same separation the project claims as an
architectural principle:

  corpus.py      validates defeat relations against their STATED BASIS.
                 A relation whose basis is not satisfied is not a defeat, it is
                 a claim of a defeat. This is a CORPUS question.

  semantics.py   computes acceptance as a grounded fixpoint over the relations
                 that survived validation. This is a SEMANTIC question.

Neither layer may consult the other. In particular the fixpoint layer has no
tiebreak available to it, because ratification removed the tiebreaks from the
spec rather than trusting the code to decline them.

`SEMANTIC` and `CORPUS` uncertainty are returned as distinct values. They are
never merged. `IMPLEMENTATION` is deliberately not producible here: only the
grader may assert it, and it is a harness finding, never an outcome.

Grounded semantics (Dung). S(0) = Theta, S(n+1) = { r : r unattacked in S(n) },
computed over ALL of Theta each step. The sequence need not be monotone and
need not converge. Non-convergence is a finding, reported as CONTESTED with
SEMANTIC uncertainty, never as a decision.
"""
from typing import Dict, List, Optional, Set, Tuple

SEMANTIC = "SEMANTIC"


class BudgetExhausted(RuntimeError):
    """Iteration bound reached. An operational failure, NOT an epistemic result.

    Raising rather than returning SEMANTIC is deliberate: a budget that is
    exhausted has learned nothing about the corpus, and a status code is a
    claim. See MILESTONE-SIT-V0.3.md finding F-1.
    """
    pass
CORPUS = "CORPUS"
NONE = "NONE"

CONTESTED = "CONTESTED"


class SelfDefeat(Exception):
    """A rule defeats itself. A corpus defect, not an open question."""


def _attack_map(relations: List[Tuple[str, str]]) -> Dict[str, Set[str]]:
    """attacker -> set of rules it attacks."""
    attacks: Dict[str, Set[str]] = {}
    for attacker, target in relations:
        if attacker == target:
            raise SelfDefeat(attacker)
        attacks.setdefault(attacker, set()).add(target)
    return attacks


def accepted(theta: Set[str],
             relations: List[Tuple[str, str]],
             max_rounds: Optional[int] = None
             ) -> Tuple[Set[str], str, List[Set[str]]]:
    """
    Ground the framework.

    Returns (accepted, uncertainty, history).

    uncertainty is SEMANTIC when acceptance could not be determined, CORPUS is
    never returned here (that is corpus.py's layer to report), NONE otherwise.
    """
    if not relations:
        return set(theta), NONE, [set(theta)]

    attacks = _attack_map(relations)
    # reverse index: target -> attackers
    attacked_by: Dict[str, Set[str]] = {}
    for attacker, targets in attacks.items():
        for t in targets:
            attacked_by.setdefault(t, set()).add(attacker)

    if max_rounds is None:
        max_rounds = 2 * len(theta) + 2

    s = set(theta)
    history = [s]
    for _ in range(max_rounds):
        nxt = {r for r in theta if not (attacked_by.get(r, set()) & s)}
        if nxt == s:
            return s, NONE, history
        if nxt in history:
            # Oscillation. The operator demonstrably has no stable fixpoint on
            # this framework. This IS an epistemic finding about the corpus.
            return s, SEMANTIC, history
        s = nxt
        history.append(s)

    # F-1. The budget ran out. This is NOT the same claim as the branch above.
    # Oscillation is a property of the defeat graph; an exhausted bound is a
    # property of the caller's loop limit. Reporting SEMANTIC here would let
    # the engine assert "the formalism is indeterminate" on the authority of
    # its own arithmetic -- the same class of error as an absent date read as
    # -inf. Fail loudly instead of returning an epistemic verdict we have not
    # earned. The default bound is derived from |theta| and provably suffices
    # for a well-founded framework, so this is a programming error if hit.
    raise BudgetExhausted(
        "grounded iteration exceeded %d rounds without stabilising; "
        "this is an operational limit, not a finding about the framework "
        "(SEMANTICS.md 4.5)" % max_rounds)


def cycle_members(relations: List[Tuple[str, str]]) -> List[List[str]]:
    """
    Every directed cycle in the attack relation, as a node list.

    Reported alongside CONTESTED so the contest is contestable: the affected
    party can see WHICH structure failed to resolve, not merely that something
    did.
    """
    succ: Dict[str, List[str]] = {}
    for a, t in relations:
        succ.setdefault(a, []).append(t)

    cycles: List[List[str]] = []
    seen: Set[frozenset] = set()
    colour: Dict[str, int] = {}
    stack: List[str] = []

    def visit(node: str):
        colour[node] = 1
        stack.append(node)
        for nxt in sorted(succ.get(node, [])):
            c = colour.get(nxt, 0)
            if c == 0:
                visit(nxt)
            elif c == 1:
                i = stack.index(nxt)
                cyc = stack[i:]
                key = frozenset(cyc)
                if key not in seen:
                    seen.add(key)
                    cycles.append(list(cyc))
        stack.pop()
        colour[node] = 2

    for n in sorted(succ):
        if colour.get(n, 0) == 0:
            visit(n)
    return cycles
