use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

use cott::compiler::{SourceFile, parse_project};
use cott::hash::sha256_hex;
use cott::hir::lower;
use cott::intent;
use cott::ir::render;
use cott::manifest::RustProjectConfig;
use cott::project::{RustPaths, load_rust_config_with_paths};
use cott::provenance::{AgentRun, AgentStatus, SemanticCoverage, StreamDigest};
use cott::rust::binding::{partition_source, resolve, validate_candidate};
use cott::rust::emit::implementation_signature;
use cott::rust::provenance::{
    RUST_GENERATION_SCHEMA_VERSION, RUST_RUNTIME_ABI_VERSION, RustBindingRecord,
    RustGenerationRecord, RustGenerationSnapshot,
};
use cott::rust::{RustCallable, RustOwner, RustPlan};
use serde_json::{Value, json};

static NEXT_TEMP: AtomicU64 = AtomicU64::new(0);

struct TempDir {
    path: PathBuf,
}

impl TempDir {
    fn new() -> Self {
        let mut id = NEXT_TEMP.fetch_add(1, Ordering::Relaxed);
        loop {
            let path =
                std::env::temp_dir().join(format!("cott-rust-binding-{}-{id}", std::process::id()));
            match fs::create_dir(&path) {
                Ok(()) => return Self { path },
                Err(error) if error.kind() == io::ErrorKind::AlreadyExists => id += 1,
                Err(error) => panic!("create temporary fixture: {error}"),
            }
        }
    }
}

impl Drop for TempDir {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.path);
    }
}

struct Fixture {
    _temp: TempDir,
    config: RustProjectConfig,
    paths: RustPaths,
    plan: RustPlan,
    allowed_runtime_packages: BTreeSet<String>,
}

const MANIFEST: &str = r#"[project]
name = "demo_app"
version = "0.1.0"
source = "src"

[target.rust]
source = "rust"
generated = "generated/rust"
cargo = "cargo"
rustc = "rustc"
runtime_validation = "boundary"
"#;

fn fixture(cott_source: &str) -> Fixture {
    let temp = TempDir::new();
    fs::create_dir_all(temp.path.join("src/api")).expect("Cott source directory");
    fs::create_dir_all(temp.path.join("rust")).expect("Rust source directory");
    fs::write(temp.path.join("cott.toml"), MANIFEST).expect("manifest");
    fs::write(temp.path.join("src/api/service.cott"), cott_source).expect("Cott source");
    let (config, paths, _) =
        load_rust_config_with_paths(&temp.path).expect("Rust manifest and paths");
    let plan = plan(&paths.source_dir, cott_source);
    Fixture {
        _temp: temp,
        config,
        paths,
        allowed_runtime_packages: BTreeSet::new(),
        plan,
    }
}

fn plan(source_dir: &Path, source: &str) -> RustPlan {
    let parsed = parse_project([SourceFile::new("api/service.cott", source)])
        .expect("fixture Cott source parses");
    let lowered = lower(source_dir, parsed).expect("fixture Cott source lowers");
    let ir = render(&lowered).expect("fixture Cott source renders");
    RustPlan::from_ir(&ir).expect("fixture Rust plan")
}

fn callable(plan: &RustPlan, symbol: &str) -> RustCallable {
    plan.callables()
        .iter()
        .find(|callable| callable.symbol == symbol)
        .expect("fixture callable")
        .clone()
}

fn candidate_source(plan: &RustPlan, callable: &RustCallable, body: &str) -> String {
    format!(
        "{} {{\n  {body}\n}}\n",
        implementation_signature(plan, callable).expect("canonical Rust signature")
    )
}

fn write_source(path: &Path, source: &str) {
    fs::create_dir_all(path.parent().expect("source parent")).expect("source parent directory");
    fs::write(path, source).expect("Rust source");
}

fn digest(byte: u8) -> String {
    format!("sha256:{}", format!("{byte:02x}").repeat(32))
}

fn empty_dependencies() -> Value {
    json!({
        "schema_version": 1,
        "cargo_manifest_hash": null,
        "lockfile_hash": null,
        "packages": []
    })
}

fn write_agent_record(
    fixture: &Fixture,
    callable: &RustCallable,
    source_path: &Path,
    source: &[u8],
    plan: &RustPlan,
    unresolved: Vec<String>,
    generator_rules: Option<&str>,
) {
    let content_hash = format!("sha256:{}", sha256_hex(source));
    let source_origin = source_path
        .strip_prefix(&fixture.paths.root)
        .expect("agent source is project-relative")
        .to_string_lossy()
        .replace('\\', "/");
    let relative = source_path
        .strip_prefix(&fixture.paths.rust_source_dir)
        .expect("agent source is source-relative")
        .to_string_lossy()
        .replace('\\', "/");
    let private = callable.name.clone();
    let target_symbol = format!("{relative}:{private}");
    let runtime_origin = format!(
        "rust/src/cott_impl/{}.rs",
        callable.symbol.replace('.', "/")
    );
    let fingerprints = intent::fingerprints(
        plan.contract_surface(),
        generator_rules.unwrap_or_default().as_bytes(),
    )
    .expect("fixture intent fingerprints");
    let tools = json!({ intent::TOOL_KEY: intent::metadata(&fingerprints) });
    let mut inputs = BTreeMap::from([
        (
            "cott.toml".to_owned(),
            format!(
                "sha256:{}",
                sha256_hex(&fs::read(&fixture.paths.manifest).unwrap())
            ),
        ),
        (
            "src/api/service.cott".to_owned(),
            format!(
                "sha256:{}",
                sha256_hex(&fs::read(fixture.paths.source_dir.join("api/service.cott")).unwrap())
            ),
        ),
        (source_origin.clone(), content_hash.clone()),
    ]);
    if let (Some(path), Some(rules)) = (&fixture.config.generator.rules, generator_rules) {
        inputs.insert(
            path.clone(),
            format!("sha256:{}", sha256_hex(rules.as_bytes())),
        );
    }
    let mut snapshot = RustGenerationSnapshot {
        target: "rust".to_owned(),
        generation_id: String::new(),
        verified: false,
        compiler_version: env!("CARGO_PKG_VERSION").to_owned(),
        canonical_ir_schema: cott::provenance::CANONICAL_IR_SCHEMA_VERSION,
        runtime_abi: RUST_RUNTIME_ABI_VERSION,
        project_name: fixture.config.project.name.clone(),
        project_version: fixture.config.project.version.clone(),
        inputs,
        tools,
        ir: plan
            .ir
            .modules
            .iter()
            .map(|module| {
                (
                    module.module.as_string(),
                    format!("sha256:{}", sha256_hex(&module.bytes)),
                )
            })
            .collect(),
        contract_surface: plan.contract_surface().clone(),
        public_symbols: BTreeMap::new(),
        implementations: vec![RustBindingRecord {
            cott_symbol: callable.symbol.clone(),
            target_symbol,
            source_origin,
            runtime_origin,
            content_hash: content_hash.clone(),
            owner: RustOwner::Agent,
        }],
        dependencies: empty_dependencies(),
        managed_files: BTreeMap::new(),
        unresolved,
        verification: Value::Null,
        semantic_coverage: SemanticCoverage::default(),
        agent_runs: vec![AgentRun {
            symbol: callable.symbol.clone(),
            adapter: "codex".to_owned(),
            adapter_version: "1".to_owned(),
            argv_template: vec!["codex".to_owned(), "{prompt}".to_owned()],
            executable: "/fixture/codex".to_owned(),
            executable_hash: digest(1),
            prompt_hash: digest(2),
            implementation_hash: content_hash,
            environment_names: Vec::new(),
            duration_ms: 1,
            status: AgentStatus {
                exit_code: Some(0),
                signal: None,
                timed_out: false,
                cancelled: false,
            },
            stdout: StreamDigest {
                bytes: 0,
                sha256: digest(3),
                truncated: false,
            },
            stderr: StreamDigest {
                bytes: 0,
                sha256: digest(4),
                truncated: false,
            },
        }],
    };
    snapshot
        .compute_generation_id()
        .expect("Rust generation identity");
    let record = RustGenerationRecord {
        schema_version: RUST_GENERATION_SCHEMA_VERSION,
        current: snapshot,
        last_verified: None,
    };
    fs::create_dir_all(&fixture.paths.artifact_root).expect("artifact root");
    fs::write(
        fixture.paths.artifact_root.join("generation.json"),
        record.canonical_bytes().expect("Rust generation JSON"),
    )
    .expect("generation record");
}

const SIMPLE: &str = "module api.service\n\nfn run(value: I32) -> I32\n";
fn check(f: &Fixture, source: &str) -> Result<(), String> {
    validate_candidate(
        &f.config,
        &f.plan,
        &callable(&f.plan, "api.service.run"),
        &f.allowed_runtime_packages,
        source.as_bytes(),
    )
}
#[test]
fn accepts_exact_signatures_and_private_helpers() {
    for cott in [
        SIMPLE,
        "module api.service\n\nasync fn run(value: I32) -> I32\n",
        "module api.service\n\nfn run[T](value: T) -> T\n",
    ] {
        let f = fixture(cott);
        let c = callable(&f.plan, "api.service.run");
        let source = candidate_source(&f.plan, &c, "value");
        validate_candidate(&f.config, &f.plan, &c, &BTreeSet::new(), source.as_bytes()).unwrap();
    }
    let f = fixture(SIMPLE);
    check(&f, "pub(crate) fn run(value: i32) -> i32 { helper(value) }\nfn helper(value: i32) -> i32 { value }").unwrap();
    assert!(check(&f, "pub(crate) fn run(value: i64) -> i32 { 0 }").is_err());
}
#[test]
fn rejects_every_unauthorized_syntax_and_capability_class() {
    let f = fixture(SIMPLE);
    for fragment in [
        "unsafe { value }",
        "std::process::exit(0)",
        "std::env::var(\"HOME\"); value",
        "std::io::stdout(); value",
        "include!(\"other.rs\")",
        "include_str!(\"secret\"); value",
        "include_bytes!(\"secret\"); value",
        "env!(\"HOME\"); value",
        "option_env!(\"HOME\"); value",
        "crate::cott_impl::other::run(value)",
        "super::other(value)",
        "crate::cott_runtime::__cott_observe_clause(); value",
        "std::fs::read(\"/secret\"); value",
        "std::net::TcpStream::connect(\"host:80\"); value",
        "std::thread::spawn(|| 1); value",
        "unrecorded_dependency::call(); value",
        "println!(\"hi\"); value",
    ] {
        let source = candidate_source(&f.plan, &callable(&f.plan, "api.service.run"), fragment);
        assert!(check(&f, &source).is_err(), "accepted {fragment}");
    }
    for prefix in [
        "extern \"C\" { fn bad(); }",
        "macro_rules! bad { () => { 1 } }",
        "#[path = \"other.rs\"] mod bad;",
        "#![allow(warnings)]",
        "#[cfg(any())]",
        "#[allow(unused)]",
        "mod bad {}",
        "pub fn bad() {}",
        "pub(crate) fn bad() {}",
        "use unauthorized::X;",
        "use std::env as e;",
        "use std::collections::*;",
        "use crate::cott_impl::other;",
    ] {
        let source = format!(
            "{prefix}\n{}",
            candidate_source(&f.plan, &callable(&f.plan, "api.service.run"), "value")
        );
        assert!(check(&f, &source).is_err(), "accepted {prefix}");
    }
}
#[test]
fn partition_preserves_comments_strings_and_authored_bytes() {
    let source = "// use fake::x;\nuse std::collections::BTreeMap;\npub(crate) fn run(value: i32) -> i32 { let _s = \"unsafe extern include!\"; value }\n";
    let result = partition_source(source.as_bytes()).unwrap();
    assert_eq!(result.imports, ["use std::collections::BTreeMap;"]);
    assert_eq!(
        result.body,
        "// use fake::x;\n\npub(crate) fn run(value: i32) -> i32 { let _s = \"unsafe extern include!\"; value }\n"
    );
    check(&fixture(SIMPLE), source).unwrap();
}
#[test]
fn manifest_binding_is_resolved_without_agent_provenance() {
    let mut f = fixture(SIMPLE);
    f.config
        .rust
        .implementations
        .insert("api.service.run".into(), "bindings/run.rs:run".into());
    write_source(
        &f.paths.rust_source_dir.join("bindings/run.rs"),
        &candidate_source(&f.plan, &callable(&f.plan, "api.service.run"), "value"),
    );
    let bindings = resolve(&f.config, &f.paths, &f.plan, &BTreeSet::new(), None).unwrap();
    assert_eq!(bindings[0].owner, RustOwner::Manifest);
    assert_eq!(
        bindings[0].runtime_origin,
        PathBuf::from("rust/src/cott_impl/api/service/run.rs")
    );
}
#[test]
fn durable_agent_authentication_and_pending_lifecycle() {
    let f = fixture(SIMPLE);
    let c = callable(&f.plan, "api.service.run");
    assert!(
        resolve(&f.config, &f.paths, &f.plan, &BTreeSet::new(), None)
            .unwrap()
            .is_empty()
    );
    let path = f.paths.rust_source_dir.join("cott_impl/api/service/run.rs");
    let source = candidate_source(&f.plan, &c, "value");
    write_source(&path, &source);
    assert!(
        resolve(&f.config, &f.paths, &f.plan, &BTreeSet::new(), None)
            .unwrap_err()
            .contains("provenance")
    );
    write_agent_record(&f, &c, &path, source.as_bytes(), &f.plan, vec![], None);
    assert_eq!(
        resolve(&f.config, &f.paths, &f.plan, &BTreeSet::new(), None).unwrap()[0].owner,
        RustOwner::Agent
    );
    write_agent_record(
        &f,
        &c,
        &path,
        source.as_bytes(),
        &f.plan,
        vec![c.symbol.clone()],
        None,
    );
    assert!(
        resolve(&f.config, &f.paths, &f.plan, &BTreeSet::new(), None)
            .unwrap()
            .is_empty()
    );
    write_source(&path, &source.replace("value\n", "value + 1\n"));
    assert!(resolve(&f.config, &f.paths, &f.plan, &BTreeSet::new(), None).is_err());
}
#[test]
fn moved_missing_manifest_shadowed_and_stale_intent_fail_closed() {
    let mut f = fixture(SIMPLE);
    let c = callable(&f.plan, "api.service.run");
    let path = f.paths.rust_source_dir.join("cott_impl/api/service/run.rs");
    let source = candidate_source(&f.plan, &c, "value");
    write_source(&path, &source);
    write_agent_record(&f, &c, &path, source.as_bytes(), &f.plan, vec![], None);
    let changed = plan(
        &f.paths.source_dir,
        "module api.service\n\nfn run(value: I32) -> I32:\n    doc \"\"\"A changed intent.\"\"\"\n",
    );
    assert!(
        resolve(&f.config, &f.paths, &changed, &BTreeSet::new(), None)
            .unwrap()
            .is_empty()
    );
    fs::rename(&path, path.with_file_name("moved.rs")).unwrap();
    assert!(resolve(&f.config, &f.paths, &f.plan, &BTreeSet::new(), None).is_err());
    fs::remove_file(path.with_file_name("moved.rs")).unwrap();
    assert!(
        resolve(&f.config, &f.paths, &f.plan, &BTreeSet::new(), None)
            .unwrap()
            .is_empty()
    );
    write_source(&path, &source);
    f.config
        .rust
        .implementations
        .insert(c.symbol, "bindings/run.rs:run".into());
    write_source(&f.paths.rust_source_dir.join("bindings/run.rs"), &source);
    assert!(
        resolve(&f.config, &f.paths, &f.plan, &BTreeSet::new(), None)
            .unwrap_err()
            .contains("manifest-shadowed")
    );
}

#[test]
fn file_effects_cannot_escalate_to_writes_network_or_control() {
    let f = fixture("module api.service\n\nfn run(value: I32) -> I32:\n    effects [file.read]\n");
    for body in [
        "let _ = std::fs::read(\"file\"); value",
        "let _ = std::fs::metadata(\"file\"); value",
    ] {
        check(
            &f,
            &candidate_source(&f.plan, &callable(&f.plan, "api.service.run"), body),
        )
        .unwrap();
    }
    for body in [
        "std::fs::write(\"file\", \"data\"); value",
        "std::fs::create_dir(\"directory\"); value",
        "std::net::TcpStream::connect(\"host:80\"); value",
        "std::io::stdout(); value",
    ] {
        assert!(
            check(
                &f,
                &candidate_source(&f.plan, &callable(&f.plan, "api.service.run"), body)
            )
            .is_err(),
            "{body}"
        );
    }
}

#[test]
fn dependency_authority_aliases_and_macro_arguments_are_closed() {
    let mut f = fixture(SIMPLE);
    let source = "use chosen_dep::Api;\npub(crate) fn run(value: i32) -> i32 { Api::call(value) }";
    assert!(check(&f, source).is_err());
    f.allowed_runtime_packages.insert("chosen_dep".into());
    check(&f, source).unwrap();
    for body in [
        "let _ = vec![include_str!(\"secret\")]; value",
        "let _ = format!(\"{}\", std::env::var(\"HOME\").unwrap()); value",
        "let _ = crate::cott_runtime::ReadField::new(&value); value",
        "crate::cott_runtime::StateGate::new(); value",
    ] {
        assert!(
            check(
                &f,
                &candidate_source(&f.plan, &callable(&f.plan, "api.service.run"), body)
            )
            .is_err(),
            "{body}"
        );
    }
    let macro_alias = "use chosen_dep::unchecked as vec;\npub(crate) fn run(value: i32) -> i32 { let _ = vec![value]; value }";
    assert!(check(&f, macro_alias).is_err());
    check(&f, "pub(crate) fn run(value: i32) -> i32 { let _ = format!(\"unsafe::extern\"); let _ = vec![value]; value }").unwrap();
}

#[test]
fn rust_keyword_callable_names_keep_canonical_raw_spelling() {
    let f = fixture(
        "module api.service\n\nfn gen(value: I32) -> I32\n\nfn loop(value: I32) -> I32\n\nfn box(value: I32) -> I32\n",
    );
    for name in ["gen", "loop", "box"] {
        let c = callable(&f.plan, &format!("api.service.{name}"));
        let source = candidate_source(&f.plan, &c, "value");
        validate_candidate(&f.config, &f.plan, &c, &BTreeSet::new(), source.as_bytes()).unwrap();
    }
}

#[test]
fn resource_method_sources_include_concrete_owner_and_declared_state_authority() {
    let f = fixture(
        r#"module api.service

trait Counter:
    fn increment(self, amount: I32) -> I32

impl CounterState for Counter:
    state:
        value: I32 = 0
    fn increment(self, amount: I32) -> I32:
        modifies self.value
"#,
    );
    let c = callable(&f.plan, "api.service.CounterState.increment");
    let source = candidate_source(
        &f.plan,
        &c,
        "let next = *receiver.get_value() + amount; receiver.set_value(next); next",
    );
    validate_candidate(&f.config, &f.plan, &c, &BTreeSet::new(), source.as_bytes()).unwrap();
    let bad = source.replace("set_value", "set_other");
    assert!(validate_candidate(&f.config, &f.plan, &c, &BTreeSet::new(), bad.as_bytes()).is_err());
    let path = f
        .paths
        .rust_source_dir
        .join("cott_impl/api/service/CounterState/increment.rs");
    write_source(&path, &source);
    write_agent_record(&f, &c, &path, source.as_bytes(), &f.plan, vec![], None);
    let resolved = resolve(&f.config, &f.paths, &f.plan, &BTreeSet::new(), None).unwrap();
    assert_eq!(
        resolved[0].source_origin,
        PathBuf::from("rust/cott_impl/api/service/CounterState/increment.rs")
    );
    assert_eq!(
        resolved[0].target_symbol,
        "cott_impl/api/service/CounterState/increment.rs:increment"
    );
}

#[test]
fn api_like_local_names_do_not_grant_or_require_standard_effect_authority() {
    let f = fixture("module api.service\n\nfn read(env: I32) -> I32\n");
    let c = callable(&f.plan, "api.service.read");
    let source = candidate_source(&f.plan, &c, "env");
    validate_candidate(&f.config, &f.plan, &c, &BTreeSet::new(), source.as_bytes()).unwrap();
    let bad = candidate_source(&f.plan, &c, "std::env::var(\"HOME\"); env");
    assert!(validate_candidate(&f.config, &f.plan, &c, &BTreeSet::new(), bad.as_bytes()).is_err());
}

#[test]
fn duration_values_are_pure_but_clock_reads_require_clock_effect() {
    let f = fixture(SIMPLE);
    check(
        &f,
        "pub(crate) fn run(value: i32) -> i32 { let _ = std::time::Duration::from_secs(1); value }",
    )
    .unwrap();
    let source =
        "pub(crate) fn run(value: i32) -> i32 { let _ = std::time::SystemTime::now(); value }";
    assert!(check(&f, source).is_err());
    let clock = fixture("module api.service\n\nfn run(value: I32) -> I32:\n    effects [clock]\n");
    check(&clock, source).unwrap();
}

#[test]
fn tracked_async_spawn_requires_unshadowed_task_scope_authority() {
    let f = fixture("module api.service\n\nasync fn run(value: I32) -> I32\n");
    let c = callable(&f.plan, "api.service.run");
    let allowed = candidate_source(
        &f.plan,
        &c,
        "let scope = crate::cott_runtime::TaskScope::new(); scope.spawn(async move { value }); value",
    );
    validate_candidate(&f.config, &f.plan, &c, &BTreeSet::new(), allowed.as_bytes()).unwrap();
    for body in [
        "value.spawn(async move { value }); value",
        "let scope = crate::cott_runtime::TaskScope::new(); { let scope = value; scope.spawn(async move { value }); } value",
        "let scope = crate::cott_runtime::TaskScope::new(); let _ = |scope| { scope.spawn(async move { value }); }; value",
        "value.__cott_observe_clause(); value",
        "static HIDDEN: i32 = 1; value",
        "use std::collections::BTreeMap; value",
    ] {
        let source = candidate_source(&f.plan, &c, body);
        assert!(
            validate_candidate(&f.config, &f.plan, &c, &BTreeSet::new(), source.as_bytes())
                .is_err(),
            "{body}"
        );
    }
    let imported = format!(
        "use crate::cott_runtime::TaskScope as Scope;\n{}",
        candidate_source(
            &f.plan,
            &c,
            "let scope: Scope = Scope::new(); scope.spawn(async move { value }); value"
        )
    );
    validate_candidate(
        &f.config,
        &f.plan,
        &c,
        &BTreeSet::new(),
        imported.as_bytes(),
    )
    .unwrap();
    let generic_shadow = format!(
        "use crate::cott_runtime::TaskScope as Scope;\n{}\nfn helper<Scope>() {{ let scope = Scope::new(); scope.spawn(async move {{ 1 }}); }}",
        candidate_source(&f.plan, &c, "value")
    );
    assert!(
        validate_candidate(
            &f.config,
            &f.plan,
            &c,
            &BTreeSet::new(),
            generic_shadow.as_bytes()
        )
        .is_err()
    );
    let sync = fixture(SIMPLE);
    let source = candidate_source(
        &sync.plan,
        &callable(&sync.plan, "api.service.run"),
        "let scope = crate::cott_runtime::TaskScope::new(); scope.spawn(async move { value }); value",
    );
    assert!(check(&sync, &source).is_err());
}

#[test]
fn scoped_generic_facade_calls_cannot_escape_context_or_become_values() {
    let f = fixture(
        "module api.service\n\nfn run(value: I32) -> I32:\n    doc \"\"\"Use api.service.other.\"\"\"\n\nfn other[T](value: T) -> T\n\nfn outside(value: I32) -> I32\n",
    );
    check(
        &f,
        &candidate_source(
            &f.plan,
            &callable(&f.plan, "api.service.run"),
            "crate::modules::api::service::other::<i32>(value)",
        ),
    )
    .unwrap();
    for body in [
        "let _ = crate::modules::api::service::other::<i32>; value",
        "crate::modules::api::service::outside(value)",
    ] {
        assert!(
            check(
                &f,
                &candidate_source(&f.plan, &callable(&f.plan, "api.service.run"), body)
            )
            .is_err(),
            "{body}"
        );
    }
}

#[test]
fn native_pure_trait_read_is_not_mistaken_for_a_filesystem_read() {
    let f = fixture(
        r#"module api.service

trait Reader:
    fn read(self, value: I32) -> I32

impl PureReader for Reader:
    fn read(self, value: I32) -> I32:
        ensures result == value

fn run(value: I32) -> I32:
    doc """Use api.service.PureReader."""
"#,
    );
    let source = candidate_source(
        &f.plan,
        &callable(&f.plan, "api.service.run"),
        "let mut reader = crate::modules::api::service::PureReader::new(); reader.read(value)",
    );
    check(&f, &source).unwrap();
    let value = candidate_source(
        &f.plan,
        &callable(&f.plan, "api.service.run"),
        "let _ = crate::modules::api::service::Reader::read; value",
    );
    assert!(check(&f, &value).is_err());
}
