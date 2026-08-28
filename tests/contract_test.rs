use std::fs;
use std::io::Write;
use std::path::PathBuf;
use std::process::{Command, Stdio};

use cott::contract_test::{Classification, ContractTestStrategy, derive_strategies};
use cott::hash::sha256_hex;
use cott::hir::ModuleId;
use cott::ir::{CanonicalIr, CanonicalModule, canonical_bytes};
use cott::python_runtime::render_runtime;
use serde_json::{Value, json};

#[test]
fn strategy_has_fixed_deterministic_limits() {
    let strategy = ContractTestStrategy::new(
        "foo.bar.run",
        b"canonical-ir",
        "sync",
        Classification::Pure,
        vec!["requires:0".to_owned()],
    );
    assert_eq!(strategy.candidate_limit, 64);
    assert_eq!(strategy.node_limit, 64);
    assert_eq!(strategy.container_length_limit, 3);
    assert_eq!(strategy.json_depth_limit, 4);
    assert_eq!(strategy.lifecycle_limit, 3);
    assert_eq!(strategy.return_kind, "value");
    let bytes = strategy.bytes().expect("schema-valid strategy");
    assert!(
        String::from_utf8(bytes)
            .expect("UTF-8")
            .contains("\"symbol\":\"foo.bar.run\"")
    );
}

fn span() -> Value {
    json!({
        "end_byte": 1,
        "end_column": 2,
        "end_line": 1,
        "start_byte": 0,
        "start_column": 1,
        "start_line": 1
    })
}

fn literal_expression() -> Value {
    json!({
        "kind": "literal",
        "reference": null,
        "span": span(),
        "type": {"kind": "primitive", "name": "bool"},
        "value": {"kind": "bool", "value": true}
    })
}

fn function(symbol: &str, return_name: &str, effects: &[&str], clauses: &[(&str, u64)]) -> Value {
    let clauses = clauses
        .iter()
        .map(|(kind, clause_id)| match *kind {
            "requires" => json!({
                "clause_id": clause_id,
                "expression": literal_expression(),
                "guard": null,
                "kind": "requires",
                "span": span()
            }),
            "ensures" => json!({
                "clause_id": clause_id,
                "expression": literal_expression(),
                "guard": null,
                "kind": "ensures",
                "span": span()
            }),
            _ => panic!("test clause kind"),
        })
        .collect::<Vec<_>>();
    let effects = effects
        .iter()
        .enumerate()
        .map(
            |(source_order, key)| json!({"key": key, "source_order": source_order, "span": span()}),
        )
        .collect::<Vec<_>>();
    json!({
        "annotations": [],
        "body": null,
        "contract": {"clauses": clauses, "effects": effects},
        "doc": null,
        "generics": [],
        "callable_kind": "sync",
        "kind": "function",
        "name": symbol,
        "parameters": [],
        "public": true,
        "return_type": {"kind": "primitive", "name": return_name},
        "source_order": 0,
        "span": span()
    })
}

fn impl_clause(kind: &str, clause_id: u64) -> Value {
    match kind {
        "requires" => json!({
            "clause_id": clause_id,
            "expression": literal_expression(),
            "guard": null,
            "kind": "requires",
            "span": span()
        }),
        "ensures" => json!({
            "clause_id": clause_id,
            "expression": literal_expression(),
            "guard": null,
            "kind": "ensures",
            "span": span()
        }),
        "error" => json!({
            "clause_id": clause_id,
            "guard": null,
            "kind": "error",
            "priority": null,
            "span": span(),
            "variant": "fixture.Failure",
            "when": null
        }),
        _ => panic!("test impl clause kind"),
    }
}

fn impl_method(
    name: &str,
    return_name: &str,
    effects: &[&str],
    modifies: &[&str],
    requires: &[u64],
    ensures: &[u64],
    errors: &[u64],
) -> Value {
    let effects = effects
        .iter()
        .enumerate()
        .map(
            |(source_order, key)| json!({"key": key, "source_order": source_order, "span": span()}),
        )
        .collect::<Vec<_>>();
    json!({
        "contracts": {
            "doc": null,
            "ensures": ensures.iter().map(|id| impl_clause("ensures", *id)).collect::<Vec<_>>(),
            "errors": errors.iter().map(|id| impl_clause("error", *id)).collect::<Vec<_>>(),
            "requires": requires.iter().map(|id| impl_clause("requires", *id)).collect::<Vec<_>>()
        },
        "effects": effects,
        "modifies": modifies,
        "name": name,
        "callable_kind": "sync",
        "parameters": [],
        "return_type": {"kind": "primitive", "name": return_name},
        "span": span(),
        "transitions": []
    })
}

fn implementation(
    name: &str,
    init: Option<(Vec<u64>, Vec<u64>)>,
    invariants: &[u64],
    methods: Vec<Value>,
) -> Value {
    let init = init.map_or(Value::Null, |(requires, ensures)| {
        json!({
            "contracts": {
                "doc": null,
                "ensures": ensures.iter().map(|id| impl_clause("ensures", *id)).collect::<Vec<_>>(),
                "requires": requires.iter().map(|id| impl_clause("requires", *id)).collect::<Vec<_>>()
            },
            "parameters": [],
            "span": span()
        })
    });
    let (module, implementation) = name.rsplit_once('.').expect("qualified impl name");
    let selected_methods = methods
        .iter()
        .map(|method| {
            let method_name = method["name"].as_str().expect("method name");
            json!({
                "callable_kind": method["callable_kind"],
                "parameters": method["parameters"],
                "receiver_type": {"args": [], "kind": "named", "name": name},
                "return_type": method["return_type"],
                "selected": {
                    "function": {
                        "module": module,
                        "symbol": format!("{implementation}.{method_name}"),
                        "verified_facade": format!("{name}.{method_name}")
                    },
                    "origin": "explicit"
                },
                "trait_method": format!("fixture.Counter.{method_name}"),
                "trait_ref": {"args": [], "kind": "named", "name": "fixture.Counter"}
            })
        })
        .collect::<Vec<_>>();
    json!({
        "annotations": [],
        "doc": null,
        "generics": [],
        "associated_types": [],
        "init": init,
        "invariants": invariants.iter().map(|clause_id| json!({
            "clause_id": clause_id,
            "expression": literal_expression(),
            "span": span(),
            "guard": null
        })).collect::<Vec<_>>(),
        "kind": "impl",
        "methods": methods,
        "name": name,
        "public": true,
        "source_order": 0,
        "span": span(),
        "state": [],
        "traits": [{"args": [], "kind": "named", "name": "fixture.Counter"}],
        "selected_methods": selected_methods,
    })
}

fn module(name: &str, declarations: Vec<Value>) -> CanonicalModule {
    let value = json!({
        "declarations": declarations,
        "imports": [],
        "module": name,
        "schema_version": 7,
        "source": format!("{name}.cott")
    });
    CanonicalModule {
        module: ModuleId::new(name.split('.').map(str::to_owned).collect()),
        source: PathBuf::from(format!("{name}.cott")),
        bytes: canonical_bytes(&value).expect("valid canonical module"),
    }
}

#[test]
fn derived_strategy_bytes_are_deterministic_in_module_declaration_order() {
    let ir = CanonicalIr {
        modules: vec![
            module(
                "first",
                vec![
                    function("first.z", "bool", &[], &[]),
                    function("first.a", "bool", &[], &[]),
                ],
            ),
            module("second", vec![function("second.run", "bool", &[], &[])]),
        ],
    };
    let first = derive_strategies(&ir).expect("canonical IR strategies");
    let second = derive_strategies(&ir).expect("canonical IR strategies");
    assert_eq!(first, second);
    assert_eq!(
        first
            .iter()
            .map(|strategy| strategy.symbol.as_str())
            .collect::<Vec<_>>(),
        ["first.z", "first.a", "second.run"]
    );
    let first_bytes = first
        .iter()
        .map(|strategy| strategy.bytes().expect("schema-valid strategy"))
        .collect::<Vec<_>>();
    let second_bytes = second
        .iter()
        .map(|strategy| strategy.bytes().expect("schema-valid strategy"))
        .collect::<Vec<_>>();
    assert_eq!(first_bytes, second_bytes);
}

#[test]
fn derived_strategy_seed_hashes_canonical_module_bytes() {
    let ir = CanonicalIr {
        modules: vec![module(
            "seeded",
            vec![function("seeded.run", "bool", &[], &[])],
        )],
    };
    let strategies = derive_strategies(&ir).expect("canonical IR strategies");
    let strategy = &strategies[0];
    assert_eq!(
        strategy.seed,
        format!("sha256:{}", sha256_hex(&ir.modules[0].bytes))
    );
}

#[test]
fn derived_strategy_clause_ids_preserve_source_order() {
    let ir = CanonicalIr {
        modules: vec![module(
            "clauses",
            vec![function(
                "clauses.check",
                "bool",
                &[],
                &[("requires", 4), ("ensures", 9), ("requires", 12)],
            )],
        )],
    };
    let strategies = derive_strategies(&ir).expect("canonical IR strategies");
    let strategy = &strategies[0];
    assert_eq!(
        strategy.clause_ids,
        ["requires:4", "ensures:9", "requires:12"]
    );
}

#[test]
fn derived_strategy_classifies_pure_effectful_and_never() {
    let ir = CanonicalIr {
        modules: vec![module(
            "classify",
            vec![
                function("classify.pure", "bool", &[], &[]),
                function("classify.effectful", "unit", &["io"], &[]),
                function("classify.never", "never", &["io"], &[]),
            ],
        )],
    };
    let strategies = derive_strategies(&ir).expect("canonical IR strategies");
    assert_eq!(
        strategies
            .iter()
            .map(|strategy| strategy.classification)
            .collect::<Vec<_>>(),
        [
            Classification::Pure,
            Classification::Effectful,
            Classification::Never
        ]
    );
    assert!(
        strategies
            .iter()
            .all(|strategy| strategy.callable_kind == "sync")
    );
}

#[test]
fn derived_free_function_strategy_carries_async_callable_kind() {
    let mut declaration = function("async_fixture.run", "bool", &[], &[]);
    declaration["callable_kind"] = json!("async");
    let strategy = derive_strategies(&CanonicalIr {
        modules: vec![module("async_fixture", vec![declaration])],
    })
    .expect("async function strategy")
    .pop()
    .expect("one strategy");
    assert_eq!(strategy.callable_kind, "async");
}

#[test]
fn derived_impl_strategy_carries_async_callable_and_protocol_return_kinds() {
    let mut method = impl_method("stream", "unit", &[], &[], &[], &[], &[]);
    method["callable_kind"] = json!("async");
    method["return_type"] = json!({
        "kind": "async_generator",
        "send": {"kind": "primitive", "name": "i32"},
        "yield": {"kind": "primitive", "name": "bool"},
    });
    let strategy = derive_strategies(&CanonicalIr {
        modules: vec![module(
            "fixture",
            vec![implementation(
                "fixture.Stream",
                Some((vec![], vec![])),
                &[],
                vec![method],
            )],
        )],
    })
    .expect("async impl strategy")
    .into_iter()
    .find(|strategy| strategy.symbol == "fixture.Stream.stream")
    .expect("method strategy");
    assert_eq!(strategy.callable_kind, "async");
    assert_eq!(strategy.return_kind, "async_generator");
}

#[test]
fn derived_async_iterator_strategy_carries_protocol_return_kind() {
    let mut declaration = function("async_fixture.stream", "unit", &[], &[]);
    declaration["return_type"] = json!({
        "kind": "async_iterator",
        "item": {"kind": "primitive", "name": "bool"},
    });
    let strategy = derive_strategies(&CanonicalIr {
        modules: vec![module("async_fixture", vec![declaration])],
    })
    .expect("async iterator strategy")
    .pop()
    .expect("one strategy");
    assert_eq!(strategy.return_kind, "async_iterator");
}

#[test]
fn derived_impl_strategies_follow_canonical_member_order_and_cover_all_clauses() {
    let ir = CanonicalIr {
        modules: vec![module(
            "fixture",
            vec![
                function("fixture.before", "bool", &[], &[]),
                implementation(
                    "fixture.Explicit",
                    Some((vec![5], vec![2])),
                    &[3, 7],
                    vec![
                        impl_method("observe", "bool", &[], &[], &[4], &[6], &[1]),
                        impl_method(
                            "write",
                            "unit",
                            &["io"],
                            &["fixture.Explicit.count", "fixture.Explicit.total"],
                            &[],
                            &[],
                            &[],
                        ),
                        impl_method("abort", "never", &["io"], &[], &[], &[], &[]),
                    ],
                ),
                implementation(
                    "fixture.Implicit",
                    None,
                    &[0],
                    vec![impl_method("read", "bool", &[], &[], &[], &[], &[])],
                ),
                function("fixture.after", "bool", &[], &[]),
            ],
        )],
    };

    let strategies = derive_strategies(&ir).expect("canonical impl strategies");
    assert_eq!(
        strategies
            .iter()
            .map(|strategy| strategy.symbol.as_str())
            .collect::<Vec<_>>(),
        [
            "fixture.before",
            "fixture.Explicit.init",
            "fixture.Explicit.observe",
            "fixture.Explicit.write",
            "fixture.Explicit.abort",
            "fixture.Implicit.init",
            "fixture.Implicit.read",
            "fixture.after",
        ]
    );
    assert_eq!(
        strategies
            .iter()
            .map(|strategy| strategy.classification)
            .collect::<Vec<_>>(),
        [
            Classification::Pure,
            Classification::Pure,
            Classification::Pure,
            Classification::Effectful,
            Classification::Never,
            Classification::Pure,
            Classification::Pure,
            Classification::Pure,
        ]
    );
    assert_eq!(
        strategies[1].clause_ids,
        ["ensures:2", "requires:5", "invariant:3", "invariant:7"]
    );
    assert_eq!(
        strategies[2].clause_ids,
        [
            "error:1",
            "requires:4",
            "ensures:6",
            "invariant:3",
            "invariant:7",
        ]
    );
    assert_eq!(
        strategies[3].clause_ids,
        [
            "modifies:fixture.Explicit.count",
            "modifies:fixture.Explicit.total",
            "invariant:3",
            "invariant:7",
        ]
    );
    assert_eq!(strategies[5].clause_ids, ["invariant:0"]);
}
#[test]
fn selected_slots_resolve_explicit_and_concrete_default_signatures() {
    let trait_method = json!({
        "contract": {
            "clauses": [impl_clause("ensures", 11)],
            "effects": []
        },
        "default": {
            "module": "fixture",
            "symbol": "Default.read",
            "verified_facade": "fixture.Default.read"
        },
        "doc": null,
        "generics": [],
        "callable_kind": "sync",
        "kind": "method",
        "name": "Default.read",
        "parameters": [],
        "public": true,
        "return_type": {"kind": "type_parameter", "name": "T"},
        "source_order": 0,
        "span": span()
    });
    let trait_declaration = json!({
        "annotations": [],
        "doc": null,
        "generics": [{
            "bounds": [],
            "kind": "type",
            "name": "T",
            "source_order": 0,
            "span": span(),
            "variance": "invariant"
        }],
        "kind": "trait",
        "associated_types": [],
        "closure": [],
        "methods": [trait_method],
        "parents": [],
        "name": "fixture.Default",
        "public": true,
        "source_order": 0,
        "span": span()
    });
    let implementation = json!({
        "annotations": [],
        "doc": null,
        "generics": [],
        "associated_types": [],
        "init": null,
        "invariants": [],
        "kind": "impl",
        "methods": [],
        "name": "fixture.UsesDefault",
        "public": true,
        "selected_methods": [{
            "callable_kind": "sync",
            "parameters": [],
            "receiver_type": {"args": [], "kind": "named", "name": "fixture.UsesDefault"},
            "return_type": {"kind": "primitive", "name": "never"},
            "selected": {
                "function": {
                    "module": "fixture",
                    "symbol": "Default.fallback",
                    "verified_facade": "fixture.Default.fallback"
                },
                "origin": "default"
            },
            "trait_method": "fixture.Default.read",
            "trait_ref": {
                "args": [{"kind": "type", "type": {"kind": "primitive", "name": "never"}}],
                "kind": "named",
                "name": "fixture.Default"
            }
        }],
        "source_order": 1,
        "span": span(),
        "state": [],
        "traits": [{
            "args": [{"kind": "type", "type": {"kind": "primitive", "name": "never"}}],
            "kind": "named",
            "name": "fixture.Default"
        }]
    });
    let ir = CanonicalIr {
        modules: vec![module("fixture", vec![trait_declaration, implementation])],
    };
    let strategies = derive_strategies(&ir).expect("selected strategies");
    assert_eq!(
        strategies
            .iter()
            .map(|strategy| strategy.symbol.as_str())
            .collect::<Vec<_>>(),
        ["fixture.UsesDefault.init", "fixture.UsesDefault.read"]
    );
    assert_eq!(strategies[1].classification, Classification::Never);
    assert_eq!(strategies[1].clause_ids, ["ensures:11"]);
}

#[test]
fn selected_slots_coalesce_inherited_specializations_in_diamonds() {
    let method = json!({
        "contract": {"clauses": [impl_clause("ensures", 19)], "effects": []},
        "default": null,
        "doc": null,
        "generics": [],
        "callable_kind": "sync",
        "kind": "method",
        "name": "fixture.Parent.read",
        "parameters": [],
        "public": true,
        "return_type": {"kind": "primitive", "name": "bool"},
        "source_order": 0,
        "span": span()
    });
    let parent = json!({
        "annotations": [], "doc": null, "generics": [], "kind": "trait",
        "associated_types": [], "closure": [], "methods": [method], "name": "fixture.Parent",
        "parents": [], "public": true, "source_order": 0, "span": span()
    });
    let child = json!({
        "annotations": [], "doc": null, "generics": [], "kind": "trait",
        "associated_types": [], "closure": [{"args": [], "kind": "named", "name": "fixture.Parent"}],
        "methods": [], "name": "fixture.Child",
        "parents": [{
            "source_order": 0,
            "span": span(),
            "trait": {"args": [], "kind": "named", "name": "fixture.Parent"}
        }],
        "public": true, "source_order": 1, "span": span()
    });
    let selected = json!({
        "callable_kind": "sync",
        "parameters": [],
        "receiver_type": {"args": [], "kind": "named", "name": "fixture.Concrete"},
        "return_type": {"kind": "primitive", "name": "bool"},
        "selected": {
            "origin": "specialization",
            "function": {
                "module": "fixture", "symbol": "specialized_read",
                "verified_facade": "fixture.specialized_read"
            },
            "specialization": "fixture.specialized_read"
        },
        "trait_method": "fixture.Parent.read",
        "trait_ref": {"args": [], "kind": "named", "name": "fixture.Parent"}
    });
    let implementation = json!({
        "annotations": [], "doc": null, "generics": [], "associated_types": [],
        "init": null, "invariants": [], "kind": "impl", "methods": [],
        "name": "fixture.Concrete", "public": true,
        "selected_methods": [selected.clone(), selected],
        "source_order": 2, "span": span(), "state": [],
        "traits": [{"args": [], "kind": "named", "name": "fixture.Child"}]
    });
    let strategies = derive_strategies(&CanonicalIr {
        modules: vec![module("fixture", vec![parent, child, implementation])],
    })
    .expect("inherited specialization strategies");
    assert_eq!(
        strategies
            .iter()
            .map(|strategy| strategy.symbol.as_str())
            .collect::<Vec<_>>(),
        ["fixture.Concrete.init", "fixture.Concrete.read"]
    );
    assert_eq!(strategies[1].clause_ids, ["ensures:19"]);
}

#[test]
fn selected_methods_are_authoritative() {
    let mut implementation = implementation(
        "fixture.Selected",
        None,
        &[],
        vec![impl_method("ignored", "bool", &[], &[], &[], &[7], &[])],
    );
    implementation["selected_methods"] = json!([]);
    let ir = CanonicalIr {
        modules: vec![module("fixture", vec![implementation])],
    };
    assert_eq!(
        derive_strategies(&ir)
            .expect("selected strategies")
            .iter()
            .map(|strategy| strategy.symbol.as_str())
            .collect::<Vec<_>>(),
        ["fixture.Selected.init"]
    );
}

#[test]
fn free_function_strategy_serialization_is_byte_compatible() {
    let ir = CanonicalIr {
        modules: vec![module(
            "compat",
            vec![function(
                "compat.run",
                "bool",
                &[],
                &[("requires", 4), ("ensures", 9)],
            )],
        )],
    };
    let strategy = derive_strategies(&ir)
        .expect("canonical function strategy")
        .pop()
        .expect("function strategy");
    let expected = ContractTestStrategy::new(
        "compat.run",
        &ir.modules[0].bytes,
        "sync",
        Classification::Pure,
        vec!["requires:4".to_owned(), "ensures:9".to_owned()],
    );
    assert_eq!(strategy, expected);
    assert_eq!(
        strategy.bytes().expect("schema-valid strategy"),
        expected.bytes().expect("schema-valid expected strategy")
    );
}

#[test]
fn malformed_function_ir_is_rejected() {
    let rendered = module(
        "malformed",
        vec![function("malformed.run", "bool", &[], &[])],
    );
    let mut value: Value = serde_json::from_slice(&rendered.bytes).expect("module JSON");
    value["declarations"][0]
        .as_object_mut()
        .expect("function object")
        .remove("return_type");
    let mut bytes = serde_json::to_vec(&value).expect("malformed module JSON");
    bytes.push(b'\n');
    let ir = CanonicalIr {
        modules: vec![CanonicalModule {
            module: rendered.module,
            source: rendered.source,
            bytes,
        }],
    };

    let error = derive_strategies(&ir).expect_err("missing return type must fail");
    assert!(error.contains("schema violation"));
}
#[test]
fn contract_runner_observes_local_result_error_variant() {
    if !Command::new("python3")
        .arg("--version")
        .output()
        .is_ok_and(|output| output.status.success())
    {
        return;
    }

    let mut number = 0;
    let root = loop {
        let path = std::env::temp_dir().join(format!(
            "cott-contract-runner-{}-{number}",
            std::process::id()
        ));
        number += 1;
        match fs::create_dir(&path) {
            Ok(()) => break path,
            Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => continue,
            Err(error) => panic!("contract runner fixture directory: {error}"),
        }
    };

    for (relative, bytes) in render_runtime("demo", "0.4.0") {
        let path = root.join(relative);
        fs::create_dir_all(path.parent().expect("runtime file parent")).expect("runtime parent");
        fs::write(path, bytes).expect("runtime file");
    }
    fs::write(
        root.join("demo.py"),
        "import dataclasses\nfrom cott_runtime import Err, Result\n\n@dataclasses.dataclass(frozen=True)\nclass Failure_Bad:\n    pass\n\ndef run() -> Result[bool, Failure_Bad]:\n    return Err(error=Failure_Bad())\n",
    )
    .expect("fixture module");

    let request = json!({
        "modules": [{
            "declarations": [{
                "annotations": [],
                "body": null,
                "contract": {
                    "clauses": [{
                        "clause_id": 0,
                        "guard": null,
                        "kind": "error",
                        "priority": null,
                        "span": span(),
                        "variant": "demo.Failure.Bad",
                        "when": null
                    }],
                    "effects": []
                },
                "doc": null,
                "generics": [],
                "callable_kind": "sync",
                "kind": "function",
                "name": "demo.run",
                "parameters": [],
                "public": true,
                "return_type": {"kind": "primitive", "name": "bool"},
                "source_order": 0,
                "span": span()
            }],
            "imports": [],
            "module": "demo",
            "schema_version": 6,
            "source": "demo.cott"
        }],
        "runtime_validation": "boundary",
        "strategies": [{
            "callable_kind": "sync",
            "return_kind": "value",
            "classification": "pure",
            "clause_ids": ["error:0"],
            "schema_version": 3,
            "seed": "sha256:test",
            "symbol": "demo.run",
            "candidate_limit": 64,
            "node_limit": 64,
            "container_length_limit": 3,
            "json_depth_limit": 4,
            "lifecycle_limit": 3
        }]
    });
    let mut child = Command::new("python3")
        .args(["-c", include_str!("../src/contract_runner.py")])
        .current_dir(&root)
        .env("PYTHONPATH", &root)
        .env("PYTHONDONTWRITEBYTECODE", "1")
        .env("PYTHONHASHSEED", "0")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("contract runner should start");
    child
        .stdin
        .take()
        .expect("contract runner stdin")
        .write_all(request.to_string().as_bytes())
        .expect("contract runner request");
    let output = child
        .wait_with_output()
        .expect("contract runner should finish");
    fs::remove_dir_all(&root).expect("contract runner fixture cleanup");
    assert!(
        output.status.success(),
        "contract runner failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("contract report JSON");
    assert_eq!(
        report["contracts"][0]["evidence"][0]["valid_cases"],
        json!(1)
    );
    assert_eq!(
        report["contracts"][0]["evidence"][0]["grade"],
        json!("test observation")
    );
}

fn run_contract_runner(source: &str, request: Value) -> Option<std::process::Output> {
    if !Command::new("python3")
        .arg("--version")
        .output()
        .is_ok_and(|output| output.status.success())
    {
        return None;
    }
    let root = std::env::temp_dir().join(format!(
        "cott-contract-runner-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .expect("clock after epoch")
            .as_nanos()
    ));
    fs::create_dir(&root).expect("contract runner fixture directory");
    for (relative, bytes) in render_runtime("demo", "0.4.0") {
        let path = root.join(relative);
        fs::create_dir_all(path.parent().expect("runtime file parent")).expect("runtime parent");
        fs::write(path, bytes).expect("runtime file");
    }
    fs::write(root.join("demo.py"), source).expect("fixture module");
    let mut child = Command::new("python3")
        .args(["-c", include_str!("../src/contract_runner.py")])
        .current_dir(&root)
        .env("PYTHONPATH", &root)
        .env("PYTHONDONTWRITEBYTECODE", "1")
        .env("PYTHONHASHSEED", "0")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("contract runner should start");
    child
        .stdin
        .take()
        .expect("contract runner stdin")
        .write_all(request.to_string().as_bytes())
        .expect("contract runner request");
    let output = child
        .wait_with_output()
        .expect("contract runner should finish");
    fs::remove_dir_all(root).expect("contract runner fixture cleanup");
    Some(output)
}

fn runner_strategy(symbol: &str, clause_ids: Vec<String>) -> Value {
    json!({
        "callable_kind": "sync",
        "return_kind": "value",
        "classification": "pure",
        "clause_ids": clause_ids,
        "schema_version": 3,
        "seed": "sha256:test",
        "symbol": symbol,
        "candidate_limit": 64,
        "node_limit": 64,
        "container_length_limit": 3,
        "json_depth_limit": 4,
        "lifecycle_limit": 3
    })
}

fn runner_expression(kind: &str, fields: Value) -> Value {
    let mut expression = fields.as_object().expect("expression fields").clone();
    expression.insert("reference".to_owned(), Value::Null);
    expression.insert("kind".to_owned(), json!(kind));
    expression.insert("span".to_owned(), span());
    expression.insert(
        "type".to_owned(),
        json!({"kind": "primitive", "name": "bool"}),
    );
    Value::Object(expression)
}

fn runner_literal(value: Value) -> Value {
    runner_expression("literal", json!({"value": value}))
}

fn runner_parameter(name: &str) -> Value {
    runner_expression(
        "parameter_ref",
        json!({"symbol": format!("demo.Counter.{name}")}),
    )
}

fn runner_self_field(name: &str) -> Value {
    runner_expression(
        "field",
        json!({"base": runner_expression("self_ref", json!({})), "name": name}),
    )
}

fn runner_old_field(name: &str) -> Value {
    runner_expression(
        "old_state_field",
        json!({"field": format!("demo.Counter.{name}")}),
    )
}

fn runner_binary(op: &str, left: Value, right: Value) -> Value {
    runner_expression("binary", json!({"op": op, "left": left, "right": right}))
}

fn runner_comparison(left: Value, operator: &str, right: Value) -> Value {
    runner_expression(
        "comparison_chain",
        json!({"operands": [left, right], "operators": [operator]}),
    )
}

fn runner_clause(kind: &str, clause_id: u64, expression: Value) -> Value {
    json!({"clause_id": clause_id, "expression": expression, "guard": null, "kind": kind, "span": span()})
}

fn runner_function(name: &str, clauses: Vec<Value>) -> Value {
    json!({
        "annotations": [],
        "body": null,
        "contract": {"clauses": clauses, "effects": []},
        "doc": null,
        "generics": [],
        "callable_kind": "sync",
        "kind": "function",
        "name": name,
        "parameters": [],
        "public": true,
        "return_type": {"kind": "primitive", "name": "i32"},
        "source_order": 0,
        "span": span()
    })
}

fn runner_impl(methods: Vec<Value>) -> Value {
    let selected_methods = methods
        .iter()
        .map(|method| {
            let name = method["name"].as_str().expect("method name");
            json!({
                "callable_kind": method["callable_kind"],
                "parameters": method["parameters"],
                "receiver_type": {"args": [], "kind": "named", "name": "demo.Counter"},
                "return_type": method["return_type"],
                "selected": {
                    "function": {
                        "module": "demo",
                        "symbol": format!("Counter.{name}"),
                        "verified_facade": format!("demo.Counter.{name}")
                    },
                    "origin": "explicit"
                },
                "trait_method": format!("demo.Counter.{name}"),
                "trait_ref": {"args": [], "kind": "named", "name": "demo.Counter"}
            })
        })
        .collect::<Vec<_>>();
    json!({
        "annotations": [],
        "doc": null,
        "generics": [],
        "associated_types": [],
        "init": {"contracts": {"doc": null, "requires": [], "ensures": []}, "parameters": [], "span": span()},
        "invariants": [json!({
            "clause_id": 0,
            "expression": runner_comparison(runner_self_field("count"), "greater_equal", runner_literal(json!({"kind": "integer", "value": "0"}))),
            "guard": null,
            "span": span()
        })],
        "kind": "impl",
        "methods": methods,
        "name": "demo.Counter",
        "public": true,
        "selected_methods": selected_methods,
        "source_order": 0,
        "span": span(),
        "state": [
            {"default": null, "name": "count", "source_order": 0, "span": span(), "type": {"kind": "primitive", "name": "i32"}},
            {"default": null, "name": "guard", "source_order": 1, "span": span(), "type": {"kind": "primitive", "name": "i32"}}
        ],
        "traits": [{"args": [], "kind": "named", "name": "demo.Counter"}]
    })
}

fn runner_method(name: &str, modifies: Vec<&str>, mut contracts: Value) -> Value {
    contracts
        .as_object_mut()
        .expect("method contracts")
        .insert("doc".to_owned(), Value::Null);
    json!({
        "contracts": contracts,
        "effects": [],
        "modifies": modifies,
        "name": name,
        "callable_kind": "sync",
        "parameters": [],
        "return_type": {"kind": "primitive", "name": "i32"},
        "span": span(),
        "transitions": []
    })
}

fn runner_request(declaration: Value, strategies: Vec<Value>) -> Value {
    json!({
        "modules": [{
            "declarations": [declaration],
            "imports": [],
            "module": "demo",
            "schema_version": 7,
            "source": "demo.cott"
        }],
        "runtime_validation": "boundary",
        "strategies": strategies
    })
}

#[test]
fn contract_runner_generates_homogeneous_tuple_candidates() {
    let declaration = runner_function(
        "demo.accepts_tuple",
        vec![runner_clause(
            "ensures",
            0,
            runner_literal(json!({"kind": "bool", "value": true})),
        )],
    );
    let Some(output) = run_contract_runner(
        "def accepts_tuple(value: tuple[int, ...]) -> int:\n    return len(value)\n",
        runner_request(
            declaration,
            vec![runner_strategy(
                "demo.accepts_tuple",
                vec!["ensures:0".to_owned()],
            )],
        ),
    ) else {
        return;
    };
    assert!(
        output.status.success(),
        "contract runner failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("contract report JSON");
    assert_eq!(
        report["contracts"][0]["evidence"][0]["grade"],
        "test observation"
    );
}

#[test]
fn contract_runner_constructs_terminating_recursive_enum_candidates_stably() {
    let declaration = runner_function(
        "demo.accepts_tree",
        vec![runner_clause(
            "ensures",
            0,
            runner_literal(json!({"kind": "bool", "value": true})),
        )],
    );
    let source = "from __future__ import annotations\nimport dataclasses\n\n@dataclasses.dataclass(frozen=True)\nclass Tree_Leaf:\n    value: int\n\n@dataclasses.dataclass(frozen=True)\nclass Tree_Branch:\n    child: Tree\n\nTree = Tree_Leaf | Tree_Branch\n\ndef accepts_tree(value: Tree) -> int:\n    return 0\n";
    let request = runner_request(
        declaration,
        vec![runner_strategy(
            "demo.accepts_tree",
            vec!["ensures:0".to_owned()],
        )],
    );
    let Some(first) = run_contract_runner(source, request.clone()) else {
        return;
    };
    let Some(second) = run_contract_runner(source, request) else {
        return;
    };
    assert!(
        first.status.success() && second.status.success(),
        "contract runner failed: {}",
        String::from_utf8_lossy(&first.stderr)
    );
    assert_eq!(first.stdout, second.stdout);
    let report: Value = serde_json::from_slice(&first.stdout).expect("contract report JSON");
    assert_eq!(
        report["contracts"][0]["evidence"][0]["grade"],
        "test observation"
    );
}

#[test]
fn contract_runner_marks_required_recursive_input_unobserved() {
    let declaration = runner_function(
        "demo.accepts_infinite",
        vec![runner_clause(
            "ensures",
            0,
            runner_literal(json!({"kind": "bool", "value": true})),
        )],
    );
    let Some(output) = run_contract_runner(
        "from __future__ import annotations\nimport dataclasses\n\n@dataclasses.dataclass(frozen=True)\nclass Infinite:\n    child: Infinite\n\ndef accepts_infinite(value: Infinite) -> int:\n    raise AssertionError('recursive candidate must not be allocated')\n",
        runner_request(
            declaration,
            vec![runner_strategy(
                "demo.accepts_infinite",
                vec!["ensures:0".to_owned()],
            )],
        ),
    ) else {
        return;
    };
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("contract report JSON");
    let evidence = &report["contracts"][0]["evidence"][0];
    assert_eq!(evidence["grade"], "unobserved");
    assert_eq!(
        evidence["reason"],
        "input parameter `value` required recursive value `Infinite` has no finite candidate"
    );
}

#[test]
fn contract_runner_distinguishes_candidate_depth_and_node_exhaustion() {
    let declaration = runner_function(
        "demo.accepts_nested",
        vec![runner_clause(
            "ensures",
            0,
            runner_literal(json!({"kind": "bool", "value": true})),
        )],
    );
    let mut depth_strategy = runner_strategy("demo.accepts_nested", vec!["ensures:0".to_owned()]);
    depth_strategy["json_depth_limit"] = json!(1);
    let Some(depth_output) = run_contract_runner(
        "def accepts_nested(value: tuple[tuple[int]]) -> int:\n    return 0\n",
        runner_request(declaration.clone(), vec![depth_strategy]),
    ) else {
        return;
    };
    assert!(
        depth_output.status.success(),
        "{}",
        String::from_utf8_lossy(&depth_output.stderr)
    );
    let depth_report: Value =
        serde_json::from_slice(&depth_output.stdout).expect("contract report JSON");
    assert_eq!(
        depth_report["contracts"][0]["evidence"][0]["reason"],
        "input parameter `value` candidate depth limit (1) exhausted"
    );

    let mut node_strategy = runner_strategy("demo.accepts_nested", vec!["ensures:0".to_owned()]);
    node_strategy["node_limit"] = json!(1);
    let Some(node_output) = run_contract_runner(
        "from __future__ import annotations\nimport dataclasses\n\n@dataclasses.dataclass(frozen=True)\nclass Node:\n    child: Node | None\n\ndef accepts_nested(value: Node) -> int:\n    return 0\n",
        runner_request(declaration, vec![node_strategy]),
    ) else {
        return;
    };
    assert!(
        node_output.status.success(),
        "{}",
        String::from_utf8_lossy(&node_output.stderr)
    );
    let node_report: Value =
        serde_json::from_slice(&node_output.stdout).expect("contract report JSON");
    assert_eq!(
        node_report["contracts"][0]["evidence"][0]["reason"],
        "input parameter `value` candidate node limit (1) exhausted"
    );
}

#[test]
fn contract_runner_observes_empty_containers_with_unavailable_elements() {
    let declaration = runner_function(
        "demo.accepts_empty",
        vec![runner_clause(
            "ensures",
            0,
            runner_literal(json!({"kind": "bool", "value": true})),
        )],
    );
    let Some(output) = run_contract_runner(
        "import typing\nimport cott_runtime\n\ndef accepts_empty(values: cott_runtime.CottList[typing.Any], mapping: cott_runtime.FrozenMap[object, typing.Annotated[int, cott_runtime.CottExternal('outside')]], array: cott_runtime.CottArray[typing.Any, typing.Literal[0]]) -> int:\n    return len(values) + len(mapping) + len(array)\n",
        runner_request(
            declaration,
            vec![runner_strategy(
                "demo.accepts_empty",
                vec!["ensures:0".to_owned()],
            )],
        ),
    ) else {
        return;
    };
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("contract report JSON");
    assert_eq!(
        report["contracts"][0]["evidence"][0]["grade"],
        "test observation"
    );
}

#[test]
fn contract_runner_observes_recursive_empty_container_candidate() {
    let declaration = runner_function(
        "demo.accepts_node",
        vec![runner_clause(
            "ensures",
            0,
            runner_literal(json!({"kind": "bool", "value": true})),
        )],
    );
    let Some(output) = run_contract_runner(
        "from __future__ import annotations\nimport dataclasses\nimport cott_runtime\n\n@dataclasses.dataclass(frozen=True)\nclass Node:\n    children: cott_runtime.CottList[Node]\n\ndef accepts_node(value: Node) -> int:\n    return len(value.children)\n",
        runner_request(
            declaration,
            vec![runner_strategy(
                "demo.accepts_node",
                vec!["ensures:0".to_owned()],
            )],
        ),
    ) else {
        return;
    };
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("contract report JSON");
    assert_eq!(
        report["contracts"][0]["evidence"][0]["grade"],
        "test observation"
    );
}

#[test]
fn contract_runner_observes_recursive_generic_enum_empty_variant() {
    let declaration = runner_function(
        "demo.accepts_tree",
        vec![runner_clause(
            "ensures",
            0,
            runner_literal(json!({"kind": "bool", "value": true})),
        )],
    );
    let Some(output) = run_contract_runner(
        "from __future__ import annotations\nimport dataclasses\nimport typing\n\nT = typing.TypeVar('T')\n\n@dataclasses.dataclass(frozen=True)\nclass Tree_Empty(typing.Generic[T]):\n    pass\n\n@dataclasses.dataclass(frozen=True)\nclass Tree_Node(typing.Generic[T]):\n    child: Tree[T]\n\nTree = Tree_Empty[T] | Tree_Node[T]\n\ndef accepts_tree(value: Tree[typing.Any]) -> int:\n    return 0\n",
        runner_request(
            declaration,
            vec![runner_strategy(
                "demo.accepts_tree",
                vec!["ensures:0".to_owned()],
            )],
        ),
    ) else {
        return;
    };
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("contract report JSON");
    assert_eq!(
        report["contracts"][0]["evidence"][0]["grade"],
        "test observation"
    );
}

#[test]
fn contract_runner_marks_required_unknown_generic_field_unobserved() {
    let declaration = runner_function(
        "demo.accepts_box",
        vec![runner_clause(
            "ensures",
            0,
            runner_literal(json!({"kind": "bool", "value": true})),
        )],
    );
    let Some(output) = run_contract_runner(
        "import dataclasses\nimport typing\n\nT = typing.TypeVar('T')\n\n@dataclasses.dataclass(frozen=True)\nclass Box(typing.Generic[T]):\n    value: T\n\ndef accepts_box(value: Box[object]) -> int:\n    raise AssertionError('unknown generic field must not be synthesized')\n",
        runner_request(
            declaration,
            vec![runner_strategy(
                "demo.accepts_box",
                vec!["ensures:0".to_owned()],
            )],
        ),
    ) else {
        return;
    };
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("contract report JSON");
    assert_eq!(report["contracts"][0]["evidence"][0]["grade"], "unobserved");
}

#[test]
fn contract_runner_rejects_oversized_fixed_candidates_before_allocation() {
    let declaration = runner_function(
        "demo.accepts_large",
        vec![runner_clause(
            "ensures",
            0,
            runner_literal(json!({"kind": "bool", "value": true})),
        )],
    );
    let Some(output) = run_contract_runner(
        "import typing\nfrom cott_runtime import CottArray, CottBuffer\n\ndef accepts_large(array: CottArray[int, typing.Literal[1_000_000_000]], buffer: CottBuffer[typing.Literal[1_000_000_000]]) -> int:\n    raise AssertionError('oversized candidate was allocated')\n",
        runner_request(
            declaration,
            vec![runner_strategy(
                "demo.accepts_large",
                vec!["ensures:0".to_owned()],
            )],
        ),
    ) else {
        return;
    };
    assert!(
        output.status.success(),
        "contract runner failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("contract report JSON");
    let evidence = &report["contracts"][0]["evidence"][0];
    assert_eq!(evidence["grade"], "unobserved");
    assert_eq!(evidence["valid_cases"], 0);
}

#[test]
fn contract_runner_marks_any_inputs_unobserved_without_executing() {
    let declaration = runner_function(
        "demo.accepts",
        vec![runner_clause(
            "requires",
            0,
            runner_literal(json!({"kind": "bool", "value": true})),
        )],
    );
    let Some(output) = run_contract_runner(
        "import typing\n\ndef accepts(value: typing.Any) -> int:\n    raise AssertionError('Any input must not be synthesized')\n",
        runner_request(
            declaration,
            vec![runner_strategy(
                "demo.accepts",
                vec!["requires:0".to_owned()],
            )],
        ),
    ) else {
        return;
    };
    assert!(
        output.status.success(),
        "contract runner failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("contract report JSON");
    let evidence = &report["contracts"][0]["evidence"][0];
    assert_eq!(evidence["grade"], json!("unobserved"));
    assert_eq!(evidence["valid_cases"], json!(0));
    assert_eq!(
        evidence["reason"],
        json!("input parameter `value` is Any and is not automatically generated")
    );
}

#[test]
fn contract_runner_marks_dyn_inputs_unobserved_without_concrete_case() {
    let declaration = runner_function(
        "demo.accepts_dynamic",
        vec![runner_clause(
            "requires",
            0,
            runner_literal(json!({"kind": "bool", "value": true})),
        )],
    );
    let Some(output) = run_contract_runner(
        "import typing\nimport cott_runtime\n\nclass Reader(typing.Protocol):\n    def read(self) -> int: ...\n\ndef accepts_dynamic(value: cott_runtime.Dyn[Reader]) -> int:\n    raise AssertionError('Dyn input must not be synthesized')\n",
        runner_request(
            declaration,
            vec![runner_strategy(
                "demo.accepts_dynamic",
                vec!["requires:0".to_owned()],
            )],
        ),
    ) else {
        return;
    };
    assert!(
        output.status.success(),
        "contract runner failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("contract report JSON");
    let evidence = &report["contracts"][0]["evidence"][0];
    assert_eq!(evidence["grade"], json!("unobserved"));
    assert_eq!(evidence["valid_cases"], json!(0));
    assert_eq!(
        evidence["reason"],
        json!(
            "input parameter `value` is Dyn[Reader] without a compiler-owned initialized concrete case and is not automatically generated"
        )
    );
}

#[test]
fn contract_runner_matches_generic_dyn_candidates_by_origin_and_exact_specification() {
    let accepts = runner_method(
        "accepts",
        vec![],
        json!({"requires": [], "ensures": [], "errors": []}),
    );
    let rejects = runner_method(
        "rejects",
        vec![],
        json!({"requires": [], "ensures": [], "errors": []}),
    );
    let declaration = runner_impl(vec![accepts, rejects]);
    let Some(output) = run_contract_runner(
        "import typing\nimport cott_runtime\n\nT = typing.TypeVar('T')\n\nclass GenericTrait(typing.Protocol[T]):\n    _cott_trait = True\n    def read(self) -> T: ...\n\nclass Counter:\n    _cott_traits = (GenericTrait,)\n    _cott_trait_specs = (GenericTrait[cott_runtime.I32],)\n\n    def __init__(self) -> None:\n        self.count = 0\n        self.guard = 0\n\n    def read(self) -> cott_runtime.I32:\n        return 0\n\n    def accepts(self, value: cott_runtime.Dyn[GenericTrait[cott_runtime.I32]]) -> int:\n        return value.value.read()\n\n    def rejects(self, value: cott_runtime.Dyn[GenericTrait[str]]) -> int:\n        raise AssertionError('Dyn with the wrong generic specification must not be selected')\n",
        runner_request(
            declaration,
            vec![
                runner_strategy("demo.Counter.init", vec!["invariant:0".to_owned()]),
                runner_strategy("demo.Counter.accepts", vec!["invariant:0".to_owned()]),
                runner_strategy("demo.Counter.rejects", vec!["invariant:0".to_owned()]),
            ],
        ),
    ) else {
        return;
    };
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("contract report JSON");
    let accepts = report["contracts"]
        .as_array()
        .expect("contracts")
        .iter()
        .find(|evidence| evidence["symbol"] == "demo.Counter.accepts")
        .expect("accepts evidence");
    let rejects = report["contracts"]
        .as_array()
        .expect("contracts")
        .iter()
        .find(|evidence| evidence["symbol"] == "demo.Counter.rejects")
        .expect("rejects evidence");
    assert_eq!(accepts["evidence"][0]["grade"], "test observation");
    assert_eq!(rejects["evidence"][0]["grade"], "unobserved");
}

#[test]
fn contract_runner_marks_factory_inputs_unobserved_without_executing() {
    let declaration = runner_function(
        "demo.accepts_factory",
        vec![runner_clause(
            "requires",
            0,
            runner_literal(json!({"kind": "bool", "value": true})),
        )],
    );
    let Some(output) = run_contract_runner(
        "class Concrete:\n    def __init__(self):\n        raise AssertionError('Factory input must not be constructed')\n\ndef accepts_factory(value: type[Concrete]) -> int:\n    raise AssertionError('Factory input must not be invoked')\n",
        runner_request(
            declaration,
            vec![runner_strategy(
                "demo.accepts_factory",
                vec!["requires:0".to_owned()],
            )],
        ),
    ) else {
        return;
    };
    assert!(
        output.status.success(),
        "contract runner failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("contract report JSON");
    let evidence = &report["contracts"][0]["evidence"][0];
    assert_eq!(evidence["grade"], json!("unobserved"));
    assert_eq!(evidence["valid_cases"], json!(0));
    assert_eq!(
        evidence["reason"],
        json!("input parameter `value` is Factory and is not automatically generated")
    );
}

#[test]
fn contract_runner_does_not_consume_iterator_returns() {
    let declaration = runner_function(
        "demo.stream",
        vec![runner_clause(
            "requires",
            0,
            runner_literal(json!({"kind": "bool", "value": true})),
        )],
    );
    let Some(output) = run_contract_runner(
        "import collections.abc\n\nclass Trap(collections.abc.Iterator):\n    def __iter__(self):\n        raise AssertionError('iterator return was consumed')\n\n    def __next__(self):\n        raise AssertionError('iterator return was consumed')\n\ndef stream() -> collections.abc.Iterator[int]:\n    return Trap()\n",
        runner_request(
            declaration,
            vec![runner_strategy(
                "demo.stream",
                vec!["requires:0".to_owned()],
            )],
        ),
    ) else {
        return;
    };
    assert!(
        output.status.success(),
        "contract runner failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("contract report JSON");
    let evidence = &report["contracts"][0]["evidence"][0];
    assert_eq!(evidence["grade"], json!("test observation"));
    assert_eq!(evidence["valid_cases"], json!(1));
}

#[test]
fn contract_runner_evaluates_free_function_result_ref() {
    let declaration = runner_function(
        "demo.identity",
        vec![runner_clause(
            "ensures",
            0,
            runner_comparison(
                runner_expression("result_ref", json!({})),
                "equal",
                runner_expression("parameter_ref", json!({"symbol": "demo.identity.value"})),
            ),
        )],
    );
    let Some(output) = run_contract_runner(
        "def identity(value: int) -> int:\n    return value\n",
        runner_request(
            declaration,
            vec![runner_strategy(
                "demo.identity",
                vec!["ensures:0".to_owned()],
            )],
        ),
    ) else {
        return;
    };
    assert!(
        output.status.success(),
        "contract runner failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("contract report JSON");
    assert_eq!(
        report["contracts"][0]["evidence"][0]["grade"],
        json!("test observation")
    );
}

#[test]
fn contract_runner_bounds_json_value_candidates() {
    let declaration = runner_function(
        "demo.accepts_json",
        vec![runner_clause(
            "ensures",
            0,
            runner_literal(json!({"kind": "bool", "value": true})),
        )],
    );
    let Some(output) = run_contract_runner(
        "import sys\nsys.setrecursionlimit(32)\nfrom cott_runtime import JsonValue\n\ndef accepts_json(value: JsonValue) -> int:\n    return 0\n",
        runner_request(
            declaration,
            vec![runner_strategy(
                "demo.accepts_json",
                vec!["ensures:0".to_owned()],
            )],
        ),
    ) else {
        return;
    };
    assert!(
        output.status.success(),
        "contract runner failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("contract report JSON");
    let evidence = &report["contracts"][0]["evidence"][0];
    assert_eq!(evidence["grade"], json!("test observation"));
    assert!(
        evidence["valid_cases"]
            .as_u64()
            .is_some_and(|count| count > 0)
    );
}

#[test]
fn contract_runner_observes_impl_old_modifies_invariants_and_errors() {
    let advance = runner_method(
        "advance",
        vec!["demo.Counter.count"],
        json!({
            "requires": [runner_clause("requires", 0, runner_comparison(runner_parameter("amount"), "greater_equal", runner_literal(json!({"kind": "integer", "value": "0"}))))],
            "ensures": [
                runner_clause("ensures", 1, runner_comparison(runner_expression("result_ref", json!({})), "equal", runner_self_field("count"))),
                runner_clause("ensures", 2, runner_comparison(runner_binary("add", runner_old_field("count"), runner_parameter("amount")), "equal", runner_self_field("count")))
            ],
            "errors": []
        }),
    );
    let fail = runner_method(
        "fail",
        vec!["demo.Counter.count"],
        json!({
            "requires": [],
            "ensures": [],
            "errors": [json!({
                "clause_id": 0,
                "guard": null,
                "kind": "error",
                "priority": null,
                "span": span(),
                "variant": "demo.Failure.Bad",
                "when": runner_comparison(runner_parameter("amount"), "less", runner_literal(json!({"kind": "integer", "value": "0"})))
            })]
        }),
    );
    let declaration = runner_impl(vec![advance, fail]);
    let Some(output) = run_contract_runner(
        "import dataclasses\nfrom cott_runtime import Err, Ok, Result\n\n@dataclasses.dataclass(frozen=True)\nclass Failure_Bad:\n    pass\n\nclass Counter:\n    def __init__(self) -> None:\n        self.count = 0\n        self.guard = 0\n\n    def advance(self, amount: int) -> int:\n        self.count += amount\n        return self.count\n\n    def fail(self, amount: int) -> Result[int, Failure_Bad]:\n        if amount < 0:\n            return Err(error=Failure_Bad())\n        self.count += amount\n        return Ok(value=self.count)\n",
        runner_request(
            declaration,
            vec![
                runner_strategy("demo.Counter.init", vec!["invariant:0".to_owned()]),
                runner_strategy(
                    "demo.Counter.advance",
                    vec![
                        "requires:0".to_owned(),
                        "ensures:1".to_owned(),
                        "ensures:2".to_owned(),
                        "modifies:demo.Counter.count".to_owned(),
                        "invariant:0".to_owned(),
                    ],
                ),
                runner_strategy(
                    "demo.Counter.fail",
                    vec![
                        "error:0".to_owned(),
                        "modifies:demo.Counter.count".to_owned(),
                        "invariant:0".to_owned(),
                    ],
                ),
            ],
        ),
    ) else {
        return;
    };
    assert!(
        output.status.success(),
        "contract runner failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("contract report JSON");
    assert!(
        report["contracts"]
            .as_array()
            .expect("contracts")
            .iter()
            .all(|contract| contract["evidence"][0]["grade"] == "test observation"),
        "unexpected report: {report}"
    );
}

#[test]
fn contract_runner_rejects_impl_forbidden_mutation_and_invariant_failure() {
    let bad_modifies = runner_method(
        "bad_modifies",
        vec!["demo.Counter.count"],
        json!({"requires": [], "ensures": [], "errors": []}),
    );
    let bad_invariant = runner_method(
        "bad_invariant",
        vec!["demo.Counter.count"],
        json!({"requires": [], "ensures": [], "errors": []}),
    );
    let declaration = runner_impl(vec![bad_modifies, bad_invariant]);
    let source = "class Counter:\n    def __init__(self) -> None:\n        self.count = 0\n        self.guard = 0\n\n    def bad_modifies(self, amount: int) -> int:\n        self.guard = amount\n        return self.count\n\n    def bad_invariant(self, amount: int) -> int:\n        self.count = -1\n        return self.count\n";
    let Some(modifies) = run_contract_runner(
        source,
        runner_request(
            declaration.clone(),
            vec![runner_strategy(
                "demo.Counter.bad_modifies",
                vec![
                    "modifies:demo.Counter.count".to_owned(),
                    "invariant:0".to_owned(),
                ],
            )],
        ),
    ) else {
        return;
    };
    assert!(!modifies.status.success());
    assert!(String::from_utf8_lossy(&modifies.stderr).contains("modifies clause"));

    let Some(invariant) = run_contract_runner(
        source,
        runner_request(
            declaration,
            vec![runner_strategy(
                "demo.Counter.bad_invariant",
                vec![
                    "modifies:demo.Counter.count".to_owned(),
                    "invariant:0".to_owned(),
                ],
            )],
        ),
    ) else {
        return;
    };
    assert!(!invariant.status.success());
    assert!(String::from_utf8_lossy(&invariant.stderr).contains("invariant clause"));
}

#[test]
fn contract_runner_constructs_methods_only_from_init_validated_cases() {
    let mut declaration = runner_impl(vec![runner_method(
        "read",
        vec![],
        json!({
            "requires": [],
            "ensures": [runner_clause(
                "ensures",
                3,
                runner_comparison(
                    runner_expression("result_ref", json!({})),
                    "equal",
                    runner_self_field("count"),
                ),
            )],
            "errors": []
        }),
    )]);
    declaration["init"] = json!({
        "contracts": {
            "doc": null,
            "requires": [runner_clause(
                "requires",
                1,
                runner_comparison(
                    runner_parameter("count"),
                    "greater",
                    runner_literal(json!({"kind": "integer", "value": "0"})),
                ),
            )],
            "ensures": [runner_clause(
                "ensures",
                2,
                runner_comparison(runner_self_field("count"), "equal", runner_parameter("count")),
            )]
        },
        "parameters": [{
            "default": null,
            "kind": "positional",
            "name": "count",
            "source_order": 0,
            "span": span(),
            "type": {"kind": "primitive", "name": "i32"}
        }],
        "span": span()
    });
    let Some(output) = run_contract_runner(
        "class Counter:\n    def __init__(self, count: int) -> None:\n        if count <= 0:\n            raise AssertionError(\"invalid constructor candidate invoked\")\n        self.count = count\n        self.guard = 0\n\n    def read(self) -> int:\n        return self.count\n",
        runner_request(
            declaration,
            vec![
                runner_strategy(
                    "demo.Counter.init",
                    vec![
                        "requires:1".to_owned(),
                        "ensures:2".to_owned(),
                        "invariant:0".to_owned(),
                    ],
                ),
                runner_strategy(
                    "demo.Counter.read",
                    vec!["ensures:3".to_owned(), "invariant:0".to_owned()],
                ),
            ],
        ),
    ) else {
        return;
    };
    assert!(
        output.status.success(),
        "contract runner failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("contract report JSON");
    assert!(
        report["contracts"]
            .as_array()
            .expect("contracts")
            .iter()
            .all(|contract| contract["evidence"][0]["grade"] == "test observation"),
        "unexpected report: {report}"
    );
}

#[test]
fn contract_runner_observes_and_closes_pure_async_protocols() {
    let mut iterator = runner_function(
        "demo.stream",
        vec![runner_clause(
            "ensures",
            0,
            runner_literal(json!({"kind": "bool", "value": true})),
        )],
    );
    iterator["return_type"] = json!({
        "kind": "async_iterator",
        "item": {"kind": "primitive", "name": "i32"},
    });
    let mut iterator_strategy = runner_strategy("demo.stream", vec!["ensures:0".to_owned()]);
    iterator_strategy["return_kind"] = json!("async_iterator");
    let Some(output) = run_contract_runner(
        "import collections.abc\n\nclass Stream(collections.abc.AsyncIterator):\n    def __init__(self): self.steps = 0; self.closed = False\n    def __aiter__(self): return self\n    async def __anext__(self):\n        if self.closed or self.steps == 3: raise StopAsyncIteration\n        self.steps += 1\n        return self.steps\n    async def aclose(self): self.closed = True\n\ndef stream() -> collections.abc.AsyncIterator[int]:\n    return Stream()\n",
        runner_request(iterator, vec![iterator_strategy]),
    ) else {
        return;
    };
    assert!(
        output.status.success(),
        "contract runner failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("contract report JSON");
    assert_eq!(report["lifecycle"][0]["lifecycle_steps"], 3);
    assert_eq!(report["lifecycle"][0]["lifecycle_sent"], false);
    assert_eq!(report["lifecycle"][0]["lifecycle_closed"], true);
    assert_eq!(
        report["lifecycle"][0]["lifecycle_reason"],
        "observation limit reached"
    );

    let mut generator = runner_function(
        "demo.generate",
        vec![runner_clause(
            "ensures",
            0,
            runner_literal(json!({"kind": "bool", "value": true})),
        )],
    );
    generator["return_type"] = json!({
        "kind": "async_generator",
        "send": {"kind": "primitive", "name": "i32"},
        "yield": {"kind": "primitive", "name": "i32"},
    });
    let mut generator_strategy = runner_strategy("demo.generate", vec!["ensures:0".to_owned()]);
    generator_strategy["return_kind"] = json!("async_generator");
    let Some(output) = run_contract_runner(
        "import collections.abc\n\nasync def values():\n    _ = yield 1\n\ndef generate() -> collections.abc.AsyncGenerator[int, int]:\n    return values()\n",
        runner_request(generator, vec![generator_strategy]),
    ) else {
        return;
    };
    assert!(
        output.status.success(),
        "contract runner failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("contract report JSON");
    assert_eq!(report["lifecycle"][0]["lifecycle_steps"], 1);
    assert_eq!(report["lifecycle"][0]["lifecycle_sent"], true);
    assert_eq!(report["lifecycle"][0]["lifecycle_closed"], true);
    assert_eq!(
        report["lifecycle"][0]["lifecycle_reason"],
        "protocol completed"
    );
}

#[test]
fn contract_runner_trusts_effectful_async_protocol_declarations() {
    let mut declaration = runner_function(
        "demo.stream",
        vec![runner_clause(
            "ensures",
            0,
            runner_literal(json!({"kind": "bool", "value": true})),
        )],
    );
    declaration["return_type"] = json!({
        "kind": "async_iterator",
        "item": {"kind": "primitive", "name": "i32"},
    });
    let mut strategy = runner_strategy("demo.stream", vec!["ensures:0".to_owned()]);
    strategy["classification"] = json!("effectful");
    strategy["return_kind"] = json!("async_iterator");
    let Some(output) = run_contract_runner("", runner_request(declaration, vec![strategy])) else {
        return;
    };
    assert!(
        output.status.success(),
        "contract runner failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("contract report JSON");
    assert_eq!(
        report["contracts"][0]["evidence"][0]["grade"],
        "trust declaration"
    );
    assert_eq!(report["lifecycle"], json!([]));
}

#[test]
fn contract_runner_awaits_async_impl_methods() {
    let mut method = runner_method(
        "read",
        vec![],
        json!({"requires": [], "ensures": [], "errors": []}),
    );
    method["callable_kind"] = json!("async");
    method["return_type"] = json!({
        "kind": "async_iterator",
        "item": {"kind": "primitive", "name": "i32"},
    });
    let declaration = runner_impl(vec![method]);
    let mut strategy = runner_strategy("demo.Counter.read", vec!["invariant:0".to_owned()]);
    strategy["callable_kind"] = json!("async");
    strategy["return_kind"] = json!("async_iterator");
    let Some(output) = run_contract_runner(
        "import collections.abc\n\nclass Stream(collections.abc.AsyncIterator):\n    def __init__(self): self.step = 0; self.closed = False\n    def __aiter__(self): return self\n    async def __anext__(self):\n        if self.closed or self.step == 3: raise StopAsyncIteration\n        self.step += 1\n        return self.step\n    async def aclose(self): self.closed = True\n\nclass Counter:\n    def __init__(self) -> None:\n        self.count = 0\n        self.guard = 0\n\n    async def read(self) -> collections.abc.AsyncIterator[int]:\n        return Stream()\n",
        runner_request(declaration, vec![strategy]),
    ) else {
        return;
    };
    assert!(
        output.status.success(),
        "contract runner failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("contract report JSON");
    assert_eq!(
        report["contracts"][0]["evidence"][0]["grade"],
        "test observation"
    );
    assert_eq!(report["lifecycle"][0]["symbol"], "demo.Counter.read");
    assert_eq!(report["lifecycle"][0]["lifecycle_steps"], 3);
    assert_eq!(report["lifecycle"][0]["lifecycle_closed"], true);
}

#[test]
fn contract_runner_fails_later_protocol_close_without_hanging() {
    let mut declaration = runner_function(
        "demo.stream",
        vec![runner_clause(
            "ensures",
            0,
            runner_literal(json!({"kind": "bool", "value": true})),
        )],
    );
    declaration["return_type"] = json!({
        "kind": "async_iterator",
        "item": {"kind": "primitive", "name": "i32"},
    });
    let mut strategy = runner_strategy("demo.stream", vec!["ensures:0".to_owned()]);
    strategy["return_kind"] = json!("async_iterator");
    let Some(output) = run_contract_runner(
        "import asyncio\nimport collections.abc\n\ncreated = 0\n\nclass Stream(collections.abc.AsyncIterator):\n    def __init__(self, number): self.number = number\n    def __aiter__(self): return self\n    async def __anext__(self): raise StopAsyncIteration\n    async def aclose(self):\n        if self.number == 1: return\n        while True:\n            try: await asyncio.sleep(0)\n            except asyncio.CancelledError: pass\n\ndef stream(value: int) -> collections.abc.AsyncIterator[int]:\n    global created\n    created += 1\n    return Stream(created)\n",
        runner_request(declaration, vec![strategy]),
    ) else {
        return;
    };
    assert!(!output.status.success());
    assert!(
        String::from_utf8_lossy(&output.stderr)
            .contains("demo.stream: cancellation-resistant protocol close")
    );
}

#[test]
fn contract_runner_awaits_async_functions_and_detects_task_leaks() {
    let mut declaration = runner_function(
        "demo.run",
        vec![runner_clause(
            "ensures",
            0,
            runner_literal(json!({"kind": "bool", "value": true})),
        )],
    );
    declaration["callable_kind"] = json!("async");
    let mut strategy = runner_strategy("demo.run", vec!["ensures:0".to_owned()]);
    strategy["callable_kind"] = json!("async");
    let request = runner_request(declaration.clone(), vec![strategy.clone()]);

    let Some(output) = run_contract_runner(
        "import asyncio\npre_existing = asyncio.create_task(asyncio.Event().wait())\nexpected = iter((-1, 0, 1, 2, 255))\n\nasync def run(value: int) -> int:\n    assert value == next(expected)\n    async def child() -> int:\n        return value\n    return await asyncio.create_task(child())\n",
        request,
    ) else {
        return;
    };
    assert!(
        output.status.success(),
        "contract runner failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("contract report JSON");
    assert_eq!(report["contracts"][0]["evidence"][0]["valid_cases"], 5);
    assert!(report["contracts"][0]["evidence"][0]["reason"].is_null());

    let Some(sync) = run_contract_runner(
        "def run(value: int) -> int:\n    return value\n",
        runner_request(
            runner_function(
                "demo.run",
                vec![runner_clause(
                    "ensures",
                    0,
                    runner_literal(json!({"kind": "bool", "value": true})),
                )],
            ),
            vec![runner_strategy("demo.run", vec!["ensures:0".to_owned()])],
        ),
    ) else {
        return;
    };
    assert!(sync.status.success());
    let sync_report =
        serde_json::from_slice::<Value>(&sync.stdout).expect("sync contract report JSON");
    assert!(sync_report["contracts"][0]["evidence"][0]["reason"].is_null());
    assert_eq!(report, sync_report);

    let Some(violation) = run_contract_runner(
        "from cott_runtime import CottContractViolation\n\nasync def run() -> int:\n    raise CottContractViolation('bad')\n",
        runner_request(declaration.clone(), vec![strategy.clone()]),
    ) else {
        return;
    };
    assert!(!violation.status.success());
    assert!(
        String::from_utf8_lossy(&violation.stderr)
            .contains("demo.run: facade contract violation for generated valid case: bad")
    );

    let Some(cancellation) = run_contract_runner(
        "import asyncio\n\nasync def run() -> int:\n    raise asyncio.CancelledError\n",
        runner_request(declaration.clone(), vec![strategy.clone()]),
    ) else {
        return;
    };
    assert!(!cancellation.status.success());
    let cancellation_stderr = String::from_utf8_lossy(&cancellation.stderr);
    assert!(cancellation_stderr.contains("CancelledError"));
    assert!(!cancellation_stderr.contains("facade contract violation"));

    let Some(sync_leak) = run_contract_runner(
        "import asyncio\n\ndef run() -> int:\n    asyncio.create_task(asyncio.Event().wait())\n    return 1\n",
        runner_request(
            runner_function(
                "demo.run",
                vec![runner_clause(
                    "ensures",
                    0,
                    runner_literal(json!({"kind": "bool", "value": true})),
                )],
            ),
            vec![runner_strategy("demo.run", vec!["ensures:0".to_owned()])],
        ),
    ) else {
        return;
    };
    assert!(!sync_leak.status.success());
    assert!(String::from_utf8_lossy(&sync_leak.stderr).contains("demo.run: leaked 1 task(s)"));

    let Some(direct_task_leak) = run_contract_runner(
        "import asyncio\n\ndef run() -> int:\n    asyncio.Task(asyncio.Event().wait())\n    return 1\n",
        runner_request(
            runner_function(
                "demo.run",
                vec![runner_clause(
                    "ensures",
                    0,
                    runner_literal(json!({"kind": "bool", "value": true})),
                )],
            ),
            vec![runner_strategy("demo.run", vec!["ensures:0".to_owned()])],
        ),
    ) else {
        return;
    };
    assert!(!direct_task_leak.status.success());
    assert!(
        String::from_utf8_lossy(&direct_task_leak.stderr).contains("demo.run: leaked 1 task(s)")
    );

    let Some(failing_child) = run_contract_runner(
        "import asyncio\n\nasync def run() -> int:\n    async def child() -> None:\n        raise RuntimeError('boom')\n    asyncio.create_task(child())\n    await asyncio.sleep(0)\n    return 1\n",
        runner_request(declaration.clone(), vec![strategy.clone()]),
    ) else {
        return;
    };
    assert!(!failing_child.status.success());
    assert!(
        String::from_utf8_lossy(&failing_child.stderr)
            .contains("demo.run: child task failed with RuntimeError")
    );

    let Some(resistant_child) = run_contract_runner(
        "import asyncio\n\nasync def run() -> int:\n    async def child() -> None:\n        while True:\n            try:\n                await asyncio.sleep(0)\n            except asyncio.CancelledError:\n                pass\n    asyncio.create_task(child())\n    return 1\n",
        runner_request(declaration.clone(), vec![strategy.clone()]),
    ) else {
        return;
    };
    assert!(!resistant_child.status.success());
    assert!(
        String::from_utf8_lossy(&resistant_child.stderr)
            .contains("demo.run: cancellation-resistant task leak")
    );

    for body in [
        "asyncio.create_task(asyncio.Event().wait())\n    return 1",
        "asyncio.create_task(asyncio.Event().wait())\n    raise RuntimeError('boom')",
        "asyncio.create_task(asyncio.Event().wait())\n    raise asyncio.CancelledError",
    ] {
        let source = format!("import asyncio\n\nasync def run() -> int:\n    {body}\n");
        let Some(output) = run_contract_runner(
            &source,
            runner_request(declaration.clone(), vec![strategy.clone()]),
        ) else {
            return;
        };
        assert!(!output.status.success());
        assert!(
            String::from_utf8_lossy(&output.stderr).contains("demo.run: leaked 1 task(s)"),
            "{}",
            String::from_utf8_lossy(&output.stderr)
        );
    }
}
