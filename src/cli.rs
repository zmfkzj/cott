#[cfg(test)]
use std::cell::RefCell;
use std::collections::BTreeMap;
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
use crate::agent::{AgentRunCandidate, adapter, render_prompt, run_agent};
use crate::binding::{ResolvedBinding, resolve_implementations, validate_candidate};
use crate::compiler::{ProjectDiagnostic, parse_project};
use crate::diagnostics::{
    Diagnostic, DiagnosticReport, Severity, SourceMap, SourceSpan, Span, code,
};
use crate::hash::sha256_hex;
use crate::hir::lower_with_effects;
use crate::ir::render;
use crate::project::{ProjectPaths, discover_sources_from_paths, load_config_with_paths};
use crate::provenance::{AgentRun, AgentStatus, GenerationRecord, StreamDigest};
use crate::python::artifact_plan::{PythonArtifactPlan, PythonCallable, PythonCallableKind};
use crate::python_emit::{Emission, EmitDiagnostic, emit};
use crate::python_verify::verify_python;
use crate::transaction::{ChangeSet, InputSnapshot, Operation, ProjectSession};
use crate::version::{is_at_least, parse_version};

const USAGE: &str = "Usage:\n  cott init <path> [--name <name>] [--no-sync] [--format json]\n  cott check [<source.cott>] [--project <dir>] [--format json]\n  cott fmt [--check] [--project <dir>] [--format json]\n  cott emit ir|python [--project <dir>] [--format json]\n  cott generate [<fully.qualified.callable>] --agent codex|omp --target python [--project <dir>] [--format json]\n  cott verify [--project <dir>] [--format json]\n  cott diff [--baseline <generation.json>] [--exit-code] [--project <dir>] [--format json]\n  cott lsp\n";

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
    let json_formats = arguments
        .windows(2)
        .filter(|pair| pair[0] == "--format" && pair[1] == "json")
        .count();
    if json_formats > 1 && !matches!(arguments.first(), Some(command) if command == "lsp") {
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
    if json_formats == 1 && !matches!(arguments.first(), Some(command) if command == "lsp") {
        return run_json(arguments);
    }

    match parse_command(&arguments) {
        Ok(Command::Lsp) => crate::lsp::run(),
        Ok(Command::Help) => {
            print!("{USAGE}");
            0
        }
        Ok(Command::Init {
            path,
            name,
            no_sync,
            format,
        }) => init_project(path, name, no_sync, format),
        Ok(Command::Check {
            source, project, ..
        }) => check_project(project, source),
        Ok(Command::Fmt { check, project, .. }) => format_project(project, check),
        Ok(Command::Emit {
            target: EmitTarget::Ir,
            project,
            ..
        }) => emit_ir(project),
        Ok(Command::Emit {
            target: EmitTarget::Python,
            project,
            ..
        }) => match plan(project) {
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
        },
        Ok(Command::Generate {
            symbol,
            agent,
            project,
            ..
        }) => generate_project(project, symbol, agent),
        Ok(Command::Diff {
            baseline,
            exit_code,
            project,
            ..
        }) => diff_project(project, baseline, exit_code),
        Ok(Command::Verify { project, .. }) => match plan(project) {
            Ok(plan) => match verify(&plan) {
                Ok(()) => {
                    println!("verified {}", generated_path(&plan.paths));
                    0
                }
                Err(messages) => {
                    for message in messages {
                        eprintln!("error: {message}");
                    }
                    4
                }
            },
            Err(code) => code,
        },
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
    let init_no_sync = human_arguments.first().is_some_and(|value| value == "init")
        && human_arguments.iter().any(|value| value == "--no-sync");
    let project_paths = json_project_paths(&human_arguments);
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
        let body = line.strip_prefix("error: ").unwrap_or(line);
        let mut diagnostic = Diagnostic::error(error_code, body, Span::new(0, 0));
        diagnostic.source_order = source_order;
        if let Some(paths) = &project_paths
            && let Some((location, message)) = body.rsplit_once(": ")
            && let Some((path, range)) = location.rsplit_once(':')
            && let Some((start, end)) = range.split_once('-')
            && let (Ok(start), Ok(end)) = (start.parse::<usize>(), end.parse::<usize>())
        {
            let relative = PathBuf::from(path);
            let absolute = paths.source_dir.join(&relative);
            if let Ok(bytes) = fs::read(&absolute) {
                let source_root = paths
                    .source_dir
                    .strip_prefix(&paths.root)
                    .unwrap_or(&paths.source_dir);
                let file = *source_ids
                    .entry(relative.clone())
                    .or_insert_with(|| sources.add(source_root.join(&relative), bytes));
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

fn json_project_paths(arguments: &[OsString]) -> Option<ProjectPaths> {
    let root = arguments
        .windows(2)
        .find(|pair| pair[0] == "--project")
        .map(|pair| PathBuf::from(&pair[1]))
        .or_else(|| std::env::current_dir().ok())?;
    load_config_with_paths(&root).ok().map(|(_, paths)| paths)
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
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Command {
    Init {
        path: PathBuf,
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
        agent: Option<AgentKind>,
        project: Option<PathBuf>,
        format: OutputFormat,
    },
    Verify {
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
}

pub fn parse_command(arguments: &[OsString]) -> Result<Command, &'static str> {
    if arguments.len() == 1 && matches!(arguments[0].to_str(), Some("--help" | "-h")) {
        return Ok(Command::Help);
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
        "lsp" if values.is_empty() => Ok(Command::Lsp),
        "lsp" => Err("`lsp` does not accept options or operands"),
        "verify" => {
            let options = ExistingOptions::parse(values)?;
            Ok(Command::Verify {
                project: options.project,
                format: options.format,
            })
        }
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
    let path = values
        .first()
        .filter(|value| !value.is_empty())
        .ok_or("`init` requires a path")?;
    if path == "--project" {
        return Err("`init` does not accept `--project`");
    }
    let mut name = None;
    let mut no_sync = false;
    let mut format = OutputFormat::Human;
    let mut index = 1;
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
            Some("--no-sync") if !no_sync => no_sync = true,
            Some("--format") if format == OutputFormat::Human => {
                index += 1;
                if values.get(index).and_then(|value| value.to_str()) != Some("json") {
                    return Err("`--format` requires `json`");
                }
                format = OutputFormat::Json;
            }
            Some("--project") => return Err("`init` does not accept `--project`"),
            _ => return Err("unexpected or duplicate option"),
        }
        index += 1;
    }
    Ok(Command::Init {
        path: PathBuf::from(path),
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
        _ => return Err("expected `emit ir` or `emit python`"),
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
    let mut options = ExistingOptions::default();
    let mut index = 0;
    while index < values.len() {
        match values[index].to_str() {
            Some("--agent") if agent.is_none() => {
                index += 1;
                agent = match values.get(index).and_then(|value| value.to_str()) {
                    Some("codex") => Some(AgentKind::Codex),
                    Some("omp") => Some(AgentKind::Omp),
                    _ => return Err("`--agent` requires `codex` or `omp`"),
                };
            }
            Some("--target") if target.is_none() => {
                index += 1;
                target = Some(
                    values
                        .get(index)
                        .and_then(|value| value.to_str())
                        .ok_or("`--target` requires `python`")?,
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
    if target != Some("python") {
        return Err("`generate` requires `--target python`");
    }
    Ok(Command::Generate {
        symbol,
        agent,
        project: options.project,
        format: options.format,
    })
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
    let input_snapshot = match capture_expected_inputs(&paths, &input_hashes, []) {
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
    if let Err(message) = enrich_generation_record(&paths, input_hashes, &mut emission) {
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

fn enrich_generation_record(
    paths: &ProjectPaths,
    inputs: BTreeMap<String, String>,
    emission: &mut Emission,
) -> Result<(), String> {
    let bytes = emission
        .files
        .get(Path::new("generation.json"))
        .ok_or_else(|| "emission omitted generation.json".to_owned())?;
    let mut record = GenerationRecord::parse(bytes)
        .map_err(|error| format!("invalid planned generation record: {error}"))?;
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
        record.current.agent_runs = existing
            .current
            .agent_runs
            .into_iter()
            .filter(|run| {
                record
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
            })
            .collect();
    }
    record.current.inputs =
        serde_json::to_value(inputs).map_err(|error| format!("serialize input hashes: {error}"))?;
    record.current.dependencies = dependencies;
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
    inputs: &BTreeMap<String, String>,
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
    let Some(baseline) = record.last_verified else {
        return Ok(());
    };
    let baseline_inputs = baseline
        .inputs
        .as_object()
        .ok_or("verified baseline inputs are not an object")?;
    let changed_inputs = baseline_inputs
        .iter()
        .any(|(path, hash)| inputs.get(path).map(String::as_str) != hash.as_str())
        || inputs
            .keys()
            .any(|path| !baseline_inputs.contains_key(path));
    if changed_inputs {
        return Err(
            "verified baseline inputs changed; run `cott emit python` and `cott verify` before generation"
                .to_owned(),
        );
    }
    for (relative, expected) in &baseline.managed_files {
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
    if let Err(error) = enrich_generation_record(&paths, input_hashes, &mut emission) {
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
    let mut managed_files = actual
        .iter()
        .filter(|(path, _)| path.as_path() != Path::new("generation.json"))
        .map(|(path, bytes)| {
            (
                relative_root
                    .join(path)
                    .to_string_lossy()
                    .replace('\\', "/"),
                format!("sha256:{}", sha256_hex(bytes)),
            )
        })
        .collect::<BTreeMap<_, _>>();
    managed_files.retain(|path, _| {
        !Path::new(path)
            .strip_prefix(relative_root)
            .is_ok_and(|relative| relative.starts_with("ir"))
    });
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
    snapshot.merge_missing(output_snapshot);
    match session.apply(&snapshot, &changes) {
        Ok(()) => 0,
        Err(error) => {
            eprintln!("error: {error}");
            6
        }
    }
}
fn generate_project(
    project_argument: Option<PathBuf>,
    symbol: Option<String>,
    agent: Option<AgentKind>,
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
    let callables = plan
        .callables()
        .into_iter()
        .map(|callable| (callable.cott_symbol.clone(), callable))
        .collect::<BTreeMap<String, PythonCallable>>();
    let requested = symbol.as_deref();
    let mut unresolved = resolution
        .unresolved
        .into_iter()
        .filter(|binding| requested.is_none_or(|symbol| symbol == binding.cott_symbol))
        .collect::<Vec<_>>();
    if let Some(symbol) = requested {
        if !callables.contains_key(symbol) {
            eprintln!("error: unknown callable `{symbol}`");
            return 2;
        }
    }
    unresolved.sort_by(|left, right| left.cott_symbol.cmp(&right.cott_symbol));
    let mut bindings = resolution.resolved;
    add_binding_input_hashes(&paths, &bindings, &mut input_hashes);
    let candidate_paths = match unresolved
        .iter()
        .map(|binding| {
            binding
                .source
                .strip_prefix(&paths.root)
                .map(Path::to_path_buf)
                .map_err(|_| {
                    format!(
                        "implementation path escaped project root: {}",
                        binding.source.display()
                    )
                })
        })
        .collect::<Result<Vec<_>, _>>()
    {
        Ok(paths) => paths,
        Err(error) => {
            eprintln!("error: {error}");
            return 6;
        }
    };
    let input_snapshot = match capture_expected_inputs(&paths, &input_hashes, candidate_paths) {
        Ok(snapshot) => snapshot,
        Err(error) => {
            eprintln!("error: {error}");
            return 6;
        }
    };
    let mut durable_sources = Vec::new();
    let mut generated_runs = Vec::new();
    if !unresolved.is_empty() {
        let Some(agent) = agent else {
            eprintln!("error: unresolved selected callable requires `--agent codex|omp`");
            return 2;
        };
        if let Err(error) = verified_baseline_guard(&paths, &input_hashes) {
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
        for unresolved_binding in unresolved {
            let callable = callables
                .get(&unresolved_binding.cott_symbol)
                .expect("resolution callable was selected from the artifact plan");
            let temporary = match agent_workspace() {
                Ok(paths) => paths,
                Err(error) => {
                    eprintln!("error: {error}");
                    return 6;
                }
            };
            let target = temporary.workspace.join("implementation.py");
            let module_ir = match ir
                .modules
                .iter()
                .find(|module| module.module.as_string() == callable.module)
            {
                Some(module) => module.bytes.clone(),
                None => {
                    let _ = fs::remove_dir_all(&temporary.root);
                    eprintln!("error: selected callable has no canonical IR module");
                    return 1;
                }
            };
            let fully_qualified = callable.cott_symbol.clone();
            let bound_symbols = bindings
                .iter()
                .filter(|binding| matches!(&binding.kind, PythonCallableKind::Function))
                .map(|binding| format!("from {} import {}", binding.module, binding.function))
                .collect::<Vec<_>>()
                .join("\n");
            let binding_context = bindings
                .iter()
                .map(|binding| {
                    format!(
                        "# {}\n{}",
                        binding.source.display(),
                        String::from_utf8_lossy(&binding.bytes)
                    )
                })
                .collect::<Vec<_>>()
                .join("\n");
            let target_rules = match &callable.kind {
                PythonCallableKind::Function => format!(
                    "CPython 3.14.6, fully annotated Python. Import only names the implementation file actually references. Keep every `def` signature on one physical line and end the file with exactly one newline. Preserve every declared ABI annotation exactly: import I8/I16/I32/I64/U8/U16/U32/U64/F32/F64, Result, Option, Unit, CottList, CottSet, FrozenMap, and CottTuple2 from cott_runtime as required; never replace contract annotations or returned contract containers with Python primitives or built-in list/set/dict/tuple, never import a nonexistent `List`, and never spell Result as an Ok/Err union. Numeric ABI aliases are plain int/float at runtime: use normal Python arithmetic and comparisons, not `.value`, constructors, casts, or `isinstance`. `Unit` means `None`; do not construct it. Use `Option.Nothing` exactly as a value; do not call it. Boolean comparison expressions have type bool; do not wrap them in a nonexistent `Bool`. Use contract containers directly: CottList(xs), CottSet(xs), FrozenMap({}), and CottTuple2(a, b). For Result returns import and return Result.Ok(value) or Result.Err(error); never raise, catch, or inspect Result. Do not use classes, mutable module state, `Any`, casts, `typing.cast`, `isinstance`, `type(...)`, dynamic imports, reflection, exception handling, `exec`, `eval`, `globals`, or `locals`. For other modules import public generated symbols only through `from {0} import name` and generated value types only through `from {0}_types import Type`. Do not import concrete facade classes from generated type modules.",
                    callable.module
                ),
                PythonCallableKind::ImplMethod { concrete } => format!(
                    "CPython 3.14.6, fully annotated Python. Import only names the implementation file actually references. Keep every `def` signature on one physical line and end the file with exactly one newline. The canonical function's leading `self` annotation must be `{concrete}`. Preserve every declared ABI annotation exactly: import I8/I16/I32/I64/U8/U16/U32/U64/F32/F64, Result, Option, Unit, CottList, CottSet, FrozenMap, and CottTuple2 from cott_runtime as required; never replace contract annotations or returned contract containers with Python primitives or built-in list/set/dict/tuple, never import a nonexistent `List`, and never spell Result as an Ok/Err union. Numeric ABI aliases are plain int/float at runtime: use normal Python arithmetic and comparisons, not `.value`, constructors, casts, or `isinstance`. `Unit` means `None`; do not construct it. Use `Option.Nothing` exactly as a value; do not call it. Boolean comparison expressions have type bool; do not wrap them in a nonexistent `Bool`. Use contract containers directly: CottList(xs), CottSet(xs), FrozenMap({}), and CottTuple2(a, b). For Result returns import and return Result.Ok(value) or Result.Err(error); never raise, catch, or inspect Result. Do not use classes, mutable module state, `Any`, casts, `typing.cast`, `isinstance`, `type(...)`, dynamic imports, reflection, exception handling, `exec`, `eval`, `globals`, or `locals`. The compiler-owned concrete facade class `{concrete}` is absent from `{0}_types`; import it exactly as `from {0} import {concrete}` for the `self` annotation. Generated value-type imports remain `from {0}_types import Type`.",
                    callable.module
                ),
            };
            let project_rules = config
                .generator
                .rules
                .as_ref()
                .map(|path| fs::read(paths.root.join(path)))
                .transpose()
                .map_err(|error| error.to_string());
            let result = project_rules
                .and_then(|project_rules| {
                    render_prompt(
                        callable,
                        &module_ir,
                        &binding_context,
                        &target_rules,
                        &config.python.external_types,
                        &bound_symbols,
                        None,
                        project_rules.as_deref(),
                        &target,
                    )
                })
                .and_then(|prompt| {
                    run_agent(
                        agent,
                        executable.clone(),
                        &temporary.workspace,
                        &temporary.scratch,
                        &target,
                        prompt,
                        config.generator.timeout_seconds,
                    )
                })
                .and_then(|candidate| {
                    validate_candidate(
                        &config,
                        &paths,
                        &plan,
                        &fully_qualified,
                        &candidate.implementation,
                    )
                    .map(|_| candidate)
                });
            let _ = fs::remove_dir_all(&temporary.root);
            let candidate = match result {
                Ok(candidate) => candidate,
                Err(error) => {
                    eprintln!("error: agent generation for `{fully_qualified}` failed: {error}");
                    return 5;
                }
            };
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
                PythonCallableKind::Function => {
                    format!("_cott_impl.{}.{}", callable.module, callable.name)
                }
                PythonCallableKind::ImplMethod { concrete } => {
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
    if let Err(message) = enrich_generation_record(&paths, input_hashes, &mut emission) {
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
    if !generated_scope.is_empty() {
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
            return 5;
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
        Ok(()) => 0,
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
    let report = generation_diff(&baseline_snapshot, &current);
    if report.lines.is_empty() {
        println!("NO CHANGE");
    } else {
        for (section, lines) in report.lines {
            println!("{section}:");
            for line in lines {
                println!("- {line}");
            }
        }
    }
    if exit_code && report.breaking { 7 } else { 0 }
}

struct DiffReport {
    breaking: bool,
    lines: BTreeMap<&'static str, Vec<String>>,
}

fn generation_diff(
    baseline: &crate::provenance::GenerationSnapshot,
    current: &crate::provenance::GenerationSnapshot,
) -> DiffReport {
    let mut lines = BTreeMap::<&'static str, Vec<String>>::new();
    let old = declarations_by_name(&baseline.contract_surface);
    let new = declarations_by_name(&current.contract_surface);
    let mut breaking = false;
    for (name, declaration) in &old {
        match new.get(name) {
            None => {
                breaking = true;
                lines
                    .entry("CONTRACT BREAKING")
                    .or_default()
                    .push(format!("{name} was removed"));
            }
            Some(updated)
                if normalized_declaration(declaration) != normalized_declaration(updated) =>
            {
                breaking = true;
                lines
                    .entry("CONTRACT BREAKING")
                    .or_default()
                    .push(format!("{name} contract changed"));
            }
            Some(updated) if declaration != updated => {
                lines
                    .entry("DOCUMENTATION")
                    .or_default()
                    .push(format!("{name} documentation changed"));
            }
            Some(_) => {}
        }
    }
    for name in new.keys().filter(|name| !old.contains_key(*name)) {
        lines
            .entry("CONTRACT NON-BREAKING")
            .or_default()
            .push(format!("{name} was added"));
    }
    let old_symbols = symbol_sets(&baseline.public_python_symbols);
    let new_symbols = symbol_sets(&current.public_python_symbols);
    for (module, symbols) in &old_symbols {
        for symbol in symbols.iter().filter(|symbol| {
            !new_symbols
                .get(module)
                .is_some_and(|new| new.contains(*symbol))
        }) {
            breaking = true;
            lines
                .entry("CONTRACT BREAKING")
                .or_default()
                .push(format!("{module}.{symbol} Python symbol was removed"));
        }
    }
    compare_implementations(
        &baseline.implementations,
        &current.implementations,
        &mut lines,
    );
    if baseline.dependencies != current.dependencies {
        lines
            .entry("DEPENDENCY")
            .or_default()
            .push("normalized dependency identity changed".to_owned());
    }
    for (name, hash) in input_hashes(&baseline.inputs) {
        if current.inputs.get(&name) != Some(&hash)
            && !name.ends_with(".cott")
            && !name.ends_with(".py")
        {
            lines
                .entry("IMPLEMENTATION")
                .or_default()
                .push(format!("{name} input changed"));
        }
    }
    for name in input_hashes(&current.inputs)
        .keys()
        .filter(|name| baseline.inputs.get(*name).is_none())
    {
        if !name.ends_with(".cott") && !name.ends_with(".py") {
            lines
                .entry("IMPLEMENTATION")
                .or_default()
                .push(format!("{name} input was added"));
        }
    }
    for tool in ["compiler", "runtime"] {
        let old = baseline
            .tools
            .get(tool)
            .and_then(|value| value.get("version"));
        let new = current
            .tools
            .get(tool)
            .and_then(|value| value.get("version"));
        if old != new {
            lines
                .entry("TOOLCHAIN")
                .or_default()
                .push(format!("{tool} version changed"));
        }
    }
    for values in lines.values_mut() {
        values.sort();
        values.dedup();
    }
    DiffReport { breaking, lines }
}

fn declarations_by_name(value: &serde_json::Value) -> BTreeMap<String, serde_json::Value> {
    value
        .as_object()
        .into_iter()
        .flat_map(|modules| modules.values())
        .filter_map(|module| {
            module
                .get("declarations")
                .and_then(serde_json::Value::as_array)
        })
        .flatten()
        .filter_map(|declaration| {
            Some((
                declaration.get("name")?.as_str()?.to_owned(),
                declaration.clone(),
            ))
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

fn compare_implementations(
    baseline: &serde_json::Value,
    current: &serde_json::Value,
    lines: &mut BTreeMap<&'static str, Vec<String>>,
) {
    let index = |value: &serde_json::Value| {
        value
            .as_array()
            .into_iter()
            .flatten()
            .filter_map(|implementation| {
                Some((
                    implementation.get("cott_symbol")?.as_str()?.to_owned(),
                    implementation.clone(),
                ))
            })
            .collect::<BTreeMap<_, _>>()
    };
    let old = index(baseline);
    let new = index(current);
    for symbol in old.keys().chain(new.keys()) {
        if old.get(symbol) != new.get(symbol) {
            lines
                .entry("IMPLEMENTATION")
                .or_default()
                .push(format!("{symbol} implementation changed"));
        }
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
        Ok(_) => 0,
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
        eprintln!("error: cott 0.1 requires uv >=0.12.3, found `{version}`");
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
            expected_record.current.unresolved.join(", ")
        ));
    }
    if !mismatches.is_empty() {
        return Err(mismatches);
    }
    let evidence = verify_python(&plan.config, &plan.paths, &artifact_root, &plan.ir, None)
        .map_err(|message| vec![message])?;
    let mut record = expected_record;
    record.current.tools = evidence.tools;
    record.current.dependencies = evidence.dependencies;
    record.current.verified = true;
    record.current.verification = evidence.report;
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
        .map_err(|error| vec![error.to_string()])
}

fn comparable_snapshot(snapshot: &crate::provenance::GenerationSnapshot) -> serde_json::Value {
    let mut value = serde_json::to_value(snapshot).expect("generation snapshot serializes");
    let object = value
        .as_object_mut()
        .expect("generation snapshot is an object");
    for field in [
        "agent_runs",
        "generation_id",
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
