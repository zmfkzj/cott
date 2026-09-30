use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::sync::atomic::{AtomicU64, Ordering};

use cott::hash::sha256_hex;

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

#[test]
fn prompt_json_is_provider_free_deterministic_scoped_and_sectioned() {
    let p = project(
        "module sample\n\nfn alpha(value: I32) -> I32:\n    doc \"\"\"Current intent marker.\"\"\"\n\nfn beta(value: I32) -> I32\n",
        Some("Project rule marker.\n"),
    );
    let tools = tool_path(&p.path);
    for name in ["cargo-never-run", "rustc-never-run", "omp"] {
        write_exec(&tools.join(name), "#!/bin/sh\nexit 77\n");
    }
    let first = prompt(&p.path, &tools, "sample.alpha");
    let second = prompt(&p.path, &tools, "sample.alpha");
    assert_eq!(first, second);
    let fields: std::collections::BTreeSet<_> = first
        .as_object()
        .unwrap()
        .keys()
        .map(String::as_str)
        .collect();
    assert_eq!(
        fields,
        [
            "symbol",
            "intent_hash",
            "prompt_hash",
            "generation_required",
            "context",
            "prompt"
        ]
        .into_iter()
        .collect()
    );
    let text = first["prompt"].as_str().unwrap();
    assert_eq!(
        first["prompt_hash"],
        format!("sha256:{}", sha256_hex(text.as_bytes()))
    );
    let formal: serde_json::Value = serde_json::from_str(
        text.split_once("```json\n")
            .unwrap()
            .1
            .split_once("\n```")
            .unwrap()
            .0,
    )
    .unwrap();
    assert!(
        formal["sample"]["declarations"]
            .as_array()
            .unwrap()
            .iter()
            .any(|d| d["name"] == "sample.alpha")
    );
    assert!(!text.contains("sample.beta"));
    assert!(
        !serde_json::to_string(&formal)
            .unwrap()
            .contains("Current intent marker.")
    );
    assert_eq!(
        fenced_prompt_section(text, "# Project rules", "text"),
        "Project rule marker.\n"
    );
    assert_eq!(
        fenced_prompt_section(text, "# Existing candidate", "rust"),
        "(none)"
    );
    assert_eq!(
        fenced_prompt_section(text, "# Actual validation feedback", "text"),
        "(none)"
    );
    assert!(!p.path.join("generated").exists());
    fs::write(p.path.join("generator.rules"), "Changed behavioral rule.\n").unwrap();
    let revised = prompt(&p.path, &tools, "sample.alpha");
    assert_ne!(revised["intent_hash"], first["intent_hash"]);
    assert_ne!(revised["prompt_hash"], first["prompt_hash"]);
    assert_eq!(
        revised["context"]["project_rules"],
        "Changed behavioral rule.\n"
    );
}

#[test]
fn prompt_signatures_equal_the_native_renderer_for_sync_async_generics_and_keywords() {
    for (source, symbol) in [
        (
            "module sample\n\nfn alpha(value: I32) -> I32\n",
            "sample.alpha",
        ),
        (
            "module sample\n\nasync fn alpha[T](value: T) -> T\n",
            "sample.alpha",
        ),
        ("module sample\n\nfn gen(value: I32) -> I32\n", "sample.gen"),
    ] {
        let p = project(source, None);
        let tools = tool_path(&p.path);
        let report = prompt(&p.path, &tools, symbol);
        let parsed =
            cott::compiler::parse_project([cott::compiler::SourceFile::new("sample.cott", source)])
                .unwrap();
        let lowered = cott::hir::lower(&p.path.join("src"), parsed).unwrap();
        let plan = cott::rust::RustPlan::from_ir(&cott::ir::render(&lowered).unwrap()).unwrap();
        let callable = plan
            .callables()
            .iter()
            .find(|callable| callable.symbol == symbol)
            .unwrap();
        let signature = cott::rust::emit::implementation_signature(&plan, callable).unwrap();
        let emitted = report["prompt"]
            .as_str()
            .unwrap()
            .split_once("```rust\n")
            .unwrap()
            .1
            .split_once("\n```")
            .unwrap()
            .0;
        assert_eq!(emitted, signature);
    }
}
