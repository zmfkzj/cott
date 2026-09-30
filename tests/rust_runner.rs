#![allow(dead_code)]
use hmac::{Hmac, Mac};
use serde_json::{Value, json};
use sha2::Sha256;
const EVIDENCE_KEY_BYTES: usize = 32;
#[path = "../src/rust/runner_support.rs"]
mod support;
#[path = "../src/rust/runner_wire.rs"]
mod wire;
fn record(sequence: u64, payload: &str, key: &[u8]) -> String {
    let mut mac = Hmac::<Sha256>::new_from_slice(key).unwrap();
    mac.update(&sequence.to_be_bytes());
    mac.update(payload.as_bytes());
    let tag = mac
        .finalize()
        .into_bytes()
        .iter()
        .map(|b| format!("{b:02x}"))
        .collect::<String>();
    format!("COTT_RUST_VERIFY:{sequence}:{tag}:{payload}\n")
}
#[test]
fn accepts_only_ordered_authenticated_exact_utf8_payloads() {
    let key = [17; 32];
    let payload = serde_json::to_string(
        &json!({"kind":"scenario","scenario_id":"unicode-é","value":"a:b\n"}),
    )
    .unwrap();
    let output = format!(
        "ordinary dependency output\n{}{}",
        record(0, &payload, &key),
        record(1, "{\"kind\":\"done\"}", &key)
    );
    let events = wire::parse_events(output.as_bytes(), &key).unwrap();
    assert_eq!(
        events,
        vec![
            serde_json::from_str::<Value>(&payload).unwrap(),
            json!({"kind":"done"})
        ]
    );
}
#[test]
fn rejects_forged_and_tampered_payloads() {
    let key = [5; 32];
    let valid = record(0, "{\"kind\":\"done\"}", &key);
    assert!(wire::parse_events(valid.as_bytes(), &[6; 32]).is_err());
    assert!(wire::parse_events(valid.replace("done", "case").as_bytes(), &key).is_err());
    let mut altered = valid.into_bytes();
    let colon = altered.iter().position(|b| *b == b':').unwrap();
    altered[colon + 3] ^= 1;
    assert!(wire::parse_events(&altered, &key).is_err());
}
#[test]
fn rejects_replay_omission_and_reordering() {
    let key = [3; 32];
    let zero = record(0, "{\"kind\":\"case\"}", &key);
    let one = record(1, "{\"kind\":\"done\"}", &key);
    assert!(wire::parse_events(format!("{zero}{zero}").as_bytes(), &key).is_err());
    assert!(wire::parse_events(one.as_bytes(), &key).is_err());
    assert!(wire::parse_events(format!("{one}{zero}").as_bytes(), &key).is_err());
}
#[test]
fn rejects_nonobject_json_even_with_valid_authentication() {
    let key = [1; 32];
    for payload in ["null", "[]", "42", "\"done\"", "{broken}"] {
        assert!(wire::parse_events(record(0, payload, &key).as_bytes(), &key).is_err());
    }
}
#[test]
fn rejects_malformed_tag_key_and_utf8() {
    let key = [0; 32];
    assert!(wire::parse_events(b"COTT_RUST_VERIFY:0:ff:{}\n", &key).is_err());
    assert!(wire::parse_events(b"\xff", &key).is_err());
    assert!(wire::parse_events(record(0, "{}", &key).as_bytes(), &key[..31]).is_err());
    assert!(wire::parse_events(b"ordinary output only\n", &key).is_err());
}
