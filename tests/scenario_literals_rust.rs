#![allow(dead_code)]
#[path = "support/rust_verification.rs"]
mod native;
use native::{Fixture, current, scenario, stderr};
const CONTRACT: &str = r#"module demo.runner

const SIZE: U32 = 2

fn echo_bytes(payload: Bytes) -> Bytes
fn describe(value: JsonValue) -> Str
fn echo_json(value: JsonValue) -> JsonValue
fn total(items: Array[U8, SIZE]) -> U32
fn flip(data: Buffer[SIZE]) -> Buffer[SIZE]

scenario literals:
    call raw = echo_bytes(Bytes("6869"))
    assert raw == Bytes("6869")
    call float_kind = describe(JsonValue.Float(value: 1))
    assert float_kind == "float"
    call integer_kind = describe(JsonValue.Integer(value: 1))
    assert integer_kind == "integer"
    data document: JsonValue = JsonValue.Object(value: Map(
        "items": JsonValue.Array(value: List(JsonValue.Null, JsonValue.Boolean(value: false), JsonValue.String(value: "x"), JsonValue.Float(value: -0.5), JsonValue.Array(value: List()))),
        "n": JsonValue.Integer(value: -7),
        "empty": JsonValue.Object(value: Map()),
    ))
    call echoed = echo_json(document)
    assert echoed == JsonValue.Object(value: Map(
        "n": JsonValue.Integer(value: -7),
        "empty": JsonValue.Object(value: Map()),
        "items": JsonValue.Array(value: List(JsonValue.Null, JsonValue.Boolean(value: false), JsonValue.String(value: "x"), JsonValue.Float(value: -0.5), JsonValue.Array(value: List()))),
    ))
    call sum = total(Array(3, 4))
    assert sum == 7
    call flipped = flip(Buffer("0102"))
    assert flipped == Buffer("0201")
"#;
fn fixture(echo: &str, flip: &str) -> Fixture {
    Fixture::new(
        "literal-values",
        CONTRACT,
        &[
            ("demo.runner.echo_bytes", "payload", ""),
            (
                "demo.runner.describe",
                "match value {crate::cott_runtime::JsonValue::Null=>\"null\",crate::cott_runtime::JsonValue::Bool(_)=>\"boolean\",crate::cott_runtime::JsonValue::Integer(_)=>\"integer\",crate::cott_runtime::JsonValue::Number(_)=>\"float\",crate::cott_runtime::JsonValue::String(_)=>\"string\",crate::cott_runtime::JsonValue::Array(_)=>\"array\",crate::cott_runtime::JsonValue::Object(_)=>\"object\"}.to_owned()",
                "",
            ),
            ("demo.runner.echo_json", echo, ""),
            (
                "demo.runner.total",
                "items.into_vec().into_iter().map(u32::from).sum()",
                "",
            ),
            ("demo.runner.flip", flip, ""),
        ],
        "",
    )
}
#[test]
#[ignore = "requires COTT_CARGO and real native sandbox"]
fn native_bytes_json_and_const_sized_arrays_buffers_preserve_literal_values() {
    let fixture = fixture(
        "value",
        "crate::cott_runtime::Buffer::new(data.iter().rev().copied().collect())",
    );
    fixture.emit();
    let record = fixture.verify();
    let event = scenario(&record, "demo.runner.scenario.literals");
    assert_eq!(event["status"], "passed");
    assert_eq!(event["assertions"], 6);
    assert_eq!(event["cleaned"], true);
}
#[test]
#[ignore = "requires COTT_CARGO and real native sandbox"]
fn native_scenario_assertions_reject_wrong_json_and_buffer_values() {
    for (echo, flip) in [
        (
            "let _=value;crate::cott_runtime::JsonValue::Null",
            "crate::cott_runtime::Buffer::new(data.iter().rev().copied().collect())",
        ),
        ("value", "data"),
    ] {
        let fixture = fixture(echo, flip);
        fixture.emit();
        let result = fixture.run(&["verify"]);
        assert_eq!(result.status.code(), Some(4), "{}", stderr(&result));
        assert_eq!(current(&fixture.record())["verified"], false);
    }
}
