use std::ffi::OsString;
use std::fs;
use std::path::PathBuf;
use std::process::Command as ProcessCommand;
use std::time::{SystemTime, UNIX_EPOCH};

use cott::cli::{AgentKind, Command, EmitTarget, OutputFormat, TargetLanguage, parse_command};

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
            target: TargetLanguage::Python,
            agent: Some(AgentKind::Omp),
            model: None,
            jobs: 1,
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
            target: TargetLanguage::Python,
            agent: Some(AgentKind::Codex),
            model: None,
            jobs: 1,
            project: None,
            format: OutputFormat::Human
        },
    );
    assert_eq!(
        parse(&[
            "generate",
            "--target",
            "python",
            "foo.bar.Writer.write",
            "--agent",
            "claude"
        ]),
        Command::Generate {
            symbol: Some("foo.bar.Writer.write".to_owned()),
            target: TargetLanguage::Python,
            agent: Some(AgentKind::Claude),
            model: None,
            jobs: 1,
            project: None,
            format: OutputFormat::Human
        },
    );
}

#[test]
fn parses_generate_jobs() {
    for option in ["-j", "--jobs"] {
        assert_eq!(
            parse(&[
                "generate", "--target", "python", "--agent", "omp", option, "5",
            ]),
            Command::Generate {
                symbol: None,
                target: TargetLanguage::Python,
                agent: Some(AgentKind::Omp),
                model: None,
                jobs: 5,
                project: None,
                format: OutputFormat::Human,
            },
        );
    }
}

#[test]
fn parses_closed_backend_targets() {
    assert_eq!(
        parse(&["init", "demo"]),
        Command::Init {
            path: PathBuf::from("demo"),
            target: TargetLanguage::Python,
            name: None,
            no_sync: false,
            format: OutputFormat::Human,
        }
    );
    assert_eq!(
        parse(&[
            "init",
            "--target",
            "kotlin",
            "--format",
            "json",
            "demo",
            "--no-sync",
        ]),
        Command::Init {
            path: PathBuf::from("demo"),
            target: TargetLanguage::Kotlin,
            name: None,
            no_sync: true,
            format: OutputFormat::Json,
        }
    );
    assert_eq!(
        parse(&["emit", "kotlin", "--project", "demo"]),
        Command::Emit {
            target: EmitTarget::Kotlin,
            project: Some(PathBuf::from("demo")),
            format: OutputFormat::Human,
        }
    );
    assert_eq!(
        parse(&[
            "generate",
            "foo.bar.run",
            "--target",
            "kotlin",
            "--agent",
            "omp"
        ]),
        Command::Generate {
            symbol: Some("foo.bar.run".to_owned()),
            target: TargetLanguage::Kotlin,
            agent: Some(AgentKind::Omp),
            model: None,
            jobs: 1,
            project: None,
            format: OutputFormat::Human,
        }
    );
    assert_eq!(
        parse(&[
            "init",
            "--target",
            "dart",
            "--format",
            "json",
            "dart_demo",
            "--no-sync",
        ]),
        Command::Init {
            path: PathBuf::from("dart_demo"),
            target: TargetLanguage::Dart,
            name: None,
            no_sync: true,
            format: OutputFormat::Json,
        }
    );
    assert_eq!(
        parse(&["emit", "dart", "--project", "dart_demo"]),
        Command::Emit {
            target: EmitTarget::Dart,
            project: Some(PathBuf::from("dart_demo")),
            format: OutputFormat::Human,
        }
    );
    assert_eq!(
        parse(&[
            "generate",
            "foo.bar.run",
            "--target",
            "dart",
            "--agent",
            "omp"
        ]),
        Command::Generate {
            symbol: Some("foo.bar.run".to_owned()),
            target: TargetLanguage::Dart,
            agent: Some(AgentKind::Omp),
            model: None,
            jobs: 1,
            project: None,
            format: OutputFormat::Human,
        }
    );
}

#[test]
fn help_advertises_the_complete_closed_target_grammar() {
    let output = ProcessCommand::new(env!("CARGO_BIN_EXE_cott"))
        .arg("--help")
        .output()
        .expect("cott should print help");
    assert!(output.status.success());
    assert!(output.stderr.is_empty());
    let help = String::from_utf8_lossy(&output.stdout);
    assert!(help.contains("--target python|kotlin|dart"));
    assert!(help.contains("emit ir|python|kotlin|dart"));
    assert!(help.contains("--model <model>"));
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
fn prompt_and_diff_target_selection_errors_remain_json() {
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let root = std::env::temp_dir().join(format!(
        "cott-command-special-json-{}-{nonce}",
        std::process::id()
    ));
    let malformed = root.join("malformed");
    fs::create_dir_all(&malformed).unwrap();
    fs::write(malformed.join("cott.toml"), "not valid toml = [").unwrap();

    let prompt = ProcessCommand::new(env!("CARGO_BIN_EXE_cott"))
        .args(["prompt", "demo.run", "--project"])
        .arg(root.join("missing"))
        .args(["--format", "json"])
        .output()
        .expect("cott should report a missing prompt project");
    let diff = ProcessCommand::new(env!("CARGO_BIN_EXE_cott"))
        .args(["diff", "--project"])
        .arg(&malformed)
        .args(["--format", "json"])
        .output()
        .expect("cott should report a malformed diff manifest");

    for output in [prompt, diff] {
        assert_eq!(output.status.code(), Some(2));
        assert!(output.stderr.is_empty());
        let report: serde_json::Value =
            serde_json::from_slice(&output.stdout).expect("selection failure should report JSON");
        assert_eq!(report["schema_version"], 1);
        assert_eq!(report["diagnostics"][0]["code"], "COTT-C001");
        assert_eq!(report["diagnostics"][0]["severity"], "error");
    }
    fs::remove_dir_all(root).unwrap();
}

#[test]
fn dart_prompt_and_diff_failures_remain_json() {
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let root = std::env::temp_dir().join(format!(
        "cott-command-dart-special-json-{}-{nonce}",
        std::process::id()
    ));
    fs::create_dir_all(root.join("src")).unwrap();
    fs::create_dir_all(root.join("dart")).unwrap();
    fs::write(
        root.join("cott.toml"),
        "[project]\nname = \"demo\"\nversion = \"0.1.0\"\nsource = \"src\"\n\n[target.dart]\nsource = \"dart\"\ngenerated = \"generated/dart\"\nsdk = \"definitely-missing-dart-sdk\"\nruntime_validation = \"boundary\"\n",
    )
    .unwrap();
    fs::write(
        root.join("src/demo.cott"),
        "module demo\n\nfn pending() -> Unit\n",
    )
    .unwrap();

    let prompt = ProcessCommand::new(env!("CARGO_BIN_EXE_cott"))
        .args(["prompt", "demo.missing", "--project"])
        .arg(&root)
        .args(["--format", "json"])
        .output()
        .expect("cott should report an unknown Dart prompt symbol");
    let diff = ProcessCommand::new(env!("CARGO_BIN_EXE_cott"))
        .args(["diff", "--project"])
        .arg(&root)
        .args(["--format", "json"])
        .output()
        .expect("cott should report a missing Dart diff snapshot");

    for output in [prompt, diff] {
        assert!(!output.status.success());
        assert!(output.stderr.is_empty());
        let report: serde_json::Value =
            serde_json::from_slice(&output.stdout).expect("Dart failure should report JSON");
        assert_eq!(report["schema_version"], 1);
        assert_eq!(report["diagnostics"][0]["severity"], "error");
    }
    fs::remove_dir_all(root).unwrap();
}

#[test]
fn rejects_duplicate_or_invalid_options() {
    assert!(
        parse_command(&["verify", "--project", "a", "--project", "b"].map(OsString::from)).is_err()
    );
    assert!(parse_command(&["init", "demo", "--project", "demo"].map(OsString::from)).is_err());
    assert!(parse_command(&["generate", "--target", "rust"].map(OsString::from)).is_err());
    assert_eq!(
        parse_command(&["generate", "--agent", "omp"].map(OsString::from)),
        Err("`generate` requires `--target python|kotlin|dart`")
    );
    for arguments in [
        &["init", "demo", "--target", "python", "--target", "kotlin"][..],
        &["generate", "--target", "python", "--target", "kotlin"][..],
        &["check", "--target", "kotlin"][..],
        &["fmt", "--target", "kotlin"][..],
        &["verify", "--target", "kotlin"][..],
        &["deploy", "--target", "kotlin"][..],
        &["diff", "--target", "kotlin"][..],
        &["emit", "java"][..],
    ] {
        assert!(
            parse_command(&arguments.iter().map(OsString::from).collect::<Vec<_>>()).is_err(),
            "{arguments:?}"
        );
    }
    assert_eq!(
        parse_command(&["generate", "--agent", "unknown"].map(OsString::from)),
        Err("`--agent` requires `codex`, `claude`, or `omp`")
    );
}

#[test]
fn parses_generate_model_alongside_agent() {
    assert_eq!(
        parse(&[
            "generate",
            "--target",
            "python",
            "--agent",
            "omp",
            "--model",
            "anthropic/claude-opus-5-5",
        ]),
        Command::Generate {
            symbol: None,
            target: TargetLanguage::Python,
            agent: Some(AgentKind::Omp),
            model: Some("anthropic/claude-opus-5-5".to_owned()),
            jobs: 1,
            project: None,
            format: OutputFormat::Human,
        },
    );
}

#[test]
fn rejects_invalid_or_misplaced_generate_model() {
    for arguments in [
        &[
            "generate", "--target", "python", "--agent", "omp", "--model",
        ][..],
        &[
            "generate", "--target", "python", "--agent", "omp", "--model", "",
        ][..],
        &[
            "generate", "--target", "python", "--agent", "omp", "--model", "-flag",
        ][..],
        &[
            "generate",
            "--target",
            "python",
            "--agent",
            "omp",
            "--model",
            "trailing ",
        ][..],
        &[
            "generate", "--target", "python", "--agent", "omp", "--model", "a", "--model", "b",
        ][..],
        &[
            "generate",
            "--target",
            "python",
            "--model",
            "anthropic/claude-opus-5-5",
        ][..],
        &["verify", "--model", "anthropic/claude-opus-5-5"][..],
        &["check", "--model", "anthropic/claude-opus-5-5"][..],
    ] {
        assert!(
            parse_command(&arguments.iter().map(OsString::from).collect::<Vec<_>>()).is_err(),
            "{arguments:?}"
        );
    }
    assert_eq!(
        parse_command(
            &[
                "generate",
                "--target",
                "python",
                "--model",
                "anthropic/claude-opus-5-5"
            ]
            .map(OsString::from)
        ),
        Err("`--model` requires `--agent`")
    );
}

#[test]
fn rejects_explicit_target_mismatch_before_backend_dispatch() {
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let root = std::env::temp_dir().join(format!(
        "cott-command-target-{}-{nonce}",
        std::process::id()
    ));
    let kotlin = root.join("kotlin");
    let python = root.join("python");
    let dart = root.join("dart");
    fs::create_dir_all(&kotlin).unwrap();
    fs::create_dir_all(&python).unwrap();
    fs::create_dir_all(&dart).unwrap();
    fs::write(
        kotlin.join("cott.toml"),
        "[project]\nname = \"demo\"\nversion = \"0.1.0\"\nsource = \"src\"\n\n[target.kotlin]\nsource = \"kotlin\"\ngenerated = \"generated/kotlin\"\nruntime_validation = \"boundary\"\n",
    )
    .unwrap();
    fs::write(
        python.join("cott.toml"),
        "[project]\nname = \"demo\"\nversion = \"0.1.0\"\nsource = \"src\"\n\n[target.python]\nsource = \"python\"\ngenerated = \"generated/python\"\nstubs = \"generated/stubs\"\ninterpreter = \".venv/bin/python\"\ntype_checker = \".venv/bin/basedpyright\"\nruntime_validation = \"boundary\"\n",
    )
    .unwrap();
    fs::write(
        dart.join("cott.toml"),
        "[project]\nname = \"demo\"\nversion = \"0.1.0\"\nsource = \"src\"\n\n[target.dart]\nsource = \"dart\"\ngenerated = \"generated/dart\"\nruntime_validation = \"boundary\"\n",
    )
    .unwrap();

    let generate = ProcessCommand::new(env!("CARGO_BIN_EXE_cott"))
        .args([
            "generate",
            "--target",
            "python",
            "--agent",
            "omp",
            "--project",
        ])
        .arg(&kotlin)
        .output()
        .expect("cott should reject the target mismatch");
    assert_eq!(generate.status.code(), Some(2));
    assert!(
        String::from_utf8_lossy(&generate.stderr)
            .contains("requested target `python` does not match project target `kotlin`")
    );

    let dart_generate = ProcessCommand::new(env!("CARGO_BIN_EXE_cott"))
        .args([
            "generate",
            "--target",
            "python",
            "--agent",
            "omp",
            "--project",
        ])
        .arg(&dart)
        .output()
        .expect("cott should reject the Dart target mismatch");
    assert_eq!(dart_generate.status.code(), Some(2));
    assert!(
        String::from_utf8_lossy(&dart_generate.stderr)
            .contains("requested target `python` does not match project target `dart`")
    );

    let emit = ProcessCommand::new(env!("CARGO_BIN_EXE_cott"))
        .args(["emit", "kotlin", "--project"])
        .arg(&python)
        .output()
        .expect("cott should reject the target mismatch");
    assert_eq!(emit.status.code(), Some(2));
    assert!(
        String::from_utf8_lossy(&emit.stderr)
            .contains("requested target `kotlin` does not match project target `python`")
    );
    fs::remove_dir_all(root).unwrap();
}

#[test]
fn reports_kotlin_validation_failures_with_kotlin_diagnostics() {
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let root =
        std::env::temp_dir().join(format!("cott-command-json-{}-{nonce}", std::process::id()));
    fs::create_dir_all(root.join("src")).unwrap();
    fs::create_dir_all(root.join("kotlin")).unwrap();
    fs::write(
        root.join("cott.toml"),
        "[project]\nname = \"demo\"\nversion = \"0.1.0\"\nsource = \"src\"\n\n[target.kotlin]\nsource = \"kotlin\"\ngenerated = \"generated/kotlin\"\nruntime_validation = \"boundary\"\n",
    )
    .unwrap();
    fs::write(
        root.join("src/demo.cott"),
        "module demo\n\nfn unresolved() -> Unit\n",
    )
    .unwrap();

    let output = ProcessCommand::new(env!("CARGO_BIN_EXE_cott"))
        .args(["verify", "--project"])
        .arg(&root)
        .args(["--format", "json"])
        .output()
        .expect("cott should report Kotlin verification failure");
    assert_eq!(output.status.code(), Some(4));
    assert!(output.stderr.is_empty());
    let report: serde_json::Value =
        serde_json::from_slice(&output.stdout).expect("Kotlin diagnostics should be JSON");
    assert_eq!(report["schema_version"], 1);
    assert_eq!(report["diagnostics"][0]["code"], "COTT-T201");
    assert!(
        report["diagnostics"][0]["message"]
            .as_str()
            .is_some_and(|message| message.contains("unresolved Kotlin implementations"))
    );
    fs::remove_dir_all(root).unwrap();
}

#[test]
fn dart_source_only_commands_do_not_require_an_sdk_or_provider() {
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let root = std::env::temp_dir().join(format!(
        "cott-command-dart-source-only-{}-{nonce}",
        std::process::id()
    ));
    fs::create_dir_all(root.join("src")).unwrap();
    fs::create_dir_all(root.join("dart")).unwrap();
    fs::write(
        root.join("cott.toml"),
        "[project]\nname = \"demo\"\nversion = \"0.1.0\"\nsource = \"src\"\n\n[target.dart]\nsource = \"dart\"\ngenerated = \"generated/dart\"\nsdk = \"definitely-missing-dart-sdk\"\nruntime_validation = \"boundary\"\n",
    )
    .unwrap();
    fs::write(
        root.join("src/demo.cott"),
        "module demo\n\nfn unresolved() -> Unit\n",
    )
    .unwrap();

    for arguments in [
        &["check", "--project"][..],
        &["fmt", "--check", "--project"][..],
        &["prompt", "demo.unresolved", "--project"][..],
    ] {
        let output = ProcessCommand::new(env!("CARGO_BIN_EXE_cott"))
            .args(arguments)
            .arg(&root)
            .output()
            .expect("cott should run a Dart source-only command");
        assert_eq!(
            output.status.code(),
            Some(0),
            "{arguments:?}: {}",
            String::from_utf8_lossy(&output.stderr)
        );
    }
    fs::remove_dir_all(root).unwrap();
}

#[test]
fn reports_dart_validation_failures_with_dart_diagnostics() {
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .unwrap()
        .as_nanos();
    let root = std::env::temp_dir().join(format!(
        "cott-command-dart-json-{}-{nonce}",
        std::process::id()
    ));
    fs::create_dir_all(root.join("src")).unwrap();
    fs::create_dir_all(root.join("dart")).unwrap();
    fs::write(
        root.join("cott.toml"),
        "[project]\nname = \"demo\"\nversion = \"0.1.0\"\nsource = \"src\"\n\n[target.dart]\nsource = \"dart\"\ngenerated = \"generated/dart\"\nsdk = \"definitely-missing-dart-sdk\"\nruntime_validation = \"boundary\"\n",
    )
    .unwrap();
    fs::write(
        root.join("src/demo.cott"),
        "module demo\n\nfn unresolved() -> Unit\n",
    )
    .unwrap();

    let output = ProcessCommand::new(env!("CARGO_BIN_EXE_cott"))
        .args(["verify", "--project"])
        .arg(&root)
        .args(["--format", "json"])
        .output()
        .expect("cott should report Dart verification failure");
    assert_eq!(output.status.code(), Some(4));
    assert!(output.stderr.is_empty());
    let report: serde_json::Value =
        serde_json::from_slice(&output.stdout).expect("Dart diagnostics should be JSON");
    assert_eq!(report["schema_version"], 1);
    assert_eq!(report["diagnostics"][0]["code"], "COTT-D201");
    fs::remove_dir_all(root).unwrap();
}

#[test]
fn rejects_invalid_generate_jobs() {
    for arguments in [
        &["generate", "--target", "python", "-j", "0"][..],
        &["generate", "--target", "python", "-j"][..],
        &["generate", "--target", "python", "--jobs", "five"][..],
        &["generate", "--target", "python", "-j", "2", "--jobs", "3"][..],
    ] {
        assert!(parse_command(&arguments.iter().map(OsString::from).collect::<Vec<_>>()).is_err());
    }
}

#[test]
fn parses_prompt_options_surrounding_symbol() {
    assert_eq!(
        parse(&[
            "prompt",
            "--format",
            "json",
            "foo.bar.run",
            "--project",
            "demo"
        ]),
        Command::Prompt {
            symbol: "foo.bar.run".to_owned(),
            project: Some(PathBuf::from("demo")),
            format: OutputFormat::Json
        },
    );
    assert_eq!(
        parse(&["prompt", "foo.bar.Reader.read", "--project", "demo"]),
        Command::Prompt {
            symbol: "foo.bar.Reader.read".to_owned(),
            project: Some(PathBuf::from("demo")),
            format: OutputFormat::Human
        },
    );
}

#[test]
fn rejects_prompt_missing_duplicates_and_generate_flags() {
    assert_eq!(
        parse_command(&["prompt"].map(OsString::from)),
        Err("`prompt` requires a fully qualified callable")
    );
    for arguments in [
        &["prompt", "foo.bar.run", "foo.bar.other"][..],
        &["prompt", "foo.bar.run", "--agent", "omp"][..],
        &["prompt", "foo.bar.run", "--target", "python"][..],
        &["prompt", "foo.bar.run", "-j", "3"][..],
        &["prompt", "--project", "a", "--project", "b", "foo.bar.run"][..],
        &[
            "prompt",
            "--format",
            "json",
            "--format",
            "json",
            "foo.bar.run",
        ][..],
        &["prompt", "foo.bar.run", "--jobs", "2"][..],
    ] {
        assert!(
            parse_command(&arguments.iter().map(OsString::from).collect::<Vec<_>>()).is_err(),
            "{arguments:?}"
        );
    }
}
