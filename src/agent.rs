use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, OpenOptions};
use std::io::{Read, Seek, SeekFrom, Write};
use std::os::unix::fs::MetadataExt;
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant};

use crate::binding::ResolvedBinding;
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
    context: &serde_json::Value,
    references: &[ResolvedBinding],
    external_types: &BTreeMap<String, String>,
    existing: Option<&[u8]>,
    feedback: Option<&str>,
    write_path: &Path,
) -> Result<Vec<u8>, String> {
    if let Some(kind) = selected_implementation_kind(callable) {
        return Err(format!(
            "compiler-owned {kind} implementation method `{}` must not be sent to an agent",
            callable.cott_symbol
        ));
    }
    let (symbol, declarations, project_rules) = intent_parts(callable, context)?;
    let existing_text = match existing {
        Some(bytes) => Some(
            std::str::from_utf8(bytes)
                .map_err(|_| "existing implementation must be valid UTF-8".to_owned())?,
        ),
        None => None,
    };
    if existing_text.map(str::len).unwrap_or(0) > MAX_RULE_BYTES
        || feedback.map(str::len).unwrap_or(0) > MAX_RULE_BYTES
        || project_rules.len() > MAX_RULE_BYTES
    {
        return Err("agent prompt input exceeds 1 MiB".to_owned());
    }
    let mut identities = BTreeSet::new();
    collect_identities(declarations, &mut identities);
    let features = type_features(declarations);
    let mut relevant = references
        .iter()
        .filter(|binding| {
            binding.cott_symbol != symbol && identities.contains(&binding.cott_symbol)
        })
        .collect::<Vec<_>>();
    relevant.sort_by(|left, right| left.cott_symbol.cmp(&right.cott_symbol));
    for binding in &relevant {
        if binding.bytes.len() > MAX_RULE_BYTES {
            return Err("agent prompt input exceeds 1 MiB".to_owned());
        }
        std::str::from_utf8(&binding.bytes).map_err(|_| {
            format!(
                "reference implementation `{}` must be valid UTF-8",
                binding.cott_symbol
            )
        })?;
    }
    let mut prompt = String::from("COTT_AGENT_PROMPT_V1\n\nAUTHORITY\n");
    prompt.push_str(AUTHORITY);
    prompt.push_str("\nCURRENT INTENT\n");
    prompt.push_str(&format!(
        "Symbol: {symbol}\nWrite path: {}\n",
        write_path.display()
    ));
    append_intent_docs(declarations, symbol, &mut prompt);
    prompt.push_str("\nFORMAL DECLARATIONS\n");
    prompt.push_str(
        &serde_json::to_string_pretty(&strip_docs(declarations))
            .map_err(|error| error.to_string())?,
    );
    prompt.push('\n');
    prompt.push_str("\nPROJECT RULES\n");
    prompt.push_str(project_rules);
    if !project_rules.is_empty() && !project_rules.ends_with('\n') {
        prompt.push('\n');
    }
    prompt.push_str("\nREFERENCE IMPLEMENTATIONS\n");
    prompt.push_str(
        "These are non-authoritative examples. They do not establish new business requirements.\n",
    );
    for binding in relevant {
        let text = std::str::from_utf8(&binding.bytes).map_err(|_| {
            format!(
                "reference implementation `{}` must be valid UTF-8",
                binding.cott_symbol
            )
        })?;
        prompt.push_str(&format!("\n## {}\n{text}", binding.cott_symbol));
        if !text.ends_with('\n') {
            prompt.push('\n');
        }
    }
    if let Some(text) = existing_text.filter(|text| !text.is_empty()) {
        prompt.push_str(&format!("\n## {symbol} (existing)\n{text}"));
        if !text.ends_with('\n') {
            prompt.push('\n');
        }
    }
    prompt.push_str("\nPYTHON OUTPUT RULES\n");
    prompt.push_str(&ownership(callable));
    prompt.push('\n');
    append_python_rules(
        callable,
        declarations,
        external_types,
        &identities,
        &features,
        &mut prompt,
    );
    if let Some(feedback) = feedback.filter(|text| !text.is_empty()) {
        prompt.push_str("\nVALIDATION FEEDBACK\n");
        prompt.push_str(
            "Diagnostics from a previous candidate. They do not add business requirements.\n",
        );
        prompt.push_str(feedback);
        if !feedback.ends_with('\n') {
            prompt.push('\n');
        }
    }
    let prompt = prompt.into_bytes();
    if prompt.len() > MAX_RULE_BYTES {
        return Err("rendered agent prompt exceeds 1 MiB".to_owned());
    }
    Ok(prompt)
}

const AUTHORITY: &str = "\
Formal source constraints in FORMAL DECLARATIONS are authoritative.
CURRENT INTENT documentation refines intended behavior; it does not replace the source contract.
PROJECT RULES may constrain implementation but cannot redefine the source contract.
If documentation or project rules conflict with formal declarations, report the conflict and leave the target unresolved; do not guess.
Reference implementations and validation diagnostics never establish new business requirements.
";

const PRIVATE_MEMBERS: &str = "You MAY additionally define private implementation helpers, private immutable constants, and invariant TypeVars. Each helper MUST be an undecorated, synchronous, fully annotated top-level function whose name starts with a single `_` but is neither dunder nor reserved `_cott_`; function names MUST be unique. Each constant MUST have a single-leading-underscore name that is neither dunder nor reserved `_cott_`, and be a literal `Final[bool|int|float|str|bytes]` value.";

struct TypeFeatures {
    factory: bool,
    dyn_trait: bool,
    array: bool,
    buffer: bool,
    lazy: bool,
    scenario: bool,
    external: bool,
    enum_ty: bool,
    struct_ty: bool,
    tuple: bool,
    result: bool,
    option: bool,
    unit: bool,
    list: bool,
    set: bool,
    map: bool,
}

fn intent_parts<'a>(
    callable: &PythonCallable,
    context: &'a serde_json::Value,
) -> Result<(&'a str, &'a serde_json::Value, &'a str), String> {
    let object = context
        .as_object()
        .ok_or_else(|| "intent context must be an object".to_owned())?;
    let symbol = object
        .get("symbol")
        .and_then(serde_json::Value::as_str)
        .ok_or_else(|| "intent context symbol must be a string".to_owned())?;
    if symbol != callable.cott_symbol {
        return Err("intent context symbol does not match callable".to_owned());
    }
    let declarations = object
        .get("declarations")
        .ok_or_else(|| "intent context declarations are required".to_owned())?;
    if !declarations.is_object() {
        return Err("intent context declarations must be an object".to_owned());
    }
    let project_rules = object
        .get("project_rules")
        .and_then(serde_json::Value::as_str)
        .ok_or_else(|| "intent context project_rules must be a string".to_owned())?;
    Ok((symbol, declarations, project_rules))
}

fn ownership(callable: &PythonCallable) -> String {
    match &callable.kind {
        PythonCallableKind::Function => format!(
            "Define exactly one canonical top-level function `{}`. {PRIVATE_MEMBERS} Do not define classes, public helpers, mutable globals, decorators, async functions, variadic parameters, parameter defaults, or other executable top-level assignments.",
            callable.name
        ),
        PythonCallableKind::AsyncFunction => format!(
            "Define exactly one canonical undecorated top-level `async def` function `{}`. {PRIVATE_MEMBERS} Do not define classes, public helpers, mutable globals, decorators, additional async functions, variadic parameters, parameter defaults, or other executable top-level assignments. Await every call to an async Cott facade; never await a synchronous Cott facade. Detached task APIs (`create_task`, `ensure_future`, `Task`, and loop task creation) are forbidden; only direct awaited `asyncio.gather(...)` and `async with asyncio.TaskGroup() as <name>` are allowed.",
            callable.name
        ),
        PythonCallableKind::ImplMethod { concrete } => format!(
            "Define exactly one canonical private top-level function `_cott_impl_{concrete}_{}`. {PRIVATE_MEMBERS} Do not define classes, public helpers, mutable globals, decorators, async functions, variadic parameters, parameter defaults, or other executable top-level assignments. The compiler owns the public class `{concrete}` and binds this helper as its method; never define a class or public method. Import `{concrete}` from `{}` only for the required `self: {concrete}` annotation. Sibling public method calls MUST use `self` (or its direct local alias) and their exact method name.",
            callable.name, callable.module
        ),
        PythonCallableKind::AsyncImplMethod { concrete } => format!(
            "Define exactly one canonical private top-level `async def` function `_cott_impl_{concrete}_{}`. {PRIVATE_MEMBERS} Do not define classes, public helpers, mutable globals, decorators, additional async functions, variadic parameters, parameter defaults, or other executable top-level assignments. The compiler owns the public class `{concrete}` and binds this helper as its method; never define a class or public method. Import `{concrete}` from `{}` only for the required `self: {concrete}` annotation. Sibling public method calls MUST use `self` (or its direct local alias) and their exact method name. Await every call to an async Cott facade or sibling method, never await a synchronous one, and use concurrency only through a direct await of `asyncio.gather(...)` or `async with asyncio.TaskGroup() as <name>`.",
            callable.name, callable.module
        ),
    }
}

fn append_python_rules(
    callable: &PythonCallable,
    declarations: &serde_json::Value,
    external_types: &BTreeMap<String, String>,
    identities: &BTreeSet<String>,
    features: &TypeFeatures,
    prompt: &mut String,
) {
    prompt.push_str("CPython 3.14.6, fully annotated Python. Import only names the implementation file actually references. Keep every `def` signature on one physical line and end the file with exactly one newline.\n");
    prompt.push_str("Preserve every declared annotation exactly. Standard ABI aliases, including integer widths, are annotations and MUST NOT be called. Numeric ABI aliases are plain int/float at runtime: use ordinary arithmetic and comparisons and return the result directly, never call or construct a numeric alias. Never replace contract annotations or returned contract containers with Python primitives or built-in list/set/dict.\n");
    prompt.push_str("Do not use dynamic imports, reflection, dynamic compilation, or suppressions. Imports may use the Python standard library, `cott_runtime`, exact generated facade and `*_types` modules, or lock-selected external distributions.\n");
    prompt.push_str("Exact generated Cott facade modules MAY be imported directly or from their parent package, with an optional module alias, for module-qualified access. Do not alias imported Cott callables. Import public generated symbols through `from <module> import name` and generated value types through `from <module>_types import Type` only for selected identities. Do not import any other project-local module or import concrete facade classes from generated type modules.\n");
    for line in generated_import_lines(declarations, callable) {
        prompt.push_str(&line);
        prompt.push('\n');
    }
    if let PythonCallableKind::ImplMethod { concrete }
    | PythonCallableKind::AsyncImplMethod { concrete } = &callable.kind
    {
        prompt.push_str(&format!(
            "The canonical function's leading `self` annotation must be `{concrete}`.\n"
        ));
    }
    prompt.push_str("Call Cott functions only by their exact imported facade name. Do not alias, store, return, pass, rebind, or shadow a Cott callable. Every direct or private-helper-reachable Cott call must be covered by the target function's declared effects. Imported stdlib, external projections, and generated value constructors are effect leaves.\n");
    if matches!(
        &callable.kind,
        PythonCallableKind::ImplMethod { .. } | PythonCallableKind::AsyncImplMethod { .. }
    ) {
        prompt.push_str("For an implementation target, a public sibling method of the same concrete may only be called through a parameter annotated with that concrete (normally `self`) or a direct local alias of one, as `<receiver>.<method>(...)`; it is a Cott call.\n");
    }
    if features.result {
        prompt.push_str("Construct result values only with top-level `cott_runtime.Ok(...)`/`cott_runtime.Err(...)`, never `Result.Ok`/`Result.Err`. Never spell Result as an Ok/Err union. Return `Ok(value=UNIT)` for Result[Unit, E].\n");
    }
    if features.unit {
        prompt.push_str("`Unit` is the annotation and `UNIT` is its only value.\n");
    }
    if features.option {
        prompt.push_str("For Option annotations use the top-level `Some(value=...)` and `Nothing()` variants, never `Option.Some` or `Option.Nothing`.\n");
    }
    if features.tuple {
        prompt.push_str("Variadic Cott `Tuple[T, ...]` and fixed Cott Tuple use native `tuple[...]` annotations and `(a, b)` values; never import a nonexistent `List`.\n");
    }
    if features.list || features.set || features.map {
        prompt.push_str("Use contract containers directly: CottList(values=xs), CottSet(values=xs), FrozenMap(values={}). Import CottList, CottSet, and FrozenMap from cott_runtime as required.\n");
    }
    if features.array || features.buffer {
        prompt.push_str("Cott `Array[T, N]` uses `CottArray[T, Literal[N]]` and is constructed only as `CottArray(values=(...))`; Cott `Buffer[N]` uses `CottBuffer[Literal[N]]` and is constructed only as `CottBuffer(data=bytes.fromhex(\"...\"))`. Import `CottArray` and `CottBuffer` from `cott_runtime` and `Literal` from `typing` when required; never substitute Python primitives or call ABI aliases.\n");
    }
    if features.enum_ty {
        prompt.push_str("Generated payload enum aliases have no members; import and construct top-level `<Enum>_<Variant>` classes from the exact generated `*_types` module, never `<Enum>.<Variant>`.\n");
    }
    if features.struct_ty {
        prompt.push_str("Generated structs are exact keyword-only dataclasses and MUST be constructed as `Struct(field=...)`; never synthesize `<Struct>_<Variant>`. Payload and singleton variant classes exist only for declared enums.\n");
    }
    if features.lazy {
        prompt.push_str("For Iterator and Generator returns, return the lazy object itself: do not iterate, materialize, normalize, or validate inner values.\n");
    }
    if features.factory {
        prompt.push_str("`Factory[Concrete]` maps to `type[Concrete]`: it is the exact compiler-generated `Concrete` class object, never an instance, subclass, or arbitrary callable. Constructor calls MUST match `Concrete`'s inferred Cott init signature. Validation MUST NOT construct or invoke a Factory value.\n");
        let imports = factory_import_lines(declarations, &callable.module);
        if !imports.is_empty() {
            prompt.push_str("Factory annotations require these exact concrete public-facade imports; do not substitute them or import from `*_types`:\n");
            for line in imports {
                prompt.push_str(&line);
                prompt.push('\n');
            }
        }
    }
    if features.dyn_trait {
        prompt.push_str("`Dyn[Trait]` is a nominal runtime wrapper: import `Dyn` only from `cott_runtime`, construct it only as `Dyn(value=<compiler-generated concrete>, trait=<exact Trait Protocol>)`, and invoke a trait method only as `dyn.value.method(...)`; never substitute structural values or inspect either wrapper or value. A `Dyn[Trait]` call is resolved only against that exact canonical trait origin and its declared inherited members.\n");
    }
    if features.external {
        prompt.push_str("Use external declarations through their exact public generated aliases; their projected public APIs MAY be called when the contract requires it. Do not reconstruct external paths or inspect and coerce external values merely to validate a contract. `typing.cast` MAY be used only from a concrete external SDK return to its declared external projection when upstream stubs are incompatible; never cast Cott-owned values.\n");
        let projections = external_types
            .iter()
            .filter(|(name, _)| identities.contains(*name))
            .map(|(name, projection)| format!("{name} = {projection}"))
            .collect::<Vec<_>>();
        if !projections.is_empty() {
            prompt.push_str("PYTHON EXTERNAL TYPE PROJECTIONS\n");
            prompt.push_str(&projections.join("\n"));
            prompt.push('\n');
        }
    }
    if features.scenario {
        prompt.push_str("Scenario fixtures and steps are runner-owned. Scenario calls are facade-only: invoke the exact generated public facade, never a private `_cott_impl` implementation or `cott_bindings` module. The only private runtime effect adapters are `cott_runtime._cott_fixture_read`, `cott_runtime._cott_fixture_write`, `cott_runtime._cott_fixture_replace`, `cott_runtime._cott_fixture_http`, and `cott_runtime._cott_fixture_now`. They MAY be used only when the contract is targeted by a compatible declared scenario with an active fixture. Otherwise, an effectful callable MUST NOT invent an adapter name or authority. Do not emulate an effect with stdlib I/O, inspect adapter internals, dynamically import an adapter, or retain an adapter value.\n");
    }
    prompt.push_str("Implement only the target Python file. Do not modify .cott contracts, manifests, rules, bindings, generated files, or other implementations. Do not reimplement bound symbols. If the contract must change, report that and leave the target unresolved.\n");
}

fn append_intent_docs(declarations: &serde_json::Value, target: &str, prompt: &mut String) {
    let Some(modules) = declarations.as_object() else {
        return;
    };
    for module in modules.values() {
        let Some(decls) = module
            .get("declarations")
            .and_then(serde_json::Value::as_array)
        else {
            continue;
        };
        for declaration in decls {
            walk_intent_docs(declaration, None, None, None, target, prompt);
        }
    }
}

fn walk_intent_docs<'a>(
    value: &'a serde_json::Value,
    mut owner: Option<&'a str>,
    mut member: Option<&'a str>,
    via: Option<&str>,
    target: &str,
    prompt: &mut String,
) {
    match value {
        serde_json::Value::Array(values) => {
            for value in values {
                walk_intent_docs(value, owner, member, via, target, prompt);
            }
        }
        serde_json::Value::Object(object) => {
            let kind = object.get("kind").and_then(serde_json::Value::as_str);
            let name = object
                .get("name")
                .and_then(serde_json::Value::as_str)
                .or_else(|| {
                    object
                        .get("trait_method")
                        .and_then(serde_json::Value::as_str)
                        .and_then(|symbol| symbol.rsplit('.').next())
                });
            if kind.is_some_and(declaration_kind) {
                if let Some(name) = name {
                    owner = Some(name);
                    member = None;
                }
            } else if via == Some("init") {
                member = Some("init");
            } else if !kind.is_some_and(type_expr_kind) {
                if let (Some(_), Some(name)) = (owner, name) {
                    member = Some(name);
                }
            }
            if let Some(doc) = declaration_doc(value) {
                emit_intent_doc(
                    owner,
                    member,
                    kind.is_some_and(type_expr_kind),
                    target,
                    doc,
                    prompt,
                );
            }
            for (key, child) in object {
                if key == "doc" {
                    continue;
                }
                let child_via = (key == "init").then_some("init");
                walk_intent_docs(child, owner, member, child_via, target, prompt);
            }
        }
        _ => {}
    }
}

fn emit_intent_doc(
    owner: Option<&str>,
    member: Option<&str>,
    type_doc: bool,
    target: &str,
    doc: &str,
    prompt: &mut String,
) {
    let mut symbol = String::new();
    if let Some(owner) = owner {
        symbol.push_str(owner);
    }
    if let Some(member) = member {
        if !symbol.is_empty() {
            symbol.push('.');
        }
        symbol.push_str(member);
    }
    if symbol.is_empty() {
        return;
    }
    let marker = if symbol == target { " (target)" } else { "" };
    if type_doc {
        prompt.push_str(&format!("{symbol}{marker} type:\n{doc}\n\n"));
    } else {
        prompt.push_str(&format!("{symbol}{marker}:\n{doc}\n\n"));
    }
}

fn declaration_kind(kind: &str) -> bool {
    matches!(
        kind,
        "function"
            | "struct"
            | "enum"
            | "alias"
            | "newtype"
            | "trait"
            | "impl"
            | "const"
            | "rule"
            | "resource"
            | "scenario"
            | "external_type"
            | "specialization"
    )
}

fn type_expr_kind(kind: &str) -> bool {
    matches!(
        kind,
        "primitive"
            | "named"
            | "type_parameter"
            | "associated_projection"
            | "list"
            | "set"
            | "map"
            | "tuple"
            | "array"
            | "buffer"
            | "option"
            | "result"
            | "iterator"
            | "async_iterator"
            | "generator"
            | "async_generator"
            | "dyn"
            | "factory"
            | "opaque"
    )
}

fn strip_docs(value: &serde_json::Value) -> serde_json::Value {
    match value {
        serde_json::Value::Array(values) => {
            serde_json::Value::Array(values.iter().map(strip_docs).collect())
        }
        serde_json::Value::Object(object) => serde_json::Value::Object(
            object
                .iter()
                .filter(|(key, _)| *key != "doc")
                .map(|(key, child)| (key.clone(), strip_docs(child)))
                .collect(),
        ),
        other => other.clone(),
    }
}

fn declaration_doc(value: &serde_json::Value) -> Option<&str> {
    match value.get("doc") {
        Some(serde_json::Value::String(text)) if !text.is_empty() => Some(text),
        Some(serde_json::Value::Object(doc)) => doc
            .get("text")
            .and_then(serde_json::Value::as_str)
            .filter(|text| !text.is_empty()),
        _ => None,
    }
}

fn collect_identities(value: &serde_json::Value, identities: &mut BTreeSet<String>) {
    match value {
        serde_json::Value::Array(values) => {
            for value in values {
                collect_identities(value, identities);
            }
        }
        serde_json::Value::Object(object) => {
            for key in ["name", "symbol", "target", "trait_method"] {
                if let Some(name) = object.get(key).and_then(serde_json::Value::as_str) {
                    identities.insert(name.to_owned());
                }
            }
            if object.get("kind").and_then(serde_json::Value::as_str) == Some("impl") {
                if let Some(name) = object.get("name").and_then(serde_json::Value::as_str) {
                    for method in object
                        .get("selected_methods")
                        .and_then(serde_json::Value::as_array)
                        .into_iter()
                        .flatten()
                        .chain(
                            object
                                .get("methods")
                                .and_then(serde_json::Value::as_array)
                                .into_iter()
                                .flatten(),
                        )
                    {
                        let method_name = method
                            .get("name")
                            .and_then(serde_json::Value::as_str)
                            .or_else(|| {
                                method
                                    .get("trait_method")
                                    .and_then(serde_json::Value::as_str)
                            })
                            .map(|name| name.rsplit('.').next().unwrap_or(name));
                        if let Some(method_name) = method_name {
                            identities.insert(format!("{name}.{method_name}"));
                        }
                    }
                }
            }
            for value in object.values() {
                collect_identities(value, identities);
            }
        }
        _ => {}
    }
}

fn type_features(value: &serde_json::Value) -> TypeFeatures {
    let mut kinds = BTreeSet::new();
    collect_kinds(value, &mut kinds);
    TypeFeatures {
        factory: kinds.contains("factory"),
        dyn_trait: kinds.contains("dyn"),
        array: kinds.contains("array"),
        buffer: kinds.contains("buffer"),
        lazy: ["iterator", "generator", "async_iterator", "async_generator"]
            .iter()
            .any(|kind| kinds.contains(*kind)),
        scenario: kinds.contains("scenario"),
        external: kinds.contains("external_type"),
        enum_ty: kinds.contains("enum"),
        struct_ty: kinds.contains("struct"),
        tuple: kinds.contains("tuple"),
        result: kinds.contains("result"),
        option: kinds.contains("option"),
        unit: kinds.contains("unit"),
        list: kinds.contains("list"),
        set: kinds.contains("set"),
        map: kinds.contains("map"),
    }
}

fn collect_kinds(value: &serde_json::Value, kinds: &mut BTreeSet<String>) {
    match value {
        serde_json::Value::Array(values) => {
            for value in values {
                collect_kinds(value, kinds);
            }
        }
        serde_json::Value::Object(object) => {
            if let Some(kind) = object.get("kind").and_then(serde_json::Value::as_str) {
                kinds.insert(kind.to_owned());
                if kind == "primitive"
                    && object.get("name").and_then(serde_json::Value::as_str) == Some("unit")
                {
                    kinds.insert("unit".to_owned());
                }
            }
            for value in object.values() {
                collect_kinds(value, kinds);
            }
        }
        _ => {}
    }
}

fn generated_import_lines(
    declarations: &serde_json::Value,
    callable: &PythonCallable,
) -> Vec<String> {
    let mut facade = BTreeMap::<String, BTreeSet<String>>::new();
    let mut types = BTreeMap::<String, BTreeSet<String>>::new();
    collect_generated_imports(declarations, callable, &mut facade, &mut types);
    let mut lines = Vec::new();
    for (module, names) in facade {
        lines.push(format!(
            "from {module} import {}",
            names.into_iter().collect::<Vec<_>>().join(", ")
        ));
    }
    for (module, names) in types {
        lines.push(format!(
            "from {module}_types import {}",
            names.into_iter().collect::<Vec<_>>().join(", ")
        ));
    }
    lines
}

fn collect_generated_imports(
    declarations: &serde_json::Value,
    callable: &PythonCallable,
    facade: &mut BTreeMap<String, BTreeSet<String>>,
    types: &mut BTreeMap<String, BTreeSet<String>>,
) {
    let Some(modules) = declarations.as_object() else {
        return;
    };
    for (module_key, module) in modules {
        let Some(decls) = module
            .get("declarations")
            .and_then(serde_json::Value::as_array)
        else {
            continue;
        };
        for declaration in decls {
            let Some(kind) = declaration.get("kind").and_then(serde_json::Value::as_str) else {
                continue;
            };
            let Some(name) = declaration.get("name").and_then(serde_json::Value::as_str) else {
                continue;
            };
            let local = name.rsplit('.').next().unwrap_or(name);
            let module = name
                .rsplit_once('.')
                .map(|(module, _)| module)
                .unwrap_or(module_key);
            match kind {
                "function" if name != callable.cott_symbol => {
                    facade
                        .entry(module.to_owned())
                        .or_default()
                        .insert(local.to_owned());
                }
                "impl" => {
                    facade
                        .entry(module.to_owned())
                        .or_default()
                        .insert(local.to_owned());
                }
                "struct" | "enum" | "alias" | "newtype" | "trait" | "external_type" | "const"
                | "resource" | "rule" => {
                    types
                        .entry(module.to_owned())
                        .or_default()
                        .insert(local.to_owned());
                    if kind == "enum" {
                        for variant in declaration
                            .get("variants")
                            .and_then(serde_json::Value::as_array)
                            .into_iter()
                            .flatten()
                        {
                            if let Some(variant) =
                                variant.get("name").and_then(serde_json::Value::as_str)
                            {
                                types
                                    .entry(module.to_owned())
                                    .or_default()
                                    .insert(format!("{local}_{variant}"));
                            }
                        }
                    }
                }
                _ => {}
            }
        }
    }
}

fn factory_import_lines(declarations: &serde_json::Value, callable_module: &str) -> Vec<String> {
    let mut imports = BTreeMap::<String, BTreeSet<String>>::new();
    collect_factory_imports(declarations, callable_module, &mut imports);
    imports
        .into_iter()
        .flat_map(|(module, concretes)| {
            concretes
                .into_iter()
                .map(move |concrete| format!("from {module} import {concrete}"))
        })
        .collect()
}

fn collect_factory_imports(
    value: &serde_json::Value,
    callable_module: &str,
    imports: &mut BTreeMap<String, BTreeSet<String>>,
) {
    let Some(object) = value.as_object() else {
        if let serde_json::Value::Array(values) = value {
            for value in values {
                collect_factory_imports(value, callable_module, imports);
            }
        }
        return;
    };
    if object.get("kind").and_then(serde_json::Value::as_str) == Some("factory") {
        if let Some(instance) = object
            .get("instance")
            .and_then(serde_json::Value::as_object)
        {
            let named = instance.get("kind").and_then(serde_json::Value::as_str) == Some("named")
                && instance
                    .get("args")
                    .and_then(serde_json::Value::as_array)
                    .is_some_and(Vec::is_empty);
            if named {
                if let Some(symbol) = instance.get("name").and_then(serde_json::Value::as_str) {
                    if let Some((facade, concrete)) = symbol.rsplit_once('.') {
                        if facade != callable_module {
                            imports
                                .entry(facade.to_owned())
                                .or_default()
                                .insert(concrete.to_owned());
                        }
                    }
                }
            }
        }
        return;
    }
    for child in object.values() {
        collect_factory_imports(child, callable_module, imports);
    }
}

pub(crate) fn selected_implementation_kind(callable: &PythonCallable) -> Option<&str> {
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
