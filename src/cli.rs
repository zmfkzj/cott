use std::collections::BTreeMap;
use std::ffi::OsString;
use std::fs;
use std::path::{Component, Path, PathBuf};
use std::process::Command as ProcessCommand;
use std::time::{SystemTime, UNIX_EPOCH};

pub use crate::agent::AgentKind;
use crate::agent::{adapter, render_prompt, run_agent};
use crate::binding::{
    ResolvedBinding, resolve_bindings, resolve_implementations, validate_candidate,
};
use crate::compiler::{ProjectDiagnostic, parse_project};
use crate::hir::lower;
use crate::ir::from_hir;
use crate::project::{Project, discover_sources, load_project};
use crate::python_emit::{Emission, EmitDiagnostic, emit};
use crate::transaction::{ChangeSet, InputSnapshot, Operation, ProjectSession};

const USAGE: &str = "Usage:\n  cott init <path> [--name <name>] [--no-sync] [--format json]\n  cott check [<source.cott>] [--project <dir>] [--format json]\n  cott fmt [--check] [--project <dir>] [--format json]\n  cott emit ir|python [--project <dir>] [--format json]\n  cott generate [<fully.qualified.function>] --agent codex|omp --target python [--project <dir>] [--format json]\n  cott verify [--project <dir>] [--format json]\n  cott diff [--baseline <generation.json>] [--exit-code] [--project <dir>] [--format json]\n";

/// Runs the command line interface. Parsing is intentionally closed: unknown,
/// duplicate, or context-invalid options are usage errors before project I/O.
pub fn run(arguments: impl IntoIterator<Item = OsString>) -> i32 {
    let mut arguments = arguments.into_iter();
    let _program = arguments.next();
    let arguments: Vec<OsString> = arguments.collect();

    match parse_command(&arguments) {
        Ok(Command::Help) => {
            print!("{USAGE}");
            0
        }
        Ok(Command::Init {
            path,
            name,
            no_sync,
            ..
        }) => init_project(path, name, no_sync),
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
                    println!("{}", generated_path(&plan.project));
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
                    println!("verified {}", generated_path(&plan.project));
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
    project: Project,
    emission: Emission,
}

fn plan(project_argument: Option<PathBuf>) -> Result<PlannedProject, i32> {
    let root = match project_argument {
        Some(path) => path,
        None => match std::env::current_dir() {
            Ok(path) => path,
            Err(error) => {
                eprintln!("error: failed to determine current directory: {error}");
                return Err(2);
            }
        },
    };
    let project = match load_project(&root) {
        Ok(project) => project,

        Err(error) => {
            eprintln!("error: {error}");
            return Err(2);
        }
    };
    if let Err(message) = artifact_root(&project) {
        eprintln!("error: {message}");
        return Err(2);
    }
    let sources = match discover_sources(&project) {
        Ok(sources) => sources,
        Err(error) => {
            eprintln!("error: {error}");
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
    let hir = match lower(&project.source_dir, parsed) {
        Ok(hir) => hir,
        Err(diagnostics) => {
            print_project_diagnostics(&diagnostics);
            return Err(3);
        }
    };
    let ir = match from_hir(&hir) {
        Ok(ir) => ir,
        Err(error) => {
            eprintln!("error: {error}");
            return Err(1);
        }
    };
    let Some(semantic) = hir.legacy() else {
        eprintln!("error: legacy binding bridge unavailable");
        return Err(1);
    };
    let bindings = match resolve_bindings(&project, semantic) {
        Ok(bindings) => bindings,
        Err(diagnostics) => {
            for diagnostic in diagnostics {
                eprintln!(
                    "error: {}: {}",
                    display_path(&project.root, &diagnostic.path),
                    diagnostic.message
                );
            }
            return Err(4);
        }
    };
    let emission = match emit(&project, semantic, &ir, &bindings) {
        Ok(emission) => emission,
        Err(diagnostics) => {
            print_emit_diagnostics(&project, &diagnostics);
            return Err(4);
        }
    };
    Ok(PlannedProject { project, emission })
}
fn emit_ir(project_argument: Option<PathBuf>) -> i32 {
    let Ok(root) = project_root(project_argument) else {
        return 2;
    };
    let project = match load_project(&root) {
        Ok(project) => project,
        Err(error) => {
            eprintln!("error: {error}");
            return 2;
        }
    };
    let session = match ProjectSession::acquire(&project.root) {
        Ok(session) => session,
        Err(error) => {
            eprintln!("error: {error}");
            return 6;
        }
    };
    let sources = match discover_sources(&project) {
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
    let hir = match lower(&project.source_dir, parsed) {
        Ok(hir) => hir,
        Err(diagnostics) => {
            print_project_diagnostics(&diagnostics);
            return 3;
        }
    };
    let ir = match from_hir(&hir) {
        Ok(ir) => ir,
        Err(error) => {
            eprintln!("error: {error}");
            return 1;
        }
    };
    let artifact_root = match artifact_root(&project) {
        Ok(path) => path,
        Err(error) => {
            eprintln!("error: {error}");
            return 2;
        }
    };
    let relative_root = artifact_root
        .strip_prefix(&project.root)
        .expect("artifact root is project-relative");
    let mut paths = Vec::new();
    let mut changes = ChangeSet::default();
    for module in ir.modules {
        let path = relative_root
            .join("ir")
            .join(format!("{}.json", module.module.as_string()));
        let current = fs::read(project.root.join(&path)).ok();
        if current.as_deref() != Some(&module.bytes) {
            paths.push(path.clone());
            changes.operations.push(Operation::Write {
                path,
                bytes: module.bytes,
            });
        }
    }
    let snapshot = match InputSnapshot::capture(&project.root, paths) {
        Ok(snapshot) => snapshot,
        Err(error) => {
            eprintln!("error: {error}");
            return 6;
        }
    };
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
    let project = match load_project(&root) {
        Ok(project) => project,
        Err(error) => {
            eprintln!("error: {error}");
            return 2;
        }
    };
    let sources = match discover_sources(&project) {
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
    let hir = match lower(&project.source_dir, parsed) {
        Ok(hir) => hir,
        Err(diagnostics) => {
            print_project_diagnostics(&diagnostics);
            return 3;
        }
    };
    let ir = match from_hir(&hir) {
        Ok(ir) => ir,
        Err(error) => {
            eprintln!("error: {error}");
            return 1;
        }
    };
    let Some(semantic) = hir.legacy() else {
        eprintln!("error: legacy binding bridge unavailable");
        return 1;
    };
    let resolution = match resolve_implementations(&project, semantic) {
        Ok(resolution) => resolution,
        Err(diagnostics) => {
            print_binding_diagnostics(&project, diagnostics);
            return 4;
        }
    };
    let requested = symbol.as_deref();
    let mut unresolved = resolution
        .unresolved
        .into_iter()
        .filter(|binding| {
            requested.is_none_or(|symbol| {
                symbol == format!("{}.{}", binding.module.as_string(), binding.function)
            })
        })
        .collect::<Vec<_>>();
    if let Some(symbol) = requested {
        let known = hir.modules.iter().any(|module| {
            module.declarations.iter().any(|declaration| {
                matches!(declaration, crate::hir::HirDeclaration::Function(function)
                    if function.id.as_string() == symbol)
            })
        });
        if !known {
            eprintln!("error: unknown function `{symbol}`");
            return 2;
        }
    }
    unresolved
        .sort_by_key(|binding| format!("{}.{}", binding.module.as_string(), binding.function));
    let mut bindings = resolution.resolved;
    let mut durable_sources = Vec::new();
    if !unresolved.is_empty() {
        let Some(agent) = agent else {
            eprintln!("error: unresolved selected function requires `--agent codex|omp`");
            return 2;
        };
        let executable = match resolve_executable(adapter(agent).executable_name) {
            Ok(path) => path,
            Err(error) => {
                eprintln!("error: {error}");
                return 5;
            }
        };
        for unresolved_binding in unresolved {
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
                .find(|module| module.module == unresolved_binding.module)
            {
                Some(module) => module.bytes.clone(),
                None => {
                    let _ = fs::remove_dir_all(&temporary.root);
                    eprintln!("error: selected function has no canonical IR module");
                    return 1;
                }
            };
            let fully_qualified = format!(
                "{}.{}",
                unresolved_binding.module.as_string(),
                unresolved_binding.function
            );
            let result = render_prompt(
                &fully_qualified,
                &module_ir,
                "",
                "",
                "",
                None,
                None,
                &target,
            )
            .and_then(|prompt| {
                run_agent(
                    agent,
                    executable.clone(),
                    &temporary.workspace,
                    &temporary.scratch,
                    &target,
                    prompt,
                    900,
                )
            })
            .and_then(|candidate| {
                validate_candidate(
                    &project,
                    &semantic,
                    &unresolved_binding.function,
                    &candidate.implementation,
                )
                .map(|_| candidate.implementation)
            });
            let _ = fs::remove_dir_all(&temporary.root);
            let bytes = match result {
                Ok(bytes) => bytes,
                Err(error) => {
                    eprintln!("error: agent generation for `{fully_qualified}` failed: {error}");
                    return 5;
                }
            };
            let mut generated_relative = PathBuf::from("_cott_impl");
            for segment in &unresolved_binding.module.segments {
                generated_relative.push(segment);
            }
            generated_relative.push(format!("{}.py", unresolved_binding.function));
            let relative_source = unresolved_binding
                .source
                .strip_prefix(&project.root)
                .expect("implementation path is project-relative")
                .to_path_buf();
            durable_sources.push((relative_source, bytes.clone()));
            bindings.push(ResolvedBinding {
                module: unresolved_binding.module,
                function: unresolved_binding.function,
                source: unresolved_binding.source,
                generated_relative,
                sha256: crate::hash::sha256_hex(&bytes),
                bytes,
            });
        }
    }
    let emission = match emit(&project, &semantic, &ir, &bindings) {
        Ok(emission) => emission,
        Err(diagnostics) => {
            print_emit_diagnostics(&project, &diagnostics);
            return 4;
        }
    };
    match publish_with_sources(&PlannedProject { project, emission }, &durable_sources) {
        Ok(()) => 0,
        Err(error) => {
            eprintln!("error: {error}");
            6
        }
    }
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
    let plan = match plan(project_argument) {
        Ok(plan) => plan,
        Err(code) => return code,
    };
    let baseline = match baseline {
        Some(path) if path.is_absolute() => path,
        Some(path) => plan.project.root.join(path),
        None => match artifact_root(&plan.project) {
            Ok(root) => root.join("generation.json"),
            Err(error) => {
                eprintln!("error: {error}");
                return 2;
            }
        },
    };
    let baseline_bytes = match fs::read(&baseline) {
        Ok(bytes) => bytes,
        Err(error) => {
            eprintln!("error: read diff baseline {}: {error}", baseline.display());
            return 2;
        }
    };
    let expected = match plan.emission.files.get(Path::new("generation.json")) {
        Some(bytes) => bytes,
        None => {
            eprintln!("error: compiler did not produce generation.json");
            return 1;
        }
    };
    if baseline_bytes == *expected {
        println!("NO CHANGE");
        0
    } else {
        println!("IMPLEMENTATION: generation output differs");
        if exit_code { 7 } else { 0 }
    }
}

fn resolve_executable(name: &str) -> Result<PathBuf, String> {
    let path =
        std::env::var_os("PATH").ok_or_else(|| format!("missing PATH while locating {name}"))?;
    for directory in std::env::split_paths(&path) {
        let candidate = directory.join(name);
        if fs::metadata(&candidate).is_ok_and(|metadata| metadata.is_file()) {
            return Ok(candidate);
        }
    }
    Err(format!("{name} executable was not found on PATH"))
}

fn print_binding_diagnostics(
    project: &Project,
    diagnostics: Vec<crate::binding::BindingDiagnostic>,
) {
    for diagnostic in diagnostics {
        eprintln!(
            "error: {}: {}",
            display_path(&project.root, &diagnostic.path),
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
    let project = match load_project(&root) {
        Ok(project) => project,
        Err(error) => {
            eprintln!("error: {error}");
            return 2;
        }
    };
    if let Some(selected) = selected {
        let selected = project.root.join(selected);
        let valid = selected
            .extension()
            .is_some_and(|extension| extension == "cott")
            && selected.starts_with(&project.source_dir)
            && fs::symlink_metadata(&selected)
                .is_ok_and(|metadata| metadata.is_file() && !metadata.file_type().is_symlink());
        if !valid {
            eprintln!("error: check source must be a regular .cott file beneath project.source");
            return 2;
        }
    }
    let sources = match discover_sources(&project) {
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
    match lower(&project.source_dir, parsed) {
        Ok(_) => 0,
        Err(diagnostics) => {
            print_project_diagnostics(&diagnostics);
            3
        }
    }
}
fn init_project(path: PathBuf, name: Option<String>, no_sync: bool) -> i32 {
    let target = if path.is_absolute() {
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
    let project_name = name.or_else(|| {
        target
            .file_name()
            .and_then(|name| name.to_str())
            .map(ToOwned::to_owned)
    });
    let Some(project_name) = project_name.filter(|name| valid_project_name(name)) else {
        eprintln!("error: init project name must be lowercase kebab-case");
        return 2;
    };
    if target.exists() {
        eprintln!("error: init target already exists: {}", target.display());
        return 2;
    }
    let uv = match resolve_executable("uv") {
        Ok(uv) => uv,
        Err(error) => {
            eprintln!("error: {error}");
            return 2;
        }
    };
    let version = match ProcessCommand::new(&uv).arg("--version").output() {
        Ok(output) => String::from_utf8_lossy(&output.stdout).trim().to_owned(),
        Err(error) => {
            eprintln!("error: probe uv: {error}");
            return 2;
        }
    };
    if version != "uv 0.12.3" {
        eprintln!("error: cott 0.1 requires uv 0.12.3, found `{version}`");
        return 2;
    }
    let module = project_name.replace('-', "_");
    let result = (|| -> Result<(), std::io::Error> {
        fs::create_dir_all(target.join("src").join(&module))?;
        fs::create_dir_all(target.join("python"))?;
        fs::write(
            target.join("cott.toml"),
            format!(
                "[project]\nname = \"{project_name}\"\nversion = \"0.1.0\"\nsource = \"src\"\n\n[target.python]\nsource = \"python\"\ngenerated = \"generated/python\"\nstubs = \"generated/stubs\"\ninterpreter = \".venv/bin/python\"\ntype_checker = \".venv/bin/basedpyright\"\nruntime_validation = \"boundary\"\n"
            ),
        )?;
        fs::write(
            target.join("src").join(&module).join("main.cott"),
            format!("module {module}.main\n"),
        )?;
        fs::write(target.join("python/.python-version"), "3.14\n")?;
        fs::write(
            target.join("python/pyproject.toml"),
            format!(
                "[project]\nname = \"{project_name}\"\nversion = \"0.1.0\"\nrequires-python = \">=3.14,<3.15\"\ndependencies = []\n\n[dependency-groups]\ndev = [\"basedpyright==1.39.9\"]\n"
            ),
        )
    })();
    if let Err(error) = result {
        let _ = fs::remove_dir_all(&target);
        eprintln!("error: create init scaffold: {error}");
        return 6;
    }
    if no_sync {
        println!(
            "uv --no-config sync --directory {}/python --frozen --managed-python",
            target.display()
        );
    }
    0
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
    let project = match load_project(&root) {
        Ok(project) => project,
        Err(error) => {
            eprintln!("error: {error}");
            return 2;
        }
    };
    let session = match ProjectSession::acquire(&project.root) {
        Ok(session) => session,
        Err(error) => {
            eprintln!("error: {error}");
            return 6;
        }
    };
    let sources = match discover_sources(&project) {
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
    let mut changes = ChangeSet::default();
    let mut paths = Vec::new();
    let mut differs = false;
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
        let relative = project
            .source_dir
            .strip_prefix(&project.root)
            .expect("project source is rooted")
            .join(&source.path);
        let current = match fs::read(project.root.join(&relative)) {
            Ok(bytes) => bytes,
            Err(error) => {
                eprintln!("error: read source {}: {error}", relative.display());
                return 2;
            }
        };
        if current != bytes {
            differs = true;
            if !check {
                paths.push(relative.clone());
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
    let snapshot = match InputSnapshot::capture(&project.root, paths) {
        Ok(snapshot) => snapshot,
        Err(error) => {
            eprintln!("error: {error}");
            return 6;
        }
    };
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

fn print_emit_diagnostics(project: &Project, diagnostics: &[EmitDiagnostic]) {
    for diagnostic in diagnostics {
        eprintln!(
            "error: {}: {}",
            display_path(&project.root, &diagnostic.path),
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

fn artifact_root(project: &Project) -> Result<PathBuf, String> {
    if project
        .generated_dir
        .file_name()
        .and_then(|name| name.to_str())
        != Some("python")
    {
        return Err("target.python.generated must end in `python`".to_owned());
    }
    let Some(root) = project.generated_dir.parent() else {
        return Err("target.python.generated has no artifact root".to_owned());
    };
    if root == project.root {
        return Err("target.python.generated must be beneath an artifact root".to_owned());
    }
    Ok(root.to_path_buf())
}

fn generated_path(project: &Project) -> String {
    display_path(&project.root, &project.generated_dir)
}

fn publish(plan: &PlannedProject) -> Result<(), String> {
    publish_with_sources(plan, &[])
}

fn publish_with_sources(
    plan: &PlannedProject,
    sources: &[(PathBuf, Vec<u8>)],
) -> Result<(), String> {
    let artifact_root = artifact_root(&plan.project)?;
    if let Ok(metadata) = fs::symlink_metadata(&artifact_root) {
        if metadata.file_type().is_symlink() || !metadata.is_dir() {
            return Err(format!(
                "artifact root is not a regular directory: {}",
                artifact_root.display()
            ));
        }
    }
    let session = ProjectSession::acquire(&plan.project.root).map_err(|error| error.to_string())?;
    let relative_root = artifact_root
        .strip_prefix(&plan.project.root)
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
    let snapshot = InputSnapshot::capture(&plan.project.root, paths.into_keys())
        .map_err(|error| error.to_string())?;
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
        let current = fs::read(plan.project.root.join(path)).ok();
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
    let artifact_root = artifact_root(&plan.project).map_err(|message| vec![message])?;
    let actual = collect_tree(&artifact_root).map_err(|message| vec![message])?;
    let mut mismatches = Vec::new();
    for (path, expected) in &plan.emission.files {
        match actual.get(path) {
            Some(actual) if actual == expected => {}
            Some(_) => mismatches.push(format!("managed artifact differs: {}", path.display())),
            None => mismatches.push(format!("missing managed artifact: {}", path.display())),
        }
    }
    for path in actual.keys() {
        if !plan.emission.files.contains_key(path) {
            mismatches.push(format!("unexpected managed artifact: {}", path.display()));
        }
    }
    if mismatches.is_empty() {
        Ok(())
    } else {
        Err(mismatches)
    }
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
    entries.sort_by_key(|entry| entry.file_name());
    for entry in entries {
        let path = entry.path();
        let metadata = fs::symlink_metadata(&path)
            .map_err(|error| format!("failed to inspect artifact {}: {error}", path.display()))?;
        if metadata.file_type().is_symlink() {
            return Err(format!(
                "artifact must not be a symlink: {}",
                path.display()
            ));
        }
        if metadata.is_dir() {
            if entry.file_name() == "__pycache__" {
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
    for entry in entries {
        let entry = entry.map_err(|error| {
            format!(
                "failed to read Python bytecode cache {}: {error}",
                directory.display()
            )
        })?;
        let path = entry.path();
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
