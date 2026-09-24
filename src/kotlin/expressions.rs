use serde_json::Value;

use super::types::{
    const_witness_values, escape_identifier, kotlin_string, local_name, render_const_witness,
    render_named_arguments, render_qualified, render_type, render_value,
};

pub(crate) fn render_expression(expression: &Value) -> Result<String, String> {
    let object = expression
        .as_object()
        .ok_or_else(|| "canonical contract expression must be an object".to_owned())?;
    let kind = required_string(object.get("kind"), "expression.kind")?;
    match kind {
        "literal" => render_value(
            required(object.get("value"), "literal expression.value")?,
            object.get("type"),
        ),
        "parameter_ref" | "binding_ref" => escape_identifier(local_name(required_string(
            object.get("symbol"),
            "reference expression.symbol",
        )?)),
        "kotlin_synthetic" => {
            Ok(required_string(object.get("code"), "synthetic Kotlin expression.code")?.to_owned())
        }
        "constant_ref" => render_qualified(required_string(
            object.get("symbol"),
            "constant reference.symbol",
        )?),
        "enum_singleton_ref" => {
            let variant = render_qualified(required_string(
                object.get("symbol"),
                "enum singleton reference.symbol",
            )?)?;
            let type_arguments = render_named_arguments(object.get("type"))?;
            let constructor = if type_arguments.is_empty() {
                variant
            } else {
                format!("{variant}<{}>", type_arguments.join(", "))
            };
            let arguments = object
                .get("type")
                .and_then(|ty| ty.get("args"))
                .and_then(Value::as_array)
                .map(Vec::as_slice)
                .unwrap_or_default();
            if arguments.is_empty() {
                Ok(constructor)
            } else {
                let witnesses = arguments
                    .iter()
                    .filter(|argument| {
                        argument.get("kind").and_then(Value::as_str) == Some("const")
                    })
                    .map(|argument| {
                        render_const_witness(required(
                            argument.get("value"),
                            "enum singleton const argument.value",
                        )?)
                    })
                    .collect::<Result<Vec<_>, _>>()?;
                Ok(format!("{constructor}({})", witnesses.join(", ")))
            }
        }
        "self_ref" => Ok("this".to_owned()),
        "result_ref" => Ok("_cottResult".to_owned()),
        "old_state_field" => Ok(format!(
            "_cottOld_{}",
            internal_name(local_name(required_string(
                object.get("field"),
                "old state field.field",
            )?))
        )),
        "field" => Ok(format!(
            "({}).{}",
            render_expression(required(object.get("base"), "field expression.base")?)?,
            escape_identifier(required_string(
                object.get("name"),
                "field expression.name"
            )?)?
        )),
        "len" => Ok(format!(
            "cott_runtime.CottRuntime.length({})",
            render_expression(required(object.get("value"), "len expression.value")?)?
        )),
        "intrinsic" => render_intrinsic(object),
        "fixture_path" | "fixture_url" => {
            let fixture = escape_identifier(local_name(required_string(
                object.get("fixture"),
                "fixture expression.fixture",
            )?))?;
            let path = kotlin_string(required_string(
                object.get("path"),
                "fixture expression.path",
            )?);
            Ok(format!(
                "cott_runtime.CottRuntime.{}({fixture}, {path})",
                if kind == "fixture_path" {
                    "fixturePath"
                } else {
                    "fixtureUrl"
                }
            ))
        }
        "unary" => render_unary(expression, object),
        "binary" => render_binary(expression, object),
        "comparison_chain" => render_comparison_chain(object),
        "construct" | "variant" | "option_some" | "result_ok" | "result_err" | "list" | "set"
        | "tuple" | "array" | "map" => render_scenario_value(kind, object),
        "match" => {
            let always = serde_json::json!({"kind": "kotlin_synthetic", "code": "true"});
            let condition = object.get("condition").filter(|value| !value.is_null());
            render_guard(expression, condition.unwrap_or(&always), false)
        }
        other => Err(format!(
            "unsupported canonical contract expression kind `{other}`"
        )),
    }
}

/// Scenario values run the generated canonical constructors, so every
/// ABI check and struct invariant applies exactly as for facade callers.
fn render_scenario_value(
    kind: &str,
    object: &serde_json::Map<String, Value>,
) -> Result<String, String> {
    let ty = object.get("type");
    let items = |field: &str| -> Result<Vec<String>, String> {
        required_array(object.get(field), field)?
            .iter()
            .map(|item| {
                render_expression(
                    item.get("value")
                        .filter(|_| field == "fields" && kind == "construct")
                        .unwrap_or(item),
                )
            })
            .collect()
    };
    let element = |name: &str| -> Result<String, String> {
        render_type(required(
            ty.and_then(|ty| ty.get(name)),
            "scenario container element type",
        )?)
    };
    match kind {
        // Explicit type arguments keep a data binding at its declared type:
        // Kotlin would otherwise infer `Box<Nothing>` from `Box(Nothing)`.
        "construct" | "variant" => {
            let type_arguments = render_named_arguments(ty)?;
            let mut fields = items("fields")?;
            fields.extend(const_witness_values(ty)?);
            let constructor = render_qualified(required_string(
                object.get("symbol"),
                "scenario value.symbol",
            )?)?;
            Ok(if type_arguments.is_empty() {
                format!("{constructor}({})", fields.join(", "))
            } else {
                format!(
                    "{constructor}<{}>({})",
                    type_arguments.join(", "),
                    fields.join(", ")
                )
            })
        }
        "option_some" | "result_ok" | "result_err" => Ok(format!(
            "cott_runtime.{}({})",
            match kind {
                "option_some" => "Some",
                "result_ok" => "Ok",
                _ => "Err",
            },
            render_expression(required(object.get("payload"), "payload")?)?
        )),
        "list" | "set" => Ok(format!(
            "cott_runtime.CottRuntime.{}(listOf<{}>({}))",
            if kind == "list" {
                "snapshotList"
            } else {
                "snapshotSet"
            },
            element("item")?,
            items("items")?.join(", ")
        )),
        "array" => Ok(format!(
            "cott_runtime.CottRuntime.snapshotArray(listOf<{}>({}), {})",
            element("item")?,
            items("items")?.join(", "),
            render_const_witness(required(
                ty.and_then(|ty| ty.get("length")),
                "array length"
            )?)?
        )),
        "tuple" => {
            let values = items("items")?;
            Ok(format!(
                "cott_runtime.CottTuple{}({})",
                values.len(),
                values.join(", ")
            ))
        }
        _ => {
            let entries = required_array(object.get("entries"), "map.entries")?
                .iter()
                .map(|entry| {
                    Ok(format!(
                        "{} to {}",
                        render_expression(required(entry.get("key"), "map entry.key")?)?,
                        render_expression(required(entry.get("value"), "map entry.value")?)?
                    ))
                })
                .collect::<Result<Vec<_>, String>>()?;
            Ok(format!(
                "cott_runtime.CottRuntime.snapshotMap(linkedMapOf<{}, {}>({}))",
                element("key")?,
                element("value")?,
                entries.join(", ")
            ))
        }
    }
}

pub(crate) fn render_guard(
    guard: &Value,
    predicate: &Value,
    non_match: bool,
) -> Result<String, String> {
    let guard = guard
        .as_object()
        .ok_or_else(|| "canonical match guard must be an object".to_owned())?;
    let scrutinee = render_expression(required(guard.get("scrutinee"), "guard.scrutinee")?)?;
    let (condition, bindings) = render_pattern(
        required(guard.get("pattern"), "guard.pattern")?,
        "_cottMatchValue",
    )?;
    let predicate = render_expression(predicate)?;
    let fallback = if non_match { "true" } else { "false" };
    let binding_lines = if bindings.is_empty() {
        String::new()
    } else {
        format!(" {};", bindings.join("; "))
    };
    Ok(format!(
        "run {{ val _cottMatchValue = {scrutinee}; if ({condition}) {{{binding_lines} {predicate} }} else {fallback} }}"
    ))
}

pub(crate) fn render_condition(
    expression: &Value,
    guard: Option<&Value>,
    non_match: bool,
) -> Result<String, String> {
    match guard.filter(|value| !value.is_null()) {
        Some(guard) => render_guard(guard, expression, non_match),
        None => render_expression(expression),
    }
}

pub(crate) fn render_span(value: Option<&Value>) -> Result<String, String> {
    let Some(span) = value.and_then(Value::as_object) else {
        return Ok("null".to_owned());
    };
    let coordinate = |name: &str| {
        span.get(name)
            .and_then(Value::as_u64)
            .ok_or_else(|| format!("canonical span.{name} must be an unsigned integer"))
    };
    Ok(format!(
        "cott_runtime.CottSpan(startByte = {}, endByte = {}, startLine = {}, startColumn = {}, endLine = {}, endColumn = {})",
        coordinate("start_byte")?,
        coordinate("end_byte")?,
        coordinate("start_line")?,
        coordinate("start_column")?,
        coordinate("end_line")?,
        coordinate("end_column")?,
    ))
}

pub(crate) fn clause_label(clause: &Value) -> Result<String, String> {
    Ok(format!(
        "{}:{}",
        clause
            .get("kind")
            .and_then(Value::as_str)
            .ok_or_else(|| "canonical contract clause is missing kind".to_owned())?,
        clause
            .get("clause_id")
            .and_then(Value::as_u64)
            .ok_or_else(|| "canonical contract clause is missing clause_id".to_owned())?
    ))
}

fn render_intrinsic(object: &serde_json::Map<String, Value>) -> Result<String, String> {
    let arguments = required_array(object.get("arguments"), "intrinsic expression.arguments")?
        .iter()
        .map(render_expression)
        .collect::<Result<Vec<_>, _>>()?;
    let first = arguments
        .first()
        .ok_or_else(|| "contract intrinsic must have a first argument".to_owned())?;
    let second = arguments.get(1);
    let name = required_string(object.get("name"), "intrinsic expression.name")?;
    match name {
        "starts_with" | "ends_with" | "contains" => {
            let second =
                second.ok_or_else(|| format!("contract intrinsic `{name}` needs two arguments"))?;
            let method = match name {
                "starts_with" => "startsWith",
                "ends_with" => "endsWith",
                _ => "contains",
            };
            Ok(format!(
                "cott_runtime.CottRuntime.{method}({first}, {second})"
            ))
        }
        "unique_by" | "descending_by" | "any_blank_by" => {
            let (owner, field) = intrinsic_selector(object, name, "selector")?;
            let method = match name {
                "unique_by" => "uniqueBy",
                "descending_by" => "descendingBy",
                _ => "anyBlankBy",
            };
            Ok(format!(
                "cott_runtime.CottRuntime.{method}({first}, {}, {})",
                kotlin_string(owner),
                kotlin_string(field)
            ))
        }
        "unknown_dependency_by" | "self_dependency_by" | "cyclic_by" => {
            let (owner, key) = intrinsic_selector(object, name, "selector")?;
            let (_, dependencies) = intrinsic_selector(object, name, "dependencies")?;
            let method = match name {
                "unknown_dependency_by" => "unknownDependencyBy",
                "self_dependency_by" => "selfDependencyBy",
                _ => "cyclicBy",
            };
            Ok(format!(
                "cott_runtime.CottRuntime.{method}({first}, {}, {}, {})",
                kotlin_string(owner),
                kotlin_string(key),
                kotlin_string(dependencies)
            ))
        }
        "permutation_by" | "dependency_ordered_by" => {
            let second =
                second.ok_or_else(|| format!("contract intrinsic `{name}` needs two arguments"))?;
            let (owner, key) = intrinsic_selector(object, name, "selector")?;
            if name == "permutation_by" {
                return Ok(format!(
                    "cott_runtime.CottRuntime.permutationBy({first}, {second}, {}, {})",
                    kotlin_string(owner),
                    kotlin_string(key)
                ));
            }
            let (_, dependencies) = intrinsic_selector(object, name, "dependencies")?;
            Ok(format!(
                "cott_runtime.CottRuntime.dependencyOrderedBy({first}, {second}, {}, {}, {})",
                kotlin_string(owner),
                kotlin_string(key),
                kotlin_string(dependencies)
            ))
        }
        other => Err(format!(
            "unsupported canonical contract intrinsic `{other}`"
        )),
    }
}

/// One canonical `{owner, field}` selector of a list intrinsic. The canonical
/// field is the qualified symbol `owner.field`; `cottField` takes the bare name.
fn intrinsic_selector<'a>(
    object: &'a serde_json::Map<String, Value>,
    name: &str,
    key: &str,
) -> Result<(&'a str, &'a str), String> {
    let selector = object
        .get(key)
        .and_then(Value::as_object)
        .ok_or_else(|| format!("contract intrinsic `{name}` requires {key}"))?;
    Ok((
        required_string(selector.get("owner"), "intrinsic selector.owner")?,
        local_name(required_string(
            selector.get("field"),
            "intrinsic selector.field",
        )?),
    ))
}

fn render_unary(
    expression: &Value,
    object: &serde_json::Map<String, Value>,
) -> Result<String, String> {
    let operand = render_expression(required(object.get("operand"), "unary expression.operand")?)?;
    let op = required_string(object.get("op"), "unary expression.op")?;
    if integer_type(expression.get("type")) {
        return match op {
            "plus" => Ok(format!("cott_runtime.CottRuntime.mathInt({operand})")),
            "minus" => Ok(format!(
                "cott_runtime.CottRuntime.intNegate(cott_runtime.CottRuntime.mathInt({operand}))"
            )),
            other => Err(format!("unsupported integer unary operator `{other}`")),
        };
    }
    match op {
        "not" => Ok(format!("!({operand})")),
        "plus" => Ok(operand),
        "minus" if primitive_type(expression.get("type")) == Some("f32") => {
            Ok(format!("cott_runtime.CottRuntime.f32Negate({operand})"))
        }
        "minus" if primitive_type(expression.get("type")) == Some("f64") => {
            Ok(format!("cott_runtime.CottRuntime.f64Negate({operand})"))
        }
        "minus" => Ok(format!("-({operand})")),
        other => Err(format!("unsupported canonical unary operator `{other}`")),
    }
}

fn render_binary(
    expression: &Value,
    object: &serde_json::Map<String, Value>,
) -> Result<String, String> {
    let left = render_expression(required(object.get("left"), "binary expression.left")?)?;
    let right = render_expression(required(object.get("right"), "binary expression.right")?)?;
    let op = required_string(object.get("op"), "binary expression.op")?;
    if matches!(op, "or" | "and") {
        return Ok(format!(
            "(({left}) {} ({right}))",
            if op == "or" { "||" } else { "&&" }
        ));
    }
    if integer_type(expression.get("type")) {
        let method = match op {
            "add" => "intAdd",
            "subtract" => "intSubtract",
            "multiply" => "intMultiply",
            "divide" => "euclideanDivide",
            "remainder" => "euclideanRemainder",
            other => return Err(format!("unsupported integer binary operator `{other}`")),
        };
        return Ok(format!(
            "cott_runtime.CottRuntime.{method}(cott_runtime.CottRuntime.mathInt({left}), cott_runtime.CottRuntime.mathInt({right}))"
        ));
    }
    if op == "remainder" {
        return Ok(format!(
            "cott_runtime.CottRuntime.euclideanRemainder(cott_runtime.CottRuntime.mathInt({left}), cott_runtime.CottRuntime.mathInt({right}))"
        ));
    }
    if let Some(prefix) = match primitive_type(expression.get("type")) {
        Some("f32") => Some("f32"),
        Some("f64") => Some("f64"),
        _ => None,
    } {
        let suffix = match op {
            "add" => "Add",
            "subtract" => "Subtract",
            "multiply" => "Multiply",
            "divide" => "Divide",
            other => return Err(format!("unsupported floating binary operator `{other}`")),
        };
        return Ok(format!(
            "cott_runtime.CottRuntime.{prefix}{suffix}({left}, {right})"
        ));
    }
    let token = match op {
        "add" => "+",
        "subtract" => "-",
        "multiply" => "*",
        "divide" => "/",
        other => return Err(format!("unsupported canonical binary operator `{other}`")),
    };
    Ok(format!("(({left}) {token} ({right}))"))
}

fn render_comparison_chain(object: &serde_json::Map<String, Value>) -> Result<String, String> {
    let operands = required_array(object.get("operands"), "comparison expression.operands")?
        .iter()
        .map(render_expression)
        .collect::<Result<Vec<_>, _>>()?;
    let operators = required_array(object.get("operators"), "comparison expression.operators")?;
    if operands.len() != operators.len() + 1 {
        return Err("comparison chain operands/operators arity mismatch".to_owned());
    }
    let mut comparisons = Vec::with_capacity(operators.len());
    for (index, operator) in operators.iter().enumerate() {
        let operator = operator
            .as_str()
            .ok_or_else(|| format!("comparison operator {index} must be a string"))?;
        let left = &operands[index];
        let right = &operands[index + 1];
        comparisons.push(match operator {
            "equal" => format!("cott_runtime.CottRuntime.canonicalEqual({left}, {right})"),
            "not_equal" => format!("!cott_runtime.CottRuntime.canonicalEqual({left}, {right})"),
            "less" | "less_equal" | "greater" | "greater_equal" => {
                let token = match operator {
                    "less" => "<",
                    "less_equal" => "<=",
                    "greater" => ">",
                    _ => ">=",
                };
                format!("cott_runtime.CottRuntime.canonicalCompare({left}, {right}) {token} 0")
            }
            other => {
                return Err(format!(
                    "unsupported canonical comparison operator `{other}`"
                ));
            }
        });
    }
    Ok(if comparisons.is_empty() {
        "true".to_owned()
    } else {
        format!("({})", comparisons.join(" && "))
    })
}

fn render_pattern(pattern: &Value, value: &str) -> Result<(String, Vec<String>), String> {
    let object = pattern
        .as_object()
        .ok_or_else(|| "canonical contract pattern must be an object".to_owned())?;
    let kind = required_string(object.get("kind"), "pattern.kind")?;
    match kind {
        "wildcard" => Ok(("true".to_owned(), Vec::new())),
        "binding" => Ok((
            "true".to_owned(),
            vec![format!(
                "val {} = ({value} as {})",
                escape_identifier(
                    object
                        .get("name")
                        .and_then(Value::as_str)
                        .or_else(|| object.get("symbol").and_then(Value::as_str).map(local_name))
                        .ok_or_else(|| "binding pattern is missing name".to_owned())?
                )?,
                render_type(required(object.get("type"), "binding pattern.type")?)?
            )],
        )),
        "result_ok" | "result_err" | "option_some" | "option_none" | "enum" | "variant" => {
            let symbol = required_string(object.get("symbol"), "variant pattern.symbol")?;
            let mut conditions = Vec::new();
            let payload = match kind {
                "result_ok" => {
                    conditions.push(format!(
                        "cott_runtime.CottRuntime.resultOk({value}) is cott_runtime.Some<*>"
                    ));
                    format!(
                        "(cott_runtime.CottRuntime.resultOk({value}) as cott_runtime.Some<*>).value"
                    )
                }
                "result_err" => {
                    conditions.push(format!(
                        "cott_runtime.CottRuntime.resultErr({value}) is cott_runtime.Some<*>"
                    ));
                    format!(
                        "(cott_runtime.CottRuntime.resultErr({value}) as cott_runtime.Some<*>).value"
                    )
                }
                "option_some" => {
                    conditions.push(format!(
                        "cott_runtime.CottRuntime.optionSome({value}) is cott_runtime.Some<*>"
                    ));
                    format!(
                        "(cott_runtime.CottRuntime.optionSome({value}) as cott_runtime.Some<*>).value"
                    )
                }
                "option_none" => {
                    conditions.push(format!("{value} === cott_runtime.Nothing"));
                    String::new()
                }
                _ => {
                    conditions.push(format!(
                        "cott_runtime.CottRuntime.variant({value}, {}) is cott_runtime.Some<*>",
                        kotlin_string(symbol)
                    ));
                    format!(
                        "(cott_runtime.CottRuntime.variant({value}, {}) as cott_runtime.Some<cott_runtime.CottList<kotlin.Any?>>).value",
                        kotlin_string(symbol)
                    )
                }
            };
            let mut bindings = Vec::new();
            for (index, argument) in required_array(object.get("arguments"), "pattern.arguments")?
                .iter()
                .enumerate()
            {
                if kind == "option_none" {
                    return Err("Option.Nothing pattern cannot contain arguments".to_owned());
                }
                let field = if matches!(kind, "result_ok" | "result_err" | "option_some") {
                    payload.clone()
                } else {
                    format!("{payload}[{index}]")
                };
                let (condition, nested) = render_pattern(argument, &field)?;
                conditions.push(condition);
                bindings.extend(nested);
            }
            Ok((format!("({})", conditions.join(" && ")), bindings))
        }
        other => Err(format!("unsupported canonical pattern kind `{other}`")),
    }
}

fn integer_type(value: Option<&Value>) -> bool {
    value
        .and_then(Value::as_object)
        .filter(|ty| ty.get("kind").and_then(Value::as_str) == Some("primitive"))
        .and_then(|ty| ty.get("name"))
        .and_then(Value::as_str)
        .is_some_and(|name| {
            matches!(
                name,
                "i8" | "i16" | "i32" | "i64" | "u8" | "u16" | "u32" | "u64"
            )
        })
}

fn primitive_type(value: Option<&Value>) -> Option<&str> {
    value
        .and_then(Value::as_object)
        .filter(|ty| ty.get("kind").and_then(Value::as_str) == Some("primitive"))
        .and_then(|ty| ty.get("name"))
        .and_then(Value::as_str)
}

fn internal_name(name: &str) -> String {
    let mut rendered = String::new();
    for byte in name.bytes() {
        if byte.is_ascii_alphanumeric() || byte == b'_' {
            rendered.push(byte as char);
        } else {
            use std::fmt::Write as _;
            write!(rendered, "_{byte:02x}").expect("writing to a String cannot fail");
        }
    }
    if rendered.is_empty() {
        "value".to_owned()
    } else {
        rendered
    }
}

fn required<'a>(value: Option<&'a Value>, field: &str) -> Result<&'a Value, String> {
    value.ok_or_else(|| format!("missing canonical `{field}`"))
}

fn required_string<'a>(value: Option<&'a Value>, field: &str) -> Result<&'a str, String> {
    required(value, field)?
        .as_str()
        .ok_or_else(|| format!("canonical `{field}` must be a string"))
}

fn required_array<'a>(value: Option<&'a Value>, field: &str) -> Result<&'a Vec<Value>, String> {
    required(value, field)?
        .as_array()
        .ok_or_else(|| format!("canonical `{field}` must be an array"))
}
