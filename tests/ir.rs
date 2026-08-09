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
        object.get("$schema").and_then(serde_json::Value::as_str),
        Some("https://json-schema.org/draft/2020-12/schema")
    );
    assert_eq!(
        object.get("$id").and_then(serde_json::Value::as_str),
        Some("https://cott.dev/schema/canonical-ir/v1")
    );
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
