use super::types::*;
use serde_json::Value;

pub(crate) fn render_expression_contextual(
    e: &Value,
    module: Option<&str>,
) -> Result<String, String> {
    let r = |k: &str| render_expression_contextual(&e[k], module);
    Ok(match text(e, "kind")? {
        "literal" => render_value_contextual(&e["value"], e.get("type"), module)?,
        "parameter_ref" => escape_identifier(local_name(text(e, "symbol")?))?,
        "binding_ref" => format!("*{}", escape_identifier(local_name(text(e, "symbol")?))?),
        "constant_ref" => {
            let path = render_canonical_symbol(text(e, "symbol")?, module)?;
            if e["type"]["kind"] == "primitive"
                && matches!(
                    e["type"]["name"].as_str(),
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
                )
            {
                path
            } else {
                format!("*{path}")
            }
        }
        "enum_singleton_ref" => render_canonical_symbol(text(e, "symbol")?, module)?,
        "rust_synthetic" => text(e, "code")?.into(),
        "self_ref" => "self".into(),
        "result_ref" => "__cott_result".into(),
        "old_state_field" => format!(
            "__cott_old_{}",
            internal_name(local_name(text(e, "field")?))
        ),
        "field" => format!(
            "*({}).{}()",
            r("base")?,
            escape_identifier(&format!("get_{}", text(e, "name")?))?
        ),
        "len" => {
            if e["value"]["type"]["kind"] == "tuple" {
                return Ok(format!(
                    "{{let _=&({});{}usize}}",
                    r("value")?,
                    items(&e["value"]["type"], "items")?.len()
                ));
            }
            if e["value"]["type"]["name"] == "str" {
                format!("({}).chars().count()", r("value")?)
            } else {
                format!("({}).len()", r("value")?)
            }
        }
        "unary" => match text(e, "op")? {
            "not" => format!("!({})", r("operand")?),
            "plus" => r("operand")?,
            "minus" if integer(&e["type"]) => narrow(e, module)?,
            "minus" => format!("-({})", r("operand")?),
            o => return Err(format!("unknown unary {o}")),
        },
        "binary" => {
            let op = text(e, "op")?;
            if integer(&e["type"]) {
                narrow(e, module)?
            } else if matches!(e["type"]["name"].as_str(), Some("f32" | "f64")) {
                let width = text(&e["type"], "name")?;
                let token = match op {
                    "add" => "+",
                    "subtract" => "-",
                    "multiply" => "*",
                    "divide" => "/",
                    other => return Err(format!("invalid floating operation {other}")),
                };
                format!(
                    "crate::cott_runtime::finite_{width}(({}) {token} ({}))",
                    r("left")?,
                    r("right")?
                )
            } else {
                format!(
                    "({}) {} ({})",
                    r("left")?,
                    match op {
                        "add" => "+",
                        "subtract" => "-",
                        "multiply" => "*",
                        "divide" => "/",
                        "and" => "&&",
                        "or" => "||",
                        "implies" => return Ok(format!("!({}) || ({})", r("left")?, r("right")?)),
                        o => return Err(format!("unknown binary {o}")),
                    },
                    r("right")?
                )
            }
        }
        "comparison_chain" => {
            let operands = items(e, "operands")?;
            let ops = items(e, "operators")?;
            let mut clauses = Vec::new();
            for (i, op) in ops.iter().enumerate() {
                let a = operand(&operands[i], module)?;
                let b = operand(&operands[i + 1], module)?;
                let op = match op.as_str().ok_or("operator must be string")? {
                    "equal" => "==",
                    "not_equal" => "!=",
                    "less" => "<",
                    "less_equal" => "<=",
                    "greater" => ">",
                    "greater_equal" => ">=",
                    o => return Err(format!("unknown comparison {o}")),
                };
                clauses.push(format!("({a}) {op} ({b})"));
            }
            clauses.join(" && ")
        }
        "intrinsic" => intrinsic(e, module)?,
        "match" => render_guard(
            e,
            e.get("condition")
                .filter(|v| !v.is_null())
                .unwrap_or(&serde_json::json!({"kind":"rust_synthetic","code":"true"})),
            false,
            module,
        )?,
        "option_some" | "result_ok" | "result_err" => format!(
            "{}({})",
            match text(e, "kind")? {
                "option_some" => "Some",
                "result_ok" => "Ok",
                _ => "Err",
            },
            r("payload")?
        ),
        "construct" => {
            let args = items(e, "fields")?
                .iter()
                .map(|f| render_expression_contextual(&f["value"], module))
                .collect::<Result<Vec<_>, _>>()?;
            format!(
                "{}::new({})",
                render_canonical_symbol(text(e, "symbol")?, module)?,
                args.join(", ")
            )
        }
        "variant" => {
            let fields = items(e, "fields")?
                .iter()
                .map(|v| render_expression_contextual(v, module))
                .collect::<Result<Vec<_>, _>>()?;
            let n = render_canonical_symbol(text(e, "symbol")?, module)?;
            if fields.is_empty() {
                n
            } else {
                format!("{n}({})", fields.join(", "))
            }
        }
        "list" | "set" | "array" | "tuple" => {
            let args = items(e, "items")?
                .iter()
                .map(|v| render_expression_contextual(v, module))
                .collect::<Result<Vec<_>, _>>()?;
            match text(e, "kind")? {
                "list" => format!("vec![{}]", args.join(", ")),
                "set" => format!("crate::cott_runtime::Set::new(vec![{}])", args.join(", ")),
                "array" => format!("crate::cott_runtime::Array::new(vec![{}])", args.join(", ")),
                "tuple" if args.len() > 12 => format!(
                    "crate::cott_runtime::Tuple{}({})",
                    args.len(),
                    args.join(", ")
                ),
                _ => format!(
                    "({}{})",
                    args.join(", "),
                    if args.len() == 1 { "," } else { "" }
                ),
            }
        }
        "map" => format!(
            "crate::cott_runtime::Map::new(vec![{}])",
            items(e, "entries")?
                .iter()
                .map(|entry| Ok(format!(
                    "({}, {})",
                    render_expression_contextual(&entry["key"], module)?,
                    render_expression_contextual(&entry["value"], module)?
                )))
                .collect::<Result<Vec<_>, String>>()?
                .join(", ")
        ),
        "fixture_path" | "fixture_url" => format!(
            "crate::cott_runtime::__cott_{}(&{}, {})",
            text(e, "kind")?,
            escape_identifier(local_name(text(e, "fixture")?))?,
            rust_string(text(e, "path")?)
        ),
        "dyn" => format!("crate::cott_runtime::Dyn::new(Box::new({}))", r("value")?),
        other => return Err(format!("unsupported canonical expression {other}")),
    })
}
fn integer(ty: &Value) -> bool {
    matches!(
        ty.get("name").and_then(Value::as_str),
        Some("i8" | "i16" | "i32" | "i64" | "u8" | "u16" | "u32" | "u64")
    )
}
fn operand(e: &Value, module: Option<&str>) -> Result<String, String> {
    if integer(&e["type"]) || e["kind"] == "len" {
        math(e, module)
    } else if matches!(e["type"]["name"].as_str(), Some("f32" | "f64")) {
        Ok(format!(
            "({}) as f64",
            render_expression_contextual(e, module)?
        ))
    } else {
        render_expression_contextual(e, module)
    }
}
fn math(e: &Value, module: Option<&str>) -> Result<String, String> {
    if e["kind"] == "literal" && e["value"]["kind"] == "integer" {
        Ok(format!("{}i128", text(&e["value"], "value")?))
    } else if e["kind"] == "binary" && integer(&e["type"]) {
        let operation = match text(e, "op")? {
            "add" => "add",
            "subtract" => "sub",
            "multiply" => "mul",
            "divide" => "div",
            "remainder" => "rem",
            other => return Err(format!("unknown integer operation {other}")),
        };
        Ok(format!(
            "crate::cott_runtime::math_{operation}({}, {})",
            math(&e["left"], module)?,
            math(&e["right"], module)?
        ))
    } else if e["kind"] == "unary" && integer(&e["type"]) {
        let operand = math(&e["operand"], module)?;
        match text(e, "op")? {
            "plus" => Ok(operand),
            "minus" => Ok(format!("crate::cott_runtime::math_neg({operand})")),
            other => Err(format!("unknown integer unary {other}")),
        }
    } else {
        Ok(format!(
            "({}) as i128",
            render_expression_contextual(e, module)?
        ))
    }
}

fn narrow(e: &Value, module: Option<&str>) -> Result<String, String> {
    Ok(format!(
        "{}::try_from({}).unwrap_or_else(|_|crate::cott_runtime::violation(\"expression\",\"validation\",\"integer range\"))",
        render_type_contextual(&e["type"], module, None)?,
        math(e, module)?
    ))
}
fn intrinsic(e: &Value, module: Option<&str>) -> Result<String, String> {
    let args = items(e, "arguments")?
        .iter()
        .map(|v| render_expression_contextual(v, module))
        .collect::<Result<Vec<_>, _>>()?;
    let n = text(e, "name")?;
    let first = args.first().ok_or("intrinsic has no argument")?;
    let field = |key: &str| -> Result<String, String> {
        escape_identifier(&format!("get_{}", local_name(text(&e[key], "field")?)))
    };
    Ok(match n {
        "starts_with" | "ends_with" | "contains" => {
            let second = args.get(1).ok_or("missing second intrinsic argument")?;
            if e["arguments"][0]["type"]["name"] == "str" {
                format!("({first}).{n}(({second}).as_str())")
            } else {
                format!("({first}).{n}(&({second}))")
            }
        }
        "unique_by" => format!(
            "crate::cott_runtime::unique_by(&({first}), |v| v.{}())",
            field("selector")?
        ),
        "descending_by" => format!(
            "({first}).windows(2).all(|v| v[0].{}() >= v[1].{}())",
            field("selector")?,
            field("selector")?
        ),
        "any_blank_by" => format!(
            "({first}).iter().any(|v| v.{}().chars().all(crate::cott_runtime::white_space))",
            field("selector")?
        ),
        "unknown_dependency_by" | "self_dependency_by" | "cyclic_by" => format!(
            "crate::cott_runtime::{n}(&({first}), |v| v.{}(), |v| v.{}())",
            field("selector")?,
            field("dependencies")?
        ),
        "permutation_by" => format!(
            "crate::cott_runtime::permutation_by(&({first}), &({}), |v| v.{}())",
            args.get(1).ok_or("missing second argument")?,
            field("selector")?
        ),
        "dependency_ordered_by" => format!(
            "crate::cott_runtime::dependency_ordered_by(&({first}), &({}), |v| v.{}(), |v| v.{}())",
            args.get(1).ok_or("missing second argument")?,
            field("selector")?,
            field("dependencies")?
        ),
        o => return Err(format!("unknown intrinsic {o}")),
    })
}
pub(crate) fn pattern(p: &Value, module: Option<&str>) -> Result<String, String> {
    Ok(match text(p, "kind")? {
        "wildcard" => "_".into(),
        "binding" => escape_identifier(
            p.get("name")
                .and_then(Value::as_str)
                .unwrap_or(local_name(text(p, "symbol")?)),
        )?,
        "option_none" => "None".into(),
        "result_ok" | "result_err" | "option_some" | "enum" | "variant" => {
            let n = match text(p, "kind")? {
                "result_ok" => "Ok".into(),
                "result_err" => "Err".into(),
                "option_some" => "Some".into(),
                _ => render_canonical_symbol(text(p, "symbol")?, module)?,
            };
            let args = items(p, "arguments")?
                .iter()
                .map(|p| pattern(p, module))
                .collect::<Result<Vec<_>, _>>()?;
            if args.is_empty() {
                n
            } else {
                format!("{n}({})", args.join(", "))
            }
        }
        o => return Err(format!("unsupported pattern {o}")),
    })
}
pub(crate) fn render_guard(
    g: &Value,
    p: &Value,
    non_match: bool,
    module: Option<&str>,
) -> Result<String, String> {
    if matches!(g["pattern"]["kind"].as_str(), Some("wildcard" | "binding")) {
        return Ok(format!(
            "{{ let {} = &({}); {} }}",
            pattern(&g["pattern"], module)?,
            render_expression_contextual(&g["scrutinee"], module)?,
            render_expression_contextual(p, module)?
        ));
    }
    Ok(format!(
        "match &({}) {{ {} => {}, _ => {} }}",
        render_expression_contextual(&g["scrutinee"], module)?,
        pattern(&g["pattern"], module)?,
        render_expression_contextual(p, module)?,
        non_match
    ))
}
pub(crate) fn render_guarded_statement(
    g: Option<&Value>,
    statement: &str,
    module: Option<&str>,
) -> Result<String, String> {
    match g.filter(|g| !g.is_null()) {
        Some(g) if matches!(g["pattern"]["kind"].as_str(), Some("wildcard" | "binding")) => {
            Ok(format!(
                "{{ let {} = &({}); {statement} }}",
                pattern(&g["pattern"], module)?,
                render_expression_contextual(&g["scrutinee"], module)?
            ))
        }
        Some(g) => Ok(format!(
            "if let {} = &({}) {{ {statement} }}",
            pattern(&g["pattern"], module)?,
            render_expression_contextual(&g["scrutinee"], module)?
        )),
        None => Ok(statement.into()),
    }
}
pub(crate) fn render_condition(
    e: &Value,
    g: Option<&Value>,
    non_match: bool,
    module: Option<&str>,
) -> Result<String, String> {
    match g.filter(|g| !g.is_null()) {
        Some(g) => render_guard(g, e, non_match, module),
        None => render_expression_contextual(e, module),
    }
}
pub(crate) fn clause_label(clause: &Value) -> Result<String, String> {
    Ok(format!(
        "{}:{}",
        text(clause, "kind")?,
        clause["clause_id"].as_u64().ok_or("missing clause_id")?
    ))
}
