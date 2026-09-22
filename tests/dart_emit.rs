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
fn finite_payloadless_enums_project_to_native_dart_enums() {
    let (config, plan) = fixture(
        r#"module api.shapes

enum Kind:
    Kind
    Local
    Remote

enum Payload:
    Empty
    Value(value: I32)

enum Wrapped[T]:
    Absent

const DEFAULT_KIND: Kind = Kind.Local
"#,
    );
    let emission = emit(&config, &plan, &[]).expect("native enum package emits");
    let types =
        std::str::from_utf8(&emission.files[Path::new("dart/lib/src/types/api/shapes.dart")])
            .unwrap();

    assert!(
        types.contains("\nenum Kind implements cott_runtime.CottVariant {\n")
            && types.contains("  Kind$('api.shapes.Kind.Kind'),\n")
            && types.contains("  Local('api.shapes.Kind.Local'),\n")
            && types.contains("  Remote('api.shapes.Kind.Remote');\n")
            && types.contains("  const Kind(this.cottVariant);"),
        "{types}"
    );
    assert!(
        !types.contains("KindLocal")
            && !types.contains("KindRemote")
            && !types.contains("sealed class Kind"),
        "eligible enums must not keep obsolete variant classes: {types}"
    );
    assert!(
        types.contains("cott_runtime.CottList<String> get cottFieldNames => _cott_no_field_names;")
            && types
                .contains("cott_runtime.CottList<Object?> get cottPayload => _cott_no_payload;")
            && types.matches("_cott_no_field_names = ").count() == 1,
        "native metadata must reuse one shared empty list per module: {types}"
    );
    assert!(
        types.contains("final Kind DEFAULT_KIND = Kind.Local;"),
        "{types}"
    );
    assert!(
        types.contains("sealed class Payload implements cott_runtime.CottVariant")
            && types.contains("final class PayloadEmpty extends Payload")
            && types.contains("final class PayloadValue extends Payload")
            && types.contains("sealed class Wrapped<T>")
            && types.contains("final class WrappedAbsent<T> extends Wrapped<T>"),
        "payload and generic enums must keep sealed value-carrying classes: {types}"
    );
    assert_eq!(
        emission.public_symbols["api.shapes"],
        ["DEFAULT_KIND", "Kind", "Payload", "Wrapped"]
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

#[test]
fn readable_module_prefixes_remain_injective_across_type_and_value_emission() {
    let (config, _) = fixture("module api.values\n\nfn run(value: I32) -> I32\n");
    let modules = [
        ("a_.b", "_cott_t_a_u__b", "Left"),
        ("a._b", "_cott_t_a___ub", "Right"),
        ("a__b", "_cott_t_a_u_ub", "Flat"),
        ("a.b", "_cott_t_a__b", "Nested"),
        ("foo_bar.baz", "_cott_t_foo_ubar__baz", "Readable"),
    ];
    let mut sources = modules
        .iter()
        .map(|(module, _, name)| {
            SourceFile::new(
                format!("src/{}.cott", module.replace('.', "/")),
                format!("module {module}\n\nstruct {name}:\n    value: I32\n"),
            )
        })
        .collect::<Vec<_>>();
    sources.push(SourceFile::new(
        "src/api/values.cott",
        r#"module api.values

use a_.b.{Left}
use a._b.{Right}
use a__b.{Flat}
use a.b.{Nested}
use foo_bar.baz.{Readable}

struct Bundle:
    left: Left
    right: Right
    flat: Flat
    nested: Nested
    readable: Readable

enum Choice:
    On
    Off

fn choose(value: Choice) -> Choice:
    ensures result == Choice.On

fn retain(value: Bundle) -> Bundle
"#,
    ));
    let ir = render(
        &lower(
            Path::new("src"),
            parse_project(sources).expect("boundary module names parse"),
        )
        .expect("distinct underscore and dotted module names lower"),
    )
    .expect("boundary module names retain canonical identities");
    let plan = DartPlan::from_ir(&ir).expect("boundary module names project");
    let choose = agent_binding(
        &plan,
        "api.values.choose",
        "return _cott_t_api__values.Choice.On;",
    );
    let retain = agent_binding(&plan, "api.values.retain", "return value;");
    for binding in [&choose, &retain] {
        cott::dart::binding::validate_candidate(
            &config,
            &plan,
            callable(&plan, &binding.cott_symbol),
            &Default::default(),
            &binding.bytes,
        )
        .expect("distinct legal modules must not collide in compiler import authority");
    }
    let emission = emit(&config, &plan, &[choose, retain])
        .expect("distinct legal modules must not collide during package emission");
    let types =
        std::str::from_utf8(&emission.files[Path::new("dart/lib/src/types/api/values.dart")])
            .unwrap();
    for (module, prefix, name) in modules {
        let ty = json!({"kind":"named","name":format!("{module}.{name}"),"args":[]});
        assert_eq!(render_type(&plan, &ty).unwrap(), format!("{prefix}.{name}"));
        let path = module.replace('.', "/");
        assert!(
            types.contains(&format!(
                "import 'package:dart_emit/src/types/{path}.dart' as {prefix};"
            )),
            "{types}"
        );
        assert!(
            emission
                .files
                .contains_key(Path::new(&format!("dart/lib/modules/{path}.dart")))
        );
        assert_eq!(emission.public_symbols[module], [name]);
    }
    let wrapper = std::str::from_utf8(
        &emission.files[Path::new("dart/lib/src/wrappers/api/values/choose.dart")],
    )
    .unwrap();
    assert!(
        wrapper.contains("_cott_t_api__values.Choice.On") && !wrapper.contains("ChoiceOn"),
        "{wrapper}"
    );
    assert!(
        wrapper.contains(
            "import 'package:dart_emit/src/types/api/values.dart' as _cott_t_api__values;"
        ),
        "{wrapper}"
    );
    assert_eq!(
        implementation_signature(&plan, callable(&plan, "api.values.choose")).unwrap(),
        "_cott_t_api__values.Choice _cott_api_values_choose(_cott_t_api__values.Choice value)"
    );
}

#[test]
fn scalar_agent_helpers_are_not_confused_with_nominal_import_aliases() {
    let (config, plan) = fixture("module t\n\nfn run(value: I32) -> I32\n");
    let callable = callable(&plan, "t.run");
    let source = "int _cott_t_run(int value) { return value; }\n";
    assert_eq!(
        implementation_signature(&plan, callable).unwrap(),
        "int _cott_t_run(int value)"
    );
    cott::dart::binding::validate_candidate(
        &config,
        &plan,
        callable,
        &Default::default(),
        source.as_bytes(),
    )
    .expect("unchanged scalar helper names remain accepted even under module t");
}
