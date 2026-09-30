use serde_json::Value;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::sync::atomic::{AtomicU64, Ordering};
static NEXT: AtomicU64 = AtomicU64::new(0);
pub struct Fixture {
    pub root: PathBuf,
}
impl Drop for Fixture {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.root);
    }
}
pub fn cargo() -> PathBuf {
    let cargo = PathBuf::from(
        std::env::var_os("COTT_CARGO").expect("COTT_CARGO must name the provisioned Cargo"),
    );
    assert!(cargo.is_absolute());
    cargo
}
pub fn rustc() -> PathBuf {
    std::env::var_os("COTT_RUSTC")
        .map(PathBuf::from)
        .unwrap_or_else(|| cargo().parent().unwrap().join("rustc"))
}
impl Fixture {
    pub fn new(label: &str, source: &str, bindings: &[(&str, &str, &str)], extra: &str) -> Self {
        let root = std::env::temp_dir().join(format!(
            "cott-rust-native-{label}-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir(&root).unwrap();
        let fixture = Self { root };
        fs::create_dir_all(fixture.root.join("src/demo")).unwrap();
        fs::create_dir_all(fixture.root.join("rust/bindings")).unwrap();
        let parsed = cott::compiler::parse_project([cott::compiler::SourceFile::new(
            "demo/runner.cott",
            source,
        )])
        .expect("native Cott source");
        let hir = cott::hir::lower(Path::new("src"), parsed).expect("native Cott HIR");
        let plan = cott::rust::RustPlan::from_ir(&cott::ir::render(&hir).unwrap()).unwrap();
        let mut manifest = format!(
            "[project]\nname='demo'\nversion='0.1.0'\nsource='src'\n[target.rust]\nsource='rust'\ngenerated='generated/rust'\nruntime_validation='boundary'\ncargo={:?}\nrustc={:?}\n[target.rust.implementations]\n",
            cargo().to_string_lossy(),
            rustc().to_string_lossy()
        );
        for &(symbol, body, helpers) in bindings {
            let callable = plan
                .callables()
                .iter()
                .find(|c| c.symbol == symbol)
                .expect("native callable");
            let signature = cott::rust::emit::implementation_signature(&plan, callable)
                .expect("native canonical signature");
            let filename = format!("{}.rs", symbol.replace('.', "_"));
            fs::write(
                fixture.root.join("rust/bindings").join(&filename),
                format!("{helpers}\n{signature} {{ {body} }}\n"),
            )
            .unwrap();
            manifest.push_str(&format!(
                "{symbol:?}={:?}\n",
                format!("bindings/{filename}:{}", callable.name)
            ));
        }
        manifest.push_str(extra);
        fs::write(fixture.root.join("cott.toml"), manifest).unwrap();
        fs::write(fixture.root.join("src/demo/runner.cott"), source).unwrap();
        fixture
    }
    pub fn run(&self, args: &[&str]) -> Output {
        let home = self.root.join("home");
        fs::create_dir_all(&home).unwrap();
        let original_home = std::env::var_os("HOME")
            .map(PathBuf::from)
            .expect("HOME for provisioned archives");
        let cargo_home = std::env::var_os("CARGO_HOME")
            .map(PathBuf::from)
            .unwrap_or_else(|| original_home.join(".cargo"));
        let rustup_home = std::env::var_os("RUSTUP_HOME")
            .map(PathBuf::from)
            .unwrap_or_else(|| original_home.join(".rustup"));
        let mut command = Command::new(env!("CARGO_BIN_EXE_cott"));
        command
            .args(args)
            .args(["--project"])
            .arg(&self.root)
            .env_clear()
            .env("HOME", home)
            .env("CARGO_HOME", cargo_home)
            .env("RUSTUP_HOME", rustup_home)
            .env("PATH", "/usr/bin:/bin")
            .env("CARGO_PROFILE_DEV_DEBUG", "0")
            .env("CARGO_PROFILE_TEST_DEBUG", "0")
            .env("CARGO_INCREMENTAL", "0");
        if let Some(toolchain) = std::env::var_os("RUSTUP_TOOLCHAIN") {
            command.env("RUSTUP_TOOLCHAIN", toolchain);
        }
        command.output().expect("native cott CLI")
    }
    pub fn emit(&self) {
        let output = self.run(&["emit", "rust"]);
        assert_eq!(output.status.code(), Some(0), "{}", stderr(&output));
    }
    pub fn verify(&self) -> Value {
        let output = self.run(&["verify"]);
        assert_eq!(output.status.code(), Some(0), "{}", stderr(&output));
        let record = self.record();
        assert_eq!(record["current"], record["last_verified"]);
        assert_eq!(current(&record)["verified"], true);
        record
    }
    pub fn record(&self) -> Value {
        serde_json::from_slice(&fs::read(self.root.join("generated/generation.json")).unwrap())
            .unwrap()
    }
}
pub fn stderr(output: &Output) -> String {
    String::from_utf8_lossy(&output.stderr).into_owned()
}
pub fn current(record: &Value) -> &Value {
    &record["snapshots"][record["current"].as_str().unwrap()]
}
pub fn observed(record: &Value, symbol: &str, clause: &str) -> bool {
    current(record)["semantic_coverage"]["clauses"]
        .as_array()
        .unwrap()
        .iter()
        .any(|c| c["symbol"] == symbol && c["clause_id"] == clause && c["status"] == "observed")
}
pub fn scenario(record: &Value, id: &str) -> Value {
    current(record)["verification"]["contract_tests"]["scenarios"]
        .as_array()
        .unwrap()
        .iter()
        .find(|s| s["scenario_id"] == id)
        .cloned()
        .expect("executed native scenario")
}
