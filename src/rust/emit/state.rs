use super::*;

fn old_referenced(value: &Value, field: &str) -> bool {
    match value {
        Value::Array(a) => a.iter().any(|v| old_referenced(v, field)),
        Value::Object(o) => {
            (o.get("kind").and_then(Value::as_str) == Some("old_state_field")
                && o.get("field").and_then(Value::as_str).map(local_name) == Some(field))
                || o.iter()
                    .filter(|(k, _)| !matches!(k.as_str(), "type" | "span"))
                    .any(|(_, v)| old_referenced(v, field))
        }
        _ => false,
    }
}
fn trait_closure(plan: &RustPlan, owner: &Value) -> Result<Vec<Value>, String> {
    let mut result = Vec::new();
    let mut seen = BTreeSet::new();
    for reference in list(owner, "traits") {
        let name = text(reference, "name")?;
        if seen.insert(reference.to_string()) {
            result.push(reference.clone());
        }
        let declaration =
            declaration_named(plan, name).ok_or_else(|| format!("unknown native trait {name}"))?;
        for parent in list(declaration, "closure") {
            let parent = type_context::instantiate(parent, declaration, reference)?;
            if seen.insert(parent.to_string()) {
                result.push(parent);
            }
        }
    }
    Ok(result)
}

pub(super) fn render(
    config: &RustProjectConfig,
    plan: &RustPlan,
    original: &Value,
    bindings: &[RustBinding],
) -> Result<String, String> {
    let mut d = original.clone();
    substitute_associated(&mut d, original);
    let canonical = text(&d, "name")?;
    let name = escape_identifier(local_name(canonical))?;
    let data = format!(
        "CottData{}",
        &crate::hash::sha256_hex(canonical.as_bytes())[..16]
    );
    let state = list(&d, "state");
    let operations = plan
        .callables()
        .iter()
        .filter(|c| c.owner.as_ref().is_some_and(|o| o["name"] == d["name"]))
        .any(|c| selected_binding(plan, c, bindings).ok().flatten().is_some());
    let gate_field = if operations {
        "gate:crate::cott_runtime::StateGate,"
    } else {
        ""
    };
    let gate_initial = if operations {
        "gate:crate::cott_runtime::StateGate::new(false),"
    } else {
        ""
    };
    let gate_snapshot = if operations {
        "gate:crate::cott_runtime::StateGate::new(true),"
    } else {
        ""
    };
    let mut out = format!(
        "#[derive(Clone)]\npub struct {name}{{inner:std::sync::Arc<{data}>}}\nstruct {data}{{{gate_field}"
    );
    for f in state {
        writeln!(
            out,
            "{}:tokio::sync::RwLock<Option<{}>>,",
            escape_identifier(local_name(text(f, "name")?))?,
            render_type_scoped(plan, &f["type"], &d)?
        )
        .unwrap();
    }
    out.push_str("}\n");
    writeln!(out,"impl std::fmt::Debug for {name}{{fn fmt(&self,f:&mut std::fmt::Formatter<'_>)->std::fmt::Result{{f.write_str({name:?})}}}}\nimpl crate::cott_sealed::Sealed for {name}{{}}\nimpl PartialEq for {name}{{fn eq(&self,other:&Self)->bool{{crate::cott_runtime::__cott_state_equal(self.__cott_id(),other.__cott_id(),||{{ {} }})}}}}",if state.is_empty(){"true".into()}else{state.iter().map(|f|Ok(format!("*self.{}()==*other.{}()",getter(f)?,getter(f)?))).collect::<Result<Vec<_>,String>>()?.join(" && ")}).unwrap();
    writeln!(
        out,
        "impl {name}{{\nfn __cott_id(&self)->usize{{std::sync::Arc::as_ptr(&self.inner) as usize}}"
    )
    .unwrap();
    let init = d.get("init").filter(|v| !v.is_null());
    let init_scope = init
        .cloned()
        .unwrap_or_else(|| serde_json::json!({"parameters":[]}));
    writeln!(
        out,
        "pub fn new({})->Self{{",
        public_parameters(plan, &init_scope)?.join(", ")
    )
    .unwrap();
    out.push_str(&defaults(plan, &init_scope)?);
    let init_symbol = format!("{canonical}.init");
    out.push_str(&effects(config, &init_scope, &init_symbol)?);
    out.push_str(&contract_checks(
        plan,
        &init_scope,
        &init_symbol,
        "requires",
        &config.rust.runtime_validation,
    )?);
    for p in list(&init_scope, "parameters") {
        out.push_str(&validate(
            plan,
            &p["type"],
            &escape_identifier(local_name(text(p, "name")?))?,
            &init_symbol,
        )?);
    }
    for field in state {
        let n = escape_identifier(local_name(text(field, "name")?))?;
        let from_param = list(&init_scope, "parameters").iter().any(|p| {
            p.get("name").and_then(Value::as_str).map(local_name)
                == Some(local_name(text(field, "name").unwrap()))
        });
        if from_param {
            writeln!(
                out,
                "let __cott_initial_{n}=crate::cott_runtime::Value::__cott_snapshot(&{n});"
            )
            .unwrap();
        } else {
            let default = field
                .get("default")
                .filter(|v| !v.is_null())
                .ok_or_else(|| {
                    format!("state field {canonical}.{n} has neither initializer nor default")
                })?;
            writeln!(
                out,
                "let __cott_initial_{n}={};",
                render_literal(plan, default, Some(&field["type"]), &d)?
            )
            .unwrap();
        }
    }
    writeln!(out,"let __cott_value=Self{{inner:std::sync::Arc::new({data}{{{gate_initial}{}}})}};__cott_value.__cott_validate();",state.iter().map(|f|Ok(format!("{}:tokio::sync::RwLock::new(Some(__cott_initial_{}))",escape_identifier(local_name(text(f,"name")?))?,escape_identifier(local_name(text(f,"name")?))?))).collect::<Result<Vec<_>,String>>()?.join(", ")).unwrap();
    for field in state {
        if field["type"]["kind"] == "named" {
            if let Some(resource) = field["type"]
                .get("name")
                .and_then(Value::as_str)
                .and_then(|n| declaration_named(plan, n))
                .filter(|d| d["kind"] == "resource")
            {
                writeln!(out,"crate::cott_runtime::__cott_check({},\"resource\",\"initial-state\",*__cott_value.{}()=={});",rust_string(&init_symbol),getter(field)?,render_canonical_symbol(text(resource,"initial")?,None)?).unwrap();
            }
        }
    }
    // Initializer clauses retain their parameter inputs, while self denotes the constructed handle.
    let mut init_post = init_scope.clone();
    rewrite_self(&mut init_post, "__cott_value");
    out.push_str(&contract_checks(
        plan,
        &init_post,
        &init_symbol,
        "ensures",
        &config.rust.runtime_validation,
    )?);
    out.push_str("__cott_value}\n");
    for field in state {
        let n = escape_identifier(local_name(text(field, "name")?))?;
        let ty = render_type_scoped(plan, &field["type"], &d)?;
        let getter = getter(field)?;
        writeln!(out,"pub fn {getter}(&self)->crate::cott_runtime::ReadField<'_,{ty}>{{crate::cott_runtime::ReadField::new(self.inner.{n}.try_read().unwrap_or_else(|_|crate::cott_runtime::violation({},\"guard\",\"overlapping field lease\")))}}",rust_string(canonical)).unwrap();
        let setter = escape_identifier(&format!("set_{}", local_name(text(field, "name")?)))?;
        let updater = escape_identifier(&format!("update_{}", local_name(text(field, "name")?)))?;
        writeln!(out,"#[allow(dead_code)] pub(crate) fn {setter}(&mut self,value:{ty}){{crate::cott_runtime::__cott_state_write(self.__cott_id(),{});crate::cott_runtime::Value::validate(&value);*self.inner.{n}.try_write().unwrap_or_else(|_|crate::cott_runtime::violation({},\"guard\",\"overlapping field lease\"))=Some(value);}}",rust_string(local_name(text(field,"name")?)),rust_string(canonical)).unwrap();
        writeln!(out,"#[allow(dead_code)] pub(crate) fn {updater}<R>(&mut self,operation:impl FnOnce(&mut {ty})->R)->R{{crate::cott_runtime::__cott_state_write(self.__cott_id(),{});let mut field=self.inner.{n}.try_write().unwrap_or_else(|_|crate::cott_runtime::violation({},\"guard\",\"overlapping field lease\"));let value=field.as_mut().expect(\"canonical field\");let result=operation(value);crate::cott_runtime::Value::validate(value);result}}",rust_string(local_name(text(field,"name")?)),rust_string(canonical)).unwrap();
    }
    writeln!(out,"fn __cott_validate(&self){{self.__cott_validate_for({});}}\nfn __cott_validate_for(&self,__cott_symbol:&str){{let _ = __cott_symbol;crate::cott_runtime::__cott_validate_state(self.__cott_id(),||{{",rust_string(canonical)).unwrap();
    for field in state {
        writeln!(
            out,
            "crate::cott_runtime::Value::validate(&*self.{}());",
            getter(field)?
        )
        .unwrap();
    }
    for c in list(&d, "invariants") {
        let predicate = expression(plan, &c["expression"], &d)?;
        let statement = format!(
            "crate::cott_runtime::__cott_check(__cott_symbol,\"invariant\",{},{predicate});",
            rust_string(&format!("invariant:{}", c["clause_id"]))
        );
        let guard = c
            .get("guard")
            .map(|g| lower_expression(plan, g, &d))
            .transpose()?;
        out.push_str(&render_guarded_statement(guard.as_ref(), &statement, None)?);
    }
    out.push_str("});}\n");
    for slot in list(&d, "selected_methods") {
        let method = local_name(text(slot, "trait_method")?);
        let symbol = format!("{canonical}.{method}");
        let callable = plan
            .callables()
            .iter()
            .find(|c| c.symbol == symbol)
            .ok_or_else(|| format!("missing selected callable {symbol}"))?;
        let Some(binding) = selected_binding(plan, callable, bindings)? else {
            continue;
        };
        let md = resolved(plan, callable)?;
        let mut params = public_parameters(plan, &md)?;
        params.insert(0, "&mut self".into());
        let asynchronous = md["callable_kind"] == "async";
        writeln!(
            out,
            "pub {}fn {}{}({})->{}{}{{",
            if asynchronous { "async " } else { "" },
            escape_identifier(method)?,
            generics(&md)?.0,
            params.join(", "),
            render_type_scoped(plan, &md["return_type"], &md)?,
            where_constraints(plan, &md)?
        )
        .unwrap();
        out.push_str(&defaults(plan, &md)?);
        let modifies = list(&md, "modifies")
            .iter()
            .filter_map(Value::as_str)
            .map(local_name)
            .chain(
                list(&md, "transitions")
                    .iter()
                    .filter_map(|t| t.get("field").and_then(Value::as_str))
                    .map(local_name),
            )
            .collect::<BTreeSet<_>>();
        out.push_str("let __cott_identity=self.__cott_id();\n");
        writeln!(out,"let __cott_lease=crate::cott_runtime::__cott_state_enter{}(&self.inner.gate,self.__cott_id(),&[{}]){};",if asynchronous{"_async"}else{""},modifies.iter().map(|s|rust_string(s)).collect::<Vec<_>>().join(", "),if asynchronous{".await"}else{""}).unwrap();
        writeln!(
            out,
            "crate::cott_runtime::__cott_with_state{}(__cott_lease,{}{{",
            if asynchronous { "_async" } else { "" },
            if asynchronous { "async " } else { "||" }
        )
        .unwrap();
        writeln!(out, "self.__cott_validate_for({});", rust_string(&symbol)).unwrap();
        out.push_str(&effects(config, &md, &symbol)?);
        for p in list(&md, "parameters") {
            out.push_str(&validate(
                plan,
                &p["type"],
                &escape_identifier(local_name(text(p, "name")?))?,
                &symbol,
            )?);
        }
        out.push_str(&contract_checks(
            plan,
            &md,
            &symbol,
            "requires",
            &config.rust.runtime_validation,
        )?);
        if config.rust.runtime_validation != RuntimeValidation::Off {
            out.push_str(&errors::before(
                plan,
                &md,
                &symbol,
                config.rust.runtime_validation == RuntimeValidation::Boundary,
            )?);
        }
        for field in state {
            let n = local_name(text(field, "name")?);
            if !modifies.contains(n) || old_referenced(&md, n) {
                writeln!(
                    out,
                    "let __cott_old_{}=crate::cott_runtime::Value::__cott_snapshot(&*self.{}());",
                    escape_identifier(n)?,
                    getter(field)?
                )
                .unwrap();
            }
        }
        for t in list(&md, "transitions") {
            writeln!(out,"crate::cott_runtime::__cott_check({},\"transition\",\"transition-before\",*self.{}()=={});",rust_string(&symbol),escape_identifier(&format!("get_{}",local_name(text(t,"field")?)))?,render_canonical_symbol(text(t,"from")?,None)?).unwrap();
        }
        let direct = binding.cott_symbol == symbol;
        let target = if direct {
            format!(
                "crate::cott_impl::{}::{}",
                private_name(callable),
                escape_identifier(
                    binding
                        .target_symbol
                        .rsplit(':')
                        .next()
                        .ok_or("binding lacks function")?
                )?
            )
        } else {
            render_canonical_symbol(&binding.cott_symbol, None)?
        };
        let receiver = if direct {
            "self".to_owned()
        } else {
            let selected = plan
                .callables()
                .iter()
                .find(|c| c.symbol == binding.cott_symbol)
                .ok_or("selected function is missing")?;
            let selected = resolved(plan, selected)?;
            let parameter = list(&selected, "parameters")
                .first()
                .ok_or("selected function lacks receiver")?;
            if traits::borrowed_parameter_type(plan, &parameter["type"])?.is_some() {
                "self".to_owned()
            } else {
                "self.clone()".to_owned()
            }
        };
        let mut args = vec![receiver];
        for p in list(&md, "parameters") {
            let n = escape_identifier(local_name(text(p, "name")?))?;
            args.push(if direct && borrowed_parameter(plan, &md, p)? {
                format!("&{n}")
            } else {
                n
            });
        }
        writeln!(
            out,
            "let __cott_result={target}({}){};",
            args.join(", "),
            if asynchronous { ".await" } else { "" }
        )
        .unwrap();
        writeln!(out,"crate::cott_runtime::__cott_check({},\"guard\",\"receiver-identity\",self.__cott_id()==__cott_identity);",rust_string(&symbol)).unwrap();
        out.push_str(&validate(
            plan,
            &md["return_type"],
            "__cott_result",
            &symbol,
        )?);
        for field in state {
            let n = local_name(text(field, "name")?);
            if !modifies.contains(n) {
                writeln!(out,"crate::cott_runtime::__cott_check({},\"modifies\",{},*self.{}()==__cott_old_{});",rust_string(&symbol),rust_string(text(field,"name")?),getter(field)?,escape_identifier(n)?).unwrap();
            }
        }
        for t in list(&md, "transitions") {
            writeln!(out,"crate::cott_runtime::__cott_check({},\"transition\",\"transition-after\",*self.{}()=={});",rust_string(&symbol),escape_identifier(&format!("get_{}",local_name(text(t,"field")?)))?,render_canonical_symbol(text(t,"to")?,None)?).unwrap();
        }
        writeln!(out, "self.__cott_validate_for({});", rust_string(&symbol)).unwrap();
        if config.rust.runtime_validation != RuntimeValidation::Off {
            out.push_str(&errors::after(
                plan,
                &md,
                &symbol,
                config.rust.runtime_validation == RuntimeValidation::Boundary,
            )?);
        }
        out.push_str(&contract_checks(
            plan,
            &md,
            &symbol,
            "ensures",
            &config.rust.runtime_validation,
        )?);
        writeln!(
            out,
            "__cott_result}}){} }}",
            if asynchronous { ".await" } else { "" }
        )
        .unwrap();
    }
    out.push_str("}\n");
    out.push_str(&traits::render_impl_types(plan, &d)?);
    writeln!(out,"impl crate::cott_runtime::Value for {name}{{const DEEP_SNAPSHOT:bool=true;fn validate(&self){{self.__cott_validate();}}fn __cott_snapshot(&self)->Self{{crate::cott_runtime::__cott_snapshot_state(self.__cott_id(),||Self{{inner:std::sync::Arc::new({data}{{{gate_snapshot}{}}})}},|copy|{{ let _ = &copy; {} }})}}}}",state.iter().map(|f|Ok(format!("{}:tokio::sync::RwLock::new(None)",escape_identifier(local_name(text(f,"name")?))?))).collect::<Result<Vec<_>,String>>()?.join(", "),state.iter().map(|f|{let n=escape_identifier(local_name(text(f,"name")?))?;Ok(format!("*copy.inner.{n}.try_write().expect(\"new snapshot\")=Some(crate::cott_runtime::Value::__cott_snapshot(&*self.{}()));",getter(f)?))}).collect::<Result<Vec<_>,String>>()?.join("\n")).unwrap();
    let args = list(&init_scope, "parameters")
        .iter()
        .map(|p| {
            parameter_type(plan, p, &init_scope).map(|t| {
                if p.get("default").is_some_and(|v| !v.is_null()) {
                    format!("Option<{t}>")
                } else {
                    t
                }
            })
        })
        .collect::<Result<Vec<_>, _>>()?;
    let argnames = list(&init_scope, "parameters")
        .iter()
        .map(|p| escape_identifier(local_name(text(p, "name")?)))
        .collect::<Result<Vec<_>, _>>()?;
    writeln!(out,"impl crate::cott_runtime::ConstructionArguments for {name}{{type Arguments=({}{});}}\nimpl crate::cott_runtime::Constructible for {name}{{fn construct(arguments:Self::Arguments)->Self{{let({}{})=arguments;Self::new({})}}}}",args.join(", "),if args.len()==1{","}else{""},argnames.join(", "),if argnames.len()==1{","}else{""},argnames.join(", ")).unwrap();
    if list(&d, "selected_methods").iter().all(|slot| {
        let n = slot
            .get("trait_method")
            .and_then(Value::as_str)
            .map(local_name);
        plan.callables()
            .iter()
            .find(|c| {
                c.owner.as_ref().is_some_and(|o| o["name"] == d["name"])
                    && Some(c.name.as_str()) == n
            })
            .is_some_and(|c| selected_binding(plan, c, bindings).ok().flatten().is_some())
    }) {
        for reference in trait_closure(plan, &d)? {
            let trait_name = text(&reference, "name")?;
            let td = declaration_named(plan, trait_name).ok_or("unknown native trait")?;
            writeln!(
                out,
                "impl {} for {name}{{",
                traits::native_trait_reference(plan, &reference)?
            )
            .unwrap();
            for method in list(td, "methods").iter().filter(|m| {
                m.get("name").and_then(Value::as_str).and_then(module_of) == Some(trait_name)
            }) {
                let n = local_name(text(method, "name")?);
                let symbol = format!("{canonical}.{n}");
                let callable = plan
                    .callables()
                    .iter()
                    .find(|c| c.symbol == symbol)
                    .ok_or("missing native method")?;
                let md = resolved(plan, callable)?;
                let mut params = public_parameters(plan, &md)?;
                params.insert(0, "&mut self".into());
                let arguments = list(&md, "parameters")
                    .iter()
                    .map(|p| escape_identifier(local_name(text(p, "name")?)))
                    .collect::<Result<Vec<_>, _>>()?;
                writeln!(
                    out,
                    "{}fn {}({})->{}{{{name}::{}(self,{}){}}}",
                    if md["callable_kind"] == "async" {
                        "async "
                    } else {
                        ""
                    },
                    escape_identifier(n)?,
                    params.join(", "),
                    render_type_scoped(plan, &md["return_type"], &md)?,
                    escape_identifier(n)?,
                    arguments.join(", "),
                    if md["callable_kind"] == "async" {
                        ".await"
                    } else {
                        ""
                    }
                )
                .unwrap();
            }
            out.push_str("}\n");
        }
    }
    Ok(out)
}
fn getter(field: &Value) -> Result<String, String> {
    escape_identifier(&format!("get_{}", local_name(text(field, "name")?)))
}
fn rewrite_self(value: &mut Value, name: &str) {
    match value {
        Value::Array(a) => {
            for v in a {
                rewrite_self(v, name)
            }
        }
        Value::Object(o) => {
            if o.get("kind").and_then(Value::as_str) == Some("self_ref") {
                let ty = o.get("type").cloned().unwrap_or(Value::Null);
                *value = serde_json::json!({"kind":"rust_synthetic","code":name,"type":ty});
            } else {
                for (k, v) in o {
                    if !matches!(k.as_str(), "type" | "span") {
                        rewrite_self(v, name)
                    }
                }
            }
        }
        _ => {}
    }
}
