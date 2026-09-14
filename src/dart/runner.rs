use std::collections::{BTreeMap, BTreeSet};
use std::fmt::Write as _;
use std::path::PathBuf;

use hmac::{Hmac, Mac};
use serde_json::Value;
use sha2::Sha256;

use crate::contract_test::{Classification, ContractTestStrategy};
use crate::manifest::{DartProjectConfig, VerificationConfig};

use super::emit;
use super::types::{escape_identifier, internal_name, local_name};
use super::{DartCallable, DartPlan};

const EVENT_PREFIX: &str = "COTT_DART_VERIFY:";
pub(crate) const EVIDENCE_KEY_BYTES: usize = 32;
const RUNNER_FILE: &str = "runner.dart";
const MAX_RUNNER_CASES: u64 = 4096;
const MAX_RUNNER_SOURCE_BYTES: usize = 8 * 1024 * 1024;

#[derive(Clone, Debug)]
pub(crate) struct RunnerProgram {
    pub source: String,
    pub file_name: &'static str,
    pub expected_cases: BTreeMap<String, u32>,
    pub expected_cancellations: BTreeSet<(String, u32)>,
    pub expected_scenarios: BTreeMap<String, ScenarioExpectation>,
    pub unavailable: BTreeMap<String, String>,
    pub support: BTreeMap<PathBuf, &'static [u8]>,
    pub needs_loopback: bool,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct ScenarioExpectation {
    pub symbol: String,
    pub assertions: u32,
    pub cancellations: u32,
}

#[derive(Clone)]
struct CandidateContext<'a> {
    config: &'a DartProjectConfig,
    plan: &'a DartPlan,
    declarations: BTreeMap<&'a str, &'a Value>,
    aliases: &'a BTreeMap<String, String>,
    marker_module: String,
    consts: BTreeMap<String, String>,
    type_arguments: BTreeMap<String, Value>,
    node_limit: usize,
    container_limit: usize,
}

struct Invocation {
    prelude: Vec<String>,
    call: String,
    return_type: Value,
    asynchronous: bool,
}

#[derive(Debug)]
enum RenderFailure {
    Unavailable(String),
    Fatal(String),
}

impl RenderFailure {
    fn unavailable(reason: impl Into<String>) -> Self {
        Self::Unavailable(reason.into())
    }
}

impl From<String> for RenderFailure {
    fn from(reason: String) -> Self {
        Self::Fatal(reason)
    }
}

impl From<&str> for RenderFailure {
    fn from(reason: &str) -> Self {
        Self::Fatal(reason.to_owned())
    }
}

pub(crate) fn render(
    config: &DartProjectConfig,
    plan: &DartPlan,
    strategies: &[ContractTestStrategy],
    verification: &VerificationConfig,
) -> Result<RunnerProgram, String> {
    let aliases = module_aliases(plan)?;
    let mut strategies_by_symbol = BTreeMap::new();
    for strategy in strategies {
        if strategies_by_symbol
            .insert(strategy.symbol.as_str(), strategy)
            .is_some()
        {
            return Err(format!(
                "duplicate Dart contract strategy for `{}`",
                strategy.symbol
            ));
        }
    }
    let declarations = declaration_index(plan)?;
    let mut source = runner_prelude(config, plan, &aliases)?;
    let mut invocations = Vec::new();
    let mut expected_cases = BTreeMap::new();
    let mut expected_cancellations = BTreeSet::new();
    let mut expected_scenarios = BTreeMap::new();
    let mut unavailable = BTreeMap::new();

    for callable in plan.callables() {
        let Some(strategy) = strategies_by_symbol.get(callable.symbol.as_str()).copied() else {
            continue;
        };
        if !callable_is_public(callable)? {
            unavailable.insert(
                callable.symbol.clone(),
                "selected implementation helper is not a public consumer facade".to_owned(),
            );
            continue;
        }
        if strategy.classification == Classification::Effectful {
            if strategy.scenario.is_none() {
                unavailable.insert(
                    callable.symbol.clone(),
                    "effectful callable requires an enforceable canonical scenario".to_owned(),
                );
            }
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
            config,
            plan,
            callable,
            &declarations,
            &aliases,
            verification,
            &mut source,
            &mut invocations,
        ) {
            Ok(count) => {
                expected_cases.insert(callable.symbol.clone(), count);
            }
            Err(RenderFailure::Unavailable(reason)) => {
                unavailable.insert(callable.symbol.clone(), reason);
            }
            Err(RenderFailure::Fatal(reason)) => {
                return Err(format!(
                    "render Dart callable evidence for `{}`: {reason}",
                    callable.symbol
                ));
            }
        }
    }

    for strategy in strategies
        .iter()
        .filter(|strategy| strategy.symbol.ends_with(".init"))
    {
        let owner_symbol = strategy.symbol.trim_end_matches(".init");
        let owner = declarations.get(owner_symbol).copied().ok_or_else(|| {
            format!(
                "Dart initializer strategy `{}` has no canonical owner",
                strategy.symbol
            )
        })?;
        if owner.get("kind").and_then(Value::as_str) != Some("impl") {
            return Err(format!(
                "Dart initializer strategy `{}` has a non-implementation owner",
                strategy.symbol
            ));
        }
        match owner.get("public").and_then(Value::as_bool) {
            Some(true) => {}
            Some(false) => {
                unavailable.insert(
                    strategy.symbol.clone(),
                    "initializer owner is not a public Dart facade".to_owned(),
                );
                continue;
            }
            None => {
                return Err(format!(
                    "Dart initializer owner `{owner_symbol}` has no public flag"
                ));
            }
        }
        match render_initializer_cases(
            config,
            plan,
            owner_symbol,
            owner,
            &declarations,
            &aliases,
            verification,
            &mut source,
            &mut invocations,
        ) {
            Ok(count) => {
                expected_cases.insert(strategy.symbol.clone(), count);
            }
            Err(RenderFailure::Unavailable(reason)) => {
                unavailable.insert(strategy.symbol.clone(), reason);
            }
            Err(RenderFailure::Fatal(reason)) => {
                return Err(format!(
                    "render Dart initializer evidence for `{}`: {reason}",
                    strategy.symbol
                ));
            }
        }
    }

    let mut needs_loopback = false;
    let mut observed_scenario_targets = BTreeSet::new();
    for strategy in strategies {
        let Some(scenario) = strategy.scenario.as_ref() else {
            continue;
        };
        let targets = scenario
            .steps
            .iter()
            .filter(|step| {
                matches!(
                    step.get("kind").and_then(Value::as_str),
                    Some("call" | "spawn")
                )
            })
            .filter_map(|step| step.get("target").and_then(Value::as_str))
            .map(str::to_owned)
            .collect::<BTreeSet<_>>();
        match render_scenario(
            plan,
            strategy,
            &aliases,
            &mut source,
            &mut invocations,
            &mut expected_cancellations,
        ) {
            Ok((loopback, expectation)) => {
                if expected_scenarios
                    .insert(scenario.id.clone(), expectation)
                    .is_some()
                {
                    return Err(format!("duplicate Dart scenario id `{}`", scenario.id));
                }
                unavailable.remove(&strategy.symbol);
                observed_scenario_targets.extend(targets);
                needs_loopback |= loopback;
            }
            Err(RenderFailure::Unavailable(reason)) => {
                unavailable.insert(strategy.symbol.clone(), reason.clone());
                for target in targets {
                    unavailable.insert(
                        target,
                        format!(
                            "canonical scenario `{}` is unavailable: {reason}",
                            scenario.id
                        ),
                    );
                }
            }
            Err(RenderFailure::Fatal(reason)) => {
                return Err(format!(
                    "render Dart scenario evidence for `{}`: {reason}",
                    scenario.id
                ));
            }
        }
    }
    for target in observed_scenario_targets {
        unavailable.remove(&target);
    }

    let total_cases = expected_cases
        .values()
        .map(|value| u64::from(*value))
        .sum::<u64>();
    if total_cases > MAX_RUNNER_CASES {
        return Err(format!(
            "bounded Dart runner case limit exceeded ({total_cases} > {MAX_RUNNER_CASES})"
        ));
    }
    writeln!(source, "Future<void> main() async {{").expect("writing to String cannot fail");
    writeln!(
        source,
        "  final evidence = EvidenceWriter(await _readEvidenceKey());"
    )
    .expect("writing to String cannot fail");
    for invocation in invocations {
        writeln!(source, "  {invocation}").expect("writing to String cannot fail");
    }
    writeln!(
        source,
        "  evidence.emit(<String, Object?>{{'kind': 'done'}});"
    )
    .expect("writing to String cannot fail");
    writeln!(source, "}}").expect("writing to String cannot fail");
    if source.len() > MAX_RUNNER_SOURCE_BYTES {
        return Err(format!(
            "bounded Dart runner source limit exceeded ({} > {MAX_RUNNER_SOURCE_BYTES})",
            source.len()
        ));
    }

    Ok(RunnerProgram {
        source,
        file_name: RUNNER_FILE,
        expected_cases,
        expected_cancellations,
        expected_scenarios,
        unavailable,
        support: crypto_support(),
        needs_loopback,
    })
}

fn runner_prelude(
    config: &DartProjectConfig,
    plan: &DartPlan,
    aliases: &BTreeMap<String, String>,
) -> Result<String, String> {
    let mut source = String::from(
        "import 'dart:async';\nimport 'dart:convert';\nimport 'dart:io';\nimport 'dart:typed_data';\n\n",
    );
    source.push_str("import 'crypto/hmac.dart';\nimport 'crypto/sha256.dart';\n");
    writeln!(
        source,
        "import 'package:{}/cott_runtime.dart' as cott_runtime;\nimport 'package:{}/src/cott_markers.dart' as cott_markers;",
        config.project.name, config.project.name
    )
    .expect("writing to String cannot fail");
    for module in &plan.modules {
        let alias = aliases
            .get(&module.name)
            .ok_or_else(|| format!("missing Dart module alias for `{}`", module.name))?;
        writeln!(
            source,
            "import 'package:{}/modules/{}.dart' as {};",
            config.project.name,
            module.name.replace('.', "/"),
            alias
        )
        .expect("writing to String cannot fail");
    }
    source.push_str(
        r#"
const String _eventPrefix = 'COTT_DART_VERIFY:';
const int _evidenceKeyBytes = 32;

final class EvidenceWriter {
  EvidenceWriter(Uint8List secret) : _secret = Uint8List.fromList(secret) {
    secret.fillRange(0, secret.length, 0);
  }

  final Uint8List _secret;
  int _sequence = 0;

  void emit(Map<String, Object?> event) {
    final payload = jsonEncode(event);
    final sequenceBytes = ByteData(8)..setUint64(0, _sequence, Endian.big);
    final payloadBytes = utf8.encode(payload);
    final authenticated = Uint8List(8 + payloadBytes.length);
    authenticated.setRange(0, 8, sequenceBytes.buffer.asUint8List());
    authenticated.setRange(8, authenticated.length, payloadBytes);
    final tag = Hmac(sha256, _secret).convert(authenticated).toString();
    stdout.writeln('\n$_eventPrefix$_sequence:$tag:$payload');
    _sequence += 1;
  }
}

Future<Uint8List> _readEvidenceKey() async {
  final bytes = <int>[];
  await for (final chunk in stdin) {
    bytes.addAll(chunk);
    if (bytes.length > _evidenceKeyBytes) {
      throw StateError('Dart evidence key has trailing bytes');
    }
  }
  if (bytes.length != _evidenceKeyBytes) {
    throw StateError('Dart evidence key was truncated');
  }
  return Uint8List.fromList(bytes);
}

List<Map<String, Object?>> _observations(cott_runtime.CottObservation observation) =>
    List<Map<String, Object?>>.unmodifiable(observation.observations().map((value) =>
      <String, Object?>{
        'symbol': value.symbol,
        'clause': value.clause,
        'phase': value.phase,
        'status': value.status.name,
        'passed': value.passed,
        'reason': value.reason,
      }));

void _emitCase(
  EvidenceWriter evidence,
  String symbol,
  int caseId,
  String status,
  cott_runtime.CottObservation observation, {
  cott_runtime.CottContractViolation? error,
}) {
  evidence.emit(<String, Object?>{
    'kind': 'case',
    'symbol': symbol,
    'case': caseId,
    'status': status,
    'phase': error?.phase,
    'clause': error?.clause,
    'error_symbol': error?.symbol,
    'observations': _observations(observation),
  });
}

void _emitCancellation(
  EvidenceWriter evidence,
  String scenario,
  int step,
  bool cooperative,
) {
  evidence.emit(<String, Object?>{
    'kind': 'cancellation',
    'symbol': scenario,
    'case': step,
    'status': cooperative ? 'passed' : 'failed',
    'cooperative': cooperative,
    'future_preempted': false,
    'reason': cooperative
        ? 'the verifier-owned scenario worker observed its explicit cancellation token; no Dart Future preemption is claimed'
        : 'the verifier-owned scenario worker did not observe its explicit cancellation token',
  });
}

void _emitScenario(
  EvidenceWriter evidence,
  String id,
  String symbol,
  String status,
  cott_runtime.CottObservation observation,
  int assertions,
  int cancellations,
  bool cleaned,
) {
  evidence.emit(<String, Object?>{
    'kind': 'scenario',
    'scenario_id': id,
    'symbol': symbol,
    'status': status,
    'assertions': assertions,
    'cancellations': cancellations,
    'cleaned': cleaned,
    'observations': _observations(observation),
  });
}

final class _CandidateConst implements cott_runtime.CottConst {
  _CandidateConst(int value) : value = BigInt.from(value);
  @override
  final BigInt value;
}

final class _ScenarioValue<T> {
  const _ScenarioValue(this.value);
  final T value;
}

final class _ScenarioFailure {
  const _ScenarioFailure(this.error, this.stackTrace);
  final Object error;
  final StackTrace stackTrace;
}

final class _ScenarioCancelled {
  const _ScenarioCancelled();
}

final class _ScenarioWorker<T> {
  _ScenarioWorker._(this._underlying) : _scope = cott_runtime.CottTaskScope() {
    _task = _scope.spawn<T>(_race);
    result = _task.result;
  }

  factory _ScenarioWorker.start(Future<T> underlying) =>
      _ScenarioWorker._(underlying);

  final Future<T> _underlying;
  final cott_runtime.CottTaskScope _scope;
  late final cott_runtime.CottTask<T> _task;
  late final Future<T> result;
  bool cancellationObserved = false;

  Future<T> _race(cott_runtime.CottCancellationToken token) async {
    final outcome = await Future.any<Object?>(<Future<Object?>>[
      _underlying.then<Object?>(
        (value) => _ScenarioValue<T>(value),
        onError: (Object error, StackTrace trace) => _ScenarioFailure(error, trace),
      ),
      token.whenCancelled.then<Object?>((_) => const _ScenarioCancelled()),
    ]);
    if (outcome is _ScenarioCancelled) {
      cancellationObserved = true;
      token.throwIfCancelled();
    }
    if (outcome is _ScenarioFailure) {
      Error.throwWithStackTrace(outcome.error, outcome.stackTrace);
    }
    return (outcome as _ScenarioValue<T>).value;
  }

  void cancel(Object reason) => _task.cancel(reason);

  Future<void> close(Duration timeout) async {
    Object? failure;
    StackTrace? failureTrace;
    try {
      await _underlying.timeout(timeout);
    } catch (error, trace) {
      failure = error;
      failureTrace = trace;
    }
    try {
      await _scope.close();
    } on cott_runtime.CottCancellationException catch (error, trace) {
      if (!cancellationObserved) {
        failure ??= error;
        failureTrace ??= trace;
      }
    } catch (error, trace) {
      failure ??= error;
      failureTrace ??= trace;
    }
    if (failure != null) {
      Error.throwWithStackTrace(failure, failureTrace ?? StackTrace.current);
    }
  }
}

final class _ScenarioRoute {
  const _ScenarioRoute.response(this.status, this.body)
      : kind = 'response',
        location = null,
        delay = Duration.zero;
  const _ScenarioRoute.redirect(this.status, this.location)
      : kind = 'redirect',
        body = const <int>[],
        delay = Duration.zero;
  const _ScenarioRoute.delay(this.delay)
      : kind = 'delay',
        status = 204,
        body = const <int>[],
        location = null;

  final String kind;
  final int status;
  final List<int> body;
  final String? location;
  final Duration delay;
}

final class _ScenarioHttpFixture {
  _ScenarioHttpFixture._(
    this._server,
    this._routes,
    this._requestLimit,
    this._bodyLimit,
    this._redirectLimit,
    this._transcriptLimit,
  ) {
    _subscription = _server.listen(_accept);
  }

  static Future<_ScenarioHttpFixture> start(
    Map<String, _ScenarioRoute> routes, {
    required int requestLimit,
    required int bodyLimit,
    required int redirectLimit,
    required int transcriptLimit,
  }) async {
    final server = await HttpServer.bind(InternetAddress.loopbackIPv4, 0, shared: false);
    return _ScenarioHttpFixture._(
      server,
      Map<String, _ScenarioRoute>.unmodifiable(routes),
      requestLimit,
      bodyLimit,
      redirectLimit,
      transcriptLimit,
    );
  }

  final HttpServer _server;
  final Map<String, _ScenarioRoute> _routes;
  final int _requestLimit;
  final int _bodyLimit;
  final int _redirectLimit;
  final int _transcriptLimit;
  final Set<Future<void>> _pending = <Future<void>>{};
  late final StreamSubscription<HttpRequest> _subscription;
  Object? _failure;
  StackTrace? _failureTrace;
  int _requests = 0;
  int _redirects = 0;
  int _transcriptEvents = 0;

  String url(String path) => 'http://127.0.0.1:${_server.port}$path';

  void _accept(HttpRequest request) {
    late final Future<void> operation;
    operation = _handle(request).catchError((Object error, StackTrace trace) {
      _failure ??= error;
      _failureTrace ??= trace;
      try {
        request.response.statusCode = HttpStatus.internalServerError;
        request.response.close();
      } catch (_) {}
    }).whenComplete(() {
      _pending.remove(operation);
    });
    _pending.add(operation);
  }

  Future<void> _handle(HttpRequest request) async {
    _requests += 1;
    _transcriptEvents += 1;
    if (_requests > _requestLimit || _transcriptEvents > _transcriptLimit) {
      throw StateError('HTTP fixture request/transcript limit exceeded');
    }
    var requestBytes = 0;
    await for (final chunk in request) {
      requestBytes += chunk.length;
      if (requestBytes > _bodyLimit) {
        throw StateError('HTTP fixture request body limit exceeded');
      }
    }
    final route = _routes[request.uri.path];
    if (route == null) {
      request.response.statusCode = HttpStatus.notFound;
    } else {
      switch (route.kind) {
        case 'response':
          if (route.body.length > _bodyLimit) {
            throw StateError('HTTP fixture response body limit exceeded');
          }
          request.response.statusCode = route.status;
          request.response.add(route.body);
          break;
        case 'redirect':
          _redirects += 1;
          if (_redirects > _redirectLimit) {
            throw StateError('HTTP fixture redirect limit exceeded');
          }
          request.response.statusCode = route.status;
          request.response.headers.set(HttpHeaders.locationHeader, route.location!);
          break;
        case 'delay':
          await Future<void>.delayed(route.delay);
          request.response.statusCode = route.status;
          break;
        default:
          throw StateError('invalid compiler-owned HTTP fixture route');
      }
    }
    await request.response.close();
    _transcriptEvents += 1;
    if (_transcriptEvents > _transcriptLimit) {
      throw StateError('HTTP fixture transcript limit exceeded');
    }
  }

  Future<void> close(Duration timeout) async {
    try {
      if (_pending.isNotEmpty) {
        await Future.wait<void>(List<Future<void>>.of(_pending)).timeout(timeout);
      }
    } finally {
      await _server.close(force: true);
      await _subscription.cancel();
    }
    final failure = _failure;
    if (failure != null) {
      Error.throwWithStackTrace(failure, _failureTrace ?? StackTrace.current);
    }
  }
}

void _auditFixtureRoot(Directory root, int fileLimit, int byteLimit) {
  var files = 0;
  var bytes = 0;
  for (final entity in root.listSync(recursive: true, followLinks: false)) {
    final type = FileSystemEntity.typeSync(entity.path, followLinks: false);
    if (type == FileSystemEntityType.link) {
      throw StateError('scenario fixture created a symbolic link');
    }
    if (type == FileSystemEntityType.file) {
      files += 1;
      bytes += File(entity.path).lengthSync();
      if (files > fileLimit || bytes > byteLimit) {
        throw StateError('scenario filesystem limit exceeded');
      }
    } else if (type != FileSystemEntityType.directory) {
      throw StateError('scenario fixture created an unsupported filesystem entry');
    }
  }
}
"#,
    );
    Ok(source)
}

fn render_case(
    source: &mut String,
    invocation: &Invocation,
    symbol: &str,
    case: u32,
    verification: &VerificationConfig,
) -> Result<(), String> {
    let rust_name = safe_name(symbol);
    let quoted_symbol = dart_string(symbol);
    writeln!(
        source,
        "Future<void> _case_{rust_name}_{case}(EvidenceWriter evidence) async {{"
    )
    .expect("writing to String cannot fail");
    source.push_str(
        "  final observation = cott_runtime.CottObservation();\n  var invoked = false;\n  try {\n",
    );
    writeln!(
        source,
        "    await cott_runtime.CottRuntime.withTestObservationAsync(observation, () async {{"
    )
    .expect("writing to String cannot fail");
    for line in &invocation.prelude {
        writeln!(source, "      {line}").expect("writing to String cannot fail");
    }
    source.push_str("      invoked = true;\n");
    writeln!(
        source,
        "      final _result = {}{};",
        if invocation.asynchronous {
            "await "
        } else {
            ""
        },
        invocation.call
    )
    .expect("writing to String cannot fail");
    render_protocol_consumption(
        source,
        &invocation.return_type,
        verification.lifecycle_limit,
        6,
    )?;
    writeln!(
        source,
        "    }}).timeout(const Duration(milliseconds: {}));",
        verification.fixtures.scenario_timeout_ms
    )
    .expect("writing to String cannot fail");
    writeln!(
        source,
        "    _emitCase(evidence, {quoted_symbol}, {case}, 'passed', observation);"
    )
    .expect("writing to String cannot fail");
    source.push_str("  } on cott_runtime.CottContractViolation catch (error) {\n");
    writeln!(
        source,
        "    _emitCase(evidence, {quoted_symbol}, {case}, !invoked ? 'candidate_unavailable' : error.phase == 'requires' ? 'ineligible' : 'failed', observation, error: error);"
    )
    .expect("writing to String cannot fail");
    source.push_str("  } on TimeoutException {\n");
    writeln!(
        source,
        "    _emitCase(evidence, {quoted_symbol}, {case}, 'timeout', observation);"
    )
    .expect("writing to String cannot fail");
    source.push_str("  } on cott_runtime.CottCancellationException {\n");
    writeln!(
        source,
        "    _emitCase(evidence, {quoted_symbol}, {case}, 'unexpected_cancellation', observation);"
    )
    .expect("writing to String cannot fail");
    source.push_str("  } catch (_) {\n");
    writeln!(
        source,
        "    _emitCase(evidence, {quoted_symbol}, {case}, 'unexpected_exception', observation);"
    )
    .expect("writing to String cannot fail");
    source.push_str("  }\n}\n\n");
    Ok(())
}

#[allow(clippy::too_many_arguments)]
fn render_callable_cases(
    config: &DartProjectConfig,
    plan: &DartPlan,
    callable: &DartCallable,
    declarations: &BTreeMap<&str, &Value>,
    aliases: &BTreeMap<String, String>,
    verification: &VerificationConfig,
    source: &mut String,
    main_lines: &mut Vec<String>,
) -> Result<u32, RenderFailure> {
    let mut context = candidate_context(config, plan, callable, declarations, aliases)?;
    let parameters = callable
        .declaration
        .get("parameters")
        .and_then(Value::as_array)
        .ok_or_else(|| {
            format!(
                "Dart callable `{}` has no canonical parameters",
                callable.symbol
            )
        })?;
    let parameter_cases = parameter_candidates(parameters, &mut context)?;
    let constructor_cases = callable
        .owner
        .as_ref()
        .map(|owner| constructor_candidates(owner, &mut context))
        .transpose()?
        .unwrap_or_else(|| vec![Vec::new()]);
    let return_type = substitute_type(
        callable
            .declaration
            .get("return_type")
            .ok_or_else(|| format!("Dart callable `{}` has no return type", callable.symbol))?,
        &context.type_arguments,
    );
    let asynchronous = match callable
        .declaration
        .get("callable_kind")
        .and_then(Value::as_str)
    {
        Some("sync") => false,
        Some("async") => true,
        Some(other) => {
            return Err(format!(
                "Dart callable `{}` has unsupported callable kind `{other}`",
                callable.symbol
            )
            .into());
        }
        None => {
            return Err(format!(
                "Dart callable `{}` has no canonical callable kind",
                callable.symbol
            )
            .into());
        }
    };
    let limit = usize::try_from(verification.candidate_limit).unwrap_or(usize::MAX);
    let mut count = 0u32;
    'constructors: for constructor in &constructor_cases {
        for values in &parameter_cases {
            if usize::try_from(count).unwrap_or(usize::MAX) >= limit {
                break 'constructors;
            }
            let invocation = invocation(
                callable,
                parameters,
                constructor,
                values,
                &context,
                return_type.clone(),
                asynchronous,
            )?;
            render_case(source, &invocation, &callable.symbol, count, verification)?;
            main_lines.push(format!(
                "await _case_{}_{}(evidence);",
                safe_name(&callable.symbol),
                count
            ));
            count = count.saturating_add(1);
        }
    }
    if count == 0 {
        return Err(RenderFailure::unavailable(
            "bounded candidate generation produced no well-typed public input",
        ));
    }
    Ok(count)
}

#[allow(clippy::too_many_arguments)]
fn render_initializer_cases(
    config: &DartProjectConfig,
    plan: &DartPlan,
    owner_symbol: &str,
    owner: &Value,
    declarations: &BTreeMap<&str, &Value>,
    aliases: &BTreeMap<String, String>,
    verification: &VerificationConfig,
    source: &mut String,
    main_lines: &mut Vec<String>,
) -> Result<u32, RenderFailure> {
    let mut context = CandidateContext {
        config,
        plan,
        declarations: declarations.clone(),
        aliases,
        marker_module: owner_symbol
            .rsplit_once('.')
            .map(|(module, _)| module)
            .unwrap_or(owner_symbol)
            .to_owned(),
        consts: BTreeMap::new(),
        type_arguments: BTreeMap::new(),
        node_limit: 64,
        container_limit: 3,
    };
    let cases = constructor_candidates(owner, &mut context)?;
    let parameters = initializer_parameters(owner)?;
    let symbol = format!("{owner_symbol}.init");
    let mut count = 0u32;
    for values in cases
        .iter()
        .take(usize::try_from(verification.candidate_limit).unwrap_or(usize::MAX))
    {
        let invocation = Invocation {
            prelude: typed_candidates("_constructor", parameters, values, &context)?,
            call: constructor_invocation(owner, parameters, "_constructor", &context)?,
            return_type: serde_json::json!({"kind": "primitive", "name": "unit"}),
            asynchronous: false,
        };
        render_case(source, &invocation, &symbol, count, verification)?;
        main_lines.push(format!(
            "await _case_{}_{}(evidence);",
            safe_name(&symbol),
            count
        ));
        count = count.saturating_add(1);
    }
    if count == 0 {
        return Err(RenderFailure::unavailable(
            "bounded initializer generation produced no well-typed public input",
        ));
    }
    Ok(count)
}

fn invocation(
    callable: &DartCallable,
    parameters: &[Value],
    constructor: &[String],
    values: &[String],
    context: &CandidateContext<'_>,
    return_type: Value,
    asynchronous: bool,
) -> Result<Invocation, String> {
    if values.len() != parameters.len() {
        return Err("internal Dart candidate arity mismatch".to_owned());
    }
    let mut prelude = context
        .consts
        .iter()
        .map(|(name, value)| {
            format!(
                "final _cott_const_{} = _CandidateConst({value});",
                internal_name(name)
            )
        })
        .collect::<Vec<_>>();
    prelude.extend(typed_candidates("_candidate", parameters, values, context)?);
    let mut positional = callable_positional_arguments("_candidate", parameters, false)?;
    positional.extend(emit::render_consumer_callable_witnesses(
        context.config,
        context.plan,
        callable,
        &context.type_arguments,
        context.aliases,
    )?);
    for generic in callable
        .declaration
        .get("generics")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter(|generic| generic.get("kind").and_then(Value::as_str) == Some("const"))
    {
        let name = generic
            .get("name")
            .and_then(Value::as_str)
            .ok_or_else(|| format!("callable `{}` has nameless const generic", callable.symbol))?;
        if !context.consts.contains_key(name) {
            return Err(format!(
                "const generic `{name}` has no concrete bounded candidate"
            ));
        }
        positional.push(format!("_cott_const_{}", internal_name(name)));
    }
    positional.extend(callable_positional_arguments(
        "_candidate",
        parameters,
        true,
    )?);
    positional.extend(parameter_arguments("_candidate", parameters, true)?);
    let call = if let Some(owner) = callable.owner.as_ref() {
        let constructor_parameters = initializer_parameters(owner)?;
        if constructor_parameters.len() != constructor.len() {
            return Err("internal Dart receiver constructor arity mismatch".to_owned());
        }
        prelude.extend(typed_candidates(
            "_constructor",
            constructor_parameters,
            constructor,
            context,
        )?);
        prelude.push(format!(
            "final _receiver = {};",
            constructor_invocation(owner, constructor_parameters, "_constructor", context)?
        ));
        format!(
            "_receiver.{}({})",
            escape_identifier(local_name(&callable.name))?,
            positional.join(", ")
        )
    } else {
        format!(
            "{}({})",
            emit::render_consumer_symbol(&callable.symbol, context.aliases)?,
            positional.join(", ")
        )
    };
    Ok(Invocation {
        prelude,
        call,
        return_type,
        asynchronous,
    })
}

fn typed_candidates(
    prefix: &str,
    parameters: &[Value],
    values: &[String],
    context: &CandidateContext<'_>,
) -> Result<Vec<String>, String> {
    if parameters.len() != values.len() {
        return Err("internal Dart typed candidate arity mismatch".to_owned());
    }
    parameters
        .iter()
        .zip(values)
        .enumerate()
        .map(|(index, (parameter, value))| {
            let ty = substitute_type(
                parameter
                    .get("type")
                    .ok_or("canonical parameter has no type")?,
                &context.type_arguments,
            );
            if contains_const_parameter(&ty) {
                return Ok(format!("final {prefix}_{index} = {value};"));
            }
            let base = emit::render_consumer_type(context.plan, &ty, context.aliases)?;
            let rendered = match parameter.get("kind").and_then(Value::as_str) {
                Some("vararg") => format!("cott_runtime.CottList<{base}>"),
                Some("kwarg") => format!("cott_runtime.CottKeywordArguments<{base}>"),
                _ => base,
            };
            Ok(format!("final {rendered} {prefix}_{index} = {value};"))
        })
        .collect()
}

fn parameter_arguments(
    prefix: &str,
    parameters: &[Value],
    named: bool,
) -> Result<Vec<String>, String> {
    parameters
        .iter()
        .enumerate()
        .filter_map(|(index, parameter)| {
            let kind = parameter.get("kind").and_then(Value::as_str);
            let is_named = matches!(kind, Some("keyword_only" | "kwarg"));
            (is_named == named).then_some((index, parameter, kind))
        })
        .map(|(index, parameter, kind)| match kind {
            Some("positional" | "vararg") if !named => Ok(format!("{prefix}_{index}")),
            Some("keyword_only" | "kwarg") if named => {
                let name = parameter
                    .get("name")
                    .and_then(Value::as_str)
                    .ok_or("canonical parameter has no name")?;
                Ok(format!("{}: {prefix}_{index}", escape_identifier(name)?))
            }
            Some(other) => Err(format!("unsupported canonical parameter kind `{other}`")),
            None => Err("canonical parameter has no kind".to_owned()),
        })
        .collect()
}

fn callable_positional_arguments(
    prefix: &str,
    parameters: &[Value],
    optional: bool,
) -> Result<Vec<String>, String> {
    parameters
        .iter()
        .enumerate()
        .filter_map(|(index, parameter)| {
            matches!(
                parameter.get("kind").and_then(Value::as_str),
                Some("positional" | "vararg")
            )
            .then_some((index, parameter))
        })
        .filter(|(_, parameter)| {
            parameter
                .get("default")
                .is_some_and(|value| !value.is_null())
                == optional
        })
        .map(|(index, _)| Ok(format!("{prefix}_{index}")))
        .collect()
}

fn constructor_invocation(
    owner: &Value,
    parameters: &[Value],
    prefix: &str,
    context: &CandidateContext<'_>,
) -> Result<String, String> {
    let symbol = owner
        .get("name")
        .and_then(Value::as_str)
        .ok_or("implementation owner has no canonical name")?;
    let positional = parameter_arguments(prefix, parameters, false)?;
    let named = parameter_arguments(prefix, parameters, true)?;
    Ok(emit::render_constructor_invocation(
        &emit::render_consumer_symbol(symbol, context.aliases)?,
        &positional,
        &named,
    ))
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
            writeln!(source, "{prefix}var _steps = 0;").unwrap();
            writeln!(source, "{prefix}while (_steps < {lifecycle_limit} && _result.moveNext()) {{ _steps += 1; }}").unwrap();
            writeln!(source, "{prefix}_result.close();").unwrap();
        }
        Some("generator") => {
            writeln!(source, "{prefix}var _steps = 0;").unwrap();
            writeln!(source, "{prefix}while (_steps < {lifecycle_limit}) {{ final _step = _result.nextStep(); _steps += 1; if (_step is cott_runtime.CottGeneratorReturn) break; }}").unwrap();
            writeln!(source, "{prefix}_result.close();").unwrap();
        }
        Some("async_iterator") => {
            writeln!(source, "{prefix}var _steps = 0;").unwrap();
            writeln!(source, "{prefix}while (_steps < {lifecycle_limit}) {{ final _step = await _result.next(); _steps += 1; if (_step is cott_runtime.CottDone) break; }}").unwrap();
            writeln!(source, "{prefix}await _result.close();").unwrap();
        }
        Some("async_generator") => {
            writeln!(source, "{prefix}var _steps = 0;").unwrap();
            writeln!(source, "{prefix}while (_steps < {lifecycle_limit}) {{ final _step = await _result.next(); _steps += 1; if (_step is cott_runtime.CottGeneratorReturn) break; }}").unwrap();
            writeln!(source, "{prefix}await _result.close();").unwrap();
        }
        Some(_) => {}
        None => return Err("canonical Dart return type is missing kind".to_owned()),
    }
    Ok(())
}

fn candidate_context<'a>(
    config: &'a DartProjectConfig,
    plan: &'a DartPlan,
    callable: &DartCallable,
    declarations: &BTreeMap<&'a str, &'a Value>,
    aliases: &'a BTreeMap<String, String>,
) -> Result<CandidateContext<'a>, RenderFailure> {
    let mut consts = BTreeMap::new();
    let mut type_arguments = BTreeMap::new();
    // Canonical impl methods inherit owner generics; unlike free functions,
    // their declaration intentionally has no separate generic inventory.
    let generic_owner = callable.owner.as_ref().unwrap_or(&callable.declaration);
    let generics = generic_owner
        .get("generics")
        .and_then(Value::as_array)
        .ok_or_else(|| {
            format!(
                "callable `{}` has no canonical generic inventory",
                callable.symbol
            )
        })?;
    for generic in generics {
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
                    .ok_or_else(|| {
                        format!(
                            "callable `{}` generic `{name}` has no bounds",
                            callable.symbol
                        )
                    })?;
                let argument = if bounds.is_empty() {
                    serde_json::json!({"kind": "primitive", "name": "i32"})
                } else {
                    implementation_type_for_bounds(bounds, declarations).ok_or_else(|| {
                        RenderFailure::unavailable(format!(
                            "generic `{name}` has no public constructible implementation witness"
                        ))
                    })?
                };
                type_arguments.insert(name.to_owned(), argument);
            }
            Some(other) => {
                return Err(format!(
                    "callable `{}` has unsupported generic kind `{other}`",
                    callable.symbol
                )
                .into());
            }
            None => {
                return Err(
                    format!("callable `{}` has malformed generics", callable.symbol).into(),
                );
            }
        }
    }
    Ok(CandidateContext {
        config,
        plan,
        declarations: declarations.clone(),
        aliases,
        marker_module: callable.module.clone(),
        consts,
        type_arguments,
        node_limit: 64,
        container_limit: 3,
    })
}

fn implementation_type_for_bound(
    bound: &Value,
    declarations: &BTreeMap<&str, &Value>,
) -> Option<Value> {
    implementation_type_for_bounds(std::slice::from_ref(bound), declarations)
}

fn implementation_type_for_bounds(
    bounds: &[Value],
    declarations: &BTreeMap<&str, &Value>,
) -> Option<Value> {
    declarations.values().find_map(|declaration| {
        let satisfies = |bound: &Value| {
            let required = bound.get("name").and_then(Value::as_str)?;
            let unparameterized = bound
                .get("args")
                .and_then(Value::as_array)
                .is_none_or(Vec::is_empty);
            Some(
                declaration
                    .get("traits")
                    .and_then(Value::as_array)
                    .is_some_and(|traits| {
                        traits.iter().any(|trait_ref| {
                            trait_ref == bound
                                || (unparameterized
                                    && trait_ref.get("name").and_then(Value::as_str).is_some_and(
                                        |actual| {
                                            trait_reaches(
                                                actual,
                                                required,
                                                declarations,
                                                &mut BTreeSet::new(),
                                            )
                                        },
                                    ))
                        })
                    }),
            )
        };
        if declaration.get("kind").and_then(Value::as_str) != Some("impl")
            || declaration.get("public").and_then(Value::as_bool) != Some(true)
            || !bounds.iter().all(|bound| satisfies(bound) == Some(true))
        {
            return None;
        }
        Some(serde_json::json!({
            "kind": "named",
            "name": declaration.get("name").and_then(Value::as_str)?,
            "args": []
        }))
    })
}

fn trait_reaches(
    actual: &str,
    required: &str,
    declarations: &BTreeMap<&str, &Value>,
    seen: &mut BTreeSet<String>,
) -> bool {
    if actual == required {
        return true;
    }
    if !seen.insert(actual.to_owned()) {
        return false;
    }
    declarations
        .get(actual)
        .and_then(|declaration| declaration.get("parents"))
        .and_then(Value::as_array)
        .is_some_and(|parents| {
            parents.iter().any(|parent| {
                parent
                    .get("trait")
                    .and_then(|trait_ref| trait_ref.get("name"))
                    .and_then(Value::as_str)
                    .is_some_and(|parent| trait_reaches(parent, required, declarations, seen))
            })
        })
}

fn parameter_candidates(
    parameters: &[Value],
    context: &mut CandidateContext<'_>,
) -> Result<Vec<Vec<String>>, RenderFailure> {
    let choices = parameters
        .iter()
        .map(|parameter| {
            let values = candidate_values(
                parameter
                    .get("type")
                    .ok_or("canonical parameter has no type")?,
                context,
                0,
            )?;
            match parameter.get("kind").and_then(Value::as_str) {
                Some("positional" | "keyword_only") => Ok(values),
                Some("vararg") => {
                    let mut output = vec!["cott_runtime.CottList(const <Never>[])".to_owned()];
                    if let Some(value) = values.first() {
                        output.push(format!("cott_runtime.CottList([{value}])"));
                    }
                    Ok(output)
                }
                Some("kwarg") => {
                    let mut output = vec![
                        "cott_runtime.CottKeywordArguments(const <String, Never>{})".to_owned(),
                    ];
                    if let Some(value) = values.first() {
                        output.push(format!(
                            "cott_runtime.CottKeywordArguments({{'value': {value}}})"
                        ));
                    }
                    Ok(output)
                }
                Some(other) => {
                    Err(format!("unsupported canonical parameter kind `{other}`").into())
                }
                None => Err("canonical parameter has no kind".into()),
            }
        })
        .collect::<Result<Vec<_>, RenderFailure>>()?;
    Ok(product_bounded(&choices, 1024))
}

fn constructor_candidates(
    owner: &Value,
    context: &mut CandidateContext<'_>,
) -> Result<Vec<Vec<String>>, RenderFailure> {
    parameter_candidates(initializer_parameters(owner)?, context)
}

fn initializer_parameters(owner: &Value) -> Result<&[Value], String> {
    match owner.get("init") {
        Some(Value::Null) => Ok(&[]),
        Some(initializer) => initializer
            .get("parameters")
            .and_then(Value::as_array)
            .map(Vec::as_slice)
            .ok_or_else(|| "Dart canonical initializer has no parameter inventory".to_owned()),
        None => Err("Dart canonical implementation has no initializer field".to_owned()),
    }
}

fn candidate_values(
    ty: &Value,
    context: &mut CandidateContext<'_>,
    depth: usize,
) -> Result<Vec<String>, RenderFailure> {
    if depth >= context.node_limit {
        return Err(RenderFailure::unavailable(
            "Dart candidate node limit exhausted",
        ));
    }
    let ty = substitute_type(ty, &context.type_arguments);
    let object = ty
        .as_object()
        .ok_or("Dart canonical candidate type is not an object")?;
    let kind = object
        .get("kind")
        .and_then(Value::as_str)
        .ok_or("Dart canonical candidate type has no kind")?;
    let candidates = match kind {
        "primitive" => primitive_values(
            object
                .get("name")
                .and_then(Value::as_str)
                .ok_or("Dart primitive candidate has no name")?,
        )?,
        "type_parameter" => {
            let name = object
                .get("name")
                .and_then(Value::as_str)
                .ok_or("Dart type parameter candidate has no name")?;
            let argument = context.type_arguments.get(name).cloned().ok_or_else(|| {
                RenderFailure::unavailable(format!(
                    "generic type parameter `{name}` has no concrete bounded candidate"
                ))
            })?;
            candidate_values(&argument, context, depth + 1)?
        }
        "associated_projection" => {
            return Err(RenderFailure::unavailable(
                "abstract associated type has no concrete runtime candidate",
            ));
        }
        "list" | "set" => {
            let class = if kind == "list" {
                "CottList"
            } else {
                "CottSet"
            };
            let mut values = vec![format!("cott_runtime.{class}(const <Never>[])")];
            match candidate_values(
                object
                    .get("item")
                    .ok_or("container candidate has no item type")?,
                context,
                depth + 1,
            ) {
                Ok(items) => {
                    if let Some(item) = items.first() {
                        values.push(format!("cott_runtime.{class}([{item}])"));
                    }
                }
                Err(RenderFailure::Unavailable(_)) => {}
                Err(error @ RenderFailure::Fatal(_)) => return Err(error),
            }
            values
        }
        "option" => {
            let mut values = vec!["const cott_runtime.Nothing()".to_owned()];
            match candidate_values(
                object
                    .get("item")
                    .ok_or("Option candidate has no item type")?,
                context,
                depth + 1,
            ) {
                Ok(items) => {
                    if let Some(item) = items.first() {
                        values.push(format!("cott_runtime.Some({item})"));
                    }
                }
                Err(RenderFailure::Unavailable(_)) => {}
                Err(error @ RenderFailure::Fatal(_)) => return Err(error),
            }
            values
        }
        "map" => {
            let mut values = vec![
                "cott_runtime.CottMap(const <cott_runtime.CottMapEntry<Never, Never>>[])"
                    .to_owned(),
            ];
            let key = optional_candidate(candidate_values(
                object.get("key").ok_or("Map candidate has no key type")?,
                context,
                depth + 1,
            ))?;
            let item = optional_candidate(candidate_values(
                object
                    .get("value")
                    .ok_or("Map candidate has no value type")?,
                context,
                depth + 1,
            ))?;
            if let (Some(key), Some(item)) = (key, item) {
                values.push(format!(
                    "cott_runtime.CottMap([cott_runtime.CottMapEntry({key}, {item})])"
                ));
            }
            values
        }
        "tuple" => {
            let items = object
                .get("items")
                .and_then(Value::as_array)
                .ok_or("Tuple candidate has no items")?;
            let values = items
                .iter()
                .map(|item| {
                    candidate_values(item, context, depth + 1)?
                        .into_iter()
                        .next()
                        .ok_or_else(|| RenderFailure::unavailable("Tuple item has no candidate"))
                })
                .collect::<Result<Vec<_>, RenderFailure>>()?;
            vec![format!(
                "cott_markers.CottTuple{}({})",
                values.len(),
                values.join(", ")
            )]
        }
        "result" => {
            let ok = optional_candidate(candidate_values(
                object.get("ok").ok_or("Result candidate has no ok type")?,
                context,
                depth + 1,
            ))?;
            let error = optional_candidate(candidate_values(
                object
                    .get("error")
                    .ok_or("Result candidate has no error type")?,
                context,
                depth + 1,
            ))?;
            let mut values = Vec::new();
            if let Some(value) = ok {
                values.push(format!("cott_runtime.Ok({value})"));
            }
            if let Some(value) = error {
                values.push(format!("cott_runtime.Err({value})"));
            }
            if values.is_empty() {
                return Err(RenderFailure::unavailable(
                    "Result has no constructible branch",
                ));
            }
            values
        }
        "array" => {
            let (witness, length) = const_witness(
                object
                    .get("length")
                    .ok_or("Array candidate has no length")?,
                context,
            )?;
            if length > context.container_limit {
                return Err(RenderFailure::unavailable(format!(
                    "Array candidate length {length} exceeds bounded container limit {}",
                    context.container_limit
                )));
            }
            let values = if length == 0 {
                String::new()
            } else {
                let item = candidate_values(
                    object
                        .get("item")
                        .ok_or("Array candidate has no item type")?,
                    context,
                    depth + 1,
                )?
                .into_iter()
                .next()
                .ok_or_else(|| RenderFailure::unavailable("Array item has no candidate"))?;
                vec![item; length].join(", ")
            };
            vec![format!("cott_runtime.CottArray([{values}], {witness})")]
        }
        "buffer" => {
            let (witness, length) = const_witness(
                object
                    .get("length")
                    .ok_or("Buffer candidate has no length")?,
                context,
            )?;
            if length > context.container_limit {
                return Err(RenderFailure::unavailable(format!(
                    "Buffer candidate length {length} exceeds bounded container limit {}",
                    context.container_limit
                )));
            }
            vec![format!(
                "cott_runtime.CottBuffer(List<int>.filled({length}, 0), {witness})"
            )]
        }
        "future" => {
            let item = candidate_values(
                object
                    .get("item")
                    .ok_or("Future candidate has no item type")?,
                context,
                depth + 1,
            )?
            .into_iter()
            .next()
            .ok_or_else(|| RenderFailure::unavailable("Future item has no candidate"))?;
            vec![format!("Future.value({item})")]
        }
        "named" => named_candidates(&ty, context, depth + 1)?,
        "factory" => {
            let instance = object
                .get("instance")
                .ok_or("Factory candidate has no instance")?
                .get("name")
                .and_then(Value::as_str)
                .ok_or_else(|| {
                    RenderFailure::unavailable(
                        "Factory candidate is not a concrete named implementation",
                    )
                })?;
            let instance_type = serde_json::json!({
                "kind": "named",
                "name": instance,
                "args": object
                    .get("instance")
                    .and_then(|value| value.get("args"))
                    .cloned()
                    .unwrap_or_else(|| Value::Array(Vec::new())),
            });
            let candidate = candidate_values(&instance_type, context, depth + 1)?
                .into_iter()
                .next()
                .ok_or_else(|| {
                    RenderFailure::unavailable(
                        "Factory implementation has no constructible candidate",
                    )
                })?;
            vec![format!(
                "cott_runtime.CottFactory.zero({}, () => {candidate})",
                emit::render_consumer_symbol(instance, context.aliases)?
            )]
        }
        "iterator" | "async_iterator" | "generator" | "async_generator" => {
            return Err(RenderFailure::unavailable(format!(
                "protocol input `{kind}` has no compiler-owned source fixture"
            )));
        }
        "dyn" => {
            let trait_ref = object
                .get("trait")
                .ok_or("Dyn candidate has no trait reference")?;
            let concrete = implementation_type_for_bound(trait_ref, &context.declarations)
                .ok_or_else(|| {
                    RenderFailure::unavailable(
                        "Dyn trait has no public concrete implementation candidate",
                    )
                })?;
            candidate_values(&concrete, context, depth + 1)?
                .into_iter()
                .map(|value| {
                    emit::render_consumer_dyn(context.plan, trait_ref, &value, context.aliases)
                })
                .collect::<Result<Vec<_>, String>>()?
        }
        "opaque" => {
            let tag = object
                .get("tag")
                .and_then(Value::as_str)
                .ok_or("Opaque candidate has no tag")?;
            vec![emit::render_consumer_opaque(
                tag,
                "Object()",
                &context.marker_module,
                context.aliases,
            )?]
        }
        other => {
            return Err(format!("unsupported bounded Dart candidate type `{other}`").into());
        }
    };
    let mut unique = BTreeSet::new();
    Ok(candidates
        .into_iter()
        .filter(|candidate| unique.insert(candidate.clone()))
        .collect())
}

fn optional_candidate(
    result: Result<Vec<String>, RenderFailure>,
) -> Result<Option<String>, RenderFailure> {
    match result {
        Ok(candidates) => Ok(candidates.into_iter().next()),
        Err(RenderFailure::Unavailable(_)) => Ok(None),
        Err(error @ RenderFailure::Fatal(_)) => Err(error),
    }
}

fn named_candidates(
    ty: &Value,
    context: &mut CandidateContext<'_>,
    depth: usize,
) -> Result<Vec<String>, RenderFailure> {
    let name = ty
        .get("name")
        .and_then(Value::as_str)
        .ok_or("named Dart candidate has no name")?;
    let declaration = context
        .declarations
        .get(name)
        .copied()
        .ok_or_else(|| format!("named Dart candidate `{name}` is absent from canonical IR"))?;
    let substitutions = named_substitutions(declaration, ty)?;
    let mut nested = context.clone();
    nested.type_arguments.extend(substitutions);
    nested.marker_module = name
        .rsplit_once('.')
        .map(|(module, _)| module)
        .unwrap_or(name)
        .to_owned();
    let type_witnesses =
        emit::render_consumer_type_witnesses(context.config, context.plan, ty, context.aliases)?;
    let const_witnesses = named_const_witnesses(declaration, ty)?;
    let constructor = emit::render_consumer_symbol(name, context.aliases)?;
    match declaration.get("kind").and_then(Value::as_str) {
        Some("alias") => candidate_values(
            declaration
                .get("target")
                .ok_or_else(|| format!("alias `{name}` has no target"))?,
            &mut nested,
            depth,
        ),
        Some("newtype") => {
            let values = candidate_values(
                declaration
                    .get("carrier")
                    .ok_or_else(|| format!("newtype `{name}` has no carrier"))?,
                &mut nested,
                depth,
            )?;
            Ok(values
                .into_iter()
                .map(|value| {
                    nominal_construction(
                        &constructor,
                        &type_witnesses,
                        &[format!("value: {value}")],
                        &const_witnesses,
                    )
                })
                .collect())
        }
        Some("struct") => {
            let fields = declaration
                .get("fields")
                .and_then(Value::as_array)
                .ok_or_else(|| format!("struct `{name}` has no fields"))?;
            let choices = field_candidates(fields, &mut nested, depth)?;
            let mut output = Vec::new();
            for values in product_bounded(&choices, 16) {
                let named = fields
                    .iter()
                    .zip(values)
                    .map(|(field, value)| {
                        let field = field
                            .get("name")
                            .and_then(Value::as_str)
                            .ok_or("canonical struct field has no name")?;
                        Ok(format!("{}: {value}", escape_identifier(field)?))
                    })
                    .collect::<Result<Vec<_>, RenderFailure>>()?;
                output.push(nominal_construction(
                    &constructor,
                    &type_witnesses,
                    &named,
                    &const_witnesses,
                ));
            }
            Ok(output)
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
                let choices = match field_candidates(fields, &mut nested, depth) {
                    Ok(choices) => choices,
                    Err(RenderFailure::Unavailable(_)) => continue,
                    Err(error @ RenderFailure::Fatal(_)) => return Err(error),
                };
                let variant = emit::render_consumer_enum_variant(symbol, context.aliases)?;
                for values in product_bounded(&choices, 4) {
                    let named = values
                        .into_iter()
                        .enumerate()
                        .map(|(index, value)| format!("field{index}: {value}"))
                        .collect::<Vec<_>>();
                    output.push(nominal_construction(
                        &variant,
                        &type_witnesses,
                        &named,
                        &const_witnesses,
                    ));
                }
            }
            Ok(output)
        }
        Some("resource") => {
            let initial = declaration
                .get("initial")
                .and_then(Value::as_str)
                .ok_or_else(|| format!("resource `{name}` has no initial state"))?;
            Ok(vec![format!(
                "{}()",
                emit::render_consumer_enum_variant(initial, context.aliases)?
            )])
        }
        Some("impl") => {
            let parameters = initializer_parameters(declaration)?;
            let cases = constructor_candidates(declaration, &mut nested)?;
            cases
                .iter()
                .map(|values| {
                    let mut positional = Vec::new();
                    let mut named = Vec::new();
                    for (parameter, value) in parameters.iter().zip(values) {
                        if matches!(
                            parameter.get("kind").and_then(Value::as_str),
                            Some("keyword_only" | "kwarg")
                        ) {
                            named.push(format!(
                                "{}: {value}",
                                escape_identifier(
                                    parameter.get("name").and_then(Value::as_str).ok_or(
                                        "implementation initializer parameter has no name"
                                    )?
                                )?
                            ));
                        } else {
                            positional.push(value.clone());
                        }
                    }
                    Ok(emit::render_constructor_invocation(
                        &constructor,
                        &positional,
                        &named,
                    ))
                })
                .collect::<Result<Vec<_>, RenderFailure>>()
        }
        Some("trait") => {
            let concrete =
                implementation_type_for_bound(ty, &nested.declarations).ok_or_else(|| {
                    RenderFailure::unavailable(format!(
                        "trait `{name}` has no public concrete implementation candidate"
                    ))
                })?;
            candidate_values(&concrete, &mut nested, depth)
        }
        Some("external_type") => Err(RenderFailure::unavailable(format!(
            "external type `{name}` has no compiler-owned value constructor"
        ))),
        Some(other) => {
            Err(format!("named Dart candidate `{name}` has unsupported kind `{other}`").into())
        }
        None => Err(format!("named Dart candidate `{name}` has malformed declaration").into()),
    }
}

fn nominal_construction(
    constructor: &str,
    positional: &[String],
    named: &[String],
    const_witnesses: &[String],
) -> String {
    let mut all_named = named.to_vec();
    all_named.extend(const_witnesses.iter().cloned());
    emit::render_constructor_invocation(constructor, positional, &all_named)
}

fn named_const_witnesses(declaration: &Value, ty: &Value) -> Result<Vec<String>, String> {
    let generics = declaration
        .get("generics")
        .and_then(Value::as_array)
        .ok_or("named declaration has no generic inventory")?;
    let arguments = ty
        .get("args")
        .and_then(Value::as_array)
        .ok_or("named type has no generic argument inventory")?;
    generics
        .iter()
        .zip(arguments)
        .filter(|(generic, _)| generic.get("kind").and_then(Value::as_str) == Some("const"))
        .map(|(generic, argument)| {
            let name = generic
                .get("name")
                .and_then(Value::as_str)
                .ok_or("named const generic has no name")?;
            let value = argument
                .get("value")
                .ok_or("named const generic argument has no value")?;
            Ok(format!(
                "cottConst{}: {}",
                pascal_identifier(name)?,
                super::types::render_const_witness(value)?
            ))
        })
        .collect()
}

fn field_candidates(
    fields: &[Value],
    context: &mut CandidateContext<'_>,
    depth: usize,
) -> Result<Vec<Vec<String>>, RenderFailure> {
    fields
        .iter()
        .map(|field| {
            candidate_values(
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
        .ok_or("named declaration has no generic inventory")?;
    let arguments = ty
        .get("args")
        .and_then(Value::as_array)
        .ok_or("named type has no generic argument inventory")?;
    if generics.len() != arguments.len() {
        return Err("named Dart candidate generic arity mismatch".to_owned());
    }
    let mut result = BTreeMap::new();
    for (generic, argument) in generics.iter().zip(arguments) {
        if generic.get("kind").and_then(Value::as_str) != Some("type") {
            continue;
        }
        let name = generic
            .get("name")
            .and_then(Value::as_str)
            .ok_or("named Dart generic has no name")?;
        let value = argument
            .get("type")
            .cloned()
            .ok_or("named Dart generic type argument has no type")?;
        result.insert(name.to_owned(), value);
    }
    Ok(result)
}

fn substitute_type(value: &Value, substitutions: &BTreeMap<String, Value>) -> Value {
    if value.get("kind").and_then(Value::as_str) == Some("type_parameter")
        && let Some(name) = value.get("name").and_then(Value::as_str)
        && let Some(replacement) = substitutions.get(name)
    {
        return replacement.clone();
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

fn const_witness(
    value: &Value,
    context: &CandidateContext<'_>,
) -> Result<(String, usize), RenderFailure> {
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
            .map_err(|_| {
                RenderFailure::unavailable(format!(
                    "const parameter `{name}` candidate is not a bounded length"
                ))
            })?;
        return Ok((format!("_cott_const_{}", internal_name(name)), numeric));
    }
    let witness = super::types::render_const_witness(value)?;
    let numeric =
        const_numeric(value, &context.declarations).map_err(RenderFailure::unavailable)?;
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
            declarations
                .get(symbol)
                .copied()
                .and_then(|declaration| declaration.pointer("/value/value"))
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

fn pascal_identifier(name: &str) -> Result<String, String> {
    escape_identifier(name)?;
    let mut characters = name.chars();
    let first = characters
        .next()
        .ok_or_else(|| "empty Dart generic name".to_owned())?;
    Ok(first.to_ascii_uppercase().to_string() + characters.as_str())
}

fn primitive_values(name: &str) -> Result<Vec<String>, String> {
    match name.to_ascii_lowercase().as_str() {
        "unit" => Ok(vec!["cott_runtime.UNIT".to_owned()]),
        "bool" => Ok(vec!["false".to_owned(), "true".to_owned()]),
        "str" | "string" => Ok(vec!["''".to_owned(), "'cott'".to_owned()]),
        "bytes" => Ok(vec![
            "cott_runtime.CottBytes(const <int>[])".to_owned(),
            "cott_runtime.CottBytes(const <int>[0, 255])".to_owned(),
        ]),
        "path" => Ok(vec!["cott_runtime.CottPath('fixture')".to_owned()]),
        "json" => Ok(vec![
            "const cott_runtime.JsonNull()".to_owned(),
            "cott_runtime.JsonInteger(BigInt.zero)".to_owned(),
        ]),
        "i8" => signed_values(-128, 127),
        "i16" => signed_values(-32768, 32767),
        "i32" => signed_values(-2147483648, 2147483647),
        "u8" => unsigned_values(255),
        "u16" => unsigned_values(65535),
        "u32" => unsigned_values(4294967295),
        "i64" => Ok(vec![
            "BigInt.zero".to_owned(),
            "BigInt.one".to_owned(),
            "BigInt.from(-1)".to_owned(),
            "BigInt.parse('-9223372036854775808')".to_owned(),
            "BigInt.parse('9223372036854775807')".to_owned(),
        ]),
        "u64" => Ok(vec![
            "BigInt.zero".to_owned(),
            "BigInt.one".to_owned(),
            "BigInt.parse('18446744073709551615')".to_owned(),
        ]),
        "f32" | "f64" => Ok(vec!["0.0".to_owned(), "1.0".to_owned(), "-1.0".to_owned()]),
        "any" | "unknown" => Ok(vec![
            "null".to_owned(),
            "0".to_owned(),
            "'candidate'".to_owned(),
        ]),
        "never" => Ok(Vec::new()),
        other => Err(format!("unsupported Dart primitive candidate `{other}`")),
    }
}

fn signed_values(minimum: i64, maximum: i64) -> Result<Vec<String>, String> {
    Ok(vec![
        "0".to_owned(),
        "1".to_owned(),
        "-1".to_owned(),
        "2".to_owned(),
        "99".to_owned(),
        "100".to_owned(),
        minimum.to_string(),
        maximum.to_string(),
    ])
}

fn unsigned_values(maximum: u64) -> Result<Vec<String>, String> {
    Ok(vec![
        "0".to_owned(),
        "1".to_owned(),
        "2".to_owned(),
        "99".to_owned(),
        "100".to_owned(),
        maximum.to_string(),
    ])
}

fn product_bounded(choices: &[Vec<String>], limit: usize) -> Vec<Vec<String>> {
    if limit == 0 || choices.iter().any(Vec::is_empty) {
        return Vec::new();
    }
    let mut product = vec![Vec::new()];
    for values in choices {
        let mut next = Vec::new();
        'outer: for prefix in &product {
            for value in values {
                let mut candidate = prefix.clone();
                candidate.push(value.clone());
                next.push(candidate);
                if next.len() == limit {
                    break 'outer;
                }
            }
        }
        product = next;
    }
    product
}

fn render_scenario(
    plan: &DartPlan,
    strategy: &ContractTestStrategy,
    aliases: &BTreeMap<String, String>,
    source: &mut String,
    main_lines: &mut Vec<String>,
    expected_cancellations: &mut BTreeSet<(String, u32)>,
) -> Result<(bool, ScenarioExpectation), RenderFailure> {
    let scenario = strategy
        .scenario
        .as_ref()
        .ok_or("Dart scenario strategy is missing")?;
    if scenario.steps.len() > usize::try_from(scenario.lifecycle_limit).unwrap_or(usize::MAX) {
        return Err(RenderFailure::unavailable(format!(
            "Dart scenario `{}` exceeds its finite lifecycle limit",
            scenario.id
        )));
    }
    for fixture in &scenario.fixtures {
        match fixture.get("kind").and_then(Value::as_str) {
            Some("fs" | "http") => {}
            Some("clock") => {
                return Err(RenderFailure::unavailable(
                    "clock fixture has no Dart runtime interception authority",
                ));
            }
            Some("failure") => {
                return Err(RenderFailure::unavailable(
                    "failure fixture has no Dart runtime interception authority",
                ));
            }
            Some(other) => {
                return Err(format!("unsupported Dart scenario fixture `{other}`").into());
            }
            None => return Err("Dart scenario fixture has no kind".into()),
        }
    }
    for step in &scenario.steps {
        if matches!(
            step.get("kind").and_then(Value::as_str),
            Some("call" | "spawn")
        ) {
            let target = step
                .get("target")
                .and_then(Value::as_str)
                .ok_or("Dart scenario call has no target")?;
            let callable = plan
                .callables()
                .iter()
                .find(|callable| callable.symbol == target)
                .ok_or_else(|| format!("Dart scenario target `{target}` is not callable"))?;
            if !callable_is_public(callable)? {
                return Err(RenderFailure::unavailable(format!(
                    "scenario target `{target}` is not a public consumer facade"
                )));
            }
            if callable.owner.is_some() {
                return Err(RenderFailure::unavailable(
                    "implementation-method scenarios require an explicit receiver fixture",
                ));
            }
            let generics = callable
                .declaration
                .get("generics")
                .and_then(Value::as_array)
                .ok_or_else(|| {
                    format!("Dart scenario target `{target}` has no generic inventory")
                })?;
            if !generics.is_empty() {
                return Err(RenderFailure::unavailable(format!(
                    "generic scenario target `{target}` has no explicit concrete scenario witness"
                )));
            }
        }
    }

    let workers = scenario
        .steps
        .iter()
        .filter(|step| step.get("kind").and_then(Value::as_str) == Some("spawn"))
        .map(|step| {
            let worker = step
                .get("worker")
                .and_then(Value::as_str)
                .ok_or("Dart scenario spawn has no worker")?;
            let ty = step
                .get("return_type")
                .ok_or("Dart scenario spawn has no return type")?;
            Ok((
                escape_identifier(local_name(worker))?,
                emit::render_consumer_type(plan, ty, aliases)?,
            ))
        })
        .collect::<Result<Vec<_>, String>>()?;

    let function = format!("_scenario_{}", safe_name(&scenario.id));
    let mut rendered = String::new();
    writeln!(
        rendered,
        "\nFuture<void> {function}(EvidenceWriter evidence) async {{"
    )
    .unwrap();
    rendered.push_str(
        "  final _observation = cott_runtime.CottObservation();\n  var _assertions = 0;\n  var _cancellations = 0;\n  var _status = 'passed';\n  var _cleaned = false;\n  Directory? _root;\n",
    );
    for (worker, ty) in &workers {
        writeln!(
            rendered,
            "  late _ScenarioWorker<{ty}> {worker};\n  var _started_{worker} = false;\n  var _awaited_{worker} = false;"
        )
        .unwrap();
    }
    let http_fixtures = scenario
        .fixtures
        .iter()
        .filter(|fixture| fixture.get("kind").and_then(Value::as_str) == Some("http"))
        .collect::<Vec<_>>();
    for index in 0..http_fixtures.len() {
        writeln!(
            rendered,
            "  late _ScenarioHttpFixture _http_{index};\n  var _started_http_{index} = false;"
        )
        .unwrap();
    }
    rendered.push_str("  try {\n");
    writeln!(
        rendered,
        "    _root = await Directory.current.createTemp({});",
        dart_string(&format!("cott-{}-", safe_name(&scenario.id)))
    )
    .unwrap();

    let mut fixture_bytes = 0u64;
    let mut needs_loopback = false;
    let mut http_index = 0usize;
    for fixture in &scenario.fixtures {
        let fixture_id = fixture
            .get("id")
            .and_then(Value::as_str)
            .ok_or("Dart scenario fixture has no id")?;
        let fixture_local = escape_identifier(local_name(fixture_id))?;
        writeln!(
            rendered,
            "    final {fixture_local} = {};",
            dart_string(fixture_id)
        )
        .unwrap();
        match fixture.get("kind").and_then(Value::as_str) {
            Some("fs") => {
                let files = fixture
                    .get("files")
                    .and_then(Value::as_array)
                    .ok_or("Dart filesystem fixture has no files")?;
                if files.len()
                    > usize::try_from(scenario.limits.filesystem_files).unwrap_or(usize::MAX)
                {
                    return Err(RenderFailure::unavailable(
                        "Dart scenario fixture exceeds its bounded file-count limit",
                    ));
                }
                for file in files {
                    let path = file
                        .get("path")
                        .and_then(Value::as_str)
                        .ok_or("Dart filesystem fixture file has no path")?;
                    validate_fixture_path(path, false)?;
                    let data = file
                        .get("data")
                        .ok_or("Dart filesystem fixture file has no data")?;
                    let bytes = render_fixture_bytes(data)?;
                    fixture_bytes = fixture_bytes.saturating_add(fixture_data_len(data)?);
                    if fixture_bytes > scenario.limits.filesystem_bytes || fixture_bytes > 1_048_576
                    {
                        return Err(RenderFailure::unavailable(
                            "Dart scenario fixture source exceeds its bounded byte limit",
                        ));
                    }
                    writeln!(
                        rendered,
                        "    {{ final _file = File(_root!.path + '/' + {fixture_local} + '/' + {}); await _file.parent.create(recursive: true); await _file.writeAsBytes({bytes}, flush: true); }}",
                        dart_string(path)
                    )
                    .unwrap();
                }
            }
            Some("http") => {
                needs_loopback = true;
                let routes = fixture
                    .get("routes")
                    .and_then(Value::as_array)
                    .ok_or("Dart HTTP fixture has no routes")?;
                writeln!(rendered, "    _http_{http_index} = await _ScenarioHttpFixture.start(<String, _ScenarioRoute>{{").unwrap();
                for route in routes {
                    let path = route
                        .get("path")
                        .and_then(Value::as_str)
                        .ok_or("Dart HTTP fixture route has no path")?;
                    validate_fixture_path(path, true)?;
                    let outcome = route
                        .get("outcome")
                        .ok_or("Dart HTTP fixture route has no outcome")?;
                    let route_value = render_http_route(outcome, &scenario.limits)?;
                    writeln!(rendered, "      {}: {route_value},", dart_string(path)).unwrap();
                }
                writeln!(
                    rendered,
                    "    }}, requestLimit: {}, bodyLimit: {}, redirectLimit: {}, transcriptLimit: {});",
                    scenario.limits.http_requests,
                    scenario.limits.http_body_bytes,
                    scenario.limits.http_redirects,
                    scenario.limits.transcript_events
                )
                .unwrap();
                writeln!(rendered, "    _started_http_{http_index} = true;").unwrap();
                http_index += 1;
            }
            _ => unreachable!("fixtures prevalidated"),
        }
    }

    rendered.push_str("    final _fixtureUrls = <cott_runtime.CottFixtureKey, String>{\n");
    http_index = 0;
    for fixture in &http_fixtures {
        let fixture_id = fixture
            .get("id")
            .and_then(Value::as_str)
            .ok_or("Dart HTTP fixture has no id")?;
        let fixture_local = escape_identifier(local_name(fixture_id))?;
        for route in fixture
            .get("routes")
            .and_then(Value::as_array)
            .ok_or("Dart HTTP fixture has no routes")?
        {
            let path = route
                .get("path")
                .and_then(Value::as_str)
                .ok_or("Dart HTTP fixture route has no path")?;
            writeln!(
                rendered,
                "      cott_runtime.CottFixtureKey({fixture_local}, {}): _http_{http_index}.url({}),",
                dart_string(path),
                dart_string(path)
            )
            .unwrap();
        }
        http_index += 1;
    }
    rendered.push_str(
        "    };\n    final _fixtures = cott_runtime.CottFixtureContext(root: cott_runtime.CottPath(_root!.path), urls: _fixtureUrls);\n",
    );
    writeln!(
        rendered,
        "    await cott_runtime.CottRuntime.withTestObservationAsync(_observation, () => cott_runtime.CottRuntime.withFixtureContextAsync(_fixtures, () async {{"
    )
    .unwrap();

    let worker_types = workers.iter().cloned().collect::<BTreeMap<_, _>>();
    let mut local_cancellations = BTreeSet::new();
    let mut assertions = 0u32;
    let mut cancellations = 0u32;
    for step in &scenario.steps {
        let step_id = step
            .get("step_id")
            .and_then(Value::as_u64)
            .and_then(|value| u32::try_from(value).ok())
            .ok_or("Dart scenario step has invalid step_id")?;
        match step.get("kind").and_then(Value::as_str) {
            Some("call") => {
                let binding = step
                    .get("binding")
                    .and_then(Value::as_str)
                    .ok_or("Dart scenario call has no binding")?;
                let target = step
                    .get("target")
                    .and_then(Value::as_str)
                    .ok_or("Dart scenario call has no target")?;
                let arguments = scenario_arguments(step, aliases)?;
                let asynchronous =
                    step.get("callable_kind").and_then(Value::as_str) == Some("async");
                writeln!(
                    rendered,
                    "      final {} = {}{}({});",
                    escape_identifier(local_name(binding))?,
                    if asynchronous { "await " } else { "" },
                    emit::render_consumer_symbol(target, aliases)?,
                    arguments.join(", ")
                )
                .unwrap();
            }
            Some("spawn") => {
                let worker = escape_identifier(local_name(
                    step.get("worker")
                        .and_then(Value::as_str)
                        .ok_or("Dart scenario spawn has no worker")?,
                ))?;
                let ty = worker_types
                    .get(&worker)
                    .ok_or("Dart scenario worker type is missing")?;
                let target = step
                    .get("target")
                    .and_then(Value::as_str)
                    .ok_or("Dart scenario spawn has no target")?;
                let arguments = scenario_arguments(step, aliases)?;
                writeln!(
                    rendered,
                    "      {worker} = _ScenarioWorker<{ty}>.start(Future<{ty}>.sync(() => {}({})));",
                    emit::render_consumer_symbol(target, aliases)?,
                    arguments.join(", ")
                )
                .unwrap();
                writeln!(rendered, "      _started_{worker} = true;").unwrap();
            }
            Some("tick") => {
                rendered.push_str("      await Future<void>.delayed(Duration.zero);\n");
            }
            Some("cancel") => {
                let worker = escape_identifier(local_name(
                    step.get("worker")
                        .and_then(Value::as_str)
                        .ok_or("Dart scenario cancel has no worker")?,
                ))?;
                writeln!(
                    rendered,
                    "      {worker}.cancel({});",
                    dart_string(&format!("scenario {} step {step_id}", scenario.id))
                )
                .unwrap();
            }
            Some("await") => {
                let worker = escape_identifier(local_name(
                    step.get("worker")
                        .and_then(Value::as_str)
                        .ok_or("Dart scenario await has no worker")?,
                ))?;
                if step.get("cancelled").and_then(Value::as_bool) == Some(true) {
                    writeln!(rendered, "      try {{ await {worker}.result; throw StateError('scenario step {step_id} expected cooperative cancellation'); }} on cott_runtime.CottCancellationException {{ if (!{worker}.cancellationObserved) rethrow; _cancellations += 1; _emitCancellation(evidence, {}, {step_id}, true); }}", dart_string(&scenario.id)).unwrap();
                    cancellations = cancellations.saturating_add(1);
                    local_cancellations.insert((scenario.id.clone(), step_id));
                } else if let Some(result) = step.get("result").and_then(Value::as_str) {
                    writeln!(
                        rendered,
                        "      final {} = await {worker}.result;",
                        escape_identifier(local_name(result))?
                    )
                    .unwrap();
                } else {
                    writeln!(rendered, "      await {worker}.result;").unwrap();
                }
                writeln!(rendered, "      _awaited_{worker} = true;").unwrap();
            }
            Some("assert") => {
                let expression = emit::render_consumer_expression(
                    step.get("expression")
                        .ok_or("Dart scenario assertion has no expression")?,
                    aliases,
                )?;
                writeln!(
                    rendered,
                    "      if (!({expression})) throw StateError('scenario assertion step:{step_id} failed');\n      _assertions += 1;"
                )
                .unwrap();
                assertions = assertions.saturating_add(1);
            }
            Some(other) => {
                return Err(format!("unsupported Dart scenario step `{other}`").into());
            }
            None => return Err("Dart scenario step has no kind".into()),
        }
    }
    writeln!(
        rendered,
        "    }})).timeout(const Duration(milliseconds: {}));",
        scenario.limits.scenario_timeout_ms
    )
    .unwrap();
    writeln!(
        rendered,
        "    _auditFixtureRoot(_root!, {}, {});",
        scenario.limits.filesystem_files, scenario.limits.filesystem_bytes
    )
    .unwrap();
    rendered.push_str("  } catch (_) {\n    _status = 'failed';\n  } finally {\n");
    for (worker, _) in &workers {
        writeln!(
            rendered,
            "    if (_started_{worker}) {{ if (!_awaited_{worker}) _status = 'failed'; try {{ await {worker}.close(const Duration(milliseconds: {})); }} catch (_) {{ _status = 'failed'; }} }}",
            scenario.limits.scenario_timeout_ms
        )
        .unwrap();
    }
    for index in 0..http_fixtures.len() {
        writeln!(
            rendered,
            "    if (_started_http_{index}) {{ try {{ await _http_{index}.close(const Duration(milliseconds: {})); }} catch (_) {{ _status = 'failed'; }} }}",
            scenario.limits.scenario_timeout_ms
        )
        .unwrap();
    }
    rendered.push_str(
        "    final _cleanupRoot = _root;\n    if (_cleanupRoot != null) {\n      try {\n        if (await _cleanupRoot.exists()) await _cleanupRoot.delete(recursive: true);\n        _cleaned = !(await _cleanupRoot.exists());\n      } catch (_) {\n        _status = 'failed';\n        _cleaned = false;\n      }\n    }\n  }\n",
    );
    writeln!(
        rendered,
        "  _emitScenario(evidence, {}, {}, _status, _observation, _assertions, _cancellations, _cleaned);\n}}",
        dart_string(&scenario.id),
        dart_string(&strategy.symbol)
    )
    .unwrap();

    source.push_str(&rendered);
    main_lines.push(format!("await {function}(evidence);"));
    expected_cancellations.extend(local_cancellations);
    Ok((
        needs_loopback,
        ScenarioExpectation {
            symbol: strategy.symbol.clone(),
            assertions,
            cancellations,
        },
    ))
}

fn scenario_arguments(
    step: &Value,
    aliases: &BTreeMap<String, String>,
) -> Result<Vec<String>, String> {
    step.get("arguments")
        .and_then(Value::as_array)
        .ok_or("Dart scenario call has no arguments")?
        .iter()
        .map(|argument| emit::render_consumer_expression(argument, aliases))
        .collect()
}

fn render_fixture_bytes(data: &Value) -> Result<String, String> {
    match data.get("kind").and_then(Value::as_str) {
        Some("text") => Ok(format!(
            "utf8.encode({})",
            dart_string(
                data.get("value")
                    .and_then(Value::as_str)
                    .ok_or("Dart text fixture has no value")?
            )
        )),
        Some("bytes") => Ok(format!(
            "cott_runtime.CottRuntime.bytesFromHex({})",
            dart_string(
                data.get("value")
                    .and_then(Value::as_str)
                    .ok_or("Dart bytes fixture has no value")?
            )
        )),
        Some(other) => Err(format!("unsupported Dart fixture data `{other}`")),
        None => Err("Dart fixture data has no kind".to_owned()),
    }
}

fn fixture_data_len(data: &Value) -> Result<u64, String> {
    let value = data
        .get("value")
        .and_then(Value::as_str)
        .ok_or("Dart fixture data has no value")?;
    match data.get("kind").and_then(Value::as_str) {
        Some("text") => {
            u64::try_from(value.len()).map_err(|_| "Dart fixture byte length overflow".to_owned())
        }
        Some("bytes") if value.len() % 2 == 0 => u64::try_from(value.len() / 2)
            .map_err(|_| "Dart fixture byte length overflow".to_owned()),
        Some("bytes") => Err("Dart bytes fixture has odd hexadecimal length".to_owned()),
        _ => Err("Dart fixture data has unsupported kind".to_owned()),
    }
}

fn render_http_route(
    outcome: &Value,
    limits: &crate::contract_test::ScenarioLimits,
) -> Result<String, RenderFailure> {
    match outcome.get("kind").and_then(Value::as_str) {
        Some("response") => {
            let status = outcome
                .get("status")
                .and_then(Value::as_u64)
                .and_then(|value| u16::try_from(value).ok())
                .ok_or("Dart HTTP response fixture has invalid status")?;
            let body = outcome
                .get("body")
                .ok_or("Dart HTTP response fixture has no body")?;
            if body.get("kind").and_then(Value::as_str) == Some("text")
                && outcome.get("encoding").and_then(Value::as_str) != Some("utf-8")
            {
                return Err("Dart HTTP text fixture requires canonical utf-8 encoding".into());
            }
            if fixture_data_len(body)? > limits.http_body_bytes {
                return Err(RenderFailure::unavailable(
                    "Dart HTTP response fixture exceeds body limit",
                ));
            }
            Ok(format!(
                "_ScenarioRoute.response({status}, {})",
                render_fixture_bytes(body)?
            ))
        }
        Some("redirect") => {
            let status = outcome
                .get("status")
                .and_then(Value::as_u64)
                .and_then(|value| u16::try_from(value).ok())
                .ok_or("Dart HTTP redirect fixture has invalid status")?;
            let location = outcome
                .get("location")
                .and_then(Value::as_str)
                .ok_or("Dart HTTP redirect fixture has no location")?;
            validate_fixture_path(location, true)?;
            Ok(format!(
                "_ScenarioRoute.redirect({status}, {})",
                dart_string(location)
            ))
        }
        Some("delay") => {
            let milliseconds = outcome
                .get("milliseconds")
                .and_then(Value::as_u64)
                .ok_or("Dart HTTP delay fixture has invalid duration")?;
            if milliseconds > u64::from(limits.scenario_timeout_ms) {
                return Err(RenderFailure::unavailable(
                    "Dart HTTP delay exceeds scenario timeout",
                ));
            }
            Ok(format!(
                "_ScenarioRoute.delay(Duration(milliseconds: {milliseconds}))"
            ))
        }
        Some(other) => Err(format!("unsupported Dart HTTP fixture outcome `{other}`").into()),
        None => Err("Dart HTTP fixture outcome has no kind".into()),
    }
}

fn validate_fixture_path(path: &str, absolute: bool) -> Result<(), String> {
    let body = if absolute {
        path.strip_prefix('/').unwrap_or(path)
    } else {
        path
    };
    if path.is_empty()
        || path.contains('\\')
        || path.as_bytes().contains(&0)
        || (absolute != path.starts_with('/'))
        || (!body.is_empty()
            && body
                .split('/')
                .any(|part| part.is_empty() || part == "." || part == ".."))
    {
        return Err(format!("unsafe Dart scenario fixture path `{path}`"));
    }
    Ok(())
}

fn module_aliases(plan: &DartPlan) -> Result<BTreeMap<String, String>, String> {
    let mut aliases = BTreeMap::new();
    let mut used = BTreeSet::new();
    for module in &plan.modules {
        let alias = super::types::consumer_module_prefix(&module.name);
        if !used.insert(alias.clone()) {
            return Err(format!("Dart module alias collision for `{}`", module.name));
        }
        if aliases.insert(module.name.clone(), alias).is_some() {
            return Err(format!("duplicate Dart module `{}`", module.name));
        }
    }
    Ok(aliases)
}

fn declaration_index(plan: &DartPlan) -> Result<BTreeMap<&str, &Value>, String> {
    let mut declarations = BTreeMap::new();
    for module in &plan.modules {
        for declaration in &module.declarations {
            let name = declaration
                .get("name")
                .and_then(Value::as_str)
                .ok_or("canonical Dart declaration has no name")?;
            if declarations.insert(name, declaration).is_some() {
                return Err(format!("duplicate canonical Dart declaration `{name}`"));
            }
        }
    }
    Ok(declarations)
}

fn callable_is_public(callable: &DartCallable) -> Result<bool, String> {
    callable
        .owner
        .as_ref()
        .unwrap_or(&callable.declaration)
        .get("public")
        .and_then(Value::as_bool)
        .ok_or_else(|| format!("Dart callable `{}` has no public flag", callable.symbol))
}

fn crypto_support() -> BTreeMap<PathBuf, &'static [u8]> {
    BTreeMap::from([
        (
            PathBuf::from("crypto/AUTHORS"),
            include_bytes!("support/crypto/AUTHORS").as_slice(),
        ),
        (
            PathBuf::from("crypto/LICENSE"),
            include_bytes!("support/crypto/LICENSE").as_slice(),
        ),
        (
            PathBuf::from("crypto/digest.dart"),
            include_bytes!("support/crypto/digest.dart").as_slice(),
        ),
        (
            PathBuf::from("crypto/digest_sink.dart"),
            include_bytes!("support/crypto/digest_sink.dart").as_slice(),
        ),
        (
            PathBuf::from("crypto/hash.dart"),
            include_bytes!("support/crypto/hash.dart").as_slice(),
        ),
        (
            PathBuf::from("crypto/hash_sink.dart"),
            include_bytes!("support/crypto/hash_sink.dart").as_slice(),
        ),
        (
            PathBuf::from("crypto/hmac.dart"),
            include_bytes!("support/crypto/hmac.dart").as_slice(),
        ),
        (
            PathBuf::from("crypto/sha256.dart"),
            include_bytes!("support/crypto/sha256.dart").as_slice(),
        ),
        (
            PathBuf::from("crypto/utils.dart"),
            include_bytes!("support/crypto/utils.dart").as_slice(),
        ),
    ])
}

pub(crate) fn validate_support() -> Result<Value, String> {
    const EXPECTED: &[(&str, &str)] = &[
        (
            "crypto/AUTHORS",
            "85337aeeee55c79d4a1da86d1393354c14e4a5f0daf402de66ffe974c51694bf",
        ),
        (
            "crypto/LICENSE",
            "ad6a71997da90924b2cfb1fb47ec46537f70faf469efe016168794ae45ed6888",
        ),
        (
            "crypto/digest.dart",
            "0aa3fc33d3f17661ba26881463ae30e63bef2dc3a70089a3b9369b79c574349d",
        ),
        (
            "crypto/digest_sink.dart",
            "9912d304a55d1b9eb534ad49e9983eed9acf914e13444e1c51c7d3b71be40ca2",
        ),
        (
            "crypto/hash.dart",
            "6a896dc98a5de35ebf6a71deb41cd0af940e3468fec1912c24c17a5a65fdd45a",
        ),
        (
            "crypto/hash_sink.dart",
            "2b0642541390cd748d257d0a7f774f4854cd737639ca4e0d7a1ec910c9e603c3",
        ),
        (
            "crypto/hmac.dart",
            "5f7dd7c618144cc8c2dbdc7d2596922287214a7b25d17c9f89aaa0b41a43f6cd",
        ),
        (
            "crypto/sha256.dart",
            "64b2b537d597a8306c0ad77e69e8b2b2e3b97adef46c622fab681333813a3797",
        ),
        (
            "crypto/utils.dart",
            "6894378a65f58f75948e070797584c326571c806500fc6f83d390a3a1b127c71",
        ),
    ];
    let support = crypto_support();
    let mut sources = Vec::new();
    for (path, expected) in EXPECTED {
        let bytes = support
            .get(PathBuf::from(path).as_path())
            .ok_or_else(|| format!("missing pinned Dart crypto support `{path}`"))?;
        let actual = crate::hash::sha256_hex(bytes);
        if &actual != expected {
            return Err(format!("pinned Dart crypto support `{path}` changed"));
        }
        sources.push(serde_json::json!({
            "path": path,
            "content_hash": format!("sha256:{actual}"),
        }));
    }
    Ok(serde_json::json!({
        "archive": "https://pub.dev/api/archives/crypto-3.0.7.tar.gz",
        "archive_sha256": "sha256:c8ea0233063ba03258fbcf2ca4d6dadfefe14f02fab57702265467a19f27fadf",
        "package": "crypto",
        "version": "3.0.7",
        "sources": sources,
    }))
}

pub(crate) fn parse_events(stdout: &[u8], key: &[u8]) -> Result<Vec<Value>, String> {
    if key.len() != EVIDENCE_KEY_BYTES {
        return Err("Dart evidence authentication key has wrong length".to_owned());
    }
    let output = std::str::from_utf8(stdout)
        .map_err(|_| "bounded Dart runner stdout is not UTF-8".to_owned())?;
    let mut events = Vec::new();
    let mut sequence = 0u64;
    for line in output.lines() {
        let Some(record) = line.strip_prefix(EVENT_PREFIX) else {
            continue;
        };
        let (reported_sequence, rest) = record
            .split_once(':')
            .ok_or("malformed authenticated Dart evidence sequence")?;
        let (tag, payload) = rest
            .split_once(':')
            .ok_or("malformed authenticated Dart evidence tag")?;
        let reported_sequence = reported_sequence
            .parse::<u64>()
            .map_err(|_| "authenticated Dart evidence sequence is not u64")?;
        if reported_sequence != sequence {
            return Err(format!(
                "authenticated Dart evidence sequence mismatch: expected {sequence}, got {reported_sequence}"
            ));
        }
        if tag.len() != 64
            || !tag
                .bytes()
                .all(|byte| byte.is_ascii_digit() || (b'a'..=b'f').contains(&byte))
        {
            return Err("authenticated Dart evidence tag is not lowercase SHA-256 hex".to_owned());
        }
        let mut authenticated = Vec::with_capacity(8 + payload.len());
        authenticated.extend_from_slice(&sequence.to_be_bytes());
        authenticated.extend_from_slice(payload.as_bytes());
        let mut mac = Hmac::<Sha256>::new_from_slice(key)
            .map_err(|_| "initialize Dart evidence HMAC-SHA256".to_owned())?;
        mac.update(&authenticated);
        let provided = decode_hex(tag)?;
        mac.verify_slice(&provided)
            .map_err(|_| "Dart contract runner emitted unauthenticated evidence".to_owned())?;
        let event: Value = serde_json::from_str(payload)
            .map_err(|error| format!("invalid authenticated Dart evidence JSON: {error}"))?;
        if !event.is_object() {
            return Err("authenticated Dart evidence is not a JSON object".to_owned());
        }
        events.push(event);
        sequence = sequence
            .checked_add(1)
            .ok_or("authenticated Dart evidence sequence overflow")?;
    }
    if events.is_empty() {
        return Err("bounded Dart runner emitted no authenticated evidence".to_owned());
    }
    Ok(events)
}

fn decode_hex(value: &str) -> Result<Vec<u8>, String> {
    value
        .as_bytes()
        .chunks_exact(2)
        .map(|chunk| {
            let high = hex_nibble(chunk[0])?;
            let low = hex_nibble(chunk[1])?;
            Ok((high << 4) | low)
        })
        .collect()
}

fn hex_nibble(value: u8) -> Result<u8, String> {
    match value {
        b'0'..=b'9' => Ok(value - b'0'),
        b'a'..=b'f' => Ok(value - b'a' + 10),
        _ => Err("Dart evidence tag contains non-hex byte".to_owned()),
    }
}

fn safe_name(value: &str) -> String {
    let mut output = String::with_capacity(value.len());
    for byte in value.bytes() {
        if byte.is_ascii_alphanumeric() || byte == b'_' {
            output.push(byte as char);
        } else {
            write!(output, "_{byte:02x}").expect("writing to String cannot fail");
        }
    }
    output
}

fn dart_string(value: &str) -> String {
    let mut output = String::from("'");
    for character in value.chars() {
        match character {
            '\\' => output.push_str("\\\\"),
            '\'' => output.push_str("\\'"),
            '$' => output.push_str("\\$"),
            '\n' => output.push_str("\\n"),
            '\r' => output.push_str("\\r"),
            '\t' => output.push_str("\\t"),
            character if character.is_control() => {
                write!(output, "\\u{{{:x}}}", character as u32)
                    .expect("writing to String cannot fail");
            }
            character => output.push(character),
        }
    }
    output.push('\'');
    output
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn scalar_callable_renders_cases_and_malformed_schema_is_fatal() {
        let source =
            "module demo.main\n\nfn identity(value: I32) -> I32:\n    ensures result == value\n";
        let parsed = crate::compiler::parse_project([crate::compiler::SourceFile::new(
            "demo/main.cott",
            source,
        )])
        .expect("parse runner fixture");
        let hir =
            crate::hir::lower(std::path::Path::new("src"), parsed).expect("lower runner fixture");
        let ir = crate::ir::render(&hir).expect("render runner fixture IR");
        let mut plan = DartPlan::from_ir(&ir).expect("project runner fixture");
        let config = DartProjectConfig::parse(
            std::path::Path::new("cott.toml"),
            r#"[project]
name = "demo"
version = "0.1.0"
source = "src"

[target.dart]
source = "dart"
generated = "generated/dart"
runtime_validation = "boundary"
"#,
        )
        .expect("parse runner manifest");
        let strategies = crate::contract_test::derive_strategies(&plan.ir, &config.verification)
            .expect("derive runner strategies");
        let program = render(&config, &plan, &strategies, &config.verification)
            .expect("render scalar callable cases");
        assert!(
            program
                .expected_cases
                .get("demo.main.identity")
                .is_some_and(|count| *count > 0),
            "scalar callable must produce executable cases"
        );
        assert!(!program.unavailable.contains_key("demo.main.identity"));

        plan.callables[0].declaration["parameters"] = Value::Null;

        let error = render(&config, &plan, &strategies, &config.verification)
            .expect_err("malformed callable schema must abort runner rendering");
        assert!(
            error.contains("has no canonical parameters"),
            "unexpected render error: {error}"
        );
    }
}
