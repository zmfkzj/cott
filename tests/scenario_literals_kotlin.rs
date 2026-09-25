//! Kotlin conformance for `Bytes("hex")`, `JsonValue` and const-sized
//! Array/Buffer scenario literals through the real `cott verify` runner.
//!
//! Native tests are ignored unless the pinned toolchain is available:
//! `COTT_KOTLIN_HOME=<kotlinc 2.2.10> JAVA_HOME=<JDK 17> cargo test --test scenario_literals_kotlin -- --ignored --test-threads=1`

use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::sync::atomic::{AtomicU64, Ordering};

use cott::compiler::{SourceFile, parse_project};
use cott::hir::lower;
use cott::ir::render;
use cott::kotlin::KotlinPlan;
use cott::kotlin::emit::implementation_signature;
use serde_json::Value;

#[path = "support/snapshot.rs"]
mod snapshot;

static NEXT_PROJECT: AtomicU64 = AtomicU64::new(0);

const CONTRACT: &str = r#"module example.literals

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

const ECHO_BYTES: &str = "    return payload\n";
const DESCRIBE: &str = "    return when (value) {
        cott_runtime.JsonNull -> \"null\"
        is cott_runtime.JsonBoolean -> \"boolean\"
        is cott_runtime.JsonInteger -> \"integer\"
        is cott_runtime.JsonFloat -> \"float\"
        is cott_runtime.JsonString -> \"string\"
        is cott_runtime.JsonArray -> \"array\"
        is cott_runtime.JsonObject -> \"object\"
    }
";
const TOTAL: &str = "    return items.fold(0u) { sum, item -> sum + item.toUInt() }\n";

struct Project {
    root: PathBuf,
}

impl Project {
    /// A manifest-bound Kotlin project whose bindings use the exact canonical
    /// implementation signatures of `CONTRACT`.
    fn new(compiler: &Path, java: &Path, bodies: &[(&str, &str)]) -> Self {
        let root = project_root();
        let binding_dir = root.join("kotlin/cott_bindings/literals");
        fs::create_dir_all(&binding_dir).expect("create Kotlin binding directory");
        fs::create_dir_all(root.join("src/example")).expect("create contract directory");
        fs::write(root.join("src/example/literals.cott"), CONTRACT).expect("write contract");
        let parsed = parse_project([SourceFile::new("src/example/literals.cott", CONTRACT)])
            .expect("literal contract parses");
        let ir = render(&lower(Path::new("src"), parsed).expect("literal contract lowers"))
            .expect("literal contract renders canonical IR");
        let plan = KotlinPlan::from_ir(&ir).expect("literal contract projects to Kotlin");
        let mut implementations = String::new();
        for callable in plan.callables() {
            let body = bodies
                .iter()
                .find(|(name, _)| *name == callable.name)
                .map(|(_, body)| *body)
                .unwrap_or_else(|| panic!("no Kotlin body for `{}`", callable.symbol));
            let signature =
                implementation_signature(&plan, &callable).expect("canonical Kotlin signature");
            fs::write(
                binding_dir.join(format!("{}.kt", callable.name)),
                format!("package cott_bindings.literals\n\n{signature} {{\n{body}}}\n"),
            )
            .expect("write Kotlin binding");
            implementations.push_str(&format!(
                "{:?} = {:?}\n",
                callable.symbol,
                format!("cott_bindings.literals.{}", callable.name)
            ));
        }
        fs::write(
            root.join("cott.toml"),
            format!(
                r#"[project]
name = "kotlin-literals-conformance"
version = "0.1.0"
source = "src"

[target.kotlin]
source = "kotlin"
generated = "generated/kotlin"
compiler = {:?}
java = {:?}
jvm_target = 17
runtime_validation = "boundary"

[target.kotlin.implementations]
{implementations}"#,
                compiler.to_string_lossy(),
                java.to_string_lossy(),
            ),
        )
        .expect("write Kotlin manifest");
        Self { root }
    }

    fn native(bodies: &[(&str, &str)]) -> Self {
        let kotlin_home = std::env::var_os("COTT_KOTLIN_HOME")
            .map(PathBuf::from)
            .unwrap_or_else(|| PathBuf::from("/tmp/cott-kotlin-toolchain/kotlinc"));
        let java_home = std::env::var_os("JAVA_HOME")
            .map(PathBuf::from)
            .unwrap_or_else(|| PathBuf::from("/tmp/cott-kotlin-toolchain/jdk"));
        Self::new(
            &kotlin_home.join("bin/kotlinc"),
            &java_home.join("bin/java"),
            bodies,
        )
    }

    fn cott(&self, arguments: &[&str]) -> Output {
        Command::new(env!("CARGO_BIN_EXE_cott"))
            .args(arguments)
            .args(["--project"])
            .arg(&self.root)
            .env("PATH", "/usr/bin:/bin")
            .output()
            .expect("run cott")
    }

    fn generation(&self) -> Value {
        snapshot::read(
            &fs::read(self.root.join("generated/generation.json"))
                .expect("read Kotlin generation record"),
        )
    }

    fn verify(&self) -> Output {
        assert_success("Kotlin emission", self.cott(&["emit", "kotlin"]));
        self.cott(&["verify"])
    }
}

impl Drop for Project {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.root);
    }
}

fn project_root() -> PathBuf {
    let mut nonce = NEXT_PROJECT.fetch_add(1, Ordering::Relaxed);
    loop {
        let candidate = std::env::temp_dir().join(format!(
            "cott-kotlin-scenario-literals-{}-{nonce}",
            std::process::id()
        ));
        match fs::create_dir(&candidate) {
            Ok(()) => return candidate,
            Err(error) if error.kind() == io::ErrorKind::AlreadyExists => {
                nonce = nonce.saturating_add(1);
            }
            Err(error) => panic!("create Kotlin literal project: {error}"),
        }
    }
}

fn assert_success(label: &str, output: Output) {
    assert!(
        output.status.success(),
        "{label} failed with {:?}\nstdout:\n{}\nstderr:\n{}",
        output.status.code(),
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr),
    );
}

fn bodies<'a>(echo_json: &'a str, flip: &'a str) -> [(&'a str, &'a str); 5] {
    [
        ("echo_bytes", ECHO_BYTES),
        ("describe", DESCRIBE),
        ("echo_json", echo_json),
        ("total", TOTAL),
        ("flip", flip),
    ]
}

const CORRECT_ECHO: &str = "    return value\n";
const CORRECT_FLIP: &str =
    "    return cott_runtime.CottBuffer(data.toByteArray().reversedArray(), data.dimension)\n";

#[test]
fn kotlin_emission_accepts_scenario_literals_without_a_toolchain() {
    let project = Project::new(
        Path::new("kotlinc-never-run"),
        Path::new("java"),
        &bodies(CORRECT_ECHO, CORRECT_FLIP),
    );
    assert_success("Kotlin emission", project.cott(&["emit", "kotlin"]));
    let current = &project.generation()["current"];
    assert_eq!(current["unresolved"], serde_json::json!([]), "{current}");
    assert_eq!(current["verified"], false);
}

#[test]
#[ignore = "requires the pinned Kotlin 2.2.10/JDK 17 toolchain and bubblewrap"]
fn kotlin_runner_passes_bytes_json_and_const_sized_literals() {
    let project = Project::native(&bodies(CORRECT_ECHO, CORRECT_FLIP));
    assert_success("Kotlin verification", project.verify());
    let generation = project.generation();
    let current = &generation["current"];
    assert_eq!(current["verified"], true);
    let scenario = current["verification"]["contract_tests"]["scenarios"]
        .as_array()
        .expect("scenario evidence")
        .iter()
        .find(|scenario| scenario["scenario_id"] == "example.literals.scenario.literals")
        .unwrap_or_else(|| panic!("literal scenario was not executed: {current}"));
    assert_eq!(scenario["status"], "passed");
    assert_eq!(scenario["assertions"], 6);
}

#[test]
#[ignore = "requires the pinned Kotlin 2.2.10/JDK 17 toolchain and bubblewrap"]
fn kotlin_runner_fails_wrong_json_payloads_and_named_buffer_lengths() {
    for (echo_json, flip, reason) in [
        // A different JsonValue fails the payload equality assertion.
        (
            "    return cott_runtime.JsonNull\n",
            CORRECT_FLIP,
            "Kotlin scenario `example.literals.scenario.literals` failed",
        ),
        // `Buffer[SIZE]` is enforced with the constant's value at the facade.
        (
            CORRECT_ECHO,
            "    return cott_runtime.CottBuffer(data.toByteArray() + byteArrayOf(0), data.dimension)\n",
            "Kotlin contract execution failed for `example.literals.flip`",
        ),
    ] {
        let project = Project::native(&bodies(echo_json, flip));
        let output = project.verify();
        let stderr = String::from_utf8_lossy(&output.stderr);
        assert!(
            !output.status.success() && stderr.contains(reason),
            "wrong implementation must be rejected by `{reason}`\nstdout:\n{}\nstderr:\n{stderr}",
            String::from_utf8_lossy(&output.stdout),
        );
        assert_eq!(project.generation()["current"]["verified"], false);
    }
}
