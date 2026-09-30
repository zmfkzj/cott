use crate::rust::types::{escape_identifier, render_canonical_symbol, text};
use serde_json::Value;

fn width(value: &Value) -> Result<u32, String> {
    match text(value, "type")? {
        "U8" => Ok(8),
        "U16" => Ok(16),
        "U32" => Ok(32),
        "U64" => Ok(64),
        other => Err(format!("invalid canonical const type {other}")),
    }
}

/// A type-level projection retains the entire canonical expression, including width.
pub(crate) fn render_marker(value: &Value, module: Option<&str>) -> Result<String, String> {
    let bits = width(value)?;
    Ok(match text(value, "kind")? {
        "value" => {
            let number = value["value"]
                .as_u64()
                .ok_or("canonical const value is not u64")?;
            if bits < 64 && number >= (1u64 << bits) {
                return Err("canonical const value exceeds its width".into());
            }
            format!("crate::cott_runtime::ConstU{bits}<{number}>")
        }
        "parameter" => escape_identifier(text(value, "name")?)?,
        "reference" => {
            let symbol = render_canonical_symbol(text(value, "symbol")?, module)?;
            format!("crate::cott_runtime::ConstU{bits}<{{ {symbol} }}>")
        }
        "binary" => {
            let operator = match text(value, "op")? {
                "add" => "Add",
                "subtract" => "Subtract",
                "multiply" => "Multiply",
                "divide" => "Divide",
                "remainder" => "Remainder",
                other => return Err(format!("invalid canonical const operator {other}")),
            };
            format!(
                "crate::cott_runtime::{operator}<{}, {}, {bits}>",
                render_marker(&value["left"], module)?,
                render_marker(&value["right"], module)?
            )
        }
        other => return Err(format!("invalid canonical const kind {other}")),
    })
}

pub(crate) fn render_kind(value: &Value) -> Result<String, String> {
    Ok(format!("crate::cott_runtime::ConstU{}Value", width(value)?))
}
