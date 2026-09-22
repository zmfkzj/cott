use cott::snapshot_record::{decode, deserialize_json, digest, encode, parse_json};
use serde_json::{Value, json};

// Independently calculated from the protocol's byte grammar, not serde JSON
// text. Python's embedded record reader uses the same cross-language vectors.
const DIGEST_VECTORS: &[(&str, &str)] = &[
    (
        "null",
        "sha256:b5b850b3aed15c1e66245394f63009c41fd0166c05e79b59f3951e2899802bcf",
    ),
    (
        "false",
        "sha256:661d7b6f2a79daf8e234e440d92518a952fd7c24696c5f0f4398090d6b5f613d",
    ),
    (
        "true",
        "sha256:59c4f0127f280440771fe8c9529f5267822cb11f40aa9fbda00c06cd55c323fc",
    ),
    (
        "0",
        "sha256:d1cb613a38fa26f28f7c4632d2534ffed32a9274ec0ddf13bd1a5523469112e4",
    ),
    (
        "1",
        "sha256:e8660e1dda82bea04ec8d6f68621381c3c5e31bd2c0de4ca2f9d112d08611393",
    ),
    (
        "-9223372036854775808",
        "sha256:f1b9dc55157cd3b8a9f991799a26b31dd4f3b3a9f703a9e8dadd88be1609db57",
    ),
    (
        "9223372036854775807",
        "sha256:dc32ea29ba1b8ceb2b7d1ffe362aaa4e88ec1d3e999881fe16255936c02b6a40",
    ),
    (
        "9223372036854775808",
        "sha256:6d7947c1a901c66ff6c8d1ba112d890346c8a5aa6f021d9af1532206c90733fc",
    ),
    (
        "18446744073709551615",
        "sha256:aada17f6673be76d5af3fa2717b1a0c9fb1b7d4505c3f2caff561e45b5d663a0",
    ),
    (
        "0.0",
        "sha256:5e4a82689fe46df343e67c14846a88fb95194f881cee231897141c9dcabc2484",
    ),
    (
        "-0.0",
        "sha256:9853ce0560595735653dc9d75f66d63da30e23d4759c5c05bdb57ae44a63de6f",
    ),
    (
        "1.0",
        "sha256:7a889be4c914b299d06c3b23d09ccc1d37b0780dd1f8fdb234ccc7191cc082f9",
    ),
    (
        "1e-7",
        "sha256:5e46ee3313338944575db4fb988f305914c77fa4142ecf074b75b4c4802429a7",
    ),
    (
        "1e20",
        "sha256:b96a19fb4305ee528a9188e15a8152be0e35ce0b9546230daa2303ba27f22b71",
    ),
    (
        "1e+100",
        "sha256:e5319bc4003e1e6aa4c76e2a472d3030e1592af7ab9b9931be978d1d1029d0ef",
    ),
    (
        "5e-324",
        "sha256:6470ab11bf2685275e275bc3516c1beb862349b39b33bb235ad96e947efcf7d5",
    ),
    (
        r#""é雪𝄞""#,
        "sha256:85214f468f5b1a4f445590483b4e3dbac43148ec22ee196d9bfde45ea98802ea",
    ),
    (
        r#"[null,true,1,1.0,"雪"]"#,
        "sha256:216e90513410fc6e5939b0cffa334a9b3a313efe8c624490427d4d74ab8329d0",
    ),
    (
        r#"{"z":0,"a":[false,{"β":"é"}]}"#,
        "sha256:900b6b376c724e7b35f496a2052128ce8ebb9e9cf3ce63a15904ab456c00683a",
    ),
    (
        "{}",
        "sha256:908471fd2a90ddb279e9a2c53eed040e0982dcab923477cc91c290c4a1c4a68e",
    ),
    (
        "[]",
        "sha256:8ae6b32441057aab17bab3c25fb606e9bd128d704f1416e6b03689b6510214f1",
    ),
];

#[test]
fn structural_digest_matches_cross_language_vectors() {
    for &(source, expected) in DIGEST_VECTORS {
        let value = parse_json(source.as_bytes()).unwrap();
        assert_eq!(digest(&value).unwrap(), expected, "vector {source}");
        let serialized = serde_json::to_vec(&value).unwrap();
        assert_eq!(digest(&parse_json(&serialized).unwrap()).unwrap(), expected);
    }
    assert_eq!(
        digest(&json!(1_i64)).unwrap(),
        digest(&json!(1_u64)).unwrap()
    );
}

#[test]
fn object_order_is_canonical_but_array_order_is_not() {
    let left = parse_json(br#"{"z":0,"a":[false,{"b":1,"a":2}]}"#).unwrap();
    let right = parse_json(br#"{"a":[false,{"a":2,"b":1}],"z":0}"#).unwrap();
    assert_eq!(digest(&left).unwrap(), digest(&right).unwrap());
    assert_eq!(
        serde_json::to_vec(&encode(8, &left, Some(&right)).unwrap()).unwrap(),
        serde_json::to_vec(&encode(8, &right, Some(&left)).unwrap()).unwrap()
    );
    assert_ne!(
        digest(&json!([1, 2])).unwrap(),
        digest(&json!([2, 1])).unwrap()
    );
}

fn snapshot() -> Value {
    json!({
        "generation_id": format!("sha256:{}", "1".repeat(64)),
        "verified": true,
        "verification": {"passed": true},
        "semantic_coverage": {"evidence": []},
        "agent_runs": [],
    })
}

#[test]
fn equal_verified_snapshots_are_stored_once_and_resolve_without_external_state() {
    let current = snapshot();
    let wire = encode(8, &current, Some(&current.clone())).unwrap();
    assert_eq!(wire["current"], wire["last_verified"]);
    let table = wire["snapshots"].as_object().unwrap();
    assert_eq!(table.len(), 1);
    assert_eq!(table[wire["current"].as_str().unwrap()], current);
    let bytes = serde_json::to_vec(&wire).unwrap();
    assert_eq!(
        decode(&parse_json(&bytes).unwrap(), 8).unwrap(),
        (current.clone(), Some(current))
    );
}

#[test]
fn divergent_history_is_complete_and_unverified_current_has_no_required_history() {
    let last = snapshot();
    let mut current = last.clone();
    current["generation_id"] = json!(format!("sha256:{}", "2".repeat(64)));
    current["verified"] = json!(false);
    current["verification"] = Value::Null;
    let wire = encode(8, &current, Some(&last)).unwrap();
    assert_ne!(wire["current"], wire["last_verified"]);
    assert_eq!(wire["snapshots"].as_object().unwrap().len(), 2);
    assert_eq!(decode(&wire, 8).unwrap(), (current.clone(), Some(last)));
    let initial = encode(8, &current, None).unwrap();
    assert!(initial["last_verified"].is_null());
    assert_eq!(initial["snapshots"].as_object().unwrap().len(), 1);
    assert_eq!(decode(&initial, 8).unwrap(), (current, None));
}

#[test]
fn full_snapshot_identity_includes_verification_coverage_and_agent_evidence() {
    let baseline = snapshot();
    for (field, replacement) in [
        ("verified", json!(false)),
        ("verification", json!({"passed": false})),
        (
            "semantic_coverage",
            json!({"evidence": [{"observed": true}]}),
        ),
        (
            "agent_runs",
            json!([{"symbol": "app.run", "duration_ms": 42}]),
        ),
    ] {
        let mut changed = baseline.clone();
        changed[field] = replacement;
        assert_eq!(changed["generation_id"], baseline["generation_id"]);
        assert_ne!(
            digest(&changed).unwrap(),
            digest(&baseline).unwrap(),
            "{field}"
        );
        let wire = encode(8, &changed, Some(&baseline)).unwrap();
        assert_eq!(wire["snapshots"].as_object().unwrap().len(), 2, "{field}");
        assert_eq!(decode(&wire, 8).unwrap(), (changed, Some(baseline.clone())));
    }
}

#[test]
fn deduplication_preserves_numeric_types_and_signed_zero_bits() {
    for (left, right) in [
        (json!(0.0), json!(-0.0)),
        (json!(1), json!(1.0)),
        (json!(true), json!(1)),
    ] {
        let current = json!({"evidence": [{"value": left}]});
        let last = json!({"evidence": [{"value": right}]});
        let wire = encode(8, &current, Some(&last)).unwrap();
        assert_ne!(wire["current"], wire["last_verified"]);
        assert_eq!(wire["snapshots"].as_object().unwrap().len(), 2);
        let (decoded_current, decoded_last) = decode(&wire, 8).unwrap();
        assert_eq!(digest(&decoded_current).unwrap(), digest(&current).unwrap());
        assert_eq!(
            digest(&decoded_last.unwrap()).unwrap(),
            digest(&last).unwrap()
        );
    }
}

#[test]
fn tampering_cannot_hide_behind_an_unchanged_generation_id() {
    let mut wire = encode(8, &snapshot(), None).unwrap();
    let current = wire["current"].as_str().unwrap().to_owned();
    wire["snapshots"][&current]["verification"]["passed"] = json!(false);
    assert!(decode(&wire, 8).is_err());
}

#[test]
fn references_cannot_be_dangling_or_make_unreachable_snapshots_acceptable() {
    let original = snapshot();
    let wire = encode(8, &original, None).unwrap();
    let other = json!({"generation_id": "other"});
    let other_id = digest(&other).unwrap();

    let mut dangling_current = wire.clone();
    dangling_current["current"] = json!(other_id);
    assert!(decode(&dangling_current, 8).is_err());

    let mut dangling_last = wire.clone();
    dangling_last["last_verified"] = json!(other_id);
    assert!(decode(&dangling_last, 8).is_err());

    let mut unreachable = wire.clone();
    unreachable["snapshots"][&other_id] = other;
    assert!(decode(&unreachable, 8).is_err());
    unreachable["last_verified"] = wire["current"].clone();
    assert!(decode(&unreachable, 8).is_err());

    let mut excessive = wire;
    for index in 0..2 {
        let extra = json!({"extra": index});
        let extra_id = digest(&extra).unwrap();
        excessive["snapshots"][extra_id] = extra;
    }
    assert!(decode(&excessive, 8).is_err());
}

#[test]
fn root_shape_types_versions_and_digest_syntax_are_closed() {
    let wire = encode(8, &snapshot(), None).unwrap();
    for (field, replacement) in [
        ("schema_version", json!(7)),
        ("schema_version", json!(8.0)),
        ("schema_version", json!("8")),
        ("current", snapshot()),
        ("current", Value::Null),
        ("current", json!(format!("sha256:{}", "A".repeat(64)))),
        ("current", json!(format!("sha256:{}", "a".repeat(63)))),
        ("last_verified", snapshot()),
        ("last_verified", json!(false)),
        ("snapshots", json!([])),
        ("snapshots", json!({})),
    ] {
        let mut invalid = wire.clone();
        invalid[field] = replacement;
        assert!(decode(&invalid, 8).is_err(), "{field}: {}", invalid[field]);
    }
    for field in ["schema_version", "current", "last_verified", "snapshots"] {
        let mut missing = wire.clone();
        missing.as_object_mut().unwrap().remove(field);
        assert!(decode(&missing, 8).is_err(), "missing {field}");
    }
    let mut unknown = wire.clone();
    unknown["sidecar"] = json!("snapshot.json");
    assert!(decode(&unknown, 8).is_err());
    assert!(decode(&json!([wire]), 8).is_err());
    assert!(
        decode(
            &json!({"schema_version": 8, "current": snapshot(), "last_verified": null}),
            8
        )
        .is_err()
    );
}

#[test]
fn snapshots_are_objects_not_scalars_arrays_or_further_references() {
    for value in [
        Value::Null,
        json!([]),
        json!(true),
        json!(42),
        json!(format!("sha256:{}", "a".repeat(64))),
    ] {
        assert!(encode(8, &value, None).is_err());
        assert!(encode(8, &snapshot(), Some(&value)).is_err());
        let id = digest(&value).unwrap();
        let wire = json!({"schema_version": 8, "current": id, "last_verified": null, "snapshots": {id: value}});
        assert!(decode(&wire, 8).is_err());
    }
    let mut wire = encode(8, &snapshot(), None).unwrap();
    let current = wire["current"].as_str().unwrap().to_owned();
    let snapshot = wire["snapshots"]
        .as_object_mut()
        .unwrap()
        .remove(&current)
        .unwrap();
    wire["snapshots"][current.to_uppercase()] = snapshot;
    assert!(decode(&wire, 8).is_err());
}

#[test]
fn duplicate_members_are_rejected_at_every_depth_and_by_custom_deserialization() {
    let snapshot = snapshot();
    let wire = encode(8, &snapshot, None).unwrap();
    let id = wire["current"].as_str().unwrap();
    let snapshot_json = serde_json::to_string(&snapshot).unwrap();
    let duplicate_table = format!(
        r#"{{"schema_version":8,"current":"{id}","last_verified":null,"snapshots":{{"{id}":{snapshot_json},"{id}":{snapshot_json}}}}}"#
    );
    for source in [
        r#"{"schema_version":8,"schema_version":8}"#,
        r#"{"snapshots":{"x":{"verified":true,"verified":false}}}"#,
        r#"{"evidence":[{"value":1,"value":2}]}"#,
        r#"{"a":1,"\u0061":1}"#,
        &duplicate_table,
    ] {
        assert!(parse_json(source.as_bytes()).is_err(), "{source}");
        let mut deserializer = serde_json::Deserializer::from_str(source);
        assert!(deserialize_json(&mut deserializer).is_err(), "{source}");
    }
}

#[test]
fn nonfinite_numbers_and_trailing_documents_are_not_json_snapshots() {
    for source in [
        "NaN",
        "Infinity",
        "-Infinity",
        "1e400",
        r#"{"value":NaN}"#,
        "{} {}",
    ] {
        assert!(parse_json(source.as_bytes()).is_err(), "{source}");
    }
    for value in [f64::NAN, f64::INFINITY, f64::NEG_INFINITY] {
        let deserializer = serde::de::value::F64Deserializer::<serde::de::value::Error>::new(value);
        assert!(deserialize_json(deserializer).is_err());
    }
}
