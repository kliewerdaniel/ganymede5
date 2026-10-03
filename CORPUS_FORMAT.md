# Corpus interchange format — the neutral contract

Implementation B receives exactly: `SEMANTICS.md`, **this file**, and the
JSON corpora. It receives no Ganymede5 source, no manifest, no expected
outputs, and no statement of which cases are contested.

This format is deliberately **not** Python. It is the only interface between
the corpus and any implementation, so neither side can leak structure into the
other through a shared dataclass.

## JSON shape

```json
{
  "id": "G4",
  "family": "G",
  "state": ["X"],
  "at": 10,
  "rules": [
    {
      "id": "B",
      "source": "r_b",
      "authority": "agency",
      "cites": "r_b §1",
      "condition": "X",
      "conclusion": "Y",
      "rank": 2,
      "promulgated": true,
      "retroactive": false,
      "effective_from": null,
      "effective_to": null,
      "requires_construct": null,
      "specificity": 0,
      "recency": 0,
      "length": 0,
      "confidence": 0.0,
      "order_index": 0,
      "text_similarity": 0.0
    }
  ],
  "defeats": [
    {
      "defeated": "B",
      "defeater": "C",
      "basis": "explicit_chain_succession",
      "provenance": "r_c §1",
      "enabled": true
    }
  ]
}
```

### Field meanings

`id`, `family`, `note` — labels. `note` is prose and carries no semantics.

`state` — the set of atoms true in the world. `at` — the evaluation time, or
`null` for no temporal evaluation.

A rule is **triggered** iff all of:
- `condition ∈ state`
- if `effective_from` is not null and `at` is not null, `at ≥ effective_from`
- if `effective_to` is not null and `at` is not null, `at < effective_to`

`authority` is one of `constitution`, `legislature`, `agency`, `memo`.

`conclusion` is an atom. Two atoms contradict iff they appear in
`contradicts`, which the corpus supplies as a per-file sibling key:

```json
{"contradicts": {"Y": "NOT-Y", "NOT-Y": "Y"}, "cases": [ ... ]}
```

An atom that is not a key in `contradicts` contradicts nothing.

A `Defeat` names `defeated` and `defeater`. **Order is significant and is not
reversible** — this has been a live source of confusion.

### Bases

`basis` is exactly one of:

| basis | holds when |
|---|---|
| `explicit_lex_posterior` | defeater's `effective_from` > defeated's |
| `explicit_constitutional_supremacy` | `authority_rank[defeater] > authority_rank[defeated]` |
| `explicit_authority_precedence` | same test as above |
| `explicit_rank_precedence` | `defeater.rank > defeated.rank` |
| `explicit_chain_succession` | **always** — stated in the corpus, nothing to verify |
| `explicit_exception` | **always** — stated in the corpus, nothing to verify |

`authority_rank` is supplied alongside `contradicts` so that no implementation
hard-codes a hierarchy it was not given:

```json
{"authority_rank": {"constitution": 4, "legislature": 3, "agency": 2, "memo": 1}}
```

Any other basis string is **not a warrant** and the relation is rejected.

> The `explicit_chain_succession → rank` defect was this file's reason for
> existing: a basis with no case fell through to a numeric heuristic and
> silently changed the meaning of the formalism. If your implementation
> dispatches on bases with a default branch, that defect is in it.

### Semantically inert fields

`rank`, `specificity`, `recency`, `length`, `confidence`, `order_index`,
`text_similarity` are carried so adversarial cases *contain* them. They carry no
semantic force except in `explicit_rank_precedence`, and they must never
resolve a contest. They are present in the data, which is exactly why they need
the prohibition.

`requires_construct` — a construct name outside the expressible operation set,
or `null`. Its presence makes the case unrunnable (`REFUSED`).

## Required output

```json
{
  "id": "G4",
  "status": "CONTESTED",
  "conclusion": null,
  "defeated": [],
  "uncertainty": "SEMANTIC",
  "represented_reason": false,
  "accepted": [],
  "trace": []
}
```

`status` ∈ `DECIDED | DEFEATED | CONTESTED | REFUSED | NONFINDING | INVALID`.
`uncertainty` ∈ `SEMANTIC | CORPUS | NONE`.

`accepted` — the grounded argument set, as rule ids. Required, so acceptance is
directly comparable rather than inferred from the status. `IMPLEMENTATION`
uncertainty must never be emitted.

`trace` is implementation-defined. Do **not** compare traces between
implementations; they are evidence for debugging, not a contract.

## What counts as agreement

- `status` — must match exactly.
- `conclusion` — must match exactly, including both being null.
- `accepted` — must match as sets.
- `uncertainty` — must match where the status is `CONTESTED` or `INVALID`.
- `defeated` — compared as sets, reported as a difference, **not** treated as a
  disagreement. It is a reporting detail, and `SEMANTICS.md` does not fix it.
- `trace` — never compared.

A difference in `defeated` with matching `status`, `conclusion`, `accepted`, and
`uncertainty` is a **reporting difference**, and is reported separately from
disagreement. If it turns out to track the spec's silence, that is a finding
about the spec.
