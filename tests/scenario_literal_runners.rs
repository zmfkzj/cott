//! The Python contract runner executes `Bytes("hex")`, `JsonValue` and
//! const-sized Array/Buffer scenario literals through the emitted facades.
//! Skipped when no `python3` is available.

use std::fs;
use std::io::Write;
use std::path::{Path, PathBuf};
use std::process::{Command, Output, Stdio};

use cott::binding::{BindingOwner, ResolvedBinding};
use cott::compiler::{SourceFile, parse_project};
use cott::contract_test::derive_strategies;
use cott::hash::sha256_hex;
use cott::manifest::VerificationConfig;
use cott::python::artifact_plan::{PythonArtifactPlan, PythonCallableKind};
use serde_json::{Value, json};

const CONTRACT: &str = r#"module demo

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
        "items": JsonValue.Array(value: List(JsonValue.Null, JsonValue.Boolean(value: false), JsonValue.String(value: "x"), JsonValue.Float(value: -0.5))),
        "n": JsonValue.Integer(value: -7),
    ))
    call echoed = echo_json(document)
    assert echoed == JsonValue.Object(value: Map(
        "n": JsonValue.Integer(value: -7),
        "items": JsonValue.Array(value: List(JsonValue.Null, JsonValue.Boolean(value: false), JsonValue.String(value: "x"), JsonValue.Float(value: -0.5))),
    ))
    call sum = total(Array(3, 4))
    assert sum == 7
    call flipped = flip(Buffer("0102"))
    assert flipped == Buffer("0201")
"#;

const ECHO_BYTES: &str = "def echo_bytes(payload: bytes) -> bytes:\n    return payload\n";

const DESCRIBE: &str = "from cott_runtime import JsonArray, JsonBoolean, JsonFloat, JsonInteger, JsonNull, JsonObject, JsonString, JsonValue\n\ndef describe(value: JsonValue) -> str:\n    kinds = ((JsonNull, \"null\"), (JsonBoolean, \"boolean\"), (JsonInteger, \"integer\"), (JsonFloat, \"float\"), (JsonString, \"string\"), (JsonArray, \"array\"), (JsonObject, \"object\"))\n    return next(name for kind, name in kinds if isinstance(value, kind))\n";

const TOTAL: &str = "def total(items: object) -> int:\n    return sum(items)\n";

fn echo_json(result: &str) -> String {
    format!(
        "from cott_runtime import JsonNull, JsonValue\n\ndef echo_json(value: JsonValue) -> JsonValue:\n    return {result}\n"
    )
}

fn flip(data: &str) -> String {
    format!(
        "from cott_runtime import CottBuffer\n\ndef flip(data: CottBuffer) -> CottBuffer:\n    return CottBuffer(data={data})\n"
    )
}

fn run(echo_json_result: &str, flip_data: &str) -> Option<Output> {
    let echo = echo_json(echo_json_result);
    let flipped = flip(flip_data);
    run_scenario(
        CONTRACT,
        &[
            ("demo.echo_bytes", ECHO_BYTES),
            ("demo.describe", DESCRIBE),
            ("demo.echo_json", &echo),
            ("demo.total", TOTAL),
            ("demo.flip", &flipped),
        ],
        "demo.scenario.literals",
    )
}

#[test]
fn python_runner_passes_bytes_json_and_const_sized_literals() {
    let Some(output) = run("value", "bytes(reversed(data.data))") else {
        return;
    };
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let report: Value = serde_json::from_slice(&output.stdout).expect("runner JSON");
    assert_eq!(report["scenarios"][0]["grade"], "test observation");
    assert_eq!(
        report["scenarios"][0]["assertions"]
            .as_array()
            .map(Vec::len),
        Some(6)
    );
}

#[test]
fn python_runner_fails_wrong_json_payloads_and_named_buffer_lengths() {
    // A different JsonValue fails the payload equality assertion.
    let Some(output) = run("JsonNull()", "bytes(reversed(data.data))") else {
        return;
    };
    assert!(!output.status.success());
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(stderr.contains("assertion step:8 failed"), "{stderr}");

    // `Buffer[SIZE]` is enforced at the facade with the constant's value.
    let Some(output) = run("value", "data.data + b\"\\x00\"") else {
        return;
    };
    assert!(!output.status.success());
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(stderr.contains("CottContractViolation"), "{stderr}");
}

/// Emit boundary-mode Python facades for manifest-bound free functions and
/// run the compiler's contract runner on one scenario.
fn run_scenario(source: &str, implementations: &[(&str, &str)], scenario: &str) -> Option<Output> {
    let mut config = cott::manifest::ProjectConfig::parse(
        Path::new("cott.toml"),
        "[project]\nname = \"demo\"\nversion = \"0.4.0\"\nsource = \"src\"\n\
         [target.python]\nsource = \"python\"\ngenerated = \"generated/python\"\n\
         stubs = \"generated/stubs\"\ninterpreter = \".venv/bin/python\"\n\
         type_checker = \".venv/bin/basedpyright\"\nruntime_validation = \"boundary\"\n",
    )
    .expect("fixture manifest");
    let parsed = parse_project([SourceFile::new("src/demo.cott", source)]).expect("fixture parse");
    let hir = cott::hir::lower(Path::new("src"), parsed).expect("fixture lower");
    let ir = cott::ir::render(&hir).expect("fixture canonical IR");
    let plan = PythonArtifactPlan::from_ir(&ir).expect("fixture plan");
    let callables = plan.callables();
    let bindings = implementations
        .iter()
        .map(|(symbol, source)| {
            let callable = callables
                .iter()
                .find(|callable| callable.cott_symbol == *symbol)
                .expect("fixture callable");
            assert_eq!(callable.kind, PythonCallableKind::Function);
            let implementation_module = format!("cott_bindings.{symbol}");
            config.python.implementations.insert(
                (*symbol).to_owned(),
                format!("{implementation_module}:{}", callable.name),
            );
            ResolvedBinding {
                module: callable.module.clone(),
                function: callable.name.clone(),
                cott_symbol: callable.cott_symbol.clone(),
                kind: callable.kind.clone(),
                implementation_module: implementation_module.clone(),
                implementation_function: callable.name.clone(),
                owner: BindingOwner::Manifest,
                source: PathBuf::from("python")
                    .join(format!("{}.py", implementation_module.replace('.', "/"))),
                generated_relative: PathBuf::from("_cott_impl")
                    .join(&callable.module)
                    .join(format!("{}.py", callable.name)),
                bytes: source.as_bytes().to_vec(),
                sha256: sha256_hex(source.as_bytes()),
            }
        })
        .collect::<Vec<_>>();
    let mut files = cott::python_emit::emit(&config, &plan, &ir, &bindings)
        .expect("fixture emission")
        .files;
    let strategies = derive_strategies(&ir, &VerificationConfig::default())
        .expect("fixture strategies")
        .into_iter()
        .filter(|strategy| strategy.symbol == scenario)
        .collect::<Vec<_>>();
    let modules = ir
        .modules
        .iter()
        .map(|module| serde_json::from_slice::<Value>(&module.bytes).unwrap())
        .collect::<Vec<_>>();
    let request =
        json!({"modules": modules, "runtime_validation": "boundary", "strategies": strategies});

    if !Command::new("python3")
        .arg("--version")
        .output()
        .is_ok_and(|output| output.status.success())
    {
        return None;
    }
    // Record the interpreter that actually executes the emitted fixture so
    // runtime provenance checks stay active.
    let bytes = files
        .get_mut(Path::new("generation.json"))
        .expect("emitted generation record");
    let inspected = Command::new("python3")
        .args([
            "-c",
            r#"import hashlib,json,pathlib,platform,sys,sysconfig
e=pathlib.Path(sys.executable).resolve()
print(json.dumps({"cache_tag":sys.implementation.cache_tag,"content_hash":"sha256:"+hashlib.sha256(e.read_bytes()).hexdigest(),"executable":str(e),"implementation":sys.implementation.name,"machine":platform.machine(),"os":sys.platform,"platform":sysconfig.get_platform(),"version":platform.python_version()}))
"#,
        ])
        .output()
        .expect("Python should inspect fixture provenance");
    assert!(inspected.status.success());
    let python_tools: Value =
        serde_json::from_slice(&inspected.stdout).expect("Python tool evidence JSON");
    let mut record: cott::provenance::GenerationRecord =
        serde_json::from_slice(bytes).expect("emitted generation record");
    for snapshot in std::iter::once(&mut record.current).chain(record.last_verified.iter_mut()) {
        snapshot.tools["python"] = python_tools.clone();
        snapshot
            .compute_generation_id()
            .expect("recompute fixture generation identity");
    }
    *bytes = record
        .canonical_bytes()
        .expect("serialize fixture generation record");

    let root = std::env::temp_dir().join(format!(
        "cott-scenario-literals-{}-{}",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .expect("clock after epoch")
            .as_nanos()
    ));
    fs::create_dir(&root).expect("fixture directory");
    for (relative, bytes) in files {
        let path = root.join(relative);
        fs::create_dir_all(path.parent().expect("fixture file parent")).expect("fixture parent");
        fs::write(path, bytes).expect("fixture file");
    }
    let python = root.join("python");
    let mut child = Command::new("python3")
        .args(["-c", include_str!("../src/contract_runner.py")])
        .current_dir(&python)
        .env("PYTHONPATH", &python)
        .env("PYTHONDONTWRITEBYTECODE", "1")
        .env("PYTHONHASHSEED", "0")
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped())
        .spawn()
        .expect("contract runner should start");
    child
        .stdin
        .take()
        .expect("contract runner stdin")
        .write_all(request.to_string().as_bytes())
        .expect("contract runner request");
    let output = child
        .wait_with_output()
        .expect("contract runner should finish");
    fs::remove_dir_all(root).expect("fixture cleanup");
    Some(output)
}
