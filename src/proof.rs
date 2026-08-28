use std::collections::{BTreeMap, BTreeSet};

use serde_json::{Map, Value, json};

use crate::ir::CanonicalIr;

pub const ALGORITHM: &str = "bounded-dnf-difference-constraints";
pub const VERSION: u32 = 1;
pub const NODE_LIMIT: usize = 1024;
pub const DEPTH_LIMIT: usize = 128;
pub const SYMBOL_LIMIT: usize = 128;
pub const ATOM_LIMIT: usize = 1024;
const DISPROVED_PREFIX: &str = "static contract proof disproved: ";

pub fn is_disproved_error(error: &str) -> bool {
    error.starts_with(DISPROVED_PREFIX)
}

pub const BRANCH_LIMIT: usize = 256;

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum Outcome {
    Proved,
    Disproved,
    Unknown,
}
impl Outcome {
    fn name(self) -> &'static str {
        match self {
            Self::Proved => "proved",
            Self::Disproved => "disproved",
            Self::Unknown => "unknown",
        }
    }
}
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum Compare {
    Eq,
    Lt,
    Le,
    Gt,
    Ge,
}
impl Compare {
    fn invert(self) -> Self {
        match self {
            Self::Eq => Self::Eq,
            Self::Lt => Self::Ge,
            Self::Le => Self::Gt,
            Self::Gt => Self::Le,
            Self::Ge => Self::Lt,
        }
    }
}
#[derive(Clone, Debug)]
enum Atom {
    Bool(String),
    Compare {
        left: Affine,
        op: Compare,
        right: Affine,
    },
}
#[derive(Clone, Debug, Default)]
struct Affine {
    constant: i64,
    terms: BTreeMap<String, i64>,
    domains: BTreeMap<String, (i64, i64)>,
}
impl Affine {
    fn constant(value: i64) -> Self {
        Self {
            constant: value,
            ..Self::default()
        }
    }
    fn variable(name: String, domain: (i64, i64)) -> Self {
        let mut terms = BTreeMap::new();
        terms.insert(name.clone(), 1);
        let mut domains = BTreeMap::new();
        domains.insert(name, domain);
        Self {
            constant: 0,
            terms,
            domains,
        }
    }
    fn add(mut self, other: Self, sign: i64) -> Option<Self> {
        self.constant = self
            .constant
            .checked_add(other.constant.checked_mul(sign)?)?;
        for (name, value) in other.terms {
            let entry = self.terms.entry(name).or_default();
            *entry = entry.checked_add(value.checked_mul(sign)?)?;
        }
        self.terms.retain(|_, value| *value != 0);
        for (name, domain) in other.domains {
            if self.domains.get(&name).is_some_and(|old| *old != domain) {
                return None;
            }
            self.domains.insert(name, domain);
        }
        Some(self)
    }
    fn scale(mut self, multiplier: i64) -> Option<Self> {
        self.constant = self.constant.checked_mul(multiplier)?;
        for value in self.terms.values_mut() {
            *value = value.checked_mul(multiplier)?;
        }
        self.terms.retain(|_, value| *value != 0);
        Some(self)
    }
}
#[derive(Clone, Debug)]
enum Formula {
    Constant(bool),
    Atom(Atom),
    And(Box<Formula>, Box<Formula>),
    Or(Box<Formula>, Box<Formula>),
    Not(Box<Formula>),
}
type Branch = Vec<(Atom, bool)>;
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum Reason {
    Unsupported,
    Limit,
}

/// Emits static mathematical evidence only; generated-code execution stays in `contract_tests`.
pub fn prove_contracts(
    ir: &CanonicalIr,
    scope: Option<&BTreeSet<String>>,
) -> Result<Value, String> {
    let scoped_refinements = scope
        .map(|selected| reachable_refinements(ir, selected))
        .transpose()?;
    let mut contracts = Vec::new();
    for (module_index, module) in ir.modules.iter().enumerate() {
        let root = crate::ir::load(&module.bytes)
            .map_err(|error| format!("module {module_index}: {error}"))?;
        let declarations = root
            .get("declarations")
            .and_then(Value::as_array)
            .ok_or_else(|| format!("module {module_index}: declarations is not an array"))?;
        for (declaration_index, declaration) in declarations.iter().enumerate() {
            let context = format!("module {module_index} declaration {declaration_index}");
            let kind = required_string(declaration, "kind", &context)?;
            let symbol = required_string(declaration, "name", &context)?.to_owned();
            if kind == "newtype"
                && scoped_refinements
                    .as_ref()
                    .is_none_or(|needed| needed.contains(&symbol))
                && declaration
                    .get("refinement")
                    .is_some_and(|value| !value.is_null())
            {
                contracts.push(obligation(
                    "refinement_satisfiability",
                    &symbol,
                    None,
                    prove_satisfiable(declaration.get("refinement").expect("checked")),
                ));
            }
            if kind == "function" && scope.is_none_or(|selected| selected.contains(&symbol)) {
                let clauses = declaration
                    .pointer("/contract/clauses")
                    .and_then(Value::as_array)
                    .ok_or_else(|| {
                        format!("{context} function {symbol}: contract clauses is not an array")
                    })?;
                let requires = clauses
                    .iter()
                    .filter(|clause| clause.get("kind").and_then(Value::as_str) == Some("requires"))
                    .filter(|clause| clause.get("guard").is_none_or(Value::is_null))
                    .map(|clause| {
                        clause.get("expression").ok_or_else(|| {
                            format!("{context} function {symbol}: requires expression missing")
                        })
                    })
                    .collect::<Result<Vec<_>, _>>()?;
                if !requires.is_empty() {
                    contracts.push(obligation(
                        "requires_consistency",
                        &symbol,
                        Some(requires.len()),
                        prove_all_satisfiable(&requires),
                    ));
                }
            }
            if kind == "impl" {
                let initializer_symbol = format!("{symbol}.init");
                if scope.is_none_or(|selected| selected.contains(&initializer_symbol)) {
                    if let Some(clauses) = declaration
                        .pointer("/init/contracts/requires")
                        .and_then(Value::as_array)
                    {
                        push_requires_obligation(
                            &mut contracts,
                            &initializer_symbol,
                            clauses,
                            &context,
                        )?;
                    }
                }
                let selected_methods = declaration
                    .get("selected_methods")
                    .and_then(Value::as_array)
                    .ok_or_else(|| {
                        format!("{context} impl {symbol}: selected_methods is not an array")
                    })?;
                // Default and specialization slots point at their own selected free
                // functions, whose declaration obligations are reported separately.
                let selected_names = selected_methods
                    .iter()
                    .filter_map(|slot| slot.get("trait_method").and_then(Value::as_str))
                    .map(local_name)
                    .collect::<BTreeSet<_>>();
                for method in declaration
                    .get("methods")
                    .and_then(Value::as_array)
                    .ok_or_else(|| format!("{context} impl {symbol}: methods is not an array"))?
                {
                    let Some(name) = method.get("name").and_then(Value::as_str).map(local_name)
                    else {
                        continue;
                    };
                    if !selected_names.contains(name) {
                        continue;
                    }
                    let method_symbol = format!("{symbol}.{name}");
                    if scope.is_none_or(|selected| selected.contains(&method_symbol)) {
                        if let Some(clauses) = method
                            .pointer("/contracts/requires")
                            .and_then(Value::as_array)
                        {
                            push_requires_obligation(
                                &mut contracts,
                                &method_symbol,
                                clauses,
                                &context,
                            )?;
                        }
                    }
                }
            }
        }
    }
    if let Some(failed) = contracts
        .iter()
        .find(|entry| entry.get("status").and_then(Value::as_str) == Some("disproved"))
    {
        return Err(format!(
            "{DISPROVED_PREFIX}{} for {} with counterexample {}",
            failed
                .get("kind")
                .and_then(Value::as_str)
                .unwrap_or("obligation"),
            failed
                .get("symbol")
                .and_then(Value::as_str)
                .unwrap_or("unknown"),
            failed.get("model").cloned().unwrap_or(Value::Null)
        ));
    }
    Ok(
        json!({"algorithm": ALGORITHM, "version": VERSION, "limits": {"nodes": NODE_LIMIT, "depth": DEPTH_LIMIT, "symbols": SYMBOL_LIMIT, "atoms": ATOM_LIMIT, "branches": BRANCH_LIMIT}, "contracts": contracts}),
    )
}
fn obligation(kind: &str, symbol: &str, clauses: Option<usize>, result: Proof) -> Value {
    let mut entry = Map::new();
    entry.insert("kind".to_owned(), json!(kind));
    entry.insert("symbol".to_owned(), json!(symbol));
    entry.insert("status".to_owned(), json!(result.outcome.name()));
    if let Some(clauses) = clauses {
        entry.insert("clauses".to_owned(), json!(clauses));
    }
    if let Some(reason) = result.reason {
        entry.insert("reason".to_owned(), json!(reason));
    }
    if let Some(model) = result.model {
        entry.insert("model".to_owned(), model);
    }
    Value::Object(entry)
}

fn push_requires_obligation(
    contracts: &mut Vec<Value>,
    symbol: &str,
    clauses: &[Value],
    context: &str,
) -> Result<(), String> {
    let requires = clauses
        .iter()
        .filter(|clause| clause.get("guard").is_none_or(Value::is_null))
        .map(|clause| {
            clause
                .get("expression")
                .ok_or_else(|| format!("{context} {symbol}: requires expression missing"))
        })
        .collect::<Result<Vec<_>, _>>()?;
    if !requires.is_empty() {
        let mut entry = obligation(
            "requires_consistency",
            symbol,
            Some(requires.len()),
            prove_all_satisfiable(&requires),
        );
        if let Some(span) = clauses.first().and_then(|clause| clause.get("span")) {
            entry["span"] = span.clone();
        }
        contracts.push(entry);
    }
    Ok(())
}
struct Proof {
    outcome: Outcome,
    reason: Option<&'static str>,
    model: Option<Value>,
}
fn unknown(reason: Reason) -> Proof {
    Proof {
        outcome: Outcome::Unknown,
        reason: Some(if reason == Reason::Limit {
            "limit"
        } else {
            "unsupported_expression"
        }),
        model: None,
    }
}
fn prove_satisfiable(expression: &Value) -> Proof {
    prove_all_satisfiable(&[expression])
}
fn prove_all_satisfiable(expressions: &[&Value]) -> Proof {
    let mut formula = Formula::Constant(true);
    let mut nodes: usize = 1;
    let mut parsed_nodes: usize = 0;
    for expression in expressions {
        if let Err(reason) = expression_budget(expression, 0, &mut parsed_nodes) {
            return unknown(reason);
        }
        let item = match parse_formula(expression, 0) {
            Ok(item) => item,
            Err(reason) => return unknown(reason),
        };
        nodes = match nodes.checked_add(formula_nodes(&item).saturating_add(1)) {
            Some(nodes) if nodes <= NODE_LIMIT => nodes,
            _ => return unknown(Reason::Limit),
        };
        formula = Formula::And(Box::new(formula), Box::new(item));
    }
    let branches = match dnf(&formula, false, 0) {
        Ok(branches) => branches,
        Err(reason) => return unknown(reason),
    };
    if branches.is_empty() {
        return Proof {
            outcome: Outcome::Disproved,
            reason: None,
            model: Some(json!({})),
        };
    }
    let mut unknown_reason = None;
    for branch in branches {
        match solve_branch(&branch) {
            Ok(Some(model)) => {
                return Proof {
                    outcome: Outcome::Proved,
                    reason: None,
                    model: Some(model),
                };
            }
            Ok(None) => {}
            Err(reason) => {
                if unknown_reason != Some(Reason::Limit) {
                    unknown_reason = Some(reason);
                }
            }
        }
    }
    if let Some(reason) = unknown_reason {
        unknown(reason)
    } else {
        Proof {
            outcome: Outcome::Disproved,
            reason: None,
            model: Some(json!({})),
        }
    }
}
fn parse_formula(value: &Value, depth: usize) -> Result<Formula, Reason> {
    if depth >= DEPTH_LIMIT {
        return Err(Reason::Limit);
    }
    match value.get("kind").and_then(Value::as_str) {
        Some("literal") if value.pointer("/value/kind").and_then(Value::as_str) == Some("bool") => {
            Ok(Formula::Constant(
                value
                    .pointer("/value/value")
                    .and_then(Value::as_bool)
                    .ok_or(Reason::Unsupported)?,
            ))
        }
        Some("parameter_ref" | "binding_ref" | "self_ref") if is_bool(value.get("type")) => {
            Ok(Formula::Atom(Atom::Bool(variable_name(value)?)))
        }
        Some("unary") if value.get("op").and_then(Value::as_str) == Some("not") => {
            Ok(Formula::Not(Box::new(parse_formula(
                field(value, "operand")?,
                depth + 1,
            )?)))
        }
        Some("binary") => match value.get("op").and_then(Value::as_str) {
            Some("and") => Ok(Formula::And(
                Box::new(parse_formula(field(value, "left")?, depth + 1)?),
                Box::new(parse_formula(field(value, "right")?, depth + 1)?),
            )),
            Some("or") => Ok(Formula::Or(
                Box::new(parse_formula(field(value, "left")?, depth + 1)?),
                Box::new(parse_formula(field(value, "right")?, depth + 1)?),
            )),
            _ => Err(Reason::Unsupported),
        },
        Some("comparison_chain") => {
            let operands = field(value, "operands")?
                .as_array()
                .ok_or(Reason::Unsupported)?;
            let operators = field(value, "operators")?
                .as_array()
                .ok_or(Reason::Unsupported)?;
            if operands.len() < 2 || operands.len() != operators.len() + 1 {
                return Err(Reason::Unsupported);
            }
            let mut result = Formula::Constant(true);
            for (index, operator) in operators.iter().enumerate() {
                let left = affine(&operands[index], depth + 1)?;
                let right = affine(&operands[index + 1], depth + 1)?;
                let atom = match operator.as_str() {
                    Some("equal") => Formula::Atom(Atom::Compare {
                        left,
                        op: Compare::Eq,
                        right,
                    }),
                    Some("not_equal") => Formula::Or(
                        Box::new(Formula::Atom(Atom::Compare {
                            left: left.clone(),
                            op: Compare::Lt,
                            right: right.clone(),
                        })),
                        Box::new(Formula::Atom(Atom::Compare {
                            left,
                            op: Compare::Gt,
                            right,
                        })),
                    ),
                    Some("less") => Formula::Atom(Atom::Compare {
                        left,
                        op: Compare::Lt,
                        right,
                    }),
                    Some("less_equal") => Formula::Atom(Atom::Compare {
                        left,
                        op: Compare::Le,
                        right,
                    }),
                    Some("greater") => Formula::Atom(Atom::Compare {
                        left,
                        op: Compare::Gt,
                        right,
                    }),
                    Some("greater_equal") => Formula::Atom(Atom::Compare {
                        left,
                        op: Compare::Ge,
                        right,
                    }),
                    _ => return Err(Reason::Unsupported),
                };
                result = Formula::And(Box::new(result), Box::new(atom));
            }
            Ok(result)
        }
        _ => Err(Reason::Unsupported),
    }
}
fn affine(value: &Value, depth: usize) -> Result<Affine, Reason> {
    if depth >= DEPTH_LIMIT {
        return Err(Reason::Limit);
    }
    match value.get("kind").and_then(Value::as_str) {
        Some("literal")
            if value.pointer("/value/kind").and_then(Value::as_str) == Some("integer") =>
        {
            value
                .pointer("/value/value")
                .and_then(Value::as_str)
                .and_then(|text| text.parse().ok())
                .map(Affine::constant)
                .ok_or(Reason::Unsupported)
        }
        Some("parameter_ref" | "binding_ref" | "self_ref") => Ok(Affine::variable(
            variable_name(value)?,
            integer_domain(value.get("type")).ok_or(Reason::Unsupported)?,
        )),
        Some("len") => Ok(Affine::variable(
            format!("len({})", variable_name(field(value, "value")?)?),
            (0, i64::MAX),
        )),
        Some("unary") => match value.get("op").and_then(Value::as_str) {
            Some("plus") => affine(field(value, "operand")?, depth + 1),
            Some("minus") => affine(field(value, "operand")?, depth + 1)?
                .scale(-1)
                .ok_or(Reason::Unsupported),
            _ => Err(Reason::Unsupported),
        },
        Some("binary") => {
            let left = affine(field(value, "left")?, depth + 1)?;
            let right = affine(field(value, "right")?, depth + 1)?;
            match value.get("op").and_then(Value::as_str) {
                Some("add") => left.add(right, 1).ok_or(Reason::Unsupported),
                Some("subtract") => left.add(right, -1).ok_or(Reason::Unsupported),
                Some("multiply") if left.terms.is_empty() => {
                    right.scale(left.constant).ok_or(Reason::Unsupported)
                }
                Some("multiply") if right.terms.is_empty() => {
                    left.scale(right.constant).ok_or(Reason::Unsupported)
                }
                _ => Err(Reason::Unsupported),
            }
        }
        _ => Err(Reason::Unsupported),
    }
}
fn formula_nodes(formula: &Formula) -> usize {
    match formula {
        Formula::Constant(_) | Formula::Atom(_) => 1,
        Formula::Not(inner) => 1 + formula_nodes(inner),
        Formula::And(left, right) | Formula::Or(left, right) => {
            1 + formula_nodes(left) + formula_nodes(right)
        }
    }
}

fn expression_budget(value: &Value, depth: usize, nodes: &mut usize) -> Result<(), Reason> {
    if depth >= DEPTH_LIMIT {
        return Err(Reason::Limit);
    }
    *nodes = nodes.checked_add(1).ok_or(Reason::Limit)?;
    if *nodes > NODE_LIMIT {
        return Err(Reason::Limit);
    }
    let descend = |value: &Value, nodes: &mut usize| expression_budget(value, depth + 1, nodes);
    match value.get("kind").and_then(Value::as_str) {
        Some("unary") => descend(field(value, "operand")?, nodes),
        Some("binary") => {
            descend(field(value, "left")?, nodes)?;
            descend(field(value, "right")?, nodes)
        }
        Some("comparison_chain") => {
            for operand in field(value, "operands")?
                .as_array()
                .ok_or(Reason::Unsupported)?
            {
                descend(operand, nodes)?;
            }
            Ok(())
        }
        Some("len") => descend(field(value, "value")?, nodes),
        Some("literal" | "parameter_ref" | "binding_ref" | "self_ref") => Ok(()),
        _ => Err(Reason::Unsupported),
    }
}
fn dnf(formula: &Formula, negated: bool, depth: usize) -> Result<Vec<Branch>, Reason> {
    if depth >= DEPTH_LIMIT {
        return Err(Reason::Limit);
    }
    match formula {
        Formula::Constant(value) => Ok(if *value != negated {
            vec![Vec::new()]
        } else {
            Vec::new()
        }),
        Formula::Atom(Atom::Compare {
            left,
            op: Compare::Eq,
            right,
        }) if negated => Ok(vec![
            vec![(
                Atom::Compare {
                    left: left.clone(),
                    op: Compare::Lt,
                    right: right.clone(),
                },
                false,
            )],
            vec![(
                Atom::Compare {
                    left: left.clone(),
                    op: Compare::Gt,
                    right: right.clone(),
                },
                false,
            )],
        ]),
        Formula::Atom(atom) => Ok(vec![vec![(atom.clone(), negated)]]),
        Formula::Not(inner) => dnf(inner, !negated, depth + 1),
        Formula::And(left, right) if !negated => {
            product(dnf(left, false, depth + 1)?, dnf(right, false, depth + 1)?)
        }
        Formula::Or(left, right) if negated => {
            product(dnf(left, true, depth + 1)?, dnf(right, true, depth + 1)?)
        }
        Formula::And(left, right) => {
            append(dnf(left, true, depth + 1)?, dnf(right, true, depth + 1)?)
        }
        Formula::Or(left, right) => {
            append(dnf(left, false, depth + 1)?, dnf(right, false, depth + 1)?)
        }
    }
}
fn append(mut left: Vec<Branch>, right: Vec<Branch>) -> Result<Vec<Branch>, Reason> {
    if left.len().checked_add(right.len()).ok_or(Reason::Limit)? > BRANCH_LIMIT {
        return Err(Reason::Limit);
    }
    left.extend(right);
    Ok(left)
}
fn product(left: Vec<Branch>, right: Vec<Branch>) -> Result<Vec<Branch>, Reason> {
    if left.len().checked_mul(right.len()).ok_or(Reason::Limit)? > BRANCH_LIMIT {
        return Err(Reason::Limit);
    }
    let mut result = Vec::with_capacity(left.len() * right.len());
    for first in left {
        for second in &right {
            if first.len().checked_add(second.len()).ok_or(Reason::Limit)? > ATOM_LIMIT {
                return Err(Reason::Limit);
            }
            let mut branch = first.clone();
            branch.extend(second.iter().cloned());
            result.push(branch);
        }
    }
    Ok(result)
}
#[derive(Clone, Copy)]
struct Edge {
    from: usize,
    to: usize,
    weight: i64,
}
fn solve_branch(branch: &Branch) -> Result<Option<Value>, Reason> {
    if branch.len() > ATOM_LIMIT {
        return Err(Reason::Limit);
    }
    let mut booleans = BTreeMap::new();
    let mut constraints = Vec::new();
    let mut domains = BTreeMap::new();
    for (atom, negated) in branch {
        match atom {
            Atom::Bool(name) => match booleans.get(name) {
                Some(value) if *value != !*negated => return Ok(None),
                _ => {
                    booleans.insert(name.clone(), !*negated);
                }
            },
            Atom::Compare { left, op, right } => match constraints_for(
                left,
                if *negated { op.invert() } else { *op },
                right,
                &mut domains,
            )? {
                Some(mut values) => constraints.append(&mut values),
                None => return Ok(None),
            },
        }
    }
    if domains
        .len()
        .checked_add(booleans.len())
        .ok_or(Reason::Limit)?
        > SYMBOL_LIMIT
    {
        return Err(Reason::Limit);
    }
    let names = domains.keys().cloned().collect::<Vec<_>>();
    let indices = names
        .iter()
        .enumerate()
        .map(|(index, name)| (name.clone(), index + 1))
        .collect::<BTreeMap<_, _>>();
    for (name, (minimum, maximum)) in &domains {
        if *maximum != i64::MAX {
            constraints.push(("$zero".to_owned(), name.clone(), *maximum));
        }
        if *minimum != i64::MIN {
            constraints.push((name.clone(), "$zero".to_owned(), -minimum));
        }
    }
    let mut edges = constraints
        .into_iter()
        .map(|(from, to, weight)| Edge {
            from: if from == "$zero" { 0 } else { indices[&from] },
            to: if to == "$zero" { 0 } else { indices[&to] },
            weight,
        })
        .collect::<Vec<_>>();
    edges.sort_by_key(|edge| (edge.from, edge.to, edge.weight));
    let mut distance = vec![0_i64; names.len() + 1];
    for iteration in 0..distance.len() {
        let mut changed = false;
        for edge in &edges {
            let candidate = distance[edge.from]
                .checked_add(edge.weight)
                .ok_or(Reason::Unsupported)?;
            if candidate < distance[edge.to] {
                distance[edge.to] = candidate;
                changed = true;
                if iteration + 1 == distance.len() {
                    return Ok(None);
                }
            }
        }
        if !changed {
            break;
        }
    }
    let zero = distance[0];
    let normalized = distance
        .iter()
        .map(|value| value.checked_sub(zero).ok_or(Reason::Unsupported))
        .collect::<Result<Vec<_>, _>>()?;
    if !edges.iter().all(|edge| {
        normalized[edge.to]
            <= normalized[edge.from]
                .checked_add(edge.weight)
                .unwrap_or(i64::MAX)
    }) {
        return Err(Reason::Unsupported);
    }
    let mut model = Map::new();
    for name in names {
        model.insert(name.clone(), json!(normalized[indices[&name]]));
    }
    for (name, value) in booleans {
        model.insert(name, json!(value));
    }
    Ok(Some(Value::Object(model)))
}
/// Returns `None` for a contradiction. Edges are `to - from <= weight`.
fn constraints_for(
    left: &Affine,
    op: Compare,
    right: &Affine,
    domains: &mut BTreeMap<String, (i64, i64)>,
) -> Result<Option<Vec<(String, String, i64)>>, Reason> {
    let difference = left
        .clone()
        .add(right.clone(), -1)
        .ok_or(Reason::Unsupported)?;
    for (name, domain) in &difference.domains {
        if domains.get(name).is_some_and(|old| *old != *domain) {
            return Err(Reason::Unsupported);
        }
        domains.insert(name.clone(), *domain);
    }
    if difference.terms.is_empty() {
        return Ok(
            if match op {
                Compare::Eq => difference.constant == 0,
                Compare::Lt => difference.constant < 0,
                Compare::Le => difference.constant <= 0,
                Compare::Gt => difference.constant > 0,
                Compare::Ge => difference.constant >= 0,
            } {
                Some(Vec::new())
            } else {
                None
            },
        );
    }
    let edge = |reverse: bool, strict: bool| -> Result<(String, String, i64), Reason> {
        let mut terms = difference.terms.clone();
        let constant = if reverse {
            difference
                .constant
                .checked_neg()
                .ok_or(Reason::Unsupported)?
        } else {
            difference.constant
        };
        if reverse {
            for value in terms.values_mut() {
                *value = value.checked_neg().ok_or(Reason::Unsupported)?;
            }
        }
        let mut positive = None;
        let mut negative = None;
        for (name, coefficient) in terms {
            match coefficient {
                1 if positive.is_none() => positive = Some(name),
                -1 if negative.is_none() => negative = Some(name),
                _ => return Err(Reason::Unsupported),
            }
        }
        let adjusted = if strict {
            constant.checked_add(1).ok_or(Reason::Unsupported)?
        } else {
            constant
        };
        Ok((
            negative.unwrap_or_else(|| "$zero".to_owned()),
            positive.unwrap_or_else(|| "$zero".to_owned()),
            adjusted.checked_neg().ok_or(Reason::Unsupported)?,
        ))
    };
    Ok(Some(match op {
        Compare::Le => vec![edge(false, false)?],
        Compare::Lt => vec![edge(false, true)?],
        Compare::Ge => vec![edge(true, false)?],
        Compare::Gt => vec![edge(true, true)?],
        Compare::Eq => vec![edge(false, false)?, edge(true, false)?],
    }))
}
fn is_bool(value: Option<&Value>) -> bool {
    value
        .and_then(|type_value| type_value.get("kind"))
        .and_then(Value::as_str)
        == Some("primitive")
        && value
            .and_then(|type_value| type_value.get("name"))
            .and_then(Value::as_str)
            == Some("bool")
}
fn integer_domain(value: Option<&Value>) -> Option<(i64, i64)> {
    Some(match value?.get("name")?.as_str()? {
        "i8" => (i8::MIN as i64, i8::MAX as i64),
        "i16" => (i16::MIN as i64, i16::MAX as i64),
        "i32" => (i32::MIN as i64, i32::MAX as i64),
        "i64" => (i64::MIN, i64::MAX),
        "u8" => (0, u8::MAX as i64),
        "u16" => (0, u16::MAX as i64),
        "u32" => (0, u32::MAX as i64),
        "u64" => return None,
        _ => return None,
    })
}
fn variable_name(value: &Value) -> Result<String, Reason> {
    match value.get("kind").and_then(Value::as_str) {
        Some("self_ref") => Ok("$self".to_owned()),
        Some("parameter_ref" | "binding_ref") => value
            .get("symbol")
            .and_then(Value::as_str)
            .map(str::to_owned)
            .ok_or(Reason::Unsupported),
        _ => Err(Reason::Unsupported),
    }
}

fn local_name(name: &str) -> &str {
    name.rsplit('.').next().unwrap_or(name)
}
fn field<'a>(value: &'a Value, name: &str) -> Result<&'a Value, Reason> {
    value.get(name).ok_or(Reason::Unsupported)
}
fn required_string<'a>(value: &'a Value, name: &str, context: &str) -> Result<&'a str, String> {
    value
        .get(name)
        .and_then(Value::as_str)
        .ok_or_else(|| format!("{context}: {name} is not a string"))
}

fn reachable_refinements(
    ir: &CanonicalIr,
    selected: &BTreeSet<String>,
) -> Result<BTreeSet<String>, String> {
    let mut declarations = BTreeMap::new();
    for module in &ir.modules {
        let root = crate::ir::load(&module.bytes)?;
        for declaration in root
            .get("declarations")
            .and_then(Value::as_array)
            .ok_or("canonical declaration array is missing")?
        {
            if let Some(name) = declaration.get("name").and_then(Value::as_str) {
                declarations.insert(name.to_owned(), declaration.clone());
            }
        }
    }
    let mut needed = BTreeSet::new();
    for symbol in selected {
        let Some(function) = declarations.get(symbol) else {
            continue;
        };
        if function.get("kind").and_then(Value::as_str) != Some("function") {
            continue;
        }
        for parameter in function
            .get("parameters")
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
        {
            named_types(parameter.get("type"), &mut needed);
        }
        named_types(function.get("return_type"), &mut needed);
    }
    let mut expanded = BTreeSet::new();
    while let Some(name) = needed
        .iter()
        .find(|name| !expanded.contains(*name))
        .cloned()
    {
        expanded.insert(name.clone());
        if declarations
            .get(&name)
            .and_then(|declaration| declaration.get("kind"))
            .and_then(Value::as_str)
            == Some("newtype")
        {
            named_types(declarations[&name].get("carrier"), &mut needed);
        }
    }
    Ok(expanded)
}

fn named_types(value: Option<&Value>, names: &mut BTreeSet<String>) {
    let Some(value) = value else { return };
    if value.get("kind").and_then(Value::as_str) == Some("named") {
        if let Some(name) = value.get("name").and_then(Value::as_str) {
            names.insert(name.to_owned());
        }
    }
    match value {
        Value::Array(values) => {
            for value in values {
                named_types(Some(value), names);
            }
        }
        Value::Object(values) => {
            for value in values.values() {
                named_types(Some(value), names);
            }
        }
        _ => {}
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    fn integer(value: i64) -> Value {
        json!({"kind":"literal","value":{"kind":"integer","value":value.to_string()}})
    }
    fn bool_(value: bool) -> Value {
        json!({"kind":"literal","value":{"kind":"bool","value":value}})
    }
    fn self_ref() -> Value {
        json!({"kind":"self_ref","type":{"kind":"primitive","name":"i8"}})
    }
    fn compare(left: Value, op: &str, right: Value) -> Value {
        json!({"kind":"comparison_chain","operands":[left,right],"operators":[op]})
    }
    fn and(left: Value, right: Value) -> Value {
        json!({"kind":"binary","op":"and","left":left,"right":right})
    }
    #[test]
    fn proves_tautology_and_models_integer_refinement() {
        assert_eq!(
            prove_satisfiable(&compare(self_ref(), "greater", integer(0))).outcome,
            Outcome::Proved
        );
        assert_eq!(
            prove_satisfiable(&compare(self_ref(), "equal", self_ref())).outcome,
            Outcome::Proved
        );
    }
    #[test]
    fn disproves_contradiction_and_respects_fixed_width_domains() {
        assert_eq!(
            prove_satisfiable(&and(
                compare(self_ref(), "greater", integer(127)),
                compare(self_ref(), "less", integer(-128))
            ))
            .outcome,
            Outcome::Disproved
        );
    }
    #[test]
    fn refuses_float_and_nonlinear_claims() {
        let float = json!({"kind":"comparison_chain","operands":[{"kind":"literal","value":{"kind":"f32","bits":"00000000"}},integer(0)],"operators":["equal"]});
        assert_eq!(prove_satisfiable(&float).outcome, Outcome::Unknown);
        assert_eq!(
            prove_satisfiable(&compare(
                json!({"kind":"binary","op":"multiply","left":self_ref(),"right":self_ref()}),
                "equal",
                integer(1)
            ))
            .outcome,
            Outcome::Unknown
        );
    }
    #[test]
    fn folds_closed_booleans_and_reports_limit_deterministically() {
        assert_eq!(prove_satisfiable(&bool_(true)).outcome, Outcome::Proved);
        assert_eq!(prove_satisfiable(&bool_(false)).outcome, Outcome::Disproved);
        let mut expression = bool_(true);
        for _ in 0..DEPTH_LIMIT {
            expression = json!({"kind":"unary","op":"not","operand":expression});
        }
        let first = prove_satisfiable(&expression);
        assert_eq!(first.outcome, Outcome::Unknown);
        assert_eq!(first.reason, prove_satisfiable(&expression).reason);
    }
}

#[cfg(test)]
mod safety_tests {
    use super::*;

    fn integer(value: i64) -> Value {
        json!({"kind":"literal","value":{"kind":"integer","value":value.to_string()}})
    }

    fn compare(left: Value, op: &str, right: Value) -> Value {
        json!({"kind":"comparison_chain","operands":[left,right],"operators":[op]})
    }

    #[test]
    fn never_proves_generic_or_negated_equality_as_a_model() {
        let generic = json!({
            "kind":"parameter_ref",
            "symbol":"generic.value",
            "type":{"kind":"type_parameter","name":"T"}
        });
        assert_eq!(
            prove_satisfiable(&compare(generic, "equal", integer(0))).outcome,
            Outcome::Unknown
        );
        let value = json!({
            "kind":"parameter_ref",
            "symbol":"app.value",
            "type":{"kind":"primitive","name":"i8"}
        });
        let impossible = json!({
            "kind":"binary",
            "op":"and",
            "left":compare(value.clone(), "equal", integer(0)),
            "right":{"kind":"unary","op":"not","operand":compare(value, "equal", integer(0))}
        });
        assert_eq!(prove_satisfiable(&impossible).outcome, Outcome::Disproved);
    }

    #[test]
    fn rejects_u64_claims_outside_the_signed_solver_domain_and_normalizes_models() {
        let unsigned = json!({
            "kind":"parameter_ref",
            "symbol":"app.value",
            "type":{"kind":"primitive","name":"u64"}
        });
        assert_eq!(
            prove_satisfiable(&compare(unsigned, "greater", integer(i64::MAX))).outcome,
            Outcome::Unknown
        );

        let signed = json!({
            "kind":"parameter_ref",
            "symbol":"app.value",
            "type":{"kind":"primitive","name":"i8"}
        });
        let proof = prove_satisfiable(&compare(signed, "greater", integer(0)));
        assert_eq!(proof.outcome, Outcome::Proved);
        assert_eq!(proof.model.expect("witness")["app.value"], 1);
    }

    #[test]
    fn bounds_clause_conjunctions_before_allocating_an_unbounded_formula() {
        let clauses = (0..NODE_LIMIT)
            .map(|_| json!({"kind":"literal","value":{"kind":"bool","value":true}}))
            .collect::<Vec<_>>();
        let references = clauses.iter().collect::<Vec<_>>();
        assert_eq!(prove_all_satisfiable(&references).outcome, Outcome::Unknown);
    }
}
