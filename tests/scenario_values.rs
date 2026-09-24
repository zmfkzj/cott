use std::path::Path;

use cott::compiler::{SourceFile, parse_project};
use cott::formatter::format;
use cott::parser::parse_cst;
use cott::syntax::Cst;
use serde_json::Value;

const TYPES: &str = r#"module demo

enum Mode:
    Fast
    Careful(retries: U8)

newtype Port(U16)
    where 1 <= self

struct Limits:
    timeout_ms: U32
    tags: List[Str]
    port: Port

    invariant self.timeout_ms > 0

struct Request:
    name: Str
    mode: Mode
    limits: Limits
    labels: Map[Str, U32]
    note: Option[Str]
    input: Path

enum Failure:
    Rejected(reason: Str)

struct Report:
    name: Str
    retries: U8

fn run(request: Request) -> Result[Report, Failure]:
    ensures Result.Ok(report) => report.retries >= 0

    error Failure.Rejected
"#;

fn lower(source: &str) -> Result<Vec<Value>, Vec<String>> {
    let parsed = parse_project([SourceFile::new("src/demo.cott", source)]).map_err(|errors| {
        errors
            .into_iter()
            .map(|error| error.diagnostic.message)
            .collect::<Vec<_>>()
    })?;
    let hir = cott::hir::lower(Path::new("src"), parsed).map_err(|errors| {
        errors
            .into_iter()
            .map(|error| error.diagnostic.message)
            .collect::<Vec<_>>()
    })?;
    let ir = cott::ir::render(&hir).expect("scenario values render schema-valid canonical IR");
    Ok(ir
        .modules
        .iter()
        .map(|module| serde_json::from_slice(&module.bytes).expect("canonical JSON"))
        .collect())
}

fn scenario(source: &str, name: &str) -> Value {
    let modules = lower(source).unwrap_or_else(|errors| panic!("{errors:?}"));
    modules[0]["declarations"]
        .as_array()
        .expect("declarations")
        .iter()
        .find(|declaration| declaration["name"] == format!("demo.scenario.{name}"))
        .cloned()
        .expect("scenario declaration")
}

fn rejected(source: &str, message: &str) {
    let errors = lower(source).expect_err("source must be rejected");
    assert!(
        errors.iter().any(|error| error.contains(message)),
        "expected `{message}` in {errors:?}"
    );
}

const VALID: &str = r#"
data base_limits: Limits = Limits(timeout_ms: 30, tags: List("a", "b"), port: Port(8080))

data request_template: Request = Request(
    name: "job",
    mode: Mode.Careful(retries: 2),
    limits: base_limits,
    labels: Map("x": 1),
    note: Option.Some(value: "n"),
    input: files.path("input.txt"),
)

scenario nested_request:
    fixtures:
        fs files:
            file "input.txt" text("x")
    data request: Request = Request(
        name: "local",
        mode: Mode.Fast,
        limits: Limits(timeout_ms: 5, tags: List(), port: Port(1)),
        labels: Map(),
        note: Option.Nothing,
        input: files.path("input.txt"),
    )
    call first = run(request)
    call second = run(request_template)
    assert first matches Result.Ok(report) => report.retries == 0
    assert second == Result.Ok(value: Report(name: "job", retries: 2))
"#;

#[test]
fn formatted_nested_call_arguments_remain_parseable() {
    let source = format!("{TYPES}{VALID}").replace(
        "call first = run(request)",
        "call first = run(Request(name: \"local\", mode: Mode.Fast, limits: Limits(timeout_ms: 5, tags: List(), port: Port(1)), labels: Map(), note: Option.Nothing, input: files.path(\"input.txt\")))",
    );
    lower(&source).expect("unformatted scenario is valid");
    let cst = Cst::parse(&source).expect("lex nested invocation");
    let ast = parse_cst(&cst).expect("parse nested invocation");
    let formatted =
        String::from_utf8(format(&cst, &ast).expect("format nested invocation")).expect("UTF-8");
    lower(&formatted).expect("formatter output remains a valid typed scenario");
    let cst = Cst::parse(&formatted).expect("lex formatted invocation");
    let ast = parse_cst(&cst).expect("parse formatted invocation");
    assert_eq!(
        String::from_utf8(format(&cst, &ast).expect("format again")).expect("UTF-8"),
        formatted,
        "nested invocations are idempotent"
    );
}

#[test]
fn nested_values_lower_to_closed_canonical_constructors() {
    let scenario = scenario(&format!("{TYPES}{VALID}"), "nested_request");
    let steps = scenario["steps"].as_array().expect("steps");
    assert_eq!(
        steps
            .iter()
            .map(|step| step["kind"].as_str().unwrap())
            .collect::<Vec<_>>(),
        ["data", "call", "call", "assert", "assert"]
    );
    assert_eq!(steps[0]["binding"], "demo.scenario.nested_request.request");
    let request = &steps[0]["expression"];
    assert_eq!(request["kind"], "construct");
    assert_eq!(request["symbol"], "demo.Request");
    let fields = request["fields"].as_array().expect("fields");
    assert_eq!(
        fields
            .iter()
            .map(|field| field["name"].as_str().unwrap())
            .collect::<Vec<_>>(),
        ["name", "mode", "limits", "labels", "note", "input"],
        "fields are canonical declaration order"
    );
    assert_eq!(fields[1]["value"]["kind"], "enum_singleton_ref");
    assert_eq!(
        fields[2]["value"]["fields"][2]["value"]["kind"],
        "construct"
    );
    assert_eq!(
        fields[2]["value"]["fields"][2]["value"]["symbol"],
        "demo.Port"
    );
    assert_eq!(fields[5]["value"]["kind"], "fixture_path");
    assert_eq!(
        fields[5]["value"]["fixture"],
        "demo.scenario.nested_request.fixture.files"
    );
    // The first call uses the data step binding: evaluated once, never re-built.
    assert_eq!(steps[1]["arguments"][0]["kind"], "binding_ref");
    // Module data is a closed template inlined per use with rebound fixtures.
    let template = &steps[2]["arguments"][0];
    assert_eq!(template["kind"], "construct");
    assert_eq!(template["fields"][1]["value"]["kind"], "variant");
    assert_eq!(
        template["fields"][1]["value"]["symbol"],
        "demo.Mode.Careful"
    );
    assert_eq!(
        template["fields"][1]["value"]["fields"][0]["type"]["name"],
        "u8"
    );
    assert_eq!(template["fields"][3]["value"]["kind"], "map");
    assert_eq!(template["fields"][4]["value"]["kind"], "option_some");
    assert_eq!(
        template["fields"][5]["value"]["fixture"],
        "demo.scenario.nested_request.fixture.files"
    );
    let guarded = &steps[3]["expression"];
    assert_eq!(guarded["kind"], "match");
    assert_eq!(guarded["pattern"]["kind"], "result_ok");
    assert_eq!(guarded["condition"]["kind"], "comparison_chain");
    let expected = &steps[4]["expression"]["operands"][1];
    assert_eq!(expected["kind"], "result_ok");
    assert_eq!(expected["payload"]["symbol"], "demo.Report");
    assert_eq!(expected["type"]["kind"], "result");
}

#[test]
fn rejects_unknown_missing_duplicate_and_positional_fields() {
    for (step, message) in [
        (
            "    data value: Report = Report(name: \"x\", retries: 1, extra: 2)",
            "unknown field `extra` for `Report`",
        ),
        (
            "    data value: Report = Report(name: \"x\")",
            "missing field `retries` for `Report`",
        ),
        (
            "    data value: Report = Report(name: \"x\", name: \"y\", retries: 1)",
            "duplicate field `name` for `Report`",
        ),
        (
            "    data value: Report = Report(\"x\", 1)",
            "`Report` values require `field: value` arguments",
        ),
        (
            "    data value: Mode = Mode.Careful(tries: 2)",
            "unknown field `tries` for `Mode.Careful`",
        ),
        (
            "    data value: Mode = Mode.Fast()",
            "payloadless variant `Mode.Fast` takes no arguments",
        ),
        (
            "    data value: Report = Report(name: \"x\", retries: 300)",
            "numeric literal does not fit its expected type",
        ),
        (
            "    data value: Port = Port(0)",
            "newtype value does not satisfy the `Port` refinement",
        ),
        (
            "    data value: Report = Limits(timeout_ms: 1, tags: List(), port: Port(1))",
            "scenario data does not match its declared type",
        ),
        (
            "    data value: Report = run(Report(name: \"x\", retries: 1))",
            "scenario values construct only structs, newtypes, enum variants and standard containers",
        ),
    ] {
        rejected(
            &format!("{TYPES}\nscenario invalid:\n{step}\n    tick\n"),
            message,
        );
    }
}

#[test]
fn pattern_bindings_stay_clause_local() {
    rejected(
        &format!(
            "{TYPES}\ndata base: Report = Report(name: \"x\", retries: 1)\n\nscenario leak:\n    data outcome: Result[Report, Failure] = Result.Ok(value: base)\n    assert outcome matches Result.Ok(report) => report.retries == 1\n    assert report.retries == 1\n"
        ),
        "unknown type or declaration `report.retries`",
    );
    rejected(
        &format!(
            "{TYPES}\ndata base: Report = Report(name: \"x\", retries: 1)\n\nscenario shadow:\n    data outcome: Result[Report, Failure] = Result.Ok(value: base)\n    assert outcome matches Result.Ok(base) => base.retries == 1\n"
        ),
        "pattern binding `base` shadows scenario data",
    );
}

#[test]
fn module_data_is_checked_unused_and_per_scenario_fixture_authority() {
    rejected(
        &format!("{TYPES}\ndata unused: Report = Report(name: \"x\", retries: 1, bogus: 1)\n"),
        "unknown field `bogus` for `Report`",
    );
    rejected(
        &format!("{TYPES}\ndata loop_a: Report = loop_b\n\ndata loop_b: Report = loop_a\n"),
        "depends on itself",
    );
    rejected(
        &format!(
            "{TYPES}\ndata needs_files: Path = files.path(\"a.txt\")\n\nscenario missing:\n    data path: Path = needs_files\n    tick\n"
        ),
        "scenario data `needs_files` requires fixture `files`, which this scenario does not declare",
    );
}

#[test]
fn value_constructors_are_unavailable_outside_scenarios() {
    let source =
        format!("{TYPES}\nconst DEFAULT_REPORT: Report = Report(name: \"x\", retries: 1)\n");
    assert!(parse_project([SourceFile::new("src/demo.cott", &source)]).is_err());
}

#[test]
fn formats_nested_scenario_values_idempotently() {
    let source = format!("{TYPES}{VALID}");
    let once = {
        let cst = Cst::parse(&source).expect("lex");
        let ast = parse_cst(&cst).expect("parse");
        String::from_utf8(format(&cst, &ast).expect("format")).expect("UTF-8")
    };
    let twice = {
        let cst = Cst::parse(&once).expect("lex formatted");
        let ast = parse_cst(&cst).expect("parse formatted");
        String::from_utf8(format(&cst, &ast).expect("format")).expect("UTF-8")
    };
    assert_eq!(once, twice);
    assert!(once.contains("    data request: Request = Request(\n        name: \"local\",\n"));
    assert!(
        once.contains("    assert second == Result.Ok(value: Report(name: \"job\", retries: 2))\n")
    );
    assert!(once.contains("    assert first matches Result.Ok(report) => report.retries == 0\n"));
    let formatted = scenario(&once, "nested_request");
    let original = scenario(&source, "nested_request");
    assert_eq!(
        formatted["steps"].as_array().map(Vec::len),
        original["steps"].as_array().map(Vec::len)
    );
}
