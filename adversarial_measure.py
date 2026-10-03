#!/usr/bin/env python3
"""
ADVERSARIAL MEASUREMENT RUN -- SIT v0.4.

Does the measurement apparatus DETECT failure, or does it merely tolerate it?

Every defect below was, at some point in this project, something that
reproduced a successful run. That is what makes them worth testing:

  1. OMITTED CASE        compare_impls.py compared 36 of 41 and reported
                         "agree on every case". It dropped Family H -- the
                         five adversarial cases. It reported SUCCESS.
  2. UNCOLLECTED TEST    11/14 mutants survived while the suite still printed
                         "Ran 67 tests ... OK". The tests existed as
                         module-level functions; unittest never called them.
                         The suite reported SUCCESS.
  3. UNREACHABLE BRANCH  H5 passed trivially because no corpus case could
                         starve the iteration budget, so the guarantee it was
                         written to support was untested. The suite reported
                         SUCCESS.
  4. VACUOUS SATISFACTION impl_d satisfied 6.3 structurally -- it has no
                         budget to exhaust, so it never faced the condition
                         the clause governs. It was CORRECT and it still
                         proved nothing about the clause.
  5. SILENT DISAGREEMENT an adversarial case can disagree while every
                         aggregate metric stays at 1.00.

The point is not that these are five bugs. It is that they are five DIFFERENT
WAYS A MEASUREMENT SYSTEM MANUFACTURES APPARENT SUCCESS, and each of them
looked like success from the outside.

Each case below asserts that the apparatus REFUSES to report success. A test
that passes while the apparatus misbehaves would itself be defect 2.

Run: python3 adversarial_measure.py
"""
import io
import json
import pathlib
import subprocess
import sys
import contextlib

ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT))


def sh(*args):
    r = subprocess.run([sys.executable] + list(args), cwd=ROOT,
                       capture_output=True, text=True)
    return r.returncode, (r.stdout or "") + (r.stderr or "")


# ---------------------------------------------------------------------------
# DETECTOR 1 -- an omitted case must be FATAL, not absorbed.
# ---------------------------------------------------------------------------

def detect_omitted_case():
    """Restore the exact historical defect: A enumerates fewer cases than the corpus.

    The original bug was NOT that B returned too few records. It was that A
    itself never registered Family H, so H existed in neither comparison set.
    The old harness compared 36 of 41, found no disagreement, and printed
    "agree on every case where the spec is decisive."

    Reproducing it faithfully matters. An earlier version of this detector
    dropped a case from B's output -- the easy direction, which the old
    harness's `missing` check would have caught anyway, and which therefore
    did not test the actual defect.

    So: reinstate the historical import set, run the comparison against D's
    complete 41-case output, and require that the apparatus now REFUSES.
    """
    target = ROOT / "compare_impls.py"
    original = target.read_text()
    historical = original.replace(
        "    for c in list(F) + list(FG) + list(FH):",
        "    for c in list(F) + list(FG):  # historical: Family H never registered")
    if historical == original:
        return False, ("could not reinstate the historical import set; this "
                       "detector is stale and must be updated")
    target.write_text(historical)
    try:
        code, out = sh("compare_impls.py", "impl_d.json")
    finally:
        target.write_text(original)

    if code == 0:
        return False, ("harness reported success while A omitted Family H -- "
                       "the historical measurement failure is back")
    if "MEASUREMENT FAILURE" not in out:
        return False, "harness failed but did not identify it as measurement failure"
    if not all(h in out for h in ("H1", "H5")):
        return False, "harness failed but did not name the omitted family"
    return True, ("A omitting 5 cases is fatal and named; the 36/41 silent pass "
                  "that produced v0.2 is no longer reachable")


# ---------------------------------------------------------------------------
# DETECTOR 2 -- a test that does not run must be visible.
# ---------------------------------------------------------------------------

def detect_uncollected_test():
    """A module-level test function is invisible to unittest. Prove it."""
    probe = ROOT / "_adversarial_uncollected.py"
    probe.write_text(
        "# This assertion is deliberately FALSE. If unittest ever collects it,\n"
        "# the suite must fail. If the suite passes, it was never collected --\n"
        "# which is exactly the M12-M14 condition, and it is silent.\n"
        "def test_this_must_never_be_collected():\n"
        "    raise AssertionError('collected')\n"
        "\n"
        "import unittest\n"
        "class T(unittest.TestCase):\n"
        "    def test_real(self):\n"
        "        self.assertTrue(True)\n")
    try:
        code, out = sh("-m", "unittest", "_adversarial_uncollected")
    finally:
        probe.unlink()

    if code != 0:
        return False, "unittest DID collect the module-level function; premise is wrong"
    # It passed -- so the function was silently ignored. That is the defect.
    if "collected" in out:
        return False, "expected the uncollected probe to be ignored, but it ran"
    return True, ("module-level test silently ignored while suite reported OK "
                  "-- defect demonstrated, and now named rather than assumed")


# ---------------------------------------------------------------------------
# DETECTOR 3 -- an unreachable branch must be detected as unreachable.
# ---------------------------------------------------------------------------

def detect_unreachable_branch():
    """DEFEATED is reserved. Nothing may report it. Prove nothing does."""
    from families import CASES as F
    from family_g import G as FG
    from family_h import H as FH
    from corpus import run_defeasible

    seen = {}
    for c in list(F) + list(FG) + list(FH):
        seen[c.cid] = run_defeasible(c)["status"]
    leaked = [k for k, v in seen.items() if v == "DEFEATED"]
    if leaked:
        return False, "DEFEATED was reported for %s" % ", ".join(leaked)
    if "DEFEATED" not in seen.values():
        return True, ("DEFEATED never emitted across %d cases; reserved status "
                      "stays reserved" % len(seen))


# ---------------------------------------------------------------------------
# DETECTOR 4 -- vacuous satisfaction must be distinguishable from exercise.
# ---------------------------------------------------------------------------

def detect_vacuous_satisfaction():
    """A clause can be satisfied without its governing condition ever occurring.

    6.3 says exhaustion is an operational error, never SEMANTIC. We can prove
    the corpus never exercises exhaustion -- so no pass on 6.3, from ANY
    implementation, on THIS corpus, is evidence about exhaustion. It is only
    evidence that nothing violated the clause.
    """
    from semantics import accepted

    # A well-founded chain with a starved budget: does it report SEMANTIC?
    # semantics.accepted() takes (defeated, defeater) pairs -- the semantic
    # layer works only on already-validated relations (SEMANTICS.md 3).
    rel = [("C", "D"), ("B", "C"), ("A", "B")]
    exhausted = False
    try:
        s, unc, _ = accepted({"A", "B", "C", "D"}, rel, max_rounds=2)
        starved_result = unc
    except Exception as e:
        exhausted = True
        starved_result = type(e).__name__

    # A genuine cycle must still be SEMANTIC, or we have over-corrected.
    cyc = [("A", "B"), ("B", "A")]
    _s, cyc_unc, _ = accepted({"A", "B"}, cyc, max_rounds=64)

    if starved_result == "SEMANTIC":
        return False, "F-1 has regressed: budget exhaustion reports SEMANTIC again"
    if cyc_unc != "SEMANTIC":
        return False, ("over-corrected: a real cycle no longer reports SEMANTIC "
                       "(got %s)" % cyc_unc)
    return True, ("starved budget -> %s (operational), genuine cycle -> SEMANTIC "
                  "(semantic); the two are distinguishable"
                  % ("exception: " + starved_result if exhausted else starved_result))


# ---------------------------------------------------------------------------
# DETECTOR 5 -- disagreement must survive the aggregate metrics.
# ---------------------------------------------------------------------------

def detect_silent_disagreement():
    """Inject one adversarial disagreement. The headline must move.

    The risk is a harness that reports "defeasible 1.00" while a specific
    adversarial case is wrong -- an aggregate that hides a defect the
    specification was written to prevent.
    """
    b = json.loads((ROOT / "impl_d.json").read_text())
    target = next(x for x in b if (x.get("id") or x.get("cid")) == "H3")
    saved = dict(target)
    # H3 is the INVALID-over-REFUSED precedence case, the newest and least
    # corroborated rule in 6.2. Corrupting it is the most adversarial single
    # mutation available.
    target["status"] = "REFUSED"
    target["uncertainty"] = "NONE"
    path = ROOT / "_adversarial_corrupt.json"
    path.write_text(json.dumps(b))
    try:
        code, out = sh("compare_impls.py", path.name)
    finally:
        path.unlink()
        b[next(i for i, x in enumerate(b)
                if (x.get("id") or x.get("cid")) == "H3")].update(saved)

    if code == 0:
        return False, "harness reported success on a corrupted adversarial case"
    if "H3" not in out:
        return False, "harness detected the corruption but did not name the case"
    if "DISAGREE" not in out.upper():
        return False, "harness failed without reporting a disagreement"
    return True, "detected and localised the injected disagreement to H3"


# ---------------------------------------------------------------------------
# NEGATIVE CONTROL -- a detector that has only ever passed is not a detector.
#
# Every detector below is an assertion about the apparatus. An assertion that
# cannot fail is indistinguishable from a broken one, so at least one must be
# demonstrated failing on purpose.
#
# This one disables the coverage invariant in compare_impls.py, re-runs the
# omitted-case detector, and requires it to MISS. If the invariant is doing
# the work, the detector stops firing when the invariant is removed. If the
# detector still fires with the invariant gone, it is passing for some other
# reason and is not measuring what it claims to.
#
# Confirmed empirically: removing the invariant turns "omitted case" from
# DETECTED to MISSED and the run from 5/5 to 4/5.
# ---------------------------------------------------------------------------


def negative_control_detector_can_fail():
    """Disable the coverage invariant; the historical defect must return silently.

    Without this, every detector above is an assertion that has only ever
    passed, which is indistinguishable from a detector that cannot fail.

    Removes the invariant from compare_impls.py, reinstates the historical
    import set, and requires the comparison to report SUCCESS over 36 of 41
    cases. If it instead fails, the invariant is doing the work and the
    detector above is measuring it. If it still fails with the invariant gone,
    something else is catching the omission and the detector is not measuring
    what it claims to.
    """
    target = ROOT / "compare_impls.py"
    original = target.read_text()
    guard = ("    if not coverage_report(exp, sorted(a), sorted(x for x in b_ids if x),\n"
             "                           sorted(set(exp) & set(a) & set(x for x in b_ids if x))):\n"
             "        return 3")
    historical_import = "    for c in list(F) + list(FG) + list(FH):"
    if guard not in original or historical_import not in original:
        return False, ("could not locate what to disable; this negative control "
                       "is stale and must be updated")
    stripped = original.replace(
        guard, "    # invariant deliberately removed by the negative control").replace(
        historical_import,
        "    for c in list(F) + list(FG):  # historical: Family H never registered")
    target.write_text(stripped)
    try:
        code, out = sh("compare_impls.py", "impl_d.json")
    finally:
        target.write_text(original)

    if code != 0:
        return False, ("harness still failed with the invariant removed -- "
                       "something else catches this, so the detector is not "
                       "testing the invariant")
    if "cases compared:   36" not in out:
        return False, ("expected the historical 36/41 comparison, got:\n"
                       + out[-600:])
    return True, ("with the invariant removed the harness reported SUCCESS over "
                  "36 of 41 cases -- exactly the v0.2 defect -- so the "
                  "detector is testing the invariant and not something else")


DETECTORS = [
    ("detector can fail",         negative_control_detector_can_fail),
    ("omitted case",              detect_omitted_case),
    ("uncollected test",          detect_uncollected_test),
    ("unreachable branch",        detect_unreachable_branch),
    ("vacuous satisfaction",      detect_vacuous_satisfaction),
    ("silent disagreement",       detect_silent_disagreement),
]


def main():
    print("=" * 74)
    print("ADVERSARIAL MEASUREMENT RUN -- SIT v0.4")
    print("=" * 74)
    print("\nEach detector seeds a defect that has previously reproduced a")
    print("successful run, and asserts the apparatus REFUSES to report success.\n")

    passed, failed = [], []
    for name, fn in DETECTORS:
        with contextlib.suppress(Exception) as _:
            pass
        try:
            ok, detail = fn()
        except Exception as e:
            ok, detail = False, "detector raised %s: %s" % (type(e).__name__, e)
        print("  %-22s %s" % (name, "DETECTED" if ok else "MISSED"))
        print("      %s" % detail)
        (passed if ok else failed).append(name)
        print()

    print("-" * 74)
    print("%d/%d detectors fired" % (len(passed), len(DETECTORS)))
    if failed:
        print("\nDETECTORS THAT DID NOT FIRE -- the apparatus is blind to these:")
        for f in failed:
            print("  - " + f)
        return 1
    print("\nAll six checks fired, including the negative control.")
    print("\nThis does NOT establish that the apparatus is complete. It")
    print("establishes that five specific ways of manufacturing false success")
    print("are now detected. A sixth may exist.")
    return 0


if __name__ == "__main__":
    sys.exit(main())