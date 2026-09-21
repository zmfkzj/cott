use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};
use std::thread;

use crate::agent::{AgentKind, AgentRunCandidate, adapter, run_agent};
use crate::hash::sha256_hex;
use crate::provenance::{AgentRun, AgentStatus, StreamDigest};

use super::binding::{candidate_binding, requires_binding, validate_candidate};
use super::pipeline::{self, Project};
use super::prompt::{PreparedPrompt, existing_agent_source, prepare as prepare_prompt};
use super::verify;
use super::{DartBinding, DartCallable, DartOwner};

const SOURCE_ATTEMPTS: usize = 3;
const VERIFICATION_RETRIES: usize = 2;
static NEXT_WORKSPACE: AtomicU64 = AtomicU64::new(0);

#[derive(Clone, Debug)]
struct WorkItem {
    callable: DartCallable,
    initial: PreparedPrompt,
    existing: Option<Vec<u8>>,
}

struct GeneratedCandidate {
    binding: DartBinding,
    run: AgentRun,
}

#[derive(Default)]
struct WaveOutcome {
    accepted: BTreeSet<String>,
    failed: bool,
}

pub(crate) fn generate(
    project: Option<PathBuf>,
    symbol: Option<String>,
    agent: Option<AgentKind>,
    jobs: usize,
) -> i32 {
    if jobs == 0 {
        eprintln!("error: Dart generation jobs must be at least 1");
        return 2;
    }
    let project = match pipeline::load(project, false) {
        Ok(project) => project,
        Err(error) => {
            eprintln!("error: {}", error.message);
            return error.code;
        }
    };
    let ordered_callables = project.plan.callables();
    let callables = ordered_callables
        .iter()
        .cloned()
        .map(|callable| (callable.symbol.clone(), callable))
        .collect::<BTreeMap<_, _>>();
    if let Some(requested) = symbol.as_deref() {
        let Some(callable) = callables.get(requested) else {
            eprintln!("error: unknown callable `{requested}`");
            return 2;
        };
        if !requires_binding(callable) {
            eprintln!(
                "error: compiler-owned implementation method `{requested}` must not be sent to an agent"
            );
            return 2;
        }
    }

    let resolved = project
        .bindings
        .iter()
        .map(|binding| binding.cott_symbol.as_str())
        .collect::<BTreeSet<_>>();
    let unresolved = callables
        .values()
        .filter(|callable| requires_binding(callable))
        .filter(|callable| !resolved.contains(callable.symbol.as_str()))
        .map(|callable| callable.symbol.clone())
        .collect::<BTreeSet<_>>();
    let selected = unresolved
        .iter()
        .filter(|candidate| {
            symbol
                .as_ref()
                .is_none_or(|requested| requested == *candidate)
        })
        .cloned()
        .collect::<BTreeSet<_>>();
    if selected.is_empty() {
        return 0;
    }

    let mut repairable = selected.clone();
    if symbol.is_none() {
        repairable.extend(
            project
                .bindings
                .iter()
                .filter(|binding| binding.owner == DartOwner::Agent)
                .map(|binding| binding.cott_symbol.clone()),
        );
    }

    // Freeze every initial prompt in canonical source order before a provider can
    // publish a candidate. Whole-target retries may change only the existing
    // candidate and actual feedback; rules, package metadata, intent, and the
    // initial prompt hash remain those consumed by this Project snapshot.
    let mut work = Vec::new();
    for callable in ordered_callables
        .iter()
        .filter(|callable| repairable.contains(&callable.symbol))
    {
        let resolved_source = project
            .bindings
            .iter()
            .find(|binding| {
                binding.owner == DartOwner::Agent && binding.cott_symbol == callable.symbol
            })
            .map(|binding| binding.bytes.clone());
        let source = match resolved_source {
            Some(source) => Some(source),
            None => match existing_agent_source(&project, callable) {
                Ok(source) => source,
                Err(message) => {
                    eprintln!("error: {message}");
                    return 4;
                }
            },
        };
        let initial = match prepare_prompt(
            &project.config,
            &project.plan,
            &project.paths.source_dir,
            callable,
            project.generator_rules.as_deref(),
            &project.package_metadata,
            &project.bindings,
            source.as_deref(),
            None,
        ) {
            Ok(initial) => initial,
            Err(message) => {
                eprintln!(
                    "error: prepare Dart generation prompt for `{}`: {message}",
                    callable.symbol
                );
                return 4;
            }
        };
        work.push(WorkItem {
            callable: callable.clone(),
            initial,
            existing: source,
        });
    }

    let selected_work = work
        .iter()
        .filter(|item| selected.contains(&item.callable.symbol))
        .cloned()
        .collect::<Vec<_>>();
    if agent.is_none() {
        eprintln!("error: unresolved selected Dart callable requires `--agent codex|claude|omp`");
        return 2;
    }

    let mut candidates = BTreeMap::<String, DartBinding>::new();
    // Keep an authenticated, intent-stale checkpoint available until a new
    // source-audited candidate replaces it. It remains pending and retains its
    // prior AgentRun/intent evidence in publication; merely parsing these bytes
    // never refreshes their trust.
    for item in &work {
        if project
            .bindings
            .iter()
            .any(|binding| binding.cott_symbol == item.callable.symbol)
        {
            continue;
        }
        let Some(bytes) = item.existing.as_ref() else {
            continue;
        };
        let binding = match candidate_binding(&project.paths, &item.callable, bytes.clone()) {
            Ok(binding) => binding,
            Err(message) => {
                eprintln!(
                    "error: preserve pending Dart implementation for `{}`: {message}",
                    item.callable.symbol
                );
                return 4;
            }
        };
        candidates.insert(item.callable.symbol.clone(), binding);
    }
    let mut runs = BTreeMap::<String, AgentRun>::new();
    let mut pending = unresolved.clone();
    let mut generation_failed = false;
    let kind = agent.expect("selected unresolved Dart work requires an agent");
    let executable = match resolve_executable(adapter(kind).executable_name) {
        Ok(executable) => Some(executable),
        Err(message) => {
            eprintln!("error: {message}");
            generation_failed = true;
            None
        }
    };
    if let Some(executable) = executable.as_deref() {
        let outcome = run_generation_waves(
            &selected_work,
            jobs,
            kind,
            executable,
            &project,
            None,
            &mut candidates,
            &mut runs,
        );
        for symbol in outcome.accepted {
            pending.remove(&symbol);
        }
        generation_failed = outcome.failed;
    }

    let mut verification_failed = false;
    if !generation_failed && pending.is_empty() {
        let mut attempts = 0usize;
        loop {
            let bindings = combined_bindings(&project, &candidates);
            match validate_complete(&project, &bindings) {
                Ok(()) => {
                    pending.clear();
                    break;
                }
                Err(message) => {
                    let implicated = implicated_agent_symbols(&message, &bindings);
                    pending = implicated.clone();
                    let mut repair = work
                        .iter()
                        .filter(|item| implicated.contains(&item.callable.symbol))
                        .cloned()
                        .collect::<Vec<_>>();
                    for item in &mut repair {
                        item.existing =
                            effective_binding(&project, &candidates, &item.callable.symbol)
                                .map(|binding| binding.bytes.clone());
                    }
                    if attempts == VERIFICATION_RETRIES || repair.is_empty() {
                        eprintln!("error: generated Dart candidate validation failed: {message}");
                        verification_failed = true;
                        break;
                    }
                    attempts += 1;
                    eprintln!(
                        "Dart complete-candidate validation retry {attempts}/{VERIFICATION_RETRIES}: {message}"
                    );
                    let feedback = format!(
                        "Complete Dart source audit, analyzer, kernel compilation, or authenticated runtime validation failed. Repair only the selected implementation without weakening the canonical contract. Exact diagnostic:\n{message}"
                    );
                    let outcome = run_generation_waves(
                        &repair,
                        jobs,
                        kind,
                        executable
                            .as_deref()
                            .expect("initial Dart agent executable was resolved"),
                        &project,
                        Some(&feedback),
                        &mut candidates,
                        &mut runs,
                    );
                    for symbol in outcome.accepted {
                        pending.remove(&symbol);
                    }
                    if outcome.failed {
                        generation_failed = true;
                        break;
                    }
                }
            }
        }
    }

    let bindings = combined_bindings(&project, &candidates);
    let agent_runs = runs.into_values().collect::<Vec<_>>();
    match pipeline::publish(&project, &bindings, &agent_runs, &pending, None, false) {
        Ok(()) if generation_failed || verification_failed => 5,
        Ok(()) => 0,
        Err(error) => {
            eprintln!("error: {}", error.message);
            error.code
        }
    }
}

#[allow(clippy::too_many_arguments)]
fn run_generation_waves(
    items: &[WorkItem],
    jobs: usize,
    kind: AgentKind,
    executable: &Path,
    project: &Project,
    feedback: Option<&str>,
    candidates: &mut BTreeMap<String, DartBinding>,
    runs: &mut BTreeMap<String, AgentRun>,
) -> WaveOutcome {
    let mut outcome = WaveOutcome::default();
    for wave in items.chunks(jobs) {
        let generated = scoped_wave(
            wave,
            |item| generate_candidate(item, kind, executable, project, feedback),
            |item| format!("agent worker for `{}` panicked", item.callable.symbol),
        );
        let mut failed = false;
        for result in generated {
            match result {
                Ok(generated) => {
                    let symbol = generated.binding.cott_symbol.clone();
                    candidates.insert(symbol.clone(), generated.binding);
                    runs.insert(symbol.clone(), generated.run);
                    outcome.accepted.insert(symbol);
                }
                Err(message) => {
                    eprintln!("error: {message}");
                    failed = true;
                }
            }
        }
        if failed {
            outcome.failed = true;
            return outcome;
        }
    }
    outcome
}

fn generate_candidate(
    item: &WorkItem,
    kind: AgentKind,
    executable: &Path,
    project: &Project,
    initial_feedback: Option<&str>,
) -> Result<GeneratedCandidate, String> {
    let mut existing = item.existing.clone();
    let mut feedback = initial_feedback.unwrap_or_default().to_owned();
    for attempt in 0..SOURCE_ATTEMPTS {
        let prompt = if attempt == 0 && initial_feedback.is_none() {
            item.initial.bytes.clone()
        } else {
            prepare_prompt(
                &project.config,
                &project.plan,
                &project.paths.source_dir,
                &item.callable,
                project.generator_rules.as_deref(),
                &project.package_metadata,
                &project.bindings,
                existing.as_deref(),
                (!feedback.is_empty()).then_some(feedback.as_str()),
            )?
            .bytes
        };
        let workspace = AgentWorkspace::create()?;
        let target = workspace.workspace.join("implementation.dart");
        let mut candidate = run_agent(
            kind,
            executable.to_path_buf(),
            &workspace.workspace,
            &workspace.scratch,
            &target,
            prompt,
            project.config.generator.timeout_seconds,
        )
        .map_err(|message| {
            format!(
                "agent generation for `{}` failed: {message}",
                item.callable.symbol
            )
        })?;
        match validate_candidate(
            &project.config,
            &project.plan,
            &item.callable,
            super::dependencies::runtime_package_names(&project.package_metadata),
            &candidate.implementation,
        ) {
            Ok(()) => {
                candidate.prompt_hash = item.initial.prompt_hash.clone();
                let binding = candidate_binding(
                    &project.paths,
                    &item.callable,
                    candidate.implementation.clone(),
                )?;
                let run = agent_run(&item.callable.symbol, kind, candidate);
                return Ok(GeneratedCandidate { binding, run });
            }
            Err(message) if attempt + 1 == SOURCE_ATTEMPTS => {
                return Err(format!(
                    "agent generation for `{}` failed Dart source audit after {SOURCE_ATTEMPTS} attempts: {message}",
                    item.callable.symbol
                ));
            }
            Err(message) => {
                if !feedback.is_empty() {
                    feedback.push('\n');
                }
                feedback.push_str("Dart source audit failed:\n");
                feedback.push_str(&message);
                existing = Some(candidate.implementation);
            }
        }
    }
    unreachable!("Dart source attempt loop always returns")
}

fn combined_bindings(
    project: &Project,
    candidates: &BTreeMap<String, DartBinding>,
) -> Vec<DartBinding> {
    let mut bindings = project
        .bindings
        .iter()
        .cloned()
        .map(|binding| (binding.cott_symbol.clone(), binding))
        .collect::<BTreeMap<_, _>>();
    bindings.extend(candidates.clone());
    bindings.into_values().collect()
}

fn effective_binding<'a>(
    project: &'a Project,
    candidates: &'a BTreeMap<String, DartBinding>,
    symbol: &str,
) -> Option<&'a DartBinding> {
    candidates.get(symbol).or_else(|| {
        project
            .bindings
            .iter()
            .find(|binding| binding.cott_symbol == symbol)
    })
}

fn implicated_agent_symbols(message: &str, bindings: &[DartBinding]) -> BTreeSet<String> {
    let matches_identity = |binding: &DartBinding| {
        let private_name = binding
            .target_symbol
            .split_once(':')
            .map(|(_, name)| name)
            .unwrap_or(binding.target_symbol.as_str());
        message.contains(&binding.cott_symbol)
            || message.contains(&binding.target_symbol)
            || message.contains(private_name)
            || message.contains(binding.source_origin.to_string_lossy().as_ref())
            || message.contains(binding.runtime_origin.to_string_lossy().as_ref())
    };
    let matched = bindings
        .iter()
        .filter(|binding| matches_identity(binding))
        .collect::<Vec<_>>();
    if !matched.is_empty() {
        return matched
            .into_iter()
            .filter(|binding| binding.owner == DartOwner::Agent)
            .map(|binding| binding.cott_symbol.clone())
            .collect();
    }

    let local = bindings
        .iter()
        .filter(|binding| {
            binding
                .cott_symbol
                .rsplit('.')
                .next()
                .is_some_and(|name| mentions_identifier(message, name))
        })
        .collect::<Vec<_>>();
    if local.len() == 1 {
        return local
            .into_iter()
            .filter(|binding| binding.owner == DartOwner::Agent)
            .map(|binding| binding.cott_symbol.clone())
            .collect();
    }

    bindings
        .iter()
        .filter(|binding| binding.owner == DartOwner::Agent)
        .map(|binding| binding.cott_symbol.clone())
        .collect()
}

fn mentions_identifier(message: &str, identifier: &str) -> bool {
    message.match_indices(identifier).any(|(start, _)| {
        let before = message[..start].chars().next_back();
        let after = message[start + identifier.len()..].chars().next();
        matches!(before, Some('`' | '\'' | '"'))
            || matches!(after, Some('`' | '\'' | '"' | '(' | ':' | '.'))
    })
}

fn validate_complete(project: &Project, bindings: &[DartBinding]) -> Result<(), String> {
    let emission = pipeline::project_emission(project, bindings)
        .map_err(|error| format!("emit complete Dart candidate: {}", error.message))?;
    if !emission.unresolved.is_empty() {
        return Err(format!(
            "complete Dart candidate unexpectedly has unresolved callables: {}",
            emission.unresolved.join(", ")
        ));
    }
    verify::verify(
        &project.config,
        &project.paths,
        &project.plan,
        &emission,
        &project.package_metadata,
    )
    .map(|_| ())
}

fn agent_run(symbol: &str, kind: AgentKind, candidate: AgentRunCandidate) -> AgentRun {
    let stream = |bytes: &[u8]| StreamDigest {
        bytes: bytes.len() as u64,
        sha256: format!("sha256:{}", sha256_hex(bytes)),
        truncated: false,
    };
    let spec = adapter(kind);
    AgentRun {
        symbol: symbol.to_owned(),
        adapter: match kind {
            AgentKind::Codex => "codex",
            AgentKind::Omp => "omp",
            AgentKind::Claude => "claude",
        }
        .to_owned(),
        adapter_version: candidate.adapter_version,
        argv_template: spec.argv_template.iter().map(ToString::to_string).collect(),
        executable: candidate.executable.display().to_string(),
        executable_hash: candidate.executable_hash,
        prompt_hash: candidate.prompt_hash,
        implementation_hash: format!("sha256:{}", sha256_hex(&candidate.implementation)),
        environment_names: candidate.environment_names,
        duration_ms: candidate.duration_ms,
        status: AgentStatus {
            exit_code: candidate.exit_code,
            signal: None,
            timed_out: candidate.timed_out,
            cancelled: false,
        },
        stdout: stream(&candidate.stdout),
        stderr: stream(&candidate.stderr),
    }
}

fn scoped_wave<T, R, E>(
    items: &[T],
    work: impl Fn(&T) -> Result<R, E> + Sync,
    panic_error: impl Fn(&T) -> E + Sync,
) -> Vec<Result<R, E>>
where
    T: Sync,
    R: Send,
    E: Send,
{
    thread::scope(|scope| {
        let mut workers = Vec::with_capacity(items.len());
        for item in items {
            workers.push((item, scope.spawn(|| work(item))));
        }
        workers
            .into_iter()
            .map(|(item, worker)| worker.join().unwrap_or_else(|_| Err(panic_error(item))))
            .collect()
    })
}

fn resolve_executable(name: &str) -> Result<PathBuf, String> {
    let path =
        std::env::var_os("PATH").ok_or_else(|| format!("missing PATH while locating {name}"))?;
    for directory in std::env::split_paths(&path) {
        let candidate = directory.join(name);
        if fs::metadata(&candidate).is_ok_and(|metadata| metadata.is_file()) {
            return fs::canonicalize(&candidate)
                .map_err(|error| format!("canonicalize {}: {error}", candidate.display()));
        }
    }
    Err(format!("{name} executable was not found on PATH"))
}

struct AgentWorkspace {
    root: PathBuf,
    workspace: PathBuf,
    scratch: PathBuf,
}

impl AgentWorkspace {
    fn create() -> Result<Self, String> {
        loop {
            let id = NEXT_WORKSPACE.fetch_add(1, Ordering::Relaxed);
            let root =
                std::env::temp_dir().join(format!("cott-dart-agent-{}-{id}", std::process::id()));
            match fs::create_dir(&root) {
                Ok(()) => {
                    let workspace = root.join("workspace");
                    let scratch = root.join("scratch");
                    if let Err(error) =
                        fs::create_dir(&workspace).and_then(|_| fs::create_dir(&scratch))
                    {
                        let _ = fs::remove_dir_all(&root);
                        return Err(format!("create Dart agent workspace: {error}"));
                    }
                    return Ok(Self {
                        root,
                        workspace,
                        scratch,
                    });
                }
                Err(error) if error.kind() == std::io::ErrorKind::AlreadyExists => continue,
                Err(error) => return Err(format!("create Dart agent workspace: {error}")),
            }
        }
    }
}

impl Drop for AgentWorkspace {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.root);
    }
}
