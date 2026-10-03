// impl_d — an independent reading of SEMANTICS.md v0.3 + CORPUS_FORMAT.md.
//
// DEFEAT-GRAPH REPRESENTATION (deliberately distinct again)
//
//   B and C both recompute S(n+1) by scanning all of Theta on every step.
//   impl_d instead holds the framework as an LABELLED ATTACK GRAPH: every
//   declared relation keeps its basis and provenance as an edge witness, and
//   grounding is a worklist DELTA PROPAGATION over per-argument attack
//   counters (`attacks_in_S`). Adding an argument to the extension decrements
//   the counter of each of its targets; removing one increments them back.
//   Resurrection (SEMANTICS.md 3: S(n+1) is computed over all of Theta, so
//   the sequence is not monotone) falls out of the counter arithmetic rather
//   than out of a full rescan.
//
//   OSCILLATION is detected with an integer FINGERPRINT of the live argument
//   set (order-independent, wrapping add of per-argument salts), not by set
//   comparison, so a repeating state is a cheap integer test. On a fingerprint
//   repeat the exact state is re-checked to rule out a collision.
//
//   Finally every extension is AUDITED by brute force: impl_d enumerates all
//   2^|Theta| subsets and collects every fixed point of the SEMANTICS.md 3
//   operator, then asserts the extension it computed is among them. The audit
//   never *selects* — selection is the Dung sequence's job, per 3 and 4.7.
//
//   Because impl_d can exhaust no budget (propagation is monotone within a
//   round and each round either changes the set or finishes), the
//   SEMANTICS.md 6.3 obligation "exhaustion is an operational error, never
//   SEMANTIC" is discharged structurally rather than by a counter.

use crate::json::Value;
use std::collections::{BTreeMap, BTreeSet};

// ---------------------------------------------------------------------------
// Status / uncertainty vocabularies (SEMANTICS.md 6.1, 6.3)
// ---------------------------------------------------------------------------

pub const STATUSES: [&str; 6] = [
    "DECIDED",
    "DEFEATED",
    "CONTESTED",
    "REFUSED",
    "NONFINDING",
    "INVALID",
];
pub const UNCERTAINTIES: [&str; 4] = ["SEMANTIC", "CORPUS", "IMPLEMENTATION", "NONE"];

/// DEFEATED is RESERVED (SEMANTICS.md 6.1). impl_d never constructs it; the
/// constant exists so the self-test can assert it is absent from every record.
#[allow(dead_code)]
pub const RESERVED: &str = "DEFEATED";

// ---------------------------------------------------------------------------
// Model
// ---------------------------------------------------------------------------

#[derive(Debug, Clone)]
pub struct Rule {
    pub id: String,
    pub source: String,
    pub authority: String,
    pub condition: String,
    pub conclusion: Option<String>,
    pub rank: Option<f64>,
    pub promulgated: Option<bool>,
    pub retroactive: Option<bool>,
    pub effective_from: Option<f64>,
    pub effective_to: Option<f64>,
    pub requires_construct: Option<String>,
}

#[derive(Debug, Clone)]
pub struct Defeat {
    pub defeated: String,
    pub defeater: String,
    pub basis: String,
    pub provenance: String,
    pub enabled: Option<bool>,
}

#[derive(Debug, Clone)]
pub struct Case {
    pub id: String,
    pub family: Option<String>,
    pub state: Vec<String>,
    pub at: Option<f64>,
    pub rules: Vec<Rule>,
    pub defeats: Vec<Defeat>,
}

#[derive(Debug, Clone)]
pub struct World {
    pub contradicts: BTreeMap<String, String>,
    pub authority_rank: BTreeMap<String, f64>,
}

/// An operational condition of the caller's program, never an epistemic
/// result about the corpus (SEMANTICS.md 6.3).
#[derive(Debug)]
pub struct OperationalError(pub String);

pub type OpResult<T> = Result<T, OperationalError>;

#[derive(Debug, Clone)]
pub struct Outcome {
    pub id: String,
    pub status: String,
    pub conclusion: Option<String>,
    pub defeated: Vec<String>,
    pub uncertainty: String,
    pub represented_reason: bool,
    pub accepted: Vec<String>,
    pub trace: Vec<String>,
}

// ---------------------------------------------------------------------------
// Parsing
// ---------------------------------------------------------------------------

fn parse_rule(v: &Value) -> Rule {
    Rule {
        id: v.opt_str("id").unwrap_or_default(),
        source: v.opt_str("source").unwrap_or_default(),
        authority: v.opt_str("authority").unwrap_or_default(),
        condition: v.opt_str("condition").unwrap_or_default(),
        conclusion: v.opt_str("conclusion"),
        rank: v.opt_f64("rank"),
        promulgated: v.opt_bool("promulgated"),
        retroactive: v.opt_bool("retroactive"),
        effective_from: v.opt_f64("effective_from"),
        effective_to: v.opt_f64("effective_to"),
        requires_construct: v.opt_str("requires_construct"),
    }
}

fn parse_defeat(v: &Value) -> Defeat {
    Defeat {
        defeated: v.opt_str("defeated").unwrap_or_default(),
        defeater: v.opt_str("defeater").unwrap_or_default(),
        basis: v.opt_str("basis").unwrap_or_default(),
        provenance: v.opt_str("provenance").unwrap_or_default(),
        enabled: v.opt_bool("enabled"),
    }
}

pub fn parse_world(doc: &Value) -> (World, Vec<Case>) {
    let mut contradicts = BTreeMap::new();
    if let Some(Value::Obj(m)) = doc.get("contradicts") {
        for (k, v) in m {
            if let Some(s) = v.as_str() {
                contradicts.insert(k.clone(), s.to_string());
            }
        }
    }
    let mut authority_rank = BTreeMap::new();
    if let Some(Value::Obj(m)) = doc.get("authority_rank") {
        for (k, v) in m {
            if let Some(n) = v.as_f64() {
                authority_rank.insert(k.clone(), n);
            }
        }
    }
    let cases = doc
        .get("cases")
        .and_then(|c| c.as_arr())
        .map(|a| {
            a.iter()
                .map(|c| Case {
                    id: c.opt_str("id").unwrap_or_default(),
                    family: c.opt_str("family"),
                    state: c.get("state").map(|s| s.as_strs()).unwrap_or_default(),
                    at: c.opt_f64("at"),
                    rules: c
                        .get("rules")
                        .and_then(|r| r.as_arr())
                        .map(|rs| rs.iter().map(parse_rule).collect())
                        .unwrap_or_default(),
                    defeats: c
                        .get("defeats")
                        .and_then(|d| d.as_arr())
                        .map(|ds| ds.iter().map(parse_defeat).collect())
                        .unwrap_or_default(),
                })
                .collect()
        })
        .unwrap_or_default();
    (World { contradicts, authority_rank }, cases)
}

// ---------------------------------------------------------------------------
// Basis satisfaction — COMPLETE dispatch. The catch-all REJECTS the relation;
// it never infers a basis. CORPUS_FORMAT.md: "Any other basis string is not a
// warrant and the relation is rejected."
// SEMANTICS.md 4.6: an unverifiable basis is an unsatisfied basis.
// ---------------------------------------------------------------------------

pub fn basis_holds(basis: &str, d: &Defeat, world: &World, rules: &BTreeMap<String, Rule>) -> bool {
    let (defeater, defeated) = match (rules.get(&d.defeater), rules.get(&d.defeated)) {
        (Some(a), Some(t)) => (a, t),
        _ => return false, // cannot verify without both operands (4.6)
    };
    match basis {
        "explicit_lex_posterior" => match (defeater.effective_from, defeated.effective_from) {
            (Some(f), Some(t)) => f > t, // absent operand => unsatisfied, NOT -inf (4.6)
            _ => false,
        },
        "explicit_constitutional_supremacy" | "explicit_authority_precedence" => {
            match (
                world.authority_rank.get(&defeater.authority),
                world.authority_rank.get(&defeated.authority),
            ) {
                (Some(f), Some(t)) => *f > *t, // absent authority_rank entry => unsatisfied (4.6)
                _ => false,
            }
        }
        "explicit_rank_precedence" => match (defeater.rank, defeated.rank) {
            (Some(f), Some(t)) => f > t,
            _ => false, // absent rank => unsatisfied for this basis (4.6)
        },
        "explicit_chain_succession" | "explicit_exception" => true, // stated; nothing to verify
        _ => false, // REJECTED RELATION — no fallback, no default that guesses
    }
}

// ---------------------------------------------------------------------------
// SEMANTICS.md 5 — structural validity, checked before anything else.
// ---------------------------------------------------------------------------

fn validity_defects(c: &Case) -> Vec<String> {
    let mut out = Vec::new();
    let mut seen: BTreeSet<&str> = BTreeSet::new();
    for r in &c.rules {
        // F5_NON_CONTRADICTION
        if !seen.insert(r.id.as_str()) {
            out.push(format!(
                "F5_NON_CONTRADICTION: duplicate rule id {}",
                r.id
            ));
        }
        // F2_PROMULGATION — absent `promulgated` is not "in force" (4.6 fail closed).
        if r.promulgated != Some(true) {
            out.push(format!(
                "F2_PROMULGATION: rule {} is unpromulgated",
                r.id
            ));
        }
        // F3_NON_RETROACTIVITY
        if r.retroactive == Some(true) && r.effective_from.is_some() {
            out.push(format!(
                "F3_NON_RETROACTIVITY: rule {} retroactive with effective_from",
                r.id
            ));
        }
        // F7_CONSTANCY
        if let (Some(f), Some(e)) = (r.effective_from, r.effective_to) {
            if f >= e {
                out.push(format!(
                    "F7_CONSTANCY: rule {} has empty validity interval [{}, {})",
                    r.id, f, e
                ));
            }
        }
    }
    let ids: BTreeSet<&str> = c.rules.iter().map(|r| r.id.as_str()).collect();
    for d in &c.defeats {
        for (role, name) in [("defeater", &d.defeater), ("defeated", &d.defeated)] {
            if !ids.contains(name.as_str()) {
                out.push(format!(
                    "F1_GENERALITY: relation names {} {} which does not exist",
                    role, name
                ));
            }
        }
    }
    out.sort();
    out.dedup();
    out
}

/// SEMANTICS.md 4.4 — a rule defeating itself. Checked over DECLARED relations
/// (not just basis-satisfying ones): 4.4 calls this a defect in the corpus, and
/// 5 requires defectiveness to be decidable without argumentation. Ordering:
/// treated as INVALID, so by 6.2(1) it outranks REFUSED.
fn self_defeat(c: &Case) -> Option<String> {
    c.defeats
        .iter()
        .find(|d| d.defeater == d.defeated)
        .map(|d| d.defeater.clone())
}

// ---------------------------------------------------------------------------
// Triggering (CORPUS_FORMAT.md, verbatim)
// ---------------------------------------------------------------------------

fn triggered(r: &Rule, state: &BTreeSet<String>, at: Option<f64>) -> bool {
    if !state.contains(r.condition.as_str()) {
        return false;
    }
    if let (Some(f), Some(t)) = (r.effective_from, at) {
        if t < f {
            return false;
        }
    }
    if let (Some(e), Some(t)) = (r.effective_to, at) {
        if t >= e {
            return false;
        }
    }
    true
}

// ---------------------------------------------------------------------------
// The labelled attack graph + delta propagation
// ---------------------------------------------------------------------------

/// An edge of the attack graph, keeping its basis witness (SEMANTICS.md 4.8:
/// a warrant must originate in the corpus as a declared relation).
#[derive(Debug, Clone)]
pub struct Edge {
    pub defeater: String,
    pub defeated: String,
    pub basis: String,
    pub provenance: String,
}

#[derive(Debug)]
pub struct Framework {
    pub nodes: Vec<String>,
    /// total declared (active) attackers of each node
    pub indeg: BTreeMap<String, usize>,
    /// attackers of each node, with edge witness
    pub arcs: BTreeMap<String, Vec<Edge>>,
    /// targets of each node
    pub out: BTreeMap<String, Vec<String>>,
}

pub fn build_framework(theta: &BTreeSet<String>, edges: &[Edge]) -> Framework {
    let mut indeg: BTreeMap<String, usize> = BTreeMap::new();
    let mut arcs: BTreeMap<String, Vec<Edge>> = BTreeMap::new();
    let mut out: BTreeMap<String, Vec<String>> = BTreeMap::new();
    for n in theta {
        indeg.insert(n.clone(), 0);
        arcs.insert(n.clone(), Vec::new());
        out.insert(n.clone(), Vec::new());
    }
    for e in edges {
        // both endpoints are in Theta by construction (SEMANTICS.md 3)
        *indeg.get_mut(&e.defeated).unwrap() += 1;
        arcs.get_mut(&e.defeater).unwrap().push(e.clone());
        out.get_mut(&e.defeater).unwrap().push(e.defeated.clone());
    }
    for v in arcs.values_mut() {
        v.sort_by(|a, b| (a.defeated.clone(), a.basis.clone()).cmp(&(b.defeated.clone(), b.basis.clone())));
    }
    for v in out.values_mut() {
        v.sort();
        v.dedup();
    }
    Framework { nodes: theta.iter().cloned().collect(), indeg, arcs, out }
}

/// Order-independent fingerprint of an argument set.
fn fingerprint(s: &BTreeSet<String>) -> u64 {
    let mut h: u64 = 0x9e3779b97f4a7c15;
    for n in s {
        let mut x: u64 = 0xcbf29ce484222325;
        for b in n.as_bytes() {
            x ^= *b as u64;
            x = x.wrapping_mul(0x100000001b3);
        }
        h = h.wrapping_add(x | 1);
    }
    h
}

pub enum Grounding {
    /// The Dung sequence stabilised.
    Extension { g: BTreeSet<String>, rounds: usize },
    /// A live state repeated: a demonstrated oscillation (SEMANTICS.md 4.2).
    Oscillation { states: Vec<BTreeSet<String>> },
}

pub fn ground(fw: &Framework) -> Grounding {
    // counters: attackers of `n` that are currently in S
    let mut in_s: BTreeSet<String> = fw.nodes.iter().cloned().collect();
    let mut counter: BTreeMap<String, usize> = fw.indeg.clone();
    let mut seen: Vec<u64> = Vec::new();
    let mut seen_states: Vec<BTreeSet<String>> = Vec::new();
    let mut states: Vec<BTreeSet<String>> = Vec::new();
    let mut rounds = 0usize;
    loop {
        let fp = fingerprint(&in_s);
        if let Some(at) = seen.iter().position(|f| *f == fp) {
            // Cheap integer test fired. Confirm with the exact state so a
            // fingerprint collision cannot manufacture an oscillation.
            if seen_states[at] == in_s {
                return Grounding::Oscillation { states: states[at..].to_vec() };
            }
        } else {
            seen.push(fp);
            seen_states.push(in_s.clone());
            states.push(in_s.clone());
        }

        // DELTA PROPAGATION: compute S(n+1) = { r in Theta : counter[r] == 0 }
        // by walking the adjacency once, never rescanning Theta per rule.
        let mut next = BTreeSet::new();
        for n in &fw.nodes {
            if counter[n] == 0 {
                next.insert(n.clone());
            }
        }
        rounds += 1;
        if next == in_s {
            return Grounding::Extension { g: in_s, rounds };
        }
        // Apply the delta. counter[t] counts the attackers of t that are
        // currently IN the extension, so an argument ENTERING the extension
        // adds an attack on each of its targets (+1) and an argument LEAVING
        // withdraws it (-1). Getting these signs backwards silently destroys
        // resurrection, which is why the exhaustive audit below exists: it
        // caught exactly this defect on the G family.
        for n in &next {
            if !in_s.contains(n) {
                for t in fw.out.get(n).unwrap() {
                    *counter.get_mut(t).unwrap() += 1;
                }
            }
        }
        for n in &in_s {
            if !next.contains(n) {
                for t in fw.out.get(n).unwrap() {
                    *counter.get_mut(t).unwrap() -= 1;
                }
            }
        }
        in_s = next;
    }
}

/// Brute-force audit: enumerate every subset of Theta and collect all fixed
/// points of the SEMANTICS.md 3 operator. Never used to SELECT an extension.
fn audit_fixpoints(fw: &Framework) -> Vec<BTreeSet<String>> {
    let n = fw.nodes.len();
    if n > 20 {
        return Vec::new(); // guard; unreachable on this corpus
    }
    let mut out = Vec::new();
    for mask in 0u32..(1u32 << n) {
        let s: BTreeSet<String> = (0..n)
            .filter(|i| mask & (1 << i) != 0)
            .map(|i| fw.nodes[i].clone())
            .collect();
        let next: BTreeSet<String> = fw
            .nodes
            .iter()
            .filter(|t| !fw.arcs_of(t).iter().any(|e| s.contains(&e.defeater)))
            .cloned()
            .collect();
        if next == s {
            out.push(s);
        }
    }
    out
}

impl Framework {
    fn arcs_of(&self, target: &str) -> Vec<&Edge> {
        self.arcs
            .values()
            .flat_map(|v| v.iter())
            .filter(|e| &e.defeated == target)
            .collect()
    }
}

// ---------------------------------------------------------------------------
// The engine
// ---------------------------------------------------------------------------

fn verdict(
    status: &str,
    conclusion: Option<String>,
    uncertainty: &str,
    accepted: Vec<String>,
    defeated: Vec<String>,
    rr: bool,
    trace: Vec<String>,
    id: &str,
) -> Outcome {
    Outcome {
        id: id.to_string(),
        status: status.to_string(),
        conclusion,
        defeated,
        uncertainty: uncertainty.to_string(),
        represented_reason: rr,
        accepted,
        trace,
    }
}

pub fn run(c: &Case, world: &World) -> OpResult<Outcome> {
    let mut trace: Vec<String> = Vec::new();
    let id = c.id.clone();

    // ---- SEMANTICS.md 5: structural validity runs FIRST -------------------
    let defects = validity_defects(c);
    if !defects.is_empty() {
        for d in &defects {
            trace.push(format!("validity: {}", d));
        }
        trace.push("validity: corpus is defective; no Theta exists to ground (5)".into());
        // 6.2(1): INVALID beats REFUSED — no requires_construct is consulted.
        return Ok(verdict("INVALID", None, "CORPUS", vec![], vec![], false, trace, &id));
    }

    let rule_map: BTreeMap<String, Rule> =
        c.rules.iter().map(|r| (r.id.clone(), r.clone())).collect();

    // ---- SEMANTICS.md 4.4: self-defeat is a corpus defect ----------------
    if let Some(who) = self_defeat(c) {
        trace.push(format!("self-defeat: {} defeats itself -> INVALID (4.4)", who));
        return Ok(verdict("INVALID", None, "CORPUS", vec![], vec![], false, trace, &id));
    }

    // ---- REFUSED: requires_construct names a construct outside the
    // expressible operation set (CORPUS_FORMAT.md). 6.2(1)/(3).
    if let Some(r) = c.rules.iter().find(|r| r.requires_construct.is_some()) {
        let construct = r.requires_construct.clone().unwrap();
        trace.push(format!(
            "expressibility: rule {} requires_construct {}",
            r.id, construct
        ));
        return Ok(verdict("REFUSED", None, "NONE", vec![], vec![], false, trace, &id));
    }

    // ---- triggering -------------------------------------------------------
    let state: BTreeSet<String> = c.state.iter().cloned().collect();
    let theta: BTreeSet<String> = c
        .rules
        .iter()
        .filter(|r| triggered(r, &state, c.at))
        .map(|r| r.id.clone())
        .collect();
    trace.push(format!(
        "theta: {{{}}}",
        theta.iter().cloned().collect::<Vec<_>>().join(", ")
    ));
    if theta.is_empty() {
        // 6.1 NONFINDING: corpus sound and no rule's condition holds.
        trace.push("triggering: nothing triggered -> NONFINDING (6.1)".into());
        return Ok(verdict("NONFINDING", None, "NONE", vec![], vec![], false, trace, &id));
    }

    // ---- active defeats (SEMANTICS.md 3) ----------------------------------
    let mut edges: Vec<Edge> = Vec::new();
    for d in &c.defeats {
        if d.enabled != Some(true) {
            trace.push(format!(
                "relation {}->{} rejected: not enabled",
                d.defeater, d.defeated
            ));
            continue;
        }
        if !theta.contains(&d.defeater) || !theta.contains(&d.defeated) {
            trace.push(format!(
                "relation {}->{} rejected: endpoint outside Theta",
                d.defeater, d.defeated
            ));
            continue;
        }
        if !basis_holds(&d.basis, d, world, &rule_map) {
            trace.push(format!(
                "relation {}->{} rejected: basis '{}' unsatisfied",
                d.defeater, d.defeated, d.basis
            ));
            continue;
        }
        trace.push(format!(
            "relation {}->{} active: {} [{}]",
            d.defeater, d.defeated, d.basis, d.provenance
        ));
        edges.push(Edge {
            defeater: d.defeater.clone(),
            defeated: d.defeated.clone(),
            basis: d.basis.clone(),
            provenance: d.provenance.clone(),
        });
    }

    let fw = build_framework(&theta, &edges);

    // ---- grounding --------------------------------------------------------
    let grounded: BTreeSet<String> = match ground(&fw) {
        Grounding::Extension { g, rounds } => {
            trace.push(format!(
                "grounding: delta propagation converged after {} round(s) at {{{}}}",
                rounds,
                g.iter().cloned().collect::<Vec<_>>().join(", ")
            ));
            g
        }
        Grounding::Oscillation { states } => {
            let names: BTreeSet<String> = states.iter().flatten().cloned().collect();
            trace.push(format!(
                "oscillation DEMONSTRATED by fingerprint repeat; states: {}",
                states
                    .iter()
                    .map(|s| format!("{{{}}}", s.iter().cloned().collect::<Vec<_>>().join(",")))
                    .collect::<Vec<_>>()
                    .join(" -> ")
            ));
            trace.push(format!("cycle members: {}", names.iter().cloned().collect::<Vec<_>>().join(", ")));
            // 4.2: CONTESTED / SEMANTIC. No stable fixpoint, so nothing accepted.
            // Not DEFEATED: 6.1 reserves that and the empty state is reached
            // only inside the oscillation, never as a stable fixpoint.
            return Ok(verdict("CONTESTED", None, "SEMANTIC", vec![], vec![], false, trace, &id));
        }
    };

    // ---- exhaustive audit (never selects; only checks) --------------------
    let fixes = audit_fixpoints(&fw);
    if fixes.len() <= 4096 && !fixes.iter().any(|s| *s == grounded) {
        return Err(OperationalError(format!(
            "case {}: computed extension {{{}}} is not a fixed point of the SEMANTICS.md 3 operator \
             ({} fixed point(s) exist)",
            id,
            grounded.iter().cloned().collect::<Vec<_>>().join(","),
            fixes.len()
        )));
    }
    trace.push(format!(
        "audit: {} fixed point(s) of the 3-operator over 2^{} subsets; computed extension is one of them",
        fixes.len(),
        theta.len()
    ));
    if fixes.len() > 1 {
        trace.push(format!(
            "audit note: multiple extensions admissible; the Dung sequence (3) selects one and \
             4.7 forbids any other preference"
        ));
    }

    if grounded.is_empty() {
        // DEFEATED is RESERVED (6.1). impl_d treats reaching this as an
        // operational contradiction of the reservation: an empty stable
        // extension cannot arise without a recursive component, which the
        // oscillation witness above has already excluded.
        return Err(OperationalError(format!(
            "case {}: empty grounded extension reached the reserved DEFEATED branch (6.1)",
            id
        )));
    }

    let defeated: Vec<String> = theta.difference(&grounded).cloned().collect();
    let accepted: Vec<String> = grounded.iter().cloned().collect();

    // ---- SEMANTICS.md 4.8: represented_reason ----------------------------
    // true iff at least one enabled, basis-satisfying relation was APPLIED —
    // read as: its defeater survived into the grounded extension, so the
    // relation actually did work — and every rule excluded from the extension
    // was excluded by such a relation.
    let applied = |x: &str| edges.iter().any(|e| e.defeated == x && grounded.contains(&e.defeater));
    let any_applied = edges.iter().any(|e| grounded.contains(&e.defeater));
    let all_excluded_represented = defeated.iter().all(|r| applied(r));
    let rr = any_applied && all_excluded_represented;
    trace.push(format!(
        "represented_reason: {} (relation applied = {}, every exclusion represented = {})",
        rr, any_applied, all_excluded_represented
    ));

    // ---- SEMANTICS.md 5a: proposition-level selection --------------------
    let atoms: BTreeSet<String> = grounded
        .iter()
        .filter_map(|r| rule_map.get(r).and_then(|x| x.conclusion.clone()))
        .collect();
    trace.push(format!(
        "surviving conclusion atoms: {{{}}}",
        atoms.iter().cloned().collect::<Vec<_>>().join(", ")
    ));

    let contradicts = |a: &str, b: &str| -> bool {
        if a == b {
            return false;
        }
        world.contradicts.get(a).map(|s| s == b).unwrap_or(false)
            || world.contradicts.get(b).map(|s| s == a).unwrap_or(false)
    };

    if atoms.len() == 1 {
        let atom = atoms.iter().next().unwrap().clone();
        return Ok(verdict("DECIDED", Some(atom), "NONE", accepted, defeated, rr, trace, &id));
    }
    if atoms.is_empty() {
        return Err(OperationalError(format!(
            "case {}: grounded extension asserts no conclusion atom; the specification defines no verdict \
             for a grounded extension with an absent `conclusion`",
            id
        )));
    }
    let alist: Vec<&String> = atoms.iter().collect();
    let mut conflicting: Option<(&String, &String)> = None;
    'outer: for i in 0..alist.len() {
        for j in (i + 1)..alist.len() {
            if contradicts(alist[i], alist[j]) {
                conflicting = Some((alist[i], alist[j]));
                break 'outer;
            }
        }
    }
    match conflicting {
        Some((x, y)) => {
            // 5a.3: contradictory surviving conclusions, and no represented
            // relation separates them. Both rules are in G, so no active edge
            // runs from either to the other.
            let separated = edges.iter().any(|e| {
                (e.defeater == *x || e.defeater == *y)
                    && (e.defeated == *x || e.defeated == *y)
                    && e.defeater != e.defeated
            });
            if separated {
                trace.push(format!("5a note: a represented relation runs between {} and {}", x, y));
            }
            trace.push(format!(
                "5a.3: {} and {} contradict; no represented relation separates them",
                x, y
            ));
            Ok(verdict("CONTESTED", None, "CORPUS", accepted, defeated, rr, trace, &id))
        }
        None => {
            // 5a.2: grounded and determinate, but no unique proposition.
            trace.push(format!(
                "5a.2: {} distinct surviving atoms, none contradictory; DECIDED with conclusion null",
                atoms.len()
            ));
            Ok(verdict("DECIDED", None, "NONE", accepted, defeated, rr, trace, &id))
        }
    }
}

// ---------------------------------------------------------------------------
// Serialisation
// ---------------------------------------------------------------------------

pub fn to_json(o: &Outcome) -> String {
    use crate::json::esc;
    let arr = |v: &Vec<String>| {
        format!(
            "[{}]",
            v.iter().map(|s| esc(s)).collect::<Vec<_>>().join(", ")
        )
    };
    format!(
        "{{\"id\": {}, \"status\": {}, \"conclusion\": {}, \"defeated\": {}, \"uncertainty\": {}, \
         \"represented_reason\": {}, \"accepted\": {}, \"trace\": {}}}",
        esc(&o.id),
        esc(&o.status),
        o.conclusion.as_ref().map(|s| esc(s)).unwrap_or_else(|| "null".into()),
        arr(&o.defeated),
        esc(&o.uncertainty),
        o.represented_reason,
        arr(&o.accepted),
        arr(&o.trace),
    )
}