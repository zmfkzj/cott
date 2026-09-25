use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};

use cott::contract_test::{Classification, ContractTestStrategy, derive_strategies};
use cott::hash::sha256_hex;
use cott::hir::ModuleId;
use cott::ir::{CanonicalIr, CanonicalModule, canonical_bytes};
use cott::manifest::VerificationConfig;
use cott::python_runtime::render_runtime;
use serde_json::{Value, json};

#[test]
fn strategy_has_default_and_fixed_limits() {
    let strategy = ContractTestStrategy::new(
        "foo.bar.run",
        b"canonical-ir",
        "sync",
        Classification::Pure,
        vec!["requires:0".to_owned()],
        &VerificationConfig::default(),
    );
    assert_eq!(strategy.proof_node_limit, 1024);
    assert_eq!(strategy.proof_branch_limit, 256);
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

#[test]
fn derived_strategy_serializes_verification_limits() {
    let config = VerificationConfig {
        proof_node_limit: 17,
        proof_branch_limit: 19,
        candidate_limit: 23,
        lifecycle_limit: 29,
        ..VerificationConfig::default()
    };
    let ir = CanonicalIr {
        modules: vec![module(
            "configured",
            vec![function("configured.run", "bool", &[], &[])],
        )],
    };
    let strategy = derive_strategies(&ir, &config)
        .expect("configured strategy")
        .pop()
        .expect("one strategy");
    assert_eq!(
        serde_json::to_value(&strategy).expect("strategy JSON"),
        json!({
            "schema_version": 6,
            "symbol": "configured.run",
            "seed": format!("sha256:{}", sha256_hex(&ir.modules[0].bytes)),
            "proof_node_limit": 17,
            "proof_branch_limit": 19,
            "candidate_limit": 23,
            "node_limit": 64,
            "container_length_limit": 3,
            "json_depth_limit": 4,
            "lifecycle_limit": 29,
            "callable_kind": "sync",
            "return_kind": "value",
            "classification": "pure",
            "obligations": [],
            "scenario": null,
            "clause_ids": [],
        })
    );
}

#[test]
fn strategy_schema_rejects_invalid_configurable_limits() {
    for config in [
        VerificationConfig {
            proof_node_limit: 0,
            ..VerificationConfig::default()
        },
        VerificationConfig {
            proof_node_limit: 16_385,
            ..VerificationConfig::default()
        },
        VerificationConfig {
            proof_branch_limit: 0,
            ..VerificationConfig::default()
        },
        VerificationConfig {
            proof_branch_limit: 4_097,
            ..VerificationConfig::default()
        },
        VerificationConfig {
            candidate_limit: 0,
            ..VerificationConfig::default()
        },
        VerificationConfig {
            candidate_limit: 1_025,
            ..VerificationConfig::default()
        },
        VerificationConfig {
            lifecycle_limit: 0,
            ..VerificationConfig::default()
        },
        VerificationConfig {
            lifecycle_limit: 65,
            ..VerificationConfig::default()
        },
    ] {
        assert!(
            ContractTestStrategy::new(
                "configured.run",
                b"canonical-ir",
                "sync",
                Classification::Pure,
                Vec::new(),
                &config,
            )
            .bytes()
            .is_err()
        );
    }
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
        "schema_version": 9,
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
    let first =
        derive_strategies(&ir, &VerificationConfig::default()).expect("canonical IR strategies");
    let second =
        derive_strategies(&ir, &VerificationConfig::default()).expect("canonical IR strategies");
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
    let strategies =
        derive_strategies(&ir, &VerificationConfig::default()).expect("canonical IR strategies");
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
    let strategies =
        derive_strategies(&ir, &VerificationConfig::default()).expect("canonical IR strategies");
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
    let strategies =
        derive_strategies(&ir, &VerificationConfig::default()).expect("canonical IR strategies");
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
    let strategy = derive_strategies(
        &CanonicalIr {
            modules: vec![module("async_fixture", vec![declaration])],
        },
        &VerificationConfig::default(),
    )
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
    let strategy = derive_strategies(
        &CanonicalIr {
            modules: vec![module(
                "fixture",
                vec![implementation(
                    "fixture.Stream",
                    Some((vec![], vec![])),
                    &[],
                    vec![method],
                )],
            )],
        },
        &VerificationConfig::default(),
    )
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
    let strategy = derive_strategies(
        &CanonicalIr {
            modules: vec![module("async_fixture", vec![declaration])],
        },
        &VerificationConfig::default(),
    )
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

    let strategies =
        derive_strategies(&ir, &VerificationConfig::default()).expect("canonical impl strategies");
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
    let strategies =
        derive_strategies(&ir, &VerificationConfig::default()).expect("selected strategies");
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
    let strategies = derive_strategies(
        &CanonicalIr {
            modules: vec![module("fixture", vec![parent, child, implementation])],
        },
        &VerificationConfig::default(),
    )
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
        derive_strategies(&ir, &VerificationConfig::default())
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
    let strategy = derive_strategies(&ir, &VerificationConfig::default())
        .expect("canonical function strategy")
        .pop()
        .expect("function strategy");
    let expected = ContractTestStrategy::new(
        "compat.run",
        &ir.modules[0].bytes,
        "sync",
        Classification::Pure,
        vec!["requires:4".to_owned(), "ensures:9".to_owned()],
        &VerificationConfig::default(),
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

    let error = derive_strategies(&ir, &VerificationConfig::default())
        .expect_err("missing return type must fail");
    assert!(error.contains("schema violation"));
}
#[test]
fn contract_runner_observes_local_result_error_variant() {
    let Some(output) = run_emitted_contract_runner(
        "module demo\n\nenum Failure:\n    Bad\n\nfn run(succeed: Bool) -> Result[Bool, Failure]:\n    ensures Result.Ok(value) => value == succeed\n    error Failure.Bad\n",
        &[(
            "demo.run",
            "from cott_runtime import Err, Ok, Result\nfrom demo_types import Failure_Bad\n\ndef run(succeed: bool) -> Result[bool, Failure_Bad]:\n    if succeed:\n        return Ok(value=True)\n    return Err(error=Failure_Bad())\n",
        )],
        &["demo.run"],
    ) else {
        return;
    };
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("contract report JSON");
    let contracts = report["contracts"].as_array().expect("reported contracts");
    assert_eq!(contracts.len(), 2);
    for contract in contracts {
        let evidence = &contract["evidence"][0];
        assert_eq!(evidence["valid_cases"], 1);
        assert_eq!(evidence["grade"], "test observation");
    }
    let success = &contracts[0]["evidence"][0];
    assert_eq!(success["eligible_cases"], 2);
    assert_eq!(success["applicable_cases"], 1);
    assert_eq!(success["satisfied_cases"], 1);
}

fn run_contract_runner(source: &str, request: Value) -> Option<std::process::Output> {
    let mut files = render_runtime("demo", "0.4.0");
    files.insert(PathBuf::from("demo.py"), source.as_bytes().to_vec());
    run_contract_runner_files(files, Path::new("."), request)
}

fn run_contract_runner_files(
    files: std::collections::BTreeMap<PathBuf, Vec<u8>>,
    python_dir: &Path,
    request: Value,
) -> Option<std::process::Output> {
    run_python_fixture(
        files,
        python_dir,
        include_str!("../src/contract_runner.py"),
        request.to_string(),
    )
}

/// Run `program` against emitted fixture files with the executing interpreter
/// recorded in the generation record, so runtime provenance checks stay active.
fn run_python_fixture(
    mut files: std::collections::BTreeMap<PathBuf, Vec<u8>>,
    python_dir: &Path,
    program: &str,
    stdin: String,
) -> Option<std::process::Output> {
    if !Command::new("python3")
        .arg("--version")
        .output()
        .is_ok_and(|output| output.status.success())
    {
        return None;
    }
    if let Some(bytes) = files.get_mut(Path::new("generation.json")) {
        // Record the interpreter that actually executes these emitted fixtures,
        // including its executable digest; keep runtime provenance checks active.
        let output = Command::new("python3")
            .args([
                "-c",
                r#"import hashlib,json,pathlib,platform,sys,sysconfig
e=pathlib.Path(sys.executable).resolve()
print(json.dumps({"cache_tag":sys.implementation.cache_tag,"content_hash":"sha256:"+hashlib.sha256(e.read_bytes()).hexdigest(),"executable":str(e),"implementation":sys.implementation.name,"machine":platform.machine(),"os":sys.platform,"platform":sysconfig.get_platform(),"version":platform.python_version()}))
"#,
            ])
            .output()
            .expect("Python should inspect fixture provenance");
        assert!(
            output.status.success(),
            "{}",
            String::from_utf8_lossy(&output.stderr)
        );
        let python_tools: Value =
            serde_json::from_slice(&output.stdout).expect("Python tool evidence JSON");
        let mut record: cott::provenance::GenerationRecord =
            serde_json::from_slice(bytes).expect("emitted generation record");
        for snapshot in std::iter::once(&mut record.current).chain(record.last_verified.iter_mut())
        {
            snapshot.tools["python"] = python_tools.clone();
            snapshot
                .compute_generation_id()
                .expect("recompute fixture generation identity");
        }
        *bytes = record
            .canonical_bytes()
            .expect("serialize fixture generation record");
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
    for (relative, bytes) in files {
        let path = root.join(relative);
        fs::create_dir_all(path.parent().expect("runtime file parent")).expect("runtime parent");
        fs::write(path, bytes).expect("runtime file");
    }
    let mut child = Command::new("python3")
        .args(["-c", program])
        .current_dir(root.join(python_dir))
        .env("PYTHONPATH", root.join(python_dir))
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
        .write_all(stdin.as_bytes())
        .expect("contract runner request");
    let output = child
        .wait_with_output()
        .expect("contract runner should finish");
    fs::remove_dir_all(root).expect("contract runner fixture cleanup");
    Some(output)
}

/// Exercise compiler-emitted boundaries, not a runner-side interpretation of
/// their predicates. Candidate-only tests below deliberately use broader Python
/// annotation shapes and provide their own explicit checked facade instead.
fn run_emitted_contract_runner(
    source: &str,
    implementations: &[(&str, &str)],
    symbols: &[&str],
) -> Option<std::process::Output> {
    let (files, ir) = emit_python_fixture(source, implementations);
    let strategies = derive_strategies(&ir, &VerificationConfig::default())
        .expect("fixture strategies")
        .into_iter()
        .filter(|strategy| symbols.contains(&strategy.symbol.as_str()))
        .collect::<Vec<_>>();
    let modules = ir
        .modules
        .iter()
        .map(|module| serde_json::from_slice::<Value>(&module.bytes).unwrap())
        .collect::<Vec<_>>();
    run_contract_runner_files(
        files,
        Path::new("python"),
        json!({"modules": modules, "runtime_validation": "boundary", "strategies": strategies}),
    )
}

/// Emit boundary-mode Python facades with manifest-bound fixture implementations.
fn emit_python_fixture(
    source: &str,
    implementations: &[(&str, &str)],
) -> (
    std::collections::BTreeMap<PathBuf, Vec<u8>>,
    cott::ir::CanonicalIr,
) {
    use cott::binding::{BindingOwner, ResolvedBinding};
    use cott::compiler::{SourceFile, parse_project};
    use cott::python::artifact_plan::{PythonArtifactPlan, PythonCallableKind};

    let mut config = cott::manifest::ProjectConfig::parse(
        Path::new("cott.toml"),
        "[project]\nname = \"demo\"\nversion = \"0.4.0\"\nsource = \"src\"\n\
         [target.python]\nsource = \"python\"\ngenerated = \"generated/python\"\n\
         stubs = \"generated/stubs\"\ninterpreter = \".venv/bin/python\"\n\
         type_checker = \".venv/bin/basedpyright\"\nruntime_validation = \"boundary\"\n",
    )
    .expect("fixture manifest");
    let parsed = parse_project([SourceFile::new("src/demo.cott", source)]).expect("fixture parse");
    let hir = cott::hir::lower(Path::new("src"), parsed).expect("fixture lower");
    let ir = cott::ir::render(&hir).expect("fixture canonical IR");
    let plan = PythonArtifactPlan::from_ir(&ir).expect("fixture plan");
    let callables = plan.callables();
    let bindings = implementations
        .iter()
        .map(|(symbol, source)| {
            let callable = callables
                .iter()
                .find(|callable| callable.cott_symbol == *symbol)
                .expect("fixture callable");
            let mut relative = PathBuf::from("_cott_impl").join(&callable.module);
            let implementation_function = match &callable.kind {
                PythonCallableKind::Function | PythonCallableKind::AsyncFunction => {
                    callable.name.clone()
                }
                PythonCallableKind::ImplMethod { concrete }
                | PythonCallableKind::AsyncImplMethod { concrete } => {
                    relative.push(concrete);
                    format!("_cott_impl_{concrete}_{}", callable.name)
                }
            };
            relative.push(format!("{}.py", callable.name));
            let manifest_owned = matches!(
                callable.kind,
                PythonCallableKind::Function | PythonCallableKind::AsyncFunction
            );
            let implementation_module = format!(
                "{}.{symbol}",
                if manifest_owned {
                    "cott_bindings"
                } else {
                    "_cott_impl"
                }
            );
            if manifest_owned {
                config.python.implementations.insert(
                    (*symbol).to_owned(),
                    format!("{implementation_module}:{implementation_function}"),
                );
            }
            ResolvedBinding {
                module: callable.module.clone(),
                function: callable.name.clone(),
                cott_symbol: callable.cott_symbol.clone(),
                kind: callable.kind.clone(),
                implementation_module: implementation_module.clone(),
                implementation_function,
                owner: if manifest_owned {
                    BindingOwner::Manifest
                } else {
                    BindingOwner::Agent
                },
                source: PathBuf::from("python")
                    .join(format!("{}.py", implementation_module.replace('.', "/"))),
                generated_relative: relative,
                bytes: source.as_bytes().to_vec(),
                sha256: sha256_hex(source.as_bytes()),
            }
        })
        .collect::<Vec<_>>();
    let emission =
        cott::python_emit::emit(&config, &plan, &ir, &bindings).expect("fixture emission");
    (emission.files, ir)
}

fn runner_strategy(symbol: &str, clause_ids: Vec<String>) -> Value {
    json!({
        "callable_kind": "sync",
        "return_kind": "value",
        "classification": "pure",
        "clause_ids": clause_ids,
        "schema_version": 6,
        "seed": "sha256:test",
        "symbol": symbol,
        "proof_node_limit": 1024,
        "proof_branch_limit": 256,
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

fn runner_self_field(name: &str) -> Value {
    runner_expression(
        "field",
        json!({"base": runner_expression("self_ref", json!({})), "name": name}),
    )
}

fn runner_comparison(left: Value, operator: &str, right: Value) -> Value {
    runner_expression(
        "comparison_chain",
        json!({"operands": [left, right], "operators": [operator]}),
    )
}

fn runner_nonnegative_result() -> Value {
    let mut result = runner_expression("result_ref", json!({}));
    result["type"] = json!({"kind": "primitive", "name": "i32"});
    let mut zero = runner_literal(json!({"kind": "integer", "value": "0"}));
    zero["type"] = json!({"kind": "primitive", "name": "i32"});
    runner_comparison(result, "greater_equal", zero)
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
            "schema_version": 9,
            "source": "demo.cott"
        }],
        "runtime_validation": "boundary",
        "strategies": strategies
    })
}

#[test]
fn contract_runner_uses_first_applicable_conditional_error() {
    let source = "module demo\n\nenum Failure:\n    First\n    Second\n\nfn run(fail: Bool) -> Result[I32, Failure]:\n    ensures Result.Ok(value) => value > 0\n    error Failure.First when fail\n    error Failure.Second when fail\n";
    let implementation = "from cott_runtime import Err, Ok, Result\nfrom demo_types import Failure_First, Failure_Second\n\ndef run(fail: bool) -> Result[int, Failure_First | Failure_Second]:\n    if fail:\n        return Err(error=Failure_First())\n    return Ok(value=1)\n";
    let Some(output) =
        run_emitted_contract_runner(source, &[("demo.run", implementation)], &["demo.run"])
    else {
        return;
    };
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("contract report JSON");
    let success = &report["contracts"][0]["evidence"][0];
    assert_eq!(success["grade"], "test observation");
    assert_eq!(success["applicable_cases"], 1);
    assert_eq!(success["satisfied_cases"], 1);
    let first = &report["contracts"][1]["evidence"][0];
    let second = &report["contracts"][2]["evidence"][0];
    assert_eq!(first["grade"], "test observation");
    assert_eq!(first["eligible_cases"], 2);
    assert_eq!(first["applicable_cases"], 1);
    assert_eq!(first["satisfied_cases"], 1);
    assert_eq!(second["grade"], "unobserved");
    assert_eq!(second["eligible_cases"], 2);
    assert_eq!(second["applicable_cases"], 0);
    assert_eq!(second["satisfied_cases"], 0);
    assert_eq!(
        second["condition_false_cases"], 1,
        "only the successful case has a false predicate; the shadowed error is skipped"
    );

    let wrong = implementation.replace(
        "return Err(error=Failure_First())",
        "return Err(error=Failure_Second())",
    );
    let Some(output) = run_emitted_contract_runner(source, &[("demo.run", &wrong)], &["demo.run"])
    else {
        return;
    };
    assert!(!output.status.success());
    let error = String::from_utf8_lossy(&output.stderr);
    assert!(error.contains("CottContractViolation") && error.contains("demo.run"));
}

#[test]
fn contract_runner_keeps_unobserved_success_as_evidence() {
    let Some(output) = run_emitted_contract_runner(
        "module demo\n\nenum Failure:\n    Bad\n\nfn run() -> Result[I32, Failure]:\n    ensures Result.Ok(value) => value > 0\n    error Failure.Bad\n",
        &[(
            "demo.run",
            "from cott_runtime import Err, Result\nfrom demo_types import Failure_Bad\n\ndef run() -> Result[int, Failure_Bad]:\n    return Err(error=Failure_Bad())\n",
        )],
        &["demo.run"],
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
    assert_eq!(evidence["eligible_cases"], 1);
    assert_eq!(evidence["applicable_cases"], 0);
    assert_eq!(evidence["satisfied_cases"], 0);
    assert_eq!(evidence["condition_false_cases"], 1);
}

#[test]
fn contract_runner_generates_homogeneous_tuple_candidates() {
    let declaration = runner_function(
        "demo.accepts_tuple",
        vec![runner_clause("ensures", 0, runner_nonnegative_result())],
    );
    let Some(output) = run_contract_runner(
        "from cott_runtime import CottContractViolation, _cott_contract_condition\n\ndef accepts_tuple(value: tuple[int, ...]) -> int:\n    result = len(value)\n    if not _cott_contract_condition(result >= 0, 'demo.accepts_tuple', 'ensures:0'):\n        raise CottContractViolation('negative length', symbol='demo.accepts_tuple', phase='ensures')\n    return result\n",
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
        vec![runner_clause("ensures", 0, runner_nonnegative_result())],
    );
    let source = "from __future__ import annotations\nimport dataclasses\nfrom cott_runtime import CottContractViolation, _cott_contract_condition\n\n@dataclasses.dataclass(frozen=True)\nclass Tree_Leaf:\n    value: int\n\n@dataclasses.dataclass(frozen=True)\nclass Tree_Branch:\n    child: Tree\n\nTree = Tree_Leaf | Tree_Branch\n\ndef accepts_tree(value: Tree) -> int:\n    result = 0\n    while isinstance(value, Tree_Branch):\n        result += 1\n        value = value.child\n    assert isinstance(value, Tree_Leaf)\n    if not _cott_contract_condition(result >= 0, 'demo.accepts_tree', 'ensures:0'):\n        raise CottContractViolation('negative depth', symbol='demo.accepts_tree', phase='ensures')\n    return result\n";
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
        vec![runner_clause("ensures", 0, runner_nonnegative_result())],
    );
    let Some(output) = run_contract_runner(
        "import typing\nimport cott_runtime\n\ndef accepts_empty(values: cott_runtime.CottList[typing.Any], mapping: cott_runtime.FrozenMap[object, typing.Annotated[int, cott_runtime.CottExternal('outside')]], array: cott_runtime.CottArray[typing.Any, typing.Literal[0]]) -> int:\n    result = len(values) + len(mapping) + len(array)\n    assert result == 0, 'unavailable elements must not be synthesized'\n    if not cott_runtime._cott_contract_condition(result >= 0, 'demo.accepts_empty', 'ensures:0'):\n        raise cott_runtime.CottContractViolation('negative length', symbol='demo.accepts_empty', phase='ensures')\n    return result\n",
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
        vec![runner_clause("ensures", 0, runner_nonnegative_result())],
    );
    let Some(output) = run_contract_runner(
        "from __future__ import annotations\nimport dataclasses\nimport cott_runtime\n\n@dataclasses.dataclass(frozen=True)\nclass Node:\n    children: cott_runtime.CottList[Node]\n\ndef accepts_node(value: Node) -> int:\n    result = len(value.children)\n    if not cott_runtime._cott_contract_condition(result >= 0, 'demo.accepts_node', 'ensures:0'):\n        raise cott_runtime.CottContractViolation('negative length', symbol='demo.accepts_node', phase='ensures')\n    return result\n",
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
        vec![runner_clause("ensures", 0, runner_nonnegative_result())],
    );
    let Some(output) = run_contract_runner(
        "from __future__ import annotations\nimport dataclasses\nimport typing\nfrom cott_runtime import CottContractViolation, _cott_contract_condition\n\nT = typing.TypeVar('T')\n\n@dataclasses.dataclass(frozen=True)\nclass Tree_Empty(typing.Generic[T]):\n    pass\n\n@dataclasses.dataclass(frozen=True)\nclass Tree_Node(typing.Generic[T]):\n    child: Tree[T]\n\nTree = Tree_Empty[T] | Tree_Node[T]\n\ndef accepts_tree(value: Tree[typing.Any]) -> int:\n    result = 0\n    while isinstance(value, Tree_Node):\n        result += 1\n        value = value.child\n    assert isinstance(value, Tree_Empty)\n    if not _cott_contract_condition(result >= 0, 'demo.accepts_tree', 'ensures:0'):\n        raise CottContractViolation('negative depth', symbol='demo.accepts_tree', phase='ensures')\n    return result\n",
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
        "import typing\nimport cott_runtime\n\nT = typing.TypeVar('T')\n\nclass GenericTrait(typing.Protocol[T]):\n    _cott_trait = True\n    def read(self) -> T: ...\n\nclass Counter:\n    _cott_traits = (GenericTrait,)\n    _cott_trait_specs = (GenericTrait[cott_runtime.I32],)\n\n    def __init__(self) -> None:\n        self.count = 0\n        self.guard = 0\n        if not cott_runtime._cott_contract_condition(self.count >= 0, 'demo.Counter.init', 'invariant:0'):\n            raise cott_runtime.CottContractViolation('negative count', symbol='demo.Counter.init', phase='invariant')\n\n    def read(self) -> cott_runtime.I32:\n        return self.count\n\n    def accepts(self, value: cott_runtime.Dyn[GenericTrait[cott_runtime.I32]]) -> int:\n        result = value.value.read()\n        if not cott_runtime._cott_contract_condition(self.count >= 0, 'demo.Counter.accepts', 'invariant:0'):\n            raise cott_runtime.CottContractViolation('negative count', symbol='demo.Counter.accepts', phase='invariant')\n        return result\n\n    def rejects(self, value: cott_runtime.Dyn[GenericTrait[str]]) -> int:\n        raise AssertionError('Dyn with the wrong generic specification must not be selected')\n",
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
    let Some(output) = run_emitted_contract_runner(
        "module demo\n\nfn stream() -> Iterator[I32]:\n    requires true\n",
        &[(
            "demo.stream",
            "import collections.abc\n\nclass Trap(collections.abc.Iterator):\n    def __iter__(self):\n        raise AssertionError('iterator return was consumed')\n\n    def __next__(self):\n        raise AssertionError('iterator return was consumed')\n\ndef stream() -> collections.abc.Iterator[int]:\n    return Trap()\n",
        )],
        &["demo.stream"],
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
    assert_eq!(report["contracts"][0]["evidence"][0]["valid_cases"], 1);
}

#[test]
fn contract_runner_observes_free_function_result_at_the_emitted_boundary() {
    let source = "module demo\n\nfn identity(value: I32) -> I32:\n    ensures result == value\n";
    let Some(output) = run_emitted_contract_runner(
        source,
        &[(
            "demo.identity",
            "def identity(value: int) -> int:\n    return value\n",
        )],
        &["demo.identity"],
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
    let Some(wrong) = run_emitted_contract_runner(
        source,
        &[(
            "demo.identity",
            "def identity(value: int) -> int:\n    return 0\n",
        )],
        &["demo.identity"],
    ) else {
        return;
    };
    assert!(!wrong.status.success());
    assert!(String::from_utf8_lossy(&wrong.stderr).contains("CottContractViolation"));
}

#[test]
fn contract_runner_bounds_json_value_candidates() {
    let declaration = runner_function(
        "demo.accepts_json",
        vec![runner_clause("ensures", 0, runner_nonnegative_result())],
    );
    let Some(output) = run_contract_runner(
        "import sys\nsys.setrecursionlimit(32)\nfrom cott_runtime import JsonValue, JsonArray, JsonObject, CottContractViolation, _cott_contract_condition\n\ndef accepts_json(value: JsonValue) -> int:\n    result = len(value.value) if isinstance(value, (JsonArray, JsonObject)) else 0\n    if not _cott_contract_condition(result >= 0, 'demo.accepts_json', 'ensures:0'):\n        raise CottContractViolation('negative container size', symbol='demo.accepts_json', phase='ensures')\n    return result\n",
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
    let source = r#"module demo

enum Failure:
    Bad

trait Operations:
    fn advance(self, amount: I32) -> I32
    fn fail(self, amount: I32) -> Result[I32, Failure]

impl Counter for Operations:
    state:
        count: I32 = 0
        guard: I32 = 0
    invariant self.count >= 0
    fn advance(self, amount: I32) -> I32:
        requires amount >= 0
        modifies self.count
        ensures result == self.count
        ensures old(self.count) + amount == self.count
    fn fail(self, amount: I32) -> Result[I32, Failure]:
        modifies self.count
        error Failure.Bad when amount < 0
"#;
    let Some(output) = run_emitted_contract_runner(
        source,
        &[
            (
                "demo.Counter.advance",
                "from __future__ import annotations\n\ndef _cott_impl_Counter_advance(self: Counter, amount: int) -> int:\n    self.count += amount\n    return self.count\n",
            ),
            (
                "demo.Counter.fail",
                "from __future__ import annotations\nfrom cott_runtime import Err, Ok, Result\nfrom demo_types import Failure_Bad\n\ndef _cott_impl_Counter_fail(self: Counter, amount: int) -> Result[int, Failure_Bad]:\n    if amount < 0:\n        return Err(error=Failure_Bad())\n    self.count += amount\n    return Ok(value=self.count)\n",
            ),
        ],
        &[
            "demo.Counter.init",
            "demo.Counter.advance",
            "demo.Counter.fail",
        ],
    ) else {
        return;
    };
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("contract report JSON");
    assert!(
        report["contracts"]
            .as_array()
            .unwrap()
            .iter()
            .all(|contract| contract["evidence"][0]["grade"] == "test observation"),
        "{report}"
    );
}

#[test]
fn contract_runner_rejects_impl_forbidden_mutation_and_invariant_failure() {
    let source = r#"module demo

trait Operations:
    fn bad_modifies(self, amount: I32) -> I32
    fn bad_invariant(self, amount: I32) -> I32

impl Counter for Operations:
    state:
        count: I32 = 0
        guard: I32 = 0
    invariant self.count >= 0
    fn bad_modifies(self, amount: I32) -> I32:
        modifies self.count
    fn bad_invariant(self, amount: I32) -> I32:
        modifies self.count
"#;
    let implementations = [
        (
            "demo.Counter.bad_modifies",
            "from __future__ import annotations\n\ndef _cott_impl_Counter_bad_modifies(self: Counter, amount: int) -> int:\n    self.guard = amount\n    return self.count\n",
        ),
        (
            "demo.Counter.bad_invariant",
            "from __future__ import annotations\n\ndef _cott_impl_Counter_bad_invariant(self: Counter, amount: int) -> int:\n    self.count = -1\n    return self.count\n",
        ),
    ];
    for symbol in ["demo.Counter.bad_modifies", "demo.Counter.bad_invariant"] {
        let Some(output) = run_emitted_contract_runner(source, &implementations, &[symbol]) else {
            return;
        };
        assert!(
            !output.status.success(),
            "{symbol} must fail at its boundary"
        );
        let error = String::from_utf8_lossy(&output.stderr);
        assert!(
            error.contains("CottContractViolation") && error.contains(symbol),
            "{error}"
        );
    }
}

#[test]
fn contract_runner_constructs_methods_only_from_init_validated_cases() {
    let source = r#"module demo

trait Reader:
    fn read(self) -> I32

impl Counter for Reader:
    state:
        count: I32
    invariant self.count > 0
    init(count: I32):
        requires count > 0
        ensures self.count == count
    fn read(self) -> I32:
        ensures result == self.count
"#;
    let Some(output) = run_emitted_contract_runner(
        source,
        &[(
            "demo.Counter.read",
            "from __future__ import annotations\n\ndef _cott_impl_Counter_read(self: Counter) -> int:\n    assert self.count > 0, 'invalid constructor case reached method'\n    return self.count\n",
        )],
        &["demo.Counter.init", "demo.Counter.read"],
    ) else {
        return;
    };
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("contract report JSON");
    assert!(
        report["contracts"]
            .as_array()
            .unwrap()
            .iter()
            .all(|contract| contract["evidence"][0]["grade"] == "test observation"),
        "{report}"
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
        "import collections.abc\n\nclass Stream(collections.abc.AsyncIterator):\n    def __init__(self): self.steps = 0; self.closed = False\n    def __aiter__(self): return self\n    async def __anext__(self):\n        if self.closed or self.steps == 2: raise StopAsyncIteration\n        self.steps += 1\n        return self.steps\n    async def aclose(self): self.closed = True\n\ndef stream() -> collections.abc.AsyncIterator[int]:\n    return Stream()\n",
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
    assert_eq!(report["lifecycle"][0]["lifecycle_limit"], 3);
    assert_eq!(report["lifecycle"][0]["lifecycle_steps"], 2);
    assert_eq!(report["lifecycle"][0]["lifecycle_sent"], false);
    assert_eq!(report["lifecycle"][0]["lifecycle_closed"], true);
    assert_eq!(
        report["lifecycle"][0]["lifecycle_reason"],
        "protocol completed"
    );
    assert_eq!(
        report["lifecycle"][0]["operations"],
        json!([
            {"operation": "anext", "outcome": "yielded"},
            {"operation": "anext", "outcome": "yielded"},
            {"operation": "anext", "outcome": "completed"},
            {"operation": "aclose", "outcome": "closed"},
            {"operation": "aclose", "outcome": "already_closed"},
        ])
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
    assert_eq!(report["lifecycle"][0]["lifecycle_limit"], 3);
    assert_eq!(report["lifecycle"][0]["lifecycle_steps"], 1);
    assert_eq!(report["lifecycle"][0]["lifecycle_sent"], true);
    assert_eq!(report["lifecycle"][0]["lifecycle_closed"], true);
    assert_eq!(
        report["lifecycle"][0]["lifecycle_reason"],
        "protocol completed"
    );
    assert_eq!(
        report["lifecycle"][0]["operations"],
        json!([
            {"operation": "anext", "outcome": "yielded"},
            {"operation": "asend", "outcome": "completed"},
            {"operation": "aclose", "outcome": "closed"},
            {"operation": "aclose", "outcome": "already_closed"},
        ])
    );
    let mut limited_strategy = runner_strategy("demo.limited", vec!["ensures:0".to_owned()]);
    limited_strategy["return_kind"] = json!("async_iterator");
    limited_strategy["lifecycle_limit"] = json!(2);
    let Some(output) = run_contract_runner(
        "import collections.abc\n\nclass Stream(collections.abc.AsyncIterator):\n    def __aiter__(self): return self\n    async def __anext__(self): return 1\n    async def aclose(self): pass\n\ndef limited() -> collections.abc.AsyncIterator[int]:\n    return Stream()\n",
        runner_request(
            runner_function(
                "demo.limited",
                vec![runner_clause(
                    "ensures",
                    0,
                    runner_literal(json!({"kind": "bool", "value": true})),
                )],
            ),
            vec![limited_strategy],
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
    assert_eq!(report["lifecycle"][0]["lifecycle_limit"], 2);
    assert_eq!(report["lifecycle"][0]["lifecycle_steps"], 2);
    assert_eq!(
        report["lifecycle"][0]["lifecycle_reason"],
        "observation limit reached"
    );
    assert_eq!(
        report["lifecycle"][0]["operations"],
        json!([
            {"operation": "anext", "outcome": "yielded"},
            {"operation": "anext", "outcome": "yielded"},
            {"operation": "aclose", "outcome": "closed"},
            {"operation": "aclose", "outcome": "already_closed"},
        ])
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
    let Some(output) = run_emitted_contract_runner(
        "module demo\n\ntrait Reader:\n    async fn read(self) -> AsyncIterator[I32]\n\nimpl Counter for Reader:\n    state:\n        count: I32 = 0\n    invariant self.count >= 0\n    async fn read(self) -> AsyncIterator[I32]:\n        ensures true\n",
        &[(
            "demo.Counter.read",
            "from __future__ import annotations\nimport collections.abc\n\nclass Stream(collections.abc.AsyncIterator):\n    def __init__(self): self.step = 0; self.closed = False\n    def __aiter__(self): return self\n    async def __anext__(self):\n        if self.closed or self.step == 3: raise StopAsyncIteration\n        self.step += 1\n        return self.step\n    async def aclose(self): self.closed = True\n\nasync def _cott_impl_Counter_read(self: Counter) -> collections.abc.AsyncIterator[int]:\n    return Stream()\n",
        )],
        &["demo.Counter.read"],
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
            runner_comparison(
                runner_expression("result_ref", json!({})),
                "equal",
                runner_expression("parameter_ref", json!({"symbol": "demo.run.value"})),
            ),
        )],
    );
    declaration["callable_kind"] = json!("async");
    let mut strategy = runner_strategy("demo.run", vec!["ensures:0".to_owned()]);
    strategy["callable_kind"] = json!("async");
    let request = runner_request(declaration.clone(), vec![strategy.clone()]);

    let Some(output) = run_contract_runner(
        "import asyncio\nimport typing\nfrom cott_runtime import CottContractViolation, _cott_contract_condition\npre_existing = asyncio.create_task(asyncio.Event().wait())\nexpected = iter((-1, 0, 1, 2, 255))\n\nasync def run(value: int) -> int:\n    assert value == next(expected)\n    assert typing.get_origin(asyncio.Task[None]) is asyncio.Task\n    assert isinstance(asyncio.current_task(), asyncio.Task)\n    assert issubclass(type(asyncio.current_task()), asyncio.Task)\n    async def child() -> int:\n        return value\n    result = await asyncio.Task[int](child())\n    assert isinstance(awaited := asyncio.create_task(child()), asyncio.Task)\n    assert await awaited == value\n    if not _cott_contract_condition(result == value, 'demo.run', 'ensures:0'):\n        raise CottContractViolation('changed result', symbol='demo.run', phase='ensures')\n    return result\n",
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
        "from cott_runtime import CottContractViolation, _cott_contract_condition\n\ndef run(value: int) -> int:\n    result = value\n    if not _cott_contract_condition(result == value, 'demo.run', 'ensures:0'):\n        raise CottContractViolation('changed result', symbol='demo.run', phase='ensures')\n    return result\n",
        runner_request(
            runner_function(
                "demo.run",
                vec![runner_clause(
                    "ensures",
                    0,
                    runner_comparison(
                        runner_expression("result_ref", json!({})),
                        "equal",
                        runner_expression("parameter_ref", json!({"symbol": "demo.run.value"})),
                    ),
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
    let error = String::from_utf8_lossy(&violation.stderr);
    assert!(error.contains("CottContractViolation") && error.contains("demo.run"));

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

const TOPOLOGICAL_CONTRACT: &str = r#"module demo

struct BuildStep:
    name: Str
    needs: Set[Str]

enum PipelineError:
    BlankStepName
    DuplicateStep
    UnknownDependency
    SelfDependency
    Cycle

fn order_steps(steps: List[BuildStep]) -> Result[List[Str], PipelineError]:
    ensures Result.Ok(order) => permutation_by(order, steps, BuildStep.name)
    ensures Result.Ok(order) => dependency_ordered_by(order, steps, BuildStep.name, BuildStep.needs)

    errors complete
    error PipelineError.BlankStepName when any_blank_by(steps, BuildStep.name)
    error PipelineError.DuplicateStep when not unique_by(steps, BuildStep.name)
    error PipelineError.UnknownDependency when unknown_dependency_by(steps, BuildStep.name, BuildStep.needs)
    error PipelineError.SelfDependency when self_dependency_by(steps, BuildStep.name, BuildStep.needs)
    error PipelineError.Cycle when cyclic_by(steps, BuildStep.name, BuildStep.needs)
"#;

/// A typed, deterministic Kahn implementation. `order` and `check_first`
/// let deliberately wrong fixtures keep the exact valid signature.
fn topological_implementation(check_first: &str, finish: &str) -> String {
    format!(
        r#"from cott_runtime import CottList, Err, Ok, Result
from demo_types import BuildStep, PipelineError, PipelineError_BlankStepName, PipelineError_Cycle, PipelineError_DuplicateStep, PipelineError_SelfDependency, PipelineError_UnknownDependency

_WHITE_SPACE = frozenset("\t\n\x0b\x0c\r \x85\xa0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000")


def order_steps(steps: CottList[BuildStep]) -> Result[CottList[str], PipelineError]:
    names = [step.name for step in steps]
    known = set(names)
    unknown = any(need not in known for step in steps for need in step.needs)
{check_first}    if any(all(character in _WHITE_SPACE for character in name) for name in names):
        return Err(error=PipelineError_BlankStepName())
    if len(known) != len(names):
        return Err(error=PipelineError_DuplicateStep())
    if unknown:
        return Err(error=PipelineError_UnknownDependency())
    if any(step.name in step.needs for step in steps):
        return Err(error=PipelineError_SelfDependency())
    remaining = {{step.name: set(step.needs) for step in steps}}
    order: list[str] = []
    while remaining:
        ready = sorted(name for name, needs in remaining.items() if not needs)
        if not ready:
            return Err(error=PipelineError_Cycle())
        order.append(ready[0])
        del remaining[ready[0]]
        for needs in remaining.values():
            needs.discard(ready[0])
{finish}    return Ok(value=CottList(values=order))
"#
    )
}

const TOPOLOGICAL_DRIVER: &str = r#"import json
import sys

from cott_runtime import CottContractViolation, CottList, CottSet, Ok
import demo
from demo_types import BuildStep


def run(case):
    steps = CottList(values=[BuildStep(name=name, needs=CottSet(values=needs)) for name, needs in case])
    try:
        result = demo.order_steps(steps)
    except CottContractViolation as error:
        return {"violation": [error.phase, error.clause]}
    if type(result) is Ok:
        return {"ok": list(result.value)}
    return {"err": type(result.error).__name__}


print(json.dumps([run(case) for case in json.loads(sys.stdin.read())]))
"#;

fn topological_cases() -> Value {
    json!([
        [],
        [["b", ["a"]], ["a", []]],
        [["c", []], ["a", ["c"]], ["b", ["c"]]],
        [[" \u{3000}", []]],
        [["\u{feff}", []]],
        [["a", []], ["a", ["zz"]]],
        [["a", ["zz"]], ["b", ["b"]]],
        [["a", ["a"]], ["b", ["c"]], ["c", ["b"]]],
        [["a", ["b"]], ["b", ["a"]]]
    ])
}

fn run_topological_driver(implementation: &str) -> Option<Value> {
    let (files, _) = emit_python_fixture(
        TOPOLOGICAL_CONTRACT,
        &[("demo.order_steps", implementation)],
    );
    let output = run_python_fixture(
        files,
        Path::new("python"),
        TOPOLOGICAL_DRIVER,
        topological_cases().to_string(),
    )?;
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    Some(serde_json::from_slice(&output.stdout).expect("driver JSON"))
}

#[test]
fn complete_errors_topological_contract_accepts_ordering_precedence_and_unicode_blanks() {
    let Some(outcomes) = run_topological_driver(&topological_implementation("", "")) else {
        return;
    };
    assert_eq!(
        outcomes,
        json!([
            {"ok": []},
            {"ok": ["a", "b"]},
            {"ok": ["c", "a", "b"]},
            {"err": "PipelineError_BlankStepName"},
            // U+FEFF is not Unicode White_Space in any target.
            {"ok": ["\u{feff}"]},
            {"err": "PipelineError_DuplicateStep"},
            {"err": "PipelineError_UnknownDependency"},
            {"err": "PipelineError_SelfDependency"},
            {"err": "PipelineError_Cycle"}
        ])
    );
}

#[test]
fn complete_errors_topological_contract_rejects_wrong_typed_implementations_at_runtime() {
    let cases = [
        // Always an error, even for valid normal input.
        (
            topological_implementation("    return Err(error=PipelineError_Cycle())\n", ""),
            1,
            json!({"violation": ["error", null]}),
        ),
        // Valid shape, wrong multiplicity.
        (
            topological_implementation("", "    order = order[:1] + order\n"),
            1,
            json!({"violation": ["ensures", "ensures:0"]}),
        ),
        // Valid shape and multiset, dependencies after dependents.
        (
            topological_implementation("", "    order.reverse()\n"),
            2,
            json!({"violation": ["ensures", "ensures:1"]}),
        ),
        // Dependency errors checked before duplicate names.
        (
            topological_implementation(
                "    if unknown:\n        return Err(error=PipelineError_UnknownDependency())\n",
                "",
            ),
            5,
            json!({"violation": ["error", "error:4"]}),
        ),
    ];
    for (implementation, case, expected) in cases {
        let Some(outcomes) = run_topological_driver(&implementation) else {
            return;
        };
        assert_eq!(outcomes[case], expected, "{implementation}");
    }
}

#[test]
fn complete_errors_is_opt_in_and_rejects_err_without_conditional_clauses() {
    let implementation = "from cott_runtime import Err, Result\nfrom demo_types import Failure_Bad\n\ndef echo(value: str) -> Result[str, Failure_Bad]:\n    return Err(error=Failure_Bad())\n";
    let default = "module demo\n\nenum Failure:\n    Bad\n\nfn echo(value: Str) -> Result[Str, Failure]:\n    ensures Result.Ok(output) => output == value\n";
    let Some(output) =
        run_emitted_contract_runner(default, &[("demo.echo", implementation)], &["demo.echo"])
    else {
        return;
    };
    assert!(
        output.status.success(),
        "the default keeps Err unchecked without error clauses: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("contract report JSON");
    assert_eq!(report["contracts"][0]["evidence"][0]["grade"], "unobserved");

    let complete = default.replace("value\n", "value\n\n    errors complete\n");
    let Some(output) =
        run_emitted_contract_runner(&complete, &[("demo.echo", implementation)], &["demo.echo"])
    else {
        return;
    };
    assert!(!output.status.success());
    let error = String::from_utf8_lossy(&output.stderr);
    assert!(
        error.contains("CottContractViolation") && error.contains("returned error is not allowed"),
        "{error}"
    );
}

#[test]
fn complete_errors_runner_reports_success_only_from_exercised_normal_cases() {
    let Some(output) = run_emitted_contract_runner(
        TOPOLOGICAL_CONTRACT,
        &[("demo.order_steps", &topological_implementation("", ""))],
        &["demo.order_steps"],
    ) else {
        return;
    };
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("contract report JSON");
    for success in &report["contracts"].as_array().expect("contracts")[..2] {
        let evidence = &success["evidence"][0];
        assert_eq!(evidence["grade"], "test observation");
        // Only generated normal inputs (no conditional applies) reach `Ok`.
        assert!(
            evidence["applicable_cases"]
                .as_u64()
                .is_some_and(|cases| cases >= 1)
        );
        assert_eq!(evidence["applicable_cases"], evidence["satisfied_cases"]);
        assert!(evidence["applicable_cases"].as_u64() < evidence["eligible_cases"].as_u64());
    }

    let always_error =
        topological_implementation("    return Err(error=PipelineError_Cycle())\n", "");
    let Some(output) = run_emitted_contract_runner(
        TOPOLOGICAL_CONTRACT,
        &[("demo.order_steps", &always_error)],
        &["demo.order_steps"],
    ) else {
        return;
    };
    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("CottContractViolation"));
}

const SCENARIO_VALUES: &str = r#"module demo

enum Mode:
    Fast
    Careful(retries: U8)

struct Limits:
    timeout_ms: U32
    tags: List[Str]

    invariant self.timeout_ms > 0

struct Request:
    name: Str
    mode: Mode
    limits: Limits
    labels: Map[Str, U32]
    note: Option[Str]

enum Failure:
    Rejected(reason: Str)

struct Report:
    name: Str
    retries: U8

fn run(request: Request) -> Result[Report, Failure]:
    ensures Result.Ok(report) => report.retries >= 0

    error Failure.Rejected

data base_limits: Limits = Limits(timeout_ms: 30, tags: List("a", "b"))

scenario nested_request:
    data request: Request = Request(
        name: "job",
        mode: Mode.Careful(retries: 2),
        limits: base_limits,
        labels: Map("x": 1),
        note: Option.Some(value: "n"),
    )
    call outcome = run(request)
    assert outcome matches Result.Ok(report) => report.retries == 2
    assert outcome == Result.Ok(value: Report(name: "job", retries: 2))

scenario invalid_limits:
    data limits: Limits = Limits(timeout_ms: 0, tags: List())
    call outcome = run(Request(name: "x", mode: Mode.Fast, limits: limits, labels: Map(), note: Option.Nothing))
    assert outcome matches Result.Ok(_)
"#;

fn scenario_value_implementation(retries: &str) -> String {
    format!(
        "from cott_runtime import Ok, Result\nfrom demo_types import Failure_Rejected, Mode_Careful, Report, Request\n\ndef run(request: Request) -> Result[Report, Failure_Rejected]:\n    retries = {retries}\n    return Ok(value=Report(name=request.name, retries=retries))\n"
    )
}

#[test]
fn scenario_values_construct_nested_inputs_and_check_payloads() {
    let correct = scenario_value_implementation(
        "request.mode.retries if isinstance(request.mode, Mode_Careful) else 0",
    );
    let Some(output) = run_emitted_contract_runner(
        SCENARIO_VALUES,
        &[("demo.run", &correct)],
        &["demo.scenario.nested_request"],
    ) else {
        return;
    };
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("runner JSON");
    assert_eq!(report["scenarios"][0]["grade"], "test observation");
    assert_eq!(
        report["scenarios"][0]["assertions"]
            .as_array()
            .map(Vec::len),
        Some(2)
    );

    // An `Ok` shell with the wrong payload must fail the guarded assertion.
    let wrong_payload = scenario_value_implementation("0");
    let Some(output) = run_emitted_contract_runner(
        SCENARIO_VALUES,
        &[("demo.run", &wrong_payload)],
        &["demo.scenario.nested_request"],
    ) else {
        return;
    };
    assert!(!output.status.success());
    assert!(String::from_utf8_lossy(&output.stderr).contains("assertion step:2 failed"));
}

#[test]
fn scenario_values_run_canonical_struct_invariants() {
    let implementation = scenario_value_implementation("0");
    let Some(output) = run_emitted_contract_runner(
        SCENARIO_VALUES,
        &[("demo.run", &implementation)],
        &["demo.scenario.invalid_limits"],
    ) else {
        return;
    };
    assert!(!output.status.success());
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(
        stderr.contains("CottContractViolation") && stderr.contains("invariant"),
        "{stderr}"
    );
}

#[test]
fn scenario_values_construct_and_compare_error_payloads() {
    let source = format!(
        "{SCENARIO_VALUES}\nscenario error_payload:\n    data outcome: Result[Report, Failure] = Result.Err(error: Failure.Rejected(reason: \"denied\"))\n    assert outcome matches Result.Err(Failure.Rejected(reason)) => reason == \"denied\"\n    assert outcome == Result.Err(error: Failure.Rejected(reason: \"denied\"))\n"
    );
    let implementation = scenario_value_implementation("0");
    let Some(output) = run_emitted_contract_runner(
        &source,
        &[("demo.run", &implementation)],
        &["demo.scenario.error_payload"],
    ) else {
        return;
    };
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("runner JSON");
    assert_eq!(report["scenarios"][0]["grade"], "test observation");
    assert_eq!(
        report["scenarios"][0]["assertions"]
            .as_array()
            .map(Vec::len),
        Some(2)
    );
}

const INTRINSIC_ASSERTIONS: &str = r#"module demo

struct Step:
    name: Str
    needs: Set[Str]

fn names(steps: List[Step]) -> List[Str]:
    effects []

fn label(name: Str) -> Str:
    effects []

scenario properties:
    data steps: List[Step] = List(
        Step(name: "b", needs: Set()),
        Step(name: "a", needs: Set("b")),
    )
    call listed = names(steps)
    assert permutation_by(listed, steps, Step.name) and dependency_ordered_by(listed, steps, Step.name, Step.needs)
    call tagged = label("x")
    assert starts_with(tagged, "cott-") and contains(tagged, "x")
"#;

fn intrinsic_assertion_implementations(names: &str, label: &str) -> [(&'static str, String); 2] {
    [
        (
            "demo.names",
            format!(
                "from cott_runtime import CottList\nfrom demo_types import Step\n\ndef names(steps: CottList[Step]) -> CottList[str]:\n    return CottList(values={names})\n"
            ),
        ),
        (
            "demo.label",
            format!("def label(name: str) -> str:\n    return {label}\n"),
        ),
    ]
}

#[test]
fn scenario_assertions_evaluate_closed_intrinsics_like_facade_contracts() {
    let run = |names: &str, label: &str| {
        let implementations = intrinsic_assertion_implementations(names, label);
        let implementations = implementations
            .iter()
            .map(|(symbol, source)| (*symbol, source.as_str()))
            .collect::<Vec<_>>();
        run_emitted_contract_runner(
            INTRINSIC_ASSERTIONS,
            &implementations,
            &["demo.scenario.properties"],
        )
    };
    let Some(output) = run("[step.name for step in steps]", "\"cott-\" + name") else {
        return;
    };
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("runner JSON");
    assert_eq!(report["scenarios"][0]["grade"], "test observation");

    for (names, label, failed_step) in [
        // A lost element violates the multiset predicate.
        ("[step.name for step in steps][:1]", "\"cott-\" + name", 2),
        // The right multiset in the wrong dependency order.
        (
            "[step.name for step in reversed(steps)]",
            "\"cott-\" + name",
            2,
        ),
        // String predicates use Cott semantics, not truthiness.
        ("[step.name for step in steps]", "name", 4),
    ] {
        let Some(output) = run(names, label) else {
            return;
        };
        assert!(!output.status.success(), "{names} / {label} passed");
        let stderr = String::from_utf8_lossy(&output.stderr);
        assert!(
            stderr.contains(&format!("assertion step:{failed_step} failed")),
            "{stderr}"
        );
    }
}

const SCENARIO_IMPL_DYN: &str = r#"module demo
trait TaskView[+T]:
    fn summary(self) -> T
impl SimpleTask for TaskView[Str]:
    state:
        title: Str
        urgency: I32
    init(title: Str, urgency: I32):
        ensures self.title == title
        ensures self.urgency == urgency
    fn summary(self) -> Str:
        ensures result == self.title
        effects []
fn inspect(view: Dyn[TaskView[Str]]) -> Str:
    effects []
scenario dispatches:
    call task = SimpleTask(title: "Launch", urgency: 1)
    call summary = task.summary()
    assert summary == "Launch"
    data view: Dyn[TaskView[Str]] = Dyn(value: task)
    call observed = inspect(view)
    assert observed == "Launch"
    call nested = inspect(Dyn(value: task))
    assert nested == "Launch"
"#;

fn scenario_impl_dyn_bindings(summary: &str, inspect: &str) -> [(&'static str, String); 2] {
    [
        (
            "demo.SimpleTask.summary",
            format!(
                "from __future__ import annotations\n\ndef _cott_impl_SimpleTask_summary(self: SimpleTask) -> str:\n    return {summary}\n"
            ),
        ),
        (
            "demo.inspect",
            format!(
                "from cott_runtime import Dyn\nfrom demo import TaskView\n\ndef inspect(view: Dyn[TaskView[str]]) -> str:\n    return {inspect}\n"
            ),
        ),
    ]
}

#[test]
fn emitted_python_scenarios_execute_impl_init_receiver_method_and_nested_dyn() {
    let run = |summary: &str, inspect: &str| {
        let implementations = scenario_impl_dyn_bindings(summary, inspect);
        let borrowed = implementations
            .iter()
            .map(|(symbol, source)| (*symbol, source.as_str()))
            .collect::<Vec<_>>();
        run_emitted_contract_runner(SCENARIO_IMPL_DYN, &borrowed, &["demo.scenario.dispatches"])
    };
    let Some(output) = run("self.title", "view.value.summary()") else {
        return;
    };
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("runner JSON");
    assert_eq!(report["scenarios"][0]["grade"], "test observation");
    for (summary, inspect, expected) in [
        ("self.title", "\"wrong\"", "assertion step:5 failed"),
        ("\"wrong\"", "view.value.summary()", "ensures clause failed"),
    ] {
        let Some(output) = run(summary, inspect) else {
            return;
        };
        assert!(!output.status.success(), "{summary} / {inspect} passed");
        let stderr = String::from_utf8_lossy(&output.stderr);
        assert!(stderr.contains(expected), "{stderr}");
    }
}
