use std::collections::{BTreeMap, BTreeSet};
use std::ffi::{CString, OsStr};
use std::fs::{self, File, OpenOptions};
use std::io::Read;
use std::os::unix::ffi::OsStrExt;
use std::os::unix::fs::{MetadataExt, OpenOptionsExt};
use std::path::{Component, Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use crate::binding::{PythonFileRole, audit_facade_file};
use crate::dart::provenance::DartGenerationRecord;
use crate::kotlin::provenance::KotlinGenerationRecord;
use crate::manifest::{TargetLanguage, normalized_relative_path};
use crate::project::{ProjectPaths, discover_python_sources};
use crate::provenance::GenerationRecord;

pub(crate) fn adapter_files(
    paths: &ProjectPaths,
    record: &GenerationRecord,
) -> Result<BTreeMap<PathBuf, Vec<u8>>, String> {
    let private_roots = private_implementation_roots(paths, record)?;
    let sources = discover_python_sources(&paths.python_source_dir).map_err(|error| {
        format!(
            "cannot discover runtime adapters under {}: {error}",
            paths.python_source_dir.display()
        )
    })?;

    let mut files = BTreeMap::new();
    let mut diagnostics = Vec::new();
    for source in sources {
        if excluded_adapter(&source.path, &private_roots) {
            continue;
        }

        let display = source
            .disk_path
            .strip_prefix(&paths.root)
            .unwrap_or(&source.disk_path)
            .to_path_buf();
        diagnostics.extend(
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
                }),
        );
        files.insert(
            Path::new("python").join(source.path),
            source.source.into_bytes(),
        );
    }

    diagnostics.sort();
    diagnostics.dedup();
    if diagnostics.is_empty() {
        Ok(files)
    } else {
        Err(format!(
            "runtime adapter facade audit failed:\n{}",
            diagnostics.join("\n")
        ))
    }
}

fn private_implementation_roots(
    paths: &ProjectPaths,
    record: &GenerationRecord,
) -> Result<BTreeSet<PathBuf>, String> {
    let configured_source = paths
        .python_source_dir
        .strip_prefix(&paths.root)
        .ok()
        .filter(|path| {
            !path.as_os_str().is_empty()
                && path
                    .components()
                    .all(|component| matches!(component, Component::Normal(_)))
        })
        .ok_or_else(|| {
            format!(
                "configured Python source is not project-relative: {}",
                paths.python_source_dir.display()
            )
        })?;
    let implementations = record
        .current
        .implementations
        .as_array()
        .ok_or("generation implementations must be an array")?;

    let mut roots = BTreeSet::from([PathBuf::from("_cott_impl"), PathBuf::from("cott_bindings")]);
    for (index, implementation) in implementations.iter().enumerate() {
        let source_origin = implementation
            .get("source_origin")
            .and_then(serde_json::Value::as_str)
            .ok_or_else(|| {
                format!("generation implementation at index {index} has no string source_origin")
            })?;
        let origin = normalized_relative_path(source_origin).map_err(|message| {
            format!("invalid implementation source path `{source_origin}`: {message}")
        })?;
        let relative = origin
            .strip_prefix(configured_source)
            .ok()
            .filter(|path| !path.as_os_str().is_empty())
            .ok_or_else(|| {
                format!(
                    "implementation source `{source_origin}` is outside configured Python source {}",
                    configured_source.display()
                )
            })?;
        if relative.extension() != Some(OsStr::new("py")) {
            return Err(format!(
                "implementation source `{source_origin}` is not a Python file"
            ));
        }

        let mut components = relative.components();
        let Some(Component::Normal(root)) = components.next() else {
            return Err(format!(
                "implementation source `{source_origin}` has no private package root"
            ));
        };
        roots.insert(PathBuf::from(root));
    }
    Ok(roots)
}

fn excluded_adapter(path: &Path, private_roots: &BTreeSet<PathBuf>) -> bool {
    if private_roots.iter().any(|root| path.starts_with(root)) {
        return true;
    }

    if path.parent().is_some_and(|parent| {
        parent.components().any(|component| {
            let Component::Normal(name) = component else {
                return true;
            };
            excluded_directory(name)
        })
    }) {
        return true;
    }

    path.file_name()
        .and_then(OsStr::to_str)
        .is_some_and(|name| {
            name.starts_with('.')
                || name == "conftest.py"
                || name.starts_with("test_")
                || name.ends_with("_test.py")
        })
}

fn excluded_directory(name: &OsStr) -> bool {
    name.to_str().is_some_and(|name| {
        name.starts_with('.')
            || matches!(
                name,
                "__pycache__" | "dev" | "development" | "test" | "tests"
            )
    })
}

pub(crate) struct ReplaceContext {
    pub root: PathBuf,
    pub source_dir: PathBuf,
    pub language_source_dir: PathBuf,
    pub artifact_root: PathBuf,
    pub extra_protected: Vec<PathBuf>,
    pub project_name: String,
    pub language: crate::manifest::TargetLanguage,
}

pub(crate) fn require_replaceable(context: &ReplaceContext, target: &Path) -> Result<(), String> {
    let metadata = match fs::symlink_metadata(target) {
        Ok(metadata) => metadata,
        Err(error) => {
            return Err(format!(
                "deployment output is not a replaceable Cott deployment: inspect {}: {error}",
                target.display()
            ));
        }
    };
    if metadata.file_type().is_symlink() {
        return Err(
            "deployment output is not a replaceable Cott deployment: path is a symlink".to_owned(),
        );
    }
    if metadata.is_file() {
        return Err(
            "deployment output is not a replaceable Cott deployment: path is a file".to_owned(),
        );
    }
    if !metadata.is_dir() {
        return Err(
            "deployment output is not a replaceable Cott deployment: not a regular directory"
                .to_owned(),
        );
    }
    if output_overlaps_project(context, target) {
        return Err(
            "deployment output is not a replaceable Cott deployment: overlaps project inputs or managed artifacts"
                .to_owned(),
        );
    }

    let generation = target.join("generation.json");
    let bytes = match read_regular_file(&generation)? {
        Some(bytes) => bytes,
        None => {
            return Err(
                "deployment output is not a replaceable Cott deployment: missing generation.json"
                    .to_owned(),
            );
        }
    };
    match generation_project_name(context.language, &bytes) {
        Ok(None) => Ok(()),
        Ok(Some(name)) if name == context.project_name => Ok(()),
        Ok(Some(_)) => Err(
            "deployment output is not a replaceable Cott deployment: generation.json names a different project"
                .to_owned(),
        ),
        Err(_) => Err(
            "deployment output is not a replaceable Cott deployment: generation.json is not this target's record"
                .to_owned(),
        ),
    }
}

pub(crate) fn output_overlaps_project(context: &ReplaceContext, target: &Path) -> bool {
    let identity = [
        context.root.as_path(),
        context.source_dir.as_path(),
        context.language_source_dir.as_path(),
        context.artifact_root.as_path(),
    ];
    if identity.iter().any(|path| path.starts_with(target)) {
        return true;
    }
    let nested = [
        context.source_dir.as_path(),
        context.language_source_dir.as_path(),
        context.artifact_root.as_path(),
    ];
    nested.iter().any(|path| target.starts_with(path))
        || context
            .extra_protected
            .iter()
            .any(|path| target.starts_with(path) || path.starts_with(target))
}

pub(crate) fn sibling_temp(target: &Path, kind: &str) -> Result<PathBuf, String> {
    let parent = target.parent().ok_or("deployment output has no parent")?;
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|error| error.to_string())?
        .as_nanos();
    Ok(parent.join(format!(
        ".cott-deploy-{kind}-{}-{nonce}",
        std::process::id()
    )))
}

pub(crate) fn remove_tree_if_present(path: &Path) -> Result<(), String> {
    match fs::symlink_metadata(path) {
        Ok(metadata) if metadata.is_dir() && !metadata.file_type().is_symlink() => {
            fs::remove_dir_all(path)
                .map_err(|error| format!("remove deployment temporary {}: {error}", path.display()))
        }
        Ok(_) => Err(format!(
            "refusing to remove non-directory deployment path {}",
            path.display()
        )),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(()),
        Err(error) => Err(format!(
            "inspect deployment temporary {}: {error}",
            path.display()
        )),
    }
}

pub(crate) fn publish_replace(staged: &Path, target: &Path) -> Result<(), String> {
    let parent = target.parent().ok_or("deployment output has no parent")?;
    let aside = sibling_temp(target, "aside")?;
    if let Err(error) = rename_exclusive(target, &aside) {
        let _ = remove_tree_if_present(staged);
        return Err(error);
    }
    if let Err(error) = rename_exclusive(staged, target) {
        let restored = rename_exclusive(&aside, target);
        let _ = remove_tree_if_present(staged);
        let _ = remove_tree_if_present(&aside);
        return match restored {
            Ok(()) => Err(error),
            Err(restore) => Err(format!("{error}; restore original deployment: {restore}")),
        };
    }
    if let Err(error) = fs::remove_dir_all(&aside) {
        let rollback = sibling_temp(target, "rollback")?;
        let _ = rename_exclusive(target, &rollback);
        let _ = rename_exclusive(&aside, target);
        let _ = remove_tree_if_present(&rollback);
        return Err(format!("remove replaced deployment: {error}"));
    }
    File::open(parent)
        .and_then(|directory| directory.sync_all())
        .map_err(|error| format!("sync deployment parent: {error}"))
}

fn generation_project_name(
    language: crate::manifest::TargetLanguage,
    bytes: &[u8],
) -> Result<Option<String>, String> {
    match language {
        crate::manifest::TargetLanguage::Python => {
            GenerationRecord::parse(bytes)?;
            Ok(None)
        }
        crate::manifest::TargetLanguage::Kotlin => {
            let record = crate::kotlin::provenance::KotlinGenerationRecord::parse(bytes)?;
            Ok(Some(record.current.project_name))
        }
        crate::manifest::TargetLanguage::Dart => {
            let record = crate::dart::provenance::DartGenerationRecord::parse(bytes)?;
            Ok(Some(record.current.project_name))
        }
    }
}

fn read_regular_file(path: &Path) -> Result<Option<Vec<u8>>, String> {
    let mut file = match OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_CLOEXEC | libc::O_NOFOLLOW | libc::O_NONBLOCK)
        .open(path)
    {
        Ok(file) => file,
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(None),
        Err(error) => {
            return Err(format!(
                "deployment output is not a replaceable Cott deployment: unreadable generation.json: {error}"
            ));
        }
    };
    let before = file.metadata().map_err(|error| {
        format!(
            "deployment output is not a replaceable Cott deployment: inspect generation.json: {error}"
        )
    })?;
    if !before.is_file() || before.nlink() != 1 {
        return Err(
            "deployment output is not a replaceable Cott deployment: generation.json is not a regular single-link file"
                .to_owned(),
        );
    }
    let mut bytes = Vec::new();
    file.read_to_end(&mut bytes).map_err(|error| {
        format!(
            "deployment output is not a replaceable Cott deployment: read generation.json: {error}"
        )
    })?;
    let after = file.metadata().map_err(|error| {
        format!(
            "deployment output is not a replaceable Cott deployment: re-inspect generation.json: {error}"
        )
    })?;
    let leaf = fs::symlink_metadata(path).map_err(|error| {
        format!(
            "deployment output is not a replaceable Cott deployment: re-inspect generation.json: {error}"
        )
    })?;
    if !after.is_file()
        || after.nlink() != 1
        || !leaf.is_file()
        || leaf.file_type().is_symlink()
        || leaf.nlink() != 1
        || before.dev() != after.dev()
        || before.ino() != after.ino()
        || before.len() != after.len()
        || after.dev() != leaf.dev()
        || after.ino() != leaf.ino()
    {
        return Err(
            "deployment output is not a replaceable Cott deployment: generation.json changed while being read"
                .to_owned(),
        );
    }
    Ok(Some(bytes))
}

fn rename_exclusive(source: &Path, target: &Path) -> Result<(), String> {
    let source = CString::new(source.as_os_str().as_bytes())
        .map_err(|_| "deployment path contains NUL".to_owned())?;
    let target_c = CString::new(target.as_os_str().as_bytes())
        .map_err(|_| "deployment path contains NUL".to_owned())?;
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
            Err(format!("output already exists: {}", target.display()))
        } else {
            Err(format!("atomically publish {}: {error}", target.display()))
        }
    }
}
