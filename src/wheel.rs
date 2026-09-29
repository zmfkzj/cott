//! Standard `py3-none-any` wheel of a verified Python deployment.
//!
//! The wheel is the deployment's importable tree in flat purelib layout: every deployed
//! `python/` member sits at the archive root, next to `generation.json`. Installed into
//! `site-packages` this is the layout the generated runtime resolves as `root/generation.json`
//! when its root directory is not named `python`. Console scripts come from the authored
//! `pyproject.toml`. The archive is reproducible: sorted members, the ZIP epoch timestamp and
//! fixed permissions.

use std::borrow::Cow;
use std::collections::btree_map::Entry;
use std::collections::{BTreeMap, BTreeSet};
use std::fmt::Write as _;
use std::io::Write as _;
use std::path::{Component, Path, PathBuf};

use flate2::write::DeflateEncoder;
use flate2::{Compression, Crc};
use sha2::{Digest, Sha256};

const PYTHON_ROOT: &str = "python";
const GENERATION_MEMBER: &str = "generation.json";
const WHEEL_TAG: &str = "py3-none-any";
const GENERATOR: &str = concat!("cott ", env!("CARGO_PKG_VERSION"));
/// Compiler-owned top-level packages that no console script may target.
const COTT_OWNED_ROOTS: [&str; 2] = ["_cott_impl", "cott_runtime"];

/// Everything a wheel is derived from. Paths in `files` and `adapters` use deployment
/// coordinates, so they carry the `python/` prefix.
pub(crate) struct WheelInput<'a> {
    /// `[project].name` and `[project].version` from `cott.toml`.
    pub name: &'a str,
    pub version: &'a str,
    /// Bytes of the authored `pyproject.toml`.
    pub pyproject: &'a [u8],
    /// Exact bytes of the deployed `generation.json`.
    pub generation: &'a [u8],
    /// Deployed `python/` members: generated runtime, facades, implementations and adapters.
    pub files: &'a BTreeMap<PathBuf, Vec<u8>>,
    /// The members of `files` that are authored runtime adapters.
    pub adapters: &'a BTreeSet<PathBuf>,
}

pub(crate) struct Wheel {
    pub file_name: String,
    pub bytes: Vec<u8>,
}

pub(crate) fn build(input: &WheelInput<'_>) -> Result<Wheel, String> {
    let distribution = distribution_name(input.name)?;
    let project = PyProject::parse(input.pyproject)?;

    let mut members: BTreeMap<String, Cow<'_, [u8]>> = BTreeMap::new();
    let mut authored = BTreeSet::new();
    let mut generated_roots = BTreeSet::new();
    for (path, bytes) in input.files {
        let relative = path
            .strip_prefix(PYTHON_ROOT)
            .map_err(|_| format!("wheel member is outside {PYTHON_ROOT}/: {}", path.display()))?;
        // The generated source-root marker is not part of any package: installed at the
        // archive root it would turn `site-packages` itself into a package.
        if relative == Path::new("__init__.py") {
            continue;
        }
        let name = archive_name(relative)?;
        let root = name.split('/').next().unwrap_or_default();
        if root.ends_with(".dist-info") || root.ends_with(".data") {
            return Err(format!(
                "wheel member collides with reserved wheel metadata directory: {name}"
            ));
        }
        if input.adapters.contains(path) {
            authored.insert(name.clone());
        } else {
            generated_roots.insert(root.strip_suffix(".py").unwrap_or(root).to_owned());
        }
        insert_member(&mut members, name, Cow::Borrowed(bytes.as_slice()))?;
    }
    insert_member(
        &mut members,
        GENERATION_MEMBER.to_owned(),
        Cow::Borrowed(input.generation),
    )?;

    let scripts = console_scripts(&project.scripts, &authored, &generated_roots)?;
    let info = format!("{distribution}-{}.dist-info", input.version);
    insert_member(
        &mut members,
        format!("{info}/METADATA"),
        Cow::Owned(metadata(input.name, input.version, &project).into_bytes()),
    )?;
    insert_member(
        &mut members,
        format!("{info}/WHEEL"),
        Cow::Owned(
            format!(
                "Wheel-Version: 1.0\nGenerator: {GENERATOR}\nRoot-Is-Purelib: true\nTag: {WHEEL_TAG}\n"
            )
            .into_bytes(),
        ),
    )?;
    if !scripts.is_empty() {
        insert_member(
            &mut members,
            format!("{info}/entry_points.txt"),
            Cow::Owned(entry_points(&scripts).into_bytes()),
        )?;
    }
    let record = format!("{info}/RECORD");
    let record_bytes = record_file(&members, &record).into_bytes();
    insert_member(&mut members, record, Cow::Owned(record_bytes))?;

    Ok(Wheel {
        file_name: format!("{distribution}-{}-{WHEEL_TAG}.whl", input.version),
        bytes: zip(&members)?,
    })
}

fn insert_member<'a>(
    members: &mut BTreeMap<String, Cow<'a, [u8]>>,
    name: String,
    bytes: Cow<'a, [u8]>,
) -> Result<(), String> {
    match members.entry(name) {
        Entry::Vacant(slot) => {
            slot.insert(bytes);
            Ok(())
        }
        Entry::Occupied(slot) => Err(format!("duplicate wheel member: {}", slot.key())),
    }
}

/// The PEP 508 project name, normalized for wheel file and `.dist-info` names: lowercase, with
/// each run of `-`, `_` and `.` collapsed to one `_`.
fn distribution_name(name: &str) -> Result<String, String> {
    let separator = |byte: u8| matches!(byte, b'-' | b'_' | b'.');
    let bytes = name.as_bytes();
    let valid = bytes.first().is_some_and(u8::is_ascii_alphanumeric)
        && bytes.last().is_some_and(u8::is_ascii_alphanumeric)
        && bytes
            .iter()
            .all(|&byte| byte.is_ascii_alphanumeric() || separator(byte));
    if !valid {
        return Err(format!(
            "project name {name:?} cannot name a Python wheel: use ASCII letters, digits, `.`, `_` and `-`, starting and ending with a letter or digit"
        ));
    }
    let mut normalized = String::with_capacity(bytes.len());
    let mut pending_separator = false;
    for &byte in bytes {
        if separator(byte) {
            pending_separator = true;
            continue;
        }
        if std::mem::take(&mut pending_separator) {
            normalized.push('_');
        }
        normalized.push(char::from(byte.to_ascii_lowercase()));
    }
    Ok(normalized)
}

/// The slash-separated archive name of a member below the wheel root.
fn archive_name(path: &Path) -> Result<String, String> {
    let mut name = String::new();
    for component in path.components() {
        let Component::Normal(part) = component else {
            return Err(format!("unsafe wheel member: {}", path.display()));
        };
        let part = part
            .to_str()
            .ok_or_else(|| format!("wheel member is not valid UTF-8: {}", path.display()))?;
        if part
            .chars()
            .any(|character| character == '\\' || character.is_control())
        {
            return Err(format!(
                "wheel member contains a backslash or control character: {}",
                path.display()
            ));
        }
        if !name.is_empty() {
            name.push('/');
        }
        name.push_str(part);
    }
    if name.is_empty() {
        return Err("empty wheel member name".to_owned());
    }
    Ok(name)
}

/// The distribution metadata fields of the authored `pyproject.toml` that a wheel carries.
struct PyProject {
    requires_python: Option<String>,
    dependencies: Vec<String>,
    scripts: BTreeMap<String, String>,
}

impl PyProject {
    fn parse(bytes: &[u8]) -> Result<Self, String> {
        let text = std::str::from_utf8(bytes)
            .map_err(|error| format!("pyproject.toml is not UTF-8: {error}"))?;
        let document: toml::Table = toml::from_str(text)
            .map_err(|error| format!("invalid pyproject.toml: {}", error.message()))?;
        let project = document
            .get("project")
            .and_then(toml::Value::as_table)
            .ok_or("pyproject.toml has no [project] table")?;
        let requires_python = project
            .get("requires-python")
            .map(|value| {
                let value = value
                    .as_str()
                    .ok_or("pyproject.toml [project].requires-python must be a string")?;
                header_value(value, "requires-python")
            })
            .transpose()?;
        let dependencies: Vec<String> = match project.get("dependencies") {
            None => Vec::new(),
            Some(value) => value
                .as_array()
                .ok_or("pyproject.toml [project].dependencies must be an array of strings")?
                .iter()
                .map(|dependency| {
                    let dependency = dependency.as_str().ok_or(
                        "pyproject.toml [project].dependencies must be an array of strings",
                    )?;
                    header_value(dependency, "dependency")
                })
                .collect::<Result<_, String>>()?,
        };
        let scripts: BTreeMap<String, String> = match project.get("scripts") {
            None => BTreeMap::new(),
            Some(value) => value
                .as_table()
                .ok_or("pyproject.toml [project.scripts] must be a table")?
                .iter()
                .map(|(name, target)| {
                    let target = target.as_str().ok_or_else(|| {
                        format!("pyproject.toml [project.scripts] {name:?} must be a string")
                    })?;
                    Ok((name.clone(), target.to_owned()))
                })
                .collect::<Result<_, String>>()?,
        };
        Ok(Self {
            requires_python,
            dependencies,
            scripts,
        })
    }
}

/// A METADATA header value must stay on one line and cannot be blank.
fn header_value(value: &str, field: &str) -> Result<String, String> {
    if value.trim().is_empty() || value.chars().any(char::is_control) {
        return Err(format!(
            "pyproject.toml {field} {value:?} must be a nonblank single line"
        ));
    }
    Ok(value.to_owned())
}

/// Validates `[project.scripts]` against the members the wheel actually installs. A console
/// script is a wrapper around an authored adapter, never around compiler-owned code.
fn console_scripts<'a>(
    scripts: &'a BTreeMap<String, String>,
    authored: &BTreeSet<String>,
    generated_roots: &BTreeSet<String>,
) -> Result<BTreeMap<&'a str, &'a str>, String> {
    let mut validated = BTreeMap::new();
    for (name, target) in scripts {
        let valid_name = !name.is_empty()
            && !matches!(name.as_str(), "." | "..")
            && name
                .bytes()
                .all(|byte| byte.is_ascii_alphanumeric() || matches!(byte, b'.' | b'_' | b'-'));
        if !valid_name {
            return Err(format!(
                "console script name {name:?} is invalid: use only ASCII letters, digits, `.`, `_` and `-`"
            ));
        }
        let module = target
            .split_once(':')
            .filter(|(module, attribute)| dotted_identifier(module) && dotted_identifier(attribute))
            .map(|(module, _)| module)
            .ok_or_else(|| {
                format!(
                    "console script {name:?} target {target:?} must be `module:function` with dotted Python identifiers"
                )
            })?;
        let root = module.split('.').next().unwrap_or_default();
        if COTT_OWNED_ROOTS.contains(&root) || generated_roots.contains(root) {
            return Err(format!(
                "console script {name:?} target {target:?} names Cott-generated code; target an authored adapter module"
            ));
        }
        let path = module.replace('.', "/");
        if !authored.contains(&format!("{path}.py"))
            && !authored.contains(&format!("{path}/__init__.py"))
        {
            return Err(format!(
                "console script {name:?} target {target:?} is not an authored adapter module in the deployment"
            ));
        }
        validated.insert(name.as_str(), target.as_str());
    }
    Ok(validated)
}

fn dotted_identifier(value: &str) -> bool {
    value.split('.').all(|part| {
        let mut bytes = part.bytes();
        bytes
            .next()
            .is_some_and(|byte| byte.is_ascii_alphabetic() || byte == b'_')
            && bytes.all(|byte| byte.is_ascii_alphanumeric() || byte == b'_')
    })
}

fn metadata(name: &str, version: &str, project: &PyProject) -> String {
    let mut text = format!("Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n");
    if let Some(requires_python) = &project.requires_python {
        let _ = writeln!(text, "Requires-Python: {requires_python}");
    }
    for dependency in &project.dependencies {
        let _ = writeln!(text, "Requires-Dist: {dependency}");
    }
    text
}

fn entry_points(scripts: &BTreeMap<&str, &str>) -> String {
    let mut text = String::from("[console_scripts]\n");
    for (name, target) in scripts {
        let _ = writeln!(text, "{name} = {target}");
    }
    text
}

/// The RECORD of every other member, plus its own row without a hash or size.
fn record_file(members: &BTreeMap<String, Cow<'_, [u8]>>, record: &str) -> String {
    let mut rows = BTreeMap::new();
    for (name, bytes) in members {
        let digest = urlsafe_base64(&Sha256::digest(bytes));
        rows.insert(name.as_str(), format!("sha256={digest},{}", bytes.len()));
    }
    rows.insert(record, ",".to_owned());
    let mut text = String::new();
    for (name, hash_and_size) in rows {
        csv_field(&mut text, name);
        text.push(',');
        text.push_str(&hash_and_size);
        text.push('\n');
    }
    text
}

fn csv_field(text: &mut String, field: &str) {
    if !field.contains([',', '"', '\r', '\n']) {
        text.push_str(field);
        return;
    }
    text.push('"');
    for character in field.chars() {
        if character == '"' {
            text.push('"');
        }
        text.push(character);
    }
    text.push('"');
}

/// URL-safe base64 without padding: the digest encoding of RECORD.
fn urlsafe_base64(bytes: &[u8]) -> String {
    const ALPHABET: &[u8; 64] = b"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_";
    let mut text = String::with_capacity(bytes.len().div_ceil(3) * 4);
    for chunk in bytes.chunks(3) {
        let group = u32::from(chunk[0]) << 16
            | u32::from(chunk.get(1).copied().unwrap_or(0)) << 8
            | u32::from(chunk.get(2).copied().unwrap_or(0));
        for (index, shift) in [18, 12, 6, 0].into_iter().enumerate() {
            if index <= chunk.len() {
                text.push(char::from(ALPHABET[(group >> shift) as usize & 0x3f]));
            }
        }
    }
    text
}

const LOCAL_FILE_HEADER: u32 = 0x0403_4b50;
const CENTRAL_DIRECTORY_HEADER: u32 = 0x0201_4b50;
const END_OF_CENTRAL_DIRECTORY: u32 = 0x0605_4b50;
const STORED: u16 = 0;
const DEFLATED: u16 = 8;
/// General-purpose flag: member names are UTF-8.
const UTF8_NAMES: u16 = 1 << 11;
/// 1980-01-01 00:00:00, the ZIP epoch.
const DOS_TIME: u16 = 0;
const DOS_DATE: u16 = (1 << 5) | 1;
/// "Made by" a Unix host (3) with ZIP specification 2.0, so external attributes are modes.
const MADE_BY_UNIX: u16 = (3 << 8) | 20;
/// Regular file, `rw-r--r--`.
const REGULAR_FILE_0644: u32 = 0o100_644 << 16;

/// Serializes members in name order without Zip64. `u16::MAX` and `u32::MAX` are Zip64
/// sentinels, so values that reach them are rejected rather than emitted ambiguously.
fn zip(members: &BTreeMap<String, Cow<'_, [u8]>>) -> Result<Vec<u8>, String> {
    let too_large = || "wheel exceeds the ZIP size limits".to_owned();
    let field16 = |value: usize| {
        u16::try_from(value)
            .ok()
            .filter(|&value| value != u16::MAX)
            .ok_or_else(too_large)
    };
    let field32 = |value: usize| {
        u32::try_from(value)
            .ok()
            .filter(|&value| value != u32::MAX)
            .ok_or_else(too_large)
    };
    let mut archive = Vec::new();
    let mut directory = Vec::new();
    for (name, data) in members {
        let offset = field32(archive.len())?;
        let (method, body) = compress(data)?;
        let mut crc = Crc::new();
        crc.update(data);
        let crc = crc.sum();
        let flags = if name.is_ascii() { 0 } else { UTF8_NAMES };
        let extract_version: u16 = if method == DEFLATED { 20 } else { 10 };
        let name_length = field16(name.len())?;
        let compressed = field32(body.len())?;
        let uncompressed = field32(data.len())?;

        put_u32(&mut archive, LOCAL_FILE_HEADER);
        put_u16(&mut archive, extract_version);
        put_u16(&mut archive, flags);
        put_u16(&mut archive, method);
        put_u16(&mut archive, DOS_TIME);
        put_u16(&mut archive, DOS_DATE);
        put_u32(&mut archive, crc);
        put_u32(&mut archive, compressed);
        put_u32(&mut archive, uncompressed);
        put_u16(&mut archive, name_length);
        put_u16(&mut archive, 0);
        archive.extend_from_slice(name.as_bytes());
        archive.extend_from_slice(&body);

        put_u32(&mut directory, CENTRAL_DIRECTORY_HEADER);
        put_u16(&mut directory, MADE_BY_UNIX);
        put_u16(&mut directory, extract_version);
        put_u16(&mut directory, flags);
        put_u16(&mut directory, method);
        put_u16(&mut directory, DOS_TIME);
        put_u16(&mut directory, DOS_DATE);
        put_u32(&mut directory, crc);
        put_u32(&mut directory, compressed);
        put_u32(&mut directory, uncompressed);
        put_u16(&mut directory, name_length);
        put_u16(&mut directory, 0);
        put_u16(&mut directory, 0);
        put_u16(&mut directory, 0);
        put_u16(&mut directory, 0);
        put_u32(&mut directory, REGULAR_FILE_0644);
        put_u32(&mut directory, offset);
        directory.extend_from_slice(name.as_bytes());
    }
    let entries = field16(members.len())?;
    let directory_offset = field32(archive.len())?;
    let directory_size = field32(directory.len())?;
    archive.extend_from_slice(&directory);
    put_u32(&mut archive, END_OF_CENTRAL_DIRECTORY);
    put_u16(&mut archive, 0);
    put_u16(&mut archive, 0);
    put_u16(&mut archive, entries);
    put_u16(&mut archive, entries);
    put_u32(&mut archive, directory_size);
    put_u32(&mut archive, directory_offset);
    put_u16(&mut archive, 0);
    Ok(archive)
}

/// Deflates a member unless that does not make it smaller.
fn compress(data: &[u8]) -> Result<(u16, Cow<'_, [u8]>), String> {
    if data.is_empty() {
        return Ok((STORED, Cow::Borrowed(data)));
    }
    let mut encoder = DeflateEncoder::new(Vec::new(), Compression::best());
    encoder
        .write_all(data)
        .map_err(|error| format!("compress wheel member: {error}"))?;
    let deflated = encoder
        .finish()
        .map_err(|error| format!("compress wheel member: {error}"))?;
    Ok(if deflated.len() < data.len() {
        (DEFLATED, Cow::Owned(deflated))
    } else {
        (STORED, Cow::Borrowed(data))
    })
}

fn put_u16(bytes: &mut Vec<u8>, value: u16) {
    bytes.extend_from_slice(&value.to_le_bytes());
}

fn put_u32(bytes: &mut Vec<u8>, value: u32) {
    bytes.extend_from_slice(&value.to_le_bytes());
}

#[cfg(test)]
mod tests {
    use super::distribution_name;

    // Manifest validation already limits Python project names to PEP 503 form, so the
    // deployment tests only reach the hyphen case; these rules are the wheel's own contract.
    #[test]
    fn distribution_names_collapse_separator_runs_and_lowercase() {
        for (name, expected) in [
            ("real-posting", "real_posting"),
            ("Demo.Tool__x-y", "demo_tool_x_y"),
            ("a", "a"),
        ] {
            assert_eq!(distribution_name(name).as_deref(), Ok(expected), "{name}");
        }
    }

    #[test]
    fn names_that_cannot_name_a_wheel_are_refused() {
        for name in ["", "-demo", "demo-", "demo app", "démo", "de/mo"] {
            assert!(distribution_name(name).is_err(), "{name:?}");
        }
    }
}
