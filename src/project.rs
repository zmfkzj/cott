use std::ffi::OsStr;
use std::fmt;
use std::fs;
use std::io;
#[cfg(unix)]
use std::os::unix::fs::MetadataExt;
use std::path::{Component, Path, PathBuf};

/// Trusted filesystem paths derived from the normative project configuration.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ProjectPaths {
    pub root: PathBuf,
    pub manifest: PathBuf,
    pub source_dir: PathBuf,
    pub python_source_dir: PathBuf,
    pub generated_dir: PathBuf,
    pub stubs_dir: PathBuf,
    pub lockfile: Option<PathBuf>,
}

/// A UTF-8 Python source safely discovered beneath a project-owned tree.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PythonSourceFile {
    /// Lexical path relative to the scanned tree.
    pub path: PathBuf,
    pub disk_path: PathBuf,
    pub source: String,
}
/// An error loading a project manifest or discovering its source files.
#[derive(Debug)]
pub enum ProjectError {
    Io {
        operation: &'static str,
        path: PathBuf,
        source: io::Error,
    },
    InvalidManifest {
        path: PathBuf,
        message: String,
    },
    InvalidPath {
        field: &'static str,
        path: String,
        message: &'static str,
    },
    Symlink {
        path: PathBuf,
    },
    InvalidProject {
        message: &'static str,
    },
    NoSources {
        path: PathBuf,
    },
}

impl fmt::Display for ProjectError {
    fn fmt(&self, f: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::Io {
                operation,
                path,
                source,
            } => {
                write!(f, "failed to {operation} {}: {source}", path.display())
            }
            Self::InvalidManifest { path, message } => {
                write!(f, "invalid manifest {}: {message}", path.display())
            }
            Self::InvalidPath {
                field,
                path,
                message,
            } => {
                write!(f, "invalid {field} path '{path}': {message}")
            }
            Self::Symlink { path } => write!(f, "symlink is not allowed: {}", path.display()),
            Self::InvalidProject { message } => write!(f, "invalid project: {message}"),
            Self::NoSources { path } => {
                write!(f, "no .cott source files found under {}", path.display())
            }
        }
    }
}

impl std::error::Error for ProjectError {
    fn source(&self) -> Option<&(dyn std::error::Error + 'static)> {
        match self {
            Self::Io { source, .. } => Some(source),
            _ => None,
        }
    }
}

/// Loads the normative manifest and derives its trusted filesystem paths.
pub fn load_config_with_paths(
    root: &Path,
) -> Result<(crate::manifest::ProjectConfig, ProjectPaths), ProjectError> {
    let (root, manifest, config) = read_config(root)?;
    let paths = derive_project_paths(&root, &manifest, &config)?;
    Ok((config, paths))
}

/// Loads the normative v0.1 manifest without deriving filesystem paths.
pub fn load_config(root: &Path) -> Result<crate::manifest::ProjectConfig, ProjectError> {
    Ok(read_config(root)?.2)
}

fn read_config(
    root: &Path,
) -> Result<(PathBuf, PathBuf, crate::manifest::ProjectConfig), ProjectError> {
    let root = canonical_project_root(root)?;
    let manifest = root.join("cott.toml");
    ensure_no_symlinks(&manifest)?;
    let manifest_meta = fs::symlink_metadata(&manifest).map_err(|source| ProjectError::Io {
        operation: "stat manifest",
        path: manifest.clone(),
        source,
    })?;
    if !manifest_meta.is_file() || manifest_meta.nlink() != 1 {
        return Err(ProjectError::InvalidManifest {
            path: manifest.clone(),
            message: "manifest is not a regular file".to_owned(),
        });
    }
    let bytes = fs::read_to_string(&manifest).map_err(|source| ProjectError::Io {
        operation: "read manifest",
        path: manifest.clone(),
        source,
    })?;
    let config = crate::manifest::ProjectConfig::parse(&manifest, &bytes).map_err(|error| {
        ProjectError::InvalidManifest {
            path: manifest.clone(),
            message: error.message,
        }
    })?;
    Ok((root, manifest, config))
}

fn canonical_project_root(root: &Path) -> Result<PathBuf, ProjectError> {
    if root.as_os_str().is_empty() {
        return Err(ProjectError::InvalidProject {
            message: "project root is empty",
        });
    }
    let metadata = fs::symlink_metadata(root).map_err(|source| ProjectError::Io {
        operation: "stat project root",
        path: root.to_path_buf(),
        source,
    })?;
    if metadata.file_type().is_symlink() {
        return Err(ProjectError::Symlink {
            path: root.to_path_buf(),
        });
    }
    if !metadata.is_dir() {
        return Err(ProjectError::InvalidProject {
            message: "project root is not a directory",
        });
    }
    fs::canonicalize(root).map_err(|source| ProjectError::Io {
        operation: "canonicalize project root",
        path: root.to_path_buf(),
        source,
    })
}

fn derive_project_paths(
    root: &Path,
    manifest: &Path,
    config: &crate::manifest::ProjectConfig,
) -> Result<ProjectPaths, ProjectError> {
    let source =
        crate::manifest::normalized_relative_path(&config.project.source).map_err(|message| {
            ProjectError::InvalidPath {
                field: "project.source",
                path: config.project.source.clone(),
                message,
            }
        })?;
    let python_source =
        crate::manifest::normalized_relative_path(&config.python.source).map_err(|message| {
            ProjectError::InvalidPath {
                field: "target.python.source",
                path: config.python.source.clone(),
                message,
            }
        })?;
    let generated =
        crate::manifest::normalized_relative_path(&config.python.generated).map_err(|message| {
            ProjectError::InvalidPath {
                field: "target.python.generated",
                path: config.python.generated.clone(),
                message,
            }
        })?;
    let stubs =
        crate::manifest::normalized_relative_path(&config.python.stubs).map_err(|message| {
            ProjectError::InvalidPath {
                field: "target.python.stubs",
                path: config.python.stubs.clone(),
                message,
            }
        })?;
    let lockfile = config
        .python
        .lockfile
        .as_deref()
        .map(|value| {
            crate::manifest::normalized_relative_path(value)
                .map(|path| root.join(path))
                .map_err(|message| ProjectError::InvalidPath {
                    field: "target.python.lockfile",
                    path: value.to_owned(),
                    message,
                })
        })
        .transpose()?;

    let source_dir = root.join(source);
    let python_source_dir = root.join(python_source);
    let generated_dir = root.join(generated);
    let stubs_dir = root.join(stubs);

    ensure_no_symlinks(&source_dir)?;
    ensure_target_metadata(&python_source_dir.join("pyproject.toml"), config)?;
    ensure_directory_if_present(&generated_dir, "generated directory")?;
    ensure_directory_if_present(&stubs_dir, "stubs directory")?;
    if let Some(lockfile) = &lockfile {
        ensure_regular_input(lockfile, "lockfile")?;
    }
    if let Some(rules) = &config.generator.rules {
        ensure_regular_input(&root.join(rules), "generator rules")?;
    }

    let source_meta = fs::symlink_metadata(&source_dir).map_err(|source| ProjectError::Io {
        operation: "stat source directory",
        path: source_dir.clone(),
        source,
    })?;
    if !source_meta.is_dir() {
        return Err(ProjectError::InvalidProject {
            message: "source path is not a directory",
        });
    }

    Ok(ProjectPaths {
        root: root.to_path_buf(),
        manifest: manifest.to_path_buf(),
        source_dir,
        python_source_dir,
        generated_dir,
        stubs_dir,
        lockfile,
    })
}

/// Reads all regular `.cott` files under normative project paths.
pub fn discover_sources_from_paths(
    project: &ProjectPaths,
) -> Result<Vec<crate::compiler::SourceFile>, ProjectError> {
    discover_sources_at(&project.root, &project.source_dir)
}

fn discover_sources_at(
    root: &Path,
    source_dir: &Path,
) -> Result<Vec<crate::compiler::SourceFile>, ProjectError> {
    if !root.is_absolute() || !source_dir.is_absolute() {
        return Err(ProjectError::InvalidProject {
            message: "project paths must be absolute",
        });
    }
    ensure_no_symlinks(root)?;
    ensure_no_symlinks(source_dir)?;
    let source_meta = fs::symlink_metadata(source_dir).map_err(|source| ProjectError::Io {
        operation: "stat source directory",
        path: source_dir.to_path_buf(),
        source,
    })?;
    if !source_meta.is_dir() {
        return Err(ProjectError::InvalidProject {
            message: "source path is not a directory",
        });
    }
    let mut files = Vec::new();
    collect_sources(source_dir, source_dir, &mut files)?;
    files.sort_by(|a, b| a.0.cmp(&b.0));
    if files.is_empty() {
        return Err(ProjectError::NoSources {
            path: source_dir.to_path_buf(),
        });
    }
    files
        .into_iter()
        .map(|(path, disk_path)| {
            let text = fs::read_to_string(&disk_path).map_err(|source| ProjectError::Io {
                operation: "read source",
                path: disk_path,
                source,
            })?;
            Ok(crate::compiler::SourceFile::new(path, text))
        })
        .collect()
}
/// Reads every Python source in a project-owned tree after rejecting unsafe
/// links and package metadata. Returned paths are lexical and stable.
pub fn discover_python_sources(root: &Path) -> Result<Vec<PythonSourceFile>, ProjectError> {
    ensure_no_symlinks(root)?;
    let metadata = fs::symlink_metadata(root).map_err(|source| ProjectError::Io {
        operation: "stat Python source directory",
        path: root.to_path_buf(),
        source,
    })?;
    if !metadata.is_dir() {
        return Err(ProjectError::InvalidProject {
            message: "Python source path is not a directory",
        });
    }

    let mut files = Vec::new();
    collect_python_sources(root, root, &mut files)?;
    files.sort_by(|left, right| left.path.cmp(&right.path));
    Ok(files)
}

fn collect_python_sources(
    root: &Path,
    directory: &Path,
    files: &mut Vec<PythonSourceFile>,
) -> Result<(), ProjectError> {
    let mut entries = fs::read_dir(directory)
        .map_err(|source| ProjectError::Io {
            operation: "read Python source directory",
            path: directory.to_path_buf(),
            source,
        })?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|source| ProjectError::Io {
            operation: "read Python source directory entry",
            path: directory.to_path_buf(),
            source,
        })?;
    entries.sort_by_key(|entry| entry.file_name());

    for entry in entries {
        let path = entry.path();
        if matches!(entry.file_name().to_str(), Some(".venv" | "__pycache__"))
            || path.extension() == Some(OsStr::new("pyc"))
        {
            continue;
        }
        let metadata = fs::symlink_metadata(&path).map_err(|source| ProjectError::Io {
            operation: "stat Python source entry",
            path: path.clone(),
            source,
        })?;
        if metadata.file_type().is_symlink() {
            return Err(ProjectError::Symlink { path });
        }
        if metadata.is_dir() {
            collect_python_sources(root, &path, files)?;
            continue;
        }

        let package_metadata = matches!(
            path.file_name().and_then(OsStr::to_str),
            Some("pyproject.toml" | "py.typed")
        );
        let python = path.extension() == Some(OsStr::new("py"));
        if !python && !package_metadata {
            continue;
        }
        #[cfg(unix)]
        let single_link = metadata.nlink() == 1;
        #[cfg(not(unix))]
        let single_link = true;
        if !metadata.is_file() || !single_link {
            return Err(ProjectError::InvalidProject {
                message: "Python tree files must be regular single-link files",
            });
        }
        if !python {
            continue;
        }
        let bytes = fs::read(&path).map_err(|source| ProjectError::Io {
            operation: "read Python source",
            path: path.clone(),
            source,
        })?;
        let source = String::from_utf8(bytes).map_err(|_| ProjectError::InvalidProject {
            message: "Python source is not UTF-8",
        })?;
        let rechecked = fs::symlink_metadata(&path).map_err(|source| ProjectError::Io {
            operation: "re-stat Python source",
            path: path.clone(),
            source,
        })?;
        #[cfg(unix)]
        let stable =
            rechecked.is_file() && !rechecked.file_type().is_symlink() && rechecked.nlink() == 1;
        #[cfg(not(unix))]
        let stable = rechecked.is_file() && !rechecked.file_type().is_symlink();
        if !stable {
            return Err(ProjectError::InvalidProject {
                message: "Python source changed while being read",
            });
        }
        let relative = path
            .strip_prefix(root)
            .map_err(|_| ProjectError::InvalidProject {
                message: "Python source path is outside scanned tree",
            })?
            .to_path_buf();
        files.push(PythonSourceFile {
            path: relative,
            disk_path: path,
            source,
        });
    }
    Ok(())
}

fn collect_sources(
    root: &Path,
    directory: &Path,
    files: &mut Vec<(PathBuf, PathBuf)>,
) -> Result<(), ProjectError> {
    let entries = fs::read_dir(directory).map_err(|source| ProjectError::Io {
        operation: "read source directory",
        path: directory.to_path_buf(),
        source,
    })?;
    for entry in entries {
        let entry = entry.map_err(|source| ProjectError::Io {
            operation: "read source directory entry",
            path: directory.to_path_buf(),
            source,
        })?;
        let path = entry.path();
        let metadata = fs::symlink_metadata(&path).map_err(|source| ProjectError::Io {
            operation: "stat source entry",
            path: path.clone(),
            source,
        })?;
        if metadata.file_type().is_symlink() {
            return Err(ProjectError::Symlink { path });
        } else if metadata.is_dir() {
            collect_sources(root, &path, files)?;
        } else if metadata.is_file() && path.extension() == Some(OsStr::new("cott")) {
            if metadata.nlink() != 1 {
                return Err(ProjectError::InvalidProject {
                    message: "source files must be regular single-link files",
                });
            }
            let relative = path
                .strip_prefix(root)
                .map_err(|_| ProjectError::InvalidProject {
                    message: "source path is outside project root",
                })?
                .to_path_buf();
            files.push((relative, path));
        }
    }
    Ok(())
}

fn ensure_no_symlinks(path: &Path) -> Result<(), ProjectError> {
    let mut current = PathBuf::new();
    for component in path.components() {
        match component {
            Component::Prefix(prefix) => current.push(prefix.as_os_str()),
            Component::RootDir => current.push(Path::new(std::path::MAIN_SEPARATOR_STR)),
            Component::CurDir => {}
            Component::ParentDir => current.push(".."),
            Component::Normal(part) => current.push(part),
        }
        match fs::symlink_metadata(&current) {
            Ok(metadata) if metadata.file_type().is_symlink() => {
                return Err(ProjectError::Symlink { path: current });
            }
            Ok(_) => {}
            Err(error) if error.kind() == io::ErrorKind::NotFound => return Ok(()),
            Err(source) => {
                return Err(ProjectError::Io {
                    operation: "stat project path",
                    path: current,
                    source,
                });
            }
        }
    }
    Ok(())
}

fn ensure_directory_if_present(path: &Path, label: &'static str) -> Result<(), ProjectError> {
    ensure_no_symlinks(path)?;
    match fs::symlink_metadata(path) {
        Ok(metadata) if metadata.is_dir() => Ok(()),
        Ok(_) => Err(ProjectError::InvalidProject { message: label }),
        Err(error) if error.kind() == io::ErrorKind::NotFound => Ok(()),
        Err(source) => Err(ProjectError::Io {
            operation: "stat project directory",
            path: path.to_path_buf(),
            source,
        }),
    }
}

fn ensure_regular_input(path: &Path, label: &'static str) -> Result<(), ProjectError> {
    ensure_no_symlinks(path)?;
    let metadata = fs::symlink_metadata(path).map_err(|source| ProjectError::Io {
        operation: "stat project input",
        path: path.to_path_buf(),
        source,
    })?;
    if !metadata.is_file() || metadata.nlink() != 1 {
        return Err(ProjectError::InvalidProject { message: label });
    }
    Ok(())
}
fn ensure_target_metadata(
    path: &Path,
    config: &crate::manifest::ProjectConfig,
) -> Result<(), ProjectError> {
    ensure_no_symlinks(path)?;
    let metadata = fs::symlink_metadata(path).map_err(|source| ProjectError::Io {
        operation: "stat target project metadata",
        path: path.to_path_buf(),
        source,
    })?;
    #[cfg(unix)]
    let single_link = metadata.nlink() == 1;
    #[cfg(not(unix))]
    let single_link = true;
    if !metadata.is_file() || !single_link {
        return Err(ProjectError::InvalidManifest {
            path: path.to_path_buf(),
            message: "target project metadata must be a regular single-link file".to_owned(),
        });
    }
    let bytes = fs::read(path).map_err(|source| ProjectError::Io {
        operation: "read target project metadata",
        path: path.to_path_buf(),
        source,
    })?;
    let text = std::str::from_utf8(&bytes).map_err(|_| ProjectError::InvalidManifest {
        path: path.to_path_buf(),
        message: "target project metadata is not UTF-8".to_owned(),
    })?;
    let value: toml::Value =
        toml::from_str(text).map_err(|error| ProjectError::InvalidManifest {
            path: path.to_path_buf(),
            message: error.to_string(),
        })?;
    let project = value
        .get("project")
        .and_then(toml::Value::as_table)
        .ok_or_else(|| ProjectError::InvalidManifest {
            path: path.to_path_buf(),
            message: "target project metadata has no [project] table".to_owned(),
        })?;
    let string = |field: &str| {
        project
            .get(field)
            .and_then(toml::Value::as_str)
            .ok_or_else(|| ProjectError::InvalidManifest {
                path: path.to_path_buf(),
                message: format!("target project metadata project.{field} must be a string"),
            })
    };
    let target_name = string("name")?;
    if !valid_distribution_name(target_name)
        || normalize_distribution_name(target_name) != config.project.name
    {
        return Err(ProjectError::InvalidManifest {
            path: path.to_path_buf(),
            message: "target project name does not match cott project name".to_owned(),
        });
    }
    if string("version")? != config.project.version {
        return Err(ProjectError::InvalidManifest {
            path: path.to_path_buf(),
            message: "target project version does not match cott project version".to_owned(),
        });
    }
    if !requires_python_allows_314(string("requires-python")?) {
        return Err(ProjectError::InvalidManifest {
            path: path.to_path_buf(),
            message: "target project requires-python is not compatible with CPython 3.14.6"
                .to_owned(),
        });
    }
    if project.get("dynamic").is_some_and(|dynamic| {
        dynamic.as_array().is_some_and(|fields| {
            fields.iter().any(|field| {
                field
                    .as_str()
                    .is_some_and(|field| matches!(field, "dependencies" | "requires-python"))
            })
        })
    }) {
        return Err(ProjectError::InvalidManifest {
            path: path.to_path_buf(),
            message: "target dependencies and requires-python must not be dynamic".to_owned(),
        });
    }
    let dependencies = project
        .get("dependencies")
        .and_then(toml::Value::as_array)
        .ok_or_else(|| ProjectError::InvalidManifest {
            path: path.to_path_buf(),
            message: "target project dependencies must be an array".to_owned(),
        })?;
    if dependencies.iter().any(|dependency| !dependency.is_str()) {
        return Err(ProjectError::InvalidManifest {
            path: path.to_path_buf(),
            message: "target project dependencies must contain strings".to_owned(),
        });
    }
    if !dependencies.is_empty() && config.python.lockfile.is_none() {
        return Err(ProjectError::InvalidManifest {
            path: path.to_path_buf(),
            message: "target project dependencies require target.python.lockfile".to_owned(),
        });
    }
    Ok(())
}

fn normalize_distribution_name(value: &str) -> String {
    let mut normalized = String::new();
    for character in value.chars() {
        if character.is_ascii_alphanumeric() {
            normalized.push(character.to_ascii_lowercase());
        } else if matches!(character, '-' | '_' | '.') && !normalized.ends_with('-') {
            normalized.push('-');
        }
    }
    normalized.trim_matches('-').to_owned()
}

fn valid_distribution_name(value: &str) -> bool {
    value
        .bytes()
        .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'-' | b'_' | b'.'))
        && value
            .as_bytes()
            .first()
            .is_some_and(u8::is_ascii_alphanumeric)
        && value
            .as_bytes()
            .last()
            .is_some_and(u8::is_ascii_alphanumeric)
}

fn requires_python_allows_314(specifier: &str) -> bool {
    let target = [3_u64, 14, 6];
    let mut saw_clause = false;
    for clause in specifier.split(',').map(str::trim) {
        if clause.is_empty() {
            return false;
        }
        saw_clause = true;
        let Some((operator, version)) = ["==", "!=", ">=", "<=", "~=", ">", "<"]
            .into_iter()
            .find_map(|operator| clause.strip_prefix(operator).map(|value| (operator, value)))
        else {
            return false;
        };
        if version.ends_with(".*") {
            let prefix = &version[..version.len() - 2];
            let parts = prefix
                .split('.')
                .map(str::parse::<u64>)
                .collect::<Result<Vec<_>, _>>();
            let Ok(parts) = parts else {
                return false;
            };
            let matches = parts
                .iter()
                .enumerate()
                .all(|(index, value)| target.get(index).is_some_and(|target| target == value));
            if (operator == "==" && !matches) || (operator == "!=" && matches) {
                return false;
            }
            if !matches!(operator, "==" | "!=") {
                return false;
            }
            continue;
        }
        let parts = version
            .split('.')
            .map(str::parse::<u64>)
            .collect::<Result<Vec<_>, _>>();
        let Ok(parts) = parts else {
            return false;
        };
        if parts.is_empty() || parts.len() > 3 {
            return false;
        }
        let mut compared = [0_u64; 3];
        compared[..parts.len()].copy_from_slice(&parts);
        let matches = match operator {
            "==" => target == compared,
            "!=" => target != compared,
            ">=" => target >= compared,
            "<=" => target <= compared,
            ">" => target > compared,
            "<" => target < compared,
            "~=" => {
                if target < compared {
                    false
                } else if parts.len() <= 2 {
                    target[0] == compared[0]
                } else {
                    target[..2] == compared[..2]
                }
            }
            _ => false,
        };
        if !matches {
            return false;
        }
    }
    saw_clause
}
