#!/usr/bin/env python3
"""
Export the corpora to the neutral JSON format defined in CORPUS_FORMAT.md.

This is the ONLY thing implementation B is allowed to read. It exists to stop
structure leaking across the boundary: B parses JSON, so it cannot import a
Rule dataclass, call `triggered()`, or inherit any of the control flow.

It deliberately does NOT export:
  * any expected status, label, or manifest field
  * which cases are designed to be contested
  * any trace or ordering hint

Those are the labels under test. Emitting them would hand B the answer.
"""
import json
import pathlib
import sys

ROOT = pathlib.Path(__file__).parent
sys.path.insert(0, str(ROOT))

from corpus import Case, CONTRADICTS, AUTH_RANK  # noqa: E402


def rule_json(r):
    return {
        "id": r.id, "source": r.source, "authority": r.authority,
        "cites": r.cites, "condition": r.condition, "conclusion": r.conclusion,
        "rank": r.rank, "promulgated": r.promulgated,
        "retroactive": r.retroactive,
        "effective_from": r.effective_from, "effective_to": r.effective_to,
        "requires_construct": r.requires_construct,
        "specificity": r.specificity, "recency": r.recency, "length": r.length,
        "confidence": r.confidence, "order_index": r.order_index,
        "text_similarity": r.text_similarity,
    }


def case_json(c: Case):
    return {
        "id": c.cid, "family": c.family,
        "state": sorted(c.state), "at": c.at,
        "rules": [rule_json(r) for r in c.rules],
        "defeats": [{"defeated": d.defeated, "defeater": d.defeater,
                     "basis": d.basis, "provenance": d.provenance,
                     "enabled": d.enabled} for d in list(c.defeats or [])],
    }


def export(cases, path):
    doc = {
        "contradicts": dict(CONTRADICTS),
        "authority_rank": dict(AUTH_RANK),
        "cases": [case_json(c) for c in cases],
    }
    path.write_text(json.dumps(doc, indent=1, ensure_ascii=False) + "\n")
    return len(cases)


def main():
    from families import CASES as F
    from family_g import G
    out = ROOT / "corpus_export.json"
    n = export(list(F) + list(G), out)
    print("wrote %s (%d cases)" % (out.name, n))

    # Sanity: the export must not contain anything label-shaped.
    blob = out.read_text()
    for banned in ("expected", "refusal_is_correct", "expect_defeasible",
                   "manifest", "CONTESTED", "DECIDED"):
        assert banned not in blob, "export leaks %r" % banned
    print("export contains no labels, expected outputs, or statuses")
    return 0


if __name__ == "__main__":
    sys.exit(main())
