//! Prompts must show canonical declaration structure, but the authored Cott
//! clause text is both authoritative and two orders of magnitude smaller than
//! typed contract-expression trees. Intent fingerprints keep consuming the
//! untouched context.

use std::collections::BTreeMap;
use std::path::Path;

use serde_json::{Map, Value};

/// Read every canonical module's authored Cott source, keyed by module name.
pub fn module_sources(
    ir: &crate::ir::CanonicalIr,
    source_dir: &Path,
) -> Result<BTreeMap<String, String>, String> {
    let mut sources = BTreeMap::new();
    for module in &ir.modules {
        let name = module.module.as_string();
        if sources.contains_key(&name) {
            return Err(format!("duplicate canonical module `{name}`"));
        }
        let path = source_dir.join(&module.source);
        let bytes = std::fs::read(&path)
            .map_err(|error| format!("failed to read source {}: {error}", path.display()))?;
        let text = String::from_utf8(bytes)
            .map_err(|_| format!("source {} is not UTF-8", path.display()))?;
        sources.insert(name, text);
    }
    Ok(sources)
}

/// Compact selected intent declarations against canonical plan modules.
pub fn scoped_declarations(
    canonical: &BTreeMap<&str, &Vec<Value>>,
    sources: &BTreeMap<String, String>,
    selected: &Value,
) -> Result<Value, String> {
    let selected = selected
        .as_object()
        .ok_or_else(|| "intent context declarations must be an object".to_owned())?;
    let mut modules = Map::new();
    for (module, value) in selected {
        let selected_declarations = value
            .get("declarations")
            .and_then(Value::as_array)
            .ok_or_else(|| format!("module `{module}` declarations must be an array"))?;
        let canonical_declarations = canonical
            .get(module.as_str())
            .ok_or_else(|| format!("module `{module}` is not in the canonical plan"))?;
        let text = sources
            .get(module)
            .ok_or_else(|| format!("module `{module}` has no authored source"))?;
        let mut compacted = Vec::with_capacity(selected_declarations.len());
        for declaration in selected_declarations {
            let name = declaration
                .get("name")
                .and_then(Value::as_str)
                .ok_or_else(|| format!("selected declaration in module `{module}` has no name"))?;
            let canonical_declaration = lookup(canonical_declarations, name, module)?;
            let owner = format!("{module}::{name}");
            compacted.push(compact(canonical_declaration, text, &owner)?);
        }
        modules.insert(
            module.clone(),
            Value::Object(Map::from_iter([(
                "declarations".to_owned(),
                Value::Array(compacted),
            )])),
        );
    }
    Ok(Value::Object(modules))
}

fn lookup<'a>(declarations: &'a [Value], name: &str, module: &str) -> Result<&'a Value, String> {
    let mut found = None;
    for declaration in declarations {
        if declaration.get("name").and_then(Value::as_str) == Some(name) {
            if found.is_some() {
                return Err(format!(
                    "duplicate declaration `{name}` in canonical module `{module}`"
                ));
            }
            found = Some(declaration);
        }
    }
    found.ok_or_else(|| format!("declaration `{name}` is not in canonical module `{module}`"))
}

fn compact(value: &Value, text: &str, owner: &str) -> Result<Value, String> {
    match value {
        Value::Array(values) => {
            let mut compacted = Vec::with_capacity(values.len());
            for value in values {
                compacted.push(compact(value, text, owner)?);
            }
            Ok(Value::Array(compacted))
        }
        Value::Object(object) => {
            let mut compacted = Map::new();
            for (key, child) in object {
                if matches!(key.as_str(), "span" | "source_order" | "doc") {
                    continue;
                }
                if matches!(
                    key.as_str(),
                    "expression" | "guard" | "condition" | "refinement"
                ) {
                    if let Value::Object(inner) = child {
                        if let Some(span) = inner.get("span") {
                            compacted
                                .insert(key.clone(), Value::String(authored(text, span, owner)?));
                            continue;
                        }
                    }
                }
                compacted.insert(key.clone(), compact(child, text, owner)?);
            }
            Ok(Value::Object(compacted))
        }
        other => Ok(other.clone()),
    }
}

fn authored(text: &str, span: &Value, owner: &str) -> Result<String, String> {
    let malformed = || format!("malformed span in `{owner}`");
    let start = span
        .get("start_byte")
        .and_then(Value::as_u64)
        .and_then(|value| usize::try_from(value).ok())
        .ok_or_else(malformed)?;
    let end = span
        .get("end_byte")
        .and_then(Value::as_u64)
        .and_then(|value| usize::try_from(value).ok())
        .ok_or_else(malformed)?;
    if start > end
        || end > text.len()
        || !text.is_char_boundary(start)
        || !text.is_char_boundary(end)
    {
        return Err(malformed());
    }
    Ok(text[start..end].trim().to_owned())
}
