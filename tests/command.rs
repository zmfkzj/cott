use std::ffi::OsString;
use std::path::PathBuf;

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
fn rejects_duplicate_or_invalid_options() {
    assert!(
        parse_command(&["verify", "--project", "a", "--project", "b"].map(OsString::from)).is_err()
    );
    assert!(parse_command(&["init", "demo", "--project", "demo"].map(OsString::from)).is_err());
    assert!(parse_command(&["generate", "--target", "rust"].map(OsString::from)).is_err());
}
