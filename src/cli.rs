use serde::Serialize;
#[cfg(test)]
use std::cell::RefCell;
use std::collections::{BTreeMap, BTreeSet};
use std::ffi::{CString, OsString};
use std::fs::{self, DirBuilder, File, OpenOptions};
use std::io::{Read, Write};
use std::os::unix::ffi::OsStrExt;
use std::os::unix::fs::MetadataExt;
use std::os::unix::fs::{DirBuilderExt, OpenOptionsExt};
use std::os::unix::process::CommandExt;
use std::path::{Component, Path, PathBuf};
use std::process::{Command as ProcessCommand, Stdio};
use std::thread;
use std::time::{Duration, Instant, SystemTime, UNIX_EPOCH};

pub use crate::agent::AgentKind;
use crate::agent::{
    AgentRunCandidate, ShadowFacet, adapter, parse_domain_rules, render_prompt, run_agent,
    scan_doc_candidates, selected_implementation_kind,
};
use crate::binding::{
    PythonFileRole, ResolvedBinding, audit_facade_file, recorded_intent_baseline,
    resolve_implementations, validate_candidate,
};
use crate::compiler::{ProjectDiagnostic, parse_project};
use crate::diagnostics::{
    Diagnostic, DiagnosticReport, Severity, SourceMap, SourceSpan, Span, code,
};
use crate::hash::sha256_hex;
use crate::hir::lower_with_effects;
use crate::intent;
use crate::ir::render;
pub use crate::manifest::TargetLanguage;
use crate::manifest::{ApiVersion, parse_api_version};
use crate::project::{
    ProjectPaths, discover_python_sources, discover_sources_from_paths, load_config_with_paths,
    load_dart_config_with_paths, load_kotlin_config_with_paths, load_target_language,
};
use crate::provenance::{
    AgentRun, AgentStatus, ClauseCoverage, CoveragePolicyResult, CoverageStatus, CoverageSummary,
    CoverageViolation, GenerationRecord, SemanticCoverage, SourceSpan as ProvenanceSpan,
    StreamDigest, UnresolvedKind, UnresolvedRecord, compare_implementation_identities,
};
use crate::python::artifact_plan::{PythonArtifactPlan, PythonCallable, PythonCallableKind};
use crate::python_emit::{Emission, EmitDiagnostic, emit};
use crate::python_verify::verify_python;
use crate::transaction::{ChangeSet, InputSnapshot, Operation, ProjectSession, TransactionError};
use crate::version::{is_at_least, parse_version};

const USAGE: &str = "Cott compiles contracts into verifiable Python, Kotlin, and Dart.\n\nUsage:\n  cott init <path> [--target python|kotlin|dart] [--name <name>] [--no-sync] [--format json]\n  cott check [<source.cott>] [--project <dir>] [--format json]\n  cott fmt [--check] [--project <dir>] [--format json]\n  cott emit ir|python|kotlin|dart [--project <dir>] [--format json]\n  cott generate [<fully.qualified.callable>] --agent codex|claude|omp --target python|kotlin|dart [-j <jobs>] [--project <dir>] [--format json]\n  cott prompt <fully.qualified.callable> [--project <dir>] [--format json]\n  cott verify [--project <dir>] [--format json]\n  cott deploy [--output <dir>] [--replace] [--project <dir>] [--format json]\n  cott diff [--baseline <generation.json>] [--exit-code] [--project <dir>] [--format json]\n  cott lsp\n  cott --version | -V\n";

#[cfg(test)]
thread_local! {
    static INIT_FAULT: RefCell<Option<&'static str>> = const { RefCell::new(None) };
}

#[cfg(test)]
fn arm_init_fault(name: &'static str) {
    INIT_FAULT.with(|fault| *fault.borrow_mut() = Some(name));
}

#[cfg(test)]
fn clear_init_fault() {
    INIT_FAULT.with(|fault| *fault.borrow_mut() = None);
}

fn init_fault(name: &'static str) -> Result<(), String> {
    #[cfg(test)]
    {
        let injected = INIT_FAULT.with(|fault| {
            let mut fault = fault.borrow_mut();
            if fault.as_ref().is_some_and(|expected| *expected == name) {
                *fault = None;
                true
            } else {
                false
            }
        });
        if injected {
            return Err(format!("injected init filesystem fault: {name}"));
        }
    }
    let _ = name;
    Ok(())
}

/// Runs the command line interface. Parsing is intentionally closed: unknown,
/// duplicate, or context-invalid options are usage errors before project I/O.
pub fn run(arguments: impl IntoIterator<Item = OsString>) -> i32 {
    let mut arguments = arguments.into_iter();
    let _program = arguments.next();
    let arguments: Vec<OsString> = arguments.collect();
    let version_requested = matches!(
        arguments.first().and_then(|argument| argument.to_str()),
        Some("--version" | "-V")
    );
    if !version_requested
        && arguments.first().is_some_and(|command| command == "diff")
        && arguments
            .windows(2)
            .filter(|pair| pair[0] == "--format" && pair[1] == "json")
            .count()
            == 1
        && let Ok(Command::Diff {
            baseline,
            exit_code,
            project,
            format: OutputFormat::Json,
        }) = parse_command(&arguments)
    {
        return diff_for_target(project, baseline, exit_code, OutputFormat::Json);
    }
    if !version_requested
        && arguments.first().is_some_and(|command| command == "prompt")
        && arguments
            .windows(2)
            .filter(|pair| pair[0] == "--format" && pair[1] == "json")
            .count()
            == 1
        && let Ok(Command::Prompt {
            symbol,
            project,
            format: OutputFormat::Json,
        }) = parse_command(&arguments)
    {
        return prompt_for_target(project, symbol, OutputFormat::Json);
    }
    let json_formats = arguments
        .windows(2)
        .filter(|pair| pair[0] == "--format" && pair[1] == "json")
        .count();
    if !version_requested
        && json_formats > 1
        && !matches!(arguments.first(), Some(command) if command == "lsp")
    {
        let report = DiagnosticReport {
            diagnostics: vec![Diagnostic::error(
                code::CLI_USAGE,
                "duplicate option",
                Span::new(0, 0),
            )],
        };
        let bytes = report
            .canonical_json(&SourceMap::default())
            .expect("diagnostic report is serializable");
        let _ = std::io::stdout().write_all(&bytes);
        return 2;
    }
    if !version_requested
        && json_formats == 1
        && !matches!(arguments.first(), Some(command) if command == "lsp")
    {
        return run_json(arguments);
    }

    match parse_command(&arguments) {
        Ok(Command::Lsp) => crate::lsp::run(),
        Ok(Command::Help) => {
            print!("{USAGE}");
            0
        }
        Ok(Command::Version) => {
            println!("cott {}", env!("CARGO_PKG_VERSION"));
            0
        }
        Ok(Command::Init {
            path,
            target,
            name,
            no_sync,
            format,
        }) => match target {
            TargetLanguage::Python => init_project(path, name, no_sync, format),
            TargetLanguage::Kotlin => {
                finish_kotlin_init(crate::kotlin::pipeline::init(path, name, no_sync, format))
            }
            TargetLanguage::Dart => {
                finish_dart_init(crate::dart::pipeline::init(path, name, no_sync, format))
            }
        },
        Ok(Command::Check {
            source, project, ..
        }) => check_for_target(project, source),
        Ok(Command::Fmt { check, project, .. }) => format_for_target(project, check),
        Ok(Command::Emit {
            target, project, ..
        }) => emit_for_target(project, target),
        Ok(Command::Generate {
            symbol,
            target,
            agent,
            jobs,
            project,
            ..
        }) => generate_for_target(project, target, symbol, agent, jobs),
        Ok(Command::Prompt {
            symbol,
            project,
            format,
        }) => prompt_for_target(project, symbol, format),
        Ok(Command::Deploy {
            output,
            replace,
            project,
            ..
        }) => deploy_for_target(project, output, replace),
        Ok(Command::Diff {
            baseline,
            exit_code,
            project,
            format,
        }) => diff_for_target(project, baseline, exit_code, format),
        Ok(Command::Verify { project, .. }) => verify_for_target(project),
        Err(message) => {
            eprintln!("error: {message}");
            eprint!("{USAGE}");
            2
        }
    }
}

fn run_json(arguments: Vec<OsString>) -> i32 {
    let mut human_arguments = Vec::with_capacity(arguments.len());
    let mut index = 0;
    while index < arguments.len() {
        if arguments[index] == "--format"
            && arguments
                .get(index + 1)
                .is_some_and(|value| value == "json")
        {
            index += 2;
        } else {
            human_arguments.push(arguments[index].clone());
            index += 1;
        }
    }
    let command = parse_command(&human_arguments).ok();
    let diagnostic_target = command
        .as_ref()
        .map(command_diagnostic_target)
        .unwrap_or(TargetLanguage::Python);
    let init_no_sync = matches!(
        command.as_ref(),
        Some(Command::Init {
            target: TargetLanguage::Python,
            no_sync: true,
            ..
        })
    );
    let project_paths = command.as_ref().and_then(json_project_paths);
    let output = match std::env::current_exe().and_then(|executable| {
        ProcessCommand::new(executable)
            .args(&human_arguments)
            .output()
    }) {
        Ok(output) => output,
        Err(error) => {
            let report = DiagnosticReport {
                diagnostics: vec![Diagnostic::error(
                    code::INTERNAL,
                    format!("execute JSON-mode command: {error}"),
                    Span::new(0, 0),
                )],
            };
            let bytes = report
                .canonical_json(&SourceMap::default())
                .expect("diagnostic report is serializable");
            let _ = std::io::stdout().write_all(&bytes);
            return 1;
        }
    };
    let exit_code = output.status.code().unwrap_or(1);
    let error_code = match exit_code {
        2 => code::CLI_USAGE,
        3 => code::SYNTAX,
        4 if diagnostic_target == TargetLanguage::Kotlin => code::KOTLIN,
        4 if diagnostic_target == TargetLanguage::Dart => code::DART,
        4 => code::PYTHON,
        5 => code::AGENT,
        6 => code::FILESYSTEM,
        1 => code::INTERNAL,
        _ => code::CONTRACT,
    };
    let mut diagnostics = Vec::new();
    let mut sources = SourceMap::default();
    let mut source_ids = BTreeMap::new();
    for (source_order, line) in String::from_utf8_lossy(&output.stderr)
        .lines()
        .filter(|line| !line.is_empty())
        .enumerate()
    {
        let warning = line.starts_with("warning: ");
        let body = line
            .strip_prefix(if warning { "warning: " } else { "error: " })
            .unwrap_or(line);
        let mut diagnostic = if warning {
            let warning_code = match diagnostic_target {
                TargetLanguage::Python => code::SHADOW_SPECIFICATION,
                TargetLanguage::Kotlin => code::KOTLIN,
                TargetLanguage::Dart => code::DART,
            };
            Diagnostic::warning(warning_code, body, Span::new(0, 0))
        } else {
            Diagnostic::error(error_code, body, Span::new(0, 0))
        };
        diagnostic.source_order = source_order;
        if let Some(paths) = &project_paths
            && let Some((location, message)) = body.rsplit_once(": ")
            && let Some((path, range)) = location.rsplit_once(':')
            && let Some((start, end)) = range.split_once('-')
            && let (Ok(start), Ok(end)) = (start.parse::<usize>(), end.parse::<usize>())
        {
            let relative = PathBuf::from(path);
            let absolute = paths
                .root
                .join(&relative)
                .is_file()
                .then(|| paths.root.join(&relative))
                .unwrap_or_else(|| paths.source_dir.join(&relative));
            if let Ok(bytes) = fs::read(&absolute) {
                let source_path = absolute
                    .strip_prefix(&paths.root)
                    .unwrap_or(&absolute)
                    .to_path_buf();
                let file = *source_ids
                    .entry(source_path.clone())
                    .or_insert_with(|| sources.add(source_path, bytes));
                diagnostic.message = message.to_owned();
                diagnostic.span = Span::new(start, end);
                diagnostic.source_span = Some(SourceSpan {
                    file,
                    start_byte: start,
                    end_byte: end,
                });
            }
        }
        diagnostics.push(diagnostic);
    }
    let offset = diagnostics.len();
    for (source_order, line) in String::from_utf8_lossy(&output.stdout)
        .lines()
        .filter(|line| !line.is_empty())
        .enumerate()
    {
        let mut diagnostic = if init_no_sync {
            let mut diagnostic = Diagnostic::error(
                code::NAME,
                "run the frozen Python environment sync",
                Span::new(0, 0),
            );
            diagnostic.help.push(line.to_owned());
            diagnostic
        } else {
            Diagnostic::error(code::CONTRACT, line, Span::new(0, 0))
        };
        diagnostic.severity = Severity::Note;
        diagnostic.source_order = offset + source_order;
        diagnostics.push(diagnostic);
    }
    let bytes = DiagnosticReport { diagnostics }
        .canonical_json(&sources)
        .expect("diagnostic report is serializable");
    let _ = std::io::stdout().write_all(&bytes);
    exit_code
}

struct JsonProjectPaths {
    root: PathBuf,
    source_dir: PathBuf,
}

fn command_project_argument(command: &Command) -> Option<&Option<PathBuf>> {
    match command {
        Command::Check { project, .. }
        | Command::Fmt { project, .. }
        | Command::Emit { project, .. }
        | Command::Generate { project, .. }
        | Command::Prompt { project, .. }
        | Command::Verify { project, .. }
        | Command::Deploy { project, .. }
        | Command::Diff { project, .. } => Some(project),
        Command::Init { .. } | Command::Lsp | Command::Help | Command::Version => None,
    }
}

fn command_diagnostic_target(command: &Command) -> TargetLanguage {
    match command {
        Command::Init { target, .. } | Command::Generate { target, .. } => *target,
        Command::Emit {
            target: EmitTarget::Python,
            ..
        } => TargetLanguage::Python,
        Command::Emit {
            target: EmitTarget::Kotlin,
            ..
        } => TargetLanguage::Kotlin,
        Command::Emit {
            target: EmitTarget::Dart,
            ..
        } => TargetLanguage::Dart,
        _ => command_project_argument(command)
            .and_then(|project| {
                project
                    .clone()
                    .or_else(|| std::env::current_dir().ok())
                    .and_then(|root| load_target_language(&root).ok())
            })
            .unwrap_or(TargetLanguage::Python),
    }
}

fn json_project_paths(command: &Command) -> Option<JsonProjectPaths> {
    let root = command_project_argument(command)?
        .clone()
        .or_else(|| std::env::current_dir().ok())?;
    match load_target_language(&root).ok()? {
        TargetLanguage::Python => {
            let (_, paths) = load_config_with_paths(&root).ok()?;
            Some(JsonProjectPaths {
                root: paths.root,
                source_dir: paths.source_dir,
            })
        }
        TargetLanguage::Kotlin => {
            let (_, paths, _) = crate::project::load_kotlin_config_with_paths(&root).ok()?;
            Some(JsonProjectPaths {
                root: paths.root,
                source_dir: paths.source_dir,
            })
        }
        TargetLanguage::Dart => {
            let (_, paths, _) = crate::project::load_dart_config_with_paths(&root).ok()?;
            Some(JsonProjectPaths {
                root: paths.root,
                source_dir: paths.source_dir,
            })
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum OutputFormat {
    Human,
    Json,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum EmitTarget {
    Ir,
    Python,
    Kotlin,
    Dart,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Command {
    Init {
        path: PathBuf,
        target: TargetLanguage,
        name: Option<String>,
        no_sync: bool,
        format: OutputFormat,
    },
    Check {
        source: Option<PathBuf>,
        project: Option<PathBuf>,
        format: OutputFormat,
    },
    Fmt {
        check: bool,
        project: Option<PathBuf>,
        format: OutputFormat,
    },
    Emit {
        target: EmitTarget,
        project: Option<PathBuf>,
        format: OutputFormat,
    },
    Generate {
        symbol: Option<String>,
        target: TargetLanguage,
        agent: Option<AgentKind>,
        jobs: usize,
        project: Option<PathBuf>,
        format: OutputFormat,
    },
    Prompt {
        symbol: String,
        project: Option<PathBuf>,
        format: OutputFormat,
    },
    Verify {
        project: Option<PathBuf>,
        format: OutputFormat,
    },
    Deploy {
        output: Option<PathBuf>,
        replace: bool,
        project: Option<PathBuf>,
        format: OutputFormat,
    },
    Diff {
        baseline: Option<PathBuf>,
        exit_code: bool,
        project: Option<PathBuf>,
        format: OutputFormat,
    },
    Lsp,
    Help,
    Version,
}

pub fn parse_command(arguments: &[OsString]) -> Result<Command, &'static str> {
    if arguments.len() == 1 && matches!(arguments[0].to_str(), Some("--help" | "-h")) {
        return Ok(Command::Help);
    }
    if arguments.len() == 1 && matches!(arguments[0].to_str(), Some("--version" | "-V")) {
        return Ok(Command::Version);
    }
    let Some(command) = arguments.first().and_then(|value| value.to_str()) else {
        return Err("expected a command");
    };
    let values = &arguments[1..];
    match command {
        "init" => parse_init(values),
        "check" => parse_check(values),
        "fmt" => parse_fmt(values),
        "emit" => parse_emit(values),
        "generate" => parse_generate(values),
        "prompt" => parse_prompt(values),
        "lsp" if values.is_empty() => Ok(Command::Lsp),
        "lsp" => Err("`lsp` does not accept options or operands"),
        "verify" => {
            let options = ExistingOptions::parse(values)?;
            Ok(Command::Verify {
                project: options.project,
                format: options.format,
            })
        }
        "deploy" => parse_deploy(values),
        "diff" => parse_diff(values),
        _ => Err("unsupported command"),
    }
}

#[derive(Default)]
struct ExistingOptions {
    project: Option<PathBuf>,
    format: OutputFormat,
}

impl Default for OutputFormat {
    fn default() -> Self {
        Self::Human
    }
}

fn parse_target_language(value: Option<&str>) -> Result<TargetLanguage, &'static str> {
    match value {
        Some("python") => Ok(TargetLanguage::Python),
        Some("kotlin") => Ok(TargetLanguage::Kotlin),
        Some("dart") => Ok(TargetLanguage::Dart),
        _ => Err("`--target` requires `python`, `kotlin`, or `dart`"),
    }
}

impl ExistingOptions {
    fn parse(values: &[OsString]) -> Result<Self, &'static str> {
        let mut options = Self::default();
        let mut index = 0;
        while index < values.len() {
            match values[index].to_str() {
                Some("--project") if options.project.is_none() => {
                    index += 1;
                    let path = values
                        .get(index)
                        .filter(|value| !value.is_empty())
                        .ok_or("`--project` requires a directory")?;
                    options.project = Some(PathBuf::from(path));
                }
                Some("--format") if options.format == OutputFormat::Human => {
                    index += 1;
                    if values.get(index).and_then(|value| value.to_str()) != Some("json") {
                        return Err("`--format` requires `json`");
                    }
                    options.format = OutputFormat::Json;
                }
                Some("--project" | "--format") => return Err("duplicate option"),
                _ => return Err("unexpected option"),
            }
            index += 1;
        }
        Ok(options)
    }
}

fn parse_init(values: &[OsString]) -> Result<Command, &'static str> {
    let mut path = None;
    let mut name = None;
    let mut target = None;
    let mut no_sync = false;
    let mut format = OutputFormat::Human;
    let mut index = 0;
    while index < values.len() {
        match values[index].to_str() {
            Some("--name") if name.is_none() => {
                index += 1;
                name = Some(
                    values
                        .get(index)
                        .and_then(|value| value.to_str())
                        .filter(|value| !value.is_empty())
                        .ok_or("`--name` requires a value")?
                        .to_owned(),
                );
            }
            Some("--target") if target.is_none() => {
                index += 1;
                target = Some(parse_target_language(
                    values.get(index).and_then(|value| value.to_str()),
                )?);
            }
            Some("--no-sync") if !no_sync => no_sync = true,
            Some("--format") if format == OutputFormat::Human => {
                index += 1;
                if values.get(index).and_then(|value| value.to_str()) != Some("json") {
                    return Err("`--format` requires `json`");
                }
                format = OutputFormat::Json;
            }
            Some("--project") => return Err("`init` does not accept `--project`"),
            Some(value) if !value.starts_with('-') && path.is_none() => {
                path = Some(&values[index]);
            }
            None if path.is_none() => {
                path = Some(&values[index]);
            }
            _ => return Err("unexpected or duplicate option"),
        }
        index += 1;
    }
    let path = path.ok_or("`init` requires a path")?;
    Ok(Command::Init {
        path: PathBuf::from(path),
        target: target.unwrap_or(TargetLanguage::Python),
        name,
        no_sync,
        format,
    })
}
fn parse_check(values: &[OsString]) -> Result<Command, &'static str> {
    let mut source = None;
    let mut options = ExistingOptions::default();
    let mut index = 0;
    while index < values.len() {
        match values[index].to_str() {
            Some("--project") if options.project.is_none() => {
                index += 1;
                options.project = Some(PathBuf::from(
                    values
                        .get(index)
                        .filter(|value| !value.is_empty())
                        .ok_or("`--project` requires a directory")?,
                ));
            }
            Some("--format") if options.format == OutputFormat::Human => {
                index += 1;
                if values.get(index).and_then(|value| value.to_str()) != Some("json") {
                    return Err("`--format` requires `json`");
                }
                options.format = OutputFormat::Json;
            }
            Some(value) if !value.starts_with('-') && source.is_none() => {
                source = Some(PathBuf::from(value))
            }
            _ => return Err("unexpected or duplicate option"),
        }
        index += 1;
    }
    Ok(Command::Check {
        source,
        project: options.project,
        format: options.format,
    })
}

fn parse_fmt(values: &[OsString]) -> Result<Command, &'static str> {
    let mut check = false;
    let mut retained = Vec::new();
    for value in values {
        if value == "--check" && !check {
            check = true;
        } else {
            retained.push(value.clone());
        }
    }
    let options = ExistingOptions::parse(&retained)?;
    Ok(Command::Fmt {
        check,
        project: options.project,
        format: options.format,
    })
}

fn parse_emit(values: &[OsString]) -> Result<Command, &'static str> {
    let target = match values.first().and_then(|value| value.to_str()) {
        Some("ir") => EmitTarget::Ir,
        Some("python") => EmitTarget::Python,
        Some("kotlin") => EmitTarget::Kotlin,
        Some("dart") => EmitTarget::Dart,
        _ => return Err("expected `emit ir`, `emit python`, `emit kotlin`, or `emit dart`"),
    };
    let options = ExistingOptions::parse(&values[1..])?;
    Ok(Command::Emit {
        target,
        project: options.project,
        format: options.format,
    })
}

fn parse_generate(values: &[OsString]) -> Result<Command, &'static str> {
    let mut symbol = None;
    let mut agent = None;
    let mut target = None;
    let mut jobs = None;
    let mut options = ExistingOptions::default();
    let mut index = 0;
    while index < values.len() {
        match values[index].to_str() {
            Some("--agent") if agent.is_none() => {
                index += 1;
                agent = match values.get(index).and_then(|value| value.to_str()) {
                    Some("claude") => Some(AgentKind::Claude),
                    Some("codex") => Some(AgentKind::Codex),
                    Some("omp") => Some(AgentKind::Omp),
                    _ => return Err("`--agent` requires `codex`, `claude`, or `omp`"),
                };
            }
            Some("--target") if target.is_none() => {
                index += 1;
                target = Some(parse_target_language(
                    values.get(index).and_then(|value| value.to_str()),
                )?);
            }
            Some("-j" | "--jobs") if jobs.is_none() => {
                index += 1;
                jobs = Some(
                    values
                        .get(index)
                        .and_then(|value| value.to_str())
                        .and_then(|value| value.parse::<usize>().ok())
                        .filter(|value| (1..=64).contains(value))
                        .ok_or("`--jobs` requires an integer from 1 to 64")?,
                );
            }
            Some("--project") if options.project.is_none() => {
                index += 1;
                options.project = Some(PathBuf::from(
                    values
                        .get(index)
                        .filter(|value| !value.is_empty())
                        .ok_or("`--project` requires a directory")?,
                ));
            }
            Some("--format") if options.format == OutputFormat::Human => {
                index += 1;
                if values.get(index).and_then(|value| value.to_str()) != Some("json") {
                    return Err("`--format` requires `json`");
                }
                options.format = OutputFormat::Json;
            }
            Some(value) if !value.starts_with('-') && symbol.is_none() => {
                symbol = Some(value.to_owned())
            }
            _ => return Err("unexpected or duplicate option"),
        }
        index += 1;
    }
    let Some(target) = target else {
        return Err("`generate` requires `--target python|kotlin|dart`");
    };
    Ok(Command::Generate {
        target,
        symbol,
        agent,
        jobs: jobs.unwrap_or(1),
        project: options.project,
        format: options.format,
    })
}

fn parse_prompt(values: &[OsString]) -> Result<Command, &'static str> {
    let mut symbol = None;
    let mut options = ExistingOptions::default();
    let mut index = 0;
    while index < values.len() {
        match values[index].to_str() {
            Some("--project") if options.project.is_none() => {
                index += 1;
                options.project = Some(PathBuf::from(
                    values
                        .get(index)
                        .filter(|value| !value.is_empty())
                        .ok_or("`--project` requires a directory")?,
                ));
            }
            Some("--format") if options.format == OutputFormat::Human => {
                index += 1;
                if values.get(index).and_then(|value| value.to_str()) != Some("json") {
                    return Err("`--format` requires `json`");
                }
                options.format = OutputFormat::Json;
            }
            Some(value) if !value.starts_with('-') && symbol.is_none() => {
                symbol = Some(value.to_owned())
            }
            _ => return Err("unexpected or duplicate option"),
        }
        index += 1;
    }
    let Some(symbol) = symbol else {
        return Err("`prompt` requires a fully qualified callable");
    };
    Ok(Command::Prompt {
        symbol,
        project: options.project,
        format: options.format,
    })
}

fn parse_deploy(values: &[OsString]) -> Result<Command, &'static str> {
    let mut output = None;
    let mut replace = false;
    let mut retained = Vec::new();
    let mut index = 0;
    while index < values.len() {
        if values[index] == "--output" {
            if output.is_some() {
                return Err("duplicate option");
            }
            index += 1;
            output = Some(PathBuf::from(
                values
                    .get(index)
                    .filter(|value| {
                        !value.is_empty() && !value.as_encoded_bytes().starts_with(b"-")
                    })
                    .ok_or("`--output` requires a directory")?,
            ));
        } else if values[index] == "--replace" {
            if replace {
                return Err("duplicate option");
            }
            replace = true;
        } else {
            retained.push(values[index].clone());
        }
        index += 1;
    }
    let options = ExistingOptions::parse(&retained)?;
    Ok(Command::Deploy {
        output,
        replace,
        project: options.project,
        format: options.format,
    })
}

fn deploy_project(
    project_argument: Option<PathBuf>,
    output: Option<PathBuf>,
    replace: bool,
) -> i32 {
    let Ok(root) = project_root(project_argument) else {
        return 2;
    };
    let session = match ProjectSession::acquire(&root) {
        Ok(session) => session,
        Err(error) => {
            eprintln!("error: {error}");
            return 6;
        }
    };
    let (config, paths) = match load_config_with_paths(session.root()) {
        Ok(project) => project,
        Err(error) => {
            eprintln!("error: {error}");
            return 2;
        }
    };
    let target = match output {
        Some(path) if path.is_absolute() => path,
        Some(path) => match std::env::current_dir() {
            Ok(cwd) => cwd.join(path),
            Err(error) => {
                eprintln!("error: determine deployment directory: {error}");
                return 6;
            }
        },
        None => paths.root.join("dist").join(format!(
            "{}-{}",
            config.project.name, config.project.version
        )),
    };
    if replace {
        match fs::symlink_metadata(&target) {
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
                if let Err(error) = deployment_target(&paths, &target, true) {
                    eprintln!("error: {error}");
                    return 6;
                }
            }
            Err(error) => {
                eprintln!(
                    "error: deployment output is not a replaceable Cott deployment: inspect {}: {error}",
                    target.display()
                );
                return 6;
            }
            Ok(_) => {
                let context = match python_replace_context(&paths, &config.project.name) {
                    Ok(context) => context,
                    Err(error) => {
                        eprintln!("error: {error}");
                        return 6;
                    }
                };
                if let Err(error) = crate::deploy::require_replaceable(&context, &target) {
                    eprintln!("error: {error}");
                    return 6;
                }
            }
        }
    } else if let Err(error) = deployment_target(&paths, &target, false) {
        eprintln!("error: {error}");
        return 6;
    }
    let (files, snapshot) = match deployment_files(&config, &paths) {
        Ok(plan) => plan,
        Err(error) => {
            eprintln!("error: {error}");
            return 4;
        }
    };
    match publish_deployment(
        &paths,
        &target,
        &files,
        &snapshot,
        replace,
        &config.project.name,
    ) {
        Ok(()) => {
            println!("{}", display_path(&paths.root, &target));
            0
        }
        Err(error) => {
            eprintln!("error: {error}");
            6
        }
    }
}

fn deployment_files(
    config: &crate::manifest::ProjectConfig,
    paths: &ProjectPaths,
) -> Result<(BTreeMap<PathBuf, Vec<u8>>, InputSnapshot), String> {
    let artifact_root = artifact_root_for_paths(paths)?;
    let prefix = artifact_root
        .strip_prefix(&paths.root)
        .map_err(|error| error.to_string())?;
    let generation = prefix.join("generation.json");
    let initial = InputSnapshot::capture(&paths.root, [generation.clone()])
        .map_err(|error| error.to_string())?;
    let bytes = fs::read(paths.root.join(&generation)).map_err(|error| {
        format!("read generation record (run `cott emit python` and `cott verify` first): {error}")
    })?;
    let record = GenerationRecord::parse(&bytes)?;
    if !record.current.verified {
        return Err(
            "deployment requires a verified current snapshot; run `cott verify`".to_owned(),
        );
    }
    if !record.current.unresolved.is_empty() {
        return Err("deployment refuses unresolved implementations".to_owned());
    }
    if !record.current.semantic_coverage.policy.passed {
        return Err("deployment refuses a failed semantic coverage policy".to_owned());
    }
    if record.current.project_version != config.project.version
        || record.current.tools["compiler"]["version"] != env!("CARGO_PKG_VERSION")
        || record.current.tools["runtime"]["version"] != env!("CARGO_PKG_VERSION")
    {
        return Err(
            "deployment snapshot is stale; emit and verify with the current compiler".to_owned(),
        );
    }
    let sources = discover_sources_from_paths(paths).map_err(|error| error.to_string())?;
    let mut inputs = collect_input_hashes(config, paths, &sources)?;
    for implementation in record
        .current
        .implementations
        .as_array()
        .ok_or("invalid implementations")?
    {
        let source = PathBuf::from(
            implementation["source_origin"]
                .as_str()
                .ok_or("missing implementation source")?,
        );
        if !safe_relative_path(&source)
            || !paths
                .root
                .join(&source)
                .starts_with(&paths.python_source_dir)
        {
            return Err(format!(
                "unsafe implementation source: {}",
                source.display()
            ));
        }
        InputSnapshot::capture(&paths.root, [source.clone()]).map_err(|error| error.to_string())?;
        let source_bytes = fs::read(paths.root.join(&source))
            .map_err(|error| format!("read {}: {error}", source.display()))?;
        inputs.insert(
            source.to_string_lossy().into_owned(),
            format!("sha256:{}", sha256_hex(&source_bytes)),
        );
    }
    if serde_json::to_value(&inputs).map_err(|error| error.to_string())? != record.current.inputs {
        return Err(
            "deployment inputs changed; emit and verify the current project first".to_owned(),
        );
    }
    let mut expected = inputs
        .into_iter()
        .map(|(path, hash)| (PathBuf::from(path), hash))
        .collect::<BTreeMap<_, _>>();
    for (path, hash) in &record.current.managed_files {
        let path = PathBuf::from(path);
        if !safe_relative_path(&path) || !path.starts_with(prefix) || path == generation {
            return Err(format!("unsafe managed artifact: {}", path.display()));
        }
        expected.insert(path, hash.clone());
    }
    expected.insert(generation.clone(), format!("sha256:{}", sha256_hex(&bytes)));
    let captured = InputSnapshot::capture_expected(&paths.root, expected.clone(), [])
        .map_err(|error| error.to_string())?;
    if captured.files.get(&generation) != initial.files.get(&generation) {
        return Err("generation record changed during deployment".to_owned());
    }
    let mut files = BTreeMap::new();
    let actual = collect_tree(&artifact_root)?;
    for (path, bytes) in actual {
        if path == Path::new("generation.json") {
            continue;
        }
        let original = prefix.join(&path).to_string_lossy().into_owned();
        if record.current.managed_files.get(&original)
            != Some(&format!("sha256:{}", sha256_hex(&bytes)))
        {
            return Err(format!(
                "unexpected or modified managed artifact: {original}"
            ));
        }
        if path.starts_with("python") && path.extension().is_some_and(|ext| ext == "py") {
            files.insert(path, bytes);
        }
    }
    if !files.contains_key(Path::new("python/cott_runtime/__init__.py")) {
        return Err("deployment is missing the generated Python runtime".to_owned());
    }
    let generated_packages = files
        .keys()
        .filter_map(|path| {
            path.strip_prefix("python")
                .ok()?
                .components()
                .next()
                .map(|top| PathBuf::from(top.as_os_str()).with_extension(""))
        })
        .collect::<BTreeSet<_>>();
    for (path, bytes) in crate::deploy::adapter_files(paths, &record)? {
        let relative = path
            .strip_prefix("python")
            .map_err(|error| error.to_string())?;
        let source = paths.python_source_dir.join(relative);
        let source = source
            .strip_prefix(&paths.root)
            .map_err(|error| error.to_string())?;
        expected.insert(
            source.to_path_buf(),
            format!("sha256:{}", sha256_hex(&bytes)),
        );
        // A distinct authored top-level package must not shadow a generated package.
        let top = relative.components().next().ok_or("empty adapter path")?;
        if generated_packages.contains(&PathBuf::from(top.as_os_str()).with_extension("")) {
            return Err(format!(
                "deployment adapter collides with generated package: {}",
                path.display()
            ));
        }
        files.insert(path, bytes);
    }
    let version = record.current.tools["python"]["version"]
        .as_str()
        .ok_or("missing target Python version")?;
    if !supports_python_version(version) || version.bytes().any(|byte| byte.is_ascii_whitespace()) {
        return Err("invalid deployment Python version".to_owned());
    }
    files.insert(
        PathBuf::from(".python-version"),
        format!("{version}\n").into_bytes(),
    );
    let requirements = deployment_requirements(paths)?;
    let requirement_text = std::str::from_utf8(&requirements).map_err(|error| error.to_string())?;
    let exported = requirement_text
        .lines()
        .filter_map(|line| {
            let (name, rest) = line.split_once("==")?;
            let version = rest.split([';', ' ', '\\']).next()?;
            Some((name, version))
        })
        .collect::<BTreeSet<_>>();
    for dependency in record
        .current
        .dependencies
        .as_array()
        .ok_or("invalid dependency records")?
    {
        if dependency.get("installed").is_none() {
            continue;
        }
        let name = dependency["name"]
            .as_str()
            .ok_or("missing dependency name")?;
        let version = dependency["version"]
            .as_str()
            .ok_or("missing dependency version")?;
        if !exported.contains(&(name, version)) {
            return Err(format!(
                "runtime dependency {name}=={version} is absent from production dependencies"
            ));
        }
    }
    files.insert(PathBuf::from("requirements.txt"), requirements);
    files.insert(PathBuf::from("generation.json"), bytes);
    let snapshot = InputSnapshot::capture_expected(&paths.root, expected, [])
        .map_err(|error| error.to_string())?;
    for (path, before) in captured.files {
        if snapshot.files.get(&path) != Some(&before) {
            return Err(format!("deployment input changed: {}", path.display()));
        }
    }
    Ok((files, snapshot))
}

fn deployment_requirements(paths: &ProjectPaths) -> Result<Vec<u8>, String> {
    let metadata = fs::read(paths.python_source_dir.join("pyproject.toml"))
        .map_err(|error| format!("read deployment dependencies: {error}"))?;
    let project: toml::Value =
        toml::from_str(std::str::from_utf8(&metadata).map_err(|error| error.to_string())?)
            .map_err(|error| error.to_string())?;
    if project["project"]["dependencies"]
        .as_array()
        .is_some_and(Vec::is_empty)
    {
        return Ok(Vec::new());
    }
    let lock = paths
        .lockfile
        .as_ref()
        .ok_or("deployment dependencies require a lockfile")?;
    let lock = fs::read(lock).map_err(|error| format!("read deployment lockfile: {error}"))?;
    let uv = resolve_executable("uv")?;
    let environment = uv_environment(&uv)?;
    let version = run_clean(
        &uv,
        &["--version"],
        &paths.root,
        &environment,
        Duration::from_secs(30),
    )?;
    if version.status != Some(0)
        || !supports_uv_version(String::from_utf8_lossy(&version.stdout).trim())
    {
        return Err("deployment dependency export requires uv >=0.12.3".to_owned());
    }
    // Export a frozen copy: never let uv discover a parent workspace or mutate the project.
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|error| error.to_string())?
        .as_nanos();
    let scratch =
        std::env::temp_dir().join(format!("cott-deploy-deps-{}-{nonce}", std::process::id()));
    DirBuilder::new()
        .mode(0o700)
        .create(&scratch)
        .map_err(|error| format!("create dependency export workspace: {error}"))?;
    let result = (|| {
        write_private(&scratch.join("pyproject.toml"), &metadata)?;
        write_private(&scratch.join("uv.lock"), &lock)?;
        let output = run_clean(
            &uv,
            &[
                "export",
                "--frozen",
                "--offline",
                "--no-default-groups",
                "--no-dev",
                "--no-emit-project",
                "--no-editable",
                "--no-header",
                "--no-annotate",
                "--no-config",
                "--no-cache",
                "--no-python-downloads",
                "--format",
                "requirements.txt",
            ],
            &scratch,
            &environment,
            Duration::from_secs(30),
        )?;
        if output.status != Some(0) {
            return Err(format!(
                "export deployment dependencies: {}",
                String::from_utf8_lossy(&output.stderr).trim()
            ));
        }
        let requirements =
            std::str::from_utf8(&output.stdout).map_err(|error| error.to_string())?;
        // Local/editable/VCS requirements would silently depend on the authoring machine.
        for line in requirements
            .lines()
            .map(str::trim)
            .filter(|line| !line.is_empty())
        {
            if !line.starts_with("--hash=sha256:")
                && !line.split_once("==").is_some_and(|(name, _)| {
                    !name.is_empty()
                        && name.bytes().all(|byte| {
                            byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_' | b'.')
                        })
                })
            {
                return Err("deployment requires locked registry dependencies, not local/editable/VCS sources".to_owned());
            }
        }
        Ok(output.stdout)
    })();
    fs::remove_dir_all(&scratch)
        .map_err(|error| format!("remove dependency export workspace: {error}"))?;
    result
}

fn deployment_target(paths: &ProjectPaths, target: &Path, replace: bool) -> Result<(), String> {
    if !target.is_absolute()
        || target
            .components()
            .any(|component| !matches!(component, Component::RootDir | Component::Normal(_)))
        || target.file_name().is_none()
    {
        return Err(
            "deployment output must be a normalized directory path without `.` or `..`".to_owned(),
        );
    }
    let artifacts = artifact_root_for_paths(paths)?;
    if paths.root.starts_with(target)
        || [
            &paths.source_dir,
            &paths.python_source_dir,
            &artifacts,
            &paths.stubs_dir,
            &paths.root.join(".cott"),
            &paths.root.join(".venv"),
        ]
        .iter()
        .any(|source| target.starts_with(source))
    {
        return Err("deployment output overlaps project inputs or managed artifacts".to_owned());
    }
    for ancestor in target.ancestors() {
        if replace && ancestor == target {
            continue;
        }
        match fs::symlink_metadata(ancestor) {
            Ok(metadata)
                if ancestor == target
                    || !metadata.is_dir()
                    || metadata.file_type().is_symlink() =>
            {
                return Err(format!(
                    "deployment output exists or has an unsafe parent: {}",
                    ancestor.display()
                ));
            }
            Ok(_) => {}
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {}
            Err(error) => {
                return Err(format!(
                    "inspect deployment output {}: {error}",
                    ancestor.display()
                ));
            }
        }
    }
    Ok(())
}

fn publish_deployment(
    paths: &ProjectPaths,
    target: &Path,
    files: &BTreeMap<PathBuf, Vec<u8>>,
    snapshot: &InputSnapshot,
    replace: bool,
    project_name: &str,
) -> Result<(), String> {
    deployment_target(paths, target, replace)?;
    let parent = target.parent().ok_or("deployment output has no parent")?;
    fs::create_dir_all(parent).map_err(|error| format!("create deployment parent: {error}"))?;
    deployment_target(paths, target, replace)?;
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|error| error.to_string())?
        .as_nanos();
    let temporary = parent.join(format!(".cott-deploy-{}-{nonce}", std::process::id()));
    DirBuilder::new()
        .mode(0o700)
        .create(&temporary)
        .map_err(|error| format!("create deployment staging: {error}"))?;
    let result = (|| {
        for (relative, bytes) in files {
            if !safe_relative_path(relative) {
                return Err(format!("unsafe deployment member: {}", relative.display()));
            }
            let path = temporary.join(relative);
            fs::create_dir_all(path.parent().ok_or("deployment member has no parent")?)
                .map_err(|error| format!("create deployment package: {error}"))?;
            let mut file = OpenOptions::new()
                .write(true)
                .create_new(true)
                .mode(0o644)
                .open(&path)
                .map_err(|error| format!("create deployment file {}: {error}", path.display()))?;
            file.write_all(bytes)
                .and_then(|_| file.sync_all())
                .map_err(|error| format!("write deployment file {}: {error}", path.display()))?;
        }
        let current = InputSnapshot::capture(&paths.root, snapshot.files.keys().cloned())
            .map_err(|error| error.to_string())?;
        if &current != snapshot {
            return Err("project changed while packaging deployment".to_owned());
        }
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&temporary, fs::Permissions::from_mode(0o755))
            .map_err(|error| format!("set deployment directory permissions: {error}"))?;
        sync_tree(&temporary)?;
        deployment_target(paths, target, replace)?;
        let existing = match fs::symlink_metadata(target) {
            Ok(_) if replace => true,
            Ok(_) => {
                return Err(format!(
                    "deployment output exists or has an unsafe parent: {}",
                    target.display()
                ));
            }
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => false,
            Err(error) => {
                return Err(format!(
                    "inspect deployment output {}: {error}",
                    target.display()
                ));
            }
        };
        if existing {
            let context = python_replace_context(paths, project_name)?;
            crate::deploy::require_replaceable(&context, target)?;
            crate::deploy::publish_replace(&temporary, target)
        } else {
            rename_noreplace(&temporary, target)?;
            File::open(parent)
                .and_then(|directory| directory.sync_all())
                .map_err(|error| format!("sync deployment parent: {error}"))
        }
    })();
    if temporary.exists() {
        fs::remove_dir_all(&temporary)
            .map_err(|error| format!("remove deployment staging: {error}"))?;
    }
    result
}

fn parse_diff(values: &[OsString]) -> Result<Command, &'static str> {
    let mut baseline = None;
    let mut exit_code = false;
    let mut retained = Vec::new();
    let mut index = 0;
    while index < values.len() {
        match values[index].to_str() {
            Some("--baseline") if baseline.is_none() => {
                index += 1;
                baseline = Some(PathBuf::from(
                    values
                        .get(index)
                        .filter(|value| !value.is_empty())
                        .ok_or("`--baseline` requires a file")?,
                ));
            }
            Some("--exit-code") if !exit_code => exit_code = true,
            _ => retained.push(values[index].clone()),
        }
        index += 1;
    }
    let options = ExistingOptions::parse(&retained)?;
    Ok(Command::Diff {
        baseline,
        exit_code,
        project: options.project,
        format: options.format,
    })
}

fn audit_authored_python(paths: &ProjectPaths) -> Result<(), Vec<String>> {
    let mut diagnostics = discover_python_sources(&paths.python_source_dir)
        .map_err(|error| vec![format!("cannot audit authored Python: {error}")])?
        .into_iter()
        .flat_map(|source| {
            let display = source
                .disk_path
                .strip_prefix(&paths.root)
                .unwrap_or(&source.disk_path)
                .to_path_buf();
            audit_facade_file(&display, &source.source, PythonFileRole::Authored)
                .into_iter()
                .map(|diagnostic| {
                    diagnostic.range.map_or_else(
                        || format!("{}: {}", diagnostic.path.display(), diagnostic.message),
                        |range| {
                            format!(
                                "{}:{}-{}: {}",
                                diagnostic.path.display(),
                                range.start,
                                range.end,
                                diagnostic.message
                            )
                        },
                    )
                })
                .collect::<Vec<_>>()
        })
        .collect::<Vec<_>>();
    diagnostics.sort();
    diagnostics.dedup();
    (!diagnostics.is_empty())
        .then_some(diagnostics)
        .map_or(Ok(()), Err)
}
fn supports_shadow_facet(declaration: &serde_json::Value, facet: ShadowFacet) -> bool {
    let contract = declaration.get("contract");
    match facet {
        ShadowFacet::Return => declaration.get("return_type").is_some(),
        ShadowFacet::Limit => false,
        ShadowFacet::Error => contract
            .and_then(|contract| contract.get("clauses"))
            .and_then(serde_json::Value::as_array)
            .is_some_and(|clauses| {
                clauses.iter().any(|clause| {
                    clause.get("kind").and_then(serde_json::Value::as_str) == Some("error")
                })
            }),
        ShadowFacet::Atomicity | ShadowFacet::Cleanup => contract
            .and_then(|contract| contract.get("effects"))
            .and_then(serde_json::Value::as_array)
            .is_some_and(|effects| {
                effects.iter().any(|effect| {
                    effect.get("key").and_then(serde_json::Value::as_str) == Some(facet.as_str())
                })
            }),
    }
}

fn shadow_warnings(
    config: &crate::manifest::ProjectConfig,
    paths: &ProjectPaths,
    ir: &crate::ir::CanonicalIr,
) -> Result<Vec<String>, String> {
    let mut facets = BTreeMap::new();
    let mut warnings = Vec::new();
    for module in &ir.modules {
        let value = crate::ir::load(&module.bytes)?;
        for declaration in value
            .get("declarations")
            .and_then(serde_json::Value::as_array)
            .into_iter()
            .flatten()
            .filter(|declaration| {
                declaration.get("kind").and_then(serde_json::Value::as_str) == Some("function")
            })
        {
            let symbol = declaration
                .get("name")
                .and_then(serde_json::Value::as_str)
                .ok_or("function declaration has no canonical name")?
                .to_owned();
            let supported = ShadowFacet::ALL
                .into_iter()
                .filter(|facet| supports_shadow_facet(declaration, *facet))
                .collect::<BTreeSet<_>>();
            if let Some(doc) = declaration.get("doc") {
                if let Some(text) = doc.get("text").and_then(serde_json::Value::as_str) {
                    let span = doc.get("span").ok_or("function doc has no span")?;
                    let start = span
                        .get("start_byte")
                        .and_then(serde_json::Value::as_u64)
                        .ok_or("function doc has invalid span")?
                        as usize;
                    for candidate in scan_doc_candidates(text) {
                        if !supported.contains(&candidate.facet) {
                            warnings.push(format!(
                                "{}:{}-{}: {}: possible shadow specification: {} duty is stated in documentation for `{symbol}` but has no formal evidence",
                                display_path(&paths.root, &module.source),
                                start + candidate.span.start,
                                start + candidate.span.end,
                                code::SHADOW_SPECIFICATION,
                                candidate.facet.as_str(),
                            ));
                        }
                    }
                }
            }
            facets.insert(symbol, supported);
        }
    }
    if let Some(rule_path) = &config.generator.rules {
        let path = paths.root.join(rule_path);
        let parsed = parse_domain_rules(
            &path,
            &fs::read(&path)
                .map_err(|error| format!("read generator rules {}: {error}", path.display()))?,
        );
        if let Some(diagnostic) = parsed.diagnostics.first() {
            return Err(format!(
                "{}:{}-{}: {}",
                display_path(&paths.root, &parsed.path),
                diagnostic.span.start,
                diagnostic.span.end,
                diagnostic.message
            ));
        }
        for rule in parsed.rules {
            if !facets
                .get(&rule.symbol)
                .is_some_and(|supported| supported.contains(&rule.facet))
            {
                warnings.push(format!(
                    "{}:{}-{}: {}: possible shadow specification: {} duty is stated in generator rules for `{}` but has no formal evidence",
                    display_path(&paths.root, &parsed.path),
                    rule.payload_span.start,
                    rule.payload_span.end,
                    code::SHADOW_SPECIFICATION,
                    rule.facet.as_str(),
                    rule.symbol,
                ));
            }
        }
    }
    warnings.sort();
    warnings.dedup();
    Ok(warnings)
}

struct PlannedProject {
    session: ProjectSession,
    config: crate::manifest::ProjectConfig,
    paths: ProjectPaths,
    ir: crate::ir::CanonicalIr,
    emission: Emission,
    input_snapshot: InputSnapshot,
}
fn plan(project_argument: Option<PathBuf>) -> Result<PlannedProject, i32> {
    let Ok(root) = project_root(project_argument) else {
        return Err(2);
    };
    let session = match ProjectSession::acquire(&root) {
        Ok(session) => session,
        Err(error) => {
            eprintln!("error: {error}");
            return Err(6);
        }
    };
    plan_with_session(session)
}

fn plan_with_session(session: ProjectSession) -> Result<PlannedProject, i32> {
    let root = session.root().to_path_buf();
    let (config, paths) = match load_config_with_paths(&root) {
        Ok(config) => config,
        Err(error) => {
            eprintln!("error: {error}");
            return Err(2);
        }
    };
    if let Err(message) = artifact_root_for_paths(&paths) {
        eprintln!("error: {message}");
        return Err(2);
    }
    if let Err(diagnostics) = audit_authored_python(&paths) {
        for diagnostic in diagnostics {
            eprintln!("error: {diagnostic}");
        }
        return Err(4);
    }
    let sources = match discover_sources_from_paths(&paths) {
        Ok(sources) => sources,
        Err(error) => {
            eprintln!("error: {error}");
            return Err(2);
        }
    };
    let mut input_hashes = match collect_input_hashes(&config, &paths, &sources) {
        Ok(inputs) => inputs,
        Err(message) => {
            eprintln!("error: {message}");
            return Err(2);
        }
    };
    let parsed = match parse_project(sources) {
        Ok(parsed) => parsed,
        Err(diagnostics) => {
            print_project_diagnostics(&diagnostics);
            return Err(3);
        }
    };
    let custom_effects = config.effects.keys().cloned().collect();
    let hir = match lower_with_effects(&paths.source_dir, parsed, &custom_effects) {
        Ok(hir) => hir,
        Err(diagnostics) => {
            print_project_diagnostics(&diagnostics);
            return Err(3);
        }
    };
    let ir = match render(&hir) {
        Ok(ir) => ir,
        Err(error) => {
            eprintln!("error: {error}");
            return Err(1);
        }
    };
    match shadow_warnings(&config, &paths, &ir) {
        Ok(warnings) => {
            for warning in warnings {
                eprintln!("warning: {warning}");
            }
        }
        Err(error) => {
            eprintln!("error: {error}");
            return Err(3);
        }
    }
    let plan = match PythonArtifactPlan::from_ir(&ir) {
        Ok(plan) => plan,
        Err(error) => {
            eprintln!("error: {error}");
            return Err(1);
        }
    };
    let resolution = match resolve_implementations(&config, &paths, &plan) {
        Ok(resolution) => resolution,
        Err(diagnostics) => {
            for diagnostic in diagnostics {
                eprintln!(
                    "error: {}: {}",
                    display_path(&paths.root, &diagnostic.path),
                    diagnostic.message
                );
            }
            return Err(4);
        }
    };
    if let Some(stale) = resolution.stale.first() {
        eprintln!(
            "error: {}: stale durable agent implementation",
            display_path(&paths.root, stale)
        );
        return Err(4);
    }
    let bindings = resolution.resolved;
    add_binding_input_hashes(&paths, &bindings, &mut input_hashes);
    let input_snapshot =
        match capture_resolution_inputs(&paths.root, &input_hashes, &resolution.pending_sources) {
            Ok(snapshot) => snapshot,
            Err(error) => {
                eprintln!("error: {error}");
                return Err(6);
            }
        };
    let mut emission = match emit(&config, &plan, &ir, &bindings) {
        Ok(emission) => emission,
        Err(diagnostics) => {
            print_emit_diagnostics(&paths, &diagnostics);
            return Err(4);
        }
    };
    if let Err(message) = enrich_generation_record(&paths, &config, input_hashes, &mut emission) {
        eprintln!("error: {message}");
        return Err(4);
    }
    Ok(PlannedProject {
        session,
        config,
        paths,
        ir,
        emission,
        input_snapshot,
    })
}
fn collect_input_hashes(
    config: &crate::manifest::ProjectConfig,
    paths: &ProjectPaths,
    sources: &[crate::compiler::SourceFile],
) -> Result<BTreeMap<String, String>, String> {
    let mut files = vec![paths.manifest.clone()];
    files.extend(
        sources
            .iter()
            .map(|source| paths.source_dir.join(&source.path)),
    );
    if let Some(lockfile) = &paths.lockfile {
        files.push(lockfile.clone());
    }
    for path in [
        paths.root.join("AGENTS.md"),
        paths.python_source_dir.join("pyproject.toml"),
    ] {
        if path.exists() {
            files.push(path);
        }
    }
    if let Some(rules) = &config.generator.rules {
        files.push(paths.root.join(rules));
    }
    files.sort();
    files.dedup();
    files
        .into_iter()
        .map(|path| {
            let bytes = fs::read(&path)
                .map_err(|error| format!("failed to read {}: {error}", path.display()))?;
            let relative = path
                .strip_prefix(&paths.root)
                .map_err(|_| format!("input is outside project root: {}", path.display()))?;
            Ok((
                relative.to_string_lossy().replace('\\', "/"),
                format!("sha256:{}", sha256_hex(&bytes)),
            ))
        })
        .collect()
}

fn add_binding_input_hashes(
    paths: &ProjectPaths,
    bindings: &[ResolvedBinding],
    inputs: &mut BTreeMap<String, String>,
) {
    for binding in bindings {
        if let Ok(relative) = binding.source.strip_prefix(&paths.root) {
            inputs.insert(
                relative.to_string_lossy().replace('\\', "/"),
                format!("sha256:{}", binding.sha256),
            );
        }
    }
}

fn capture_expected_inputs(
    paths: &ProjectPaths,
    hashes: &BTreeMap<String, String>,
    extra: impl IntoIterator<Item = PathBuf>,
) -> Result<InputSnapshot, crate::transaction::TransactionError> {
    InputSnapshot::capture_expected(
        &paths.root,
        hashes
            .iter()
            .map(|(path, hash)| (PathBuf::from(path), hash.clone())),
        extra,
    )
}

fn capture_resolution_inputs(
    root: &Path,
    hashes: &BTreeMap<String, String>,
    pending_sources: &BTreeMap<PathBuf, Option<String>>,
) -> Result<InputSnapshot, TransactionError> {
    let mut expected = hashes.clone();
    for (path, hash) in pending_sources {
        if let Some(hash) = hash {
            expected.insert(path.to_string_lossy().replace('\\', "/"), hash.clone());
        }
    }
    let snapshot = InputSnapshot::capture_expected(
        root,
        expected
            .iter()
            .map(|(path, hash)| (PathBuf::from(path), hash.clone())),
        pending_sources.keys().cloned(),
    )?;
    for (path, hash) in pending_sources {
        if hash.is_none() && snapshot.files.get(path).is_some_and(Option::is_some) {
            return Err(TransactionError::SnapshotDrift(path.clone()));
        }
    }
    Ok(snapshot)
}

fn configured_rule_bytes(
    config: &crate::manifest::ProjectConfig,
    paths: &ProjectPaths,
) -> Result<Vec<u8>, String> {
    match &config.generator.rules {
        Some(relative) => fs::read(paths.root.join(relative)).map_err(|error| {
            format!(
                "failed to read generator rules {}: {error}",
                paths.root.join(relative).display()
            )
        }),
        None => Ok(Vec::new()),
    }
}

fn render_generation_prompt(
    plan: &PythonArtifactPlan,
    ir: &crate::ir::CanonicalIr,
    paths: &ProjectPaths,
    callable: &PythonCallable,
    rules: &[u8],
    references: &[ResolvedBinding],
    external_types: &BTreeMap<String, String>,
    existing: Option<&[u8]>,
    feedback: Option<&str>,
) -> Result<Vec<u8>, String> {
    let context = intent::context(&plan.contract_surface(), &callable.cott_symbol, rules)?;
    let canonical = plan
        .modules
        .iter()
        .map(|module| (module.module.as_str(), &module.declarations))
        .collect::<BTreeMap<_, _>>();
    let module_sources = crate::prompt_declarations::module_sources(ir, &paths.source_dir)?;
    render_prompt(
        callable,
        &context,
        &canonical,
        &module_sources,
        references,
        external_types,
        existing,
        feedback,
        Path::new("implementation.py"),
    )
}

fn pending_implementation(
    root: &Path,
    source: &Path,
    pending_sources: &BTreeMap<PathBuf, Option<String>>,
) -> Result<Option<Vec<u8>>, String> {
    let Ok(relative) = source.strip_prefix(root) else {
        return Err(format!(
            "implementation path is not project-relative: {}",
            display_path(root, source)
        ));
    };
    match pending_sources.get(relative) {
        Some(Some(expected)) => {
            let bytes = fs::read(source).map_err(|error| {
                format!(
                    "failed to read pending implementation {}: {error}",
                    display_path(root, source)
                )
            })?;
            if format!("sha256:{}", sha256_hex(&bytes)) != *expected {
                return Err(format!(
                    "pending implementation {} changed before generation",
                    display_path(root, source)
                ));
            }
            Ok(Some(bytes))
        }
        Some(None) | None => Ok(None),
    }
}

fn prompt_fail(format: OutputFormat, code: i32, message: impl AsRef<str>) -> i32 {
    let message = message.as_ref();
    match format {
        OutputFormat::Human => {
            eprintln!("error: {message}");
            code
        }
        OutputFormat::Json => write_prompt_json_errors(code, [message]),
    }
}

fn write_prompt_json_errors<I, S>(code: i32, messages: I) -> i32
where
    I: IntoIterator<Item = S>,
    S: AsRef<str>,
{
    let error_code = match code {
        2 => code::CLI_USAGE,
        3 => code::SYNTAX,
        4 => code::PYTHON,
        5 => code::AGENT,
        6 => code::FILESYSTEM,
        1 => code::INTERNAL,
        _ => code::CONTRACT,
    };
    let diagnostics = messages
        .into_iter()
        .enumerate()
        .map(|(source_order, message)| {
            let mut diagnostic = Diagnostic::error(error_code, message.as_ref(), Span::new(0, 0));
            diagnostic.source_order = source_order;
            diagnostic
        })
        .collect();
    let bytes = DiagnosticReport { diagnostics }
        .canonical_json(&SourceMap::default())
        .expect("diagnostic report is serializable");
    let _ = std::io::stdout().write_all(&bytes);
    code
}

fn prompt_source_fail(
    format: OutputFormat,
    paths: &ProjectPaths,
    diagnostics: &[ProjectDiagnostic],
) -> i32 {
    match format {
        OutputFormat::Human => {
            print_project_diagnostics(diagnostics);
            3
        }
        OutputFormat::Json => {
            let mut sources = SourceMap::default();
            let mut source_ids = BTreeMap::new();
            let mut report = Vec::new();
            for (source_order, diagnostic) in diagnostics.iter().enumerate() {
                let mut item = diagnostic.diagnostic.clone();
                item.source_order = source_order;
                let absolute = if diagnostic.path.is_absolute() {
                    diagnostic.path.clone()
                } else {
                    paths.source_dir.join(&diagnostic.path)
                };
                if let Ok(bytes) = fs::read(&absolute) {
                    let source_path = absolute
                        .strip_prefix(&paths.root)
                        .unwrap_or(&absolute)
                        .to_path_buf();
                    let file = *source_ids
                        .entry(source_path.clone())
                        .or_insert_with(|| sources.add(source_path, bytes));
                    item.source_span = Some(SourceSpan {
                        file,
                        start_byte: item.span.start,
                        end_byte: item.span.end,
                    });
                }
                report.push(item);
            }
            let bytes = DiagnosticReport {
                diagnostics: report,
            }
            .canonical_json(&sources)
            .expect("diagnostic report is serializable");
            let _ = std::io::stdout().write_all(&bytes);
            3
        }
    }
}

fn prompt_project(project_argument: Option<PathBuf>, symbol: String, format: OutputFormat) -> i32 {
    let root = match project_argument {
        Some(root) => root,
        None => match std::env::current_dir() {
            Ok(root) => root,
            Err(_) => {
                return prompt_fail(format, 2, "failed to determine current directory");
            }
        },
    };
    let session = match ProjectSession::acquire_for_inspection(&root) {
        Ok(session) => session,
        Err(error) => return prompt_fail(format, 6, error.to_string()),
    };
    let root = session.root().to_path_buf();
    let (config, paths) = match load_config_with_paths(&root) {
        Ok(config) => config,
        Err(error) => return prompt_fail(format, 2, error.to_string()),
    };
    if let Err(diagnostics) = audit_authored_python(&paths) {
        return match format {
            OutputFormat::Human => {
                for diagnostic in &diagnostics {
                    eprintln!("error: {diagnostic}");
                }
                4
            }
            OutputFormat::Json => write_prompt_json_errors(4, diagnostics),
        };
    }
    let sources = match discover_sources_from_paths(&paths) {
        Ok(sources) => sources,
        Err(error) => return prompt_fail(format, 2, error.to_string()),
    };
    let parsed = match parse_project(sources) {
        Ok(parsed) => parsed,
        Err(diagnostics) => return prompt_source_fail(format, &paths, &diagnostics),
    };
    let custom_effects = config.effects.keys().cloned().collect();
    let hir = match lower_with_effects(&paths.source_dir, parsed, &custom_effects) {
        Ok(hir) => hir,
        Err(diagnostics) => return prompt_source_fail(format, &paths, &diagnostics),
    };
    let ir = match render(&hir) {
        Ok(ir) => ir,
        Err(error) => return prompt_fail(format, 1, error),
    };
    match shadow_warnings(&config, &paths, &ir) {
        Ok(warnings) => {
            for warning in warnings {
                eprintln!("warning: {warning}");
            }
        }
        Err(error) => return prompt_fail(format, 3, error),
    }
    let plan = match PythonArtifactPlan::from_ir(&ir) {
        Ok(plan) => plan,
        Err(error) => return prompt_fail(format, 1, error.to_string()),
    };
    let resolution = match resolve_implementations(&config, &paths, &plan) {
        Ok(resolution) => resolution,
        Err(diagnostics) => {
            return match format {
                OutputFormat::Human => {
                    print_binding_diagnostics(&paths, diagnostics);
                    4
                }
                OutputFormat::Json => write_prompt_json_errors(
                    4,
                    diagnostics.iter().map(|diagnostic| {
                        format!(
                            "{}: {}",
                            display_path(&paths.root, &diagnostic.path),
                            diagnostic.message
                        )
                    }),
                ),
            };
        }
    };
    let callables = plan
        .callables()
        .into_iter()
        .map(|callable| (callable.cott_symbol.clone(), callable))
        .collect::<BTreeMap<String, PythonCallable>>();
    let Some(callable) = callables.get(&symbol) else {
        return prompt_fail(format, 2, format!("unknown callable `{symbol}`"));
    };
    if let Some(kind) = selected_implementation_kind(callable) {
        return prompt_fail(
            format,
            2,
            format!(
                "compiler-owned {kind} implementation method `{}` must not be sent to an agent",
                callable.cott_symbol
            ),
        );
    }
    let generation_required = resolution
        .unresolved
        .iter()
        .any(|binding| binding.cott_symbol == symbol);
    let existing = match resolution
        .unresolved
        .iter()
        .find(|binding| binding.cott_symbol == symbol)
    {
        Some(binding) => {
            match pending_implementation(&paths.root, &binding.source, &resolution.pending_sources)
            {
                Ok(existing) => existing,
                Err(error) => return prompt_fail(format, 6, error),
            }
        }
        None => None,
    };
    let rules = match configured_rule_bytes(&config, &paths) {
        Ok(rules) => rules,
        Err(error) => return prompt_fail(format, 4, error),
    };
    let context = match intent::context(&plan.contract_surface(), &symbol, &rules) {
        Ok(context) => context,
        Err(error) => {
            let code = if error.starts_with("unknown callable") {
                2
            } else {
                4
            };
            return prompt_fail(format, code, error);
        }
    };
    let prompt = match render_generation_prompt(
        &plan,
        &ir,
        &paths,
        callable,
        &rules,
        &resolution.resolved,
        &config.python.external_types,
        existing.as_deref(),
        None,
    ) {
        Ok(prompt) => prompt,
        Err(error) => {
            let code =
                if error.starts_with("compiler-owned") || error.starts_with("unknown callable") {
                    2
                } else {
                    4
                };
            return prompt_fail(format, code, error);
        }
    };
    let intent_hash = match intent::fingerprint_context(&context) {
        Ok(hash) => hash,
        Err(error) => return prompt_fail(format, 1, error),
    };
    let prompt_hash = format!("sha256:{}", sha256_hex(&prompt));
    match format {
        OutputFormat::Human => {
            let _ = std::io::stdout().write_all(&prompt);
            0
        }
        OutputFormat::Json => {
            let prompt_text = String::from_utf8(prompt).expect("agent prompt is UTF-8");
            let report = serde_json::json!({
                "symbol": symbol,
                "intent_hash": intent_hash,
                "prompt_hash": prompt_hash,
                "generation_required": generation_required,
                "context": context,
                "prompt": prompt_text,
            });
            serde_json::to_writer(std::io::stdout(), &report)
                .expect("prompt report is serializable");
            println!();
            0
        }
    }
}

fn attach_intent_tool(
    tools: &mut serde_json::Value,
    surface: &serde_json::Value,
    rules: &[u8],
) -> Result<(), String> {
    let hashes = intent::fingerprints(surface, rules)?;
    tools
        .as_object_mut()
        .ok_or_else(|| "planned generation tools are not an object".to_owned())?
        .insert(intent::TOOL_KEY.to_owned(), intent::metadata(&hashes));
    Ok(())
}

fn enrich_generation_record(
    paths: &ProjectPaths,
    config: &crate::manifest::ProjectConfig,
    inputs: BTreeMap<String, String>,
    emission: &mut Emission,
) -> Result<(), String> {
    let bytes = emission
        .files
        .get(Path::new("generation.json"))
        .ok_or_else(|| "emission omitted generation.json".to_owned())?;
    let mut record = GenerationRecord::parse(bytes)
        .map_err(|error| format!("invalid planned generation record: {error}"))?;
    record.current.project_version = config.project.version.clone();
    record.current.compatibility = crate::provenance::GenerationCompatibility::current();
    let mut dependencies = dependency_records(paths)?;
    let existing_path = artifact_root_for_paths(paths)?.join("generation.json");
    if existing_path.exists() {
        let existing = fs::read(&existing_path).map_err(|error| {
            format!(
                "failed to read existing generation record {}: {error}",
                existing_path.display()
            )
        })?;
        let existing = GenerationRecord::parse(&existing).map_err(|error| {
            format!(
                "invalid existing generation record {}: {error}",
                existing_path.display()
            )
        })?;
        merge_dependency_evidence(&mut dependencies, &existing.current.dependencies);
        record.last_verified = existing.last_verified;
        let planned_runtime = record.current.tools.get("runtime").cloned();
        merge_tool_evidence(&mut record.current.tools, &existing.current.tools);
        let tools = record
            .current
            .tools
            .as_object_mut()
            .expect("planned generation tools are an object");
        tools.insert("compiler".to_owned(), current_compiler_tool()?);
        if let Some(runtime) = planned_runtime {
            tools.insert("runtime".to_owned(), runtime);
        }
        record.current.agent_runs = existing
            .current
            .agent_runs
            .into_iter()
            .filter(|run| agent_run_applies(&record, run))
            .collect();
    }
    record.current.inputs =
        serde_json::to_value(inputs).map_err(|error| format!("serialize input hashes: {error}"))?;
    record.current.dependencies = dependencies;
    let rules = configured_rule_bytes(config, paths)?;
    attach_intent_tool(
        &mut record.current.tools,
        &record.current.contract_surface,
        &rules,
    )?;
    record.current.compute_generation_id()?;
    emission
        .files
        .insert(PathBuf::from("generation.json"), record.canonical_bytes()?);
    Ok(())
}

fn merge_dependency_evidence(current: &mut serde_json::Value, existing: &serde_json::Value) {
    let Some(current) = current.as_array_mut() else {
        return;
    };
    let Some(existing) = existing.as_array() else {
        return;
    };
    for dependency in current {
        let Some(previous) = existing.iter().find(|previous| {
            ["name", "version", "lock_hash", "artifacts"]
                .into_iter()
                .all(|field| previous.get(field) == dependency.get(field))
        }) else {
            continue;
        };
        if let Some(installed) = previous.get("installed") {
            dependency
                .as_object_mut()
                .expect("dependency is an object")
                .insert("installed".to_owned(), installed.clone());
        }
    }
}

fn merge_tool_evidence(current: &mut serde_json::Value, existing: &serde_json::Value) {
    let Some(planned) = current.as_object() else {
        return;
    };
    let Some(existing) = existing.as_object() else {
        return;
    };
    let mut merged = existing.clone();
    for (tool, planned_record) in planned {
        merged
            .entry(tool.clone())
            .or_insert_with(|| planned_record.clone());
    }
    *current = serde_json::Value::Object(merged);
}

fn current_compiler_tool() -> Result<serde_json::Value, String> {
    let executable = std::env::current_exe().map_err(|error| error.to_string())?;
    let executable = fs::canonicalize(executable).map_err(|error| error.to_string())?;
    let content_hash = format!(
        "sha256:{}",
        sha256_hex(&fs::read(&executable).map_err(|error| error.to_string())?)
    );
    Ok(serde_json::json!({
        "content_hash": content_hash,
        "executable": executable,
        "version": env!("CARGO_PKG_VERSION"),
    }))
}

fn dependency_records(paths: &ProjectPaths) -> Result<serde_json::Value, String> {
    let Some(path) = &paths.lockfile else {
        return Ok(serde_json::Value::Array(Vec::new()));
    };
    let bytes = fs::read(path)
        .map_err(|error| format!("failed to read lockfile {}: {error}", path.display()))?;
    let lock: toml::Value = toml::from_str(
        std::str::from_utf8(&bytes)
            .map_err(|_| format!("lockfile {} is not UTF-8", path.display()))?,
    )
    .map_err(|error| format!("invalid uv lockfile {}: {error}", path.display()))?;
    let lock_hash = format!("sha256:{}", sha256_hex(&bytes));
    let mut packages = lock
        .get("package")
        .and_then(toml::Value::as_array)
        .into_iter()
        .flatten()
        .filter_map(|package| {
            let name = package.get("name")?.as_str()?;
            let version = package.get("version")?.as_str()?;
            let mut artifacts = package
                .get("wheels")
                .and_then(toml::Value::as_array)
                .into_iter()
                .flatten()
                .filter_map(|wheel| wheel.get("hash").and_then(toml::Value::as_str))
                .map(str::to_owned)
                .collect::<Vec<_>>();
            if let Some(hash) = package
                .get("sdist")
                .and_then(|sdist| sdist.get("hash"))
                .and_then(toml::Value::as_str)
            {
                artifacts.push(hash.to_owned());
            }
            artifacts.sort();
            artifacts.dedup();
            Some(serde_json::json!({
                "artifacts": artifacts,
                "lock_hash": lock_hash,
                "name": name.to_ascii_lowercase().replace('_', "-"),
                "version": version,
            }))
        })
        .collect::<Vec<_>>();
    packages.sort_by(|left, right| {
        (
            left.get("name").and_then(serde_json::Value::as_str),
            left.get("version").and_then(serde_json::Value::as_str),
        )
            .cmp(&(
                right.get("name").and_then(serde_json::Value::as_str),
                right.get("version").and_then(serde_json::Value::as_str),
            ))
    });
    Ok(serde_json::Value::Array(packages))
}

fn verified_baseline_guard(
    paths: &ProjectPaths,
    config: &crate::manifest::ProjectConfig,
    inputs: &BTreeMap<String, String>,
    allowed_missing: &[PathBuf],
) -> Result<(), String> {
    let generation = artifact_root_for_paths(paths)?.join("generation.json");
    let bytes = match fs::read(&generation) {
        Ok(bytes) => bytes,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(()),
        Err(error) => {
            return Err(format!(
                "read verified baseline {}: {error}",
                generation.display()
            ));
        }
    };
    let record = GenerationRecord::parse(&bytes).map_err(|error| {
        format!(
            "invalid verified baseline {}: {error}",
            generation.display()
        )
    })?;
    let allowed_missing = allowed_missing
        .iter()
        .map(|path| path.to_string_lossy().replace('\\', "/"))
        .collect::<BTreeSet<_>>();
    let rules = config.generator.rules.as_deref();
    let intentional_contract = |path: &str| path.ends_with(".cott") || rules == Some(path);
    let ignorable = |path: &str| allowed_missing.contains(path) || intentional_contract(path);
    if let Some(epoch_inputs) = record.current.inputs.as_object() {
        let changed_inputs = epoch_inputs.iter().any(|(path, hash)| {
            if ignorable(path) {
                return false;
            }
            inputs
                .get(path)
                .map(String::as_str)
                .is_some_and(|current| current != hash)
                || !inputs.contains_key(path)
        }) || inputs
            .keys()
            .any(|path| !ignorable(path) && !epoch_inputs.contains_key(path));
        if changed_inputs {
            return Err(
                "emitted inputs changed; run `cott emit python` before generation".to_owned(),
            );
        }
    }
    for (relative, expected) in &record.current.managed_files {
        let bytes = fs::read(paths.root.join(relative))
            .map_err(|_| format!("verified baseline managed file is missing: {relative}"))?;
        if expected != &format!("sha256:{}", sha256_hex(&bytes)) {
            return Err(format!(
                "verified baseline managed file changed: {relative}"
            ));
        }
    }
    Ok(())
}

fn add_agent_runs(
    emission: &mut Emission,
    runs: Vec<(String, AgentKind, AgentRunCandidate)>,
) -> Result<(), String> {
    if runs.is_empty() {
        return Ok(());
    }
    let bytes = emission
        .files
        .get(Path::new("generation.json"))
        .ok_or_else(|| "emission omitted generation.json".to_owned())?;
    let mut record = GenerationRecord::parse(bytes)?;
    let replaced = runs
        .iter()
        .map(|(symbol, _, _)| symbol.as_str())
        .collect::<std::collections::BTreeSet<_>>();
    record
        .current
        .agent_runs
        .retain(|run| !replaced.contains(run.symbol.as_str()));
    for (symbol, kind, candidate) in runs {
        let spec = adapter(kind);
        let stream = |bytes: &[u8]| StreamDigest {
            bytes: bytes.len() as u64,
            sha256: format!("sha256:{}", sha256_hex(bytes)),
            truncated: false,
        };
        record.current.agent_runs.push(AgentRun {
            symbol,
            adapter: match kind {
                AgentKind::Claude => "claude",
                AgentKind::Codex => "codex",
                AgentKind::Omp => "omp",
            }
            .to_owned(),
            adapter_version: candidate.adapter_version,
            argv_template: spec.argv_template.iter().map(ToString::to_string).collect(),
            executable: candidate.executable.display().to_string(),
            executable_hash: candidate.executable_hash,
            prompt_hash: candidate.prompt_hash,
            implementation_hash: format!("sha256:{}", sha256_hex(&candidate.implementation)),
            environment_names: candidate.environment_names,
            duration_ms: candidate.duration_ms,
            status: AgentStatus {
                exit_code: candidate.exit_code,
                signal: None,
                timed_out: candidate.timed_out,
                cancelled: false,
            },
            stdout: stream(&candidate.stdout),
            stderr: stream(&candidate.stderr),
        });
    }
    record
        .current
        .agent_runs
        .sort_by(|left, right| left.symbol.cmp(&right.symbol));
    record.current.compute_generation_id()?;
    emission
        .files
        .insert(PathBuf::from("generation.json"), record.canonical_bytes()?);
    Ok(())
}

fn agent_run_applies(record: &GenerationRecord, run: &AgentRun) -> bool {
    record
        .current
        .unresolved
        .iter()
        .any(|pending| pending.cott_symbol == run.symbol)
        || record
            .current
            .implementations
            .as_array()
            .into_iter()
            .flatten()
            .any(|implementation| {
                implementation
                    .get("cott_symbol")
                    .and_then(serde_json::Value::as_str)
                    == Some(run.symbol.as_str())
                    && implementation
                        .get("content_hash")
                        .and_then(serde_json::Value::as_str)
                        .is_some_and(|hash| {
                            hash == run.implementation_hash
                                || hash.strip_prefix("sha256:")
                                    == Some(run.implementation_hash.as_str())
                        })
            })
}

fn implementation_matches_unresolved(
    implementation: &serde_json::Value,
    unresolved: &UnresolvedRecord,
) -> bool {
    let kind = match unresolved.kind {
        UnresolvedKind::Function => "function",
        UnresolvedKind::AsyncFunction => "async_function",
        UnresolvedKind::ImplMethod => "impl_method",
        UnresolvedKind::AsyncImplMethod => "async_impl_method",
    };
    implementation
        .get("kind")
        .and_then(serde_json::Value::as_str)
        == Some(kind)
        && implementation
            .get("callable_kind")
            .and_then(serde_json::Value::as_str)
            == Some(unresolved.callable_kind.as_str())
}

fn carry_trusted_python_state(
    record: &mut GenerationRecord,
    trusted: &GenerationRecord,
    config: &crate::manifest::ProjectConfig,
    paths: &ProjectPaths,
) -> Result<(), String> {
    let rules = configured_rule_bytes(config, paths)?;
    let current_intent = intent::recorded_fingerprints(&record.current.tools)?.unwrap_or_default();
    let baseline = recorded_intent_baseline(trusted, config, paths, &rules)?;
    let previous_pending = trusted
        .current
        .unresolved
        .iter()
        .map(|record| record.cott_symbol.as_str())
        .collect::<BTreeSet<_>>();
    let previous_implementations = trusted
        .current
        .implementations
        .as_array()
        .into_iter()
        .flatten()
        .filter_map(|implementation| {
            Some((
                implementation.get("cott_symbol")?.as_str()?.to_owned(),
                implementation.clone(),
            ))
        })
        .collect::<BTreeMap<_, _>>();
    let mut implementations = Vec::new();
    let mut unresolved = Vec::new();
    for pending in std::mem::take(&mut record.current.unresolved) {
        let symbol = pending.cott_symbol.clone();
        let intent_matches = baseline
            .as_ref()
            .and_then(|baseline| baseline.get(&symbol))
            .zip(current_intent.get(&symbol))
            .is_some_and(|(previous, current)| previous == current);
        match previous_implementations.get(&symbol) {
            Some(implementation)
                if !previous_pending.contains(symbol.as_str())
                    && intent_matches
                    && implementation_matches_unresolved(implementation, &pending) =>
            {
                if let (Some(path), Some(inputs)) = (
                    implementation
                        .get("source_origin")
                        .and_then(serde_json::Value::as_str),
                    record.current.inputs.as_object_mut(),
                ) {
                    if let Some(hash) = trusted.current.inputs.get(path).cloned() {
                        inputs.insert(path.to_owned(), hash);
                    }
                }
                implementations.push(implementation.clone());
            }
            _ => unresolved.push(pending),
        }
    }
    implementations.sort_by(|left, right| {
        left.get("cott_symbol")
            .and_then(serde_json::Value::as_str)
            .cmp(&right.get("cott_symbol").and_then(serde_json::Value::as_str))
    });
    unresolved.sort_by(|left, right| left.cott_symbol.cmp(&right.cott_symbol));
    record.current.implementations = serde_json::Value::Array(implementations);
    record.current.unresolved = unresolved;
    record.current.agent_runs = std::mem::take(&mut record.current.agent_runs)
        .into_iter()
        .filter(|run| agent_run_applies(record, run))
        .collect();
    record
        .current
        .agent_runs
        .sort_by(|left, right| left.symbol.cmp(&right.symbol));
    Ok(())
}

fn emit_ir(project_argument: Option<PathBuf>) -> i32 {
    let Ok(root) = project_root(project_argument) else {
        return 2;
    };
    let session = match ProjectSession::acquire(&root) {
        Ok(session) => session,
        Err(error) => {
            eprintln!("error: {error}");
            return 6;
        }
    };
    let (config, paths) = match load_config_with_paths(session.root()) {
        Ok(config) => config,
        Err(error) => {
            eprintln!("error: {error}");
            return 2;
        }
    };
    let sources = match discover_sources_from_paths(&paths) {
        Ok(sources) => sources,
        Err(error) => {
            eprintln!("error: {error}");
            return 2;
        }
    };
    let input_hashes = match collect_input_hashes(&config, &paths, &sources) {
        Ok(inputs) => inputs,
        Err(error) => {
            eprintln!("error: {error}");
            return 2;
        }
    };
    let parsed = match parse_project(sources) {
        Ok(parsed) => parsed,
        Err(diagnostics) => {
            print_project_diagnostics(&diagnostics);
            return 3;
        }
    };
    let custom_effects = config.effects.keys().cloned().collect();
    let hir = match lower_with_effects(&paths.source_dir, parsed, &custom_effects) {
        Ok(hir) => hir,
        Err(diagnostics) => {
            print_project_diagnostics(&diagnostics);
            return 3;
        }
    };
    let ir = match render(&hir) {
        Ok(ir) => ir,
        Err(error) => {
            eprintln!("error: {error}");
            return 1;
        }
    };
    let artifact_plan = match PythonArtifactPlan::from_ir(&ir) {
        Ok(plan) => plan,
        Err(error) => {
            eprintln!("error: {error}");
            return 1;
        }
    };
    let mut emission = match emit(&config, &artifact_plan, &ir, &[]) {
        Ok(emission) => emission,
        Err(diagnostics) => {
            print_emit_diagnostics(&paths, &diagnostics);
            return 4;
        }
    };
    let input_snapshot = match capture_expected_inputs(&paths, &input_hashes, []) {
        Ok(snapshot) => snapshot,
        Err(error) => {
            eprintln!("error: {error}");
            return 6;
        }
    };
    if let Err(error) = enrich_generation_record(&paths, &config, input_hashes, &mut emission) {
        eprintln!("error: {error}");
        return 4;
    }
    let artifact_root = match artifact_root_for_paths(&paths) {
        Ok(path) => path,
        Err(error) => {
            eprintln!("error: {error}");
            return 2;
        }
    };
    let relative_root = artifact_root
        .strip_prefix(&paths.root)
        .expect("artifact root is project-relative");
    let actual = match fs::symlink_metadata(&artifact_root) {
        Ok(_) => match collect_tree(&artifact_root) {
            Ok(files) => files,
            Err(error) => {
                eprintln!("error: {error}");
                return 4;
            }
        },
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => BTreeMap::new(),
        Err(error) => {
            eprintln!("error: inspect artifact root: {error}");
            return 4;
        }
    };
    let expected_ir = emission
        .files
        .iter()
        .filter(|(path, _)| path.starts_with("ir"))
        .map(|(path, bytes)| (path.clone(), bytes.clone()))
        .collect::<BTreeMap<_, _>>();
    let mut record = match emission.files.get(Path::new("generation.json")) {
        Some(bytes) => match GenerationRecord::parse(bytes) {
            Ok(record) => record,
            Err(error) => {
                eprintln!("error: invalid planned generation record: {error}");
                return 1;
            }
        },
        None => {
            eprintln!("error: compiler omitted generation.json");
            return 1;
        }
    };
    let trusted = match actual.get(Path::new("generation.json")) {
        Some(bytes) => match GenerationRecord::parse(bytes) {
            Ok(record) => Some(record),
            Err(error) => {
                eprintln!("error: invalid existing generation record: {error}");
                return 4;
            }
        },
        None => None,
    };
    let mut managed_files = BTreeMap::new();
    match &trusted {
        None => {
            for path in actual.keys() {
                if path.as_path() == Path::new("generation.json") || path.starts_with("ir") {
                    continue;
                }
                eprintln!(
                    "error: no trusted generation record for existing managed artifact: {}",
                    relative_root.join(path).display()
                );
                return 4;
            }
        }
        Some(trusted) => {
            for (relative, expected) in &trusted.current.managed_files {
                if Path::new(relative)
                    .strip_prefix(relative_root)
                    .is_ok_and(|path| path.starts_with("ir"))
                {
                    continue;
                }
                let on_disk = match Path::new(relative).strip_prefix(relative_root) {
                    Ok(path) => actual.get(path).map(Vec::as_slice),
                    Err(_) => None,
                };
                let matches = |bytes: &[u8]| expected == &format!("sha256:{}", sha256_hex(bytes));
                let trusted_bytes = if let Some(bytes) = on_disk {
                    Some(matches(bytes))
                } else {
                    fs::read(paths.root.join(relative))
                        .ok()
                        .map(|bytes| matches(&bytes))
                };
                match trusted_bytes {
                    Some(true) => {
                        managed_files.insert(relative.clone(), expected.clone());
                    }
                    Some(false) => {
                        eprintln!("error: managed file changed: {relative}");
                        return 4;
                    }
                    None => {
                        eprintln!("error: managed file is missing: {relative}");
                        return 4;
                    }
                }
            }
            for path in actual.keys() {
                if path.as_path() == Path::new("generation.json") || path.starts_with("ir") {
                    continue;
                }
                let relative = relative_root
                    .join(path)
                    .to_string_lossy()
                    .replace('\\', "/");
                if !managed_files.contains_key(&relative) {
                    eprintln!("error: unexpected managed artifact: {relative}");
                    return 4;
                }
            }
        }
    }
    let non_ir_snapshot = match InputSnapshot::capture_expected(
        &paths.root,
        managed_files
            .iter()
            .map(|(path, hash)| (PathBuf::from(path), hash.clone())),
        [],
    ) {
        Ok(snapshot) => snapshot,
        Err(error) => {
            eprintln!("error: {error}");
            return 6;
        }
    };
    for (path, bytes) in &expected_ir {
        managed_files.insert(
            relative_root
                .join(path)
                .to_string_lossy()
                .replace('\\', "/"),
            format!("sha256:{}", sha256_hex(bytes)),
        );
    }
    record.current.managed_files = managed_files;
    record.current.verified = false;
    record.current.verification = serde_json::Value::Null;
    if let Some(trusted) = &trusted {
        if let Err(error) = carry_trusted_python_state(&mut record, trusted, &config, &paths) {
            eprintln!("error: {error}");
            return 4;
        }
    }
    if let Err(error) = record.current.compute_generation_id() {
        eprintln!("error: compute IR generation identity: {error}");
        return 1;
    }
    let generation_bytes = match record.canonical_bytes() {
        Ok(bytes) => bytes,
        Err(error) => {
            eprintln!("error: serialize IR generation record: {error}");
            return 1;
        }
    };
    let mut changes = ChangeSet::default();
    let mut paths_to_write = Vec::new();
    for (path, bytes) in &expected_ir {
        if actual.get(path) != Some(bytes) {
            let relative = relative_root.join(path);
            paths_to_write.push(relative.clone());
            changes.operations.push(Operation::Write {
                path: relative,
                bytes: bytes.clone(),
            });
        }
    }
    for path in actual
        .keys()
        .filter(|path| path.starts_with("ir") && !expected_ir.contains_key(*path))
    {
        let relative = relative_root.join(path);
        paths_to_write.push(relative.clone());
        changes
            .operations
            .push(Operation::Remove { path: relative });
    }
    let generation_path = relative_root.join("generation.json");
    paths_to_write.push(generation_path.clone());
    changes.operations.push(Operation::Write {
        path: generation_path,
        bytes: generation_bytes,
    });
    changes.generation_record_last = true;
    let output_snapshot = match InputSnapshot::capture(&paths.root, paths_to_write) {
        Ok(snapshot) => snapshot,
        Err(error) => {
            eprintln!("error: {error}");
            return 6;
        }
    };
    let mut snapshot = input_snapshot;
    snapshot.merge_missing(non_ir_snapshot);
    snapshot.merge_missing(output_snapshot);
    match session.apply(&snapshot, &changes) {
        Ok(()) => 0,
        Err(error) => {
            eprintln!("error: {error}");
            6
        }
    }
}
fn run_scoped_wave<T, R, E>(
    items: &[T],
    work: impl Fn(&T) -> Result<R, E> + Sync,
    panic_error: impl Fn(&T) -> E + Sync,
) -> Vec<Result<R, E>>
where
    T: Sync,
    R: Send,
    E: Send,
{
    thread::scope(|scope| {
        let mut workers = Vec::with_capacity(items.len());
        for item in items {
            workers.push((item, scope.spawn(|| work(item))));
        }
        workers
            .into_iter()
            .map(|(item, worker)| worker.join().unwrap_or_else(|_| Err(panic_error(item))))
            .collect()
    })
}

fn generate_project(
    project_argument: Option<PathBuf>,
    symbol: Option<String>,
    agent: Option<AgentKind>,
    jobs: usize,
) -> i32 {
    let Ok(root) = project_root(project_argument) else {
        return 2;
    };
    let session = match ProjectSession::acquire(&root) {
        Ok(session) => session,
        Err(error) => {
            eprintln!("error: {error}");
            return 6;
        }
    };
    let root = session.root().to_path_buf();
    let (config, paths) = match load_config_with_paths(&root) {
        Ok(config) => config,
        Err(error) => {
            eprintln!("error: {error}");
            return 2;
        }
    };
    if let Err(diagnostics) = audit_authored_python(&paths) {
        for diagnostic in diagnostics {
            eprintln!("error: {diagnostic}");
        }
        return 4;
    }
    let sources = match discover_sources_from_paths(&paths) {
        Ok(sources) => sources,
        Err(error) => {
            eprintln!("error: {error}");
            return 2;
        }
    };
    let mut input_hashes = match collect_input_hashes(&config, &paths, &sources) {
        Ok(inputs) => inputs,
        Err(message) => {
            eprintln!("error: {message}");
            return 2;
        }
    };
    let parsed = match parse_project(sources) {
        Ok(parsed) => parsed,
        Err(diagnostics) => {
            print_project_diagnostics(&diagnostics);
            return 3;
        }
    };
    let custom_effects = config.effects.keys().cloned().collect();
    let hir = match lower_with_effects(&paths.source_dir, parsed, &custom_effects) {
        Ok(hir) => hir,
        Err(diagnostics) => {
            print_project_diagnostics(&diagnostics);
            return 3;
        }
    };
    let ir = match render(&hir) {
        Ok(ir) => ir,
        Err(error) => {
            eprintln!("error: {error}");
            return 1;
        }
    };
    match shadow_warnings(&config, &paths, &ir) {
        Ok(warnings) => {
            for warning in warnings {
                eprintln!("warning: {warning}");
            }
        }
        Err(error) => {
            eprintln!("error: {error}");
            return 3;
        }
    }
    let plan = match PythonArtifactPlan::from_ir(&ir) {
        Ok(plan) => plan,
        Err(error) => {
            eprintln!("error: {error}");
            return 1;
        }
    };
    let resolution = match resolve_implementations(&config, &paths, &plan) {
        Ok(resolution) => resolution,
        Err(diagnostics) => {
            print_binding_diagnostics(&paths, diagnostics);
            return 4;
        }
    };
    if let Some(stale) = resolution.stale.first() {
        eprintln!(
            "error: {}: stale durable agent implementation",
            display_path(&paths.root, stale)
        );
        return 4;
    }
    let callables = plan
        .callables()
        .into_iter()
        .map(|callable| (callable.cott_symbol.clone(), callable))
        .collect::<BTreeMap<String, PythonCallable>>();
    let requested = symbol.as_deref();
    let intent_changed = resolution.intent_changed;
    let pending_paths = resolution
        .pending_sources
        .keys()
        .cloned()
        .collect::<Vec<_>>();
    let pending = resolution.unresolved;
    let mut unresolved = pending
        .into_iter()
        .filter(|binding| requested.is_none_or(|symbol| symbol == binding.cott_symbol))
        .collect::<Vec<_>>();
    if let Some(symbol) = requested {
        if !callables.contains_key(symbol) {
            eprintln!("error: unknown callable `{symbol}`");
            return 2;
        }
        if intent_changed.contains(symbol)
            && !unresolved
                .iter()
                .any(|binding| binding.cott_symbol == symbol)
        {
            eprintln!("error: intent-stale callable `{symbol}` is not queued for generation");
            return 4;
        }
    } else if let Some(symbol) = intent_changed.iter().find(|symbol| {
        !unresolved
            .iter()
            .any(|binding| binding.cott_symbol == **symbol)
    }) {
        eprintln!("error: intent-stale callable `{symbol}` is not queued for generation");
        return 4;
    }
    unresolved.sort_by(|left, right| left.cott_symbol.cmp(&right.cott_symbol));
    let mut bindings = resolution.resolved;
    add_binding_input_hashes(&paths, &bindings, &mut input_hashes);
    let input_snapshot =
        match capture_resolution_inputs(&paths.root, &input_hashes, &resolution.pending_sources) {
            Ok(snapshot) => snapshot,
            Err(error) => {
                eprintln!("error: {error}");
                return 6;
            }
        };
    let mut durable_sources = Vec::new();
    let mut generated_runs = Vec::new();
    let mut generation_failure = None;
    let generation_total = unresolved.len();
    let generation_positions = unresolved
        .iter()
        .enumerate()
        .map(|(index, binding)| (binding.cott_symbol.clone(), index + 1))
        .collect::<BTreeMap<_, _>>();
    if !unresolved.is_empty() {
        let Some(agent) = agent else {
            eprintln!("error: unresolved selected callable requires `--agent codex|claude|omp`");
            return 2;
        };
        if let Err(error) = verified_baseline_guard(&paths, &config, &input_hashes, &pending_paths)
        {
            eprintln!("error: {error}");
            return 4;
        }
        let executable = match resolve_executable(adapter(agent).executable_name) {
            Ok(path) => path,
            Err(error) => {
                eprintln!("error: {error}");
                return 5;
            }
        };
        let rules = match configured_rule_bytes(&config, &paths) {
            Ok(rules) => rules,
            Err(error) => {
                eprintln!("error: {error}");
                return 4;
            }
        };
        let generate_candidate =
            |unresolved_binding: &crate::binding::UnresolvedBinding,
             bindings: &[ResolvedBinding]|
             -> Result<(PythonCallable, AgentRunCandidate), (i32, String)> {
                let callable = callables
                    .get(&unresolved_binding.cott_symbol)
                    .expect("resolution callable was selected from the artifact plan");
                let existing = match pending_implementation(
                    &paths.root,
                    &unresolved_binding.source,
                    &resolution.pending_sources,
                ) {
                    Ok(existing) => existing,
                    Err(error) => return Err((6, error)),
                };
                let temporary = match agent_workspace() {
                    Ok(paths) => paths,
                    Err(error) => {
                        return Err((6, error));
                    }
                };
                let target = temporary.workspace.join("implementation.py");
                let fully_qualified = callable.cott_symbol.clone();
                let position = generation_positions[&fully_qualified];
                eprintln!("generate [{position}/{generation_total}] start `{fully_qualified}`");
                let result = (|| {
                    let prompt = render_generation_prompt(
                        &plan,
                        &ir,
                        &paths,
                        callable,
                        &rules,
                        bindings,
                        &config.python.external_types,
                        existing.as_deref(),
                        None,
                    )?;
                    let mut candidate = run_agent(
                        agent,
                        executable.clone(),
                        &temporary.workspace,
                        &temporary.scratch,
                        &target,
                        prompt,
                        config.generator.timeout_seconds,
                    )?;
                    eprintln!(
                        "generate [{position}/{generation_total}] validate `{fully_qualified}`"
                    );
                    let mut feedback = String::new();
                    for attempt in 0..=2 {
                        match validate_candidate(
                            &config,
                            &paths,
                            &plan,
                            &fully_qualified,
                            &candidate.implementation,
                        ) {
                            Ok(()) => {
                                eprintln!(
                                    "generate [{position}/{generation_total}] done `{fully_qualified}`"
                                );
                                return Ok(candidate);
                            }
                            Err(validation_error) if attempt == 2 => return Err(validation_error),
                            Err(validation_error) => {
                                eprintln!(
                                    "generate [{position}/{generation_total}] retry {}/2 `{fully_qualified}`",
                                    attempt + 1
                                );
                                if !feedback.is_empty() {
                                    feedback.push('\n');
                                }
                                feedback.push_str(&validation_error);
                                let retry_prompt = render_generation_prompt(
                                    &plan,
                                    &ir,
                                    &paths,
                                    callable,
                                    &rules,
                                    bindings,
                                    &config.python.external_types,
                                    Some(&candidate.implementation),
                                    Some(feedback.as_str()),
                                )?;
                                fs::remove_file(&target).map_err(|error| {
                                    format!(
                                        "reset isolated agent target {}: {error}",
                                        target.display()
                                    )
                                })?;
                                candidate = run_agent(
                                    agent,
                                    executable.clone(),
                                    &temporary.workspace,
                                    &temporary.scratch,
                                    &target,
                                    retry_prompt,
                                    config.generator.timeout_seconds,
                                )?;
                                eprintln!(
                                    "generate [{position}/{generation_total}] validate `{fully_qualified}`"
                                );
                            }
                        }
                    }
                    unreachable!()
                })();
                let _ = fs::remove_dir_all(&temporary.root);
                result
                    .map(|candidate| (callable.clone(), candidate))
                    .map_err(|error| {
                        (
                            5,
                            format!("agent generation for `{fully_qualified}` failed: {error}"),
                        )
                    })
            };
        let merge_candidate =
            |unresolved_binding: crate::binding::UnresolvedBinding,
             callable: PythonCallable,
             candidate: AgentRunCandidate,
             bindings: &mut Vec<ResolvedBinding>,
             durable_sources: &mut Vec<(PathBuf, Vec<u8>)>,
             generated_runs: &mut Vec<(String, AgentKind, AgentRunCandidate)>| {
                let fully_qualified = callable.cott_symbol.clone();
                let bytes = candidate.implementation.clone();
                generated_runs.push((fully_qualified, agent, candidate));
                let generated_relative = unresolved_binding
                    .source
                    .strip_prefix(&paths.python_source_dir)
                    .expect("implementation path is rooted at Python source")
                    .to_path_buf();
                let relative_source = unresolved_binding
                    .source
                    .strip_prefix(&paths.root)
                    .expect("implementation path is project-relative")
                    .to_path_buf();
                durable_sources.push((relative_source, bytes.clone()));
                let implementation_module = match &callable.kind {
                    PythonCallableKind::Function | PythonCallableKind::AsyncFunction => {
                        format!("_cott_impl.{}.{}", callable.module, callable.name)
                    }
                    PythonCallableKind::ImplMethod { concrete }
                    | PythonCallableKind::AsyncImplMethod { concrete } => {
                        format!(
                            "_cott_impl.{}.{concrete}.{}",
                            callable.module, callable.name
                        )
                    }
                };
                bindings.push(ResolvedBinding {
                    module: callable.module.clone(),
                    function: callable.name.clone(),
                    cott_symbol: callable.cott_symbol.clone(),
                    kind: callable.kind.clone(),
                    implementation_module,
                    implementation_function: unresolved_binding.expected_implementation_function,
                    owner: crate::binding::BindingOwner::Agent,
                    source: unresolved_binding.source,
                    generated_relative,
                    sha256: crate::hash::sha256_hex(&bytes),
                    bytes,
                });
            };
        let prompt_refs = bindings.len();
        if jobs == 1 {
            for unresolved_binding in unresolved {
                let (callable, candidate) =
                    match generate_candidate(&unresolved_binding, &bindings[..prompt_refs]) {
                        Ok(candidate) => candidate,
                        Err((code, error)) => {
                            eprintln!("error: {error}");
                            generation_failure = Some(code);
                            break;
                        }
                    };
                merge_candidate(
                    unresolved_binding,
                    callable,
                    candidate,
                    &mut bindings,
                    &mut durable_sources,
                    &mut generated_runs,
                );
            }
        } else {
            for wave in unresolved.chunks(jobs) {
                let generated = run_scoped_wave(
                    wave,
                    |unresolved_binding| {
                        generate_candidate(unresolved_binding, &bindings[..prompt_refs]).map(
                            |(callable, candidate)| {
                                (unresolved_binding.clone(), callable, candidate)
                            },
                        )
                    },
                    |_| (1, "agent worker panicked".to_owned()),
                );
                let mut wave_failed = false;
                for result in generated {
                    match result {
                        Ok((unresolved_binding, callable, candidate)) => merge_candidate(
                            unresolved_binding,
                            callable,
                            candidate,
                            &mut bindings,
                            &mut durable_sources,
                            &mut generated_runs,
                        ),
                        Err((code, error)) => {
                            eprintln!("error: {error}");
                            generation_failure.get_or_insert(code);
                            wave_failed = true;
                        }
                    }
                }
                if wave_failed {
                    break;
                }
            }
        }
    }
    bindings.sort_by(|left, right| left.cott_symbol.cmp(&right.cott_symbol));
    add_binding_input_hashes(&paths, &bindings, &mut input_hashes);
    let mut emission = match emit(&config, &plan, &ir, &bindings) {
        Ok(emission) => emission,
        Err(diagnostics) => {
            print_emit_diagnostics(&paths, &diagnostics);
            return 4;
        }
    };
    if let Err(message) = enrich_generation_record(&paths, &config, input_hashes, &mut emission) {
        eprintln!("error: {message}");
        return 4;
    }
    let generated_scope = generated_runs
        .iter()
        .map(|(symbol, _, _)| symbol.clone())
        .collect::<std::collections::BTreeSet<_>>();
    if let Err(message) = add_agent_runs(&mut emission, generated_runs) {
        eprintln!("error: {message}");
        return 4;
    }
    let mut validation_failed = false;
    if !generated_scope.is_empty() && generation_failure.is_none() {
        let staged = match materialize_candidate_artifacts(&emission) {
            Ok(path) => path,
            Err(error) => {
                eprintln!("error: {error}");
                return 6;
            }
        };
        let validation = verify_python(&config, &paths, &staged, &ir, Some(&generated_scope));
        let cleanup = fs::remove_dir_all(&staged);
        if let Err(error) = cleanup {
            eprintln!(
                "error: remove candidate staging {}: {error}",
                staged.display()
            );
            return 6;
        }
        if let Err(error) = validation {
            eprintln!("error: generated candidate validation failed: {error}");
            validation_failed = true;
        }
    }
    match publish_with_sources(
        &PlannedProject {
            session,
            config,
            paths,
            ir,
            emission,
            input_snapshot,
        },
        &durable_sources,
    ) {
        Ok(()) => generation_failure.unwrap_or(if validation_failed { 5 } else { 0 }),
        Err(error) => {
            eprintln!("error: {error}");
            6
        }
    }
}

fn materialize_candidate_artifacts(emission: &Emission) -> Result<PathBuf, String> {
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|error| error.to_string())?
        .as_nanos();
    let root = std::env::temp_dir().join(format!("cott-candidate-{}-{nonce}", std::process::id()));
    fs::create_dir(&root)
        .map_err(|error| format!("create candidate staging {}: {error}", root.display()))?;
    for (relative, bytes) in &emission.files {
        if relative.is_absolute()
            || relative
                .components()
                .any(|component| !matches!(component, Component::Normal(_)))
        {
            let _ = fs::remove_dir_all(&root);
            return Err(format!(
                "candidate artifact has unsafe path {}",
                relative.display()
            ));
        }
        let path = root.join(relative);
        if let Some(parent) = path.parent() {
            fs::create_dir_all(parent).map_err(|error| {
                format!("create candidate directory {}: {error}", parent.display())
            })?;
        }
        fs::write(&path, bytes)
            .map_err(|error| format!("write candidate artifact {}: {error}", path.display()))?;
    }
    Ok(root)
}

struct AgentWorkspace {
    root: PathBuf,
    workspace: PathBuf,
    scratch: PathBuf,
}

fn agent_workspace() -> Result<AgentWorkspace, String> {
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|error| error.to_string())?
        .as_nanos();
    let root = std::env::temp_dir().join(format!("cott-agent-{}-{nonce}", std::process::id()));
    fs::create_dir(&root).map_err(|error| format!("create agent workspace: {error}"))?;
    let workspace = root.join("workspace");
    let scratch = root.join("scratch");
    fs::create_dir(&workspace)
        .and_then(|_| fs::create_dir(&scratch))
        .map_err(|error| format!("create agent workspace directories: {error}"))?;
    Ok(AgentWorkspace {
        root,
        workspace,
        scratch,
    })
}
fn diff_project(
    project_argument: Option<PathBuf>,
    baseline: Option<PathBuf>,
    exit_code: bool,
    format: OutputFormat,
) -> i32 {
    let Ok(root) = project_root(project_argument) else {
        return 2;
    };
    let session = match ProjectSession::acquire(&root) {
        Ok(session) => session,
        Err(error) => {
            eprintln!("error: {error}");
            return 6;
        }
    };
    let root = session.root().to_path_buf();
    let (_, paths) = match load_config_with_paths(&root) {
        Ok(value) => value,
        Err(error) => {
            eprintln!("error: {error}");
            return 2;
        }
    };
    let explicit_baseline = baseline.is_some();
    let baseline_path = match baseline {
        Some(path) if path.is_absolute() => path,
        Some(path) => paths.root.join(path),
        None => match artifact_root_for_paths(&paths) {
            Ok(root) => root.join("generation.json"),
            Err(error) => {
                eprintln!("error: {error}");
                return 2;
            }
        },
    };
    let baseline_bytes = match fs::read(&baseline_path) {
        Ok(bytes) => bytes,
        Err(error) => {
            eprintln!(
                "error: read diff baseline {}: {error}",
                baseline_path.display()
            );
            return 2;
        }
    };
    let baseline_record = match GenerationRecord::parse(&baseline_bytes) {
        Ok(record) => record,
        Err(error) => {
            eprintln!(
                "error: invalid diff baseline {}: {error}",
                baseline_path.display()
            );
            return 2;
        }
    };
    let baseline_snapshot = if explicit_baseline {
        baseline_record.current
    } else {
        let Some(snapshot) = baseline_record.last_verified else {
            eprintln!("error: default diff baseline has no last_verified snapshot");
            return 2;
        };
        snapshot
    };
    let plan = match plan_with_session(session) {
        Ok(plan) => plan,
        Err(code) => return code,
    };
    let current_bytes = plan
        .emission
        .files
        .get(Path::new("generation.json"))
        .expect("compiler emits generation.json");
    let current = match GenerationRecord::parse(current_bytes) {
        Ok(record) => record.current,
        Err(error) => {
            eprintln!("error: invalid compiler generation record: {error}");
            return 1;
        }
    };
    let report = match generation_diff(&baseline_snapshot, &current) {
        Ok(report) => report,
        Err(error) => {
            eprintln!("error: {error}");
            return 2;
        }
    };
    match format {
        OutputFormat::Human => print_diff_report(&report),
        OutputFormat::Json => {
            serde_json::to_writer(std::io::stdout(), &report).expect("diff report is serializable");
            println!();
        }
    }
    if exit_code && (report.breaking || !report.version_compatible) {
        7
    } else {
        0
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
    PythonSymbolAdded,
    PythonSymbolRemoved,
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

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
struct MigrationAdvice {
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
    baseline_version: String,
    current_version: String,
    breaking: bool,
    version_compatible: bool,
    required_version_bump: VersionBump,
    changes: Vec<DiffChange>,
    advice: Vec<MigrationAdvice>,
}

fn generation_diff(
    baseline: &crate::provenance::GenerationSnapshot,
    current: &crate::provenance::GenerationSnapshot,
) -> Result<DiffReport, String> {
    let baseline_version = parse_api_version(&baseline.project_version)
        .ok_or_else(|| "baseline project_version is invalid".to_owned())?;
    let current_version = parse_api_version(&current.project_version)
        .ok_or_else(|| "current project_version is invalid".to_owned())?;
    if current_version < baseline_version {
        return Err(format!(
            "project version regressed from {baseline_version} to {current_version}"
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
                advice.push(MigrationAdvice {
                    kind: DiffKind::DeclarationRemoved,
                    subject: name.clone(),
                    message: format!("Remove uses of declaration `{name}`."),
                });
            }
            Some(updated)
                if normalized_declaration(declaration) != normalized_declaration(updated) =>
            {
                if !structural_declaration_diff(
                    name,
                    declaration,
                    updated,
                    &mut changes,
                    &mut advice,
                ) {
                    push_change(
                        &mut changes,
                        DiffClass::Breaking,
                        DiffKind::SemanticChanged,
                        name,
                        format!("{name} contract changed"),
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
        advice.push(MigrationAdvice {
            kind: DiffKind::DeclarationAdded,
            subject: name.clone(),
            message: format!("Adopt declaration `{name}` where its API is needed."),
        });
    }
    let old_symbols = symbol_sets(&baseline.public_python_symbols);
    let new_symbols = symbol_sets(&current.public_python_symbols);
    for (module, symbols) in &old_symbols {
        for symbol in symbols.iter().filter(|symbol| {
            !new_symbols
                .get(module)
                .is_some_and(|new| new.contains(*symbol))
        }) {
            let subject = format!("{module}.{symbol}");
            push_change(
                &mut changes,
                DiffClass::Breaking,
                DiffKind::PythonSymbolRemoved,
                &subject,
                format!("{subject} Python symbol was removed"),
            );
        }
    }
    for (module, symbols) in &new_symbols {
        for symbol in symbols.iter().filter(|symbol| {
            !old_symbols
                .get(module)
                .is_some_and(|old| old.contains(*symbol))
        }) {
            let subject = format!("{module}.{symbol}");
            push_change(
                &mut changes,
                DiffClass::Additive,
                DiffKind::PythonSymbolAdded,
                &subject,
                format!("{subject} Python symbol was added"),
            );
        }
    }
    compare_implementations(baseline, current, &mut changes);
    if baseline.dependencies != current.dependencies {
        push_change(
            &mut changes,
            DiffClass::Dependency,
            DiffKind::DependencyChanged,
            "dependencies",
            "normalized dependency identity changed".to_owned(),
        );
    }
    for (name, hash) in input_hashes(&baseline.inputs) {
        if current.inputs.get(&name) != Some(&hash)
            && !name.ends_with(".cott")
            && !name.ends_with(".py")
        {
            push_change(
                &mut changes,
                DiffClass::Implementation,
                DiffKind::InputChanged,
                &name,
                format!("{name} input changed"),
            );
        }
    }
    for name in input_hashes(&current.inputs)
        .keys()
        .filter(|name| baseline.inputs.get(*name).is_none())
    {
        if !name.ends_with(".cott") && !name.ends_with(".py") {
            push_change(
                &mut changes,
                DiffClass::Implementation,
                DiffKind::InputChanged,
                name,
                format!("{name} input was added"),
            );
        }
    }
    if same_target_platform(baseline, current) {
        compare_tools(&baseline.tools, &current.tools, &mut changes);
        compare_managed_files(
            &baseline.managed_files,
            &current.managed_files,
            &mut changes,
        );
    }
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
        let subject = format!("{baseline_version} -> {current_version}");
        push_change(
            &mut changes,
            DiffClass::VersionIncompatible,
            DiffKind::VersionIncompatible,
            &subject,
            format!(
                "VERSION INCOMPATIBLE: {required_version_bump:?} bump required for API changes"
            ),
        );
    }
    Ok(DiffReport {
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

fn structural_declaration_diff(
    subject: &str,
    old: &serde_json::Value,
    new: &serde_json::Value,
    changes: &mut Vec<DiffChange>,
    advice: &mut Vec<MigrationAdvice>,
) -> bool {
    let mut recognized = false;
    let mut structural_changes = Vec::new();
    let mut structural_advice = Vec::new();
    for (field, added, removed, added_kind, removed_kind) in [
        (
            "parameters",
            "required parameter",
            "required parameter",
            DiffKind::RequiredParameterAdded,
            DiffKind::RequiredParameterRemoved,
        ),
        (
            "fields",
            "field",
            "field",
            DiffKind::FieldAdded,
            DiffKind::FieldRemoved,
        ),
        (
            "variants",
            "enum variant",
            "enum variant",
            DiffKind::EnumVariantAdded,
            DiffKind::EnumVariantRemoved,
        ),
    ] {
        let Some(old_members) = named_members(old, field) else {
            continue;
        };
        let Some(new_members) = named_members(new, field) else {
            return false;
        };
        for (name, value) in &old_members {
            match new_members.get(name) {
                None => {
                    recognized = true;
                    let member = format!("{subject}.{name}");
                    push_change(
                        &mut structural_changes,
                        DiffClass::Breaking,
                        removed_kind,
                        &member,
                        format!("{member} {removed} was removed"),
                    );
                    structural_advice.push(MigrationAdvice {
                        kind: removed_kind,
                        subject: member,
                        message: format!("Remove uses of the removed {removed} `{name}`."),
                    });
                }
                Some(updated)
                    if normalized_declaration(value) != normalized_declaration(updated) =>
                {
                    return false;
                }
                Some(_) => {}
            }
        }
        for name in new_members
            .keys()
            .filter(|name| !old_members.contains_key(*name))
        {
            recognized = true;
            let member = format!("{subject}.{name}");
            push_change(
                &mut structural_changes,
                DiffClass::Breaking,
                added_kind,
                &member,
                format!("{member} {added} was added"),
            );
            structural_advice.push(MigrationAdvice {
                kind: added_kind,
                subject: member,
                message: format!("Supply the new {added} `{name}` where required."),
            });
        }
    }
    if let Some(old_methods) = named_members(old, "methods") {
        let Some(new_methods) = named_members(new, "methods") else {
            return false;
        };
        if old_methods.len() != new_methods.len() {
            return false;
        }
        for (name, method) in old_methods {
            let Some(updated) = new_methods.get(&name) else {
                return false;
            };
            if normalized_declaration(&method) != normalized_declaration(updated) {
                let mut method_changes = Vec::new();
                let mut method_advice = Vec::new();
                if !structural_declaration_diff(
                    &format!("{subject}.{name}"),
                    &method,
                    updated,
                    &mut method_changes,
                    &mut method_advice,
                ) {
                    return false;
                }
                recognized = true;
                structural_changes.extend(method_changes);
                structural_advice.extend(method_advice);
            }
        }
    }
    if !recognized {
        return false;
    }
    let mut old = normalized_declaration(old);
    let mut new = normalized_declaration(new);
    for field in ["parameters", "fields", "variants", "methods"] {
        old.as_object_mut()
            .expect("declaration is an object")
            .remove(field);
        new.as_object_mut()
            .expect("declaration is an object")
            .remove(field);
    }
    if old != new {
        return false;
    }
    changes.extend(structural_changes);
    advice.extend(structural_advice);
    true
}

fn named_members(
    value: &serde_json::Value,
    field: &str,
) -> Option<BTreeMap<String, serde_json::Value>> {
    value
        .get(field)?
        .as_array()?
        .iter()
        .map(|member| Some((member.get("name")?.as_str()?.to_owned(), member.clone())))
        .collect()
}

fn print_diff_report(report: &DiffReport) {
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
        let changes = report
            .changes
            .iter()
            .filter(|change| change.class == class)
            .collect::<Vec<_>>();
        if changes.is_empty() {
            continue;
        }
        println!("{}:", diff_class_heading(class));
        for change in changes {
            println!("- {}", change.message);
        }
    }
    if !report.advice.is_empty() {
        println!("MIGRATION ADVICE:");
        for advice in &report.advice {
            println!("- {}", advice.message);
        }
    }
}

fn diff_class_heading(class: DiffClass) -> &'static str {
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
}

fn declarations_by_name(value: &serde_json::Value) -> BTreeMap<String, serde_json::Value> {
    value
        .as_object()
        .into_iter()
        .flat_map(|modules| modules.iter())
        .flat_map(|(module_name, module)| {
            module
                .get("declarations")
                .and_then(serde_json::Value::as_array)
                .into_iter()
                .flatten()
                .filter_map(move |declaration| {
                    let name = declaration.get("name")?.as_str()?;
                    let subject = name
                        .contains('.')
                        .then(|| name.to_owned())
                        .unwrap_or_else(|| format!("{module_name}.{name}"));
                    Some((subject, declaration.clone()))
                })
        })
        .collect()
}

fn normalized_declaration(value: &serde_json::Value) -> serde_json::Value {
    fn strip(value: &mut serde_json::Value) {
        match value {
            serde_json::Value::Object(object) => {
                object.remove("doc");
                object.remove("span");
                object.remove("source_order");
                for value in object.values_mut() {
                    strip(value);
                }
            }
            serde_json::Value::Array(values) => {
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

fn symbol_sets(value: &serde_json::Value) -> BTreeMap<String, std::collections::BTreeSet<String>> {
    value
        .as_object()
        .into_iter()
        .flat_map(|modules| modules.iter())
        .map(|(module, symbols)| {
            (
                module.clone(),
                symbols
                    .as_array()
                    .into_iter()
                    .flatten()
                    .filter_map(serde_json::Value::as_str)
                    .map(str::to_owned)
                    .collect(),
            )
        })
        .collect()
}

fn same_target_platform(
    baseline: &crate::provenance::GenerationSnapshot,
    current: &crate::provenance::GenerationSnapshot,
) -> bool {
    let Some(baseline) = baseline
        .tools
        .get("python")
        .and_then(serde_json::Value::as_object)
    else {
        return false;
    };
    let Some(current) = current
        .tools
        .get("python")
        .and_then(serde_json::Value::as_object)
    else {
        return false;
    };
    ["os", "machine", "platform"].into_iter().all(|field| {
        baseline
            .get(field)
            .is_some_and(|value| current.get(field) == Some(value))
    })
}

fn compare_tools(
    baseline: &serde_json::Value,
    current: &serde_json::Value,
    changes: &mut Vec<DiffChange>,
) {
    let baseline = baseline.as_object();
    let current = current.as_object();
    let tools = baseline
        .into_iter()
        .flat_map(|tools| tools.keys())
        .chain(current.into_iter().flat_map(|tools| tools.keys()))
        .cloned()
        .collect::<BTreeSet<_>>();
    for tool in tools {
        let before = baseline.and_then(|tools| tools.get(&tool));
        let after = current.and_then(|tools| tools.get(&tool));
        if before == after {
            continue;
        }
        let message = match (before, after) {
            (None, Some(_)) => format!("{tool} toolchain was added"),
            (Some(_), None) => format!("{tool} toolchain was removed"),
            (Some(_), Some(_)) => format!("{tool} toolchain changed"),
            (None, None) => unreachable!("tool belongs to a comparison index"),
        };
        push_change(
            changes,
            DiffClass::Toolchain,
            DiffKind::ToolchainChanged,
            &tool,
            message,
        );
    }
}

fn compare_managed_files(
    baseline: &BTreeMap<String, String>,
    current: &BTreeMap<String, String>,
    changes: &mut Vec<DiffChange>,
) {
    for path in baseline
        .keys()
        .chain(current.keys())
        .cloned()
        .collect::<BTreeSet<_>>()
    {
        let before = baseline.get(&path);
        let after = current.get(&path);
        if before == after {
            continue;
        }
        let message = match (before, after) {
            (None, Some(_)) => format!("{path} artifact was added"),
            (Some(_), None) => format!("{path} artifact was removed"),
            (Some(_), Some(_)) => format!("{path} artifact changed"),
            (None, None) => unreachable!("artifact belongs to a comparison index"),
        };
        push_change(
            changes,
            DiffClass::Artifact,
            DiffKind::ArtifactChanged,
            &path,
            message,
        );
    }
}

fn compare_implementations(
    baseline: &crate::provenance::GenerationSnapshot,
    current: &crate::provenance::GenerationSnapshot,
    changes: &mut Vec<DiffChange>,
) {
    for entry in compare_implementation_identities(Some(baseline), current).entries {
        let message = match entry.status {
            "added" => format!("{} implementation was added", entry.cott_symbol),
            "removed" => format!("{} implementation was removed", entry.cott_symbol),
            "changed" => format!(
                "{} implementation changed: {}",
                entry.cott_symbol,
                entry
                    .changed_fields
                    .keys()
                    .map(String::as_str)
                    .collect::<Vec<_>>()
                    .join(", ")
            ),
            "unchanged" => continue,
            _ => unreachable!("implementation comparison has a known status"),
        };
        let async_kind_change = entry.changed_fields.get("kind").is_some_and(|change| {
            matches!(
                (&change.before, &change.after),
                (
                    serde_json::Value::String(before),
                    serde_json::Value::String(after)
                ) if (before == "function" && after == "async_function")
                    || (before == "async_function" && after == "function")
            )
        });
        push_change(
            changes,
            if async_kind_change {
                DiffClass::Breaking
            } else {
                DiffClass::Implementation
            },
            if async_kind_change {
                DiffKind::SemanticChanged
            } else {
                DiffKind::ImplementationChanged
            },
            &entry.cott_symbol,
            message,
        );
    }
}

fn input_hashes(value: &serde_json::Value) -> BTreeMap<String, serde_json::Value> {
    value
        .as_object()
        .into_iter()
        .flat_map(|inputs| inputs.iter())
        .map(|(name, hash)| (name.clone(), hash.clone()))
        .collect()
}

fn resolve_executable(name: &str) -> Result<PathBuf, String> {
    let path =
        std::env::var_os("PATH").ok_or_else(|| format!("missing PATH while locating {name}"))?;
    for directory in std::env::split_paths(&path) {
        let candidate = directory.join(name);
        if fs::metadata(&candidate).is_ok_and(|metadata| metadata.is_file()) {
            return fs::canonicalize(&candidate)
                .map_err(|error| format!("canonicalize {}: {error}", candidate.display()));
        }
    }
    Err(format!("{name} executable was not found on PATH"))
}

fn print_binding_diagnostics(
    paths: &ProjectPaths,
    diagnostics: Vec<crate::binding::BindingDiagnostic>,
) {
    for diagnostic in diagnostics {
        eprintln!(
            "error: {}: {}",
            display_path(&paths.root, &diagnostic.path),
            diagnostic.message
        );
    }
}

fn project_root(project: Option<PathBuf>) -> Result<PathBuf, i32> {
    project
        .or_else(|| std::env::current_dir().ok())
        .ok_or_else(|| {
            eprintln!("error: failed to determine current directory");
            2
        })
}

fn target_name(target: TargetLanguage) -> &'static str {
    match target {
        TargetLanguage::Python => "python",
        TargetLanguage::Kotlin => "kotlin",
        TargetLanguage::Dart => "dart",
    }
}

fn selected_project_target(project: &Option<PathBuf>) -> Result<TargetLanguage, String> {
    let root = project
        .clone()
        .or_else(|| std::env::current_dir().ok())
        .ok_or_else(|| "failed to determine current directory".to_owned())?;
    load_target_language(&root).map_err(|error| error.to_string())
}

fn target_selection_failure(format: OutputFormat, message: impl AsRef<str>) -> i32 {
    prompt_fail(format, 2, message)
}

fn target_mismatch(requested: TargetLanguage, actual: TargetLanguage) -> i32 {
    eprintln!(
        "error: requested target `{}` does not match project target `{}`",
        target_name(requested),
        target_name(actual)
    );
    2
}

fn finish_kotlin_unit(result: Result<(), crate::kotlin::pipeline::Failure>) -> i32 {
    match result {
        Ok(()) => 0,
        Err(failure) => {
            eprintln!("error: {}", failure.message);
            failure.code
        }
    }
}

fn finish_kotlin_init(result: Result<PathBuf, crate::kotlin::pipeline::Failure>) -> i32 {
    finish_kotlin_unit(result.map(|_| ()))
}

fn finish_kotlin_path(result: Result<PathBuf, crate::kotlin::pipeline::Failure>) -> i32 {
    match result {
        Ok(path) => {
            println!("{}", path.display());
            0
        }
        Err(failure) => {
            eprintln!("error: {}", failure.message);
            failure.code
        }
    }
}

fn finish_kotlin_verification(result: Result<PathBuf, crate::kotlin::pipeline::Failure>) -> i32 {
    match result {
        Ok(path) => {
            println!("verified {}", path.display());
            0
        }
        Err(failure) => {
            eprintln!("error: {}", failure.message);
            failure.code
        }
    }
}

fn finish_dart_unit(result: Result<(), crate::dart::pipeline::Failure>) -> i32 {
    match result {
        Ok(()) => 0,
        Err(failure) => {
            eprintln!("error: {}", failure.message);
            failure.code
        }
    }
}

fn finish_dart_init(result: Result<PathBuf, crate::dart::pipeline::Failure>) -> i32 {
    finish_dart_unit(result.map(|_| ()))
}

fn finish_dart_path(result: Result<PathBuf, crate::dart::pipeline::Failure>) -> i32 {
    match result {
        Ok(path) => {
            println!("{}", path.display());
            0
        }
        Err(failure) => {
            eprintln!("error: {}", failure.message);
            failure.code
        }
    }
}

fn finish_dart_verification(result: Result<PathBuf, crate::dart::pipeline::Failure>) -> i32 {
    match result {
        Ok(path) => {
            println!("verified {}", path.display());
            0
        }
        Err(failure) => {
            eprintln!("error: {}", failure.message);
            failure.code
        }
    }
}

fn check_for_target(project: Option<PathBuf>, source: Option<PathBuf>) -> i32 {
    match selected_project_target(&project) {
        Ok(TargetLanguage::Python) => check_project(project, source),
        Ok(TargetLanguage::Kotlin) => {
            finish_kotlin_unit(crate::kotlin::pipeline::check(project, source))
        }
        Ok(TargetLanguage::Dart) => finish_dart_unit(crate::dart::pipeline::check(project, source)),
        Err(message) => target_selection_failure(OutputFormat::Human, message),
    }
}

fn format_for_target(project: Option<PathBuf>, check: bool) -> i32 {
    match selected_project_target(&project) {
        Ok(TargetLanguage::Python) => format_project(project, check),
        Ok(TargetLanguage::Kotlin) => {
            finish_kotlin_unit(crate::kotlin::pipeline::format(project, check))
        }
        Ok(TargetLanguage::Dart) => finish_dart_unit(crate::dart::pipeline::format(project, check)),
        Err(message) => target_selection_failure(OutputFormat::Human, message),
    }
}

fn emit_python_project(project: Option<PathBuf>) -> i32 {
    match plan(project) {
        Ok(plan) => match publish(&plan) {
            Ok(()) => {
                println!("{}", generated_path(&plan.paths));
                0
            }
            Err(message) => {
                eprintln!("error: {message}");
                6
            }
        },
        Err(code) => code,
    }
}

fn emit_for_target(project: Option<PathBuf>, requested: EmitTarget) -> i32 {
    let actual = match selected_project_target(&project) {
        Ok(target) => target,
        Err(message) => return target_selection_failure(OutputFormat::Human, message),
    };
    match (requested, actual) {
        (EmitTarget::Ir, TargetLanguage::Python) => emit_ir(project),
        (EmitTarget::Ir, TargetLanguage::Kotlin) => {
            finish_kotlin_path(crate::kotlin::pipeline::emit(project, true))
        }
        (EmitTarget::Ir, TargetLanguage::Dart) => {
            finish_dart_path(crate::dart::pipeline::emit(project, true))
        }
        (EmitTarget::Python, TargetLanguage::Python) => emit_python_project(project),
        (EmitTarget::Kotlin, TargetLanguage::Kotlin) => {
            finish_kotlin_path(crate::kotlin::pipeline::emit(project, false))
        }
        (EmitTarget::Dart, TargetLanguage::Dart) => {
            finish_dart_path(crate::dart::pipeline::emit(project, false))
        }
        (EmitTarget::Python, actual @ (TargetLanguage::Kotlin | TargetLanguage::Dart)) => {
            target_mismatch(TargetLanguage::Python, actual)
        }
        (EmitTarget::Kotlin, actual @ (TargetLanguage::Python | TargetLanguage::Dart)) => {
            target_mismatch(TargetLanguage::Kotlin, actual)
        }
        (EmitTarget::Dart, actual @ (TargetLanguage::Python | TargetLanguage::Kotlin)) => {
            target_mismatch(TargetLanguage::Dart, actual)
        }
    }
}

fn generate_for_target(
    project: Option<PathBuf>,
    requested: TargetLanguage,
    symbol: Option<String>,
    agent: Option<AgentKind>,
    jobs: usize,
) -> i32 {
    let actual = match selected_project_target(&project) {
        Ok(target) => target,
        Err(message) => return target_selection_failure(OutputFormat::Human, message),
    };
    if actual != requested {
        return target_mismatch(requested, actual);
    }
    match requested {
        TargetLanguage::Python => generate_project(project, symbol, agent, jobs),
        TargetLanguage::Kotlin => crate::kotlin::generation::generate(project, symbol, agent, jobs),
        TargetLanguage::Dart => crate::dart::generation::generate(project, symbol, agent, jobs),
    }
}

fn prompt_for_target(project: Option<PathBuf>, symbol: String, format: OutputFormat) -> i32 {
    match selected_project_target(&project) {
        Ok(TargetLanguage::Python) => prompt_project(project, symbol, format),
        Ok(TargetLanguage::Kotlin) => crate::kotlin::prompt::prompt(project, symbol, format),
        Ok(TargetLanguage::Dart) => crate::dart::prompt::prompt(project, symbol, format),
        Err(message) => target_selection_failure(format, message),
    }
}

fn verify_python_project(project: Option<PathBuf>) -> i32 {
    match plan(project) {
        Ok(plan) => match verify(&plan) {
            Ok(()) => {
                println!("verified {}", generated_path(&plan.paths));
                0
            }
            Err(messages) => {
                let contract_failure = messages.iter().any(|message| {
                    crate::proof::is_disproved_error(message)
                        || message.starts_with(COVERAGE_POLICY_PREFIX)
                });
                for message in messages {
                    eprintln!("error: {message}");
                }
                if contract_failure { 3 } else { 4 }
            }
        },
        Err(code) => code,
    }
}

fn verify_for_target(project: Option<PathBuf>) -> i32 {
    match selected_project_target(&project) {
        Ok(TargetLanguage::Python) => verify_python_project(project),
        Ok(TargetLanguage::Kotlin) => {
            finish_kotlin_verification(crate::kotlin::pipeline::verify(project))
        }
        Ok(TargetLanguage::Dart) => {
            finish_dart_verification(crate::dart::pipeline::verify(project))
        }
        Err(message) => target_selection_failure(OutputFormat::Human, message),
    }
}

fn diff_for_target(
    project: Option<PathBuf>,
    baseline: Option<PathBuf>,
    exit_code: bool,
    format: OutputFormat,
) -> i32 {
    match selected_project_target(&project) {
        Ok(TargetLanguage::Python) => diff_project(project, baseline, exit_code, format),
        Ok(TargetLanguage::Kotlin) => {
            crate::kotlin::pipeline::diff(project, baseline, exit_code, format)
        }
        Ok(TargetLanguage::Dart) => {
            crate::dart::pipeline::diff(project, baseline, exit_code, format)
        }
        Err(message) => target_selection_failure(format, message),
    }
}

fn deploy_for_target(project: Option<PathBuf>, output: Option<PathBuf>, replace: bool) -> i32 {
    match selected_project_target(&project) {
        Ok(TargetLanguage::Python) => deploy_project(project, output, replace),
        Ok(TargetLanguage::Kotlin) => finish_kotlin_path(deploy_language(
            project,
            output,
            replace,
            TargetLanguage::Kotlin,
            crate::kotlin::pipeline::deploy,
            |code, message| crate::kotlin::pipeline::Failure::new(code, message),
        )),
        Ok(TargetLanguage::Dart) => finish_dart_path(deploy_language(
            project,
            output,
            replace,
            TargetLanguage::Dart,
            crate::dart::pipeline::deploy,
            |code, message| crate::dart::pipeline::Failure::new(code, message),
        )),
        Err(message) => target_selection_failure(OutputFormat::Human, message),
    }
}

fn python_replace_context(
    paths: &ProjectPaths,
    project_name: &str,
) -> Result<crate::deploy::ReplaceContext, String> {
    Ok(crate::deploy::ReplaceContext {
        root: paths.root.clone(),
        source_dir: paths.source_dir.clone(),
        language_source_dir: paths.python_source_dir.clone(),
        artifact_root: artifact_root_for_paths(paths)?,
        extra_protected: vec![
            paths.stubs_dir.clone(),
            paths.root.join(".cott"),
            paths.root.join(".venv"),
        ],
        project_name: project_name.to_owned(),
        language: TargetLanguage::Python,
    })
}

fn resolve_deploy_output(
    root: &Path,
    name: &str,
    version: &str,
    output: Option<PathBuf>,
) -> Result<PathBuf, String> {
    match output {
        Some(path) if path.is_absolute() => Ok(path),
        Some(path) => match std::env::current_dir() {
            Ok(cwd) => Ok(cwd.join(path)),
            Err(error) => Err(format!("determine deployment directory: {error}")),
        },
        None => Ok(root.join("dist").join(format!("{name}-{version}"))),
    }
}

fn deploy_language<E>(
    project: Option<PathBuf>,
    output: Option<PathBuf>,
    replace: bool,
    language: TargetLanguage,
    deploy: impl FnOnce(Option<PathBuf>, Option<PathBuf>) -> Result<PathBuf, E>,
    error: impl Fn(i32, String) -> E,
) -> Result<PathBuf, E> {
    if !replace {
        return deploy(project, output);
    }
    let context_and_target = language_replace_plan(project.clone(), output.clone(), language)
        .map_err(|message| error(6, message))?;
    match context_and_target {
        LanguageReplacePlan::Create => deploy(project, output),
        LanguageReplacePlan::Replace { target, staging } => {
            match deploy(project, Some(staging.clone())) {
                Ok(_) => crate::deploy::publish_replace(&staging, &target)
                    .map(|()| target)
                    .map_err(|message| {
                        let _ = crate::deploy::remove_tree_if_present(&staging);
                        error(6, message)
                    }),
                Err(failure) => {
                    let _ = crate::deploy::remove_tree_if_present(&staging);
                    Err(failure)
                }
            }
        }
    }
}

enum LanguageReplacePlan {
    Create,
    Replace { target: PathBuf, staging: PathBuf },
}

fn language_replace_plan(
    project: Option<PathBuf>,
    output: Option<PathBuf>,
    language: TargetLanguage,
) -> Result<LanguageReplacePlan, String> {
    let root = project
        .clone()
        .or_else(|| std::env::current_dir().ok())
        .ok_or_else(|| "failed to determine current directory".to_owned())?;
    let (context, target) = match language {
        TargetLanguage::Python => {
            return Err("Python replace is handled by the Python deploy path".to_owned());
        }
        TargetLanguage::Kotlin => {
            let (config, paths, _) =
                load_kotlin_config_with_paths(&root).map_err(|error| error.to_string())?;
            let target = resolve_deploy_output(
                &paths.root,
                &config.project.name,
                &config.project.version,
                output,
            )?;
            let context = crate::deploy::ReplaceContext {
                extra_protected: vec![paths.root.join(".cott")],
                root: paths.root,
                source_dir: paths.source_dir,
                language_source_dir: paths.kotlin_source_dir,
                artifact_root: paths.artifact_root,
                project_name: config.project.name,
                language: TargetLanguage::Kotlin,
            };
            (context, target)
        }
        TargetLanguage::Dart => {
            let (config, paths, _) =
                load_dart_config_with_paths(&root).map_err(|error| error.to_string())?;
            let target = resolve_deploy_output(
                &paths.root,
                &config.project.name,
                &config.project.version,
                output,
            )?;
            let context = crate::deploy::ReplaceContext {
                extra_protected: vec![paths.root.join(".cott")],
                root: paths.root,
                source_dir: paths.source_dir,
                language_source_dir: paths.dart_source_dir,
                artifact_root: paths.artifact_root,
                project_name: config.project.name,
                language: TargetLanguage::Dart,
            };
            (context, target)
        }
    };
    match fs::symlink_metadata(&target) {
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            Ok(LanguageReplacePlan::Create)
        }
        Err(error) => Err(format!(
            "deployment output is not a replaceable Cott deployment: inspect {}: {error}",
            target.display()
        )),
        Ok(_) => {
            crate::deploy::require_replaceable(&context, &target)?;
            Ok(LanguageReplacePlan::Replace {
                staging: crate::deploy::sibling_temp(&target, "replace")?,
                target,
            })
        }
    }
}

fn check_project(project_argument: Option<PathBuf>, selected: Option<PathBuf>) -> i32 {
    let Ok(root) = project_root(project_argument) else {
        return 2;
    };
    let session = match ProjectSession::acquire(&root) {
        Ok(session) => session,
        Err(error) => {
            eprintln!("error: {error}");
            return 6;
        }
    };
    let (config, paths) = match load_config_with_paths(session.root()) {
        Ok(config) => config,
        Err(error) => {
            eprintln!("error: {error}");
            return 2;
        }
    };
    if let Err(diagnostics) = audit_authored_python(&paths) {
        for diagnostic in diagnostics {
            eprintln!("error: {diagnostic}");
        }
        return 4;
    }
    if let Some(selected) = selected {
        let selected = paths.root.join(selected);
        let valid = selected
            .extension()
            .is_some_and(|extension| extension == "cott")
            && selected.starts_with(&paths.source_dir)
            && fs::symlink_metadata(&selected)
                .is_ok_and(|metadata| metadata.is_file() && !metadata.file_type().is_symlink());
        if !valid {
            eprintln!("error: check source must be a regular .cott file beneath project.source");
            return 2;
        }
    }
    let sources = match discover_sources_from_paths(&paths) {
        Ok(sources) => sources,
        Err(error) => {
            eprintln!("error: {error}");
            return 2;
        }
    };
    let parsed = match parse_project(sources) {
        Ok(parsed) => parsed,
        Err(diagnostics) => {
            print_project_diagnostics(&diagnostics);
            return 3;
        }
    };
    let custom_effects = config.effects.keys().cloned().collect();
    match lower_with_effects(&paths.source_dir, parsed, &custom_effects) {
        Ok(hir) => match render(&hir).and_then(|ir| shadow_warnings(&config, &paths, &ir)) {
            Ok(warnings) => {
                for warning in warnings {
                    eprintln!("warning: {warning}");
                }
                0
            }
            Err(error) => {
                eprintln!("error: {error}");
                3
            }
        },
        Err(diagnostics) => {
            print_project_diagnostics(&diagnostics);
            3
        }
    }
}
fn supports_uv_version(version: &str) -> bool {
    version
        .strip_prefix("uv ")
        .is_some_and(|version| is_at_least(version, (0, 12, 3)))
}

fn supports_basedpyright_version(version: &str) -> bool {
    let version = version
        .lines()
        .next()
        .unwrap_or_default()
        .strip_prefix("basedpyright ")
        .unwrap_or(version);
    is_at_least(version, (1, 39, 9))
}

fn supports_python_version(version: &str) -> bool {
    parse_version(version)
        .is_some_and(|(major, minor, patch)| (major, minor) == (3, 14) && patch >= 6)
}

fn init_project(path: PathBuf, name: Option<String>, no_sync: bool, format: OutputFormat) -> i32 {
    let absolute = if path.is_absolute() {
        path
    } else {
        match std::env::current_dir() {
            Ok(current) => current.join(path),
            Err(error) => {
                eprintln!("error: determine init directory: {error}");
                return 2;
            }
        }
    };
    let Some(final_name) = absolute.file_name().filter(|name| !name.is_empty()) else {
        eprintln!("error: init path must have one non-empty final component");
        return 2;
    };
    if !matches!(
        absolute.components().next_back(),
        Some(Component::Normal(_))
    ) {
        eprintln!("error: init path must not end in `.` or `..`");
        return 2;
    }
    let Some(parent) = absolute.parent() else {
        eprintln!("error: init path has no parent");
        return 2;
    };
    let parent = match fs::canonicalize(parent) {
        Ok(parent) if parent.is_dir() => parent,
        Ok(_) => {
            eprintln!("error: init parent is not a directory");
            return 2;
        }
        Err(error) => {
            eprintln!("error: resolve init parent {}: {error}", parent.display());
            return 2;
        }
    };
    let target = parent.join(final_name);
    let project_name = name.or_else(|| final_name.to_str().map(ToOwned::to_owned));
    let Some(project_name) = project_name.filter(|name| valid_project_name(name)) else {
        eprintln!("error: init project name must be lowercase kebab-case");
        return 2;
    };
    if fs::symlink_metadata(&target).is_ok() {
        eprintln!("error: init target already exists: {}", target.display());
        return 2;
    }
    let uv = match resolve_executable("uv") {
        Ok(path) => path,
        Err(error) => {
            eprintln!("error: {error}");
            return 2;
        }
    };
    let environment = match uv_environment(&uv) {
        Ok(environment) => environment,
        Err(error) => {
            eprintln!("error: {error}");
            return 2;
        }
    };
    let version = match run_clean(
        &uv,
        &["--version"],
        &parent,
        &environment,
        Duration::from_secs(30),
    ) {
        Ok(output) if output.status == Some(0) => {
            String::from_utf8_lossy(&output.stdout).trim().to_owned()
        }
        Ok(output) => {
            eprintln!(
                "error: probe uv failed: {}",
                String::from_utf8_lossy(&output.stderr).trim()
            );
            return 2;
        }
        Err(error) => {
            eprintln!("error: probe uv: {error}");
            return 2;
        }
    };
    if !supports_uv_version(&version) {
        eprintln!(
            "error: cott {} requires uv >=0.12.3, found `{version}`",
            env!("CARGO_PKG_VERSION")
        );
        return 2;
    }

    let nonce = format!(
        "{:x}-{:x}",
        std::process::id(),
        SystemTime::now()
            .duration_since(UNIX_EPOCH)
            .map_or(0, |duration| duration.as_nanos())
    );
    let temporary = parent.join(format!(".cott-init-{nonce}"));
    let marker = format!(
        "{{\"nonce\":{},\"schema_version\":1}}\n",
        serde_json::json!(nonce)
    );
    let scaffold = publish_init_scaffold(
        &temporary,
        &target,
        &parent,
        &project_name,
        marker.as_bytes(),
    );
    if let Err(error) = scaffold {
        let collision = error.starts_with("init target already exists:");
        let cleanup = remove_owned_init_temp(&temporary, marker.as_bytes(), &parent);
        if let Err(cleanup) = cleanup {
            eprintln!("error: {error}; cleanup failed: {cleanup}");
            return 6;
        }
        eprintln!("error: {error}");
        return if collision { 2 } else { 6 };
    }

    let uv_result = initialize_python(&uv, &target, &environment, no_sync);
    let managed_interpreter = match uv_result {
        Ok(interpreter) => interpreter,
        Err(error) => {
            let cleanup = remove_owned_init(&target, marker.as_bytes(), &parent);
            if let Err(cleanup) = cleanup {
                eprintln!("error: {error}; init cleanup failed: {cleanup}");
                return 6;
            }
            eprintln!("error: {error}");
            return 5;
        }
    };
    if let Err(error) = commit_init(&target, marker.as_bytes(), &parent) {
        eprintln!("error: commit init scaffold: {error}");
        return 6;
    }
    if no_sync {
        print_sync_note(&format, &uv, &target, &managed_interpreter, &environment);
    }
    0
}

fn matching_init_marker(directory: &Path, marker: &[u8]) -> bool {
    let path = directory.join(".cott-init");
    fs::symlink_metadata(&path).is_ok_and(|metadata| {
        metadata.is_file()
            && metadata.nlink() == 1
            && fs::read(&path).is_ok_and(|bytes| bytes == marker)
    })
}

fn publish_init_scaffold(
    temporary: &Path,
    target: &Path,
    parent: &Path,
    project_name: &str,
    marker: &[u8],
) -> Result<(), String> {
    let module = project_name.replace('-', "_");
    DirBuilder::new()
        .mode(0o700)
        .create(temporary)
        .map_err(|error| format!("create private init scaffold: {error}"))?;
    fs::create_dir_all(temporary.join("src").join(&module))
        .map_err(|error| format!("create source scaffold: {error}"))?;
    fs::create_dir_all(temporary.join("python"))
        .map_err(|error| format!("create Python scaffold: {error}"))?;
    write_private(&temporary.join(".cott-init"), marker)?;
    write_private(
        &temporary.join(".gitignore"),
        b".cott/\n.venv/\ngenerated/generation.json\n__pycache__/\n*.py[cod]\n",
    )?;
    write_private(
        &temporary.join("cott.toml"),
        format!(
            "[project]\nname = \"{project_name}\"\nversion = \"0.1.0\"\nsource = \"src\"\n\n[target.python]\nsource = \"python\"\ngenerated = \"generated/python\"\nstubs = \"generated/stubs\"\nlockfile = \"python/uv.lock\"\ninterpreter = \".venv/bin/python\"\ntype_checker = \".venv/bin/basedpyright\"\nruntime_validation = \"boundary\"\n"
        )
        .as_bytes(),
    )?;
    write_private(
        &temporary.join("src").join(&module).join("main.cott"),
        format!("module {module}.main\n").as_bytes(),
    )?;
    write_private(&temporary.join("python/.python-version"), b"3.14\n")?;
    write_private(
        &temporary.join("python/pyproject.toml"),
        format!(
            "[project]\nname = \"{project_name}\"\nversion = \"0.1.0\"\nrequires-python = \">=3.14.6,<3.15\"\ndependencies = []\n\n[dependency-groups]\ndev = [\"basedpyright>=1.39.9\"]\n"
        )
        .as_bytes(),
    )?;
    sync_tree(temporary)?;
    rename_noreplace(temporary, target)?;
    sync_parent(parent, "init.publish.parent_fsync")
}

fn sync_parent(parent: &Path, fault_name: &'static str) -> Result<(), String> {
    init_fault(fault_name)?;
    File::open(parent)
        .and_then(|directory| directory.sync_all())
        .map_err(|error| format!("sync init parent: {error}"))
}

fn commit_init(target: &Path, marker: &[u8], parent: &Path) -> Result<(), String> {
    if !matching_init_marker(target, marker) {
        return Err("refusing to commit init target without matching ownership marker".to_owned());
    }
    init_fault("init.commit.marker_unlink")?;
    fs::remove_file(target.join(".cott-init"))
        .map_err(|error| format!("remove init ownership marker: {error}"))?;
    init_fault("init.commit.target_fsync")?;
    File::open(target)
        .and_then(|directory| directory.sync_all())
        .map_err(|error| format!("sync committed init target: {error}"))?;
    sync_parent(parent, "init.commit.parent_fsync")
}

fn write_private(path: &Path, bytes: &[u8]) -> Result<(), String> {
    let mut file = OpenOptions::new()
        .create_new(true)
        .write(true)
        .mode(0o600)
        .open(path)
        .map_err(|error| format!("create scaffold file {}: {error}", path.display()))?;
    file.write_all(bytes)
        .map_err(|error| format!("write scaffold file {}: {error}", path.display()))?;
    init_fault("init.scaffold.file_fsync")?;
    file.sync_all()
        .map_err(|error| format!("write scaffold file {}: {error}", path.display()))
}

fn sync_tree(path: &Path) -> Result<(), String> {
    let mut entries = fs::read_dir(path)
        .map_err(|error| format!("read scaffold directory {}: {error}", path.display()))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|error| format!("read scaffold directory {}: {error}", path.display()))?;
    entries.sort_by_key(|entry| entry.file_name());
    for entry in entries {
        let metadata = fs::symlink_metadata(entry.path())
            .map_err(|error| format!("inspect scaffold {}: {error}", entry.path().display()))?;
        if metadata.file_type().is_symlink() {
            return Err(format!(
                "scaffold contains a symlink: {}",
                entry.path().display()
            ));
        }
        if metadata.is_dir() {
            sync_tree(&entry.path())?;
        } else if metadata.is_file() {
            init_fault("init.scaffold.tree_file_fsync")?;
            File::open(entry.path())
                .and_then(|file| file.sync_all())
                .map_err(|error| format!("sync scaffold file: {error}"))?;
        } else {
            return Err(format!(
                "scaffold contains a special file: {}",
                entry.path().display()
            ));
        }
    }
    init_fault("init.scaffold.directory_fsync")?;
    File::open(path)
        .and_then(|directory| directory.sync_all())
        .map_err(|error| format!("sync scaffold directory {}: {error}", path.display()))
}

fn rename_noreplace(source: &Path, target: &Path) -> Result<(), String> {
    let source = CString::new(source.as_os_str().as_bytes())
        .map_err(|_| "init temporary path contains NUL".to_owned())?;
    let target_bytes = target.as_os_str().as_bytes();
    let target_c =
        CString::new(target_bytes).map_err(|_| "init target path contains NUL".to_owned())?;
    init_fault("init.publish.noreplace")?;
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
            Err(format!(
                "init target already exists: {}",
                String::from_utf8_lossy(target_bytes)
            ))
        } else {
            Err(format!("atomically publish init scaffold: {error}"))
        }
    }
}

fn remove_owned_init_temp(temporary: &Path, marker: &[u8], parent: &Path) -> Result<(), String> {
    let metadata = match fs::symlink_metadata(temporary) {
        Ok(metadata) => metadata,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(()),
        Err(error) => return Err(format!("inspect init temporary scaffold: {error}")),
    };
    if metadata.file_type().is_symlink()
        || !metadata.is_dir()
        || !matching_init_marker(temporary, marker)
    {
        return Err(
            "refusing to remove init temporary without matching ownership marker".to_owned(),
        );
    }
    init_fault("init.cleanup.temp_remove")?;
    fs::remove_dir_all(temporary)
        .map_err(|error| format!("remove init temporary scaffold: {error}"))?;
    sync_parent(parent, "init.cleanup.temp_parent_fsync")
}

fn remove_owned_init(target: &Path, marker: &[u8], parent: &Path) -> Result<(), String> {
    let metadata = match fs::symlink_metadata(target) {
        Ok(metadata) => metadata,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(()),
        Err(error) => return Err(format!("inspect failed init target: {error}")),
    };
    if metadata.file_type().is_symlink()
        || !metadata.is_dir()
        || !matching_init_marker(target, marker)
    {
        return Err("refusing to remove init target without matching ownership marker".to_owned());
    }
    init_fault("init.cleanup.target_remove")?;
    fs::remove_dir_all(target).map_err(|error| format!("remove failed init target: {error}"))?;
    sync_parent(parent, "init.cleanup.target_parent_fsync")
}

fn uv_environment(uv: &Path) -> Result<BTreeMap<String, OsString>, String> {
    let home = std::env::var_os("HOME").ok_or("HOME is required for uv")?;
    let path = std::env::join_paths([
        uv.parent().unwrap_or_else(|| Path::new("/usr/bin")),
        Path::new("/usr/bin"),
        Path::new("/bin"),
    ])
    .map_err(|error| format!("construct sanitized PATH: {error}"))?;
    let mut environment = BTreeMap::from([
        ("HOME".to_owned(), home),
        ("PATH".to_owned(), path),
        ("TMPDIR".to_owned(), std::env::temp_dir().into_os_string()),
    ]);
    for name in [
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
        "REQUESTS_CA_BUNDLE",
        "CURL_CA_BUNDLE",
    ] {
        if let Some(value) = std::env::var_os(name) {
            environment.insert(name.to_owned(), value);
        }
    }
    Ok(environment)
}

fn initialize_python(
    uv: &Path,
    target: &Path,
    base_environment: &BTreeMap<String, OsString>,
    no_sync: bool,
) -> Result<PathBuf, String> {
    let run_uv = |arguments: &[&str], environment: &BTreeMap<String, OsString>| {
        run_clean(uv, arguments, target, environment, Duration::from_secs(900)).and_then(|output| {
            if output.status == Some(0) {
                Ok(output)
            } else {
                Err(format!(
                    "uv {} failed: {}",
                    arguments.join(" "),
                    String::from_utf8_lossy(&output.stderr).trim()
                ))
            }
        })
    };
    let root_output = run_uv(&["--no-config", "python", "dir"], base_environment)?;
    let managed_root = fs::canonicalize(String::from_utf8_lossy(&root_output.stdout).trim())
        .map_err(|error| format!("resolve uv managed Python root: {error}"))?;
    run_uv(
        &["--no-config", "python", "install", "--upgrade", "3.14"],
        base_environment,
    )?;
    let interpreter_output = run_uv(
        &[
            "--no-config",
            "python",
            "find",
            "--managed-python",
            "--system",
            "3.14",
        ],
        base_environment,
    )?;
    let interpreter = fs::canonicalize(String::from_utf8_lossy(&interpreter_output.stdout).trim())
        .map_err(|error| format!("resolve uv managed interpreter: {error}"))?;
    if !interpreter.starts_with(&managed_root) {
        return Err("uv selected an interpreter outside its managed Python root".to_owned());
    }
    probe_python(&interpreter, target, base_environment)?;
    let mut environment = base_environment.clone();
    environment.insert("UV_PYTHON".to_owned(), interpreter.clone().into_os_string());
    environment.insert(
        "UV_PROJECT_ENVIRONMENT".to_owned(),
        target.join(".venv").into_os_string(),
    );
    run_uv(
        &[
            "--no-config",
            "lock",
            "--directory",
            target
                .join("python")
                .to_str()
                .ok_or("init path is not UTF-8")?,
        ],
        &environment,
    )?;
    let lockfile = target.join("python/uv.lock");
    let lock_metadata = fs::symlink_metadata(&lockfile)
        .map_err(|error| format!("uv did not create {}: {error}", lockfile.display()))?;
    if lock_metadata.file_type().is_symlink() || !lock_metadata.is_file() {
        return Err("uv lock output is not a regular file".to_owned());
    }
    if !no_sync {
        run_uv(
            &[
                "--no-config",
                "sync",
                "--directory",
                target
                    .join("python")
                    .to_str()
                    .ok_or("init path is not UTF-8")?,
                "--frozen",
                "--managed-python",
            ],
            &environment,
        )?;
        probe_python(&target.join(".venv/bin/python"), target, &environment)?;
        let checker = run_clean(
            &target.join(".venv/bin/basedpyright"),
            &["--version"],
            target,
            &environment,
            Duration::from_secs(30),
        )?;
        if checker.status != Some(0)
            || !supports_basedpyright_version(&String::from_utf8_lossy(&checker.stdout))
        {
            return Err("root BasedPyright probe requires >=1.39.9".to_owned());
        }
    }
    Ok(interpreter)
}

fn probe_python(
    interpreter: &Path,
    cwd: &Path,
    environment: &BTreeMap<String, OsString>,
) -> Result<(), String> {
    let output = run_clean(
        interpreter,
        &[
            "-I",
            "-c",
            "import platform,sys; print(sys.implementation.name, platform.python_version())",
        ],
        cwd,
        environment,
        Duration::from_secs(30),
    )?;
    let identity = String::from_utf8_lossy(&output.stdout);
    let valid = identity
        .trim()
        .split_once(' ')
        .is_some_and(|(implementation, version)| {
            implementation == "cpython" && supports_python_version(version)
        });
    if output.status == Some(0) && valid {
        Ok(())
    } else {
        Err(format!(
            "Python probe requires CPython >=3.14.6,<3.15: {}",
            String::from_utf8_lossy(&output.stderr).trim()
        ))
    }
}

struct BoundedOutput {
    status: Option<i32>,
    stdout: Vec<u8>,
    stderr: Vec<u8>,
}

fn run_clean(
    program: &Path,
    arguments: &[&str],
    cwd: &Path,
    environment: &BTreeMap<String, OsString>,
    timeout: Duration,
) -> Result<BoundedOutput, String> {
    let mut command = ProcessCommand::new(program);
    command
        .args(arguments)
        .current_dir(cwd)
        .env_clear()
        .envs(environment)
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    unsafe {
        command.pre_exec(|| {
            if libc::setpgid(0, 0) == 0 {
                Ok(())
            } else {
                Err(std::io::Error::last_os_error())
            }
        });
    }
    let mut child = command
        .spawn()
        .map_err(|error| format!("start {}: {error}", program.display()))?;
    let stdout = child.stdout.take().expect("piped stdout");
    let stderr = child.stderr.take().expect("piped stderr");
    let drain = |mut stream: Box<dyn Read + Send>| {
        let mut bytes = Vec::new();
        stream
            .by_ref()
            .take(16 * 1024 * 1024 + 1)
            .read_to_end(&mut bytes)
            .map(|_| bytes)
    };
    let stdout = thread::spawn(move || drain(Box::new(stdout)));
    let stderr = thread::spawn(move || drain(Box::new(stderr)));
    let started = Instant::now();
    let status = loop {
        match child.try_wait() {
            Ok(Some(status)) => break status.code(),
            Ok(None) if started.elapsed() < timeout => thread::sleep(Duration::from_millis(20)),
            Ok(None) => {
                unsafe {
                    libc::kill(-(child.id() as i32), libc::SIGKILL);
                }
                let _ = child.wait();
                return Err(format!("{} timed out", program.display()));
            }
            Err(error) => return Err(format!("wait for {}: {error}", program.display())),
        }
    };
    let stdout = stdout
        .join()
        .map_err(|_| "stdout drain panicked".to_owned())?
        .map_err(|error| format!("read stdout: {error}"))?;
    let stderr = stderr
        .join()
        .map_err(|_| "stderr drain panicked".to_owned())?
        .map_err(|error| format!("read stderr: {error}"))?;
    if stdout.len() > 16 * 1024 * 1024 || stderr.len() > 16 * 1024 * 1024 {
        return Err(format!("{} output exceeded 16 MiB", program.display()));
    }
    Ok(BoundedOutput {
        status,
        stdout,
        stderr,
    })
}

fn print_sync_note(
    format: &OutputFormat,
    uv: &Path,
    target: &Path,
    interpreter: &Path,
    base_environment: &BTreeMap<String, OsString>,
) {
    let mut environment = base_environment.clone();
    environment.insert("UV_PYTHON".to_owned(), interpreter.into());
    environment.insert(
        "UV_PROJECT_ENVIRONMENT".to_owned(),
        target.join(".venv").into_os_string(),
    );
    let mut words = vec!["/usr/bin/env".to_owned(), "-i".to_owned()];
    words.extend(
        environment
            .iter()
            .map(|(name, value)| shell_word(&format!("{name}={}", value.to_string_lossy()))),
    );
    words.extend([
        shell_word(&uv.display().to_string()),
        "--no-config".to_owned(),
        "sync".to_owned(),
        "--directory".to_owned(),
        shell_word(&target.join("python").display().to_string()),
        "--frozen".to_owned(),
        "--managed-python".to_owned(),
    ]);
    let command = words.join(" ");
    match format {
        OutputFormat::Human => println!("{command}"),
        OutputFormat::Json => println!(
            "{}",
            serde_json::json!({
                "diagnostics": [{
                    "code": crate::diagnostics::code::NAME,
                    "help": [command],
                    "message": "run the frozen Python environment sync",
                    "severity": "note",
                    "span": null,
                }],
                "schema_version": 1,
            })
        ),
    }
}

fn shell_word(value: &str) -> String {
    if !value.is_empty()
        && value
            .bytes()
            .all(|byte| byte.is_ascii_alphanumeric() || b"_@%+=:,./-".contains(&byte))
    {
        value.to_owned()
    } else {
        format!("'{}'", value.replace('\'', "'\"'\"'"))
    }
}

fn valid_project_name(value: &str) -> bool {
    let bytes = value.as_bytes();
    !bytes.is_empty()
        && bytes.len() <= 64
        && bytes[0].is_ascii_lowercase()
        && bytes.last().is_some_and(u8::is_ascii_alphanumeric)
        && !value.contains("--")
        && bytes
            .iter()
            .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit() || *byte == b'-')
}

fn format_project(project_argument: Option<PathBuf>, check: bool) -> i32 {
    let Ok(root) = project_root(project_argument) else {
        return 2;
    };
    let session = match ProjectSession::acquire(&root) {
        Ok(session) => session,
        Err(error) => {
            eprintln!("error: {error}");
            return 6;
        }
    };
    let (config, paths) = match load_config_with_paths(session.root()) {
        Ok(config) => config,
        Err(error) => {
            eprintln!("error: {error}");
            return 2;
        }
    };
    let sources = match discover_sources_from_paths(&paths) {
        Ok(sources) => sources,
        Err(error) => {
            eprintln!("error: {error}");
            return 2;
        }
    };
    let input_hashes = match collect_input_hashes(&config, &paths, &sources) {
        Ok(inputs) => inputs,
        Err(error) => {
            eprintln!("error: {error}");
            return 2;
        }
    };
    let input_snapshot = match capture_expected_inputs(&paths, &input_hashes, []) {
        Ok(snapshot) => snapshot,
        Err(error) => {
            eprintln!("error: {error}");
            return 6;
        }
    };
    let parsed = match parse_project(sources) {
        Ok(parsed) => parsed,
        Err(diagnostics) => {
            print_project_diagnostics(&diagnostics);
            return 3;
        }
    };
    let mut changes = ChangeSet::default();
    let mut paths_to_write = Vec::new();
    let mut differs = false;
    let mut formatted_inputs = BTreeMap::new();
    for source in parsed.sources {
        let bytes = match crate::formatter::format(&source.cst, &source.syntax) {
            Ok(bytes) => bytes,
            Err(diagnostic) => {
                print_project_diagnostics(&[ProjectDiagnostic {
                    path: source.path,
                    diagnostic,
                }]);
                return 3;
            }
        };
        let relative = paths
            .source_dir
            .strip_prefix(&paths.root)
            .expect("project source is rooted")
            .join(&source.path);
        let current = match fs::read(paths.root.join(&relative)) {
            Ok(bytes) => bytes,
            Err(error) => {
                eprintln!("error: read source {}: {error}", relative.display());
                return 2;
            }
        };
        if current != bytes {
            differs = true;
            if !check {
                formatted_inputs.insert(
                    relative.to_string_lossy().replace('\\', "/"),
                    format!("sha256:{}", sha256_hex(&bytes)),
                );
                paths_to_write.push(relative.clone());
                changes.operations.push(Operation::Write {
                    path: relative,
                    bytes,
                });
            }
        }
    }
    if check {
        return if differs { 8 } else { 0 };
    }
    if differs {
        if let Ok(artifact_root) = artifact_root_for_paths(&paths) {
            let generation = artifact_root.join("generation.json");
            if generation.exists() {
                let mut record = match fs::read(&generation)
                    .map_err(|error| error.to_string())
                    .and_then(|bytes| GenerationRecord::parse(&bytes))
                {
                    Ok(record) => record,
                    Err(error) => {
                        eprintln!("error: invalidate generation record: {error}");
                        return 4;
                    }
                };
                let Some(inputs) = record.current.inputs.as_object_mut() else {
                    eprintln!("error: generation inputs are not an object");
                    return 4;
                };
                for (path, hash) in formatted_inputs {
                    inputs.insert(path, serde_json::Value::String(hash));
                }
                record.current.verified = false;
                record.current.verification = serde_json::Value::Null;
                if let Err(error) = record.current.compute_generation_id() {
                    eprintln!("error: invalidate generation identity: {error}");
                    return 4;
                }
                let bytes = match record.canonical_bytes() {
                    Ok(bytes) => bytes,
                    Err(error) => {
                        eprintln!("error: serialize invalidated generation record: {error}");
                        return 4;
                    }
                };
                let relative = generation
                    .strip_prefix(&paths.root)
                    .expect("generation record is project-relative")
                    .to_path_buf();
                paths_to_write.push(relative.clone());
                changes.operations.push(Operation::Write {
                    path: relative,
                    bytes,
                });
                changes.generation_record_last = true;
            }
        }
    }
    let output_snapshot = match InputSnapshot::capture(&paths.root, paths_to_write) {
        Ok(snapshot) => snapshot,
        Err(error) => {
            eprintln!("error: {error}");
            return 6;
        }
    };
    let mut snapshot = input_snapshot;
    snapshot.merge_missing(output_snapshot);
    match session.apply(&snapshot, &changes) {
        Ok(()) => 0,
        Err(error) => {
            eprintln!("error: {error}");
            6
        }
    }
}

fn print_project_diagnostics(diagnostics: &[ProjectDiagnostic]) {
    for diagnostic in diagnostics {
        eprintln!(
            "error: {}:{}-{}: {}",
            diagnostic.path.display(),
            diagnostic.diagnostic.span.start,
            diagnostic.diagnostic.span.end,
            diagnostic.diagnostic.message
        );
    }
}

fn print_emit_diagnostics(paths: &ProjectPaths, diagnostics: &[EmitDiagnostic]) {
    for diagnostic in diagnostics {
        eprintln!(
            "error: {}: {}",
            display_path(&paths.root, &diagnostic.path),
            diagnostic.message
        );
    }
}

fn display_path(root: &Path, path: &Path) -> String {
    path.strip_prefix(root)
        .unwrap_or(path)
        .display()
        .to_string()
}

fn artifact_root_for_paths(project: &ProjectPaths) -> Result<PathBuf, String> {
    artifact_root_at(&project.root, &project.generated_dir)
}

fn artifact_root_at(root_dir: &Path, generated_dir: &Path) -> Result<PathBuf, String> {
    if generated_dir.file_name().and_then(|name| name.to_str()) != Some("python") {
        return Err("target.python.generated must end in `python`".to_owned());
    }
    let Some(root) = generated_dir.parent() else {
        return Err("target.python.generated has no artifact root".to_owned());
    };
    if root == root_dir {
        return Err("target.python.generated must be beneath an artifact root".to_owned());
    }
    Ok(root.to_path_buf())
}

fn generated_path(paths: &ProjectPaths) -> String {
    display_path(&paths.root, &paths.generated_dir)
}

fn publish(plan: &PlannedProject) -> Result<(), String> {
    publish_with_sources(plan, &[])
}

fn publish_with_sources(
    plan: &PlannedProject,
    sources: &[(PathBuf, Vec<u8>)],
) -> Result<(), String> {
    let artifact_root = artifact_root_for_paths(&plan.paths)?;
    if let Ok(metadata) = fs::symlink_metadata(&artifact_root) {
        if metadata.file_type().is_symlink() || !metadata.is_dir() {
            return Err(format!(
                "artifact root is not a regular directory: {}",
                artifact_root.display()
            ));
        }
    }
    let session = &plan.session;
    let relative_root = artifact_root
        .strip_prefix(&plan.paths.root)
        .map_err(|_| "artifact root escaped project root".to_owned())?;
    let actual = match fs::symlink_metadata(&artifact_root) {
        Ok(_) => collect_tree(&artifact_root)?,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => BTreeMap::new(),
        Err(error) => {
            return Err(format!(
                "failed to inspect artifact root {}: {error}",
                artifact_root.display()
            ));
        }
    };
    let mut paths = BTreeMap::new();
    for path in actual.keys().chain(plan.emission.files.keys()) {
        let relative = relative_root.join(path);
        if !safe_relative_path(&relative) {
            return Err(format!(
                "emitter produced an unsafe output path: {}",
                relative.display()
            ));
        }
        paths.insert(relative, ());
    }
    for (path, _) in sources {
        if !safe_relative_path(path) {
            return Err(format!(
                "generated implementation has an unsafe path: {}",
                path.display()
            ));
        }
        paths.insert(path.clone(), ());
    }
    let output_snapshot = InputSnapshot::capture(&plan.paths.root, paths.into_keys())
        .map_err(|error| error.to_string())?;
    let mut snapshot = plan.input_snapshot.clone();
    snapshot.merge_missing(output_snapshot);
    let mut changes = ChangeSet::default();
    for (path, bytes) in &plan.emission.files {
        if actual.get(path) != Some(bytes) {
            changes.operations.push(Operation::Write {
                path: relative_root.join(path),
                bytes: bytes.clone(),
            });
        }
    }
    for (path, bytes) in sources {
        let current = fs::read(plan.paths.root.join(path)).ok();
        if current.as_deref() != Some(bytes) {
            changes.operations.push(Operation::Write {
                path: path.clone(),
                bytes: bytes.clone(),
            });
        }
    }
    for path in actual.keys() {
        if !plan.emission.files.contains_key(path) {
            changes.operations.push(Operation::Remove {
                path: relative_root.join(path),
            });
        }
    }
    changes.operations.sort_by_key(|operation| match operation {
        Operation::Write { path, .. } | Operation::Remove { path } => path
            .file_name()
            .is_some_and(|name| name == "generation.json"),
    });
    changes.generation_record_last = true;
    session
        .apply(&snapshot, &changes)
        .map_err(|error| error.to_string())
}

fn safe_relative_path(path: &Path) -> bool {
    !path.as_os_str().is_empty()
        && path.is_relative()
        && path
            .components()
            .all(|component| matches!(component, Component::Normal(_)))
}
fn verify(plan: &PlannedProject) -> Result<(), Vec<String>> {
    let artifact_root = artifact_root_for_paths(&plan.paths).map_err(|message| vec![message])?;
    let session = &plan.session;
    let actual = collect_tree(&artifact_root).map_err(|message| vec![message])?;
    let mut mismatches = Vec::new();
    for (path, expected) in &plan.emission.files {
        if path == Path::new("generation.json") {
            continue;
        }
        match actual.get(path) {
            Some(actual) if actual == expected => {}
            Some(_) => mismatches.push(format!("managed artifact differs: {}", path.display())),
            None => mismatches.push(format!("missing managed artifact: {}", path.display())),
        }
    }
    for path in actual.keys() {
        if path != Path::new("generation.json") && !plan.emission.files.contains_key(path) {
            mismatches.push(format!("unexpected managed artifact: {}", path.display()));
        }
    }
    let expected_record = plan
        .emission
        .files
        .get(Path::new("generation.json"))
        .ok_or_else(|| vec!["planned generation record is missing".to_owned()])
        .and_then(|bytes| {
            GenerationRecord::parse(bytes)
                .map_err(|error| vec![format!("invalid planned generation record: {error}")])
        })?;
    let actual_record = actual
        .get(Path::new("generation.json"))
        .ok_or_else(|| vec!["missing managed artifact: generation.json".to_owned()])
        .and_then(|bytes| {
            GenerationRecord::parse(bytes)
                .map_err(|error| vec![format!("invalid managed generation record: {error}")])
        })?;
    if comparable_snapshot(&actual_record.current) != comparable_snapshot(&expected_record.current)
    {
        mismatches
            .push("generation record does not describe the current compiler inputs".to_owned());
    }
    if !expected_record.current.unresolved.is_empty() {
        mismatches.push(format!(
            "unresolved implementations: {}",
            expected_record
                .current
                .unresolved
                .iter()
                .map(|record| record.cott_symbol.as_str())
                .collect::<Vec<_>>()
                .join(", ")
        ));
    }
    if !mismatches.is_empty() {
        return Err(mismatches);
    }
    let implementation_comparison = compare_implementation_identities(
        actual_record.last_verified.as_ref(),
        &expected_record.current,
    );
    let evidence = verify_python(&plan.config, &plan.paths, &artifact_root, &plan.ir, None)
        .map_err(|message| vec![message])?;
    let mut verification = evidence.report;
    verification
        .as_object_mut()
        .expect("verification evidence is an object")
        .insert(
            "implementation_comparison".to_owned(),
            serde_json::to_value(implementation_comparison)
                .map_err(|message| vec![message.to_string()])?,
        );
    let coverage = semantic_coverage(&verification, &plan.config.verification.coverage)
        .map_err(|message| vec![message])?;
    let policy = coverage.policy.clone();
    let mut record = expected_record;
    let intent = record.current.tools.get(intent::TOOL_KEY).cloned();
    record.current.tools = evidence.tools;
    if let Some(intent) = intent {
        record
            .current
            .tools
            .as_object_mut()
            .ok_or_else(|| vec!["verification tools are not an object".to_owned()])?
            .insert(intent::TOOL_KEY.to_owned(), intent);
    }
    record.current.dependencies = evidence.dependencies;
    record.current.verified = true;
    record.current.verification = verification;
    record.current.semantic_coverage = coverage;
    record
        .current
        .compute_generation_id()
        .map_err(|message| vec![message])?;
    record.last_verified = Some(record.current.clone());
    let bytes = record.canonical_bytes().map_err(|message| vec![message])?;
    let relative = artifact_root
        .strip_prefix(&plan.paths.root)
        .map_err(|_| vec!["artifact root escaped project root".to_owned()])?
        .join("generation.json");
    let output_snapshot = InputSnapshot::capture(&plan.paths.root, [relative.clone()])
        .map_err(|error| vec![error.to_string()])?;
    let mut snapshot = plan.input_snapshot.clone();
    snapshot.merge_missing(output_snapshot);
    let mut changes = ChangeSet::default();
    changes.operations.push(Operation::Write {
        path: relative,
        bytes,
    });
    changes.generation_record_last = true;
    session
        .apply(&snapshot, &changes)
        .map_err(|error| vec![error.to_string()])?;
    if !policy.passed {
        return Err(policy
            .violations
            .into_iter()
            .map(|violation| {
                format!(
                    "{COVERAGE_POLICY_PREFIX}{}:{}:{}-{}: {}",
                    violation.symbol,
                    violation.clause_id,
                    violation.span.start_byte,
                    violation.span.end_byte,
                    violation.reason,
                )
            })
            .collect());
    }
    Ok(())
}

const COVERAGE_POLICY_PREFIX: &str = "semantic coverage policy failed: ";

fn provenance_span(value: &serde_json::Value) -> Result<ProvenanceSpan, String> {
    let field = |name| {
        value
            .get(name)
            .and_then(serde_json::Value::as_u64)
            .ok_or_else(|| format!("coverage evidence has invalid span field `{name}`"))
    };
    Ok(ProvenanceSpan {
        start_byte: field("start_byte")?,
        end_byte: field("end_byte")?,
        start_line: field("start_line")?,
        start_column: field("start_column")?,
        end_line: field("end_line")?,
        end_column: field("end_column")?,
    })
}

fn coverage_status(evidence: &[serde_json::Value]) -> CoverageStatus {
    let observed = evidence.iter().any(|entry| {
        matches!(
            entry.get("status").and_then(serde_json::Value::as_str),
            Some("proved")
        ) || matches!(
            entry.get("grade").and_then(serde_json::Value::as_str),
            Some("runtime check" | "test observation")
        )
    });
    if observed {
        return CoverageStatus::Observed;
    }
    if evidence.is_empty()
        || evidence.iter().any(|entry| {
            matches!(
                entry.get("status").and_then(serde_json::Value::as_str),
                Some("unknown")
            ) || entry
                .get("reason")
                .and_then(serde_json::Value::as_str)
                .is_some_and(|reason| {
                    let reason = reason.to_ascii_lowercase();
                    reason.contains("unsupported") || reason.contains("limit")
                })
        })
    {
        return CoverageStatus::Unknown;
    }
    if evidence.iter().any(|entry| {
        entry.get("grade").and_then(serde_json::Value::as_str) == Some("trust declaration")
    }) {
        return CoverageStatus::TrustDeclaration;
    }
    CoverageStatus::Unobserved
}

fn coverage_order_values(symbol: &str, clause_id: &str) -> (String, u8, u32, String) {
    let (kind, id) = clause_id
        .split_once(':')
        .expect("coverage evidence clause IDs originate in canonical IR");
    let order = match kind {
        "requires" => 0,
        "ensures" => 1,
        "error" => 2,
        "modifies" => 3,
        "invariant" => 4,
        _ => 5,
    };
    (
        symbol.to_owned(),
        order,
        id.parse().unwrap_or_default(),
        if kind == "modifies" {
            id.to_owned()
        } else {
            String::new()
        },
    )
}

fn coverage_order(clause: &ClauseCoverage) -> (String, u8, u32, String) {
    coverage_order_values(&clause.symbol, &clause.clause_id)
}

pub(crate) fn semantic_coverage(
    report: &serde_json::Value,
    policy: &crate::manifest::CoveragePolicy,
) -> Result<SemanticCoverage, String> {
    let mut clauses = BTreeMap::<(String, String), (ProvenanceSpan, Vec<serde_json::Value>)>::new();
    let mut insert =
        |entry: &serde_json::Value, payloads: Vec<serde_json::Value>| -> Result<(), String> {
            let symbol = entry
                .get("symbol")
                .and_then(serde_json::Value::as_str)
                .ok_or("coverage evidence has no symbol")?;
            let clause_id = entry
                .get("clause_id")
                .and_then(serde_json::Value::as_str)
                .ok_or("coverage evidence has no clause_id")?;
            let span = provenance_span(entry.get("span").ok_or("coverage evidence has no span")?)?;
            let key = (symbol.to_owned(), clause_id.to_owned());
            match clauses.get_mut(&key) {
                Some((existing, evidence)) => {
                    if *existing != span {
                        return Err(format!(
                            "coverage evidence disagrees on span for `{symbol}:{clause_id}`"
                        ));
                    }
                    evidence.extend(payloads);
                }
                None => {
                    clauses.insert(key, (span, payloads));
                }
            }
            Ok(())
        };

    for entry in report
        .pointer("/contract_tests/contracts")
        .and_then(serde_json::Value::as_array)
        .into_iter()
        .flatten()
    {
        let payloads = entry
            .get("evidence")
            .and_then(serde_json::Value::as_array)
            .cloned()
            .unwrap_or_default();
        insert(entry, payloads)?;
    }
    for entry in report
        .pointer("/contract_proofs/contracts")
        .and_then(serde_json::Value::as_array)
        .into_iter()
        .flatten()
        .filter(|entry| entry.get("clause_id").is_some())
    {
        insert(entry, vec![entry.clone()])?;
    }

    let mut clauses = clauses
        .into_iter()
        .map(|((symbol, clause_id), (span, evidence))| ClauseCoverage {
            symbol,
            clause_id,
            span,
            status: coverage_status(&evidence),
            evidence,
        })
        .collect::<Vec<_>>();
    clauses.sort_by(|left, right| coverage_order(left).cmp(&coverage_order(right)));
    let mut summary = CoverageSummary::default();
    for clause in &clauses {
        match clause.status {
            CoverageStatus::Observed => summary.observed += 1,
            CoverageStatus::Unobserved => summary.unobserved += 1,
            CoverageStatus::TrustDeclaration => summary.trust_declaration += 1,
            CoverageStatus::Unknown => summary.unknown += 1,
        }
    }

    let by_key = clauses
        .iter()
        .map(|clause| ((clause.symbol.as_str(), clause.clause_id.as_str()), clause))
        .collect::<BTreeMap<_, _>>();
    let mut selected = BTreeSet::new();
    for (rule_index, rule) in policy.rules.iter().enumerate() {
        let known = clauses.iter().any(|clause| clause.symbol == rule.symbol);
        if !known {
            return Err(format!(
                "coverage policy rule {rule_index} selects unknown symbol `{}`",
                rule.symbol
            ));
        }
        for clause_id in &rule.clauses {
            if !by_key.contains_key(&(rule.symbol.as_str(), clause_id.as_str())) {
                return Err(format!(
                    "coverage policy rule {rule_index} selects unknown clause `{}:{clause_id}`",
                    rule.symbol
                ));
            }
            selected.insert((rule.symbol.as_str(), clause_id.as_str()));
        }
    }
    let mut violations = Vec::new();
    for (rule_index, rule) in policy.rules.iter().enumerate() {
        for clause_id in &rule.clauses {
            let clause = by_key[&(rule.symbol.as_str(), clause_id.as_str())];
            let allowed = match clause.status {
                CoverageStatus::Observed => true,
                CoverageStatus::Unobserved => rule.allow_unobserved,
                CoverageStatus::TrustDeclaration => rule.allow_trust_declaration,
                CoverageStatus::Unknown => rule.allow_unknown,
            };
            if !allowed {
                violations.push(CoverageViolation {
                    symbol: clause.symbol.clone(),
                    clause_id: clause.clause_id.clone(),
                    span: clause.span.clone(),
                    status: clause.status.clone(),
                    reason: format!(
                        "coverage policy rule {rule_index} does not allow `{}`",
                        match clause.status {
                            CoverageStatus::Observed => "observed",
                            CoverageStatus::Unobserved => "unobserved",
                            CoverageStatus::TrustDeclaration => "trust_declaration",
                            CoverageStatus::Unknown => "unknown",
                        }
                    ),
                });
            }
        }
    }
    violations.sort_by(|left, right| {
        coverage_order_values(&left.symbol, &left.clause_id)
            .cmp(&coverage_order_values(&right.symbol, &right.clause_id))
    });
    violations
        .dedup_by(|left, right| left.symbol == right.symbol && left.clause_id == right.clause_id);
    Ok(SemanticCoverage {
        clauses,
        summary,
        policy: CoveragePolicyResult {
            selected: selected.len() as u64,
            passed: violations.is_empty(),
            violations,
        },
    })
}
fn comparable_snapshot(snapshot: &crate::provenance::GenerationSnapshot) -> serde_json::Value {
    let mut value = serde_json::to_value(snapshot).expect("generation snapshot serializes");
    let object = value
        .as_object_mut()
        .expect("generation snapshot is an object");
    for field in [
        "agent_runs",
        "generation_id",
        "semantic_coverage",
        "tools",
        "verification",
        "verified",
    ] {
        object.remove(field);
    }
    value
}
fn collect_tree(root: &Path) -> Result<BTreeMap<PathBuf, Vec<u8>>, String> {
    let metadata = fs::symlink_metadata(root).map_err(|error| {
        format!(
            "failed to inspect artifact root {}: {error}",
            root.display()
        )
    })?;
    if metadata.file_type().is_symlink() || !metadata.is_dir() {
        return Err(format!(
            "artifact root is not a regular directory: {}",
            root.display()
        ));
    }
    let mut files = BTreeMap::new();
    collect_tree_at(root, root, &mut files)?;
    Ok(files)
}

fn collect_tree_at(
    root: &Path,
    directory: &Path,
    files: &mut BTreeMap<PathBuf, Vec<u8>>,
) -> Result<(), String> {
    let entries = fs::read_dir(directory).map_err(|error| {
        format!(
            "failed to read artifact directory {}: {error}",
            directory.display()
        )
    })?;
    let mut entries: Vec<_> = entries.collect::<Result<_, _>>().map_err(|error| {
        format!(
            "failed to read artifact directory {}: {error}",
            directory.display()
        )
    })?;
    entries.sort_by_key(|dir_entry| dir_entry.file_name());
    for dir_entry in entries {
        let path = dir_entry.path();
        let metadata = fs::symlink_metadata(&path)
            .map_err(|error| format!("failed to inspect artifact {}: {error}", path.display()))?;
        if metadata.file_type().is_symlink() {
            return Err(format!(
                "artifact must not be a symlink: {}",
                path.display()
            ));
        }
        if metadata.is_dir() {
            if dir_entry.file_name() == "__pycache__" {
                validate_python_bytecode_cache(&path)?;
            } else {
                collect_tree_at(root, &path, files)?;
            }
        } else if metadata.is_file() {
            let relative = path
                .strip_prefix(root)
                .map_err(|_| format!("artifact escaped output root: {}", path.display()))?
                .to_path_buf();
            let bytes = fs::read(&path)
                .map_err(|error| format!("failed to read artifact {}: {error}", path.display()))?;
            files.insert(relative, bytes);
        } else {
            return Err(format!(
                "artifact is not a regular file: {}",
                path.display()
            ));
        }
    }
    Ok(())
}

fn validate_python_bytecode_cache(directory: &Path) -> Result<(), String> {
    let entries = fs::read_dir(directory).map_err(|error| {
        format!(
            "failed to read Python bytecode cache {}: {error}",
            directory.display()
        )
    })?;
    for cache_entry in entries {
        let cache_entry = cache_entry.map_err(|error| {
            format!(
                "failed to read Python bytecode cache {}: {error}",
                directory.display()
            )
        })?;
        let path = cache_entry.path();
        let metadata = fs::symlink_metadata(&path)
            .map_err(|error| format!("failed to inspect artifact {}: {error}", path.display()))?;
        if metadata.file_type().is_symlink()
            || !metadata.is_file()
            || path.extension().and_then(|extension| extension.to_str()) != Some("pyc")
        {
            return Err(format!(
                "Python bytecode cache contains an unexpected artifact: {}",
                path.display()
            ));
        }
    }
    Ok(())
}

#[cfg(test)]
#[test]
fn scoped_wave_limits_concurrency_and_preserves_input_order() {
    use std::sync::atomic::{AtomicUsize, Ordering};
    use std::sync::{Arc, Barrier};

    struct InFlight(Arc<AtomicUsize>);

    impl Drop for InFlight {
        fn drop(&mut self) {
            self.0.fetch_sub(1, Ordering::SeqCst);
        }
    }

    let items = [0, 1, 2, 3, 4];
    let barrier = Arc::new(Barrier::new(items.len()));
    let in_flight = Arc::new(AtomicUsize::new(0));
    let maximum = Arc::new(AtomicUsize::new(0));
    let completed = Arc::new(AtomicUsize::new(0));
    let results = run_scoped_wave(
        &items,
        |item| {
            barrier.wait();
            let active = in_flight.fetch_add(1, Ordering::SeqCst) + 1;
            maximum.fetch_max(active, Ordering::SeqCst);
            let _guard = InFlight(Arc::clone(&in_flight));
            thread::sleep(Duration::from_millis((items.len() - *item) as u64 * 20));
            Ok::<_, ()>((*item, completed.fetch_add(1, Ordering::SeqCst)))
        },
        |_| (),
    );

    let results = results
        .into_iter()
        .collect::<Result<Vec<_>, _>>()
        .expect("wave workers should succeed");
    assert_eq!(
        results.iter().map(|(item, _)| *item).collect::<Vec<_>>(),
        items
    );
    assert_eq!(maximum.load(Ordering::SeqCst), items.len());
    assert_eq!(in_flight.load(Ordering::SeqCst), 0);
    assert!(results[0].1 > results[4].1);
}

#[cfg(test)]
#[test]
fn pending_capture_rejects_late_source_edits() {
    use std::sync::atomic::{AtomicU64, Ordering};

    struct TempRoot(PathBuf);
    impl Drop for TempRoot {
        fn drop(&mut self) {
            let _ = fs::remove_dir_all(&self.0);
        }
    }

    static NEXT: AtomicU64 = AtomicU64::new(0);
    let root = TempRoot(std::env::temp_dir().join(format!(
        "cott-pending-capture-{}-{}",
        std::process::id(),
        NEXT.fetch_add(1, Ordering::Relaxed)
    )));
    fs::create_dir_all(root.0.join("python")).expect("temp project");
    let stable = PathBuf::from("cott.toml");
    let authenticated = PathBuf::from("python/selected.py");
    let unselected = PathBuf::from("python/unselected.py");
    let missing = PathBuf::from("python/missing.py");
    let stable_bytes = b"[project]\n";
    let source_bytes = b"def run() -> int:\n    return 1\n";
    fs::write(root.0.join(&stable), stable_bytes).expect("stable input");
    fs::write(root.0.join(&authenticated), source_bytes).expect("authenticated pending");
    fs::write(root.0.join(&unselected), source_bytes).expect("unselected pending");
    let hash = |bytes: &[u8]| format!("sha256:{}", sha256_hex(bytes));
    let hashes = BTreeMap::from([("cott.toml".to_owned(), hash(stable_bytes))]);
    let pending = BTreeMap::from([
        (authenticated.clone(), Some(hash(source_bytes))),
        (unselected.clone(), Some(hash(source_bytes))),
        (missing.clone(), None),
    ]);

    let snapshot = capture_resolution_inputs(&root.0, &hashes, &pending)
        .expect("unchanged pending sources should capture");
    assert!(
        snapshot
            .files
            .get(&authenticated)
            .is_some_and(Option::is_some),
        "authenticated pending source must stay in the snapshot"
    );
    assert!(
        snapshot.files.get(&unselected).is_some_and(Option::is_some),
        "unselected pending source must stay in the snapshot"
    );
    assert!(
        snapshot.files.get(&missing).is_some_and(Option::is_none),
        "expected-missing pending source must stay absent"
    );
    assert!(
        snapshot.files.get(&stable).is_some_and(Option::is_some),
        "resolved expected inputs must stay in the snapshot"
    );

    fs::write(root.0.join(&authenticated), b"changed\n").expect("tamper selected");
    let error = capture_resolution_inputs(&root.0, &hashes, &pending)
        .expect_err("changed authenticated pending source is drift");
    assert!(
        matches!(&error, TransactionError::SnapshotDrift(path) if path == &authenticated),
        "{error}"
    );
    fs::write(root.0.join(&authenticated), source_bytes).expect("restore selected");

    fs::write(root.0.join(&unselected), b"changed\n").expect("tamper unselected");
    let error = capture_resolution_inputs(&root.0, &hashes, &pending)
        .expect_err("changed unselected pending source is drift");
    assert!(
        matches!(&error, TransactionError::SnapshotDrift(path) if path == &unselected),
        "{error}"
    );
    fs::write(root.0.join(&unselected), source_bytes).expect("restore unselected");

    fs::write(root.0.join(&missing), source_bytes).expect("create missing");
    let error = capture_resolution_inputs(&root.0, &hashes, &pending)
        .expect_err("created expected-missing pending source is drift");
    assert!(
        matches!(&error, TransactionError::SnapshotDrift(path) if path == &missing),
        "{error}"
    );
}

#[cfg(test)]
mod init_publication_tests {
    use super::*;
    use std::collections::BTreeMap;
    use std::sync::atomic::{AtomicU64, Ordering};

    static NEXT: AtomicU64 = AtomicU64::new(0);

    struct Fixture {
        root: PathBuf,
        parent: PathBuf,
        temporary: PathBuf,
        target: PathBuf,
        marker: Vec<u8>,
    }

    impl Fixture {
        fn new() -> Self {
            let id = NEXT.fetch_add(1, Ordering::Relaxed);
            let root =
                std::env::temp_dir().join(format!("cott-init-fault-{}-{id}", std::process::id()));
            fs::create_dir_all(&root).expect("fixture root");
            let parent = root.join("parent");
            fs::create_dir(&parent).expect("fixture parent");
            let temporary = parent.join(".cott-init-test");
            let target = parent.join("demo-app");
            Self {
                root,
                parent,
                temporary,
                target,
                marker: b"{\"nonce\":\"test\",\"schema_version\":1}\n".to_vec(),
            }
        }

        fn expected(&self, marker: bool) -> BTreeMap<PathBuf, Vec<u8>> {
            let mut tree = BTreeMap::from([
                (
                    PathBuf::from(".gitignore"),
                    b".cott/\n.venv/\ngenerated/generation.json\n__pycache__/\n*.py[cod]\n"
                        .to_vec(),
                ),
                (
                    PathBuf::from("cott.toml"),
                    b"[project]\nname = \"demo-app\"\nversion = \"0.1.0\"\nsource = \"src\"\n\n[target.python]\nsource = \"python\"\ngenerated = \"generated/python\"\nstubs = \"generated/stubs\"\nlockfile = \"python/uv.lock\"\ninterpreter = \".venv/bin/python\"\ntype_checker = \".venv/bin/basedpyright\"\nruntime_validation = \"boundary\"\n"
                        .to_vec(),
                ),
                (
                    PathBuf::from("python/.python-version"),
                    b"3.14\n".to_vec(),
                ),
                (
                    PathBuf::from("python/pyproject.toml"),
                    b"[project]\nname = \"demo-app\"\nversion = \"0.1.0\"\nrequires-python = \">=3.14.6,<3.15\"\ndependencies = []\n\n[dependency-groups]\ndev = [\"basedpyright>=1.39.9\"]\n"
                        .to_vec(),
                ),
                (
                    PathBuf::from("src/demo_app/main.cott"),
                    b"module demo_app.main\n".to_vec(),
                ),
            ]);
            if marker {
                tree.insert(PathBuf::from(".cott-init"), self.marker.clone());
            }
            tree
        }

        fn publish(&self) -> Result<(), String> {
            publish_init_scaffold(
                &self.temporary,
                &self.target,
                &self.parent,
                "demo-app",
                &self.marker,
            )
        }
    }

    impl Drop for Fixture {
        fn drop(&mut self) {
            clear_init_fault();
            let _ = fs::remove_dir_all(&self.root);
        }
    }

    fn assert_tree(path: &Path, expected: BTreeMap<PathBuf, Vec<u8>>) {
        assert_eq!(collect_tree(path).expect("tree"), expected);
    }

    #[test]
    fn scaffold_file_and_directory_fsync_faults_leave_no_target() {
        for fault in [
            "init.scaffold.file_fsync",
            "init.scaffold.tree_file_fsync",
            "init.scaffold.directory_fsync",
        ] {
            let fixture = Fixture::new();
            arm_init_fault(fault);
            assert!(fixture.publish().is_err(), "{fault}");
            assert!(!fixture.target.exists());
            clear_init_fault();
            remove_owned_init_temp(&fixture.temporary, &fixture.marker, &fixture.parent)
                .expect("owned temp cleanup");
            assert!(!fixture.temporary.exists());
        }
    }

    #[test]
    fn no_replace_publish_fault_and_collision_preserve_foreign_target() {
        let fixture = Fixture::new();
        arm_init_fault("init.publish.noreplace");
        assert!(fixture.publish().is_err());
        clear_init_fault();
        remove_owned_init_temp(&fixture.temporary, &fixture.marker, &fixture.parent)
            .expect("owned temp cleanup");
        assert!(!fixture.target.exists());

        let fixture = Fixture::new();
        fs::create_dir(&fixture.target).expect("foreign target");
        fs::write(fixture.target.join("foreign"), b"keep").expect("foreign file");
        assert!(fixture.publish().is_err());
        remove_owned_init_temp(&fixture.temporary, &fixture.marker, &fixture.parent)
            .expect("owned temp cleanup");
        assert_tree(
            &fixture.target,
            BTreeMap::from([(PathBuf::from("foreign"), b"keep".to_vec())]),
        );
    }

    #[test]
    fn publish_parent_fsync_fault_leaves_owned_incomplete_target_then_cleans() {
        let fixture = Fixture::new();
        arm_init_fault("init.publish.parent_fsync");
        assert!(fixture.publish().is_err());
        assert_tree(&fixture.target, fixture.expected(true));
        clear_init_fault();
        remove_owned_init(&fixture.target, &fixture.marker, &fixture.parent)
            .expect("owned target cleanup");
        assert!(!fixture.target.exists());
    }

    #[test]
    fn temp_cleanup_remove_and_parent_fsync_are_retryable() {
        for fault in ["init.cleanup.temp_remove", "init.cleanup.temp_parent_fsync"] {
            let fixture = Fixture::new();
            arm_init_fault("init.publish.noreplace");
            assert!(fixture.publish().is_err());
            clear_init_fault();
            arm_init_fault(fault);
            assert!(
                remove_owned_init_temp(&fixture.temporary, &fixture.marker, &fixture.parent)
                    .is_err()
            );
            if fault == "init.cleanup.temp_remove" {
                assert_tree(&fixture.temporary, fixture.expected(true));
            } else {
                assert!(!fixture.temporary.exists());
            }
            clear_init_fault();
            remove_owned_init_temp(&fixture.temporary, &fixture.marker, &fixture.parent)
                .expect("retry temp cleanup");
            assert!(!fixture.temporary.exists());
        }
    }

    #[test]
    fn target_cleanup_remove_and_parent_fsync_are_ownership_checked_and_retryable() {
        for fault in [
            "init.cleanup.target_remove",
            "init.cleanup.target_parent_fsync",
        ] {
            let fixture = Fixture::new();
            fixture.publish().expect("publish");
            arm_init_fault(fault);
            assert!(remove_owned_init(&fixture.target, &fixture.marker, &fixture.parent).is_err());
            if fault == "init.cleanup.target_remove" {
                assert_tree(&fixture.target, fixture.expected(true));
            } else {
                assert!(!fixture.target.exists());
            }
            clear_init_fault();
            remove_owned_init(&fixture.target, &fixture.marker, &fixture.parent)
                .expect("retry target cleanup");
            assert!(!fixture.target.exists());
        }

        let fixture = Fixture::new();
        fs::create_dir(&fixture.target).expect("foreign target");
        fs::write(fixture.target.join(".cott-init"), b"foreign").expect("foreign marker");
        assert!(remove_owned_init(&fixture.target, &fixture.marker, &fixture.parent).is_err());
        assert!(fixture.target.exists());
    }

    #[test]
    fn final_commit_faults_preserve_exact_ownership_states_and_resume() {
        for fault in [
            "init.commit.marker_unlink",
            "init.commit.target_fsync",
            "init.commit.parent_fsync",
        ] {
            let fixture = Fixture::new();
            fixture.publish().expect("publish");
            arm_init_fault(fault);
            assert!(commit_init(&fixture.target, &fixture.marker, &fixture.parent).is_err());
            clear_init_fault();
            if fault == "init.commit.marker_unlink" {
                assert_tree(&fixture.target, fixture.expected(true));
                commit_init(&fixture.target, &fixture.marker, &fixture.parent)
                    .expect("retry commit");
            } else {
                assert_tree(&fixture.target, fixture.expected(false));
            }
            assert_tree(&fixture.target, fixture.expected(false));
        }
    }
    #[test]
    fn tool_versions_require_the_minimum_release() {
        assert!(supports_uv_version("uv 0.12.3"));
        assert!(supports_uv_version("uv 0.12.4"));
        assert!(!supports_uv_version("uv 0.12.2"));
        assert!(!supports_uv_version("uv 0.12"));
        assert!(supports_python_version("3.14.6"));
        assert!(supports_python_version("3.14.7"));
        assert!(!supports_python_version("3.14.5"));
        assert!(!supports_python_version("3.15.0"));
        assert!(supports_basedpyright_version("basedpyright 1.39.9"));
        assert!(supports_basedpyright_version("1.40.0"));
        assert!(!supports_basedpyright_version("basedpyright 1.39.8"));
    }
}
