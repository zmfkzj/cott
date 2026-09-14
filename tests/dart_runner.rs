use std::fs;
use std::io;
use std::path::PathBuf;
use std::process::{Command, Output};
use std::sync::atomic::{AtomicU64, Ordering};

use serde_json::Value;

static NEXT_TEMP: AtomicU64 = AtomicU64::new(0);

struct TempDir(PathBuf);

impl TempDir {
    fn new(label: &str) -> Self {
        let mut number = NEXT_TEMP.fetch_add(1, Ordering::Relaxed);
        loop {
            let path = std::env::temp_dir().join(format!(
                "cott-dart-runner-{label}-{}-{number}",
                std::process::id()
            ));
            match fs::create_dir(&path) {
                Ok(()) => return Self(path),
                Err(error) if error.kind() == io::ErrorKind::AlreadyExists => number += 1,
                Err(error) => panic!("create Dart runner fixture: {error}"),
            }
        }
    }
}

impl Drop for TempDir {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.0);
    }
}

struct Fixture {
    temp: TempDir,
}

impl Fixture {
    fn new(label: &str, source: &str, bindings: &[(&str, &str, &str, &str)]) -> Self {
        let temp = TempDir::new(label);
        fs::create_dir_all(temp.0.join("src/demo")).expect("Cott source directory");
        fs::create_dir_all(temp.0.join("dart/bindings")).expect("Dart binding directory");
        let dart = native_dart();
        let mut manifest = format!(
            r#"[project]
name = "demo"
version = "0.1.0"
source = "src"

[target.dart]
source = "dart"
generated = "generated/dart"
sdk = {:?}
runtime_validation = "boundary"

[target.dart.implementations]
"#,
            dart.to_string_lossy()
        );
        for &(symbol, file, private_name, _) in bindings {
            manifest.push_str(&format!(
                "{symbol:?} = {:?}\n",
                format!("bindings/{file}:{private_name}")
            ));
        }
        fs::write(temp.0.join("cott.toml"), manifest).expect("Dart manifest");
        fs::write(temp.0.join("src/demo/runner.cott"), source).expect("Cott source");
        let parsed = cott::compiler::parse_project([cott::compiler::SourceFile::new(
            "demo/runner.cott",
            source,
        )])
        .expect("runner contract");
        let hir = cott::hir::lower(std::path::Path::new("src"), parsed).expect("runner HIR");
        let ir = cott::ir::render(&hir).expect("runner IR");
        let plan = cott::dart::DartPlan::from_ir(&ir).expect("runner plan");
        for &(symbol, file, private_name, body) in bindings {
            let callable = plan
                .callables()
                .iter()
                .find(|callable| callable.symbol == symbol)
                .expect("runner callable");
            let signature = cott::dart::emit::implementation_signature(&plan, callable)
                .expect("canonical signature")
                .replacen(
                    &format!("_cott_{}", symbol.replace('.', "_")),
                    private_name,
                    1,
                );
            let partition = cott::dart::binding::partition_source(body.as_bytes())
                .expect("fixture source partition");
            let (_, function_body) = partition.body.split_once('{').expect("fixture body");
            let asynchronous = if callable.declaration["callable_kind"] == "async" {
                " async"
            } else {
                ""
            };
            let binding = format!(
                "{}\n{signature}{asynchronous} {{{function_body}",
                partition.imports.join("\n")
            );
            fs::write(temp.0.join("dart/bindings").join(file), binding)
                .expect("Dart implementation");
        }
        Self { temp }
    }

    fn run(&self, arguments: &[&str]) -> Output {
        let home = self.temp.0.join("home");
        let pub_cache = self.temp.0.join("pub-cache");
        fs::create_dir_all(&home).expect("isolated Dart home");
        fs::create_dir_all(&pub_cache).expect("isolated Dart pub cache");
        Command::new(env!("CARGO_BIN_EXE_cott"))
            .args(arguments)
            .args(["--project"])
            .arg(&self.temp.0)
            .env_clear()
            .env("HOME", home)
            .env("PUB_CACHE", pub_cache)
            .output()
            .expect("cott should run with the provisioned Dart SDK")
    }

    fn generation(&self) -> Value {
        serde_json::from_slice(
            &fs::read(self.temp.0.join("generated/generation.json")).expect("generation record"),
        )
        .expect("generation JSON")
    }
}

fn native_dart() -> PathBuf {
    let path = PathBuf::from(
        std::env::var_os("COTT_DART").expect("COTT_DART must name the provisioned Dart SDK"),
    );
    assert!(path.is_absolute(), "COTT_DART must be absolute");
    path
}

fn stderr(output: &Output) -> String {
    String::from_utf8_lossy(&output.stderr).into_owned()
}

fn has_positive_clause(generation: &Value, symbol: &str) -> bool {
    generation["current"]["semantic_coverage"]["clauses"]
        .as_array()
        .expect("semantic coverage clauses")
        .iter()
        .any(|clause| {
            clause["symbol"] == symbol
                && clause["evidence"].as_array().is_some_and(|evidence| {
                    evidence.iter().any(|entry| {
                        entry["status"] == "passed" && entry["positive_applicable"] == true
                    })
                })
        })
}

#[test]
#[ignore = "requires COTT_DART, bubblewrap, and the provisioned Dart 3.13.3 SDK"]
fn native_runner_observes_struct_initializer_and_public_receiver_method_clauses() {
    let fixture = Fixture::new(
        "structured",
        r#"module demo.runner

struct Amount:
    value: I32
    invariant self.value >= 0

fn unwrap(amount: Amount) -> I32:
    ensures result == amount.value

trait Reads:
    fn current(self) -> I32

impl Meter for Reads:
    state:
        base: I32

    invariant self.base >= 0

    init(base: I32):
        requires base >= 0
        ensures self.base == base

    fn current(self) -> I32:
        ensures result == self.base
"#,
        &[
            (
                "demo.runner.unwrap",
                "unwrap.dart",
                "_unwrap",
                "int _unwrap(Amount amount) {\n  return amount.value;\n}\n",
            ),
            (
                "demo.runner.Meter.current",
                "current.dart",
                "_current",
                "int _current(Meter self) {\n  return self.base$cott;\n}\n",
            ),
        ],
    );
    let emitted = fixture.run(&["emit", "dart"]);
    assert_eq!(emitted.status.code(), Some(0), "{}", stderr(&emitted));
    let verified = fixture.run(&["verify"]);
    assert_eq!(verified.status.code(), Some(0), "{}", stderr(&verified));

    let generation = fixture.generation();
    for symbol in [
        "demo.runner.Amount",
        "demo.runner.unwrap",
        "demo.runner.Meter.init",
        "demo.runner.Meter.current",
    ] {
        assert!(
            has_positive_clause(&generation, symbol),
            "missing observed evidence for {symbol}"
        );
    }
    let cases = generation["current"]["verification"]["contract_tests"]["cases"]
        .as_array()
        .expect("runner cases");
    for symbol in [
        "demo.runner.unwrap",
        "demo.runner.Meter.init",
        "demo.runner.Meter.current",
    ] {
        assert!(
            cases
                .iter()
                .any(|case| case["symbol"] == symbol && case["status"] == "passed"),
            "missing passing case for {symbol}"
        );
    }
    assert!(
        cases.iter().any(|case| {
            matches!(
                case["status"].as_str(),
                Some("ineligible" | "candidate_unavailable")
            )
        }),
        "bounded invalid constructors were not rejected"
    );
}

#[test]
#[ignore = "requires COTT_DART, bubblewrap, and the provisioned Dart 3.13.3 SDK"]
fn native_runner_rejects_an_authenticated_failed_clause() {
    let source = r#"module demo.runner

fn identity(value: I32) -> I32:
    ensures result == value
"#;
    let control = Fixture::new(
        "failed-clause-control",
        source,
        &[(
            "demo.runner.identity",
            "identity.dart",
            "_identity",
            "int _identity(int value) {\n  return value;\n}\n",
        )],
    );
    let emitted = control.run(&["emit", "dart"]);
    assert_eq!(emitted.status.code(), Some(0), "{}", stderr(&emitted));
    let verified = control.run(&["verify"]);
    assert_eq!(
        verified.status.code(),
        Some(0),
        "the matching control must establish a working SDK and runner: {}",
        stderr(&verified)
    );
    assert!(has_positive_clause(
        &control.generation(),
        "demo.runner.identity"
    ));
    assert!(
        control.generation()["current"]["verification"]["contract_tests"]["cases"]
            .as_array()
            .expect("identity runner cases")
            .iter()
            .any(|case| { case["symbol"] == "demo.runner.identity" && case["status"] == "passed" }),
        "identity must execute a passing public-facade case"
    );

    let fixture = Fixture::new(
        "failed-clause",
        source,
        &[(
            "demo.runner.identity",
            "identity.dart",
            "_identity",
            "int _identity(int value) {\n  return value == 2147483647 ? value : value + 1;\n}\n",
        )],
    );
    let emitted = fixture.run(&["emit", "dart"]);
    assert_eq!(emitted.status.code(), Some(0), "{}", stderr(&emitted));
    let pending_generation =
        fs::read(fixture.temp.0.join("generated/generation.json")).expect("generation record");
    let rejected = fixture.run(&["verify"]);
    assert!(!rejected.status.success());
    assert_eq!(
        fs::read(fixture.temp.0.join("generated/generation.json"))
            .expect("preserved generation record"),
        pending_generation,
        "failed contract execution must not rewrite or certify the pending generation",
    );
    let generation = fixture.generation();
    assert_eq!(generation["current"]["verified"], false);
    assert!(generation["current"]["verification"].is_null());
    assert!(generation["last_verified"].is_null());
    assert!(
        !fixture
            .temp
            .0
            .join("generated/dart/verification/cott-module.dill")
            .exists()
    );
}

#[test]
#[ignore = "requires COTT_DART, bubblewrap, and the provisioned Dart 3.13.3 SDK"]
fn native_runner_executes_pure_filesystem_and_cooperative_cancellation_scenarios() {
    let fixture = Fixture::new(
        "scenarios",
        r#"module demo.runner

const THREE: I32 = 3
const SEVEN: I32 = 7

fn identity(value: I32) -> I32:
    ensures result == value

fn read_text(source: Path) -> Str:
    ensures result.len >= 0
    effects [file.read]

async fn later(value: I32) -> I32:
    ensures result == value
    effects []

scenario pure_math:
    call total = identity(THREE)
    assert total == 3

scenario filesystem_read:
    fixtures:
        fs files:
            file "input.txt" text("fixture text")
    call text = read_text(files.path("input.txt"))
    assert text == "fixture text"

scenario cancelled_worker:
    spawn worker = later(SEVEN)
    cancel worker
    await worker cancelled
"#,
        &[
            (
                "demo.runner.identity",
                "identity.dart",
                "_identity",
                "int _identity(int value) {\n  return value;\n}\n",
            ),
            (
                "demo.runner.read_text",
                "read_text.dart",
                "_read_text",
                "import 'dart:io';\n\nString _read_text(cott_runtime.CottPath source) {\n  return File(source.value).readAsStringSync();\n}\n",
            ),
            (
                "demo.runner.later",
                "later.dart",
                "_later",
                "Future<int> _later(int value) async {\n  await Future<void>.delayed(Duration.zero);\n  return value;\n}\n",
            ),
        ],
    );
    let emitted = fixture.run(&["emit", "dart"]);
    assert_eq!(emitted.status.code(), Some(0), "{}", stderr(&emitted));
    let verified = fixture.run(&["verify"]);
    assert_eq!(verified.status.code(), Some(0), "{}", stderr(&verified));

    let generation = fixture.generation();
    let contract_tests = &generation["current"]["verification"]["contract_tests"];
    let scenarios = contract_tests["scenarios"]
        .as_array()
        .expect("scenario evidence");
    for id in [
        "demo.runner.scenario.pure_math",
        "demo.runner.scenario.filesystem_read",
        "demo.runner.scenario.cancelled_worker",
    ] {
        let scenario = scenarios
            .iter()
            .find(|scenario| scenario["scenario_id"] == id)
            .unwrap_or_else(|| panic!("missing scenario {id}"));
        assert_eq!(scenario["status"], "passed");
        assert_eq!(scenario["cleaned"], true);
    }
    let lifecycle = contract_tests["lifecycle"]
        .as_array()
        .expect("cancellation evidence");
    assert!(lifecycle.iter().any(|event| {
        event["symbol"] == "demo.runner.scenario.cancelled_worker"
            && event["status"] == "passed"
            && event["cooperative"] == true
            && event["future_preempted"] == false
    }));
    assert!(has_positive_clause(&generation, "demo.runner.identity"));
    assert!(has_positive_clause(&generation, "demo.runner.read_text"));
    assert!(has_positive_clause(&generation, "demo.runner.later"));
}

#[test]
#[ignore = "requires COTT_DART, bubblewrap and Landlock ABI >=3"]
fn native_dart_io_cannot_open_process_memory_from_vm_threads() {
    let fixture = Fixture::new(
        "process-memory",
        r#"module demo.runner

async fn probe(source: Path) -> Bool:
    ensures result
    effects [file.read]

scenario confined_files:
    fixtures:
        fs files:
            file "input.txt" text("allowed fixture")
    call safe = probe(files.path("input.txt"))
    assert safe
"#,
        &[(
            "demo.runner.probe",
            "probe.dart",
            "_probe",
            r#"import 'dart:io';
Future<bool> _probe(cott_runtime.CottPath source) async {
  for (final path in ['/proc/self/mem', '/proc/thread-self/mem', '/proc/self/environ', '/proc/self/cmdline']) {
    var syncDenied = false;
    try {
      final file = File(path).openSync();
      file.closeSync();
    } on FileSystemException catch (error) {
      syncDenied = error.osError?.errorCode == 13 || error.osError?.errorCode == 1;
    }
    if (!syncDenied) return false;
    var asyncDenied = false;
    try {
      final file = await File(path).open();
      await file.close();
    } on FileSystemException catch (error) {
      asyncDenied = error.osError?.errorCode == 13 || error.osError?.errorCode == 1;
    }
    if (!asyncDenied) return false;
  }
  return await File(source.value).readAsString() == 'allowed fixture';
}
"#,
        )],
    );
    let emitted = fixture.run(&["emit", "dart"]);
    assert_eq!(emitted.status.code(), Some(0), "{}", stderr(&emitted));
    let verified = fixture.run(&["verify"]);
    assert_eq!(verified.status.code(), Some(0), "{}", stderr(&verified));
    assert!(has_positive_clause(
        &fixture.generation(),
        "demo.runner.probe"
    ));
}
