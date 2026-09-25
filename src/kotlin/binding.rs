use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, OpenOptions};
use std::io::Read;
use std::os::unix::fs::{MetadataExt, OpenOptionsExt};
use std::path::{Component, Path, PathBuf};

use tree_sitter::{Node, Parser, Tree};

use crate::hash::sha256_hex;
use crate::intent;
use crate::manifest::KotlinProjectConfig;
use crate::project::{KotlinPaths, discover_kotlin_sources};

use super::emit::implementation_signature;
use super::provenance::{KotlinBindingRecord, KotlinGenerationRecord};
use super::{KotlinBinding, KotlinCallable, KotlinOwner, KotlinPlan};

const PROCESS_EXIT_RUNTIME_TARGET: &str = "cott_runtime.CottRuntime.exitWithCode";

#[derive(Clone, Debug)]
struct SourceIndex {
    package: Option<String>,
    functions: Vec<String>,
}

#[derive(Clone, Debug)]
struct SelectedBinding {
    callable: KotlinCallable,
    target_symbol: String,
    source: PathBuf,
    source_origin: PathBuf,
    runtime_origin: PathBuf,
    owner: KotlinOwner,
}

#[derive(Clone, Debug)]
struct ExpectedFunction<'a> {
    target_symbol: &'a str,
    signature: String,
    allows_process_exit: bool,
}

fn declaration_allows_process_exit(declaration: &serde_json::Value) -> bool {
    declaration
        .get("effects")
        .or_else(|| {
            declaration
                .get("contract")
                .and_then(|contract| contract.get("effects"))
        })
        .and_then(serde_json::Value::as_array)
        .into_iter()
        .flatten()
        .any(|effect| {
            effect
                .get("key")
                .and_then(serde_json::Value::as_str)
                .or_else(|| effect.as_str())
                == Some("process.exit")
        })
}

/// Resolves every canonical Kotlin callable to one source whose syntax, ABI,
/// ownership, and durable identity have all been checked.
/// `generator_rules` must be the exact configured text frozen by project loading.
pub fn resolve(
    config: &KotlinProjectConfig,
    paths: &KotlinPaths,
    plan: &KotlinPlan,
    generator_rules: Option<&str>,
) -> Result<Vec<KotlinBinding>, String> {
    resolve_with_record(config, paths, plan, generator_rules, None)
}

/// Emit alone may pass the previously authenticated legacy baseline. Other
/// callers must load the strict current-schema record from disk.
pub(crate) fn resolve_for_emit(
    config: &KotlinProjectConfig,
    paths: &KotlinPaths,
    plan: &KotlinPlan,
    generator_rules: Option<&str>,
    legacy_baseline: &KotlinGenerationRecord,
) -> Result<Vec<KotlinBinding>, String> {
    resolve_with_record(config, paths, plan, generator_rules, Some(legacy_baseline))
}

fn resolve_with_record(
    config: &KotlinProjectConfig,
    paths: &KotlinPaths,
    plan: &KotlinPlan,
    generator_rules: Option<&str>,
    legacy_baseline: Option<&KotlinGenerationRecord>,
) -> Result<Vec<KotlinBinding>, String> {
    let callables = callable_index(plan)?;
    validate_manifest_bindings(config, paths, plan, &callables)?;

    let sources = discover_kotlin_sources(&paths.kotlin_source_dir).map_err(|error| {
        format!(
            "{}: unable to discover Kotlin implementation sources: {error}",
            paths.kotlin_source_dir.display()
        )
    })?;
    let mut source_indexes = BTreeMap::new();
    for source in &sources {
        let index = index_source(&source.source)
            .map_err(|message| path_error(&source.disk_path, &message))?;
        source_indexes.insert(source.disk_path.clone(), index);
    }

    let generation_path = paths.artifact_root.join("generation.json");
    let record = match legacy_baseline {
        Some(record) => Some(record.clone()),
        None => load_generation_record(&generation_path)?,
    };
    if let Some(record) = &record
        && record.current.project_name != config.project.name
    {
        return Err(path_error(
            &generation_path,
            "Kotlin generation provenance belongs to a different project identity",
        ));
    }
    let rules = match (&config.generator.rules, generator_rules) {
        (Some(_), Some(rules)) => rules.as_bytes(),
        (None, None) => &[],
        (Some(relative), None) => {
            return Err(path_error(
                &paths.root.join(relative),
                "configured Kotlin generator rules were not supplied to binding resolution",
            ));
        }
        (None, Some(_)) => {
            return Err(path_error(
                &paths.manifest,
                "binding resolution received generator rules that are not configured",
            ));
        }
    };
    let current_intent = intent::fingerprints(&plan.contract_surface(), rules)
        .map_err(|message| format!("Kotlin implementation intent: {message}"))?;
    let baseline_intent = record
        .as_ref()
        .map(|record| recorded_intent(record, config, paths, rules))
        .transpose()?;

    let private_targets = declared_private_targets(config, plan)?;

    let generated_prefix = paths
        .generated_dir
        .strip_prefix(&paths.artifact_root)
        .map_err(|_| {
            format!(
                "{}: Kotlin generated directory is outside the artifact root {}",
                paths.generated_dir.display(),
                paths.artifact_root.display()
            )
        })?;
    if !safe_relative(generated_prefix) {
        return Err(format!(
            "{}: Kotlin generated directory has an unsafe artifact-relative path",
            paths.generated_dir.display()
        ));
    }

    let mut selected = Vec::new();
    let mut expected_agent_files = BTreeSet::new();
    let mut retired_agent_files = BTreeSet::new();
    for callable in callables.values() {
        if compiler_owned(callable) {
            continue;
        }
        let agent_relative = agent_relative_path(callable)?;
        let runtime_origin = generated_prefix.join(&agent_relative);
        let agent_source = paths.kotlin_source_dir.join(&agent_relative);
        let selection = if let Some(target) = config.kotlin.implementations.get(&callable.symbol) {
            let (target_symbol, package, function) = parse_target_symbol(target)?;
            let matches = sources
                .iter()
                .filter(|source| {
                    source_indexes.get(&source.disk_path).is_some_and(|index| {
                        index.package.as_deref() == Some(package.as_str())
                            && index.functions.iter().any(|name| name == &function)
                    })
                })
                .collect::<Vec<_>>();
            if matches.len() != 1 {
                return Err(path_error(
                    &paths.manifest,
                    &format!(
                        "implementation binding `{}` = `{target}` resolved to {} top-level declarations; expected exactly one",
                        callable.symbol,
                        matches.len()
                    ),
                ));
            }
            let source = matches[0];
            SelectedBinding {
                callable: callable.clone(),
                target_symbol,
                source: source.disk_path.clone(),
                source_origin: project_relative(&paths.root, &source.disk_path)?,
                runtime_origin,
                owner: KotlinOwner::Manifest,
            }
        } else {
            expected_agent_files.insert(agent_source.clone());
            let target_symbol = agent_target_symbol(callable)?;
            let source = sources
                .iter()
                .find(|source| source.disk_path == agent_source);
            let Some(source) = source else {
                // Absence is unresolved. In particular, never reuse an accepted
                // record after its durable source has disappeared.
                continue;
            };
            let source_origin = project_relative(&paths.root, &source.disk_path)?;
            if !validate_agent_provenance(
                record.as_ref(),
                callable,
                &target_symbol,
                &source_origin,
                &runtime_origin,
                source.source.as_bytes(),
                &current_intent,
                baseline_intent.as_ref(),
            )? {
                // Authenticated pending or intent-stale bytes stay unresolved so
                // generate can replace them; parsing them must not refresh trust.
                continue;
            }
            SelectedBinding {
                callable: callable.clone(),
                target_symbol,
                source: source.disk_path.clone(),
                source_origin,
                runtime_origin,
                owner: KotlinOwner::Agent,
            }
        };
        selected.push(selection);
    }

    for source in &sources {
        let relative = source
            .disk_path
            .strip_prefix(&paths.kotlin_source_dir)
            .unwrap_or(&source.path);
        if relative.starts_with("cott_impl") && !expected_agent_files.contains(&source.disk_path) {
            if retired_agent_source_is_authenticated(
                record.as_ref(),
                &callables,
                paths,
                &source.disk_path,
                source.source.as_bytes(),
            )? {
                retired_agent_files.insert(source.disk_path.clone());
                continue;
            }
            return Err(path_error(
                &source.disk_path,
                "stale or manifest-shadowed durable Kotlin implementation is not owned by the current plan",
            ));
        }
    }

    let no_reserved_identifiers = BTreeSet::new();
    for source in &sources {
        if retired_agent_files.contains(&source.disk_path) {
            continue;
        }
        audit_source(
            &source.source,
            &private_targets,
            false,
            false,
            &no_reserved_identifiers,
            None,
        )
        .map_err(|message| path_error(&source.disk_path, &message))?;
    }

    let mut by_source = BTreeMap::<PathBuf, Vec<usize>>::new();
    for (index, binding) in selected.iter().enumerate() {
        by_source
            .entry(binding.source.clone())
            .or_default()
            .push(index);
    }
    for (source_path, indexes) in &by_source {
        let source = sources
            .iter()
            .find(|source| &source.disk_path == source_path)
            .ok_or_else(|| path_error(source_path, "selected Kotlin source disappeared"))?;
        if indexes.len() != 1 {
            return Err(path_error(
                source_path,
                "one Kotlin source file must own exactly one canonical implementation function",
            ));
        }
        let mut expected = Vec::new();
        for index in indexes {
            let selected = &selected[*index];
            expected.push(ExpectedFunction {
                target_symbol: &selected.target_symbol,
                signature: implementation_signature(plan, &selected.callable).map_err(|message| {
                    path_error(
                        source_path,
                        &format!(
                            "cannot render canonical implementation signature for `{}`: {message}",
                            selected.callable.symbol
                        ),
                    )
                })?,
                allows_process_exit: declaration_allows_process_exit(
                    &selected.callable.declaration,
                ),
            });
        }
        validate_restricted_source(&source.source, &expected, &private_targets)
            .map_err(|message| path_error(source_path, &message))?;
    }

    let mut bindings = Vec::with_capacity(selected.len());
    for selected in selected {
        let source = sources
            .iter()
            .find(|source| source.disk_path.as_path() == selected.source.as_path())
            .ok_or_else(|| path_error(&selected.source, "selected Kotlin source disappeared"))?;
        let bytes = source.source.as_bytes().to_vec();
        bindings.push(KotlinBinding {
            cott_symbol: selected.callable.symbol,
            target_symbol: selected.target_symbol,
            source_origin: selected.source_origin,
            runtime_origin: selected.runtime_origin,
            content_hash: format!("sha256:{}", sha256_hex(&bytes)),
            bytes,
            owner: selected.owner,
        });
    }
    bindings.sort_by(|left, right| left.cott_symbol.cmp(&right.cott_symbol));
    Ok(bindings)
}

/// Validates a newly generated durable source. This proves only source shape
/// and binding compatibility; compiler and contract verification remain a
/// separate pipeline state.
pub fn validate_candidate(
    config: &KotlinProjectConfig,
    plan: &KotlinPlan,
    callable: &KotlinCallable,
    bytes: &[u8],
) -> Result<(), String> {
    let source = std::str::from_utf8(bytes)
        .map_err(|_| "Kotlin candidate source is not valid UTF-8".to_owned())?;
    let planned = plan
        .callables()
        .into_iter()
        .filter(|candidate| candidate.symbol == callable.symbol)
        .collect::<Vec<_>>();
    if planned.len() != 1 || planned[0] != *callable {
        return Err(format!(
            "Kotlin candidate callable `{}` is not the unique canonical callable in the plan",
            callable.symbol
        ));
    }
    if compiler_owned(callable) {
        return Err(format!(
            "compiler-owned selected method `{}` does not accept a Kotlin candidate",
            callable.symbol
        ));
    }
    let target_symbol = agent_target_symbol(callable)?;
    let private_targets = declared_private_targets(config, plan)?;
    let expected = [ExpectedFunction {
        target_symbol: &target_symbol,
        signature: implementation_signature(plan, callable).map_err(|message| {
            format!(
                "cannot render canonical implementation signature for `{}`: {message}",
                callable.symbol
            )
        })?,
        allows_process_exit: declaration_allows_process_exit(&callable.declaration),
    }];
    validate_restricted_source(source, &expected, &private_targets)
}

fn callable_index(plan: &KotlinPlan) -> Result<BTreeMap<String, KotlinCallable>, String> {
    let mut callables = BTreeMap::new();
    for callable in plan.callables() {
        if callables
            .insert(callable.symbol.clone(), callable.clone())
            .is_some()
        {
            return Err(format!(
                "Kotlin plan contains duplicate callable `{}`",
                callable.symbol
            ));
        }
    }
    Ok(callables)
}

fn validate_manifest_bindings(
    config: &KotlinProjectConfig,
    paths: &KotlinPaths,
    plan: &KotlinPlan,
    callables: &BTreeMap<String, KotlinCallable>,
) -> Result<(), String> {
    let public_packages = plan
        .modules
        .iter()
        .map(|module| module.name.as_str())
        .collect::<BTreeSet<_>>();
    let mut targets = BTreeMap::<String, &String>::new();
    for (symbol, target) in &config.kotlin.implementations {
        let Some(callable) = callables.get(symbol) else {
            return Err(path_error(
                &paths.manifest,
                &format!("implementation binding key `{symbol}` is not a canonical callable"),
            ));
        };
        if compiler_owned(callable) {
            return Err(path_error(
                &paths.manifest,
                &format!(
                    "implementation binding key `{symbol}` names a compiler-owned selected method"
                ),
            ));
        }
        let (normalized, package, _) =
            parse_target_symbol(target).map_err(|message| path_error(&paths.manifest, &message))?;
        if package == "cott_impl" || package.starts_with("cott_impl.") {
            return Err(path_error(
                &paths.manifest,
                &format!(
                    "manifest implementation `{symbol}` must not claim the agent-owned package `cott_impl`"
                ),
            ));
        }
        if package == "cott_runtime"
            || package.starts_with("cott_runtime.")
            || public_packages
                .iter()
                .any(|public| *public == package.as_str())
        {
            return Err(path_error(
                &paths.manifest,
                &format!(
                    "manifest implementation `{symbol}` targets reserved generated package `{package}`"
                ),
            ));
        }
        if let Some(previous) = targets.insert(normalized.clone(), symbol) {
            return Err(path_error(
                &paths.manifest,
                &format!(
                    "manifest implementations `{previous}` and `{symbol}` both claim `{normalized}`"
                ),
            ));
        }
    }
    Ok(())
}

pub(crate) fn requires_binding(callable: &KotlinCallable) -> bool {
    !(callable.owner.is_some()
        && matches!(
            callable
                .declaration
                .get("selected")
                .and_then(|selected| selected.get("origin"))
                .and_then(serde_json::Value::as_str),
            Some("default" | "specialization")
        ))
}

fn compiler_owned(callable: &KotlinCallable) -> bool {
    !requires_binding(callable)
}

fn concrete_name(callable: &KotlinCallable) -> Result<Option<String>, String> {
    callable
        .owner
        .as_ref()
        .map(|owner| {
            owner
                .get("name")
                .and_then(serde_json::Value::as_str)
                .and_then(|name| name.rsplit('.').next())
                .filter(|name| valid_cott_identifier(name))
                .map(str::to_owned)
                .ok_or_else(|| {
                    format!(
                        "Kotlin callable `{}` has a malformed implementation owner",
                        callable.symbol
                    )
                })
        })
        .transpose()
}

fn declared_private_targets(
    config: &KotlinProjectConfig,
    plan: &KotlinPlan,
) -> Result<BTreeSet<String>, String> {
    let mut targets = config
        .kotlin
        .implementations
        .values()
        .map(|target| parse_target_symbol(target).map(|parsed| parsed.0))
        .collect::<Result<BTreeSet<_>, _>>()?;
    for callable in plan
        .callables()
        .into_iter()
        .filter(|callable| !compiler_owned(callable))
    {
        if !config.kotlin.implementations.contains_key(&callable.symbol) {
            targets.insert(agent_target_symbol(&callable)?);
        }
    }
    Ok(targets)
}

fn agent_relative_path(callable: &KotlinCallable) -> Result<PathBuf, String> {
    let mut path = PathBuf::from("cott_impl");
    for segment in cott_segments(&callable.module)? {
        path.push(segment);
    }
    if let Some(concrete) = concrete_name(callable)? {
        path.push(concrete);
    }
    if !valid_cott_identifier(&callable.name) {
        return Err(format!(
            "Kotlin callable `{}` has invalid function name `{}`",
            callable.symbol, callable.name
        ));
    }
    path.push(format!("{}.kt", callable.name));
    Ok(path)
}
pub(crate) fn agent_source_origin(
    paths: &KotlinPaths,
    callable: &KotlinCallable,
) -> Result<PathBuf, String> {
    project_relative(
        &paths.root,
        &paths.kotlin_source_dir.join(agent_relative_path(callable)?),
    )
}

pub(crate) fn candidate_binding(
    paths: &KotlinPaths,
    callable: &KotlinCallable,
    bytes: Vec<u8>,
) -> Result<KotlinBinding, String> {
    let generated_prefix = paths
        .generated_dir
        .strip_prefix(&paths.artifact_root)
        .map_err(|_| {
            format!(
                "{}: Kotlin generated directory is outside the artifact root {}",
                paths.generated_dir.display(),
                paths.artifact_root.display()
            )
        })?;
    if !safe_relative(generated_prefix) {
        return Err(format!(
            "{}: Kotlin generated directory has an unsafe artifact-relative path",
            paths.generated_dir.display()
        ));
    }
    Ok(KotlinBinding {
        cott_symbol: callable.symbol.clone(),
        target_symbol: agent_target_symbol(callable)?,
        source_origin: agent_source_origin(paths, callable)?,
        runtime_origin: generated_prefix.join(agent_relative_path(callable)?),
        content_hash: format!("sha256:{}", sha256_hex(&bytes)),
        bytes,
        owner: KotlinOwner::Agent,
    })
}

fn agent_target_symbol(callable: &KotlinCallable) -> Result<String, String> {
    let mut segments = vec!["cott_impl".to_owned()];
    segments.extend(
        cott_segments(&callable.module)?
            .into_iter()
            .map(str::to_owned),
    );
    if let Some(concrete) = concrete_name(callable)? {
        segments.push(concrete);
    }
    if !valid_cott_identifier(&callable.name) {
        return Err(format!(
            "Kotlin callable `{}` has invalid function name `{}`",
            callable.symbol, callable.name
        ));
    }
    segments.push(callable.name.clone());
    Ok(segments.join("."))
}

fn parse_target_symbol(target: &str) -> Result<(String, String, String), String> {
    if !crate::manifest::valid_kotlin_fqn(target) {
        return Err(format!("invalid Kotlin qualified name `{target}`"));
    }
    let segments = target.split('.').collect::<Vec<_>>();
    let function = segments[segments.len() - 1].to_owned();
    let package = segments[..segments.len() - 1].join(".");
    Ok((target.to_owned(), package, function))
}

fn cott_segments(value: &str) -> Result<Vec<&str>, String> {
    let segments = value.split('.').collect::<Vec<_>>();
    if segments.is_empty()
        || segments
            .iter()
            .any(|segment| !valid_cott_identifier(segment))
    {
        return Err(format!("invalid canonical qualified name `{value}`"));
    }
    Ok(segments)
}

fn valid_cott_identifier(value: &str) -> bool {
    let mut bytes = value.bytes();
    bytes
        .next()
        .is_some_and(|byte| byte == b'_' || byte.is_ascii_alphabetic())
        && bytes.all(|byte| byte == b'_' || byte.is_ascii_alphanumeric())
}

fn project_relative(root: &Path, path: &Path) -> Result<PathBuf, String> {
    let relative = path.strip_prefix(root).map_err(|_| {
        path_error(
            path,
            &format!(
                "implementation path escaped project root {}",
                root.display()
            ),
        )
    })?;
    if !safe_relative(relative) {
        return Err(path_error(
            path,
            "implementation path is not a safe relative path",
        ));
    }
    Ok(relative.to_path_buf())
}

fn safe_relative(path: &Path) -> bool {
    !path.as_os_str().is_empty()
        && path.to_str().is_some()
        && path
            .components()
            .all(|component| matches!(component, Component::Normal(_)))
}

fn path_text(path: &Path) -> Result<String, String> {
    if !safe_relative(path) {
        return Err(format!(
            "unsafe Kotlin provenance path `{}`",
            path.display()
        ));
    }
    path.to_str()
        .map(|path| path.replace('\\', "/"))
        .ok_or_else(|| format!("non-UTF-8 Kotlin provenance path `{}`", path.display()))
}

fn path_error(path: &Path, message: &str) -> String {
    format!("{}: {message}", path.display())
}

fn load_generation_record(path: &Path) -> Result<Option<KotlinGenerationRecord>, String> {
    let mut file = match OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_CLOEXEC | libc::O_NOFOLLOW | libc::O_NONBLOCK)
        .open(path)
    {
        Ok(file) => file,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(None),
        Err(error) => {
            return Err(path_error(
                path,
                &format!("unable to open Kotlin generation provenance safely: {error}"),
            ));
        }
    };
    let before = file.metadata().map_err(|error| {
        path_error(
            path,
            &format!("unable to inspect opened Kotlin generation provenance: {error}"),
        )
    })?;
    if !before.is_file() || before.nlink() != 1 {
        return Err(path_error(
            path,
            "Kotlin generation provenance must be a regular non-symlink single-link file",
        ));
    }
    let mut bytes = Vec::new();
    file.read_to_end(&mut bytes).map_err(|error| {
        path_error(
            path,
            &format!("unable to read opened Kotlin generation provenance: {error}"),
        )
    })?;
    let after = file.metadata().map_err(|error| {
        path_error(
            path,
            &format!("unable to re-inspect opened Kotlin generation provenance: {error}"),
        )
    })?;
    let leaf = fs::symlink_metadata(path).map_err(|error| {
        path_error(
            path,
            &format!("unable to re-inspect Kotlin generation provenance leaf: {error}"),
        )
    })?;
    if !after.is_file()
        || after.nlink() != 1
        || !leaf.is_file()
        || leaf.file_type().is_symlink()
        || leaf.nlink() != 1
        || before.dev() != after.dev()
        || before.ino() != after.ino()
        || before.mode() != after.mode()
        || before.len() != after.len()
        || after.dev() != leaf.dev()
        || after.ino() != leaf.ino()
    {
        return Err(path_error(
            path,
            "Kotlin generation provenance changed or became unsafe while being read",
        ));
    }
    KotlinGenerationRecord::parse(&bytes)
        .map(Some)
        .map_err(|message| path_error(path, &message))
}

fn recorded_intent(
    record: &KotlinGenerationRecord,
    config: &KotlinProjectConfig,
    paths: &KotlinPaths,
    rules: &[u8],
) -> Result<BTreeMap<String, String>, String> {
    match intent::recorded_fingerprints(&record.current.tools) {
        Ok(Some(hashes)) => Ok(hashes),
        Ok(None) if !recorded_inputs_match(record, config, paths, rules) => Ok(BTreeMap::new()),
        Ok(None) => intent::fingerprints(&record.current.contract_surface, rules)
            .map_err(|message| format!("recorded Kotlin implementation intent: {message}")),
        Err(message) => Err(path_error(
            &paths.artifact_root.join("generation.json"),
            &message,
        )),
    }
}

fn recorded_inputs_match(
    record: &KotlinGenerationRecord,
    config: &KotlinProjectConfig,
    paths: &KotlinPaths,
    rules: &[u8],
) -> bool {
    let manifest_hash = fs::read(&paths.manifest)
        .ok()
        .map(|bytes| format!("sha256:{}", sha256_hex(&bytes)));
    if record.current.inputs.get("cott.toml") != manifest_hash.as_ref() {
        return false;
    }
    match &config.generator.rules {
        Some(relative) => {
            record.current.inputs.get(relative) == Some(&format!("sha256:{}", sha256_hex(rules)))
        }
        None => true,
    }
}

fn accepted_agent_record<'a>(
    record: Option<&'a KotlinGenerationRecord>,
    symbol: &str,
) -> Option<&'a KotlinBindingRecord> {
    record?
        .current
        .implementations
        .iter()
        .find(|implementation| {
            implementation.cott_symbol == symbol && implementation.owner == KotlinOwner::Agent
        })
}

fn retired_agent_source_is_authenticated(
    record: Option<&KotlinGenerationRecord>,
    callables: &BTreeMap<String, KotlinCallable>,
    paths: &KotlinPaths,
    source: &Path,
    bytes: &[u8],
) -> Result<bool, String> {
    let Some(record) = record else {
        return Ok(false);
    };
    let source_origin = project_relative(&paths.root, source)?;
    let source_text = path_text(&source_origin)?;
    let content_hash = format!("sha256:{}", sha256_hex(bytes));
    for snapshot in std::iter::once(&record.current).chain(record.last_verified.iter()) {
        let authenticated = snapshot.implementations.iter().any(|implementation| {
            implementation.owner == KotlinOwner::Agent
                && !callables.contains_key(&implementation.cott_symbol)
                && implementation.source_origin == source_text
                && implementation.content_hash == content_hash
                && snapshot.agent_runs.iter().any(|run| {
                    run.symbol == implementation.cott_symbol
                        && run.implementation_hash == content_hash
                })
        });
        if authenticated {
            return Ok(true);
        }
    }
    Ok(false)
}

#[allow(clippy::too_many_arguments)]
fn validate_agent_provenance(
    record: Option<&KotlinGenerationRecord>,
    callable: &KotlinCallable,
    target_symbol: &str,
    source_origin: &Path,
    runtime_origin: &Path,
    bytes: &[u8],
    current_intent: &BTreeMap<String, String>,
    baseline_intent: Option<&BTreeMap<String, String>>,
) -> Result<bool, String> {
    let Some(record) = record else {
        return Err(path_error(
            source_origin,
            &format!(
                "durable implementation `{}` has no matching Kotlin agent provenance",
                callable.symbol
            ),
        ));
    };
    let content_hash = format!("sha256:{}", sha256_hex(bytes));
    let source_text = path_text(source_origin)?;
    let runtime_text = path_text(runtime_origin)?;
    let recorded = accepted_agent_record(Some(record), &callable.symbol);
    let pending = record
        .current
        .unresolved
        .iter()
        .any(|symbol| symbol == &callable.symbol);
    let run_matches = record
        .current
        .agent_runs
        .iter()
        .any(|run| run.symbol == callable.symbol && run.implementation_hash == content_hash);
    let identity_matches = recorded.is_some_and(|recorded| {
        recorded.target_symbol == target_symbol
            && recorded.source_origin == source_text
            && recorded.runtime_origin == runtime_text
            && recorded.content_hash == content_hash
    });
    if !identity_matches || !run_matches {
        return Err(path_error(
            source_origin,
            &format!(
                "durable implementation `{}` does not match recorded Kotlin path, target, content identity, and ownership",
                callable.symbol
            ),
        ));
    }

    // An unresolved record takes precedence over a retained accepted identity.
    // This prevents repeated checkpoints from refreshing stale bytes merely by
    // recording the current intent metadata.
    if pending {
        return Ok(false);
    }
    let intent_matches = baseline_intent.is_some_and(|baseline| {
        current_intent.get(&callable.symbol) == baseline.get(&callable.symbol)
            && current_intent.contains_key(&callable.symbol)
    });
    if !intent_matches {
        return Ok(false);
    }
    Ok(true)
}

fn index_source(source: &str) -> Result<SourceIndex, String> {
    let tree = parse_kotlin(source)?;
    let root = tree.root_node();
    let package = source_package(root, source)?;
    let functions = top_level_functions(root)
        .into_iter()
        .map(|function| function_name(function, source))
        .collect::<Result<Vec<_>, _>>()?;
    Ok(SourceIndex { package, functions })
}

fn parse_kotlin(source: &str) -> Result<Tree, String> {
    let mut parser = Parser::new();
    parser
        .set_language(super::syntax::language()?)
        .map_err(|error| format!("unable to load Kotlin syntax grammar: {error}"))?;
    let tree = parser
        .parse(source.as_bytes(), None)
        .ok_or_else(|| "Kotlin syntax parser returned no tree".to_owned())?;
    if tree.root_node().has_error() {
        let error = first_syntax_error(tree.root_node()).unwrap_or(tree.root_node());
        let position = error.start_position();
        return Err(format!(
            "malformed Kotlin source at {}:{} near `{}`",
            position.row + 1,
            position.column + 1,
            source
                .get(error.byte_range())
                .unwrap_or(error.kind())
                .chars()
                .take(48)
                .collect::<String>()
        ));
    }
    Ok(tree)
}

fn first_syntax_error(node: Node<'_>) -> Option<Node<'_>> {
    if node.is_error() || node.is_missing() {
        return Some(node);
    }
    let mut cursor = node.walk();
    for child in node.children(&mut cursor) {
        if let Some(error) = first_syntax_error(child) {
            return Some(error);
        }
    }
    None
}

fn source_package(root: Node<'_>, source: &str) -> Result<Option<String>, String> {
    let packages = direct_named_children(root)
        .into_iter()
        .filter(|node| node.kind() == "package_header")
        .collect::<Vec<_>>();
    if packages.len() > 1 {
        return Err("Kotlin source declares more than one package".to_owned());
    }
    packages
        .first()
        .map(|package| {
            let qualified = direct_named_children(*package)
                .into_iter()
                .find(|node| node.kind() == "qualified_identifier")
                .ok_or_else(|| "Kotlin package declaration has no qualified name".to_owned())?;
            qualified_syntax(qualified, source)
        })
        .transpose()
}

fn top_level_functions(root: Node<'_>) -> Vec<Node<'_>> {
    direct_named_children(root)
        .into_iter()
        .filter(|node| node.kind() == "function_declaration")
        .collect()
}

fn direct_named_children(node: Node<'_>) -> Vec<Node<'_>> {
    let mut cursor = node.walk();
    node.named_children(&mut cursor).collect()
}

fn qualified_syntax(node: Node<'_>, source: &str) -> Result<String, String> {
    let invalid = || {
        format!(
            "invalid Kotlin qualified syntax `{}`",
            node_text(node, source)
        )
    };
    if node.kind() == "identifier" {
        return normalized_identifier(node_text(node, source)).map_err(|_| invalid());
    }
    if node.kind() != "qualified_identifier" {
        return Err(invalid());
    }

    let mut identifiers = Vec::new();
    for child in direct_named_children(node) {
        match child.kind() {
            "identifier" => identifiers
                .push(normalized_identifier(node_text(child, source)).map_err(|_| invalid())?),
            kind if is_comment(kind) => {}
            _ => return Err(invalid()),
        }
    }
    if identifiers.is_empty() {
        return Err(invalid());
    }
    Ok(identifiers.join("."))
}

struct ImportSyntax {
    target: String,
    alias: Option<String>,
    wildcard: bool,
}

fn import_syntax(node: Node<'_>, source: &str) -> Result<ImportSyntax, String> {
    if node.kind() != "import" || !node.is_named() {
        return Err("malformed Kotlin import".to_owned());
    }

    let mut target = None;
    let mut alias = None;
    for child in direct_named_children(node) {
        match child.kind() {
            "qualified_identifier" if target.is_none() => {
                target = Some(qualified_syntax(child, source)?);
            }
            "identifier" if target.is_some() && alias.is_none() => {
                alias = Some(qualified_syntax(child, source)?);
            }
            kind if is_comment(kind) => {}
            _ => return Err("malformed Kotlin import".to_owned()),
        }
    }
    let target = target.ok_or_else(|| "Kotlin import has no qualified name".to_owned())?;

    let mut cursor = node.walk();
    let wildcard = node
        .children(&mut cursor)
        .any(|child| !child.is_named() && child.kind() == "*");
    if wildcard && alias.is_some() {
        return Err("malformed Kotlin import".to_owned());
    }

    Ok(ImportSyntax {
        target,
        alias,
        wildcard,
    })
}

fn normalized_identifier(value: &str) -> Result<String, String> {
    let value = value
        .strip_prefix('`')
        .and_then(|value| value.strip_suffix('`'))
        .unwrap_or(value);
    valid_kotlin_identifier(value)
        .then(|| value.to_owned())
        .ok_or_else(|| format!("unsupported Kotlin identifier `{value}`"))
}

fn valid_kotlin_identifier(value: &str) -> bool {
    let mut characters = value.chars();
    characters
        .next()
        .is_some_and(|character| character == '_' || character.is_alphabetic())
        && characters.all(|character| character == '_' || character.is_alphanumeric())
}

fn function_name(node: Node<'_>, source: &str) -> Result<String, String> {
    let name = node
        .child_by_field_name("name")
        .ok_or_else(|| "Kotlin function has no name".to_owned())?;
    normalized_identifier(node_text(name, source))
}

fn audit_source(
    source: &str,
    private_targets: &BTreeSet<String>,
    implementation_rules: bool,
    allows_process_exit: bool,
    allowed_reserved_identifiers: &BTreeSet<String>,
    reserved_identifier_owner: Option<&str>,
) -> Result<(), String> {
    let tree = parse_kotlin(source)?;
    let root = tree.root_node();
    let package = source_package(root, source)?;
    let imports = import_index(root, source)?;
    let local_functions = top_level_functions(root)
        .into_iter()
        .map(|function| {
            let name = function_name(function, source)?;
            Ok(match &package {
                Some(package) => format!("{package}.{name}"),
                None => name,
            })
        })
        .collect::<Result<BTreeSet<_>, String>>()?;
    let exit_reaching_local_functions = local_exit_reaching_functions(
        root,
        source,
        package.as_deref(),
        &imports,
        private_targets,
        &local_functions,
    )?;
    let mut errors = Vec::new();
    audit_node(
        root,
        source,
        package.as_deref(),
        &imports,
        private_targets,
        &local_functions,
        &exit_reaching_local_functions,
        None,
        implementation_rules,
        allows_process_exit,
        allowed_reserved_identifiers,
        reserved_identifier_owner,
        &mut errors,
    );
    if errors.is_empty() {
        Ok(())
    } else {
        Err(errors.join("; "))
    }
}

fn import_index(root: Node<'_>, source: &str) -> Result<BTreeMap<String, String>, String> {
    let mut imports = BTreeMap::new();
    for import in direct_named_children(root)
        .into_iter()
        .filter(|node| node.kind() == "import")
    {
        let import = import_syntax(import, source)?;
        if import.wildcard {
            continue;
        }
        let name = import.alias.unwrap_or_else(|| {
            import
                .target
                .rsplit('.')
                .next()
                .unwrap_or(&import.target)
                .to_owned()
        });
        if imports
            .insert(name.clone(), import.target.clone())
            .is_some()
        {
            return Err(format!("duplicate or shadowed Kotlin import name `{name}`"));
        }
    }
    Ok(imports)
}

fn collect_resolved_call_targets(
    node: Node<'_>,
    source: &str,
    package: Option<&str>,
    imports: &BTreeMap<String, String>,
    private_targets: &BTreeSet<String>,
    local_functions: &BTreeSet<String>,
    targets: &mut BTreeSet<String>,
) {
    if node.kind() == "call_expression"
        && let Some(callee) = direct_named_children(node).first().copied()
        && let Some(reference) = reference_path(callee, source)
    {
        targets.insert(resolve_reference(
            &reference,
            package,
            imports,
            private_targets,
            local_functions,
        ));
    }
    let mut cursor = node.walk();
    for child in node.children(&mut cursor) {
        collect_resolved_call_targets(
            child,
            source,
            package,
            imports,
            private_targets,
            local_functions,
            targets,
        );
    }
}

fn local_exit_reaching_functions(
    root: Node<'_>,
    source: &str,
    package: Option<&str>,
    imports: &BTreeMap<String, String>,
    private_targets: &BTreeSet<String>,
    local_functions: &BTreeSet<String>,
) -> Result<BTreeSet<String>, String> {
    let mut callers = BTreeMap::<String, BTreeSet<String>>::new();
    let mut exit_reaching = BTreeSet::new();
    for function in top_level_functions(root) {
        let name = function_name(function, source)?;
        let owner = package.map_or(name.clone(), |package| format!("{package}.{name}"));
        let mut targets = BTreeSet::new();
        collect_resolved_call_targets(
            function,
            source,
            package,
            imports,
            private_targets,
            local_functions,
            &mut targets,
        );
        for target in targets {
            if target == PROCESS_EXIT_RUNTIME_TARGET {
                exit_reaching.insert(owner.clone());
            } else if local_functions.contains(&target) {
                callers.entry(target).or_default().insert(owner.clone());
            }
        }
    }

    let mut pending = exit_reaching.iter().cloned().collect::<Vec<_>>();
    while let Some(callee) = pending.pop() {
        let Some(dependents) = callers.get(&callee) else {
            continue;
        };
        for caller in dependents {
            if exit_reaching.insert(caller.clone()) {
                pending.push(caller.clone());
            }
        }
    }
    Ok(exit_reaching)
}

#[allow(clippy::too_many_arguments)]
fn audit_node(
    node: Node<'_>,
    source: &str,
    package: Option<&str>,
    imports: &BTreeMap<String, String>,
    private_targets: &BTreeSet<String>,
    local_functions: &BTreeSet<String>,
    exit_reaching_local_functions: &BTreeSet<String>,
    current_function: Option<&str>,
    implementation_rules: bool,
    allows_process_exit: bool,
    allowed_reserved_identifiers: &BTreeSet<String>,
    reserved_identifier_owner: Option<&str>,
    errors: &mut Vec<String>,
) {
    let current_function = if node.kind() == "function_declaration"
        && current_function.is_some()
        && is_anonymous_object_member(node)
    {
        current_function.map(str::to_owned)
    } else if node.kind() == "function_declaration" {
        function_name(node, source).ok().map(|name| match package {
            Some(package) => format!("{package}.{name}"),
            None => name,
        })
    } else {
        current_function.map(str::to_owned)
    };
    let current = current_function.as_deref();

    match node.kind() {
        "line_comment" | "block_comment" => {
            if implementation_rules {
                let comment = node_text(node, source).to_ascii_lowercase();
                if comment.contains("noinspection") || comment.contains("suppress(") {
                    push_error(
                        errors,
                        "Kotlin source suppression comments are not allowed".to_owned(),
                    );
                }
            }
            return;
        }
        "file_annotation" if implementation_rules => push_error(
            errors,
            "Kotlin file annotations are not allowed in implementation sources".to_owned(),
        ),
        "annotation" if implementation_rules => {
            let annotation = compact_node(node, source);
            if annotation.contains("Suppress") || annotation.contains("SuppressWarnings") {
                push_error(
                    errors,
                    format!("Kotlin suppression `{annotation}` is not allowed"),
                );
            }
        }
        "import" if node.is_named() => audit_import(
            node,
            source,
            private_targets,
            implementation_rules,
            allows_process_exit,
            errors,
        ),
        "callable_reference" => audit_callable_reference(
            node,
            source,
            package,
            imports,
            private_targets,
            local_functions,
            exit_reaching_local_functions,
            current,
            implementation_rules,
            allows_process_exit,
            errors,
        ),
        "navigation_expression" if compact_node(node, source).contains("::") => {
            audit_callable_reference(
                node,
                source,
                package,
                imports,
                private_targets,
                local_functions,
                exit_reaching_local_functions,
                current,
                implementation_rules,
                allows_process_exit,
                errors,
            )
        }
        "navigation_expression" if implementation_rules => {
            let compact = compact_node(node, source);
            if reference_path(node, source)
                .map(|path| {
                    resolve_reference(&path, package, imports, private_targets, local_functions)
                })
                .as_deref()
                .is_some_and(|reference| {
                    forbidden_kotlin_capability(reference, allows_process_exit)
                })
                || reference_path(node, source)
                    .as_deref()
                    .is_some_and(|reference| {
                        reference
                            .rsplit('.')
                            .next()
                            .is_some_and(reserved_cott_runtime_control)
                    })
                || forbidden_kotlin_capability(&compact, allows_process_exit)
                || invalid_cott_runtime_object_use(
                    node,
                    source,
                    package,
                    imports,
                    private_targets,
                    local_functions,
                    allows_process_exit,
                )
            {
                push_error(
                    errors,
                    format!(
                        "Kotlin process or verifier-control capability `{compact}` is not allowed"
                    ),
                );
            }
        }
        "call_expression" => audit_call(
            node,
            source,
            package,
            imports,
            private_targets,
            local_functions,
            exit_reaching_local_functions,
            current,
            implementation_rules,
            allows_process_exit,
            errors,
        ),
        "platform_modifier"
            if implementation_rules
                && matches!(compact_node(node, source).as_str(), "external" | "native") =>
        {
            push_error(
                errors,
                "external/native Kotlin declarations are not allowed".to_owned(),
            )
        }
        "identifier" if implementation_rules => {
            let identifier = normalized_identifier(node_text(node, source)).unwrap_or_default();
            if matches!(
                identifier.as_str(),
                "TODO" | "NotImplemented" | "NotImplementedError"
            ) {
                push_error(errors, format!("placeholder `{identifier}` is not allowed"));
            } else if matches!(
                identifier.as_str(),
                "javaClass"
                    | "classLoader"
                    | "contextClassLoader"
                    | "declaredMethods"
                    | "declaredFields"
                    | "declaredConstructors"
                    | "declaredMemberFunctions"
                    | "declaredMemberProperties"
                    | "memberFunctions"
                    | "memberProperties"
            ) {
                push_error(
                    errors,
                    format!("runtime reflection reference `{identifier}` is not allowed"),
                );
            } else if identifier.starts_with("_cott_")
                && (current != reserved_identifier_owner
                    || !allowed_reserved_identifiers.contains(&identifier)
                    || reserved_identifier_is_declaration(node))
            {
                push_error(
                    errors,
                    format!("reserved implementation identifier `{identifier}` is not allowed"),
                );
            }
            if invalid_cott_runtime_object_use(
                node,
                source,
                package,
                imports,
                private_targets,
                local_functions,
                allows_process_exit,
            ) {
                push_error(
                    errors,
                    format!(
                        "compiler-owned CottRuntime object reference `{identifier}` must remain the receiver of an approved direct member access"
                    ),
                );
            }
        }
        _ => {}
    }
    let mut cursor = node.walk();
    for child in node.children(&mut cursor) {
        audit_node(
            child,
            source,
            package,
            imports,
            private_targets,
            local_functions,
            exit_reaching_local_functions,
            current,
            implementation_rules,
            allows_process_exit,
            allowed_reserved_identifiers,
            reserved_identifier_owner,
            errors,
        );
    }
}

fn audit_import(
    node: Node<'_>,
    source: &str,
    private_targets: &BTreeSet<String>,
    implementation_rules: bool,
    allows_process_exit: bool,
    errors: &mut Vec<String>,
) {
    let Ok(import) = import_syntax(node, source) else {
        push_error(errors, "malformed Kotlin import".to_owned());
        return;
    };
    let target = &import.target;
    let wildcard = import.wildcard;
    if implementation_rules && wildcard {
        push_error(
            errors,
            format!("wildcard Kotlin import `{target}.*` is not allowed"),
        );
    }
    let local_name = import
        .alias
        .as_deref()
        .unwrap_or_else(|| target.rsplit('.').next().unwrap_or(target));
    if implementation_rules
        && safe_cott_runtime_member(local_name, allows_process_exit)
        && target.strip_prefix("cott_runtime.CottRuntime.") != Some(local_name)
    {
        push_error(
            errors,
            format!("Kotlin import `{target}` shadows approved CottRuntime member `{local_name}`"),
        );
    }
    if target == "cott_impl" || target.starts_with("cott_impl.") {
        push_error(
            errors,
            format!("private facade bypass import `{target}` is not allowed"),
        );
    }
    if private_targets.contains(target)
        || (wildcard
            && private_targets.iter().any(|private| {
                private
                    .strip_prefix(target)
                    .is_some_and(|tail| tail.starts_with('.'))
            }))
    {
        push_error(
            errors,
            format!("manifest implementation bypass import `{target}` is not allowed"),
        );
    }
    if implementation_rules && forbidden_import(target) {
        push_error(errors, format!("forbidden Kotlin import `{target}`"));
    }
    if implementation_rules && forbidden_kotlin_capability(target, allows_process_exit) {
        push_error(
            errors,
            format!("forbidden Kotlin process or verifier-control import `{target}`"),
        );
    }
}

fn forbidden_import(target: &str) -> bool {
    [
        "kotlin.reflect",
        "java.lang.reflect",
        "kotlin.Suppress",
        "java.lang.SuppressWarnings",
        "java.lang.invoke",
        "javax.script",
        "javax.tools",
        "kotlin.script",
        "org.jetbrains.kotlin.cli",
        "org.jetbrains.kotlin.compiler",
        "com.intellij.psi",
        "dalvik.system.DexClassLoader",
        "dalvik.system.PathClassLoader",
        "java.net.URLClassLoader",
        "java.lang.Process",
        "java.lang.ProcessBuilder",
        "java.lang.Runtime",
        "java.lang.ProcessHandle",
        "java.util.ServiceLoader",
        "kotlin.system.exitProcess",
        "sun.misc.Unsafe",
        "jdk.internal",
    ]
    .iter()
    .any(|forbidden| target == *forbidden || target.starts_with(&format!("{forbidden}.")))
}

fn invalid_cott_runtime_object_use(
    node: Node<'_>,
    source: &str,
    package: Option<&str>,
    imports: &BTreeMap<String, String>,
    private_targets: &BTreeSet<String>,
    local_functions: &BTreeSet<String>,
    allows_process_exit: bool,
) -> bool {
    if node.kind() == "identifier" {
        let mut ancestor = node.parent();
        while let Some(parent) = ancestor {
            if parent.kind() == "import" {
                return false;
            }
            if parent.kind() != "qualified_identifier" {
                break;
            }
            ancestor = parent.parent();
        }
        if let Some(parent) = node
            .parent()
            .filter(|parent| parent.kind() == "navigation_expression")
        {
            let is_receiver = direct_named_children(parent)
                .first()
                .is_some_and(|receiver| {
                    receiver.start_byte() == node.start_byte()
                        && receiver.end_byte() == node.end_byte()
                });
            if !is_receiver {
                return false;
            }
        }
    }
    let Some(reference) = reference_path(node, source) else {
        return false;
    };
    if resolve_reference(
        &reference,
        package,
        imports,
        private_targets,
        local_functions,
    ) != "cott_runtime.CottRuntime"
    {
        return false;
    }

    let Some(parent) = node.parent().filter(|parent| {
        parent.kind() == "navigation_expression" && !compact_node(*parent, source).contains("::")
    }) else {
        return true;
    };
    let Some(selected) = reference_path(parent, source).map(|reference| {
        resolve_reference(
            &reference,
            package,
            imports,
            private_targets,
            local_functions,
        )
    }) else {
        return true;
    };
    let Some(member) = selected.strip_prefix("cott_runtime.CottRuntime.") else {
        return true;
    };
    !safe_cott_runtime_member(member, allows_process_exit)
}

fn safe_cott_runtime_member(member: &str, allows_process_exit: bool) -> bool {
    matches!(
        member,
        "constValue"
            | "validateConst"
            | "sameConst"
            | "constHash"
            | "constLength"
            | "abi"
            | "abiSuspend"
            | "returnValue"
            | "returnValueSuspend"
            | "fixtureClockNs"
            | "fixtureClockNsSuspend"
            | "int"
            | "checkInt"
            | "mathInt"
            | "intValue"
            | "intAdd"
            | "intSubtract"
            | "intMultiply"
            | "intNegate"
            | "intDivide"
            | "euclideanRemainder"
            | "euclideanDivide"
            | "normalizeF32"
            | "validateF32"
            | "validateF64"
            | "f32Add"
            | "f32Subtract"
            | "f32Multiply"
            | "f32Divide"
            | "f32Negate"
            | "f64Add"
            | "f64Subtract"
            | "f64Multiply"
            | "f64Divide"
            | "f64Negate"
            | "validateUnicode"
            | "canonicalEqual"
            | "canonicalOrder"
            | "canonicalCompare"
            | "startsWith"
            | "endsWith"
            | "contains"
            | "length"
            | "uniqueBy"
            | "descendingBy"
            | "anyBlankBy"
            | "unknownDependencyBy"
            | "selfDependencyBy"
            | "cyclicBy"
            | "permutationBy"
            | "dependencyOrderedBy"
            | "field"
            | "resultOk"
            | "resultErr"
            | "deepSnapshot"
            | "deepEqual"
            | "deepHash"
            | "optionSome"
            | "variant"
            | "matchesResultOk"
            | "matchesResultErr"
            | "matchesSome"
            | "matchesNothing"
            | "matchesVariant"
            | "snapshotBytes"
            | "snapshotBuffer"
            | "snapshotList"
            | "snapshotSet"
            | "snapshotMap"
            | "snapshotTuple"
            | "snapshotArray"
            | "wrapIterator"
            | "wrapGenerator"
            | "wrapAsyncIterator"
            | "wrapAsyncGenerator"
    ) || (allows_process_exit && member == "exitWithCode")
}

fn reserved_cott_runtime_control(member: &str) -> bool {
    matches!(
        member,
        "withTestObservation"
            | "withTestObservationSuspend"
            | "withFixtureContext"
            | "withFixtureContextSuspend"
            | "shouldValidate"
            | "shouldValidateSuspend"
            | "contractsEnabled"
            | "contractsEnabledSuspend"
            | "requireContract"
            | "requireContractSuspend"
            | "ensureContract"
            | "ensureContractSuspend"
            | "invariant"
            | "invariantSuspend"
            | "checkContract"
            | "checkContractSuspend"
    )
}

fn forbidden_kotlin_capability(reference: &str, allows_process_exit: bool) -> bool {
    let reference = reference.replace('`', "").replace("()", "");
    let reference = reference.trim_start_matches('.');
    if reference == PROCESS_EXIT_RUNTIME_TARGET {
        return !allows_process_exit;
    }
    if reference
        .strip_prefix("cott_runtime.CottRuntime.")
        .is_some_and(reserved_cott_runtime_control)
    {
        return true;
    }
    if matches!(
        reference,
        "System.exit"
            | "java.lang.System.exit"
            | "System.setOut"
            | "java.lang.System.setOut"
            | "System.setIn"
            | "java.lang.System.setIn"
            | "System.in"
            | "java.lang.System.in"
            | "System.out.close"
            | "java.lang.System.out.close"
            | "FileDescriptor.in"
            | "java.io.FileDescriptor.in"
            | "FileDescriptor.out"
            | "java.io.FileDescriptor.out"
            | "Runtime.getRuntime"
            | "java.lang.Runtime.getRuntime"
            | "Runtime.exit"
            | "java.lang.Runtime.exit"
            | "Runtime.halt"
            | "java.lang.Runtime.halt"
            | "ProcessBuilder"
            | "java.lang.ProcessBuilder"
            | "ProcessHandle"
            | "java.lang.ProcessHandle"
            | "kotlin.system.exitProcess"
            | "exitProcess"
    ) || reference.starts_with("Runtime.getRuntime.")
        || reference.starts_with("java.lang.Runtime.getRuntime.")
        || reference.starts_with("ProcessBuilder.")
        || reference.starts_with("java.lang.ProcessBuilder.")
        || reference.starts_with("ProcessHandle.")
        || reference.starts_with("java.lang.ProcessHandle.")
        || reference.starts_with("System.in.")
        || reference.starts_with("java.lang.System.in.")
        || reference.starts_with("FileDescriptor.in.")
        || reference.starts_with("java.io.FileDescriptor.in.")
        || reference.starts_with("FileDescriptor.out.")
        || reference.starts_with("java.io.FileDescriptor.out.")
    {
        return true;
    }

    let runtime = reference.strip_prefix("cott_runtime.").unwrap_or(reference);
    if matches!(
        runtime,
        "CottClauseObservation"
            | "CottObservation"
            | "CottFixtureContext"
            | "CottFixtureKey"
            | "CottResourceGuard"
            | "CottStateField"
            | "CottTransition"
            | "CottInvariant"
            | "CottStateSnapshot"
            | "CottResourceContract"
            | "RuntimeValidation"
    ) || [
        "CottClauseObservation.",
        "CottObservation.",
        "CottFixtureContext.",
        "CottFixtureKey.",
        "CottResourceGuard.",
        "CottStateField.",
        "CottTransition.",
        "CottInvariant.",
        "CottStateSnapshot.",
        "CottResourceContract.",
        "RuntimeValidation.",
    ]
    .iter()
    .any(|prefix| runtime.starts_with(prefix))
    {
        return true;
    }

    false
}

fn call_is_inside_escaping_callable(node: Node<'_>) -> bool {
    let mut ancestor = node.parent();
    while let Some(candidate) = ancestor {
        match candidate.kind() {
            "lambda_literal" | "anonymous_function" => return true,
            "function_declaration" => return is_anonymous_object_member(candidate),
            _ => ancestor = candidate.parent(),
        }
    }
    false
}

#[allow(clippy::too_many_arguments)]
fn audit_call(
    node: Node<'_>,
    source: &str,
    package: Option<&str>,
    imports: &BTreeMap<String, String>,
    private_targets: &BTreeSet<String>,
    local_functions: &BTreeSet<String>,
    exit_reaching_local_functions: &BTreeSet<String>,
    current_function: Option<&str>,
    implementation_rules: bool,
    allows_process_exit: bool,
    errors: &mut Vec<String>,
) {
    let Some(callee) = direct_named_children(node).first().copied() else {
        return;
    };
    let compact = compact_node(callee, source);
    let path = reference_path(callee, source)
        .map(|path| resolve_reference(&path, package, imports, private_targets, local_functions));
    if let Some(path) = &path {
        let known_private =
            private_targets.contains(path) && Some(path.as_str()) != current_function;
        let explicit_private_package = (path == "cott_impl" || path.starts_with("cott_impl."))
            && !local_functions.contains(path)
            && Some(path.as_str()) != current_function;
        if known_private || explicit_private_package {
            push_error(
                errors,
                format!("private implementation call `{path}` bypasses the generated facade"),
            );
        }
    }

    if implementation_rules {
        let invocation = compact_node(node, source).to_ascii_lowercase();
        if invocation.starts_with("error(\"todo")
            || invocation.starts_with("error(\"notimplemented")
            || invocation.starts_with("error(\"not implemented")
        {
            push_error(
                errors,
                "placeholder failure is not allowed in a Kotlin implementation".to_owned(),
            );
        }
        let path = path.as_deref().unwrap_or(&compact);
        let leaf = path.rsplit('.').next().unwrap_or(path);
        let forbidden = forbidden_import(path)
            || forbidden_kotlin_capability(path, allows_process_exit)
            || forbidden_kotlin_capability(&compact, allows_process_exit)
            || ((path == PROCESS_EXIT_RUNTIME_TARGET
                || exit_reaching_local_functions.contains(path))
                && call_is_inside_escaping_callable(node))
            || leaf == "ProcessBuilder"
            || path.ends_with("Class.forName")
            || path.ends_with("System.load")
            || path.ends_with("System.loadLibrary")
            || compact.contains("Class.forName")
            || compact.contains("DexClassLoader")
            || compact.contains("PathClassLoader")
            || compact.contains("URLClassLoader")
            || [
                "getDeclaredMethod",
                "getDeclaredField",
                "getDeclaredConstructor",
                "getDeclaredMethods",
                "getDeclaredFields",
                "getMethod",
                "getField",
                "setAccessible",
                "trySetAccessible",
                "loadClass",
                "defineClass",
                "newInstance",
                "getSystemClassLoader",
                "callBy",
            ]
            .contains(&leaf);
        if forbidden {
            push_error(
                errors,
                format!(
                    "reflection, dynamic compilation, or process capability call `{compact}` is not allowed"
                ),
            );
        }
    }
}

#[allow(clippy::too_many_arguments)]
fn audit_callable_reference(
    node: Node<'_>,
    source: &str,
    package: Option<&str>,
    imports: &BTreeMap<String, String>,
    private_targets: &BTreeSet<String>,
    local_functions: &BTreeSet<String>,
    exit_reaching_local_functions: &BTreeSet<String>,
    current_function: Option<&str>,
    implementation_rules: bool,
    allows_process_exit: bool,
    errors: &mut Vec<String>,
) {
    let compact = compact_node(node, source);
    let reference = compact
        .replace('`', "")
        .replace("::", ".")
        .trim_start_matches('.')
        .to_owned();
    let target = resolve_reference(
        &reference,
        package,
        imports,
        private_targets,
        local_functions,
    );
    let known_private =
        private_targets.contains(&target) && Some(target.as_str()) != current_function;
    let explicit_private_package = (target == "cott_impl" || target.starts_with("cott_impl."))
        && !local_functions.contains(&target)
        && Some(target.as_str()) != current_function;
    if known_private || explicit_private_package {
        push_error(
            errors,
            format!("private implementation reference `{compact}` bypasses the generated facade"),
        );
    }
    let leaf = target.rsplit('.').next().unwrap_or(&target);
    if implementation_rules
        && (compact.contains("::class")
            || target == PROCESS_EXIT_RUNTIME_TARGET
            || exit_reaching_local_functions.contains(&target)
            || forbidden_import(&target)
            || forbidden_kotlin_capability(&target, allows_process_exit)
            || forbidden_kotlin_capability(&reference, allows_process_exit)
            || reserved_cott_runtime_control(leaf)
            || matches!(
                leaf,
                "forName"
                    | "getDeclaredMethod"
                    | "getDeclaredField"
                    | "getDeclaredConstructor"
                    | "loadClass"
                    | "defineClass"
                    | "newInstance"
                    | "callBy"
            ))
    {
        push_error(
            errors,
            format!("runtime reflection or capability reference `{compact}` is not allowed"),
        );
    }
}

fn resolve_reference(
    reference: &str,
    package: Option<&str>,
    imports: &BTreeMap<String, String>,
    private_targets: &BTreeSet<String>,
    local_functions: &BTreeSet<String>,
) -> String {
    let (first, rest) = reference
        .split_once('.')
        .map_or((reference, None), |(first, rest)| (first, Some(rest)));
    if let Some(imported) = imports.get(first) {
        return rest.map_or_else(|| imported.clone(), |rest| format!("{imported}.{rest}"));
    }
    if reference.contains('.') {
        return reference.to_owned();
    }
    let Some(package) = package else {
        return reference.to_owned();
    };
    let same_package = format!("{package}.{reference}");
    if private_targets.contains(&same_package) || local_functions.contains(&same_package) {
        same_package
    } else {
        reference.to_owned()
    }
}

fn reference_path(node: Node<'_>, source: &str) -> Option<String> {
    match node.kind() {
        "identifier" => normalized_identifier(node_text(node, source)).ok(),
        "navigation_expression" => {
            if compact_node(node, source).contains("::") {
                return None;
            }
            let children = direct_named_children(node);
            let left = reference_path(*children.first()?, source)?;
            let right = children
                .iter()
                .rev()
                .find(|child| child.kind() == "identifier")
                .and_then(|child| normalized_identifier(node_text(*child, source)).ok())?;
            Some(format!("{left}.{right}"))
        }
        _ => None,
    }
}

fn reserved_identifier_is_declaration(node: Node<'_>) -> bool {
    let Some(parent) = node.parent() else {
        return false;
    };
    if parent.kind() == "parameter" {
        let mut ancestor = parent.parent();
        while let Some(candidate) = ancestor {
            if candidate.kind() == "function_declaration" {
                return is_anonymous_object_member(candidate);
            }
            ancestor = candidate.parent();
        }
        return false;
    }
    matches!(
        parent.kind(),
        "variable_declaration"
            | "multi_variable_declaration"
            | "type_parameter"
            | "class_declaration"
            | "object_declaration"
            | "function_declaration"
            | "import"
    )
}

fn expected_reserved_identifiers(
    expected: &[ExpectedFunction<'_>],
) -> Result<BTreeSet<String>, String> {
    let mut names = BTreeSet::new();
    for expected_function in expected {
        let source = format!(
            "{} {{ throw IllegalStateException() }}\n",
            expected_function.signature
        );
        let tree = parse_kotlin(&source).map_err(|message| {
            format!(
                "emitter produced an invalid canonical Kotlin signature `{}`: {message}",
                expected_function.signature
            )
        })?;
        let function = top_level_functions(tree.root_node())
            .into_iter()
            .next()
            .ok_or_else(|| {
                format!(
                    "emitter produced no canonical Kotlin function for `{}`",
                    expected_function.signature
                )
            })?;
        let parameters = direct_named_children(function)
            .into_iter()
            .find(|child| child.kind() == "function_value_parameters")
            .ok_or_else(|| {
                format!(
                    "emitter produced no parameter list for `{}`",
                    expected_function.signature
                )
            })?;
        for parameter in direct_named_children(parameters)
            .into_iter()
            .filter(|child| child.kind() == "parameter")
        {
            let Some(identifier) = direct_named_children(parameter)
                .into_iter()
                .find(|child| child.kind() == "identifier")
            else {
                continue;
            };
            let name = normalized_identifier(node_text(identifier, &source))?;
            if name.starts_with("_cott_") {
                names.insert(name);
            }
        }
    }
    Ok(names)
}

fn validate_restricted_source(
    source: &str,
    expected: &[ExpectedFunction<'_>],
    private_targets: &BTreeSet<String>,
) -> Result<(), String> {
    if expected.len() != 1 {
        return Err(
            "one Kotlin source file must own exactly one canonical implementation function"
                .to_owned(),
        );
    }
    if !source.ends_with('\n') || source.ends_with("\n\n") {
        return Err("Kotlin implementation must end in exactly one newline".to_owned());
    }
    let tree = parse_kotlin(source)?;
    let root = tree.root_node();
    let expected_package = expected
        .first()
        .and_then(|expected| expected.target_symbol.rsplit_once('.'))
        .map(|(package, _)| package)
        .ok_or_else(|| "Kotlin implementation target has no package".to_owned())?;
    if expected.iter().any(|function| {
        function
            .target_symbol
            .rsplit_once('.')
            .map(|(package, _)| package)
            != Some(expected_package)
    }) {
        return Err(
            "one Kotlin source file cannot own implementations from multiple packages".to_owned(),
        );
    }
    if source_package(root, source)?.as_deref() != Some(expected_package) {
        return Err(format!(
            "Kotlin implementation must declare exact package `{expected_package}`"
        ));
    }
    let allowed_reserved_identifiers = expected_reserved_identifiers(expected)?;
    audit_source(
        source,
        private_targets,
        true,
        expected[0].allows_process_exit,
        &allowed_reserved_identifiers,
        Some(expected[0].target_symbol),
    )?;

    for child in direct_named_children(root) {
        if is_comment(child.kind())
            || matches!(
                child.kind(),
                "package_header" | "import" | "function_declaration"
            )
        {
            continue;
        }
        return Err(format!(
            "executable top-level or non-function declaration `{}` is not allowed",
            compact_node(child, source)
        ));
    }

    let target_function = expected[0]
        .target_symbol
        .rsplit_once('.')
        .map(|(_, function)| function)
        .ok_or_else(|| "Kotlin implementation target has no function name".to_owned())?;
    let functions = top_level_functions(root);
    let mut seen = BTreeSet::new();
    for function in &functions {
        let name = function_name(*function, source)?;
        if !seen.insert(name.clone()) {
            return Err(format!(
                "Kotlin implementation must not overload or duplicate function `{name}`"
            ));
        }
        if name == target_function {
            validate_canonical_function(*function, source, &expected[0])?;
        } else {
            validate_helper_function(*function, source, &name)?;
        }
    }
    if !seen.contains(target_function) {
        return Err(format!(
            "Kotlin implementation must define exactly one target function `{target_function}`"
        ));
    }
    reject_nested_declarations(root, source)?;
    Ok(())
}

fn validate_canonical_function(
    function: Node<'_>,
    source: &str,
    expected: &ExpectedFunction<'_>,
) -> Result<(), String> {
    let target_function = expected
        .target_symbol
        .rsplit_once('.')
        .map(|(_, function)| function)
        .ok_or_else(|| "Kotlin implementation target has no function name".to_owned())?;
    let actual_name = function_name(function, source)?;
    if actual_name != target_function {
        return Err(format!(
            "implementation function `{actual_name}` does not match target `{target_function}`"
        ));
    }
    let actual_tokens = signature_tokens_with_name_marker(function, source)?;
    let expected_tokens = expected_signature_tokens(&expected.signature)?;
    if actual_tokens != expected_tokens {
        return Err(format!(
            "function `{target_function}` does not match the canonical Kotlin ABI signature `{}`",
            expected.signature
        ));
    }
    function_body(function)
        .ok_or_else(|| format!("function `{target_function}` must have an implementation body"))?;
    Ok(())
}

fn expected_signature_tokens(signature: &str) -> Result<Vec<SignatureToken>, String> {
    let source = format!("{signature} {{ throw IllegalStateException() }}\n");
    let tree = parse_kotlin(&source).map_err(|message| {
        format!("emitter produced an invalid canonical Kotlin signature `{signature}`: {message}")
    })?;
    let function = top_level_functions(tree.root_node())
        .into_iter()
        .next()
        .ok_or_else(|| {
            format!("emitter produced no canonical Kotlin function for `{signature}`")
        })?;
    signature_tokens_with_name_marker(function, &source)
}
#[derive(Eq, PartialEq)]
enum SignatureToken {
    ImplementationFunction,
    Identifier(String),
    Syntax(String),
}

fn signature_tokens_with_name_marker(
    function: Node<'_>,
    source: &str,
) -> Result<Vec<SignatureToken>, String> {
    let name = function
        .child_by_field_name("name")
        .ok_or_else(|| "Kotlin function has no name".to_owned())?;
    let name_range = name.byte_range();
    let mut tokens = Vec::new();
    collect_signature_tokens_with_name_marker(function, source, &name_range, &mut tokens)?;
    Ok(tokens)
}

fn collect_signature_tokens_with_name_marker(
    node: Node<'_>,
    source: &str,
    name_range: &std::ops::Range<usize>,
    tokens: &mut Vec<SignatureToken>,
) -> Result<(), String> {
    if node.byte_range() == *name_range {
        tokens.push(SignatureToken::ImplementationFunction);
        return Ok(());
    }
    if node.kind() == "function_body" || is_comment(node.kind()) {
        return Ok(());
    }
    if node.child_count() == 0 {
        let token = if node.kind() == "identifier" {
            SignatureToken::Identifier(normalized_identifier(node_text(node, source))?)
        } else {
            SignatureToken::Syntax(node_text(node, source).to_owned())
        };
        tokens.push(token);
        return Ok(());
    }
    let mut cursor = node.walk();
    for child in node.children(&mut cursor) {
        collect_signature_tokens_with_name_marker(child, source, name_range, tokens)?;
    }
    Ok(())
}

fn validate_helper_function(function: Node<'_>, source: &str, name: &str) -> Result<(), String> {
    if !name.starts_with('_') || name.starts_with("__") || name.starts_with("_cott") {
        return Err(format!(
            "helper function `{name}` must have one private `_` prefix and must not use the reserved `_cott` prefix"
        ));
    }
    if contains_kind(function, "annotation") {
        return Err(format!("helper function `{name}` must not be annotated"));
    }
    let modifiers = direct_named_children(function)
        .into_iter()
        .find(|child| child.kind() == "modifiers")
        .map(|node| syntax_tokens(node, source))
        .unwrap_or_default();
    let valid_modifiers = modifiers.len() == 1 && modifiers[0] == "private"
        || modifiers.len() == 2 && modifiers[0] == "private" && modifiers[1] == "suspend";
    if !valid_modifiers {
        return Err(format!(
            "helper function `{name}` must be exactly `private fun` or `private suspend fun`"
        ));
    }
    let parameters = direct_named_children(function)
        .into_iter()
        .find(|child| child.kind() == "function_value_parameters")
        .ok_or_else(|| format!("helper function `{name}` has no parameter list"))?;
    if syntax_tokens(parameters, source)
        .iter()
        .any(|token| token == "=")
    {
        return Err(format!(
            "helper function `{name}` must not declare defaults"
        ));
    }
    let body = function_body(function)
        .ok_or_else(|| format!("helper function `{name}` must have an implementation body"))?;
    let has_return_type = direct_named_children(function).into_iter().any(|child| {
        child.start_byte() >= parameters.end_byte()
            && child.end_byte() <= body.start_byte()
            && !is_comment(child.kind())
            && !matches!(child.kind(), "type_constraints" | "function_body")
    });
    if !has_return_type {
        return Err(format!(
            "helper function `{name}` must have an explicit return type"
        ));
    }
    Ok(())
}

fn function_body(function: Node<'_>) -> Option<Node<'_>> {
    direct_named_children(function)
        .into_iter()
        .find(|child| child.kind() == "function_body")
}

fn syntax_tokens(node: Node<'_>, source: &str) -> Vec<String> {
    let mut tokens = Vec::new();
    collect_syntax_tokens(node, source, &mut tokens);
    tokens
}

fn collect_syntax_tokens(node: Node<'_>, source: &str, tokens: &mut Vec<String>) {
    if is_comment(node.kind()) {
        return;
    }
    if node.child_count() == 0 {
        tokens.push(node_text(node, source).to_owned());
        return;
    }
    let mut cursor = node.walk();
    for child in node.children(&mut cursor) {
        collect_syntax_tokens(child, source, tokens);
    }
}

fn compact_node(node: Node<'_>, source: &str) -> String {
    syntax_tokens(node, source).concat()
}

fn contains_kind(node: Node<'_>, kind: &str) -> bool {
    if node.kind() == kind {
        return true;
    }
    let mut cursor = node.walk();
    let found = node
        .named_children(&mut cursor)
        .any(|child| contains_kind(child, kind));
    found
}

fn is_anonymous_object_member(node: Node<'_>) -> bool {
    let mut ancestor = node.parent();
    while let Some(candidate) = ancestor {
        match candidate.kind() {
            "object_literal" => return true,
            "function_declaration" => return false,
            _ => ancestor = candidate.parent(),
        }
    }
    false
}

fn validate_anonymous_override(function: Node<'_>, source: &str) -> Result<(), String> {
    let name = function_name(function, source)?;
    let modifiers = direct_named_children(function)
        .into_iter()
        .find(|child| child.kind() == "modifiers")
        .map(|node| syntax_tokens(node, source))
        .unwrap_or_default();
    if !modifiers.iter().any(|modifier| modifier == "override") {
        return Err(format!(
            "anonymous adapter method `{name}` must be an explicit override"
        ));
    }
    let forbidden_modifier = [
        "public",
        "private",
        "protected",
        "internal",
        "external",
        "expect",
        "actual",
        "abstract",
        "final",
        "open",
        "inline",
        "tailrec",
        "infix",
    ]
    .iter()
    .find(|forbidden| modifiers.iter().any(|modifier| modifier == *forbidden));
    if let Some(modifier) = forbidden_modifier {
        return Err(format!(
            "anonymous adapter method `{name}` must not use `{modifier}`"
        ));
    }
    let parameters = direct_named_children(function)
        .into_iter()
        .find(|child| child.kind() == "function_value_parameters")
        .ok_or_else(|| format!("anonymous adapter method `{name}` has no parameter list"))?;
    if syntax_tokens(parameters, source)
        .iter()
        .any(|token| token == "=")
    {
        return Err(format!(
            "anonymous adapter method `{name}` must not declare defaults"
        ));
    }
    let body = function_body(function)
        .ok_or_else(|| format!("anonymous adapter method `{name}` must have a body"))?;
    let has_return_type = direct_named_children(function).into_iter().any(|child| {
        child.start_byte() >= parameters.end_byte()
            && child.end_byte() <= body.start_byte()
            && !is_comment(child.kind())
            && !matches!(child.kind(), "type_constraints" | "function_body")
    });
    if !has_return_type {
        return Err(format!(
            "anonymous adapter method `{name}` must have an explicit return type"
        ));
    }
    Ok(())
}

fn reject_nested_declarations(root: Node<'_>, source: &str) -> Result<(), String> {
    fn visit(node: Node<'_>, source: &str, depth: usize) -> Result<(), String> {
        if depth > 0
            && matches!(
                node.kind(),
                "class_declaration" | "object_declaration" | "type_alias"
            )
        {
            return Err(format!(
                "named nested declaration `{}` is not allowed in Kotlin implementations",
                compact_node(node, source)
            ));
        }
        if node.kind() == "function_declaration" && depth > 0 {
            if !is_anonymous_object_member(node) {
                return Err(format!(
                    "local function declaration `{}` is not allowed in Kotlin implementations",
                    compact_node(node, source)
                ));
            }
            validate_anonymous_override(node, source)?;
        }
        if node.kind() == "property_declaration" && is_anonymous_object_member(node) {
            return Err(
                "anonymous implementation adapters must not declare uncontracted properties"
                    .to_owned(),
            );
        }
        if matches!(node.kind(), "anonymous_initializer" | "explicit_delegation")
            && is_anonymous_object_member(node)
        {
            return Err(
                "anonymous implementation adapters must use explicit audited override methods"
                    .to_owned(),
            );
        }
        let next_depth = if node.kind() == "function_declaration" {
            depth + 1
        } else {
            depth
        };
        let mut cursor = node.walk();
        for child in node.named_children(&mut cursor) {
            visit(child, source, next_depth)?;
        }
        Ok(())
    }
    let mut cursor = root.walk();
    for child in root.named_children(&mut cursor) {
        visit(child, source, 0)?;
    }
    Ok(())
}

fn node_text<'a>(node: Node<'_>, source: &'a str) -> &'a str {
    source.get(node.byte_range()).unwrap_or("")
}

fn is_comment(kind: &str) -> bool {
    matches!(kind, "line_comment" | "block_comment")
}

fn push_error(errors: &mut Vec<String>, message: String) {
    if !errors.contains(&message) {
        errors.push(message);
    }
}
