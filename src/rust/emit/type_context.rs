use super::*;

pub(super) fn render(plan: &RustPlan, ty: &Value, scope: Option<&Value>) -> Result<String, String> {
    render_type_contextual(ty, None, Some(&Context { plan, scope }))
}
struct Context<'a> {
    plan: &'a RustPlan,
    scope: Option<&'a Value>,
}
impl RustTypeContext for Context<'_> {
    fn named_associated_arguments(&self, _ty: &Value, _name: &str) -> Result<Vec<String>, String> {
        Ok(Vec::new())
    }
    fn value_projection(&self, ty: &Value) -> Result<Option<String>, String> {
        if let Some(projected) = super::traits::project_value_type(self.plan, ty)? {
            return Ok(Some(projected));
        }
        if ty["kind"] == "named" {
            let name = text(ty, "name")?;
            if super::layout::recursive(self.plan, name) {
                let args = list(ty, "args")
                    .iter()
                    .map(|a| {
                        if a["kind"] == "const" {
                            super::consts::render_marker(&a["value"], None)
                        } else {
                            render_type_contextual(&a["type"], None, Some(self))
                        }
                    })
                    .collect::<Result<Vec<_>, _>>()?;
                let raw = render_canonical_symbol(name, None)?;
                return Ok(Some(format!(
                    "Box<{}{}>",
                    raw,
                    if args.is_empty() {
                        String::new()
                    } else {
                        format!("<{}>", args.join(", "))
                    }
                )));
            }
        }
        Ok(None)
    }
    fn associated_projection(
        &self,
        base: &Value,
        trait_name: &str,
        slot_name: &str,
    ) -> Result<String, String> {
        if let Some(projected) =
            super::traits::project_associated_type(self.plan, base, trait_name, slot_name)?
        {
            return Ok(projected);
        }
        let trait_ref = self.trait_reference(base, trait_name)?;
        Ok(format!(
            "<{} as {}>::{}",
            render_type_contextual(base, None, Some(self))?,
            super::traits::native_data_trait_reference(self.plan, &trait_ref)?,
            escape_identifier(local_name(slot_name))?
        ))
    }
}
impl Context<'_> {
    fn declaration(&self, name: &str) -> Option<&Value> {
        self.plan
            .modules
            .iter()
            .flat_map(|m| &m.declarations)
            .find(|d| d.get("name").and_then(Value::as_str) == Some(name))
    }
    fn scope_owner(&self) -> Option<&Value> {
        let scope = self.scope?;
        let name = scope.get("name").and_then(Value::as_str)?;
        if scope["kind"] == "trait" {
            Some(scope)
        } else {
            module_of(name)
                .and_then(|owner| self.declaration(owner))
                .filter(|d| d["kind"] == "trait")
        }
    }
    fn trait_reference(&self, base: &Value, name: &str) -> Result<Value, String> {
        let base_name = base.get("name").and_then(Value::as_str).unwrap_or("");
        let mut references = Vec::new();
        if base["kind"] == "type_parameter" && base_name == "Self" {
            if let Some(owner) = self.scope_owner() {
                references.push(declaration_reference(owner)?);
            }
        } else if base["kind"] == "type_parameter" {
            for scope in self.scope.into_iter().chain(self.scope_owner()) {
                if let Some(g) = list(scope, "generics").iter().find(|g| {
                    g.get("name").and_then(Value::as_str).map(local_name)
                        == Some(local_name(base_name))
                }) {
                    references.extend(list(g, "bounds").iter().cloned());
                }
            }
        } else if base["kind"] == "named" {
            if let Some(owner) = self.declaration(base_name) {
                references.extend(list(owner, "traits").iter().cloned());
            }
        }
        for reference in references {
            if reference.get("name").and_then(Value::as_str) == Some(name) {
                return Ok(reference);
            }
            if let Some(declaration) = reference
                .get("name")
                .and_then(Value::as_str)
                .and_then(|n| self.declaration(n))
            {
                for parent in list(declaration, "closure") {
                    let parent = instantiate(parent, declaration, &reference)?;
                    if parent.get("name").and_then(Value::as_str) == Some(name) {
                        return Ok(parent);
                    }
                }
            }
        }
        let declaration = self
            .declaration(name)
            .ok_or_else(|| format!("unknown associated trait {name}"))?;
        if list(declaration, "generics").is_empty() {
            return Ok(serde_json::json!({"kind":"named","name":name,"args":[]}));
        }
        Err(format!(
            "associated projection {base_name}.{slot} lacks native trait arguments for {name}",
            slot = local_name(name)
        ))
    }
}
pub(super) fn declaration_reference(declaration: &Value) -> Result<Value, String> {
    let args=list(declaration,"generics").iter().map(|g|if g["kind"]=="const"{Ok(serde_json::json!({"kind":"const","value":{"kind":"parameter","name":text(g,"name")?}}))}else{Ok(serde_json::json!({"kind":"type","type":{"kind":"type_parameter","name":text(g,"name")?}}))}).collect::<Result<Vec<_>,String>>()?;
    Ok(serde_json::json!({"kind":"named","name":text(declaration,"name")?,"args":args}))
}
pub(super) fn instantiate(
    value: &Value,
    declaration: &Value,
    reference: &Value,
) -> Result<Value, String> {
    let mut bindings = BTreeMap::new();
    for (g, arg) in list(declaration, "generics")
        .iter()
        .zip(list(reference, "args"))
    {
        bindings.insert(
            text(g, "name")?.to_owned(),
            if g["kind"] == "const" {
                arg["value"].clone()
            } else {
                arg["type"].clone()
            },
        );
    }
    fn visit(v: &mut Value, bindings: &BTreeMap<String, Value>) {
        match v {
            Value::Array(a) => {
                for v in a {
                    visit(v, bindings)
                }
            }
            Value::Object(o) => {
                let replacement = matches!(
                    o.get("kind").and_then(Value::as_str),
                    Some("type_parameter" | "parameter")
                )
                .then(|| {
                    o.get("name")
                        .and_then(Value::as_str)
                        .and_then(|name| bindings.get(name))
                        .cloned()
                })
                .flatten();
                if let Some(replacement) = replacement {
                    *v = replacement
                } else {
                    for (k, v) in o {
                        if k != "span" {
                            visit(v, bindings)
                        }
                    }
                }
            }
            _ => {}
        }
    }
    let mut result = value.clone();
    visit(&mut result, &bindings);
    Ok(result)
}
