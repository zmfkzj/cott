use std::ffi::OsStr;
use std::fmt;
use std::fs;
use std::io;
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
    if !manifest_meta.is_file() {
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
    ensure_directory_if_present(&python_source_dir, "python source directory")?;
    ensure_directory_if_present(&generated_dir, "generated directory")?;
    ensure_directory_if_present(&stubs_dir, "stubs directory")?;
    if let Some(lockfile) = &lockfile {
        ensure_no_symlinks(lockfile)?;
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
        }
        if metadata.is_dir() {
            collect_sources(root, &path, files)?;
        } else if metadata.is_file() && path.extension() == Some(OsStr::new("cott")) {
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
