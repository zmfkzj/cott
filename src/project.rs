use std::ffi::OsStr;
use std::fmt;
use std::fs;
use std::io;
use std::path::{Component, Path, PathBuf};

/// A validated Cott project manifest and its compiler-owned paths.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Project {
    pub root: PathBuf,
    pub name: String,
    pub source_dir: PathBuf,
    pub generated_dir: PathBuf,
    pub implementation_dir: PathBuf,
    pub entry: String,
}
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
    Manifest {
        path: PathBuf,
        line: usize,
        message: String,
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
            Self::Manifest {
                path,
                line,
                message,
            } => {
                write!(f, "invalid manifest {}:{line}: {message}", path.display())
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

struct Manifest {
    name: String,
    source: String,
    generated: String,
    entry: String,
}

#[derive(Clone, Copy)]
enum Table {
    None,
    Project,
    Python,
}

/// Loads and validates the closed project manifest at `root/cott.toml`.
pub fn load_project(root: &Path) -> Result<Project, ProjectError> {
    if root.as_os_str().is_empty() {
        return Err(ProjectError::InvalidProject {
            message: "project root is empty",
        });
    }
    let root_meta = fs::symlink_metadata(root).map_err(|source| ProjectError::Io {
        operation: "stat project root",
        path: root.to_path_buf(),
        source,
    })?;
    if root_meta.file_type().is_symlink() {
        return Err(ProjectError::Symlink {
            path: root.to_path_buf(),
        });
    }
    if !root_meta.is_dir() {
        return Err(ProjectError::InvalidProject {
            message: "project root is not a directory",
        });
    }
    let root = fs::canonicalize(root).map_err(|source| ProjectError::Io {
        operation: "canonicalize project root",
        path: root.to_path_buf(),
        source,
    })?;

    let manifest_path = root.join("cott.toml");
    ensure_no_symlinks(&manifest_path)?;
    let manifest_meta =
        fs::symlink_metadata(&manifest_path).map_err(|source| ProjectError::Io {
            operation: "stat manifest",
            path: manifest_path.clone(),
            source,
        })?;
    if !manifest_meta.is_file() {
        return Err(ProjectError::InvalidManifest {
            path: manifest_path,
            message: "manifest is not a regular file".to_owned(),
        });
    }
    let text = fs::read_to_string(&manifest_path).map_err(|source| ProjectError::Io {
        operation: "read manifest",
        path: manifest_path.clone(),
        source,
    })?;
    let manifest = parse_manifest(&manifest_path, &text)?;

    if manifest.name.is_empty() || manifest.name.trim().is_empty() {
        return Err(ProjectError::InvalidManifest {
            path: manifest_path.clone(),
            message: "project.name must be nonempty".to_owned(),
        });
    }
    validate_entry(&manifest.entry).map_err(|message| ProjectError::InvalidManifest {
        path: manifest_path.clone(),
        message,
    })?;
    let source = normalize_path("source", &manifest.source)?;
    let generated = normalize_path("generated", &manifest.generated)?;
    if source == generated || source.starts_with(&generated) || generated.starts_with(&source) {
        return Err(ProjectError::InvalidManifest {
            path: manifest_path,
            message: "source and generated paths must not overlap".to_owned(),
        });
    }

    let source_dir = root.join(&source);
    let generated_dir = root.join(&generated);
    let implementation_dir = root.join("python").join("_cott_impl");
    ensure_no_symlinks(&source_dir)?;
    ensure_directory_if_present(&generated_dir, "generated directory")?;
    ensure_directory_if_present(&implementation_dir, "implementation directory")?;

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

    Ok(Project {
        root,
        name: manifest.name,
        source_dir,
        generated_dir,
        implementation_dir,
        entry: manifest.entry,
    })
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

/// Reads all regular `.cott` files under `project.source_dir` in source-relative lexical order.
pub fn discover_sources(
    project: &Project,
) -> Result<Vec<crate::compiler::SourceFile>, ProjectError> {
    discover_sources_at(&project.root, &project.source_dir)
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

fn normalize_path(field: &'static str, value: &str) -> Result<PathBuf, ProjectError> {
    if value.is_empty() || value.starts_with('/') || value.contains('\\') || value.contains('\0') {
        return Err(ProjectError::InvalidPath {
            field,
            path: value.to_owned(),
            message: "must be a normalized relative path",
        });
    }
    let mut normalized = PathBuf::new();
    for component in value.split('/') {
        if component.is_empty() || component == "." || component == ".." {
            return Err(ProjectError::InvalidPath {
                field,
                path: value.to_owned(),
                message: "must be a normalized relative path",
            });
        }
        normalized.push(component);
    }
    if normalized.as_os_str().is_empty() {
        return Err(ProjectError::InvalidPath {
            field,
            path: value.to_owned(),
            message: "must be a normalized relative path",
        });
    }
    Ok(normalized)
}

fn validate_entry(entry: &str) -> Result<(), String> {
    let mut segments = entry.split('.');
    let first = segments.next().unwrap_or_default();
    if first.is_empty() || !segments.clone().next().is_some() {
        return Err("target.python.entry must be module.function".to_owned());
    }
    if !entry.split('.').all(valid_identifier) {
        return Err("target.python.entry must be a dotted identifier".to_owned());
    }
    Ok(())
}

fn valid_identifier(value: &str) -> bool {
    let mut chars = value.chars();
    match chars.next() {
        Some(c) if c == '_' || c.is_ascii_alphabetic() => {}
        _ => return false,
    }
    chars.all(|c| c == '_' || c.is_ascii_alphanumeric())
}

fn parse_manifest(path: &Path, text: &str) -> Result<Manifest, ProjectError> {
    let mut table = Table::None;
    let mut project_seen = false;
    let mut python_seen = false;
    let mut name = None;
    let mut source = None;
    let mut generated = None;
    let mut entry = None;

    for (line_index, raw_line) in text.lines().enumerate() {
        let line_number = line_index + 1;
        let line = strip_comment(raw_line).map_err(|message| ProjectError::Manifest {
            path: path.to_path_buf(),
            line: line_number,
            message,
        })?;
        let line = line.trim();
        if line.is_empty() {
            continue;
        }
        if line.starts_with('[') {
            if !line.ends_with(']') || line.starts_with("[[") {
                return Err(manifest_error(path, line_number, "malformed table header"));
            }
            if line == "[project]" {
                if project_seen {
                    return Err(manifest_error(
                        path,
                        line_number,
                        "duplicate [project] table",
                    ));
                }
                project_seen = true;
                table = Table::Project;
            } else if line == "[target.python]" {
                if python_seen {
                    return Err(manifest_error(
                        path,
                        line_number,
                        "duplicate [target.python] table",
                    ));
                }
                python_seen = true;
                table = Table::Python;
            } else {
                return Err(manifest_error(path, line_number, "unknown table"));
            }
            continue;
        }

        let Some(equal) = find_unquoted_equal(line) else {
            return Err(manifest_error(path, line_number, "expected key = value"));
        };
        if find_unquoted_equal(&line[equal + 1..]).is_some() {
            return Err(manifest_error(path, line_number, "malformed assignment"));
        }
        let key = line[..equal].trim();
        if key.is_empty() || key.chars().any(|c| c.is_whitespace()) {
            return Err(manifest_error(path, line_number, "malformed key"));
        }
        let value = parse_string(path, line_number, line[equal + 1..].trim())?;
        let slot = match (table, key) {
            (Table::Project, "name") => &mut name,
            (Table::Project, "source") => &mut source,
            (Table::Python, "generated") => &mut generated,
            (Table::Python, "entry") => &mut entry,
            _ => {
                return Err(manifest_error(
                    path,
                    line_number,
                    "unknown or misplaced field",
                ));
            }
        };
        if slot.is_some() {
            return Err(manifest_error(path, line_number, "duplicate field"));
        }
        *slot = Some(value);
    }

    if !project_seen || !python_seen {
        return Err(manifest_error(
            path,
            0,
            "manifest must contain [project] and [target.python] tables",
        ));
    }
    let missing = match (&name, &source, &generated, &entry) {
        (None, _, _, _) => Some("project.name"),
        (_, None, _, _) => Some("project.source"),
        (_, _, None, _) => Some("target.python.generated"),
        (_, _, _, None) => Some("target.python.entry"),
        _ => None,
    };
    if let Some(field) = missing {
        return Err(manifest_error(
            path,
            0,
            &format!("missing required field {field}"),
        ));
    }
    Ok(Manifest {
        name: name.unwrap_or_default(),
        source: source.unwrap_or_default(),
        generated: generated.unwrap_or_default(),
        entry: entry.unwrap_or_default(),
    })
}

fn manifest_error(path: &Path, line: usize, message: &str) -> ProjectError {
    ProjectError::Manifest {
        path: path.to_path_buf(),
        line,
        message: message.to_owned(),
    }
}

fn strip_comment(line: &str) -> Result<&str, String> {
    let bytes = line.as_bytes();
    let mut quote = false;
    let mut escaped = false;
    for (index, byte) in bytes.iter().enumerate() {
        if quote {
            if escaped {
                escaped = false;
            } else if *byte == b'\\' {
                escaped = true;
            } else if *byte == b'"' {
                quote = false;
            }
        } else if *byte == b'"' {
            quote = true;
        } else if *byte == b'#' {
            return Ok(&line[..index]);
        }
    }
    if quote || escaped {
        return Err("unterminated string".to_owned());
    }
    Ok(line)
}

fn find_unquoted_equal(line: &str) -> Option<usize> {
    let mut quoted = false;
    let mut escaped = false;
    for (index, byte) in line.bytes().enumerate() {
        if quoted {
            if escaped {
                escaped = false;
            } else if byte == b'\\' {
                escaped = true;
            } else if byte == b'"' {
                quoted = false;
            }
        } else if byte == b'"' {
            quoted = true;
        } else if byte == b'=' {
            return Some(index);
        }
    }
    None
}

fn parse_string(path: &Path, line: usize, value: &str) -> Result<String, ProjectError> {
    if value.len() < 2 || !value.starts_with('"') || !value.ends_with('"') {
        return Err(manifest_error(
            path,
            line,
            "value must be a double-quoted string",
        ));
    }
    let body = &value[1..value.len() - 1];
    let mut result = String::new();
    let mut chars = body.chars();
    while let Some(c) = chars.next() {
        if c == '\\' {
            let Some(escaped) = chars.next() else {
                return Err(manifest_error(path, line, "unterminated escape"));
            };
            result.push(match escaped {
                'b' => '\u{0008}',
                't' => '\t',
                'n' => '\n',
                'f' => '\u{000c}',
                'r' => '\r',
                '"' => '"',
                '\\' => '\\',
                _ => return Err(manifest_error(path, line, "unsupported string escape")),
            });
        } else if c == '\n' || c == '\r' || (c.is_control() && c != '\t') {
            return Err(manifest_error(path, line, "control character in string"));
        } else {
            result.push(c);
        }
    }
    Ok(result)
}
