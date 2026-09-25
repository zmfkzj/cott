//! A presentation-only projection of the *selected, resolved* intent context.
//! Never look declarations up again: an impl in that context may contain only a
//! selected method subset. Never interpret spans: inherited/applied clauses may
//! still carry a rule's diagnostic location after semantic substitution.

use std::fmt::Write as _;

use serde_json::{Map, Value};

pub(crate) const FORMAT: &str = "Compact semantic view: declaration objects retain the selected resolved contract, not authored source snippets. Expression and pattern strings use canonical kind(field=value,...) constructors; nested constructors and ordered lists preserve structure, and strings use JSON quoting. Every expression carries its resolved type; reference and binding symbols are fully qualified identities. Integer value strings are exact decimal integers, f32/f64 bits are exact IEEE-754 hexadecimal bits (including signed zero), and enum variant/symbol fields identify the exact variant. Types, const arguments, values, operators and intrinsic names retain their canonical meanings, not target-language arithmetic. A guard matches its scrutinee against its pattern and binds the pattern symbols for the sibling expression/when predicate: unmatched requires/ensures/invariants impose no predicate, and unmatched error guards do not trigger. Declaration order and clause_id/identity metadata are retained; only diagnostic spans, source order and documentation are omitted.\n";

/// Compact only the supplied closure, without changing it or its fingerprint.
pub fn scoped_declarations(selected: &Value) -> Result<Value, String> {
    let modules = selected
        .as_object()
        .ok_or_else(|| "intent context declarations must be an object".to_owned())?;
    let mut requirements = false;
    for (module, value) in modules {
        requirements |= value
            .get("declarations")
            .and_then(Value::as_array)
            .ok_or_else(|| format!("module `{module}` declarations must be an array"))?
            .iter()
            .any(requirement);
    }
    if !requirements {
        return compact(selected);
    }
    // Requirement statements are normative prose rendered in CURRENT INTENT, never formal
    // source constraints; keep them out of the authoritative formal view.
    let mut formal = selected.clone();
    for value in formal.as_object_mut().into_iter().flat_map(Map::values_mut) {
        if let Some(Value::Array(declarations)) = value.get_mut("declarations") {
            declarations.retain(|declaration| !requirement(declaration));
        }
    }
    compact(&formal)
}

fn requirement(declaration: &Value) -> bool {
    declaration.get("kind").and_then(Value::as_str) == Some("requirement")
}

/// Render the presentation projection as minified JSON for prompt embedding.
///
/// This changes only JSON whitespace; the selected context and its fingerprint
/// input remain untouched.
pub fn render_scoped_declarations(selected: &Value) -> Result<String, String> {
    serde_json::to_string(&scoped_declarations(selected)?).map_err(|error| error.to_string())
}

fn diagnostic(key: &str) -> bool {
    matches!(key, "span" | "source_order" | "doc")
}

fn compact(value: &Value) -> Result<Value, String> {
    match value {
        Value::Array(values) => values
            .iter()
            .map(compact)
            .collect::<Result<Vec<_>, _>>()
            .map(Value::Array),
        Value::Object(object) => {
            // `reference` and `type` distinguish canonical expressions from
            // declarations, values, const arithmetic and refinement wrappers.
            if object.contains_key("reference") && object.contains_key("type") {
                return rendered(value, Form::Expression);
            }
            let mut output = Map::new();
            for (key, child) in object {
                if diagnostic(key) {
                    continue;
                }
                let projected = if child.is_null() {
                    Value::Null
                } else if object.get("kind").and_then(Value::as_str) == Some("json")
                    && key == "value"
                {
                    // User JsonValue object keys are data, even `span` or `doc`.
                    child.clone()
                } else {
                    match key.as_str() {
                        "expression" | "condition" | "when" | "scrutinee" => {
                            rendered(child, Form::Expression)?
                        }
                        "pattern" => rendered(child, Form::Pattern)?,
                        // A refinement can be an expression OR a projection's
                        // wrapper carrying identity/clause_id and an expression.
                        "refinement"
                            if child.get("kind").is_some()
                                && child.get("expression").is_none()
                                && child.get("condition").is_none() =>
                        {
                            rendered(child, Form::Expression)?
                        }
                        _ => compact(child)?,
                    }
                };
                output.insert(key.clone(), projected);
            }
            Ok(Value::Object(output))
        }
        _ => Ok(value.clone()),
    }
}

// The compact grammar is lossless for semantic fields: kind(field=value,...),
// [ordered elements], and JSON scalars. Field names are canonical schema keys;
// no precedence, source spelling, inferred nominal names or float conversion is
// involved. These roles disambiguate e.g. type `named`, value `named`, pattern
// `enum`, and value `enum`. Raw JSON is never traversed as compiler metadata.
#[derive(Clone, Copy)]
enum Form {
    Expression,
    Type,
    Value,
    Pattern,
    Const,
    Generic,
    Reference,
    Selector,
    /// A selector key present only on some nodes of a kind.
    OptionalSelector,
    Member,
    Expressions,
    Types,
    Values,
    Patterns,
    Generics,
    Members,
    Entries,
    /// Scenario `construct` field `{name, value: expression}`.
    ExpressionMember,
    ExpressionMembers,
    /// Scenario `map` entry `{key: expression, value: expression}`.
    ExpressionEntry,
    ExpressionEntries,
    Raw,
}

fn rendered(value: &Value, form: Form) -> Result<Value, String> {
    let mut text = String::new();
    render(value, form, &mut text)?;
    Ok(Value::String(text))
}

fn render(value: &Value, form: Form, output: &mut String) -> Result<(), String> {
    use Form::*;
    if matches!(form, Raw) || value.is_null() {
        write!(output, "{value}").expect("writing to String cannot fail");
        return Ok(());
    }
    let element = match form {
        Expressions => Some(Expression),
        Types => Some(Type),
        Values => Some(Value),
        Patterns => Some(Pattern),
        Generics => Some(Generic),
        Members => Some(Member),
        Entries => Some(Values),
        ExpressionMembers => Some(ExpressionMember),
        ExpressionEntries => Some(ExpressionEntry),
        _ => None,
    };
    if let Some(element) = element {
        let values = value
            .as_array()
            .ok_or_else(|| "semantic prompt node must be an array".to_owned())?;
        output.push('[');
        for (index, value) in values.iter().enumerate() {
            if index != 0 {
                output.push(',');
            }
            render(value, element, output)?;
        }
        output.push(']');
        return Ok(());
    }
    let object = value
        .as_object()
        .ok_or_else(|| "semantic prompt node must be an object".to_owned())?;
    let kind = match form {
        Selector | OptionalSelector => "selector",
        Member | ExpressionMember => "member",
        ExpressionEntry => "entry",
        _ => object
            .get("kind")
            .and_then(serde_json::Value::as_str)
            .ok_or_else(|| "semantic prompt node must have a kind".to_owned())?,
    };
    let fields = fields(form, kind)?;
    for (key, form) in fields {
        if !object.contains_key(*key) && !matches!(form, OptionalSelector) {
            return Err(format!("semantic prompt {kind} is missing `{key}`"));
        }
    }
    if matches!(form, Expression | Pattern) && !object.contains_key("type") {
        return Err(format!(
            "semantic prompt {kind} is missing its resolved type"
        ));
    }
    output.push_str(kind);
    output.push('(');
    let mut separator = "";
    for (key, child) in object {
        if key == "kind" || diagnostic(key) {
            continue;
        }
        output.push_str(separator);
        separator = ",";
        output.push_str(key);
        output.push('=');
        let child_form = if key == "type" && matches!(form, Expression | Pattern) {
            Type
        } else if key == "reference" && matches!(form, Expression) {
            Reference
        } else {
            fields
                .iter()
                .find_map(|(field, form)| (*field == key).then_some(*form))
                // Preserve non-expression metadata rather than dropping it.
                .unwrap_or(Raw)
        };
        render(child, child_form, output)?;
    }
    output.push(')');
    Ok(())
}

// Exhaustive over canonical-ir v9 expression/type/value/pattern/const kinds.
// Expressions have no general call or quantifier node: collection predicates
// are the closed intrinsics below. Future expression kinds must be implemented
// here, never recovered from source or silently treated as prose.
fn fields(form: Form, kind: &str) -> Result<&'static [(&'static str, Form)], String> {
    use Form::*;
    let fields: &[(&str, Form)] = match form {
        Expression => match kind {
            "literal" => &[("value", Value)],
            "parameter_ref" | "binding_ref" | "constant_ref" | "enum_singleton_ref" => {
                &[("symbol", Raw)]
            }
            "self_ref" | "result_ref" => &[],
            "old_state_field" => &[("field", Raw)],
            "field" => &[("base", Expression), ("name", Raw)],
            "len" => &[("value", Expression)],
            "unary" => &[("op", Raw), ("operand", Expression)],
            "binary" => &[("left", Expression), ("op", Raw), ("right", Expression)],
            "comparison_chain" => &[("operands", Expressions), ("operators", Raw)],
            "intrinsic" => &[
                ("arguments", Expressions),
                ("name", Raw),
                ("selector", Selector),
                ("dependencies", OptionalSelector),
            ],
            "fixture_path" | "fixture_url" => &[("fixture", Raw), ("path", Raw)],
            "construct" => &[("fields", ExpressionMembers), ("symbol", Raw)],
            "dyn" => &[("trait_ref", Type), ("value", Expression)],
            "variant" => &[("fields", Expressions), ("symbol", Raw)],
            "option_some" | "result_ok" | "result_err" => &[("payload", Expression)],
            "list" | "set" | "tuple" | "array" => &[("items", Expressions)],
            "map" => &[("entries", ExpressionEntries)],
            "match" => &[
                ("condition", Expression),
                ("pattern", Pattern),
                ("scrutinee", Expression),
            ],
            _ => {
                return Err(format!(
                    "unsupported canonical prompt expression kind `{kind}`"
                ));
            }
        },
        Type => match kind {
            "primitive" | "type_parameter" => &[("name", Raw)],
            "named" => &[("args", Generics), ("name", Raw)],
            "list" | "set" | "option" | "iterator" | "async_iterator" => &[("item", Type)],
            "map" => &[("key", Type), ("value", Type)],
            "tuple" => &[("items", Types)],
            "array" => &[("item", Type), ("length", Const)],
            "buffer" => &[("length", Const)],
            "result" => &[("error", Type), ("ok", Type)],
            "opaque" => &[("tag", Raw)],
            "generator" => &[("return", Type), ("send", Type), ("yield", Type)],
            "async_generator" => &[("send", Type), ("yield", Type)],
            "factory" => &[("instance", Type)],
            "associated_projection" => &[("base", Type), ("name", Raw), ("trait", Raw)],
            "dyn" => &[("trait", Type)],
            _ => return Err(format!("unsupported canonical prompt type kind `{kind}`")),
        },
        Value => match kind {
            "bool" | "integer" | "string" | "bytes" | "json" => &[("value", Raw)],
            "f32" | "f64" => &[("bits", Raw)],
            "unit" => &[],
            "option" => &[("value", Value)],
            "result" => &[("ok", Raw), ("value", Value)],
            "list" | "set" | "tuple" | "array" => &[("items", Values)],
            "map" => &[("entries", Entries)],
            "buffer" => &[("hex", Raw)],
            "named" => &[("fields", Members), ("symbol", Raw)],
            "enum" => &[("fields", Values), ("variant", Raw)],
            _ => return Err(format!("unsupported canonical prompt value kind `{kind}`")),
        },
        Pattern => match kind {
            "wildcard" => &[],
            "binding" => &[("name", Raw), ("symbol", Raw)],
            "result_ok" | "result_err" | "option_some" | "option_none" | "enum" => {
                &[("arguments", Patterns), ("symbol", Raw)]
            }
            _ => {
                return Err(format!(
                    "unsupported canonical prompt pattern kind `{kind}`"
                ));
            }
        },
        Const => match kind {
            "value" => &[("type", Raw), ("value", Raw)],
            "parameter" => &[("name", Raw), ("type", Raw)],
            "reference" => &[("symbol", Raw), ("type", Raw)],
            "binary" => &[
                ("left", Const),
                ("op", Raw),
                ("right", Const),
                ("type", Raw),
            ],
            _ => return Err(format!("unsupported canonical prompt const kind `{kind}`")),
        },
        Generic => match kind {
            "type" => &[("type", Type)],
            "const" => &[("value", Const)],
            _ => {
                return Err(format!(
                    "unsupported canonical prompt generic kind `{kind}`"
                ));
            }
        },
        Reference => match kind {
            "parameter" | "binding" | "constant" | "enum_singleton" | "field"
            | "old_state_field" => &[("symbol", Raw)],
            _ => {
                return Err(format!(
                    "unsupported canonical prompt reference kind `{kind}`"
                ));
            }
        },
        Selector | OptionalSelector => &[("field", Raw), ("owner", Raw)],
        Member => &[("name", Raw), ("value", Value)],
        ExpressionMember => &[("name", Raw), ("value", Expression)],
        ExpressionEntry => &[("key", Expression), ("value", Expression)],
        _ => unreachable!("arrays and raw JSON are handled before node fields"),
    };
    Ok(fields)
}
