use std::sync::LazyLock;

use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::hash::sha256_hex;

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum Classification {
    Pure,
    Effectful,
    Never,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ContractTestStrategy {
    pub schema_version: u32,
    pub symbol: String,
    pub seed: String,
    pub candidate_limit: u32,
    pub container_length_limit: u32,
    pub json_depth_limit: u32,
    pub classification: Classification,
    pub clause_ids: Vec<String>,
}

impl ContractTestStrategy {
    pub fn new(
        symbol: impl Into<String>,
        ir_bytes: &[u8],
        classification: Classification,
        clause_ids: Vec<String>,
    ) -> Self {
        Self {
            schema_version: 1,
            symbol: symbol.into(),
            seed: format!("sha256:{}", sha256_hex(ir_bytes)),
            candidate_limit: 64,
            container_length_limit: 3,
            json_depth_limit: 4,
            classification,
            clause_ids,
        }
    }

    pub fn bytes(&self) -> Result<Vec<u8>, String> {
        let value = serde_json::to_value(self).map_err(|error| error.to_string())?;
        validate(&value)?;
        let mut bytes = serde_json::to_vec(&value).map_err(|error| error.to_string())?;
        bytes.push(b'\n');
        Ok(bytes)
    }
}

fn validate(value: &Value) -> Result<(), String> {
    static SCHEMA: LazyLock<Value> = LazyLock::new(|| {
        serde_json::from_str(include_str!("../schemas/contract-test.schema.json"))
            .expect("embedded contract-test schema is valid JSON")
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
