use std::collections::{BTreeMap, BTreeSet};
use std::path::{Component, Path, PathBuf};

use serde::Deserialize;

pub const DEFAULT_PROOF_NODE_LIMIT: u32 = 1024;
pub const DEFAULT_PROOF_BRANCH_LIMIT: u32 = 256;
pub const DEFAULT_CANDIDATE_LIMIT: u32 = 64;
pub const DEFAULT_LIFECYCLE_LIMIT: u32 = 3;
pub const DEFAULT_SCENARIO_TIMEOUT_MS: u32 = 1000;
pub const DEFAULT_FILESYSTEM_BYTES: u64 = 16_777_216;
pub const DEFAULT_FILESYSTEM_FILES: u32 = 256;
pub const DEFAULT_HTTP_BODY_BYTES: u64 = 1_048_576;
pub const DEFAULT_HTTP_REQUESTS: u32 = 64;
pub const DEFAULT_HTTP_REDIRECTS: u32 = 8;
pub const DEFAULT_TRANSCRIPT_EVENTS: u32 = 1024;
pub const MAX_PROOF_NODE_LIMIT: u32 = 16384;
pub const MAX_PROOF_BRANCH_LIMIT: u32 = 4096;
pub const MAX_CANDIDATE_LIMIT: u32 = 1024;
pub const MAX_LIFECYCLE_LIMIT: u32 = 64;
pub const MAX_SCENARIO_TIMEOUT_MS: u32 = 60_000;
pub const MAX_FILESYSTEM_BYTES: u64 = 268_435_456;
pub const MAX_FILESYSTEM_FILES: u32 = 4096;
pub const MAX_HTTP_BODY_BYTES: u64 = 16_777_216;
pub const MAX_HTTP_REQUESTS: u32 = 1024;
pub const MAX_HTTP_REDIRECTS: u32 = 64;
pub const MAX_TRANSCRIPT_EVENTS: u32 = 16_384;

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ProjectConfig {
    pub project: ProjectMetadata,
    pub python: PythonTarget,
    pub effects: BTreeMap<String, bool>,
    pub generator: GeneratorConfig,
    pub verification: VerificationConfig,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub enum TargetLanguage {
    Python,
    Kotlin,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct KotlinProjectConfig {
    pub project: ProjectMetadata,
    pub kotlin: KotlinTarget,
    pub effects: BTreeMap<String, bool>,
    pub generator: GeneratorConfig,
    pub verification: VerificationConfig,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct VerificationConfig {
    #[serde(default = "default_proof_node_limit")]
    pub proof_node_limit: u32,
    #[serde(default = "default_proof_branch_limit")]
    pub proof_branch_limit: u32,
    #[serde(default = "default_candidate_limit")]
    pub candidate_limit: u32,
    #[serde(default = "default_lifecycle_limit")]
    pub lifecycle_limit: u32,
    #[serde(default)]
    pub fixtures: FixtureLimits,
    #[serde(default)]
    pub coverage: CoveragePolicy,
}

impl Default for VerificationConfig {
    fn default() -> Self {
        Self {
            proof_node_limit: default_proof_node_limit(),
            proof_branch_limit: default_proof_branch_limit(),
            candidate_limit: default_candidate_limit(),
            lifecycle_limit: default_lifecycle_limit(),
            fixtures: FixtureLimits::default(),
            coverage: CoveragePolicy::default(),
        }
    }
}

const fn default_proof_node_limit() -> u32 {
    DEFAULT_PROOF_NODE_LIMIT
}

const fn default_proof_branch_limit() -> u32 {
    DEFAULT_PROOF_BRANCH_LIMIT
}

const fn default_candidate_limit() -> u32 {
    DEFAULT_CANDIDATE_LIMIT
}

const fn default_lifecycle_limit() -> u32 {
    DEFAULT_LIFECYCLE_LIMIT
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct FixtureLimits {
    #[serde(default = "default_scenario_timeout_ms")]
    pub scenario_timeout_ms: u32,
    #[serde(default = "default_filesystem_bytes")]
    pub filesystem_bytes: u64,
    #[serde(default = "default_filesystem_files")]
    pub filesystem_files: u32,
    #[serde(default = "default_http_body_bytes")]
    pub http_body_bytes: u64,
    #[serde(default = "default_http_requests")]
    pub http_requests: u32,
    #[serde(default = "default_http_redirects")]
    pub http_redirects: u32,
    #[serde(default = "default_transcript_events")]
    pub transcript_events: u32,
}

impl Default for FixtureLimits {
    fn default() -> Self {
        Self {
            scenario_timeout_ms: default_scenario_timeout_ms(),
            filesystem_bytes: default_filesystem_bytes(),
            filesystem_files: default_filesystem_files(),
            http_body_bytes: default_http_body_bytes(),
            http_requests: default_http_requests(),
            http_redirects: default_http_redirects(),
            transcript_events: default_transcript_events(),
        }
    }
}

const fn default_scenario_timeout_ms() -> u32 {
    DEFAULT_SCENARIO_TIMEOUT_MS
}

const fn default_filesystem_bytes() -> u64 {
    DEFAULT_FILESYSTEM_BYTES
}

const fn default_filesystem_files() -> u32 {
    DEFAULT_FILESYSTEM_FILES
}

const fn default_http_body_bytes() -> u64 {
    DEFAULT_HTTP_BODY_BYTES
}

const fn default_http_requests() -> u32 {
    DEFAULT_HTTP_REQUESTS
}

const fn default_http_redirects() -> u32 {
    DEFAULT_HTTP_REDIRECTS
}

const fn default_transcript_events() -> u32 {
    DEFAULT_TRANSCRIPT_EVENTS
}

#[derive(Clone, Debug, Default, Deserialize, Eq, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct CoveragePolicy {
    #[serde(default)]
    pub rules: Vec<CoverageRule>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct CoverageRule {
    pub symbol: String,
    pub clauses: Vec<String>,
    #[serde(default)]
    pub allow_unobserved: bool,
    #[serde(default)]
    pub allow_trust_declaration: bool,
    #[serde(default)]
    pub allow_unknown: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct ProjectMetadata {
    pub name: String,
    pub version: String,
    pub source: String,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd)]
pub struct ApiVersion {
    pub major: u64,
    pub minor: u64,
    pub patch: u64,
}

pub fn parse_api_version(value: &str) -> Option<ApiVersion> {
    let mut parts = value.split('.');
    let parse = |part: Option<&str>| {
        let part = part?;
        (!part.is_empty()
            && (part == "0" || !part.starts_with('0'))
            && part.bytes().all(|byte| byte.is_ascii_digit()))
        .then(|| part.parse().ok())
        .flatten()
    };
    let version = ApiVersion {
        major: parse(parts.next())?,
        minor: parse(parts.next())?,
        patch: parse(parts.next())?,
    };
    parts.next().is_none().then_some(version)
}

impl std::fmt::Display for ApiVersion {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(formatter, "{}.{}.{}", self.major, self.minor, self.patch)
    }
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
    #[serde(default)]
    verification: VerificationConfig,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq)]
#[serde(deny_unknown_fields)]
struct Target {
    #[serde(default)]
    python: Option<PythonTarget>,
    #[serde(default)]
    kotlin: Option<KotlinTarget>,
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
    #[serde(default)]
    pub external_types: BTreeMap<String, String>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq)]
#[serde(deny_unknown_fields)]
pub struct KotlinTarget {
    pub source: String,
    pub generated: String,
    #[serde(default = "default_kotlin_compiler")]
    pub compiler: String,
    #[serde(default = "default_java")]
    pub java: String,
    #[serde(default = "default_jvm_target")]
    pub jvm_target: u8,
    pub runtime_validation: RuntimeValidation,
    #[serde(default)]
    pub classpath: Vec<String>,
    #[serde(default)]
    pub compile_only: Vec<String>,
    #[serde(default)]
    pub implementations: BTreeMap<String, String>,
    #[serde(default)]
    pub external_types: BTreeMap<String, String>,
}

fn default_kotlin_compiler() -> String {
    "kotlinc".to_owned()
}

fn default_java() -> String {
    "java".to_owned()
}

const fn default_jvm_target() -> u8 {
    17
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

fn parse_raw(path: &Path, bytes: &str) -> Result<RawManifest, ManifestError> {
    toml::from_str(bytes).map_err(|source| ManifestError {
        path: path.to_path_buf(),
        message: source.to_string(),
    })
}

fn selected_target(path: &Path, target: &Target) -> Result<TargetLanguage, ManifestError> {
    match (&target.python, &target.kotlin) {
        (Some(_), None) => Ok(TargetLanguage::Python),
        (None, Some(_)) => Ok(TargetLanguage::Kotlin),
        (None, None) => Err(ManifestError::new(
            path,
            "target must define exactly one of target.python or target.kotlin",
        )),
        (Some(_), Some(_)) => Err(ManifestError::new(
            path,
            "target must not define both target.python and target.kotlin",
        )),
    }
}

pub fn target_language(path: &Path, bytes: &str) -> Result<TargetLanguage, ManifestError> {
    let raw = parse_raw(path, bytes)?;
    selected_target(path, &raw.target)
}

impl ProjectConfig {
    pub fn parse(path: &Path, bytes: &str) -> Result<Self, ManifestError> {
        let raw = parse_raw(path, bytes)?;
        if selected_target(path, &raw.target)? != TargetLanguage::Python {
            return Err(ManifestError::new(
                path,
                "ProjectConfig only supports target.python manifests",
            ));
        }
        let config = Self {
            project: raw.project,
            python: raw
                .target
                .python
                .expect("selected Python target must be present"),
            effects: raw.effects,
            generator: raw.generator,
            verification: raw.verification,
        };
        validate_common(
            path,
            &config.project,
            &config.effects,
            &config.generator,
            &config.verification,
        )?;
        config.validate_python(path)?;
        Ok(config)
    }

    fn validate_python(&self, path: &Path) -> Result<(), ManifestError> {
        for (field, value) in [
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
        validate_path_overlaps(
            path,
            &[
                Path::new(&self.project.source),
                Path::new(&self.python.source),
                artifact_root,
                Path::new("tests/generated"),
                Path::new(".cott"),
            ],
        )?;
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
        for (symbol, target) in &self.python.external_types {
            if !valid_external_type_symbol(symbol) || !valid_external_type_projection(target) {
                return Err(ManifestError::new(
                    path,
                    format!("invalid external type projection `{symbol}` = `{target}`"),
                ));
            }
        }
        Ok(())
    }
}

impl KotlinProjectConfig {
    pub fn parse(path: &Path, bytes: &str) -> Result<Self, ManifestError> {
        let raw = parse_raw(path, bytes)?;
        if selected_target(path, &raw.target)? != TargetLanguage::Kotlin {
            return Err(ManifestError::new(
                path,
                "KotlinProjectConfig only supports target.kotlin manifests",
            ));
        }
        let config = Self {
            project: raw.project,
            kotlin: raw
                .target
                .kotlin
                .expect("selected Kotlin target must be present"),
            effects: raw.effects,
            generator: raw.generator,
            verification: raw.verification,
        };
        validate_common(
            path,
            &config.project,
            &config.effects,
            &config.generator,
            &config.verification,
        )?;
        config.validate_kotlin(path)?;
        Ok(config)
    }

    fn validate_kotlin(&self, path: &Path) -> Result<(), ManifestError> {
        if !valid_kotlin_project_name(&self.project.name) {
            return Err(ManifestError::new(
                path,
                "project.name must be lowercase kebab-case for Kotlin targets",
            ));
        }
        for (field, value) in [
            ("target.kotlin.source", &self.kotlin.source),
            ("target.kotlin.generated", &self.kotlin.generated),
        ] {
            normalized_relative_path(value)
                .map_err(|message| ManifestError::new(path, format!("{field} {message}")))?;
        }
        for (field, value) in [
            ("target.kotlin.compiler", &self.kotlin.compiler),
            ("target.kotlin.java", &self.kotlin.java),
        ] {
            if !valid_tool_spec(value) {
                return Err(ManifestError::new(
                    path,
                    format!("{field} must be a bare executable or normalized path"),
                ));
            }
        }
        if self.kotlin.jvm_target != 17 {
            return Err(ManifestError::new(
                path,
                "target.kotlin.jvm_target must be 17",
            ));
        }
        let generated = Path::new(&self.kotlin.generated);
        let Some(artifact_root) = generated
            .parent()
            .filter(|parent| !parent.as_os_str().is_empty())
        else {
            return Err(ManifestError::new(
                path,
                "target.kotlin.generated must be `<artifact-root>/kotlin`",
            ));
        };
        if generated.file_name().and_then(|name| name.to_str()) != Some("kotlin") {
            return Err(ManifestError::new(
                path,
                "target.kotlin.generated must be `<artifact-root>/kotlin`",
            ));
        }

        let mut protected_paths = vec![
            PathBuf::from(&self.project.source),
            PathBuf::from(&self.kotlin.source),
            artifact_root.to_path_buf(),
            PathBuf::from("tests/generated"),
            PathBuf::from(".cott"),
        ];
        if let Some(rules) = &self.generator.rules {
            protected_paths.push(PathBuf::from(rules));
        }
        for (field, entries) in [
            ("target.kotlin.classpath", &self.kotlin.classpath),
            ("target.kotlin.compile_only", &self.kotlin.compile_only),
        ] {
            for classpath in entries {
                let classpath_path = normalized_relative_path(classpath).map_err(|message| {
                    ManifestError::new(path, format!("{field} entry {message}"))
                })?;
                if classpath_path
                    .extension()
                    .and_then(|extension| extension.to_str())
                    != Some("jar")
                {
                    return Err(ManifestError::new(
                        path,
                        format!("{field} entries must be .jar files"),
                    ));
                }
                protected_paths.push(classpath_path);
            }
        }
        validate_path_overlaps(path, &protected_paths)?;

        for (symbol, target) in &self.kotlin.implementations {
            if !valid_qname(symbol) || !valid_kotlin_fqn(target) {
                return Err(ManifestError::new(
                    path,
                    format!("invalid Kotlin implementation binding `{symbol}` = `{target}`"),
                ));
            }
        }
        for (symbol, target) in &self.kotlin.external_types {
            if !valid_external_type_symbol(symbol) || !valid_kotlin_fqn(target) {
                return Err(ManifestError::new(
                    path,
                    format!("invalid Kotlin external type projection `{symbol}` = `{target}`"),
                ));
            }
        }
        Ok(())
    }
}

fn validate_common(
    path: &Path,
    project: &ProjectMetadata,
    effects: &BTreeMap<String, bool>,
    generator: &GeneratorConfig,
    verification: &VerificationConfig,
) -> Result<(), ManifestError> {
    if project.name.trim().is_empty() {
        return Err(ManifestError::new(path, "project.name must be nonempty"));
    }
    if parse_api_version(&project.version).is_none() {
        return Err(ManifestError::new(
            path,
            "project.version must be a restricted x.y.z version",
        ));
    }
    normalized_relative_path(&project.source)
        .map_err(|message| ManifestError::new(path, format!("project.source {message}")))?;
    if let Some(rules) = &generator.rules {
        normalized_relative_path(rules)
            .map_err(|message| ManifestError::new(path, format!("generator.rules {message}")))?;
    }
    if generator.timeout_seconds == 0 || generator.timeout_seconds > 3600 {
        return Err(ManifestError::new(
            path,
            "generator.timeout_seconds must be 1..=3600",
        ));
    }
    for (field, value, maximum) in [
        (
            "verification.proof_node_limit",
            verification.proof_node_limit,
            MAX_PROOF_NODE_LIMIT,
        ),
        (
            "verification.proof_branch_limit",
            verification.proof_branch_limit,
            MAX_PROOF_BRANCH_LIMIT,
        ),
        (
            "verification.candidate_limit",
            verification.candidate_limit,
            MAX_CANDIDATE_LIMIT,
        ),
        (
            "verification.lifecycle_limit",
            verification.lifecycle_limit,
            MAX_LIFECYCLE_LIMIT,
        ),
    ] {
        if value == 0 || value > maximum {
            return Err(ManifestError::new(
                path,
                format!("{field} must be 1..={maximum}"),
            ));
        }
    }
    validate_fixture_limits(path, &verification.fixtures)?;
    validate_coverage_policy(path, &verification.coverage)?;
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
    for (name, enabled) in effects {
        if !enabled || !valid_qname(name) || PRELUDE_EFFECTS.contains(&name.as_str()) {
            return Err(ManifestError::new(
                path,
                format!("effect `{name}` must be a custom qname with literal value true"),
            ));
        }
    }
    Ok(())
}

fn validate_path_overlaps<P: AsRef<Path>>(path: &Path, paths: &[P]) -> Result<(), ManifestError> {
    for (index, left) in paths.iter().enumerate() {
        let left = left.as_ref();
        for right in paths.iter().skip(index + 1) {
            let right = right.as_ref();
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
    Ok(())
}

fn validate_fixture_limits(path: &Path, fixtures: &FixtureLimits) -> Result<(), ManifestError> {
    for (field, value, maximum) in [
        (
            "scenario_timeout_ms",
            fixtures.scenario_timeout_ms as u64,
            MAX_SCENARIO_TIMEOUT_MS as u64,
        ),
        (
            "filesystem_bytes",
            fixtures.filesystem_bytes,
            MAX_FILESYSTEM_BYTES,
        ),
        (
            "filesystem_files",
            fixtures.filesystem_files as u64,
            MAX_FILESYSTEM_FILES as u64,
        ),
        (
            "http_body_bytes",
            fixtures.http_body_bytes,
            MAX_HTTP_BODY_BYTES,
        ),
        (
            "http_requests",
            fixtures.http_requests as u64,
            MAX_HTTP_REQUESTS as u64,
        ),
        (
            "http_redirects",
            fixtures.http_redirects as u64,
            MAX_HTTP_REDIRECTS as u64,
        ),
        (
            "transcript_events",
            fixtures.transcript_events as u64,
            MAX_TRANSCRIPT_EVENTS as u64,
        ),
    ] {
        if value == 0 || value > maximum {
            return Err(ManifestError::new(
                path,
                format!("verification.fixtures.{field} must be 1..={maximum}"),
            ));
        }
    }
    Ok(())
}

fn validate_coverage_policy(path: &Path, policy: &CoveragePolicy) -> Result<(), ManifestError> {
    let mut selected = BTreeSet::new();
    for rule in &policy.rules {
        if !valid_qname(&rule.symbol) {
            return Err(ManifestError::new(
                path,
                format!(
                    "verification.coverage.rules symbol `{}` must be an exact qname",
                    rule.symbol
                ),
            ));
        }
        if rule.clauses.is_empty() {
            return Err(ManifestError::new(
                path,
                format!(
                    "verification.coverage.rules `{}` must select at least one clause",
                    rule.symbol
                ),
            ));
        }
        let mut previous = None;
        for clause in &rule.clauses {
            let key = normalized_clause_selector(clause).ok_or_else(|| {
                ManifestError::new(
                    path,
                    format!(
                        "verification.coverage.rules `{}` has invalid clause selector `{clause}`",
                        rule.symbol
                    ),
                )
            })?;
            if previous.as_ref().is_some_and(|previous| previous >= &key) {
                return Err(ManifestError::new(
                    path,
                    format!(
                        "verification.coverage.rules `{}` clauses must be sorted and unique",
                        rule.symbol
                    ),
                ));
            }
            previous = Some(key);
            if !selected.insert((rule.symbol.as_str(), clause.as_str())) {
                return Err(ManifestError::new(
                    path,
                    format!(
                        "verification.coverage.rules contains duplicate selector `{}:{clause}`",
                        rule.symbol
                    ),
                ));
            }
        }
    }
    Ok(())
}

fn normalized_clause_selector(value: &str) -> Option<(u8, u64, String)> {
    let (kind, id) = value.split_once(':')?;
    if id.is_empty() || id.contains(':') {
        return None;
    }
    let kind_order = match kind {
        "requires" => 0,
        "ensures" => 1,
        "error" => 2,
        "modifies" => 3,
        "invariant" => 4,
        _ => return None,
    };
    if kind == "modifies" {
        valid_qname(id).then(|| (kind_order, 0, id.to_owned()))
    } else {
        let numeric_id = id.parse::<u64>().ok()?;
        (numeric_id.to_string() == id).then(|| (kind_order, numeric_id, String::new()))
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

fn valid_tool_spec(value: &str) -> bool {
    if value.is_empty() || value.contains('\0') {
        return false;
    }
    #[cfg(not(windows))]
    if value.contains('\\') {
        return false;
    }
    let path = Path::new(value);
    if !path.is_absolute() {
        return normalized_relative_path(value).is_ok();
    }
    let mut saw_name = false;
    for component in path.components() {
        match component {
            Component::Prefix(_) | Component::RootDir => {}
            Component::Normal(_) => saw_name = true,
            Component::CurDir | Component::ParentDir => return false,
        }
    }
    saw_name
}

pub(crate) fn valid_kotlin_project_name(value: &str) -> bool {
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

pub(crate) fn valid_kotlin_fqn(value: &str) -> bool {
    value.contains('.') && value.split('.').all(valid_kotlin_name)
}

fn valid_kotlin_name(value: &str) -> bool {
    let mut characters = value.chars();
    characters
        .next()
        .is_some_and(|character| character == '_' || character.is_alphabetic())
        && characters.all(|character| character == '_' || character.is_alphanumeric())
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

fn valid_external_type_symbol(value: &str) -> bool {
    value.contains('.') && value.split('.').all(valid_cott_name)
}

fn valid_external_type_projection(value: &str) -> bool {
    value.matches(':').count() == 1
        && value.split_once(':').is_some_and(|(module, qualified)| {
            valid_python_qname(module) && valid_python_qname(qualified)
        })
}

fn valid_cott_name(value: &str) -> bool {
    valid_identifier(value)
        && !matches!(
            value,
            "module"
                | "use"
                | "external"
                | "type"
                | "alias"
                | "newtype"
                | "where"
                | "struct"
                | "enum"
                | "trait"
                | "impl"
                | "for"
                | "state"
                | "const"
                | "fn"
                | "self"
                | "doc"
                | "requires"
                | "invariant"
                | "init"
                | "ensures"
                | "when"
                | "effects"
                | "modifies"
                | "old"
                | "error"
                | "true"
                | "false"
                | "and"
                | "or"
                | "not"
                | "rule"
                | "override"
                | "delete"
                | "remove"
        )
}

fn valid_python_qname(value: &str) -> bool {
    !value.is_empty() && value.split('.').all(valid_python_name)
}

fn valid_python_name(value: &str) -> bool {
    valid_identifier(value)
        && !value.starts_with("_cott_")
        && !(value.starts_with("__") && value.ends_with("__"))
        && !matches!(
            value,
            "False"
                | "None"
                | "True"
                | "and"
                | "as"
                | "assert"
                | "async"
                | "await"
                | "break"
                | "class"
                | "continue"
                | "def"
                | "del"
                | "elif"
                | "else"
                | "except"
                | "finally"
                | "for"
                | "from"
                | "global"
                | "if"
                | "import"
                | "in"
                | "is"
                | "lambda"
                | "nonlocal"
                | "not"
                | "or"
                | "pass"
                | "raise"
                | "return"
                | "try"
                | "while"
                | "with"
                | "yield"
        )
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
