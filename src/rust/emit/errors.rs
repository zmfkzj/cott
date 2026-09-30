use super::*;

fn variant_pattern(plan: &RustPlan, symbol: &str) -> Result<String, String> {
    let owner = module_of(symbol).ok_or("error variant lacks owner")?;
    let declaration = plan
        .modules
        .iter()
        .flat_map(|m| &m.declarations)
        .find(|d| d.get("name").and_then(Value::as_str) == Some(owner))
        .ok_or_else(|| format!("unknown error enum {owner}"))?;
    let variant = list(declaration, "variants")
        .iter()
        .find(|v| v.get("name").and_then(Value::as_str).map(local_name) == Some(local_name(symbol)))
        .ok_or_else(|| format!("unknown error variant {symbol}"))?;
    let n = render_canonical_symbol(symbol, None)?;
    Ok(if list(variant, "fields").is_empty() {
        n
    } else {
        format!("{n}(..)")
    })
}
pub(super) fn before(
    plan: &RustPlan,
    d: &Value,
    symbol: &str,
    boundary: bool,
) -> Result<String, String> {
    if !checks_error_return(d.as_object().ok_or("callable is not object")?) {
        return Ok(String::new());
    }
    let conditional = clauses(d).iter().any(|c| {
        c["kind"] == "error"
            && (!c.get("guard").is_none_or(Value::is_null)
                || !c.get("when").is_none_or(Value::is_null))
    });
    let mut out = format!(
        "let {}__cott_expected_error: Option<usize> = None;\n",
        if conditional { "mut " } else { "" }
    );
    for (index, c) in clauses(d)
        .into_iter()
        .filter(|c| c["kind"] == "error")
        .enumerate()
    {
        if c.get("guard").is_none_or(Value::is_null) && c.get("when").is_none_or(Value::is_null) {
            continue;
        }
        variant_pattern(plan, text(c, "variant")?)?;
        let when = c
            .get("when")
            .filter(|v| !v.is_null())
            .cloned()
            .unwrap_or_else(|| serde_json::json!({"kind":"rust_synthetic","code":"true"}));
        let when = lower_expression(plan, &when, d)?;
        let guard = c
            .get("guard")
            .map(|g| lower_expression(plan, g, d))
            .transpose()?;
        let condition =
            super::super::expressions::render_condition(&when, guard.as_ref(), false, None)?;
        writeln!(out,"if crate::cott_runtime::__cott_validation_enabled({boundary}) && __cott_expected_error.is_none() && ({condition}) {{ __cott_expected_error = Some({index}); }}").unwrap();
    }
    let _ = symbol;
    Ok(out)
}
pub(super) fn after(
    plan: &RustPlan,
    d: &Value,
    symbol: &str,
    boundary: bool,
) -> Result<String, String> {
    if !checks_error_return(d.as_object().ok_or("callable is not object")?) {
        return Ok(String::new());
    }
    let mut arms = Vec::new();
    let mut bare = Vec::new();
    let mut observations = String::new();
    for (index, c) in clauses(d)
        .into_iter()
        .filter(|c| c["kind"] == "error")
        .enumerate()
    {
        let p = variant_pattern(plan, text(c, "variant")?)?;
        let label = rust_string(&clause_label(c)?);
        arms.push(format!("Some({index}) => {{ let passed=matches!(&__cott_result,Err({p}));crate::cott_runtime::__cott_check({},\"error\",{label},passed);passed }}",rust_string(symbol)));
        if c.get("guard").is_none_or(Value::is_null) && c.get("when").is_none_or(Value::is_null) {
            let variable = format!("__cott_allowed_error_{index}");
            writeln!(observations,"let {variable}=matches!(&__cott_result,Err({p}));if __cott_expected_error.is_none()&&{variable}{{crate::cott_runtime::__cott_check({},\"error\",{label},{variable});}}",rust_string(symbol)).unwrap();
            bare.push(variable);
        }
    }
    let allowed =
        if crate::ir::complete_errors(d.as_object().unwrap()) == Ok(true) || bare.is_empty() {
            "__cott_result.is_ok()".to_owned()
        } else {
            format!("__cott_result.is_ok() || {}", bare.join(" || "))
        };
    arms.push(format!("None => {allowed}"));
    arms.push("_ => false".into());
    Ok(format!(
        "if crate::cott_runtime::__cott_validation_enabled({boundary}) {{ {observations} crate::cott_runtime::__cott_check({}, \"error\", \"error-return\", match __cott_expected_error {{ {} }}); }}\n",
        rust_string(symbol),
        arms.join(", ")
    ))
}
