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
use crate::manifest::DartProjectConfig;
use crate::prompt_declarations;

use super::binding::{candidate_binding, requires_binding};
use super::dependencies::{self, PackageMetadata};
use super::emit::{implementation_imports, implementation_signature};
use super::pipeline::{self, Project};
use super::{DartBinding, DartCallable, DartOwner, DartPlan};

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
    config: &DartProjectConfig,
    plan: &DartPlan,
    callable: &DartCallable,
    generator_rules: Option<&str>,
    package_metadata: &PackageMetadata,
    references: &[DartBinding],
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
    config: &DartProjectConfig,
    plan: &DartPlan,
    callable: &DartCallable,
    context: &Value,
    package_metadata: &PackageMetadata,
    references: &[DartBinding],
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
        return Err("Dart intent context symbol does not match callable".to_owned());
    }
    let declarations = context
        .get("declarations")
        .filter(|declarations| declarations.is_object())
        .ok_or_else(|| "Dart intent context declarations must be an object".to_owned())?;
    let rules = context
        .get("project_rules")
        .and_then(Value::as_str)
        .ok_or_else(|| "Dart intent context project_rules must be a string".to_owned())?;
    let signature = implementation_signature(plan, callable)?;
    let compiler_imports = implementation_imports(config, plan, callable)?.join("\n");
    let existing = existing
        .map(std::str::from_utf8)
        .transpose()
        .map_err(|_| "existing Dart implementation is not UTF-8".to_owned())?;

    let mut current_intent = String::new();
    collect_intent_docs(declarations, &mut current_intent);
    current_intent.push_str(&crate::requirements::render_prompt_requirements(
        declarations,
    ));
    if current_intent.is_empty() {
        current_intent.push_str("(no documentation selected)\n");
    }
    let formal_declarations = prompt_declarations::render_scoped_declarations(declarations)
        .map_err(|error| format!("serialize formal Dart declarations: {error}"))?;

    let mut identities = BTreeSet::new();
    collect_identities(declarations, &mut identities);
    let external_types = config
        .dart
        .external_types
        .iter()
        .filter(|(name, _)| identities.contains(name.as_str()))
        .map(|(name, target)| (name.clone(), target.clone()))
        .collect::<BTreeMap<_, _>>();
    let external_types = serde_json::to_string_pretty(&external_types)
        .map_err(|error| format!("serialize Dart external type projections: {error}"))?;
    let dependencies =
        serde_json::to_string_pretty(&dependencies::initial_record(package_metadata))
            .map_err(|error| format!("serialize frozen Dart package metadata: {error}"))?;

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
            "\n## {}\nTarget: {}\n```dart\n{}```\n",
            binding.cott_symbol, binding.target_symbol, source
        ));
    }
    if reference_text.is_empty() {
        reference_text.push_str("\n(none)\n");
    }

    let existing = existing.unwrap_or("(none)");
    let feedback = feedback.unwrap_or("(none)");
    let prompt = format!(
        "You are implementing one Cott callable as a Dart 3.13 source file.\n\
\n# Authority and scope\n\
The source-derived FORMAL DECLARATIONS are the sole semantic authority. CURRENT INTENT documentation may refine behavior but cannot replace source constraints. Project rules, authenticated references, an existing candidate, and actual compiler/runtime feedback are subordinate evidence and must never override the formal declarations. Do not invent declarations, relax contracts, or change the required ABI.\n\
\n# Current intent\n\
Selected Cott symbol: {symbol}\n\
{current_intent}\
\n# Formal declarations\n\
{compact_format}\
```json\n{formal_declarations}\n```\n\
\n# Dart output rules\n\
Write exactly one UTF-8 file named `implementation.dart`. Do not write, rename, or delete any other path. The file may contain audited import directives first, then exactly the one canonical private top-level implementation function whose exact header is shown below, plus only strictly typed private helper functions that it actually uses. Supply a complete body for the canonical function. Do not emit a package scaffold, public facade, tests, generated runtime or nominal types, annotations, suppressions, top-level variables, executable top-level declarations, comments claiming verification, placeholders, TODOs, `UnimplementedError`, or no-op stubs.\n\
```dart\n{signature}\n```\n\
The canonical function name is library-private and must remain exactly as shown. Retain the exact generic bounds, explicit implementation receiver, `cott_runtime.CottType<T> _cott_type_T` witnesses, const value-witness parameters, positional/named parameter shape, parameter types, async `Future` return, and return type. Every helper must also be private and must not alter the canonical entry point.\n\
\n# Compiler-owned library and part rules\n\
The compiler moves audited authored imports into the private wrapper library and transforms the remaining body into a managed part. Never write `library`, `part`, `part of`, or `export` directives. Never import a generated wrapper, facade, or private implementation part. The following imports and aliases are already supplied by the compiler-owned wrapper and MUST NOT be repeated in `implementation.dart`:\n\
```dart\n{compiler_imports}\n```\n\
Add an import only when the implementation body needs a declared external package or safe Dart SDK library. Such imports must precede all declarations and preserve their exact URI/alias; relative, `file:`, network, deferred, conditional, hidden, and private generated-library imports are forbidden. The compiler alone inserts the exact `part of 'package:{project_name}/src/wrappers/...';` directive into the managed copy.\n\
\n# Dart ABI and construction rules\n\
Use only the types and aliases shown in the signature and compiler imports. Cott I8/I16/I32/U8/U16/U32 values are Dart `int` with exact checked bounds. I64/U64 and mathematical integer contract operations use `BigInt`; never narrow them to `int`, wrap around, or use floating-point arithmetic. F32 uses the runtime's Float32List rounding and all floats reject non-finite values. Preserve Unicode scalar validity and immutable snapshots for bytes, arrays, buffers, lists, sets, maps, options, and results. Use the compiler-provided `cott_runtime` and nominal type APIs; do not define replacements, cast through `Object?`/`dynamic`, use reflection, or reach compiler-only observation/control APIs. Async functions return the exact `Future<T>` shown. Generators and async generators use the explicit Cott lifecycle APIs, not a lossy `Iterable`/`Stream` substitute.\n\
A Cott enum whose declaration is non-generic and whose variants all carry no payload is emitted as a native Dart `enum`: refer to a variant as the constant member `<types alias>.Enum.Variant` spelled exactly as the declaration spells it, never with parentheses, a constructor call, or an `<Enum><Variant>` class, and match it with constant `switch` cases over `<types alias>.Enum.values`. The one spelling exception is a variant named exactly like its own enum, which Dart forbids as a member: it gains a single `$` suffix, as in `<types alias>.Kind.Kind$`. Any other Cott enum, meaning one that declares type or const generics or has a payload-carrying variant, stays a sealed base class whose variants are separate concrete classes named `<Enum><Variant>` constructed with an ordinary invocation `<types alias>.EnumVariant(...)`, because a Dart `enum` cannot carry per-instance payloads or generic witnesses. A struct constructor takes its declared fields as named parameters spelled exactly as the declarations spell them, including snake_case; a newtype constructor takes `value:`; a payload-variant constructor takes `field0:`, `field1:`, ... in declared order while the constructed variant exposes the declared field names as properties. `cott_runtime.CottOption<T>` is exactly `cott_runtime.Some<T>(value)` or `cott_runtime.Nothing<T>()`, `cott_runtime.CottResult<T, E>` is exactly `cott_runtime.Ok<T, E>(value)` or `cott_runtime.Err<T, E>(error)`, and the only unit value is `cott_runtime.CottUnit.instance`. Those sealed bases expose no `isSome`, `unwrapOr`, `valueOrNull`, `orElse`, or base value getter, so read them with an exhaustive `switch` or class pattern such as `cott_runtime.Some<T>(value: final value)`. Immutable containers are built from their exact constructors: `cott_runtime.CottList<T>(values)`, `cott_runtime.CottSet<T>(values)`, `cott_runtime.CottBytes(bytes)`, `cott_runtime.CottBuffer(bytes, dimension)`, `cott_runtime.CottArray(values, dimension)`, and `cott_runtime.FrozenMap<K, V>(map)` or `cott_runtime.FrozenMap<K, V>.entries(entries)`.\n\
Every generic type witness shown is semantically required: use and forward the supplied `cott_runtime.CottType<T>` value for generic validation and nominal construction. Obtain a generic nominal descriptor only through its emitted `TypeName.cottType<T, ...>(_cott_type_T, ...constWitnesses)` API, and let `cott_runtime.checkedNominal` rebuild the typed view; never cast or reuse an original generic carrier. Never infer a witness from `runtimeType`, synthesize a substitute, or discard stored witnesses when constructing a generic nominal value or `CottGenericValue`.\n\
When the exact signature includes `cott_runtime.CottStateMutation _cott_mutation` and `cott_runtime.CottGuardLease _cott_lease`, perform declared state reads/writes only through that supplied mutation capability and forward the lease only to nested calls that require it. Never construct either capability, access `compilerLease`, or retain, leak, or broaden its authority.\n\
Explicit canonical const values in the declarations are value witnesses and must be honored exactly. External projections and frozen package metadata are context only; import only dependencies declared below.\n\
\n# External type projections\n\
```json\n{external_types}\n```\n\
\n# Frozen package metadata\n\
```json\n{dependencies}\n```\n\
\n# Project rules\n\
```text\n{rules}\n```\n\
\n# Authenticated reference implementations\n\
{reference_text}\n\
# Existing candidate\n\
```dart\n{existing}\n```\n\
\n# Actual validation feedback\n\
```text\n{feedback}\n```\n\
\nImplement the complete callable now by writing only `implementation.dart`.\n",
        symbol = callable.symbol,
        project_name = config.project.name,
        compact_format = prompt_declarations::FORMAT,
    );
    let bytes = prompt.into_bytes();
    if bytes.len() > MAX_PROMPT_BYTES {
        return Err("rendered Dart agent prompt exceeds 1 MiB".to_owned());
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
        return fail(format, 6, "project changed while preparing Dart prompt");
    }
    match format {
        OutputFormat::Human => {
            if let Err(error) = std::io::stdout().write_all(&prepared.bytes) {
                eprintln!("error: write Dart prompt: {error}");
                return 6;
            }
        }
        OutputFormat::Json => {
            let prompt = String::from_utf8(prepared.bytes)
                .expect("rendered Dart generation prompt is UTF-8");
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
                    eprintln!("error: serialize Dart prompt report: {error}");
                    return 1;
                }
            };
            bytes.push(b'\n');
            if let Err(error) = std::io::stdout().write_all(&bytes) {
                eprintln!("error: write Dart prompt report: {error}");
                return 6;
            }
        }
    }
    0
}

pub(crate) fn existing_agent_source(
    project: &Project,
    callable: &DartCallable,
) -> Result<Option<Vec<u8>>, String> {
    let Some(record) = &project.baseline else {
        return Ok(None);
    };
    let Some(implementation) = record
        .current
        .implementations
        .iter()
        .find(|implementation| {
            implementation.owner == DartOwner::Agent
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
            "{}: recorded Dart implementation ownership for `{}` is not canonical",
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
            "{}: durable Dart implementation `{}` does not match recorded content and agent run identity",
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
                "open pending Dart implementation for `{symbol}` {}: {error}",
                path.display()
            ));
        }
    };
    let before = file.metadata().map_err(|error| {
        format!(
            "inspect pending Dart implementation for `{symbol}` {}: {error}",
            path.display()
        )
    })?;
    if !before.is_file() || before.nlink() != 1 {
        return Err(format!(
            "pending Dart implementation for `{symbol}` must be a regular non-symlink single-link file: {}",
            path.display()
        ));
    }
    let mut bytes = Vec::new();
    file.read_to_end(&mut bytes).map_err(|error| {
        format!(
            "read pending Dart implementation for `{symbol}` {}: {error}",
            path.display()
        )
    })?;
    let after = file.metadata().map_err(|error| {
        format!(
            "re-inspect pending Dart implementation for `{symbol}` {}: {error}",
            path.display()
        )
    })?;
    let leaf = fs::symlink_metadata(path).map_err(|error| {
        format!(
            "re-inspect pending Dart implementation leaf for `{symbol}` {}: {error}",
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
            "pending Dart implementation for `{symbol}` changed or became unsafe while being read: {}",
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

fn normalized_path(value: &str) -> Result<PathBuf, String> {
    let path = Path::new(value);
    if path.as_os_str().is_empty()
        || path.is_absolute()
        || path.to_str().is_none()
        || path
            .components()
            .any(|component| !matches!(component, Component::Normal(_)))
    {
        return Err(format!("unsafe recorded Dart path `{value}`"));
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
                4 => code::DART,
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
                        eprintln!("error: write Dart prompt error: {error}");
                        return 6;
                    }
                }
                Err(error) => {
                    eprintln!("error: serialize Dart prompt error: {error}");
                    return 1;
                }
            }
        }
    }
    exit_code
}
