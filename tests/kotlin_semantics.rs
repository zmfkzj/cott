use std::collections::BTreeMap;
use std::ffi::OsString;
use std::fs::{self, File};
use std::io;
use std::path::{Path, PathBuf};
use std::process::{Command, Output, Stdio};
use std::sync::atomic::{AtomicU64, Ordering};
use std::thread;
use std::time::{Duration, Instant};

use cott::compiler::{SourceFile, parse_project};
use cott::hash::sha256_hex;
use cott::hir::lower;
use cott::ir::render;
use cott::kotlin::binding::validate_candidate;
use cott::kotlin::emit::{emit, implementation_signature};
use cott::kotlin::{KotlinBinding, KotlinCallable, KotlinOwner, KotlinPlan};
use cott::manifest::{
    GeneratorConfig, KotlinProjectConfig, KotlinTarget, ProjectMetadata, RuntimeValidation,
    VerificationConfig,
};

const LIBRARY_MODULE: &str = "cott_semantics_library";
const CONSUMER_MODULE: &str = "cott_semantics_consumer";
const DRIVER_MAIN_CLASS: &str = "cott_semantics.NativeSemanticsKt";
const PROCESS_POLL_INTERVAL: Duration = Duration::from_millis(20);
const COMPILER_TIMEOUT: Duration = Duration::from_secs(120);
const CONSUMER_TIMEOUT: Duration = Duration::from_secs(20);

const CONTRACT: &str = r#"module semantics

enum Choice[T]:
    Empty
    Value(value: T)

struct Node:
    value: I32
    next: Option[Node]

struct SharedNode:
    value: I32
    children: List[SharedNode]

trait Parent:
    type Item
    fn inherited(self, value: Parent.Item) -> Parent.Item

trait Child for Parent:
    fn child(self, value: Parent.Item) -> Parent.Item

trait Secondary:
    type Label
    fn secondary(self, value: Secondary.Label) -> Secondary.Label

trait Combined for Child + Secondary:
    fn combined(self, value: Parent.Item) -> Parent.Item

impl CombinedState for Combined:
    type Item = I32
    type Label = Str
    fn inherited(self, value: I32) -> I32:
        ensures result == value
    fn child(self, value: I32) -> I32:
        ensures result == value
    fn secondary(self, value: Str) -> Str:
        ensures result == value
    fn combined(self, value: I32) -> I32:
        ensures result == value

fn increment(value: I32) -> I32
fn echo(node: Node) -> Node
fn echo_shared(node: SharedNode) -> SharedNode
fn retain[T: Combined](value: T) -> T
"#;

const ABI_OPAQUE_TAG: &str = "kotlin-abi-secret";

const ABI_CONTRACT: &str = r#"module abi

alias Count = I32

newtype NonEmpty(Str)
    where self != ""

const DEFAULT_COUNT: I32 = 7
const DEFAULT_NON_EMPTY: NonEmpty = NonEmpty("ready")
const FIXED_VALUES: Array[U8, 2] = Array(1, 2)
const FIXED_BYTES: Buffer[2] = Buffer("00ff")

external type Moment

alias Secret = Opaque["kotlin-abi-secret"]

trait Reader:
    fn read(self) -> I32

impl ReaderState for Reader:
    fn read(self) -> I32:
        ensures result == 37

alias ReaderFactory = Factory[ReaderState]
alias DynamicReader = Dyn[Reader]

struct AbiBundle:
    count: Count
    label: NonEmpty
    values: Array[U8, 2]
    bytes: Buffer[2]
    moment: Moment
    secret: Secret
    factory: ReaderFactory
    dynamic: DynamicReader

fn echo_bundle(value: AbiBundle) -> AbiBundle
"#;

const CONSUMER: &str = r#"package cott_semantics

import cott_runtime.CottContractViolation
import cott_runtime.CottOption
import cott_runtime.CottList
import cott_runtime.Nothing
import cott_runtime.Some
import semantics.Child
import semantics.Choice
import semantics.Combined
import semantics.CombinedState
import semantics.Node
import semantics.SharedNode
import semantics.Secondary
import semantics.echo
import semantics.echo_shared
import semantics.increment
import semantics.retain

private inline fun expectViolation(block: () -> Unit): Unit {
    try {
        block()
        error("expected Cott validation to reject the value")
    } catch (_: CottContractViolation) {
        Unit
    }
}

fun main(): Unit {
    check(increment(41) == 42)

    val firstEmpty: Choice<Int> = Choice.Empty<Int>()
    val secondEmpty: Choice<Int> = Choice.Empty<Int>()
    val payload: Choice<Int> = Choice.Value(0)
    check(firstEmpty == secondEmpty)
    check(firstEmpty != payload)

    val valid = Node(1, Nothing)
    check(echo(valid) == valid)

    var shared = SharedNode(0, CottList(emptyList()))
    repeat(16) { depth ->
        val child = shared
        shared = SharedNode(depth + 1, CottList(listOf(child, child)))
    }
    val echoedShared = echo_shared(shared)
    check(echoedShared.value == 16)
    check(echoedShared.children.size == 2)

    @Suppress("UNCHECKED_CAST")
    val invalidNext = Some("not a node") as CottOption<Node>
    expectViolation { Node(0, invalidNext) }

    val nextField = Node::class.java.getDeclaredField("next").also {
        it.isAccessible = true
    }
    val cycle = Node(0, Nothing)
    nextField.set(cycle, Some(cycle))
    expectViolation { echo(cycle) }

    val deep = List(96) { Node(it, Nothing) }
    for (index in 0 until deep.lastIndex) {
        nextField.set(deep[index], Some(deep[index + 1]))
    }
    expectViolation { echo(deep.first()) }

    val combined = CombinedState()
    val composite: Combined<Int, String> = combined
    val child: Child<Int> = combined
    val secondary: Secondary<String> = combined
    check(child.inherited(7) == 7)
    check(child.child(9) == 9)
    check(composite.combined(11) == 11)
    check(secondary.secondary("usable") == "usable")
    val retained: CombinedState = retain(combined)
    check(retained == combined)
}
"#;

const ABI_CONSUMER: &str = r#"package cott_semantics

import abi.AbiBundle
import abi.Count
import abi.DEFAULT_COUNT
import abi.DEFAULT_NON_EMPTY
import abi.DynamicReader
import abi.FIXED_BYTES
import abi.FIXED_VALUES
import abi.Moment
import abi.NonEmpty
import abi.Reader
import abi.ReaderFactory
import abi.ReaderState
import abi.Secret
import abi.echo_bundle
import cott_runtime.CottArray
import cott_runtime.CottBuffer
import cott_runtime.CottFactory
import cott_runtime.CottTrait
import cott_runtime.Dyn
import cott_runtime.Opaque
import java.math.BigInteger
import java.time.Instant

private inline fun expectAbiViolation(block: () -> Unit): Unit {
    try {
        block()
        error("expected Cott validation to reject the ABI value")
    } catch (_: cott_runtime.CottContractViolation) {
        Unit
    }
}

fun main(): Unit {
    val count: Count = DEFAULT_COUNT
    check(count == 7)
    check(DEFAULT_NON_EMPTY.value == "ready")
    check(FIXED_VALUES.toList() == listOf(1.toUByte(), 2.toUByte()))
    check(FIXED_VALUES.dimension.value == BigInteger.valueOf(2))
    check(FIXED_BYTES.toByteArray().contentEquals(byteArrayOf(0, -1)))
    check(FIXED_BYTES.dimension.value == BigInteger.valueOf(2))
    val values =
        CottArray(listOf(5.toUByte(), 8.toUByte()), FIXED_VALUES.dimension)
    val bytes = CottBuffer(byteArrayOf(0x12, 0x34), FIXED_BYTES.dimension)
    check(values.dimension === FIXED_VALUES.dimension)
    check(bytes.dimension === FIXED_BYTES.dimension)

    val label = NonEmpty("valid")
    expectAbiViolation { NonEmpty("") }

    val moment: Moment = Instant.parse("2026-09-13T12:34:56Z")
    val secretPayload = Any()
    val secret: Secret =
        Opaque.of(cott_runtime.__COTT_OPAQUE_MARKER__, secretPayload)

    check(secret.tag.tag == "kotlin-abi-secret")
    val factory: ReaderFactory = CottFactory.of(ReaderState::class.java)
    val readerState = ReaderState()
    val reader: Reader = readerState
    @Suppress("UNCHECKED_CAST")
    val readerTrait = readerState.cottTraits.single() as CottTrait<Reader>
    val dynamic: DynamicReader = Dyn.of(reader, readerTrait)
    check(dynamic.value.read() == 37)
    check(dynamic.trait === readerTrait)

    val bundle = AbiBundle(
        count,
        label,
        values,
        bytes,
        moment,
        secret,
        factory,
        dynamic,
    )
    val echoed = echo_bundle(bundle)
    check(echoed === bundle)
    check(echoed.count == 7)
    check(echoed.label === label)
    check(echoed.values === values)
    check(echoed.values.toList() == listOf(5.toUByte(), 8.toUByte()))
    check(echoed.bytes === bytes)
    check(echoed.bytes.toByteArray().contentEquals(byteArrayOf(0x12, 0x34)))
    check(echoed.moment === moment)
    check(echoed.secret === secret)
    check(echoed.secret.unwrap() === secretPayload)
    check(echoed.factory === factory)
    check(echoed.factory.type === ReaderState::class.java)
    check(echoed.dynamic === dynamic)
    check(echoed.dynamic.value.read() == 37)
}
"#;

static NEXT_TEMP_DIR: AtomicU64 = AtomicU64::new(0);

struct TempDir {
    path: PathBuf,
}

impl TempDir {
    fn new() -> Self {
        let mut number = NEXT_TEMP_DIR.fetch_add(1, Ordering::Relaxed);
        loop {
            let path = std::env::temp_dir().join(format!(
                "cott-kotlin-semantics-{}-{number}",
                std::process::id()
            ));
            match fs::create_dir(&path) {
                Ok(()) => return Self { path },
                Err(error) if error.kind() == io::ErrorKind::AlreadyExists => number += 1,
                Err(error) => panic!(
                    "failed to create Kotlin semantics fixture {}: {error}",
                    path.display()
                ),
            }
        }
    }
}

impl Drop for TempDir {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.path);
    }
}

struct KotlinToolchain {
    kotlinc: PathBuf,
    java_home: PathBuf,
    java: PathBuf,
    stdlib: PathBuf,
    coroutines: PathBuf,
}

impl KotlinToolchain {
    fn from_required_environment() -> Self {
        let kotlin_home = PathBuf::from(
            std::env::var_os("COTT_KOTLIN_HOME")
                .expect("COTT_KOTLIN_HOME must name the Kotlin compiler installation"),
        );
        let java_home = PathBuf::from(
            std::env::var_os("JAVA_HOME").expect("JAVA_HOME must name a JDK 17 installation"),
        );
        let toolchain = Self {
            kotlinc: kotlin_home.join("bin/kotlinc"),
            java: java_home.join("bin/java"),
            java_home,
            stdlib: kotlin_home.join("lib/kotlin-stdlib.jar"),
            coroutines: kotlin_home.join("lib/kotlinx-coroutines-core-jvm.jar"),
        };
        for (description, path) in [
            ("Kotlin compiler", &toolchain.kotlinc),
            ("Java launcher", &toolchain.java),
            ("Kotlin standard library", &toolchain.stdlib),
            ("Kotlin coroutines runtime", &toolchain.coroutines),
        ] {
            assert!(
                path.is_file(),
                "{description} is missing at {}",
                path.display()
            );
        }
        toolchain
    }
}

fn classpath(paths: &[&Path]) -> OsString {
    std::env::join_paths(paths.iter().copied())
        .expect("temporary Kotlin classpath should be representable")
}

fn assert_command_succeeded(label: &str, output: Output) {
    assert!(
        output.status.success(),
        "{label} failed with {}\nstdout:\n{}\nstderr:\n{}",
        output.status,
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr),
    );
}

fn bounded_output(label: &str, command: &mut Command, scratch: &Path, timeout: Duration) -> Output {
    let stdout_path = scratch.join(format!("{label}.stdout"));
    let stderr_path = scratch.join(format!("{label}.stderr"));
    command
        .stdout(Stdio::from(
            File::create(&stdout_path).expect("process stdout capture should be writable"),
        ))
        .stderr(Stdio::from(
            File::create(&stderr_path).expect("process stderr capture should be writable"),
        ));
    let mut child = command
        .spawn()
        .unwrap_or_else(|error| panic!("{label} should launch: {error}"));
    let deadline = Instant::now() + timeout;
    let status = loop {
        match child.try_wait() {
            Ok(Some(status)) => break status,
            Ok(None) => {}
            Err(error) => {
                let _ = child.kill();
                let _ = child.wait();
                panic!("{label} status should be readable: {error}");
            }
        }
        if Instant::now() >= deadline {
            let _ = child.kill();
            let _ = child.wait();
            let stdout = fs::read(&stdout_path).unwrap_or_default();
            let stderr = fs::read(&stderr_path).unwrap_or_default();
            panic!(
                "{label} exceeded {timeout:?}\nstdout:\n{}\nstderr:\n{}",
                String::from_utf8_lossy(&stdout),
                String::from_utf8_lossy(&stderr),
            );
        }
        thread::sleep(PROCESS_POLL_INTERVAL);
    };
    Output {
        status,
        stdout: fs::read(stdout_path).expect("process stdout should be readable"),
        stderr: fs::read(stderr_path).expect("process stderr should be readable"),
    }
}

fn fixture_from_source(
    source_path: &str,
    source: &str,
    project_name: &str,
    external_types: BTreeMap<String, String>,
) -> (KotlinProjectConfig, KotlinPlan) {
    let parsed = parse_project([SourceFile::new(source_path, source)])
        .expect("Kotlin semantics fixture should parse");
    let ir = render(&lower(Path::new("src"), parsed).expect("fixture should lower"))
        .expect("fixture should render canonical IR");
    let plan = KotlinPlan::from_ir(&ir).expect("fixture should project to Kotlin");
    let config = KotlinProjectConfig {
        project: ProjectMetadata {
            name: project_name.to_owned(),
            version: "1.0.0".to_owned(),
            source: "src".to_owned(),
        },
        kotlin: KotlinTarget {
            source: "kotlin".to_owned(),
            generated: "generated/kotlin".to_owned(),
            compiler: "kotlinc".to_owned(),
            java: "java".to_owned(),
            jvm_target: 17,
            runtime_validation: RuntimeValidation::Boundary,
            classpath: Vec::new(),
            compile_only: Vec::new(),
            implementations: BTreeMap::new(),
            external_types,
        },
        effects: BTreeMap::new(),
        generator: GeneratorConfig::default(),
        verification: VerificationConfig::default(),
    };
    (config, plan)
}

fn fixture() -> (KotlinProjectConfig, KotlinPlan) {
    fixture_from_source(
        "src/semantics.cott",
        CONTRACT,
        "semantics-regression",
        BTreeMap::new(),
    )
}

fn abi_fixture() -> (KotlinProjectConfig, KotlinPlan) {
    fixture_from_source(
        "src/abi.cott",
        ABI_CONTRACT,
        "abi-regression",
        BTreeMap::from([("abi.Moment".to_owned(), "java.time.Instant".to_owned())]),
    )
}

fn abi_consumer() -> String {
    let hash = sha256_hex(ABI_OPAQUE_TAG.as_bytes());
    ABI_CONSUMER.replace(
        "__COTT_OPAQUE_MARKER__",
        &format!("CottOpaque_{}", &hash[..24]),
    )
}

fn implementation_body(callable: &KotlinCallable) -> &'static str {
    match callable.symbol.as_str() {
        "semantics.increment" => "return value + 1",
        "semantics.echo" | "semantics.echo_shared" => "return node",
        "semantics.retain"
        | "semantics.CombinedState.inherited"
        | "semantics.CombinedState.child"
        | "semantics.CombinedState.secondary"
        | "semantics.CombinedState.combined" => "return value",
        "abi.ReaderState.read" => "return 37",
        "abi.echo_bundle" => "return value",
        symbol => panic!("unexpected callable in Kotlin fixture: {symbol}"),
    }
}

fn binding(
    plan: &KotlinPlan,
    config: &KotlinProjectConfig,
    callable: KotlinCallable,
) -> KotlinBinding {
    let mut package = format!("cott_impl.{}", callable.module);
    let mut relative = PathBuf::from("kotlin/cott_impl");
    for segment in callable.module.split('.') {
        relative.push(segment);
    }
    if let Some(owner) = &callable.owner {
        let concrete = owner["name"]
            .as_str()
            .expect("implementation owner should have a name")
            .rsplit('.')
            .next()
            .expect("implementation owner should have a local name");
        package.push('.');
        package.push_str(concrete);
        relative.push(concrete);
    }
    let signature = implementation_signature(plan, &callable)
        .expect("canonical implementation signature should render");
    let source = format!(
        "package {package}\n\n{signature} {{\n    {}\n}}\n",
        implementation_body(&callable)
    );
    validate_candidate(config, plan, &callable, source.as_bytes())
        .expect("fixture implementation should satisfy the binding audit");
    relative.push(format!("{}.kt", callable.name));
    let target_symbol = format!("{package}.{}", callable.name);
    KotlinBinding {
        cott_symbol: callable.symbol,
        target_symbol,
        source_origin: relative.clone(),
        runtime_origin: relative,
        content_hash: format!("sha256:{}", sha256_hex(source.as_bytes())),
        bytes: source.into_bytes(),
        owner: KotlinOwner::Agent,
    }
}

fn compile_and_run_fixture(
    config: KotlinProjectConfig,
    plan: KotlinPlan,
    consumer_source: &str,
    expected_callables: usize,
) {
    let toolchain = KotlinToolchain::from_required_environment();
    let temp = TempDir::new();
    let source_root = temp.path.join("emitted");
    fs::create_dir(&source_root).expect("emitted source root should be writable");

    let callables = plan.callables();
    assert_eq!(
        callables.len(),
        expected_callables,
        "fixture callable projection changed"
    );
    let bindings = callables
        .into_iter()
        .map(|callable| binding(&plan, &config, callable))
        .collect::<Vec<_>>();
    let emission = emit(&config, &plan, &bindings).expect("canonical fixture should emit");
    assert!(emission.unresolved.is_empty());

    let mut library_sources = Vec::new();
    for (relative, bytes) in emission.files {
        if relative
            .extension()
            .is_none_or(|extension| extension != "kt")
        {
            continue;
        }
        let destination = source_root.join(relative);
        fs::create_dir_all(
            destination
                .parent()
                .expect("emitted Kotlin path should have a parent"),
        )
        .expect("emitted Kotlin directory should be writable");
        fs::write(&destination, bytes).expect("emitted Kotlin source should be writable");
        library_sources.push(destination);
    }
    assert!(
        !library_sources.is_empty(),
        "emit must produce Kotlin sources"
    );

    let library = temp.path.join("semantics-library.jar");
    let compiler_classpath = classpath(&[&toolchain.stdlib, &toolchain.coroutines]);
    let mut library_compiler = Command::new(&toolchain.kotlinc);
    library_compiler
        .args(&library_sources)
        .arg("-no-stdlib")
        .arg("-classpath")
        .arg(&compiler_classpath)
        .args(["-jvm-target", "17", "-module-name", LIBRARY_MODULE, "-d"])
        .arg(&library)
        .current_dir(&temp.path)
        .env("JAVA_HOME", &toolchain.java_home);
    let output = bounded_output(
        "library-compile",
        &mut library_compiler,
        &temp.path,
        COMPILER_TIMEOUT,
    );
    assert_command_succeeded("emitted Kotlin library compilation", output);

    let driver = temp.path.join("NativeSemantics.kt");
    fs::write(&driver, consumer_source).expect("Kotlin semantics consumer should be writable");
    let consumer = temp.path.join("semantics-consumer.jar");
    let consumer_classpath = classpath(&[&library, &toolchain.stdlib, &toolchain.coroutines]);
    let mut consumer_compiler = Command::new(&toolchain.kotlinc);
    consumer_compiler
        .arg(&driver)
        .arg("-no-stdlib")
        .arg("-classpath")
        .arg(&consumer_classpath)
        .args(["-jvm-target", "17", "-module-name", CONSUMER_MODULE, "-d"])
        .arg(&consumer)
        .current_dir(&temp.path)
        .env("JAVA_HOME", &toolchain.java_home);
    let output = bounded_output(
        "consumer-compile",
        &mut consumer_compiler,
        &temp.path,
        COMPILER_TIMEOUT,
    );
    assert_command_succeeded("Kotlin consumer compilation", output);

    let runtime_classpath = classpath(&[
        &consumer,
        &library,
        &toolchain.stdlib,
        &toolchain.coroutines,
    ]);
    let mut runner = Command::new(&toolchain.java);
    runner
        .args(["-ea", "-cp"])
        .arg(runtime_classpath)
        .arg(DRIVER_MAIN_CLASS)
        .current_dir(&temp.path);
    let output = bounded_output("consumer-run", &mut runner, &temp.path, CONSUMER_TIMEOUT);
    assert_command_succeeded("Kotlin semantics consumer", output);
}

fn compile_and_run_emission() {
    let (config, plan) = fixture();
    compile_and_run_fixture(config, plan, CONSUMER, 8);
}

#[test]
#[ignore = "requires COTT_KOTLIN_HOME with Kotlin 2.2.10 and JAVA_HOME with JDK 17"]
fn emitted_kotlin_preserves_generic_recursive_and_associated_semantics() {
    compile_and_run_emission();
}

#[test]
#[ignore = "requires COTT_KOTLIN_HOME with Kotlin 2.2.10 and JAVA_HOME with JDK 17"]
fn emitted_kotlin_exposes_public_value_and_wrapper_abi_to_a_separate_consumer() {
    let (config, plan) = abi_fixture();
    let consumer = abi_consumer();
    compile_and_run_fixture(config, plan, &consumer, 2);
}
