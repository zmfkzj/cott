use std::collections::BTreeMap;

use std::path::Path;

use cott::hash::sha256_hex;

use cott::agent::{AgentKind, CODEX, OMP, adapter, render_prompt};
use cott::python::artifact_plan::{PythonCallable, PythonCallableKind};

#[test]
fn adapter_contracts_have_minimum_versions_and_exact_argv() {
    assert_eq!(adapter(AgentKind::Codex), &CODEX);
    assert_eq!(adapter(AgentKind::Omp), &OMP);
    assert_eq!(CODEX.executable_name, "codex");
    assert_eq!(CODEX.minimum_version, "0.147.0");
    assert_eq!(CODEX.version_argv, &["--version"]);
    assert_eq!(
        CODEX.argv_template,
        &[
            "exec",
            "--strict-config",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--skip-git-repo-check",
            "--sandbox",
            "workspace-write",
            "--color",
            "never",
            "--cd",
            "<workspace>",
            "-",
        ]
    );
    assert!(CODEX.prompt_on_stdin);
    assert_eq!(OMP.executable_name, "omp");
    assert_eq!(OMP.minimum_version, "17.2.12");
    assert_eq!(OMP.version_argv, &["--version"]);
    assert_eq!(
        OMP.argv_template,
        &[
            "-p",
            "--cwd",
            "<workspace>",
            "--no-session",
            "--no-rules",
            "--no-skills",
            "--no-extensions",
            "--no-lsp",
            "--no-pty",
            "--no-title",
            "--tools",
            "read,grep,glob,edit,write",
            "--approval-mode",
            "yolo",
            "--max-time",
            "<seconds>s",
            "--config",
            "<overlay>",
            "<prompt>",
        ]
    );
    assert!(!OMP.prompt_on_stdin);
}

#[test]
fn prompt_has_fixed_sections_and_final_instruction() {
    let callable = PythonCallable {
        module: "app".to_owned(),
        cott_symbol: "app.run".to_owned(),
        name: "run".to_owned(),
        kind: PythonCallableKind::Function,
        declaration: serde_json::json!({}),
        owner: None,
    };
    let external_types = BTreeMap::from([
        ("app.Widget".to_owned(), "vendor.models:Widget".to_owned()),
        ("app.Alpha".to_owned(), "vendor.models:Alpha".to_owned()),
    ]);
    let generated_type_import_rule = "For other modules import public generated symbols only through `from app import name` and generated value types only through `from app_types import Type`.";
    let prompt = render_prompt(
        &callable,
        br#"{"module":"app"}"#,
        "docs",
        generated_type_import_rule,
        &external_types,
        "bound",
        None,
        None,
        Path::new("python/_cott_impl/app/run.py"),
    )
    .expect("prompt");
    let unmapped = render_prompt(
        &callable,
        br#"{"module":"app"}"#,
        "docs",
        generated_type_import_rule,
        &BTreeMap::new(),
        "bound",
        None,
        None,
        Path::new("python/_cott_impl/app/run.py"),
    )
    .expect("prompt");
    assert_ne!(sha256_hex(&prompt), sha256_hex(&unmapped));
    let text = String::from_utf8(prompt).expect("UTF-8 prompt");
    assert!(text.starts_with("COTT_AGENT_PROMPT_V1\n\nTARGET\n"));
    assert!(text.contains("Symbol: app.run"));
    assert!(text.contains("Define exactly one canonical top-level function `run`."));
    assert!(text.contains(
        "You MAY additionally define private implementation helpers, private immutable constants, and invariant TypeVars. Each helper MUST be an undecorated, synchronous, fully annotated top-level function whose name starts with a single `_` but is neither dunder nor reserved `_cott_`; function names MUST be unique. Each constant MUST have a single-leading-underscore name that is neither dunder nor reserved `_cott_`, and be a literal `Final[bool|int|float|str|bytes]` value. Do not define classes, public helpers, mutable globals, decorators, async functions, variadic parameters, parameter defaults, or other executable top-level assignments."
    ));
    assert!(text.contains("CANONICAL IR\n{\"module\":\"app\"}\n\nDOCS CONTRACTS EFFECTS"));
    assert!(!text.contains("\"external_types\""));
    assert!(text.contains(
        "RELEVANT TYPES\nFor other modules import public generated symbols only through `from app import name` and generated value types only through `from app_types import Type`.\n\nPYTHON EXTERNAL TYPE PROJECTIONS\napp.Alpha = vendor.models:Alpha\napp.Widget = vendor.models:Widget\n\nBOUND SYMBOLS IMPORT RULES"
    ));
    assert!(text.contains(
        "Use external declarations through their exact public generated aliases; their projected public APIs MAY be called when the contract requires it. Do not reconstruct external paths, use dynamic imports or reflection, or inspect and coerce external values merely to validate a contract."
    ));
    assert!(text.contains(
        "FACTORY TYPE MODEL\n`Factory[Concrete]` maps to `type[Concrete]`: it is the exact compiler-generated `Concrete` class object, never an instance, subclass, or arbitrary callable. Constructor calls MUST match `Concrete`'s inferred Cott init signature. Validation MUST NOT construct or invoke a Factory value."
    ));
    assert!(text.contains(
        "EFFECT CALLS\nCall Cott functions only by their exact imported facade name. Do not alias, store, return, pass, rebind, or shadow a Cott callable"
    ));
    assert!(text.contains(
        "Standard ABI aliases, including integer widths, are annotations and MUST NOT be called. Construct result values only with top-level `cott_runtime.Ok(...)`/`cott_runtime.Err(...)`, never `Result.Ok`/`Result.Err`. Generated payload enum aliases have no members; import and construct top-level `<Enum>_<Variant>` classes from the exact generated `*_types` module, never `<Enum>.<Variant>`."
    ));
    assert!(
        text.ends_with(
            "If the contract must change, report that and leave the target unresolved.\n"
        )
    );
}

#[test]
fn async_prompt_requires_the_exact_definition_and_awaits() {
    let prompt = render_prompt(
        &PythonCallable {
            module: "app".to_owned(),
            cott_symbol: "app.fetch".to_owned(),
            name: "fetch".to_owned(),
            kind: PythonCallableKind::AsyncFunction,
            declaration: serde_json::json!({}),
            owner: None,
        },
        br#"{"module":"app"}"#,
        "docs",
        "types",
        &BTreeMap::new(),
        "bound",
        None,
        None,
        Path::new("python/_cott_impl/app/fetch.py"),
    )
    .expect("async prompt");
    let text = String::from_utf8(prompt).expect("UTF-8 prompt");
    assert!(text.contains("canonical undecorated top-level `async def` function `fetch`"));
    assert!(text.contains("Await every call to an async Cott facade"));
    assert!(text.contains("additional async functions"));
}

#[test]
fn method_prompt_allows_private_helpers_and_constants() {
    let prompt = render_prompt(
        &PythonCallable {
            module: "foo.bar".to_owned(),
            cott_symbol: "foo.bar.Reader.read".to_owned(),
            name: "read".to_owned(),
            kind: PythonCallableKind::ImplMethod {
                concrete: "Reader".to_owned(),
            },
            declaration: serde_json::json!({}),
            owner: Some(serde_json::json!({})),
        },
        br#"{"module":"foo.bar"}"#,
        "docs",
        "The compiler-owned concrete facade class `Reader` is absent from `foo.bar_types`; import it exactly as `from foo.bar import Reader` for the `self` annotation. Generated value-type imports remain `from foo.bar_types import Type`.",
        &BTreeMap::new(),
        "bound",
        None,
        None,
        Path::new("python/_cott_impl/foo/bar/Reader/read.py"),
    )
    .expect("prompt");
    let text = String::from_utf8(prompt).expect("UTF-8 prompt");
    assert!(text.contains("Symbol: foo.bar.Reader.read"));
    assert!(
        text.contains("exactly one canonical private top-level function `_cott_impl_Reader_read`")
    );
    assert!(text.contains(
        "You MAY additionally define private implementation helpers, private immutable constants, and invariant TypeVars. Each helper MUST be an undecorated, synchronous, fully annotated top-level function whose name starts with a single `_` but is neither dunder nor reserved `_cott_`; function names MUST be unique. Each constant MUST have a single-leading-underscore name that is neither dunder nor reserved `_cott_`, and be a literal `Final[bool|int|float|str|bytes]` value. Do not define classes, public helpers, mutable globals, decorators, async functions, variadic parameters, parameter defaults, or other executable top-level assignments."
    ));
    assert!(text.contains(
        "The compiler-owned concrete facade class `Reader` is absent from `foo.bar_types`; import it exactly as `from foo.bar import Reader` for the `self` annotation. Generated value-type imports remain `from foo.bar_types import Type`."
    ));
}
