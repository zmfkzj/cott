use std::collections::{BTreeMap, BTreeSet};
use std::path::PathBuf;

use serde::{Deserialize, Serialize};
use serde_json::Value;

use crate::ir::CanonicalIr;
use crate::python::artifact_plan::{PythonArtifactPlan, PythonCallable};

use self::types::DartEnumProjection;

pub mod binding;
pub(crate) mod dependencies;
pub mod emit;
pub(crate) mod expressions;
pub(crate) mod generation;
pub(crate) mod pipeline;
pub(crate) mod prompt;
pub mod provenance;
pub(crate) mod runner;
pub mod runtime;
pub(crate) mod types;
pub(crate) mod verify;

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DartPlan {
    pub ir: CanonicalIr,
    pub modules: Vec<DartModule>,
    callables: Vec<DartCallable>,
    contract_surface: Value,
    enum_projection: DartEnumProjection,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DartModule {
    pub name: String,
    pub imports: Vec<String>,
    pub declarations: Vec<Value>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DartCallable {
    pub symbol: String,
    pub module: String,
    pub name: String,
    pub declaration: Value,
    pub owner: Option<Value>,
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum DartOwner {
    Manifest,
    Agent,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DartBinding {
    pub cott_symbol: String,
    pub target_symbol: String,
    pub source_origin: PathBuf,
    pub runtime_origin: PathBuf,
    pub bytes: Vec<u8>,
    pub owner: DartOwner,
    pub content_hash: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct DartEmission {
    pub files: BTreeMap<PathBuf, Vec<u8>>,
    pub public_symbols: BTreeMap<String, Vec<String>>,
    pub unresolved: Vec<String>,
}

impl DartPlan {
    pub fn from_ir(ir: &CanonicalIr) -> Result<Self, String> {
        let canonical = PythonArtifactPlan::from_ir(ir)
            .map_err(|error| format!("build Dart plan from canonical IR: {error}"))?;
        let callables = complete_callables(&canonical)?
            .into_iter()
            .map(|callable| DartCallable {
                symbol: callable.cott_symbol,
                module: callable.module,
                name: callable.name,
                declaration: callable.declaration,
                owner: callable.owner,
            })
            .collect();
        let contract_surface = canonical.contract_surface();
        let modules: Vec<DartModule> = canonical
            .modules
            .into_iter()
            .map(|module| DartModule {
                name: module.module,
                imports: module.imports,
                declarations: module.declarations,
            })
            .collect();
        let enum_projection = DartEnumProjection::from_modules(&modules)?;
        Ok(Self {
            ir: ir.clone(),
            modules,
            callables,
            contract_surface,
            enum_projection,
        })
    }

    pub fn callables(&self) -> &[DartCallable] {
        &self.callables
    }

    /// The single deterministic Cott-to-Dart enum projection for this plan.
    pub(crate) fn enum_projection(&self) -> &DartEnumProjection {
        &self.enum_projection
    }

    pub fn contract_surface(&self) -> &Value {
        &self.contract_surface
    }
}

fn complete_callables(plan: &PythonArtifactPlan) -> Result<Vec<PythonCallable>, String> {
    let callables = plan.callables();
    let actual = callables
        .iter()
        .map(|callable| callable.cott_symbol.clone())
        .collect::<BTreeSet<_>>();
    if actual.len() != callables.len() {
        return Err("Dart callable projection contains duplicate symbols".to_owned());
    }

    let mut expected = BTreeSet::new();
    for module in &plan.modules {
        for declaration in &module.declarations {
            match declaration.get("kind").and_then(Value::as_str) {
                Some("function")
                    if declaration.get("public").and_then(Value::as_bool) == Some(true) =>
                {
                    let symbol =
                        declaration
                            .get("name")
                            .and_then(Value::as_str)
                            .ok_or_else(|| {
                                format!(
                                    "Dart callable in `{}` is missing its canonical name",
                                    module.module
                                )
                            })?;
                    expected.insert(symbol.to_owned());
                }
                Some("impl") => {
                    let owner =
                        declaration
                            .get("name")
                            .and_then(Value::as_str)
                            .ok_or_else(|| {
                                format!(
                                    "Dart implementation in `{}` is missing its canonical name",
                                    module.module
                                )
                            })?;
                    for slot in declaration
                        .get("selected_methods")
                        .and_then(Value::as_array)
                        .into_iter()
                        .flatten()
                    {
                        let trait_method = slot
                            .get("trait_method")
                            .and_then(Value::as_str)
                            .ok_or_else(|| {
                                format!(
                                    "Dart implementation `{owner}` has a malformed selected method"
                                )
                            })?;
                        let method = trait_method.rsplit('.').next().ok_or_else(|| {
                            format!("Dart implementation `{owner}` has a malformed trait method")
                        })?;
                        expected.insert(format!("{owner}.{method}"));

                        let selected = slot.get("selected").and_then(Value::as_object).ok_or_else(
                            || {
                                format!(
                                    "Dart implementation `{owner}` has missing selection provenance"
                                )
                            },
                        )?;
                        if matches!(
                            selected.get("origin").and_then(Value::as_str),
                            Some("default" | "specialization")
                        ) {
                            let function = selected
                                .get("function")
                                .and_then(Value::as_object)
                                .ok_or_else(|| {
                                    format!(
                                        "Dart implementation `{owner}` has missing default or specialization provenance"
                                    )
                                })?;
                            let function_module = function
                                .get("module")
                                .and_then(Value::as_str)
                                .ok_or_else(|| {
                                    format!(
                                        "Dart implementation `{owner}` has malformed default or specialization provenance"
                                    )
                                })?;
                            let function_symbol = function
                                .get("symbol")
                                .and_then(Value::as_str)
                                .ok_or_else(|| {
                                    format!(
                                        "Dart implementation `{owner}` has malformed default or specialization provenance"
                                    )
                                })?;
                            expected.insert(format!("{function_module}.{function_symbol}"));
                        }
                    }
                }
                _ => {}
            }
        }
    }

    if actual == expected {
        Ok(callables)
    } else {
        let missing = expected.difference(&actual).cloned().collect::<Vec<_>>();
        let unexpected = actual.difference(&expected).cloned().collect::<Vec<_>>();
        Err(format!(
            "Dart callable projection is incomplete (missing: {}; unexpected: {})",
            missing.join(", "),
            unexpected.join(", ")
        ))
    }
}
