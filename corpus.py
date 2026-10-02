#!/usr/bin/env python3
"""
Ganymede5 Experiment 0b — the six-family corpus.

Experiment 0 built one divergent case. This builds a corpus designed to make
the capability hypothesis FALSIFIABLE, including cases chosen to make the
defeasible approach look unnecessary.

THE MEASUREMENT

Two axes, deliberately separate, because they can diverge:

  decisiveness   fraction of cases returning DECIDED
  justification  fraction of DECIDED cases carrying a represented defeat
                 relation in the trace

A regime can raise decisiveness while justification stays flat. That gap is
the finding, and it is the precise form of "resolution is not decision."

FAMILIES

  A  deterministically resolvable    precedence explicit and unambiguous
  B  genuine defeaters               argument-level defeat exists
  C  apparent defeaters              plausible reason, not encoded
  D  unexpressible constructs        outside the operation set
  E  invalid corpus                  malformed authority / promulgation / time
  F  adversarial irrelevant features salience signals with no semantic force

Family F is the important one. It asks whether the engine has a hidden
heuristic layer that it consults when the formalism is silent.
"""
import json
from dataclasses import dataclass, replace
from typing import List, Optional, Set, Tuple

DECIDED = "DECIDED"
DEFEATED = "DEFEATED"
REFUSED = "REFUSED"
CONTESTED = "CONTESTED"
NONFINDING = "NONFINDING"
INVALID = "INVALID"

X, Y, NOT_Y = "X", "Y", "NOT-Y"
CONTRADICTS = {Y: NOT_Y, NOT_Y: Y}

AUTH_RANK = {"constitution": 4, "legislature": 3, "agency": 2, "memo": 1}


@dataclass(frozen=True)
class Rule:
    id: str
    source: str
    authority: str
    cites: str
    condition: str
    conclusion: str
    requires_construct: Optional[str] = None
    # Adjudicative weight. Used ONLY through an explicit, represented defeat
    # relation. Never consulted directly, never as a tiebreak.
    rank: int = 0
    promulgated: bool = True
    # Default False. A rule with a defined start is normally prospective; the
    # retroactive case must be stated explicitly (as E2 does).
    retroactive: bool = False
    effective_from: Optional[int] = None   # temporal: None = always
    effective_to: Optional[int] = None
    # Family F. Tempting, semantically inert unless explicitly represented.
    specificity: int = 0
    recency: int = 0
    length: int = 0
    confidence: float = 0.0
    order_index: int = 0
    text_similarity: float = 0.0


@dataclass(frozen=True)
class Defeat:
    defeated: str
    defeater: str
    basis: str
    provenance: str
    enabled: bool = True


@dataclass
class Case:
    cid: str
    family: str
    note: str
    state: Set[str]
    at: Optional[int] = None
    # Optional fields carry no default and are normalised in __post_init__.
    rules: Optional[List[Rule]] = None
    defeats: Optional[List[Defeat]] = None
    # What the case is designed to test, stated before it is run.
    expect_defeasible: Optional[str] = None
    # The decisive question: is refusal here CORRECT, or a limitation?
    refusal_is_correct: Optional[bool] = None

    def __post_init__(self):
        if self.rules is None:
            self.rules = []
        if self.defeats is None:
            self.defeats = []
        if self.state is None:
            self.state = set()

    def triggered(self) -> List[Rule]:
        out = []
        for r in self.rules:
            if r.condition not in self.state:
                continue
            if r.effective_from is not None and self.at is not None and self.at < r.effective_from:
                continue
            if r.effective_to is not None and self.at is not None and self.at >= r.effective_to:
                continue
            out.append(r)
        return out


# ----------------------------------------------------------------- regime 1/2

def run_refusal(c: Case, encoded_precedence: bool = False) -> dict:
    trace = []
    blocked = [r for r in c.rules if r.requires_construct]
    if blocked:
        return out(REFUSED, trace, audit=True,
                    reason="operation set cannot express %s" % blocked[0].requires_construct)

    live = c.triggered()
    concl = {r.conclusion: r for r in live}
    conflict = [a for a in concl if a in CONTRADICTS and CONTRADICTS[a] in concl]
    if conflict and not encoded_precedence:
        return out(REFUSED, trace, reason="unresolved normative conflict in the operation set")
    if conflict and encoded_precedence:
        # The translator resolved it. Highest authority wins. Note what the
        # trace can and cannot say about why.
        winner = max(live, key=lambda r: (AUTH_RANK.get(r.authority, 0), r.rank))
        trace.append(("translator_encoded_precedence",
                      "no represented defeat relation exists in the corpus",
                      winner.id, winner.conclusion))
        return out(DECIDED, trace, conclusion=winner.conclusion, represented_reason=False)
    if not live:
        return out(NONFINDING, trace, reason="no rule triggered on state")
    return out(DECIDED, trace, conclusion=live[0].conclusion, represented_reason=False)


# ------------------------------------------------------------------- regime 3

def check_invariants(c: Case) -> List[str]:
    v = []
    seen = set()
    for r in c.rules:
        if r.id in seen:
            v.append("F5_NON_CONTRADICTION: duplicate rule id %s" % r.id)
        seen.add(r.id)
        if not r.promulgated:
            v.append("F2_PROMULGATION: %s is unpromulgated (%s)" % (r.id, r.source))
        if r.retroactive and r.effective_from is not None:
            v.append("F3_NON_RETROACTIVITY: %s operates retroactively (%s)"
                     % (r.id, r.source))
        if (r.effective_from is not None and r.effective_to is not None
                and r.effective_from >= r.effective_to):
            v.append("F7_CONSTANCY: %s has an empty validity interval" % r.id)
    for d in c.defeats:
        if d.defeated not in {r.id for r in c.rules} or d.defeater not in {r.id for r in c.rules}:
            v.append("F1_GENERALITY: defeater references an unknown rule (%s/%s)"
                     % (d.defeater, d.defeated))
    return v


def run_defeasible(c: Case) -> dict:
    trace = []
    violations = check_invariants(c)
    if violations:
        trace.append(("invariant_violation", "; ".join(violations)))
        return out(INVALID, trace, reason=violations[0], represented_reason=False)

    blocked = [r for r in c.rules if r.requires_construct]
    if blocked:
        return out(REFUSED, trace, audit=True,
                    reason="operation set cannot express %s" % blocked[0].requires_construct,
                    represented_reason=False)

    live = {r.id: r for r in c.triggered()}
    if not live:
        return out(NONFINDING, trace, reason="no rule triggered on state", represented_reason=False)

    concl = {r.conclusion: r for r in live.values()}
    conflict = [a for a in concl if a in CONTRADICTS and CONTRADICTS[a] in concl]

    # Defeat: enabled AND represented AND actually supported by precedence.
    defeated = {}
    for d in c.defeats:
        if not d.enabled:
            trace.append(("defeat_absent", d.defeated, d.defeater, d.basis))
            continue
        if d.defeated not in live or d.defeater not in live:
            trace.append(("defeat_inapplicable", d.defeated, d.defeater, d.basis))
            continue
        lo, hi = live[d.defeated], live[d.defeater]
        # Precedence must be checked against the BASIS the corpus states.
        # A temporal supersession rests on dates, not on adjudicative weight;
        # checking it with rank would silently convert "later rule wins" into
        # "heavier rule wins", which is a different and wrong claim.
        if d.basis == "explicit_lex_posterior":
            lo_from = lo.effective_from if lo.effective_from is not None else float("-inf")
            hi_from = hi.effective_from if hi.effective_from is not None else float("-inf")
            holds = hi_from > lo_from
        elif d.basis == "explicit_constitutional_supremacy":
            holds = AUTH_RANK.get(hi.authority, 0) > AUTH_RANK.get(lo.authority, 0)
        elif d.basis == "explicit_authority_precedence":
            # Authority precedence means authority order. A numeric rank may
            # NOT substitute for it, or a memo given rank=9 would defeat a
            # statute — which is the heuristic failure this project exists to
            # detect, wearing a formalism's clothes.
            holds = AUTH_RANK.get(hi.authority, 0) > AUTH_RANK.get(lo.authority, 0)
        else:  # explicit_rank_precedence — here an explicit rank IS the basis
            holds = hi.rank > lo.rank
        if not holds:
            trace.append(("defeat_rejected", d.defeated, d.defeater,
                          "precedence does not hold for basis %s" % d.basis))
            continue
        defeated[d.defeated] = d
        trace.append(("defeat", d.defeated, d.defeater, d.basis, d.provenance))

    survivors = [r for r in live.values() if r.id not in defeated]
    s_concl = {r.conclusion for r in survivors}

    if conflict:
        a = conflict[0]
        b = CONTRADICTS[a]
        if a in s_concl and b in s_concl:
            for r in live.values():
                trace.append(("argument", r.id, r.source, r.authority, r.cites, r.conclusion))
            return out(CONTESTED, trace,
                       reason="both arguments survive; no represented defeat relation",
                       represented_reason=False)
        win = _pick(survivors)
        trace.append(("result", win.id, win.conclusion, "defeated: " + ",".join(sorted(defeated))))
        return out(DECIDED, trace, conclusion=win.conclusion,
                   represented_reason=bool(defeated),
                   defeated=sorted(defeated))

    if not survivors:
        return out(DEFEATED, trace, reason="every triggered rule was defeated",
                   represented_reason=True, defeated=sorted(defeated))
    win = _pick(survivors)
    return out(DECIDED, trace, conclusion=win.conclusion, represented_reason=False)


def _pick(survivors):
    """Order survivors by authority then explicit rank. Nothing else.

    Sorting is only reached when survivors do not contradict each other, so
    this is a total order for picking a representative, not a tiebreak that
    resolves a conflict. The Family-F signals are absent by construction.
    """
    return sorted(survivors,
                  key=lambda r: (AUTH_RANK.get(r.authority, 0), r.rank),
                  reverse=True)[0]


def out(status, trace, reason=None, conclusion=None, audit=False,
        represented_reason=False, defeated=None):
    return {"status": status, "trace": trace, "reason": reason, "conclusion": conclusion,
            "audit": audit, "represented_reason": represented_reason,
            "defeated": defeated or []}
