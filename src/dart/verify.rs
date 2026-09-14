use std::collections::{BTreeMap, BTreeSet};
use std::fmt::Write as _;
use std::fs::{self, DirBuilder, OpenOptions};
use std::io::Read;
use std::os::unix::fs::{DirBuilderExt, MetadataExt, OpenOptionsExt, PermissionsExt};
use std::path::{Component, Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use serde_json::{Value, json};
use sha2::{Digest as _, Sha256};
use tree_sitter::{Node, Parser};

use crate::contract_test::{ContractTestStrategy, derive_strategies};
use crate::hash::sha256_hex;
use crate::manifest::DartProjectConfig;
use crate::project::DartPaths;
use crate::proof::prove_contracts;
use crate::provenance::{SemanticCoverage, validate_semantic_coverage};
use crate::sandbox::{BindMounts, NetworkAccess, ResourceLimits, SandboxSpec, run};

use super::dependencies::{self, PackageMetadata, ResolvedDependencies};
use super::runner::{self, RunnerProgram};
use super::{DartEmission, DartPlan};

const MINIMUM_DART: (u64, u64, u64) = (3, 13, 3);
const MAXIMUM_DART_MAJOR: u64 = 4;
const KERNEL_ARTIFACT: &str = "dart/verification/cott-module.dill";
const MAX_DIAGNOSTICS: usize = 20;
const DART_PROCESS_ALLOWANCE: u64 = 64;
static NEXT_SCRATCH: AtomicU64 = AtomicU64::new(0);

#[derive(Clone, Debug)]
pub(crate) struct Verification {
    pub artifacts: BTreeMap<PathBuf, Vec<u8>>,
    pub tools: Value,
    pub report: Value,
    pub coverage: SemanticCoverage,
    pub dependencies: Value,
}

#[derive(Clone, Debug)]
struct Toolchain {
    executable: PathBuf,
    distribution: PathBuf,
    identity_files: BTreeMap<PathBuf, String>,
}

#[derive(Clone, Debug)]
struct ToolInspection {
    tools: Value,
    identity_files: BTreeMap<PathBuf, String>,
}

pub(crate) fn probe(config: &DartProjectConfig, paths: &DartPaths) -> Result<Value, String> {
    let scratch = scratch_directory()?;
    let result = (|| {
        let toolchain = Toolchain::discover(config, paths)?;
        Ok(toolchain.inspect(&scratch)?.tools)
    })();
    finish_scratch(scratch, result)
}

pub(crate) fn verify(
    config: &DartProjectConfig,
    paths: &DartPaths,
    plan: &DartPlan,
    emission: &DartEmission,
    metadata: &PackageMetadata,
) -> Result<Verification, String> {
    if !emission.unresolved.is_empty() {
        let mut unresolved = emission.unresolved.clone();
        unresolved.sort();
        unresolved.dedup();
        return Err(format!(
            "Dart verification requires a fully resolved target; unresolved: {}",
            unresolved.join(", ")
        ));
    }
    let strategies = derive_strategies(&plan.ir, &config.verification)
        .map_err(|error| format!("derive Dart contract strategies: {error}"))?;
    let contract_proofs = prove_contracts(&plan.ir, None, &config.verification)
        .map_err(|error| format!("prove Dart contracts: {error}"))?;
    let program = runner::render(config, plan, &strategies, &config.verification)
        .map_err(|error| format!("render bounded Dart contract runner: {error}"))?;
    let scratch = scratch_directory()?;
    let result = verify_in_scratch(
        config,
        paths,
        plan,
        emission,
        metadata,
        &strategies,
        contract_proofs,
        &program,
        &scratch,
    );
    finish_scratch(scratch, result)
}

#[allow(clippy::too_many_arguments)]
fn verify_in_scratch(
    config: &DartProjectConfig,
    paths: &DartPaths,
    plan: &DartPlan,
    emission: &DartEmission,
    metadata: &PackageMetadata,
    strategies: &[ContractTestStrategy],
    contract_proofs: Value,
    program: &RunnerProgram,
    scratch: &Path,
) -> Result<Verification, String> {
    audit_canonical_ir(plan, emission)?;
    let support_identity = runner::validate_support()?;
    let toolchain = Toolchain::discover(config, paths)?;
    let inspection = toolchain.inspect(scratch)?;
    let pub_cache = configured_pub_cache()?;
    let resolved = dependencies::resolve(metadata, pub_cache.as_deref())
        .map_err(|error| format!("resolve locked Dart dependencies: {error}"))?;
    dependencies::validate_frozen_resolution(metadata, &resolved)
        .map_err(|error| format!("validate frozen Dart dependency material: {error}"))?;

    let package_root = scratch.join("package");
    let compiler_root = scratch.join("compiler");
    fs::create_dir(&package_root)
        .map_err(|error| format!("create Dart package scratch: {error}"))?;
    fs::create_dir(&compiler_root)
        .map_err(|error| format!("create Dart compiler scratch: {error}"))?;
    materialize_package(emission, &resolved, &package_root)?;
    audit_package_sources(&package_root)?;

    let compiler_lock = dependencies::compiler_lock(metadata, &resolved)?;
    fs::write(package_root.join("pubspec.lock"), &compiler_lock)
        .map_err(|error| format!("write compiler-owned Dart lockfile: {error}"))?;
    let isolated_pub_cache = compiler_root.join("pub-cache");
    let isolated_home = compiler_root.join("home");
    fs::create_dir(&isolated_pub_cache)
        .map_err(|error| format!("create isolated Dart pub cache: {error}"))?;
    fs::create_dir(&isolated_home)
        .map_err(|error| format!("create isolated Dart home: {error}"))?;

    let pub_arguments = vec![
        "pub".to_owned(),
        "get".to_owned(),
        "--offline".to_owned(),
        "--enforce-lockfile".to_owned(),
        "--no-precompile".to_owned(),
        "--no-example".to_owned(),
    ];
    let pub_result = dart_process(
        &toolchain,
        pub_arguments.clone(),
        &package_root,
        scratch,
        BindMounts {
            read_only: external_readonly(&toolchain, pub_cache.as_deref()),
            writable: vec![package_root.clone(), compiler_root.clone()],
        },
        NetworkAccess::Disabled,
        compiler_limits(),
        Vec::new(),
        Some(&isolated_pub_cache),
        false,
    )?;
    require_success(
        "Dart offline locked dependency resolution",
        &pub_result,
        scratch,
    )?;
    let lock_after = read_regular(&package_root.join("pubspec.lock"), "resolved Dart lockfile")?;
    let expected_lock: serde_yaml_ng::Value = serde_yaml_ng::from_slice(&compiler_lock)
        .map_err(|error| format!("parse compiler-owned Dart lockfile: {error}"))?;
    let actual_lock: serde_yaml_ng::Value = serde_yaml_ng::from_slice(&lock_after)
        .map_err(|error| format!("parse Dart pub resolved lockfile: {error}"))?;
    if actual_lock != expected_lock {
        return Err("Dart pub changed the compiler-owned enforced dependency graph".to_owned());
    }
    let package_config = package_root.join(".dart_tool/package_config.json");
    let package_config_bytes = read_regular(&package_config, "Dart package configuration")?;
    validate_package_config(config, &resolved, &package_root, &package_config_bytes)?;

    let analyze_arguments = vec![
        "analyze".to_owned(),
        "--fatal-infos".to_owned(),
        path_argument(&package_root, "Dart package")?,
    ];
    let analyzed = dart_process(
        &toolchain,
        analyze_arguments.clone(),
        &compiler_root,
        scratch,
        compiler_binds(&toolchain, &package_root, &compiler_root),
        NetworkAccess::Disabled,
        compiler_limits(),
        Vec::new(),
        Some(&isolated_pub_cache),
        false,
    )?;
    require_success("Dart analyzer", &analyzed, scratch)?;

    let entry_source = compiler_root.join("entry.dart");
    fs::write(&entry_source, compile_entry(config, plan)?.as_bytes())
        .map_err(|error| format!("write Dart facade compilation entry: {error}"))?;
    let module_kernel = compiler_root.join("cott-module.dill");
    let module_depfile = compiler_root.join("cott-module.d");
    let compile_arguments = kernel_arguments(
        &package_config,
        &module_depfile,
        &module_kernel,
        &entry_source,
    )?;
    let compiled = dart_process(
        &toolchain,
        compile_arguments.clone(),
        &compiler_root,
        scratch,
        compiler_binds(&toolchain, &package_root, &compiler_root),
        NetworkAccess::Disabled,
        compiler_limits(),
        Vec::new(),
        Some(&isolated_pub_cache),
        false,
    )?;
    require_success("Dart facade kernel compilation", &compiled, scratch)?;
    let kernel_bytes = read_regular(&module_kernel, "compiled Dart facade kernel")?;
    if kernel_bytes.is_empty() {
        return Err("Dart compiler produced an empty facade kernel".to_owned());
    }
    audit_depfile(&module_depfile, &toolchain, &package_root, &compiler_root)?;

    let runner_root = compiler_root.join("runner");
    fs::create_dir(&runner_root).map_err(|error| format!("create Dart runner scratch: {error}"))?;
    let runner_source = runner_root.join(program.file_name);
    fs::write(&runner_source, program.source.as_bytes())
        .map_err(|error| format!("write bounded Dart runner: {error}"))?;
    for (relative, bytes) in &program.support {
        if !safe_relative(relative) {
            return Err(format!(
                "unsafe Dart compiler support path: {}",
                relative.display()
            ));
        }
        let destination = runner_root.join(relative);
        fs::create_dir_all(
            destination
                .parent()
                .ok_or("Dart compiler support path has no parent")?,
        )
        .map_err(|error| format!("create Dart compiler support directory: {error}"))?;
        fs::write(&destination, bytes)
            .map_err(|error| format!("write Dart compiler support source: {error}"))?;
    }
    let runner_kernel = compiler_root.join("cott-contract-runner.dill");
    let runner_depfile = compiler_root.join("cott-contract-runner.d");
    let runner_compile_arguments = kernel_arguments(
        &package_config,
        &runner_depfile,
        &runner_kernel,
        &runner_source,
    )?;
    let runner_compiled = dart_process(
        &toolchain,
        runner_compile_arguments.clone(),
        &compiler_root,
        scratch,
        compiler_binds(&toolchain, &package_root, &compiler_root),
        NetworkAccess::Disabled,
        compiler_limits(),
        Vec::new(),
        Some(&isolated_pub_cache),
        false,
    )?;
    require_success(
        "Dart contract runner kernel compilation",
        &runner_compiled,
        scratch,
    )?;
    let runner_kernel_bytes = read_regular(&runner_kernel, "compiled Dart contract runner")?;
    if runner_kernel_bytes.is_empty() {
        return Err("Dart compiler produced an empty contract runner kernel".to_owned());
    }
    audit_depfile(&runner_depfile, &toolchain, &package_root, &compiler_root)?;

    let mut evidence_key = [0u8; runner::EVIDENCE_KEY_BYTES];
    getrandom::fill(&mut evidence_key)
        .map_err(|error| format!("generate Dart evidence authentication key: {error}"))?;
    let runtime_arguments = vec![
        "--disable-dart-dev".to_owned(),
        path_argument(&runner_kernel, "Dart contract runner kernel")?,
    ];
    let runtime = dart_process(
        &toolchain,
        runtime_arguments.clone(),
        &compiler_root,
        scratch,
        compiler_binds(&toolchain, &package_root, &compiler_root),
        if program.needs_loopback {
            NetworkAccess::IsolatedLoopback
        } else {
            NetworkAccess::Disabled
        },
        runtime_limits(config, program),
        evidence_key.to_vec(),
        Some(&isolated_pub_cache),
        true,
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
            "bounded Dart contract runner failed with status {:?}: {}",
            runtime.status,
            diagnostics(&runtime)
        ));
    }
    let events = runner::parse_events(&runtime.stdout, &evidence_key);
    evidence_key.fill(0);
    let events = events?;
    validate_events(plan, program, strategies, &events)?;

    verify_file_identities(&inspection.identity_files)?;
    let resolved_after = dependencies::resolve(metadata, pub_cache.as_deref())
        .map_err(|error| format!("re-audit locked Dart dependencies: {error}"))?;
    if resolved.record != resolved_after.record || resolved.artifacts != resolved_after.artifacts {
        return Err("Dart dependency material changed during verification".to_owned());
    }

    let contract_tests = contract_report(plan, strategies, program, &events)?;
    let analyze_command = command_record(&toolchain, &analyze_arguments, scratch, &compiler_root)?;
    let compile_command = command_record(&toolchain, &compile_arguments, scratch, &compiler_root)?;
    let runner_compile_command = command_record(
        &toolchain,
        &runner_compile_arguments,
        scratch,
        &compiler_root,
    )?;
    let pub_command = command_record(&toolchain, &pub_arguments, scratch, &package_root)?;
    let runtime_command = command_record(&toolchain, &runtime_arguments, scratch, &compiler_root)?;
    let report = json!({
        "analysis": {
            "command": analyze_command.clone(),
            "diagnostics": 0,
            "status": "passed",
        },
        "compilation": {
            "artifact": KERNEL_ARTIFACT,
            "artifact_hash": format!("sha256:{}", sha256_hex(&kernel_bytes)),
            "command": compile_command.clone(),
            "depfile": "compiler/cott-module.d",
            "embed_sources": false,
            "runner_command": runner_compile_command.clone(),
            "runner_source_hash": format!("sha256:{}", sha256_hex(program.source.as_bytes())),
            "status": "passed",
        },
        "contract_proofs": contract_proofs,
        "contract_tests": contract_tests,
        "dependencies": resolved.record,
        "limits": {
            "candidate_limit": config.verification.candidate_limit,
            "lifecycle_limit": config.verification.lifecycle_limit,
            "proof_branch_limit": config.verification.proof_branch_limit,
            "proof_node_limit": config.verification.proof_node_limit,
            "scenario_timeout_ms": config.verification.fixtures.scenario_timeout_ms,
        },
        "pub_resolution": {
            "command": pub_command.clone(),
            "lockfile_hash": format!("sha256:{}", sha256_hex(&compiler_lock)),
            "network": "disabled",
            "package_config_hash": format!("sha256:{}", sha256_hex(&package_config_bytes)),
            "status": "passed",
        },
        "runtime_capability": {
            "compilation_only": false,
            "facade_only": true,
            "grade": "runtime check",
            "sandbox": "bubblewrap",
            "filesystem_confinement": {
                "mechanism": "landlock",
                "minimum_abi": 3,
                "applied_before_vm_threads": true,
                "proc_read_allowlist": ["/proc/self/maps"],
            },
            "network": if program.needs_loopback { "isolated_loopback" } else { "disabled" },
            "status": "passed",
        },
    });
    let coverage = crate::cli::semantic_coverage(&report, &config.verification.coverage)?;
    validate_semantic_coverage(&coverage)
        .map_err(|error| format!("invalid Dart semantic coverage: {error}"))?;

    let mut artifacts = resolved.artifacts;
    if artifacts
        .insert(PathBuf::from(KERNEL_ARTIFACT), kernel_bytes)
        .is_some()
    {
        return Err("Dart dependency material collided with the kernel artifact".to_owned());
    }
    let mut tools = inspection.tools;
    tools["compiler_support"] = support_identity;
    tools["commands"] = json!({
        "analyze": analyze_command,
        "compile_kernel": compile_command,
        "compile_runner_kernel": runner_compile_command,
        "pub_get": pub_command,
        "run_kernel": runtime_command,
    });
    tools["runtime_sandbox"] = json!({
        "network": if program.needs_loopback { "isolated_loopback" } else { "disabled" },
        "provider": "bubblewrap",
    });
    tools["required_inputs"] = json!({
        "package_config": format!("sha256:{}", sha256_hex(&package_config_bytes)),
        "runtime_dependencies": resolved.packages.iter().map(|package| package.name.clone()).collect::<Vec<_>>(),
        "support": "private relative crypto 3.0.7 source closure",
    });
    Ok(Verification {
        artifacts,
        tools,
        report,
        coverage,
        dependencies: resolved.record,
    })
}

impl Toolchain {
    fn discover(config: &DartProjectConfig, paths: &DartPaths) -> Result<Self, String> {
        let executable = resolve_executable(&paths.root, &config.dart.sdk, "Dart SDK")?;
        let distribution = executable
            .parent()
            .and_then(Path::parent)
            .ok_or("Dart executable has no SDK distribution root")?
            .to_path_buf();
        let required = [
            executable.clone(),
            distribution.join("version"),
            distribution.join("bin/snapshots/dartdev_aot.dart.snapshot"),
            distribution.join("bin/snapshots/analysis_server_aot.dart.snapshot"),
            distribution.join("bin/snapshots/gen_kernel_aot.dart.snapshot"),
            distribution.join("bin/snapshots/kernel-service.dart.snapshot"),
        ];
        let mut identity_files = BTreeMap::new();
        for path in required {
            identity_files.insert(path.clone(), hash_file(&path)?);
        }
        Ok(Self {
            executable,
            distribution,
            identity_files,
        })
    }

    fn inspect(&self, scratch: &Path) -> Result<ToolInspection, String> {
        let probe_source = scratch.join("dart_identity.dart");
        fs::write(
            &probe_source,
            br#"import 'dart:convert';
import 'dart:ffi';
import 'dart:io';
void main() {
  stdout.write(jsonEncode(<String, Object?>{
    'abi': Abi.current().toString(),
    'executable': Platform.executable,
    'resolved_executable': Platform.resolvedExecutable,
    'operating_system': Platform.operatingSystem,
    'operating_system_version': Platform.operatingSystemVersion,
    'version': Platform.version,
  }));
}
"#,
        )
        .map_err(|error| format!("write Dart identity probe: {error}"))?;
        let process = dart_process(
            self,
            vec![path_argument(&probe_source, "Dart identity probe")?],
            scratch,
            scratch,
            BindMounts {
                read_only: vec![self.distribution.clone()],
                writable: vec![scratch.to_path_buf()],
            },
            NetworkAccess::Disabled,
            probe_limits(),
            Vec::new(),
            None,
            false,
        )?;
        require_success("Dart SDK identity probe", &process, scratch)?;
        let platform: Value = serde_json::from_slice(&process.stdout)
            .map_err(|error| format!("invalid Dart SDK identity probe output: {error}"))?;
        let version = platform
            .get("version")
            .and_then(Value::as_str)
            .and_then(|value| value.split_whitespace().next())
            .ok_or("Dart SDK identity probe omitted version")?
            .to_owned();
        let parsed = parse_version(&version)
            .ok_or_else(|| format!("Dart SDK reported invalid version `{version}`"))?;
        if parsed < MINIMUM_DART || parsed.0 >= MAXIMUM_DART_MAJOR {
            return Err(format!(
                "Dart target requires SDK >=3.13.3,<4.0.0, got `{version}`"
            ));
        }
        let reported = platform
            .get("resolved_executable")
            .and_then(Value::as_str)
            .ok_or("Dart SDK identity probe omitted resolved executable")?;
        let reported = fs::canonicalize(reported)
            .map_err(|error| format!("canonicalize probed Dart executable: {error}"))?;
        if reported != self.executable {
            return Err(format!(
                "Dart SDK identity probe resolved {}, expected {}",
                reported.display(),
                self.executable.display()
            ));
        }
        verify_file_identities(&self.identity_files)?;
        let identities = self
            .identity_files
            .iter()
            .map(|(path, hash)| {
                json!({
                    "path": path.strip_prefix(&self.distribution).unwrap_or(path),
                    "content_hash": hash,
                })
            })
            .collect::<Vec<_>>();
        let distribution_identity = serde_json::to_vec(&identities)
            .map_err(|error| format!("serialize Dart distribution identity: {error}"))?;
        let tools = json!({
            "dart": {
                "content_hash": self.identity_files[&self.executable],
                "distribution": self.distribution,
                "distribution_files": identities,
                "distribution_hash": format!("sha256:{}", sha256_hex(&distribution_identity)),
                "executable": self.executable,
                "platform": platform,
                "version": version,
            },
            "sandbox": {
                "environment": ["CI", "DART_SUPPRESS_ANALYTICS", "HOME", "LC_ALL", "PATH", "PUB_CACHE", "TMPDIR"],
                "network": "disabled",
                "provider": "bubblewrap",
            },
        });
        Ok(ToolInspection {
            tools,
            identity_files: self.identity_files.clone(),
        })
    }
}

fn materialize_package(
    emission: &DartEmission,
    resolved: &ResolvedDependencies,
    root: &Path,
) -> Result<(), String> {
    for (path, bytes) in emission.files.iter().chain(&resolved.artifacts) {
        let Ok(relative) = path.strip_prefix("dart") else {
            continue;
        };
        if !safe_relative(relative) {
            return Err(format!(
                "unsafe emitted Dart package path: {}",
                path.display()
            ));
        }
        let destination = root.join(relative);
        fs::create_dir_all(
            destination
                .parent()
                .ok_or("emitted Dart package path has no parent")?,
        )
        .map_err(|error| format!("create emitted Dart package directory: {error}"))?;
        if destination.exists() {
            return Err(format!(
                "duplicate emitted Dart package path: {}",
                path.display()
            ));
        }
        fs::write(&destination, bytes)
            .map_err(|error| format!("write emitted Dart package {}: {error}", path.display()))?;
    }
    if !root.join("pubspec.yaml").is_file() || !root.join("lib/cott_runtime.dart").is_file() {
        return Err("Dart emission omitted package pubspec or runtime".to_owned());
    }
    Ok(())
}

fn audit_canonical_ir(plan: &DartPlan, emission: &DartEmission) -> Result<(), String> {
    for module in &plan.ir.modules {
        let mut path = PathBuf::from("ir");
        let segments = module.module.segments.as_slice();
        for segment in &segments[..segments.len().saturating_sub(1)] {
            path.push(segment);
        }
        let Some(last) = segments.last() else {
            return Err("canonical Dart module has no name".to_owned());
        };
        path.push(format!("{last}.json"));
        match emission.files.get(&path) {
            Some(bytes) if bytes == &module.bytes => {}
            Some(_) => {
                return Err(format!(
                    "Dart emission canonical IR was tampered: {}",
                    path.display()
                ));
            }
            None => {
                return Err(format!(
                    "Dart emission omitted canonical IR: {}",
                    path.display()
                ));
            }
        }
    }
    Ok(())
}

fn audit_package_sources(root: &Path) -> Result<(), String> {
    let mut pending = vec![root.join("lib")];
    while let Some(directory) = pending.pop() {
        let mut entries = fs::read_dir(&directory)
            .map_err(|error| format!("read Dart source audit directory: {error}"))?
            .collect::<Result<Vec<_>, _>>()
            .map_err(|error| format!("read Dart source audit entry: {error}"))?;
        entries.sort_by_key(fs::DirEntry::file_name);
        for entry in entries {
            let path = entry.path();
            let metadata = fs::symlink_metadata(&path)
                .map_err(|error| format!("stat Dart source audit entry: {error}"))?;
            if metadata.file_type().is_symlink() {
                return Err(format!(
                    "Dart source audit rejects symlink: {}",
                    path.display()
                ));
            }
            if metadata.is_dir() {
                pending.push(path);
                continue;
            }
            if !metadata.is_file() || metadata.nlink() != 1 {
                return Err(format!(
                    "Dart source audit requires regular source: {}",
                    path.display()
                ));
            }
            if path.extension().and_then(|value| value.to_str()) != Some("dart") {
                continue;
            }
            let bytes = read_regular(&path, "Dart source audit input")?;
            let source = std::str::from_utf8(&bytes)
                .map_err(|_| format!("Dart source is not UTF-8: {}", path.display()))?;
            let tree = parse_dart(source)
                .map_err(|error| format!("Dart source audit {}: {error}", path.display()))?;
            if path.starts_with(root.join("lib/src/cott_impl")) {
                audit_private_control_references(tree.root_node(), source, &path)?;
            }
        }
    }
    Ok(())
}

fn audit_private_control_references(
    root: Node<'_>,
    source: &str,
    path: &Path,
) -> Result<(), String> {
    const FORBIDDEN: &[&str] = &[
        "CottObservation",
        "CottClauseObservation",
        "CottObservationStatus",
        "withTestObservation",
        "withTestObservationAsync",
        "recordUnobserved",
        "EvidenceWriter",
        "COTT_DART_VERIFY",
    ];
    let mut pending = vec![root];
    while let Some(node) = pending.pop() {
        if matches!(node.kind(), "identifier" | "type_identifier") {
            let text = source.get(node.byte_range()).unwrap_or_default();
            if FORBIDDEN.contains(&text) || text.starts_with("_cott_verify") {
                let position = node.start_position();
                return Err(format!(
                    "Dart source audit rejects compiler-only control `{text}` at {}:{}:{}",
                    path.display(),
                    position.row + 1,
                    position.column + 1
                ));
            }
        }
        let mut cursor = node.walk();
        pending.extend(node.named_children(&mut cursor));
    }
    Ok(())
}

fn parse_dart(source: &str) -> Result<tree_sitter::Tree, String> {
    let mut parser = Parser::new();
    parser
        .set_language(&tree_sitter_dart::LANGUAGE.into())
        .map_err(|error| format!("load Dart syntax grammar: {error}"))?;
    let tree = parser
        .parse(source.as_bytes(), None)
        .ok_or("Dart syntax parser returned no tree")?;
    if tree.root_node().has_error() {
        return Err("malformed Dart syntax".to_owned());
    }
    Ok(tree)
}

fn compile_entry(config: &DartProjectConfig, plan: &DartPlan) -> Result<String, String> {
    let mut source = String::new();
    for (index, module) in plan.modules.iter().enumerate() {
        if module.name.split('.').any(|segment| segment.is_empty()) {
            return Err(format!("invalid Dart module name `{}`", module.name));
        }
        writeln!(
            source,
            "import 'package:{}/modules/{}.dart' as module_{index};",
            config.project.name,
            module.name.replace('.', "/")
        )
        .expect("writing to String cannot fail");
    }
    source.push_str("\nvoid main() {}\n");
    Ok(source)
}

fn kernel_arguments(
    package_config: &Path,
    depfile: &Path,
    output: &Path,
    entry: &Path,
) -> Result<Vec<String>, String> {
    Ok(vec![
        "compile".to_owned(),
        "kernel".to_owned(),
        format!(
            "--packages={}",
            path_argument(package_config, "Dart package configuration")?
        ),
        format!(
            "--depfile={}",
            path_argument(depfile, "Dart kernel depfile")?
        ),
        "--no-embed-sources".to_owned(),
        format!("--output={}", path_argument(output, "Dart kernel output")?),
        path_argument(entry, "Dart kernel entry")?,
    ])
}

fn validate_package_config(
    config: &DartProjectConfig,
    resolved: &ResolvedDependencies,
    package_root: &Path,
    bytes: &[u8],
) -> Result<(), String> {
    let document: Value = serde_json::from_slice(bytes)
        .map_err(|error| format!("invalid Dart package_config.json: {error}"))?;
    if document.get("configVersion").and_then(Value::as_u64) != Some(2) {
        return Err("Dart package_config.json must use configVersion 2".to_owned());
    }
    let packages = document
        .get("packages")
        .and_then(Value::as_array)
        .ok_or("Dart package_config.json packages is not an array")?;
    let expected = std::iter::once(config.project.name.as_str())
        .chain(
            resolved
                .packages
                .iter()
                .map(|package| package.name.as_str()),
        )
        .collect::<BTreeSet<_>>();
    let mut actual = BTreeSet::new();
    for package in packages {
        let name = package
            .get("name")
            .and_then(Value::as_str)
            .ok_or("Dart package_config entry has no name")?;
        if !actual.insert(name) {
            return Err(format!("Dart package_config duplicates package `{name}`"));
        }
        let root_uri = package
            .get("rootUri")
            .and_then(Value::as_str)
            .ok_or_else(|| format!("Dart package_config package `{name}` has no rootUri"))?;
        if root_uri.contains('%')
            || root_uri.contains('\\')
            || root_uri.contains(':')
            || Path::new(root_uri).is_absolute()
        {
            return Err(format!(
                "Dart package_config package `{name}` has unsafe rootUri"
            ));
        }
        let actual_root = fs::canonicalize(package_root.join(".dart_tool").join(root_uri))
            .map_err(|error| {
                format!("canonicalize Dart package_config package `{name}` root: {error}")
            })?;
        let expected_root = if name == config.project.name {
            package_root.to_path_buf()
        } else {
            package_root.join("vendor").join(name)
        };
        if actual_root != expected_root {
            return Err(format!(
                "Dart package_config package `{name}` resolves outside its verified ownership root"
            ));
        }
        if package.get("packageUri").and_then(Value::as_str) != Some("lib/") {
            return Err(format!(
                "Dart package_config package `{name}` has non-library packageUri"
            ));
        }
    }
    if actual != expected {
        return Err(format!(
            "Dart package_config ownership mismatch: expected {:?}, got {:?}",
            expected, actual
        ));
    }
    Ok(())
}

fn audit_depfile(
    path: &Path,
    toolchain: &Toolchain,
    package_root: &Path,
    compiler_root: &Path,
) -> Result<(), String> {
    let bytes = read_regular(path, "Dart kernel depfile")?;
    let text = std::str::from_utf8(&bytes).map_err(|_| "Dart kernel depfile is not UTF-8")?;
    let (_, inputs) = text
        .split_once(':')
        .ok_or("Dart kernel depfile has no target separator")?;
    let inputs = split_depfile_paths(inputs)?;
    if inputs.is_empty() {
        return Err("Dart kernel depfile has no source inputs".to_owned());
    }
    for input in inputs {
        let input = PathBuf::from(input);
        let path = if input.is_absolute() {
            input
        } else {
            compiler_root.join(input)
        };
        let canonical = fs::canonicalize(&path).map_err(|error| {
            format!(
                "canonicalize Dart kernel depfile input {}: {error}",
                path.display()
            )
        })?;
        if !canonical.starts_with(&toolchain.distribution)
            && !canonical.starts_with(package_root)
            && !canonical.starts_with(compiler_root)
        {
            return Err(format!(
                "Dart compiler consumed source outside verified roots: {}",
                canonical.display()
            ));
        }
        let metadata = fs::symlink_metadata(&canonical)
            .map_err(|error| format!("stat Dart kernel depfile input: {error}"))?;
        if !metadata.is_file() || metadata.nlink() != 1 {
            return Err(format!(
                "Dart compiler input is not a single-link regular file: {}",
                canonical.display()
            ));
        }
    }
    Ok(())
}

fn split_depfile_paths(value: &str) -> Result<Vec<String>, String> {
    let mut paths = Vec::new();
    let mut current = String::new();
    let mut escaped = false;
    for character in value.trim().chars() {
        if escaped {
            current.push(character);
            escaped = false;
        } else if character == '\\' {
            escaped = true;
        } else if character.is_whitespace() {
            if !current.is_empty() {
                paths.push(std::mem::take(&mut current));
            }
        } else {
            current.push(character);
        }
    }
    if escaped {
        return Err("Dart kernel depfile ends with an escape".to_owned());
    }
    if !current.is_empty() {
        paths.push(current);
    }
    Ok(paths)
}

fn validate_events(
    plan: &DartPlan,
    program: &RunnerProgram,
    strategies: &[ContractTestStrategy],
    events: &[Value],
) -> Result<(), String> {
    let mut expected_clauses = BTreeSet::new();
    for (symbol, clause) in coverage_inventory(plan, strategies)? {
        for alias in observation_aliases(plan, &symbol) {
            expected_clauses.insert((alias, clause.clone()));
        }
    }
    for declaration in plan
        .modules
        .iter()
        .flat_map(|module| &module.declarations)
        .filter(|declaration| {
            declaration.get("public").and_then(Value::as_bool) == Some(true)
                && declaration.get("kind").and_then(Value::as_str) == Some("newtype")
                && declaration
                    .get("refinement")
                    .is_some_and(|value| !value.is_null())
        })
    {
        if let Some(symbol) = declaration.get("name").and_then(Value::as_str) {
            expected_clauses.insert((symbol.to_owned(), "refinement".to_owned()));
        }
    }
    let mut seen_cases = BTreeSet::new();
    let mut seen_cancellations = BTreeSet::new();
    let mut seen_scenarios = BTreeSet::new();
    let mut done = 0usize;
    for (index, event) in events.iter().enumerate() {
        match event.get("kind").and_then(Value::as_str) {
            Some("done") => {
                exact_event_fields(event, &["kind"], "completion")?;
                if index + 1 != events.len() {
                    return Err("Dart runner completion marker was not the final event".to_owned());
                }
                done += 1;
            }
            Some("case") => {
                exact_event_fields(
                    event,
                    &[
                        "kind",
                        "symbol",
                        "case",
                        "status",
                        "phase",
                        "clause",
                        "error_symbol",
                        "observations",
                    ],
                    "case",
                )?;
                validate_optional_event_strings(
                    event,
                    &["phase", "clause", "error_symbol"],
                    "Dart case",
                )?;
                let symbol = required_event_string(event, "symbol")?;
                let case = required_event_u32(event, "case")?;
                let expected = program.expected_cases.get(symbol).ok_or_else(|| {
                    format!("Dart contract runner emitted an unknown case for `{symbol}`")
                })?;
                if case >= *expected || !seen_cases.insert((symbol.to_owned(), case)) {
                    return Err(format!(
                        "Dart contract runner emitted a duplicate or out-of-range case for `{symbol}`"
                    ));
                }
                let observations = validate_observations(event, &expected_clauses, "Dart case")?;
                let status = required_event_string(event, "status")?;
                match status {
                    "passed" => {
                        if observations.iter().any(|observation| {
                            observation.get("passed").and_then(Value::as_bool) == Some(false)
                        }) {
                            return Err(format!(
                                "Dart runtime reported a failed clause without rejecting `{symbol}`"
                            ));
                        }
                        require_null_event_fields(
                            event,
                            &["phase", "clause", "error_symbol"],
                            "passed Dart case",
                        )?;
                    }
                    "ineligible" => {
                        if event.get("phase").and_then(Value::as_str) != Some("requires")
                            || !observations.iter().any(|observation| {
                                observation.get("phase").and_then(Value::as_str) == Some("requires")
                                    && observation.get("passed").and_then(Value::as_bool)
                                        == Some(false)
                            })
                        {
                            return Err(format!(
                                "Dart runner marked `{symbol}` ineligible without a failed requires observation"
                            ));
                        }
                    }
                    "candidate_unavailable" => {
                        if event.get("phase").and_then(Value::as_str).is_none()
                            || !observations.iter().any(|observation| {
                                observation.get("passed").and_then(Value::as_bool) == Some(false)
                            })
                        {
                            return Err(format!(
                                "Dart runner marked `{symbol}` candidate unavailable without an observed construction failure"
                            ));
                        }
                    }
                    "failed" | "timeout" | "unexpected_cancellation" | "unexpected_exception" => {
                        return Err(format!(
                            "Dart contract execution failed for `{symbol}` case {case} ({status})"
                        ));
                    }
                    other => {
                        return Err(format!("Dart runner emitted unknown case status `{other}`"));
                    }
                }
            }
            Some("cancellation") => {
                exact_event_fields(
                    event,
                    &[
                        "kind",
                        "symbol",
                        "case",
                        "status",
                        "cooperative",
                        "future_preempted",
                        "reason",
                    ],
                    "cancellation",
                )?;
                let symbol = required_event_string(event, "symbol")?;
                let case = required_event_u32(event, "case")?;
                let key = (symbol.to_owned(), case);
                if !program.expected_cancellations.contains(&key) || !seen_cancellations.insert(key)
                {
                    return Err(format!(
                        "Dart runner emitted duplicate or unknown cancellation evidence for `{symbol}`"
                    ));
                }
                let reason = required_event_string(event, "reason")?;
                if required_event_string(event, "status")? != "passed"
                    || event.get("cooperative").and_then(Value::as_bool) != Some(true)
                    || event.get("future_preempted").and_then(Value::as_bool) != Some(false)
                    || reason.is_empty()
                {
                    return Err(format!(
                        "Dart cancellation evidence for `{symbol}` does not prove cooperative observation without Future preemption"
                    ));
                }
            }
            Some("scenario") => {
                exact_event_fields(
                    event,
                    &[
                        "kind",
                        "scenario_id",
                        "symbol",
                        "status",
                        "assertions",
                        "cancellations",
                        "cleaned",
                        "observations",
                    ],
                    "scenario",
                )?;
                let id = required_event_string(event, "scenario_id")?;
                let expectation = program
                    .expected_scenarios
                    .get(id)
                    .ok_or_else(|| format!("Dart runner emitted unknown scenario `{id}`"))?;
                if !seen_scenarios.insert(id.to_owned()) {
                    return Err(format!("Dart runner emitted duplicate scenario `{id}`"));
                }
                if required_event_string(event, "symbol")? != expectation.symbol.as_str()
                    || required_event_u32(event, "assertions")? != expectation.assertions
                    || required_event_u32(event, "cancellations")? != expectation.cancellations
                    || event.get("cleaned").and_then(Value::as_bool) != Some(true)
                {
                    return Err(format!(
                        "Dart scenario `{id}` evidence does not match its finite plan or cleanup"
                    ));
                }
                let observations =
                    validate_observations(event, &expected_clauses, "Dart scenario")?;
                if required_event_string(event, "status")? != "passed"
                    || observations.iter().any(|observation| {
                        observation.get("passed").and_then(Value::as_bool) == Some(false)
                    })
                {
                    return Err(format!("Dart scenario `{id}` failed"));
                }
            }
            Some(other) => return Err(format!("Dart runner emitted unknown event `{other}`")),
            None => return Err("Dart contract runner event has no kind".to_owned()),
        }
    }
    if done != 1 {
        return Err("Dart contract runner completion marker is missing or duplicated".to_owned());
    }
    for (symbol, count) in &program.expected_cases {
        for case in 0..*count {
            if !seen_cases.contains(&(symbol.clone(), case)) {
                return Err(format!(
                    "Dart contract runner omitted `{symbol}` case {case}"
                ));
            }
        }
    }
    if seen_cancellations != program.expected_cancellations {
        return Err("Dart contract runner omitted cooperative cancellation evidence".to_owned());
    }
    if seen_scenarios
        != program
            .expected_scenarios
            .keys()
            .cloned()
            .collect::<BTreeSet<_>>()
    {
        return Err("Dart contract runner omitted an enforceable scenario".to_owned());
    }
    Ok(())
}

fn exact_event_fields(event: &Value, expected: &[&str], kind: &str) -> Result<(), String> {
    let object = event
        .as_object()
        .ok_or_else(|| format!("Dart {kind} event is not an object"))?;
    let actual = object.keys().map(String::as_str).collect::<BTreeSet<_>>();
    let expected = expected.iter().copied().collect::<BTreeSet<_>>();
    if actual != expected {
        return Err(format!("Dart {kind} event has unexpected fields"));
    }
    Ok(())
}

fn require_null_event_fields(event: &Value, fields: &[&str], context: &str) -> Result<(), String> {
    if fields
        .iter()
        .any(|field| event.get(*field).is_none_or(|value| !value.is_null()))
    {
        return Err(format!("{context} has unexpected error metadata"));
    }
    Ok(())
}

fn validate_optional_event_strings(
    event: &Value,
    fields: &[&str],
    context: &str,
) -> Result<(), String> {
    if fields.iter().any(|field| {
        event
            .get(*field)
            .is_none_or(|value| !value.is_null() && !value.is_string())
    }) {
        return Err(format!("{context} has malformed error metadata"));
    }
    Ok(())
}

fn validate_observations<'a>(
    event: &'a Value,
    expected_clauses: &BTreeSet<(String, String)>,
    context: &str,
) -> Result<&'a [Value], String> {
    let observations = event
        .get("observations")
        .and_then(Value::as_array)
        .ok_or_else(|| format!("{context} observations are not an array"))?;
    let mut seen = BTreeMap::new();
    for observation in observations {
        exact_event_fields(
            observation,
            &["symbol", "clause", "phase", "status", "passed", "reason"],
            "clause observation",
        )?;
        let symbol = required_event_string(observation, "symbol")?;
        let clause = required_event_string(observation, "clause")?;
        let phase = required_event_string(observation, "phase")?;
        if !expected_clauses
            .iter()
            .any(|(expected_symbol, expected_clause)| {
                expected_symbol == symbol && expected_clause == clause
            })
        {
            return Err(format!(
                "Dart runner emitted unknown clause observation `{symbol}:{clause}`"
            ));
        }
        let status = required_event_string(observation, "status")?;
        let passed = observation.get("passed").unwrap_or(&Value::Null);
        match status {
            "passed" if passed == &Value::Bool(true) => {
                if observation
                    .get("reason")
                    .is_none_or(|reason| !reason.is_null())
                {
                    return Err("Dart passed clause observation has a reason".to_owned());
                }
            }
            "failed" if passed == &Value::Bool(false) => {
                if observation
                    .get("reason")
                    .is_none_or(|reason| !reason.is_null())
                {
                    return Err("Dart failed clause observation has a reason".to_owned());
                }
            }
            "unobserved" if passed.is_null() => {
                if observation
                    .get("reason")
                    .and_then(Value::as_str)
                    .is_none_or(str::is_empty)
                {
                    return Err("Dart unobserved clause has no reason".to_owned());
                }
            }
            _ => {
                return Err("Dart clause observation status/passed fields disagree".to_owned());
            }
        }
        if let Some(prior) = seen.insert((symbol, clause, phase), status)
            && prior != status
        {
            return Err(format!(
                "Dart runner emitted contradictory clause observations `{symbol}:{clause}:{phase}`"
            ));
        }
    }
    Ok(observations)
}

fn contract_report(
    plan: &DartPlan,
    strategies: &[ContractTestStrategy],
    program: &RunnerProgram,
    events: &[Value],
) -> Result<Value, String> {
    let case_events = events
        .iter()
        .filter(|event| event.get("kind").and_then(Value::as_str) == Some("case"))
        .collect::<Vec<_>>();
    let scenario_events = events
        .iter()
        .filter(|event| event.get("kind").and_then(Value::as_str) == Some("scenario"))
        .collect::<Vec<_>>();
    let mut passed_cases = BTreeMap::<String, u64>::new();
    let mut ineligible_cases = BTreeMap::<String, u64>::new();
    let mut unavailable_cases = BTreeMap::<String, u64>::new();
    for event in &case_events {
        let symbol = required_event_string(event, "symbol")?.to_owned();
        match required_event_string(event, "status")? {
            "passed" => *passed_cases.entry(symbol).or_default() += 1,
            "ineligible" => *ineligible_cases.entry(symbol).or_default() += 1,
            "candidate_unavailable" => {
                *unavailable_cases.entry(symbol).or_default() += 1;
            }
            _ => {}
        }
    }
    let mut contracts = Vec::new();
    for (symbol, clause_id) in coverage_inventory(plan, strategies)? {
        let span = clause_span(plan, &symbol, &clause_id)?;
        let guarded = clause_is_guarded(plan, &symbol, &clause_id);
        let aliases = observation_aliases(plan, &symbol);
        let mut phases = BTreeSet::new();
        let mut valid_cases = BTreeSet::new();
        let mut valid_scenarios = BTreeSet::new();
        for event in &case_events {
            if event.get("status").and_then(Value::as_str) != Some("passed") {
                continue;
            }
            for observation in event
                .get("observations")
                .and_then(Value::as_array)
                .ok_or("Dart case observations are not an array")?
            {
                let observed_symbol = observation
                    .get("symbol")
                    .and_then(Value::as_str)
                    .ok_or("Dart clause observation has no symbol")?;
                if aliases.contains(observed_symbol)
                    && observation.get("clause").and_then(Value::as_str) == Some(clause_id.as_str())
                    && observation.get("passed").and_then(Value::as_bool) == Some(true)
                {
                    phases.insert(
                        observation
                            .get("phase")
                            .and_then(Value::as_str)
                            .unwrap_or("contract")
                            .to_owned(),
                    );
                    valid_cases.insert((
                        required_event_string(event, "symbol")?.to_owned(),
                        required_event_u32(event, "case")?,
                    ));
                }
            }
        }
        for event in &scenario_events {
            if event.get("status").and_then(Value::as_str) != Some("passed") {
                continue;
            }
            for observation in event
                .get("observations")
                .and_then(Value::as_array)
                .ok_or("Dart scenario observations are not an array")?
            {
                let observed_symbol = observation
                    .get("symbol")
                    .and_then(Value::as_str)
                    .ok_or("Dart scenario clause observation has no symbol")?;
                if aliases.contains(observed_symbol)
                    && observation.get("clause").and_then(Value::as_str) == Some(clause_id.as_str())
                    && observation.get("passed").and_then(Value::as_bool) == Some(true)
                {
                    phases.insert(
                        observation
                            .get("phase")
                            .and_then(Value::as_str)
                            .unwrap_or("contract")
                            .to_owned(),
                    );
                    valid_scenarios.insert(required_event_string(event, "scenario_id")?.to_owned());
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
            let reason = if let Some(reason) = program.unavailable.get(&symbol) {
                reason.clone()
            } else if guarded {
                "runtime clause hook does not expose whether a guarded clause was positively applicable".to_owned()
            } else if clause_id.starts_with("error:") {
                "individual Result error branch was not reached by a positive applicable case"
                    .to_owned()
            } else if clause_id.starts_with("modifies:") {
                "a modifies permission is not itself evidence of a state mutation".to_owned()
            } else if passed_cases.get(&symbol).copied().unwrap_or(0) == 0
                && ineligible_cases.get(&symbol).copied().unwrap_or(0) > 0
            {
                "no bounded candidate satisfied every requires clause".to_owned()
            } else if passed_cases.get(&symbol).copied().unwrap_or(0) == 0
                && unavailable_cases.get(&symbol).copied().unwrap_or(0) > 0
            {
                "no bounded candidate could be constructed by the public facade".to_owned()
            } else if matches!(
                plan.modules
                    .iter()
                    .flat_map(|module| &module.declarations)
                    .find(|declaration| {
                        declaration.get("name").and_then(Value::as_str) == Some(symbol.as_str())
                    })
                    .and_then(|declaration| declaration.get("kind"))
                    .and_then(Value::as_str),
                Some("newtype" | "struct")
            ) {
                "no bounded public consumer constructed this nominal type".to_owned()
            } else {
                return Err(format!(
                    "Dart runtime produced no positive applicable evidence for observable clause `{symbol}:{clause_id}`"
                ));
            };
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
            "symbol": symbol,
        }));
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
    let strategy_values = strategies
        .iter()
        .map(serde_json::to_value)
        .collect::<Result<Vec<_>, _>>()
        .map_err(|error| format!("serialize Dart contract strategy: {error}"))?;
    Ok(json!({
        "cases": cases,
        "contracts": contracts,
        "lifecycle": lifecycle,
        "observation_inventory": {
            "cases": cases.len(),
            "clauses": contracts.len(),
            "lifecycle": lifecycle.len(),
            "scenarios": scenarios.len(),
            "strategies": strategies.len(),
            "status": if strategies.is_empty() && contracts.is_empty() { "not_applicable" } else { "executed" },
        },
        "scenarios": scenarios,
        "strategies": strategy_values,
        "unavailable": program.unavailable,
    }))
}

fn coverage_inventory(
    plan: &DartPlan,
    strategies: &[ContractTestStrategy],
) -> Result<Vec<(String, String)>, String> {
    let mut inventory = strategies
        .iter()
        .flat_map(|strategy| {
            strategy
                .clause_ids
                .iter()
                .map(|clause| (strategy.symbol.clone(), clause.clone()))
        })
        .collect::<Vec<_>>();
    for declaration in plan
        .modules
        .iter()
        .flat_map(|module| &module.declarations)
        .filter(|declaration| declaration.get("public").and_then(Value::as_bool) == Some(true))
    {
        let Some(symbol) = declaration.get("name").and_then(Value::as_str) else {
            continue;
        };
        match declaration.get("kind").and_then(Value::as_str) {
            Some("struct") => {
                for invariant in declaration
                    .get("invariants")
                    .and_then(Value::as_array)
                    .into_iter()
                    .flatten()
                {
                    let clause = invariant
                        .get("clause_id")
                        .and_then(Value::as_u64)
                        .ok_or_else(|| {
                            format!("Dart struct `{symbol}` invariant has no clause_id")
                        })?;
                    inventory.push((symbol.to_owned(), format!("invariant:{clause}")));
                }
            }
            _ => {}
        }
    }
    inventory.sort_by(|left, right| {
        coverage_key(&left.0, &left.1).cmp(&coverage_key(&right.0, &right.1))
    });
    inventory.dedup();
    Ok(inventory)
}

fn clause_is_guarded(plan: &DartPlan, symbol: &str, clause_id: &str) -> bool {
    let Some((kind, id)) = clause_id.split_once(':') else {
        return false;
    };
    let Ok(id) = id.parse::<u64>() else {
        return false;
    };
    if kind == "modifies" {
        return false;
    }
    if let Some(callable) = plan
        .callables()
        .iter()
        .find(|callable| callable.symbol == symbol)
    {
        if find_guarded_clause(&callable.declaration, kind, id) {
            return true;
        }
        return kind == "invariant"
            && callable
                .owner
                .as_ref()
                .and_then(|owner| owner.get("invariants"))
                .is_some_and(|value| find_guarded_clause(value, kind, id));
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

fn clause_span(plan: &DartPlan, symbol: &str, clause_id: &str) -> Result<Value, String> {
    if clause_id == "refinement" {
        return plan
            .modules
            .iter()
            .flat_map(|module| &module.declarations)
            .find(|declaration| {
                declaration.get("name").and_then(Value::as_str) == Some(symbol)
                    && declaration.get("kind").and_then(Value::as_str) == Some("newtype")
            })
            .and_then(|declaration| declaration.pointer("/refinement/span"))
            .cloned()
            .ok_or_else(|| format!("no Dart newtype span owns `{symbol}:{clause_id}`"));
    }
    let (kind, id) = clause_id
        .split_once(':')
        .ok_or_else(|| format!("invalid Dart clause ID `{symbol}:{clause_id}`"))?;
    if kind == "modifies" {
        return plan
            .callables()
            .iter()
            .find(|callable| callable.symbol == symbol)
            .and_then(|callable| callable.declaration.get("span"))
            .cloned()
            .ok_or_else(|| format!("no Dart callable span owns `{symbol}:{clause_id}`"));
    }
    let numeric = id
        .parse::<u64>()
        .map_err(|_| format!("invalid Dart clause ID `{symbol}:{clause_id}`"))?;
    let owner_symbol = symbol.strip_suffix(".init").unwrap_or(symbol);
    let callable = plan
        .callables()
        .iter()
        .find(|callable| callable.symbol == symbol);
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
            "canonical Dart clause `{symbol}:{clause_id}` has no source span"
        )),
        _ => Err(format!(
            "canonical Dart clause `{symbol}:{clause_id}` has ambiguous source spans"
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
            if matches && let Some(span) = object.get("span") {
                candidates.push(span.clone());
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

fn observation_aliases(plan: &DartPlan, symbol: &str) -> BTreeSet<String> {
    let mut aliases = BTreeSet::from([symbol.to_owned()]);
    if let Some(owner) = symbol.strip_suffix(".init") {
        aliases.insert(owner.to_owned());
    }
    if let Some(owner) = plan
        .callables()
        .iter()
        .find(|callable| callable.symbol == symbol)
        .and_then(|callable| callable.owner.as_ref())
        .and_then(|owner| owner.get("name"))
        .and_then(Value::as_str)
    {
        aliases.insert(owner.to_owned());
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

fn required_event_string<'a>(event: &'a Value, field: &str) -> Result<&'a str, String> {
    event
        .get(field)
        .and_then(Value::as_str)
        .ok_or_else(|| format!("Dart evidence field `{field}` is not a string"))
}

fn required_event_u32(event: &Value, field: &str) -> Result<u32, String> {
    event
        .get(field)
        .and_then(Value::as_u64)
        .and_then(|value| u32::try_from(value).ok())
        .ok_or_else(|| format!("Dart evidence field `{field}` is not u32"))
}

fn configured_pub_cache() -> Result<Option<PathBuf>, String> {
    let Some(value) = std::env::var_os("PUB_CACHE") else {
        return Ok(None);
    };
    let path = PathBuf::from(value);
    if !path.is_absolute() {
        return Err("PUB_CACHE must be an absolute path for Dart verification".to_owned());
    }
    let canonical = fs::canonicalize(&path)
        .map_err(|error| format!("canonicalize PUB_CACHE {}: {error}", path.display()))?;
    if canonical != path || !canonical.is_dir() {
        return Err("PUB_CACHE must name a canonical real directory".to_owned());
    }
    Ok(Some(canonical))
}

fn resolve_executable(root: &Path, configured: &str, label: &str) -> Result<PathBuf, String> {
    if configured.is_empty() || configured.contains('\0') {
        return Err(format!("{label} executable is empty or contains NUL"));
    }
    let configured_path = Path::new(configured);
    let candidate = if configured_path.components().count() > 1 {
        if configured_path.is_absolute() {
            configured_path.to_path_buf()
        } else {
            root.join(configured_path)
        }
    } else {
        std::env::var_os("PATH")
            .into_iter()
            .flat_map(|path| std::env::split_paths(&path).collect::<Vec<_>>())
            .map(|directory| directory.join(configured_path))
            .find(|path| path.is_file())
            .ok_or_else(|| format!("cannot find {label} executable `{configured}` on PATH"))?
    };
    let canonical = fs::canonicalize(&candidate).map_err(|error| {
        format!(
            "canonicalize {label} executable {}: {error}",
            candidate.display()
        )
    })?;
    let metadata = fs::symlink_metadata(&canonical)
        .map_err(|error| format!("stat {label} executable {}: {error}", canonical.display()))?;
    if !metadata.is_file() || metadata.nlink() != 1 || metadata.permissions().mode() & 0o111 == 0 {
        return Err(format!(
            "{label} must be an executable single-link regular file"
        ));
    }
    Ok(canonical)
}

fn command_record(
    toolchain: &Toolchain,
    arguments: &[String],
    scratch: &Path,
    cwd: &Path,
) -> Result<Value, String> {
    let scratch_text = path_argument(scratch, "Dart scratch")?;
    let sanitize = |value: &str| value.replace(scratch_text.as_str(), "<scratch>");
    let path = std::env::join_paths([
        toolchain.distribution.join("bin"),
        PathBuf::from("/usr/bin"),
        PathBuf::from("/bin"),
    ])
    .map_err(|error| format!("construct reported sanitized Dart PATH: {error}"))?;
    Ok(json!({
        "arguments": arguments
            .iter()
            .map(|argument| sanitize(argument))
            .collect::<Vec<_>>(),
        "cwd": sanitize(&path_argument(cwd, "Dart command cwd")?),
        "environment": {
            "CI": "true",
            "DART_SUPPRESS_ANALYTICS": "true",
            "HOME": "<scratch>/compiler/home",
            "LC_ALL": "C.UTF-8",
            "PATH": path.to_string_lossy(),
            "PUB_CACHE": "<scratch>/compiler/pub-cache",
            "TMPDIR": "<scratch>",
        },
        "executable": toolchain.executable,
        "network": "disabled",
    }))
}

fn dart_process(
    toolchain: &Toolchain,
    arguments: Vec<String>,
    cwd: &Path,
    scratch: &Path,
    mut binds: BindMounts,
    network: NetworkAccess,
    limits: ResourceLimits,
    stdin: Vec<u8>,
    pub_cache: Option<&Path>,
    confine_process_filesystem: bool,
) -> Result<crate::sandbox::CompletedProcess, String> {
    let path = std::env::join_paths([
        toolchain.distribution.join("bin"),
        PathBuf::from("/usr/bin"),
        PathBuf::from("/bin"),
    ])
    .map_err(|error| format!("construct sanitized Dart PATH: {error}"))?;
    let home = scratch.join("compiler/home");
    let cache = pub_cache.unwrap_or_else(|| Path::new("/tmp"));
    let environment = BTreeMap::from([
        ("CI".to_owned(), "true".to_owned()),
        ("DART_SUPPRESS_ANALYTICS".to_owned(), "true".to_owned()),
        ("HOME".to_owned(), path_argument(&home, "Dart HOME")?),
        ("LC_ALL".to_owned(), "C.UTF-8".to_owned()),
        ("PATH".to_owned(), path.to_string_lossy().into_owned()),
        (
            "PUB_CACHE".to_owned(),
            path_argument(cache, "Dart PUB_CACHE")?,
        ),
        (
            "TMPDIR".to_owned(),
            path_argument(
                if confine_process_filesystem {
                    cwd
                } else {
                    scratch
                },
                "Dart scratch",
            )?,
        ),
    ]);
    let (program, arguments) = if confine_process_filesystem {
        let launcher = std::fs::canonicalize(
            std::env::current_exe()
                .map_err(|error| format!("locate confinement launcher: {error}"))?,
        )
        .map_err(|error| format!("resolve confinement launcher: {error}"))?;
        let launch = crate::sandbox::landlock::ConfinedExec {
            executable: toolchain.executable.clone(),
            arguments,
            read_only: binds.read_only.clone(),
            writable: binds.writable.clone(),
        };
        let encoded = serde_json::to_string(&launch)
            .map_err(|error| format!("encode confined Dart invocation: {error}"))?;
        binds.read_only.push(launcher.clone());
        (
            launcher,
            vec![crate::sandbox::landlock::EXEC_MODE.to_owned(), encoded],
        )
    } else {
        (toolchain.executable.clone(), arguments)
    };
    run(&SandboxSpec {
        program,
        arguments,
        cwd: cwd.to_path_buf(),
        environment,
        stdin,
        binds,
        network,
        limits,
    })
    .map_err(|error| format!("sandboxed Dart tool execution failed: {error}"))
}

fn external_readonly(toolchain: &Toolchain, pub_cache: Option<&Path>) -> Vec<PathBuf> {
    let mut inputs = vec![toolchain.distribution.clone()];
    if let Some(cache) = pub_cache {
        inputs.push(cache.to_path_buf());
    }
    inputs
}

fn compiler_binds(toolchain: &Toolchain, package: &Path, compiler: &Path) -> BindMounts {
    BindMounts {
        read_only: vec![toolchain.distribution.clone(), package.to_path_buf()],
        writable: vec![compiler.to_path_buf()],
    }
}

fn probe_limits() -> ResourceLimits {
    ResourceLimits {
        cpu_time: Duration::from_secs(15),
        address_space_bytes: 2 * 1024 * 1024 * 1024,
        process_count: DART_PROCESS_ALLOWANCE,
        open_files: 128,
        file_size_bytes: 8 * 1024 * 1024,
        wall_time: Duration::from_secs(20),
        stream_limit_bytes: 1024 * 1024,
        writable_bytes: 16 * 1024 * 1024,
    }
}

fn compiler_limits() -> ResourceLimits {
    ResourceLimits {
        cpu_time: Duration::from_secs(90),
        address_space_bytes: 4 * 1024 * 1024 * 1024,
        process_count: DART_PROCESS_ALLOWANCE,
        open_files: 256,
        file_size_bytes: 128 * 1024 * 1024,
        wall_time: Duration::from_secs(120),
        stream_limit_bytes: 4 * 1024 * 1024,
        writable_bytes: 256 * 1024 * 1024,
    }
}

fn runtime_limits(config: &DartProjectConfig, program: &RunnerProgram) -> ResourceLimits {
    let cases = program
        .expected_cases
        .values()
        .map(|value| u64::from(*value))
        .sum::<u64>();
    let scenarios = program
        .expected_scenarios
        .values()
        .map(|scenario| u64::from(scenario.cancellations).saturating_add(1))
        .sum::<u64>();
    let work_units = cases.saturating_add(scenarios).max(1);
    let configured_ms = u64::from(config.verification.fixtures.scenario_timeout_ms)
        .saturating_mul(work_units)
        .clamp(5_000, 120_000);
    ResourceLimits {
        cpu_time: Duration::from_millis(configured_ms),
        address_space_bytes: 2 * 1024 * 1024 * 1024,
        process_count: DART_PROCESS_ALLOWANCE,
        open_files: 128,
        file_size_bytes: 16 * 1024 * 1024,
        wall_time: Duration::from_millis(configured_ms.saturating_add(5_000)),
        stream_limit_bytes: 4 * 1024 * 1024,
        writable_bytes: 32 * 1024 * 1024,
    }
}

fn require_success(
    label: &str,
    process: &crate::sandbox::CompletedProcess,
    scratch: &Path,
) -> Result<(), String> {
    if process.status == Some(0) && !process.timed_out {
        return Ok(());
    }
    let scratch_text = scratch.to_string_lossy();
    let details = diagnostics(process).replace(scratch_text.as_ref(), "<scratch>");
    Err(format!(
        "{label} failed with status {:?}: {details}",
        process.status
    ))
}

fn diagnostics(process: &crate::sandbox::CompletedProcess) -> String {
    let mut output = String::from_utf8_lossy(&process.stdout).into_owned();
    if !output.is_empty() && !process.stderr.is_empty() {
        output.push('\n');
    }
    output.push_str(&String::from_utf8_lossy(&process.stderr));
    output
        .lines()
        .take(MAX_DIAGNOSTICS)
        .collect::<Vec<_>>()
        .join("\n")
}

fn hash_file(path: &Path) -> Result<String, String> {
    let mut file = OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_NOFOLLOW | libc::O_NONBLOCK | libc::O_CLOEXEC)
        .open(path)
        .map_err(|error| format!("open Dart SDK identity file {}: {error}", path.display()))?;
    let metadata = file
        .metadata()
        .map_err(|error| format!("stat Dart SDK identity file {}: {error}", path.display()))?;
    if !metadata.is_file() || metadata.nlink() != 1 {
        return Err(format!(
            "Dart SDK identity input must be a single-link regular file: {}",
            path.display()
        ));
    }
    let mut digest = Sha256::new();
    let mut buffer = [0u8; 64 * 1024];
    loop {
        let read = file
            .read(&mut buffer)
            .map_err(|error| format!("hash Dart SDK identity file {}: {error}", path.display()))?;
        if read == 0 {
            break;
        }
        digest.update(&buffer[..read]);
    }
    Ok(format!("sha256:{:x}", digest.finalize()))
}

fn verify_file_identities(identities: &BTreeMap<PathBuf, String>) -> Result<(), String> {
    for (path, expected) in identities {
        if &hash_file(path)? != expected {
            return Err(format!(
                "Dart SDK identity changed during verification: {}",
                path.display()
            ));
        }
    }
    Ok(())
}

fn read_regular(path: &Path, label: &str) -> Result<Vec<u8>, String> {
    let mut file = OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_NOFOLLOW | libc::O_NONBLOCK | libc::O_CLOEXEC)
        .open(path)
        .map_err(|error| format!("open {label} {}: {error}", path.display()))?;
    let metadata = file
        .metadata()
        .map_err(|error| format!("stat {label} {}: {error}", path.display()))?;
    if !metadata.is_file() || metadata.nlink() != 1 {
        return Err(format!(
            "{label} must be a single-link regular file: {}",
            path.display()
        ));
    }
    let mut bytes = Vec::new();
    file.read_to_end(&mut bytes)
        .map_err(|error| format!("read {label} {}: {error}", path.display()))?;
    Ok(bytes)
}

fn scratch_directory() -> Result<PathBuf, String> {
    let nonce = NEXT_SCRATCH.fetch_add(1, Ordering::Relaxed);
    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|error| format!("read clock for Dart scratch: {error}"))?
        .as_nanos();
    let root = std::env::temp_dir().join(format!(
        "cott-dart-verify-{}-{timestamp}-{nonce}",
        std::process::id()
    ));
    DirBuilder::new()
        .mode(0o700)
        .create(&root)
        .map_err(|error| format!("create Dart verification scratch: {error}"))?;
    fs::write(
        root.join(".cott-owner"),
        format!("{}-{timestamp}-{nonce}\n", std::process::id()),
    )
    .map_err(|error| format!("write Dart scratch ownership marker: {error}"))?;
    Ok(root)
}

fn finish_scratch<T>(scratch: PathBuf, result: Result<T, String>) -> Result<T, String> {
    let marker = scratch.join(".cott-owner");
    let owned = fs::symlink_metadata(&scratch).is_ok_and(|metadata| metadata.is_dir())
        && fs::symlink_metadata(&marker).is_ok_and(|metadata| {
            metadata.is_file() && metadata.nlink() == 1 && !metadata.file_type().is_symlink()
        });
    let cleanup = if owned {
        fs::remove_dir_all(&scratch)
            .map_err(|error| format!("remove Dart verification scratch: {error}"))
    } else {
        Err("Dart verification scratch ownership changed before cleanup".to_owned())
    };
    match (result, cleanup) {
        (Ok(value), Ok(())) => Ok(value),
        (Err(error), Ok(())) => Err(error),
        (Ok(_), Err(error)) => Err(error),
        (Err(error), Err(cleanup)) => Err(format!("{error}; additionally {cleanup}")),
    }
}

fn parse_version(value: &str) -> Option<(u64, u64, u64)> {
    let mut parts = value.split('.');
    let version = (
        parts.next()?.parse().ok()?,
        parts.next()?.parse().ok()?,
        parts.next()?.parse().ok()?,
    );
    parts.next().is_none().then_some(version)
}

fn safe_relative(path: &Path) -> bool {
    !path.as_os_str().is_empty()
        && path.is_relative()
        && path
            .components()
            .all(|component| matches!(component, Component::Normal(_)))
}

fn path_argument(path: &Path, label: &str) -> Result<String, String> {
    path.to_str()
        .map(str::to_owned)
        .ok_or_else(|| format!("{label} path is not UTF-8"))
}
