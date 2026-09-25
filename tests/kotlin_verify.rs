use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::sync::atomic::{AtomicU64, Ordering};

use serde_json::Value;

#[path = "support/snapshot.rs"]
mod snapshot;

static NEXT_FIXTURE: AtomicU64 = AtomicU64::new(0);

struct Fixture {
    root: PathBuf,
}

fn fixture_root() -> PathBuf {
    let mut nonce = NEXT_FIXTURE.fetch_add(1, Ordering::Relaxed);
    loop {
        let candidate = std::env::temp_dir().join(format!(
            "cott-kotlin-verify-test-{}-{nonce}",
            std::process::id()
        ));
        match fs::create_dir(&candidate) {
            Ok(()) => return candidate,
            Err(error) if error.kind() == io::ErrorKind::AlreadyExists => {
                nonce = nonce.saturating_add(1);
            }
            Err(error) => panic!("create Kotlin verification fixture: {error}"),
        }
    }
}

impl Fixture {
    fn new(compiler: &Path, java: &Path) -> Self {
        let root = fixture_root();
        fs::create_dir_all(root.join("src/example")).expect("create contract source directory");
        fs::create_dir_all(root.join("kotlin/cott_bindings/counter"))
            .expect("create Kotlin binding directory");
        fs::write(
            root.join("cott.toml"),
            format!(
                r#"[project]
name = "verify-counter"
version = "0.1.0"
source = "src"

[target.kotlin]
source = "kotlin"
generated = "generated/kotlin"
compiler = {}
java = {}
jvm_target = 17
runtime_validation = "boundary"

[target.kotlin.implementations]
"example.counter.increment" = "cott_bindings.counter.increment"
"#,
                toml_string(compiler),
                toml_string(java),
            ),
        )
        .expect("write Kotlin fixture manifest");
        fs::write(
            root.join("src/example/counter.cott"),
            r#"module example.counter

fn increment(current: I32) -> I32:
    requires current >= 0
    requires current < 100
    ensures result == current + 1
"#,
        )
        .expect("write Kotlin contract");
        fs::write(
            root.join("kotlin/cott_bindings/counter/increment.kt"),
            r#"package cott_bindings.counter

internal fun increment(current: kotlin.Int): kotlin.Int {
    print("candidate-log-without-newline")
    return current + 1
}
"#,
        )
        .expect("write Kotlin implementation");
        Self { root }
    }

    fn type_only(compiler: &Path, java: &Path) -> Self {
        let root = fixture_root();
        fs::create_dir_all(root.join("src/example")).expect("create contract source directory");
        fs::create_dir(root.join("kotlin")).expect("create Kotlin source directory");
        fs::write(
            root.join("cott.toml"),
            format!(
                r#"[project]
name = "verify-types"
version = "0.1.0"
source = "src"

[target.kotlin]
source = "kotlin"
generated = "generated/kotlin"
compiler = {}
java = {}
jvm_target = 17
runtime_validation = "boundary"
classpath = ["libs/versioned.jar"]
"#,
                toml_string(compiler),
                toml_string(java),
            ),
        )
        .expect("write type-only Kotlin fixture manifest");
        fs::write(
            root.join("src/example/types.cott"),
            r#"module example.types

alias Count = I32
const DEFAULT_COUNT: Count = 7

struct Pair:
    left: Count
    right: Count
"#,
        )
        .expect("write type-only Kotlin contract");
        Self { root }
    }

    fn forged_evidence(compiler: &Path, java: &Path) -> Self {
        let root = fixture_root();
        fs::create_dir_all(root.join("src/example")).expect("create contract source directory");
        fs::create_dir_all(root.join("kotlin/cott_bindings/escape"))
            .expect("create Kotlin binding directory");
        fs::write(
            root.join("cott.toml"),
            format!(
                r#"[project]
name = "forged-evidence"
version = "0.1.0"
source = "src"

[target.kotlin]
source = "kotlin"
generated = "generated/kotlin"
compiler = {}
java = {}
jvm_target = 17
runtime_validation = "boundary"
classpath = ["libs/host-exit.jar"]

[target.kotlin.implementations]
"example.escape.answer" = "cott_bindings.escape.answer"
"#,
                toml_string(compiler),
                toml_string(java),
            ),
        )
        .expect("write forged-evidence manifest");
        fs::write(
            root.join("src/example/escape.cott"),
            r#"module example.escape

fn answer() -> I32:
    ensures result == 7
"#,
        )
        .expect("write forged-evidence contract");
        fs::write(
            root.join("kotlin/cott_bindings/escape/answer.kt"),
            r#"package cott_bindings.escape

internal fun answer(): kotlin.Int {
    return fixture.escape.HostExit.answer()
}
"#,
        )
        .expect("write forged-evidence Kotlin binding");
        Self { root }
    }

    fn process_exit(compiler: &Path, java: &Path) -> Self {
        let root = fixture_root();
        fs::create_dir_all(root.join("src/example")).expect("create contract source directory");
        fs::create_dir_all(root.join("kotlin/cott_bindings/process_exit"))
            .expect("create Kotlin process-exit binding directory");
        fs::write(
            root.join("cott.toml"),
            format!(
                r#"[project]
name = "verify-process-exit"
version = "0.1.0"
source = "src"

[target.kotlin]
source = "kotlin"
generated = "generated/kotlin"
compiler = {}
java = {}
jvm_target = 17
runtime_validation = "boundary"

[target.kotlin.implementations]
"example.process_exit.exit_with_code" = "cott_bindings.process_exit.exit_with_code"
"#,
                toml_string(compiler),
                toml_string(java),
            ),
        )
        .expect("write process-exit manifest");
        fs::write(
            root.join("src/example/process_exit.cott"),
            r#"module example.process_exit

fn exit_with_code(code: U8) -> Never:
    effects [process.exit]
"#,
        )
        .expect("write process-exit contract");
        fs::write(
            root.join("kotlin/cott_bindings/process_exit/exit_with_code.kt"),
            r#"package cott_bindings.process_exit

internal fun exit_with_code(code: kotlin.UByte): kotlin.Nothing =
    cott_runtime.CottRuntime.exitWithCode(code)
"#,
        )
        .expect("write process-exit Kotlin binding");
        Self { root }
    }

    fn clock_scenario(compiler: &Path, java: &Path) -> Self {
        let root = fixture_root();
        fs::create_dir_all(root.join("src/example")).expect("create contract source directory");
        fs::create_dir_all(root.join("kotlin/cott_bindings/clock"))
            .expect("create Kotlin clock binding directory");
        fs::write(
            root.join("cott.toml"),
            format!(
                r#"[project]
name = "verify-clock"
version = "0.1.0"
source = "src"

[target.kotlin]
source = "kotlin"
generated = "generated/kotlin"
compiler = {}
java = {}
jvm_target = 17
runtime_validation = "boundary"

[target.kotlin.implementations]
"example.clock.clock_ns" = "cott_bindings.clock.clock_ns"
"example.clock.other_clock_ns" = "cott_bindings.clock.other_clock_ns"
"#,
                toml_string(compiler),
                toml_string(java),
            ),
        )
        .expect("write Kotlin clock fixture manifest");
        fs::write(
            root.join("src/example/clock.cott"),
            r#"module example.clock

fn clock_ns() -> U64:
    ensures result == 17000000
    effects [clock]

fn other_clock_ns() -> U64:
    ensures result == 29000000
    effects [clock]

scenario deterministic_clock:
    fixtures:
        clock clock:
            start_ms: 17
            tick_ms: 1
        clock other:
            start_ms: 29
            tick_ms: 7
    call first = clock_ns()
    tick
    call second = clock_ns()
    call other_value = other_clock_ns()
    assert first == 17000000
    assert second == 17000000
    assert other_value == 29000000
"#,
        )
        .expect("write Kotlin clock contract");
        fs::write(
            root.join("kotlin/cott_bindings/clock/clock.kt"),
            r#"package cott_bindings.clock

internal fun clock_ns(): kotlin.ULong =
    cott_runtime.CottRuntime.fixtureClockNs("clock")
"#,
        )
        .expect("write primary Kotlin clock implementation");
        fs::write(
            root.join("kotlin/cott_bindings/clock/other_clock.kt"),
            r#"package cott_bindings.clock

internal fun other_clock_ns(): kotlin.ULong =
    cott_runtime.CottRuntime.fixtureClockNs("other")
"#,
        )
        .expect("write Kotlin clock implementation");
        Self { root }
    }

    fn generic_trait(compiler: &Path, java: &Path) -> Self {
        let root = fixture_root();
        fs::create_dir_all(root.join("src/example")).expect("create contract source directory");
        fs::create_dir_all(root.join("kotlin/cott_bindings/traits"))
            .expect("create Kotlin trait binding directory");
        fs::write(
            root.join("cott.toml"),
            format!(
                r#"[project]
name = "verify-generic-trait"
version = "0.1.0"
source = "src"

[target.kotlin]
source = "kotlin"
generated = "generated/kotlin"
compiler = {}
java = {}
jvm_target = 17
runtime_validation = "boundary"

[target.kotlin.implementations]
"example.traits.echo" = "cott_bindings.traits.echo"
"example.traits.integer_only" = "cott_bindings.traits.integer_only"
"example.traits.SimpleTask.summary" = "cott_bindings.traits.summary"
"example.traits.SimpleTask.display" = "cott_bindings.traits.display"
"#,
                toml_string(compiler),
                toml_string(java),
            ),
        )
        .expect("write generic trait manifest");
        fs::write(
            root.join("src/example/traits.cott"),
            r#"module example.traits

trait Summarizable:
    type Summary
    fn summary(self) -> Summarizable.Summary

trait TaskView[T] for Summarizable:
    fn display(self) -> T

fn echo[T](value: T, receiver: TaskView[T]) -> T:
    effects []

fn integer_only(receiver: TaskView[I32]) -> I32:
    ensures result == 7
    effects []

impl SimpleTask for TaskView[Str]:
    type Summary = Str
    state:
        title: Str

    init(title: Str):
        ensures self.title == title

    fn summary(self) -> Str:
        ensures result == self.title
        effects []

    fn display(self) -> Str:
        ensures result == self.title
        effects []
"#,
        )
        .expect("write generic trait contract");
        for (name, source) in [
            (
                "echo",
                r#"package cott_bindings.traits

internal fun <T : kotlin.Any> echo(value: T, receiver: example.traits.TaskView<T, *>): T =
    value
"#,
            ),
            (
                "integer_only",
                r#"package cott_bindings.traits

internal fun integer_only(receiver: example.traits.TaskView<kotlin.Int, *>): kotlin.Int =
    7
"#,
            ),
            (
                "summary",
                r#"package cott_bindings.traits

internal fun summary(self: example.traits.SimpleTask): kotlin.String =
    self.title
"#,
            ),
            (
                "display",
                r#"package cott_bindings.traits

internal fun display(self: example.traits.SimpleTask): kotlin.String =
    self.title
"#,
            ),
        ] {
            fs::write(
                root.join(format!("kotlin/cott_bindings/traits/{name}.kt")),
                source,
            )
            .expect("write canonical Kotlin trait helper");
        }
        Self { root }
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
}

impl Drop for Fixture {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.root);
    }
}

fn toml_string(path: &Path) -> String {
    format!("{:?}", path.to_string_lossy())
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

fn pinned_toolchain() -> (PathBuf, PathBuf) {
    let kotlin_home = std::env::var_os("COTT_KOTLIN_HOME")
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("/tmp/cott-kotlin-toolchain/kotlinc"));
    let java_home = std::env::var_os("JAVA_HOME")
        .map(PathBuf::from)
        .unwrap_or_else(|| PathBuf::from("/tmp/cott-kotlin-toolchain/jdk"));
    (kotlin_home, java_home)
}

fn compile_fixture_class(fixture: &Fixture, java_home: &Path) -> PathBuf {
    let source = fixture
        .root
        .join("jar-fixture/source/fixture/shadow/Hidden.java");
    let classes = fixture.root.join("jar-fixture/classes");
    fs::create_dir_all(source.parent().expect("fixture class source parent"))
        .expect("create fixture class source directory");
    fs::create_dir_all(&classes).expect("create fixture class output directory");
    fs::write(
        &source,
        b"package fixture.shadow;\npublic final class Hidden { public static int value() { return 7; } }\n",
    )
    .expect("write fixture Java class");
    let output = Command::new(java_home.join("bin/javac"))
        .args(["--release", "9", "-d"])
        .arg(&classes)
        .arg(&source)
        .output()
        .expect("run JDK Java compiler");
    assert_success("fixture Java class compilation", output);
    let class = classes.join("fixture/shadow/Hidden.class");
    assert!(
        class.is_file(),
        "Java compiler must produce a real class file"
    );
    class
}

fn write_class_jar(
    fixture: &Fixture,
    java_home: &Path,
    class: &Path,
    name: &str,
    root_entry: bool,
    versioned_entry: bool,
    extra_manifest: Option<&[u8]>,
) -> PathBuf {
    assert!(
        root_entry || versioned_entry,
        "class fixture JAR needs at least one class entry"
    );
    let staging = fixture.root.join("jar-fixture").join(name);
    if root_entry {
        let destination = staging.join("fixture/shadow/Hidden.class");
        fs::create_dir_all(destination.parent().expect("root class parent"))
            .expect("create root class staging directory");
        fs::copy(class, destination).expect("stage root class");
    }
    let manifest = if versioned_entry || extra_manifest.is_some() {
        if versioned_entry {
            let destination = staging.join("META-INF/versions/9/fixture/shadow/Hidden.class");
            fs::create_dir_all(destination.parent().expect("versioned class parent"))
                .expect("create versioned class staging directory");
            fs::copy(class, destination).expect("stage versioned class");
        }
        let manifest = fixture.root.join("jar-fixture").join(format!("{name}.mf"));
        let mut bytes = b"Manifest-Version: 1.0\n".to_vec();
        if versioned_entry {
            bytes.extend_from_slice(b"Multi-Release: true\n");
        }
        if let Some(extra) = extra_manifest {
            bytes.extend_from_slice(extra);
            if !extra.ends_with(b"\n") {
                bytes.push(b'\n');
            }
        }
        bytes.push(b'\n');
        fs::write(&manifest, bytes).expect("write fixture manifest");
        Some(manifest)
    } else {
        None
    };
    let output = fixture.root.join("libs").join(name);
    fs::create_dir_all(output.parent().expect("fixture JAR parent"))
        .expect("create fixture JAR directory");
    let mut command = Command::new(java_home.join("bin/jar"));
    command.args(["--create", "--file"]).arg(&output);
    if let Some(manifest) = manifest {
        command.arg("--manifest").arg(manifest);
    }
    let result = command
        .arg("-C")
        .arg(&staging)
        .arg(".")
        .output()
        .expect("run JDK jar tool");
    assert_success("fixture JAR creation", result);
    output
}

fn write_forged_evidence_host_jar(fixture: &Fixture, java_home: &Path) {
    let source = fixture
        .root
        .join("host-exit/source/fixture/escape/HostExit.java");
    let classes = fixture.root.join("host-exit/classes");
    fs::create_dir_all(source.parent().expect("host source parent"))
        .expect("create host source directory");
    fs::create_dir_all(&classes).expect("create host classes directory");
    fs::write(
        &source,
        br#"package fixture.escape;

public final class HostExit {
    private static final String PREFIX = "COTT_KOTLIN_VERIFY:";

    public static int answer() {
        System.out.println(PREFIX + "{\"kind\":\"case\",\"symbol\":\"example.escape.answer\",\"case\":0,\"status\":\"passed\",\"phase\":null,\"clause\":null,\"error_symbol\":null,\"observations\":[{\"symbol\":\"example.escape.answer\",\"clause\":\"ensures:0\",\"phase\":\"ensures\",\"passed\":true}]}");
        System.out.println(PREFIX + "{\"kind\":\"done\"}");
        System.exit(0);
        return 7;
    }
}
"#,
    )
    .expect("write host exit source");
    let compiled = Command::new(java_home.join("bin/javac"))
        .args(["--release", "17", "-d"])
        .arg(&classes)
        .arg(&source)
        .output()
        .expect("compile forged-evidence host class");
    assert_success("forged-evidence host compilation", compiled);
    let output = fixture.root.join("libs/host-exit.jar");
    fs::create_dir_all(output.parent().expect("host JAR parent"))
        .expect("create host JAR directory");
    let archived = Command::new(java_home.join("bin/jar"))
        .args(["--create", "--file"])
        .arg(&output)
        .arg("-C")
        .arg(&classes)
        .arg(".")
        .output()
        .expect("create forged-evidence host JAR");
    assert_success("forged-evidence host JAR creation", archived);
}

fn generation_view(fixture: &Fixture) -> Value {
    snapshot::read(
        &fs::read(fixture.root.join("generated/generation.json"))
            .expect("read Kotlin generation record"),
    )
}

fn assert_current_unverified(fixture: &Fixture) {
    let generation = generation_view(fixture);
    assert_eq!(
        generation["current"]["verified"], false,
        "verification rejection must not certify the current snapshot"
    );
}

fn configure_classpath(fixture: &Fixture, entries: &[&str]) {
    let path = fixture.root.join("cott.toml");
    let manifest = fs::read_to_string(&path).expect("read Kotlin fixture manifest");
    let classpath = entries
        .iter()
        .map(|entry| format!("{entry:?}"))
        .collect::<Vec<_>>()
        .join(", ");
    let updated = manifest.replacen(
        "runtime_validation = \"boundary\"\n",
        &format!("runtime_validation = \"boundary\"\nclasspath = [{classpath}]\n"),
        1,
    );
    assert_ne!(updated, manifest, "fixture manifest insertion point");
    fs::write(path, updated).expect("configure Kotlin fixture classpath");
}

fn compile_and_run_type_only_consumer(fixture: &Fixture, kotlin_home: &Path, java_home: &Path) {
    let deployment = fixture.root.join("dist/verify-types-0.1.0");
    let source = fixture.root.join("native-consumer/TypeOnlyConsumer.kt");
    fs::create_dir_all(source.parent().expect("native consumer source parent"))
        .expect("create native consumer source directory");
    fs::write(
        &source,
        r#"package cott_type_only_consumer

import example.types.DEFAULT_COUNT
import example.types.Pair

fun main(): Unit {
    val pair = Pair(DEFAULT_COUNT, 9)
    check(pair.left == 7)
    check(pair.right == 9)
    println("type-only-ok")
}
"#,
    )
    .expect("write native type-only consumer");
    let module = deployment.join("cott-module.jar");
    let coroutines = deployment.join("runtime-libs/kotlinx-coroutines-core-jvm.jar");
    let versioned = deployment.join("runtime-libs/000-versioned.jar");
    let stdlib = kotlin_home.join("lib/kotlin-stdlib.jar");
    let consumer = fixture.root.join("native-consumer/type-only-consumer.jar");
    let compile_classpath = std::env::join_paths([&module, &coroutines, &versioned, &stdlib])
        .expect("construct native consumer compile classpath");
    let compiled = Command::new(kotlin_home.join("bin/kotlinc"))
        .arg(&source)
        .args(["-no-stdlib", "-no-reflect", "-classpath"])
        .arg(&compile_classpath)
        .args([
            "-jvm-target",
            "17",
            "-Xjdk-release=17",
            "-module-name",
            "cott_type_only_consumer",
            "-d",
        ])
        .arg(&consumer)
        .env("JAVA_HOME", java_home)
        .env(
            "JAVA_OPTS",
            "-Xms32m -Xmx512m -XX:MaxMetaspaceSize=256m -XX:CompressedClassSpaceSize=64m -XX:ReservedCodeCacheSize=128m -XX:ActiveProcessorCount=2 -XX:+UseSerialGC",
        )
        .output()
        .expect("compile native type-only consumer");
    assert_success("native type-only consumer compilation", compiled);
    let runtime_classpath =
        std::env::join_paths([&consumer, &module, &coroutines, &versioned, &stdlib])
            .expect("construct native consumer runtime classpath");
    let runtime = Command::new(java_home.join("bin/java"))
        .args([
            "-Xms16m",
            "-Xmx256m",
            "-XX:MaxMetaspaceSize=128m",
            "-XX:CompressedClassSpaceSize=64m",
            "-XX:ReservedCodeCacheSize=64m",
            "-XX:ActiveProcessorCount=2",
            "-XX:+UseSerialGC",
            "-ea",
            "-cp",
        ])
        .arg(runtime_classpath)
        .arg("cott_type_only_consumer.TypeOnlyConsumerKt")
        .output()
        .expect("run native type-only consumer");
    let stdout = runtime.stdout.clone();
    assert_success("native type-only consumer execution", runtime);
    assert_eq!(
        String::from_utf8(stdout).expect("consumer UTF-8"),
        "type-only-ok\n"
    );
}

fn compile_and_run_process_exit_consumer(
    fixture: &Fixture,
    kotlin_home: &Path,
    java_home: &Path,
) -> Output {
    let source = fixture.root.join("native-consumer/ProcessExitConsumer.kt");
    fs::create_dir_all(source.parent().expect("native consumer source parent"))
        .expect("create native consumer source directory");
    fs::write(
        &source,
        r#"package cott_process_exit_consumer

import example.process_exit.exit_with_code

fun main(): kotlin.Unit {
    exit_with_code(37.toUByte())
}
"#,
    )
    .expect("write native process-exit consumer");
    let module = fixture.root.join("generated/library/cott-module.jar");
    let coroutines = fixture
        .root
        .join("generated/runtime-libs/kotlinx-coroutines-core-jvm.jar");
    let stdlib = kotlin_home.join("lib/kotlin-stdlib.jar");
    let consumer = fixture
        .root
        .join("native-consumer/process-exit-consumer.jar");
    let compile_classpath = std::env::join_paths([&module, &coroutines, &stdlib])
        .expect("construct process-exit consumer compile classpath");
    let compiled = Command::new(kotlin_home.join("bin/kotlinc"))
        .arg(&source)
        .args(["-no-stdlib", "-no-reflect", "-classpath"])
        .arg(&compile_classpath)
        .args([
            "-jvm-target",
            "17",
            "-Xjdk-release=17",
            "-module-name",
            "cott_process_exit_consumer",
            "-d",
        ])
        .arg(&consumer)
        .env("JAVA_HOME", java_home)
        .env(
            "JAVA_OPTS",
            "-Xms32m -Xmx512m -XX:MaxMetaspaceSize=256m -XX:CompressedClassSpaceSize=64m -XX:ReservedCodeCacheSize=128m -XX:ActiveProcessorCount=2 -XX:+UseSerialGC",
        )
        .output()
        .expect("compile native process-exit consumer");
    assert_success("native process-exit consumer compilation", compiled);
    let runtime_classpath = std::env::join_paths([&consumer, &module, &coroutines, &stdlib])
        .expect("construct process-exit consumer runtime classpath");
    Command::new(java_home.join("bin/java"))
        .args([
            "-Xms16m",
            "-Xmx256m",
            "-XX:MaxMetaspaceSize=128m",
            "-XX:CompressedClassSpaceSize=64m",
            "-XX:ReservedCodeCacheSize=64m",
            "-XX:ActiveProcessorCount=2",
            "-XX:+UseSerialGC",
            "-ea",
            "-cp",
        ])
        .arg(runtime_classpath)
        .arg("cott_process_exit_consumer.ProcessExitConsumerKt")
        .output()
        .expect("run native process-exit consumer")
}

#[test]
fn verify_rejects_a_missing_configured_kotlin_compiler_without_a_fake_jar() {
    let fixture = Fixture::new(Path::new("kotlinc-never-run"), Path::new("java"));
    assert_success("Kotlin emission", fixture.cott(&["emit", "kotlin"]));

    let verified = fixture.cott(&["verify"]);
    assert!(
        !verified.status.success(),
        "missing compiler must fail closed"
    );
    let stderr = String::from_utf8_lossy(&verified.stderr);
    assert!(
        stderr.contains("kotlinc-never-run") && stderr.contains("not found on PATH"),
        "configured compiler identity must survive the diagnostic: {stderr}"
    );
    assert!(
        !fixture
            .root
            .join("generated/library/cott-module.jar")
            .exists(),
        "failed verification must not publish a compiled artifact"
    );
}

#[test]
fn removing_a_manifest_binding_leaves_the_callable_unresolved() {
    let fixture = Fixture::new(Path::new("kotlinc-never-run"), Path::new("java"));
    assert_success("bound Kotlin emission", fixture.cott(&["emit", "kotlin"]));
    assert_eq!(
        generation_view(&fixture)["current"]["implementations"][0]["owner"],
        "manifest"
    );

    let manifest_path = fixture.root.join("cott.toml");
    let manifest = fs::read_to_string(&manifest_path).expect("read Kotlin fixture manifest");
    let (unbound, _) = manifest
        .split_once("\n[target.kotlin.implementations]\n")
        .expect("fixture manifest selects a binding");
    fs::write(&manifest_path, format!("{unbound}\n")).expect("remove manifest binding");
    fs::remove_dir_all(fixture.root.join("kotlin/cott_bindings")).expect("remove binding source");

    assert_success("unbound Kotlin emission", fixture.cott(&["emit", "kotlin"]));
    let current = &generation_view(&fixture)["current"];
    assert_eq!(current["implementations"], serde_json::json!([]));
    assert_eq!(
        current["unresolved"],
        serde_json::json!(["example.counter.increment"])
    );
    assert_eq!(current["verified"], false);
}

#[test]
#[ignore = "requires the pinned Kotlin 2.2.10/JDK 17 toolchain and bubblewrap"]
fn option_payload_candidates_reach_nonempty_guarded_obligations() {
    let (kotlin_home, java_home) = pinned_toolchain();
    let fixture = Fixture::new(
        &kotlin_home.join("bin/kotlinc"),
        &java_home.join("bin/java"),
    );
    fs::write(
        fixture.root.join("src/example/counter.cott"),
        r#"module example.counter

fn increment(current: Option[Str]) -> U64:
    requires current matches Option.Some(text) => text.len > 0
    ensures current matches Option.Some(text) => result == text.len

    effects []
"#,
    )
    .expect("write guarded optional-input contract");
    fs::write(
        fixture
            .root
            .join("kotlin/cott_bindings/counter/increment.kt"),
        r#"package cott_bindings.counter

internal fun increment(current: cott_runtime.CottOption<kotlin.String>): kotlin.ULong =
    when (current) {
        is cott_runtime.Some -> current.value.codePointCount(0, current.value.length).toULong()
        cott_runtime.Nothing -> 0UL
    }
"#,
    )
    .expect("write real optional-input implementation");
    let path = fixture.root.join("cott.toml");
    let mut manifest = fs::read_to_string(&path).expect("read fixture manifest");
    manifest.push_str(
        "\n[verification]\ncandidate_limit = 17\n\n[[verification.coverage.rules]]\nsymbol = \"example.counter.increment\"\nclauses = [\"ensures:1\"]\nallow_unknown = false\nallow_unobserved = false\nallow_trust_declaration = false\n",
    );
    fs::write(path, manifest).expect("require actual guarded predicate evidence");
    assert_success("optional input emission", fixture.cott(&["emit", "kotlin"]));
    assert_success("optional input verification", fixture.cott(&["verify"]));
    let generation = generation_view(&fixture);
    assert_eq!(generation["current"]["verified"], true);
}

#[test]
#[ignore = "requires the pinned Kotlin 2.2.10/JDK 17 toolchain and bubblewrap"]
fn valid_fixture_produces_a_real_jar_and_executed_clause_evidence() {
    let (kotlin_home, java_home) = pinned_toolchain();
    let fixture = Fixture::new(
        &kotlin_home.join("bin/kotlinc"),
        &java_home.join("bin/java"),
    );
    assert_success("Kotlin emission", fixture.cott(&["emit", "kotlin"]));
    assert_success("Kotlin verification", fixture.cott(&["verify"]));

    let module = fixture.root.join("generated/library/cott-module.jar");
    let coroutines = fixture
        .root
        .join("generated/runtime-libs/kotlinx-coroutines-core-jvm.jar");
    assert!(
        fs::metadata(&module).is_ok_and(|metadata| metadata.len() > 0),
        "verification must publish a non-empty JVM library"
    );
    assert!(
        fs::metadata(&coroutines).is_ok_and(|metadata| metadata.len() > 0),
        "verification must publish its hashed coroutine runtime"
    );

    let generation = generation_view(&fixture);
    let current = &generation["current"];
    assert_eq!(current["verified"], true);
    assert_eq!(
        generation["last_verified"], *current,
        "a certified record must expand to one shared snapshot"
    );
    assert_eq!(current["tools"]["kotlin"]["version"], "2.2.10");
    assert_eq!(
        current["tools"]["runtime_dependencies"]["kotlin_stdlib"]["required"],
        true
    );
    assert_eq!(
        current["tools"]["runtime_dependencies"]["kotlinx_coroutines_core_jvm"]["version"],
        "1.8.0"
    );
    let contracts = current["verification"]["contract_tests"]["contracts"]
        .as_array()
        .expect("contract report must retain its clause inventory");
    assert!(!contracts.is_empty(), "contract report cannot be empty");
    assert_eq!(
        current["verification"]["contract_tests"]["observation_inventory"]["status"],
        "executed"
    );
    assert!(
        current["verification"]["contract_tests"]["observation_inventory"]["cases"]
            .as_u64()
            .is_some_and(|cases| cases > 0),
        "callable verification must retain executed case inventory"
    );
    assert!(contracts.iter().any(|contract| {
        contract["symbol"] == "example.counter.increment"
            && contract["clause_id"] == "ensures:2"
            && contract["evidence"].as_array().is_some_and(|evidence| {
                evidence.iter().any(|item| item["grade"] == "runtime check")
            })
    }));
    assert!(
        current["semantic_coverage"]["summary"]["observed"]
            .as_u64()
            .is_some_and(|observed| observed >= 3),
        "requires and ensures clauses need positive runtime evidence"
    );
}

#[test]
#[ignore = "requires the pinned Kotlin 2.2.10/JDK 17 toolchain and bubblewrap"]
fn async_precondition_failures_are_not_cancellation_failures() {
    let (kotlin_home, java_home) = pinned_toolchain();
    let fixture = Fixture::new(
        &kotlin_home.join("bin/kotlinc"),
        &java_home.join("bin/java"),
    );
    let contract = fixture.root.join("src/example/counter.cott");
    let source = fs::read_to_string(&contract).expect("read owned fixture contract");
    fs::write(
        &contract,
        source.replace("fn increment", "async fn increment"),
    )
    .expect("make fixture asynchronous");
    let implementation = fixture
        .root
        .join("kotlin/cott_bindings/counter/increment.kt");
    let source = fs::read_to_string(&implementation).expect("read owned fixture implementation");
    fs::write(
        &implementation,
        source.replace("internal fun increment", "internal suspend fun increment"),
    )
    .expect("make fixture helper asynchronous");
    assert_success("async fixture emission", fixture.cott(&["emit", "kotlin"]));
    assert_success("async fixture verification", fixture.cott(&["verify"]));
    let generation = generation_view(&fixture);
    let report = &generation["current"]["verification"]["contract_tests"];
    let cases = report["cases"].as_array().expect("observed callable cases");
    assert!(cases.iter().any(|case| case["status"] == "passed"));
    let ineligible = cases
        .iter()
        .filter(|case| case["status"] == "ineligible")
        .collect::<Vec<_>>();
    assert!(
        !ineligible.is_empty(),
        "fixture must exercise rejected inputs"
    );
    let lifecycle = report["lifecycle"]
        .as_array()
        .expect("cancellation evidence");
    for case in ineligible {
        let cancellation = lifecycle
            .iter()
            .find(|event| event["symbol"] == case["symbol"] && event["case"] == case["case"])
            .expect("each candidate has cancellation evidence");
        assert_eq!(cancellation["status"], "candidate_unavailable");
    }
}

#[test]
#[ignore = "requires the pinned Kotlin 2.2.10/JDK 17 toolchain and bubblewrap"]
fn generic_trait_candidates_preserve_specialization_and_inherited_associated_types() {
    let (kotlin_home, java_home) = pinned_toolchain();
    let fixture = Fixture::generic_trait(
        &kotlin_home.join("bin/kotlinc"),
        &java_home.join("bin/java"),
    );
    assert_success(
        "generic trait Kotlin emission",
        fixture.cott(&["emit", "kotlin"]),
    );
    assert_success(
        "generic trait Kotlin verification",
        fixture.cott(&["verify"]),
    );

    let generation = generation_view(&fixture);
    let current = &generation["current"];
    assert_eq!(current["verified"], true);
    let report = &current["verification"]["contract_tests"];
    let cases = report["cases"]
        .as_array()
        .expect("authenticated callable cases");
    assert!(
        cases
            .iter()
            .any(|case| { case["symbol"] == "example.traits.echo" && case["status"] == "passed" }),
        "a concrete TaskView[Str] must produce an executed generic facade call: {report}"
    );
    let unavailable = report["unavailable"]
        .as_object()
        .expect("unavailable callable reasons");
    assert!(
        !unavailable.contains_key("example.traits.echo"),
        "a supported generic trait callable must not silently become unavailable"
    );
    assert!(
        !cases
            .iter()
            .any(|case| case["symbol"] == "example.traits.integer_only"),
        "TaskView[Str] must never be passed as the incompatible TaskView[I32]"
    );
    assert!(
        unavailable
            .get("example.traits.integer_only")
            .and_then(Value::as_str)
            .is_some_and(|reason| !reason.is_empty()),
        "a closed trait specialization without a compatible implementation needs an honest reason"
    );
}

#[test]
#[ignore = "requires the pinned Kotlin 2.2.10/JDK 17 toolchain and bubblewrap"]
fn canonical_clock_scenario_produces_authenticated_stable_named_clock_evidence() {
    let (kotlin_home, java_home) = pinned_toolchain();
    let fixture = Fixture::clock_scenario(
        &kotlin_home.join("bin/kotlinc"),
        &java_home.join("bin/java"),
    );
    assert_success(
        "clock scenario Kotlin emission",
        fixture.cott(&["emit", "kotlin"]),
    );
    assert_success(
        "clock scenario Kotlin verification",
        fixture.cott(&["verify"]),
    );

    let generation = generation_view(&fixture);
    let current = &generation["current"];
    assert_eq!(current["verified"], true);
    let scenarios = current["verification"]["contract_tests"]["scenarios"]
        .as_array()
        .expect("clock scenario evidence");
    let scenario = scenarios
        .iter()
        .find(|scenario| scenario["scenario_id"] == "example.clock.scenario.deterministic_clock")
        .expect("authenticated deterministic clock scenario evidence");
    assert_eq!(scenario["status"], "passed");
    assert_eq!(scenario["assertions"], 3);
}

#[test]
#[ignore = "requires the pinned Kotlin 2.2.10/JDK 17 toolchain and bubblewrap"]
fn verified_process_exit_facade_terminates_a_separate_jvm_with_supplied_status() {
    let (kotlin_home, java_home) = pinned_toolchain();
    let fixture = Fixture::process_exit(
        &kotlin_home.join("bin/kotlinc"),
        &java_home.join("bin/java"),
    );
    assert_success(
        "process-exit Kotlin emission",
        fixture.cott(&["emit", "kotlin"]),
    );
    assert_success(
        "process-exit Kotlin verification",
        fixture.cott(&["verify"]),
    );
    assert_eq!(generation_view(&fixture)["current"]["verified"], true);

    let exited = compile_and_run_process_exit_consumer(&fixture, &kotlin_home, &java_home);
    assert_eq!(
        exited.status.code(),
        Some(37),
        "the public facade must terminate its child JVM with the supplied status\nstdout:\n{}\nstderr:\n{}",
        String::from_utf8_lossy(&exited.stdout),
        String::from_utf8_lossy(&exited.stderr),
    );
}

#[test]
#[ignore = "requires the pinned Kotlin 2.2.10/JDK 17 toolchain and bubblewrap"]
fn type_only_module_verifies_deploys_and_runs_from_a_native_consumer() {
    let (kotlin_home, java_home) = pinned_toolchain();
    let fixture = Fixture::type_only(
        &kotlin_home.join("bin/kotlinc"),
        &java_home.join("bin/java"),
    );
    let class = compile_fixture_class(&fixture, &java_home);
    write_class_jar(
        &fixture,
        &java_home,
        &class,
        "versioned.jar",
        true,
        true,
        None,
    );

    assert_success(
        "type-only Kotlin emission",
        fixture.cott(&["emit", "kotlin"]),
    );
    assert_success("type-only Kotlin verification", fixture.cott(&["verify"]));
    let generation = generation_view(&fixture);
    let current = &generation["current"];
    assert_eq!(current["verified"], true);
    let contract_tests = &current["verification"]["contract_tests"];
    for field in ["cases", "contracts", "lifecycle", "scenarios", "strategies"] {
        assert_eq!(
            contract_tests[field],
            serde_json::json!([]),
            "type-only `{field}` inventory must be empty"
        );
    }
    assert_eq!(contract_tests["unavailable"], serde_json::json!({}));
    assert_eq!(
        contract_tests["observation_inventory"],
        serde_json::json!({
            "cases": 0,
            "clauses": 0,
            "lifecycle": 0,
            "scenarios": 0,
            "strategies": 0,
            "status": "not_applicable",
        })
    );
    assert_eq!(
        current["semantic_coverage"]["clauses"],
        serde_json::json!([])
    );
    assert_eq!(
        current["semantic_coverage"]["summary"],
        serde_json::json!({
            "observed": 0,
            "unobserved": 0,
            "trust_declaration": 0,
            "unknown": 0,
        })
    );

    assert_success("type-only Kotlin deployment", fixture.cott(&["deploy"]));
    let deployment = fixture.root.join("dist/verify-types-0.1.0");
    for relative in [
        "cott-module.jar",
        "dependencies.json",
        "generation.json",
        "runtime-libs/kotlinx-coroutines-core-jvm.jar",
        "runtime-libs/000-versioned.jar",
    ] {
        assert!(
            deployment.join(relative).is_file(),
            "type-only deployment omitted `{relative}`"
        );
    }
    let deployed = fs::read(deployment.join("generation.json")).expect("deployed record");
    let deployed_view = snapshot::read(&deployed);
    assert_eq!(deployed_view["current"]["verified"], true);
    assert_eq!(deployed_view["current"], deployed_view["last_verified"]);
    assert_eq!(
        deployed,
        fs::read(fixture.root.join("generated/generation.json"))
            .expect("published generation record"),
        "deployment must copy the self-contained record verbatim"
    );
    compile_and_run_type_only_consumer(&fixture, &kotlin_home, &java_home);
}

#[test]
#[ignore = "requires the pinned Kotlin 2.2.10/JDK 17 toolchain and bubblewrap"]
fn multi_release_class_entries_cannot_hide_classpath_shadowing() {
    let (kotlin_home, java_home) = pinned_toolchain();
    let fixture = Fixture::new(
        &kotlin_home.join("bin/kotlinc"),
        &java_home.join("bin/java"),
    );
    let class = compile_fixture_class(&fixture, &java_home);
    write_class_jar(&fixture, &java_home, &class, "root.jar", true, false, None);
    write_class_jar(
        &fixture,
        &java_home,
        &class,
        "versioned.jar",
        false,
        true,
        None,
    );
    configure_classpath(&fixture, &["libs/root.jar", "libs/versioned.jar"]);

    assert_success(
        "shadowing fixture emission",
        fixture.cott(&["emit", "kotlin"]),
    );
    let rejected = fixture.cott(&["verify"]);
    assert!(
        !rejected.status.success(),
        "a versioned class must not bypass classpath shadow rejection"
    );
    let stderr = String::from_utf8_lossy(&rejected.stderr);
    assert!(
        stderr.contains("fixture/shadow/Hidden.class")
            && stderr.contains("classpath[0]")
            && stderr.contains("classpath[1]"),
        "shadow diagnostic must identify the effective class and both JARs: {stderr}"
    );
    assert_current_unverified(&fixture);
    assert!(
        !fixture
            .root
            .join("generated/library/cott-module.jar")
            .exists(),
        "rejected shadowing must not publish a compiled artifact"
    );
}

#[test]
#[ignore = "requires the pinned Kotlin 2.2.10/JDK 17 toolchain and bubblewrap"]
fn manifest_class_path_is_rejected_from_real_folded_case_insensitive_jar_metadata() {
    let (kotlin_home, java_home) = pinned_toolchain();
    let fixture = Fixture::new(
        &kotlin_home.join("bin/kotlinc"),
        &java_home.join("bin/java"),
    );
    let class = compile_fixture_class(&fixture, &java_home);
    write_class_jar(
        &fixture,
        &java_home,
        &class,
        "manifest-class-path.jar",
        true,
        false,
        Some(
            b"cLaSs-PaTh: dependencies/aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa.jar dependencies/bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb.jar\n",
        ),
    );
    configure_classpath(&fixture, &["libs/manifest-class-path.jar"]);

    assert_success(
        "manifest Class-Path fixture emission",
        fixture.cott(&["emit", "kotlin"]),
    );
    let rejected = fixture.cott(&["verify"]);
    assert!(
        !rejected.status.success(),
        "a manifest Class-Path must not expand the audited dependency closure"
    );
    let stderr = String::from_utf8_lossy(&rejected.stderr);
    assert!(
        stderr.contains("classpath[0]")
            && stderr.contains("Class-Path")
            && stderr.contains("nonempty"),
        "manifest rejection must identify the configured JAR and attribute: {stderr}"
    );
    assert_current_unverified(&fixture);
    assert!(
        !fixture
            .root
            .join("generated/library/cott-module.jar")
            .exists(),
        "manifest rejection must not publish a compiled artifact"
    );
}

#[test]
#[ignore = "requires the pinned Kotlin 2.2.10/JDK 17 toolchain and bubblewrap"]
fn external_host_exit_with_forged_legacy_rows_cannot_authorize_verification() {
    let (kotlin_home, java_home) = pinned_toolchain();
    let fixture = Fixture::forged_evidence(
        &kotlin_home.join("bin/kotlinc"),
        &java_home.join("bin/java"),
    );
    write_forged_evidence_host_jar(&fixture, &java_home);

    assert_success(
        "forged-evidence fixture emission",
        fixture.cott(&["emit", "kotlin"]),
    );
    let rejected = fixture.cott(&["verify"]);
    assert!(
        !rejected.status.success(),
        "external host exit with successful OS status cannot authorize forged stdout evidence"
    );
    assert_current_unverified(&fixture);
    assert!(
        !fixture
            .root
            .join("generated/library/cott-module.jar")
            .exists(),
        "forged evidence rejection must not publish a compiled artifact"
    );
}

/// Negative integer literals and integer arithmetic in scenario call arguments, data and
/// constructor fields are exact ABI values (`Int`, `Long`, `Byte`), including the minimum
/// value whose negated operand is outside its own type.
fn negative_integer_scenario(compiler: &Path, java: &Path) -> Fixture {
    let root = fixture_root();
    fs::create_dir_all(root.join("src/example")).expect("create contract source directory");
    fs::create_dir_all(root.join("kotlin/cott_bindings/neg"))
        .expect("create Kotlin binding directory");
    fs::write(
        root.join("cott.toml"),
        format!(
            r#"[project]
name = "verify-negative"
version = "0.1.0"
source = "src"

[target.kotlin]
source = "kotlin"
generated = "generated/kotlin"
compiler = {}
java = {}
jvm_target = 17
runtime_validation = "boundary"

[target.kotlin.implementations]
"example.neg.widen" = "cott_bindings.neg.widen"
"example.neg.shares" = "cott_bindings.neg.shares"
"#,
            toml_string(compiler),
            toml_string(java),
        ),
    )
    .expect("write negative-integer manifest");
    fs::write(
        root.join("src/example/neg.cott"),
        r#"module example.neg

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
    )
    .expect("write negative-integer contract");
    fs::write(
        root.join("kotlin/cott_bindings/neg/widen.kt"),
        "package cott_bindings.neg\n\ninternal fun widen(left: kotlin.Int, right: kotlin.Int): kotlin.Long =\n    left.toLong() + right.toLong()\n",
    )
    .expect("write widen implementation");
    fs::write(
        root.join("kotlin/cott_bindings/neg/shares.kt"),
        "package cott_bindings.neg\n\ninternal fun shares(holding: example.neg.Holding): kotlin.Long =\n    holding.shares\n",
    )
    .expect("write shares implementation");
    Fixture { root }
}

#[test]
#[ignore = "requires the pinned Kotlin 2.2.10/JDK 17 toolchain and bubblewrap"]
fn negative_integer_scenario_values_use_exact_kotlin_abi_types() {
    let (kotlin_home, java_home) = pinned_toolchain();
    let fixture = negative_integer_scenario(
        &kotlin_home.join("bin/kotlinc"),
        &java_home.join("bin/java"),
    );
    assert_success(
        "negative-integer Kotlin emission",
        fixture.cott(&["emit", "kotlin"]),
    );
    assert_success(
        "negative-integer Kotlin verification",
        fixture.cott(&["verify"]),
    );
    let generation = generation_view(&fixture);
    let current = &generation["current"];
    assert_eq!(current["verified"], true);
    let scenario = current["verification"]["contract_tests"]["scenarios"]
        .as_array()
        .expect("negative-integer scenario evidence")
        .iter()
        .find(|scenario| scenario["scenario_id"] == "example.neg.scenario.negative_arguments")
        .expect("negative-integer scenario evidence");
    assert_eq!(scenario["status"], "passed", "{scenario}");
    assert_eq!(scenario["assertions"], 5, "{scenario}");
}

#[test]
#[ignore = "requires the pinned Kotlin 2.2.10/JDK 17 toolchain and bubblewrap"]
fn native_impl_scenario_executes_initializer_receiver_method_and_nested_dyn_argument() {
    let (kotlin_home, java_home) = pinned_toolchain();
    let fixture = Fixture::generic_trait(
        &kotlin_home.join("bin/kotlinc"),
        &java_home.join("bin/java"),
    );
    // `TaskView` inherits the associated `Summary` slot, so its Kotlin interface takes a
    // star-projected second type argument that every scenario-rendered `Dyn` must spell,
    // including inside a container argument.
    let contract = fixture.root.join("src/example/traits.cott");
    fs::write(
        &contract,
        format!(
            "{}\nfn inspect(view: Dyn[TaskView[Str]]) -> Str:\n    effects []\n\nfn first_summary(views: List[Dyn[TaskView[Str]]]) -> Str:\n    requires views.len > 0\n    effects []\n\nscenario view:\n    call task = SimpleTask(title: \"Launch\")\n    call summary = task.summary()\n    assert summary == \"Launch\"\n    data wrapped: Dyn[TaskView[Str]] = Dyn(value: task)\n    call observed = inspect(wrapped)\n    assert observed == \"Launch\"\n    call nested = inspect(Dyn(value: task))\n    assert nested == \"Launch\"\n    call listed = first_summary(List(Dyn(value: task)))\n    assert listed == \"Launch\"\n",
            fs::read_to_string(&contract).expect("trait source")
        ),
    )
    .expect("append native scenario");
    let manifest = fixture.root.join("cott.toml");
    fs::write(
        &manifest,
        format!(
            "{}\"example.traits.inspect\" = \"cott_bindings.traits.inspect\"\n\"example.traits.first_summary\" = \"cott_bindings.traits.first_summary\"\n",
            fs::read_to_string(&manifest).expect("trait manifest")
        ),
    )
    .expect("add inspect bindings");
    fs::write(
        fixture.root.join("kotlin/cott_bindings/traits/first_summary.kt"),
        "package cott_bindings.traits\n\ninternal fun first_summary(views: cott_runtime.CottList<cott_runtime.Dyn<example.traits.TaskView<kotlin.String, *>>>): kotlin.String =\n    views[0].value.summary().toString()\n",
    )
    .expect("write first_summary implementation");
    let inspect_file = fixture.root.join("kotlin/cott_bindings/traits/inspect.kt");
    let inspect = |body: &str| {
        fs::write(
            &inspect_file,
            format!(
                "package cott_bindings.traits\n\ninternal fun inspect(view: cott_runtime.Dyn<example.traits.TaskView<kotlin.String, *>>): kotlin.String =\n    {body}\n"
            ),
        )
        .expect("write inspect implementation");
    };
    inspect("view.value.summary().toString()");
    assert_success(
        "impl scenario Kotlin emission",
        fixture.cott(&["emit", "kotlin"]),
    );
    assert_success(
        "impl scenario Kotlin verification",
        fixture.cott(&["verify"]),
    );
    let generation = generation_view(&fixture);
    let scenario = generation["current"]["verification"]["contract_tests"]["scenarios"]
        .as_array()
        .expect("native scenarios")
        .iter()
        .find(|scenario| scenario["scenario_id"] == "example.traits.scenario.view")
        .expect("native impl scenario");
    assert_eq!(scenario["status"], "passed", "{scenario}");
    assert_eq!(scenario["assertions"], 4, "{scenario}");
    inspect("\"wrong\"");
    assert_success(
        "wrong inspect Kotlin emission",
        fixture.cott(&["emit", "kotlin"]),
    );
    let rejected = fixture.cott(&["verify"]);
    assert!(
        !rejected.status.success(),
        "wrong Dyn result passed verification"
    );
    assert!(
        String::from_utf8_lossy(&rejected.stderr)
            .contains("Kotlin scenario `example.traits.scenario.view` failed"),
        "{}",
        String::from_utf8_lossy(&rejected.stderr)
    );
}
