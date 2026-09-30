//! Deterministic public-facade candidates and finite scenarios with authenticated evidence.
use super::types::{escape_identifier, local_name, rust_string};
use super::{RustCallable, RustPlan, emit};
use crate::contract_test::{Classification, ContractTestStrategy};
use crate::manifest::{RustProjectConfig, VerificationConfig};
use serde_json::{Value, json};
use std::collections::{BTreeMap, BTreeSet};
use std::fmt::Write as _;
use std::path::PathBuf;
#[path = "runner_scenarios.rs"]
mod scenarios;
#[path = "runner_wire.rs"]
mod wire;
use scenarios::render_scenario;
pub(crate) use wire::parse_events;
pub(crate) const EVIDENCE_KEY_BYTES: usize = 32;
const MAX_RUNNER_CASES: u64 = 4096;
const MAX_RUNNER_SOURCE_BYTES: usize = 8 * 1024 * 1024;
#[derive(Clone, Debug)]
pub(crate) struct RunnerProgram {
    pub source: String,
    pub file_name: &'static str,
    pub expected_cases: BTreeMap<String, u32>,
    pub expected_cancellations: BTreeSet<(String, u32)>,
    pub expected_scenarios: BTreeMap<String, ScenarioExpectation>,
    pub unavailable: BTreeMap<String, String>,
    pub support: BTreeMap<PathBuf, &'static [u8]>,
    pub needs_loopback: bool,
}
#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct ScenarioExpectation {
    pub symbol: String,
    pub assertions: u32,
    pub cancellations: u32,
}
#[derive(Clone)]
struct CandidateContext<'a> {
    plan: &'a RustPlan,
    declarations: BTreeMap<&'a str, &'a Value>,
    aliases: &'a BTreeMap<String, String>,
    type_arguments: BTreeMap<String, Value>,
    consts: BTreeMap<String, String>,
    literals: Vec<(String, String)>,
    node_limit: usize,
    container_limit: usize,
}
struct Invocation {
    prelude: Vec<String>,
    call: String,
    return_type: Value,
    protocol_send: Option<String>,
    asynchronous: bool,
    construction: bool,
}
#[derive(Debug)]
enum RenderFailure {
    Unavailable(String),
    Fatal(String),
}
impl RenderFailure {
    fn unavailable(s: impl Into<String>) -> Self {
        Self::Unavailable(s.into())
    }
}
impl From<String> for RenderFailure {
    fn from(s: String) -> Self {
        Self::Fatal(s)
    }
}
impl From<&str> for RenderFailure {
    fn from(s: &str) -> Self {
        Self::Fatal(s.into())
    }
}

pub(crate) fn render(
    config: &RustProjectConfig,
    plan: &RustPlan,
    strategies: &[ContractTestStrategy],
    verification: &VerificationConfig,
) -> Result<RunnerProgram, String> {
    let declarations = declaration_index(plan)?;
    let aliases = module_aliases(plan)?;
    let mut source = runner_prelude(config, plan, &aliases)?;
    let mut main_lines = Vec::new();
    let mut expected_cases = BTreeMap::new();
    let mut expected_cancellations = BTreeSet::new();
    let mut expected_scenarios = BTreeMap::new();
    let mut unavailable = BTreeMap::new();
    let mut needs_loopback = false;
    let mut strategies_by_symbol = BTreeMap::new();
    for strategy in strategies {
        if strategies_by_symbol
            .insert(strategy.symbol.as_str(), strategy)
            .is_some()
        {
            return Err(format!("duplicate Rust strategy for `{}`", strategy.symbol));
        }
    }
    for callable in plan.callables() {
        let Some(strategy) = strategies_by_symbol.get(callable.symbol.as_str()) else {
            continue;
        };
        if !callable_is_public(callable)? {
            unavailable.insert(
                callable.symbol.clone(),
                "selected implementation helper is not a public consumer facade".into(),
            );
            continue;
        }
        if strategy.classification == Classification::Effectful {
            if strategy.scenario.is_none() {
                unavailable.insert(
                    callable.symbol.clone(),
                    "effectful callable requires an enforceable canonical scenario".into(),
                );
            }
            continue;
        }
        if strategy.classification == Classification::Never {
            unavailable.insert(
                callable.symbol.clone(),
                "Never callable cannot be safely invoked by bounded value generation".into(),
            );
            continue;
        }
        match render_callable_cases(
            config,
            plan,
            callable,
            &declarations,
            &aliases,
            verification,
            &mut source,
            &mut main_lines,
        ) {
            Ok(count) => {
                expected_cases.insert(callable.symbol.clone(), count);
            }
            Err(RenderFailure::Unavailable(reason)) => {
                unavailable.insert(callable.symbol.clone(), reason);
            }
            Err(RenderFailure::Fatal(reason)) => {
                return Err(format!(
                    "render Rust callable evidence for `{}`: {reason}",
                    callable.symbol
                ));
            }
        }
    }
    for strategy in strategies.iter().filter(|s| s.symbol.ends_with(".init")) {
        let owner_symbol = strategy.symbol.trim_end_matches(".init");
        let owner = declarations
            .get(owner_symbol)
            .copied()
            .ok_or("initializer strategy has no owner")?;
        if owner["kind"] != "impl" {
            return Err("initializer strategy has a non-implementation owner".into());
        }
        if owner["public"] != true {
            unavailable.insert(
                strategy.symbol.clone(),
                "initializer is not a public consumer facade".into(),
            );
            continue;
        }
        match render_initializer_cases(
            config,
            plan,
            owner_symbol,
            owner,
            &declarations,
            &aliases,
            verification,
            &mut source,
            &mut main_lines,
        ) {
            Ok(count) => {
                expected_cases.insert(strategy.symbol.clone(), count);
            }
            Err(RenderFailure::Unavailable(reason)) => {
                unavailable.insert(strategy.symbol.clone(), reason);
            }
            Err(RenderFailure::Fatal(reason)) => return Err(reason),
        }
    }
    for module in &plan.modules {
        for declaration in &module.declarations {
            if declaration["public"] != true
                || !matches!(declaration["kind"].as_str(), Some("struct" | "newtype"))
            {
                continue;
            }
            let symbol = text(declaration, "name")?;
            if expected_cases.contains_key(symbol) {
                continue;
            }
            match render_nominal_cases(
                config,
                plan,
                symbol,
                declaration,
                &declarations,
                &aliases,
                verification,
                &mut source,
                &mut main_lines,
            ) {
                Ok(count) => {
                    expected_cases.insert(symbol.into(), count);
                }
                Err(RenderFailure::Unavailable(reason)) => {
                    unavailable.insert(symbol.into(), reason);
                }
                Err(RenderFailure::Fatal(reason)) => return Err(reason),
            }
        }
    }
    for strategy in strategies.iter().filter(|s| s.scenario.is_some()) {
        match render_scenario(
            config,
            plan,
            strategy,
            &aliases,
            &mut source,
            &mut main_lines,
            &mut expected_cancellations,
        ) {
            Ok((loopback, expectation)) => {
                let id = &strategy.scenario.as_ref().ok_or("scenario missing")?.id;
                if expected_scenarios.insert(id.clone(), expectation).is_some() {
                    return Err(format!("duplicate Rust scenario `{id}`"));
                }
                needs_loopback |= loopback;
            }
            Err(RenderFailure::Unavailable(reason)) => {
                unavailable.entry(strategy.symbol.clone()).or_insert(reason);
            }
            Err(RenderFailure::Fatal(reason)) => {
                return Err(format!(
                    "render Rust scenario for `{}`: {reason}",
                    strategy.symbol
                ));
            }
        }
    }
    let cases = expected_cases.values().map(|n| u64::from(*n)).sum::<u64>();
    if cases > MAX_RUNNER_CASES {
        return Err("Rust runner exceeds bounded case inventory".into());
    }
    source.push_str("fn main() -> Result<(), Box<dyn std::error::Error>> {\nconfinement::install().map_err(std::io::Error::other)?;\nlet mut evidence=evidence::EvidenceWriter::from_stdin()?;\nlet previous=std::panic::take_hook(); std::panic::set_hook(Box::new(move |info| {if !info.payload().is::<cott_runtime::ContractViolation>() {previous(info)}}));\nlet runtime=tokio::runtime::Builder::new_current_thread().enable_time().build()?;\nruntime.block_on(async {\n");
    for line in main_lines {
        writeln!(source, "{line}").unwrap();
    }
    source.push_str("evidence.event(\"{\\\"kind\\\":\\\"done\\\"}\")?;\nOk::<(),std::io::Error>(())\n})?;\nOk(())\n}\n");
    if source.len() > MAX_RUNNER_SOURCE_BYTES {
        return Err("Rust runner source exceeds its bounded size".into());
    }
    Ok(RunnerProgram {
        source,
        file_name: "main.rs",
        expected_cases,
        expected_cancellations,
        expected_scenarios,
        unavailable,
        support: BTreeMap::from([
            (
                PathBuf::from("evidence.rs"),
                include_bytes!("runner_support.rs").as_slice(),
            ),
            (
                PathBuf::from("scenario.rs"),
                include_bytes!("runner_scenario_support.rs").as_slice(),
            ),
            (
                PathBuf::from("confinement.rs"),
                include_bytes!("runner_confinement_support.rs").as_slice(),
            ),
        ]),
        needs_loopback,
    })
}
fn runner_prelude(
    config: &RustProjectConfig,
    plan: &RustPlan,
    aliases: &BTreeMap<String, String>,
) -> Result<String, String> {
    let mut s = format!(
        "#![deny(unsafe_code)]\n#[allow(unsafe_code)] mod confinement;\n#[allow(dead_code)] mod evidence;\n#[allow(dead_code)] mod scenario;\nuse {}::cott_runtime;\n#[allow(unused_imports)] use {}::modules;\n",
        config.project.name, config.project.name
    );
    for module in &plan.modules {
        let alias = aliases
            .get(&module.name)
            .ok_or("module has no runner alias")?;
        let mut segments = Vec::new();
        for segment in module.name.split('.') {
            segments.push(escape_identifier(segment)?);
        }
        writeln!(
            s,
            "#[allow(unused_imports)] use {}::modules::{} as {alias};",
            config.project.name,
            segments.join("::")
        )
        .unwrap();
    }
    s.push_str(r#"
#[allow(dead_code)]
fn observations_json(observations: &[cott_runtime::PredicateObservation]) -> String {
    let mut result=String::from("[");
    for (index,observation) in observations.iter().enumerate() {
        if index!=0 {result.push(',');}
        result.push_str(&format!("{{\"symbol\":{},\"clause\":{},\"phase\":{},\"status\":{},\"passed\":{},\"reason\":null,\"applicable\":true}}",evidence::json_quote(&observation.symbol),evidence::json_quote(&observation.clause),evidence::json_quote(&observation.phase),evidence::json_quote(if observation.passed {"passed"}else{"failed"}),observation.passed));
    }
    result.push(']');result
}
#[allow(dead_code)]
fn emit_case(evidence: &mut evidence::EvidenceWriter,symbol: &str,case:u32,entered:bool,construction:bool,result:Result<(),Box<dyn std::any::Any+Send>>,observations:Vec<cott_runtime::PredicateObservation>)->std::io::Result<()> {
    let(mut status,mut phase,mut clause,mut error_symbol)=("passed","null".to_owned(),"null".to_owned(),"null".to_owned());
    if let Err(error)=result {
        if let Some(error)=error.downcast_ref::<cott_runtime::ContractViolation>() {
            status=if !entered||construction {"candidate_unavailable"}else if error.phase=="requires" {"ineligible"}else if error.phase=="cancellation" {"unexpected_cancellation"}else {"failed"};
            phase=evidence::json_quote(&error.phase);clause=evidence::json_quote(&error.clause);error_symbol=evidence::json_quote(&error.symbol);
        }else {status="unexpected_exception";}
    }
    evidence.event(&format!("{{\"kind\":\"case\",\"symbol\":{},\"case\":{},\"status\":{},\"phase\":{},\"clause\":{},\"error_symbol\":{},\"observations\":{}}}",evidence::json_quote(symbol),case,evidence::json_quote(status),phase,clause,error_symbol,observations_json(&observations)))
}
#[allow(dead_code)]
fn emit_cancellation(evidence:&mut evidence::EvidenceWriter,symbol:&str,case:u32,observed:bool,reason:&str)->std::io::Result<()> {
    evidence.event(&format!("{{\"kind\":\"cancellation\",\"symbol\":{},\"case\":{},\"status\":{},\"cooperative\":{},\"future_preempted\":false,\"reason\":{}}}",evidence::json_quote(symbol),case,evidence::json_quote(if observed {"passed"}else{"failed"}),observed,evidence::json_quote(reason)))
}
"#);
    Ok(s)
}
fn render_case(
    source: &mut String,
    invocation: &Invocation,
    symbol: &str,
    case: u32,
    verification: &VerificationConfig,
) -> Result<(), String> {
    let name = format!("case_{}_{}", safe_name(symbol), case);
    writeln!(source,"async fn {name}(evidence:&mut evidence::EvidenceWriter)->std::io::Result<()> {{\nlet mut _entered=false;").unwrap();
    let consumption = protocol_consumption(
        &invocation.return_type,
        verification.lifecycle_limit,
        invocation.protocol_send.as_deref(),
    )?;
    let mut body = invocation.prelude.join("\n");
    body.push_str("\n_entered=true;\n");
    let mutable = invocation.return_type["kind"] == "iterator";
    writeln!(
        body,
        "let {}_value={}{};",
        if mutable { "mut " } else { "" },
        invocation.call,
        if invocation.asynchronous {
            ".await"
        } else {
            ""
        }
    )
    .unwrap();
    body.push_str(&consumption);
    if invocation.asynchronous || protocol_is_async(&invocation.return_type) {
        writeln!(source,"let (_result,_observations)=cott_runtime::__cott_observe_async(async {{ {body}\n }}).await;\nlet _result=_result.map(|_|());").unwrap();
    } else {
        writeln!(source,"cott_runtime::__cott_observe_begin();\nlet _result=std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {{ {body}\n }}));\nlet _observations=cott_runtime::__cott_observe_end();\nlet _result=_result.map(|_|());").unwrap();
    }
    writeln!(
        source,
        "emit_case(evidence,{},{case},_entered,{},_result,_observations)\n}}",
        rust_string(symbol),
        invocation.construction
    )
    .unwrap();
    Ok(())
}
fn protocol_is_async(ty: &Value) -> bool {
    matches!(
        ty["kind"].as_str(),
        Some("async_iterator" | "async_generator" | "future")
    )
}
fn protocol_consumption(ty: &Value, limit: u32, send: Option<&str>) -> Result<String, String> {
    let s = match ty["kind"].as_str() {
        Some("iterator") => format!(
            "for _ in 0..{limit} {{ match _value.next() {{Some(_item)=>cott_runtime::Value::validate(&_item),None=>break}} }} _value.close();"
        ),
        Some("async_iterator") => format!(
            "for _ in 0..{limit} {{ match _value.next().await {{Some(_item)=>cott_runtime::Value::validate(&_item),None=>break}} }} _value.close().await;"
        ),
        Some("generator") => {
            let candidate = send.ok_or("generator send has no concrete bounded candidate")?;
            format!(
                "for _operation in 0..{limit} {{match if _operation==0 {{_value.start()}}else{{_value.send({candidate})}} {{cott_runtime::GeneratorStep::Yield(_item)=>cott_runtime::Value::validate(&_item),cott_runtime::GeneratorStep::Return(_item)=>{{cott_runtime::Value::validate(&_item);break;}}}}}} _value.close();"
            )
        }
        Some("async_generator") => {
            let candidate = send.ok_or("async generator send has no concrete bounded candidate")?;
            format!(
                "for _operation in 0..{limit} {{match if _operation==0 {{_value.start().await}}else{{_value.send({candidate}).await}} {{cott_runtime::GeneratorStep::Yield(_item)=>cott_runtime::Value::validate(&_item),cott_runtime::GeneratorStep::Return(_item)=>{{cott_runtime::Value::validate(&_item);break;}}}}}} _value.close().await;"
            )
        }
        Some("future") => "let _item=_value.await;cott_runtime::Value::validate(&_item);".into(),
        _ => String::new(),
    };
    Ok(s)
}
#[allow(clippy::too_many_arguments)]
fn render_callable_cases(
    config: &RustProjectConfig,
    plan: &RustPlan,
    callable: &RustCallable,
    declarations: &BTreeMap<&str, &Value>,
    aliases: &BTreeMap<String, String>,
    verification: &VerificationConfig,
    source: &mut String,
    main: &mut Vec<String>,
) -> Result<u32, RenderFailure> {
    let mut context = candidate_context(
        config,
        plan,
        callable.owner.as_ref().unwrap_or(&callable.declaration),
        declarations,
        aliases,
    )?;
    let mut callable_literals = Vec::new();
    let mut seen = BTreeSet::new();
    collect_literals(
        &callable.declaration,
        aliases,
        &mut callable_literals,
        &mut seen,
    );
    for literal in std::mem::take(&mut context.literals) {
        if seen.insert(literal.clone()) {
            callable_literals.push(literal);
        }
    }
    context.literals = callable_literals;
    let params = array(&callable.declaration, "parameters")?;
    let cases = parameter_candidates(params, &mut context)?;
    let receiver_cases = callable
        .owner
        .as_ref()
        .map(|owner| parameter_candidates(initializer_parameters(owner)?, &mut context))
        .transpose()?
        .unwrap_or_else(|| vec![vec![]]);
    let ty = substitute_candidate_type(&callable.declaration["return_type"], &context);
    let protocol_send = if matches!(ty["kind"].as_str(), Some("generator" | "async_generator")) {
        Some(
            candidate_values(&ty["send"], &mut context, 0)?
                .into_iter()
                .next()
                .ok_or_else(|| {
                    RenderFailure::unavailable(
                        "generator send type has no bounded public candidate",
                    )
                })?,
        )
    } else {
        None
    };
    let asynchronous = callable.declaration["callable_kind"] == "async";
    let mut count = 0;
    for indices in bounded_product_indices(
        &[receiver_cases.len(), cases.len()],
        verification.candidate_limit as usize,
    ) {
        let values = &cases[indices[1]];
        let mut prelude = typed_candidates("_arg", params, values, &context)?;
        let args = (0..params.len())
            .map(|i| format!("_arg{i}"))
            .collect::<Vec<_>>();
        let call = if let Some(owner) = &callable.owner {
            let constructor = constructor_expression(owner, &receiver_cases[indices[0]], &context)?;
            prelude.push(format!("let mut _receiver={constructor};"));
            format!(
                "_receiver.{}({})",
                escape_identifier(local_name(&callable.name))?,
                args.join(",")
            )
        } else {
            let function = emit::render_consumer_symbol(&callable.symbol, aliases)?;
            let named = concrete_named_type(&callable.declaration, &context)?;
            let arguments = array(&callable.declaration, "generics")?
                .iter()
                .zip(array(&named, "args")?)
                .map(|(g, a)| {
                    Ok((
                        text(g, "name")?.to_owned(),
                        if a["kind"] == "const" {
                            a["value"].clone()
                        } else {
                            a["type"].clone()
                        },
                    ))
                })
                .collect::<Result<BTreeMap<_, _>, String>>()?;
            let generics =
                emit::render_consumer_generic_arguments(plan, callable, &arguments, aliases)?;
            format!("{function}{}({})", turbofish(&generics), args.join(","))
        };
        let invocation = Invocation {
            prelude,
            call,
            return_type: ty.clone(),
            protocol_send: protocol_send.clone(),
            asynchronous,
            construction: false,
        };
        render_case(source, &invocation, &callable.symbol, count, verification)?;
        main.push(format!(
            "case_{}_{}(&mut evidence).await?;",
            safe_name(&callable.symbol),
            count
        ));
        count += 1;
    }
    if count == 0 {
        return Err(RenderFailure::unavailable(
            "bounded candidates produced no public well-typed input",
        ));
    }
    Ok(count)
}
#[allow(clippy::too_many_arguments)]
fn render_initializer_cases(
    config: &RustProjectConfig,
    plan: &RustPlan,
    symbol: &str,
    owner: &Value,
    declarations: &BTreeMap<&str, &Value>,
    aliases: &BTreeMap<String, String>,
    verification: &VerificationConfig,
    source: &mut String,
    main: &mut Vec<String>,
) -> Result<u32, RenderFailure> {
    let mut context = candidate_context(config, plan, owner, declarations, aliases)?;
    let cases = parameter_candidates(initializer_parameters(owner)?, &mut context)?;
    let symbol = format!("{symbol}.init");
    let mut count = 0;
    for values in cases.iter().take(verification.candidate_limit as usize) {
        let call = constructor_expression(owner, values, &context)?;
        let invocation = Invocation {
            prelude: vec![],
            call,
            return_type: json!({"kind":"primitive","name":"unit"}),
            protocol_send: None,
            asynchronous: false,
            construction: true,
        };
        render_case(source, &invocation, &symbol, count, verification)?;
        main.push(format!(
            "case_{}_{}(&mut evidence).await?;",
            safe_name(&symbol),
            count
        ));
        count += 1;
    }
    if count == 0 {
        return Err(RenderFailure::unavailable(
            "initializer has no well-typed bounded candidates",
        ));
    }
    Ok(count)
}
#[allow(clippy::too_many_arguments)]
fn render_nominal_cases(
    config: &RustProjectConfig,
    plan: &RustPlan,
    symbol: &str,
    declaration: &Value,
    declarations: &BTreeMap<&str, &Value>,
    aliases: &BTreeMap<String, String>,
    verification: &VerificationConfig,
    source: &mut String,
    main: &mut Vec<String>,
) -> Result<u32, RenderFailure> {
    let mut context = candidate_context(config, plan, declaration, declarations, aliases)?;
    let ty = concrete_named_type(declaration, &context)?;
    let candidates = named_candidates(&ty, &mut context, 0)?;
    let mut count = 0;
    for call in candidates
        .into_iter()
        .take(verification.candidate_limit as usize)
    {
        let invocation = Invocation {
            prelude: vec![],
            call,
            return_type: json!({"kind":"primitive","name":"unit"}),
            protocol_send: None,
            asynchronous: false,
            construction: true,
        };
        render_case(source, &invocation, symbol, count, verification)?;
        main.push(format!(
            "case_{}_{}(&mut evidence).await?;",
            safe_name(symbol),
            count
        ));
        count += 1;
    }
    if count == 0 {
        return Err(RenderFailure::unavailable(
            "nominal type has no well-typed bounded candidates",
        ));
    }
    Ok(count)
}
fn typed_candidates(
    prefix: &str,
    params: &[Value],
    values: &[String],
    context: &CandidateContext<'_>,
) -> Result<Vec<String>, String> {
    if params.len() != values.len() {
        return Err("Rust candidate arity mismatch".into());
    }
    params
        .iter()
        .zip(values)
        .enumerate()
        .map(|(i, (param, value))| {
            let ty = substitute_candidate_type(&param["type"], context);
            let base = emit::render_consumer_type(context.plan, &ty, context.aliases)?;
            let ty = match param["kind"].as_str() {
                Some("vararg") => format!("Vec<{base}>"),
                Some("kwarg") => format!("cott_runtime::Map<String,{base}>"),
                _ => base,
            };
            let default = param.get("default").is_some_and(|d| !d.is_null());
            Ok(format!(
                "let {prefix}{i}:{}={};",
                if default { format!("Option<{ty}>") } else { ty },
                if default {
                    format!("Some({value})")
                } else {
                    value.clone()
                }
            ))
        })
        .collect()
}
fn constructor_expression(
    owner: &Value,
    values: &[String],
    context: &CandidateContext<'_>,
) -> Result<String, String> {
    let params = initializer_parameters(owner)?;
    if params.len() != values.len() {
        return Err("Rust constructor candidate arity mismatch".into());
    }
    let symbol = emit::render_consumer_symbol(text(owner, "name")?, context.aliases)?;
    let generics = generic_arguments(owner, context)?;
    let args = params
        .iter()
        .zip(values)
        .map(|(p, v)| {
            if p.get("default").is_some_and(|d| !d.is_null()) {
                format!("Some({v})")
            } else {
                v.clone()
            }
        })
        .collect::<Vec<_>>();
    Ok(format!(
        "{symbol}{}::new({})",
        turbofish(&generics),
        args.join(",")
    ))
}
fn generic_arguments(owner: &Value, context: &CandidateContext<'_>) -> Result<Vec<String>, String> {
    let ty = concrete_named_type(owner, context)?;
    emit::render_consumer_type_arguments(context.plan, &ty, context.aliases)
}
fn turbofish(args: &[String]) -> String {
    if args.is_empty() {
        String::new()
    } else {
        format!("::<{}>", args.join(","))
    }
}
fn candidate_context<'a>(
    _config: &'a RustProjectConfig,
    plan: &'a RustPlan,
    owner: &Value,
    declarations: &BTreeMap<&'a str, &'a Value>,
    aliases: &'a BTreeMap<String, String>,
) -> Result<CandidateContext<'a>, RenderFailure> {
    let mut type_arguments = BTreeMap::new();
    let mut consts = BTreeMap::new();
    for g in array(owner, "generics")? {
        let name = text(g, "name")?;
        match g["kind"].as_str() {
            Some("const") => {
                consts.insert(name.into(), "1".into());
            }
            Some("type") => {
                let bounds = array(g, "bounds")?;
                let witness = if bounds.is_empty() {
                    json!({"kind":"primitive","name":"i32"})
                } else {
                    implementation_type_for_bounds(bounds, declarations).ok_or_else(|| {
                        RenderFailure::unavailable(format!(
                            "generic `{name}` has no public concrete bounded witness"
                        ))
                    })?
                };
                type_arguments.insert(name.into(), witness);
            }
            _ => return Err("invalid canonical generic kind".into()),
        }
    }
    let mut context = CandidateContext {
        plan,
        declarations: declarations.clone(),
        aliases,
        type_arguments,
        consts,
        literals: vec![],
        node_limit: 64,
        container_limit: 3,
    };
    let mut seen = BTreeSet::new();
    collect_literals(owner, aliases, &mut context.literals, &mut seen);
    Ok(context)
}
fn parameter_candidates(
    params: &[Value],
    context: &mut CandidateContext<'_>,
) -> Result<Vec<Vec<String>>, RenderFailure> {
    let choices = params
        .iter()
        .map(|p| {
            let values = candidate_values(&p["type"], context, 0)?;
            match p["kind"].as_str() {
                Some("positional" | "keyword_only") => Ok(values),
                Some("vararg") => {
                    let mut out = vec!["Vec::new()".into()];
                    if let Some(v) = values.first() {
                        out.push(format!("vec![{v}]"));
                    }
                    Ok(out)
                }
                Some("kwarg") => {
                    let mut out = vec!["cott_runtime::Map::new(Vec::new())".into()];
                    if let Some(v) = values.first() {
                        out.push(format!(
                            "cott_runtime::Map::new(vec![(\"value\".to_owned(),{v})])"
                        ));
                    }
                    Ok(out)
                }
                _ => Err("unsupported canonical parameter kind".into()),
            }
        })
        .collect::<Result<Vec<_>, RenderFailure>>()?;
    Ok(product_bounded(&choices, 1024))
}
fn concrete_named_type(
    declaration: &Value,
    context: &CandidateContext<'_>,
) -> Result<Value, String> {
    let args=array(declaration,"generics")?.iter().map(|g|{let name=text(g,"name")?;Ok(match g["kind"].as_str(){Some("type")=>json!({"kind":"type","type":context.type_arguments.get(name).ok_or("generic named type has no witness")?}),Some("const")=>json!({"kind":"const","value":{"kind":"value","type":g["type"],"value":serde_json::from_str::<Value>(context.consts.get(name).ok_or("generic named const has no witness")?).map_err(|e|e.to_string())?}}),_=>return Err("invalid named generic kind".into())})}).collect::<Result<Vec<_>,String>>()?;
    Ok(json!({"kind":"named","name":text(declaration,"name")?,"args":args}))
}
fn substitute_candidate_type(value: &Value, context: &CandidateContext<'_>) -> Value {
    if value["kind"] == "type_parameter" {
        if let Some(v) = value["name"]
            .as_str()
            .and_then(|n| context.type_arguments.get(n))
        {
            return v.clone();
        }
    }
    if value["kind"] == "parameter" {
        if let Some(v) = value["name"].as_str().and_then(|n| context.consts.get(n)) {
            return json!({"kind":"value","type":value["type"],"value":serde_json::from_str::<Value>(v).expect("compiler-assigned exact numeric constant")});
        }
    }
    match value {
        Value::Array(a) => Value::Array(
            a.iter()
                .map(|v| substitute_candidate_type(v, context))
                .collect(),
        ),
        Value::Object(m) => Value::Object(
            m.iter()
                .map(|(k, v)| (k.clone(), substitute_candidate_type(v, context)))
                .collect(),
        ),
        _ => value.clone(),
    }
}
fn candidate_values(
    ty: &Value,
    context: &mut CandidateContext<'_>,
    depth: usize,
) -> Result<Vec<String>, RenderFailure> {
    if depth >= context.node_limit {
        return Err(RenderFailure::unavailable(
            "candidate recursion limit exhausted",
        ));
    }
    let ty = substitute_candidate_type(ty, context);
    let values = match ty["kind"].as_str() {
        Some("primitive") => primitive_values(text(&ty, "name")?)?,
        Some("type_parameter") => {
            return Err(RenderFailure::unavailable(
                "abstract generic has no concrete bounded candidate",
            ));
        }
        Some("associated_projection") => {
            let base = &ty["base"];
            let declaration = context
                .declarations
                .get(text(base, "name")?)
                .copied()
                .ok_or_else(|| {
                    RenderFailure::unavailable("associated projection has no concrete owner")
                })?;
            let slot = text(&ty, "name")?;
            let assignment = array(declaration, "associated_types")?
                .iter()
                .find(|a| {
                    a["trait"] == ty["trait"]
                        && a["name"]
                            .as_str()
                            .is_some_and(|n| local_name(n) == local_name(slot))
                })
                .ok_or_else(|| {
                    RenderFailure::unavailable("associated projection has no concrete assignment")
                })?;
            candidate_values(&assignment["type"], context, depth + 1)?
        }
        Some("list" | "set") => {
            let set = ty["kind"] == "set";
            let wrap = |v: &str| {
                if set {
                    format!("cott_runtime::Set::new({v})")
                } else {
                    v.into()
                }
            };
            let mut out = vec![wrap("Vec::new()")];
            if let Some(item) =
                optional_candidate(candidate_values(&ty["item"], context, depth + 1))?
            {
                out.push(wrap(&format!("vec![{item}]")));
            }
            out
        }
        Some("option") => {
            let mut out = vec!["None".into()];
            if let Some(item) =
                optional_candidate(candidate_values(&ty["item"], context, depth + 1))?
            {
                out.push(format!("Some({item})"));
            }
            out
        }
        Some("map") => {
            let mut out = vec!["cott_runtime::Map::new(Vec::new())".into()];
            let key = optional_candidate(candidate_values(&ty["key"], context, depth + 1))?;
            let value = optional_candidate(candidate_values(&ty["value"], context, depth + 1))?;
            if let (Some(k), Some(v)) = (key, value) {
                out.push(format!("cott_runtime::Map::new(vec![({k},{v})])"));
            }
            out
        }
        Some("tuple") => {
            let choices = array(&ty, "items")?
                .iter()
                .map(|t| candidate_values(t, context, depth + 1))
                .collect::<Result<Vec<_>, _>>()?;
            product_bounded(&choices, 16)
                .into_iter()
                .map(|values| {
                    if values.is_empty() {
                        "()".into()
                    } else {
                        format!("({},)", values.join(","))
                    }
                })
                .collect()
        }
        Some("result") => {
            let mut out = vec![];
            if let Some(v) = optional_candidate(candidate_values(&ty["ok"], context, depth + 1))? {
                out.push(format!("Ok({v})"));
            }
            if let Some(v) = optional_candidate(candidate_values(&ty["error"], context, depth + 1))?
            {
                out.push(format!("Err({v})"));
            }
            if out.is_empty() {
                return Err(RenderFailure::unavailable(
                    "Result has no constructible branch",
                ));
            }
            out
        }
        Some("array" | "buffer") => {
            let length = const_numeric(&ty["length"], &context.declarations)
                .map_err(RenderFailure::unavailable)?;
            if length > context.container_limit {
                return Err(RenderFailure::unavailable(format!(
                    "array length {length} exceeds bounded container limit"
                )));
            }
            if ty["kind"] == "buffer" {
                vec![format!("cott_runtime::Buffer::new(vec![0u8;{length}])")]
            } else if length == 0 {
                vec!["cott_runtime::Array::new(Vec::new())".into()]
            } else {
                let value = candidate_values(&ty["item"], context, depth + 1)?
                    .into_iter()
                    .next()
                    .ok_or_else(|| RenderFailure::unavailable("array item has no candidate"))?;
                vec![format!(
                    "cott_runtime::Array::new(vec![{}])",
                    vec![value; length].join(",")
                )]
            }
        }
        Some("future") => {
            let value = candidate_values(&ty["item"], context, depth + 1)?
                .into_iter()
                .next()
                .ok_or_else(|| RenderFailure::unavailable("future item has no candidate"))?;
            vec![format!("Box::pin(async move {{ {value} }})")]
        }
        Some("named") => named_candidates(&ty, context, depth + 1)?,
        Some("factory") => {
            let value = candidate_values(&ty["instance"], context, depth + 1)?
                .into_iter()
                .next()
                .ok_or_else(|| {
                    RenderFailure::unavailable("factory implementation has no candidate")
                })?;
            vec![format!("cott_runtime::Factory::new(|| {{ {value} }})")]
        }
        Some("iterator" | "async_iterator" | "generator" | "async_generator") => {
            return Err(RenderFailure::unavailable(
                "protocol input has no compiler-owned source fixture",
            ));
        }
        Some("dyn") => {
            let concrete = implementation_type_for_bounds(
                std::slice::from_ref(&ty["trait"]),
                &context.declarations,
            )
            .ok_or_else(|| {
                RenderFailure::unavailable("Dyn has no public concrete implementation witness")
            })?;
            candidate_values(&concrete, context, depth + 1)?
                .into_iter()
                .map(|v| emit::render_consumer_dyn(context.plan, &ty["trait"], &v, context.aliases))
                .collect::<Result<Vec<_>, _>>()?
        }
        Some("opaque") => vec![emit::render_consumer_opaque(
            text(&ty, "tag")?,
            "0i32",
            "",
            context.aliases,
        )?],
        Some(other) => {
            return Err(format!("unsupported canonical Rust candidate kind `{other}`").into());
        }
        None => return Err("candidate type has no canonical kind".into()),
    };
    Ok(seed_contract_literals(values, &ty, context))
}
fn named_candidates(
    ty: &Value,
    context: &mut CandidateContext<'_>,
    depth: usize,
) -> Result<Vec<String>, RenderFailure> {
    let name = text(ty, "name")?;
    let declaration = context
        .declarations
        .get(name)
        .copied()
        .ok_or_else(|| format!("named Rust candidate `{name}` absent from canonical IR"))?;
    let mut nested = context.clone();
    let args = array(ty, "args")?;
    let generics = array(declaration, "generics")?;
    if args.len() != generics.len() {
        return Err(RenderFailure::unavailable(
            "named generic has no concrete argument inventory",
        ));
    }
    for (g, arg) in generics.iter().zip(args) {
        let name = text(g, "name")?;
        if g["kind"] == "type" {
            nested
                .type_arguments
                .insert(name.into(), arg["type"].clone());
        } else {
            let value = const_integer(
                &substitute_candidate_type(&arg["value"], context),
                &context.declarations,
            )
            .map_err(RenderFailure::unavailable)?;
            nested.consts.insert(name.into(), value.to_string());
        }
    }
    let mut seen = nested.literals.iter().cloned().collect();
    collect_literals(
        declaration,
        context.aliases,
        &mut nested.literals,
        &mut seen,
    );
    let symbol = emit::render_consumer_symbol(name, context.aliases)?;
    let generic_args = generic_arguments(declaration, &nested)?;
    let constructor = format!("{symbol}{}", turbofish(&generic_args));
    match declaration["kind"].as_str() {
        Some("alias") => candidate_values(&declaration["target"], &mut nested, depth),
        Some("newtype") => Ok(
            candidate_values(&declaration["carrier"], &mut nested, depth)?
                .into_iter()
                .map(|v| format!("{constructor}::new({v})"))
                .collect(),
        ),
        Some("struct") => {
            let fields = array(declaration, "fields")?;
            let choices = fields
                .iter()
                .map(|f| candidate_values(&f["type"], &mut nested, depth))
                .collect::<Result<Vec<_>, _>>()?;
            Ok(product_bounded(&choices, 16)
                .into_iter()
                .map(|values| {
                    let values = fields
                        .iter()
                        .zip(values)
                        .map(|(f, v)| {
                            if f.get("default").is_some_and(|d| !d.is_null()) {
                                format!("Some({v})")
                            } else {
                                v
                            }
                        })
                        .collect::<Vec<_>>();
                    format!("{constructor}::new({})", values.join(","))
                })
                .collect())
        }
        Some("enum") => {
            let mut out = vec![];
            for variant in array(declaration, "variants")?.iter().take(4) {
                let fields = array(variant, "fields")?;
                let choices = match fields
                    .iter()
                    .map(|f| candidate_values(&f["type"], &mut nested, depth))
                    .collect::<Result<Vec<_>, _>>()
                {
                    Ok(c) => c,
                    Err(RenderFailure::Unavailable(_)) => continue,
                    Err(e) => return Err(e),
                };
                let variant = escape_identifier(local_name(text(variant, "symbol")?))?;
                for values in product_bounded(&choices, 4) {
                    out.push(if values.is_empty() {
                        format!("{constructor}::{variant}")
                    } else {
                        format!("{constructor}::{variant}({})", values.join(","))
                    });
                }
            }
            Ok(out)
        }
        Some("resource") => Ok(vec![emit::render_consumer_resource_state(
            text(declaration, "initial")?,
            context.aliases,
        )?]),
        Some("impl") => {
            let choices = parameter_candidates(initializer_parameters(declaration)?, &mut nested)?;
            choices
                .iter()
                .map(|v| {
                    constructor_expression(declaration, v, &nested).map_err(RenderFailure::Fatal)
                })
                .collect()
        }
        Some("trait") => {
            let concrete =
                implementation_type_for_bounds(std::slice::from_ref(ty), &nested.declarations)
                    .ok_or_else(|| {
                        RenderFailure::unavailable(
                            "trait has no constructible concrete public witness",
                        )
                    })?;
            candidate_values(&concrete, &mut nested, depth)
        }
        Some("external_type") => Err(RenderFailure::unavailable(format!(
            "external type `{name}` has no compiler-owned constructor"
        ))),
        _ => Err(format!("named Rust candidate `{name}` has unsupported declaration kind").into()),
    }
}
fn optional_candidate(
    value: Result<Vec<String>, RenderFailure>,
) -> Result<Option<String>, RenderFailure> {
    match value {
        Ok(values) => Ok(values.into_iter().next()),
        Err(RenderFailure::Unavailable(_)) => Ok(None),
        Err(e) => Err(e),
    }
}
fn primitive_values(name: &str) -> Result<Vec<String>, String> {
    match name.to_ascii_lowercase().as_str() {
        "unit" => Ok(vec!["()".into()]),
        "bool" => Ok(vec!["false".into(), "true".into()]),
        "str" | "string" => Ok(vec![
            "String::new()".into(),
            "\"cott\".to_owned()".into(),
            "\" \\n\\t\".to_owned()".into(),
        ]),
        "bytes" => Ok(vec!["Vec::<u8>::new()".into(), "vec![0u8,1,255]".into()]),
        "path" => Ok(vec!["std::path::PathBuf::from(\"cott.txt\")".into()]),
        "any" | "unknown" => Ok(vec![
            "cott_runtime::AnyValue::new(0i32)".into(),
            "cott_runtime::AnyValue::new(String::new())".into(),
        ]),
        "json" | "jsonvalue" | "json_value" => Ok(vec![
            "cott_runtime::JsonValue::Null".into(),
            "cott_runtime::JsonValue::Integer(0)".into(),
        ]),
        "never" => Ok(vec![]),
        "f32" => Ok(vec![
            "0.0f32".into(),
            "1.0f32".into(),
            "-1.0f32".into(),
            "f32::MIN".into(),
            "f32::MAX".into(),
        ]),
        "f64" => Ok(vec![
            "0.0f64".into(),
            "1.0f64".into(),
            "-1.0f64".into(),
            "f64::MIN".into(),
            "f64::MAX".into(),
        ]),
        integer @ ("i8" | "i16" | "i32" | "i64") => Ok(vec![
            format!("0{integer}"),
            format!("1{integer}"),
            format!("-1{integer}"),
            format!("{integer}::MIN"),
            format!("{integer}::MAX"),
        ]),
        integer @ ("u8" | "u16" | "u32" | "u64") => Ok(vec![
            format!("0{integer}"),
            format!("1{integer}"),
            format!("{integer}::MAX"),
        ]),
        _ => Err(format!("unknown primitive candidate type `{name}`")),
    }
}
fn collect_literals(
    value: &Value,
    aliases: &BTreeMap<String, String>,
    literals: &mut Vec<(String, String)>,
    seen: &mut BTreeSet<(String, String)>,
) {
    match value {
        Value::Array(a) => {
            for v in a {
                collect_literals(v, aliases, literals, seen)
            }
        }
        Value::Object(m) => {
            if matches!(
                value["kind"].as_str(),
                Some("literal" | "enum_singleton_ref")
            ) {
                if let Some(key) = candidate_type_key(&value["type"]) {
                    if let Ok(code) = emit::render_consumer_expression(value, aliases) {
                        let candidate = (key, code);
                        if seen.insert(candidate.clone()) {
                            literals.push(candidate);
                        }
                    }
                }
                for candidate in integer_boundary_candidates(value) {
                    if seen.insert(candidate.clone()) {
                        literals.push(candidate);
                    }
                }
            }
            for v in m.values() {
                collect_literals(v, aliases, literals, seen)
            }
        }
        _ => {}
    }
}
fn candidate_type_key(ty: &Value) -> Option<String> {
    match ty["kind"].as_str()? {
        "primitive" => Some(format!(
            "primitive:{}",
            text(ty, "name")
                .ok()?
                .to_ascii_lowercase()
                .replace("string", "str")
        )),
        "named" => Some(format!("named:{}", text(ty, "name").ok()?)),
        _ => None,
    }
}
fn seed_contract_literals(
    values: Vec<String>,
    ty: &Value,
    context: &CandidateContext<'_>,
) -> Vec<String> {
    let mut out = vec![];
    let mut seen = BTreeSet::new();
    if let Some(key) = candidate_type_key(ty) {
        for (k, v) in &context.literals {
            if *k == key && seen.insert(v.clone()) {
                out.push(v.clone());
            }
        }
    }
    for v in values {
        if seen.insert(v.clone()) {
            out.push(v)
        }
    }
    out
}
fn integer_boundary_candidates(expression: &Value) -> Vec<(String, String)> {
    let ty = &expression["type"];
    let Some(name) = ty["name"].as_str() else {
        return vec![];
    };
    let Some(value) = expression
        .pointer("/value/value")
        .and_then(Value::as_str)
        .and_then(|s| s.parse::<i128>().ok())
    else {
        return vec![];
    };
    let bounds = match name {
        "i8" => (i8::MIN as i128, i8::MAX as i128),
        "i16" => (i16::MIN as i128, i16::MAX as i128),
        "i32" => (i32::MIN as i128, i32::MAX as i128),
        "i64" => (i64::MIN as i128, i64::MAX as i128),
        "u8" => (0, u8::MAX as i128),
        "u16" => (0, u16::MAX as i128),
        "u32" => (0, u32::MAX as i128),
        "u64" => (0, u64::MAX as i128),
        _ => return vec![],
    };
    let Some(key) = candidate_type_key(ty) else {
        return vec![];
    };
    [value.checked_add(1), value.checked_sub(1)]
        .into_iter()
        .flatten()
        .filter(|v| (bounds.0..=bounds.1).contains(v))
        .map(|v| (key.clone(), format!("{v}{name}")))
        .collect()
}
fn text<'a>(v: &'a Value, key: &str) -> Result<&'a str, String> {
    v.get(key)
        .and_then(Value::as_str)
        .ok_or_else(|| format!("canonical Rust {key} is not a string"))
}
fn array<'a>(v: &'a Value, key: &str) -> Result<&'a [Value], String> {
    v.get(key)
        .and_then(Value::as_array)
        .map(Vec::as_slice)
        .ok_or_else(|| format!("canonical Rust {key} is not an array"))
}
fn module_aliases(plan: &RustPlan) -> Result<BTreeMap<String, String>, String> {
    let mut out = BTreeMap::new();
    for (index, module) in plan.modules.iter().enumerate() {
        if out
            .insert(module.name.clone(), format!("module_{index}"))
            .is_some()
        {
            return Err("duplicate Rust module alias".into());
        }
    }
    Ok(out)
}
fn declaration_index(plan: &RustPlan) -> Result<BTreeMap<&str, &Value>, String> {
    let mut out = BTreeMap::new();
    for module in &plan.modules {
        for declaration in &module.declarations {
            let symbol = text(declaration, "name")?;
            if out.insert(symbol, declaration).is_some() {
                return Err(format!("duplicate Rust declaration `{symbol}`"));
            }
        }
    }
    Ok(out)
}
fn callable_is_public(callable: &RustCallable) -> Result<bool, String> {
    callable
        .owner
        .as_ref()
        .unwrap_or(&callable.declaration)
        .get("public")
        .and_then(Value::as_bool)
        .ok_or_else(|| format!("callable `{}` has no visibility", callable.symbol))
}
fn safe_name(value: &str) -> String {
    let mut result = String::new();
    for byte in value.bytes() {
        if byte.is_ascii_lowercase() || byte.is_ascii_digit() {
            result.push(byte as char);
        } else {
            write!(result, "_{byte:02x}").unwrap();
        }
    }
    result
}
pub(crate) fn validate_support() -> Result<Value, String> {
    Ok(
        json!({"implementation":"std-only SHA-256/HMAC-SHA256","files":{"evidence.rs":format!("sha256:{}",crate::hash::sha256_hex(include_bytes!("runner_support.rs"))),"scenario.rs":format!("sha256:{}",crate::hash::sha256_hex(include_bytes!("runner_scenario_support.rs"))),"confinement.rs":format!("sha256:{}",crate::hash::sha256_hex(include_bytes!("runner_confinement_support.rs")))}}),
    )
}

fn implementation_type_for_bounds(
    bounds: &[Value],
    declarations: &BTreeMap<&str, &Value>,
) -> Option<Value> {
    declarations.values().find_map(|declaration| {
        let satisfies = |bound: &Value| {
            let required = bound.get("name").and_then(Value::as_str)?;
            let unparameterized = bound
                .get("args")
                .and_then(Value::as_array)
                .is_none_or(Vec::is_empty);
            Some(
                declaration
                    .get("traits")
                    .and_then(Value::as_array)
                    .is_some_and(|traits| {
                        traits.iter().any(|trait_ref| {
                            trait_ref == bound
                                || (unparameterized
                                    && trait_ref.get("name").and_then(Value::as_str).is_some_and(
                                        |actual| {
                                            trait_reaches(
                                                actual,
                                                required,
                                                declarations,
                                                &mut BTreeSet::new(),
                                            )
                                        },
                                    ))
                        })
                    }),
            )
        };
        if declaration.get("kind").and_then(Value::as_str) != Some("impl")
            || declaration.get("public").and_then(Value::as_bool) != Some(true)
            || !bounds.iter().all(|bound| satisfies(bound) == Some(true))
        {
            return None;
        }
        Some(serde_json::json!({
            "kind": "named",
            "name": declaration.get("name").and_then(Value::as_str)?,
            "args": []
        }))
    })
}

fn trait_reaches(
    actual: &str,
    required: &str,
    declarations: &BTreeMap<&str, &Value>,
    seen: &mut BTreeSet<String>,
) -> bool {
    if actual == required {
        return true;
    }
    if !seen.insert(actual.to_owned()) {
        return false;
    }
    declarations
        .get(actual)
        .and_then(|declaration| declaration.get("parents"))
        .and_then(Value::as_array)
        .is_some_and(|parents| {
            parents.iter().any(|parent| {
                parent
                    .get("trait")
                    .and_then(|trait_ref| trait_ref.get("name"))
                    .and_then(Value::as_str)
                    .is_some_and(|parent| trait_reaches(parent, required, declarations, seen))
            })
        })
}
fn initializer_parameters(owner: &Value) -> Result<&[Value], String> {
    match owner.get("init") {
        Some(Value::Null) => Ok(&[]),
        Some(initializer) => initializer
            .get("parameters")
            .and_then(Value::as_array)
            .map(Vec::as_slice)
            .ok_or_else(|| "Rust canonical initializer has no parameter inventory".to_owned()),
        None => Err("Rust canonical implementation has no initializer field".to_owned()),
    }
}
fn const_numeric(value: &Value, declarations: &BTreeMap<&str, &Value>) -> Result<usize, String> {
    usize::try_from(const_integer(value, declarations)?)
        .map_err(|_| "constant is not a bounded unsigned container length".into())
}
fn const_integer(value: &Value, declarations: &BTreeMap<&str, &Value>) -> Result<i128, String> {
    match value["kind"].as_str() {
        Some("value" | "integer") => value["value"]
            .as_i64()
            .map(i128::from)
            .or_else(|| value["value"].as_u64().map(i128::from))
            .or_else(|| value["value"].as_str().and_then(|v| v.parse::<i128>().ok()))
            .ok_or_else(|| "constant is not an exact integer".into()),
        Some("reference") => {
            let name = text(value, "symbol")?;
            const_integer(
                &declarations
                    .get(name)
                    .ok_or_else(|| format!("constant reference `{name}` has no declaration"))?["value"],
                declarations,
            )
        }
        Some("binary") => {
            let left = const_integer(&value["left"], declarations)?;
            let right = const_integer(&value["right"], declarations)?;
            let result = match value["op"].as_str() {
                Some("add") => left.checked_add(right),
                Some("subtract" | "sub") => left.checked_sub(right),
                Some("multiply" | "mul") => left.checked_mul(right),
                Some("divide" | "div") if right != 0 => left.checked_div_euclid(right),
                Some("modulo" | "mod") if right != 0 => left.checked_rem_euclid(right),
                _ => None,
            }
            .ok_or("constant arithmetic overflow or invalid operator")?;
            if result < i64::MIN as i128 || result > u64::MAX as i128 {
                return Err("constant exceeds supported exact native integer widths".into());
            }
            Ok(result)
        }
        _ => Err("constant has no concrete integer value".into()),
    }
}
fn product_bounded(choices: &[Vec<String>], limit: usize) -> Vec<Vec<String>> {
    bounded_product_indices(&choices.iter().map(Vec::len).collect::<Vec<_>>(), limit)
        .into_iter()
        .map(|indices| {
            indices
                .into_iter()
                .enumerate()
                .map(|(dimension, index)| choices[dimension][index].clone())
                .collect()
        })
        .collect()
}

fn bounded_product_indices(lengths: &[usize], limit: usize) -> Vec<Vec<usize>> {
    if limit == 0 || lengths.contains(&0) {
        return Vec::new();
    }
    // Visit low-index candidates in every dimension before advancing deeply in one.
    // Literal seeds retain priority without starving other parameters or receivers.
    let mut pending = BTreeSet::from([(0usize, vec![0usize; lengths.len()])]);
    let mut product = Vec::new();
    while product.len() < limit {
        let Some((distance, indices)) = pending.pop_first() else {
            break;
        };
        for (dimension, length) in lengths.iter().enumerate() {
            if indices[dimension] + 1 < *length {
                let mut next = indices.clone();
                next[dimension] += 1;
                pending.insert((distance + 1, next));
            }
        }
        product.push(indices);
    }
    product
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn exact_const_candidates_preserve_native_width_boundaries_and_euclidean_arithmetic() {
        let declarations = BTreeMap::new();
        assert_eq!(
            const_integer(
                &json!({"kind":"value","type":"u64","value":u64::MAX}),
                &declarations
            )
            .unwrap(),
            u64::MAX as i128
        );
        assert_eq!(
            const_integer(
                &json!({"kind":"value","type":"i64","value":i64::MIN}),
                &declarations
            )
            .unwrap(),
            i64::MIN as i128
        );
        let value = |n: i64| json!({"kind":"value","type":"i64","value":n});
        assert_eq!(
            const_integer(
                &json!({"kind":"binary","op":"divide","left":value(-3),"right":value(2)}),
                &declarations
            )
            .unwrap(),
            -2
        );
        assert_eq!(
            const_integer(
                &json!({"kind":"binary","op":"modulo","left":value(-3),"right":value(2)}),
                &declarations
            )
            .unwrap(),
            1
        );
        assert!(const_numeric(&value(-1), &declarations).is_err());
        assert!(
            const_integer(
                &json!({"kind":"binary","op":"divide","left":value(3),"right":value(0)}),
                &declarations
            )
            .is_err()
        );
    }
    #[test]
    fn bounded_product_visits_all_parameter_dimensions_before_deepening_one() {
        assert_eq!(
            bounded_product_indices(&[3, 3], 3),
            vec![vec![0, 0], vec![0, 1], vec![1, 0]]
        );
        assert_eq!(bounded_product_indices(&[], 4), vec![Vec::<usize>::new()]);
        assert!(bounded_product_indices(&[0, 3], 4).is_empty());
    }
}
