use std::collections::{BTreeMap, BTreeSet};
use std::fmt::Write as _;
use std::path::{Component, Path, PathBuf};

use serde_json::{Map, Value};

use crate::hash::sha256_hex;
use crate::kotlin::expressions;
use crate::manifest::{KotlinProjectConfig, RuntimeValidation};

use super::expressions::{clause_label, render_condition, render_expression, render_span};
use super::runtime::render_runtime;
use super::types::{
    self, KotlinTypeContext, associated_type_name, const_marker, const_parameters_in,
    escape_identifier, kotlin_string, local_name, opaque_marker, render_const_kind,
    render_const_value, render_const_witness, render_qualified,
    render_type as render_type_uncontextual, render_type_contextual, render_value, trait_marker,
};
use super::{KotlinBinding, KotlinCallable, KotlinEmission, KotlinModule, KotlinOwner, KotlinPlan};

pub fn render_type(plan: &KotlinPlan, ty: &Value) -> Result<String, String> {
    let declarations = declaration_index(plan)?;
    render_contextual_type(ty, None, &declarations)
}

const KOTLIN_RUNTIME_ABI: i32 = 1;

pub fn emit(
    config: &KotlinProjectConfig,
    plan: &KotlinPlan,
    bindings: &[KotlinBinding],
) -> Result<KotlinEmission, String> {
    validate_modules(plan)?;
    let declarations = declaration_index(plan)?;
    let callables = plan
        .callables()
        .into_iter()
        .map(|callable| (callable.symbol.clone(), callable))
        .collect::<BTreeMap<_, _>>();
    validate_bindings(bindings, &callables)?;

    let bindings_by_symbol = bindings
        .iter()
        .map(|binding| (binding.cott_symbol.as_str(), binding))
        .collect::<BTreeMap<_, _>>();
    let unresolved = required_bindings(&callables)
        .into_iter()
        .filter(|symbol| !bindings_by_symbol.contains_key(symbol.as_str()))
        .collect::<Vec<_>>();

    let mut files = render_runtime(&config.project.name, &config.project.version);
    if files.keys().any(|path| !safe_artifact_path(path)) {
        return Err("Kotlin runtime renderer returned an unsafe artifact path".to_owned());
    }
    let marker_source = render_markers(plan)?;
    insert_file(
        &mut files,
        PathBuf::from("kotlin/cott_runtime/CottMarkers.kt"),
        marker_source.into_bytes(),
    )?;

    let mut public_symbols = BTreeMap::new();
    for module in &plan.modules {
        let mut exported = public_target_names(module)?;
        exported.sort();
        exported.dedup();
        let types = render_types_file(config, module, &declarations)?;
        let facade = render_facade_file(
            config,
            module,
            &declarations,
            &callables,
            &bindings_by_symbol,
        )?;
        public_symbols.insert(module.name.clone(), exported);
        insert_file(&mut files, types_path(&module.name)?, types.into_bytes())?;
        insert_file(&mut files, facade_path(&module.name)?, facade.into_bytes())?;
    }

    for canonical in &plan.ir.modules {
        let name = canonical.module.as_string();
        if plan.multiline_module(&name).is_none() {
            return Err(format!(
                "authoritative canonical IR contains unknown module `{name}`"
            ));
        }
        if !canonical.bytes.ends_with(b"\n") || canonical.bytes.ends_with(b"\n\n") {
            return Err(format!(
                "authoritative canonical IR for `{name}` must end in exactly one newline"
            ));
        }
        insert_file(&mut files, ir_path(&name)?, canonical.bytes.clone())?;
    }

    for binding in bindings {
        insert_file(
            &mut files,
            binding.runtime_origin.clone(),
            binding.bytes.clone(),
        )?;
    }

    Ok(KotlinEmission {
        files,
        public_symbols,
        unresolved,
    })
}

trait PlanLookup {
    fn multiline_module(&self, name: &str) -> Option<&KotlinModule>;
}

impl PlanLookup for KotlinPlan {
    fn multiline_module(&self, name: &str) -> Option<&KotlinModule> {
        self.modules.iter().find(|module| module.name == name)
    }
}
#[derive(Clone)]
struct EmissionTypeContext<'a> {
    declarations: &'a BTreeMap<String, (&'a str, &'a Map<String, Value>)>,
    projections: BTreeMap<String, String>,
    trait_scope: BTreeMap<(String, String), String>,
    named_arguments: BTreeMap<String, Vec<String>>,
}

impl<'a> EmissionTypeContext<'a> {
    fn new(declarations: &'a BTreeMap<String, (&'a str, &'a Map<String, Value>)>) -> Self {
        Self {
            declarations,
            projections: BTreeMap::new(),
            trait_scope: BTreeMap::new(),
            named_arguments: BTreeMap::new(),
        }
    }
}

impl KotlinTypeContext for EmissionTypeContext<'_> {
    fn named_associated_arguments(&self, ty: &Value, name: &str) -> Result<Vec<String>, String> {
        let identity = serde_json::to_string(ty)
            .map_err(|error| format!("serialize contextual Kotlin type: {error}"))?;
        if let Some(arguments) = self.named_arguments.get(&identity) {
            return Ok(arguments.clone());
        }
        if self
            .declarations
            .get(name)
            .is_some_and(|(kind, _)| *kind == "trait")
        {
            return Ok(vec![
                "*".to_owned();
                trait_slot_definitions(ty, self.declarations)?.len()
            ]);
        }
        Ok(Vec::new())
    }

    fn associated_projection(
        &self,
        base: &Value,
        trait_name: &str,
        slot_name: &str,
    ) -> Result<String, String> {
        let key = associated_projection_key(base, trait_name, slot_name)?;
        if let Some(name) = self.projections.get(&key) {
            return Ok(name.clone());
        }
        if let Some(name) = self
            .trait_scope
            .get(&(trait_name.to_owned(), local_name(slot_name).to_owned()))
        {
            return Ok(name.clone());
        }

        associated_projection_name(base, trait_name, slot_name)
    }
}
fn render_contextual_type(
    ty: &Value,
    module: Option<&str>,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
) -> Result<String, String> {
    let context = EmissionTypeContext::new(declarations);
    render_type_contextual(ty, module, Some(&context))
}

#[derive(Clone)]
struct TraitSlot {
    trait_name: String,
    slot_name: String,
    bounds: Vec<Value>,
}

#[derive(Clone)]
struct AssociatedParameter {
    base: Value,
    trait_name: String,
    slot_name: String,
    bounds: Vec<Value>,
}
fn declared_associated_identity<'a>(
    associated: &'a Map<String, Value>,
    context: &str,
) -> Result<(&'a str, &'a str), String> {
    let identity = required_string(associated, "name", context)?;
    let (trait_name, slot_name) = identity.rsplit_once('.').ok_or_else(|| {
        format!("trait `{context}` associated slot `{identity}` is not canonically qualified")
    })?;
    if trait_name.is_empty() || slot_name.is_empty() {
        return Err(format!(
            "trait `{context}` associated slot `{identity}` is not canonically qualified"
        ));
    }
    Ok((trait_name, slot_name))
}

struct CallableRendering<'a> {
    context: EmissionTypeContext<'a>,
    generics: String,
    where_bounds: String,
}

fn associated_projection_key(
    base: &Value,
    trait_name: &str,
    slot_name: &str,
) -> Result<String, String> {
    let base = serde_json::to_string(base)
        .map_err(|error| format!("serialize associated projection base: {error}"))?;
    Ok(format!("{trait_name}::{}::{base}", local_name(slot_name)))
}

fn associated_projection_name(
    base: &Value,
    trait_name: &str,
    slot_name: &str,
) -> Result<String, String> {
    types::projected_associated_type_name(base, trait_name, slot_name)
}

fn declaration_trait_ref(declaration: &Map<String, Value>) -> Result<Value, String> {
    let name = required_string(declaration, "name", "trait")?;
    let args = required_array(declaration, "generics", name)?
        .iter()
        .map(|generic| {
            let generic = generic
                .as_object()
                .ok_or_else(|| format!("trait `{name}` generic must be an object"))?;
            let parameter = required_string(generic, "name", name)?;
            match required_string(generic, "kind", name)? {
                "type" => Ok(serde_json::json!({
                    "kind": "type",
                    "type": {"kind": "type_parameter", "name": parameter},
                })),
                "const" => Ok(serde_json::json!({
                    "kind": "const",
                    "value": {
                        "kind": "parameter",
                        "name": parameter,
                        "type": required_string(generic, "type", name)?,
                    },
                })),
                other => Err(format!(
                    "trait `{name}` has unsupported generic kind `{other}`"
                )),
            }
        })
        .collect::<Result<Vec<_>, String>>()?;
    Ok(serde_json::json!({"args": args, "kind": "named", "name": name}))
}

fn trait_specializations_from_ref(
    trait_ref: &Value,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
) -> Result<Vec<Value>, String> {
    let root_identity = serde_json::to_string(trait_ref)
        .map_err(|error| format!("serialize root trait specialization: {error}"))?;
    let mut pending = vec![trait_ref.clone()];
    let mut resolved = BTreeMap::<String, Value>::new();
    while let Some(current) = pending.pop() {
        let identity = serde_json::to_string(&current)
            .map_err(|error| format!("serialize trait specialization: {error}"))?;
        if resolved.contains_key(&identity) {
            continue;
        }
        let object = current
            .as_object()
            .ok_or_else(|| "trait specialization must be an object".to_owned())?;
        let name = required_string(object, "name", "trait specialization")?;
        let (kind, declaration) = declarations
            .get(name)
            .copied()
            .ok_or_else(|| format!("unknown trait specialization `{name}`"))?;
        if kind != "trait" {
            return Err(format!(
                "trait specialization `{name}` resolves to `{kind}`"
            ));
        }
        for closure in required_array(declaration, "closure", name)? {
            pending.push(instantiate_type(closure, declaration, object));
        }
        resolved.insert(identity, current);
    }
    let root = resolved
        .remove(&root_identity)
        .ok_or_else(|| "trait closure lost its root specialization".to_owned())?;
    let mut ordered = vec![root];
    ordered.extend(resolved.into_values());
    Ok(ordered)
}

fn trait_slot_definitions(
    trait_ref: &Value,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
) -> Result<Vec<TraitSlot>, String> {
    let mut slots = Vec::new();
    let mut seen = BTreeSet::new();
    for specialization in trait_specializations_from_ref(trait_ref, declarations)? {
        let object = specialization
            .as_object()
            .ok_or_else(|| "trait specialization must be an object".to_owned())?;
        let name = required_string(object, "name", "trait specialization")?;
        let (_, declaration) = declarations
            .get(name)
            .copied()
            .ok_or_else(|| format!("unknown trait specialization `{name}`"))?;
        for associated in required_array(declaration, "associated_types", name)? {
            let associated = associated
                .as_object()
                .ok_or_else(|| format!("trait `{name}` associated type must be an object"))?;
            let (trait_name, slot_name) = declared_associated_identity(associated, name)?;
            if !seen.insert((trait_name, slot_name)) {
                continue;
            }
            let bounds = required_array(associated, "bounds", slot_name)?
                .iter()
                .map(|bound| instantiate_type(bound, declaration, object))
                .collect();
            slots.push(TraitSlot {
                trait_name: trait_name.to_owned(),
                slot_name: slot_name.to_owned(),
                bounds,
            });
        }
    }
    Ok(slots)
}

fn is_trait_type(ty: &Value, declarations: &BTreeMap<String, (&str, &Map<String, Value>)>) -> bool {
    let Some(name) = ty
        .as_object()
        .filter(|object| object.get("kind").and_then(Value::as_str) == Some("named"))
        .and_then(|object| object.get("name"))
        .and_then(Value::as_str)
    else {
        return false;
    };
    declarations
        .get(name)
        .is_some_and(|(kind, _)| *kind == "trait")
}

fn collect_associated_projections(
    value: &Value,
    output: &mut Vec<(Value, String, String)>,
) -> Result<(), String> {
    match value {
        Value::Array(values) => {
            for value in values {
                collect_associated_projections(value, output)?;
            }
        }
        Value::Object(object) => {
            if object.get("kind").and_then(Value::as_str) == Some("associated_projection") {
                output.push((
                    required(object, "base", "associated projection")?.clone(),
                    required_string(object, "trait", "associated projection")?.to_owned(),
                    required_string(object, "name", "associated projection")?.to_owned(),
                ));
                return Ok(());
            }
            for value in object.values() {
                collect_associated_projections(value, output)?;
            }
        }
        _ => {}
    }
    Ok(())
}

fn associated_slot_bounds(
    trait_name: &str,
    slot_name: &str,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
) -> Result<Vec<Value>, String> {
    let (kind, declaration) = declarations
        .get(trait_name)
        .copied()
        .ok_or_else(|| format!("unknown associated trait `{trait_name}`"))?;
    if kind != "trait" {
        return Err(format!(
            "associated trait `{trait_name}` resolves to `{kind}`"
        ));
    }
    let mut matched = None;
    for associated in required_array(declaration, "associated_types", trait_name)? {
        let associated = associated
            .as_object()
            .ok_or_else(|| format!("trait `{trait_name}` associated slot must be an object"))?;
        let (declaring_trait, declared_slot) =
            declared_associated_identity(associated, trait_name)?;
        if declaring_trait == trait_name && declared_slot == local_name(slot_name) {
            matched = Some(associated);
            break;
        }
    }
    let associated = matched
        .ok_or_else(|| format!("trait `{trait_name}` has no associated slot `{slot_name}`"))?;
    Ok(required_array(associated, "bounds", slot_name)?.clone())
}

fn associated_assignment_type<'a>(
    implementation: &'a Map<String, Value>,
    trait_name: &str,
    slot_name: &str,
) -> Option<&'a Value> {
    implementation
        .get("associated_types")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .find(|assignment| {
            assignment.get("trait").and_then(Value::as_str) == Some(trait_name)
                && assignment
                    .get("name")
                    .and_then(Value::as_str)
                    .is_some_and(|candidate| local_name(candidate) == local_name(slot_name))
        })
        .and_then(|assignment| assignment.get("type"))
}

fn render_bound_for_base(
    bound: &Value,
    base: &Value,
    context: &EmissionTypeContext<'_>,
) -> Result<String, String> {
    let mut contextual = context.clone();
    if is_trait_type(bound, context.declarations) {
        let arguments = trait_slot_definitions(bound, context.declarations)?
            .iter()
            .map(|slot| associated_projection_name(base, &slot.trait_name, &slot.slot_name))
            .collect::<Result<Vec<_>, _>>()?;
        let identity = serde_json::to_string(bound)
            .map_err(|error| format!("serialize trait bound: {error}"))?;
        contextual.named_arguments.insert(identity, arguments);
    }
    render_type_contextual(bound, None, Some(&contextual))
}

fn callable_rendering<'a>(
    declaration: &Map<String, Value>,
    declarations: &'a BTreeMap<String, (&'a str, &'a Map<String, Value>)>,
    trait_scope: BTreeMap<(String, String), String>,
) -> Result<CallableRendering<'a>, String> {
    let mut associated = BTreeMap::<String, AssociatedParameter>::new();
    for generic in required_array(declaration, "generics", "callable")? {
        let generic = generic
            .as_object()
            .ok_or_else(|| "callable generic must be an object".to_owned())?;
        if generic.get("kind").and_then(Value::as_str) != Some("type") {
            continue;
        }
        let name = required_string(generic, "name", "callable generic")?;
        let base = serde_json::json!({"kind": "type_parameter", "name": name});
        for bound in required_array(generic, "bounds", name)? {
            if !is_trait_type(bound, declarations) {
                continue;
            }
            for slot in trait_slot_definitions(bound, declarations)? {
                let parameter =
                    associated_projection_name(&base, &slot.trait_name, &slot.slot_name)?;
                associated.entry(parameter).or_insert(AssociatedParameter {
                    base: base.clone(),
                    trait_name: slot.trait_name,
                    slot_name: slot.slot_name,
                    bounds: slot.bounds,
                });
            }
        }
    }
    let mut projections = Vec::new();
    collect_associated_projections(&Value::Object(declaration.clone()), &mut projections)?;
    for (base, trait_name, slot_name) in projections {
        if trait_scope.contains_key(&(trait_name.clone(), local_name(&slot_name).to_owned())) {
            continue;
        }
        let parameter = associated_projection_name(&base, &trait_name, &slot_name)?;
        if associated.contains_key(&parameter) {
            continue;
        }
        associated.insert(
            parameter,
            AssociatedParameter {
                base,
                bounds: associated_slot_bounds(&trait_name, &slot_name, declarations)?,
                trait_name,
                slot_name,
            },
        );
    }

    let mut context = EmissionTypeContext::new(declarations);
    context.trait_scope = trait_scope;
    for parameter in associated.values() {
        context.projections.insert(
            associated_projection_key(
                &parameter.base,
                &parameter.trait_name,
                &parameter.slot_name,
            )?,
            associated_projection_name(
                &parameter.base,
                &parameter.trait_name,
                &parameter.slot_name,
            )?,
        );
    }

    let mut generic_parts = Vec::new();
    let mut where_parts = Vec::new();
    for generic in required_array(declaration, "generics", "callable")? {
        let generic = generic
            .as_object()
            .ok_or_else(|| "callable generic must be an object".to_owned())?;
        let raw_name = required_string(generic, "name", "callable generic")?;
        let name = escape_identifier(raw_name)?;
        match required_string(generic, "kind", "callable generic")? {
            "type" => {
                let base = serde_json::json!({"kind": "type_parameter", "name": raw_name});
                let bounds = required_array(generic, "bounds", raw_name)?
                    .iter()
                    .map(|bound| render_bound_for_base(bound, &base, &context))
                    .collect::<Result<Vec<_>, _>>()?;
                generic_parts.push(format!(
                    "{name} : {}",
                    bounds
                        .first()
                        .cloned()
                        .unwrap_or_else(|| "kotlin.Any".to_owned())
                ));
                where_parts.extend(
                    bounds
                        .into_iter()
                        .skip(1)
                        .map(|bound| format!("{name} : {bound}")),
                );
            }
            "const" => generic_parts.push(format!("{name} : cott_runtime.CottConst")),
            other => {
                return Err(format!(
                    "callable generic `{name}` has unsupported kind `{other}`"
                ));
            }
        }
    }
    for (name, parameter) in &associated {
        let bounds = parameter
            .bounds
            .iter()
            .map(|bound| render_type_contextual(bound, None, Some(&context)))
            .collect::<Result<Vec<_>, _>>()?;
        generic_parts.push(format!(
            "{name} : {}",
            bounds
                .first()
                .cloned()
                .unwrap_or_else(|| "kotlin.Any".to_owned())
        ));
        where_parts.extend(
            bounds
                .into_iter()
                .skip(1)
                .map(|bound| format!("{name} : {bound}")),
        );
    }
    Ok(CallableRendering {
        context,
        generics: if generic_parts.is_empty() {
            String::new()
        } else {
            format!("<{}>", generic_parts.join(", "))
        },
        where_bounds: if where_parts.is_empty() {
            String::new()
        } else {
            format!(" where {}", where_parts.join(", "))
        },
    })
}

#[derive(Clone)]
struct OwnerConstWitness {
    name: String,
    ty: String,
}

fn selected_method_slot<'a>(
    owner: &'a Map<String, Value>,
    callable: &KotlinCallable,
) -> Result<&'a Map<String, Value>, String> {
    required_array(owner, "selected_methods", &callable.symbol)?
        .iter()
        .filter_map(Value::as_object)
        .find(|slot| {
            slot.get("trait_method")
                .and_then(Value::as_str)
                .map(local_name)
                == Some(callable.name.as_str())
        })
        .ok_or_else(|| {
            format!(
                "callable `{}` has no canonical selected method",
                callable.symbol
            )
        })
}

fn selected_method_generics(
    slot: &Map<String, Value>,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
) -> Result<Value, String> {
    let trait_method = required_string(slot, "trait_method", "selected method")?;
    let (trait_name, method_name) = trait_method
        .rsplit_once('.')
        .ok_or_else(|| format!("selected trait method `{trait_method}` is not qualified"))?;
    let (kind, trait_declaration) = declarations
        .get(trait_name)
        .copied()
        .ok_or_else(|| format!("selected method references unknown trait `{trait_name}`"))?;
    if kind != "trait" {
        return Err(format!(
            "selected method owner `{trait_name}` resolves to `{kind}`"
        ));
    }
    let method = required_array(trait_declaration, "methods", trait_name)?
        .iter()
        .filter_map(Value::as_object)
        .find(|method| {
            method.get("name").and_then(Value::as_str).map(local_name) == Some(method_name)
        })
        .ok_or_else(|| {
            format!("selected trait method `{trait_method}` has no canonical declaration")
        })?;
    let trait_ref = required(slot, "trait_ref", trait_method)?
        .as_object()
        .ok_or_else(|| format!("selected trait method `{trait_method}` has malformed trait_ref"))?;
    if required_string(trait_ref, "name", trait_method)? != trait_name {
        return Err(format!(
            "selected trait method `{trait_method}` has mismatched trait_ref"
        ));
    }
    Ok(instantiate_type(
        &Value::Array(required_array(method, "generics", trait_method)?.clone()),
        trait_declaration,
        trait_ref,
    ))
}

fn resolved_method_declaration(
    callable: &KotlinCallable,
    owner: &Map<String, Value>,
    slot: &Map<String, Value>,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
) -> Result<Value, String> {
    let mut declaration_value = callable.declaration.clone();
    let declaration = declaration_value.as_object_mut().ok_or_else(|| {
        format!(
            "callable `{}` declaration must be an object",
            callable.symbol
        )
    })?;
    declaration.insert(
        "generics".to_owned(),
        selected_method_generics(slot, declarations)?,
    );
    for field in ["parameters", "return_type", "callable_kind"] {
        declaration.insert(
            field.to_owned(),
            required(slot, field, &callable.symbol)?.clone(),
        );
    }
    substitute_associated_types(&mut declaration_value, owner);
    Ok(declaration_value)
}

fn selected_owner_const_witnesses(
    slot: &Map<String, Value>,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
) -> Result<Vec<OwnerConstWitness>, String> {
    let trait_ref = required(slot, "trait_ref", "selected method")?
        .as_object()
        .ok_or_else(|| "selected method trait_ref must be an object".to_owned())?;
    let trait_name = required_string(trait_ref, "name", "selected method trait_ref")?;
    let (kind, trait_declaration) = declarations
        .get(trait_name)
        .copied()
        .ok_or_else(|| format!("selected method references unknown trait `{trait_name}`"))?;
    if kind != "trait" {
        return Err(format!(
            "selected method owner `{trait_name}` resolves to `{kind}`"
        ));
    }
    let generics = required_array(trait_declaration, "generics", trait_name)?;
    let arguments = required_array(trait_ref, "args", trait_name)?;
    if generics.len() != arguments.len() {
        return Err(format!(
            "selected trait specialization `{trait_name}` has {} arguments for {} generics",
            arguments.len(),
            generics.len()
        ));
    }
    generics
        .iter()
        .zip(arguments)
        .filter(|(generic, _)| generic.get("kind").and_then(Value::as_str) == Some("const"))
        .map(|(generic, argument)| {
            if argument.get("kind").and_then(Value::as_str) != Some("const") {
                return Err(format!(
                    "selected trait `{trait_name}` const generic has a non-const argument"
                ));
            }
            let name = generic
                .get("name")
                .and_then(Value::as_str)
                .ok_or_else(|| format!("trait `{trait_name}` const generic is missing name"))?;
            let value = argument.get("value").ok_or_else(|| {
                format!("selected trait `{trait_name}` const argument is missing value")
            })?;
            Ok(OwnerConstWitness {
                name: format!("_cott_const_{}", safe_internal_name(name)),
                ty: types::render_const_marker(value)?,
            })
        })
        .collect()
}

pub fn implementation_signature(
    plan: &KotlinPlan,
    callable: &KotlinCallable,
) -> Result<String, String> {
    let declarations = declaration_index(plan)?;
    let mut owner_witnesses = Vec::new();
    let declaration_value = if let Some(owner) = callable.owner.as_ref() {
        let owner = owner
            .as_object()
            .ok_or_else(|| format!("callable `{}` owner must be an object", callable.symbol))?;
        let slot = selected_method_slot(owner, callable)?;
        owner_witnesses = selected_owner_const_witnesses(slot, &declarations)?;
        resolved_method_declaration(callable, owner, slot, &declarations)?
    } else {
        callable.declaration.clone()
    };
    let declaration = declaration_value.as_object().ok_or_else(|| {
        format!(
            "callable `{}` declaration must be an object",
            callable.symbol
        )
    })?;
    let callable_kind = required_string(declaration, "callable_kind", &callable.symbol)?;
    if !matches!(callable_kind, "sync" | "async") {
        return Err(format!(
            "callable `{}` has unsupported callable kind `{callable_kind}`",
            callable.symbol
        ));
    }
    let rendering = callable_rendering(declaration, &declarations, BTreeMap::new())?;
    let mut parameters = Vec::new();
    if let Some(owner) = callable.owner.as_ref() {
        let owner = owner
            .as_object()
            .ok_or_else(|| format!("callable `{}` owner must be an object", callable.symbol))?;
        let concrete = required_string(owner, "name", &callable.symbol)?;
        parameters.push(format!("self: {}", render_qualified(concrete)?));
    }
    parameters.extend(render_parameters_contextual(
        declaration,
        false,
        &rendering.context,
    )?);
    parameters.extend(
        owner_witnesses
            .iter()
            .map(|witness| format!("{}: {}", witness.name, witness.ty)),
    );
    let return_type = render_type_contextual(
        required(declaration, "return_type", &callable.symbol)?,
        None,
        Some(&rendering.context),
    )?;
    Ok(format!(
        "internal {}fun {} {}({}): {return_type}{}",
        if callable_kind == "async" {
            "suspend "
        } else {
            ""
        },
        rendering.generics,
        escape_identifier(&callable.name)?,
        parameters.join(", "),
        rendering.where_bounds,
    ))
}

fn validate_modules(plan: &KotlinPlan) -> Result<(), String> {
    if plan.modules.is_empty() {
        return Err("canonical Kotlin plan has no modules".to_owned());
    }
    let mut names = BTreeSet::new();
    for module in &plan.modules {
        if !names.insert(module.name.as_str()) {
            return Err(format!(
                "duplicate canonical Kotlin module `{}`",
                module.name
            ));
        }
        let root = module.name.split('.').next().unwrap_or_default();
        if matches!(
            root,
            "cott_runtime" | "cott_impl" | "java" | "javax" | "kotlin" | "android"
        ) {
            return Err(format!(
                "canonical module `{}` uses a reserved Kotlin package",
                module.name
            ));
        }
        render_qualified(&module.name)?;
    }
    let ir_names = plan
        .ir
        .modules
        .iter()
        .map(|module| module.module.as_string())
        .collect::<BTreeSet<_>>();
    let plan_names = plan
        .modules
        .iter()
        .map(|module| module.name.clone())
        .collect::<BTreeSet<_>>();
    if ir_names != plan_names {
        return Err("Kotlin plan modules differ from its authoritative canonical IR".to_owned());
    }
    Ok(())
}

fn declaration_index<'a>(
    plan: &'a KotlinPlan,
) -> Result<BTreeMap<String, (&'a str, &'a Map<String, Value>)>, String> {
    let mut declarations = BTreeMap::new();
    for module in &plan.modules {
        for (index, declaration) in module.declarations.iter().enumerate() {
            let declaration = declaration.as_object().ok_or_else(|| {
                format!(
                    "canonical declaration {}[{index}] must be an object",
                    module.name
                )
            })?;
            let name = required_string(declaration, "name", &module.name)?;
            if !name.starts_with(&format!("{}.", module.name)) {
                return Err(format!(
                    "canonical declaration `{name}` does not belong to module `{}`",
                    module.name
                ));
            }
            let kind = required_string(declaration, "kind", name)?;
            if !matches!(
                kind,
                "external_type"
                    | "alias"
                    | "newtype"
                    | "struct"
                    | "enum"
                    | "trait"
                    | "impl"
                    | "specialization"
                    | "rule"
                    | "resource"
                    | "const"
                    | "function"
                    | "scenario"
                    | "requirement"
            ) {
                return Err(format!(
                    "unsupported canonical declaration kind `{kind}` for `{name}`"
                ));
            }
            if declarations
                .insert(name.to_owned(), (kind, declaration))
                .is_some()
            {
                return Err(format!("duplicate canonical declaration identity `{name}`"));
            }
        }
    }
    Ok(declarations)
}

fn validate_bindings(
    bindings: &[KotlinBinding],
    callables: &BTreeMap<String, KotlinCallable>,
) -> Result<(), String> {
    let mut symbols = BTreeSet::new();
    let mut paths = BTreeSet::new();
    for binding in bindings {
        let callable = callables.get(&binding.cott_symbol).ok_or_else(|| {
            format!(
                "Kotlin binding `{}` does not match a canonical callable",
                binding.cott_symbol
            )
        })?;
        let mut expected_target = format!("cott_impl.{}.", callable.module);
        if let Some(owner) = callable.owner.as_ref().and_then(Value::as_object)
            && let Some(concrete) = owner.get("name").and_then(Value::as_str)
        {
            expected_target.push_str(local_name(concrete));
            expected_target.push('.');
        }
        expected_target.push_str(&callable.name);
        if binding.owner == KotlinOwner::Agent && binding.target_symbol != expected_target {
            return Err(format!(
                "Kotlin binding `{}` target must be `{expected_target}`",
                binding.cott_symbol
            ));
        }
        if !symbols.insert(binding.cott_symbol.as_str()) {
            return Err(format!(
                "duplicate Kotlin binding for `{}`",
                binding.cott_symbol
            ));
        }
        if !safe_artifact_path(&binding.runtime_origin)
            || binding
                .runtime_origin
                .extension()
                .and_then(|value| value.to_str())
                != Some("kt")
            || !binding.runtime_origin.starts_with("kotlin/cott_impl")
        {
            return Err(format!(
                "Kotlin binding `{}` has unsafe runtime origin `{}`",
                binding.cott_symbol,
                binding.runtime_origin.display()
            ));
        }
        if !paths.insert(binding.runtime_origin.as_path()) {
            return Err(format!(
                "Kotlin bindings collide at `{}`",
                binding.runtime_origin.display()
            ));
        }
        if binding.source_origin.is_absolute()
            || binding
                .source_origin
                .components()
                .any(|component| !matches!(component, Component::Normal(_)))
        {
            return Err(format!(
                "Kotlin binding `{}` has unsafe source origin `{}`",
                binding.cott_symbol,
                binding.source_origin.display()
            ));
        }
        render_qualified(&binding.target_symbol)?;
        let expected_hash = format!("sha256:{}", sha256_hex(&binding.bytes));
        if binding.content_hash != expected_hash {
            return Err(format!(
                "Kotlin binding `{}` content hash does not match its exact bytes",
                binding.cott_symbol
            ));
        }
    }
    Ok(())
}

fn required_bindings(callables: &BTreeMap<String, KotlinCallable>) -> BTreeSet<String> {
    callables
        .values()
        .filter(|callable| {
            callable.owner.is_none()
                || callable
                    .declaration
                    .get("selected")
                    .and_then(Value::as_object)
                    .and_then(|selected| selected.get("origin"))
                    .and_then(Value::as_str)
                    == Some("explicit")
        })
        .map(|callable| callable.symbol.clone())
        .collect()
}

fn render_markers(plan: &KotlinPlan) -> Result<String, String> {
    let declarations = declaration_index(plan)?;
    let mut constants = BTreeMap::<String, Value>::new();
    let mut opaques = BTreeSet::<String>::new();
    let mut trait_tokens = BTreeMap::<String, Value>::new();
    let mut tuple_arities = BTreeSet::<usize>::new();
    for module in &plan.modules {
        for declaration in &module.declarations {
            collect_markers(
                declaration,
                &mut constants,
                &mut opaques,
                &mut trait_tokens,
                &mut tuple_arities,
            )?;
            if declaration.get("kind").and_then(Value::as_str) == Some("impl")
                && let Some(implementation) = declaration.as_object()
            {
                for trait_ref in trait_specializations(implementation, &declarations)? {
                    trait_tokens.insert(trait_marker(&trait_ref)?, trait_ref);
                }
            }
        }
    }
    let mut out = generated_header("cott_runtime")?;
    out.push_str("\n@Target(AnnotationTarget.VALUE_PARAMETER)\n@Retention(AnnotationRetention.BINARY)\npublic annotation class CottKeywordOnly\n");
    for (name, value) in constants {
        let rendered = render_const_value(&value)?;
        let parameters = const_parameters_in(&value)?;
        if parameters.is_empty() {
            writeln!(
                out,
                "\npublic object {name} : CottConst {{\n    override val value: java.math.BigInteger\n        get() = CottRuntime.mathInt({rendered})\n}}"
            )
            .expect("writing to String cannot fail");
        } else {
            let generics = parameters
                .iter()
                .map(|parameter| {
                    format!(
                        "{} : CottConst",
                        escape_identifier(parameter).expect("validated canonical const parameter")
                    )
                })
                .collect::<Vec<_>>()
                .join(", ");
            let witnesses = parameters
                .iter()
                .map(|parameter| {
                    format!(
                        "private val _cott_const_{}: {}",
                        safe_internal_name(parameter),
                        escape_identifier(parameter).expect("validated canonical const parameter")
                    )
                })
                .collect::<Vec<_>>()
                .join(", ");
            writeln!(
                out,
                "\npublic class {name}<{generics}>({witnesses}) : CottConst {{\n    override val value: java.math.BigInteger\n        get() = CottRuntime.mathInt({rendered})\n}}"
            )
            .expect("writing to String cannot fail");
        }
    }
    for tag in opaques {
        let name = opaque_marker(&tag);
        writeln!(
            out,
            "\npublic object {name} : CottOpaqueTag {{\n    override val tag: kotlin.String\n        get() = {}\n}}",
            kotlin_string(&tag)
        )
        .expect("writing to String cannot fail");
    }
    for (name, trait_ref) in trait_tokens {
        let object = trait_ref
            .as_object()
            .ok_or_else(|| "Dyn trait specialization must be an object".to_owned())?;
        let canonical = serde_json::to_string(&trait_ref)
            .map_err(|error| format!("serialize Dyn trait identity: {error}"))?;
        let trait_name = object
            .get("name")
            .and_then(Value::as_str)
            .ok_or_else(|| "Dyn trait specialization is missing name".to_owned())?;
        let original_arity = object
            .get("args")
            .and_then(Value::as_array)
            .map(Vec::len)
            .unwrap_or_default();
        let associated_arity = trait_slot_definitions(&trait_ref, &declarations)?.len();
        let arity = original_arity + associated_arity;
        let stars = if arity == 0 {
            String::new()
        } else {
            format!("<{}>", vec!["*"; arity].join(", "))
        };
        writeln!(
            out,
            "\npublic val {name}: CottTrait<{}{stars}> = CottTrait.checked({}) {{ value -> value is {}{stars} }}",
            render_qualified(trait_name)?,
            kotlin_string(&canonical),
            render_qualified(trait_name)?
        )
        .expect("writing to String cannot fail");
    }
    for arity in tuple_arities {
        render_tuple_marker(&mut out, arity);
    }
    Ok(finish_source(out))
}

fn collect_markers(
    value: &Value,
    constants: &mut BTreeMap<String, Value>,
    opaques: &mut BTreeSet<String>,
    trait_tokens: &mut BTreeMap<String, Value>,
    tuple_arities: &mut BTreeSet<usize>,
) -> Result<(), String> {
    match value {
        Value::Array(values) => {
            for value in values {
                collect_markers(value, constants, opaques, trait_tokens, tuple_arities)?;
            }
        }
        Value::Object(object) => {
            match object.get("kind").and_then(Value::as_str) {
                Some("const") if object.contains_key("value") && !object.contains_key("name") => {
                    let value = required(object, "value", "generic const argument")?;
                    if value.get("kind").and_then(Value::as_str) != Some("parameter") {
                        constants.insert(const_marker(value)?, value.clone());
                    }
                }
                Some("array" | "buffer") if object.contains_key("length") => {
                    let value = required(object, "length", "fixed container type")?;
                    if value.get("kind").and_then(Value::as_str) != Some("parameter") {
                        constants.insert(const_marker(value)?, value.clone());
                    }
                }
                Some("opaque") => {
                    opaques.insert(required_string(object, "tag", "opaque type")?.to_owned());
                }
                Some("dyn") => {
                    let trait_ref = required(object, "trait", "Dyn type")?;
                    trait_tokens.insert(trait_marker(trait_ref)?, trait_ref.clone());
                }
                Some("tuple") => {
                    tuple_arities.insert(required_array(object, "items", "tuple type")?.len());
                }
                _ => {}
            }
            for value in object.values() {
                collect_markers(value, constants, opaques, trait_tokens, tuple_arities)?;
            }
        }
        _ => {}
    }
    Ok(())
}

fn render_tuple_marker(out: &mut String, arity: usize) {
    if arity == 0 {
        out.push_str("\npublic object CottTuple0 : CottTupleValue {\n    override val cottTupleElements: CottList<kotlin.Any?> = CottList(emptyList())\n    override fun cottRebuild(elements: CottList<kotlin.Any?>): CottTupleValue {\n        if (elements.isNotEmpty()) CottRuntime.violation(\"tuple arity changed during ABI adaptation\", phase = \"validation\", expected = \"0\", actual = elements.size.toString())\n        return this\n    }\n}\n");
        return;
    }
    let parameters = (0..arity)
        .map(|index| format!("out T{index}"))
        .collect::<Vec<_>>()
        .join(", ");
    let fields = (0..arity)
        .map(|index| format!("public val item{index}: T{index}"))
        .collect::<Vec<_>>()
        .join(",\n    ");
    let values = (0..arity)
        .map(|index| format!("item{index}"))
        .collect::<Vec<_>>()
        .join(", ");
    let casts = (0..arity)
        .map(|index| format!("elements[{index}] as T{index}"))
        .collect::<Vec<_>>()
        .join(", ");
    writeln!(
        out,
        "\npublic data class CottTuple{arity}<{parameters}>(\n    {fields},\n) : CottTupleValue {{\n    override val cottTupleElements: CottList<kotlin.Any?> = CottList(listOf({values}))\n    override fun cottRebuild(elements: CottList<kotlin.Any?>): CottTupleValue {{\n        if (elements.size != {arity}) CottRuntime.violation(\"tuple arity changed during ABI adaptation\", phase = \"validation\", expected = \"{arity}\", actual = elements.size.toString())\n        return CottTuple{arity}({casts})\n    }}\n}}"
    )
    .expect("writing to String cannot fail");
}

fn render_types_file(
    config: &KotlinProjectConfig,
    module: &KotlinModule,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
) -> Result<String, String> {
    let mut out = generated_header(&module.name)?;
    for declaration in &module.declarations {
        let object = declaration
            .as_object()
            .ok_or_else(|| format!("declaration in `{}` must be an object", module.name))?;
        let kind = required_string(object, "kind", &module.name)?;
        // Scenarios and requirements have no Kotlin ABI symbol; requirements are report metadata.
        if matches!(
            kind,
            "function" | "impl" | "specialization" | "scenario" | "requirement"
        ) {
            continue;
        }
        render_doc(&mut out, object.get("doc"), 0);
        match kind {
            "external_type" => render_external(&mut out, config, object)?,
            "alias" => render_alias(&mut out, object, declarations)?,
            "newtype" => render_newtype(
                &mut out,
                object,
                declarations,
                &config.kotlin.external_types,
            )?,
            "struct" => render_struct(
                &mut out,
                object,
                declarations,
                &config.kotlin.external_types,
            )?,
            "enum" => render_enum(
                &mut out,
                object,
                declarations,
                &config.kotlin.external_types,
            )?,
            "trait" => render_trait(&mut out, object, declarations)?,
            "rule" => render_rule(&mut out, object, declarations)?,
            "resource" => render_resource(&mut out, object)?,
            "const" => render_const(&mut out, object, declarations)?,
            other => {
                return Err(format!(
                    "unsupported Kotlin type declaration kind `{other}`"
                ));
            }
        }
    }
    render_descriptor_registry(
        &mut out,
        module,
        declarations,
        &config.kotlin.external_types,
    )?;
    Ok(finish_source(out))
}
fn declaration_type_parameter_parts(
    declaration: &Map<String, Value>,
    declaration_site_variance: bool,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
) -> Result<(Vec<String>, Vec<String>), String> {
    let context = EmissionTypeContext::new(declarations);
    let mut parameters = Vec::new();
    let mut where_bounds = Vec::new();
    for generic in required_array(declaration, "generics", "declaration")? {
        let generic = generic
            .as_object()
            .ok_or_else(|| "generic parameter must be an object".to_owned())?;
        let name = escape_identifier(required_string(generic, "name", "generic parameter")?)?;
        match required_string(generic, "kind", "generic parameter")? {
            "type" => {
                let variance = if declaration_site_variance {
                    match required_string(generic, "variance", "generic parameter")? {
                        "invariant" => "",
                        "covariant" => "out ",
                        "contravariant" => "in ",
                        other => {
                            return Err(format!("unsupported generic variance `{other}`"));
                        }
                    }
                } else {
                    ""
                };
                let bounds = required_array(generic, "bounds", &name)?
                    .iter()
                    .map(|bound| render_type_contextual(bound, None, Some(&context)))
                    .collect::<Result<Vec<_>, _>>()?;
                parameters.push(format!(
                    "{variance}{name} : {}",
                    bounds
                        .first()
                        .cloned()
                        .unwrap_or_else(|| "kotlin.Any".to_owned())
                ));
                where_bounds.extend(
                    bounds
                        .into_iter()
                        .skip(1)
                        .map(|bound| format!("{name} : {bound}")),
                );
            }
            "const" => parameters.push(format!("{name} : cott_runtime.CottConst")),
            other => {
                return Err(format!("unsupported generic parameter kind `{other}`"));
            }
        }
    }
    Ok((parameters, where_bounds))
}

fn render_declaration_type_parameters(
    declaration: &Map<String, Value>,
    declaration_site_variance: bool,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
) -> Result<(String, String), String> {
    let (parameters, where_bounds) =
        declaration_type_parameter_parts(declaration, declaration_site_variance, declarations)?;
    Ok((
        if parameters.is_empty() {
            String::new()
        } else {
            format!("<{}>", parameters.join(", "))
        },
        if where_bounds.is_empty() {
            String::new()
        } else {
            format!(" where {}", where_bounds.join(", "))
        },
    ))
}

fn declaration_named_type(declaration: &Map<String, Value>) -> Result<Value, String> {
    let name = required_string(declaration, "name", "declaration")?;
    let args = required_array(declaration, "generics", name)?
        .iter()
        .map(|generic| {
            let generic = generic
                .as_object()
                .ok_or_else(|| format!("generic parameter on `{name}` must be an object"))?;
            let parameter = required_string(generic, "name", name)?;
            match required_string(generic, "kind", name)? {
                "type" => Ok(serde_json::json!({
                    "kind": "type",
                    "type": {"kind": "type_parameter", "name": parameter},
                })),
                "const" => Ok(serde_json::json!({
                    "kind": "const",
                    "value": {
                        "kind": "parameter",
                        "name": parameter,
                        "type": required_string(generic, "type", name)?,
                    },
                })),
                other => Err(format!(
                    "generic parameter on `{name}` has unsupported kind `{other}`"
                )),
            }
        })
        .collect::<Result<Vec<_>, String>>()?;
    Ok(serde_json::json!({"args": args, "kind": "named", "name": name}))
}

fn descriptor_registry_name(module: &str) -> String {
    format!("CottDescriptors_{}", &sha256_hex(module.as_bytes())[..24])
}

fn descriptor_registry_reference(name: &str) -> Result<String, String> {
    let module = module_of(name)
        .ok_or_else(|| format!("canonical type `{name}` has no module qualifier"))?;
    Ok(format!(
        "{}.{}",
        render_qualified(module)?,
        descriptor_registry_name(module)
    ))
}

fn descriptor_function_name(name: &str) -> String {
    format!("type_{}", &sha256_hex(name.as_bytes())[..24])
}

fn descriptor_for_factory_type(
    ty: &Value,
    declaration: &Map<String, Value>,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
    external_types: &BTreeMap<String, String>,
) -> Result<String, String> {
    let mut rendered = descriptor_for(ty, declarations, external_types)?;
    for generic in required_array(declaration, "generics", "descriptor factory")? {
        if generic.get("kind").and_then(Value::as_str) != Some("type") {
            continue;
        }
        let name = generic
            .get("name")
            .and_then(Value::as_str)
            .ok_or_else(|| "descriptor factory type parameter is missing name".to_owned())?;
        let ty = serde_json::json!({"kind": "type_parameter", "name": name});
        let erased = format!(
            "(cott_runtime.CottTypes.ANY as cott_runtime.CottType<{}>)",
            render_type_uncontextual(&ty)?
        );
        rendered = rendered.replace(&erased, &format!("_cott_type_{}", safe_internal_name(name)));
        rendered = rendered.replace(
            &descriptor_type_key(&ty)?,
            &format!("_cott_key_{}", safe_internal_name(name)),
        );
    }
    Ok(rendered)
}

fn descriptor_factory_parameters(declaration: &Map<String, Value>) -> Result<Vec<String>, String> {
    let mut parameters = Vec::new();
    for generic in required_array(declaration, "generics", "descriptor factory")? {
        let generic = generic
            .as_object()
            .ok_or_else(|| "descriptor factory generic must be an object".to_owned())?;
        let name = required_string(generic, "name", "descriptor factory generic")?;
        match required_string(generic, "kind", "descriptor factory generic")? {
            "type" => {
                parameters.push(format!(
                    "_cott_key_{}: kotlin.String",
                    safe_internal_name(name),
                ));
                parameters.push(format!(
                    "_cott_type_{}: cott_runtime.CottType<{}>",
                    safe_internal_name(name),
                    escape_identifier(name)?
                ));
            }
            "const" => parameters.push(format!(
                "_cott_const_{}: {}",
                safe_internal_name(name),
                escape_identifier(name)?
            )),
            other => {
                return Err(format!(
                    "descriptor factory generic `{name}` has unsupported kind `{other}`"
                ));
            }
        }
    }
    Ok(parameters)
}

fn descriptor_factory_key_arguments(
    declaration: &Map<String, Value>,
) -> Result<Vec<String>, String> {
    let mut arguments = Vec::new();
    for generic in required_array(declaration, "generics", "descriptor factory")? {
        let name = generic
            .get("name")
            .and_then(Value::as_str)
            .ok_or_else(|| "descriptor factory generic is missing name".to_owned())?;
        match generic.get("kind").and_then(Value::as_str) {
            Some("type") => arguments.push(format!(
                "_cott_key_{} + \"|\" + _cott_type_{}.displayName",
                safe_internal_name(name),
                safe_internal_name(name),
            )),
            Some("const") => {
                arguments.push(format!(
                    "_cott_const_{}.javaClass.name",
                    safe_internal_name(name)
                ));
                arguments.push(format!("_cott_const_{}.value", safe_internal_name(name)));
            }
            other => {
                return Err(format!(
                    "descriptor factory generic `{name}` has unsupported kind `{other:?}`"
                ));
            }
        }
    }
    Ok(arguments)
}

fn render_nominal_descriptor_body(
    declaration: &Map<String, Value>,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
    external_types: &BTreeMap<String, String>,
) -> Result<String, String> {
    let canonical = required_string(declaration, "name", "nominal descriptor")?;
    let kind = required_string(declaration, "kind", canonical)?;
    let named = declaration_named_type(declaration)?;
    let rendered = render_contextual_type(&named, None, declarations)?;
    let fields = if kind == "newtype" {
        vec![(
            "value".to_owned(),
            required(declaration, "carrier", canonical)?.clone(),
        )]
    } else {
        required_array(declaration, "fields", canonical)?
            .iter()
            .map(|field| {
                Ok((
                    field
                        .get("name")
                        .and_then(Value::as_str)
                        .ok_or_else(|| format!("field on `{canonical}` is missing name"))?
                        .to_owned(),
                    field
                        .get("type")
                        .ok_or_else(|| format!("field on `{canonical}` is missing type"))?
                        .clone(),
                ))
            })
            .collect::<Result<Vec<_>, String>>()?
    };
    let rendered_fields = fields
        .iter()
        .map(|(name, ty)| {
            Ok(format!(
                "cott_runtime.CottNominalField<{rendered}>({}, {}, {{ value -> value.{} }})",
                kotlin_string(name),
                descriptor_for_factory_type(ty, declaration, declarations, external_types)?,
                escape_identifier(name)?,
            ))
        })
        .collect::<Result<Vec<_>, String>>()?;
    let mut rebuild = fields
        .iter()
        .enumerate()
        .map(|(index, (_, ty))| {
            Ok(format!(
                "values[{index}] as {}",
                render_contextual_type(ty, None, declarations)?
            ))
        })
        .collect::<Result<Vec<_>, String>>()?;
    rebuild.extend(
        required_array(declaration, "generics", canonical)?
            .iter()
            .filter(|generic| generic.get("kind").and_then(Value::as_str) == Some("const"))
            .map(|generic| {
                let name = generic
                    .get("name")
                    .and_then(Value::as_str)
                    .ok_or_else(|| format!("const generic on `{canonical}` is missing name"))?;
                Ok(format!("_cott_const_{}", safe_internal_name(name)))
            })
            .collect::<Result<Vec<_>, String>>()?,
    );
    Ok(format!(
        "cott_runtime.CottTypes.nominal(_cottDisplayName, {}::class.java as java.lang.Class<{rendered}>, listOf({}), {{ values -> {}({}) }})",
        render_qualified(canonical)?,
        rendered_fields.join(", "),
        render_qualified(canonical)?,
        rebuild.join(", "),
    ))
}

fn render_enum_descriptor_body(
    declaration: &Map<String, Value>,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
    external_types: &BTreeMap<String, String>,
) -> Result<String, String> {
    let canonical = required_string(declaration, "name", "enum descriptor")?;
    let named = declaration_named_type(declaration)?;
    let rendered_enum = render_contextual_type(&named, None, declarations)?;
    let generic_arguments = generic_names(declaration)?;
    let const_arguments = required_array(declaration, "generics", canonical)?
        .iter()
        .filter(|generic| generic.get("kind").and_then(Value::as_str) == Some("const"))
        .map(|generic| {
            let name = generic
                .get("name")
                .and_then(Value::as_str)
                .ok_or_else(|| format!("const generic on `{canonical}` is missing name"))?;
            Ok(format!("_cott_const_{}", safe_internal_name(name)))
        })
        .collect::<Result<Vec<_>, String>>()?;
    let variants = required_array(declaration, "variants", canonical)?
        .iter()
        .map(|variant| {
            let variant = variant
                .as_object()
                .ok_or_else(|| format!("variant on `{canonical}` must be an object"))?;
            let name = required_string(variant, "name", canonical)?;
            let symbol = required_string(variant, "symbol", canonical)?;
            let fields = required_array(variant, "fields", symbol)?;
            let qualified = format!(
                "{}.{}",
                render_qualified(canonical)?,
                escape_identifier(name)?
            );
            let rendered_variant = if generic_arguments.is_empty() {
                qualified.clone()
            } else {
                format!("{qualified}<{}>", generic_arguments.join(", "))
            };
            let descriptors = fields
                .iter()
                .map(|field| {
                    let field_name = field
                        .get("name")
                        .and_then(Value::as_str)
                        .ok_or_else(|| format!("field on `{symbol}` is missing name"))?;
                    let ty = field
                        .get("type")
                        .ok_or_else(|| format!("field `{field_name}` on `{symbol}` is missing type"))?;
                    Ok(format!(
                        "cott_runtime.CottNominalField<{rendered_variant}>({}, {}, {{ value -> value.{} }})",
                        kotlin_string(field_name),
                        descriptor_for_factory_type(
                            ty,
                            declaration,
                            declarations,
                            external_types,
                        )?,
                        escape_identifier(field_name)?,
                    ))
                })
                .collect::<Result<Vec<_>, String>>()?;
            let mut rebuild = fields
                .iter()
                .enumerate()
                .map(|(index, field)| {
                    let ty = field
                        .get("type")
                        .ok_or_else(|| format!("field on `{symbol}` is missing type"))?;
                    Ok(format!(
                        "values[{index}] as {}",
                        render_contextual_type(ty, None, declarations)?
                    ))
                })
                .collect::<Result<Vec<_>, String>>()?;
            rebuild.extend(const_arguments.iter().cloned());
            let rebuild = if fields.is_empty() && generic_arguments.is_empty() {
                qualified.clone()
            } else if generic_arguments.is_empty() {
                format!("{qualified}({})", rebuild.join(", "))
            } else {
                format!(
                    "{qualified}<{}>({})",
                    generic_arguments.join(", "),
                    rebuild.join(", "),
                )
            };
            Ok(format!(
                "cott_runtime.CottTypes.nominal(_cottDisplayName + {}, {qualified}::class.java as java.lang.Class<{rendered_variant}>, listOf({}), {{ values -> {rebuild} }})",
                kotlin_string(&format!("#{}", local_name(symbol))),
                descriptors.join(", "),
            ))
        })
        .collect::<Result<Vec<_>, String>>()?;
    Ok(format!(
        "(cott_runtime.CottTypes.oneOf(listOf({})) as cott_runtime.CottType<{rendered_enum}>)",
        variants.join(", ")
    ))
}

fn render_descriptor_registry(
    out: &mut String,
    module: &KotlinModule,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
    external_types: &BTreeMap<String, String>,
) -> Result<(), String> {
    let nominal = module
        .declarations
        .iter()
        .filter_map(Value::as_object)
        .filter(|declaration| {
            matches!(
                declaration.get("kind").and_then(Value::as_str),
                Some("newtype" | "struct" | "enum")
            )
        })
        .collect::<Vec<_>>();
    if nominal.is_empty() {
        return Ok(());
    }
    writeln!(
        out,
        "\ninternal object {} {{\n    private val descriptors: kotlin.collections.MutableMap<kotlin.collections.List<kotlin.Any>, cott_runtime.CottType<*>> = java.util.HashMap()",
        descriptor_registry_name(&module.name)
    )
    .expect("writing to String cannot fail");
    for declaration in nominal {
        let canonical = required_string(declaration, "name", &module.name)?;
        let (generics, where_bounds) =
            render_declaration_type_parameters(declaration, false, declarations)?;
        let named = declaration_named_type(declaration)?;
        let rendered = render_contextual_type(&named, None, declarations)?;
        let parameters = descriptor_factory_parameters(declaration)?.join(", ");
        let arguments = descriptor_factory_key_arguments(declaration)?;
        let mut key = vec![kotlin_string(canonical)];
        key.extend(arguments);
        let body = match required_string(declaration, "kind", canonical)? {
            "newtype" | "struct" => {
                render_nominal_descriptor_body(declaration, declarations, external_types)?
            }
            "enum" => render_enum_descriptor_body(declaration, declarations, external_types)?,
            _ => unreachable!(),
        };
        writeln!(
            out,
            "\n    internal fun {generics} {}({parameters}): cott_runtime.CottType<{rendered}>{where_bounds} =\n        kotlin.synchronized(cott_runtime.CottTypes) {{\n            val key: kotlin.collections.List<kotlin.Any> = listOf({})\n            val existing = descriptors[key]\n            if (existing != null) return@synchronized existing as cott_runtime.CottType<{rendered}>\n            val _cottDisplayName: kotlin.String = key.joinToString(separator = \"|\")\n            val deferred: cott_runtime.CottType<{rendered}> = cott_runtime.CottTypes.deferred(_cottDisplayName) {{\n                kotlin.synchronized(cott_runtime.CottTypes) {{\n                    descriptors[key] as? cott_runtime.CottType<{rendered}>\n                        ?: cott_runtime.CottRuntime.violation(\"recursive descriptor was resolved before initialization\", symbol = {}, phase = \"validation\")\n                }}\n            }}\n            descriptors[key] = deferred\n            val resolved: cott_runtime.CottType<{rendered}> = {body}\n            descriptors[key] = resolved\n            resolved\n        }}",
            descriptor_function_name(canonical),
            key.join(", "),
            kotlin_string(canonical),
        )
        .expect("writing to String cannot fail");
    }
    out.push_str("}\n");
    Ok(())
}

fn render_external(
    out: &mut String,
    config: &KotlinProjectConfig,
    declaration: &Map<String, Value>,
) -> Result<(), String> {
    let canonical = required_string(declaration, "name", "external type")?;
    let target = config.kotlin.external_types.get(canonical).ok_or_else(|| {
        format!("external Kotlin type `{canonical}` has no configured projection")
    })?;
    writeln!(
        out,
        "\n{}typealias {} = {}",
        visibility(declaration),
        escape_identifier(local_name(canonical))?,
        render_qualified(target)?
    )
    .expect("writing to String cannot fail");
    Ok(())
}

fn render_alias(
    out: &mut String,
    declaration: &Map<String, Value>,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
) -> Result<(), String> {
    let name = required_string(declaration, "name", "alias")?;
    let (generics, _) = render_declaration_type_parameters(declaration, false, declarations)?;
    let target = render_contextual_type(
        required(declaration, "target", name)?,
        module_of(name),
        declarations,
    )?;
    writeln!(
        out,
        "\n{}typealias {}{generics} = {target}",
        visibility(declaration),
        escape_identifier(local_name(name))?
    )
    .expect("writing to String cannot fail");
    Ok(())
}

fn render_newtype(
    out: &mut String,
    declaration: &Map<String, Value>,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
    external_types: &BTreeMap<String, String>,
) -> Result<(), String> {
    let canonical = required_string(declaration, "name", "newtype")?;
    let name = escape_identifier(local_name(canonical))?;
    let (generics, where_bounds) =
        render_declaration_type_parameters(declaration, true, declarations)?;
    let carrier_value = required(declaration, "carrier", canonical)?;
    let carrier = render_contextual_type(carrier_value, module_of(canonical), declarations)?;
    let witnesses = const_constructor_suffix(declaration)?;
    writeln!(
        out,
        "\n{}data class {name}{generics}(public val value: {carrier}{witnesses}) : cott_runtime.CottFieldValue{where_bounds} {{",
        visibility(declaration)
    )
    .expect("writing to String cannot fail");
    writeln!(
        out,
        "    override val cottTypeIdentity: kotlin.String get() = {}",
        kotlin_string(canonical)
    )
    .expect("writing to String cannot fail");
    out.push_str("    override val cottFieldNames: cott_runtime.CottList<kotlin.String> get() = cott_runtime.CottList(listOf(\"value\"))\n");
    out.push_str("    override fun cottField(name: kotlin.String): kotlin.Any? = when (name) {\n        \"value\" -> value\n        else -> cott_runtime.CottRuntime.violation(\"unknown canonical field\", symbol = cottTypeIdentity, phase = \"field\", actual = name)\n    }\n");
    let descriptor = descriptor_for(carrier_value, declarations, external_types)?;
    writeln!(
        out,
        "    init {{\n        cott_runtime.CottRuntime.abi(value, {descriptor}, cott_runtime.RuntimeValidation.BOUNDARY, \"$.value\")"
    )
    .expect("writing to String cannot fail");
    render_const_witness_validation(out, declaration, 8)?;
    if let Some(refinement) = declaration
        .get("refinement")
        .filter(|value| !value.is_null())
    {
        writeln!(out, "        val _cottResult = value").expect("writing to String cannot fail");
        let mut refinement = refinement.clone();
        rewrite_refinement_receiver(&mut refinement);
        rewrite_const_references(&mut refinement, declaration);
        let condition = render_expression(&refinement)?;
        writeln!(
            out,
            "        cott_runtime.CottRuntime.checkContract({condition}, {}, \"refinement\", clause = \"refinement\", span = {}, expected = \"true\", actual = \"false\")",
            kotlin_string(canonical),
            render_span(refinement.get("span"))?
        )
        .expect("writing to String cannot fail");
    }
    out.push_str("    }\n}\n");
    Ok(())
}

fn rewrite_refinement_receiver(value: &mut Value) {
    match value {
        Value::Object(object) => {
            if object.get("kind").and_then(Value::as_str) == Some("self_ref") {
                object.insert("kind".to_owned(), Value::String("result_ref".to_owned()));
            }
            for child in object.values_mut() {
                rewrite_refinement_receiver(child);
            }
        }
        Value::Array(values) => {
            for child in values {
                rewrite_refinement_receiver(child);
            }
        }
        _ => {}
    }
}

fn render_struct(
    out: &mut String,
    declaration: &Map<String, Value>,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
    external_types: &BTreeMap<String, String>,
) -> Result<(), String> {
    let canonical = required_string(declaration, "name", "struct")?;
    let name = escape_identifier(local_name(canonical))?;
    let (generics, where_bounds) =
        render_declaration_type_parameters(declaration, true, declarations)?;
    let fields = required_array(declaration, "fields", canonical)?;
    let witnesses = const_constructor_lines(declaration)?;
    writeln!(
        out,
        "\n{}{} {name}{generics}(",
        visibility(declaration),
        if fields.is_empty() {
            "class"
        } else {
            "data class"
        },
    )
    .expect("writing to String cannot fail");
    for field in fields {
        let field = field
            .as_object()
            .ok_or_else(|| format!("struct `{canonical}` field must be an object"))?;
        let field_name = required_string(field, "name", canonical)?;
        let ty = required(field, "type", canonical)?;
        let default = field
            .get("default")
            .filter(|value| !value.is_null())
            .map(|value| render_value(value, Some(ty)).map(|value| format!(" = {value}")))
            .transpose()?
            .unwrap_or_default();
        writeln!(
            out,
            "    public val {}: {}{default},",
            escape_identifier(field_name)?,
            render_contextual_type(ty, module_of(canonical), declarations)?
        )
        .expect("writing to String cannot fail");
    }
    for witness in &witnesses {
        writeln!(out, "    {witness},").expect("writing to String cannot fail");
    }
    writeln!(out, ") : cott_runtime.CottFieldValue{where_bounds} {{")
        .expect("writing to String cannot fail");
    writeln!(
        out,
        "    override val cottTypeIdentity: kotlin.String get() = {}",
        kotlin_string(canonical)
    )
    .expect("writing to String cannot fail");
    if fields.is_empty() {
        let arity = generic_names(declaration)?.len();
        let erased = if arity == 0 {
            name.clone()
        } else {
            format!("{name}<{}>", vec!["*"; arity].join(", "))
        };
        writeln!(
            out,
            "    override fun equals(other: kotlin.Any?): kotlin.Boolean = other is {erased} && other.cottTypeIdentity == cottTypeIdentity\n    override fun hashCode(): kotlin.Int = cottTypeIdentity.hashCode()"
        )
        .expect("writing to String cannot fail");
    }
    let field_names = fields
        .iter()
        .filter_map(|field| field.get("name").and_then(Value::as_str))
        .map(kotlin_string)
        .collect::<Vec<_>>();
    writeln!(
        out,
        "    override val cottFieldNames: cott_runtime.CottList<kotlin.String> get() = cott_runtime.CottList(listOf({}))",
        field_names.join(", ")
    )
    .expect("writing to String cannot fail");
    out.push_str("    override fun cottField(name: kotlin.String): kotlin.Any? = when (name) {\n");
    for field in fields {
        let field_name = field
            .get("name")
            .and_then(Value::as_str)
            .expect("validated field");
        writeln!(
            out,
            "        {} -> this.{}",
            kotlin_string(field_name),
            escape_identifier(field_name)?
        )
        .expect("writing to String cannot fail");
    }
    out.push_str("        else -> cott_runtime.CottRuntime.violation(\"unknown canonical field\", symbol = cottTypeIdentity, phase = \"field\", actual = name)\n    }\n    init {\n");
    render_const_witness_validation(out, declaration, 8)?;
    for field in fields {
        let field_name = field
            .get("name")
            .and_then(Value::as_str)
            .expect("validated field");
        let ty = field.get("type").expect("validated field type");
        writeln!(
            out,
            "        cott_runtime.CottRuntime.abi({}, {}, cott_runtime.RuntimeValidation.BOUNDARY, {})",
            escape_identifier(field_name)?,
            descriptor_for(ty, declarations, external_types)?,
            kotlin_string(&format!("$.{field_name}"))
        )
        .expect("writing to String cannot fail");
    }
    render_invariant_calls(out, declaration, canonical, 8)?;
    out.push_str("    }\n}\n");
    Ok(())
}

fn render_enum(
    out: &mut String,
    declaration: &Map<String, Value>,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
    external_types: &BTreeMap<String, String>,
) -> Result<(), String> {
    let canonical = required_string(declaration, "name", "enum")?;
    let name = escape_identifier(local_name(canonical))?;
    let (generics, where_bounds) =
        render_declaration_type_parameters(declaration, true, declarations)?;
    let generic_arguments = generic_names(declaration)?;
    writeln!(
        out,
        "\n{}sealed interface {name}{generics}{where_bounds} {{",
        visibility(declaration)
    )
    .expect("writing to String cannot fail");
    for variant in required_array(declaration, "variants", canonical)? {
        let variant = variant
            .as_object()
            .ok_or_else(|| format!("enum `{canonical}` variant must be an object"))?;
        let variant_name = escape_identifier(required_string(variant, "name", canonical)?)?;
        let variant_symbol = required_string(variant, "symbol", canonical)?;
        let fields = required_array(variant, "fields", variant_symbol)?;
        if fields.is_empty() && generic_arguments.is_empty() {
            writeln!(
                out,
                "    public data object {variant_name} : {name}, cott_runtime.CottVariant {{"
            )
            .expect("writing to String cannot fail");
            render_variant_metadata(out, variant_symbol, fields, 8)?;
            out.push_str("    }\n");
            continue;
        }
        let variant_generics = if generic_arguments.is_empty() {
            String::new()
        } else {
            generics.clone()
        };
        let applied = if generic_arguments.is_empty() {
            name.clone()
        } else {
            format!("{name}<{}>", generic_arguments.join(", "))
        };
        if fields.is_empty() {
            let witnesses = const_constructor_lines(declaration)?;
            if witnesses.is_empty() {
                writeln!(
                    out,
                    "    public class {variant_name}{variant_generics}() : {applied}, cott_runtime.CottVariant{where_bounds} {{"
                )
                .expect("writing to String cannot fail");
            } else {
                writeln!(out, "    public class {variant_name}{variant_generics}(")
                    .expect("writing to String cannot fail");
                for witness in witnesses {
                    writeln!(out, "        {witness},").expect("writing to String cannot fail");
                }
                writeln!(
                    out,
                    "    ) : {applied}, cott_runtime.CottVariant{where_bounds} {{"
                )
                .expect("writing to String cannot fail");
            }
            render_variant_metadata(out, variant_symbol, fields, 8)?;
            let stars = vec!["*"; generic_arguments.len()].join(", ");
            let erased = format!("{variant_name}<{stars}>");
            writeln!(
                out,
                "        override fun equals(other: kotlin.Any?): kotlin.Boolean = other is {erased} && other.cottVariant == cottVariant\n        override fun hashCode(): kotlin.Int = cottVariant.hashCode()"
            )
            .expect("writing to String cannot fail");
            if declaration
                .get("generics")
                .and_then(Value::as_array)
                .is_some_and(|generics| {
                    generics
                        .iter()
                        .any(|generic| generic.get("kind").and_then(Value::as_str) == Some("const"))
                })
            {
                out.push_str("        init {\n");
                render_const_witness_validation(out, declaration, 12)?;
                out.push_str("        }\n");
            }
            out.push_str("    }\n");
            continue;
        }

        writeln!(
            out,
            "    public data class {variant_name}{variant_generics}("
        )
        .expect("writing to String cannot fail");
        for field in fields {
            let field = field
                .as_object()
                .ok_or_else(|| "enum field must be an object".to_owned())?;
            let field_name = required_string(field, "name", variant_symbol)?;
            let ty = required(field, "type", variant_symbol)?;
            let default = field
                .get("default")
                .filter(|value| !value.is_null())
                .map(|value| render_value(value, Some(ty)).map(|value| format!(" = {value}")))
                .transpose()?
                .unwrap_or_default();
            writeln!(
                out,
                "        public val {}: {}{default},",
                escape_identifier(field_name)?,
                render_contextual_type(ty, module_of(canonical), declarations)?
            )
            .expect("writing to String cannot fail");
        }
        for witness in const_constructor_lines(declaration)? {
            writeln!(out, "        {witness},").expect("writing to String cannot fail");
        }
        writeln!(
            out,
            "    ) : {applied}, cott_runtime.CottVariant{where_bounds} {{"
        )
        .expect("writing to String cannot fail");
        render_variant_metadata(out, variant_symbol, fields, 8)?;
        out.push_str("        init {\n");
        render_const_witness_validation(out, declaration, 12)?;
        for field in fields {
            let field = field.as_object().expect("validated enum variant field");
            let field_name = required_string(field, "name", variant_symbol)?;
            writeln!(
                out,
                "            cott_runtime.CottRuntime.abi({}, {}, cott_runtime.RuntimeValidation.BOUNDARY, {})",
                escape_identifier(field_name)?,
                descriptor_for(required(field, "type", variant_symbol)?, declarations, external_types)?,
                kotlin_string(&format!("$.{field_name}")),
            )
            .expect("writing to String cannot fail");
        }
        out.push_str("        }\n    }\n");
    }
    out.push_str("}\n");
    Ok(())
}

fn render_variant_metadata(
    out: &mut String,
    variant_symbol: &str,
    fields: &[Value],
    indent: usize,
) -> Result<(), String> {
    let prefix = " ".repeat(indent);
    writeln!(
        out,
        "{prefix}override val cottVariant: kotlin.String get() = {}",
        kotlin_string(variant_symbol)
    )
    .expect("writing to String cannot fail");
    writeln!(
        out,
        "{prefix}override val cottTypeIdentity: kotlin.String get() = {}",
        kotlin_string(variant_symbol)
    )
    .expect("writing to String cannot fail");
    let field_names = fields
        .iter()
        .filter_map(|field| field.get("name").and_then(Value::as_str))
        .map(kotlin_string)
        .collect::<Vec<_>>();
    writeln!(
        out,
        "{prefix}override val cottFieldNames: cott_runtime.CottList<kotlin.String> get() = cott_runtime.CottList(listOf({}))",
        field_names.join(", ")
    )
    .expect("writing to String cannot fail");
    let values = fields
        .iter()
        .filter_map(|field| field.get("name").and_then(Value::as_str))
        .map(escape_identifier)
        .collect::<Result<Vec<_>, _>>()?;
    writeln!(
        out,
        "{prefix}override val cottPayload: cott_runtime.CottList<kotlin.Any?> get() = cott_runtime.CottList(listOf({}))",
        values.join(", ")
    )
    .expect("writing to String cannot fail");
    out.push_str(&format!(
        "{prefix}override fun cottField(name: kotlin.String): kotlin.Any? = when (name) {{\n"
    ));
    for field in fields {
        let name = field
            .get("name")
            .and_then(Value::as_str)
            .expect("validated enum field");
        writeln!(
            out,
            "{prefix}    {} -> this.{}",
            kotlin_string(name),
            escape_identifier(name)?
        )
        .expect("writing to String cannot fail");
    }
    writeln!(out, "{prefix}    else -> cott_runtime.CottRuntime.violation(\"unknown canonical field\", symbol = cottVariant, phase = \"field\", actual = name)\n{prefix}}}")
        .expect("writing to String cannot fail");
    Ok(())
}

fn render_trait(
    out: &mut String,
    declaration: &Map<String, Value>,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
) -> Result<(), String> {
    let canonical = required_string(declaration, "name", "trait")?;
    let name = escape_identifier(local_name(canonical))?;
    let (mut generic_parts, mut where_parts) =
        declaration_type_parameter_parts(declaration, true, declarations)?;
    let trait_ref = declaration_trait_ref(declaration)?;
    let slots = trait_slot_definitions(&trait_ref, declarations)?;
    let trait_scope = slots
        .iter()
        .map(|slot| {
            (
                (
                    slot.trait_name.clone(),
                    local_name(&slot.slot_name).to_owned(),
                ),
                associated_type_name(&slot.trait_name, &slot.slot_name),
            )
        })
        .collect::<BTreeMap<_, _>>();
    let mut context = EmissionTypeContext::new(declarations);
    context.trait_scope = trait_scope.clone();
    for slot in &slots {
        let parameter = associated_type_name(&slot.trait_name, &slot.slot_name);
        let bounds = slot
            .bounds
            .iter()
            .map(|bound| render_type_contextual(bound, None, Some(&context)))
            .collect::<Result<Vec<_>, _>>()?;
        generic_parts.push(format!(
            "{parameter} : {}",
            bounds
                .first()
                .cloned()
                .unwrap_or_else(|| "kotlin.Any".to_owned())
        ));
        where_parts.extend(
            bounds
                .into_iter()
                .skip(1)
                .map(|bound| format!("{parameter} : {bound}")),
        );
    }
    let generics = if generic_parts.is_empty() {
        String::new()
    } else {
        format!("<{}>", generic_parts.join(", "))
    };
    let where_bounds = if where_parts.is_empty() {
        String::new()
    } else {
        format!(" where {}", where_parts.join(", "))
    };
    let parents = required_array(declaration, "parents", canonical)?
        .iter()
        .map(|parent| {
            render_trait_reference(
                parent
                    .get("trait")
                    .ok_or_else(|| format!("trait `{canonical}` parent is missing trait type"))?,
                None,
                declarations,
                Some(&context),
            )
        })
        .collect::<Result<Vec<_>, _>>()?;
    let extends = if parents.is_empty() {
        String::new()
    } else {
        format!(" : {}", parents.join(", "))
    };
    writeln!(
        out,
        "\n{}interface {name}{generics}{extends}{where_bounds} {{",
        visibility(declaration)
    )
    .expect("writing to String cannot fail");
    for generic in declaration
        .get("generics")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter(|generic| generic.get("kind").and_then(Value::as_str) == Some("const"))
    {
        let generic_name = generic
            .get("name")
            .and_then(Value::as_str)
            .ok_or_else(|| format!("trait `{canonical}` const generic is missing name"))?;
        writeln!(
            out,
            "    public val _cott_const_{}: {}",
            safe_internal_name(generic_name),
            escape_identifier(generic_name)?
        )
        .expect("writing to String cannot fail");
    }
    let inherited_methods = required_array(declaration, "parents", canonical)?
        .iter()
        .filter_map(|parent| parent.pointer("/trait/name").and_then(Value::as_str))
        .filter_map(|parent| declarations.get(parent))
        .flat_map(|(_, parent)| {
            parent
                .get("methods")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
        })
        .filter_map(|method| method.get("name").and_then(Value::as_str))
        .map(local_name)
        .collect::<BTreeSet<_>>();
    for method in required_array(declaration, "methods", canonical)? {
        let method = method
            .as_object()
            .ok_or_else(|| "trait method must be an object".to_owned())?;
        render_doc(out, method.get("doc"), 4);
        let canonical_method = required_string(method, "name", canonical)?;
        let method_name = escape_identifier(local_name(canonical_method))?;
        let rendering = callable_rendering(method, declarations, trait_scope.clone())?;
        let parameters = render_parameters_contextual(method, true, &rendering.context)?.join(", ");
        let return_type = render_type_contextual(
            required(method, "return_type", canonical)?,
            module_of(canonical),
            Some(&rendering.context),
        )?;
        writeln!(
            out,
            "    public {}{}fun {} {method_name}({parameters}): {return_type}{}",
            if inherited_methods.contains(local_name(canonical_method)) {
                "override "
            } else {
                ""
            },
            if method.get("callable_kind").and_then(Value::as_str) == Some("async") {
                "suspend "
            } else {
                ""
            },
            rendering.generics,
            rendering.where_bounds,
        )
        .expect("writing to String cannot fail");
    }
    out.push_str("}\n");
    Ok(())
}

fn render_rule(
    out: &mut String,
    declaration: &Map<String, Value>,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
) -> Result<(), String> {
    let canonical = required_string(declaration, "name", "rule")?;
    let name = escape_identifier(local_name(canonical))?;
    let (generics, where_bounds) =
        render_declaration_type_parameters(declaration, true, declarations)?;
    let base = declaration
        .get("base")
        .and_then(Value::as_str)
        .map(render_qualified)
        .transpose()?
        .map(|base| format!(" : {base}"))
        .unwrap_or_default();
    writeln!(
        out,
        "\n{}interface {name}{generics}{base}{}",
        visibility(declaration),
        where_bounds
    )
    .expect("writing to String cannot fail");
    Ok(())
}

fn render_resource(out: &mut String, declaration: &Map<String, Value>) -> Result<(), String> {
    let canonical = required_string(declaration, "name", "resource")?;
    let name = escape_identifier(local_name(canonical))?;
    writeln!(
        out,
        "\n{}sealed interface {name} : cott_runtime.CottVariant {{",
        visibility(declaration)
    )
    .expect("writing to String cannot fail");
    for state in required_array(declaration, "states", canonical)? {
        let state_name = state
            .get("name")
            .and_then(Value::as_str)
            .ok_or_else(|| format!("resource `{canonical}` state is missing name"))?;
        let local = escape_identifier(local_name(state_name))?;
        writeln!(
            out,
            "    public data object {local} : {name} {{\n        override val cottVariant: kotlin.String get() = {}\n        override val cottTypeIdentity: kotlin.String get() = {}\n        override val cottFieldNames: cott_runtime.CottList<kotlin.String> get() = cott_runtime.CottList(emptyList())\n        override val cottPayload: cott_runtime.CottList<kotlin.Any?> get() = cott_runtime.CottList(emptyList())\n        override fun cottField(name: kotlin.String): kotlin.Any? = cott_runtime.CottRuntime.violation(\"resource state has no fields\", symbol = cottVariant, phase = \"field\", actual = name)\n    }}",
            kotlin_string(state_name),
            kotlin_string(state_name)
        )
        .expect("writing to String cannot fail");
    }
    out.push_str("}\n");
    Ok(())
}

fn render_const(
    out: &mut String,
    declaration: &Map<String, Value>,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
) -> Result<(), String> {
    let canonical = required_string(declaration, "name", "const")?;
    let ty = required(declaration, "type", canonical)?;
    writeln!(
        out,
        "\n{}val {}: {} = {}",
        visibility(declaration),
        escape_identifier(local_name(canonical))?,
        render_contextual_type(ty, module_of(canonical), declarations)?,
        render_value(required(declaration, "value", canonical)?, Some(ty))?
    )
    .expect("writing to String cannot fail");
    Ok(())
}

fn public_target_names(module: &KotlinModule) -> Result<Vec<String>, String> {
    module
        .declarations
        .iter()
        .filter_map(Value::as_object)
        .filter(|declaration| declaration.get("public").and_then(Value::as_bool) == Some(true))
        .filter(|declaration| {
            !matches!(
                declaration.get("kind").and_then(Value::as_str),
                Some("specialization" | "scenario" | "requirement")
            )
        })
        .map(|declaration| {
            required_string(declaration, "name", &module.name)
                .map(|name| local_name(name).to_owned())
        })
        .collect()
}

fn render_parameters(
    declaration: &Map<String, Value>,
    include_defaults: bool,
) -> Result<Vec<String>, String> {
    render_parameters_with_context(declaration, include_defaults, None)
}

fn render_parameters_contextual(
    declaration: &Map<String, Value>,
    include_defaults: bool,
    context: &EmissionTypeContext<'_>,
) -> Result<Vec<String>, String> {
    render_parameters_with_context(declaration, include_defaults, Some(context))
}

fn render_parameters_with_context(
    declaration: &Map<String, Value>,
    include_defaults: bool,
    context: Option<&EmissionTypeContext<'_>>,
) -> Result<Vec<String>, String> {
    let symbol = declaration
        .get("name")
        .and_then(Value::as_str)
        .unwrap_or("callable");
    let mut rendered = required_array(declaration, "parameters", symbol)?
        .iter()
        .map(|parameter| {
            let parameter = parameter
                .as_object()
                .ok_or_else(|| format!("callable `{symbol}` parameter must be an object"))?;
            let name = required_string(parameter, "name", symbol)?;
            let kind = required_string(parameter, "kind", symbol)?;
            let base_type = render_type_contextual(
                required(parameter, "type", symbol)?,
                None,
                context.map(|context| context as &dyn KotlinTypeContext),
            )?;
            let (annotation, modifier, ty) = match kind {
                "positional" => ("", "", base_type),
                "keyword_only" => ("@cott_runtime.CottKeywordOnly ", "", base_type),
                "vararg" => ("", "vararg ", base_type),
                "kwarg" => (
                    "",
                    "",
                    format!("cott_runtime.CottKeywordArguments<{base_type}>"),
                ),
                other => return Err(format!("unsupported canonical parameter kind `{other}`")),
            };
            let default = if include_defaults {
                parameter
                    .get("default")
                    .filter(|value| !value.is_null())
                    .map(|value| {
                        render_value(value, parameter.get("type"))
                            .map(|value| format!(" = {value}"))
                    })
                    .transpose()?
                    .unwrap_or_default()
            } else {
                String::new()
            };
            Ok(format!(
                "{annotation}{modifier}{}: {ty}{default}",
                escape_identifier(name)?
            ))
        })
        .collect::<Result<Vec<_>, String>>()?;
    for generic in declaration
        .get("generics")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter(|generic| generic.get("kind").and_then(Value::as_str) == Some("const"))
    {
        let name = generic
            .get("name")
            .and_then(Value::as_str)
            .ok_or_else(|| format!("callable `{symbol}` const generic is missing name"))?;
        rendered.push(format!(
            "_cott_const_{}: {}",
            safe_internal_name(name),
            escape_identifier(name)?
        ));
    }
    Ok(rendered)
}

fn generic_names(declaration: &Map<String, Value>) -> Result<Vec<String>, String> {
    required_array(declaration, "generics", "declaration")?
        .iter()
        .map(|generic| {
            escape_identifier(
                generic
                    .get("name")
                    .and_then(Value::as_str)
                    .ok_or_else(|| "generic parameter is missing name".to_owned())?,
            )
        })
        .collect()
}

fn const_constructor_lines(declaration: &Map<String, Value>) -> Result<Vec<String>, String> {
    let mut lines = Vec::new();
    lines.extend(
        declaration
            .get("generics")
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
            .filter(|generic| generic.get("kind").and_then(Value::as_str) == Some("const"))
            .map(|generic| {
                let name = generic
                    .get("name")
                    .and_then(Value::as_str)
                    .ok_or_else(|| "const generic is missing name".to_owned())?;
                Ok(format!(
                    "public val _cott_const_{}: {}",
                    safe_internal_name(name),
                    escape_identifier(name)?
                ))
            })
            .collect::<Result<Vec<_>, String>>()?,
    );
    Ok(lines)
}

fn const_constructor_suffix(declaration: &Map<String, Value>) -> Result<String, String> {
    let values = const_constructor_lines(declaration)?;
    Ok(if values.is_empty() {
        String::new()
    } else {
        format!(", {}", values.join(", "))
    })
}

fn render_const_witness_validation(
    out: &mut String,
    declaration: &Map<String, Value>,
    indent: usize,
) -> Result<(), String> {
    let prefix = " ".repeat(indent);
    for generic in declaration
        .get("generics")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter(|generic| generic.get("kind").and_then(Value::as_str) == Some("const"))
    {
        let name = generic
            .get("name")
            .and_then(Value::as_str)
            .ok_or_else(|| "const generic is missing name".to_owned())?;
        writeln!(
            out,
            "{prefix}cott_runtime.CottRuntime.validateConst(_cott_const_{}, {}, {})",
            safe_internal_name(name),
            generic_const_kind(generic)?,
            kotlin_string(&format!("$.const.{name}"))
        )
        .expect("writing to String cannot fail");
    }
    Ok(())
}

fn render_doc(out: &mut String, doc: Option<&Value>, indent: usize) {
    let Some(text) = doc
        .and_then(Value::as_object)
        .and_then(|doc| doc.get("text"))
        .and_then(Value::as_str)
    else {
        return;
    };
    let prefix = " ".repeat(indent);
    writeln!(out, "\n{prefix}/**").expect("writing to String cannot fail");
    for line in text.lines() {
        writeln!(out, "{prefix} * {}", line.replace("*/", "* /"))
            .expect("writing to String cannot fail");
    }
    writeln!(out, "{prefix} */").expect("writing to String cannot fail");
}

fn guarded_check(guard: Option<&Value>, statement: String) -> Result<String, String> {
    let Some(guard) = guard.filter(|value| !value.is_null()) else {
        return Ok(statement);
    };
    expressions::render_guard(
        guard,
        &serde_json::json!({
            "kind": "kotlin_synthetic",
            "code": format!("run {{ {statement}; true }}"),
        }),
        true,
    )
}

fn render_invariant_calls(
    out: &mut String,
    declaration: &Map<String, Value>,
    symbol: &str,
    indent: usize,
) -> Result<(), String> {
    let prefix = " ".repeat(indent);
    for invariant in required_array(declaration, "invariants", symbol)? {
        let mut expression = required_value(invariant, "expression", symbol)?.clone();
        let mut guard = invariant.get("guard").cloned();
        rewrite_const_references(&mut expression, declaration);
        if let Some(guard) = &mut guard {
            rewrite_const_references(guard, declaration);
        }
        let condition = render_condition(&expression, None, true)?;
        let clause = format!(
            "invariant:{}",
            invariant
                .get("clause_id")
                .and_then(Value::as_u64)
                .ok_or_else(|| format!("invariant on `{symbol}` is missing clause_id"))?
        );
        let statement = format!(
            "cott_runtime.CottRuntime.invariant({condition}, {}, clause = {}, span = {}, expected = \"true\", actual = \"false\")",
            kotlin_string(symbol),
            kotlin_string(&clause),
            render_span(invariant.get("span"))?
        );
        writeln!(out, "{prefix}{}", guarded_check(guard.as_ref(), statement)?)
            .expect("writing to String cannot fail");
    }
    Ok(())
}

fn descriptor_for(
    ty: &Value,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
    external_types: &BTreeMap<String, String>,
) -> Result<String, String> {
    let object = ty
        .as_object()
        .ok_or_else(|| "canonical descriptor type must be an object".to_owned())?;
    let kind = object
        .get("kind")
        .and_then(Value::as_str)
        .ok_or_else(|| "canonical descriptor type is missing kind".to_owned())?;
    match kind {
        "primitive" => types::render_primitive_descriptor(ty),
        "type_parameter" => Ok(format!(
            "(cott_runtime.CottTypes.ANY as cott_runtime.CottType<{}>)",
            render_contextual_type(ty, None, declarations)?
        )),
        "associated_projection" => Ok(format!(
            "(cott_runtime.CottTypes.ANY as cott_runtime.CottType<{}>)",
            render_contextual_type(ty, None, declarations)?
        )),
        "list" | "set" | "option" | "iterator" | "async_iterator" => {
            let (method, field) = match kind {
                "list" => ("list", "item"),
                "set" => ("set", "item"),
                "option" => ("option", "item"),
                "iterator" => ("iterator", "item"),
                "async_iterator" => ("asyncIterator", "item"),
                _ => unreachable!(),
            };
            Ok(format!(
                "cott_runtime.CottTypes.{method}({})",
                descriptor_for(
                    required(object, field, "container type")?,
                    declarations,
                    external_types,
                )?
            ))
        }
        "map" | "result" => {
            let (method, left, right) = if kind == "map" {
                ("map", "key", "value")
            } else {
                ("result", "ok", "error")
            };
            Ok(format!(
                "cott_runtime.CottTypes.{method}({}, {})",
                descriptor_for(required(object, left, kind)?, declarations, external_types,)?,
                descriptor_for(required(object, right, kind)?, declarations, external_types,)?
            ))
        }
        "tuple" => {
            let items = required_array(object, "items", "tuple type")?
                .iter()
                .map(|item| descriptor_for(item, declarations, external_types))
                .collect::<Result<Vec<_>, _>>()?;
            Ok(format!(
                "(cott_runtime.CottTypes.tuple(listOf({})) as cott_runtime.CottType<{}>)",
                items.join(", "),
                render_contextual_type(ty, None, declarations)?
            ))
        }
        "array" => {
            let item = required(object, "item", "array type")?;
            let length = required(object, "length", "array type")?;
            let marker = types::render_const_marker(length)?;
            let witness = render_const_witness(length)?;
            if length.get("kind").and_then(Value::as_str) == Some("parameter") {
                Ok(format!(
                    "cott_runtime.CottTypes.arrayParameterized<{}, {}>({}, {}, {})",
                    render_contextual_type(item, None, declarations)?,
                    marker,
                    descriptor_for(item, declarations, external_types)?,
                    witness,
                    render_const_kind(length)?
                ))
            } else {
                Ok(format!(
                    "cott_runtime.CottTypes.array<{}, {}>({}, cott_runtime.CottRuntime.mathInt({}).intValueExact(), {})",
                    render_contextual_type(item, None, declarations)?,
                    marker,
                    descriptor_for(item, declarations, external_types)?,
                    render_const_value(length)?,
                    witness
                ))
            }
        }
        "buffer" => {
            let length = required(object, "length", "buffer type")?;
            let marker = types::render_const_marker(length)?;
            let witness = render_const_witness(length)?;
            if length.get("kind").and_then(Value::as_str) == Some("parameter") {
                Ok(format!(
                    "cott_runtime.CottTypes.bufferParameterized<{marker}>({witness}, {})",
                    render_const_kind(length)?
                ))
            } else {
                Ok(format!(
                    "cott_runtime.CottTypes.buffer<{marker}>(cott_runtime.CottRuntime.mathInt({}).intValueExact(), {witness})",
                    render_const_value(length)?
                ))
            }
        }
        "generator" => Ok(format!(
            "cott_runtime.CottTypes.generator({}, {}, {})",
            descriptor_for(
                required(object, "yield", "generator type")?,
                declarations,
                external_types,
            )?,
            descriptor_for(
                required(object, "send", "generator type")?,
                declarations,
                external_types,
            )?,
            descriptor_for(
                required(object, "return", "generator type")?,
                declarations,
                external_types,
            )?
        )),
        "async_generator" => Ok(format!(
            "cott_runtime.CottTypes.asyncGenerator({}, {}, cott_runtime.CottTypes.UNIT)",
            descriptor_for(
                required(object, "yield", "async generator type")?,
                declarations,
                external_types,
            )?,
            descriptor_for(
                required(object, "send", "async generator type")?,
                declarations,
                external_types,
            )?
        )),
        "opaque" => Ok(format!(
            "cott_runtime.CottTypes.opaque(cott_runtime.{})",
            opaque_marker(required_string(object, "tag", "opaque type")?)
        )),
        "dyn" => Ok(format!(
            "(cott_runtime.CottTypes.dyn(cott_runtime.{}) as cott_runtime.CottType<{}>)",
            trait_marker(required(object, "trait", "Dyn type")?)?,
            render_contextual_type(ty, None, declarations)?
        )),
        "factory" => Ok(format!(
            "cott_runtime.CottTypes.factory({}::class.java)",
            types::erased_class_name(required(object, "instance", "Factory type")?)?
        )),
        "named" => descriptor_for_named(ty, object, declarations, external_types),
        other => Err(format!("unsupported Kotlin descriptor type kind `{other}`")),
    }
}

fn descriptor_type_key(ty: &Value) -> Result<String, String> {
    let identity = serde_json::to_string(ty)
        .map_err(|error| format!("serialize descriptor type identity: {error}"))?;
    Ok(kotlin_string(&identity))
}

fn descriptor_for_named(
    ty: &Value,
    object: &Map<String, Value>,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
    external_types: &BTreeMap<String, String>,
) -> Result<String, String> {
    let name = required_string(object, "name", "named type")?;
    let Some((declaration_kind, declaration)) = declarations.get(name).copied() else {
        return Err(format!("named type `{name}` has no canonical declaration"));
    };
    match declaration_kind {
        "alias" => {
            let target =
                instantiate_type(required(declaration, "target", name)?, declaration, object);
            descriptor_for(&target, declarations, external_types)
        }
        "external_type" => {
            let target = external_types.get(name).ok_or_else(|| {
                format!("external Kotlin type `{name}` has no configured projection")
            })?;
            let target_type = render_qualified(target)?;
            Ok(format!(
                "cott_runtime.CottTypes.external<{target_type}>({}, {{ value -> value != null && {target_type}::class.java.isInstance(value) }})",
                kotlin_string(target)
            ))
        }
        "newtype" | "struct" | "enum" => {
            let parameters = required_array(declaration, "generics", name)?;
            let arguments = required_array(object, "args", name)?;
            if parameters.len() != arguments.len() {
                return Err(format!(
                    "named type `{name}` has {} arguments but declares {} parameters",
                    arguments.len(),
                    parameters.len()
                ));
            }
            let mut rendered = Vec::new();
            for (parameter, argument) in parameters.iter().zip(arguments) {
                let parameter_kind = parameter
                    .get("kind")
                    .and_then(Value::as_str)
                    .ok_or_else(|| format!("generic parameter on `{name}` is missing kind"))?;
                let argument_kind = argument
                    .get("kind")
                    .and_then(Value::as_str)
                    .ok_or_else(|| format!("generic argument on `{name}` is missing kind"))?;
                match (parameter_kind, argument_kind) {
                    ("type", "type") => {
                        let ty = argument
                            .get("type")
                            .ok_or_else(|| format!("type argument on `{name}` is missing type"))?;
                        rendered.push(descriptor_type_key(ty)?);
                        rendered.push(descriptor_for(ty, declarations, external_types)?);
                    }
                    ("const", "const") => {
                        rendered.push(render_const_witness(argument.get("value").ok_or_else(
                            || format!("const argument on `{name}` is missing value"),
                        )?)?)
                    }
                    _ => {
                        return Err(format!(
                            "generic argument kind `{argument_kind}` does not match `{parameter_kind}` on `{name}`"
                        ));
                    }
                }
            }
            Ok(format!(
                "{}.{}({})",
                descriptor_registry_reference(name)?,
                descriptor_function_name(name),
                rendered.join(", ")
            ))
        }
        "resource" | "trait" | "impl" => {
            let rendered = render_contextual_type(ty, None, declarations)?;
            let erased = erased_kotlin_type(name, declaration, declarations)?;
            Ok(format!(
                "cott_runtime.CottTypes.external<{rendered}>({}, {{ value -> value is {erased} }})",
                kotlin_string(name)
            ))
        }
        other => Err(format!(
            "declaration `{name}` of kind `{other}` is not a Kotlin ABI type"
        )),
    }
}
fn descriptor_for_contextual(
    ty: &Value,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
    external_types: &BTreeMap<String, String>,
    context: &EmissionTypeContext<'_>,
) -> Result<String, String> {
    let mut rendered = descriptor_for(ty, declarations, external_types)?;
    let mut projections = Vec::new();
    collect_associated_projections(ty, &mut projections)?;
    for (base, trait_name, slot_name) in projections {
        rendered = rendered.replace(
            &associated_projection_name(&base, &trait_name, &slot_name)?,
            &context.associated_projection(&base, &trait_name, &slot_name)?,
        );
    }
    Ok(rendered)
}

fn instantiate_type(
    value: &Value,
    declaration: &Map<String, Value>,
    named: &Map<String, Value>,
) -> Value {
    let mut types = BTreeMap::<String, Value>::new();
    let mut constants = BTreeMap::<String, Value>::new();
    for (parameter, argument) in declaration
        .get("generics")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter_map(Value::as_object)
        .zip(
            named
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
                if let Some(value) = argument.get("type") {
                    types.insert(name.to_owned(), value.clone());
                }
            }
            Some("const") => {
                if let Some(value) = argument.get("value") {
                    constants.insert(name.to_owned(), value.clone());
                }
            }
            _ => {}
        }
    }
    let mut value = value.clone();
    substitute_arguments(&mut value, &types, &constants);
    value
}

fn render_trait_reference(
    trait_ref: &Value,
    implementation: Option<&Map<String, Value>>,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
    context: Option<&EmissionTypeContext<'_>>,
) -> Result<String, String> {
    let object = trait_ref
        .as_object()
        .ok_or_else(|| "trait reference must be an object".to_owned())?;
    let name = required_string(object, "name", "trait reference")?;
    let (kind, _) = declarations
        .get(name)
        .copied()
        .ok_or_else(|| format!("unknown trait reference `{name}`"))?;
    if kind != "trait" {
        return Err(format!("trait reference `{name}` resolves to `{kind}`"));
    }
    let mut arguments = object
        .get("args")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .map(
            |argument| match argument.get("kind").and_then(Value::as_str) {
                Some("type") => match context {
                    Some(context) => render_type_contextual(
                        argument
                            .get("type")
                            .ok_or_else(|| "trait type argument is missing type".to_owned())?,
                        None,
                        Some(context),
                    ),
                    None => render_contextual_type(
                        argument
                            .get("type")
                            .ok_or_else(|| "trait type argument is missing type".to_owned())?,
                        None,
                        declarations,
                    ),
                },
                Some("const") => types::render_const_marker(
                    argument
                        .get("value")
                        .ok_or_else(|| "trait const argument is missing value".to_owned())?,
                ),
                other => Err(format!("unsupported trait argument kind `{other:?}`")),
            },
        )
        .collect::<Result<Vec<_>, _>>()?;
    for slot in trait_slot_definitions(trait_ref, declarations)? {
        if let Some(implementation) = implementation {
            let assignment =
                associated_assignment_type(implementation, &slot.trait_name, &slot.slot_name)
                    .ok_or_else(|| {
                        format!(
                            "implementation `{}` is missing associated assignment `{}.{}`",
                            implementation
                                .get("name")
                                .and_then(Value::as_str)
                                .unwrap_or("<implementation>"),
                            slot.trait_name,
                            local_name(&slot.slot_name),
                        )
                    })?;
            arguments.push(render_contextual_type(assignment, None, declarations)?);
        } else {
            arguments.push(associated_type_name(&slot.trait_name, &slot.slot_name));
        }
    }
    let name = render_qualified(name)?;
    Ok(if arguments.is_empty() {
        name
    } else {
        format!("{name}<{}>", arguments.join(", "))
    })
}

fn substitute_associated_types(value: &mut Value, implementation: &Map<String, Value>) {
    let replacement = value.as_object().and_then(|object| {
        if object.get("kind").and_then(Value::as_str) != Some("associated_projection") {
            return None;
        }
        if object
            .get("base")
            .and_then(Value::as_object)
            .and_then(|base| base.get("kind"))
            .and_then(Value::as_str)
            == Some("type_parameter")
        {
            return None;
        }
        let trait_name = object.get("trait").and_then(Value::as_str)?;
        let slot_name = object.get("name").and_then(Value::as_str)?;
        associated_assignment_type(implementation, trait_name, slot_name).cloned()
    });
    if let Some(replacement) = replacement {
        *value = replacement;
        return;
    }
    match value {
        Value::Array(values) => {
            for value in values {
                substitute_associated_types(value, implementation);
            }
        }
        Value::Object(object) => {
            for value in object.values_mut() {
                substitute_associated_types(value, implementation);
            }
        }
        _ => {}
    }
}

fn substitute_arguments(
    value: &mut Value,
    types: &BTreeMap<String, Value>,
    constants: &BTreeMap<String, Value>,
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
                substitute_arguments(value, types, constants);
            }
        }
        Value::Object(object) => {
            for value in object.values_mut() {
                substitute_arguments(value, types, constants);
            }
        }
        _ => {}
    }
}

fn trait_specializations(
    implementation: &Map<String, Value>,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
) -> Result<Vec<Value>, String> {
    let mut pending = required_array(implementation, "traits", "implementation")?.clone();
    let mut resolved = BTreeMap::<String, Value>::new();
    while let Some(trait_ref) = pending.pop() {
        let identity = serde_json::to_string(&trait_ref)
            .map_err(|error| format!("serialize trait specialization: {error}"))?;
        if resolved.contains_key(&identity) {
            continue;
        }
        let object = trait_ref
            .as_object()
            .ok_or_else(|| "implementation trait specialization must be an object".to_owned())?;
        let name = required_string(object, "name", "implementation trait")?;
        let (kind, declaration) = declarations
            .get(name)
            .copied()
            .ok_or_else(|| format!("implementation references unknown trait `{name}`"))?;
        if kind != "trait" {
            return Err(format!(
                "implementation trait `{name}` is a `{kind}` declaration"
            ));
        }
        for closure in required_array(declaration, "closure", name)? {
            pending.push(instantiate_type(closure, declaration, object));
        }
        resolved.insert(identity, trait_ref);
    }
    Ok(resolved.into_values().collect())
}

fn erased_kotlin_type(
    name: &str,
    declaration: &Map<String, Value>,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
) -> Result<String, String> {
    let mut arity = declaration
        .get("generics")
        .and_then(Value::as_array)
        .map(Vec::len)
        .unwrap_or_default();
    if declaration.get("kind").and_then(Value::as_str) == Some("trait") {
        arity += trait_slot_definitions(&declaration_trait_ref(declaration)?, declarations)?.len();
    }
    Ok(if arity == 0 {
        render_qualified(name)?
    } else {
        format!(
            "{}<{}>",
            render_qualified(name)?,
            vec!["*"; arity].join(", ")
        )
    })
}

fn visibility(declaration: &Map<String, Value>) -> &'static str {
    if declaration.get("public").and_then(Value::as_bool) == Some(true) {
        "public "
    } else {
        "internal "
    }
}

fn generated_header(module: &str) -> Result<String, String> {
    Ok(format!(
        "// Generated by Cott. Do not edit.\n@file:Suppress(\"UNCHECKED_CAST\", \"RedundantVisibilityModifier\")\n\npackage {}\n",
        render_qualified(module)?
    ))
}

fn finish_source(mut source: String) -> String {
    while source.ends_with("\n\n") {
        source.pop();
    }
    if !source.ends_with('\n') {
        source.push('\n');
    }
    source
}

fn types_path(module: &str) -> Result<PathBuf, String> {
    kotlin_module_path(module, "Types.kt")
}

fn facade_path(module: &str) -> Result<PathBuf, String> {
    kotlin_module_path(module, "Facade.kt")
}

fn kotlin_module_path(module: &str, file: &str) -> Result<PathBuf, String> {
    let mut path = PathBuf::from("kotlin");
    for segment in module.split('.') {
        escape_identifier(segment)?;
        path.push(segment);
    }
    path.push(file);
    Ok(path)
}

fn ir_path(module: &str) -> Result<PathBuf, String> {
    let mut path = PathBuf::from("ir");
    let mut segments = module.split('.').peekable();
    while let Some(segment) = segments.next() {
        escape_identifier(segment)?;
        if segments.peek().is_some() {
            path.push(segment);
        } else {
            path.push(format!("{segment}.json"));
        }
    }
    Ok(path)
}

fn safe_artifact_path(path: &Path) -> bool {
    !path.as_os_str().is_empty()
        && !path.is_absolute()
        && path
            .components()
            .all(|component| matches!(component, Component::Normal(_)))
}

fn insert_file(
    files: &mut BTreeMap<PathBuf, Vec<u8>>,
    path: PathBuf,
    bytes: Vec<u8>,
) -> Result<(), String> {
    if !safe_artifact_path(&path) {
        return Err(format!("unsafe Kotlin artifact path `{}`", path.display()));
    }
    if files.insert(path.clone(), bytes).is_some() {
        return Err(format!(
            "colliding Kotlin artifact path `{}`",
            path.display()
        ));
    }
    Ok(())
}

fn module_of(name: &str) -> Option<&str> {
    name.rsplit_once('.').map(|(module, _)| module)
}

fn required<'a>(
    object: &'a Map<String, Value>,
    field: &str,
    context: &str,
) -> Result<&'a Value, String> {
    object
        .get(field)
        .ok_or_else(|| format!("canonical `{context}` is missing `{field}`"))
}

fn required_value<'a>(value: &'a Value, field: &str, context: &str) -> Result<&'a Value, String> {
    value
        .get(field)
        .ok_or_else(|| format!("canonical `{context}` is missing `{field}`"))
}

fn required_string<'a>(
    object: &'a Map<String, Value>,
    field: &str,
    context: &str,
) -> Result<&'a str, String> {
    required(object, field, context)?
        .as_str()
        .ok_or_else(|| format!("canonical `{context}.{field}` must be a string"))
}

fn required_array<'a>(
    object: &'a Map<String, Value>,
    field: &str,
    context: &str,
) -> Result<&'a Vec<Value>, String> {
    required(object, field, context)?
        .as_array()
        .ok_or_else(|| format!("canonical `{context}.{field}` must be an array"))
}

// Facade rendering is kept below the declaration renderer so its public surface
// can only be created after every canonical type declaration has been accepted.
fn render_facade_file(
    config: &KotlinProjectConfig,
    module: &KotlinModule,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
    callables: &BTreeMap<String, KotlinCallable>,
    bindings: &BTreeMap<&str, &KotlinBinding>,
) -> Result<String, String> {
    let mut out = generated_header(&module.name)?;
    for callable in callables
        .values()
        .filter(|callable| callable.module == module.name && callable.owner.is_none())
    {
        let Some(binding) = bindings.get(callable.symbol.as_str()).copied() else {
            continue;
        };
        let declaration = callable
            .declaration
            .as_object()
            .ok_or_else(|| format!("callable `{}` must be an object", callable.symbol))?;
        render_function_facade(
            &mut out,
            config,
            callable,
            declaration,
            binding,
            declarations,
        )?;
    }
    for declaration in &module.declarations {
        let Some(implementation) = declaration
            .as_object()
            .filter(|value| value.get("kind").and_then(Value::as_str) == Some("impl"))
        else {
            continue;
        };
        if implementation.get("public").and_then(Value::as_bool) != Some(true) {
            continue;
        }
        let concrete = required_string(implementation, "name", &module.name)?;
        if !implementation_resolved(concrete, implementation, callables, bindings) {
            continue;
        }
        render_implementation_class(
            &mut out,
            config,
            implementation,
            declarations,
            callables,
            bindings,
        )?;
    }
    Ok(finish_source(out))
}

fn render_function_facade(
    out: &mut String,
    config: &KotlinProjectConfig,
    callable: &KotlinCallable,
    declaration: &Map<String, Value>,
    binding: &KotlinBinding,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
) -> Result<(), String> {
    let public = declaration.get("public").and_then(Value::as_bool) == Some(true);
    render_doc(out, declaration.get("doc"), 0);
    let rendering = callable_rendering(declaration, declarations, BTreeMap::new())?;
    let parameters =
        render_parameters_contextual(declaration, true, &rendering.context)?.join(", ");
    let return_value = required(declaration, "return_type", &callable.symbol)?;
    let return_type = render_type_contextual(return_value, None, Some(&rendering.context))?;
    let asynchronous = declaration.get("callable_kind").and_then(Value::as_str) == Some("async");
    writeln!(
        out,
        "\n{}{}fun {} {}({parameters}): {return_type}{} {{",
        if public { "public " } else { "internal " },
        if asynchronous { "suspend " } else { "" },
        rendering.generics,
        escape_identifier(&callable.name)?,
        rendering.where_bounds,
    )
    .expect("writing to String cannot fail");
    render_identity_preflight(out, config, 4);
    let parameter_locals = render_parameter_validation(
        out,
        config,
        declaration,
        declarations,
        4,
        asynchronous,
        true,
        Some(&rendering.context),
    )?;
    render_contract_clauses(
        out,
        config,
        declaration,
        &callable.symbol,
        true,
        4,
        asynchronous,
        &parameter_locals,
    )?;
    render_expected_errors(
        out,
        config,
        declaration,
        &callable.symbol,
        4,
        asynchronous,
        &parameter_locals,
        true,
    )?;
    let call = render_call_arguments(declaration, &parameter_locals)?;
    let target = render_qualified(&binding.target_symbol)?;
    writeln!(out, "    val _cottRawResult = try {{").expect("writing to String cannot fail");
    writeln!(out, "        {target}({call})").expect("writing to String cannot fail");
    out.push_str("    } catch (error: cott_runtime.CottContractViolation) {\n        if (error.symbol == null) error.symbol = ");
    out.push_str(&kotlin_string(&callable.symbol));
    out.push_str("\n        throw error\n    } catch (error: java.util.concurrent.CancellationException) {\n");
    if asynchronous {
        out.push_str("        throw error\n");
    } else {
        writeln!(out, "        cott_runtime.CottRuntime.violation(\"synchronous implementation threw cancellation\", symbol = {}, phase = \"implementation-call\", cause = error)", kotlin_string(&callable.symbol)).expect("writing to String cannot fail");
    }
    writeln!(out, "    }} catch (error: kotlin.Throwable) {{\n        cott_runtime.CottRuntime.violation(\"implementation raised an undeclared exception\", symbol = {}, phase = \"implementation-call\", expected = \"declared Result error or ordinary return\", actual = error::class.java.name, cause = error)\n    }}", kotlin_string(&callable.symbol)).expect("writing to String cannot fail");
    if is_never(return_value) {
        writeln!(out, "    cott_runtime.CottRuntime.violation(\"Never function returned\", symbol = {}, phase = \"return\", expected = \"Never\", actual = _cottRawResult.toString())", kotlin_string(&callable.symbol)).expect("writing to String cannot fail");
    } else {
        let descriptor = descriptor_for_contextual(
            return_value,
            declarations,
            &config.kotlin.external_types,
            &rendering.context,
        )?;
        writeln!(
            out,
            "    val _cottResult = cott_runtime.CottRuntime.{}(_cottRawResult, {descriptor}, {}, \"$.return\")",
            if asynchronous { "returnValueSuspend" } else { "returnValue" },
            runtime_mode(config)
        )
        .expect("writing to String cannot fail");
        render_contract_clauses(
            out,
            config,
            declaration,
            &callable.symbol,
            false,
            4,
            asynchronous,
            &parameter_locals,
        )?;
        out.push_str("    return _cottResult\n");
    }
    out.push_str("}\n");
    Ok(())
}

fn render_parameter_validation(
    out: &mut String,
    config: &KotlinProjectConfig,
    declaration: &Map<String, Value>,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
    indent: usize,
    asynchronous: bool,
    declare: bool,
    context: Option<&EmissionTypeContext<'_>>,
) -> Result<BTreeMap<String, String>, String> {
    let prefix = " ".repeat(indent);
    let mut locals = BTreeMap::new();
    for parameter in required_array(declaration, "parameters", "callable")? {
        let parameter = parameter
            .as_object()
            .ok_or_else(|| "callable parameter must be an object".to_owned())?;
        let name = required_string(parameter, "name", "callable parameter")?;
        let escaped = escape_identifier(name)?;
        let local = format!("_cottArg_{}", safe_internal_name(name));
        let kind = required_string(parameter, "kind", name)?;
        let item_descriptor = match context {
            Some(context) => descriptor_for_contextual(
                required(parameter, "type", name)?,
                declarations,
                &config.kotlin.external_types,
                context,
            )?,
            None => descriptor_for(
                required(parameter, "type", name)?,
                declarations,
                &config.kotlin.external_types,
            )?,
        };
        if kind == "vararg" {
            writeln!(out, "{prefix}for (_cottIndex in {escaped}.indices) {{")
                .expect("writing to String cannot fail");
            writeln!(
                out,
                "{prefix}    cott_runtime.CottRuntime.{}({escaped}[_cottIndex], {item_descriptor}, {}, \"$.{name}[${{_cottIndex}}]\")",
                if asynchronous { "abiSuspend" } else { "abi" },
                runtime_mode(config),
            )
            .expect("writing to String cannot fail");
            writeln!(
                out,
                "{prefix}}}\n{prefix}{}{local} = {escaped}",
                if declare { "val " } else { "" }
            )
            .expect("writing to String cannot fail");
        } else {
            let descriptor = if kind == "kwarg" {
                format!("cott_runtime.CottTypes.keywordArguments({item_descriptor})")
            } else {
                item_descriptor
            };
            writeln!(
                out,
                "{prefix}{}{local} = cott_runtime.CottRuntime.{}({escaped}, {descriptor}, {}, {})",
                if declare { "val " } else { "" },
                if asynchronous { "abiSuspend" } else { "abi" },
                runtime_mode(config),
                kotlin_string(&format!("$.{name}"))
            )
            .expect("writing to String cannot fail");
        }
        locals.insert(name.to_owned(), local);
    }
    for generic in declaration
        .get("generics")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter(|generic| generic.get("kind").and_then(Value::as_str) == Some("const"))
    {
        let name = generic
            .get("name")
            .and_then(Value::as_str)
            .ok_or_else(|| "const generic is missing name".to_owned())?;
        writeln!(
            out,
            "{prefix}cott_runtime.CottRuntime.validateConst(_cott_const_{}, {}, {})",
            safe_internal_name(name),
            generic_const_kind(generic)?,
            kotlin_string(&format!("$.const.{name}"))
        )
        .expect("writing to String cannot fail");
    }
    Ok(locals)
}

fn parameter_local_names(
    declaration: &Map<String, Value>,
) -> Result<BTreeMap<String, String>, String> {
    required_array(declaration, "parameters", "callable")?
        .iter()
        .map(|parameter| {
            let name = parameter
                .get("name")
                .and_then(Value::as_str)
                .ok_or_else(|| "callable parameter is missing name".to_owned())?;
            Ok((
                name.to_owned(),
                format!("_cottArg_{}", safe_internal_name(name)),
            ))
        })
        .collect()
}
fn render_parameter_placeholders(
    out: &mut String,
    declaration: &Map<String, Value>,
    locals: &BTreeMap<String, String>,
    indent: usize,
) -> Result<(), String> {
    let prefix = " ".repeat(indent);
    for parameter in required_array(declaration, "parameters", "callable")? {
        let name = parameter
            .get("name")
            .and_then(Value::as_str)
            .ok_or_else(|| "callable parameter is missing name".to_owned())?;
        writeln!(
            out,
            "{prefix}var {} = {}",
            locals
                .get(name)
                .ok_or_else(|| format!("missing parameter local `{name}`"))?,
            escape_identifier(name)?
        )
        .expect("writing to String cannot fail");
    }
    Ok(())
}

fn render_call_arguments(
    declaration: &Map<String, Value>,
    locals: &BTreeMap<String, String>,
) -> Result<String, String> {
    let mut values = required_array(declaration, "parameters", "callable")?
        .iter()
        .map(|parameter| {
            let name = parameter
                .get("name")
                .and_then(Value::as_str)
                .ok_or_else(|| "callable parameter is missing name".to_owned())?;
            let local = locals
                .get(name)
                .ok_or_else(|| format!("missing validated parameter `{name}`"))?;
            Ok(
                if parameter.get("kind").and_then(Value::as_str) == Some("vararg") {
                    format!("*{local}")
                } else {
                    local.clone()
                },
            )
        })
        .collect::<Result<Vec<_>, String>>()?;
    values.extend(
        declaration
            .get("generics")
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
            .filter(|generic| generic.get("kind").and_then(Value::as_str) == Some("const"))
            .filter_map(|generic| generic.get("name").and_then(Value::as_str))
            .map(|name| format!("_cott_const_{}", safe_internal_name(name))),
    );
    Ok(values.join(", "))
}

fn render_contract_clauses(
    out: &mut String,
    config: &KotlinProjectConfig,
    declaration: &Map<String, Value>,
    symbol: &str,
    pre: bool,
    indent: usize,
    asynchronous: bool,
    locals: &BTreeMap<String, String>,
) -> Result<(), String> {
    let clauses = declaration
        .get("contract")
        .and_then(Value::as_object)
        .and_then(|contract| contract.get("clauses"))
        .and_then(Value::as_array)
        .map(Vec::as_slice)
        .or_else(|| {
            declaration
                .get("contracts")
                .and_then(Value::as_object)
                .map(|contracts| {
                    let key = if pre { "requires" } else { "ensures" };
                    contracts
                        .get(key)
                        .and_then(Value::as_array)
                        .map(Vec::as_slice)
                        .unwrap_or_default()
                })
        })
        .unwrap_or_default();
    let has_checks = clauses.iter().any(|clause| {
        let kind = clause.get("kind").and_then(Value::as_str);
        (pre && kind == Some("requires"))
            || (!pre && matches!(kind, Some("ensures" | "error")))
            || (kind.is_none() && !clauses.is_empty())
    }) || (!pre && crate::ir::complete_errors(declaration) == Ok(true));
    if !has_checks {
        return Ok(());
    }
    let prefix = " ".repeat(indent);
    let nested = " ".repeat(indent + 4);
    writeln!(
        out,
        "{prefix}if (cott_runtime.CottRuntime.{}({})) {{",
        if asynchronous {
            "contractsEnabledSuspend"
        } else {
            "contractsEnabled"
        },
        runtime_mode(config)
    )
    .expect("writing to String cannot fail");
    for clause in clauses {
        let kind = clause
            .get("kind")
            .and_then(Value::as_str)
            .unwrap_or(if pre { "requires" } else { "ensures" });
        if (pre && kind != "requires") || (!pre && kind != "ensures") {
            continue;
        }
        let mut expression = clause
            .get("expression")
            .cloned()
            .ok_or_else(|| format!("contract clause on `{symbol}` is missing expression"))?;
        let mut guard = clause.get("guard").cloned();
        rewrite_parameter_references(&mut expression, locals);
        if let Some(guard) = &mut guard {
            rewrite_parameter_references(guard, locals);
        }
        rewrite_const_references(&mut expression, declaration);
        if let Some(guard) = &mut guard {
            rewrite_const_references(guard, declaration);
        }
        let condition =
            callable_expression(render_condition(&expression, None, true)?, asynchronous);
        let label = clause_label(clause)?;
        let statement = format!(
            "cott_runtime.CottRuntime.{}({condition}, {}, \"{}\", clause = {}, span = {}, expected = \"true\", actual = \"false\")",
            if asynchronous {
                "checkContractSuspend"
            } else {
                "checkContract"
            },
            kotlin_string(symbol),
            kind,
            kotlin_string(&label),
            render_span(clause.get("span"))?
        );
        writeln!(
            out,
            "{nested}{}",
            callable_expression(guarded_check(guard.as_ref(), statement)?, asynchronous)
        )
        .expect("writing to String cannot fail");
    }
    if !pre {
        render_error_contracts(out, declaration, symbol, indent + 4, asynchronous)?;
    }
    writeln!(out, "{prefix}}}").expect("writing to String cannot fail");
    Ok(())
}

fn render_expected_errors(
    out: &mut String,
    config: &KotlinProjectConfig,
    declaration: &Map<String, Value>,
    symbol: &str,
    indent: usize,
    asynchronous: bool,
    locals: &BTreeMap<String, String>,
    declare: bool,
) -> Result<(), String> {
    let clauses = declaration
        .get("contract")
        .and_then(Value::as_object)
        .and_then(|contract| contract.get("clauses"))
        .and_then(Value::as_array)
        .map(Vec::as_slice)
        .or_else(|| {
            declaration
                .get("contracts")
                .and_then(Value::as_object)
                .and_then(|contracts| contracts.get("errors"))
                .and_then(Value::as_array)
                .map(Vec::as_slice)
        })
        .unwrap_or_default();
    let errors = clauses
        .iter()
        .filter(|clause| clause.get("kind").and_then(Value::as_str) == Some("error"))
        .collect::<Vec<_>>();
    // Complete errors keep the check with zero conditional clauses: then no
    // requires-valid input may return `Err`.
    if errors.is_empty() && crate::ir::complete_errors(declaration) != Ok(true) {
        return Ok(());
    }
    let prefix = " ".repeat(indent);
    let nested = " ".repeat(indent + 4);
    if declare {
        writeln!(out, "{prefix}var _cottExpectedError: kotlin.String? = null\n{prefix}var _cottExpectedErrorClause: kotlin.String? = null")
            .expect("writing to String cannot fail");
    }
    writeln!(
        out,
        "{prefix}if (cott_runtime.CottRuntime.{}({})) {{",
        if asynchronous {
            "contractsEnabledSuspend"
        } else {
            "contractsEnabled"
        },
        runtime_mode(config)
    )
    .expect("writing to String cannot fail");
    for clause in errors {
        let mut guard = clause.get("guard").cloned();
        if let Some(guard) = &mut guard {
            rewrite_parameter_references(guard, locals);
            rewrite_const_references(guard, declaration);
        }
        let condition = match clause.get("when").filter(|value| !value.is_null()) {
            Some(expression) => {
                let mut expression = expression.clone();
                rewrite_parameter_references(&mut expression, locals);
                rewrite_const_references(&mut expression, declaration);
                callable_expression(
                    render_condition(&expression, guard.as_ref(), false)?,
                    asynchronous,
                )
            }
            None if guard.as_ref().is_some_and(|guard| !guard.is_null()) => {
                let literal = serde_json::json!({
                    "kind": "literal",
                    "value": {"kind": "bool", "value": true},
                    "type": {"kind": "primitive", "name": "bool"}
                });
                callable_expression(
                    expressions::render_guard(
                        guard.as_ref().expect("checked guard"),
                        &literal,
                        false,
                    )?,
                    asynchronous,
                )
            }
            None => continue,
        };
        let variant = clause
            .get("variant")
            .and_then(Value::as_str)
            .ok_or_else(|| format!("error clause on `{symbol}` is missing variant"))?;
        writeln!(
            out,
            "{nested}if (_cottExpectedError == null && ({condition})) {{ _cottExpectedError = {}; _cottExpectedErrorClause = {} }}",
            kotlin_string(variant),
            kotlin_string(&clause_label(clause)?),
        )
        .expect("writing to String cannot fail");
    }
    writeln!(out, "{prefix}}}").expect("writing to String cannot fail");
    Ok(())
}

fn render_error_contracts(
    out: &mut String,
    declaration: &Map<String, Value>,
    symbol: &str,
    indent: usize,
    asynchronous: bool,
) -> Result<(), String> {
    let clauses = declaration
        .get("contract")
        .and_then(Value::as_object)
        .and_then(|contract| contract.get("clauses"))
        .and_then(Value::as_array)
        .map(Vec::as_slice)
        .or_else(|| {
            declaration
                .get("contracts")
                .and_then(Value::as_object)
                .and_then(|contracts| contracts.get("errors"))
                .and_then(Value::as_array)
                .map(Vec::as_slice)
        })
        .unwrap_or_default();
    let errors = clauses
        .iter()
        .filter(|clause| clause.get("kind").and_then(Value::as_str) == Some("error"))
        .collect::<Vec<_>>();
    if errors.is_empty() && crate::ir::complete_errors(declaration) != Ok(true) {
        return Ok(());
    }
    let prefix = " ".repeat(indent);
    writeln!(
        out,
        "{prefix}val _cottActualError = (_cottResult as? cott_runtime.Err<*>)?.error"
    )
    .expect("writing to String cannot fail");
    let unconditional = errors
        .iter()
        .filter(|clause| {
            clause.get("guard").is_none_or(Value::is_null)
                && clause.get("when").is_none_or(Value::is_null)
        })
        .filter_map(|clause| clause.get("variant").and_then(Value::as_str))
        .map(kotlin_string)
        .collect::<Vec<_>>();
    let allowed = format!("setOf<kotlin.String>({})", unconditional.join(", "));
    writeln!(out, "{prefix}val _cottActualErrorVariant = (_cottActualError as? cott_runtime.CottVariant)?.cottVariant").expect("writing to String cannot fail");
    let condition = format!(
        "if (_cottExpectedError != null) _cottActualErrorVariant == _cottExpectedError else _cottActualError == null || _cottActualErrorVariant in {allowed}"
    );
    writeln!(
        out,
        "{prefix}cott_runtime.CottRuntime.{}({condition}, {}, \"error\", clause = \"error-return\", expected = _cottExpectedError ?: {allowed}.toString(), actual = _cottActualErrorVariant ?: _cottActualError?.javaClass?.name)",
        if asynchronous { "checkContractSuspend" } else { "checkContract" },
        kotlin_string(symbol)
    )
    .expect("writing to String cannot fail");
    for clause in errors {
        let label = clause_label(clause)?;
        let variant = required_string(
            clause.as_object().ok_or("error clause must be an object")?,
            "variant",
            symbol,
        )?;
        let applicable = if clause.get("guard").is_none_or(Value::is_null)
            && clause.get("when").is_none_or(Value::is_null)
        {
            format!("_cottActualErrorVariant == {}", kotlin_string(variant))
        } else {
            format!("_cottExpectedErrorClause == {}", kotlin_string(&label))
        };
        writeln!(
            out,
            "{prefix}if ({applicable}) cott_runtime.CottRuntime.{}(_cottActualErrorVariant == {}, {}, \"error\", clause = {}, span = {})",
            if asynchronous { "checkContractSuspend" } else { "checkContract" },
            kotlin_string(variant),
            kotlin_string(symbol),
            kotlin_string(&label),
            render_span(clause.get("span"))?,
        )
        .expect("writing to String cannot fail");
    }
    Ok(())
}

fn implementation_resolved(
    concrete: &str,
    implementation: &Map<String, Value>,
    _callables: &BTreeMap<String, KotlinCallable>,
    bindings: &BTreeMap<&str, &KotlinBinding>,
) -> bool {
    implementation
        .get("selected_methods")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .all(|slot| {
            let method = slot
                .get("trait_method")
                .and_then(Value::as_str)
                .map(local_name)
                .unwrap_or_default();
            match slot
                .get("selected")
                .and_then(Value::as_object)
                .and_then(|selected| selected.get("origin"))
                .and_then(Value::as_str)
            {
                Some("explicit") => bindings.contains_key(format!("{concrete}.{method}").as_str()),
                Some("default" | "specialization") => slot
                    .get("selected")
                    .and_then(Value::as_object)
                    .and_then(|selected| selected.get("function"))
                    .and_then(Value::as_object)
                    .and_then(|function| function.get("verified_facade"))
                    .and_then(Value::as_str)
                    .is_some_and(|symbol| bindings.contains_key(symbol)),
                _ => false,
            }
        })
}

fn render_implementation_class(
    out: &mut String,
    config: &KotlinProjectConfig,
    implementation: &Map<String, Value>,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
    callables: &BTreeMap<String, KotlinCallable>,
    bindings: &BTreeMap<&str, &KotlinBinding>,
) -> Result<(), String> {
    let canonical = required_string(implementation, "name", "implementation")?;
    let name = escape_identifier(local_name(canonical))?;
    let mut traits = required_array(implementation, "traits", canonical)?
        .iter()
        .map(|trait_ref| {
            render_trait_reference(trait_ref, Some(implementation), declarations, None)
        })
        .collect::<Result<Vec<_>, _>>()?;
    traits.push("cott_runtime.CottFieldValue".to_owned());
    traits.push("cott_runtime.CottTraitCarrier".to_owned());
    let extends = format!(" : {}", traits.join(", "));
    let state = required_array(implementation, "state", canonical)?;
    let initializer = implementation.get("init").and_then(Value::as_object);
    let constructor_parameters = initializer
        .map(|initializer| render_parameters(initializer, true))
        .transpose()?
        .unwrap_or_default();
    writeln!(
        out,
        "\npublic class {name}({}){extends} {{",
        constructor_parameters.join(", ")
    )
    .expect("writing to String cannot fail");
    writeln!(
        out,
        "    public companion object {{\n        public val cottFactory: cott_runtime.CottFactory<{name}> = cott_runtime.CottFactory.of({name}::class.java)\n    }}"
    )
    .expect("writing to String cannot fail");
    let trait_tokens = trait_specializations(implementation, declarations)?
        .iter()
        .map(|trait_ref| trait_marker(trait_ref).map(|name| format!("cott_runtime.{name}")))
        .collect::<Result<Vec<_>, _>>()?;
    writeln!(
        out,
        "    override val cottTraits: cott_runtime.CottSet<cott_runtime.CottTrait<*>> = cott_runtime.CottSet(listOf({}))",
        trait_tokens.join(", ")
    )
    .expect("writing to String cannot fail");
    out.push_str("    private val _cottResourceGuard: cott_runtime.CottResourceGuard = cott_runtime.CottResourceGuard()\n");
    let mut const_trait_properties = BTreeMap::<String, (String, String)>::new();
    for trait_ref in trait_specializations(implementation, declarations)? {
        let trait_ref = trait_ref
            .as_object()
            .ok_or_else(|| "implementation trait reference must be an object".to_owned())?;
        let trait_name = required_string(trait_ref, "name", canonical)?;
        let (_, trait_declaration) = declarations
            .get(trait_name)
            .copied()
            .ok_or_else(|| format!("unknown implementation trait `{trait_name}`"))?;
        for (parameter, argument) in required_array(trait_declaration, "generics", trait_name)?
            .iter()
            .zip(required_array(trait_ref, "args", trait_name)?)
            .filter(|(parameter, _)| parameter.get("kind").and_then(Value::as_str) == Some("const"))
        {
            let parameter_name = parameter
                .get("name")
                .and_then(Value::as_str)
                .ok_or_else(|| format!("trait `{trait_name}` const generic is missing name"))?;
            let value = argument
                .get("value")
                .ok_or_else(|| format!("trait `{trait_name}` const argument is missing value"))?;
            let property = format!("_cott_const_{}", safe_internal_name(parameter_name));
            let assignment = (
                types::render_const_marker(value)?,
                render_const_witness(value)?,
            );
            if const_trait_properties
                .insert(property.clone(), assignment.clone())
                .is_some_and(|previous| previous != assignment)
            {
                return Err(format!(
                    "implementation `{canonical}` inherits incompatible const witness property `{property}`"
                ));
            }
        }
    }
    for (property, (ty, witness)) in const_trait_properties {
        writeln!(out, "    override val {property}: {ty} = {witness}")
            .expect("writing to String cannot fail");
    }
    let initializer_names = initializer
        .and_then(|initializer| initializer.get("parameters"))
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter_map(|parameter| parameter.get("name").and_then(Value::as_str))
        .collect::<BTreeSet<_>>();
    for field in state {
        let field = field
            .as_object()
            .ok_or_else(|| format!("implementation `{canonical}` state field must be object"))?;
        let field_name = required_string(field, "name", canonical)?;
        let ty = required(field, "type", canonical)?;
        let initial = if initializer_names.contains(field_name) {
            escape_identifier(field_name)?
        } else {
            render_value(
                field.get("default").filter(|value| !value.is_null()).ok_or_else(|| {
                    format!(
                        "implementation `{canonical}` state field `{field_name}` has neither an initializer parameter nor a default"
                    )
                })?,
                Some(ty),
            )?
        };
        writeln!(
            out,
            "    public var {}: {} = {initial}\n        internal set",
            escape_identifier(field_name)?,
            render_contextual_type(ty, None, declarations)?
        )
        .expect("writing to String cannot fail");
    }
    writeln!(
        out,
        "    override val cottTypeIdentity: kotlin.String get() = {}",
        kotlin_string(canonical)
    )
    .expect("writing to String cannot fail");
    let state_names = state
        .iter()
        .filter_map(|field| field.get("name").and_then(Value::as_str))
        .map(kotlin_string)
        .collect::<Vec<_>>();
    writeln!(
        out,
        "    override val cottFieldNames: cott_runtime.CottList<kotlin.String> get() = cott_runtime.CottList(listOf({}))",
        state_names.join(", ")
    )
    .expect("writing to String cannot fail");
    out.push_str("    override fun cottField(name: kotlin.String): kotlin.Any? = when (name) {\n");
    for field in state {
        let field_name = field
            .get("name")
            .and_then(Value::as_str)
            .expect("validated state field");
        writeln!(
            out,
            "        {} -> this.{}",
            kotlin_string(field_name),
            escape_identifier(field_name)?
        )
        .expect("writing to String cannot fail");
    }
    out.push_str("        else -> cott_runtime.CottRuntime.violation(\"unknown canonical field\", symbol = cottTypeIdentity, phase = \"field\", actual = name)\n    }\n");
    out.push_str("    init {\n");
    render_identity_preflight(out, config, 8);
    let initializer_locals = if let Some(initializer) = initializer {
        let locals = render_parameter_validation(
            out,
            config,
            initializer,
            declarations,
            8,
            false,
            true,
            None,
        )?;
        render_contract_clauses(out, config, initializer, canonical, true, 8, false, &locals)?;
        locals
    } else {
        BTreeMap::new()
    };
    for field in state {
        let field_name = field
            .get("name")
            .and_then(Value::as_str)
            .expect("validated state field");
        writeln!(
            out,
            "        this.{} = cott_runtime.CottRuntime.abi(this.{}, {}, cott_runtime.RuntimeValidation.BOUNDARY, {})",
            escape_identifier(field_name)?,
            escape_identifier(field_name)?,
            descriptor_for(
                field.get("type").expect("validated state type"),
                declarations,
                &config.kotlin.external_types,
            )?,
            kotlin_string(&format!("$.{field_name}"))
        )
        .expect("writing to String cannot fail");
    }
    if let Some(initializer) = initializer {
        render_contract_clauses(
            out,
            config,
            initializer,
            canonical,
            false,
            8,
            false,
            &initializer_locals,
        )?;
    }
    let initial_fields = state
        .iter()
        .map(|field| {
            let field_name = field
                .get("name")
                .and_then(Value::as_str)
                .ok_or_else(|| "state field is missing name".to_owned())?;
            Ok(format!(
                "cott_runtime.CottStateField({}, {}, {{ this.{} }}, {{ value -> this.{} = value as {} }})",
                kotlin_string(field_name),
                descriptor_for(
                    field
                        .get("type")
                        .ok_or_else(|| "state field is missing type".to_owned())?,
                    declarations,
                    &config.kotlin.external_types,
                )?,
                escape_identifier(field_name)?,
                escape_identifier(field_name)?,
                render_contextual_type(
                    field.get("type").expect("checked state type"),
                    None,
                    declarations,
                )?,
            ))
        })
        .collect::<Result<Vec<_>, String>>()?;
    let initial_invariants = implementation
        .get("invariants")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .map(|invariant| {
            let expression = render_condition(
                invariant
                    .get("expression")
                    .ok_or_else(|| "implementation invariant is missing expression".to_owned())?,
                None,
                true,
            )?;
            let clause = format!(
                "invariant:{}",
                invariant
                    .get("clause_id")
                    .and_then(Value::as_u64)
                    .ok_or_else(|| "implementation invariant is missing clause_id".to_owned())?
            );
            let statement = format!(
                "cott_runtime.CottRuntime.invariant({expression}, {}, clause = {}, span = {})",
                kotlin_string(canonical),
                kotlin_string(&clause),
                render_span(invariant.get("span"))?
            );
            Ok(format!(
                "cott_runtime.CottInvariant.checked({}, {{ {} }}, {})",
                kotlin_string(&clause),
                guarded_check(invariant.get("guard"), statement)?,
                render_span(invariant.get("span"))?
            ))
        })
        .collect::<Result<Vec<_>, String>>()?;
    writeln!(
        out,
        "        cott_runtime.CottResourceContract({}, listOf({}), emptySet(), emptyList(), listOf({}), _cottResourceGuard).validateInitial()",
        kotlin_string(canonical),
        initial_fields.join(", "),
        initial_invariants.join(", "),
    )
    .expect("writing to String cannot fail");
    out.push_str("    }\n");
    for slot in required_array(implementation, "selected_methods", canonical)? {
        let trait_method = slot
            .get("trait_method")
            .and_then(Value::as_str)
            .ok_or_else(|| {
                format!("implementation `{canonical}` selected slot is missing trait_method")
            })?;
        let method_name = local_name(trait_method);
        let symbol = format!("{canonical}.{method_name}");
        let callable = callables
            .get(&symbol)
            .ok_or_else(|| format!("selected method `{symbol}` absent from Kotlin plan"))?;
        render_impl_method(
            out,
            config,
            implementation,
            slot,
            callable,
            declarations,
            bindings,
        )?;
    }
    out.push_str("}\n");
    Ok(())
}

fn render_impl_method(
    out: &mut String,
    config: &KotlinProjectConfig,
    implementation: &Map<String, Value>,
    slot: &Value,
    callable: &KotlinCallable,
    declarations: &BTreeMap<String, (&str, &Map<String, Value>)>,
    bindings: &BTreeMap<&str, &KotlinBinding>,
) -> Result<(), String> {
    let slot = slot
        .as_object()
        .ok_or_else(|| format!("selected method `{}` must be an object", callable.symbol))?;
    let method_value = resolved_method_declaration(callable, implementation, slot, declarations)?;
    let method = method_value
        .as_object()
        .expect("resolved method declaration remains an object");
    let owner_witnesses = selected_owner_const_witnesses(slot, declarations)?;
    let asynchronous = method.get("callable_kind").and_then(Value::as_str) == Some("async");
    let rendering = callable_rendering(method, declarations, BTreeMap::new())?;
    let parameters = render_parameters_contextual(method, false, &rendering.context)?.join(", ");
    let return_value = required(method, "return_type", &callable.symbol)?;
    let return_type = render_type_contextual(return_value, None, Some(&rendering.context))?;
    writeln!(
        out,
        "\n    override {}fun {} {}({parameters}): {return_type}{} {{",
        if asynchronous { "suspend " } else { "" },
        rendering.generics,
        escape_identifier(&callable.name)?,
        rendering.where_bounds,
    )
    .expect("writing to String cannot fail");
    render_identity_preflight(out, config, 8);
    let locals = parameter_local_names(method)?;
    let state = required_array(implementation, "state", &callable.symbol)?;
    let selected = slot
        .get("selected")
        .and_then(Value::as_object)
        .ok_or_else(|| format!("selected method `{}` is missing selection", callable.symbol))?;
    let origin = required_string(selected, "origin", &callable.symbol)?;
    let target = if origin == "explicit" {
        render_qualified(
            &bindings
                .get(callable.symbol.as_str())
                .ok_or_else(|| format!("resolved method `{}` has no binding", callable.symbol))?
                .target_symbol,
        )?
    } else {
        let facade = selected
            .get("function")
            .and_then(Value::as_object)
            .and_then(|function| function.get("verified_facade"))
            .and_then(Value::as_str)
            .ok_or_else(|| {
                format!(
                    "default method `{}` has no verified facade",
                    callable.symbol
                )
            })?;
        render_qualified(facade)?
    };
    render_parameter_placeholders(out, method, &locals, 8)?;
    let mut arguments = vec!["this".to_owned()];
    arguments.extend(
        render_call_arguments(method, &locals)?
            .split(", ")
            .filter(|value| !value.is_empty())
            .map(str::to_owned),
    );
    arguments.extend(
        owner_witnesses
            .iter()
            .map(|witness| format!("this.{}", witness.name)),
    );
    let modifies = method
        .get("modifies")
        .and_then(Value::as_array)
        .map(Vec::as_slice)
        .unwrap_or_default();
    let transitions = method
        .get("transitions")
        .and_then(Value::as_array)
        .map(Vec::as_slice)
        .unwrap_or_default();
    let fields = state
        .iter()
        .map(|field| {
            let name = field
                .get("name")
                .and_then(Value::as_str)
                .ok_or_else(|| "state field missing name".to_owned())?;
            Ok(format!(
                "cott_runtime.CottStateField({}, {}, {{ this.{} }}, {{ value -> this.{} = value as {} }})",
                kotlin_string(name),
                descriptor_for(
                    field
                        .get("type")
                        .ok_or_else(|| "state field missing type".to_owned())?,
                    declarations,
                    &config.kotlin.external_types
                )?,
                escape_identifier(name)?,
                escape_identifier(name)?,
                render_contextual_type(field.get("type").expect("checked"), None, declarations,)?
            ))
        })
        .collect::<Result<Vec<_>, String>>()?;
    let modifies = modifies
        .iter()
        .filter_map(Value::as_str)
        .map(local_name)
        .map(kotlin_string)
        .collect::<Vec<_>>();
    let transitions = transitions
        .iter()
        .map(|transition| {
            let field = transition
                .get("field")
                .and_then(Value::as_str)
                .ok_or_else(|| "transition missing field".to_owned())?;
            let from = transition
                .get("from")
                .and_then(Value::as_str)
                .ok_or_else(|| "transition missing from".to_owned())?;
            let to = transition
                .get("to")
                .and_then(Value::as_str)
                .ok_or_else(|| "transition missing to".to_owned())?;
            Ok(format!(
                "cott_runtime.CottTransition({}, {}, {})",
                kotlin_string(local_name(field)),
                render_qualified(from)?,
                render_qualified(to)?
            ))
        })
        .collect::<Result<Vec<_>, String>>()?;
    let invariants = implementation
        .get("invariants")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .map(|invariant| {
            let expression = render_condition(
                invariant
                    .get("expression")
                    .ok_or_else(|| "implementation invariant missing expression".to_owned())?,
                None,
                true,
            )?;
            let clause = format!(
                "invariant:{}",
                invariant
                    .get("clause_id")
                    .and_then(Value::as_u64)
                    .ok_or_else(|| "implementation invariant missing clause_id".to_owned())?
            );
            let statement = format!(
                "cott_runtime.CottRuntime.invariant({expression}, {}, clause = {}, span = {})",
                kotlin_string(&callable.symbol),
                kotlin_string(&clause),
                render_span(invariant.get("span"))?
            );
            Ok(format!(
                "cott_runtime.CottInvariant.checked({}, {{ {} }}, {})",
                kotlin_string(&clause),
                guarded_check(invariant.get("guard"), statement)?,
                render_span(invariant.get("span"))?
            ))
        })
        .collect::<Result<Vec<_>, String>>()?;
    let has_errors = method
        .get("contracts")
        .and_then(Value::as_object)
        .and_then(|contracts| contracts.get("errors"))
        .and_then(Value::as_array)
        .is_some_and(|errors| !errors.is_empty());
    if has_errors {
        out.push_str("        var _cottExpectedError: kotlin.String? = null\n        var _cottExpectedErrorClause: kotlin.String? = null\n");
    }
    for field in state {
        let field_name = field
            .get("name")
            .and_then(Value::as_str)
            .expect("validated state field");
        writeln!(
            out,
            "        var _cottOld_{}: {} = this.{}",
            safe_internal_name(field_name),
            render_contextual_type(
                field.get("type").expect("validated state type"),
                None,
                declarations,
            )?,
            escape_identifier(field_name)?
        )
        .expect("writing to String cannot fail");
    }
    writeln!(
        out,
        "        val _cottResource = cott_runtime.CottResourceContract({}, listOf({}), setOf({}), listOf({}), listOf({}), _cottResourceGuard)",
        kotlin_string(&callable.symbol),
        fields.join(", "),
        modifies.join(", "),
        transitions.join(", "),
        invariants.join(", ")
    )
    .expect("writing to String cannot fail");
    writeln!(
        out,
        "        return _cottResource.{}(",
        if asynchronous {
            "enforceMutationSuspend"
        } else {
            "enforceMutation"
        }
    )
    .expect("writing to String cannot fail");
    out.push_str("            before = {\n");
    render_parameter_validation(
        out,
        config,
        method,
        declarations,
        16,
        asynchronous,
        false,
        Some(&rendering.context),
    )?;
    render_contract_clauses(
        out,
        config,
        method,
        &callable.symbol,
        true,
        16,
        asynchronous,
        &locals,
    )?;
    render_expected_errors(
        out,
        config,
        method,
        &callable.symbol,
        16,
        asynchronous,
        &locals,
        false,
    )?;
    for field in state {
        let field_name = field
            .get("name")
            .and_then(Value::as_str)
            .expect("validated state field");
        writeln!(
            out,
            "                _cottOld_{} = cott_runtime.CottRuntime.deepSnapshot(this.{}) as {}",
            safe_internal_name(field_name),
            escape_identifier(field_name)?,
            render_contextual_type(
                field.get("type").expect("validated state type"),
                None,
                declarations,
            )?
        )
        .expect("writing to String cannot fail");
    }
    out.push_str("            },\n            implementation = {\n                try {\n");
    writeln!(
        out,
        "                    {target}({})",
        arguments.join(", ")
    )
    .expect("writing to String cannot fail");
    out.push_str("                } catch (error: cott_runtime.CottContractViolation) {\n                    if (error.symbol == null) error.symbol = ");
    out.push_str(&kotlin_string(&callable.symbol));
    out.push_str("\n                    throw error\n                } catch (error: java.util.concurrent.CancellationException) {\n");
    if asynchronous {
        out.push_str("                    throw error\n");
    } else {
        writeln!(
            out,
            "                    cott_runtime.CottRuntime.violation(\"synchronous implementation threw cancellation\", symbol = {}, phase = \"implementation-call\", cause = error)",
            kotlin_string(&callable.symbol)
        )
        .expect("writing to String cannot fail");
    }
    writeln!(
        out,
        "                }} catch (error: kotlin.Throwable) {{\n                    cott_runtime.CottRuntime.violation(\"implementation raised an undeclared exception\", symbol = {}, phase = \"implementation-call\", expected = \"declared Result error or ordinary return\", actual = error::class.java.name, cause = error)\n                }}\n            }},\n            after = {{ _cottRawResult ->",
        kotlin_string(&callable.symbol)
    )
    .expect("writing to String cannot fail");
    if is_never(return_value) {
        writeln!(
            out,
            "                cott_runtime.CottRuntime.violation(\"Never method returned\", symbol = {}, phase = \"return\")",
            kotlin_string(&callable.symbol)
        )
        .expect("writing to String cannot fail");
    } else {
        let descriptor = descriptor_for_contextual(
            return_value,
            declarations,
            &config.kotlin.external_types,
            &rendering.context,
        )?;
        writeln!(
            out,
            "                val _cottResult = cott_runtime.CottRuntime.{}(_cottRawResult, {descriptor}, {}, \"$.return\")",
            if asynchronous {
                "returnValueSuspend"
            } else {
                "returnValue"
            },
            runtime_mode(config)
        )
        .expect("writing to String cannot fail");
        render_contract_clauses(
            out,
            config,
            method,
            &callable.symbol,
            false,
            16,
            asynchronous,
            &locals,
        )?;
        out.push_str("                _cottResult\n");
    }
    out.push_str("            },\n        )\n    }\n");
    Ok(())
}

fn render_identity_preflight(out: &mut String, config: &KotlinProjectConfig, indent: usize) {
    let prefix = " ".repeat(indent);
    writeln!(
        out,
        "{prefix}cott_runtime.CottRuntime.requireIdentity({}, {}, {KOTLIN_RUNTIME_ABI})",
        kotlin_string(&config.project.name),
        kotlin_string(&config.project.version)
    )
    .expect("writing to String cannot fail");
}

fn rewrite_parameter_references(value: &mut Value, locals: &BTreeMap<String, String>) {
    match value {
        Value::Array(values) => {
            for value in values {
                rewrite_parameter_references(value, locals);
            }
        }
        Value::Object(object) => {
            if object.get("kind").and_then(Value::as_str) == Some("parameter_ref")
                && let Some(symbol) = object.get("symbol").and_then(Value::as_str)
                && let Some(local) = locals.get(local_name(symbol))
            {
                object.insert("symbol".to_owned(), Value::String(local.clone()));
                return;
            }
            for value in object.values_mut() {
                rewrite_parameter_references(value, locals);
            }
        }
        _ => {}
    }
}
fn rewrite_const_references(value: &mut Value, declaration: &Map<String, Value>) {
    let constants = declaration
        .get("generics")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter(|generic| generic.get("kind").and_then(Value::as_str) == Some("const"))
        .filter_map(|generic| generic.get("name").and_then(Value::as_str))
        .map(|name| {
            (
                name.to_owned(),
                format!("_cott_const_{}.value", safe_internal_name(name)),
            )
        })
        .collect::<BTreeMap<_, _>>();
    fn rewrite(value: &mut Value, constants: &BTreeMap<String, String>) {
        match value {
            Value::Array(values) => {
                for value in values {
                    rewrite(value, constants);
                }
            }
            Value::Object(object) => {
                if matches!(
                    object.get("kind").and_then(Value::as_str),
                    Some("parameter_ref" | "binding_ref")
                ) && let Some(symbol) = object.get("symbol").and_then(Value::as_str)
                    && let Some(code) = constants.get(local_name(symbol))
                {
                    object.clear();
                    object.insert(
                        "kind".to_owned(),
                        Value::String("kotlin_synthetic".to_owned()),
                    );
                    object.insert("code".to_owned(), Value::String(code.clone()));
                    return;
                }
                for value in object.values_mut() {
                    rewrite(value, constants);
                }
            }
            _ => {}
        }
    }
    rewrite(value, &constants);
}

fn callable_expression(expression: String, asynchronous: bool) -> String {
    if asynchronous {
        expression
            .replace(
                "cott_runtime.CottRuntime.fixturePath(",
                "cott_runtime.CottRuntime.fixturePathSuspend(",
            )
            .replace(
                "cott_runtime.CottRuntime.fixtureUrl(",
                "cott_runtime.CottRuntime.fixtureUrlSuspend(",
            )
    } else {
        expression
    }
}

fn generic_const_kind(generic: &Value) -> Result<&'static str, String> {
    match generic.get("type").and_then(Value::as_str) {
        Some("u8" | "U8") => Ok("cott_runtime.CottIntKind.U8"),
        Some("u16" | "U16") => Ok("cott_runtime.CottIntKind.U16"),
        Some("u32" | "U32") => Ok("cott_runtime.CottIntKind.U32"),
        Some("u64" | "U64") => Ok("cott_runtime.CottIntKind.U64"),
        Some(other) => Err(format!("unsupported const generic integer kind `{other}`")),
        None => Err("const generic is missing integer type".to_owned()),
    }
}

fn runtime_mode(config: &KotlinProjectConfig) -> &'static str {
    match &config.kotlin.runtime_validation {
        RuntimeValidation::Boundary => "cott_runtime.RuntimeValidation.BOUNDARY",
        RuntimeValidation::TestOnly => "cott_runtime.RuntimeValidation.TEST_ONLY",
        RuntimeValidation::Off => "cott_runtime.RuntimeValidation.OFF",
    }
}

fn is_never(value: &Value) -> bool {
    value.get("kind").and_then(Value::as_str) == Some("primitive")
        && value.get("name").and_then(Value::as_str) == Some("never")
}

fn safe_internal_name(name: &str) -> String {
    let mut result = String::new();
    for byte in name.bytes() {
        if byte.is_ascii_alphanumeric() || byte == b'_' {
            result.push(byte as char);
        } else {
            write!(result, "_{byte:02x}").expect("writing to String cannot fail");
        }
    }
    if result.is_empty() {
        "value".to_owned()
    } else {
        result
    }
}
