use std::collections::{BTreeMap, BTreeSet};
use std::ffi::CString;
use std::fs::{self, DirBuilder, File, OpenOptions};
use std::io::{Read as _, Write as _};
use std::os::unix::ffi::OsStrExt;
use std::os::unix::fs::{DirBuilderExt, MetadataExt, OpenOptionsExt, PermissionsExt};
use std::path::{Component, Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use serde::Serialize;
use serde_json::{Value, json};

use crate::cli::OutputFormat;
use crate::compiler::{ProjectDiagnostic, SourceFile, parse_project};
use crate::hash::sha256_hex;
use crate::hir::lower_with_effects;
use crate::ir::render;
use crate::manifest::{ApiVersion, KotlinProjectConfig, parse_api_version};
use crate::project::{
    KotlinPaths, discover_kotlin_contract_sources, discover_kotlin_sources,
    load_kotlin_config_with_paths,
};
use crate::provenance::{AgentRun, SemanticCoverage};
use crate::transaction::{ChangeSet, InputSnapshot, Operation, ProjectSession};

use super::binding::{agent_source_origin, requires_binding, resolve};
use super::emit;
use super::provenance::{
    KOTLIN_GENERATION_SCHEMA_VERSION, KOTLIN_RUNTIME_ABI_VERSION, KotlinBindingRecord,
    KotlinGenerationRecord, KotlinGenerationSnapshot,
};
use super::verify::{self as kotlin_verify, Verification};
use super::{KotlinBinding, KotlinEmission, KotlinOwner, KotlinPlan};

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct Failure {
    pub code: i32,
    pub message: String,
}

impl Failure {
    pub(crate) fn new(code: i32, message: impl Into<String>) -> Self {
        Self {
            code,
            message: message.into(),
        }
    }
}

pub(crate) struct Project {
    pub session: ProjectSession,
    pub config: KotlinProjectConfig,
    pub paths: KotlinPaths,
    pub plan: KotlinPlan,
    pub generator_rules: Option<String>,
    pub bindings: Vec<KotlinBinding>,
    pub baseline: Option<KotlinGenerationRecord>,
    pub generation_bytes: Option<Vec<u8>>,
    pub input_snapshot: InputSnapshot,
    pub inputs: BTreeMap<String, String>,
}

pub(crate) fn load(project: Option<PathBuf>, inspection: bool) -> Result<Project, Failure> {
    let root = project_root(project)?;
    let session = if inspection {
        ProjectSession::acquire_for_inspection(&root)
    } else {
        ProjectSession::acquire(&root)
    }
    .map_err(|error| Failure::new(6, error.to_string()))?;
    let (config, paths, manifest_source) = load_kotlin_config_with_paths(session.root())
        .map_err(|error| Failure::new(2, error.to_string()))?;
    let generator_rules = load_generator_rules(&config, &paths)?;

    let contract_sources = discover_kotlin_contract_sources(&paths)
        .map_err(|error| Failure::new(2, error.to_string()))?;
    let parsed = parse_project(contract_sources.clone())
        .map_err(|diagnostics| Failure::new(3, render_diagnostics(&diagnostics)))?;
    let effects = config.effects.keys().cloned().collect::<BTreeSet<_>>();
    let hir = lower_with_effects(&paths.source_dir, parsed, &effects)
        .map_err(|diagnostics| Failure::new(3, render_diagnostics(&diagnostics)))?;
    let ir = render(&hir).map_err(|message| Failure::new(3, message))?;
    let plan = KotlinPlan::from_ir(&ir).map_err(|message| Failure::new(3, message))?;

    let generation = generation_relative(&paths)?;
    let (baseline, baseline_bytes, baseline_identity) = match read_generation_record(&paths)? {
        Some((record, leaf)) => (
            Some(record),
            Some(leaf.bytes),
            Some((leaf.device, leaf.inode)),
        ),
        None => (None, None, None),
    };
    let generation_snapshot = match &baseline_bytes {
        Some(bytes) => InputSnapshot::capture_expected(
            &paths.root,
            [(generation.clone(), digest(bytes))],
            std::iter::empty(),
        ),
        None => InputSnapshot::capture(&paths.root, [generation.clone()]),
    }
    .map_err(|error| Failure::new(6, error.to_string()))?;
    let generation_leaf = paths.root.join(&generation);
    match (baseline_identity, fs::symlink_metadata(&generation_leaf)) {
        (Some((device, inode)), Ok(metadata))
            if metadata.is_file()
                && !metadata.file_type().is_symlink()
                && metadata.nlink() == 1
                && metadata.dev() == device
                && metadata.ino() == inode => {}
        (None, Err(error)) if error.kind() == std::io::ErrorKind::NotFound => {}
        (_, Err(error)) => {
            return Err(Failure::new(
                6,
                format!(
                    "re-inspect Kotlin generation record {}: {error}",
                    generation_leaf.display()
                ),
            ));
        }
        _ => {
            return Err(Failure::new(
                6,
                format!(
                    "Kotlin generation record changed while establishing its input snapshot: {}",
                    generation_leaf.display()
                ),
            ));
        }
    }
    let bindings = resolve(&config, &paths, &plan, generator_rules.as_deref())
        .map_err(|message| Failure::new(4, message))?;
    let mut inputs = collect_inputs(
        &config,
        &paths,
        &manifest_source,
        &contract_sources,
        generator_rules.as_deref(),
    )?;
    for binding in &bindings {
        insert_binding_input(&paths, binding, &mut inputs, false)?;
    }

    let authored = discover_kotlin_sources(&paths.kotlin_source_dir)
        .map_err(|error| Failure::new(4, error.to_string()))?;
    for source in authored {
        let relative = project_relative(&paths.root, &source.disk_path)?;
        insert_consumed_input(
            &mut inputs,
            path_text(&relative)?,
            digest(source.source.as_bytes()),
            "Kotlin source",
        )?;
    }

    let mut extra = Vec::new();
    for callable in plan.callables() {
        if config.kotlin.implementations.contains_key(&callable.symbol)
            || !requires_binding(&callable)
        {
            continue;
        }
        extra.push(
            agent_source_origin(&paths, &callable).map_err(|message| Failure::new(4, message))?,
        );
    }
    let expected = inputs
        .iter()
        .map(|(path, hash)| (PathBuf::from(path), hash.clone()))
        .collect::<Vec<_>>();
    let actual_artifacts = collect_tree_if_present(&paths.artifact_root)
        .map_err(|message| Failure::new(4, message))?;
    match (
        baseline_bytes.as_ref(),
        actual_artifacts.get(Path::new("generation.json")),
    ) {
        (Some(consumed), Some(discovered)) if consumed == discovered => {}
        (None, None) => {}
        _ => {
            return Err(Failure::new(
                6,
                "Kotlin generation record changed while loading the project",
            ));
        }
    }
    let artifact_prefix = artifact_prefix(&paths)?;
    extra.extend(
        actual_artifacts
            .keys()
            .filter(|path| path.as_path() != Path::new("generation.json"))
            .map(|path| artifact_prefix.join(path)),
    );
    let mut input_snapshot = InputSnapshot::capture_expected(&paths.root, expected, extra)
        .map_err(|error| Failure::new(6, error.to_string()))?;
    input_snapshot.merge_missing(generation_snapshot);

    Ok(Project {
        session,
        config,
        paths,
        plan,
        generator_rules,
        bindings,
        baseline,
        generation_bytes: baseline_bytes,
        input_snapshot,
        inputs,
    })
}

pub(crate) fn publish(
    project: &Project,
    bindings: &[KotlinBinding],
    agent_runs: &[AgentRun],
    pending: &BTreeSet<String>,
    verification: Option<&Verification>,
    ir_only: bool,
) -> Result<(), Failure> {
    validate_binding_set(project, bindings, pending, agent_runs)?;
    if verification.is_some() && (ir_only || !pending.is_empty()) {
        return Err(Failure::new(
            4,
            "Kotlin verification cannot certify an IR-only or pending publication",
        ));
    }

    let resolved = bindings
        .iter()
        .filter(|binding| !pending.contains(&binding.cott_symbol))
        .cloned()
        .collect::<Vec<_>>();
    let emission = emit::emit(&project.config, &project.plan, &resolved)
        .map_err(|message| Failure::new(4, message))?;
    let emitted_pending = emission.unresolved.iter().cloned().collect::<BTreeSet<_>>();
    if emitted_pending != *pending {
        return Err(Failure::new(
            4,
            "Kotlin pending set does not match unresolved emitted callables",
        ));
    }
    let actual = collect_tree_if_present(&project.paths.artifact_root)
        .map_err(|message| Failure::new(4, message))?;
    let prefix = artifact_prefix(&project.paths)?;
    let owned = validate_owned_artifacts(project, &actual)?;

    let mut desired = if ir_only {
        emission
            .files
            .iter()
            .filter(|(path, _)| path.starts_with("ir"))
            .map(|(path, bytes)| (path.clone(), bytes.clone()))
            .collect::<BTreeMap<_, _>>()
    } else {
        emission.files.clone()
    };
    if let Some(verification) = verification {
        for (path, bytes) in &verification.artifacts {
            if !safe_relative(path) {
                return Err(Failure::new(
                    4,
                    format!(
                        "Kotlin verifier returned unsafe artifact path {}",
                        path.display()
                    ),
                ));
            }
            if desired.insert(path.clone(), bytes.clone()).is_some() {
                return Err(Failure::new(
                    4,
                    format!(
                        "Kotlin verifier artifact collides with emitted output {}",
                        path.display()
                    ),
                ));
            }
        }
    }

    for path in desired.keys() {
        if actual.contains_key(path) && !owned.contains(path) {
            return Err(Failure::new(
                4,
                format!(
                    "refusing to overwrite unowned Kotlin artifact {}",
                    prefix.join(path).display()
                ),
            ));
        }
    }
    for path in actual.keys() {
        if path == Path::new("generation.json") {
            continue;
        }
        if !owned.contains(path) && !desired.contains_key(path) {
            return Err(Failure::new(
                4,
                format!(
                    "unexpected unowned Kotlin artifact {}",
                    prefix.join(path).display()
                ),
            ));
        }
    }

    let mut managed = BTreeMap::new();
    if ir_only {
        for (path, bytes) in &actual {
            if path == Path::new("generation.json") || path.starts_with("ir") {
                continue;
            }
            if owned.contains(path) {
                managed.insert(path_text(&prefix.join(path))?, digest(bytes));
            }
        }
    }
    for (path, bytes) in &desired {
        managed.insert(path_text(&prefix.join(path))?, digest(bytes));
    }

    let (mut record, mut source_writes) = build_record(
        project,
        bindings,
        agent_runs,
        pending,
        verification,
        managed,
        &emission,
    )?;
    if ir_only {
        carry_trusted_ir_state(project, &mut record)?;
        source_writes.clear();
    }
    let generation_bytes = record
        .canonical_bytes()
        .map_err(|message| Failure::new(4, message))?;

    let mut output_paths = actual
        .keys()
        .map(|path| prefix.join(path))
        .collect::<Vec<_>>();
    output_paths.extend(desired.keys().map(|path| prefix.join(path)));
    output_paths.extend(source_writes.iter().map(|(path, _)| path.clone()));
    output_paths.push(prefix.join("generation.json"));
    output_paths.sort();
    output_paths.dedup();
    let output_snapshot = InputSnapshot::capture(&project.paths.root, output_paths)
        .map_err(|error| Failure::new(6, error.to_string()))?;
    let rechecked_artifacts = collect_tree_if_present(&project.paths.artifact_root)
        .map_err(|message| Failure::new(4, message))?;
    if rechecked_artifacts != actual {
        return Err(Failure::new(
            6,
            "Kotlin managed outputs changed while planning publication",
        ));
    }
    let mut snapshot = project.input_snapshot.clone();
    snapshot.merge_missing(output_snapshot);

    let mut changes = ChangeSet::default();
    for (path, bytes) in &source_writes {
        if fs::read(project.paths.root.join(path)).ok().as_deref() != Some(bytes) {
            changes.operations.push(Operation::Write {
                path: path.clone(),
                bytes: bytes.clone(),
            });
        }
    }
    for (path, bytes) in &desired {
        if actual.get(path) != Some(bytes) {
            changes.operations.push(Operation::Write {
                path: prefix.join(path),
                bytes: bytes.clone(),
            });
        }
    }
    for path in &owned {
        let remove = if ir_only {
            path.starts_with("ir") && !desired.contains_key(path)
        } else {
            !desired.contains_key(path)
        };
        if remove {
            changes.operations.push(Operation::Remove {
                path: prefix.join(path),
            });
        }
    }
    if actual.get(Path::new("generation.json")) != Some(&generation_bytes) {
        changes.operations.push(Operation::Write {
            path: prefix.join("generation.json"),
            bytes: generation_bytes,
        });
    }
    changes.generation_record_last = true;
    project
        .session
        .apply(&snapshot, &changes)
        .map_err(|error| Failure::new(6, error.to_string()))?;
    if let Some(verification) = verification
        && !verification.coverage.policy.passed
    {
        return Err(coverage_failure(&verification.coverage));
    }
    Ok(())
}

pub(crate) fn check(project: Option<PathBuf>, source: Option<PathBuf>) -> Result<(), Failure> {
    let loaded = load(project, false)?;
    if let Some(source) = source {
        let relative = crate::manifest::normalized_relative_path(
            source
                .to_str()
                .ok_or_else(|| Failure::new(2, "check source path is not UTF-8"))?,
        )
        .map_err(|message| Failure::new(2, format!("invalid check source: {message}")))?;
        let absolute = loaded.paths.root.join(&relative);
        let metadata = fs::symlink_metadata(&absolute).map_err(|error| {
            Failure::new(
                2,
                format!("inspect check source {}: {error}", relative.display()),
            )
        })?;
        if !absolute.starts_with(&loaded.paths.source_dir)
            || absolute.extension().and_then(|value| value.to_str()) != Some("cott")
            || metadata.file_type().is_symlink()
            || !metadata.is_file()
            || metadata.nlink() != 1
        {
            return Err(Failure::new(
                2,
                "check source must be a regular single-link .cott file beneath project.source",
            ));
        }
    }
    emit::emit(&loaded.config, &loaded.plan, &loaded.bindings)
        .map_err(|message| Failure::new(4, message))?;
    Ok(())
}

pub(crate) fn format(project: Option<PathBuf>, check: bool) -> Result<(), Failure> {
    let loaded = load(project, false)?;
    let sources = discover_kotlin_contract_sources(&loaded.paths)
        .map_err(|error| Failure::new(2, error.to_string()))?;
    let parsed = parse_project(sources)
        .map_err(|diagnostics| Failure::new(3, render_diagnostics(&diagnostics)))?;
    let mut writes = Vec::new();
    for source in parsed.sources {
        let bytes =
            crate::formatter::format(&source.cst, &source.syntax).map_err(|diagnostic| {
                Failure::new(
                    3,
                    render_diagnostics(&[ProjectDiagnostic {
                        path: source.path.clone(),
                        diagnostic,
                    }]),
                )
            })?;
        let relative = project_relative(
            &loaded.paths.root,
            &loaded.paths.source_dir.join(&source.path),
        )?;
        let current = fs::read(loaded.paths.root.join(&relative)).map_err(|error| {
            Failure::new(2, format!("read source {}: {error}", relative.display()))
        })?;
        if current != bytes {
            writes.push((relative, bytes));
        }
    }
    if check && !writes.is_empty() {
        return Err(Failure::new(8, "Cott source formatting differs"));
    }
    if check || writes.is_empty() {
        return Ok(());
    }

    let mut snapshot = loaded.input_snapshot.clone();
    let mut changes = ChangeSet::default();
    let mut replacement_hashes = BTreeMap::new();
    for (path, bytes) in writes {
        replacement_hashes.insert(path_text(&path)?, digest(&bytes));
        changes.operations.push(Operation::Write { path, bytes });
    }
    if let Some(mut record) = loaded.baseline.clone() {
        for (path, hash) in replacement_hashes {
            record.current.inputs.insert(path, hash);
        }
        record.current.verified = false;
        record.current.verification = Value::Null;
        record.current.semantic_coverage = SemanticCoverage::default();
        record
            .current
            .compute_generation_id()
            .map_err(|message| Failure::new(4, message))?;
        let bytes = record
            .canonical_bytes()
            .map_err(|message| Failure::new(4, message))?;
        let generation = generation_relative(&loaded.paths)?;
        let output = InputSnapshot::capture(&loaded.paths.root, [generation.clone()])
            .map_err(|error| Failure::new(6, error.to_string()))?;
        snapshot.merge_missing(output);
        changes.operations.push(Operation::Write {
            path: generation,
            bytes,
        });
        changes.generation_record_last = true;
    }
    loaded
        .session
        .apply(&snapshot, &changes)
        .map_err(|error| Failure::new(6, error.to_string()))
}

pub(crate) fn emit(project: Option<PathBuf>, ir_only: bool) -> Result<PathBuf, Failure> {
    let loaded = load(project, false)?;
    let planned = emit::emit(&loaded.config, &loaded.plan, &loaded.bindings)
        .map_err(|message| Failure::new(4, message))?;
    let pending = planned.unresolved.into_iter().collect::<BTreeSet<_>>();
    publish(&loaded, &loaded.bindings, &[], &pending, None, ir_only)?;
    Ok(if ir_only {
        loaded.paths.artifact_root.join("ir")
    } else {
        loaded.paths.generated_dir.clone()
    })
}

pub(crate) fn verify(project: Option<PathBuf>) -> Result<PathBuf, Failure> {
    let loaded = load(project, false)?;
    let emission = emit::emit(&loaded.config, &loaded.plan, &loaded.bindings)
        .map_err(|message| Failure::new(4, message))?;
    if !emission.unresolved.is_empty() {
        return Err(Failure::new(
            4,
            format!(
                "unresolved Kotlin implementations: {}",
                emission.unresolved.join(", ")
            ),
        ));
    }
    validate_current_publication(&loaded, &emission)?;
    let verification =
        kotlin_verify::verify(&loaded.config, &loaded.paths, &loaded.plan, &emission)
            .map_err(|message| Failure::new(4, message))?;
    publish(
        &loaded,
        &loaded.bindings,
        &[],
        &BTreeSet::new(),
        Some(&verification),
        false,
    )?;
    Ok(loaded.paths.artifact_root.join("library/cott-module.jar"))
}
fn coverage_failure(coverage: &SemanticCoverage) -> Failure {
    let violations = coverage
        .policy
        .violations
        .iter()
        .map(|violation| {
            format!(
                "{}:{}:{}-{}: {}",
                violation.symbol,
                violation.clause_id,
                violation.span.start_byte,
                violation.span.end_byte,
                violation.reason
            )
        })
        .collect::<Vec<_>>()
        .join("; ");
    Failure::new(8, format!("semantic coverage policy failed: {violations}"))
}

pub(crate) fn diff(
    project: Option<PathBuf>,
    baseline: Option<PathBuf>,
    exit_code: bool,
    format: OutputFormat,
) -> i32 {
    match diff_inner(project, baseline) {
        Ok(report) => {
            match format {
                OutputFormat::Human => print_diff(&report),
                OutputFormat::Json => match serde_json::to_writer(std::io::stdout(), &report) {
                    Ok(()) => println!(),
                    Err(error) => {
                        eprintln!("error: serialize Kotlin diff report: {error}");
                        return 6;
                    }
                },
            }
            if exit_code && (report.breaking || !report.version_compatible) {
                7
            } else {
                0
            }
        }
        Err(error) => {
            eprintln!("error: {}", error.message);
            error.code
        }
    }
}

pub(crate) fn deploy(
    project: Option<PathBuf>,
    output: Option<PathBuf>,
) -> Result<PathBuf, Failure> {
    let loaded = load(project, false)?;
    let emission = emit::emit(&loaded.config, &loaded.plan, &loaded.bindings)
        .map_err(|message| Failure::new(4, message))?;
    if !emission.unresolved.is_empty() {
        return Err(Failure::new(
            4,
            "deployment refuses unresolved Kotlin implementations",
        ));
    }
    validate_current_publication(&loaded, &emission)?;
    let record = loaded
        .baseline
        .as_ref()
        .ok_or_else(|| Failure::new(4, "deployment requires generation.json"))?;
    if !record.current.verified || record.last_verified.as_ref() != Some(&record.current) {
        return Err(Failure::new(
            4,
            "deployment requires a verified current Kotlin snapshot; run `cott verify`",
        ));
    }
    if !record.current.semantic_coverage.policy.passed {
        return Err(Failure::new(
            4,
            "deployment refuses a failed semantic coverage policy",
        ));
    }

    let target = deployment_output(&loaded, output)?;
    validate_deployment_target(&loaded.paths, &target)?;
    let prefix = artifact_prefix(&loaded.paths)?;
    let mut package = BTreeMap::new();
    let jar_relative = prefix.join("library/cott-module.jar");
    let jar = read_managed(&loaded, &jar_relative)?;
    package.insert(PathBuf::from("cott-module.jar"), jar);

    let compile_only_hashes = loaded
        .paths
        .compile_only
        .iter()
        .map(|path| read_digest(path))
        .collect::<Result<BTreeSet<_>, _>>()?;
    let mut runtime_libraries = Vec::new();
    for (path, expected) in &record.current.managed_files {
        let relative = PathBuf::from(path);
        let Ok(artifact) = relative.strip_prefix(&prefix) else {
            continue;
        };
        if !artifact.starts_with("runtime-libs") {
            continue;
        }
        if artifact != Path::new("runtime-libs/kotlinx-coroutines-core-jvm.jar") {
            return Err(Failure::new(
                4,
                format!(
                    "unexpected verified runtime dependency: {}",
                    relative.display()
                ),
            ));
        }
        let bytes = read_managed(&loaded, &relative)?;
        let actual = digest(&bytes);
        if &actual != expected {
            return Err(Failure::new(4, format!("runtime dependency drift: {path}")));
        }
        if record
            .current
            .tools
            .pointer("/runtime_dependencies/kotlinx_coroutines_core_jvm/artifact")
            .and_then(Value::as_str)
            != Some("runtime-libs/kotlinx-coroutines-core-jvm.jar")
            || record
                .current
                .tools
                .pointer("/runtime_dependencies/kotlinx_coroutines_core_jvm/content_hash")
                .and_then(Value::as_str)
                != Some(actual.as_str())
        {
            return Err(Failure::new(
                4,
                "verified coroutine dependency metadata does not match the managed JAR",
            ));
        }
        if compile_only_hashes.contains(&actual) {
            return Err(Failure::new(
                4,
                format!("compile-only Kotlin dependency must not be deployed: {path}"),
            ));
        }
        let name = artifact
            .file_name()
            .ok_or_else(|| Failure::new(4, "runtime dependency has no file name"))?;
        let member = PathBuf::from("runtime-libs").join(name);
        let version = record
            .current
            .tools
            .pointer("/runtime_dependencies/kotlinx_coroutines_core_jvm/version")
            .and_then(Value::as_str)
            .filter(|version| !version.is_empty())
            .ok_or_else(|| Failure::new(4, "verified coroutine dependency version is missing"))?;
        runtime_libraries.push(json!({
            "path": path_text(&member)?,
            "name": "kotlinx-coroutines-core-jvm",
            "sha256": actual,
            "version": version,
        }));
        if package.insert(member.clone(), bytes).is_some() {
            return Err(Failure::new(
                4,
                format!(
                    "runtime dependency file name collides in deployment: {}",
                    member.display()
                ),
            ));
        }
    }
    if runtime_libraries.is_empty() {
        return Err(Failure::new(
            4,
            "verified Kotlin deployment has no runtime libraries",
        ));
    }
    let verified_classpath = record
        .current
        .tools
        .pointer("/compile_inputs/classpath")
        .and_then(Value::as_array)
        .ok_or_else(|| Failure::new(4, "verified Kotlin tools omit compile_inputs.classpath"))?;
    if verified_classpath.len() != loaded.paths.classpath.len() {
        return Err(Failure::new(
            4,
            "verified Kotlin classpath count does not match the current manifest",
        ));
    }
    for (index, classpath) in loaded.paths.classpath.iter().enumerate() {
        let canonical = fs::canonicalize(classpath).map_err(|error| {
            Failure::new(
                6,
                format!(
                    "canonicalize runtime classpath {}: {error}",
                    classpath.display()
                ),
            )
        })?;
        let bytes = fs::read(&canonical).map_err(|error| {
            Failure::new(
                6,
                format!("read runtime classpath {}: {error}", canonical.display()),
            )
        })?;
        let hash = digest(&bytes);
        let verified = &verified_classpath[index];
        if verified.get("index").and_then(Value::as_u64) != Some(index as u64)
            || verified.get("scope").and_then(Value::as_str) != Some("runtime")
            || verified.get("path").and_then(Value::as_str) != canonical.to_str()
            || verified.get("content_hash").and_then(Value::as_str) != Some(hash.as_str())
        {
            return Err(Failure::new(
                4,
                format!(
                    "runtime classpath dependency was not verified exactly: {}",
                    classpath.display()
                ),
            ));
        }
        let name = classpath
            .file_name()
            .and_then(|name| name.to_str())
            .ok_or_else(|| Failure::new(4, "runtime classpath JAR has no UTF-8 file name"))?;
        let member = PathBuf::from("runtime-libs").join(format!("{index:03}-{name}"));
        if package.insert(member.clone(), bytes).is_some() {
            return Err(Failure::new(
                4,
                format!(
                    "runtime classpath file name collides in deployment: {}",
                    member.display()
                ),
            ));
        }
        runtime_libraries.push(json!({
            "path": path_text(&member)?,
            "sha256": hash,
        }));
    }

    let generation = loaded
        .generation_bytes
        .clone()
        .ok_or_else(|| Failure::new(4, "deployment requires generation.json"))?;
    let module_hash = package
        .get(Path::new("cott-module.jar"))
        .map(|bytes| digest(bytes))
        .ok_or_else(|| Failure::new(4, "verified Kotlin module JAR is missing"))?;
    let metadata = json!({
        "schema_version": 1,
        "target": "kotlin",
        "project": {
            "name": loaded.config.project.name,
            "version": loaded.config.project.version,
        },
        "jvm_target": loaded.config.kotlin.jvm_target,
        "provided": [kotlin_stdlib_dependency(&record.current.tools)?],
        "runtime_libraries": runtime_libraries,
        "module": {
            "path": "cott-module.jar",
            "sha256": module_hash,
        },
    });
    let mut metadata_bytes = serde_json::to_vec(&metadata)
        .map_err(|error| Failure::new(6, format!("serialize deployment metadata: {error}")))?;
    metadata_bytes.push(b'\n');
    package.insert(PathBuf::from("dependencies.json"), metadata_bytes);
    package.insert(PathBuf::from("generation.json"), generation);

    publish_directory_noreplace(&loaded.paths, &target, &package, &loaded.input_snapshot)?;
    Ok(target)
}

pub(crate) fn init(
    path: PathBuf,
    name: Option<String>,
    no_sync: bool,
    _format: OutputFormat,
) -> Result<PathBuf, Failure> {
    let absolute = if path.is_absolute() {
        path
    } else {
        std::env::current_dir()
            .map_err(|error| Failure::new(2, format!("determine init directory: {error}")))?
            .join(path)
    };
    if !matches!(
        absolute.components().next_back(),
        Some(Component::Normal(_))
    ) {
        return Err(Failure::new(
            2,
            "init path must have a normal final component",
        ));
    }
    let final_name = absolute
        .file_name()
        .ok_or_else(|| Failure::new(2, "init path has no final component"))?;
    let parent = absolute
        .parent()
        .ok_or_else(|| Failure::new(2, "init path has no parent"))?;
    let parent = fs::canonicalize(parent)
        .map_err(|error| Failure::new(2, format!("resolve init parent: {error}")))?;
    let metadata = fs::symlink_metadata(&parent)
        .map_err(|error| Failure::new(2, format!("inspect init parent: {error}")))?;
    if metadata.file_type().is_symlink() || !metadata.is_dir() {
        return Err(Failure::new(2, "init parent is not a regular directory"));
    }
    let target = parent.join(final_name);
    if fs::symlink_metadata(&target).is_ok() {
        return Err(Failure::new(
            2,
            format!("init target already exists: {}", target.display()),
        ));
    }
    let project_name = name
        .or_else(|| final_name.to_str().map(str::to_owned))
        .filter(|name| crate::manifest::valid_kotlin_project_name(name))
        .ok_or_else(|| Failure::new(2, "init project name must be lowercase kebab-case"))?;
    let module = project_name.replace('-', "_");
    let nonce = format!(
        "{:x}-{:x}",
        std::process::id(),
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map_or(0, |duration| duration.as_nanos())
    );
    let temporary = parent.join(format!(".cott-kotlin-init-{nonce}"));
    let marker = format!("{{\"nonce\":{},\"schema_version\":1}}\n", json!(nonce));
    let result = (|| {
        DirBuilder::new()
            .mode(0o700)
            .create(&temporary)
            .map_err(|error| Failure::new(6, format!("create init staging: {error}")))?;
        write_new(&temporary.join(".cott-init"), marker.as_bytes())?;
        fs::create_dir_all(temporary.join("src").join(&module))
            .and_then(|_| fs::create_dir(temporary.join("kotlin")))
            .map_err(|error| Failure::new(6, format!("create Kotlin scaffold: {error}")))?;
        write_new(
            &temporary.join(".gitignore"),
            b".cott/\ngenerated/\ndist/\n.gradle/\nbuild/\n",
        )?;
        let manifest = format!(
            "[project]\nname = \"{project_name}\"\nversion = \"0.1.0\"\nsource = \"src\"\n\n[target.kotlin]\nsource = \"kotlin\"\ngenerated = \"generated/kotlin\"\ncompiler = \"kotlinc\"\njava = \"java\"\njvm_target = 17\nruntime_validation = \"boundary\"\n"
        );
        write_new(&temporary.join("cott.toml"), manifest.as_bytes())?;
        write_new(
            &temporary.join("src").join(&module).join("main.cott"),
            format!("module {module}.main\n\nfn main() -> Unit\n").as_bytes(),
        )?;
        sync_tree(&temporary)?;
        if !no_sync {
            let (config, paths, _) = load_kotlin_config_with_paths(&temporary)
                .map_err(|error| Failure::new(2, error.to_string()))?;
            kotlin_verify::probe(&config, &paths)
                .map_err(|message| Failure::new(2, format!("probe Kotlin toolchain: {message}")))?;
        }
        rename_noreplace(&temporary, &target)?;
        sync_directory(&parent)?;
        let marker_path = target.join(".cott-init");
        let actual = fs::read(&marker_path)
            .map_err(|error| Failure::new(6, format!("read init ownership marker: {error}")))?;
        if actual != marker.as_bytes() {
            return Err(Failure::new(
                6,
                "init ownership marker changed before commit",
            ));
        }
        fs::remove_file(&marker_path)
            .map_err(|error| Failure::new(6, format!("commit init scaffold: {error}")))?;
        sync_directory(&target)?;
        sync_directory(&parent)?;
        Ok(target.clone())
    })();
    if temporary.exists() {
        let owned =
            fs::read(temporary.join(".cott-init")).is_ok_and(|bytes| bytes == marker.as_bytes());
        if owned {
            fs::remove_dir_all(&temporary)
                .map_err(|error| Failure::new(6, format!("remove failed init staging: {error}")))?;
            sync_directory(&parent)?;
        }
    }
    result
}

fn project_root(project: Option<PathBuf>) -> Result<PathBuf, Failure> {
    project.map(Ok).unwrap_or_else(|| {
        std::env::current_dir().map_err(|error| Failure::new(2, error.to_string()))
    })
}

fn render_diagnostics(diagnostics: &[ProjectDiagnostic]) -> String {
    diagnostics
        .iter()
        .map(|diagnostic| {
            format!(
                "{}:{}-{}: {}",
                diagnostic.path.display(),
                diagnostic.diagnostic.span.start,
                diagnostic.diagnostic.span.end,
                diagnostic.diagnostic.message
            )
        })
        .collect::<Vec<_>>()
        .join("\n")
}

fn collect_inputs(
    config: &KotlinProjectConfig,
    paths: &KotlinPaths,
    manifest_source: &str,
    sources: &[SourceFile],
    generator_rules: Option<&str>,
) -> Result<BTreeMap<String, String>, Failure> {
    let mut inputs = BTreeMap::new();
    insert_consumed_input(
        &mut inputs,
        path_text(&project_relative(&paths.root, &paths.manifest)?)?,
        digest(manifest_source.as_bytes()),
        "Kotlin manifest",
    )?;
    for source in sources {
        let path = paths.source_dir.join(&source.path);
        let relative = project_relative(&paths.root, &path)?;
        insert_consumed_input(
            &mut inputs,
            path_text(&relative)?,
            digest(source.text.as_bytes()),
            "Cott source",
        )?;
    }
    match (&config.generator.rules, generator_rules) {
        (Some(relative), Some(rules)) => {
            let path = paths.root.join(relative);
            let relative = project_relative(&paths.root, &path)?;
            insert_consumed_input(
                &mut inputs,
                path_text(&relative)?,
                digest(rules.as_bytes()),
                "Kotlin generator rules",
            )?;
        }
        (None, None) => {}
        _ => {
            return Err(Failure::new(
                6,
                "configured Kotlin generator rules do not match the frozen project input",
            ));
        }
    }

    let mut files = Vec::new();
    files.extend(paths.classpath.iter().cloned());
    files.extend(paths.compile_only.iter().cloned());
    let agents = paths.root.join("AGENTS.md");
    if agents.exists() {
        files.push(agents);
    }
    files.sort();
    for path in files {
        let relative = project_relative(&paths.root, &path)?;
        let leaf = read_regular_leaf(&path, "Kotlin project input")
            .map_err(|message| Failure::new(6, message))?
            .ok_or_else(|| {
                Failure::new(
                    6,
                    format!("Kotlin project input disappeared: {}", path.display()),
                )
            })?;
        insert_consumed_input(
            &mut inputs,
            path_text(&relative)?,
            digest(&leaf.bytes),
            "Kotlin project input",
        )?;
    }
    Ok(inputs)
}

fn insert_consumed_input(
    inputs: &mut BTreeMap<String, String>,
    path: String,
    hash: String,
    kind: &str,
) -> Result<(), Failure> {
    match inputs.get(&path) {
        Some(existing) if existing != &hash => Err(Failure::new(
            6,
            format!("{kind} `{path}` yielded inconsistent bytes while loading the project"),
        )),
        Some(_) => Ok(()),
        None => {
            inputs.insert(path, hash);
            Ok(())
        }
    }
}

fn insert_binding_input(
    paths: &KotlinPaths,
    binding: &KotlinBinding,
    inputs: &mut BTreeMap<String, String>,
    planned_source_write: bool,
) -> Result<(), Failure> {
    if digest(&binding.bytes) != binding.content_hash {
        return Err(Failure::new(
            4,
            format!(
                "Kotlin binding `{}` content hash is invalid",
                binding.cott_symbol
            ),
        ));
    }
    let source = normalized_relative(&binding.source_origin)?;
    if !paths
        .root
        .join(&source)
        .starts_with(&paths.kotlin_source_dir)
    {
        return Err(Failure::new(
            4,
            format!(
                "Kotlin binding source escaped target.kotlin.source: {}",
                source.display()
            ),
        ));
    }
    let source = path_text(&source)?;
    if planned_source_write {
        inputs.insert(source, binding.content_hash.clone());
    } else {
        insert_consumed_input(
            inputs,
            source,
            binding.content_hash.clone(),
            "Kotlin binding source",
        )?;
    }
    Ok(())
}

fn validate_binding_set(
    project: &Project,
    bindings: &[KotlinBinding],
    pending: &BTreeSet<String>,
    agent_runs: &[AgentRun],
) -> Result<(), Failure> {
    let callables = project
        .plan
        .callables()
        .into_iter()
        .map(|callable| callable.symbol)
        .collect::<BTreeSet<_>>();
    if let Some(symbol) = pending.iter().find(|symbol| !callables.contains(*symbol)) {
        return Err(Failure::new(
            4,
            format!("unknown pending Kotlin symbol `{symbol}`"),
        ));
    }
    let mut symbols = BTreeSet::new();
    for binding in bindings {
        if !callables.contains(&binding.cott_symbol) || !symbols.insert(&binding.cott_symbol) {
            return Err(Failure::new(
                4,
                format!(
                    "invalid or duplicate Kotlin binding `{}`",
                    binding.cott_symbol
                ),
            ));
        }
        if binding.owner == KotlinOwner::Manifest && pending.contains(&binding.cott_symbol) {
            return Err(Failure::new(
                4,
                format!(
                    "manifest Kotlin binding `{}` cannot be pending",
                    binding.cott_symbol
                ),
            ));
        }
        if digest(&binding.bytes) != binding.content_hash {
            return Err(Failure::new(
                4,
                format!(
                    "Kotlin binding `{}` content hash does not match bytes",
                    binding.cott_symbol
                ),
            ));
        }
    }
    if let Some(run) = agent_runs
        .iter()
        .find(|run| !callables.contains(&run.symbol))
    {
        return Err(Failure::new(
            4,
            format!("agent run has unknown Kotlin symbol `{}`", run.symbol),
        ));
    }
    Ok(())
}

fn build_record(
    project: &Project,
    bindings: &[KotlinBinding],
    supplied_runs: &[AgentRun],
    pending: &BTreeSet<String>,
    verification: Option<&Verification>,
    managed_files: BTreeMap<String, String>,
    emission: &KotlinEmission,
) -> Result<(KotlinGenerationRecord, Vec<(PathBuf, Vec<u8>)>), Failure> {
    let mut inputs = project.inputs.clone();
    let mut implementations = BTreeMap::<String, KotlinBindingRecord>::new();
    let mut source_writes = BTreeMap::<PathBuf, Vec<u8>>::new();
    for binding in bindings {
        let planned_source_write = binding.owner == KotlinOwner::Agent
            && supplied_runs.iter().any(|run| {
                run.symbol == binding.cott_symbol && run.implementation_hash == binding.content_hash
            });
        insert_binding_input(&project.paths, binding, &mut inputs, planned_source_write)?;
        let source = normalized_relative(&binding.source_origin)?;
        let runtime = normalized_relative(&binding.runtime_origin)?;
        if binding.owner == KotlinOwner::Agent {
            match source_writes.get(&source) {
                Some(bytes) if bytes != &binding.bytes => {
                    return Err(Failure::new(
                        4,
                        format!(
                            "Kotlin bindings supplied inconsistent bytes for source {}",
                            source.display()
                        ),
                    ));
                }
                Some(_) => {}
                None => {
                    source_writes.insert(source.clone(), binding.bytes.clone());
                }
            }
        }
        implementations.insert(
            binding.cott_symbol.clone(),
            KotlinBindingRecord {
                cott_symbol: binding.cott_symbol.clone(),
                target_symbol: binding.target_symbol.clone(),
                source_origin: path_text(&source)?,
                runtime_origin: path_text(&runtime)?,
                content_hash: binding.content_hash.clone(),
                owner: binding.owner,
            },
        );
    }
    if let Some(baseline) = &project.baseline {
        for symbol in pending {
            if implementations.contains_key(symbol) {
                continue;
            }
            let Some(existing) = baseline
                .current
                .implementations
                .iter()
                .find(|implementation| &implementation.cott_symbol == symbol)
            else {
                continue;
            };
            if existing.owner != KotlinOwner::Agent {
                return Err(Failure::new(
                    4,
                    format!("pending Kotlin source `{symbol}` has invalid recorded ownership"),
                ));
            }
            match inputs.get(&existing.source_origin) {
                Some(hash) if hash == &existing.content_hash => {
                    implementations.insert(symbol.clone(), existing.clone());
                }
                Some(_) => {
                    return Err(Failure::new(
                        4,
                        format!(
                            "pending Kotlin source `{symbol}` is not authenticated by its recorded identity"
                        ),
                    ));
                }
                None => {
                    // A missing accepted source is unresolved, but its obsolete
                    // implementation and run identity are not current evidence.
                }
            }
        }
        let current_symbols = project
            .plan
            .callables()
            .into_iter()
            .map(|callable| callable.symbol)
            .collect::<BTreeSet<_>>();
        for existing in &baseline.current.implementations {
            if current_symbols.contains(&existing.cott_symbol)
                || existing.owner != KotlinOwner::Agent
                || inputs.get(&existing.source_origin) != Some(&existing.content_hash)
            {
                continue;
            }
            implementations
                .entry(existing.cott_symbol.clone())
                .or_insert_with(|| existing.clone());
        }
    }

    let mut runs = project
        .baseline
        .as_ref()
        .into_iter()
        .flat_map(|record| record.current.agent_runs.iter().cloned())
        .chain(supplied_runs.iter().cloned())
        .filter(|run| {
            implementations
                .get(&run.symbol)
                .is_some_and(|implementation| {
                    implementation.owner == KotlinOwner::Agent
                        && implementation.content_hash == run.implementation_hash
                })
        })
        .collect::<Vec<_>>();
    runs.sort_by(|left, right| {
        (
            &left.symbol,
            &left.implementation_hash,
            &left.prompt_hash,
            left.duration_ms,
        )
            .cmp(&(
                &right.symbol,
                &right.implementation_hash,
                &right.prompt_hash,
                right.duration_ms,
            ))
    });
    runs.dedup();
    for implementation in implementations.values() {
        if implementation.owner == KotlinOwner::Agent
            && !runs.iter().any(|run| {
                run.symbol == implementation.cott_symbol
                    && run.implementation_hash == implementation.content_hash
            })
        {
            return Err(Failure::new(
                4,
                format!(
                    "Kotlin agent implementation `{}` has no authentic matching agent run",
                    implementation.cott_symbol
                ),
            ));
        }
    }

    let intents =
        crate::intent::fingerprints(&project.plan.contract_surface(), configured_rules(project))
            .map_err(|message| {
                Failure::new(3, format!("Kotlin implementation intent: {message}"))
            })?;
    let mut tools = verification
        .map(|verification| verification.tools.clone())
        .or_else(|| {
            project
                .baseline
                .as_ref()
                .map(|record| record.current.tools.clone())
        })
        .unwrap_or_else(|| json!({}));
    let object = tools
        .as_object_mut()
        .ok_or_else(|| Failure::new(4, "Kotlin tools metadata is not an object"))?;
    object.insert(
        crate::intent::TOOL_KEY.to_owned(),
        crate::intent::metadata(&intents),
    );
    object.insert(
        "cott".to_owned(),
        current_compiler_tool().map_err(|message| Failure::new(6, message))?,
    );
    object.entry("runtime".to_owned()).or_insert_with(|| {
        json!({
            "abi": KOTLIN_RUNTIME_ABI_VERSION,
            "version": env!("CARGO_PKG_VERSION"),
        })
    });
    object.insert(
        "target".to_owned(),
        json!({"language": "kotlin", "jvm_target": project.config.kotlin.jvm_target}),
    );

    let ir = project
        .plan
        .ir
        .modules
        .iter()
        .map(|module| (module.module.as_string(), digest(&module.bytes)))
        .collect::<BTreeMap<_, _>>();
    let unresolved = pending.iter().cloned().collect::<Vec<_>>();
    let verified = verification.is_some();
    let mut snapshot = KotlinGenerationSnapshot {
        target: "kotlin".to_owned(),
        generation_id: String::new(),
        verified,
        compiler_version: env!("CARGO_PKG_VERSION").to_owned(),
        canonical_ir_schema: crate::provenance::CANONICAL_IR_SCHEMA_VERSION,
        runtime_abi: KOTLIN_RUNTIME_ABI_VERSION,
        project_name: project.config.project.name.clone(),
        project_version: project.config.project.version.clone(),
        inputs,
        tools,
        ir,
        contract_surface: project.plan.contract_surface(),
        public_symbols: emission.public_symbols.clone(),
        implementations: implementations.into_values().collect(),
        managed_files,
        unresolved,
        verification: verification
            .map(|verification| verification.report.clone())
            .unwrap_or(Value::Null),
        semantic_coverage: verification
            .map(|verification| verification.coverage.clone())
            .unwrap_or_default(),
        agent_runs: runs,
    };
    snapshot
        .compute_generation_id()
        .map_err(|message| Failure::new(4, message))?;
    let last_verified = if verified {
        Some(snapshot.clone())
    } else {
        project
            .baseline
            .as_ref()
            .and_then(|record| record.last_verified.clone())
    };
    Ok((
        KotlinGenerationRecord {
            schema_version: KOTLIN_GENERATION_SCHEMA_VERSION,
            current: snapshot,
            last_verified,
        },
        source_writes.into_iter().collect(),
    ))
}
fn carry_trusted_ir_state(
    project: &Project,
    record: &mut KotlinGenerationRecord,
) -> Result<(), Failure> {
    let skeleton = emit::emit(&project.config, &project.plan, &[])
        .map_err(|message| Failure::new(4, message))?;
    let mut unresolved = skeleton.unresolved.into_iter().collect::<BTreeSet<_>>();
    let current_symbols = project
        .plan
        .callables()
        .into_iter()
        .map(|callable| callable.symbol)
        .collect::<BTreeSet<_>>();
    let current_bindings = project
        .bindings
        .iter()
        .map(|binding| binding_record(binding).map(|record| (record.cott_symbol.clone(), record)))
        .collect::<Result<BTreeMap<_, _>, _>>()?;
    let mut implementations = BTreeMap::new();
    let Some(baseline) = &project.baseline else {
        record.current.implementations.clear();
        record.current.unresolved = unresolved.into_iter().collect();
        record.current.agent_runs.clear();
        record
            .current
            .compute_generation_id()
            .map_err(|message| Failure::new(4, message))?;
        return Ok(());
    };
    let baseline_pending = baseline
        .current
        .unresolved
        .iter()
        .cloned()
        .collect::<BTreeSet<_>>();
    for implementation in &baseline.current.implementations {
        let current = current_symbols.contains(&implementation.cott_symbol);
        let configured_manifest = project
            .config
            .kotlin
            .implementations
            .contains_key(&implementation.cott_symbol);
        let exact_agent_source =
            project.inputs.get(&implementation.source_origin) == Some(&implementation.content_hash);
        let keep = if current {
            match implementation.owner {
                KotlinOwner::Manifest => configured_manifest,
                KotlinOwner::Agent => !configured_manifest && exact_agent_source,
            }
        } else {
            implementation.owner == KotlinOwner::Agent && exact_agent_source
        };
        if !keep {
            continue;
        }
        if let Some(hash) = baseline.current.inputs.get(&implementation.source_origin) {
            record
                .current
                .inputs
                .insert(implementation.source_origin.clone(), hash.clone());
        }
        if current && !baseline_pending.contains(&implementation.cott_symbol) {
            let remains_resolved = match implementation.owner {
                KotlinOwner::Manifest => true,
                KotlinOwner::Agent => current_bindings
                    .get(&implementation.cott_symbol)
                    .is_some_and(|binding| binding == implementation),
            };
            if remains_resolved {
                unresolved.remove(&implementation.cott_symbol);
            }
        }
        implementations.insert(implementation.cott_symbol.clone(), implementation.clone());
    }
    record.current.implementations = implementations.into_values().collect();
    record.current.unresolved = unresolved.into_iter().collect();
    record.current.agent_runs = baseline
        .current
        .agent_runs
        .iter()
        .filter(|run| {
            record.current.implementations.iter().any(|implementation| {
                implementation.owner == KotlinOwner::Agent
                    && implementation.cott_symbol == run.symbol
                    && implementation.content_hash == run.implementation_hash
            })
        })
        .cloned()
        .collect();
    record
        .current
        .compute_generation_id()
        .map_err(|message| Failure::new(4, message))
}

fn validate_current_publication(
    project: &Project,
    emission: &KotlinEmission,
) -> Result<(), Failure> {
    let record = project.baseline.as_ref().ok_or_else(|| {
        Failure::new(
            4,
            "missing Kotlin generation record; run `cott emit kotlin`",
        )
    })?;
    let current = &record.current;
    if current.project_name != project.config.project.name
        || current.project_version != project.config.project.version
        || current.compiler_version != env!("CARGO_PKG_VERSION")
        || current.canonical_ir_schema != crate::provenance::CANONICAL_IR_SCHEMA_VERSION
        || current.runtime_abi != KOTLIN_RUNTIME_ABI_VERSION
        || current.inputs != project.inputs
        || current.contract_surface != project.plan.contract_surface()
        || current.public_symbols != emission.public_symbols
        || current.unresolved != emission.unresolved
    {
        return Err(Failure::new(
            4,
            "Kotlin generation record does not describe the current compiler inputs and target surface",
        ));
    }
    let expected_ir = project
        .plan
        .ir
        .modules
        .iter()
        .map(|module| (module.module.as_string(), digest(&module.bytes)))
        .collect::<BTreeMap<_, _>>();
    if current.ir != expected_ir {
        return Err(Failure::new(
            4,
            "Kotlin generation record has stale canonical IR hashes",
        ));
    }
    let current_symbols = project
        .plan
        .callables()
        .into_iter()
        .map(|callable| callable.symbol)
        .collect::<BTreeSet<_>>();
    let recorded_current = current
        .implementations
        .iter()
        .filter(|implementation| current_symbols.contains(&implementation.cott_symbol))
        .cloned()
        .collect::<Vec<_>>();
    let expected_implementations = project
        .bindings
        .iter()
        .map(binding_record)
        .collect::<Result<Vec<_>, _>>()?;
    if recorded_current != expected_implementations {
        return Err(Failure::new(
            4,
            "Kotlin generation record has stale implementation identities",
        ));
    }
    let actual = collect_tree_if_present(&project.paths.artifact_root)
        .map_err(|message| Failure::new(4, message))?;
    let owned = validate_owned_artifacts(project, &actual)?;
    for (path, bytes) in &emission.files {
        match actual.get(path) {
            Some(actual) if actual == bytes => {}
            Some(_) => {
                return Err(Failure::new(
                    4,
                    format!("managed Kotlin artifact differs: {}", path.display()),
                ));
            }
            None => {
                return Err(Failure::new(
                    4,
                    format!("missing managed Kotlin artifact: {}", path.display()),
                ));
            }
        }
    }
    for path in actual.keys() {
        if path == Path::new("generation.json") || emission.files.contains_key(path) {
            continue;
        }
        let compiled_output = path.starts_with("library") || path.starts_with("runtime-libs");
        if !compiled_output || !owned.contains(path) {
            return Err(Failure::new(
                4,
                format!("unexpected Kotlin artifact: {}", path.display()),
            ));
        }
    }
    Ok(())
}

fn binding_record(binding: &KotlinBinding) -> Result<KotlinBindingRecord, Failure> {
    Ok(KotlinBindingRecord {
        cott_symbol: binding.cott_symbol.clone(),
        target_symbol: binding.target_symbol.clone(),
        source_origin: path_text(&normalized_relative(&binding.source_origin)?)?,
        runtime_origin: path_text(&normalized_relative(&binding.runtime_origin)?)?,
        content_hash: binding.content_hash.clone(),
        owner: binding.owner,
    })
}

fn read_generation_record(
    paths: &KotlinPaths,
) -> Result<Option<(KotlinGenerationRecord, RegularLeaf)>, Failure> {
    let path = paths.artifact_root.join("generation.json");
    let Some(leaf) = read_regular_leaf(&path, "Kotlin generation record")
        .map_err(|message| Failure::new(6, message))?
    else {
        return Ok(None);
    };
    let record = KotlinGenerationRecord::parse(&leaf.bytes)
        .map_err(|message| Failure::new(4, format!("invalid {}: {message}", path.display())))?;
    Ok(Some((record, leaf)))
}

struct RegularLeaf {
    bytes: Vec<u8>,
    device: u64,
    inode: u64,
}

fn read_regular_leaf(path: &Path, label: &str) -> Result<Option<RegularLeaf>, String> {
    let mut file = match OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_CLOEXEC | libc::O_NOFOLLOW | libc::O_NONBLOCK)
        .open(path)
    {
        Ok(file) => file,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(None),
        Err(error) => return Err(format!("open {label} {}: {error}", path.display())),
    };
    let before = file
        .metadata()
        .map_err(|error| format!("inspect {label} {}: {error}", path.display()))?;
    if !before.is_file() || before.nlink() != 1 {
        return Err(format!(
            "{label} must be a regular non-symlink single-link file: {}",
            path.display()
        ));
    }

    let mut bytes = Vec::new();
    file.read_to_end(&mut bytes)
        .map_err(|error| format!("read {label} {}: {error}", path.display()))?;
    let after = file
        .metadata()
        .map_err(|error| format!("re-inspect opened {label} {}: {error}", path.display()))?;
    let leaf = fs::symlink_metadata(path)
        .map_err(|error| format!("re-inspect {label} leaf {}: {error}", path.display()))?;
    if !after.is_file()
        || after.nlink() != 1
        || !leaf.is_file()
        || leaf.file_type().is_symlink()
        || leaf.nlink() != 1
        || before.dev() != after.dev()
        || before.ino() != after.ino()
        || before.mode() != after.mode()
        || before.len() != after.len()
        || before.mtime() != after.mtime()
        || before.mtime_nsec() != after.mtime_nsec()
        || after.dev() != leaf.dev()
        || after.ino() != leaf.ino()
    {
        return Err(format!(
            "{label} changed or became unsafe while being read: {}",
            path.display()
        ));
    }
    Ok(Some(RegularLeaf {
        bytes,
        device: before.dev(),
        inode: before.ino(),
    }))
}

fn validate_owned_artifacts(
    project: &Project,
    actual: &BTreeMap<PathBuf, Vec<u8>>,
) -> Result<BTreeSet<PathBuf>, Failure> {
    let prefix = artifact_prefix(&project.paths)?;
    let mut owned = BTreeSet::new();
    if let Some(record) = &project.baseline {
        for (path, expected) in &record.current.managed_files {
            let path = normalized_relative(Path::new(path))?;
            let relative = path.strip_prefix(&prefix).map_err(|_| {
                Failure::new(
                    4,
                    format!(
                        "Kotlin managed path is outside artifact root: {}",
                        path.display()
                    ),
                )
            })?;
            if !safe_relative(relative) {
                return Err(Failure::new(
                    4,
                    format!("unsafe Kotlin managed path: {}", path.display()),
                ));
            }
            let bytes = actual.get(relative).ok_or_else(|| {
                Failure::new(
                    4,
                    format!("managed Kotlin artifact is missing: {}", path.display()),
                )
            })?;
            if digest(bytes) != *expected {
                return Err(Failure::new(
                    4,
                    format!("managed Kotlin artifact changed: {}", path.display()),
                ));
            }
            owned.insert(relative.to_path_buf());
        }
    }
    if actual.contains_key(Path::new("generation.json")) && project.baseline.is_none() {
        return Err(Failure::new(4, "unowned Kotlin generation.json is present"));
    }
    Ok(owned)
}

fn load_generator_rules(
    config: &KotlinProjectConfig,
    paths: &KotlinPaths,
) -> Result<Option<String>, Failure> {
    let Some(relative) = &config.generator.rules else {
        return Ok(None);
    };
    let path = paths.root.join(relative);
    let leaf = read_regular_leaf(&path, "Kotlin generator rules")
        .map_err(|message| Failure::new(6, message))?
        .ok_or_else(|| {
            Failure::new(
                4,
                format!(
                    "configured Kotlin generator rules are missing: {}",
                    path.display()
                ),
            )
        })?;
    String::from_utf8(leaf.bytes).map(Some).map_err(|_| {
        Failure::new(
            3,
            format!("Kotlin generator rules are not UTF-8: {}", path.display()),
        )
    })
}

fn configured_rules(project: &Project) -> &[u8] {
    project
        .generator_rules
        .as_deref()
        .unwrap_or_default()
        .as_bytes()
}

fn current_compiler_tool() -> Result<Value, String> {
    let executable = fs::canonicalize(std::env::current_exe().map_err(|error| error.to_string())?)
        .map_err(|error| error.to_string())?;
    Ok(json!({
        "content_hash": read_digest(&executable).map_err(|error| error.message)?,
        "executable": executable,
        "version": env!("CARGO_PKG_VERSION"),
    }))
}

fn collect_tree_if_present(root: &Path) -> Result<BTreeMap<PathBuf, Vec<u8>>, String> {
    match fs::symlink_metadata(root) {
        Ok(metadata) => {
            if metadata.file_type().is_symlink() || !metadata.is_dir() {
                return Err(format!(
                    "Kotlin artifact root is not a regular directory: {}",
                    root.display()
                ));
            }
            let mut files = BTreeMap::new();
            collect_tree(root, root, &mut files)?;
            Ok(files)
        }
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(BTreeMap::new()),
        Err(error) => Err(format!(
            "inspect Kotlin artifact root {}: {error}",
            root.display()
        )),
    }
}

fn collect_tree(
    root: &Path,
    directory: &Path,
    files: &mut BTreeMap<PathBuf, Vec<u8>>,
) -> Result<(), String> {
    let mut entries = fs::read_dir(directory)
        .map_err(|error| format!("read artifact directory {}: {error}", directory.display()))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|error| format!("read artifact directory {}: {error}", directory.display()))?;
    entries.sort_by_key(|entry| entry.file_name());
    for entry in entries {
        let path = entry.path();
        let metadata = fs::symlink_metadata(&path)
            .map_err(|error| format!("inspect Kotlin artifact {}: {error}", path.display()))?;
        if metadata.file_type().is_symlink() {
            return Err(format!(
                "Kotlin artifact must not be a symlink: {}",
                path.display()
            ));
        }
        if metadata.is_dir() {
            collect_tree(root, &path, files)?;
        } else if metadata.is_file() && metadata.nlink() == 1 {
            let relative = path
                .strip_prefix(root)
                .map_err(|_| format!("Kotlin artifact escaped root: {}", path.display()))?
                .to_path_buf();
            if !safe_relative(&relative) {
                return Err(format!(
                    "unsafe Kotlin artifact path: {}",
                    relative.display()
                ));
            }
            let leaf = read_regular_leaf(&path, "Kotlin artifact")?
                .ok_or_else(|| format!("Kotlin artifact disappeared: {}", path.display()))?;
            files.insert(relative, leaf.bytes);
        } else {
            return Err(format!(
                "Kotlin artifact is not a regular single-link file: {}",
                path.display()
            ));
        }
    }
    Ok(())
}

fn artifact_prefix(paths: &KotlinPaths) -> Result<PathBuf, Failure> {
    project_relative(&paths.root, &paths.artifact_root)
}

fn generation_relative(paths: &KotlinPaths) -> Result<PathBuf, Failure> {
    Ok(artifact_prefix(paths)?.join("generation.json"))
}

fn project_relative(root: &Path, path: &Path) -> Result<PathBuf, Failure> {
    let relative = path.strip_prefix(root).map_err(|_| {
        Failure::new(
            2,
            format!("path is outside project root: {}", path.display()),
        )
    })?;
    normalized_relative(relative)
}

fn normalized_relative(path: &Path) -> Result<PathBuf, Failure> {
    if !safe_relative(path) {
        return Err(Failure::new(
            2,
            format!("unsafe relative path: {}", path.display()),
        ));
    }
    Ok(path.to_path_buf())
}

fn safe_relative(path: &Path) -> bool {
    !path.as_os_str().is_empty()
        && path.is_relative()
        && path
            .components()
            .all(|component| matches!(component, Component::Normal(_)))
}

fn path_text(path: &Path) -> Result<String, Failure> {
    path.to_str()
        .map(|value| value.replace('\\', "/"))
        .ok_or_else(|| Failure::new(2, format!("path is not UTF-8: {}", path.display())))
}

fn digest(bytes: &[u8]) -> String {
    format!("sha256:{}", sha256_hex(bytes))
}

fn read_digest(path: &Path) -> Result<String, Failure> {
    fs::read(path)
        .map(|bytes| digest(&bytes))
        .map_err(|error| Failure::new(6, format!("read {}: {error}", path.display())))
}

fn deployment_output(project: &Project, output: Option<PathBuf>) -> Result<PathBuf, Failure> {
    match output {
        Some(path) if path.is_absolute() => Ok(path),
        Some(path) => Ok(std::env::current_dir()
            .map_err(|error| Failure::new(6, format!("determine deployment directory: {error}")))?
            .join(path)),
        None => Ok(project.paths.root.join("dist").join(format!(
            "{}-{}",
            project.config.project.name, project.config.project.version
        ))),
    }
}

fn validate_deployment_target(paths: &KotlinPaths, target: &Path) -> Result<(), Failure> {
    if !target.is_absolute()
        || target.file_name().is_none()
        || target
            .components()
            .any(|component| !matches!(component, Component::RootDir | Component::Normal(_)))
    {
        return Err(Failure::new(
            6,
            "deployment output must be a normalized absolute directory path",
        ));
    }
    if paths.root.starts_with(target)
        || [
            &paths.source_dir,
            &paths.kotlin_source_dir,
            &paths.artifact_root,
            &paths.root.join(".cott"),
        ]
        .iter()
        .any(|protected| target.starts_with(protected))
    {
        return Err(Failure::new(
            6,
            "deployment output overlaps project inputs or managed artifacts",
        ));
    }
    for ancestor in target.ancestors() {
        match fs::symlink_metadata(ancestor) {
            Ok(metadata)
                if ancestor == target
                    || metadata.file_type().is_symlink()
                    || !metadata.is_dir() =>
            {
                return Err(Failure::new(
                    6,
                    format!(
                        "deployment output exists or has unsafe parent: {}",
                        ancestor.display()
                    ),
                ));
            }
            Ok(_) => {}
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {}
            Err(error) => {
                return Err(Failure::new(
                    6,
                    format!("inspect deployment output {}: {error}", ancestor.display()),
                ));
            }
        }
    }
    Ok(())
}

fn read_managed(project: &Project, relative: &Path) -> Result<Vec<u8>, Failure> {
    let record = project
        .baseline
        .as_ref()
        .ok_or_else(|| Failure::new(4, "missing Kotlin generation record"))?;
    let key = path_text(relative)?;
    let expected = record
        .current
        .managed_files
        .get(&key)
        .ok_or_else(|| Failure::new(4, format!("artifact is not managed: {key}")))?;
    let bytes = fs::read(project.paths.root.join(relative))
        .map_err(|error| Failure::new(4, format!("read managed artifact {key}: {error}")))?;
    if digest(&bytes) != *expected {
        return Err(Failure::new(4, format!("managed artifact drift: {key}")));
    }
    Ok(bytes)
}

fn kotlin_stdlib_dependency(tools: &Value) -> Result<Value, Failure> {
    let dependency = tools
        .pointer("/runtime_dependencies/kotlin_stdlib")
        .and_then(Value::as_object)
        .ok_or_else(|| Failure::new(4, "verified Kotlin tools omit kotlin-stdlib metadata"))?;
    let version = dependency
        .get("version")
        .and_then(Value::as_str)
        .filter(|version| !version.is_empty())
        .ok_or_else(|| Failure::new(4, "verified Kotlin tools omit kotlin-stdlib version"))?;
    let content_hash = dependency
        .get("content_hash")
        .and_then(Value::as_str)
        .filter(|hash| {
            hash.strip_prefix("sha256:").is_some_and(|hex| {
                hex.len() == 64
                    && hex
                        .bytes()
                        .all(|byte| byte.is_ascii_digit() || matches!(byte, b'a'..=b'f'))
            })
        })
        .ok_or_else(|| Failure::new(4, "verified Kotlin tools have invalid kotlin-stdlib hash"))?;
    if dependency.get("required").and_then(Value::as_bool) != Some(true)
        || dependency.get("bundled").and_then(Value::as_bool) != Some(false)
    {
        return Err(Failure::new(
            4,
            "verified Kotlin stdlib must be required and consumer-provided",
        ));
    }
    let provided_by = dependency
        .get("provided_by")
        .and_then(Value::as_str)
        .filter(|provider| !provider.is_empty())
        .ok_or_else(|| Failure::new(4, "verified Kotlin tools omit stdlib provider"))?;
    Ok(json!({
        "bundled": false,
        "content_hash": content_hash,
        "name": "kotlin-stdlib",
        "provided_by": provided_by,
        "required": true,
        "version": version,
    }))
}

fn publish_directory_noreplace(
    paths: &KotlinPaths,
    target: &Path,
    files: &BTreeMap<PathBuf, Vec<u8>>,
    snapshot: &InputSnapshot,
) -> Result<(), Failure> {
    validate_deployment_target(paths, target)?;
    let parent = target
        .parent()
        .ok_or_else(|| Failure::new(6, "deployment output has no parent"))?;
    fs::create_dir_all(parent)
        .map_err(|error| Failure::new(6, format!("create deployment parent: {error}")))?;
    validate_deployment_target(paths, target)?;
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|error| Failure::new(6, error.to_string()))?
        .as_nanos();
    let temporary = parent.join(format!(
        ".cott-kotlin-deploy-{}-{nonce}",
        std::process::id()
    ));
    let marker = format!("{}-{nonce}\n", std::process::id()).into_bytes();
    let marker_path = PathBuf::from(".cott-deploy-owner");
    if files.contains_key(&marker_path) {
        return Err(Failure::new(
            6,
            "deployment member collides with ownership marker",
        ));
    }
    DirBuilder::new()
        .mode(0o700)
        .create(&temporary)
        .map_err(|error| Failure::new(6, format!("create deployment staging: {error}")))?;
    write_new(&temporary.join(&marker_path), &marker)?;
    let result = (|| {
        for (relative, bytes) in files {
            if !safe_relative(relative) {
                return Err(Failure::new(
                    6,
                    format!("unsafe deployment member: {}", relative.display()),
                ));
            }
            let path = temporary.join(relative);
            fs::create_dir_all(
                path.parent()
                    .ok_or_else(|| Failure::new(6, "deployment member has no parent"))?,
            )
            .map_err(|error| Failure::new(6, format!("create deployment directory: {error}")))?;
            write_new(&path, bytes)?;
        }
        let current = InputSnapshot::capture(&paths.root, snapshot.files.keys().cloned())
            .map_err(|error| Failure::new(6, error.to_string()))?;
        if &current != snapshot {
            return Err(Failure::new(
                6,
                "project changed while packaging Kotlin deployment",
            ));
        }
        fs::set_permissions(&temporary, fs::Permissions::from_mode(0o755))
            .map_err(|error| Failure::new(6, format!("set deployment permissions: {error}")))?;
        sync_tree(&temporary)?;
        validate_deployment_target(paths, target)?;
        rename_noreplace(&temporary, target)?;
        sync_directory(parent)?;
        let published_marker = target.join(&marker_path);
        if fs::read(&published_marker).ok().as_deref() != Some(marker.as_slice()) {
            return Err(Failure::new(
                6,
                "published deployment ownership marker changed before commit",
            ));
        }
        fs::remove_file(&published_marker)
            .map_err(|error| Failure::new(6, format!("commit deployment package: {error}")))?;
        sync_directory(target)?;
        sync_directory(parent)
    })();
    if temporary.exists()
        && fs::read(temporary.join(&marker_path)).is_ok_and(|bytes| bytes == marker)
    {
        fs::remove_dir_all(&temporary)
            .map_err(|error| Failure::new(6, format!("remove deployment staging: {error}")))?;
        sync_directory(parent)?;
    }
    result
}

fn write_new(path: &Path, bytes: &[u8]) -> Result<(), Failure> {
    let mut file = OpenOptions::new()
        .create_new(true)
        .write(true)
        .mode(0o600)
        .custom_flags(libc::O_CLOEXEC | libc::O_NOFOLLOW)
        .open(path)
        .map_err(|error| Failure::new(6, format!("create {}: {error}", path.display())))?;
    file.write_all(bytes)
        .and_then(|_| file.sync_all())
        .map_err(|error| Failure::new(6, format!("write {}: {error}", path.display())))
}

fn sync_tree(path: &Path) -> Result<(), Failure> {
    let mut entries = fs::read_dir(path)
        .map_err(|error| Failure::new(6, format!("read directory {}: {error}", path.display())))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|error| Failure::new(6, format!("read directory {}: {error}", path.display())))?;
    entries.sort_by_key(|entry| entry.file_name());
    for entry in entries {
        let metadata = fs::symlink_metadata(entry.path()).map_err(|error| {
            Failure::new(6, format!("inspect {}: {error}", entry.path().display()))
        })?;
        if metadata.file_type().is_symlink() {
            return Err(Failure::new(
                6,
                format!("staged tree contains symlink: {}", entry.path().display()),
            ));
        }
        if metadata.is_dir() {
            sync_tree(&entry.path())?;
        } else if metadata.is_file() && metadata.nlink() == 1 {
            File::open(entry.path())
                .and_then(|file| file.sync_all())
                .map_err(|error| Failure::new(6, format!("sync staged file: {error}")))?;
        } else {
            return Err(Failure::new(
                6,
                format!(
                    "staged tree contains special file: {}",
                    entry.path().display()
                ),
            ));
        }
    }
    sync_directory(path)
}

fn sync_directory(path: &Path) -> Result<(), Failure> {
    File::open(path)
        .and_then(|directory| directory.sync_all())
        .map_err(|error| Failure::new(6, format!("sync directory {}: {error}", path.display())))
}

fn rename_noreplace(source: &Path, target: &Path) -> Result<(), Failure> {
    let source = CString::new(source.as_os_str().as_bytes())
        .map_err(|_| Failure::new(6, "staging path contains NUL"))?;
    let target_c = CString::new(target.as_os_str().as_bytes())
        .map_err(|_| Failure::new(6, "target path contains NUL"))?;
    let result = unsafe {
        libc::renameat2(
            libc::AT_FDCWD,
            source.as_ptr(),
            libc::AT_FDCWD,
            target_c.as_ptr(),
            libc::RENAME_NOREPLACE,
        )
    };
    if result == 0 {
        Ok(())
    } else {
        let error = std::io::Error::last_os_error();
        if error.kind() == std::io::ErrorKind::AlreadyExists {
            Err(Failure::new(
                6,
                format!("output already exists: {}", target.display()),
            ))
        } else {
            Err(Failure::new(
                6,
                format!("atomically publish {}: {error}", target.display()),
            ))
        }
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
enum DiffClass {
    Breaking,
    Additive,
    Documentation,
    Implementation,
    Dependency,
    Toolchain,
    Artifact,
    VersionIncompatible,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
enum DiffKind {
    DeclarationAdded,
    DeclarationRemoved,
    RequiredParameterAdded,
    RequiredParameterRemoved,
    FieldAdded,
    FieldRemoved,
    EnumVariantAdded,
    EnumVariantRemoved,
    SemanticChanged,
    KotlinSymbolAdded,
    KotlinSymbolRemoved,
    ImplementationChanged,
    DependencyChanged,
    InputChanged,
    ToolchainChanged,
    ArtifactChanged,
    DocumentationChanged,
    VersionIncompatible,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
struct DiffChange {
    class: DiffClass,
    kind: DiffKind,
    subject: String,
    message: String,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
enum VersionBump {
    None,
    Minor,
    Major,
}

#[derive(Debug, Serialize)]
struct DiffReport {
    target: &'static str,
    baseline_version: String,
    current_version: String,
    breaking: bool,
    version_compatible: bool,
    required_version_bump: VersionBump,
    changes: Vec<DiffChange>,
    advice: Vec<String>,
}

fn diff_inner(project: Option<PathBuf>, baseline: Option<PathBuf>) -> Result<DiffReport, Failure> {
    let loaded = load(project, true)?;
    let explicit = baseline.is_some();
    let baseline_path = match baseline {
        Some(path) if path.is_absolute() => path,
        Some(path) => loaded.paths.root.join(path),
        None => loaded.paths.artifact_root.join("generation.json"),
    };
    let bytes = if explicit {
        read_regular_leaf(&baseline_path, "Kotlin diff baseline")
            .map_err(|message| Failure::new(6, message))?
            .ok_or_else(|| {
                Failure::new(
                    2,
                    format!("diff baseline does not exist: {}", baseline_path.display()),
                )
            })?
            .bytes
    } else {
        loaded
            .generation_bytes
            .clone()
            .ok_or_else(|| Failure::new(2, "default Kotlin diff baseline is missing"))?
    };
    let record = KotlinGenerationRecord::parse(&bytes).map_err(|message| {
        Failure::new(
            2,
            format!(
                "invalid diff baseline {}: {message}",
                baseline_path.display()
            ),
        )
    })?;
    let baseline = if explicit {
        record.current
    } else {
        record.last_verified.ok_or_else(|| {
            Failure::new(
                2,
                "default Kotlin diff baseline has no last_verified snapshot",
            )
        })?
    };
    let emission = emit::emit(&loaded.config, &loaded.plan, &loaded.bindings)
        .map_err(|message| Failure::new(4, message))?;
    let pending = emission.unresolved.iter().cloned().collect::<BTreeSet<_>>();
    let actual = collect_tree_if_present(&loaded.paths.artifact_root)
        .map_err(|message| Failure::new(4, message))?;
    validate_owned_artifacts(&loaded, &actual)?;
    let prefix = artifact_prefix(&loaded.paths)?;
    let mut managed = loaded
        .baseline
        .as_ref()
        .into_iter()
        .flat_map(|record| record.current.managed_files.iter())
        .filter(|(path, _)| {
            Path::new(path).strip_prefix(&prefix).is_ok_and(|relative| {
                relative.starts_with("library") || relative.starts_with("runtime-libs")
            })
        })
        .map(|(path, hash)| (path.clone(), hash.clone()))
        .collect::<BTreeMap<_, _>>();
    for (path, bytes) in &emission.files {
        managed.insert(path_text(&prefix.join(path))?, digest(bytes));
    }
    let (current, _) = build_record(
        &loaded,
        &loaded.bindings,
        &[],
        &pending,
        None,
        managed,
        &emission,
    )?;
    let frozen = InputSnapshot::capture(
        &loaded.paths.root,
        loaded.input_snapshot.files.keys().cloned(),
    )
    .map_err(|error| Failure::new(6, error.to_string()))?;
    if frozen != loaded.input_snapshot {
        return Err(Failure::new(
            6,
            "Kotlin project changed during frozen diff inspection",
        ));
    }
    generation_diff(&baseline, &current.current)
}

fn generation_diff(
    baseline: &KotlinGenerationSnapshot,
    current: &KotlinGenerationSnapshot,
) -> Result<DiffReport, Failure> {
    let baseline_version = parse_api_version(&baseline.project_version)
        .ok_or_else(|| Failure::new(2, "baseline project_version is invalid"))?;
    let current_version = parse_api_version(&current.project_version)
        .ok_or_else(|| Failure::new(2, "current project_version is invalid"))?;
    if current_version < baseline_version {
        return Err(Failure::new(
            2,
            format!("project version regressed from {baseline_version} to {current_version}"),
        ));
    }
    let old = declarations_by_name(&baseline.contract_surface);
    let new = declarations_by_name(&current.contract_surface);
    let mut changes = Vec::new();
    let mut advice = Vec::new();
    for (name, declaration) in &old {
        match new.get(name) {
            None => {
                push_change(
                    &mut changes,
                    DiffClass::Breaking,
                    DiffKind::DeclarationRemoved,
                    name,
                    format!("{name} was removed"),
                );
                advice.push(format!("Remove uses of declaration `{name}`."));
            }
            Some(updated)
                if normalized_declaration(declaration) != normalized_declaration(updated) =>
            {
                if !structural_changes(name, declaration, updated, &mut changes, &mut advice) {
                    push_change(
                        &mut changes,
                        DiffClass::Breaking,
                        DiffKind::SemanticChanged,
                        name,
                        format!("{name} contract or type changed"),
                    );
                }
            }
            Some(updated) if declaration != updated => push_change(
                &mut changes,
                DiffClass::Documentation,
                DiffKind::DocumentationChanged,
                name,
                format!("{name} documentation changed"),
            ),
            Some(_) => {}
        }
    }
    for name in new.keys().filter(|name| !old.contains_key(*name)) {
        push_change(
            &mut changes,
            DiffClass::Additive,
            DiffKind::DeclarationAdded,
            name,
            format!("{name} was added"),
        );
        advice.push(format!(
            "Adopt declaration `{name}` where its API is needed."
        ));
    }
    compare_symbols(
        &baseline.public_symbols,
        &current.public_symbols,
        &mut changes,
    );
    compare_implementations(
        &baseline.implementations,
        &current.implementations,
        &mut changes,
    );
    compare_inputs(&baseline.inputs, &current.inputs, &mut changes);
    compare_maps(
        "tool",
        &baseline.tools,
        &current.tools,
        DiffClass::Toolchain,
        DiffKind::ToolchainChanged,
        &mut changes,
    );
    compare_path_maps(
        &baseline.managed_files,
        &current.managed_files,
        DiffClass::Artifact,
        DiffKind::ArtifactChanged,
        &mut changes,
    );

    changes.sort_by(|left, right| {
        (left.class as u8, left.subject.as_str(), left.kind as u8).cmp(&(
            right.class as u8,
            right.subject.as_str(),
            right.kind as u8,
        ))
    });
    let breaking = changes
        .iter()
        .any(|change| change.class == DiffClass::Breaking);
    let required_version_bump = if breaking {
        if baseline_version.major == 0 {
            VersionBump::Minor
        } else {
            VersionBump::Major
        }
    } else if changes
        .iter()
        .any(|change| change.class == DiffClass::Additive)
    {
        VersionBump::Minor
    } else {
        VersionBump::None
    };
    let version_compatible =
        version_bump_is_sufficient(baseline_version, current_version, required_version_bump);
    if !version_compatible {
        push_change(
            &mut changes,
            DiffClass::VersionIncompatible,
            DiffKind::VersionIncompatible,
            &format!("{baseline_version} -> {current_version}"),
            format!(
                "VERSION INCOMPATIBLE: {required_version_bump:?} bump required for Kotlin API changes"
            ),
        );
    }
    Ok(DiffReport {
        target: "kotlin",
        baseline_version: baseline.project_version.clone(),
        current_version: current.project_version.clone(),
        breaking,
        version_compatible,
        required_version_bump,
        changes,
        advice,
    })
}

fn push_change(
    changes: &mut Vec<DiffChange>,
    class: DiffClass,
    kind: DiffKind,
    subject: &str,
    message: String,
) {
    changes.push(DiffChange {
        class,
        kind,
        subject: subject.to_owned(),
        message,
    });
}

fn declarations_by_name(value: &Value) -> BTreeMap<String, Value> {
    value
        .as_object()
        .into_iter()
        .flat_map(|modules| modules.iter())
        .flat_map(|(module, surface)| {
            surface
                .get("declarations")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
                .filter_map(move |declaration| {
                    let name = declaration.get("name")?.as_str()?;
                    Some((
                        if name.contains('.') {
                            name.to_owned()
                        } else {
                            format!("{module}.{name}")
                        },
                        declaration.clone(),
                    ))
                })
        })
        .collect()
}

fn normalized_declaration(value: &Value) -> Value {
    fn strip(value: &mut Value) {
        match value {
            Value::Object(object) => {
                object.remove("doc");
                object.remove("span");
                object.remove("source_order");
                for value in object.values_mut() {
                    strip(value);
                }
            }
            Value::Array(values) => {
                for value in values {
                    strip(value);
                }
            }
            _ => {}
        }
    }
    let mut value = value.clone();
    strip(&mut value);
    value
}

fn named_members(value: &Value, field: &str) -> Option<BTreeMap<String, Value>> {
    value
        .get(field)?
        .as_array()?
        .iter()
        .map(|member| Some((member.get("name")?.as_str()?.to_owned(), member.clone())))
        .collect()
}

fn structural_changes(
    subject: &str,
    old: &Value,
    new: &Value,
    changes: &mut Vec<DiffChange>,
    advice: &mut Vec<String>,
) -> bool {
    let mut local = Vec::new();
    let mut local_advice = Vec::new();
    let mut recognized = false;
    for (field, added_kind, removed_kind, label) in [
        (
            "parameters",
            DiffKind::RequiredParameterAdded,
            DiffKind::RequiredParameterRemoved,
            "required parameter",
        ),
        (
            "fields",
            DiffKind::FieldAdded,
            DiffKind::FieldRemoved,
            "field",
        ),
        (
            "variants",
            DiffKind::EnumVariantAdded,
            DiffKind::EnumVariantRemoved,
            "enum variant",
        ),
    ] {
        let Some(before) = named_members(old, field) else {
            continue;
        };
        let Some(after) = named_members(new, field) else {
            return false;
        };
        for name in before.keys().filter(|name| !after.contains_key(*name)) {
            recognized = true;
            let member = format!("{subject}.{name}");
            push_change(
                &mut local,
                DiffClass::Breaking,
                removed_kind,
                &member,
                format!("{member} {label} was removed"),
            );
            local_advice.push(format!("Remove uses of the removed {label} `{name}`."));
        }
        for name in after.keys().filter(|name| !before.contains_key(*name)) {
            recognized = true;
            let member = format!("{subject}.{name}");
            push_change(
                &mut local,
                DiffClass::Breaking,
                added_kind,
                &member,
                format!("{member} {label} was added"),
            );
            local_advice.push(format!("Supply or handle the new {label} `{name}`."));
        }
        for (name, before) in &before {
            if let Some(after) = after.get(name) {
                if normalized_declaration(before) != normalized_declaration(after) {
                    return false;
                }
            }
        }
    }
    if !recognized {
        return false;
    }
    let mut old_rest = normalized_declaration(old);
    let mut new_rest = normalized_declaration(new);
    for field in ["parameters", "fields", "variants"] {
        old_rest
            .as_object_mut()
            .and_then(|value| value.remove(field));
        new_rest
            .as_object_mut()
            .and_then(|value| value.remove(field));
    }
    if old_rest != new_rest {
        return false;
    }
    changes.extend(local);
    advice.extend(local_advice);
    true
}

fn compare_symbols(
    old: &BTreeMap<String, Vec<String>>,
    new: &BTreeMap<String, Vec<String>>,
    changes: &mut Vec<DiffChange>,
) {
    for module in old
        .keys()
        .chain(new.keys())
        .cloned()
        .collect::<BTreeSet<_>>()
    {
        let before = old
            .get(&module)
            .into_iter()
            .flatten()
            .cloned()
            .collect::<BTreeSet<_>>();
        let after = new
            .get(&module)
            .into_iter()
            .flatten()
            .cloned()
            .collect::<BTreeSet<_>>();
        for symbol in before.difference(&after) {
            let subject = format!("{module}.{symbol}");
            push_change(
                changes,
                DiffClass::Breaking,
                DiffKind::KotlinSymbolRemoved,
                &subject,
                format!("{subject} Kotlin symbol was removed"),
            );
        }
        for symbol in after.difference(&before) {
            let subject = format!("{module}.{symbol}");
            push_change(
                changes,
                DiffClass::Additive,
                DiffKind::KotlinSymbolAdded,
                &subject,
                format!("{subject} Kotlin symbol was added"),
            );
        }
    }
}

fn compare_implementations(
    old: &[KotlinBindingRecord],
    new: &[KotlinBindingRecord],
    changes: &mut Vec<DiffChange>,
) {
    let old = old
        .iter()
        .map(|value| (&value.cott_symbol, value))
        .collect::<BTreeMap<_, _>>();
    let new = new
        .iter()
        .map(|value| (&value.cott_symbol, value))
        .collect::<BTreeMap<_, _>>();
    for symbol in old
        .keys()
        .chain(new.keys())
        .cloned()
        .collect::<BTreeSet<_>>()
    {
        if old.get(symbol) != new.get(symbol) {
            push_change(
                changes,
                DiffClass::Implementation,
                DiffKind::ImplementationChanged,
                symbol,
                format!("{symbol} Kotlin implementation identity changed"),
            );
        }
    }
}

fn compare_inputs(
    old: &BTreeMap<String, String>,
    new: &BTreeMap<String, String>,
    changes: &mut Vec<DiffChange>,
) {
    for path in old
        .keys()
        .chain(new.keys())
        .cloned()
        .collect::<BTreeSet<_>>()
    {
        if old.get(&path) == new.get(&path) || path.ends_with(".cott") || path.ends_with(".kt") {
            continue;
        }
        let class = if path.ends_with(".jar") {
            DiffClass::Dependency
        } else {
            DiffClass::Implementation
        };
        let kind = if class == DiffClass::Dependency {
            DiffKind::DependencyChanged
        } else {
            DiffKind::InputChanged
        };
        push_change(changes, class, kind, &path, format!("{path} input changed"));
    }
}

fn compare_maps(
    label: &str,
    old: &Value,
    new: &Value,
    class: DiffClass,
    kind: DiffKind,
    changes: &mut Vec<DiffChange>,
) {
    let before = old.as_object();
    let after = new.as_object();
    for name in before
        .into_iter()
        .flat_map(|map| map.keys())
        .chain(after.into_iter().flat_map(|map| map.keys()))
        .cloned()
        .collect::<BTreeSet<_>>()
    {
        if before.and_then(|map| map.get(&name)) != after.and_then(|map| map.get(&name)) {
            push_change(
                changes,
                class,
                kind,
                &name,
                format!("{name} {label} metadata changed"),
            );
        }
    }
}

fn compare_path_maps(
    old: &BTreeMap<String, String>,
    new: &BTreeMap<String, String>,
    class: DiffClass,
    kind: DiffKind,
    changes: &mut Vec<DiffChange>,
) {
    for path in old
        .keys()
        .chain(new.keys())
        .cloned()
        .collect::<BTreeSet<_>>()
    {
        if old.get(&path) != new.get(&path) {
            push_change(
                changes,
                class,
                kind,
                &path,
                format!("{path} artifact changed"),
            );
        }
    }
}

fn version_bump_is_sufficient(
    baseline: ApiVersion,
    current: ApiVersion,
    required: VersionBump,
) -> bool {
    match required {
        VersionBump::None => true,
        VersionBump::Minor if baseline.major == 0 => {
            current.major > 0 || current.minor > baseline.minor
        }
        VersionBump::Minor => {
            current.major > baseline.major
                || current.major == baseline.major && current.minor > baseline.minor
        }
        VersionBump::Major => current.major > baseline.major,
    }
}

fn print_diff(report: &DiffReport) {
    if report.changes.is_empty() {
        println!("NO CHANGE");
        return;
    }
    for class in [
        DiffClass::Breaking,
        DiffClass::Additive,
        DiffClass::Documentation,
        DiffClass::Implementation,
        DiffClass::Dependency,
        DiffClass::Toolchain,
        DiffClass::Artifact,
        DiffClass::VersionIncompatible,
    ] {
        let selected = report
            .changes
            .iter()
            .filter(|change| change.class == class)
            .collect::<Vec<_>>();
        if selected.is_empty() {
            continue;
        }
        println!(
            "{}:",
            match class {
                DiffClass::Breaking => "CONTRACT BREAKING",
                DiffClass::Additive => "CONTRACT NON-BREAKING",
                DiffClass::Documentation => "DOCUMENTATION",
                DiffClass::Implementation => "IMPLEMENTATION",
                DiffClass::Dependency => "DEPENDENCY",
                DiffClass::Toolchain => "TOOLCHAIN",
                DiffClass::Artifact => "ARTIFACT",
                DiffClass::VersionIncompatible => "VERSION INCOMPATIBLE",
            }
        );
        for change in selected {
            println!("- {}", change.message);
        }
    }
    if !report.advice.is_empty() {
        println!("MIGRATION ADVICE:");
        for advice in &report.advice {
            println!("- {advice}");
        }
    }
}

#[cfg(test)]
#[test]
fn frozen_generator_rules_drift_preserves_published_snapshot() {
    struct TempRoot(PathBuf);
    impl Drop for TempRoot {
        fn drop(&mut self) {
            let _ = fs::remove_dir_all(&self.0);
        }
    }

    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("system clock")
        .as_nanos();
    let root = TempRoot(std::env::temp_dir().join(format!(
        "cott-kotlin-rules-drift-{}-{nonce}",
        std::process::id()
    )));
    fs::create_dir(&root.0).expect("temporary project");
    fs::create_dir_all(root.0.join("src/demo")).expect("contract source directory");
    fs::create_dir(root.0.join("kotlin")).expect("Kotlin source directory");
    fs::write(
        root.0.join("cott.toml"),
        r#"[project]
name = "demo"
version = "0.1.0"
source = "src"

[target.kotlin]
source = "kotlin"
generated = "generated/kotlin"
runtime_validation = "boundary"

[generator]
rules = "GENERATOR_RULES.txt"
"#,
    )
    .expect("Kotlin manifest");
    fs::write(
        root.0.join("src/demo/main.cott"),
        "module demo.main\n\nfn run(value: I32) -> I32\n",
    )
    .expect("contract source");
    let rules_path = root.0.join("GENERATOR_RULES.txt");
    fs::write(
        &rules_path,
        "cott-domain demo.main.run return: preserve the value\n",
    )
    .expect("initial generator rules");
    emit(Some(root.0.clone()), false).expect("initial unresolved snapshot");

    let project = load(Some(root.0.clone()), false).expect("frozen project inputs");
    let before = collect_tree_if_present(&project.paths.artifact_root).expect("published snapshot");
    let revised_rules = "cott-domain demo.main.run return: increment the value\n";
    fs::write(&rules_path, revised_rules).expect("concurrent generator rules edit");
    let error = publish(
        &project,
        &project.bindings,
        &[],
        &BTreeSet::from(["demo.main.run".to_owned()]),
        None,
        false,
    )
    .expect_err("changed frozen rules must prevent publication");
    assert_eq!(error.code, 6, "{}", error.message);
    assert_eq!(
        collect_tree_if_present(&project.paths.artifact_root).expect("preserved snapshot"),
        before,
        "input drift must not alter any published artifact"
    );
    assert_eq!(
        fs::read_to_string(&rules_path).expect("concurrent edit"),
        revised_rules,
        "publication must not overwrite the concurrent authoring change"
    );
}
