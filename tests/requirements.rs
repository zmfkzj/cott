use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::process::Command;

use cott::compiler::{SourceFile, parse_project};
use cott::hash::sha256_hex;
use cott::hir::lower;
use cott::ir::{CanonicalIr, render};
use cott::manifest::TargetLanguage;
use cott::python::artifact_plan::PythonArtifactPlan;
use cott::requirements::{
    CheckScope, CheckStatus, Evidence, EvidenceState, RequirementModel, RequirementStatus,
};
use serde_json::{Value, json};

const CONTRACT: &str = r#"module shop

fn place_order(total: U32) -> Bool:
    doc """
    Accept an order whose total is within the account limit.
    """

    ensures result == (total <= 100)

fn cancel_order(total: U32) -> Bool:
    ensures result == (total > 0)

scenario order_limits:
    call accepted = place_order(10)
    assert accepted
    call rejected = place_order(500)
    assert not rejected
"#;

const SCENARIO: &str = "shop.scenario.order_limits";
const REQUIREMENT: &str = "shop.requirement.ORDER_LIMIT";

fn source(requirement: &str) -> String {
    format!("{CONTRACT}\n{requirement}")
}

fn compile(text: &str) -> CanonicalIr {
    let parsed = parse_project([SourceFile::new("src/shop.cott", text)]).expect("contract parses");
    render(&lower(Path::new("src"), parsed).expect("contract lowers")).expect("IR renders")
}

fn lower_errors(text: &str) -> Vec<String> {
    let parsed = parse_project([SourceFile::new("src/shop.cott", text)]).expect("contract parses");
    lower(Path::new("src"), parsed)
        .expect_err("contract must be rejected")
        .into_iter()
        .map(|error| error.diagnostic.message)
        .collect()
}

fn model(text: &str) -> (CanonicalIr, RequirementModel) {
    let ir = compile(text);
    let model = RequirementModel::from_ir(&ir).expect("requirements load from IR");
    (ir, model)
}

fn ir_identity(ir: &CanonicalIr) -> Value {
    Value::Object(
        ir.modules
            .iter()
            .map(|module| {
                (
                    module.module.as_string(),
                    json!(format!("sha256:{}", sha256_hex(&module.bytes))),
                )
            })
            .collect(),
    )
}

fn record(schema: u32, snapshot: Value, verified: bool) -> Value {
    let mut snapshot = snapshot;
    snapshot["verified"] = json!(verified);
    cott::snapshot_record::encode(schema, &snapshot, verified.then_some(&snapshot))
        .expect("record encodes")
}

fn python_record(ir: &CanonicalIr, scenarios: Value) -> Value {
    record(
        8,
        json!({
            "generation_id": "sha256:1111111111111111111111111111111111111111111111111111111111111111",
            "ir": ir_identity(ir),
            "public_python_symbols": {},
            "verification": {"contract_tests": {"contracts": [], "lifecycle": [], "scenarios": scenarios}},
        }),
        true,
    )
}

fn kotlin_record(ir: &CanonicalIr, scenarios: Value, unavailable: Value) -> Value {
    record(
        2,
        json!({
            "generation_id": "sha256:2222222222222222222222222222222222222222222222222222222222222222",
            "ir": ir_identity(ir),
            "target": "kotlin",
            "verification": {"contract_tests": {"scenarios": scenarios, "unavailable": unavailable}},
        }),
        true,
    )
}

fn python_scenario(grades: [&str; 2]) -> Value {
    json!([{
        "scenario_id": SCENARIO,
        "grade": if grades.iter().all(|grade| *grade == "test observation") { "test observation" } else { "unobserved" },
        "reason": "isolated loopback capability unavailable",
        "trace": [],
        "fixtures": [],
        "assertions": [
            {"assertion_id": "assert:1", "grade": grades[0], "span": null},
            {"assertion_id": "assert:3", "grade": grades[1], "span": null},
        ],
    }])
}

#[test]
fn requirement_with_only_stable_id_and_text_is_accepted_and_unverified() {
    let (ir, model) = model(&source(
        "requirement ORDER_LIMIT for place_order:\n    text \"Orders above the account limit are rejected.\"\n",
    ));
    let requirement = &model.requirements[0];
    assert_eq!(requirement.id, REQUIREMENT);
    assert_eq!(requirement.callable, "shop.place_order");
    assert_eq!(
        requirement.statement,
        "Orders above the account limit are rejected."
    );
    assert!(requirement.checked_by.is_empty());

    // Even fully observed scenario evidence never verifies an unlinked requirement.
    let record = python_record(&ir, python_scenario(["test observation"; 2]));
    let report = model.report(TargetLanguage::Python, Evidence::Recorded(&record));
    assert_eq!(report.evidence.state, EvidenceState::Current);
    assert_eq!(report.requirements[0].status, RequirementStatus::Unverified);
    assert!(report.requirements[0].checks.is_empty());
    assert_eq!(report.summary.unverified, 1);
    report.to_json().expect("report matches the closed schema");
    assert!(
        report
            .to_string()
            .contains("requirement shop.requirement.ORDER_LIMIT for shop.place_order: unverified")
    );
}

#[test]
fn scenario_linkage_reports_observed_scope_but_never_proof() {
    let (ir, model) = model(&source(
        "requirement ORDER_LIMIT for place_order:\n    text \"Orders above the account limit are rejected.\"\n    checked_by order_limits\n    assumption \"The account limit is configured by billing.\"\n",
    ));
    let record = python_record(&ir, python_scenario(["test observation"; 2]));
    let report = model.report(TargetLanguage::Python, Evidence::Recorded(&record));
    let entry = &report.requirements[0];
    assert_eq!(entry.status, RequirementStatus::Observed);
    let check = &entry.checks[0];
    assert_eq!(check.scope, CheckScope::Scenario);
    assert!(check.executed);
    assert_eq!(
        (check.assertions_observed, check.assertions_declared),
        (2, 2)
    );
    assert_eq!(
        entry.assumptions,
        ["The account limit is configured by billing."]
    );
    assert!(report.meaning.contains("never proves the requirement"));
    let json = report.to_json().expect("closed schema");
    assert_eq!(json["evidence"]["target"], "python");

    // A partially unobserved scenario is not an observed scenario-scope check.
    let partial = python_record(&ir, python_scenario(["test observation", "unobserved"]));
    let report = model.report(TargetLanguage::Python, Evidence::Recorded(&partial));
    assert_ne!(report.requirements[0].status, RequirementStatus::Observed);

    let kotlin = kotlin_record(
        &ir,
        json!([{"kind": "scenario", "scenario_id": SCENARIO, "status": "passed", "assertions": 2, "observations": []}]),
        json!({}),
    );
    let report = model.report(TargetLanguage::Kotlin, Evidence::Recorded(&kotlin));
    assert_eq!(report.requirements[0].status, RequirementStatus::Observed);
    let unavailable = kotlin_record(
        &ir,
        json!([]),
        json!({SCENARIO: "failure fixtures have no Kotlin runtime"}),
    );
    let report = model.report(TargetLanguage::Kotlin, Evidence::Recorded(&unavailable));
    assert_eq!(report.requirements[0].status, RequirementStatus::Unverified);
    assert_eq!(
        report.requirements[0].checks[0].status,
        CheckStatus::Unobserved
    );
}

#[test]
fn missing_or_failed_scenarios_stay_failures_despite_waivers() {
    let (ir, model) = model(&source(
        "requirement ORDER_LIMIT for place_order:\n    text \"Orders above the account limit are rejected.\"\n    checked_by order_limits\n    waiver \"PAY-12: limit service rollout pending.\"\n",
    ));
    let missing = python_record(&ir, json!([]));
    let report = model.report(TargetLanguage::Python, Evidence::Recorded(&missing));
    assert_eq!(
        report.requirements[0].checks[0].status,
        CheckStatus::Missing
    );
    assert_eq!(report.requirements[0].status, RequirementStatus::Unknown);

    let message = "contract test process exited Some(1): Traceback (most recent call last):\nAssertionError: shop.scenario.order_limits: assertion step:3 failed\n";
    let failures = model.scenario_failures(TargetLanguage::Python, message);
    assert_eq!(failures.len(), 1);
    assert_eq!(failures[0].assertion.as_deref(), Some("assert:3"));
    let report = model.report(
        TargetLanguage::Python,
        Evidence::Failed {
            reason: message,
            failures: &failures,
        },
    );
    assert_eq!(report.evidence.state, EvidenceState::Failed);
    assert_eq!(report.requirements[0].status, RequirementStatus::Failed);
    assert_eq!(
        report.requirements[0].waivers,
        ["PAY-12: limit service rollout pending."]
    );
    assert_eq!((report.summary.failed, report.summary.waived), (1, 1));
    report.to_json().expect("closed schema");

    let kotlin = kotlin_record(
        &ir,
        json!([{"kind": "scenario", "scenario_id": SCENARIO, "status": "failed", "assertions": 1, "observations": []}]),
        json!({}),
    );
    let report = model.report(TargetLanguage::Kotlin, Evidence::Recorded(&kotlin));
    assert_eq!(report.requirements[0].status, RequirementStatus::Failed);
    assert!(report.requirements[0].checks[0].executed);

    let unrelated = model.scenario_failures(
        TargetLanguage::Kotlin,
        "Kotlin scenario `shop.scenario.other` failed",
    );
    assert!(
        unrelated.is_empty(),
        "only declared scenarios are recognized"
    );
}

#[test]
fn assertion_linkage_joins_the_resolved_step_identity() {
    let (ir, model) = model(&source(
        "requirement ORDER_LIMIT for place_order:\n    text \"Orders above the account limit are rejected.\"\n    checked_by order_limits assert 2\n",
    ));
    let link = &model.requirements[0].checked_by[0];
    assert_eq!(link.scenario, SCENARIO);
    assert_eq!(link.assertion.as_deref(), Some("assert:3"));

    let observed = python_record(&ir, python_scenario(["unobserved", "test observation"]));
    let report = model.report(TargetLanguage::Python, Evidence::Recorded(&observed));
    let check = &report.requirements[0].checks[0];
    assert_eq!(check.scope, CheckScope::Assertion);
    assert_eq!(
        check.status,
        CheckStatus::Unknown,
        "grades contradict scenario grade"
    );

    let ok = json!([{
        "scenario_id": SCENARIO,
        "grade": "test observation",
        "trace": [],
        "fixtures": [],
        "assertions": [
            {"assertion_id": "assert:1", "grade": "test observation", "span": null},
            {"assertion_id": "assert:3", "grade": "test observation", "span": null},
        ],
    }]);
    let report = model.report(
        TargetLanguage::Python,
        Evidence::Recorded(&python_record(&ir, ok)),
    );
    let check = &report.requirements[0].checks[0];
    assert_eq!(check.status, CheckStatus::Observed);
    assert_eq!(
        (check.assertions_observed, check.assertions_declared),
        (1, 1)
    );

    let other_assertion = model.scenario_failures(
        TargetLanguage::Python,
        "AssertionError: shop.scenario.order_limits: assertion step:1 failed",
    );
    let report = model.report(
        TargetLanguage::Python,
        Evidence::Failed {
            reason: "verification failed",
            failures: &other_assertion,
        },
    );
    assert_eq!(
        report.requirements[0].checks[0].status,
        CheckStatus::Unverified,
        "another assertion's failure is not this assertion's outcome"
    );

    let errors = lower_errors(&source(
        "requirement ORDER_LIMIT for place_order:\n    text \"Orders above the account limit are rejected.\"\n    checked_by order_limits assert 3\n",
    ));
    assert!(
        errors.iter().any(|error| error.contains("assert 3")),
        "{errors:?}"
    );
}

#[test]
fn stale_or_uncertified_evidence_is_never_reused() {
    let original = source(
        "requirement ORDER_LIMIT for place_order:\n    text \"Orders above the account limit are rejected.\"\n    checked_by order_limits\n",
    );
    let (old_ir, _) = model(&original);
    let record = python_record(&old_ir, python_scenario(["test observation"; 2]));
    let changed = original.replace("place_order(500)", "place_order(501)");
    let (_, changed_model) = model(&changed);
    let report = changed_model.report(TargetLanguage::Python, Evidence::Recorded(&record));
    assert_eq!(report.evidence.state, EvidenceState::Stale);
    assert_eq!(report.requirements[0].status, RequirementStatus::Unverified);
    report.to_json().expect("closed schema");

    let (ir, model) = model(&original);
    let mut unverified = python_record(&ir, python_scenario(["test observation"; 2]));
    let current = unverified["current"].as_str().expect("digest").to_owned();
    let mut snapshot = unverified["snapshots"][&current].clone();
    snapshot["verified"] = json!(false);
    unverified = cott::snapshot_record::encode(8, &snapshot, None).expect("record");
    let report = model.report(TargetLanguage::Python, Evidence::Recorded(&unverified));
    assert_eq!(report.evidence.state, EvidenceState::Stale);
    assert_eq!(report.requirements[0].status, RequirementStatus::Unverified);

    let foreign = kotlin_record(&ir, json!([]), json!({}));
    let report = model.report(TargetLanguage::Python, Evidence::Recorded(&foreign));
    assert_eq!(report.evidence.state, EvidenceState::Stale);
}

fn surface(text: &str) -> Value {
    PythonArtifactPlan::from_ir(&compile(text))
        .expect("plan")
        .contract_surface()
}

#[test]
fn prompts_and_intent_preserve_normative_text_but_not_evidence_metadata() {
    let plain = surface(CONTRACT);
    let base = source(
        "requirement ORDER_LIMIT for place_order:\n    text \"Orders above the account limit are rejected.\"\n    assumption \"The account limit is configured by billing.\"\n",
    );
    let linked = base.replace(
        "rejected.\"\n",
        "rejected.\"\n    checked_by order_limits assert 1\n",
    ) + "    waiver \"PAY-12: limit service rollout pending.\"\n";
    let reworded = base.replace("are rejected", "are refused");
    let hashes = |text: &str| cott::intent::fingerprints(&surface(text), b"").expect("hashes");
    let before = cott::intent::fingerprints(&plain, b"").expect("hashes");
    let with_requirement = hashes(&base);
    assert_ne!(
        before["shop.place_order"],
        with_requirement["shop.place_order"]
    );
    assert_eq!(
        before["shop.cancel_order"],
        with_requirement["shop.cancel_order"]
    );
    assert_eq!(with_requirement, hashes(&linked));
    assert_ne!(
        with_requirement["shop.place_order"],
        hashes(&reworded)["shop.place_order"]
    );

    let linked_surface = surface(&linked);
    let context = cott::intent::context(&linked_surface, "shop.place_order", b"").expect("context");
    let selected = context["declarations"]["shop"]["declarations"]
        .as_array()
        .expect("selected declarations");
    let requirement = selected
        .iter()
        .find(|declaration| declaration["kind"] == "requirement")
        .expect("requirement is part of the callable intent");
    assert!(requirement.get("checked_by").is_none());
    assert!(requirement.get("waivers").is_none());

    let plan = PythonArtifactPlan::from_ir(&compile(&linked)).expect("plan");
    let callable = plan
        .callables()
        .into_iter()
        .find(|callable| callable.cott_symbol == "shop.place_order")
        .expect("callable");
    let prompt = String::from_utf8(
        cott::agent::render_prompt(
            &callable,
            &context,
            &[],
            &BTreeMap::new(),
            None,
            None,
            Path::new("implementation.py"),
        )
        .expect("prompt renders"),
    )
    .expect("UTF-8 prompt");
    let (intent, formal) = prompt
        .split_once("\nFORMAL DECLARATIONS\n")
        .expect("prompt sections");
    assert!(intent.contains("Accept an order whose total is within the account limit."));
    assert!(intent.contains(
        "Requirement shop.requirement.ORDER_LIMIT for shop.place_order:\nOrders above the account limit are rejected.\n"
    ));
    assert!(intent.contains("External assumption: The account limit is configured by billing."));
    assert!(!prompt.contains("PAY-12"));
    let formal = formal.split("\nPROJECT RULES\n").next().expect("formal");
    assert!(!formal.contains("requirement"), "{formal}");

    let unrelated =
        cott::intent::context(&linked_surface, "shop.cancel_order", b"").expect("context");
    assert!(
        unrelated["declarations"]["shop"]["declarations"]
            .as_array()
            .expect("declarations")
            .iter()
            .all(|declaration| declaration["kind"] != "requirement")
    );
}

#[test]
fn requirement_targets_and_links_are_resolved_explicitly() {
    for (requirement, expected) in [
        (
            "requirement ORDER_LIMIT for missing_order:\n    text \"Orders are rejected.\"\n",
            "missing_order",
        ),
        (
            "requirement ORDER_LIMIT for place_order:\n    text \"Orders are rejected.\"\n    checked_by unknown_scenario\n",
            "unknown_scenario",
        ),
        (
            "requirement ORDER_LIMIT for place_order:\n    text \"\"\n",
            "must not be empty",
        ),
        (
            "requirement ORDER_LIMIT for place_order:\n    text \"Orders are rejected.\"\nrequirement ORDER_LIMIT for cancel_order:\n    text \"Cancels are accepted.\"\n",
            "duplicate requirement",
        ),
    ] {
        let errors = lower_errors(&source(requirement));
        assert!(
            errors.iter().any(|error| error.contains(expected)),
            "{requirement}: {errors:?}"
        );
    }

    let method = "module shop\n\ntrait Reader:\n    fn read(self, amount: I32) -> I32\n\nimpl ReaderState for Reader:\n    state:\n        count: I32 = 0\n    init(count: I32):\n        requires count > 0\n        ensures self.count == count\n    fn read(self, amount: I32) -> I32:\n        ensures result == amount\n\nrequirement READS for ReaderState.read:\n    text \"Reads return the amount.\"\n";
    let errors = lower_errors(method);
    assert!(
        errors.iter().any(|error| error.contains("free function")),
        "{errors:?}"
    );
}

struct TempProject(PathBuf);

impl Drop for TempProject {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.0);
    }
}

#[test]
fn requirement_shadow_specification_is_only_a_warning() {
    let root = std::env::temp_dir().join(format!("cott-requirements-k101-{}", std::process::id()));
    let _ = fs::remove_dir_all(&root);
    let project = TempProject(root);
    fs::create_dir_all(project.0.join("src")).expect("source directory");
    fs::create_dir_all(project.0.join("python")).expect("target directory");
    fs::write(
        project.0.join("cott.toml"),
        "[project]\nname = \"demo\"\nversion = \"0.1.0\"\nsource = \"src\"\n\n[target.python]\nsource = \"python\"\ngenerated = \"generated/python\"\nstubs = \"generated/stubs\"\ninterpreter = \".venv/bin/python\"\ntype_checker = \".venv/bin/basedpyright\"\nruntime_validation = \"boundary\"\n",
    )
    .expect("manifest");
    fs::write(
        project.0.join("python/pyproject.toml"),
        "[project]\nname = \"demo\"\nversion = \"0.1.0\"\nrequires-python = \">=3.14,<3.15\"\ndependencies = []\n",
    )
    .expect("target metadata");
    fs::write(
        project.0.join("src/shop.cott"),
        "module shop\n\nfn place_order(total: U32) -> Bool\n\nrequirement ORDER_LIMIT for place_order:\n    text \"The call must fail above the account limit.\"\n",
    )
    .expect("source");
    let output = Command::new(env!("CARGO_BIN_EXE_cott"))
        .args(["check", "--project"])
        .arg(&project.0)
        .output()
        .expect("cott check runs");
    let stderr = String::from_utf8_lossy(&output.stderr);
    assert!(output.status.success(), "{stderr}");
    assert!(
        stderr.contains("warning: ")
            && stderr.contains("COTT-K101")
            && stderr.contains(
                "error duty is stated in requirement `shop.requirement.ORDER_LIMIT` for `shop.place_order`"
            ),
        "{stderr}"
    );
}
