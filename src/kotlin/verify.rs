use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::io;
use std::os::unix::fs::{DirBuilderExt, MetadataExt};
use std::path::{Component, Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use serde_json::{Value, json};

use crate::contract_test::{ContractTestStrategy, derive_strategies};
use crate::hash::sha256_hex;
use crate::manifest::KotlinProjectConfig;
use crate::project::KotlinPaths;
use crate::proof::prove_contracts;
use crate::provenance::{SemanticCoverage, validate_semantic_coverage};
use crate::sandbox::{BindMounts, NetworkAccess, ResourceLimits, SandboxSpec, run};

use super::runner::{self, RunnerProgram};
use super::{KotlinEmission, KotlinPlan};

const MINIMUM_KOTLIN: (u64, u64, u64) = (2, 2, 10);
const MINIMUM_JAVA_MAJOR: u64 = 17;
const REQUIRED_COROUTINES: &str = "1.8.0";
const MODULE_JAR: &str = "library/cott-module.jar";
const COROUTINES_OUTPUT: &str = "runtime-libs/kotlinx-coroutines-core-jvm.jar";
const MAX_DIAGNOSTICS: usize = 20;
const MAX_IDENTITY_LIBRARIES: usize = 256;
// HotSpot creates VM, service, and compiler threads in addition to the launched tool.
// Keep bounded headroom for those threads and user-task changes after sandbox accounting.
const KOTLIN_JVM_TASK_ALLOWANCE: u64 = 32;

static NEXT_SCRATCH: AtomicU64 = AtomicU64::new(0);

#[derive(Clone, Debug)]
pub(crate) struct Verification {
    pub artifacts: BTreeMap<PathBuf, Vec<u8>>,
    pub tools: Value,
    pub report: Value,
    pub coverage: SemanticCoverage,
}

#[derive(Clone, Debug)]
struct Toolchain {
    compiler: PathBuf,
    kotlin_home: PathBuf,
    java: PathBuf,
    java_home: PathBuf,
    jar: PathBuf,
    stdlib: PathBuf,
    coroutines: PathBuf,
}

#[derive(Clone, Debug)]
struct ToolInspection {
    tools: Value,
    identities: BTreeMap<PathBuf, String>,
    classpath: Vec<PathBuf>,
    compile_only: Vec<PathBuf>,
}

pub(crate) fn probe(config: &KotlinProjectConfig, paths: &KotlinPaths) -> Result<Value, String> {
    let scratch = scratch_directory()?;
    let result = (|| {
        let toolchain = Toolchain::discover(config, paths)?;
        let inspection = toolchain.inspect(paths, &scratch)?;
        verify_identities(&inspection.identities)?;
        Ok(inspection.tools)
    })();
    finish_scratch(scratch, result)
}

pub(crate) fn verify(
    config: &KotlinProjectConfig,
    paths: &KotlinPaths,
    plan: &KotlinPlan,
    emission: &KotlinEmission,
) -> Result<Verification, String> {
    if !emission.unresolved.is_empty() {
        let mut unresolved = emission.unresolved.clone();
        unresolved.sort();
        unresolved.dedup();
        return Err(format!(
            "Kotlin verification requires a fully resolved target; unresolved: {}",
            unresolved.join(", ")
        ));
    }
    let strategies = derive_strategies(&plan.ir, &config.verification)
        .map_err(|error| format!("derive Kotlin contract strategies: {error}"))?;
    let contract_proofs = prove_contracts(&plan.ir, None, &config.verification)
        .map_err(|error| format!("prove Kotlin contracts: {error}"))?;
    let program = runner::render(plan, &strategies, &config.verification)
        .map_err(|error| format!("render bounded Kotlin contract runner: {error}"))?;
    let scratch = scratch_directory()?;
    let result = verify_in_scratch(
        config,
        paths,
        plan,
        emission,
        &strategies,
        contract_proofs,
        &program,
        &scratch,
    );
    finish_scratch(scratch, result)
}

fn verify_in_scratch(
    config: &KotlinProjectConfig,
    paths: &KotlinPaths,
    plan: &KotlinPlan,
    emission: &KotlinEmission,
    strategies: &[ContractTestStrategy],
    contract_proofs: Value,
    program: &RunnerProgram,
    scratch: &Path,
) -> Result<Verification, String> {
    let toolchain = Toolchain::discover(config, paths)?;
    let inspection = toolchain.inspect(paths, scratch)?;
    let mut dependency_shadow_inputs = vec![
        ("kotlin-stdlib.jar".to_owned(), toolchain.stdlib.clone()),
        (
            "kotlinx-coroutines-core-jvm.jar".to_owned(),
            toolchain.coroutines.clone(),
        ),
    ];
    dependency_shadow_inputs.extend(
        inspection
            .classpath
            .iter()
            .enumerate()
            .map(|(index, path)| (format!("classpath[{index}]"), path.clone())),
    );
    dependency_shadow_inputs.extend(
        inspection
            .compile_only
            .iter()
            .enumerate()
            .map(|(index, path)| (format!("compile_only[{index}]"), path.clone())),
    );
    reject_class_shadowing(&toolchain, scratch, &dependency_shadow_inputs)?;
    let source_root = scratch.join("sources");
    let library_root = scratch.join("library");
    let runner_root = scratch.join("runner");
    fs::create_dir(&source_root)
        .map_err(|error| format!("create Kotlin source scratch: {error}"))?;
    fs::create_dir(&library_root)
        .map_err(|error| format!("create Kotlin library scratch: {error}"))?;
    fs::create_dir(&runner_root)
        .map_err(|error| format!("create Kotlin runner scratch: {error}"))?;

    let sources = materialize_sources(emission, &source_root)?;
    audit_canonical_ir(plan, emission)?;
    let library = library_root.join("cott-module.jar");
    let module_name = module_name(config);
    let mut compiler_classpath = vec![toolchain.stdlib.clone(), toolchain.coroutines.clone()];
    compiler_classpath.extend(inspection.classpath.iter().cloned());
    compiler_classpath.extend(inspection.compile_only.iter().cloned());
    let mut compile_arguments = sources
        .iter()
        .map(|path| path_argument(path, "Kotlin source"))
        .collect::<Result<Vec<_>, _>>()?;
    compile_arguments.extend([
        "-no-stdlib".to_owned(),
        "-no-reflect".to_owned(),
        "-classpath".to_owned(),
        joined_paths(&compiler_classpath, "Kotlin compiler classpath")?,
        "-jvm-target".to_owned(),
        "17".to_owned(),
        "-Xjdk-release=17".to_owned(),
        "-module-name".to_owned(),
        module_name.clone(),
        "-d".to_owned(),
        path_argument(&library, "Kotlin library output")?,
    ]);
    let compiled = sandbox_process(
        &toolchain.compiler,
        compile_arguments,
        scratch,
        &toolchain,
        compiler_binds(scratch, &toolchain, &compiler_classpath),
        NetworkAccess::Disabled,
        compiler_limits(),
        true,
    )?;
    require_compile_success("Kotlin library compilation", &compiled, scratch)?;
    let library_bytes =
        fs::read(&library).map_err(|error| format!("read compiled Kotlin library: {error}"))?;
    let mut library_shadow_inputs = vec![("cott-module.jar".to_owned(), library.clone())];
    library_shadow_inputs.extend(dependency_shadow_inputs);
    reject_class_shadowing(&toolchain, scratch, &library_shadow_inputs)?;
    if library_bytes.is_empty() {
        return Err("Kotlin compiler produced an empty library JAR".to_owned());
    }

    let runner_source = runner_root.join(program.file_name);
    fs::write(&runner_source, program.source.as_bytes())
        .map_err(|error| format!("write bounded Kotlin runner: {error}"))?;
    let runner_jar = runner_root.join("cott-contract-runner.jar");
    let mut runner_compile_classpath = vec![
        library.clone(),
        toolchain.stdlib.clone(),
        toolchain.coroutines.clone(),
    ];
    runner_compile_classpath.extend(inspection.classpath.iter().cloned());
    runner_compile_classpath.extend(inspection.compile_only.iter().cloned());
    let runner_arguments = vec![
        path_argument(&runner_source, "Kotlin runner source")?,
        "-no-stdlib".to_owned(),
        "-no-reflect".to_owned(),
        "-classpath".to_owned(),
        joined_paths(
            &runner_compile_classpath,
            "Kotlin runner compiler classpath",
        )?,
        "-jvm-target".to_owned(),
        "17".to_owned(),
        "-Xjdk-release=17".to_owned(),
        "-module-name".to_owned(),
        format!("{module_name}_contract_runner"),
        "-d".to_owned(),
        path_argument(&runner_jar, "Kotlin runner output")?,
    ];
    let runner_compiled = sandbox_process(
        &toolchain.compiler,
        runner_arguments,
        scratch,
        &toolchain,
        compiler_binds(scratch, &toolchain, &runner_compile_classpath),
        NetworkAccess::Disabled,
        compiler_limits(),
        true,
    )?;
    require_compile_success(
        "Kotlin contract runner compilation",
        &runner_compiled,
        scratch,
    )?;

    let mut runtime_classpath = vec![
        runner_jar.clone(),
        library.clone(),
        toolchain.stdlib.clone(),
        toolchain.coroutines.clone(),
    ];
    runtime_classpath.extend(inspection.classpath.iter().cloned());
    let runtime_arguments = java_arguments(
        scratch,
        vec![
            "-ea".to_owned(),
            "-cp".to_owned(),
            joined_paths(&runtime_classpath, "Kotlin runtime classpath")?,
            runner::MAIN_CLASS.to_owned(),
        ],
    );
    let mut runtime_shadow_inputs = vec![
        ("cott-contract-runner.jar".to_owned(), runner_jar.clone()),
        ("cott-module.jar".to_owned(), library.clone()),
        ("kotlin-stdlib.jar".to_owned(), toolchain.stdlib.clone()),
        (
            "kotlinx-coroutines-core-jvm.jar".to_owned(),
            toolchain.coroutines.clone(),
        ),
    ];
    runtime_shadow_inputs.extend(
        inspection
            .classpath
            .iter()
            .enumerate()
            .map(|(index, path)| (format!("classpath[{index}]"), path.clone())),
    );
    reject_class_shadowing(&toolchain, scratch, &runtime_shadow_inputs)?;
    let mut evidence_key = [0u8; runner::EVIDENCE_KEY_BYTES];
    getrandom::fill(&mut evidence_key)
        .map_err(|error| format!("generate Kotlin evidence authentication key: {error}"))?;
    let runtime = sandbox_process_with_stdin(
        &toolchain.java,
        runtime_arguments,
        scratch,
        &toolchain,
        compiler_binds(scratch, &toolchain, &runtime_classpath),
        if program.needs_loopback {
            NetworkAccess::IsolatedLoopback
        } else {
            NetworkAccess::Disabled
        },
        runtime_limits(config),
        false,
        evidence_key.to_vec(),
    );
    let runtime = match runtime {
        Ok(runtime) => runtime,
        Err(error) => {
            evidence_key.fill(0);
            return Err(error);
        }
    };
    if runtime.status != Some(0) {
        evidence_key.fill(0);
        return Err(format!(
            "bounded Kotlin contract runner failed with status {:?}",
            runtime.status
        ));
    }
    let events = runner::parse_events(&runtime.stdout, &evidence_key);
    evidence_key.fill(0);
    let events = events?;
    validate_events(program, &events)?;

    verify_identities(&inspection.identities)?;

    let contract_tests = contract_report(plan, strategies, program, &events)?;
    let report = json!({
        "compilation": {
            "artifact": MODULE_JAR,
            "artifact_hash": format!("sha256:{}", sha256_hex(&library_bytes)),
            "jvm_target": 17,
            "module_name": module_name,
            "source_files": sources.len(),
            "runner_source_hash": format!("sha256:{}", sha256_hex(program.source.as_bytes())),
            "status": "passed",
        },
        "contract_proofs": contract_proofs,
        "contract_tests": contract_tests,
        "limits": {
            "candidate_limit": config.verification.candidate_limit,
            "lifecycle_limit": config.verification.lifecycle_limit,
            "proof_branch_limit": config.verification.proof_branch_limit,
            "proof_node_limit": config.verification.proof_node_limit,
            "scenario_timeout_ms": config.verification.fixtures.scenario_timeout_ms,
        },
        "runtime_capability": {
            "compilation_only": false,
            "grade": "runtime check",
            "sandbox": "bubblewrap",
            "status": "passed",
        },
    });
    let coverage = crate::cli::semantic_coverage(&report, &config.verification.coverage)?;
    validate_semantic_coverage(&coverage)
        .map_err(|error| format!("invalid Kotlin semantic coverage: {error}"))?;
    let coroutine_bytes = fs::read(&toolchain.coroutines)
        .map_err(|error| format!("read Kotlin coroutine runtime: {error}"))?;
    let expected_coroutine_hash = inspection
        .identities
        .get(&toolchain.coroutines)
        .ok_or("verified Kotlin tools omit the coroutine JAR identity")?;
    let actual_coroutine_hash = format!("sha256:{}", sha256_hex(&coroutine_bytes));
    if &actual_coroutine_hash != expected_coroutine_hash {
        return Err("Kotlin coroutine runtime changed while collecting artifacts".to_owned());
    }
    let artifacts = BTreeMap::from([
        (PathBuf::from(MODULE_JAR), library_bytes),
        (PathBuf::from(COROUTINES_OUTPUT), coroutine_bytes),
    ]);
    Ok(Verification {
        artifacts,
        tools: inspection.tools,
        report,
        coverage,
    })
}

impl Toolchain {
    fn discover(config: &KotlinProjectConfig, paths: &KotlinPaths) -> Result<Self, String> {
        let compiler = resolve_executable(&paths.root, &config.kotlin.compiler, "Kotlin compiler")?;
        let kotlin_home = compiler
            .parent()
            .and_then(Path::parent)
            .ok_or("Kotlin compiler executable has no distribution root")?
            .to_path_buf();
        let stdlib = regular_file(
            &kotlin_home.join("lib/kotlin-stdlib.jar"),
            "Kotlin standard library",
        )?;
        let coroutines = regular_file(
            &kotlin_home.join("lib/kotlinx-coroutines-core-jvm.jar"),
            "Kotlin coroutine runtime",
        )?;
        let java = resolve_executable(&paths.root, &config.kotlin.java, "Java launcher")?;
        let java_home = java
            .parent()
            .and_then(Path::parent)
            .ok_or("Java launcher has no JDK root")?
            .to_path_buf();
        let jar = regular_file(&java_home.join("bin/jar"), "JDK jar tool")?;
        Ok(Self {
            compiler,
            kotlin_home,
            java,
            java_home,
            jar,
            stdlib,
            coroutines,
        })
    }

    fn inspect(&self, paths: &KotlinPaths, scratch: &Path) -> Result<ToolInspection, String> {
        let mut starting_identities = BTreeMap::new();
        for path in [
            &self.compiler,
            &self.java,
            &self.jar,
            &self.stdlib,
            &self.coroutines,
        ] {
            starting_identities.insert(path.clone(), hash_file(path)?);
        }
        let compiler_libraries =
            compiler_library_records(&self.kotlin_home, &mut starting_identities)?;
        let compiler_probe = sandbox_process(
            &self.compiler,
            vec!["-version".to_owned()],
            scratch,
            self,
            compiler_binds(scratch, self, &[]),
            NetworkAccess::Disabled,
            probe_limits(),
            true,
        )?;
        require_compile_success("Kotlin compiler version probe", &compiler_probe, scratch)?;
        let compiler_output = combined_output(&compiler_probe);
        let kotlin_version = token_after(&compiler_output, "kotlinc-jvm ")
            .ok_or("Kotlin compiler version probe did not report kotlinc-jvm")?
            .to_owned();
        if !version_at_least(&kotlin_version, MINIMUM_KOTLIN) {
            return Err(format!(
                "Kotlin target requires kotlinc-jvm >=2.2.10, got `{kotlin_version}`"
            ));
        }

        let java_probe = sandbox_process(
            &self.java,
            java_arguments(scratch, vec!["-version".to_owned()]),
            scratch,
            self,
            compiler_binds(scratch, self, &[]),
            NetworkAccess::Disabled,
            probe_limits(),
            false,
        )?;
        require_compile_success("Java version probe", &java_probe, scratch)?;
        let java_output = combined_output(&java_probe);
        let java_version = quoted_version(&java_output)
            .ok_or("Java version probe did not report a quoted version")?
            .to_owned();
        let java_major = java_version
            .split('.')
            .next()
            .and_then(|value| value.parse::<u64>().ok())
            .ok_or("Java version probe reported a non-numeric major version")?;
        if java_major < MINIMUM_JAVA_MAJOR {
            return Err(format!(
                "Kotlin target requires JDK >=17, got `{java_version}`"
            ));
        }

        let dependency_source = scratch.join("DependencyProbe.java");
        fs::write(
            &dependency_source,
            br#"import java.io.InputStream;
import java.nio.charset.StandardCharsets;
public final class DependencyProbe {
  public static void main(String[] args) throws Exception {
    System.out.println("stdlib=" + kotlin.KotlinVersion.CURRENT.toString());
    try (InputStream stream = DependencyProbe.class.getClassLoader().getResourceAsStream("META-INF/kotlinx_coroutines_core.version")) {
      if (stream == null) throw new IllegalStateException("missing coroutine version resource");
      System.out.println("coroutines=" + new String(stream.readAllBytes(), StandardCharsets.UTF_8).trim());
    }
  }
}
"#,
        )
        .map_err(|error| format!("write Kotlin dependency identity probe: {error}"))?;
        let dependency_classpath = vec![self.stdlib.clone(), self.coroutines.clone()];
        let dependency_probe = sandbox_process(
            &self.java,
            java_arguments(
                scratch,
                vec![
                    "--class-path".to_owned(),
                    joined_paths(&dependency_classpath, "Kotlin dependency probe classpath")?,
                    path_argument(&dependency_source, "Kotlin dependency probe")?,
                ],
            ),
            scratch,
            self,
            compiler_binds(scratch, self, &dependency_classpath),
            NetworkAccess::Disabled,
            compiler_limits(),
            false,
        )?;
        if dependency_probe.status != Some(0) {
            return Err(format!(
                "Kotlin dependency identity probe failed with status {:?}",
                dependency_probe.status
            ));
        }
        let dependency_output = std::str::from_utf8(&dependency_probe.stdout)
            .map_err(|_| "Kotlin dependency identity probe output is not UTF-8")?;
        let stdlib_version = dependency_output
            .lines()
            .find_map(|line| line.strip_prefix("stdlib="))
            .ok_or("Kotlin dependency probe omitted the standard library version")?
            .to_owned();
        let coroutines_version = dependency_output
            .lines()
            .find_map(|line| line.strip_prefix("coroutines="))
            .ok_or("Kotlin dependency probe omitted the coroutine version")?
            .to_owned();
        if stdlib_version != kotlin_version {
            return Err(format!(
                "Kotlin compiler {kotlin_version} is paired with incompatible standard library {stdlib_version}"
            ));
        }
        if coroutines_version != REQUIRED_COROUTINES {
            return Err(format!(
                "Kotlin target requires compiler-bundled kotlinx-coroutines-core-jvm {REQUIRED_COROUTINES}, got `{coroutines_version}`"
            ));
        }
        verify_identities(&starting_identities)?;

        let classpath = canonical_inputs(&paths.classpath, "target.kotlin.classpath")?;
        let compile_only = canonical_inputs(&paths.compile_only, "target.kotlin.compile_only")?;
        let classpath_set = classpath.iter().cloned().collect::<BTreeSet<_>>();
        if let Some(overlap) = compile_only
            .iter()
            .find(|path| classpath_set.contains(*path))
        {
            return Err(format!(
                "Kotlin dependency appears in both classpath and compile_only: {}",
                overlap.display()
            ));
        }
        let mut identities = starting_identities;
        for path in classpath.iter().chain(compile_only.iter()) {
            identities.insert(path.clone(), hash_file(path)?);
        }
        let classpath_records = dependency_records(&classpath, "runtime", &mut identities)?;
        let compile_only_records =
            dependency_records(&compile_only, "compile_only", &mut identities)?;
        let tools = json!({
            "compile_inputs": {
                "classpath": classpath_records,
                "compile_only": compile_only_records,
            },
            "java": {
                "content_hash": identities[&self.java].clone(),
                "executable": self.java,
                "home": self.java_home,
                "major": java_major,
                "version": java_version,
            },
            "jar": {
                "content_hash": identities[&self.jar].clone(),
                "executable": self.jar,
                "version": java_version,
            },
            "kotlin": {
                "compiler_libraries": compiler_libraries,
                "content_hash": identities[&self.compiler].clone(),
                "distribution": self.kotlin_home,
                "executable": self.compiler,
                "jvm_target": 17,
                "version": kotlin_version,
            },
            "runtime_dependencies": {
                "kotlin_stdlib": {
                    "bundled": false,
                    "content_hash": identities[&self.stdlib].clone(),
                    "path": self.stdlib,
                    "provided_by": "Kotlin compiler or Android Gradle plugin",
                    "required": true,
                    "version": stdlib_version,
                },
                "kotlinx_coroutines_core_jvm": {
                    "artifact": COROUTINES_OUTPUT,
                    "bundled": true,
                    "content_hash": identities[&self.coroutines].clone(),
                    "path": self.coroutines,
                    "version": coroutines_version,
                },
            },
            "sandbox": {
                "environment": ["HOME", "JAVA_HOME", "JAVA_OPTS", "LC_ALL", "PATH", "TMPDIR"],
                "network": "disabled_by_default",
                "provider": "bubblewrap",
            },
        });
        Ok(ToolInspection {
            tools,
            identities,
            classpath,
            compile_only,
        })
    }
}

fn materialize_sources(
    emission: &KotlinEmission,
    source_root: &Path,
) -> Result<Vec<PathBuf>, String> {
    let mut sources = Vec::new();
    for (relative, bytes) in &emission.files {
        if !safe_relative(relative) {
            return Err(format!(
                "unsafe Kotlin emission path `{}`",
                relative.display()
            ));
        }
        if relative.extension().and_then(|value| value.to_str()) != Some("kt") {
            continue;
        }
        std::str::from_utf8(bytes)
            .map_err(|_| format!("Kotlin source `{}` is not valid UTF-8", relative.display()))?;
        if bytes.contains(&0) {
            return Err(format!(
                "Kotlin source `{}` contains NUL",
                relative.display()
            ));
        }
        let target = source_root.join(relative);
        fs::create_dir_all(
            target
                .parent()
                .ok_or_else(|| format!("Kotlin source `{}` has no parent", relative.display()))?,
        )
        .map_err(|error| format!("create Kotlin source directory: {error}"))?;
        fs::write(&target, bytes)
            .map_err(|error| format!("write Kotlin source `{}`: {error}", relative.display()))?;
        sources.push(target);
    }
    sources.sort();
    if sources.is_empty() {
        return Err("Kotlin emission contains no compilable source files".to_owned());
    }
    Ok(sources)
}

fn audit_canonical_ir(plan: &KotlinPlan, emission: &KotlinEmission) -> Result<(), String> {
    for module in &plan.ir.modules {
        let mut path = PathBuf::from("ir");
        let segments = module.module.segments.as_slice();
        for segment in &segments[..segments.len().saturating_sub(1)] {
            path.push(segment);
        }
        let Some(last) = segments.last() else {
            return Err("canonical Kotlin module has no name".to_owned());
        };
        path.push(format!("{last}.json"));
        match emission.files.get(&path) {
            Some(bytes) if bytes == &module.bytes => {}
            Some(_) => {
                return Err(format!(
                    "Kotlin emission canonical IR was tampered: {}",
                    path.display()
                ));
            }
            None => {
                return Err(format!(
                    "Kotlin emission omitted canonical IR: {}",
                    path.display()
                ));
            }
        }
    }
    Ok(())
}

fn validate_events(program: &RunnerProgram, events: &[Value]) -> Result<(), String> {
    let mut seen_cases = BTreeSet::new();
    let mut seen_cancellations = BTreeSet::new();
    let mut seen_scenarios = BTreeSet::new();
    let mut done = 0usize;
    for (index, event) in events.iter().enumerate() {
        match event.get("kind").and_then(Value::as_str) {
            Some("done") => {
                if index + 1 != events.len() {
                    return Err(
                        "Kotlin contract runner completion marker was not the final event"
                            .to_owned(),
                    );
                }
                done += 1;
            }
            Some("case") => {
                let symbol = required_event_string(event, "symbol")?;
                let case = required_event_u32(event, "case")?;
                let expected = program.expected_cases.get(symbol).ok_or_else(|| {
                    format!("Kotlin contract runner emitted an unknown case for `{symbol}`")
                })?;
                if case >= *expected || !seen_cases.insert((symbol.to_owned(), case)) {
                    return Err(format!(
                        "Kotlin contract runner emitted a duplicate or out-of-range case for `{symbol}`"
                    ));
                }
                let status = required_event_string(event, "status")?;
                match status {
                    "passed" => {
                        for observation in event
                            .get("observations")
                            .and_then(Value::as_array)
                            .ok_or("Kotlin case observations are not an array")?
                        {
                            if observation.get("passed").and_then(Value::as_bool) != Some(true) {
                                return Err(format!(
                                    "Kotlin runtime reported a failed clause without rejecting `{symbol}`"
                                ));
                            }
                        }
                    }
                    "ineligible" => {
                        if event.get("phase").and_then(Value::as_str) != Some("requires") {
                            return Err(format!(
                                "Kotlin runner marked `{symbol}` ineligible without a requires failure"
                            ));
                        }
                    }
                    "candidate_unavailable" => {}
                    "failed" | "timeout" | "unexpected_cancellation" | "unexpected_exception" => {
                        return Err(format!(
                            "Kotlin contract execution failed for `{symbol}` case {case} ({status})"
                        ));
                    }
                    other => {
                        return Err(format!(
                            "Kotlin contract runner emitted unknown case status `{other}`"
                        ));
                    }
                }
            }
            Some("cancellation") => {
                let symbol = required_event_string(event, "symbol")?;
                let case = required_event_u32(event, "case")?;
                let key = (symbol.to_owned(), case);
                if !program.expected_cancellations.contains(&key) || !seen_cancellations.insert(key)
                {
                    return Err(format!(
                        "Kotlin runner emitted duplicate or unknown cancellation evidence for `{symbol}`"
                    ));
                }
                match required_event_string(event, "status")? {
                    "passed" | "not_applicable" | "candidate_unavailable" => {}
                    status => {
                        return Err(format!(
                            "Kotlin async cancellation failed for `{symbol}` case {case} ({status})"
                        ));
                    }
                }
            }
            Some("scenario") => {
                let id = required_event_string(event, "scenario_id")?;
                if !program.expected_scenarios.contains(id) || !seen_scenarios.insert(id.to_owned())
                {
                    return Err(format!(
                        "Kotlin runner emitted duplicate or unknown scenario `{id}`"
                    ));
                }
                if required_event_string(event, "status")? != "passed" {
                    return Err(format!("Kotlin scenario `{id}` failed"));
                }
            }
            Some(other) => {
                return Err(format!(
                    "Kotlin contract runner emitted unknown event `{other}`"
                ));
            }
            None => return Err("Kotlin contract runner event has no kind".to_owned()),
        }
    }
    if done != 1 {
        return Err("Kotlin contract runner completion marker is missing or duplicated".to_owned());
    }
    for (symbol, count) in &program.expected_cases {
        for case in 0..*count {
            if !seen_cases.contains(&(symbol.clone(), case)) {
                return Err(format!(
                    "Kotlin contract runner omitted `{symbol}` case {case}"
                ));
            }
        }
    }
    if seen_cancellations != program.expected_cancellations {
        return Err("Kotlin contract runner omitted async cancellation evidence".to_owned());
    }
    if seen_scenarios != program.expected_scenarios {
        return Err("Kotlin contract runner omitted an enforceable scenario".to_owned());
    }
    Ok(())
}

fn contract_report(
    plan: &KotlinPlan,
    strategies: &[ContractTestStrategy],
    program: &RunnerProgram,
    events: &[Value],
) -> Result<Value, String> {
    let mut contracts = Vec::new();
    let mut passed_cases = BTreeMap::<String, u64>::new();
    let mut ineligible_cases = BTreeMap::<String, u64>::new();
    let case_events = events
        .iter()
        .filter(|event| event.get("kind").and_then(Value::as_str) == Some("case"))
        .collect::<Vec<_>>();
    for event in &case_events {
        let symbol = required_event_string(event, "symbol")?.to_owned();
        match required_event_string(event, "status")? {
            "passed" => *passed_cases.entry(symbol).or_default() += 1,
            "ineligible" => *ineligible_cases.entry(symbol).or_default() += 1,
            _ => {}
        }
    }

    for strategy in strategies {
        for clause_id in &strategy.clause_ids {
            let span = clause_span(plan, &strategy.symbol, clause_id)?;
            let guarded = clause_is_guarded(plan, &strategy.symbol, clause_id);
            let aliases = observation_aliases(&strategy.symbol);
            let mut phases = BTreeSet::new();
            let mut valid_cases = BTreeSet::new();
            let mut valid_scenarios = BTreeSet::new();
            for event in &case_events {
                if event.get("status").and_then(Value::as_str) != Some("passed") {
                    continue;
                }
                let event_symbol = required_event_string(event, "symbol")?;
                if event_symbol != strategy.symbol {
                    continue;
                }
                for observation in event
                    .get("observations")
                    .and_then(Value::as_array)
                    .ok_or("Kotlin case observations are not an array")?
                {
                    let observation_symbol = observation
                        .get("symbol")
                        .and_then(Value::as_str)
                        .ok_or("Kotlin clause observation has no symbol")?;
                    if aliases.contains(observation_symbol)
                        && observation.get("clause").and_then(Value::as_str)
                            == Some(clause_id.as_str())
                        && observation.get("passed").and_then(Value::as_bool) == Some(true)
                    {
                        phases.insert(
                            observation
                                .get("phase")
                                .and_then(Value::as_str)
                                .unwrap_or("contract")
                                .to_owned(),
                        );
                        valid_cases.insert(required_event_u32(event, "case")?);
                    }
                }
            }
            for event in events.iter().filter(|event| {
                event.get("kind").and_then(Value::as_str) == Some("scenario")
                    && event.get("status").and_then(Value::as_str) == Some("passed")
            }) {
                for observation in event
                    .get("observations")
                    .and_then(Value::as_array)
                    .ok_or("Kotlin scenario observations are not an array")?
                {
                    if aliases.contains(
                        observation
                            .get("symbol")
                            .and_then(Value::as_str)
                            .ok_or("Kotlin scenario observation has no symbol")?,
                    ) && observation.get("clause").and_then(Value::as_str)
                        == Some(clause_id.as_str())
                        && observation.get("passed").and_then(Value::as_bool) == Some(true)
                    {
                        phases.insert(
                            observation
                                .get("phase")
                                .and_then(Value::as_str)
                                .unwrap_or("contract")
                                .to_owned(),
                        );
                        valid_scenarios.insert(required_event_string(event, "scenario_id")?);
                    }
                }
            }
            let evidence = if !valid_cases.is_empty() || !valid_scenarios.is_empty() {
                vec![json!({
                    "applicable_cases": valid_cases.len() + valid_scenarios.len(),
                    "grade": "runtime check",
                    "phases": phases,
                    "positive_applicable": true,
                    "status": "passed",
                    "valid_cases": valid_cases.len() + valid_scenarios.len(),
                })]
            } else {
                let reason = program
                    .unavailable
                    .get(&strategy.symbol)
                    .cloned()
                    .unwrap_or_else(|| {
                        if guarded {
                            "no matched guarded clause condition completed successfully"
                                .to_owned()
                        } else if clause_id.starts_with("error:") {
                            "individual Result error branch was not reached by a positive applicable case; aggregate first-error priority remained enforced"
                                .to_owned()
                        } else if clause_id.starts_with("modifies:") {
                            "a modifies permission is not itself evidence of a state mutation; no positive frame observation matched this field"
                                .to_owned()
                        } else if passed_cases.get(&strategy.symbol).copied().unwrap_or(0) == 0
                            && ineligible_cases.get(&strategy.symbol).copied().unwrap_or(0) > 0
                        {
                            "no bounded candidate satisfied every requires clause".to_owned()
                        } else {
                            "no generated positive applicable case observed this clause".to_owned()
                        }
                    });
                vec![json!({
                    "applicable_cases": 0,
                    "grade": "unobserved",
                    "reason": reason,
                    "status": "unknown",
                    "valid_cases": 0,
                })]
            };
            contracts.push(json!({
                "clause_id": clause_id,
                "evidence": evidence,
                "span": span,
                "symbol": strategy.symbol,
            }));
        }
    }
    contracts.sort_by(|left, right| {
        coverage_key(
            left.get("symbol")
                .and_then(Value::as_str)
                .unwrap_or_default(),
            left.get("clause_id")
                .and_then(Value::as_str)
                .unwrap_or_default(),
        )
        .cmp(&coverage_key(
            right
                .get("symbol")
                .and_then(Value::as_str)
                .unwrap_or_default(),
            right
                .get("clause_id")
                .and_then(Value::as_str)
                .unwrap_or_default(),
        ))
    });
    let cases = case_events
        .into_iter()
        .map(|event| {
            json!({
                "case": event.get("case").cloned().unwrap_or(Value::Null),
                "status": event.get("status").cloned().unwrap_or(Value::Null),
                "symbol": event.get("symbol").cloned().unwrap_or(Value::Null),
            })
        })
        .collect::<Vec<_>>();
    let lifecycle = events
        .iter()
        .filter(|event| event.get("kind").and_then(Value::as_str) == Some("cancellation"))
        .cloned()
        .collect::<Vec<_>>();
    let scenarios = events
        .iter()
        .filter(|event| event.get("kind").and_then(Value::as_str) == Some("scenario"))
        .cloned()
        .collect::<Vec<_>>();
    let observation_inventory = json!({
        "cases": cases.len(),
        "clauses": contracts.len(),
        "lifecycle": lifecycle.len(),
        "scenarios": scenarios.len(),
        "strategies": strategies.len(),
        "status": if strategies.is_empty() {
            "not_applicable"
        } else {
            "executed"
        },
    });
    let strategy_values = strategies
        .iter()
        .map(serde_json::to_value)
        .collect::<Result<Vec<_>, _>>()
        .map_err(|error| format!("serialize Kotlin contract strategy: {error}"))?;
    Ok(json!({
        "cases": cases,
        "contracts": contracts,
        "lifecycle": lifecycle,
        "observation_inventory": observation_inventory,
        "scenarios": scenarios,
        "strategies": strategy_values,
        "unavailable": program.unavailable,
    }))
}
fn clause_is_guarded(plan: &KotlinPlan, symbol: &str, clause_id: &str) -> bool {
    let Some((kind, id)) = clause_id.split_once(':') else {
        return false;
    };
    let Ok(id) = id.parse::<u64>() else {
        return false;
    };
    if kind == "modifies" {
        return false;
    }
    let callables = plan.callables();
    if let Some(callable) = callables.iter().find(|callable| callable.symbol == symbol) {
        if find_guarded_clause(&callable.declaration, kind, id) {
            return true;
        }
        return kind == "invariant"
            && callable
                .owner
                .as_ref()
                .and_then(|owner| owner.get("invariants"))
                .is_some_and(|invariants| find_guarded_clause(invariants, kind, id));
    }
    let owner_symbol = symbol.strip_suffix(".init").unwrap_or(symbol);
    plan.modules
        .iter()
        .flat_map(|module| &module.declarations)
        .find(|declaration| declaration.get("name").and_then(Value::as_str) == Some(owner_symbol))
        .and_then(|owner| {
            if kind == "invariant" {
                owner.get("invariants")
            } else {
                owner.get("init")
            }
        })
        .is_some_and(|scope| find_guarded_clause(scope, kind, id))
}

fn find_guarded_clause(value: &Value, kind: &str, id: u64) -> bool {
    match value {
        Value::Object(object) => {
            let matches = if kind == "invariant" {
                object.get("kind").is_none()
                    && object.get("clause_id").and_then(Value::as_u64) == Some(id)
                    && object.get("expression").is_some()
                    && object.get("span").is_some()
            } else {
                object.get("kind").and_then(Value::as_str) == Some(kind)
                    && object.get("clause_id").and_then(Value::as_u64) == Some(id)
            };
            (matches && object.get("guard").is_some_and(|guard| !guard.is_null()))
                || object
                    .values()
                    .any(|child| find_guarded_clause(child, kind, id))
        }
        Value::Array(values) => values
            .iter()
            .any(|child| find_guarded_clause(child, kind, id)),
        _ => false,
    }
}

fn clause_span(plan: &KotlinPlan, symbol: &str, clause_id: &str) -> Result<Value, String> {
    let (kind, id) = clause_id
        .split_once(':')
        .ok_or_else(|| format!("invalid Kotlin clause ID `{symbol}:{clause_id}`"))?;
    if kind == "modifies" {
        let callable = plan
            .callables()
            .into_iter()
            .find(|callable| callable.symbol == symbol)
            .ok_or_else(|| format!("no Kotlin callable owns `{symbol}:{clause_id}`"))?;
        return callable
            .declaration
            .get("span")
            .cloned()
            .ok_or_else(|| format!("Kotlin callable `{symbol}` has no span"));
    }
    let numeric = id
        .parse::<u64>()
        .map_err(|_| format!("invalid Kotlin clause ID `{symbol}:{clause_id}`"))?;
    let owner_symbol = symbol.strip_suffix(".init").unwrap_or(symbol);
    let callables = plan.callables();
    let callable = callables.iter().find(|callable| callable.symbol == symbol);
    let owner = callable
        .and_then(|callable| callable.owner.as_ref())
        .or_else(|| {
            plan.modules
                .iter()
                .flat_map(|module| &module.declarations)
                .find(|declaration| {
                    declaration.get("name").and_then(Value::as_str) == Some(owner_symbol)
                })
        });
    let mut candidates = Vec::new();
    if let Some(callable) = callable {
        collect_clause_candidates(&callable.declaration, kind, numeric, &mut candidates);
        if kind == "invariant"
            && let Some(invariants) = callable
                .owner
                .as_ref()
                .and_then(|owner| owner.get("invariants"))
        {
            collect_clause_candidates(invariants, kind, numeric, &mut candidates);
        }
    } else {
        let owner =
            owner.ok_or_else(|| format!("no canonical declaration owns `{symbol}:{clause_id}`"))?;
        let scope = if kind == "invariant" {
            owner.get("invariants")
        } else {
            owner.get("init")
        }
        .ok_or_else(|| format!("no canonical declaration owns `{symbol}:{clause_id}`"))?;
        collect_clause_candidates(scope, kind, numeric, &mut candidates);
    }
    candidates.sort_by_key(|value| serde_json::to_string(value).unwrap_or_default());
    candidates.dedup();
    match candidates.as_slice() {
        [span] => Ok(span.clone()),
        [] => Err(format!(
            "canonical Kotlin clause `{symbol}:{clause_id}` has no source span"
        )),
        _ => Err(format!(
            "canonical Kotlin clause `{symbol}:{clause_id}` has ambiguous source spans"
        )),
    }
}

fn collect_clause_candidates(value: &Value, kind: &str, id: u64, candidates: &mut Vec<Value>) {
    match value {
        Value::Object(object) => {
            let matches = if kind == "invariant" {
                object.get("kind").is_none()
                    && object.get("clause_id").and_then(Value::as_u64) == Some(id)
                    && object.get("expression").is_some()
                    && object.get("span").is_some()
            } else {
                object.get("kind").and_then(Value::as_str) == Some(kind)
                    && object.get("clause_id").and_then(Value::as_u64) == Some(id)
            };
            if matches {
                if let Some(span) = object.get("span") {
                    candidates.push(span.clone());
                }
            }
            for child in object.values() {
                collect_clause_candidates(child, kind, id, candidates);
            }
        }
        Value::Array(values) => {
            for child in values {
                collect_clause_candidates(child, kind, id, candidates);
            }
        }
        _ => {}
    }
}

fn observation_aliases(symbol: &str) -> BTreeSet<&str> {
    let mut aliases = BTreeSet::from([symbol]);
    if let Some(owner) = symbol.strip_suffix(".init") {
        aliases.insert(owner);
    }
    aliases
}

fn coverage_key(symbol: &str, clause_id: &str) -> (String, u8, u64, String) {
    let (kind, id) = clause_id.split_once(':').unwrap_or((clause_id, "0"));
    let order = match kind {
        "requires" => 0,
        "ensures" => 1,
        "error" => 2,
        "modifies" => 3,
        "invariant" => 4,
        _ => 5,
    };
    (
        symbol.to_owned(),
        order,
        id.parse().unwrap_or_default(),
        if kind == "modifies" {
            id.to_owned()
        } else {
            String::new()
        },
    )
}

fn reject_class_shadowing(
    toolchain: &Toolchain,
    scratch: &Path,
    jars: &[(String, PathBuf)],
) -> Result<(), String> {
    reject_manifest_class_paths(toolchain, scratch, jars)?;
    let mut classes = BTreeMap::<String, String>::new();
    for (label, path) in jars {
        let mut arguments = java_arguments(scratch, Vec::new())
            .into_iter()
            .map(|argument| format!("-J{argument}"))
            .collect::<Vec<_>>();
        arguments.extend(["tf".to_owned(), path_argument(path, "JAR input")?]);
        let listed = sandbox_process(
            &toolchain.jar,
            arguments,
            scratch,
            toolchain,
            compiler_binds(scratch, toolchain, std::slice::from_ref(path)),
            NetworkAccess::Disabled,
            jar_limits(),
            false,
        )?;
        require_compile_success(&format!("inspect JAR `{label}`"), &listed, scratch)?;
        let listing = std::str::from_utf8(&listed.stdout)
            .map_err(|_| format!("JAR `{label}` listing is not UTF-8"))?;
        let mut raw_entries = BTreeSet::new();
        let mut logical_classes = BTreeSet::new();
        for entry in listing.lines() {
            validate_jar_entry(label, entry)?;
            if !raw_entries.insert(entry.to_owned()) {
                return Err(format!("JAR `{label}` contains duplicate entry `{entry}`"));
            }
            if entry.ends_with(".class") {
                if let Some(logical) = logical_class_name(label, entry)? {
                    logical_classes.insert(logical.to_owned());
                }
            }
        }
        for class in logical_classes {
            if let Some(previous) = classes.insert(class.clone(), label.clone()) {
                return Err(format!(
                    "Kotlin classpath shadowing is forbidden: class `{class}` occurs in `{previous}` and `{label}`"
                ));
            }
        }
    }
    Ok(())
}

fn reject_manifest_class_paths(
    toolchain: &Toolchain,
    scratch: &Path,
    jars: &[(String, PathBuf)],
) -> Result<(), String> {
    if jars.is_empty() {
        return Ok(());
    }
    let probe_source = scratch.join("CottJarManifestProbe.java");
    if !probe_source.exists() {
        fs::write(
            &probe_source,
            br#"import java.util.jar.Attributes;
import java.util.jar.JarFile;
import java.util.jar.Manifest;

public final class CottJarManifestProbe {
    public static void main(String[] arguments) throws Exception {
        for (int index = 0; index < arguments.length; index++) {
            try (JarFile jar = new JarFile(arguments[index], false)) {
                Manifest manifest = jar.getManifest();
                String classPath = manifest == null
                    ? null
                    : manifest.getMainAttributes().getValue(Attributes.Name.CLASS_PATH);
                if (classPath != null && !classPath.isEmpty()) {
                    System.out.println(index);
                }
            }
        }
    }
}
"#,
        )
        .map_err(|error| format!("write bounded JAR manifest probe: {error}"))?;
    }
    let mut arguments = vec![path_argument(&probe_source, "JAR manifest probe")?];
    arguments.extend(
        jars.iter()
            .map(|(_, path)| path_argument(path, "JAR manifest input"))
            .collect::<Result<Vec<_>, _>>()?,
    );
    let inputs = jars
        .iter()
        .map(|(_, path)| path.clone())
        .collect::<Vec<_>>();
    let inspected = sandbox_process(
        &toolchain.java,
        java_arguments(scratch, arguments),
        scratch,
        toolchain,
        compiler_binds(scratch, toolchain, &inputs),
        NetworkAccess::Disabled,
        jar_limits(),
        false,
    )?;
    require_compile_success("inspect JAR manifests", &inspected, scratch)?;
    let output = std::str::from_utf8(&inspected.stdout)
        .map_err(|_| "JAR manifest inspection output is not UTF-8")?;
    let mut rejected = None;
    for line in output.lines() {
        let index = line
            .parse::<usize>()
            .ok()
            .filter(|index| *index < jars.len())
            .ok_or("JAR manifest inspection returned an invalid result")?;
        rejected.get_or_insert(index);
    }
    if let Some(index) = rejected {
        return Err(format!(
            "JAR `{}` has a nonempty manifest Class-Path attribute",
            &jars[index].0
        ));
    }
    Ok(())
}

fn validate_jar_entry(label: &str, entry: &str) -> Result<(), String> {
    let path = entry.strip_suffix('/').unwrap_or(entry);
    if path.is_empty()
        || path.starts_with('/')
        || path.contains('\\')
        || path
            .split('/')
            .any(|part| part.is_empty() || part == "." || part == "..")
    {
        return Err(format!("JAR `{label}` contains unsafe entry `{entry}`"));
    }
    Ok(())
}

fn logical_class_name<'a>(label: &str, entry: &'a str) -> Result<Option<&'a str>, String> {
    if entry == "module-info.class" {
        return Ok(None);
    }
    let Some(versioned) = entry.strip_prefix("META-INF/versions/") else {
        return Ok(Some(entry));
    };
    let (release, class) = versioned.split_once('/').ok_or_else(|| {
        format!("JAR `{label}` contains malformed multi-release class entry `{entry}`")
    })?;
    let valid_release =
        !release.starts_with('0') && release.parse::<u32>().is_ok_and(|release| release >= 9);
    if !valid_release {
        return Err(format!(
            "JAR `{label}` contains malformed multi-release class entry `{entry}`"
        ));
    }
    if class == "module-info.class" {
        Ok(None)
    } else {
        Ok(Some(class))
    }
}

fn compiler_library_records(
    kotlin_home: &Path,
    identities: &mut BTreeMap<PathBuf, String>,
) -> Result<Value, String> {
    let library_root = kotlin_home.join("lib");
    let mut paths = fs::read_dir(&library_root)
        .map_err(|error| format!("read Kotlin compiler libraries: {error}"))?
        .map(|entry| {
            entry
                .map(|entry| entry.path())
                .map_err(|error| format!("read Kotlin compiler library entry: {error}"))
        })
        .collect::<Result<Vec<_>, _>>()?;
    paths.sort();
    let mut records = BTreeMap::new();
    for path in paths {
        if path.extension().and_then(|value| value.to_str()) != Some("jar") {
            continue;
        }
        if records.len() >= MAX_IDENTITY_LIBRARIES {
            return Err("Kotlin compiler distribution has too many library JARs".to_owned());
        }
        let path = regular_file(&path, "Kotlin compiler library")?;
        let hash = hash_file(&path)?;
        identities.insert(path.clone(), hash.clone());
        let name = path
            .file_name()
            .and_then(|value| value.to_str())
            .ok_or("Kotlin compiler library name is not UTF-8")?;
        records.insert(name.to_owned(), json!({"content_hash": hash, "path": path}));
    }
    serde_json::to_value(records).map_err(|error| error.to_string())
}

fn dependency_records(
    paths: &[PathBuf],
    scope: &str,
    identities: &mut BTreeMap<PathBuf, String>,
) -> Result<Vec<Value>, String> {
    paths
        .iter()
        .enumerate()
        .map(|(index, path)| {
            let hash = match identities.get(path) {
                Some(hash) => hash.clone(),
                None => hash_file(path)?,
            };
            identities.insert(path.clone(), hash.clone());
            Ok(json!({
                "content_hash": hash,
                "index": index,
                "path": path,
                "scope": scope,
            }))
        })
        .collect()
}

fn canonical_inputs(paths: &[PathBuf], label: &str) -> Result<Vec<PathBuf>, String> {
    let mut canonical = Vec::with_capacity(paths.len());
    let mut seen = BTreeSet::new();
    for path in paths {
        let resolved = regular_file(path, label)?;
        if !seen.insert(resolved.clone()) {
            return Err(format!(
                "{label} contains duplicate JAR `{}`",
                path.display()
            ));
        }
        canonical.push(resolved);
    }
    Ok(canonical)
}

fn resolve_executable(root: &Path, spec: &str, label: &str) -> Result<PathBuf, String> {
    let configured = Path::new(spec);
    let candidate = if configured.is_absolute() {
        configured.to_path_buf()
    } else if configured.components().count() > 1 {
        root.join(configured)
    } else {
        let path = std::env::var_os("PATH")
            .ok_or_else(|| format!("missing PATH while locating {label}"))?;
        std::env::split_paths(&path)
            .map(|directory| directory.join(configured))
            .find(|path| fs::metadata(path).is_ok_and(|metadata| metadata.is_file()))
            .ok_or_else(|| format!("{label} `{spec}` was not found on PATH"))?
    };
    regular_file(&candidate, label)
}

fn regular_file(path: &Path, label: &str) -> Result<PathBuf, String> {
    let canonical = fs::canonicalize(path)
        .map_err(|error| format!("resolve {label} {}: {error}", path.display()))?;
    let metadata = fs::symlink_metadata(&canonical)
        .map_err(|error| format!("inspect {label} {}: {error}", canonical.display()))?;
    if !metadata.is_file() || metadata.file_type().is_symlink() || metadata.nlink() != 1 {
        return Err(format!(
            "{label} must resolve to a regular single-link file: {}",
            canonical.display()
        ));
    }
    if canonical.to_str().is_none() {
        return Err(format!("{label} path must be UTF-8"));
    }
    Ok(canonical)
}

fn sandbox_process(
    program: &Path,
    arguments: Vec<String>,
    scratch: &Path,
    toolchain: &Toolchain,
    binds: BindMounts,
    network: NetworkAccess,
    limits: ResourceLimits,
    compiler: bool,
) -> Result<crate::sandbox::CompletedProcess, String> {
    sandbox_process_with_stdin(
        program,
        arguments,
        scratch,
        toolchain,
        binds,
        network,
        limits,
        compiler,
        Vec::new(),
    )
}

#[allow(clippy::too_many_arguments)]
fn sandbox_process_with_stdin(
    program: &Path,
    arguments: Vec<String>,
    scratch: &Path,
    toolchain: &Toolchain,
    binds: BindMounts,
    network: NetworkAccess,
    limits: ResourceLimits,
    compiler: bool,
    stdin: Vec<u8>,
) -> Result<crate::sandbox::CompletedProcess, String> {
    let path = std::env::join_paths([
        toolchain.kotlin_home.join("bin"),
        toolchain.java_home.join("bin"),
        PathBuf::from("/usr/bin"),
        PathBuf::from("/bin"),
    ])
    .map_err(|error| format!("construct sanitized Kotlin PATH: {error}"))?;
    let mut environment = BTreeMap::from([
        ("HOME".to_owned(), path_argument(scratch, "Kotlin scratch")?),
        (
            "JAVA_HOME".to_owned(),
            path_argument(&toolchain.java_home, "JDK home")?,
        ),
        ("LC_ALL".to_owned(), "C.UTF-8".to_owned()),
        ("PATH".to_owned(), path.to_string_lossy().into_owned()),
        (
            "TMPDIR".to_owned(),
            path_argument(scratch, "Kotlin scratch")?,
        ),
    ]);
    if compiler {
        environment.insert("JAVA_OPTS".to_owned(), compiler_jvm_flags().join(" "));
    }
    run(&SandboxSpec {
        program: program.to_path_buf(),
        arguments,
        cwd: scratch.to_path_buf(),
        environment,
        stdin,
        binds,
        network,
        limits,
    })
    .map_err(|error| format!("sandboxed Kotlin tool execution failed: {error}"))
}

fn compiler_binds(scratch: &Path, toolchain: &Toolchain, inputs: &[PathBuf]) -> BindMounts {
    let mut read_only = vec![toolchain.kotlin_home.clone(), toolchain.java_home.clone()];
    read_only.extend(inputs.iter().cloned());
    read_only.sort();
    read_only.dedup();
    BindMounts {
        read_only,
        writable: vec![scratch.to_path_buf()],
    }
}

fn compiler_jvm_flags() -> Vec<&'static str> {
    vec![
        "-Xms32m",
        "-Xmx512m",
        "-XX:MaxMetaspaceSize=256m",
        "-XX:CompressedClassSpaceSize=64m",
        "-XX:ReservedCodeCacheSize=128m",
        "-XX:ActiveProcessorCount=2",
        "-XX:+UseSerialGC",
        "-Dfile.encoding=UTF-8",
        "-Dkotlin.environment.keepalive=false",
    ]
}

fn java_arguments(scratch: &Path, mut arguments: Vec<String>) -> Vec<String> {
    let mut prefix = vec![
        "-Xms16m".to_owned(),
        "-Xmx256m".to_owned(),
        "-XX:MaxMetaspaceSize=128m".to_owned(),
        "-XX:CompressedClassSpaceSize=64m".to_owned(),
        "-XX:ReservedCodeCacheSize=64m".to_owned(),
        "-XX:ActiveProcessorCount=2".to_owned(),
        "-XX:+UseSerialGC".to_owned(),
        "-Dfile.encoding=UTF-8".to_owned(),
        "-Duser.language=en".to_owned(),
        "-Duser.country=US".to_owned(),
        format!("-Duser.home={}", scratch.display()),
        format!("-Djava.io.tmpdir={}", scratch.display()),
    ];
    prefix.append(&mut arguments);
    prefix
}

fn probe_limits() -> ResourceLimits {
    ResourceLimits {
        cpu_time: Duration::from_secs(10),
        address_space_bytes: 2 * 1024 * 1024 * 1024,
        process_count: KOTLIN_JVM_TASK_ALLOWANCE,
        open_files: 128,
        file_size_bytes: 8 * 1024 * 1024,
        wall_time: Duration::from_secs(15),
        stream_limit_bytes: 1024 * 1024,
        writable_bytes: 16 * 1024 * 1024,
    }
}

fn compiler_limits() -> ResourceLimits {
    ResourceLimits {
        cpu_time: Duration::from_secs(60),
        address_space_bytes: 4 * 1024 * 1024 * 1024,
        process_count: KOTLIN_JVM_TASK_ALLOWANCE,
        open_files: 512,
        file_size_bytes: 128 * 1024 * 1024,
        wall_time: Duration::from_secs(90),
        stream_limit_bytes: 4 * 1024 * 1024,
        writable_bytes: 256 * 1024 * 1024,
    }
}

fn runtime_limits(config: &KotlinProjectConfig) -> ResourceLimits {
    let scenario_seconds =
        u64::from(config.verification.fixtures.scenario_timeout_ms).saturating_add(999) / 1000;
    ResourceLimits {
        cpu_time: Duration::from_secs(30),
        address_space_bytes: 2 * 1024 * 1024 * 1024,
        process_count: KOTLIN_JVM_TASK_ALLOWANCE,
        open_files: 256,
        file_size_bytes: config
            .verification
            .fixtures
            .filesystem_bytes
            .max(8 * 1024 * 1024),
        wall_time: Duration::from_secs(scenario_seconds.saturating_add(30).min(90)),
        stream_limit_bytes: 4 * 1024 * 1024,
        writable_bytes: config
            .verification
            .fixtures
            .filesystem_bytes
            .saturating_add(32 * 1024 * 1024),
    }
}

fn jar_limits() -> ResourceLimits {
    ResourceLimits {
        cpu_time: Duration::from_secs(20),
        address_space_bytes: 2 * 1024 * 1024 * 1024,
        process_count: KOTLIN_JVM_TASK_ALLOWANCE,
        open_files: 256,
        file_size_bytes: 8 * 1024 * 1024,
        wall_time: Duration::from_secs(30),
        stream_limit_bytes: 32 * 1024 * 1024,
        writable_bytes: 16 * 1024 * 1024,
    }
}

fn require_compile_success(
    label: &str,
    completed: &crate::sandbox::CompletedProcess,
    scratch: &Path,
) -> Result<(), String> {
    if completed.status == Some(0) {
        return Ok(());
    }
    let diagnostics = sanitized_diagnostics(&completed.stdout, &completed.stderr, scratch);
    Err(if diagnostics.is_empty() {
        format!("{label} failed with status {:?}", completed.status)
    } else {
        format!(
            "{label} failed with status {:?}:\n{}",
            completed.status,
            diagnostics.join("\n")
        )
    })
}

fn sanitized_diagnostics(stdout: &[u8], stderr: &[u8], scratch: &Path) -> Vec<String> {
    let scratch = scratch.to_string_lossy();
    stdout
        .split(|byte| *byte == b'\n')
        .chain(stderr.split(|byte| *byte == b'\n'))
        .filter_map(|line| std::str::from_utf8(line).ok())
        .map(str::trim)
        .filter(|line| !line.is_empty())
        .take(MAX_DIAGNOSTICS)
        .map(|line| {
            let line = line.replace(scratch.as_ref(), "<scratch>");
            line.chars().take(512).collect()
        })
        .collect()
}

fn verify_identities(expected: &BTreeMap<PathBuf, String>) -> Result<(), String> {
    for (path, hash) in expected {
        let actual = hash_file(path)?;
        if &actual != hash {
            return Err(format!(
                "Kotlin tool or dependency changed during verification: {}",
                path.display()
            ));
        }
    }
    Ok(())
}

fn hash_file(path: &Path) -> Result<String, String> {
    fs::read(path)
        .map(|bytes| format!("sha256:{}", sha256_hex(&bytes)))
        .map_err(|error| format!("hash Kotlin tool input {}: {error}", path.display()))
}

fn module_name(config: &KotlinProjectConfig) -> String {
    let normalized = config.project.name.replace('-', "_");
    let identity = format!("{}@{}", config.project.name, config.project.version);
    format!(
        "cott_{normalized}_{}",
        &sha256_hex(identity.as_bytes())[..12]
    )
}

fn joined_paths(paths: &[PathBuf], label: &str) -> Result<String, String> {
    std::env::join_paths(paths)
        .map_err(|error| format!("construct {label}: {error}"))?
        .into_string()
        .map_err(|_| format!("{label} contains a non-UTF-8 path"))
}

fn path_argument(path: &Path, label: &str) -> Result<String, String> {
    path.to_str()
        .map(str::to_owned)
        .ok_or_else(|| format!("{label} path is not UTF-8"))
}

fn combined_output(process: &crate::sandbox::CompletedProcess) -> String {
    let mut output = String::from_utf8_lossy(&process.stdout).into_owned();
    output.push('\n');
    output.push_str(&String::from_utf8_lossy(&process.stderr));
    output
}

fn token_after<'a>(value: &'a str, marker: &str) -> Option<&'a str> {
    value
        .split_once(marker)
        .and_then(|(_, rest)| rest.split_whitespace().next())
        .filter(|token| !token.is_empty())
}

fn quoted_version(value: &str) -> Option<&str> {
    let (_, rest) = value.split_once("version \"")?;
    rest.split_once('"').map(|(version, _)| version)
}

fn version_at_least(value: &str, minimum: (u64, u64, u64)) -> bool {
    let mut parts = value.split('.').map(str::parse::<u64>);
    let (Some(Ok(major)), Some(Ok(minor)), Some(Ok(patch))) =
        (parts.next(), parts.next(), parts.next())
    else {
        return false;
    };
    parts.next().is_none() && (major, minor, patch) >= minimum
}

fn required_event_string<'a>(event: &'a Value, field: &str) -> Result<&'a str, String> {
    event
        .get(field)
        .and_then(Value::as_str)
        .ok_or_else(|| format!("Kotlin runner event has no string `{field}`"))
}

fn required_event_u32(event: &Value, field: &str) -> Result<u32, String> {
    event
        .get(field)
        .and_then(Value::as_u64)
        .and_then(|value| u32::try_from(value).ok())
        .ok_or_else(|| format!("Kotlin runner event has no u32 `{field}`"))
}

fn safe_relative(path: &Path) -> bool {
    !path.as_os_str().is_empty()
        && path.is_relative()
        && path
            .components()
            .all(|component| matches!(component, Component::Normal(_)))
}

fn scratch_directory() -> Result<PathBuf, String> {
    let mut nonce = NEXT_SCRATCH.fetch_add(1, Ordering::Relaxed);
    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|error| format!("read system time for Kotlin verification: {error}"))?
        .as_nanos();
    loop {
        let path = std::env::temp_dir().join(format!(
            "cott-kotlin-verify-{}-{timestamp}-{nonce}",
            std::process::id()
        ));
        match fs::DirBuilder::new().mode(0o700).create(&path) {
            Ok(()) => return Ok(path),
            Err(error) if error.kind() == io::ErrorKind::AlreadyExists => {
                nonce = nonce.saturating_add(1);
            }
            Err(error) => {
                return Err(format!(
                    "create Kotlin verification scratch {}: {error}",
                    path.display()
                ));
            }
        }
    }
}

fn finish_scratch<T>(scratch: PathBuf, result: Result<T, String>) -> Result<T, String> {
    let cleanup = fs::remove_dir_all(&scratch);
    match (result, cleanup) {
        (Err(error), _) => Err(error),
        (Ok(_), Err(error)) => Err(format!(
            "remove Kotlin verification scratch {}: {error}",
            scratch.display()
        )),
        (Ok(value), Ok(())) => Ok(value),
    }
}
