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
    AsyncFunction,
    ImplMethod { concrete: String },
    AsyncImplMethod { concrete: String },
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
    /// Enumerate public free functions, trait-default free-function
    /// dependencies, and every implementation method in deterministic module,
    /// declaration, and method source order.
    pub fn callables(&self) -> Vec<PythonCallable> {
        let trait_declarations = self
            .modules
            .iter()
            .flat_map(|module| &module.declarations)
            .filter_map(Value::as_object)
            .filter(|declaration| declaration.get("kind").and_then(Value::as_str) == Some("trait"))
            .filter_map(|declaration| {
                Some((
                    declaration.get("name")?.as_str()?.to_owned(),
                    Value::Object(declaration.clone()),
                ))
            })
            .collect::<std::collections::BTreeMap<_, _>>();
        let default_dependencies = self
            .modules
            .iter()
            .flat_map(|module| &module.declarations)
            .filter_map(Value::as_object)
            .filter(|declaration| declaration.get("kind").and_then(Value::as_str) == Some("impl"))
            .flat_map(|implementation| {
                implementation
                    .get("selected_methods")
                    .and_then(Value::as_array)
                    .into_iter()
                    .flatten()
                    .filter_map(|slot| {
                        let selected = slot.get("selected")?.as_object()?;
                        if !matches!(
                            selected.get("origin")?.as_str()?,
                            "default" | "specialization"
                        ) {
                            return None;
                        }
                        let function = selected.get("function")?.as_object()?;
                        Some(format!(
                            "{}.{}",
                            function.get("module")?.as_str()?,
                            function.get("symbol")?.as_str()?
                        ))
                    })
            })
            .collect::<std::collections::BTreeSet<_>>();
        self.modules
            .iter()
            .flat_map(|module| {
                module
                    .declarations
                    .iter()
                    .zip(&module.declaration_info)
                    .flat_map(|(declaration, info)| match info.kind.as_str() {
                        "function"
                            if info.public || default_dependencies.contains(info.name.as_str()) =>
                        {
                            let callable_kind = declaration
                                .get("callable_kind")
                                .and_then(Value::as_str)
                                .expect("validated canonical function callable_kind");
                            vec![PythonCallable {
                                module: module.module.clone(),
                                cott_symbol: info.name.clone(),
                                name: info
                                    .name
                                    .rsplit('.')
                                    .next()
                                    .expect("validated canonical function name")
                                    .to_owned(),
                                kind: match callable_kind {
                                    "sync" => PythonCallableKind::Function,
                                    "async" => PythonCallableKind::AsyncFunction,
                                    _ => unreachable!("validated canonical function callable_kind"),
                                },
                                declaration: declaration.clone(),
                                owner: None,
                            }]
                        }
                        "impl" => {
                            let implementation = declaration
                                .as_object()
                                .expect("validated canonical implementation declaration");
                            let concrete = info
                                .name
                                .rsplit('.')
                                .next()
                                .expect("validated canonical implementation name");
                            let explicit = declaration
                                .get("methods")
                                .and_then(Value::as_array)
                                .map(Vec::as_slice)
                                .unwrap_or_default();
                            let mut selected_names = std::collections::BTreeSet::new();
                            let mut methods = Vec::new();
                            for slot in declaration
                                .get("selected_methods")
                                .and_then(Value::as_array)
                                .into_iter()
                                .flatten()
                            {
                                let Some(trait_method) =
                                    slot.get("trait_method").and_then(Value::as_str)
                                else {
                                    continue;
                                };
                                let Some(method_name) = trait_method.rsplit('.').next() else {
                                    continue;
                                };
                                let Some(selected) =
                                    slot.get("selected").and_then(Value::as_object)
                                else {
                                    continue;
                                };
                                let source = if selected.get("origin").and_then(Value::as_str)
                                    == Some("explicit")
                                {
                                    explicit
                                        .iter()
                                        .find(|method| {
                                            method
                                                .get("name")
                                                .and_then(Value::as_str)
                                                .map(local_name)
                                                == Some(method_name)
                                        })
                                        .cloned()
                                } else {
                                    resolve_trait_default(
                                        implementation,
                                        slot.get("trait_ref").and_then(Value::as_object),
                                        trait_method,
                                        selected,
                                        &trait_declarations,
                                    )
                                };
                                let Some(mut method) = source else {
                                    continue;
                                };
                                let Some(method_object) = method.as_object_mut() else {
                                    continue;
                                };
                                let callable_kind = slot
                                    .get("callable_kind")
                                    .and_then(Value::as_str)
                                    .expect("validated implementation method callable_kind");
                                method_object.insert(
                                    "name".to_owned(),
                                    Value::String(method_name.to_owned()),
                                );
                                method_object.insert(
                                    "callable_kind".to_owned(),
                                    Value::String(callable_kind.to_owned()),
                                );
                                method_object
                                    .insert("selected".to_owned(), Value::Object(selected.clone()));
                                method_object.insert(
                                    "receiver_type".to_owned(),
                                    slot.get("receiver_type").cloned().unwrap_or(Value::Null),
                                );
                                method_object.insert(
                                    "trait_method".to_owned(),
                                    Value::String(trait_method.to_owned()),
                                );
                                if selected_names.insert(method_name.to_owned()) {
                                    methods.push(method);
                                }
                            }
                            methods
                                .into_iter()
                                .filter_map(|method| {
                                    let name = method.get("name")?.as_str()?.to_owned();
                                    Some(PythonCallable {
                                        module: module.module.clone(),
                                        cott_symbol: format!(
                                            "{}.{}.{}",
                                            module.module, concrete, name
                                        ),
                                        name,
                                        kind: match method
                                            .get("callable_kind")
                                            .and_then(Value::as_str)
                                            .expect("validated implementation method callable_kind")
                                        {
                                            "sync" => PythonCallableKind::ImplMethod {
                                                concrete: concrete.to_owned(),
                                            },
                                            "async" => PythonCallableKind::AsyncImplMethod {
                                                concrete: concrete.to_owned(),
                                            },
                                            _ => unreachable!(
                                                "validated implementation method callable_kind"
                                            ),
                                        },
                                        declaration: method,
                                        owner: Some(declaration.clone()),
                                    })
                                })
                                .collect()
                        }
                        "scenario" => Vec::new(),
                        _ => Vec::new(),
                    })
                    .collect::<Vec<_>>()
            })
            .collect()
    }

    /// Return public declarations plus scenarios, which affect contract identity
    /// without becoming a Python ABI symbol.
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
                        .filter(|(_, info)| info.public || info.kind == "scenario")
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
    if kind == "function"
        && !matches!(
            object.get("callable_kind").and_then(Value::as_str),
            Some("sync" | "async")
        )
    {
        return Err(malformed(
            module_index,
            module,
            declaration_index,
            "missing or invalid `callable_kind` field",
        ));
    }
    if kind == "impl" {
        validate_impl_selection(object)
            .map_err(|message| malformed(module_index, module, declaration_index, message))?;
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
fn validate_impl_selection(object: &Map<String, Value>) -> Result<(), String> {
    let selected = required_array(object, "selected_methods")?;
    let mut explicit = std::collections::BTreeSet::new();
    let mut effective_callable_kind = None;
    for slot in selected {
        let slot = slot
            .as_object()
            .ok_or_else(|| "selected implementation method must be an object".to_owned())?;
        let trait_method = required_string(slot, "trait_method")?;
        let method_name = local_name(&trait_method);
        let callable_kind = required_string(slot, "callable_kind")?;
        if !matches!(callable_kind.as_str(), "sync" | "async") {
            return Err("selected implementation method callable_kind is invalid".to_owned());
        }
        if effective_callable_kind
            .replace(callable_kind.clone())
            .is_some_and(|previous| previous != callable_kind)
        {
            return Err("implementation methods must have one callable_kind".to_owned());
        }
        let selected = slot
            .get("selected")
            .and_then(Value::as_object)
            .ok_or_else(|| "selected implementation method is missing `selected`".to_owned())?;
        let kind = required_string(selected, "origin")?;
        let function = selected
            .get("function")
            .and_then(Value::as_object)
            .ok_or_else(|| "selected implementation method is missing `function`".to_owned())?;
        let function_module = required_string(function, "module")?;
        let function_symbol = required_string(function, "symbol")?;
        if required_string(function, "verified_facade")?
            != format!("{function_module}.{function_symbol}")
        {
            return Err("selected implementation method has invalid provenance".to_owned());
        }
        match kind.as_str() {
            "explicit" => {
                explicit.insert(method_name.to_owned());
            }
            "default" | "specialization" => {}
            _ => return Err("selected implementation method origin is invalid".to_owned()),
        }
    }
    for method in required_array(object, "methods")? {
        let method = method
            .as_object()
            .ok_or_else(|| "implementation method must be an object".to_owned())?;
        let name = required_string(method, "name")?;
        let callable_kind = required_string(method, "callable_kind")?;
        if !matches!(callable_kind.as_str(), "sync" | "async")
            || effective_callable_kind.as_deref() != Some(callable_kind.as_str())
        {
            return Err("implementation methods must have one callable_kind".to_owned());
        }
        if !explicit.contains(local_name(&name)) {
            return Err(format!(
                "implementation method `{}` is absent from `selected_methods`",
                local_name(&name)
            ));
        }
    }
    Ok(())
}

fn resolve_trait_default(
    implementation: &Map<String, Value>,
    slot_trait_ref: Option<&Map<String, Value>>,
    trait_method: &str,
    selected: &Map<String, Value>,
    trait_declarations: &std::collections::BTreeMap<String, Value>,
) -> Option<Value> {
    let (trait_name, method_name) = trait_method.rsplit_once('.')?;
    let trait_declaration = trait_declarations.get(trait_name)?.as_object()?;
    let trait_ref = slot_trait_ref.or_else(|| {
        implementation
            .get("traits")?
            .as_array()?
            .iter()
            .filter_map(Value::as_object)
            .find(|trait_ref| {
                trait_ref.get("kind").and_then(Value::as_str) == Some("named")
                    && trait_ref.get("name").and_then(Value::as_str) == Some(trait_name)
            })
    })?;
    let mut method = trait_declaration
        .get("methods")?
        .as_array()?
        .iter()
        .find(|method| {
            method.get("name").and_then(Value::as_str).map(local_name) == Some(method_name)
        })?
        .clone();
    (selected.get("origin").and_then(Value::as_str) == Some("specialization")
        || method.get("default")? == selected.get("function")?)
    .then_some(())?;
    substitute_trait_arguments(&mut method, trait_declaration, trait_ref);
    Some(method)
}

fn substitute_trait_arguments(
    value: &mut Value,
    trait_declaration: &Map<String, Value>,
    trait_ref: &Map<String, Value>,
) {
    let mut types = std::collections::BTreeMap::new();
    let mut constants = std::collections::BTreeMap::new();
    for (parameter, argument) in trait_declaration
        .get("generics")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter_map(Value::as_object)
        .zip(
            trait_ref
                .get("args")
                .and_then(Value::as_array)
                .into_iter()
                .flatten(),
        )
    {
        let Some(name) = parameter.get("name").and_then(Value::as_str) else {
            continue;
        };
        match parameter.get("kind").and_then(Value::as_str) {
            Some("type") => {
                if let Some(argument) = argument.get("type") {
                    types.insert(name.to_owned(), argument.clone());
                }
            }
            Some("const") => {
                if let Some(argument) = argument.get("value") {
                    constants.insert(name.to_owned(), argument.clone());
                }
            }
            _ => {}
        }
    }
    substitute_generic_arguments(value, &types, &constants);
}

fn substitute_generic_arguments(
    value: &mut Value,
    types: &std::collections::BTreeMap<String, Value>,
    constants: &std::collections::BTreeMap<String, Value>,
) {
    let replacement = value.as_object().and_then(|object| {
        match (
            object.get("kind").and_then(Value::as_str),
            object.get("name").and_then(Value::as_str),
        ) {
            (Some("type_parameter"), Some(name)) => types.get(name).cloned(),
            (Some("parameter"), Some(name)) => constants.get(name).cloned(),
            _ => None,
        }
    });
    if let Some(replacement) = replacement {
        *value = replacement;
        return;
    }
    match value {
        Value::Array(values) => {
            for value in values {
                substitute_generic_arguments(value, types, constants);
            }
        }
        Value::Object(object) => {
            for value in object.values_mut() {
                substitute_generic_arguments(value, types, constants);
            }
        }
        _ => {}
    }
}

fn local_name(name: &str) -> &str {
    name.rsplit('.').next().unwrap_or(name)
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
