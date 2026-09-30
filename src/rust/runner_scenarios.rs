use super::*;
#[allow(clippy::too_many_arguments)]
pub(super) fn render_scenario(
    _config: &RustProjectConfig,
    plan: &RustPlan,
    strategy: &ContractTestStrategy,
    aliases: &BTreeMap<String, String>,
    source: &mut String,
    main: &mut Vec<String>,
    expected_cancellations: &mut BTreeSet<(String, u32)>,
) -> Result<(bool, ScenarioExpectation), RenderFailure> {
    let scenario = strategy
        .scenario
        .as_ref()
        .ok_or("Rust scenario strategy missing")?;
    if scenario.steps.len() > scenario.lifecycle_limit as usize {
        return Err(RenderFailure::unavailable(
            "scenario exceeds finite lifecycle limit",
        ));
    }
    for fixture in &scenario.fixtures {
        match fixture["kind"].as_str() {
            Some("fs" | "http") => {}
            Some("clock" | "random" | "failure" | "database" | "socket") => {
                return Err(RenderFailure::unavailable(format!(
                    "{} fixture has no native interception authority",
                    fixture["kind"].as_str().unwrap_or("unknown")
                )));
            }
            _ => return Err("unsupported canonical fixture kind".into()),
        }
    }
    let declarations = declaration_index(plan)?;
    for step in &scenario.steps {
        if !matches!(
            step["kind"].as_str(),
            Some("call" | "spawn" | "init" | "method_call")
        ) {
            continue;
        }
        let target = text(step, "target")?;
        let owner = if step["kind"] == "init" {
            declarations
                .get(target)
                .copied()
                .ok_or("scenario initializer has no owner")?
        } else {
            let callable = plan
                .callables()
                .iter()
                .find(|c| c.symbol == target)
                .ok_or("scenario target has no canonical callable")?;
            if !callable_is_public(callable)? {
                return Err(RenderFailure::unavailable(
                    "scenario invokes a non-public helper",
                ));
            }
            if (step["kind"] == "method_call") != callable.owner.is_some() {
                return Err("scenario invocation has mismatched receiver".into());
            }
            callable.owner.as_ref().unwrap_or(&callable.declaration)
        };
        if owner["public"] != true {
            return Err(RenderFailure::unavailable(
                "scenario initializer is not public",
            ));
        }
        if !array(owner, "generics")?.is_empty() {
            return Err(RenderFailure::unavailable(
                "generic scenario has no explicit concrete witness",
            ));
        }
    }
    let function = format!("scenario_{}", safe_name(&scenario.id));
    let mut s = String::new();
    writeln!(s,"async fn {function}(evidence:&mut evidence::EvidenceWriter)->std::io::Result<()> {{\nlet _root=std::env::current_dir()?.join({});\nlet mut _step:Option<u32>=None;let mut _assertions=0u32;let mut _cancellations=0u32;",rust_string(&format!("cott_{}",safe_name(&scenario.id)))).unwrap();
    let mut workers = BTreeMap::new();
    for step in &scenario.steps {
        if step["kind"] == "spawn" {
            let worker = text(step, "worker")?.to_owned();
            let local = worker_name(&worker);
            let ty = emit::render_consumer_type(plan, &step["return_type"], aliases)?;
            if workers.insert(worker.clone(), local.clone()).is_some() {
                return Err("scenario duplicates a worker".into());
            }
            writeln!(
                s,
                "let mut {local}:Option<scenario::Worker<{ty}>>=None;let mut _awaited{local}=false;"
            )
            .unwrap();
        }
    }
    let http = scenario
        .fixtures
        .iter()
        .filter(|f| f["kind"] == "http")
        .collect::<Vec<_>>();
    for index in 0..http.len() {
        writeln!(
            s,
            "let mut _http_{index}:Option<scenario::HttpFixture>=None;"
        )
        .unwrap();
    }
    let mut body = String::from(
        "std::fs::create_dir(&_root).unwrap_or_else(|_|std::panic::panic_any(scenario::LifecycleFailure));\n",
    );
    let mut bytes = 0u64;
    let mut http_index = 0;
    let mut needs_loopback = false;
    for fixture in &scenario.fixtures {
        let id = text(fixture, "id")?;
        let local = escape_identifier(local_name(id))?;
        let mut allowed = BTreeSet::new();
        collect_fixture_paths(&scenario.steps, id, &mut allowed)?;
        if fixture["kind"] == "fs" {
            let files = array(fixture, "files")?;
            if files.len() > scenario.limits.filesystem_files as usize {
                return Err(RenderFailure::unavailable(
                    "filesystem fixture exceeds file limit",
                ));
            }
            let root = format!(
                "_root.join({})",
                rust_string(&format!("fixture_{}", safe_name(id)))
            );
            writeln!(body,"std::fs::create_dir_all({root}).unwrap_or_else(|_|std::panic::panic_any(scenario::LifecycleFailure));").unwrap();
            for file in files {
                let path = text(file, "path")?;
                validate_fixture_path(path, false)?;
                allowed.insert(path.to_owned());
                bytes = bytes
                    .checked_add(fixture_data_len(&file["data"])?)
                    .ok_or("fixture byte count overflow")?;
                if bytes > scenario.limits.filesystem_bytes || bytes > 1_048_576 {
                    return Err(RenderFailure::unavailable(
                        "filesystem fixture exceeds bounded byte material",
                    ));
                }
                let data = fixture_bytes(&file["data"])?;
                writeln!(body,"{{let _file={root}.join({});std::fs::create_dir_all(_file.parent().expect(\"fixture file parent\")).unwrap_or_else(|_|std::panic::panic_any(scenario::LifecycleFailure));std::fs::write(_file,{data}).unwrap_or_else(|_|std::panic::panic_any(scenario::LifecycleFailure));}}",rust_string(path)).unwrap();
            }
            writeln!(
                body,
                "let {local}=cott_runtime::__cott_fixture({root},String::new(),{});let _=&{local};",
                string_set(&allowed)
            )
            .unwrap();
        } else {
            needs_loopback = true;
            let mut routes = Vec::new();
            for route in array(fixture, "routes")? {
                let path = text(route, "path")?;
                validate_fixture_path(path, true)?;
                allowed.insert(path.into());
                routes.push(format!(
                    "({}.to_owned(),{})",
                    rust_string(path),
                    http_route(&route["outcome"], &scenario.limits)?
                ));
            }
            writeln!(body,"_http_{http_index}=Some(scenario::HttpFixture::start(std::collections::BTreeMap::from([{}]),{},{},{},{},{}).unwrap_or_else(|_|std::panic::panic_any(scenario::LifecycleFailure)));",routes.join(","),scenario.limits.http_requests,scenario.limits.http_body_bytes,scenario.limits.http_redirects,scenario.limits.transcript_events,scenario.limits.scenario_timeout_ms).unwrap();
            writeln!(body,"let {local}=cott_runtime::__cott_fixture(_root.clone(),_http_{http_index}.as_ref().expect(\"HTTP fixture\").base_url(),{});let _=&{local};",string_set(&allowed)).unwrap();
            http_index += 1;
        }
    }
    let mut assertions = 0u32;
    let mut cancellations = 0u32;
    let mut cancellation_inventory = BTreeSet::new();
    for step in &scenario.steps {
        let step_id = step["step_id"]
            .as_u64()
            .and_then(|n| u32::try_from(n).ok())
            .ok_or("scenario step has invalid step_id")?;
        writeln!(body, "_step=Some({step_id});").unwrap();
        match step["kind"].as_str() {
            Some("call" | "spawn" | "method_call") => {
                let target = text(step, "target")?;
                let callable = plan
                    .callables()
                    .iter()
                    .find(|c| c.symbol == target)
                    .ok_or("scenario callable missing")?;
                let params = array(&callable.declaration, "parameters")?;
                let args = scenario_arguments(step, params, plan, aliases)?;
                let asynchronous = callable.declaration["callable_kind"] == "async";
                if step["kind"] == "spawn" {
                    let worker = text(step, "worker")?;
                    let local = workers.get(worker).ok_or("scenario worker not declared")?;
                    let mut names = Vec::new();
                    for (index, arg) in args.into_iter().enumerate() {
                        let name = format!("_spawn_{step_id}_{index}");
                        writeln!(body, "let {name}={arg};").unwrap();
                        names.push(name);
                    }
                    let function = emit::render_consumer_symbol(target, aliases)?;
                    writeln!(body,"{local}=Some(scenario::Worker::start(async move {{ {function}({}){} }}).await);",names.join(","),if asynchronous{".await"}else{""}).unwrap();
                } else {
                    let binding = escape_identifier(local_name(text(step, "binding")?))?;
                    let call = if step["kind"] == "method_call" {
                        let receiver =
                            scenario_expression(&step["receiver"], plan, aliases, false)?;
                        format!(
                            "({receiver}).{}({})",
                            escape_identifier(local_name(&callable.name))?,
                            args.join(",")
                        )
                    } else {
                        format!(
                            "{}({})",
                            emit::render_consumer_symbol(target, aliases)?,
                            args.join(",")
                        )
                    };
                    writeln!(
                        body,
                        "let {binding}={call}{};let _=&{binding};",
                        if asynchronous { ".await" } else { "" }
                    )
                    .unwrap();
                }
            }
            Some("init") => {
                let binding = escape_identifier(local_name(text(step, "binding")?))?;
                let target = text(step, "target")?;
                let owner = declarations
                    .get(target)
                    .copied()
                    .ok_or("scenario initializer owner missing")?;
                let args = scenario_arguments(step, initializer_parameters(owner)?, plan, aliases)?;
                writeln!(
                    body,
                    "#[allow(unused_mut)] let mut {binding}={}::new({});let _=&{binding};",
                    emit::render_consumer_symbol(target, aliases)?,
                    args.join(",")
                )
                .unwrap();
            }
            Some("data") => {
                let binding = escape_identifier(local_name(text(step, "binding")?))?;
                let expression = &step["expression"];
                let value = scenario_expression(expression, plan, aliases, true)?;
                let ty = emit::render_consumer_type(plan, &expression["type"], aliases)?;
                writeln!(body, "let {binding}:{ty}={value};let _=&{binding};").unwrap();
            }
            Some("tick") => body.push_str("tokio::task::yield_now().await;\n"),
            Some("cancel") => {
                let worker = workers
                    .get(text(step, "worker")?)
                    .ok_or("cancel names unknown worker")?;
                writeln!(
                    body,
                    "{worker}.as_ref().expect(\"started worker\").cancel();"
                )
                .unwrap();
            }
            Some("await") => {
                let worker = workers
                    .get(text(step, "worker")?)
                    .ok_or("await names unknown worker")?;
                if step["cancelled"] == true {
                    writeln!(body,"{{let _worker={worker}.as_mut().expect(\"started worker\");let _outcome=_worker.result().await;let _observed=_outcome.as_ref().err().is_some_and(|e|e.is::<cott_runtime::CancellationException>())&&_worker.cancellation_observed;if !_observed {{std::panic::panic_any(scenario::AssertionFailure)}}_cancellations+=1;}}").unwrap();
                    cancellations += 1;
                    cancellation_inventory.insert((scenario.id.clone(), step_id));
                } else {
                    let result = step["result"]
                        .as_str()
                        .map(|r| escape_identifier(local_name(r)))
                        .transpose()?;
                    let target = result.as_deref().unwrap_or("_worker_value");
                    writeln!(body,"let {target}=match {worker}.as_mut().expect(\"started worker\").result().await {{Ok(value)=>value,Err(error)=>std::panic::resume_unwind(error)}};let _=&{target};").unwrap();
                }
                writeln!(body, "_awaited{worker}=true;").unwrap();
            }
            Some("assert") => {
                let expr = scenario_expression(&step["expression"], plan, aliases, false)?;
                writeln!(body,"if !({expr}){{std::panic::panic_any(scenario::AssertionFailure)}}_assertions+=1;").unwrap();
                assertions += 1;
            }
            Some("unwrap_result" | "list_item") => {
                let binding = escape_identifier(local_name(text(step, "binding")?))?;
                let expr = scenario_expression(&step["value"], plan, aliases, true)?;
                writeln!(body, "let _extract_{step_id}={expr};").unwrap();
                if step["kind"] == "unwrap_result" {
                    writeln!(body,"let {binding}=match _extract_{step_id}{{Ok(value)=>value,Err(_)=>std::panic::panic_any(scenario::AssertionFailure)}};let _=&{binding};").unwrap();
                } else {
                    let index = step["index"]
                        .as_u64()
                        .ok_or("scenario list index is not u64")?;
                    writeln!(body,"let {binding}=_extract_{step_id}.into_iter().nth({index}usize).unwrap_or_else(||std::panic::panic_any(scenario::AssertionFailure));let _=&{binding};").unwrap();
                }
            }
            Some(other) => return Err(format!("unsupported scenario step `{other}`").into()),
            None => return Err("scenario step kind missing".into()),
        }
    }
    writeln!(body,"_step=None;scenario::audit_root(&_root,{},{}).unwrap_or_else(|_|std::panic::panic_any(scenario::LifecycleFailure));",scenario.limits.filesystem_files,scenario.limits.filesystem_bytes).unwrap();
    writeln!(s,"let(mut _result,mut _observations)=match tokio::time::timeout(std::time::Duration::from_millis({}),cott_runtime::__cott_observe_async(async {{ {body} }})).await {{Ok(result)=>result,Err(_)=>(Err(Box::new(scenario::TimeoutFailure) as Box<dyn std::any::Any+Send>),Vec::new())}};",scenario.limits.scenario_timeout_ms).unwrap();
    for worker in workers.values() {
        writeln!(s,"if let Some(_worker)={worker}.as_mut(){{if !_awaited{worker}&&_result.is_ok(){{_result=Err(Box::new(scenario::LifecycleFailure));}}let _closed=_worker.close({}).await;_observations.extend(_worker.take_observations());if let Err(error)=_closed{{if _result.is_ok(){{_result=Err(error);}}}}}}",scenario.limits.scenario_timeout_ms).unwrap();
    }
    for index in 0..http.len() {
        writeln!(s,"if let Some(_http)=_http_{index}.as_mut(){{if _http.close().is_err()&&_result.is_ok(){{_result=Err(Box::new(scenario::LifecycleFailure));}}}}").unwrap();
    }
    s.push_str("let _cleaned=if _root.exists(){std::fs::remove_dir_all(&_root).is_ok()&&!_root.exists()}else{true};if !_cleaned&&_result.is_ok(){_result=Err(Box::new(scenario::LifecycleFailure));}\n");
    for (id, step_id) in &cancellation_inventory {
        writeln!(
            s,
            "if _result.is_ok()&&_cleaned{{emit_cancellation(evidence,{},{step_id},true,{})?;}}",
            rust_string(id),
            rust_string(&format!(
                "scenario {id} step {step_id}: cooperative cancellation after structured join"
            ))
        )
        .unwrap();
    }
    writeln!(s,"scenario::emit_scenario(evidence,{},{},_result,_observations,_assertions,_cancellations,_cleaned,_step)\n}}",rust_string(&scenario.id),rust_string(&strategy.symbol)).unwrap();
    source.push_str(&s);
    main.push(format!("{function}(&mut evidence).await?;"));
    expected_cancellations.extend(cancellation_inventory);
    Ok((
        needs_loopback,
        ScenarioExpectation {
            symbol: strategy.symbol.clone(),
            assertions,
            cancellations,
        },
    ))
}
fn worker_name(name: &str) -> String {
    format!("_worker_{}", safe_name(name))
}
fn scenario_arguments(
    step: &Value,
    params: &[Value],
    plan: &RustPlan,
    aliases: &BTreeMap<String, String>,
) -> Result<Vec<String>, String> {
    let values = array(step, "arguments")?;
    if values.len() != params.len() {
        return Err("canonical scenario argument arity mismatch".into());
    }
    values
        .iter()
        .zip(params)
        .map(|(e, p)| {
            let expr = scenario_expression(e, plan, aliases, true)?;
            Ok(if p.get("default").is_some_and(|d| !d.is_null()) {
                format!("Some({expr})")
            } else {
                expr
            })
        })
        .collect()
}
fn scenario_expression(
    expression: &Value,
    plan: &RustPlan,
    aliases: &BTreeMap<String, String>,
    consuming: bool,
) -> Result<String, String> {
    fn copy_value(ty: &Value) -> bool {
        match ty["kind"].as_str() {
            Some("primitive") => matches!(
                ty["name"].as_str(),
                Some(
                    "unit"
                        | "bool"
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
                )
            ),
            Some("option" | "array") => copy_value(&ty["item"]),
            Some("tuple") => ty["items"]
                .as_array()
                .is_some_and(|a| a.iter().all(copy_value)),
            _ => false,
        }
    }
    fn rewrite(
        value: &Value,
        plan: &RustPlan,
        aliases: &BTreeMap<String, String>,
        consuming: bool,
    ) -> Result<Value, String> {
        let code = match value["kind"].as_str() {
            Some("binding_ref") => {
                let id = escape_identifier(local_name(text(value, "symbol")?))?;
                Some(if consuming && !copy_value(&value["type"]) {
                    format!("{id}.clone()")
                } else {
                    id
                })
            }
            Some("field") if consuming && !copy_value(&value["type"]) => {
                let base = emit::render_consumer_expression(
                    &rewrite(&value["base"], plan, aliases, false)?,
                    aliases,
                )?;
                Some(format!(
                    "({base}).{}().clone()",
                    escape_identifier(&format!("get_{}", text(value, "name")?))?
                ))
            }
            Some("constant_ref") if consuming && !copy_value(&value["type"]) => Some(format!(
                "(*{}).clone()",
                emit::render_consumer_symbol(text(value, "symbol")?, aliases)?
            )),
            _ => None,
        };
        if let Some(code) = code {
            return Ok(json!({"kind":"rust_synthetic","type":value["type"],"code":code}));
        }
        Ok(match value {
            Value::Array(a) => Value::Array(
                a.iter()
                    .map(|v| rewrite(v, plan, aliases, consuming))
                    .collect::<Result<_, _>>()?,
            ),
            Value::Object(m) => Value::Object(
                m.iter()
                    .map(|(k, v)| {
                        Ok((
                            k.clone(),
                            if matches!(k.as_str(), "type" | "span") {
                                v.clone()
                            } else {
                                rewrite(v, plan, aliases, consuming)?
                            },
                        ))
                    })
                    .collect::<Result<_, String>>()?,
            ),
            _ => value.clone(),
        })
    }
    emit::render_consumer_expression(&rewrite(expression, plan, aliases, consuming)?, aliases)
}
fn collect_fixture_paths(
    steps: &[Value],
    fixture: &str,
    out: &mut BTreeSet<String>,
) -> Result<(), String> {
    fn walk(v: &Value, fixture: &str, out: &mut BTreeSet<String>) -> Result<(), String> {
        if matches!(v["kind"].as_str(), Some("fixture_path" | "fixture_url"))
            && v["fixture"] == fixture
        {
            let path = text(v, "path")?;
            validate_fixture_path(path, v["kind"] == "fixture_url")?;
            out.insert(path.into());
        }
        match v {
            Value::Array(a) => {
                for c in a {
                    walk(c, fixture, out)?
                }
            }
            Value::Object(m) => {
                for c in m.values() {
                    walk(c, fixture, out)?
                }
            }
            _ => {}
        }
        Ok(())
    }
    for step in steps {
        walk(step, fixture, out)?;
    }
    Ok(())
}
fn string_set(values: &BTreeSet<String>) -> String {
    if values.is_empty() {
        "std::collections::BTreeSet::new()".into()
    } else {
        format!(
            "std::collections::BTreeSet::from([{}])",
            values
                .iter()
                .map(|s| format!("{}.to_owned()", rust_string(s)))
                .collect::<Vec<_>>()
                .join(",")
        )
    }
}
fn validate_fixture_path(path: &str, absolute: bool) -> Result<(), String> {
    let body = if absolute {
        path.strip_prefix('/').unwrap_or(path)
    } else {
        path
    };
    if path.is_empty()
        || path.contains(['\\', '\0'])
        || absolute != path.starts_with('/')
        || (!body.is_empty()
            && body
                .split('/')
                .any(|p| p.is_empty() || p == "." || p == ".."))
    {
        return Err(format!("unsafe Rust fixture path `{path}`"));
    }
    Ok(())
}
fn fixture_data_len(data: &Value) -> Result<u64, String> {
    let value = text(data, "value")?;
    match text(data, "kind")? {
        "text" => Ok(value.len() as u64),
        "hex" => {
            if !value.len().is_multiple_of(2) || !value.bytes().all(|b| b.is_ascii_hexdigit()) {
                return Err("invalid hex fixture bytes".into());
            }
            Ok((value.len() / 2) as u64)
        }
        _ => Err("unsupported fixture byte encoding".into()),
    }
}
fn fixture_bytes(data: &Value) -> Result<String, String> {
    let value = text(data, "value")?;
    match text(data, "kind")? {
        "text" => Ok(format!("{}.as_bytes()", rust_string(value))),
        "hex" => {
            fixture_data_len(data)?;
            let bytes = value
                .as_bytes()
                .chunks_exact(2)
                .map(|c| {
                    u8::from_str_radix(std::str::from_utf8(c).expect("ASCII hex"), 16)
                        .map(|b| format!("{b}u8"))
                        .map_err(|e| e.to_string())
                })
                .collect::<Result<Vec<_>, _>>()?;
            Ok(format!("&[{}]", bytes.join(",")))
        }
        _ => Err("unsupported fixture byte encoding".into()),
    }
}
fn http_route(
    outcome: &Value,
    limits: &crate::contract_test::ScenarioLimits,
) -> Result<String, RenderFailure> {
    match outcome["kind"].as_str() {
        Some("response") => {
            let status = outcome["status"]
                .as_u64()
                .and_then(|s| u16::try_from(s).ok())
                .ok_or("HTTP fixture invalid status")?;
            let body = &outcome["body"];
            if body["kind"] == "text" && outcome["encoding"] != "utf-8" {
                return Err("HTTP fixture text needs utf-8 encoding".into());
            }
            if fixture_data_len(body)? > limits.http_body_bytes {
                return Err(RenderFailure::unavailable(
                    "HTTP fixture body exceeds byte limit",
                ));
            }
            let content = outcome["content_type"]
                .as_str()
                .map(|s| format!("Some({}.to_owned())", rust_string(s)))
                .unwrap_or_else(|| "None".into());
            Ok(format!(
                "scenario::Route::Response{{status:{status},body:({}).to_vec(),content_type:{content}}}",
                fixture_bytes(body)?
            ))
        }
        Some("redirect") => {
            let status = outcome["status"]
                .as_u64()
                .and_then(|s| u16::try_from(s).ok())
                .ok_or("invalid HTTP redirect status")?;
            let location = text(outcome, "location")?;
            validate_fixture_path(location, true)?;
            Ok(format!(
                "scenario::Route::Redirect{{status:{status},location:{}.to_owned()}}",
                rust_string(location)
            ))
        }
        Some("delay") => {
            let milliseconds = outcome["milliseconds"]
                .as_u64()
                .ok_or("invalid HTTP fixture delay")?;
            if milliseconds > limits.scenario_timeout_ms as u64 {
                return Err(RenderFailure::unavailable(
                    "HTTP delay exceeds scenario timeout",
                ));
            }
            Ok(format!(
                "scenario::Route::Delay{{milliseconds:{milliseconds}}}"
            ))
        }
        _ => Err("unsupported HTTP fixture outcome".into()),
    }
}
