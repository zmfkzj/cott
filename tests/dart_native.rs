use std::collections::{BTreeMap, BTreeSet};
use std::env;
use std::fs::{self, File};
use std::io;
use std::path::{Path, PathBuf};
use std::process::{Command, Output, Stdio};
use std::sync::atomic::{AtomicU64, Ordering};
use std::thread;
use std::time::{Duration, Instant};

use cott::compiler::{SourceFile, parse_project};
use cott::dart::binding::validate_candidate;
use cott::dart::emit::{emit, implementation_signature};
use cott::dart::{DartBinding, DartCallable, DartOwner, DartPlan};
use cott::hash::sha256_hex;
use cott::hir::lower_with_effects;
use cott::ir::render;
use cott::manifest::{
    DartProjectConfig, DartTarget, GeneratorConfig, ProjectMetadata, RuntimeValidation,
    VerificationConfig,
};
use serde_json::{Value, json};

const PROCESS_POLL_INTERVAL: Duration = Duration::from_millis(20);
const COMPILER_TIMEOUT: Duration = Duration::from_secs(120);
const CONSUMER_TIMEOUT: Duration = Duration::from_secs(20);
const ABI_OPAQUE_TAG: &str = "dart-abi-secret";

const CONTRACT: &str = r#"module semantics

enum Choice[T]:
    Empty
    Value(value: T)

enum Consumer[-T]:
    Ready

struct GenericDefault[T]:
    value: Option[T] = Option.Nothing

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

impl ChildOnlyState for Child:
    type Item = I32
    fn inherited(self, value: I32) -> I32:
        ensures result == value
    fn child(self, value: I32) -> I32:
        ensures result == value

trait Associated:
    type Member: Child + Secondary
    fn member(self, value: Associated.Member) -> Associated.Member

impl AssociatedState for Associated + Child + Secondary:
    type Item = I32
    type Label = Str
    type Member = AssociatedState
    fn inherited(self, value: I32) -> I32:
        ensures result == value
    fn child(self, value: I32) -> I32:
        ensures result == value
    fn secondary(self, value: Str) -> Str:
        ensures result == value
    fn member(self, value: AssociatedState) -> AssociatedState:
        ensures result == value

enum MultiBound[T: Child + Secondary]:
    Empty

fn increment(value: I32) -> I32:
    effects [file.read, vendor.audit]
fn echo(node: Node) -> Node
fn echo_shared(node: SharedNode) -> SharedNode
fn retain[T: Combined](value: T) -> T
fn retain_both[T: Child + Secondary](value: T) -> T
fn retain_member[T: Associated](owner: T, member: T.Member) -> T.Member
"#;

const ABI_CONTRACT: &str = r#"module abi

alias Count = I32

newtype NonEmpty(Str)
    where self != ""

const DEFAULT_COUNT: I32 = 7
const DEFAULT_NON_EMPTY: NonEmpty = NonEmpty("ready")
const FIXED_VALUES: Array[U8, 2] = Array(1, 2)
const FIXED_BYTES: Buffer[2] = Buffer("00ff")

external type Moment

alias Secret = Opaque["dart-abi-secret"]

trait Reader:
    fn read(self) -> I32

impl ReaderState for Reader:
    fn read(self) -> I32:
        ensures result == 37

alias ReaderFactory = Factory[ReaderState]
alias DynamicReader = Dyn[Reader]

struct Defaulted:
    wide: I64 = 9223372036854775807
    label: NonEmpty = NonEmpty("ready")
    values: Array[U8, 2] = Array(1, 2)
    bytes: Buffer[2] = Buffer("00ff")
    anything: Any

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

const SEMANTICS_CONSUMER: &str = r#"import 'package:dart_semantics/cott_runtime.dart' as cott_runtime;
import 'package:dart_semantics/modules/semantics.dart' as semantics;

void check(bool condition, String label) {
  if (!condition) throw StateError(label);
}

void expectViolation(void Function() operation, String label) {
  try {
    operation();
  } on cott_runtime.CottContractViolation {
    return;
  }
  throw StateError('expected Cott violation: $label');
}

final class BadAssociated implements semantics.Associated<semantics.ChildOnlyState> {
  @override
  semantics.ChildOnlyState member(semantics.ChildOnlyState value) => value;
}

void main() {
  check(semantics.increment(41) == 42, 'increment');

  final firstEmpty = semantics.ChoiceEmpty<int>(cott_runtime.CottTypes.i32);
  final secondEmpty = semantics.ChoiceEmpty<int>(cott_runtime.CottTypes.i32);
  final payload = semantics.ChoiceValue<int>(cott_runtime.CottTypes.i32, field0: 0);
  check(firstEmpty == secondEmpty, 'generic empty enum equality');
  check(firstEmpty != payload, 'generic payload tag');

  final genericDefault =
      semantics.GenericDefault<int>(cott_runtime.CottTypes.i32);
  check(genericDefault.value is cott_runtime.Nothing<int>, 'generic omitted default');
  final explicitOption = const cott_runtime.Some<int>(9);
  final explicitDefault = semantics.GenericDefault<int>(
    cott_runtime.CottTypes.i32,
    value: explicitOption,
  );
  check(
    identical(explicitDefault.value, explicitOption),
    'generic explicit default override',
  );
  expectViolation(
    () => semantics.GenericDefault<int>(
      cott_runtime.CottTypes.i32,
      value: const Object(),
    ),
    'explicit invalid object must not impersonate an omitted argument',
  );

  final valid = semantics.Node(
    value: 1,
    next: const cott_runtime.Nothing<semantics.Node>(),
  );
  check(semantics.echo(valid) == valid, 'recursive nominal');

  var shared = semantics.SharedNode(
    value: 0,
    children: cott_runtime.CottList<semantics.SharedNode>(const []),
  );
  for (var depth = 0; depth < 16; depth += 1) {
    final child = shared;
    shared = semantics.SharedNode(
      value: depth + 1,
      children: cott_runtime.CottList<semantics.SharedNode>([child, child]),
    );
  }
  final echoedShared = semantics.echo_shared(shared);
  check(identical(echoedShared, shared), 'shared DAG root identity');
  check(
    identical(echoedShared.children[0], echoedShared.children[1]),
    'shared DAG child identity',
  );

  final combined = semantics.CombinedState();
  final semantics.Combined<int, String> composite = combined;
  final semantics.Child<int> child = combined;
  final semantics.Secondary<String> secondary = combined;
  check(child.inherited(7) == 7, 'inherited associated slot');
  check(child.child(9) == 9, 'child associated slot');
  check(composite.combined(11) == 11, 'combined trait');
  check(secondary.secondary('usable') == 'usable', 'secondary associated slot');
  check(
    identical(semantics.retain(combined, __COMBINED_WITNESSES__), combined),
    'generic inherited witnesses',
  );
  check(
    identical(semantics.retain_both(combined, __COMBINED_WITNESSES__), combined),
    'multiple callable bounds',
  );

  semantics.MultiBoundEmpty<semantics.CombinedState>(
    semantics.CombinedState.cottType,
  );
  expectViolation(
    () => semantics.MultiBoundEmpty<semantics.ChildOnlyState>(
      semantics.ChildOnlyState.cottType,
    ),
    'second nominal declaration bound',
  );

  final associated = semantics.AssociatedState();
  check(
    identical(
      semantics.retain_member(associated, associated, __MEMBER_WITNESSES__),
      associated,
    ),
    'associated type multiple bounds',
  );

  final badAssociatedType = cott_runtime.CottTypes.external<BadAssociated>(
    'test.BadAssociated',
    (value) => value is BadAssociated,
    identityWitness: BadAssociated,
    supertypes: [
      cott_runtime.CottTypes.external<
          semantics.Associated<semantics.ChildOnlyState>>(
        'semantics.Associated',
        (value) =>
            value is semantics.Associated<semantics.ChildOnlyState>,
        identityWitness: semantics.Associated<semantics.ChildOnlyState>,
      ) as cott_runtime.CottType<Object?>,
    ],
  );
  expectViolation(
    () => semantics.retain_member(
      BadAssociated(),
      semantics.ChildOnlyState(),
      __BAD_MEMBER_WITNESSES__,
    ),
    'second associated bound',
  );

  final consumerAny =
      semantics.ConsumerReady<Object?>(cott_runtime.CottTypes.any);
  final consumerInt = cott_runtime.CottRuntime.abi(
    consumerAny,
    semantics.Consumer.cottType<int>(cott_runtime.CottTypes.i32),
  );
  check(!identical(consumerInt, consumerAny), 'contravariant checked view');

  final choiceAny = semantics.ChoiceEmpty<Object?>(cott_runtime.CottTypes.any);
  expectViolation(
    () => cott_runtime.CottRuntime.abi(
      choiceAny,
      semantics.Choice.cottType<int>(cott_runtime.CottTypes.i32),
    ),
    'invariant checked view',
  );
}
"#;

const ABI_CONSUMER: &str = r#"import 'package:dart_abi/cott_runtime.dart' as cott_runtime;
import 'package:dart_abi/modules/abi.dart' as abi;

void check(bool condition, String label) {
  if (!condition) throw StateError(label);
}

void expectViolation(void Function() operation, String label) {
  try {
    operation();
  } on cott_runtime.CottContractViolation {
    return;
  }
  throw StateError('expected Cott violation: $label');
}

void main() {
  final abi.Count count = abi.DEFAULT_COUNT;
  check(count == 7, 'alias constant');
  check(abi.DEFAULT_NON_EMPTY.value == 'ready', 'refined nominal constant');
  check(abi.FIXED_VALUES[0] == 1 && abi.FIXED_VALUES[1] == 2, 'array constant');
  check(abi.FIXED_VALUES.dimension.value == BigInt.from(2), 'array dimension');
  check(abi.FIXED_BYTES[0] == 0 && abi.FIXED_BYTES[1] == 255, 'buffer constant');
  check(abi.FIXED_BYTES.dimension.value == BigInt.from(2), 'buffer dimension');

  final values = cott_runtime.CottArray(
    [5, 8],
    abi.FIXED_VALUES.dimension,
  );
  final bytes = cott_runtime.CottBuffer(
    [0x12, 0x34],
    abi.FIXED_BYTES.dimension,
  );
  final label = abi.NonEmpty(value: 'valid');
  expectViolation(() => abi.NonEmpty(value: ''), 'newtype refinement');

  final defaults = abi.Defaulted(anything: null);
  check(defaults.wide == BigInt.parse('9223372036854775807'), 'BigInt default');
  check(defaults.label.value == 'ready', 'nominal default');
  check(defaults.values[0] == 1 && defaults.values[1] == 2, 'array default');
  check(defaults.bytes[0] == 0 && defaults.bytes[1] == 255, 'buffer default');
  check(defaults.anything == null, 'required Any null');

  final abi.Moment moment = DateTime.parse('2026-09-13T12:34:56Z');
  final secretPayload = Object();
  final abi.Secret secret = cott_runtime.Opaque.of(
    const abi.__COTT_OPAQUE_MARKER__(),
    secretPayload,
  );
  check(secret.tag.tag == 'dart-abi-secret', 'opaque tag');

  final factory = cott_runtime.CottFactory.zero(
    abi.ReaderState,
    () => abi.ReaderState(),
  );
  final readerState = abi.ReaderState();
  final abi.Reader reader = readerState;
  final readerTrait =
      readerState.cottTraits.single as cott_runtime.CottTrait<abi.Reader>;
  final dynamicReader = cott_runtime.Dyn<abi.Reader>.of(reader, readerTrait);
  check(dynamicReader.value.read() == 37, 'Dyn dispatch');

  final bundle = abi.AbiBundle(
    count: count,
    label: label,
    values: values,
    bytes: bytes,
    moment: moment,
    secret: secret,
    factory$cott: factory,
    dynamic$cott: dynamicReader,
  );
  final echoed = abi.echo_bundle(bundle);
  check(identical(echoed, bundle), 'bundle identity');
  check(identical(echoed.label, label), 'nominal identity');
  check(identical(echoed.values, values), 'array identity');
  check(identical(echoed.bytes, bytes), 'buffer identity');
  check(identical(echoed.moment, moment), 'external identity');
  check(identical(echoed.secret.unwrap(), secretPayload), 'opaque identity');
  check(identical(echoed.factory$cott, factory), 'factory identity');
  check(identical(echoed.dynamic$cott, dynamicReader), 'Dyn identity');
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
            let path =
                env::temp_dir().join(format!("cott-dart-native-{}-{number}", std::process::id()));
            match fs::create_dir(&path) {
                Ok(()) => return Self { path },
                Err(error) if error.kind() == io::ErrorKind::AlreadyExists => number += 1,
                Err(error) => panic!(
                    "failed to create Dart native fixture {}: {error}",
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

fn dart_executable() -> PathBuf {
    let path = PathBuf::from(
        env::var_os("COTT_DART").expect("COTT_DART must name the Dart 3.13.3 executable"),
    );
    assert!(
        path.is_file(),
        "Dart executable is missing at {}",
        path.display()
    );
    path
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

fn assert_succeeded(label: &str, output: &Output) {
    assert!(
        output.status.success(),
        "{label} failed with {}\nstdout:\n{}\nstderr:\n{}",
        output.status,
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr),
    );
}

fn fixture(
    source_path: &str,
    source: &str,
    project_name: &str,
    external_types: BTreeMap<String, String>,
    effects: BTreeMap<String, bool>,
) -> (DartProjectConfig, DartPlan) {
    let parsed = parse_project([SourceFile::new(source_path, source)])
        .expect("Dart native semantics fixture should parse");
    let effect_names = effects.keys().cloned().collect();
    let ir = render(
        &lower_with_effects(Path::new("src"), parsed, &effect_names).expect("fixture should lower"),
    )
    .expect("fixture should render canonical IR");
    let plan = DartPlan::from_ir(&ir).expect("fixture should project to Dart");
    let config = DartProjectConfig {
        project: ProjectMetadata {
            name: project_name.to_owned(),
            version: "1.0.0".to_owned(),
            source: "src".to_owned(),
        },
        dart: DartTarget {
            source: "dart".to_owned(),
            generated: "generated/dart".to_owned(),
            sdk: "dart".to_owned(),
            runtime_validation: RuntimeValidation::Boundary,
            pubspec: None,
            lockfile: None,
            implementations: BTreeMap::new(),
            external_types,
        },
        effects,
        generator: GeneratorConfig::default(),
        verification: VerificationConfig::default(),
    };
    (config, plan)
}

fn implementation_body(callable: &DartCallable) -> &'static str {
    match callable.symbol.as_str() {
        "semantics.echo" | "semantics.echo_shared" => "return node;",
        "semantics.retain"
        | "semantics.retain_both"
        | "semantics.CombinedState.inherited"
        | "semantics.CombinedState.child"
        | "semantics.CombinedState.secondary"
        | "semantics.CombinedState.combined"
        | "semantics.ChildOnlyState.inherited"
        | "semantics.AssociatedState.inherited"
        | "semantics.AssociatedState.child"
        | "semantics.AssociatedState.secondary"
        | "semantics.AssociatedState.member"
        | "semantics.ChildOnlyState.child" => "return value;",
        "semantics.retain_member" => "return member;",
        "abi.ReaderState.read" => "return 37;",
        "abi.echo_bundle" => "return value;",
        symbol => panic!("unexpected callable in Dart native fixture: {symbol}"),
    }
}

fn binding(plan: &DartPlan, config: &DartProjectConfig, callable: &DartCallable) -> DartBinding {
    let signature = implementation_signature(plan, callable)
        .expect("canonical Dart implementation signature should render");
    let source = if callable.symbol == "semantics.increment" {
        let prefix = format!("_cott_t_{}", &sha256_hex(b"semantics")[..16]);
        format!(
            "import 'dart:math' as arithmetic;\n\n{signature} {{\n  return _incrementValue(value, null);\n}}\n\nint _incrementValue(int value, {prefix}.Node? marker) {{\n  return marker == null ? arithmetic.max(value, value + 1) : marker.value;\n}}\n"
        )
    } else {
        format!("{signature} {{\n  {}\n}}\n", implementation_body(callable))
    };
    validate_candidate(config, plan, callable, &BTreeSet::new(), source.as_bytes())
        .expect("fixture implementation should satisfy the Dart source audit");
    let relative = PathBuf::from(format!(
        "bindings/{}.dart",
        callable.symbol.replace('.', "/")
    ));
    let private_name = format!("_cott_{}", callable.symbol.replace('.', "_"));
    DartBinding {
        cott_symbol: callable.symbol.clone(),
        target_symbol: format!("{}:{private_name}", relative.display()),
        source_origin: relative,
        runtime_origin: PathBuf::from(format!(
            "dart/lib/src/cott_impl/{}.dart",
            callable.symbol.replace('.', "/")
        )),
        content_hash: format!("sha256:{}", sha256_hex(source.as_bytes())),
        bytes: source.into_bytes(),
        owner: DartOwner::Agent,
    }
}

fn associated_projection(base: Value, trait_name: &str, slot_name: &str) -> Value {
    json!({
        "kind": "associated_projection",
        "base": base,
        "trait": trait_name,
        "name": slot_name,
    })
}

fn associated_name(base: &Value, trait_name: &str, slot_name: &str) -> String {
    let base = serde_json::to_string(base).expect("associated base should serialize");
    let local = slot_name.rsplit('.').next().unwrap_or(slot_name);
    let identity = format!("{trait_name}::{local}::{base}");
    format!("CottAssoc_{}", &sha256_hex(identity.as_bytes())[..24])
}

fn ordered_witnesses(entries: Vec<(Value, &'static str, &'static str, String)>) -> String {
    entries
        .into_iter()
        .map(|(base, trait_name, slot_name, value)| {
            (associated_name(&base, trait_name, slot_name), value)
        })
        .collect::<BTreeMap<_, _>>()
        .into_values()
        .collect::<Vec<_>>()
        .join(", ")
}

fn semantics_consumer() -> String {
    let base = json!({"kind": "type_parameter", "name": "T"});
    let combined_associated = ordered_witnesses(vec![
        (
            base.clone(),
            "semantics.Parent",
            "semantics.Parent.Item",
            "cott_runtime.CottTypes.i32".to_owned(),
        ),
        (
            base.clone(),
            "semantics.Secondary",
            "semantics.Secondary.Label",
            "cott_runtime.CottTypes.string".to_owned(),
        ),
    ]);
    let combined = format!("semantics.CombinedState.cottType, {combined_associated}");

    let member = associated_projection(base.clone(), "semantics.Associated", "Member");
    let member_witnesses = ordered_witnesses(vec![
        (
            base.clone(),
            "semantics.Associated",
            "semantics.Associated.Member",
            "semantics.AssociatedState.cottType".to_owned(),
        ),
        (
            member.clone(),
            "semantics.Parent",
            "semantics.Parent.Item",
            "cott_runtime.CottTypes.i32".to_owned(),
        ),
        (
            member.clone(),
            "semantics.Secondary",
            "semantics.Secondary.Label",
            "cott_runtime.CottTypes.string".to_owned(),
        ),
    ]);
    let member_witnesses = format!("semantics.AssociatedState.cottType, {member_witnesses}");
    let bad_member_witnesses = ordered_witnesses(vec![
        (
            base,
            "semantics.Associated",
            "semantics.Associated.Member",
            "semantics.ChildOnlyState.cottType".to_owned(),
        ),
        (
            member.clone(),
            "semantics.Parent",
            "semantics.Parent.Item",
            "cott_runtime.CottTypes.i32".to_owned(),
        ),
        (
            member,
            "semantics.Secondary",
            "semantics.Secondary.Label",
            "cott_runtime.CottTypes.string".to_owned(),
        ),
    ]);
    let bad_member_witnesses = format!("badAssociatedType, {bad_member_witnesses}");

    SEMANTICS_CONSUMER
        .replace("__COMBINED_WITNESSES__", &combined)
        .replace("__MEMBER_WITNESSES__", &member_witnesses)
        .replace("__BAD_MEMBER_WITNESSES__", &bad_member_witnesses)
}

fn abi_consumer() -> String {
    let opaque_marker = format!(
        "CottOpaque_{}",
        &sha256_hex(ABI_OPAQUE_TAG.as_bytes())[..24]
    );
    ABI_CONSUMER.replace("__COTT_OPAQUE_MARKER__", &opaque_marker)
}

fn write_emission(root: &Path, emission: cott::dart::DartEmission) {
    for (relative, bytes) in emission.files {
        let Ok(relative) = relative.strip_prefix("dart") else {
            continue;
        };
        if relative
            .extension()
            .is_none_or(|extension| extension != "dart")
        {
            continue;
        }
        let destination = root.join(relative);
        fs::create_dir_all(
            destination
                .parent()
                .expect("emitted Dart file should have a parent"),
        )
        .expect("emitted Dart directory should be writable");
        fs::write(destination, bytes).expect("emitted Dart source should be writable");
    }
}

fn compile_and_run(
    config: DartProjectConfig,
    plan: DartPlan,
    consumer_source: &str,
    expected_callables: usize,
    private_part: &str,
) {
    let dart = dart_executable();
    let temp = TempDir::new();
    let package = temp.path.join("package");
    let consumer = temp.path.join("consumer");
    let pub_cache = temp.path.join("pub-cache");
    let home = temp.path.join("home");
    fs::create_dir_all(&package).expect("package root should be writable");
    fs::create_dir_all(consumer.join("bin")).expect("consumer bin should be writable");
    fs::create_dir_all(consumer.join("build")).expect("consumer build should be writable");
    fs::create_dir_all(&pub_cache).expect("isolated pub cache should be writable");
    fs::create_dir_all(&home).expect("isolated home should be writable");

    assert_eq!(
        plan.callables().len(),
        expected_callables,
        "native fixture callable inventory changed"
    );
    let bindings = plan
        .callables()
        .iter()
        .map(|callable| binding(&plan, &config, callable))
        .collect::<Vec<_>>();
    let emission = emit(&config, &plan, &bindings).expect("native fixture should emit");
    assert!(
        emission.unresolved.is_empty(),
        "native fixture must be fully bound"
    );
    write_emission(&package, emission);

    fs::write(
        package.join("pubspec.yaml"),
        format!(
            "name: {}\nversion: 1.0.0\nenvironment:\n  sdk: '>=3.13.3 <4.0.0'\n",
            config.project.name
        ),
    )
    .expect("package pubspec should be writable");
    fs::write(
        consumer.join("pubspec.yaml"),
        format!(
            "name: {}_consumer\nenvironment:\n  sdk: '>=3.13.3 <4.0.0'\ndependencies:\n  {}:\n    path: ../package\n",
            config.project.name, config.project.name
        ),
    )
    .expect("consumer pubspec should be writable");
    fs::write(consumer.join("bin/main.dart"), consumer_source)
        .expect("consumer source should be writable");

    let configure = |command: &mut Command| {
        command
            .current_dir(&consumer)
            .env("PUB_CACHE", &pub_cache)
            .env("HOME", &home)
            .env("DART_DISABLE_ANALYTICS", "1");
    };

    let mut pub_get = Command::new(&dart);
    pub_get.args(["pub", "get", "--offline"]);
    configure(&mut pub_get);
    let output = bounded_output("pub-get", &mut pub_get, &temp.path, COMPILER_TIMEOUT);
    assert_succeeded("isolated Dart path dependency resolution", &output);

    let executable = consumer.join("build/consumer");
    let mut compile = Command::new(&dart);
    compile
        .args(["compile", "exe", "bin/main.dart", "-o"])
        .arg(&executable);
    configure(&mut compile);
    let output = bounded_output(
        "consumer-compile",
        &mut compile,
        &temp.path,
        COMPILER_TIMEOUT,
    );
    assert_succeeded("Dart native consumer compilation", &output);

    let mut run = Command::new(&executable);
    run.current_dir(&consumer);
    let output = bounded_output("consumer-run", &mut run, &temp.path, CONSUMER_TIMEOUT);
    assert_succeeded("Dart native consumer execution", &output);

    fs::write(
        consumer.join("bin/private_part.dart"),
        format!(
            "import 'package:{}/{}';\nvoid main() {{}}\n",
            config.project.name, private_part
        ),
    )
    .expect("private part probe should be writable");
    let mut private_compile = Command::new(&dart);
    private_compile.args([
        "compile",
        "kernel",
        "bin/private_part.dart",
        "-o",
        "build/private_part.dill",
    ]);
    configure(&mut private_compile);
    let output = bounded_output(
        "private-part-compile",
        &mut private_compile,
        &temp.path,
        COMPILER_TIMEOUT,
    );
    assert!(
        !output.status.success(),
        "a separate consumer unexpectedly imported compiler-owned part {}\nstdout:\n{}\nstderr:\n{}",
        private_part,
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr),
    );
}

#[test]
#[ignore = "requires COTT_DART=/tmp/cott-dart-toolchain/dart-sdk/bin/dart"]
fn emitted_dart_preserves_generic_recursive_associated_and_variance_semantics() {
    let (config, plan) = fixture(
        "src/semantics.cott",
        CONTRACT,
        "dart_semantics",
        BTreeMap::new(),
        BTreeMap::from([("vendor.audit".to_owned(), true)]),
    );
    compile_and_run(
        config,
        plan,
        &semantics_consumer(),
        16,
        "src/cott_impl/semantics/increment.dart",
    );
}

#[test]
#[ignore = "requires COTT_DART=/tmp/cott-dart-toolchain/dart-sdk/bin/dart"]
fn emitted_dart_exposes_full_abi_and_runtime_defaults_to_a_real_consumer() {
    let (config, plan) = fixture(
        "src/abi.cott",
        ABI_CONTRACT,
        "dart_abi",
        BTreeMap::from([("abi.Moment".to_owned(), "dart:core#DateTime".to_owned())]),
        BTreeMap::new(),
    );
    compile_and_run(
        config,
        plan,
        &abi_consumer(),
        2,
        "src/cott_impl/abi/echo_bundle.dart",
    );
}
