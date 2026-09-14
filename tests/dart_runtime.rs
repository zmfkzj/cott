use std::fs::{self, File};
use std::io;
use std::path::{Path, PathBuf};
use std::process::{Command, Output, Stdio};
use std::sync::atomic::{AtomicU64, Ordering};
use std::thread;
use std::time::{Duration, Instant};

use cott::dart::runtime::render_runtime;

static NEXT_TEMP_DIR: AtomicU64 = AtomicU64::new(0);

const PROCESS_POLL_INTERVAL: Duration = Duration::from_millis(20);
const DART_RUNTIME_TIMEOUT: Duration = Duration::from_secs(20);

struct TempDir {
    path: PathBuf,
}

impl TempDir {
    fn new() -> Self {
        let mut number = NEXT_TEMP_DIR.fetch_add(1, Ordering::Relaxed);
        loop {
            let path = std::env::temp_dir()
                .join(format!("cott-dart-runtime-{}-{number}", std::process::id()));
            match fs::create_dir(&path) {
                Ok(()) => return Self { path },
                Err(error) if error.kind() == io::ErrorKind::AlreadyExists => number += 1,
                Err(error) => panic!(
                    "failed to create Dart runtime fixture {}: {error}",
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

fn run_dart(driver_source: &str) {
    let dart = PathBuf::from(
        std::env::var_os("COTT_DART")
            .expect("COTT_DART must be the absolute path to the pinned Dart executable"),
    );
    assert!(dart.is_absolute(), "COTT_DART must be absolute");
    assert!(dart.is_file(), "COTT_DART must name an executable file");

    let temp = TempDir::new();
    let home = temp.path.join("home");
    let pub_cache = temp.path.join("pub-cache");
    fs::create_dir_all(&home).expect("isolated Dart HOME should be writable");
    fs::create_dir_all(&pub_cache).expect("isolated Dart pub cache should be writable");
    for (relative, bytes) in render_runtime("runtime_regression", "1.0.0") {
        let destination = temp.path.join(relative);
        fs::create_dir_all(
            destination
                .parent()
                .expect("rendered runtime path should have a parent"),
        )
        .expect("runtime output directory should be writable");
        fs::write(destination, bytes).expect("runtime output should be writable");
    }
    let package_root = temp.path.join("dart");
    let driver = package_root.join("bin/runtime_regression.dart");
    fs::create_dir_all(driver.parent().expect("driver should have a parent"))
        .expect("driver directory should be writable");
    fs::write(&driver, driver_source).expect("Dart driver should be writable");

    let mut command = Command::new(dart);
    command
        .arg("run")
        .arg(&driver)
        .current_dir(&package_root)
        .env_clear()
        .env("HOME", home)
        .env("PUB_CACHE", pub_cache);
    let output = bounded_output(
        "dart-runtime-regression",
        &mut command,
        &temp.path,
        DART_RUNTIME_TIMEOUT,
    );
    assert_command_succeeded("Dart runtime regression", output);
}

const PRELUDE: &str = r#"
import 'dart:async';
import '../lib/cott_runtime.dart';

Never fail(String message) => throw StateError(message);
void expect(bool condition, String message) {
  if (!condition) fail(message);
}
void expectViolation(void Function() body, String message) {
  try {
    body();
  } on CottContractViolation {
    return;
  }
  fail(message);
}
void expectUnsupported(void Function() body, String message) {
  try {
    body();
  } on UnsupportedError {
    return;
  }
  fail(message);
}
Future<void> expectAsyncViolation(Future<void> Function() body, String message) async {
  try {
    await body();
  } on CottContractViolation {
    return;
  }
  fail(message);
}
Future<void> expectCancellation(Future<void> Function() body, String message) async {
  try {
    await body();
  } on CottCancellationException {
    return;
  }
  fail(message);
}
"#;

#[test]
#[ignore = "requires COTT_DART=/tmp/cott-dart-toolchain/dart-sdk/bin/dart"]
fn dart_runtime_preserves_numeric_unicode_and_tagged_json_contracts() {
    run_dart(&format!(
        r#"{PRELUDE}
void main() {{
  expect(CottRuntime.intAdd(BigInt.parse('18446744073709551615'), BigInt.one) ==
      BigInt.parse('18446744073709551616'), 'integer math was not exact');
  expect(CottRuntime.intValue(BigInt.parse('-9223372036854775808'), CottIntKind.i64)
      is BigInt, 'I64 was not represented by BigInt');
  expect(CottRuntime.intValue(BigInt.parse('4294967295'), CottIntKind.u32) ==
      4294967295, 'U32 upper bound was rejected');
  expectViolation(
    () => CottRuntime.intValue(BigInt.parse('4294967296'), CottIntKind.u32),
    'U32 overflow was accepted',
  );
  expect(CottRuntime.euclideanRemainder(-5, 3) == BigInt.one,
      'Euclidean remainder was negative');
  expect(CottRuntime.euclideanDivide(-5, 3) == BigInt.from(-2),
      'Euclidean division was inconsistent');
  expect(CottRuntime.f32FromBits('3f800000') == 1.0,
      'F32 bit literal lost its value');
  expect(CottRuntime.f64FromBits('3ff0000000000000') == 1.0,
      'F64 bit literal lost its value');
  expect(CottRuntime.normalizeF32(1.00000006) == 1.0000001192092896,
      'F32 did not round through IEEE binary32');
  expectViolation(() => CottRuntime.validateF64(double.infinity),
      'non-finite F64 was accepted');
  expectViolation(() => CottRuntime.f32FromBits('7f800000'),
      'non-finite F32 bits were accepted');
  expectViolation(
    () => CottRuntime.validateUnicode(String.fromCharCode(0xd800)),
    'unpaired UTF-16 surrogate was accepted',
  );
  expect(CottRuntime.length('A😀') == BigInt.two,
      'string length did not count Unicode scalars');

  final tagged = JsonObject({{
    'integer': JsonInteger(BigInt.parse('9007199254740993')),
    'float': JsonFloat(1.0),
  }});
  final decoded = CottRuntime.decodeTaggedJson(CottRuntime.encodeTaggedJson(tagged));
  expect(decoded is JsonObject, 'tagged JSON object did not round-trip');
  final values = (decoded as JsonObject).value;
  expect(values['integer'] is JsonInteger && values['float'] is JsonFloat,
      'JSON integer and float tags collapsed');
}}
"#
    ));
}

#[test]
#[ignore = "requires COTT_DART=/tmp/cott-dart-toolchain/dart-sdk/bin/dart"]
fn dart_runtime_preserves_graph_sharing_and_immutable_values() {
    run_dart(&format!(
        r#"{PRELUDE}
final class N2 implements CottConst {{
  const N2();
  @override
  BigInt get value => BigInt.two;
}}

class Animal {{}}
final class Dog extends Animal {{}}
final class TraitValue implements CottTraitCarrier {{
  TraitValue(this.cottTraits);
  @override
  final CottSet<CottTrait<dynamic>> cottTraits;
}}
final Object _boxSeal = Object();

final class BoxCarrier implements CottNominalCarrier {{
  BoxCarrier(this.witness);
  final CottType<Object?> witness;
  @override
  String get cottGenericIdentity => 'Box';
  @override
  CottList<CottType<Object?>> get cottTypeArguments => CottList([witness]);
  @override
  String get cottTypeIdentity => 'Box';
  @override
  CottList<String> get cottFieldNames => CottList(const []);
  @override
  Object? cottField(String name) =>
      CottRuntime.violation('Box carrier has no fields', phase: 'field');
  @override
  CottNominalCarrier cottRebuildCarrier(CottList<Object?> fields) {{
    expect(fields.isEmpty, 'fieldless carrier received rebuilt fields');
    return this;
  }}
}}

final class BoxView<T> implements CottCheckedView {{
  BoxView._(this._carrier, this.witness);
  final BoxCarrier _carrier;
  final CottType<T> witness;
  @override
  String get cottGenericIdentity => 'Box';
  @override
  CottList<CottType<Object?>> get cottTypeArguments =>
      CottList([witness as CottType<Object?>]);
  @override
  String get cottTypeIdentity => 'Box';
  @override
  CottList<String> get cottFieldNames => CottList(const []);
  @override
  Object? cottField(String name) =>
      CottRuntime.violation('Box view has no fields', phase: 'field');
  @override
  CottNominalCarrier cottCarrier(CottViewAccess access) {{
    if (!access.allows(_boxSeal)) {{
      return CottRuntime.violation('invalid Box view access', phase: 'validation');
    }}
    return _carrier;
  }}
}}

CottType<BoxView<T>> boxDescriptor<T>(
  CottType<T> argument,
  CottVariance variance,
) => CottTypes.checkedNominal<BoxView<T>>(
  'Box',
  const [],
  (carrier) => carrier is BoxCarrier,
  (carrier, arguments) => BoxView<T>._(
    carrier as BoxCarrier,
    arguments[0] as CottType<T>,
  ),
  acceptsView: (value) => value is BoxView<dynamic>,
  viewSeal: _boxSeal,
  arguments: [argument as CottType<Object?>],
  variances: [variance],
);

void main() {{
  final shared = <Object?>[1, 2];
  final graph = <Object?>[shared, shared];
  final snapshot = CottRuntime.deepSnapshot(graph) as List<Object?>;
  expect(identical(snapshot[0], snapshot[1]),
      'deep snapshot did not preserve shared DAG identity');
  shared[0] = 9;
  expect((snapshot[0] as List<Object?>)[0] == 1,
      'deep snapshot retained mutable source storage');

  final cycle = <Object?>[];
  cycle.add(cycle);
  expectViolation(() => CottRuntime.deepSnapshot(cycle),
      'active snapshot cycle was accepted');
  final otherCycle = <Object?>[];
  otherCycle.add(otherCycle);
  expectViolation(() => CottRuntime.deepEqual(cycle, otherCycle),
      'active equality cycle was accepted');

  final list = CottList<int>([1, 2]);
  final set = CottSet<Object?>([1, BigInt.one, 2]);
  final map = CottMap<String, int>([
    const CottMapEntry('a', 1),
    const CottMapEntry('b', 2),
  ]);
  final array = CottArray<int, N2>([3, 4], const N2());
  final buffer = CottBuffer.fromHex('00ff', const N2());
  expect(set.length == 2, 'canonical integer duplicates survived in CottSet');
  expect(map['b'] == 2 && array[1] == 4 && buffer[1] == 255,
      'immutable container contents changed');
  expectUnsupported(() => list[0] = 4, 'CottList mutation succeeded');
  expectUnsupported(() => map['a'] = 3, 'CottMap mutation succeeded');
  expect(CottRuntime.deepEqual(CottList([array]), CottList([array])),
      'immutable value graph did not compare canonically');

  final animal = CottTypes.external<Animal>('Animal', (value) => value is Animal);
  final dog = CottTypes.external<Dog>(
    'Dog',
    (value) => value is Dog,
    supertypes: [animal as CottType<Object?>],
  );
  expect(
    dog.satisfiesNominal('Dog') &&
        dog.satisfiesNominal('Animal') &&
        !animal.satisfiesNominal('Dog'),
    'nominal satisfaction did not follow exact transitive descriptor supertypes',
  );
  final deferredDog = CottTypes.deferred<Dog>('DeferredDog', () => dog);
  expect(deferredDog.satisfiesNominal('Animal'),
      'deferred descriptor did not resolve nominal satisfaction');
  late CottType<int> cyclicDescriptor;
  cyclicDescriptor = CottTypes.deferred<int>('Cycle', () => cyclicDescriptor);
  expectViolation(
    () => CottRuntime.abi(1, cyclicDescriptor),
    'cyclic descriptor providers must fail instead of recursing indefinitely',
  );
  final dogView = BoxView<Dog>._(
    BoxCarrier(dog as CottType<Object?>),
    dog,
  );
  final covariantBox = boxDescriptor<Animal>(
    animal,
    CottVariance.covariant,
  );
  final covariantView = CottRuntime.abi(dogView, covariantBox);
  expect(!identical(covariantView, dogView) &&
      identical(covariantView.cottTypeArguments[0], animal),
      'covariant carrier was not rebuilt as an expected typed view');
  final invariantBox = boxDescriptor<Animal>(
    animal,
    CottVariance.invariant,
  );
  expectViolation(() => CottRuntime.abi(dogView, invariantBox),
      'Dart covariance bypassed invariant Cott witness checking');
  final animalView = BoxView<Animal>._(
    BoxCarrier(animal as CottType<Object?>),
    animal,
  );
  final contravariantBox = boxDescriptor<Dog>(
    dog,
    CottVariance.contravariant,
  );
  final contravariantView =
      CottRuntime.abi(animalView, contravariantBox);
  expect(!identical(contravariantView, animalView) &&
      identical(contravariantView.cottTypeArguments[0], dog),
      'Cott-valid contravariance did not produce a new typed view');

  late final CottTrait<TraitValue> trait;
  trait = CottTrait<TraitValue>.checked(
    'TraitValue',
    (value) => value is TraitValue,
  );
  final traitValue = TraitValue(
    CottSet<CottTrait<dynamic>>([trait]),
  );
  expect(identical(Dyn.of(traitValue, trait).value, traitValue),
      'typed Dyn factory did not preserve its generated trait carrier');
  final factory = CottFactory<Animal>.zero(Animal, Animal.new);
  expect(factory.construct(
        CottList<Object?>(const []),
        CottMap<String, Object?>(const []),
      ) is Animal,
      'typed zero-argument factory did not construct its value');
  expectViolation(
    () => factory.construct(
      CottList<Object?>([1]),
      CottMap<String, Object?>(const []),
    ),
    'zero-argument factory accepted positional arguments',
  );
}}
"#
    ));
}

#[test]
#[ignore = "requires COTT_DART=/tmp/cott-dart-toolchain/dart-sdk/bin/dart"]
fn dart_runtime_enforces_state_and_generator_lifecycle() {
    run_dart(&format!(
        r#"{PRELUDE}

void main() {{
  Object state = 0;
  final contract = CottResourceContract(
    symbol: 'counter.advance',
    fields: [
      CottStateField(
        name: 'state',
        type: CottTypes.i32,
        read: () => state,
        write: (value) => state = value!,
      ),
    ],
    modifies: const [],
    transitions: const [CottTransition(field: 'state', from: 0, to: 1)],
    invariants: [CottInvariant(clause: 'state-valid', check: () => state == 0 || state == 1)],
  );
  contract.validateInitial();
  late CottStateMutation escaped;
  final result = contract.enforceMutation<int, int>(
    (_) {{}},
    (mutation, lease) {{
      expect(identical(mutation.compilerLease, lease), 'mutation lease witness changed');
      mutation.write('state', 1);
      return 7;
    }},
    (value, mutation) {{
      escaped = mutation;
      return value + 1;
    }},
  );
  expect(result == 8 && state == 1, 'resource mutation did not commit');
  expectViolation(() => escaped.read('state'), 'revoked mutation capability remained usable');

  final source = CottGeneratorSource<int, int, String>.callbacks(
    start: () => const CottGeneratorYield(1),
    next: () => const CottGeneratorYield(2),
    send: (value) => CottGeneratorReturn('$value'),
    raise: (error, stackTrace) => CottGeneratorReturn(error.toString()),
    close: () {{}},
  );
  final generator = CottRuntime.wrapGenerator(
    source,
    CottTypes.i32,
    CottTypes.i32,
    CottTypes.string,
  );
  final first = generator.nextStep();
  expect(first is CottGeneratorYield<int, String> && first.value == 1,
      'generator start did not yield');
  final returned = generator.send(9);
  expect(returned is CottGeneratorReturn<int, String> && returned.value == '9',
      'generator return value was lost');
  expect(generator.returnValue == const Some<String>('9'),
      'generator completion was not retained');
  expectViolation(() => generator.send(10), 'send after return succeeded');
}}
"#
    ));
}

#[test]
#[ignore = "requires COTT_DART=/tmp/cott-dart-toolchain/dart-sdk/bin/dart"]
fn dart_runtime_async_cancellation_and_guard_ownership_are_honest() {
    run_dart(&format!(
        r#"{PRELUDE}

Future<void> main() async {{
  final source = CottAsyncGeneratorSource<int, int, String>.callbacks(
    start: (cancellation) async => const CottGeneratorYield(1),
    next: (cancellation) async => const CottGeneratorYield(2),
    send: (value, cancellation) async => CottGeneratorReturn('$value'),
    raise: (error, stackTrace, cancellation) async =>
        CottGeneratorReturn(error.toString()),
    close: (cancellation) async {{}},
  );
  final generator = CottRuntime.wrapAsyncGenerator(
    source,
    CottTypes.i32,
    CottTypes.i32,
    CottTypes.string,
  );
  await expectAsyncViolation(
    () async {{ await generator.send(3); }},
    'async generator accepted send before start',
  );
  final yielded = await generator.start();
  expect(yielded is CottGeneratorYield<int, String> && yielded.value == 1,
      'async generator start did not yield');
  final returned = await generator.send(4);
  expect(returned is CottGeneratorReturn<int, String> && returned.value == '4',
      'async generator return value was lost');
  expect(generator.returnValue == const Some<String>('4'),
      'async generator completion was not retained');
  await expectAsyncViolation(
    () async {{ await generator.send(5); }},
    'async generator accepted send after return',
  );

  final guard = CottResourceGuard();
  final acquired = Completer<void>();
  final release = Completer<void>();
  late CottGuardLease outerLease;
  final outer = guard.runExclusive<void>((lease) async {{
    outerLease = lease;
    acquired.complete();
    await release.future;
  }});
  await acquired.future;

  var inheritedZoneEntered = false;
  final child = runZoned(
    () => guard.runExclusive<void>((_) {{ inheritedZoneEntered = true; }}),
  );
  await Future<void>.delayed(Duration.zero);
  expect(!inheritedZoneEntered,
      'a child Zone inherited false reentrant guard ownership');

  final cancellation = CottCancellationSource();
  var cancelledWaiterEntered = false;
  final cancelledWaiter = guard.runExclusive<void>(
    (_) {{ cancelledWaiterEntered = true; }},
    cancellation: cancellation.token,
  );
  cancellation.cancel('fixture cancellation');
  await expectCancellation(() => cancelledWaiter,
      'cancelled queued waiter did not report cooperative cancellation');
  expect(!cancelledWaiterEntered, 'cancelled queued waiter entered the guard');

  final otherGuard = CottResourceGuard();
  expectViolation(
    () => otherGuard.withLease(outerLease, () {{}}),
    'cross-guard lease was accepted',
  );
  release.complete();
  await outer;
  await child;
  expect(inheritedZoneEntered, 'queued child never entered after release');
  expectViolation(
    () => guard.withLease(outerLease, () {{}}),
    'revoked lease remained usable',
  );

  final unrelated = Completer<void>();
  final signal = CottCancellationSource();
  signal.cancel();
  expect(!unrelated.isCompleted,
      'cooperative cancellation falsely completed an arbitrary Future');
  unrelated.complete();
  await unrelated.future;

  final scope = CottTaskScope();
  final observed = Completer<void>();
  final task = scope.spawn<void>((token) async {{
    await token.whenCancelled;
    observed.complete();
    token.throwIfCancelled();
  }});
  scope.cancel('scope shutdown');
  await expectCancellation(() => task.result,
      'structured child did not observe scope cancellation');
  await observed.future;
  await expectCancellation(scope.join,
      'scope join hid the owned child cancellation');
}}
"#
    ));
}

#[test]
fn dart_runtime_renderer_uses_artifact_relative_package_layout() {
    let files = render_runtime("sample_package", "2.3.4");
    assert_eq!(files.len(), 1);
    let path = Path::new("dart/lib/cott_runtime.dart");
    let source = String::from_utf8(
        files
            .get(path)
            .expect("runtime renderer should emit the public package library")
            .clone(),
    )
    .expect("Dart runtime should be UTF-8");
    assert!(source.contains("const String cottProjectName = 'sample_package';"));
    assert!(source.contains("const String cottProjectVersion = '2.3.4';"));
    assert!(!source.contains("__COTT_"));
}
