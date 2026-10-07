use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, OpenOptions};
use std::io::{Read, Seek, SeekFrom, Write};
use std::os::unix::fs::MetadataExt;
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant};

use crate::binding::ResolvedBinding;
use crate::diagnostics::{Diagnostic, Span, code};
use crate::hash::sha256_hex;
use crate::prompt_declarations;
use crate::python::artifact_plan::{PythonCallable, PythonCallableKind};
use crate::sandbox::{
    BindMounts, MappedMount, NetworkAccess, ResourceLimits, SandboxSpec, run_with_mounts,
};
use crate::version::{is_at_least, parse_version};

const MAX_RULE_BYTES: usize = 1024 * 1024;
const MAX_RENDERED_PROMPT_BYTES: usize = 8 * 1024 * 1024;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum AgentKind {
    Codex,
    Omp,
    Claude,
    Pi,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub struct AgentSelection<'a> {
    pub kind: AgentKind,
    pub model: Option<&'a str>,
}

/// Nonempty, equal to its own trim, free of control characters, and not
/// starting with `-` (so it can never be mistaken for a flag). Internal
/// spaces are allowed; the value is passed as a single argv element.
pub fn valid_model(model: &str) -> bool {
    !model.is_empty()
        && model == model.trim()
        && !model.chars().any(|character| character.is_control())
        && !model.starts_with('-')
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AdapterSpec {
    pub executable_name: &'static str,
    pub minimum_version: &'static str,
    pub version_argv: &'static [&'static str],
    pub argv_template: &'static [&'static str],
    pub prompt_on_stdin: bool,
}

/// Codex CLI, run with the caller's own `CODEX_HOME` (`config.toml`,
/// profiles, providers, MCP servers, rules, skills, `AGENTS.md`, login,
/// project trust) and the caller's own sandbox and approval policy: Cott
/// passes no `--sandbox`, `--full-auto` or approval flag, so `sandbox_mode`,
/// `permission_profile` and the trust-dependent defaults of the user's
/// configuration decide whether `codex exec` may write the target, exactly as
/// in a normal run in the project. Cott keeps only what a one-shot
/// non-interactive run needs: `exec` with the prompt on stdin (`-`),
/// `--ephemeral` (no session rollout files), `--skip-git-repo-check` (the
/// isolated workspace presented at the project path is not a checkout),
/// `--color never` and `--cd` (the project path).
pub const CODEX: AdapterSpec = AdapterSpec {
    executable_name: "codex",
    minimum_version: "0.147.0",
    version_argv: &["--version"],
    argv_template: &[
        "exec",
        "--ephemeral",
        "--skip-git-repo-check",
        "--color",
        "never",
        "--cd",
        "<workspace>",
        "-",
    ],
    prompt_on_stdin: true,
};
/// OMP, run with the caller's own agent directory (config, providers,
/// credentials, rules, skills, extensions, LSP, MCP) and the caller's own
/// tool approval policy (`tools.approvalMode`, `tools.approval`): Cott passes
/// no `--approval-mode` or `--auto-approve`. Cott keeps the one-shot print
/// mode, the working directory (`--cwd`, the project path), `--no-session`,
/// `--no-pty` (no terminal in a print run), `--no-title` (no extra
/// session-title model call for a session that is never stored), the
/// wall-clock limit, and the prompt file attachment.
pub const OMP: AdapterSpec = AdapterSpec {
    executable_name: "omp",
    minimum_version: "17.2.12",
    version_argv: &["--version"],
    argv_template: &[
        "-p",
        "--cwd",
        "<workspace>",
        "--no-session",
        "--no-pty",
        "--no-title",
        "--max-time",
        "<seconds>s",
        "@<prompt-file>",
    ],
    prompt_on_stdin: false,
};

/// Claude Code, run without `--bare`, so the caller's settings, login
/// (OAuth or API key), hooks, plugins, MCP servers, skills, agents and
/// `CLAUDE.md` memory load as usual, with the tools those settings allow and
/// the caller's own permission mode and rules: Cott passes no
/// `--permission-mode`, `--allowedTools` or `--dangerously-skip-permissions`,
/// so `permissions.defaultMode` and the allow/deny rules of the user and
/// project settings decide every tool call. A request nothing allows is
/// denied in print mode and reported in the result's `permission_denials`.
/// Cott keeps print mode with text input and JSON output (the completion
/// protocol) and `--no-session-persistence`.
pub const CLAUDE: AdapterSpec = AdapterSpec {
    executable_name: "claude",
    minimum_version: "2.1.89",
    version_argv: &["--version"],
    argv_template: &[
        "--print",
        "--input-format",
        "text",
        "--output-format",
        "json",
        "--no-session-persistence",
    ],
    prompt_on_stdin: true,
};

/// Pi coding agent (`@earendil-works/pi-coding-agent`), run with the caller's
/// own Pi setup: the agent directory (settings, `auth.json`, `models.json`,
/// packages and extensions, skills, prompt templates, themes, context files,
/// MCP servers), Pi's default model resolution and default tools. Only the
/// official Node package entrypoint `dist/bundle/cli.js` is accepted. Cott adds
/// only what its one-shot protocol needs: JSON event output, an in-memory
/// session, and the frozen prompt as the single positional message after `--`.
/// `--model` is inserted only when the caller selects one, verbatim in Pi's own
/// syntax (`provider/id`, a pattern, an optional `:<thinking>` suffix).
pub const PI: AdapterSpec = AdapterSpec {
    executable_name: "pi",
    minimum_version: "1.0.4",
    version_argv: &["--version"],
    argv_template: &["--mode", "json", "--no-session", "--", "<prompt>"],
    prompt_on_stdin: false,
};

/// Pi releases accepted by the adapter: `1.0.4 <= version < 2.0.0`, the 1.x
/// JSON event contract (session header version 3 through `agent_settled`)
/// that [`validate_pi_json_stream`] checks.
pub const PI_UNSUPPORTED_MAJOR: u64 = 2;
/// `engines.node` of the supported Pi package.
pub const PI_MINIMUM_NODE_VERSION: &str = "22.19.0";
/// Caller environment variables an agent generation run does not inherit;
/// everything else (provider keys, proxies, CLI configuration variables,
/// PATH) passes through unchanged. Cott sets `HOME` (the caller's home),
/// `TMPDIR` (the run's writable scratch) and `PWD` (the run's logical working
/// directory, the caller project's path) itself; the shell's previous
/// directory and nesting markers do not describe the sandboxed process. The
/// rest mark a *parent* agent session when cott itself runs inside one, never
/// configuration: `PI_SESSION_*`, `PI_PROVIDER`, `PI_MODEL` and
/// `PI_REASONING_LEVEL` describe a parent Pi session (Pi drops them before it
/// launches tools so nested Pi processes never report stale session
/// metadata), `CLAUDECODE` and `CLAUDE_CODE_ENTRYPOINT` are set by Claude Code
/// for its own tool processes (a nested `claude` refuses to start under
/// `CLAUDECODE`), and `CODEX_SANDBOX*` are set by Codex for the commands it
/// sandboxes.
pub const AGENT_NOT_INHERITED: &[&str] = &[
    "CLAUDECODE",
    "CLAUDE_CODE_ENTRYPOINT",
    "CODEX_SANDBOX",
    "CODEX_SANDBOX_NETWORK_DISABLED",
    "HOME",
    "OLDPWD",
    "PI_MODEL",
    "PI_PROVIDER",
    "PI_REASONING_LEVEL",
    "PI_SESSION_FILE",
    "PI_SESSION_ID",
    "PWD",
    "SHLVL",
    "TMPDIR",
    "_",
];
/// Inherited variables that name certificate or credential files read by the
/// CLIs, Node, or built-in providers; existing absolute paths are mounted
/// read-only.
const AGENT_FILE_VARIABLES: &[&str] = &[
    "ANTHROPIC_IDENTITY_TOKEN_FILE",
    "AWS_CONFIG_FILE",
    "AWS_SHARED_CREDENTIALS_FILE",
    "AWS_WEB_IDENTITY_TOKEN_FILE",
    "CODEX_CA_CERTIFICATE",
    "GOOGLE_APPLICATION_CREDENTIALS",
    "NODE_EXTRA_CA_CERTS",
    "REQUESTS_CA_BUNDLE",
    "SSL_CERT_DIR",
    "SSL_CERT_FILE",
];
const PI_EVENT_TYPES: &[&str] = &[
    "agent_start",
    "agent_end",
    "turn_start",
    "turn_end",
    "message_start",
    "message_update",
    "message_end",
    "tool_execution_start",
    "tool_execution_update",
    "tool_execution_end",
    "agent_settled",
    "queue_update",
    "compaction_start",
    "compaction_end",
    "entry_appended",
    "session_info_changed",
    "thinking_level_changed",
    "auto_retry_start",
    "auto_retry_end",
    "summarization_retry_scheduled",
    "summarization_retry_attempt_start",
    "summarization_retry_finished",
];
/// Terminal `stopReason` values of a completed assistant message.
const PI_STOP_REASONS: &[&str] = &["stop", "length", "toolUse", "error", "aborted", "deferred"];

/// Linux `MAX_ARG_STRLEN` is 32 pages including the terminating NUL: the
/// largest prompt that one argv element can carry without modification on
/// this host (131071 bytes with 4 KiB pages).
pub fn pi_max_prompt_bytes() -> usize {
    // SAFETY: sysconf has no preconditions.
    let page = unsafe { libc::sysconf(libc::_SC_PAGESIZE) };
    let page = usize::try_from(page)
        .ok()
        .filter(|page| *page > 0)
        .unwrap_or(4096);
    32 * page - 1
}

/// What a validated Pi JSON event stream reports about the model that answered.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PiStreamSummary {
    /// Distinct `provider/model` attributions of the session's assistant
    /// messages, in order of first use.
    pub models: Vec<String>,
    /// The `provider/model` of the final assistant message.
    pub final_model: String,
}

pub fn adapter(kind: AgentKind) -> &'static AdapterSpec {
    match kind {
        AgentKind::Codex => &CODEX,
        AgentKind::Omp => &OMP,
        AgentKind::Claude => &CLAUDE,
        AgentKind::Pi => &PI,
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
    pub argv_template: Vec<String>,
    /// For Pi, the `provider/model` attributions its JSON event stream reported
    /// (see [`PiStreamSummary::models`]); empty for the other adapters.
    pub resolved_models: Vec<String>,
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
    prompt.push_str(&crate::requirements::render_prompt_requirements(
        declarations,
    ));
    prompt.push_str("\nFORMAL DECLARATIONS\n");
    prompt.push_str(prompt_declarations::FORMAT);
    prompt.push_str(&prompt_declarations::render_scoped_declarations(
        declarations,
    )?);
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
    if prompt.len() > MAX_RENDERED_PROMPT_BYTES {
        return Err("rendered agent prompt exceeds 8 MiB".to_owned());
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
    opaque: bool,
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
    prompt.push_str("Use the Python ABI projections of the canonical types, not the raw IR type names. Numeric annotations are case-sensitive cott_runtime imports: I8, I16, I32, I64, U8, U16, U32, U64, F32, F64. For example, canonical primitive i32 means `from cott_runtime import I32` and a Python annotation of `I32`; lowercase `i32` is not a runtime export. These aliases are annotations and MUST NOT be called. Numeric ABI aliases are plain int/float at runtime: use ordinary arithmetic and comparisons and return the result directly, never call or construct a numeric alias. Never replace width-specific annotations or returned contract containers with Python primitives or built-in list/set/dict.\n");
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
        prompt.push_str("Construct result values only with top-level `cott_runtime.Ok(value=...)`/`cott_runtime.Err(error=...)`, never `Result.Ok`/`Result.Err`. Both constructors are keyword-only: never pass their payload positionally. Never spell Result as an Ok/Err union. Return `Ok(value=UNIT)` for Result[Unit, E].\n");
    }
    if features.unit {
        prompt.push_str("`Unit` is the annotation and `UNIT` is its only value.\n");
    }
    if features.option {
        prompt.push_str("For Option annotations use the top-level `Some(value=...)` and `Nothing()` variants, never `Option.Some` or `Option.Nothing`.\n");
    }
    if features.opaque {
        prompt.push_str("`Opaque[\"tag\"]` maps to `cott_runtime.Opaque[typing.Literal[\"tag\"]]`. Construct it with keyword arguments `Opaque(tag=\"tag\", value=payload)`. Its public `.tag` is a string; `.unwrap()` returns the exact stored payload as `object` (also available as `.value`), without cloning it. Validate and narrow that object using the declared payload contract before use. There is no `.payload` field or reflective accessor. Opaque tags are type labels, not cryptographic ownership seals.\n");
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
        prompt.push_str("Scenario fixtures and steps are runner-owned. Scenario calls are facade-only: invoke the exact generated public facade, never a private `_cott_impl` implementation or `cott_bindings` module. The only private runtime effect adapters are `cott_runtime._cott_fixture_read`, `cott_runtime._cott_fixture_write`, `cott_runtime._cott_fixture_replace`, `cott_runtime._cott_fixture_remove`, `cott_runtime._cott_fixture_http`, `cott_runtime._cott_fixture_now`, `cott_runtime._cott_fixture_shuffle`, and `cott_runtime._cott_fixture_database`. They MAY be used only when the contract is targeted by a compatible declared scenario, and they act only inside that scenario's active compiler-owned fixture. Otherwise, an effectful callable MUST NOT invent an adapter name or authority. Do not emulate a fixture effect with stdlib I/O: never reach fixture files through standard-library file access. Do not inspect adapter internals, dynamically import an adapter, or retain an adapter value.\n");
        prompt.push_str("Fixture filesystem adapters accept a relative pathlib.Path or str inside the fixture root. `_cott_fixture_read(path)` and `_cott_fixture_http(url)` return bytes; `_cott_fixture_write(path, data)` and `_cott_fixture_replace(path, data)` require bytes, so encode/decode text explicitly using the contract's encoding. `_cott_fixture_now()` returns the configured clock fixture's start_ms value in milliseconds; convert explicitly if the callable contract returns another unit, such as nanoseconds. `_cott_fixture_shuffle(values)` shuffles an ordinary Python `list` in place with the declared random fixture's scenario-private seeded generator and returns None; copy an immutable Cott collection into a `list` first, and never seed, reseed, or read the global `random` module state. No fixture adapter supplies authority outside an active compiler-owned fixture.\n");
        prompt.push_str("Outside an active fixture every adapter raises `CottContractViolation` whose `.message` is exactly `\"fixture adapters are inactive\"` before inspecting its arguments, and has no other effect; compare `.message`, not `str(error)`, which appends ` [phase=fixture]`. Inside an active fixture, a real file-system error from `_cott_fixture_read`, `_cott_fixture_write`, or `_cott_fixture_replace` raises `CottContractViolation` whose `__cause__` is the original `OSError`, for example `FileNotFoundError` for a missing file or `PermissionError` for denied access. A scenario-injected failure uses the configured closed label: `permission_denied` raises `PermissionError` (EACCES), `not_found` raises `FileNotFoundError` (ENOENT), `disk_full` raises `OSError` (ENOSPC), `timeout` raises `TimeoutError` (ETIMEDOUT), and `connection_reset` raises `ConnectionResetError` (ECONNRESET). It fires once at the configured occurrence: directly at the `file.open`, `file.read`, and `file.write` points, and as the `__cause__` of such a `CottContractViolation` at the `file.flush` and `file.replace` points; handle both forms wherever the contract maps I/O failures. An unsafe path, non-bytes data, or invalid parent policy raises `CottContractViolation` without a `__cause__`. `_cott_fixture_write` creates missing parent directories. `_cott_fixture_replace(path, data, *, create_parents=True)` uses descriptor-relative no-follow directory traversal, refuses symlink components and existing nonregular leaves, writes an exclusive mode-0600 same-directory temporary file, flushes and fsyncs it, atomically replaces the target, then fsyncs the parent directory. Set `create_parents=False` when the contract forbids creating parents: a missing parent fails without creating it. Precommit failure cleans up only the temporary file created by this call and preserves the prior target; a parent-fsync error after replacement reports failure but leaves the new target in place. Unsupported safety primitives fail closed. These guarantees apply inside the fixture; do not implement them with direct fixture filesystem access.\n");
        prompt.push_str("`_cott_fixture_remove(path)` removes one existing file inside the fixture root and returns None; it does not remove directories or create parents. A missing file raises `CottContractViolation` with a `FileNotFoundError` cause, not silent success. Removal visits the existing `file.write` failure point before changing the filesystem; an injected failure leaves the file unchanged. Actual unlink errors are wrapped with their original `OSError` cause. It uses the same inactive-adapter and path-confinement rules as the other filesystem adapters.\n");
        prompt.push_str("When this scenario-targeted contract also says a path is read or written on the host file system outside a Cott scenario, call the fixture adapter first and select host standard-library I/O only when that call raises the inactive-adapter violation; that probe is the only permitted adapter call outside an active fixture, and the adapter grants no authority there. Every other adapter outcome, including an I/O failure, belongs to the active fixture: map it as the contract requires and never retry it through the host file system.\n");
        prompt.push_str("Likewise, when this scenario-targeted contract declares the `random` effect and requires a shuffle, call `_cott_fixture_shuffle` first and use standard-library `random.shuffle` on the same list only when that call raises the inactive-adapter violation; every other adapter outcome belongs to the active fixture and MUST NOT fall back to standard-library randomness.\n");
        prompt.push_str("For scenario-targeted database operations, call `_cott_fixture_database(operation)` inside the operation's normal error-handling boundary immediately before the real SDK operation. The exact operation is one of `connect`, `read`, `write`, `commit`, `rollback`, `close`, or `cancel`. The adapter requires active database fixture authority, records the reached boundary, and may raise a configured OSError at `database.<operation>`; map that error to the callable's declared error just as a driver failure. Only the exact inactive-adapter violation permits normal host SDK execution outside a scenario. With active authority and no injected failure, continue through the actual SDK and keep genuine facade-created connections/cursors; the adapter does not provide or emulate a driver, return data, or manufacture Opaque handles. A recorded boundary is not evidence that the SDK operation succeeded.\n");
        prompt.push_str("A database `interrupted` failure delivers real SIGINT to the isolated runner's main thread, so keep `_cott_fixture_database` inside the same KeyboardInterrupt handling that the contract requires. Use one boundary call for the callable's logical database operation; do not double-instrument its internal SDK substeps. It is never permission to synthesize a database result or driver object.\n");
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
            | "requirement"
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
        opaque: kinds.contains("opaque"),
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

fn insert_model_argument(
    kind: AgentKind,
    mut arguments: Vec<String>,
    model: Option<&str>,
) -> Vec<String> {
    let Some(model) = model else {
        return arguments;
    };
    let index = match kind {
        AgentKind::Codex => 1,
        AgentKind::Omp | AgentKind::Claude | AgentKind::Pi => 0,
    };
    arguments.splice(index..index, [String::from("--model"), model.to_owned()]);
    arguments
}

/// [`run_agent_in_project`] without a caller project: only the caller's user
/// configuration is presented to the CLI, whose working directory is the
/// isolated workspace's own path.
pub fn run_agent(
    selection: AgentSelection,
    executable: PathBuf,
    workspace: &Path,
    scratch: &Path,
    target: &Path,
    prompt: Vec<u8>,
    timeout_seconds: u16,
) -> Result<AgentRunCandidate, String> {
    run_agent_in_project(
        selection,
        None,
        executable,
        workspace,
        scratch,
        target,
        prompt,
        timeout_seconds,
    )
}

/// Run the selected CLI once in the isolated `workspace` with the caller's
/// own configuration ([`user_environment`]) and, when `project` names the
/// caller's Cott project, inside the sandbox at that project's own path: the
/// read-only workspace (with the writable target) is presented at the project
/// root path, which is the CLI's working directory, with the project's
/// [`PROJECT_RESOURCES`], the context and configuration of its ancestors
/// ([`ANCESTOR_RESOURCES`]) and its repository root marker read-only. The
/// project's own files are never visible or writable.
#[allow(clippy::too_many_arguments)]
pub fn run_agent_in_project(
    selection: AgentSelection,
    project: Option<&Path>,
    executable: PathBuf,
    workspace: &Path,
    scratch: &Path,
    target: &Path,
    prompt: Vec<u8>,
    timeout_seconds: u16,
) -> Result<AgentRunCandidate, String> {
    if let Some(model) = selection.model {
        if !valid_model(model) {
            return Err(format!("invalid agent model `{model}`"));
        }
    }
    let kind = selection.kind;
    // The Pi prompt must fit one argv element unmodified; this is checked
    // before any external command runs.
    let pi_prompt = if kind == AgentKind::Pi {
        Some(pi_prompt_argument(&prompt)?)
    } else {
        None
    };
    let scratch = fs::canonicalize(scratch)
        .map_err(|error| format!("resolve agent scratch {}: {error}", scratch.display()))?;
    let spec = adapter(kind);
    let executable = fs::canonicalize(&executable)
        .map_err(|error| format!("resolve {} executable: {error}", spec.executable_name))?;
    let metadata = fs::symlink_metadata(&executable)
        .map_err(|error| format!("stat {} executable: {error}", spec.executable_name))?;
    if !metadata.is_file() || metadata.file_type().is_symlink() {
        return Err(format!(
            "{} executable must be a regular file",
            spec.executable_name
        ));
    }
    let executable_bytes = fs::read(&executable)
        .map_err(|error| format!("read {} executable: {error}", spec.executable_name))?;
    if kind == AgentKind::Claude && !native_claude_entrypoint(&executable, &executable_bytes) {
        return Err("claude executable must use the official native entrypoint".to_owned());
    }
    let (runtime, pi_package_version) = if kind == AgentKind::Pi {
        let (runtime, version) = pi_node_runtime(&executable, &executable_bytes)?;
        probe_pi_node(&runtime, workspace, &scratch, timeout_seconds)?;
        (Some(runtime), Some(version))
    } else {
        (omp_bun_runtime(kind, &executable, &executable_bytes)?, None)
    };
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
    // The caller's own CLI setup, resolved before the workspace snapshot
    // because everything mounted below the project path needs a mount point
    // in the workspace the sandbox presents there. Only the generation run
    // uses it; the probes stay offline and isolated.
    let environment = user_environment(kind, &scratch, workspace, project)?;
    let mut runtime_paths = vec![executable.clone(), scratch.clone()];
    if let Some(runtime) = &runtime {
        runtime_paths.push(runtime.executable.clone());
        runtime_paths.extend(runtime.read_only.iter().cloned());
    }
    environment.prepare_mount_points(workspace, &target_relative, &runtime_paths)?;
    let workspace_before = workspace_snapshot(workspace, Some(&target_relative))?;
    let version = run_process(
        &executable,
        runtime.as_ref(),
        spec.version_argv.iter().map(ToString::to_string).collect(),
        workspace,
        &scratch,
        Vec::new(),
        Launch::Probe(kind),
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
            closed_version_token(&version.stdout)
                .filter(|version| is_at_least(version, minimum_version))
        }
        AgentKind::Claude => None,
        // The probe must agree with the package metadata of the mounted entrypoint.
        AgentKind::Pi if !version.timed_out && version.status == Some(0) => {
            closed_version_token(&version.stdout)
                .filter(|version| Some(*version) == pi_package_version.as_deref())
                .filter(|version| is_at_least(version, minimum_version))
                .filter(|version| {
                    parse_version(version).is_some_and(|(major, _, _)| major < PI_UNSUPPORTED_MAJOR)
                })
        }
        AgentKind::Pi => None,
    };
    let Some(adapter_version) = adapter_version else {
        return Err(format!(
            "unsupported {} version `{version_text}` (exit {:?}): {}",
            spec.executable_name,
            version.status,
            String::from_utf8_lossy(&version.stderr).trim()
        ));
    };
    // The CLI's working directory: the caller project's path (where the
    // sandbox presents the workspace), else the workspace itself.
    let cwd = environment
        .cwd
        .to_str()
        .ok_or("agent working directory is not UTF-8")?;
    let arguments = match kind {
        AgentKind::Codex => vec![
            "exec",
            "--ephemeral",
            "--skip-git-repo-check",
            "--color",
            "never",
            "--cd",
            cwd,
            "-",
        ]
        .into_iter()
        .map(str::to_owned)
        .collect(),
        AgentKind::Omp => {
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
                cwd.to_owned(),
                "--no-session".to_owned(),
                "--no-pty".to_owned(),
                "--no-title".to_owned(),
                "--max-time".to_owned(),
                format!("{timeout_seconds}s"),
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
        AgentKind::Pi => {
            let prompt_text = pi_prompt.expect("the Pi prompt was validated");
            let mut arguments = PI.argv_template[..PI.argv_template.len() - 1]
                .iter()
                .map(ToString::to_string)
                .collect::<Vec<_>>();
            arguments.push(prompt_text.to_owned());
            arguments
        }
    };
    let arguments = insert_model_argument(kind, arguments, selection.model);
    let stdin = if spec.prompt_on_stdin {
        prompt.clone()
    } else {
        Vec::new()
    };
    let started = Instant::now();
    let completed = run_process(
        &executable,
        runtime.as_ref(),
        arguments,
        workspace,
        &scratch,
        stdin,
        Launch::Generation(kind, &environment),
        Some(target),
        timeout_seconds,
    )?;
    let duration_ms = started.elapsed().as_millis().min(u128::from(u64::MAX)) as u64;
    if let Some(runtime) = &runtime {
        runtime.verify()?;
    }
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
    let pi_summary = match pi_prompt {
        Some(prompt_text) => {
            // Pi reports its working directory: the project path the sandbox
            // presents, or the workspace path (possibly canonicalized).
            let canonical_workspace = fs::canonicalize(workspace).unwrap_or_default();
            let cwds: Vec<&Path> = if environment.cwd == workspace {
                vec![workspace, &canonical_workspace]
            } else {
                vec![&environment.cwd]
            };
            let summary = validate_pi_json_stream(&completed.stdout, &cwds, prompt_text).map_err(
                |reason| {
                    format!(
                        "pi JSON event stream rejected: {reason}{}",
                        stderr_excerpt(&completed.stderr)
                    )
                },
            )?;
            Some(summary)
        }
        None => None,
    };
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
        let stdout = if kind == AgentKind::Pi {
            format!("<{} bytes of Pi JSON events>", completed.stdout.len())
        } else {
            String::from_utf8_lossy(&completed.stdout).trim().to_owned()
        };
        return Err(format!(
            "agent did not write target {}{}\nprovider stdout:\n{}\nprovider stderr:\n{}",
            target.display(),
            local_policy_note(kind, &completed.stdout),
            stdout,
            String::from_utf8_lossy(&completed.stderr).trim(),
        ));
    }
    while implementation.last() == Some(&b'\n') {
        implementation.pop();
    }
    implementation.push(b'\n');
    let argv_template = insert_model_argument(
        kind,
        spec.argv_template.iter().map(ToString::to_string).collect(),
        selection.model,
    );
    let resolved_models = match (kind, pi_summary) {
        (AgentKind::Pi, Some(summary)) => summary.models,
        (AgentKind::Claude, _) => claude_models(&completed.stdout),
        _ => Vec::new(),
    };
    if !resolved_models.is_empty() {
        // AgentRun has no model field; the attribution the CLI reported is
        // shown here and bound to the record through the stdout digest.
        eprintln!(
            "{} answered with {}",
            spec.executable_name,
            resolved_models
                .iter()
                .map(|model| format!("`{model}`"))
                .collect::<Vec<_>>()
                .join(", ")
        );
    }
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
        environment_names: agent_environment_names(),
        argv_template,
        resolved_models,
    })
}

/// The tail of a failed run's stderr, appended to a rejection so the cause
/// (provider, authentication, network, extension) is visible.
fn stderr_excerpt(stderr: &[u8]) -> String {
    const LIMIT: usize = 4000;
    let text = String::from_utf8_lossy(stderr);
    let text = text.trim();
    if text.is_empty() {
        return String::new();
    }
    let mut start = text.len().saturating_sub(LIMIT);
    while !text.is_char_boundary(start) {
        start += 1;
    }
    format!("\npi stderr:\n{}", &text[start..])
}

/// An interpreter-hosted agent entrypoint: OMP under Bun or Pi under Node.
struct ScriptRuntime {
    label: &'static str,
    executable: PathBuf,
    digest: [u8; 32],
    read_only: Vec<PathBuf>,
}

impl ScriptRuntime {
    fn verify(&self) -> Result<(), String> {
        if runtime_digest(&self.executable, self.label)? != self.digest {
            return Err(format!("{} changed during generation", self.label));
        }
        Ok(())
    }
}

fn runtime_digest(executable: &Path, label: &str) -> Result<[u8; 32], String> {
    use sha2::{Digest, Sha256};

    let metadata =
        fs::symlink_metadata(executable).map_err(|error| format!("stat {label}: {error}"))?;
    if !metadata.is_file() || metadata.mode() & 0o111 == 0 {
        return Err(format!("{label} must be a regular executable file"));
    }
    let mut file = fs::File::open(executable).map_err(|error| format!("open {label}: {error}"))?;
    let mut digest = Sha256::new();
    let mut buffer = [0u8; 64 * 1024];
    loop {
        let count = file
            .read(&mut buffer)
            .map_err(|error| format!("read {label}: {error}"))?;
        if count == 0 {
            break;
        }
        digest.update(&buffer[..count]);
    }
    Ok(digest.finalize().into())
}

/// First `name` entry on the caller's PATH, canonicalized.
fn path_runtime(name: &str, label: &str) -> Result<PathBuf, String> {
    let path =
        std::env::var_os("PATH").ok_or_else(|| format!("missing PATH while locating {label}"))?;
    for directory in std::env::split_paths(&path) {
        let candidate = directory.join(name);
        match fs::symlink_metadata(&candidate) {
            Ok(_) => {
                return fs::canonicalize(&candidate)
                    .map_err(|error| format!("resolve {label}: {error}"));
            }
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {}
            Err(error) => return Err(format!("locate {label}: {error}")),
        }
    }
    Err(format!("missing {label} on PATH"))
}

/// Resolve the official Pi Node package around its canonical entrypoint and
/// the Node runtime from PATH. Returns the runtime and the package version.
/// The runtime mounts the installed Pi package with its dependency closure
/// (extensions resolve and load Pi's own packages, such as `pi-ai`, from it)
/// and the Node installation the caller's PATH selects.
fn pi_node_runtime(executable: &Path, bytes: &[u8]) -> Result<(ScriptRuntime, String), String> {
    let shebang = bytes
        .split(|byte| *byte == b'\n')
        .next()
        .unwrap_or_default();
    if shebang != b"#!/usr/bin/env node" {
        return Err(
            "pi executable must be the official Node package entrypoint dist/bundle/cli.js (`#!/usr/bin/env node`); compiled, Bun, or wrapper launchers are unsupported"
                .to_owned(),
        );
    }
    let root = executable
        .ancestors()
        .nth(3)
        .filter(|root| {
            executable.ends_with("dist/bundle/cli.js")
                && root.ends_with("node_modules/@earendil-works/pi-coding-agent")
        })
        .ok_or(
            "pi entrypoint must be node_modules/@earendil-works/pi-coding-agent/dist/bundle/cli.js of an installed package",
        )?;
    let metadata = package_metadata(root, "Pi package")?;
    if metadata["name"].as_str() != Some("@earendil-works/pi-coding-agent")
        || metadata["bin"]["pi"].as_str() != Some("dist/bundle/cli.js")
    {
        return Err("pi script does not match the official package entrypoint".to_owned());
    }
    let version = metadata["version"]
        .as_str()
        .filter(|version| closed_semver(version))
        .ok_or("Pi package must declare a release version")?
        .to_owned();
    let modules = root
        .ancestors()
        .filter(|path| path.file_name().is_some_and(|name| name == "node_modules"))
        .last()
        .ok_or("pi entrypoint must belong to an installed node_modules package")?;
    let mut read_only =
        package_closure_mounts(root, modules, "@earendil-works/pi-coding-agent", "Pi")?;
    let label = "Pi Node runtime";
    let node = path_runtime("node", label)?;
    let digest = runtime_digest(&node, label)?;
    read_only.extend(node_installation(&node));
    Ok((
        ScriptRuntime {
            label,
            executable: node,
            digest,
            read_only,
        },
        version,
    ))
}

/// The installation prefix of a canonical `<prefix>/bin/node` from a Node
/// distribution (nvm, official tarballs, version managers), so that `node`,
/// `npm` and `npx` run by Pi, its extensions and its tools resolve exactly as
/// on the caller's PATH. System prefixes are already mounted; anything that
/// does not look like a Node distribution keeps only the binary itself.
fn node_installation(node: &Path) -> Option<PathBuf> {
    let bin = node.parent()?;
    let prefix = bin.parent()?;
    let home = std::env::var_os("HOME").map(PathBuf::from);
    (bin.file_name()? == "bin"
        && !matches!(prefix.to_str(), Some("/" | "/usr" | "/usr/local"))
        && home.as_deref().is_none_or(|home| !home.starts_with(prefix))
        && (prefix.join("include/node").is_dir() || prefix.join("lib/node_modules").is_dir()))
    .then(|| prefix.to_path_buf())
}

/// `node --version` without network or credentials must report a release at
/// or above the Pi package's `engines.node`.
fn probe_pi_node(
    runtime: &ScriptRuntime,
    workspace: &Path,
    scratch: &Path,
    timeout_seconds: u16,
) -> Result<(), String> {
    let probe = run_process(
        &runtime.executable,
        None,
        vec!["--version".to_owned()],
        workspace,
        scratch,
        Vec::new(),
        Launch::Probe(AgentKind::Pi),
        None,
        timeout_seconds,
    )?;
    runtime.verify()?;
    let minimum =
        parse_version(PI_MINIMUM_NODE_VERSION).expect("the Node minimum is a complete version");
    let reported = std::str::from_utf8(&probe.stdout)
        .ok()
        .filter(|stdout| stdout.split_ascii_whitespace().count() == 1)
        .map(str::trim)
        .unwrap_or_default();
    if probe.timed_out
        || probe.status != Some(0)
        || !reported
            .strip_prefix('v')
            .is_some_and(|version| closed_semver(version) && is_at_least(version, minimum))
    {
        return Err(format!(
            "pi requires Node >= {PI_MINIMUM_NODE_VERSION}; `node --version` reported `{}` (exit {:?})",
            String::from_utf8_lossy(&probe.stdout).trim(),
            probe.status
        ));
    }
    Ok(())
}

/// The prompt is Pi's single positional message after `--`. Pi passes such a
/// message to the model unmodified, so anything an argv element cannot carry
/// exactly, or that Pi would parse as a file argument (`@`) or command (`/`),
/// fails instead of being altered.
fn pi_prompt_argument(prompt: &[u8]) -> Result<&str, String> {
    let limit = pi_max_prompt_bytes();
    if prompt.len() > limit {
        return Err(format!(
            "pi prompt is {} bytes; one Linux argv element (MAX_ARG_STRLEN, 32 pages) carries at most {limit} bytes on this host, so `--agent pi` cannot deliver it unmodified",
            prompt.len()
        ));
    }
    if prompt.contains(&0) {
        return Err("pi prompt contains a NUL byte, which an argv element cannot carry".to_owned());
    }
    let text = std::str::from_utf8(prompt).map_err(|_| "pi prompt is not valid UTF-8")?;
    if text.is_empty() || text.starts_with('@') || text.starts_with('/') {
        return Err(
            "pi prompt must be nonempty and must not start with `@` or `/`, which Pi parses as a file argument or command"
                .to_owned(),
        );
    }
    Ok(text)
}

/// Validate Pi 1.x `--mode json` stdout: strict LF-framed JSONL whose first
/// record is the version 3 session header for the isolated workspace and
/// whose last record is `agent_settled`, with only documented event types,
/// balanced agent runs, a final `agent_end` that schedules no retry, no failed
/// automatic retry, a first user message equal to the exact prompt, every
/// assistant message attributed to a provider and model with a terminal
/// `stopReason`, and a final assistant message stopped normally. The
/// attribution is whatever the caller's Pi resolved (its default model, a
/// pattern, an extension provider) and is returned rather than compared with
/// a requested name. Tools are not restricted: the caller's Pi setup decides
/// which tools exist. Event order inside a run is not constrained beyond
/// that, so multi-turn tool use and extension follow-up messages are accepted.
pub fn validate_pi_json_stream(
    stdout: &[u8],
    workspaces: &[&Path],
    prompt: &str,
) -> Result<PiStreamSummary, String> {
    use serde_json::Value;

    let text = std::str::from_utf8(stdout).map_err(|_| "stdout is not UTF-8")?;
    let Some(body) = text.strip_suffix('\n') else {
        return Err("stdout does not end with a complete JSONL record".to_owned());
    };
    let mut records = Vec::new();
    for (index, line) in body.split('\n').enumerate() {
        let line_number = index + 1;
        let line = line.strip_suffix('\r').unwrap_or(line);
        let Ok(Value::Object(record)) = serde_json::from_str::<Value>(line) else {
            return Err(format!("line {line_number} is not a JSON object"));
        };
        if !record.get("type").is_some_and(Value::is_string) {
            return Err(format!("line {line_number} has no string `type`"));
        }
        records.push((line_number, record));
    }
    let kind = |record: &serde_json::Map<String, Value>| {
        record
            .get("type")
            .and_then(Value::as_str)
            .unwrap_or_default()
            .to_owned()
    };
    let (_, header) = &records[0];
    if kind(header) != "session"
        || header.get("version").and_then(Value::as_u64) != Some(3)
        || !header.get("id").is_some_and(Value::is_string)
    {
        return Err("first record is not a version 3 session header".to_owned());
    }
    if !header
        .get("cwd")
        .and_then(Value::as_str)
        .is_some_and(|cwd| {
            workspaces
                .iter()
                .any(|workspace| Path::new(cwd) == *workspace)
        })
    {
        return Err("session header cwd is not the isolated workspace".to_owned());
    }
    if kind(&records[records.len() - 1].1) != "agent_settled" {
        return Err("stream does not end with `agent_settled`".to_owned());
    }
    let mut agent_runs = 0usize;
    let mut open_runs = 0usize;
    let mut final_will_retry = None;
    let mut user_messages = 0usize;
    let mut models = Vec::<String>::new();
    let mut final_assistant = None::<(String, Option<String>, String)>;
    for (line_number, record) in &records[1..] {
        let event = kind(record);
        match event.as_str() {
            "session" => return Err(format!("line {line_number} repeats the session header")),
            "agent_start" => {
                agent_runs += 1;
                open_runs += 1;
            }
            "agent_end" => {
                open_runs = open_runs
                    .checked_sub(1)
                    .ok_or_else(|| format!("line {line_number} ends an agent run never started"))?;
                final_will_retry = Some(
                    record
                        .get("willRetry")
                        .and_then(Value::as_bool)
                        .ok_or_else(|| format!("line {line_number} agent_end lacks `willRetry`"))?,
                );
            }
            "agent_settled" if *line_number != records[records.len() - 1].0 => {
                return Err(format!("line {line_number} settles before the stream ends"));
            }
            "auto_retry_end" if record.get("success").and_then(Value::as_bool) == Some(false) => {
                return Err(format!(
                    "line {line_number} reports a failed automatic retry{}",
                    pi_error_suffix(record.get("finalError"))
                ));
            }
            "message_end" => {
                let message = record
                    .get("message")
                    .and_then(Value::as_object)
                    .ok_or_else(|| format!("line {line_number} message_end lacks a message"))?;
                match message.get("role").and_then(Value::as_str) {
                    Some("user") => {
                        user_messages += 1;
                        // Only the first user message is cott's prompt; later
                        // ones are follow-ups sent by the caller's extensions.
                        let exact = match message.get("content") {
                            Some(Value::String(content)) => content == prompt,
                            Some(Value::Array(blocks)) => {
                                blocks.len() == 1
                                    && blocks[0].get("type").and_then(Value::as_str) == Some("text")
                                    && blocks[0].get("text").and_then(Value::as_str) == Some(prompt)
                            }
                            _ => false,
                        };
                        if user_messages == 1 && !exact {
                            return Err(format!(
                                "line {line_number} first user message differs from the exact prompt (an input transform or file expansion changed it)"
                            ));
                        }
                    }
                    Some("assistant") => {
                        let attribution = |field: &str| {
                            message
                                .get(field)
                                .and_then(Value::as_str)
                                .filter(|value| !value.trim().is_empty())
                                .ok_or_else(|| {
                                    format!("line {line_number} assistant message has no `{field}`")
                                })
                        };
                        let model =
                            format!("{}/{}", attribution("provider")?, attribution("model")?);
                        let stop_reason = message
                            .get("stopReason")
                            .and_then(Value::as_str)
                            .filter(|reason| PI_STOP_REASONS.contains(reason))
                            .ok_or_else(|| {
                                format!(
                                    "line {line_number} assistant message has no valid `stopReason`"
                                )
                            })?;
                        if !models.contains(&model) {
                            models.push(model.clone());
                        }
                        final_assistant = Some((
                            stop_reason.to_owned(),
                            message
                                .get("errorMessage")
                                .map(|error| pi_error_suffix(Some(error))),
                            model,
                        ));
                    }
                    _ => {}
                }
            }
            "tool_execution_start" | "tool_execution_update" | "tool_execution_end" => {
                if !record.get("toolName").is_some_and(Value::is_string) {
                    return Err(format!("line {line_number} tool event lacks `toolName`"));
                }
            }
            other if PI_EVENT_TYPES.contains(&other) => {}
            other => {
                return Err(format!(
                    "line {line_number} has unsupported event `{other}`"
                ));
            }
        }
    }
    if agent_runs == 0 || open_runs != 0 {
        return Err("agent runs are missing or unbalanced".to_owned());
    }
    if final_will_retry != Some(false) {
        return Err("final agent_end still schedules a retry".to_owned());
    }
    if user_messages == 0 {
        return Err("no user message carries the prompt".to_owned());
    }
    match final_assistant {
        Some((reason, _, final_model)) if reason == "stop" => Ok(PiStreamSummary {
            models,
            final_model,
        }),
        Some((reason, error, model)) => Err(format!(
            "final assistant message from `{model}` stopped with `{reason}`{}",
            error.unwrap_or_default()
        )),
        None => Err("no assistant message".to_owned()),
    }
}

/// `: <message>` for a Pi error string, flattened to one line and capped at
/// 300 characters; empty when there is none.
fn pi_error_suffix(error: Option<&serde_json::Value>) -> String {
    let Some(error) = error.and_then(serde_json::Value::as_str) else {
        return String::new();
    };
    let flat = error
        .chars()
        .map(|character| {
            if character.is_control() {
                ' '
            } else {
                character
            }
        })
        .collect::<String>();
    let flat = flat.trim();
    if flat.is_empty() {
        return String::new();
    }
    match flat.char_indices().nth(300) {
        Some((index, _)) => format!(": {}…", &flat[..index]),
        None => format!(": {flat}"),
    }
}

fn omp_bun_runtime(
    kind: AgentKind,
    executable: &Path,
    bytes: &[u8],
) -> Result<Option<ScriptRuntime>, String> {
    if kind != AgentKind::Omp {
        return Ok(None);
    }
    let shebang = bytes
        .split(|byte| *byte == b'\n')
        .next()
        .unwrap_or_default();
    if shebang != b"#!/usr/bin/env bun" {
        if executable
            .extension()
            .is_some_and(|extension| extension == "js")
            || shebang
                .split(|byte| byte.is_ascii_whitespace())
                .any(|word| word == b"bun" || word.ends_with(b"/bun"))
        {
            return Err(
                "unsupported OMP script entrypoint; expected #!/usr/bin/env bun".to_owned(),
            );
        }
        return Ok(None);
    }
    let label = "OMP Bun runtime";
    let bun = path_runtime("bun", label)?;
    let digest = runtime_digest(&bun, label)?;
    let read_only = omp_package_mounts(executable)?;
    Ok(Some(ScriptRuntime {
        label,
        executable: bun,
        digest,
        read_only,
    }))
}

fn package_metadata(root: &Path, label: &str) -> Result<serde_json::Value, String> {
    let path = root.join("package.json");
    let metadata = fs::symlink_metadata(&path)
        .map_err(|error| format!("inspect {label} {}: {error}", path.display()))?;
    if !metadata.is_file() || metadata.len() > 1024 * 1024 {
        return Err(format!("unsafe {label} metadata {}", path.display()));
    }
    serde_json::from_slice(
        &fs::read(&path).map_err(|error| format!("read {label} {}: {error}", path.display()))?,
    )
    .map_err(|error| format!("parse {label} {}: {error}", path.display()))
}

fn package_name(name: &str) -> bool {
    let valid_part = |part: &str| {
        !part.is_empty()
            && !part.starts_with('.')
            && part
                .bytes()
                .all(|byte| byte.is_ascii_alphanumeric() || b"-_.".contains(&byte))
    };
    match name.split_once('/') {
        Some((scope, name)) => scope.strip_prefix('@').is_some_and(valid_part) && valid_part(name),
        None => valid_part(name),
    }
}

fn omp_package_mounts(executable: &Path) -> Result<Vec<PathBuf>, String> {
    // Only installed node_modules packages qualify. A linked checkout or an
    // arbitrary directory with a fabricated package.json is not a runtime root.
    let modules = executable
        .ancestors()
        .filter(|path| path.file_name().is_some_and(|name| name == "node_modules"))
        .last()
        .ok_or("OMP Bun entrypoint must belong to an installed node_modules package")?;
    let root = executable
        .ancestors()
        .skip(1)
        .take_while(|path| *path != modules)
        .find(|path| path.join("package.json").exists())
        .ok_or("missing OMP entrypoint package metadata")?;
    let metadata = package_metadata(root, "OMP runtime package")?;
    let bin = metadata["bin"]["omp"]
        .as_str()
        .ok_or("OMP package must declare its omp entrypoint")?;
    if metadata["name"].as_str() != Some("@oh-my-pi/pi-coding-agent")
        || !Path::new(bin)
            .components()
            .all(|part| matches!(part, std::path::Component::Normal(_)))
        || root.join(bin) != executable
    {
        return Err("OMP script does not match the official package entrypoint".to_owned());
    }
    package_closure_mounts(root, modules, "@oh-my-pi/pi-coding-agent", "OMP")
}

/// Read-only mounts for an installed package and its runtime dependency
/// closure, resolved like Node from each package location upwards but never
/// above `modules`, the outermost `node_modules` that holds `root`. Package
/// contents are mounted, not `node_modules` containers: hoisted and symlinked
/// dependencies are exposed individually, at every location that names them.
fn package_closure_mounts(
    root: &Path,
    modules: &Path,
    name: &str,
    label: &str,
) -> Result<Vec<PathBuf>, String> {
    let mut pending = vec![(root.to_path_buf(), name.to_owned())];
    let mut packages = BTreeMap::<PathBuf, BTreeSet<PathBuf>>::new();
    while let Some((location, expected_name)) = pending.pop() {
        let canonical = fs::canonicalize(&location).map_err(|error| {
            format!(
                "resolve {label} runtime package {}: {error}",
                location.display()
            )
        })?;
        if !canonical.starts_with(modules)
            || !canonical.ends_with(Path::new("node_modules").join(&expected_name))
            || !canonical.is_dir()
        {
            return Err(format!(
                "unsafe {label} runtime package location {}",
                location.display()
            ));
        }
        if let Some(locations) = packages.get_mut(&canonical) {
            locations.insert(location);
            continue;
        }
        let metadata = package_metadata(&canonical, &format!("{label} runtime package"))?;
        if metadata["name"].as_str() != Some(expected_name.as_str()) {
            return Err(format!(
                "{label} runtime package identity mismatch at {}",
                location.display()
            ));
        }
        packages.insert(
            canonical.clone(),
            BTreeSet::from([location, canonical.clone()]),
        );
        let mut dependencies = BTreeMap::new();
        for field in ["dependencies", "peerDependencies", "optionalDependencies"] {
            let Some(values) = metadata.get(field) else {
                continue;
            };
            let values = values
                .as_object()
                .ok_or_else(|| format!("invalid {label} package dependency metadata"))?;
            for name in values.keys() {
                if !package_name(name) {
                    return Err(format!("unsafe {label} runtime dependency name `{name}`"));
                }
                let optional = field == "optionalDependencies"
                    || (field == "peerDependencies"
                        && metadata["peerDependenciesMeta"][name]["optional"].as_bool()
                            == Some(true));
                dependencies.insert(name.clone(), optional);
            }
        }
        for (name, optional) in dependencies {
            let mut found = None;
            for ancestor in canonical.ancestors() {
                if !ancestor.starts_with(modules) && Some(ancestor) != modules.parent() {
                    break;
                }
                if ancestor
                    .file_name()
                    .is_some_and(|name| name == "node_modules")
                {
                    continue;
                }
                let candidate = ancestor.join("node_modules").join(&name);
                match fs::symlink_metadata(&candidate) {
                    Ok(_) => {
                        found = Some(candidate);
                        break;
                    }
                    Err(error) if error.kind() == std::io::ErrorKind::NotFound => {}
                    Err(error) => {
                        return Err(format!(
                            "locate {label} runtime dependency `{name}`: {error}"
                        ));
                    }
                }
            }
            if let Some(dependency) = found {
                pending.push((dependency, name));
            } else if !optional {
                return Err(format!("missing {label} runtime dependency `{name}`"));
            }
        }
    }

    let mut mounts = BTreeSet::new();
    for (package, locations) in packages {
        for entry in fs::read_dir(&package)
            .map_err(|error| format!("list {label} runtime package: {error}"))?
        {
            let entry = entry.map_err(|error| format!("list {label} runtime package: {error}"))?;
            if entry.file_name() == "node_modules" {
                continue;
            }
            validate_package_content(&entry.path(), &package, &format!("{label} package"))?;
            for location in &locations {
                mounts.insert(location.join(entry.file_name()));
            }
        }
    }
    Ok(mounts.into_iter().collect())
}

fn validate_package_content(path: &Path, package: &Path, label: &str) -> Result<(), String> {
    let metadata = fs::symlink_metadata(path)
        .map_err(|error| format!("inspect {label} content {}: {error}", path.display()))?;
    if metadata.file_type().is_symlink() {
        let target = fs::canonicalize(path)
            .map_err(|error| format!("resolve {label} content {}: {error}", path.display()))?;
        if !target.starts_with(package) || target.starts_with(package.join("node_modules")) {
            return Err(format!(
                "{label} content escapes its package: {}",
                path.display()
            ));
        }
    } else if metadata.is_dir() {
        for entry in fs::read_dir(path)
            .map_err(|error| format!("list {label} content {}: {error}", path.display()))?
        {
            let entry = entry.map_err(|error| format!("list {label} content: {error}"))?;
            validate_package_content(&entry.path(), package, label)?;
        }
    } else if !metadata.is_file() {
        return Err(format!("unsafe {label} content {}", path.display()));
    }
    Ok(())
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

fn closed_version_token(stdout: &[u8]) -> Option<&str> {
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

/// Model ids a successful Claude Code JSON result lists in `modelUsage`: the
/// models that actually answered, whatever alias or default selected them.
fn claude_models(stdout: &[u8]) -> Vec<String> {
    serde_json::from_slice::<serde_json::Value>(stdout)
        .ok()
        .and_then(|result| {
            result
                .get("modelUsage")
                .and_then(serde_json::Value::as_object)
                .map(|usage| usage.keys().cloned().collect())
        })
        .unwrap_or_default()
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

/// Tool requests a Claude Code JSON result lists in `permission_denials`
/// (requests the caller's permission mode and rules did not allow, denied
/// because nobody can answer a prompt in print mode): the tool name and, for
/// file tools, the path; never the rest of the tool input.
fn claude_permission_denials(stdout: &[u8]) -> Vec<String> {
    let Ok(serde_json::Value::Object(result)) = serde_json::from_slice(stdout) else {
        return Vec::new();
    };
    let Some(denials) = result
        .get("permission_denials")
        .and_then(serde_json::Value::as_array)
    else {
        return Vec::new();
    };
    denials
        .iter()
        .map(|denial| {
            let tool = denial
                .get("tool_name")
                .and_then(serde_json::Value::as_str)
                .filter(|tool| !tool.is_empty() && !tool.chars().any(char::is_control))
                .unwrap_or("tool");
            let path = denial.get("tool_input").and_then(|input| {
                ["file_path", "notebook_path", "path"]
                    .iter()
                    .find_map(|key| input.get(*key).and_then(serde_json::Value::as_str))
            });
            match path {
                Some(path) if !path.chars().any(char::is_control) => format!("{tool} `{path}`"),
                _ => tool.to_owned(),
            }
        })
        .collect()
}

/// Why a CLI that exited successfully may have left the target empty: Cott
/// passes no permission, sandbox or approval override, so the caller's own
/// policy decides whether the CLI may write it, and a denial is final (no run
/// is retried with a more permissive policy).
fn local_policy_note(kind: AgentKind, stdout: &[u8]) -> String {
    match kind {
        AgentKind::Claude => {
            let denials = claude_permission_denials(stdout);
            if denials.is_empty() {
                "; Cott passes no --permission-mode: the caller's Claude Code permission mode and rules decide whether print mode may edit files".to_owned()
            } else {
                let shown = denials.iter().take(8).cloned().collect::<Vec<_>>().join(", ");
                let more = denials.len().saturating_sub(8);
                format!(
                    ": the caller's Claude Code permission settings denied {} tool request(s) ({shown}{}); Cott passes no --permission-mode or allow rule, so file edits must be allowed there (for example `permissions.defaultMode` `acceptEdits` or an `Edit`/`Write` allow rule)",
                    denials.len(),
                    if more > 0 { format!(", {more} more") } else { String::new() },
                )
            }
        }
        AgentKind::Codex => "; Cott passes no --sandbox or approval flag: the caller's Codex `sandbox_mode`/`permission_profile` and project trust decide whether `codex exec` may write the project path, and a read-only policy cannot write the target".to_owned(),
        AgentKind::Omp => "; Cott passes no --approval-mode: the caller's OMP `tools.approvalMode` and `tools.approval` settings decide whether print mode may write files".to_owned(),
        AgentKind::Pi => String::new(),
    }
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

/// Environment names recorded in AgentRun for a generation run: `PATH` and
/// the variables cott itself sets. Every adapter otherwise inherits the
/// caller's environment (see [`AGENT_NOT_INHERITED`]) without recording its
/// names or values, so credentials and private configuration never reach
/// provenance.
fn agent_environment_names() -> Vec<String> {
    ["HOME", "PATH", "PWD", "PYTHONDONTWRITEBYTECODE", "TMPDIR"]
        .into_iter()
        .map(str::to_owned)
        .collect()
}

/// Pi version and Node probes only: no startup network, no `pi.dev` version
/// request, no telemetry. Generation runs never get these overrides.
const PI_FIXED_ENVIRONMENT: [(&str, &str); 3] = [
    ("PI_OFFLINE", "1"),
    ("PI_SKIP_VERSION_CHECK", "1"),
    ("PI_TELEMETRY", "0"),
];

/// Where each CLI keeps its user configuration and login: the variable that
/// relocates it, the home-relative default, and the credential stores inside
/// it that the CLI rewrites when a login is refreshed (Codex `auth.json`,
/// Claude Code `.credentials.json`, OMP's SQLite `agent.db` and its
/// `-journal`/`-wal`/`-shm` companions, Pi `auth.json`). The directory is the
/// CLI's store: it is shared with the host as a whole ([`MappedMount::Shared`])
/// so the CLI's lock files, `rename` temporaries and SQLite companion files are
/// created next to the host's and coordinate with concurrent host sessions.
fn configuration_root(kind: AgentKind) -> (&'static str, &'static str, &'static [&'static str]) {
    match kind {
        AgentKind::Codex => ("CODEX_HOME", ".codex", &["auth.json"]),
        AgentKind::Claude => ("CLAUDE_CONFIG_DIR", ".claude", &[".credentials.json"]),
        AgentKind::Omp => (
            "PI_CODING_AGENT_DIR",
            ".omp/agent",
            &[
                "agent.db",
                "agent.db-journal",
                "agent.db-shm",
                "agent.db-wal",
            ],
        ),
        AgentKind::Pi => ("PI_CODING_AGENT_DIR", ".pi/agent", &["auth.json"]),
    }
}

/// Agent configuration and context the supported CLIs read from the project
/// root, their working directory: Pi `.pi/`; Codex `.codex/` (project config
/// layers, rules, hooks); Claude Code `.claude/`, `.mcp.json` and
/// `CLAUDE.local.md`; OMP `.omp/` and the other tools' project locations its
/// discovery reads (`.agent`, `.clinerules`, `.cursor`, `.cursorrules`,
/// `.gemini`, `.github` Copilot instructions, `.opencode`, `opencode.json(c)`,
/// `.vscode/mcp.json`, `.windsurf`, `.windsurfrules`, `mcp.json`); the shared
/// `.agents/` skills; and the context files (`AGENTS.md`,
/// `AGENTS.override.md`, `CLAUDE.md`, and Pi's `AGENTS.MD`/`CLAUDE.MD`).
/// Present entries are mounted read-only at their own names under the project
/// root path, where the sandbox presents the isolated workspace.
pub const PROJECT_RESOURCES: &[&str] = &[
    ".agent",
    ".agents",
    ".claude",
    ".clinerules",
    ".codex",
    ".cursor",
    ".cursorrules",
    ".gemini",
    ".github/copilot-instructions.md",
    ".github/instructions",
    ".mcp.json",
    ".omp",
    ".opencode",
    ".pi",
    ".vscode/mcp.json",
    ".windsurf",
    ".windsurfrules",
    "AGENTS.MD",
    "AGENTS.md",
    "AGENTS.override.md",
    "CLAUDE.MD",
    "CLAUDE.local.md",
    "CLAUDE.md",
    "mcp.json",
    "opencode.json",
    "opencode.jsonc",
];

/// Context and configuration the supported CLIs read from the project root's
/// ancestors: the context files (Pi and Claude Code up to `/`, Codex from the
/// repository root down), Claude Code `.claude/` memory and rules, Codex
/// `.codex/` project config layers between the repository root and the
/// working directory, `.agents/` skills (Pi and Codex, up to the repository
/// root), and OMP's `.omp/` and `.clinerules`. Present entries are mounted
/// read-only at their own paths; each CLI applies its own discovery rules to
/// them. Directories directly in the home directory are the user-level setup
/// ([`user_environment`]), not project ancestors, and are not mounted again.
pub const ANCESTOR_RESOURCES: &[&str] = &[
    ".agents",
    ".claude",
    ".clinerules",
    ".codex",
    ".omp",
    "AGENTS.MD",
    "AGENTS.md",
    "AGENTS.override.md",
    "CLAUDE.MD",
    "CLAUDE.local.md",
    "CLAUDE.md",
];

/// Largest repository metadata file (`.git` pointer, `HEAD`, `commondir`,
/// `gitdir`) mounted as a repository root marker.
const MAX_GIT_METADATA_BYTES: u64 = 64 * 1024;

/// The caller's own CLI setup for a generation run: inherited environment,
/// extra read-only paths, the configuration mounts, and the working directory
/// at which the sandbox presents the isolated workspace.
#[derive(Clone, Debug)]
pub struct UserEnvironment {
    variables: BTreeMap<String, String>,
    read_only: Vec<PathBuf>,
    mounts: Vec<MappedMount>,
    /// The caller project's root path, or the workspace path without one.
    cwd: PathBuf,
}

impl UserEnvironment {
    /// Create, in `workspace`, a mount point for every destination below
    /// [`Self::cwd`] (and for `runtime_paths` there): the sandbox presents the
    /// workspace read-only at the working directory, and a read-only bind
    /// cannot receive new mount points. Missing parents become empty
    /// directories and missing leaves empty files or directories of the
    /// source's kind; existing entries of the same kind are reused (the mount
    /// covers them). The agent target (`target`, workspace-relative) is never
    /// a mount point. This runs before the workspace snapshot, so the mount
    /// points are part of the audited workspace.
    fn prepare_mount_points(
        &self,
        workspace: &Path,
        target: &Path,
        runtime_paths: &[PathBuf],
    ) -> Result<(), String> {
        let destinations = self
            .mounts
            .iter()
            .map(|mount| (mount.destination(), mount.source()))
            .chain(
                self.read_only
                    .iter()
                    .map(|path| (path.as_path(), path.as_path())),
            )
            .chain(
                runtime_paths
                    .iter()
                    .map(|path| (path.as_path(), path.as_path())),
            );
        for (destination, source) in destinations {
            let Ok(relative) = destination.strip_prefix(&self.cwd) else {
                continue;
            };
            if relative.as_os_str().is_empty() {
                continue;
            }
            let prepared = if relative == target {
                Err("it is the agent target".to_owned())
            } else {
                mount_point(workspace, relative, source.is_dir())
            };
            prepared.map_err(|reason| {
                format!(
                    "prepare the mount point for {} in the agent workspace: {reason}",
                    destination.display()
                )
            })?;
        }
        Ok(())
    }
}

/// Ensure `workspace/relative` exists as a directory (`directory`) or a
/// regular file, creating missing components; symlinks and entries of the
/// other kind are refused.
fn mount_point(workspace: &Path, relative: &Path, directory: bool) -> Result<(), String> {
    let mut path = workspace.to_path_buf();
    let components = relative.components().collect::<Vec<_>>();
    for (index, component) in components.iter().enumerate() {
        let std::path::Component::Normal(name) = component else {
            return Err(format!(
                "`{}` is not a plain relative path",
                relative.display()
            ));
        };
        path.push(name);
        let leaf = index + 1 == components.len();
        let want_directory = !leaf || directory;
        match fs::symlink_metadata(&path) {
            Ok(existing) if want_directory && existing.is_dir() => {}
            Ok(existing) if !want_directory && existing.is_file() => {}
            Ok(_) => {
                return Err(format!(
                    "`{}` already exists as another kind of entry",
                    path.display()
                ));
            }
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
                if want_directory {
                    fs::create_dir(&path)
                } else {
                    OpenOptions::new()
                        .write(true)
                        .create_new(true)
                        .open(&path)
                        .map(drop)
                }
                .map_err(|error| format!("create `{}`: {error}", path.display()))?;
            }
            Err(error) => return Err(format!("inspect `{}`: {error}", path.display())),
        }
    }
    Ok(())
}

/// `/` and the home directory or its ancestors are never mounted whole.
fn too_broad(path: &Path, home: &Path) -> bool {
    path == Path::new("/") || home.starts_with(path)
}

/// Trees the sandbox already provides read-only.
fn system_tree(path: &Path) -> bool {
    [
        "/usr", "/bin", "/lib", "/lib64", "/etc", "/proc", "/dev", "/sys",
    ]
    .iter()
    .any(|root| path.starts_with(root))
}

/// The absolute path a symlink names, resolved lexically against the
/// directory it lies in (as the kernel resolves it in the sandbox, where the
/// directories leading to a presented path are plain directories).
fn link_destination(link: &Path) -> Option<PathBuf> {
    let named = link.parent()?.join(fs::read_link(link).ok()?);
    let mut destination = PathBuf::new();
    for component in named.components() {
        match component {
            std::path::Component::RootDir => destination.push("/"),
            std::path::Component::CurDir => {}
            std::path::Component::ParentDir => {
                destination.pop();
            }
            std::path::Component::Normal(name) => destination.push(name),
            std::path::Component::Prefix(_) => return None,
        }
    }
    destination.is_absolute().then_some(destination)
}

/// Resolve the caller's setup for `kind` where the CLI itself looks for it,
/// without copying, selecting or rewriting anything:
///
/// - the caller's environment minus [`AGENT_NOT_INHERITED`], with the real
///   `HOME`, the run's scratch as `TMPDIR` and the working directory as `PWD`;
/// - the working directory: the canonical caller project root, where the
///   sandbox presents the isolated workspace, else the workspace itself;
/// - the configuration root ([`configuration_root`]) shared with the host at
///   its own path ([`configuration_store`]): reads, login refreshes, lock
///   files, `rename` temporaries, caches and SQLite companion files act on
///   the host directory as in a normal run and coordinate with concurrent
///   host sessions; Cott itself never writes there;
/// - read-only: targets of top-level links out of the configuration root (at
///   their own path and, for a chain of links or a link through a linked
///   directory, also at the path the link names, so the caller's link
///   resolves; [`link_destination`]),
///   local paths named by Pi settings, `~/.agents/skills`, `~/.aws`,
///   `~/.config/gcloud`, Claude Code's `~/.claude.json`, OMP's
///   `~/.omp/natives`, certificate and credential files named by
///   [`AGENT_FILE_VARIABLES`], the caller project's [`PROJECT_RESOURCES`]
///   (with Codex's configured `project_doc_fallback_filenames`), the
///   [`ANCESTOR_RESOURCES`] of the project's ancestors, its repository root
///   marker ([`repository_marker`]), and the PATH installations
///   ([`path_mounts`]). Read-only paths inside the shared configuration root
///   are already visible there and are not mounted over it.
fn user_environment(
    kind: AgentKind,
    scratch: &Path,
    workspace: &Path,
    project: Option<&Path>,
) -> Result<UserEnvironment, String> {
    let mut variables = BTreeMap::new();
    for (name, value) in std::env::vars_os() {
        let (Ok(name), Ok(value)) = (name.into_string(), value.into_string()) else {
            continue;
        };
        if !AGENT_NOT_INHERITED.contains(&name.as_str()) {
            variables.insert(name, value);
        }
    }
    let home = std::env::var("HOME")
        .ok()
        .map(PathBuf::from)
        .filter(|home| home.is_absolute() && home.is_dir())
        .ok_or("agent generation needs HOME to name the caller's home directory")?;
    let project = project
        .map(|project| {
            fs::canonicalize(project)
                .ok()
                .filter(|project| project.is_dir())
                .ok_or_else(|| format!("resolve project {}", project.display()))
        })
        .transpose()?;
    let cwd = project.clone().unwrap_or_else(|| workspace.to_path_buf());
    variables.insert("HOME".to_owned(), home.display().to_string());
    variables.insert("TMPDIR".to_owned(), scratch.display().to_string());
    variables.insert("PWD".to_owned(), cwd.display().to_string());
    variables.insert("PYTHONDONTWRITEBYTECODE".to_owned(), "1".to_owned());
    variables
        .entry("PATH".to_owned())
        .or_insert_with(|| "/usr/bin:/bin".to_owned());
    let mut read_only = Vec::new();
    let mut mounts = Vec::new();
    let mut context_files = Vec::new();
    let mut link_hops = Vec::new();
    let (variable, default, credentials) = configuration_root(kind);
    let root = match variables.get(variable).map(String::as_str) {
        Some("~") => home.clone(),
        Some(value) if value.starts_with("~/") => home.join(&value[2..]),
        Some(value) if !value.is_empty() => PathBuf::from(value),
        _ => home.join(default),
    };
    if !root.is_absolute() {
        return Err(format!(
            "{variable} `{}` must be an absolute path",
            root.display()
        ));
    }
    if let Some(source) = fs::canonicalize(&root)
        .ok()
        .filter(|source| source.is_dir())
    {
        configuration_store(&root, &source, credentials, &home, project.as_deref())?;
        let list_error = |error: std::io::Error| format!("list {}: {error}", root.display());
        for entry in fs::read_dir(&source).map_err(list_error)? {
            let entry = entry.map_err(list_error)?;
            if entry.file_type().is_ok_and(|kind| kind.is_symlink()) {
                if let Ok(target) = fs::canonicalize(entry.path()) {
                    if !target.starts_with(&source) {
                        // The link names its first hop, not the final file:
                        // a chain of links (a dotfile manager's generated
                        // tree) or a linked directory on the way only
                        // resolves in the sandbox if that path is presented.
                        for directory in [&root, &source] {
                            if let Some(hop) = link_destination(&directory.join(entry.file_name()))
                            {
                                if hop != target
                                    && !link_hops.contains(&(target.clone(), hop.clone()))
                                {
                                    link_hops.push((target.clone(), hop));
                                }
                            }
                        }
                        read_only.push(target);
                    }
                }
            }
        }
        match kind {
            AgentKind::Pi => mounts.extend(pi_settings_paths(
                &source.join("settings.json"),
                &source,
                &home,
            )),
            AgentKind::Codex => {
                context_files = codex_fallback_filenames(&source.join("config.toml"));
            }
            AgentKind::Claude | AgentKind::Omp => {}
        }
        if source != root {
            mounts.push(MappedMount::Shared {
                source: source.clone(),
                destination: source.clone(),
            });
        }
        mounts.push(MappedMount::Shared {
            source,
            destination: root.clone(),
        });
    }
    let mut home_resources = vec![".agents/skills", ".aws", ".config/gcloud"];
    match kind {
        AgentKind::Claude if !variables.contains_key("CLAUDE_CONFIG_DIR") => {
            home_resources.push(".claude.json");
        }
        AgentKind::Omp => home_resources.push(".omp/natives"),
        _ => {}
    }
    for relative in home_resources {
        let logical = home.join(relative);
        if let Ok(source) = fs::canonicalize(&logical) {
            mounts.push(MappedMount::ReadOnly {
                source,
                destination: logical,
            });
        }
    }
    for name in AGENT_FILE_VARIABLES {
        if let Some(path) = variables
            .get(*name)
            .map(Path::new)
            .filter(|path| path.is_absolute())
        {
            if let Ok(source) = fs::canonicalize(path) {
                read_only.push(source);
            }
        }
    }
    if let Some(project) = &project {
        mounts.extend(project_resources(project, &context_files, &home));
        mounts.extend(ancestor_resources(project, &context_files, &home));
        mounts.extend(repository_marker(project));
    }
    mounts.extend(path_mounts(&variables["PATH"], &home));
    // Present a link's first hop as the final file or directory, unless the
    // hop lies in a system tree or a tree presented already (there it is the
    // host's own entry and a bind onto it would follow it).
    for (source, hop) in link_hops {
        let presented = mounts
            .iter()
            .map(MappedMount::destination)
            .chain(read_only.iter().map(PathBuf::as_path))
            .any(|presented| hop.starts_with(presented));
        if !presented && !system_tree(&hop) {
            mounts.push(MappedMount::ReadOnly {
                source,
                destination: hop,
            });
        }
    }
    let stores = mounts
        .iter()
        .filter(|mount| matches!(mount, MappedMount::Shared { .. }))
        .map(|mount| mount.destination().to_path_buf())
        .collect::<Vec<_>>();
    let in_store = |path: &Path| stores.iter().any(|store| path.starts_with(store));
    read_only.retain(|path| !too_broad(path, &home) && !in_store(path));
    mounts.retain(|mount| {
        !too_broad(mount.destination(), &home)
            && (matches!(mount, MappedMount::Shared { .. }) || !in_store(mount.destination()))
    });
    Ok(UserEnvironment {
        variables,
        read_only,
        mounts,
        cwd,
    })
}

/// Check a CLI configuration directory before it is shared writable with the
/// host: a directory owned by the caller that is neither `/`, a system tree,
/// the home directory or one of its ancestors, nor the caller project, one of
/// its ancestors or inside it (the project's own files are never writable), whose login
/// stores ([`configuration_root`]) are absent or regular single-link files
/// owned by the caller directly inside it. A login store must not be a link:
/// a symlink would send the CLI's writes out of the shared directory, and a
/// second hard link would let them change another path.
fn configuration_store(
    root: &Path,
    source: &Path,
    credentials: &[&str],
    home: &Path,
    project: Option<&Path>,
) -> Result<(), String> {
    // SAFETY: geteuid has no preconditions.
    let euid = unsafe { libc::geteuid() };
    let metadata =
        fs::metadata(source).map_err(|error| format!("inspect {}: {error}", root.display()))?;
    if !metadata.is_dir() || metadata.uid() != euid {
        return Err(format!(
            "configuration directory {} must be a directory owned by the caller",
            root.display()
        ));
    }
    if too_broad(source, home) || system_tree(source) {
        return Err(format!(
            "configuration directory {} must not be `/`, a system tree, or the home directory or one of its ancestors: the agent shares it writable",
            root.display()
        ));
    }
    if project.is_some_and(|project| project.starts_with(source)) {
        return Err(format!(
            "configuration directory {} contains the caller project; the project is never writable to an agent",
            root.display()
        ));
    }
    if project.is_some_and(|project| source.starts_with(project)) {
        return Err(format!(
            "configuration directory {} is inside the caller project; the project is never writable to an agent",
            root.display()
        ));
    }
    for name in credentials {
        let path = source.join(name);
        match fs::symlink_metadata(&path) {
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {}
            Err(error) => return Err(format!("inspect {}: {error}", root.join(name).display())),
            Ok(metadata)
                if metadata.file_type().is_file()
                    && metadata.uid() == euid
                    && metadata.nlink() == 1 => {}
            Ok(_) => {
                return Err(format!(
                    "credential store {} must be a regular single-link file owned by the caller, not a symlink or hard link",
                    root.join(name).display()
                ));
            }
        }
    }
    Ok(())
}

/// `project_doc_fallback_filenames` of the caller's Codex `config.toml`: the
/// extra context file names Codex looks for next to `AGENTS.md` from the
/// repository root down to the working directory. Only plain file names are
/// kept, as Codex does.
fn codex_fallback_filenames(config: &Path) -> Vec<String> {
    let Ok(text) = fs::read_to_string(config) else {
        return Vec::new();
    };
    let Ok(table) = text.parse::<toml::Table>() else {
        return Vec::new();
    };
    table
        .get("project_doc_fallback_filenames")
        .and_then(toml::Value::as_array)
        .into_iter()
        .flatten()
        .filter_map(toml::Value::as_str)
        .filter(|name| {
            !name.is_empty() && !matches!(*name, "." | "..") && !name.contains(['/', '\0'])
        })
        .map(str::to_owned)
        .collect()
}

/// Read-only mounts for the caller project's [`PROJECT_RESOURCES`] and
/// `context_files` at their own paths under the canonical `project` root,
/// where the sandbox presents the isolated workspace
/// ([`UserEnvironment::prepare_mount_points`] creates their mount points).
/// Links are resolved: a resource linking elsewhere is presented with its
/// target's content.
fn project_resources(project: &Path, context_files: &[String], home: &Path) -> Vec<MappedMount> {
    let names = PROJECT_RESOURCES
        .iter()
        .copied()
        .chain(context_files.iter().map(String::as_str))
        .collect::<BTreeSet<_>>();
    let mut mounts = Vec::new();
    for name in names {
        let destination = project.join(name);
        let Ok(source) = fs::canonicalize(&destination) else {
            continue;
        };
        if too_broad(&source, home) || !(source.is_dir() || source.is_file()) {
            continue;
        }
        if name == ".pi" {
            mounts.extend(pi_settings_paths(
                &source.join("settings.json"),
                &source,
                home,
            ));
        }
        mounts.push(MappedMount::ReadOnly {
            source,
            destination,
        });
    }
    mounts
}

/// Read-only mounts for the [`ANCESTOR_RESOURCES`] and `context_files` of
/// every ancestor of the canonical `project` root, at their own paths.
/// Directories directly in the home directory or in `/` are skipped: the
/// former are the user-level setup, the latter system state.
fn ancestor_resources(project: &Path, context_files: &[String], home: &Path) -> Vec<MappedMount> {
    let names = ANCESTOR_RESOURCES
        .iter()
        .copied()
        .chain(context_files.iter().map(String::as_str))
        .collect::<BTreeSet<_>>();
    let mut mounts = Vec::new();
    for ancestor in project.ancestors().skip(1) {
        for name in &names {
            let destination = ancestor.join(name);
            let Ok(metadata) = fs::metadata(&destination) else {
                continue;
            };
            if metadata.is_dir() && (ancestor == home || ancestor == Path::new("/")) {
                continue;
            }
            if !(metadata.is_dir() || metadata.is_file()) {
                continue;
            }
            let Ok(source) = fs::canonicalize(&destination) else {
                continue;
            };
            if too_broad(&source, home) {
                continue;
            }
            mounts.push(MappedMount::ReadOnly {
                source,
                destination,
            });
        }
    }
    mounts
}

/// The repository root marker of the canonical `project`: the nearest `.git`
/// at or above the project root, presented read-only with only the metadata
/// the CLIs read to find the repository root, which bounds their context and
/// skill discovery and keys Codex project trust. A `.git` directory
/// contributes its `HEAD`; a `.git` pointer file (worktree, submodule) is
/// mounted itself with its git directory's `HEAD`, `commondir` and `gitdir`
/// and the common directory's `HEAD`. Objects, refs, index and config stay
/// hidden, so the project's history and files remain outside the sandbox and
/// `git` there finds no repository. Links are not followed.
fn repository_marker(project: &Path) -> Vec<MappedMount> {
    fn metadata_file(mounts: &mut Vec<MappedMount>, path: &Path) {
        if fs::symlink_metadata(path)
            .is_ok_and(|metadata| metadata.is_file() && metadata.len() <= MAX_GIT_METADATA_BYTES)
        {
            mounts.push(MappedMount::ReadOnly {
                source: path.to_path_buf(),
                destination: path.to_path_buf(),
            });
        }
    }
    let mut mounts = Vec::new();
    let Some((root, metadata)) = project.ancestors().find_map(|ancestor| {
        fs::symlink_metadata(ancestor.join(".git"))
            .ok()
            .map(|metadata| (ancestor, metadata))
    }) else {
        return mounts;
    };
    let dot_git = root.join(".git");
    if metadata.is_dir() {
        metadata_file(&mut mounts, &dot_git.join("HEAD"));
        return mounts;
    }
    metadata_file(&mut mounts, &dot_git);
    if mounts.is_empty() {
        return mounts;
    }
    let Some(git_dir) = fs::read_to_string(&dot_git)
        .ok()
        .and_then(|text| {
            text.trim()
                .strip_prefix("gitdir:")
                .map(|target| root.join(target.trim()))
        })
        .and_then(|git_dir| fs::canonicalize(git_dir).ok())
        .filter(|git_dir| git_dir.is_dir())
    else {
        return mounts;
    };
    for name in ["HEAD", "commondir", "gitdir"] {
        metadata_file(&mut mounts, &git_dir.join(name));
    }
    if let Some(common) = fs::read_to_string(git_dir.join("commondir"))
        .ok()
        .and_then(|text| fs::canonicalize(git_dir.join(text.trim())).ok())
        .filter(|common| common.is_dir())
    {
        metadata_file(&mut mounts, &common.join("HEAD"));
    }
    mounts
}

/// Read-only mounts for local paths a Pi settings file names in `packages`,
/// `extensions`, `skills`, `prompts` and `themes`: `~/` paths, absolute
/// paths, and paths relative to the settings directory `base` that leave it.
/// Package-manager sources (`npm:`, `git:`, URLs) live inside the agent
/// directory already; patterns that name no existing path are skipped.
fn pi_settings_paths(settings: &Path, base: &Path, home: &Path) -> Vec<MappedMount> {
    let Ok(text) = fs::read_to_string(settings) else {
        return Vec::new();
    };
    let Ok(value) = serde_json::from_str::<serde_json::Value>(&text) else {
        return Vec::new();
    };
    let mut mounts = Vec::new();
    for key in ["packages", "extensions", "skills", "prompts", "themes"] {
        let Some(entries) = value.get(key).and_then(serde_json::Value::as_array) else {
            continue;
        };
        for entry in entries {
            let Some(spec) = entry
                .as_str()
                .or_else(|| entry.get("source").and_then(serde_json::Value::as_str))
            else {
                continue;
            };
            let spec = spec.trim_start_matches(['!', '+', '-']);
            if [
                "npm:", "git:", "git+", "git@", "http://", "https://", "ssh://",
            ]
            .iter()
            .any(|prefix| spec.starts_with(prefix))
            {
                continue;
            }
            let logical = match spec.strip_prefix("~/") {
                Some(rest) => home.join(rest),
                None if spec == "~" => home.to_path_buf(),
                None => base.join(spec),
            };
            let Ok(source) = fs::canonicalize(&logical) else {
                continue;
            };
            if source.starts_with(base) || too_broad(&source, home) {
                continue;
            }
            let plain = logical.components().all(|component| {
                matches!(
                    component,
                    std::path::Component::RootDir | std::path::Component::Normal(_)
                )
            });
            if plain && logical != source {
                mounts.push(MappedMount::ReadOnly {
                    source: source.clone(),
                    destination: logical,
                });
            }
            mounts.push(MappedMount::ReadOnly {
                source: source.clone(),
                destination: source,
            });
        }
    }
    mounts
}

/// Read-only mounts that keep the caller's PATH usable in the sandbox: each
/// absolute PATH directory outside the system trees (at its own path), and
/// for every entry linking out of its directory the installation it belongs
/// to: `<prefix>` of a `<prefix>/bin/<tool>` target (followed through that
/// prefix's own `bin`), else the target itself. At most 256 mounts.
fn path_mounts(path: &str, home: &Path) -> Vec<MappedMount> {
    const LIMIT: usize = 256;
    let mut mounts = Vec::new();
    let mut seen = BTreeSet::new();
    let mut pending = Vec::new();
    for directory in std::env::split_paths(path) {
        if !directory.is_absolute() {
            continue;
        }
        let Ok(source) = fs::canonicalize(&directory) else {
            continue;
        };
        if !source.is_dir() || system_tree(&source) || too_broad(&source, home) {
            continue;
        }
        if seen.insert(directory.clone()) {
            mounts.push(MappedMount::ReadOnly {
                source: source.clone(),
                destination: directory,
            });
        }
        pending.push(source);
    }
    let mut visited = BTreeSet::new();
    while let Some(directory) = pending.pop() {
        if mounts.len() >= LIMIT || !visited.insert(directory.clone()) {
            continue;
        }
        let Ok(entries) = fs::read_dir(&directory) else {
            continue;
        };
        for entry in entries.flatten() {
            if !entry.file_type().is_ok_and(|kind| kind.is_symlink()) {
                continue;
            }
            let Ok(target) = fs::canonicalize(entry.path()) else {
                continue;
            };
            if target.starts_with(&directory) || system_tree(&target) {
                continue;
            }
            let prefix = target
                .parent()
                .filter(|parent| parent.file_name().is_some_and(|name| name == "bin"))
                .and_then(Path::parent)
                .filter(|prefix| !system_tree(prefix) && !too_broad(prefix, home))
                .map(Path::to_path_buf);
            let source = prefix.clone().unwrap_or(target);
            if too_broad(&source, home) || mounts.len() >= LIMIT {
                continue;
            }
            if seen.insert(source.clone()) {
                mounts.push(MappedMount::ReadOnly {
                    source: source.clone(),
                    destination: source,
                });
            }
            if let Some(prefix) = prefix {
                pending.push(prefix.join("bin"));
            }
        }
    }
    mounts
}

/// How a sandboxed adapter process is launched.
#[derive(Clone, Copy)]
enum Launch<'a> {
    /// Version and runtime probes: no network, no credentials, no caller
    /// configuration (Pi additionally runs offline with an empty agent
    /// directory).
    Probe(AgentKind),
    /// Generation: the caller's own CLI setup with the network enabled.
    Generation(AgentKind, &'a UserEnvironment),
}

#[allow(clippy::too_many_arguments)]
fn run_process(
    executable: &Path,
    runtime: Option<&ScriptRuntime>,
    mut arguments: Vec<String>,
    workspace: &Path,
    scratch: &Path,
    stdin: Vec<u8>,
    launch: Launch<'_>,
    writable_target: Option<&Path>,
    timeout_seconds: u16,
) -> Result<crate::sandbox::CompletedProcess, String> {
    let mut read_only = vec![executable.to_path_buf()];
    let mut mapped = Vec::new();
    let program = if let Some(runtime) = runtime {
        runtime.verify()?;
        read_only.push(runtime.executable.clone());
        read_only.extend(runtime.read_only.iter().cloned());
        arguments.insert(
            0,
            executable
                .to_str()
                .ok_or("agent script entrypoint path is not UTF-8")?
                .to_owned(),
        );
        &runtime.executable
    } else {
        executable
    };
    let (kind, network) = match launch {
        Launch::Probe(kind) => (kind, false),
        Launch::Generation(kind, _) => (kind, true),
    };
    let environment = match launch {
        Launch::Generation(_, user) => {
            read_only.extend(user.read_only.iter().cloned());
            mapped.extend(user.mounts.iter().cloned());
            user.variables.clone()
        }
        Launch::Probe(kind) => {
            let mut environment = BTreeMap::from([
                ("HOME".to_owned(), scratch.display().to_string()),
                ("TMPDIR".to_owned(), scratch.display().to_string()),
                ("PATH".to_owned(), "/usr/bin:/bin".to_owned()),
                ("PYTHONDONTWRITEBYTECODE".to_owned(), "1".to_owned()),
            ]);
            if kind == AgentKind::Pi {
                let agent_dir = scratch.join("pi-agent");
                fs::create_dir_all(&agent_dir)
                    .map_err(|error| format!("create Pi probe agent directory: {error}"))?;
                environment.insert(
                    "PI_CODING_AGENT_DIR".to_owned(),
                    agent_dir.display().to_string(),
                );
                for (name, value) in PI_FIXED_ENVIRONMENT {
                    environment.insert(name.to_owned(), value.to_owned());
                }
            }
            environment
        }
    };
    if network {
        if let Ok(resolver) = fs::canonicalize("/etc/resolv.conf") {
            read_only.push(resolver);
        }
    }
    // The working directory: a generation run with a caller project sees the
    // read-only workspace (and its writable target) at the project root path;
    // probes and project-less runs see the workspace at its own path.
    let cwd = match launch {
        Launch::Generation(_, user) => user.cwd.clone(),
        Launch::Probe(_) => workspace.to_path_buf(),
    };
    let mut writable = vec![scratch.to_path_buf()];
    if cwd == workspace {
        read_only.push(workspace.to_path_buf());
        if let Some(target) = writable_target {
            writable.push(target.to_path_buf());
        }
    } else {
        mapped.push(MappedMount::ReadOnly {
            source: workspace.to_path_buf(),
            destination: cwd.clone(),
        });
        if let Some(target) = writable_target {
            let relative = target
                .strip_prefix(workspace)
                .map_err(|_| "agent target escaped workspace")?;
            mapped.push(MappedMount::Writable {
                source: target.to_path_buf(),
                destination: cwd.join(relative),
            });
        }
    }
    // JavaScript runtimes reserve large virtual address ranges.
    let javascript_runtime = matches!(kind, AgentKind::Omp | AgentKind::Pi);
    let address_space_bytes = if javascript_runtime {
        128 * 1024 * 1024 * 1024
    } else {
        4 * 1024 * 1024 * 1024
    };
    let writable_bytes = if javascript_runtime {
        512 * 1024 * 1024
    } else {
        64 * 1024 * 1024
    };
    run_with_mounts(
        &SandboxSpec {
            program: program.to_path_buf(),
            arguments,
            cwd,
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
        },
        &mapped,
    )
    .map_err(|error| error.to_string())
}
