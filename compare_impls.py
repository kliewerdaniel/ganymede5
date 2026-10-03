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

from corpus import run_defeasible  # noqa: E402
from families import CASES as F  # noqa: E402
from family_g import G as FG  # noqa: E402
from family_h import H as FH  # noqa: E402


# --------------------------------------------------------------------------
# MEASUREMENT FAILURE, made fatal.
#
# This harness once reported "agree on every case where the spec is decisive"
# while comparing 36 of the corpus's 41 cases. It dropped Family H -- the five
# adversarial cases that exist specifically to test the newest specification
# text. A harness that silently excludes cases cannot detect disagreement in
# them, and it will report success while doing so.
#
# The omission was not random, which is what makes it dangerous: it excluded
# precisely the cases most likely to disagree. Coverage that is inferred from
# a successful run is not coverage.
#
# So the case-id invariant is enforced, not documented:
#
#     corpus_export_ids == A_ids == B_ids == compared_ids
#
# EXPECTED ids are read from corpus_export.json -- the neutral interchange file,
# which is written by the exporter and read by every independent implementation.
# They are deliberately NOT derived from A's case list. If the expected set
# came from A, then any case A failed to register would be invisible to the
# check, and the instrument would inherit the very blind spot it exists to
# detect.
# --------------------------------------------------------------------------


def expected_ids():
    """The corpus's own case ids, from the neutral export."""
    export = ROOT / "corpus_export.json"
    if not export.exists():
        sys.exit("FATAL: corpus_export.json is missing. The expected case set "
                 "must come from the neutral corpus, never from implementation A.")
    data = json.loads(export.read_text())
    cases = data["cases"] if isinstance(data, dict) else data
    ids = [c.get("id") or c.get("cid") for c in cases]
    dupes = {i for i in ids if ids.count(i) > 1}
    if dupes:
        sys.exit("FATAL: duplicate case ids in corpus_export.json: %s"
                 % ", ".join(sorted(dupes)))
    return ids


def coverage_report(expected, a_ids, b_ids, compared):
    """Fatal unless all four sets are identical. Returns nothing on success."""
    problems = []
    for label, ids in (("A", a_ids), ("B", b_ids), ("compared", compared)):
        short = sorted(set(expected) - set(ids))
        extra = sorted(set(ids) - set(expected))
        if short:
            problems.append("  %-8s is MISSING %d case(s): %s"
                            % (label, len(short), ", ".join(short)))
        if extra:
            problems.append("  %-8s has %d case(s) NOT IN THE CORPUS: %s"
                            % (label, len(extra), ", ".join(extra)))
    if problems:
        print("=" * 72)
        print("FATAL -- MEASUREMENT FAILURE. Refusing to report agreement.")
        print("=" * 72)
        print("\n".join(problems))
        print("\nThe case sets are not identical. Any agreement figure computed")
        print("over a subset is not evidence about the whole corpus: a harness")
        print("that drops cases cannot find disagreement in the ones it dropped.")
        print("\nNothing below is reported, because nothing below would mean anything.")
        return False
    print("coverage: %d/%d cases -- corpus, A, B, and compared set are identical"
          % (len(expected), len(expected)))
    return True


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

    exp = expected_ids()
    b_ids = [x.get("id") or x.get("cid") for x in b]
    if not coverage_report(exp, sorted(a), sorted(x for x in b_ids if x),
                           sorted(set(exp) & set(a) & set(x for x in b_ids if x))):
        return 3

    agree, violations, spec, reporting, missing = compare(a, b)

    n = len(a)
    print("=" * 72)
    print("IMPLEMENTATION A vs INDEPENDENT IMPLEMENTATION B")
    print("=" * 72)
    print("cases in corpus: %d" % len(exp))
    print("cases compared:   %d" % n)
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
        print("VERDICT: A and B agree on all %d corpus cases. This is agreement," % n)
        print("         over the whole corpus, between two implementations.")
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
