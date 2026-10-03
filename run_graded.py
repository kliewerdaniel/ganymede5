#!/usr/bin/env python3
"""
Experiment 0c — grade every case against the INDEPENDENT manifest.

Regimes, renamed for what they actually are:

  refusal_only   lower-bound behaviour: decline what the format cannot settle
  authoring_time resolve the ambiguity BEFORE execution, as a human
                 translator pre-encodes it into a deterministic branch
  defeasible     represent the ambiguity and resolve it DURING execution

The comparison is therefore not dumb vs smart. It is:

    resolve before execution   vs   resolve during execution

with refusal_only supplying the lower bound.

Grading is against expected.MANIFEST, which imports no engine code. A regime
cannot change its grade by changing its behaviour.
"""
import sys
from collections import defaultdict

from corpus import run_refusal, run_defeasible, DECIDED
from families import CASES
from family_g import G as CASES_G
from family_h import H as CASES_H
from expected import MANIFEST

ALL = list(CASES) + list(CASES_G) + list(CASES_H)

REGIMES = [
    ("refusal_only", lambda c: run_refusal(c, False)),
    ("authoring_time", lambda c: run_refusal(c, True)),
    ("defeasible", run_defeasible),
]


def grade(rows, cases):
    """Compare each regime against the manifest."""
    out = {}
    for name, fn in REGIMES:
        r = [fn(c) for c in cases]
        correct = sum(1 for c, x in zip(cases, r)
                      if x["status"] == MANIFEST[c.cid]["status"])
        out[name] = {"rows": r, "correct": correct, "n": len(cases),
                     "accuracy": correct / float(len(cases))}
    return out


def main():
    cases = ALL
    g = grade(cases, cases)

    print("=" * 100)
    print("EXPERIMENT 0c — %d cases, graded against the independent manifest" % len(cases))
    print("=" * 100)
    print()
    print("%-4s %-40s %-9s %-14s %-14s %-11s" % (
        "id", "case", "expected", "refusal_only", "authoring_time", "defeasible"))
    print("-" * 100)

    disagreements = defaultdict(list)
    for c in cases:
        exp = MANIFEST[c.cid]["status"]
        cells = []
        for name, _ in REGIMES:
            st = g[name]["rows"][cases.index(c)]["status"]
            mark = "" if st == exp else "  <<"
            cells.append(st + mark)
            if st != exp:
                disagreements[name].append(c.cid)
        print("%-4s %-40s %-9s %-14s %-14s %-11s" % (
            c.cid, c.note[:40], exp, *cells))

    print()
    print("=" * 100)
    print("GRADED AGAINST THE INDEPENDENT MANIFEST")
    print("-" * 100)
    print("%-18s %-12s %-30s" % ("regime", "accuracy", "disagreements"))
    for name, _ in REGIMES:
        d = disagreements[name]
        ds = ", ".join(d) if d else "none"
        print("%-18s %-12.2f %-30s" % (name, g[name]["accuracy"], ds[:30]))

    print()
    print("=" * 100)
    print("THE TWO AXES, RESTRICTED TO GENUINELY CONTESTED CASES")
    print("-" * 100)
    contested = [c for c in cases
                 if MANIFEST[c.cid]["conflict"] and MANIFEST[c.cid]["representable"]
                 and MANIFEST[c.cid]["status"] != "INVALID"]
    print("contested cases: %d of %d" % (len(contested), len(cases)))
    print()
    print("%-18s %-14s %-16s %-22s" % (
        "regime", "decisiveness", "justification", "on contested"))
    for name, _ in REGIMES:
        rows = [g[name]["rows"][cases.index(c)] for c in contested]
        dec = [r for r in rows if r["status"] == DECIDED]
        just = [r for r in dec if r["represented_reason"]]
        j = (len(just) / float(len(dec))) if dec else float("nan")
        js = "n/a" if j != j else "%.2f (%d/%d)" % (j, len(just), len(dec))
        print("%-18s %-14.2f %-16s %-22d" % (
            name, len(dec) / float(len(rows)), js, len(rows)))

    print()
    print("=" * 100)
    print("CONTEST PRESERVATION — cases the manifest says must stay open")
    print("-" * 100)
    must_open = [c for c in cases if MANIFEST[c.cid]["status"] == "CONTESTED"]
    print("cases that MUST remain contested: %d" % len(must_open))
    for name, _ in REGIMES:
        closed = [c.cid for c in must_open
                  if g[name]["rows"][cases.index(c)]["status"] == DECIDED]
        rate = len(closed) / float(len(must_open))
        print("  %-18s closed %-2d of %-2d   (%.0f%% suppressed)"
              % (name, len(closed), len(must_open), 100 * rate))
    print()
    print("Suppression rate is the sharpest single number here. A regime that")
    print("closes contested cases has not decided them; it has decided them")
    print("without warrant.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
