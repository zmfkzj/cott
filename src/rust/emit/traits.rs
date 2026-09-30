use super::*;

fn declarations(plan: &RustPlan) -> impl Iterator<Item = &Value> {
    plan.modules.iter().flat_map(|m| &m.declarations)
}
fn trait_decl<'a>(plan: &'a RustPlan, name: &str) -> Result<&'a Value, String> {
    declarations(plan)
        .find(|d| d["kind"] == "trait" && d["name"] == name)
        .ok_or_else(|| format!("missing canonical trait {name}"))
}
fn bridge_name(name: &str) -> String {
    format!(
        "TraitDispatch_{}",
        &crate::hash::sha256_hex(name.as_bytes())[..16]
    )
}
fn slot_name(name: &str) -> String {
    format!(
        "Associated_{}",
        &crate::hash::sha256_hex(name.as_bytes())[..16]
    )
}
fn owner(slot: &Value) -> Result<&str, String> {
    text(slot, "name")?
        .rsplit_once('.')
        .map(|(o, _)| o)
        .ok_or_else(|| "associated slot lacks owner".into())
}
fn normalize_aliases(plan: &RustPlan, ty: &Value) -> Result<Value, String> {
    if ty["kind"] == "named" {
        if let Some(d) =
            declarations(plan).find(|d| d["kind"] == "alias" && d["name"] == ty["name"])
        {
            let substitutions = list(d, "generics")
                .iter()
                .zip(list(ty, "args"))
                .map(|(g, a)| {
                    Ok((
                        text(g, "name")?.to_owned(),
                        if a["kind"] == "type" {
                            a["type"].clone()
                        } else {
                            a["value"].clone()
                        },
                    ))
                })
                .collect::<Result<BTreeMap<_, _>, String>>()?;
            return normalize_aliases(plan, &substitute(&d["target"], &substitutions));
        }
    }
    match ty {
        Value::Object(o) => Ok(Value::Object(
            o.iter()
                .map(|(k, v)| Ok((k.clone(), normalize_aliases(plan, v)?)))
                .collect::<Result<_, String>>()?,
        )),
        Value::Array(a) => Ok(Value::Array(
            a.iter()
                .map(|v| normalize_aliases(plan, v))
                .collect::<Result<_, _>>()?,
        )),
        _ => Ok(ty.clone()),
    }
}
fn assignments(plan: &RustPlan, slot: &Value) -> Result<Vec<String>, String> {
    let mut types = std::collections::BTreeSet::new();
    for d in declarations(plan).filter(|d| d["kind"] == "impl") {
        for a in list(d, "associated_types") {
            if a["trait"] == owner(slot)?
                && local_name(text(a, "name")?) == local_name(text(slot, "name")?)
            {
                types.insert(render_type(plan, &normalize_aliases(plan, &a["type"])?)?);
            }
        }
    }
    Ok(types.into_iter().collect())
}
fn projected_slot(plan: &RustPlan, slot: &Value) -> Result<String, String> {
    let types = assignments(plan, slot)?;
    Ok(if types.len() == 1 {
        types[0].clone()
    } else {
        format!(
            "crate::cott_runtime::trait_values::{}",
            slot_name(text(slot, "name")?)
        )
    })
}
fn family_slot_name(root: &Value, slot: &Value) -> Result<String, String> {
    Ok(format!(
        "Family_{}_{}",
        bridge_name(text(root, "name")?),
        slot_name(text(slot, "name")?)
    ))
}
fn projected_slot_scoped(
    plan: &RustPlan,
    slot: &Value,
    root: Option<&Value>,
) -> Result<String, String> {
    if let Some(root) = root {
        if !list(root, "generics").is_empty() && assignments(plan, slot)?.len() != 1 {
            return Ok(format!(
                "crate::cott_runtime::trait_values::{}{}",
                family_slot_name(root, slot)?,
                generics(root)?.1
            ));
        }
    }
    projected_slot(plan, slot)
}
fn render_families(plan: &RustPlan, bindings: &[RustBinding]) -> Result<String, String> {
    let mut out = String::new();
    for root in
        declarations(plan).filter(|d| d["kind"] == "trait" && !list(d, "generics").is_empty())
    {
        let (g, a) = generics(root)?;
        for slot in list(root, "associated_types") {
            if assignments(plan, slot)?.len() == 1 {
                continue;
            }
            let family = family_slot_name(root, slot)?;
            let union = projected_slot(plan, slot)?;
            let marker = list(root, "generics")
                .iter()
                .map(|g| escape_identifier(text(g, "name")?))
                .collect::<Result<Vec<_>, _>>()?
                .join(",");
            writeln!(out,"#[allow(non_camel_case_types)]\n#[derive(Clone,Debug,PartialEq)]\npub struct {family}{g} {{ value: {union}, marker: std::marker::PhantomData<({marker},)> }}").unwrap();
            writeln!(
                out,
                "impl{g} crate::cott_sealed::Sealed for {family}{a} {{}}"
            )
            .unwrap();
            writeln!(out,"impl{g} crate::cott_runtime::Value for {family}{a} {{ const NEEDS_VALIDATION:bool=<{union} as crate::cott_runtime::Value>::NEEDS_VALIDATION; const DEEP_SNAPSHOT:bool=<{union} as crate::cott_runtime::Value>::DEEP_SNAPSHOT; fn validate(&self) {{ crate::cott_runtime::Value::validate(&self.value); }} fn __cott_snapshot(&self)->Self {{ Self {{ value:crate::cott_runtime::Value::__cott_snapshot(&self.value),marker:std::marker::PhantomData }} }} }}").unwrap();
            let owner_ref = references(root)
                .into_iter()
                .find(|r| r["name"] == owner(slot).unwrap_or(""))
                .ok_or("missing family slot owner")?;
            let owner_decl = trait_decl(plan, owner(slot)?)?;
            let substitutions = list(owner_decl, "generics")
                .iter()
                .zip(list(&owner_ref, "args"))
                .map(|(g, arg)| {
                    Ok((
                        text(g, "name")?.to_owned(),
                        if arg["kind"] == "type" {
                            arg["type"].clone()
                        } else {
                            arg["value"].clone()
                        },
                    ))
                })
                .collect::<Result<BTreeMap<_, _>, String>>()?;
            let mut bounds = BTreeMap::new();
            for bound in list(slot, "bounds") {
                for reference in instantiated_references(plan, &substitute(bound, &substitutions))?
                {
                    bounds.insert(native_trait_reference(plan, &reference)?, reference);
                }
            }
            for (native_ref, reference) in bounds {
                let bound = trait_decl(plan, text(&reference, "name")?)?;
                let data_ref = native_data_trait_reference(plan, &reference)?;
                writeln!(
                    out,
                    "impl{g} {data_ref} for {family}{a} where {union}:{data_ref} {{"
                )
                .unwrap();
                for associated in list(bound, "associated_types")
                    .iter()
                    .filter(|s| owner(s).ok() == bound["name"].as_str())
                {
                    let name = escape_identifier(local_name(text(associated, "name")?))?;
                    writeln!(out, "type {name}=<{union} as {data_ref}>::{name};").unwrap();
                }
                out.push_str("}\n");
                let ready = assignments(plan, slot)?.iter().all(|native| {
                    declarations(plan).any(|d| {
                        d["kind"] == "impl"
                            && render_canonical_symbol(text(d, "name").unwrap_or(""), None)
                                .ok()
                                .as_ref()
                                == Some(native)
                            && owner_ready(d, bindings)
                    })
                });
                if !ready {
                    continue;
                }
                writeln!(
                    out,
                    "impl{g} {native_ref} for {family}{a} where {union}:{native_ref} {{"
                )
                .unwrap();
                let substitutions = list(bound, "generics")
                    .iter()
                    .zip(list(&reference, "args"))
                    .map(|(g, arg)| {
                        Ok((
                            text(g, "name")?.to_owned(),
                            if arg["kind"] == "type" {
                                arg["type"].clone()
                            } else {
                                arg["value"].clone()
                            },
                        ))
                    })
                    .collect::<Result<BTreeMap<_, _>, String>>()?;
                for method in list(bound, "methods").iter().filter(|m| {
                    m["name"]
                        .as_str()
                        .and_then(|n| n.rsplit_once('.'))
                        .map(|(o, _)| o)
                        == bound["name"].as_str()
                }) {
                    let method = substitute(method, &substitutions);
                    let name = escape_identifier(local_name(text(&method, "name")?))?;
                    let params = list(&method, "parameters")
                        .iter()
                        .map(|p| {
                            Ok(format!(
                                "{}:{}",
                                escape_identifier(local_name(text(p, "name")?))?,
                                parameter_projection(plan, p, false, bound)?
                            ))
                        })
                        .collect::<Result<Vec<_>, String>>()?;
                    let args = list(&method, "parameters")
                        .iter()
                        .map(|p| escape_identifier(local_name(text(p, "name")?)))
                        .collect::<Result<Vec<_>, _>>()?;
                    let async_method = method["callable_kind"] == "async";
                    writeln!(out,"{}fn {name}{}(&mut self{}{}) -> {} {{ <{union} as {native_ref}>::{name}(&mut self.value{}{}){} }}",if async_method{"async "}else{""},generics(&method)?.0,if params.is_empty(){""}else{","},params.join(","),native_type(plan,&method["return_type"],bound)?,if args.is_empty(){""}else{","},args.join(","),if async_method{".await"}else{""}).unwrap();
                }
                out.push_str("}\n");
            }
            let mut from = std::collections::BTreeSet::new();
            for concrete in declarations(plan).filter(|d| d["kind"] == "impl") {
                let Some(reference) = implementation_references(plan, concrete)?
                    .into_iter()
                    .find(|r| r["name"] == root["name"])
                else {
                    continue;
                };
                let Some(assignment) = assignment_for(concrete, slot)? else {
                    continue;
                };
                let args = list(&reference, "args")
                    .iter()
                    .map(|arg| {
                        if arg["kind"] == "type" {
                            render_type(plan, &arg["type"])
                        } else {
                            consts::render_marker(&arg["value"], None)
                        }
                    })
                    .collect::<Result<Vec<_>, _>>()?
                    .join(", ");
                let target = format!("{family}<{args}>");
                let native = render_type(plan, &assignment["type"])?;
                let concrete = render_canonical_symbol(text(concrete, "name")?, None)?;
                writeln!(out,"impl SlotAdapter<{concrete}> for {target} {{ type Native={native}; fn close(value:{native})->Self {{ Self {{ value:<{union} as SlotAdapter<{concrete}>>::close(value),marker:std::marker::PhantomData }} }} fn open(value:Self)->{native} {{ <{union} as SlotAdapter<{concrete}>>::open(value.value) }} }}").unwrap();
                if from.insert((target.clone(), native.clone())) {
                    writeln!(out,"impl From<{native}> for {target} {{ fn from(value:{native})->Self {{ <Self as SlotAdapter<{concrete}>>::close(value) }} }}").unwrap();
                }
            }
        }
    }
    Ok(out)
}
pub(super) fn project_associated_type(
    plan: &RustPlan,
    base: &Value,
    trait_name: &str,
    slot_name: &str,
) -> Result<Option<String>, String> {
    if project_value_type(plan, base)?.is_none() {
        return Ok(None);
    }
    let d = trait_decl(plan, trait_name)?;
    let slot = list(d, "associated_types")
        .iter()
        .find(|s| s["name"].as_str().map(local_name) == Some(local_name(slot_name)))
        .ok_or_else(|| format!("missing associated slot {trait_name}.{slot_name}"))?;
    let reference = if base["kind"] == "dyn" {
        &base["trait"]
    } else {
        base
    };
    let root = trait_decl(plan, text(reference, "name")?)?;
    let projected = projected_slot_scoped(plan, slot, Some(root))?;
    let substitutions = list(root, "generics")
        .iter()
        .zip(list(reference, "args"))
        .map(|(g, a)| {
            Ok((
                escape_identifier(text(g, "name")?)?,
                if a["kind"] == "type" {
                    render_type(plan, &a["type"])?
                } else {
                    consts::render_marker(&a["value"], None)?
                },
            ))
        })
        .collect::<Result<BTreeMap<_, _>, String>>()?;
    Ok(Some(rewrite(projected, &substitutions)))
}
pub(super) fn native_data_trait_reference(plan: &RustPlan, ty: &Value) -> Result<String, String> {
    let mut reference = ty.clone();
    reference["name"] = Value::String(format!("{}Types", text(ty, "name")?));
    native_trait_reference(plan, &reference)
}
fn data_generics(d: &Value) -> Result<(String, String), String> {
    let mut scope = d.clone();
    for generic in scope["generics"].as_array_mut().into_iter().flatten() {
        for bound in generic["bounds"].as_array_mut().into_iter().flatten() {
            if bound["kind"] == "named" {
                bound["name"] = Value::String(format!("{}Types", text(bound, "name")?));
            }
        }
    }
    generics(&scope)
}
pub(super) fn render_impl_types(plan: &RustPlan, d: &Value) -> Result<String, String> {
    let concrete = render_canonical_symbol(text(d, "name")?, None)?;
    let mut out = String::new();
    for reference in implementation_references(plan, d)? {
        let declaration = trait_decl(plan, text(&reference, "name")?)?;
        writeln!(
            out,
            "impl {} for {concrete} {{",
            native_data_trait_reference(plan, &reference)?
        )
        .unwrap();
        for slot in list(declaration, "associated_types")
            .iter()
            .filter(|s| owner(s).ok() == declaration["name"].as_str())
        {
            let assignment = assignment_for(d, slot)?.ok_or_else(|| {
                format!(
                    "missing associated assignment {} on {}",
                    text(slot, "name").unwrap_or(""),
                    text(d, "name").unwrap_or("")
                )
            })?;
            writeln!(
                out,
                "type {} = {};",
                escape_identifier(local_name(text(slot, "name")?))?,
                render_type(plan, &assignment["type"])?
            )
            .unwrap();
        }
        out.push_str("}\n");
    }
    Ok(out)
}
pub(super) fn native_trait_reference(plan: &RustPlan, ty: &Value) -> Result<String, String> {
    let name = render_canonical_symbol(text(ty, "name")?, None)?;
    let args = list(ty, "args")
        .iter()
        .map(|a| {
            if a["kind"] == "type" {
                render_type(plan, &a["type"])
            } else {
                consts::render_marker(&a["value"], None)
            }
        })
        .collect::<Result<Vec<_>, _>>()?;
    Ok(if args.is_empty() {
        name
    } else {
        format!("{name}<{}>", args.join(", "))
    })
}
pub(super) fn project_value_type(plan: &RustPlan, ty: &Value) -> Result<Option<String>, String> {
    let reference = if ty["kind"] == "dyn" {
        &ty["trait"]
    } else {
        ty
    };
    if reference["kind"] != "named" {
        return Ok(None);
    }
    let name = text(reference, "name")?;
    if !declarations(plan).any(|d| d["kind"] == "trait" && d["name"] == name) {
        return Ok(None);
    }
    let args = list(reference, "args")
        .iter()
        .map(|a| {
            if a["kind"] == "type" {
                render_type(plan, &a["type"])
            } else {
                consts::render_marker(&a["value"], None)
            }
        })
        .collect::<Result<Vec<_>, _>>()?;
    let args = if args.is_empty() {
        String::new()
    } else {
        format!("<{}>", args.join(", "))
    };
    Ok(Some(format!(
        "crate::cott_runtime::Dyn<dyn crate::cott_runtime::trait_values::{}{args}>",
        bridge_name(name)
    )))
}
pub(super) fn borrowed_parameter_type(
    plan: &RustPlan,
    ty: &Value,
) -> Result<Option<String>, String> {
    if ty["kind"] != "named" {
        return Ok(None);
    }
    Ok(project_value_type(plan, ty)?.map(|value| {
        let dispatch = value
            .strip_prefix("crate::cott_runtime::Dyn<")
            .and_then(|v| v.strip_suffix('>'))
            .expect("generated Dyn projection");
        format!("&mut {dispatch}")
    }))
}
fn map_type(
    plan: &RustPlan,
    ty: &Value,
    projection: &dyn Fn(&Value) -> Result<String, String>,
) -> Result<String, String> {
    let r = |key: &str| map_type(plan, &ty[key], projection);
    Ok(match text(ty, "kind")? {
        "associated_projection" => projection(ty)?,
        "named" => {
            let canonical = text(ty, "name")?;
            let is_trait =
                declarations(plan).any(|d| d["kind"] == "trait" && d["name"] == canonical);
            let name = if is_trait {
                format!(
                    "dyn crate::cott_runtime::trait_values::{}",
                    bridge_name(canonical)
                )
            } else {
                render_canonical_symbol(canonical, None)?
            };
            let args = list(ty, "args")
                .iter()
                .map(|a| {
                    if a["kind"] == "type" {
                        map_type(plan, &a["type"], projection)
                    } else {
                        consts::render_marker(&a["value"], None)
                    }
                })
                .collect::<Result<Vec<_>, _>>()?;
            let projected = if args.is_empty() {
                name
            } else {
                format!("{name}<{}>", args.join(", "))
            };
            if is_trait {
                format!("crate::cott_runtime::Dyn<{projected}>")
            } else {
                projected
            }
        }
        "list" => format!("Vec<{}>", r("item")?),
        "set" => format!("crate::cott_runtime::Set<{}>", r("item")?),
        "map" => format!("crate::cott_runtime::Map<{}, {}>", r("key")?, r("value")?),
        "option" => format!("Option<{}>", r("item")?),
        "result" => format!("Result<{}, {}>", r("ok")?, r("error")?),
        "array" => format!(
            "crate::cott_runtime::Array<{}, {}>",
            r("item")?,
            consts::render_marker(&ty["length"], None)?
        ),
        "iterator" => format!("crate::cott_runtime::IteratorValue<{}>", r("item")?),
        "async_iterator" => format!("crate::cott_runtime::AsyncIteratorValue<{}>", r("item")?),
        "generator" => format!(
            "crate::cott_runtime::Generator<{}, {}, {}>",
            r("yield")?,
            r("send")?,
            r("return")?
        ),
        "async_generator" => format!(
            "crate::cott_runtime::AsyncGenerator<{}, {}>",
            r("yield")?,
            r("send")?
        ),
        "factory" => format!("crate::cott_runtime::Factory<{}>", r("instance")?),
        "tuple" => {
            let parts = list(ty, "items")
                .iter()
                .map(|v| map_type(plan, v, projection))
                .collect::<Result<Vec<_>, _>>()?;
            format!(
                "({}{})",
                parts.join(", "),
                if parts.len() == 1 { "," } else { "" }
            )
        }
        _ => render_type(plan, ty)?,
    })
}
fn native_type(plan: &RustPlan, ty: &Value, scope: &Value) -> Result<String, String> {
    map_type(plan, ty, &|p| {
        let own_slot = list(scope, "associated_types").iter().any(|slot| {
            owner(slot).ok() == p["trait"].as_str()
                && slot["name"].as_str().map(local_name) == p["name"].as_str().map(local_name)
        });
        if existential_projection(plan, p)? && own_slot {
            Ok(format!(
                "Self::{}",
                escape_identifier(local_name(text(p, "name")?))?
            ))
        } else {
            render_type_scoped(plan, p, scope)
        }
    })
}
fn parameter_projection(
    plan: &RustPlan,
    p: &Value,
    bridge: bool,
    scope: &Value,
) -> Result<String, String> {
    let mut ty = if bridge {
        bridge_type_scoped(plan, &p["type"], Some(scope))?
    } else {
        native_type(plan, &p["type"], scope)?
    };
    if borrowed_parameter_type(plan, &p["type"])?.is_some() {
        let dispatch = ty
            .strip_prefix("crate::cott_runtime::Dyn<")
            .and_then(|v| v.strip_suffix('>'))
            .ok_or("missing contextual trait value projection")?;
        ty = format!("&mut {dispatch}");
    }
    Ok(
        match p
            .get("kind")
            .and_then(Value::as_str)
            .unwrap_or("positional")
        {
            "positional" | "keyword_only" => ty,
            "vararg" => format!("Vec<{ty}>"),
            "kwarg" => format!("crate::cott_runtime::Map<String, {ty}>"),
            other => return Err(format!("unsupported canonical parameter kind {other}")),
        },
    )
}
pub(super) fn render(
    plan: &RustPlan,
    d: &Value,
    _bindings: &[RustBinding],
) -> Result<String, String> {
    let name = escape_identifier(local_name(text(d, "name")?))?;
    let (g, _) = generics(d)?;
    let parents = list(d, "parents")
        .iter()
        .map(|p| native_trait_reference(plan, &p["trait"]))
        .collect::<Result<Vec<_>, _>>()?;
    let (data_g, data_a) = data_generics(d)?;
    let data_parents = list(d, "parents")
        .iter()
        .map(|p| native_data_trait_reference(plan, &p["trait"]))
        .collect::<Result<Vec<_>, _>>()?;
    let mut out = format!(
        "pub trait {name}Types{data_g}: crate::cott_sealed::Sealed + std::marker::Send + std::marker::Sync{} {{\n",
        data_parents
            .iter()
            .map(|p| format!(" + {p}"))
            .collect::<String>()
    );
    for slot in list(d, "associated_types")
        .iter()
        .filter(|s| owner(s).ok() == d["name"].as_str())
    {
        let mut bounds = vec![
            "crate::cott_runtime::Value".to_owned(),
            "std::clone::Clone".to_owned(),
            "std::cmp::PartialEq".to_owned(),
            "std::fmt::Debug".to_owned(),
            "std::marker::Send".to_owned(),
            "std::marker::Sync".to_owned(),
            "'static".to_owned(),
        ];
        for b in list(slot, "bounds") {
            bounds.push(native_data_trait_reference(plan, b)?);
        }
        writeln!(
            out,
            "type {}: {};",
            escape_identifier(local_name(text(slot, "name")?))?,
            bounds.join(" + ")
        )
        .unwrap();
    }
    out.push_str("}\n");
    writeln!(
        out,
        "pub trait {name}{g}: {name}Types{data_a}{} {{",
        parents
            .iter()
            .map(|p| format!(" + {p}"))
            .collect::<String>()
    )
    .unwrap();
    for method in list(d, "methods").iter().filter(|m| {
        m["name"]
            .as_str()
            .and_then(|n| n.rsplit_once('.'))
            .map(|(o, _)| o)
            == d["name"].as_str()
    }) {
        let mut params = list(method, "parameters")
            .iter()
            .map(|p| {
                Ok(format!(
                    "{}: {}",
                    escape_identifier(local_name(text(p, "name")?))?,
                    parameter_projection(plan, p, false, d)?
                ))
            })
            .collect::<Result<Vec<_>, String>>()?;
        params.insert(0, "&mut self".into());
        let ret = native_type(plan, &method["return_type"], d)?;
        writeln!(
            out,
            "fn {}{}({}) -> {};",
            escape_identifier(local_name(text(method, "name")?))?,
            generics(method)?.0,
            params.join(", "),
            if method["callable_kind"] == "async" {
                format!("impl Future<Output = {ret}> + Send")
            } else {
                ret
            }
        )
        .unwrap();
    }
    out.push_str("}\n");
    let (_, arguments) = generics(d)?;
    let alias_generics = list(d, "generics")
        .iter()
        .map(|g| {
            if g["kind"] == "const" {
                let mut single = d.clone();
                single["generics"] = serde_json::json!([g]);
                generics(&single).map(|(decl, _)| {
                    decl.trim_start_matches('<')
                        .trim_end_matches('>')
                        .to_owned()
                })
            } else {
                escape_identifier(text(g, "name")?)
            }
        })
        .collect::<Result<Vec<_>, _>>()?;
    let alias_generics = if alias_generics.is_empty() {
        String::new()
    } else {
        format!("<{}>", alias_generics.join(", "))
    };
    writeln!(out, "pub type {name}Value{alias_generics} = crate::cott_runtime::Dyn<dyn crate::cott_runtime::trait_values::{}{arguments}>;", bridge_name(text(d,"name")?)).unwrap();
    for slot in list(d, "associated_types") {
        let alias = escape_identifier(&format!(
            "{}{}",
            local_name(text(d, "name")?),
            local_name(text(slot, "name")?)
        ))?;
        let slot_generics = if assignments(plan, slot)?.len() == 1 {
            ""
        } else {
            &alias_generics
        };
        writeln!(
            out,
            "pub type {alias}{slot_generics} = {};",
            projected_slot_scoped(plan, slot, Some(d))?
        )
        .unwrap();
    }
    Ok(out)
}
fn existential_projection(plan: &RustPlan, ty: &Value) -> Result<bool, String> {
    let base = &ty["base"];
    Ok((base["kind"] == "type_parameter" && base["name"] == "Self")
        || project_value_type(plan, base)?.is_some())
}
fn bridge_type_scoped(
    plan: &RustPlan,
    ty: &Value,
    scope: Option<&Value>,
) -> Result<String, String> {
    map_type(plan, ty, &|p| {
        if !existential_projection(plan, p)? {
            return if let Some(scope) = scope {
                render_type_scoped(plan, p, scope)
            } else {
                render_type(plan, p)
            };
        }
        let d = trait_decl(plan, text(p, "trait")?)?;
        let slot = list(d, "associated_types")
            .iter()
            .find(|s| {
                local_name(text(s, "name").unwrap_or(""))
                    == local_name(text(p, "name").unwrap_or(""))
            })
            .ok_or("missing associated slot")?;
        projected_slot_scoped(plan, slot, scope)
    })
}
fn substitute(value: &Value, substitutions: &BTreeMap<String, Value>) -> Value {
    if matches!(
        value["kind"].as_str(),
        Some("type_parameter" | "parameter" | "const_parameter")
    ) {
        if let Some(replacement) = value["name"].as_str().and_then(|n| substitutions.get(n)) {
            return replacement.clone();
        }
    }
    match value {
        Value::Object(o) => Value::Object(
            o.iter()
                .map(|(k, v)| (k.clone(), substitute(v, substitutions)))
                .collect(),
        ),
        Value::Array(a) => Value::Array(a.iter().map(|v| substitute(v, substitutions)).collect()),
        _ => value.clone(),
    }
}
fn references(d: &Value) -> Vec<Value> {
    let mut refs = list(d, "closure").to_vec();
    refs.push(serde_json::json!({
        "kind":"named", "name":d["name"],
        "args":list(d,"generics").iter().map(|g| {
            if g["kind"] == "const" {
                serde_json::json!({"kind":"const","value":{"kind":"parameter","name":g["name"],"type":g["type"]}})
            } else {
                serde_json::json!({"kind":"type","type":{"kind":"type_parameter","name":g["name"]}})
            }
        }).collect::<Vec<_>>()
    }));
    refs
}
fn methods(plan: &RustPlan, d: &Value) -> Result<Vec<(Value, Value)>, String> {
    let mut result = Vec::new();
    for reference in references(d) {
        let parent = trait_decl(plan, text(&reference, "name")?)?;
        let substitutions = list(parent, "generics")
            .iter()
            .zip(list(&reference, "args"))
            .map(|(g, a)| {
                Ok((
                    text(g, "name")?.to_owned(),
                    if a["kind"] == "type" {
                        a["type"].clone()
                    } else {
                        a["value"].clone()
                    },
                ))
            })
            .collect::<Result<BTreeMap<_, _>, String>>()?;
        for m in list(parent, "methods").iter().filter(|m| {
            m["name"]
                .as_str()
                .and_then(|n| n.rsplit_once('.'))
                .map(|(o, _)| o)
                == parent["name"].as_str()
        }) {
            result.push((reference.clone(), substitute(m, &substitutions)));
        }
    }
    Ok(result)
}
fn slot_for_projection<'a>(plan: &'a RustPlan, ty: &Value) -> Result<&'a Value, String> {
    let d = trait_decl(plan, text(ty, "trait")?)?;
    list(d, "associated_types")
        .iter()
        .find(|s| {
            local_name(text(s, "name").unwrap_or("")) == local_name(text(ty, "name").unwrap_or(""))
        })
        .ok_or_else(|| "missing associated slot".into())
}
fn needs_conversion(plan: &RustPlan, ty: &Value) -> Result<bool, String> {
    if ty["kind"] == "associated_projection" {
        if !existential_projection(plan, ty)? {
            return Ok(false);
        }
        return Ok(assignments(plan, slot_for_projection(plan, ty)?)?.len() != 1);
    }
    match ty {
        Value::Array(a) => {
            for v in a {
                if needs_conversion(plan, v)? {
                    return Ok(true);
                }
            }
        }
        Value::Object(o) => {
            for v in o.values() {
                if needs_conversion(plan, v)? {
                    return Ok(true);
                }
            }
        }
        _ => {}
    }
    Ok(false)
}
fn convert_nominal(
    plan: &RustPlan,
    ty: &Value,
    value: &str,
    outward: bool,
    concrete: &str,
    root: Option<&Value>,
) -> Result<String, String> {
    let name = text(ty, "name")?;
    let d = declarations(plan)
        .find(|d| d["name"] == name)
        .ok_or_else(|| format!("missing nominal projection {name}"))?;
    let substitutions = list(d, "generics")
        .iter()
        .zip(list(ty, "args"))
        .map(|(g, a)| {
            Ok((
                text(g, "name")?.to_owned(),
                if a["kind"] == "type" {
                    a["type"].clone()
                } else {
                    a["value"].clone()
                },
            ))
        })
        .collect::<Result<BTreeMap<_, _>, String>>()?;
    if d["kind"] == "alias" {
        return convert_as_scoped(
            plan,
            &substitute(&d["target"], &substitutions),
            value,
            outward,
            concrete,
            root,
        );
    }
    let path = render_canonical_symbol(name, None)?;
    if d["kind"] == "struct" || d["kind"] == "newtype" {
        let fields = if d["kind"] == "newtype" {
            vec![serde_json::json!({"type":d["carrier"]})]
        } else {
            list(d, "fields").to_vec()
        };
        let mut names = Vec::new();
        let mut values = Vec::new();
        for (i, field) in fields.iter().enumerate() {
            let binding = format!("__cott_field_{i}");
            let ty = substitute(&field["type"], &substitutions);
            let mapped = convert_as_scoped(plan, &ty, &binding, outward, concrete, root)?;
            values.push(if field.get("default").is_some_and(|v| !v.is_null()) {
                format!("Some({mapped})")
            } else {
                mapped
            });
            names.push(binding);
        }
        return Ok(format!(
            "{{ let ({}{}) = ({value}).__cott_into_fields(); {path}::new({}) }}",
            names.join(", "),
            if names.len() == 1 { "," } else { "" },
            values.join(", ")
        ));
    }
    if d["kind"] == "enum" {
        let mut arms = Vec::new();
        for variant in list(d, "variants") {
            let variant_name = escape_identifier(local_name(text(variant, "name")?))?;
            let mut bindings = Vec::new();
            let mut mapped = Vec::new();
            for (i, field) in list(variant, "fields").iter().enumerate() {
                let binding = format!("__cott_field_{i}");
                mapped.push(convert_as_scoped(
                    plan,
                    &substitute(field.get("type").unwrap_or(field), &substitutions),
                    &binding,
                    outward,
                    concrete,
                    root,
                )?);
                bindings.push(binding);
            }
            let pattern = if bindings.is_empty() {
                format!("{path}::{variant_name}")
            } else {
                format!("{path}::{variant_name}({})", bindings.join(", "))
            };
            let result = if mapped.is_empty() {
                format!("{path}::{variant_name}")
            } else {
                format!("{path}::{variant_name}({})", mapped.join(", "))
            };
            arms.push(format!("{pattern} => {result}"));
        }
        let fields = list(d, "variants")
            .iter()
            .flat_map(|v| list(v, "fields"))
            .collect::<Vec<_>>();
        if list(d, "generics").iter().any(|g| {
            g["kind"] == "type"
                && !fields
                    .iter()
                    .any(|f| contains_type_parameter(f, local_name(text(g, "name").unwrap_or(""))))
        }) {
            arms.push(format!(
                "{path}::__cott_marker(_, never) => match never {{}}"
            ));
        }
        return Ok(format!("match {value} {{ {} }}", arms.join(", ")));
    }
    Err(format!(
        "canonical {name} cannot structurally map associated type arguments"
    ))
}
fn convert(
    plan: &RustPlan,
    ty: &Value,
    value: &str,
    outward: bool,
    root: Option<&Value>,
) -> Result<String, String> {
    convert_as_scoped(plan, ty, value, outward, "CottConcrete", root)
}
fn convert_as(
    plan: &RustPlan,
    ty: &Value,
    value: &str,
    outward: bool,
    concrete: &str,
) -> Result<String, String> {
    convert_as_scoped(plan, ty, value, outward, concrete, None)
}
fn convert_as_scoped(
    plan: &RustPlan,
    ty: &Value,
    value: &str,
    outward: bool,
    concrete: &str,
    root: Option<&Value>,
) -> Result<String, String> {
    if !needs_conversion(plan, ty)? {
        return Ok(value.to_owned());
    }
    let nested = |key: &str, v: &str| convert_as_scoped(plan, &ty[key], v, outward, concrete, root);
    Ok(match text(ty, "kind")? {
        "named" => convert_nominal(plan, ty, value, outward, concrete, root)?,
        "associated_projection" => {
            let projected = bridge_type_scoped(plan, ty, root)?;
            if outward {
                format!(
                    "<{projected} as crate::cott_runtime::trait_values::SlotAdapter<{concrete}>>::close({value})"
                )
            } else {
                format!(
                    "<{projected} as crate::cott_runtime::trait_values::SlotAdapter<{concrete}>>::open({value})"
                )
            }
        }
        "set" => format!(
            "crate::cott_runtime::Set::__cott_from_unique(({value}).into_vec().into_iter().map(|value| {}).collect())",
            nested("item", "value")?
        ),
        "map" => format!(
            "crate::cott_runtime::Map::__cott_from_unique(({value}).into_vec().into_iter().map(|(key,value)| ({}, {})).collect())",
            nested("key", "key")?,
            nested("value", "value")?
        ),
        "option" => format!("({value}).map(|value| {})", nested("item", "value")?),
        "result" => format!(
            "({value}).map(|value| {}).map_err(|value| {})",
            nested("ok", "value")?,
            nested("error", "value")?
        ),
        "list" => format!(
            "({value}).into_iter().map(|value| {}).collect()",
            nested("item", "value")?
        ),
        "array" => format!("({value}).map(|value| {})", nested("item", "value")?),
        "iterator" | "async_iterator" => {
            format!("({value}).map(|value| {})", nested("item", "value")?)
        }
        "generator" => format!(
            "({value}).map(|value| {}, |value| {}, |value| {})",
            nested("yield", "value")?,
            convert_as_scoped(plan, &ty["send"], "value", !outward, concrete, root)?,
            nested("return", "value")?
        ),
        "async_generator" => format!(
            "({value}).map(|value| {}, |value| {})",
            nested("yield", "value")?,
            convert_as_scoped(plan, &ty["send"], "value", !outward, concrete, root)?
        ),
        "tuple" => {
            let parts = list(ty, "items")
                .iter()
                .enumerate()
                .map(|(i, t)| {
                    convert_as_scoped(
                        plan,
                        t,
                        &format!("__cott_tuple.{i}"),
                        outward,
                        concrete,
                        root,
                    )
                })
                .collect::<Result<Vec<_>, _>>()?;
            if parts.len() > 12 {
                return Ok(format!(
                    "{{ let __cott_tuple = {value}; crate::cott_runtime::Tuple{}({}) }}",
                    parts.len(),
                    parts.join(", ")
                ));
            }
            format!(
                "{{ let __cott_tuple = {value}; ({}{}) }}",
                parts.join(", "),
                if parts.len() == 1 { "," } else { "" }
            )
        }
        _ => value.to_owned(),
    })
}
fn bridge_signature(plan: &RustPlan, m: &Value, scope: &Value) -> Result<String, String> {
    if !list(m, "generics").is_empty() {
        return Err(format!(
            "generic dynamic trait method {} requires a closed generic dispatch projection",
            text(m, "name")?
        ));
    }
    let borrowed = list(m, "parameters").iter().any(|p| {
        borrowed_parameter_type(plan, &p["type"])
            .ok()
            .flatten()
            .is_some()
    });
    let lifetime = if borrowed { "'cott" } else { "'_" };
    let mut params = list(m, "parameters")
        .iter()
        .map(|p| {
            let ty = parameter_projection(plan, p, true, scope)?;
            let ty = if borrowed {
                ty.replace("&mut dyn ", "&'cott mut dyn ")
            } else {
                ty
            };
            Ok(format!(
                "{}: {ty}",
                escape_identifier(local_name(text(p, "name")?))?
            ))
        })
        .collect::<Result<Vec<_>, String>>()?;
    params.insert(
        0,
        if borrowed {
            "&'cott mut self".into()
        } else {
            "&mut self".into()
        },
    );
    let ret = bridge_type_scoped(plan, &m["return_type"], Some(scope))?;
    Ok(format!(
        "fn {}{}({}) -> {}",
        escape_identifier(local_name(text(m, "name")?))?,
        if borrowed { "<'cott>" } else { "" },
        params.join(", "),
        if m["callable_kind"] == "async" {
            format!("std::pin::Pin<Box<dyn Future<Output = {ret}> + Send + {lifetime}>>")
        } else {
            ret
        }
    ))
}
pub(super) fn value_constraints(plan: &RustPlan, scope: &Value) -> Result<Vec<String>, String> {
    fn arguments(d: &Value, reference: &Value) -> Result<BTreeMap<String, Value>, String> {
        list(d, "generics")
            .iter()
            .zip(list(reference, "args"))
            .map(|(g, a)| {
                Ok((
                    text(g, "name")?.to_owned(),
                    if a["kind"] == "type" {
                        a["type"].clone()
                    } else {
                        a["value"].clone()
                    },
                ))
            })
            .collect()
    }
    fn visit(
        plan: &RustPlan,
        ty: &Value,
        constraints: &mut std::collections::BTreeSet<String>,
    ) -> Result<(), String> {
        if ty["kind"] == "associated_projection" {
            return Ok(());
        }
        if ty["kind"] == "dyn" {
            return visit(plan, &ty["trait"], constraints);
        }
        if ty["kind"] == "named" {
            if let Some(d) =
                declarations(plan).find(|d| d["kind"] == "trait" && d["name"] == ty["name"])
            {
                if list(d, "generics").len() == list(ty, "args").len() {
                    let root_arguments = arguments(d, ty)?;
                    for slot in list(d, "associated_types") {
                        let slot_owner = trait_decl(plan, owner(slot)?)?;
                        let owner_ref = references(d)
                            .into_iter()
                            .find(|r| r["name"] == owner(slot).unwrap_or(""))
                            .ok_or("missing associated bound owner")?;
                        let owner_arguments =
                            arguments(slot_owner, &substitute(&owner_ref, &root_arguments))?;
                        for bound in list(slot, "bounds") {
                            let bound =
                                substitute(&substitute(bound, &owner_arguments), &root_arguments);
                            constraints.insert(format!(
                                "{}: {}",
                                projected_slot(plan, slot)?,
                                native_data_trait_reference(plan, &bound)?
                            ));
                        }
                    }
                }
            }
        }
        match ty {
            Value::Object(o) => {
                for v in o.values() {
                    visit(plan, v, constraints)?;
                }
            }
            Value::Array(a) => {
                for v in a {
                    visit(plan, v, constraints)?;
                }
            }
            _ => {}
        }
        Ok(())
    }
    fn declaration(
        plan: &RustPlan,
        scope: &Value,
        constraints: &mut std::collections::BTreeSet<String>,
    ) -> Result<(), String> {
        for key in ["return_type", "target", "carrier", "type"] {
            if let Some(ty) = scope.get(key) {
                visit(plan, ty, constraints)?;
            }
        }
        for key in ["parameters", "fields", "state"] {
            for field in list(scope, key) {
                visit(plan, &field["type"], constraints)?;
            }
        }
        for method in list(scope, "methods") {
            declaration(plan, method, constraints)?;
        }
        for generic in list(scope, "generics") {
            for bound in list(generic, "bounds") {
                for argument in list(bound, "args") {
                    if argument["kind"] == "type" {
                        visit(plan, &argument["type"], constraints)?;
                    }
                }
            }
        }
        for key in ["parents", "traits", "closure"] {
            for reference in list(scope, key) {
                let reference = reference.get("trait").unwrap_or(reference);
                for argument in list(reference, "args") {
                    if argument["kind"] == "type" {
                        visit(plan, &argument["type"], constraints)?;
                    }
                }
            }
        }
        Ok(())
    }
    let mut constraints = std::collections::BTreeSet::new();
    declaration(plan, scope, &mut constraints)?;
    Ok(constraints.into_iter().collect())
}
fn instantiated_references(plan: &RustPlan, reference: &Value) -> Result<Vec<Value>, String> {
    let d = trait_decl(plan, text(reference, "name")?)?;
    let substitutions = list(d, "generics")
        .iter()
        .zip(list(reference, "args"))
        .map(|(g, a)| {
            Ok((
                text(g, "name")?.to_owned(),
                if a["kind"] == "type" {
                    a["type"].clone()
                } else {
                    a["value"].clone()
                },
            ))
        })
        .collect::<Result<BTreeMap<_, _>, String>>()?;
    let mut refs = list(d, "closure")
        .iter()
        .map(|r| substitute(r, &substitutions))
        .collect::<Vec<_>>();
    refs.push(reference.clone());
    Ok(refs)
}
fn implementation_references(plan: &RustPlan, concrete: &Value) -> Result<Vec<Value>, String> {
    let mut refs = BTreeMap::new();
    for root in list(concrete, "traits") {
        for reference in instantiated_references(plan, root)? {
            let reference = normalize_aliases(plan, &reference)?;
            refs.insert(native_trait_reference(plan, &reference)?, reference);
        }
    }
    Ok(refs.into_values().collect())
}
fn assignment_for<'a>(concrete: &'a Value, slot: &Value) -> Result<Option<&'a Value>, String> {
    Ok(list(concrete, "associated_types").iter().find(|a| {
        a["trait"].as_str() == owner(slot).ok()
            && a["name"].as_str().map(local_name) == slot["name"].as_str().map(local_name)
    }))
}
fn owner_ready(concrete: &Value, bindings: &[RustBinding]) -> bool {
    list(concrete, "selected_methods").iter().all(|slot| {
        let direct = format!(
            "{}.{}",
            concrete["name"].as_str().unwrap_or(""),
            local_name(slot["trait_method"].as_str().unwrap_or(""))
        );
        if bindings.iter().any(|b| b.cott_symbol == direct) {
            return true;
        }
        if slot["selected"]["origin"] == "explicit" {
            return false;
        }
        let function = &slot["selected"]["function"];
        let selected = function["verified_facade"]
            .as_str()
            .map(str::to_owned)
            .unwrap_or_else(|| {
                format!(
                    "{}.{}",
                    function["module"].as_str().unwrap_or(""),
                    function["symbol"].as_str().unwrap_or("")
                )
            });
        bindings.iter().any(|b| b.cott_symbol == selected)
    })
}
fn render_slot_bounds(
    plan: &RustPlan,
    slot: &Value,
    types: &[String],
    bindings: &[RustBinding],
) -> Result<String, String> {
    if list(slot, "bounds").is_empty() {
        return Ok(String::new());
    }
    let union = slot_name(text(slot, "name")?);
    let mut bound_refs = BTreeMap::new();
    for concrete in declarations(plan).filter(|d| d["kind"] == "impl") {
        if assignment_for(concrete, slot)?.is_none() {
            continue;
        }
        let owner_ref = implementation_references(plan, concrete)?
            .into_iter()
            .find(|r| r["name"] == owner(slot).unwrap_or(""))
            .ok_or("missing associated trait instantiation")?;
        let owner_decl = trait_decl(plan, owner(slot)?)?;
        let substitutions = list(owner_decl, "generics")
            .iter()
            .zip(list(&owner_ref, "args"))
            .map(|(g, a)| {
                Ok((
                    text(g, "name")?.to_owned(),
                    if a["kind"] == "type" {
                        a["type"].clone()
                    } else {
                        a["value"].clone()
                    },
                ))
            })
            .collect::<Result<BTreeMap<_, _>, String>>()?;
        for bound in list(slot, "bounds") {
            for reference in instantiated_references(plan, &substitute(bound, &substitutions))? {
                let reference = normalize_aliases(plan, &reference)?;
                bound_refs.insert(native_trait_reference(plan, &reference)?, reference);
            }
        }
    }
    let mut out = String::new();
    let mut identity_slots = std::collections::BTreeSet::new();
    for (native_ref, reference) in bound_refs {
        let bound = trait_decl(plan, text(&reference, "name")?)?;
        let substitutions = list(bound, "generics")
            .iter()
            .zip(list(&reference, "args"))
            .map(|(g, a)| {
                Ok((
                    text(g, "name")?.to_owned(),
                    if a["kind"] == "type" {
                        a["type"].clone()
                    } else {
                        a["value"].clone()
                    },
                ))
            })
            .collect::<Result<BTreeMap<_, _>, String>>()?;
        for associated in list(bound, "associated_types") {
            if assignments(plan, associated)?.len() == 1 {
                continue;
            }
            let projected = projected_slot(plan, associated)?;
            if identity_slots.insert(projected.clone()) {
                writeln!(out,"impl SlotAdapter<{union}> for {projected} {{ type Native = Self; fn close(value: Self) -> Self {{ value }} fn open(value: Self) -> Self {{ value }} }}").unwrap();
            }
        }
        let data_ref = native_data_trait_reference(plan, &reference)?;
        writeln!(out, "impl {data_ref} for {union} {{").unwrap();
        for associated in list(bound, "associated_types")
            .iter()
            .filter(|s| owner(s).ok() == bound["name"].as_str())
        {
            writeln!(
                out,
                "type {} = {};",
                escape_identifier(local_name(text(associated, "name")?))?,
                projected_slot(plan, associated)?
            )
            .unwrap();
        }
        out.push_str("}\n");
        let mut callable = true;
        for native in types {
            let member = declarations(plan).find(|d| {
                d["kind"] == "impl"
                    && render_canonical_symbol(d["name"].as_str().unwrap_or(""), None)
                        .ok()
                        .as_ref()
                        == Some(native)
            });
            if member.is_none_or(|d| !owner_ready(d, bindings)) {
                callable = false;
            }
        }
        if !callable {
            continue;
        }
        writeln!(out, "impl {native_ref} for {union} {{").unwrap();
        for m in list(bound, "methods").iter().filter(|m| {
            m["name"]
                .as_str()
                .and_then(|n| n.rsplit_once('.'))
                .map(|(o, _)| o)
                == bound["name"].as_str()
        }) {
            let m = substitute(m, &substitutions);
            let method = escape_identifier(local_name(text(&m, "name")?))?;
            let mut parameters = vec!["&mut self".to_owned()];
            for p in list(&m, "parameters") {
                parameters.push(format!(
                    "{}: {}",
                    escape_identifier(local_name(text(p, "name")?))?,
                    parameter_projection(plan, p, false, bound)?
                ));
            }
            writeln!(
                out,
                "{}fn {method}({}) -> {} {{ match self {{",
                if m["callable_kind"] == "async" {
                    "async "
                } else {
                    ""
                },
                parameters.join(", "),
                native_type(plan, &m["return_type"], bound)?
            )
            .unwrap();
            for (index, native) in types.iter().enumerate() {
                let mut compatible = false;
                for concrete in declarations(plan).filter(|d| d["kind"] == "impl") {
                    if render_canonical_symbol(text(concrete, "name")?, None)? != *native {
                        continue;
                    }
                    compatible = implementation_references(plan, concrete)?.iter().any(|r| {
                        native_trait_reference(plan, r).ok().as_deref() == Some(native_ref.as_str())
                    });
                }
                if compatible {
                    let args = list(&m, "parameters")
                        .iter()
                        .map(|p| {
                            convert_as(
                                plan,
                                &p["type"],
                                &escape_identifier(local_name(text(p, "name")?))?,
                                false,
                                native,
                            )
                        })
                        .collect::<Result<Vec<_>, String>>()?;
                    let call = format!(
                        "<{native} as {native_ref}>::{method}(value{}{}){}",
                        if args.is_empty() { "" } else { ", " },
                        args.join(", "),
                        if m["callable_kind"] == "async" {
                            ".await"
                        } else {
                            ""
                        }
                    );
                    writeln!(
                        out,
                        "Self::Alternative{index}(value) => {},",
                        convert_as(plan, &m["return_type"], &call, true, native)?
                    )
                    .unwrap();
                } else {
                    writeln!(out,"Self::Alternative{index}(_) => crate::cott_runtime::violation(\"trait\",\"validation\",\"associated alternative does not satisfy this trait instantiation\"),").unwrap();
                }
            }
            out.push_str("} }\n");
        }
        out.push_str("}\n");
    }
    Ok(out)
}
pub(super) fn runtime_projections(
    plan: &RustPlan,
    bindings: &[RustBinding],
) -> Result<String, String> {
    if !declarations(plan).any(|d| d["kind"] == "trait") {
        return Ok(String::new());
    }
    let mut out = String::from("pub mod trait_values {\n");
    out.push_str("pub trait SlotAdapter<C>: Sized { type Native; fn close(value: Self::Native) -> Self; fn open(value: Self) -> Self::Native; }\n");
    let mut seen = std::collections::BTreeSet::new();
    for d in declarations(plan).filter(|d| d["kind"] == "trait") {
        for slot in list(d, "associated_types") {
            let name = text(slot, "name")?;
            if !seen.insert(name.to_owned()) {
                continue;
            }
            let types = assignments(plan, slot)?;
            if types.len() == 1 {
                continue;
            }
            let union = slot_name(name);
            writeln!(out, "#[allow(non_camel_case_types)]\n#[derive(Clone,Debug,PartialEq)]\npub enum {union} {{").unwrap();
            for (i, ty) in types.iter().enumerate() {
                writeln!(out, "Alternative{i}({ty}),").unwrap();
            }
            out.push_str("}\n");
            writeln!(out, "impl crate::cott_sealed::Sealed for {union} {{}}").unwrap();
            for concrete in declarations(plan).filter(|d| d["kind"] == "impl") {
                for assignment in list(concrete, "associated_types") {
                    if assignment["trait"] != owner(slot)?
                        || local_name(text(assignment, "name")?) != local_name(text(slot, "name")?)
                    {
                        continue;
                    }
                    let native = render_type(plan, &assignment["type"])?;
                    let normalized =
                        render_type(plan, &normalize_aliases(plan, &assignment["type"])?)?;
                    let index = types
                        .iter()
                        .position(|t| t == &normalized)
                        .ok_or("associated assignment missing closed alternative")?;
                    let concrete = render_canonical_symbol(text(concrete, "name")?, None)?;
                    writeln!(out,"impl SlotAdapter<{concrete}> for {union} {{ type Native = {native}; fn close(value: {native}) -> Self {{ Self::Alternative{index}(value) }} fn open(value: Self) -> {native} {{ match value {{ Self::Alternative{index}(value) => value, _ => crate::cott_runtime::violation(\"trait\", \"validation\", \"associated value belongs to another canonical implementation\") }} }} }}").unwrap();
                }
            }
            let needs = types
                .iter()
                .map(|ty| format!("<{ty} as crate::cott_runtime::Value>::NEEDS_VALIDATION"))
                .collect::<Vec<_>>()
                .join(" || ");
            let deep = types
                .iter()
                .map(|ty| format!("<{ty} as crate::cott_runtime::Value>::DEEP_SNAPSHOT"))
                .collect::<Vec<_>>()
                .join(" || ");
            writeln!(out, "impl crate::cott_runtime::Value for {union} {{ const NEEDS_VALIDATION:bool={}; const DEEP_SNAPSHOT:bool={}; fn validate(&self) {{ match {} {{", if needs.is_empty(){"false"}else{&needs},if deep.is_empty(){"false"}else{&deep}, if types.is_empty() { "*self" } else { "self" }).unwrap();
            for (i, _) in types.iter().enumerate() {
                writeln!(
                    out,
                    "Self::Alternative{i}(value)=>crate::cott_runtime::Value::validate(value),"
                )
                .unwrap();
            }
            out.push_str("} }\nfn __cott_snapshot(&self)->Self { match ");
            out.push_str(if types.is_empty() { "*self" } else { "self" });
            out.push_str(" {\n");
            for (i, _) in types.iter().enumerate() {
                writeln!(out,"Self::Alternative{i}(value) => Self::Alternative{i}(crate::cott_runtime::Value::__cott_snapshot(value)),").unwrap();
            }
            out.push_str("} } }\n");
            out.push_str(&render_slot_bounds(plan, slot, &types, bindings)?);
        }
    }
    out.push_str(&render_families(plan, bindings)?);
    for d in declarations(plan).filter(|d| d["kind"] == "trait") {
        let name = bridge_name(text(d, "name")?);
        let (g, a) = generics(d)?;
        writeln!(out, "#[allow(non_camel_case_types)]\npub trait {name}{g}: crate::cott_sealed::Sealed + Send + Sync {{").unwrap();
        out.push_str("#[doc(hidden)] fn __cott_trait_validate(&self);\n");
        let all_methods = methods(plan, d)?;
        for (_, m) in &all_methods {
            writeln!(out, "{};", bridge_signature(plan, m, d)?).unwrap();
        }
        out.push_str("}\n");
        let lifetime_generics = if g.is_empty() {
            "<'cott_value>".to_owned()
        } else {
            format!("<'cott_value, {}>", &g[1..g.len() - 1])
        };
        writeln!(out,"impl{lifetime_generics} crate::cott_runtime::Value for dyn {name}{a} + 'cott_value {{ const NEEDS_VALIDATION:bool=true; fn validate(&self) {{ self.__cott_trait_validate(); }} }}").unwrap();
        let mut gd = list(d, "generics").to_vec();
        gd.insert(
            0,
            serde_json::json!({"kind":"type","name":"CottConcrete","bounds":[]}),
        );
        let template = serde_json::json!({"generics":gd});
        let native = format!("{}{}", render_canonical_symbol(text(d, "name")?, None)?, a);
        let mut bounds = vec![format!("CottConcrete: {native}")];
        for slot in list(d, "associated_types") {
            let reference = references(d)
                .into_iter()
                .find(|r| r["name"] == owner(slot).unwrap_or(""))
                .ok_or("missing associated owner reference")?;
            let assoc = format!(
                "<CottConcrete as {}>::{}",
                native_data_trait_reference(plan, &reference)?,
                escape_identifier(local_name(text(slot, "name")?))?
            );
            let projected = projected_slot_scoped(plan, slot, Some(d))?;
            if assignments(plan, slot)?.len() == 1 {
                let reference = native_data_trait_reference(plan, &reference)?;
                let binding = format!(
                    "{} = {projected}",
                    escape_identifier(local_name(text(slot, "name")?))?
                );
                let reference = if let Some(prefix) = reference.strip_suffix('>') {
                    format!("{prefix}, {binding}>")
                } else {
                    format!("{reference}<{binding}>")
                };
                bounds.push(format!("CottConcrete: {reference}"));
            } else {
                bounds.push(format!("{projected}: crate::cott_runtime::trait_values::SlotAdapter<CottConcrete, Native = {assoc}>"));
            }
        }
        writeln!(
            out,
            "impl{} {name}{a} for CottConcrete where {} {{",
            generics(&template)?.0,
            bounds.join(", ")
        )
        .unwrap();
        out.push_str(
            "fn __cott_trait_validate(&self) { crate::cott_runtime::Value::validate(self); }\n",
        );
        for (owner_ref, m) in all_methods {
            let method = escape_identifier(local_name(text(&m, "name")?))?;
            let args = list(&m, "parameters")
                .iter()
                .map(|p| {
                    let name = escape_identifier(local_name(text(p, "name")?))?;
                    convert(plan, &p["type"], &name, false, Some(d))
                })
                .collect::<Result<Vec<_>, String>>()?;
            let owner_ref = native_trait_reference(plan, &owner_ref)?;
            let call = format!(
                "<CottConcrete as {owner_ref}>::{method}(self{}{}){}",
                if args.is_empty() { "" } else { ", " },
                args.join(", "),
                if m["callable_kind"] == "async" {
                    ".await"
                } else {
                    ""
                }
            );
            let call = convert(plan, &m["return_type"], &call, true, Some(d))?;
            writeln!(
                out,
                "{} {{ {} }}",
                bridge_signature(plan, &m, d)?,
                if m["callable_kind"] == "async" {
                    format!("Box::pin(async move {{ {call} }})")
                } else {
                    call
                }
            )
            .unwrap();
        }
        out.push_str("}\n");
    }
    out.push_str("}\n");
    Ok(out)
}
