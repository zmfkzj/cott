#![allow(dead_code)]

use cott::snapshot_record;
use serde_json::{Value, json};

/// Read the real wire format, then expose an expanded test-only assertion view.
pub fn read(bytes: &[u8]) -> Value {
    expand(snapshot_record::parse_json(bytes).expect("valid generation JSON"))
}

/// Reseal an expanded assertion view when testing target snapshot semantics.
/// Corruption tests of the envelope itself must instead edit the raw wire.
pub fn bytes(view: &Value) -> Vec<u8> {
    let mut bytes = serde_json::to_vec(&pack(view)).expect("serialize generation record");
    bytes.push(b'\n');
    bytes
}

pub fn expand(wire: Value) -> Value {
    let schema_version = schema_version(&wire);
    let (current, last_verified) =
        snapshot_record::decode(&wire, schema_version).expect("valid snapshot references");
    json!({
        "schema_version": schema_version,
        "current": current,
        "last_verified": last_verified,
    })
}

pub fn pack(view: &Value) -> Value {
    let schema_version = schema_version(view);
    let current = view.get("current").expect("current snapshot in test view");
    let last_verified = view
        .get("last_verified")
        .expect("last_verified in test view");
    snapshot_record::encode(
        schema_version,
        current,
        (!last_verified.is_null()).then_some(last_verified),
    )
    .expect("encodable snapshot test view")
}

fn schema_version(value: &Value) -> u32 {
    value["schema_version"]
        .as_u64()
        .and_then(|version| u32::try_from(version).ok())
        .expect("u32 generation schema version")
}
