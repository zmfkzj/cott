use serde_json::Value;

use super::types::{
    KotlinTypeContext, const_witness_values, escape_identifier, kotlin_string, local_name,
    render_const_witness, render_named_arguments_contextual, render_qualified,
    render_type_contextual, render_value, trait_marker,
};

/// Kotlin type spelling for one expression tree. Contract clauses render without a context;
/// scenario steps carry the plan's emission context so every trait type in a scenario value
/// (a `Dyn` trait, a container item, a generic argument or a pattern binding) spells the
/// generated declaration, including its star-projected associated-type slots.
type Types<'a> = Option<&'a dyn KotlinTypeContext>;

pub(crate) fn render_expression(expression: &Value) -> Result<String, String> {
    render(expression, None)
}

/// Render a scenario step expression (call/initializer argument, method receiver, `data`
/// value or assertion) against the plan's emission type context.
pub(crate) fn render_scenario_expression(
    expression: &Value,
    types: &dyn KotlinTypeContext,
) -> Result<String, String> {
    render(expression, Some(types))
}

fn render_type(ty: &Value, types: Types) -> Result<String, String> {
    render_type_contextual(ty, None, types)
}

fn render(expression: &Value, types: Types) -> Result<String, String> {
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
            let type_arguments = render_named_arguments_contextual(object.get("type"), types)?;
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
            render(
                required(object.get("base"), "field expression.base")?,
                types
            )?,
            escape_identifier(required_string(
                object.get("name"),
                "field expression.name"
            )?)?
        )),
        "len" => Ok(format!(
            "cott_runtime.CottRuntime.length({})",
            render(
                required(object.get("value"), "len expression.value")?,
                types
            )?
        )),
        "intrinsic" => render_intrinsic(object, types),
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
        "unary" | "binary" if integer_type(object.get("type")) => {
            render_exact_integer(expression, object.get("type"), types)
        }
        "unary" => render_unary(expression, object, types),
        "binary" => render_binary(expression, object, types),
        "comparison_chain" => render_comparison_chain(object, types),
        "dyn" => {
            // `Dyn(value: ...)` exists only in scenario values, whose trait spelling needs the
            // generated associated-type slots; a context-free spelling would name the wrong
            // Kotlin type arity.
            let types = types
                .ok_or("Dyn value construction requires the scenario emission type context")?;
            let trait_ref = required(object.get("trait_ref"), "dyn expression.trait_ref")?;
            let dyn_type = required(object.get("type"), "dyn expression.type")?;
            if dyn_type.get("kind").and_then(Value::as_str) != Some("dyn")
                || dyn_type.get("trait") != Some(trait_ref)
            {
                return Err("dyn expression trait_ref does not match its type".to_owned());
            }
            let trait_type = render_type(trait_ref, Some(types))?;
            let value = render(
                required(object.get("value"), "dyn expression.value")?,
                Some(types),
            )?;
            Ok(format!(
                "cott_runtime.Dyn.of<{trait_type}>({value}, cott_runtime.{} as cott_runtime.CottTrait<{trait_type}>)",
                trait_marker(trait_ref)?
            ))
        }
        "construct" | "variant" | "option_some" | "result_ok" | "result_err" | "list" | "set"
        | "tuple" | "array" | "map" => render_scenario_value(kind, object, types),
        "match" => {
            let always = serde_json::json!({"kind": "kotlin_synthetic", "code": "true"});
            let condition = object.get("condition").filter(|value| !value.is_null());
            render_guard_in(expression, condition.unwrap_or(&always), false, types)
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
    types: Types,
) -> Result<String, String> {
    let ty = object.get("type");
    let items = |field: &str| -> Result<Vec<String>, String> {
        required_array(object.get(field), field)?
            .iter()
            .map(|item| {
                render(
                    item.get("value")
                        .filter(|_| field == "fields" && kind == "construct")
                        .unwrap_or(item),
                    types,
                )
            })
            .collect()
    };
    let element = |name: &str| -> Result<String, String> {
        render_type(
            required(
                ty.and_then(|ty| ty.get(name)),
                "scenario container element type",
            )?,
            types,
        )
    };
    match kind {
        // Explicit type arguments keep a data binding at its declared type:
        // Kotlin would otherwise infer `Box<Nothing>` from `Box(Nothing)`.
        "construct" | "variant" => {
            let type_arguments = render_named_arguments_contextual(ty, types)?;
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
            render(required(object.get("payload"), "payload")?, types)?
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
                        render(required(entry.get("key"), "map entry.key")?, types)?,
                        render(required(entry.get("value"), "map entry.value")?, types)?
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
    render_guard_in(guard, predicate, non_match, None)
}

fn render_guard_in(
    guard: &Value,
    predicate: &Value,
    non_match: bool,
    types: Types,
) -> Result<String, String> {
    let guard = guard
        .as_object()
        .ok_or_else(|| "canonical match guard must be an object".to_owned())?;
    let scrutinee = render(required(guard.get("scrutinee"), "guard.scrutinee")?, types)?;
    let (condition, bindings) = render_pattern(
        required(guard.get("pattern"), "guard.pattern")?,
        "_cottMatchValue",
        types,
    )?;
    let predicate = render(predicate, types)?;
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

fn render_intrinsic(
    object: &serde_json::Map<String, Value>,
    types: Types,
) -> Result<String, String> {
    let arguments = required_array(object.get("arguments"), "intrinsic expression.arguments")?
        .iter()
        .map(|argument| render_operand(argument, types))
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

/// An integer-typed arithmetic result in a value position (scenario call
/// argument, data, constructor field, container item, payload) takes the
/// exact Kotlin ABI type of its canonical integer type. The mathematical
/// result is range-checked instead of wrapped, so an out-of-range value is a
/// contract violation rather than a silently different argument.
fn render_exact_integer(
    expression: &Value,
    ty: Option<&Value>,
    types: Types,
) -> Result<String, String> {
    let ty = required(ty, "integer expression.type")?;
    let kind = match primitive_type(Some(ty)) {
        Some("i8") => "I8",
        Some("i16") => "I16",
        Some("i32") => "I32",
        Some("i64") => "I64",
        Some("u8") => "U8",
        Some("u16") => "U16",
        Some("u32") => "U32",
        Some("u64") => "U64",
        _ => return Err("exact integer expression requires an integer primitive type".to_owned()),
    };
    Ok(format!(
        "(cott_runtime.CottRuntime.intValue({}, cott_runtime.CottIntKind.{kind}) as {})",
        render_math_integer(expression, types)?,
        render_type(ty, types)?
    ))
}

/// Operands whose value is only observed by the runtime's canonical
/// comparison, intrinsic and pattern helpers keep integer arithmetic as
/// unbounded mathematical integers.
fn render_operand(expression: &Value, types: Types) -> Result<String, String> {
    if is_integer_arithmetic(expression) {
        render_math_integer(expression, types)
    } else {
        render(expression, types)
    }
}

fn is_integer_arithmetic(expression: &Value) -> bool {
    matches!(
        expression.get("kind").and_then(Value::as_str),
        Some("unary" | "binary")
    ) && integer_type(expression.get("type"))
}

/// Contract integer arithmetic is exact: every operand is a `BigInteger`.
/// An integer literal operand is its exact decimal, never the width-typed
/// literal, because a negated minimum such as `-2147483648` has an operand
/// outside its own type's range.
fn render_math_integer(expression: &Value, types: Types) -> Result<String, String> {
    let object = expression
        .as_object()
        .ok_or_else(|| "canonical contract expression must be an object".to_owned())?;
    match object.get("kind").and_then(Value::as_str) {
        Some("literal")
            if object
                .get("value")
                .and_then(|value| value.get("kind"))
                .and_then(Value::as_str)
                == Some("integer") =>
        {
            let value = required(object.get("value"), "literal expression.value")?;
            Ok(format!(
                "cott_runtime.CottRuntime.int({})",
                kotlin_string(required_string(value.get("value"), "integer value.value")?)
            ))
        }
        Some("unary") if is_integer_arithmetic(expression) => {
            let operand = render_math_integer(
                required(object.get("operand"), "unary expression.operand")?,
                types,
            )?;
            match required_string(object.get("op"), "unary expression.op")? {
                "plus" => Ok(operand),
                "minus" => Ok(format!("cott_runtime.CottRuntime.intNegate({operand})")),
                other => Err(format!("unsupported integer unary operator `{other}`")),
            }
        }
        Some("binary") if is_integer_arithmetic(expression) => {
            let method = match required_string(object.get("op"), "binary expression.op")? {
                "add" => "intAdd",
                "subtract" => "intSubtract",
                "multiply" => "intMultiply",
                "divide" => "euclideanDivide",
                "remainder" => "euclideanRemainder",
                other => return Err(format!("unsupported integer binary operator `{other}`")),
            };
            Ok(format!(
                "cott_runtime.CottRuntime.{method}({}, {})",
                render_math_integer(
                    required(object.get("left"), "binary expression.left")?,
                    types
                )?,
                render_math_integer(
                    required(object.get("right"), "binary expression.right")?,
                    types
                )?
            ))
        }
        _ => Ok(format!(
            "cott_runtime.CottRuntime.mathInt({})",
            render(expression, types)?
        )),
    }
}

fn render_unary(
    expression: &Value,
    object: &serde_json::Map<String, Value>,
    types: Types,
) -> Result<String, String> {
    let operand = render(
        required(object.get("operand"), "unary expression.operand")?,
        types,
    )?;
    let op = required_string(object.get("op"), "unary expression.op")?;
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
    types: Types,
) -> Result<String, String> {
    let left = required(object.get("left"), "binary expression.left")?;
    let right = required(object.get("right"), "binary expression.right")?;
    let op = required_string(object.get("op"), "binary expression.op")?;
    if op == "remainder" {
        return Ok(format!(
            "cott_runtime.CottRuntime.euclideanRemainder({}, {})",
            render_math_integer(left, types)?,
            render_math_integer(right, types)?
        ));
    }
    let left = render(left, types)?;
    let right = render(right, types)?;
    if matches!(op, "or" | "and") {
        return Ok(format!(
            "(({left}) {} ({right}))",
            if op == "or" { "||" } else { "&&" }
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

fn render_comparison_chain(
    object: &serde_json::Map<String, Value>,
    types: Types,
) -> Result<String, String> {
    let operands = required_array(object.get("operands"), "comparison expression.operands")?
        .iter()
        .map(|operand| render_operand(operand, types))
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

fn render_pattern(
    pattern: &Value,
    value: &str,
    types: Types,
) -> Result<(String, Vec<String>), String> {
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
                render_type(required(object.get("type"), "binding pattern.type")?, types)?
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
                let (condition, nested) = render_pattern(argument, &field, types)?;
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
