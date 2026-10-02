#!/usr/bin/env python3
"""
Run the six-family corpus through all three regimes and report the two axes.

    decisiveness   fraction of cases returning DECIDED
    justification  of the cases that GENUINELY CONTESTED a conflict, the
                   fraction DECIDED with a represented defeat relation

Justification is measured only where a conflict actually existed. Counting it
over all DECIDED cases would credit a regime for deciding uncontested cases,
where no defeat relation is needed and none should be demanded.

Also reports the count of cases where refusal was CORRECT — because a
regime's decisiveness only means something relative to that.
"""
import sys
from collections import defaultdict

from corpus import run_refusal, run_defeasible, DECIDED
from families import CASES

REGIMES = [
    ("refusal", lambda c: run_refusal(c, False)),
    ("refusal+prec", lambda c: run_refusal(c, True)),
    ("defeasible", run_defeasible),
]


def genuinely_contested(case):
    """True when two triggered rules assert contradictory conclusions, or the
    corpus is procedurally invalid. These are the only cases where DECIDED
    makes an epistemic claim that needs backing."""
    from corpus import CONTRADICTS, check_invariants
    if check_invariants(case):
        return True
    live = case.triggered()
    concl = {r.conclusion for r in live}
    return any(a in CONTRADICTS and CONTRADICTS[a] in concl for a in concl)


def measure(cases):
    table = {}
    contested_idx = [i for i, c in enumerate(cases) if genuinely_contested(c)]
    for name, fn in REGIMES:
        rows = [fn(c) for c in cases]
        decided = [r for r in rows if r["status"] == DECIDED]
        contested_rows = [rows[i] for i in contested_idx]
        contested_decided = [r for r in contested_rows if r["status"] == DECIDED]
        just = [r for r in contested_decided if r["represented_reason"]]
        table[name] = {
            "rows": rows,
            "decisive": len(decided),
            "justified": len(just),
            "n_contested": len(contested_rows),
            "n_contested_decided": len(contested_decided),
            "decisiveness": len(decided) / float(len(rows)),
            "justification": (len(just) / float(len(contested_decided)))
                             if contested_decided else float("nan"),
        }
    return table


def main():
    cases = CASES
    fams = sorted({c.family for c in cases})
    t = measure(cases)

    print("=" * 96)
    print("SIX-FAMILY CORPUS  —  %d cases" % len(cases))
    print("=" * 96)

    hdr = "%-4s %-46s %-11s %-11s %-11s" % ("id", "note", "refusal", "ref+prec", "defeasible")
    print(hdr)
    print("-" * 96)
    for c in cases:
        cells = []
        for name, _ in REGIMES:
            r = [x for x in t[name]["rows"] if True][cases.index(c)]
            cells.append(r["status"])
        print("%-4s %-46s %-11s %-11s %-11s" % (c.cid, c.note[:46], *cells))
        exp = c.expect_defeasible
        d = [x for x in t["defeasible"]["rows"]][cases.index(c)]
        flag = "  " if d["status"] == exp else "!!"
        if flag == "!!":
            print("     %s expected %s, got %s" % (flag, exp, d["status"]))

    print()
    print("=" * 96)
    print("PER-FAMILY (defeasible regime)")
    print("-" * 96)
    print("%-8s %-7s %-40s" % ("family", "n", "statuses"))
    for f in fams:
        sub = [c for c in cases if c.family == f]
        rows = [run_defeasible(c) for c in sub]
        counts = defaultdict(int)
        for r in rows:
            counts[r["status"]] += 1
        print("%-8s %-7d %-40s" % (f, len(sub), dict(counts)))

    print()
    print("=" * 96)
    print("THE TWO AXES")
    print("-" * 96)
    print("%-14s %-13s %-26s %-12s %-12s" % (
        "regime", "decisiveness", "justification (contested only)", "contested", "decided"))
    for name, _ in REGIMES:
        m = t[name]
        j = m["justification"]
        js = "n/a" if j != j else "%.2f  (%d/%d)" % (j, m["justified"], m["n_contested_decided"])
        print("%-14s %-13.2f %-26s %-12d %-12d" % (
            name, m["decisiveness"], js, m["n_contested"], m["n_contested_decided"]))

    correct_refusals = sum(1 for c in cases if c.refusal_is_correct)
    print()
    print("cases where refusal is the CORRECT behaviour: %d/%d (%.0f%%)"
          % (correct_refusals, len(cases), 100.0 * correct_refusals / len(cases)))
    print()
    print("Reading: a regime's decisiveness is only meaningful against that last")
    print("number. Deciding 100%% of cases in a corpus where refusal is correct")
    print("more than half the time is not capability, it is suppression.")

    return 0


if __name__ == "__main__":
    sys.exit(main())
