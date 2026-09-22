use std::fmt;

use serde::de::{self, MapAccess, SeqAccess, Visitor};
use serde::{Deserialize, Deserializer};
use serde_json::{Map, Number, Value};
use sha2::{Digest, Sha256};

const DOMAIN: &[u8] = b"cott.snapshot.v1\0";

/// Hash the complete value using the language-independent snapshot encoding.
/// Record references hash full snapshots, including verification and agent
/// evidence; generation identities instead pass their normalized domain wrapper.
pub fn digest(value: &Value) -> Result<String, String> {
    let mut hash = Sha256::new();
    hash.update(DOMAIN);
    hash_value(&mut hash, value)?;
    Ok(format!("sha256:{:x}", hash.finalize()))
}

fn hash_value(hash: &mut Sha256, value: &Value) -> Result<(), String> {
    match value {
        Value::Null => hash.update(b"n"),
        Value::Bool(false) => hash.update(b"f"),
        Value::Bool(true) => hash.update(b"t"),
        Value::Number(number) => {
            if number.is_f64() {
                let number = number
                    .as_f64()
                    .filter(|number| number.is_finite())
                    .ok_or("snapshot numbers must be finite")?;
                hash.update(b"d");
                hash.update(number.to_bits().to_be_bytes());
            } else {
                let (mut magnitude, negative) = if let Some(value) = number.as_u64() {
                    (value, false)
                } else {
                    let value = number.as_i64().ok_or("snapshot integer is out of range")?;
                    (value.unsigned_abs(), true)
                };
                let mut decimal = [0_u8; 20];
                let mut start = decimal.len();
                loop {
                    start -= 1;
                    decimal[start] = b'0' + (magnitude % 10) as u8;
                    magnitude /= 10;
                    if magnitude == 0 {
                        break;
                    }
                }
                if negative {
                    start -= 1;
                    decimal[start] = b'-';
                }
                hash.update(b"i");
                hash.update(((decimal.len() - start) as u64).to_be_bytes());
                hash.update(&decimal[start..]);
            }
        }
        Value::String(string) => hash_string(hash, string),
        Value::Array(values) => {
            hash.update(b"a");
            hash.update((values.len() as u64).to_be_bytes());
            for value in values {
                hash_value(hash, value)?;
            }
        }
        Value::Object(object) => {
            hash.update(b"o");
            hash.update((object.len() as u64).to_be_bytes());
            // serde_json::Map uses sorted keys (preserve_order is not enabled).
            for (key, value) in object {
                hash_string(hash, key);
                hash_value(hash, value)?;
            }
        }
    }
    Ok(())
}

fn hash_string(hash: &mut Sha256, string: &str) {
    hash.update(b"s");
    hash.update((string.len() as u64).to_be_bytes());
    hash.update(string.as_bytes());
}

/// Build the sole on-disk record format, storing each reachable snapshot once.
/// Target-specific snapshot semantics are checked by the target record type.
pub fn encode(
    schema_version: u32,
    current: &Value,
    last_verified: Option<&Value>,
) -> Result<Value, String> {
    require_snapshot(current)?;
    if let Some(last_verified) = last_verified {
        require_snapshot(last_verified)?;
    }
    let current_id = digest(current)?;
    let mut snapshots = Map::new();
    let last_id = match last_verified {
        None => Value::Null,
        Some(last_verified) if same_value(current, last_verified) => {
            Value::String(current_id.clone())
        }
        Some(last_verified) => {
            let last_id = digest(last_verified)?;
            if last_id == current_id {
                return Err("snapshot digest collision".to_owned());
            }
            snapshots.insert(last_id.clone(), last_verified.clone());
            Value::String(last_id)
        }
    };
    snapshots.insert(current_id.clone(), current.clone());
    let mut record = Map::new();
    record.insert("schema_version".to_owned(), schema_version.into());
    record.insert("current".to_owned(), Value::String(current_id));
    record.insert("last_verified".to_owned(), last_id);
    record.insert("snapshots".to_owned(), Value::Object(snapshots));
    Ok(Value::Object(record))
}

// Value's PartialEq treats opposite signed floating-point zeros as equal. The
// snapshot protocol does not; deduplication must preserve their distinct bits.
fn same_value(left: &Value, right: &Value) -> bool {
    match (left, right) {
        (Value::Number(left), Value::Number(right)) if left.is_f64() || right.is_f64() => {
            left.is_f64()
                && right.is_f64()
                && left.as_f64().map(f64::to_bits) == right.as_f64().map(f64::to_bits)
        }
        (Value::Array(left), Value::Array(right)) => {
            left.len() == right.len()
                && left
                    .iter()
                    .zip(right)
                    .all(|(left, right)| same_value(left, right))
        }
        (Value::Object(left), Value::Object(right)) => {
            left.len() == right.len()
                && left
                    .iter()
                    .all(|(key, left)| right.get(key).is_some_and(|right| same_value(left, right)))
        }
        _ => left == right,
    }
}

/// Validate a self-contained reference envelope and return its expanded values.
/// There is deliberately no reader for the previous expanded record format.
pub fn decode(wire: &Value, expected_schema: u32) -> Result<(Value, Option<Value>), String> {
    let record = wire
        .as_object()
        .ok_or("generation record must be an object")?;
    const FIELDS: [&str; 4] = ["schema_version", "current", "last_verified", "snapshots"];
    if record.len() != FIELDS.len() || FIELDS.iter().any(|key| !record.contains_key(*key)) {
        return Err("generation record must contain exactly schema_version, current, last_verified, and snapshots".to_owned());
    }
    if record["schema_version"].as_u64() != Some(u64::from(expected_schema)) {
        return Err(format!(
            "generation schema version must be {expected_schema}"
        ));
    }
    let current_id = reference(&record["current"])?;
    let last_id = match &record["last_verified"] {
        Value::Null => None,
        value => Some(reference(value)?),
    };
    let snapshots = record["snapshots"]
        .as_object()
        .ok_or("generation snapshots must be an object")?;
    if !(1..=2).contains(&snapshots.len()) {
        return Err("generation snapshots must contain one or two reachable snapshots".to_owned());
    }
    for (id, snapshot) in snapshots {
        if !valid_digest(id) {
            return Err("snapshot key must be a lowercase SHA-256 digest".to_owned());
        }
        if id != current_id && Some(id.as_str()) != last_id {
            return Err(format!("unreachable snapshot {id}"));
        }
        require_snapshot(snapshot)?;
        if digest(snapshot)? != *id {
            return Err(format!("snapshot digest mismatch for {id}"));
        }
    }
    let current = snapshots
        .get(current_id)
        .ok_or_else(|| format!("dangling current snapshot reference {current_id}"))?;
    let last_verified = last_id
        .map(|id| {
            snapshots
                .get(id)
                .cloned()
                .ok_or_else(|| format!("dangling last_verified snapshot reference {id}"))
        })
        .transpose()?;
    Ok((current.clone(), last_verified))
}

fn require_snapshot(value: &Value) -> Result<(), String> {
    if value.is_object() {
        Ok(())
    } else {
        Err("snapshot must be a complete object".to_owned())
    }
}

fn reference(value: &Value) -> Result<&str, String> {
    value
        .as_str()
        .filter(|value| valid_digest(value))
        .ok_or_else(|| "snapshot reference must be a lowercase SHA-256 digest".to_owned())
}

fn valid_digest(value: &str) -> bool {
    value.len() == 71
        && value.starts_with("sha256:")
        && value.as_bytes()[7..]
            .iter()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(byte))
}

/// Parse JSON without silently overwriting any duplicate object members.
pub fn parse_json(bytes: &[u8]) -> Result<Value, String> {
    serde_json::from_slice::<StrictValue>(bytes)
        .map(|value| value.0)
        .map_err(|error| format!("invalid generation JSON: {error}"))
}

/// Strict JSON-value deserialization for each target record's custom reader.
pub fn deserialize_json<'de, D: Deserializer<'de>>(deserializer: D) -> Result<Value, D::Error> {
    StrictValue::deserialize(deserializer).map(|value| value.0)
}

struct StrictValue(Value);

impl<'de> Deserialize<'de> for StrictValue {
    fn deserialize<D: Deserializer<'de>>(deserializer: D) -> Result<Self, D::Error> {
        deserializer.deserialize_any(StrictVisitor).map(Self)
    }
}

struct StrictVisitor;

impl<'de> Visitor<'de> for StrictVisitor {
    type Value = Value;

    fn expecting(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter.write_str("JSON with unique object members and finite numbers")
    }

    fn visit_unit<E: de::Error>(self) -> Result<Value, E> {
        Ok(Value::Null)
    }

    fn visit_bool<E: de::Error>(self, value: bool) -> Result<Value, E> {
        Ok(Value::Bool(value))
    }

    fn visit_i64<E: de::Error>(self, value: i64) -> Result<Value, E> {
        Ok(Value::Number(value.into()))
    }

    fn visit_u64<E: de::Error>(self, value: u64) -> Result<Value, E> {
        Ok(Value::Number(value.into()))
    }

    fn visit_f64<E: de::Error>(self, value: f64) -> Result<Value, E> {
        Number::from_f64(value)
            .map(Value::Number)
            .ok_or_else(|| E::custom("snapshot numbers must be finite"))
    }

    fn visit_str<E: de::Error>(self, value: &str) -> Result<Value, E> {
        Ok(Value::String(value.to_owned()))
    }

    fn visit_string<E: de::Error>(self, value: String) -> Result<Value, E> {
        Ok(Value::String(value))
    }

    fn visit_seq<A: SeqAccess<'de>>(self, mut sequence: A) -> Result<Value, A::Error> {
        let mut values = Vec::new();
        while let Some(value) = sequence.next_element::<StrictValue>()? {
            values.push(value.0);
        }
        Ok(Value::Array(values))
    }

    fn visit_map<A: MapAccess<'de>>(self, mut map: A) -> Result<Value, A::Error> {
        let mut values = Map::new();
        while let Some(key) = map.next_key::<String>()? {
            if values.contains_key(&key) {
                return Err(de::Error::custom(format!("duplicate JSON member {key:?}")));
            }
            values.insert(key, map.next_value::<StrictValue>()?.0);
        }
        Ok(Value::Object(values))
    }
}
