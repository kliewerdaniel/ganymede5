// impl_d driver.
//
// Reads ../corpus_export.json, runs the engine on every case, writes
// ../impl_d.json (a JSON array, one object per case, in the "Required output"
// shape of CORPUS_FORMAT.md).
//
// No case id appears anywhere in engine.rs. This file also contains no
// case-specific logic; it is generic plumbing.

mod engine;
mod json;
mod selftest;

use std::fs;

fn main() {
    let base = std::env::args()
        .nth(1)
        .unwrap_or_else(|| "..".to_string());
    let corpus_path = format!("{}/corpus_export.json", base);
    let out_path = format!("{}/impl_d.json", base);

    let text = fs::read_to_string(&corpus_path)
        .unwrap_or_else(|e| panic!("cannot read {}: {}", corpus_path, e));
    let doc = json::parse(&text).unwrap_or_else(|e| panic!("cannot parse {}: {}", corpus_path, e));
    let (world, cases) = engine::parse_world(&doc);
    eprintln!("impl_d: {} case(s) from {}", cases.len(), corpus_path);

    let mut out: Vec<String> = Vec::new();
    let mut failures: Vec<String> = Vec::new();
    for c in &cases {
        match engine::run(c, &world) {
            Ok(o) => {
                // Never emit IMPLEMENTATION uncertainty (SEMANTICS.md 2).
                assert_ne!(o.uncertainty, "IMPLEMENTATION", "engine emitted IMPLEMENTATION");
                // Never emit the reserved status (6.1).
                assert_ne!(o.status, "DEFEATED", "engine emitted reserved DEFEATED");
                out.push(engine::to_json(&o));
                eprintln!(
                    "  {:<5} {:<12} {:<9} conclusion={:<6} accepted={:?} rr={}",
                    o.id,
                    o.status,
                    o.uncertainty,
                    o.conclusion.clone().unwrap_or_else(|| "null".into()),
                    o.accepted,
                    o.represented_reason
                );
            }
            Err(op) => {
                // SEMANTICS.md 6.3: an operational error is reported, never
                // converted into an epistemic result.
                eprintln!("  OPERATIONAL ERROR: {}", op.0);
                failures.push(op.0);
            }
        }
    }

    if !failures.is_empty() {
        eprintln!("impl_d: {} operational error(s); refusing to write results", failures.len());
        std::process::exit(2);
    }

    fs::write(
        &out_path,
        format!("[\n{}\n]\n", out.join(",\n")),
    )
    .unwrap_or_else(|e| panic!("cannot write {}: {}", out_path, e));
    eprintln!("impl_d: wrote {} case(s) to {}", out.len(), out_path);

    // ---- self-tests ------------------------------------------------------
    let t = selftest::run(&world, &cases);
    for line in &t.log {
        println!("{}", line);
    }
    eprintln!(
        "impl_d: self-test {} — {} passed, {} failed",
        if t.failed == 0 { "PASS" } else { "FAIL" },
        t.passed,
        t.failed
    );
    if t.failed > 0 {
        std::process::exit(1);
    }
}