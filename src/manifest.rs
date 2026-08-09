use std::collections::BTreeMap;
use std::path::{Component, Path, PathBuf};

use serde::Deserialize;

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ProjectConfig {
    pub project: ProjectMetadata,
    pub python: PythonTarget,
    pub effects: BTreeMap<String, EffectConfig>,
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
    effects: BTreeMap<String, EffectConfig>,
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

#[derive(Clone, Debug, Default, Deserialize, Eq, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct EffectConfig {
    #[serde(default)]
    pub enabled: bool,
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
        if self.generator.timeout_seconds == 0 || self.generator.timeout_seconds > 3600 {
            return Err(ManifestError::new(
                path,
                "generator.timeout_seconds must be 1..=3600",
            ));
        }
        let paths = [
            &self.project.source,
            &self.python.source,
            &self.python.generated,
            &self.python.stubs,
        ];
        for (index, left) in paths.iter().enumerate() {
            for right in paths.iter().skip(index + 1) {
                if overlaps(left, right) {
                    return Err(ManifestError::new(
                        path,
                        format!("managed path overlap: {left} and {right}"),
                    ));
                }
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

fn overlaps(left: &str, right: &str) -> bool {
    let left = Path::new(left);
    let right = Path::new(right);
    left == right || left.starts_with(right) || right.starts_with(left)
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
