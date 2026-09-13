use std::collections::{BTreeMap, BTreeSet};
use std::ffi::OsStr;
use std::path::{Component, Path, PathBuf};

use crate::binding::{PythonFileRole, audit_facade_file};
use crate::manifest::normalized_relative_path;
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
