use std::collections::{BTreeMap, BTreeSet};
use std::sync::LazyLock;

use serde::{Deserialize, Serialize};
use serde_json::{Value, json};

use crate::hash::sha256_hex;

pub const GENERATION_SCHEMA_VERSION: u32 = 2;
pub const CANONICAL_IR_SCHEMA_VERSION: u32 = 5;
pub const RUNTIME_ABI_VERSION: u32 = 2;

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct GenerationCompatibility {
    pub generation_schema: u32,
    pub canonical_ir_schema: u32,
    pub runtime_abi: u32,
}

impl GenerationCompatibility {
    pub const fn current() -> Self {
        Self {
            generation_schema: GENERATION_SCHEMA_VERSION,
            canonical_ir_schema: CANONICAL_IR_SCHEMA_VERSION,
            runtime_abi: RUNTIME_ABI_VERSION,
        }
    }

    pub const fn is_current(&self) -> bool {
        self.generation_schema == GENERATION_SCHEMA_VERSION
            && self.canonical_ir_schema == CANONICAL_IR_SCHEMA_VERSION
            && self.runtime_abi == RUNTIME_ABI_VERSION
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct GenerationRecord {
    pub schema_version: u32,
    pub current: GenerationSnapshot,
    pub last_verified: Option<GenerationSnapshot>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SourceSpan {
    pub start_byte: u64,
    pub end_byte: u64,
    pub start_line: u64,
    pub start_column: u64,
    pub end_line: u64,
    pub end_column: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum UnresolvedKind {
    Function,
    AsyncFunction,
    ImplMethod,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct UnresolvedRecord {
    pub cott_symbol: String,
    pub kind: UnresolvedKind,
    pub span: SourceSpan,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct GenerationSnapshot {
    pub generation_id: String,
    pub verified: bool,
    pub project_version: String,
    pub compatibility: GenerationCompatibility,
    pub inputs: Value,
    pub tools: Value,
    pub ir: Value,
    pub contract_surface: Value,
    pub public_python_symbols: Value,
    pub implementations: Value,
    pub dependencies: Value,
    pub managed_files: BTreeMap<String, String>,
    pub unresolved: Vec<UnresolvedRecord>,
    pub verification: Value,
    pub agent_runs: Vec<AgentRun>,
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ImplementationComparison {
    pub baseline_generation_id: Option<String>,
    pub status: &'static str,
    pub entries: Vec<ImplementationComparisonEntry>,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ImplementationComparisonEntry {
    pub cott_symbol: String,
    pub status: &'static str,
    pub changed_fields: BTreeMap<String, ImplementationFieldChange>,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ImplementationFieldChange {
    pub before: Value,
    pub after: Value,
}

pub fn compare_implementation_identities(
    baseline: Option<&GenerationSnapshot>,
    current: &GenerationSnapshot,
) -> ImplementationComparison {
    let Some(baseline) = baseline else {
        return ImplementationComparison {
            baseline_generation_id: None,
            status: "no_baseline",
            entries: Vec::new(),
        };
    };
    let baseline_id = baseline.generation_id.clone();
    let baseline = implementation_identity_index(&baseline.implementations);
    let current = implementation_identity_index(&current.implementations);
    let symbols = baseline
        .keys()
        .chain(current.keys())
        .cloned()
        .collect::<BTreeSet<_>>();
    let entries = symbols
        .into_iter()
        .map(|cott_symbol| {
            let baseline = baseline.get(&cott_symbol);
            let current = current.get(&cott_symbol);
            let status = match (baseline, current) {
                (None, Some(_)) => "added",
                (Some(_), None) => "removed",
                (Some(baseline), Some(current)) if baseline == current => "unchanged",
                (Some(_), Some(_)) => "changed",
                (None, None) => unreachable!("symbol belongs to a comparison index"),
            };
            ImplementationComparisonEntry {
                cott_symbol,
                status,
                changed_fields: implementation_field_changes(baseline, current),
            }
        })
        .collect();
    ImplementationComparison {
        baseline_generation_id: Some(baseline_id),
        status: "compared",
        entries,
    }
}

fn implementation_field_changes(
    baseline: Option<&BTreeMap<String, Value>>,
    current: Option<&BTreeMap<String, Value>>,
) -> BTreeMap<String, ImplementationFieldChange> {
    baseline
        .into_iter()
        .flat_map(|identity| identity.keys())
        .chain(current.into_iter().flat_map(|identity| identity.keys()))
        .cloned()
        .collect::<BTreeSet<_>>()
        .into_iter()
        .filter_map(|field| {
            let before = baseline.and_then(|identity| identity.get(&field)).cloned();
            let after = current.and_then(|identity| identity.get(&field)).cloned();
            ((before != after) || baseline.is_none() || current.is_none()).then(|| {
                (
                    field,
                    ImplementationFieldChange {
                        before: before.unwrap_or(Value::Null),
                        after: after.unwrap_or(Value::Null),
                    },
                )
            })
        })
        .collect()
}

fn implementation_identity_index(value: &Value) -> BTreeMap<String, BTreeMap<String, Value>> {
    value
        .as_array()
        .into_iter()
        .flatten()
        .filter_map(normalized_implementation_identity)
        .collect()
}

fn normalized_implementation_identity(
    implementation: &Value,
) -> Option<(String, BTreeMap<String, Value>)> {
    let implementation = implementation.as_object()?;
    let symbol = implementation.get("cott_symbol")?.as_str()?.to_owned();
    let mut identity = BTreeMap::new();
    for field in [
        "owner",
        "python_symbol",
        "source_origin",
        "runtime_origin",
        "content_hash",
    ] {
        identity.insert(field.to_owned(), implementation.get(field)?.clone());
    }
    identity.insert(
        "kind".to_owned(),
        implementation
            .get("kind")
            .cloned()
            .unwrap_or_else(|| Value::String("function".to_owned())),
    );
    for field in ["concrete", "method"] {
        identity.insert(
            field.to_owned(),
            implementation.get(field).cloned().unwrap_or(Value::Null),
        );
    }
    Some((symbol, identity))
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct AgentRun {
    pub symbol: String,
    pub adapter: String,
    pub adapter_version: String,
    pub argv_template: Vec<String>,
    pub executable: String,
    pub executable_hash: String,
    pub prompt_hash: String,
    pub implementation_hash: String,
    pub environment_names: Vec<String>,
    pub duration_ms: u64,
    pub status: AgentStatus,
    pub stdout: StreamDigest,
    pub stderr: StreamDigest,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct AgentStatus {
    pub exit_code: Option<i32>,
    pub signal: Option<i32>,
    pub timed_out: bool,
    pub cancelled: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct StreamDigest {
    pub bytes: u64,
    pub sha256: String,
    pub truncated: bool,
}

impl GenerationSnapshot {
    pub fn compute_generation_id(&mut self) -> Result<(), String> {
        let identity = canonical_json(&normalized_generation_identity(self)?)?;
        self.generation_id = format!("sha256:{}", sha256_hex(&identity));
        Ok(())
    }
}

impl GenerationRecord {
    pub fn canonical_bytes(&self) -> Result<Vec<u8>, String> {
        self.validate_identities()?;
        let value = serde_json::to_value(self).map_err(|error| error.to_string())?;
        validate(&value)?;
        canonical_json(&value)
    }

    pub fn parse(bytes: &[u8]) -> Result<Self, String> {
        let value: Value = serde_json::from_slice(bytes).map_err(|error| error.to_string())?;
        validate(&value)?;
        let record: Self = serde_json::from_value(value).map_err(|error| error.to_string())?;
        record.validate_identities()?;
        Ok(record)
    }

    fn validate_identities(&self) -> Result<(), String> {
        if self.schema_version != GENERATION_SCHEMA_VERSION {
            return Err(format!(
                "generation schema version must be {GENERATION_SCHEMA_VERSION}"
            ));
        }
        validate_snapshot_identity(&self.current)?;
        if let Some(snapshot) = &self.last_verified {
            if !snapshot.verified {
                return Err("last_verified snapshot is not verified".to_owned());
            }
            validate_snapshot_identity(snapshot)?;
        }
        Ok(())
    }
}

fn validate_snapshot_identity(snapshot: &GenerationSnapshot) -> Result<(), String> {
    if crate::manifest::parse_api_version(&snapshot.project_version).is_none() {
        return Err("generation project_version must be a restricted x.y.z version".to_owned());
    }
    if !snapshot.compatibility.is_current() {
        return Err(format!(
            "generation compatibility must be {GENERATION_SCHEMA_VERSION}/{CANONICAL_IR_SCHEMA_VERSION}/{RUNTIME_ABI_VERSION}"
        ));
    }
    validate_unresolved_records(&snapshot.unresolved)?;
    validate_implementation_records(&snapshot.implementations)?;
    let mut expected = snapshot.clone();
    expected.compute_generation_id()?;
    if expected.generation_id == snapshot.generation_id {
        Ok(())
    } else {
        Err(format!(
            "generation identity mismatch: expected {}, got {}",
            expected.generation_id, snapshot.generation_id
        ))
    }
}

fn normalized_generation_identity(snapshot: &GenerationSnapshot) -> Result<Value, String> {
    let mut current = serde_json::to_value(snapshot).map_err(|error| error.to_string())?;
    let object = current
        .as_object_mut()
        .expect("generation snapshot serializes as object");
    for key in ["generation_id", "verified", "verification", "agent_runs"] {
        object.remove(key);
    }
    Ok(json!({
        "domain": "cott.generation.v2",
        "schema_version": GENERATION_SCHEMA_VERSION,
        "current": current,
    }))
}

fn validate_unresolved_records(unresolved: &[UnresolvedRecord]) -> Result<(), String> {
    let mut symbols = BTreeSet::new();
    for record in unresolved {
        if record.cott_symbol.is_empty() {
            return Err("generation unresolved record has an empty cott_symbol".to_owned());
        }
        if !symbols.insert(&record.cott_symbol) {
            return Err(format!(
                "generation record contains duplicate unresolved callable `{}`",
                record.cott_symbol
            ));
        }
        if record.span.end_byte < record.span.start_byte
            || record.span.end_line < record.span.start_line
            || record.span.start_line == 0
            || record.span.start_column == 0
            || record.span.end_line == 0
            || record.span.end_column == 0
        {
            return Err(format!(
                "generation unresolved callable `{}` has an invalid span",
                record.cott_symbol
            ));
        }
    }
    Ok(())
}

fn validate_implementation_records(implementations: &Value) -> Result<(), String> {
    let implementations = implementations
        .as_array()
        .ok_or("generation implementations must be an array")?;
    let mut symbols = BTreeSet::new();
    for implementation in implementations {
        let object = implementation
            .as_object()
            .ok_or("generation implementation must be an object")?;
        let symbol = object
            .get("cott_symbol")
            .and_then(Value::as_str)
            .ok_or("generation implementation is missing cott_symbol")?;
        if !symbols.insert(symbol) {
            return Err(format!(
                "generation record contains duplicate implementation `{symbol}`"
            ));
        }
        match object.get("kind").and_then(Value::as_str) {
            None if object.get("concrete").is_none()
                && object.get("method").is_none()
                && !object
                    .get("python_symbol")
                    .and_then(Value::as_str)
                    .and_then(|value| value.rsplit_once(':').map(|(_, function)| function))
                    .is_some_and(|function| function.starts_with("_cott_impl_")) => {}
            Some("function" | "async_function") => {
                if object.get("concrete") != Some(&Value::Null)
                    || object.get("method") != Some(&Value::Null)
                {
                    return Err(format!(
                        "function implementation `{symbol}` must not name a concrete or method"
                    ));
                }
            }
            Some("impl_method") => {
                let concrete = object
                    .get("concrete")
                    .and_then(Value::as_str)
                    .filter(|value| !value.is_empty())
                    .ok_or_else(|| {
                        format!("implementation method `{symbol}` is missing its concrete class")
                    })?;
                let method = object
                    .get("method")
                    .and_then(Value::as_str)
                    .filter(|value| !value.is_empty())
                    .ok_or_else(|| {
                        format!("implementation method `{symbol}` is missing its method name")
                    })?;
                if !symbol.ends_with(&format!(".{concrete}.{method}")) {
                    return Err(format!(
                        "implementation method `{symbol}` does not match `{concrete}.{method}`"
                    ));
                }
            }
            _ => {
                return Err(format!(
                    "generation implementation `{symbol}` has an invalid kind"
                ));
            }
        }
    }
    Ok(())
}

fn canonical_json(value: &Value) -> Result<Vec<u8>, String> {
    let mut bytes = serde_json::to_vec(value).map_err(|error| error.to_string())?;
    bytes.push(b'\n');
    Ok(bytes)
}

fn validate(value: &Value) -> Result<(), String> {
    static SCHEMA: LazyLock<Value> = LazyLock::new(|| {
        serde_json::from_str(include_str!("../schemas/generation.schema.json"))
            .expect("embedded generation schema is valid JSON")
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
