use std::ffi::OsString;
use std::path::PathBuf;
use std::process::Command as ProcessCommand;

use cott::cli::{AgentKind, Command, EmitTarget, OutputFormat, parse_command};

fn parse(values: &[&str]) -> Command {
    parse_command(&values.iter().map(OsString::from).collect::<Vec<_>>())
        .expect("command should parse")
}

#[test]
fn parses_global_options_in_any_position() {
    assert_eq!(
        parse(&["emit", "python", "--format", "json", "--project", "demo"]),
        Command::Emit {
            target: EmitTarget::Python,
            project: Some(PathBuf::from("demo")),
            format: OutputFormat::Json
        },
    );
    assert_eq!(
        parse(&[
            "generate",
            "--target",
            "python",
            "foo.bar.run",
            "--agent",
            "omp"
        ]),
        Command::Generate {
            symbol: Some("foo.bar.run".to_owned()),
            agent: Some(AgentKind::Omp),
            project: None,
            format: OutputFormat::Human
        },
    );
    assert_eq!(
        parse(&[
            "generate",
            "--target",
            "python",
            "foo.bar.Reader.read",
            "--agent",
            "codex"
        ]),
        Command::Generate {
            symbol: Some("foo.bar.Reader.read".to_owned()),
            agent: Some(AgentKind::Codex),
            project: None,
            format: OutputFormat::Human
        },
    );
}

#[test]
fn parses_parameterless_lsp_only() {
    assert_eq!(parse(&["lsp"]), Command::Lsp);
    for arguments in [
        &["lsp", "--format", "json"][..],
        &["lsp", "--project", "demo"][..],
        &["lsp", "--unknown"][..],
        &["lsp", "--help"][..],
        &["lsp", "source.cott"][..],
    ] {
        assert!(
            parse_command(
                &arguments
                    .iter()
                    .map(|value| OsString::from(*value))
                    .collect::<Vec<_>>()
            )
            .is_err()
        );
    }
}

#[test]
fn lsp_options_bypass_json_diagnostic_routing() {
    let output = ProcessCommand::new(env!("CARGO_BIN_EXE_cott"))
        .args(["lsp", "--format", "json", "--format", "json"])
        .output()
        .expect("cott should run");
    assert_eq!(output.status.code(), Some(2));
    assert!(output.stdout.is_empty());
    assert!(
        String::from_utf8_lossy(&output.stderr)
            .contains("`lsp` does not accept options or operands")
    );

    let duplicate = ProcessCommand::new(env!("CARGO_BIN_EXE_cott"))
        .args(["check", "--format", "json", "--format", "json"])
        .output()
        .expect("cott should run");
    assert_eq!(duplicate.status.code(), Some(2));
    let report: serde_json::Value =
        serde_json::from_slice(&duplicate.stdout).expect("duplicate format reports JSON");
    assert_eq!(report["diagnostics"][0]["message"], "duplicate option");
}

#[test]
fn rejects_duplicate_or_invalid_options() {
    assert!(
        parse_command(&["verify", "--project", "a", "--project", "b"].map(OsString::from)).is_err()
    );
    assert!(parse_command(&["init", "demo", "--project", "demo"].map(OsString::from)).is_err());
    assert!(parse_command(&["generate", "--target", "rust"].map(OsString::from)).is_err());
}
