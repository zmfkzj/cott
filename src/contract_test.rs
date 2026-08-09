use std::sync::LazyLock;

use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::hash::sha256_hex;
use crate::ir::CanonicalIr;

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

/// Derive metadata-only contract test strategies directly from canonical module
/// bytes, preserving the canonical module and declaration order.
pub fn derive_strategies(ir: &CanonicalIr) -> Result<Vec<ContractTestStrategy>, String> {
    let mut strategies = Vec::new();
    for (module_index, module) in ir.modules.iter().enumerate() {
        let value = crate::ir::load(&module.bytes)
            .map_err(|error| format!("module {module_index}: {error}"))?;
        let declarations = value
            .get("declarations")
            .and_then(Value::as_array)
            .ok_or_else(|| format!("module {module_index}: missing declarations"))?;

        for (declaration_index, declaration) in declarations.iter().enumerate() {
            let kind = required_string(declaration, "kind").map_err(|error| {
                format!("module {module_index} declaration {declaration_index}: {error}")
            })?;
            if kind != "function" {
                continue;
            }

            let symbol = required_string(declaration, "name").map_err(|error| {
                format!("module {module_index} declaration {declaration_index}: {error}")
            })?;
            let return_type = required_object(declaration, "return_type")
                .map_err(|error| format!("module {module_index} function {symbol}: {error}"))?;
            let return_kind = required_string(return_type, "kind")
                .map_err(|error| format!("module {module_index} function {symbol}: {error}"))?;
            let contract = required_object(declaration, "contract")
                .map_err(|error| format!("module {module_index} function {symbol}: {error}"))?;
            let effects = required_array(contract, "effects")
                .map_err(|error| format!("module {module_index} function {symbol}: {error}"))?;
            let classification = if return_kind == "primitive"
                && required_string(return_type, "name")
                    .map_err(|error| format!("module {module_index} function {symbol}: {error}"))?
                    == "never"
            {
                Classification::Never
            } else if effects.is_empty() {
                Classification::Pure
            } else {
                Classification::Effectful
            };

            let clauses = required_array(contract, "clauses")
                .map_err(|error| format!("module {module_index} function {symbol}: {error}"))?;
            let mut clause_ids = Vec::with_capacity(clauses.len());
            for (clause_index, clause) in clauses.iter().enumerate() {
                let clause_kind = required_string(clause, "kind").map_err(|error| {
                    format!(
                        "module {module_index} function {symbol} clause {clause_index}: {error}"
                    )
                })?;
                let clause_id = required_field(clause, "clause_id")
                    .and_then(|value| {
                        value.as_u64().ok_or_else(|| {
                            "required field `clause_id` must be a non-negative integer".to_owned()
                        })
                    })
                    .map_err(|error| {
                        format!(
                            "module {module_index} function {symbol} clause {clause_index}: {error}"
                        )
                    })?;
                clause_ids.push(format!("{clause_kind}:{clause_id}"));
            }

            let strategy =
                ContractTestStrategy::new(symbol, &module.bytes, classification, clause_ids);
            strategy.bytes()?;
            strategies.push(strategy);
        }
    }
    Ok(strategies)
}

fn required_field<'a>(value: &'a Value, field: &str) -> Result<&'a Value, String> {
    value
        .get(field)
        .ok_or_else(|| format!("missing required field `{field}`"))
}

fn required_string<'a>(value: &'a Value, field: &str) -> Result<&'a str, String> {
    required_field(value, field)?
        .as_str()
        .ok_or_else(|| format!("required field `{field}` must be a string"))
}

fn required_object<'a>(value: &'a Value, field: &str) -> Result<&'a Value, String> {
    let object = required_field(value, field)?;
    if object.is_object() {
        Ok(object)
    } else {
        Err(format!("required field `{field}` must be an object"))
    }
}

fn required_array<'a>(value: &'a Value, field: &str) -> Result<&'a Vec<Value>, String> {
    required_field(value, field)?
        .as_array()
        .ok_or_else(|| format!("required field `{field}` must be an array"))
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
