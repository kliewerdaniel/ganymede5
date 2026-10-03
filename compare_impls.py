#!/usr/bin/env python3
"""
Compare implementation A against implementation B.

This harness is deliberately one-sided: it computes A's answers through the
normal engine and reads B's answers from a JSON file. It has no access to the
manifest and never mentions expected labels, because agreement is being tested,
not correctness.

READING THE RESULTS

Four outcomes, and they mean different things. Keeping them apart is the whole
point of doing this experiment.

  AGREE              the semantics is precise enough to implement twice
  DISAGREE-VIOLATION one side contradicts SEMANTICS.md  -> an implementation
                     defect, and the offending case is the diagnosis
  DISAGREE-SPEC      both are defensible but differ       -> SEMANTICS.md is
                     underspecified at that point, and the case tells us where
  REPORTING          status/conclusion/accepted/uncertainty all match, but the
                     `defeated` list differs. This is the spec's silence, not a
                     disagreement.

`defeated` and `trace` are deliberately excluded from the pass/fail comparison.
A reporting difference is not a semantic difference, and conflating them would
manufacture disagreements that mean nothing.
"""
import json
import pathlib
import subprocess
import sys

ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT))

from corpus import run_defeasible, run_refusal  # noqa: E402
from families import CASES as F  # noqa: E402
from family_g import G as FG  # noqa: E402
from family_h import H as FH  # noqa: E402


def a_answers():
    """Implementation A, through the ordinary engine."""
    out = {}
    for c in list(F) + list(FG) + list(FH):
        r = run_defeasible(c)
        out[c.cid] = {
            "id": c.cid,
            "status": r["status"],
            "conclusion": r["conclusion"],
            "uncertainty": r["uncertainty"],
            "defeated": sorted(r["defeated"]),
            "represented_reason": r["represented_reason"],
            # SEMANTICS.md 4 fixes the argument set, so it is a reported output
            # and one of the four fields the format says must match.
            "accepted": sorted(r["accepted"]),
        }
    return out


def compare(a, b):
    agree, violations, spec, reporting, missing = [], [], [], [], []
    by_id = {x["id"]: x for x in b}

    for cid, av in sorted(a.items()):
        bv = by_id.get(cid)
        if bv is None:
            missing.append(cid)
            continue
        core_a = (av["status"], av["conclusion"], av["uncertainty"],
                  tuple(av["accepted"]))
        core_b = (bv.get("status"), bv.get("conclusion"), bv.get("uncertainty"),
                  tuple(sorted(bv.get("accepted") or [])))
        if core_a == core_b:
            if sorted(av["defeated"]) == sorted(bv.get("defeated") or []):
                agree.append(cid)
            else:
                reporting.append((cid, av["defeated"], sorted(bv.get("defeated") or [])))
        else:
            # Which side is at fault is NOT decidable here. Classify as a
            # potential spec ambiguity and leave attribution to a human reading
            # SEMANTICS.md. Pretending to know would defeat the experiment.
            spec.append((cid, core_a, core_b))
    return agree, violations, spec, reporting, missing


def main():
    bpath = pathlib.Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / "impl_b.json"
    if not bpath.exists():
        print("no B output at %s -- nothing to compare" % bpath.name)
        return 2
    b = json.loads(bpath.read_text())
    a = a_answers()
    agree, violations, spec, reporting, missing = compare(a, b)

    n = len(a)
    print("=" * 72)
    print("IMPLEMENTATION A vs INDEPENDENT IMPLEMENTATION B")
    print("=" * 72)
    print("cases compared: %d" % n)
    print()
    print("  AGREE            %2d" % len(agree))
    print("  DISAGREE         %2d   <- inspect each" % len(spec))
    print("  REPORTING only   %2d   <- spec is silent on `defeated`" % len(reporting))
    if missing:
        print("  MISSING from B   %2d   %s" % (len(missing), ", ".join(missing)))

    if spec:
        print("\n--- DISAGREEMENTS ---")
        for cid, ca, cb in spec:
            print("  %-4s A=%s" % (cid, ca))
            print("       B=%s" % (cb,))
    if reporting:
        print("\n--- REPORTING DIFFERENCES (not disagreements) ---")
        for cid, da, db in reporting:
            print("  %-4s A defeated=%s   B defeated=%s" % (cid, da, db))
    if agree:
        print("\n  agreeing: %s" % ", ".join(agree))

    print("\n" + "-" * 72)
    if not spec and not missing:
        print("VERDICT: A and B agree on every case where the spec is decisive.")
        if reporting:
            print("         Differences are confined to `defeated`, which "
                  "SEMANTICS.md")
            print("         does not fix. That is a finding about the spec, "
                  "not a")
            print("         defect in either implementation.")
    else:
        print("VERDICT: the semantics does not yet determine unique answers.")
        print("         Each disagreement is either an underspecified point in")
        print("         SEMANTICS.md or an implementation defect. Attributing")
        print("         them requires reading the spec, not a script.")
    return 0 if not spec and not missing else 1


if __name__ == "__main__":
    sys.exit(main())
