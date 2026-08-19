//! Owned Python-facing projection of canonical IR.
//!
//! This module deliberately keeps declarations as canonical JSON values.  It
//! is the boundary used by Python binding and emission code while those users
//! move away from semantic and HIR models.

use std::fmt;

use serde_json::{Map, Value};

use crate::ir::{self, CanonicalIr};

/// A deterministic, owned projection of canonical modules for Python work.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PythonArtifactPlan {
    /// Modules ordered by their dotted canonical module name.
    pub modules: Vec<PythonArtifactModule>,
}

/// One canonical module and its declaration values.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PythonArtifactModule {
    /// Dotted canonical module name (for example, `api.service`).
    pub module: String,
    /// Canonical imports in their source order.
    pub imports: Vec<String>,
    /// Canonical declaration objects, retained without target-specific parsing.
    pub declarations: Vec<Value>,
    declaration_info: Vec<DeclarationInfo>,
}

/// The kind of a callable selected from a plan.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum PythonCallableKind {
    Function,
    ImplMethod { concrete: String },
}

/// A callable selected from a plan.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct PythonCallable {
    /// Dotted canonical module name.
    pub module: String,
    /// Canonical Cott symbol.
    pub cott_symbol: String,
    /// The free-function or method name.
    pub name: String,
    /// Whether this is a free function or an implementation method.
    pub kind: PythonCallableKind,
    /// The complete canonical function or method declaration.
    pub declaration: Value,
    /// The enclosing implementation declaration for methods.
    pub owner: Option<Value>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
struct DeclarationInfo {
    name: String,
    kind: String,
    public: bool,
    source_order: u64,
}

/// Errors found while loading or projecting one canonical module.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum PythonArtifactPlanError {
    /// The module bytes are not a valid canonical module.
    InvalidModule {
        module_index: usize,
        module: String,
        message: String,
    },
    /// A loaded module or declaration is missing a required canonical field.
    MalformedDeclaration {
        module_index: usize,
        module: String,
        declaration_index: usize,
        message: String,
    },
}

impl fmt::Display for PythonArtifactPlanError {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        match self {
            Self::InvalidModule {
                module_index,
                module,
                message,
            } => write!(
                formatter,
                "invalid canonical module {module:?} at index {module_index}: {message}"
            ),
            Self::MalformedDeclaration {
                module_index,
                module,
                declaration_index,
                message,
            } => write!(
                formatter,
                "malformed declaration {module}[{declaration_index}] in module index {module_index}: {message}"
            ),
        }
    }
}

impl std::error::Error for PythonArtifactPlanError {}

impl PythonArtifactPlan {
    /// Load and project every canonical module in `ir`.
    pub fn from_ir(ir: &CanonicalIr) -> Result<Self, PythonArtifactPlanError> {
        let mut modules = Vec::with_capacity(ir.modules.len());
        for (module_index, canonical) in ir.modules.iter().enumerate() {
            let fallback_module = format!("module[{module_index}]");
            let value = ir::load(&canonical.bytes).map_err(|message| {
                PythonArtifactPlanError::InvalidModule {
                    module_index,
                    module: fallback_module.clone(),
                    message,
                }
            })?;
            modules.push(load_module(module_index, fallback_module, value)?);
        }

        modules.sort_by(|left, right| left.module.cmp(&right.module));
        for pair in modules.windows(2) {
            if pair[0].module == pair[1].module {
                return Err(PythonArtifactPlanError::InvalidModule {
                    module_index: 0,
                    module: pair[0].module.clone(),
                    message: "duplicate canonical module name".to_owned(),
                });
            }
        }
        Ok(Self { modules })
    }

    /// Alias for [`Self::from_ir`].
    pub fn new(ir: &CanonicalIr) -> Result<Self, PythonArtifactPlanError> {
        Self::from_ir(ir)
    }

    /// Borrow modules in deterministic dotted-name order.
    pub fn modules(&self) -> &[PythonArtifactModule] {
        &self.modules
    }

    /// Enumerate all declarations in module/name order.
    pub fn declarations(&self) -> Vec<(String, Value)> {
        self.modules
            .iter()
            .flat_map(|module| {
                module
                    .declarations
                    .iter()
                    .cloned()
                    .map(|declaration| (module.module.clone(), declaration))
            })
            .collect()
    }
    /// Enumerate public free functions and every implementation method in
    /// deterministic module, declaration, and method source order.
    pub fn callables(&self) -> Vec<PythonCallable> {
        self.modules
            .iter()
            .flat_map(|module| {
                module
                    .declarations
                    .iter()
                    .zip(&module.declaration_info)
                    .flat_map(|(declaration, info)| match info.kind.as_str() {
                        "function" if info.public => vec![PythonCallable {
                            module: module.module.clone(),
                            cott_symbol: info.name.clone(),
                            name: info
                                .name
                                .rsplit('.')
                                .next()
                                .expect("validated canonical function name")
                                .to_owned(),
                            kind: PythonCallableKind::Function,
                            declaration: declaration.clone(),
                            owner: None,
                        }],
                        "impl" => {
                            let concrete = info
                                .name
                                .rsplit('.')
                                .next()
                                .expect("validated canonical implementation name");
                            declaration
                                .get("methods")
                                .and_then(Value::as_array)
                                .into_iter()
                                .flatten()
                                .filter_map(|method| {
                                    method.get("name").and_then(Value::as_str).map(|name| {
                                        PythonCallable {
                                            module: module.module.clone(),
                                            cott_symbol: format!(
                                                "{}.{}.{}",
                                                module.module, concrete, name
                                            ),
                                            name: name.to_owned(),
                                            kind: PythonCallableKind::ImplMethod {
                                                concrete: concrete.to_owned(),
                                            },
                                            declaration: method.clone(),
                                            owner: Some(declaration.clone()),
                                        }
                                    })
                                })
                                .collect()
                        }
                        _ => Vec::new(),
                    })
                    .collect::<Vec<_>>()
            })
            .collect()
    }

    /// Return a plan containing only public declarations.
    pub fn public_projection(&self) -> Self {
        Self {
            modules: self
                .modules
                .iter()
                .map(|module| {
                    let selected = module
                        .declarations
                        .iter()
                        .zip(&module.declaration_info)
                        .filter(|(_, info)| info.public)
                        .map(|(declaration, info)| (declaration.clone(), info.clone()))
                        .collect::<Vec<_>>();
                    PythonArtifactModule {
                        module: module.module.clone(),
                        imports: module.imports.clone(),
                        declarations: selected
                            .iter()
                            .map(|(declaration, _)| declaration.clone())
                            .collect(),
                        declaration_info: selected.into_iter().map(|(_, info)| info).collect(),
                    }
                })
                .collect(),
        }
    }
    /// Project public declarations for generation identity without source-only
    /// metadata.
    pub fn contract_surface(&self) -> Value {
        let mut modules = Map::new();
        for module in self.public_projection().modules {
            let mut declarations = module.declarations;
            for declaration in &mut declarations {
                strip_source_metadata(declaration);
            }
            modules.insert(
                module.module,
                serde_json::json!({"declarations": declarations}),
            );
        }
        Value::Object(modules)
    }

    /// Enumerate public free functions and every implementation method.
    pub fn public_callables(&self) -> Vec<PythonCallable> {
        self.callables()
    }
}

fn load_module(
    module_index: usize,
    fallback_module: String,
    value: Value,
) -> Result<PythonArtifactModule, PythonArtifactPlanError> {
    let object = value.as_object().ok_or_else(|| {
        invalid_module(
            module_index,
            fallback_module.clone(),
            "module must be an object".to_owned(),
        )
    })?;
    let module = required_string(object, "module")
        .map_err(|message| invalid_module(module_index, fallback_module.clone(), message))?;
    if module.is_empty() || module.split('.').any(str::is_empty) {
        return Err(invalid_module(
            module_index,
            module,
            "module name must be a non-empty dotted string".to_owned(),
        ));
    }
    let imports = required_array(object, "imports")
        .map_err(|message| invalid_module(module_index, module.clone(), message))?
        .iter()
        .enumerate()
        .map(|(index, import)| {
            import.as_str().map(str::to_owned).ok_or_else(|| {
                invalid_module(
                    module_index,
                    module.clone(),
                    format!("invalid `imports[{index}]` field"),
                )
            })
        })
        .collect::<Result<Vec<_>, _>>()?;
    let declarations = required_array(object, "declarations")
        .map_err(|message| invalid_module(module_index, module.clone(), message))?;
    let mut values = Vec::with_capacity(declarations.len());
    let mut infos = Vec::with_capacity(declarations.len());
    for (declaration_index, declaration) in declarations.iter().enumerate() {
        let info = declaration_info(module_index, &module, declaration_index, declaration)?;
        values.push(declaration.clone());
        infos.push(info);
    }
    // Keep values paired with the same deterministic declaration order.
    let mut pairs = values.into_iter().zip(infos).collect::<Vec<_>>();
    pairs.sort_by(|(_, left), (_, right)| {
        left.source_order
            .cmp(&right.source_order)
            .then_with(|| left.name.cmp(&right.name))
    });
    let (declarations, declaration_info): (Vec<_>, Vec<_>) = pairs.into_iter().unzip();
    Ok(PythonArtifactModule {
        module,
        imports,
        declarations,
        declaration_info,
    })
}

fn declaration_info(
    module_index: usize,
    module: &str,
    declaration_index: usize,
    declaration: &Value,
) -> Result<DeclarationInfo, PythonArtifactPlanError> {
    let object = declaration.as_object().ok_or_else(|| {
        malformed(
            module_index,
            module,
            declaration_index,
            "declaration must be an object",
        )
    })?;
    let kind = required_string(object, "kind")
        .map_err(|message| malformed(module_index, module, declaration_index, message))?;
    let name = required_string(object, "name")
        .map_err(|message| malformed(module_index, module, declaration_index, message))?;
    let public = object
        .get("public")
        .and_then(Value::as_bool)
        .ok_or_else(|| {
            malformed(
                module_index,
                module,
                declaration_index,
                "missing or invalid `public` field",
            )
        })?;
    let source_order = object
        .get("source_order")
        .and_then(Value::as_u64)
        .ok_or_else(|| {
            malformed(
                module_index,
                module,
                declaration_index,
                "missing or invalid `source_order` field",
            )
        })?;
    let prefix = format!("{module}.");
    if !name.starts_with(&prefix)
        || name.len() == prefix.len()
        || name.split('.').any(str::is_empty)
    {
        return Err(malformed(
            module_index,
            module,
            declaration_index,
            "declaration `name` must be a dotted name under its module",
        ));
    }
    Ok(DeclarationInfo {
        name,
        kind,
        public,
        source_order,
    })
}

fn required_string(object: &Map<String, Value>, field: &str) -> Result<String, String> {
    object
        .get(field)
        .and_then(Value::as_str)
        .map(str::to_owned)
        .ok_or_else(|| format!("missing or invalid `{field}` field"))
}

fn required_array<'a>(
    object: &'a Map<String, Value>,
    field: &str,
) -> Result<&'a Vec<Value>, String> {
    object
        .get(field)
        .and_then(Value::as_array)
        .ok_or_else(|| format!("missing or invalid `{field}` field"))
}

fn invalid_module(module_index: usize, module: String, message: String) -> PythonArtifactPlanError {
    PythonArtifactPlanError::InvalidModule {
        module_index,
        module,
        message,
    }
}

fn malformed(
    module_index: usize,
    module: &str,
    declaration_index: usize,
    message: impl Into<String>,
) -> PythonArtifactPlanError {
    PythonArtifactPlanError::MalformedDeclaration {
        module_index,
        module: module.to_owned(),
        declaration_index,
        message: message.into(),
    }
}

fn strip_source_metadata(value: &mut Value) {
    match value {
        Value::Array(values) => {
            for value in values {
                strip_source_metadata(value);
            }
        }
        Value::Object(object) => {
            object.remove("span");
            object.remove("source_order");
            for value in object.values_mut() {
                strip_source_metadata(value);
            }
        }
        _ => {}
    }
}
