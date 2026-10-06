use cott::{
    compiler::{SourceFile, parse_project},
    hir::lower,
    ir::{CanonicalIr, render},
};
use serde_json::Value;
use std::{
    fs,
    path::{Path, PathBuf},
    process::Command,
};

fn corpus() -> Vec<Value> {
    serde_json::from_str(include_str!("fixtures/ready_ordered.json")).unwrap()
}
#[path = "../src/rust/runtime/graph.rs"]
mod graph_runtime;
#[test]
fn shared_graph_corpus_and_long_chain_are_finite() {
    for case in corpus() {
        let nodes = case["nodes"]
            .as_array()
            .unwrap()
            .iter()
            .map(|v| {
                (
                    v[0].as_str().unwrap().to_owned(),
                    v[1].as_array()
                        .unwrap()
                        .iter()
                        .map(|s| s.as_str().unwrap().to_owned())
                        .collect::<Vec<_>>(),
                )
            })
            .collect::<Vec<_>>();
        let order = case["order"]
            .as_array()
            .unwrap()
            .iter()
            .map(|v| v.as_str().unwrap().to_owned())
            .collect::<Vec<_>>();
        let result = graph_runtime::ready_ordered_by(
            &order,
            &nodes,
            |n| n.0.as_str(),
            |n| n.1.iter().map(String::as_str),
        );
        assert_eq!(
            result,
            case["expected"].as_bool().unwrap(),
            "{}",
            case["name"]
        );
        let reversed = nodes.into_iter().rev().collect::<Vec<_>>();
        assert_eq!(
            result,
            graph_runtime::ready_ordered_by(
                &order,
                &reversed,
                |n| n.0.as_str(),
                |n| n.1.iter().map(String::as_str)
            )
        );
    }
    let nodes = (0..10000)
        .map(|i| {
            (
                i.to_string(),
                if i == 0 {
                    vec![]
                } else {
                    vec![(i - 1).to_string()]
                },
            )
        })
        .collect::<Vec<_>>();
    let order = nodes.iter().map(|n| n.0.clone()).collect::<Vec<_>>();
    assert!(graph_runtime::ready_ordered_by(
        &order,
        &nodes,
        |n| n.0.as_str(),
        |n| n.1.iter().map(String::as_str)
    ));
}

fn source() -> String {
    let mut source = "module graph\n\n".to_owned();
    for collection in ["List", "Set"] {
        let tag = collection.to_lowercase();
        let ty = format!("Step{collection}");
        source.push_str(&format!("struct {ty}:\n    name: Str\n    needs: {collection}[Str]\n\nfn decide_{tag}(order: List[Str], steps: List[{ty}], expected: Bool) -> Bool:\n    requires expected == ready_ordered_by(order, steps, {ty}.name, {ty}.needs)\n    ensures result == ready_ordered_by(order, steps, {ty}.name, {ty}.needs)\n\n"));
        for case in corpus() {
            let strings = |v: &Value| {
                v.as_array()
                    .unwrap()
                    .iter()
                    .map(|s| serde_json::to_string(s).unwrap())
                    .collect::<Vec<_>>()
                    .join(", ")
            };
            let nodes = case["nodes"]
                .as_array()
                .unwrap()
                .iter()
                .map(|v| {
                    let deps = if collection == "Set" {
                        v[1].as_array()
                            .unwrap()
                            .iter()
                            .map(|v| v.to_string())
                            .collect::<std::collections::BTreeSet<_>>()
                            .into_iter()
                            .collect::<Vec<_>>()
                            .join(", ")
                    } else {
                        strings(&v[1])
                    };
                    format!("{ty}(name: {}, needs: {collection}({deps}))", v[0])
                })
                .collect::<Vec<_>>()
                .join(", ");
            source.push_str(&format!("scenario {tag}_{}:\n    data steps: List[{ty}] = List({nodes})\n    data order: List[Str] = List({})\n    call actual = decide_{tag}(order, steps, {})\n    assert actual == {}\n    assert ready_ordered_by(order, steps, {ty}.name, {ty}.needs) == {}\n\n",case["name"].as_str().unwrap(),strings(&case["order"]),case["expected"],case["expected"],case["expected"]));
        }
    }
    source.push_str("requirement READY_MINIMUM for decide_list:\n    text \"Select the Unicode scalar minimum among currently ready steps; observed checks do not prove the entire requirement.\"\n    checked_by list_new_minimum\n    checked_by list_unicode_scalar\n");
    source
}
fn ir(source: &str) -> CanonicalIr {
    let parsed = parse_project([SourceFile::new("graph.cott", source)]).unwrap();
    render(&lower(Path::new("src"), parsed).unwrap()).unwrap()
}
#[test]
fn ready_ordered_is_closed_typed_formatted_and_proof_unknown() {
    let src = source();
    let parsed = parse_project([SourceFile::new("graph.cott", src.as_str())]).unwrap();
    let formatted =
        cott::formatter::format(&parsed.sources[0].cst, &parsed.sources[0].syntax).unwrap();
    assert_eq!(
        ir(std::str::from_utf8(&formatted).unwrap()).modules.len(),
        1
    );
    let value: Value = serde_json::from_slice(&ir(&src).modules[0].bytes).unwrap();
    let function = value["declarations"]
        .as_array()
        .unwrap()
        .iter()
        .find(|d| d["name"] == "graph.decide_list")
        .unwrap();
    assert_eq!(
        function["contract"]["clauses"][0]["expression"]["operands"][1]["name"],
        "ready_ordered_by"
    );
    let proof = cott::proof::prove_contracts(&ir(&src), None, &Default::default()).unwrap();
    assert!(proof.to_string().contains("unknown"));
    for (from, to) in [
        ("StepList.name", "StepList.needs"),
        ("StepList.needs)", "StepList.name)"),
        ("order: List[Str]", "order: List[I32]"),
    ] {
        let invalid = src.replace(from, to);
        let parsed = parse_project([SourceFile::new("graph.cott", invalid.as_str())]).unwrap();
        assert!(lower(Path::new("src"), parsed).is_err(), "{from} => {to}");
    }
    fn tamper(v: &mut Value, kind: u8) {
        if v["kind"] == "intrinsic" && v["name"] == "ready_ordered_by" {
            match kind {
                0 => v["name"] = "arbitrary_user_function".into(),
                1 => v["arguments"]
                    .as_array_mut()
                    .unwrap()
                    .pop()
                    .map(|_| ())
                    .unwrap(),
                _ => v["dependencies"]["owner"] = "Other".into(),
            }
        } else {
            match v {
                Value::Array(a) => {
                    for v in a {
                        tamper(v, kind)
                    }
                }
                Value::Object(o) => {
                    for v in o.values_mut() {
                        tamper(v, kind)
                    }
                }
                _ => (),
            }
        }
    }
    for kind in 0..3 {
        let mut bad = value.clone();
        tamper(&mut bad, kind);
        assert!(cott::ir::canonical_bytes(&bad).is_err());
    }
}

fn absolute(name: &str) -> PathBuf {
    let p = PathBuf::from(std::env::var_os(name).unwrap_or_else(|| panic!("required {name}")));
    assert!(p.is_absolute());
    p
}
fn put(root: &Path, path: &str, text: &str) {
    let p = root.join(path);
    fs::create_dir_all(p.parent().unwrap()).unwrap();
    fs::write(p, text).unwrap();
}
fn run(root: &Path, args: &[&str]) -> std::process::Output {
    Command::new(env!("CARGO_BIN_EXE_cott"))
        .args(args)
        .arg("--project")
        .arg(root)
        .env("PUB_CACHE", root.join("pub-cache"))
        .output()
        .unwrap()
}
fn okay(out: std::process::Output) {
    assert!(
        out.status.success(),
        "{}\n{}",
        String::from_utf8_lossy(&out.stdout),
        String::from_utf8_lossy(&out.stderr)
    );
}
fn native(target: &str) {
    let root = std::env::temp_dir().join(format!("cott-ready-{target}-{}", std::process::id()));
    fs::create_dir(&root).unwrap();
    fs::create_dir(root.join("pub-cache")).unwrap();
    let project = if matches!(target, "python" | "kotlin") {
        "ready-graph"
    } else {
        "ready_graph"
    };
    let src = source();
    put(&root, "src/graph.cott", &src);
    let ir = ir(&src);
    let mut manifest = format!(
        "[project]\nname={project:?}\nversion=\"0.1.0\"\nsource=\"src\"\n[target.{target}]\nsource=\"{target}\"\ngenerated=\"generated/{target}\"\nruntime_validation=\"boundary\"\n"
    );
    let mut implementations = String::new();
    let mut files = Vec::new();
    match target {
        "rust" => {
            manifest.push_str(&format!(
                "cargo={:?}\nrustc={:?}\n",
                absolute("COTT_CARGO"),
                absolute("COTT_RUSTC")
            ));
            let plan = cott::rust::RustPlan::from_ir(&ir).unwrap();
            for c in plan.callables() {
                let path = format!("{target}/bindings/{}.rs", c.name);
                put(
                    &root,
                    &path,
                    &format!(
                        "{} {{ let _ = (order, steps); expected }}\n",
                        cott::rust::emit::implementation_signature(&plan, c).unwrap()
                    ),
                );
                files.push(path);
                implementations.push_str(&format!(
                    "{:?}={:?}\n",
                    c.symbol,
                    format!("bindings/{}.rs:{}", c.name, c.name)
                ));
            }
        }
        "kotlin" => {
            manifest.push_str(&format!(
                "compiler={:?}\njava={:?}\njvm_target=17\n",
                absolute("COTT_KOTLIN_HOME").join("bin/kotlinc"),
                absolute("JAVA_HOME").join("bin/java")
            ));
            let plan = cott::kotlin::KotlinPlan::from_ir(&ir).unwrap();
            for c in plan.callables() {
                let path = format!("kotlin/bindings/{}.kt", c.name);
                put(
                    &root,
                    &path,
                    &format!(
                        "package bindings\n{} {{ return expected }}\n",
                        cott::kotlin::emit::implementation_signature(&plan, &c).unwrap()
                    ),
                );
                files.push(path);
                implementations.push_str(&format!(
                    "{:?}={:?}\n",
                    c.symbol,
                    format!("bindings.{}", c.name)
                ));
            }
        }
        "dart" => {
            manifest.push_str(&format!("sdk={:?}\n", absolute("COTT_DART")));
            let plan = cott::dart::DartPlan::from_ir(&ir).unwrap();
            for c in plan.callables() {
                let name = format!("_{}", c.name);
                let signature = cott::dart::emit::implementation_signature(&plan, c)
                    .unwrap()
                    .replacen(&format!("_cott_{}", c.symbol.replace('.', "_")), &name, 1);
                let path = format!("dart/bindings/{}.dart", c.name);
                put(
                    &root,
                    &path,
                    &format!("{signature} {{ return expected; }}\n"),
                );
                files.push(path);
                implementations.push_str(&format!(
                    "{:?}={:?}\n",
                    c.symbol,
                    format!("bindings/{}.dart:{name}", c.name)
                ));
            }
        }
        "python" => {
            fs::create_dir(root.join("tools")).unwrap();
            std::os::unix::fs::symlink(absolute("COTT_PYTHON"), root.join("tools/python")).unwrap();
            std::os::unix::fs::symlink(
                absolute("COTT_BASEDPYRIGHT"),
                root.join("tools/basedpyright"),
            )
            .unwrap();
            manifest.push_str("interpreter=\"tools/python\"\ntype_checker=\"tools/basedpyright\"\nstubs=\"generated/stubs\"\n");
            put(
                &root,
                "python/pyproject.toml",
                "[project]\nname=\"ready-graph\"\nversion=\"0.1.0\"\nrequires-python=\">=3.14.6,<3.15\"\ndependencies=[]\n",
            );
            for kind in ["List", "Set"] {
                let name = format!("decide_{}", kind.to_lowercase());
                let path = format!("python/cott_bindings/{name}.py");
                put(
                    &root,
                    &path,
                    &format!(
                        "from cott_runtime import CottList\nfrom graph import Step{kind}\ndef {name}(order: CottList[str], steps: CottList[Step{kind}], expected: bool) -> bool:\n    return expected\n"
                    ),
                );
                files.push(path);
                implementations.push_str(&format!(
                    "\"graph.{name}\"=\"cott_bindings.{name}:{name}\"\n"
                ));
            }
        }
        _ => unreachable!(),
    }
    manifest.push_str(&format!(
        "\n[target.{target}.implementations]\n{implementations}"
    ));
    put(&root, "cott.toml", &manifest);
    okay(run(&root, &["check"]));
    okay(run(&root, &["fmt"]));
    let prompt = run(&root, &["prompt", "graph.decide_list", "--format", "json"]);
    assert!(
        prompt.status.success(),
        "{}\n{}",
        String::from_utf8_lossy(&prompt.stdout),
        String::from_utf8_lossy(&prompt.stderr)
    );
    let text = String::from_utf8(prompt.stdout).unwrap();
    assert!(text.contains("ready_ordered_by"));
    okay(run(&root, &["emit", target]));
    okay(run(&root, &["verify"]));
    let record: Value =
        serde_json::from_slice(&fs::read(root.join("generated/generation.json")).unwrap()).unwrap();
    assert_eq!(record["current"], record["last_verified"]);
    let snap = &record["snapshots"][record["current"].as_str().unwrap()];
    assert_eq!(snap["verified"], true);
    let scenarios = snap["verification"]["contract_tests"]["scenarios"]
        .as_array()
        .unwrap();
    assert_eq!(scenarios.len(), corpus().len() * 2);
    for scenario in scenarios {
        if target == "python" {
            assert_eq!(scenario["grade"], "test observation");
        } else {
            assert_eq!(scenario["status"], "passed");
            assert_eq!(scenario["assertions"], 2);
            let observations = scenario["observations"].as_array().unwrap();
            for id in ["requires:0", "ensures:1"] {
                assert!(
                    observations
                        .iter()
                        .any(|o| o["clause"] == id && o["passed"] == true),
                    "{target} {scenario}"
                );
            }
        }
    }
    // Actual facade clause observations, not inferred from the successful scenario report.
    for symbol in ["graph.decide_list", "graph.decide_set"] {
        let clauses = snap["semantic_coverage"]["clauses"].as_array().unwrap();
        for id in ["requires:0", "ensures:1"] {
            let c = clauses
                .iter()
                .find(|v| v["symbol"] == symbol && v["clause_id"] == id)
                .unwrap();
            assert_eq!(c["status"], "observed");
            assert!(
                c["evidence"]
                    .as_array()
                    .unwrap()
                    .iter()
                    .any(|e| if target == "python" {
                        e["grade"] == "test observation"
                            && e["valid_cases"].as_u64().unwrap_or(0) > 0
                    } else {
                        e["status"] == "passed" && e["positive_applicable"] == true
                    }),
                "{target} {symbol} {id}: {c}"
            );
        }
    }
    if let Some(out) = std::env::var_os("COTT_READY_EVIDENCE") {
        let out = PathBuf::from(out);
        fs::create_dir_all(&out).unwrap();
        fs::write(
            out.join(format!("{target}-verified.json")),
            serde_json::to_vec_pretty(&record).unwrap(),
        )
        .unwrap();
    }
    // Changing only an authored binding must be rejected at the exact ensures clause by real verify.
    let p = root.join(&files[0]);
    let text = fs::read_to_string(&p).unwrap();
    let wrong = if target == "python" {
        text.replace("return expected", "return not expected")
    } else {
        text.replace("expected }", "!expected }")
            .replace("return expected;", "return !expected;")
    };
    assert_ne!(text, wrong);
    fs::write(&p, wrong).unwrap();
    okay(run(&root, &["emit", target]));
    let bad = run(&root, &["verify"]);
    assert!(!bad.status.success());
    let stderr = String::from_utf8_lossy(&bad.stderr);
    assert!(
        stderr.contains("ensures") || stderr.contains("contract"),
        "{target}: {stderr}"
    );
    let failed: Value =
        serde_json::from_slice(&fs::read(root.join("generated/generation.json")).unwrap()).unwrap();
    assert_eq!(failed["last_verified"], record["last_verified"]);
    assert_eq!(
        failed["snapshots"][failed["current"].as_str().unwrap()]["verified"],
        false
    );
    if let Some(out) = std::env::var_os("COTT_READY_EVIDENCE") {
        fs::write(
            PathBuf::from(out).join(format!("{target}-rejected.txt")),
            stderr.as_bytes(),
        )
        .unwrap();
    }
    fs::remove_dir_all(root).unwrap();
}
#[test]
#[ignore = "requires real supported Python and BasedPyright"]
fn native_ready_python() {
    native("python")
}
#[test]
#[ignore = "requires absolute COTT_CARGO/COTT_RUSTC"]
fn native_ready_rust() {
    native("rust")
}
#[test]
#[ignore = "requires actual Kotlin>=2.2.10 and JDK17"]
fn native_ready_kotlin() {
    native("kotlin")
}
#[test]
#[ignore = "requires actual supported Dart SDK"]
fn native_ready_dart() {
    native("dart")
}
