// ============================================================================
// impl_b — an INDEPENDENT implementation of the Ganymede5 defeat semantics.
//
// Written from SEMANTICS.md + CORPUS_FORMAT.md only. No Ganymede5 source was
// consulted. Language: Rust (chosen to maximise structural independence from
// the Python implementation that also exists).
//
// ---------------------------------------------------------------------------
// REPRESENTATION CHOICE (see requirement 2)
// ---------------------------------------------------------------------------
// The defeat (attack) relation is held as an ADJACENCY MATRIX OF BITWORDS, one
// row per rule-object, `attack[i][w]` bit j set iff rule i attacks rule j.
//
// Rationale:
//   * A matrix (rather than a per-rule list of opponents) makes the operator
//     `S(n+1) = { r in Theta : r is unattacked in S(n) }` (SEMANTICS.md §3) a
//     single word-parallel OR-reduction: the set of attacked rules is
//     `OR_{s in S} attack[s]`, a bitwise union of rows, and the next set is
//     `Theta \\ attacked`. That is a different iteration scheme from scanning
//     "does any member of S attack r" one rule at a time.
//   * The matrix is also the input to a Warshall transitive closure, which
//     supplies cycle membership (SCCs) independently of the acceptance
//     iteration. A cycle in the ATTACK structure is a distinct fact from a
//     failure of the acceptance iteration to stabilise, and SEMANTICS.md
//     routes them to different answers (§4.2 vs §4.5), so they are computed
//     by separate mechanisms.
//   * Rules are nodes by rule OBJECT, not by rule id, so a corpus that
//     supplies the same id twice (a procedural oddity) does not silently
//     collapse into one argument. Defeat entries address nodes by id and
//     therefore apply to every node carrying that id.
//
// Basis dispatch (requirement 3): `basis_holds` is a total `match` over the
// six bases CORPUS_FORMAT.md defines, with the unmatched arm returning None.
// None is NOT a warrant, so an unrecognised basis string rejects the relation.
// There is no fallback, no numeric heuristic, no default branch.
// ============================================================================

use std::collections::{HashMap, HashSet};
use std::fs;

// ---------------------------------------------------------------- JSON ------

#[derive(Debug, Clone)]
enum J {
    Null,
    Bool(bool),
    Num(f64),
    Str(String),
    Arr(Vec<J>),
    Obj(Vec<(String, J)>),
}

impl J {
    fn get(&self, k: &str) -> Option<&J> {
        if let J::Obj(m) = self {
            m.iter().find(|(kk, _)| kk == k).map(|(_, v)| v)
        } else {
            None
        }
    }
    fn s(&self, k: &str) -> Option<String> {
        match self.get(k) {
            Some(J::Str(v)) => Some(v.clone()),
            _ => None,
        }
    }
    fn n(&self, k: &str) -> Option<f64> {
        match self.get(k) {
            Some(J::Num(v)) => Some(*v),
            _ => None,
        }
    }
    fn b(&self, k: &str) -> Option<bool> {
        match self.get(k) {
            Some(J::Bool(v)) => Some(*v),
            _ => None,
        }
    }
    fn is_null(&self, k: &str) -> bool {
        matches!(self.get(k), Some(J::Null)) || self.get(k).is_none()
    }
    fn arr(&self, k: &str) -> Vec<J> {
        match self.get(k) {
            Some(J::Arr(v)) => v.clone(),
            _ => vec![],
        }
    }
}

struct P<'a> {
    b: &'a [u8],
    i: usize,
}

impl<'a> P<'a> {
    fn ws(&mut self) {
        while self.i < self.b.len() && (self.b[self.i] as char).is_whitespace() {
            self.i += 1;
        }
    }
    fn val(&mut self) -> Result<J, String> {
        self.ws();
        if self.i >= self.b.len() {
            return Err("eof".into());
        }
        match self.b[self.i] {
            b'{' => {
                self.i += 1;
                let mut out = vec![];
                self.ws();
                if self.b[self.i] == b'}' {
                    self.i += 1;
                    return Ok(J::Obj(out));
                }
                loop {
                    self.ws();
                    let k = match self.val()? {
                        J::Str(s) => s,
                        _ => return Err("key".into()),
                    };
                    self.ws();
                    if self.b[self.i] != b':' {
                        return Err("colon".into());
                    }
                    self.i += 1;
                    let v = self.val()?;
                    out.push((k, v));
                    self.ws();
                    match self.b[self.i] {
                        b',' => {
                            self.i += 1;
                        }
                        b'}' => {
                            self.i += 1;
                            return Ok(J::Obj(out));
                        }
                        _ => return Err("obj".into()),
                    }
                }
            }
            b'[' => {
                self.i += 1;
                let mut out = vec![];
                self.ws();
                if self.b[self.i] == b']' {
                    self.i += 1;
                    return Ok(J::Arr(out));
                }
                loop {
                    out.push(self.val()?);
                    self.ws();
                    match self.b[self.i] {
                        b',' => {
                            self.i += 1;
                        }
                        b']' => {
                            self.i += 1;
                            return Ok(J::Arr(out));
                        }
                        _ => return Err("arr".into()),
                    }
                }
            }
            b'"' => {
                self.i += 1;
                let mut s = String::new();
                while self.b[self.i] != b'"' {
                    if self.b[self.i] == b'\\' {
                        self.i += 1;
                        let c = self.b[self.i];
                        self.i += 1;
                        match c {
                            b'n' => s.push('\n'),
                            b't' => s.push('\t'),
                            b'r' => s.push('\r'),
                            b'u' => {
                                let hex = std::str::from_utf8(&self.b[self.i..self.i + 4]).unwrap();
                                let cp = u32::from_str_radix(hex, 16).unwrap();
                                s.push(char::from_u32(cp).unwrap_or('?'));
                                self.i += 4;
                            }
                            other => s.push(other as char),
                        }
                    } else {
                        // copy raw utf-8 byte
                        let start = self.i;
                        let mut end = self.i;
                        while self.b[end] != b'"' && self.b[end] != b'\\' {
                            end += 1;
                        }
                        s.push_str(std::str::from_utf8(&self.b[start..end]).unwrap());
                        self.i = end;
                    }
                }
                self.i += 1;
                Ok(J::Str(s))
            }
            b't' => {
                self.i += 4;
                Ok(J::Bool(true))
            }
            b'f' => {
                self.i += 5;
                Ok(J::Bool(false))
            }
            b'n' => {
                self.i += 4;
                Ok(J::Null)
            }
            _ => {
                let start = self.i;
                while self.i < self.b.len()
                    && matches!(self.b[self.i], b'0'..=b'9' | b'-' | b'+' | b'.' | b'e' | b'E')
                {
                    self.i += 1;
                }
                let s = std::str::from_utf8(&self.b[start..self.i]).unwrap();
                s.parse::<f64>().map(J::Num).map_err(|e| e.to_string())
            }
        }
    }
}

// ------------------------------------------------------------- bit matrix ---

type Bits = Vec<u64>;

fn bits_new(n: usize) -> Bits {
    vec![0u64; (n + 63) / 64]
}
fn bits_set(b: &mut Bits, i: usize) {
    b[i / 64] |= 1u64 << (i % 64);
}
fn bits_get(b: &Bits, i: usize) -> bool {
    (b[i / 64] >> (i % 64)) & 1 == 1
}
fn bits_or(acc: &mut Bits, x: &Bits) {
    for (a, y) in acc.iter_mut().zip(x.iter()) {
        *a |= *y;
    }
}

// ----------------------------------------------------------------- rules ----

struct Rule {
    id: String,
    authority: String,
    condition: String,
    conclusion: String,
    rank: f64,
    eff_from: Option<f64>,
    eff_to: Option<f64>,
    requires_construct: Option<String>,
}

fn triggered(r: &Rule, state: &HashSet<String>, at: Option<f64>) -> bool {
    // CORPUS_FORMAT.md: "A rule is triggered iff all of: condition in state;
    // [temporal tests guarded by `at is not null`]".
    if !state.contains(&r.condition) {
        return false;
    }
    if let Some(t) = at {
        if let Some(ef) = r.eff_from {
            if t < ef {
                return false;
            }
        }
        if let Some(et) = r.eff_to {
            if !(t < et) {
                return false;
            }
        }
    }
    true
}

// ------------------------------------------------------------ basis table ---

// Returns Some(holds) only for the six bases CORPUS_FORMAT.md defines.
// None = unrecognised basis = NOT a warrant = relation rejected.
fn basis_holds(
    basis: &str,
    defeater: &Rule,
    defeated: &Rule,
    arank: &HashMap<String, f64>,
) -> Option<bool> {
    match basis {
        "explicit_lex_posterior" => {
            // "defeater's effective_from > defeated's"
            // A rule with no `effective_from` states no lower temporal bound,
            // i.e. it is in force from the beginning of time; read as -inf so
            // that a dated rule is posterior to it. (Under-specified: the
            // format does not say how a null date compares. Flagged.)
            let a = defeater.eff_from.unwrap_or(f64::NEG_INFINITY);
            let b = defeated.eff_from.unwrap_or(f64::NEG_INFINITY);
            Some(a > b)
        }
        "explicit_constitutional_supremacy" | "explicit_authority_precedence" => Some(
            arank.get(&defeater.authority).copied().unwrap_or(f64::NEG_INFINITY)
                > arank.get(&defeated.authority).copied().unwrap_or(f64::NEG_INFINITY),
        ),
        "explicit_rank_precedence" => Some(defeater.rank > defeated.rank),
        "explicit_chain_succession" | "explicit_exception" => Some(true),
        _ => None,
    }
}

// ------------------------------------------------------------------ case ----

struct Out {
    id: String,
    status: String,
    conclusion: Option<String>,
    defeated: Vec<String>,
    uncertainty: String,
    represented_reason: bool,
    accepted: Vec<String>,
    trace: Vec<String>,
}

fn contradiction_pair(a: &str, b: &str, contra: &HashMap<String, String>) -> bool {
    // "Two atoms contradict iff they appear in `contradicts`."
    contra.get(a).map(|x| x == b).unwrap_or(false) || contra.get(b).map(|x| x == a).unwrap_or(false)
}

fn solve(case: &J, contra: &HashMap<String, String>, arank: &HashMap<String, f64>) -> Out {
    let id = case.s("id").unwrap_or_default();
    let state: HashSet<String> = case.arr("state").iter().filter_map(|v| match v {
        J::Str(s) => Some(s.clone()),
        _ => None,
    }).collect();
    let at = case.n("at");

    let mut rules: Vec<Rule> = vec![];
    for r in case.arr("rules") {
        rules.push(Rule {
            id: r.s("id").unwrap_or_default(),
            authority: r.s("authority").unwrap_or_default(),
            condition: r.s("condition").unwrap_or_default(),
            conclusion: r.s("conclusion").unwrap_or_default(),
            rank: r.n("rank").unwrap_or(0.0),
            eff_from: r.n("effective_from"),
            eff_to: r.n("effective_to"),
            requires_construct: if r.is_null("requires_construct") {
                None
            } else {
                r.s("requires_construct")
            },
        });
    }
    let m = rules.len();
    let idx_of: HashMap<String, Vec<usize>> = {
        let mut h: HashMap<String, Vec<usize>> = HashMap::new();
        for (i, r) in rules.iter().enumerate() {
            h.entry(r.id.clone()).or_default().push(i);
        }
        h
    };

    let ids_of = |v: &Vec<usize>| -> Vec<String> {
        let mut o: Vec<String> = v.iter().map(|&i| rules[i].id.clone()).collect();
        o.sort();
        o.dedup();
        o
    };

    let mut o = Out {
        id: id.clone(),
        status: "NONFINDING".into(),
        conclusion: None,
        defeated: vec![],
        uncertainty: "NONE".into(),
        represented_reason: false,
        accepted: vec![],
        trace: vec![],
    };

    // ---- REFUSED: `requires_construct` outside the expressible operation set.
    if let Some(ri) = rules.iter().find(|r| r.requires_construct.is_some()) {
        o.status = "REFUSED".into();
        o.trace.push(format!(
            "REFUSED: rule {} requires construct {}",
            ri.id,
            ri.requires_construct.clone().unwrap()
        ));
        return o;
    }

    // ---- Theta: the triggered rules (node indices).
    let theta: Vec<usize> = (0..m).filter(|&i| triggered(&rules[i], &state, at)).collect();
    if theta.is_empty() {
        o.status = "NONFINDING".into();
        o.trace.push("NONFINDING: no rule triggered at the evaluation time".into());
        return o;
    }
    let mut in_theta = bits_new(m);
    for &i in &theta {
        bits_set(&mut in_theta, i);
    }

    // ---- Build the ATTACK MATRIX: attack[i][j] iff rule i defeats rule j,
    // relation enabled, both endpoints in Theta, basis recognised & satisfied.
    let mut attack: Vec<Bits> = vec![bits_new(m); m];
    let mut trace_edges: Vec<String> = vec![];
    let mut self_defeat: Option<String> = None;
    for d in case.arr("defeats") {
        let defeated = d.s("defeated").unwrap_or_default();
        let defeater = d.s("defeater").unwrap_or_default();
        let basis = d.s("basis").unwrap_or_default();
        let enabled = d.b("enabled").unwrap_or(false);
        let (di, fi) = (idx_of.get(&defeated), idx_of.get(&defeater));
        let (di, fi) = match (di, fi) {
            (Some(a), Some(b)) => (a.clone(), b.clone()),
            _ => {
                trace_edges.push(format!(
                    "reject {}>{}: endpoint(s) not among the rules of this case",
                    defeater, defeated
                ));
                continue;
            }
        };
        if !enabled {
            trace_edges.push(format!("reject {}>{}: relation disabled", defeater, defeated));
            continue;
        }
        match basis_holds(&basis, &rules[fi[0]], &rules[di[0]], arank) {
            None => {
                // Unrecognised basis string: NOT a warrant (CORPUS_FORMAT.md,
                // "Any other basis string is not a warrant").
                trace_edges.push(format!(
                    "reject {}>{}: basis `{}` is not a warrant",
                    defeater, defeated, basis
                ));
                continue;
            }
            Some(false) => {
                // Recognised basis, but its stated test is not satisfied.
                trace_edges.push(format!(
                    "reject {}>{}: basis `{}` does not hold",
                    defeater, defeated, basis
                ));
                continue;
            }
            Some(true) => {}
        }
        // endpoint must be triggered (be in Theta)
        let ok: Vec<usize> = di
            .iter()
            .chain(fi.iter())
            .copied()
            .filter(|&i| bits_get(&in_theta, i))
            .collect();
        if di.iter().any(|&i| !bits_get(&in_theta, i))
            || fi.iter().any(|&i| !bits_get(&in_theta, i))
        {
            trace_edges.push(format!(
                "reject {}>{}: endpoint not triggered, so the pair is not in Theta",
                defeater, defeated
            ));
            continue;
        }
        let _ = ok;
        if defeated == defeater {
            self_defeat = Some(defeated.clone());
        }
        for &a in &fi {
            for &b in &di {
                bits_set(&mut attack[a], b);
            }
        }
        trace_edges.push(format!("active {}>{} [{}]", defeater, defeated, basis));
    }
    o.trace.extend(trace_edges.iter().cloned());

    // ---- §4.4 Self-defeat -> INVALID (a rule defeating itself).
    if let Some(sd) = self_defeat {
        o.status = "INVALID".into();
        o.uncertainty = "CORPUS".into();
        o.trace.push(format!(
            "INVALID: rule `{}` defeats itself; the corpus asserts something incoherent",
            sd
        ));
        return o;
    }

    // ---- Cycle structure, computed independently of the acceptance
    // iteration: Warshall transitive closure of the attack matrix, then
    // strongly-connected components by mutual reachability. (SEMANTICS.md §4.2
    // treats a cycle as its own finding.)
    let reach: Vec<Bits> = {
        let mut r = attack.clone();
        // reflexive closure (path of length zero), so mutual reachability
        // detects singleton cycles as well as longer ones
        for i in 0..m {
            bits_set(&mut r[i], i);
        }
        for k in 0..m {
            for i in 0..m {
                if bits_get(&r[i], k) {
                    let rowk = r[k].clone();
                    bits_or(&mut r[i], &rowk);
                }
            }
        }
        r
    };
    let mut scc: Vec<Vec<usize>> = vec![];
    let mut placed = vec![false; m];
    for i in 0..m {
        if placed[i] || !bits_get(&in_theta, i) {
            continue;
        }
        let mut comp = vec![];
        for j in 0..m {
            if bits_get(&in_theta, j) && bits_get(&reach[i], j) && bits_get(&reach[j], i) {
                comp.push(j);
            }
        }
        for &c in &comp {
            placed[c] = true;
        }
        scc.push(comp);
    }
    let cyclic: Vec<&Vec<usize>> = scc
        .iter()
        .filter(|c| !c.is_empty() && (c.len() > 1 || bits_get(&attack[c[0]], c[0])))
        .collect();
    if !cyclic.is_empty() {
        // SEMANTICS.md 4.2: "Ganymede5 does not resolve cyclic defeat by
        // default." A cycle is reported, not iterated to an answer, even if
        // the operator would happen to stabilise.
        let mut members: Vec<String> = vec![];
        for c in &cyclic {
            for &i in c.iter() {
                members.push(rules[i].id.clone());
            }
        }
        members.sort();
        members.dedup();
        o.trace.push(format!(
            "cycle in the attack relation among {{{}}}; no well-founded argument set",
            members.join(", ")
        ));
        // SEMANTICS.md 4.2: a cycle has no well-founded argument set, so
        // grounded semantics does not determine an answer. Report CONTESTED
        // with uncertainty SEMANTIC, naming the cycle members, and stop. This
        // takes precedence over any outcome the iteration might have reached.
        o.status = "CONTESTED".into();
        o.uncertainty = "SEMANTIC".into();
        o.conclusion = None;
        o.accepted = vec![];
        o.defeated = vec![];
        o.trace.push(
            "CONTESTED/SEMANTIC: cyclic defeat between distinct rules (SEMANTICS.md 4.2)"
                .to_string(),
        );
        return o;
    }

    // ---- Grounded iteration (SEMANTICS.md §3).
    // S0 = Theta ; S(n+1) = { r in Theta : r is unattacked in S(n) },
    // computed as Theta \ (OR of the attack rows of the members of S(n)).
    // Convergence bound 2*|Theta| + 2 (§4.5); exceeding it = no stable fixpoint.
    let bound = 2 * theta.len() + 2;
    let mut cur = in_theta.clone();
    let mut trace_sets: Vec<Bits> = vec![];
    let mut converged: Option<Bits> = None;
    let mut did_converge = false;
    for _n in 0..=bound {
        trace_sets.push(cur.clone());
        let mut attacked = bits_new(m);
        for i in 0..m {
            if bits_get(&cur, i) {
                bits_or(&mut attacked, &attack[i]);
            }
        }
        let mut next = bits_new(m);
        for &i in &theta {
            if !bits_get(&attacked, i) {
                bits_set(&mut next, i);
            }
        }
        if next == cur {
            converged = Some(next);
            did_converge = true;
            break;
        }
        cur = next;
    }
    for (n, s) in trace_sets.iter().enumerate() {
        let ids = ids_of(&(0..m).filter(|&i| bits_get(s, i)).collect());
        o.trace.push(format!("S({}) = {{{}}}", n, ids.join(", ")));
    }

    let accepted_bits = match converged {
        Some(c) => c,
        None => {
            // §4.5 non-convergence: fail closed.
            o.trace
                .push(format!("no stable fixpoint within bound {}", bound));
            o.status = "CONTESTED".into();
            o.uncertainty = "SEMANTIC".into();
            o.conclusion = None;
            o.accepted = vec![];
            o.trace
                .push("CONTESTED/SEMANTIC: the operator has no stable fixpoint (SEMANTICS.md 4.5)".to_string());
            return o;
        }
    };

    let acc: Vec<usize> = (0..m).filter(|&i| bits_get(&accepted_bits, i)).collect();
    let rejected: Vec<usize> = (0..m)
        .filter(|&i| bits_get(&in_theta, i) && !bits_get(&accepted_bits, i))
        .collect();
    o.accepted = ids_of(&acc);
    o.defeated = ids_of(&rejected);

    // ---- Conclusion / status from the grounded set.
    let mut concl: Vec<String> = vec![];
    for &i in &acc {
        let c = rules[i].conclusion.clone();
        if !concl.contains(&c) {
            concl.push(c);
        }
    }
    let contested_by_conclusion = {
        let mut f = false;
        'o: for a in 0..concl.len() {
            for b in (a + 1)..concl.len() {
                if contradiction_pair(&concl[a], &concl[b], contra) {
                    f = true;
                    break 'o;
                }
            }
        }
        f
    };

    if !did_converge {
        // non-convergence
        o.status = "CONTESTED".into();
        o.uncertainty = "SEMANTIC".into();
        o.conclusion = None;
        o.accepted = vec![];
        o.trace.push("CONTESTED/SEMANTIC: the operator has no stable fixpoint".into());
        return o;
    }

    if acc.is_empty() {
        // every triggered rule was defeated
        o.status = "DEFEATED".into();
        o.conclusion = None;
        o.uncertainty = "NONE".into();
        o.represented_reason = true;
        o.trace.push("DEFEATED: the grounded set is empty".into());
        return o;
    }

    if contested_by_conclusion {
        // §4.1: "If the grounded extension is contradiction-free and
        // determinate, report DECIDED; otherwise CONTESTED with
        // uncertainty=CORPUS."  Also covers §4.3 (an extension that admits
        // more than one grounded answer): no preference relation exists and
        // none is invented.
        o.status = "CONTESTED".into();
        o.uncertainty = "CORPUS".into();
        o.conclusion = None;
        o.represented_reason = false;
        o.trace.push(format!(
            "CONTESTED/CORPUS: the grounded set {{{}}} carries contradictory conclusions ({})",
            o.accepted.join(", "),
            concl.join(" vs ")
        ));
        return o;
    }

    // §4.1 acyclic & determinate: a single, contradiction-free grounded set.
    // DECIDED. `represented_reason` = every defeat that removed a rule from
    // the set rested on a recognised, basis-satisfying, enabled relation.
    let all_used = (0..m)
        .filter(|&i| bits_get(&in_theta, i) && !bits_get(&accepted_bits, i))
        .all(|i| {
            (0..m).any(|a| bits_get(&attack[a], i) && bits_get(&in_theta, a))
        });
    o.status = "DECIDED".into();
    o.uncertainty = "NONE".into();
    o.represented_reason = all_used;
    o.conclusion = if concl.len() == 1 { Some(concl[0].clone()) } else { None };
    o.trace
        .push(format!("DECIDED: grounded set {{{}}}", o.accepted.join(", ")));
    o
}

// ------------------------------------------------------------------ main ----

fn esc(s: &str) -> String {
    let mut o = String::from("\"");
    for c in s.chars() {
        match c {
            '"' => o.push_str("\\\""),
            '\\' => o.push_str("\\\\"),
            '\n' => o.push_str("\\n"),
            '\t' => o.push_str("\\t"),
            _ => o.push(c),
        }
    }
    o.push('"');
    o
}

fn main() {
    let args: Vec<String> = std::env::args().collect();
    let inp = args.get(1).cloned().unwrap_or_else(|| {
        concat!(env!("CARGO_MANIFEST_DIR"), "/../corpus_export.json").to_string()
    });
    let outp = args.get(2).cloned().unwrap_or_else(|| {
        concat!(env!("CARGO_MANIFEST_DIR"), "/../impl_b.json").to_string()
    });
    let txt = fs::read_to_string(&inp).expect("cannot read corpus");
    let mut p = P { b: txt.as_bytes(), i: 0 };
    let root = p.val().expect("json parse");

    let contra: HashMap<String, String> = root
        .get("contradicts")
        .map(|c| match c {
            J::Obj(m) => m
                .iter()
                .filter_map(|(k, v)| match v {
                    J::Str(s) => Some((k.clone(), s.clone())),
                    _ => None,
                })
                .collect(),
            _ => HashMap::new(),
        })
        .unwrap_or_default();
    let arank: HashMap<String, f64> = root
        .get("authority_rank")
        .map(|c| match c {
            J::Obj(m) => m
                .iter()
                .filter_map(|(k, v)| match v {
                    J::Num(n) => Some((k.clone(), *n)),
                    _ => None,
                })
                .collect(),
            _ => HashMap::new(),
        })
        .unwrap_or_default();

    let cases = root.arr("cases");
    let mut buf = String::from("[\n");
    for (n, c) in cases.iter().enumerate() {
        let r = solve(c, &contra, &arank);
        if n > 0 {
            buf.push_str(",\n");
        }
        buf.push_str("  {\n");
        buf.push_str(&format!("    \"id\": {},\n", esc(&r.id)));
        buf.push_str(&format!("    \"status\": {},\n", esc(&r.status)));
        buf.push_str(&format!(
            "    \"conclusion\": {},\n",
            match &r.conclusion {
                Some(s) => esc(s),
                None => "null".to_string(),
            }
        ));
        buf.push_str(&format!(
            "    \"defeated\": [{}],\n",
            r.defeated.iter().map(|s| esc(s)).collect::<Vec<_>>().join(", ")
        ));
        buf.push_str(&format!("    \"uncertainty\": {},\n", esc(&r.uncertainty)));
        buf.push_str(&format!(
            "    \"represented_reason\": {},\n",
            r.represented_reason
        ));
        buf.push_str(&format!(
            "    \"accepted\": [{}],\n",
            r.accepted.iter().map(|s| esc(s)).collect::<Vec<_>>().join(", ")
        ));
        buf.push_str(&format!(
            "    \"trace\": [{}]\n",
            r.trace.iter().map(|s| esc(s)).collect::<Vec<_>>().join(", ")
        ));
        buf.push_str("  }");
    }
    buf.push_str("\n]\n");
    fs::write(&outp, buf).expect("cannot write output");
    eprintln!("wrote {} cases to {}", cases.len(), outp);
}
