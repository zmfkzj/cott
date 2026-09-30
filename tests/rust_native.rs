#![allow(dead_code)]
#[path = "support/rust_verification.rs"]
mod native;
use native::{Fixture, current, observed, scenario, stderr};
use std::fs;

const PURE: &str = r#"module demo.runner

struct Amount:
    value: I32
    invariant self.value >= 0

newtype Positive(I32)
    where self > 0

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

fn echo(value: I32) -> I32:
    requires value == 701
    ensures result == value

fn unwrap(amount: Amount) -> I32:
    ensures result == amount.value

fn positive(value: Positive) -> I32:
    ensures result > 0

enum Failure:
    Bad

fn classify(value: I32) -> Result[I32, Failure]:
    ensures Result.Ok(output) => output == value
    errors complete
    error Failure.Bad when value < 0

async fn later(value: I32) -> I32:
    ensures result == value

fn values(value: I32) -> Iterator[I32]:
    ensures true

fn conversation(value: I32) -> Generator[I32, Unit, I32]:
    ensures true

async fn async_values(value: I32) -> AsyncIterator[I32]:
    ensures true

async fn async_conversation(value: I32) -> AsyncGenerator[I32, Unit]:
    ensures true
"#;
#[test]
#[ignore = "requires COTT_CARGO and the real native sandbox"]
fn native_candidates_refinements_invariants_initializers_methods_errors_and_protocols() {
    let fixture = Fixture::new(
        "contracts",
        PURE,
        &[
            ("demo.runner.echo", "value", ""),
            ("demo.runner.unwrap", "*amount.get_value()", ""),
            ("demo.runner.positive", "*value.get_value()", ""),
            ("demo.runner.Meter.current", "*receiver.get_base()", ""),
            (
                "demo.runner.classify",
                "if value<0 {Err(crate::modules::demo::runner::Failure::Bad)}else{Ok(value)}",
                "",
            ),
            (
                "demo.runner.later",
                "tokio::task::yield_now().await; value",
                "",
            ),
            (
                "demo.runner.values",
                "crate::cott_runtime::IteratorValue::new(vec![value].into_iter())",
                "",
            ),
            (
                "demo.runner.conversation",
                "let mut done=false;crate::cott_runtime::Generator::from_fn(move |_| {if done {crate::cott_runtime::GeneratorStep::Return(value)}else{done=true;crate::cott_runtime::GeneratorStep::Yield(value)}},||{})",
                "",
            ),
            (
                "demo.runner.async_values",
                "let mut done=false;crate::cott_runtime::AsyncIteratorValue::from_fn(move |_| {let item=if done {None}else{done=true;Some(value)};Box::pin(async move {item})},|_|Box::pin(async{}))",
                "",
            ),
            (
                "demo.runner.async_conversation",
                "let mut done=false;crate::cott_runtime::AsyncGenerator::from_fn(move |_,_| {let step=if done {crate::cott_runtime::GeneratorStep::Return(())}else{done=true;crate::cott_runtime::GeneratorStep::Yield(value)};Box::pin(async move {step})},|_|Box::pin(async{}))",
                "",
            ),
        ],
        "",
    );
    fixture.emit();
    let record = fixture.verify();
    for (symbol, clause) in [
        ("demo.runner.Amount", "invariant:0"),
        ("demo.runner.echo", "requires:0"),
        ("demo.runner.echo", "ensures:1"),
        ("demo.runner.unwrap", "ensures:0"),
        ("demo.runner.positive", "ensures:0"),
        ("demo.runner.Meter.init", "requires:0"),
        ("demo.runner.Meter.init", "ensures:1"),
        ("demo.runner.Meter.current", "ensures:0"),
        ("demo.runner.classify", "ensures:0"),
        ("demo.runner.classify", "error:2"),
        ("demo.runner.later", "ensures:0"),
        ("demo.runner.values", "ensures:0"),
        ("demo.runner.conversation", "ensures:0"),
        ("demo.runner.async_values", "ensures:0"),
        ("demo.runner.async_conversation", "ensures:0"),
    ] {
        assert!(
            observed(&record, symbol, clause),
            "missing runtime evidence {symbol}:{clause}"
        );
    }
    let cases = current(&record)["verification"]["contract_tests"]["cases"]
        .as_array()
        .unwrap();
    assert!(
        cases
            .iter()
            .any(|c| c["symbol"] == "demo.runner.echo" && c["status"] == "ineligible")
    );
    assert!(
        cases
            .iter()
            .any(|c| c["symbol"] == "demo.runner.Amount" && c["status"] == "candidate_unavailable")
    );
    let library = fs::read(
        fixture
            .root
            .join("generated/rust/verification/cott-module.rlib"),
    )
    .unwrap();
    assert!(library.starts_with(b"!<arch>\n"));
}

#[test]
#[ignore = "requires COTT_CARGO and the real native sandbox"]
fn native_bad_contract_and_tampered_managed_bytes_never_certify() {
    let fixture = Fixture::new(
        "reject-contract",
        "module demo.runner\n\nfn echo(value: I32) -> I32:\n    ensures result == value\n",
        &[("demo.runner.echo", "value.wrapping_add(1)", "")],
        "",
    );
    fixture.emit();
    let pending = fs::read(fixture.root.join("generated/generation.json")).unwrap();
    let rejected = fixture.run(&["verify"]);
    assert_eq!(rejected.status.code(), Some(4), "{}", stderr(&rejected));
    assert_eq!(
        fs::read(fixture.root.join("generated/generation.json")).unwrap(),
        pending
    );
    let safe = Fixture::new(
        "reject-managed",
        "module demo.runner\n\nfn echo(value: I32) -> I32:\n    ensures result == value\n",
        &[("demo.runner.echo", "value", "")],
        "",
    );
    safe.emit();
    let file = safe.root.join("generated/rust/src/lib.rs");
    let mut bytes = fs::read(&file).unwrap();
    bytes.extend_from_slice(b"\n// modified managed material\n");
    fs::write(file, bytes).unwrap();
    let rejected = safe.run(&["verify"]);
    assert_eq!(rejected.status.code(), Some(4), "{}", stderr(&rejected));
    assert_eq!(current(&safe.record())["verified"], false);
}
#[test]
#[ignore = "requires COTT_CARGO and the real native sandbox"]
fn native_guarded_absence_trips_coverage_policy_exit_eight() {
    let fixture = Fixture::new(
        "coverage",
        "module demo.runner\n\nfn absent(value: Bool) -> Option[I32]:\n    ensures result matches Option.Some(item) => item > 0\n",
        &[("demo.runner.absent", "if value {None}else{None}", "")],
        "\n[verification]\ncandidate_limit=2\n[[verification.coverage.rules]]\nsymbol='demo.runner.absent'\nclauses=['ensures:0']\nallow_unknown=false\nallow_unobserved=false\nallow_trust_declaration=false\n",
    );
    fixture.emit();
    let result = fixture.run(&["verify"]);
    assert_eq!(result.status.code(), Some(8), "{}", stderr(&result));
    let record = fixture.record();
    assert_eq!(current(&record)["verified"], true);
    assert_eq!(record["current"], record["last_verified"]);
    assert_eq!(
        current(&record)["semantic_coverage"]["policy"]["passed"],
        false
    );
    let deployment = fixture.run(&["deploy"]);
    assert_eq!(deployment.status.code(), Some(4), "{}", stderr(&deployment));
    assert!(!fixture.root.join("dist/demo-0.1.0").exists());
}

const SCENARIOS: &str = r#"module demo.runner

fn identity(value: I32) -> I32:
    ensures result == value

fn read_text(source: Path) -> Str:
    ensures result.len > 0
    effects [file.read]

fn fetch(url: Str) -> Str:
    ensures result == "loopback fixture"
    effects [network]

async fn later(value: I32) -> I32:
    ensures result == value
    effects []

scenario pure_math:
    call total = identity(7)
    assert total == 7

scenario filesystem_read:
    fixtures:
        fs files:
            file "input.txt" text("filesystem fixture")
    call text = read_text(files.path("input.txt"))
    assert text == "filesystem fixture"

scenario loopback:
    fixtures:
        http service:
            route "/ok" -> response(status: 200, body: text("loopback fixture"), encoding: "utf-8")
    call reply = fetch(service.url("/ok"))
    assert reply == "loopback fixture"

scenario cancelled_worker:
    spawn worker = later(7)
    cancel worker
    await worker cancelled

requirement fixtures_are_observed for read_text:
    text "The finite file fixture is read through the public facade."
    checked_by filesystem_read
"#;
#[test]
#[ignore = "requires COTT_CARGO, the real native sandbox, and isolated loopback setup"]
fn native_finite_filesystem_loopback_and_cooperative_cancellation_scenarios() {
    let fixture = Fixture::new(
        "scenarios",
        SCENARIOS,
        &[
            ("demo.runner.identity", "value", ""),
            (
                "demo.runner.read_text",
                "std::fs::read_to_string(source).expect(\"finite file fixture\")",
                "",
            ),
            (
                "demo.runner.fetch",
                r#"let raw=url.strip_prefix("http://").expect("loopback URL");let(authority,path)=raw.split_once('/').expect("route path");let mut stream=std::net::TcpStream::connect(authority).expect("loopback connection");let request=format!("GET /{path} HTTP/1.1\r\nHost: {authority}\r\nConnection: close\r\n\r\n");stream.write_all(request.as_bytes()).expect("request");let mut response=String::new();stream.read_to_string(&mut response).expect("response");response.split_once("\r\n\r\n").expect("response body").1.to_owned()"#,
                "use std::io::{Read,Write};",
            ),
            (
                "demo.runner.later",
                "tokio::task::yield_now().await; value",
                "",
            ),
        ],
        "",
    );
    fixture.emit();
    let record = fixture.verify();
    for (id, assertions, cancellations) in [
        ("pure_math", 1, 0),
        ("filesystem_read", 1, 0),
        ("loopback", 1, 0),
        ("cancelled_worker", 0, 1),
    ] {
        let event = scenario(&record, &format!("demo.runner.scenario.{id}"));
        assert_eq!(event["status"], "passed");
        assert_eq!(event["assertions"], assertions);
        assert_eq!(event["cancellations"], cancellations);
        assert_eq!(event["cleaned"], true);
    }
    assert!(observed(&record, "demo.runner.read_text", "ensures:0"));
    assert!(observed(&record, "demo.runner.fetch", "ensures:0"));
    let requirements = fixture.run(&["requirements", "--format", "json"]);
    assert_eq!(
        requirements.status.code(),
        Some(0),
        "{}",
        stderr(&requirements)
    );
    let report: serde_json::Value = serde_json::from_slice(&requirements.stdout).unwrap();
    let requirement = report["requirements"]
        .as_array()
        .unwrap()
        .iter()
        .find(|r| r["id"] == "demo.runner.requirement.fixtures_are_observed")
        .unwrap();
    assert_eq!(requirement["status"], "observed");
    assert_eq!(requirement["checks"][0]["executed"], true);
    assert_eq!(requirement["checks"][0]["assertions_observed"], 1);
    assert_eq!(requirement["checks"][0]["assertions_declared"], 1);
}
