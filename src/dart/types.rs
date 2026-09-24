use std::collections::BTreeSet;

use serde_json::{Map, Value};

use crate::hash::sha256_hex;

use super::DartModule;

/// Deterministic Cott-to-Dart projection of enum declarations.
///
/// A Cott enum becomes a native Dart `enum` when the whole declaration can be
/// modelled by a finite set of constant members: it declares at least one
/// variant, no variant carries a payload, and the declaration takes no type or
/// const generics. Payload-carrying and generic enums keep the sealed
/// value-carrying class hierarchy because a Dart `enum` cannot represent
/// arbitrary runtime instances or per-instance generic witness arguments.
#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub(crate) struct DartEnumProjection {
    native: BTreeSet<String>,
}

impl DartEnumProjection {
    pub(crate) fn from_modules(modules: &[DartModule]) -> Result<Self, String> {
        let mut native = BTreeSet::new();
        for module in modules {
            for declaration in &module.declarations {
                let Some(declaration) = declaration
                    .as_object()
                    .filter(|object| object.get("kind").and_then(Value::as_str) == Some("enum"))
                else {
                    continue;
                };
                let name = string(declaration.get("name"), "enum.name")?;
                if projects_to_native_enum(declaration)? {
                    native.insert(name.to_owned());
                }
            }
        }
        Ok(Self { native })
    }

    /// `true` when `canonical` names an enum emitted as a native Dart `enum`.
    pub(crate) fn is_native(&self, canonical: &str) -> bool {
        self.native.contains(canonical)
    }

    /// `true` when `symbol` names a variant of a native Dart `enum`, which is
    /// a constant member reference rather than a constructed class.
    pub(crate) fn is_native_variant(&self, symbol: &str) -> bool {
        module_of(symbol).is_some_and(|owner| self.is_native(owner))
    }
}

fn projects_to_native_enum(declaration: &Map<String, Value>) -> Result<bool, String> {
    if !array(declaration.get("generics"), "enum.generics")?.is_empty() {
        return Ok(false);
    }
    let variants = array(declaration.get("variants"), "enum.variants")?;
    if variants.is_empty() {
        return Ok(false);
    }
    for variant in variants {
        if !array(variant.get("fields"), "enum variant.fields")?.is_empty() {
            return Ok(false);
        }
    }
    Ok(true)
}

/// The Dart member name of one native enum variant.
///
/// Members keep the exact Cott variant spelling. The single target-language
/// exception is a variant spelled like its own enum, which Dart rejects as a
/// member shadowing the enum type: such a member gains a `$` suffix. `$` is
/// outside the Cott identifier alphabet, so the escape stays injective and
/// can never collide with another declared variant. The canonical variant
/// identity carried by the member is unchanged.
pub(crate) fn native_enum_member(enum_local: &str, variant_local: &str) -> Result<String, String> {
    let owner = escape_identifier(enum_local)?;
    let member = escape_identifier(variant_local)?;
    Ok(if member == owner {
        format!("{member}$")
    } else {
        member
    })
}

const DART_KEYWORDS: &[&str] = &[
    "abstract",
    "as",
    "assert",
    "async",
    "await",
    "base",
    "break",
    "case",
    "catch",
    "class",
    "const",
    "continue",
    "covariant",
    "default",
    "deferred",
    "do",
    "dynamic",
    "else",
    "enum",
    "export",
    "extends",
    "extension",
    "external",
    "factory",
    "false",
    "final",
    "finally",
    "for",
    "Function",
    "get",
    "hide",
    "if",
    "implements",
    "import",
    "in",
    "interface",
    "is",
    "late",
    "library",
    "mixin",
    "new",
    "null",
    "of",
    "on",
    "operator",
    "part",
    "required",
    "rethrow",
    "return",
    "sealed",
    "set",
    "show",
    "static",
    "super",
    "switch",
    "sync",
    "this",
    "throw",
    "true",
    "try",
    "typedef",
    "var",
    "void",
    "when",
    "while",
    "with",
    "yield",
];

pub(crate) trait DartTypeContext {
    fn named_associated_arguments(&self, ty: &Value, name: &str) -> Result<Vec<String>, String>;

    fn associated_projection(
        &self,
        base: &Value,
        trait_name: &str,
        slot_name: &str,
    ) -> Result<String, String>;
}

pub(crate) fn render_type_contextual(
    ty: &Value,
    module: Option<&str>,
    context: Option<&dyn DartTypeContext>,
) -> Result<String, String> {
    let object = ty
        .as_object()
        .ok_or_else(|| "canonical Dart type must be an object".to_owned())?;
    let kind = string(object.get("kind"), "type.kind")?;
    match kind {
        "primitive" => match string(object.get("name"), "primitive type.name")? {
            "bool" => Ok("bool".to_owned()),
            "i8" | "i16" | "i32" | "u8" | "u16" | "u32" => Ok("int".to_owned()),
            "i64" | "u64" => Ok("BigInt".to_owned()),
            "f32" | "f64" => Ok("double".to_owned()),
            "str" => Ok("String".to_owned()),
            "bytes" => Ok("cott_runtime.CottBytes".to_owned()),
            "path" => Ok("cott_runtime.CottPath".to_owned()),
            "unit" => Ok("cott_runtime.CottUnit".to_owned()),
            "json" => Ok("cott_runtime.JsonValue".to_owned()),
            "any" | "unknown" => Ok("Object?".to_owned()),
            "never" => Ok("Never".to_owned()),
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
            let name = render_canonical_symbol(name, module)?;
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
            "cott_runtime.CottMap<{}, {}>",
            render_type_contextual(
                required(object.get("key"), "map type.key")?,
                module,
                context
            )?,
            render_type_contextual(
                required(object.get("value"), "map type.value")?,
                module,
                context
            )?
        )),
        "tuple" => {
            let items = array(object.get("items"), "tuple type.items")?;
            let rendered = items
                .iter()
                .map(|item| render_type_contextual(item, module, context))
                .collect::<Result<Vec<_>, _>>()?;
            let name = format!("cott_markers.CottTuple{}", rendered.len());
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
                context
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
                context
            )?,
            render_type_contextual(
                required(object.get("error"), "result type.error")?,
                module,
                context
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
                context
            )?,
            render_type_contextual(
                required(object.get("send"), "generator type.send")?,
                module,
                context
            )?,
            render_type_contextual(
                required(object.get("return"), "generator type.return")?,
                module,
                context
            )?
        )),
        "async_generator" => Ok(format!(
            "cott_runtime.CottAsyncGenerator<{}, {}, cott_runtime.CottUnit>",
            render_type_contextual(
                required(object.get("yield"), "async generator type.yield")?,
                module,
                context
            )?,
            render_type_contextual(
                required(object.get("send"), "async generator type.send")?,
                module,
                context
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
            "cott_runtime.Opaque<cott_markers.{}>",
            opaque_marker(string(object.get("tag"), "opaque type.tag")?)
        )),
        other => Err(format!("unsupported canonical type kind `{other}`")),
    }
}

pub(crate) fn render_primitive_descriptor(ty: &Value) -> Result<String, String> {
    let object = ty
        .as_object()
        .ok_or_else(|| "canonical Dart primitive descriptor must be an object".to_owned())?;
    if string(object.get("kind"), "type.kind")? != "primitive" {
        return Err("Dart primitive descriptor requires a primitive type".to_owned());
    }
    let property = match string(object.get("name"), "primitive type.name")? {
        "bool" => "boolean",
        "i8" => "i8",
        "i16" => "i16",
        "i32" => "i32",
        "i64" => "i64",
        "u8" => "u8",
        "u16" => "u16",
        "u32" => "u32",
        "u64" => "u64",
        "f32" => "f32",
        "f64" => "f64",
        "str" => "string",
        "bytes" => "bytes",
        "path" => "path",
        "unit" => "unit",
        "json" => "json",
        "any" | "unknown" => "any",
        "never" => "never",
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
        format!("cott_markers.{}", const_marker(value)?)
    } else {
        format!(
            "cott_markers.{}<{}>",
            const_marker(value)?,
            parameters
                .iter()
                .map(|name| escape_identifier(name))
                .collect::<Result<Vec<_>, _>>()?
                .join(", ")
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
    let marker = const_marker(value)?;
    Ok(if parameters.is_empty() {
        format!("const cott_markers.{marker}()")
    } else {
        format!(
            "cott_markers.{marker}<{}>({})",
            parameters
                .iter()
                .map(|name| escape_identifier(name))
                .collect::<Result<Vec<_>, _>>()?
                .join(", "),
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

pub(crate) fn render_const_value(value: &Value) -> Result<String, String> {
    let object = value
        .as_object()
        .ok_or_else(|| "const argument must be an object".to_owned())?;
    match string(object.get("kind"), "const argument.kind")? {
        "value" => Ok(format!(
            "BigInt.parse({})",
            dart_string(
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
            render_canonical_symbol(
                string(object.get("symbol"), "const reference.symbol")?,
                None
            )?
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
    match value
        .get("type")
        .and_then(Value::as_str)
        .ok_or_else(|| "const argument is missing integer type".to_owned())?
    {
        "u8" | "U8" => Ok("cott_runtime.CottIntKind.u8"),
        "u16" | "U16" => Ok("cott_runtime.CottIntKind.u16"),
        "u32" | "U32" => Ok("cott_runtime.CottIntKind.u32"),
        "u64" | "U64" => Ok("cott_runtime.CottIntKind.u64"),
        other => Err(format!("unsupported const generic integer kind `{other}`")),
    }
}

pub(crate) fn render_value_contextual(
    value: &Value,
    expected_type: Option<&Value>,
    module: Option<&str>,
    projection: &DartEnumProjection,
) -> Result<String, String> {
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
        "f32" => Ok(format!(
            "cott_runtime.CottRuntime.f32FromBits({})",
            dart_string(string(object.get("bits"), "f32 value.bits")?)
        )),
        "f64" => Ok(format!(
            "cott_runtime.CottRuntime.f64FromBits({})",
            dart_string(string(object.get("bits"), "f64 value.bits")?)
        )),
        "string" => Ok(dart_string(string(
            object.get("value"),
            "string value.value",
        )?)),
        "bytes" => Ok(format!(
            "cott_runtime.CottBytes.fromHex({})",
            dart_string(string(object.get("value"), "bytes value.value")?)
        )),
        "unit" => Ok("cott_runtime.CottUnit.instance".to_owned()),
        "option" => match object.get("value").filter(|value| !value.is_null()) {
            Some(value) => Ok(format!(
                "cott_runtime.Some({})",
                render_value_contextual(
                    value,
                    expected_type.and_then(|ty| ty.get("item")),
                    module,
                    projection
                )?
            )),
            None => match expected_type.and_then(|ty| ty.get("item")) {
                Some(item) => Ok(format!(
                    "cott_runtime.Nothing<{}>()",
                    render_type_contextual(item, module, None)?
                )),
                None => Ok("cott_runtime.Nothing()".to_owned()),
            },
        },
        "result" => {
            let ok = object.get("ok").and_then(Value::as_bool) == Some(true);
            let field = if ok { "ok" } else { "error" };
            Ok(format!(
                "cott_runtime.{}({})",
                if ok { "Ok" } else { "Err" },
                render_value_contextual(
                    required(object.get("value"), "result value.value")?,
                    expected_type.and_then(|ty| ty.get(field)),
                    module,
                    projection,
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
                    render_value_contextual(item, expected, module, projection)
                })
                .collect::<Result<Vec<_>, _>>()?;
            match string(object.get("kind"), "container value.kind")? {
                "list" => Ok(format!("cott_runtime.CottList([{}])", values.join(", "))),
                "set" => Ok(format!("cott_runtime.CottSet([{}])", values.join(", "))),
                "array" => {
                    let length =
                        expected_type
                            .and_then(|ty| ty.get("length"))
                            .ok_or_else(|| {
                                "array literal requires its canonical expected type".to_owned()
                            })?;
                    Ok(format!(
                        "cott_runtime.CottArray([{}], {})",
                        values.join(", "),
                        render_const_witness(length)?
                    ))
                }
                "tuple" => Ok(format!(
                    "cott_markers.CottTuple{}({})",
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
                        "cott_runtime.CottMapEntry({}, {})",
                        render_value_contextual(&entry[0], key_type, module, projection)?,
                        render_value_contextual(&entry[1], value_type, module, projection)?
                    ))
                })
                .collect::<Result<Vec<_>, String>>()?;
            Ok(format!("cott_runtime.CottMap([{}])", entries.join(", ")))
        }
        "buffer" => {
            let length = expected_type
                .and_then(|ty| ty.get("length"))
                .ok_or_else(|| "buffer literal requires its canonical expected type".to_owned())?;
            Ok(format!(
                "cott_runtime.CottBuffer<{}>.fromHex({}, {})",
                render_const_marker(length)?,
                dart_string(string(object.get("hex"), "buffer value.hex")?),
                render_const_witness(length)?
            ))
        }
        "named" => {
            let symbol = render_canonical_symbol(
                string(object.get("symbol"), "named value.symbol")?,
                module,
            )?;
            let fields = array(object.get("fields"), "named value.fields")?
                .iter()
                .enumerate()
                .map(|(index, field)| {
                    let field = field
                        .as_object()
                        .ok_or_else(|| format!("named value field {index} must be an object"))?;
                    let name = string(field.get("name"), "named value field.name")?;
                    Ok(format!(
                        "{}: {}",
                        escape_identifier(name)?,
                        render_value_contextual(
                            required(field.get("value"), "named value field.value")?,
                            None,
                            module,
                            projection,
                        )?
                    ))
                })
                .collect::<Result<Vec<_>, String>>()?;
            let mut named_arguments = fields;
            named_arguments.extend(const_witness_values(expected_type)?);
            let type_witnesses = render_type_witness_values(expected_type, module)?;
            Ok(
                match (type_witnesses.is_empty(), named_arguments.is_empty()) {
                    (true, true) => format!("{symbol}()"),
                    (true, false) => format!("{symbol}({})", named_arguments.join(", ")),
                    (false, true) => format!("{symbol}({})", type_witnesses.join(", ")),
                    (false, false) => format!(
                        "{symbol}({}, {})",
                        type_witnesses.join(", "),
                        named_arguments.join(", ")
                    ),
                },
            )
        }
        "enum" => {
            let symbol = string(object.get("variant"), "enum value.variant")?;
            let variant = enum_variant_name(symbol, module, projection)?;
            if projection.is_native_variant(symbol) {
                return Ok(variant);
            }
            let type_arguments = render_named_arguments(expected_type, module)?;
            let constructor = if type_arguments.is_empty() {
                variant
            } else {
                format!("{variant}<{}>", type_arguments.join(", "))
            };
            let mut fields = array(object.get("fields"), "enum value.fields")?
                .iter()
                .enumerate()
                .map(|(index, field)| {
                    Ok(format!(
                        "field{index}: {}",
                        render_value_contextual(field, None, module, projection)?
                    ))
                })
                .collect::<Result<Vec<_>, String>>()?;
            fields.extend(const_witness_values(expected_type)?);
            let type_witnesses = render_type_witness_values(expected_type, module)?;
            Ok(match (type_witnesses.is_empty(), fields.is_empty()) {
                (true, true) => format!("{constructor}()"),
                (true, false) => format!("{constructor}({})", fields.join(", ")),
                (false, true) => format!("{constructor}({})", type_witnesses.join(", ")),
                (false, false) => format!(
                    "{constructor}({}, {})",
                    type_witnesses.join(", "),
                    fields.join(", ")
                ),
            })
        }
        "json" => render_json(required(object.get("value"), "json value.value")?),
        other => Err(format!("unsupported canonical value kind `{other}`")),
    }
}

pub(crate) fn render_named_arguments(
    ty: Option<&Value>,
    module: Option<&str>,
) -> Result<Vec<String>, String> {
    ty.and_then(|ty| ty.get("args"))
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .map(|argument| {
            let argument = argument
                .as_object()
                .ok_or_else(|| "named generic argument must be an object".to_owned())?;
            match string(argument.get("kind"), "generic argument.kind")? {
                "type" => render_type_contextual(
                    required(argument.get("type"), "generic type argument.type")?,
                    module,
                    None,
                ),
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
            let value = argument
                .get("value")
                .ok_or_else(|| "generic const argument is missing value".to_owned())?;
            let name = value.get("name").and_then(Value::as_str).unwrap_or("value");
            Ok(format!(
                "cottConst{}: {}",
                pascal_identifier(name)?,
                render_const_witness(value)?,
            ))
        })
        .collect()
}

pub(crate) fn render_type_witness_values(
    ty: Option<&Value>,
    module: Option<&str>,
) -> Result<Vec<String>, String> {
    ty.and_then(|ty| ty.get("args"))
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter(|argument| argument.get("kind").and_then(Value::as_str) == Some("type"))
        .map(|argument| {
            render_simple_descriptor(
                required(argument.get("type"), "generic type argument.type")?,
                module,
            )
        })
        .collect()
}

fn render_simple_descriptor(ty: &Value, module: Option<&str>) -> Result<String, String> {
    let object = ty
        .as_object()
        .ok_or_else(|| "generic type witness must be an object".to_owned())?;
    match string(object.get("kind"), "generic type witness.kind")? {
        "primitive" => render_primitive_descriptor(ty),
        "type_parameter" => Ok(format!(
            "_cott_type_{}",
            internal_name(string(object.get("name"), "type parameter.name")?)
        )),
        "list" | "set" | "option" | "iterator" | "async_iterator" => {
            let (method, field) = match string(object.get("kind"), "container type.kind")? {
                "list" => ("list", "item"),
                "set" => ("set", "item"),
                "option" => ("option", "item"),
                "iterator" => ("iterator", "item"),
                "async_iterator" => ("asyncIterator", "item"),
                _ => unreachable!(),
            };
            Ok(format!(
                "cott_runtime.CottTypes.{method}({})",
                render_simple_descriptor(
                    required(object.get(field), "container item type")?,
                    module
                )?
            ))
        }
        "map" | "result" => {
            let kind = string(object.get("kind"), "binary container.kind")?;
            let (method, left, right) = if kind == "map" {
                ("map", "key", "value")
            } else {
                ("result", "ok", "error")
            };
            Ok(format!(
                "cott_runtime.CottTypes.{method}({}, {})",
                render_simple_descriptor(required(object.get(left), kind)?, module)?,
                render_simple_descriptor(required(object.get(right), kind)?, module)?
            ))
        }
        "named" => {
            let canonical = string(object.get("name"), "named type.name")?;
            let rendered = render_type_contextual(ty, module, None)?;
            Ok(format!(
                "cott_runtime.CottTypes.external<{rendered}>({}, (value) => value is {rendered}, identityWitness: {rendered})",
                dart_string(canonical)
            ))
        }
        other => Err(format!(
            "generic value literal uses unsupported type witness kind `{other}`"
        )),
    }
}

fn pascal_identifier(name: &str) -> Result<String, String> {
    escape_identifier(name)?;
    let mut chars = name.chars();
    let first = chars
        .next()
        .ok_or_else(|| "empty Dart identifier".to_owned())?;
    Ok(first.to_ascii_uppercase().to_string() + chars.as_str())
}

fn render_integer_value(value: &str, expected_type: Option<&Value>) -> Result<String, String> {
    let primitive = expected_type
        .and_then(Value::as_object)
        .filter(|ty| ty.get("kind").and_then(Value::as_str) == Some("primitive"))
        .and_then(|ty| ty.get("name"))
        .and_then(Value::as_str);
    Ok(match primitive {
        Some("i8") => format!("cott_runtime.CottRuntime.i8({})", dart_string(value)),
        Some("i16") => format!("cott_runtime.CottRuntime.i16({})", dart_string(value)),
        Some("i32") => format!("cott_runtime.CottRuntime.i32({})", dart_string(value)),
        Some("i64") => format!("cott_runtime.CottRuntime.i64({})", dart_string(value)),
        Some("u8") => format!("cott_runtime.CottRuntime.u8({})", dart_string(value)),
        Some("u16") => format!("cott_runtime.CottRuntime.u16({})", dart_string(value)),
        Some("u32") => format!("cott_runtime.CottRuntime.u32({})", dart_string(value)),
        Some("u64") => format!("cott_runtime.CottRuntime.u64({})", dart_string(value)),
        _ => format!("BigInt.parse({})", dart_string(value)),
    })
}

fn render_json(value: &Value) -> Result<String, String> {
    match value {
        Value::Null => Ok("const cott_runtime.JsonNull()".to_owned()),
        Value::Bool(value) => Ok(format!("cott_runtime.JsonBoolean({value})")),
        Value::Number(value) if value.is_i64() || value.is_u64() => Ok(format!(
            "cott_runtime.JsonInteger(BigInt.parse({}))",
            dart_string(&value.to_string())
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
        Value::String(value) => Ok(format!("cott_runtime.JsonString({})", dart_string(value))),
        Value::Array(values) => Ok(format!(
            "cott_runtime.JsonArray(cott_runtime.CottList([{}]))",
            values
                .iter()
                .map(render_json)
                .collect::<Result<Vec<_>, _>>()?
                .join(", ")
        )),
        Value::Object(values) => Ok(format!(
            "cott_runtime.JsonObject.entries([{}])",
            values
                .iter()
                .map(|(key, value)| Ok(format!(
                    "cott_runtime.CottMapEntry({}, {})",
                    dart_string(key),
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
    context: Option<&dyn DartTypeContext>,
) -> Result<String, String> {
    Ok(format!(
        "{name}<{}>",
        render_type_contextual(required(value, "unary type argument")?, module, context)?
    ))
}

pub(crate) fn module_prefix(module: &str) -> String {
    let extra = module
        .bytes()
        .filter(|byte| matches!(byte, b'_' | b'.'))
        .count();
    let mut prefix = String::with_capacity("_cott_t_".len() + module.len() + extra);
    prefix.push_str("_cott_t_");
    for character in module.chars() {
        match character {
            '_' => prefix.push_str("_u"),
            '.' => prefix.push_str("__"),
            _ => prefix.push(character),
        }
    }
    prefix
}

pub(crate) fn consumer_module_prefix(module: &str) -> String {
    format!("cottT{}", &sha256_hex(module.as_bytes())[..16])
}

pub(crate) fn render_canonical_symbol(
    name: &str,
    current_module: Option<&str>,
) -> Result<String, String> {
    let (module, local) = name
        .rsplit_once('.')
        .ok_or_else(|| format!("canonical Dart identity `{name}` has no module qualifier"))?;
    let local = escape_identifier(local)?;
    Ok(if current_module == Some(module) {
        local
    } else {
        format!("{}.{}", module_prefix(module), local)
    })
}

/// Renders the Dart reference for a canonical enum variant: a constant member
/// of the native Dart `enum` when the owning declaration projects natively,
/// otherwise the concatenated sealed-subclass name.
pub(crate) fn enum_variant_name(
    symbol: &str,
    current_module: Option<&str>,
    projection: &DartEnumProjection,
) -> Result<String, String> {
    let (enum_name, variant) = symbol
        .rsplit_once('.')
        .ok_or_else(|| format!("enum variant `{symbol}` has no owner"))?;
    let (_, enum_local) = enum_name
        .rsplit_once('.')
        .ok_or_else(|| format!("enum variant owner `{enum_name}` has no module"))?;
    let module = module_of(enum_name).expect("checked module");
    let local = if projection.is_native(enum_name) {
        format!(
            "{}.{}",
            escape_identifier(enum_local)?,
            native_enum_member(enum_local, variant)?
        )
    } else {
        format!(
            "{}{}",
            escape_identifier(enum_local)?,
            escape_identifier(variant)?
        )
    };
    Ok(if current_module == Some(module) {
        local
    } else {
        format!("{}.{}", module_prefix(module), local)
    })
}

pub(crate) fn local_name(name: &str) -> &str {
    name.rsplit('.').next().unwrap_or(name)
}

pub(crate) fn module_of(name: &str) -> Option<&str> {
    name.rsplit_once('.').map(|(module, _)| module)
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
    let mut chars = name.chars();
    let first = chars
        .next()
        .ok_or_else(|| "empty Dart identifier".to_owned())?;
    if !(first == '_' || first == '$' || first.is_ascii_alphabetic())
        || !chars.all(|ch| ch == '_' || ch == '$' || ch.is_ascii_alphanumeric())
    {
        return Err(format!("invalid Dart identifier `{name}`"));
    }
    if name.starts_with("_cott_") {
        return Err(format!(
            "canonical identifier `{name}` uses compiler-reserved `_cott_` prefix"
        ));
    }
    Ok(
        if DART_KEYWORDS.contains(&name) || matches!(name, "cott_runtime" | "cott_markers") {
            format!("{name}$cott")
        } else {
            name.to_owned()
        },
    )
}

pub(crate) fn dart_string(value: &str) -> String {
    let mut out = String::from("'");
    for ch in value.chars() {
        match ch {
            '\\' => out.push_str("\\\\"),
            '\'' => out.push_str("\\'"),
            '$' => out.push_str("\\$"),
            '\n' => out.push_str("\\n"),
            '\r' => out.push_str("\\r"),
            '\t' => out.push_str("\\t"),
            '\u{08}' => out.push_str("\\b"),
            '\u{0c}' => out.push_str("\\f"),
            ch if ch.is_control() => {
                use std::fmt::Write as _;
                write!(out, "\\u{{{:x}}}", ch as u32).expect("writing to String cannot fail");
            }
            ch => out.push(ch),
        }
    }
    out.push('\'');
    out
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
