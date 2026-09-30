use std::collections::BTreeMap;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::sync::atomic::{AtomicU64, Ordering};

use cott::hash::sha256_hex;
use cott::rust::RustOwner;
use cott::rust::provenance::RustGenerationRecord;

static NEXT_TEMP: AtomicU64 = AtomicU64::new(0);

struct TempDir {
    path: PathBuf,
}

impl TempDir {
    fn new() -> Self {
        let mut id = NEXT_TEMP.fetch_add(1, Ordering::Relaxed);
        loop {
            let path = std::env::temp_dir()
                .join(format!("cott-rust-generation-{}-{id}", std::process::id()));
            match fs::create_dir(&path) {
                Ok(()) => return Self { path },
                Err(error) if error.kind() == io::ErrorKind::AlreadyExists => id += 1,
                Err(error) => panic!("create Rust generation fixture: {error}"),
            }
        }
    }
}

impl Drop for TempDir {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.path);
    }
}

fn project(source: &str, rules: Option<&str>) -> TempDir {
    let temp = TempDir::new();
    fs::create_dir_all(temp.path.join("src")).expect("Cott source directory");
    fs::create_dir_all(temp.path.join("rust")).expect("Rust source directory");
    let generator = if rules.is_some() {
        "\n[generator]\nrules = \"generator.rules\"\n"
    } else {
        ""
    };
    fs::write(
        temp.path.join("cott.toml"),
        format!(
            r#"[project]
name = "generation_fixture"
version = "0.1.0"
source = "src"
{generator}
[target.rust]
source = "rust"
generated = "generated/rust"
cargo = "cargo-never-run"
rustc = "rustc-never-run"
runtime_validation = "boundary"
"#
        ),
    )
    .expect("Rust manifest");
    fs::write(temp.path.join("src/sample.cott"), source).expect("Cott source");
    if let Some(rules) = rules {
        fs::write(temp.path.join("generator.rules"), rules).expect("generator rules");
    }
    temp
}

fn write_exec(path: &Path, body: &str) {
    fs::write(path, body).expect("write fixture executable");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(path, fs::Permissions::from_mode(0o755))
            .expect("make fixture executable");
    }
}

fn tool_path(root: &Path) -> PathBuf {
    let tools = root.join("tools");
    fs::create_dir(&tools).expect("tool directory");
    tools
}

fn command(root: &Path, tools: &Path, arguments: &[&str]) -> Output {
    let path = std::env::join_paths([tools, Path::new("/usr/bin"), Path::new("/bin")])
        .expect("fixture PATH");
    Command::new(env!("CARGO_BIN_EXE_cott"))
        .args(arguments)
        .args(["--project"])
        .arg(root)
        .env("PATH", path)
        .output()
        .expect("run cott command")
}

fn prompt(root: &Path, tools: &Path, symbol: &str) -> serde_json::Value {
    let output = command(root, tools, &["prompt", symbol, "--format", "json"]);
    assert!(
        output.status.success(),
        "stdout: {}\nstderr: {}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(output.stderr.is_empty(), "prompt wrote stderr");
    serde_json::from_slice(&output.stdout).expect("Rust prompt JSON")
}

fn generation_record(root: &Path) -> RustGenerationRecord {
    RustGenerationRecord::parse(
        &fs::read(root.join("generated/generation.json")).expect("Rust generation record"),
    )
    .expect("valid Rust generation record")
}

fn fenced_prompt_section<'a>(prompt: &'a str, heading: &str, language: &str) -> &'a str {
    let opening = format!("{heading}\n```{language}\n");
    prompt
        .split_once(&opening)
        .unwrap_or_else(|| panic!("missing prompt section {heading}"))
        .1
        .split_once("\n```\n")
        .unwrap_or_else(|| panic!("unterminated prompt section {heading}"))
        .0
}

const CAPTURED_PROMPT_PREFIX: &str = "// cott-test-prompt-json: ";

fn captured_prompt(source: &str) -> String {
    let mut captures = source
        .lines()
        .filter_map(|line| line.strip_prefix(CAPTURED_PROMPT_PREFIX));
    let encoded = captures.next().expect("candidate prompt capture comment");
    assert!(
        captures.next().is_none(),
        "candidate contained multiple prompt capture comments"
    );
    serde_json::from_str(encoded).expect("JSON-encoded candidate prompt")
}

const SOURCE: &str = "module sample\n\nfn alpha(value: I32) -> I32\n\nfn beta(value: I32) -> I32\n";
fn fake_omp(tools: &Path, retry: bool) {
    let script = r#"#!/usr/bin/python3
import json, pathlib, sys
if sys.argv[1:] == ['--version']:
    print('omp/17.2.12')
    raise SystemExit(0)
prompt = pathlib.Path(sys.argv[-1][1:]).read_text()
signature = prompt.split('```rust\n',1)[1].split('\n```',1)[0]
existing = prompt.split('# Existing candidate\n```rust\n',1)[1].split('\n```\n',1)[0]
feedback = prompt.split('# Actual validation feedback\n```text\n',1)[1].split('\n```\n',1)[0]
if RETRY and existing.strip() == '(none)':
    signature = signature.replace('pub(crate)', 'pub')
elif RETRY and 'Rust source audit failed' not in feedback:
    raise SystemExit(64)
source = signature + ' { value }\n// cott-test-prompt-json: ' + json.dumps(prompt,separators=(',',':')) + '\n'
pathlib.Path('implementation.rs').write_text(source)
"#;
    write_exec(
        &tools.join("omp"),
        &script.replace("RETRY", if retry { "True" } else { "False" }),
    );
}
#[test]
fn source_audit_retry_preserves_frozen_prompt_and_authored_identity() {
    let p = project(SOURCE, None);
    let tools = tool_path(&p.path);
    fake_omp(&tools, true);
    let initial = prompt(&p.path, &tools, "sample.alpha");
    let result = command(
        &p.path,
        &tools,
        &[
            "generate",
            "sample.alpha",
            "--agent",
            "omp",
            "--target",
            "rust",
        ],
    );
    assert!(
        result.status.success(),
        "{}",
        String::from_utf8_lossy(&result.stderr)
    );
    let source = fs::read_to_string(p.path.join("rust/cott_impl/sample/alpha.rs")).unwrap();
    let retry = captured_prompt(&source);
    let rejected = fenced_prompt_section(&retry, "# Existing candidate", "rust");
    assert_eq!(captured_prompt(rejected), initial["prompt"]);
    let record = generation_record(&p.path);
    assert_eq!(record.current.unresolved, ["sample.beta"]);
    assert_eq!(record.current.implementations[0].owner, RustOwner::Agent);
    assert_eq!(
        record.current.agent_runs[0].prompt_hash,
        initial["prompt_hash"]
    );
    assert_eq!(
        record.current.agent_runs[0].implementation_hash,
        format!("sha256:{}", sha256_hex(source.as_bytes()))
    );
    let managed = fs::read(p.path.join("generated/rust/src/cott_impl/sample/alpha.rs")).unwrap();
    assert_ne!(sha256_hex(&managed), sha256_hex(source.as_bytes()));
}
#[test]
fn stale_rules_preserve_authenticated_pending_sources_across_failed_generation() {
    let p = project(SOURCE, Some("Keep the value unchanged.\n"));
    let tools = tool_path(&p.path);
    fake_omp(&tools, false);
    let args = [
        "generate",
        "sample.alpha",
        "--agent",
        "omp",
        "--target",
        "rust",
    ];
    let result = command(&p.path, &tools, &args);
    assert!(
        result.status.success(),
        "{}",
        String::from_utf8_lossy(&result.stderr)
    );
    let old = fs::read(p.path.join("rust/cott_impl/sample/alpha.rs")).unwrap();
    fs::write(p.path.join("generator.rules"), "Use a neutral addition.\n").unwrap();
    let changed = prompt(&p.path, &tools, "sample.alpha");
    assert_eq!(changed["generation_required"], true);
    write_exec(
        &tools.join("omp"),
        "#!/bin/sh\nif [ \"$1\" = --version ]; then echo omp/17.2.12; exit 0; fi\nexit 17\n",
    );
    assert_eq!(command(&p.path, &tools, &args).status.code(), Some(5));
    assert_eq!(
        fs::read(p.path.join("rust/cott_impl/sample/alpha.rs")).unwrap(),
        old
    );
    assert!(
        generation_record(&p.path)
            .current
            .unresolved
            .contains(&"sample.alpha".into())
    );
    let emitted = command(&p.path, &tools, &["emit", "rust"]);
    assert!(
        emitted.status.success(),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    assert_eq!(
        fs::read(p.path.join("rust/cott_impl/sample/alpha.rs")).unwrap(),
        old
    );
}
#[test]
#[ignore = "requires COTT_CARGO native sandbox toolchain"]
fn native_fake_agent_generate_and_emit_compiles() {
    let Some(cargo) = std::env::var_os("COTT_CARGO") else {
        return;
    };
    let cargo = PathBuf::from(cargo);
    let rustc = std::env::var_os("COTT_RUSTC")
        .map(PathBuf::from)
        .unwrap_or_else(|| cargo.with_file_name("rustc"));
    let p = project("module sample\n\nfn alpha(value: I32) -> I32\n", None);
    let manifest = fs::read_to_string(p.path.join("cott.toml"))
        .unwrap()
        .replace("cargo-never-run", &cargo.to_string_lossy())
        .replace("rustc-never-run", &rustc.to_string_lossy());
    fs::write(p.path.join("cott.toml"), manifest).unwrap();
    let tools = tool_path(&p.path);
    fake_omp(&tools, false);
    let output = command(
        &p.path,
        &tools,
        &["generate", "--agent", "omp", "--target", "rust"],
    );
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(command(&p.path, &tools, &["emit", "rust"]).status.success());
    let build = Command::new(cargo)
        .args(["check", "--offline", "--locked", "--manifest-path"])
        .arg(p.path.join("generated/rust/Cargo.toml"))
        .env("RUSTC", rustc)
        .env("RUSTFLAGS", "-D warnings")
        .env("CARGO_PROFILE_DEV_DEBUG", "0")
        .env("CARGO_INCREMENTAL", "0")
        .output()
        .unwrap();
    assert!(
        build.status.success(),
        "{}",
        String::from_utf8_lossy(&build.stderr)
    );
}

#[test]
fn parallel_waves_finish_failed_wave_and_stop_later_source_order_work() {
    let p = project(
        "module sample\n\nfn zeta(value: I32) -> I32\n\nfn alpha(value: I32) -> I32\n\nfn gamma(value: I32) -> I32\n\nfn delta(value: I32) -> I32\n\nfn epsilon(value: I32) -> I32\n",
        None,
    );
    let tools = tool_path(&p.path);
    write_exec(
        &tools.join("omp"),
        r#"#!/usr/bin/python3
import pathlib, sys
if sys.argv[1:] == ['--version']:
    print('omp/17.2.12')
    raise SystemExit(0)
prompt = pathlib.Path(sys.argv[-1][1:]).read_text()
if 'Selected Cott symbol: sample.gamma\n' in prompt:
    raise SystemExit(17)
signature = prompt.split('```rust\n',1)[1].split('\n```',1)[0]
pathlib.Path('implementation.rs').write_text(signature + ' { value }\n')
"#,
    );
    let frozen: BTreeMap<_, _> = ["zeta", "alpha", "delta"]
        .into_iter()
        .map(|name| {
            (
                name,
                prompt(&p.path, &tools, &format!("sample.{name}"))["prompt_hash"].clone(),
            )
        })
        .collect();
    assert_eq!(
        command(
            &p.path,
            &tools,
            &["generate", "--agent", "omp", "--target", "rust", "-j", "2"]
        )
        .status
        .code(),
        Some(5)
    );
    let record = generation_record(&p.path);
    assert_eq!(
        record.current.unresolved,
        ["sample.epsilon", "sample.gamma"]
    );
    assert_eq!(
        record
            .current
            .implementations
            .iter()
            .map(|b| b.cott_symbol.as_str())
            .collect::<Vec<_>>(),
        ["sample.alpha", "sample.delta", "sample.zeta"]
    );
    for run in &record.current.agent_runs {
        assert_eq!(
            run.prompt_hash,
            frozen[run.symbol.strip_prefix("sample.").unwrap()]
        );
    }
    assert!(!p.path.join("rust/cott_impl/sample/epsilon.rs").exists());
    assert!(!record.current.verified);
}

#[test]
fn direct_codex_and_claude_adapters_accept_audited_rust_candidates() {
    for kind in ["codex", "claude"] {
        let p = project(SOURCE, None);
        let tools = tool_path(&p.path);
        write_exec(
            &tools.join(kind),
            &format!(
                r#"#!/usr/bin/python3
import json, pathlib, sys
kind = {kind:?}
if sys.argv[1:] == ['--version']:
    print('2.1.89' if kind == 'claude' else 'codex-cli 0.147.1')
    raise SystemExit(0)
prompt = sys.stdin.read()
signature = prompt.split('```rust\n',1)[1].split('\n```',1)[0]
pathlib.Path('implementation.rs').write_text(signature + ' {{ value }}\n')
if kind == 'claude':
    print(json.dumps({{'type':'result','subtype':'success','is_error':False,'result':'done'}}))
"#
            ),
        );
        let result = command(
            &p.path,
            &tools,
            &[
                "generate",
                "sample.alpha",
                "--agent",
                kind,
                "--target",
                "rust",
                "--model",
                "fixture-model",
            ],
        );
        assert!(
            result.status.success(),
            "{kind}: {}",
            String::from_utf8_lossy(&result.stderr)
        );
        let record = generation_record(&p.path);
        assert_eq!(
            record.current.implementations[0].cott_symbol,
            "sample.alpha"
        );
        assert_eq!(record.current.unresolved, ["sample.beta"]);
        assert_eq!(record.current.agent_runs[0].adapter, kind);
        let argv = &record.current.agent_runs[0].argv_template;
        assert!(
            argv.windows(2)
                .any(|args| args == ["--model", "fixture-model"])
        );
    }
}

#[test]
fn complete_validation_failure_keeps_authenticated_unverified_pending_checkpoint() {
    let p = project("module sample\n\nfn alpha(value: I32) -> I32\n", None);
    let tools = tool_path(&p.path);
    fake_omp(&tools, false);
    let initial = prompt(&p.path, &tools, "sample.alpha");
    let result = command(
        &p.path,
        &tools,
        &[
            "generate",
            "sample.alpha",
            "--agent",
            "omp",
            "--target",
            "rust",
        ],
    );
    assert_eq!(result.status.code(), Some(5));
    let source = fs::read_to_string(p.path.join("rust/cott_impl/sample/alpha.rs")).unwrap();
    let repair_prompt = captured_prompt(&source);
    assert_ne!(
        fenced_prompt_section(&repair_prompt, "# Actual validation feedback", "text"),
        "(none)"
    );
    let record = generation_record(&p.path);
    assert_eq!(record.current.unresolved, ["sample.alpha"]);
    assert!(!record.current.verified);
    assert!(record.current.verification.is_null());
    assert_eq!(
        record.current.agent_runs[0].prompt_hash,
        initial["prompt_hash"]
    );
    assert_eq!(
        record.current.agent_runs[0].implementation_hash,
        format!("sha256:{}", sha256_hex(source.as_bytes()))
    );
    assert!(
        !p.path
            .join("generated/rust/src/cott_impl/sample/alpha.rs")
            .exists()
    );
}
