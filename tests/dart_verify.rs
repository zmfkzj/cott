use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::sync::atomic::{AtomicU64, Ordering};

use serde_json::Value;

static NEXT_TEMP: AtomicU64 = AtomicU64::new(0);

struct TempDir {
    path: PathBuf,
}

impl TempDir {
    fn new(label: &str) -> Self {
        let mut number = NEXT_TEMP.fetch_add(1, Ordering::Relaxed);
        loop {
            let path = std::env::temp_dir().join(format!(
                "cott-dart-verify-{label}-{}-{number}",
                std::process::id()
            ));
            match fs::create_dir(&path) {
                Ok(()) => return Self { path },
                Err(error) if error.kind() == io::ErrorKind::AlreadyExists => number += 1,
                Err(error) => panic!("create Dart verifier fixture: {error}"),
            }
        }
    }
}

impl Drop for TempDir {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.path);
    }
}

struct Fixture {
    temp: TempDir,
}

impl Fixture {
    fn standard(label: &str, sdk: &Path, cott_source: &str, binding: Option<&str>) -> Self {
        let temp = TempDir::new(label);
        fs::create_dir_all(temp.path.join("src/demo")).expect("Cott source directory");
        fs::create_dir_all(temp.path.join("dart/bindings")).expect("Dart binding directory");
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
"#,
            sdk.to_string_lossy()
        );
        if binding.is_some() {
            manifest.push_str(
                "\n[target.dart.implementations]\n\"demo.main.increment\" = \"bindings/increment.dart:_increment\"\n",
            );
        }
        fs::write(temp.path.join("cott.toml"), manifest).expect("Dart manifest");
        fs::write(temp.path.join("src/demo/main.cott"), cott_source).expect("Cott source");
        if let Some(binding) = binding {
            fs::write(temp.path.join("dart/bindings/increment.dart"), binding)
                .expect("Dart binding");
        }
        Self { temp }
    }

    fn metadata(label: &str, pubspec: &str, lockfile: &str) -> Self {
        let temp = TempDir::new(label);
        fs::create_dir_all(temp.path.join("src/demo")).expect("Cott source directory");
        fs::create_dir(temp.path.join("dart")).expect("Dart source directory");
        fs::create_dir_all(temp.path.join("dart_package")).expect("Dart metadata directory");
        fs::write(
            temp.path.join("cott.toml"),
            r#"[project]
name = "demo"
version = "0.1.0"
source = "src"

[target.dart]
source = "dart"
generated = "generated/dart"
sdk = "missing-dart"
runtime_validation = "boundary"
pubspec = "dart_package/pubspec.yaml"
lockfile = "dart_package/pubspec.lock"
"#,
        )
        .expect("Dart manifest");
        fs::write(temp.path.join("src/demo/main.cott"), "module demo.main\n").expect("Cott source");
        fs::write(temp.path.join("dart_package/pubspec.yaml"), pubspec).expect("Dart pubspec");
        fs::write(temp.path.join("dart_package/pubspec.lock"), lockfile).expect("Dart lockfile");
        Self { temp }
    }

    fn run(&self, arguments: &[&str]) -> Output {
        Command::new(env!("CARGO_BIN_EXE_cott"))
            .args(arguments)
            .args(["--project"])
            .arg(&self.temp.path)
            .output()
            .expect("cott should run")
    }

    fn run_native(&self, arguments: &[&str]) -> Output {
        let home = self.temp.path.join("home");
        let pub_cache = self.temp.path.join("pub-cache");
        fs::create_dir_all(&home).expect("isolated Dart home");
        fs::create_dir_all(&pub_cache).expect("isolated Dart pub cache");
        Command::new(env!("CARGO_BIN_EXE_cott"))
            .args(arguments)
            .args(["--project"])
            .arg(&self.temp.path)
            .env_clear()
            .env("HOME", home)
            .env("PUB_CACHE", pub_cache)
            .output()
            .expect("cott should run with isolated Dart environment")
    }

    fn root(&self) -> &Path {
        &self.temp.path
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

fn assert_pending_generation_preserved(fixture: &Fixture, expected: &[u8]) {
    let generation_path = fixture.root().join("generated/generation.json");
    let actual = fs::read(&generation_path).expect("preserved generation record");
    assert_eq!(
        actual, expected,
        "rejected verification must preserve the pending generation"
    );
    let generation: Value = serde_json::from_slice(&actual).expect("preserved generation JSON");
    assert_eq!(generation["current"]["verified"], false);
    assert!(generation["current"]["verification"].is_null());
    assert!(generation["last_verified"].is_null());
    assert!(
        !fixture
            .root()
            .join("generated/dart/verification/cott-module.dill")
            .exists(),
        "rejected verification must not publish a kernel artifact"
    );
}

fn assert_native_verifies(label: &str, source: &str, binding: &str) {
    let fixture = Fixture::standard(label, &native_dart(), source, Some(binding));
    let emitted = fixture.run_native(&["emit", "dart"]);
    assert_eq!(emitted.status.code(), Some(0), "{}", stderr(&emitted));
    let verified = fixture.run_native(&["verify"]);
    assert_eq!(
        verified.status.code(),
        Some(0),
        "the matching control must establish a working SDK and runner: {}",
        stderr(&verified)
    );
    let generation: Value = serde_json::from_slice(
        &fs::read(fixture.root().join("generated/generation.json")).expect("generation record"),
    )
    .expect("generation JSON");
    assert_eq!(generation["current"]["verified"], true);
    assert_eq!(generation["last_verified"], generation["current"]);
}

fn valid_empty_lock() -> &'static str {
    "packages: {}\nsdks:\n  dart: '>=3.13.3 <4.0.0'\n"
}

#[test]
fn malformed_pub_metadata_fails_before_tool_discovery() {
    let malformed_pubspec = Fixture::metadata(
        "bad-pubspec",
        "name: other\nversion: 0.1.0\nenvironment:\n  sdk: '>=3.13.3 <4.0.0'\n",
        valid_empty_lock(),
    );
    let rejected = malformed_pubspec.run(&["emit", "dart"]);
    assert_eq!(rejected.status.code(), Some(4));
    assert!(
        !malformed_pubspec
            .root()
            .join("generated/generation.json")
            .exists()
    );
    fs::write(
        malformed_pubspec.root().join("dart_package/pubspec.yaml"),
        "name: demo\nversion: 0.1.0\nenvironment:\n  sdk: '>=3.13.3 <4.0.0'\n",
    )
    .expect("repair Dart pubspec");
    let repaired = malformed_pubspec.run(&["emit", "dart"]);
    assert_eq!(repaired.status.code(), Some(0), "{}", stderr(&repaired));

    let malformed_lock = Fixture::metadata(
        "bad-lock",
        "name: demo\nversion: 0.1.0\nenvironment:\n  sdk: '>=3.13.3 <4.0.0'\ndependencies:\n  crypto: ^3.0.7\n",
        "packages:\n  crypto:\n    dependency: direct main\n    description:\n      name: crypto\n      url: https://pub.dev\n    source: hosted\n    version: 3.0.7\nsdks:\n  dart: '>=3.13.3 <4.0.0'\n",
    );
    let rejected = malformed_lock.run(&["emit", "dart"]);
    assert_eq!(rejected.status.code(), Some(4));
    assert!(
        !malformed_lock
            .root()
            .join("generated/generation.json")
            .exists()
    );
    fs::write(
        malformed_lock.root().join("dart_package/pubspec.yaml"),
        "name: demo\nversion: 0.1.0\nenvironment:\n  sdk: '>=3.13.3 <4.0.0'\n",
    )
    .expect("repair Dart pubspec dependencies");
    fs::write(
        malformed_lock.root().join("dart_package/pubspec.lock"),
        valid_empty_lock(),
    )
    .expect("repair Dart lockfile");
    let repaired = malformed_lock.run(&["emit", "dart"]);
    assert_eq!(repaired.status.code(), Some(0), "{}", stderr(&repaired));
}

#[test]
fn project_external_path_dependency_is_rejected() {
    let fixture = Fixture::metadata(
        "path-escape",
        "name: demo\nversion: 0.1.0\nenvironment:\n  sdk: '>=3.13.3 <4.0.0'\ndependencies:\n  escape:\n    path: ../../..\n",
        "packages:\n  escape:\n    dependency: direct main\n    description:\n      path: ../../..\n      relative: true\n    source: path\n    version: 1.0.0\nsdks:\n  dart: '>=3.13.3 <4.0.0'\n",
    );
    let rejected = fixture.run(&["emit", "dart"]);
    assert_eq!(rejected.status.code(), Some(4));
    assert!(!fixture.root().join("generated/generation.json").exists());
    fs::write(
        fixture.root().join("dart_package/pubspec.yaml"),
        "name: demo\nversion: 0.1.0\nenvironment:\n  sdk: '>=3.13.3 <4.0.0'\n",
    )
    .expect("repair external path dependency");
    fs::write(
        fixture.root().join("dart_package/pubspec.lock"),
        valid_empty_lock(),
    )
    .expect("repair external path lockfile");
    let repaired = fixture.run(&["emit", "dart"]);
    assert_eq!(repaired.status.code(), Some(0), "{}", stderr(&repaired));
}

#[test]
fn malformed_dependency_record_is_rejected_without_publication() {
    let fixture = Fixture::standard(
        "bad-record",
        Path::new("missing-dart"),
        "module demo.main\n",
        None,
    );
    let emitted = fixture.run(&["emit", "dart"]);
    assert_eq!(emitted.status.code(), Some(0), "{}", stderr(&emitted));
    let generation_path = fixture.root().join("generated/generation.json");
    let mut generation: Value =
        serde_json::from_slice(&fs::read(&generation_path).expect("generation record"))
            .expect("generation JSON");
    generation["current"]["dependencies"]["packages"] = serde_json::json!([{
        "name": "forged",
        "version": "1.0.0",
        "source": "path",
        "source_identity": "../escape",
        "content_hash": "sha256:0000000000000000000000000000000000000000000000000000000000000000",
        "dependencies": [],
        "runtime": true
    }]);
    let malformed_bytes = serde_json::to_vec(&generation).expect("serialize malformed record");
    fs::write(&generation_path, &malformed_bytes).expect("write malformed record");
    let rejected = fixture.run(&["verify"]);
    assert_eq!(rejected.status.code(), Some(4));
    assert_eq!(
        fs::read(&generation_path).expect("preserved malformed record"),
        malformed_bytes,
        "rejected metadata must not be rewritten or certified",
    );
}

#[test]
fn invalid_compiler_distribution_fails_closed_without_runtime_evidence() {
    let fixture = Fixture::standard(
        "invalid-compiler",
        Path::new("/bin/false"),
        "module demo.main\n",
        None,
    );
    let emitted = fixture.run(&["emit", "dart"]);
    assert_eq!(emitted.status.code(), Some(0), "{}", stderr(&emitted));
    let pending =
        fs::read(fixture.root().join("generated/generation.json")).expect("pending generation");
    let rejected = fixture.run(&["verify"]);
    assert_eq!(rejected.status.code(), Some(4));
    assert_pending_generation_preserved(&fixture, &pending);
}

#[test]
#[ignore = "requires COTT_DART, bubblewrap, and the provisioned Dart 3.13.3 SDK"]
fn native_verifier_records_positive_applicable_facade_evidence() {
    let fixture = Fixture::standard(
        "native-positive",
        &native_dart(),
        "module demo.main\n\nfn increment(current: I32) -> I32:\n    requires current >= 0\n    requires current < 100\n    ensures result == current + 1\n",
        Some("int _increment(int current) {\n  return current + 1;\n}\n"),
    );
    let emitted = fixture.run_native(&["emit", "dart"]);
    assert_eq!(emitted.status.code(), Some(0), "{}", stderr(&emitted));
    let verified = fixture.run_native(&["verify"]);
    assert_eq!(verified.status.code(), Some(0), "{}", stderr(&verified));
    assert!(
        fixture
            .root()
            .join("generated/dart/verification/cott-module.dill")
            .is_file()
    );
    let generation: Value = serde_json::from_slice(
        &fs::read(fixture.root().join("generated/generation.json")).expect("generation record"),
    )
    .expect("generation JSON");
    assert_eq!(generation["current"]["verified"], true);
    assert_eq!(generation["last_verified"], generation["current"]);
    let diff = fixture.run_native(&["diff", "--format", "json", "--exit-code"]);
    assert_eq!(diff.status.code(), Some(0), "{}", stderr(&diff));
    let diff: Value = serde_json::from_slice(&diff.stdout).expect("verified snapshot diff");
    assert_eq!(diff["changes"], serde_json::json!([]));
    let clauses = generation["current"]["semantic_coverage"]["clauses"]
        .as_array()
        .expect("semantic clauses")
        .iter()
        .filter(|clause| clause["symbol"] == "demo.main.increment")
        .collect::<Vec<_>>();
    assert_eq!(clauses.len(), 3, "increment contract inventory");
    assert!(
        clauses.iter().all(|clause| {
            clause["evidence"].as_array().is_some_and(|evidence| {
                evidence.iter().any(|entry| {
                    entry["status"] == "passed" && entry["positive_applicable"] == true
                })
            })
        }),
        "every increment clause must have positive applicable runtime evidence"
    );
    assert!(
        generation["current"]["verification"]["contract_tests"]["cases"]
            .as_array()
            .expect("contract runner cases")
            .iter()
            .any(|case| { case["symbol"] == "demo.main.increment" && case["status"] == "passed" }),
        "increment must execute a passing public-facade case"
    );
}

#[test]
#[ignore = "requires COTT_DART, bubblewrap, and the provisioned Dart 3.13.3 SDK"]
fn native_type_only_package_is_analyzed_and_kernel_compiled() {
    let fixture = Fixture::standard(
        "native-types",
        &native_dart(),
        "module demo.main\n\nalias Count = I32\n\nstruct Pair:\n    left: Count\n    right: Count\n",
        None,
    );
    let emitted = fixture.run_native(&["emit", "dart"]);
    assert_eq!(emitted.status.code(), Some(0), "{}", stderr(&emitted));
    let verified = fixture.run_native(&["verify"]);
    assert_eq!(verified.status.code(), Some(0), "{}", stderr(&verified));
    let generation: Value = serde_json::from_slice(
        &fs::read(fixture.root().join("generated/generation.json")).expect("generation record"),
    )
    .expect("generation JSON");
    assert!(
        fixture
            .root()
            .join("generated/dart/verification/cott-module.dill")
            .is_file()
    );
    assert_eq!(generation["current"]["verified"], true);
    assert_eq!(
        generation["current"]["verification"]["contract_tests"]["observation_inventory"]["status"],
        "not_applicable"
    );
    assert!(
        generation["current"]["verification"]["contract_tests"]["cases"]
            .as_array()
            .expect("type-only runner cases")
            .is_empty(),
        "a package with no callable must retain a genuine zero-case inventory"
    );
}

#[test]
#[ignore = "requires COTT_DART, bubblewrap, and the provisioned Dart 3.13.3 SDK"]
fn native_candidate_stdout_cannot_forge_authenticated_evidence() {
    let source = "module demo.main\n\nfn increment(current: I32) -> I32:\n    requires current < 2147483647\n    ensures result == current + 1\n";
    assert_native_verifies(
        "native-forged-control",
        source,
        "int _increment(int current) {\n  return current + 1;\n}\n",
    );

    let forged = format!(
        "int _increment(int current) {{\n  print('COTT_DART_VERIFY:0:{}:{{\"kind\":\"done\"}}');\n  return current + 1;\n}}\n",
        "0".repeat(64)
    );
    let fixture = Fixture::standard("native-forged", &native_dart(), source, Some(&forged));
    let emitted = fixture.run_native(&["emit", "dart"]);
    assert_eq!(emitted.status.code(), Some(0), "{}", stderr(&emitted));
    let pending =
        fs::read(fixture.root().join("generated/generation.json")).expect("pending generation");
    let rejected = fixture.run_native(&["verify"]);
    assert!(!rejected.status.success());
    assert_pending_generation_preserved(&fixture, &pending);
    assert!(
        stderr(&rejected).contains("unauthenticated evidence"),
        "forged stdout must reach and fail HMAC authentication: {}",
        stderr(&rejected)
    );
}

#[test]
#[ignore = "requires COTT_DART, bubblewrap, and the provisioned Dart 3.13.3 SDK"]
fn native_analyzer_failure_is_not_treated_as_unobserved_success() {
    let source = "module demo.main\n\nfn increment(current: I32) -> I32:\n    requires current < 2147483647\n    ensures result == current + 1\n";
    assert_native_verifies(
        "native-analyzer-control",
        source,
        "int _increment(int current) {\n  return current + 1;\n}\n",
    );
    let fixture = Fixture::standard(
        "native-compiler-failure",
        &native_dart(),
        source,
        Some("int _increment(int current) {\n  return 'not an int';\n}\n"),
    );
    let emitted = fixture.run_native(&["emit", "dart"]);
    assert_eq!(emitted.status.code(), Some(0), "{}", stderr(&emitted));
    let pending =
        fs::read(fixture.root().join("generated/generation.json")).expect("pending generation");
    let rejected = fixture.run_native(&["verify"]);
    assert!(!rejected.status.success());
    assert_pending_generation_preserved(&fixture, &pending);
}

#[test]
#[ignore = "requires COTT_DART and exercises frozen path dependency drift through native verify"]
fn locked_path_dependency_drift_is_rejected_before_certification() {
    let dart = native_dart();
    let fixture = Fixture::metadata(
        "dependency-drift",
        "name: demo\nversion: 0.1.0\nenvironment:\n  sdk: '>=3.13.3 <4.0.0'\ndependencies:\n  helper:\n    path: ../packages/helper\n",
        "packages:\n  helper:\n    dependency: direct main\n    description:\n      path: ../packages/helper\n      relative: true\n    source: path\n    version: 1.0.0\nsdks:\n  dart: '>=3.13.3 <4.0.0'\n",
    );
    let manifest_path = fixture.root().join("cott.toml");
    let manifest = fs::read_to_string(&manifest_path)
        .expect("manifest")
        .replace(
            "sdk = \"missing-dart\"",
            &format!("sdk = {:?}", dart.to_string_lossy()),
        );
    fs::write(&manifest_path, manifest).expect("native SDK manifest");
    fs::create_dir_all(fixture.root().join("packages/helper/lib")).expect("path package directory");
    fs::write(
        fixture.root().join("packages/helper/pubspec.yaml"),
        "name: helper\nversion: 1.0.0\nenvironment:\n  sdk: '>=3.13.3 <4.0.0'\n",
    )
    .expect("path package pubspec");
    let library = fixture.root().join("packages/helper/lib/helper.dart");
    fs::write(&library, "int helper() => 1;\n").expect("path package source");
    let emitted = fixture.run_native(&["emit", "dart"]);
    assert_eq!(emitted.status.code(), Some(0), "{}", stderr(&emitted));
    let pending =
        fs::read(fixture.root().join("generated/generation.json")).expect("pending generation");
    fs::write(&library, "int helper() => 2;\n").expect("drift path package source");
    let rejected = fixture.run_native(&["verify"]);
    assert!(!rejected.status.success());
    assert_pending_generation_preserved(&fixture, &pending);

    fs::write(&library, "int helper() => 1;\n").expect("restore path package source");
    let verified = fixture.run_native(&["verify"]);
    assert_eq!(
        verified.status.code(),
        Some(0),
        "restoring the locked dependency must prove the SDK path is healthy: {}",
        stderr(&verified)
    );
    let generation: Value = serde_json::from_slice(
        &fs::read(fixture.root().join("generated/generation.json")).expect("generation record"),
    )
    .expect("generation JSON");
    assert_eq!(generation["current"]["verified"], true);
    assert_eq!(generation["last_verified"], generation["current"]);
    assert!(
        fixture
            .root()
            .join("generated/dart/verification/cott-module.dill")
            .is_file()
    );
}
