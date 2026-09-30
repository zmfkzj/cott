use super::*;
pub(super) fn render(plan: &RustPlan, d: &Value) -> Result<String, String> {
    let name = escape_identifier(local_name(text(d, "name")?))?;
    let recursive = layout::metadata_recursive(plan, text(d, "name")?);
    let (g, a) = generics(d)?;
    let w = where_constraints(plan, d)?;
    let mut variants = Vec::new();
    let mut arms = Vec::new();
    let mut snapshots = Vec::new();
    let mut validation = Vec::new();
    let mut deep = Vec::new();
    let fields = list(d, "variants")
        .iter()
        .flat_map(|v| list(v, "fields"))
        .cloned()
        .collect::<Vec<_>>();
    let phantom = list(d, "generics")
        .iter()
        .filter(|g| {
            !fields
                .iter()
                .any(|f| contains_type_parameter(f, local_name(text(g, "name").unwrap_or(""))))
        })
        .map(|g| escape_identifier(local_name(text(g, "name")?)))
        .collect::<Result<Vec<_>, _>>()?;
    for variant in list(d, "variants") {
        let n = escape_identifier(local_name(text(variant, "name")?))?;
        let fields = list(variant, "fields")
            .iter()
            .map(|f| render_type_scoped(plan, f.get("type").unwrap_or(f), d))
            .collect::<Result<Vec<_>, _>>()?;
        variants.push(if fields.is_empty() {
            n.clone()
        } else {
            format!("{n}({})", fields.join(", "))
        });
        validation.extend(
            fields
                .iter()
                .map(|t| format!("<{t} as crate::cott_runtime::Value>::NEEDS_VALIDATION")),
        );
        deep.extend(
            fields
                .iter()
                .map(|t| format!("<{t} as crate::cott_runtime::Value>::DEEP_SNAPSHOT")),
        );
        let args = (0..fields.len())
            .map(|i| format!("__cott_v{i}"))
            .collect::<Vec<_>>();
        arms.push(if args.is_empty() {
            format!("Self::{n}=>{{}}")
        } else {
            format!(
                "Self::{n}({})=>{{ {} }}",
                args.join(", "),
                args.iter()
                    .map(|v| format!("crate::cott_runtime::Value::validate({v});"))
                    .collect::<String>()
            )
        });
        snapshots.push(if args.is_empty() {
            format!("Self::{n}=>Self::{n}")
        } else {
            format!(
                "Self::{n}({})=>Self::{n}({})",
                args.join(", "),
                args.iter()
                    .map(|v| format!("crate::cott_runtime::Value::__cott_snapshot({v})"))
                    .collect::<Vec<_>>()
                    .join(", ")
            )
        });
    }
    if !phantom.is_empty() {
        variants.push(format!("#[doc(hidden)] __cott_marker(std::marker::PhantomData<({},)>,crate::cott_runtime::Never)",phantom.join(", ")));
        arms.push("Self::__cott_marker(_,never)=>match *never{}".into());
        snapshots.push("Self::__cott_marker(_,never)=>match *never{}".into());
    }
    let copy = fields.is_empty() && phantom.is_empty();
    let mut out = format!(
        "#[derive(Clone,{}Debug,PartialEq)]\npub enum {name}{g}{w}{{ {} }}\n",
        if copy { "Copy," } else { "" },
        variants.join(", ")
    );
    writeln!(
        out,
        "impl{g} crate::cott_sealed::Sealed for {name}{a}{w}{{}}"
    )
    .unwrap();
    writeln!(out,"impl{g} crate::cott_runtime::Value for {name}{a}{w} {{\nconst NEEDS_VALIDATION:bool={};\nconst DEEP_SNAPSHOT:bool={};\nfn validate(&self) {{ match self {{ {} }} }}\nfn __cott_snapshot(&self)->Self {{ match self {{ {} }} }}\n}}",if recursive{"true".into()}else if validation.is_empty(){"false".into()}else{validation.join(" || ")},if recursive{"true".into()}else if deep.is_empty(){"false".into()}else{deep.join(" || ")},arms.join(", "),snapshots.join(", ")).unwrap();
    writeln!(out,"impl{g} crate::cott_runtime::ConstructionArguments for {name}{a}{w}{{type Arguments=Self;}}\nimpl{g} crate::cott_runtime::Constructible for {name}{a}{w}{{fn construct(value:Self)->Self{{crate::cott_runtime::Value::validate(&value);value}}}}").unwrap();
    Ok(out)
}
