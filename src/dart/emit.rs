use std::collections::{BTreeMap, BTreeSet};
use std::fmt::Write as _;
use std::ops::Deref;
use std::path::{Component, Path, PathBuf};

use serde_json::{Map, Value};
use tree_sitter::{Node, Parser};

use crate::hash::sha256_hex;
use crate::hir::INTRINSIC_EFFECTS;
use crate::manifest::{DartProjectConfig, RuntimeValidation};

use super::binding::partition_source;
use super::expressions::{clause_label, render_condition, render_span};
use super::runtime::render_runtime;
use super::types::{
    self, DartEnumProjection, DartTypeContext, associated_type_name, dart_string,
    enum_variant_name, escape_identifier, local_name, module_of, module_prefix,
    render_canonical_symbol, render_const_kind, render_const_value, render_const_witness,
    render_type_contextual, render_value_contextual, trait_marker,
};
use super::{DartBinding, DartCallable, DartEmission, DartModule, DartOwner, DartPlan};

const DART_RUNTIME_ABI: i32 = 2;

pub fn render_type(plan: &DartPlan, ty: &Value) -> Result<String, String> {
    let declarations = declaration_index(plan)?;
    let context = EmissionTypeContext::new(&declarations);
    render_type_contextual(ty, None, Some(&context))
}

pub(crate) fn render_constructor_invocation(
    constructor: &str,
    positional: &[String],
    named: &[String],
) -> String {
    match (positional.is_empty(), named.is_empty()) {
        (true, true) => format!("{constructor}()"),
        (true, false) => format!("{constructor}({})", named.join(", ")),
        (false, true) => format!("{constructor}({})", positional.join(", ")),
        (false, false) => format!(
            "{constructor}({}, {})",
            positional.join(", "),
            named.join(", ")
        ),
    }
}

pub(crate) fn render_consumer_type(
    plan: &DartPlan,
    ty: &Value,
    aliases: &BTreeMap<String, String>,
) -> Result<String, String> {
    rewrite_consumer_prefixes(render_type(plan, ty)?, aliases)
}

pub(crate) fn render_consumer_expression(
    expression: &Value,
    aliases: &BTreeMap<String, String>,
    projection: &DartEnumProjection,
) -> Result<String, String> {
    rewrite_consumer_prefixes(
        super::expressions::render_expression_contextual(expression, None, projection)?,
        aliases,
    )
}

pub(crate) fn render_consumer_dyn(
    plan: &DartPlan,
    trait_ref: &Value,
    value: &str,
    aliases: &BTreeMap<String, String>,
) -> Result<String, String> {
    let declarations = declaration_index(plan)?;
    let rendered = rewrite_consumer_prefixes(
        render_existential_trait_reference(trait_ref, &declarations)?,
        aliases,
    )?;
    let identity = serde_json::to_string(trait_ref)
        .map_err(|error| format!("serialize consumer Dyn trait: {error}"))?;
    Ok(format!(
        "(() {{ final _cott_dyn_value = {value}; final _cott_dyn_trait = (_cott_dyn_value as cott_runtime.CottTraitCarrier).cottTraits.singleWhere((candidate) => candidate.id == {}); return cott_runtime.Dyn<{rendered}>.of(_cott_dyn_value as {rendered}, _cott_dyn_trait as cott_runtime.CottTrait<{rendered}>); }})()",
        dart_string(&identity)
    ))
}

pub(crate) fn render_consumer_opaque(
    tag: &str,
    payload: &str,
    marker_module: &str,
    aliases: &BTreeMap<String, String>,
) -> Result<String, String> {
    let alias = aliases
        .get(marker_module)
        .ok_or_else(|| format!("consumer opaque marker module `{marker_module}` has no alias"))?;
    escape_identifier(alias)?;
    Ok(format!(
        "cott_runtime.Opaque.of(const {alias}.{}(), {payload})",
        types::opaque_marker(tag)
    ))
}

pub(crate) fn render_consumer_symbol(
    symbol: &str,
    aliases: &BTreeMap<String, String>,
) -> Result<String, String> {
    rewrite_consumer_prefixes(render_canonical_symbol(symbol, None)?, aliases)
}

pub(crate) fn render_consumer_enum_variant(
    symbol: &str,
    aliases: &BTreeMap<String, String>,
    projection: &DartEnumProjection,
) -> Result<String, String> {
    rewrite_consumer_prefixes(enum_variant_name(symbol, None, projection)?, aliases)
}

pub(crate) fn render_consumer_resource_state(
    symbol: &str,
    aliases: &BTreeMap<String, String>,
) -> Result<String, String> {
    rewrite_consumer_prefixes(resource_state_name(symbol, None)?, aliases)
}

pub(crate) fn render_consumer_type_witnesses(
    config: &DartProjectConfig,
    plan: &DartPlan,
    ty: &Value,
    aliases: &BTreeMap<String, String>,
) -> Result<Vec<String>, String> {
    let declarations = declaration_index(plan)?;
    ty.get("args")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter(|argument| argument.get("kind").and_then(Value::as_str) == Some("type"))
        .map(|argument| {
            rewrite_consumer_prefixes(
                descriptor_for(
                    required_value(argument, "type", "consumer generic argument")?,
                    &declarations,
                    &config.dart.external_types,
                )?,
                aliases,
            )
        })
        .collect()
}

pub(crate) fn render_consumer_callable_witnesses(
    config: &DartProjectConfig,
    plan: &DartPlan,
    callable: &DartCallable,
    type_arguments: &BTreeMap<String, Value>,
    aliases: &BTreeMap<String, String>,
) -> Result<Vec<String>, String> {
    let declarations = declaration_index(plan)?;
    let declaration_value = if let Some(owner) = callable.owner.as_ref() {
        let owner = owner
            .as_object()
            .ok_or_else(|| format!("callable `{}` owner must be an object", callable.symbol))?;
        let slot = selected_method_slot(owner, callable)?;
        resolved_method_declaration(callable, owner, slot, &declarations)?
    } else {
        callable.declaration.clone()
    };
    let declaration = declaration_value
        .as_object()
        .ok_or_else(|| format!("callable `{}` must be an object", callable.symbol))?;
    let rendering = callable_rendering(declaration, &declarations, BTreeMap::new())?;
    let mut witnesses = Vec::new();
    for generic in required_array(declaration, "generics", &callable.symbol)? {
        if generic.get("kind").and_then(Value::as_str) != Some("type") {
            continue;
        }
        let name = generic.get("name").and_then(Value::as_str).ok_or_else(|| {
            format!(
                "callable `{}` type generic is missing name",
                callable.symbol
            )
        })?;
        let ty = type_arguments.get(name).ok_or_else(|| {
            format!(
                "consumer callable `{}` is missing concrete type argument `{name}`",
                callable.symbol
            )
        })?;
        witnesses.push(rewrite_consumer_prefixes(
            descriptor_for(ty, &declarations, &config.dart.external_types)?,
            aliases,
        )?);
    }
    for name in &rendering.associated {
        let parameter = rendering.associated_parameters.get(name).ok_or_else(|| {
            format!(
                "consumer callable `{}` lost associated witness `{name}`",
                callable.symbol
            )
        })?;
        let ty = resolve_consumer_associated_type(parameter, type_arguments, &declarations)?;
        witnesses.push(rewrite_consumer_prefixes(
            descriptor_for(&ty, &declarations, &config.dart.external_types)?,
            aliases,
        )?);
    }
    Ok(witnesses)
}

fn resolve_consumer_associated_type(
    parameter: &AssociatedParameter,
    type_arguments: &BTreeMap<String, Value>,
    declarations: &DeclarationIndex<'_>,
) -> Result<Value, String> {
    let base = resolve_consumer_projection_base(&parameter.base, type_arguments, declarations)?;
    let object = base
        .as_object()
        .filter(|object| object.get("kind").and_then(Value::as_str) == Some("named"))
        .ok_or_else(|| {
            format!(
                "associated consumer base for `{}.{}` is not a concrete nominal type",
                parameter.trait_name, parameter.slot_name
            )
        })?;
    let name = required_string(object, "name", "associated consumer base")?;
    let (kind, declaration) = declarations
        .get(name)
        .copied()
        .ok_or_else(|| format!("associated consumer base `{name}` is unknown"))?;
    if kind == "alias" {
        let target = instantiate_type(required(declaration, "target", name)?, declaration, object);
        let aliased = AssociatedParameter {
            base: target,
            trait_name: parameter.trait_name.clone(),
            slot_name: parameter.slot_name.clone(),
            bounds: parameter.bounds.clone(),
        };
        return resolve_consumer_associated_type(&aliased, type_arguments, declarations);
    }
    if kind != "impl" {
        return Err(format!(
            "associated consumer base `{name}` is `{kind}`, not an implementation nominal"
        ));
    }
    associated_assignment_type(declaration, &parameter.trait_name, &parameter.slot_name)
        .cloned()
        .ok_or_else(|| {
            format!(
                "implementation `{name}` has no associated assignment `{}.{}`",
                parameter.trait_name,
                local_name(&parameter.slot_name)
            )
        })
}

fn resolve_consumer_projection_base(
    value: &Value,
    type_arguments: &BTreeMap<String, Value>,
    declarations: &DeclarationIndex<'_>,
) -> Result<Value, String> {
    let Some(object) = value.as_object() else {
        return Err("consumer projection base must be a canonical type object".to_owned());
    };
    match object.get("kind").and_then(Value::as_str) {
        Some("type_parameter") => {
            let name = required_string(object, "name", "consumer type parameter")?;
            type_arguments
                .get(name)
                .cloned()
                .ok_or_else(|| format!("consumer projection is missing type argument `{name}`"))
        }
        Some("associated_projection") => {
            let parameter = AssociatedParameter {
                base: required(object, "base", "consumer associated projection")?.clone(),
                trait_name: required_string(object, "trait", "consumer associated projection")?
                    .to_owned(),
                slot_name: required_string(object, "name", "consumer associated projection")?
                    .to_owned(),
                bounds: Vec::new(),
            };
            resolve_consumer_associated_type(&parameter, type_arguments, declarations)
        }
        Some("named") => Ok(value.clone()),
        other => Err(format!(
            "consumer projection base has unsupported canonical kind `{other:?}`"
        )),
    }
}

fn rewrite_consumer_prefixes(
    mut rendered: String,
    aliases: &BTreeMap<String, String>,
) -> Result<String, String> {
    let mut replacements = BTreeMap::new();
    for (module, alias) in aliases {
        escape_identifier(alias)?;
        replacements.insert(module_prefix(module), alias.clone());
    }
    if replacements.is_empty() {
        return Ok(rendered);
    }

    let mut parser = Parser::new();
    parser
        .set_language(&tree_sitter_dart::LANGUAGE.into())
        .map_err(|error| format!("unable to load Dart syntax grammar: {error}"))?;
    let mut parsed = None;
    for (prefix, suffix) in [
        ("typedef _CottConsumerType = ", ";"),
        ("Object? _cottConsumerExpression() => ", ";"),
    ] {
        let mut source = String::with_capacity(prefix.len() + rendered.len() + suffix.len());
        source.push_str(prefix);
        let start = source.len();
        source.push_str(&rendered);
        let end = source.len();
        source.push_str(suffix);
        let tree = parser
            .parse(source.as_bytes(), None)
            .ok_or_else(|| "Dart syntax parser returned no tree".to_owned())?;
        if !tree.root_node().has_error() {
            parsed = Some((source, start, end, tree));
            break;
        }
    }
    let (source, start, end, tree) = parsed.ok_or_else(|| {
        "cannot rewrite module aliases in malformed generated Dart consumer fragment".to_owned()
    })?;
    let mut edits = Vec::new();
    collect_consumer_prefix_edits(
        tree.root_node(),
        &source,
        start,
        end,
        &replacements,
        &mut edits,
    );
    edits.sort_by_key(|edit| (edit.0, edit.1));
    edits.dedup_by(|left, right| left.0 == right.0 && left.1 == right.1);
    for (edit_start, edit_end, replacement) in edits.into_iter().rev() {
        rendered.replace_range(edit_start..edit_end, &replacement);
    }
    Ok(rendered)
}

fn collect_consumer_prefix_edits(
    node: Node<'_>,
    source: &str,
    fragment_start: usize,
    fragment_end: usize,
    replacements: &BTreeMap<String, String>,
    edits: &mut Vec<(usize, usize, String)>,
) {
    let range = node.byte_range();
    if matches!(node.kind(), "identifier" | "type_identifier")
        && range.start >= fragment_start
        && range.end < fragment_end
        && source.as_bytes().get(range.end) == Some(&b'.')
        && let Some(identifier) = source.get(range.clone())
        && let Some(replacement) = replacements.get(identifier)
    {
        edits.push((
            range.start - fragment_start,
            range.end - fragment_start,
            replacement.clone(),
        ));
    }
    let mut cursor = node.walk();
    for child in node.named_children(&mut cursor) {
        collect_consumer_prefix_edits(
            child,
            source,
            fragment_start,
            fragment_end,
            replacements,
            edits,
        );
    }
}

pub fn emit(
    config: &DartProjectConfig,
    plan: &DartPlan,
    bindings: &[DartBinding],
) -> Result<DartEmission, String> {
    validate_modules(plan)?;
    let declarations = declaration_index(plan)?;
    let callables = plan
        .callables()
        .iter()
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
    for path in files.keys() {
        if !safe_artifact_path(path) {
            return Err(format!(
                "Dart runtime renderer returned unsafe artifact path `{}`",
                path.display()
            ));
        }
    }
    insert_file(
        &mut files,
        PathBuf::from("dart/lib/src/cott_markers.dart"),
        render_markers(config, plan, &declarations)?.into_bytes(),
    )?;

    let mut public_symbols = BTreeMap::new();
    for module in &plan.modules {
        let mut exported = public_target_names(module)?;
        exported.sort();
        exported.dedup();
        public_symbols.insert(module.name.clone(), exported);

        let types = render_types_file(config, plan, module, &declarations, &bindings_by_symbol)?;
        insert_file(&mut files, types_path(&module.name)?, types.into_bytes())?;

        for callable in callables
            .values()
            .copied()
            .filter(|callable| callable.module == module.name && callable.owner.is_none())
        {
            let Some(binding) = bindings_by_symbol.get(callable.symbol.as_str()).copied() else {
                continue;
            };
            let source = render_callable_wrapper(config, plan, callable, binding, &declarations)?;
            insert_file(&mut files, wrapper_path(callable)?, source.into_bytes())?;
            let parsed = partition_source(&binding.bytes).map_err(|error| {
                format!("partition Dart binding `{}`: {error}", binding.cott_symbol)
            })?;
            let transformed = render_part(config, callable, &parsed.body)?;
            insert_file(
                &mut files,
                binding.runtime_origin.clone(),
                transformed.into_bytes(),
            )?;
        }

        for declaration in &module.declarations {
            let Some(implementation) = declaration
                .as_object()
                .filter(|value| value.get("kind").and_then(Value::as_str) == Some("impl"))
            else {
                continue;
            };
            let concrete = required_string(implementation, "name", &module.name)?;
            if implementation_resolved(concrete, implementation, &bindings_by_symbol) {
                let source = render_implementation_library(
                    config,
                    plan,
                    implementation,
                    &declarations,
                    &callables,
                    &bindings_by_symbol,
                )?;
                insert_file(
                    &mut files,
                    implementation_path(concrete)?,
                    source.into_bytes(),
                )?;
                for callable in callables.values().copied().filter(|callable| {
                    callable
                        .owner
                        .as_ref()
                        .and_then(|owner| owner.get("name"))
                        .and_then(Value::as_str)
                        == Some(concrete)
                }) {
                    let Some(binding) = bindings_by_symbol.get(callable.symbol.as_str()).copied()
                    else {
                        continue;
                    };
                    let parsed = partition_source(&binding.bytes).map_err(|error| {
                        format!("partition Dart binding `{}`: {error}", binding.cott_symbol)
                    })?;
                    let transformed = render_part(config, callable, &parsed.body)?;
                    insert_file(
                        &mut files,
                        binding.runtime_origin.clone(),
                        transformed.into_bytes(),
                    )?;
                }
            }
        }

        let facade = render_facade_file(
            config,
            module,
            &callables,
            &bindings_by_symbol,
            &declarations,
        )?;
        insert_file(&mut files, facade_path(&module.name)?, facade.into_bytes())?;
    }

    for canonical in &plan.ir.modules {
        let name = canonical.module.as_string();
        if !plan.modules.iter().any(|module| module.name == name) {
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

    Ok(DartEmission {
        files,
        public_symbols,
        unresolved,
    })
}

/// The canonical declaration index paired with the plan's enum projection, so
/// every emission path resolves enum variants through one deterministic map.
#[derive(Clone)]
struct DeclarationIndex<'a> {
    entries: BTreeMap<String, (&'a str, &'a Map<String, Value>)>,
    projection: &'a DartEnumProjection,
}

impl<'a> Deref for DeclarationIndex<'a> {
    type Target = BTreeMap<String, (&'a str, &'a Map<String, Value>)>;

    fn deref(&self) -> &Self::Target {
        &self.entries
    }
}

#[derive(Clone)]
struct EmissionTypeContext<'a> {
    declarations: &'a DeclarationIndex<'a>,
    projections: BTreeMap<String, String>,
    trait_scope: BTreeMap<(String, String), String>,
    named_arguments: BTreeMap<String, Vec<String>>,
}

impl<'a> EmissionTypeContext<'a> {
    fn new(declarations: &'a DeclarationIndex<'a>) -> Self {
        Self {
            declarations,
            projections: BTreeMap::new(),
            trait_scope: BTreeMap::new(),
            named_arguments: BTreeMap::new(),
        }
    }
}

impl DartTypeContext for EmissionTypeContext<'_> {
    fn named_associated_arguments(&self, ty: &Value, name: &str) -> Result<Vec<String>, String> {
        let identity = serde_json::to_string(ty)
            .map_err(|error| format!("serialize contextual Dart type: {error}"))?;
        if let Some(arguments) = self.named_arguments.get(&identity) {
            return Ok(arguments.clone());
        }
        if self
            .declarations
            .get(name)
            .is_some_and(|(kind, _)| *kind == "trait")
        {
            return trait_slot_definitions(ty, self.declarations).map(|slots| {
                slots
                    .iter()
                    .map(|slot| associated_type_name(&slot.trait_name, &slot.slot_name))
                    .collect()
            });
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

#[derive(Clone)]
struct BoundCheck {
    witness: String,
    base: Value,
    bound: Value,
    label: String,
    exact: bool,
}

struct CallableRendering<'a> {
    context: EmissionTypeContext<'a>,
    generics: String,
    associated: Vec<String>,
    associated_parameters: BTreeMap<String, AssociatedParameter>,
    bounds: Vec<BoundCheck>,
}

#[derive(Clone)]
struct OwnerConstWitness {
    name: String,
    ty: String,
}

pub fn implementation_signature(
    plan: &DartPlan,
    callable: &DartCallable,
) -> Result<String, String> {
    implementation_signature_inner(plan, callable)
}

fn implementation_signature_inner(
    plan: &DartPlan,
    callable: &DartCallable,
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
        parameters.push(format!("{} self", escape_identifier(local_name(concrete))?));
    }
    parameters.extend(render_parameters_contextual(
        declaration,
        false,
        &rendering.context,
        &rendering.associated,
        ParameterSurface::Implementation,
    )?);
    parameters.extend(
        owner_witnesses
            .iter()
            .map(|witness| format!("{} {}", witness.ty, witness.name)),
    );
    if callable.owner.is_some() && callable_modifies_state(declaration) {
        parameters.push("cott_runtime.CottStateMutation _cott_mutation".to_owned());
        parameters.push("cott_runtime.CottGuardLease _cott_lease".to_owned());
    }
    let return_type = render_type_contextual(
        required(declaration, "return_type", &callable.symbol)?,
        None,
        Some(&rendering.context),
    )?;
    Ok(format!(
        "{} {}{}({})",
        if callable_kind == "async" {
            format!("Future<{return_type}>")
        } else {
            return_type
        },
        private_callable_name(&callable.symbol)?,
        rendering.generics,
        parameters.join(", "),
    ))
}

#[derive(Clone, Copy)]
enum ParameterSurface {
    Implementation,
    Public,
}

fn render_parameters_contextual(
    declaration: &Map<String, Value>,
    include_defaults: bool,
    context: &EmissionTypeContext<'_>,
    associated: &[String],
    surface: ParameterSurface,
) -> Result<Vec<String>, String> {
    let symbol = declaration
        .get("name")
        .and_then(Value::as_str)
        .unwrap_or("callable");
    let mut positional = Vec::new();
    let mut optional_positional = Vec::new();
    let mut named = Vec::new();
    for parameter in required_array(declaration, "parameters", symbol)? {
        let parameter = parameter
            .as_object()
            .ok_or_else(|| format!("callable `{symbol}` parameter must be an object"))?;
        let name = required_string(parameter, "name", symbol)?;
        let kind = required_string(parameter, "kind", symbol)?;
        let base_type =
            render_type_contextual(required(parameter, "type", symbol)?, None, Some(context))?;
        let ty = match kind {
            "positional" | "keyword_only" => base_type,
            "vararg" => format!("cott_runtime.CottList<{base_type}>"),
            "kwarg" => format!("cott_runtime.CottKeywordArguments<{base_type}>"),
            other => return Err(format!("unsupported canonical parameter kind `{other}`")),
        };
        let has_default = include_defaults
            && parameter
                .get("default")
                .is_some_and(|value| !value.is_null());
        let rendered = if has_default {
            format!("Object? {} = _cott_omitted", escape_identifier(name)?)
        } else {
            format!("{ty} {}", escape_identifier(name)?)
        };
        match (surface, kind, has_default) {
            (ParameterSurface::Public, "keyword_only" | "kwarg", false) => {
                named.push(format!("required {rendered}"));
            }
            (ParameterSurface::Public, "keyword_only" | "kwarg", true) => named.push(rendered),
            (ParameterSurface::Public, "positional", true) => optional_positional.push(rendered),
            _ => positional.push(rendered),
        }
    }
    for generic in declaration
        .get("generics")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter(|generic| generic.get("kind").and_then(Value::as_str) == Some("type"))
    {
        let name = generic
            .get("name")
            .and_then(Value::as_str)
            .ok_or_else(|| format!("callable `{symbol}` type generic is missing name"))?;
        positional.push(format!(
            "cott_runtime.CottType<{}> _cott_type_{}",
            escape_identifier(name)?,
            safe_internal_name(name),
        ));
    }
    for name in associated {
        positional.push(format!(
            "cott_runtime.CottType<{name}> _cott_type_{}",
            safe_internal_name(name),
        ));
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
            .ok_or_else(|| format!("callable `{symbol}` const generic is missing name"))?;
        positional.push(format!(
            "{} _cott_const_{}",
            escape_identifier(name)?,
            safe_internal_name(name),
        ));
    }
    if !optional_positional.is_empty() {
        positional.push(format!("[{}]", optional_positional.join(", ")));
    }
    if !named.is_empty() {
        positional.push(format!("{{{}}}", named.join(", ")));
    }
    Ok(positional)
}

fn bound_requires_existential_projection(
    bound: &Value,
    declarations: &DeclarationIndex<'_>,
) -> Result<bool, String> {
    Ok(is_trait_type(bound, declarations)
        && !trait_slot_definitions(bound, declarations)?.is_empty())
}

fn declaration_type_parameters(
    declaration: &Map<String, Value>,
    declarations: &DeclarationIndex<'_>,
) -> Result<(String, Vec<BoundCheck>), String> {
    let context = EmissionTypeContext::new(declarations);
    let mut parameters = Vec::new();
    let mut checks = Vec::new();
    for generic in required_array(declaration, "generics", "declaration")? {
        let generic = generic
            .as_object()
            .ok_or_else(|| "generic parameter must be an object".to_owned())?;
        let raw_name = required_string(generic, "name", "generic parameter")?;
        let name = escape_identifier(raw_name)?;
        match required_string(generic, "kind", "generic parameter")? {
            "type" => {
                let base = serde_json::json!({"kind": "type_parameter", "name": raw_name});
                let bounds = required_array(generic, "bounds", raw_name)?;
                let mut static_bound = None;
                for bound in bounds {
                    if !bound_requires_existential_projection(bound, declarations)? {
                        static_bound = Some(render_type_contextual(bound, None, Some(&context))?);
                        break;
                    }
                }
                parameters.push(if let Some(bound) = static_bound {
                    format!("{name} extends {bound}")
                } else {
                    name
                });
                for (index, bound) in bounds.iter().enumerate() {
                    checks.push(BoundCheck {
                        witness: format!("_cott_type_{}", safe_internal_name(raw_name)),
                        base: base.clone(),
                        bound: bound.clone(),
                        exact: !bound_requires_existential_projection(bound, declarations)?,
                        label: format!("generic-bound:{raw_name}:{index}"),
                    });
                }
            }
            "const" => parameters.push(format!("{name} extends cott_runtime.CottConst")),
            other => return Err(format!("unsupported generic parameter kind `{other}`")),
        }
    }
    Ok((
        if parameters.is_empty() {
            String::new()
        } else {
            format!("<{}>", parameters.join(", "))
        },
        checks,
    ))
}

fn callable_rendering<'a>(
    declaration: &Map<String, Value>,
    declarations: &'a DeclarationIndex<'a>,
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
            insert_bound_associated_parameters(&base, bound, &mut associated, declarations)?;
        }
    }
    let mut projections = Vec::new();
    collect_associated_projections(&Value::Object(declaration.clone()), &mut projections)?;
    for (base, trait_name, slot_name) in projections {
        if trait_scope.contains_key(&(trait_name.clone(), local_name(&slot_name).to_owned())) {
            continue;
        }
        let parameter = associated_projection_name(&base, &trait_name, &slot_name)?;
        associated.entry(parameter).or_insert(AssociatedParameter {
            base,
            bounds: associated_slot_bounds(&trait_name, &slot_name, declarations)?,
            trait_name,
            slot_name,
        });
    }
    loop {
        let current = associated.values().cloned().collect::<Vec<_>>();
        let before = associated.len();
        for parameter in current {
            let base = associated_parameter_type(&parameter);
            for bound in &parameter.bounds {
                insert_bound_associated_parameters(&base, bound, &mut associated, declarations)?;
            }
        }
        if associated.len() == before {
            break;
        }
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
    let mut checks = Vec::new();
    for generic in required_array(declaration, "generics", "callable")? {
        let generic = generic
            .as_object()
            .ok_or_else(|| "callable generic must be an object".to_owned())?;
        let raw_name = required_string(generic, "name", "callable generic")?;
        let name = escape_identifier(raw_name)?;
        match required_string(generic, "kind", "callable generic")? {
            "type" => {
                let base = serde_json::json!({"kind": "type_parameter", "name": raw_name});
                let bounds = required_array(generic, "bounds", raw_name)?;
                let static_bound = bounds
                    .first()
                    .map(|bound| render_bound_for_base(bound, &base, &context))
                    .transpose()?;
                generic_parts.push(if let Some(bound) = static_bound {
                    format!("{name} extends {bound}")
                } else {
                    name
                });
                checks.extend(bounds.iter().enumerate().map(|(index, bound)| BoundCheck {
                    witness: format!("_cott_type_{}", safe_internal_name(raw_name)),
                    base: base.clone(),
                    bound: bound.clone(),
                    exact: true,
                    label: format!("generic-bound:{raw_name}:{index}"),
                }));
            }
            "const" => generic_parts.push(format!("{name} extends cott_runtime.CottConst")),
            other => {
                return Err(format!(
                    "callable generic `{name}` has unsupported kind `{other}`"
                ));
            }
        }
    }
    for (name, parameter) in &associated {
        let base = associated_parameter_type(parameter);
        let bounds = parameter
            .bounds
            .iter()
            .map(|bound| render_bound_for_base(bound, &base, &context))
            .collect::<Result<Vec<_>, _>>()?;
        generic_parts.push(if let Some(bound) = bounds.first() {
            format!("{name} extends {bound}")
        } else {
            name.clone()
        });
        checks.extend(
            parameter
                .bounds
                .iter()
                .enumerate()
                .map(|(index, bound)| BoundCheck {
                    witness: format!("_cott_type_{}", safe_internal_name(name)),
                    base: base.clone(),
                    bound: bound.clone(),
                    label: format!("associated-bound:{name}:{index}"),
                    exact: true,
                }),
        );
    }
    Ok(CallableRendering {
        associated: associated.keys().cloned().collect(),
        associated_parameters: associated,
        bounds: checks,
        context,
        generics: if generic_parts.is_empty() {
            String::new()
        } else {
            format!("<{}>", generic_parts.join(", "))
        },
    })
}

fn associated_parameter_type(parameter: &AssociatedParameter) -> Value {
    serde_json::json!({
        "kind": "associated_projection",
        "base": parameter.base.clone(),
        "trait": parameter.trait_name.clone(),
        "name": parameter.slot_name.clone(),
    })
}

fn insert_bound_associated_parameters(
    base: &Value,
    bound: &Value,
    associated: &mut BTreeMap<String, AssociatedParameter>,
    declarations: &DeclarationIndex<'_>,
) -> Result<(), String> {
    if !is_trait_type(bound, declarations) {
        return Ok(());
    }
    for slot in trait_slot_definitions(bound, declarations)? {
        let name = associated_projection_name(base, &slot.trait_name, &slot.slot_name)?;
        associated.entry(name).or_insert(AssociatedParameter {
            base: base.clone(),
            trait_name: slot.trait_name,
            slot_name: slot.slot_name,
            bounds: slot.bounds,
        });
    }
    Ok(())
}

fn render_bound_descriptor(
    bound: &Value,
    base: &Value,
    context: &EmissionTypeContext<'_>,
    declarations: &DeclarationIndex<'_>,
    external_types: &BTreeMap<String, String>,
) -> Result<String, String> {
    if is_trait_type(bound, declarations) {
        let object = bound
            .as_object()
            .ok_or_else(|| "trait bound must be an object".to_owned())?;
        let canonical = required_string(object, "name", "trait bound")?;
        let rendered = render_bound_for_base(bound, base, context)?;
        return Ok(format!(
            "cott_runtime.CottTypes.external<{rendered}>({}, (value) => value is {rendered}, identityWitness: {rendered})",
            dart_string(canonical)
        ));
    }
    descriptor_for_contextual(bound, declarations, external_types, context)
}

fn render_bound_checks(
    out: &mut String,
    checks: &[BoundCheck],
    symbol: &str,
    context: &EmissionTypeContext<'_>,
    declarations: &DeclarationIndex<'_>,
    external_types: &BTreeMap<String, String>,
    indent: usize,
) -> Result<(), String> {
    let prefix = " ".repeat(indent);
    for check in checks {
        let condition = if check.exact {
            let expected = render_bound_descriptor(
                &check.bound,
                &check.base,
                context,
                declarations,
                external_types,
            )?;
            format!(
                "({} as cott_runtime.CottType<Object?>).isSubtypeOf(({expected} as cott_runtime.CottType<Object?>))",
                check.witness
            )
        } else {
            let bound = check
                .bound
                .get("name")
                .and_then(Value::as_str)
                .ok_or_else(|| {
                    format!(
                        "existential Dart bound `{}` is not a nominal trait",
                        check.label
                    )
                })?;
            format!(
                "({} as cott_runtime.CottType<Object?>).satisfiesNominal({})",
                check.witness,
                dart_string(bound)
            )
        };
        writeln!(
            out,
            "{prefix}cott_runtime.CottRuntime.requireContract({condition}, {}, clause: {}, expected: 'a descriptor satisfying every Cott bound', actual: ({}).displayName);",
            dart_string(symbol),
            dart_string(&check.label),
            check.witness,
        )
        .expect("writing to String cannot fail");
    }
    Ok(())
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

fn validate_modules(plan: &DartPlan) -> Result<(), String> {
    if plan.modules.is_empty() {
        return Err("canonical Dart plan has no modules".to_owned());
    }
    let mut names = BTreeSet::new();
    let mut prefixes = BTreeMap::<String, String>::new();
    for module in &plan.modules {
        if !names.insert(module.name.as_str()) {
            return Err(format!("duplicate canonical Dart module `{}`", module.name));
        }
        for segment in module.name.split('.') {
            escape_identifier(segment)?;
            if matches!(segment, "cott_runtime" | "cott_impl" | "src" | "modules") {
                return Err(format!(
                    "canonical module `{}` uses reserved Dart path segment `{segment}`",
                    module.name
                ));
            }
        }
        let prefix = module_prefix(&module.name);
        if let Some(previous) = prefixes.insert(prefix.clone(), module.name.clone())
            && previous != module.name
        {
            return Err(format!(
                "canonical Dart modules `{previous}` and `{}` collide at compiler import prefix `{prefix}`",
                module.name
            ));
        }
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
        return Err("Dart plan modules differ from its authoritative canonical IR".to_owned());
    }
    Ok(())
}

fn declaration_index<'a>(plan: &'a DartPlan) -> Result<DeclarationIndex<'a>, String> {
    let mut entries = BTreeMap::new();
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
            if entries
                .insert(name.to_owned(), (kind, declaration))
                .is_some()
            {
                return Err(format!("duplicate canonical declaration identity `{name}`"));
            }
        }
    }
    Ok(DeclarationIndex {
        entries,
        projection: plan.enum_projection(),
    })
}

fn validate_bindings(
    bindings: &[DartBinding],
    callables: &BTreeMap<String, &DartCallable>,
) -> Result<(), String> {
    let mut symbols = BTreeSet::new();
    let mut paths = BTreeSet::new();
    for binding in bindings {
        let callable = callables.get(&binding.cott_symbol).ok_or_else(|| {
            format!(
                "Dart binding `{}` does not match a canonical callable",
                binding.cott_symbol
            )
        })?;
        if !symbols.insert(binding.cott_symbol.as_str()) {
            return Err(format!(
                "duplicate Dart binding for `{}`",
                binding.cott_symbol
            ));
        }
        let expected_runtime = runtime_part_path(callable)?;
        if binding.runtime_origin != expected_runtime
            || !safe_artifact_path(&binding.runtime_origin)
            || binding
                .runtime_origin
                .extension()
                .and_then(|value| value.to_str())
                != Some("dart")
        {
            return Err(format!(
                "Dart binding `{}` runtime origin must be `{}`",
                binding.cott_symbol,
                expected_runtime.display()
            ));
        }
        if !paths.insert(binding.runtime_origin.as_path()) {
            return Err(format!(
                "Dart bindings collide at `{}`",
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
                "Dart binding `{}` has unsafe source origin `{}`",
                binding.cott_symbol,
                binding.source_origin.display()
            ));
        }
        let (_, target_name) = binding.target_symbol.split_once(':').ok_or_else(|| {
            format!(
                "Dart binding `{}` target symbol must be source.dart:privateName",
                binding.cott_symbol
            )
        })?;
        if !target_name.starts_with('_')
            || target_name.starts_with("_cott_") && binding.owner == DartOwner::Manifest
        {
            return Err(format!(
                "Dart binding `{}` has invalid private target `{target_name}`",
                binding.cott_symbol
            ));
        }
        if binding.owner == DartOwner::Agent
            && target_name != private_callable_name(&callable.symbol)?
        {
            return Err(format!(
                "Dart agent binding `{}` target must use `{}`",
                binding.cott_symbol,
                private_callable_name(&callable.symbol)?
            ));
        }
        let expected_hash = format!("sha256:{}", sha256_hex(&binding.bytes));
        if binding.content_hash != expected_hash {
            return Err(format!(
                "Dart binding `{}` content hash does not match its exact authored bytes",
                binding.cott_symbol
            ));
        }
    }
    Ok(())
}

fn required_bindings(callables: &BTreeMap<String, &DartCallable>) -> BTreeSet<String> {
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

fn private_callable_name(symbol: &str) -> Result<String, String> {
    for segment in symbol.split('.') {
        escape_identifier(segment)?;
    }
    Ok(format!("_cott_{}", symbol.replace('.', "_")))
}

fn binding_private_name(binding: &DartBinding) -> Result<&str, String> {
    binding
        .target_symbol
        .split_once(':')
        .map(|(_, name)| name)
        .ok_or_else(|| {
            format!(
                "Dart binding `{}` target symbol is malformed",
                binding.cott_symbol
            )
        })
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
        return Err(format!("unsafe Dart artifact path `{}`", path.display()));
    }
    if files.insert(path.clone(), bytes).is_some() {
        return Err(format!("colliding Dart artifact path `{}`", path.display()));
    }
    Ok(())
}

fn module_file_path(root: &str, module: &str) -> Result<PathBuf, String> {
    let mut path = PathBuf::from(root);
    let segments = module.split('.').collect::<Vec<_>>();
    for segment in &segments[..segments.len().saturating_sub(1)] {
        escape_identifier(segment)?;
        path.push(segment);
    }
    let leaf = segments
        .last()
        .ok_or_else(|| "empty canonical Dart module".to_owned())?;
    escape_identifier(leaf)?;
    path.push(format!("{leaf}.dart"));
    Ok(path)
}

fn types_path(module: &str) -> Result<PathBuf, String> {
    module_file_path("dart/lib/src/types", module)
}

fn facade_path(module: &str) -> Result<PathBuf, String> {
    module_file_path("dart/lib/modules", module)
}

fn implementation_path(canonical: &str) -> Result<PathBuf, String> {
    module_file_path("dart/lib/src/wrappers", canonical)
}

fn wrapper_path(callable: &DartCallable) -> Result<PathBuf, String> {
    module_file_path("dart/lib/src/wrappers", &callable.symbol)
}

fn runtime_part_path(callable: &DartCallable) -> Result<PathBuf, String> {
    module_file_path("dart/lib/src/cott_impl", &callable.symbol)
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

fn package_uri(project: &str, path: &Path) -> Result<String, String> {
    let relative = path
        .strip_prefix("dart/lib/")
        .map_err(|_| format!("Dart library path `{}` is outside dart/lib", path.display()))?;
    let text = relative
        .to_str()
        .ok_or_else(|| format!("Dart library path `{}` is not UTF-8", path.display()))?;
    Ok(format!("package:{project}/{}", text.replace('\\', "/")))
}

fn runtime_import(project: &str) -> String {
    format!("import 'package:{project}/cott_runtime.dart' as cott_runtime;")
}

fn marker_import(project: &str) -> String {
    format!("import 'package:{project}/src/cott_markers.dart' as cott_markers;")
}

fn type_import(project: &str, module: &str) -> Result<String, String> {
    let uri = package_uri(project, &types_path(module)?)?;
    Ok(format!("import '{}' as {};", uri, module_prefix(module)))
}

struct CompilerImport {
    reference: String,
    directive: String,
}

fn common_imports(
    config: &DartProjectConfig,
    plan: &DartPlan,
    current_module: Option<&str>,
    include_markers: bool,
) -> Result<Vec<CompilerImport>, String> {
    let mut imports = vec![CompilerImport {
        reference: "cott_runtime".to_owned(),
        directive: runtime_import(&config.project.name),
    }];
    if include_markers {
        imports.push(CompilerImport {
            reference: "cott_markers".to_owned(),
            directive: marker_import(&config.project.name),
        });
    }
    for module in &plan.modules {
        if current_module == Some(module.name.as_str()) {
            continue;
        }
        imports.push(CompilerImport {
            reference: module_prefix(&module.name),
            directive: type_import(&config.project.name, &module.name)?,
        });
    }
    Ok(imports)
}

fn render_used_imports(imports: &[CompilerImport], sources: &[&str]) -> Result<String, String> {
    let candidates = imports
        .iter()
        .map(|import| import.reference.as_str())
        .collect::<BTreeSet<_>>();
    let references = referenced_dart_identifiers(sources, &candidates)?;
    let mut out = String::new();
    let mut rendered_directives = BTreeSet::new();
    for import in imports {
        if references.contains(import.reference.as_str())
            && rendered_directives.insert(import.directive.as_str())
        {
            writeln!(out, "{}", import.directive).expect("writing to String cannot fail");
        }
    }
    Ok(out)
}

fn referenced_dart_identifiers<'a>(
    sources: &[&str],
    candidates: &BTreeSet<&'a str>,
) -> Result<BTreeSet<&'a str>, String> {
    let mut parser = Parser::new();
    parser
        .set_language(&tree_sitter_dart::LANGUAGE.into())
        .map_err(|error| format!("unable to load Dart syntax grammar: {error}"))?;
    let mut identifiers = BTreeSet::new();
    for source in sources {
        let tree = parser
            .parse(source.as_bytes(), None)
            .ok_or_else(|| "Dart syntax parser returned no tree".to_owned())?;
        if tree.root_node().has_error() {
            return Err(
                "cannot select compiler-owned imports for malformed generated Dart source"
                    .to_owned(),
            );
        }
        collect_referenced_dart_identifiers(tree.root_node(), source, candidates, &mut identifiers);
    }
    Ok(identifiers)
}

fn collect_referenced_dart_identifiers<'a>(
    node: Node<'_>,
    source: &str,
    candidates: &BTreeSet<&'a str>,
    identifiers: &mut BTreeSet<&'a str>,
) {
    // Authored directives are retained verbatim. Only actual identifier tokens
    // outside directives authorize a compiler-owned prefixed import.
    if node.kind() == "import_or_export" {
        return;
    }
    if matches!(node.kind(), "identifier" | "type_identifier")
        && let Some(identifier) = source.get(node.byte_range())
        && let Some(reference) = candidates.get(identifier)
    {
        identifiers.insert(*reference);
    }
    let mut cursor = node.walk();
    for child in node.named_children(&mut cursor) {
        collect_referenced_dart_identifiers(child, source, candidates, identifiers);
    }
}

fn generated_header() -> &'static str {
    "// Generated by Cott. Do not edit.\n"
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

fn render_part(
    config: &DartProjectConfig,
    callable: &DartCallable,
    body: &str,
) -> Result<String, String> {
    let library = if let Some(owner) = callable.owner.as_ref() {
        let canonical = owner
            .get("name")
            .and_then(Value::as_str)
            .ok_or_else(|| format!("callable `{}` owner is missing name", callable.symbol))?;
        implementation_path(canonical)?
    } else {
        wrapper_path(callable)?
    };
    let wrapper = package_uri(&config.project.name, &library)?;
    let mut out = format!("part of '{}';\n", wrapper);
    if !body.starts_with('\n') {
        out.push('\n');
    }
    out.push_str(body);
    Ok(finish_source(out))
}

fn public_target_names(module: &DartModule) -> Result<Vec<String>, String> {
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

fn render_markers(
    config: &DartProjectConfig,
    plan: &DartPlan,
    declarations: &DeclarationIndex<'_>,
) -> Result<String, String> {
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
            if let Some(implementation) = declaration
                .as_object()
                .filter(|value| value.get("kind").and_then(Value::as_str) == Some("impl"))
            {
                for trait_ref in trait_specializations(implementation, declarations)? {
                    trait_tokens.insert(trait_marker(&trait_ref)?, trait_ref);
                }
            }
        }
    }
    let mut out = generated_header().to_owned();
    for (name, value) in constants {
        let parameters = types::const_parameters_in(&value)?;
        let generics = if parameters.is_empty() {
            String::new()
        } else {
            format!(
                "<{}>",
                parameters
                    .iter()
                    .map(|parameter| {
                        escape_identifier(parameter)
                            .map(|name| format!("{name} extends cott_runtime.CottConst"))
                    })
                    .collect::<Result<Vec<_>, _>>()?
                    .join(", ")
            )
        };
        let fields = parameters
            .iter()
            .map(|parameter| {
                Ok(format!(
                    "final {} _cott_const_{};",
                    escape_identifier(parameter)?,
                    safe_internal_name(parameter)
                ))
            })
            .collect::<Result<Vec<_>, String>>()?;
        let constructor = if parameters.is_empty() {
            format!("const {name}();")
        } else {
            format!(
                "const {name}({});",
                parameters
                    .iter()
                    .map(|parameter| format!("this._cott_const_{}", safe_internal_name(parameter)))
                    .collect::<Vec<_>>()
                    .join(", ")
            )
        };
        writeln!(
            out,
            "\nfinal class {name}{generics} implements cott_runtime.CottConst {{"
        )
        .expect("writing to String cannot fail");
        for field in fields {
            writeln!(out, "  {field}").expect("writing to String cannot fail");
        }
        writeln!(
            out,
            "  {constructor}\n  @override\n  BigInt get value => {};\n}}",
            render_const_value(&value)?
        )
        .expect("writing to String cannot fail");
    }
    for tag in opaques {
        let name = types::opaque_marker(&tag);
        writeln!(
            out,
            "\nfinal class {name} implements cott_runtime.CottOpaqueTag {{\n  const {name}();\n  @override\n  String get tag => {};\n}}",
            dart_string(&tag)
        )
        .expect("writing to String cannot fail");
    }
    for (name, trait_ref) in trait_tokens {
        let object = trait_ref
            .as_object()
            .ok_or_else(|| "Dyn trait specialization must be an object".to_owned())?;
        let canonical = serde_json::to_string(&trait_ref)
            .map_err(|error| format!("serialize Dyn trait identity: {error}"))?;
        let trait_name = required_string(object, "name", "Dyn trait")?;
        let rendered = render_existential_trait_reference(&trait_ref, declarations)?;
        writeln!(
            out,
            "\nfinal cott_runtime.CottTrait<{rendered}> {name} = cott_runtime.CottTrait<{rendered}>.checked({}, (value) => value is {rendered});",
            dart_string(&canonical)
        )
        .expect("writing to String cannot fail");
        let _ = trait_name;
    }
    for arity in tuple_arities {
        render_tuple_marker(&mut out, arity);
    }
    let imports = common_imports(config, plan, None, false)?;
    let imports = render_used_imports(&imports, &[out.as_str()])?;
    out.insert_str(generated_header().len(), &imports);
    let _ = declarations;
    Ok(finish_source(out))
}

fn render_existential_trait_reference(
    trait_ref: &Value,
    declarations: &DeclarationIndex<'_>,
) -> Result<String, String> {
    let object = trait_ref
        .as_object()
        .ok_or_else(|| "trait specialization must be an object".to_owned())?;
    let name = required_string(object, "name", "trait specialization")?;
    let identity = serde_json::to_string(trait_ref)
        .map_err(|error| format!("serialize trait specialization: {error}"))?;
    let mut context = EmissionTypeContext::new(declarations);
    context.named_arguments.insert(
        identity,
        trait_slot_definitions(trait_ref, declarations)?
            .iter()
            .map(|_| "dynamic".to_owned())
            .collect(),
    );
    let rendered = render_type_contextual(trait_ref, None, Some(&context))?;
    if !is_trait_type(trait_ref, declarations) {
        return Err(format!("trait specialization `{name}` is not a trait"));
    }
    Ok(rendered)
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
                        constants.insert(types::const_marker(value)?, value.clone());
                    }
                }
                Some("array" | "buffer") if object.contains_key("length") => {
                    let value = required(object, "length", "fixed container type")?;
                    if value.get("kind").and_then(Value::as_str) != Some("parameter") {
                        constants.insert(types::const_marker(value)?, value.clone());
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
            for child in object.values() {
                collect_markers(child, constants, opaques, trait_tokens, tuple_arities)?;
            }
        }
        _ => {}
    }
    Ok(())
}
fn module_marker_exports(module: &DartModule) -> Result<Vec<String>, String> {
    let mut constants = BTreeMap::<String, Value>::new();
    let mut opaques = BTreeSet::<String>::new();
    let mut trait_tokens = BTreeMap::<String, Value>::new();
    let mut tuple_arities = BTreeSet::<usize>::new();
    for declaration in &module.declarations {
        collect_markers(
            declaration,
            &mut constants,
            &mut opaques,
            &mut trait_tokens,
            &mut tuple_arities,
        )?;
    }
    let mut names = constants.into_keys().collect::<BTreeSet<_>>();
    names.extend(opaques.into_iter().map(|tag| types::opaque_marker(&tag)));
    names.extend(trait_tokens.into_keys());
    names.extend(
        tuple_arities
            .into_iter()
            .map(|arity| format!("CottTuple{arity}")),
    );
    Ok(names.into_iter().collect())
}

fn render_tuple_marker(out: &mut String, arity: usize) {
    if arity == 0 {
        out.push_str(
            "\nfinal class CottTuple0 implements cott_runtime.CottTupleValue {\n  CottTuple0();\n  @override\n  cott_runtime.CottList<Object?> get cottTupleElements => cott_runtime.CottList([]);\n  @override\n  CottTuple0 cottRebuild(cott_runtime.CottList<Object?> elements) {\n    if (elements.isNotEmpty) cott_runtime.CottRuntime.violation('tuple arity changed during ABI adaptation', phase: 'validation', expected: '0', actual: '${elements.length}');\n    return CottTuple0();\n  }\n}\n",
        );
        return;
    }
    let generics = (0..arity)
        .map(|index| format!("T{index}"))
        .collect::<Vec<_>>();
    let fields = (0..arity)
        .map(|index| format!("final T{index} item{index};"))
        .collect::<Vec<_>>();
    let parameters = (0..arity)
        .map(|index| format!("this.item{index}"))
        .collect::<Vec<_>>();
    let values = (0..arity)
        .map(|index| format!("item{index}"))
        .collect::<Vec<_>>();
    let casts = (0..arity)
        .map(|index| format!("elements[{index}] as T{index}"))
        .collect::<Vec<_>>();
    writeln!(
        out,
        "\nfinal class CottTuple{arity}<{}> implements cott_runtime.CottTupleValue {{\n  {}\n  CottTuple{arity}({});\n  @override\n  cott_runtime.CottList<Object?> get cottTupleElements => cott_runtime.CottList([{}]);\n  @override\n  CottTuple{arity}<{}> cottRebuild(cott_runtime.CottList<Object?> elements) {{\n    if (elements.length != {arity}) cott_runtime.CottRuntime.violation('tuple arity changed during ABI adaptation', phase: 'validation', expected: '{arity}', actual: '${{elements.length}}');\n    return CottTuple{arity}<{}>({});\n  }}\n}}",
        generics.join(", "),
        fields.join("\n  "),
        parameters.join(", "),
        values.join(", "),
        generics.join(", "),
        generics.join(", "),
        casts.join(", "),
    )
    .expect("writing to String cannot fail");
}

fn render_types_file(
    config: &DartProjectConfig,
    plan: &DartPlan,
    module: &DartModule,
    declarations: &DeclarationIndex<'_>,
    bindings: &BTreeMap<&str, &DartBinding>,
) -> Result<String, String> {
    let mut out = generated_header().to_owned();
    let mut compiler_imports = common_imports(config, plan, Some(&module.name), true)?;
    for declaration in module
        .declarations
        .iter()
        .filter_map(Value::as_object)
        .filter(|declaration| {
            declaration.get("kind").and_then(Value::as_str) == Some("external_type")
        })
    {
        let canonical = required_string(declaration, "name", &module.name)?;
        let projection = config.dart.external_types.get(canonical).ok_or_else(|| {
            format!("external Dart type `{canonical}` has no configured projection")
        })?;
        let (uri, ty) = parse_external_projection(projection)?;
        let index = config
            .dart
            .external_types
            .values()
            .position(|candidate| candidate == projection)
            .expect("configured external projection");
        compiler_imports.push(if uri == "dart:core" {
            CompilerImport {
                reference: ty.to_owned(),
                directive: "import 'dart:core';".to_owned(),
            }
        } else {
            CompilerImport {
                reference: format!("_cott_external_{index}"),
                directive: format!(
                    "import '{}' as _cott_external_{index};",
                    uri.replace('\'', "%27")
                ),
            }
        });
    }
    for implementation in module
        .declarations
        .iter()
        .filter_map(Value::as_object)
        .filter(|declaration| {
            declaration.get("kind").and_then(Value::as_str) == Some("impl")
                && declaration
                    .get("name")
                    .and_then(Value::as_str)
                    .is_some_and(|name| implementation_resolved(name, declaration, bindings))
        })
    {
        let canonical = required_string(implementation, "name", &module.name)?;
        let name = escape_identifier(local_name(canonical))?;
        let uri = package_uri(&config.project.name, &implementation_path(canonical)?)?;
        compiler_imports.push(CompilerImport {
            reference: name.clone(),
            directive: format!("import '{uri}' show {name};"),
        });
        if implementation.get("public").and_then(Value::as_bool) == Some(true) {
            writeln!(out, "export '{uri}' show {name};").expect("writing to String cannot fail");
        }
    }
    if module.declarations.iter().any(|declaration| {
        type_declaration_has_defaults(declaration)
            || declaration.get("kind").and_then(Value::as_str) == Some("struct")
    }) {
        out.push_str(
            "\nenum _cott_omission { value }\nconst _cott_omitted = _cott_omission.value;\n",
        );
    }
    if module.declarations.iter().any(|declaration| {
        matches!(
            declaration.get("kind").and_then(Value::as_str),
            Some("newtype" | "struct" | "enum")
        ) && declaration
            .get("generics")
            .and_then(Value::as_array)
            .is_some_and(|generics| {
                generics
                    .iter()
                    .any(|generic| generic.get("kind").and_then(Value::as_str) == Some("type"))
            })
    }) {
        render_private_carrier(&mut out, &module.name)?;
    }
    if module.declarations.iter().any(|declaration| {
        declaration
            .get("name")
            .and_then(Value::as_str)
            .is_some_and(|name| declarations.projection.is_native(name))
    }) {
        out.push_str(
            "\nfinal cott_runtime.CottList<String> _cott_no_field_names = cott_runtime.CottList(const <String>[]);\nfinal cott_runtime.CottList<Object?> _cott_no_payload = cott_runtime.CottList(const <Object?>[]);\n",
        );
    }
    for declaration in &module.declarations {
        let object = declaration
            .as_object()
            .ok_or_else(|| format!("declaration in `{}` must be an object", module.name))?;
        let kind = required_string(object, "kind", &module.name)?;
        // Scenarios and requirements have no Dart ABI symbol; requirements are report metadata.
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
            "newtype" => render_newtype(&mut out, config, object, declarations)?,
            "struct" => render_struct(&mut out, config, object, declarations)?,
            "enum" => render_enum(&mut out, config, object, declarations)?,
            "trait" => render_trait(&mut out, object, declarations)?,
            "rule" => render_rule(&mut out, object, declarations)?,
            "resource" => render_resource(&mut out, object)?,
            "const" => render_const(&mut out, object, declarations)?,
            other => {
                return Err(format!("unsupported Dart type declaration kind `{other}`"));
            }
        }
    }
    let imports = render_used_imports(&compiler_imports, &[out.as_str()])?;
    out.insert_str(generated_header().len(), &imports);
    Ok(finish_source(out))
}

fn render_private_carrier(out: &mut String, module: &str) -> Result<(), String> {
    let name = format!("_cott_carrier_{}", &sha256_hex(module.as_bytes())[..16]);
    writeln!(
        out,
        "\nfinal class {name} implements cott_runtime.CottNominalCarrier {{\n  {name}(this._cott_view, this._cott_rebuild);\n  final cott_runtime.CottFieldValue _cott_view;\n  final cott_runtime.CottFieldValue Function(cott_runtime.CottList<Object?>) _cott_rebuild;\n  @override\n  String get cottGenericIdentity => (_cott_view as cott_runtime.CottGenericValue).cottGenericIdentity;\n  @override\n  cott_runtime.CottList<cott_runtime.CottType<Object?>> get cottTypeArguments => (_cott_view as cott_runtime.CottGenericValue).cottTypeArguments;\n  @override\n  String get cottTypeIdentity => _cott_view.cottTypeIdentity;\n  @override\n  cott_runtime.CottList<String> get cottFieldNames => _cott_view.cottFieldNames;\n  @override\n  Object? cottField(String name) => _cott_view.cottField(name);\n  @override\n  cott_runtime.CottNominalCarrier cottRebuildCarrier(cott_runtime.CottList<Object?> fields) => {name}(_cott_rebuild(fields), _cott_rebuild);\n}}"
    )
    .expect("writing to String cannot fail");
    Ok(())
}

fn parse_external_projection(value: &str) -> Result<(&str, &str), String> {
    let (uri, ty) = value
        .split_once('#')
        .ok_or_else(|| format!("Dart external projection `{value}` must be URI#Type"))?;
    if uri.is_empty() || ty.is_empty() || value.matches('#').count() != 1 {
        return Err(format!("invalid Dart external projection `{value}`"));
    }
    escape_identifier(ty)?;
    Ok((uri, ty))
}

fn render_external(
    out: &mut String,
    config: &DartProjectConfig,
    declaration: &Map<String, Value>,
) -> Result<(), String> {
    let canonical = required_string(declaration, "name", "external type")?;
    let target =
        config.dart.external_types.get(canonical).ok_or_else(|| {
            format!("external Dart type `{canonical}` has no configured projection")
        })?;
    let (uri, ty) = parse_external_projection(target)?;
    let target = if uri == "dart:core" {
        escape_identifier(ty)?
    } else {
        let index = config
            .dart
            .external_types
            .values()
            .position(|candidate| candidate == target)
            .expect("configured external projection");
        format!("_cott_external_{index}.{}", escape_identifier(ty)?)
    };
    writeln!(
        out,
        "\ntypedef {} = {target};",
        escape_identifier(local_name(canonical))?,
    )
    .expect("writing to String cannot fail");
    Ok(())
}

fn render_alias(
    out: &mut String,
    declaration: &Map<String, Value>,
    declarations: &DeclarationIndex<'_>,
) -> Result<(), String> {
    let canonical = required_string(declaration, "name", "alias")?;
    let (generics, _) = declaration_type_parameters(declaration, declarations)?;
    let target = render_contextual_type(
        required(declaration, "target", canonical)?,
        module_of(canonical),
        declarations,
    )?;
    writeln!(
        out,
        "\ntypedef {}{generics} = {target};",
        escape_identifier(local_name(canonical))?
    )
    .expect("writing to String cannot fail");
    Ok(())
}

fn render_newtype(
    out: &mut String,
    config: &DartProjectConfig,
    declaration: &Map<String, Value>,
    declarations: &DeclarationIndex<'_>,
) -> Result<(), String> {
    let canonical = required_string(declaration, "name", "newtype")?;
    let module = module_of(canonical);
    let name = escape_identifier(local_name(canonical))?;
    let (generics, extra_bounds) = declaration_type_parameters(declaration, declarations)?;
    let carrier_value = required(declaration, "carrier", canonical)?;
    let carrier = render_contextual_type(carrier_value, module, declarations)?;
    let witness_fields = const_witness_fields(declaration)?;
    let type_witnesses = type_witness_fields(declaration)?;
    writeln!(
        out,
        "\nfinal class {name}{generics} implements cott_runtime.CottFieldValue{} {{\n  final {carrier} value;",
        if type_witnesses.is_empty() {
            ""
        } else {
            ", cott_runtime.CottGenericValue, cott_runtime.CottCheckedView"
        }
    )
    .expect("writing to String cannot fail");
    for witness in &type_witnesses {
        writeln!(out, "  final {} {};", witness.ty, witness.public_name)
            .expect("writing to String cannot fail");
    }
    for witness in &witness_fields {
        writeln!(out, "  final {} {};", witness.ty, witness.public_name)
            .expect("writing to String cannot fail");
    }
    let positional = type_witnesses
        .iter()
        .map(|witness| {
            format!(
                "{} _cott_type_{}",
                witness.ty,
                safe_internal_name(&witness.generic)
            )
        })
        .collect::<Vec<_>>();
    let type_initializers = type_witnesses
        .iter()
        .map(|witness| {
            format!(
                "{} = _cott_type_{}",
                witness.public_name,
                safe_internal_name(&witness.generic)
            )
        })
        .collect::<Vec<_>>();
    let mut named = vec!["required this.value".to_owned()];
    named.extend(
        witness_fields
            .iter()
            .map(|witness| format!("required this.{}", witness.public_name)),
    );
    let constructor = if positional.is_empty() {
        format!("{{{}}}", named.join(", "))
    } else {
        format!("{}, {{{}}}", positional.join(", "), named.join(", "))
    };
    writeln!(
        out,
        "\n  {name}({constructor}){} {{",
        if type_initializers.is_empty() {
            String::new()
        } else {
            format!(" : {}", type_initializers.join(", "))
        }
    )
    .expect("writing to String cannot fail");
    render_identity_preflight(out, config, 4);
    writeln!(
        out,
        "    cott_runtime.CottRuntime.abi(value, {}, mode: {}, path: r'$.value');",
        descriptor_for_nominal(
            carrier_value,
            declaration,
            declarations,
            &config.dart.external_types
        )?,
        "cott_runtime.RuntimeValidation.boundary"
    )
    .expect("writing to String cannot fail");
    render_bound_checks(
        out,
        &constructor_bound_checks(&extra_bounds, &type_witnesses)?,
        canonical,
        &EmissionTypeContext::new(declarations),
        declarations,
        &config.dart.external_types,
        4,
    )?;
    render_const_witness_validation(out, declaration, &witness_fields, 4)?;
    if let Some(refinement) = declaration
        .get("refinement")
        .filter(|value| !value.is_null())
    {
        let mut refinement = refinement.clone();
        rewrite_refinement_receiver(&mut refinement);
        rewrite_const_references(&mut refinement, declaration, &witness_fields);
        let condition = render_condition(&refinement, None, true, module, declarations.projection)?;
        writeln!(
            out,
            "    final _cott_result = value;\n    cott_runtime.CottRuntime.checkContract({condition}, {}, 'refinement', clause: 'refinement', span: {}, expected: 'true', actual: 'false');",
            dart_string(canonical),
            render_span(refinement.get("span"))?
        )
        .expect("writing to String cannot fail");
    }
    writeln!(
        out,
        "  }}\n\n  @override\n  String get cottTypeIdentity => {};\n  @override\n  cott_runtime.CottList<String> get cottFieldNames => cott_runtime.CottList(['value']);\n  @override\n  Object? cottField(String name) => switch (name) {{\n    'value' => value,\n    _ => cott_runtime.CottRuntime.violation('unknown canonical field', symbol: cottTypeIdentity, phase: 'field', actual: name),\n  }};\n\n  @override\n  bool operator ==(Object other) => other is {name} && cott_runtime.CottRuntime.canonicalEqual(value, other.value);\n  @override\n  int get hashCode => cott_runtime.CottRuntime.deepHash(value);",
        dart_string(canonical)
    )
    .expect("writing to String cannot fail");
    render_generic_metadata(out, canonical, &type_witnesses, 2)?;
    render_nominal_carrier_methods(
        out,
        &name,
        declaration,
        &[("value".to_owned(), carrier_value.clone())],
        &type_witnesses,
        &witness_fields,
        module,
        declarations,
        &config.dart.external_types,
        2,
    )?;
    writeln!(out, "}}").expect("writing to String cannot fail");
    Ok(())
}

struct WitnessField {
    generic: String,
    ty: String,
    public_name: String,
}

fn type_witness_fields(declaration: &Map<String, Value>) -> Result<Vec<WitnessField>, String> {
    required_array(declaration, "generics", "declaration")?
        .iter()
        .filter(|generic| generic.get("kind").and_then(Value::as_str) == Some("type"))
        .map(|generic| {
            let name = generic
                .get("name")
                .and_then(Value::as_str)
                .ok_or_else(|| "type generic is missing name".to_owned())?;
            Ok(WitnessField {
                generic: name.to_owned(),
                ty: format!("cott_runtime.CottType<{}>", escape_identifier(name)?),
                public_name: format!("cottType{}", pascal_identifier(name)?),
            })
        })
        .collect()
}

fn constructor_bound_checks(
    checks: &[BoundCheck],
    witnesses: &[WitnessField],
) -> Result<Vec<BoundCheck>, String> {
    checks
        .iter()
        .cloned()
        .map(|mut check| {
            let generic = check
                .base
                .get("name")
                .and_then(Value::as_str)
                .ok_or_else(|| {
                    format!("declaration bound `{}` has no type parameter", check.label)
                })?;
            check.witness = witnesses
                .iter()
                .find(|witness| witness.generic == generic)
                .map(|witness| witness.public_name.clone())
                .ok_or_else(|| {
                    format!(
                        "declaration bound `{}` has no explicit type witness",
                        check.label
                    )
                })?;
            Ok(check)
        })
        .collect()
}

fn render_generic_metadata(
    out: &mut String,
    canonical: &str,
    witnesses: &[WitnessField],
    indent: usize,
) -> Result<(), String> {
    if witnesses.is_empty() {
        return Ok(());
    }
    let prefix = " ".repeat(indent);
    writeln!(
        out,
        "\n{prefix}@override\n{prefix}String get cottGenericIdentity => {};",
        dart_string(canonical)
    )
    .expect("writing to String cannot fail");
    writeln!(
        out,
        "{prefix}@override\n{prefix}cott_runtime.CottList<cott_runtime.CottType<Object?>> get cottTypeArguments => cott_runtime.CottList([{}]);",
        witnesses
            .iter()
            .map(|witness| format!("({} as cott_runtime.CottType<Object?>)", witness.public_name))
            .collect::<Vec<_>>()
            .join(", ")
    )
    .expect("writing to String cannot fail");
    Ok(())
}
fn descriptor_for_constructor(
    ty: &Value,
    declaration: &Map<String, Value>,
    witnesses: &[WitnessField],
    declarations: &DeclarationIndex<'_>,
    external_types: &BTreeMap<String, String>,
) -> Result<String, String> {
    let mut descriptor = descriptor_for_nominal(ty, declaration, declarations, external_types)?;
    for witness in witnesses {
        descriptor = descriptor.replace(
            &witness.public_name,
            &format!("_cott_type_{}", safe_internal_name(&witness.generic)),
        );
    }
    Ok(descriptor)
}

fn const_witness_fields(declaration: &Map<String, Value>) -> Result<Vec<WitnessField>, String> {
    required_array(declaration, "generics", "declaration")?
        .iter()
        .filter(|generic| generic.get("kind").and_then(Value::as_str) == Some("const"))
        .map(|generic| {
            let name = generic
                .get("name")
                .and_then(Value::as_str)
                .ok_or_else(|| "const generic is missing name".to_owned())?;
            Ok(WitnessField {
                generic: name.to_owned(),
                ty: escape_identifier(name)?,
                public_name: format!("cottConst{}", pascal_identifier(name)?),
            })
        })
        .collect()
}

fn render_plain_nominal_type_factory(
    out: &mut String,
    class_name: &str,
    declaration: &Map<String, Value>,
    fields: &[(String, Value)],
    const_witnesses: &[WitnessField],
    module: Option<&str>,
    declarations: &DeclarationIndex<'_>,
    external_types: &BTreeMap<String, String>,
    indent: usize,
) -> Result<(), String> {
    let canonical = required_string(declaration, "name", class_name)?;
    let module = module.ok_or_else(|| format!("nominal `{class_name}` has no canonical module"))?;
    let prefix = " ".repeat(indent);
    let (method_generics, bound_checks) = declaration_type_parameters(declaration, declarations)?;
    let applied_names = generic_names(declaration)?;
    let applied = if applied_names.is_empty() {
        class_name.to_owned()
    } else {
        format!("{class_name}<{}>", applied_names.join(", "))
    };
    let parameters = const_witnesses
        .iter()
        .map(|witness| {
            format!(
                "{} _cott_const_{}",
                witness.ty,
                safe_internal_name(&witness.generic)
            )
        })
        .collect::<Vec<_>>();
    let mut named = fields
        .iter()
        .enumerate()
        .map(|(index, (name, ty))| {
            Ok(format!(
                "{}: fields[{index}] as {}",
                escape_identifier(name)?,
                render_contextual_type(ty, Some(module), declarations)?
            ))
        })
        .collect::<Result<Vec<_>, String>>()?;
    named.extend(const_witnesses.iter().map(|witness| {
        format!(
            "{}: _cott_const_{}",
            witness.public_name,
            safe_internal_name(&witness.generic)
        )
    }));
    let rebuild = render_constructor_invocation(&applied, &[], &named);
    let descriptor_fields = fields
        .iter()
        .map(|(name, ty)| {
            let mut descriptor = descriptor_for_contextual(
                ty,
                declarations,
                external_types,
                &EmissionTypeContext::new(declarations),
            )?;
            descriptor =
                descriptor.replace(&format!("{}.", module_prefix(module)), "");
            Ok(format!(
                "cott_runtime.CottNominalField<{applied}>({}, ({} as cott_runtime.CottType<Object?>), (value) => value.{})",
                dart_string(name),
                descriptor,
                escape_identifier(name)?
            ))
        })
        .collect::<Result<Vec<_>, String>>()?;
    let descriptor = format!(
        "cott_runtime.CottTypes.deferred<{applied}>({}, () => cott_runtime.CottTypes.nominal<{applied}>({}, {applied}, [{}], (fields) => {rebuild}))",
        dart_string(canonical),
        dart_string(canonical),
        descriptor_fields.join(", "),
    );
    if required_array(declaration, "generics", canonical)?.is_empty() {
        writeln!(
            out,
            "\n{prefix}static final cott_runtime.CottType<{applied}> cottType = {descriptor};"
        )
        .expect("writing to String cannot fail");
        return Ok(());
    }
    writeln!(
        out,
        "\n{prefix}static cott_runtime.CottType<{applied}> cottType{method_generics}({}) {{",
        parameters.join(", ")
    )
    .expect("writing to String cannot fail");
    render_bound_checks(
        out,
        &bound_checks,
        canonical,
        &EmissionTypeContext::new(declarations),
        declarations,
        external_types,
        indent + 2,
    )?;
    render_const_witness_validation(out, declaration, const_witnesses, indent + 2)?;
    writeln!(out, "{prefix}  return {descriptor};\n{prefix}}}")
        .expect("writing to String cannot fail");
    Ok(())
}

fn render_nominal_carrier_methods(
    out: &mut String,
    class_name: &str,
    declaration: &Map<String, Value>,
    fields: &[(String, Value)],
    type_witnesses: &[WitnessField],
    const_witnesses: &[WitnessField],
    module: Option<&str>,
    declarations: &DeclarationIndex<'_>,
    external_types: &BTreeMap<String, String>,
    indent: usize,
) -> Result<(), String> {
    if type_witnesses.is_empty() {
        return render_plain_nominal_type_factory(
            out,
            class_name,
            declaration,
            fields,
            const_witnesses,
            module,
            declarations,
            external_types,
            indent,
        );
    }
    let prefix = " ".repeat(indent);
    let positional = type_witnesses
        .iter()
        .map(|witness| witness.public_name.clone())
        .collect::<Vec<_>>();
    let mut named = fields
        .iter()
        .enumerate()
        .map(|(index, (name, ty))| {
            Ok(format!(
                "{}: fields[{index}] as {}",
                escape_identifier(name)?,
                render_contextual_type(ty, module, declarations)?
            ))
        })
        .collect::<Result<Vec<_>, String>>()?;
    named.extend(
        const_witnesses
            .iter()
            .map(|witness| format!("{}: {}", witness.public_name, witness.public_name)),
    );
    let construction = render_constructor_invocation(class_name, &positional, &named);
    let module =
        module.ok_or_else(|| format!("generic nominal `{class_name}` has no canonical module"))?;
    let carrier = format!("_cott_carrier_{}", &sha256_hex(module.as_bytes())[..16]);
    writeln!(
        out,
        "\n{prefix}static final Object _cott_view_seal = Object();\n{prefix}@override\n{prefix}cott_runtime.CottNominalCarrier cottCarrier(cott_runtime.CottViewAccess access) {{\n{prefix}  if (!access.allows(_cott_view_seal)) {{\n{prefix}    cott_runtime.CottRuntime.violation('invalid checked-view access', phase: 'validation');\n{prefix}  }}\n{prefix}  return {carrier}(this, (fields) => {construction});\n{prefix}}}"
    )
    .expect("writing to String cannot fail");
    let canonical = required_string(declaration, "name", class_name)?;
    let (method_generics, bound_checks) = declaration_type_parameters(declaration, declarations)?;
    let applied_names = generic_names(declaration)?;
    let applied = if applied_names.is_empty() {
        class_name.to_owned()
    } else {
        format!("{class_name}<{}>", applied_names.join(", "))
    };
    let mut parameters = type_witnesses
        .iter()
        .map(|witness| {
            format!(
                "{} _cott_type_{}",
                witness.ty,
                safe_internal_name(&witness.generic)
            )
        })
        .collect::<Vec<_>>();
    parameters.extend(const_witnesses.iter().map(|witness| {
        format!(
            "{} _cott_const_{}",
            witness.ty,
            safe_internal_name(&witness.generic)
        )
    }));
    let expected_witnesses = type_witnesses
        .iter()
        .enumerate()
        .map(|(index, witness)| format!("expectedArguments[{index}] as {}", witness.ty))
        .collect::<Vec<_>>();
    let mut build_named = fields
        .iter()
        .map(|(name, ty)| {
            Ok(format!(
                "{}: carrier.cottField({}) as {}",
                escape_identifier(name)?,
                dart_string(name),
                render_contextual_type(ty, Some(module), declarations)?
            ))
        })
        .collect::<Result<Vec<_>, String>>()?;
    build_named.extend(const_witnesses.iter().map(|witness| {
        format!(
            "{}: _cott_const_{}",
            witness.public_name,
            safe_internal_name(&witness.generic)
        )
    }));
    let build = render_constructor_invocation(&applied, &expected_witnesses, &build_named);
    let arguments = type_witnesses
        .iter()
        .map(|witness| {
            format!(
                "(_cott_type_{} as cott_runtime.CottType<Object?>)",
                safe_internal_name(&witness.generic)
            )
        })
        .collect::<Vec<_>>();
    let variances = required_array(declaration, "generics", canonical)?
        .iter()
        .filter(|generic| generic.get("kind").and_then(Value::as_str) == Some("type"))
        .map(|generic| {
            match generic
                .get("variance")
                .and_then(Value::as_str)
                .unwrap_or("invariant")
            {
                "invariant" => Ok("cott_runtime.CottVariance.invariant"),
                "covariant" => Ok("cott_runtime.CottVariance.covariant"),
                "contravariant" => Ok("cott_runtime.CottVariance.contravariant"),
                other => Err(format!(
                    "unsupported Cott variance `{other}` on `{canonical}`"
                )),
            }
        })
        .collect::<Result<Vec<_>, String>>()?;
    let descriptor_fields = fields
        .iter()
        .map(|(name, ty)| {
            let mut descriptor = descriptor_for_contextual(
                ty,
                declarations,
                external_types,
                &EmissionTypeContext::new(declarations),
            )?;
            descriptor = descriptor.replace(
                &format!("{}.", module_prefix(module)),
                "",
            );
            Ok(format!(
                "cott_runtime.CottNominalField<cott_runtime.CottNominalCarrier>({}, ({} as cott_runtime.CottType<Object?>), (carrier) => carrier.cottField({}))",
                dart_string(name),
                descriptor,
                dart_string(name)
            ))
        })
        .collect::<Result<Vec<_>, String>>()?;
    writeln!(
        out,
        "\n{prefix}static cott_runtime.CottType<{applied}> cottType{method_generics}({}) {{",
        parameters.join(", "),
    )
    .expect("writing to String cannot fail");
    render_bound_checks(
        out,
        &bound_checks,
        canonical,
        &EmissionTypeContext::new(declarations),
        declarations,
        external_types,
        indent + 2,
    )?;
    writeln!(
        out,
        "{prefix}  return cott_runtime.CottTypes.deferred<{applied}>({}, () => cott_runtime.CottTypes.checkedNominal<{applied}>({}, [{}], (carrier) => carrier.cottGenericIdentity == {}, (carrier, expectedArguments) => {build}, acceptsView: (value) => value is {class_name}, viewSeal: _cott_view_seal, arguments: [{}], variances: [{}]));\n{prefix}}}",
        dart_string(canonical),
        dart_string(canonical),
        descriptor_fields.join(", "),
        dart_string(canonical),
        arguments.join(", "),
        variances.join(", ")
    )
    .expect("writing to String cannot fail");
    Ok(())
}

fn pascal_identifier(name: &str) -> Result<String, String> {
    escape_identifier(name)?;
    let mut chars = name.chars();
    let first = chars
        .next()
        .ok_or_else(|| "empty Dart identifier".to_owned())?;
    Ok(first.to_ascii_uppercase().to_string() + chars.as_str())
}

fn render_struct(
    out: &mut String,
    config: &DartProjectConfig,
    declaration: &Map<String, Value>,
    declarations: &DeclarationIndex<'_>,
) -> Result<(), String> {
    let canonical = required_string(declaration, "name", "struct")?;
    let module = module_of(canonical);
    let name = escape_identifier(local_name(canonical))?;
    let (generics, extra_bounds) = declaration_type_parameters(declaration, declarations)?;
    let fields = required_array(declaration, "fields", canonical)?;
    let witnesses = const_witness_fields(declaration)?;
    let type_witnesses = type_witness_fields(declaration)?;
    writeln!(
        out,
        "\nfinal class {name}{generics} implements cott_runtime.CottFieldValue{} {{",
        if type_witnesses.is_empty() {
            ""
        } else {
            ", cott_runtime.CottGenericValue, cott_runtime.CottCheckedView"
        }
    )
    .expect("writing to String cannot fail");
    for field in fields {
        let field = field
            .as_object()
            .ok_or_else(|| format!("struct `{canonical}` field must be an object"))?;
        writeln!(
            out,
            "  final {} {};",
            render_contextual_type(required(field, "type", canonical)?, module, declarations)?,
            escape_identifier(required_string(field, "name", canonical)?)?
        )
        .expect("writing to String cannot fail");
    }
    for witness in &type_witnesses {
        writeln!(out, "  final {} {};", witness.ty, witness.public_name)
            .expect("writing to String cannot fail");
    }
    for witness in &witnesses {
        writeln!(out, "  final {} {};", witness.ty, witness.public_name)
            .expect("writing to String cannot fail");
    }
    let mut parameters = Vec::new();
    let mut default_initializers = Vec::new();
    for field in fields {
        let field = field.as_object().expect("validated struct field");
        let field_name = required_string(field, "name", canonical)?;
        let escaped = escape_identifier(field_name)?;
        if let Some(default) = field.get("default").filter(|value| !value.is_null()) {
            parameters.push(format!("Object? {escaped} = _cott_omitted"));
            default_initializers.push(format!(
                "{escaped} = cott_runtime.CottRuntime.abi(identical({escaped}, _cott_omitted) ? {} : {escaped}, {}, mode: cott_runtime.RuntimeValidation.boundary, path: {})",
                render_value_contextual(default, field.get("type"), module, declarations.projection)?,
                descriptor_for_constructor(
                    required(field, "type", canonical)?,
                    declaration,
                    &type_witnesses,
                    declarations,
                    &config.dart.external_types,
                )?,
                dart_string(&format!("$.{field_name}")),
            ));
        } else {
            parameters.push(format!("required this.{escaped}"));
        }
    }
    parameters.extend(
        witnesses
            .iter()
            .map(|witness| format!("required this.{}", witness.public_name)),
    );
    let positional = type_witnesses
        .iter()
        .map(|witness| {
            format!(
                "{} _cott_type_{}",
                witness.ty,
                safe_internal_name(&witness.generic)
            )
        })
        .collect::<Vec<_>>();
    default_initializers.splice(
        0..0,
        type_witnesses.iter().map(|witness| {
            format!(
                "{} = _cott_type_{}",
                witness.public_name,
                safe_internal_name(&witness.generic)
            )
        }),
    );
    let constructor = match (positional.is_empty(), parameters.is_empty()) {
        (true, true) => String::new(),
        (true, false) => format!("{{{}}}", parameters.join(", ")),
        (false, true) => positional.join(", "),
        (false, false) => format!("{}, {{{}}}", positional.join(", "), parameters.join(", ")),
    };
    writeln!(
        out,
        "\n  {name}({constructor}){} {{",
        if default_initializers.is_empty() {
            String::new()
        } else {
            format!(" : {}", default_initializers.join(", "))
        }
    )
    .expect("writing to String cannot fail");
    render_identity_preflight(out, config, 4);
    render_bound_checks(
        out,
        &constructor_bound_checks(&extra_bounds, &type_witnesses)?,
        canonical,
        &EmissionTypeContext::new(declarations),
        declarations,
        &config.dart.external_types,
        4,
    )?;
    render_const_witness_validation(out, declaration, &witnesses, 4)?;
    for field in fields {
        let field = field.as_object().expect("validated struct field");
        let field_name = required_string(field, "name", canonical)?;
        writeln!(
            out,
            "    cott_runtime.CottRuntime.abi(this.{}, {}, mode: {}, path: {});",
            escape_identifier(field_name)?,
            descriptor_for_nominal(
                required(field, "type", canonical)?,
                declaration,
                declarations,
                &config.dart.external_types
            )?,
            "cott_runtime.RuntimeValidation.boundary",
            dart_string(&format!("$.{field_name}"))
        )
        .expect("writing to String cannot fail");
    }
    render_invariant_calls(
        out,
        declaration,
        canonical,
        4,
        module,
        &witnesses,
        declarations.projection,
    )?;
    writeln!(out, "  }}").expect("writing to String cannot fail");
    render_field_metadata(out, canonical, fields, 2)?;
    if fields.is_empty() {
        writeln!(
            out,
            "\n  @override\n  bool operator ==(Object other) => other is {name} && other.cottTypeIdentity == cottTypeIdentity;\n  @override\n  int get hashCode => cottTypeIdentity.hashCode;"
        )
        .expect("writing to String cannot fail");
    } else {
        let comparisons = fields
            .iter()
            .filter_map(|field| field.get("name").and_then(Value::as_str))
            .map(|field| {
                escape_identifier(field).map(|field| {
                    format!("cott_runtime.CottRuntime.canonicalEqual({field}, other.{field})")
                })
            })
            .collect::<Result<Vec<_>, _>>()?;
        let hashes = fields
            .iter()
            .filter_map(|field| field.get("name").and_then(Value::as_str))
            .map(escape_identifier)
            .collect::<Result<Vec<_>, _>>()?;
        writeln!(
            out,
            "\n  @override\n  bool operator ==(Object other) => other is {name} && {};\n  @override\n  int get hashCode => Object.hashAll([{}].map(cott_runtime.CottRuntime.deepHash));",
            comparisons.join(" && "),
            hashes.join(", ")
        )
        .expect("writing to String cannot fail");
    }
    render_generic_metadata(out, canonical, &type_witnesses, 2)?;
    let carrier_fields = fields
        .iter()
        .map(|field| {
            Ok((
                required_value(field, "name", canonical)?
                    .as_str()
                    .ok_or_else(|| format!("field on `{canonical}` has non-string name"))?
                    .to_owned(),
                required_value(field, "type", canonical)?.clone(),
            ))
        })
        .collect::<Result<Vec<_>, String>>()?;
    render_nominal_carrier_methods(
        out,
        &name,
        declaration,
        &carrier_fields,
        &type_witnesses,
        &witnesses,
        module,
        declarations,
        &config.dart.external_types,
        2,
    )?;
    writeln!(out, "}}").expect("writing to String cannot fail");
    let arguments = generic_names(declaration)?;
    let applied = if arguments.is_empty() {
        name.clone()
    } else {
        format!("{name}<{}>", arguments.join(", "))
    };
    let mut copy_parameters = Vec::new();
    let mut copy_fields = Vec::new();
    for field in fields {
        let field = field.as_object().expect("validated struct field");
        let field_name = required_string(field, "name", canonical)?;
        let escaped = escape_identifier(field_name)?;
        copy_parameters.push(format!("Object? {escaped} = _cott_omitted"));
        let value = if field.get("default").is_some_and(|value| !value.is_null()) {
            // Defaulted constructor parameters already admit the omission sentinel
            // and perform their own descriptor adaptation before storing the field.
            escaped.clone()
        } else {
            let descriptor = descriptor_for_nominal(
                required(field, "type", canonical)?,
                declaration,
                declarations,
                &config.dart.external_types,
            )?;
            format!(
                "cott_runtime.CottRuntime.abi({escaped}, {descriptor}, mode: cott_runtime.RuntimeValidation.boundary, path: {})",
                dart_string(&format!("$.{field_name}")),
            )
        };
        copy_fields.push(format!(
            "{escaped}: _cott_omitted == {escaped} ? this.{escaped} : {value}",
        ));
    }
    copy_fields.extend(
        witnesses
            .iter()
            .map(|witness| format!("{}: this.{}", witness.public_name, witness.public_name)),
    );
    let copy_witnesses = type_witnesses
        .iter()
        .map(|witness| format!("this.{}", witness.public_name))
        .collect::<Vec<_>>();
    let copy_constructor = render_constructor_invocation(&applied, &copy_witnesses, &copy_fields);
    let copy_parameters = if copy_parameters.is_empty() {
        String::new()
    } else {
        format!("{{{}}}", copy_parameters.join(", "))
    };
    // Keep convenience methods outside the canonical record interface. The dollar
    // sign cannot occur in a Cott identifier, so the extension name is unique.
    writeln!(
        out,
        "\n/// Copies exact stored fields unless overridden, then revalidates the value.\nextension {name}$CopyWith{generics} on {applied} {{\n  {applied} copyWith({copy_parameters}) => {copy_constructor};\n}}",
    )
    .expect("writing to String cannot fail");
    Ok(())
}

fn render_field_metadata(
    out: &mut String,
    canonical: &str,
    fields: &[Value],
    indent: usize,
) -> Result<(), String> {
    let prefix = " ".repeat(indent);
    let names = fields
        .iter()
        .map(|field| {
            field
                .get("name")
                .and_then(Value::as_str)
                .ok_or_else(|| format!("field on `{canonical}` is missing name"))
        })
        .collect::<Result<Vec<_>, _>>()?;
    writeln!(
        out,
        "\n{prefix}@override\n{prefix}String get cottTypeIdentity => {};\n{prefix}@override\n{prefix}cott_runtime.CottList<String> get cottFieldNames => cott_runtime.CottList([{}]);",
        dart_string(canonical),
        names
            .iter()
            .map(|name| dart_string(name))
            .collect::<Vec<_>>()
            .join(", ")
    )
    .expect("writing to String cannot fail");
    writeln!(
        out,
        "{prefix}@override\n{prefix}Object? cottField(String _cott_field) => switch (_cott_field) {{"
    )
    .expect("writing to String cannot fail");
    for name in names {
        writeln!(
            out,
            "{prefix}  {} => {},",
            dart_string(name),
            escape_identifier(name)?
        )
        .expect("writing to String cannot fail");
    }
    writeln!(
        out,
        "{prefix}  _ => cott_runtime.CottRuntime.violation('unknown canonical field', symbol: cottTypeIdentity, phase: 'field', actual: _cott_field),\n{prefix}}};"
    )
    .expect("writing to String cannot fail");
    Ok(())
}

/// Emits a native Dart `enum` for a declaration the projection accepted: a
/// finite set of constant members that keeps the canonical variant identity
/// while Dart owns `==`, `hashCode`, `index` and `values`.
fn render_native_enum(
    out: &mut String,
    declaration: &Map<String, Value>,
    canonical: &str,
) -> Result<(), String> {
    let name = escape_identifier(local_name(canonical))?;
    let variants = required_array(declaration, "variants", canonical)?;
    let mut members = Vec::with_capacity(variants.len());
    for variant in variants {
        let variant = variant
            .as_object()
            .ok_or_else(|| format!("enum `{canonical}` variant must be an object"))?;
        let symbol = required_string(variant, "symbol", canonical)?;
        members.push(format!(
            "  {}({})",
            types::native_enum_member(local_name(canonical), local_name(symbol))?,
            dart_string(symbol)
        ));
    }
    writeln!(
        out,
        "\nenum {name} implements cott_runtime.CottVariant {{\n{};\n\n  const {name}(this.cottVariant);\n  @override\n  final String cottVariant;\n  @override\n  String get cottTypeIdentity => cottVariant;\n  @override\n  cott_runtime.CottList<String> get cottFieldNames => _cott_no_field_names;\n  @override\n  cott_runtime.CottList<Object?> get cottPayload => _cott_no_payload;\n  @override\n  Object? cottField(String name) => cott_runtime.CottRuntime.violation('unknown canonical field', symbol: cottTypeIdentity, phase: 'field', actual: name);\n}}",
        members.join(",\n")
    )
    .expect("writing to String cannot fail");
    Ok(())
}

fn render_enum(
    out: &mut String,
    config: &DartProjectConfig,
    declaration: &Map<String, Value>,
    declarations: &DeclarationIndex<'_>,
) -> Result<(), String> {
    let canonical = required_string(declaration, "name", "enum")?;
    if declarations.projection.is_native(canonical) {
        return render_native_enum(out, declaration, canonical);
    }
    let module = module_of(canonical);
    let name = escape_identifier(local_name(canonical))?;
    let (generics, extra_bounds) = declaration_type_parameters(declaration, declarations)?;
    let generic_names = generic_names(declaration)?;
    let applied = if generic_names.is_empty() {
        name.clone()
    } else {
        format!("{name}<{}>", generic_names.join(", "))
    };
    let checked = declaration
        .get("generics")
        .and_then(Value::as_array)
        .is_some_and(|generics| {
            generics
                .iter()
                .any(|generic| generic.get("kind").and_then(Value::as_str) == Some("type"))
        });
    writeln!(
        out,
        "\nsealed class {name}{generics} implements cott_runtime.CottVariant{} {{\n  const {name}();",
        if checked {
            ", cott_runtime.CottCheckedView"
        } else {
            ""
        }
    )
    .expect("writing to String cannot fail");
    if checked {
        render_enum_type_factory(
            out,
            declaration,
            declarations,
            &config.dart.external_types,
            module,
        )?;
    }
    writeln!(out, "}}").expect("writing to String cannot fail");
    for variant in required_array(declaration, "variants", canonical)? {
        let variant = variant
            .as_object()
            .ok_or_else(|| format!("enum `{canonical}` variant must be an object"))?;
        let variant_symbol = required_string(variant, "symbol", canonical)?;
        let variant_name = enum_variant_name(variant_symbol, module, declarations.projection)?;
        let fields = required_array(variant, "fields", variant_symbol)?;
        let witnesses = const_witness_fields(declaration)?;
        let type_witnesses = type_witness_fields(declaration)?;
        writeln!(
            out,
            "\nfinal class {variant_name}{generics} extends {applied}{} {{",
            if type_witnesses.is_empty() {
                ""
            } else {
                " implements cott_runtime.CottGenericValue, cott_runtime.CottCheckedView"
            }
        )
        .expect("writing to String cannot fail");
        for (index, field) in fields.iter().enumerate() {
            let ty = required_value(field, "type", variant_symbol)?;
            writeln!(
                out,
                "  final {} {};",
                render_contextual_type(ty, module, declarations)?,
                enum_field_name(field, index)?
            )
            .expect("writing to String cannot fail");
        }
        for witness in &type_witnesses {
            writeln!(out, "  final {} {};", witness.ty, witness.public_name)
                .expect("writing to String cannot fail");
        }
        for witness in &witnesses {
            writeln!(out, "  final {} {};", witness.ty, witness.public_name)
                .expect("writing to String cannot fail");
        }
        let mut parameters = Vec::new();
        let mut initializers = Vec::new();
        for (index, field) in fields.iter().enumerate() {
            let property = enum_field_name(field, index)?;
            let ty = render_contextual_type(
                required_value(field, "type", variant_symbol)?,
                module,
                declarations,
            )?;
            if let Some(default) = field.get("default").filter(|value| !value.is_null()) {
                parameters.push(format!("Object? field{index} = _cott_omitted"));
                initializers.push(format!(
                    "{property} = cott_runtime.CottRuntime.abi(identical(field{index}, _cott_omitted) ? {} : field{index}, {}, mode: cott_runtime.RuntimeValidation.boundary, path: {})",
                    render_value_contextual(default, field.get("type"), module, declarations.projection)?,
                    descriptor_for_constructor(
                        required_value(field, "type", variant_symbol)?,
                        declaration,
                        &type_witnesses,
                        declarations,
                        &config.dart.external_types,
                    )?,
                    dart_string(&format!("$.{property}")),
                ));
            } else {
                parameters.push(format!("required {ty} field{index}"));
                initializers.push(format!("{property} = field{index}"));
            }
        }
        parameters.extend(
            witnesses
                .iter()
                .map(|witness| format!("required this.{}", witness.public_name)),
        );
        let positional = type_witnesses
            .iter()
            .map(|witness| {
                format!(
                    "{} _cott_type_{}",
                    witness.ty,
                    safe_internal_name(&witness.generic)
                )
            })
            .collect::<Vec<_>>();
        initializers.splice(
            0..0,
            type_witnesses.iter().map(|witness| {
                format!(
                    "{} = _cott_type_{}",
                    witness.public_name,
                    safe_internal_name(&witness.generic)
                )
            }),
        );
        let constructor = match (positional.is_empty(), parameters.is_empty()) {
            (true, true) => String::new(),
            (true, false) => format!("{{{}}}", parameters.join(", ")),
            (false, true) => positional.join(", "),
            (false, false) => format!("{}, {{{}}}", positional.join(", "), parameters.join(", ")),
        };
        writeln!(
            out,
            "\n  {variant_name}({constructor}){} {{",
            if initializers.is_empty() {
                String::new()
            } else {
                format!(" : {}", initializers.join(", "))
            }
        )
        .expect("writing to String cannot fail");
        render_identity_preflight(out, config, 4);
        render_bound_checks(
            out,
            &constructor_bound_checks(&extra_bounds, &type_witnesses)?,
            canonical,
            &EmissionTypeContext::new(declarations),
            declarations,
            &config.dart.external_types,
            4,
        )?;
        render_const_witness_validation(out, declaration, &witnesses, 4)?;
        for (index, field) in fields.iter().enumerate() {
            let field_name = enum_field_name(field, index)?;
            writeln!(
                out,
                "    cott_runtime.CottRuntime.abi(this.{field_name}, {}, mode: {}, path: {});",
                descriptor_for_nominal(
                    required_value(field, "type", variant_symbol)?,
                    declaration,
                    declarations,
                    &config.dart.external_types
                )?,
                "cott_runtime.RuntimeValidation.boundary",
                dart_string(&format!("$.{field_name}"))
            )
            .expect("writing to String cannot fail");
        }
        writeln!(out, "  }}").expect("writing to String cannot fail");
        render_variant_metadata(out, variant_symbol, fields, 2)?;
        let comparisons = fields
            .iter()
            .enumerate()
            .map(|(index, field)| {
                enum_field_name(field, index).map(|name| {
                    format!("cott_runtime.CottRuntime.canonicalEqual({name}, other.{name})")
                })
            })
            .collect::<Result<Vec<_>, _>>()?;
        writeln!(
            out,
            "\n  @override\n  bool operator ==(Object other) => other is {variant_name}{};\n  @override\n  int get hashCode => Object.hashAll([cottVariant, ...cottPayload]);",
            if comparisons.is_empty() {
                String::new()
            } else {
                format!(" && {}", comparisons.join(" && "))
            }
        )
        .expect("writing to String cannot fail");
        render_generic_metadata(out, canonical, &type_witnesses, 2)?;
        if !type_witnesses.is_empty() {
            let positional = type_witnesses
                .iter()
                .map(|witness| witness.public_name.clone())
                .collect::<Vec<_>>();
            let mut named = fields
                .iter()
                .enumerate()
                .map(|(index, field)| {
                    Ok(format!(
                        "field{index}: fields[{index}] as {}",
                        render_contextual_type(
                            required_value(field, "type", variant_symbol)?,
                            module,
                            declarations
                        )?
                    ))
                })
                .collect::<Result<Vec<_>, String>>()?;
            named.extend(
                witnesses
                    .iter()
                    .map(|witness| format!("{}: {}", witness.public_name, witness.public_name)),
            );
            let carrier = format!(
                "_cott_carrier_{}",
                &sha256_hex(
                    module
                        .ok_or_else(|| format!("generic enum `{canonical}` has no module"))?
                        .as_bytes()
                )[..16]
            );
            let construction = render_constructor_invocation(&variant_name, &positional, &named);
            writeln!(
                out,
                "\n  @override\n  cott_runtime.CottNominalCarrier cottCarrier(cott_runtime.CottViewAccess access) {{\n    if (!access.allows({name}._cott_view_seal)) cott_runtime.CottRuntime.violation('invalid checked-view access', phase: 'validation');\n    return {carrier}(this, (fields) => {construction});\n  }}"
            )
            .expect("writing to String cannot fail");
        }
        writeln!(out, "}}").expect("writing to String cannot fail");
    }
    Ok(())
}

fn render_enum_type_factory(
    out: &mut String,
    declaration: &Map<String, Value>,
    declarations: &DeclarationIndex<'_>,
    external_types: &BTreeMap<String, String>,
    module: Option<&str>,
) -> Result<(), String> {
    let canonical = required_string(declaration, "name", "enum")?;
    let name = escape_identifier(local_name(canonical))?;
    let (generics, bound_checks) = declaration_type_parameters(declaration, declarations)?;
    let applied_names = generic_names(declaration)?;
    let applied = format!("{name}<{}>", applied_names.join(", "));
    let type_witnesses = type_witness_fields(declaration)?;
    let const_witnesses = const_witness_fields(declaration)?;
    let mut parameters = type_witnesses
        .iter()
        .map(|witness| {
            format!(
                "{} _cott_type_{}",
                witness.ty,
                safe_internal_name(&witness.generic)
            )
        })
        .collect::<Vec<_>>();
    parameters.extend(const_witnesses.iter().map(|witness| {
        format!(
            "{} _cott_const_{}",
            witness.ty,
            safe_internal_name(&witness.generic)
        )
    }));
    let expected = type_witnesses
        .iter()
        .enumerate()
        .map(|(index, witness)| format!("expectedArguments[{index}] as {}", witness.ty))
        .collect::<Vec<_>>();
    let mut cases = Vec::new();
    for variant in required_array(declaration, "variants", canonical)? {
        let symbol = required_value(variant, "symbol", canonical)?
            .as_str()
            .ok_or_else(|| format!("variant on `{canonical}` has non-string symbol"))?;
        let variant_name = enum_variant_name(symbol, module, declarations.projection)?;
        let variant_applied = format!("{variant_name}<{}>", applied_names.join(", "));
        let fields = required_array(
            variant
                .as_object()
                .ok_or_else(|| format!("variant on `{canonical}` is not an object"))?,
            "fields",
            symbol,
        )?;
        let mut named = fields
            .iter()
            .enumerate()
            .map(|(index, field)| {
                Ok(format!(
                    "field{index}: carrier.cottField({}) as {}",
                    dart_string(
                        field
                            .get("name")
                            .and_then(Value::as_str)
                            .unwrap_or_else(|| local_name(symbol))
                    ),
                    render_contextual_type(
                        required_value(field, "type", symbol)?,
                        module,
                        declarations
                    )?
                ))
            })
            .collect::<Result<Vec<_>, String>>()?;
        named.extend(const_witnesses.iter().map(|witness| {
            format!(
                "{}: _cott_const_{}",
                witness.public_name,
                safe_internal_name(&witness.generic)
            )
        }));
        cases.push(format!(
            "{} => {}",
            dart_string(symbol),
            render_constructor_invocation(&variant_applied, &expected, &named)
        ));
    }
    cases.push("_ => cott_runtime.CottRuntime.violation('unknown enum carrier variant', phase: 'validation')".to_owned());
    let arguments = type_witnesses
        .iter()
        .map(|witness| {
            format!(
                "(_cott_type_{} as cott_runtime.CottType<Object?>)",
                safe_internal_name(&witness.generic)
            )
        })
        .collect::<Vec<_>>();
    let variances = required_array(declaration, "generics", canonical)?
        .iter()
        .filter(|generic| generic.get("kind").and_then(Value::as_str) == Some("type"))
        .map(|generic| {
            match generic
                .get("variance")
                .and_then(Value::as_str)
                .unwrap_or("invariant")
            {
                "invariant" => Ok("cott_runtime.CottVariance.invariant"),
                "covariant" => Ok("cott_runtime.CottVariance.covariant"),
                "contravariant" => Ok("cott_runtime.CottVariance.contravariant"),
                other => Err(format!(
                    "unsupported Cott variance `{other}` on `{canonical}`"
                )),
            }
        })
        .collect::<Result<Vec<_>, String>>()?;
    writeln!(
        out,
        "\n  static final Object _cott_view_seal = Object();\n  static cott_runtime.CottType<{applied}> cottType{generics}({}) {{",
        parameters.join(", "),
    )
    .expect("writing to String cannot fail");
    render_bound_checks(
        out,
        &bound_checks,
        canonical,
        &EmissionTypeContext::new(declarations),
        declarations,
        external_types,
        4,
    )?;
    writeln!(
        out,
        "    return cott_runtime.CottTypes.deferred<{applied}>({}, () => cott_runtime.CottTypes.checkedNominal<{applied}>({}, const [], (carrier) => carrier.cottGenericIdentity == {}, (carrier, expectedArguments) => switch (carrier.cottTypeIdentity) {{ {} }}, acceptsView: (value) => value is {name}, viewSeal: _cott_view_seal, arguments: [{}], variances: [{}]));\n  }}",
        dart_string(canonical),
        dart_string(canonical),
        dart_string(canonical),
        cases.join(", "),
        arguments.join(", "),
        variances.join(", ")
    )
    .expect("writing to String cannot fail");
    Ok(())
}

fn enum_field_name(field: &Value, index: usize) -> Result<String, String> {
    field
        .get("name")
        .and_then(Value::as_str)
        .map(escape_identifier)
        .transpose()?
        .map(Ok)
        .unwrap_or_else(|| Ok(format!("field{index}")))
}

fn render_variant_metadata(
    out: &mut String,
    variant_symbol: &str,
    fields: &[Value],
    indent: usize,
) -> Result<(), String> {
    let prefix = " ".repeat(indent);
    let properties = fields
        .iter()
        .enumerate()
        .map(|(index, field)| enum_field_name(field, index))
        .collect::<Result<Vec<_>, _>>()?;
    let canonical_names = fields
        .iter()
        .enumerate()
        .map(|(index, field)| {
            field
                .get("name")
                .and_then(Value::as_str)
                .map(str::to_owned)
                .unwrap_or_else(|| format!("field{index}"))
        })
        .collect::<Vec<_>>();
    writeln!(
        out,
        "\n{prefix}@override\n{prefix}String get cottVariant => {};\n{prefix}@override\n{prefix}String get cottTypeIdentity => {};\n{prefix}@override\n{prefix}cott_runtime.CottList<String> get cottFieldNames => cott_runtime.CottList([{}]);\n{prefix}@override\n{prefix}cott_runtime.CottList<Object?> get cottPayload => cott_runtime.CottList([{}]);",
        dart_string(variant_symbol),
        dart_string(variant_symbol),
        canonical_names.iter().map(|name| dart_string(name)).collect::<Vec<_>>().join(", "),
        properties.join(", ")
    )
    .expect("writing to String cannot fail");
    writeln!(
        out,
        "{prefix}@override\n{prefix}Object? cottField(String _cott_field) => switch (_cott_field) {{"
    )
    .expect("writing to String cannot fail");
    for (canonical, property) in canonical_names.iter().zip(properties) {
        writeln!(out, "{prefix}  {} => {property},", dart_string(canonical))
            .expect("writing to String cannot fail");
    }
    writeln!(
        out,
        "{prefix}  _ => cott_runtime.CottRuntime.violation('unknown canonical field', symbol: cottVariant, phase: 'field', actual: _cott_field),\n{prefix}}};"
    )
    .expect("writing to String cannot fail");
    Ok(())
}

fn render_trait(
    out: &mut String,
    declaration: &Map<String, Value>,
    declarations: &DeclarationIndex<'_>,
) -> Result<(), String> {
    let canonical = required_string(declaration, "name", "trait")?;
    let module = module_of(canonical);
    let name = escape_identifier(local_name(canonical))?;
    let (generics, _) = declaration_type_parameters(declaration, declarations)?;
    let trait_ref = declaration_trait_ref(declaration)?;
    let slots = trait_slot_definitions(&trait_ref, declarations)?;
    let mut generic_parts = if generics.is_empty() {
        Vec::new()
    } else {
        generics[1..generics.len() - 1]
            .split(", ")
            .map(str::to_owned)
            .collect()
    };
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
        let base = serde_json::json!({
            "kind": "associated_projection",
            "base": {"kind": "type_parameter", "name": "Self"},
            "trait": slot.trait_name,
            "name": slot.slot_name,
        });
        let mut bound = None;
        for candidate in &slot.bounds {
            if !bound_requires_existential_projection(candidate, declarations)? {
                bound = Some(render_bound_for_base(candidate, &base, &context)?);
                break;
            }
        }
        generic_parts.push(if let Some(bound) = bound {
            format!("{parameter} extends {bound}")
        } else {
            parameter
        });
    }
    let generics = if generic_parts.is_empty() {
        String::new()
    } else {
        format!("<{}>", generic_parts.join(", "))
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
                module,
            )
        })
        .collect::<Result<Vec<_>, _>>()?;
    writeln!(
        out,
        "\nabstract interface class {name}{generics}{} {{",
        if parents.is_empty() {
            String::new()
        } else {
            format!(" implements {}", parents.join(", "))
        }
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
            "  {} get cottConst{};",
            escape_identifier(generic_name)?,
            pascal_identifier(generic_name)?
        )
        .expect("writing to String cannot fail");
    }
    for method in required_array(declaration, "methods", canonical)? {
        let method = method
            .as_object()
            .ok_or_else(|| "trait method must be an object".to_owned())?;
        render_doc(out, method.get("doc"), 2);
        let rendering = callable_rendering(method, declarations, trait_scope.clone())?;
        let parameters = render_parameters_contextual(
            method,
            true,
            &rendering.context,
            &rendering.associated,
            ParameterSurface::Public,
        )?
        .join(", ");
        let return_type = render_type_contextual(
            required(method, "return_type", canonical)?,
            module,
            Some(&rendering.context),
        )?;
        let return_type = if method.get("callable_kind").and_then(Value::as_str) == Some("async") {
            format!("Future<{return_type}>")
        } else {
            return_type
        };
        writeln!(
            out,
            "  {return_type} {}{}({parameters});",
            escape_identifier(local_name(required_string(method, "name", canonical)?))?,
            rendering.generics
        )
        .expect("writing to String cannot fail");
    }
    writeln!(out, "}}").expect("writing to String cannot fail");
    Ok(())
}

fn render_rule(
    out: &mut String,
    declaration: &Map<String, Value>,
    declarations: &DeclarationIndex<'_>,
) -> Result<(), String> {
    let canonical = required_string(declaration, "name", "rule")?;
    let name = escape_identifier(local_name(canonical))?;
    let (generics, _) = declaration_type_parameters(declaration, declarations)?;
    let base = declaration
        .get("base")
        .and_then(Value::as_str)
        .map(|base| render_canonical_symbol(base, module_of(canonical)))
        .transpose()?
        .map(|base| format!(" implements {base}"))
        .unwrap_or_default();
    writeln!(
        out,
        "\nabstract interface class {name}{generics}{base} {{}}"
    )
    .expect("writing to String cannot fail");
    Ok(())
}

fn render_resource(out: &mut String, declaration: &Map<String, Value>) -> Result<(), String> {
    let canonical = required_string(declaration, "name", "resource")?;
    let name = escape_identifier(local_name(canonical))?;
    writeln!(
        out,
        "\nsealed class {name} implements cott_runtime.CottVariant {{\n  const {name}();\n}}"
    )
    .expect("writing to String cannot fail");
    for state in required_array(declaration, "states", canonical)? {
        let state_name = state
            .get("name")
            .and_then(Value::as_str)
            .ok_or_else(|| format!("resource `{canonical}` state is missing name"))?;
        let local = format!("{}{}", name, escape_identifier(local_name(state_name))?);
        writeln!(
            out,
            "\nfinal class {local} extends {name} {{\n  const {local}();\n  @override\n  String get cottVariant => {};\n  @override\n  String get cottTypeIdentity => {};\n  @override\n  cott_runtime.CottList<String> get cottFieldNames => cott_runtime.CottList([]);\n  @override\n  cott_runtime.CottList<Object?> get cottPayload => cott_runtime.CottList([]);\n  @override\n  Object? cottField(String name) => cott_runtime.CottRuntime.violation('resource state has no fields', symbol: cottVariant, phase: 'field', actual: name);\n}}",
            dart_string(state_name),
            dart_string(state_name)
        )
        .expect("writing to String cannot fail");
    }
    Ok(())
}

fn render_const(
    out: &mut String,
    declaration: &Map<String, Value>,
    declarations: &DeclarationIndex<'_>,
) -> Result<(), String> {
    let canonical = required_string(declaration, "name", "const")?;
    let ty = required(declaration, "type", canonical)?;
    writeln!(
        out,
        "\nfinal {} {} = {};",
        render_contextual_type(ty, module_of(canonical), declarations)?,
        escape_identifier(local_name(canonical))?,
        render_value_contextual(
            required(declaration, "value", canonical)?,
            Some(ty),
            module_of(canonical),
            declarations.projection,
        )?
    )
    .expect("writing to String cannot fail");
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
    for line in text.lines() {
        writeln!(out, "{prefix}/// {}", line.replace("*/", "* /"))
            .expect("writing to String cannot fail");
    }
}

fn render_identity_preflight(out: &mut String, config: &DartProjectConfig, indent: usize) {
    let prefix = " ".repeat(indent);
    writeln!(
        out,
        "{prefix}cott_runtime.CottRuntime.requireIdentity({}, {}, {DART_RUNTIME_ABI});",
        dart_string(&config.project.name),
        dart_string(&config.project.version)
    )
    .expect("writing to String cannot fail");
}

fn render_const_witness_validation(
    out: &mut String,
    declaration: &Map<String, Value>,
    witnesses: &[WitnessField],
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
        let field = witnesses
            .iter()
            .find(|witness| witness.generic == name)
            .ok_or_else(|| format!("const witness field `{name}` is missing"))?;
        writeln!(
            out,
            "{prefix}cott_runtime.CottRuntime.validateConst({}, {}, path: {});",
            field.public_name,
            generic_const_kind(generic)?,
            dart_string(&format!("$.const.{name}"))
        )
        .expect("writing to String cannot fail");
    }
    Ok(())
}

fn qualify_constructor_field_references(
    value: &mut Value,
    fields: &BTreeSet<String>,
) -> Result<(), String> {
    let referenced_field = value.as_object().and_then(|object| {
        (object.get("kind").and_then(Value::as_str) == Some("parameter_ref"))
            .then(|| object.get("symbol").and_then(Value::as_str))
            .flatten()
            .map(local_name)
            .filter(|name| fields.contains(*name))
            .map(str::to_owned)
    });
    if let Some(field) = referenced_field {
        *value = serde_json::json!({
            "kind": "dart_synthetic",
            "code": format!("this.{}", escape_identifier(&field)?),
        });
        return Ok(());
    }
    match value {
        Value::Array(values) => {
            for value in values {
                qualify_constructor_field_references(value, fields)?;
            }
        }
        Value::Object(object) => {
            for value in object.values_mut() {
                qualify_constructor_field_references(value, fields)?;
            }
        }
        _ => {}
    }
    Ok(())
}

fn render_invariant_calls(
    out: &mut String,
    declaration: &Map<String, Value>,
    symbol: &str,
    indent: usize,
    module: Option<&str>,
    witnesses: &[WitnessField],
    projection: &DartEnumProjection,
) -> Result<(), String> {
    let prefix = " ".repeat(indent);
    let fields = required_array(declaration, "fields", symbol)?
        .iter()
        .map(|field| {
            field
                .get("name")
                .and_then(Value::as_str)
                .ok_or_else(|| format!("struct `{symbol}` field is missing name"))
                .map(str::to_owned)
        })
        .collect::<Result<BTreeSet<_>, _>>()?;
    for invariant in required_array(declaration, "invariants", symbol)? {
        let mut expression = required_value(invariant, "expression", symbol)?.clone();
        let mut guard = invariant.get("guard").cloned();
        qualify_constructor_field_references(&mut expression, &fields)?;
        if let Some(guard) = &mut guard {
            qualify_constructor_field_references(guard, &fields)?;
        }
        rewrite_const_references(&mut expression, declaration, witnesses);
        if let Some(guard) = &mut guard {
            rewrite_const_references(guard, declaration, witnesses);
        }
        let condition = render_condition(&expression, None, true, module, projection)?;
        let clause = format!(
            "invariant:{}",
            invariant
                .get("clause_id")
                .and_then(Value::as_u64)
                .ok_or_else(|| format!("invariant on `{symbol}` is missing clause_id"))?
        );
        let statement = format!(
            "cott_runtime.CottRuntime.invariant({condition}, {}, clause: {}, span: {}, expected: 'true', actual: 'false');",
            dart_string(symbol),
            dart_string(&clause),
            render_span(invariant.get("span"))?
        );
        writeln!(
            out,
            "{prefix}{}",
            super::expressions::render_guarded_statement(
                guard.as_ref(),
                &statement,
                module,
                projection
            )?
        )
        .expect("writing to String cannot fail");
    }
    Ok(())
}

pub(crate) fn implementation_imports(
    config: &DartProjectConfig,
    plan: &DartPlan,
    _callable: &DartCallable,
) -> Result<Vec<String>, String> {
    let mut imports = vec![
        runtime_import(&config.project.name),
        marker_import(&config.project.name),
    ];
    for module in &plan.modules {
        imports.push(type_import(&config.project.name, &module.name)?);
    }
    Ok(imports)
}

fn render_contextual_type(
    ty: &Value,
    module: Option<&str>,
    declarations: &DeclarationIndex<'_>,
) -> Result<String, String> {
    let context = EmissionTypeContext::new(declarations);
    render_type_contextual(ty, module, Some(&context))
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
    declarations: &DeclarationIndex<'_>,
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
    declarations: &DeclarationIndex<'_>,
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
            if !seen.insert((trait_name.to_owned(), slot_name.to_owned())) {
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

fn is_trait_type(ty: &Value, declarations: &DeclarationIndex<'_>) -> bool {
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
    declarations: &DeclarationIndex<'_>,
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
    for associated in required_array(declaration, "associated_types", trait_name)? {
        let associated = associated
            .as_object()
            .ok_or_else(|| format!("trait `{trait_name}` associated slot must be an object"))?;
        let (declaring_trait, declared_slot) =
            declared_associated_identity(associated, trait_name)?;
        if declaring_trait == trait_name && declared_slot == local_name(slot_name) {
            return Ok(required_array(associated, "bounds", slot_name)?.clone());
        }
    }
    Err(format!(
        "trait `{trait_name}` has no associated slot `{slot_name}`"
    ))
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

fn selected_method_slot<'a>(
    owner: &'a Map<String, Value>,
    callable: &DartCallable,
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
    declarations: &DeclarationIndex<'_>,
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
    callable: &DartCallable,
    owner: &Map<String, Value>,
    slot: &Map<String, Value>,
    declarations: &DeclarationIndex<'_>,
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
    declarations: &DeclarationIndex<'_>,
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

fn instantiate_type(
    value: &Value,
    declaration: &Map<String, Value>,
    named: &Map<String, Value>,
) -> Value {
    let mut type_arguments = BTreeMap::<String, Value>::new();
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
                    type_arguments.insert(name.to_owned(), value.clone());
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
    substitute_arguments(&mut value, &type_arguments, &constants);
    value
}

fn substitute_arguments(
    value: &mut Value,
    type_arguments: &BTreeMap<String, Value>,
    constants: &BTreeMap<String, Value>,
) {
    let replacement = value.as_object().and_then(|object| {
        match (
            object.get("kind").and_then(Value::as_str),
            object.get("name").and_then(Value::as_str),
        ) {
            (Some("type_parameter"), Some(name)) => type_arguments.get(name).cloned(),
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
                substitute_arguments(value, type_arguments, constants);
            }
        }
        Value::Object(object) => {
            for value in object.values_mut() {
                substitute_arguments(value, type_arguments, constants);
            }
        }
        _ => {}
    }
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

fn render_trait_reference(
    trait_ref: &Value,
    implementation: Option<&Map<String, Value>>,
    declarations: &DeclarationIndex<'_>,
    context: Option<&EmissionTypeContext<'_>>,
    module: Option<&str>,
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
                Some("type") => render_type_contextual(
                    argument
                        .get("type")
                        .ok_or_else(|| "trait type argument is missing type".to_owned())?,
                    module,
                    context.map(|context| context as &dyn DartTypeContext),
                ),
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
            arguments.push(render_contextual_type(assignment, module, declarations)?);
        } else {
            arguments.push(associated_type_name(&slot.trait_name, &slot.slot_name));
        }
    }
    let name = render_canonical_symbol(name, module)?;
    Ok(if arguments.is_empty() {
        name
    } else {
        format!("{name}<{}>", arguments.join(", "))
    })
}

fn trait_specializations(
    implementation: &Map<String, Value>,
    declarations: &DeclarationIndex<'_>,
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

fn trait_descriptor(
    trait_ref: &Value,
    implementation: Option<&Map<String, Value>>,
    declarations: &DeclarationIndex<'_>,
) -> Result<String, String> {
    let object = trait_ref
        .as_object()
        .ok_or_else(|| "trait descriptor reference must be an object".to_owned())?;
    let canonical = required_string(object, "name", "trait descriptor")?;
    let rendered = render_trait_reference(trait_ref, implementation, declarations, None, None)?;
    Ok(format!(
        "cott_runtime.CottTypes.external<{rendered}>({}, (value) => value is {rendered}, identityWitness: {rendered})",
        dart_string(canonical)
    ))
}

fn implementation_bound_checks(
    implementation: &Map<String, Value>,
    declarations: &DeclarationIndex<'_>,
    external_types: &BTreeMap<String, String>,
) -> Result<Vec<BoundCheck>, String> {
    let canonical = required_string(implementation, "name", "implementation")?;
    let mut checks = BTreeMap::new();
    for trait_ref in trait_specializations(implementation, declarations)? {
        for slot in trait_slot_definitions(&trait_ref, declarations)? {
            let assignment =
                associated_assignment_type(implementation, &slot.trait_name, &slot.slot_name)
                    .ok_or_else(|| {
                        format!(
                            "implementation `{canonical}` is missing associated assignment `{}.{}`",
                            slot.trait_name,
                            local_name(&slot.slot_name)
                        )
                    })?
                    .clone();
            let witness = descriptor_for(&assignment, declarations, external_types)?;
            for (index, bound) in slot.bounds.iter().enumerate() {
                let mut bound = bound.clone();
                substitute_associated_types(&mut bound, implementation);
                let exact = !bound_requires_existential_projection(&bound, declarations)?;
                let identity = format!(
                    "associated-bound:{}:{}:{index}:{}",
                    slot.trait_name,
                    local_name(&slot.slot_name),
                    serde_json::to_string(&bound)
                        .map_err(|error| format!("serialize associated bound: {error}"))?,
                );
                checks.entry(identity.clone()).or_insert(BoundCheck {
                    witness: witness.clone(),
                    base: assignment.clone(),
                    bound,
                    label: identity,
                    exact,
                });
            }
        }
    }
    Ok(checks.into_values().collect())
}

fn render_implementation_descriptor(
    out: &mut String,
    implementation: &Map<String, Value>,
    declarations: &DeclarationIndex<'_>,
) -> Result<(), String> {
    let canonical = required_string(implementation, "name", "implementation")?;
    let name = escape_identifier(local_name(canonical))?;
    let supertypes = trait_specializations(implementation, declarations)?
        .iter()
        .map(|trait_ref| {
            trait_descriptor(trait_ref, Some(implementation), declarations)
                .map(|descriptor| format!("({descriptor} as cott_runtime.CottType<Object?>)"))
        })
        .collect::<Result<Vec<_>, _>>()?;
    writeln!(
        out,
        "\n  static final cott_runtime.CottType<{name}> cottType = cott_runtime.CottTypes.external<{name}>({}, (value) => value is {name}, identityWitness: {name}, supertypes: [{}]);",
        dart_string(canonical),
        supertypes.join(", "),
    )
    .expect("writing to String cannot fail");
    Ok(())
}

fn descriptor_for(
    ty: &Value,
    declarations: &DeclarationIndex<'_>,
    external_types: &BTreeMap<String, String>,
) -> Result<String, String> {
    let object = ty
        .as_object()
        .ok_or_else(|| "canonical descriptor type must be an object".to_owned())?;
    let kind = required_string(object, "kind", "descriptor type")?;
    match kind {
        "primitive" => types::render_primitive_descriptor(ty),
        "type_parameter" | "associated_projection" => Ok(format!(
            "(cott_runtime.CottTypes.any as cott_runtime.CottType<{}>)",
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
                descriptor_for(required(object, left, kind)?, declarations, external_types)?,
                descriptor_for(required(object, right, kind)?, declarations, external_types)?
            ))
        }
        "tuple" => {
            let items = required_array(object, "items", "tuple type")?
                .iter()
                .map(|item| {
                    descriptor_for(item, declarations, external_types)
                        .map(|value| format!("({value} as cott_runtime.CottType<Object?>)"))
                })
                .collect::<Result<Vec<_>, _>>()?;
            let rendered = render_contextual_type(ty, None, declarations)?;
            Ok(format!(
                "cott_runtime.CottTypes.tuple<{rendered}>([{}])",
                items.join(", ")
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
                    "cott_runtime.CottTypes.array<{}, {}>({}, cott_runtime.CottRuntime.constLength({witness}), witness: {witness})",
                    render_contextual_type(item, None, declarations)?,
                    marker,
                    descriptor_for(item, declarations, external_types)?,
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
                    "cott_runtime.CottTypes.buffer<{marker}>(cott_runtime.CottRuntime.constLength({witness}), witness: {witness})"
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
            "cott_runtime.CottTypes.asyncGenerator({}, {}, cott_runtime.CottTypes.unit)",
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
        "opaque" => {
            let marker = types::opaque_marker(required_string(object, "tag", "opaque type")?);
            Ok(format!(
                "cott_runtime.CottTypes.opaque(const cott_markers.{marker}())"
            ))
        }
        "dyn" => Ok(format!(
            "(cott_runtime.CottTypes.dyn(cott_markers.{}) as cott_runtime.CottType<{}>)",
            trait_marker(required(object, "trait", "Dyn type")?)?,
            render_contextual_type(ty, None, declarations)?
        )),
        "factory" => {
            let instance = required(object, "instance", "Factory type")?;
            let rendered = render_contextual_type(instance, None, declarations)?;
            Ok(format!(
                "cott_runtime.CottTypes.factory<{rendered}>({rendered})"
            ))
        }
        "named" => descriptor_for_named(ty, object, declarations, external_types),
        other => Err(format!("unsupported Dart descriptor type kind `{other}`")),
    }
}

fn descriptor_for_named(
    ty: &Value,
    object: &Map<String, Value>,
    declarations: &DeclarationIndex<'_>,
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
            let projection = external_types.get(name).ok_or_else(|| {
                format!("external Dart type `{name}` has no configured projection")
            })?;
            let (_, target) = parse_external_projection(projection)?;
            let rendered = render_contextual_type(ty, None, declarations)?;
            Ok(format!(
                "cott_runtime.CottTypes.external<{rendered}>({}, (value) => value is {rendered}, identityWitness: {rendered})",
                dart_string(target)
            ))
        }
        "impl" => Ok(format!("{}.cottType", render_canonical_symbol(name, None)?)),
        "newtype" | "struct" | "enum" | "resource" | "trait" => {
            let rendered = render_contextual_type(ty, None, declarations)?;
            let parameters = required_array(declaration, "generics", name)?;
            let arguments = required_array(object, "args", name)?;
            if parameters.len() != arguments.len() {
                return Err(format!(
                    "named type `{name}` has {} arguments but declares {} parameters",
                    arguments.len(),
                    parameters.len()
                ));
            }
            let mut type_arguments = Vec::new();
            let mut variances = Vec::new();
            for (parameter, argument) in parameters.iter().zip(arguments) {
                match (
                    parameter.get("kind").and_then(Value::as_str),
                    argument.get("kind").and_then(Value::as_str),
                ) {
                    (Some("type"), Some("type")) => {
                        type_arguments.push(format!(
                            "({} as cott_runtime.CottType<Object?>)",
                            descriptor_for(
                                required_value(argument, "type", name)?,
                                declarations,
                                external_types
                            )?
                        ));
                        variances.push(match parameter
                            .get("variance")
                            .and_then(Value::as_str)
                            .unwrap_or("invariant")
                        {
                            "invariant" => "cott_runtime.CottVariance.invariant",
                            "covariant" => "cott_runtime.CottVariance.covariant",
                            "contravariant" => "cott_runtime.CottVariance.contravariant",
                            other => {
                                return Err(format!(
                                    "generic parameter on `{name}` has unsupported variance `{other}`"
                                ));
                            }
                        });
                    }
                    (Some("const"), Some("const")) => {}
                    (expected, actual) => {
                        return Err(format!(
                            "generic argument kind `{actual:?}` does not match `{expected:?}` on `{name}`"
                        ));
                    }
                }
            }
            let generated_factory = matches!(declaration_kind, "newtype" | "struct")
                || declaration_kind == "enum" && !type_arguments.is_empty();
            if !generated_factory {
                return Ok(format!(
                    "cott_runtime.CottTypes.external<{rendered}>({}, (value) => value is {rendered}, identityWitness: {rendered})",
                    dart_string(name)
                ));
            }
            render_checked_nominal_descriptor(
                &rendered,
                name,
                declaration_kind,
                declaration,
                object,
                &type_arguments,
                &variances,
                declarations,
                external_types,
            )
        }
        other => Err(format!(
            "declaration `{name}` of kind `{other}` is not a Dart ABI type"
        )),
    }
}

fn render_checked_nominal_descriptor(
    _rendered: &str,
    name: &str,
    _declaration_kind: &str,
    declaration: &Map<String, Value>,
    object: &Map<String, Value>,
    _type_arguments: &[String],
    _variances: &[&str],
    declarations: &DeclarationIndex<'_>,
    external_types: &BTreeMap<String, String>,
) -> Result<String, String> {
    let mut parameters = Vec::new();
    for argument in required_array(object, "args", name)? {
        match argument.get("kind").and_then(Value::as_str) {
            Some("type") => parameters.push(descriptor_for(
                required_value(argument, "type", name)?,
                declarations,
                external_types,
            )?),
            Some("const") => parameters.push(render_const_witness(required_value(
                argument, "value", name,
            )?)?),
            other => {
                return Err(format!(
                    "generic argument on `{name}` has unsupported kind `{other:?}`"
                ));
            }
        }
    }
    let generic_arguments =
        types::render_named_arguments(Some(&Value::Object(object.clone())), None)?;
    let base = render_canonical_symbol(name, None)?;
    if required_array(declaration, "generics", name)?.is_empty() {
        return Ok(format!("{base}.cottType"));
    }
    Ok(format!(
        "{base}.cottType{}({})",
        if generic_arguments.is_empty() {
            String::new()
        } else {
            format!("<{}>", generic_arguments.join(", "))
        },
        parameters.join(", ")
    ))
}

fn descriptor_for_nominal(
    ty: &Value,
    declaration: &Map<String, Value>,
    declarations: &DeclarationIndex<'_>,
    external_types: &BTreeMap<String, String>,
) -> Result<String, String> {
    let context = EmissionTypeContext::new(declarations);
    let mut rendered = descriptor_for_contextual(ty, declarations, external_types, &context)?;
    for witness in type_witness_fields(declaration)? {
        rendered = rendered.replace(
            &format!("_cott_type_{}", safe_internal_name(&witness.generic)),
            &witness.public_name,
        );
    }
    for witness in const_witness_fields(declaration)? {
        rendered = rendered.replace(
            &format!("_cott_const_{}", safe_internal_name(&witness.generic)),
            &witness.public_name,
        );
    }
    if let Some(module) = module_of(required_string(declaration, "name", "nominal")?) {
        rendered = rendered.replace(&format!("{}.", module_prefix(module)), "");
    }
    Ok(rendered)
}

fn descriptor_for_contextual(
    ty: &Value,
    declarations: &DeclarationIndex<'_>,
    external_types: &BTreeMap<String, String>,
    context: &EmissionTypeContext<'_>,
) -> Result<String, String> {
    let mut rendered = descriptor_for(ty, declarations, external_types)?;
    let mut type_parameters = BTreeSet::new();
    collect_type_parameters(ty, &mut type_parameters)?;
    for name in type_parameters {
        let parameter = serde_json::json!({"kind": "type_parameter", "name": name});
        let placeholder = descriptor_for(&parameter, declarations, external_types)?;
        rendered = rendered.replace(
            &placeholder,
            &format!("_cott_type_{}", safe_internal_name(&name)),
        );
    }
    let mut projections = Vec::new();
    collect_associated_projections(ty, &mut projections)?;
    for (base, trait_name, slot_name) in projections {
        let projection = serde_json::json!({
            "kind": "associated_projection",
            "base": base,
            "trait": trait_name,
            "name": slot_name,
        });
        let placeholder = descriptor_for(&projection, declarations, external_types)?;
        let name = context.associated_projection(&base, &trait_name, &slot_name)?;
        rendered = rendered.replace(
            &placeholder,
            &format!("_cott_type_{}", safe_internal_name(&name)),
        );
        rendered = rendered.replace(
            &associated_projection_name(&base, &trait_name, &slot_name)?,
            &name,
        );
    }
    Ok(rendered)
}

fn collect_type_parameters(value: &Value, output: &mut BTreeSet<String>) -> Result<(), String> {
    match value {
        Value::Array(values) => {
            for value in values {
                collect_type_parameters(value, output)?;
            }
        }
        Value::Object(object) => {
            if object.get("kind").and_then(Value::as_str) == Some("type_parameter") {
                output.insert(required_string(object, "name", "type parameter")?.to_owned());
                return Ok(());
            }
            for value in object.values() {
                collect_type_parameters(value, output)?;
            }
        }
        _ => {}
    }
    Ok(())
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

fn generic_const_kind(generic: &Value) -> Result<&'static str, String> {
    match generic.get("type").and_then(Value::as_str) {
        Some("u8" | "U8") => Ok("cott_runtime.CottIntKind.u8"),
        Some("u16" | "U16") => Ok("cott_runtime.CottIntKind.u16"),
        Some("u32" | "U32") => Ok("cott_runtime.CottIntKind.u32"),
        Some("u64" | "U64") => Ok("cott_runtime.CottIntKind.u64"),
        Some(other) => Err(format!("unsupported const generic integer kind `{other}`")),
        None => Err("const generic is missing integer type".to_owned()),
    }
}

fn render_callable_wrapper(
    config: &DartProjectConfig,
    plan: &DartPlan,
    callable: &DartCallable,
    binding: &DartBinding,
    declarations: &DeclarationIndex<'_>,
) -> Result<String, String> {
    let mut owner_witnesses = Vec::new();
    let declaration_value = if let Some(owner) = callable.owner.as_ref() {
        let owner = owner
            .as_object()
            .ok_or_else(|| format!("callable `{}` owner must be an object", callable.symbol))?;
        let slot = selected_method_slot(owner, callable)?;
        owner_witnesses = selected_owner_const_witnesses(slot, declarations)?;
        resolved_method_declaration(callable, owner, slot, declarations)?
    } else {
        callable.declaration.clone()
    };
    let declaration = declaration_value
        .as_object()
        .ok_or_else(|| format!("callable `{}` must be an object", callable.symbol))?;
    let mut out = generated_header().to_owned();
    let parsed = partition_source(&binding.bytes)
        .map_err(|error| format!("partition Dart binding `{}`: {error}", binding.cott_symbol))?;
    for import in &parsed.imports {
        writeln!(out, "{import}").expect("writing to String cannot fail");
    }
    writeln!(
        out,
        "part '{}';",
        package_uri(&config.project.name, &binding.runtime_origin)?
    )
    .expect("writing to String cannot fail");
    if parameters_have_defaults(declaration) {
        out.push_str(
            "\nenum _cott_omission { value }\nconst _cott_omitted = _cott_omission.value;\n",
        );
    }

    let rendering = callable_rendering(declaration, declarations, BTreeMap::new())?;
    let public_name = if callable.owner.is_none() {
        escape_identifier(&callable.name)?
    } else {
        callable_bridge_name(&callable.symbol)
    };
    let mut signature_parameters = Vec::new();
    if let Some(owner) = callable.owner.as_ref() {
        let concrete = owner
            .get("name")
            .and_then(Value::as_str)
            .ok_or_else(|| format!("method `{}` owner is missing name", callable.symbol))?;
        signature_parameters.push(format!("{} self", render_canonical_symbol(concrete, None)?));
    }
    signature_parameters.extend(render_parameters_contextual(
        declaration,
        callable.owner.is_none(),
        &rendering.context,
        &rendering.associated,
        if callable.owner.is_none() {
            ParameterSurface::Public
        } else {
            ParameterSurface::Implementation
        },
    )?);
    signature_parameters.extend(
        owner_witnesses
            .iter()
            .map(|witness| format!("{} {}", witness.ty, witness.name)),
    );
    let return_value = required(declaration, "return_type", &callable.symbol)?;
    let return_type = render_type_contextual(return_value, None, Some(&rendering.context))?;
    let asynchronous = declaration.get("callable_kind").and_then(Value::as_str) == Some("async");
    let rendered_return = if asynchronous {
        format!("Future<{return_type}>")
    } else {
        return_type
    };
    writeln!(
        out,
        "\n{rendered_return} {public_name}{}({}){} {{",
        rendering.generics,
        signature_parameters.join(", "),
        if asynchronous { " async" } else { "" }
    )
    .expect("writing to String cannot fail");
    render_identity_preflight(&mut out, config, 2);
    render_bound_checks(
        &mut out,
        &rendering.bounds,
        &callable.symbol,
        &rendering.context,
        declarations,
        &config.dart.external_types,
        2,
    )?;
    render_effect_checks(&mut out, config, declaration, &callable.symbol, 2)?;
    let locals = render_parameter_validation(
        &mut out,
        config,
        declaration,
        declarations,
        &rendering.context,
        2,
    )?;
    render_contract_clauses(
        &mut out,
        config,
        declaration,
        &callable.symbol,
        true,
        2,
        &locals,
        None,
        declarations.projection,
    )?;
    render_expected_errors(
        &mut out,
        config,
        declaration,
        &callable.symbol,
        2,
        &locals,
        None,
        true,
        declarations.projection,
    )?;
    let mut call_arguments = Vec::new();
    if callable.owner.is_some() {
        call_arguments.push("self".to_owned());
    }
    call_arguments.extend(render_call_arguments(
        declaration,
        &locals,
        &rendering.associated,
    )?);
    call_arguments.extend(owner_witnesses.iter().map(|witness| witness.name.clone()));
    let target = binding_private_name(binding)?;
    writeln!(out, "  Object? _cott_raw_result;").expect("writing to String cannot fail");
    writeln!(out, "  try {{").expect("writing to String cannot fail");
    writeln!(
        out,
        "    _cott_raw_result = {}{target}({});",
        if asynchronous { "await " } else { "" },
        call_arguments.join(", ")
    )
    .expect("writing to String cannot fail");
    writeln!(
        out,
        "  }} catch (error, stackTrace) {{\n    cott_runtime.CottRuntime.rethrowImplementation(error, stackTrace, {}, asynchronous: {});\n  }}",
        dart_string(&callable.symbol),
        asynchronous
    )
    .expect("writing to String cannot fail");
    if is_never(return_value) {
        writeln!(
            out,
            "  return cott_runtime.CottRuntime.violation('Never callable returned', symbol: {}, phase: 'return', expected: 'Never', actual: '$_cott_raw_result');",
            dart_string(&callable.symbol)
        )
        .expect("writing to String cannot fail");
    } else {
        let descriptor = descriptor_for_contextual(
            return_value,
            declarations,
            &config.dart.external_types,
            &rendering.context,
        )?;
        writeln!(
            out,
            "  final _cott_result = cott_runtime.CottRuntime.returnValue(_cott_raw_result, {descriptor}, mode: {}, path: r'$.return');",
            runtime_mode(config)
        )
        .expect("writing to String cannot fail");
        render_contract_clauses(
            &mut out,
            config,
            declaration,
            &callable.symbol,
            false,
            2,
            &locals,
            None,
            declarations.projection,
        )?;
        render_error_contracts(&mut out, config, declaration, &callable.symbol, 2)?;
        out.push_str("  return _cott_result;\n");
    }
    out.push_str("}\n");
    let imports = common_imports(config, plan, None, true)?;
    let imports = render_used_imports(&imports, &[out.as_str(), parsed.body.as_str()])?;
    out.insert_str(generated_header().len(), &imports);
    Ok(finish_source(out))
}

fn callable_bridge_name(symbol: &str) -> String {
    format!("cottInvoke_{}", &sha256_hex(symbol.as_bytes())[..24])
}

fn render_effect_checks(
    out: &mut String,
    config: &DartProjectConfig,
    declaration: &Map<String, Value>,
    symbol: &str,
    indent: usize,
) -> Result<(), String> {
    let prefix = " ".repeat(indent);
    for effect in declaration
        .get("contract")
        .and_then(Value::as_object)
        .and_then(|contract| contract.get("effects"))
        .or_else(|| declaration.get("effects"))
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
    {
        let key = effect
            .get("key")
            .and_then(Value::as_str)
            .ok_or_else(|| format!("effect on `{symbol}` is missing key"))?;
        let allowed =
            INTRINSIC_EFFECTS.contains(&key) || config.effects.get(key).copied().unwrap_or(false);
        writeln!(
            out,
            "{prefix}cott_runtime.CottRuntime.requireEffect({allowed}, {}, {}, span: {});",
            dart_string(key),
            dart_string(symbol),
            render_span(effect.get("span"))?
        )
        .expect("writing to String cannot fail");
    }
    Ok(())
}

fn render_parameter_validation(
    out: &mut String,
    config: &DartProjectConfig,
    declaration: &Map<String, Value>,
    declarations: &DeclarationIndex<'_>,
    context: &EmissionTypeContext<'_>,
    indent: usize,
) -> Result<BTreeMap<String, String>, String> {
    let prefix = " ".repeat(indent);
    let mut locals = BTreeMap::new();
    for parameter in required_array(declaration, "parameters", "callable")? {
        let parameter = parameter
            .as_object()
            .ok_or_else(|| "callable parameter must be an object".to_owned())?;
        let name = required_string(parameter, "name", "callable parameter")?;
        let escaped = escape_identifier(name)?;
        let input = if let Some(default) = parameter.get("default").filter(|value| !value.is_null())
        {
            let input = format!("_cott_input_{}", safe_internal_name(name));
            writeln!(
                out,
                "{prefix}final {input} = identical({escaped}, _cott_omitted) ? {} : {escaped};",
                render_value_contextual(
                    default,
                    parameter.get("type"),
                    declaration
                        .get("name")
                        .and_then(Value::as_str)
                        .and_then(module_of),
                    declarations.projection,
                )?
            )
            .expect("writing to String cannot fail");
            input
        } else {
            escaped
        };
        let local = format!("_cott_arg_{}", safe_internal_name(name));
        let kind = required_string(parameter, "kind", name)?;
        let item_descriptor = descriptor_for_contextual(
            required(parameter, "type", name)?,
            declarations,
            &config.dart.external_types,
            context,
        )?;
        let descriptor = match kind {
            "vararg" => format!("cott_runtime.CottTypes.list({item_descriptor})"),
            "kwarg" => format!("cott_runtime.CottTypes.keywordArguments({item_descriptor})"),
            "positional" | "keyword_only" => item_descriptor,
            other => return Err(format!("unsupported canonical parameter kind `{other}`")),
        };
        writeln!(
            out,
            "{prefix}final {local} = cott_runtime.CottRuntime.abi({input}, {descriptor}, mode: {}, path: {});",
            runtime_mode(config),
            dart_string(&format!("$.{name}"))
        )
        .expect("writing to String cannot fail");
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
            "{prefix}cott_runtime.CottRuntime.validateConst(_cott_const_{}, {}, path: {});",
            safe_internal_name(name),
            generic_const_kind(generic)?,
            dart_string(&format!("$.const.{name}"))
        )
        .expect("writing to String cannot fail");
    }
    Ok(locals)
}

fn render_call_arguments(
    declaration: &Map<String, Value>,
    locals: &BTreeMap<String, String>,
    associated: &[String],
) -> Result<Vec<String>, String> {
    let mut values = required_array(declaration, "parameters", "callable")?
        .iter()
        .map(|parameter| {
            let name = parameter
                .get("name")
                .and_then(Value::as_str)
                .ok_or_else(|| "callable parameter is missing name".to_owned())?;
            locals
                .get(name)
                .cloned()
                .ok_or_else(|| format!("missing validated parameter `{name}`"))
        })
        .collect::<Result<Vec<_>, String>>()?;
    values.extend(
        declaration
            .get("generics")
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
            .filter(|generic| generic.get("kind").and_then(Value::as_str) == Some("type"))
            .filter_map(|generic| generic.get("name").and_then(Value::as_str))
            .map(|name| format!("_cott_type_{}", safe_internal_name(name))),
    );
    values.extend(
        associated
            .iter()
            .map(|name| format!("_cott_type_{}", safe_internal_name(name))),
    );
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
    Ok(values)
}

fn contract_clauses(declaration: &Map<String, Value>) -> impl Iterator<Item = &Value> {
    let ordinary = declaration
        .get("contract")
        .and_then(Value::as_object)
        .and_then(|contract| contract.get("clauses"))
        .and_then(Value::as_array);
    let grouped = if ordinary.is_none() {
        declaration.get("contracts").and_then(Value::as_object)
    } else {
        None
    };
    ordinary
        .into_iter()
        .flatten()
        .chain(
            ["requires", "errors", "ensures"]
                .into_iter()
                .flat_map(move |kind| {
                    grouped
                        .and_then(|contracts| contracts.get(kind))
                        .and_then(Value::as_array)
                        .into_iter()
                        .flatten()
                }),
        )
}

fn render_contract_clauses(
    out: &mut String,
    config: &DartProjectConfig,
    declaration: &Map<String, Value>,
    symbol: &str,
    pre: bool,
    indent: usize,
    locals: &BTreeMap<String, String>,
    module: Option<&str>,
    projection: &DartEnumProjection,
) -> Result<(), String> {
    let clauses = contract_clauses(declaration)
        .filter(|clause| {
            let kind = clause.get("kind").and_then(Value::as_str);
            (pre && kind == Some("requires")) || (!pre && kind == Some("ensures"))
        })
        .collect::<Vec<_>>();
    if clauses.is_empty() {
        return Ok(());
    }
    let prefix = " ".repeat(indent);
    let nested = " ".repeat(indent + 2);
    writeln!(
        out,
        "{prefix}if (cott_runtime.CottRuntime.shouldValidate({})) {{",
        runtime_mode(config)
    )
    .expect("writing to String cannot fail");
    for clause in clauses {
        let kind = clause
            .get("kind")
            .and_then(Value::as_str)
            .ok_or_else(|| format!("contract clause on `{symbol}` is missing kind"))?;
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
        rewrite_const_references_for_callable(&mut expression, declaration);
        if let Some(guard) = &mut guard {
            rewrite_const_references_for_callable(guard, declaration);
        }
        let condition = render_condition(&expression, None, true, module, projection)?;
        let label = clause_label(clause)?;
        let statement = format!(
            "cott_runtime.CottRuntime.checkContract({condition}, {}, {}, clause: {}, span: {}, expected: 'true', actual: 'false');",
            dart_string(symbol),
            dart_string(kind),
            dart_string(&label),
            render_span(clause.get("span"))?
        );
        writeln!(
            out,
            "{nested}{}",
            super::expressions::render_guarded_statement(
                guard.as_ref(),
                &statement,
                module,
                projection
            )?
        )
        .expect("writing to String cannot fail");
    }
    writeln!(out, "{prefix}}}").expect("writing to String cannot fail");
    Ok(())
}

fn render_expected_errors(
    out: &mut String,
    config: &DartProjectConfig,
    declaration: &Map<String, Value>,
    symbol: &str,
    indent: usize,
    locals: &BTreeMap<String, String>,
    module: Option<&str>,
    declare: bool,
    projection: &DartEnumProjection,
) -> Result<(), String> {
    let errors = contract_clauses(declaration)
        .filter(|clause| clause.get("kind").and_then(Value::as_str) == Some("error"))
        .collect::<Vec<_>>();
    if !checks_error_return(declaration) {
        return Ok(());
    }
    let prefix = " ".repeat(indent);
    if declare {
        writeln!(out, "{prefix}String? _cott_expected_error = null;")
            .expect("writing to String cannot fail");
        if errors.iter().copied().any(conditional_error) {
            writeln!(out, "{prefix}String? _cott_expected_error_clause = null;")
                .expect("writing to String cannot fail");
        }
    }
    writeln!(
        out,
        "{prefix}if (cott_runtime.CottRuntime.shouldValidate({})) {{",
        runtime_mode(config)
    )
    .expect("writing to String cannot fail");
    let nested = " ".repeat(indent + 2);
    for clause in errors {
        let mut guard = clause.get("guard").cloned();
        if let Some(guard) = &mut guard {
            rewrite_parameter_references(guard, locals);
            rewrite_const_references_for_callable(guard, declaration);
        }
        let condition = match clause.get("when").filter(|value| !value.is_null()) {
            Some(expression) => {
                let mut expression = expression.clone();
                rewrite_parameter_references(&mut expression, locals);
                rewrite_const_references_for_callable(&mut expression, declaration);
                render_condition(&expression, guard.as_ref(), false, module, projection)?
            }
            None if guard.as_ref().is_some_and(|guard| !guard.is_null()) => {
                let literal = serde_json::json!({
                    "kind": "literal",
                    "value": {"kind": "bool", "value": true},
                    "type": {"kind": "primitive", "name": "bool"}
                });
                super::expressions::render_guard(
                    guard.as_ref().expect("checked guard"),
                    &literal,
                    false,
                    module,
                    projection,
                )?
            }
            None => continue,
        };
        let variant = clause
            .get("variant")
            .and_then(Value::as_str)
            .ok_or_else(|| format!("error clause on `{symbol}` is missing variant"))?;
        writeln!(
            out,
            "{nested}if (_cott_expected_error == null && ({condition})) {{ _cott_expected_error = {}; _cott_expected_error_clause = {}; }}",
            dart_string(variant),
            dart_string(&clause_label(clause)?),
        )
        .expect("writing to String cannot fail");
    }
    writeln!(out, "{prefix}}}").expect("writing to String cannot fail");
    Ok(())
}

fn render_error_contracts(
    out: &mut String,
    config: &DartProjectConfig,
    declaration: &Map<String, Value>,
    symbol: &str,
    indent: usize,
) -> Result<(), String> {
    let errors = contract_clauses(declaration)
        .filter(|clause| clause.get("kind").and_then(Value::as_str) == Some("error"))
        .collect::<Vec<_>>();
    if !checks_error_return(declaration) {
        return Ok(());
    }
    let prefix = " ".repeat(indent);
    let unconditional = errors
        .iter()
        .copied()
        .filter(|clause| !conditional_error(clause))
        .filter_map(|clause| clause.get("variant").and_then(Value::as_str))
        .map(dart_string)
        .collect::<Vec<_>>();
    writeln!(
        out,
        "{prefix}if (cott_runtime.CottRuntime.shouldValidate({})) {{\n{prefix}  final _cott_actual_error = cott_runtime.CottRuntime.resultError(_cott_result);\n{prefix}  final _cott_actual_error_variant = _cott_actual_error is cott_runtime.CottVariant ? _cott_actual_error.cottVariant : null;\n{prefix}  const _cott_allowed_errors = <String>{{{}}};\n{prefix}  cott_runtime.CottRuntime.checkContract(_cott_expected_error != null ? _cott_actual_error_variant == _cott_expected_error : _cott_actual_error == null || _cott_allowed_errors.contains(_cott_actual_error_variant), {}, 'error', clause: 'error-return', expected: _cott_expected_error ?? '$_cott_allowed_errors', actual: _cott_actual_error_variant ?? _cott_actual_error?.runtimeType.toString());",
        runtime_mode(config),
        unconditional.join(", "),
        dart_string(symbol)
    )
    .expect("writing to String cannot fail");
    for clause in errors {
        let label = clause_label(clause)?;
        let variant = required_string(
            clause.as_object().ok_or("error clause must be an object")?,
            "variant",
            symbol,
        )?;
        let applicable = if !conditional_error(clause) {
            format!("_cott_actual_error_variant == {}", dart_string(variant))
        } else {
            format!("_cott_expected_error_clause == {}", dart_string(&label))
        };
        writeln!(
            out,
            "{prefix}  if ({applicable}) cott_runtime.CottRuntime.checkContract(_cott_actual_error_variant == {}, {}, 'error', clause: {}, span: {});",
            dart_string(variant),
            dart_string(symbol),
            dart_string(&label),
            render_span(clause.get("span"))?,
        )
        .expect("writing to String cannot fail");
    }
    writeln!(out, "{prefix}}}").expect("writing to String cannot fail");
    Ok(())
}

/// A guarded or `when` error clause selects the expected variant before the call; only such
/// clauses assign and read `_cott_expected_error_clause`, so the local exists only with them.
fn conditional_error(clause: &Value) -> bool {
    clause.get("guard").is_some_and(|guard| !guard.is_null())
        || clause.get("when").is_some_and(|when| !when.is_null())
}

/// `true` when the facade checks a returned `Err` as the `error-return` observation: with any
/// `error` clause, and with `errors complete` even without one, when every requires-valid
/// input must return `Ok`.
pub(crate) fn checks_error_return(declaration: &Map<String, Value>) -> bool {
    contract_clauses(declaration)
        .any(|clause| clause.get("kind").and_then(Value::as_str) == Some("error"))
        || crate::ir::complete_errors(declaration) == Ok(true)
}

fn render_facade_file(
    config: &DartProjectConfig,
    module: &DartModule,
    callables: &BTreeMap<String, &DartCallable>,
    bindings: &BTreeMap<&str, &DartBinding>,
    declarations: &DeclarationIndex<'_>,
) -> Result<String, String> {
    let mut out = generated_header().to_owned();
    writeln!(
        out,
        "export '{}';",
        package_uri(&config.project.name, &types_path(&module.name)?)?
    )
    .expect("writing to String cannot fail");
    let marker_exports = module_marker_exports(module)?;
    if !marker_exports.is_empty() {
        writeln!(
            out,
            "export '{}' show {};",
            package_uri(
                &config.project.name,
                Path::new("dart/lib/src/cott_markers.dart")
            )?,
            marker_exports.join(", ")
        )
        .expect("writing to String cannot fail");
    }
    for callable in callables
        .values()
        .copied()
        .filter(|callable| callable.module == module.name && callable.owner.is_none())
    {
        if !bindings.contains_key(callable.symbol.as_str()) {
            continue;
        }
        let declaration = callable
            .declaration
            .as_object()
            .ok_or_else(|| format!("callable `{}` must be an object", callable.symbol))?;
        if declaration.get("public").and_then(Value::as_bool) != Some(true) {
            continue;
        }
        writeln!(
            out,
            "export '{}' show {};",
            package_uri(&config.project.name, &wrapper_path(callable)?)?,
            escape_identifier(&callable.name)?
        )
        .expect("writing to String cannot fail");
    }
    let _ = declarations;
    Ok(finish_source(out))
}

fn implementation_resolved(
    concrete: &str,
    implementation: &Map<String, Value>,
    bindings: &BTreeMap<&str, &DartBinding>,
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

fn render_implementation_library(
    config: &DartProjectConfig,
    plan: &DartPlan,
    implementation: &Map<String, Value>,
    declarations: &DeclarationIndex<'_>,
    callables: &BTreeMap<String, &DartCallable>,
    bindings: &BTreeMap<&str, &DartBinding>,
) -> Result<String, String> {
    let canonical = required_string(implementation, "name", "implementation")?;
    let module = module_of(canonical);
    let name = escape_identifier(local_name(canonical))?;
    let mut out = generated_header().to_owned();
    let selected = required_array(implementation, "selected_methods", canonical)?;
    let mut bridge_targets = BTreeMap::new();
    let mut authored_imports = Vec::new();
    let mut seen_authored_imports = BTreeSet::new();
    let mut parts = Vec::new();
    let mut private_sources = Vec::new();
    for slot in selected {
        let callable = selected_callable(canonical, slot, callables)?;
        let selection = slot
            .get("selected")
            .and_then(Value::as_object)
            .ok_or_else(|| {
                format!(
                    "selected method `{}` is missing provenance",
                    callable.symbol
                )
            })?;
        if selection.get("origin").and_then(Value::as_str) == Some("explicit") {
            let binding = bindings
                .get(callable.symbol.as_str())
                .copied()
                .ok_or_else(|| {
                    format!(
                        "resolved implementation `{canonical}` has no binding for `{}`",
                        callable.symbol
                    )
                })?;
            let parsed = partition_source(&binding.bytes).map_err(|error| {
                format!("partition Dart binding `{}`: {error}", binding.cott_symbol)
            })?;
            for import in parsed.imports {
                if seen_authored_imports.insert(import.clone()) {
                    authored_imports.push(import);
                }
            }
            private_sources.push(parsed.body);
            parts.push(format!(
                "part '{}';",
                package_uri(&config.project.name, &binding.runtime_origin)?
            ));
            bridge_targets.insert(
                callable.symbol.clone(),
                binding_private_name(binding)?.to_owned(),
            );
        } else {
            let target = selected_bridge_callable(slot, callable, callables)?;
            if !bindings.contains_key(target.symbol.as_str()) {
                return Err(format!(
                    "resolved implementation `{canonical}` bridge `{}` has no binding",
                    target.symbol
                ));
            }
            let prefix = format!("_cott_w_{}", &sha256_hex(target.symbol.as_bytes())[..16]);
            writeln!(
                out,
                "import '{}' as {prefix};",
                package_uri(&config.project.name, &wrapper_path(target)?)?
            )
            .expect("writing to String cannot fail");
            if target.owner.is_some() {
                return Err(format!(
                    "default bridge `{}` unexpectedly belongs to an implementation owner",
                    target.symbol
                ));
            }
            bridge_targets.insert(
                callable.symbol.clone(),
                format!("{prefix}.{}", escape_identifier(&target.name)?),
            );
        }
    }
    for import in authored_imports {
        writeln!(out, "{import}").expect("writing to String cannot fail");
    }
    for part in parts {
        writeln!(out, "{part}").expect("writing to String cannot fail");
    }
    let traits = required_array(implementation, "traits", canonical)?
        .iter()
        .map(|trait_ref| {
            render_trait_reference(trait_ref, Some(implementation), declarations, None, None)
        })
        .collect::<Result<Vec<_>, _>>()?;
    if implementation
        .get("init")
        .and_then(Value::as_object)
        .is_some_and(parameters_have_defaults)
        || selected
            .iter()
            .filter_map(Value::as_object)
            .any(parameters_have_defaults)
    {
        out.push_str(
            "\nenum _cott_omission { value }\nconst _cott_omitted = _cott_omission.value;\n",
        );
    }
    let state = required_array(implementation, "state", canonical)?;
    let initializer = implementation.get("init").and_then(Value::as_object);
    let constructor_parameters = initializer
        .map(|initializer| {
            let context = EmissionTypeContext::new(declarations);
            render_parameters_contextual(initializer, true, &context, &[], ParameterSurface::Public)
        })
        .transpose()?
        .unwrap_or_default();
    writeln!(
        out,
        "\nfinal class {name} implements {}, cott_runtime.CottFieldValue, cott_runtime.CottTraitCarrier {{",
        traits.join(", ")
    )
    .expect("writing to String cannot fail");
    out.push_str("  final cott_runtime.CottResourceGuard _cott_resource_guard = cott_runtime.CottResourceGuard();\n");
    for field in state {
        let field = field
            .as_object()
            .ok_or_else(|| format!("implementation `{canonical}` state field must be object"))?;
        let field_name = required_string(field, "name", canonical)?;
        writeln!(
            out,
            "  late {} _cott_state_{};\n  {} get {} => _cott_state_{};",
            render_contextual_type(required(field, "type", canonical)?, None, declarations)?,
            safe_internal_name(field_name),
            render_contextual_type(required(field, "type", canonical)?, None, declarations)?,
            escape_identifier(field_name)?,
            safe_internal_name(field_name)
        )
        .expect("writing to String cannot fail");
    }
    let trait_tokens = trait_specializations(implementation, declarations)?
        .iter()
        .map(|trait_ref| trait_marker(trait_ref).map(|name| format!("cott_markers.{name}")))
        .collect::<Result<Vec<_>, _>>()?;
    writeln!(
        out,
        "\n  @override\n  cott_runtime.CottSet<cott_runtime.CottTrait<dynamic>> get cottTraits => cott_runtime.CottSet([{}]);",
        trait_tokens.join(", ")
    )
    .expect("writing to String cannot fail");
    render_implementation_descriptor(&mut out, implementation, declarations)?;
    for trait_ref in trait_specializations(implementation, declarations)? {
        let object = trait_ref
            .as_object()
            .ok_or_else(|| "implementation trait reference must be an object".to_owned())?;
        let trait_name = required_string(object, "name", canonical)?;
        let (_, trait_declaration) = declarations
            .get(trait_name)
            .copied()
            .ok_or_else(|| format!("unknown implementation trait `{trait_name}`"))?;
        for (parameter, argument) in required_array(trait_declaration, "generics", trait_name)?
            .iter()
            .zip(required_array(object, "args", trait_name)?)
            .filter(|(parameter, _)| parameter.get("kind").and_then(Value::as_str) == Some("const"))
        {
            let parameter_name = parameter
                .get("name")
                .and_then(Value::as_str)
                .ok_or_else(|| format!("trait `{trait_name}` const generic is missing name"))?;
            let value = required_value(argument, "value", trait_name)?;
            writeln!(
                out,
                "  @override\n  {} get cottConst{} => {};",
                types::render_const_marker(value)?,
                pascal_identifier(parameter_name)?,
                render_const_witness(value)?
            )
            .expect("writing to String cannot fail");
        }
    }
    writeln!(out, "\n  {name}({}) {{", constructor_parameters.join(", "))
        .expect("writing to String cannot fail");
    render_identity_preflight(&mut out, config, 4);
    let implementation_checks =
        implementation_bound_checks(implementation, declarations, &config.dart.external_types)?;
    render_bound_checks(
        &mut out,
        &implementation_checks,
        canonical,
        &EmissionTypeContext::new(declarations),
        declarations,
        &config.dart.external_types,
        4,
    )?;
    let mut initializer_locals = BTreeMap::new();
    if let Some(initializer) = initializer {
        let symbol = format!("{canonical}.init");
        render_effect_checks(&mut out, config, initializer, &symbol, 4)?;
        initializer_locals = render_parameter_validation(
            &mut out,
            config,
            initializer,
            declarations,
            &EmissionTypeContext::new(declarations),
            4,
        )?;
        render_contract_clauses(
            &mut out,
            config,
            initializer,
            &symbol,
            true,
            4,
            &initializer_locals,
            module,
            declarations.projection,
        )?;
    }
    for field in state {
        let field = field.as_object().expect("validated state field");
        let field_name = required_string(field, "name", canonical)?;
        let initializer_parameter = initializer.and_then(|initializer| {
            initializer
                .get("parameters")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
                .find(|parameter| parameter.get("name").and_then(Value::as_str) == Some(field_name))
        });
        let initial = if initializer_parameter.is_some() {
            initializer_locals
                .get(field_name)
                .cloned()
                .ok_or_else(|| format!("missing validated initializer parameter `{field_name}`"))?
        } else {
            render_value_contextual(
                field
                    .get("default")
                    .filter(|value| !value.is_null())
                    .ok_or_else(|| {
                        format!(
                            "implementation `{canonical}` state field `{field_name}` has neither initializer parameter nor default"
                        )
                    })?,
                field.get("type"),
                module,
                declarations.projection,
            )?
        };
        writeln!(
            out,
            "    _cott_state_{} = cott_runtime.CottRuntime.abi({initial}, {}, mode: {}, path: {});",
            safe_internal_name(field_name),
            descriptor_for(
                required(field, "type", canonical)?,
                declarations,
                &config.dart.external_types
            )?,
            "cott_runtime.RuntimeValidation.boundary",
            dart_string(&format!("$.{field_name}"))
        )
        .expect("writing to String cannot fail");
    }
    if let Some(initializer) = initializer {
        render_contract_clauses(
            &mut out,
            config,
            initializer,
            &format!("{canonical}.init"),
            false,
            4,
            &initializer_locals,
            module,
            declarations.projection,
        )?;
    }
    writeln!(
        out,
        "    _cott_resource({}, const <String>{{}}, const <cott_runtime.CottTransition>[]).validateInitial();\n  }}",
        dart_string(canonical)
    )
    .expect("writing to String cannot fail");
    render_implementation_metadata(&mut out, canonical, state)?;
    render_resource_factory(&mut out, config, implementation, declarations, state)?;
    for slot in selected {
        let callable = selected_callable(canonical, slot, callables)?;
        let target = bridge_targets
            .get(&callable.symbol)
            .ok_or_else(|| format!("selected method `{}` has no bridge target", callable.symbol))?;
        render_impl_method(
            &mut out,
            config,
            implementation,
            slot,
            callable,
            target,
            declarations,
        )?;
    }
    out.push_str("}\n");
    let mut sources = Vec::with_capacity(private_sources.len() + 1);
    sources.push(out.as_str());
    sources.extend(private_sources.iter().map(String::as_str));
    let imports = common_imports(config, plan, None, true)?;
    let imports = render_used_imports(&imports, &sources)?;
    out.insert_str(generated_header().len(), &imports);
    Ok(finish_source(out))
}

fn selected_callable<'a>(
    concrete: &str,
    slot: &Value,
    callables: &'a BTreeMap<String, &DartCallable>,
) -> Result<&'a DartCallable, String> {
    let method = slot
        .get("trait_method")
        .and_then(Value::as_str)
        .map(local_name)
        .ok_or_else(|| format!("implementation `{concrete}` selected slot is missing method"))?;
    let symbol = format!("{concrete}.{method}");
    callables
        .get(&symbol)
        .copied()
        .ok_or_else(|| format!("selected method `{symbol}` absent from Dart plan"))
}

fn selected_bridge_callable<'a>(
    slot: &Value,
    explicit: &'a DartCallable,
    callables: &'a BTreeMap<String, &DartCallable>,
) -> Result<&'a DartCallable, String> {
    let selected = slot
        .get("selected")
        .and_then(Value::as_object)
        .ok_or_else(|| {
            format!(
                "selected method `{}` is missing provenance",
                explicit.symbol
            )
        })?;
    match selected.get("origin").and_then(Value::as_str) {
        Some("explicit") => Ok(explicit),
        Some("default" | "specialization") => {
            let symbol = selected
                .get("function")
                .and_then(Value::as_object)
                .and_then(|function| function.get("verified_facade"))
                .and_then(Value::as_str)
                .ok_or_else(|| {
                    format!(
                        "default method `{}` has no verified facade",
                        explicit.symbol
                    )
                })?;
            callables
                .get(symbol)
                .copied()
                .ok_or_else(|| format!("default facade `{symbol}` absent from Dart plan"))
        }
        other => Err(format!(
            "selected method `{}` has unsupported origin `{other:?}`",
            explicit.symbol
        )),
    }
}

fn render_implementation_metadata(
    out: &mut String,
    canonical: &str,
    state: &[Value],
) -> Result<(), String> {
    writeln!(
        out,
        "\n  @override\n  String get cottTypeIdentity => {};",
        dart_string(canonical)
    )
    .expect("writing to String cannot fail");
    let names = state
        .iter()
        .filter_map(|field| field.get("name").and_then(Value::as_str))
        .collect::<Vec<_>>();
    writeln!(
        out,
        "  @override\n  cott_runtime.CottList<String> get cottFieldNames => cott_runtime.CottList([{}]);\n  @override\n  Object? cottField(String _cott_field) => switch (_cott_field) {{",
        names.iter().map(|name| dart_string(name)).collect::<Vec<_>>().join(", ")
    )
    .expect("writing to String cannot fail");
    for name in names {
        writeln!(
            out,
            "    {} => {},",
            dart_string(name),
            escape_identifier(name)?
        )
        .expect("writing to String cannot fail");
    }
    out.push_str("    _ => cott_runtime.CottRuntime.violation('unknown canonical field', symbol: cottTypeIdentity, phase: 'field', actual: _cott_field),\n  };\n");
    Ok(())
}

fn render_resource_factory(
    out: &mut String,
    config: &DartProjectConfig,
    implementation: &Map<String, Value>,
    declarations: &DeclarationIndex<'_>,
    state: &[Value],
) -> Result<(), String> {
    let canonical = required_string(implementation, "name", "implementation")?;
    writeln!(
        out,
        "\n  cott_runtime.CottResourceContract _cott_resource(String symbol, Set<String> modifies, List<cott_runtime.CottTransition> transitions) => cott_runtime.CottResourceContract(\n    symbol: symbol,\n    fields: ["
    )
    .expect("writing to String cannot fail");
    for field in state {
        let name = field
            .get("name")
            .and_then(Value::as_str)
            .ok_or_else(|| format!("state field on `{canonical}` is missing name"))?;
        writeln!(
            out,
            "      cott_runtime.CottStateField(name: {}, type: ({} as cott_runtime.CottType<Object?>), read: () => _cott_state_{}, write: (value) => _cott_state_{} = value as {}),",
            dart_string(name),
            descriptor_for(
                required_value(field, "type", canonical)?,
                declarations,
                &config.dart.external_types
            )?,
            safe_internal_name(name),
            safe_internal_name(name),
            render_contextual_type(
                required_value(field, "type", canonical)?,
                None,
                declarations
            )?
        )
        .expect("writing to String cannot fail");
    }
    let invariants = implementation
        .get("invariants")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .map(|invariant| {
            let expression = render_condition(
                required_value(invariant, "expression", canonical)?,
                None,
                true,
                module_of(canonical),
                declarations.projection,
            )?;
            let clause = format!(
                "invariant:{}",
                invariant
                    .get("clause_id")
                    .and_then(Value::as_u64)
                    .ok_or_else(|| "implementation invariant is missing clause_id".to_owned())?
            );
            let statement = format!(
                "cott_runtime.CottRuntime.invariant({expression}, symbol, clause: {}, span: {}, expected: 'true', actual: 'false');",
                dart_string(&clause),
                render_span(invariant.get("span"))?
            );
            Ok(format!(
                "cott_runtime.CottInvariant.checked(clause: {}, check: () {{ {} }}, span: {})",
                dart_string(&clause),
                super::expressions::render_guarded_statement(
                    invariant.get("guard"),
                    &statement,
                    module_of(canonical),
                    declarations.projection,
                )?,
                render_span(invariant.get("span"))?
            ))
        })
        .collect::<Result<Vec<_>, String>>()?;
    writeln!(
        out,
        "    ],\n    modifies: modifies,\n    transitions: transitions,\n    invariants: [{}],\n    guard: _cott_resource_guard,\n  );",
        invariants.join(", ")
    )
    .expect("writing to String cannot fail");
    Ok(())
}

fn render_impl_method(
    out: &mut String,
    config: &DartProjectConfig,
    implementation: &Map<String, Value>,
    slot: &Value,
    callable: &DartCallable,
    target: &str,
    declarations: &DeclarationIndex<'_>,
) -> Result<(), String> {
    let slot = slot
        .as_object()
        .ok_or_else(|| format!("selected method `{}` must be an object", callable.symbol))?;
    let method_value = resolved_method_declaration(callable, implementation, slot, declarations)?;
    let method = method_value
        .as_object()
        .ok_or_else(|| format!("resolved method `{}` must be an object", callable.symbol))?;
    let rendering = callable_rendering(method, declarations, BTreeMap::new())?;
    let asynchronous = method.get("callable_kind").and_then(Value::as_str) == Some("async");
    let return_value = required(method, "return_type", &callable.symbol)?;
    let return_type = render_type_contextual(return_value, None, Some(&rendering.context))?;
    let rendered_return = if asynchronous {
        format!("Future<{return_type}>")
    } else {
        return_type
    };
    let mut parameters = render_parameters_contextual(
        method,
        true,
        &rendering.context,
        &rendering.associated,
        ParameterSurface::Public,
    )?;
    if let Some(last) = parameters.last_mut().filter(|value| value.starts_with('{')) {
        last.pop();
        if last.len() > 1 {
            last.push_str(", ");
        }
        last.push_str("cott_runtime.CottGuardLease? cottLease}");
    } else if let Some(last) = parameters.last_mut().filter(|value| value.starts_with('[')) {
        last.pop();
        if last.len() > 1 {
            last.push_str(", ");
        }
        last.push_str("cott_runtime.CottGuardLease? cottLease]");
    } else {
        parameters.push("{cott_runtime.CottGuardLease? cottLease}".to_owned());
    }
    writeln!(
        out,
        "\n  @override\n  {rendered_return} {}{}({}){} {{",
        escape_identifier(&callable.name)?,
        rendering.generics,
        parameters.join(", "),
        if asynchronous { " async" } else { "" }
    )
    .expect("writing to String cannot fail");
    render_identity_preflight(out, config, 4);
    render_bound_checks(
        out,
        &rendering.bounds,
        &callable.symbol,
        &rendering.context,
        declarations,
        &config.dart.external_types,
        4,
    )?;
    render_effect_checks(out, config, method, &callable.symbol, 4)?;
    let locals =
        render_parameter_validation(out, config, method, declarations, &rendering.context, 4)?;
    let errors = contract_clauses(method)
        .filter(|clause| clause.get("kind").and_then(Value::as_str) == Some("error"))
        .collect::<Vec<_>>();
    if !errors.is_empty() {
        out.push_str("    String? _cott_expected_error = null;\n");
        if errors.iter().copied().any(conditional_error) {
            out.push_str("    String? _cott_expected_error_clause = null;\n");
        }
    }
    let state = required_array(implementation, "state", &callable.symbol)?;
    let old_state_fields = old_state_field_references(method)?;
    let state_names = state
        .iter()
        .map(|field| {
            field
                .get("name")
                .and_then(Value::as_str)
                .ok_or_else(|| format!("state field on `{}` is missing name", callable.symbol))
                .map(local_name)
                .map(str::to_owned)
        })
        .collect::<Result<BTreeSet<_>, _>>()?;
    for name in &old_state_fields {
        if !state_names.contains(name) {
            return Err(format!(
                "method `{}` references unknown old state field `{name}`",
                callable.symbol
            ));
        }
    }
    for field in state {
        let name = field
            .get("name")
            .and_then(Value::as_str)
            .ok_or_else(|| format!("state field on `{}` is missing name", callable.symbol))?;
        if !old_state_fields.contains(local_name(name)) {
            continue;
        }
        writeln!(out, "    Object? _cott_old_{};", safe_internal_name(name))
            .expect("writing to String cannot fail");
    }
    let modifies = method
        .get("modifies")
        .and_then(Value::as_array)
        .map(Vec::as_slice)
        .unwrap_or_default()
        .iter()
        .filter_map(Value::as_str)
        .map(local_name)
        .map(dart_string)
        .collect::<Vec<_>>();
    let transitions = method
        .get("transitions")
        .and_then(Value::as_array)
        .map(Vec::as_slice)
        .unwrap_or_default()
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
                "cott_runtime.CottTransition(field: {}, from: {}, to: {})",
                dart_string(local_name(field)),
                resource_state_name(from, None)?,
                resource_state_name(to, None)?
            ))
        })
        .collect::<Result<Vec<_>, String>>()?;
    writeln!(
        out,
        "    final _cott_resource_contract = _cott_resource({}, <String>{{{}}}, <cott_runtime.CottTransition>[{}]);",
        dart_string(&callable.symbol),
        modifies.join(", "),
        transitions.join(", ")
    )
    .expect("writing to String cannot fail");
    let owner_witnesses = selected_owner_const_witnesses(slot, declarations)?;
    let mut arguments = vec!["this".to_owned()];
    arguments.extend(render_call_arguments(
        method,
        &locals,
        &rendering.associated,
    )?);
    arguments.extend(owner_witnesses.iter().map(|witness| {
        let suffix = witness
            .name
            .strip_prefix("_cott_const_")
            .unwrap_or(&witness.name);
        format!(
            "cottConst{}",
            pascal_identifier(suffix).unwrap_or_else(|_| "Value".to_owned())
        )
    }));
    if callable_modifies_state(method) {
        arguments.push("_cott_mutation".to_owned());
        arguments.push("_cott_lease".to_owned());
    }
    let before = |out: &mut String, indent: usize| -> Result<(), String> {
        render_contract_clauses(
            out,
            config,
            method,
            &callable.symbol,
            true,
            indent,
            &locals,
            None,
            declarations.projection,
        )?;
        render_expected_errors(
            out,
            config,
            method,
            &callable.symbol,
            indent,
            &locals,
            None,
            false,
            declarations.projection,
        )?;
        let prefix = " ".repeat(indent);
        for field in state {
            let name = field
                .get("name")
                .and_then(Value::as_str)
                .ok_or_else(|| "state field is missing name".to_owned())?;
            if !old_state_fields.contains(local_name(name)) {
                continue;
            }
            writeln!(
                out,
                "{prefix}_cott_old_{} = cott_runtime.CottRuntime.deepSnapshot({});",
                safe_internal_name(name),
                escape_identifier(name)?
            )
            .expect("writing to String cannot fail");
        }
        Ok(())
    };
    let descriptor = descriptor_for_contextual(
        return_value,
        declarations,
        &config.dart.external_types,
        &rendering.context,
    )?;
    if asynchronous {
        out.push_str("    return await _cott_resource_contract.enforceMutationAsync(\n      (_cott_mutation) async {\n");
        before(out, 8)?;
        out.push_str("      },\n      (_cott_mutation, _cott_lease) async {\n        try {\n");
        writeln!(
            out,
            "          return await {target}({});",
            arguments.join(", ")
        )
        .expect("writing to String cannot fail");
        writeln!(
            out,
            "        }} catch (error, stackTrace) {{\n          cott_runtime.CottRuntime.rethrowImplementation(error, stackTrace, {}, asynchronous: true);\n        }}\n      }},\n      (_cott_raw_result, _cott_mutation) async {{",
            dart_string(&callable.symbol)
        )
        .expect("writing to String cannot fail");
    } else {
        out.push_str(
            "    return _cott_resource_contract.enforceMutation(\n      (_cott_mutation) {\n",
        );
        before(out, 8)?;
        out.push_str("      },\n      (_cott_mutation, _cott_lease) {\n        try {\n");
        writeln!(out, "          return {target}({});", arguments.join(", "))
            .expect("writing to String cannot fail");
        writeln!(
            out,
            "        }} catch (error, stackTrace) {{\n          cott_runtime.CottRuntime.rethrowImplementation(error, stackTrace, {});\n        }}\n      }},\n      (_cott_raw_result, _cott_mutation) {{",
            dart_string(&callable.symbol)
        )
        .expect("writing to String cannot fail");
    }
    if is_never(return_value) {
        writeln!(
            out,
            "        return cott_runtime.CottRuntime.violation('Never method returned', symbol: {}, phase: 'return');",
            dart_string(&callable.symbol)
        )
        .expect("writing to String cannot fail");
    } else {
        writeln!(
            out,
            "        final _cott_result = cott_runtime.CottRuntime.returnValue(_cott_raw_result, {descriptor}, mode: {}, path: r'$.return');",
            runtime_mode(config)
        )
        .expect("writing to String cannot fail");
        render_contract_clauses(
            out,
            config,
            method,
            &callable.symbol,
            false,
            8,
            &locals,
            None,
            declarations.projection,
        )?;
        render_error_contracts(out, config, method, &callable.symbol, 8)?;
        out.push_str("        return _cott_result;\n");
    }
    writeln!(out, "      }},\n      lease: cottLease,\n    );\n  }}")
        .expect("writing to String cannot fail");
    Ok(())
}

fn old_state_field_references(method: &Map<String, Value>) -> Result<BTreeSet<String>, String> {
    let mut fields = BTreeSet::new();
    for clause in contract_clauses(method) {
        let keys: &[&str] = match clause.get("kind").and_then(Value::as_str) {
            Some("requires" | "ensures") => &["expression", "guard"],
            Some("error") => &["when", "guard"],
            _ => &[],
        };
        for key in keys {
            if let Some(value) = clause.get(*key).filter(|value| !value.is_null()) {
                collect_old_state_field_references(value, &mut fields)?;
            }
        }
    }
    Ok(fields)
}

fn collect_old_state_field_references(
    value: &Value,
    fields: &mut BTreeSet<String>,
) -> Result<(), String> {
    if value.get("kind").and_then(Value::as_str) == Some("old_state_field") {
        let field = value
            .get("field")
            .and_then(Value::as_str)
            .ok_or_else(|| "old state field reference is missing field".to_owned())?;
        fields.insert(local_name(field).to_owned());
    }
    match value {
        Value::Array(values) => {
            for value in values {
                collect_old_state_field_references(value, fields)?;
            }
        }
        Value::Object(object) => {
            for value in object.values() {
                collect_old_state_field_references(value, fields)?;
            }
        }
        _ => {}
    }
    Ok(())
}

fn parameters_have_defaults(declaration: &Map<String, Value>) -> bool {
    declaration
        .get("parameters")
        .and_then(Value::as_array)
        .is_some_and(|parameters| {
            parameters.iter().any(|parameter| {
                parameter
                    .get("default")
                    .is_some_and(|value| !value.is_null())
            })
        })
}

fn type_declaration_has_defaults(declaration: &Value) -> bool {
    let Some(object) = declaration.as_object() else {
        return false;
    };
    match object.get("kind").and_then(Value::as_str) {
        Some("struct") => object
            .get("fields")
            .and_then(Value::as_array)
            .is_some_and(|fields| {
                fields
                    .iter()
                    .any(|field| field.get("default").is_some_and(|value| !value.is_null()))
            }),
        Some("enum") => object
            .get("variants")
            .and_then(Value::as_array)
            .is_some_and(|variants| {
                variants.iter().any(|variant| {
                    variant
                        .get("fields")
                        .and_then(Value::as_array)
                        .is_some_and(|fields| {
                            fields.iter().any(|field| {
                                field.get("default").is_some_and(|value| !value.is_null())
                            })
                        })
                })
            }),
        Some("trait") => object
            .get("methods")
            .and_then(Value::as_array)
            .is_some_and(|methods| {
                methods
                    .iter()
                    .filter_map(Value::as_object)
                    .any(parameters_have_defaults)
            }),
        _ => false,
    }
}

fn callable_modifies_state(declaration: &Map<String, Value>) -> bool {
    ["modifies", "transitions"].into_iter().any(|field| {
        declaration
            .get(field)
            .and_then(Value::as_array)
            .is_some_and(|values| !values.is_empty())
    })
}

fn resource_state_name(symbol: &str, current_module: Option<&str>) -> Result<String, String> {
    let (resource, state) = symbol
        .rsplit_once('.')
        .ok_or_else(|| format!("resource state `{symbol}` has no owner"))?;
    let module = module_of(resource)
        .ok_or_else(|| format!("resource state owner `{resource}` has no module"))?;
    let local = format!(
        "{}{}",
        escape_identifier(local_name(resource))?,
        escape_identifier(state)?
    );
    Ok(if current_module == Some(module) {
        local
    } else {
        format!("{}.{}", module_prefix(module), local)
    })
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
                object.clear();
                object.insert(
                    "kind".to_owned(),
                    Value::String("dart_synthetic".to_owned()),
                );
                object.insert("code".to_owned(), Value::String(local.clone()));
                return;
            }
            for value in object.values_mut() {
                rewrite_parameter_references(value, locals);
            }
        }
        _ => {}
    }
}

fn rewrite_const_references_for_callable(value: &mut Value, declaration: &Map<String, Value>) {
    let witnesses = declaration
        .get("generics")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter(|generic| generic.get("kind").and_then(Value::as_str) == Some("const"))
        .filter_map(|generic| generic.get("name").and_then(Value::as_str))
        .map(|name| WitnessField {
            generic: name.to_owned(),
            ty: name.to_owned(),
            public_name: format!("_cott_const_{}", safe_internal_name(name)),
        })
        .collect::<Vec<_>>();
    rewrite_const_references(value, declaration, &witnesses);
}

fn rewrite_const_references(
    value: &mut Value,
    declaration: &Map<String, Value>,
    witnesses: &[WitnessField],
) {
    let constants = declaration
        .get("generics")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter(|generic| generic.get("kind").and_then(Value::as_str) == Some("const"))
        .filter_map(|generic| generic.get("name").and_then(Value::as_str))
        .filter_map(|name| {
            witnesses
                .iter()
                .find(|witness| witness.generic == name)
                .map(|witness| (name.to_owned(), format!("{}.value", witness.public_name)))
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
                        Value::String("dart_synthetic".to_owned()),
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

fn runtime_mode(config: &DartProjectConfig) -> &'static str {
    match &config.dart.runtime_validation {
        RuntimeValidation::Boundary => "cott_runtime.RuntimeValidation.boundary",
        RuntimeValidation::TestOnly => "cott_runtime.RuntimeValidation.testOnly",
        RuntimeValidation::Off => "cott_runtime.RuntimeValidation.off",
    }
}

fn is_never(value: &Value) -> bool {
    value.get("kind").and_then(Value::as_str) == Some("primitive")
        && value.get("name").and_then(Value::as_str) == Some("never")
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
