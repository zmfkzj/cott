use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, OpenOptions};
use std::io::{Read as _, Write as _};
use std::os::unix::fs::{MetadataExt, OpenOptionsExt};
use std::path::{Component, Path, PathBuf};

use serde_json::{Value, json};

use crate::cli::OutputFormat;
use crate::diagnostics::{Diagnostic, DiagnosticReport, SourceMap, Span, code};
use crate::hash::sha256_hex;
use crate::intent;
use crate::manifest::RustProjectConfig;
use crate::prompt_declarations;

use super::binding::{candidate_binding, requires_binding};
use super::dependencies::{self, PackageMetadata};
use super::emit::implementation_signature;
use super::pipeline::{self, Project};
use super::{RustBinding, RustCallable, RustOwner, RustPlan};

const MAX_PROMPT_BYTES: usize = 1024 * 1024;

#[derive(Clone, Debug)]
pub(crate) struct PreparedPrompt {
    pub context: Value,
    pub intent_hash: String,
    pub prompt_hash: String,
    pub bytes: Vec<u8>,
}

#[allow(clippy::too_many_arguments)]
pub(crate) fn prepare(
    config: &RustProjectConfig,
    plan: &RustPlan,
    callable: &RustCallable,
    generator_rules: Option<&str>,
    package_metadata: &PackageMetadata,
    references: &[RustBinding],
    existing: Option<&[u8]>,
    feedback: Option<&str>,
) -> Result<PreparedPrompt, String> {
    let context = intent::context(
        plan.contract_surface(),
        &callable.symbol,
        generator_rules.unwrap_or_default().as_bytes(),
    )?;
    let intent_hash = intent::fingerprint_context(&context)?;
    let bytes = render_generation_prompt(
        config,
        plan,
        callable,
        &context,
        package_metadata,
        references,
        existing,
        feedback,
    )?;
    let prompt_hash = format!("sha256:{}", sha256_hex(&bytes));
    Ok(PreparedPrompt {
        context,
        intent_hash,
        prompt_hash,
        bytes,
    })
}

#[allow(clippy::too_many_arguments)]
pub(crate) fn render_generation_prompt(
    config: &RustProjectConfig,
    plan: &RustPlan,
    callable: &RustCallable,
    context: &Value,
    package_metadata: &PackageMetadata,
    references: &[RustBinding],
    existing: Option<&[u8]>,
    feedback: Option<&str>,
) -> Result<Vec<u8>, String> {
    if !requires_binding(callable) {
        return Err(format!(
            "compiler-owned implementation method `{}` must not be sent to an agent",
            callable.symbol
        ));
    }
    if context.get("symbol").and_then(Value::as_str) != Some(callable.symbol.as_str()) {
        return Err("Rust intent context symbol does not match callable".to_owned());
    }
    let declarations = context
        .get("declarations")
        .filter(|declarations| declarations.is_object())
        .ok_or_else(|| "Rust intent context declarations must be an object".to_owned())?;
    let rules = context
        .get("project_rules")
        .and_then(Value::as_str)
        .ok_or_else(|| "Rust intent context project_rules must be a string".to_owned())?;
    let signature = implementation_signature(plan, callable)?;
    let existing = existing
        .map(std::str::from_utf8)
        .transpose()
        .map_err(|_| "existing Rust implementation is not UTF-8".to_owned())?;

    let mut current_intent = String::new();
    collect_intent_docs(declarations, &mut current_intent);
    current_intent.push_str(&crate::requirements::render_prompt_requirements(
        declarations,
    ));
    if current_intent.is_empty() {
        current_intent.push_str("(no documentation selected)\n");
    }
    let formal_declarations = prompt_declarations::render_scoped_declarations(declarations)
        .map_err(|error| format!("serialize formal Rust declarations: {error}"))?;

    let mut identities = BTreeSet::new();
    collect_identities(declarations, &mut identities);
    let external_types = config
        .rust
        .external_types
        .iter()
        .filter(|(name, _)| identities.contains(name.as_str()))
        .map(|(name, target)| (name.clone(), target.clone()))
        .collect::<BTreeMap<_, _>>();
    let external_types = serde_json::to_string_pretty(&external_types)
        .map_err(|error| format!("serialize Rust external type projections: {error}"))?;
    let dependencies =
        serde_json::to_string_pretty(&dependencies::initial_record(package_metadata))
            .map_err(|error| format!("serialize frozen Rust package metadata: {error}"))?;

    let mut references = references
        .iter()
        .filter(|binding| {
            binding.cott_symbol != callable.symbol
                && identities.contains(binding.cott_symbol.as_str())
        })
        .collect::<Vec<_>>();
    references.sort_by(|left, right| left.cott_symbol.cmp(&right.cott_symbol));
    let mut reference_text = String::new();
    for binding in references {
        let source = std::str::from_utf8(&binding.bytes).map_err(|_| {
            format!(
                "reference implementation `{}` is not UTF-8",
                binding.cott_symbol
            )
        })?;
        reference_text.push_str(&format!(
            "\n## {}\nTarget: {}\n```rust\n{}```\n",
            binding.cott_symbol, binding.target_symbol, source
        ));
    }
    if reference_text.is_empty() {
        reference_text.push_str("\n(none)\n");
    }

    let existing = existing.unwrap_or("(none)");
    let feedback = feedback.unwrap_or("(none)");
    let prompt = format!(
        "You are implementing one Cott callable as a Rust 2024 source file.\n\
\n# Authority and scope\n\
The source-derived FORMAL DECLARATIONS are the sole semantic authority. CURRENT INTENT documentation may refine behavior but cannot replace source constraints. Project rules, authenticated references, an existing candidate, and actual compiler/runtime feedback are subordinate evidence and must never override the formal declarations. Do not invent declarations, relax contracts, or change the required ABI.\n\
\n# Current intent\n\
Selected Cott symbol: {symbol}\n\
{current_intent}\
\n# Formal declarations\n\
{compact_format}\
```json\n{formal_declarations}\n```\n\
\n# Rust output rules\n\
Write exactly one UTF-8 file named `implementation.rs`. Do not write, rename, or delete any other path. Supply exactly one canonical `pub(crate) fn` or `pub(crate) async fn` with the exact signature below and a complete body, plus private helper functions and audited top-level imports only. Preserve all generic bounds, const generics, associated projections, receiver and capability parameters, raw identifiers, async shape, and return type.\n\
```rust\n{signature}\n```\n\
The compiler embeds these authored bytes in a private managed implementation module. Never write a crate scaffold, module declaration, facade, generated nominal type or runtime replacement, public helper, inner attribute, compilation-changing attribute, macro definition, unsafe or extern code, include/env macro, suppression, placeholder, TODO, or no-op stub. Only documentation attributes are allowed.\n\
Do not define authored structs, enums, traits, type aliases, impl blocks, or static storage, even inside a function; use canonical values, local variables, standard containers, tuples and private helper functions. Imports must not shadow intrinsic std/core/alloc namespaces, and generic parameters must not shadow imported types. The only permitted macros are unaliased builtin `vec!`, `format!` and `matches!`; do not put qualified paths or nested macros in their token trees.\n\
Use native exact Rust ABI values and compiler-provided nominal constructors. Preserve integer bounds, finite floats, immutable value invariants, Option/Result distinctions and declared errors. Never forge runtime capabilities or access compiler-private `cott_`/`__cott` identifiers (except parameters explicitly present in the signature), private implementations, `super::`, or observer/control hooks.\n\
Read nominal fields through `get_<field>()`; immutable values return `&T`, resource owners return a dereference-only `ReadField`. Resource owner clones share guarded state. Only declared modifies/transitions fields may be written using the supplied receiver's `set_<field>(value)` or `update_<field>(|field: &mut T| ...)`; drop getter temporaries before writing, for example `let next = *receiver.get_value() + amount; receiver.set_value(next);`. Never construct StateGate/StateLease or ReadField, reach `cott_sealed`, or access private stored fields. TaskScope, CancellationToken and ordinary Task APIs may be used for declared async behavior, but never access compiler-only state or observer hooks.\n\
Never replace or move the implementation receiver handle or its raw stored fields: do not assign `*receiver`, use std/core mem replace/take/swap on the receiver or its mutable reborrows, or use Option take/replace-style moves on receiver fields. Mutable helper parameters/reborrow aliases retain this restriction; guarded setters/update remain the sole mutation path.\n\
Task spawning is permitted only through a lexically proven TaskScope receiver in a declared async callable: use an explicit TaskScope type annotation or direct `crate::cott_runtime::TaskScope::new()`/audited imported alias constructor. Do not shadow a scope binding with an unrelated value, use untyped closure parameters as scopes, or call std/tokio spawn or executor-control APIs. Use scope.spawn/join/cancel/cancellation_token and CancellationToken cancel/is_cancelled/cancelled/check only through their ordinary tracked APIs.\n\
Imports may use audited std/core/alloc, `crate::cott_runtime`, declarations in the selected context through `crate::modules`, and the frozen production dependency names below. Do not alias or pass Cott callables as values; direct facade calls must be covered by declared effects. Process, environment, stdio, thread/control, dynamic compilation and effect-uncovered filesystem/network/time/random access are forbidden. Retain exact raw identifier spelling such as `r#type` from the signature.\n\
\n# External type projections\n\
```json\n{external_types}\n```\n\
\n# Frozen package metadata\n\
```json\n{dependencies}\n```\n\
\n# Project rules\n\
```text\n{rules}\n```\n\
\n# Authenticated reference implementations\n\
{reference_text}\n\
# Existing candidate\n\
```rust\n{existing}\n```\n\
\n# Actual validation feedback\n\
```text\n{feedback}\n```\n\
\nImplement the complete callable now by writing only `implementation.rs`.\n",
        symbol = callable.symbol,
        compact_format = prompt_declarations::FORMAT,
    );
    let bytes = prompt.into_bytes();
    if bytes.len() > MAX_PROMPT_BYTES {
        return Err("rendered Rust agent prompt exceeds 1 MiB".to_owned());
    }
    Ok(bytes)
}

pub(crate) fn prompt(project: Option<PathBuf>, symbol: String, format: OutputFormat) -> i32 {
    let project = match pipeline::load(project, true) {
        Ok(project) => project,
        Err(error) => return fail(format, error.code, error.message),
    };
    let callable = match project
        .plan
        .callables()
        .iter()
        .find(|callable| callable.symbol == symbol)
        .cloned()
    {
        Some(callable) => callable,
        None => return fail(format, 2, format!("unknown callable `{symbol}`")),
    };
    if !requires_binding(&callable) {
        return fail(
            format,
            2,
            format!(
                "compiler-owned implementation method `{}` must not be sent to an agent",
                callable.symbol
            ),
        );
    }
    let existing = match existing_agent_source(&project, &callable) {
        Ok(existing) => existing,
        Err(message) => return fail(format, 4, message),
    };
    let prepared = match prepare(
        &project.config,
        &project.plan,
        &callable,
        project.generator_rules.as_deref(),
        &project.package_metadata,
        &project.bindings,
        existing.as_deref(),
        None,
    ) {
        Ok(prepared) => prepared,
        Err(message) => return fail(format, 4, message),
    };
    let generation_required = !project
        .bindings
        .iter()
        .any(|binding| binding.cott_symbol == symbol);
    let current = match crate::transaction::InputSnapshot::capture(
        &project.paths.root,
        project.input_snapshot.files.keys().cloned(),
    ) {
        Ok(current) => current,
        Err(error) => return fail(format, 6, error.to_string()),
    };
    if current != project.input_snapshot {
        return fail(format, 6, "project changed while preparing Rust prompt");
    }
    match format {
        OutputFormat::Human => {
            if let Err(error) = std::io::stdout().write_all(&prepared.bytes) {
                eprintln!("error: write Rust prompt: {error}");
                return 6;
            }
        }
        OutputFormat::Json => {
            let prompt = String::from_utf8(prepared.bytes)
                .expect("rendered Rust generation prompt is UTF-8");
            let report = json!({
                "symbol": symbol,
                "intent_hash": prepared.intent_hash,
                "prompt_hash": prepared.prompt_hash,
                "generation_required": generation_required,
                "context": prepared.context,
                "prompt": prompt,
            });
            let mut bytes = match serde_json::to_vec(&report) {
                Ok(bytes) => bytes,
                Err(error) => {
                    eprintln!("error: serialize Rust prompt report: {error}");
                    return 1;
                }
            };
            bytes.push(b'\n');
            if let Err(error) = std::io::stdout().write_all(&bytes) {
                eprintln!("error: write Rust prompt report: {error}");
                return 6;
            }
        }
    }
    0
}

pub(crate) fn existing_agent_source(
    project: &Project,
    callable: &RustCallable,
) -> Result<Option<Vec<u8>>, String> {
    let Some(record) = &project.baseline else {
        return Ok(None);
    };
    let Some(implementation) = record
        .current
        .implementations
        .iter()
        .find(|implementation| {
            implementation.owner == RustOwner::Agent
                && implementation.cott_symbol == callable.symbol
        })
    else {
        return Ok(None);
    };
    let expected = candidate_binding(&project.paths, callable, Vec::new())?;
    let recorded_origin = normalized_path(&implementation.source_origin)?;
    let recorded_runtime = normalized_path(&implementation.runtime_origin)?;
    if recorded_origin != expected.source_origin
        || implementation.target_symbol != expected.target_symbol
        || recorded_runtime != expected.runtime_origin
    {
        return Err(format!(
            "{}: recorded Rust implementation ownership for `{}` is not canonical",
            implementation.source_origin, callable.symbol
        ));
    }
    let path = project.paths.root.join(&recorded_origin);
    let Some(bytes) = read_regular_source(&path, &callable.symbol)? else {
        return Ok(None);
    };
    let content_hash = format!("sha256:{}", sha256_hex(&bytes));
    let run_matches = record
        .current
        .agent_runs
        .iter()
        .any(|run| run.symbol == callable.symbol && run.implementation_hash == content_hash);
    if implementation.content_hash != content_hash || !run_matches {
        return Err(format!(
            "{}: durable Rust implementation `{}` does not match recorded content and agent run identity",
            path.display(),
            callable.symbol
        ));
    }
    Ok(Some(bytes))
}

fn read_regular_source(path: &Path, symbol: &str) -> Result<Option<Vec<u8>>, String> {
    let mut file = match OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_CLOEXEC | libc::O_NOFOLLOW | libc::O_NONBLOCK)
        .open(path)
    {
        Ok(file) => file,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(None),
        Err(error) => {
            return Err(format!(
                "open pending Rust implementation for `{symbol}` {}: {error}",
                path.display()
            ));
        }
    };
    let before = file.metadata().map_err(|error| {
        format!(
            "inspect pending Rust implementation for `{symbol}` {}: {error}",
            path.display()
        )
    })?;
    if !before.is_file() || before.nlink() != 1 {
        return Err(format!(
            "pending Rust implementation for `{symbol}` must be a regular non-symlink single-link file: {}",
            path.display()
        ));
    }
    let mut bytes = Vec::new();
    file.read_to_end(&mut bytes).map_err(|error| {
        format!(
            "read pending Rust implementation for `{symbol}` {}: {error}",
            path.display()
        )
    })?;
    let after = file.metadata().map_err(|error| {
        format!(
            "re-inspect pending Rust implementation for `{symbol}` {}: {error}",
            path.display()
        )
    })?;
    let leaf = fs::symlink_metadata(path).map_err(|error| {
        format!(
            "re-inspect pending Rust implementation leaf for `{symbol}` {}: {error}",
            path.display()
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
        return Err(format!(
            "pending Rust implementation for `{symbol}` changed or became unsafe while being read: {}",
            path.display()
        ));
    }
    Ok(Some(bytes))
}

fn collect_identities(value: &Value, identities: &mut BTreeSet<String>) {
    match value {
        Value::Array(values) => {
            for value in values {
                collect_identities(value, identities);
            }
        }
        Value::Object(values) => {
            for key in ["name", "symbol", "target", "trait_method"] {
                if let Some(identity) = values.get(key).and_then(Value::as_str) {
                    identities.insert(identity.to_owned());
                }
            }
            for value in values.values() {
                collect_identities(value, identities);
            }
        }
        Value::Null | Value::Bool(_) | Value::Number(_) | Value::String(_) => {}
    }
}

fn collect_intent_docs(value: &Value, output: &mut String) {
    match value {
        Value::Array(values) => {
            for value in values {
                collect_intent_docs(value, output);
            }
        }
        Value::Object(values) => {
            let name = values
                .get("name")
                .or_else(|| values.get("trait_method"))
                .and_then(Value::as_str);
            let doc = values
                .get("doc")
                .filter(|doc| !doc.is_null())
                .or_else(|| {
                    values
                        .get("contract")
                        .and_then(|contract| contract.get("doc"))
                })
                .or_else(|| {
                    values
                        .get("contracts")
                        .and_then(|contract| contract.get("doc"))
                })
                .and_then(|doc| match doc {
                    Value::String(text) => Some(text.as_str()),
                    Value::Object(doc) => doc.get("text").and_then(Value::as_str),
                    _ => None,
                });
            if let (Some(name), Some(doc)) = (name, doc.filter(|doc| !doc.is_empty())) {
                output.push_str(name);
                output.push_str(":\n");
                output.push_str(doc);
                output.push_str("\n\n");
            }
            for (key, value) in values {
                if key != "doc" {
                    collect_intent_docs(value, output);
                }
            }
        }
        Value::Null | Value::Bool(_) | Value::Number(_) | Value::String(_) => {}
    }
}

fn normalized_path(value: &str) -> Result<PathBuf, String> {
    let path = Path::new(value);
    if path.as_os_str().is_empty()
        || path.is_absolute()
        || path.to_str().is_none()
        || path
            .components()
            .any(|component| !matches!(component, Component::Normal(_)))
    {
        return Err(format!("unsafe recorded Rust path `{value}`"));
    }
    Ok(path.to_path_buf())
}

fn fail(format: OutputFormat, exit_code: i32, message: impl Into<String>) -> i32 {
    let message = message.into();
    match format {
        OutputFormat::Human => eprintln!("error: {message}"),
        OutputFormat::Json => {
            let diagnostic_code = match exit_code {
                2 => code::CLI_USAGE,
                3 => code::SYNTAX,
                4 => code::RUST,
                5 => code::AGENT,
                6 => code::FILESYSTEM,
                _ => code::INTERNAL,
            };
            let report = DiagnosticReport {
                diagnostics: vec![Diagnostic::error(diagnostic_code, message, Span::new(0, 0))],
            };
            match report.canonical_json(&SourceMap::default()) {
                Ok(bytes) => {
                    if let Err(error) = std::io::stdout().write_all(&bytes) {
                        eprintln!("error: write Rust prompt error: {error}");
                        return 6;
                    }
                }
                Err(error) => {
                    eprintln!("error: serialize Rust prompt error: {error}");
                    return 1;
                }
            }
        }
    }
    exit_code
}
