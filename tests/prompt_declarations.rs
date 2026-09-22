use std::path::Path;

use cott::compiler::{SourceFile, parse_project};
use cott::hir::lower;
use cott::ir::render;
use cott::prompt_declarations::{render_scoped_declarations, scoped_declarations};
use cott::python::artifact_plan::PythonArtifactPlan;
use serde_json::{Value, json};

fn surface(sources: &[(&str, &str)]) -> Value {
    // These are in-memory sources: prompt rendering cannot reopen their paths.
    let parsed = parse_project(
        sources
            .iter()
            .map(|(path, text)| SourceFile::new(*path, *text)),
    )
    .expect("parse semantic prompt fixture");
    let hir = lower(Path::new("unavailable"), parsed).expect("lower semantic prompt fixture");
    PythonArtifactPlan::from_ir(&render(&hir).expect("render canonical fixture"))
        .expect("project canonical fixture")
        .contract_surface()
}

fn declaration<'a>(modules: &'a Value, module: &str, name: &str) -> &'a Value {
    modules[module]["declarations"]
        .as_array()
        .expect("declarations")
        .iter()
        .find(|value| value["name"] == name)
        .expect("selected declaration")
}

fn misleading_diagnostics(value: &mut Value) {
    match value {
        Value::Array(values) => {
            for value in values {
                misleading_diagnostics(value);
            }
        }
        Value::Object(object) => {
            for value in object.values_mut() {
                misleading_diagnostics(value);
            }
            if object.contains_key("kind") || object.contains_key("pattern") {
                object.insert(
                    "span".to_owned(),
                    json!({"start_byte": 999999, "end_byte": 0}),
                );
                object.insert("source_order".to_owned(), json!(999999));
                object.insert(
                    "doc".to_owned(),
                    json!("misleading authored expression: false"),
                );
            }
        }
        _ => {}
    }
}

fn binding_symbol(pattern: &Value) -> Option<&str> {
    if pattern["kind"] == "binding" {
        pattern["symbol"].as_str()
    } else {
        pattern
            .get("arguments")?
            .as_array()?
            .iter()
            .find_map(binding_symbol)
    }
}

#[test]
fn applied_cross_module_rule_uses_resolved_substitution_not_source_locations() {
    let original = surface(&[
        (
            "unavailable/a.cott",
            r#"module a

enum Failure:
    Bad

const LIMIT: I32 = 4

rule Base[T]:
    ensures Result.Ok(T) => true

rule Concrete(Base[I32]):
    requires a.LIMIT > 0
"#,
        ),
        (
            "unavailable/b.cott",
            r#"module b

fn run() -> Result[I32, a.Failure]:
    rule a.Concrete
"#,
        ),
    ]);
    let context = cott::intent::context(&original, "b.run", b"").expect("select effective context");
    let selected = &context["declarations"];
    let before = selected.clone();
    let projected = scoped_declarations(selected).expect("render without sources or spans");
    let run = declaration(&projected, "b", "b.run");
    let clauses = run["contract"]["clauses"].as_array().expect("clauses");
    let ensures = clauses
        .iter()
        .find(|clause| clause["kind"] == "ensures")
        .unwrap();
    let pattern = ensures["guard"]["pattern"]
        .as_str()
        .expect("resolved pattern");
    assert!(pattern.contains("i32"));
    assert!(!pattern.contains("type_parameter"));
    let scrutinee = ensures["guard"]["scrutinee"].as_str().unwrap();
    assert!(scrutinee.contains("result_ref"));
    assert!(scrutinee.contains("a.Failure"));
    let requires = clauses
        .iter()
        .find(|clause| clause["kind"] == "requires")
        .unwrap();
    let predicate = requires["expression"].as_str().unwrap();
    assert!(predicate.contains("constant_ref"));
    assert!(predicate.contains("a.LIMIT"));
    assert!(predicate.contains("greater"));
    assert_eq!(
        declaration(&projected, "a", "a.LIMIT")["value"]["value"],
        "4"
    );
    assert_eq!(
        selected, &before,
        "presentation must not mutate fingerprint inputs"
    );

    let mut relocated = selected.clone();
    misleading_diagnostics(&mut relocated);
    assert_eq!(scoped_declarations(&relocated).unwrap(), projected);
}

#[test]
fn selected_impl_method_subset_is_not_reexpanded() {
    let original = surface(&[(
        "unavailable/counter.cott",
        r#"module counter

trait Counter:
    fn advance(self, amount: I32) -> I32
    fn read(self) -> I32

impl CounterState for Counter:
    state:
        count: I32 = 0
    invariant self.count >= 0
    fn advance(self, amount: I32) -> I32:
        requires amount > 0
        modifies self.count
        ensures old(self.count) + amount == self.count
    fn read(self) -> I32:
        ensures result == self.count
"#,
    )]);
    let mut implementation = declaration(&original, "counter", "counter.CounterState").clone();
    implementation["methods"]
        .as_array_mut()
        .unwrap()
        .retain(|method| method["name"] == "read");
    implementation["selected_methods"]
        .as_array_mut()
        .unwrap()
        .retain(|method| method["trait_method"].as_str().unwrap().ends_with(".read"));
    assert_eq!(implementation["methods"].as_array().unwrap().len(), 1);
    assert_eq!(
        implementation["selected_methods"].as_array().unwrap().len(),
        1
    );
    let selected = json!({"counter": {"declarations": [implementation]}});
    let projected = scoped_declarations(&selected).expect("render exact selected subset");
    let implementation = &projected["counter"]["declarations"][0];
    assert_eq!(implementation["methods"][0]["name"], "read");
    assert_eq!(implementation["methods"].as_array().unwrap().len(), 1);
    assert_eq!(
        implementation["selected_methods"].as_array().unwrap().len(),
        1
    );
    assert!(!projected.to_string().contains("advance"));
    assert!(!projected.to_string().contains("amount"));
    assert!(projected.to_string().contains("result_ref"));
    // Canonical state access identifies the field by its typed self base and
    // member name; neither node carries a standalone reference symbol.
    assert!(
        implementation["methods"][0]["contracts"]["ensures"][0]["expression"]
            .as_str()
            .unwrap()
            .contains(
                r#"field(base=self_ref(reference=null,type=named(args=[],name="counter.CounterState")),name="count",reference=null,type=primitive(name="i32"))"#
            )
    );
    let mut relocated = selected;
    misleading_diagnostics(&mut relocated);
    assert_eq!(scoped_declarations(&relocated).unwrap(), projected);
}

#[test]
fn guard_patterns_keep_the_symbols_used_by_their_predicates() {
    let original = surface(&[(
        "unavailable/guards.cott",
        r#"module guards

enum Failure:
    Missing
    Short(actual: Str)

fn inspect(label: Option[Str]) -> Result[Str, Failure]:
    ensures Result.Ok(text) => text.len > 0
    ensures Result.Err(Failure.Short(actual)) => actual.len == 0
    error Failure.Short with label matches Option.Some(input) when (input.len == 0)
"#,
    )]);
    let context = cott::intent::context(&original, "guards.inspect", b"").unwrap();
    let selected = &context["declarations"];
    let projected = scoped_declarations(selected).unwrap();
    let input = declaration(selected, "guards", "guards.inspect")["contract"]["clauses"]
        .as_array()
        .unwrap();
    let output = declaration(&projected, "guards", "guards.inspect")["contract"]["clauses"]
        .as_array()
        .unwrap();
    assert_eq!(output.len(), input.len());
    for (input, output) in input.iter().zip(output) {
        let symbol = binding_symbol(&input["guard"]["pattern"]).expect("guard binding");
        assert!(
            output["guard"]["pattern"]
                .as_str()
                .unwrap()
                .contains(symbol)
        );
        let predicate = if input["kind"] == "error" {
            "when"
        } else {
            "expression"
        };
        assert!(output[predicate].as_str().unwrap().contains(symbol));
        assert_eq!(output["clause_id"], input["clause_id"]);
        if input["kind"] == "error" {
            assert_eq!(output["variant"], "guards.Failure.Short");
            let parameter_symbol = input["guard"]["scrutinee"]["symbol"]
                .as_str()
                .expect("resolved guard parameter identity");
            assert!(
                output["guard"]["scrutinee"]
                    .as_str()
                    .unwrap()
                    .contains(&serde_json::to_string(parameter_symbol).unwrap())
            );
        }
    }
}

fn literal(value: Value, ty: Value) -> Value {
    json!({"kind": "literal", "reference": null, "type": ty, "value": value})
}

#[test]
fn literal_evidence_and_refinement_identity_survive_compaction() {
    let integer = json!({"kind": "integer", "value": "18446744073709551615"});
    let raw_json =
        json!({"span": "data", "doc": "data", "kind": "unknown-expression", "source_order": 17});
    let selected = json!({"values": {"declarations": [{
        "kind": "newtype", "name": "values.Exact", "doc": "intent only",
        "refinement": {
            "identity": "values.Exact.refinement", "clause_id": 42,
            "expression": {
                "kind": "comparison_chain", "reference": null,
                "type": {"kind": "primitive", "name": "bool"},
                "operands": [literal(integer.clone(), json!({"kind": "primitive", "name": "u64"})),
                    literal(integer.clone(), json!({"kind": "primitive", "name": "u64"}))],
                "operators": ["equal"]
            }
        },
        "constants": [
            literal(json!({"kind": "f32", "bits": "80000000"}), json!({"kind": "primitive", "name": "f32"})),
            literal(json!({"kind": "f64", "bits": "8000000000000000"}), json!({"kind": "primitive", "name": "f64"})),
            literal(json!({"kind": "enum", "variant": "values.Token.Some", "fields": [integer.clone()]}),
                json!({"kind": "named", "name": "values.Token", "args": []})),
            literal(json!({"kind": "json", "value": raw_json.clone()}), json!({"kind": "primitive", "name": "json"}))
        ],
        "fields": [{"name": "maximum", "default": integer}],
        "json_default": {"kind": "json", "value": raw_json.clone()}
    }]}});
    let projected = scoped_declarations(&selected).unwrap();
    let rendered = render_scoped_declarations(&selected).unwrap();
    assert_eq!(
        serde_json::from_str::<Value>(&rendered).unwrap(),
        projected,
        "minified prompt JSON must preserve the complete projection"
    );
    assert!(rendered.len() < serde_json::to_string_pretty(&projected).unwrap().len());
    let declaration = &projected["values"]["declarations"][0];
    assert_eq!(
        declaration["refinement"]["identity"],
        "values.Exact.refinement"
    );
    assert_eq!(declaration["refinement"]["clause_id"], 42);
    assert!(
        declaration["refinement"]["expression"]
            .as_str()
            .unwrap()
            .contains("18446744073709551615")
    );
    let constants = declaration["constants"].as_array().unwrap();
    assert!(constants[0].as_str().unwrap().contains("80000000"));
    assert!(constants[1].as_str().unwrap().contains("8000000000000000"));
    assert!(constants[2].as_str().unwrap().contains("values.Token.Some"));
    assert!(
        constants[2]
            .as_str()
            .unwrap()
            .contains("18446744073709551615")
    );
    assert!(
        constants[3]
            .as_str()
            .unwrap()
            .contains(&raw_json.to_string())
    );
    assert_eq!(declaration["json_default"]["value"], raw_json);
    assert_eq!(
        declaration["fields"][0]["default"]["value"],
        "18446744073709551615"
    );
    assert!(declaration.get("doc").is_none());
}

#[test]
fn unknown_nested_expression_fails_closed_without_source_fallback() {
    let selected = json!({"app": {"declarations": [{
        "kind": "function", "name": "app.run", "contract": {"clauses": [{
            "kind": "ensures", "clause_id": 0, "guard": null,
            "expression": {
                "kind": "unary", "op": "not", "reference": null,
                "type": {"kind": "primitive", "name": "bool"},
                "operand": {"kind": "future_expression", "span": {"start_byte": 0, "end_byte": 4}}
            }
        }]}
    }]}});
    assert!(
        scoped_declarations(&selected)
            .unwrap_err()
            .contains("future_expression")
    );
}
