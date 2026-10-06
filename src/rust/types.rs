use serde_json::Value;

pub(crate) trait RustTypeContext {
    fn named_associated_arguments(&self, ty: &Value, name: &str) -> Result<Vec<String>, String>;
    fn value_projection(&self, _ty: &Value) -> Result<Option<String>, String> {
        Ok(None)
    }
    fn associated_projection(
        &self,
        base: &Value,
        trait_name: &str,
        slot_name: &str,
    ) -> Result<String, String>;
}
pub(crate) fn text<'a>(value: &'a Value, field: &str) -> Result<&'a str, String> {
    value
        .get(field)
        .and_then(Value::as_str)
        .ok_or_else(|| format!("canonical value lacks string {field}: {value}"))
}
pub(crate) fn items<'a>(value: &'a Value, field: &str) -> Result<&'a [Value], String> {
    value
        .get(field)
        .and_then(Value::as_array)
        .map(Vec::as_slice)
        .ok_or_else(|| format!("canonical value lacks array {field}"))
}
pub(crate) fn render_type_contextual(
    ty: &Value,
    module: Option<&str>,
    context: Option<&dyn RustTypeContext>,
) -> Result<String, String> {
    let r = |key: &str| render_type_contextual(&ty[key], module, context);
    let unary =
        |name: &str, key: &str| -> Result<String, String> { Ok(format!("{name}<{}>", r(key)?)) };
    if matches!(ty["kind"].as_str(), Some("named" | "dyn")) {
        if let Some(context) = context {
            if let Some(projected) = context.value_projection(ty)? {
                return Ok(projected);
            }
        }
    }
    Ok(match text(ty, "kind")? {
        "primitive" => match text(ty, "name")? {
            "bool" | "i8" | "i16" | "i32" | "i64" | "u8" | "u16" | "u32" | "u64" | "f32"
            | "f64" => text(ty, "name")?.into(),
            "str" => "String".into(),
            "bytes" => "Vec<u8>".into(),
            "path" => "std::path::PathBuf".into(),
            "unit" => "()".into(),
            "never" => "crate::cott_runtime::Never".into(),
            "json" => "crate::cott_runtime::JsonValue".into(),
            "any" | "unknown" => "crate::cott_runtime::AnyValue".into(),
            other => return Err(format!("unknown primitive {other}")),
        },
        "named" => {
            let name = text(ty, "name")?;
            let mut args = render_named_arguments(Some(ty), module)?;
            if let Some(c) = context {
                args.extend(c.named_associated_arguments(ty, name)?);
            }
            let name = render_canonical_symbol(name, module)?;
            if args.is_empty() {
                name
            } else {
                format!("{name}<{}>", args.join(", "))
            }
        }
        "type_parameter" => {
            if text(ty, "name")? == "Self" {
                "Self".into()
            } else {
                escape_identifier(text(ty, "name")?)?
            }
        }
        "associated_projection" => {
            if let Some(c) = context {
                c.associated_projection(&ty["base"], text(ty, "trait")?, text(ty, "name")?)?
            } else {
                projected_associated_type_name(&ty["base"], text(ty, "trait")?, text(ty, "name")?)?
            }
        }
        "list" => unary("Vec", "item")?,
        "set" => unary("crate::cott_runtime::Set", "item")?,
        "map" => format!("crate::cott_runtime::Map<{}, {}>", r("key")?, r("value")?),
        "tuple" => {
            let values = items(ty, "items")?
                .iter()
                .map(|v| render_type_contextual(v, module, context))
                .collect::<Result<Vec<_>, _>>()?;
            if values.len() > 12 {
                format!(
                    "crate::cott_runtime::Tuple{}<{}>",
                    values.len(),
                    values.join(", ")
                )
            } else {
                format!(
                    "({}{})",
                    values.join(", "),
                    if values.len() == 1 { "," } else { "" }
                )
            }
        }
        "array" => format!(
            "crate::cott_runtime::Array<{},{}>",
            r("item")?,
            super::emit::consts::render_marker(&ty["length"], module)?
        ),
        "buffer" => format!(
            "crate::cott_runtime::Buffer<{}>",
            super::emit::consts::render_marker(&ty["length"], module)?
        ),
        "option" => unary("Option", "item")?,
        "result" => format!("Result<{}, {}>", r("ok")?, r("error")?),
        "iterator" => unary("crate::cott_runtime::IteratorValue", "item")?,
        "async_iterator" => unary("crate::cott_runtime::AsyncIteratorValue", "item")?,
        "generator" => format!(
            "crate::cott_runtime::Generator<{}, {}, {}>",
            r("yield")?,
            r("send")?,
            r("return")?
        ),
        "async_generator" => format!(
            "crate::cott_runtime::AsyncGenerator<{}, {}>",
            r("yield")?,
            r("send")?
        ),
        "factory" => format!("crate::cott_runtime::Factory<{}>", r("instance")?),
        "dyn" => format!("crate::cott_runtime::Dyn<dyn {} + Send>", r("trait")?),
        "opaque" => format!(
            "crate::cott_runtime::Opaque<{}>",
            opaque_marker(text(ty, "tag")?)
        ),
        other => return Err(format!("unknown canonical type {other}")),
    })
}
pub(crate) fn render_const_marker(value: &Value) -> Result<String, String> {
    super::emit::consts::render_marker(value, None)
}
pub(crate) fn projected_associated_type_name(
    base: &Value,
    trait_name: &str,
    slot_name: &str,
) -> Result<String, String> {
    Ok(format!(
        "<{} as {}>::{}",
        render_type_contextual(base, None, None)?,
        render_canonical_symbol(trait_name, None)?,
        escape_identifier(local_name(slot_name))?
    ))
}
pub(crate) fn opaque_marker(tag: &str) -> String {
    format!(
        "{}",
        u64::from_str_radix(&crate::hash::sha256_hex(tag.as_bytes())[..16], 16)
            .expect("hex digest")
    )
}
pub(crate) fn collection_constructor(key: Option<&Value>) -> &'static str {
    if key.is_some_and(|ty| {
        ty["kind"] == "primitive"
            && matches!(
                ty["name"].as_str(),
                Some("str" | "bool" | "i8" | "i16" | "i32" | "i64" | "u8" | "u16" | "u32" | "u64")
            )
    }) {
        "from_scalar"
    } else {
        "new"
    }
}

pub(crate) fn render_value_contextual(
    value: &Value,
    expected_type: Option<&Value>,
    module: Option<&str>,
) -> Result<String, String> {
    let render = |v: &Value| render_value_contextual(v, None, module);
    Ok(match text(value, "kind")? {
        "integer" => text(value, "value")?.into(),
        "bool" | "boolean" => value["value"].to_string(),
        "f32" | "f64" => format!(
            "{}::from_bits(0x{})",
            text(value, "kind")?,
            text(value, "bits")?
        ),
        "string" if expected_type.is_some_and(|ty| ty["name"] == "path") => format!(
            "std::path::PathBuf::from({})",
            rust_string(text(value, "value")?)
        ),
        "string" => format!("{}.to_owned()", rust_string(text(value, "value")?)),
        "path" => format!(
            "std::path::PathBuf::from({})",
            rust_string(text(value, "value")?)
        ),
        "bytes" | "buffer" => {
            let hex = text(
                value,
                if value["kind"] == "bytes" {
                    "value"
                } else {
                    "hex"
                },
            )?;
            let bytes = (0..hex.len())
                .step_by(2)
                .map(|i| {
                    u8::from_str_radix(&hex[i..i + 2], 16)
                        .map(|b| b.to_string())
                        .map_err(|e| e.to_string())
                })
                .collect::<Result<Vec<_>, _>>()?;
            if value["kind"] == "bytes" {
                format!("vec![{}]", bytes.join(", "))
            } else {
                format!(
                    "crate::cott_runtime::Buffer::new(vec![{}])",
                    bytes.join(", ")
                )
            }
        }
        "unit" => "()".into(),
        "none" => "None".into(),
        "option" => {
            if !value["value"].is_null() {
                format!("Some({})", render(&value["value"])?)
            } else {
                "None".into()
            }
        }
        "result" => format!(
            "{}({})",
            if value["ok"] == true { "Ok" } else { "Err" },
            render(&value["value"])?
        ),
        "list" | "set" | "array" | "tuple" => {
            let values = items(value, "items")?
                .iter()
                .map(render)
                .collect::<Result<Vec<_>, _>>()?;
            match text(value, "kind")? {
                "list" => format!("vec![{}]", values.join(", ")),
                "set" => format!(
                    "crate::cott_runtime::Set::{}(vec![{}])",
                    collection_constructor(expected_type.and_then(|t| t.get("item"))),
                    values.join(", ")
                ),
                "array" => format!("[{}]", values.join(", ")),
                _ => format!(
                    "({}{})",
                    values.join(", "),
                    if values.len() == 1 { "," } else { "" }
                ),
            }
        }
        "map" => {
            let entries = items(value, "entries")?
                .iter()
                .map(|e| Ok(format!("({}, {})", render(&e[0])?, render(&e[1])?)))
                .collect::<Result<Vec<_>, String>>()?;
            format!(
                "crate::cott_runtime::Map::{}(vec![{}])",
                collection_constructor(expected_type.and_then(|t| t.get("key"))),
                entries.join(", ")
            )
        }
        "named" => {
            let fields = items(value, "fields")?
                .iter()
                .map(|f| render(&f["value"]))
                .collect::<Result<Vec<_>, _>>()?;
            format!(
                "{}::new({})",
                render_canonical_symbol(text(value, "symbol")?, module)?,
                fields.join(", ")
            )
        }
        "enum" => {
            let fields = items(value, "fields")?
                .iter()
                .map(render)
                .collect::<Result<Vec<_>, _>>()?;
            let name = enum_variant_name(text(value, "variant")?, module)?;
            if fields.is_empty() {
                name
            } else {
                format!("{name}({})", fields.join(", "))
            }
        }
        "json" => render_json_value(&value["value"])?,
        other => return Err(format!("unsupported canonical literal {other}")),
    })
}

fn render_json_value(value: &Value) -> Result<String, String> {
    Ok(match value {
        Value::Null => "crate::cott_runtime::JsonValue::Null".into(),
        Value::Bool(v) => format!("crate::cott_runtime::JsonValue::Bool({v})"),
        Value::Number(v) if v.is_i64() || v.is_u64() => {
            format!("crate::cott_runtime::JsonValue::Integer({v}i128)")
        }
        Value::Number(v) => format!("crate::cott_runtime::JsonValue::Number({}f64)", v),
        Value::String(v) => format!(
            "crate::cott_runtime::JsonValue::String({}.to_owned())",
            rust_string(v)
        ),
        Value::Array(values) => format!(
            "crate::cott_runtime::JsonValue::Array(vec![{}])",
            values
                .iter()
                .map(render_json_value)
                .collect::<Result<Vec<_>, _>>()?
                .join(", ")
        ),
        Value::Object(values) => format!(
            "crate::cott_runtime::JsonValue::Object(std::collections::BTreeMap::from([{}]))",
            values
                .iter()
                .map(|(k, v)| Ok(format!(
                    "({}.to_owned(), {})",
                    rust_string(k),
                    render_json_value(v)?
                )))
                .collect::<Result<Vec<_>, String>>()?
                .join(", ")
        ),
    })
}
pub(crate) fn render_named_arguments(
    ty: Option<&Value>,
    module: Option<&str>,
) -> Result<Vec<String>, String> {
    ty.and_then(|v| v.get("args"))
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .map(|a| {
            if a["kind"] == "type" {
                render_type_contextual(&a["type"], module, None)
            } else {
                render_const_marker(&a["value"])
            }
        })
        .collect()
}
pub(crate) fn module_prefix(module: &str) -> String {
    module
        .split('.')
        .map(|s| escape_identifier(s).unwrap_or_else(|_| s.into()))
        .collect::<Vec<_>>()
        .join("::")
}
pub(crate) fn render_canonical_symbol(
    name: &str,
    _current_module: Option<&str>,
) -> Result<String, String> {
    Ok(format!(
        "crate::modules::{}",
        name.split('.')
            .map(escape_identifier)
            .collect::<Result<Vec<_>, _>>()?
            .join("::")
    ))
}
pub(crate) fn enum_variant_name(
    symbol: &str,
    current_module: Option<&str>,
) -> Result<String, String> {
    render_canonical_symbol(symbol, current_module)
}
pub(crate) fn local_name(name: &str) -> &str {
    name.rsplit('.').next().unwrap_or(name)
}
pub(crate) fn module_of(name: &str) -> Option<&str> {
    name.rsplit_once('.').map(|v| v.0)
}
pub(crate) fn internal_name(name: &str) -> String {
    name.replace('.', "_")
}
pub(crate) fn escape_identifier(name: &str) -> Result<String, String> {
    if name.is_empty()
        || !name
            .bytes()
            .enumerate()
            .all(|(i, b)| b == b'_' || b.is_ascii_alphabetic() || (i > 0 && b.is_ascii_digit()))
    {
        return Err(format!("invalid Rust identifier {name}"));
    }
    if ["self", "Self", "super", "crate"].iter().any(|keyword| {
        name.strip_prefix(keyword)
            .is_some_and(|suffix| suffix.bytes().all(|b| b == b'_'))
    }) || name.bytes().all(|b| b == b'_')
    {
        return Ok(format!("{name}_"));
    }
    Ok(match name {
        "abstract" | "become" | "box" | "do" | "final" | "macro" | "override" | "priv"
        | "typeof" | "unsized" | "virtual" => format!("r#{name}"),
        "as" | "async" | "await" | "break" | "const" | "continue" | "dyn" | "else" | "enum"
        | "extern" | "false" | "fn" | "for" | "if" | "impl" | "in" | "let" | "loop" | "match"
        | "mod" | "move" | "mut" | "pub" | "ref" | "return" | "static" | "struct" | "trait"
        | "true" | "type" | "unsafe" | "use" | "where" | "while" | "yield" | "try" | "gen" => {
            format!("r#{name}")
        }
        _ => name.into(),
    })
}
pub(crate) fn rust_string(value: &str) -> String {
    format!("{value:?}")
}
