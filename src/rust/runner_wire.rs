use super::EVIDENCE_KEY_BYTES;
use hmac::{Hmac, Mac};
use serde_json::Value;
use sha2::Sha256;
const EVENT_PREFIX: &str = "COTT_RUST_VERIFY:";

pub(crate) fn parse_events(stdout: &[u8], key: &[u8]) -> Result<Vec<Value>, String> {
    if key.len() != EVIDENCE_KEY_BYTES {
        return Err("Rust evidence authentication key has wrong length".to_owned());
    }
    let output = std::str::from_utf8(stdout)
        .map_err(|_| "bounded Rust runner stdout is not UTF-8".to_owned())?;
    let mut events = Vec::new();
    let mut sequence = 0u64;
    for line in output.lines() {
        let Some(record) = line.strip_prefix(EVENT_PREFIX) else {
            continue;
        };
        let (reported_sequence, rest) = record
            .split_once(':')
            .ok_or("malformed authenticated Rust evidence sequence")?;
        let (tag, payload) = rest
            .split_once(':')
            .ok_or("malformed authenticated Rust evidence tag")?;
        let reported_sequence = reported_sequence
            .parse::<u64>()
            .map_err(|_| "authenticated Rust evidence sequence is not u64")?;
        if tag.len() != 64
            || !tag
                .bytes()
                .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
        {
            return Err("authenticated Rust evidence tag is not lowercase SHA-256 hex".to_owned());
        }
        let mut authenticated = Vec::with_capacity(8 + payload.len());
        authenticated.extend_from_slice(&reported_sequence.to_be_bytes());
        authenticated.extend_from_slice(payload.as_bytes());
        let mut mac = Hmac::<Sha256>::new_from_slice(key)
            .map_err(|_| "initialize Rust evidence HMAC-SHA256".to_owned())?;
        mac.update(&authenticated);
        let provided = decode_hex(tag)?;
        mac.verify_slice(&provided)
            .map_err(|_| "Rust contract runner emitted unauthenticated evidence".to_owned())?;
        if reported_sequence != sequence {
            return Err(format!(
                "authenticated Rust evidence sequence mismatch: expected {sequence}, got {reported_sequence}"
            ));
        }
        let event: Value = serde_json::from_str(payload)
            .map_err(|error| format!("invalid authenticated Rust evidence JSON: {error}"))?;
        if !event.is_object() {
            return Err("authenticated Rust evidence is not a JSON object".to_owned());
        }
        events.push(event);
        sequence = sequence
            .checked_add(1)
            .ok_or("authenticated Rust evidence sequence overflow")?;
    }
    if events.is_empty() {
        return Err("bounded Rust runner emitted no authenticated evidence".to_owned());
    }
    Ok(events)
}

fn decode_hex(value: &str) -> Result<Vec<u8>, String> {
    value
        .as_bytes()
        .chunks_exact(2)
        .map(|chunk| {
            let high = hex_nibble(chunk[0])?;
            let low = hex_nibble(chunk[1])?;
            Ok((high << 4) | low)
        })
        .collect()
}

fn hex_nibble(value: u8) -> Result<u8, String> {
    match value {
        b'0'..=b'9' => Ok(value - b'0'),
        b'a'..=b'f' => Ok(value - b'a' + 10),
        _ => Err("Rust evidence tag contains non-hex byte".to_owned()),
    }
}
