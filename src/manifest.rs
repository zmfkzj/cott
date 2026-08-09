use std::collections::BTreeMap;
use std::path::{Component, Path, PathBuf};

use serde::Deserialize;

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ProjectConfig {
    pub project: ProjectMetadata,
    pub python: PythonTarget,
    pub effects: BTreeMap<String, bool>,
    pub generator: GeneratorConfig,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct ProjectMetadata {
    pub name: String,
    pub version: String,
    pub source: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq)]
#[serde(deny_unknown_fields)]
struct RawManifest {
    project: ProjectMetadata,
    target: Target,
    #[serde(default)]
    effects: BTreeMap<String, bool>,
    #[serde(default)]
    generator: GeneratorConfig,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq)]
#[serde(deny_unknown_fields)]
struct Target {
    python: PythonTarget,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct PythonTarget {
    pub source: String,
    pub generated: String,
    pub stubs: String,
    #[serde(default)]
    pub lockfile: Option<String>,
    pub interpreter: String,
    pub type_checker: String,
    pub runtime_validation: RuntimeValidation,
    #[serde(default)]
    pub implementations: BTreeMap<String, String>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq)]
#[serde(rename_all = "kebab-case")]
pub enum RuntimeValidation {
    Off,
    Boundary,
    TestOnly,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct GeneratorConfig {
    #[serde(default)]
    pub rules: Option<String>,
    #[serde(default = "default_timeout_seconds")]
    pub timeout_seconds: u16,
}

impl Default for GeneratorConfig {
    fn default() -> Self {
        Self {
            rules: None,
            timeout_seconds: default_timeout_seconds(),
        }
    }
}

const fn default_timeout_seconds() -> u16 {
    900
}

impl ProjectConfig {
    pub fn parse(path: &Path, bytes: &str) -> Result<Self, ManifestError> {
        let raw: RawManifest = toml::from_str(bytes).map_err(|source| ManifestError {
            path: path.to_path_buf(),
            message: source.to_string(),
        })?;
        let config = Self {
            project: raw.project,
            python: raw.target.python,
            effects: raw.effects,
            generator: raw.generator,
        };
        config.validate(path)?;
        Ok(config)
    }

    fn validate(&self, path: &Path) -> Result<(), ManifestError> {
        if self.project.name.trim().is_empty() || self.project.version.trim().is_empty() {
            return Err(ManifestError::new(
                path,
                "project.name and project.version must be nonempty",
            ));
        }
        for (field, value) in [
            ("project.source", &self.project.source),
            ("target.python.source", &self.python.source),
            ("target.python.generated", &self.python.generated),
            ("target.python.stubs", &self.python.stubs),
            ("target.python.interpreter", &self.python.interpreter),
            ("target.python.type_checker", &self.python.type_checker),
        ] {
            normalized_relative_path(value)
                .map_err(|message| ManifestError::new(path, format!("{field} {message}")))?;
        }
        if let Some(lockfile) = &self.python.lockfile {
            normalized_relative_path(lockfile).map_err(|message| {
                ManifestError::new(path, format!("target.python.lockfile {message}"))
            })?;
        }
        if let Some(rules) = &self.generator.rules {
            normalized_relative_path(rules).map_err(|message| {
                ManifestError::new(path, format!("generator.rules {message}"))
            })?;
        }
        if self.generator.timeout_seconds == 0 || self.generator.timeout_seconds > 3600 {
            return Err(ManifestError::new(
                path,
                "generator.timeout_seconds must be 1..=3600",
            ));
        }
        let generated = Path::new(&self.python.generated);
        let Some(artifact_root) = generated
            .parent()
            .filter(|parent| !parent.as_os_str().is_empty())
        else {
            return Err(ManifestError::new(
                path,
                "target.python.generated must be `<artifact-root>/python`",
            ));
        };
        if generated.file_name().and_then(|name| name.to_str()) != Some("python")
            || Path::new(&self.python.stubs) != artifact_root.join("stubs")
        {
            return Err(ManifestError::new(
                path,
                "target.python.generated and stubs must be `<artifact-root>/python` and `<artifact-root>/stubs`",
            ));
        }
        let roots = [
            Path::new(&self.project.source),
            Path::new(&self.python.source),
            artifact_root,
            Path::new("tests/generated"),
            Path::new(".cott"),
        ];
        for (index, left) in roots.iter().enumerate() {
            for right in roots.iter().skip(index + 1) {
                if path_overlaps(left, right) {
                    return Err(ManifestError::new(
                        path,
                        format!(
                            "managed path overlap: {} and {}",
                            left.display(),
                            right.display()
                        ),
                    ));
                }
            }
        }
        const PRELUDE_EFFECTS: [&str; 8] = [
            "file.read",
            "file.write",
            "network",
            "database.read",
            "database.write",
            "clock",
            "random",
            "process.exit",
        ];
        for (name, enabled) in &self.effects {
            if !enabled || !valid_qname(name) || PRELUDE_EFFECTS.contains(&name.as_str()) {
                return Err(ManifestError::new(
                    path,
                    format!("effect `{name}` must be a custom qname with literal value true"),
                ));
            }
        }
        for (symbol, target) in &self.python.implementations {
            let valid_target = target
                .split_once(':')
                .is_some_and(|(module, name)| valid_qname(module) && valid_identifier(name))
                && target.matches(':').count() == 1;
            if !valid_qname(symbol) || !valid_target {
                return Err(ManifestError::new(
                    path,
                    format!("invalid implementation binding `{symbol}` = `{target}`"),
                ));
            }
        }
        Ok(())
    }
}

pub fn normalized_relative_path(value: &str) -> Result<PathBuf, &'static str> {
    if value.is_empty() || value.contains('\\') || value.contains('\0') {
        return Err("must be a normalized relative path");
    }
    let path = Path::new(value);
    if path.is_absolute()
        || path
            .components()
            .any(|component| !matches!(component, Component::Normal(_)))
    {
        return Err("must be a normalized relative path");
    }
    Ok(path.to_path_buf())
}

fn path_overlaps(left: &Path, right: &Path) -> bool {
    left == right || left.starts_with(right) || right.starts_with(left)
}

fn valid_qname(value: &str) -> bool {
    value.split('.').all(valid_identifier)
}

fn valid_identifier(value: &str) -> bool {
    let mut chars = value.bytes();
    chars
        .next()
        .is_some_and(|byte| byte == b'_' || byte.is_ascii_alphabetic())
        && chars.all(|byte| byte == b'_' || byte.is_ascii_alphanumeric())
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ManifestError {
    pub path: PathBuf,
    pub message: String,
}

impl ManifestError {
    fn new(path: &Path, message: impl Into<String>) -> Self {
        Self {
            path: path.to_path_buf(),
            message: message.into(),
        }
    }
}

impl std::fmt::Display for ManifestError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(
            formatter,
            "invalid manifest {}: {}",
            self.path.display(),
            self.message
        )
    }
}

impl std::error::Error for ManifestError {}
