use std::collections::{BTreeMap, BTreeSet};
use std::sync::LazyLock;

use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::hash::sha256_hex;

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct GenerationRecord {
    pub schema_version: u32,
    pub current: GenerationSnapshot,
    pub last_verified: Option<GenerationSnapshot>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct GenerationSnapshot {
    pub generation_id: String,
    pub verified: bool,
    pub inputs: Value,
    pub tools: Value,
    pub ir: Value,
    pub contract_surface: Value,
    pub public_python_symbols: Value,
    pub implementations: Value,
    pub dependencies: Value,
    pub managed_files: BTreeMap<String, String>,
    pub unresolved: Vec<String>,
    pub verification: Value,
    pub agent_runs: Vec<AgentRun>,
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
        let mut value = serde_json::to_value(&*self).map_err(|error| error.to_string())?;
        let object = value
            .as_object_mut()
            .expect("generation snapshot serializes as object");
        for key in ["generation_id", "verified", "verification", "agent_runs"] {
            object.remove(key);
        }
        self.generation_id = format!("sha256:{}", sha256_hex(&canonical_json(&value)?));
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
            Some("function") => {
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
