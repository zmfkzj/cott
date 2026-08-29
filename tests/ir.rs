use std::collections::BTreeSet;
use std::path::{Path, PathBuf};

use cott::compiler::{SourceFile, parse_project};
use cott::hir::{HirModule, HirProject, ModuleId};
use cott::ir::{load, render};

#[test]
fn checked_in_canonical_ir_schema_is_parseable() {
    let text = std::str::from_utf8(include_bytes!("../schemas/canonical-ir.schema.json"))
        .expect("canonical IR schema must be UTF-8");
    let schema: serde_json::Value =
        serde_json::from_str(text).expect("canonical IR schema must be valid JSON");
    let object = schema
        .as_object()
        .expect("canonical IR schema must be a JSON object");

    assert_eq!(
        object.keys().map(String::as_str).collect::<BTreeSet<_>>(),
        BTreeSet::from([
            "$defs",
            "$id",
            "$schema",
            "additionalProperties",
            "properties",
            "required",
            "title",
            "type",
        ])
    );
    assert_eq!(
        object.get("$schema").and_then(serde_json::Value::as_str),
        Some("https://json-schema.org/draft/2020-12/schema")
    );
    assert_eq!(
        object.get("$id").and_then(serde_json::Value::as_str),
        Some("https://cott.dev/schema/canonical-ir/v8")
    );
    assert_eq!(
        object
            .get("properties")
            .and_then(serde_json::Value::as_object)
            .and_then(|properties| properties.get("schema_version"))
            .and_then(serde_json::Value::as_object)
            .and_then(|version| version.get("const"))
            .and_then(serde_json::Value::as_u64),
        Some(8)
    );

    let definitions = object
        .get("$defs")
        .and_then(serde_json::Value::as_object)
        .expect("canonical IR schema must define $defs");
    for definition in [
        "pattern",
        "contract",
        "effect",
        "tfactory",
        "tdyn",
        "specialization",
    ] {
        assert!(
            definitions.contains_key(definition),
            "canonical IR schema must define $defs.{definition}"
        );
    }
    let factory = definitions
        .get("tfactory")
        .and_then(serde_json::Value::as_object)
        .expect("canonical IR schema must define Factory");
    assert_eq!(factory["required"], serde_json::json!(["instance", "kind"]));
    assert_eq!(factory["additionalProperties"], false);
    assert_eq!(factory["properties"]["instance"]["$ref"], "#/$defs/tn");
    assert_eq!(
        definitions["tdyn"]["properties"]["trait"]["$ref"],
        "#/$defs/tn"
    );

    for definition in ["tasync_iterator", "tasync_generator"] {
        assert!(
            definitions.contains_key(definition),
            "canonical IR schema must define $defs.{definition}"
        );
    }
    assert_eq!(
        definitions["tasync_generator"]["required"],
        serde_json::json!(["kind", "yield", "send"])
    );
    for definition in ["method", "impl_method", "selected_method"] {
        assert!(
            definitions[definition]["required"]
                .as_array()
                .expect("method schema must declare required fields")
                .contains(&serde_json::json!("callable_kind")),
            "canonical IR schema must require callable kind on {definition}"
        );
    }
}

fn source(path: &str, text: &str) -> SourceFile {
    SourceFile::new(PathBuf::from(path), text)
}

fn project() -> HirProject {
    let parsed = parse_project([
        source(
            "src/types/core.cott",
            r#"module types.core

newtype UserId(I32)

enum Status:
    Ready
    Failed(code: I32, label: Str)

struct User:
    id: UserId
    status: Status
"#,
        ),
        source(
            "src/api/service.cott",
            r#"module api.service
use types.core.{UserId, Status, User}

doc """alias-doc"""
alias MaybeUser = Option[User]
alias Outcome = Result[User, Status]

struct Envelope:
    first: MaybeUser
    second: UserId

enum Decision:
    Open
    Closed(reason: Str, code: I32)

fn run() -> Outcome
"#,
        ),
    ])
    .expect("IR fixture must parse");

    cott::hir::lower(Path::new("src"), parsed).expect("IR fixture must lower")
}

fn advanced_types_project() -> HirProject {
    let parsed = parse_project([source(
        "src/types/advanced.cott",
        r#"module types.advanced

external type PyIterator

alias Anything = Any
alias UnknownValue = Unknown
alias Imported = PyIterator
alias Stream = Generator[Opaque["yield"], Unknown, Iterator[Opaque["handle"]]]
alias AsyncStream = AsyncGenerator[Opaque["async-yield"], Opaque["async-send"]]

fn consume(items: Iterator[Opaque["handle"]]) -> Stream
fn consume_async(items: AsyncIterator[Opaque["async-handle"]]) -> AsyncStream
"#,
    )])
    .expect("advanced type fixture must parse");

    cott::hir::lower(Path::new("src"), parsed).expect("advanced type fixture must lower")
}

fn factory_project() -> HirProject {
    let parsed = parse_project([source(
        "src/factories/counter.cott",
        r#"module factories.counter

trait Counter:
    fn count(self) -> I32

impl CounterState for Counter:
    state:
        count: I32 = 0
    fn count(self) -> I32:
        effects []

alias CounterFactory = Factory[CounterState]

fn make() -> CounterFactory
"#,
    )])
    .expect("Factory IR fixture must parse");

    cott::hir::lower(Path::new("src"), parsed).expect("Factory IR fixture must lower")
}

fn impl_project() -> HirProject {
    let parsed = parse_project([source(
        "src/impls/counter.cott",
        r#"module impls.counter

trait Counter:
    fn advance(self, amount: I32) -> I32
    fn read(self) -> I32

impl CounterState for Counter:
    state:
        count: I32 = 0
    invariant self.count >= 0
    init():
        doc """initialize"""
        ensures self.count == 0
    fn advance(self, amount: I32) -> I32:
        doc """advance"""
        requires amount > 0
        modifies self.count
        ensures result == self.count
        ensures old(self.count) + amount == self.count
        effects [network]
    fn read(self) -> I32:
        ensures result == self.count
"#,
    )])
    .expect("impl IR fixture must parse");

    cott::hir::lower(Path::new("src"), parsed).expect("impl IR fixture must lower")
}

fn json(module: &cott::ir::CanonicalModule) -> &str {
    std::str::from_utf8(&module.bytes).expect("canonical IR must be UTF-8")
}

fn assert_in_order(text: &str, values: &[&str]) {
    let mut previous = 0;
    for value in values {
        let position = text[previous..]
            .find(value)
            .unwrap_or_else(|| panic!("missing {value:?} in {text}"))
            + previous;
        previous = position + value.len();
    }
}

#[test]
fn renders_deterministic_owned_hir_modules() {
    let project = project();
    let first = render(&project).expect("owned HIR must render");
    let second = render(&project).expect("owned HIR must render twice");

    assert_eq!(first.modules.len(), 2);
    assert_eq!(first.modules.len(), second.modules.len());
    assert_eq!(
        first
            .modules
            .iter()
            .map(|module| module.module.as_string())
            .collect::<Vec<_>>(),
        ["types.core", "api.service"]
    );
    for (left, right) in first.modules.iter().zip(&second.modules) {
        assert_eq!(left.bytes, right.bytes);
        let text = json(left);
        assert!(text.ends_with('\n'));
        assert!(!text[..text.len() - 1].chars().any(char::is_whitespace));
    }

    let api = json(&first.modules[1]);
    assert!(api.contains(r#""module":"api.service""#));
    assert_in_order(
        api,
        &[
            r#""declarations":"#,
            r#""imports":"#,
            r#""module":"#,
            r#""schema_version":"#,
            r#""source":"#,
        ],
    );
    assert_in_order(
        api,
        &[
            r#""name":"api.service.MaybeUser""#,
            r#""name":"api.service.Outcome""#,
            r#""name":"api.service.Envelope""#,
            r#""name":"api.service.Decision""#,
            r#""name":"api.service.run""#,
        ],
    );
    assert!(api.contains(r#""kind":"option""#));
    assert!(api.contains(r#""kind":"result""#));
    assert!(api.contains(r#""text":"alias-doc""#));
    assert!(api.contains(r#""start_byte":"#));
    assert!(api.contains(r#""start_line":"#));
    assert!(api.contains(r#""start_column":"#));
}

#[test]
fn renders_and_closes_advanced_type_nodes() {
    let project = advanced_types_project();
    let first = render(&project).expect("advanced HIR must render");
    let second = render(&project).expect("advanced HIR must render twice");
    assert_eq!(first.modules[0].bytes, second.modules[0].bytes);

    let text = json(&first.modules[0]);
    assert!(text.contains(r#""schema_version":8"#));
    assert_in_order(
        text,
        &[
            r#""annotations":[]"#,
            r#""doc":null"#,
            r#""kind":"external_type""#,
            r#""name":"types.advanced.PyIterator""#,
            r#""public":true"#,
            r#""source_order":0"#,
            r#""span":"#,
        ],
    );
    assert!(text.contains(r#"{"kind":"primitive","name":"any"}"#));
    assert!(text.contains(r#"{"kind":"primitive","name":"unknown"}"#));
    assert!(text.contains(r#"{"args":[],"kind":"named","name":"types.advanced.PyIterator"}"#));
    assert!(text.contains(r#"{"item":{"kind":"opaque","tag":"handle"},"kind":"iterator"}"#));
    assert!(text.contains(
        r#"{"kind":"generator","return":{"item":{"kind":"opaque","tag":"handle"},"kind":"iterator"},"send":{"kind":"primitive","name":"unknown"},"yield":{"kind":"opaque","tag":"yield"}}"#,
    ));
    assert!(text.contains(
        r#"{"kind":"async_generator","send":{"kind":"opaque","tag":"async-send"},"yield":{"kind":"opaque","tag":"async-yield"}}"#,
    ));
    assert!(text.contains(
        r#"{"item":{"kind":"opaque","tag":"async-handle"},"kind":"async_iterator"}"#,
    ));

    let value = load(&first.modules[0].bytes).expect("advanced canonical IR must load");
    assert_eq!(value["schema_version"], 8);
    assert_eq!(value["declarations"][0]["kind"], "external_type");
    let external = value["declarations"][0]
        .as_object()
        .expect("external declaration object");
    assert!(!external.contains_key("target"));
    assert!(!external.contains_key("path"));
    assert_eq!(
        value["declarations"][0]["name"],
        "types.advanced.PyIterator"
    );
    assert_eq!(value["declarations"][0]["public"], true);
    assert_eq!(value["declarations"][4]["target"]["kind"], "generator");
}

#[test]
fn renders_and_closes_factory_type_nodes() {
    let rendered = render(&factory_project()).expect("Factory HIR must render");
    let text = json(&rendered.modules[0]);
    assert!(text.contains(
        r#"{"instance":{"args":[],"kind":"named","name":"factories.counter.CounterState"},"kind":"factory"}"#,
    ));

    let value = load(&rendered.modules[0].bytes).expect("Factory canonical IR must load");
    assert_eq!(value["schema_version"], 8);
    let declarations = value["declarations"].as_array().expect("declarations");
    let alias = declarations
        .iter()
        .find(|declaration| declaration["kind"] == "alias")
        .expect("Factory alias declaration");
    assert_eq!(alias["name"], "factories.counter.CounterFactory");
    assert_eq!(alias["public"], true);
    assert_eq!(alias["target"]["kind"], "factory");
    assert_eq!(
        alias["target"]["instance"]["name"],
        "factories.counter.CounterState"
    );

    let factory = declarations
        .iter()
        .find(|declaration| declaration["kind"] == "function")
        .expect("Factory-returning function")["return_type"]
        .as_object()
        .expect("Factory return type");
    assert_eq!(factory["kind"], "factory");
    assert_eq!(factory["instance"]["kind"], "named");
    assert_eq!(
        factory["instance"]["name"],
        "factories.counter.CounterState"
    );
}

#[test]
fn hand_built_hir_needs_no_semantic_snapshot() {
    let project = HirProject::new(vec![HirModule {
        source: PathBuf::from("src/empty.cott"),
        source_bytes: std::sync::Arc::from(&b"module empty\n"[..]),
        id: ModuleId::new(vec!["empty".into()]),
        imports: Vec::new(),
        declarations: Vec::new(),
        source_order: 0,
    }]);
    let first = render(&project).expect("hand-built HIR must render");
    let second = render(&project).expect("hand-built HIR must render deterministically");
    assert_eq!(first.modules[0].bytes, second.modules[0].bytes);
    assert!(first.modules[0].bytes.ends_with(b"\n"));
}

#[test]
fn load_rejects_unknown_declaration_fields() {
    let rendered = render(&project()).expect("fixture must render");
    let mut value: serde_json::Value = serde_json::from_slice(&rendered.modules[0].bytes).unwrap();
    value["declarations"][0]["unknown"] = serde_json::Value::Null;
    let mut bytes = serde_json::to_vec(&value).unwrap();
    bytes.push(b'\n');
    let error = load(&bytes).expect_err("unknown declaration fields must be rejected");
    assert!(error.contains("schema violation"));
}

#[test]
fn renders_and_validates_canonical_ir_for_rules() {
    let parsed = parse_project([source(
        "src/rules.cott",
        r#"module rules

struct Assignment:
    name: Str
    value: Str

enum ParseAssignmentError:
    MissingEquals
    EmptyName

rule BaseAssignmentRule:
    doc """Base assignment rule."""
    ensures Result.Ok(assignment) => assignment.name.len > 0
    error ParseAssignmentError.MissingEquals

rule StrictAssignmentRule(BaseAssignmentRule):
    doc """Strict assignment rule."""
    override ensures Result.Ok(assignment) => assignment.name.len > 1
    delete error ParseAssignmentError.MissingEquals
    ensures Result.Ok(assignment) => assignment.value.len > 0
    error ParseAssignmentError.EmptyName
"#,
    )])
    .expect("IR fixture with rules must parse");

    let hir = cott::hir::lower(Path::new("src"), parsed).expect("IR fixture with rules must lower");
    let rendered = render(&hir).expect("IR with rules must render");
    assert_eq!(rendered.modules.len(), 1);

    let text = json(&rendered.modules[0]);
    assert!(text.contains(r#""kind":"rule""#));
    assert!(text.contains(r#""name":"rules.BaseAssignmentRule""#));
    assert!(text.contains(r#""name":"rules.StrictAssignmentRule""#));
    assert!(text.contains(r#""base":"rules.BaseAssignmentRule""#));

    // Validate that load parses and validates against the schema
    let loaded = load(&rendered.modules[0].bytes).expect("canonical IR with rules must load");
    assert_eq!(loaded["module"], "rules");
}

#[test]
fn renders_exact_deterministic_impl_canonical_ir() {
    let project = impl_project();
    let first = render(&project).expect("impl HIR must render");
    let second = render(&project).expect("impl HIR must render twice");
    assert_eq!(first.modules[0].bytes, second.modules[0].bytes);

    let text = json(&first.modules[0]);
    let impl_start = text[..text.find(r#""kind":"impl""#).expect("impl declaration")]
        .rfind(r#"{"annotations""#)
        .expect("impl declaration start");
    assert_in_order(
        &text[impl_start..],
        &[
            r#""annotations":"#,
            r#""doc":null"#,
            r#""generics":[]"#,
            r#""init":"#,
            r#""invariants":"#,
            r#""kind":"impl""#,
            r#""methods":"#,
            r#""name":"impls.counter.CounterState""#,
            r#""state":"#,
            r#""traits":"#,
        ],
    );
    assert!(text.contains(r#""kind":"result_ref""#));
    assert!(text.contains(r#""kind":"old_state_field""#));

    let value = load(&first.modules[0].bytes).expect("impl canonical IR must load");
    let implementation = value["declarations"]
        .as_array()
        .expect("declarations")
        .iter()
        .find(|declaration| declaration["kind"] == "impl")
        .expect("impl declaration");
    assert_eq!(implementation["traits"][0]["kind"], "named");
    assert_eq!(implementation["traits"][0]["name"], "impls.counter.Counter");
    assert_eq!(implementation["state"][0]["name"], "count");
    assert_eq!(implementation["invariants"][0]["clause_id"], 0);
    assert_eq!(implementation["init"]["contracts"]["doc"], "initialize");
    assert_eq!(implementation["methods"][0]["name"], "advance");
    assert_eq!(implementation["methods"][0]["contracts"]["doc"], "advance");
    assert_eq!(implementation["methods"][0]["effects"][0]["key"], "network");
    assert_eq!(
        implementation["methods"][0]["modifies"][0],
        "impls.counter.CounterState.count"
    );
    assert_eq!(implementation["methods"][1]["name"], "read");
}

#[test]
fn renders_option_nothing_state_default_with_implicit_initializer() {
    let parsed = parse_project([source(
        "src/impls/option_state.cott",
        r#"module impls.option_state

trait Holder:
    fn value(self) -> Option[Any]

impl HolderState for Holder:
    state:
        value: Option[Any] = Option.Nothing
    fn value(self) -> Option[Any]:
        ensures Option.Nothing => true
"#,
    )])
    .expect("Option.Nothing IR fixture must parse");
    let project =
        cott::hir::lower(Path::new("src"), parsed).expect("Option.Nothing IR fixture must lower");
    let rendered = render(&project).expect("Option.Nothing HIR must render");
    let value = load(&rendered.modules[0].bytes).expect("Option.Nothing IR must load");
    let implementation = value["declarations"]
        .as_array()
        .expect("declarations")
        .iter()
        .find(|declaration| declaration["kind"] == "impl")
        .expect("impl declaration");
    assert!(implementation["init"].is_null());
    assert_eq!(implementation["state"][0]["name"], "value");
    assert_eq!(
        implementation["state"][0]["default"],
        serde_json::json!({"kind": "option", "value": null}),
    );
}

fn remove_old_state_field(value: &mut serde_json::Value) -> bool {
    match value {
        serde_json::Value::Array(values) => values.iter_mut().any(remove_old_state_field),
        serde_json::Value::Object(values) => {
            if values.get("kind").and_then(serde_json::Value::as_str) == Some("old_state_field") {
                values.remove("field");
                true
            } else {
                values.values_mut().any(remove_old_state_field)
            }
        }
        _ => false,
    }
}

fn assert_schema_rejects(value: serde_json::Value, message: &str) {
    let mut bytes = serde_json::to_vec(&value).expect("serialize malformed IR");
    bytes.push(b'\n');
    let error = load(&bytes).expect_err(message);
    assert!(error.contains("schema violation"), "{error}");
}

#[test]
fn schema_rejects_v7_documents() {
    let rendered = render(&advanced_types_project()).expect("advanced fixture must render");
    let mut value: serde_json::Value =
        serde_json::from_slice(&rendered.modules[0].bytes).expect("canonical IR must parse");
    value["schema_version"] = serde_json::json!(7);
    assert_schema_rejects(value, "v7 canonical IR must fail closed");
}

#[test]
fn schema_rejects_malformed_advanced_type_nodes() {
    let rendered = render(&advanced_types_project()).expect("advanced fixture must render");
    let value: serde_json::Value = serde_json::from_slice(&rendered.modules[0].bytes).unwrap();
    let declarations = value["declarations"].as_array().expect("declarations");
    let external_index = declarations
        .iter()
        .position(|declaration| declaration["kind"] == "external_type")
        .expect("external declaration");
    let generator_index = declarations
        .iter()
        .position(|declaration| declaration["target"]["kind"] == "generator")
        .expect("generator declaration");
    let primitive_index = declarations
        .iter()
        .position(|declaration| declaration["target"]["name"] == "any")
        .expect("any declaration");

    let mut stale_external_path = value.clone();
    stale_external_path["declarations"][external_index]["path"] =
        serde_json::Value::String("collections.abc:Iterator".into());
    assert_schema_rejects(stale_external_path, "stale external path must fail");
    let mut stale_external_target = value.clone();
    stale_external_target["declarations"][external_index]["target"] =
        serde_json::Value::String("python".into());
    assert_schema_rejects(stale_external_target, "stale external target must fail");

    let mut malformed_generator = value.clone();
    malformed_generator["declarations"][generator_index]["target"]
        .as_object_mut()
        .expect("generator object")
        .remove("return");
    assert_schema_rejects(
        malformed_generator,
        "generator without return type must fail",
    );

    let mut malformed_iterator = value.clone();
    malformed_iterator["declarations"][generator_index]["target"]["return"]
        .as_object_mut()
        .expect("iterator object")
        .remove("item");
    assert_schema_rejects(malformed_iterator, "iterator without item type must fail");

    let mut malformed_primitive = value;
    malformed_primitive["declarations"][primitive_index]["target"]["name"] =
        serde_json::Value::String("invalid".into());
    assert_schema_rejects(malformed_primitive, "unknown primitive name must fail");
}

#[test]
fn schema_rejects_malformed_factory_type_nodes() {
    let rendered = render(&factory_project()).expect("Factory fixture must render");
    let value: serde_json::Value = serde_json::from_slice(&rendered.modules[0].bytes).unwrap();
    let factory_index = value["declarations"]
        .as_array()
        .expect("declarations")
        .iter()
        .position(|declaration| declaration["return_type"]["kind"] == "factory")
        .expect("Factory-returning declaration");

    let mut missing_instance = value.clone();
    missing_instance["declarations"][factory_index]["return_type"]
        .as_object_mut()
        .expect("Factory type")
        .remove("instance");
    assert_schema_rejects(missing_instance, "Factory without instance must fail");

    let mut primitive_instance = value.clone();
    primitive_instance["declarations"][factory_index]["return_type"]["instance"] =
        serde_json::json!({"kind": "primitive", "name": "i32"});
    assert_schema_rejects(
        primitive_instance,
        "Factory instance must be structurally named",
    );

    let mut stale_arguments = value;
    stale_arguments["declarations"][factory_index]["return_type"]["args"] = serde_json::json!([]);
    assert_schema_rejects(stale_arguments, "Factory must reject stale arguments");
}

#[test]
fn schema_rejects_malformed_impl_nodes() {
    let rendered = render(&impl_project()).expect("impl fixture must render");
    let value: serde_json::Value = serde_json::from_slice(&rendered.modules[0].bytes).unwrap();
    let impl_index = value["declarations"]
        .as_array()
        .expect("declarations")
        .iter()
        .position(|declaration| declaration["kind"] == "impl")
        .expect("impl declaration");

    let mut malformed_impl = value.clone();
    malformed_impl["declarations"][impl_index]
        .as_object_mut()
        .expect("impl object")
        .remove("traits");
    assert_schema_rejects(malformed_impl, "impl without traits must fail");

    let mut malformed_init = value.clone();
    malformed_init["declarations"][impl_index]["init"]
        .as_object_mut()
        .expect("explicit init")
        .remove("contracts");
    assert_schema_rejects(malformed_init, "init without contracts must fail");

    let mut malformed_method = value.clone();
    malformed_method["declarations"][impl_index]["methods"][0]
        .as_object_mut()
        .expect("method object")
        .remove("return_type");
    assert_schema_rejects(malformed_method, "method without return type must fail");

    let mut malformed_modifies = value.clone();
    malformed_modifies["declarations"][impl_index]["methods"][0]["modifies"] =
        serde_json::json!([{"field": "impls.counter.CounterState.count"}]);
    assert_schema_rejects(malformed_modifies, "non-identity modifies entry must fail");

    let mut malformed_old = value;
    assert!(remove_old_state_field(&mut malformed_old));
    assert_schema_rejects(malformed_old, "old state field without identity must fail");
}

#[test]
fn renders_v8_associated_async_and_resource_identity() {
    let parsed = parse_project([source(
        "src/v03.cott",
        r#"module v03

trait Stream:
    type Item
    fn next(self) -> Stream.Item

impl NumberStream for Stream:
    type Item = I32
    fn next(self) -> I32:
        ensures true

resource Door:
    initial Open
    state Open
    state Closed
    terminal Closed
    transition Open -> Closed

async fn fetch() -> I32
"#,
    )])
    .expect("v0.3 fixture must parse");
    let project = cott::hir::lower(Path::new("src"), parsed).expect("v0.3 fixture must lower");
    let rendered = render(&project).expect("v0.3 HIR must render");
    let value = load(&rendered.modules[0].bytes).expect("v0.3 IR must load");
    let declarations = value["declarations"].as_array().expect("declarations");
    assert_eq!(value["schema_version"], 8);
    assert_eq!(
        declarations[0]["associated_types"][0]["name"],
        "v03.Stream.Item"
    );
    assert_eq!(
        declarations[1]["associated_types"][0]["trait"],
        "v03.Stream"
    );
    assert_eq!(
        declarations[3]["callable_kind"],
        serde_json::Value::String("async".into())
    );
    assert_eq!(declarations[0]["methods"][0]["callable_kind"], "sync");
    assert_eq!(declarations[1]["methods"][0]["callable_kind"], "sync");
    assert_eq!(
        declarations[1]["selected_methods"][0]["callable_kind"],
        "sync"
    );
    assert_eq!(declarations[2]["states"][0]["name"], "v03.Door.Open");
    assert_eq!(declarations[2]["edges"][0]["to"], "v03.Door.Closed");
    let mut missing_callable_kind = value.clone();
    missing_callable_kind["declarations"][3]
        .as_object_mut()
        .expect("function object")
        .remove("callable_kind");
    assert_schema_rejects(
        missing_callable_kind,
        "function without callable identity must fail",
    );
    let mut missing_associated_types = value.clone();
    missing_associated_types["declarations"][0]
        .as_object_mut()
        .expect("trait object")
        .remove("associated_types");
    assert_schema_rejects(
        missing_associated_types,
        "trait without associated declarations must fail",
    );
    let mut missing_resource_edges = value;
    missing_resource_edges["declarations"][2]
        .as_object_mut()
        .expect("resource object")
        .remove("edges");
    assert_schema_rejects(
        missing_resource_edges,
        "resource without graph edges must fail",
    );
}

#[test]
fn renders_v8_inheritance_specialization_variance_and_dyn_slots() {
    let parsed = parse_project([source(
        "src/v05_ir.cott",
        r#"module v05_ir

trait Parent:
    fn read(self) -> I32

trait Child for Parent:
    fn write(self) -> I32

fn fallback(receiver: Concrete) -> I32

specialize Concrete for Child:
    read = v05_ir.fallback

impl Concrete for Child:
    fn read(self) -> I32:
        ensures true
    fn write(self) -> I32:
        ensures true

alias Dynamic = Dyn[Child]
"#,
    )])
    .expect("v0.5 fixture must parse");
    let project = cott::hir::lower(Path::new("src"), parsed).expect("v0.5 fixture must lower");
    let rendered = render(&project).expect("v0.5 HIR must render");
    let value = load(&rendered.modules[0].bytes).expect("v0.5 canonical IR must load");
    let declarations = value["declarations"].as_array().expect("declarations");
    let child = declarations
        .iter()
        .find(|declaration| declaration["name"] == "v05_ir.Child")
        .expect("child trait");
    assert_eq!(child["parents"].as_array().expect("parents").len(), 1);
    assert_eq!(child["closure"].as_array().expect("closure").len(), 1);
    let specialization = declarations
        .iter()
        .find(|declaration| declaration["kind"] == "specialization")
        .expect("specialization");
    assert_eq!(
        specialization["methods"][0]["trait_method"],
        "v05_ir.Parent.read"
    );
    assert_eq!(specialization["public"], false);
    let implementation = declarations
        .iter()
        .find(|declaration| declaration["kind"] == "impl")
        .expect("implementation");
    assert_eq!(
        implementation["selected_methods"][0]["selected"]["origin"],
        "explicit"
    );
    assert!(
        implementation["selected_methods"][0]
            .get("parameters")
            .is_some()
    );
    let dynamic = declarations
        .iter()
        .find(|declaration| declaration["name"] == "v05_ir.Dynamic")
        .expect("dynamic alias");
    assert_eq!(dynamic["target"]["kind"], "dyn");
}

#[test]
fn renders_resource_initial_state_defaults_as_enum_values() {
    let parsed = parse_project([source(
        "src/lifecycle.cott",
        r#"module lifecycle

trait Controller:
    fn close(self) -> Unit

resource Door:
    initial Open
    state Open
    state Closed
    terminal Closed
    transition Open -> Closed

impl DoorController for Controller:
    state:
        door: Door
    init(door: Door):
        requires true
    fn close(self) -> Unit:
        requires true
        transitions self.door: Door.Open -> Door.Closed
        ensures true
"#,
    )])
    .expect("resource default fixture must parse");
    let project = cott::hir::lower(Path::new("src"), parsed).expect("fixture must lower");
    let rendered = render(&project).expect("fixture must render");
    let value = load(&rendered.modules[0].bytes).expect("fixture must load");
    let implementation = value["declarations"]
        .as_array()
        .expect("declarations")
        .iter()
        .find(|declaration| declaration["kind"] == "impl")
        .expect("impl declaration");
    assert_eq!(
        implementation["state"][0]["default"],
        serde_json::json!({"kind":"enum","fields":[],"variant":"lifecycle.Door.Open"})
    );
}

#[test]
fn renders_resource_terminals_in_declaration_order_with_source_spans() {
    let text = r#"module lifecycle

resource Job:
    initial new
    state new
    state done
    state failed
    terminal failed
    terminal done
    transition new -> done
    transition new -> failed
"#;
    let parsed = parse_project([source("src/lifecycle.cott", text)])
        .expect("resource terminal fixture must parse");
    let project = cott::hir::lower(Path::new("src"), parsed).expect("fixture must lower");
    let rendered = render(&project).expect("fixture must render");
    let value = load(&rendered.modules[0].bytes).expect("fixture must load");
    let resource = value["declarations"]
        .as_array()
        .expect("declarations")
        .iter()
        .find(|declaration| declaration["kind"] == "resource")
        .expect("resource declaration");
    let terminals = resource["terminals"]
        .as_array()
        .expect("resource terminals");
    assert_eq!(
        terminals
            .iter()
            .map(|terminal| terminal["state"].as_str().expect("terminal state"))
            .collect::<Vec<_>>(),
        ["lifecycle.Job.failed", "lifecycle.Job.done"]
    );
    assert_eq!(
        terminals
            .iter()
            .map(|terminal| terminal["source_order"].as_u64().expect("terminal order"))
            .collect::<Vec<_>>(),
        [0, 1]
    );
    for (terminal, state) in terminals.iter().zip(["failed", "done"]) {
        let start = text
            .find(&format!("terminal {state}"))
            .expect("terminal declaration")
            + "terminal ".len();
        assert_eq!(terminal["span"]["start_byte"], start);
        assert_eq!(terminal["span"]["end_byte"], start + state.len());
    }
}

#[test]
fn loads_reference_and_binary_const_generic_arguments() {
    let parsed = parse_project([
        source(
            "src/foo/sizes.cott",
            "module foo.sizes\n\nconst THREE: U32 = 3\n",
        ),
        source(
            "src/foo/consumer.cott",
            r#"module foo.consumer
use foo.sizes.{THREE}

const FOUR: U32 = 4

struct Page[T, const N: U32]:
    items: Array[T, N]

struct Holder:
    named: Page[U8, FOUR]
    qualified: Page[U8, foo.sizes.THREE]
    arithmetic: Page[U8, FOUR + 1]
"#,
        ),
    ])
    .expect("const generic IR fixture must parse");
    let project = cott::hir::lower(Path::new("src"), parsed).expect("fixture must lower");
    let rendered = render(&project).expect("fixture must render");
    let consumer = rendered
        .modules
        .iter()
        .find(|module| module.module.as_string() == "foo.consumer")
        .expect("consumer module");
    let value = load(&consumer.bytes).expect("fixture IR must load");
    let holder = value["declarations"]
        .as_array()
        .expect("declarations")
        .iter()
        .find(|declaration| declaration["name"] == "foo.consumer.Holder")
        .expect("Holder declaration");
    let named = &holder["fields"][0]["type"]["args"][1]["value"];
    assert_eq!(named["kind"], "reference");
    assert_eq!(named["symbol"], "foo.consumer.FOUR");
    let qualified = &holder["fields"][1]["type"]["args"][1]["value"];
    assert_eq!(qualified["kind"], "reference");
    assert_eq!(qualified["symbol"], "foo.sizes.THREE");
    let arithmetic = &holder["fields"][2]["type"]["args"][1]["value"];
    assert_eq!(arithmetic["kind"], "binary");
    assert_eq!(arithmetic["op"], "add");
    assert_eq!(arithmetic["left"]["symbol"], "foo.consumer.FOUR");
    assert_eq!(arithmetic["right"]["value"], 1);
}

#[test]
fn renders_v06_recursive_named_types_deterministically_and_loads_them() {
    let parsed = parse_project([source(
        "src/recursive.cott",
        r#"module recursive

struct Chain[T]:
    value: T
    next: Option[Chain[T]]

enum Tree:
    Empty
    Branch(left: Tree, right: Tree)
"#,
    )])
    .expect("recursive IR fixture must parse");
    let project = cott::hir::lower(Path::new("src"), parsed)
        .expect("guarded recursive IR fixture must lower");

    let first = render(&project).expect("recursive HIR must render");
    let second = render(&project).expect("recursive HIR must render twice");
    assert_eq!(first.modules[0].bytes, second.modules[0].bytes);

    let value = load(&first.modules[0].bytes).expect("recursive canonical IR must load");
    assert_eq!(value["schema_version"], 8);
    let chain = value["declarations"]
        .as_array()
        .expect("declarations")
        .iter()
        .find(|declaration| declaration["name"] == "recursive.Chain")
        .expect("Chain declaration");
    let next = chain["fields"]
        .as_array()
        .expect("Chain fields")
        .iter()
        .find(|field| field["name"] == "next")
        .expect("next field");
    assert_eq!(next["type"]["kind"], "option");
    assert_eq!(next["type"]["item"]["kind"], "named");
    assert_eq!(next["type"]["item"]["name"], "recursive.Chain");
    assert_eq!(next["type"]["item"]["args"][0]["kind"], "type");
    assert_eq!(
        next["type"]["item"]["args"][0]["type"]["kind"],
        "type_parameter"
    );
    assert_eq!(next["type"]["item"]["args"][0]["type"]["name"], "T");
}

#[test]
fn canonical_ir_includes_struct_invariants_deterministically() {
    let parsed = parse_project([SourceFile::new(
        "src/location.cott",
        r#"module location

struct Location:
    target: Str

    invariant starts_with(self.target, "https://")
"#,
    )])
    .expect("fixture should parse");
    let project = cott::hir::lower(Path::new("src"), parsed).expect("fixture should lower");
    let first = render(&project).expect("fixture should render");
    let second = render(&project).expect("fixture should render deterministically");
    assert_eq!(first.modules[0].bytes, second.modules[0].bytes);
    let value = load(&first.modules[0].bytes).expect("invariant IR should validate");
    let location = value["declarations"][0]
        .as_object()
        .expect("struct declaration");
    assert_eq!(location["invariants"][0]["clause_id"], 0);
    assert_eq!(location["invariants"][0]["expression"]["kind"], "intrinsic");
}
