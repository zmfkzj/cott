use super::*;

/// Inline cycles require Box; heap-container cycles already have finite physical layout.
pub(super) fn recursive(plan: &RustPlan, name: &str) -> bool {
    cycle(plan, name, false)
}
/// Metadata flags must break recursive evaluation even across Vec/Map/Array indirection.
pub(super) fn metadata_recursive(plan: &RustPlan, name: &str) -> bool {
    cycle(plan, name, true)
}
fn cycle(plan: &RustPlan, name: &str, heap: bool) -> bool {
    fn reaches(
        plan: &RustPlan,
        ty: &Value,
        target: &str,
        seen: &mut BTreeSet<String>,
        heap: bool,
    ) -> bool {
        match ty["kind"].as_str() {
            Some("named") => {
                let Some(name) = ty.get("name").and_then(Value::as_str) else {
                    return false;
                };
                if name == target {
                    return true;
                }
                if !seen.insert(ty.to_string()) {
                    return false;
                }
                let Some(d) = declaration_named(plan, name) else {
                    return false;
                };
                let d = type_context::instantiate(d, d, ty).unwrap_or_else(|_| d.clone());
                match d["kind"].as_str() {
                    Some("alias") => reaches(plan, &d["target"], target, seen, heap),
                    Some("newtype") => reaches(plan, &d["carrier"], target, seen, heap),
                    Some("struct") => list(&d, "fields")
                        .iter()
                        .any(|f| reaches(plan, &f["type"], target, seen, heap)),
                    Some("enum") => list(&d, "variants")
                        .iter()
                        .flat_map(|v| list(v, "fields"))
                        .any(|f| reaches(plan, &f["type"], target, seen, heap)),
                    _ => false,
                }
            }
            Some("option") => reaches(plan, &ty["item"], target, seen, heap),
            Some("result") => {
                reaches(plan, &ty["ok"], target, seen, heap)
                    || reaches(plan, &ty["error"], target, seen, heap)
            }
            Some("tuple") => list(ty, "items")
                .iter()
                .any(|t| reaches(plan, t, target, seen, heap)),
            Some("list" | "set" | "array") if heap => {
                reaches(plan, &ty["item"], target, seen, heap)
            }
            Some("map") if heap => {
                reaches(plan, &ty["key"], target, seen, heap)
                    || reaches(plan, &ty["value"], target, seen, heap)
            }
            _ => false,
        }
    }
    let Some(d) = declaration_named(plan, name) else {
        return false;
    };
    let mut seen = BTreeSet::new();
    match d["kind"].as_str() {
        Some("newtype") => reaches(plan, &d["carrier"], name, &mut seen, heap),
        Some("struct") => list(d, "fields")
            .iter()
            .any(|f| reaches(plan, &f["type"], name, &mut seen, heap)),
        Some("enum") => list(d, "variants")
            .iter()
            .flat_map(|v| list(v, "fields"))
            .any(|f| reaches(plan, &f["type"], name, &mut seen, heap)),
        _ => false,
    }
}
pub(super) fn raw_type(plan: &RustPlan, ty: &Value, scope: &Value) -> Result<String, String> {
    let rendered = render_type_scoped(plan, ty, scope)?;
    if ty["kind"] == "named"
        && ty
            .get("name")
            .and_then(Value::as_str)
            .is_some_and(|n| recursive(plan, n))
    {
        Ok(rendered
            .strip_prefix("Box<")
            .and_then(|s| s.strip_suffix('>'))
            .ok_or("invalid recursive native projection")?
            .to_owned())
    } else {
        Ok(rendered)
    }
}
