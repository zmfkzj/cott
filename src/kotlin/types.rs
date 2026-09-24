use serde_json::Value;

use crate::hash::sha256_hex;

const KOTLIN_KEYWORDS: &[&str] = &[
    "as",
    "break",
    "class",
    "continue",
    "do",
    "else",
    "false",
    "for",
    "fun",
    "if",
    "in",
    "interface",
    "is",
    "null",
    "object",
    "package",
    "return",
    "super",
    "this",
    "throw",
    "true",
    "try",
    "typealias",
    "typeof",
    "val",
    "var",
    "when",
    "while",
    "by",
    "catch",
    "constructor",
    "delegate",
    "dynamic",
    "field",
    "file",
    "finally",
    "get",
    "import",
    "init",
    "param",
    "property",
    "receiver",
    "set",
    "setparam",
    "value",
    "where",
    "actual",
    "abstract",
    "annotation",
    "companion",
    "const",
    "crossinline",
    "data",
    "enum",
    "expect",
    "external",
    "final",
    "infix",
    "inline",
    "inner",
    "internal",
    "lateinit",
    "noinline",
    "open",
    "operator",
    "out",
    "override",
    "private",
    "protected",
    "public",
    "reified",
    "sealed",
    "suspend",
    "tailrec",
    "vararg",
    "field",
    "it",
];

pub(crate) trait KotlinTypeContext {
    fn named_associated_arguments(&self, ty: &Value, name: &str) -> Result<Vec<String>, String>;

    fn associated_projection(
        &self,
        base: &Value,
        trait_name: &str,
        slot_name: &str,
    ) -> Result<String, String>;
}

pub(crate) fn render_type(ty: &Value) -> Result<String, String> {
    render_type_contextual(ty, None, None)
}

pub(crate) fn render_type_contextual(
    ty: &Value,
    module: Option<&str>,
    context: Option<&dyn KotlinTypeContext>,
) -> Result<String, String> {
    let object = ty
        .as_object()
        .ok_or_else(|| "canonical Kotlin type must be an object".to_owned())?;
    let kind = string(object.get("kind"), "type.kind")?;
    match kind {
        "primitive" => match string(object.get("name"), "primitive type.name")? {
            "bool" => Ok("kotlin.Boolean".to_owned()),
            "i8" => Ok("kotlin.Byte".to_owned()),
            "i16" => Ok("kotlin.Short".to_owned()),
            "i32" => Ok("kotlin.Int".to_owned()),
            "i64" => Ok("kotlin.Long".to_owned()),
            "u8" => Ok("kotlin.UByte".to_owned()),
            "u16" => Ok("kotlin.UShort".to_owned()),
            "u32" => Ok("kotlin.UInt".to_owned()),
            "u64" => Ok("kotlin.ULong".to_owned()),
            "f32" => Ok("kotlin.Float".to_owned()),
            "f64" => Ok("kotlin.Double".to_owned()),
            "str" => Ok("kotlin.String".to_owned()),
            "bytes" => Ok("cott_runtime.CottBytes".to_owned()),
            "path" => Ok("java.nio.file.Path".to_owned()),
            "unit" => Ok("cott_runtime.CottUnit".to_owned()),
            "json" => Ok("cott_runtime.JsonValue".to_owned()),
            "any" => Ok("kotlin.Any?".to_owned()),
            "unknown" => Ok("kotlin.Any?".to_owned()),
            "never" => Ok("kotlin.Nothing".to_owned()),
            name => Err(format!("unsupported canonical primitive type `{name}`")),
        },
        "named" => {
            let name = string(object.get("name"), "named type.name")?;
            let mut arguments = Vec::new();
            for (index, argument) in array(object.get("args"), "named type.args")?
                .iter()
                .enumerate()
            {
                let argument = argument
                    .as_object()
                    .ok_or_else(|| format!("named type argument {index} must be an object"))?;
                match string(argument.get("kind"), "generic argument.kind")? {
                    "type" => arguments.push(render_type_contextual(
                        required(argument.get("type"), "generic type argument.type")?,
                        module,
                        context,
                    )?),
                    "const" => arguments.push(render_const_marker(required(
                        argument.get("value"),
                        "generic const argument.value",
                    )?)?),
                    other => return Err(format!("unsupported generic argument kind `{other}`")),
                }
            }
            if let Some(context) = context {
                arguments.extend(context.named_associated_arguments(ty, name)?);
            }
            let name = render_qualified(name)?;
            Ok(if arguments.is_empty() {
                name
            } else {
                format!("{name}<{}>", arguments.join(", "))
            })
        }
        "type_parameter" => escape_identifier(string(object.get("name"), "type parameter.name")?),
        "associated_projection" => {
            let trait_name = string(object.get("trait"), "associated projection.trait")?;
            let slot_name = string(object.get("name"), "associated projection.name")?;
            match context {
                Some(context) => context.associated_projection(
                    required(object.get("base"), "associated projection.base")?,
                    trait_name,
                    slot_name,
                ),
                None => projected_associated_type_name(
                    required(object.get("base"), "associated projection.base")?,
                    trait_name,
                    slot_name,
                ),
            }
        }
        "list" => unary_type("cott_runtime.CottList", object.get("item"), module, context),
        "set" => unary_type("cott_runtime.CottSet", object.get("item"), module, context),
        "map" => Ok(format!(
            "cott_runtime.FrozenMap<{}, {}>",
            render_type_contextual(
                required(object.get("key"), "map type.key")?,
                module,
                context,
            )?,
            render_type_contextual(
                required(object.get("value"), "map type.value")?,
                module,
                context,
            )?
        )),
        "tuple" => {
            let items = array(object.get("items"), "tuple type.items")?;
            let rendered = items
                .iter()
                .map(|item| render_type_contextual(item, module, context))
                .collect::<Result<Vec<_>, _>>()?;
            let name = format!("cott_runtime.CottTuple{}", rendered.len());
            Ok(if rendered.is_empty() {
                name
            } else {
                format!("{name}<{}>", rendered.join(", "))
            })
        }
        "array" => Ok(format!(
            "cott_runtime.CottArray<{}, {}>",
            render_type_contextual(
                required(object.get("item"), "array type.item")?,
                module,
                context,
            )?,
            render_const_marker(required(object.get("length"), "array type.length")?)?
        )),
        "buffer" => Ok(format!(
            "cott_runtime.CottBuffer<{}>",
            render_const_marker(required(object.get("length"), "buffer type.length")?)?
        )),
        "option" => unary_type(
            "cott_runtime.CottOption",
            object.get("item"),
            module,
            context,
        ),
        "result" => Ok(format!(
            "cott_runtime.CottResult<{}, {}>",
            render_type_contextual(
                required(object.get("ok"), "result type.ok")?,
                module,
                context,
            )?,
            render_type_contextual(
                required(object.get("error"), "result type.error")?,
                module,
                context,
            )?
        )),
        "iterator" => unary_type(
            "cott_runtime.CottIterator",
            object.get("item"),
            module,
            context,
        ),
        "async_iterator" => unary_type(
            "cott_runtime.CottAsyncIterator",
            object.get("item"),
            module,
            context,
        ),
        "generator" => Ok(format!(
            "cott_runtime.CottGenerator<{}, {}, {}>",
            render_type_contextual(
                required(object.get("yield"), "generator type.yield")?,
                module,
                context,
            )?,
            render_type_contextual(
                required(object.get("send"), "generator type.send")?,
                module,
                context,
            )?,
            render_type_contextual(
                required(object.get("return"), "generator type.return")?,
                module,
                context,
            )?
        )),
        "async_generator" => Ok(format!(
            "cott_runtime.CottAsyncGenerator<{}, {}, cott_runtime.CottUnit>",
            render_type_contextual(
                required(object.get("yield"), "async generator type.yield")?,
                module,
                context,
            )?,
            render_type_contextual(
                required(object.get("send"), "async generator type.send")?,
                module,
                context,
            )?
        )),
        "dyn" => unary_type("cott_runtime.Dyn", object.get("trait"), module, context),
        "factory" => unary_type(
            "cott_runtime.CottFactory",
            object.get("instance"),
            module,
            context,
        ),
        "opaque" => Ok(format!(
            "cott_runtime.Opaque<cott_runtime.{}>",
            opaque_marker(string(object.get("tag"), "opaque type.tag")?)
        )),
        other => Err(format!("unsupported canonical type kind `{other}`")),
    }
}
pub(crate) fn render_primitive_descriptor(ty: &Value) -> Result<String, String> {
    let object = ty
        .as_object()
        .ok_or_else(|| "canonical Kotlin primitive descriptor must be an object".to_owned())?;
    if string(object.get("kind"), "type.kind")? != "primitive" {
        return Err("Kotlin primitive descriptor requires a primitive type".to_owned());
    }
    let name = string(object.get("name"), "primitive type.name")?;
    let property = match name {
        "bool" => "BOOL",
        "i8" => "I8",
        "i16" => "I16",
        "i32" => "I32",
        "i64" => "I64",
        "u8" => "U8",
        "u16" => "U16",
        "u32" => "U32",
        "u64" => "U64",
        "f32" => "F32",
        "f64" => "F64",
        "str" => "STRING",
        "bytes" => "BYTES",
        "path" => "PATH",
        "unit" => "UNIT",
        "json" => "JSON",
        "any" | "unknown" => "ANY",
        "never" => "NEVER",
        other => return Err(format!("unsupported descriptor primitive `{other}`")),
    };
    Ok(format!("cott_runtime.CottTypes.{property}"))
}

pub(crate) fn render_const_marker(value: &Value) -> Result<String, String> {
    if value.get("kind").and_then(Value::as_str) == Some("parameter") {
        return escape_identifier(
            value
                .get("name")
                .and_then(Value::as_str)
                .ok_or_else(|| "const parameter is missing name".to_owned())?,
        );
    }
    let parameters = const_parameters_in(value)?;
    Ok(if parameters.is_empty() {
        format!("cott_runtime.{}", const_marker(value)?)
    } else {
        format!(
            "cott_runtime.{}<{}>",
            const_marker(value)?,
            parameters.join(", ")
        )
    })
}

pub(crate) fn render_const_witness(value: &Value) -> Result<String, String> {
    if value.get("kind").and_then(Value::as_str) == Some("parameter") {
        return Ok(format!(
            "_cott_const_{}",
            internal_name(
                value
                    .get("name")
                    .and_then(Value::as_str)
                    .ok_or_else(|| "const parameter is missing name".to_owned())?
            )
        ));
    }
    let parameters = const_parameters_in(value)?;
    Ok(if parameters.is_empty() {
        format!("cott_runtime.{}", const_marker(value)?)
    } else {
        format!(
            "cott_runtime.{}({})",
            const_marker(value)?,
            parameters
                .iter()
                .map(|name| format!("_cott_const_{}", internal_name(name)))
                .collect::<Vec<_>>()
                .join(", ")
        )
    })
}
pub(crate) fn const_marker(value: &Value) -> Result<String, String> {
    let bytes = serde_json::to_vec(value)
        .map_err(|error| format!("serialize canonical const argument: {error}"))?;
    Ok(format!("CottConst_{}", &sha256_hex(&bytes)[..24]))
}

pub(crate) fn const_parameters_in(value: &Value) -> Result<Vec<String>, String> {
    let mut parameters = Vec::new();
    collect_const_parameters(value, &mut parameters)?;
    Ok(parameters)
}

fn collect_const_parameters(value: &Value, parameters: &mut Vec<String>) -> Result<(), String> {
    match value {
        Value::Array(values) => {
            for value in values {
                collect_const_parameters(value, parameters)?;
            }
        }
        Value::Object(object) => {
            if object.get("kind").and_then(Value::as_str) == Some("parameter") {
                let name = string(object.get("name"), "const parameter.name")?.to_owned();
                if !parameters.contains(&name) {
                    parameters.push(name);
                }
                return Ok(());
            }
            for value in object.values() {
                collect_const_parameters(value, parameters)?;
            }
        }
        _ => {}
    }
    Ok(())
}
pub(crate) fn associated_type_name(trait_name: &str, slot_name: &str) -> String {
    let identity = format!("{trait_name}::{}", local_name(slot_name));
    format!("CottAssoc_{}", &sha256_hex(identity.as_bytes())[..24])
}

pub(crate) fn projected_associated_type_name(
    base: &Value,
    trait_name: &str,
    slot_name: &str,
) -> Result<String, String> {
    let base = serde_json::to_string(base)
        .map_err(|error| format!("serialize associated projection base: {error}"))?;
    let identity = format!("{trait_name}::{}::{base}", local_name(slot_name));
    Ok(format!(
        "CottAssoc_{}",
        &sha256_hex(identity.as_bytes())[..24]
    ))
}

pub(crate) fn opaque_marker(tag: &str) -> String {
    format!("CottOpaque_{}", &sha256_hex(tag.as_bytes())[..24])
}

pub(crate) fn trait_marker(trait_ref: &Value) -> Result<String, String> {
    let bytes = serde_json::to_vec(trait_ref)
        .map_err(|error| format!("serialize canonical trait specialization: {error}"))?;
    Ok(format!("CottTrait_{}", &sha256_hex(&bytes)[..24]))
}

pub(crate) fn erased_class_name(ty: &Value) -> Result<String, String> {
    let object = ty
        .as_object()
        .ok_or_else(|| "factory instance type must be an object".to_owned())?;
    if object.get("kind").and_then(Value::as_str) != Some("named") {
        return Err("Factory instance must be a canonical named type".to_owned());
    }
    render_qualified(string(object.get("name"), "factory instance.name")?)
}

pub(crate) fn render_const_value(value: &Value) -> Result<String, String> {
    let object = value
        .as_object()
        .ok_or_else(|| "const argument must be an object".to_owned())?;
    match string(object.get("kind"), "const argument.kind")? {
        "value" => Ok(format!(
            "java.math.BigInteger({})",
            kotlin_string(
                object
                    .get("value")
                    .map(Value::to_string)
                    .as_deref()
                    .ok_or_else(|| "const value is missing value".to_owned())?
            )
        )),
        "parameter" => Ok(format!(
            "_cott_const_{}.value",
            internal_name(string(object.get("name"), "const parameter.name")?)
        )),
        "reference" => Ok(format!(
            "cott_runtime.CottRuntime.mathInt({})",
            render_qualified(string(object.get("symbol"), "const reference.symbol")?)?
        )),
        "binary" => {
            let left = render_const_value(required(object.get("left"), "const binary.left")?)?;
            let right = render_const_value(required(object.get("right"), "const binary.right")?)?;
            let method = match string(object.get("op"), "const binary.op")? {
                "add" => "intAdd",
                "subtract" => "intSubtract",
                "multiply" => "intMultiply",
                "divide" => "euclideanDivide",
                "remainder" => "euclideanRemainder",
                other => return Err(format!("unsupported const binary operator `{other}`")),
            };
            Ok(format!(
                "cott_runtime.CottRuntime.{method}({left}, {right})"
            ))
        }
        other => Err(format!("unsupported const argument kind `{other}`")),
    }
}
pub(crate) fn render_const_kind(value: &Value) -> Result<&'static str, String> {
    let kind = value
        .get("type")
        .and_then(Value::as_str)
        .ok_or_else(|| "const argument is missing integer type".to_owned())?;
    match kind {
        "u8" | "U8" => Ok("cott_runtime.CottIntKind.U8"),
        "u16" | "U16" => Ok("cott_runtime.CottIntKind.U16"),
        "u32" | "U32" => Ok("cott_runtime.CottIntKind.U32"),
        "u64" | "U64" => Ok("cott_runtime.CottIntKind.U64"),
        other => Err(format!("unsupported const generic integer kind `{other}`")),
    }
}

pub(crate) fn render_value(value: &Value, expected_type: Option<&Value>) -> Result<String, String> {
    let object = value
        .as_object()
        .ok_or_else(|| "canonical value must be an object".to_owned())?;
    match string(object.get("kind"), "value.kind")? {
        "bool" => Ok(
            if object.get("value").and_then(Value::as_bool) == Some(true) {
                "true".to_owned()
            } else {
                "false".to_owned()
            },
        ),
        "integer" => render_integer_value(
            string(object.get("value"), "integer value.value")?,
            expected_type,
        ),
        "f32" => {
            let bits = parse_hex_u32(string(object.get("bits"), "f32 value.bits")?)?;
            Ok(format!("kotlin.Float.fromBits({})", bits as i32))
        }
        "f64" => {
            let bits = parse_hex_u64(string(object.get("bits"), "f64 value.bits")?)?;
            Ok(format!("kotlin.Double.fromBits({})", bits as i64))
        }
        "string" => Ok(kotlin_string(string(
            object.get("value"),
            "string value.value",
        )?)),
        "bytes" => Ok(format!(
            "cott_runtime.CottBytes({})",
            render_byte_array(string(object.get("value"), "bytes value.value")?)?
        )),
        "unit" => Ok("cott_runtime.CottUnit".to_owned()),
        "option" => match object.get("value").filter(|value| !value.is_null()) {
            Some(value) => Ok(format!(
                "cott_runtime.Some({})",
                render_value(value, expected_type.and_then(|ty| ty.get("item")))?
            )),
            None => Ok("cott_runtime.Nothing".to_owned()),
        },
        "result" => {
            let ok = object.get("ok").and_then(Value::as_bool) == Some(true);
            let field = if ok { "ok" } else { "error" };
            Ok(format!(
                "cott_runtime.{}({})",
                if ok { "Ok" } else { "Err" },
                render_value(
                    required(object.get("value"), "result value.value")?,
                    expected_type.and_then(|ty| ty.get(field)),
                )?
            ))
        }
        "list" | "set" | "array" | "tuple" => {
            let items = array(object.get("items"), "container value.items")?;
            let item_type = expected_type.and_then(|ty| ty.get("item"));
            let values = items
                .iter()
                .enumerate()
                .map(|(index, item)| {
                    let expected = if object.get("kind").and_then(Value::as_str) == Some("tuple") {
                        expected_type
                            .and_then(|ty| ty.get("items"))
                            .and_then(Value::as_array)
                            .and_then(|items| items.get(index))
                    } else {
                        item_type
                    };
                    render_value(item, expected)
                })
                .collect::<Result<Vec<_>, _>>()?;
            match string(object.get("kind"), "container value.kind")? {
                "list" => Ok(format!(
                    "cott_runtime.CottRuntime.snapshotList(listOf({}))",
                    values.join(", ")
                )),
                "set" => Ok(format!(
                    "cott_runtime.CottRuntime.snapshotSet(listOf({}))",
                    values.join(", ")
                )),
                "array" => {
                    let length =
                        expected_type
                            .and_then(|ty| ty.get("length"))
                            .ok_or_else(|| {
                                "array literal requires its canonical expected type".to_owned()
                            })?;
                    Ok(format!(
                        "cott_runtime.CottRuntime.snapshotArray(listOf({}), {})",
                        values.join(", "),
                        render_const_witness(length)?
                    ))
                }
                "tuple" => Ok(format!(
                    "cott_runtime.CottTuple{}({})",
                    values.len(),
                    values.join(", ")
                )),
                _ => unreachable!(),
            }
        }
        "map" => {
            let (key_type, value_type) = expected_type
                .map(|ty| (ty.get("key"), ty.get("value")))
                .unwrap_or((None, None));
            let entries = array(object.get("entries"), "map value.entries")?
                .iter()
                .enumerate()
                .map(|(index, entry)| {
                    let entry = entry.as_array().ok_or_else(|| {
                        format!("map value entry {index} must be a two-element array")
                    })?;
                    if entry.len() != 2 {
                        return Err(format!("map value entry {index} must have two elements"));
                    }
                    Ok(format!(
                        "{} to {}",
                        render_value(&entry[0], key_type)?,
                        render_value(&entry[1], value_type)?
                    ))
                })
                .collect::<Result<Vec<_>, String>>()?;
            Ok(format!(
                "cott_runtime.CottRuntime.snapshotMap(linkedMapOf({}))",
                entries.join(", ")
            ))
        }
        "buffer" => {
            let length = expected_type
                .and_then(|ty| ty.get("length"))
                .ok_or_else(|| "buffer literal requires its canonical expected type".to_owned())?;
            let marker = render_const_marker(length)?;
            let witness = render_const_witness(length)?;
            Ok(format!(
                "cott_runtime.CottBuffer<{marker}>({}, {witness})",
                render_byte_array(string(object.get("hex"), "buffer value.hex")?)?
            ))
        }
        "named" => {
            let symbol = render_qualified(string(object.get("symbol"), "named value.symbol")?)?;
            let mut fields = array(object.get("fields"), "named value.fields")?
                .iter()
                .enumerate()
                .map(|(index, field)| {
                    let field = field
                        .as_object()
                        .ok_or_else(|| format!("named value field {index} must be an object"))?;
                    render_value(
                        required(field.get("value"), "named value field.value")?,
                        None,
                    )
                })
                .collect::<Result<Vec<_>, String>>()?;
            fields.extend(const_witness_values(expected_type)?);
            Ok(format!("{symbol}({})", fields.join(", ")))
        }
        "enum" => {
            let variant = render_qualified(string(object.get("variant"), "enum value.variant")?)?;
            let type_arguments = render_named_arguments(expected_type)?;
            let constructor = if type_arguments.is_empty() {
                variant
            } else {
                format!("{variant}<{}>", type_arguments.join(", "))
            };
            let mut fields = array(object.get("fields"), "enum value.fields")?
                .iter()
                .map(|field| render_value(field, None))
                .collect::<Result<Vec<_>, _>>()?;
            fields.extend(const_witness_values(expected_type)?);
            Ok(if fields.is_empty() && type_arguments.is_empty() {
                constructor
            } else {
                format!("{constructor}({})", fields.join(", "))
            })
        }
        "json" => render_json(required(object.get("value"), "json value.value")?),
        other => Err(format!("unsupported canonical value kind `{other}`")),
    }
}

pub(crate) fn render_named_arguments(ty: Option<&Value>) -> Result<Vec<String>, String> {
    ty.and_then(|ty| ty.get("args"))
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .map(|argument| {
            let argument = argument
                .as_object()
                .ok_or_else(|| "named generic argument must be an object".to_owned())?;
            match string(argument.get("kind"), "generic argument.kind")? {
                "type" => render_type(required(
                    argument.get("type"),
                    "generic type argument.type",
                )?),
                "const" => render_const_marker(required(
                    argument.get("value"),
                    "generic const argument.value",
                )?),
                other => Err(format!("unsupported generic argument kind `{other}`")),
            }
        })
        .collect()
}

pub(crate) fn const_witness_values(expected_type: Option<&Value>) -> Result<Vec<String>, String> {
    expected_type
        .and_then(|ty| ty.get("args"))
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter(|argument| argument.get("kind").and_then(Value::as_str) == Some("const"))
        .map(|argument| {
            render_const_witness(
                argument
                    .get("value")
                    .ok_or_else(|| "generic const argument is missing value".to_owned())?,
            )
        })
        .collect()
}

fn render_integer_value(value: &str, expected_type: Option<&Value>) -> Result<String, String> {
    let primitive = expected_type
        .and_then(Value::as_object)
        .filter(|ty| ty.get("kind").and_then(Value::as_str) == Some("primitive"))
        .and_then(|ty| ty.get("name"))
        .and_then(Value::as_str);
    Ok(match primitive {
        Some("i8") => format!("java.math.BigInteger({}).toByte()", kotlin_string(value)),
        Some("i16") => format!("java.math.BigInteger({}).toShort()", kotlin_string(value)),
        Some("i32") => format!("java.math.BigInteger({}).toInt()", kotlin_string(value)),
        Some("i64") => format!("java.math.BigInteger({}).toLong()", kotlin_string(value)),
        Some("u8") => format!(
            "java.math.BigInteger({}).toInt().toUByte()",
            kotlin_string(value)
        ),
        Some("u16") => format!(
            "java.math.BigInteger({}).toInt().toUShort()",
            kotlin_string(value)
        ),
        Some("u32") => format!(
            "java.math.BigInteger({}).toLong().toUInt()",
            kotlin_string(value)
        ),
        Some("u64") => format!(
            "java.math.BigInteger({}).toString().toULong()",
            kotlin_string(value)
        ),
        _ => format!("cott_runtime.CottRuntime.int({})", kotlin_string(value)),
    })
}

fn render_json(value: &Value) -> Result<String, String> {
    match value {
        Value::Null => Ok("cott_runtime.JsonNull".to_owned()),
        Value::Bool(value) => Ok(format!("cott_runtime.JsonBoolean({value})")),
        Value::Number(value) if value.is_i64() => Ok(format!(
            "cott_runtime.JsonInteger(java.math.BigInteger({}))",
            kotlin_string(&value.to_string())
        )),
        Value::Number(value) => {
            let number = value
                .as_f64()
                .ok_or_else(|| "JSON number cannot be represented as finite f64".to_owned())?;
            if !number.is_finite() {
                return Err("JSON float must be finite".to_owned());
            }
            Ok(format!("cott_runtime.JsonFloat({number:?})"))
        }
        Value::String(value) => Ok(format!("cott_runtime.JsonString({})", kotlin_string(value))),
        Value::Array(values) => Ok(format!(
            "cott_runtime.JsonArray(cott_runtime.CottRuntime.snapshotList(listOf({})))",
            values
                .iter()
                .map(render_json)
                .collect::<Result<Vec<_>, _>>()?
                .join(", ")
        )),
        Value::Object(values) => Ok(format!(
            "cott_runtime.JsonObject(linkedMapOf({}))",
            values
                .iter()
                .map(|(key, value)| Ok(format!(
                    "{} to {}",
                    kotlin_string(key),
                    render_json(value)?
                )))
                .collect::<Result<Vec<_>, String>>()?
                .join(", ")
        )),
    }
}

fn unary_type(
    name: &str,
    value: Option<&Value>,
    module: Option<&str>,
    context: Option<&dyn KotlinTypeContext>,
) -> Result<String, String> {
    Ok(format!(
        "{name}<{}>",
        render_type_contextual(required(value, "unary type argument")?, module, context)?
    ))
}

pub(crate) fn render_qualified(name: &str) -> Result<String, String> {
    if name.is_empty() || name.split('.').any(str::is_empty) {
        return Err(format!(
            "invalid empty segment in canonical identity `{name}`"
        ));
    }
    name.split('.')
        .map(escape_identifier)
        .collect::<Result<Vec<_>, _>>()
        .map(|parts| parts.join("."))
}

pub(crate) fn local_name(name: &str) -> &str {
    name.rsplit('.').next().unwrap_or(name)
}
pub(crate) fn internal_name(name: &str) -> String {
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

pub(crate) fn escape_identifier(name: &str) -> Result<String, String> {
    if name.is_empty()
        || name.contains('`')
        || name
            .chars()
            .any(|character| character == '\n' || character == '\r')
    {
        return Err(format!(
            "canonical identifier `{name}` cannot be represented in Kotlin"
        ));
    }
    let mut chars = name.chars();
    let ordinary = chars
        .next()
        .is_some_and(|character| character == '_' || character.is_alphabetic())
        && chars.all(|character| character == '_' || character.is_alphanumeric());
    Ok(if ordinary && !KOTLIN_KEYWORDS.contains(&name) {
        name.to_owned()
    } else {
        format!("`{name}`")
    })
}

pub(crate) fn kotlin_string(value: &str) -> String {
    let mut output = String::from("\"");
    for character in value.chars() {
        match character {
            '\\' => output.push_str("\\\\"),
            '"' => output.push_str("\\\""),
            '\n' => output.push_str("\\n"),
            '\r' => output.push_str("\\r"),
            '\t' => output.push_str("\\t"),
            '$' => output.push_str("\\$"),
            character if character.is_control() => {
                use std::fmt::Write as _;
                write!(output, "\\u{:04x}", character as u32)
                    .expect("writing to a String cannot fail");
            }
            character => output.push(character),
        }
    }
    output.push('"');
    output
}

fn render_byte_array(hex: &str) -> Result<String, String> {
    if hex.len() % 2 != 0 || !hex.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        return Err(format!("invalid canonical byte hex `{hex}`"));
    }
    let bytes = (0..hex.len())
        .step_by(2)
        .map(|index| {
            u8::from_str_radix(&hex[index..index + 2], 16)
                .map(|byte| format!("0x{byte:02x}.toByte()"))
                .map_err(|error| format!("invalid canonical byte hex `{hex}`: {error}"))
        })
        .collect::<Result<Vec<_>, _>>()?;
    Ok(format!("byteArrayOf({})", bytes.join(", ")))
}

fn parse_hex_u32(value: &str) -> Result<u32, String> {
    u32::from_str_radix(value.trim_start_matches("0x"), 16)
        .map_err(|error| format!("invalid canonical f32 bit pattern `{value}`: {error}"))
}

fn parse_hex_u64(value: &str) -> Result<u64, String> {
    u64::from_str_radix(value.trim_start_matches("0x"), 16)
        .map_err(|error| format!("invalid canonical f64 bit pattern `{value}`: {error}"))
}

fn required<'a>(value: Option<&'a Value>, field: &str) -> Result<&'a Value, String> {
    value.ok_or_else(|| format!("missing canonical `{field}`"))
}

fn string<'a>(value: Option<&'a Value>, field: &str) -> Result<&'a str, String> {
    required(value, field)?
        .as_str()
        .ok_or_else(|| format!("canonical `{field}` must be a string"))
}

fn array<'a>(value: Option<&'a Value>, field: &str) -> Result<&'a Vec<Value>, String> {
    required(value, field)?
        .as_array()
        .ok_or_else(|| format!("canonical `{field}` must be an array"))
}
