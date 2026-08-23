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
        Some("https://cott.dev/schema/canonical-ir/v2")
    );
    assert_eq!(
        object
            .get("properties")
            .and_then(serde_json::Value::as_object)
            .and_then(|properties| properties.get("schema_version"))
            .and_then(serde_json::Value::as_object)
            .and_then(|version| version.get("const"))
            .and_then(serde_json::Value::as_u64),
        Some(2)
    );

    let definitions = object
        .get("$defs")
        .and_then(serde_json::Value::as_object)
        .expect("canonical IR schema must define $defs");
    for definition in ["pattern", "contract", "effect"] {
        assert!(
            definitions.contains_key(definition),
            "canonical IR schema must define $defs.{definition}"
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

fn consume(items: Iterator[Opaque["handle"]]) -> Stream
"#,
    )])
    .expect("advanced type fixture must parse");

    cott::hir::lower(Path::new("src"), parsed).expect("advanced type fixture must lower")
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
    assert!(text.contains(r#""schema_version":2"#));
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

    let value = load(&first.modules[0].bytes).expect("advanced canonical IR must load");
    assert_eq!(value["schema_version"], 2);
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
