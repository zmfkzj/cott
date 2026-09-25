use std::collections::{BTreeMap, BTreeSet};
use std::sync::LazyLock;

use serde::de::Error as _;
use serde::ser::Error as _;
use serde::{Deserialize, Deserializer, Serialize, Serializer};
use serde_json::{Value, json};

use crate::provenance::{AgentRun, SemanticCoverage};
use crate::snapshot_record;

use super::KotlinOwner;

pub const KOTLIN_GENERATION_SCHEMA_VERSION: u32 = 2;
pub const KOTLIN_RUNTIME_ABI_VERSION: u32 = 1;
const KOTLIN_GENERATION_DOMAIN: &str = "cott.kotlin.generation.v2";

/// In-memory Kotlin generation record.
///
/// The on-disk form is the portable snapshot envelope produced by
/// [`snapshot_record`]: `current`/`last_verified` are digest references into a
/// self-contained `snapshots` map, so an identical verified history is stored
/// once.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct KotlinGenerationRecord {
    pub schema_version: u32,
    pub current: KotlinGenerationSnapshot,
    pub last_verified: Option<KotlinGenerationSnapshot>,
}

impl Serialize for KotlinGenerationRecord {
    fn serialize<S: Serializer>(&self, serializer: S) -> Result<S::Ok, S::Error> {
        let current = serde_json::to_value(&self.current).map_err(S::Error::custom)?;
        let last_verified = self
            .last_verified
            .as_ref()
            .map(serde_json::to_value)
            .transpose()
            .map_err(S::Error::custom)?;
        snapshot_record::encode(self.schema_version, &current, last_verified.as_ref())
            .map_err(S::Error::custom)?
            .serialize(serializer)
    }
}

impl<'de> Deserialize<'de> for KotlinGenerationRecord {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        let wire = snapshot_record::deserialize_json(deserializer)?;
        Self::from_wire(&wire).map_err(D::Error::custom)
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct KotlinGenerationSnapshot {
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
    pub implementations: Vec<KotlinBindingRecord>,
    pub managed_files: BTreeMap<String, String>,
    pub unresolved: Vec<String>,
    pub verification: Value,
    pub semantic_coverage: SemanticCoverage,
    pub agent_runs: Vec<AgentRun>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct KotlinBindingRecord {
    pub cott_symbol: String,
    pub target_symbol: String,
    pub source_origin: String,
    pub runtime_origin: String,
    pub content_hash: String,
    pub owner: KotlinOwner,
}

impl KotlinGenerationSnapshot {
    pub fn compute_generation_id(&mut self) -> Result<(), String> {
        validate_snapshot_contents(self)?;
        self.generation_id = snapshot_record::digest(&normalized_generation_identity(self)?)?;
        Ok(())
    }

    /// Content digest of the complete snapshot, including `verified`,
    /// verification evidence and agent runs.
    ///
    /// This is the envelope reference key and the only sound equality test for
    /// two snapshots: `serde_json::Value` equality conflates `-0.0` with `0.0`
    /// and integers with floats inside the opaque `tools`, `contract_surface`
    /// and `verification` payloads.
    pub fn snapshot_digest(&self) -> Result<String, String> {
        let value = serde_json::to_value(self)
            .map_err(|error| format!("serialize Kotlin generation snapshot: {error}"))?;
        snapshot_record::digest(&value)
    }
}

impl KotlinGenerationRecord {
    pub fn parse(bytes: &[u8]) -> Result<Self, String> {
        let wire = snapshot_record::parse_json(bytes)
            .map_err(|error| format!("invalid Kotlin generation JSON: {error}"))?;
        Self::from_wire(&wire)
    }

    pub fn canonical_bytes(&self) -> Result<Vec<u8>, String> {
        self.validate_identities()?;
        let value = serde_json::to_value(self)
            .map_err(|error| format!("serialize Kotlin generation record: {error}"))?;
        validate_schema(&value)?;
        canonical_json(&value)
    }
    /// Only the explicit emit cutover may inspect a sealed IR-8 record. Normal
    /// record parsing continues to require the current canonical IR schema.
    pub(crate) fn convert_legacy_for_emit(bytes: &[u8]) -> Result<Option<Self>, String> {
        let wire = snapshot_record::parse_json(bytes)
            .map_err(|error| format!("invalid Kotlin generation JSON: {error}"))?;
        let (current, last_verified) =
            snapshot_record::decode_legacy(&wire, KOTLIN_GENERATION_SCHEMA_VERSION)?;
        let mut record = Self {
            schema_version: KOTLIN_GENERATION_SCHEMA_VERSION,
            current: serde_json::from_value(current)
                .map_err(|error| format!("invalid legacy Kotlin generation record: {error}"))?,
            last_verified: last_verified
                .map(serde_json::from_value)
                .transpose()
                .map_err(|error| format!("invalid legacy Kotlin generation record: {error}"))?,
        };
        if record.current.canonical_ir_schema != 8 {
            return Ok(None);
        }
        validate_legacy_snapshot_identity(&record.current)?;
        if let Some(previous) = &record.last_verified {
            if !previous.verified || previous.project_name != record.current.project_name {
                return Err("invalid legacy Kotlin last_verified snapshot".to_owned());
            }
            validate_legacy_snapshot_identity(previous)?;
        }
        if record.current.verified {
            let previous = record
                .last_verified
                .as_ref()
                .ok_or("verified legacy Kotlin current snapshot requires last_verified")?;
            if previous.snapshot_digest()? != record.current.snapshot_digest()? {
                return Err("verified legacy Kotlin current differs from last_verified".to_owned());
            }
        }
        record.current.canonical_ir_schema = crate::provenance::CANONICAL_IR_SCHEMA_VERSION;
        record.current.verified = false;
        record.current.verification = Value::Null;
        record.current.semantic_coverage = SemanticCoverage::default();
        record.current.compute_generation_id()?;
        record.last_verified = None;
        record.canonical_bytes()?;
        Ok(Some(record))
    }

    fn from_wire(wire: &Value) -> Result<Self, String> {
        validate_schema(wire)?;
        let (current, last_verified) =
            snapshot_record::decode(wire, KOTLIN_GENERATION_SCHEMA_VERSION)?;
        let record = Self {
            schema_version: KOTLIN_GENERATION_SCHEMA_VERSION,
            current: serde_json::from_value(current)
                .map_err(|error| format!("invalid Kotlin generation record: {error}"))?,
            last_verified: last_verified
                .map(serde_json::from_value)
                .transpose()
                .map_err(|error| format!("invalid Kotlin generation record: {error}"))?,
        };
        record.validate_identities()?;
        Ok(record)
    }

    /// True when a verified history exists and is byte-identical to `current`.
    ///
    /// Compares full snapshot digests so the envelope stores exactly one
    /// snapshot for a certified record.
    pub fn current_is_last_verified(&self) -> Result<bool, String> {
        let Some(last_verified) = &self.last_verified else {
            return Ok(false);
        };
        Ok(last_verified.snapshot_digest()? == self.current.snapshot_digest()?)
    }

    fn validate_identities(&self) -> Result<(), String> {
        if self.schema_version != KOTLIN_GENERATION_SCHEMA_VERSION {
            return Err(format!(
                "Kotlin generation schema version must be {KOTLIN_GENERATION_SCHEMA_VERSION}"
            ));
        }
        validate_snapshot_identity(&self.current)?;
        if let Some(snapshot) = &self.last_verified {
            if !snapshot.verified {
                return Err("Kotlin last_verified snapshot is not verified".to_owned());
            }
            validate_snapshot_identity(snapshot)?;
            if snapshot.project_name != self.current.project_name {
                return Err(
                    "Kotlin last_verified snapshot belongs to a different project".to_owned(),
                );
            }
        }
        if self.current.verified && !self.current_is_last_verified()? {
            return Err(
                "verified Kotlin current snapshot must equal last_verified snapshot".to_owned(),
            );
        }
        Ok(())
    }
}

fn validate_snapshot_identity(snapshot: &KotlinGenerationSnapshot) -> Result<(), String> {
    validate_snapshot_contents(snapshot)?;
    if let Some(strategies) = snapshot.verification.pointer("/contract_tests/strategies") {
        let strategies = strategies
            .as_array()
            .ok_or("Kotlin contract strategies must be an array")?;
        if strategies.iter().any(|strategy| {
            strategy.get("schema_version").and_then(Value::as_u64)
                != Some(u64::from(
                    crate::provenance::CONTRACT_STRATEGY_SCHEMA_VERSION,
                ))
        }) {
            return Err(format!(
                "Kotlin contract strategy schema must be {}",
                crate::provenance::CONTRACT_STRATEGY_SCHEMA_VERSION
            ));
        }
    }
    if !valid_digest(&snapshot.generation_id) {
        return Err("Kotlin generation_id must be a lowercase SHA-256 digest".to_owned());
    }
    let mut expected = snapshot.clone();
    expected.compute_generation_id()?;
    if expected.generation_id != snapshot.generation_id {
        return Err(format!(
            "Kotlin generation identity mismatch: expected {}, got {}",
            expected.generation_id, snapshot.generation_id
        ));
    }
    Ok(())
}

fn validate_legacy_snapshot_identity(snapshot: &KotlinGenerationSnapshot) -> Result<(), String> {
    if snapshot.canonical_ir_schema != 8 {
        return Err("legacy Kotlin canonical IR schema must be 8".to_owned());
    }
    let mut shape = snapshot.clone();
    shape.canonical_ir_schema = crate::provenance::CANONICAL_IR_SCHEMA_VERSION;
    validate_snapshot_contents(&shape)?;
    if !valid_digest(&snapshot.generation_id)
        || snapshot_record::digest(&normalized_generation_identity(snapshot)?)?
            != snapshot.generation_id
    {
        return Err("legacy Kotlin generation identity mismatch".to_owned());
    }
    if snapshot.verified {
        let strategies = snapshot
            .verification
            .pointer("/contract_tests/strategies")
            .and_then(Value::as_array)
            .ok_or("verified legacy Kotlin snapshot has no contract strategies")?;
        if strategies
            .iter()
            .any(|strategy| strategy.get("schema_version").and_then(Value::as_u64) != Some(5))
        {
            return Err("legacy Kotlin contract strategy schema must be 5".to_owned());
        }
    }
    Ok(())
}

fn validate_snapshot_contents(snapshot: &KotlinGenerationSnapshot) -> Result<(), String> {
    if snapshot.target != "kotlin" {
        return Err("Kotlin generation target must be `kotlin`".to_owned());
    }
    if snapshot.compiler_version != env!("CARGO_PKG_VERSION") {
        return Err(format!(
            "Kotlin generation compiler_version must be {}",
            env!("CARGO_PKG_VERSION")
        ));
    }
    if snapshot.canonical_ir_schema != crate::provenance::CANONICAL_IR_SCHEMA_VERSION {
        return Err(format!(
            "Kotlin canonical IR schema must be {}",
            crate::provenance::CANONICAL_IR_SCHEMA_VERSION
        ));
    }
    if snapshot.runtime_abi != KOTLIN_RUNTIME_ABI_VERSION {
        return Err(format!(
            "Kotlin runtime ABI must be {KOTLIN_RUNTIME_ABI_VERSION}"
        ));
    }
    if !crate::manifest::valid_kotlin_project_name(&snapshot.project_name) {
        return Err(
            "Kotlin generation project_name must be normalized lowercase kebab-case".to_owned(),
        );
    }
    if crate::manifest::parse_api_version(&snapshot.project_version).is_none() {
        return Err(
            "Kotlin generation project_version must be a restricted x.y.z version".to_owned(),
        );
    }
    if !snapshot.tools.is_object() {
        return Err("Kotlin generation tools must be an object".to_owned());
    }
    crate::intent::recorded_fingerprints(&snapshot.tools)?;
    if !snapshot.contract_surface.is_object() {
        return Err("Kotlin generation contract_surface must be an object".to_owned());
    }
    if snapshot.verified != snapshot.verification.is_object() {
        return Err(
            "Kotlin generation verification evidence must be present exactly when verified"
                .to_owned(),
        );
    }
    if snapshot.verified && !snapshot.unresolved.is_empty() {
        return Err("verified Kotlin generation snapshot has unresolved callables".to_owned());
    }

    validate_path_hashes("input", &snapshot.inputs)?;
    validate_ir_hashes(&snapshot.ir)?;
    validate_public_symbols(&snapshot.public_symbols)?;
    validate_implementations(&snapshot.implementations)?;
    validate_path_hashes("managed file", &snapshot.managed_files)?;
    validate_unresolved(&snapshot.unresolved)?;
    crate::provenance::validate_semantic_coverage(&snapshot.semantic_coverage)?;
    validate_agent_runs(&snapshot.agent_runs)?;
    Ok(())
}

fn validate_path_hashes(label: &str, entries: &BTreeMap<String, String>) -> Result<(), String> {
    for (path, digest) in entries {
        normalized_relative_path(path)
            .map_err(|message| format!("Kotlin generation {label} path `{path}` {message}"))?;
        if !valid_digest(digest) {
            return Err(format!(
                "Kotlin generation {label} `{path}` has an invalid SHA-256 digest"
            ));
        }
    }
    Ok(())
}

fn validate_ir_hashes(ir: &BTreeMap<String, String>) -> Result<(), String> {
    for (module, digest) in ir {
        if !valid_qualified_name(module) {
            return Err(format!(
                "Kotlin generation IR module `{module}` is not a canonical symbol"
            ));
        }
        if !valid_digest(digest) {
            return Err(format!(
                "Kotlin generation IR module `{module}` has an invalid SHA-256 digest"
            ));
        }
    }
    Ok(())
}

fn validate_public_symbols(symbols: &BTreeMap<String, Vec<String>>) -> Result<(), String> {
    for (module, names) in symbols {
        if !valid_qualified_name(module) {
            return Err(format!(
                "Kotlin public symbol module `{module}` is not a canonical symbol"
            ));
        }
        let mut previous = None;
        for name in names {
            if !valid_identifier(name) {
                return Err(format!(
                    "Kotlin public symbol `{module}.{name}` is not a canonical identifier"
                ));
            }
            if previous.is_some_and(|previous: &String| previous >= name) {
                return Err(format!(
                    "Kotlin public symbols for `{module}` must be sorted and unique"
                ));
            }
            previous = Some(name);
        }
    }
    Ok(())
}

fn validate_implementations(implementations: &[KotlinBindingRecord]) -> Result<(), String> {
    let mut previous = None;
    for implementation in implementations {
        if !valid_qualified_name(&implementation.cott_symbol) {
            return Err(format!(
                "Kotlin implementation has invalid Cott symbol `{}`",
                implementation.cott_symbol
            ));
        }
        if previous.is_some_and(|previous: &String| previous >= &implementation.cott_symbol) {
            return Err(
                "Kotlin implementations must be sorted and unique by Cott symbol".to_owned(),
            );
        }
        previous = Some(&implementation.cott_symbol);
        if !crate::manifest::valid_kotlin_fqn(&implementation.target_symbol) {
            return Err(format!(
                "Kotlin implementation `{}` has invalid target symbol `{}`",
                implementation.cott_symbol, implementation.target_symbol
            ));
        }
        let source =
            normalized_relative_path(&implementation.source_origin).map_err(|message| {
                format!(
                    "Kotlin implementation `{}` source_origin {message}",
                    implementation.cott_symbol
                )
            })?;
        if source.extension().and_then(|extension| extension.to_str()) != Some("kt") {
            return Err(format!(
                "Kotlin implementation `{}` source_origin must name a .kt file",
                implementation.cott_symbol
            ));
        }
        let runtime =
            normalized_relative_path(&implementation.runtime_origin).map_err(|message| {
                format!(
                    "Kotlin implementation `{}` runtime_origin {message}",
                    implementation.cott_symbol
                )
            })?;
        if !runtime.starts_with("kotlin")
            || runtime.extension().and_then(|extension| extension.to_str()) != Some("kt")
        {
            return Err(format!(
                "Kotlin implementation `{}` runtime_origin must name a .kt file below kotlin/",
                implementation.cott_symbol
            ));
        }
        if !valid_digest(&implementation.content_hash) {
            return Err(format!(
                "Kotlin implementation `{}` has an invalid content hash",
                implementation.cott_symbol
            ));
        }
    }
    Ok(())
}

fn validate_unresolved(unresolved: &[String]) -> Result<(), String> {
    let mut previous = None;
    for symbol in unresolved {
        if !valid_qualified_name(symbol) {
            return Err(format!("Kotlin unresolved symbol `{symbol}` is invalid"));
        }
        if previous.is_some_and(|previous: &String| previous >= symbol) {
            return Err("Kotlin unresolved symbols must be sorted and unique".to_owned());
        }
        previous = Some(symbol);
    }
    Ok(())
}

fn validate_agent_runs(runs: &[AgentRun]) -> Result<(), String> {
    for run in runs {
        if !valid_qualified_name(&run.symbol) {
            return Err(format!(
                "Kotlin agent run symbol `{}` is invalid",
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
                    "Kotlin agent run `{}` has invalid {label}",
                    run.symbol
                ));
            }
        }
        let mut names = BTreeSet::new();
        for name in &run.environment_names {
            if !valid_environment_name(name) || !names.insert(name) {
                return Err(format!(
                    "Kotlin agent run `{}` has invalid or duplicate environment names",
                    run.symbol
                ));
            }
        }
    }
    Ok(())
}

fn normalized_relative_path(value: &str) -> Result<std::path::PathBuf, &'static str> {
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

fn valid_environment_name(value: &str) -> bool {
    let mut bytes = value.bytes();
    bytes
        .next()
        .is_some_and(|byte| byte == b'_' || byte.is_ascii_alphabetic())
        && bytes.all(|byte| byte == b'_' || byte.is_ascii_alphanumeric())
}

fn normalized_generation_identity(snapshot: &KotlinGenerationSnapshot) -> Result<Value, String> {
    let mut current = serde_json::to_value(snapshot)
        .map_err(|error| format!("serialize Kotlin generation identity: {error}"))?;
    let object = current
        .as_object_mut()
        .expect("Kotlin generation snapshot serializes as an object");
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
        "domain": KOTLIN_GENERATION_DOMAIN,
        "schema_version": KOTLIN_GENERATION_SCHEMA_VERSION,
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
        serde_json::from_str(include_str!("../../schemas/kotlin-generation.schema.json"))
            .expect("embedded Kotlin generation schema is valid JSON")
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
