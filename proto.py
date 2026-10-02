#!/usr/bin/env python3
"""
Ganymede5 prototype — Experiment 0.

One question: can a refusal-only executable specification and a defeasible
reasoning layer be made to *necessarily* diverge on a case, such that the
divergence is visible in a trace and cannot be explained away as a gain in
decision rate?

Five cases. Three execution regimes. No LLM, no network, no compiler.

REGIMES
  refusal        Hotting/Schuth discipline. The operation set contains no
                 precedence operator. Anything the restricted format cannot
                 determinately resolve -> REFUSED, or a non-decisive AUDIT mark.
  refusal+prec   Same discipline, but a human translator has *pre-encoded* the
                 conflict as a deterministic if-then branch. This is what
                 "resolving the conflict at authoring time" actually buys.
  defeasible     ASPIC+-lite. Strict rules, explicit attack rules, an explicit
                 precedence relation. Defeat is a relation, not a condition.

OUTCOMES
  DECIDED DEFEATED REFUSED CONTESTED NONFINDING INVALID AUDIT
"""
import json
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Set

# ---------------------------------------------------------------- vocabulary

DECIDED = "DECIDED"
DEFEATED = "DEFEATED"
REFUSED = "REFUSED"
CONTESTED = "CONTESTED"
NONFINDING = "NONFINDING"
INVALID = "INVALID"
AUDIT = "AUDIT"

# Atom vocabulary Sigma. Deliberately artificial and legally structural.
# Two conflicting rules are both triggered by X and assert Y / NOT-Y.
X, Y, NOT_Y = "X", "Y", "NOT-Y"
CONTRADICTS = {Y: NOT_Y, NOT_Y: Y}


@dataclass(frozen=True)
class Rule:
    id: str
    source: str          # statute_01, regulation_07 ...
    authority: str       # legislature, agency ...
    cites: str           # provenance pin: regulation_07 §14
    condition: str
    conclusion: str
    # Constructs outside the executable operation set. A rule naming one of
    # these cannot be run and must be refused or marked.
    requires_construct: Optional[str] = None
    # Adjudicative priority, used ONLY by the defeasible regime, and only
    # through an explicit precedence relation. Never as a tiebreak heuristic.
    priority: int = 0
    # A procedural tag, for invariant checking. Not a rule about content.
    promulgated: bool = True
    retroactive: bool = False
    # A heuristic attractiveness signal deliberately made AVAILABLE to the
    # engine and forbidden as a tiebreak. Used by the case-4 probe.
    specificity: int = 0


@dataclass(frozen=True)
class Defeat:
    """An explicit, represented reason why one rule does not apply."""
    defeated: str
    defeater: str
    basis: str            # explicit_authority_precedence | lex_posterior | none
    provenance: str       # regulation_07 §14
    enabled: bool = True  # case 2 removes this


@dataclass
class Corpus:
    name: str
    state: Set[str]
    rules: List[Rule] = field(default_factory=list)
    defeats: List[Defeat] = field(default_factory=list)
    # Procedural invariants, checked independently of any regime.
    def priority_of(self, r: Rule) -> int:
        return r.priority


# ------------------------------------------------------------------ the cases

def corpus_c1() -> Corpus:
    """DIVERGENCE. A and B both triggered by X, and A has a real defeater over B.

    The defeater direction matters. `explicit_authority_precedence` means the
    legislature outranks the agency, so the statute defeats the regulation. A
    corpus asserting the reverse is not a defeasible corpus; it is incoherent,
    and a correct engine must reject it.
    """
    return Corpus(
        name="c1_divergence",
        state={X},
        rules=[
            Rule("A", "statute_01", "legislature", "statute_01 §1", X, Y, priority=2),
            Rule("B", "regulation_07", "agency", "regulation_07 §14", X, NOT_Y,
                 priority=1),
        ],
        defeats=[Defeat("B", "A", "explicit_authority_precedence",
                        "statute_01 §1", enabled=True)],
    )


def corpus_c2() -> Corpus:
    """DEFEATER REMOVED. Same conflict, no represented reason to prefer either."""
    c = corpus_c1()
    c.name = "c2_no_defeater"
    c.defeats = [Defeat("B", "A", "explicit_authority_precedence",
                        "statute_01 §1", enabled=False)]
    return c


def corpus_c3() -> Corpus:
    """UNEXPRESSIBLE. B needs a construct outside the operation set."""
    c = corpus_c1()
    c.name = "c3_unexpressible"
    c.rules[1] = Rule("B", "regulation_07", "agency", "regulation_07 §14", X, NOT_Y,
                      requires_construct="ROUND", priority=1)
    return c


def corpus_c4() -> Corpus:
    """THE PROBE. Two conflicting rules. B looks better on a heuristic and has
    no represented defeat relation. Any engine returning DECIDED here has not
    reasoned; it has invented an interpretation."""
    return Corpus(
        name="c4_attractive_wrong",
        state={X},
        rules=[
            Rule("A", "statute_01", "legislature", "statute_01 §1", X, Y,
                 priority=2, specificity=1),
            Rule("B", "memo_03", "agency", "memo_03 §2", X, NOT_Y,
                 priority=1, specificity=99),   # very specific, no authority
        ],
        defeats=[],
    )


def corpus_c5() -> Corpus:
    """PROCEDURAL VIOLATION. A retroactive, unpromulgated rule. Not a normative
    conflict at all — this is INVALID, and no regime may call it CONTESTED."""
    return Corpus(
        name="c5_procedural",
        state={X},
        rules=[
            Rule("A", "statute_01", "legislature", "statute_01 §1", X, Y, priority=2),
            Rule("B", "decree_09", "agency", "decree_09 §1", X, NOT_Y,
                 priority=1, promulgated=False, retroactive=True),
        ],
        defeats=[Defeat("B", "A", "explicit_authority_precedence",
                        "decree_09 §1", enabled=True)],
    )


# ------------------------------------------------------------- rule activation

def triggered(c: Corpus) -> List[Rule]:
    return [r for r in c.rules if r.condition in c.state]


def check_invariants(c: Corpus) -> List[str]:
    """Procedural invariants, checked before and independently of any regime.
    These are validity conditions on the corpus, not judgements about content.
    Fuller numbering per the 1964 edition; #4-#6 renumbered consistently."""
    violations = []
    for r in c.rules:
        if not r.promulgated:
            violations.append("F2_PROMULGATION: %s is unpromulgated (%s)" % (r.id, r.source))
        if r.retroactive:
            violations.append("F3_NON_RETROACTIVITY: %s operates retroactively (%s)"
                              % (r.id, r.source))
    return violations


# ------------------------------------------------------------------- regime 1

def run_refusal(c: Corpus, encoded_precedence: bool = False) -> dict:
    """Hotting/Schuth discipline.

    The operation set has no precedence operator unless a translator pre-encoded
    one. An unexpressible construct halts execution. A conflict that the format
    cannot legitimately resolve is REFUSED, or marked in a non-decisive audit.
    """
    trace = []

    blocked = [r for r in c.rules if r.requires_construct]
    if blocked:
        for r in blocked:
            trace.append(("annotation", r.id, "requires_construct=%s" % r.requires_construct))
        return outcome(REFUSED, trace, AUDIT,
                       reason="operation set cannot express %s" %
                              blocked[0].requires_construct)

    live = triggered(c)
    conclusions = {r.conclusion: r for r in live}
    conflict = [c1 for c1 in conclusions if c1 in CONTRADICTS and
                CONTRADICTS[c1] in conclusions]
    if conflict and not encoded_precedence:
        return outcome(REFUSED, trace, None,
                       reason="unresolved normative conflict in the operation set")
    if conflict and encoded_precedence:
        # A translator resolved it. The result is correct but the trace records
        # no reason, because there is none in the corpus. This is the whole point.
        winner = max(live, key=lambda r: r.priority).conclusion
        trace.append(("translator_encoded_precedence",
                      "no defeat relation exists in the corpus", winner))
        return outcome(DECIDED, trace, None, conclusion=winner)
    if not live:
        return outcome(NONFINDING, trace, None, reason="no rule triggered on state")
    winner = live[0].conclusion
    return outcome(DECIDED, trace, None, conclusion=winner)


# ------------------------------------------------------------------- regime 3

def run_defeasible(c: Corpus) -> dict:
    """ASPIC+-lite. Defeat is a relation. Precedence is explicit or absent.

    Hard rule: `specificity` is never read. There is no tiebreak. If two
    arguments survive and contradict, the result is CONTESTED, full stop.
    """
    trace = []
    violations = check_invariants(c)
    if violations:
        trace.append(("invariant_violation", "; ".join(violations)))
        return outcome(INVALID, trace, None, reason=violations[0])

    blocked = [r for r in c.rules if r.requires_construct]
    if blocked:
        r = blocked[0]
        trace.append(("annotation", r.id, "requires_construct=%s" % r.requires_construct))
        return outcome(REFUSED, trace, AUDIT,
                       reason="operation set cannot express %s" % r.requires_construct)

    live = {r.id: r for r in triggered(c)}
    conclusions = {r.conclusion: r for r in live.values()}

    # Attack: is any triggered rule contradicted by another triggered rule?
    conflicts = [a for a in conclusions
                 if a in CONTRADICTS and CONTRADICTS[a] in conclusions]

    # Defeat: an *enabled* and *represented* relation only.
    defeated: Dict[str, Defeat] = {}
    for d in c.defeats:
        if not d.enabled:
            trace.append(("defeat_disabled", d.defeated, d.defeater, d.basis))
            continue
        if d.defeated in live and d.defeater in live:
            defeated[d.defeated] = d
            trace.append(("defeat", d.defeated, d.defeater, d.basis, d.provenance))
            # authority precedence must actually hold for the basis to apply
            hi, lo = live[d.defeater], live[d.defeated]
            if not (hi.priority > lo.priority):
                trace.append(("defeat_rejected", "precedence does not hold"))
                del defeated[d.defeated]

    survivors = [r for r in live.values() if r.id not in defeated]
    surviving_conclusions = {r.conclusion for r in survivors}

    if conflicts:
        a = conflicts[0]
        b = CONTRADICTS[a]
        if a in surviving_conclusions and b in surviving_conclusions:
            for r in live.values():
                trace.append(("argument", r.id, r.source, r.authority,
                              r.cites, r.conclusion))
            return outcome(CONTESTED, trace, None,
                           reason="both arguments survive; no represented defeat relation")
        winner = sorted(survivors, key=lambda r: r.priority, reverse=True)[0]
        trace.append(("result", winner.id, winner.conclusion,
                      "defeated: " + ", ".join(sorted(defeated))))
        return outcome(DECIDED, trace, None, conclusion=winner.conclusion,
                       defeated=[d.defeated for d in defeated.values()])

    if not survivors:
        return outcome(DEFEATED, trace, None,
                       reason="every triggered rule was defeated")
    winner = sorted(survivors, key=lambda r: r.priority, reverse=True)[0]
    return outcome(DECIDED, trace, None, conclusion=winner.conclusion)


# ---------------------------------------------------------------------- report

def outcome(status, trace, audit=None, reason=None, conclusion=None, defeated=None):
    return {"status": status, "audit": audit, "reason": reason,
            "conclusion": conclusion, "defeated": defeated or [], "trace": trace}


def show(c: Corpus, res: dict) -> None:
    head = "  status: %s" % res["status"]
    if res["conclusion"]:
        head += "   conclusion: %s" % res["conclusion"]
    if res["defeated"]:
        head += "   defeated: %s" % ",".join(res["defeated"])
    if res["audit"]:
        head += "   [audit-mode: never decides a case]"
    if res["reason"]:
        head += "\n  reason: %s" % res["reason"]
    print(head)
    for t in res["trace"]:
        print("    | " + "  ".join(str(x) for x in t))


def main():
    cases = [
        ("C1  divergence (A vs B, statute defeats regulation)", corpus_c1()),
        ("C2  defeater removed (no represented reason to prefer)", corpus_c2()),
        ("C3  unexpressible construct (ROUND)", corpus_c3()),
        ("C4  PROBE — attractive but unrepresented defeater", corpus_c4()),
        ("C5  procedural violation (unpromulgated + retroactive)", corpus_c5()),
    ]
    hard_fail = False

    for title, c in cases:
        print("\n" + "=" * 78)
        print(title)
        print("  state: %s" % sorted(c.state))
        for r in c.rules:
            note = "  [needs %s]" % r.requires_construct if r.requires_construct else ""
            print("  rule %-2s %s/%s  %s : %s -> %s"
                  % (r.id, r.source, r.authority, r.condition, r.conclusion, note))
        for d in c.defeats:
            print("  defeat %s <- %s  basis=%s  %s  enabled=%s"
                  % (d.defeated, d.defeater, d.basis, d.provenance, d.enabled))
        print("-" * 78)

        for label, res in (
            ("refusal        (Hotting/Schuth)", run_refusal(c, False)),
            ("refusal+prec   (translator pre-encoded)", run_refusal(c, True)),
            ("defeasible     (explicit defeat relation)", run_defeasible(c)),
        ):
            print("  %s" % label)
            show(c, res)

        # The probe assertion.
        if c.name == "c4_attractive_wrong":
            d = run_defeasible(c)
            ok = d["status"] == CONTESTED
            hard_fail = hard_fail or not ok
            print("-" * 78)
            print("  PROBE RESULT: %s" % ("PASS — refused to invent an interpretation"
                                           if ok else "HARD FAIL — returned %s" % d["status"]))

    print("\n" + "=" * 78)
    print("HARD FAIL: %s" % ("yes" if hard_fail else "none — the probe did not break the engine"))
    return 1 if hard_fail else 0


if __name__ == "__main__":
    raise SystemExit(main())
