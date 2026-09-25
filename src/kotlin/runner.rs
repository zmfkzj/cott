use std::collections::{BTreeMap, BTreeSet};
use std::fmt::Write as _;

use hmac::{Hmac, Mac};
use sha2::Sha256;

use serde_json::Value;

use crate::contract_test::{Classification, ContractTestStrategy};
use crate::manifest::VerificationConfig;

use super::emit;
use super::expressions;
use super::types::{self, KotlinTypeContext};
use super::{KotlinCallable, KotlinPlan};

const EVENT_PREFIX: &str = "COTT_KOTLIN_VERIFY:";
pub(crate) const EVIDENCE_KEY_BYTES: usize = 32;
const RUNNER_PACKAGE: &str = "cott_verification";
const RUNNER_FILE: &str = "CottContractRunner.kt";
const MAX_RUNNER_CASES: u64 = 4096;
const MAX_RUNNER_SOURCE_BYTES: usize = 8 * 1024 * 1024;
const MAX_CANDIDATE_SEARCH_STEPS: usize = 4096;
const MAX_CANDIDATE_SEARCH_DEPTH: usize = 64;
pub(crate) const MAIN_CLASS: &str = "cott_verification.CottContractRunnerKt";

#[derive(Clone, Debug)]
pub(crate) struct RunnerProgram {
    pub source: String,
    pub file_name: &'static str,
    pub expected_cases: BTreeMap<String, u32>,
    pub expected_cancellations: BTreeSet<(String, u32)>,
    pub unavailable: BTreeMap<String, String>,
    pub expected_scenarios: BTreeSet<String>,
    pub needs_loopback: bool,
}

#[derive(Clone, Debug)]
struct CandidateContext<'a> {
    plan: &'a KotlinPlan,
    declarations: BTreeMap<&'a str, &'a Value>,
    consts: BTreeMap<String, String>,
    type_arguments: BTreeMap<String, Value>,
    node_limit: usize,
    container_limit: usize,
}
struct CandidateSearchBudget {
    remaining: usize,
}

impl CandidateSearchBudget {
    fn new() -> Self {
        Self {
            remaining: MAX_CANDIDATE_SEARCH_STEPS,
        }
    }

    fn enter(&mut self, depth: usize) -> Result<(), ()> {
        if depth > MAX_CANDIDATE_SEARCH_DEPTH || self.remaining == 0 {
            return Err(());
        }
        self.remaining -= 1;
        Ok(())
    }
}

#[derive(Clone, Debug)]
struct Invocation {
    prelude: Vec<String>,
    call: String,
    return_type: Value,
    asynchronous: bool,
}

pub(crate) fn render(
    plan: &KotlinPlan,
    strategies: &[ContractTestStrategy],
    verification: &VerificationConfig,
) -> Result<RunnerProgram, String> {
    let declarations = declaration_index(plan)?;
    let strategy_by_symbol = strategies
        .iter()
        .map(|strategy| (strategy.symbol.as_str(), strategy))
        .collect::<BTreeMap<_, _>>();
    let mut source = runner_prelude();
    let mut main_lines = Vec::new();
    let mut expected_cancellations = BTreeSet::new();
    let mut expected_cases = BTreeMap::new();
    let mut unavailable = BTreeMap::new();
    let mut expected_scenarios = BTreeSet::new();
    let mut needs_loopback = false;

    for callable in plan.callables() {
        let Some(strategy) = strategy_by_symbol.get(callable.symbol.as_str()).copied() else {
            continue;
        };
        if !callable_is_public(&callable) {
            unavailable.insert(
                callable.symbol.clone(),
                "selected implementation helper is not a public consumer facade".to_owned(),
            );
            continue;
        }
        if strategy.classification == Classification::Effectful {
            unavailable.insert(
                callable.symbol.clone(),
                "effectful callable requires an enforceable canonical scenario".to_owned(),
            );
            continue;
        }
        if strategy.classification == Classification::Never {
            unavailable.insert(
                callable.symbol.clone(),
                "Never callable cannot be safely invoked by bounded value generation".to_owned(),
            );
            continue;
        }
        match render_callable_cases(
            plan,
            &callable,
            &declarations,
            verification,
            &mut source,
            &mut main_lines,
            &mut expected_cancellations,
        ) {
            Ok(count) if count > 0 => {
                expected_cases.insert(callable.symbol.clone(), count);
            }
            Ok(_) => {
                unavailable.insert(
                    callable.symbol.clone(),
                    "bounded candidate generation produced no well-typed input".to_owned(),
                );
            }
            Err(reason) => {
                unavailable.insert(callable.symbol.clone(), reason);
            }
        }
    }

    for strategy in strategies {
        if !strategy.symbol.ends_with(".init") {
            continue;
        }
        let owner_symbol = strategy.symbol.trim_end_matches(".init");
        let Some(owner) = declarations.get(owner_symbol).copied() else {
            unavailable.insert(
                strategy.symbol.clone(),
                "initializer owner is absent from canonical IR".to_owned(),
            );
            continue;
        };
        if owner.get("kind").and_then(Value::as_str) != Some("impl")
            || owner.get("public").and_then(Value::as_bool) != Some(true)
        {
            unavailable.insert(
                strategy.symbol.clone(),
                "initializer owner is not a public Kotlin facade".to_owned(),
            );
            continue;
        }
        match render_initializer_cases(
            plan,
            owner_symbol,
            owner,
            &declarations,
            verification,
            &mut source,
            &mut main_lines,
        ) {
            Ok(count) if count > 0 => {
                expected_cases.insert(strategy.symbol.clone(), count);
            }
            Ok(_) => {
                unavailable.insert(
                    strategy.symbol.clone(),
                    "bounded initializer generation produced no well-typed input".to_owned(),
                );
            }
            Err(reason) => {
                unavailable.insert(strategy.symbol.clone(), reason);
            }
        }
    }

    emit::with_type_context(plan, |types| {
        for strategy in strategies {
            let Some(scenario) = strategy.scenario.as_ref() else {
                continue;
            };
            match render_scenario(strategy, &declarations, types, &mut source, &mut main_lines) {
                Ok(loopback) => {
                    expected_scenarios.insert(scenario.id.clone());
                    needs_loopback |= loopback;
                }
                Err(reason) => {
                    unavailable.insert(strategy.symbol.clone(), reason);
                }
            }
        }
    })?;
    let total_cases = expected_cases
        .values()
        .map(|value| u64::from(*value))
        .sum::<u64>();
    if total_cases > MAX_RUNNER_CASES {
        return Err(format!(
            "bounded Kotlin runner case limit exceeded ({total_cases} > {MAX_RUNNER_CASES})"
        ));
    }
    if source.len() > MAX_RUNNER_SOURCE_BYTES {
        return Err(format!(
            "bounded Kotlin runner source limit exceeded ({} > {MAX_RUNNER_SOURCE_BYTES})",
            source.len()
        ));
    }

    source.push_str("\npublic fun main(): kotlin.Unit {\n");
    source.push_str("    val evidence = EvidenceWriter(readEvidenceKey(), java.lang.System.out)\n");
    for line in main_lines {
        writeln!(source, "    {line}").expect("writing to String cannot fail");
    }
    source.push_str("    emitEvidence(evidence, \"{\\\"kind\\\":\\\"done\\\"}\")\n");
    source.push_str("}\n");

    Ok(RunnerProgram {
        source,
        file_name: RUNNER_FILE,
        expected_cases,
        expected_cancellations,
        unavailable,
        expected_scenarios,
        needs_loopback,
    })
}

fn runner_prelude() -> String {
    format!(
        r#"@file:Suppress("UNUSED_VARIABLE", "UNCHECKED_CAST")

package {RUNNER_PACKAGE}

import cott_runtime.CottClauseObservation
import cott_runtime.CottContractViolation
import cott_runtime.CottFixtureContext
import cott_runtime.CottFixtureKey
import cott_runtime.CottObservation
import cott_runtime.CottRuntime
import java.math.BigInteger
import java.nio.file.Files
import java.nio.file.LinkOption
import java.nio.file.Path
import java.io.PrintStream
import java.nio.ByteBuffer
import java.nio.charset.StandardCharsets
import java.util.Comparator
import java.util.concurrent.CancellationException
import javax.crypto.Mac
import javax.crypto.spec.SecretKeySpec
import kotlinx.coroutines.CoroutineStart
import kotlinx.coroutines.async
import kotlinx.coroutines.cancelAndJoin
import kotlinx.coroutines.runBlocking
import kotlinx.coroutines.supervisorScope
import kotlinx.coroutines.withTimeout
import kotlinx.coroutines.yield

private const val EVENT_PREFIX: kotlin.String = "{EVENT_PREFIX}"
private const val EVIDENCE_KEY_BYTES: kotlin.Int = {EVIDENCE_KEY_BYTES}
private const val HEX_DIGITS: kotlin.String = "0123456789abcdef"

private class EvidenceWriter(secret: kotlin.ByteArray, private val output: PrintStream) {{
    private val authenticator: Mac = Mac.getInstance("HmacSHA256")
    private var sequence: kotlin.Long = 0

    init {{
        val material = secret.copyOf()
        try {{
            authenticator.init(SecretKeySpec(material, "HmacSHA256"))
        }} finally {{
            material.fill(0)
            secret.fill(0)
        }}
    }}

    @Synchronized
    fun emit(payload: kotlin.String) {{
        val payloadBytes = payload.toByteArray(StandardCharsets.UTF_8)
        authenticator.update(ByteBuffer.allocate(java.lang.Long.BYTES).putLong(sequence).array())
        val tag = authenticator.doFinal(payloadBytes)
        output.println("\n" + EVENT_PREFIX + sequence + ":" + authHex(tag) + ":" + payload)
        if (output.checkError()) throw IllegalStateException("write authenticated Kotlin evidence")
        sequence = java.lang.Math.addExact(sequence, 1)
    }}
}}

private fun authHex(value: kotlin.ByteArray): kotlin.String {{
    val encoded = kotlin.CharArray(value.size * 2)
    for (index in value.indices) {{
        val byte = value[index].toInt() and 0xff
        encoded[index * 2] = HEX_DIGITS[byte ushr 4]
        encoded[index * 2 + 1] = HEX_DIGITS[byte and 0x0f]
    }}
    return encoded.concatToString()
}}

private fun readEvidenceKey(): kotlin.ByteArray {{
    val secret = kotlin.ByteArray(EVIDENCE_KEY_BYTES)
    var offset = 0
    while (offset < secret.size) {{
        val read = java.lang.System.`in`.read(secret, offset, secret.size - offset)
        if (read < 0) throw IllegalStateException("Kotlin evidence key was truncated")
        if (read == 0) continue
        offset += read
    }}
    return secret
}}

private fun emitEvidence(evidence: EvidenceWriter, payload: kotlin.String) {{
    evidence.emit(payload)
}}

private data class CandidateConst(override val value: BigInteger) : cott_runtime.CottConst

private fun json(value: kotlin.String?): kotlin.String {{
    if (value == null) return "null"
    val out = StringBuilder("\"")
    for (character in value) when (character) {{
        '"' -> out.append("\\\"")
        '\\' -> out.append("\\\\")
        '\b' -> out.append("\\b")
        '\u000c' -> out.append("\\f")
        '\n' -> out.append("\\n")
        '\r' -> out.append("\\r")
        '\t' -> out.append("\\t")
        else -> if (character.code < 0x20) out.append("\\u").append(character.code.toString(16).padStart(4, '0')) else out.append(character)
    }}
    return out.append('"').toString()
}}

private fun observations(value: CottObservation): kotlin.String = value.observations().joinToString(
    prefix = "[", postfix = "]", separator = ",",
) {{ observation ->
    "{{\"symbol\":${{json(observation.symbol)}},\"clause\":${{json(observation.clause)}},\"phase\":${{json(observation.phase)}},\"passed\":${{observation.passed}}}}"
}}

private fun emitCase(evidence: EvidenceWriter, symbol: kotlin.String, caseId: kotlin.Int, status: kotlin.String, observation: CottObservation, error: CottContractViolation? = null) {{
    emitEvidence(evidence, "{{\"kind\":\"case\",\"symbol\":${{json(symbol)}},\"case\":$caseId,\"status\":${{json(status)}},\"phase\":${{json(error?.phase)}},\"clause\":${{json(error?.clause)}},\"error_symbol\":${{json(error?.symbol)}},\"observations\":${{observations(observation)}}}}")
}}

private fun candidateUnavailable(evidence: EvidenceWriter, symbol: kotlin.String, caseId: kotlin.Int, error: CottContractViolation) {{
    emitEvidence(evidence, "{{\"kind\":\"case\",\"symbol\":${{json(symbol)}},\"case\":$caseId,\"status\":\"candidate_unavailable\",\"phase\":${{json(error.phase)}},\"clause\":${{json(error.clause)}},\"error_symbol\":${{json(error.symbol)}},\"observations\":[]}}")
}}

private fun observedCase(evidence: EvidenceWriter, symbol: kotlin.String, caseId: kotlin.Int, block: () -> kotlin.Unit) {{
    val observation = CottObservation()
    try {{
        CottRuntime.withTestObservation(observation, block)
        emitCase(evidence, symbol, caseId, "passed", observation)
    }} catch (error: CottContractViolation) {{
        emitCase(evidence, symbol, caseId, if (error.phase == "requires") "ineligible" else "failed", observation, error)
    }} catch (_: CancellationException) {{
        emitCase(evidence, symbol, caseId, "unexpected_cancellation", observation)
    }} catch (_: kotlin.Throwable) {{
        emitCase(evidence, symbol, caseId, "unexpected_exception", observation)
    }}
}}

private fun observedSuspendCase(evidence: EvidenceWriter, symbol: kotlin.String, caseId: kotlin.Int, timeoutMs: kotlin.Long, block: suspend () -> kotlin.Unit) {{
    val observation = CottObservation()
    try {{
        CottRuntime.withTestObservation(observation) {{
            runBlocking {{
                withTimeout(timeoutMs) {{ CottRuntime.withTestObservationSuspend(observation, block) }}
            }}
        }}
        emitCase(evidence, symbol, caseId, "passed", observation)
    }} catch (error: CottContractViolation) {{
        emitCase(evidence, symbol, caseId, if (error.phase == "requires") "ineligible" else "failed", observation, error)
    }} catch (_: kotlinx.coroutines.TimeoutCancellationException) {{
        emitCase(evidence, symbol, caseId, "timeout", observation)
    }} catch (_: CancellationException) {{
        emitCase(evidence, symbol, caseId, "unexpected_cancellation", observation)
    }} catch (_: kotlin.Throwable) {{
        emitCase(evidence, symbol, caseId, "unexpected_exception", observation)
    }}
}}

private fun cancellationCase(evidence: EvidenceWriter, symbol: kotlin.String, caseId: kotlin.Int, timeoutMs: kotlin.Long, block: suspend () -> kotlin.Unit) {{
    var status = "not_applicable"
    try {{
        runBlocking {{
            withTimeout(timeoutMs) {{
                supervisorScope {{
                    val task = async(start = CoroutineStart.UNDISPATCHED) {{ block() }}
                    yield()
                    if (task.isActive) {{
                        task.cancelAndJoin()
                        status = "passed"
                    }} else {{
                        try {{ task.await() }} catch (error: CottContractViolation) {{
                            status = if (error.phase == "requires") "candidate_unavailable" else "failed"
                        }} catch (_: kotlin.Throwable) {{ status = "failed" }}
                    }}
                }}
            }}
        }}
    }} catch (error: CottContractViolation) {{
        status = if (error.phase == "requires") "candidate_unavailable" else "failed"
    }} catch (_: kotlin.Throwable) {{ status = "failed" }}
    emitEvidence(evidence, "{{\"kind\":\"cancellation\",\"symbol\":${{json(symbol)}},\"case\":$caseId,\"status\":${{json(status)}}}}")
}}

private fun emitScenario(evidence: EvidenceWriter, id: kotlin.String, status: kotlin.String, observation: CottObservation, assertions: kotlin.Int) {{
    emitEvidence(evidence, "{{\"kind\":\"scenario\",\"scenario_id\":${{json(id)}},\"status\":${{json(status)}},\"assertions\":$assertions,\"observations\":${{observations(observation)}}}}")
}}

private fun deleteTree(root: Path) {{
    if (!Files.exists(root, LinkOption.NOFOLLOW_LINKS)) return
    Files.walk(root).use {{ paths -> paths.sorted(Comparator.reverseOrder()).forEach {{ path -> Files.delete(path) }} }}
}}

private fun auditFixtureRoot(root: Path, maximumFiles: kotlin.Long, maximumBytes: kotlin.Long) {{
    var files = 0L
    var bytes = 0L
    Files.walk(root).use {{ paths ->
        paths.forEach {{ path ->
            if (Files.isSymbolicLink(path)) throw IllegalStateException("fixture filesystem contains a symbolic link")
            if (Files.isRegularFile(path, LinkOption.NOFOLLOW_LINKS)) {{
                files += 1
                bytes += Files.size(path)
            }}
        }}
    }}
    check(files <= maximumFiles && bytes <= maximumBytes) {{ "fixture filesystem exceeds configured limits" }}
}}

private fun hex(value: kotlin.String): kotlin.ByteArray {{
    require(value.length % 2 == 0)
    return kotlin.ByteArray(value.length / 2) {{ index -> value.substring(index * 2, index * 2 + 2).toInt(16).toByte() }}
}}
"#
    )
}

fn declaration_index(plan: &KotlinPlan) -> Result<BTreeMap<&str, &Value>, String> {
    let mut declarations = BTreeMap::new();
    for module in &plan.modules {
        for declaration in &module.declarations {
            let Some(name) = declaration.get("name").and_then(Value::as_str) else {
                continue;
            };
            if declarations.insert(name, declaration).is_some() {
                return Err(format!("duplicate canonical declaration `{name}`"));
            }
        }
    }
    Ok(declarations)
}

fn callable_is_public(callable: &KotlinCallable) -> bool {
    callable.owner.as_ref().map_or_else(
        || callable.declaration.get("public").and_then(Value::as_bool) == Some(true),
        |owner| owner.get("public").and_then(Value::as_bool) == Some(true),
    )
}

fn render_callable_cases<'a>(
    plan: &'a KotlinPlan,
    callable: &KotlinCallable,
    declarations: &BTreeMap<&'a str, &'a Value>,
    verification: &VerificationConfig,
    source: &mut String,
    main_lines: &mut Vec<String>,
    expected_cancellations: &mut BTreeSet<(String, u32)>,
) -> Result<u32, String> {
    let mut context = candidate_context(plan, callable, declarations)?;
    let parameters = callable
        .declaration
        .get("parameters")
        .and_then(Value::as_array)
        .ok_or_else(|| format!("callable `{}` has no canonical parameters", callable.symbol))?;
    for generic in callable
        .declaration
        .get("generics")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter(|generic| generic.get("kind").and_then(Value::as_str) == Some("type"))
    {
        let name = generic
            .get("name")
            .and_then(Value::as_str)
            .ok_or_else(|| format!("callable `{}` has a nameless type generic", callable.symbol))?;
        if !parameters.iter().any(|parameter| {
            parameter
                .get("type")
                .is_some_and(|ty| contains_type_parameter(ty, name))
        }) {
            return Err(format!(
                "generic `{name}` is not inferable from a public input parameter"
            ));
        }
    }
    let parameter_cases = parameter_candidates(parameters, &mut context)?;
    let constructor_cases = callable
        .owner
        .as_ref()
        .map(|owner| constructor_candidates(owner, &mut context))
        .transpose()?
        .unwrap_or_else(|| vec![Vec::new()]);
    let combinations = product_bounded(
        &[constructor_cases, parameter_cases],
        verification.candidate_limit as usize,
    );
    if combinations.is_empty() {
        return Ok(0);
    }
    let return_type = callable
        .declaration
        .get("return_type")
        .cloned()
        .ok_or_else(|| format!("callable `{}` has no return type", callable.symbol))?;
    let asynchronous = callable
        .declaration
        .get("callable_kind")
        .and_then(Value::as_str)
        == Some("async");
    let mut count = 0u32;
    for combined in combinations {
        let split = combined
            .iter()
            .position(|line| line == "__COTT_PARAMETER_BOUNDARY__")
            .ok_or("internal candidate boundary is missing")?;
        let constructor = &combined[..split];
        let parameter_values = &combined[split + 1..];
        let invocation = invocation(
            callable,
            parameters,
            constructor,
            parameter_values,
            &context,
            return_type.clone(),
            asynchronous,
        )?;
        render_invocation_case(source, &invocation, &callable.symbol, count, verification)?;
        main_lines.push(format!(
            "case_{}_{}(evidence)",
            safe_name(&callable.symbol),
            count
        ));
        if asynchronous {
            main_lines.push(format!(
                "cancellation_case_{}_{}(evidence)",
                safe_name(&callable.symbol),
                count
            ));
            expected_cancellations.insert((callable.symbol.clone(), count));
        }
        count = count.saturating_add(1);
    }
    Ok(count)
}

fn render_initializer_cases<'a>(
    plan: &'a KotlinPlan,
    owner_symbol: &str,
    owner: &Value,
    declarations: &BTreeMap<&'a str, &'a Value>,
    verification: &VerificationConfig,
    source: &mut String,
    main_lines: &mut Vec<String>,
) -> Result<u32, String> {
    let mut context = CandidateContext {
        plan,
        declarations: declarations.clone(),
        consts: BTreeMap::new(),
        type_arguments: BTreeMap::new(),
        node_limit: 64,
        container_limit: 3,
    };
    let cases = constructor_candidates(owner, &mut context)?;
    let parameters = owner
        .pointer("/init/parameters")
        .and_then(Value::as_array)
        .map(Vec::as_slice)
        .unwrap_or_default();
    let symbol = format!("{owner_symbol}.init");
    let mut count = 0u32;
    for arguments in cases
        .into_iter()
        .take(verification.candidate_limit as usize)
    {
        let prelude = parameters
            .iter()
            .zip(&arguments)
            .enumerate()
            .map(|(index, (parameter, value))| {
                typed_candidate("_candidate", index, parameter, value, &context)
            })
            .collect::<Result<Vec<_>, _>>()?;
        let args = parameters
            .iter()
            .enumerate()
            .map(|(index, parameter)| argument_expression("_candidate", index, parameter))
            .collect::<Vec<_>>()
            .join(", ");
        let invocation = Invocation {
            prelude,
            call: format!("{}({args})", qualified(owner_symbol)),
            return_type: serde_json::json!({"kind":"primitive","name":"unit"}),
            asynchronous: false,
        };
        render_invocation_case(source, &invocation, &symbol, count, verification)?;
        main_lines.push(format!("case_{}_{}(evidence)", safe_name(&symbol), count));
        count = count.saturating_add(1);
    }
    Ok(count)
}

fn invocation(
    callable: &KotlinCallable,
    parameters: &[Value],
    constructor: &[String],
    values: &[String],
    context: &CandidateContext<'_>,
    return_type: Value,
    asynchronous: bool,
) -> Result<Invocation, String> {
    if values.len() != parameters.len() {
        return Err("internal Kotlin candidate arity mismatch".to_owned());
    }
    let mut prelude = Vec::new();
    for (name, value) in &context.consts {
        prelude.push(format!(
            "val {} = CandidateConst(java.math.BigInteger({}))",
            quoted(name),
            kotlin_string(value)
        ));
    }
    for (index, (parameter, value)) in parameters.iter().zip(values).enumerate() {
        prelude.push(typed_candidate(
            "_candidate",
            index,
            parameter,
            value,
            context,
        )?);
    }
    let mut arguments = parameters
        .iter()
        .enumerate()
        .map(|(index, parameter)| argument_expression("_candidate", index, parameter))
        .collect::<Vec<_>>();
    arguments.extend(context.consts.keys().map(|name| quoted(name)));
    let call = if let Some(owner) = callable.owner.as_ref() {
        let owner_symbol = owner
            .get("name")
            .and_then(Value::as_str)
            .ok_or("implementation owner has no canonical name")?;
        let constructor_parameters = owner
            .pointer("/init/parameters")
            .and_then(Value::as_array)
            .map(Vec::as_slice)
            .unwrap_or_default();
        if constructor_parameters.len() != constructor.len() {
            return Err("internal Kotlin constructor candidate arity mismatch".to_owned());
        }
        for (index, (parameter, value)) in
            constructor_parameters.iter().zip(constructor).enumerate()
        {
            prelude.push(typed_candidate(
                "_constructor",
                index,
                parameter,
                value,
                context,
            )?);
        }
        let constructor_arguments = constructor_parameters
            .iter()
            .enumerate()
            .map(|(index, parameter)| argument_expression("_constructor", index, parameter))
            .collect::<Vec<_>>()
            .join(", ");
        prelude.push(format!(
            "val _receiver = {}({constructor_arguments})",
            qualified(owner_symbol)
        ));
        format!(
            "_receiver.{}({})",
            quoted(&callable.name),
            arguments.join(", ")
        )
    } else {
        format!("{}({})", qualified(&callable.symbol), arguments.join(", "))
    };
    Ok(Invocation {
        prelude,
        call,
        return_type,
        asynchronous,
    })
}

fn argument_expression(prefix: &str, index: usize, parameter: &Value) -> String {
    let value = format!("{prefix}_{index}");
    match parameter.get("kind").and_then(Value::as_str) {
        Some("vararg") => format!("*arrayOf({value})"),
        Some("kwarg") => {
            format!("cott_runtime.CottKeywordArguments(linkedMapOf(\"value\" to {value}))")
        }
        _ => value,
    }
}

fn typed_candidate(
    prefix: &str,
    index: usize,
    parameter: &Value,
    value: &str,
    context: &CandidateContext<'_>,
) -> Result<String, String> {
    let ty = parameter
        .get("type")
        .ok_or("canonical parameter has no type")?;
    let ty = substitute_type(ty, &context.type_arguments);
    Ok(if contains_const_parameter(&ty) {
        format!("val {prefix}_{index} = {value}")
    } else {
        format!(
            "val {prefix}_{index}: {} = {value}",
            emit::render_type(context.plan, &ty)?
        )
    })
}

fn render_invocation_case(
    source: &mut String,
    invocation: &Invocation,
    symbol: &str,
    case_id: u32,
    verification: &VerificationConfig,
) -> Result<(), String> {
    let function = format!("case_{}_{}", safe_name(symbol), case_id);
    writeln!(
        source,
        "\nprivate fun {function}(evidence: EvidenceWriter) {{"
    )
    .expect("writing to String cannot fail");
    source.push_str("    try {\n");
    for line in &invocation.prelude {
        writeln!(source, "        {line}").expect("writing to String cannot fail");
    }
    let observe = if invocation.asynchronous {
        format!(
            "observedSuspendCase(evidence, {}, {case_id}, {}L)",
            kotlin_string(symbol),
            verification.fixtures.scenario_timeout_ms
        )
    } else {
        format!(
            "observedCase(evidence, {}, {case_id})",
            kotlin_string(symbol)
        )
    };
    writeln!(source, "        {observe} {{").expect("writing to String cannot fail");
    writeln!(source, "            val _result = {}", invocation.call)
        .expect("writing to String cannot fail");
    render_protocol_consumption(
        source,
        &invocation.return_type,
        verification.lifecycle_limit,
        12,
    )?;
    source.push_str("        }\n");
    source.push_str("    } catch (error: CottContractViolation) {\n");
    writeln!(
        source,
        "        candidateUnavailable(evidence, {}, {case_id}, error)",
        kotlin_string(symbol)
    )
    .expect("writing to String cannot fail");
    source.push_str("    }\n}\n");

    if invocation.asynchronous {
        writeln!(
            source,
            "\nprivate fun cancellation_{function}(evidence: EvidenceWriter) {{\n    try {{"
        )
        .expect("writing to String cannot fail");
        for line in &invocation.prelude {
            writeln!(source, "        {line}").expect("writing to String cannot fail");
        }
        writeln!(
            source,
            "        cancellationCase(evidence, {}, {case_id}, {}L) {{ {} ; kotlin.Unit }}",
            kotlin_string(symbol),
            verification.fixtures.scenario_timeout_ms,
            invocation.call
        )
        .expect("writing to String cannot fail");
        source.push_str("    } catch (_: CottContractViolation) {\n");
        writeln!(
            source,
            "        emitEvidence(evidence, \"{{\\\"kind\\\":\\\"cancellation\\\",\\\"symbol\\\":${{json({})}},\\\"case\\\":{case_id},\\\"status\\\":\\\"candidate_unavailable\\\"}}\")",
            kotlin_string(symbol)
        )
        .expect("writing to String cannot fail");
        source.push_str("    }\n}\n");
    }
    Ok(())
}

fn render_protocol_consumption(
    source: &mut String,
    return_type: &Value,
    lifecycle_limit: u32,
    indent: usize,
) -> Result<(), String> {
    let prefix = " ".repeat(indent);
    match return_type.get("kind").and_then(Value::as_str) {
        Some("iterator") => {
            writeln!(source, "{prefix}var _steps = 0").unwrap();
            writeln!(source, "{prefix}while (_steps < {lifecycle_limit} && _result.hasNext()) {{ _result.next(); _steps += 1 }}").unwrap();
            writeln!(source, "{prefix}_result.close()").unwrap();
        }
        Some("generator") => {
            writeln!(source, "{prefix}var _steps = 0").unwrap();
            writeln!(source, "{prefix}while (_steps < {lifecycle_limit}) {{ val _step = _result.nextStep(); _steps += 1; if (_step is cott_runtime.CottGeneratorStep.Return<*>) break }}").unwrap();
            writeln!(source, "{prefix}_result.close()").unwrap();
        }
        Some("async_iterator") => {
            writeln!(source, "{prefix}var _steps = 0").unwrap();
            writeln!(source, "{prefix}while (_steps < {lifecycle_limit}) {{ val _step = _result.next(); _steps += 1; if (_step === cott_runtime.CottStep.Done) break }}").unwrap();
            writeln!(source, "{prefix}_result.close()").unwrap();
        }
        Some("async_generator") => {
            writeln!(source, "{prefix}var _steps = 0").unwrap();
            writeln!(source, "{prefix}while (_steps < {lifecycle_limit}) {{ val _step = _result.next(); _steps += 1; if (_step is cott_runtime.CottGeneratorStep.Return<*>) break }}").unwrap();
            writeln!(source, "{prefix}_result.close()").unwrap();
        }
        Some(_) => {}
        None => return Err("canonical return type is missing kind".to_owned()),
    }
    Ok(())
}

enum TypeConstraint {
    Trait(Value),
    GenericBounds { name: String, bounds: Vec<Value> },
}

fn candidate_context<'a>(
    plan: &'a KotlinPlan,
    callable: &KotlinCallable,
    declarations: &BTreeMap<&'a str, &'a Value>,
) -> Result<CandidateContext<'a>, String> {
    let mut consts = BTreeMap::new();
    let mut type_generics = Vec::new();
    for generic in callable
        .declaration
        .get("generics")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
    {
        let name = generic.get("name").and_then(Value::as_str).ok_or_else(|| {
            format!(
                "callable `{}` has a generic without a name",
                callable.symbol
            )
        })?;
        match generic.get("kind").and_then(Value::as_str) {
            Some("const") => {
                consts.insert(name.to_owned(), "1".to_owned());
            }
            Some("type") => {
                let bounds = generic
                    .get("bounds")
                    .and_then(Value::as_array)
                    .cloned()
                    .unwrap_or_default();
                type_generics.push((name.to_owned(), bounds));
            }
            Some(other) => {
                return Err(format!(
                    "callable `{}` has unsupported generic kind `{other}`",
                    callable.symbol
                ));
            }
            None => {
                return Err(format!(
                    "callable `{}` has malformed generics",
                    callable.symbol
                ));
            }
        }
    }

    let mut constraints = Vec::new();
    for parameter in callable
        .declaration
        .get("parameters")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
    {
        if let Some(ty) = parameter.get("type") {
            collect_trait_constraints(ty, declarations, &mut constraints);
        }
    }
    constraints.extend(
        type_generics
            .iter()
            .filter(|(_, bounds)| !bounds.is_empty())
            .map(|(name, bounds)| TypeConstraint::GenericBounds {
                name: name.clone(),
                bounds: bounds.clone(),
            }),
    );

    let mut search = CandidateSearchBudget::new();
    let mut type_arguments = solve_type_constraints(
        &constraints,
        0,
        declarations,
        BTreeMap::new(),
        &mut search,
    )
    .map_err(|()| {
        format!(
            "callable `{}` candidate constraint search exhausted its bounded work or depth budget",
            callable.symbol
        )
    })?
    .ok_or_else(|| {
        format!(
            "callable `{}` has no coherent public concrete implementation for its trait input constraints",
            callable.symbol
        )
    })?;
    for (name, bounds) in type_generics {
        if bounds.is_empty() {
            type_arguments
                .entry(name)
                .or_insert_with(|| serde_json::json!({"kind":"primitive","name":"i32"}));
        } else if !type_arguments.contains_key(&name) {
            return Err(format!(
                "generic `{name}` has no public concrete implementation satisfying every required bound"
            ));
        }
    }

    Ok(CandidateContext {
        plan,
        declarations: declarations.clone(),
        consts,
        type_arguments,
        node_limit: 64,
        container_limit: 3,
    })
}

fn collect_trait_constraints(
    value: &Value,
    declarations: &BTreeMap<&str, &Value>,
    output: &mut Vec<TypeConstraint>,
) {
    match value {
        Value::Array(values) => {
            for value in values {
                collect_trait_constraints(value, declarations, output);
            }
        }
        Value::Object(object) => {
            let is_trait = object.get("kind").and_then(Value::as_str) == Some("named")
                && object
                    .get("name")
                    .and_then(Value::as_str)
                    .and_then(|name| declarations.get(name))
                    .is_some_and(|declaration| {
                        declaration.get("kind").and_then(Value::as_str) == Some("trait")
                    });
            if is_trait {
                output.push(TypeConstraint::Trait(value.clone()));
            } else {
                for value in object.values() {
                    collect_trait_constraints(value, declarations, output);
                }
            }
        }
        _ => {}
    }
}

fn solve_type_constraints(
    constraints: &[TypeConstraint],
    index: usize,
    declarations: &BTreeMap<&str, &Value>,
    substitutions: BTreeMap<String, Value>,
    search: &mut CandidateSearchBudget,
) -> Result<Option<BTreeMap<String, Value>>, ()> {
    search.enter(index)?;
    let Some(constraint) = constraints.get(index) else {
        return Ok(Some(substitutions));
    };
    match constraint {
        TypeConstraint::Trait(bound) => {
            for (_, matched) in compatible_implementations(
                std::slice::from_ref(bound),
                declarations,
                &substitutions,
                search,
            )? {
                if let Some(result) =
                    solve_type_constraints(constraints, index + 1, declarations, matched, search)?
                {
                    return Ok(Some(result));
                }
            }
            Ok(None)
        }
        TypeConstraint::GenericBounds { name, bounds } => {
            if let Some(argument) = substitutions.get(name) {
                let Some(declaration) = argument
                    .get("name")
                    .and_then(Value::as_str)
                    .and_then(|name| declarations.get(name))
                    .copied()
                else {
                    return Ok(None);
                };
                let Some(matched) = match_implementation_bounds(
                    declaration,
                    bounds,
                    declarations,
                    &substitutions,
                    search,
                )?
                else {
                    return Ok(None);
                };
                return solve_type_constraints(
                    constraints,
                    index + 1,
                    declarations,
                    matched,
                    search,
                );
            }
            for (implementation, mut matched) in
                compatible_implementations(bounds, declarations, &substitutions, search)?
            {
                if let Some(existing) = matched.get(name) {
                    if existing != &implementation {
                        continue;
                    }
                } else {
                    matched.insert(name.clone(), implementation);
                }
                if let Some(result) =
                    solve_type_constraints(constraints, index + 1, declarations, matched, search)?
                {
                    return Ok(Some(result));
                }
            }
            Ok(None)
        }
    }
}

fn implementation_type_for_bound(
    bound: &Value,
    declarations: &BTreeMap<&str, &Value>,
) -> Result<Option<Value>, String> {
    let mut search = CandidateSearchBudget::new();
    let compatible = compatible_implementations(
        std::slice::from_ref(bound),
        declarations,
        &BTreeMap::new(),
        &mut search,
    )
    .map_err(|()| {
        "trait implementation candidate search exhausted its bounded work or depth budget"
            .to_owned()
    })?;
    Ok(compatible
        .into_iter()
        .next()
        .map(|(implementation, _)| implementation))
}

fn compatible_implementations(
    bounds: &[Value],
    declarations: &BTreeMap<&str, &Value>,
    substitutions: &BTreeMap<String, Value>,
    search: &mut CandidateSearchBudget,
) -> Result<Vec<(Value, BTreeMap<String, Value>)>, ()> {
    let mut compatible = Vec::new();
    for declaration in declarations.values() {
        let Some(implementation) = concrete_implementation_type(declaration) else {
            continue;
        };
        if let Some(matched) =
            match_implementation_bounds(declaration, bounds, declarations, substitutions, search)?
        {
            compatible.push((implementation, matched));
        }
    }
    Ok(compatible)
}

fn concrete_implementation_type(declaration: &Value) -> Option<Value> {
    if declaration.get("kind").and_then(Value::as_str) != Some("impl")
        || declaration.get("public").and_then(Value::as_bool) != Some(true)
        || declaration
            .get("generics")
            .and_then(Value::as_array)
            .is_some_and(|generics| !generics.is_empty())
    {
        return None;
    }
    Some(serde_json::json!({
        "kind": "named",
        "name": declaration.get("name").and_then(Value::as_str)?,
        "args": []
    }))
}

fn match_implementation_bounds(
    implementation: &Value,
    bounds: &[Value],
    declarations: &BTreeMap<&str, &Value>,
    substitutions: &BTreeMap<String, Value>,
    search: &mut CandidateSearchBudget,
) -> Result<Option<BTreeMap<String, Value>>, ()> {
    let implemented = implemented_trait_refs(implementation, declarations);
    match_bound_at(bounds, 0, &implemented, substitutions.clone(), search)
}

fn match_bound_at(
    bounds: &[Value],
    index: usize,
    implemented: &[Value],
    substitutions: BTreeMap<String, Value>,
    search: &mut CandidateSearchBudget,
) -> Result<Option<BTreeMap<String, Value>>, ()> {
    search.enter(index)?;
    let Some(bound) = bounds.get(index) else {
        return Ok(Some(substitutions));
    };
    for actual in implemented {
        let mut matched = substitutions.clone();
        if match_type_pattern(bound, actual, &mut matched, search, 0)?
            && let Some(result) = match_bound_at(bounds, index + 1, implemented, matched, search)?
        {
            return Ok(Some(result));
        }
    }
    Ok(None)
}

fn implemented_trait_refs(
    implementation: &Value,
    declarations: &BTreeMap<&str, &Value>,
) -> Vec<Value> {
    let direct = implementation
        .get("traits")
        .and_then(Value::as_array)
        .cloned()
        .unwrap_or_default();
    let mut implemented = Vec::new();
    for trait_ref in direct {
        if !implemented.contains(&trait_ref) {
            implemented.push(trait_ref.clone());
        }
        let Some(trait_name) = trait_ref.get("name").and_then(Value::as_str) else {
            continue;
        };
        let Some(declaration) = declarations.get(trait_name).copied() else {
            continue;
        };
        let Ok(substitutions) = named_substitutions(declaration, &trait_ref) else {
            continue;
        };
        for inherited in declaration
            .get("closure")
            .and_then(Value::as_array)
            .into_iter()
            .flatten()
        {
            let inherited = substitute_type(inherited, &substitutions);
            if !implemented.contains(&inherited) {
                implemented.push(inherited);
            }
        }
    }
    implemented
}

fn match_type_pattern(
    pattern: &Value,
    actual: &Value,
    substitutions: &mut BTreeMap<String, Value>,
    search: &mut CandidateSearchBudget,
    depth: usize,
) -> Result<bool, ()> {
    search.enter(depth)?;
    if pattern.get("kind").and_then(Value::as_str) == Some("type_parameter") {
        let Some(name) = pattern.get("name").and_then(Value::as_str) else {
            return Ok(false);
        };
        if let Some(existing) = substitutions.get(name) {
            let existing = substitute_type(existing, substitutions);
            return Ok(&existing == actual);
        }
        substitutions.insert(name.to_owned(), actual.clone());
        return Ok(true);
    }
    match (pattern, actual) {
        (Value::Array(pattern), Value::Array(actual)) => {
            if pattern.len() != actual.len() {
                return Ok(false);
            }
            for (pattern, actual) in pattern.iter().zip(actual) {
                if !match_type_pattern(pattern, actual, substitutions, search, depth + 1)? {
                    return Ok(false);
                }
            }
            Ok(true)
        }
        (Value::Object(pattern), Value::Object(actual)) => {
            if pattern.len() != actual.len() {
                return Ok(false);
            }
            for (key, pattern) in pattern {
                let Some(actual) = actual.get(key) else {
                    return Ok(false);
                };
                if !match_type_pattern(pattern, actual, substitutions, search, depth + 1)? {
                    return Ok(false);
                }
            }
            Ok(true)
        }
        _ => Ok(pattern == actual),
    }
}

fn parameter_candidates(
    parameters: &[Value],
    context: &mut CandidateContext<'_>,
) -> Result<Vec<Vec<String>>, String> {
    let mut candidates = Vec::new();
    for parameter in parameters {
        let ty = parameter
            .get("type")
            .ok_or("canonical parameter has no type")?;
        candidates.push(candidate_expressions(ty, context, 0)?);
    }
    product_bounded_plain(&candidates, 1024)
}

fn constructor_candidates(
    owner: &Value,
    context: &mut CandidateContext<'_>,
) -> Result<Vec<Vec<String>>, String> {
    let parameters = owner
        .pointer("/init/parameters")
        .and_then(Value::as_array)
        .map(Vec::as_slice)
        .unwrap_or_default();
    parameter_candidates(parameters, context)
}

fn product_bounded(parts: &[Vec<Vec<String>>], limit: usize) -> Vec<Vec<String>> {
    let mut output = vec![Vec::new()];
    for (part_index, part) in parts.iter().enumerate() {
        let mut next = Vec::new();
        for left in &output {
            for right in part {
                let mut combined = left.clone();
                if part_index == 1 {
                    combined.push("__COTT_PARAMETER_BOUNDARY__".to_owned());
                }
                combined.extend(right.iter().cloned());
                next.push(combined);
                if next.len() >= limit {
                    break;
                }
            }
            if next.len() >= limit {
                break;
            }
        }
        output = next;
    }
    output
}

fn product_bounded_plain(parts: &[Vec<String>], limit: usize) -> Result<Vec<Vec<String>>, String> {
    if parts.iter().any(Vec::is_empty) {
        return Ok(Vec::new());
    }
    let mut output = vec![Vec::new()];
    for part in parts {
        let mut next = Vec::new();
        for left in &output {
            for right in part {
                let mut combined = left.clone();
                combined.push(right.clone());
                next.push(combined);
                if next.len() >= limit {
                    break;
                }
            }
            if next.len() >= limit {
                break;
            }
        }
        output = next;
    }
    Ok(output)
}

fn candidate_expressions(
    ty: &Value,
    context: &mut CandidateContext<'_>,
    depth: usize,
) -> Result<Vec<String>, String> {
    if depth >= context.node_limit {
        return Err("candidate node limit exhausted".to_owned());
    }
    let ty = substitute_type(ty, &context.type_arguments);
    let kind = ty
        .get("kind")
        .and_then(Value::as_str)
        .ok_or("canonical candidate type has no kind")?;
    let candidates = match kind {
        "primitive" => primitive_candidates(
            ty.get("name")
                .and_then(Value::as_str)
                .ok_or("primitive candidate type has no name")?,
        )?,
        "type_parameter" => {
            let name = ty
                .get("name")
                .and_then(Value::as_str)
                .ok_or("type parameter candidate has no name")?;
            let Some(argument) = context.type_arguments.get(name).cloned() else {
                return Err(format!(
                    "generic type parameter `{name}` has no concrete bounded candidate"
                ));
            };
            candidate_expressions(&argument, context, depth + 1)?
        }
        "associated_projection" => {
            return Err("abstract associated type has no concrete runtime candidate".to_owned());
        }
        "list" | "set" => {
            let mut values = vec![if kind == "list" {
                "cott_runtime.CottList(emptyList())".to_owned()
            } else {
                "cott_runtime.CottSet(emptyList())".to_owned()
            }];
            if let Ok(items) = candidate_expressions(
                ty.get("item")
                    .ok_or("container candidate has no item type")?,
                context,
                depth + 1,
            ) && let Some(item) = items.first()
            {
                values.push(if kind == "list" {
                    format!("cott_runtime.CottList(listOf({item}))")
                } else {
                    format!("cott_runtime.CottSet(listOf({item}))")
                });
            }
            values
        }
        "option" => {
            let mut values = vec!["cott_runtime.Nothing".to_owned()];
            if let Ok(items) = candidate_expressions(
                ty.get("item").ok_or("Option candidate has no item type")?,
                context,
                depth + 1,
            ) {
                values.extend(
                    items
                        .into_iter()
                        .map(|item| format!("cott_runtime.Some({item})")),
                );
            }
            values
        }
        "map" => {
            let mut output = vec!["cott_runtime.FrozenMap(emptyMap())".to_owned()];
            let keys = candidate_expressions(
                ty.get("key").ok_or("map candidate has no key type")?,
                context,
                depth + 1,
            );
            let values = candidate_expressions(
                ty.get("value").ok_or("map candidate has no value type")?,
                context,
                depth + 1,
            );
            if let (Ok(keys), Ok(values)) = (keys, values)
                && let (Some(key), Some(value)) = (keys.first(), values.first())
            {
                output.push(format!(
                    "cott_runtime.FrozenMap(linkedMapOf({key} to {value}))"
                ));
            }
            output
        }
        "tuple" => {
            let items = ty
                .get("items")
                .and_then(Value::as_array)
                .ok_or("tuple candidate has no items")?;
            let mut values = Vec::new();
            for item in items {
                values.push(
                    candidate_expressions(item, context, depth + 1)?
                        .into_iter()
                        .next()
                        .ok_or("tuple item has no candidate")?,
                );
            }
            vec![format!(
                "cott_runtime.CottTuple{}({})",
                values.len(),
                values.join(", ")
            )]
        }
        "result" => {
            let ok = candidate_expressions(
                ty.get("ok").ok_or("Result candidate has no ok type")?,
                context,
                depth + 1,
            )?;
            let error = candidate_expressions(
                ty.get("error")
                    .ok_or("Result candidate has no error type")?,
                context,
                depth + 1,
            )?;
            let mut output = Vec::new();
            if let Some(value) = ok.first() {
                output.push(format!("cott_runtime.Ok({value})"));
            }
            if let Some(value) = error.first() {
                output.push(format!("cott_runtime.Err({value})"));
            }
            output
        }
        "array" => {
            let length = ty.get("length").ok_or("array candidate has no length")?;
            let (witness, length) = const_witness(length, context)?;
            if length > context.container_limit {
                return Err(format!(
                    "array candidate length {length} exceeds bounded container limit {}",
                    context.container_limit
                ));
            }
            let item = candidate_expressions(
                ty.get("item").ok_or("array candidate has no item type")?,
                context,
                depth + 1,
            )?
            .into_iter()
            .next()
            .ok_or("array item has no candidate")?;
            vec![format!(
                "cott_runtime.CottArray(listOf({}), {witness})",
                vec![item; length].join(", ")
            )]
        }
        "buffer" => {
            let (witness, length) = const_witness(
                ty.get("length").ok_or("buffer candidate has no length")?,
                context,
            )?;
            if length > context.container_limit {
                return Err(format!(
                    "buffer candidate length {length} exceeds bounded container limit {}",
                    context.container_limit
                ));
            }
            vec![format!(
                "cott_runtime.CottBuffer(kotlin.ByteArray({length}), {witness})"
            )]
        }
        "named" => named_candidates(&ty, context, depth + 1)?,
        "factory" => {
            let instance = ty
                .get("instance")
                .and_then(|value| value.get("name"))
                .and_then(Value::as_str)
                .ok_or("Factory candidate is not a concrete named implementation")?;
            let declaration = context
                .declarations
                .get(instance)
                .copied()
                .ok_or_else(|| format!("Factory implementation `{instance}` is absent"))?;
            if declaration.get("kind").and_then(Value::as_str) != Some("impl") {
                return Err(format!(
                    "Factory candidate `{instance}` is not an implementation"
                ));
            }
            vec![format!(
                "cott_runtime.CottFactory.of({}::class.java)",
                qualified(instance)
            )]
        }
        "iterator" | "async_iterator" | "generator" | "async_generator" => {
            return Err(format!(
                "protocol input `{kind}` has no compiler-owned source fixture"
            ));
        }
        "dyn" | "opaque" => {
            return Err(format!(
                "opaque runtime input `{kind}` has no public construction authority"
            ));
        }
        other => return Err(format!("unsupported canonical candidate type `{other}`")),
    };
    let mut unique = BTreeSet::new();
    Ok(candidates
        .into_iter()
        .filter(|candidate| unique.insert(candidate.clone()))
        .collect())
}

fn primitive_candidates(name: &str) -> Result<Vec<String>, String> {
    let values = match name {
        "bool" => vec!["false", "true"],
        "i8" => vec!["(-1).toByte()", "0.toByte()", "1.toByte()", "100.toByte()"],
        "i16" => vec![
            "(-1).toShort()",
            "0.toShort()",
            "1.toShort()",
            "100.toShort()",
        ],
        "i32" => vec!["-1", "0", "1", "2", "99", "100"],
        "i64" => vec!["-1L", "0L", "1L", "2L", "99L", "100L"],
        "u8" => vec!["0.toUByte()", "1.toUByte()", "2.toUByte()", "100.toUByte()"],
        "u16" => vec![
            "0.toUShort()",
            "1.toUShort()",
            "2.toUShort()",
            "100.toUShort()",
        ],
        "u32" => vec!["0U", "1U", "2U", "100U"],
        "u64" => vec!["0UL", "1UL", "2UL", "100UL"],
        "f32" => vec!["-1.0F", "0.0F", "1.0F", "2.0F"],
        "f64" => vec!["-1.0", "0.0", "1.0", "2.0"],
        "str" => vec!["\"\"", "\"a\"", "\"test\""],
        "bytes" => vec![
            "cott_runtime.CottBytes(kotlin.ByteArray(0))",
            "cott_runtime.CottBytes(kotlin.byteArrayOf(0))",
        ],
        "path" => vec!["java.nio.file.Path.of(\"fixture\")"],
        "unit" => vec!["cott_runtime.CottUnit"],
        "json" => vec![
            "cott_runtime.JsonNull",
            "cott_runtime.JsonInteger(java.math.BigInteger.ZERO)",
        ],
        "any" | "unknown" => vec!["0", "\"candidate\""],
        "never" => return Err("Never has no runtime input value".to_owned()),
        other => return Err(format!("unsupported primitive candidate `{other}`")),
    };
    Ok(values.into_iter().map(str::to_owned).collect())
}

fn named_candidates(
    ty: &Value,
    context: &mut CandidateContext<'_>,
    depth: usize,
) -> Result<Vec<String>, String> {
    let name = ty
        .get("name")
        .and_then(Value::as_str)
        .ok_or("named candidate has no name")?;
    let declaration = context
        .declarations
        .get(name)
        .copied()
        .ok_or_else(|| format!("named candidate `{name}` is absent from canonical IR"))?;
    let substitutions = named_substitutions(declaration, ty)?;
    let mut nested = context.clone();
    nested.type_arguments.extend(substitutions);
    let witnesses = named_const_witnesses(declaration, ty)?;
    match declaration.get("kind").and_then(Value::as_str) {
        Some("alias") => candidate_expressions(
            declaration
                .get("target")
                .ok_or_else(|| format!("alias `{name}` has no target"))?,
            &mut nested,
            depth,
        ),
        Some("newtype") => {
            let values = candidate_expressions(
                declaration
                    .get("carrier")
                    .ok_or_else(|| format!("newtype `{name}` has no carrier"))?,
                &mut nested,
                depth,
            )?;
            Ok(values
                .into_iter()
                .map(|value| {
                    let mut arguments = vec![value];
                    arguments.extend(witnesses.iter().cloned());
                    format!("{}({})", qualified(name), arguments.join(", "))
                })
                .collect())
        }
        Some("struct") => {
            let fields = declaration
                .get("fields")
                .and_then(Value::as_array)
                .ok_or_else(|| format!("struct `{name}` has no fields"))?;
            let arguments = field_candidates(fields, &mut nested, depth)?;
            Ok(product_bounded_plain(&arguments, 16)?
                .into_iter()
                .map(|mut values| {
                    values.extend(witnesses.iter().cloned());
                    format!("{}({})", qualified(name), values.join(", "))
                })
                .collect())
        }
        Some("enum") => {
            let variants = declaration
                .get("variants")
                .and_then(Value::as_array)
                .ok_or_else(|| format!("enum `{name}` has no variants"))?;
            let mut output = Vec::new();
            for variant in variants.iter().take(4) {
                let symbol = variant
                    .get("symbol")
                    .and_then(Value::as_str)
                    .ok_or_else(|| format!("enum `{name}` variant has no symbol"))?;
                let fields = variant
                    .get("fields")
                    .and_then(Value::as_array)
                    .ok_or_else(|| format!("enum variant `{symbol}` has no fields"))?;
                let arguments = field_candidates(fields, &mut nested, depth)?;
                let generic_arguments = types::render_named_arguments(Some(ty))?;
                let constructor = if generic_arguments.is_empty() {
                    qualified(symbol)
                } else {
                    format!("{}<{}>", qualified(symbol), generic_arguments.join(", "))
                };
                for mut values in product_bounded_plain(&arguments, 4)? {
                    values.extend(witnesses.iter().cloned());
                    output.push(if values.is_empty() && generic_arguments.is_empty() {
                        constructor.clone()
                    } else {
                        format!("{constructor}({})", values.join(", "))
                    });
                }
            }
            Ok(output)
        }
        Some("resource") => {
            let initial = declaration
                .get("initial")
                .and_then(Value::as_str)
                .ok_or_else(|| format!("resource `{name}` has no initial state"))?;
            Ok(vec![qualified(initial)])
        }
        Some("impl") => {
            let constructors = constructor_candidates(declaration, &mut nested)?;
            Ok(constructors
                .into_iter()
                .map(|values| format!("{}({})", qualified(name), values.join(", ")))
                .collect())
        }
        Some("trait") => {
            let concrete =
                implementation_type_for_bound(ty, &nested.declarations)?.ok_or_else(|| {
                    format!("trait `{name}` has no public concrete implementation candidate")
                })?;
            candidate_expressions(&concrete, &mut nested, depth)
        }
        Some("external_type") => Err(format!(
            "external type `{name}` has no compiler-owned value constructor"
        )),
        Some(other) => Err(format!(
            "named candidate `{name}` has unsupported kind `{other}`"
        )),
        None => Err(format!(
            "named candidate `{name}` has malformed declaration"
        )),
    }
}

fn named_const_witnesses(declaration: &Value, ty: &Value) -> Result<Vec<String>, String> {
    let generics = declaration
        .get("generics")
        .and_then(Value::as_array)
        .map(Vec::as_slice)
        .unwrap_or_default();
    let arguments = ty
        .get("args")
        .and_then(Value::as_array)
        .map(Vec::as_slice)
        .unwrap_or_default();
    generics
        .iter()
        .zip(arguments)
        .filter(|(generic, _)| generic.get("kind").and_then(Value::as_str) == Some("const"))
        .map(|(_, argument)| {
            types::render_const_witness(
                argument
                    .get("value")
                    .ok_or("named const generic argument has no value")?,
            )
        })
        .collect()
}

fn field_candidates(
    fields: &[Value],
    context: &mut CandidateContext<'_>,
    depth: usize,
) -> Result<Vec<Vec<String>>, String> {
    fields
        .iter()
        .map(|field| {
            candidate_expressions(
                field.get("type").ok_or("canonical field has no type")?,
                context,
                depth,
            )
        })
        .collect()
}

fn named_substitutions(declaration: &Value, ty: &Value) -> Result<BTreeMap<String, Value>, String> {
    let generics = declaration
        .get("generics")
        .and_then(Value::as_array)
        .map(Vec::as_slice)
        .unwrap_or_default();
    let arguments = ty
        .get("args")
        .and_then(Value::as_array)
        .map(Vec::as_slice)
        .unwrap_or_default();
    if generics.len() != arguments.len() {
        return Err("named candidate generic arity mismatch".to_owned());
    }
    let mut result = BTreeMap::new();
    for (generic, argument) in generics.iter().zip(arguments) {
        if generic.get("kind").and_then(Value::as_str) != Some("type") {
            continue;
        }
        let name = generic
            .get("name")
            .and_then(Value::as_str)
            .ok_or("named generic has no name")?;
        let value = argument
            .get("type")
            .cloned()
            .ok_or("named generic type argument has no type")?;
        result.insert(name.to_owned(), value);
    }
    Ok(result)
}

fn substitute_type(value: &Value, substitutions: &BTreeMap<String, Value>) -> Value {
    if value.get("kind").and_then(Value::as_str) == Some("type_parameter") {
        if let Some(name) = value.get("name").and_then(Value::as_str) {
            if let Some(replacement) = substitutions.get(name) {
                return replacement.clone();
            }
        }
    }
    match value {
        Value::Array(values) => Value::Array(
            values
                .iter()
                .map(|value| substitute_type(value, substitutions))
                .collect(),
        ),
        Value::Object(object) => Value::Object(
            object
                .iter()
                .map(|(key, value)| (key.clone(), substitute_type(value, substitutions)))
                .collect(),
        ),
        _ => value.clone(),
    }
}

fn contains_type_parameter(value: &Value, name: &str) -> bool {
    match value {
        Value::Object(object) => {
            (object.get("kind").and_then(Value::as_str) == Some("type_parameter")
                && object.get("name").and_then(Value::as_str) == Some(name))
                || object
                    .values()
                    .any(|value| contains_type_parameter(value, name))
        }
        Value::Array(values) => values
            .iter()
            .any(|value| contains_type_parameter(value, name)),
        _ => false,
    }
}
fn contains_const_parameter(value: &Value) -> bool {
    match value {
        Value::Object(object) => {
            (object.get("kind").and_then(Value::as_str) == Some("parameter")
                && object.get("type").and_then(Value::as_str).is_some())
                || object.values().any(contains_const_parameter)
        }
        Value::Array(values) => values.iter().any(contains_const_parameter),
        _ => false,
    }
}

fn const_witness(value: &Value, context: &CandidateContext<'_>) -> Result<(String, usize), String> {
    if value.get("kind").and_then(Value::as_str) == Some("parameter") {
        let name = value
            .get("name")
            .and_then(Value::as_str)
            .ok_or("const parameter has no name")?;
        let numeric = context
            .consts
            .get(name)
            .ok_or_else(|| format!("const parameter `{name}` has no candidate witness"))?
            .parse::<usize>()
            .map_err(|_| format!("const parameter `{name}` candidate is not a container length"))?;
        return Ok((quoted(name), numeric));
    }
    let numeric = const_numeric(value, &context.declarations)?;
    let witness = types::render_const_witness(value)?;
    Ok((witness, numeric))
}

fn const_numeric(value: &Value, declarations: &BTreeMap<&str, &Value>) -> Result<usize, String> {
    match value.get("kind").and_then(Value::as_str) {
        Some("value") => value
            .get("value")
            .and_then(Value::as_str)
            .ok_or("const value has no numeric value")?
            .parse::<usize>()
            .map_err(|_| "const value is not a bounded container length".to_owned()),
        Some("reference") => {
            let symbol = value
                .get("symbol")
                .and_then(Value::as_str)
                .ok_or("const reference has no symbol")?;
            let declaration = declarations
                .get(symbol)
                .copied()
                .ok_or_else(|| format!("const reference `{symbol}` is absent"))?;
            declaration
                .pointer("/value/value")
                .and_then(Value::as_str)
                .ok_or_else(|| format!("const reference `{symbol}` is not an integer"))?
                .parse::<usize>()
                .map_err(|_| format!("const reference `{symbol}` is not a bounded length"))
        }
        Some("binary") => {
            let left = const_numeric(
                value
                    .get("left")
                    .ok_or("const binary has no left operand")?,
                declarations,
            )?;
            let right = const_numeric(
                value
                    .get("right")
                    .ok_or("const binary has no right operand")?,
                declarations,
            )?;
            match value.get("op").and_then(Value::as_str) {
                Some("add") => left.checked_add(right),
                Some("sub") => left.checked_sub(right),
                Some("mul") => left.checked_mul(right),
                Some("div") if right != 0 => left.checked_div(right),
                Some("mod") if right != 0 => left.checked_rem(right),
                _ => None,
            }
            .ok_or_else(|| "const expression is not a bounded container length".to_owned())
        }
        _ => Err("const expression has no concrete container length".to_owned()),
    }
}

fn render_scenario(
    strategy: &ContractTestStrategy,
    declarations: &BTreeMap<&str, &Value>,
    types: &dyn KotlinTypeContext,
    output: &mut String,
    main_lines: &mut Vec<String>,
) -> Result<bool, String> {
    let scenario = strategy
        .scenario
        .as_ref()
        .ok_or("scenario strategy is missing")?;
    if scenario
        .fixtures
        .iter()
        .any(|fixture| fixture.get("kind").and_then(Value::as_str) == Some("failure"))
    {
        return Err("failure fixtures have no Kotlin runtime interception authority".to_owned());
    }
    if scenario
        .fixtures
        .iter()
        .any(|fixture| fixture.get("kind").and_then(Value::as_str) == Some("http"))
    {
        return Err(
            "HTTP scenario fixture is unavailable without a compiler-owned loopback transcript adapter"
                .to_owned(),
        );
    }
    for step in &scenario.steps {
        if matches!(
            step.get("kind").and_then(Value::as_str),
            Some("call" | "spawn")
        ) {
            let target = step
                .get("target")
                .and_then(Value::as_str)
                .ok_or("scenario call has no target")?;
            if target.rsplit_once('.').is_some_and(|(owner, _)| {
                declarations.get(owner).is_some_and(|declaration| {
                    declaration.get("kind").and_then(Value::as_str) == Some("impl")
                })
            }) {
                return Err(
                    "scenario impl methods require a receiver-bearing method_call step".to_owned(),
                );
            }
        }
    }

    // An unsupported fixture, step, or value becomes this scenario's unavailability
    // reason; a partially written function would break the whole runner instead.
    let mut source = String::new();
    let function = format!("scenario_{}", safe_name(&scenario.id));
    writeln!(
        source,
        "\nprivate fun {function}(evidence: EvidenceWriter) {{"
    )
    .unwrap();
    writeln!(source, "    val _observation = CottObservation()").unwrap();
    writeln!(
        source,
        "    val _root = Path.of(java.lang.System.getProperty(\"java.io.tmpdir\"), {})",
        kotlin_string(&format!("scenario-{}", safe_name(&scenario.id)))
    )
    .unwrap();
    source.push_str("    var _assertions = 0\n    try {\n        deleteTree(_root)\n        Files.createDirectory(_root)\n");
    let mut total_fixture_source = 0usize;
    let mut clock_starts = Vec::new();
    for fixture in &scenario.fixtures {
        let fixture_id = fixture
            .get("id")
            .and_then(Value::as_str)
            .ok_or("scenario fixture has no id")?;
        writeln!(
            source,
            "        val {} = {}",
            quoted(local_name(fixture_id)),
            kotlin_string(fixture_id)
        )
        .unwrap();
        match fixture.get("kind").and_then(Value::as_str) {
            Some("fs") => {
                for file in fixture
                    .get("files")
                    .and_then(Value::as_array)
                    .ok_or("filesystem fixture has no files")?
                {
                    let path = file
                        .get("path")
                        .and_then(Value::as_str)
                        .ok_or("filesystem fixture file has no path")?;
                    let data = file
                        .get("data")
                        .ok_or("filesystem fixture file has no data")?;
                    let rendered = match data.get("kind").and_then(Value::as_str) {
                        Some("text") => {
                            let value = data
                                .get("value")
                                .and_then(Value::as_str)
                                .ok_or("text fixture has no value")?;
                            total_fixture_source = total_fixture_source.saturating_add(value.len());
                            format!(
                                "{}.toByteArray(kotlin.text.Charsets.UTF_8)",
                                kotlin_string(value)
                            )
                        }
                        Some("bytes") => {
                            let value = data
                                .get("value")
                                .and_then(Value::as_str)
                                .ok_or("byte fixture has no value")?;
                            total_fixture_source =
                                total_fixture_source.saturating_add(value.len() / 2);
                            format!("hex({})", kotlin_string(value))
                        }
                        _ => return Err("unsupported filesystem fixture data".to_owned()),
                    };
                    if total_fixture_source > 1_048_576 {
                        return Err(
                            "scenario fixture source exceeds the bounded runner limit".to_owned()
                        );
                    }
                    writeln!(source, "        run {{ val _path = _root.resolve({}).resolve({}); Files.createDirectories(_path.parent); Files.write(_path, {rendered}) }}", kotlin_string(fixture_id), kotlin_string(path)).unwrap();
                }
            }
            Some("clock") => {
                let start_ms = fixture
                    .get("start_ms")
                    .and_then(Value::as_u64)
                    .ok_or("clock fixture has no unsigned start_ms")?;
                clock_starts.push((local_name(fixture_id), start_ms));
            }
            Some(_) => return Err("unsupported Kotlin scenario fixture".to_owned()),
            None => return Err("scenario fixture has no kind".to_owned()),
        }
    }
    writeln!(
        source,
        "        auditFixtureRoot(_root, {}L, {}L)",
        scenario.limits.filesystem_files, scenario.limits.filesystem_bytes
    )
    .unwrap();
    source.push_str("        val _fixtures = CottFixtureContext(_root, emptyMap<CottFixtureKey, kotlin.String>(), ");
    if clock_starts.is_empty() {
        source.push_str("emptyMap<kotlin.String, kotlin.ULong>()");
    } else {
        source.push_str("mapOf(");
        for (index, (name, start_ms)) in clock_starts.iter().enumerate() {
            if index != 0 {
                source.push_str(", ");
            }
            write!(source, "{} to {start_ms}UL", kotlin_string(name)).unwrap();
        }
        source.push(')');
    }
    source.push_str(")\n");
    writeln!(source, "        CottRuntime.withTestObservation(_observation) {{ CottRuntime.withFixtureContext(_fixtures) {{ runBlocking {{ withTimeout({}L) {{ CottRuntime.withTestObservationSuspend(_observation) {{ CottRuntime.withFixtureContextSuspend(_fixtures) {{", scenario.limits.scenario_timeout_ms).unwrap();

    let mut workers = BTreeSet::new();
    for step in &scenario.steps {
        let step_id = step
            .get("step_id")
            .and_then(Value::as_u64)
            .ok_or("scenario step has no step_id")?;
        match step.get("kind").and_then(Value::as_str) {
            Some("call") => {
                let binding = step
                    .get("binding")
                    .and_then(Value::as_str)
                    .ok_or("scenario call has no binding")?;
                let target = step
                    .get("target")
                    .and_then(Value::as_str)
                    .ok_or("scenario call has no target")?;
                let arguments = scenario_arguments(step, types)?;
                writeln!(
                    source,
                    "            val {} = {}({})",
                    quoted(local_name(binding)),
                    qualified(target),
                    arguments.join(", ")
                )
                .unwrap();
            }
            Some("init") => {
                let binding = step
                    .get("binding")
                    .and_then(Value::as_str)
                    .ok_or("scenario initializer has no binding")?;
                let target = step
                    .get("target")
                    .and_then(Value::as_str)
                    .ok_or("scenario initializer has no target")?;
                let owner = declarations.get(target).ok_or_else(|| {
                    format!("scenario initializer `{target}` has no public facade")
                })?;
                if owner.get("kind").and_then(Value::as_str) != Some("impl")
                    || owner.get("public").and_then(Value::as_bool) != Some(true)
                {
                    return Err(format!(
                        "scenario initializer `{target}` has no public facade"
                    ));
                }
                let arguments = scenario_arguments(step, types)?;
                writeln!(
                    source,
                    "            val {} = {}({})",
                    quoted(local_name(binding)),
                    qualified(target),
                    arguments.join(", ")
                )
                .unwrap();
            }
            Some("method_call") => {
                let binding = step
                    .get("binding")
                    .and_then(Value::as_str)
                    .ok_or("scenario method call has no binding")?;
                let target = step
                    .get("target")
                    .and_then(Value::as_str)
                    .ok_or("scenario method call has no target")?;
                let (owner_symbol, method) = target
                    .rsplit_once('.')
                    .ok_or("scenario method call has no owner")?;
                let owner = declarations
                    .get(owner_symbol)
                    .ok_or_else(|| format!("scenario method `{target}` has no public facade"))?;
                if owner.get("kind").and_then(Value::as_str) != Some("impl")
                    || owner.get("public").and_then(Value::as_bool) != Some(true)
                    || !owner
                        .get("selected_methods")
                        .and_then(Value::as_array)
                        .is_some_and(|methods| {
                            methods.iter().any(|slot| {
                                slot.get("trait_method")
                                    .and_then(Value::as_str)
                                    .is_some_and(|name| local_name(name) == method)
                            })
                        })
                {
                    return Err(format!("scenario method `{target}` has no public facade"));
                }
                let receiver = expressions::render_scenario_expression(
                    step.get("receiver")
                        .ok_or("scenario method call has no receiver")?,
                    types,
                )?;
                let arguments = scenario_arguments(step, types)?;
                writeln!(
                    source,
                    "            val {} = ({}).{}({})",
                    quoted(local_name(binding)),
                    receiver,
                    quoted(method),
                    arguments.join(", ")
                )
                .unwrap();
            }
            Some("spawn") => {
                let worker = step
                    .get("worker")
                    .and_then(Value::as_str)
                    .ok_or("scenario spawn has no worker")?;
                let target = step
                    .get("target")
                    .and_then(Value::as_str)
                    .ok_or("scenario spawn has no target")?;
                let arguments = scenario_arguments(step, types)?;
                let local = local_name(worker).to_owned();
                workers.insert(local.clone());
                writeln!(
                    source,
                    "            val {} = async(start = CoroutineStart.UNDISPATCHED) {{ {}({}) }}",
                    quoted(&local),
                    qualified(target),
                    arguments.join(", ")
                )
                .unwrap();
            }
            Some("tick") => source.push_str("            yield()\n"),
            Some("cancel") => {
                let worker = local_name(
                    step.get("worker")
                        .and_then(Value::as_str)
                        .ok_or("scenario cancel has no worker")?,
                );
                writeln!(source, "            {}.cancel()", quoted(worker)).unwrap();
            }
            Some("await") => {
                let worker = local_name(
                    step.get("worker")
                        .and_then(Value::as_str)
                        .ok_or("scenario await has no worker")?,
                );
                let cancelled = step.get("cancelled").and_then(Value::as_bool) == Some(true);
                let result = step.get("result").and_then(Value::as_str).map(local_name);
                if cancelled {
                    writeln!(source, "            try {{ {}.await(); error(\"step {step_id} expected cancellation\") }} catch (_: CancellationException) {{ }}", quoted(worker)).unwrap();
                } else if let Some(result) = result {
                    writeln!(
                        source,
                        "            val {} = {}.await()",
                        quoted(result),
                        quoted(worker)
                    )
                    .unwrap();
                } else {
                    writeln!(source, "            {}.await()", quoted(worker)).unwrap();
                }
            }
            Some("assert") => {
                let expression = expressions::render_scenario_expression(
                    step.get("expression")
                        .ok_or("scenario assertion has no expression")?,
                    types,
                )?;
                writeln!(source, "            check({expression}) {{ \"scenario assertion step:{step_id} failed\" }}; _assertions += 1").unwrap();
            }
            Some("data") => {
                let binding = step
                    .get("binding")
                    .and_then(Value::as_str)
                    .ok_or("scenario data has no binding")?;
                let expression = expressions::render_scenario_expression(
                    step.get("expression")
                        .ok_or("scenario data has no expression")?,
                    types,
                )?;
                writeln!(
                    source,
                    "            val {} = {expression}",
                    quoted(local_name(binding))
                )
                .unwrap();
            }
            Some(other) => return Err(format!("unsupported scenario step `{other}`")),
            None => return Err("scenario step has no kind".to_owned()),
        }
    }
    for worker in workers {
        writeln!(
            source,
            "            check({}.isCompleted) {{ \"scenario leaked worker\" }}",
            quoted(&worker)
        )
        .unwrap();
    }
    source.push_str("        } } } } } }\n");
    writeln!(
        source,
        "        auditFixtureRoot(_root, {}L, {}L)",
        scenario.limits.filesystem_files, scenario.limits.filesystem_bytes
    )
    .unwrap();
    writeln!(
        source,
        "        emitScenario(evidence, {}, \"passed\", _observation, _assertions)",
        kotlin_string(&scenario.id)
    )
    .unwrap();
    source.push_str("    } catch (_: kotlin.Throwable) {\n");
    writeln!(
        source,
        "        emitScenario(evidence, {}, \"failed\", _observation, _assertions)",
        kotlin_string(&scenario.id)
    )
    .unwrap();
    source.push_str("    } finally { deleteTree(_root) }\n}\n");
    output.push_str(&source);
    main_lines.push(format!("{function}(evidence)"));
    Ok(false)
}

fn scenario_arguments(step: &Value, types: &dyn KotlinTypeContext) -> Result<Vec<String>, String> {
    step.get("arguments")
        .and_then(Value::as_array)
        .ok_or_else(|| "scenario call has no arguments".to_owned())?
        .iter()
        .map(|argument| expressions::render_scenario_expression(argument, types))
        .collect()
}

pub(crate) fn parse_events(output: &[u8], secret: &[u8]) -> Result<Vec<Value>, String> {
    if secret.len() != EVIDENCE_KEY_BYTES {
        return Err("Kotlin evidence authentication key has the wrong length".to_owned());
    }
    let text = std::str::from_utf8(output)
        .map_err(|_| "Kotlin contract runner output is not valid UTF-8".to_owned())?;
    let mut events = Vec::new();
    let mut expected_sequence = 0u64;
    for line in text.lines() {
        let Some(envelope) = line.strip_prefix(EVENT_PREFIX) else {
            continue;
        };
        let mut fields = envelope.splitn(3, ':');
        let sequence_text = fields
            .next()
            .ok_or("Kotlin contract runner emitted a malformed authenticated event")?;
        let tag_text = fields
            .next()
            .ok_or("Kotlin contract runner emitted a malformed authenticated event")?;
        let payload = fields
            .next()
            .ok_or("Kotlin contract runner emitted a malformed authenticated event")?;
        if sequence_text != expected_sequence.to_string() {
            return Err(format!(
                "Kotlin contract runner authenticated evidence sequence is not strictly monotonic at {expected_sequence}"
            ));
        }
        let tag = decode_auth_tag(tag_text)?;
        let mut authenticator = Hmac::<Sha256>::new_from_slice(secret)
            .map_err(|_| "initialize Kotlin evidence authenticator".to_owned())?;
        authenticator.update(&expected_sequence.to_be_bytes());
        authenticator.update(payload.as_bytes());
        authenticator
            .verify_slice(&tag)
            .map_err(|_| "Kotlin contract runner evidence authentication failed".to_owned())?;
        let event: Value = serde_json::from_str(payload)
            .map_err(|error| format!("Kotlin contract runner emitted invalid JSON: {error}"))?;
        if !event.is_object() {
            return Err("Kotlin contract runner event is not an object".to_owned());
        }
        events.push(event);
        expected_sequence = expected_sequence
            .checked_add(1)
            .ok_or("Kotlin contract runner evidence sequence overflow")?;
    }
    if events
        .last()
        .and_then(|event| event.get("kind"))
        .and_then(Value::as_str)
        != Some("done")
    {
        return Err(
            "Kotlin contract runner did not emit an authenticated final completion marker"
                .to_owned(),
        );
    }
    Ok(events)
}

fn decode_auth_tag(value: &str) -> Result<[u8; 32], String> {
    if value.len() != 64
        || !value
            .bytes()
            .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
    {
        return Err("Kotlin contract runner emitted a malformed authentication tag".to_owned());
    }
    let mut tag = [0u8; 32];
    for (index, byte) in tag.iter_mut().enumerate() {
        let offset = index * 2;
        *byte = u8::from_str_radix(&value[offset..offset + 2], 16)
            .map_err(|_| "Kotlin contract runner emitted a malformed authentication tag")?;
    }
    Ok(tag)
}

fn qualified(value: &str) -> String {
    value.split('.').map(quoted).collect::<Vec<_>>().join(".")
}

fn quoted(value: &str) -> String {
    format!("`{}`", value.replace('`', ""))
}

fn safe_name(value: &str) -> String {
    let mut result = String::with_capacity(value.len());
    for character in value.chars() {
        if character.is_ascii_alphanumeric() {
            result.push(character);
        } else {
            result.push('_');
        }
    }
    result
}

fn local_name(value: &str) -> &str {
    value.rsplit('.').next().unwrap_or(value)
}

fn kotlin_string(value: &str) -> String {
    let mut result = String::from("\"");
    for character in value.chars() {
        match character {
            '\\' => result.push_str("\\\\"),
            '"' => result.push_str("\\\""),
            '\n' => result.push_str("\\n"),
            '\r' => result.push_str("\\r"),
            '\t' => result.push_str("\\t"),
            '$' => result.push_str("\\$"),
            character if character.is_control() => {
                write!(result, "\\u{:04x}", character as u32)
                    .expect("writing to String cannot fail");
            }
            character => result.push(character),
        }
    }
    result.push('"');
    result
}
