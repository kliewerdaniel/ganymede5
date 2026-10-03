# impl_c — independent implementation of the ganymede5 defeat semantics

Written from `SEMANTICS.md` + `CORPUS_FORMAT.md` only. No Ganymede5 source,
no expected outputs, no other implementation was read.

## Files

- `engine.js` — the engine (Node.js, no dependencies).
- `selftest.js` — asserts the spec's own worked examples and checks the basis
  dispatch is complete.

## Run

```
node engine.js ../corpus_export.json ../impl_c.json
node selftest.js
```

## Defeat-graph representation

The defeat graph is a **bitword adjacency matrix**. Argument *i* is bit
`1n << BigInt(i)` of a BigInt; `attack[a]` is the mask of arguments *a* actively
defeats, `attackedBy[t]` its transpose. The grounded operator of §3 is then a
bitwise contraction:

```
attacked(S) = OR_{a in S} attack[a]
step(S)     = Theta & ~attacked(S)
```

This is deliberately not a set-membership fixpoint loop. Consequences:

1. `step` is computed over all of Θ unconditionally — the §3 requirement that
   "S(n+1) is computed over all of Θ, **not** restricted to S(n)" is structural
   here, not something that has to be remembered at each call site.
2. Stability is exact BigInt equality, so non-convergence (§4.5) is a fact about
   the operator rather than a heuristic.
3. Cycle membership for the §4.2 trace is recovered *independently* by Tarjan
   SCC over `attackedBy`, so a contest is named from the graph, not inferred
   from the oscillation trace.

## Basis dispatch

`basisSatisfied` is an exhaustive `switch` over the six bases in
CORPUS_FORMAT.md. There is no guessing default: `default:` returns
`{ok: false, why: 'UNRECOGNIZED_BASIS'}` — a rejected relation. §4.6 is applied
uniformly: an absent operand (`effective_from`, `authority`, `rank`, or an
authority missing from `authority_rank`) makes the basis **unsatisfied**. An
unverifiable basis is an unsatisfied basis.

§4.7: `rank` is read only inside `explicit_rank_precedence`. No inert field
(`specificity`, `recency`, `confidence`, `order_index`, `text_similarity`,
`length`) and no declaration order is consulted anywhere. §5a.4 is respected
structurally — the atom set is built as a *set* and a multi-atom extension goes
straight to `conclusion: null`; there is no index into a rule list that could be
mistaken for a selection rule.

## Pipeline order

§5 validity → §4.4 self-defeat → `requires_construct` (REFUSED) → triggering →
active-defeat construction → §3 iteration → §5a proposition selection.

Validity runs first, as §5 requires: a defective corpus has no Θ to ground.
Self-defeat is checked in the same structural phase because §4.4 calls it a
corpus defect, decidable without argumentation, and explicitly "a different
state from CONTESTED".

## represented_reason (§4.8)

Computed mechanically, never asserted: true iff at least one *active* relation
exists (declared, `enabled: true`, basis in the table, basis satisfied, both
endpoints in Θ) **and** every rule dropped from Θ is the target of some active
relation. If there is no active relation at all it is `false` — a decisive
outcome without a warrant, which §4.8 calls the most important thing measured.