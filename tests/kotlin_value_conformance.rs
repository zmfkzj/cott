//! Kotlin conformance for scenario data values, guarded pattern assertions,
//! `errors complete`, and the topological list predicates.
//!
//! Native tests run the real `cott verify` pipeline and are ignored unless the
//! pinned toolchain is available. Each compiles a Kotlin library, so run them
//! serially on small hosts:
//! `COTT_KOTLIN_HOME=<kotlinc 2.2.10> JAVA_HOME=<JDK 17> cargo test --test kotlin_value_conformance -- --ignored --test-threads=1`

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

const VALUES_TYPES: &str = r#"module example.values

enum Mode:
    Fast
    Careful(retries: U8)

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
    limits: Limits
    labels: Map[Str, U32]
    note: Option[Str]

enum Failure:
    Rejected(reason: Str)

struct Report:
    name: Str
    retries: U8
    tags: U64
    note: Option[Str]

struct Page[T, const N: U32]:
    items: Array[T, N]
    marker: Option[T]

struct Slot[T]:
    value: Option[T]

fn summarize(request: Request) -> Result[Report, Failure]:
    ensures Result.Ok(report) => report.name == request.name

    error Failure.Rejected

fn head(page: Page[Str, 2]) -> Option[Str]

fn fill(slot: Slot[Str]) -> Str

data base_limits: Limits = Limits(timeout_ms: 30, tags: List("a", "b"), port: Port(8080))
"#;

/// Six passing assertions over nested struct/enum/list/map/Option values, a
/// module data template, a generic const-witness struct, and a generic struct
/// whose only payload is `Option.Nothing`.
const NESTED_VALUES: &str = r#"
scenario nested_values:
    data request: Request = Request(
        name: "job",
        mode: Mode.Careful(retries: 2),
        limits: base_limits,
        labels: Map("x": 1, "y": 2),
        note: Option.Some(value: "n"),
    )
    data page: Page[Str, 2] = Page(items: Array("a", "b"), marker: Option.Nothing)
    data empty_slot: Slot[Str] = Slot(value: Option.Nothing)
    call outcome = summarize(request)
    call plain = summarize(Request(name: "fast", mode: Mode.Fast, limits: Limits(timeout_ms: 1, tags: List(), port: Port(1)), labels: Map(), note: Option.Nothing))
    call first = head(page)
    call filled = fill(empty_slot)
    call named = fill(Slot(value: Option.Some(value: "x")))
    assert outcome matches Result.Ok(report) => report.retries == 2
    assert outcome == Result.Ok(value: Report(name: "job", retries: 2, tags: 2, note: Option.Some(value: "n")))
    assert plain matches Result.Ok(report) => report.retries == 0 and report.tags == 0
    assert first == Option.Some(value: "a")
    assert filled == "empty"
    assert named == "x"
"#;

const INVALID_LIMITS: &str = r#"
scenario invalid_limits:
    data limits: Limits = Limits(timeout_ms: 0, tags: List(), port: Port(1))
    call outcome = summarize(Request(name: "x", mode: Mode.Fast, limits: limits, labels: Map(), note: Option.Nothing))
    assert outcome matches Result.Ok(_)
"#;

const SUMMARIZE: &str = "    val mode = request.mode
    val retries = if (mode is example.values.Mode.Careful) mode.retries else 0u.toUByte()
    return cott_runtime.Ok(example.values.Report(request.name, __RETRIES__, request.limits.tags.size.toULong(), request.note))
";
const HEAD: &str = "    return cott_runtime.Some(page.items.first())\n";
const FILL: &str = "    val value = slot.value
    return if (value is cott_runtime.Some) value.value else \"empty\"
";

const GRAPH_TYPES: &str = r#"module example.graph

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
"#;

/// Every variant, first-applicable precedence, and a Unicode `White_Space`
/// blank name (`__IDEOGRAPHIC_SPACE__` becomes U+3000).
const GRAPH_OUTCOMES: &str = r#"
scenario outcomes:
    data diamond: List[BuildStep] = List(BuildStep(name: "c", needs: Set()), BuildStep(name: "a", needs: Set("c")), BuildStep(name: "b", needs: Set("c")))
    call ordered = order_steps(diamond)
    call nothing = order_steps(List())
    call blank = order_steps(List(BuildStep(name: " __IDEOGRAPHIC_SPACE__", needs: Set())))
    call duplicate = order_steps(List(BuildStep(name: "a", needs: Set()), BuildStep(name: "a", needs: Set("zz"))))
    call unknown = order_steps(List(BuildStep(name: "a", needs: Set("zz")), BuildStep(name: "b", needs: Set("b"))))
    call self_dependent = order_steps(List(BuildStep(name: "a", needs: Set("a")), BuildStep(name: "b", needs: Set("c")), BuildStep(name: "c", needs: Set("b"))))
    call cycle = order_steps(List(BuildStep(name: "a", needs: Set("b")), BuildStep(name: "b", needs: Set("a"))))
    assert ordered == Result.Ok(value: List("c", "a", "b"))
    assert nothing == Result.Ok(value: List())
    assert blank == Result.Err(error: PipelineError.BlankStepName)
    assert duplicate == Result.Err(error: PipelineError.DuplicateStep)
    assert unknown == Result.Err(error: PipelineError.UnknownDependency)
    assert self_dependent == Result.Err(error: PipelineError.SelfDependency)
    assert cycle == Result.Err(error: PipelineError.Cycle)
"#;

/// No assertions: only the generated completeness, ensures, and first-error
/// checks can reject these calls.
const GRAPH_EXERCISE: &str = r#"
scenario exercise:
    call ordered = order_steps(List(BuildStep(name: "b", needs: Set("a")), BuildStep(name: "a", needs: Set())))
    call duplicate = order_steps(List(BuildStep(name: "a", needs: Set()), BuildStep(name: "a", needs: Set("zz"))))
"#;

/// A deterministic Kahn order over the canonical signature; `__CHECK_FIRST__`
/// and `__FINISH__` inject deliberate defects.
const ORDER_STEPS: &str = "    val whiteSpace = setOf(0x09, 0x0A, 0x0B, 0x0C, 0x0D, 0x20, 0x85, 0xA0, 0x1680, 0x2000, 0x2001, 0x2002, 0x2003, 0x2004, 0x2005, 0x2006, 0x2007, 0x2008, 0x2009, 0x200A, 0x2028, 0x2029, 0x202F, 0x205F, 0x3000)
    val names = steps.map { it.name }
    val known = names.toSet()
    val unknown = steps.any { step -> step.needs.any { it !in known } }
__CHECK_FIRST__    if (names.any { name -> name.all { it.code in whiteSpace } }) return cott_runtime.Err(example.graph.PipelineError.BlankStepName)
    if (known.size != names.size) return cott_runtime.Err(example.graph.PipelineError.DuplicateStep)
    if (unknown) return cott_runtime.Err(example.graph.PipelineError.UnknownDependency)
    if (steps.any { it.name in it.needs }) return cott_runtime.Err(example.graph.PipelineError.SelfDependency)
    val remaining = steps.map { it.name to it.needs.toMutableSet() }.toMutableList()
    val order = mutableListOf<kotlin.String>()
    while (remaining.isNotEmpty()) {
        val ready = remaining.filter { it.second.isEmpty() }.minByOrNull { it.first }
            ?: return cott_runtime.Err(example.graph.PipelineError.Cycle)
        order.add(ready.first)
        remaining.remove(ready)
        remaining.forEach { it.second.remove(ready.first) }
    }
__FINISH__    return cott_runtime.Ok(cott_runtime.CottList(order))
";

fn order_steps(check_first: &str, finish: &str) -> String {
    ORDER_STEPS
        .replace("__CHECK_FIRST__", check_first)
        .replace("__FINISH__", finish)
}

struct Project {
    root: PathBuf,
}

impl Project {
    /// A manifest-bound Kotlin project whose bindings use the exact canonical
    /// implementation signatures of `contract`.
    fn new(compiler: &Path, java: &Path, contract: &str, bodies: &[(&str, &str)]) -> Self {
        let module = contract
            .lines()
            .next()
            .and_then(|line| line.strip_prefix("module "))
            .expect("contract starts with its module");
        let leaf = module.rsplit('.').next().expect("module leaf");
        let contract_path = format!("src/{}.cott", module.replace('.', "/"));
        let root = project_root();
        let package = format!("cott_bindings.{leaf}");
        let binding_dir = root.join("kotlin/cott_bindings").join(leaf);
        fs::create_dir_all(&binding_dir).expect("create Kotlin binding directory");
        fs::create_dir_all(root.join(&contract_path).parent().expect("contract parent"))
            .expect("create contract directory");
        fs::write(root.join(&contract_path), contract).expect("write contract");

        let parsed = parse_project([SourceFile::new(contract_path.as_str(), contract)])
            .expect("conformance contract parses");
        let ir = render(&lower(Path::new("src"), parsed).expect("conformance contract lowers"))
            .expect("conformance contract renders canonical IR");
        let plan = KotlinPlan::from_ir(&ir).expect("conformance contract projects to Kotlin");
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
                format!("package {package}\n\n{signature} {{\n{body}}}\n"),
            )
            .expect("write Kotlin binding");
            implementations.push_str(&format!(
                "{:?} = {:?}\n",
                callable.symbol,
                format!("{package}.{}", callable.name)
            ));
        }
        fs::write(
            root.join("cott.toml"),
            format!(
                r#"[project]
name = "kotlin-{leaf}-conformance"
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

    fn native(contract: &str, bodies: &[(&str, &str)]) -> Self {
        let kotlin_home = std::env::var_os("COTT_KOTLIN_HOME")
            .map(PathBuf::from)
            .unwrap_or_else(|| PathBuf::from("/tmp/cott-kotlin-toolchain/kotlinc"));
        let java_home = std::env::var_os("JAVA_HOME")
            .map(PathBuf::from)
            .unwrap_or_else(|| PathBuf::from("/tmp/cott-kotlin-toolchain/jdk"));
        Self::new(
            &kotlin_home.join("bin/kotlinc"),
            &java_home.join("bin/java"),
            contract,
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

    /// A verified project whose named scenario really ran every assertion.
    fn assert_scenario_passed(&self, scenario_id: &str, assertions: u64) {
        assert_success("Kotlin verification", self.verify());
        let generation = self.generation();
        let current = &generation["current"];
        assert_eq!(current["verified"], true);
        let scenario = current["verification"]["contract_tests"]["scenarios"]
            .as_array()
            .expect("scenario evidence")
            .iter()
            .find(|scenario| scenario["scenario_id"] == scenario_id)
            .unwrap_or_else(|| panic!("`{scenario_id}` was not executed: {current}"));
        assert_eq!(scenario["status"], "passed");
        assert_eq!(scenario["assertions"], assertions);
    }

    /// Verification rejects the project for one of `reasons` and certifies nothing.
    fn assert_rejected(&self, label: &str, reasons: &[&str]) {
        let output = self.verify();
        let stderr = String::from_utf8_lossy(&output.stderr);
        assert!(
            !output.status.success() && reasons.iter().any(|reason| stderr.contains(reason)),
            "{label} must be rejected by one of {reasons:?}\nstdout:\n{}\nstderr:\n{stderr}",
            String::from_utf8_lossy(&output.stdout),
        );
        assert_eq!(self.generation()["current"]["verified"], false, "{label}");
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
            "cott-kotlin-value-conformance-{}-{nonce}",
            std::process::id()
        ));
        match fs::create_dir(&candidate) {
            Ok(()) => return candidate,
            Err(error) if error.kind() == io::ErrorKind::AlreadyExists => {
                nonce = nonce.saturating_add(1);
            }
            Err(error) => panic!("create Kotlin conformance project: {error}"),
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

fn summarize(retries: &str) -> String {
    SUMMARIZE.replace("__RETRIES__", retries)
}

fn values_project(scenarios: &str, retries: &str) -> Project {
    let body = summarize(retries);
    Project::native(
        &format!("{VALUES_TYPES}{scenarios}"),
        &[("summarize", body.as_str()), ("head", HEAD), ("fill", FILL)],
    )
}

fn graph_project(scenarios: &str, body: &str) -> Project {
    Project::native(
        &format!("{GRAPH_TYPES}{scenarios}").replace("__IDEOGRAPHIC_SPACE__", "\u{3000}"),
        &[("order_steps", body)],
    )
}

#[test]
fn kotlin_emission_binds_scenario_value_and_complete_error_contracts_without_a_toolchain() {
    let never = Path::new("kotlinc-never-run");
    let body = summarize("retries");
    let graph_body = order_steps("", "");
    for project in [
        Project::new(
            never,
            Path::new("java"),
            &format!("{VALUES_TYPES}{NESTED_VALUES}{INVALID_LIMITS}"),
            &[("summarize", body.as_str()), ("head", HEAD), ("fill", FILL)],
        ),
        Project::new(
            never,
            Path::new("java"),
            &format!("{GRAPH_TYPES}{GRAPH_OUTCOMES}{GRAPH_EXERCISE}")
                .replace("__IDEOGRAPHIC_SPACE__", "\u{3000}"),
            &[("order_steps", graph_body.as_str())],
        ),
    ] {
        assert_success("Kotlin emission", project.cott(&["emit", "kotlin"]));
        let generation = project.generation();
        let current = &generation["current"];
        assert_eq!(current["unresolved"], serde_json::json!([]), "{current}");
        assert!(
            current["implementations"]
                .as_array()
                .is_some_and(|implementations| implementations
                    .iter()
                    .all(|implementation| implementation["owner"] == "manifest")),
            "{current}"
        );
        assert_eq!(current["verified"], false);
    }
}

#[test]
#[ignore = "requires the pinned Kotlin 2.2.10/JDK 17 toolchain and bubblewrap"]
fn nested_scenario_values_reach_implementations_through_canonical_constructors() {
    values_project(NESTED_VALUES, "retries")
        .assert_scenario_passed("example.values.scenario.nested_values", 6);
}

#[test]
#[ignore = "requires the pinned Kotlin 2.2.10/JDK 17 toolchain and bubblewrap"]
fn guarded_assertions_fail_on_wrong_payload_and_nonmatching_variant() {
    // An `Ok` shell with the wrong payload fails the guarded predicate.
    values_project(NESTED_VALUES, "0u.toUByte()").assert_rejected(
        "wrong guarded payload",
        &["Kotlin scenario `example.values.scenario.nested_values` failed"],
    );
    // A variant that does not match fails instead of passing vacuously.
    let nonmatching = NESTED_VALUES.replace(
        "assert outcome matches Result.Ok(report) => report.retries == 2",
        "assert outcome matches Result.Err(_)",
    );
    assert_ne!(nonmatching, NESTED_VALUES);
    values_project(&nonmatching, "retries").assert_rejected(
        "non-matching guarded pattern",
        &["Kotlin scenario `example.values.scenario.nested_values` failed"],
    );
}

#[test]
#[ignore = "requires the pinned Kotlin 2.2.10/JDK 17 toolchain and bubblewrap"]
fn scenario_data_runs_canonical_struct_invariants() {
    // `nested_values` builds `Limits(timeout_ms: 1, ...)` with the same
    // implementation and passes; only the invariant differs here.
    values_project(INVALID_LIMITS, "retries").assert_rejected(
        "invariant-violating scenario data",
        &["Kotlin scenario `example.values.scenario.invalid_limits` failed"],
    );
}

#[test]
#[ignore = "requires the pinned Kotlin 2.2.10/JDK 17 toolchain and bubblewrap"]
fn complete_errors_and_graph_predicates_accept_a_correct_topological_order() {
    graph_project(GRAPH_OUTCOMES, &order_steps("", ""))
        .assert_scenario_passed("example.graph.scenario.outcomes", 7);
}

#[test]
#[ignore = "requires the pinned Kotlin 2.2.10/JDK 17 toolchain and bubblewrap"]
fn complete_errors_and_graph_predicates_reject_wrong_implementations() {
    let reasons = [
        "Kotlin contract execution failed for `example.graph.order_steps`",
        "Kotlin scenario `example.graph.scenario.exercise` failed",
    ];
    for (label, check_first, finish) in [
        (
            "Err on valid input under errors complete",
            "    return cott_runtime.Err(example.graph.PipelineError.Cycle)\n",
            "",
        ),
        (
            "order with a duplicated key",
            "",
            "    if (order.isNotEmpty()) order.add(0, order[0])\n",
        ),
        ("dependencies after dependents", "", "    order.reverse()\n"),
        (
            "unknown dependency reported before a duplicate name",
            "    if (unknown) return cott_runtime.Err(example.graph.PipelineError.UnknownDependency)\n",
            "",
        ),
    ] {
        graph_project(GRAPH_EXERCISE, &order_steps(check_first, finish))
            .assert_rejected(label, &reasons);
    }
    // The same exercise with the correct implementation verifies.
    assert_success(
        "correct implementation of the exercise scenario",
        graph_project(GRAPH_EXERCISE, &order_steps("", "")).verify(),
    );
}
