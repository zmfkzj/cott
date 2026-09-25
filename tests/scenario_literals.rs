//! Closed scenario literals for ABI values without a struct constructor:
//! `Bytes("hex")`, §12.5 `JsonValue` variants, and Array/Buffer values whose
//! length is a named or arithmetic constant.

use std::path::Path;

use cott::compiler::{SourceFile, parse_project};
use serde_json::Value;

const TYPES: &str = r#"module demo

const SIZE: U32 = 2

const DOUBLE: U32 = SIZE * 2

const MINUS_ONE: I64 = -1

fn digest(payload: Bytes) -> Bytes

fn inspect(value: JsonValue) -> JsonValue

fn total(items: Array[U8, SIZE]) -> U32

fn pack(data: Buffer[SIZE]) -> U32

fn wide(data: Buffer[DOUBLE + 1]) -> U32
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
    let ir = cott::ir::render(&hir).expect("scenario literals render schema-valid canonical IR");
    Ok(ir
        .modules
        .iter()
        .map(|module| serde_json::from_slice(&module.bytes).expect("canonical JSON"))
        .collect())
}

fn steps(scenarios: &str) -> Vec<Value> {
    let modules =
        lower(&format!("{TYPES}{scenarios}")).unwrap_or_else(|errors| panic!("{errors:?}"));
    modules[0]["declarations"]
        .as_array()
        .expect("declarations")
        .iter()
        .find(|declaration| declaration["kind"] == "scenario")
        .and_then(|scenario| scenario["steps"].as_array().cloned())
        .expect("scenario steps")
}

fn rejected(scenario: &str, message: &str) {
    let errors =
        lower(&format!("{TYPES}\nscenario s:\n{scenario}\n")).expect_err("source must be rejected");
    assert!(
        errors.iter().any(|error| error.contains(message)),
        "expected `{message}` in {errors:?}"
    );
}

fn literal(expression: &Value) -> &Value {
    assert_eq!(expression["kind"], "literal", "{expression}");
    &expression["value"]
}

#[test]
fn bytes_literals_lower_to_canonical_bytes_values() {
    let steps = steps(
        r#"
scenario bytes_root:
    data raw: Bytes = Bytes("6869")
    call empty = digest(Bytes(""))
    call echoed = digest(raw)
    assert echoed == Bytes("00ff")
"#,
    );
    assert_eq!(
        literal(&steps[0]["expression"]),
        &serde_json::json!({"kind": "bytes", "value": "6869"})
    );
    assert_eq!(steps[0]["expression"]["type"]["name"], "bytes");
    assert_eq!(literal(&steps[1]["arguments"][0])["value"], "");
    assert_eq!(steps[2]["arguments"][0]["kind"], "binding_ref");
    assert_eq!(
        literal(&steps[3]["expression"]["operands"][1])["value"],
        "00ff"
    );
}

#[test]
fn bytes_values_reject_strings_buffers_and_malformed_hex() {
    for (step, message) in [
        (
            "    call out = digest(\"hi\")",
            "Str does not convert to Bytes, write `Bytes(\"<lowercase hex>\")`",
        ),
        (
            "    call out = digest(Buffer(\"6869\"))",
            "`Buffer(...)` requires an expected Buffer type; write `Bytes(\"<lowercase hex>\")` for Bytes",
        ),
        (
            "    call out = pack(Bytes(\"0102\"))",
            "scenario argument does not match callable parameter type",
        ),
        (
            "    call out = digest(Bytes(\"ABCD\"))",
            "Bytes hex must contain lowercase hexadecimal byte pairs",
        ),
        (
            "    call out = digest(Bytes(\"abc\"))",
            "Bytes hex must contain lowercase hexadecimal byte pairs",
        ),
        (
            "    call out = digest(Bytes(value: \"ab\"))",
            "`Bytes(...)` requires one lowercase hexadecimal string",
        ),
        (
            "    call out = digest(Bytes(\"ab\", \"cd\"))",
            "`Bytes(...)` requires one lowercase hexadecimal string",
        ),
    ] {
        rejected(step, message);
    }
}

#[test]
fn json_constructors_lower_to_one_canonical_json_literal() {
    let steps = steps(
        r#"
data member: JsonValue = JsonValue.String(value: "x")

scenario documents:
    call out = inspect(JsonValue.Object(value: Map(
        "b": JsonValue.Array(value: List(
            JsonValue.Integer(value: MINUS_ONE),
            JsonValue.Float(value: 1),
            JsonValue.Float(value: -0.0),
            JsonValue.Float(value: 0.1),
            JsonValue.Null,
        )),
        "a": JsonValue.Boolean(value: true),
        "c": JsonValue.Object(value: Map()),
        "d": JsonValue.Array(value: List(member)),
    )))
    assert out == JsonValue.Null
    assert out != JsonValue.Integer(value: -9223372036854775808)
"#,
    );
    let document = literal(&steps[0]["arguments"][0]);
    assert_eq!(document["kind"], "json");
    assert_eq!(steps[0]["arguments"][0]["type"]["name"], "json");
    let payload = &document["value"];
    assert_eq!(
        payload.as_object().unwrap().keys().collect::<Vec<_>>(),
        ["a", "b", "c", "d"],
        "object members are canonical map keys"
    );
    assert_eq!(payload["a"], true);
    let items = payload["b"].as_array().expect("array payload");
    assert!(items[0].is_i64() && items[0] == -1, "{items:?}");
    assert!(
        items[1].is_f64() && items[1] == 1.0,
        "a Float stays a float: {items:?}"
    );
    let negative_zero = items[2].as_f64().expect("f64");
    assert!(negative_zero == 0.0 && negative_zero.is_sign_negative());
    assert_eq!(items[3].as_f64().map(f64::to_bits), Some(0.1f64.to_bits()));
    assert!(items[4].is_null());
    assert_eq!(payload["c"], serde_json::json!({}));
    assert_eq!(
        payload["d"],
        serde_json::json!(["x"]),
        "module data is inlined"
    );
    assert_eq!(
        literal(&steps[1]["expression"]["operands"][1]),
        &serde_json::json!({"kind": "json", "value": null})
    );
    assert_eq!(
        literal(&steps[2]["expression"]["operands"][1])["value"],
        i64::MIN
    );
}

#[test]
fn json_constructors_reject_out_of_domain_and_runtime_payloads() {
    for (step, message) in [
        (
            "    call out = inspect(JsonValue.Integer(value: 9223372036854775808))",
            "numeric literal does not fit its expected type",
        ),
        (
            "    call out = inspect(JsonValue.Float(value: 1e999))",
            "numeric literal does not fit its expected type",
        ),
        (
            "    call out = inspect(JsonValue.Integer(value: 1.5))",
            "numeric literal does not fit its expected type",
        ),
        (
            "    call out = inspect(JsonValue.String(value: 1))",
            "scenario value does not match its variant field type",
        ),
        (
            "    call out = inspect(JsonValue.Number(value: 1))",
            "unknown JsonValue variant `Number`",
        ),
        (
            "    call out = inspect(JsonValue.Null())",
            "payloadless variant `JsonValue.Null` takes no arguments",
        ),
        (
            "    call out = inspect(JsonValue.Integer(1))",
            "`JsonValue.Integer` requires exactly one `value: ...` argument",
        ),
        (
            "    call out = inspect(JsonValue.String)",
            "`JsonValue.String` requires exactly one `value: ...` argument",
        ),
        (
            "    call out = inspect(JsonValue(value: 1))",
            "JsonValue scenario values name one variant",
        ),
        (
            "    call out = inspect(JsonValue.Object(value: Map(\"a\": JsonValue.Null, \"a\": JsonValue.Null)))",
            "duplicate `Map` key",
        ),
        (
            "    call first = inspect(JsonValue.Null)\n    call second = inspect(JsonValue.Array(value: List(first)))",
            "`JsonValue.Array` payload must be a compile-time value",
        ),
    ] {
        rejected(step, message);
    }
}

#[test]
fn const_sized_values_check_against_evaluated_lengths() {
    let steps = steps(
        r#"
scenario sized:
    call sum = total(Array(1, 2))
    call packed = pack(Buffer("0102"))
    call widened = wide(Buffer("0102030405"))
    assert sum == 3
"#,
    );
    // The canonical type keeps the named and arithmetic const argument.
    assert_eq!(
        steps[0]["arguments"][0]["type"]["length"],
        serde_json::json!({"kind": "reference", "symbol": "demo.SIZE", "type": "U32"})
    );
    assert_eq!(
        steps[1]["arguments"][0]["type"]["length"]["kind"],
        "reference"
    );
    assert_eq!(
        literal(&steps[1]["arguments"][0]),
        &serde_json::json!({"hex": "0102", "kind": "buffer"})
    );
    assert_eq!(steps[2]["arguments"][0]["type"]["length"]["kind"], "binary");

    for (step, message) in [
        (
            "    call out = total(Array(1, 2, 3))",
            "Array value length must match its type",
        ),
        (
            "    call out = pack(Buffer(\"010203\"))",
            "Buffer value length must match its type",
        ),
        (
            "    call out = wide(Buffer(\"0102\"))",
            "Buffer value length must match its type",
        ),
    ] {
        rejected(step, message);
    }
}

#[test]
fn constants_and_defaults_check_against_named_lengths() {
    let valid = r#"module demo

const SIZE: U32 = 2

const RAW: Buffer[SIZE] = Buffer("0102")

const DIGITS: Array[U8, SIZE + 1] = Array(1, 2, 3)

newtype Frame(Buffer[SIZE])

const FRAME: Frame = Frame(Buffer("0304"))

struct Header:
    magic: Buffer[SIZE] = Buffer("cafe")
"#;
    lower(valid).unwrap_or_else(|errors| panic!("{errors:?}"));
    for (declaration, message) in [
        (
            "const SHORT: Buffer[SIZE] = Buffer(\"01\")",
            "Buffer constant length does not match its declared type",
        ),
        (
            "const LONG: Array[U8, SIZE] = Array(1, 2, 3)",
            "Array constant length does not match its declared type",
        ),
        (
            "struct Bad:\n    magic: Buffer[SIZE] = Buffer(\"ca\")",
            "default value does not match its declared type",
        ),
    ] {
        let errors = lower(&format!(
            "module demo\n\nconst SIZE: U32 = 2\n\n{declaration}\n"
        ))
        .expect_err("wrong constant length must be rejected");
        assert!(
            errors.iter().any(|error| error.contains(message)),
            "expected `{message}` in {errors:?}"
        );
    }
}

#[test]
fn ir_loader_keeps_json_literals_in_the_jsonvalue_domain() {
    let source = format!(
        "{TYPES}\nscenario s:\n    call out = inspect(JsonValue.Object(value: Map(\"kind\": JsonValue.String(value: \"json\"), \"value\": JsonValue.Integer(value: 7))))\n"
    );
    let parsed = parse_project([SourceFile::new("src/demo.cott", source.as_str())]).expect("parse");
    let hir = cott::hir::lower(Path::new("src"), parsed).expect("lower");
    let ir = cott::ir::render(&hir).expect("render");
    let bytes = &ir.modules[0].bytes;
    // User payload members named `kind`/`value` are data, not IR nodes.
    cott::ir::load(bytes).expect("a JsonValue object payload loads");

    let text = String::from_utf8(bytes.clone()).expect("UTF-8 IR");
    let marker = r#""value":7}"#;
    assert!(text.contains(marker), "{text}");
    for (replacement, message) in [
        (r#""value":9223372036854775808}"#, "outside the I64 range"),
        (r#""value":18446744073709551615}"#, "outside the I64 range"),
    ] {
        let tampered = text.replacen(marker, replacement, 1);
        let error = cott::ir::load(tampered.as_bytes()).expect_err("out-of-domain JsonValue");
        assert!(error.contains(message), "{error}");
    }
    let float = text.replacen(marker, r#""value":7.5}"#, 1);
    cott::ir::load(float.as_bytes()).expect("finite JSON floats stay valid");
}
