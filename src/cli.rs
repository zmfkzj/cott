use std::collections::BTreeMap;
use std::ffi::OsString;
use std::fs;
use std::io;
use std::path::{Component, Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

use crate::binding::resolve_bindings;
use crate::compiler::{ProjectDiagnostic, parse_project};
use crate::ir::render;
use crate::project::{Project, discover_sources, load_project};
use crate::python_emit::{Emission, EmitDiagnostic, emit};
use crate::semantic::analyze_project;

const USAGE: &str =
    "Usage:\n  cott emit python [--project <dir>]\n  cott verify [--project <dir>]\n";
static STAGING_COUNTER: AtomicU64 = AtomicU64::new(0);

/// Runs the deliberately small, fully implemented command surface.
pub fn run(arguments: impl IntoIterator<Item = OsString>) -> i32 {
    let mut arguments = arguments.into_iter();
    let _program = arguments.next();
    let arguments: Vec<OsString> = arguments.collect();

    match parse_command(&arguments) {
        Ok(Command::Help) => {
            print!("{USAGE}");
            0
        }
        Ok(Command::Emit { project }) => match plan(project) {
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
        Ok(Command::Verify { project }) => match plan(project) {
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

enum Command {
    Emit { project: Option<PathBuf> },
    Help,
    Verify { project: Option<PathBuf> },
}

fn parse_command(arguments: &[OsString]) -> Result<Command, &'static str> {
    if arguments.len() == 1 && arguments[0] == "--help" {
        return Ok(Command::Help);
    }
    let Some(command) = arguments.first().and_then(|value| value.to_str()) else {
        return Err("expected a command");
    };
    match command {
        "emit" => {
            if arguments.get(1).and_then(|value| value.to_str()) != Some("python") {
                return Err("expected `emit python`");
            }
            if arguments.get(2).and_then(|value| value.to_str()) == Some("--help")
                && arguments.len() == 3
            {
                return Ok(Command::Help);
            }
            Ok(Command::Emit {
                project: parse_project_option(&arguments[2..])?,
            })
        }
        "verify" => {
            if arguments.get(1).and_then(|value| value.to_str()) == Some("--help")
                && arguments.len() == 2
            {
                return Ok(Command::Help);
            }
            Ok(Command::Verify {
                project: parse_project_option(&arguments[1..])?,
            })
        }
        _ => Err("unsupported command"),
    }
}

fn parse_project_option(arguments: &[OsString]) -> Result<Option<PathBuf>, &'static str> {
    if arguments.is_empty() {
        return Ok(None);
    }
    if arguments.len() != 2 || arguments[0] != "--project" {
        return Err("expected at most one `--project <dir>` option");
    }
    if arguments[1].is_empty() {
        return Err("`--project` requires a directory");
    }
    Ok(Some(PathBuf::from(arguments[1].clone())))
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
    let semantic = match analyze_project(&project.source_dir, parsed) {
        Ok(semantic) => semantic,
        Err(diagnostics) => {
            print_project_diagnostics(&diagnostics);
            return Err(3);
        }
    };
    let ir = render(&semantic);
    let bindings = match resolve_bindings(&project, &semantic) {
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
    let emission = match emit(&project, &semantic, &ir, &bindings) {
        Ok(emission) => emission,
        Err(diagnostics) => {
            print_emit_diagnostics(&project, &diagnostics);
            return Err(4);
        }
    };
    Ok(PlannedProject { project, emission })
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
    let artifact_root = artifact_root(&plan.project)?;
    if let Ok(metadata) = fs::symlink_metadata(&artifact_root) {
        if metadata.file_type().is_symlink() {
            return Err(format!(
                "artifact root must not be a symlink: {}",
                artifact_root.display()
            ));
        }
        if !metadata.is_dir() {
            return Err(format!(
                "artifact root is not a directory: {}",
                artifact_root.display()
            ));
        }
    }

    let staging = create_staging_dir(&artifact_root)?;
    if let Err(error) = write_tree(&staging, &plan.emission.files) {
        let _ = fs::remove_dir_all(&staging);
        return Err(error);
    }
    replace_tree(&artifact_root, &staging)
}

fn create_staging_dir(artifact_root: &Path) -> Result<PathBuf, String> {
    let parent = artifact_root
        .parent()
        .ok_or_else(|| "artifact root has no parent directory".to_owned())?;
    let name = artifact_root
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| "artifact root has an invalid name".to_owned())?;
    for _ in 0..128 {
        let counter = STAGING_COUNTER.fetch_add(1, Ordering::Relaxed);
        let path = parent.join(format!(
            ".{name}.cott-stage-{}-{counter}",
            std::process::id()
        ));
        match fs::create_dir(&path) {
            Ok(()) => return Ok(path),
            Err(error) if error.kind() == io::ErrorKind::AlreadyExists => continue,
            Err(error) => {
                return Err(format!(
                    "failed to create staging directory {}: {error}",
                    path.display()
                ));
            }
        }
    }
    Err("failed to allocate a unique staging directory".to_owned())
}

fn write_tree(root: &Path, files: &BTreeMap<PathBuf, Vec<u8>>) -> Result<(), String> {
    for (relative, bytes) in files {
        if !safe_relative_path(relative) {
            return Err(format!(
                "emitter produced an unsafe output path: {}",
                relative.display()
            ));
        }
        let path = root.join(relative);
        let parent = path
            .parent()
            .ok_or_else(|| format!("output file has no parent: {}", path.display()))?;
        fs::create_dir_all(parent).map_err(|error| {
            format!(
                "failed to create output directory {}: {error}",
                parent.display()
            )
        })?;
        fs::write(&path, bytes)
            .map_err(|error| format!("failed to write output file {}: {error}", path.display()))?;
    }
    Ok(())
}

fn safe_relative_path(path: &Path) -> bool {
    !path.as_os_str().is_empty()
        && path.is_relative()
        && path
            .components()
            .all(|component| matches!(component, Component::Normal(_)))
}

fn replace_tree(artifact_root: &Path, staging: &Path) -> Result<(), String> {
    let existing = fs::symlink_metadata(artifact_root);
    match existing {
        Ok(metadata) => {
            if metadata.file_type().is_symlink() || !metadata.is_dir() {
                let _ = fs::remove_dir_all(staging);
                return Err(format!(
                    "artifact root is not a regular directory: {}",
                    artifact_root.display()
                ));
            }
            let backup = unique_sibling(artifact_root, "backup")?;
            fs::rename(artifact_root, &backup).map_err(|error| {
                format!(
                    "failed to move existing artifacts {}: {error}",
                    artifact_root.display()
                )
            })?;
            if let Err(error) = fs::rename(staging, artifact_root) {
                let restore = fs::rename(&backup, artifact_root);
                let _ = fs::remove_dir_all(staging);
                return Err(match restore {
                    Ok(()) => format!(
                        "failed to publish staged artifacts {}: {error}; restored prior artifacts",
                        artifact_root.display()
                    ),
                    Err(restore_error) => format!(
                        "failed to publish staged artifacts {}: {error}; failed to restore prior artifacts: {restore_error}",
                        artifact_root.display()
                    ),
                });
            }
            fs::remove_dir_all(&backup).map_err(|error| {
                format!(
                    "published artifacts but failed to remove prior artifact tree {}: {error}",
                    backup.display()
                )
            })
        }
        Err(error) if error.kind() == io::ErrorKind::NotFound => fs::rename(staging, artifact_root)
            .map_err(|error| {
                format!(
                    "failed to publish artifacts {}: {error}",
                    artifact_root.display()
                )
            }),
        Err(error) => {
            let _ = fs::remove_dir_all(staging);
            Err(format!(
                "failed to inspect artifact root {}: {error}",
                artifact_root.display()
            ))
        }
    }
}

fn unique_sibling(artifact_root: &Path, kind: &str) -> Result<PathBuf, String> {
    let parent = artifact_root
        .parent()
        .ok_or_else(|| "artifact root has no parent directory".to_owned())?;
    let name = artifact_root
        .file_name()
        .and_then(|name| name.to_str())
        .ok_or_else(|| "artifact root has an invalid name".to_owned())?;
    for _ in 0..128 {
        let counter = STAGING_COUNTER.fetch_add(1, Ordering::Relaxed);
        let path = parent.join(format!(
            ".{name}.cott-{kind}-{}-{counter}",
            std::process::id()
        ));
        if !path.exists() {
            return Ok(path);
        }
    }
    Err("failed to allocate a unique artifact backup path".to_owned())
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
