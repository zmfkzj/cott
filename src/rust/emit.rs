use super::expressions::{clause_label, render_expression_contextual, render_guarded_statement};
use super::types::*;
use super::{RustBinding, RustCallable, RustEmission, RustPlan};
use crate::manifest::{RuntimeValidation, RustProjectConfig};
use serde_json::{Map, Value};
use std::collections::{BTreeMap, BTreeSet};
use std::fmt::Write as _;
use std::path::PathBuf;

pub(crate) mod consts;
mod enums;
mod errors;
mod layout;
mod state;
mod traits;
mod tuples;
mod type_context;

pub fn render_type(plan: &RustPlan, ty: &Value) -> Result<String, String> {
    type_context::render(plan, ty, None)
}
pub(super) fn render_type_scoped(
    plan: &RustPlan,
    ty: &Value,
    scope: &Value,
) -> Result<String, String> {
    type_context::render(plan, ty, Some(scope))
}
fn rewrite(mut code: String, aliases: &BTreeMap<String, String>) -> String {
    for (module, alias) in aliases.iter().rev() {
        code = code.replace(
            &format!("crate::modules::{}::", module_prefix(module)),
            &format!("{alias}::"),
        );
    }
    code
}
pub(crate) fn render_consumer_type_arguments(
    plan: &RustPlan,
    ty: &Value,
    aliases: &BTreeMap<String, String>,
) -> Result<Vec<String>, String> {
    list(ty, "args")
        .iter()
        .map(|argument| {
            Ok(rewrite(
                if argument["kind"] == "const" {
                    consts::render_marker(&argument["value"], None)?
                } else {
                    render_type(plan, &argument["type"])?
                },
                aliases,
            ))
        })
        .collect()
}
pub(crate) fn render_consumer_type(
    plan: &RustPlan,
    ty: &Value,
    aliases: &BTreeMap<String, String>,
) -> Result<String, String> {
    Ok(rewrite(render_type(plan, ty)?, aliases))
}
pub(crate) fn render_consumer_expression(
    e: &Value,
    aliases: &BTreeMap<String, String>,
) -> Result<String, String> {
    Ok(rewrite(render_expression_contextual(e, None)?, aliases))
}
pub(crate) fn render_consumer_dyn(
    plan: &RustPlan,
    trait_ref: &Value,
    value: &str,
    aliases: &BTreeMap<String, String>,
) -> Result<String, String> {
    let ty = serde_json::json!({"kind":"dyn","trait":trait_ref});
    Ok(format!(
        "<{}>::new(Box::new({value}))",
        rewrite(render_type(plan, &ty)?, aliases)
    ))
}
pub(crate) fn render_consumer_opaque(
    tag: &str,
    payload: &str,
    _marker_module: &str,
    _aliases: &BTreeMap<String, String>,
) -> Result<String, String> {
    Ok(format!(
        "crate::cott_runtime::Opaque::<{}>::new({payload})",
        opaque_marker(tag)
    ))
}
pub(crate) fn render_consumer_symbol(
    symbol: &str,
    aliases: &BTreeMap<String, String>,
) -> Result<String, String> {
    Ok(rewrite(render_canonical_symbol(symbol, None)?, aliases))
}
pub(crate) fn render_consumer_resource_state(
    symbol: &str,
    aliases: &BTreeMap<String, String>,
) -> Result<String, String> {
    render_consumer_symbol(symbol, aliases)
}
/// Native turbofish arguments, in canonical order; never positional witness values.
pub(crate) fn render_consumer_generic_arguments(
    plan: &RustPlan,
    callable: &RustCallable,
    arguments: &BTreeMap<String, Value>,
    aliases: &BTreeMap<String, String>,
) -> Result<Vec<String>, String> {
    let declaration = resolved(plan, callable)?;
    list(&declaration, "generics")
        .iter()
        .map(|g| {
            let name = text(g, "name")?;
            let value = arguments
                .get(name)
                .ok_or_else(|| format!("missing native generic argument {name}"))?;
            Ok(rewrite(
                if g["kind"] == "const" {
                    consts::render_marker(value, None)?
                } else {
                    render_type(plan, value)?
                },
                aliases,
            ))
        })
        .collect()
}
pub(super) fn list<'a>(v: &'a Value, key: &str) -> &'a [Value] {
    v.get(key)
        .and_then(Value::as_array)
        .map(Vec::as_slice)
        .unwrap_or_default()
}
pub(super) fn declaration_named<'a>(plan: &'a RustPlan, name: &str) -> Option<&'a Value> {
    plan.modules
        .iter()
        .flat_map(|m| &m.declarations)
        .find(|d| d.get("name").and_then(Value::as_str) == Some(name))
}
pub(super) fn generics(d: &Value) -> Result<(String, String), String> {
    let mut declarations = Vec::new();
    let mut names = Vec::new();
    for g in list(d, "generics") {
        let name = escape_identifier(local_name(text(g, "name")?))?;
        names.push(name.clone());
        let bounds = if g["kind"] == "const" {
            vec![consts::render_kind(g)?]
        } else {
            let mut b = list(g, "bounds")
                .iter()
                .map(|v| {
                    let mut bound = v.clone();
                    if matches!(
                        d["kind"].as_str(),
                        Some("alias" | "struct" | "newtype" | "enum")
                    ) {
                        let name = text(v, "name")?;
                        bound["name"] = Value::String(format!("{name}Types"));
                    }
                    render_type_contextual(&bound, None, None)
                })
                .collect::<Result<Vec<_>, _>>()?;
            b.extend([
                "crate::cott_runtime::Value".into(),
                "Clone".into(),
                "PartialEq".into(),
                "std::fmt::Debug".into(),
                "Send".into(),
                "Sync".into(),
                "'static".into(),
            ]);
            b
        };
        declarations.push(format!("{name}: {}", bounds.join(" + ")));
    }
    let angle = |v: Vec<String>| {
        if v.is_empty() {
            String::new()
        } else {
            format!("<{}>", v.join(", "))
        }
    };
    Ok((angle(declarations), angle(names)))
}
pub(super) fn where_constraints(plan: &RustPlan, scope: &Value) -> Result<String, String> {
    let mut clauses = traits::value_constraints(plan, scope)?;
    fn constructors(
        plan: &RustPlan,
        value: &Value,
        scope: &Value,
        result: &mut BTreeSet<String>,
    ) -> Result<(), String> {
        match value {
            Value::Array(a) => {
                for value in a {
                    constructors(plan, value, scope, result)?
                }
            }
            Value::Object(o) => {
                if o.get("kind").and_then(Value::as_str) == Some("factory") {
                    result.insert(format!(
                        "{}:crate::cott_runtime::ConstructionArguments",
                        render_type_scoped(plan, &value["instance"], scope)?
                    ));
                }
                for (k, value) in o {
                    if !matches!(k.as_str(), "span" | "doc") {
                        constructors(plan, value, scope, result)?
                    }
                }
            }
            _ => {}
        }
        Ok(())
    }
    let mut required = BTreeSet::new();
    constructors(plan, scope, scope, &mut required)?;
    clauses.extend(required);
    Ok(if clauses.is_empty() {
        String::new()
    } else {
        format!(" where {}", clauses.join(", "))
    })
}
pub(super) fn resolved(plan: &RustPlan, c: &RustCallable) -> Result<Value, String> {
    let mut d = c.declaration.clone();
    if let Some(owner) = &c.owner {
        let slot = list(owner, "selected_methods")
            .iter()
            .find(|s| {
                s.get("trait_method")
                    .and_then(Value::as_str)
                    .map(local_name)
                    == Some(c.name.as_str())
            })
            .ok_or_else(|| format!("missing selected method {}", c.symbol))?;
        let trait_name =
            module_of(text(slot, "trait_method")?).ok_or("unqualified trait method")?;
        let trait_decl = declaration_named(plan, trait_name).ok_or("unknown selected trait")?;
        let method = list(trait_decl, "methods")
            .iter()
            .find(|m| {
                m.get("name").and_then(Value::as_str)
                    == slot.get("trait_method").and_then(Value::as_str)
            })
            .ok_or("missing canonical trait method")?;
        d["generics"] =
            type_context::instantiate(&method["generics"], trait_decl, &slot["trait_ref"])?;
        for key in ["parameters", "return_type", "callable_kind"] {
            d[key] = slot[key].clone();
        }
        substitute_associated(&mut d, owner);
    }
    Ok(d)
}
pub(super) fn substitute_associated(value: &mut Value, owner: &Value) {
    match value {
        Value::Array(a) => {
            for v in a {
                substitute_associated(v, owner)
            }
        }
        Value::Object(o) => {
            let replacement = if o.get("kind").and_then(Value::as_str)
                == Some("associated_projection")
                && o.get("base")
                    .is_some_and(|b| b["kind"] == "type_parameter" && b["name"] == "Self")
            {
                list(owner, "associated_types")
                    .iter()
                    .find(|a| {
                        a.get("trait").and_then(Value::as_str)
                            == o.get("trait").and_then(Value::as_str)
                            && a.get("name").and_then(Value::as_str).map(local_name)
                                == o.get("name").and_then(Value::as_str).map(local_name)
                    })
                    .map(|a| a["type"].clone())
            } else if o.get("kind").and_then(Value::as_str) == Some("type_parameter")
                && o.get("name").and_then(Value::as_str) == Some("Self")
            {
                Some(serde_json::json!({"kind":"named","name":owner["name"],"args":[]}))
            } else {
                None
            };
            if let Some(replacement) = replacement {
                *value = replacement
            } else {
                for (k, v) in o {
                    if k != "span" {
                        substitute_associated(v, owner)
                    }
                }
            }
        }
        _ => {}
    }
}
pub(super) fn parameter_type(plan: &RustPlan, p: &Value, scope: &Value) -> Result<String, String> {
    let base = render_type_scoped(plan, &p["type"], scope)?;
    Ok(
        match p
            .get("kind")
            .and_then(Value::as_str)
            .unwrap_or("positional")
        {
            "positional" | "keyword_only" => {
                traits::borrowed_parameter_type(plan, &p["type"])?.unwrap_or(base)
            }
            "vararg" => format!("Vec<{base}>"),
            "kwarg" => format!("crate::cott_runtime::Map<String,{base}>"),
            kind => return Err(format!("unsupported parameter kind {kind}")),
        },
    )
}
pub(super) fn public_parameters(plan: &RustPlan, d: &Value) -> Result<Vec<String>, String> {
    list(d, "parameters")
        .iter()
        .map(|p| {
            let ty = parameter_type(plan, p, d)?;
            Ok(format!(
                "{}: {}",
                escape_identifier(local_name(text(p, "name")?))?,
                if has_default(p) {
                    format!("Option<{ty}>")
                } else {
                    ty
                }
            ))
        })
        .collect()
}
fn has_default(value: &Value) -> bool {
    value.get("default").is_some_and(|v| !v.is_null())
}
pub(super) fn defaults(plan: &RustPlan, d: &Value) -> Result<String, String> {
    let mut out = String::new();
    for p in list(d, "parameters").iter().filter(|p| has_default(p)) {
        let name = escape_identifier(local_name(text(p, "name")?))?;
        writeln!(
            out,
            "let {name} = {name}.unwrap_or_else(|| {});",
            render_literal(plan, &p["default"], Some(&p["type"]), d)?
        )
        .unwrap();
    }
    Ok(out)
}
pub(super) fn const_checks(d: &Value, _symbol: &str) -> Result<String, String> {
    let mut out = String::new();
    for g in list(d, "generics").iter().filter(|g| g["kind"] == "const") {
        writeln!(
            out,
            "let _ = <{} as crate::cott_runtime::ConstValue>::value();",
            escape_identifier(text(g, "name")?)?
        )
        .unwrap();
    }
    Ok(out)
}
pub(super) fn contains_type_parameter(value: &Value, name: &str) -> bool {
    match value {
        Value::Array(a) => a.iter().any(|v| contains_type_parameter(v, name)),
        Value::Object(o) => {
            (o.get("kind").and_then(Value::as_str) == Some("type_parameter")
                && o.get("name").and_then(Value::as_str).map(local_name) == Some(name))
                || o.values().any(|v| contains_type_parameter(v, name))
        }
        _ => false,
    }
}
fn references_parameter(value: &Value, name: &str) -> bool {
    match value {
        Value::Array(a) => a.iter().any(|v| references_parameter(v, name)),
        Value::Object(o) => {
            (o.get("kind").and_then(Value::as_str) == Some("parameter_ref")
                && o.get("symbol").and_then(Value::as_str).map(local_name) == Some(name))
                || o.iter()
                    .filter(|(k, _)| !matches!(k.as_str(), "type" | "span"))
                    .any(|(_, v)| references_parameter(v, name))
        }
        _ => false,
    }
}
pub(super) fn borrowed_parameter(plan: &RustPlan, d: &Value, p: &Value) -> Result<bool, String> {
    if traits::borrowed_parameter_type(plan, &p["type"])?.is_some() {
        return Ok(false);
    }
    let copy = !matches!(p["kind"].as_str(), Some("vararg" | "kwarg"))
        && p["type"]["kind"] == "primitive"
        && matches!(
            p["type"]["name"].as_str(),
            Some(
                "bool"
                    | "i8"
                    | "i16"
                    | "i32"
                    | "i64"
                    | "u8"
                    | "u16"
                    | "u32"
                    | "u64"
                    | "f32"
                    | "f64"
                    | "unit"
                    | "never"
            )
        );
    Ok(!copy
        && clauses(d)
            .iter()
            .filter(|c| c["kind"] == "ensures")
            .any(|c| references_parameter(c, local_name(text(p, "name").unwrap_or("")))))
}
fn implementation_parameters(plan: &RustPlan, d: &Value) -> Result<Vec<String>, String> {
    list(d, "parameters")
        .iter()
        .map(|p| {
            Ok(format!(
                "{}: {}{}",
                escape_identifier(local_name(text(p, "name")?))?,
                if borrowed_parameter(plan, d, p)? {
                    "&"
                } else {
                    ""
                },
                parameter_type(plan, p, d)?
            ))
        })
        .collect()
}
pub(super) fn private_name(c: &RustCallable) -> String {
    format!(
        "cott_{}",
        &crate::hash::sha256_hex(c.symbol.as_bytes())[..24]
    )
}
/// The single deterministic implementation ABI, reused by binding audit and prompts.
pub fn implementation_signature(plan: &RustPlan, c: &RustCallable) -> Result<String, String> {
    let d = resolved(plan, c)?;
    let mut args = implementation_parameters(plan, &d)?;
    if let Some(owner) = &c.owner {
        args.insert(
            0,
            format!(
                "receiver: &mut {}",
                render_canonical_symbol(text(owner, "name")?, None)?
            ),
        );
    }
    Ok(format!(
        "pub(crate) {}fn {}{}({}) -> {}{}",
        if d["callable_kind"] == "async" {
            "async "
        } else {
            ""
        },
        escape_identifier(&c.name)?,
        generics(&d)?.0,
        args.join(", "),
        render_type_scoped(plan, &d["return_type"], &d)?,
        where_constraints(plan, &d)?
    ))
}
/// Authored bytes remain the source identity; the managed module adds a compiler header.
pub fn managed_implementation_source(binding: &RustBinding) -> Result<Vec<u8>, String> {
    let authored = std::str::from_utf8(&binding.bytes)
        .map_err(|e| format!("implementation is not UTF-8: {e}"))?;
    Ok(
        format!("// Generated by Cott. Authored implementation embedded below.\n{authored}\n")
            .into_bytes(),
    )
}
pub(super) fn clauses(d: &Value) -> Vec<&Value> {
    if let Some(c) = d
        .get("contract")
        .and_then(|v| v.get("clauses"))
        .and_then(Value::as_array)
    {
        c.iter().collect()
    } else {
        ["requires", "errors", "ensures"]
            .into_iter()
            .flat_map(|k| list(&d["contracts"], k))
            .collect()
    }
}
pub(crate) fn checks_error_return(d: &Map<String, Value>) -> bool {
    crate::ir::complete_errors(d) == Ok(true)
        || d.get("contract")
            .and_then(|v| v.get("clauses"))
            .and_then(Value::as_array)
            .is_some_and(|c| c.iter().any(|c| c["kind"] == "error"))
        || d.get("contracts")
            .is_some_and(|v| !list(v, "errors").is_empty())
}
pub(super) fn expression(plan: &RustPlan, e: &Value, scope: &Value) -> Result<String, String> {
    render_expression_contextual(&lower_expression(plan, e, scope)?, None)
}
pub(super) fn lower_expression(plan: &RustPlan, e: &Value, scope: &Value) -> Result<Value, String> {
    match e {
        Value::Array(a) => Ok(Value::Array(
            a.iter()
                .map(|e| lower_expression(plan, e, scope))
                .collect::<Result<Vec<_>, _>>()?,
        )),
        Value::Object(o) => {
            if e["kind"] == "constant_ref" {
                if let Some(g) = list(scope, "generics").iter().find(|g| {
                    g["kind"] == "const"
                        && g.get("name").and_then(Value::as_str).map(local_name)
                            == e.get("symbol").and_then(Value::as_str).map(local_name)
                }) {
                    return Ok(
                        serde_json::json!({"kind":"rust_synthetic","type":e["type"],"code":format!("(<{} as crate::cott_runtime::ConstValue>::value() as {})",escape_identifier(text(g,"name")?)?,text(g,"type")?.to_ascii_lowercase())}),
                    );
                }
            }
            if e["kind"] == "literal" {
                if e["value"]["kind"] == "integer"
                    && e["type"]["kind"] == "primitive"
                    && !matches!(e["type"]["name"].as_str(), Some("any" | "unknown"))
                {
                    return Ok(e.clone());
                }
                return Ok(
                    serde_json::json!({"kind":"rust_synthetic","type":e["type"],"code":render_literal(plan,&e["value"],e.get("type"),scope)?}),
                );
            }
            if e["kind"] == "construct" {
                let args = constructor_arguments(
                    plan,
                    text(e, "symbol")?,
                    list(e, "fields"),
                    e.get("type"),
                    scope,
                    true,
                )?;
                let ty = layout::raw_type(plan, &e["type"], scope)?;
                return Ok(
                    serde_json::json!({"kind":"rust_synthetic","type":e["type"],"code":format!("<{ty}>::new({})",args.join(", "))}),
                );
            }
            if e["kind"] == "variant" {
                let args = list(e, "fields")
                    .iter()
                    .map(|v| expression(plan, v, scope))
                    .collect::<Result<Vec<_>, _>>()?;
                let ty = layout::raw_type(plan, &e["type"], scope)?;
                let name = escape_identifier(local_name(text(e, "symbol")?))?;
                let code = if args.is_empty() {
                    format!("<{ty}>::{name}")
                } else {
                    format!("<{ty}>::{name}({})", args.join(", "))
                };
                let code = if e["type"]
                    .get("name")
                    .and_then(Value::as_str)
                    .is_some_and(|n| layout::recursive(plan, n))
                {
                    format!("Box::new({code})")
                } else {
                    code
                };
                return Ok(
                    serde_json::json!({"kind":"rust_synthetic","type":e["type"],"code":code}),
                );
            }
            if matches!(e["kind"].as_str(), Some("array")) {
                let items = list(e, "items")
                    .iter()
                    .map(|v| expression(plan, v, scope))
                    .collect::<Result<Vec<_>, _>>()?;
                let ty = render_type_scoped(plan, &e["type"], scope)?;
                return Ok(
                    serde_json::json!({"kind":"rust_synthetic","type":e["type"],"code":format!("<{ty}>::new(vec![{}])",items.join(", "))}),
                );
            }
            if e["kind"] == "dyn" {
                let value = expression(plan, &e["value"], scope)?;
                let ty = serde_json::json!({"kind":"dyn","trait":e["trait_ref"]});
                return Ok(
                    serde_json::json!({"kind":"rust_synthetic","type":ty,"code":format!("<{}>::new(Box::new({value}))",render_type_scoped(plan,&ty,scope)?)}),
                );
            }
            let mut result = o.clone();
            for (k, v) in &mut result {
                if !matches!(k.as_str(), "type" | "trait_ref" | "span" | "value") {
                    *v = lower_expression(plan, v, scope)?;
                }
            }
            Ok(Value::Object(result))
        }
        _ => Ok(e.clone()),
    }
}
pub(super) fn contract_checks(
    plan: &RustPlan,
    d: &Value,
    symbol: &str,
    kind: &str,
    mode: &RuntimeValidation,
) -> Result<String, String> {
    if *mode == RuntimeValidation::Off {
        return Ok(String::new());
    }
    let mut out = String::new();
    for c in clauses(d).into_iter().filter(|c| c["kind"] == kind) {
        let predicate = expression(plan, &c["expression"], d)?;
        let statement = format!(
            "crate::cott_runtime::__cott_check({}, {}, {}, {predicate});",
            rust_string(symbol),
            rust_string(kind),
            rust_string(&clause_label(c)?)
        );
        let guard = c
            .get("guard")
            .map(|g| lower_expression(plan, g, d))
            .transpose()?;
        writeln!(
            out,
            "if crate::cott_runtime::__cott_validation_enabled({}) {{ {} }}",
            *mode == RuntimeValidation::Boundary,
            render_guarded_statement(guard.as_ref(), &statement, None)?
        )
        .unwrap();
    }
    Ok(out)
}
pub(super) fn validate(
    _plan: &RustPlan,
    _ty: &Value,
    value: &str,
    _symbol: &str,
) -> Result<String, String> {
    Ok(format!(
        "crate::cott_runtime::Value::validate(&({value}));\n"
    ))
}
pub(super) fn effects(
    config: &RustProjectConfig,
    d: &Value,
    symbol: &str,
) -> Result<String, String> {
    let effects = d
        .get("contract")
        .and_then(|c| c.get("effects"))
        .or_else(|| d.get("effects"))
        .and_then(Value::as_array);
    let mut out = String::new();
    for effect in effects.into_iter().flatten() {
        let key = text(effect, "key")?;
        let allowed = crate::hir::INTRINSIC_EFFECTS.contains(&key)
            || config.effects.get(key).copied().unwrap_or(false);
        if !allowed {
            writeln!(
                out,
                "crate::cott_runtime::violation({},\"effect\",{});",
                rust_string(symbol),
                rust_string(key)
            )
            .unwrap();
        }
    }
    Ok(out)
}
fn facade(
    config: &RustProjectConfig,
    plan: &RustPlan,
    c: &RustCallable,
    binding: &RustBinding,
) -> Result<String, String> {
    let d = resolved(plan, c)?;
    let mut out = format!(
        "pub {}fn {}{}({}) -> {}{} {{\n",
        if d["callable_kind"] == "async" {
            "async "
        } else {
            ""
        },
        escape_identifier(&c.name)?,
        generics(&d)?.0,
        public_parameters(plan, &d)?.join(", "),
        render_type_scoped(plan, &d["return_type"], &d)?,
        where_constraints(plan, &d)?
    );
    out.push_str(&defaults(plan, &d)?);
    out.push_str(&effects(config, &d, &c.symbol)?);
    for p in list(&d, "parameters") {
        out.push_str(&validate(
            plan,
            &p["type"],
            &escape_identifier(local_name(text(p, "name")?))?,
            &c.symbol,
        )?);
    }
    out.push_str(&contract_checks(
        plan,
        &d,
        &c.symbol,
        "requires",
        &config.rust.runtime_validation,
    )?);
    if config.rust.runtime_validation != RuntimeValidation::Off {
        out.push_str(&errors::before(
            plan,
            &d,
            &c.symbol,
            config.rust.runtime_validation == RuntimeValidation::Boundary,
        )?);
    }
    let args = list(&d, "parameters")
        .iter()
        .map(|p| {
            let name = escape_identifier(local_name(text(p, "name")?))?;
            Ok(if borrowed_parameter(plan, &d, p)? {
                format!("&{name}")
            } else {
                name
            })
        })
        .collect::<Result<Vec<_>, String>>()?;
    let target = escape_identifier(
        binding
            .target_symbol
            .rsplit(':')
            .next()
            .ok_or("binding has no function")?
            .strip_prefix("r#")
            .unwrap_or(binding.target_symbol.rsplit(':').next().unwrap()),
    )?;
    let type_arguments = generics(&d)?.1;
    let turbofish = if type_arguments.is_empty() {
        String::new()
    } else {
        format!("::{type_arguments}")
    };
    writeln!(
        out,
        "let __cott_result = crate::cott_impl::{}::{target}{turbofish}({}){};",
        private_name(c),
        args.join(", "),
        if d["callable_kind"] == "async" {
            ".await"
        } else {
            ""
        }
    )
    .unwrap();
    out.push_str(&validate(
        plan,
        &d["return_type"],
        "__cott_result",
        &c.symbol,
    )?);
    if config.rust.runtime_validation != RuntimeValidation::Off {
        out.push_str(&errors::after(
            plan,
            &d,
            &c.symbol,
            config.rust.runtime_validation == RuntimeValidation::Boundary,
        )?);
    }
    out.push_str(&contract_checks(
        plan,
        &d,
        &c.symbol,
        "ensures",
        &config.rust.runtime_validation,
    )?);
    out.push_str("__cott_result\n}\n");
    Ok(out)
}
fn expand_alias(plan: &RustPlan, ty: &Value) -> Result<Value, String> {
    if ty["kind"] == "named" {
        if let Some(d) = ty
            .get("name")
            .and_then(Value::as_str)
            .and_then(|n| declaration_named(plan, n))
            .filter(|d| d["kind"] == "alias")
        {
            return expand_alias(plan, &type_context::instantiate(&d["target"], d, ty)?);
        }
    }
    Ok(ty.clone())
}
pub(super) fn constructor_arguments(
    plan: &RustPlan,
    symbol: &str,
    fields: &[Value],
    expected: Option<&Value>,
    scope: &Value,
    expressions: bool,
) -> Result<Vec<String>, String> {
    let d =
        declaration_named(plan, symbol).ok_or_else(|| format!("unknown constructor {symbol}"))?;
    let d = if let Some(expected) = expected.filter(|t| t["kind"] == "named" && t["name"] == symbol)
    {
        type_context::instantiate(d, d, expected)?
    } else {
        d.clone()
    };
    let params = if d["kind"] == "newtype" {
        vec![serde_json::json!({"name":"value","type":d["carrier"]})]
    } else if d["kind"] == "impl" {
        list(&d["init"], "parameters").to_vec()
    } else {
        list(&d, "fields").to_vec()
    };
    params
        .iter()
        .map(|p| {
            let name = local_name(text(p, "name")?);
            if let Some(field) = fields
                .iter()
                .find(|f| f.get("name").and_then(Value::as_str).map(local_name) == Some(name))
            {
                let value = if expressions {
                    expression(plan, &field["value"], scope)?
                } else {
                    render_literal(plan, &field["value"], Some(&p["type"]), scope)?
                };
                Ok(if has_default(p) {
                    format!("Some({value})")
                } else {
                    value
                })
            } else if has_default(p) {
                Ok("None".into())
            } else {
                Err(format!("constructor {symbol} lacks required field {name}"))
            }
        })
        .collect()
}
pub(super) fn render_literal(
    plan: &RustPlan,
    value: &Value,
    expected: Option<&Value>,
    scope: &Value,
) -> Result<String, String> {
    let expected = expected.map(|t| expand_alias(plan, t)).transpose()?;
    let ty = expected.as_ref();
    let r = |v: &Value, t: Option<&Value>| render_literal(plan, v, t, scope);
    let code = match text(value, "kind")? {
        "named" => {
            let symbol = text(value, "symbol")?;
            let args =
                constructor_arguments(plan, symbol, list(value, "fields"), ty, scope, false)?;
            let target =
                if let Some(ty) = ty.filter(|t| t["kind"] == "named" && t["name"] == symbol) {
                    layout::raw_type(plan, ty, scope)?
                } else {
                    render_canonical_symbol(symbol, None)?
                };
            format!("<{target}>::new({})", args.join(", "))
        }
        "enum" => {
            let variant = text(value, "variant")?;
            let owner = module_of(variant).ok_or("enum variant lacks owner")?;
            let target = if let Some(ty) = ty {
                layout::raw_type(plan, ty, scope)?
            } else {
                render_canonical_symbol(owner, None)?
            };
            let args = list(value, "fields")
                .iter()
                .map(|v| r(v, None))
                .collect::<Result<Vec<_>, _>>()?;
            let variant = escape_identifier(local_name(variant))?;
            let code = if args.is_empty() {
                format!("<{target}>::{variant}")
            } else {
                format!("<{target}>::{variant}({})", args.join(", "))
            };
            if layout::recursive(plan, owner) {
                format!("Box::new({code})")
            } else {
                code
            }
        }
        "option" => {
            if value["value"].is_null() {
                "None".into()
            } else {
                format!(
                    "Some({})",
                    r(&value["value"], ty.and_then(|t| t.get("item")))?
                )
            }
        }
        "result" => format!(
            "{}({})",
            if value["ok"] == true { "Ok" } else { "Err" },
            r(
                &value["value"],
                ty.and_then(|t| t.get(if value["ok"] == true { "ok" } else { "error" }))
            )?
        ),
        "list" | "set" | "array" | "tuple" => {
            let values = list(value, "items")
                .iter()
                .enumerate()
                .map(|(i, v)| {
                    r(
                        v,
                        ty.and_then(|t| {
                            if value["kind"] == "tuple" {
                                t.get("items")
                                    .and_then(Value::as_array)
                                    .and_then(|a| a.get(i))
                            } else {
                                t.get("item")
                            }
                        }),
                    )
                })
                .collect::<Result<Vec<_>, _>>()?;
            match text(value, "kind")? {
                "list" => format!("vec![{}]", values.join(", ")),
                "set" => format!(
                    "crate::cott_runtime::Set::{}(vec![{}])",
                    super::types::collection_constructor(ty.and_then(|t| t.get("item"))),
                    values.join(", ")
                ),
                "array" => format!(
                    "<{}>::new(vec![{}])",
                    render_type_scoped(
                        plan,
                        ty.ok_or("array literal lacks expected type")?,
                        scope
                    )?,
                    values.join(", ")
                ),
                "tuple" if values.len() > 12 => format!(
                    "crate::cott_runtime::Tuple{}({})",
                    values.len(),
                    values.join(", ")
                ),
                _ => format!(
                    "({}{})",
                    values.join(", "),
                    if values.len() == 1 { "," } else { "" }
                ),
            }
        }
        "buffer" => render_value_contextual(value, None, None)?,
        "map" => {
            let entries = list(value, "entries")
                .iter()
                .map(|v| {
                    Ok(format!(
                        "({}, {})",
                        r(&v[0], ty.and_then(|t| t.get("key")))?,
                        r(&v[1], ty.and_then(|t| t.get("value")))?
                    ))
                })
                .collect::<Result<Vec<_>, String>>()?;
            format!(
                "crate::cott_runtime::Map::{}(vec![{}])",
                super::types::collection_constructor(ty.and_then(|t| t.get("key"))),
                entries.join(", ")
            )
        }
        _ => render_value_contextual(value, ty, None)?,
    };
    Ok(
        if ty.is_some_and(|t| {
            t["kind"] == "primitive" && matches!(t["name"].as_str(), Some("any" | "unknown"))
        }) {
            format!("crate::cott_runtime::AnyValue::new({code})")
        } else {
            code
        },
    )
}
pub(super) fn constructor_expression(
    expression: &Value,
    fields: &[Value],
    refinement: bool,
) -> Value {
    let mut result = expression.clone();
    fn visit(v: &mut Value, fields: &[Value], refinement: bool) {
        match v {
            Value::Array(a) => {
                for v in a {
                    visit(v, fields, refinement)
                }
            }
            Value::Object(o) => {
                let field =
                    if refinement && o.get("kind").and_then(Value::as_str) == Some("self_ref") {
                        Some("value".to_owned())
                    } else if o.get("kind").and_then(Value::as_str) == Some("parameter_ref") {
                        o.get("symbol")
                            .and_then(Value::as_str)
                            .and_then(|n| {
                                fields.iter().find(|f| {
                                    f.get("name").and_then(Value::as_str).map(local_name)
                                        == Some(local_name(n))
                                })
                            })
                            .and_then(|f| f.get("name"))
                            .and_then(Value::as_str)
                            .map(|n| local_name(n).into())
                    } else {
                        None
                    };
                if let Some(field) = field {
                    let ty = o.get("type").cloned().unwrap_or(Value::Null);
                    *v = serde_json::json!({"kind":"rust_synthetic","type":ty,"code":format!("self.{}",escape_identifier(&field).expect("canonical field"))});
                } else {
                    for (k, v) in o {
                        if !matches!(k.as_str(), "type" | "span") {
                            visit(v, fields, refinement)
                        }
                    }
                }
            }
            _ => {}
        }
    }
    visit(&mut result, fields, refinement);
    result
}
fn nominal(plan: &RustPlan, d: &Value) -> Result<String, String> {
    let canonical = text(d, "name")?;
    let name = escape_identifier(local_name(canonical))?;
    let recursive = layout::recursive(plan, canonical);
    let metadata_recursive = layout::metadata_recursive(plan, canonical);
    let returned = if recursive { "Box<Self>" } else { "Self" };
    let (g, a) = generics(d)?;
    let w = where_constraints(plan, d)?;
    let fields = if d["kind"] == "newtype" {
        vec![serde_json::json!({"name":"value","type":d["carrier"]})]
    } else {
        list(d, "fields").to_vec()
    };
    let phantom = list(d, "generics")
        .iter()
        .filter(|g| {
            !fields
                .iter()
                .any(|f| contains_type_parameter(f, local_name(text(g, "name").unwrap_or(""))))
        })
        .map(|g| escape_identifier(local_name(text(g, "name")?)))
        .collect::<Result<Vec<_>, _>>()?;
    let mut out = format!("#[derive(Clone,Debug,PartialEq)]\npub struct {name}{g}{w} {{\n");
    for f in &fields {
        writeln!(
            out,
            "{}: {},",
            escape_identifier(local_name(text(f, "name")?))?,
            render_type_scoped(plan, &f["type"], d)?
        )
        .unwrap();
    }
    if !phantom.is_empty() {
        writeln!(
            out,
            "__cott_marker: std::marker::PhantomData<({},)>,",
            phantom.join(", ")
        )
        .unwrap();
    }
    writeln!(out, "}}\nimpl{g} {name}{a}{w} {{").unwrap();
    let params = fields
        .iter()
        .map(|f| {
            Ok(format!(
                "{}: {}",
                escape_identifier(local_name(text(f, "name")?))?,
                if has_default(f) {
                    format!("Option<{}>", render_type_scoped(plan, &f["type"], d)?)
                } else {
                    render_type_scoped(plan, &f["type"], d)?
                }
            ))
        })
        .collect::<Result<Vec<_>, String>>()?;
    if recursive {
        let arguments = fields
            .iter()
            .map(|f| escape_identifier(local_name(text(f, "name")?)))
            .collect::<Result<Vec<_>, _>>()?
            .join(", ");
        writeln!(
            out,
            "pub fn new({})->Box<Self>{{Box::new(Self::__cott_new_raw({arguments}))}}",
            params.join(", ")
        )
        .unwrap();
        writeln!(out, "fn __cott_new_raw({})->Self{{", params.join(", ")).unwrap();
    } else {
        writeln!(out, "pub fn new({})->Self{{", params.join(", ")).unwrap();
    }
    out.push_str(&defaults(plan, &serde_json::json!({"parameters":fields}))?);
    let initialized = fields
        .iter()
        .map(|f| escape_identifier(local_name(text(f, "name")?)))
        .collect::<Result<Vec<_>, _>>()?
        .into_iter()
        .chain((!phantom.is_empty()).then_some("__cott_marker: std::marker::PhantomData".into()))
        .collect::<Vec<_>>();
    writeln!(
        out,
        "let value=Self{{{}}};value.__cott_validate();value }}",
        initialized.join(", ")
    )
    .unwrap();
    for f in &fields {
        let n = escape_identifier(local_name(text(f, "name")?))?;
        let getter = escape_identifier(&format!("get_{}", local_name(text(f, "name")?)))?;
        writeln!(
            out,
            "pub fn {getter}(&self)->&{}{{&self.{n}}}",
            render_type_scoped(plan, &f["type"], d)?
        )
        .unwrap();
    }
    writeln!(
        out,
        "pub fn copy_with(&self,{}) -> {returned} where Self:Clone {{ let {}__cott_copy=self.clone();",
        fields
            .iter()
            .map(|f| Ok(format!(
                "{}:Option<{}>",
                escape_identifier(local_name(text(f, "name")?))?,
                render_type_scoped(plan, &f["type"], d)?
            )))
            .collect::<Result<Vec<_>, String>>()?
            .join(", "),
        if fields.is_empty() { "" } else { "mut " }
    )
    .unwrap();
    for f in &fields {
        let n = escape_identifier(local_name(text(f, "name")?))?;
        writeln!(out, "if let Some(value)={n}{{__cott_copy.{n}=value;}}").unwrap();
    }
    out.push_str(if recursive {
        "__cott_copy.__cott_validate();Box::new(__cott_copy)}\n"
    } else {
        "__cott_copy.__cott_validate();__cott_copy}\n"
    });
    let tuple_types = fields
        .iter()
        .map(|f| render_type_scoped(plan, &f["type"], d))
        .collect::<Result<Vec<_>, _>>()?;
    let tuple_values = fields
        .iter()
        .map(|f| {
            Ok(format!(
                "self.{}",
                escape_identifier(local_name(text(f, "name")?))?
            ))
        })
        .collect::<Result<Vec<_>, String>>()?;
    writeln!(
        out,
        "#[allow(dead_code)] pub(crate) fn __cott_into_fields(self)->({}{}){{({}{})}}",
        tuple_types.join(", "),
        if tuple_types.len() == 1 { "," } else { "" },
        tuple_values.join(", "),
        if tuple_values.len() == 1 { "," } else { "" }
    )
    .unwrap();
    out.push_str("pub(crate) fn __cott_validate(&self){\n");
    out.push_str(&const_checks(d, canonical)?);
    for f in &fields {
        out.push_str(&validate(
            plan,
            &f["type"],
            &format!("self.{}", escape_identifier(local_name(text(f, "name")?))?),
            canonical,
        )?);
    }
    for invariant in list(d, "invariants") {
        let expr = constructor_expression(&invariant["expression"], &fields, false);
        let predicate = expression(plan, &expr, d)?;
        let statement = format!(
            "crate::cott_runtime::__cott_check({},\"invariant\",{}, {predicate});",
            rust_string(canonical),
            rust_string(&format!("invariant:{}", invariant["clause_id"]))
        );
        let guard = invariant
            .get("guard")
            .map(|g| constructor_expression(g, &fields, false))
            .map(|g| lower_expression(plan, &g, d))
            .transpose()?;
        out.push_str(&render_guarded_statement(guard.as_ref(), &statement, None)?);
    }
    if let Some(refinement) = d.get("refinement").filter(|v| !v.is_null()) {
        let predicate = expression(plan, &constructor_expression(refinement, &fields, true), d)?;
        writeln!(
            out,
            "crate::cott_runtime::__cott_check({},\"refinement\",\"refinement\",{predicate});",
            rust_string(canonical)
        )
        .unwrap();
    }
    out.push_str("}\n}\n");
    writeln!(
        out,
        "impl{g} crate::cott_sealed::Sealed for {name}{a}{w}{{}}"
    )
    .unwrap();
    let needs = if metadata_recursive
        || !list(d, "invariants").is_empty()
        || d.get("refinement").is_some_and(|v| !v.is_null())
        || list(d, "generics").iter().any(|g| g["kind"] == "const")
    {
        "true".into()
    } else {
        tuple_types
            .iter()
            .map(|t| format!("<{t} as crate::cott_runtime::Value>::NEEDS_VALIDATION"))
            .collect::<Vec<_>>()
            .join(" || ")
    };
    let deep = if metadata_recursive {
        "true".to_owned()
    } else {
        tuple_types
            .iter()
            .map(|t| format!("<{t} as crate::cott_runtime::Value>::DEEP_SNAPSHOT"))
            .collect::<Vec<_>>()
            .join(" || ")
    };
    writeln!(out,"impl{g} crate::cott_runtime::Value for {name}{a}{w} {{const NEEDS_VALIDATION:bool={};const DEEP_SNAPSHOT:bool={};fn validate(&self){{self.__cott_validate();}}fn __cott_snapshot(&self)->Self{{ Self{{{} }} }} }}",if needs.is_empty(){"false"}else{&needs},if deep.is_empty(){"false"}else{&deep},fields.iter().map(|f|Ok(format!("{}:crate::cott_runtime::Value::__cott_snapshot(&self.{})",escape_identifier(local_name(text(f,"name")?))?,escape_identifier(local_name(text(f,"name")?))?))).collect::<Result<Vec<_>,String>>()?.into_iter().chain((!phantom.is_empty()).then_some("__cott_marker:std::marker::PhantomData".into())).collect::<Vec<_>>().join(", ")).unwrap();
    let args = fields
        .iter()
        .map(|f| {
            Ok(if has_default(f) {
                format!("Option<{}>", render_type_scoped(plan, &f["type"], d)?)
            } else {
                render_type_scoped(plan, &f["type"], d)?
            })
        })
        .collect::<Result<Vec<_>, String>>()?;
    let ctor = if recursive { "__cott_new_raw" } else { "new" };
    writeln!(out,"impl{g} crate::cott_runtime::ConstructionArguments for {name}{a}{w}{{type Arguments=({}{});}}\nimpl{g} crate::cott_runtime::Constructible for {name}{a}{w}{{fn construct(args:Self::Arguments)->Self{{let({}{})=args;Self::{ctor}({})}}}}",args.join(", "),if args.len()==1{","}else{""},fields.iter().map(|f|escape_identifier(local_name(text(f,"name").unwrap()))).collect::<Result<Vec<_>,_>>()?.join(", "),if fields.len()==1{","}else{""},fields.iter().map(|f|escape_identifier(local_name(text(f,"name").unwrap()))).collect::<Result<Vec<_>,_>>()?.join(", ")).unwrap();
    Ok(out)
}
fn declaration(
    config: &RustProjectConfig,
    plan: &RustPlan,
    d: &Value,
    bindings: &[RustBinding],
) -> Result<String, String> {
    let kind = text(d, "kind")?;
    if matches!(
        kind,
        "function" | "scenario" | "data" | "requirement" | "rule" | "specialization"
    ) {
        return Ok(String::new());
    }
    let name = escape_identifier(local_name(text(d, "name")?))?;
    Ok(match kind {
        "alias" => {
            let (g, _) = generics(d)?;
            format!(
                "#[allow(type_alias_bounds)]\npub type {name}{g} = {};\n",
                render_type_scoped(plan, &d["target"], d)?
            )
        }
        "external_type" => external(config, d)?,
        "struct" | "newtype" => nominal(plan, d)?,
        "enum" => enums::render(plan, d)?,
        "resource" => format!(
            "#[derive(Clone,Copy,Debug,PartialEq,Eq)]\npub enum {name}{{{}}}\nimpl crate::cott_sealed::Sealed for {name}{{}}\nimpl crate::cott_runtime::Value for {name}{{const NEEDS_VALIDATION:bool=false;fn validate(&self){{}}}}\nimpl crate::cott_runtime::ConstructionArguments for {name}{{type Arguments=Self;}}",
            list(d, "states")
                .iter()
                .map(|v| escape_identifier(local_name(text(v, "name")?)))
                .collect::<Result<Vec<_>, _>>()?
                .join(", ")
        ),
        "const" => {
            let primitive = d["type"]["kind"] == "primitive"
                && matches!(
                    d["type"]["name"].as_str(),
                    Some(
                        "bool"
                            | "i8"
                            | "i16"
                            | "i32"
                            | "i64"
                            | "u8"
                            | "u16"
                            | "u32"
                            | "u64"
                            | "f32"
                            | "f64"
                            | "unit"
                    )
                );
            let value = render_literal(plan, &d["value"], Some(&d["type"]), d)?;
            let ty = render_type_scoped(plan, &d["type"], d)?;
            format!(
                "#[allow(non_upper_case_globals)]\npub {} {name}: {} = {};\n",
                if primitive { "const" } else { "static" },
                if primitive {
                    ty
                } else {
                    format!("std::sync::LazyLock<{ty}>")
                },
                if primitive {
                    value
                } else {
                    format!("std::sync::LazyLock::new(||{value})")
                }
            )
        }
        "trait" => traits::render(plan, d, bindings)?,
        kind => return Err(format!("unsupported canonical declaration {kind}")),
    })
}
fn external(config: &RustProjectConfig, d: &Value) -> Result<String, String> {
    let canonical = text(d, "name")?;
    let name = escape_identifier(local_name(canonical))?;
    let native = config
        .rust
        .external_types
        .get(canonical)
        .ok_or_else(|| format!("external type {canonical} lacks native projection"))?;
    let mut out = format!("pub struct {name}(std::sync::Arc<{native}>);\n");
    writeln!(out,"impl {name}{{pub fn from_native(value:{native})->Self{{Self(std::sync::Arc::new(value))}}pub fn as_native(&self)->&{native}{{&self.0}}}}").unwrap();
    writeln!(
        out,
        "impl Clone for {name}{{fn clone(&self)->Self{{Self(self.0.clone())}}}}"
    )
    .unwrap();
    writeln!(out,"impl std::fmt::Debug for {name}{{fn fmt(&self,f:&mut std::fmt::Formatter<'_>)->std::fmt::Result{{f.write_str({name:?})}}}}").unwrap();
    writeln!(out,"impl PartialEq for {name}{{fn eq(&self,other:&Self)->bool{{use crate::cott_runtime::ExternalEqual as _;(&crate::cott_runtime::ExternalEquality::<{native}>(std::marker::PhantomData)).external_equal(&self.0,&other.0)}}}}").unwrap();
    writeln!(out,"impl crate::cott_sealed::Sealed for {name}{{}}\nimpl crate::cott_runtime::Value for {name}{{const NEEDS_VALIDATION:bool=false;fn validate(&self){{}}}}\nimpl crate::cott_runtime::ConstructionArguments for {name}{{type Arguments=();}}").unwrap();
    Ok(out)
}
#[derive(Default)]
struct ModuleTree {
    source: String,
    children: BTreeMap<String, ModuleTree>,
}
impl ModuleTree {
    fn insert(&mut self, path: &str, source: String) {
        let mut node = self;
        for part in path.split('.') {
            node = node.children.entry(part.into()).or_default();
        }
        node.source.push_str(&source);
    }
    fn render(&self) -> Result<String, String> {
        let mut out = self.source.clone();
        for (name, node) in &self.children {
            writeln!(
                out,
                "pub mod {}{{\n{}\n}}",
                escape_identifier(name)?,
                node.render()?
            )
            .unwrap();
        }
        Ok(out)
    }
}
pub(super) fn selected_binding<'a>(
    plan: &RustPlan,
    c: &RustCallable,
    bindings: &'a [RustBinding],
) -> Result<Option<&'a RustBinding>, String> {
    if let Some(binding) = bindings.iter().find(|b| b.cott_symbol == c.symbol) {
        return Ok(Some(binding));
    }
    if let Some(owner) = &c.owner {
        if let Some(slot) = list(owner, "selected_methods").iter().find(|s| {
            s.get("trait_method")
                .and_then(Value::as_str)
                .map(local_name)
                == Some(c.name.as_str())
        }) {
            if slot["selected"]["origin"] != "explicit" {
                let f = &slot["selected"]["function"];
                let symbol = format!("{}.{}", text(f, "module")?, text(f, "symbol")?);
                if !plan.callables().iter().any(|c| c.symbol == symbol) {
                    return Err(format!("missing selected implementation {symbol}"));
                }
                return Ok(bindings.iter().find(|b| b.cott_symbol == symbol));
            }
        }
    }
    Ok(None)
}
pub fn emit(
    config: &RustProjectConfig,
    plan: &RustPlan,
    bindings: &[RustBinding],
) -> Result<RustEmission, String> {
    let mut files = super::runtime::render_runtime(&config.project.name, &config.project.version);
    let runtime = files
        .get_mut(&PathBuf::from("rust/src/cott_runtime.rs"))
        .expect("compiler runtime");
    runtime.extend_from_slice(traits::runtime_projections(plan, bindings)?.as_bytes());
    runtime.extend_from_slice(tuples::runtime_projection(plan)?.as_bytes());
    if !config.rust.external_types.is_empty() {
        runtime.extend_from_slice(include_str!("runtime/external.rs").as_bytes());
    }
    let mut tree = ModuleTree::default();
    let mut impl_root = String::new();
    let mut unresolved = Vec::new();
    let mut public_symbols = BTreeMap::new();
    let mut seen = BTreeSet::new();
    for module in &plan.modules {
        let mut source = String::new();
        let mut names = Vec::new();
        for d in &module.declarations {
            source.push_str(&if d["kind"] == "impl" {
                state::render(config, plan, d, bindings)?
            } else {
                declaration(config, plan, d, bindings)?
            });
            if d["public"] == true {
                if let Some(n) = d.get("name").and_then(Value::as_str) {
                    names.push(local_name(n).to_owned());
                }
            }
        }
        for c in plan.callables().iter().filter(|c| c.module == module.name) {
            if selected_binding(plan, c, bindings)?.is_none() {
                unresolved.push(c.symbol.clone());
                continue;
            }
            if let Some(binding) = bindings.iter().find(|b| b.cott_symbol == c.symbol) {
                if c.owner.is_none() {
                    source.push_str(&facade(config, plan, c, binding)?);
                }
                if !seen.insert(c.symbol.clone()) {
                    return Err(format!("duplicate managed callable {}", c.symbol));
                }
                let path = binding
                    .runtime_origin
                    .strip_prefix("rust/src")
                    .map_err(|_| "managed implementation outside generated Rust source")?;
                if path
                    .components()
                    .any(|c| !matches!(c, std::path::Component::Normal(_)))
                {
                    return Err("unsafe managed implementation path".into());
                }
                let path = path.to_str().ok_or("non-UTF-8 implementation path")?;
                writeln!(
                    impl_root,
                    "#[path={:?}] pub(crate) mod {};",
                    format!("../{path}"),
                    private_name(c)
                )
                .unwrap();
                if files
                    .insert(
                        binding.runtime_origin.clone(),
                        managed_implementation_source(binding)?,
                    )
                    .is_some()
                {
                    return Err("duplicate managed implementation artifact".into());
                }
            }
        }
        tree.insert(&module.name, source);
        names.sort();
        names.dedup();
        public_symbols.insert(module.name.clone(), names);
    }
    for module in &plan.ir.modules {
        files.insert(
            PathBuf::from(format!(
                "ir/{}.json",
                module.module.as_string().replace('.', "/")
            )),
            module.bytes.clone(),
        );
    }
    files.insert(
        PathBuf::from("rust/src/cott_impl/mod.rs"),
        impl_root.into_bytes(),
    );
    files.insert(PathBuf::from("rust/src/lib.rs"),format!("// Generated by Cott. Do not edit.\n#![forbid(unsafe_code)]\nmod cott_sealed{{pub trait Sealed{{}}}}\npub mod cott_runtime;\nmod cott_impl;\npub mod modules{{\n{}\n}}\n",tree.render()?).into_bytes());
    Ok(RustEmission {
        files,
        public_symbols,
        unresolved,
    })
}
