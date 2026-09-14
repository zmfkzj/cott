use std::collections::BTreeMap;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

use cott::compiler::{SourceFile, parse_project};
use cott::hash::sha256_hex;
use cott::hir::lower;
use cott::intent;
use cott::ir::render;
use cott::kotlin::binding::{resolve, validate_candidate};
use cott::kotlin::emit::implementation_signature;
use cott::kotlin::provenance::{
    KOTLIN_GENERATION_SCHEMA_VERSION, KOTLIN_RUNTIME_ABI_VERSION, KotlinBindingRecord,
    KotlinGenerationRecord, KotlinGenerationSnapshot,
};
use cott::kotlin::{KotlinCallable, KotlinOwner, KotlinPlan};
use cott::manifest::KotlinProjectConfig;
use cott::project::{KotlinPaths, load_kotlin_config_with_paths};
use cott::provenance::{AgentRun, AgentStatus, SemanticCoverage, StreamDigest};

static NEXT_TEMP: AtomicU64 = AtomicU64::new(0);

struct TempDir {
    path: PathBuf,
}

impl TempDir {
    fn new() -> Self {
        let mut id = NEXT_TEMP.fetch_add(1, Ordering::Relaxed);
        loop {
            let path = std::env::temp_dir()
                .join(format!("cott-kotlin-binding-{}-{id}", std::process::id()));
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
    config: KotlinProjectConfig,
    paths: KotlinPaths,
    plan: KotlinPlan,
}

const MANIFEST: &str = r#"[project]
name = "demo"
version = "0.1.0"
source = "src"

[target.kotlin]
source = "kotlin"
generated = "generated/kotlin"
compiler = "kotlinc"
java = "java"
jvm_target = 17
runtime_validation = "boundary"
"#;

fn fixture(cott_source: &str) -> Fixture {
    let temp = TempDir::new();
    fs::create_dir_all(temp.path.join("src/api")).expect("Cott source directory");
    fs::create_dir_all(temp.path.join("kotlin")).expect("Kotlin source directory");
    fs::write(temp.path.join("cott.toml"), MANIFEST).expect("manifest");
    fs::write(temp.path.join("src/api/service.cott"), cott_source).expect("Cott source");
    let (config, paths, _) =
        load_kotlin_config_with_paths(&temp.path).expect("Kotlin manifest and paths");
    let plan = plan(&paths.source_dir, cott_source);
    Fixture {
        _temp: temp,
        config,
        paths,
        plan,
    }
}

fn plan(source_dir: &Path, source: &str) -> KotlinPlan {
    let parsed = parse_project([SourceFile::new("api/service.cott", source)])
        .expect("fixture Cott source parses");
    let lowered = lower(source_dir, parsed).expect("fixture Cott source lowers");
    let ir = render(&lowered).expect("fixture Cott source renders");
    KotlinPlan::from_ir(&ir).expect("fixture Kotlin plan")
}

fn callable<'a>(plan: &'a KotlinPlan, symbol: &str) -> KotlinCallable {
    plan.callables()
        .into_iter()
        .find(|callable| callable.symbol == symbol)
        .expect("fixture callable")
}

fn candidate_source(plan: &KotlinPlan, callable: &KotlinCallable, body: &str) -> String {
    let mut package = format!("cott_impl.{}", callable.module);
    if let Some(owner) = &callable.owner {
        package.push('.');
        package.push_str(
            owner["name"]
                .as_str()
                .expect("implementation owner name")
                .rsplit('.')
                .next()
                .expect("concrete name"),
        );
    }
    format!(
        "package {package}\n\n{} {{\n    {body}\n}}\n",
        implementation_signature(plan, callable).expect("canonical Kotlin signature")
    )
}

fn write_source(path: &Path, source: &str) {
    fs::create_dir_all(path.parent().expect("source parent")).expect("source parent directory");
    fs::write(path, source).expect("Kotlin source");
}

fn digest(byte: u8) -> String {
    format!("sha256:{}", format!("{byte:02x}").repeat(32))
}

fn write_agent_record(
    fixture: &Fixture,
    callable: &KotlinCallable,
    source_path: &Path,
    source: &[u8],
    plan: &KotlinPlan,
    unresolved: Vec<String>,
    generator_rules: Option<&str>,
) {
    let content_hash = format!("sha256:{}", sha256_hex(source));
    let source_origin = source_path
        .strip_prefix(&fixture.paths.root)
        .expect("agent source is project-relative")
        .to_string_lossy()
        .replace('\\', "/");
    let target_symbol = format!("cott_impl.{}.{}", callable.module, callable.name);
    let runtime_origin = format!(
        "kotlin/cott_impl/{}/{}.kt",
        callable.module.replace('.', "/"),
        callable.name
    );
    let fingerprints = intent::fingerprints(
        &plan.contract_surface(),
        generator_rules.unwrap_or_default().as_bytes(),
    )
    .expect("fixture intent fingerprints");
    let tools = serde_json::json!({ intent::TOOL_KEY: intent::metadata(&fingerprints) });
    let mut inputs = BTreeMap::new();
    inputs.insert(
        "cott.toml".to_owned(),
        format!(
            "sha256:{}",
            sha256_hex(&fs::read(&fixture.paths.manifest).expect("manifest bytes"))
        ),
    );
    match (&fixture.config.generator.rules, generator_rules) {
        (Some(path), Some(rules)) => {
            inputs.insert(
                path.clone(),
                format!("sha256:{}", sha256_hex(rules.as_bytes())),
            );
        }
        (None, None) => {}
        _ => panic!("fixture generator rules do not match its config"),
    }
    let mut snapshot = KotlinGenerationSnapshot {
        target: "kotlin".to_owned(),
        generation_id: String::new(),
        verified: false,
        compiler_version: env!("CARGO_PKG_VERSION").to_owned(),
        canonical_ir_schema: cott::provenance::CANONICAL_IR_SCHEMA_VERSION,
        runtime_abi: KOTLIN_RUNTIME_ABI_VERSION,
        project_name: fixture.config.project.name.clone(),
        project_version: fixture.config.project.version.clone(),
        inputs,
        tools,
        ir: BTreeMap::new(),
        contract_surface: plan.contract_surface(),
        public_symbols: BTreeMap::new(),
        implementations: vec![KotlinBindingRecord {
            cott_symbol: callable.symbol.clone(),
            target_symbol,
            source_origin,
            runtime_origin,
            content_hash: content_hash.clone(),
            owner: KotlinOwner::Agent,
        }],
        managed_files: BTreeMap::new(),
        unresolved,
        verification: serde_json::Value::Null,
        semantic_coverage: SemanticCoverage::default(),
        agent_runs: vec![AgentRun {
            symbol: callable.symbol.clone(),
            adapter: "fixture".to_owned(),
            adapter_version: "1".to_owned(),
            argv_template: Vec::new(),
            executable: "/fixture/agent".to_owned(),
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
        .expect("Kotlin generation identity");
    let record = KotlinGenerationRecord {
        schema_version: KOTLIN_GENERATION_SCHEMA_VERSION,
        current: snapshot,
        last_verified: None,
    };
    fs::create_dir_all(&fixture.paths.artifact_root).expect("artifact root");
    fs::write(
        fixture.paths.artifact_root.join("generation.json"),
        record.canonical_bytes().expect("Kotlin generation JSON"),
    )
    .expect("generation record");
}

#[test]
fn exact_sync_async_and_generic_candidates_match_canonical_signatures() {
    for cott_source in [
        "module api.service\n\nfn run(value: I32) -> I32\n",
        "module api.service\n\nasync fn run(value: I32) -> I32\n",
        "module api.service\n\nfn run[T](value: T) -> T\n",
    ] {
        let fixture = fixture(cott_source);
        let callable = callable(&fixture.plan, "api.service.run");
        let source = candidate_source(
            &fixture.plan,
            &callable,
            "throw IllegalStateException(\"fixture\")",
        );
        validate_candidate(&fixture.config, &fixture.plan, &callable, source.as_bytes())
            .expect("exact candidate source");
    }
}

#[test]
fn identifier_quoting_is_semantic_in_canonical_signature_comparison() {
    let fixture = fixture("module api.service\n\nfn run(value: I32) -> I32\n");
    let callable = callable(&fixture.plan, "api.service.run");
    let canonical = candidate_source(&fixture.plan, &callable, "return value");
    let ordinary_parameter = canonical.replacen("`value`", "value", 1);
    assert_ne!(
        ordinary_parameter, canonical,
        "fixture must unquote the parameter identifier"
    );
    let equivalent = ordinary_parameter.replacen("kotlin.Int", "kotlin.`Int`", 1);
    assert_ne!(
        equivalent, ordinary_parameter,
        "fixture must quote a qualified type segment"
    );

    validate_candidate(
        &fixture.config,
        &fixture.plan,
        &callable,
        equivalent.as_bytes(),
    )
    .expect("equivalent identifier quoting");
}

#[test]
fn identifier_normalization_preserves_signature_identity() {
    let fixture = fixture("module api.service\n\nfn run(value: I32) -> I32\n");
    let callable = callable(&fixture.plan, "api.service.run");
    let canonical = candidate_source(
        &fixture.plan,
        &callable,
        "throw IllegalStateException(\"fixture\")",
    );
    let equivalent =
        canonical
            .replacen("`value`", "value", 1)
            .replacen("kotlin.Int", "kotlin.`Int`", 1);

    let wrong_parameter = equivalent.replacen("value:", "other:", 1);
    assert_ne!(
        wrong_parameter, equivalent,
        "fixture must change the parameter identity"
    );
    validate_candidate(
        &fixture.config,
        &fixture.plan,
        &callable,
        wrong_parameter.as_bytes(),
    )
    .expect_err("a renamed parameter must fail");

    let bare_keyword = equivalent.replacen("value:", "when:", 1);
    assert_ne!(
        bare_keyword, equivalent,
        "fixture must use an unquoted Kotlin keyword as a parameter"
    );
    validate_candidate(
        &fixture.config,
        &fixture.plan,
        &callable,
        bare_keyword.as_bytes(),
    )
    .expect_err("an unquoted keyword parameter must remain malformed");

    let wrong_type = equivalent.replacen("kotlin.`Int`", "kotlin.`Long`", 1);
    assert_ne!(
        wrong_type, equivalent,
        "fixture must change a parameter type"
    );
    validate_candidate(
        &fixture.config,
        &fixture.plan,
        &callable,
        wrong_type.as_bytes(),
    )
    .expect_err("a changed type must fail");

    let wrong_modifier = equivalent.replacen("internal fun", "public fun", 1);
    assert_ne!(
        wrong_modifier, equivalent,
        "fixture must change the visibility modifier"
    );
    validate_candidate(
        &fixture.config,
        &fixture.plan,
        &callable,
        wrong_modifier.as_bytes(),
    )
    .expect_err("a changed modifier must fail");
}

#[test]
fn const_generic_witness_is_exact_and_only_declared_witness_references_are_allowed() {
    let fixture =
        fixture("module api.service\n\nfn run[const N: U32](values: Array[I32, N]) -> I32\n");
    let callable = callable(&fixture.plan, "api.service.run");
    let source = candidate_source(
        &fixture.plan,
        &callable,
        "val witness = _cott_const_N\n    throw IllegalStateException(witness.toString())",
    );
    assert!(
        source.contains("_cott_const_N: N"),
        "implementation signature must carry the const witness"
    );
    validate_candidate(&fixture.config, &fixture.plan, &callable, source.as_bytes())
        .expect("declared const witness reference");

    let bypass = candidate_source(
        &fixture.plan,
        &callable,
        "_cott_runtime_escape()\n    throw IllegalStateException()",
    );
    validate_candidate(&fixture.config, &fixture.plan, &callable, bypass.as_bytes())
        .expect_err("arbitrary reserved implementation reference must fail");
}

#[test]
fn explicit_unit_bodies_are_complete_source_shapes() {
    let fixture = fixture("module api.service\n\nfn finish() -> Unit\n");
    let callable = callable(&fixture.plan, "api.service.finish");
    let signature = implementation_signature(&fixture.plan, &callable).expect("signature");
    for source in [
        format!("package cott_impl.api.service\n\n{signature} = Unit\n"),
        format!("package cott_impl.api.service\n\n{signature} {{\n    return Unit\n}}\n"),
    ] {
        validate_candidate(&fixture.config, &fixture.plan, &callable, source.as_bytes())
            .expect("explicit Unit body is structurally complete");
    }

    let missing = format!("package cott_impl.api.service\n\n{signature}\n");
    validate_candidate(
        &fixture.config,
        &fixture.plan,
        &callable,
        missing.as_bytes(),
    )
    .expect_err("a declaration without a body must fail");
}

#[test]
fn anonymous_protocol_overrides_may_capture_const_witnesses() {
    let fixture = fixture(
        "module api.service\n\nfn run[const N: U32](values: Array[I32, N]) -> Iterator[I32]\n",
    );
    let callable = callable(&fixture.plan, "api.service.run");
    let source = candidate_source(
        &fixture.plan,
        &callable,
        "return object : kotlin.collections.Iterator<kotlin.Int> {\n        override fun hasNext(): kotlin.Boolean = false\n        override fun next(): kotlin.Int = _cott_const_N.value.toInt()\n    }",
    );
    validate_candidate(&fixture.config, &fixture.plan, &callable, source.as_bytes())
        .expect("anonymous protocol adapter overrides");

    let shadowed = source.replacen(
        "override fun next():",
        "override fun next(_cott_const_N: N):",
        1,
    );
    validate_candidate(
        &fixture.config,
        &fixture.plan,
        &callable,
        shadowed.as_bytes(),
    )
    .expect_err("adapter override must not shadow a captured witness");

    let named = candidate_source(
        &fixture.plan,
        &callable,
        "class Named {\n        fun leak(): kotlin.Int = 1\n    }\n    throw IllegalStateException()",
    );
    validate_candidate(&fixture.config, &fixture.plan, &callable, named.as_bytes())
        .expect_err("named nested classes remain forbidden");
}

#[test]
fn candidate_allows_only_exactly_typed_private_helpers() {
    let fixture = fixture("module api.service\n\nfn run(value: I32) -> I32\n");
    let callable = callable(&fixture.plan, "api.service.run");
    let source = format!(
        "package cott_impl.api.service\n\n{} {{\n    return _identity(value)\n}}\n\nprivate fun _identity(value: kotlin.Int): kotlin.Int {{\n    return value\n}}\n",
        implementation_signature(&fixture.plan, &callable).expect("signature")
    );
    validate_candidate(&fixture.config, &fixture.plan, &callable, source.as_bytes())
        .expect("typed private helper");

    let untyped_return = source.replacen(
        ": kotlin.Int {\n    return value",
        " {\n    return value",
        1,
    );
    validate_candidate(
        &fixture.config,
        &fixture.plan,
        &callable,
        untyped_return.as_bytes(),
    )
    .expect_err("private helpers require an explicit return type");
}

#[test]
fn implementation_method_candidate_requires_concrete_package_and_self_type() {
    let fixture = fixture(
        r#"module api.service

trait Reader:
    fn read(self, amount: I32) -> I32

impl ReaderState for Reader:
    fn read(self, amount: I32) -> I32:
        ensures result == amount
"#,
    );
    let callable = callable(&fixture.plan, "api.service.ReaderState.read");
    let exact = candidate_source(
        &fixture.plan,
        &callable,
        "throw IllegalStateException(\"fixture\")",
    );
    validate_candidate(&fixture.config, &fixture.plan, &callable, exact.as_bytes())
        .expect("exact implementation method candidate");

    let wrong_package = exact.replacen(
        "package cott_impl.api.service.ReaderState",
        "package cott_impl.api.service",
        1,
    );
    validate_candidate(
        &fixture.config,
        &fixture.plan,
        &callable,
        wrong_package.as_bytes(),
    )
    .expect_err("an implementation method in the wrong package must fail");

    let wrong_self = exact.replacen("self: api.service.ReaderState", "self: kotlin.Any", 1);
    assert_ne!(wrong_self, exact, "fixture must alter the receiver type");
    validate_candidate(
        &fixture.config,
        &fixture.plan,
        &callable,
        wrong_self.as_bytes(),
    )
    .expect_err("an implementation method with the wrong receiver type must fail");
}

#[test]
fn candidate_rejects_visibility_suspend_and_generic_signature_drift() {
    let sync = fixture("module api.service\n\nfn run(value: I32) -> I32\n");
    let sync_callable = callable(&sync.plan, "api.service.run");
    let exact = candidate_source(
        &sync.plan,
        &sync_callable,
        "throw IllegalStateException(\"fixture\")",
    );
    let public = exact.replacen("internal fun", "fun", 1);
    validate_candidate(&sync.config, &sync.plan, &sync_callable, public.as_bytes())
        .expect_err("public implementation visibility must fail");

    let asynchronous = fixture("module api.service\n\nasync fn run(value: I32) -> I32\n");
    let async_callable = callable(&asynchronous.plan, "api.service.run");
    let exact = candidate_source(
        &asynchronous.plan,
        &async_callable,
        "throw IllegalStateException(\"fixture\")",
    );
    let not_suspend = exact.replacen("internal suspend fun", "internal fun", 1);
    validate_candidate(
        &asynchronous.config,
        &asynchronous.plan,
        &async_callable,
        not_suspend.as_bytes(),
    )
    .expect_err("a non-suspend implementation of an async callable must fail");

    let generic = fixture("module api.service\n\nfn run[T](value: T) -> T\n");
    let generic_callable = callable(&generic.plan, "api.service.run");
    let exact = candidate_source(
        &generic.plan,
        &generic_callable,
        "throw IllegalStateException(\"fixture\")",
    );
    let drifted = exact.replacen("T : kotlin.Any", "T : kotlin.String", 1);
    assert_ne!(drifted, exact, "fixture must alter the generic bound");
    validate_candidate(
        &generic.config,
        &generic.plan,
        &generic_callable,
        drifted.as_bytes(),
    )
    .expect_err("a changed generic bound must fail");
}

#[test]
fn syntax_audit_rejects_private_bypass_suppressions_top_level_code_and_templates() {
    let fixture = fixture("module api.service\n\nfn run(value: I32) -> I32\n");
    let callable = callable(&fixture.plan, "api.service.run");
    let signature = implementation_signature(&fixture.plan, &callable).expect("signature");
    let package = "cott_impl.api.service";
    let cases = [
        format!(
            "package {package}\n\nimport cott_impl.other.secret\n\n{signature} {{\n    secret()\n    throw IllegalStateException()\n}}\n"
        ),
        format!(
            "package {package}\n\n@Suppress(\"UNCHECKED_CAST\")\n{signature} {{\n    throw IllegalStateException()\n}}\n"
        ),
        format!(
            "package {package}\n\nval eager = java.lang.System.nanoTime()\n\n{signature} {{\n    throw IllegalStateException()\n}}\n"
        ),
        format!(
            "package {package}\n\n{signature} {{\n    val reflected = \"${{Class.forName(\"java.lang.String\")}}\"\n    throw IllegalStateException(reflected)\n}}\n"
        ),
        format!(
            "package {package}\n\nimport javax.script.ScriptEngineManager\n\n{signature} {{\n    ScriptEngineManager()\n    throw IllegalStateException()\n}}\n"
        ),
        format!(
            "package {package}\n\n{signature} {{\n    ProcessBuilder(\"sh\").start()\n    throw IllegalStateException()\n}}\n"
        ),
        format!(
            "package {package}\n\n{signature} {{\n    val malformed = \"${{\"\n    throw IllegalStateException(malformed)\n}}\n"
        ),
    ];
    for source in cases {
        assert!(
            validate_candidate(&fixture.config, &fixture.plan, &callable, source.as_bytes(),)
                .is_err(),
            "audit accepted forbidden source:\n{source}"
        );
    }
}

#[test]
fn audit_allows_default_and_explicit_imports_without_treating_string_text_as_code() {
    let fixture = fixture("module api.service\n\nfn run(value: I32) -> I32\n");
    let callable = callable(&fixture.plan, "api.service.run");
    let default_imports = candidate_source(
        &fixture.plan,
        &callable,
        "val endpoint = java.net.URI.create(\"Class.forName and cott_impl are inert text\")\n    val incremented = listOf(value).map(kotlin.Int::inc)\n    throw IllegalStateException(\"$endpoint: $incremented\")",
    );
    let explicit_imports = candidate_source(
        &fixture.plan,
        &callable,
        "val endpoint = URI.create(\"https://example.invalid\")\n    val incremented = valuesOf(value).map(kotlin.Int::inc)\n    throw Failure(\"$endpoint: $incremented\")",
    )
    .replacen(
        "\n\n",
        "\n\nimport java.net.URI\nimport kotlin.collections.listOf as valuesOf\nimport java.lang.IllegalStateException as Failure\n\n",
        1,
    );
    for source in [default_imports, explicit_imports] {
        validate_candidate(&fixture.config, &fixture.plan, &callable, source.as_bytes()).expect(
            "ordinary calls, imports, function references, templates, and inert text are legal",
        );
    }
}

#[test]
fn audit_rejects_process_exit_stdout_replacement_and_verifier_control_spellings() {
    let fixture = fixture("module api.service\n\nfn run(value: I32) -> I32\n");
    let callable = callable(&fixture.plan, "api.service.run");
    let candidate = |body| candidate_source(&fixture.plan, &callable, body);
    let with_imports =
        |imports: &str, body| candidate(body).replacen("\n\n", &format!("\n\n{imports}\n\n"), 1);
    let cases = [
        candidate("System.exit(0)\n    throw IllegalStateException()"),
        candidate("java.lang.System.exit(0)\n    throw IllegalStateException()"),
        candidate("java.lang.System.`exit`(0)\n    throw IllegalStateException()"),
        with_imports(
            "import java.lang.System as HostSystem",
            "HostSystem.exit(0)\n    throw IllegalStateException()",
        ),
        with_imports(
            "import java.lang.System.exit as terminate",
            "terminate(0)\n    throw IllegalStateException()",
        ),
        candidate(
            "val terminate = java.lang.System::exit\n    terminate(0)\n    throw IllegalStateException()",
        ),
        candidate("java.lang.Runtime.getRuntime().`halt`(0)\n    throw IllegalStateException()"),
        with_imports(
            "import java.lang.Runtime as JvmRuntime",
            "val halt = JvmRuntime.getRuntime()::halt\n    halt(0)\n    throw IllegalStateException()",
        ),
        candidate(
            "java.lang.System.setOut(java.io.PrintStream(java.io.ByteArrayOutputStream()))\n    throw IllegalStateException()",
        ),
        candidate(
            "System.`setOut`(java.io.PrintStream(java.io.ByteArrayOutputStream()))\n    throw IllegalStateException()",
        ),
        with_imports(
            "import java.lang.System.setOut as replaceOutput",
            "replaceOutput(java.io.PrintStream(java.io.ByteArrayOutputStream()))\n    throw IllegalStateException()",
        ),
        with_imports(
            "import java.lang.System.*",
            "exit(0)\n    throw IllegalStateException()",
        ),
        candidate(
            "val replaceOutput = java.lang.System::setOut\n    throw IllegalStateException(replaceOutput.toString())",
        ),
        candidate("java.lang.System.out.close()\n    throw IllegalStateException()"),
        candidate(
            "val leaked = java.lang.System.`in`.read()\n    throw IllegalStateException(leaked.toString())",
        ),
        candidate("java.io.FileDescriptor.out.sync()\n    throw IllegalStateException()"),
        candidate(
            "cott_runtime.CottRuntime.checkContract(true, \"api.service.run\", \"ensures\", \"ensures:0\")\n    return value",
        ),
        candidate(
            "value.checkContract(true, \"api.service.run\", \"ensures\", \"ensures:0\")\n    return value",
        ),
        candidate(
            "val recordClause = value::checkContract\n    throw IllegalStateException(recordClause.toString())",
        ),
        with_imports(
            "import cott_runtime.CottRuntime as RuntimeApi",
            "RuntimeApi.`withTestObservation`(cott_runtime.CottObservation()) { return value }\n    return value",
        ),
        with_imports(
            "import cott_runtime.CottRuntime.checkContract as recordClause",
            "recordClause(true, \"api.service.run\", \"ensures\", \"ensures:0\")\n    return value",
        ),
        with_imports(
            "import cott_runtime.CottRuntime.*",
            "checkContract(true, \"api.service.run\", \"ensures\", \"ensures:0\")\n    return value",
        ),
        candidate(
            "val recordClause = cott_runtime.CottRuntime::checkContract\n    throw IllegalStateException(recordClause.toString())",
        ),
        candidate(
            "val disabled = cott_runtime.RuntimeValidation.OFF\n    throw IllegalStateException(disabled.toString())",
        ),
        candidate(
            "val validate = cott_runtime.CottResourceContract::validateInitial\n    throw IllegalStateException(validate.toString())",
        ),
    ];
    for source in cases {
        assert!(
            validate_candidate(&fixture.config, &fixture.plan, &callable, source.as_bytes())
                .is_err(),
            "audit accepted a process or verifier-control capability:\n{source}"
        );
    }
}

#[test]
fn audit_rejects_cott_runtime_object_aliases_and_unapproved_receiver_extensions() {
    let fixture = fixture("module api.service\n\nfn run(value: I32) -> I32\n");
    let callable = callable(&fixture.plan, "api.service.run");
    let candidate = |body| candidate_source(&fixture.plan, &callable, body);
    let with_imports =
        |imports: &str, body| candidate(body).replacen("\n\n", &format!("\n\n{imports}\n\n"), 1);
    let returned = candidate("return value").replacen(
        "\n\n",
        "\n\nprivate fun _runtime(): kotlin.Any = cott_runtime.CottRuntime\n\n",
        1,
    );
    let receiver_extension = candidate(
        "val runtime = cott_runtime.CottRuntime._identity()\n    runtime.checkContract(true, \"api.service.run\", \"ensures\", \"ensures:0\")\n    return value",
    )
    .replacen(
        "\n\n",
        "\n\nprivate fun <T> T._identity(): T = this\n\n",
        1,
    );
    let cases = [
        candidate(
            "val runtime = cott_runtime.CottRuntime\n    runtime.checkContract(true, \"api.service.run\", \"ensures\", \"ensures:0\")\n    return value",
        ),
        candidate(
            "val runtime = cott_runtime.`CottRuntime`\n    runtime.checkContract(true, \"api.service.run\", \"ensures\", \"ensures:0\")\n    return value",
        ),
        with_imports(
            "import cott_runtime.CottRuntime",
            "val runtime = CottRuntime\n    runtime.checkContract(true, \"api.service.run\", \"ensures\", \"ensures:0\")\n    return value",
        ),
        with_imports(
            "import cott_runtime.`CottRuntime` as RuntimeApi",
            "val runtime = RuntimeApi\n    runtime.checkContract(true, \"api.service.run\", \"ensures\", \"ensures:0\")\n    return value",
        ),
        candidate(
            "val runtimes = listOf(cott_runtime.CottRuntime)\n    runtimes.single().checkContract(true, \"api.service.run\", \"ensures\", \"ensures:0\")\n    return value",
        ),
        candidate(
            "with(cott_runtime.CottRuntime) { checkContract(true, \"api.service.run\", \"ensures\", \"ensures:0\") }\n    return value",
        ),
        candidate(
            "cott_runtime.CottRuntime.run { checkContract(true, \"api.service.run\", \"ensures\", \"ensures:0\") }\n    return value",
        ),
        returned,
        receiver_extension,
    ];
    for source in cases {
        assert!(
            validate_candidate(&fixture.config, &fixture.plan, &callable, source.as_bytes())
                .is_err(),
            "audit accepted a CottRuntime receiver escape:\n{source}"
        );
    }
}

#[test]
fn audit_rejects_imports_that_shadow_approved_cott_runtime_members() {
    let fixture = fixture("module api.service\n\nfn run(value: I32) -> I32\n");
    let callable = callable(&fixture.plan, "api.service.run");
    let candidate = |import: &str, body: &str| {
        candidate_source(&fixture.plan, &callable, body).replacen(
            "\n\n",
            &format!("\n\n{import}\n\n"),
            1,
        )
    };
    for source in [
        candidate(
            "import kotlin.also as intAdd",
            "cott_runtime.CottRuntime.intAdd { it.checkContract(true, \"api.service.run\", \"ensures\", \"ensures:0\") }\n    return value",
        ),
        candidate(
            "import kotlin.let as snapshotList",
            "cott_runtime.CottRuntime.snapshotList { runtime -> runtime.checkContract(true, \"api.service.run\", \"ensures\", \"ensures:0\") }\n    return value",
        ),
    ] {
        let error =
            validate_candidate(&fixture.config, &fixture.plan, &callable, source.as_bytes())
                .expect_err("a safe runtime member name must not select an imported extension");
        assert!(
            error.contains("shadows approved CottRuntime member"),
            "unexpected shadowing diagnostic: {error}"
        );
    }
}

#[test]
fn audit_preserves_logging_and_runtime_value_and_mathematical_apis() {
    let fixture = fixture("module api.service\n\nfn run(value: I32) -> I32\n");
    let callable = callable(&fixture.plan, "api.service.run");
    let direct = candidate_source(
        &fixture.plan,
        &callable,
        "val exact = java.math.BigInteger.valueOf(value.toLong())\n    val sum = cott_runtime.CottRuntime.intAdd(exact, java.math.BigInteger.ONE)\n    val json = cott_runtime.JsonInteger(sum)\n    val values = cott_runtime.CottRuntime.snapshotList(listOf(json))\n    java.lang.System.out.println(values)\n    return value",
    );
    let imported = direct
        .replacen(
            "\n\n",
            "\n\nimport cott_runtime.CottRuntime as RuntimeApi\n\n",
            1,
        )
        .replace("cott_runtime.CottRuntime.intAdd", "RuntimeApi.`intAdd`")
        .replace(
            "cott_runtime.CottRuntime.snapshotList",
            "RuntimeApi.snapshotList",
        );
    let member_imported = direct
        .replace("cott_runtime.CottRuntime.intAdd", "intAdd")
        .replace("cott_runtime.CottRuntime.snapshotList", "snapshotList")
        .replacen(
            "\n\n",
            "\n\nimport cott_runtime.CottRuntime.intAdd\nimport cott_runtime.CottRuntime.snapshotList\n\n",
            1,
        );
    for source in [direct, imported, member_imported] {
        validate_candidate(&fixture.config, &fixture.plan, &callable, source.as_bytes())
            .expect("normal logging and direct approved Kotlin runtime APIs remain legal");
    }
}

#[test]
fn audit_rejects_unqualified_calls_and_references_to_other_known_agent_targets() {
    let fixture =
        fixture("module api.service\n\nfn run(value: I32) -> I32\nfn hidden(value: I32) -> I32\n");
    let callable = callable(&fixture.plan, "api.service.run");
    for body in [
        "return hidden(value)",
        "val hiddenReference = ::hidden\n    return hiddenReference(value)",
    ] {
        let source = candidate_source(&fixture.plan, &callable, body);
        validate_candidate(&fixture.config, &fixture.plan, &callable, source.as_bytes())
            .expect_err("a known unresolved implementation target must not bypass the facade");
    }
}

#[test]
fn resolves_renamed_manifest_fqn_with_truthful_origins_and_identity() {
    let mut fixture = fixture("module api.service\n\nfn run(value: I32) -> I32\n");
    fixture.config.kotlin.implementations.insert(
        "api.service.run".to_owned(),
        "bindings.service.sum".to_owned(),
    );
    let callable = callable(&fixture.plan, "api.service.run");
    let signature = implementation_signature(&fixture.plan, &callable).expect("signature");
    let renamed = signature.replacen("run(", "sum(", 1);
    assert_ne!(
        renamed, signature,
        "fixture must rename the implementation function"
    );
    let source = format!(
        "package bindings.service\n\n{renamed} {{\n    throw IllegalStateException(\"fixture\")\n}}\n"
    );
    write_source(
        &fixture.paths.kotlin_source_dir.join("bindings/service.kt"),
        &source,
    );

    let bindings = resolve(&fixture.config, &fixture.paths, &fixture.plan, None)
        .expect("manifest Kotlin implementation resolves");
    assert_eq!(bindings.len(), 1);
    assert_eq!(bindings[0].cott_symbol, "api.service.run");
    assert_eq!(bindings[0].target_symbol, "bindings.service.sum");
    assert_eq!(
        bindings[0].source_origin,
        Path::new("kotlin/bindings/service.kt")
    );
    assert_eq!(
        bindings[0].runtime_origin,
        Path::new("kotlin/cott_impl/api/service/run.kt")
    );
    assert_eq!(bindings[0].owner, KotlinOwner::Manifest);
    assert_eq!(
        bindings[0].content_hash,
        format!("sha256:{}", sha256_hex(source.as_bytes()))
    );
}

#[test]
fn manifest_resolution_rejects_duplicate_declarations_and_incompatible_signature() {
    let mut fixture = fixture("module api.service\n\nfn run(value: I32) -> I32\n");
    fixture.config.kotlin.implementations.insert(
        "api.service.run".to_owned(),
        "bindings.service.run".to_owned(),
    );
    let callable = callable(&fixture.plan, "api.service.run");
    let exact = format!(
        "package bindings.service\n\n{} {{\n    throw IllegalStateException(\"fixture\")\n}}\n",
        implementation_signature(&fixture.plan, &callable).expect("signature")
    );
    let first = fixture.paths.kotlin_source_dir.join("bindings/first.kt");
    let second = fixture.paths.kotlin_source_dir.join("bindings/second.kt");
    write_source(&first, &exact);
    write_source(&second, &exact);
    resolve(&fixture.config, &fixture.paths, &fixture.plan, None)
        .expect_err("duplicate implementation declarations must fail");

    fs::remove_file(&second).expect("remove duplicate");
    fs::write(&first, exact.replacen("internal fun", "fun", 1))
        .expect("write incompatible signature");
    resolve(&fixture.config, &fixture.paths, &fixture.plan, None)
        .expect_err("manifest implementation signature drift must fail");
}

#[test]
fn durable_agent_source_requires_matching_recorded_content_identity() {
    let fixture = fixture("module api.service\n\nfn run(value: I32) -> I32\n");
    let callable = callable(&fixture.plan, "api.service.run");
    let source = candidate_source(
        &fixture.plan,
        &callable,
        "throw IllegalStateException(\"fixture\")",
    );
    let path = fixture
        .paths
        .kotlin_source_dir
        .join("cott_impl/api/service/run.kt");
    write_source(&path, &source);

    resolve(&fixture.config, &fixture.paths, &fixture.plan, None)
        .expect_err("unrecorded durable source must fail");

    write_agent_record(
        &fixture,
        &callable,
        &path,
        source.as_bytes(),
        &fixture.plan,
        Vec::new(),
        None,
    );
    let bindings = resolve(&fixture.config, &fixture.paths, &fixture.plan, None)
        .expect("recorded durable source resolves");
    assert_eq!(bindings.len(), 1);
    assert_eq!(bindings[0].owner, KotlinOwner::Agent);

    fs::write(&path, format!("{source}// tampered\n")).expect("tampered source");
    resolve(&fixture.config, &fixture.paths, &fixture.plan, None)
        .expect_err("tampered durable source must fail before execution");
}

#[test]
fn missing_and_intent_stale_authenticated_agent_sources_remain_unresolved() {
    let fixture =
        fixture("module api.service\n\nfn run(value: I32) -> I32:\n    ensures result > 0\n");
    let callable = callable(&fixture.plan, "api.service.run");
    let source = candidate_source(
        &fixture.plan,
        &callable,
        "throw IllegalStateException(\"fixture\")",
    );
    let path = fixture
        .paths
        .kotlin_source_dir
        .join("cott_impl/api/service/run.kt");
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

    let changed = plan(
        &fixture.paths.source_dir,
        "module api.service\n\nfn run(value: I32) -> I32:\n    ensures result > 1\n",
    );
    let bindings = resolve(&fixture.config, &fixture.paths, &changed, None)
        .expect("intent-stale authenticated source is unresolved, not fatal");
    assert!(bindings.is_empty());

    fs::remove_file(&path).expect("remove durable source");
    let bindings = resolve(&fixture.config, &fixture.paths, &fixture.plan, None)
        .expect("missing durable source is unresolved");
    assert!(bindings.is_empty());
}

#[test]
fn generator_rules_only_changes_require_agent_regeneration() {
    let mut fixture = fixture("module api.service\n\nfn run(value: I32) -> I32\n");
    fs::write(
        &fixture.paths.manifest,
        format!("{MANIFEST}\n[generator]\nrules = \"GENERATOR_RULES.txt\"\n"),
    )
    .expect("manifest with generator rules");
    fixture.config.generator.rules = Some("GENERATOR_RULES.txt".to_owned());
    let original_rules = "cott-domain api.service.run return: preserve the value\n";
    let revised_rules = "cott-domain api.service.run return: increment the value\n";
    let rules_path = fixture.paths.root.join("GENERATOR_RULES.txt");
    fs::write(&rules_path, original_rules).expect("original generator rules");

    let callable = callable(&fixture.plan, "api.service.run");
    let source = candidate_source(&fixture.plan, &callable, "return value");
    let path = fixture
        .paths
        .kotlin_source_dir
        .join("cott_impl/api/service/run.kt");
    write_source(&path, &source);
    write_agent_record(
        &fixture,
        &callable,
        &path,
        source.as_bytes(),
        &fixture.plan,
        Vec::new(),
        Some(original_rules),
    );

    let bindings = resolve(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        Some(original_rules),
    )
    .expect("unchanged frozen rules retain the authenticated binding");
    assert_eq!(bindings.len(), 1);

    fs::write(&rules_path, revised_rules).expect("revised generator rules");
    let bindings = resolve(
        &fixture.config,
        &fixture.paths,
        &fixture.plan,
        Some(revised_rules),
    )
    .expect("revised frozen rules make the authenticated binding stale");
    assert!(
        bindings.is_empty(),
        "rules-only intent changes must require regeneration"
    );
}

#[test]
fn unresolved_record_takes_precedence_over_retained_accepted_implementation() {
    let fixture = fixture("module api.service\n\nfn run(value: I32) -> I32\n");
    let callable = callable(&fixture.plan, "api.service.run");
    let source = candidate_source(
        &fixture.plan,
        &callable,
        "throw IllegalStateException(\"fixture\")",
    );
    let path = fixture
        .paths
        .kotlin_source_dir
        .join("cott_impl/api/service/run.kt");
    write_source(&path, &source);
    write_agent_record(
        &fixture,
        &callable,
        &path,
        source.as_bytes(),
        &fixture.plan,
        vec![callable.symbol.clone()],
        None,
    );

    let bindings = resolve(&fixture.config, &fixture.paths, &fixture.plan, None)
        .expect("authenticated pending implementation remains unresolved");
    assert!(bindings.is_empty());

    let record_path = fixture.paths.artifact_root.join("generation.json");
    let mut moved =
        KotlinGenerationRecord::parse(&fs::read(&record_path).expect("pending Kotlin record"))
            .expect("parse pending Kotlin record");
    moved.current.implementations[0].source_origin =
        "kotlin/cott_impl/api/service/moved.kt".to_owned();
    moved
        .current
        .compute_generation_id()
        .expect("moved pending identity");
    fs::write(
        &record_path,
        moved.canonical_bytes().expect("moved pending record"),
    )
    .expect("write moved pending record");
    resolve(&fixture.config, &fixture.paths, &fixture.plan, None)
        .expect_err("pending source must match its recorded path identity");

    write_agent_record(
        &fixture,
        &callable,
        &path,
        source.as_bytes(),
        &fixture.plan,
        vec![callable.symbol.clone()],
        None,
    );

    fs::write(&path, format!("{source}// unauthenticated change\n"))
        .expect("tamper pending source");
    resolve(&fixture.config, &fixture.paths, &fixture.plan, None)
        .expect_err("pending status must not hide content tampering");
}

#[test]
fn same_project_version_change_preserves_authenticated_agent_ownership() {
    let fixture = fixture("module api.service\n\nfn run(value: I32) -> I32\n");
    let callable = callable(&fixture.plan, "api.service.run");
    let source = candidate_source(
        &fixture.plan,
        &callable,
        "throw IllegalStateException(\"fixture\")",
    );
    let path = fixture
        .paths
        .kotlin_source_dir
        .join("cott_impl/api/service/run.kt");
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
        MANIFEST.replace("version = \"0.1.0\"", "version = \"0.2.0\""),
    )
    .expect("version-bumped manifest");
    let (config, paths, _) =
        load_kotlin_config_with_paths(&fixture.paths.root).expect("version-bumped Kotlin project");
    let bindings = resolve(&config, &paths, &fixture.plan, None)
        .expect("same named project retains authenticated ownership across API versions");
    assert_eq!(
        bindings
            .iter()
            .map(|binding| binding.cott_symbol.as_str())
            .collect::<Vec<_>>(),
        ["api.service.run"]
    );
}

#[test]
fn authenticated_source_for_removed_declaration_is_ignored_but_still_hash_checked() {
    let fixture = fixture("module api.service\n\nfn obsolete(value: I32) -> I32\n");
    let callable = callable(&fixture.plan, "api.service.obsolete");
    let source = candidate_source(
        &fixture.plan,
        &callable,
        "throw IllegalStateException(\"fixture\")",
    );
    let path = fixture
        .paths
        .kotlin_source_dir
        .join("cott_impl/api/service/obsolete.kt");
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

    let current = plan(
        &fixture.paths.source_dir,
        "module api.service\n\nconst answer: I32 = 42\n",
    );
    let bindings = resolve(&fixture.config, &fixture.paths, &current, None)
        .expect("authenticated removed declaration source does not block current facade");
    assert!(
        bindings.is_empty(),
        "removed declaration must not be exported"
    );
    assert!(
        path.exists(),
        "resolver must not auto-delete retired source"
    );

    fs::write(&path, format!("{source}// tampered retired source\n"))
        .expect("tamper retired source");
    resolve(&fixture.config, &fixture.paths, &current, None)
        .expect_err("tampered retired source must still fail ownership validation");
}

#[test]
fn project_source_cannot_import_private_agent_implementation() {
    let fixture = fixture("module api.service\n\nfn run(value: I32) -> I32\n");
    for source in [
        "package consumer\n\nimport cott_impl.api.service.run\n\nfun call(): kotlin.Int = run(1)\n",
        "package consumer\n\nimport cott_impl.api.service.run as privateRun\n\nfun call(): kotlin.Int = privateRun(1)\n",
        "package consumer\n\nimport cott_impl.api.service.*;\n\nfun call(): kotlin.Int = run(1)\n",
    ] {
        write_source(&fixture.paths.kotlin_source_dir.join("consumer.kt"), source);
        assert!(
            resolve(&fixture.config, &fixture.paths, &fixture.plan, None).is_err(),
            "private facade bypass import and call were accepted:\n{source}"
        );
    }
}

#[cfg(unix)]
#[test]
fn source_links_fail_with_their_unsafe_path() {
    use std::os::unix::fs::symlink;

    let fixture = fixture("module api.service\n\nfn run(value: I32) -> I32\n");
    let outside = fixture.paths.root.join("outside.kt");
    fs::write(&outside, "package outside\n").expect("outside source");
    let linked = fixture.paths.kotlin_source_dir.join("linked.kt");
    symlink(&outside, &linked).expect("source symlink");
    resolve(&fixture.config, &fixture.paths, &fixture.plan, None)
        .expect_err("linked Kotlin source must fail");
}
