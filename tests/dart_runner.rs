use std::fs;
use std::io;
use std::path::PathBuf;
use std::process::{Command, Output};
use std::sync::atomic::{AtomicU64, Ordering};

use serde_json::Value;

#[path = "support/snapshot.rs"]
mod snapshot;

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
        let fixture = Self {
            temp: TempDir::new(label),
        };
        fixture.write(source, bindings);
        fixture
    }

    /// Replace the manifest, Cott source and manifest-bound implementations in place, keeping
    /// the isolated Dart home and pub cache of earlier runs.
    fn write(&self, source: &str, bindings: &[(&str, &str, &str, &str)]) {
        let temp = &self.temp;
        fs::create_dir_all(temp.0.join("src/demo")).expect("Cott source directory");
        let _ = fs::remove_dir_all(temp.0.join("dart/bindings"));
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
        snapshot::read(
            &fs::read(self.temp.0.join("generated/generation.json")).expect("generation record"),
        )
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
fn native_runner_uses_typed_nothing_for_defaulted_option_fields() {
    let fixture = Fixture::new(
        "typed-nothing",
        r#"module demo.runner

struct Payload:
    bytes: Bytes

enum Envelope:
    Wrapped(payload: Payload)

enum PayloadFailure:
    Failed(payload: Payload)

enum Grade:
    Low
    High

struct Message:
    payload: Option[Payload] = Option.Nothing
    outcome: Result[Payload, PayloadFailure]
    envelope: Envelope
    grade: Grade = Grade.Low

    invariant self.payload matches Option.Some(payload) => payload.bytes.len >= 0
    invariant self.outcome matches Result.Ok(payload) => payload.bytes.len >= 0
    invariant self.outcome matches Result.Err(PayloadFailure.Failed(payload)) => payload.bytes.len >= 0
    invariant self.envelope matches Envelope.Wrapped(payload) => payload.bytes.len >= 0

fn payload_is_nothing(message: Message) -> Bool:
    effects []
"#,
        &[(
            "demo.runner.payload_is_nothing",
            "payload_is_nothing.dart",
            "_payload_is_nothing",
            "bool _payload_is_nothing(Message message) {\n  return message.payload is cott_runtime.Nothing<Object?>;\n}\n",
        )],
    );
    let emitted = fixture.run(&["emit", "dart"]);
    assert_eq!(emitted.status.code(), Some(0), "{}", stderr(&emitted));
    let verified = fixture.run(&["verify"]);
    assert_eq!(verified.status.code(), Some(0), "{}", stderr(&verified));

    let generation = fixture.generation();
    assert_eq!(generation["current"]["verified"], true);
    assert!(
        generation["current"]["verification"]["contract_tests"]["cases"]
            .as_array()
            .expect("typed Nothing runner cases")
            .iter()
            .any(|case| {
                case["symbol"] == "demo.runner.payload_is_nothing" && case["status"] == "passed"
            }),
        "missing passing case for typed Nothing candidate"
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

#[test]
#[ignore = "requires COTT_DART, bubblewrap, and the provisioned Dart 3.13.3 SDK"]
fn native_runner_guarded_success_requires_a_matched_condition() {
    let fixture = Fixture::new(
        "guarded-success",
        r#"module demo.runner

fn absent(value: Bool) -> Option[I32]:
    ensures result matches Option.Some(item) => item > 0

fn mixed(value: Bool) -> Option[I32]:
    ensures result matches Option.Some(item) => item > 0

async fn asynchronous(value: Bool) -> Option[I32]:
    ensures result matches Option.Some(item) => item > 0

fn beyond_boundary(value: I32) -> Option[I32]:
    requires value > 41
    ensures result matches Option.Some(item) => item > 41
"#,
        &[
            (
                "demo.runner.absent",
                "absent.dart",
                "_absent",
                "cott_runtime.CottOption<int> _absent(bool value) { return const cott_runtime.Nothing<int>(); }\n",
            ),
            (
                "demo.runner.mixed",
                "mixed.dart",
                "_mixed",
                "cott_runtime.CottOption<int> _mixed(bool value) { return value ? const cott_runtime.Some<int>(1) : const cott_runtime.Nothing<int>(); }\n",
            ),
            (
                "demo.runner.asynchronous",
                "asynchronous.dart",
                "_asynchronous",
                "Future<cott_runtime.CottOption<int>> _asynchronous(bool value) async { await Future<void>.delayed(Duration.zero); return value ? const cott_runtime.Some<int>(1) : const cott_runtime.Nothing<int>(); }\n",
            ),
            (
                "demo.runner.beyond_boundary",
                "beyond_boundary.dart",
                "_beyond_boundary",
                "cott_runtime.CottOption<int> _beyond_boundary(int value) { return cott_runtime.Some<int>(value); }\n",
            ),
        ],
    );
    let emitted = fixture.run(&["emit", "dart"]);
    assert_eq!(emitted.status.code(), Some(0), "{}", stderr(&emitted));
    let verified = fixture.run(&["verify"]);
    assert_eq!(verified.status.code(), Some(0), "{}", stderr(&verified));
    let generation = fixture.generation();
    assert!(!has_positive_clause(&generation, "demo.runner.absent"));
    assert!(has_positive_clause(&generation, "demo.runner.mixed"));
    assert!(has_positive_clause(&generation, "demo.runner.asynchronous"));
    let absent = generation["current"]["semantic_coverage"]["clauses"]
        .as_array()
        .expect("coverage inventory")
        .iter()
        .find(|clause| clause["symbol"] == "demo.runner.absent")
        .expect("guarded absent clause remains in inventory");
    assert_ne!(absent["status"], "observed");
    let success = generation["current"]["semantic_coverage"]["clauses"]
        .as_array()
        .expect("coverage inventory")
        .iter()
        .find(|clause| {
            clause["symbol"] == "demo.runner.beyond_boundary"
                && clause["clause_id"]
                    .as_str()
                    .is_some_and(|id| id.starts_with("ensures:"))
        })
        .expect("guarded boundary clause");
    assert_eq!(success["status"], "observed");
}

/// The import prefix of module `demo.runner` types inside a canonical implementation part.
const DEMO_TYPES: &str = "_cott_t_demo__runner.";

fn dart_body(template: &str) -> String {
    template.replace("{T}", DEMO_TYPES)
}

fn assert_verifies(fixture: &Fixture) -> Value {
    let emitted = fixture.run(&["emit", "dart"]);
    assert_eq!(emitted.status.code(), Some(0), "{}", stderr(&emitted));
    let verified = fixture.run(&["verify"]);
    assert_eq!(verified.status.code(), Some(0), "{}", stderr(&verified));
    let generation = fixture.generation();
    assert_eq!(generation["current"]["verified"], true);
    generation
}

/// Real native verification must fail with the exact compiler-owned failure explanation and
/// must leave the pending snapshot uncertified.
fn assert_verify_rejects(fixture: &Fixture, expected: &str) {
    let emitted = fixture.run(&["emit", "dart"]);
    assert_eq!(emitted.status.code(), Some(0), "{}", stderr(&emitted));
    let rejected = fixture.run(&["verify"]);
    let message = stderr(&rejected);
    assert_eq!(rejected.status.code(), Some(4), "{message}");
    assert!(
        message.contains(expected),
        "expected `{expected}` in:\n{message}"
    );
    assert_eq!(fixture.generation()["current"]["verified"], false);
}

fn assert_scenario_passed(generation: &Value, id: &str, assertions: u64) {
    let scenario = generation["current"]["verification"]["contract_tests"]["scenarios"]
        .as_array()
        .expect("scenario evidence")
        .iter()
        .find(|scenario| scenario["scenario_id"] == id)
        .unwrap_or_else(|| panic!("missing scenario {id}"));
    assert_eq!(scenario["status"], "passed", "{scenario}");
    assert_eq!(scenario["assertions"], assertions, "{scenario}");
    assert_eq!(scenario["cleaned"], true, "{scenario}");
}

const SCENARIO_VALUES: &str = r#"module demo.runner

enum Grade:
    Low
    High

enum Mode:
    Fast
    Careful(retries: U8)
    Graded(grade: Grade)

newtype Port(U16)
    where 1 <= self

struct Limits:
    timeout_ms: U32
    tags: List[Str]
    port: Port

    invariant self.timeout_ms > 0

struct Request:
    name: Str
    mode: Mode
    fallback: Mode
    grade: Grade
    limits: Limits
    labels: Map[Str, U32]
    note: Option[Str]

enum Failure:
    Rejected(reason: Str)

struct Report:
    name: Str
    retries: U8
    grade: Grade

fn run(request: Request) -> Result[Report, Failure]:
    ensures Result.Ok(report) => report.name == request.name

    error Failure.Rejected

fn echo(request: Request) -> Request:
    ensures result == request

data base_limits: Limits = Limits(timeout_ms: 30, tags: List("a", "b"), port: Port(8080))

scenario nested_request:
    data request: Request = Request(
        name: "job",
        mode: Mode.Careful(retries: 2),
        fallback: Mode.Graded(grade: Grade.Low),
        grade: Grade.High,
        limits: base_limits,
        labels: Map("x": 1, "y": 2),
        note: Option.Some(value: "n"),
    )
    call outcome = run(request)
    assert outcome matches Result.Ok(report) => report.retries == 2
    assert outcome == Result.Ok(value: Report(name: "job", retries: 2, grade: Grade.High))
    call copy = echo(request)
    assert copy == request
    assert copy.mode matches Mode.Careful(retries) => retries == 2
    assert copy.fallback == Mode.Graded(grade: Grade.Low)
    assert copy.fallback matches Mode.Graded(grade) => grade == Grade.Low
    assert copy.note matches Option.Some(note) => note == "n"
    assert copy.labels == Map("y": 2, "x": 1)
    assert copy.limits == Limits(tags: List("a", "b"), port: Port(8080), timeout_ms: 30)

scenario plain_request:
    data rejected: Result[Report, Failure] = Result.Err(error: Failure.Rejected(reason: "plain"))
    call outcome = run(Request(
        name: "plain",
        mode: Mode.Fast,
        fallback: Mode.Fast,
        grade: Grade.Low,
        limits: Limits(timeout_ms: 1, tags: List(), port: Port(1)),
        labels: Map(),
        note: Option.Nothing,
    ))
    assert outcome == Result.Ok(value: Report(name: "plain", retries: 0, grade: Grade.Low))
    assert rejected matches Result.Err(Failure.Rejected(reason)) => reason == "plain"
"#;

const INVALID_LIMITS_SCENARIO: &str = r#"
scenario invalid_limits:
    data limits: Limits = Limits(timeout_ms: 0, tags: List(), port: Port(1))
    call outcome = run(Request(name: "x", mode: Mode.Fast, fallback: Mode.Fast, grade: Grade.Low, limits: limits, labels: Map(), note: Option.Nothing))
    assert outcome matches Result.Ok(_)
"#;

fn scenario_value_bindings(
    result: &str,
) -> [(&'static str, &'static str, &'static str, String); 2] {
    [
        (
            "demo.runner.run",
            "run.dart",
            "_run",
            dart_body(&format!(
                "cott_runtime.CottResult<{{T}}Report, {{T}}Failure> _run({{T}}Request request) {{\n  return {result};\n}}\n"
            )),
        ),
        (
            "demo.runner.echo",
            "echo.dart",
            "_echo",
            dart_body("{T}Request _echo({T}Request request) {\n  return request;\n}\n"),
        ),
    ]
}

fn borrowed<'a>(
    bindings: &'a [(&'a str, &'a str, &'a str, String)],
) -> Vec<(&'a str, &'a str, &'a str, &'a str)> {
    bindings
        .iter()
        .map(|(symbol, file, name, body)| (*symbol, *file, *name, body.as_str()))
        .collect()
}

const CORRECT_REPORT: &str = "cott_runtime.Ok<{T}Report, {T}Failure>({T}Report(name: request.name, retries: switch (request.mode) { {T}ModeCareful(:final retries) => retries, _ => 0 }, grade: request.grade))";

#[test]
#[ignore = "requires COTT_DART, bubblewrap, and the provisioned Dart 3.13.3 SDK"]
fn native_scenario_values_construct_nested_canonical_values_and_check_guarded_payloads() {
    let correct = scenario_value_bindings(CORRECT_REPORT);
    let fixture = Fixture::new("scenario-values", SCENARIO_VALUES, &borrowed(&correct));
    let generation = assert_verifies(&fixture);
    assert_scenario_passed(&generation, "demo.runner.scenario.nested_request", 9);
    assert_scenario_passed(&generation, "demo.runner.scenario.plain_request", 2);

    // Each wrong implementation keeps the exact typed signature. A wrong `Ok` payload and a
    // non-matching `Err` both fail the guarded assertion instead of satisfying it vacuously.
    for (result, failed_step) in [
        (
            "cott_runtime.Ok<{T}Report, {T}Failure>({T}Report(name: request.name, retries: 0, grade: request.grade))",
            2,
        ),
        (
            "cott_runtime.Err<{T}Report, {T}Failure>({T}FailureRejected(field0: 'rejected'))",
            2,
        ),
        // A native enum member differs only in the projected Dart `enum` constant.
        (
            "cott_runtime.Ok<{T}Report, {T}Failure>({T}Report(name: request.name, retries: switch (request.mode) { {T}ModeCareful(:final retries) => retries, _ => 0 }, grade: {T}Grade.Low))",
            3,
        ),
    ] {
        fixture.write(SCENARIO_VALUES, &borrowed(&scenario_value_bindings(result)));
        assert_verify_rejects(
            &fixture,
            &format!(
                "Dart scenario `demo.runner.scenario.nested_request` failed: assertion step:{failed_step} failed"
            ),
        );
    }
}

#[test]
#[ignore = "requires COTT_DART, bubblewrap, and the provisioned Dart 3.13.3 SDK"]
fn native_scenario_values_run_canonical_struct_invariants() {
    let correct = scenario_value_bindings(CORRECT_REPORT);
    let fixture = Fixture::new(
        "scenario-invariants",
        &format!("{SCENARIO_VALUES}{INVALID_LIMITS_SCENARIO}"),
        &borrowed(&correct),
    );
    assert_verify_rejects(
        &fixture,
        "Dart scenario `demo.runner.scenario.invalid_limits` failed at step:0: contract violation for `demo.runner.Limits` (invariant invariant:0)",
    );
}

const TOPOLOGICAL_CONTRACT: &str = r#"module demo.runner

struct BuildStep:
    name: Str
    needs: Set[Str]

enum PipelineError:
    BlankStepName
    DuplicateStep
    UnknownDependency
    SelfDependency
    Cycle

fn order_steps(steps: List[BuildStep]) -> Result[List[Str], PipelineError]:
    ensures Result.Ok(order) => permutation_by(order, steps, BuildStep.name)
    ensures Result.Ok(order) => dependency_ordered_by(order, steps, BuildStep.name, BuildStep.needs)

    errors complete
    error PipelineError.BlankStepName when any_blank_by(steps, BuildStep.name)
    error PipelineError.DuplicateStep when not unique_by(steps, BuildStep.name)
    error PipelineError.UnknownDependency when unknown_dependency_by(steps, BuildStep.name, BuildStep.needs)
    error PipelineError.SelfDependency when self_dependency_by(steps, BuildStep.name, BuildStep.needs)
    error PipelineError.Cycle when cyclic_by(steps, BuildStep.name, BuildStep.needs)

scenario valid_orders:
    call empty = order_steps(List())
    assert empty == Result.Ok(value: List())
    call chain = order_steps(List(BuildStep(name: "b", needs: Set("a")), BuildStep(name: "a", needs: Set())))
    assert chain == Result.Ok(value: List("a", "b"))
    call diamond = order_steps(List(BuildStep(name: "c", needs: Set()), BuildStep(name: "a", needs: Set("c")), BuildStep(name: "b", needs: Set("c"))))
    assert diamond == Result.Ok(value: List("c", "a", "b"))
    call not_blank = order_steps(List(BuildStep(name: "\uFEFF", needs: Set()), BuildStep(name: "\u200B", needs: Set("\uFEFF"))))
    assert not_blank == Result.Ok(value: List("\uFEFF", "\u200B"))

scenario invalid_graphs:
    data blank_error: Result[List[Str], PipelineError] = Result.Err(error: PipelineError.BlankStepName)
    call empty_name = order_steps(List(BuildStep(name: "", needs: Set())))
    assert empty_name == blank_error
    call blank = order_steps(List(BuildStep(name: "a", needs: Set()), BuildStep(name: " \u3000\u0085", needs: Set("a"))))
    assert blank matches Result.Err(PipelineError.BlankStepName)
    call duplicate = order_steps(List(BuildStep(name: "a", needs: Set()), BuildStep(name: "a", needs: Set("zz"))))
    assert duplicate == Result.Err(error: PipelineError.DuplicateStep)
    call unknown = order_steps(List(BuildStep(name: "a", needs: Set("zz")), BuildStep(name: "b", needs: Set("b"))))
    assert unknown == Result.Err(error: PipelineError.UnknownDependency)
    call self_edge = order_steps(List(BuildStep(name: "a", needs: Set("a")), BuildStep(name: "b", needs: Set("c")), BuildStep(name: "c", needs: Set("b"))))
    assert self_edge == Result.Err(error: PipelineError.SelfDependency)
    call cycle = order_steps(List(BuildStep(name: "a", needs: Set("b")), BuildStep(name: "b", needs: Set("a"))))
    assert cycle == Result.Err(error: PipelineError.Cycle)
"#;

/// A typed deterministic Kahn implementation with the pinned Unicode `White_Space` table.
/// `check_first` and `finish` let deliberately wrong fixtures keep the exact signature.
fn topological_binding(
    check_first: &str,
    finish: &str,
) -> [(&'static str, &'static str, &'static str, String); 1] {
    let error = |variant: &str| {
        format!(
            "return cott_runtime.Err<cott_runtime.CottList<String>, {{T}}PipelineError>({{T}}PipelineError.{variant});"
        )
    };
    let body = format!(
        r#"cott_runtime.CottResult<cott_runtime.CottList<String>, {{T}}PipelineError> _order_steps(cott_runtime.CottList<{{T}}BuildStep> steps) {{
  const whiteSpace = <int>{{0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x20, 0x85, 0xA0, 0x1680, 0x2000, 0x2001, 0x2002, 0x2003, 0x2004, 0x2005, 0x2006, 0x2007, 0x2008, 0x2009, 0x200A, 0x2028, 0x2029, 0x202F, 0x205F, 0x3000}};
  final names = <String>[for (final step in steps) step.name];
  final known = names.toSet();
  final unknown = steps.any((step) => step.needs.any((need) => !known.contains(need)));
{check_first}  if (names.any((name) => name.codeUnits.every(whiteSpace.contains))) {blank}
  if (known.length != names.length) {duplicate}
  if (unknown) {unknown_error}
  if (steps.any((step) => step.needs.contains(step.name))) {self_error}
  final remaining = <String, Set<String>>{{for (final step in steps) step.name: Set<String>.of(step.needs)}};
  final order = <String>[];
  while (remaining.isNotEmpty) {{
    final ready = <String>[for (final entry in remaining.entries) if (entry.value.isEmpty) entry.key]..sort();
    if (ready.isEmpty) {cycle}
    order.add(ready.first);
    remaining.remove(ready.first);
    for (final needs in remaining.values) {{
      needs.remove(ready.first);
    }}
  }}
{finish}  return cott_runtime.Ok<cott_runtime.CottList<String>, {{T}}PipelineError>(cott_runtime.CottList<String>(order));
}}
"#,
        blank = error("BlankStepName"),
        duplicate = error("DuplicateStep"),
        unknown_error = error("UnknownDependency"),
        self_error = error("SelfDependency"),
        cycle = error("Cycle"),
    );
    [(
        "demo.runner.order_steps",
        "order_steps.dart",
        "_order_steps",
        dart_body(&body),
    )]
}

#[test]
#[ignore = "requires COTT_DART, bubblewrap, and the provisioned Dart 3.13.3 SDK"]
fn native_complete_errors_align_graph_predicates_with_fixed_semantics() {
    let binding = topological_binding("", "");
    let fixture = Fixture::new("topological", TOPOLOGICAL_CONTRACT, &borrowed(&binding));
    // Every scenario call passes the facade's complete error check, so the runtime predicates
    // agree with the fixed whitespace, duplicate, missing, self and empty semantics.
    let generation = assert_verifies(&fixture);
    assert_scenario_passed(&generation, "demo.runner.scenario.valid_orders", 4);
    assert_scenario_passed(&generation, "demo.runner.scenario.invalid_graphs", 6);
    for clause in ["ensures:0", "ensures:1"] {
        let coverage = generation["current"]["semantic_coverage"]["clauses"]
            .as_array()
            .expect("coverage inventory")
            .iter()
            .find(|entry| {
                entry["symbol"] == "demo.runner.order_steps" && entry["clause_id"] == clause
            })
            .unwrap_or_else(|| panic!("missing {clause}"));
        assert_eq!(coverage["status"], "observed", "{coverage}");
    }
}

#[test]
#[ignore = "requires COTT_DART, bubblewrap, and the provisioned Dart 3.13.3 SDK"]
fn native_complete_errors_reject_wrong_typed_implementations() {
    let binding = topological_binding("", "");
    let fixture = Fixture::new(
        "topological-wrong",
        TOPOLOGICAL_CONTRACT,
        &borrowed(&binding),
    );
    for (check_first, finish, expected) in [
        // Always an error, even for the valid empty input.
        (
            "  if (known.length >= 0) return cott_runtime.Err<cott_runtime.CottList<String>, {T}PipelineError>({T}PipelineError.Cycle);\n",
            "",
            "Dart contract execution failed for `demo.runner.order_steps` case 0 (failed: error error-return)",
        ),
        // Valid shape and multiset, but dependents before their dependencies.
        (
            "",
            "  order.setAll(0, order.reversed.toList());\n",
            "Dart scenario `demo.runner.scenario.valid_orders` failed at step:2: contract violation for `demo.runner.order_steps` (ensures ensures:1)",
        ),
        // Dependency errors checked before duplicate names.
        (
            "  if (unknown) return cott_runtime.Err<cott_runtime.CottList<String>, {T}PipelineError>({T}PipelineError.UnknownDependency);\n",
            "",
            "Dart scenario `demo.runner.scenario.invalid_graphs` failed at step:5: contract violation for `demo.runner.order_steps` (error error-return)",
        ),
    ] {
        fixture.write(
            TOPOLOGICAL_CONTRACT,
            &borrowed(&topological_binding(check_first, finish)),
        );
        assert_verify_rejects(&fixture, expected);
    }
}

#[test]
#[ignore = "requires COTT_DART, bubblewrap, and the provisioned Dart 3.13.3 SDK"]
fn native_complete_errors_is_opt_in_and_rejects_err_without_conditions() {
    let default = "module demo.runner\n\nenum Failure:\n    Bad\n\nfn echo(value: Str) -> Result[Str, Failure]:\n    ensures Result.Ok(output) => output == value\n";
    let always_error = [(
        "demo.runner.echo",
        "echo.dart",
        "_echo",
        dart_body(
            "cott_runtime.CottResult<String, {T}Failure> _echo(String value) {\n  return cott_runtime.Err<String, {T}Failure>({T}Failure.Bad);\n}\n",
        ),
    )];
    let fixture = Fixture::new("complete-errors", default, &borrowed(&always_error));
    // Without `errors complete` and without error clauses, `Err` stays unchecked.
    assert_verifies(&fixture);

    let complete = default.replace("value\n", "value\n\n    errors complete\n");
    fixture.write(&complete, &borrowed(&always_error));
    assert_verify_rejects(
        &fixture,
        "Dart contract execution failed for `demo.runner.echo` case 0 (failed: error error-return)",
    );
}

/// Negative integer literals and integer arithmetic in scenario call arguments, data and
/// constructor fields are exact ABI values (`int` for I32/I8, `BigInt` for I64), including the
/// minimum value whose negated operand is outside its own type.
#[test]
#[ignore = "requires COTT_DART, bubblewrap, and the provisioned Dart 3.13.3 SDK"]
fn native_scenario_negative_integers_use_exact_dart_abi_types() {
    let bindings = [
        (
            "demo.runner.widen",
            "widen.dart",
            "_widen",
            "BigInt _widen(int left, int right) {\n  return BigInt.from(left) + BigInt.from(right);\n}\n"
                .to_owned(),
        ),
        (
            "demo.runner.shares",
            "shares.dart",
            "_shares",
            dart_body("BigInt _shares({T}Holding holding) {\n  return holding.shares;\n}\n"),
        ),
    ];
    let fixture = Fixture::new(
        "negative-integers",
        r#"module demo.runner

struct Holding:
    shares: I64
    small: I8

fn widen(left: I32, right: I32) -> I64:
    requires left <= right + 0

fn shares(holding: Holding) -> I64:
    ensures result == holding.shares

data low_i32: I32 = -2147483648

scenario negative_arguments:
    call low = widen(-2147483648, -1)
    assert low == -2147483649
    call again = widen(low_i32, -(1 + 2))
    assert again == -2147483651
    data owned: Holding = Holding(shares: -5, small: -128)
    call count = shares(owned)
    assert count == -5
    assert owned.small == -128
    call nested = shares(Holding(shares: -7, small: -1))
    assert nested == -7
"#,
        &borrowed(&bindings),
    );
    let generation = assert_verifies(&fixture);
    assert_scenario_passed(&generation, "demo.runner.scenario.negative_arguments", 5);
}

const IMPL_DYN_SCENARIO: &str = r#"module demo.runner
trait TaskView:
    fn summary(self) -> Str
impl SimpleTask for TaskView:
    state:
        title: Str
        urgency: I32
    init(title: Str, urgency: I32):
        ensures self.title == title
        ensures self.urgency == urgency
    fn summary(self) -> Str:
        ensures result == self.title
        effects []
fn inspect(view: Dyn[TaskView]) -> Str:
    effects []
scenario view:
    call task = SimpleTask(title: "Launch", urgency: 1)
    call summary = task.summary()
    assert summary == "Launch"
    data wrapped: Dyn[TaskView] = Dyn(value: task)
    call observed = inspect(wrapped)
    assert observed == "Launch"
    call nested = inspect(Dyn(value: task))
    assert nested == "Launch"
"#;

fn impl_dyn_bindings(inspect: &str) -> [(&'static str, &'static str, &'static str, String); 2] {
    [
        (
            "demo.runner.SimpleTask.summary",
            "summary.dart",
            "_summary",
            dart_body("String _summary({T}SimpleTask self) {\n  return self.title;\n}\n"),
        ),
        (
            "demo.runner.inspect",
            "inspect.dart",
            "_inspect",
            dart_body(&format!(
                "String _inspect(cott_runtime.Dyn<{{T}}TaskView> view) {{\n  return {inspect};\n}}\n"
            )),
        ),
    ]
}

#[test]
#[ignore = "requires COTT_DART, bubblewrap, and the provisioned Dart 3.13.3 SDK"]
fn native_impl_scenario_executes_initializer_receiver_method_and_nested_dyn_argument() {
    let correct = impl_dyn_bindings("view.value.summary()");
    let fixture = Fixture::new("scenario-impl-dyn", IMPL_DYN_SCENARIO, &borrowed(&correct));
    let generation = assert_verifies(&fixture);
    assert_scenario_passed(&generation, "demo.runner.scenario.view", 3);

    let wrong = impl_dyn_bindings("'wrong'");
    fixture.write(IMPL_DYN_SCENARIO, &borrowed(&wrong));
    assert_verify_rejects(
        &fixture,
        "Dart scenario `demo.runner.scenario.view` failed: assertion step:5 failed",
    );
}
