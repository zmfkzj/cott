use std::collections::{BTreeMap, BTreeSet};
use std::sync::LazyLock;

use serde::{Deserialize, Serialize};
use serde_json::{Value, json};

use crate::hash::sha256_hex;

pub const GENERATION_SCHEMA_VERSION: u32 = 7;
pub const CANONICAL_IR_SCHEMA_VERSION: u32 = 8;
pub const RUNTIME_ABI_VERSION: u32 = 7;
pub const CONTRACT_STRATEGY_SCHEMA_VERSION: u32 = 5;

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct GenerationCompatibility {
    pub generation_schema: u32,
    pub canonical_ir_schema: u32,
    pub runtime_abi: u32,
    pub contract_strategy_schema: u32,
}

impl GenerationCompatibility {
    pub const fn current() -> Self {
        Self {
            generation_schema: GENERATION_SCHEMA_VERSION,
            canonical_ir_schema: CANONICAL_IR_SCHEMA_VERSION,
            runtime_abi: RUNTIME_ABI_VERSION,
            contract_strategy_schema: CONTRACT_STRATEGY_SCHEMA_VERSION,
        }
    }

    pub const fn is_current(&self) -> bool {
        self.generation_schema == GENERATION_SCHEMA_VERSION
            && self.canonical_ir_schema == CANONICAL_IR_SCHEMA_VERSION
            && self.runtime_abi == RUNTIME_ABI_VERSION
            && self.contract_strategy_schema == CONTRACT_STRATEGY_SCHEMA_VERSION
    }
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct GenerationRecord {
    pub schema_version: u32,
    pub current: GenerationSnapshot,
    pub last_verified: Option<GenerationSnapshot>,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SourceSpan {
    pub start_byte: u64,
    pub end_byte: u64,
    pub start_line: u64,
    pub start_column: u64,
    pub end_line: u64,
    pub end_column: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum CoverageStatus {
    Observed,
    Unobserved,
    TrustDeclaration,
    Unknown,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ClauseCoverage {
    pub symbol: String,
    pub clause_id: String,
    pub span: SourceSpan,
    pub status: CoverageStatus,
    pub evidence: Vec<Value>,
}

#[derive(Clone, Debug, Default, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CoverageSummary {
    pub observed: u64,
    pub unobserved: u64,
    pub trust_declaration: u64,
    pub unknown: u64,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CoverageViolation {
    pub symbol: String,
    pub clause_id: String,
    pub span: SourceSpan,
    pub status: CoverageStatus,
    pub reason: String,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct CoveragePolicyResult {
    pub selected: u64,
    pub passed: bool,
    pub violations: Vec<CoverageViolation>,
}

impl Default for CoveragePolicyResult {
    fn default() -> Self {
        Self {
            selected: 0,
            passed: true,
            violations: Vec::new(),
        }
    }
}

#[derive(Clone, Debug, Default, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct SemanticCoverage {
    pub clauses: Vec<ClauseCoverage>,
    pub summary: CoverageSummary,
    pub policy: CoveragePolicyResult,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "snake_case")]
pub enum UnresolvedKind {
    Function,
    AsyncFunction,
    ImplMethod,
    AsyncImplMethod,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
pub struct UnresolvedRecord {
    pub cott_symbol: String,
    pub kind: UnresolvedKind,
    pub callable_kind: String,
    pub span: SourceSpan,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct GenerationSnapshot {
    pub generation_id: String,
    pub verified: bool,
    pub project_version: String,
    pub compatibility: GenerationCompatibility,
    pub inputs: Value,
    pub tools: Value,
    pub ir: Value,
    pub contract_surface: Value,
    pub public_python_symbols: Value,
    pub implementations: Value,
    pub dependencies: Value,
    pub managed_files: BTreeMap<String, String>,
    pub unresolved: Vec<UnresolvedRecord>,
    pub verification: Value,
    pub semantic_coverage: SemanticCoverage,
    pub agent_runs: Vec<AgentRun>,
}
#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ImplementationComparison {
    pub baseline_generation_id: Option<String>,
    pub status: &'static str,
    pub entries: Vec<ImplementationComparisonEntry>,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ImplementationComparisonEntry {
    pub cott_symbol: String,
    pub status: &'static str,
    pub changed_fields: BTreeMap<String, ImplementationFieldChange>,
}

#[derive(Clone, Debug, Eq, PartialEq, Serialize)]
pub struct ImplementationFieldChange {
    pub before: Value,
    pub after: Value,
}

pub fn compare_implementation_identities(
    baseline: Option<&GenerationSnapshot>,
    current: &GenerationSnapshot,
) -> ImplementationComparison {
    let Some(baseline) = baseline else {
        return ImplementationComparison {
            baseline_generation_id: None,
            status: "no_baseline",
            entries: Vec::new(),
        };
    };
    let baseline_id = baseline.generation_id.clone();
    let baseline = implementation_identity_index(&baseline.implementations);
    let current = implementation_identity_index(&current.implementations);
    let symbols = baseline
        .keys()
        .chain(current.keys())
        .cloned()
        .collect::<BTreeSet<_>>();
    let entries = symbols
        .into_iter()
        .map(|cott_symbol| {
            let baseline = baseline.get(&cott_symbol);
            let current = current.get(&cott_symbol);
            let status = match (baseline, current) {
                (None, Some(_)) => "added",
                (Some(_), None) => "removed",
                (Some(baseline), Some(current)) if baseline == current => "unchanged",
                (Some(_), Some(_)) => "changed",
                (None, None) => unreachable!("symbol belongs to a comparison index"),
            };
            ImplementationComparisonEntry {
                cott_symbol,
                status,
                changed_fields: implementation_field_changes(baseline, current),
            }
        })
        .collect();
    ImplementationComparison {
        baseline_generation_id: Some(baseline_id),
        status: "compared",
        entries,
    }
}

fn implementation_field_changes(
    baseline: Option<&BTreeMap<String, Value>>,
    current: Option<&BTreeMap<String, Value>>,
) -> BTreeMap<String, ImplementationFieldChange> {
    baseline
        .into_iter()
        .flat_map(|identity| identity.keys())
        .chain(current.into_iter().flat_map(|identity| identity.keys()))
        .cloned()
        .collect::<BTreeSet<_>>()
        .into_iter()
        .filter_map(|field| {
            let before = baseline.and_then(|identity| identity.get(&field)).cloned();
            let after = current.and_then(|identity| identity.get(&field)).cloned();
            ((before != after) || baseline.is_none() || current.is_none()).then(|| {
                (
                    field,
                    ImplementationFieldChange {
                        before: before.unwrap_or(Value::Null),
                        after: after.unwrap_or(Value::Null),
                    },
                )
            })
        })
        .collect()
}

fn implementation_identity_index(value: &Value) -> BTreeMap<String, BTreeMap<String, Value>> {
    value
        .as_array()
        .into_iter()
        .flatten()
        .filter_map(normalized_implementation_identity)
        .collect()
}

fn normalized_implementation_identity(
    implementation: &Value,
) -> Option<(String, BTreeMap<String, Value>)> {
    let implementation = implementation.as_object()?;
    let symbol = implementation.get("cott_symbol")?.as_str()?.to_owned();
    let mut identity = BTreeMap::new();
    for field in [
        "owner",
        "python_symbol",
        "source_origin",
        "runtime_origin",
        "content_hash",
    ] {
        identity.insert(field.to_owned(), implementation.get(field)?.clone());
    }
    identity.insert(
        "callable_kind".to_owned(),
        implementation.get("callable_kind")?.clone(),
    );
    identity.insert(
        "kind".to_owned(),
        implementation
            .get("kind")
            .cloned()
            .unwrap_or_else(|| Value::String("function".to_owned())),
    );
    for field in ["concrete", "method", "selection"] {
        identity.insert(
            field.to_owned(),
            implementation.get(field).cloned().unwrap_or(Value::Null),
        );
    }
    Some((symbol, identity))
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct AgentRun {
    pub symbol: String,
    pub adapter: String,
    pub adapter_version: String,
    pub argv_template: Vec<String>,
    pub executable: String,
    pub executable_hash: String,
    pub prompt_hash: String,
    pub implementation_hash: String,
    pub environment_names: Vec<String>,
    pub duration_ms: u64,
    pub status: AgentStatus,
    pub stdout: StreamDigest,
    pub stderr: StreamDigest,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct AgentStatus {
    pub exit_code: Option<i32>,
    pub signal: Option<i32>,
    pub timed_out: bool,
    pub cancelled: bool,
}

#[derive(Clone, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(deny_unknown_fields)]
pub struct StreamDigest {
    pub bytes: u64,
    pub sha256: String,
    pub truncated: bool,
}

impl GenerationSnapshot {
    pub fn compute_generation_id(&mut self) -> Result<(), String> {
        let identity = canonical_json(&normalized_generation_identity(self)?)?;
        self.generation_id = format!("sha256:{}", sha256_hex(&identity));
        Ok(())
    }
}

impl GenerationRecord {
    pub fn canonical_bytes(&self) -> Result<Vec<u8>, String> {
        self.validate_identities()?;
        let value = serde_json::to_value(self).map_err(|error| error.to_string())?;
        validate(&value)?;
        canonical_json(&value)
    }

    pub fn parse(bytes: &[u8]) -> Result<Self, String> {
        let value: Value = serde_json::from_slice(bytes).map_err(|error| error.to_string())?;
        validate(&value)?;
        let record: Self = serde_json::from_value(value).map_err(|error| error.to_string())?;
        record.validate_identities()?;
        Ok(record)
    }

    fn validate_identities(&self) -> Result<(), String> {
        if self.schema_version != GENERATION_SCHEMA_VERSION {
            return Err(format!(
                "generation schema version must be {GENERATION_SCHEMA_VERSION}"
            ));
        }
        validate_snapshot_identity(&self.current)?;
        if let Some(snapshot) = &self.last_verified {
            if !snapshot.verified {
                return Err("last_verified snapshot is not verified".to_owned());
            }
            validate_snapshot_identity(snapshot)?;
        }
        Ok(())
    }
}

fn validate_snapshot_identity(snapshot: &GenerationSnapshot) -> Result<(), String> {
    if crate::manifest::parse_api_version(&snapshot.project_version).is_none() {
        return Err("generation project_version must be a restricted x.y.z version".to_owned());
    }
    if !snapshot.compatibility.is_current() {
        return Err(format!(
            "generation compatibility must be {GENERATION_SCHEMA_VERSION}/{CANONICAL_IR_SCHEMA_VERSION}/{RUNTIME_ABI_VERSION}/{CONTRACT_STRATEGY_SCHEMA_VERSION}"
        ));
    }
    validate_unresolved_records(&snapshot.unresolved)?;
    validate_implementation_records(&snapshot.implementations)?;
    validate_semantic_coverage(&snapshot.semantic_coverage)?;
    let mut expected = snapshot.clone();
    expected.compute_generation_id()?;
    if expected.generation_id == snapshot.generation_id {
        Ok(())
    } else {
        Err(format!(
            "generation identity mismatch: expected {}, got {}",
            expected.generation_id, snapshot.generation_id
        ))
    }
}

fn normalized_generation_identity(snapshot: &GenerationSnapshot) -> Result<Value, String> {
    let mut current = serde_json::to_value(snapshot).map_err(|error| error.to_string())?;
    let object = current
        .as_object_mut()
        .expect("generation snapshot serializes as object");
    for key in [
        "generation_id",
        "verified",
        "verification",
        "semantic_coverage",
        "agent_runs",
    ] {
        object.remove(key);
    }
    Ok(json!({
        "domain": "cott.generation.v7",
        "schema_version": GENERATION_SCHEMA_VERSION,
        "current": current,
    }))
}

fn validate_unresolved_records(unresolved: &[UnresolvedRecord]) -> Result<(), String> {
    let mut symbols = BTreeSet::new();
    for record in unresolved {
        if record.cott_symbol.is_empty() {
            return Err("generation unresolved record has an empty cott_symbol".to_owned());
        }
        if !symbols.insert(&record.cott_symbol) {
            return Err(format!(
                "generation record contains duplicate unresolved callable `{}`",
                record.cott_symbol
            ));
        }
        let expected_callable_kind = match record.kind {
            UnresolvedKind::Function | UnresolvedKind::ImplMethod => "sync",
            UnresolvedKind::AsyncFunction | UnresolvedKind::AsyncImplMethod => "async",
        };
        if record.callable_kind != expected_callable_kind {
            return Err(format!(
                "generation unresolved callable `{}` has an incompatible callable_kind",
                record.cott_symbol
            ));
        }
        if record.span.end_byte < record.span.start_byte
            || record.span.end_line < record.span.start_line
            || record.span.start_line == 0
            || record.span.start_column == 0
            || record.span.end_line == 0
            || record.span.end_column == 0
        {
            return Err(format!(
                "generation unresolved callable `{}` has an invalid span",
                record.cott_symbol
            ));
        }
    }
    Ok(())
}

fn validate_semantic_coverage(coverage: &SemanticCoverage) -> Result<(), String> {
    let mut summary = CoverageSummary::default();
    let mut previous = None;
    let mut clauses = BTreeMap::new();
    for clause in &coverage.clauses {
        if !valid_coverage_symbol(&clause.symbol) {
            return Err(format!(
                "semantic coverage clause has invalid symbol `{}`",
                clause.symbol
            ));
        }
        let key = coverage_sort_key(&clause.symbol, &clause.clause_id).ok_or_else(|| {
            format!(
                "semantic coverage clause `{}` has an invalid clause_id",
                clause.symbol
            )
        })?;
        if previous.as_ref().is_some_and(|previous| previous >= &key) {
            return Err("semantic coverage clauses must be sorted and unique".to_owned());
        }
        previous = Some(key);
        if !valid_source_span(&clause.span) {
            return Err(format!(
                "semantic coverage clause `{}:{}` has an invalid span",
                clause.symbol, clause.clause_id
            ));
        }
        clauses.insert((clause.symbol.as_str(), clause.clause_id.as_str()), clause);
        match clause.status {
            CoverageStatus::Observed => summary.observed += 1,
            CoverageStatus::Unobserved => summary.unobserved += 1,
            CoverageStatus::TrustDeclaration => summary.trust_declaration += 1,
            CoverageStatus::Unknown => summary.unknown += 1,
        }
    }
    if coverage.summary != summary {
        return Err("semantic coverage summary does not match clause statuses".to_owned());
    }
    if coverage.policy.selected > coverage.clauses.len() as u64 {
        return Err("semantic coverage policy selected count exceeds clauses".to_owned());
    }
    if coverage.policy.passed != coverage.policy.violations.is_empty() {
        return Err("semantic coverage policy passed must match violations".to_owned());
    }
    if coverage.policy.violations.len() as u64 > coverage.policy.selected {
        return Err("semantic coverage policy violations exceed selected clauses".to_owned());
    }
    let mut previous = None;
    for violation in &coverage.policy.violations {
        let key = coverage_sort_key(&violation.symbol, &violation.clause_id).ok_or_else(|| {
            format!(
                "semantic coverage policy violation `{}` has an invalid clause_id",
                violation.symbol
            )
        })?;
        if previous.as_ref().is_some_and(|previous| previous >= &key) {
            return Err("semantic coverage policy violations must be sorted and unique".to_owned());
        }
        previous = Some(key);
        if violation.reason.trim().is_empty() {
            return Err("semantic coverage policy violation has an empty reason".to_owned());
        }
        let clause = clauses
            .get(&(violation.symbol.as_str(), violation.clause_id.as_str()))
            .ok_or_else(|| {
                format!(
                    "semantic coverage policy violation `{}:{}` has no clause",
                    violation.symbol, violation.clause_id
                )
            })?;
        if violation.status != clause.status || violation.span != clause.span {
            return Err(format!(
                "semantic coverage policy violation `{}:{}` does not match its clause",
                violation.symbol, violation.clause_id
            ));
        }
        if matches!(violation.status, CoverageStatus::Observed) {
            return Err("semantic coverage policy cannot reject an observed clause".to_owned());
        }
    }
    Ok(())
}

fn coverage_sort_key(symbol: &str, clause_id: &str) -> Option<(String, u8, u32, String)> {
    let (kind, id) = clause_id.split_once(':')?;
    if id.is_empty() || id.contains(':') {
        return None;
    }
    let kind_order = match kind {
        "requires" => 0,
        "ensures" => 1,
        "error" => 2,
        "modifies" => 3,
        "invariant" => 4,
        _ => return None,
    };
    if kind == "modifies" {
        valid_coverage_symbol(id).then(|| (symbol.to_owned(), kind_order, 0, id.to_owned()))
    } else {
        let numeric_id = id.parse::<u32>().ok()?;
        (numeric_id.to_string() == id)
            .then(|| (symbol.to_owned(), kind_order, numeric_id, String::new()))
    }
}

fn valid_coverage_symbol(symbol: &str) -> bool {
    !symbol.is_empty() && symbol.split('.').all(valid_coverage_identifier)
}

fn valid_coverage_identifier(value: &str) -> bool {
    let mut chars = value.bytes();
    chars
        .next()
        .is_some_and(|byte| byte == b'_' || byte.is_ascii_alphabetic())
        && chars.all(|byte| byte == b'_' || byte.is_ascii_alphanumeric())
}

fn valid_source_span(span: &SourceSpan) -> bool {
    span.end_byte >= span.start_byte
        && span.end_line >= span.start_line
        && span.start_line != 0
        && span.start_column != 0
        && span.end_line != 0
        && span.end_column != 0
}

fn validate_implementation_records(implementations: &Value) -> Result<(), String> {
    let implementations = implementations
        .as_array()
        .ok_or("generation implementations must be an array")?;
    let mut symbols = BTreeSet::new();
    for implementation in implementations {
        let object = implementation
            .as_object()
            .ok_or("generation implementation must be an object")?;
        let symbol = object
            .get("cott_symbol")
            .and_then(Value::as_str)
            .ok_or("generation implementation is missing cott_symbol")?;
        if !symbols.insert(symbol) {
            return Err(format!(
                "generation record contains duplicate implementation `{symbol}`"
            ));
        }
        let callable_kind = object
            .get("callable_kind")
            .and_then(Value::as_str)
            .ok_or_else(|| {
                format!("generation implementation `{symbol}` is missing callable_kind")
            })?;
        let selection = object.get("selection").unwrap_or(&Value::Null);
        match (object.get("kind").and_then(Value::as_str), callable_kind) {
            (Some("function"), "sync") | (Some("async_function"), "async") => {
                if object.get("concrete") != Some(&Value::Null)
                    || object.get("method") != Some(&Value::Null)
                    || selection != &Value::Null
                {
                    return Err(format!(
                        "function implementation `{symbol}` must not name a concrete or method"
                    ));
                }
            }
            (Some("impl_method"), "sync") | (Some("async_impl_method"), "async") => {
                let concrete = object
                    .get("concrete")
                    .and_then(Value::as_str)
                    .filter(|value| !value.is_empty())
                    .ok_or_else(|| {
                        format!("implementation method `{symbol}` is missing its concrete class")
                    })?;
                let method = object
                    .get("method")
                    .and_then(Value::as_str)
                    .filter(|value| !value.is_empty())
                    .ok_or_else(|| {
                        format!("implementation method `{symbol}` is missing its method name")
                    })?;
                if !symbol.ends_with(&format!(".{concrete}.{method}")) {
                    return Err(format!(
                        "implementation method `{symbol}` does not match `{concrete}.{method}`"
                    ));
                }
                let valid_selection = selection.as_object().is_some_and(|selection| {
                    selection.len() == 2
                        && selection.get("kind").and_then(Value::as_str) == Some("explicit")
                        && selection
                            .get("trait_method")
                            .and_then(Value::as_str)
                            .is_some_and(|trait_method| !trait_method.is_empty())
                });
                if !valid_selection {
                    return Err(format!(
                        "implementation method `{symbol}` has invalid selection provenance"
                    ));
                }
            }
            (Some("function" | "async_function" | "impl_method" | "async_impl_method"), _) => {
                return Err(format!(
                    "generation implementation `{symbol}` has an incompatible callable_kind"
                ));
            }
            _ => {
                return Err(format!(
                    "generation implementation `{symbol}` has an invalid kind"
                ));
            }
        }
    }
    Ok(())
}

fn canonical_json(value: &Value) -> Result<Vec<u8>, String> {
    let mut bytes = serde_json::to_vec(value).map_err(|error| error.to_string())?;
    bytes.push(b'\n');
    Ok(bytes)
}

fn validate(value: &Value) -> Result<(), String> {
    static SCHEMA: LazyLock<Value> = LazyLock::new(|| {
        serde_json::from_str(include_str!("../schemas/generation.schema.json"))
            .expect("embedded generation schema is valid JSON")
    });
    let validator = jsonschema::validator_for(&SCHEMA).map_err(|error| error.to_string())?;
    let errors = validator
        .iter_errors(value)
        .map(|error| error.to_string())
        .collect::<Vec<_>>();
    if errors.is_empty() {
        Ok(())
    } else {
        Err(errors.join("; "))
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    fn span() -> SourceSpan {
        SourceSpan {
            start_byte: 0,
            end_byte: 1,
            start_line: 1,
            start_column: 1,
            end_line: 1,
            end_column: 2,
        }
    }

    fn coverage() -> SemanticCoverage {
        SemanticCoverage {
            clauses: vec![
                ClauseCoverage {
                    symbol: "app.fetch".to_owned(),
                    clause_id: "requires:0".to_owned(),
                    span: span(),
                    status: CoverageStatus::Observed,
                    evidence: vec![],
                },
                ClauseCoverage {
                    symbol: "app.fetch".to_owned(),
                    clause_id: "ensures:1".to_owned(),
                    span: span(),
                    status: CoverageStatus::Unobserved,
                    evidence: vec![],
                },
                ClauseCoverage {
                    symbol: "app.fetch".to_owned(),
                    clause_id: "error:2".to_owned(),
                    span: span(),
                    status: CoverageStatus::TrustDeclaration,
                    evidence: vec![],
                },
                ClauseCoverage {
                    symbol: "app.fetch".to_owned(),
                    clause_id: "modifies:curriculum.trait_protocol.SimpleTask.completion_count"
                        .to_owned(),
                    span: span(),
                    status: CoverageStatus::Unknown,
                    evidence: vec![],
                },
                ClauseCoverage {
                    symbol: "app.fetch".to_owned(),
                    clause_id: "invariant:3".to_owned(),
                    span: span(),
                    status: CoverageStatus::Observed,
                    evidence: vec![],
                },
            ],
            summary: CoverageSummary {
                observed: 2,
                unobserved: 1,
                trust_declaration: 1,
                unknown: 1,
            },
            policy: CoveragePolicyResult::default(),
        }
    }

    #[test]
    fn empty_semantic_coverage_has_no_gate() {
        let coverage = SemanticCoverage::default();

        assert_eq!(coverage.policy.selected, 0);
        assert!(coverage.policy.passed);
        validate_semantic_coverage(&coverage).expect("empty coverage must be valid");
    }

    #[test]
    fn generation_compatibility_requires_exact_current_members() {
        assert!(GenerationCompatibility::current().is_current());
        let legacy = GenerationCompatibility {
            generation_schema: 6,
            canonical_ir_schema: 7,
            runtime_abi: 6,
            contract_strategy_schema: 4,
        };
        assert!(!legacy.is_current());

        assert!(
            serde_json::from_value::<GenerationCompatibility>(serde_json::json!({
                "generation_schema": GENERATION_SCHEMA_VERSION,
                "canonical_ir_schema": CANONICAL_IR_SCHEMA_VERSION,
                "runtime_abi": RUNTIME_ABI_VERSION,
            }))
            .is_err()
        );
    }

    #[test]
    fn semantic_coverage_requires_sorted_consistent_policy_evidence() {
        let mut coverage = coverage();
        coverage.policy = CoveragePolicyResult {
            selected: 2,
            passed: false,
            violations: vec![CoverageViolation {
                symbol: "app.fetch".to_owned(),
                clause_id: "ensures:1".to_owned(),
                span: span(),
                status: CoverageStatus::Unobserved,
                reason: "not observed".to_owned(),
            }],
        };
        validate_semantic_coverage(&coverage).expect("consistent semantic coverage must be valid");

        coverage.summary.observed = 1;
        assert!(validate_semantic_coverage(&coverage).is_err());
    }

    #[test]
    fn semantic_coverage_does_not_change_generation_identity() {
        let mut snapshot = GenerationSnapshot {
            generation_id: String::new(),
            verified: false,
            project_version: "0.1.0".to_owned(),
            compatibility: GenerationCompatibility::current(),
            inputs: serde_json::json!({}),
            tools: serde_json::json!({}),
            ir: serde_json::json!({}),
            contract_surface: serde_json::json!({}),
            public_python_symbols: serde_json::json!({}),
            implementations: serde_json::json!([]),
            dependencies: serde_json::json!([]),
            managed_files: BTreeMap::new(),
            unresolved: vec![],
            verification: Value::Null,
            semantic_coverage: SemanticCoverage::default(),
            agent_runs: vec![],
        };
        snapshot
            .compute_generation_id()
            .expect("baseline identity should compute");
        let identity = snapshot.generation_id.clone();
        snapshot.semantic_coverage = coverage();
        snapshot
            .compute_generation_id()
            .expect("coverage identity should compute");
        assert_eq!(snapshot.generation_id, identity);
    }
}
