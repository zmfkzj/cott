use std::path::PathBuf;

use cott::contract_test::{Classification, ContractTestStrategy, derive_strategies};
use cott::hash::sha256_hex;
use cott::hir::ModuleId;
use cott::ir::{CanonicalIr, CanonicalModule, canonical_bytes};
use serde_json::{Value, json};

#[test]
fn strategy_has_fixed_deterministic_limits() {
    let strategy = ContractTestStrategy::new(
        "foo.bar.run",
        b"canonical-ir",
        Classification::Pure,
        vec!["requires:0".to_owned()],
    );
    assert_eq!(strategy.candidate_limit, 64);
    assert_eq!(strategy.container_length_limit, 3);
    assert_eq!(strategy.json_depth_limit, 4);
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
                "kind": "requires",
                "span": span()
            }),
            "ensures" => json!({
                "clause_id": clause_id,
                "expression": literal_expression(),
                "kind": "ensures",
                "pattern": null,
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
        "body": null,
        "contract": {"clauses": clauses, "effects": effects},
        "doc": null,
        "generics": [],
        "kind": "function",
        "name": symbol,
        "parameters": [],
        "public": true,
        "return_type": {"kind": "primitive", "name": return_name},
        "source_order": 0,
        "span": span()
    })
}

fn module(name: &str, declarations: Vec<Value>) -> CanonicalModule {
    let value = json!({
        "declarations": declarations,
        "imports": [],
        "module": name,
        "schema_version": 1,
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
