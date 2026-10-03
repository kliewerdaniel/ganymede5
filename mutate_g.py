#!/usr/bin/env python3
"""
Family G mutation testing.

A green suite is evidence only if the tests can go red. This injects defects
that the ratified semantics in SEMANTICS.md is supposed to make IMPOSSIBLE to
ship, and requires each one to be caught by at least one test.

Every mutant here is a violation of a ratified commitment, not a random bug:

  M1  single-pass defeat          breaks SEMANTICS.md 3 (defeat is a fixpoint)
  M2  chain_succession -> rank    the defect that made G4 report DECIDED
  M3  resolve cycles by rank      breaks 4.2 (no cyclic resolution)
  M4  prefer constitution         breaks 4.1/4.3 (no preference relation)
  M5  never return CONTESTED      breaks the governing constraint
  M6  accept unsupported basis    breaks the CORPUS layer
  M7  self-defeat silently ignored breaks 4.4
  M8  engine reports IMPLEMENTATION breaks the audit boundary
  M9  drop the reversal from trace breaks the witness property
  M10 drop defeated from CONTESTED the record bug found this round
  M11 tiebreak on rank            breaks 4.6
  M12 pick an atom by declaration order   breaks 5a.4
  M13 INVALID reported as NONE           breaks 2.1
  M14 absent date read as -inf           breaks 4.6
  M15 exhausted budget -> SEMANTIC       breaks 6.3 (F-1)
  M16 oscillation -> NONE, never SEMANTIC  breaks 4.5
  M17 INVALID loses to REFUSED           breaks 6.2 precedence
  M18 nothing-triggered -> DEFEATED      breaks 6.1 reserved status
"""
import re
import subprocess
import sys
import pathlib

ROOT = pathlib.Path(__file__).parent
SUITE = ["test_proto", "test_families", "test_family_g"]


def run_suite():
    r = subprocess.run([sys.executable, "-m", "unittest"] + SUITE,
                       cwd=ROOT, capture_output=True, text=True)
    return r.returncode == 0, r.stderr


# (id, file, description, original, replacement)
MUTANTS = [
    ("M1", "corpus.py",
     "single-pass defeat instead of a fixpoint",
     "        accepted, uncertainty, _hist = sem.accepted(",
     "        _o,_u,_h = sem.accepted("),

    ("M2", "corpus.py",
     "chain succession falls through to the rank branch",
     '        elif d.basis in ("explicit_chain_succession", "explicit_exception"):',
     '        elif False:'),

    ("M3", "semantics.py",
     "cycles are resolved instead of reported",
     "    if not relations:\n        return set(theta), NONE, [set(theta)]",
     "    if not relations:\n        return set(theta), NONE, [set(theta)]\n"
     "    if frozenset(relations) and all(a in {t for a2, t in relations}\n"
     "                                  for a, t in relations):\n"
     "        return set(theta), NONE, [set(theta)]"),

    ("M4", "corpus.py",
     "prefer the higher-authority survivor",
     "    return sorted(survivors, key=lambda r: r.id)[0]",
     "    return sorted(survivors,\n"
     "                  key=lambda r: (AUTH_RANK.get(r.authority, 0), r.rank),\n"
     "                  reverse=True)[0]"),

    ("M5", "corpus.py",
     "never report CONTESTED",
     "    if uncertainty == SEMANTIC:",
     "    if False:"),

    ("M6", "corpus.py",
     "accept a defeat whose basis does not hold",
     "        if not holds:",
     "        if False:"),

    ("M7", "corpus.py",
     "silently ignore a self-defeating rule",
     "    except sem.SelfDefeat as e:",
     "    except _NeverRaised as e:"),

    ("M8", "corpus.py",
     "engine reports IMPLEMENTATION uncertainty",
     "            \"uncertainty\": uncertainty or (CORPUS if status == CONTESTED else NONE),",
     "            \"uncertainty\": \"IMPLEMENTATION\","),

    ("M9", "corpus.py",
     "the reversal is dropped from the trace",
     '        trace.append(("defeat_effective", tgt, defeated[tgt].defeater,\n'
     '                      defeated[tgt].basis, defeated[tgt].provenance))',
     "        pass"),

    ("M10", "corpus.py",
     "CONTESTED omits the defeats that were applied",
     "                       # to why the contest remains open.",
     "                       # to why the contest remains open.\n"
     "                       defeated = {}"),

    ("M12", "corpus.py",
     "pick one atom by declaration order (violates 5a.4)",
     "    if len(s_concl) > 1:",
     "    if False:"),
    ("M13", "corpus.py",
     "report a defective corpus as INVALID/NONE (violates 2.1)",
     "                   represented_reason=False, uncertainty=CORPUS)",
     "                   represented_reason=False, uncertainty=NONE)"),
    ("M14", "corpus.py",
     "treat an absent date as -inf (violates 4.6)",
     "            if lo.effective_from is None or hi.effective_from is None:",
     "            if False:"),
    ("M11", "corpus.py",
     "tiebreak survivors on numeric rank",
     "    return sorted(survivors, key=lambda r: r.id)[0]",
     "    return sorted(survivors, key=lambda r: r.rank, reverse=True)[0]"),
    # --- SIT v0.3: the rules Family H was built to force ---

    ("M15", "semantics.py",
     "exhausted iteration budget reported as SEMANTIC (F-1)",
     "    raise BudgetExhausted(",
     "    return s, SEMANTIC, history\n    _dead = ("),

    ("M16", "semantics.py",
     "oscillation silently stabilised instead of reported",
     "            return s, SEMANTIC, history",
     "            return s, NONE, history"),

    ("M17", "corpus.py",
     "precedence inverted: REFUSED decided before INVALID",
     '    blocked = [r for r in c.rules if r.requires_construct]\n    if blocked:\n        return out(REFUSED, trace, audit=True,\n                    reason="operation set cannot express %s" % blocked[0].requires_construct,\n                    represented_reason=False)',
     "    blocked = []\n    if blocked and False:\n        return out(REFUSED, trace, audit=True,\n                    reason='x', represented_reason=False)"),

    ("M18", "corpus.py",
     "nothing-applicable reported as DEFEATED (a reserved status)",
     '        return out(NONFINDING, trace, reason="no rule triggered on state", represented_reason=False)',
     '        return out(DEFEATED, trace, reason="no rule triggered on state", represented_reason=False)'),
]


def main():
    ok, _ = run_suite()
    print("baseline suite: %s" % ("PASS" if ok else "FAIL"))
    if not ok:
        print("refusing to mutate a red baseline")
        return 1

    killed, survived = [], []
    for mid, fname, desc, orig, repl in MUTANTS:
        path = ROOT / fname
        src = path.read_text()
        if orig not in src:
            print("  %-4s SKIP (anchor not found) %s" % (mid, desc))
            survived.append(mid + " (anchor missing)")
            continue
        path.write_text(src.replace(orig, repl, 1))
        # M7 needs a name that cannot exist for the except clause to be legal.
        if mid == "M7":
            s2 = (ROOT / "corpus.py").read_text().replace(
                "import semantics as sem", "import semantics as sem\nclass _NeverRaised(Exception): pass", 1)
            (ROOT / "corpus.py").write_text(s2)
        passed, err = run_suite()
        path.write_text(src)
        if passed:
            survived.append("%s (%s)" % (mid, desc))
            print("  %-4s SURVIVED  %s" % (mid, desc))
        else:
            killed.append(mid)
            first = [l for l in err.splitlines() if l.startswith(("FAIL:", "ERROR:"))]
            print("  %-4s killed    %s   [%s]" % (mid, desc, first[0][:58] if first else ""))

    print("\n%d/%d mutants killed" % (len(killed), len(MUTANTS)))
    if survived:
        print("SURVIVORS (the suite does not actually enforce these):")
        for s in survived:
            print("  - " + s)
    return 0 if not survived else 1


if __name__ == "__main__":
    sys.exit(main())
