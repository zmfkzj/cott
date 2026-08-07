use std::path::{Path, PathBuf};

use cott::compiler::{SourceFile, parse_project};
use cott::ir::render;
use cott::semantic::analyze_project;

fn source(path: &str, text: &str) -> SourceFile {
    SourceFile::new(PathBuf::from(path), text)
}

fn project() -> cott::semantic::SemanticProject {
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

    analyze_project(Path::new("src"), parsed).expect("IR fixture must validate")
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
fn renders_deterministic_canonical_modules() {
    let project = project();
    let first = render(&project);
    let second = render(&project);

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
    assert_eq!(
        first
            .modules
            .iter()
            .map(|module| module.source.as_path())
            .collect::<Vec<_>>(),
        [
            Path::new("src/types/core.cott"),
            Path::new("src/api/service.cott")
        ]
    );
    for (left, right) in first.modules.iter().zip(&second.modules) {
        assert_eq!(left.bytes, right.bytes);

        let text = json(left);
        assert!(text.ends_with('\n'));
        assert!(!text[..text.len() - 1].chars().any(char::is_whitespace));
        assert!(!text[..text.len() - 1].ends_with('\n'));
    }

    let types = json(&first.modules[0]);
    assert!(types.contains(r#""module":"types.core""#));
    assert!(types.contains(r#""source":"src/types/core.cott""#));

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
    assert!(api.contains(r#""source":"src/api/service.cott""#));

    let imports_start = api.find(r#""imports":["#).expect("imports array");
    let imports = &api[imports_start..api[imports_start..].find(']').unwrap() + imports_start];
    assert_in_order(
        imports,
        &[
            r#""types.core.Status""#,
            r#""types.core.User""#,
            r#""types.core.UserId""#,
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

    assert!(api.contains(
        r#""target":{"item":{"kind":"named","name":"types.core.User"},"kind":"option"}"#
    ));
    assert!(api.contains(
        r#""target":{"error":{"kind":"named","name":"types.core.Status"},"kind":"result","ok":{"kind":"named","name":"types.core.User"}}"#
    ));
    assert!(api.contains(r#""text":"alias-doc""#));
    assert!(api.contains(r#""type":{"kind":"primitive","name":"i32"}"#));
    assert!(api.contains(r#""type":{"kind":"primitive","name":"str"}"#));
    assert!(api.contains(r#""kind":"alias","name":"api.service.MaybeUser""#));
    assert!(api.contains(r#""doc":{"span":{"end":"#));

    assert_in_order(
        api,
        &[
            r#""name":"api.service.Decision.Open""#,
            r#""name":"api.service.Decision.Closed""#,
        ],
    );
    assert_in_order(api, &[r#""name":"reason""#, r#""name":"code""#]);
}
