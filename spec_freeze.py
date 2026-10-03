#!/usr/bin/env python3
"""
Verify the specification freeze.

The rule this enforces:

    Do not modify the specification to make the measurement apparatus pass.

Without a mechanical check, that rule is a sentence in a document, and this
project has already established that documented intentions are not enforcement:
SEMANTICS.md once declared a governing constraint, and the implementation
enforced five invariants the document never mentioned. A rule that cannot fail
is indistinguishable from no rule at all.

So: SPEC-FREEZE.json pins a digest for every normative file. If a pinned file
changes and no semantic decision was recorded here, that is SPECIFICATION
FAILURE wearing the costume of an ordinary edit, and this exits non-zero.

What this does NOT do: it does not judge whether a recorded decision was
justified. That still requires reading the specification. A digest mismatch is
evidence that something moved; only a person can say whether it should have.

Run: python3 spec_freeze.py
"""
import hashlib
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent
FREEZE = ROOT / "SPEC-FREEZE.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()[:16]


def repin():
    """Record the current digests. Only ever run deliberately, after reading
    the drift report and deciding the change was warranted."""
    data = json.loads(FREEZE.read_text())
    old = dict(data.get("pinned", {}))
    data["pinned"] = {n: digest(ROOT / n) for n in sorted(old)}
    FREEZE.write_text(json.dumps(data, indent=2) + "\n")
    print("re-pinned v%s:" % data.get("spec_version"))
    for n, v in data["pinned"].items():
        mark = "" if old.get(n) == v else "   (was %s)" % old.get(n)
        print("  %-22s %s%s" % (n, v, mark))


def main():
    if "--repin" in sys.argv:
        repin()
        return 0
    if not FREEZE.exists():
        sys.exit("FATAL: SPEC-FREEZE.json is missing. The specification is no "
                 "longer pinned, and nothing is holding it still.")

    data = json.loads(FREEZE.read_text())
    pinned = data.get("pinned", {})
    if not pinned:
        sys.exit("FATAL: SPEC-FREEZE.json pins no files.")

    drift = []
    for name, expected in sorted(pinned.items()):
        path = ROOT / name
        if not path.exists():
            drift.append((name, expected, "MISSING"))
            continue
        actual = digest(path)
        if actual != expected:
            drift.append((name, expected, actual))

    print("=" * 72)
    print("SPECIFICATION FREEZE -- v%s" % data.get("spec_version", "?"))
    print("=" * 72)
    for name, expected in sorted(pinned.items()):
        print("  %-22s %s" % (name, expected))
    print()

    if drift:
        print("FATAL -- SPECIFICATION DRIFT. A pinned normative file changed")
        print("without a recorded semantic decision.\n")
        for name, expected, actual in drift:
            print("  %-22s expected %s, found %s" % (name, expected, actual))
        print("\nA specification change is legitimate when a semantic ambiguity")
        print("or a genuine defect warrants it. It is NOT legitimate merely")
        print("because an implementation or a measurement system disagrees.")
        print("\nIf the change is warranted: bump spec_version in")
        print("SPEC-FREEZE.json, add a decision with its rationale and the")
        print("evidence that surfaced it, and re-pin the digests with")
        print("  python3 spec_freeze.py --repin")
        print("\nIf it is not warranted: revert the file. An implementation")
        print("disagreeing with the specification is evidence about the")
        print("implementation.")
        return 1

    print("all pinned files match their recorded digests.")
    print("specification v%s is frozen: %d decisions recorded."
          % (data.get("spec_version"), len(data.get("decisions", []))))
    print("\nFrozen does not mean correct. It means the specification cannot be")
    print("edited without the edit being visible as an edit.")
    return 0


if __name__ == "__main__":
    sys.exit(main())