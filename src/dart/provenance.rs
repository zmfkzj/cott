use std::collections::{BTreeMap, BTreeSet};
use std::path::{Path, PathBuf};
use std::sync::LazyLock;

use serde::{Deserialize, Serialize};
use serde_json::{Map, Value, json};

use crate::provenance::{AgentRun, SemanticCoverage};
use crate::snapshot_record;

use super::DartOwner;

pub const DART_GENERATION_SCHEMA_VERSION: u32 = 2;
pub const DART_RUNTIME_ABI_VERSION: u32 = 2;
const DART_GENERATION_DOMAIN: &str = "cott.dart.generation.v2";
const LEGACY_CANONICAL_IR_SCHEMA_VERSION: u32 = 8;
const LEGACY_CONTRACT_STRATEGY_SCHEMA_VERSION: u64 = 5;

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DartGenerationRecord {
    pub schema_version: u32,
    pub current: DartGenerationSnapshot,
    pub last_verified: Option<DartGenerationSnapshot>,
}

impl Serialize for DartGenerationRecord {
    fn serialize<S>(&self, serializer: S) -> Result<S::Ok, S::Error>
    where
        S: serde::Serializer,
    {
        let current = serde_json::to_value(&self.current).map_err(serde::ser::Error::custom)?;
        let last_verified = self
            .last_verified
            .as_ref()
            .map(serde_json::to_value)
            .transpose()
            .map_err(serde::ser::Error::custom)?;
        let wire = snapshot_record::encode(self.schema_version, &current, last_verified.as_ref())
            .map_err(serde::ser::Error::custom)?;
        self.validate_identities(&wire)
            .map_err(serde::ser::Error::custom)?;
        wire.serialize(serializer)
    }
}

impl<'de> Deserialize<'de> for DartGenerationRecord {
    fn deserialize<D>(deserializer: D) -> Result<Self, D::Error>
    where
        D: serde::Deserializer<'de>,
    {
        let wire = snapshot_record::deserialize_json(deserializer)?;
        validate_schema(&wire).map_err(serde::de::Error::custom)?;
        let (current, last_verified) =
            snapshot_record::decode(&wire, DART_GENERATION_SCHEMA_VERSION)
                .map_err(serde::de::Error::custom)?;
        let record = Self {
            schema_version: DART_GENERATION_SCHEMA_VERSION,
            current: serde_json::from_value(current).map_err(serde::de::Error::custom)?,
            last_verified: last_verified
                .map(serde_json::from_value)
                .transpose()
                .map_err(serde::de::Error::custom)?,
        };
        record
            .validate_identities(&wire)
            .map_err(serde::de::Error::custom)?;
        Ok(record)
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct DartGenerationSnapshot {
    pub target: String,
    pub generation_id: String,
    pub verified: bool,
    pub compiler_version: String,
    pub canonical_ir_schema: u32,
    pub runtime_abi: u32,
    pub project_name: String,
    pub project_version: String,
    pub inputs: BTreeMap<String, String>,
    pub tools: Value,
    pub ir: BTreeMap<String, String>,
    pub contract_surface: Value,
    pub public_symbols: BTreeMap<String, Vec<String>>,
    pub implementations: Vec<DartBindingRecord>,
    pub dependencies: Value,
    pub managed_files: BTreeMap<String, String>,
    pub unresolved: Vec<String>,
    pub verification: Value,
    pub semantic_coverage: SemanticCoverage,
    pub agent_runs: Vec<AgentRun>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct DartBindingRecord {
    pub cott_symbol: String,
    pub target_symbol: String,
    pub source_origin: String,
    pub runtime_origin: String,
    pub content_hash: String,
    pub owner: DartOwner,
}

impl DartGenerationSnapshot {
    pub fn compute_generation_id(&mut self) -> Result<(), String> {
        validate_snapshot_contents(self)?;
        self.generation_id = snapshot_record::digest(&normalized_generation_identity(self)?)?;
        Ok(())
    }
}

impl DartGenerationRecord {
    pub fn parse(bytes: &[u8]) -> Result<Self, String> {
        let value = snapshot_record::parse_json(bytes)
            .map_err(|error| format!("invalid Dart generation JSON: {error}"))?;
        serde_json::from_value(value)
            .map_err(|error| format!("invalid Dart generation record: {error}"))
    }

    /// Restricted compiler-internal cutover input. Normal parsing never calls this reader.
    pub(crate) fn parse_legacy_for_emit(bytes: &[u8]) -> Result<Self, String> {
        let wire = snapshot_record::parse_json(bytes)?;
        validate_legacy_schema(&wire)?;
        let (current, last_verified) =
            snapshot_record::decode_legacy(&wire, DART_GENERATION_SCHEMA_VERSION)?;
        let record = Self {
            schema_version: DART_GENERATION_SCHEMA_VERSION,
            current: serde_json::from_value(current).map_err(|error| error.to_string())?,
            last_verified: last_verified
                .map(serde_json::from_value)
                .transpose()
                .map_err(|error| error.to_string())?,
        };
        record.validate_legacy_identities(&wire)?;
        Ok(record)
    }

    pub fn canonical_bytes(&self) -> Result<Vec<u8>, String> {
        let value = serde_json::to_value(self)
            .map_err(|error| format!("serialize Dart generation record: {error}"))?;
        validate_schema(&value)?;
        canonical_json(&value)
    }

    fn validate_identities(&self, wire: &Value) -> Result<(), String> {
        if self.schema_version != DART_GENERATION_SCHEMA_VERSION {
            return Err(format!(
                "Dart generation schema version must be {DART_GENERATION_SCHEMA_VERSION}"
            ));
        }
        validate_snapshot_identity(&self.current)?;
        if let Some(snapshot) = &self.last_verified {
            if !snapshot.verified {
                return Err("Dart last_verified snapshot is not verified".to_owned());
            }
            validate_snapshot_identity(snapshot)?;
            if snapshot.project_name != self.current.project_name {
                return Err("Dart last_verified snapshot belongs to a different project".to_owned());
            }
        }
        if self.current.verified && wire["current"] != wire["last_verified"] {
            return Err(
                "verified Dart current snapshot must equal last_verified snapshot".to_owned(),
            );
        }
        Ok(())
    }

    fn validate_legacy_identities(&self, wire: &Value) -> Result<(), String> {
        validate_snapshot_identity_for_schema(&self.current, LEGACY_CANONICAL_IR_SCHEMA_VERSION)?;
        if let Some(snapshot) = &self.last_verified {
            if !snapshot.verified || snapshot.project_name != self.current.project_name {
                return Err("invalid legacy Dart last_verified snapshot".to_owned());
            }
            validate_snapshot_identity_for_schema(snapshot, LEGACY_CANONICAL_IR_SCHEMA_VERSION)?;
        }
        if self.current.verified && wire["current"] != wire["last_verified"] {
            return Err("verified legacy Dart current must equal last_verified".to_owned());
        }
        Ok(())
    }
}

fn validate_snapshot_identity(snapshot: &DartGenerationSnapshot) -> Result<(), String> {
    validate_snapshot_identity_for_schema(snapshot, crate::provenance::CANONICAL_IR_SCHEMA_VERSION)
}

fn validate_snapshot_identity_for_schema(
    snapshot: &DartGenerationSnapshot,
    canonical_ir_schema: u32,
) -> Result<(), String> {
    validate_snapshot_contents_for_schema(snapshot, canonical_ir_schema)?;
    if !valid_digest(&snapshot.generation_id) {
        return Err("Dart generation_id must be a lowercase SHA-256 digest".to_owned());
    }
    let expected = snapshot_record::digest(&normalized_generation_identity(snapshot)?)?;
    if expected != snapshot.generation_id {
        return Err(format!(
            "Dart generation identity mismatch: expected {}, got {}",
            expected, snapshot.generation_id
        ));
    }
    Ok(())
}

fn validate_snapshot_contents(snapshot: &DartGenerationSnapshot) -> Result<(), String> {
    validate_snapshot_contents_for_schema(snapshot, crate::provenance::CANONICAL_IR_SCHEMA_VERSION)
}

fn validate_snapshot_contents_for_schema(
    snapshot: &DartGenerationSnapshot,
    canonical_ir_schema: u32,
) -> Result<(), String> {
    if snapshot.target != "dart" {
        return Err("Dart generation target must be `dart`".to_owned());
    }
    if snapshot.compiler_version != env!("CARGO_PKG_VERSION") {
        return Err(format!(
            "Dart generation compiler_version must be {}",
            env!("CARGO_PKG_VERSION")
        ));
    }
    if snapshot.canonical_ir_schema != canonical_ir_schema {
        return Err(format!(
            "Dart canonical IR schema must be {canonical_ir_schema}"
        ));
    }
    if snapshot.runtime_abi != DART_RUNTIME_ABI_VERSION {
        return Err(format!(
            "Dart runtime ABI must be {DART_RUNTIME_ABI_VERSION}"
        ));
    }
    if !crate::manifest::valid_dart_project_name(&snapshot.project_name) {
        return Err(
            "Dart generation project_name must be a non-keyword lowercase snake_case package name"
                .to_owned(),
        );
    }
    if crate::manifest::parse_api_version(&snapshot.project_version).is_none() {
        return Err(
            "Dart generation project_version must be a restricted x.y.z version".to_owned(),
        );
    }
    if !snapshot.tools.is_object() {
        return Err("Dart generation tools must be an object".to_owned());
    }
    let intent = crate::intent::recorded_fingerprints(&snapshot.tools)?;
    if let Some(hashes) = &intent {
        for symbol in hashes.keys() {
            if !valid_qualified_name(symbol) {
                return Err(format!(
                    "Dart tools.cott_intent symbol `{symbol}` is not canonical"
                ));
            }
        }
    }
    let surface = snapshot
        .contract_surface
        .as_object()
        .ok_or_else(|| "Dart generation contract_surface must be an object".to_owned())?;
    if snapshot.verified != snapshot.verification.is_object() {
        return Err(
            "Dart generation verification evidence must be present exactly when verified"
                .to_owned(),
        );
    }
    if snapshot.verified && !snapshot.unresolved.is_empty() {
        return Err("verified Dart generation snapshot has unresolved callables".to_owned());
    }
    if canonical_ir_schema == LEGACY_CANONICAL_IR_SCHEMA_VERSION && snapshot.verified {
        let strategies = snapshot
            .verification
            .pointer("/contract_tests/strategies")
            .and_then(Value::as_array)
            .ok_or("verified legacy Dart record has no contract strategy evidence")?;
        if strategies.iter().any(|strategy| {
            strategy.get("schema_version").and_then(Value::as_u64)
                != Some(LEGACY_CONTRACT_STRATEGY_SCHEMA_VERSION)
        }) {
            return Err("legacy Dart contract strategy schema must be 5".to_owned());
        }
    }

    validate_path_hashes("input", &snapshot.inputs)?;
    if !snapshot.inputs.contains_key("cott.toml") {
        return Err("Dart generation inputs must identify cott.toml".to_owned());
    }
    if !snapshot
        .inputs
        .keys()
        .any(|path| Path::new(path).extension().and_then(|value| value.to_str()) == Some("cott"))
    {
        return Err("Dart generation inputs must identify at least one .cott source".to_owned());
    }
    validate_ir_hashes(&snapshot.ir)?;
    if snapshot.ir.is_empty() {
        return Err("Dart generation IR identities must not be empty".to_owned());
    }
    let ir_modules = snapshot
        .ir
        .keys()
        .map(String::as_str)
        .collect::<BTreeSet<_>>();
    let surface_modules = surface.keys().map(String::as_str).collect::<BTreeSet<_>>();
    if ir_modules != surface_modules {
        return Err("Dart contract_surface modules must exactly match IR identities".to_owned());
    }
    validate_public_symbols(&snapshot.public_symbols)?;
    validate_dependencies(&snapshot.dependencies, &snapshot.project_name)?;
    validate_path_hashes("managed file", &snapshot.managed_files)?;
    validate_unresolved(&snapshot.unresolved)?;
    let implementations = validate_implementations(&snapshot.implementations)?;
    for symbol in &snapshot.unresolved {
        if implementations
            .get(symbol.as_str())
            .is_some_and(|implementation| implementation.owner != DartOwner::Agent)
        {
            return Err(format!(
                "unresolved Dart callable `{symbol}` cannot retain a manifest implementation"
            ));
        }
    }
    validate_agent_runs(
        &snapshot.agent_runs,
        &implementations,
        &snapshot.unresolved,
        intent.as_ref(),
    )?;
    crate::provenance::validate_semantic_coverage(&snapshot.semantic_coverage)?;
    Ok(())
}

fn validate_path_hashes(label: &str, entries: &BTreeMap<String, String>) -> Result<(), String> {
    for (path, digest) in entries {
        normalized_relative_path(path)
            .map_err(|message| format!("Dart generation {label} path `{path}` {message}"))?;
        if !valid_digest(digest) {
            return Err(format!(
                "Dart generation {label} `{path}` has an invalid SHA-256 digest"
            ));
        }
    }
    Ok(())
}

fn validate_ir_hashes(ir: &BTreeMap<String, String>) -> Result<(), String> {
    for (module, digest) in ir {
        if !valid_qualified_name(module) {
            return Err(format!(
                "Dart generation IR module `{module}` is not a canonical symbol"
            ));
        }
        if !valid_digest(digest) {
            return Err(format!(
                "Dart generation IR module `{module}` has an invalid SHA-256 digest"
            ));
        }
    }
    Ok(())
}

fn validate_public_symbols(symbols: &BTreeMap<String, Vec<String>>) -> Result<(), String> {
    for (module, names) in symbols {
        if !valid_qualified_name(module) {
            return Err(format!(
                "Dart public symbol module `{module}` is not a canonical symbol"
            ));
        }
        let mut previous = None;
        for name in names {
            if !valid_identifier(name) {
                return Err(format!(
                    "Dart public symbol `{module}.{name}` is not a canonical identifier"
                ));
            }
            if previous.is_some_and(|previous: &String| previous >= name) {
                return Err(format!(
                    "Dart public symbols for `{module}` must be sorted and unique"
                ));
            }
            previous = Some(name);
        }
    }
    Ok(())
}

fn validate_implementations(
    implementations: &[DartBindingRecord],
) -> Result<BTreeMap<&str, &DartBindingRecord>, String> {
    let mut records = BTreeMap::new();
    let mut previous = None;
    for implementation in implementations {
        if !valid_qualified_name(&implementation.cott_symbol) {
            return Err(format!(
                "Dart implementation has invalid Cott symbol `{}`",
                implementation.cott_symbol
            ));
        }
        if previous.is_some_and(|previous: &String| previous >= &implementation.cott_symbol) {
            return Err("Dart implementations must be sorted and unique by Cott symbol".to_owned());
        }
        previous = Some(&implementation.cott_symbol);

        let (target_path, target_name) = parse_target_symbol(&implementation.target_symbol)
            .map_err(|message| {
                format!(
                    "Dart implementation `{}` target_symbol {message}",
                    implementation.cott_symbol
                )
            })?;
        if !valid_private_dart_identifier(target_name) {
            return Err(format!(
                "Dart implementation `{}` target symbol must name a private Dart function",
                implementation.cott_symbol
            ));
        }
        let source =
            normalized_relative_path(&implementation.source_origin).map_err(|message| {
                format!(
                    "Dart implementation `{}` source_origin {message}",
                    implementation.cott_symbol
                )
            })?;
        if source.extension().and_then(|extension| extension.to_str()) != Some("dart")
            || !source.ends_with(&target_path)
        {
            return Err(format!(
                "Dart implementation `{}` source_origin must end with its target .dart path",
                implementation.cott_symbol
            ));
        }
        let runtime =
            normalized_relative_path(&implementation.runtime_origin).map_err(|message| {
                format!(
                    "Dart implementation `{}` runtime_origin {message}",
                    implementation.cott_symbol
                )
            })?;
        let expected_runtime = runtime_origin(&implementation.cott_symbol);
        if runtime != expected_runtime {
            return Err(format!(
                "Dart implementation `{}` runtime_origin must be `{}`",
                implementation.cott_symbol,
                expected_runtime.display()
            ));
        }
        if !valid_digest(&implementation.content_hash) {
            return Err(format!(
                "Dart implementation `{}` has an invalid content hash",
                implementation.cott_symbol
            ));
        }
        records.insert(implementation.cott_symbol.as_str(), implementation);
    }
    Ok(records)
}

fn parse_target_symbol(value: &str) -> Result<(PathBuf, &str), String> {
    let Some((path, name)) = value.split_once(':') else {
        return Err("must use `source-relative-file.dart:_private_name` syntax".to_owned());
    };
    if value.matches(':').count() != 1 {
        return Err("must contain exactly one `:` separator".to_owned());
    }
    let path = normalized_relative_path(path).map_err(|message| format!("path {message}"))?;
    if path.extension().and_then(|extension| extension.to_str()) != Some("dart") {
        return Err("path must name a .dart file".to_owned());
    }
    Ok((path, name))
}

fn runtime_origin(symbol: &str) -> PathBuf {
    let mut path = PathBuf::from("dart/lib/src/cott_impl");
    for segment in symbol.split('.') {
        path.push(segment);
    }
    path.set_extension("dart");
    path
}

fn validate_unresolved(unresolved: &[String]) -> Result<(), String> {
    let mut previous = None;
    for symbol in unresolved {
        if !valid_qualified_name(symbol) {
            return Err(format!("Dart unresolved symbol `{symbol}` is invalid"));
        }
        if previous.is_some_and(|previous: &String| previous >= symbol) {
            return Err("Dart unresolved symbols must be sorted and unique".to_owned());
        }
        previous = Some(symbol);
    }
    Ok(())
}

fn validate_dependencies(dependencies: &Value, project_name: &str) -> Result<(), String> {
    let object = dependencies
        .as_object()
        .ok_or_else(|| "Dart dependencies must be a closed object".to_owned())?;
    require_exact_fields(
        object,
        &[
            "schema_version",
            "pubspec_hash",
            "lockfile_hash",
            "packages",
        ],
        "Dart dependencies",
    )?;
    if object.get("schema_version").and_then(Value::as_u64) != Some(1) {
        return Err("Dart dependencies schema_version must be 1".to_owned());
    }
    let pubspec_hash = optional_digest(object.get("pubspec_hash"), "pubspec_hash")?;
    let lockfile_hash = optional_digest(object.get("lockfile_hash"), "lockfile_hash")?;
    if pubspec_hash.is_some() != lockfile_hash.is_some() {
        return Err(
            "Dart dependency pubspec_hash and lockfile_hash must be present together".to_owned(),
        );
    }
    let packages = object
        .get("packages")
        .and_then(Value::as_array)
        .ok_or_else(|| "Dart dependency packages must be an array".to_owned())?;
    if !packages.is_empty() && pubspec_hash.is_none() {
        return Err(
            "Dart dependency packages require verified pubspec and lockfile hashes".to_owned(),
        );
    }

    let mut names = BTreeSet::new();
    let mut previous = None;
    for package in packages {
        let package = package
            .as_object()
            .ok_or_else(|| "Dart dependency package must be an object".to_owned())?;
        require_exact_fields(
            package,
            &[
                "name",
                "version",
                "source",
                "source_identity",
                "content_hash",
                "dependencies",
                "runtime",
            ],
            "Dart dependency package",
        )?;
        let name = required_string(package, "name", "Dart dependency package")?;
        if !valid_dependency_package_name(name) || name == project_name {
            return Err(format!("Dart dependency package name `{name}` is invalid"));
        }
        if previous.is_some_and(|previous: &str| previous >= name) {
            return Err("Dart dependency packages must be sorted and unique by name".to_owned());
        }
        previous = Some(name);
        names.insert(name);

        let version = required_string(package, "version", "Dart dependency package")?;
        if !valid_semver(version) {
            return Err(format!(
                "Dart dependency package `{name}` has an invalid exact semantic version"
            ));
        }
        let source = required_string(package, "source", "Dart dependency package")?;
        let source_identity =
            required_string(package, "source_identity", "Dart dependency package")?;
        match source {
            "hosted" if valid_hosted_source_identity(source_identity) => {}
            "path" if normalized_relative_path(source_identity).is_ok() => {}
            "hosted" | "path" => {
                return Err(format!(
                    "Dart dependency package `{name}` has an invalid {source} source identity"
                ));
            }
            _ => {
                return Err(format!(
                    "Dart dependency package `{name}` has unsupported source `{source}`"
                ));
            }
        }
        let content_hash = required_string(package, "content_hash", "Dart dependency package")?;
        if !valid_digest(content_hash) {
            return Err(format!(
                "Dart dependency package `{name}` has an invalid content hash"
            ));
        }
        if package.get("runtime").and_then(Value::as_bool).is_none() {
            return Err(format!(
                "Dart dependency package `{name}` runtime must be a boolean"
            ));
        }
        let package_dependencies = package
            .get("dependencies")
            .and_then(Value::as_array)
            .ok_or_else(|| {
                format!("Dart dependency package `{name}` dependencies must be an array")
            })?;
        let mut previous_dependency = None;
        for dependency in package_dependencies {
            let dependency = dependency.as_str().ok_or_else(|| {
                format!("Dart dependency package `{name}` has a non-string dependency")
            })?;
            if !valid_dependency_package_name(dependency) || dependency == name {
                return Err(format!(
                    "Dart dependency package `{name}` has invalid dependency `{dependency}`"
                ));
            }
            if previous_dependency.is_some_and(|previous: &str| previous >= dependency) {
                return Err(format!(
                    "Dart dependency package `{name}` dependencies must be sorted and unique"
                ));
            }
            previous_dependency = Some(dependency);
        }
    }

    for package in packages {
        let package = package.as_object().expect("validated package object");
        let name = package
            .get("name")
            .and_then(Value::as_str)
            .expect("validated name");
        for dependency in package
            .get("dependencies")
            .and_then(Value::as_array)
            .expect("validated dependencies")
        {
            let dependency = dependency.as_str().expect("validated dependency");
            if !names.contains(dependency) {
                return Err(format!(
                    "Dart dependency package `{name}` references missing package `{dependency}`"
                ));
            }
        }
    }
    Ok(())
}

fn validate_agent_runs<'a>(
    runs: &[AgentRun],
    implementations: &BTreeMap<&'a str, &'a DartBindingRecord>,
    unresolved: &[String],
    intent: Option<&BTreeMap<String, String>>,
) -> Result<(), String> {
    let unresolved = unresolved
        .iter()
        .map(String::as_str)
        .collect::<BTreeSet<_>>();
    let mut successful = BTreeMap::new();
    let mut previous = None;
    for run in runs {
        if !valid_qualified_name(&run.symbol) {
            return Err(format!("Dart agent run symbol `{}` is invalid", run.symbol));
        }
        if previous.is_some_and(|previous: &String| previous >= &run.symbol) {
            return Err("Dart agent runs must be sorted and unique by symbol".to_owned());
        }
        previous = Some(&run.symbol);
        if !matches!(run.adapter.as_str(), "claude" | "codex" | "omp") {
            return Err(format!(
                "Dart agent run `{}` has unsupported adapter `{}`",
                run.symbol, run.adapter
            ));
        }
        if run.adapter_version.is_empty()
            || run.argv_template.is_empty()
            || run.executable.is_empty()
            || run
                .argv_template
                .iter()
                .any(|argument| argument.contains('\0'))
            || run.executable.contains('\0')
        {
            return Err(format!(
                "Dart agent run `{}` has incomplete execution identity",
                run.symbol
            ));
        }
        for (label, digest) in [
            ("executable_hash", run.executable_hash.as_str()),
            ("prompt_hash", run.prompt_hash.as_str()),
            ("implementation_hash", run.implementation_hash.as_str()),
            ("stdout.sha256", run.stdout.sha256.as_str()),
            ("stderr.sha256", run.stderr.sha256.as_str()),
        ] {
            if !valid_digest(digest) {
                return Err(format!(
                    "Dart agent run `{}` has invalid {label}",
                    run.symbol
                ));
            }
        }
        let mut environment_names = BTreeSet::new();
        for name in &run.environment_names {
            if !valid_environment_name(name) || !environment_names.insert(name) {
                return Err(format!(
                    "Dart agent run `{}` has invalid or duplicate environment names",
                    run.symbol
                ));
            }
        }
        validate_agent_status(run)?;

        let succeeded = run.status.exit_code == Some(0);
        match implementations.get(run.symbol.as_str()) {
            Some(implementation)
                if succeeded
                    && implementation.owner == DartOwner::Agent
                    && implementation.content_hash == run.implementation_hash =>
            {
                successful.insert(run.symbol.as_str(), run);
            }
            Some(_) => {
                return Err(format!(
                    "Dart agent run `{}` does not authenticate its current agent-owned implementation",
                    run.symbol
                ));
            }
            None if !succeeded && unresolved.contains(run.symbol.as_str()) => {}
            None => {
                return Err(format!(
                    "Dart agent run `{}` is not tied to a current implementation or unresolved callable",
                    run.symbol
                ));
            }
        }
    }

    for implementation in implementations.values() {
        match implementation.owner {
            DartOwner::Manifest => {
                if successful.contains_key(implementation.cott_symbol.as_str()) {
                    return Err(format!(
                        "manifest-owned Dart implementation `{}` cannot use agent trust",
                        implementation.cott_symbol
                    ));
                }
            }
            DartOwner::Agent => {
                if !successful.contains_key(implementation.cott_symbol.as_str()) {
                    return Err(format!(
                        "agent-owned Dart implementation `{}` lacks matching successful agent provenance",
                        implementation.cott_symbol
                    ));
                }
                if intent
                    .and_then(|hashes| hashes.get(&implementation.cott_symbol))
                    .is_none()
                {
                    return Err(format!(
                        "agent-owned Dart implementation `{}` lacks cott_intent identity",
                        implementation.cott_symbol
                    ));
                }
            }
        }
    }
    Ok(())
}

fn validate_agent_status(run: &AgentRun) -> Result<(), String> {
    let status = &run.status;
    let terminal_channels = u8::from(status.exit_code.is_some())
        + u8::from(status.signal.is_some())
        + u8::from(status.timed_out)
        + u8::from(status.cancelled);
    if terminal_channels != 1 {
        return Err(format!(
            "Dart agent run `{}` must have exactly one terminal status",
            run.symbol
        ));
    }
    Ok(())
}

fn optional_digest<'a>(value: Option<&'a Value>, field: &str) -> Result<Option<&'a str>, String> {
    match value {
        Some(Value::Null) => Ok(None),
        Some(Value::String(value)) if valid_digest(value) => Ok(Some(value)),
        _ => Err(format!(
            "Dart dependencies {field} must be null or a lowercase SHA-256 digest"
        )),
    }
}

fn required_string<'a>(
    object: &'a Map<String, Value>,
    field: &str,
    label: &str,
) -> Result<&'a str, String> {
    object
        .get(field)
        .and_then(Value::as_str)
        .filter(|value| !value.is_empty())
        .ok_or_else(|| format!("{label} {field} must be a nonempty string"))
}

fn require_exact_fields(
    object: &Map<String, Value>,
    fields: &[&str],
    label: &str,
) -> Result<(), String> {
    if object.len() == fields.len() && fields.iter().all(|field| object.contains_key(*field)) {
        Ok(())
    } else {
        Err(format!("{label} has missing or unsupported fields"))
    }
}

fn normalized_relative_path(value: &str) -> Result<PathBuf, &'static str> {
    let path = crate::manifest::normalized_relative_path(value)?;
    if value.split('/').any(str::is_empty) {
        return Err("must be a normalized relative path");
    }
    Ok(path)
}

fn valid_digest(value: &str) -> bool {
    value.strip_prefix("sha256:").is_some_and(|digest| {
        digest.len() == 64
            && digest
                .bytes()
                .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    })
}

fn valid_qualified_name(value: &str) -> bool {
    !value.is_empty() && value.split('.').all(valid_identifier)
}

fn valid_identifier(value: &str) -> bool {
    let mut bytes = value.bytes();
    bytes
        .next()
        .is_some_and(|byte| byte == b'_' || byte.is_ascii_alphabetic())
        && bytes.all(|byte| byte == b'_' || byte.is_ascii_alphanumeric())
}

fn valid_private_dart_identifier(value: &str) -> bool {
    value.starts_with('_')
        && value
            .bytes()
            .all(|byte| byte == b'_' || byte == b'$' || byte.is_ascii_alphanumeric())
}

fn valid_environment_name(value: &str) -> bool {
    let mut bytes = value.bytes();
    bytes
        .next()
        .is_some_and(|byte| byte == b'_' || byte.is_ascii_alphabetic())
        && bytes.all(|byte| byte == b'_' || byte.is_ascii_alphanumeric())
}

fn valid_dependency_package_name(value: &str) -> bool {
    !value.is_empty()
        && value
            .bytes()
            .next()
            .is_some_and(|byte| byte == b'_' || byte.is_ascii_lowercase())
        && value
            .bytes()
            .all(|byte| byte == b'_' || byte.is_ascii_lowercase() || byte.is_ascii_digit())
}

fn valid_semver(value: &str) -> bool {
    let (without_build, build) = value
        .split_once('+')
        .map_or((value, None), |(base, metadata)| (base, Some(metadata)));
    if value.matches('+').count() > 1
        || build.is_some_and(|value| !valid_semver_identifiers(value, false))
    {
        return false;
    }
    let (core, prerelease) = without_build
        .split_once('-')
        .map_or((without_build, None), |(core, pre)| (core, Some(pre)));
    if prerelease.is_some_and(|value| !valid_semver_identifiers(value, true)) {
        return false;
    }
    let mut parts = core.split('.');
    let valid_number = |part: Option<&str>| {
        part.is_some_and(|part| {
            !part.is_empty()
                && (part == "0" || !part.starts_with('0'))
                && part.bytes().all(|byte| byte.is_ascii_digit())
        })
    };
    valid_number(parts.next())
        && valid_number(parts.next())
        && valid_number(parts.next())
        && parts.next().is_none()
}

fn valid_semver_identifiers(value: &str, reject_numeric_leading_zero: bool) -> bool {
    !value.is_empty()
        && value.split('.').all(|identifier| {
            !identifier.is_empty()
                && identifier
                    .bytes()
                    .all(|byte| byte == b'-' || byte.is_ascii_alphanumeric())
                && (!reject_numeric_leading_zero
                    || !identifier.bytes().all(|byte| byte.is_ascii_digit())
                    || identifier == "0"
                    || !identifier.starts_with('0'))
        })
}

fn valid_hosted_source_identity(value: &str) -> bool {
    let Some((registry, archive_hash)) = value.rsplit_once('#') else {
        return false;
    };
    let Some(authority_and_path) = registry.strip_prefix("https://") else {
        return false;
    };
    let authority = authority_and_path.split('/').next().unwrap_or_default();
    !authority.is_empty()
        && !authority.contains('@')
        && !registry.ends_with('/')
        && !registry.contains('?')
        && !registry.contains('#')
        && !registry.contains(char::is_whitespace)
        && registry.is_ascii()
        && valid_digest(archive_hash)
}

fn normalized_generation_identity(snapshot: &DartGenerationSnapshot) -> Result<Value, String> {
    let mut current = serde_json::to_value(snapshot)
        .map_err(|error| format!("serialize Dart generation identity: {error}"))?;
    let object = current
        .as_object_mut()
        .expect("Dart generation snapshot serializes as an object");
    for key in [
        "generation_id",
        "verified",
        "verification",
        "semantic_coverage",
        "agent_runs",
    ] {
        object.remove(key);
    }
    Ok(json!({
        "domain": DART_GENERATION_DOMAIN,
        "schema_version": DART_GENERATION_SCHEMA_VERSION,
        "current": current,
    }))
}

fn canonical_json(value: &Value) -> Result<Vec<u8>, String> {
    let mut bytes = serde_json::to_vec(value).map_err(|error| error.to_string())?;
    bytes.push(b'\n');
    Ok(bytes)
}

fn validate_schema(value: &Value) -> Result<(), String> {
    static SCHEMA: LazyLock<Value> = LazyLock::new(|| {
        serde_json::from_str(include_str!("../../schemas/dart-generation.schema.json"))
            .expect("embedded Dart generation schema is valid JSON")
    });
    let validator = jsonschema::validator_for(&SCHEMA).map_err(|error| error.to_string())?;
    let errors = validator
        .iter_errors(value)
        .map(|error| error.to_string())
        .collect::<Vec<_>>();
    if errors.is_empty() {
        Ok(())
    } else {
        Err(errors.join("; "))
    }
}

fn validate_legacy_schema(value: &Value) -> Result<(), String> {
    static LEGACY_SCHEMA: LazyLock<Value> = LazyLock::new(|| {
        let mut schema: Value =
            serde_json::from_str(include_str!("../../schemas/dart-generation.schema.json"))
                .expect("embedded Dart generation schema is valid JSON");
        schema["$defs"]["snapshot"]["properties"]["canonical_ir_schema"]["const"] =
            json!(LEGACY_CANONICAL_IR_SCHEMA_VERSION);
        schema
    });
    let validator = jsonschema::validator_for(&LEGACY_SCHEMA).map_err(|error| error.to_string())?;
    let errors = validator
        .iter_errors(value)
        .map(|error| error.to_string())
        .collect::<Vec<_>>();
    if errors.is_empty() {
        Ok(())
    } else {
        Err(errors.join("; "))
    }
}
