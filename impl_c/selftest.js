#!/usr/bin/env node
'use strict';
/* Self-test: asserts impl_c reproduces the worked examples the spec itself
 * states, and that the dispatch has no guessing fallback. */

const fs = require('fs');
const path = require('path');
const out = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'impl_c.json'), 'utf8'));
const by = new Map(out.map(r => [r.id, r]));
let fails = 0;
const eq = (label, got, want) => {
  const g = JSON.stringify(got), w = JSON.stringify(want);
  if (g !== w) { console.log('FAIL', label, 'got', g, 'want', w); fails++; }
  else console.log('ok  ', label, g);
};

// SEMANTICS.md SS3 worked chain: D defeats C defeats B defeats A -> Accepted {B,D}.
// G1 is that exact shape. Both survivors assert NOT-Y -> DECIDED NOT-Y.
eq('SS3/G1 accepted == {B,D}', by.get('G1').accepted.sort(), ['B', 'D']);
eq('SS3/G1 conclusion', by.get('G1').conclusion, 'NOT-Y');

// SS4.2 cycle {B,C} -> {} -> {B,C}: CONTESTED / SEMANTIC, cycle named.
eq('SS4.2/G4 status', by.get('G4').status, 'CONTESTED');
eq('SS4.2/G4 uncertainty', by.get('G4').uncertainty, 'SEMANTIC');
eq('SS4.2/G4 cycle named', by.get('G4').trace.slice(-1)[0].cycle_members, [['B', 'C']]);

// SS4.4 self-defeat (A defeats A) -> INVALID, not CONTESTED.
eq('SS4.4/G8 status', by.get('G8').status, 'INVALID');
eq('SS4.4/G8 uncertainty', by.get('G8').uncertainty, 'CORPUS');

// SS5 all five invariants -> INVALID/CORPUS, checked before triggering.
for (const [id, inv] of [['E1', 'F2'], ['E2', 'F3'], ['E3', 'F7'], ['E4', 'F1'], ['E5', 'F5']]) {
  eq(`SS5/${id} ${inv}`, [by.get(id).status, by.get(id).uncertainty], ['INVALID', 'CORPUS']);
  const t = by.get(id).trace[0];
  if (!t.defects.some(d => d.startsWith(inv))) { console.log('FAIL', id, 'defect not', inv, t.defects); fails++; }
  else console.log('ok   SS5/' + id, inv, t.defects[0]);
}

// SS5a.2 multiple distinct surviving atoms -> DECIDED with conclusion null.
eq('SS5a.2/G3 status', by.get('G3').status, 'DECIDED');
eq('SS5a.2/G3 conclusion', by.get('G3').conclusion, null);
eq('SS5a.2/G3 accepted', by.get('G3').accepted.sort(), ['B', 'C']);

// SS5a.3 contradictory survivors, no separating relation -> CONTESTED/CORPUS.
eq('SS5a.3/G5 status', by.get('G5').status, 'CONTESTED');
eq('SS5a.3/G5 uncertainty', by.get('G5').uncertainty, 'CORPUS');

// SS4.6 absent effective_from is not -inf: B2 (ef 15>0) still triggers A only via
// the date gate, and the relation is not applied because A is out of Theta;
// B4 has ef 50 > at 10 so B is untriggered and its lex_posterior cannot bite.
eq('SS4.6/B4 accepted', by.get('B4').accepted, ['A']);
eq('SS4.6/B4 represented_reason', by.get('B4').represented_reason, false);

// SS4.7 rank read ONLY where the corpus states it as the basis (C4, A3).
eq('SS4.7/C4 (basis stated)', by.get('C4').conclusion, 'NOT-Y');
eq('SS4.7/C3 (basis not satisfied)', by.get('C3').status, 'CONTESTED');
// C1: memo beats legislature with no declared relation at all -> must stay open.
eq('SS4.7/C1 (no relation, rank 9 present)', by.get('C1').status, 'CONTESTED');

// SS4.8 provenance: no defeat applied -> false, even though outcome is DECIDED.
eq('SS4.8/A2 rr', by.get('A2').represented_reason, false);
eq('SS4.8/A1 rr', by.get('A1').represented_reason, true);

// Unknown basis must be REJECTED, never guessed: synthesize one.
const engine = fs.readFileSync(path.join(__dirname, 'engine.js'), 'utf8');
const corpus = JSON.parse(fs.readFileSync(path.join(__dirname, '..', 'corpus_export.json'), 'utf8'));
const mutant = JSON.parse(JSON.stringify(corpus));
mutant.cases = [{
  id: 'ZZ', family: 'Z', state: ['X'], at: 10,
  rules: [
    { id: 'A', source: 's', authority: 'memo', cites: 'c', condition: 'X', conclusion: 'Y', rank: 1, promulgated: true, retroactive: false, effective_from: null, effective_to: null, requires_construct: null, specificity: 0, recency: 0, length: 0, confidence: 0.0, order_index: 0, text_similarity: 0.0 },
    { id: 'B', source: 's', authority: 'agency', cites: 'c', condition: 'X', conclusion: 'NOT-Y', rank: 99, promulgated: true, retroactive: false, effective_from: null, effective_to: null, requires_construct: null, specificity: 0, recency: 0, length: 0, confidence: 0.0, order_index: 0, text_similarity: 0.0 },
  ],
  defeats: [{ defeated: 'B', defeater: 'A', basis: 'chain_succession', provenance: 'p', enabled: true }],
}];
fs.writeFileSync('/tmp/mutant_corpus.json', JSON.stringify(mutant));
const { execFileSync } = require('child_process');
execFileSync(process.execPath, [path.join(__dirname, 'engine.js'), '/tmp/mutant_corpus.json', '/tmp/mutant_out.json']);
const zz = JSON.parse(fs.readFileSync('/tmp/mutant_out.json', 'utf8'))[0];
// Unrecognized basis + rank 99 tempting a heuristic fallback -> must stay CONTESTED.
eq('dispatch/unknown basis rejected', [zz.status, zz.uncertainty, zz.accepted.sort()],
   ['CONTESTED', 'CORPUS', ['A', 'B']]);

// Completeness of the basis dispatch table.
const KNOWN = ['explicit_lex_posterior', 'explicit_constitutional_supremacy',
  'explicit_authority_precedence', 'explicit_rank_precedence',
  'explicit_chain_succession', 'explicit_exception'];
for (const b of KNOWN) {
  if (!engine.includes(`case '${b}'`)) { console.log('FAIL basis not in dispatch:', b); fails++; }
  else console.log('ok   dispatch has', b);
}
if (/switch\s*\([^)]*\)\s*\{[\s\S]*?default:[^}]*basisSatisfied\(?[^?]*\?\?/i.test(engine)) {
  console.log('WARN dispatch default appears to guess'); fails++;
}

console.log(fails === 0 ? '\nALL SELF-TESTS PASS' : `\n${fails} FAILURES`);
process.exit(fails === 0 ? 0 : 1);