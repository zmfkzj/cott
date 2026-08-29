use std::collections::BTreeMap;
use std::collections::BTreeSet;
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::LazyLock;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::hash::sha256_hex;
use crate::ir::CanonicalIr;
use crate::manifest::{RuntimeValidation, VerificationConfig};
use crate::sandbox::{BindMounts, NetworkAccess, ResourceLimits, SandboxError, SandboxSpec, run};

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "lowercase")]
pub enum Classification {
    Pure,
    Effectful,
    Never,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum ContractObligationRole {
    Success,
    ConditionalError,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ContractObligation {
    pub clause_id: String,
    pub role: ContractObligationRole,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ScenarioLimits {
    pub scenario_timeout_ms: u32,
    pub filesystem_bytes: u64,
    pub filesystem_files: u32,
    pub http_body_bytes: u64,
    pub http_requests: u32,
    pub http_redirects: u32,
    pub transcript_events: u32,
}

impl ScenarioLimits {
    fn from_verification(verification: &VerificationConfig) -> Self {
        let fixtures = &verification.fixtures;
        Self {
            scenario_timeout_ms: fixtures.scenario_timeout_ms,
            filesystem_bytes: fixtures.filesystem_bytes,
            filesystem_files: fixtures.filesystem_files,
            http_body_bytes: fixtures.http_body_bytes,
            http_requests: fixtures.http_requests,
            http_redirects: fixtures.http_redirects,
            transcript_events: fixtures.transcript_events,
        }
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ScenarioStrategy {
    pub id: String,
    pub required_effects: Vec<String>,
    pub fixtures: Vec<Value>,
    pub steps: Vec<Value>,
    pub lifecycle_limit: u32,
    pub limits: ScenarioLimits,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ContractTestStrategy {
    pub schema_version: u32,
    pub symbol: String,
    pub seed: String,
    pub proof_node_limit: u32,
    pub proof_branch_limit: u32,
    pub candidate_limit: u32,
    pub node_limit: u32,
    pub container_length_limit: u32,
    pub json_depth_limit: u32,
    pub lifecycle_limit: u32,
    pub callable_kind: String,
    pub return_kind: String,
    pub classification: Classification,
    pub clause_ids: Vec<String>,
    pub obligations: Vec<ContractObligation>,
    pub scenario: Option<ScenarioStrategy>,
}

impl ContractTestStrategy {
    pub fn new(
        symbol: impl Into<String>,
        ir_bytes: &[u8],
        callable_kind: impl Into<String>,
        classification: Classification,
        clause_ids: Vec<String>,
        verification: &VerificationConfig,
    ) -> Self {
        Self {
            schema_version: crate::provenance::CONTRACT_STRATEGY_SCHEMA_VERSION,
            symbol: symbol.into(),
            seed: format!("sha256:{}", sha256_hex(ir_bytes)),
            proof_node_limit: verification.proof_node_limit,
            proof_branch_limit: verification.proof_branch_limit,
            candidate_limit: verification.candidate_limit,
            node_limit: 64,
            container_length_limit: 3,
            json_depth_limit: 4,
            lifecycle_limit: verification.lifecycle_limit,
            callable_kind: callable_kind.into(),
            return_kind: "value".to_owned(),
            classification,
            clause_ids,
            obligations: Vec::new(),
            scenario: None,
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

/// Derive metadata-only contract test strategies from canonical IR v8 module
/// bytes, preserving canonical module, declaration, and selected-slot order.
pub fn derive_strategies(
    ir: &CanonicalIr,
    verification: &VerificationConfig,
) -> Result<Vec<ContractTestStrategy>, String> {
    Ok(derive_strategy_entries(ir, verification)?
        .into_iter()
        .map(|(strategy, _)| strategy)
        .collect())
}

fn derive_strategy_entries(
    ir: &CanonicalIr,
    verification: &VerificationConfig,
) -> Result<Vec<(ContractTestStrategy, Option<String>)>, String> {
    let modules = ir
        .modules
        .iter()
        .enumerate()
        .map(|(index, module)| {
            crate::ir::load(&module.bytes).map_err(|error| format!("module {index}: {error}"))
        })
        .collect::<Result<Vec<_>, _>>()?;
    let mut strategies = Vec::new();
    for (module_index, (module, value)) in ir.modules.iter().zip(&modules).enumerate() {
        let declarations = required_array(value, "declarations")
            .map_err(|error| format!("module {module_index}: {error}"))?;

        for (declaration_index, declaration) in declarations.iter().enumerate() {
            let kind = required_string(declaration, "kind").map_err(|error| {
                format!("module {module_index} declaration {declaration_index}: {error}")
            })?;
            let context = format!("module {module_index} declaration {declaration_index}");
            match kind {
                "function" => {
                    let symbol = required_string(declaration, "name")
                        .map_err(|error| format!("{context}: {error}"))?;
                    let callable_kind = required_string(declaration, "callable_kind")
                        .map_err(|error| format!("{context} function {symbol}: {error}"))?;
                    if !matches!(callable_kind, "sync" | "async") {
                        return Err(format!(
                            "{context} function {symbol}: unsupported callable_kind `{callable_kind}`"
                        ));
                    }
                    let return_type = required_object(declaration, "return_type")
                        .map_err(|error| format!("{context} function {symbol}: {error}"))?;
                    let contract = required_object(declaration, "contract")
                        .map_err(|error| format!("{context} function {symbol}: {error}"))?;
                    let classification = classify(
                        return_type,
                        required_array(contract, "effects")
                            .map_err(|error| format!("{context} function {symbol}: {error}"))?,
                        &format!("{context} function {symbol}"),
                    )?;
                    let clause_ids = contract_clause_ids(
                        contract,
                        &["clauses"],
                        &format!("{context} function {symbol}"),
                    )?;

                    let mut strategy = ContractTestStrategy::new(
                        symbol,
                        &module.bytes,
                        callable_kind,
                        classification,
                        clause_ids,
                        verification,
                    );
                    strategy.return_kind = protocol_return_kind(return_type)?.to_owned();
                    strategy.obligations = contract_obligations(
                        contract,
                        &["clauses"],
                        return_type,
                        &format!("{context} function {symbol}"),
                    )?;
                    strategy.bytes()?;
                    strategies.push((strategy, None));
                }
                "impl" => {
                    let name = required_string(declaration, "name")
                        .map_err(|error| format!("{context}: {error}"))?;
                    let invariants = invariant_clause_ids(
                        required_array(declaration, "invariants")
                            .map_err(|error| format!("{context} impl {name}: {error}"))?,
                        &format!("{context} impl {name}"),
                    )?;
                    let init_symbol = format!("{name}.init");
                    let mut init_clause_ids = match required_field(declaration, "init")
                        .map_err(|error| format!("{context} impl {name}: {error}"))?
                    {
                        Value::Null => Vec::new(),
                        init => {
                            let contracts = required_object(init, "contracts")
                                .map_err(|error| format!("{context} impl {name} init: {error}"))?;
                            contract_clause_ids(
                                contracts,
                                &["requires", "ensures"],
                                &format!("{context} impl {name} init"),
                            )?
                        }
                    };
                    init_clause_ids.extend(invariants.iter().cloned());
                    let strategy = ContractTestStrategy::new(
                        init_symbol.clone(),
                        &module.bytes,
                        "sync",
                        Classification::Pure,
                        init_clause_ids,
                        verification,
                    );
                    strategy.bytes()?;
                    strategies.push((strategy, None));

                    let mut selected = Vec::<(String, Value, Value)>::new();
                    for (slot_index, slot) in required_array(declaration, "selected_methods")
                        .map_err(|error| format!("{context} impl {name}: {error}"))?
                        .iter()
                        .enumerate()
                    {
                        let trait_method =
                            required_string(slot, "trait_method").map_err(|error| {
                                format!(
                                    "{context} impl {name} selected method {slot_index}: {error}"
                                )
                            })?;
                        let method_name = local_name(trait_method).ok_or_else(|| {
                            format!("{context} impl {name} selected method {slot_index}: invalid trait method")
                        })?;
                        let selected_impl = required_object(slot, "selected").map_err(|error| {
                            format!("{context} impl {name} selected method {method_name}: {error}")
                        })?;
                        let selected_kind = selected_origin(selected_impl).map_err(|error| {
                            format!("{context} impl {name} selected method {method_name}: {error}")
                        })?;
                        let function =
                            required_object(selected_impl, "function").map_err(|error| {
                                format!(
                                    "{context} impl {name} selected method {method_name}: {error}"
                                )
                            })?;
                        if selected_kind == "explicit"
                            && local_name(required_string(function, "symbol").map_err(|error| {
                                format!(
                                    "{context} impl {name} selected method {method_name}: {error}"
                                )
                            })?) != Some(method_name)
                        {
                            return Err(format!(
                                "{context} impl {name} selected method {method_name}: selected function does not match trait method"
                            ));
                        }
                        let (source, substitutions) = match selected_kind {
                            "explicit" => (
                                required_array(declaration, "methods")
                                    .map_err(|error| format!("{context} impl {name}: {error}"))?
                                    .iter()
                                    .find(|method| {
                                        method.get("name").and_then(Value::as_str).and_then(local_name)
                                            == Some(method_name)
                                    })
                                    .ok_or_else(|| {
                                        format!("{context} impl {name} selected method {method_name}: missing explicit method")
                                    })?,
                                BTreeMap::new(),
                            ),
                            "default" | "specialization" => {
                                let (trait_declaration, method) = find_trait_method(
                                    &modules,
                                    trait_method,
                                    &format!("{context} impl {name} selected method {method_name}"),
                                )?;
                                (
                                    method,
                                    if slot.get("return_type").is_some() {
                                        BTreeMap::new()
                                    } else {
                                        trait_substitutions(
                                            declaration,
                                            trait_declaration,
                                            trait_method,
                                            &format!("{context} impl {name} selected method {method_name}"),
                                        )?
                                    },
                                )
                            }
                            _ => {
                                return Err(format!(
                                    "{context} impl {name} selected method {method_name}: unsupported selected implementation `{selected_kind}`"
                                ));
                            }
                        };
                        let parameters = match slot.get("parameters") {
                            Some(parameters) => parameters.as_array().ok_or_else(|| {
                                format!(
                                    "{context} impl {name} selected method {method_name}: selected parameters must be an array"
                                )
                            })?,
                            None => required_array(source, "parameters").map_err(|error| {
                                format!("{context} impl {name} selected method {method_name}: {error}")
                            })?,
                        };
                        let parameter_types = parameters
                            .iter()
                            .enumerate()
                            .map(|(parameter_index, parameter)| {
                                required_field(parameter, "type")
                                    .map(|ty| concretize(ty, &substitutions))
                                    .map_err(|error| {
                                        format!(
                                            "{context} impl {name} selected method {method_name} parameter {parameter_index}: {error}"
                                        )
                                    })
                            })
                            .collect::<Result<Vec<_>, _>>()?;
                        let return_type = match slot.get("return_type") {
                            Some(return_type) => return_type.clone(),
                            None => concretize(
                                required_field(source, "return_type").map_err(|error| {
                                    format!("{context} impl {name} selected method {method_name}: {error}")
                                })?,
                                &substitutions,
                            ),
                        };
                        let signature = serde_json::json!({
                            "parameters": parameter_types,
                            "return_type": return_type,
                        });
                        if let Some((_, previous_signature, previous_selected)) = selected
                            .iter()
                            .find(|(selected_name, _, _)| selected_name == method_name)
                        {
                            if previous_signature != &signature
                                || previous_selected != selected_impl
                            {
                                return Err(format!(
                                    "{context} impl {name} selected method {method_name}: duplicate concrete slot differs"
                                ));
                            }
                            continue;
                        }
                        selected.push((method_name.to_owned(), signature, selected_impl.clone()));

                        let return_type = selected
                            .last()
                            .expect("selected method")
                            .1
                            .get("return_type")
                            .expect("return type");
                        let effects = match selected_kind {
                            "explicit" => required_array(source, "effects"),
                            "default" | "specialization" => required_object(source, "contract")
                                .and_then(|contract| required_array(contract, "effects")),
                            _ => Err(format!(
                                "unsupported selected implementation `{selected_kind}`"
                            )),
                        }
                        .map_err(|error| {
                            format!("{context} impl {name} selected method {method_name}: {error}")
                        })?;
                        let classification = classify(
                            return_type,
                            effects,
                            &format!("{context} impl {name} selected method {method_name}"),
                        )?;
                        let mut clause_ids = match selected_kind {
                            "explicit" => contract_clause_ids(
                                required_object(source, "contracts").map_err(|error| {
                                    format!("{context} impl {name} selected method {method_name}: {error}")
                                })?,
                                &["requires", "ensures", "errors"],
                                &format!("{context} impl {name} selected method {method_name}"),
                            ),
                            "default" | "specialization" => contract_clause_ids(
                                required_object(source, "contract").map_err(|error| {
                                    format!("{context} impl {name} selected method {method_name}: {error}")
                                })?,
                                &["clauses"],
                                &format!("{context} impl {name} selected method {method_name}"),
                            ),
                            _ => Err(format!(
                                "{context} impl {name} selected method {method_name}: unsupported selected implementation `{selected_kind}`"
                            )),
                        }?;
                        if selected_kind == "explicit" {
                            for (modifies_index, field) in required_array(source, "modifies")
                                .map_err(|error| {
                                    format!("{context} impl {name} selected method {method_name}: {error}")
                                })?
                                .iter()
                                .enumerate()
                            {
                                let field = field.as_str().ok_or_else(|| {
                                    format!(
                                        "{context} impl {name} selected method {method_name} modifies {modifies_index}: required field must be a string"
                                    )
                                })?;
                                clause_ids.push(format!("modifies:{field}"));
                            }
                        }
                        clause_ids.extend(invariants.iter().cloned());
                        let callable_kind =
                            required_string(slot, "callable_kind").map_err(|error| {
                                format!(
                                    "{context} impl {name} selected method {method_name}: {error}"
                                )
                            })?;
                        if !matches!(callable_kind, "sync" | "async") {
                            return Err(format!(
                                "{context} impl {name} selected method {method_name}: unsupported callable_kind `{callable_kind}`"
                            ));
                        }
                        let mut strategy = ContractTestStrategy::new(
                            format!("{name}.{method_name}"),
                            &module.bytes,
                            callable_kind,
                            classification,
                            clause_ids,
                            verification,
                        );
                        strategy.return_kind = protocol_return_kind(return_type)?.to_owned();
                        strategy.obligations = match selected_kind {
                            "explicit" => contract_obligations(
                                required_object(source, "contracts").map_err(|error| {
                                    format!("{context} impl {name} selected method {method_name}: {error}")
                                })?,
                                &["requires", "ensures", "errors"],
                                return_type,
                                &format!("{context} impl {name} selected method {method_name}"),
                            ),
                            "default" | "specialization" => contract_obligations(
                                required_object(source, "contract").map_err(|error| {
                                    format!("{context} impl {name} selected method {method_name}: {error}")
                                })?,
                                &["clauses"],
                                return_type,
                                &format!("{context} impl {name} selected method {method_name}"),
                            ),
                            _ => unreachable!("selected implementation was checked"),
                        }?;
                        strategy.bytes()?;
                        strategies.push((strategy, Some(init_symbol.clone())));
                    }
                }
                "scenario" => {
                    let symbol = required_string(declaration, "name")
                        .map_err(|error| format!("{context}: {error}"))?;
                    let required_effects = required_array(declaration, "required_effects")
                        .map_err(|error| format!("{context} scenario {symbol}: {error}"))?
                        .iter()
                        .enumerate()
                        .map(|(index, effect)| {
                            required_string(effect, "key")
                                .map(str::to_owned)
                                .map_err(|error| {
                                    format!("{context} scenario {symbol} effect {index}: {error}")
                                })
                        })
                        .collect::<Result<Vec<_>, _>>()?;
                    let mut strategy = ContractTestStrategy::new(
                        symbol,
                        &module.bytes,
                        "sync",
                        if required_effects.is_empty() {
                            Classification::Pure
                        } else {
                            Classification::Effectful
                        },
                        Vec::new(),
                        verification,
                    );
                    strategy.scenario = Some(scenario_strategy(
                        declaration,
                        symbol,
                        required_effects,
                        verification,
                        &context,
                    )?);
                    strategy.bytes()?;
                    strategies.push((strategy, None));
                }
                _ => {}
            }
        }
    }
    Ok(strategies)
}

fn local_name(symbol: &str) -> Option<&str> {
    symbol.rsplit('.').next().filter(|name| !name.is_empty())
}
fn selected_origin(selected: &Value) -> Result<&str, String> {
    selected
        .get("origin")
        .or_else(|| selected.get("kind"))
        .and_then(Value::as_str)
        .ok_or_else(|| "required selected `origin` must be a string".to_owned())
}

fn find_trait_method<'a>(
    modules: &'a [Value],

    trait_method: &str,
    context: &str,
) -> Result<(&'a Value, &'a Value), String> {
    let (trait_name, method_name) = trait_method
        .rsplit_once('.')
        .ok_or_else(|| format!("{context}: invalid trait method"))?;
    for module in modules {
        for declaration in
            required_array(module, "declarations").map_err(|error| format!("{context}: {error}"))?
        {
            if declaration.get("kind").and_then(Value::as_str) != Some("trait")
                || declaration.get("name").and_then(Value::as_str) != Some(trait_name)
            {
                continue;
            }
            let method = required_array(declaration, "methods")
                .map_err(|error| format!("{context}: {error}"))?
                .iter()
                .find(|method| {
                    method
                        .get("name")
                        .and_then(Value::as_str)
                        .and_then(local_name)
                        == Some(method_name)
                })
                .ok_or_else(|| format!("{context}: missing trait method"))?;
            return Ok((declaration, method));
        }
    }
    Err(format!("{context}: missing trait declaration"))
}

fn trait_substitutions(
    implementation: &Value,
    trait_declaration: &Value,
    trait_method: &str,
    context: &str,
) -> Result<BTreeMap<String, Value>, String> {
    let (trait_name, _) = trait_method
        .rsplit_once('.')
        .ok_or_else(|| format!("{context}: invalid trait method"))?;
    let trait_reference = required_array(implementation, "traits")
        .map_err(|error| format!("{context}: {error}"))?
        .iter()
        .find(|reference| {
            reference.get("kind").and_then(Value::as_str) == Some("named")
                && reference.get("name").and_then(Value::as_str) == Some(trait_name)
        });
    let generics = required_array(trait_declaration, "generics")
        .map_err(|error| format!("{context}: {error}"))?;
    let Some(trait_reference) = trait_reference else {
        return generics
            .is_empty()
            .then(BTreeMap::new)
            .ok_or_else(|| format!("{context}: missing instantiated trait"));
    };
    let arguments =
        required_array(trait_reference, "args").map_err(|error| format!("{context}: {error}"))?;
    if generics.len() != arguments.len() {
        return Err(format!("{context}: trait generic arity differs"));
    }
    generics
        .iter()
        .zip(arguments)
        .map(|(generic, argument)| {
            let name =
                required_string(generic, "name").map_err(|error| format!("{context}: {error}"))?;
            let value = match required_string(argument, "kind")
                .map_err(|error| format!("{context}: {error}"))?
            {
                "type" => required_field(argument, "type"),
                "const" => required_field(argument, "value"),
                _ => Err("unsupported generic argument".to_owned()),
            }
            .map_err(|error| format!("{context}: {error}"))?;
            Ok((name.to_owned(), value.clone()))
        })
        .collect()
}

fn concretize(value: &Value, substitutions: &BTreeMap<String, Value>) -> Value {
    if let Some(object) = value.as_object() {
        if matches!(
            object.get("kind").and_then(Value::as_str),
            Some("type_parameter" | "parameter")
        ) && let Some(name) = object.get("name").and_then(Value::as_str)
            && let Some(replacement) = substitutions.get(name)
        {
            return replacement.clone();
        }
        return Value::Object(
            object
                .iter()
                .map(|(key, value)| (key.clone(), concretize(value, substitutions)))
                .collect(),
        );
    }
    if let Some(values) = value.as_array() {
        return Value::Array(
            values
                .iter()
                .map(|value| concretize(value, substitutions))
                .collect(),
        );
    }
    value.clone()
}

fn classify(
    return_type: &Value,
    effects: &[Value],
    context: &str,
) -> Result<Classification, String> {
    let return_kind =
        required_string(return_type, "kind").map_err(|error| format!("{context}: {error}"))?;
    if return_kind == "primitive"
        && required_string(return_type, "name").map_err(|error| format!("{context}: {error}"))?
            == "never"
    {
        Ok(Classification::Never)
    } else if effects.is_empty() {
        Ok(Classification::Pure)
    } else {
        Ok(Classification::Effectful)
    }
}
fn protocol_return_kind(return_type: &Value) -> Result<&'static str, String> {
    match required_string(return_type, "kind")? {
        "async_iterator" => Ok("async_iterator"),
        "async_generator" => Ok("async_generator"),
        _ => Ok("value"),
    }
}

fn contract_clause_ids(
    contract: &Value,
    fields: &[&str],
    context: &str,
) -> Result<Vec<String>, String> {
    let mut clauses = Vec::new();
    for (field_order, field) in fields.iter().enumerate() {
        for (clause_index, clause) in required_array(contract, field)
            .map_err(|error| format!("{context} {field}: {error}"))?
            .iter()
            .enumerate()
        {
            let clause_kind = required_string(clause, "kind")
                .map_err(|error| format!("{context} {field} clause {clause_index}: {error}"))?;
            let clause_id = required_field(clause, "clause_id")
                .and_then(|value| {
                    value.as_u64().ok_or_else(|| {
                        "required field `clause_id` must be a non-negative integer".to_owned()
                    })
                })
                .map_err(|error| format!("{context} {field} clause {clause_index}: {error}"))?;
            clauses.push((
                clause_id,
                field_order,
                clause_index,
                format!("{clause_kind}:{clause_id}"),
            ));
        }
    }
    if fields.len() > 1 {
        clauses.sort_unstable_by_key(|(clause_id, field_order, clause_index, _)| {
            (*clause_id, *field_order, *clause_index)
        });
    }
    Ok(clauses
        .into_iter()
        .map(|(_, _, _, clause_id)| clause_id)
        .collect())
}
fn contract_obligations(
    contract: &Value,
    fields: &[&str],
    return_type: &Value,
    context: &str,
) -> Result<Vec<ContractObligation>, String> {
    if required_string(return_type, "kind").map_err(|error| format!("{context}: {error}"))?
        != "result"
    {
        return Ok(Vec::new());
    }
    let mut clauses = Vec::new();
    for (field_order, field) in fields.iter().enumerate() {
        for (clause_order, clause) in required_array(contract, field)
            .map_err(|error| format!("{context} {field}: {error}"))?
            .iter()
            .enumerate()
        {
            let kind = required_string(clause, "kind")
                .map_err(|error| format!("{context} {field} clause {clause_order}: {error}"))?;
            let clause_id = required_field(clause, "clause_id")
                .and_then(|value| {
                    value.as_u64().ok_or_else(|| {
                        "required field `clause_id` must be a non-negative integer".to_owned()
                    })
                })
                .map_err(|error| format!("{context} {field} clause {clause_order}: {error}"))?;
            clauses.push((clause_id, field_order, clause_order, kind, clause));
        }
    }
    if !clauses.iter().any(|(_, _, _, kind, _)| *kind == "error") {
        return Ok(Vec::new());
    }
    clauses.sort_unstable_by_key(|(id, field, order, _, _)| (*id, *field, *order));
    Ok(clauses
        .into_iter()
        .filter_map(|(clause_id, _, _, kind, clause)| {
            let role = match kind {
                "ensures"
                    if clause
                        .pointer("/guard/pattern/kind")
                        .and_then(Value::as_str)
                        == Some("result_ok") =>
                {
                    Some(ContractObligationRole::Success)
                }
                "error"
                    if clause.get("guard").is_some_and(|guard| !guard.is_null())
                        || clause.get("when").is_some_and(|when| !when.is_null()) =>
                {
                    Some(ContractObligationRole::ConditionalError)
                }
                _ => None,
            }?;
            Some(ContractObligation {
                clause_id: format!("{kind}:{clause_id}"),
                role,
            })
        })
        .collect())
}

fn scenario_strategy(
    declaration: &Value,
    id: &str,
    required_effects: Vec<String>,
    verification: &VerificationConfig,
    context: &str,
) -> Result<ScenarioStrategy, String> {
    let fixtures = required_array(declaration, "fixtures")
        .map_err(|error| format!("{context} scenario {id}: {error}"))?
        .clone();
    let steps = required_array(declaration, "steps")
        .map_err(|error| format!("{context} scenario {id}: {error}"))?
        .clone();
    if steps.len() > 64 {
        return Err(format!("{context} scenario {id}: step limit exceeds 64"));
    }
    let lifecycle_limit = required_field(declaration, "lifecycle_limit")
        .and_then(|value| {
            value
                .as_u64()
                .filter(|value| (1..=64).contains(value))
                .ok_or_else(|| "lifecycle_limit must be in 1..=64".to_owned())
        })
        .map_err(|error| format!("{context} scenario {id}: {error}"))?;
    let lifecycle_limit = u32::try_from(lifecycle_limit)
        .map_err(|_| format!("{context} scenario {id}: lifecycle_limit exceeds u32"))?;
    let mut fixture_ids = BTreeSet::new();
    for (index, fixture) in fixtures.iter().enumerate() {
        let fixture_id = required_string(fixture, "id")
            .map_err(|error| format!("{context} scenario {id} fixture {index}: {error}"))?;
        if !fixture_ids.insert(fixture_id) {
            return Err(format!(
                "{context} scenario {id}: duplicate fixture id `{fixture_id}`"
            ));
        }
        validate_scenario_fixture(fixture)
            .map_err(|error| format!("{context} scenario {id} fixture {index}: {error}"))?;
    }
    let mut step_ids = BTreeSet::new();
    for (index, step) in steps.iter().enumerate() {
        let step_id = required_field(step, "step_id")
            .and_then(|value| {
                value.as_u64().ok_or_else(|| {
                    "required field `step_id` must be a non-negative integer".to_owned()
                })
            })
            .map_err(|error| format!("{context} scenario {id} step {index}: {error}"))?;
        if step_id != index as u64 || !step_ids.insert(step_id) {
            return Err(format!(
                "{context} scenario {id}: step IDs must be ordered and unique"
            ));
        }
        let kind = required_string(step, "kind")
            .map_err(|error| format!("{context} scenario {id} step {index}: {error}"))?;
        if matches!(kind, "call" | "spawn")
            && required_string(step, "target")
                .map_err(|error| format!("{context} scenario {id} step {index}: {error}"))?
                .is_empty()
        {
            return Err(format!(
                "{context} scenario {id} step {index}: empty facade target"
            ));
        }
    }
    Ok(ScenarioStrategy {
        id: id.to_owned(),
        required_effects,
        fixtures,
        steps,
        lifecycle_limit,
        limits: ScenarioLimits::from_verification(verification),
    })
}

fn validate_scenario_fixture(fixture: &Value) -> Result<(), String> {
    match required_string(fixture, "kind")? {
        "fs" => {
            for file in required_array(fixture, "files")? {
                if !closed_relative_path(required_string(file, "path")?) {
                    return Err("filesystem fixture path must be a closed relative path".to_owned());
                }
            }
        }
        "http" => {
            for route in required_array(fixture, "routes")? {
                if !closed_route_path(required_string(route, "path")?) {
                    return Err("HTTP fixture route must be a closed absolute route".to_owned());
                }
            }
        }
        "clock" | "failure" => {}
        kind => return Err(format!("unsupported fixture kind `{kind}`")),
    }
    Ok(())
}

fn closed_relative_path(path: &str) -> bool {
    !path.is_empty()
        && path.split('/').all(|part| {
            !part.is_empty()
                && part != "."
                && part != ".."
                && part
                    .bytes()
                    .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b'-'))
        })
}

fn closed_route_path(path: &str) -> bool {
    path.strip_prefix('/').is_some_and(|path| {
        path.is_empty()
            || path.split('/').all(|part| {
                !part.is_empty()
                    && part != "."
                    && part != ".."
                    && part.bytes().all(|byte| {
                        byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b'-')
                    })
            })
    })
}

fn invariant_clause_ids(invariants: &[Value], context: &str) -> Result<Vec<String>, String> {
    invariants
        .iter()
        .enumerate()
        .map(|(invariant_index, invariant)| {
            let clause_id = required_field(invariant, "clause_id")
                .and_then(|value| {
                    value.as_u64().ok_or_else(|| {
                        "required field `clause_id` must be a non-negative integer".to_owned()
                    })
                })
                .map_err(|error| format!("{context} invariant {invariant_index}: {error}"))?;
            Ok(format!("invariant:{clause_id}"))
        })
        .collect()
}

fn unavailable_scenario_evidence(strategies: &[ContractTestStrategy]) -> Vec<Value> {
    strategies
        .iter()
        .filter_map(|strategy| strategy.scenario.as_ref())
        .map(|scenario| {
            let assertions = scenario
                .steps
                .iter()
                .filter(|step| step.get("kind").and_then(Value::as_str) == Some("assert"))
                .filter_map(|step| {
                    step.get("step_id").and_then(Value::as_u64).map(|step_id| {
                        serde_json::json!({
                            "assertion_id": format!("assert:{step_id}"),
                            "grade": "unobserved",
                            "reason": "isolated loopback capability unavailable",
                            "span": step.get("span").cloned().unwrap_or(Value::Null),
                        })
                    })
                })
                .collect::<Vec<_>>();
            serde_json::json!({
                "assertions": assertions,
                "fixtures": [],
                "grade": "unobserved",
                "reason": "isolated loopback capability unavailable",
                "scenario_id": scenario.id,
                "trace": [],
            })
        })
        .collect()
}

pub fn execute_contract_tests(
    interpreter: &Path,
    generated_root: &Path,
    site_packages: &[PathBuf],
    ir: &CanonicalIr,
    verification: &VerificationConfig,
    runtime_validation: RuntimeValidation,
    scope: Option<&BTreeSet<String>>,
) -> Result<Value, String> {
    static NEXT: AtomicU64 = AtomicU64::new(0);
    let strategies = derive_strategy_entries(ir, verification)?;
    let selected_initializers = scope.map(|scope| {
        strategies
            .iter()
            .filter(|(strategy, _)| scope.contains(&strategy.symbol))
            .filter_map(|(_, initializer)| initializer.as_ref())
            .cloned()
            .collect::<BTreeSet<_>>()
    });
    let strategies = strategies
        .into_iter()
        .filter(|(strategy, _)| {
            scope.is_none_or(|scope| {
                scope.contains(&strategy.symbol)
                    || selected_initializers
                        .as_ref()
                        .is_some_and(|initializers| initializers.contains(&strategy.symbol))
            })
        })
        .map(|(strategy, _)| strategy)
        .collect::<Vec<_>>();
    let modules = ir
        .modules
        .iter()
        .map(|module| crate::ir::load(&module.bytes))
        .collect::<Result<Vec<_>, _>>()?;
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|error| error.to_string())?
        .as_nanos();
    let scratch = std::env::temp_dir().join(format!(
        "cott-contract-test-{}-{nonce}-{}",
        std::process::id(),
        NEXT.fetch_add(1, Ordering::Relaxed)
    ));
    fs::create_dir(&scratch).map_err(|error| {
        format!(
            "create contract-test scratch {}: {error}",
            scratch.display()
        )
    })?;
    let needs_loopback = strategies.iter().any(|strategy| {
        strategy.scenario.as_ref().is_some_and(|scenario| {
            scenario
                .fixtures
                .iter()
                .any(|fixture| fixture.get("kind").and_then(Value::as_str) == Some("http"))
        })
    });
    let fallback_scope = strategies
        .iter()
        .filter(|strategy| strategy.scenario.is_none())
        .map(|strategy| strategy.symbol.clone())
        .collect::<BTreeSet<_>>();
    let fixture_root = scratch.join("fixtures");
    let request = serde_json::json!({
        "fixture_root": fixture_root,
        "modules": modules,
        "runtime_validation": match runtime_validation {
            RuntimeValidation::Off => "off",
            RuntimeValidation::Boundary => "boundary",
            RuntimeValidation::TestOnly => "test-only",
        },
        "strategies": strategies.clone(),
    });
    let stdin = serde_json::to_vec(&request).map_err(|error| error.to_string())?;
    let mut read_only = vec![
        generated_root
            .parent()
            .unwrap_or(generated_root)
            .to_path_buf(),
    ];
    read_only.extend(site_packages.iter().cloned());
    if !interpreter.starts_with("/usr")
        && !interpreter.starts_with("/bin")
        && !interpreter.starts_with("/lib")
        && let Some(environment) = interpreter.parent().and_then(Path::parent)
    {
        read_only.push(environment.to_path_buf());
    }
    let mut python_paths = vec![generated_root.to_path_buf()];
    python_paths.extend(site_packages.iter().cloned());
    let python_path = std::env::join_paths(python_paths)
        .map_err(|error| format!("construct contract-test PYTHONPATH: {error}"))?;
    let result = run(&SandboxSpec {
        program: interpreter.to_path_buf(),
        arguments: vec![
            "-c".to_owned(),
            include_str!("contract_runner.py").to_owned(),
        ],
        cwd: generated_root.to_path_buf(),
        environment: BTreeMap::from([
            ("HOME".to_owned(), scratch.display().to_string()),
            ("PATH".to_owned(), "/usr/bin:/bin".to_owned()),
            ("PYTHONDONTWRITEBYTECODE".to_owned(), "1".to_owned()),
            ("PYTHONHASHSEED".to_owned(), "0".to_owned()),
            (
                "PYTHONPATH".to_owned(),
                python_path.to_string_lossy().into_owned(),
            ),
            ("TMPDIR".to_owned(), scratch.display().to_string()),
        ]),
        stdin,
        binds: BindMounts {
            read_only,
            writable: vec![scratch.clone()],
        },
        network: if needs_loopback {
            NetworkAccess::IsolatedLoopback
        } else {
            NetworkAccess::Disabled
        },
        limits: ResourceLimits::contract_test(),
    });
    let cleanup = fs::remove_dir_all(&scratch);
    if let Err(error) = cleanup {
        return Err(format!(
            "remove contract-test scratch {}: {error}",
            scratch.display()
        ));
    }
    let completed = match result {
        Ok(completed) => completed,
        Err(SandboxError::UnsupportedLoopback) if needs_loopback => {
            let mut report = if fallback_scope.is_empty() {
                serde_json::json!({"contracts": [], "lifecycle": [], "scenarios": []})
            } else {
                execute_contract_tests(
                    interpreter,
                    generated_root,
                    site_packages,
                    ir,
                    verification,
                    runtime_validation,
                    Some(&fallback_scope),
                )?
            };
            let scenarios = report
                .get_mut("scenarios")
                .and_then(Value::as_array_mut)
                .ok_or("contract-test fallback report has no scenarios array")?;
            scenarios.extend(unavailable_scenario_evidence(&strategies));
            return Ok(report);
        }
        Err(error) => return Err(error.to_string()),
    };
    if completed.status != Some(0) {
        return Err(format!(
            "contract test process exited {:?}: {}",
            completed.status,
            String::from_utf8_lossy(&completed.stderr).trim()
        ));
    }
    if !completed.stderr.is_empty() {
        return Err(format!(
            "contract test process wrote stderr: {}",
            String::from_utf8_lossy(&completed.stderr).trim()
        ));
    }
    let output = completed
        .stdout
        .rsplit(|byte| *byte == b'\n')
        .find(|line| !line.is_empty())
        .ok_or("contract test process produced no JSON")?;
    serde_json::from_slice(output).map_err(|error| format!("invalid contract-test report: {error}"))
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

#[cfg(test)]
mod tests {
    use std::io::Write;
    use std::process::{Command, Stdio};

    use super::*;

    #[test]
    fn effectful_strategies_do_not_import_their_facade() {
        let root = std::env::temp_dir().join(format!(
            "cott-effectful-contract-test-{}",
            std::process::id()
        ));
        let _ = fs::remove_dir_all(&root);
        fs::create_dir(&root).expect("fixture root");
        fs::write(root.join("cott_runtime.py"), "").expect("runtime stub");
        let request = serde_json::json!({
            "modules": [{
                "module": "missing.facade",
                "declarations": [
                    {
                        "kind": "function",
                        "name": "missing.facade.fetch",
                        "contract": {"clauses": []},
                    },
                    {
                        "kind": "impl",
                        "name": "missing.facade.Camera",
                        "init": {
                            "contracts": {
                                "requires": [{"clause_id": 0, "span": null, "expression": {}}],
                            },
                        },
                        "invariants": [],
                        "methods": [{
                            "name": "build",
                            "contracts": {},
                            "modifies": [],
                            "parameters": [],
                            "return_type": {"kind": "primitive", "name": "bool"},
                            "span": null,
                        }],
                        "selected_methods": [{
                            "receiver_type": {
                                "args": [],
                                "kind": "named",
                                "name": "missing.facade.Camera",
                            },
                            "trait_method": "missing.facade.Camera.build",
                            "selected": {
                                "kind": "explicit",
                                "function": {
                                    "module": "missing.facade",
                                    "symbol": "Camera.build",
                                    "verified_facade": "missing.facade.Camera.build",
                                },
                            },
                        }],
                    },
                ],
            }],
            "runtime_validation": "boundary",
            "strategies": [
                {
                    "symbol": "missing.facade.fetch",
                    "classification": "effectful",
                },
                {
                    "symbol": "missing.facade.Camera.init",
                    "classification": "pure",
                },
                {
                    "symbol": "missing.facade.Camera.build",
                    "classification": "effectful",
                },
            ],
        });
        let mut child = match Command::new("python3")
            .args(["-c", include_str!("contract_runner.py")])
            .env("PYTHONPATH", &root)
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(Stdio::piped())
            .spawn()
        {
            Ok(child) => child,
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => return,
            Err(error) => panic!("spawn Python: {error}"),
        };
        child
            .stdin
            .take()
            .expect("Python stdin")
            .write_all(&serde_json::to_vec(&request).expect("request"))
            .expect("write request");
        let output = child.wait_with_output().expect("wait for Python");
        fs::remove_dir_all(root).expect("remove fixture root");
        assert!(
            output.status.success(),
            "{}",
            String::from_utf8_lossy(&output.stderr)
        );
        let report = serde_json::from_slice::<Value>(&output.stdout).expect("report");
        assert_eq!(report["contracts"].as_array().map(Vec::len), Some(1));
        assert_eq!(report["contracts"][0]["evidence"][0]["grade"], "unobserved");
    }
    #[test]
    fn unavailable_loopback_emits_only_logical_unobserved_scenario_evidence() {
        let verification = VerificationConfig::default();
        let mut strategy = ContractTestStrategy::new(
            "demo.scenario.fetch",
            b"module",
            "sync",
            Classification::Effectful,
            Vec::new(),
            &verification,
        );
        strategy.scenario = Some(ScenarioStrategy {
            id: "demo.scenario.fetch".to_owned(),
            required_effects: vec!["network".to_owned()],
            fixtures: vec![serde_json::json!({"kind": "http"})],
            steps: vec![serde_json::json!({
                "kind": "assert",
                "step_id": 7,
                "span": {"start_byte": 0, "end_byte": 1, "start_line": 1, "start_column": 1, "end_line": 1, "end_column": 2},
            })],
            lifecycle_limit: 64,
            limits: ScenarioLimits::from_verification(&verification),
        });
        let evidence = unavailable_scenario_evidence(&[strategy]);
        assert_eq!(evidence[0]["grade"], "unobserved");
        assert_eq!(
            evidence[0]["assertions"][0]["reason"],
            "isolated loopback capability unavailable"
        );
        assert!(evidence[0]["trace"].as_array().is_some_and(Vec::is_empty));
    }
}
