use std::path::Path;

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
    let prompt = render_prompt(
        &PythonCallable {
            module: "foo.bar".to_owned(),
            cott_symbol: "foo.bar.run".to_owned(),
            name: "run".to_owned(),
            kind: PythonCallableKind::Function,
            declaration: serde_json::json!({}),
            owner: None,
        },
        br#"{"module":"foo.bar"}"#,
        "docs",
        "types",
        "bound",
        None,
        None,
        Path::new("python/_cott_impl/foo/bar/run.py"),
    )
    .expect("prompt");
    let text = String::from_utf8(prompt).expect("UTF-8 prompt");
    assert!(text.starts_with("COTT_AGENT_PROMPT_V1\n\nTARGET\n"));
    assert!(text.contains("CANONICAL IR\n{\"module\":\"foo.bar\"}"));
    assert!(
        text.ends_with(
            "If the contract must change, report that and leave the target unresolved.\n"
        )
    );
}

#[test]
fn method_prompt_requires_only_the_private_helper() {
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
        "types",
        "bound",
        None,
        None,
        Path::new("python/_cott_impl/foo/bar/Reader/read.py"),
    )
    .expect("prompt");
    let text = String::from_utf8(prompt).expect("UTF-8 prompt");
    assert!(text.contains("Symbol: foo.bar.Reader.read"));
    assert!(text.contains("exactly one private top-level helper `_cott_impl_Reader_read`"));
    assert!(
        text.contains("Do not define a class, facade shell, or any other top-level definition")
    );
    assert!(text.contains(
        "The concrete class `Reader` is absent from `foo.bar_types`; import it exactly as `from foo.bar import Reader`"
    ));
}
