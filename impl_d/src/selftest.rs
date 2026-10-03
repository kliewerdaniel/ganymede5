// impl_d self-test.
//
// Two kinds of assertion:
//   1. Corpus assertions on cases impl_d considers DIAGNOSTIC — the ones that
//      pin a specific clause of SEMANTICS.md. These are the only place a case
//      id appears; engine.rs contains none.
//   2. SYNTHETIC cases of impl_d's own construction (ids prefixed SYN-), probing
//      edges the 41-case corpus does not cover. Written as literal JSON so the
//      corpus-format parser is exercised too.

use crate::engine::{self, Case, World};
use crate::json;

pub struct Report {
    pub passed: usize,
    pub failed: usize,
    pub log: Vec<String>,
}

struct T {
    passed: usize,
    failed: usize,
    log: Vec<String>,
}

impl T {
    fn check(&mut self, name: &str, cond: bool, detail: String) {
        if cond {
            self.passed += 1;
            self.log.push(format!("  ok    {}", name));
        } else {
            self.failed += 1;
            self.log.push(format!("  FAIL  {}  -- {}", name, detail));
        }
    }
}

fn case<'a>(cases: &'a [Case], id: &str) -> &'a Case {
    cases
        .iter()
        .find(|c| c.id == id)
        .unwrap_or_else(|| panic!("no such case {}", id))
}

fn expect(t: &mut T, world: &World, cases: &[Case], id: &str, status: &str, unc: &str, conc: Option<&str>, acc: &[&str]) {
    let c = case(cases, id);
    match engine::run(c, world) {
        Err(e) => t.check(id, false, format!("operational error: {}", e.0)),
        Ok(o) => {
            let want_acc: Vec<String> = acc.iter().map(|s| s.to_string()).collect();
            let ok = o.status == status && o.uncertainty == unc && o.conclusion.as_deref() == conc && o.accepted == want_acc;
            t.check(
                id,
                ok,
                format!(
                    "got status={} unc={} conc={:?} acc={:?}; want status={} unc={} conc={:?} acc={:?}",
                    o.status, o.uncertainty, o.conclusion, o.accepted, status, unc, conc, want_acc
                ),
            );
        }
    }
}

fn expect_rr(t: &mut T, world: &World, cases: &[Case], id: &str, rr: bool) {
    match engine::run(case(cases, id), world) {
        Err(e) => t.check(id, false, format!("operational error: {}", e.0)),
        Ok(o) => t.check(
            &format!("{} represented_reason", id),
            o.represented_reason == rr,
            format!("got {}, want {} (4.8)", o.represented_reason, rr),
        ),
    }
}

// ---------------------------------------------------------------------------
// Synthetic corpus fragments
// ---------------------------------------------------------------------------

fn synth(cases_json: &str) -> (World, Vec<Case>) {
    let doc = json::parse(cases_json).expect("synthetic JSON must parse");
    engine::parse_world(&doc)
}

/// SYN-1: an UNRECOGNISED basis string, on a relation that would otherwise be a
/// rank fallback. Both rules assert the same atom and nothing else, so the only
/// possible difference is whether the rejected relation still bites. CORPUS_FORMAT
/// forbids a dispatch default; SEMANTICS 6.3 forbids inventing meaning for an
/// unlisted value. Expected: relation rejected, both survive, DECIDED, and
/// represented_reason FALSE (a decisive outcome without a represented warrant).
const SYN1: &str = r#"{
  "contradicts": {"Y": "NOT-Y", "NOT-Y": "Y"},
  "authority_rank": {"constitution": 4, "legislature": 3, "agency": 2, "memo": 1},
  "cases": [{
    "id": "SYN1_UNRECOGNISED_BASIS", "family": "SYN",
    "state": ["X"], "at": 10,
    "rules": [
      {"id":"A","source":"r_a","authority":"memo","cites":"r_a","condition":"X","conclusion":"Y",
       "rank":1,"promulgated":true,"retroactive":false,"effective_from":null,"effective_to":null,
       "requires_construct":null,"specificity":0,"recency":0,"length":0,"confidence":0.0,
       "order_index":0,"text_similarity":0.0},
      {"id":"B","source":"r_b","authority":"memo","cites":"r_b","condition":"X","conclusion":"Y",
       "rank":99,"promulgated":true,"retroactive":false,"effective_from":null,"effective_to":null,
       "requires_construct":null,"specificity":0,"recency":0,"length":0,"confidence":0.0,
       "order_index":0,"text_similarity":0.0}
    ],
    "defeats": [{"defeated":"B","defeater":"A","basis":"explicit_tacit_preference",
                 "provenance":"r_a","enabled":true}]
  }]
}"#;

/// SYN-2: explicit_lex_posterior where the DEFEE has no effective_from.
/// SEMANTICS 4.6: an absent effective_from is NOT -inf, so the basis is
/// unsatisfied and the relation is not a warrant. Both rules then survive and
/// contradict. If an implementation read absent as -inf, lex_posterior would
/// hold and one rule would be eliminated. Expected: CONTESTED / CORPUS via 5a.3,
/// accepted {A,B}, conclusion null.
const SYN2: &str = r#"{
  "contradicts": {"Y": "NOT-Y", "NOT-Y": "Y"},
  "authority_rank": {"constitution": 4, "legislature": 3, "agency": 2, "memo": 1},
  "cases": [{
    "id": "SYN2_ABSENT_EFFECTIVE_FROM_IS_NOT_NEG_INF", "family": "SYN",
    "state": ["X"], "at": 10,
    "rules": [
      {"id":"A","source":"r_a","authority":"agency","cites":"r_a","condition":"X","conclusion":"Y",
       "rank":1,"promulgated":true,"retroactive":false,"effective_from":null,"effective_to":null,
       "requires_construct":null,"specificity":0,"recency":0,"length":0,"confidence":0.0,
       "order_index":0,"text_similarity":0.0},
      {"id":"B","source":"r_b","authority":"agency","cites":"r_b","condition":"X","conclusion":"NOT-Y",
       "rank":1,"promulgated":true,"retroactive":false,"effective_from":7,"effective_to":null,
       "requires_construct":null,"specificity":0,"recency":0,"length":0,"confidence":0.0,
       "order_index":0,"text_similarity":0.0}
    ],
    "defeats": [{"defeated":"A","defeater":"B","basis":"explicit_lex_posterior",
                 "provenance":"r_b","enabled":true}]
  }]
}"#;

/// SYN-3: 5a.2 — three surviving rules asserting THREE DISTINCT, NON-
/// contradictory atoms, with no relations at all. The corpus has no such case:
/// G2/G2b/G2c/G5/G6 all end in 5a.3 (contradiction), never in a clean 5a.2.
/// Expected: DECIDED, conclusion null, accepted {A,B,C}, represented_reason
/// FALSE — no relation was applied, and per 4.8 that is a substantive finding.
const SYN3: &str = r#"{
  "contradicts": {"Y": "NOT-Y", "NOT-Y": "Y"},
  "authority_rank": {"constitution": 4, "legislature": 3, "agency": 2, "memo": 1},
  "cases": [{
    "id": "SYN3_MULTIPLE_DISTINCT_ATOMS_5A2", "family": "SYN",
    "state": ["X"], "at": 10,
    "rules": [
      {"id":"A","source":"r_a","authority":"agency","cites":"r_a","condition":"X","conclusion":"ALPHA",
       "rank":1,"promulgated":true,"retroactive":false,"effective_from":null,"effective_to":null,
       "requires_construct":null,"specificity":0,"recency":0,"length":0,"confidence":0.0,
       "order_index":0,"text_similarity":0.0},
      {"id":"B","source":"r_b","authority":"agency","cites":"r_b","condition":"X","conclusion":"BETA",
       "rank":2,"promulgated":true,"retroactive":false,"effective_from":null,"effective_to":null,
       "requires_construct":null,"specificity":0,"recency":0,"length":0,"confidence":0.0,
       "order_index":0,"text_similarity":0.0},
      {"id":"C","source":"r_c","authority":"agency","cites":"r_c","condition":"X","conclusion":"GAMMA",
       "rank":3,"promulgated":true,"retroactive":false,"effective_from":null,"effective_to":null,
       "requires_construct":null,"specificity":0,"recency":0,"length":0,"confidence":0.0,
       "order_index":0,"text_similarity":0.0}
    ],
    "defeats": []
  }]
}"#;

/// SYN-4: precedence 6.2(3) REFUSED beats NONFINDING. requires_construct on a
/// rule whose condition does NOT hold, so nothing triggers. The corpus's two
/// REFUSED cases (D1, D2) both have a triggered corpus, so this ordering is
/// never exercised there. Expected: REFUSED / NONE, not NONFINDING.
const SYN4: &str = r#"{
  "contradicts": {"Y": "NOT-Y", "NOT-Y": "Y"},
  "authority_rank": {"constitution": 4, "legislature": 3, "agency": 2, "memo": 1},
  "cases": [{
    "id": "SYN4_REFUSED_BEATS_NONFINDING", "family": "SYN",
    "state": ["Z"], "at": 10,
    "rules": [
      {"id":"A","source":"r_a","authority":"agency","cites":"r_a","condition":"X","conclusion":"Y",
       "rank":1,"promulgated":true,"retroactive":false,"effective_from":null,"effective_to":null,
       "requires_construct":"COUNTERFACTUAL","specificity":0,"recency":0,"length":0,"confidence":0.0,
       "order_index":0,"text_similarity":0.0}
    ],
    "defeats": []
  }]
}"#;

/// SYN-5: a THREE-cycle A->B->C->A, unattacked by anything. Every argument is
/// attacked, so no stable extension exists. Expected: CONTESTED / SEMANTIC on a
/// DEMONSTRATED oscillation ({A,B,C} -> {} -> {A,B,C}), accepted empty, and NOT
/// DEFEATED (reserved, 6.1). This is the cleanest witness that the empty set
/// encountered mid-oscillation must never be reported as a status.
const SYN5: &str = r#"{
  "contradicts": {"Y": "NOT-Y", "NOT-Y": "Y"},
  "authority_rank": {"constitution": 4, "legislature": 3, "agency": 2, "memo": 1},
  "cases": [{
    "id": "SYN5_THREE_CYCLE", "family": "SYN",
    "state": ["X"], "at": 10,
    "rules": [
      {"id":"A","source":"r_a","authority":"agency","cites":"r_a","condition":"X","conclusion":"Y",
       "rank":1,"promulgated":true,"retroactive":false,"effective_from":null,"effective_to":null,
       "requires_construct":null,"specificity":0,"recency":0,"length":0,"confidence":0.0,
       "order_index":0,"text_similarity":0.0},
      {"id":"B","source":"r_b","authority":"agency","cites":"r_b","condition":"X","conclusion":"NOT-Y",
       "rank":2,"promulgated":true,"retroactive":false,"effective_from":null,"effective_to":null,
       "requires_construct":null,"specificity":0,"recency":0,"length":0,"confidence":0.0,
       "order_index":0,"text_similarity":0.0},
      {"id":"C","source":"r_c","authority":"agency","cites":"r_c","condition":"X","conclusion":"ALPHA",
       "rank":3,"promulgated":true,"retroactive":false,"effective_from":null,"effective_to":null,
       "requires_construct":null,"specificity":0,"recency":0,"length":0,"confidence":0.0,
       "order_index":0,"text_similarity":0.0}
    ],
    "defeats": [
      {"defeated":"A","defeater":"B","basis":"explicit_chain_succession","provenance":"r_b","enabled":true},
      {"defeated":"B","defeater":"C","basis":"explicit_chain_succession","provenance":"r_c","enabled":true},
      {"defeated":"C","defeater":"A","basis":"explicit_chain_succession","provenance":"r_a","enabled":true}
    ]
  }]
}"#;

/// SYN-6: a DISABLED self-defeat. 4.4 says a rule defeating itself is INVALID,
/// but does not say whether a disabled relation counts. impl_d's reading: the
/// relation is DECLARED in the corpus, 4.4 calls it a corpus defect, and 5
/// requires defectiveness to be decidable without argumentation, so the verdict
/// is INVALID regardless of `enabled`. This assertion pins impl_d's reading and
/// is the case most likely to disagree with another implementation.
const SYN6: &str = r#"{
  "contradicts": {"Y": "NOT-Y", "NOT-Y": "Y"},
  "authority_rank": {"constitution": 4, "legislature": 3, "agency": 2, "memo": 1},
  "cases": [{
    "id": "SYN6_DISABLED_SELF_DEFEAT", "family": "SYN",
    "state": ["X"], "at": 10,
    "rules": [
      {"id":"A","source":"r_a","authority":"agency","cites":"r_a","condition":"X","conclusion":"Y",
       "rank":1,"promulgated":true,"retroactive":false,"effective_from":null,"effective_to":null,
       "requires_construct":null,"specificity":0,"recency":0,"length":0,"confidence":0.0,
       "order_index":0,"text_similarity":0.0}
    ],
    "defeats": [{"defeated":"A","defeater":"A","basis":"explicit_chain_succession",
                 "provenance":"r_a","enabled":false}]
  }]
}"#;

/// SYN-7: a defeat relation whose endpoint is OUTSIDE Theta (defeater not
/// triggered) on an otherwise-decisive framework. SEMANTICS 3 makes an active
/// defeat require both endpoints in Theta, so the relation does not apply and
/// the outcome is decisive WITHOUT a warrant: DECIDED with represented_reason
/// FALSE. Probes that 4.8 measures the relation actually applied, not merely
/// declared.
const SYN7: &str = r#"{
  "contradicts": {"Y": "NOT-Y", "NOT-Y": "Y"},
  "authority_rank": {"constitution": 4, "legislature": 3, "agency": 2, "memo": 1},
  "cases": [{
    "id": "SYN7_RELATION_ENDPOINT_OUTSIDE_THETA", "family": "SYN",
    "state": ["X"], "at": 10,
    "rules": [
      {"id":"A","source":"r_a","authority":"legislature","cites":"r_a","condition":"X","conclusion":"Y",
       "rank":2,"promulgated":true,"retroactive":false,"effective_from":null,"effective_to":null,
       "requires_construct":null,"specificity":0,"recency":0,"length":0,"confidence":0.0,
       "order_index":0,"text_similarity":0.0},
      {"id":"B","source":"r_b","authority":"agency","cites":"r_b","condition":"X","conclusion":"NOT-Y",
       "rank":1,"promulgated":true,"retroactive":false,"effective_from":null,"effective_to":null,
       "requires_construct":null,"specificity":0,"recency":0,"length":0,"confidence":0.0,
       "order_index":0,"text_similarity":0.0},
      {"id":"Z","source":"r_z","authority":"constitution","cites":"r_z","condition":"Q","conclusion":"OMEGA",
       "rank":9,"promulgated":true,"retroactive":false,"effective_from":null,"effective_to":null,
       "requires_construct":null,"specificity":0,"recency":0,"length":0,"confidence":0.0,
       "order_index":0,"text_similarity":0.0}
    ],
    "defeats": [{"defeated":"B","defeater":"A","basis":"explicit_constitutional_supremacy",
                 "provenance":"r_a","enabled":true},
                {"defeated":"B","defeater":"Z","basis":"explicit_constitutional_supremacy",
                 "provenance":"r_z","enabled":true}]
  }]
}"#;

/// SYN-8: 6.2(1) INVALID beats REFUSED, independently of the corpus's own H3:
/// F7_CONSTANCY (effective_from >= effective_to) co-occurring with a
/// requires_construct. Expected: INVALID / CORPUS.
const SYN8: &str = r#"{
  "contradicts": {"Y": "NOT-Y", "NOT-Y": "Y"},
  "authority_rank": {"constitution": 4, "legislature": 3, "agency": 2, "memo": 1},
  "cases": [{
    "id": "SYN8_INVALID_BEATS_REFUSED", "family": "SYN",
    "state": ["X"], "at": 10,
    "rules": [
      {"id":"A","source":"r_a","authority":"legislature","cites":"r_a","condition":"X","conclusion":"Y",
       "rank":1,"promulgated":true,"retroactive":false,"effective_from":20,"effective_to":20,
       "requires_construct":"ROUND","specificity":0,"recency":0,"length":0,"confidence":0.0,
       "order_index":0,"text_similarity":0.0}
    ],
    "defeats": []
  }]
}"#;

// ---------------------------------------------------------------------------

pub fn run(world: &World, cases: &[Case]) -> Report {
    let mut t = T { passed: 0, failed: 0, log: Vec::new() };
    t.log.push("impl_d self-test".into());

    // ---- 5: the five validity invariants, one case each ------------------
    t.log.push("[corpus] SEMANTICS.md 5 structural defects".into());
    expect(&mut t, world, cases, "E1", "INVALID", "CORPUS", None, &[]); // F2 promulgation
    expect(&mut t, world, cases, "E2", "INVALID", "CORPUS", None, &[]); // F3 non-retroactivity
    expect(&mut t, world, cases, "E3", "INVALID", "CORPUS", None, &[]); // F7 constancy
    expect(&mut t, world, cases, "E4", "INVALID", "CORPUS", None, &[]); // F1 generality
    expect(&mut t, world, cases, "E5", "INVALID", "CORPUS", None, &[]); // F5 non-contradiction

    // ---- 4.4 self-defeat is INVALID, never CONTESTED ---------------------
    t.log.push("[corpus] SEMANTICS.md 4.4 self-defeat".into());
    expect(&mut t, world, cases, "G8", "INVALID", "CORPUS", None, &[]);

    // ---- 6.1 NONFINDING --------------------------------------------------
    t.log.push("[corpus] SEMANTICS.md 6.1 NONFINDING".into());
    expect(&mut t, world, cases, "H1", "NONFINDING", "NONE", None, &[]);
    expect(&mut t, world, cases, "H4", "NONFINDING", "NONE", None, &[]);

    // ---- 6.1 REFUSED, and 6.2(1) INVALID beats REFUSED -------------------
    t.log.push("[corpus] SEMANTICS.md 6.1/6.2 REFUSED and precedence".into());
    expect(&mut t, world, cases, "D1", "REFUSED", "NONE", None, &[]);
    expect(&mut t, world, cases, "D2", "REFUSED", "NONE", None, &[]);
    expect(&mut t, world, cases, "H3", "INVALID", "CORPUS", None, &[]);

    // ---- 4.1 basis satisfaction: a stated, satisfied warrant decides ------
    t.log.push("[corpus] SEMANTICS.md 4.1 satisfied basis -> DECIDED".into());
    expect(&mut t, world, cases, "A1", "DECIDED", "NONE", Some("Y"), &["A"]);
    expect(&mut t, world, cases, "A3", "DECIDED", "NONE", Some("Y"), &["A"]);
    expect(&mut t, world, cases, "B3", "DECIDED", "NONE", Some("NOT-Y"), &["B"]);
    expect(&mut t, world, cases, "B5", "DECIDED", "NONE", Some("NOT-Y"), &["B"]);
    // absent effective_from is NOT -inf: the lex_posterior basis is unsatisfied,
    // so the relation is not a warrant and the outcome is decisive without one.
    expect(&mut t, world, cases, "B2", "DECIDED", "NONE", Some("NOT-Y"), &["B"]);
    expect(&mut t, world, cases, "B4", "DECIDED", "NONE", Some("Y"), &["A"]);
    // no relation at all: still DECIDED, but 4.8 warrants represented_reason=false.
    expect(&mut t, world, cases, "A2", "DECIDED", "NONE", Some("Y"), &["A"]);
    expect(&mut t, world, cases, "G7", "DECIDED", "NONE", Some("Y"), &["M", "N"]);

    // ---- 4.7 inert fields must never decide ------------------------------
    t.log.push("[corpus] SEMANTICS.md 4.7 semantically inert fields".into());
    expect(&mut t, world, cases, "C4", "DECIDED", "NONE", Some("NOT-Y"), &["B"]); // rank IS the stated basis
    expect(&mut t, world, cases, "F7", "DECIDED", "NONE", Some("Y"), &["A"]); // stated basis wins over confidence
    // F1..F6 carry specificity / recency / confidence / order / length /
    // similarity with no relation at all: nothing may be decided by them.
    for id in ["F1", "F2", "F3", "F4", "F5", "F6"] {
        expect(&mut t, world, cases, id, "CONTESTED", "CORPUS", None, &["A", "B"]);
    }
    // C2 relation disabled; C3 basis unsatisfied (memo cannot outrank
    // legislature): both leave a contradiction standing.
    expect(&mut t, world, cases, "C2", "CONTESTED", "CORPUS", None, &["A", "B"]);
    expect(&mut t, world, cases, "C3", "CONTESTED", "CORPUS", None, &["A", "B"]);
    expect(&mut t, world, cases, "C1", "CONTESTED", "CORPUS", None, &["A", "B"]);

    // ---- 3: the worked chain, and non-propagation of a defeated defeater --
    t.log.push("[corpus] SEMANTICS.md 3 fixpoint; defeated defeater's attack".into());
    // D defeats C defeats B defeats A -> {B,D} per the table in 3.
    expect(&mut t, world, cases, "G1", "DECIDED", "NONE", Some("NOT-Y"), &["B", "D"]);
    // H5 is the same four-chain with a different atom labelling.
    expect(&mut t, world, cases, "H5", "DECIDED", "NONE", Some("NOT-Y"), &["B", "D"]);
    // G5: the exception D defeats C, so C is out and B survives.
    expect(&mut t, world, cases, "G5", "CONTESTED", "CORPUS", None, &["B", "D"]);
    // G3: the chain C->B is DISABLED, so B never defeats A and A survives.
    expect(&mut t, world, cases, "G3", "DECIDED", "NONE", None, &["B", "C"]);
    // G6: the only relation's basis is unsatisfied (agency > legislature fails),
    // so nothing is excluded and two contradiction pairs stand.
    expect(&mut t, world, cases, "G6", "CONTESTED", "CORPUS", None, &["A", "B", "C", "D"]);
    expect(&mut t, world, cases, "G2", "CONTESTED", "CORPUS", None, &["B", "D", "F"]);
    expect(&mut t, world, cases, "G2b", "CONTESTED", "CORPUS", None, &["B", "D", "F"]);
    expect(&mut t, world, cases, "G2c", "CONTESTED", "CORPUS", None, &["B", "D", "E"]);

    // ---- 4.2 cycle -> CONTESTED / SEMANTIC -------------------------------
    t.log.push("[corpus] SEMANTICS.md 4.2 cyclic defeat".into());
    expect(&mut t, world, cases, "G4", "CONTESTED", "SEMANTIC", None, &[]);

    // ---- 5a proposition selection ----------------------------------------
    t.log.push("[corpus] SEMANTICS.md 5a proposition-level selection".into());
    // H2: constitutional supremacy, single surviving atom.
    expect(&mut t, world, cases, "H2", "DECIDED", "NONE", Some("NOT-Y"), &["B"]);
    // G3: two distinct non-contradictory atoms -> DECIDED with conclusion null.
    expect(&mut t, world, cases, "G3", "DECIDED", "NONE", None, &["B", "C"]);

    // ---- 4.8 represented_reason ------------------------------------------
    t.log.push("[corpus] SEMANTICS.md 4.8 represented_reason".into());
    expect_rr(&mut t, world, cases, "A1", true); // authority precedence applied
    expect_rr(&mut t, world, cases, "A2", false); // decisive with no warrant
    expect_rr(&mut t, world, cases, "G7", false);
    expect_rr(&mut t, world, cases, "F1", false); // inert fields are not warrants
    expect_rr(&mut t, world, cases, "G1", true);
    expect_rr(&mut t, world, cases, "H2", true);
    expect_rr(&mut t, world, cases, "G4", false); // no stable extension to warrant
    expect_rr(&mut t, world, cases, "E1", false); // INVALID asserts nothing

    // ---- 6.1 DEFEATED is reserved: never emitted -------------------------
    t.log.push("[global] SEMANTICS.md 6.1 DEFEATED reserved".into());
    let mut emitted_defeated = false;
    for c in cases {
        if let Ok(o) = engine::run(c, world) {
            if o.status == engine::RESERVED {
                emitted_defeated = true;
                t.log.push(format!("       {} emitted reserved DEFEATED", o.id));
            }
            if o.uncertainty == "IMPLEMENTATION" {
                t.log.push(format!("       {} emitted IMPLEMENTATION", o.id));
            }
        }
    }
    t.check("no case emits DEFEATED", !emitted_defeated, "a case reached the reserved status".into());
    t.check("6.4 every case reached a status in the enumerated domain",
            cases.iter().all(|c| engine::run(c, world)
                .map(|o| engine::STATUSES.contains(&o.status.as_str()))
                .unwrap_or(false)),
            "a status outside SEMANTICS.md 6.1 was produced".into());
    t.check("every uncertainty is engine-emittable (SEMANTIC|CORPUS|NONE)",
            cases.iter().all(|c| engine::run(c, world)
                .map(|o| o.uncertainty == "SEMANTIC" || o.uncertainty == "CORPUS" || o.uncertainty == "NONE")
                .unwrap_or(false)),
            "an engine-illegal uncertainty was produced".into());

    // ---- 6.3 operational limits are not epistemic results ---------------
    t.log.push("[global] SEMANTICS.md 6.3 no SEMANTIC without oscillation".into());
    t.check("SEMANTIC only ever accompanies CONTESTED",
            cases.iter().all(|c| engine::run(c, world)
                .map(|o| o.uncertainty != "SEMANTIC" || o.status == "CONTESTED")
                .unwrap_or(false)),
            "SEMANTIC was reported on a non-CONTESTED status".into());
    t.check("every case terminates without an operational error",
            cases.iter().all(|c| engine::run(c, world).is_ok()),
            "a case exhausted its budget (see main's OPERATIONAL ERROR report)".into());

    // ---- synthetic cases --------------------------------------------------
    t.log.push("[synthetic] impl_d's own constructions".into());

    let (w1, c1) = synth(SYN1);
    expect(&mut t, &w1, &c1, "SYN1_UNRECOGNISED_BASIS", "DECIDED", "NONE", Some("Y"), &["A", "B"]);
    expect_rr(&mut t, &w1, &c1, "SYN1_UNRECOGNISED_BASIS", false);

    let (w2, c2) = synth(SYN2);
    expect(&mut t, &w2, &c2, "SYN2_ABSENT_EFFECTIVE_FROM_IS_NOT_NEG_INF", "CONTESTED", "CORPUS", None, &["A", "B"]);
    expect_rr(&mut t, &w2, &c2, "SYN2_ABSENT_EFFECTIVE_FROM_IS_NOT_NEG_INF", false);

    let (w3, c3) = synth(SYN3);
    expect(&mut t, &w3, &c3, "SYN3_MULTIPLE_DISTINCT_ATOMS_5A2", "DECIDED", "NONE", None, &["A", "B", "C"]);
    expect_rr(&mut t, &w3, &c3, "SYN3_MULTIPLE_DISTINCT_ATOMS_5A2", false);

    let (w4, c4) = synth(SYN4);
    expect(&mut t, &w4, &c4, "SYN4_REFUSED_BEATS_NONFINDING", "REFUSED", "NONE", None, &[]);

    let (w5, c5) = synth(SYN5);
    expect(&mut t, &w5, &c5, "SYN5_THREE_CYCLE", "CONTESTED", "SEMANTIC", None, &[]);
    match engine::run(&c5[0], &w5) {
        Ok(o) => {
            t.check("SYN5 reports the cycle members in the trace",
                    o.trace.iter().any(|l| l.contains("cycle members")),
                    "4.2 requires the cycle to be named in the trace".into());
            t.check("SYN5 does not report DEFEATED for the empty state inside the oscillation",
                    o.status != "DEFEATED", "6.1 reserves DEFEATED".into());
        }
        Err(e) => t.check("SYN5", false, e.0),
    }

    let (w6, c6) = synth(SYN6);
    expect(&mut t, &w6, &c6, "SYN6_DISABLED_SELF_DEFEAT", "INVALID", "CORPUS", None, &[]);

    let (w7, c7) = synth(SYN7);
    expect(&mut t, &w7, &c7, "SYN7_RELATION_ENDPOINT_OUTSIDE_THETA", "DECIDED", "NONE", Some("Y"), &["A"]);
    expect_rr(&mut t, &w7, &c7, "SYN7_RELATION_ENDPOINT_OUTSIDE_THETA", true);

    let (w8, c8) = synth(SYN8);
    expect(&mut t, &w8, &c8, "SYN8_INVALID_BEATS_REFUSED", "INVALID", "CORPUS", None, &[]);

    Report { passed: t.passed, failed: t.failed, log: t.log }
}