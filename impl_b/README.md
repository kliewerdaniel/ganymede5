# impl_b — independent implementation of the Ganymede5 defeat semantics

Written from `SEMANTICS.md` + `CORPUS_FORMAT.md` + `corpus_export.json` only.
No Ganymede5 source, manifest, or expected outputs were read.

    cd impl_b && cargo build --release
    ./target/release/impl_b <corpus.json> <out.json>

Defaults to `../corpus_export.json` → `../impl_b.json`.

## Structure

- **Language:** Rust, std only (hand-rolled JSON reader, no dependencies).
- **Defeat graph:** an adjacency matrix of `u64` bitwords, one row per rule
  *object*. The grounded operator `S(n+1) = { r ∈ Θ : r unattacked in S(n) }`
  (§3) becomes a word-parallel OR-reduction of the rows of the members of
  `S(n)`; the next set is `Θ \ attacked`. Cycle structure is obtained
  independently by Warshall transitive closure over the same matrix plus
  mutual-reachability grouping, so "the attack graph has a cycle" (§4.2) and
  "the operator does not stabilise" (§4.5) are separate computations rather
  than the same accident.
- Nodes are rule **objects**, not rule ids, so a repeated id does not silently
  collapse into one argument; defeat entries resolve by id and apply to every
  node carrying it.
- `basis_holds` is a total `match` over the six bases; the unmatched arm
  returns `None` = "not a warrant". No default, no fallback, no numeric
  heuristic. Verified against near-miss spellings (`chain_succession`,
  `EXPLICIT_RANK_PRECEDENCE`, `explicit_`, `""`) — all rejected.
- Precedence of rules: `REFUSED` (requires_construct) → `NONFINDING` (Θ empty)
  → `INVALID` (self-defeat, §4.4) → `CONTESTED/SEMANTIC` (cycle, §4.2)
  → iterate (§3) → `CONTESTED/SEMANTIC` (no fixpoint in bound, §4.5) →
  `DEFEATED` (empty grounded set) → `CONTESTED/CORPUS` (grounded set carries
  contradictory conclusions, §4.1) → `DECIDED`.

## Where the specification is silent (and what I did)

1. **`explicit_lex_posterior` with a `null` date.** The rule reads "defeater's
   `effective_from` > defeated's". The format never says how a missing date
   compares. I read `null` as *no lower bound* = `-∞`, so a dated rule is
   posterior to an undated one. (Cases: E2 — decided on this reading.)
2. **`uncertainty` for `INVALID`.** §4.4 calls self-defeat "a defect in the
   corpus" and CORPUS_FORMAT requires uncertainty to match where the status is
   `CONTESTED` **or `INVALID`**, but §2's table does not say which of the three
   kinds an `INVALID` carries. I emit `CORPUS` (the corpus is what is wrong).
3. **`uncertainty` for statuses other than `CONTESTED`/`INVALID`.** Emitted as
   `NONE`. §2 defines `IMPLEMENTATION` as non-emittable and gives no value for
   decided cases; `NONE` is the only remaining legal token.
4. **`accepted` when there is no stable fixpoint.** Emitted `[]`, because there
   is no grounded argument set to report. The format requires the field but
   does not say what it holds in the non-convergent case.
5. **`conclusion` when the accepted rules agree on nothing and nothing
   contradicts.** G3 accepts `{B, C}` with conclusions `A1` and `NOT-Y` — two
   atoms, neither contradicting the other under `contradicts`. The status is
   determinate (the grounded extension is unique and contradiction-free) but
   there is no single atom to report, so `conclusion` is `null` and the status
   is `DECIDED`. `DECIDED` with a null conclusion is not obviously what §5
   intends; an alternative reading is that a multi-conclusion grounded set is
   itself `CONTESTED`. This is a real fork in the spec.
6. **`promulgated: false`.** The format's triggered-rule definition lists
   condition and the two temporal tests; it says nothing about `promulgated` or
   `retroactive`. I did not read them (E1 keeps `B` in Θ). If promulgation
   gates in-force status, E1's status changes.
7. **`defeated`.** Reported as Θ minus the accepted set, which is the only
   reading the spec supports, and compared as a reporting detail anyway.
8. **`represented_reason`.** True iff every rule excluded from the grounded set
   was excluded by an active, recognised, basis-satisfying, enabled relation.
   The format gives the field no definition at all.
9. **`state`/`condition` matching** is read as exact atom equality; the format
   gives no other option but does not exclude a subset reading.