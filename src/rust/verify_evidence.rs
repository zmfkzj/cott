use super::*;

pub(super) fn validate_events(
    plan: &RustPlan,
    program: &RunnerProgram,
    strategies: &[ContractTestStrategy],
    events: &[Value],
) -> Result<(), String> {
    let mut expected_clauses = BTreeSet::new();
    for (symbol, clause) in coverage_inventory(plan, strategies)? {
        for alias in observation_aliases(&symbol) {
            expected_clauses.insert((alias, clause.clone()));
        }
    }
    for declaration in plan
        .modules
        .iter()
        .flat_map(|module| &module.declarations)
        .filter(|declaration| {
            declaration.get("public").and_then(Value::as_bool) == Some(true)
                && declaration.get("kind").and_then(Value::as_str) == Some("newtype")
                && declaration
                    .get("refinement")
                    .is_some_and(|value| !value.is_null())
        })
    {
        if let Some(symbol) = declaration.get("name").and_then(Value::as_str) {
            expected_clauses.insert((symbol.to_owned(), "refinement".to_owned()));
        }
    }
    // The facade's `error-return` check is observed like a clause but is no coverage clause.
    for callable in plan.callables() {
        // Compiler safety checks are authentic runtime observations, not IR
        // coverage clauses. Admit only checks emitted for this concrete owner.
        if let Some(owner) = &callable.owner {
            expected_clauses.insert((callable.symbol.clone(), "receiver-identity".to_owned()));
            if let Some(fields) = owner["state"].as_array() {
                for field in fields {
                    if let Some(name) = field["name"].as_str() {
                        expected_clauses.insert((callable.symbol.clone(), name.to_owned()));
                    }
                }
            }
            if callable.declaration["transitions"]
                .as_array()
                .is_some_and(|v| !v.is_empty())
            {
                expected_clauses.insert((callable.symbol.clone(), "transition-before".to_owned()));
                expected_clauses.insert((callable.symbol.clone(), "transition-after".to_owned()));
            }
        }
        if callable
            .declaration
            .as_object()
            .is_some_and(super::emit::checks_error_return)
        {
            for alias in observation_aliases(&callable.symbol) {
                expected_clauses.insert((alias, "error-return".to_owned()));
            }
        }
    }
    let mut seen_cases = BTreeSet::new();
    let mut seen_cancellations = BTreeSet::new();
    let mut seen_scenarios = BTreeSet::new();
    let mut done = 0usize;
    for (index, event) in events.iter().enumerate() {
        match event.get("kind").and_then(Value::as_str) {
            Some("done") => {
                exact_event_fields(event, &["kind"], "completion")?;
                if index + 1 != events.len() {
                    return Err("Rust runner completion marker was not the final event".to_owned());
                }
                done += 1;
            }
            Some("case") => {
                exact_event_fields(
                    event,
                    &[
                        "kind",
                        "symbol",
                        "case",
                        "status",
                        "phase",
                        "clause",
                        "error_symbol",
                        "observations",
                    ],
                    "case",
                )?;
                validate_optional_event_strings(
                    event,
                    &["phase", "clause", "error_symbol"],
                    "Rust case",
                )?;
                let symbol = required_event_string(event, "symbol")?;
                let case = required_event_u32(event, "case")?;
                let expected = program.expected_cases.get(symbol).ok_or_else(|| {
                    format!("Rust contract runner emitted an unknown case for `{symbol}`")
                })?;
                if case >= *expected || !seen_cases.insert((symbol.to_owned(), case)) {
                    return Err(format!(
                        "Rust contract runner emitted a duplicate or out-of-range case for `{symbol}`"
                    ));
                }
                let observations = validate_observations(event, &expected_clauses, "Rust case")?;
                let status = required_event_string(event, "status")?;
                match status {
                    "passed" => {
                        if observations.iter().any(|observation| {
                            observation.get("passed").and_then(Value::as_bool) == Some(false)
                        }) {
                            return Err(format!(
                                "Rust runtime reported a failed clause without rejecting `{symbol}`"
                            ));
                        }
                        require_null_event_fields(
                            event,
                            &["phase", "clause", "error_symbol"],
                            "passed Rust case",
                        )?;
                    }
                    "ineligible" => {
                        if event.get("phase").and_then(Value::as_str) != Some("requires")
                            || !observations.iter().any(|observation| {
                                observation.get("phase").and_then(Value::as_str) == Some("requires")
                                    && observation.get("passed").and_then(Value::as_bool)
                                        == Some(false)
                            })
                        {
                            return Err(format!(
                                "Rust runner marked `{symbol}` ineligible without a failed requires observation"
                            ));
                        }
                    }
                    "candidate_unavailable" => {
                        if event.get("phase").and_then(Value::as_str).is_none()
                            || !observations.iter().any(|observation| {
                                observation.get("passed").and_then(Value::as_bool) == Some(false)
                            })
                        {
                            return Err(format!(
                                "Rust runner marked `{symbol}` candidate unavailable without an observed construction failure"
                            ));
                        }
                    }
                    "failed" | "timeout" | "unexpected_cancellation" | "unexpected_exception" => {
                        let detail = match (
                            event.get("phase").and_then(Value::as_str),
                            event.get("clause").and_then(Value::as_str),
                        ) {
                            (Some(phase), Some(clause)) => format!(": {phase} {clause}"),
                            (Some(phase), None) => format!(": {phase}"),
                            _ => String::new(),
                        };
                        return Err(format!(
                            "Rust contract execution failed for `{symbol}` case {case} ({status}{detail})"
                        ));
                    }
                    other => {
                        return Err(format!("Rust runner emitted unknown case status `{other}`"));
                    }
                }
            }
            Some("cancellation") => {
                exact_event_fields(
                    event,
                    &[
                        "kind",
                        "symbol",
                        "case",
                        "status",
                        "cooperative",
                        "future_preempted",
                        "reason",
                    ],
                    "cancellation",
                )?;
                let symbol = required_event_string(event, "symbol")?;
                let case = required_event_u32(event, "case")?;
                let key = (symbol.to_owned(), case);
                if !program.expected_cancellations.contains(&key) || !seen_cancellations.insert(key)
                {
                    return Err(format!(
                        "Rust runner emitted duplicate or unknown cancellation evidence for `{symbol}`"
                    ));
                }
                let reason = required_event_string(event, "reason")?;
                if required_event_string(event, "status")? != "passed"
                    || event.get("cooperative").and_then(Value::as_bool) != Some(true)
                    || event.get("future_preempted").and_then(Value::as_bool) != Some(false)
                    || reason.is_empty()
                {
                    return Err(format!(
                        "Rust cancellation evidence for `{symbol}` does not prove cooperative observation without Future preemption"
                    ));
                }
            }
            Some("scenario") => {
                const SCENARIO_FIELDS: [&str; 8] = [
                    "kind",
                    "scenario_id",
                    "symbol",
                    "status",
                    "assertions",
                    "cancellations",
                    "cleaned",
                    "observations",
                ];
                let passed = match required_event_string(event, "status")? {
                    "passed" => true,
                    "failed" => false,
                    other => {
                        return Err(format!(
                            "Rust runner emitted unknown scenario status `{other}`"
                        ));
                    }
                };
                if passed {
                    exact_event_fields(event, &SCENARIO_FIELDS, "scenario")?;
                } else {
                    let mut fields = SCENARIO_FIELDS.to_vec();
                    fields.extend([
                        "failure",
                        "failed_step",
                        "phase",
                        "clause",
                        "error_symbol",
                        "exception_type",
                    ]);
                    exact_event_fields(event, &fields, "scenario")?;
                }
                let id = required_event_string(event, "scenario_id")?;
                let expectation = program
                    .expected_scenarios
                    .get(id)
                    .ok_or_else(|| format!("Rust runner emitted unknown scenario `{id}`"))?;
                if !seen_scenarios.insert(id.to_owned()) {
                    return Err(format!("Rust runner emitted duplicate scenario `{id}`"));
                }
                if !passed {
                    return Err(scenario_failure(id, event)?);
                }
                if required_event_string(event, "symbol")? != expectation.symbol.as_str()
                    || required_event_u32(event, "assertions")? != expectation.assertions
                    || required_event_u32(event, "cancellations")? != expectation.cancellations
                    || event.get("cleaned").and_then(Value::as_bool) != Some(true)
                {
                    return Err(format!(
                        "Rust scenario `{id}` evidence does not match its finite plan or cleanup"
                    ));
                }
                let observations =
                    validate_observations(event, &expected_clauses, "Rust scenario")?;
                if observations.iter().any(|observation| {
                    observation.get("passed").and_then(Value::as_bool) == Some(false)
                }) {
                    return Err(format!(
                        "Rust scenario `{id}` failed: a runtime clause observation failed"
                    ));
                }
            }
            Some(other) => return Err(format!("Rust runner emitted unknown event `{other}`")),
            None => return Err("Rust contract runner event has no kind".to_owned()),
        }
    }
    if done != 1 {
        return Err("Rust contract runner completion marker is missing or duplicated".to_owned());
    }
    for (symbol, count) in &program.expected_cases {
        for case in 0..*count {
            if !seen_cases.contains(&(symbol.clone(), case)) {
                return Err(format!(
                    "Rust contract runner omitted `{symbol}` case {case}"
                ));
            }
        }
    }
    if seen_cancellations != program.expected_cancellations {
        return Err("Rust contract runner omitted cooperative cancellation evidence".to_owned());
    }
    if seen_scenarios
        != program
            .expected_scenarios
            .keys()
            .cloned()
            .collect::<BTreeSet<_>>()
    {
        return Err("Rust contract runner omitted an enforceable scenario".to_owned());
    }
    Ok(())
}

fn exact_event_fields(event: &Value, expected: &[&str], kind: &str) -> Result<(), String> {
    let object = event
        .as_object()
        .ok_or_else(|| format!("Rust {kind} event is not an object"))?;
    let actual = object.keys().map(String::as_str).collect::<BTreeSet<_>>();
    let expected = expected.iter().copied().collect::<BTreeSet<_>>();
    if actual != expected {
        return Err(format!("Rust {kind} event has unexpected fields"));
    }
    Ok(())
}

/// The failure message of one failed scenario event. It always starts with
/// ``Rust scenario `<id>` failed`` so requirement reports can bind the failure.
fn scenario_failure(id: &str, event: &Value) -> Result<String, String> {
    validate_optional_event_strings(
        event,
        &["phase", "clause", "error_symbol", "exception_type"],
        "Rust scenario",
    )?;
    let step = match event.get("failed_step") {
        Some(Value::Null) => None,
        Some(_) => Some(required_event_u32(event, "failed_step")?),
        None => return Err("Rust scenario failure has no failed_step".to_owned()),
    };
    let at = step
        .map(|step| format!(" at step:{step}"))
        .unwrap_or_default();
    let text = |field: &str| event.get(field).and_then(Value::as_str);
    Ok(match required_event_string(event, "failure")? {
        "assertion" => format!(
            "Rust scenario `{id}` failed: assertion step:{} failed",
            step.ok_or("Rust scenario assertion failure has no step")?
        ),
        "contract" => format!(
            "Rust scenario `{id}` failed{at}: contract violation for `{}` ({}{})",
            text("error_symbol").unwrap_or("unknown symbol"),
            text("phase").unwrap_or("unknown phase"),
            text("clause")
                .map(|clause| format!(" {clause}"))
                .unwrap_or_default()
        ),
        "timeout" => format!("Rust scenario `{id}` failed{at}: the scenario timeout elapsed"),
        "cancellation" => format!(
            "Rust scenario `{id}` failed{at}: the worker finished without observing its cancellation"
        ),
        "exception" => format!(
            "Rust scenario `{id}` failed{at}: unexpected {}",
            text("exception_type").unwrap_or("exception")
        ),
        "lifecycle" => format!(
            "Rust scenario `{id}` failed: a worker, fixture server or scratch cleanup did not finish"
        ),
        other => {
            return Err(format!(
                "Rust runner emitted unknown scenario failure `{other}`"
            ));
        }
    })
}

fn require_null_event_fields(event: &Value, fields: &[&str], context: &str) -> Result<(), String> {
    if fields
        .iter()
        .any(|field| event.get(*field).is_none_or(|value| !value.is_null()))
    {
        return Err(format!("{context} has unexpected error metadata"));
    }
    Ok(())
}

fn validate_optional_event_strings(
    event: &Value,
    fields: &[&str],
    context: &str,
) -> Result<(), String> {
    if fields.iter().any(|field| {
        event
            .get(*field)
            .is_none_or(|value| !value.is_null() && !value.is_string())
    }) {
        return Err(format!("{context} has malformed error metadata"));
    }
    Ok(())
}

fn validate_observations<'a>(
    event: &'a Value,
    expected_clauses: &BTreeSet<(String, String)>,
    context: &str,
) -> Result<&'a [Value], String> {
    let observations = event
        .get("observations")
        .and_then(Value::as_array)
        .ok_or_else(|| format!("{context} observations are not an array"))?;
    for observation in observations {
        exact_event_fields(
            observation,
            &[
                "symbol",
                "clause",
                "phase",
                "status",
                "passed",
                "reason",
                "applicable",
            ],
            "clause observation",
        )?;
        let symbol = required_event_string(observation, "symbol")?;
        let clause = required_event_string(observation, "clause")?;
        required_event_string(observation, "phase")?;
        if !expected_clauses
            .iter()
            .any(|(expected_symbol, expected_clause)| {
                expected_symbol == symbol && expected_clause == clause
            })
        {
            return Err(format!(
                "Rust runner emitted unknown clause observation `{symbol}:{clause}`"
            ));
        }
        let status = required_event_string(observation, "status")?;
        let passed = observation.get("passed").unwrap_or(&Value::Null);
        match status {
            "passed" if passed == &Value::Bool(true) => {
                if observation
                    .get("reason")
                    .is_none_or(|reason| !reason.is_null())
                {
                    return Err("Rust passed clause observation has a reason".to_owned());
                }
            }
            "failed" if passed == &Value::Bool(false) => {
                if observation
                    .get("reason")
                    .is_none_or(|reason| !reason.is_null())
                {
                    return Err("Rust failed clause observation has a reason".to_owned());
                }
            }
            "unobserved" if passed.is_null() => {
                if observation
                    .get("reason")
                    .and_then(Value::as_str)
                    .is_none_or(str::is_empty)
                {
                    return Err("Rust unobserved clause has no reason".to_owned());
                }
            }
            _ => {
                return Err("Rust clause observation status/passed fields disagree".to_owned());
            }
        }
        let applicable = observation.get("applicable").unwrap_or(&Value::Null);
        if !applicable.is_null() && !applicable.is_boolean() {
            return Err("Rust clause observation applicable field is not a boolean".to_owned());
        }
    }
    Ok(observations)
}

pub(super) fn contract_report(
    plan: &RustPlan,
    strategies: &[ContractTestStrategy],
    program: &RunnerProgram,
    events: &[Value],
) -> Result<Value, String> {
    let case_events = events
        .iter()
        .filter(|event| event.get("kind").and_then(Value::as_str) == Some("case"))
        .collect::<Vec<_>>();
    let scenario_events = events
        .iter()
        .filter(|event| event.get("kind").and_then(Value::as_str) == Some("scenario"))
        .collect::<Vec<_>>();
    let mut passed_cases = BTreeMap::<String, u64>::new();
    let mut ineligible_cases = BTreeMap::<String, u64>::new();
    let mut unavailable_cases = BTreeMap::<String, u64>::new();
    for event in &case_events {
        let symbol = required_event_string(event, "symbol")?.to_owned();
        match required_event_string(event, "status")? {
            "passed" => *passed_cases.entry(symbol).or_default() += 1,
            "ineligible" => *ineligible_cases.entry(symbol).or_default() += 1,
            "candidate_unavailable" => {
                *unavailable_cases.entry(symbol).or_default() += 1;
            }
            _ => {}
        }
    }
    let mut contracts = Vec::new();
    for (symbol, clause_id) in coverage_inventory(plan, strategies)? {
        let span = clause_span(plan, &symbol, &clause_id)?;
        let guarded = clause_is_guarded(plan, &symbol, &clause_id);
        let aliases = observation_aliases(&symbol);
        let mut phases = BTreeSet::new();
        let mut valid_cases = BTreeSet::new();
        let mut valid_scenarios = BTreeSet::new();
        for event in &case_events {
            if event.get("status").and_then(Value::as_str) != Some("passed") {
                continue;
            }
            for observation in event
                .get("observations")
                .and_then(Value::as_array)
                .ok_or("Rust case observations are not an array")?
            {
                let observed_symbol = observation
                    .get("symbol")
                    .and_then(Value::as_str)
                    .ok_or("Rust clause observation has no symbol")?;
                if aliases.contains(observed_symbol)
                    && observation.get("clause").and_then(Value::as_str) == Some(clause_id.as_str())
                    && observation.get("passed").and_then(Value::as_bool) == Some(true)
                    && (!guarded
                        || observation.get("applicable").and_then(Value::as_bool) == Some(true))
                {
                    phases.insert(
                        observation
                            .get("phase")
                            .and_then(Value::as_str)
                            .unwrap_or("contract")
                            .to_owned(),
                    );
                    valid_cases.insert((
                        required_event_string(event, "symbol")?.to_owned(),
                        required_event_u32(event, "case")?,
                    ));
                }
            }
        }
        for event in &scenario_events {
            if event.get("status").and_then(Value::as_str) != Some("passed") {
                continue;
            }
            for observation in event
                .get("observations")
                .and_then(Value::as_array)
                .ok_or("Rust scenario observations are not an array")?
            {
                let observed_symbol = observation
                    .get("symbol")
                    .and_then(Value::as_str)
                    .ok_or("Rust scenario clause observation has no symbol")?;
                if aliases.contains(observed_symbol)
                    && observation.get("clause").and_then(Value::as_str) == Some(clause_id.as_str())
                    && observation.get("passed").and_then(Value::as_bool) == Some(true)
                    && (!guarded
                        || observation.get("applicable").and_then(Value::as_bool) == Some(true))
                {
                    phases.insert(
                        observation
                            .get("phase")
                            .and_then(Value::as_str)
                            .unwrap_or("contract")
                            .to_owned(),
                    );
                    valid_scenarios.insert(required_event_string(event, "scenario_id")?.to_owned());
                }
            }
        }
        let evidence = if !valid_cases.is_empty() || !valid_scenarios.is_empty() {
            vec![json!({
                "applicable_cases": valid_cases.len() + valid_scenarios.len(),
                "grade": "runtime check",
                "phases": phases,
                "positive_applicable": true,
                "status": "passed",
                "valid_cases": valid_cases.len() + valid_scenarios.len(),
            })]
        } else {
            let reason = if let Some(reason) = program.unavailable.get(&symbol) {
                reason.clone()
            } else if guarded {
                "no matched guarded clause condition completed successfully".to_owned()
            } else if clause_id.starts_with("error:") {
                "individual Result error branch was not reached by a positive applicable case"
                    .to_owned()
            } else if clause_id.starts_with("modifies:") {
                "a modifies permission is not itself evidence of a state mutation".to_owned()
            } else if passed_cases.get(&symbol).copied().unwrap_or(0) == 0
                && ineligible_cases.get(&symbol).copied().unwrap_or(0) > 0
            {
                "no bounded candidate satisfied every requires clause".to_owned()
            } else if passed_cases.get(&symbol).copied().unwrap_or(0) == 0
                && unavailable_cases.get(&symbol).copied().unwrap_or(0) > 0
            {
                "no bounded candidate could be constructed by the public facade".to_owned()
            } else if matches!(
                plan.modules
                    .iter()
                    .flat_map(|module| &module.declarations)
                    .find(|declaration| {
                        declaration.get("name").and_then(Value::as_str) == Some(symbol.as_str())
                    })
                    .and_then(|declaration| declaration.get("kind"))
                    .and_then(Value::as_str),
                Some("newtype" | "struct")
            ) {
                "no bounded public consumer constructed this nominal type".to_owned()
            } else {
                return Err(format!(
                    "Rust runtime produced no positive applicable evidence for observable clause `{symbol}:{clause_id}`"
                ));
            };
            vec![json!({
                "applicable_cases": 0,
                "grade": "unobserved",
                "reason": reason,
                "status": "unknown",
                "valid_cases": 0,
            })]
        };
        contracts.push(json!({
            "clause_id": clause_id,
            "evidence": evidence,
            "span": span,
            "symbol": symbol,
        }));
    }
    contracts.sort_by(|left, right| {
        coverage_key(
            left.get("symbol")
                .and_then(Value::as_str)
                .unwrap_or_default(),
            left.get("clause_id")
                .and_then(Value::as_str)
                .unwrap_or_default(),
        )
        .cmp(&coverage_key(
            right
                .get("symbol")
                .and_then(Value::as_str)
                .unwrap_or_default(),
            right
                .get("clause_id")
                .and_then(Value::as_str)
                .unwrap_or_default(),
        ))
    });
    let cases = case_events
        .into_iter()
        .map(|event| {
            json!({
                "case": event.get("case").cloned().unwrap_or(Value::Null),
                "status": event.get("status").cloned().unwrap_or(Value::Null),
                "symbol": event.get("symbol").cloned().unwrap_or(Value::Null),
            })
        })
        .collect::<Vec<_>>();
    let lifecycle = events
        .iter()
        .filter(|event| event.get("kind").and_then(Value::as_str) == Some("cancellation"))
        .cloned()
        .collect::<Vec<_>>();
    let scenarios = events
        .iter()
        .filter(|event| event.get("kind").and_then(Value::as_str) == Some("scenario"))
        .cloned()
        .collect::<Vec<_>>();
    let strategy_values = strategies
        .iter()
        .map(serde_json::to_value)
        .collect::<Result<Vec<_>, _>>()
        .map_err(|error| format!("serialize Rust contract strategy: {error}"))?;
    Ok(json!({
        "cases": cases,
        "contracts": contracts,
        "lifecycle": lifecycle,
        "observation_inventory": {
            "cases": cases.len(),
            "clauses": contracts.len(),
            "lifecycle": lifecycle.len(),
            "scenarios": scenarios.len(),
            "strategies": strategies.len(),
            "status": if strategies.is_empty() && contracts.is_empty() { "not_applicable" } else { "executed" },
        },
        "scenarios": scenarios,
        "strategies": strategy_values,
        "unavailable": program.unavailable,
    }))
}

fn coverage_inventory(
    plan: &RustPlan,
    strategies: &[ContractTestStrategy],
) -> Result<Vec<(String, String)>, String> {
    let mut inventory = strategies
        .iter()
        .flat_map(|strategy| {
            strategy
                .clause_ids
                .iter()
                .map(|clause| (strategy.symbol.clone(), clause.clone()))
        })
        .collect::<Vec<_>>();
    for declaration in plan
        .modules
        .iter()
        .flat_map(|module| &module.declarations)
        .filter(|declaration| declaration.get("public").and_then(Value::as_bool) == Some(true))
    {
        let Some(symbol) = declaration.get("name").and_then(Value::as_str) else {
            continue;
        };
        match declaration.get("kind").and_then(Value::as_str) {
            Some(kind @ ("struct" | "newtype")) => {
                for invariant in declaration
                    .get("invariants")
                    .and_then(Value::as_array)
                    .into_iter()
                    .flatten()
                {
                    let clause = invariant
                        .get("clause_id")
                        .and_then(Value::as_u64)
                        .ok_or_else(|| {
                            format!("Rust {kind} `{symbol}` invariant has no clause_id")
                        })?;
                    inventory.push((symbol.to_owned(), format!("invariant:{clause}")));
                }
            }
            _ => {}
        }
    }
    inventory.sort_by(|left, right| {
        coverage_key(&left.0, &left.1).cmp(&coverage_key(&right.0, &right.1))
    });
    inventory.dedup();
    Ok(inventory)
}

fn clause_is_guarded(plan: &RustPlan, symbol: &str, clause_id: &str) -> bool {
    let Some((kind, id)) = clause_id.split_once(':') else {
        return false;
    };
    let Ok(id) = id.parse::<u64>() else {
        return false;
    };
    if kind == "modifies" {
        return false;
    }
    if let Some(callable) = plan
        .callables()
        .iter()
        .find(|callable| callable.symbol == symbol)
    {
        if find_guarded_clause(&callable.declaration, kind, id) {
            return true;
        }
        return kind == "invariant"
            && callable
                .owner
                .as_ref()
                .and_then(|owner| owner.get("invariants"))
                .is_some_and(|value| find_guarded_clause(value, kind, id));
    }
    let owner_symbol = symbol.strip_suffix(".init").unwrap_or(symbol);
    plan.modules
        .iter()
        .flat_map(|module| &module.declarations)
        .find(|declaration| declaration.get("name").and_then(Value::as_str) == Some(owner_symbol))
        .and_then(|owner| {
            if kind == "invariant" {
                owner.get("invariants")
            } else {
                owner.get("init")
            }
        })
        .is_some_and(|scope| find_guarded_clause(scope, kind, id))
}

fn find_guarded_clause(value: &Value, kind: &str, id: u64) -> bool {
    match value {
        Value::Object(object) => {
            let matches = if kind == "invariant" {
                object.get("kind").is_none()
                    && object.get("clause_id").and_then(Value::as_u64) == Some(id)
                    && object.get("expression").is_some()
                    && object.get("span").is_some()
            } else {
                object.get("kind").and_then(Value::as_str) == Some(kind)
                    && object.get("clause_id").and_then(Value::as_u64) == Some(id)
            };
            (matches && object.get("guard").is_some_and(|guard| !guard.is_null()))
                || object
                    .values()
                    .any(|child| find_guarded_clause(child, kind, id))
        }
        Value::Array(values) => values
            .iter()
            .any(|child| find_guarded_clause(child, kind, id)),
        _ => false,
    }
}

fn clause_span(plan: &RustPlan, symbol: &str, clause_id: &str) -> Result<Value, String> {
    if clause_id == "refinement" {
        return plan
            .modules
            .iter()
            .flat_map(|module| &module.declarations)
            .find(|declaration| {
                declaration.get("name").and_then(Value::as_str) == Some(symbol)
                    && declaration.get("kind").and_then(Value::as_str) == Some("newtype")
            })
            .and_then(|declaration| declaration.pointer("/refinement/span"))
            .cloned()
            .ok_or_else(|| format!("no Rust newtype span owns `{symbol}:{clause_id}`"));
    }
    let (kind, id) = clause_id
        .split_once(':')
        .ok_or_else(|| format!("invalid Rust clause ID `{symbol}:{clause_id}`"))?;
    if kind == "modifies" {
        return plan
            .callables()
            .iter()
            .find(|callable| callable.symbol == symbol)
            .and_then(|callable| callable.declaration.get("span"))
            .cloned()
            .ok_or_else(|| format!("no Rust callable span owns `{symbol}:{clause_id}`"));
    }
    let numeric = id
        .parse::<u64>()
        .map_err(|_| format!("invalid Rust clause ID `{symbol}:{clause_id}`"))?;
    let owner_symbol = symbol.strip_suffix(".init").unwrap_or(symbol);
    let callable = plan
        .callables()
        .iter()
        .find(|callable| callable.symbol == symbol);
    let owner = callable
        .and_then(|callable| callable.owner.as_ref())
        .or_else(|| {
            plan.modules
                .iter()
                .flat_map(|module| &module.declarations)
                .find(|declaration| {
                    declaration.get("name").and_then(Value::as_str) == Some(owner_symbol)
                })
        });
    let mut candidates = Vec::new();
    if let Some(callable) = callable {
        collect_clause_candidates(&callable.declaration, kind, numeric, &mut candidates);
        if kind == "invariant"
            && let Some(invariants) = callable
                .owner
                .as_ref()
                .and_then(|owner| owner.get("invariants"))
        {
            collect_clause_candidates(invariants, kind, numeric, &mut candidates);
        }
    } else {
        let owner =
            owner.ok_or_else(|| format!("no canonical declaration owns `{symbol}:{clause_id}`"))?;
        let scope = if kind == "invariant" {
            owner.get("invariants")
        } else {
            owner.get("init")
        }
        .ok_or_else(|| format!("no canonical declaration owns `{symbol}:{clause_id}`"))?;
        collect_clause_candidates(scope, kind, numeric, &mut candidates);
    }
    candidates.sort_by_key(|value| serde_json::to_string(value).unwrap_or_default());
    candidates.dedup();
    match candidates.as_slice() {
        [span] => Ok(span.clone()),
        [] => Err(format!(
            "canonical Rust clause `{symbol}:{clause_id}` has no source span"
        )),
        _ => Err(format!(
            "canonical Rust clause `{symbol}:{clause_id}` has ambiguous source spans"
        )),
    }
}

fn collect_clause_candidates(value: &Value, kind: &str, id: u64, candidates: &mut Vec<Value>) {
    match value {
        Value::Object(object) => {
            let matches = if kind == "invariant" {
                object.get("kind").is_none()
                    && object.get("clause_id").and_then(Value::as_u64) == Some(id)
                    && object.get("expression").is_some()
                    && object.get("span").is_some()
            } else {
                object.get("kind").and_then(Value::as_str) == Some(kind)
                    && object.get("clause_id").and_then(Value::as_u64) == Some(id)
            };
            if matches && let Some(span) = object.get("span") {
                candidates.push(span.clone());
            }
            for child in object.values() {
                collect_clause_candidates(child, kind, id, candidates);
            }
        }
        Value::Array(values) => {
            for child in values {
                collect_clause_candidates(child, kind, id, candidates);
            }
        }
        _ => {}
    }
}

fn observation_aliases(symbol: &str) -> BTreeSet<String> {
    let mut aliases = BTreeSet::from([symbol.to_owned()]);
    if let Some(owner) = symbol.strip_suffix(".init") {
        aliases.insert(owner.to_owned());
    }
    aliases
}

fn coverage_key(symbol: &str, clause_id: &str) -> (String, u8, u64, String) {
    let (kind, id) = clause_id.split_once(':').unwrap_or((clause_id, "0"));
    let order = match kind {
        "requires" => 0,
        "ensures" => 1,
        "error" => 2,
        "modifies" => 3,
        "invariant" => 4,
        _ => 5,
    };
    (
        symbol.to_owned(),
        order,
        id.parse().unwrap_or_default(),
        if kind == "modifies" {
            id.to_owned()
        } else {
            String::new()
        },
    )
}

fn required_event_string<'a>(event: &'a Value, field: &str) -> Result<&'a str, String> {
    event
        .get(field)
        .and_then(Value::as_str)
        .ok_or_else(|| format!("Rust evidence field `{field}` is not a string"))
}

fn required_event_u32(event: &Value, field: &str) -> Result<u32, String> {
    event
        .get(field)
        .and_then(Value::as_u64)
        .and_then(|value| u32::try_from(value).ok())
        .ok_or_else(|| format!("Rust evidence field `{field}` is not u32"))
}
