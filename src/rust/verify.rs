//! Compiler-owned offline Cargo build and authenticated native contract execution.
use super::dependencies::{self, PackageMetadata, ResolvedDependencies};
use super::runner::{self, RunnerProgram};
use super::{RustEmission, RustPlan, emit};
use crate::contract_test::{ContractTestStrategy, derive_strategies};
use crate::hash::sha256_hex;
use crate::manifest::RustProjectConfig;
use crate::project::RustPaths;
use crate::proof::prove_contracts;
use crate::provenance::{SemanticCoverage, validate_semantic_coverage};
use crate::sandbox::{BindMounts, NetworkAccess, ResourceLimits, SandboxSpec, run};
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, DirBuilder, OpenOptions};
use std::io::Read;
use std::os::unix::fs::{DirBuilderExt, MetadataExt, OpenOptionsExt, PermissionsExt};
use std::path::{Component, Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::{Duration, SystemTime, UNIX_EPOCH};
#[path = "verify_evidence.rs"]
mod evidence;
const LIBRARY_ARTIFACT: &str = "rust/verification/cott-module.rlib";
const MAX_DIAGNOSTICS: usize = 20;
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
    cargo: PathBuf,
    rustc: PathBuf,
    roots: Vec<PathBuf>,
    tools: Value,
    identity_files: BTreeMap<PathBuf, String>,
}
pub(crate) fn probe(config: &RustProjectConfig, paths: &RustPaths) -> Result<Value, String> {
    let scratch = scratch_directory()?;
    let result = Toolchain::inspect(config, paths, &scratch).map(|t| t.tools);
    finish_scratch(scratch, result)
}
pub(crate) fn verify(
    config: &RustProjectConfig,
    paths: &RustPaths,
    plan: &RustPlan,
    emission: &RustEmission,
    metadata: &PackageMetadata,
) -> Result<Verification, String> {
    if !emission.unresolved.is_empty() {
        let mut missing = emission.unresolved.clone();
        missing.sort();
        missing.dedup();
        return Err(format!(
            "Rust verification requires a fully resolved target; unresolved: {}",
            missing.join(", ")
        ));
    }
    audit_canonical_ir(plan, emission)?;
    let strategies = derive_strategies(&plan.ir, &config.verification)
        .map_err(|e| format!("derive Rust contract strategies: {e}"))?;
    let proofs = prove_contracts(&plan.ir, None, &config.verification)
        .map_err(|e| format!("prove Rust contracts: {e}"))?;
    let program = runner::render(config, plan, &strategies, &config.verification)
        .map_err(|e| format!("render bounded Rust contract runner: {e}"))?;
    let scratch = scratch_directory()?;
    let result = verify_in_scratch(
        config,
        paths,
        plan,
        emission,
        metadata,
        &strategies,
        proofs,
        &program,
        &scratch,
    );
    finish_scratch(scratch, result)
}
#[allow(clippy::too_many_arguments)]
fn verify_in_scratch(
    config: &RustProjectConfig,
    paths: &RustPaths,
    plan: &RustPlan,
    emission: &RustEmission,
    metadata: &PackageMetadata,
    strategies: &[ContractTestStrategy],
    proofs: Value,
    program: &RunnerProgram,
    scratch: &Path,
) -> Result<Verification, String> {
    let input_snapshot = frozen_inputs(paths, metadata)?;
    let toolchain = Toolchain::inspect(config, paths, scratch)?;
    let resolved = dependencies::resolve(metadata, None)?;
    dependencies::validate_frozen_resolution(metadata, &resolved)?;
    let package = scratch.join("package");
    let runner_root = scratch.join("runner");
    let compiler = scratch.join("compiler");
    let runtime_root = scratch.join("runtime");
    for dir in [&package, &runner_root, &compiler, &runtime_root] {
        fs::create_dir(dir).map_err(|e| format!("create Rust verification scratch: {e}"))?;
    }
    for child in ["cargo-home", "home", "target", "tmp"] {
        fs::create_dir(compiler.join(child)).map_err(|e| e.to_string())?;
    }
    materialize_package(emission, &resolved, &package)?;
    let compiler_lock = dependencies::compiler_lock(metadata, &resolved)?;
    fs::write(package.join("Cargo.lock"), &compiler_lock).map_err(|e| e.to_string())?;
    fs::create_dir(runner_root.join("src")).map_err(|e| e.to_string())?;
    fs::create_dir(runner_root.join(".cargo")).map_err(|e| e.to_string())?;
    fs::write(
        runner_root.join("src").join(program.file_name),
        program.source.as_bytes(),
    )
    .map_err(|e| e.to_string())?;
    for (path, bytes) in &program.support {
        if !safe_relative(path) {
            return Err("unsafe Rust compiler support path".into());
        }
        let out = runner_root.join("src").join(path);
        fs::create_dir_all(out.parent().ok_or("invalid support path")?)
            .map_err(|e| e.to_string())?;
        fs::write(out, bytes).map_err(|e| e.to_string())?;
    }
    fs::write(runner_root.join(".cargo/config.toml"),b"[source.crates-io]\nreplace-with='cott-vendor'\n[source.cott-vendor]\ndirectory='../package/vendor'\n[net]\noffline=true\n").map_err(|e|e.to_string())?;
    let (runner_package, runner_lock) = runner_lock(config, &compiler_lock)?;
    fs::write(
        runner_root.join("Cargo.toml"),
        runner_manifest(config, &runner_package)?,
    )
    .map_err(|e| e.to_string())?;
    fs::write(runner_root.join("Cargo.lock"), &runner_lock).map_err(|e| e.to_string())?;
    let library_arguments = vec![
        "build".into(),
        "--lib".into(),
        "--offline".into(),
        "--locked".into(),
        "--jobs".into(),
        "1".into(),
        "--message-format=json".into(),
    ];
    let library_environment = toolchain.environment(&compiler)?;
    let library_command = command_record(
        &toolchain.cargo,
        &library_arguments,
        &package,
        scratch,
        &library_environment,
        NetworkAccess::Disabled,
    );
    let library_built = cargo_process(
        &toolchain,
        library_arguments,
        &package,
        &compiler,
        &package,
        library_environment,
    )?;
    require_success(
        "Rust strict facade library compilation",
        &library_built,
        scratch,
    )?;
    let build_arguments = vec![
        "build".into(),
        "--offline".into(),
        "--locked".into(),
        "--jobs".into(),
        "1".into(),
        "--message-format=json".into(),
    ];
    let build_environment = toolchain.environment(&compiler)?;
    let build_command = command_record(
        &toolchain.cargo,
        &build_arguments,
        &runner_root,
        scratch,
        &build_environment,
        NetworkAccess::Disabled,
    );
    let built = cargo_process(
        &toolchain,
        build_arguments,
        &runner_root,
        &compiler,
        &package,
        build_environment,
    )?;
    require_success("Rust offline locked compilation", &built, scratch)?;
    if read_regular(&runner_root.join("Cargo.lock"), "compiler runner lock")? != runner_lock
        || read_regular(&package.join("Cargo.lock"), "compiler package lock")? != compiler_lock
    {
        return Err("Cargo changed the compiler-owned frozen dependency graph".into());
    }
    let (library, binary) =
        compiled_outputs(&built.stdout, config, &package, &runner_root, &compiler)?;
    // Cargo hardlinks its public output names to target/debug/deps. Freeze only
    // compiler-created outputs into exclusive single-link files; authored-input
    // readers deliberately retain their stricter no-hardlink trust boundary.
    let library = freeze_compiler_output(
        &library,
        &compiler.join("target/cott-module-frozen.rlib"),
        &compiler,
        false,
    )?;
    let binary = freeze_compiler_output(
        &binary,
        &compiler.join("target/cott-contract-runner-frozen"),
        &compiler,
        true,
    )?;
    let library_bytes = read_regular(&library, "compiled Rust facade library")?;
    if library_bytes.is_empty() {
        return Err("Cargo produced an empty Rust facade library".into());
    }
    let binary_hash = hash_file(&binary)?;
    let mut key = [0u8; runner::EVIDENCE_KEY_BYTES];
    getrandom::fill(&mut key).map_err(|e| format!("generate Rust evidence key: {e}"))?;
    let runtime_environment = runtime_environment(&runtime_root);
    let runtime_network = if program.needs_loopback {
        NetworkAccess::IsolatedLoopback
    } else {
        NetworkAccess::Disabled
    };
    let runtime_command = command_record(
        &binary,
        &[],
        &runtime_root,
        scratch,
        &runtime_environment,
        runtime_network,
    );
    let executed = runtime_process(
        &binary,
        &runtime_root,
        &compiler,
        program,
        config,
        &key,
        runtime_environment,
    );
    let executed = match executed {
        Ok(p) => p,
        Err(e) => {
            key.fill(0);
            return Err(e);
        }
    };
    if executed.status != Some(0) || executed.timed_out {
        key.fill(0);
        return Err(format!(
            "bounded Rust contract runner failed with status {:?}; {}: {}",
            executed.status,
            executed.resources,
            diagnostics(&executed)
        ));
    }
    let events = runner::parse_events(&executed.stdout, &key);
    key.fill(0);
    let events = events?;
    evidence::validate_events(plan, program, strategies, &events)?;
    if hash_file(&binary)? != binary_hash {
        return Err("Rust contract runner binary changed during execution".into());
    }
    verify_file_identities(&toolchain.identity_files)?;
    if frozen_inputs(paths, metadata)? != input_snapshot {
        return Err("Rust authored input bytes changed during verification".into());
    }
    let resolved_after = dependencies::resolve(metadata, None)?;
    dependencies::validate_frozen_resolution(metadata, &resolved_after)?;
    let contracts = evidence::contract_report(plan, strategies, program, &events)?;
    let report = json!({
        "analysis":{"command":library_command,"diagnostics":0,"status":"passed"},
        "compilation":{"artifact":LIBRARY_ARTIFACT,"artifact_hash":format!("sha256:{}",sha256_hex(&library_bytes)),"command":library_command,"runner_command":build_command,"runner_source_hash":format!("sha256:{}",sha256_hex(program.source.as_bytes())),"runner_binary_hash":binary_hash,"status":"passed"},
        "contract_proofs":proofs,"contract_tests":contracts,"dependencies":resolved.record,
        "limits":{"candidate_limit":config.verification.candidate_limit,"lifecycle_limit":config.verification.lifecycle_limit,"proof_branch_limit":config.verification.proof_branch_limit,"proof_node_limit":config.verification.proof_node_limit,"scenario_timeout_ms":config.verification.fixtures.scenario_timeout_ms},
        "cargo_resolution":{"command":build_command,"lockfile_hash":format!("sha256:{}",sha256_hex(&compiler_lock)),"network":"disabled","status":"passed"},
        "runtime_capability":{"compilation_only":false,"facade_only":true,"grade":"runtime check","sandbox":"bubblewrap","filesystem_confinement":{"mechanism":"landlock","minimum_abi":3,"applied_before_runtime_threads":true,"proc_read_allowlist":[]},"process_confinement":{"mechanism":"seccomp","thread_synchronization":true,"applied_before_secret_input":true,"child_execution":"denied","non_thread_clone":"denied"},"network":if program.needs_loopback{"isolated_loopback"}else{"disabled"},"status":"passed"}
    });
    let coverage = crate::cli::semantic_coverage(&report, &config.verification.coverage)?;
    validate_semantic_coverage(&coverage)
        .map_err(|e| format!("invalid Rust semantic coverage: {e}"))?;
    let mut artifacts = resolved
        .artifacts
        .iter()
        .filter(|(path, _)| {
            path.as_path() == Path::new("rust/dependencies.json")
                || !emission.files.contains_key(*path)
        })
        .map(|(path, bytes)| (path.clone(), bytes.clone()))
        .collect::<BTreeMap<_, _>>();
    if artifacts
        .insert(LIBRARY_ARTIFACT.into(), library_bytes)
        .is_some()
    {
        return Err("Rust dependency material collided with library evidence".into());
    }
    let mut tools = toolchain.tools;
    tools["compiler_support"] = runner::validate_support()?;
    tools["commands"] =
        json!({"build_library":library_command,"build_runner":build_command,"run":runtime_command});
    tools["runtime_sandbox"] = report["runtime_capability"].clone();
    Ok(Verification {
        artifacts,
        tools,
        report,
        coverage,
        dependencies: resolved.record,
    })
}
fn runner_manifest(config: &RustProjectConfig, runner_package: &str) -> Result<Vec<u8>, String> {
    let name = &config.project.name;
    let version = &config.project.version;
    let value=format!("[package]\nname='{runner_package}'\nversion='0.0.0'\nedition='2024'\npublish=false\n[workspace]\n[dependencies]\n{name}={{path='../package',version='={version}'}}\ntokio={{version='=1.53.1',default-features=false,features=['rt','rt-multi-thread','sync','time']}}\n").parse::<toml::Value>().map_err(|e|e.to_string())?;
    toml::to_string(&value)
        .map(String::into_bytes)
        .map_err(|e| e.to_string())
}
fn runner_lock(config: &RustProjectConfig, bytes: &[u8]) -> Result<(String, Vec<u8>), String> {
    let mut lock = std::str::from_utf8(bytes)
        .map_err(|e| e.to_string())?
        .parse::<toml::Value>()
        .map_err(|e| e.to_string())?;
    let p = lock
        .get_mut("package")
        .and_then(toml::Value::as_array_mut)
        .ok_or("compiler Cargo lock has no package array")?;
    let mut runner_package = "cott_contract_runner".to_owned();
    let mut suffix = 0;
    while p
        .iter()
        .any(|p| p.get("name").and_then(toml::Value::as_str) == Some(&runner_package))
    {
        suffix += 1;
        runner_package = format!("cott_contract_runner_{suffix}");
    }
    let value=serde_json::from_value::<toml::Value>(json!({"name":runner_package,"version":"0.0.0","dependencies":[config.project.name,"tokio"]})).map_err(|e|e.to_string())?;
    p.push(value);
    p.sort_by_key(|p| {
        p.get("name")
            .and_then(toml::Value::as_str)
            .unwrap_or("")
            .to_owned()
    });
    let bytes = toml::to_string(&lock)
        .map(String::into_bytes)
        .map_err(|e| e.to_string())?;
    Ok((runner_package, bytes))
}
fn materialize_package(
    emission: &RustEmission,
    resolved: &ResolvedDependencies,
    root: &Path,
) -> Result<(), String> {
    let mut files = BTreeMap::new();
    for (path, bytes) in emission.files.iter().chain(&resolved.artifacts) {
        let Ok(relative) = path.strip_prefix("rust") else {
            continue;
        };
        if relative.starts_with("verification") {
            continue;
        }
        if !safe_relative(relative) {
            return Err(format!(
                "unsafe managed Rust package path {}",
                relative.display()
            ));
        }
        if let Some(old) = files.insert(relative.to_path_buf(), bytes) {
            if old != bytes {
                return Err(format!(
                    "compiler-owned Rust artifact collision: {}",
                    relative.display()
                ));
            }
        }
    }
    for (path, bytes) in files {
        let out = root.join(path);
        fs::create_dir_all(out.parent().ok_or("invalid Rust output")?)
            .map_err(|e| e.to_string())?;
        fs::write(out, bytes).map_err(|e| e.to_string())?;
    }
    Ok(())
}
fn frozen_inputs(
    paths: &RustPaths,
    metadata: &PackageMetadata,
) -> Result<BTreeMap<PathBuf, Vec<u8>>, String> {
    let mut inputs = dependencies::metadata_inputs(metadata);
    for (path, expected) in &inputs {
        if read_regular(path, "Rust frozen dependency input")? != *expected {
            return Err(format!(
                "Rust frozen dependency input changed: {}",
                path.display()
            ));
        }
    }
    inputs.insert(
        paths.manifest.clone(),
        read_regular(&paths.manifest, "Rust project manifest")?,
    );
    for s in crate::project::discover_rust_contract_sources(paths).map_err(|e| e.to_string())? {
        inputs.insert(s.path, s.text.into_bytes());
    }
    for s in
        crate::project::discover_rust_sources(&paths.rust_source_dir).map_err(|e| e.to_string())?
    {
        inputs.insert(s.disk_path, s.source.into_bytes());
    }
    Ok(inputs)
}
impl Toolchain {
    fn inspect(
        config: &RustProjectConfig,
        paths: &RustPaths,
        scratch: &Path,
    ) -> Result<Self, String> {
        let cargo = resolve_executable(&paths.root, &config.rust.cargo, "Cargo")?;
        let rustc = resolve_executable(&paths.root, &config.rust.rustc, "rustc")?;
        let mut roots = vec![distribution(&cargo)?, distribution(&rustc)?];
        roots.sort();
        roots.dedup();
        let mut t = Self {
            cargo,
            rustc,
            roots,
            tools: Value::Null,
            identity_files: BTreeMap::new(),
        };
        let cargo_result = t.probe_process(&t.cargo, &["-V"], scratch)?;
        require_success("Cargo identity probe", &cargo_result, scratch)?;
        let rustc_result = t.probe_process(&t.rustc, &["-vV"], scratch)?;
        require_success("rustc identity probe", &rustc_result, scratch)?;
        let cargo_output = std::str::from_utf8(&cargo_result.stdout)
            .map_err(|_| "Cargo version is not UTF-8")?
            .trim();
        let cargo_release = cargo_output
            .strip_prefix("cargo ")
            .and_then(|s| s.split_whitespace().next())
            .ok_or("Cargo -V did not report its version")?;
        let rustc_output = std::str::from_utf8(&rustc_result.stdout)
            .map_err(|_| "rustc identity is not UTF-8")?
            .trim();
        let values = rustc_output
            .lines()
            .filter_map(|l| l.split_once(": "))
            .collect::<BTreeMap<_, _>>();
        let release = *values.get("release").ok_or("rustc -vV has no release")?;
        let host = *values.get("host").ok_or("rustc -vV has no host")?;
        let commit = *values
            .get("commit-hash")
            .ok_or("rustc -vV has no commit-hash")?;
        validate_versions(cargo_release, release)?;
        if host.is_empty()
            || host.contains(['/', '\\'])
            || (commit != "unknown"
                && (commit.len() != 40 || !commit.bytes().all(|b| b.is_ascii_hexdigit())))
        {
            return Err("rustc -vV reported invalid host/commit identity".into());
        }
        let sysroot_result = t.probe_process(&t.rustc, &["--print", "sysroot"], scratch)?;
        require_success("rustc sysroot probe", &sysroot_result, scratch)?;
        let sysroot = fs::canonicalize(
            std::str::from_utf8(&sysroot_result.stdout)
                .map_err(|_| "rustc sysroot is not UTF-8")?
                .trim(),
        )
        .map_err(|e| format!("resolve rustc sysroot: {e}"))?;
        if sysroot == Path::new("/") {
            return Err("rustc sysroot cannot be filesystem root".into());
        }
        t.roots.push(sysroot.clone());
        t.roots.sort();
        t.roots.dedup();
        for p in [&t.cargo, &t.rustc] {
            t.identity_files.insert(p.clone(), hash_file(p)?);
        }
        let lib = sysroot.join("lib");
        if lib.is_dir() {
            for entry in fs::read_dir(&lib).map_err(|e| e.to_string())? {
                let p = entry.map_err(|e| e.to_string())?.path();
                if p.is_file() {
                    t.identity_files.insert(p.clone(), hash_file(&p)?);
                }
            }
        }
        let libs = sysroot.join("lib/rustlib").join(host).join("lib");
        if !libs.is_dir() {
            return Err(format!(
                "rustc host standard library is missing: {}",
                libs.display()
            ));
        }
        for entry in fs::read_dir(libs).map_err(|e| e.to_string())? {
            let p = entry.map_err(|e| e.to_string())?.path();
            if p.is_file() {
                t.identity_files.insert(p.clone(), hash_file(&p)?);
            }
        }
        t.tools = json!({"cargo":{"executable":t.cargo,"version":cargo_output,"release":cargo_release,"hash":t.identity_files[&t.cargo]},"rustc":{"executable":t.rustc,"version":rustc_output,"release":release,"commit_hash":commit,"host":host,"hash":t.identity_files[&t.rustc]},"sysroot":sysroot,"identity_files":t.identity_files.iter().map(|(p,h)|(p.to_string_lossy().into_owned(),h.clone())).collect::<BTreeMap<_,_>>()});
        Ok(t)
    }
    fn environment(&self, compiler: &Path) -> Result<BTreeMap<String, String>, String> {
        let path = std::env::join_paths([
            self.rustc.parent().ok_or("rustc has no directory")?,
            self.cargo.parent().ok_or("cargo has no directory")?,
            Path::new("/usr/bin"),
            Path::new("/bin"),
        ])
        .map_err(|e| e.to_string())?;
        Ok(BTreeMap::from([
            ("CI".into(), "true".into()),
            (
                "HOME".into(),
                path_argument(&compiler.join("home"), "Rust HOME")?,
            ),
            (
                "CARGO_HOME".into(),
                path_argument(&compiler.join("cargo-home"), "isolated Cargo home")?,
            ),
            (
                "CARGO_TARGET_DIR".into(),
                path_argument(&compiler.join("target"), "Rust target directory")?,
            ),
            ("RUSTC".into(), path_argument(&self.rustc, "rustc")?),
            ("RUSTFLAGS".into(), "-D warnings".into()),
            ("CARGO_PROFILE_DEV_DEBUG".into(), "0".into()),
            ("CARGO_INCREMENTAL".into(), "0".into()),
            ("LC_ALL".into(), "C.UTF-8".into()),
            ("PATH".into(), path.to_string_lossy().into_owned()),
            (
                "TMPDIR".into(),
                path_argument(&compiler.join("tmp"), "Rust TMPDIR")?,
            ),
        ]))
    }
    fn probe_process(
        &self,
        program: &Path,
        args: &[&str],
        scratch: &Path,
    ) -> Result<crate::sandbox::CompletedProcess, String> {
        let mut environment = BTreeMap::from([
            ("HOME".into(), scratch.to_string_lossy().into_owned()),
            ("PATH".into(), "/usr/bin:/bin".into()),
            ("LC_ALL".into(), "C.UTF-8".into()),
        ]);
        environment.insert("TMPDIR".into(), scratch.to_string_lossy().into_owned());
        run(&SandboxSpec {
            program: program.into(),
            arguments: args.iter().map(|s| (*s).into()).collect(),
            cwd: scratch.into(),
            environment,
            stdin: vec![],
            binds: BindMounts {
                read_only: self.roots.clone(),
                writable: vec![scratch.into()],
            },
            network: NetworkAccess::Disabled,
            limits: probe_limits(),
        })
        .map_err(|e| format!("sandboxed Rust toolchain probe failed: {e}"))
    }
}
fn distribution(executable: &Path) -> Result<PathBuf, String> {
    let dir = executable.parent().ok_or("tool has no parent")?;
    Ok(if dir.file_name().is_some_and(|n| n == "bin") {
        dir.parent().ok_or("tool distribution has no root")?.into()
    } else {
        dir.into()
    })
}
fn validate_versions(cargo: &str, rustc: &str) -> Result<(), String> {
    let c = semver::Version::parse(cargo).map_err(|e| format!("invalid Cargo release: {e}"))?;
    let r = semver::Version::parse(rustc).map_err(|e| format!("invalid rustc release: {e}"))?;
    if c != r {
        return Err(format!("Cargo/rustc release mismatch: {cargo} vs {rustc}"));
    }
    if !r.pre.is_empty()
        || !r.build.is_empty()
        || r < semver::Version::new(1, 85, 0)
        || r.major >= 2
    {
        return Err(format!(
            "Rust toolchain release {rustc} is outside supported >=1.85.0,<2.0.0 stable releases"
        ));
    }
    Ok(())
}
fn resolve_executable(root: &Path, configured: &str, label: &str) -> Result<PathBuf, String> {
    if configured.is_empty() || configured.contains('\0') {
        return Err(format!("{label} executable is empty or contains NUL"));
    }
    let p = Path::new(configured);
    let candidate = if p.components().count() > 1 {
        if p.is_absolute() {
            p.into()
        } else {
            root.join(p)
        }
    } else {
        std::env::var_os("PATH")
            .into_iter()
            .flat_map(|p| std::env::split_paths(&p).collect::<Vec<_>>())
            .map(|d| d.join(p))
            .find(|p| p.is_file())
            .ok_or_else(|| format!("cannot find {label} executable `{configured}` on PATH"))?
    };
    let mut real = fs::canonicalize(&candidate).map_err(|e| format!("resolve {label}: {e}"))?;
    if real.file_name().is_some_and(|n| n == "rustup")
        && candidate
            .file_name()
            .is_some_and(|n| n == "cargo" || n == "rustc")
    {
        let home = std::env::var_os("RUSTUP_HOME")
            .map(PathBuf::from)
            .or_else(|| std::env::var_os("HOME").map(|h| PathBuf::from(h).join(".rustup")))
            .ok_or("HOME/RUSTUP_HOME is required for Rustup proxies")?;
        let settings = read_regular(&home.join("settings.toml"), "Rustup settings")?;
        let settings = std::str::from_utf8(&settings)
            .map_err(|e| e.to_string())?
            .parse::<toml::Value>()
            .map_err(|e| e.to_string())?;
        let selected = std::env::var("RUSTUP_TOOLCHAIN")
            .ok()
            .or_else(|| {
                settings
                    .get("default_toolchain")
                    .and_then(toml::Value::as_str)
                    .map(str::to_owned)
            })
            .ok_or("Rustup has no selected default toolchain")?;
        if selected.contains(['/', '\\']) || selected.is_empty() {
            return Err("Rustup selected toolchain name is not safe".into());
        }
        let dir = home.join("toolchains");
        let mut matches = fs::read_dir(&dir)
            .map_err(|e| e.to_string())?
            .filter_map(Result::ok)
            .filter(|e| {
                e.file_name()
                    .to_str()
                    .is_some_and(|n| n == selected || n.starts_with(&format!("{selected}-")))
            })
            .map(|e| e.path())
            .collect::<Vec<_>>();
        matches.sort();
        if matches.len() != 1 {
            return Err(format!(
                "Rustup toolchain `{selected}` must identify one installed distribution; configure absolute cargo/rustc paths"
            ));
        }
        real = fs::canonicalize(
            matches
                .remove(0)
                .join("bin")
                .join(candidate.file_name().ok_or("invalid tool name")?),
        )
        .map_err(|e| e.to_string())?;
    }
    let m = fs::metadata(&real).map_err(|e| e.to_string())?;
    if !m.is_file() || m.nlink() != 1 || m.permissions().mode() & 0o111 == 0 {
        return Err(format!(
            "{label} must be an executable single-link regular file"
        ));
    }
    Ok(real)
}
fn cargo_process(
    t: &Toolchain,
    args: Vec<String>,
    runner_root: &Path,
    compiler: &Path,
    package: &Path,
    environment: BTreeMap<String, String>,
) -> Result<crate::sandbox::CompletedProcess, String> {
    let mut ro = t.roots.clone();
    ro.extend([package.into(), runner_root.into()]);
    ro.sort();
    ro.dedup();
    run(&SandboxSpec {
        program: t.cargo.clone(),
        arguments: args,
        cwd: runner_root.into(),
        environment,
        stdin: vec![],
        binds: BindMounts {
            read_only: ro,
            writable: vec![compiler.into()],
        },
        network: NetworkAccess::Disabled,
        limits: compiler_limits(),
    })
    .map_err(|e| format!("sandboxed Rust Cargo execution failed: {e}"))
}
fn runtime_process(
    binary: &Path,
    runtime_root: &Path,
    compiler: &Path,
    program: &RunnerProgram,
    config: &RustProjectConfig,
    key: &[u8],
    environment: BTreeMap<String, String>,
) -> Result<crate::sandbox::CompletedProcess, String> {
    let launcher = fs::canonicalize(std::env::current_exe().map_err(|e| e.to_string())?)
        .map_err(|e| e.to_string())?;
    let readonly = vec![compiler.join("target"), launcher.clone()];
    let writable = vec![runtime_root.into()];
    let spec = crate::sandbox::landlock::ConfinedExec {
        executable: binary.into(),
        arguments: vec![],
        read_only: readonly.clone(),
        writable: writable.clone(),
    };
    let json = serde_json::to_string(&spec).map_err(|e| e.to_string())?;
    run(&SandboxSpec {
        program: launcher,
        arguments: vec![crate::sandbox::landlock::RUST_EXEC_MODE.into(), json],
        cwd: runtime_root.into(),
        environment,
        stdin: key.to_vec(),
        binds: BindMounts {
            read_only: readonly,
            writable,
        },
        network: if program.needs_loopback {
            NetworkAccess::IsolatedLoopback
        } else {
            NetworkAccess::Disabled
        },
        limits: runtime_limits(config, program),
    })
    .map_err(|e| format!("sandboxed Rust runtime execution failed: {e}"))
}
fn compiled_outputs(
    stdout: &[u8],
    config: &RustProjectConfig,
    package: &Path,
    runner: &Path,
    compiler: &Path,
) -> Result<(PathBuf, PathBuf), String> {
    let mut library = None;
    let mut binary = None;
    for line in stdout.split(|b| *b == b'\n') {
        let Ok(v) = serde_json::from_slice::<Value>(line) else {
            continue;
        };
        if v["reason"] != "compiler-artifact" {
            continue;
        }
        let source = v
            .pointer("/target/src_path")
            .and_then(Value::as_str)
            .map(PathBuf::from);
        if source.as_deref() == Some(package.join("src/lib.rs").as_path())
            && v.pointer("/target/name").and_then(Value::as_str)
                == Some(config.project.name.as_str())
        {
            for f in v["filenames"]
                .as_array()
                .ok_or("invalid Cargo compiler filenames")?
            {
                let p = PathBuf::from(f.as_str().ok_or("invalid Cargo filename")?);
                if p.extension().is_some_and(|e| e == "rlib") {
                    if library.replace(p).is_some() {
                        return Err("Cargo emitted duplicate facade library artifacts".into());
                    }
                }
            }
        }
        if source.as_deref() == Some(runner.join("src/main.rs").as_path())
            && v.pointer("/target/kind")
                .and_then(Value::as_array)
                .is_some_and(|k| k.iter().any(|v| v == "bin"))
        {
            binary = v["executable"].as_str().map(PathBuf::from);
        }
    }
    let library = library.ok_or("Cargo omitted the compiled Rust facade .rlib")?;
    let binary = binary.ok_or("Cargo omitted the compiled Rust contract runner")?;
    let root = compiler.join("target");
    for p in [&library, &binary] {
        if !p.starts_with(&root)
            || !safe_relative(p.strip_prefix(&root).map_err(|e| e.to_string())?)
        {
            return Err("Cargo output escaped the compiler target directory".into());
        }
        let real = fs::canonicalize(p).map_err(|e| e.to_string())?;
        if !real.starts_with(&root) {
            return Err("Cargo output symlink escaped its target directory".into());
        }
    }
    Ok((library, binary))
}
fn runtime_environment(root: &Path) -> BTreeMap<String, String> {
    BTreeMap::from([
        ("HOME".into(), root.to_string_lossy().into_owned()),
        ("TMPDIR".into(), root.to_string_lossy().into_owned()),
        ("LC_ALL".into(), "C.UTF-8".into()),
        ("PATH".into(), "/usr/bin:/bin".into()),
    ])
}
fn command_record(
    program: &Path,
    args: &[String],
    cwd: &Path,
    scratch: &Path,
    environment: &BTreeMap<String, String>,
    network: NetworkAccess,
) -> Value {
    let clean = |p: &str| p.replace(scratch.to_string_lossy().as_ref(), "<scratch>");
    json!({"executable":clean(&program.to_string_lossy()),"arguments":args.iter().map(|a|clean(a)).collect::<Vec<_>>(),"cwd":clean(&cwd.to_string_lossy()),"network":match network{NetworkAccess::Disabled=>"disabled",NetworkAccess::IsolatedLoopback=>"isolated_loopback",NetworkAccess::Enabled=>"enabled"},"environment":environment.iter().map(|(k,v)|(k,clean(v))).collect::<BTreeMap<_,_>>()})
}
fn probe_limits() -> ResourceLimits {
    ResourceLimits {
        cpu_time: Duration::from_secs(15),
        address_space_bytes: 2 * 1024 * 1024 * 1024,
        process_count: 32,
        open_files: 128,
        file_size_bytes: 8 * 1024 * 1024,
        wall_time: Duration::from_secs(20),
        stream_limit_bytes: 1024 * 1024,
        writable_bytes: 16 * 1024 * 1024,
    }
}
fn compiler_limits() -> ResourceLimits {
    ResourceLimits {
        cpu_time: Duration::from_secs(180),
        address_space_bytes: 4 * 1024 * 1024 * 1024,
        process_count: 64,
        open_files: 256,
        file_size_bytes: 256 * 1024 * 1024,
        wall_time: Duration::from_secs(240),
        stream_limit_bytes: 8 * 1024 * 1024,
        writable_bytes: 512 * 1024 * 1024,
    }
}
fn runtime_limits(config: &RustProjectConfig, program: &RunnerProgram) -> ResourceLimits {
    let units = program
        .expected_cases
        .values()
        .map(|v| u64::from(*v))
        .sum::<u64>()
        .saturating_add(
            program
                .expected_scenarios
                .values()
                .map(|s| u64::from(s.cancellations) + 1)
                .sum::<u64>(),
        )
        .max(1);
    let ms = u64::from(config.verification.fixtures.scenario_timeout_ms)
        .saturating_mul(units)
        .clamp(5000, 120000);
    ResourceLimits {
        cpu_time: Duration::from_millis(ms),
        address_space_bytes: 2 * 1024 * 1024 * 1024,
        process_count: 64,
        open_files: 128,
        file_size_bytes: 16 * 1024 * 1024,
        wall_time: Duration::from_millis(ms + 5000),
        stream_limit_bytes: 4 * 1024 * 1024,
        writable_bytes: 32 * 1024 * 1024,
    }
}

fn audit_canonical_ir(plan: &RustPlan, emission: &RustEmission) -> Result<(), String> {
    for module in &plan.ir.modules {
        let mut path = PathBuf::from("ir");
        let segments = &module.module.segments;
        for segment in &segments[..segments.len().saturating_sub(1)] {
            path.push(segment);
        }
        path.push(format!(
            "{}.json",
            segments.last().ok_or("canonical Rust module has no name")?
        ));
        if emission.files.get(&path) != Some(&module.bytes) {
            return Err(format!(
                "Rust emission canonical IR was omitted or tampered: {}",
                path.display()
            ));
        }
    }
    Ok(())
}
fn require_success(
    label: &str,
    process: &crate::sandbox::CompletedProcess,
    scratch: &Path,
) -> Result<(), String> {
    if process.status == Some(0) && !process.timed_out {
        return Ok(());
    }
    Err(format!(
        "{label} failed with status {:?}; {}: {}",
        process.status,
        process.resources,
        diagnostics(process).replace(scratch.to_string_lossy().as_ref(), "<scratch>")
    ))
}
fn diagnostics(process: &crate::sandbox::CompletedProcess) -> String {
    let stdout = String::from_utf8_lossy(&process.stdout);
    let mut errors = String::new();
    for line in stdout.lines() {
        match serde_json::from_str::<Value>(line) {
            Ok(value) if value["reason"] == "compiler-message" => {
                if let Some(rendered) = value.pointer("/message/rendered").and_then(Value::as_str) {
                    errors.push_str(rendered);
                    errors.push('\n');
                }
            }
            Ok(value) if value.get("reason").is_some() => {}
            _ => {
                errors.push_str(line);
                errors.push('\n');
            }
        }
    }
    errors.push_str(&String::from_utf8_lossy(&process.stderr));
    errors
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
        .map_err(|e| format!("open Rust identity file {}: {e}", path.display()))?;
    let m = file.metadata().map_err(|e| e.to_string())?;
    if !m.is_file() || m.nlink() != 1 {
        return Err(format!(
            "Rust identity must be a single-link regular file: {}",
            path.display()
        ));
    }
    let mut hash = Sha256::new();
    let mut buffer = [0u8; 64 * 1024];
    loop {
        let count = file.read(&mut buffer).map_err(|e| e.to_string())?;
        if count == 0 {
            break;
        }
        hash.update(&buffer[..count]);
    }
    Ok(format!("sha256:{:x}", hash.finalize()))
}
fn verify_file_identities(identities: &BTreeMap<PathBuf, String>) -> Result<(), String> {
    for (path, expected) in identities {
        if hash_file(path)? != *expected {
            return Err(format!(
                "Rust toolchain identity changed during verification: {}",
                path.display()
            ));
        }
    }
    Ok(())
}
fn read_regular(path: &Path, label: &str) -> Result<Vec<u8>, String> {
    let file = OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_NOFOLLOW | libc::O_NONBLOCK | libc::O_CLOEXEC)
        .open(path)
        .map_err(|e| format!("open {label} {}: {e}", path.display()))?;
    let m = file.metadata().map_err(|e| e.to_string())?;
    if !m.is_file() || m.nlink() != 1 || m.len() > 256 * 1024 * 1024 {
        return Err(format!(
            "{label} must be a bounded single-link regular file: {}",
            path.display()
        ));
    }
    let mut bytes = Vec::new();
    file.take(256 * 1024 * 1024 + 1)
        .read_to_end(&mut bytes)
        .map_err(|e| e.to_string())?;
    if bytes.len() > 256 * 1024 * 1024 {
        return Err(format!("{label} exceeds its material limit"));
    }
    Ok(bytes)
}
fn scratch_directory() -> Result<PathBuf, String> {
    let nonce = NEXT_SCRATCH.fetch_add(1, Ordering::Relaxed);
    let timestamp = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|e| e.to_string())?
        .as_nanos();
    let root = std::env::temp_dir().join(format!(
        "cott-rust-verify-{}-{timestamp}-{nonce}",
        std::process::id()
    ));
    DirBuilder::new()
        .mode(0o700)
        .create(&root)
        .map_err(|e| e.to_string())?;
    fs::write(
        root.join(".cott-owner"),
        format!("{}-{timestamp}-{nonce}\n", std::process::id()),
    )
    .map_err(|e| e.to_string())?;
    Ok(root)
}
fn finish_scratch<T>(scratch: PathBuf, result: Result<T, String>) -> Result<T, String> {
    let marker = scratch.join(".cott-owner");
    let owned = fs::symlink_metadata(&scratch)
        .is_ok_and(|m| m.is_dir() && !m.file_type().is_symlink())
        && fs::symlink_metadata(&marker)
            .is_ok_and(|m| m.is_file() && m.nlink() == 1 && !m.file_type().is_symlink());
    let cleanup = if owned {
        fs::remove_dir_all(&scratch).map_err(|e| format!("remove Rust verification scratch: {e}"))
    } else {
        Err("Rust verification scratch ownership changed before cleanup".into())
    };
    match (result, cleanup) {
        (Ok(value), Ok(())) => Ok(value),
        (Err(error), Ok(())) => Err(error),
        (Ok(_), Err(error)) => Err(error),
        (Err(error), Err(cleanup)) => Err(format!("{error}; additionally {cleanup}")),
    }
}
fn safe_relative(path: &Path) -> bool {
    !path.as_os_str().is_empty() && path.components().all(|c| matches!(c, Component::Normal(_)))
}
fn path_argument(path: &Path, label: &str) -> Result<String, String> {
    path.to_str()
        .map(str::to_owned)
        .ok_or_else(|| format!("{label} path is not UTF-8"))
}

#[cfg(test)]
#[path = "verify_tests.rs"]
mod tests;

fn freeze_compiler_output(
    source: &Path,
    destination: &Path,
    compiler: &Path,
    executable: bool,
) -> Result<PathBuf, String> {
    use std::io::Write;
    use std::os::unix::fs::OpenOptionsExt;
    let root = compiler.join("target");
    for path in [source, destination] {
        if !path.starts_with(&root)
            || !safe_relative(path.strip_prefix(&root).map_err(|e| e.to_string())?)
        {
            return Err("compiler output freeze escaped target scratch".into());
        }
    }
    let mut input = OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_NOFOLLOW | libc::O_NONBLOCK | libc::O_CLOEXEC)
        .open(source)
        .map_err(|e| format!("open compiler output {}: {e}", source.display()))?;
    let before = input.metadata().map_err(|e| e.to_string())?;
    if !before.is_file()
        || before.len() == 0
        || before.len() > 256 * 1024 * 1024
        || executable && before.permissions().mode() & 0o111 == 0
    {
        return Err("Cargo output is not a bounded regular compiler artifact".into());
    }
    let mut output = OpenOptions::new()
        .write(true)
        .create_new(true)
        .mode(if executable { 0o500 } else { 0o400 })
        .custom_flags(libc::O_NOFOLLOW | libc::O_CLOEXEC)
        .open(destination)
        .map_err(|e| format!("create exclusive compiler output freeze: {e}"))?;
    let copied = std::io::copy(
        &mut Read::by_ref(&mut input).take(256 * 1024 * 1024 + 1),
        &mut output,
    )
    .map_err(|e| e.to_string())?;
    let after = input.metadata().map_err(|e| e.to_string())?;
    let identity = |m: &fs::Metadata| {
        (
            m.dev(),
            m.ino(),
            m.len(),
            m.mtime(),
            m.mtime_nsec(),
            m.ctime(),
            m.ctime_nsec(),
        )
    };
    if copied != before.len() || identity(&before) != identity(&after) {
        return Err("compiler artifact changed while being frozen".into());
    }
    output.flush().map_err(|e| e.to_string())?;
    output.sync_all().map_err(|e| e.to_string())?;
    let frozen = output.metadata().map_err(|e| e.to_string())?;
    if frozen.nlink() != 1 || !frozen.is_file() || frozen.len() != copied {
        return Err("compiler artifact freeze is not single-link regular output".into());
    }
    Ok(destination.to_path_buf())
}
