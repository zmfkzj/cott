use std::collections::BTreeMap;
use std::collections::BTreeSet;
use std::fs;
use std::path::Path;
use std::sync::LazyLock;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::hash::sha256_hex;
use crate::ir::CanonicalIr;
use crate::manifest::RuntimeValidation;
use crate::sandbox::{BindMounts, NetworkAccess, ResourceLimits, SandboxSpec, run};

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

/// Derive metadata-only contract test strategies from canonical IR v2 module
/// bytes, preserving canonical module, declaration, and impl-member order.
pub fn derive_strategies(ir: &CanonicalIr) -> Result<Vec<ContractTestStrategy>, String> {
    Ok(derive_strategy_entries(ir)?
        .into_iter()
        .map(|(strategy, _)| strategy)
        .collect())
}

fn derive_strategy_entries(
    ir: &CanonicalIr,
) -> Result<Vec<(ContractTestStrategy, Option<String>)>, String> {
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
            let context = format!("module {module_index} declaration {declaration_index}");
            match kind {
                "function" => {
                    let symbol = required_string(declaration, "name")
                        .map_err(|error| format!("{context}: {error}"))?;
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

                    let strategy = ContractTestStrategy::new(
                        symbol,
                        &module.bytes,
                        classification,
                        clause_ids,
                    );
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
                        Classification::Pure,
                        init_clause_ids,
                    );
                    strategy.bytes()?;
                    strategies.push((strategy, None));

                    let methods = required_array(declaration, "methods")
                        .map_err(|error| format!("{context} impl {name}: {error}"))?;
                    for (method_index, method) in methods.iter().enumerate() {
                        let method_name = required_string(method, "name").map_err(|error| {
                            format!("{context} impl {name} method {method_index}: {error}")
                        })?;
                        let method_context = format!("{context} impl {name} method {method_name}");
                        let contracts = required_object(method, "contracts")
                            .map_err(|error| format!("{method_context}: {error}"))?;
                        let mut clause_ids = contract_clause_ids(
                            contracts,
                            &["requires", "ensures", "errors"],
                            &method_context,
                        )?;
                        let modifies = required_array(method, "modifies")
                            .map_err(|error| format!("{method_context}: {error}"))?;
                        for (modifies_index, field) in modifies.iter().enumerate() {
                            let field = field.as_str().ok_or_else(|| {
                                format!(
                                    "{method_context} modifies {modifies_index}: required field must be a string"
                                )
                            })?;
                            clause_ids.push(format!("modifies:{field}"));
                        }
                        clause_ids.extend(invariants.iter().cloned());
                        let return_type = required_object(method, "return_type")
                            .map_err(|error| format!("{method_context}: {error}"))?;
                        let classification = classify(
                            return_type,
                            required_array(method, "effects")
                                .map_err(|error| format!("{method_context}: {error}"))?,
                            &method_context,
                        )?;
                        let strategy = ContractTestStrategy::new(
                            format!("{name}.{method_name}"),
                            &module.bytes,
                            classification,
                            clause_ids,
                        );
                        strategy.bytes()?;
                        strategies.push((strategy, Some(init_symbol.clone())));
                    }
                }
                _ => {}
            }
        }
    }
    Ok(strategies)
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

pub fn execute_contract_tests(
    interpreter: &Path,
    generated_root: &Path,
    ir: &CanonicalIr,
    runtime_validation: RuntimeValidation,
    scope: Option<&BTreeSet<String>>,
) -> Result<Value, String> {
    static NEXT: AtomicU64 = AtomicU64::new(0);
    let strategies = derive_strategy_entries(ir)?;
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
    let request = serde_json::json!({
        "modules": modules,
        "runtime_validation": match runtime_validation {
            RuntimeValidation::Off => "off",
            RuntimeValidation::Boundary => "boundary",
            RuntimeValidation::TestOnly => "test-only",
        },
        "strategies": strategies,
    });
    let stdin = serde_json::to_vec(&request).map_err(|error| error.to_string())?;
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
    let mut read_only = vec![
        generated_root
            .parent()
            .unwrap_or(generated_root)
            .to_path_buf(),
    ];
    if !interpreter.starts_with("/usr")
        && !interpreter.starts_with("/bin")
        && !interpreter.starts_with("/lib")
        && let Some(environment) = interpreter.parent().and_then(Path::parent)
    {
        read_only.push(environment.to_path_buf());
    }
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
                generated_root.display().to_string(),
            ),
            ("TMPDIR".to_owned(), scratch.display().to_string()),
        ]),
        stdin,
        binds: BindMounts {
            read_only,
            writable: vec![scratch.clone()],
        },
        network: NetworkAccess::Disabled,
        limits: ResourceLimits::contract_test(),
    });
    let cleanup = fs::remove_dir_all(&scratch);
    if let Err(error) = cleanup {
        return Err(format!(
            "remove contract-test scratch {}: {error}",
            scratch.display()
        ));
    }
    let completed = result.map_err(|error| error.to_string())?;
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
    serde_json::from_slice(&completed.stdout)
        .map_err(|error| format!("invalid contract-test report: {error}"))
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
