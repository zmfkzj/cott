use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, OpenOptions};
use std::io::Read;
use std::os::unix::fs::{MetadataExt, OpenOptionsExt};
use std::path::{Component, Path, PathBuf};

use tree_sitter::{Parser, Tree};

use crate::hash::sha256_hex;
use crate::intent;
use crate::manifest::RustProjectConfig;
use crate::project::{RustPaths, RustSourceFile, discover_rust_sources};

use super::emit::implementation_signature;
use super::provenance::{RustBindingRecord, RustGenerationRecord};
use super::{RustBinding, RustCallable, RustOwner, RustPlan};

mod audit;
use audit::{audit_private_access, audit_source, index_source, rust_identifier};

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ParsedImplementation {
    /// Complete authored import directives, including their semicolons, in source order.
    pub imports: Vec<String>,
    /// Every non-import byte from the authored source, in its original order.
    pub body: String,
}

#[derive(Clone, Debug)]
struct SourceIndex {
    functions: Vec<String>,
}

struct ParsedSource {
    tree: Tree,
    index: SourceIndex,
}

#[derive(Clone, Debug)]
struct SelectedBinding {
    callable: RustCallable,
    target_symbol: String,
    source: PathBuf,
    source_origin: PathBuf,
    runtime_origin: PathBuf,
    owner: RustOwner,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum AgentDisposition {
    Resolved,
    Pending,
    Stale,
}

#[derive(Clone, Debug)]
struct ExpectedFunction {
    signature: String,
}
pub fn resolve(
    config: &RustProjectConfig,
    paths: &RustPaths,
    plan: &RustPlan,
    allowed_runtime_packages: &BTreeSet<String>,
    generator_rules: Option<&str>,
) -> Result<Vec<RustBinding>, String> {
    resolve_with_baseline(
        config,
        paths,
        plan,
        allowed_runtime_packages,
        generator_rules,
        None,
    )
}

/// Used only by emit after the old record was fully authenticated and its
/// original bytes frozen in the publication transaction's input snapshot.
pub(crate) fn resolve_with_baseline(
    config: &RustProjectConfig,
    paths: &RustPaths,
    plan: &RustPlan,
    allowed_runtime_packages: &BTreeSet<String>,
    generator_rules: Option<&str>,
    authenticated_cutover: Option<&RustGenerationRecord>,
) -> Result<Vec<RustBinding>, String> {
    let callables = callable_index(plan)?;
    validate_manifest_bindings(config, paths, plan, &callables)?;

    let sources = discover_rust_sources(&paths.rust_source_dir).map_err(|error| {
        format!(
            "{}: unable to discover Rust implementation sources: {error}",
            paths.rust_source_dir.display()
        )
    })?;
    let mut parsed_sources = BTreeMap::new();
    for source in &sources {
        let tree = parse_rust(&source.source)
            .map_err(|message| path_error(&source.disk_path, &message))?;
        let index = index_source(&tree, &source.source)
            .map_err(|message| path_error(&source.disk_path, &message))?;
        parsed_sources.insert(source.disk_path.clone(), ParsedSource { tree, index });
    }

    let generation_path = paths.artifact_root.join("generation.json");
    let owned_record = if authenticated_cutover.is_some() {
        None
    } else {
        load_generation_record(&generation_path)?
    };
    let record = authenticated_cutover.or(owned_record.as_ref());
    if let Some(record) = record
        && record.current.project_name != config.project.name
    {
        return Err(path_error(
            &generation_path,
            "Rust generation provenance belongs to a different project identity",
        ));
    }
    let rules = match (&config.generator.rules, generator_rules) {
        (Some(_), Some(rules)) => rules.as_bytes(),
        (None, None) => &[],
        (Some(relative), None) => {
            return Err(path_error(
                &paths.root.join(relative),
                "configured Rust generator rules were not supplied to binding resolution",
            ));
        }
        (None, Some(_)) => {
            return Err(path_error(
                &paths.manifest,
                "binding resolution received generator rules that are not configured",
            ));
        }
    };
    let current_intent = intent::fingerprints(plan.contract_surface(), rules)
        .map_err(|message| format!("Rust implementation intent: {message}"))?;
    let baseline_intent = record
        .map(|record| recorded_intent(record, paths))
        .transpose()?;

    let mut selected = Vec::new();
    let mut pending = Vec::new();
    let mut expected_agent_files = BTreeSet::new();
    let mut retired_agent_files = BTreeSet::new();

    for callable in callables.values() {
        if !requires_binding(callable) {
            continue;
        }
        let runtime_origin = runtime_origin(callable)?;
        let selection = if let Some(target) = config.rust.implementations.get(&callable.symbol) {
            let (relative, function) = parse_target_symbol(target)?;
            let source_path = paths.rust_source_dir.join(&relative);
            let source = source_at(&sources, &source_path).ok_or_else(|| {
                path_error(
                    &paths.manifest,
                    &format!(
                        "implementation binding `{}` = `{target}` does not name a discovered Rust source",
                        callable.symbol
                    ),
                )
            })?;
            let parsed = parsed_sources.get(&source.disk_path).ok_or_else(|| {
                path_error(&source.disk_path, "selected Rust source was not parsed")
            })?;
            let matches = parsed
                .index
                .functions
                .iter()
                .filter(|name| *name == &function)
                .count();
            if matches != 1 {
                return Err(path_error(
                    &paths.manifest,
                    &format!(
                        "implementation binding `{}` = `{target}` resolved to {matches} top-level declarations; expected exactly one",
                        callable.symbol
                    ),
                ));
            }
            SelectedBinding {
                callable: callable.clone(),
                target_symbol: target_text(&relative, &function)?,
                source: source.disk_path.clone(),
                source_origin: project_relative(&paths.root, &source.disk_path)?,
                runtime_origin,
                owner: RustOwner::Manifest,
            }
        } else {
            let relative = agent_relative_path(callable)?;
            let source_path = paths.rust_source_dir.join(&relative);
            expected_agent_files.insert(source_path.clone());
            let target_symbol = agent_target_symbol(callable)?;
            let Some(source) = source_at(&sources, &source_path) else {
                // Missing genuine source is unresolved. A prior record is never
                // allowed to stand in for absent durable bytes.
                continue;
            };
            let source_origin = project_relative(&paths.root, &source.disk_path)?;
            let disposition = validate_agent_provenance(
                record,
                callable,
                &target_symbol,
                &source_origin,
                &runtime_origin,
                source.source.as_bytes(),
                &current_intent,
                baseline_intent.as_ref(),
            )?;
            let binding = SelectedBinding {
                callable: callable.clone(),
                target_symbol,
                source: source.disk_path.clone(),
                source_origin,
                runtime_origin,
                owner: RustOwner::Agent,
            };
            match disposition {
                AgentDisposition::Resolved => binding,
                AgentDisposition::Pending => {
                    pending.push(binding);
                    continue;
                }
                AgentDisposition::Stale => {
                    // Intent-stale bytes remain unresolved. Reading them cannot
                    // refresh the intent frozen in authenticated provenance.
                    continue;
                }
            }
        };
        selected.push(selection);
    }

    for source in &sources {
        let relative = source_relative(paths, source)?;
        if relative.starts_with("cott_impl") && !expected_agent_files.contains(&source.disk_path) {
            if retired_agent_source_is_authenticated(
                record,
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
                "stale or manifest-shadowed durable Rust implementation is not owned by the current plan",
            ));
        }
    }

    for source in &sources {
        if retired_agent_files.contains(&source.disk_path) {
            continue;
        }
        let parsed = &parsed_sources[&source.disk_path];
        audit_private_access(parsed.tree.root_node(), &source.source)?;
    }

    let mut by_source = BTreeMap::<PathBuf, Vec<&SelectedBinding>>::new();
    for binding in selected.iter().chain(pending.iter()) {
        by_source
            .entry(binding.source.clone())
            .or_default()
            .push(binding);
    }
    for (source_path, indexes) in &by_source {
        if indexes.len() != 1 {
            return Err(path_error(
                source_path,
                "one Rust source file must own exactly one canonical implementation function",
            ));
        }
        let source = source_at(&sources, source_path)
            .ok_or_else(|| path_error(source_path, "selected Rust source disappeared"))?;
        let parsed = parsed_sources
            .get(source_path)
            .ok_or_else(|| path_error(source_path, "selected Rust source was not parsed"))?;
        let selected_binding = indexes[0];
        let expected = ExpectedFunction {
            signature: implementation_signature(plan, &selected_binding.callable).map_err(
                |message| {
                    path_error(
                        source_path,
                        &format!(
                            "cannot render canonical implementation signature for `{}`: {message}",
                            selected_binding.callable.symbol
                        ),
                    )
                },
            )?,
        };
        let context = intent::context(
            plan.contract_surface(),
            &selected_binding.callable.symbol,
            rules,
        )?;
        audit_source(
            plan,
            &selected_binding.callable,
            allowed_runtime_packages,
            &source.source,
            &parsed.tree,
            &expected.signature,
            &parse_target_symbol(&selected_binding.target_symbol)?.1,
            Some(&context),
        )
        .map_err(|message| path_error(source_path, &message))?;
    }

    let mut bindings = Vec::with_capacity(selected.len());
    for selected in selected {
        let source = source_at(&sources, &selected.source)
            .ok_or_else(|| path_error(&selected.source, "selected Rust source disappeared"))?;
        let bytes = source.source.as_bytes().to_vec();
        bindings.push(RustBinding {
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

pub fn validate_candidate(
    _config: &RustProjectConfig,
    plan: &RustPlan,
    callable: &RustCallable,
    allowed_runtime_packages: &BTreeSet<String>,
    bytes: &[u8],
) -> Result<(), String> {
    validate_candidate_in_context(
        _config,
        plan,
        callable,
        allowed_runtime_packages,
        bytes,
        None,
    )
}

pub(crate) fn validate_candidate_in_context(
    _config: &RustProjectConfig,
    plan: &RustPlan,
    callable: &RustCallable,
    allowed_runtime_packages: &BTreeSet<String>,
    bytes: &[u8],
    context: Option<&serde_json::Value>,
) -> Result<(), String> {
    let mut planned = plan
        .callables()
        .iter()
        .filter(|candidate| candidate.symbol == callable.symbol);
    if planned.next() != Some(callable) || planned.next().is_some() {
        return Err(format!(
            "Rust candidate callable `{}` is not the unique canonical callable in the plan",
            callable.symbol
        ));
    }
    if !requires_binding(callable) {
        return Err(format!(
            "compiler-owned selected method `{}` does not accept a Rust candidate",
            callable.symbol
        ));
    }
    let source = std::str::from_utf8(bytes).map_err(|_| "Rust implementation is not UTF-8")?;
    let tree = audit::parse_rust(source)?;
    audit_source(
        plan,
        callable,
        allowed_runtime_packages,
        source,
        &tree,
        &implementation_signature(plan, callable)?,
        &private_callable_name(callable)?,
        context,
    )
}

pub fn partition_source(bytes: &[u8]) -> Result<ParsedImplementation, String> {
    audit::partition(bytes)
}

fn parse_rust(source: &str) -> Result<Tree, String> {
    audit::parse_rust(source)
}
pub(crate) fn requires_binding(callable: &RustCallable) -> bool {
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

pub(crate) fn agent_source_origin(
    paths: &RustPaths,
    callable: &RustCallable,
) -> Result<PathBuf, String> {
    project_relative(
        &paths.root,
        &paths.rust_source_dir.join(agent_relative_path(callable)?),
    )
}

pub(crate) fn agent_target_symbol(callable: &RustCallable) -> Result<String, String> {
    let relative = agent_relative_path(callable)?;
    let private = private_callable_name(callable)?;
    target_text(&relative, &private)
}

pub(crate) fn candidate_binding(
    paths: &RustPaths,
    callable: &RustCallable,
    bytes: Vec<u8>,
) -> Result<RustBinding, String> {
    Ok(RustBinding {
        cott_symbol: callable.symbol.clone(),
        target_symbol: agent_target_symbol(callable)?,
        source_origin: agent_source_origin(paths, callable)?,
        runtime_origin: runtime_origin(callable)?,
        content_hash: format!("sha256:{}", sha256_hex(&bytes)),
        bytes,
        owner: RustOwner::Agent,
    })
}

fn callable_index(plan: &RustPlan) -> Result<BTreeMap<String, RustCallable>, String> {
    let mut callables = BTreeMap::new();
    for callable in plan.callables() {
        if callables
            .insert(callable.symbol.clone(), callable.clone())
            .is_some()
        {
            return Err(format!(
                "Rust plan contains duplicate callable `{}`",
                callable.symbol
            ));
        }
    }
    Ok(callables)
}

fn validate_manifest_bindings(
    config: &RustProjectConfig,
    paths: &RustPaths,
    plan: &RustPlan,
    callables: &BTreeMap<String, RustCallable>,
) -> Result<(), String> {
    let mut targets = BTreeMap::<String, &str>::new();
    for (symbol, target) in &config.rust.implementations {
        let Some(callable) = callables.get(symbol) else {
            return Err(path_error(
                &paths.manifest,
                &format!("implementation binding key `{symbol}` is not a canonical callable"),
            ));
        };
        if !requires_binding(callable) {
            return Err(path_error(
                &paths.manifest,
                &format!(
                    "implementation binding key `{symbol}` names a compiler-owned selected method"
                ),
            ));
        }
        let (relative, function) =
            parse_target_symbol(target).map_err(|message| path_error(&paths.manifest, &message))?;
        if function.starts_with("cott_") || function.starts_with("__cott") {
            return Err(path_error(
                &paths.manifest,
                &format!(
                    "manifest implementation `{symbol}` must not claim compiler-owned private name `{function}`"
                ),
            ));
        }
        if reserved_authored_path(&relative) {
            return Err(path_error(
                &paths.manifest,
                &format!(
                    "manifest implementation `{symbol}` targets reserved compiler or agent path `{}`",
                    relative.display()
                ),
            ));
        }
        let normalized = target_text(&relative, &function)?;
        if let Some(previous) = targets.insert(normalized.clone(), symbol) {
            return Err(path_error(
                &paths.manifest,
                &format!(
                    "manifest implementations `{previous}` and `{symbol}` both claim `{normalized}`"
                ),
            ));
        }
    }

    // Force every canonical agent path to be valid and collision-free even when
    // a manifest currently overrides one of the callables.
    let mut agent_paths = BTreeMap::new();
    for callable in plan
        .callables()
        .iter()
        .filter(|callable| requires_binding(callable))
    {
        let path = agent_relative_path(callable)?;
        if let Some(previous) = agent_paths.insert(path.clone(), callable.symbol.as_str()) {
            return Err(format!(
                "Rust callables `{previous}` and `{}` collide at agent path `{}`",
                callable.symbol,
                path.display()
            ));
        }
    }
    Ok(())
}

fn agent_relative_path(callable: &RustCallable) -> Result<PathBuf, String> {
    canonical_callable_path("cott_impl", callable)
}

fn runtime_origin(callable: &RustCallable) -> Result<PathBuf, String> {
    canonical_callable_path("rust/src/cott_impl", callable)
}

fn canonical_callable_path(root: &str, callable: &RustCallable) -> Result<PathBuf, String> {
    let segments = cott_segments(&callable.symbol)?;
    let mut path = PathBuf::from(root);
    for segment in &segments[..segments.len() - 1] {
        path.push(segment);
    }
    path.push(format!("{}.rs", segments[segments.len() - 1]));
    Ok(path)
}

fn private_callable_name(callable: &RustCallable) -> Result<String, String> {
    let segments = cott_segments(&callable.symbol)?;
    Ok(rust_identifier(segments[segments.len() - 1]))
}

fn parse_target_symbol(target: &str) -> Result<(PathBuf, String), String> {
    let Some((path, function)) = target.split_once(':') else {
        return Err(format!(
            "invalid Rust implementation target `{target}`; expected source-relative-file.rs:function"
        ));
    };
    if target.matches(':').count() != 1 {
        return Err(format!(
            "invalid Rust implementation target `{target}`; expected exactly one `:`"
        ));
    }
    let path = PathBuf::from(path);
    if !safe_relative(&path) || path.extension().and_then(|value| value.to_str()) != Some("rs") {
        return Err(format!(
            "invalid Rust implementation source path `{}`",
            path.display()
        ));
    }
    let identifier = function.strip_prefix("r#").unwrap_or(function);
    let valid_spelling = if function.starts_with("r#") {
        rust_identifier(identifier) == function
    } else {
        !matches!(function, "_" | "self" | "Self" | "super" | "crate")
            && !rust_identifier(function).starts_with("r#")
    };
    if !valid_cott_identifier(identifier) || !valid_spelling {
        return Err(format!(
            "Rust implementation target `{target}` must name a function identifier"
        ));
    }
    Ok((path, function.to_owned()))
}

fn target_text(path: &Path, function: &str) -> Result<String, String> {
    Ok(format!("{}:{function}", path_text(path)?))
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

fn reserved_authored_path(path: &Path) -> bool {
    [
        "cott_impl",
        "src/cott_impl",
        "src/modules",
        "src/cott_runtime",
        "target",
        ".cott",
    ]
    .iter()
    .any(|reserved| path.starts_with(reserved))
}

fn source_at<'a>(sources: &'a [RustSourceFile], path: &Path) -> Option<&'a RustSourceFile> {
    sources.iter().find(|source| source.disk_path == path)
}

fn source_relative(paths: &RustPaths, source: &RustSourceFile) -> Result<PathBuf, String> {
    let relative = source
        .disk_path
        .strip_prefix(&paths.rust_source_dir)
        .map_err(|_| {
            path_error(
                &source.disk_path,
                &format!(
                    "Rust source is outside configured tree {}",
                    paths.rust_source_dir.display()
                ),
            )
        })?;
    if !safe_relative(relative) {
        return Err(path_error(
            &source.disk_path,
            "Rust source does not have a safe source-relative path",
        ));
    }
    Ok(relative.to_path_buf())
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
        && !path.is_absolute()
        && path
            .components()
            .all(|component| matches!(component, Component::Normal(_)))
}

fn path_text(path: &Path) -> Result<String, String> {
    if !safe_relative(path) {
        return Err(format!("unsafe Rust provenance path `{}`", path.display()));
    }
    path.to_str()
        .map(|path| path.replace('\\', "/"))
        .ok_or_else(|| format!("non-UTF-8 Rust provenance path `{}`", path.display()))
}

fn path_error(path: &Path, message: &str) -> String {
    format!("{}: {message}", path.display())
}

fn load_generation_record(path: &Path) -> Result<Option<RustGenerationRecord>, String> {
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
                &format!("unable to open Rust generation provenance safely: {error}"),
            ));
        }
    };
    let before = file.metadata().map_err(|error| {
        path_error(
            path,
            &format!("unable to inspect opened Rust generation provenance: {error}"),
        )
    })?;
    if !before.is_file() || before.nlink() != 1 {
        return Err(path_error(
            path,
            "Rust generation provenance must be a regular non-symlink single-link file",
        ));
    }
    let mut bytes = Vec::new();
    file.read_to_end(&mut bytes).map_err(|error| {
        path_error(
            path,
            &format!("unable to read opened Rust generation provenance: {error}"),
        )
    })?;
    let after = file.metadata().map_err(|error| {
        path_error(
            path,
            &format!("unable to re-inspect opened Rust generation provenance: {error}"),
        )
    })?;
    let leaf = fs::symlink_metadata(path).map_err(|error| {
        path_error(
            path,
            &format!("unable to re-inspect Rust generation provenance leaf: {error}"),
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
        || before.mtime() != after.mtime()
        || before.mtime_nsec() != after.mtime_nsec()
        || after.dev() != leaf.dev()
        || after.ino() != leaf.ino()
    {
        return Err(path_error(
            path,
            "Rust generation provenance changed or became unsafe while being read",
        ));
    }
    RustGenerationRecord::parse(&bytes)
        .map(Some)
        .map_err(|message| path_error(path, &message))
}

fn recorded_intent(
    record: &RustGenerationRecord,
    paths: &RustPaths,
) -> Result<BTreeMap<String, String>, String> {
    // There is deliberately no fallback that re-reads cott.toml or generator
    // rules. Only authenticated, previously frozen intent metadata can retain
    // an agent implementation.
    match intent::recorded_fingerprints(&record.current.tools) {
        Ok(Some(hashes)) => Ok(hashes),
        Ok(None) => Ok(BTreeMap::new()),
        Err(message) => Err(path_error(
            &paths.artifact_root.join("generation.json"),
            &message,
        )),
    }
}

fn accepted_agent_record<'a>(
    record: Option<&'a RustGenerationRecord>,
    symbol: &str,
) -> Option<&'a RustBindingRecord> {
    record?
        .current
        .implementations
        .iter()
        .find(|implementation| {
            implementation.cott_symbol == symbol && implementation.owner == RustOwner::Agent
        })
}

fn retired_agent_source_is_authenticated(
    record: Option<&RustGenerationRecord>,
    callables: &BTreeMap<String, RustCallable>,
    paths: &RustPaths,
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
            implementation.owner == RustOwner::Agent
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
    record: Option<&RustGenerationRecord>,
    callable: &RustCallable,
    target_symbol: &str,
    source_origin: &Path,
    runtime_origin: &Path,
    bytes: &[u8],
    current_intent: &BTreeMap<String, String>,
    baseline_intent: Option<&BTreeMap<String, String>>,
) -> Result<AgentDisposition, String> {
    let Some(record) = record else {
        return Err(path_error(
            source_origin,
            &format!(
                "durable implementation `{}` has no matching Rust agent provenance",
                callable.symbol
            ),
        ));
    };
    let content_hash = format!("sha256:{}", sha256_hex(bytes));
    let source_text = path_text(source_origin)?;
    let runtime_text = path_text(runtime_origin)?;
    let recorded = accepted_agent_record(Some(record), &callable.symbol);
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
                "durable implementation `{}` does not match recorded Rust path, target, content identity, and ownership",
                callable.symbol
            ),
        ));
    }
    let intent_matches = baseline_intent.is_some_and(|baseline| {
        current_intent.get(&callable.symbol) == baseline.get(&callable.symbol)
            && current_intent.contains_key(&callable.symbol)
    });
    if !intent_matches {
        return Ok(AgentDisposition::Stale);
    }
    if record
        .current
        .unresolved
        .iter()
        .any(|symbol| symbol == &callable.symbol)
    {
        Ok(AgentDisposition::Pending)
    } else {
        Ok(AgentDisposition::Resolved)
    }
}
