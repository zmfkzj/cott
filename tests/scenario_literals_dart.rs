//! Dart conformance for `Bytes("hex")`, `JsonValue` and const-sized
//! Array/Buffer scenario literals through the real `cott verify` runner.
//! Native tests need `COTT_DART` (absolute Dart 3.13.3 SDK path) and bubblewrap:
//! `cargo test --test scenario_literals_dart -- --ignored --test-threads=1`

use std::fs;
use std::io;
use std::path::PathBuf;
use std::process::{Command, Output};
use std::sync::atomic::{AtomicU64, Ordering};

use serde_json::Value;

#[path = "support/snapshot.rs"]
mod snapshot;

static NEXT_TEMP: AtomicU64 = AtomicU64::new(0);

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

const ECHO_BYTES: &str = "Object _echo_bytes() {\n  return payload;\n}\n";
const DESCRIBE: &str = "Object _describe() {
  return switch (value) {
    cott_runtime.JsonNull() => 'null',
    cott_runtime.JsonBoolean() => 'boolean',
    cott_runtime.JsonInteger() => 'integer',
    cott_runtime.JsonFloat() => 'float',
    cott_runtime.JsonString() => 'string',
    cott_runtime.JsonArray() => 'array',
    cott_runtime.JsonObject() => 'object',
  };
}
";
const TOTAL: &str =
    "Object _total() {\n  return items.fold<int>(0, (sum, item) => sum + item);\n}\n";
const CORRECT_ECHO: &str = "Object _echo_json() {\n  return value;\n}\n";
const CORRECT_FLIP: &str =
    "Object _flip() {\n  return cott_runtime.CottBuffer(data.reversed, data.dimension);\n}\n";

struct Fixture(PathBuf);

impl Fixture {
    /// A manifest-bound Dart project whose private implementations take the
    /// canonical signature of each callable and the given body.
    fn new(echo_json: &str, flip: &str) -> Self {
        let mut number = NEXT_TEMP.fetch_add(1, Ordering::Relaxed);
        let root = loop {
            let path = std::env::temp_dir().join(format!(
                "cott-dart-scenario-literals-{}-{number}",
                std::process::id()
            ));
            match fs::create_dir(&path) {
                Ok(()) => break path,
                Err(error) if error.kind() == io::ErrorKind::AlreadyExists => number += 1,
                Err(error) => panic!("create Dart literal fixture: {error}"),
            }
        };
        fs::create_dir_all(root.join("src/demo")).expect("Cott source directory");
        fs::create_dir_all(root.join("dart/bindings")).expect("Dart binding directory");
        fs::write(root.join("src/demo/runner.cott"), CONTRACT).expect("Cott source");
        let dart = PathBuf::from(
            std::env::var_os("COTT_DART").expect("COTT_DART must name the provisioned Dart SDK"),
        );
        assert!(dart.is_absolute(), "COTT_DART must be absolute");
        let parsed = cott::compiler::parse_project([cott::compiler::SourceFile::new(
            "demo/runner.cott",
            CONTRACT,
        )])
        .expect("literal contract");
        let hir = cott::hir::lower(std::path::Path::new("src"), parsed).expect("literal HIR");
        let ir = cott::ir::render(&hir).expect("literal IR");
        let plan = cott::dart::DartPlan::from_ir(&ir).expect("literal plan");
        let mut manifest = format!(
            "[project]\nname = \"demo\"\nversion = \"0.1.0\"\nsource = \"src\"\n\n\
             [target.dart]\nsource = \"dart\"\ngenerated = \"generated/dart\"\nsdk = {:?}\n\
             runtime_validation = \"boundary\"\n\n[target.dart.implementations]\n",
            dart.to_string_lossy()
        );
        for (name, body) in [
            ("echo_bytes", ECHO_BYTES),
            ("describe", DESCRIBE),
            ("echo_json", echo_json),
            ("total", TOTAL),
            ("flip", flip),
        ] {
            let symbol = format!("demo.runner.{name}");
            let private_name = format!("_{name}");
            let callable = plan
                .callables()
                .iter()
                .find(|callable| callable.symbol == symbol)
                .expect("literal callable");
            let signature = cott::dart::emit::implementation_signature(&plan, callable)
                .expect("canonical signature")
                .replacen(
                    &format!("_cott_{}", symbol.replace('.', "_")),
                    &private_name,
                    1,
                );
            let (_, function_body) = body.split_once('{').expect("fixture body");
            fs::write(
                root.join("dart/bindings").join(format!("{name}.dart")),
                format!("{signature} {{{function_body}"),
            )
            .expect("Dart implementation");
            manifest.push_str(&format!(
                "{symbol:?} = {:?}\n",
                format!("bindings/{name}.dart:{private_name}")
            ));
        }
        fs::write(root.join("cott.toml"), manifest).expect("Dart manifest");
        Self(root)
    }

    fn run(&self, arguments: &[&str]) -> Output {
        let home = self.0.join("home");
        let pub_cache = self.0.join("pub-cache");
        fs::create_dir_all(&home).expect("isolated Dart home");
        fs::create_dir_all(&pub_cache).expect("isolated Dart pub cache");
        Command::new(env!("CARGO_BIN_EXE_cott"))
            .args(arguments)
            .args(["--project"])
            .arg(&self.0)
            .env_clear()
            .env("HOME", home)
            .env("PUB_CACHE", pub_cache)
            .output()
            .expect("cott should run with the provisioned Dart SDK")
    }

    fn generation(&self) -> Value {
        snapshot::read(&fs::read(self.0.join("generated/generation.json")).expect("record"))
    }

    fn verify(&self) -> Output {
        let emitted = self.run(&["emit", "dart"]);
        assert_eq!(
            emitted.status.code(),
            Some(0),
            "{}",
            String::from_utf8_lossy(&emitted.stderr)
        );
        self.run(&["verify"])
    }
}

impl Drop for Fixture {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.0);
    }
}

#[test]
#[ignore = "requires COTT_DART, bubblewrap, and the provisioned Dart 3.13.3 SDK"]
fn dart_runner_passes_bytes_json_and_const_sized_literals() {
    let fixture = Fixture::new(CORRECT_ECHO, CORRECT_FLIP);
    let verified = fixture.verify();
    assert_eq!(
        verified.status.code(),
        Some(0),
        "{}",
        String::from_utf8_lossy(&verified.stderr)
    );
    let generation = fixture.generation();
    assert_eq!(generation["current"]["verified"], true);
    let scenario = generation["current"]["verification"]["contract_tests"]["scenarios"]
        .as_array()
        .expect("scenario evidence")
        .iter()
        .find(|scenario| scenario["scenario_id"] == "demo.runner.scenario.literals")
        .expect("literal scenario evidence");
    assert_eq!(scenario["status"], "passed", "{scenario}");
    assert_eq!(scenario["assertions"], 6, "{scenario}");
    assert_eq!(scenario["cleaned"], true, "{scenario}");
}

#[test]
#[ignore = "requires COTT_DART, bubblewrap, and the provisioned Dart 3.13.3 SDK"]
fn dart_runner_fails_wrong_json_payloads_and_named_buffer_lengths() {
    for (echo_json, flip, reason) in [
        // A different JsonValue fails the payload equality assertion.
        (
            "Object _echo_json() {\n  return const cott_runtime.JsonNull();\n}\n",
            CORRECT_FLIP,
            "demo.runner.scenario.literals",
        ),
        // `Buffer[SIZE]` is enforced with the constant's value.
        (
            CORRECT_ECHO,
            "Object _flip() {\n  return cott_runtime.CottBuffer([...data, 0], data.dimension);\n}\n",
            "demo.runner.flip",
        ),
    ] {
        let fixture = Fixture::new(echo_json, flip);
        let rejected = fixture.verify();
        let stderr = String::from_utf8_lossy(&rejected.stderr);
        assert_eq!(rejected.status.code(), Some(4), "{stderr}");
        assert!(
            stderr.contains(reason),
            "expected rejection by `{reason}`:\n{stderr}"
        );
        assert_eq!(fixture.generation()["current"]["verified"], false);
    }
}
