use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, OpenOptions};
use std::io::{Read, Seek, SeekFrom, Write};
use std::os::unix::fs::MetadataExt;
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant};

use crate::diagnostics::{Diagnostic, Span, code};
use crate::hash::sha256_hex;
use crate::python::artifact_plan::{PythonCallable, PythonCallableKind};
use crate::sandbox::{BindMounts, NetworkAccess, ResourceLimits, SandboxSpec, run};
use crate::version::{is_at_least, parse_version};

const MAX_RULE_BYTES: usize = 1024 * 1024;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum AgentKind {
    Codex,
    Omp,
    Claude,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AdapterSpec {
    pub executable_name: &'static str,
    pub minimum_version: &'static str,
    pub version_argv: &'static [&'static str],
    pub argv_template: &'static [&'static str],
    pub prompt_on_stdin: bool,
}

pub const CODEX: AdapterSpec = AdapterSpec {
    executable_name: "codex",
    minimum_version: "0.147.0",
    version_argv: &["--version"],
    argv_template: &[
        "exec",
        "--strict-config",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--sandbox",
        "workspace-write",
        "--color",
        "never",
        "--cd",
        "<workspace>",
        "-",
    ],
    prompt_on_stdin: true,
};
pub const OMP: AdapterSpec = AdapterSpec {
    executable_name: "omp",
    minimum_version: "17.2.12",
    version_argv: &["--version"],
    argv_template: &[
        "-p",
        "--cwd",
        "<workspace>",
        "--no-session",
        "--no-rules",
        "--no-skills",
        "--no-extensions",
        "--no-lsp",
        "--no-pty",
        "--no-title",
        "--tools",
        "read,grep,glob,edit,write",
        "--approval-mode",
        "yolo",
        "--max-time",
        "<seconds>s",
        "--config",
        "<overlay>",
        "@<prompt-file>",
    ],
    prompt_on_stdin: false,
};

pub const CLAUDE: AdapterSpec = AdapterSpec {
    executable_name: "claude",
    minimum_version: "2.1.89",
    version_argv: &["--version"],
    argv_template: &[
        "--bare",
        "--print",
        "--input-format",
        "text",
        "--output-format",
        "json",
        "--permission-mode",
        "dontAsk",
        "--tools",
        "Read,Write",
        "--allowedTools",
        "Read,Write",
        "--disallowedTools",
        "Bash,Edit,Glob,Grep,WebFetch,WebSearch,Task,mcp__*",
        "--no-session-persistence",
    ],
    prompt_on_stdin: true,
};

pub fn adapter(kind: AgentKind) -> &'static AdapterSpec {
    match kind {
        AgentKind::Codex => &CODEX,
        AgentKind::Omp => &OMP,
        AgentKind::Claude => &CLAUDE,
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AgentRunCandidate {
    pub implementation: Vec<u8>,
    pub executable: PathBuf,
    pub executable_hash: String,
    pub adapter_version: String,
    pub prompt_hash: String,
    pub stdout: Vec<u8>,
    pub stderr: Vec<u8>,
    pub exit_code: Option<i32>,
    pub timed_out: bool,
    pub duration_ms: u64,
    pub environment_names: Vec<String>,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum ShadowFacet {
    Return,
    Limit,
    Error,
    Atomicity,
    Cleanup,
}

impl ShadowFacet {
    pub const ALL: [Self; 5] = [
        Self::Return,
        Self::Limit,
        Self::Error,
        Self::Atomicity,
        Self::Cleanup,
    ];

    pub const fn as_str(self) -> &'static str {
        match self {
            Self::Return => "return",
            Self::Limit => "limit",
            Self::Error => "error",
            Self::Atomicity => "atomicity",
            Self::Cleanup => "cleanup",
        }
    }

    fn parse(value: &str) -> Option<Self> {
        Some(match value {
            "return" => Self::Return,
            "limit" => Self::Limit,
            "error" => Self::Error,
            "atomicity" => Self::Atomicity,
            "cleanup" => Self::Cleanup,
            _ => return None,
        })
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DomainRule {
    pub symbol: String,
    pub facet: ShadowFacet,
    pub payload: String,
    pub payload_span: Span,
    pub source_order: usize,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DomainRuleParse {
    pub path: PathBuf,
    pub rules: Vec<DomainRule>,
    pub diagnostics: Vec<Diagnostic>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DocCandidate {
    pub facet: ShadowFacet,
    pub span: Span,
    pub source_order: usize,
}

pub fn parse_domain_rules(path: &Path, bytes: &[u8]) -> DomainRuleParse {
    if bytes.len() > MAX_RULE_BYTES {
        return DomainRuleParse {
            path: path.to_path_buf(),
            rules: Vec::new(),
            diagnostics: vec![malformed_domain_rule(
                "generator rules exceed 1 MiB",
                Span::new(0, bytes.len()),
            )],
        };
    }

    let mut rules = Vec::new();
    let mut diagnostics = Vec::new();
    let mut seen = BTreeSet::new();
    let mut offset = 0;

    for raw_line in bytes.split_inclusive(|byte| *byte == b'\n') {
        let line = if raw_line.last() == Some(&b'\n') {
            &raw_line[..raw_line.len() - 1]
        } else {
            raw_line
        };
        if line.starts_with(b"cott-domain ") {
            let line_span = Span::new(offset, offset + line.len());
            if line.contains(&b'\r') {
                diagnostics.push(malformed_domain_rule(
                    "cott-domain directives must use LF line endings",
                    line_span,
                ));
            } else if let Err(error) = std::str::from_utf8(line) {
                diagnostics.push(malformed_domain_rule(
                    "cott-domain directives must be valid UTF-8",
                    Span::new(offset + error.valid_up_to(), offset + line.len()),
                ));
            } else if let Some(rule) = parse_domain_rule_line(line, offset, &mut diagnostics) {
                if !seen.insert((rule.symbol.clone(), rule.facet)) {
                    diagnostics.push(malformed_domain_rule(
                        format!(
                            "duplicate cott-domain directive for `{}` {}",
                            rule.symbol,
                            rule.facet.as_str()
                        ),
                        line_span,
                    ));
                } else {
                    rules.push(rule);
                }
            }
        }
        offset += raw_line.len();
    }

    DomainRuleParse {
        path: path.to_path_buf(),
        rules,
        diagnostics,
    }
}

pub fn scan_doc_candidates(text: &str) -> Vec<DocCandidate> {
    let bytes = text.as_bytes();
    let mut candidates = Vec::new();
    let mut start = 0;
    for (index, byte) in bytes.iter().enumerate() {
        if matches!(byte, b'.' | b'!' | b'?' | b'\n') {
            scan_doc_sentence(
                &text[start..index + usize::from(*byte != b'\n')],
                start,
                &mut candidates,
            );
            start = index + 1;
        }
    }
    if start < bytes.len() {
        scan_doc_sentence(&text[start..], start, &mut candidates);
    }
    candidates
}

pub fn has_normative_modal(sentence: &str) -> bool {
    ["must", "shall", "required to", "must not"]
        .into_iter()
        .any(|modal| has_ascii_phrase(sentence.as_bytes(), modal.as_bytes()))
}

pub fn sentence_has_facet(sentence: &str, facet: ShadowFacet) -> bool {
    facet_anchors(facet)
        .iter()
        .any(|anchor| has_ascii_phrase(sentence.as_bytes(), anchor.as_bytes()))
}

fn parse_domain_rule_line(
    line: &[u8],
    offset: usize,
    diagnostics: &mut Vec<Diagnostic>,
) -> Option<DomainRule> {
    const PREFIX: &[u8] = b"cott-domain ";
    let mut cursor = PREFIX.len();
    let symbol_start = cursor;
    cursor = next_ascii_whitespace(line, cursor);
    if cursor == symbol_start {
        diagnostics.push(malformed_domain_rule(
            "cott-domain directive requires a fully qualified callable symbol",
            Span::new(offset, offset + line.len()),
        ));
        return None;
    }
    let symbol = std::str::from_utf8(&line[symbol_start..cursor]).expect("validated directive");
    if !canonical_callable_symbol(symbol) {
        diagnostics.push(malformed_domain_rule(
            "cott-domain directive symbol must be a fully qualified callable",
            Span::new(offset + symbol_start, offset + cursor),
        ));
        return None;
    }

    let separator_start = cursor;
    cursor = skip_ascii_whitespace(line, cursor);
    if cursor == separator_start {
        diagnostics.push(malformed_domain_rule(
            "cott-domain directive requires a facet",
            Span::new(offset, offset + line.len()),
        ));
        return None;
    }
    let facet_start = cursor;
    cursor = next_ascii_whitespace_or_colon(line, cursor);
    if cursor == facet_start || line.get(cursor) != Some(&b':') {
        diagnostics.push(malformed_domain_rule(
            "cott-domain directive facet must be followed immediately by `:`",
            Span::new(offset + facet_start, offset + cursor),
        ));
        return None;
    }
    let facet_name = std::str::from_utf8(&line[facet_start..cursor]).expect("validated directive");
    let Some(facet) = ShadowFacet::parse(facet_name) else {
        diagnostics.push(malformed_domain_rule(
            "cott-domain directive has an unknown facet",
            Span::new(offset + facet_start, offset + cursor),
        ));
        return None;
    };

    cursor += 1;
    let payload_start = skip_ascii_whitespace(line, cursor);
    if payload_start == cursor || payload_start == line.len() {
        diagnostics.push(malformed_domain_rule(
            "cott-domain directive requires nonempty text after `:`",
            Span::new(offset + cursor.saturating_sub(1), offset + line.len()),
        ));
        return None;
    }
    let payload = std::str::from_utf8(&line[payload_start..]).expect("validated directive");
    if payload.bytes().all(|byte| byte.is_ascii_whitespace()) {
        diagnostics.push(malformed_domain_rule(
            "cott-domain directive requires nonempty text after `:`",
            Span::new(offset + payload_start, offset + line.len()),
        ));
        return None;
    }

    Some(DomainRule {
        symbol: symbol.to_owned(),
        facet,
        payload: payload.to_owned(),
        payload_span: Span::new(offset + payload_start, offset + line.len()),
        source_order: offset,
    })
}

fn malformed_domain_rule(message: impl Into<String>, span: Span) -> Diagnostic {
    let mut diagnostic = Diagnostic::error(code::CONTRACT, message, span.clone());
    diagnostic.source_order = span.start;
    diagnostic
}

fn canonical_callable_symbol(symbol: &str) -> bool {
    symbol.split('.').count() >= 2
        && symbol.split('.').all(|segment| {
            let mut characters = segment.bytes();
            characters
                .next()
                .is_some_and(|byte| byte == b'_' || byte.is_ascii_alphabetic())
                && characters.all(|byte| byte == b'_' || byte.is_ascii_alphanumeric())
        })
}

fn skip_ascii_whitespace(bytes: &[u8], mut cursor: usize) -> usize {
    while bytes.get(cursor).is_some_and(u8::is_ascii_whitespace) {
        cursor += 1;
    }
    cursor
}

fn next_ascii_whitespace(bytes: &[u8], mut cursor: usize) -> usize {
    while bytes
        .get(cursor)
        .is_some_and(|byte| !byte.is_ascii_whitespace())
    {
        cursor += 1;
    }
    cursor
}

fn next_ascii_whitespace_or_colon(bytes: &[u8], mut cursor: usize) -> usize {
    while bytes
        .get(cursor)
        .is_some_and(|byte| !byte.is_ascii_whitespace() && *byte != b':')
    {
        cursor += 1;
    }
    cursor
}

fn scan_doc_sentence(sentence: &str, start: usize, candidates: &mut Vec<DocCandidate>) {
    if !has_normative_modal(sentence) {
        return;
    }
    for facet in ShadowFacet::ALL {
        if sentence_has_facet(sentence, facet) {
            candidates.push(DocCandidate {
                facet,
                span: Span::new(start, start + sentence.len()),
                source_order: start,
            });
        }
    }
}

fn facet_anchors(facet: ShadowFacet) -> &'static [&'static str] {
    match facet {
        ShadowFacet::Return => &["return", "returns", "result", "same as"],
        ShadowFacet::Limit => &[
            "limit",
            "maximum",
            "minimum",
            "at most",
            "at least",
            "less than",
            "greater than",
            "bytes",
            "timeout",
        ],
        ShadowFacet::Error => &["error", "fail", "fails", "reject"],
        ShadowFacet::Atomicity => &["atomic", "atomically", "all-or-nothing"],
        ShadowFacet::Cleanup => &[
            "cleanup",
            "clean up",
            "remove temporary",
            "delete temporary",
            "leave no",
        ],
    }
}

fn has_ascii_phrase(haystack: &[u8], needle: &[u8]) -> bool {
    haystack
        .windows(needle.len())
        .enumerate()
        .any(|(start, candidate)| {
            candidate.eq_ignore_ascii_case(needle)
                && !haystack
                    .get(start.wrapping_sub(1))
                    .is_some_and(|byte| ascii_word(*byte))
                && !haystack
                    .get(start + needle.len())
                    .is_some_and(|byte| ascii_word(*byte))
        })
}

const fn ascii_word(byte: u8) -> bool {
    byte.is_ascii_alphanumeric() || byte == b'_'
}

pub fn render_prompt(
    callable: &PythonCallable,
    selected_ir: &[u8],
    docs: &str,
    type_declarations: &str,
    external_types: &BTreeMap<String, String>,
    bound_symbols: &str,
    existing: Option<&[u8]>,
    rules: Option<&[u8]>,
    write_path: &Path,
) -> Result<Vec<u8>, String> {
    if let Some(kind) = selected_implementation_kind(callable) {
        return Err(format!(
            "compiler-owned {kind} implementation method `{}` must not be sent to an agent",
            callable.cott_symbol
        ));
    }
    if rules.is_some_and(|rules| rules.len() > MAX_RULE_BYTES) || selected_ir.len() > MAX_RULE_BYTES
    {
        return Err("agent prompt input exceeds 1 MiB".to_owned());
    }
    let ownership = match &callable.kind {
        PythonCallableKind::Function => format!(
            "Define exactly one canonical top-level function `{}`. You MAY additionally define private implementation helpers, private immutable constants, and invariant TypeVars. Each helper MUST be an undecorated, synchronous, fully annotated top-level function whose name starts with a single `_` but is neither dunder nor reserved `_cott_`; function names MUST be unique. Each constant MUST have a single-leading-underscore name that is neither dunder nor reserved `_cott_`, and be a literal `Final[bool|int|float|str|bytes]` value. Do not define classes, public helpers, mutable globals, decorators, async functions, variadic parameters, parameter defaults, or other executable top-level assignments.",
            callable.name
        ),
        PythonCallableKind::AsyncFunction => format!(
            "Define exactly one canonical undecorated top-level `async def` function `{}`. You MAY additionally define private implementation helpers, private immutable constants, and invariant TypeVars. Each helper MUST be an undecorated, synchronous, fully annotated top-level function whose name starts with a single `_` but is neither dunder nor reserved `_cott_`; function names MUST be unique. Each constant MUST have a single-leading-underscore name that is neither dunder nor reserved `_cott_`, and be a literal `Final[bool|int|float|str|bytes]` value. Do not define classes, public helpers, mutable globals, decorators, additional async functions, variadic parameters, parameter defaults, or other executable top-level assignments. Await every call to an async Cott facade; never await a synchronous Cott facade.",
            callable.name
        ),
        PythonCallableKind::ImplMethod { concrete } => format!(
            "Define exactly one canonical private top-level function `_cott_impl_{concrete}_{}`. You MAY additionally define private implementation helpers, private immutable constants, and invariant TypeVars. Each helper MUST be an undecorated, synchronous, fully annotated top-level function whose name starts with a single `_` but is neither dunder nor reserved `_cott_`; function names MUST be unique. Each constant MUST have a single-leading-underscore name that is neither dunder nor reserved `_cott_`, and be a literal `Final[bool|int|float|str|bytes]` value. Do not define classes, public helpers, mutable globals, decorators, async functions, variadic parameters, parameter defaults, or other executable top-level assignments. The compiler owns the public class `{concrete}` and binds this helper as its method; never define a class or public method. Import `{concrete}` from `{}` only for the required `self: {concrete}` annotation. Sibling public method calls MUST use `self` (or its direct local alias) and their exact method name.",
            callable.name, callable.module
        ),
        PythonCallableKind::AsyncImplMethod { concrete } => format!(
            "Define exactly one canonical private top-level `async def` function `_cott_impl_{concrete}_{}`. You MAY additionally define private implementation helpers, private immutable constants, and invariant TypeVars. Each helper MUST be an undecorated, synchronous, fully annotated top-level function whose name starts with a single `_` but is neither dunder nor reserved `_cott_`; function names MUST be unique. Each constant MUST have a single-leading-underscore name that is neither dunder nor reserved `_cott_`, and be a literal `Final[bool|int|float|str|bytes]` value. Do not define classes, public helpers, mutable globals, decorators, additional async functions, variadic parameters, parameter defaults, or other executable top-level assignments. The compiler owns the public class `{concrete}` and binds this helper as its method; never define a class or public method. Import `{concrete}` from `{}` only for the required `self: {concrete}` annotation. Sibling public method calls MUST use `self` (or its direct local alias) and their exact method name. Await every call to an async Cott facade or sibling method, never await a synchronous one, and use concurrency only through a direct await of `asyncio.gather(...)` or `async with asyncio.TaskGroup() as <name>`.",
            callable.name, callable.module
        ),
    };
    let external_types = external_types
        .iter()
        .map(|(name, projection)| format!("{name} = {projection}"))
        .collect::<Vec<_>>()
        .join("\n");
    let mut prompt = format!(
        "COTT_AGENT_PROMPT_V1\n\nTARGET\nSymbol: {}\nWrite path: {}\n\nIMPLEMENTATION OWNERSHIP\n{ownership}\n\nCANONICAL IR\n{}\n\nDOCS CONTRACTS EFFECTS\n{docs}\n\nRELEVANT TYPES\n{type_declarations}\n\nPYTHON EXTERNAL TYPE PROJECTIONS\n{external_types}\n\nBOUND SYMBOLS IMPORT RULES\n{bound_symbols}\n\nTYPE MODEL\nPreserve every declared annotation exactly. For Iterator and Generator returns, return the lazy object itself: do not iterate, materialize, normalize, or validate inner values. Use external declarations through their exact public generated aliases; their projected public APIs MAY be called when the contract requires it. Do not reconstruct external paths, use dynamic imports or reflection, or inspect and coerce external values merely to validate a contract. `Dyn[Trait]` is a nominal runtime wrapper: import `Dyn` only from `cott_runtime`, construct it only as `Dyn(value=<compiler-generated concrete>, trait=<exact Trait Protocol>)`, and invoke a trait method only as `dyn.value.method(...)`; never substitute structural values or inspect either wrapper or value.\n",
        callable.cott_symbol,
        write_path.display(),
        String::from_utf8_lossy(selected_ir)
    )
    .into_bytes();
    prompt.extend_from_slice(b"Standard ABI aliases, including integer widths, are annotations and MUST NOT be called. Construct result values only with top-level `cott_runtime.Ok(...)`/`cott_runtime.Err(...)`, never `Result.Ok`/`Result.Err`. Generated payload enum aliases have no members; import and construct top-level `<Enum>_<Variant>` classes from the exact generated `*_types` module, never `<Enum>.<Variant>`.\n");
    prompt.extend_from_slice(b"Generated structs are exact keyword-only dataclasses and MUST be constructed as `Struct(field=...)`; never synthesize `<Struct>_<Variant>`. Payload and singleton variant classes exist only for declared enums. Inspect enum-valued struct fields with the exact `<Enum>_<Variant>` classes.\n");
    prompt.extend_from_slice(b"\nFACTORY TYPE MODEL\n`Factory[Concrete]` maps to `type[Concrete]`: it is the exact compiler-generated `Concrete` class object, never an instance, subclass, or arbitrary callable. Constructor calls MUST match `Concrete`'s inferred Cott init signature. Validation MUST NOT construct or invoke a Factory value.\n");
    prompt.extend_from_slice(b"\nDYN DISPATCH\nA `Dyn[Trait]` call is resolved only against that exact canonical trait origin and its declared inherited members; generic arguments remain part of its annotation. A nearer child member overrides a parent, while same-depth inherited members are ambiguous; unrelated traits with the same method name are not interchangeable. Await an async trait member and do not await a synchronous one.\n");
    prompt.extend_from_slice(b"\nEFFECT CALLS\nCall Cott functions only by their exact imported facade name. Do not alias, store, return, pass, rebind, or shadow a Cott callable, and do not call a value whose Cott identity is dynamic except an exact `dyn.value.method(...)` invocation. For an implementation target, a public sibling method of the same concrete may only be called through a parameter annotated with that concrete (normally `self`) or a direct local alias of one, as `<receiver>.<method>(...)`; it is a Cott call. Every direct or private-helper-reachable Cott call must be covered by the target function's declared effects. Imported stdlib, external projections, generated value constructors, exact Dyn construction, and exact Factory constructors are effect leaves.\n");
    prompt.extend_from_slice(b"\nPRIVATE RUNTIME EFFECT ADAPTERS\nThe only private runtime effect adapters are `cott_runtime._cott_fixture_read`, `cott_runtime._cott_fixture_write`, `cott_runtime._cott_fixture_replace`, `cott_runtime._cott_fixture_http`, and `cott_runtime._cott_fixture_now`. They MAY be used only when the contract is targeted by a compatible declared scenario with an active fixture. Otherwise, an effectful callable MUST NOT invent an adapter name or authority; follow ordinary declared-effect implementation rules and leave it as trust evidence. Do not emulate an effect with stdlib I/O, inspect adapter internals, dynamically import an adapter, or retain an adapter value.\n");
    prompt.extend_from_slice(b"\nSCENARIOS\nScenario fixtures and steps are runner-owned. Scenario calls are facade-only: invoke the exact generated public facade, never a private `_cott_impl` implementation or `cott_bindings` module.\n");
    prompt.extend_from_slice(b"\nCONTAINER ABI\nVariadic Cott `Tuple[T, ...]` uses native `tuple[T, ...]`. Cott `Array[T, N]` uses `CottArray[T, Literal[N]]` and is constructed only as `CottArray(values=(...))`; Cott `Buffer[N]` uses `CottBuffer[Literal[N]]` and is constructed only as `CottBuffer(data=bytes.fromhex(\"...\"))`. Import `CottArray` and `CottBuffer` from `cott_runtime` and `Literal` from `typing` when required; never substitute Python primitives or call ABI aliases.\n");
    if let Some(existing) = existing {
        prompt.extend_from_slice(b"\nEXISTING IMPLEMENTATION\n");
        prompt.extend_from_slice(existing);
    }
    if let Some(rules) = rules {
        prompt.extend_from_slice(b"\nPROJECT RULES\n");
        prompt.extend_from_slice(rules);
        prompt.push(b'\n');
    }
    prompt.extend_from_slice(b"\nImplement only the target Python file. Do not modify .cott contracts, manifests, rules, bindings, generated files, or other implementations. Do not reimplement bound symbols. If the contract must change, report that and leave the target unresolved.\n");
    if prompt.len() > 1024 * 1024 {
        return Err("rendered agent prompt exceeds 1 MiB".to_owned());
    }
    Ok(prompt)
}

fn selected_implementation_kind(callable: &PythonCallable) -> Option<&str> {
    matches!(
        &callable.kind,
        PythonCallableKind::ImplMethod { .. } | PythonCallableKind::AsyncImplMethod { .. }
    )
    .then(|| {
        callable
            .declaration
            .get("selected")
            .and_then(serde_json::Value::as_object)
            .and_then(|selected| selected.get("origin"))
            .and_then(serde_json::Value::as_str)
    })
    .flatten()
    .filter(|kind| matches!(*kind, "default" | "specialization"))
}

pub fn run_agent(
    kind: AgentKind,
    executable: PathBuf,
    workspace: &Path,
    scratch: &Path,
    target: &Path,
    prompt: Vec<u8>,
    timeout_seconds: u16,
) -> Result<AgentRunCandidate, String> {
    let scratch = fs::canonicalize(scratch)
        .map_err(|error| format!("resolve agent scratch {}: {error}", scratch.display()))?;
    let spec = adapter(kind);
    let executable = fs::canonicalize(&executable)
        .map_err(|error| format!("resolve {} executable: {error}", spec.executable_name))?;
    let metadata = fs::symlink_metadata(&executable)
        .map_err(|error| format!("stat {} executable: {error}", spec.executable_name))?;
    if !metadata.is_file() || metadata.file_type().is_symlink() || metadata.nlink() != 1 {
        return Err(format!(
            "{} executable must be a regular single-link file",
            spec.executable_name
        ));
    }
    let executable_bytes = fs::read(&executable)
        .map_err(|error| format!("read {} executable: {error}", spec.executable_name))?;
    if kind == AgentKind::Claude && !native_claude_entrypoint(&executable, &executable_bytes) {
        return Err("claude executable must use the official native entrypoint".to_owned());
    }
    let target_relative = target
        .strip_prefix(workspace)
        .map_err(|_| "agent target escaped workspace")?
        .to_path_buf();
    let mut target_file = OpenOptions::new()
        .read(true)
        .write(true)
        .create_new(true)
        .open(target)
        .map_err(|error| format!("create isolated agent target {}: {error}", target.display()))?;
    let workspace_before = workspace_snapshot(workspace, Some(&target_relative))?;
    let version = run_process(
        &executable,
        spec.version_argv.iter().map(ToString::to_string).collect(),
        workspace,
        &scratch,
        Vec::new(),
        false,
        (kind != AgentKind::Claude).then_some(kind),
        None,
        timeout_seconds,
    )?;
    let version_text = String::from_utf8_lossy(&version.stdout).trim().to_owned();
    let minimum_version =
        parse_version(spec.minimum_version).expect("adapter minimum versions are complete numbers");
    let adapter_version = match kind {
        AgentKind::Codex => version_text
            .strip_prefix("codex-cli ")
            .or_else(|| version_text.strip_prefix("codex "))
            .filter(|version| is_at_least(version, minimum_version)),
        AgentKind::Omp => version_text
            .strip_prefix("omp/")
            .filter(|version| is_at_least(version, minimum_version)),
        AgentKind::Claude if !version.timed_out && version.status == Some(0) => {
            closed_claude_version(&version.stdout)
                .filter(|version| is_at_least(version, minimum_version))
        }
        AgentKind::Claude => None,
    };
    let Some(adapter_version) = adapter_version else {
        return Err(format!(
            "unsupported {} version `{version_text}` (exit {:?}): {}",
            spec.executable_name,
            version.status,
            String::from_utf8_lossy(&version.stderr).trim()
        ));
    };
    let arguments = match kind {
        AgentKind::Codex => vec![
            "exec",
            "--strict-config",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--skip-git-repo-check",
            "--sandbox",
            "workspace-write",
            "--color",
            "never",
            "--cd",
            workspace.to_str().ok_or("workspace is not UTF-8")?,
            "-",
        ]
        .into_iter()
        .map(str::to_owned)
        .collect(),
        AgentKind::Omp => {
            let overlay = scratch.join("omp.yaml");
            fs::write(&overlay, "startup:\n  checkUpdate: false\n")
                .map_err(|error| format!("write OMP overlay: {error}"))?;
            let mut attempt = 0u64;
            let prompt_file = loop {
                let prompt_file = scratch.join(format!("omp-prompt-{attempt}"));
                match OpenOptions::new()
                    .write(true)
                    .create_new(true)
                    .open(&prompt_file)
                {
                    Ok(mut file) => {
                        file.write_all(&prompt)
                            .map_err(|error| format!("write OMP prompt: {error}"))?;
                        break prompt_file;
                    }
                    Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => {
                        attempt += 1;
                    }
                    Err(error) => return Err(format!("create OMP prompt: {error}")),
                }
            };
            vec![
                "-p".to_owned(),
                "--cwd".to_owned(),
                workspace.display().to_string(),
                "--no-session".to_owned(),
                "--no-rules".to_owned(),
                "--no-skills".to_owned(),
                "--no-extensions".to_owned(),
                "--no-lsp".to_owned(),
                "--no-pty".to_owned(),
                "--no-title".to_owned(),
                "--tools".to_owned(),
                "read,grep,glob,edit,write".to_owned(),
                "--approval-mode".to_owned(),
                "yolo".to_owned(),
                "--max-time".to_owned(),
                format!("{timeout_seconds}s"),
                "--config".to_owned(),
                overlay.display().to_string(),
                format!(
                    "@{}",
                    prompt_file.to_str().ok_or("OMP prompt path is not UTF-8")?
                ),
            ]
        }
        AgentKind::Claude => CLAUDE
            .argv_template
            .iter()
            .map(ToString::to_string)
            .collect(),
    };
    let stdin = if spec.prompt_on_stdin {
        prompt.clone()
    } else {
        Vec::new()
    };
    let started = Instant::now();
    let completed = run_process(
        &executable,
        arguments,
        workspace,
        &scratch,
        stdin,
        true,
        Some(kind),
        Some(target),
        timeout_seconds,
    )?;
    let duration_ms = started.elapsed().as_millis().min(u128::from(u64::MAX)) as u64;
    if fs::read(&executable)
        .map_err(|error| format!("re-read {} executable: {error}", spec.executable_name))?
        != executable_bytes
    {
        return Err(format!(
            "{} executable changed during generation",
            spec.executable_name
        ));
    }
    let after = workspace_snapshot(workspace, Some(&target_relative))?;
    if workspace_before != after {
        return Err("agent modified an unauthorized workspace path".to_owned());
    }
    if completed.timed_out || completed.status != Some(0) {
        return Err(format!(
            "{} failed with status {:?}: {}",
            spec.executable_name,
            completed.status,
            String::from_utf8_lossy(&completed.stderr).trim()
        ));
    }
    if kind == AgentKind::Claude && !claude_success(&completed.stdout) {
        return Err("claude returned an invalid result".to_owned());
    }
    let metadata = target_file
        .metadata()
        .map_err(|error| format!("stat agent target: {error}"))?;
    if !metadata.is_file() || metadata.nlink() != 1 {
        return Err("agent candidate must be a regular single-link file".to_owned());
    }
    if metadata.len() > 1024 * 1024 {
        return Err("agent implementation exceeds 1 MiB".to_owned());
    }
    target_file
        .seek(SeekFrom::Start(0))
        .map_err(|error| format!("seek agent target: {error}"))?;
    let mut implementation = Vec::with_capacity(metadata.len() as usize);
    target_file
        .read_to_end(&mut implementation)
        .map_err(|error| format!("read agent target: {error}"))?;
    if implementation.is_empty() {
        return Err(format!("agent did not write target {}", target.display()));
    }
    while implementation.last() == Some(&b'\n') {
        implementation.pop();
    }
    implementation.push(b'\n');
    Ok(AgentRunCandidate {
        implementation,
        executable: executable.clone(),
        executable_hash: format!("sha256:{}", sha256_hex(&executable_bytes)),
        adapter_version: adapter_version.to_owned(),
        prompt_hash: format!("sha256:{}", sha256_hex(&prompt)),
        stdout: completed.stdout,
        stderr: completed.stderr,
        exit_code: completed.status,
        timed_out: completed.timed_out,
        duration_ms,
        environment_names: agent_environment_names(kind),
    })
}

fn native_claude_entrypoint(executable: &Path, bytes: &[u8]) -> bool {
    if executable.file_name().and_then(|name| name.to_str()) == Some("cli.js") {
        return false;
    }
    let shebang = bytes
        .split(|byte| *byte == b'\n')
        .next()
        .unwrap_or_default();
    !shebang.starts_with(b"#!")
        || !shebang
            .split(|byte| byte.is_ascii_whitespace())
            .any(|word| word == b"node" || word.ends_with(b"/node"))
}

fn closed_claude_version(stdout: &[u8]) -> Option<&str> {
    let stdout = std::str::from_utf8(stdout).ok()?;
    let mut tokens = stdout.split_ascii_whitespace();
    let version = tokens.next()?;
    (tokens.next().is_none() && closed_semver(version)).then_some(version)
}

fn closed_semver(version: &str) -> bool {
    let mut parts = version.split('.');
    let valid_part = |part: Option<&str>| {
        part.is_some_and(|part| {
            !part.is_empty()
                && part.bytes().all(|byte| byte.is_ascii_digit())
                && (part.len() == 1 || !part.starts_with('0'))
        })
    };
    valid_part(parts.next())
        && valid_part(parts.next())
        && valid_part(parts.next())
        && parts.next().is_none()
}

fn claude_success(stdout: &[u8]) -> bool {
    let Ok(serde_json::Value::Object(result)) = serde_json::from_slice(stdout) else {
        return false;
    };
    result.get("type").and_then(serde_json::Value::as_str) == Some("result")
        && result.get("subtype").and_then(serde_json::Value::as_str) == Some("success")
        && result.get("is_error").and_then(serde_json::Value::as_bool) == Some(false)
        && result
            .get("result")
            .is_some_and(serde_json::Value::is_string)
}

fn workspace_snapshot(
    root: &Path,
    excluded: Option<&Path>,
) -> Result<BTreeMap<PathBuf, (u8, u32, u64, String)>, String> {
    let mut snapshot = BTreeMap::new();
    let mut pending = vec![root.to_path_buf()];
    while let Some(directory) = pending.pop() {
        let mut entries = fs::read_dir(&directory)
            .map_err(|error| format!("read agent workspace {}: {error}", directory.display()))?
            .collect::<Result<Vec<_>, _>>()
            .map_err(|error| format!("read agent workspace entry: {error}"))?;
        entries.sort_by_key(std::fs::DirEntry::file_name);
        for entry in entries {
            let path = entry.path();
            let relative = path
                .strip_prefix(root)
                .map_err(|_| "agent workspace path escaped root")?
                .to_path_buf();
            if excluded == Some(relative.as_path()) {
                continue;
            }
            let metadata = fs::symlink_metadata(&path)
                .map_err(|error| format!("stat agent workspace {}: {error}", path.display()))?;
            if metadata.file_type().is_symlink() {
                return Err(format!(
                    "agent workspace contains a symlink: {}",
                    path.display()
                ));
            }
            if metadata.is_dir() {
                snapshot.insert(relative, (1, metadata.mode(), 0, String::new()));
                pending.push(path);
            } else if metadata.is_file() && metadata.nlink() == 1 {
                let bytes = fs::read(&path)
                    .map_err(|error| format!("read agent workspace {}: {error}", path.display()))?;
                snapshot.insert(
                    relative,
                    (0, metadata.mode(), bytes.len() as u64, sha256_hex(&bytes)),
                );
            } else {
                return Err(format!(
                    "agent workspace entry is not a regular single-link file: {}",
                    path.display()
                ));
            }
        }
    }
    Ok(snapshot)
}

fn agent_environment_names(kind: AgentKind) -> Vec<String> {
    let mut names = vec![
        "HOME".to_owned(),
        "PATH".to_owned(),
        "PYTHONDONTWRITEBYTECODE".to_owned(),
        "TMPDIR".to_owned(),
    ];
    for name in [
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
        "HTTPS_PROXY",
        "HTTP_PROXY",
        "NO_PROXY",
    ] {
        if std::env::var_os(name).is_some() {
            names.push(name.to_owned());
        }
    }
    let home = std::env::var_os("HOME").map(PathBuf::from);
    match kind {
        AgentKind::Codex => {
            for name in ["CODEX_API_KEY", "CODEX_ACCESS_TOKEN"] {
                if std::env::var_os(name).is_some() {
                    names.push(name.to_owned());
                }
            }
            if std::env::var_os("CODEX_HOME")
                .map(PathBuf::from)
                .or_else(|| home.map(|home| home.join(".codex")))
                .is_some_and(|path| path.is_dir())
            {
                names.push("CODEX_HOME".to_owned());
            }
        }
        AgentKind::Omp => {
            if std::env::var_os("PI_CODING_AGENT_DIR")
                .map(PathBuf::from)
                .or_else(|| home.map(|home| home.join(".omp/agent")))
                .is_some_and(|path| path.is_dir())
            {
                names.push("PI_CODING_AGENT_DIR".to_owned());
            }
        }
        AgentKind::Claude => {
            if std::env::var_os("ANTHROPIC_API_KEY").is_some() {
                names.push("ANTHROPIC_API_KEY".to_owned());
            }
            names.push("CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC".to_owned());
            names.push("DISABLE_ERROR_REPORTING".to_owned());
            names.push("DISABLE_TELEMETRY".to_owned());
        }
    }
    names.sort();
    names
}

fn run_process(
    executable: &Path,
    arguments: Vec<String>,
    workspace: &Path,
    scratch: &Path,
    stdin: Vec<u8>,
    network: bool,
    credential_kind: Option<AgentKind>,
    writable_target: Option<&Path>,
    timeout_seconds: u16,
) -> Result<crate::sandbox::CompletedProcess, String> {
    let mut read_only = vec![executable.to_path_buf()];
    let mut environment = BTreeMap::from([
        ("HOME".to_owned(), scratch.display().to_string()),
        ("TMPDIR".to_owned(), scratch.display().to_string()),
        ("PATH".to_owned(), "/usr/bin:/bin".to_owned()),
        ("PYTHONDONTWRITEBYTECODE".to_owned(), "1".to_owned()),
    ]);
    for name in [
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
        "HTTPS_PROXY",
        "HTTP_PROXY",
        "NO_PROXY",
    ] {
        if let Some(value) = std::env::var_os(name) {
            let value = value
                .into_string()
                .map_err(|_| format!("{name} is not valid UTF-8"))?;
            if matches!(name, "SSL_CERT_FILE" | "SSL_CERT_DIR") {
                let path = fs::canonicalize(&value)
                    .map_err(|error| format!("resolve {name} `{value}`: {error}"))?;
                read_only.push(path);
            }
            environment.insert(name.to_owned(), value);
        }
    }
    if let Some(kind) = credential_kind {
        let home = std::env::var_os("HOME").map(PathBuf::from);
        match kind {
            AgentKind::Codex => {
                for name in ["CODEX_API_KEY", "CODEX_ACCESS_TOKEN"] {
                    if let Some(value) = std::env::var_os(name) {
                        environment.insert(
                            name.to_owned(),
                            value
                                .into_string()
                                .map_err(|_| format!("{name} is not valid UTF-8"))?,
                        );
                    }
                }
                let credential_root = std::env::var_os("CODEX_HOME")
                    .map(PathBuf::from)
                    .or_else(|| home.map(|home| home.join(".codex")));
                if let Some(root) = credential_root.filter(|root| root.is_dir()) {
                    let root = fs::canonicalize(root)
                        .map_err(|error| format!("resolve CODEX_HOME: {error}"))?;
                    read_only.push(root.clone());
                    environment.insert("CODEX_HOME".to_owned(), root.display().to_string());
                }
            }
            AgentKind::Omp => {
                let credential_root = std::env::var_os("PI_CODING_AGENT_DIR")
                    .map(PathBuf::from)
                    .or_else(|| home.as_ref().map(|home| home.join(".omp/agent")));
                if network {
                    if let Some(root) = credential_root.filter(|root| root.is_dir()) {
                        let isolated = scratch.join("omp-agent");
                        fs::create_dir_all(&isolated)
                            .map_err(|error| format!("create isolated OMP state: {error}"))?;
                        for name in ["config.yml", "agent.db"] {
                            let source = root.join(name);
                            if source.is_file() {
                                fs::copy(&source, isolated.join(name)).map_err(|error| {
                                    format!("copy isolated OMP state `{name}`: {error}")
                                })?;
                            }
                        }
                        environment.insert(
                            "PI_CODING_AGENT_DIR".to_owned(),
                            isolated.display().to_string(),
                        );
                    }
                    if let Some(home) = home {
                        let natives = home.join(".omp/natives");
                        if natives.is_dir() {
                            read_only.push(
                                fs::canonicalize(&natives).map_err(|error| {
                                    format!("resolve OMP native addons: {error}")
                                })?,
                            );
                            environment.insert("HOME".to_owned(), home.display().to_string());
                        }
                    }
                }
            }
            AgentKind::Claude => {
                if let Some(value) = std::env::var_os("ANTHROPIC_API_KEY") {
                    environment.insert(
                        "ANTHROPIC_API_KEY".to_owned(),
                        value
                            .into_string()
                            .map_err(|_| "ANTHROPIC_API_KEY is not valid UTF-8")?,
                    );
                }
                environment.insert(
                    "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC".to_owned(),
                    "1".to_owned(),
                );
                environment.insert("DISABLE_TELEMETRY".to_owned(), "1".to_owned());
                environment.insert("DISABLE_ERROR_REPORTING".to_owned(), "1".to_owned());
            }
        }
    }
    if network {
        if let Ok(resolver) = fs::canonicalize("/etc/resolv.conf") {
            read_only.push(resolver);
        }
    }
    read_only.push(workspace.to_path_buf());
    let mut writable = vec![scratch.to_path_buf()];
    if let Some(target) = writable_target {
        writable.push(target.to_path_buf());
    }
    let address_space_bytes = if credential_kind == Some(AgentKind::Omp) {
        128 * 1024 * 1024 * 1024
    } else {
        4 * 1024 * 1024 * 1024
    };
    let writable_bytes = if credential_kind == Some(AgentKind::Omp) {
        512 * 1024 * 1024
    } else {
        64 * 1024 * 1024
    };
    run(&SandboxSpec {
        program: executable.to_path_buf(),
        arguments,
        cwd: workspace.to_path_buf(),
        environment,
        stdin,
        binds: BindMounts {
            read_only,
            writable,
        },
        network: if network {
            NetworkAccess::Enabled
        } else {
            NetworkAccess::Disabled
        },
        limits: ResourceLimits {
            cpu_time: Duration::from_secs(timeout_seconds.into()),
            address_space_bytes,
            process_count: 64,
            open_files: 256,
            file_size_bytes: writable_bytes,
            wall_time: Duration::from_secs(timeout_seconds.into()),
            stream_limit_bytes: 16 * 1024 * 1024,
            writable_bytes,
        },
    })
    .map_err(|error| error.to_string())
}
