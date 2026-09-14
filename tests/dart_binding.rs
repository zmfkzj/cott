use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

use cott::compiler::{SourceFile, parse_project};
use cott::dart::binding::{partition_source, resolve, validate_candidate};
use cott::dart::emit::implementation_signature;
use cott::dart::provenance::{
    DART_GENERATION_SCHEMA_VERSION, DART_RUNTIME_ABI_VERSION, DartBindingRecord,
    DartGenerationRecord, DartGenerationSnapshot,
};
use cott::dart::{DartCallable, DartOwner, DartPlan};
use cott::hash::sha256_hex;
use cott::hir::lower;
use cott::intent;
use cott::ir::render;
use cott::manifest::DartProjectConfig;
use cott::project::{DartPaths, load_dart_config_with_paths};
use cott::provenance::{AgentRun, AgentStatus, SemanticCoverage, StreamDigest};
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
                std::env::temp_dir().join(format!("cott-dart-binding-{}-{id}", std::process::id()));
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
    config: DartProjectConfig,
    paths: DartPaths,
    plan: DartPlan,
    allowed_runtime_packages: BTreeSet<String>,
}

const MANIFEST: &str = r#"[project]
name = "demo_app"
version = "0.1.0"
source = "src"

[target.dart]
source = "dart"
generated = "generated/dart"
sdk = "dart"
runtime_validation = "boundary"
"#;

fn fixture(cott_source: &str) -> Fixture {
    let temp = TempDir::new();
    fs::create_dir_all(temp.path.join("src/api")).expect("Cott source directory");
    fs::create_dir_all(temp.path.join("dart")).expect("Dart source directory");
    fs::write(temp.path.join("cott.toml"), MANIFEST).expect("manifest");
    fs::write(temp.path.join("src/api/service.cott"), cott_source).expect("Cott source");
    let (config, paths, _) =
        load_dart_config_with_paths(&temp.path).expect("Dart manifest and paths");
    let plan = plan(&paths.source_dir, cott_source);
    Fixture {
        _temp: temp,
        config,
        paths,
        allowed_runtime_packages: BTreeSet::new(),
        plan,
    }
}

fn plan(source_dir: &Path, source: &str) -> DartPlan {
    let parsed = parse_project([SourceFile::new("api/service.cott", source)])
        .expect("fixture Cott source parses");
    let lowered = lower(source_dir, parsed).expect("fixture Cott source lowers");
    let ir = render(&lowered).expect("fixture Cott source renders");
    DartPlan::from_ir(&ir).expect("fixture Dart plan")
}

fn callable(plan: &DartPlan, symbol: &str) -> DartCallable {
    plan.callables()
        .iter()
        .find(|callable| callable.symbol == symbol)
        .expect("fixture callable")
        .clone()
}

fn candidate_source(plan: &DartPlan, callable: &DartCallable, body: &str) -> String {
    format!(
        "{} {{\n  {body}\n}}\n",
        implementation_signature(plan, callable).expect("canonical Dart signature")
    )
}

fn async_candidate_source(plan: &DartPlan, callable: &DartCallable, body: &str) -> String {
    format!(
        "{} async {{\n  {body}\n}}\n",
        implementation_signature(plan, callable).expect("canonical async Dart signature")
    )
}

fn write_source(path: &Path, source: &str) {
    fs::create_dir_all(path.parent().expect("source parent")).expect("source parent directory");
    fs::write(path, source).expect("Dart source");
}

fn digest(byte: u8) -> String {
    format!("sha256:{}", format!("{byte:02x}").repeat(32))
}

fn empty_dependencies() -> Value {
    json!({
        "schema_version": 1,
        "pubspec_hash": null,
        "lockfile_hash": null,
        "packages": []
    })
}

fn write_agent_record(
    fixture: &Fixture,
    callable: &DartCallable,
    source_path: &Path,
    source: &[u8],
    plan: &DartPlan,
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
        .strip_prefix(&fixture.paths.dart_source_dir)
        .expect("agent source is source-relative")
        .to_string_lossy()
        .replace('\\', "/");
    let private = format!("_cott_{}", callable.symbol.replace('.', "_"));
    let target_symbol = format!("{relative}:{private}");
    let runtime_origin = format!(
        "dart/lib/src/cott_impl/{}.dart",
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
    let mut snapshot = DartGenerationSnapshot {
        target: "dart".to_owned(),
        generation_id: String::new(),
        verified: false,
        compiler_version: env!("CARGO_PKG_VERSION").to_owned(),
        canonical_ir_schema: cott::provenance::CANONICAL_IR_SCHEMA_VERSION,
        runtime_abi: DART_RUNTIME_ABI_VERSION,
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
        implementations: vec![DartBindingRecord {
            cott_symbol: callable.symbol.clone(),
            target_symbol,
            source_origin,
            runtime_origin,
            content_hash: content_hash.clone(),
            owner: DartOwner::Agent,
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
        .expect("Dart generation identity");
    let record = DartGenerationRecord {
        schema_version: DART_GENERATION_SCHEMA_VERSION,
        current: snapshot,
        last_verified: None,
    };
    fs::create_dir_all(&fixture.paths.artifact_root).expect("artifact root");
    fs::write(
        fixture.paths.artifact_root.join("generation.json"),
        record.canonical_bytes().expect("Dart generation JSON"),
    )
    .expect("generation record");
}

#[test]
fn canonical_sync_async_and_generic_signatures_are_ast_exact() {
    for (cott_source, asynchronous) in [
        ("module api.service\n\nfn run(value: I32) -> I32\n", false),
        (
            "module api.service\n\nasync fn run(value: I32) -> I32\n",
            true,
        ),
        ("module api.service\n\nfn run[T](value: T) -> T\n", false),
    ] {
        let fixture = fixture(cott_source);
        let callable = callable(&fixture.plan, "api.service.run");
        let source = if asynchronous {
            async_candidate_source(&fixture.plan, &callable, "return value;")
        } else {
            candidate_source(&fixture.plan, &callable, "return value;")
        };
        validate_candidate(
            &fixture.config,
            &fixture.plan,
            &callable,
            &fixture.allowed_runtime_packages,
            source.as_bytes(),
        )
        .expect("canonical Dart candidate");
        if cott_source.contains("run[T]") {
            assert!(
                source.contains("cott_runtime.CottType<T> _cott_type_T"),
                "generic implementation ABI must carry an explicit canonical type witness"
            );
            let uses_declared_witness = source.replacen(
                "return value;",
                "final descriptor = _cott_type_T; return value;",
                1,
            );
            validate_candidate(
                &fixture.config,
                &fixture.plan,
                &callable,
                &fixture.allowed_runtime_packages,
                uses_declared_witness.as_bytes(),
            )
            .expect("the exact declared type witness is available to the target body");
            let uses_witness_value = source.replacen(
                "return value;",
                "final descriptor = [_cott_type_T].single; return value;",
                1,
            );
            validate_candidate(
                &fixture.config,
                &fixture.plan,
                &callable,
                &fixture.allowed_runtime_packages,
                uses_witness_value.as_bytes(),
            )
            .expect("a canonical witness remains usable as an ordinary value");
            let forged_witness_member = source.replacen(
                "return value;",
                "final hidden = [_cott_type_T].single._cott_type_T; return value;",
                1,
            );
            validate_candidate(
                &fixture.config,
                &fixture.plan,
                &callable,
                &fixture.allowed_runtime_packages,
                forged_witness_member.as_bytes(),
            )
            .expect_err("canonical witness spelling must not authorize a private member");
            let forged_witness =
                source.replacen("return value;", "_cott_type_escape; return value;", 1);
            validate_candidate(
                &fixture.config,
                &fixture.plan,
                &callable,
                &fixture.allowed_runtime_packages,
                forged_witness.as_bytes(),
            )
            .expect_err("undeclared `_cott_` controls must not be broadly allowed");
        }

        let wrong_parameter = source.replacen(" value", " changed", 1);
        validate_candidate(
            &fixture.config,
            &fixture.plan,
            &callable,
            &fixture.allowed_runtime_packages,
            wrong_parameter.as_bytes(),
        )
        .expect_err("renamed canonical parameter must fail");

        let public_name = source.replacen("_cott_api_service_run", "run", 1);
        validate_candidate(
            &fixture.config,
            &fixture.plan,
            &callable,
            &fixture.allowed_runtime_packages,
            public_name.as_bytes(),
        )
        .expect_err("agent implementation must use its exact private name");
    }
}

#[test]
fn guarded_state_witnesses_are_exact_without_exposing_compiler_private_members() {
    let mut fixture = fixture(
        r#"module api.service

trait Counter:
    fn increment(self, amount: I32) -> I32
    fn decrement(self, amount: I32) -> I32

impl CounterState for Counter:
    state:
        value: I32 = 0
    fn increment(self, amount: I32) -> I32:
        modifies self.value
        ensures result >= 0
    fn decrement(self, amount: I32) -> I32:
        modifies self.value
        ensures result >= 0
"#,
    );
    fixture.config.dart.implementations.insert(
        "api.service.CounterState.decrement".to_owned(),
        "bindings/decrement.dart:_decrement".to_owned(),
    );
    let callable = callable(&fixture.plan, "api.service.CounterState.increment");
    let source = candidate_source(
        &fixture.plan,
        &callable,
        "final leaseIdentity = _cott_lease.hashCode;\n  final current = _cott_mutation.read('value') as int;\n  _cott_mutation.write('value', current + amount);\n  return current + amount + leaseIdentity - leaseIdentity;",
    );
    validate_candidate(
        &fixture.config,
        &fixture.plan,
        &callable,
        &fixture.allowed_runtime_packages,
        source.as_bytes(),
    )
    .expect("exact mutation and lease witnesses are legal in the guarded owner boundary");

    let safe_callback = format!(
        "import 'dart:async' show scheduleMicrotask;\n\n{}",
        candidate_source(
            &fixture.plan,
            &callable,
            "scheduleMicrotask(() { amount.abs(); });\n  return (amount >= 0 ? [amount] : [amount]).single.abs();",
        )
    );
    validate_candidate(
        &fixture.config,
        &fixture.plan,
        &callable,
        &fixture.allowed_runtime_packages,
        safe_callback.as_bytes(),
    )
    .expect("ordinary callbacks, values, and arbitrary receiver members remain legal");

    for body in [
        "final raw = _cott_mutation.compilerLease; return amount;",
        "final raw = [_cott_mutation].single.compilerLease; return amount;",
        "final raw = [_cott_mutation][0].compilerLease; return amount;",
        "final raw = (() => _cott_mutation)().compilerLease; return amount;",
        "final raw = (amount >= 0 ? _cott_mutation : _cott_mutation).compilerLease; return amount;",
        "final raw = Object().runtimeType; return amount;",
    ] {
        let bypass = candidate_source(&fixture.plan, &callable, body);
        validate_candidate(
            &fixture.config,
            &fixture.plan,
            &callable,
            &fixture.allowed_runtime_packages,
            bypass.as_bytes(),
        )
        .expect_err("forbidden member capabilities must not depend on receiver path resolution");
    }

    let aliased_capability = format!(
        "import 'dart:math' as compilerLease;\n\n{}",
        candidate_source(
            &fixture.plan,
            &callable,
            "final raw = [_cott_mutation].single.compilerLease; return amount;",
        )
    );
    validate_candidate(
        &fixture.config,
        &fixture.plan,
        &callable,
        &fixture.allowed_runtime_packages,
        aliased_capability.as_bytes(),
    )
    .expect_err("an ordinary import alias cannot launder a selected capability leaf");

    let deferred_state_write = format!(
        "import 'dart:async' show scheduleMicrotask;\n\n{}",
        candidate_source(
            &fixture.plan,
            &callable,
            "scheduleMicrotask(() { self._cott_state_value = 999; });\n  return self.value;",
        )
    );
    validate_candidate(
        &fixture.config,
        &fixture.plan,
        &callable,
        &fixture.allowed_runtime_packages,
        deferred_state_write.as_bytes(),
    )
    .expect_err("a shared-owner callback cannot mutate raw state after guard revocation");

    for body in [
        "final raw = self._cott_state_value; return amount + raw;",
        "[self][0]._cott_state_value = amount; return amount;",
        "final raw = [self].single._cott_resource_guard; return amount;",
        "final raw = (() => self)()._cott_resource; return amount;",
        "final raw = (amount >= 0 ? self : self)._cott_resource_contract; return amount;",
        "final raw = [self][0]._cott_carrier_8cd0efa9d510b04f; return amount;",
        "final raw = [self].single._cott_view; return amount;",
        "final raw = (() => self)()._cott_rebuild; return amount;",
        "final raw = (amount >= 0 ? self : self)._cott_view_seal; return amount;",
        "final raw = self._cott_mutation; return amount;",
        "final raw = self._cott_lease; return amount;",
    ] {
        let bypass = candidate_source(&fixture.plan, &callable, body);
        validate_candidate(
            &fixture.config,
            &fixture.plan,
            &callable,
            &fixture.allowed_runtime_packages,
            bypass.as_bytes(),
        )
        .expect_err("compiler-private members must be inaccessible on every receiver shape");
    }

    let cross_method = source.replacen(
        "final current =",
        "final bypass = _decrement;\n  final current =",
        1,
    );
    validate_candidate(
        &fixture.config,
        &fixture.plan,
        &callable,
        &fixture.allowed_runtime_packages,
        cross_method.as_bytes(),
    )
    .expect_err("an owner-private method tear-off cannot bypass its guarded wrapper");
}

#[test]
fn typed_scalar_generic_and_async_helpers_must_be_reachable() {
    let fixture = fixture("module api.service\n\nasync fn run(value: I32) -> I32\n");
    let callable = callable(&fixture.plan, "api.service.run");
    let source = format!(
        "{} async {{\n  return await _later(_identity<int>(_twice(value)));\n}}\n\nint _twice(int value) {{\n  return value * 2;\n}}\n\nT _identity<T>(T value) {{\n  return value;\n}}\n\nFuture<int> _later(int value) async {{\n  return value;\n}}\n",
        implementation_signature(&fixture.plan, &callable).unwrap()
    );
    validate_candidate(
        &fixture.config,
        &fixture.plan,
        &callable,
        &fixture.allowed_runtime_packages,
        source.as_bytes(),
    )
    .expect("reachable typed scalar, generic, and async helpers");

    for invalid in [
        source.replace("int _twice(int value)", "int twice(int value)"),
        source.replace("int _twice(int value)", "int _twice(value)"),
        source.replace("int _twice(int value)", "dynamic _twice(int value)"),
        source.replace(
            "Future<int> _later(int value) async",
            "int _later(int value) async",
        ),
        format!("{source}\nint _unused(int value) => value;\n"),
        source.replace("int _twice(int value)", "int _twice([int value = 0])"),
    ] {
        assert!(
            validate_candidate(
                &fixture.config,
                &fixture.plan,
                &callable,
                &fixture.allowed_runtime_packages,
                invalid.as_bytes()
            )
            .is_err(),
            "invalid helper surface was accepted:\n{invalid}"
        );
    }
}

#[test]
fn callable_references_resolve_private_targets_without_banning_local_helpers() {
    let fixture =
        fixture("module api.service\n\nfn run(value: I32) -> I32\nfn hidden(value: I32) -> I32\n");
    let callable = callable(&fixture.plan, "api.service.run");
    let signature = implementation_signature(&fixture.plan, &callable).unwrap();
    let helper_reference = format!(
        "{signature} {{ final transform = _identity; return transform(value); }}\n\nint _identity(int value) => value;\n"
    );
    validate_candidate(
        &fixture.config,
        &fixture.plan,
        &callable,
        &fixture.allowed_runtime_packages,
        helper_reference.as_bytes(),
    )
    .expect("a referenced typed local helper tear-off remains legal");

    for body in [
        "return _cott_api_service_hidden(value);",
        "final hidden = _cott_api_service_hidden; return hidden(value);",
    ] {
        let source = format!("{signature} {{ {body} }}\n");
        validate_candidate(
            &fixture.config,
            &fixture.plan,
            &callable,
            &fixture.allowed_runtime_packages,
            source.as_bytes(),
        )
        .expect_err("another canonical private implementation cannot bypass its facade");
    }
}

#[test]
fn imports_allow_real_aliases_but_reject_prefix_spoofing_and_capabilities() {
    let fixture = fixture("module api.service\n\nfn run(value: I32) -> I32\n");
    let callable = callable(&fixture.plan, "api.service.run");
    let aliased = format!(
        "import 'dart:math' as arithmetic show max;\n\n{} {{\n  const inert = 'CottObservation compilerLease Process';\n  return arithmetic.max(value, inert.length);\n}}\n",
        implementation_signature(&fixture.plan, &callable).unwrap()
    );
    validate_candidate(
        &fixture.config,
        &fixture.plan,
        &callable,
        &fixture.allowed_runtime_packages,
        aliased.as_bytes(),
    )
    .expect("ordinary audited import prefix");
    let capability_spelling_is_only_an_alias = aliased
        .replace("as arithmetic", "as Process")
        .replace("arithmetic.max", "Process.max");
    validate_candidate(
        &fixture.config,
        &fixture.plan,
        &callable,
        &fixture.allowed_runtime_packages,
        capability_spelling_is_only_an_alias.as_bytes(),
    )
    .expect("a valid alias is resolved by its URI, not banned by its spelling");

    let signature = implementation_signature(&fixture.plan, &callable).unwrap();
    let cases = [
        format!("import 'dart:math' as cott_runtime;\n\n{signature} {{ return value; }}\n"),
        format!("import 'dart:io' as host;\n\n{signature} {{ return value; }}\n"),
        format!("import 'dart:math' deferred as arithmetic;\n\n{signature} {{ return value; }}\n"),
        format!(
            "import 'dart:math' if (dart.library.io) 'dart:io';\n\n{signature} {{ return value; }}\n"
        ),
        format!(
            "import 'package:demo_app/src/wrappers/api/service/run.dart';\n\n{signature} {{ return value; }}\n"
        ),
        format!("{signature} {{ dynamic result = value; return result; }}\n"),
        format!(
            "{signature} {{ final text = '${{CottObservation()}}'; return value + text.length; }}\n"
        ),
        format!(
            "{signature} {{ return Function.apply(_identity, <Object?>[value]) as int; }}\n\nint _identity(int value) => value;\n"
        ),
        format!("{signature} {{ CottTaskScope(); return value; }}\n"),
        format!(
            "{signature} {{ cott_runtime.CottRuntime.withTestObservation(() => value); return value; }}\n"
        ),
        format!(
            "import 'package:demo_app/cott_runtime.dart' as runtime_api;\n\n{signature} {{ final observe = runtime_api.CottRuntime.withTestObservation; return value; }}\n"
        ),
        format!(
            "{signature} {{ final forge = cott_runtime.CottTypes.checkedNominal; return value + forge.hashCode; }}\n"
        ),
        format!("{signature} {{ final spawn = Isolate.spawn; return value + spawn.hashCode; }}\n"),
        format!("{signature} {{ return _cott_mutation.compilerLease.hashCode + value; }}\n"),
    ];
    for source in cases {
        assert!(
            validate_candidate(
                &fixture.config,
                &fixture.plan,
                &callable,
                &fixture.allowed_runtime_packages,
                source.as_bytes()
            )
            .is_err(),
            "malicious import or capability was accepted:\n{source}"
        );
    }
}

#[test]
fn locked_dependency_packages_authorize_only_exact_safe_import_prefixes() {
    let mut fixture = fixture("module api.service\n\nfn run(value: I32) -> I32\n");
    fixture
        .allowed_runtime_packages
        .extend(["path_a", "hosted_b"].map(str::to_owned));
    let callable = callable(&fixture.plan, "api.service.run");
    for uri in [
        "package:path_a/path_a.dart",
        "package:hosted_b/src/value-helper.dart",
    ] {
        let source = format!(
            "import '{uri}' as dependency;\n\n{}",
            candidate_source(&fixture.plan, &callable, "return dependency.adjust(value);",)
        );
        validate_candidate(
            &fixture.config,
            &fixture.plan,
            &callable,
            &fixture.allowed_runtime_packages,
            source.as_bytes(),
        )
        .expect("an exact frozen runtime dependency package grants import authority");
    }

    for uri in [
        "package:path_a_extra/path_a.dart",
        "package:dev_only/dev_only.dart",
        "package:demo_app/modules/api/service.dart",
        "package:demo_app/src/wrappers/api/service/run.dart",
        "package:path_a/path_a.txt",
        "package:path_a/src/../path_a.dart",
        "package:path_a/src//helper.dart",
        "package:path_a/path%2Fa.dart",
        "file:///tmp/escape.dart",
        "http://example.invalid/escape.dart",
        "https://example.invalid/escape.dart",
    ] {
        let source = format!(
            "import '{uri}' as dependency;\n\n{}",
            candidate_source(&fixture.plan, &callable, "return value;")
        );
        assert!(
            validate_candidate(
                &fixture.config,
                &fixture.plan,
                &callable,
                &fixture.allowed_runtime_packages,
                source.as_bytes(),
            )
            .is_err(),
            "non-authoritative or unsafe dependency import was accepted:\n{source}"
        );
    }
}

#[test]
fn declared_io_effects_authorize_canonical_file_and_network_apis() {
    let fixture = fixture(
        "module api.service\n\nfn read(path: Path) -> Str:\n    effects [file.read]\n\nfn write(path: Path, value: I32) -> I32:\n    effects [file.write]\n\nfn fetch(value: I32) -> I32:\n    effects [network]\n\nfn pure(value: I32) -> I32\n",
    );

    let read = callable(&fixture.plan, "api.service.read");
    let read_source = format!(
        "import 'dart:io' as host show File;\n\n{}",
        candidate_source(
            &fixture.plan,
            &read,
            "return host.File(path.value).readAsStringSync();",
        )
    );
    validate_candidate(
        &fixture.config,
        &fixture.plan,
        &read,
        &fixture.allowed_runtime_packages,
        read_source.as_bytes(),
    )
    .expect("a declared file.read boundary can use File with the caller's CottPath");

    for body in [
        "return File(path.value).readAsStringSync();",
        "return host.File(path.value).readAsStringSync();",
    ] {
        let source = candidate_source(&fixture.plan, &read, body);
        validate_candidate(
            &fixture.config,
            &fixture.plan,
            &read,
            &fixture.allowed_runtime_packages,
            source.as_bytes(),
        )
        .expect_err("I/O authority must come from this implementation source's own import");
    }

    let write = callable(&fixture.plan, "api.service.write");
    let write_source = format!(
        "import 'dart:io' show File;\n\n{}",
        candidate_source(
            &fixture.plan,
            &write,
            "File(path.value).writeAsStringSync(value.toString());\n  return value;",
        )
    );
    validate_candidate(
        &fixture.config,
        &fixture.plan,
        &write,
        &fixture.allowed_runtime_packages,
        write_source.as_bytes(),
    )
    .expect("a declared file.write boundary can use ordinary File APIs");

    let fetch = callable(&fixture.plan, "api.service.fetch");
    let fetch_source = format!(
        "import 'dart:io' as host show HttpClient;\n\n{}",
        candidate_source(
            &fixture.plan,
            &fetch,
            "final client = host.HttpClient();\n  client.close(force: true);\n  return value;",
        )
    );
    validate_candidate(
        &fixture.config,
        &fixture.plan,
        &fetch,
        &fixture.allowed_runtime_packages,
        fetch_source.as_bytes(),
    )
    .expect("a declared network boundary can use ordinary dart:io HTTP APIs");

    let pure = callable(&fixture.plan, "api.service.pure");
    let core_source = format!(
        "import 'dart:core';\n\n{}",
        candidate_source(&fixture.plan, &pure, "return value.abs();")
    );
    validate_candidate(
        &fixture.config,
        &fixture.plan,
        &pure,
        &fixture.allowed_runtime_packages,
        core_source.as_bytes(),
    )
    .expect("an explicit canonical dart:core import is legal");

    let file_network_escalation = format!(
        "import 'dart:io' as host;\n\n{}",
        candidate_source(
            &fixture.plan,
            &read,
            "final client = host.HttpClient();\n  client.close();\n  return path.value;",
        )
    );
    validate_candidate(
        &fixture.config,
        &fixture.plan,
        &read,
        &fixture.allowed_runtime_packages,
        file_network_escalation.as_bytes(),
    )
    .expect_err("file authority must not grant network authority");

    let network_file_escalation = format!(
        "import 'dart:io' as host;\n\n{}",
        candidate_source(
            &fixture.plan,
            &fetch,
            "final file = host.File('outside');\n  return value + file.path.length;",
        )
    );
    validate_candidate(
        &fixture.config,
        &fixture.plan,
        &fetch,
        &fixture.allowed_runtime_packages,
        network_file_escalation.as_bytes(),
    )
    .expect_err("network authority must not grant filesystem authority");
}

#[test]
fn dart_io_keeps_process_stdio_and_compiler_observation_closed() {
    let fixture =
        fixture("module api.service\n\nfn read(path: Path) -> Str:\n    effects [file.read]\n");
    let callable = callable(&fixture.plan, "api.service.read");
    for body in [
        "final start = [host.Process].single.start;\n  return start.toString();",
        "host.exit(0);",
        "host.exitCode = 0;\n  return path.value;",
        "final input = [host.stdin].single;\n  return input.toString();",
        "final output = (() => host.stdout)();\n  return output.toString();",
        "final environment = (true ? host.Platform : host.Platform).environment;\n  return environment.toString();",
        "final rss = [host.ProcessInfo].single.currentRss;\n  return rss.toString();",
        "final overrides = host.IOOverrides.current;\n  return overrides.toString();",
        "final overrides = host.HttpOverrides.current;\n  return overrides.toString();",
        "host.Directory.current = host.Directory(path.value);\n  return path.value;",
    ] {
        let source = format!(
            "import 'dart:io' as host;\n\n{}",
            candidate_source(&fixture.plan, &callable, body)
        );
        assert!(
            validate_candidate(
                &fixture.config,
                &fixture.plan,
                &callable,
                &fixture.allowed_runtime_packages,
                source.as_bytes()
            )
            .is_err(),
            "dart:io control or observation capability was accepted:\n{source}"
        );
    }

    for body in [
        "exitCode = 0;\n  return path.value;",
        "final start = [Process].single.start;\n  return start.toString();",
        "final input = [stdin].single;\n  return input.toString();",
        "final environment = (() => Platform)().environment;\n  return environment.toString();",
    ] {
        let source = format!(
            "import 'dart:io';\n\n{}",
            candidate_source(&fixture.plan, &callable, body)
        );
        assert!(
            validate_candidate(
                &fixture.config,
                &fixture.plan,
                &callable,
                &fixture.allowed_runtime_packages,
                source.as_bytes()
            )
            .is_err(),
            "unprefixed dart:io control or observation capability was accepted:\n{source}"
        );
    }
}

#[test]
fn external_type_projections_never_grant_import_authority() {
    let mut fixture = fixture("module api.service\n\nfn run(value: I32) -> I32\n");
    fixture.config.dart.external_types.insert(
        "api.service.External".to_owned(),
        "package:untrusted/io.dart#External".to_owned(),
    );
    let callable = callable(&fixture.plan, "api.service.run");
    for uri in [
        "package:untrusted/io.dart",
        "dart:ffi",
        "dart:developer",
        "dart:isolate",
        "dart:mirrors",
        "file:///tmp/escape.dart",
        "https://example.invalid/escape.dart",
    ] {
        let source = format!(
            "import '{uri}' as external;\n\n{}",
            candidate_source(&fixture.plan, &callable, "return value;")
        );
        assert!(
            validate_candidate(
                &fixture.config,
                &fixture.plan,
                &callable,
                &fixture.allowed_runtime_packages,
                source.as_bytes()
            )
            .is_err(),
            "external projection or arbitrary URI granted import authority:\n{source}"
        );
    }
}

#[test]
fn authored_library_control_and_top_level_execution_are_rejected() {
    let fixture = fixture("module api.service\n\nfn run(value: I32) -> I32\n");
    let callable = callable(&fixture.plan, "api.service.run");
    let signature = implementation_signature(&fixture.plan, &callable).unwrap();
    for source in [
        format!("library forged;\n{signature} {{ return value; }}\n"),
        format!("part 'forged.dart';\n{signature} {{ return value; }}\n"),
        format!("part of forged;\n{signature} {{ return value; }}\n"),
        format!("export 'dart:math';\n{signature} {{ return value; }}\n"),
        format!("final eager = 1;\n{signature} {{ return value; }}\n"),
        format!("@pragma('vm:entry-point')\n{signature} {{ return value; }}\n"),
        format!("// ignore_for_file: unused_local_variable\n{signature} {{ return value; }}\n"),
        format!("{signature} {{ assert(value >= 0); return value; }}\n"),
    ] {
        assert!(
            validate_candidate(
                &fixture.config,
                &fixture.plan,
                &callable,
                &fixture.allowed_runtime_packages,
                source.as_bytes()
            )
            .is_err(),
            "forbidden Dart source shape was accepted:\n{source}"
        );
    }
}

#[test]
fn partition_preserves_every_non_import_byte_and_never_rewrites_inert_text() {
    let source = concat!(
        "// leading comment\n",
        "import 'dart:math' as maths show max;\n",
        "\n",
        "int _run(int value) {\n",
        "  const inert = \"import 'dart:io'; part of forged;\";\n",
        "  // export 'private.dart';\n",
        "  return maths.max(value, inert.length);\n",
        "}\n"
    );
    let parsed = partition_source(source.as_bytes()).expect("AST source partition");
    assert_eq!(
        parsed.imports,
        vec!["import 'dart:math' as maths show max;".to_owned()]
    );
    assert_eq!(
        parsed.body,
        concat!(
            "// leading comment\n",
            "\n",
            "\n",
            "int _run(int value) {\n",
            "  const inert = \"import 'dart:io'; part of forged;\";\n",
            "  // export 'private.dart';\n",
            "  return maths.max(value, inert.length);\n",
            "}\n"
        )
    );

    for forbidden in [
        "export 'dart:math';\nint _run() => 1;\n",
        "library forged;\nint _run() => 1;\n",
        "part 'forged.dart';\nint _run() => 1;\n",
        "final eager = 1;\nint _run() => eager;\n",
    ] {
        partition_source(forbidden.as_bytes())
            .expect_err("non-import directive or executable top level cannot be partitioned");
    }
}

#[test]
fn manifest_resolution_uses_exact_path_private_name_and_original_identity() {
    let mut fixture = fixture("module api.service\n\nfn run(value: I32) -> I32\n");
    fixture.config.dart.implementations.insert(
        "api.service.run".to_owned(),
        "bindings/service.dart:_run".to_owned(),
    );
    let callable = callable(&fixture.plan, "api.service.run");
    let signature = implementation_signature(&fixture.plan, &callable).unwrap();
    let source = format!(
        "{} {{\n  return value;\n}}\n",
        signature.replacen("_cott_api_service_run", "_run", 1)
    );
    let selected = fixture.paths.dart_source_dir.join("bindings/service.dart");
    write_source(&selected, &source);
    write_source(
        &fixture.paths.dart_source_dir.join("other.dart"),
        "int _run(int value) => value + 1;\n",
    );

    let bindings = resolve(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        &fixture.allowed_runtime_packages,
        None,
    )
    .expect("exact configured Dart source resolves despite same name elsewhere");
    assert_eq!(bindings.len(), 1);
    assert_eq!(bindings[0].cott_symbol, "api.service.run");
    assert_eq!(bindings[0].target_symbol, "bindings/service.dart:_run");
    assert_eq!(
        bindings[0].source_origin,
        Path::new("dart/bindings/service.dart")
    );
    assert_eq!(
        bindings[0].runtime_origin,
        Path::new("dart/lib/src/cott_impl/api/service/run.dart")
    );
    assert_eq!(bindings[0].owner, DartOwner::Manifest);
    assert_eq!(bindings[0].bytes, source.as_bytes());
    assert_eq!(
        bindings[0].content_hash,
        format!("sha256:{}", sha256_hex(source.as_bytes()))
    );

    fs::write(&selected, format!("{source}{source}")).expect("duplicate private declaration");
    resolve(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        &fixture.allowed_runtime_packages,
        None,
    )
    .expect_err("duplicate target declarations in selected path must fail");
}

#[test]
fn durable_agent_identity_distinguishes_missing_stale_tampered_and_pending_sources() {
    let fixture =
        fixture("module api.service\n\nfn run(value: I32) -> I32:\n    ensures result > 0\n");
    let callable = callable(&fixture.plan, "api.service.run");
    let source = candidate_source(&fixture.plan, &callable, "return value;");
    let path = fixture
        .paths
        .dart_source_dir
        .join("cott_impl/api/service/run.dart");

    let bindings = resolve(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        &fixture.allowed_runtime_packages,
        None,
    )
    .expect("absent agent source is unresolved");
    assert!(bindings.is_empty());

    write_source(&path, &source);
    resolve(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        &fixture.allowed_runtime_packages,
        None,
    )
    .expect_err("unrecorded durable agent source must fail");

    write_agent_record(
        &fixture,
        &callable,
        &path,
        source.as_bytes(),
        &fixture.plan,
        Vec::new(),
        None,
    );
    let bindings = resolve(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        &fixture.allowed_runtime_packages,
        None,
    )
    .expect("recorded durable source resolves");
    assert_eq!(bindings.len(), 1);
    assert_eq!(bindings[0].owner, DartOwner::Agent);

    fs::write(&path, format!("{source}// tampered\n")).expect("tamper source");
    resolve(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        &fixture.allowed_runtime_packages,
        None,
    )
    .expect_err("tampered durable source must fail");
    fs::write(&path, &source).expect("restore source");

    let changed = plan(
        &fixture.paths.source_dir,
        "module api.service\n\nfn run(value: I32) -> I32:\n    ensures result > 1\n",
    );
    let bindings = resolve(
        &fixture.config,
        &fixture.paths,
        &changed,
        &fixture.allowed_runtime_packages,
        None,
    )
    .expect("intent-stale authentic bytes remain unresolved");
    assert!(bindings.is_empty());

    write_agent_record(
        &fixture,
        &callable,
        &path,
        source.as_bytes(),
        &fixture.plan,
        vec![callable.symbol.clone()],
        None,
    );
    let bindings = resolve(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        &fixture.allowed_runtime_packages,
        None,
    )
    .expect("authentic pending bytes remain source-audited but unresolved");
    assert!(bindings.is_empty());

    let unsafe_pending =
        candidate_source(&fixture.plan, &callable, "CottObservation(); return value;");
    fs::write(&path, &unsafe_pending).expect("unsafe pending source");
    write_agent_record(
        &fixture,
        &callable,
        &path,
        unsafe_pending.as_bytes(),
        &fixture.plan,
        vec![callable.symbol.clone()],
        None,
    );
    resolve(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        &fixture.allowed_runtime_packages,
        None,
    )
    .expect_err("provider success cannot retain a source that fails the AST authority audit");
}

#[test]
fn recorded_agent_paths_cannot_move_and_manifest_rereads_cannot_refresh_intent() {
    let fixture = fixture("module api.service\n\nfn run(value: I32) -> I32\n");
    let callable = callable(&fixture.plan, "api.service.run");
    let source = candidate_source(&fixture.plan, &callable, "return value;");
    let path = fixture
        .paths
        .dart_source_dir
        .join("cott_impl/api/service/run.dart");
    write_source(&path, &source);
    write_agent_record(
        &fixture,
        &callable,
        &path,
        source.as_bytes(),
        &fixture.plan,
        Vec::new(),
        None,
    );

    fs::write(
        &fixture.paths.manifest,
        MANIFEST.replace("version = \"0.1.0\"", "version = \"9.9.9\""),
    )
    .expect("change bytes after config was frozen");
    assert_eq!(
        resolve(
            &fixture.config,
            &fixture.paths,
            &fixture.plan,
            &fixture.allowed_runtime_packages,
            None
        )
        .expect("resolver must not re-read manifest intent")
        .len(),
        1
    );

    let record_path = fixture.paths.artifact_root.join("generation.json");
    let mut moved = DartGenerationRecord::parse(&fs::read(&record_path).unwrap()).unwrap();
    moved.current.implementations[0].target_symbol =
        "cott_impl/api/service/moved.dart:_cott_api_service_run".to_owned();
    moved.current.implementations[0].source_origin =
        "dart/cott_impl/api/service/moved.dart".to_owned();
    moved.current.compute_generation_id().unwrap();
    fs::write(&record_path, moved.canonical_bytes().unwrap()).unwrap();
    resolve(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        &fixture.allowed_runtime_packages,
        None,
    )
    .expect_err("moved recorded agent identity must fail closed");
}

#[test]
fn only_supplied_frozen_generator_rules_can_retain_agent_intent() {
    let mut fixture = fixture("module api.service\n\nfn run(value: I32) -> I32\n");
    fixture.config.generator.rules = Some("GENERATOR_RULES.txt".to_owned());
    let callable = callable(&fixture.plan, "api.service.run");
    let source = candidate_source(&fixture.plan, &callable, "return value;");
    let path = fixture
        .paths
        .dart_source_dir
        .join("cott_impl/api/service/run.dart");
    write_source(&path, &source);
    let original_rules = "cott-domain api.service.run return: preserve the value\n";
    let revised_rules = "cott-domain api.service.run return: increment the value\n";
    fs::write(
        fixture.paths.root.join("GENERATOR_RULES.txt"),
        "contents on disk are deliberately not authoritative\n",
    )
    .expect("non-authoritative rules file");
    write_agent_record(
        &fixture,
        &callable,
        &path,
        source.as_bytes(),
        &fixture.plan,
        Vec::new(),
        Some(original_rules),
    );

    assert_eq!(
        resolve(
            &fixture.config,
            &fixture.paths,
            &fixture.plan,
            &fixture.allowed_runtime_packages,
            Some(original_rules),
        )
        .expect("matching frozen rules retain the agent implementation")
        .len(),
        1
    );
    assert!(
        resolve(
            &fixture.config,
            &fixture.paths,
            &fixture.plan,
            &fixture.allowed_runtime_packages,
            Some(revised_rules),
        )
        .expect("changed frozen rules make genuine bytes stale")
        .is_empty()
    );
    resolve(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        &fixture.allowed_runtime_packages,
        None,
    )
    .expect_err("configured rules must be supplied from the frozen project load");
}

#[test]
fn project_consumers_must_use_public_facades_not_private_or_generated_libraries() {
    let mut fixture = fixture("module api.service\n\nfn run(value: I32) -> I32\n");
    fixture.config.dart.implementations.insert(
        "api.service.run".to_owned(),
        "bindings/service.dart:_run".to_owned(),
    );
    let callable = callable(&fixture.plan, "api.service.run");
    let signature = implementation_signature(&fixture.plan, &callable).unwrap();
    write_source(
        &fixture.paths.dart_source_dir.join("bindings/service.dart"),
        &format!(
            "{} => value;\n",
            signature.replacen("_cott_api_service_run", "_run", 1)
        ),
    );
    let consumer = fixture.paths.dart_source_dir.join("consumer.dart");
    write_source(
        &consumer,
        "import 'package:demo_app/modules/api/service.dart' as api;\nObject? call(Object? value) => value;\n",
    );
    resolve(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        &fixture.allowed_runtime_packages,
        None,
    )
    .expect("public module facade with an ordinary alias remains legal");

    for source in [
        "import 'bindings/service.dart';\nObject? call(Object? value) => value;\n",
        "export 'bindings/service.dart';\nObject? call(Object? value) => value;\n",
        "import 'package:demo_app/src/wrappers/api/service/run.dart' as hidden;\nObject? call(Object? value) => value;\n",
        "import 'package:demo_app/src/types/api/service.dart' as internal_types;\nObject? call(Object? value) => value;\n",
        "import 'cott_impl/api/service/run.dart';\nObject? call(Object? value) => value;\n",
    ] {
        fs::write(&consumer, source).expect("consumer source");
        resolve(
            &fixture.config,
            &fixture.paths,
            &fixture.plan,
            &fixture.allowed_runtime_packages,
            None,
        )
        .expect_err("project consumer bypassed the generated public facade");
    }
}
