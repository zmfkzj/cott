//! Normative requirements: a stable identity plus normative text tied to one callable.
//!
//! Requirements are not a second evidence engine. `checked_by` only names scenario (or scenario
//! assertion) evidence that the selected target runner already records in its certified
//! generation snapshot. The report joins those links against exactly one bound snapshot; a
//! link is never evidence by itself, observed evidence never proves the requirement, and
//! external assumptions and temporary waivers are reported separately without changing any
//! status. Nothing here consults coverage policy allowances, so relaxing policy cannot upgrade
//! a failed or unverified requirement.

use std::collections::{BTreeMap, BTreeSet};
use std::fmt;
use std::sync::LazyLock;

use serde::Serialize;
use serde_json::{Map, Value};

use crate::agent::{ShadowFacet, scan_doc_candidates};
use crate::hash::sha256_hex;
use crate::ir::CanonicalIr;
use crate::manifest::TargetLanguage;
use crate::provenance::SourceSpan;

/// Version of the separate `cott.requirements` report. Generation, IR and runtime schemas are
/// unaffected by this report.
pub const REPORT_SCHEMA_VERSION: u32 = 1;
pub const REPORT_KIND: &str = "cott.requirements";
pub const REPORT_MEANING: &str = "observed means every checked_by link executed and held in the bound snapshot within its reported scope; it never proves the requirement, and assumptions or waivers never change a status";

/// One source-declared requirement from the current Canonical IR.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct Requirement {
    /// Stable identity: the fully qualified `module.requirement.NAME`.
    pub id: String,
    pub callable: String,
    pub statement: String,
    /// Project-relative source path of the declaring module.
    pub source: String,
    pub span: SourceSpan,
    pub checked_by: Vec<CheckLink>,
    pub assumptions: Vec<String>,
    pub waivers: Vec<String>,
}

/// Declared linkage only; the report decides what, if anything, it observed.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct CheckLink {
    pub scenario: String,
    /// Resolved scenario step identity `assert:<step_id>`; `None` links the whole scenario.
    pub assertion: Option<String>,
}

/// Requirements plus the current IR identity and scenario assertion inventory they bind to.
#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub struct RequirementModel {
    pub requirements: Vec<Requirement>,
    scenarios: BTreeMap<String, Vec<String>>,
    ir: BTreeMap<String, String>,
}

/// Where the report's evidence comes from. Construct [`Evidence::Recorded`] only after the
/// selected target's existing freshness gate proved that the record's current snapshot
/// describes the current inputs and managed bytes (the checks `verify`/`deploy` already run).
/// The report additionally requires a certified current snapshot and an exact Canonical IR
/// identity match, so evidence recorded for other sources, scenarios or fixtures never binds.
/// [`Evidence::Failed`] describes a verification attempt of the current inputs that failed
/// before certification: linked scenarios named by `failures` stay failed, and every other
/// link stays unverified. A failed attempt never falls back to an older certified snapshot.
#[derive(Clone, Copy, Debug)]
pub enum Evidence<'a> {
    Recorded(&'a Value),
    Failed {
        reason: &'a str,
        failures: &'a [ScenarioFailure],
    },
    Stale(&'a str),
    Absent(&'a str),
}

/// One scenario failure observed by a failed verification run of the current inputs.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ScenarioFailure {
    pub scenario: String,
    /// `assert:<step_id>` when the runner named the failing assertion.
    pub assertion: Option<String>,
    pub reason: String,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum EvidenceState {
    Current,
    Failed,
    Stale,
    Absent,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct EvidenceIdentity {
    pub state: EvidenceState,
    pub target: &'static str,
    pub snapshot: Option<String>,
    pub generation_id: Option<String>,
    pub reason: Option<String>,
}

#[derive(Clone, Copy, Debug, Eq, Ord, PartialEq, PartialOrd, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum RequirementStatus {
    Observed,
    Unverified,
    Unknown,
    Failed,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CheckScope {
    Scenario,
    Assertion,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CheckStatus {
    Observed,
    Unobserved,
    Missing,
    Unverified,
    Unknown,
    Failed,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct CheckReport {
    pub scenario: String,
    pub assertion: Option<String>,
    pub scope: CheckScope,
    pub status: CheckStatus,
    /// Whether the linked check actually ran in the bound snapshot.
    pub executed: bool,
    /// Assertions inside this link's scope, and how many of them the runner recorded as held.
    pub assertions_declared: u64,
    pub assertions_observed: u64,
    pub reason: Option<String>,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct RequirementEntry {
    pub id: String,
    pub callable: String,
    pub statement: String,
    pub source: String,
    pub span: SourceSpan,
    pub status: RequirementStatus,
    pub reason: Option<String>,
    pub checks: Vec<CheckReport>,
    pub assumptions: Vec<String>,
    pub waivers: Vec<String>,
}

#[derive(Clone, Debug, Default, Eq, PartialEq, Serialize)]
pub struct RequirementSummary {
    pub total: u64,
    pub observed: u64,
    pub unverified: u64,
    pub unknown: u64,
    pub failed: u64,
    /// Requirements carrying at least one waiver; counted separately from every status.
    pub waived: u64,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct RequirementReport {
    pub schema_version: u32,
    pub kind: &'static str,
    pub meaning: &'static str,
    pub evidence: EvidenceIdentity,
    pub requirements: Vec<RequirementEntry>,
    pub summary: RequirementSummary,
}

impl RequirementModel {
    /// Read requirement declarations and scenario assertion identities from validated IR.
    pub fn from_ir(ir: &CanonicalIr) -> Result<Self, String> {
        let mut model = Self::default();
        for module in &ir.modules {
            model.ir.insert(
                module.module.as_string(),
                format!("sha256:{}", sha256_hex(&module.bytes)),
            );
            let value = crate::ir::load(&module.bytes)?;
            let source = value
                .get("source")
                .and_then(Value::as_str)
                .ok_or("canonical IR module has no source")?;
            for declaration in value
                .get("declarations")
                .and_then(Value::as_array)
                .into_iter()
                .flatten()
            {
                match declaration.get("kind").and_then(Value::as_str) {
                    Some("scenario") => {
                        let name = string(declaration, "name")?;
                        let assertions = declaration
                            .get("steps")
                            .and_then(Value::as_array)
                            .into_iter()
                            .flatten()
                            .filter(|step| {
                                step.get("kind").and_then(Value::as_str) == Some("assert")
                            })
                            .map(|step| {
                                step.get("step_id")
                                    .and_then(Value::as_u64)
                                    .map(|id| format!("assert:{id}"))
                                    .ok_or_else(|| {
                                        format!("scenario `{name}` assert step has no step_id")
                                    })
                            })
                            .collect::<Result<Vec<_>, _>>()?;
                        model.scenarios.insert(name.to_owned(), assertions);
                    }
                    Some("requirement") => {
                        model.requirements.push(requirement(declaration, source)?);
                    }
                    _ => {}
                }
            }
        }
        model
            .requirements
            .sort_by(|left, right| left.id.cmp(&right.id));
        Ok(model)
    }

    pub fn is_empty(&self) -> bool {
        self.requirements.is_empty()
    }

    /// Recognize the compiler-owned runner failure messages that name a declared scenario in a
    /// failed verification of the current inputs. Only declared scenarios (and their declared
    /// assertions) are matched, and the result can only keep links failed or unverified; it
    /// never produces observed evidence.
    pub fn scenario_failures(&self, target: TargetLanguage, message: &str) -> Vec<ScenarioFailure> {
        let mut failures = Vec::new();
        for (scenario, assertions) in &self.scenarios {
            match target {
                // contract_runner.py raises `AssertionError(f"{id}: ...")` for scenario failures.
                TargetLanguage::Python => {
                    let prefix = format!("AssertionError: {scenario}: ");
                    for (index, _) in message.match_indices(&prefix) {
                        let detail = message[index + prefix.len()..]
                            .lines()
                            .next()
                            .unwrap_or_default()
                            .trim();
                        let assertion = detail
                            .strip_prefix("assertion step:")
                            .and_then(|rest| rest.strip_suffix(" failed"))
                            .and_then(|step| step.parse::<u32>().ok())
                            .map(|step| format!("assert:{step}"))
                            .filter(|assertion| assertions.contains(assertion));
                        failures.push(ScenarioFailure {
                            scenario: scenario.clone(),
                            assertion,
                            reason: detail.to_owned(),
                        });
                    }
                }
                TargetLanguage::Kotlin | TargetLanguage::Dart => {
                    let label = if target == TargetLanguage::Kotlin {
                        "Kotlin"
                    } else {
                        "Dart"
                    };
                    if message.contains(&format!("{label} scenario `{scenario}` failed")) {
                        failures.push(ScenarioFailure {
                            scenario: scenario.clone(),
                            assertion: None,
                            reason: "scenario failed".to_owned(),
                        });
                    }
                }
            }
        }
        failures.dedup();
        failures
    }

    /// Join every requirement against one evidence source for `target`.
    pub fn report(&self, target: TargetLanguage, evidence: Evidence<'_>) -> RequirementReport {
        let evidence_identity =
            |state, snapshot, generation_id, reason: Option<&str>| EvidenceIdentity {
                state,
                target: target_name(target),
                snapshot,
                generation_id,
                reason: reason.map(str::to_owned),
            };
        let (identity, joined) = match evidence {
            Evidence::Recorded(record) => match self.bind(target, record) {
                Ok((digest, generation_id, bound)) => (
                    evidence_identity(EvidenceState::Current, Some(digest), generation_id, None),
                    Joined::Current(bound),
                ),
                Err((digest, reason)) => (
                    evidence_identity(EvidenceState::Stale, digest, None, Some(&reason)),
                    Joined::Unbound,
                ),
            },
            Evidence::Failed { reason, failures } => (
                evidence_identity(EvidenceState::Failed, None, None, Some(reason)),
                Joined::Failed(failures),
            ),
            Evidence::Stale(reason) => (
                evidence_identity(EvidenceState::Stale, None, None, Some(reason)),
                Joined::Unbound,
            ),
            Evidence::Absent(reason) => (
                evidence_identity(EvidenceState::Absent, None, None, Some(reason)),
                Joined::Unbound,
            ),
        };
        let mut summary = RequirementSummary::default();
        let requirements = self
            .requirements
            .iter()
            .map(|requirement| {
                let checks = requirement
                    .checked_by
                    .iter()
                    .map(|link| self.check(link, &joined, &identity))
                    .collect::<Vec<_>>();
                let (status, reason) = aggregate(&checks);
                summary.total += 1;
                match status {
                    RequirementStatus::Observed => summary.observed += 1,
                    RequirementStatus::Unverified => summary.unverified += 1,
                    RequirementStatus::Unknown => summary.unknown += 1,
                    RequirementStatus::Failed => summary.failed += 1,
                }
                if !requirement.waivers.is_empty() {
                    summary.waived += 1;
                }
                RequirementEntry {
                    id: requirement.id.clone(),
                    callable: requirement.callable.clone(),
                    statement: requirement.statement.clone(),
                    source: requirement.source.clone(),
                    span: requirement.span.clone(),
                    status,
                    reason,
                    checks,
                    assumptions: requirement.assumptions.clone(),
                    waivers: requirement.waivers.clone(),
                }
            })
            .collect();
        RequirementReport {
            schema_version: REPORT_SCHEMA_VERSION,
            kind: REPORT_KIND,
            meaning: REPORT_MEANING,
            evidence: identity,
            requirements,
            summary,
        }
    }

    fn bind(
        &self,
        target: TargetLanguage,
        record: &Value,
    ) -> Result<(String, Option<String>, Bound), (Option<String>, String)> {
        let schema = match target {
            TargetLanguage::Python => crate::provenance::GENERATION_SCHEMA_VERSION,
            TargetLanguage::Kotlin => crate::kotlin::provenance::KOTLIN_GENERATION_SCHEMA_VERSION,
            TargetLanguage::Dart => crate::dart::provenance::DART_GENERATION_SCHEMA_VERSION,
        };
        let (current, last_verified) = crate::snapshot_record::decode(record, schema)
            .map_err(|error| (None, format!("generation record is invalid: {error}")))?;
        let digest = crate::snapshot_record::digest(&current)
            .map_err(|error| (None, format!("generation snapshot is invalid: {error}")))?;
        let stale = |reason: &str| (Some(digest.clone()), reason.to_owned());
        let target_matches = match target {
            TargetLanguage::Python => {
                current.get("target").is_none() && current.get("public_python_symbols").is_some()
            }
            TargetLanguage::Kotlin => {
                current.get("target").and_then(Value::as_str) == Some("kotlin")
            }
            TargetLanguage::Dart => current.get("target").and_then(Value::as_str) == Some("dart"),
        };
        if !target_matches {
            return Err(stale("current snapshot belongs to a different target"));
        }
        if current.get("verified").and_then(Value::as_bool) != Some(true) {
            return Err(stale("current snapshot is not verified"));
        }
        let certified = last_verified
            .as_ref()
            .map(crate::snapshot_record::digest)
            .transpose()
            .map_err(|error| (Some(digest.clone()), error))?;
        if certified.as_deref() != Some(digest.as_str()) {
            return Err(stale("current snapshot is not the last verified snapshot"));
        }
        let recorded_ir = current.get("ir").and_then(Value::as_object).map(|modules| {
            modules
                .iter()
                .map(|(module, hash)| {
                    hash.as_str()
                        .map(|hash| (module.clone(), hash.to_owned()))
                        .ok_or(())
                })
                .collect::<Result<BTreeMap<_, _>, _>>()
        });
        if !matches!(&recorded_ir, Some(Ok(recorded)) if *recorded == self.ir) {
            return Err(stale(
                "snapshot Canonical IR identity does not match the current sources",
            ));
        }
        let tests = current
            .pointer("/verification/contract_tests")
            .and_then(Value::as_object)
            .ok_or_else(|| stale("verified snapshot has no contract-test evidence"))?;
        let mut scenarios = BTreeMap::<String, Vec<Value>>::new();
        for entry in tests
            .get("scenarios")
            .and_then(Value::as_array)
            .ok_or_else(|| stale("verified snapshot has no scenario evidence"))?
        {
            let id = entry
                .get("scenario_id")
                .and_then(Value::as_str)
                .ok_or_else(|| stale("scenario evidence has no scenario_id"))?;
            scenarios
                .entry(id.to_owned())
                .or_default()
                .push(entry.clone());
        }
        let unavailable = match target {
            TargetLanguage::Python => BTreeMap::new(),
            TargetLanguage::Kotlin | TargetLanguage::Dart => tests
                .get("unavailable")
                .and_then(Value::as_object)
                .map(|entries| {
                    entries
                        .iter()
                        .filter_map(|(symbol, reason)| {
                            reason
                                .as_str()
                                .map(|reason| (symbol.clone(), reason.to_owned()))
                        })
                        .collect()
                })
                .unwrap_or_default(),
        };
        let generation_id = current
            .get("generation_id")
            .and_then(Value::as_str)
            .map(str::to_owned);
        Ok((
            digest,
            generation_id,
            Bound {
                target,
                scenarios,
                unavailable,
            },
        ))
    }

    fn check(
        &self,
        link: &CheckLink,
        joined: &Joined<'_>,
        identity: &EvidenceIdentity,
    ) -> CheckReport {
        let declared = self.scenarios.get(&link.scenario);
        let scope = if link.assertion.is_some() {
            CheckScope::Assertion
        } else {
            CheckScope::Scenario
        };
        let assertions_declared = match (&link.assertion, declared) {
            (Some(_), _) => 1,
            (None, Some(assertions)) => assertions.len() as u64,
            (None, None) => 0,
        };
        let mut report = CheckReport {
            scenario: link.scenario.clone(),
            assertion: link.assertion.clone(),
            scope,
            status: CheckStatus::Unverified,
            executed: false,
            assertions_declared,
            assertions_observed: 0,
            reason: None,
        };
        let bound = match joined {
            Joined::Current(bound) => bound,
            Joined::Failed(failures) => return failed_check(report, link, failures, identity),
            Joined::Unbound => {
                report.reason = Some(format!(
                    "no current verified evidence: {}",
                    identity
                        .reason
                        .as_deref()
                        .unwrap_or("evidence is not bound")
                ));
                return report;
            }
        };
        let Some(declared) = declared else {
            return report.with(CheckStatus::Unknown, "linked scenario is not declared");
        };
        if link
            .assertion
            .as_ref()
            .is_some_and(|assertion| !declared.contains(assertion))
        {
            return report.with(
                CheckStatus::Unknown,
                "linked assertion is not declared in the scenario",
            );
        }
        let entries = bound
            .scenarios
            .get(&link.scenario)
            .map(Vec::as_slice)
            .unwrap_or_default();
        let entry = match entries {
            [] => {
                return match bound.unavailable.get(&link.scenario) {
                    Some(reason) => report.with(CheckStatus::Unobserved, reason),
                    None => report.with(
                        CheckStatus::Missing,
                        "bound snapshot has no evidence for the linked scenario",
                    ),
                };
            }
            [entry] => entry,
            _ => {
                return report.with(CheckStatus::Unknown, "duplicate scenario evidence");
            }
        };
        match bound.target {
            TargetLanguage::Python => python_check(report, entry, link, declared),
            TargetLanguage::Kotlin | TargetLanguage::Dart => counted_check(report, entry, declared),
        }
    }
}

enum Joined<'a> {
    Current(Bound),
    Failed(&'a [ScenarioFailure]),
    Unbound,
}

/// A failed verification run certifies nothing. Its named scenario failures remain failures
/// for links whose scope they cover; every other link stays unverified, never observed.
fn failed_check(
    mut report: CheckReport,
    link: &CheckLink,
    failures: &[ScenarioFailure],
    identity: &EvidenceIdentity,
) -> CheckReport {
    let failure = failures
        .iter()
        .filter(|failure| failure.scenario == link.scenario)
        .find(|failure| link.assertion.is_none() || failure.assertion == link.assertion)
        .or_else(|| {
            failures
                .iter()
                .find(|failure| failure.scenario == link.scenario)
        });
    match failure {
        Some(failure) if link.assertion.is_none() || failure.assertion == link.assertion => {
            report.executed = true;
            let reason = format!("verification failed in this check: {}", failure.reason);
            report.with(CheckStatus::Failed, &reason)
        }
        Some(failure) => {
            let reason = format!(
                "linked scenario failed elsewhere ({}); the linked assertion has no certified outcome",
                failure.reason
            );
            report.with(CheckStatus::Unverified, &reason)
        }
        None => {
            let reason = format!(
                "verification failed before certification: {}",
                identity.reason.as_deref().unwrap_or("no reason recorded")
            );
            report.with(CheckStatus::Unverified, &reason)
        }
    }
}

struct Bound {
    target: TargetLanguage,
    scenarios: BTreeMap<String, Vec<Value>>,
    unavailable: BTreeMap<String, String>,
}

impl CheckReport {
    fn with(mut self, status: CheckStatus, reason: &str) -> Self {
        self.status = status;
        self.reason = Some(reason.to_owned());
        self
    }
}

/// Python records per-assertion grades inside each scenario entry.
fn python_check(
    mut report: CheckReport,
    entry: &Value,
    link: &CheckLink,
    declared: &[String],
) -> CheckReport {
    let reason = entry
        .get("reason")
        .and_then(Value::as_str)
        .unwrap_or("scenario was not observed");
    let scenario_grade = entry.get("grade").and_then(Value::as_str);
    if scenario_grade == Some("failed") || entry.get("status").is_some() {
        report.executed = scenario_grade == Some("failed");
        return if report.executed {
            report.with(CheckStatus::Failed, "linked scenario failed")
        } else {
            report.with(
                CheckStatus::Unknown,
                "unrecognized Python scenario evidence",
            )
        };
    }
    let Some(assertions) = entry.get("assertions").and_then(Value::as_array) else {
        return report.with(
            CheckStatus::Unknown,
            "Python scenario evidence has no assertions",
        );
    };
    let mut grades = BTreeMap::<&str, &str>::new();
    for assertion in assertions {
        let (Some(id), Some(grade)) = (
            assertion.get("assertion_id").and_then(Value::as_str),
            assertion.get("grade").and_then(Value::as_str),
        ) else {
            return report.with(
                CheckStatus::Unknown,
                "unrecognized Python assertion evidence",
            );
        };
        if grades.insert(id, grade).is_some() || !declared.iter().any(|declared| declared == id) {
            return report.with(
                CheckStatus::Unknown,
                "assertion evidence contradicts the declared scenario",
            );
        }
    }
    let scope = link
        .assertion
        .as_ref()
        .map_or(declared, std::slice::from_ref);
    let grade = |id: &String| grades.get(id.as_str()).copied();
    let observed = scope
        .iter()
        .filter(|&id| grade(id) == Some("test observation"))
        .count() as u64;
    report.assertions_observed = observed;
    if scope.iter().any(|id| grade(id) == Some("failed")) {
        report.executed = true;
        return report.with(CheckStatus::Failed, "linked assertion failed");
    }
    match scenario_grade {
        Some("test observation") if observed == report.assertions_declared => {
            report.executed = true;
            report.status = CheckStatus::Observed;
            report
        }
        Some("unobserved") if scope.iter().all(|id| grade(id) == Some("unobserved")) => {
            report.with(CheckStatus::Unobserved, reason)
        }
        _ => report.with(
            CheckStatus::Unknown,
            "recorded assertions do not match the linked scope",
        ),
    }
}

/// Kotlin and Dart record a scenario status and the count of assertions that executed and held,
/// in order, before any failure. A passing scenario therefore held every declared assertion.
fn counted_check(mut report: CheckReport, entry: &Value, declared: &[String]) -> CheckReport {
    let status = entry.get("status").and_then(Value::as_str);
    let counted = entry.get("assertions").and_then(Value::as_u64);
    match status {
        Some("passed") if counted == Some(declared.len() as u64) => {
            report.executed = true;
            report.assertions_observed = report.assertions_declared;
            report.status = CheckStatus::Observed;
            report
        }
        Some("failed" | "timeout" | "unexpected_cancellation" | "unexpected_exception") => {
            report.executed = true;
            report.with(CheckStatus::Failed, "linked scenario failed")
        }
        Some("unobserved") => {
            let reason = entry
                .get("reason")
                .and_then(Value::as_str)
                .unwrap_or("scenario was not observed");
            report.with(CheckStatus::Unobserved, reason)
        }
        _ => report.with(
            CheckStatus::Unknown,
            "scenario evidence does not match the declared assertions",
        ),
    }
}

fn aggregate(checks: &[CheckReport]) -> (RequirementStatus, Option<String>) {
    if checks.is_empty() {
        return (
            RequirementStatus::Unverified,
            Some("no checked_by linkage; the requirement has no evidence".to_owned()),
        );
    }
    let status = |check: &CheckReport| match check.status {
        CheckStatus::Observed => RequirementStatus::Observed,
        CheckStatus::Unobserved | CheckStatus::Unverified => RequirementStatus::Unverified,
        CheckStatus::Missing | CheckStatus::Unknown => RequirementStatus::Unknown,
        CheckStatus::Failed => RequirementStatus::Failed,
    };
    let worst = checks
        .iter()
        .map(status)
        .max()
        .expect("checks are nonempty");
    let reason = checks
        .iter()
        .find(|&check| status(check) == worst)
        .and_then(|check| check.reason.clone());
    (worst, reason)
}

fn target_name(target: TargetLanguage) -> &'static str {
    match target {
        TargetLanguage::Python => "python",
        TargetLanguage::Kotlin => "kotlin",
        TargetLanguage::Dart => "dart",
    }
}

fn string<'a>(value: &'a Value, key: &str) -> Result<&'a str, String> {
    value
        .get(key)
        .and_then(Value::as_str)
        .ok_or_else(|| format!("canonical declaration has no string `{key}`"))
}

fn texts(value: &Value, key: &str, id: &str) -> Result<Vec<String>, String> {
    value
        .get(key)
        .and_then(Value::as_array)
        .ok_or_else(|| format!("requirement `{id}` has no `{key}` array"))?
        .iter()
        .map(|entry| {
            entry
                .get("text")
                .and_then(Value::as_str)
                .map(str::to_owned)
                .ok_or_else(|| format!("requirement `{id}` has an invalid `{key}` entry"))
        })
        .collect()
}

fn requirement(declaration: &Value, source: &str) -> Result<Requirement, String> {
    let id = string(declaration, "name")?.to_owned();
    let span = serde_json::from_value(declaration.get("span").cloned().unwrap_or(Value::Null))
        .map_err(|error| format!("requirement `{id}` has an invalid span: {error}"))?;
    let checked_by = declaration
        .get("checked_by")
        .and_then(Value::as_array)
        .ok_or_else(|| format!("requirement `{id}` has no `checked_by` array"))?
        .iter()
        .map(|link| {
            Ok(CheckLink {
                scenario: string(link, "scenario")?.to_owned(),
                assertion: match link.get("assertion") {
                    Some(Value::Null) => None,
                    Some(Value::String(assertion)) => Some(assertion.clone()),
                    _ => return Err(format!("requirement `{id}` has an invalid assertion link")),
                },
            })
        })
        .collect::<Result<Vec<_>, String>>()?;
    Ok(Requirement {
        callable: string(declaration, "callable")?.to_owned(),
        statement: declaration
            .pointer("/statement/text")
            .and_then(Value::as_str)
            .ok_or_else(|| format!("requirement `{id}` has no statement"))?
            .to_owned(),
        source: source.to_owned(),
        span,
        checked_by,
        assumptions: texts(declaration, "assumptions", &id)?,
        waivers: texts(declaration, "waivers", &id)?,
        id,
    })
}

impl RequirementReport {
    /// Canonical JSON validated against the closed `requirement-report` schema.
    pub fn to_json(&self) -> Result<Value, String> {
        let value = serde_json::to_value(self)
            .map_err(|error| format!("serialize requirement report: {error}"))?;
        validate_report(&value)?;
        Ok(value)
    }
}

/// Validate a serialized report against the embedded closed schema.
pub fn validate_report(value: &Value) -> Result<(), String> {
    static SCHEMA: LazyLock<Value> = LazyLock::new(|| {
        serde_json::from_str(include_str!("../schemas/requirement-report.schema.json"))
            .expect("embedded requirement report schema is valid JSON")
    });
    let validator = jsonschema::validator_for(&SCHEMA)
        .map_err(|error| format!("invalid embedded requirement report schema: {error}"))?;
    let errors = validator
        .iter_errors(value)
        .map(|error| error.to_string())
        .collect::<Vec<_>>();
    if errors.is_empty() {
        Ok(())
    } else {
        Err(format!(
            "requirement report schema violation: {}",
            errors.join("; ")
        ))
    }
}

impl fmt::Display for RequirementReport {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        let summary = &self.summary;
        write!(
            formatter,
            "requirements: total={} observed={} unverified={} unknown={} failed={} waived={}; evidence={} target={}",
            summary.total,
            summary.observed,
            summary.unverified,
            summary.unknown,
            summary.failed,
            summary.waived,
            match self.evidence.state {
                EvidenceState::Current => "current",
                EvidenceState::Failed => "failed",
                EvidenceState::Stale => "stale",
                EvidenceState::Absent => "absent",
            },
            self.evidence.target,
        )?;
        if let Some(snapshot) = &self.evidence.snapshot {
            write!(formatter, " snapshot={snapshot}")?;
        }
        if let Some(reason) = &self.evidence.reason {
            write!(formatter, " reason={reason:?}")?;
        }
        write!(formatter, "\nrequirements meaning: {REPORT_MEANING}")?;
        for requirement in &self.requirements {
            write!(
                formatter,
                "\nrequirement {} for {}: {}",
                requirement.id,
                requirement.callable,
                status_name(requirement.status),
            )?;
            if let Some(reason) = &requirement.reason {
                write!(formatter, " reason={reason:?}")?;
            }
            for check in &requirement.checks {
                write!(
                    formatter,
                    "\n  check {}{} scope={} status={} executed={} assertions={}/{}",
                    check.scenario,
                    check
                        .assertion
                        .as_ref()
                        .map(|assertion| format!(" {assertion}"))
                        .unwrap_or_default(),
                    match check.scope {
                        CheckScope::Scenario => "scenario",
                        CheckScope::Assertion => "assertion",
                    },
                    check_name(check.status),
                    check.executed,
                    check.assertions_observed,
                    check.assertions_declared,
                )?;
                if let Some(reason) = &check.reason {
                    write!(formatter, " reason={reason:?}")?;
                }
            }
            for assumption in &requirement.assumptions {
                write!(formatter, "\n  external assumption: {assumption:?}")?;
            }
            for waiver in &requirement.waivers {
                write!(
                    formatter,
                    "\n  temporary waiver (does not change status): {waiver:?}"
                )?;
            }
        }
        Ok(())
    }
}

fn status_name(status: RequirementStatus) -> &'static str {
    match status {
        RequirementStatus::Observed => "observed",
        RequirementStatus::Unverified => "unverified",
        RequirementStatus::Unknown => "unknown",
        RequirementStatus::Failed => "failed",
    }
}

fn check_name(status: CheckStatus) -> &'static str {
    match status {
        CheckStatus::Observed => "observed",
        CheckStatus::Unobserved => "unobserved",
        CheckStatus::Missing => "missing",
        CheckStatus::Unverified => "unverified",
        CheckStatus::Unknown => "unknown",
        CheckStatus::Failed => "failed",
    }
}

/// Render the CURRENT INTENT requirement block for a selected intent context. Selected
/// requirements keep their exact normative statement and external assumptions; `checked_by`
/// and waivers are verification/reporting metadata and are not part of the intent context.
/// Returns an empty string when no requirement is selected, leaving existing prompts unchanged.
pub(crate) fn render_prompt_requirements(declarations: &Value) -> String {
    let mut selected = Vec::new();
    for module in declarations.as_object().into_iter().flat_map(Map::values) {
        for declaration in module
            .get("declarations")
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
            .filter(|declaration| {
                declaration.get("kind").and_then(Value::as_str) == Some("requirement")
            })
        {
            selected.push(declaration);
        }
    }
    if selected.is_empty() {
        return String::new();
    }
    let mut output = String::from(
        "Normative requirements (source-declared intent; keep every one. Linked checks are verification evidence, not proof, and never relax a requirement):\n",
    );
    for declaration in selected {
        let name = declaration
            .get("name")
            .and_then(Value::as_str)
            .unwrap_or("");
        let callable = declaration
            .get("callable")
            .and_then(Value::as_str)
            .unwrap_or("");
        let statement = declaration
            .pointer("/statement/text")
            .and_then(Value::as_str)
            .unwrap_or("");
        output.push_str(&format!(
            "Requirement {name} for {callable}:\n{statement}\n"
        ));
        for assumption in declaration
            .get("assumptions")
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
            .filter_map(|assumption| assumption.get("text").and_then(Value::as_str))
        {
            output.push_str(&format!("External assumption: {assumption}\n"));
        }
        output.push('\n');
    }
    output
}

/// A `COTT-K101` candidate in a requirement statement: normative text naming a facet that the
/// target callable's formal declaration does not support. Always a warning, never evidence.
#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct ShadowCandidate {
    pub requirement: String,
    pub callable: String,
    pub facet: ShadowFacet,
    pub start_byte: u64,
    pub end_byte: u64,
}

/// Scan one IR module's requirement statements with the existing closed doc scanner. The
/// location is the whole statement literal, because decoded text offsets are not source bytes.
pub(crate) fn shadow_candidates(module: &Value) -> Vec<ShadowCandidate> {
    let mut candidates = Vec::new();
    for declaration in module
        .get("declarations")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter(|declaration| {
            declaration.get("kind").and_then(Value::as_str) == Some("requirement")
        })
    {
        let (Some(requirement), Some(callable), Some(text), Some(start), Some(end)) = (
            declaration.get("name").and_then(Value::as_str),
            declaration.get("callable").and_then(Value::as_str),
            declaration
                .pointer("/statement/text")
                .and_then(Value::as_str),
            declaration
                .pointer("/statement/span/start_byte")
                .and_then(Value::as_u64),
            declaration
                .pointer("/statement/span/end_byte")
                .and_then(Value::as_u64),
        ) else {
            continue;
        };
        let facets = scan_doc_candidates(text)
            .into_iter()
            .map(|candidate| candidate.facet)
            .collect::<BTreeSet<_>>();
        candidates.extend(facets.into_iter().map(|facet| ShadowCandidate {
            requirement: requirement.to_owned(),
            callable: callable.to_owned(),
            facet,
            start_byte: start,
            end_byte: end,
        }));
    }
    candidates
}
