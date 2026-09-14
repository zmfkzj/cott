use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

use cott::compiler::{SourceFile, parse_project};
use cott::dart::emit::{emit, implementation_signature, render_type};
use cott::dart::{DartBinding, DartOwner, DartPlan};
use cott::hash::sha256_hex;
use cott::hir::lower;
use cott::ir::render;
use cott::manifest::{
    DartProjectConfig, DartTarget, GeneratorConfig, ProjectMetadata, RuntimeValidation,
    VerificationConfig,
};
use serde_json::json;

fn fixture(source: &str) -> (DartProjectConfig, DartPlan) {
    let module = source
        .lines()
        .find_map(|line| line.strip_prefix("module "))
        .and_then(|module| module.split_whitespace().next())
        .expect("Dart emitter fixture declares a module");
    let source_path = format!("src/{}.cott", module.replace('.', "/"));
    let parsed =
        parse_project([SourceFile::new(source_path, source)]).expect("Dart emitter fixture parses");
    let ir = render(&lower(Path::new("src"), parsed).expect("fixture lowers"))
        .expect("fixture renders canonical IR");
    let plan = DartPlan::from_ir(&ir).expect("fixture projects to Dart");
    let config = DartProjectConfig {
        project: ProjectMetadata {
            name: "dart_emit".to_owned(),
            version: "0.1.0".to_owned(),
            source: "src".to_owned(),
        },
        dart: DartTarget {
            source: "dart".to_owned(),
            generated: "generated/dart".to_owned(),
            sdk: "dart".to_owned(),
            runtime_validation: RuntimeValidation::Boundary,
            pubspec: None,
            lockfile: None,
            implementations: BTreeMap::new(),
            external_types: BTreeMap::new(),
        },
        effects: BTreeMap::new(),
        generator: GeneratorConfig::default(),
        verification: VerificationConfig::default(),
    };
    (config, plan)
}

fn callable<'a>(plan: &'a DartPlan, symbol: &str) -> &'a cott::dart::DartCallable {
    plan.callables()
        .iter()
        .find(|callable| callable.symbol == symbol)
        .expect("fixture callable exists")
}

fn agent_binding(plan: &DartPlan, symbol: &str, body: &str) -> DartBinding {
    let callable = callable(plan, symbol);
    let signature = implementation_signature(plan, callable).expect("signature renders");
    agent_source_binding(symbol, format!("{signature} {{\n{body}\n}}\n").into_bytes())
}

fn agent_source_binding(symbol: &str, bytes: Vec<u8>) -> DartBinding {
    let relative = format!("cott_impl/{}.dart", symbol.replace('.', "/"));
    DartBinding {
        cott_symbol: symbol.to_owned(),
        target_symbol: format!("{relative}:_cott_{}", symbol.replace('.', "_")),
        source_origin: PathBuf::from(&relative),
        runtime_origin: PathBuf::from(format!("dart/lib/src/{relative}")),
        content_hash: format!("sha256:{}", sha256_hex(&bytes)),
        bytes,
        owner: DartOwner::Agent,
    }
}

#[test]
fn primitive_and_container_types_preserve_dart_abi_distinctions() {
    let (_, plan) = fixture("module api.values\n\nstruct Marker:\n    value: I32\n");
    let cases = [
        (json!({"kind":"primitive","name":"i32"}), "int"),
        (json!({"kind":"primitive","name":"u32"}), "int"),
        (json!({"kind":"primitive","name":"i64"}), "BigInt"),
        (json!({"kind":"primitive","name":"u64"}), "BigInt"),
        (
            json!({"kind":"primitive","name":"path"}),
            "cott_runtime.CottPath",
        ),
        (
            json!({"kind":"result","ok":{"kind":"primitive","name":"i32"},"error":{"kind":"primitive","name":"str"}}),
            "cott_runtime.CottResult<int, String>",
        ),
    ];
    for (canonical, expected) in cases {
        assert_eq!(render_type(&plan, &canonical).unwrap(), expected);
    }
}

#[test]
fn implementation_signatures_expose_exact_type_const_and_mutation_witnesses() {
    let (_, generic) = fixture(
        "module api.values\n\nfn echo[T, const N: U32](value: T, data: Array[U8, N]) -> T\n",
    );
    assert_eq!(
        implementation_signature(&generic, callable(&generic, "api.values.echo")).unwrap(),
        "T _cott_api_values_echo<T, N extends cott_runtime.CottConst>(T value, cott_runtime.CottArray<int, N> data, cott_runtime.CottType<T> _cott_type_T, N _cott_const_N)"
    );

    let (_, stateful) = fixture(
        r#"module api.counter

trait Counter:
    fn increment(self, amount: I32) -> I32

impl CounterState for Counter:
    state:
        value: I32 = 0
    fn increment(self, amount: I32) -> I32:
        modifies self.value
        ensures result >= 0
"#,
    );
    assert_eq!(
        implementation_signature(
            &stateful,
            callable(&stateful, "api.counter.CounterState.increment")
        )
        .unwrap(),
        "int _cott_api_counter_CounterState_increment(CounterState self, int amount, cott_runtime.CottStateMutation _cott_mutation, cott_runtime.CottGuardLease _cott_lease)"
    );
}

#[test]
fn unresolved_public_contract_omits_only_the_callable_wrapper() {
    let (config, plan) = fixture("module api.service\n\nfn run() -> I32\n");
    let emission = emit(&config, &plan, &[]).expect("unresolved package still emits");

    assert_eq!(emission.unresolved, ["api.service.run"]);
    assert_eq!(emission.public_symbols["api.service"], ["run"]);
    assert_eq!(
        emission.files[Path::new("dart/lib/modules/api/service.dart")],
        b"// Generated by Cott. Do not edit.\nexport 'package:dart_emit/src/types/api/service.dart';\n"
    );
    assert!(
        !emission
            .files
            .contains_key(Path::new("dart/lib/src/wrappers/api/service/run.dart"))
    );
}

#[test]
fn managed_part_identity_is_distinct_from_exact_authored_binding_identity() {
    let (config, plan) = fixture("module api.service\n\nfn run() -> I32\n");
    let binding = agent_binding(&plan, "api.service.run", "  return 7;");
    let authored = binding.bytes.clone();
    let authored_hash = binding.content_hash.clone();
    let emission = emit(&config, &plan, &[binding]).expect("resolved package emits");
    let managed = &emission.files[Path::new("dart/lib/src/cott_impl/api/service/run.dart")];

    assert_ne!(managed, &authored);
    assert_ne!(format!("sha256:{}", sha256_hex(managed)), authored_hash);
    assert_eq!(
        managed,
        b"part of 'package:dart_emit/src/wrappers/api/service/run.dart';\n\nint _cott_api_service_run() {\n  return 7;\n}\n"
    );
    assert_eq!(
        emission.files[Path::new("ir/api/service.json")],
        plan.ir.modules[0].bytes
    );
}

#[test]
fn generic_payload_variants_and_recursive_nominals_emit_closed_type_libraries() {
    let (config, plan) = fixture(
        r#"module graph.model

enum Choice[T]:
    Empty
    Value(value: T)

struct Node:
    value: I32
    next: Option[Node]

struct SharedNode:
    children: List[SharedNode]
"#,
    );
    let emission = emit(&config, &plan, &[]).expect("recursive nominal package emits");

    assert_eq!(
        emission.public_symbols["graph.model"],
        ["Choice", "Node", "SharedNode"]
    );
    assert!(emission.unresolved.is_empty());
    assert!(
        emission
            .files
            .contains_key(Path::new("dart/lib/src/types/graph/model.dart"))
    );
    assert!(
        emission
            .files
            .contains_key(Path::new("dart/lib/src/cott_markers.dart"))
    );
}

#[test]
fn multiple_declaration_callable_and_associated_bounds_are_projectable() {
    let (config, plan) = fixture(
        r#"module api.bounds

trait Left:
    type Item

trait Right:
    type Label

trait Bounded:
    type Value: Left + Right

enum Choice[T: Left + Right]:
    Empty

fn retain[T: Left + Right](value: T) -> T
"#,
    );

    implementation_signature(&plan, callable(&plan, "api.bounds.retain"))
        .expect("multiple callable and inherited associated bounds should project");
    emit(&config, &plan, &[])
        .expect("multiple declaration and trait-associated bounds should emit");
}
