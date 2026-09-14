use std::collections::{BTreeMap, BTreeSet, VecDeque};
use std::fs::{self, OpenOptions};
use std::io::Read;
use std::os::unix::fs::{MetadataExt, OpenOptionsExt};
use std::path::{Component, Path, PathBuf};

use tree_sitter::{Node, Parser, Tree};

use crate::hash::sha256_hex;
use crate::intent;
use crate::manifest::DartProjectConfig;
use crate::project::{DartPaths, DartSourceFile, discover_dart_sources};

use super::emit::implementation_signature;
use super::provenance::{DartBindingRecord, DartGenerationRecord};
use super::types::module_prefix;
use super::{DartBinding, DartCallable, DartOwner, DartPlan};

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
    callable: DartCallable,
    target_symbol: String,
    source: PathBuf,
    source_origin: PathBuf,
    runtime_origin: PathBuf,
    owner: DartOwner,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum AgentDisposition {
    Resolved,
    Pending,
    Stale,
}

#[derive(Clone, Debug)]
struct ExpectedFunction<'a> {
    target_symbol: &'a str,
    signature: String,
}

#[derive(Clone, Debug)]
struct ImportSyntax {
    uri: String,
    alias: Option<String>,
    deferred: bool,
    configurable: bool,
}

#[derive(Clone, Debug, Default)]
struct ImportIndex {
    prefixes: BTreeMap<String, String>,
    unprefixed: Vec<String>,
}

/// Resolves every canonical Dart callable to one source whose syntax, ABI,
/// ownership, and durable identity have all been checked. Package import
/// authority and `generator_rules` must be the exact values frozen by project
/// loading.
pub fn resolve(
    config: &DartProjectConfig,
    paths: &DartPaths,
    plan: &DartPlan,
    allowed_runtime_packages: &BTreeSet<String>,
    generator_rules: Option<&str>,
) -> Result<Vec<DartBinding>, String> {
    let callables = callable_index(plan)?;
    validate_manifest_bindings(config, paths, plan, &callables)?;

    let sources = discover_dart_sources(&paths.dart_source_dir).map_err(|error| {
        format!(
            "{}: unable to discover Dart implementation sources: {error}",
            paths.dart_source_dir.display()
        )
    })?;
    let mut parsed_sources = BTreeMap::new();
    for source in &sources {
        let tree = parse_dart(&source.source)
            .map_err(|message| path_error(&source.disk_path, &message))?;
        let index = index_source(&tree, &source.source)
            .map_err(|message| path_error(&source.disk_path, &message))?;
        parsed_sources.insert(source.disk_path.clone(), ParsedSource { tree, index });
    }

    let generation_path = paths.artifact_root.join("generation.json");
    let record = load_generation_record(&generation_path)?;
    if let Some(record) = &record
        && record.current.project_name != config.project.name
    {
        return Err(path_error(
            &generation_path,
            "Dart generation provenance belongs to a different project identity",
        ));
    }
    let rules = match (&config.generator.rules, generator_rules) {
        (Some(_), Some(rules)) => rules.as_bytes(),
        (None, None) => &[],
        (Some(relative), None) => {
            return Err(path_error(
                &paths.root.join(relative),
                "configured Dart generator rules were not supplied to binding resolution",
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
        .map_err(|message| format!("Dart implementation intent: {message}"))?;
    let baseline_intent = record
        .as_ref()
        .map(|record| recorded_intent(record, paths))
        .transpose()?;

    let private_paths = declared_private_paths(config, plan)?;
    let mut selected = Vec::new();
    let mut pending = Vec::new();
    let mut expected_agent_files = BTreeSet::new();
    let mut retired_agent_files = BTreeSet::new();

    for callable in callables.values() {
        if !requires_binding(callable) {
            continue;
        }
        let runtime_origin = runtime_origin(callable)?;
        let selection = if let Some(target) = config.dart.implementations.get(&callable.symbol) {
            let (relative, function) = parse_target_symbol(target)?;
            let source_path = paths.dart_source_dir.join(&relative);
            let source = source_at(&sources, &source_path).ok_or_else(|| {
                path_error(
                    &paths.manifest,
                    &format!(
                        "implementation binding `{}` = `{target}` does not name a discovered Dart source",
                        callable.symbol
                    ),
                )
            })?;
            let parsed = parsed_sources.get(&source.disk_path).ok_or_else(|| {
                path_error(&source.disk_path, "selected Dart source was not parsed")
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
                owner: DartOwner::Manifest,
            }
        } else {
            let relative = agent_relative_path(callable)?;
            let source_path = paths.dart_source_dir.join(&relative);
            expected_agent_files.insert(source_path.clone());
            let target_symbol = agent_target_symbol(callable)?;
            let Some(source) = source_at(&sources, &source_path) else {
                // Missing genuine source is unresolved. A prior record is never
                // allowed to stand in for absent durable bytes.
                continue;
            };
            let source_origin = project_relative(&paths.root, &source.disk_path)?;
            let disposition = validate_agent_provenance(
                record.as_ref(),
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
                owner: DartOwner::Agent,
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
                "stale or manifest-shadowed durable Dart implementation is not owned by the current plan",
            ));
        }
    }

    // Every authored source is checked for direct access to compiler-private
    // libraries or selected implementation files. Only selected implementation
    // sources receive the stricter capability and shape audit below.
    for source in &sources {
        if retired_agent_files.contains(&source.disk_path) {
            continue;
        }
        let parsed = parsed_sources
            .get(&source.disk_path)
            .ok_or_else(|| path_error(&source.disk_path, "Dart source was not parsed"))?;
        let relative = source_relative(paths, source)?;
        audit_project_imports(
            parsed.tree.root_node(),
            &source.source,
            &relative,
            &private_paths,
            &config.project.name,
            private_paths.contains(&relative),
        )
        .map_err(|message| path_error(&source.disk_path, &message))?;
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
                "one Dart source file must own exactly one canonical implementation function",
            ));
        }
        let source = source_at(&sources, source_path)
            .ok_or_else(|| path_error(source_path, "selected Dart source disappeared"))?;
        let parsed = parsed_sources
            .get(source_path)
            .ok_or_else(|| path_error(source_path, "selected Dart source was not parsed"))?;
        let selected_binding = indexes[0];
        let expected = ExpectedFunction {
            target_symbol: &selected_binding.target_symbol,
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
        let declared_effects = declaration_effects(&selected_binding.callable.declaration);
        let shared_private_targets =
            shared_private_target_names(config, plan, &selected_binding.callable)?;
        validate_restricted_tree(
            config,
            plan,
            allowed_runtime_packages,
            &source.source,
            &parsed.tree,
            &expected,
            &declared_effects,
            &private_paths,
            &shared_private_targets,
            Some(&source_relative(paths, source)?),
        )
        .map_err(|message| path_error(source_path, &message))?;
    }
    validate_owner_private_scopes(&selected, &sources, &parsed_sources)?;

    let mut bindings = Vec::with_capacity(selected.len());
    for selected in selected {
        let source = source_at(&sources, &selected.source)
            .ok_or_else(|| path_error(&selected.source, "selected Dart source disappeared"))?;
        let bytes = source.source.as_bytes().to_vec();
        bindings.push(DartBinding {
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

/// Validates a newly generated durable source. This proves source shape and
/// binding compatibility only; compiler and contract verification are separate.
/// Package import authority must be the immutable set frozen by project loading.
pub fn validate_candidate(
    config: &DartProjectConfig,
    plan: &DartPlan,
    callable: &DartCallable,
    allowed_runtime_packages: &BTreeSet<String>,
    bytes: &[u8],
) -> Result<(), String> {
    let source = std::str::from_utf8(bytes)
        .map_err(|_| "Dart candidate source is not valid UTF-8".to_owned())?;
    let planned = plan
        .callables()
        .iter()
        .filter(|candidate| candidate.symbol == callable.symbol)
        .collect::<Vec<_>>();
    if planned.len() != 1 || planned[0] != callable {
        return Err(format!(
            "Dart candidate callable `{}` is not the unique canonical callable in the plan",
            callable.symbol
        ));
    }
    if !requires_binding(callable) {
        return Err(format!(
            "compiler-owned selected method `{}` does not accept a Dart candidate",
            callable.symbol
        ));
    }
    let target_symbol = agent_target_symbol(callable)?;
    let expected = ExpectedFunction {
        target_symbol: &target_symbol,
        signature: implementation_signature(plan, callable).map_err(|message| {
            format!(
                "cannot render canonical implementation signature for `{}`: {message}",
                callable.symbol
            )
        })?,
    };
    let declared_effects = declaration_effects(&callable.declaration);
    let private_paths = declared_private_paths(config, plan)?;
    let tree = parse_dart(source)?;
    let shared_private_targets = shared_private_target_names(config, plan, callable)?;
    validate_restricted_tree(
        config,
        plan,
        allowed_runtime_packages,
        source,
        &tree,
        &expected,
        &declared_effects,
        &private_paths,
        &shared_private_targets,
        Some(&agent_relative_path(callable)?),
    )
}

/// Partitions an already-authored implementation without reparsing or rewriting
/// strings and comments as code. The compiler owns the later `part of` header.
pub fn partition_source(bytes: &[u8]) -> Result<ParsedImplementation, String> {
    let source = std::str::from_utf8(bytes)
        .map_err(|_| "Dart implementation source is not valid UTF-8".to_owned())?;
    let tree = parse_dart(source)?;
    let root = tree.root_node();
    reject_suppressions(root, source)?;

    let mut imports = Vec::new();
    let mut ranges = Vec::new();
    for child in direct_named_children(root) {
        if is_comment(child.kind()) {
            continue;
        }
        match child.kind() {
            "import_or_export" => {
                import_syntax(child, source)?;
                imports.push(node_text(child, source).to_owned());
                ranges.push(child.byte_range());
            }
            "function_declaration" => {}
            other => {
                return Err(format!(
                    "Dart implementation source cannot be partitioned with top-level `{other}`"
                ));
            }
        }
    }

    let mut body = String::with_capacity(source.len());
    let mut cursor = 0;
    for range in ranges {
        body.push_str(&source[cursor..range.start]);
        cursor = range.end;
    }
    body.push_str(&source[cursor..]);
    Ok(ParsedImplementation { imports, body })
}

pub(crate) fn requires_binding(callable: &DartCallable) -> bool {
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
    paths: &DartPaths,
    callable: &DartCallable,
) -> Result<PathBuf, String> {
    project_relative(
        &paths.root,
        &paths.dart_source_dir.join(agent_relative_path(callable)?),
    )
}

pub(crate) fn agent_target_symbol(callable: &DartCallable) -> Result<String, String> {
    let relative = agent_relative_path(callable)?;
    let private = private_callable_name(callable)?;
    target_text(&relative, &private)
}

pub(crate) fn candidate_binding(
    paths: &DartPaths,
    callable: &DartCallable,
    bytes: Vec<u8>,
) -> Result<DartBinding, String> {
    Ok(DartBinding {
        cott_symbol: callable.symbol.clone(),
        target_symbol: agent_target_symbol(callable)?,
        source_origin: agent_source_origin(paths, callable)?,
        runtime_origin: runtime_origin(callable)?,
        content_hash: format!("sha256:{}", sha256_hex(&bytes)),
        bytes,
        owner: DartOwner::Agent,
    })
}

fn callable_index(plan: &DartPlan) -> Result<BTreeMap<String, DartCallable>, String> {
    let mut callables = BTreeMap::new();
    for callable in plan.callables() {
        if callables
            .insert(callable.symbol.clone(), callable.clone())
            .is_some()
        {
            return Err(format!(
                "Dart plan contains duplicate callable `{}`",
                callable.symbol
            ));
        }
    }
    Ok(callables)
}

fn validate_manifest_bindings(
    config: &DartProjectConfig,
    paths: &DartPaths,
    plan: &DartPlan,
    callables: &BTreeMap<String, DartCallable>,
) -> Result<(), String> {
    let mut targets = BTreeMap::<String, &str>::new();
    for (symbol, target) in &config.dart.implementations {
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
        if function.starts_with("_cott_") {
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
                "Dart callables `{previous}` and `{}` collide at agent path `{}`",
                callable.symbol,
                path.display()
            ));
        }
    }
    Ok(())
}

fn declared_private_paths(
    config: &DartProjectConfig,
    plan: &DartPlan,
) -> Result<BTreeSet<PathBuf>, String> {
    let mut paths = config
        .dart
        .implementations
        .values()
        .map(|target| parse_target_symbol(target).map(|(path, _)| path))
        .collect::<Result<BTreeSet<_>, _>>()?;
    for callable in plan
        .callables()
        .iter()
        .filter(|callable| requires_binding(callable))
    {
        if !config.dart.implementations.contains_key(&callable.symbol) {
            paths.insert(agent_relative_path(callable)?);
        }
    }
    Ok(paths)
}
fn shared_private_target_names(
    config: &DartProjectConfig,
    plan: &DartPlan,
    callable: &DartCallable,
) -> Result<BTreeSet<String>, String> {
    let Some(owner_name) = callable
        .owner
        .as_ref()
        .and_then(|owner| owner.get("name"))
        .and_then(serde_json::Value::as_str)
    else {
        return Ok(BTreeSet::new());
    };
    let mut targets = BTreeSet::new();
    for candidate in plan
        .callables()
        .iter()
        .filter(|candidate| requires_binding(candidate))
    {
        let candidate_owner = candidate
            .owner
            .as_ref()
            .and_then(|owner| owner.get("name"))
            .and_then(serde_json::Value::as_str);
        if candidate_owner != Some(owner_name) {
            continue;
        }
        let target = if let Some(configured) = config.dart.implementations.get(&candidate.symbol) {
            parse_target_symbol(configured)?.1
        } else {
            private_callable_name(candidate)?
        };
        if !targets.insert(target.clone()) {
            return Err(format!(
                "owner-private Dart library `{owner_name}` has duplicate target function `{target}`"
            ));
        }
    }
    Ok(targets)
}

fn validate_owner_private_scopes(
    selected: &[SelectedBinding],
    sources: &[DartSourceFile],
    parsed_sources: &BTreeMap<PathBuf, ParsedSource>,
) -> Result<(), String> {
    let mut groups = BTreeMap::<String, Vec<&SelectedBinding>>::new();
    for binding in selected {
        let Some(owner) = &binding.callable.owner else {
            continue;
        };
        let name = owner
            .get("name")
            .and_then(serde_json::Value::as_str)
            .ok_or_else(|| {
                format!(
                    "Dart callable `{}` has malformed owner identity",
                    binding.callable.symbol
                )
            })?;
        groups.entry(name.to_owned()).or_default().push(binding);
    }

    for (owner, bindings) in groups {
        let mut functions = BTreeMap::<String, PathBuf>::new();
        let mut prefixes = BTreeMap::<String, PathBuf>::new();
        let mut unprefixed = BTreeMap::<String, PathBuf>::new();
        for binding in bindings {
            let source = source_at(sources, &binding.source)
                .ok_or_else(|| path_error(&binding.source, "selected Dart source disappeared"))?;
            let parsed = parsed_sources.get(&binding.source).ok_or_else(|| {
                path_error(&binding.source, "selected Dart source was not parsed")
            })?;
            for function in &parsed.index.functions {
                if let Some(previous) = functions.insert(function.clone(), binding.source.clone()) {
                    return Err(format!(
                        "owner-private Dart library `{owner}` has function `{function}` in both {} and {}",
                        previous.display(),
                        binding.source.display()
                    ));
                }
            }
            for node in direct_named_children(parsed.tree.root_node())
                .into_iter()
                .filter(|node| node.kind() == "import_or_export")
            {
                let import = import_syntax(node, &source.source)?;
                let collision = if let Some(prefix) = import.alias {
                    prefixes
                        .insert(prefix.clone(), binding.source.clone())
                        .map(|previous| {
                            format!(
                                "import prefix `{prefix}` in both {} and {}",
                                previous.display(),
                                binding.source.display()
                            )
                        })
                } else {
                    unprefixed
                        .insert(import.uri.clone(), binding.source.clone())
                        .map(|previous| {
                            format!(
                                "unprefixed import `{}` in both {} and {}",
                                import.uri,
                                previous.display(),
                                binding.source.display()
                            )
                        })
                };
                if let Some(collision) = collision {
                    return Err(format!(
                        "owner-private Dart library `{owner}` has colliding {collision}"
                    ));
                }
            }
        }
    }
    Ok(())
}

fn agent_relative_path(callable: &DartCallable) -> Result<PathBuf, String> {
    canonical_callable_path("cott_impl", callable)
}

fn runtime_origin(callable: &DartCallable) -> Result<PathBuf, String> {
    canonical_callable_path("dart/lib/src/cott_impl", callable)
}

fn canonical_callable_path(root: &str, callable: &DartCallable) -> Result<PathBuf, String> {
    let segments = cott_segments(&callable.symbol)?;
    let mut path = PathBuf::from(root);
    for segment in &segments[..segments.len() - 1] {
        path.push(segment);
    }
    path.push(format!("{}.dart", segments[segments.len() - 1]));
    Ok(path)
}

fn private_callable_name(callable: &DartCallable) -> Result<String, String> {
    let segments = cott_segments(&callable.symbol)?;
    Ok(format!("_cott_{}", segments.join("_")))
}

fn parse_target_symbol(target: &str) -> Result<(PathBuf, String), String> {
    let Some((path, function)) = target.split_once(':') else {
        return Err(format!(
            "invalid Dart implementation target `{target}`; expected source-relative-file.dart:_private"
        ));
    };
    if target.matches(':').count() != 1 {
        return Err(format!(
            "invalid Dart implementation target `{target}`; expected exactly one `:`"
        ));
    }
    let path = PathBuf::from(path);
    if !safe_relative(&path) || path.extension().and_then(|value| value.to_str()) != Some("dart") {
        return Err(format!(
            "invalid Dart implementation source path `{}`",
            path.display()
        ));
    }
    if !valid_dart_identifier(function) || !function.starts_with('_') {
        return Err(format!(
            "Dart implementation target `{target}` must name a private function"
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

fn valid_dart_identifier(value: &str) -> bool {
    let mut bytes = value.bytes();
    bytes
        .next()
        .is_some_and(|byte| byte == b'_' || byte == b'$' || byte.is_ascii_alphabetic())
        && bytes.all(|byte| byte == b'_' || byte == b'$' || byte.is_ascii_alphanumeric())
}

fn reserved_authored_path(path: &Path) -> bool {
    path.starts_with("cott_impl")
        || path.starts_with("lib/src/cott_impl")
        || path.starts_with("lib/src/wrappers")
        || path.starts_with("lib/modules")
        || path.starts_with(".dart_tool")
        || path.starts_with("build")
}

fn source_at<'a>(sources: &'a [DartSourceFile], path: &Path) -> Option<&'a DartSourceFile> {
    sources.iter().find(|source| source.disk_path == path)
}

fn source_relative(paths: &DartPaths, source: &DartSourceFile) -> Result<PathBuf, String> {
    let relative = source
        .disk_path
        .strip_prefix(&paths.dart_source_dir)
        .map_err(|_| {
            path_error(
                &source.disk_path,
                &format!(
                    "Dart source is outside configured tree {}",
                    paths.dart_source_dir.display()
                ),
            )
        })?;
    if !safe_relative(relative) {
        return Err(path_error(
            &source.disk_path,
            "Dart source does not have a safe source-relative path",
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
        return Err(format!("unsafe Dart provenance path `{}`", path.display()));
    }
    path.to_str()
        .map(|path| path.replace('\\', "/"))
        .ok_or_else(|| format!("non-UTF-8 Dart provenance path `{}`", path.display()))
}

fn path_error(path: &Path, message: &str) -> String {
    format!("{}: {message}", path.display())
}

fn load_generation_record(path: &Path) -> Result<Option<DartGenerationRecord>, String> {
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
                &format!("unable to open Dart generation provenance safely: {error}"),
            ));
        }
    };
    let before = file.metadata().map_err(|error| {
        path_error(
            path,
            &format!("unable to inspect opened Dart generation provenance: {error}"),
        )
    })?;
    if !before.is_file() || before.nlink() != 1 {
        return Err(path_error(
            path,
            "Dart generation provenance must be a regular non-symlink single-link file",
        ));
    }
    let mut bytes = Vec::new();
    file.read_to_end(&mut bytes).map_err(|error| {
        path_error(
            path,
            &format!("unable to read opened Dart generation provenance: {error}"),
        )
    })?;
    let after = file.metadata().map_err(|error| {
        path_error(
            path,
            &format!("unable to re-inspect opened Dart generation provenance: {error}"),
        )
    })?;
    let leaf = fs::symlink_metadata(path).map_err(|error| {
        path_error(
            path,
            &format!("unable to re-inspect Dart generation provenance leaf: {error}"),
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
            "Dart generation provenance changed or became unsafe while being read",
        ));
    }
    DartGenerationRecord::parse(&bytes)
        .map(Some)
        .map_err(|message| path_error(path, &message))
}

fn recorded_intent(
    record: &DartGenerationRecord,
    paths: &DartPaths,
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
    record: Option<&'a DartGenerationRecord>,
    symbol: &str,
) -> Option<&'a DartBindingRecord> {
    record?
        .current
        .implementations
        .iter()
        .find(|implementation| {
            implementation.cott_symbol == symbol && implementation.owner == DartOwner::Agent
        })
}

fn retired_agent_source_is_authenticated(
    record: Option<&DartGenerationRecord>,
    callables: &BTreeMap<String, DartCallable>,
    paths: &DartPaths,
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
            implementation.owner == DartOwner::Agent
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
    record: Option<&DartGenerationRecord>,
    callable: &DartCallable,
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
                "durable implementation `{}` has no matching Dart agent provenance",
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
                "durable implementation `{}` does not match recorded Dart path, target, content identity, and ownership",
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

fn index_source(tree: &Tree, source: &str) -> Result<SourceIndex, String> {
    let functions = top_level_functions(tree.root_node())
        .into_iter()
        .map(|function| function_name(function, source))
        .collect::<Result<Vec<_>, _>>()?;
    Ok(SourceIndex { functions })
}

fn parse_dart(source: &str) -> Result<Tree, String> {
    let mut parser = Parser::new();
    parser
        .set_language(&tree_sitter_dart::LANGUAGE.into())
        .map_err(|error| format!("unable to load Dart syntax grammar: {error}"))?;
    let tree = parser
        .parse(source.as_bytes(), None)
        .ok_or_else(|| "Dart syntax parser returned no tree".to_owned())?;
    if tree.root_node().has_error() {
        let error = first_syntax_error(tree.root_node()).unwrap_or(tree.root_node());
        let position = error.start_position();
        return Err(format!(
            "malformed Dart source at {}:{} near `{}`",
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

fn top_level_functions(root: Node<'_>) -> Vec<Node<'_>> {
    direct_named_children(root)
        .into_iter()
        .filter(|node| node.kind() == "function_declaration")
        .collect()
}

fn function_name(function: Node<'_>, source: &str) -> Result<String, String> {
    let signature = function
        .child_by_field_name("signature")
        .ok_or_else(|| "Dart function has no signature".to_owned())?;
    let name = signature
        .child_by_field_name("name")
        .ok_or_else(|| "Dart function has no name".to_owned())?;
    let name = node_text(name, source);
    valid_dart_identifier(name)
        .then(|| name.to_owned())
        .ok_or_else(|| format!("unsupported Dart identifier `{name}`"))
}

fn direct_named_children(node: Node<'_>) -> Vec<Node<'_>> {
    let mut cursor = node.walk();
    node.named_children(&mut cursor).collect()
}

fn import_syntax(node: Node<'_>, source: &str) -> Result<ImportSyntax, String> {
    if node.kind() != "import_or_export" {
        return Err("malformed Dart import".to_owned());
    }
    let children = direct_named_children(node);
    if children.len() != 1 || children[0].kind() != "library_import" {
        return Err("Dart export directives are not allowed in implementation sources".to_owned());
    }
    if contains_kind(children[0], "annotation") {
        return Err("annotated Dart imports are not allowed".to_owned());
    }
    let specification = direct_named_children(children[0])
        .into_iter()
        .find(|child| child.kind() == "import_specification")
        .ok_or_else(|| "Dart import has no import specification".to_owned())?;
    let uri_field = specification
        .child_by_field_name("uri")
        .ok_or_else(|| "Dart import has no URI".to_owned())?;
    let configurable = contains_kind(uri_field, "configuration_uri");
    let literals = descendants_of_kind(uri_field, "string_literal");
    if literals.len() != 1 {
        return Err("Dart import URI must be one plain string literal".to_owned());
    }
    let uri = plain_uri_literal(node_text(literals[0], source))?;
    let alias = specification
        .child_by_field_name("alias")
        .map(|node| node_text(node, source).to_owned());
    if alias
        .as_deref()
        .is_some_and(|alias| !valid_dart_identifier(alias))
    {
        return Err("Dart import has an invalid prefix".to_owned());
    }
    let deferred = syntax_tokens(specification, source)
        .iter()
        .any(|token| token == "deferred");
    Ok(ImportSyntax {
        uri,
        alias,
        deferred,
        configurable,
    })
}

fn plain_uri_literal(literal: &str) -> Result<String, String> {
    let bytes = literal.as_bytes();
    if bytes.len() < 2 || !matches!(bytes[0], b'\'' | b'"') || bytes[bytes.len() - 1] != bytes[0] {
        return Err(format!(
            "Dart import URI `{literal}` must use a plain quoted string"
        ));
    }
    let inner = &literal[1..literal.len() - 1];
    if inner.is_empty()
        || inner.bytes().any(|byte| {
            byte == b'\\'
                || byte == b'$'
                || byte == b'\n'
                || byte == b'\r'
                || byte == b'\''
                || byte == b'"'
        })
    {
        return Err(format!(
            "Dart import URI `{literal}` is not a literal safe URI"
        ));
    }
    Ok(inner.to_owned())
}

fn audit_project_imports(
    root: Node<'_>,
    source: &str,
    source_path: &Path,
    private_paths: &BTreeSet<PathBuf>,
    project_name: &str,
    implementation_source: bool,
) -> Result<(), String> {
    for child in direct_named_children(root)
        .into_iter()
        .filter(|child| child.kind() == "import_or_export")
    {
        for uri in directive_uris(child, source)? {
            if import_targets_private(source_path, &uri, private_paths, project_name)
                || (!implementation_source && imports_generated_internal(&uri, project_name))
            {
                return Err(format!(
                    "Dart directive `{uri}` bypasses a private implementation or generated facade"
                ));
            }
        }
    }
    Ok(())
}
fn directive_uris(node: Node<'_>, source: &str) -> Result<Vec<String>, String> {
    let children = direct_named_children(node);
    if children.len() != 1 {
        return Err("malformed Dart import or export directive".to_owned());
    }
    let uri = match children[0].kind() {
        "library_import" => direct_named_children(children[0])
            .into_iter()
            .find(|child| child.kind() == "import_specification")
            .and_then(|specification| specification.child_by_field_name("uri"))
            .ok_or_else(|| "Dart import has no URI".to_owned())?,
        "library_export" => children[0]
            .child_by_field_name("uri")
            .ok_or_else(|| "Dart export has no URI".to_owned())?,
        _ => return Err("malformed Dart import or export directive".to_owned()),
    };
    let literals = descendants_of_kind(uri, "string_literal");
    if literals.is_empty() {
        return Err("Dart directive has no literal URI".to_owned());
    }
    literals
        .into_iter()
        .map(|literal| plain_uri_literal(node_text(literal, source)))
        .collect()
}

fn import_targets_private(
    source_path: &Path,
    uri: &str,
    private_paths: &BTreeSet<PathBuf>,
    project_name: &str,
) -> bool {
    if uri.contains('%')
        || uri.contains("/cott_impl/")
        || uri.starts_with("cott_impl/")
        || uri.contains("/src/wrappers/")
    {
        return true;
    }
    if let Some(rest) = uri.strip_prefix(&format!("package:{project_name}/")) {
        if rest.starts_with("src/cott_impl/") || rest.starts_with("src/wrappers/") {
            return true;
        }
        let package_path = PathBuf::from("lib").join(rest);
        if private_paths.contains(&package_path) {
            return true;
        }
    }
    if uri.contains(':') || uri.starts_with('/') {
        return false;
    }
    normalize_import_path(source_path.parent().unwrap_or(Path::new("")), uri)
        .is_some_and(|path| private_paths.contains(&path))
}

fn imports_generated_internal(uri: &str, project_name: &str) -> bool {
    uri.strip_prefix(&format!("package:{project_name}/"))
        .is_some_and(|rest| rest.starts_with("src/"))
}

fn normalize_import_path(parent: &Path, uri: &str) -> Option<PathBuf> {
    if uri.is_empty()
        || uri.contains('\\')
        || uri.contains('%')
        || uri.contains('?')
        || uri.contains('#')
    {
        return None;
    }
    let mut segments = parent
        .components()
        .filter_map(|component| match component {
            Component::Normal(segment) => Some(segment.to_owned()),
            _ => None,
        })
        .collect::<Vec<_>>();
    for segment in uri.split('/') {
        match segment {
            "" | "." => {}
            ".." => {
                segments.pop()?;
            }
            value if value.as_bytes().contains(&0) => return None,
            value => segments.push(value.into()),
        }
    }
    (!segments.is_empty()).then(|| segments.into_iter().collect())
}

fn validate_restricted_tree(
    config: &DartProjectConfig,
    plan: &DartPlan,
    allowed_runtime_packages: &BTreeSet<String>,
    source: &str,
    tree: &Tree,
    expected: &ExpectedFunction<'_>,
    declared_effects: &BTreeSet<String>,
    private_paths: &BTreeSet<PathBuf>,
    shared_private_targets: &BTreeSet<String>,
    source_path: Option<&Path>,
) -> Result<(), String> {
    let root = tree.root_node();
    reject_suppressions(root, source)?;

    for child in direct_named_children(root) {
        if is_comment(child.kind()) {
            continue;
        }
        if !matches!(child.kind(), "import_or_export" | "function_declaration") {
            return Err(format!(
                "executable top-level or non-function declaration `{}` is not allowed",
                compact_node(child, source)
            ));
        }
    }

    let compiler_prefixes = compiler_prefixes(config, plan)?;
    let imports = import_index(
        root,
        source,
        config,
        plan,
        allowed_runtime_packages,
        declared_effects,
        source_path,
        private_paths,
        &compiler_prefixes,
    )?;
    let functions = top_level_functions(root);
    let target_name = parse_target_symbol(expected.target_symbol)?.1;
    let mut by_name = BTreeMap::new();
    for function in &functions {
        let name = function_name(*function, source)?;
        if by_name.insert(name.clone(), *function).is_some() {
            return Err(format!(
                "Dart implementation must not overload or duplicate function `{name}`"
            ));
        }
    }
    let target = by_name.get(&target_name).copied().ok_or_else(|| {
        format!("Dart implementation must define exactly one target function `{target_name}`")
    })?;

    for prefix in imports.prefixes.keys() {
        if by_name.contains_key(prefix) {
            return Err(format!(
                "Dart import prefix `{prefix}` collides with a top-level function"
            ));
        }
    }

    let mut allowed_reserved = compiler_prefixes.keys().cloned().collect::<BTreeSet<_>>();
    allowed_reserved.extend(expected_reserved_identifiers(&expected.signature)?);
    if target_name.starts_with("_cott_") {
        allowed_reserved.insert(target_name.clone());
    }

    validate_canonical_function(target, source, expected)?;
    for (name, function) in &by_name {
        if name != &target_name {
            validate_helper_function(*function, source, name, &compiler_prefixes)?;
        }
    }
    validate_helper_reachability(&by_name, &target_name, source)?;

    for (name, function) in &by_name {
        audit_function(
            *function,
            source,
            name,
            &target_name,
            &imports,
            declared_effects,
            &allowed_reserved,
            &compiler_prefixes,
            &by_name,
            shared_private_targets,
        )?;
    }
    Ok(())
}

fn import_index(
    root: Node<'_>,
    source: &str,
    config: &DartProjectConfig,
    plan: &DartPlan,
    allowed_runtime_packages: &BTreeSet<String>,
    declared_effects: &BTreeSet<String>,
    source_path: Option<&Path>,
    private_paths: &BTreeSet<PathBuf>,
    compiler_prefixes: &BTreeMap<String, String>,
) -> Result<ImportIndex, String> {
    let allowed = allowed_import_uris(config, plan, declared_effects)?;
    let mut index = ImportIndex::default();
    let mut identities = BTreeSet::new();
    for node in direct_named_children(root)
        .into_iter()
        .filter(|node| node.kind() == "import_or_export")
    {
        let import = import_syntax(node, source)?;
        if import.configurable {
            return Err(format!(
                "configurable Dart import `{}` is not allowed",
                import.uri
            ));
        }
        if import.deferred {
            return Err(format!(
                "deferred Dart import `{}` is not allowed",
                import.uri
            ));
        }
        if !allowed.contains(&import.uri)
            && !allowed_runtime_package_import(
                &import.uri,
                &config.project.name,
                allowed_runtime_packages,
            )
        {
            return Err(format!("forbidden Dart import `{}`", import.uri));
        }
        if source_path.is_some_and(|path| {
            import_targets_private(path, &import.uri, private_paths, &config.project.name)
        }) {
            return Err(format!(
                "Dart import `{}` bypasses a private implementation or generated facade",
                import.uri
            ));
        }
        let identity = (import.uri.clone(), import.alias.clone());
        if !identities.insert(identity) {
            return Err(format!("duplicate Dart import `{}`", import.uri));
        }
        if let Some(prefix) = import.alias {
            if prefix.starts_with("_cott_") || compiler_prefixes.contains_key(&prefix) {
                return Err(format!(
                    "authored Dart import prefix `{prefix}` shadows a compiler-owned import"
                ));
            }
            if index.prefixes.insert(prefix.clone(), import.uri).is_some() {
                return Err(format!(
                    "duplicate or shadowed Dart import prefix `{prefix}`"
                ));
            }
        } else {
            index.unprefixed.push(import.uri);
        }
    }
    Ok(index)
}

fn declaration_effects(declaration: &serde_json::Value) -> BTreeSet<String> {
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
        .filter_map(|effect| {
            effect
                .get("key")
                .and_then(serde_json::Value::as_str)
                .or_else(|| effect.as_str())
        })
        .map(str::to_owned)
        .collect()
}

fn allowed_import_uris(
    config: &DartProjectConfig,
    plan: &DartPlan,
    declared_effects: &BTreeSet<String>,
) -> Result<BTreeSet<String>, String> {
    let mut uris = [
        "dart:async",
        "dart:collection",
        "dart:convert",
        "dart:core",
        "dart:math",
        "dart:typed_data",
    ]
    .into_iter()
    .map(str::to_owned)
    .collect::<BTreeSet<_>>();
    if declared_effects
        .iter()
        .any(|effect| matches!(effect.as_str(), "file.read" | "file.write" | "network"))
    {
        uris.insert("dart:io".to_owned());
    }
    uris.insert(format!("package:{}/cott_runtime.dart", config.project.name));
    uris.insert(format!(
        "package:{}/src/cott_markers.dart",
        config.project.name
    ));
    for module in &plan.modules {
        uris.insert(type_library_uri(&config.project.name, &module.name)?);
    }
    Ok(uris)
}

fn allowed_runtime_package_import(
    uri: &str,
    project_name: &str,
    allowed_runtime_packages: &BTreeSet<String>,
) -> bool {
    if uri
        .bytes()
        .any(|byte| byte.is_ascii_control() || byte.is_ascii_whitespace())
        || uri.contains(|character| matches!(character, '\\' | '%' | '?' | '#'))
    {
        return false;
    }
    let Some((package, source)) = uri
        .strip_prefix("package:")
        .and_then(|value| value.split_once('/'))
    else {
        return false;
    };
    let mut package_bytes = package.bytes();
    if package == project_name
        || !allowed_runtime_packages.contains(package)
        || !package_bytes
            .next()
            .is_some_and(|byte| byte.is_ascii_lowercase())
        || !package_bytes
            .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit() || byte == b'_')
        || !source
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'_' | b'-' | b'.' | b'/'))
    {
        return false;
    }
    if source.split('/').any(|segment| segment.is_empty()) {
        return false;
    }
    let Ok(path) = crate::manifest::normalized_relative_path(source) else {
        return false;
    };
    path.components().collect::<PathBuf>() == path
        && path.extension().and_then(|extension| extension.to_str()) == Some("dart")
}

fn compiler_prefixes(
    config: &DartProjectConfig,
    plan: &DartPlan,
) -> Result<BTreeMap<String, String>, String> {
    let mut prefixes = BTreeMap::from([
        (
            "cott_runtime".to_owned(),
            format!("package:{}/cott_runtime.dart", config.project.name),
        ),
        (
            "cott_markers".to_owned(),
            format!("package:{}/src/cott_markers.dart", config.project.name),
        ),
    ]);
    for module in &plan.modules {
        let prefix = module_prefix(&module.name);
        let uri = type_library_uri(&config.project.name, &module.name)?;
        if prefixes.insert(prefix.clone(), uri).is_some() {
            return Err(format!(
                "colliding compiler-owned Dart import prefix `{prefix}`"
            ));
        }
    }
    Ok(prefixes)
}

fn type_library_uri(project: &str, module: &str) -> Result<String, String> {
    let segments = cott_segments(module)?;
    let mut path = segments[..segments.len() - 1].join("/");
    if !path.is_empty() {
        path.push('/');
    }
    path.push_str(segments[segments.len() - 1]);
    path.push_str(".dart");
    Ok(format!("package:{project}/src/types/{path}"))
}

fn reject_suppressions(root: Node<'_>, source: &str) -> Result<(), String> {
    fn visit(node: Node<'_>, source: &str) -> Result<(), String> {
        if node.kind() == "annotation" {
            return Err(format!(
                "Dart annotations are not allowed in implementation sources: `{}`",
                compact_node(node, source)
            ));
        }
        if is_comment(node.kind()) {
            let compact = node_text(node, source)
                .to_ascii_lowercase()
                .chars()
                .filter(|character| !character.is_whitespace())
                .collect::<String>();
            if compact.contains("ignore:")
                || compact.contains("ignore_for_file:")
                || compact.contains("analyzer:")
                || compact.contains("coverage:ignore")
                || compact.contains("dartformat:off")
                || compact.contains("dartformatoff")
                || compact.contains("@dart=")
            {
                return Err(
                    "Dart analyzer, coverage, or formatter suppression comments are not allowed"
                        .to_owned(),
                );
            }
            return Ok(());
        }
        let mut cursor = node.walk();
        for child in node.children(&mut cursor) {
            visit(child, source)?;
        }
        Ok(())
    }
    visit(root, source)
}

fn validate_canonical_function(
    function: Node<'_>,
    source: &str,
    expected: &ExpectedFunction<'_>,
) -> Result<(), String> {
    let target_name = parse_target_symbol(expected.target_symbol)?.1;
    let actual_name = function_name(function, source)?;
    if actual_name != target_name {
        return Err(format!(
            "implementation function `{actual_name}` does not match target `{target_name}`"
        ));
    }
    if has_direct_token(function, source, "augment") {
        return Err(format!(
            "function `{target_name}` cannot be an augment declaration"
        ));
    }
    let actual_tokens = signature_tokens_with_name_marker(function, source)?;
    let expected_tokens = expected_signature_tokens(&expected.signature)?;
    if actual_tokens != expected_tokens {
        return Err(format!(
            "function `{target_name}` does not match the canonical Dart ABI signature `{}`",
            expected.signature
        ));
    }
    let body = function
        .child_by_field_name("body")
        .ok_or_else(|| format!("function `{target_name}` must have an implementation body"))?;
    if node_text(body, source).trim_start().starts_with("native") {
        return Err(format!("function `{target_name}` cannot use a native body"));
    }
    Ok(())
}

#[derive(Debug, Eq, PartialEq)]
enum SignatureToken {
    ImplementationFunction,
    Token(String, String),
}

fn expected_signature_tokens(signature: &str) -> Result<Vec<SignatureToken>, String> {
    let source = format!("{signature} {{ throw StateError('unimplemented'); }}\n");
    let tree = parse_dart(&source).map_err(|message| {
        format!("emitter produced an invalid canonical Dart signature `{signature}`: {message}")
    })?;
    let functions = top_level_functions(tree.root_node());
    if functions.len() != 1 {
        return Err(format!(
            "emitter produced no unique canonical Dart function for `{signature}`"
        ));
    }
    signature_tokens_with_name_marker(functions[0], &source)
}

fn signature_tokens_with_name_marker(
    function: Node<'_>,
    source: &str,
) -> Result<Vec<SignatureToken>, String> {
    let signature = function
        .child_by_field_name("signature")
        .ok_or_else(|| "Dart function has no signature".to_owned())?;
    let name = signature
        .child_by_field_name("name")
        .ok_or_else(|| "Dart function has no name".to_owned())?;
    let name_range = name.byte_range();
    let mut tokens = Vec::new();
    collect_signature_tokens(signature, source, &name_range, &mut tokens);
    Ok(tokens)
}

fn collect_signature_tokens(
    node: Node<'_>,
    source: &str,
    name_range: &std::ops::Range<usize>,
    tokens: &mut Vec<SignatureToken>,
) {
    if node.byte_range() == *name_range {
        tokens.push(SignatureToken::ImplementationFunction);
        return;
    }
    if is_comment(node.kind()) {
        return;
    }
    if node.child_count() == 0 {
        tokens.push(SignatureToken::Token(
            node.kind().to_owned(),
            node_text(node, source).to_owned(),
        ));
        return;
    }
    let mut cursor = node.walk();
    for child in node.children(&mut cursor) {
        collect_signature_tokens(child, source, name_range, tokens);
    }
}

fn expected_reserved_identifiers(signature: &str) -> Result<BTreeSet<String>, String> {
    let source = format!("{signature} {{ throw StateError('unimplemented'); }}\n");
    let tree = parse_dart(&source)?;
    let function = top_level_functions(tree.root_node())
        .into_iter()
        .next()
        .ok_or_else(|| "emitter produced no canonical Dart function".to_owned())?;
    let canonical_name = function_name(function, &source)?;
    let signature = function
        .child_by_field_name("signature")
        .ok_or_else(|| "emitter produced a Dart function without a signature".to_owned())?;
    let mut names = BTreeSet::new();
    collect_identifiers(signature, &source, &mut names);
    names.retain(|name| name.starts_with("_cott_"));
    names.remove(&canonical_name);
    Ok(names)
}

fn validate_helper_function(
    function: Node<'_>,
    source: &str,
    name: &str,
    compiler_prefixes: &BTreeMap<String, String>,
) -> Result<(), String> {
    if !name.starts_with('_') || name.starts_with("__") || name.starts_with("_cott_") {
        return Err(format!(
            "helper function `{name}` must have one private `_` prefix and must not use the reserved `_cott_` prefix"
        ));
    }
    if compiler_prefixes.contains_key(name) {
        return Err(format!(
            "helper function `{name}` shadows a compiler-owned import"
        ));
    }
    if contains_kind(function, "annotation") {
        return Err(format!("helper function `{name}` must not be annotated"));
    }
    if has_direct_token(function, source, "augment") {
        return Err(format!(
            "helper function `{name}` cannot be an augment declaration"
        ));
    }
    let signature = function
        .child_by_field_name("signature")
        .ok_or_else(|| format!("helper function `{name}` has no signature"))?;
    let return_type = signature
        .child_by_field_name("return_type")
        .ok_or_else(|| format!("helper function `{name}` must have an explicit return type"))?;
    let return_text = compact_node(return_type, source);
    if return_text == "dynamic" || return_text == "Function" {
        return Err(format!(
            "helper function `{name}` must not use a dynamic return type"
        ));
    }
    let parameters = direct_named_children(signature)
        .into_iter()
        .find(|child| child.kind() == "formal_parameter_list")
        .ok_or_else(|| format!("helper function `{name}` has no parameter list"))?;
    if contains_kind(parameters, "optional_formal_parameters") {
        return Err(format!(
            "helper function `{name}` must not declare optional, named, or default parameters"
        ));
    }
    for parameter in descendants_of_kind(parameters, "formal_parameter") {
        if direct_named_children(parameter)
            .into_iter()
            .all(|child| child.kind() != "type")
        {
            return Err(format!(
                "helper function `{name}` must explicitly type every parameter"
            ));
        }
        let text = compact_node(parameter, source);
        if text.contains("dynamic") || text.starts_with("covariant") {
            return Err(format!(
                "helper function `{name}` has an unsupported dynamic or covariant parameter"
            ));
        }
    }
    let body = function
        .child_by_field_name("body")
        .ok_or_else(|| format!("helper function `{name}` must have an implementation body"))?;
    let body_text = node_text(body, source).trim_start();
    let expected_outer = if body_text.starts_with("async*") {
        Some("Stream<")
    } else if body_text.starts_with("async") {
        Some("Future<")
    } else if body_text.starts_with("sync*") {
        Some("Iterable<")
    } else if body_text.starts_with("native") {
        return Err(format!("helper function `{name}` cannot use a native body"));
    } else {
        None
    };
    if let Some(outer) = expected_outer
        && !return_text.starts_with(outer)
        && !return_text.contains(&format!(".{outer}"))
    {
        return Err(format!(
            "helper function `{name}` body requires explicit `{outer}...` return type"
        ));
    }
    Ok(())
}

fn validate_helper_reachability(
    functions: &BTreeMap<String, Node<'_>>,
    target: &str,
    source: &str,
) -> Result<(), String> {
    let names = functions.keys().cloned().collect::<BTreeSet<_>>();
    let mut edges = BTreeMap::<String, BTreeSet<String>>::new();
    for (name, function) in functions {
        let body = function
            .child_by_field_name("body")
            .ok_or_else(|| format!("Dart function `{name}` has no body"))?;
        let mut references = BTreeSet::new();
        collect_top_level_references(body, source, &names, &mut references)?;
        edges.insert(name.clone(), references);
    }
    let mut reachable = BTreeSet::new();
    let mut queue = VecDeque::from([target.to_owned()]);
    while let Some(name) = queue.pop_front() {
        if !reachable.insert(name.clone()) {
            continue;
        }
        if let Some(references) = edges.get(&name) {
            queue.extend(references.iter().cloned());
        }
    }
    let unused = names.difference(&reachable).cloned().collect::<Vec<_>>();
    if !unused.is_empty() {
        return Err(format!(
            "Dart implementation contains unused private helper functions: {}",
            unused.join(", ")
        ));
    }
    Ok(())
}

fn collect_top_level_references(
    node: Node<'_>,
    source: &str,
    top_level: &BTreeSet<String>,
    references: &mut BTreeSet<String>,
) -> Result<(), String> {
    if node.kind() == "identifier" {
        let name = node_text(node, source);
        if top_level.contains(name) {
            if is_declaration_identifier(node) {
                return Err(format!(
                    "local declaration `{name}` shadows a top-level implementation function"
                ));
            }
            if !is_member_property(node) && !is_nonvalue_identifier(node) {
                references.insert(name.to_owned());
            }
        }
    }
    let mut cursor = node.walk();
    for child in node.named_children(&mut cursor) {
        collect_top_level_references(child, source, top_level, references)?;
    }
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn audit_function(
    function: Node<'_>,
    source: &str,
    current: &str,
    target: &str,
    imports: &ImportIndex,
    declared_effects: &BTreeSet<String>,
    allowed_reserved: &BTreeSet<String>,
    compiler_prefixes: &BTreeMap<String, String>,
    functions: &BTreeMap<String, Node<'_>>,
    shared_private_targets: &BTreeSet<String>,
) -> Result<(), String> {
    let mut errors = Vec::new();
    audit_node(
        function,
        source,
        current,
        target,
        imports,
        declared_effects,
        allowed_reserved,
        compiler_prefixes,
        functions,
        shared_private_targets,
        &mut errors,
    );
    if errors.is_empty() {
        Ok(())
    } else {
        Err(errors.join("; "))
    }
}

#[allow(clippy::too_many_arguments)]
fn audit_node(
    node: Node<'_>,
    source: &str,
    current: &str,
    target: &str,
    imports: &ImportIndex,
    declared_effects: &BTreeSet<String>,
    allowed_reserved: &BTreeSet<String>,
    compiler_prefixes: &BTreeMap<String, String>,
    functions: &BTreeMap<String, Node<'_>>,
    shared_private_targets: &BTreeSet<String>,
    errors: &mut Vec<String>,
) {
    if is_comment(node.kind()) {
        return;
    }
    match node.kind() {
        "annotation" => push_error(
            errors,
            "Dart annotations are not allowed in implementation sources".to_owned(),
        ),
        "local_function_declaration" => push_error(
            errors,
            "local named function declarations are not allowed in Dart implementations".to_owned(),
        ),
        "assert_statement" => push_error(
            errors,
            "Dart assert statements are not allowed because they disappear in production"
                .to_owned(),
        ),
        "native" => push_error(errors, "native Dart bodies are not allowed".to_owned()),
        "symbol_literal" => push_error(
            errors,
            "Dart Symbol literals are not allowed in implementation sources".to_owned(),
        ),
        "call_expression" => {
            if let Some(callee) = node.child_by_field_name("function") {
                if let Some(path) = reference_path(callee, source) {
                    audit_reference(
                        &path,
                        current,
                        target,
                        imports,
                        declared_effects,
                        allowed_reserved,
                        functions,
                        shared_private_targets,
                        errors,
                    );
                    let resolved = resolve_reference(&path, imports);
                    if forbidden_call(&resolved, &path) {
                        push_error(
                            errors,
                            format!(
                                "reflection, dynamic execution, process, or verifier-control call `{}` is not allowed",
                                compact_node(callee, source)
                            ),
                        );
                    }
                } else if let Some(leaf) = reference_leaf(callee, source) {
                    audit_member_leaf(
                        leaf,
                        current,
                        target,
                        declared_effects,
                        true,
                        functions,
                        shared_private_targets,
                        errors,
                    );
                    if forbidden_call(leaf, leaf) {
                        push_error(
                            errors,
                            format!(
                                "reflection, dynamic execution, process, or verifier-control call `{}` is not allowed",
                                compact_node(callee, source)
                            ),
                        );
                    }
                }
            }
        }
        "member_expression" | "null_aware_member_expression" | "assignable_expression" => {
            let path = reference_path(node, source);
            // I/O authority comes from a complete import path when available;
            // private/control member leaves are always checked independently.
            if let Some(property) = node.child_by_field_name("property") {
                audit_member_leaf(
                    node_text(property, source),
                    current,
                    target,
                    declared_effects,
                    path.is_none(),
                    functions,
                    shared_private_targets,
                    errors,
                );
            }
            if !is_member_chain_child(node)
                && let Some(path) = path
            {
                audit_reference(
                    &path,
                    current,
                    target,
                    imports,
                    declared_effects,
                    allowed_reserved,
                    functions,
                    shared_private_targets,
                    errors,
                );
            }
        }
        "identifier" | "type_identifier" => {
            let canonical_signature = current == target && inside_function_signature(node);
            if !canonical_signature && !is_reference_chain_child(node) {
                let name = node_text(node, source);
                audit_reference(
                    name,
                    current,
                    target,
                    imports,
                    declared_effects,
                    allowed_reserved,
                    functions,
                    shared_private_targets,
                    errors,
                );
            }
            let name = node_text(node, source);
            if (compiler_prefixes.contains_key(name) || imports.prefixes.contains_key(name))
                && is_declaration_identifier(node)
            {
                push_error(
                    errors,
                    format!("declaration `{name}` shadows a Dart import prefix"),
                );
            }
            let reserved_declaration = is_declaration_identifier(node);
            let compiler_prefix = compiler_prefixes.contains_key(name);
            if name.starts_with("_cott_")
                && (!allowed_reserved.contains(name)
                    || !compiler_prefix && current != target
                    || reserved_declaration
                        && !(current == target && inside_function_signature(node)))
            {
                push_error(
                    errors,
                    format!("reserved implementation identifier `{name}` is not allowed"),
                );
            }
            if name == "dynamic" {
                push_error(errors, "dynamic Dart types are not allowed".to_owned());
            }
        }
        "dynamic" => push_error(errors, "dynamic Dart types are not allowed".to_owned()),
        _ => {}
    }

    let mut cursor = node.walk();
    for child in node.children(&mut cursor) {
        audit_node(
            child,
            source,
            current,
            target,
            imports,
            declared_effects,
            allowed_reserved,
            compiler_prefixes,
            functions,
            shared_private_targets,
            errors,
        );
    }
}

#[allow(clippy::too_many_arguments)]
fn audit_reference(
    reference: &str,
    current: &str,
    target: &str,
    imports: &ImportIndex,
    declared_effects: &BTreeSet<String>,
    allowed_reserved: &BTreeSet<String>,
    functions: &BTreeMap<String, Node<'_>>,
    shared_private_targets: &BTreeSet<String>,
    errors: &mut Vec<String>,
) {
    let resolved = resolve_reference(reference, imports);
    let first = reference.split('.').next().unwrap_or(reference);
    audit_reference_identity(
        reference,
        &resolved,
        current,
        target,
        declared_effects,
        true,
        allowed_reserved.contains(first),
        functions,
        shared_private_targets,
        errors,
    );
}

fn audit_member_leaf(
    leaf: &str,
    current: &str,
    target: &str,
    declared_effects: &BTreeSet<String>,
    check_io_authority: bool,
    functions: &BTreeMap<String, Node<'_>>,
    shared_private_targets: &BTreeSet<String>,
    errors: &mut Vec<String>,
) {
    audit_reference_identity(
        leaf,
        leaf,
        current,
        target,
        declared_effects,
        check_io_authority,
        false,
        functions,
        shared_private_targets,
        errors,
    );
}

#[allow(clippy::too_many_arguments)]
fn audit_reference_identity(
    reference: &str,
    resolved: &str,
    current: &str,
    target: &str,
    declared_effects: &BTreeSet<String>,
    check_io_authority: bool,
    reserved_allowed: bool,
    functions: &BTreeMap<String, Node<'_>>,
    shared_private_targets: &BTreeSet<String>,
    errors: &mut Vec<String>,
) {
    let first = reference.split('.').next().unwrap_or(reference);
    if first.starts_with("_cott_") && !reserved_allowed {
        push_error(
            errors,
            format!("private implementation reference `{reference}` is not allowed"),
        );
    }
    if shared_private_targets.contains(first) && first != target {
        push_error(
            errors,
            format!("private implementation reference `{reference}` bypasses its owner wrapper"),
        );
    }
    if functions.contains_key(first) && first != current && first == target {
        push_error(
            errors,
            format!("helper `{current}` cannot call the canonical entry point `{target}`"),
        );
    }
    if forbidden_reference(resolved, reference) {
        push_error(
            errors,
            format!(
                "runtime reflection, dynamic execution, process, or verifier-control reference `{reference}` is not allowed"
            ),
        );
    }
    if check_io_authority && forbidden_dart_io_reference(resolved, declared_effects) {
        push_error(
            errors,
            format!(
                "Dart I/O reference `{reference}` is not authorized by the callable's declared effects"
            ),
        );
    }
}

fn resolve_reference(reference: &str, imports: &ImportIndex) -> String {
    let (first, rest) = reference
        .split_once('.')
        .map_or((reference, None), |(first, rest)| (first, Some(rest)));
    if let Some(uri) = imports.prefixes.get(first) {
        return rest.map_or_else(|| uri.clone(), |rest| format!("{uri}#{rest}"));
    }
    if imports
        .unprefixed
        .iter()
        .any(|uri| uri.ends_with("/cott_runtime.dart"))
        && known_runtime_identifier(first)
    {
        return rest.map_or_else(
            || format!("cott_runtime#{first}"),
            |rest| format!("cott_runtime#{first}.{rest}"),
        );
    }
    if imports.unprefixed.iter().any(|uri| uri == "dart:io") && known_dart_io_identifier(first) {
        return rest.map_or_else(
            || format!("dart:io#{first}"),
            |rest| format!("dart:io#{first}.{rest}"),
        );
    }
    reference.to_owned()
}

fn reference_path(node: Node<'_>, source: &str) -> Option<String> {
    match node.kind() {
        "identifier" | "type_identifier" => Some(node_text(node, source).to_owned()),
        "member_expression" | "null_aware_member_expression" | "assignable_expression" => {
            let object = node.child_by_field_name("object")?;
            let property = node.child_by_field_name("property")?;
            Some(format!(
                "{}.{}",
                reference_path(object, source)?,
                node_text(property, source)
            ))
        }
        "instantiation_expression" => reference_path(node.child_by_field_name("function")?, source),
        "parenthesized_expression" | "null_assertion_expression" => direct_named_children(node)
            .into_iter()
            .find_map(|child| reference_path(child, source)),
        _ => None,
    }
}

fn reference_leaf<'a>(node: Node<'_>, source: &'a str) -> Option<&'a str> {
    match node.kind() {
        "identifier" | "type_identifier" => Some(node_text(node, source)),
        "member_expression" | "null_aware_member_expression" | "assignable_expression" => node
            .child_by_field_name("property")
            .map(|property| node_text(property, source)),
        "instantiation_expression" => reference_leaf(node.child_by_field_name("function")?, source),
        "parenthesized_expression" | "null_assertion_expression" => direct_named_children(node)
            .into_iter()
            .find_map(|child| reference_leaf(child, source)),
        _ => None,
    }
}

fn forbidden_call(resolved: &str, raw: &str) -> bool {
    forbidden_reference(resolved, raw)
        || matches!(
            leaf_name(resolved),
            "apply" | "noSuchMethod" | "loadLibrary"
        )
        || matches!(
            leaf_name(raw),
            "eval" | "spawn" | "spawnUri" | "kill" | "killPid" | "exit"
        )
}

fn forbidden_reference(resolved: &str, raw: &str) -> bool {
    let leaf = leaf_name(resolved);
    let raw_leaf = leaf_name(raw);
    let imported = resolved != raw && (resolved.contains('#') || resolved.contains(':'));
    let mut components = resolved
        .split(['.', '#', '/', ':'])
        .collect::<BTreeSet<_>>();
    if !imported {
        components.extend(raw.split('.'));
    }
    components.iter().any(|name| {
        matches!(
            *name,
            "dynamic"
                | "TODO"
                | "UnimplementedError"
                | "Invocation"
                | "MirrorSystem"
                | "ClassMirror"
                | "InstanceMirror"
                | "LibraryMirror"
                | "runtimeType"
                | "noSuchMethod"
                | "DynamicLibrary"
                | "Isolate"
                | "Platform"
                | "Process"
                | "ProcessInfo"
                | "ProcessResult"
                | "ProcessSignal"
                | "ProcessStartMode"
                | "IOOverrides"
                | "HttpOverrides"
                | "Stdin"
                | "Stdout"
                | "StdioType"
                | "stdin"
                | "stdout"
                | "stderr"
                | "exitCode"
                | "pid"
                | "killPid"
                | "CottCancellationSource"
                | "CottTaskScope"
                | "CottResourceGuard"
                | "CottGuardLease"
                | "CottResourceContract"
                | "CottStateField"
                | "CottTransition"
                | "CottInvariant"
                | "CottStateSnapshot"
                | "CottClauseObservation"
                | "CottObservation"
                | "CottFixtureContext"
                | "CottCheckedView"
                | "CottViewAccess"
                | "CottTypes"
                | "CottNominalCarrier"
                | "cottCarrier"
                | "allows"
                | "cottRebuildCarrier"
                | "checkedNominal"
                | "viewSeal"
                | "RuntimeValidation"
                | "withTestObservation"
                | "withTestObservationAsync"
                | "withFixtureContext"
                | "withFixtureContextAsync"
                | "recordUnobserved"
                | "checkContract"
                | "requireContract"
                | "ensureContract"
                | "invariant"
                | "requireEffect"
                | "shouldValidate"
                | "contractsEnabled"
                | "validateInitial"
                | "validateTransition"
                | "activateObservation"
                | "installFixtureContext"
                | "compilerLease"
        )
    }) || resolved.ends_with("#Function.apply")
        || resolved.contains("#Function.apply.")
        || resolved.ends_with(".Function.apply")
        || resolved.contains(".Function.apply.")
        || raw == "Function.apply"
        || raw.starts_with("Function.apply.")
        || matches!(
            leaf,
            "withTestObservation"
                | "withTestObservationAsync"
                | "withFixtureContext"
                | "withFixtureContextAsync"
                | "recordUnobserved"
                | "checkContract"
                | "requireContract"
                | "ensureContract"
                | "invariant"
                | "requireEffect"
                | "shouldValidate"
                | "contractsEnabled"
                | "validateInitial"
                | "validateTransition"
                | "activateObservation"
                | "installFixtureContext"
                | "compilerLease"
        )
        || matches!(
            raw_leaf,
            "reflect"
                | "reflectClass"
                | "spawn"
                | "spawnUri"
                | "kill"
                | "killPid"
                | "exit"
                | "setExitCode"
        )
}

fn forbidden_dart_io_reference(resolved: &str, declared_effects: &BTreeSet<String>) -> bool {
    let reference = if let Some(reference) = resolved.strip_prefix("dart:io#") {
        reference
    } else {
        // Owner-private libraries merge imports from several implementation
        // parts. Requiring this source's own import prevents one callable from
        // borrowing a sibling's broader I/O authority.
        return resolved.split('.').any(known_dart_io_identifier);
    };
    if reference == "Directory.current" || reference.starts_with("Directory.current.") {
        return true;
    }
    let root = reference.split('.').next().unwrap_or(reference);
    if file_io_identifier(root) {
        return !declared_effects
            .iter()
            .any(|effect| matches!(effect.as_str(), "file.read" | "file.write"));
    }
    if network_io_identifier(root) {
        return !declared_effects.contains("network");
    }
    !safe_common_io_identifier(root)
}

fn file_io_identifier(name: &str) -> bool {
    matches!(
        name,
        "Directory"
            | "File"
            | "FileLock"
            | "FileMode"
            | "FileStat"
            | "FileSystemCreateEvent"
            | "FileSystemDeleteEvent"
            | "FileSystemEntity"
            | "FileSystemEntityType"
            | "FileSystemEvent"
            | "FileSystemException"
            | "FileSystemModifyEvent"
            | "FileSystemMoveEvent"
            | "Link"
            | "PathAccessException"
            | "PathExistsException"
            | "PathNotFoundException"
            | "RandomAccessFile"
    )
}

fn network_io_identifier(name: &str) -> bool {
    matches!(
        name,
        "BadCertificateCallback"
            | "HttpClientBearerCredentials"
            | "HttpClientResponseCompressionState"
            | "InterfaceAddress"
            | "RedirectException"
            | "ResourceHandle"
            | "SameSite"
            | "SocketControlMessage"
            | "SocketMessage"
            | "SocketOption"
            | "TlsException"
            | "TlsProtocolVersion"
            | "WebSocketTransformer"
            | "CertificateException"
            | "CompressionOptions"
            | "ConnectionTask"
            | "ContentType"
            | "Cookie"
            | "Datagram"
            | "HandshakeException"
            | "HeaderValue"
            | "HttpClient"
            | "HttpClientBasicCredentials"
            | "HttpClientCredentials"
            | "HttpClientDigestCredentials"
            | "HttpClientRequest"
            | "HttpClientResponse"
            | "HttpConnectionInfo"
            | "HttpConnectionsInfo"
            | "HttpDate"
            | "HttpException"
            | "HttpHeaders"
            | "HttpRequest"
            | "HttpResponse"
            | "HttpServer"
            | "HttpSession"
            | "HttpStatus"
            | "InternetAddress"
            | "InternetAddressType"
            | "NetworkInterface"
            | "RawDatagramSocket"
            | "RawSecureServerSocket"
            | "RawSecureSocket"
            | "RawServerSocket"
            | "RawSocket"
            | "RawSocketEvent"
            | "RawSocketOption"
            | "RawSynchronousSocket"
            | "RedirectInfo"
            | "SecureServerSocket"
            | "SecureSocket"
            | "SecurityContext"
            | "ServerSocket"
            | "Socket"
            | "SocketDirection"
            | "SocketException"
            | "WebSocket"
            | "WebSocketException"
            | "WebSocketStatus"
            | "X509Certificate"
    )
}

fn safe_common_io_identifier(name: &str) -> bool {
    matches!(
        name,
        "BytesBuilder"
            | "GZipCodec"
            | "IOException"
            | "IOSink"
            | "OSError"
            | "Pipe"
            | "ProcessException"
            | "RawZLibFilter"
            | "ReadPipe"
            | "SignalException"
            | "StdinException"
            | "StdoutException"
            | "SystemEncoding"
            | "WritePipe"
            | "ZLibCodec"
            | "ZLibDecoder"
            | "ZLibEncoder"
            | "ZLibOption"
            | "gzip"
            | "systemEncoding"
            | "zlib"
    )
}

fn known_dart_io_identifier(name: &str) -> bool {
    file_io_identifier(name)
        || network_io_identifier(name)
        || safe_common_io_identifier(name)
        || matches!(
            name,
            "HttpOverrides"
                | "IOOverrides"
                | "Platform"
                | "Process"
                | "ProcessInfo"
                | "ProcessResult"
                | "ProcessSignal"
                | "ProcessStartMode"
                | "Stdin"
                | "StdioType"
                | "Stdout"
                | "exit"
                | "exitCode"
                | "killPid"
                | "pid"
                | "sleep"
                | "stderr"
                | "stdin"
                | "stdioType"
                | "stdout"
        )
}

fn known_runtime_identifier(name: &str) -> bool {
    name == "CottRuntime"
        || name.starts_with("Cott")
        || matches!(
            name,
            "Some"
                | "Nothing"
                | "Ok"
                | "Err"
                | "JsonValue"
                | "JsonNull"
                | "JsonBool"
                | "JsonInteger"
                | "JsonFloat"
                | "JsonString"
                | "JsonArray"
                | "JsonObject"
                | "Opaque"
                | "Dyn"
        )
}

fn leaf_name(value: &str) -> &str {
    value.rsplit(['.', '#', '/', ':']).next().unwrap_or(value)
}

fn is_declaration_identifier(node: Node<'_>) -> bool {
    let range = node.byte_range();
    let mut ancestor = node.parent();
    for _ in 0..5 {
        let Some(parent) = ancestor else {
            break;
        };
        let named_declaration = parent
            .child_by_field_name("name")
            .is_some_and(|name| name.byte_range() == range)
            && matches!(
                parent.kind(),
                "formal_parameter"
                    | "type_parameter"
                    | "initialized_variable_definition"
                    | "initialized_identifier"
                    | "declared_identifier"
                    | "variable_pattern"
            );
        let catch_declaration = parent.kind() == "catch_clause"
            && ["exception", "stack_trace"].iter().any(|field| {
                parent
                    .child_by_field_name(field)
                    .is_some_and(|name| name.byte_range() == range)
            });
        if named_declaration || catch_declaration {
            return true;
        }
        if matches!(parent.kind(), "function_signature" | "function_declaration") {
            break;
        }
        ancestor = parent.parent();
    }
    false
}
fn is_nonvalue_identifier(node: Node<'_>) -> bool {
    let mut ancestor = node.parent();
    while let Some(parent) = ancestor {
        match parent.kind() {
            "label" | "type" | "type_arguments" | "type_parameter" => return true,
            "call_expression"
            | "function_body"
            | "function_expression_body"
            | "assignment_expression"
            | "return_statement"
            | "expression_statement" => return false,
            _ => ancestor = parent.parent(),
        }
    }
    false
}

fn has_direct_token(node: Node<'_>, source: &str, token: &str) -> bool {
    let mut cursor = node.walk();
    node.children(&mut cursor)
        .any(|child| child.child_count() == 0 && node_text(child, source) == token)
}

fn inside_function_signature(node: Node<'_>) -> bool {
    let mut ancestor = node.parent();
    while let Some(parent) = ancestor {
        match parent.kind() {
            "function_signature" => return true,
            "function_body" | "function_declaration" => return false,
            _ => ancestor = parent.parent(),
        }
    }
    false
}

fn is_member_property(node: Node<'_>) -> bool {
    node.parent().is_some_and(|parent| {
        matches!(
            parent.kind(),
            "member_expression" | "null_aware_member_expression"
        ) && parent
            .child_by_field_name("property")
            .is_some_and(|property| property.byte_range() == node.byte_range())
    })
}

fn is_member_chain_child(node: Node<'_>) -> bool {
    node.parent().is_some_and(|parent| {
        matches!(
            parent.kind(),
            "member_expression" | "null_aware_member_expression" | "assignable_expression"
        ) && parent
            .child_by_field_name("object")
            .is_some_and(|object| object.byte_range() == node.byte_range())
    })
}

fn is_reference_chain_child(node: Node<'_>) -> bool {
    node.parent().is_some_and(|parent| {
        matches!(
            parent.kind(),
            "member_expression" | "null_aware_member_expression" | "instantiation_expression"
        ) || parent.kind() == "assignable_expression"
            && parent.child_by_field_name("property").is_some()
    })
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
    node.named_children(&mut cursor)
        .any(|child| contains_kind(child, kind))
}

fn descendants_of_kind<'tree>(node: Node<'tree>, kind: &str) -> Vec<Node<'tree>> {
    fn visit<'tree>(node: Node<'tree>, kind: &str, found: &mut Vec<Node<'tree>>) {
        if node.kind() == kind {
            found.push(node);
        }
        let mut cursor = node.walk();
        for child in node.named_children(&mut cursor) {
            visit(child, kind, found);
        }
    }
    let mut found = Vec::new();
    visit(node, kind, &mut found);
    found
}

fn collect_identifiers(node: Node<'_>, source: &str, names: &mut BTreeSet<String>) {
    if matches!(node.kind(), "identifier" | "type_identifier") {
        names.insert(node_text(node, source).to_owned());
    }
    let mut cursor = node.walk();
    for child in node.named_children(&mut cursor) {
        collect_identifiers(child, source, names);
    }
}

fn node_text<'a>(node: Node<'_>, source: &'a str) -> &'a str {
    source.get(node.byte_range()).unwrap_or("")
}

fn is_comment(kind: &str) -> bool {
    kind.contains("comment")
}

fn push_error(errors: &mut Vec<String>, message: String) {
    if !errors.contains(&message) {
        errors.push(message);
    }
}
