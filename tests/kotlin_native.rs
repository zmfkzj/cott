use std::ffi::OsString;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::sync::atomic::{AtomicU64, Ordering};

use cott::kotlin::runtime::render_runtime;

const MODULE_NAME: &str = "cott_native_regression";
const DRIVER_FILE: &str = "NativeRegression.kt";
const DRIVER_MAIN_CLASS: &str = "cott_native_regression.NativeRegressionKt";

static NEXT_TEMP_DIR: AtomicU64 = AtomicU64::new(0);

struct TempDir {
    path: PathBuf,
}

impl TempDir {
    fn new() -> Self {
        let mut number = NEXT_TEMP_DIR.fetch_add(1, Ordering::Relaxed);
        loop {
            let path = std::env::temp_dir().join(format!(
                "cott-kotlin-native-{}-{number}",
                std::process::id()
            ));
            match fs::create_dir(&path) {
                Ok(()) => return Self { path },
                Err(error) if error.kind() == io::ErrorKind::AlreadyExists => number += 1,
                Err(error) => panic!(
                    "failed to create Kotlin native fixture {}: {error}",
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

fn compile_and_run(driver_source: &str) {
    let toolchain = KotlinToolchain::from_required_environment();
    let temp = TempDir::new();
    let source_root = temp.path.join("src");
    let classes = temp.path.join("classes");
    fs::create_dir_all(&source_root).expect("Kotlin source root should be writable");
    fs::create_dir(&classes).expect("Kotlin class output should be writable");

    let mut source_files = Vec::new();
    for (relative_path, bytes) in render_runtime("native-regression", "1.0.0") {
        let destination = source_root.join(relative_path);
        fs::create_dir_all(
            destination
                .parent()
                .expect("rendered Kotlin runtime path should have a parent"),
        )
        .expect("rendered Kotlin runtime directory should be writable");
        fs::write(&destination, bytes).expect("rendered Kotlin runtime should be writable");
        if destination
            .extension()
            .is_some_and(|extension| extension == "kt")
        {
            source_files.push(destination);
        }
    }
    assert!(
        !source_files.is_empty(),
        "render_runtime must produce Kotlin sources"
    );

    let driver = source_root.join(DRIVER_FILE);
    fs::write(&driver, driver_source).expect("Kotlin regression driver should be writable");
    source_files.push(driver);

    let compile_classpath = classpath(&[&toolchain.stdlib, &toolchain.coroutines]);
    let mut compiler = Command::new(&toolchain.kotlinc);
    compiler
        .args(&source_files)
        .arg("-no-stdlib")
        .arg("-classpath")
        .arg(&compile_classpath)
        .args(["-jvm-target", "17", "-module-name", MODULE_NAME, "-d"])
        .arg(&classes)
        .current_dir(&temp.path)
        .env("JAVA_HOME", &toolchain.java_home);
    let compile_output = compiler
        .output()
        .expect("configured Kotlin compiler should launch");
    assert_command_succeeded("Kotlin runtime compilation", compile_output);

    let runtime_classpath = classpath(&[
        classes.as_path(),
        toolchain.stdlib.as_path(),
        toolchain.coroutines.as_path(),
    ]);
    let run_output = Command::new(&toolchain.java)
        .args(["-ea", "-cp"])
        .arg(runtime_classpath)
        .arg(DRIVER_MAIN_CLASS)
        .current_dir(&temp.path)
        .output()
        .expect("configured Java runtime should launch");
    assert_command_succeeded("Kotlin runtime regression driver", run_output);
}

#[test]
#[ignore = "requires COTT_KOTLIN_HOME with Kotlin 2.2.10 and JAVA_HOME with JDK 17"]
fn canceled_queued_kotlin_lock_waiters_finish_without_entering() {
    compile_and_run(
        r#"
package cott_native_regression

import cott_runtime.CottResourceGuard
import cott_runtime.CottSuspendLock
import java.util.concurrent.atomic.AtomicBoolean
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.TimeoutCancellationException
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout

private interface CriticalSection {
    suspend fun <T> withLock(block: suspend () -> T): T
}

private class ResourceCriticalSection : CriticalSection {
    private val guard = CottResourceGuard()

    override suspend fun <T> withLock(block: suspend () -> T): T =
        guard.withLockSuspend(block)
}

private class SuspendCriticalSection : CriticalSection {
    private val lock = CottSuspendLock()

    override suspend fun <T> withLock(block: suspend () -> T): T =
        lock.withLock(block)
}

private suspend fun exerciseQueuedCancellation(
    name: String,
    critical: CriticalSection,
): Unit = coroutineScope {
    val ownerEntered = CompletableDeferred<Unit>()
    val releaseOwner = CompletableDeferred<Unit>()
    val canceledBodyRan = AtomicBoolean(false)
    val nextEntered = CompletableDeferred<Unit>()

    val owner = launch(start = CoroutineStart.UNDISPATCHED) {
        critical.withLock {
            ownerEntered.complete(Unit)
            releaseOwner.await()
        }
    }
    withTimeout(2_000) { ownerEntered.await() }

    val canceled = launch(start = CoroutineStart.UNDISPATCHED) {
        critical.withLock {
            canceledBodyRan.set(true)
        }
    }
    canceled.cancel()
    val canceledWhileOwnerHeld = try {
        withTimeout(1_000) { canceled.join() }
        true
    } catch (_: TimeoutCancellationException) {
        false
    }

    val next = launch(start = CoroutineStart.UNDISPATCHED) {
        critical.withLock {
            nextEntered.complete(Unit)
        }
    }
    val nextBypassedOwner = nextEntered.isCompleted

    releaseOwner.complete(Unit)
    withTimeout(5_000) {
        owner.join()
        canceled.join()
        nextEntered.await()
        next.join()
    }

    check(canceledWhileOwnerHeld) {
        "$name canceled waiter did not finish while the owner still held the lock"
    }
    check(!canceledBodyRan.get()) {
        "$name executed a canceled waiter's guarded body after cancellation"
    }
    check(!nextBypassedOwner) {
        "$name allowed the next waiter to bypass the current owner"
    }

    withTimeout(2_000) {
        critical.withLock { Unit }
    }
}

fun main(): Unit = runBlocking {
    withTimeout(15_000) {
        exerciseQueuedCancellation("CottResourceGuard", ResourceCriticalSection())
        exerciseQueuedCancellation("CottSuspendLock", SuspendCriticalSection())
    }
}
"#,
    );
}

#[test]
#[ignore = "requires COTT_KOTLIN_HOME with Kotlin 2.2.10 and JAVA_HOME with JDK 17"]
fn kotlin_locks_reenter_across_dispatchers_without_granting_child_ownership() {
    compile_and_run(
        r#"
package cott_native_regression

import cott_runtime.CottResourceGuard
import cott_runtime.CottSuspendLock
import java.util.concurrent.Executors
import kotlin.coroutines.coroutineContext
import kotlinx.coroutines.CompletableDeferred
import kotlinx.coroutines.CoroutineDispatcher
import kotlinx.coroutines.CoroutineScope
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.Job
import kotlinx.coroutines.asCoroutineDispatcher
import kotlinx.coroutines.coroutineScope
import kotlinx.coroutines.launch
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withContext
import kotlinx.coroutines.withTimeout

private interface CriticalSection {
    suspend fun <T> withLock(block: suspend () -> T): T
}

private class ResourceCriticalSection : CriticalSection {
    private val guard = CottResourceGuard()

    override suspend fun <T> withLock(block: suspend () -> T): T =
        guard.withLockSuspend(block)
}

private class SuspendCriticalSection : CriticalSection {
    private val lock = CottSuspendLock()

    override suspend fun <T> withLock(block: suspend () -> T): T =
        lock.withLock(block)
}

private suspend fun exerciseOwnershipBoundary(
    name: String,
    critical: CriticalSection,
    switchedDispatcher: CoroutineDispatcher,
): Unit = coroutineScope {
    val nestedEntered = CompletableDeferred<Unit>()
    val childAttempting = CompletableDeferred<Unit>()
    val childEntered = CompletableDeferred<Unit>()
    val childBypassedOwner = CompletableDeferred<Boolean>()
    lateinit var child: Job

    val owner = launch(start = CoroutineStart.UNDISPATCHED) {
        critical.withLock {
            withContext(switchedDispatcher) {
                critical.withLock {
                    nestedEntered.complete(Unit)
                }
            }

            child = CoroutineScope(coroutineContext).launch(switchedDispatcher) {
                childAttempting.complete(Unit)
                critical.withLock {
                    childEntered.complete(Unit)
                }
            }

            withTimeout(2_000) {
                childAttempting.await()
                withContext(switchedDispatcher) { Unit }
            }
            childBypassedOwner.complete(childEntered.isCompleted)
        }
    }

    val bypassed = withTimeout(5_000) {
        nestedEntered.await()
        val result = childBypassedOwner.await()
        childEntered.await()
        child.join()
        owner.join()
        result
    }

    check(!bypassed) {
        "$name treated a newly launched child as the current lock owner"
    }
    withTimeout(2_000) {
        critical.withLock { Unit }
    }
}

fun main(): Unit = runBlocking {
    val executor = Executors.newSingleThreadExecutor { runnable ->
        Thread(runnable, "cott-native-regression-dispatcher").apply {
            isDaemon = true
        }
    }
    val switchedDispatcher = executor.asCoroutineDispatcher()
    try {
        withTimeout(15_000) {
            exerciseOwnershipBoundary(
                "CottResourceGuard",
                ResourceCriticalSection(),
                switchedDispatcher,
            )
            exerciseOwnershipBoundary(
                "CottSuspendLock",
                SuspendCriticalSection(),
                switchedDispatcher,
            )
        }
    } finally {
        switchedDispatcher.close()
    }
}
"#,
    );
}

#[test]
#[ignore = "requires COTT_KOTLIN_HOME with Kotlin 2.2.10 and JAVA_HOME with JDK 17"]
fn kotlin_runtime_preserves_value_and_protocol_semantics() {
    compile_and_run(
        r#"
package cott_native_regression

import cott_runtime.CottAsyncGenerator
import cott_runtime.CottAsyncGeneratorSource
import cott_runtime.CottContractViolation
import cott_runtime.CottGenerator
import cott_runtime.CottGeneratorSource
import cott_runtime.CottGeneratorStep
import cott_runtime.CottRuntime
import cott_runtime.CottTypes
import cott_runtime.Some
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.withTimeout

private fun expectContractViolation(label: String, operation: () -> Unit): Unit {
    try {
        operation()
    } catch (_: CottContractViolation) {
        return
    }
    error("$label did not raise CottContractViolation")
}

private suspend fun expectContractViolationSuspend(
    label: String,
    operation: suspend () -> Unit,
): Unit {
    try {
        operation()
    } catch (_: CottContractViolation) {
        return
    }
    error("$label did not raise CottContractViolation")
}

private fun expectNoSuchElement(label: String, operation: () -> Unit): Unit {
    try {
        operation()
    } catch (_: NoSuchElementException) {
        return
    }
    error("$label did not raise NoSuchElementException")
}

private class ScriptedGeneratorSource(
    private val startResult: CottGeneratorStep<Any?, Any?>,
    private val sendResult: CottGeneratorStep<Any?, Any?>,
    private val nextResult: CottGeneratorStep<Any?, Any?>,
) : CottGeneratorSource<Any?, Any?, Any?> {
    var starts: Int = 0
        private set
    var nexts: Int = 0
        private set
    var closes: Int = 0
        private set
    val sentValues: MutableList<Any?> = mutableListOf()

    override fun start(): CottGeneratorStep<Any?, Any?> {
        starts += 1
        return startResult
    }

    override fun send(value: Any?): CottGeneratorStep<Any?, Any?> {
        sentValues.add(value)
        return sendResult
    }

    override fun next(): CottGeneratorStep<Any?, Any?> {
        nexts += 1
        return nextResult
    }

    override fun raise(error: Throwable): CottGeneratorStep<Any?, Any?> = throw error

    override fun close(): Unit {
        closes += 1
    }
}

private class ScriptedAsyncGeneratorSource(
    private val startResult: CottGeneratorStep<Any?, Any?>,
    private val sendResult: CottGeneratorStep<Any?, Any?>,
    private val nextResult: CottGeneratorStep<Any?, Any?>,
) : CottAsyncGeneratorSource<Any?, Any?, Any?> {
    var starts: Int = 0
        private set
    var nexts: Int = 0
        private set
    var closes: Int = 0
        private set
    val sentValues: MutableList<Any?> = mutableListOf()

    override suspend fun start(): CottGeneratorStep<Any?, Any?> {
        starts += 1
        return startResult
    }

    override suspend fun send(value: Any?): CottGeneratorStep<Any?, Any?> {
        sentValues.add(value)
        return sendResult
    }

    override suspend fun next(): CottGeneratorStep<Any?, Any?> {
        nexts += 1
        return nextResult
    }

    override suspend fun raise(error: Throwable): CottGeneratorStep<Any?, Any?> = throw error

    override suspend fun close(): Unit {
        closes += 1
    }
}

@Suppress("UNCHECKED_CAST")
private fun wrapGenerator(
    source: ScriptedGeneratorSource,
): CottGenerator<String, Int, Boolean> = CottRuntime.wrapGenerator(
    source as CottGeneratorSource<String, Int, Boolean>,
    CottTypes.STRING,
    CottTypes.I32,
    CottTypes.BOOL,
)

@Suppress("UNCHECKED_CAST")
private fun wrapAsyncGenerator(
    source: ScriptedAsyncGeneratorSource,
): CottAsyncGenerator<String, Int, Boolean> = CottRuntime.wrapAsyncGenerator(
    source as CottAsyncGeneratorSource<String, Int, Boolean>,
    CottTypes.STRING,
    CottTypes.I32,
    CottTypes.BOOL,
)

private fun expectYield(
    label: String,
    step: CottGeneratorStep<String, Boolean>,
    expected: String,
): Unit {
    check(step is CottGeneratorStep.Yield && step.value == expected) {
        "$label did not yield $expected: $step"
    }
}

private fun expectReturn(
    label: String,
    step: CottGeneratorStep<String, Boolean>,
    expected: Boolean,
): Unit {
    check(step is CottGeneratorStep.Return && step.value == expected) {
        "$label did not return $expected: $step"
    }
}

private fun verifyNumericAndUnicodeSemantics(): Unit {
    check(
        CottRuntime.intAdd(ULong.MAX_VALUE, 1uL) ==
            CottRuntime.int("18446744073709551616")
    ) {
        "U64 arithmetic wrapped instead of preserving its mathematical value"
    }
    check(
        CottRuntime.euclideanRemainder(-5L, 3L) == CottRuntime.int("1")
    ) {
        "negative integer remainder was not Euclidean"
    }

    check(
        CottRuntime.length("A\uD83D\uDE00Z") == CottRuntime.int("3")
    ) {
        "String length counted UTF-16 code units instead of Unicode scalars"
    }
    expectContractViolation("lone UTF-16 surrogate") {
        CottRuntime.abi("\uD800", CottTypes.STRING)
    }

    expectContractViolation("non-finite F32") {
        CottRuntime.abi(Float.POSITIVE_INFINITY, CottTypes.F32)
    }
    expectContractViolation("non-finite F64") {
        CottRuntime.abi(Double.NaN, CottTypes.F64)
    }
}

private fun verifyImmutableSnapshots(): Unit {
    val byteInput = byteArrayOf(1, 2, 3)
    val byteSnapshot = CottRuntime.snapshotBytes(byteInput)
    byteInput[0] = 9
    check(byteSnapshot[0] == 1.toByte()) {
        "CottBytes retained its mutable input array"
    }
    val exportedBytes = byteSnapshot.toByteArray()
    exportedBytes[1] = 9
    check(byteSnapshot[1] == 2.toByte()) {
        "CottBytes exposed its mutable backing array"
    }

    val listInput = mutableListOf("first", "second")
    val listSnapshot = CottRuntime.snapshotList(listInput)
    listInput[0] = "changed"
    listInput.add("third")
    check(
        listSnapshot.size == 2 &&
            listSnapshot[0] == "first" &&
            listSnapshot[1] == "second"
    ) {
        "CottList changed with its mutable input"
    }

    val setInput = linkedSetOf("red", "blue")
    val setSnapshot = CottRuntime.snapshotSet(setInput)
    setInput.remove("red")
    setInput.add("green")
    check(
        setSnapshot.size == 2 &&
            setSnapshot.contains("red") &&
            setSnapshot.contains("blue") &&
            !setSnapshot.contains("green")
    ) {
        "CottSet changed with its mutable input"
    }

    val mapInput = linkedMapOf("answer" to 42)
    val mapSnapshot = CottRuntime.snapshotMap(mapInput)
    mapInput["answer"] = -1
    mapInput["extra"] = 1
    check(
        mapSnapshot.size == 1 &&
            mapSnapshot["answer"] == 42 &&
            !mapSnapshot.containsKey("extra")
    ) {
        "FrozenMap changed with its mutable input"
    }
}

@Suppress("UNCHECKED_CAST")
private fun verifyGeneratorSemantics(): Unit {
    val source = ScriptedGeneratorSource(
        CottGeneratorStep.Yield("sync-start"),
        CottGeneratorStep.Yield("sync-send"),
        CottGeneratorStep.Return(true),
    )
    val generator = wrapGenerator(source)
    expectYield("sync start", generator.nextStep(), "sync-start")

    val erasedSend = generator as CottGenerator<String, Any?, Boolean>
    expectContractViolation("sync typed send") {
        erasedSend.send("not-an-int")
    }
    check(source.sentValues.isEmpty()) {
        "sync generator forwarded an invalid sent value to its source"
    }

    expectYield("sync send", generator.send(7), "sync-send")
    check(source.sentValues == listOf(7)) {
        "sync generator did not forward the validated sent value"
    }
    expectReturn("sync completion", generator.nextStep(), true)
    check(generator.returnValue() == Some(true)) {
        "sync generator did not retain its typed completion value"
    }
    expectReturn("cached sync completion", generator.nextStep(), true)
    check(source.nexts == 1) {
        "completed sync generator re-entered its source"
    }
    expectContractViolation("sync send after completion") {
        generator.send(8)
    }
    check(source.sentValues == listOf(7)) {
        "completed sync generator re-entered send"
    }

    val invalidYield = wrapGenerator(
        ScriptedGeneratorSource(
            CottGeneratorStep.Yield(99),
            CottGeneratorStep.Return(true),
            CottGeneratorStep.Return(true),
        )
    )
    expectContractViolation("sync typed yield") {
        invalidYield.nextStep()
    }

    val invalidCompletion = wrapGenerator(
        ScriptedGeneratorSource(
            CottGeneratorStep.Return("not-a-boolean"),
            CottGeneratorStep.Return(true),
            CottGeneratorStep.Return(true),
        )
    )
    expectContractViolation("sync typed completion") {
        invalidCompletion.nextStep()
    }

    val closedSource = ScriptedGeneratorSource(
        CottGeneratorStep.Yield("unreachable"),
        CottGeneratorStep.Yield("unreachable"),
        CottGeneratorStep.Return(true),
    )
    val closed = wrapGenerator(closedSource)
    closed.close()
    check(closedSource.closes == 1) {
        "sync generator did not close its source exactly once"
    }
    expectNoSuchElement("sync next after close") {
        closed.nextStep()
    }
    expectContractViolation("sync send after close") {
        closed.send(1)
    }
    check(closedSource.starts == 0 && closedSource.sentValues.isEmpty()) {
        "closed sync generator re-entered its source"
    }
}

@Suppress("UNCHECKED_CAST")
private suspend fun verifyAsyncGeneratorSemantics(): Unit {
    val source = ScriptedAsyncGeneratorSource(
        CottGeneratorStep.Yield("async-start"),
        CottGeneratorStep.Yield("async-send"),
        CottGeneratorStep.Return(true),
    )
    val generator = wrapAsyncGenerator(source)
    expectYield("async start", generator.start(), "async-start")

    val erasedSend = generator as CottAsyncGenerator<String, Any?, Boolean>
    expectContractViolationSuspend("async typed send") {
        erasedSend.send("not-an-int")
    }
    check(source.sentValues.isEmpty()) {
        "async generator forwarded an invalid sent value to its source"
    }

    expectYield("async send", generator.send(11), "async-send")
    check(source.sentValues == listOf(11)) {
        "async generator did not forward the validated sent value"
    }
    expectReturn("async completion", generator.next(), true)
    check(generator.returnValue() == Some(true)) {
        "async generator did not retain its typed completion value"
    }
    expectReturn("cached async completion", generator.next(), true)
    check(source.nexts == 1) {
        "completed async generator re-entered its source"
    }
    expectContractViolationSuspend("async send after completion") {
        generator.send(12)
    }
    check(source.sentValues == listOf(11)) {
        "completed async generator re-entered send"
    }

    val invalidYield = wrapAsyncGenerator(
        ScriptedAsyncGeneratorSource(
            CottGeneratorStep.Yield(99),
            CottGeneratorStep.Return(true),
            CottGeneratorStep.Return(true),
        )
    )
    expectContractViolationSuspend("async typed yield") {
        invalidYield.start()
    }

    val invalidCompletion = wrapAsyncGenerator(
        ScriptedAsyncGeneratorSource(
            CottGeneratorStep.Return("not-a-boolean"),
            CottGeneratorStep.Return(true),
            CottGeneratorStep.Return(true),
        )
    )
    expectContractViolationSuspend("async typed completion") {
        invalidCompletion.start()
    }

    val closedSource = ScriptedAsyncGeneratorSource(
        CottGeneratorStep.Yield("unreachable"),
        CottGeneratorStep.Yield("unreachable"),
        CottGeneratorStep.Return(true),
    )
    val closed = wrapAsyncGenerator(closedSource)
    closed.close()
    check(closedSource.closes == 1) {
        "async generator did not close its source exactly once"
    }
    expectContractViolationSuspend("async next after close") {
        closed.next()
    }
    expectContractViolationSuspend("async send after close") {
        closed.send(1)
    }
    check(closedSource.starts == 0 && closedSource.sentValues.isEmpty()) {
        "closed async generator re-entered its source"
    }
}

fun main(): Unit = runBlocking {
    withTimeout(5_000) {
        verifyNumericAndUnicodeSemantics()
        verifyImmutableSnapshots()
        verifyGeneratorSemantics()
        verifyAsyncGeneratorSemantics()
    }
}
"#,
    );
}
