#!/usr/bin/env node
'use strict';
/*
 * impl_c — independent implementation of ganymede5 defeat semantics.
 * Written from SEMANTICS.md + CORPUS_FORMAT.md only.
 *
 * Representation choice: the defeat graph is a bitword adjacency matrix.
 * Argument i is bit (1n<<BigInt(i)) of a BigInt mask. `attack[a]` is the mask
 * of arguments that a actively defeats; `attackedBy[t]` its transpose. The
 * grounded operator is then a pure bitwise algebra:
 *     attacked(S)  = OR_{a in S} attack[a]      (parallel, order-free)
 *     step(S)      = Theta & ~attacked(S)
 * This is not a fixpoint loop over set membership; it is a mask contraction,
 * so oscillation detection is exact bitmask equality rather than a heuristic.
 * Cycle membership is recovered independently by Tarjan SCC on the transpose
 * matrix, so a CONTESTED/SEMANTIC report can name the cycle (SS4.2) without
 * relying on the oscillation trace.
 *
 * Basis dispatch is an exhaustive match with NO guessing default: any basis
 * string not listed in CORPUS_FORMAT.md is a rejected relation (fail closed).
 */

const fs = require('fs');
const path = require('path');

const CORPUS = process.argv[2];
const OUT = process.argv[3];

const raw = JSON.parse(fs.readFileSync(CORPUS, 'utf8'));
const CONTRADICTS = raw.contradicts || {};
const AUTHORITY_RANK = raw.authority_rank || {};

/* ---------------------------------------------------------------- helpers */

const bit = (i) => (1n << BigInt(i));

function popcount(m) {
  let n = 0;
  while (m) { if (m & 1n) n++; m >>= 1n; }
  return n;
}
function bits(m) {
  const out = [];
  for (let i = 0; i < 64; i++) if ((m >> BigInt(i)) & 1n) out.push(i);
  return out;
}
function has(m, i) { return ((m >> BigInt(i)) & 1n) === 1n; }

/* ------------------------------------------------- SS5 corpus validity ---- */
/* Runs FIRST, before triggering, before precedence, before iteration. */

function checkValidity(c) {
  const rules = c.rules || [];
  const defects = [];

  // F5_NON_CONTRADICTION: two rules share an id.
  const idCount = new Map();
  for (const r of rules) idCount.set(r.id, (idCount.get(r.id) || 0) + 1);
  for (const [id, n] of idCount) if (n > 1) defects.push('F5_NON_CONTRADICTION:' + id);

  // F1_GENERALITY: a defeat relation names a rule that does not exist.
  for (const d of (c.defeats || [])) {
    if (!idCount.has(d.defeater)) defects.push('F1_GENERALITY:defeater=' + d.defeater);
    if (!idCount.has(d.defeated)) defects.push('F1_GENERALITY:defeated=' + d.defeated);
  }

  // F2_PROMULGATION: an unpromulgated rule is not in force.
  for (const r of rules) if (r.promulgated !== true) defects.push('F2_PROMULGATION:' + r.id);

  // F3_NON_RETROACTIVITY: retroactive AND carrying an effective_from.
  for (const r of rules)
    if (r.retroactive === true && r.effective_from !== null && r.effective_from !== undefined)
      defects.push('F3_NON_RETROACTIVITY:' + r.id);

  // F7_CONSTANCY: effective_from >= effective_to (empty validity interval).
  for (const r of rules) {
    const f = r.effective_from, t = r.effective_to;
    if (f !== null && f !== undefined && t !== null && t !== undefined && f >= t)
      defects.push('F7_CONSTANCY:' + r.id);
  }
  return defects;
}

/* ------------------------------------------------------- SS4.4 self-defeat */
/* a defeats a. A corpus defect, not an unresolved question. Reported before
 * grounding (it is structural and decidable without argumentation).        */

function checkSelfDefeat(c) {
  const ids = new Set((c.rules || []).map(r => r.id));
  for (const d of (c.defeats || []))
    if (d.defeater === d.defeated && ids.has(d.defeater)) return d.defeater;
  return null;
}

/* ------------------------------------------------------------- triggering */

function triggered(c) {
  const state = new Set((c.state || []).map(String));
  const at = (c.at === null || c.at === undefined) ? null : c.at;
  const idx = [];
  (c.rules || []).forEach((r, i) => {
    if (!state.has(String(r.condition))) return;
    const f = (r.effective_from === null || r.effective_from === undefined) ? null : r.effective_from;
    const t = (r.effective_to === null || r.effective_to === undefined) ? null : r.effective_to;
    // Dates gate triggers separately from precedence (SS4.6).
    if (at !== null && f !== null && !(at >= f)) return;
    if (at !== null && t !== null && !(at < t)) return;
    idx.push(i);
  });
  return idx;
}

/* --------------------------------------------------- SS4.6 basis dispatch */
/* Exhaustive. Absent operand => UNSATISFIED. No default branch, no guessing. */

const KNOWN_BASES = new Set([
  'explicit_lex_posterior',
  'explicit_constitutional_supremacy',
  'explicit_authority_precedence',
  'explicit_rank_precedence',
  'explicit_chain_succession',
  'explicit_exception',
]);

function basisSatisfied(basis, defeater, defeated) {
  switch (basis) {
    case 'explicit_chain_succession':
    case 'explicit_exception':
      // Stated in the corpus, nothing to verify.
      return { ok: true, why: basis };

    case 'explicit_lex_posterior': {
      // defeater.effective_from > defeated.effective_from
      const a = norm(defeater.effective_from), b = norm(defeated.effective_from);
      if (a === null || b === null) return { ok: false, why: 'ABSENT_OPERAND' }; // fail closed
      return { ok: a > b, why: `${a}>${b}` };
    }

    case 'explicit_constitutional_supremacy':
    case 'explicit_authority_precedence': {
      const a = rankOf(defeater), b = rankOf(defeated);
      if (a === null || b === null) return { ok: false, why: 'ABSENT_OPERAND' };
      return { ok: a > b, why: `${a}>${b}` };
    }

    case 'explicit_rank_precedence': {
      const a = norm(defeater.rank), b = norm(defeated.rank);
      if (a === null || b === null) return { ok: false, why: 'ABSENT_OPERAND' };
      return { ok: a > b, why: `${a}>${b}` };
    }

    default:
      // Unrecognized basis string: NOT a warrant. Rejected, fail closed.
      return { ok: false, why: 'UNRECOGNIZED_BASIS', rejected: true };
  }
}
function norm(v) { return (v === null || v === undefined) ? null : v; }
function rankOf(r) {
  const a = r.authority;
  if (a === null || a === undefined) return null;           // absent authority -> unsatisfied
  if (!Object.prototype.hasOwnProperty.call(AUTHORITY_RANK, a)) return null;
  return AUTHORITY_RANK[a];
}

/* ---------------------------------------------- active defeat construction */

function buildGraph(c, trig) {
  const n = c.rules.length;
  const attack = new Array(n).fill(0n);    // attack[a] = mask of targets
  const attackedBy = new Array(n).fill(0n); // transpose
  const inTheta = new Array(n).fill(false);
  for (const i of trig) inTheta[i] = true;

  const thetaMask = trig.reduce((m, i) => m | bit(i), 0n);

  const relations = [];
  for (const d of (c.defeats || [])) {
    const ai = c.rules.findIndex(r => r.id === d.defeater);
    const ti = c.rules.findIndex(r => r.id === d.defeated);
    if (ai < 0 || ti < 0) continue;                       // F1 already reported -> INVALID
    if (d.enabled !== true) { relations.push({ d, active: false, why: 'DISABLED' }); continue; }
    if (!KNOWN_BASES.has(d.basis)) { relations.push({ d, active: false, why: 'UNRECOGNIZED_BASIS' }); continue; }
    if (!inTheta[ai] || !inTheta[ti]) { relations.push({ d, active: false, why: 'OUT_OF_THETA' }); continue; }
    const v = basisSatisfied(d.basis, c.rules[ai], c.rules[ti]);
    if (!v.ok) { relations.push({ d, active: false, why: v.why }); continue; }
    attack[ai] |= bit(ti);
    attackedBy[ti] |= bit(ai);
    relations.push({ d, active: true, why: v.why });
  }
  return { attack, attackedBy, thetaMask, relations };
}

/* ------------------------------------------------------------ SS3 iterate */

function ground(g, idOf) {
  const { attack, thetaMask } = g;
  const bound = 2 * popcount(thetaMask) + 2;      // SS4.5
  const trace = [];
  let S = thetaMask;
  let n = 0;
  trace.push({ n, S: bits(S).map(idOf) });
  for (n = 1; n <= bound; n++) {
    // attacked(S) = OR_{a in S} attack[a]  -- bitwise parallel contraction
    let attacked = 0n;
    for (const a of bits(S)) attacked |= attack[a];
    const next = thetaMask & ~attacked;         // computed over ALL of Theta
    trace.push({ n, S: bits(next).map(idOf) });
    if (next === S) return { converged: true, S, steps: n, trace };
    S = next;
  }
  return { converged: false, S, steps: n, trace, bound };
}

/* ------------------------------------------- Tarjan SCC on attackedBy ------ */
/* Independent cycle membership recovery for SS4.2 trace reporting.        */

function cycleMembers(g, trig) {
  const { attackedBy } = g;
  const idx = new Map();
  const low = new Map();
  const on = new Set();
  const stack = [];
  const sccs = [];
  let counter = 0;

  const strong = (v) => {
    idx.set(v, counter); low.set(v, counter); counter++;
    stack.push(v); on.add(v);
    for (const w of bits(attackedBy[v])) {
      if (!idx.has(w)) { strong(w); low.set(v, Math.min(low.get(v), low.get(w))); }
      else if (on.has(w)) low.set(v, Math.min(low.get(v), idx.get(w)));
    }
    if (low.get(v) === idx.get(v)) {
      const comp = [];
      let w;
      do { w = stack.pop(); on.delete(w); comp.push(w); } while (w !== v);
      sccs.push(comp);
    }
  };
  for (const i of trig) if (!idx.has(i)) strong(i);
  // A cycle between DISTINCT rules is an SCC of size > 1.
  // Self-loops (a defeats a) are SS4.4 corpus defects, already reported.
  return sccs.filter(comp => comp.length > 1);
}

/* ------------------------------------------------------------- SS5a atoms */

function contradicts(a, b) {
  return Object.prototype.hasOwnProperty.call(CONTRADICTS, a) && CONTRADICTS[a] === b;
}

function atomAnalysis(c, survivors) {
  const atoms = [];
  for (const i of survivors) {
    const a = c.rules[i].conclusion;
    if (!atoms.includes(a)) atoms.push(a);
  }
  // 5a.3 contradictory survivors with no represented relation separating them
  for (let i = 0; i < survivors.length; i++)
    for (let j = i + 1; j < survivors.length; j++) {
      const a = c.rules[survivors[i]].conclusion, b = c.rules[survivors[j]].conclusion;
      if (contradicts(a, b) || contradicts(b, a)) return { atoms, contradiction: true };
    }
  return { atoms, contradiction: false };
}

/* ------------------------------------------------------------ SS4.8 reason */
/* Provenance claim: true only if >=1 enabled, basis-satisfying declared
 * relation did the work AND every rule excluded from the grounded set was
 * excluded by such a relation. Never an engine-generated explanation.      */

function representedReason(g, trig, survivors, idOf) {
  const activeRels = g.relations.filter(r => r.active);
  if (activeRels.length === 0) return false;
  const surviving = new Set(survivors);
  // Every rule dropped from Theta must have been dropped by an active relation
  // whose defeater was itself attacked in the iteration that dropped it --
  // the spec does not require the defeater to survive, but it does require
  // the exclusion to rest on a declared, enabled, basis-satisfying relation.
  // Verify directly: each dropped rule is a target of some active relation.
  const targets = new Set();
  for (const r of activeRels) targets.add(r.d.defeated);
  for (const i of trig) if (!surviving.has(i) && !targets.has(idOf(i))) return false;
  return true;
}

/* ------------------------------------------------------------- main solve */

function solve(c) {
  const idOf = (i) => c.rules[i].id;

  const base = (status, conclusion, uncertainty, accepted, defeated, represented_reason, extra) => ({
    id: c.id, status, conclusion, uncertainty,
    accepted, defeated, represented_reason,
    trace: (extra && extra.trace) || [],
  });

  // -- SS5 validity, first ----------------------------------------------
  const defects = checkValidity(c);
  if (defects.length) return base('INVALID', null, 'CORPUS', [], [], false, { trace: [{ defects }] });

  // -- SS4.4 self-defeat -------------------------------------------------
  const selfDef = checkSelfDefeat(c);
  if (selfDef) return base('INVALID', null, 'CORPUS', [], [], false, { trace: [{ self_defeat: selfDef }] });

  // -- REFUSED: requires_construct outside the expressible operation set --
  for (const r of (c.rules || []))
    if (r.requires_construct !== null && r.requires_construct !== undefined)
      return base('REFUSED', null, 'NONE', [], [], false, { trace: [{ requires_construct: r.requires_construct }] });

  // -- triggering --------------------------------------------------------
  const trig = triggered(c);
  if (trig.length === 0)
    return base('NONFINDING', null, 'NONE', [], [], false, { trace: [{ theta: [] }] });

  // -- active defeats (bitword graph) ------------------------------------
  const g = buildGraph(c, trig);
  g.trace_pre = g.relations.map(r => ({
    defeater: r.d.defeater, defeated: r.d.defeated, basis: r.d.basis,
    active: r.active, why: r.why,
  }));

  // -- SS3 grounded iteration --------------------------------------------
  const gr = ground(g, idOf);
  const trace = g.trace_pre.concat(gr.trace);

  if (!gr.converged) {
    // SS4.2 / SS4.5: no stable fixpoint. Name the cycle members.
    const cyc = cycleMembers(g, trig).map(comp => comp.map(idOf).sort());
    return base('CONTESTED', null, 'SEMANTIC', [], trig.map(idOf), false,
      { trace: trace.concat([{ cycle_members: cyc, bound: gr.bound, steps: gr.steps }]) });
  }

  const survivors = bits(gr.S);
  const accepted = survivors.map(idOf);
  const inSurv = new Set(survivors);
  const defeated = trig.filter(i => !inSurv.has(i)).map(idOf);

  if (survivors.length === 0) {
    // every triggered rule was defeated
    return base('DEFEATED', null, 'NONE', [], defeated, false, { trace });
  }

  const { atoms, contradiction } = atomAnalysis(c, survivors);

  if (contradiction) {
    // SS5a.3: contradictory conclusions, no represented relation separates them
    return base('CONTESTED', null, 'CORPUS', accepted, defeated,
      representedReason(g, trig, survivors, idOf),
      { trace: trace.concat([{ note: '5a.3 contradictory survivors', atoms }]) });
  }

  const rr = representedReason(g, trig, survivors, idOf);
  if (atoms.length >= 2) {
    // SS5a.2: grounded and determinate, no unique proposition. NOT contested.
    return base('DECIDED', null, 'NONE', accepted, defeated, rr,
      { trace: trace.concat([{ note: '5a.2 multiple distinct surviving atoms', atoms }]) });
  }
  return base('DECIDED', atoms[0] ?? null, 'NONE', accepted, defeated, rr,
    { trace: trace.concat([{ atoms }]) });
}

const results = raw.cases.map(solve);
fs.writeFileSync(OUT, JSON.stringify(results, null, 2));
process.stderr.write(`wrote ${results.length} results to ${OUT}\n`);