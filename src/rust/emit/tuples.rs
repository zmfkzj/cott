use super::*;

pub(super) fn runtime_projection(plan: &RustPlan) -> Result<String, String> {
    fn collect(value: &Value, arities: &mut BTreeSet<usize>) {
        match value {
            Value::Array(a) => {
                for v in a {
                    collect(v, arities)
                }
            }
            Value::Object(o) => {
                if o.get("kind").and_then(Value::as_str) == Some("tuple") {
                    if let Some(items) = o.get("items").and_then(Value::as_array) {
                        if items.len() > 12 {
                            arities.insert(items.len());
                        }
                    }
                }
                for (k, v) in o {
                    if k != "span" {
                        collect(v, arities)
                    }
                }
            }
            _ => {}
        }
    }
    let mut arities = BTreeSet::new();
    for module in &plan.modules {
        for declaration in &module.declarations {
            collect(declaration, &mut arities)
        }
    }
    let mut out = String::new();
    for arity in arities {
        let names = (0..arity).map(|i| format!("T{i}")).collect::<Vec<_>>();
        let args = names.join(", ");
        let bounds = names
            .iter()
            .map(|n| format!("{n}:Value+Clone"))
            .collect::<Vec<_>>()
            .join(", ");
        writeln!(
            out,
            "#[derive(Clone,Debug,PartialEq)]\npub struct Tuple{arity}<{args}>({});",
            names
                .iter()
                .map(|n| format!("pub {n}"))
                .collect::<Vec<_>>()
                .join(", ")
        )
        .unwrap();
        writeln!(
            out,
            "impl<{bounds}> crate::cott_sealed::Sealed for Tuple{arity}<{args}>{{}}"
        )
        .unwrap();
        writeln!(out,"impl<{bounds}> Value for Tuple{arity}<{args}>{{const NEEDS_VALIDATION:bool={};const DEEP_SNAPSHOT:bool={};fn validate(&self){{{}}}fn __cott_snapshot(&self)->Self{{Self({})}}}}",names.iter().map(|n|format!("{n}::NEEDS_VALIDATION")).collect::<Vec<_>>().join(" || "),names.iter().map(|n|format!("{n}::DEEP_SNAPSHOT")).collect::<Vec<_>>().join(" || "),(0..arity).map(|i|format!("if T{i}::NEEDS_VALIDATION{{self.{i}.validate();}}")).collect::<String>(),(0..arity).map(|i|format!("self.{i}.__cott_snapshot()")).collect::<Vec<_>>().join(", ")).unwrap();
        writeln!(out,"impl<{bounds}> ConstructionArguments for Tuple{arity}<{args}>{{type Arguments=Self;}}\nimpl<{bounds}> Constructible for Tuple{arity}<{args}>{{fn construct(value:Self)->Self{{value.validate();value}}}}").unwrap();
    }
    Ok(out)
}
