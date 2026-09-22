use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::io::Write as _;
use std::path::{Path, PathBuf};

use serde_json::{Value, json};

use crate::cli::OutputFormat;
use crate::diagnostics::{Diagnostic, DiagnosticReport, SourceMap, Span, code};
use crate::hash::sha256_hex;
use crate::intent;
use crate::manifest::KotlinProjectConfig;
use crate::prompt_declarations;

use super::binding::{agent_source_origin, requires_binding};
use super::emit::implementation_signature;
use super::pipeline::{self, Project};
use super::{KotlinBinding, KotlinCallable, KotlinOwner, KotlinPlan};
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
    config: &KotlinProjectConfig,
    plan: &KotlinPlan,
    callable: &KotlinCallable,
    generator_rules: Option<&str>,
    references: &[KotlinBinding],
    existing: Option<&[u8]>,
    feedback: Option<&str>,
) -> Result<PreparedPrompt, String> {
    let context = intent::context(
        &plan.contract_surface(),
        &callable.symbol,
        generator_rules.unwrap_or_default().as_bytes(),
    )?;
    let intent_hash = intent::fingerprint_context(&context)?;
    let bytes = render_generation_prompt(
        config, plan, callable, &context, references, existing, feedback,
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
    config: &KotlinProjectConfig,
    plan: &KotlinPlan,
    callable: &KotlinCallable,
    context: &Value,
    references: &[KotlinBinding],
    existing: Option<&[u8]>,
    feedback: Option<&str>,
) -> Result<Vec<u8>, String> {
    if !requires_binding(callable) {
        return Err(format!(
            "compiler-owned implementation method `{}` must not be sent to an agent",
            callable.symbol
        ));
    }
    let signature = implementation_signature(plan, callable)?;
    let package = implementation_package(callable)?;
    if context.get("symbol").and_then(Value::as_str) != Some(callable.symbol.as_str()) {
        return Err("Kotlin intent context symbol does not match callable".to_owned());
    }
    let declarations = context
        .get("declarations")
        .filter(|declarations| declarations.is_object())
        .ok_or_else(|| "Kotlin intent context declarations must be an object".to_owned())?;
    let rules = context
        .get("project_rules")
        .and_then(Value::as_str)
        .ok_or_else(|| "Kotlin intent context project_rules must be a string".to_owned())?;
    let existing = existing
        .map(std::str::from_utf8)
        .transpose()
        .map_err(|_| "existing Kotlin implementation is not UTF-8".to_owned())?;
    let mut current_intent = String::new();
    collect_intent_docs(declarations, &mut current_intent);
    if current_intent.is_empty() {
        current_intent.push_str("(no documentation selected)\n");
    }
    let formal_declarations = prompt_declarations::render_scoped_declarations(declarations)
        .map_err(|error| format!("serialize formal Kotlin declarations: {error}"))?;
    let mut identities = BTreeSet::new();
    collect_identities(declarations, &mut identities);
    let external_types = config
        .kotlin
        .external_types
        .iter()
        .filter(|(name, _)| identities.contains(name.as_str()))
        .map(|(name, target)| (name.clone(), target.clone()))
        .collect::<BTreeMap<_, _>>();
    let external_types = serde_json::to_string_pretty(&external_types)
        .map_err(|error| format!("serialize Kotlin external type projections: {error}"))?;
    let dependencies = serde_json::to_string_pretty(&json!({
        "classpath": config.kotlin.classpath,
        "compile_only": config.kotlin.compile_only,
        "jvm_target": config.kotlin.jvm_target,
    }))
    .map_err(|error| format!("serialize Kotlin dependency context: {error}"))?;

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
            "\n## {}\nTarget: {}\n```kotlin\n{}```\n",
            binding.cott_symbol, binding.target_symbol, source
        ));
    }
    if reference_text.is_empty() {
        reference_text.push_str("\n(none)\n");
    }

    let existing = existing.unwrap_or("(none)");
    let feedback = feedback.unwrap_or("(none)");
    let prompt = format!(
        "You are implementing one Cott callable as a Kotlin/JVM 17 source file.\n\
\n# Authority and scope\n\
The source-derived FORMAL DECLARATIONS are the sole semantic authority. CURRENT INTENT documentation may refine behavior but cannot replace source constraints. Project rules, reference implementations, an existing candidate, and feedback are subordinate evidence and must never override the formal declarations. Do not invent declarations, relax contracts, or change the required ABI.\n\
\n# Current intent\n\
Selected Cott symbol: {symbol}\n\
{current_intent}\
\n# Formal declarations\n\
{compact_format}\
```json\n{formal_declarations}\n```\n\
\n# Kotlin output rules\n\
Write exactly one UTF-8 file named `implementation.kt`. Do not write, rename, or delete any other path. The file must contain exactly package `{package}`, the one canonical top-level implementation function with the signature below, and only strictly typed private helper functions used by it. Do not emit a public facade, tests, build files, generated runtime code, comments claiming verification, placeholders, TODOs, `NotImplementedError`-style throws, or no-op stubs.\n\
```kotlin\npackage {package}\n\n{signature}\n```\n\
The canonical function must remain `internal`, must remain `suspend` exactly when shown, and must retain the exact name, generic bounds, associated-type parameters, const value-witness parameters, parameter types, and return type. A method helper's explicit `self` parameter is required.\n\
\n# Kotlin ABI and construction rules\n\
Use the fully qualified types in the signature. Cott integers use the exact Kotlin primitive or `java.math.BigInteger` type shown; do not narrow, wrap around, or use floating-point arithmetic for integer contracts. `cott_runtime.CottConst` witnesses carry exact mathematical values through `.value`; every `_cott_const_*` parameter shown is semantically required. Associated Cott types are the bounded Kotlin type parameters shown in the signature, not reflection, casts, `Any?`, or a phantom wrapper.\n\
Construct canonical values with the current runtime/public API: `cott_runtime.CottUnit`, `cott_runtime.Some(value)` / `cott_runtime.Nothing`, `cott_runtime.Ok(value)` / `cott_runtime.Err(error)`, immutable `cott_runtime.CottList`, `cott_runtime.CottSet`, `cott_runtime.FrozenMap`, `cott_runtime.CottArray`, `cott_runtime.CottBuffer`, and the nominal public constructors/factories present in the declarations. Preserve immutable snapshots and exact nominal identities. Do not define replacement runtime types or import private generated implementation packages.\n\
Explicit canonical const values in the declarations are value witnesses and must be honored exactly. External projections and compile dependencies are context only; use only mappings actually declared below.\n\
\n# External type projections\n\
```json\n{external_types}\n```\n\
\n# Dependency context\n\
```json\n{dependencies}\n```\n\
\n# Project rules\n\
```text\n{rules}\n```\n\
\n# Authenticated reference implementations\n\
{reference_text}\n\
# Existing candidate\n\
```kotlin\n{existing}\n```\n\
\n# Actual validation feedback\n\
```text\n{feedback}\n```\n\
\nImplement the complete callable now by writing only `implementation.kt`.\n",
        symbol = callable.symbol,
        compact_format = prompt_declarations::FORMAT,
    );
    let bytes = prompt.into_bytes();
    if bytes.len() > MAX_PROMPT_BYTES {
        return Err("rendered Kotlin agent prompt exceeds 1 MiB".to_owned());
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
        .into_iter()
        .find(|callable| callable.symbol == symbol)
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
    let rules = project.generator_rules.as_deref();
    let existing = match existing_agent_source(&project, &callable) {
        Ok(existing) => existing,
        Err(message) => return fail(format, 4, message),
    };
    let prepared = match prepare(
        &project.config,
        &project.plan,
        &callable,
        rules,
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
        return fail(format, 6, "project changed while preparing Kotlin prompt");
    }
    match format {
        OutputFormat::Human => {
            if let Err(error) = std::io::stdout().write_all(&prepared.bytes) {
                eprintln!("error: write Kotlin prompt: {error}");
                return 6;
            }
        }
        OutputFormat::Json => {
            let prompt = String::from_utf8(prepared.bytes)
                .expect("rendered Kotlin generation prompt is UTF-8");
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
                    eprintln!("error: serialize Kotlin prompt report: {error}");
                    return 1;
                }
            };
            bytes.push(b'\n');
            if let Err(error) = std::io::stdout().write_all(&bytes) {
                eprintln!("error: write Kotlin prompt report: {error}");
                return 6;
            }
        }
    }
    0
}

pub(crate) fn existing_agent_source(
    project: &Project,
    callable: &KotlinCallable,
) -> Result<Option<Vec<u8>>, String> {
    let Some(record) = &project.baseline else {
        return Ok(None);
    };
    let Some(implementation) = record
        .current
        .implementations
        .iter()
        .find(|implementation| {
            implementation.owner == KotlinOwner::Agent
                && implementation.cott_symbol == callable.symbol
        })
    else {
        return Ok(None);
    };
    let expected_origin = agent_source_origin(&project.paths, callable)?;
    let recorded_origin = normalized_path(&implementation.source_origin)?;
    if recorded_origin != expected_origin {
        return Err(format!(
            "{}: recorded Kotlin implementation path for `{}` is not its canonical agent path",
            implementation.source_origin, callable.symbol
        ));
    }
    let path = project.paths.root.join(&recorded_origin);
    let bytes = match fs::read(&path) {
        Ok(bytes) => bytes,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(None),
        Err(error) => {
            return Err(format!(
                "read pending Kotlin implementation {}: {error}",
                path.display()
            ));
        }
    };
    let content_hash = format!("sha256:{}", sha256_hex(&bytes));
    let run_matches = record
        .current
        .agent_runs
        .iter()
        .any(|run| run.symbol == callable.symbol && run.implementation_hash == content_hash);
    if implementation.content_hash != content_hash || !run_matches {
        return Err(format!(
            "{}: durable Kotlin implementation `{}` does not match recorded content and agent run identity",
            path.display(),
            callable.symbol
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
            let doc = values.get("doc").and_then(|doc| match doc {
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

fn implementation_package(callable: &KotlinCallable) -> Result<String, String> {
    let mut package = format!("cott_impl.{}", callable.module);
    if let Some(owner) = &callable.owner {
        let concrete = owner
            .get("name")
            .and_then(Value::as_str)
            .and_then(|name| name.rsplit('.').next())
            .filter(|name| !name.is_empty())
            .ok_or_else(|| {
                format!(
                    "Kotlin callable `{}` has a malformed implementation owner",
                    callable.symbol
                )
            })?;
        package.push('.');
        package.push_str(concrete);
    }
    Ok(package)
}

fn normalized_path(value: &str) -> Result<PathBuf, String> {
    let path = Path::new(value);
    if path.as_os_str().is_empty()
        || path.is_absolute()
        || path.to_str().is_none()
        || path
            .components()
            .any(|component| !matches!(component, std::path::Component::Normal(_)))
    {
        return Err(format!("unsafe Kotlin implementation path `{value}`"));
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
                4 => code::KOTLIN,
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
                        eprintln!("error: write Kotlin prompt error: {error}");
                        return 6;
                    }
                }
                Err(error) => {
                    eprintln!("error: serialize Kotlin prompt error: {error}");
                    return 1;
                }
            }
        }
    }
    exit_code
}
