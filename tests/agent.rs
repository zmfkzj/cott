use std::path::Path;

use cott::agent::{AgentKind, CODEX, OMP, adapter, render_prompt};

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
        "foo.bar.run",
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
