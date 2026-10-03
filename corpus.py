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
import semantics as sem
from semantics import SEMANTIC, CORPUS, NONE
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
        # SEMANTICS.md 2.1: a defective corpus is INVALID/CORPUS. NONE would
        # assert both that the semantics decided and that the corpus is sound.
        return out(INVALID, trace, reason=violations[0], represented_reason=False,
                   uncertainty=CORPUS)

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

    # Defeat is a FIXPOINT, not a pass. SEMANTICS.md is normative; the basis
    # check below is the CORPUS layer and the grounded iteration in semantics.py
    # is the SEMANTIC layer. The single-pass application this replaces was
    # correct only for depth-1 relations, which is all of families A-F.
    valid = []
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
            # SEMANTICS.md 4.6: an absent operand is NOT -inf. The corpus did
            # not state a temporal position, so it did not assert this
            # relation, and an unasserted relation is not a warrant. Fail
            # closed. Substituting -inf here silently converts "later rule
            # wins" into "rule with a stated date wins", which is a different
            # and unstated rule.
            if lo.effective_from is None or hi.effective_from is None:
                trace.append(("defeat_rejected", d.defeated, d.defeater,
                              d.basis, "absent effective_from: temporal "
                                       "position unstated (SEMANTICS.md 4.6)"))
                continue
            lo_from = lo.effective_from
            hi_from = hi.effective_from
            holds = hi_from > lo_from
        elif d.basis == "explicit_constitutional_supremacy":
            holds = AUTH_RANK.get(hi.authority, 0) > AUTH_RANK.get(lo.authority, 0)
        elif d.basis == "explicit_authority_precedence":
            # Authority precedence means authority order. A numeric rank may
            # NOT substitute for it, or a memo given rank=9 would defeat a
            # statute — which is the heuristic failure this project exists to
            # detect, wearing a formalism's clothes.
            holds = AUTH_RANK.get(hi.authority, 0) > AUTH_RANK.get(lo.authority, 0)
        elif d.basis in ("explicit_chain_succession", "explicit_exception"):
            # Succession and exception are stated IN the corpus: the corpus
            # says rule C succeeds rule B. There is no independent precedence
            # to verify, so the relation is valid as stated.
            #
            # This branch did not exist before. `chain_succession` fell through
            # to the rank branch below, where C (rank 7) beat B (rank 2) and
            # the G4 defeat cycle was DESTROYED BY RANK -- the precise
            # heuristic failure G4 was constructed to detect, hiding inside the
            # formalism. The cycle only reappeared once the basis was honoured.
            holds = True
        elif d.basis == "explicit_rank_precedence":
            # An explicit rank IS the stated basis here. This is the only branch
            # permitted to read `rank`.
            holds = hi.rank > lo.rank
        else:
            # An unrecognised basis is not a warrant. Fail closed.
            trace.append(("defeat_rejected", d.defeated, d.defeater,
                          "unrecognised basis %s" % d.basis))
            continue
        if not holds:
            trace.append(("defeat_rejected", d.defeated, d.defeater,
                          "precedence does not hold for basis %s" % d.basis))
            continue
        valid.append(d)
        trace.append(("defeat_validated", d.defeated, d.defeater, d.basis,
                      d.provenance))

    # ---- SEMANTIC layer. Acceptance is a grounded fixpoint over the relations
    # that survived basis validation. No tiebreak is available here: the
    # spec removed tiebreaks rather than trusting the code to decline them.
    uncertainty = NONE
    try:
        accepted, uncertainty, _hist = sem.accepted(
            {r.id for r in live.values()},
            [(d.defeater, d.defeated) for d in valid])
    except sem.SelfDefeat as e:
        trace.append(("self_defeat", str(e)))
        return out(INVALID, trace,
                   reason="a rule defeats itself; the corpus is malformed",
                   represented_reason=False, uncertainty=CORPUS)

    if uncertainty == SEMANTIC:
        cyc = sem.cycle_members([(d.defeater, d.defeated) for d in valid])
        for ring in cyc:
            trace.append(("defeat_cycle", "->".join(ring)))
        return out(CONTESTED, trace,
                   reason="defeat structure is not well-founded; no unique "
                          "argument set exists, and Ganymede5 does not resolve "
                          "cyclic defeat by default",
                   represented_reason=False, uncertainty=SEMANTIC)

    # The grounded argument set is an OUTPUT, not an internal. SEMANTICS.md
    # section 4 fixes it, and CORPUS_FORMAT.md requires it, so it must be
    # reportable. It was previously recoverable only by reading the trace,
    # which made the A/B comparison structurally weaker than the spec requires.
    survivors = [r for r in live.values() if r.id in accepted]
    # A validated defeat that the fixpoint did not apply is not discarded
    # silently: it is the trace record that shows the reversal.
    defeated = {d.defeated: d for d in valid if d.defeated not in accepted}
    for tgt in sorted(defeated):
        trace.append(("defeat_effective", tgt, defeated[tgt].defeater,
                      defeated[tgt].basis, defeated[tgt].provenance))
    s_concl = {r.conclusion for r in survivors}

    if conflict:
        a = conflict[0]
        b = CONTRADICTS[a]
        if a in s_concl and b in s_concl:
            for r in live.values():
                trace.append(("argument", r.id, r.source, r.authority, r.cites, r.conclusion))
            return out(CONTESTED, trace,
                       reason="both arguments survive; no represented defeat relation",
                       represented_reason=False,
                       # The contested survivors must be reportable WITH the
                       # defeats that were applied. Returning without this made
                       # a correct case look like nothing had been decided --
                       # the record of what WAS defeated is part of the answer
                       # to why the contest remains open.
                       defeated=sorted(defeated),
                       accepted_ids=sorted(accepted))
        # Only ONE side of the contradiction survived, so there is no contest
        # (5a.3) -- but there may still be several surviving atoms, which 5a.2
        # makes a null conclusion. Fall through rather than picking one here:
        # G3 reaches here with survivors {B,C} asserting A1 and NOT-Y.
        pass

    # SEMANTICS.md 5a.2: a grounded extension whose survivors assert two or
    # more distinct atoms yields NO unique proposition-level conclusion. This
    # is DECIDED, not CONTESTED: the extension is unique and determinate, and
    # nothing is contested. 5a.4 forbids resolving it by declaration order --
    # indexing a list to choose what to believe is an undeclared preference.
    # Implementation B refused to guess here; it was right to.
    if len(s_concl) > 1:
        trace.append(("result", None, None,
                      "distinct surviving conclusions: " + ",".join(sorted(s_concl))))
        for _r in sorted(survivors, key=lambda x: x.id):
            trace.append(("surviving_conclusion", _r.id, _r.conclusion,
                          _r.source))
        return out(DECIDED, trace, conclusion=None,
                   reason="grounded extension is determinate but yields no "
                          "unique proposition-level conclusion",
                   represented_reason=bool(defeated),
                   defeated=sorted(defeated),
                   accepted_ids=sorted(accepted))
        # Report EVERY surviving atom to the reader (5a.4): showing the full set
        # does not require preferring one member of it.

    if not survivors:
        return out(DEFEATED, trace, reason="every triggered rule was defeated",
                   represented_reason=True, defeated=sorted(defeated),
                   accepted_ids=sorted(accepted))
    win = _pick(survivors)
    # Name the representative even when nothing was contested. On an
    # uncontested case the choice is immaterial to the outcome, which is
    # exactly why it must still be recorded: otherwise a preference-driven
    # engine is indistinguishable from a correct one.
    trace.append(("result", win.id, win.conclusion,
                  "defeated: " + ",".join(sorted(defeated))))
    return out(DECIDED, trace, conclusion=win.conclusion,
               represented_reason=bool(defeated), defeated=sorted(defeated),
               accepted_ids=sorted(accepted))


def _pick(survivors):
    """Name ONE surviving rule as the representative. This is NOT a tiebreak.

    SEMANTICS.md 4.1 and 4.6: no ordering by authority, rank, recency, or
    saliency may decide anything. Sorting by AUTH_RANK here looked harmless
    because this function is only reached when survivors do not contradict --
    so the choice cannot change the conclusion. It is still an authority
    preference, and it made the representative in the trace an artifact of
    authority rather than of declaration order.

    The mutation run made this concrete: a case where two survivors assert the
    SAME atom (G7) is invisible at the conclusion level, so the only way to
    detect a preference-driven engine is to inspect the trace. Keeping the
    sort would have meant the spec's prohibition was true only where it was
    convenient.

    So: deterministic and inert. First in declaration order.
    """
    return sorted(survivors, key=lambda r: r.id)[0]


def out(status, trace, reason=None, conclusion=None, audit=False,
        represented_reason=False, defeated=None, uncertainty=None,
        accepted_ids=None):
    return {"status": status, "trace": trace, "reason": reason, "conclusion": conclusion,
            "audit": audit, "represented_reason": represented_reason,
            "defeated": defeated or [],
            # IMPLEMENTATION uncertainty is not emittable here by design. Only
            # the independent grader may assert it.
            "uncertainty": uncertainty or (CORPUS if status == CONTESTED else NONE),
            "accepted": accepted_ids or []}
