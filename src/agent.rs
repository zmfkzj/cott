use std::collections::BTreeMap;
use std::fs::{self, OpenOptions};
use std::os::unix::fs::MetadataExt;
use std::path::{Path, PathBuf};
use std::time::{Duration, Instant};

use crate::hash::sha256_hex;
use crate::python::artifact_plan::{PythonCallable, PythonCallableKind};
use crate::sandbox::{BindMounts, NetworkAccess, ResourceLimits, SandboxSpec, run};
use crate::version::{is_at_least, parse_version};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum AgentKind {
    Codex,
    Omp,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AdapterSpec {
    pub executable_name: &'static str,
    pub minimum_version: &'static str,
    pub version_argv: &'static [&'static str],
    pub argv_template: &'static [&'static str],
    pub prompt_on_stdin: bool,
}

pub const CODEX: AdapterSpec = AdapterSpec {
    executable_name: "codex",
    minimum_version: "0.147.0",
    version_argv: &["--version"],
    argv_template: &[
        "exec",
        "--strict-config",
        "--ephemeral",
        "--ignore-user-config",
        "--ignore-rules",
        "--skip-git-repo-check",
        "--sandbox",
        "workspace-write",
        "--color",
        "never",
        "--cd",
        "<workspace>",
        "-",
    ],
    prompt_on_stdin: true,
};
pub const OMP: AdapterSpec = AdapterSpec {
    executable_name: "omp",
    minimum_version: "17.2.12",
    version_argv: &["--version"],
    argv_template: &[
        "-p",
        "--cwd",
        "<workspace>",
        "--no-session",
        "--no-rules",
        "--no-skills",
        "--no-extensions",
        "--no-lsp",
        "--no-pty",
        "--no-title",
        "--tools",
        "read,grep,glob,edit,write",
        "--approval-mode",
        "yolo",
        "--max-time",
        "<seconds>s",
        "--config",
        "<overlay>",
        "<prompt>",
    ],
    prompt_on_stdin: false,
};

pub fn adapter(kind: AgentKind) -> &'static AdapterSpec {
    match kind {
        AgentKind::Codex => &CODEX,
        AgentKind::Omp => &OMP,
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AgentRunCandidate {
    pub implementation: Vec<u8>,
    pub executable: PathBuf,
    pub executable_hash: String,
    pub adapter_version: String,
    pub prompt_hash: String,
    pub stdout: Vec<u8>,
    pub stderr: Vec<u8>,
    pub exit_code: Option<i32>,
    pub timed_out: bool,
    pub duration_ms: u64,
    pub environment_names: Vec<String>,
}

pub fn render_prompt(
    callable: &PythonCallable,
    selected_ir: &[u8],
    docs: &str,
    type_declarations: &str,
    external_types: &BTreeMap<String, String>,
    bound_symbols: &str,
    existing: Option<&[u8]>,
    rules: Option<&[u8]>,
    write_path: &Path,
) -> Result<Vec<u8>, String> {
    if is_default_impl_method(callable) {
        return Err(format!(
            "compiler-owned default implementation method `{}` must not be sent to an agent",
            callable.cott_symbol
        ));
    }
    if rules.is_some_and(|rules| rules.len() > 1024 * 1024) || selected_ir.len() > 1024 * 1024 {
        return Err("agent prompt input exceeds 1 MiB".to_owned());
    }
    let ownership = match &callable.kind {
        PythonCallableKind::Function => format!(
            "Define exactly one canonical top-level function `{}`. You MAY additionally define private implementation helpers, private immutable constants, and invariant TypeVars. Each helper MUST be an undecorated, synchronous, fully annotated top-level function whose name starts with a single `_` but is neither dunder nor reserved `_cott_`; function names MUST be unique. Each constant MUST have a single-leading-underscore name that is neither dunder nor reserved `_cott_`, and be a literal `Final[bool|int|float|str|bytes]` value. Do not define classes, public helpers, mutable globals, decorators, async functions, variadic parameters, parameter defaults, or other executable top-level assignments.",
            callable.name
        ),
        PythonCallableKind::AsyncFunction => format!(
            "Define exactly one canonical undecorated top-level `async def` function `{}`. You MAY additionally define private implementation helpers, private immutable constants, and invariant TypeVars. Each helper MUST be an undecorated, synchronous, fully annotated top-level function whose name starts with a single `_` but is neither dunder nor reserved `_cott_`; function names MUST be unique. Each constant MUST have a single-leading-underscore name that is neither dunder nor reserved `_cott_`, and be a literal `Final[bool|int|float|str|bytes]` value. Do not define classes, public helpers, mutable globals, decorators, additional async functions, variadic parameters, parameter defaults, or other executable top-level assignments. Await every call to an async Cott facade; never await a synchronous Cott facade.",
            callable.name
        ),
        PythonCallableKind::ImplMethod { concrete } => format!(
            "Define exactly one canonical private top-level function `_cott_impl_{concrete}_{}`. You MAY additionally define private implementation helpers, private immutable constants, and invariant TypeVars. Each helper MUST be an undecorated, synchronous, fully annotated top-level function whose name starts with a single `_` but is neither dunder nor reserved `_cott_`; function names MUST be unique. Each constant MUST have a single-leading-underscore name that is neither dunder nor reserved `_cott_`, and be a literal `Final[bool|int|float|str|bytes]` value. Do not define classes, public helpers, mutable globals, decorators, async functions, variadic parameters, parameter defaults, or other executable top-level assignments. The compiler owns the public class `{concrete}` in `{}`; import it only as `from {} import {concrete}` for the `self` annotation and never construct, subclass, or redefine it.",
            callable.name, callable.module, callable.module
        ),
    };
    let external_types = external_types
        .iter()
        .map(|(name, projection)| format!("{name} = {projection}"))
        .collect::<Vec<_>>()
        .join("\n");
    let mut prompt = format!("COTT_AGENT_PROMPT_V1\n\nTARGET\nSymbol: {}\nWrite path: {}\n\nIMPLEMENTATION OWNERSHIP\n{ownership}\n\nCANONICAL IR\n{}\n\nDOCS CONTRACTS EFFECTS\n{docs}\n\nRELEVANT TYPES\n{type_declarations}\n\nPYTHON EXTERNAL TYPE PROJECTIONS\n{external_types}\n\nBOUND SYMBOLS IMPORT RULES\n{bound_symbols}\n\nTYPE MODEL\nPreserve every declared annotation exactly. For Iterator and Generator returns, return the lazy object itself: do not iterate, materialize, normalize, or validate inner values. Use external declarations through their exact public generated aliases; their projected public APIs MAY be called when the contract requires it. Do not reconstruct external paths, use dynamic imports or reflection, or inspect and coerce external values merely to validate a contract. Any, Unknown, and inner values of Opaque or lazy types are evidence-only: preserve them without inspection, coercion, or validation. Preserve Opaque values and their declared tag boundary without inspecting their payload.\n", callable.cott_symbol, write_path.display(), String::from_utf8_lossy(selected_ir)).into_bytes();
    prompt.extend_from_slice(b"Standard ABI aliases, including integer widths, are annotations and MUST NOT be called. Construct result values only with top-level `cott_runtime.Ok(...)`/`cott_runtime.Err(...)`, never `Result.Ok`/`Result.Err`. Generated payload enum aliases have no members; import and construct top-level `<Enum>_<Variant>` classes from the exact generated `*_types` module, never `<Enum>.<Variant>`.\n");
    prompt.extend_from_slice(b"\nFACTORY TYPE MODEL\n`Factory[Concrete]` maps to `type[Concrete]`: it is the exact compiler-generated `Concrete` class object, never an instance, subclass, or arbitrary callable. Constructor calls MUST match `Concrete`'s inferred Cott init signature. Validation MUST NOT construct or invoke a Factory value.\n");
    prompt.extend_from_slice(b"\nEFFECT CALLS\nCall Cott functions only by their exact imported facade name. Do not alias, store, return, pass, rebind, or shadow a Cott callable, and do not call a value whose Cott identity is dynamic. For an implementation target, a public sibling method of the same concrete may only be called through a parameter annotated with that concrete (normally `self`) or a direct local alias of one, as `<receiver>.<method>(...)`; it is a Cott call. Every direct or private-helper-reachable Cott call must be covered by the target function's declared effects. Imported stdlib, external projections, generated value constructors, and exact Factory constructors are effect leaves.\n");
    prompt.extend_from_slice(b"\nCONTAINER ABI\nVariadic Cott `Tuple[T, ...]` uses native `tuple[T, ...]`. Cott `Array[T, N]` uses `CottArray[T, Literal[N]]` and is constructed only as `CottArray(values=(...))`; Cott `Buffer[N]` uses `CottBuffer[Literal[N]]` and is constructed only as `CottBuffer(data=bytes.fromhex(\"...\"))`. Import `CottArray` and `CottBuffer` from `cott_runtime` and `Literal` from `typing` when required; never substitute Python primitives or call ABI aliases.\n");
    if let Some(existing) = existing {
        prompt.extend_from_slice(b"\nEXISTING IMPLEMENTATION\n");
        prompt.extend_from_slice(existing);
    }
    if let Some(rules) = rules {
        prompt.extend_from_slice(b"\nPROJECT RULES\n");
        prompt.extend_from_slice(rules);
        prompt.push(b'\n');
    }
    prompt.extend_from_slice(b"\nImplement only the target Python file. Do not modify .cott contracts, manifests, rules, bindings, generated files, or other implementations. Do not reimplement bound symbols. If the contract must change, report that and leave the target unresolved.\n");
    if prompt.len() > 1024 * 1024 {
        return Err("rendered agent prompt exceeds 1 MiB".to_owned());
    }
    Ok(prompt)
}

fn is_default_impl_method(callable: &PythonCallable) -> bool {
    matches!(&callable.kind, PythonCallableKind::ImplMethod { .. })
        && callable
            .declaration
            .get("selected")
            .and_then(serde_json::Value::as_object)
            .and_then(|selected| selected.get("kind"))
            .and_then(serde_json::Value::as_str)
            == Some("default")
}

pub fn run_agent(
    kind: AgentKind,
    executable: PathBuf,
    workspace: &Path,
    scratch: &Path,
    target: &Path,
    prompt: Vec<u8>,
    timeout_seconds: u16,
) -> Result<AgentRunCandidate, String> {
    let spec = adapter(kind);
    let executable = fs::canonicalize(&executable)
        .map_err(|error| format!("resolve {} executable: {error}", spec.executable_name))?;
    let metadata = fs::symlink_metadata(&executable)
        .map_err(|error| format!("stat {} executable: {error}", spec.executable_name))?;
    if !metadata.is_file() || metadata.file_type().is_symlink() || metadata.nlink() != 1 {
        return Err(format!(
            "{} executable must be a regular single-link file",
            spec.executable_name
        ));
    }
    let executable_bytes = fs::read(&executable)
        .map_err(|error| format!("read {} executable: {error}", spec.executable_name))?;
    OpenOptions::new()
        .write(true)
        .create_new(true)
        .open(target)
        .map_err(|error| format!("create isolated agent target {}: {error}", target.display()))?;
    let workspace_before = workspace_snapshot(workspace)?;
    let version = run_process(
        &executable,
        spec.version_argv.iter().map(ToString::to_string).collect(),
        workspace,
        scratch,
        Vec::new(),
        false,
        Some(kind),
        None,
        timeout_seconds,
    )?;
    let version_text = String::from_utf8_lossy(&version.stdout).trim().to_owned();
    let minimum_version =
        parse_version(spec.minimum_version).expect("adapter minimum versions are complete numbers");
    let adapter_version = match kind {
        AgentKind::Codex => version_text
            .strip_prefix("codex-cli ")
            .or_else(|| version_text.strip_prefix("codex ")),
        AgentKind::Omp => version_text.strip_prefix("omp/"),
    }
    .filter(|version| is_at_least(version, minimum_version));
    let Some(adapter_version) = adapter_version else {
        return Err(format!(
            "unsupported {} version `{version_text}` (exit {:?}): {}",
            spec.executable_name,
            version.status,
            String::from_utf8_lossy(&version.stderr).trim()
        ));
    };
    let arguments = match kind {
        AgentKind::Codex => vec![
            "exec",
            "--strict-config",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--skip-git-repo-check",
            "--sandbox",
            "workspace-write",
            "--color",
            "never",
            "--cd",
            workspace.to_str().ok_or("workspace is not UTF-8")?,
            "-",
        ]
        .into_iter()
        .map(str::to_owned)
        .collect(),
        AgentKind::Omp => {
            let overlay = scratch.join("omp.yaml");
            fs::write(&overlay, "startup:\n  checkUpdate: false\n")
                .map_err(|error| format!("write OMP overlay: {error}"))?;
            vec![
                "-p".to_owned(),
                "--cwd".to_owned(),
                workspace.display().to_string(),
                "--no-session".to_owned(),
                "--no-rules".to_owned(),
                "--no-skills".to_owned(),
                "--no-extensions".to_owned(),
                "--no-lsp".to_owned(),
                "--no-pty".to_owned(),
                "--no-title".to_owned(),
                "--tools".to_owned(),
                "read,grep,glob,edit,write".to_owned(),
                "--approval-mode".to_owned(),
                "yolo".to_owned(),
                "--max-time".to_owned(),
                format!("{timeout_seconds}s"),
                "--config".to_owned(),
                overlay.display().to_string(),
                String::from_utf8(prompt.clone()).map_err(|_| "OMP prompt is not UTF-8")?,
            ]
        }
    };
    let stdin = if spec.prompt_on_stdin {
        prompt.clone()
    } else {
        Vec::new()
    };
    let started = Instant::now();
    let completed = run_process(
        &executable,
        arguments,
        workspace,
        scratch,
        stdin,
        true,
        Some(kind),
        Some(target),
        timeout_seconds,
    )?;
    let duration_ms = started.elapsed().as_millis().min(u128::from(u64::MAX)) as u64;
    if fs::read(&executable)
        .map_err(|error| format!("re-read {} executable: {error}", spec.executable_name))?
        != executable_bytes
    {
        return Err(format!(
            "{} executable changed during generation",
            spec.executable_name
        ));
    }
    let target_relative = target
        .strip_prefix(workspace)
        .map_err(|_| "agent target escaped workspace")?;
    let mut before = workspace_before;
    let mut after = workspace_snapshot(workspace)?;
    before.remove(target_relative);
    after.remove(target_relative);
    if before != after {
        return Err("agent modified an unauthorized workspace path".to_owned());
    }
    if completed.timed_out || completed.status != Some(0) {
        return Err(format!(
            "{} failed with status {:?}: {}",
            spec.executable_name,
            completed.status,
            String::from_utf8_lossy(&completed.stderr).trim()
        ));
    }
    let metadata = fs::symlink_metadata(target)
        .map_err(|error| format!("agent did not write target {}: {error}", target.display()))?;
    if metadata.file_type().is_symlink() || !metadata.is_file() || metadata.nlink() != 1 {
        return Err("agent candidate must be a regular single-link file".to_owned());
    }
    if metadata.len() > 1024 * 1024 {
        return Err("agent implementation exceeds 1 MiB".to_owned());
    }
    let mut implementation = fs::read(target)
        .map_err(|error| format!("read agent target {}: {error}", target.display()))?;
    if implementation.is_empty() {
        return Err(format!("agent did not write target {}", target.display()));
    }
    while implementation.last() == Some(&b'\n') {
        implementation.pop();
    }
    implementation.push(b'\n');
    Ok(AgentRunCandidate {
        implementation,
        executable: executable.clone(),
        executable_hash: format!("sha256:{}", sha256_hex(&executable_bytes)),
        adapter_version: adapter_version.to_owned(),
        prompt_hash: format!("sha256:{}", sha256_hex(&prompt)),
        stdout: completed.stdout,
        stderr: completed.stderr,
        exit_code: completed.status,
        timed_out: completed.timed_out,
        duration_ms,
        environment_names: agent_environment_names(kind),
    })
}

fn workspace_snapshot(root: &Path) -> Result<BTreeMap<PathBuf, (u8, u32, u64, String)>, String> {
    let mut snapshot = BTreeMap::new();
    let mut pending = vec![root.to_path_buf()];
    while let Some(directory) = pending.pop() {
        let mut entries = fs::read_dir(&directory)
            .map_err(|error| format!("read agent workspace {}: {error}", directory.display()))?
            .collect::<Result<Vec<_>, _>>()
            .map_err(|error| format!("read agent workspace entry: {error}"))?;
        entries.sort_by_key(std::fs::DirEntry::file_name);
        for entry in entries {
            let path = entry.path();
            let relative = path
                .strip_prefix(root)
                .map_err(|_| "agent workspace path escaped root")?
                .to_path_buf();
            let metadata = fs::symlink_metadata(&path)
                .map_err(|error| format!("stat agent workspace {}: {error}", path.display()))?;
            if metadata.file_type().is_symlink() {
                return Err(format!(
                    "agent workspace contains a symlink: {}",
                    path.display()
                ));
            }
            if metadata.is_dir() {
                snapshot.insert(relative, (1, metadata.mode(), 0, String::new()));
                pending.push(path);
            } else if metadata.is_file() && metadata.nlink() == 1 {
                let bytes = fs::read(&path)
                    .map_err(|error| format!("read agent workspace {}: {error}", path.display()))?;
                snapshot.insert(
                    relative,
                    (0, metadata.mode(), bytes.len() as u64, sha256_hex(&bytes)),
                );
            } else {
                return Err(format!(
                    "agent workspace entry is not a regular single-link file: {}",
                    path.display()
                ));
            }
        }
    }
    Ok(snapshot)
}

fn agent_environment_names(kind: AgentKind) -> Vec<String> {
    let mut names = vec![
        "HOME".to_owned(),
        "PATH".to_owned(),
        "PYTHONDONTWRITEBYTECODE".to_owned(),
        "TMPDIR".to_owned(),
    ];
    for name in [
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
        "HTTPS_PROXY",
        "HTTP_PROXY",
        "NO_PROXY",
    ] {
        if std::env::var_os(name).is_some() {
            names.push(name.to_owned());
        }
    }
    let home = std::env::var_os("HOME").map(PathBuf::from);
    match kind {
        AgentKind::Codex => {
            for name in ["CODEX_API_KEY", "CODEX_ACCESS_TOKEN"] {
                if std::env::var_os(name).is_some() {
                    names.push(name.to_owned());
                }
            }
            if std::env::var_os("CODEX_HOME")
                .map(PathBuf::from)
                .or_else(|| home.map(|home| home.join(".codex")))
                .is_some_and(|path| path.is_dir())
            {
                names.push("CODEX_HOME".to_owned());
            }
        }
        AgentKind::Omp => {
            if std::env::var_os("PI_CODING_AGENT_DIR")
                .map(PathBuf::from)
                .or_else(|| home.map(|home| home.join(".omp/agent")))
                .is_some_and(|path| path.is_dir())
            {
                names.push("PI_CODING_AGENT_DIR".to_owned());
            }
        }
    }
    names.sort();
    names
}

fn run_process(
    executable: &Path,
    arguments: Vec<String>,
    workspace: &Path,
    scratch: &Path,
    stdin: Vec<u8>,
    network: bool,
    credential_kind: Option<AgentKind>,
    writable_target: Option<&Path>,
    timeout_seconds: u16,
) -> Result<crate::sandbox::CompletedProcess, String> {
    let mut read_only = vec![executable.to_path_buf()];
    let mut environment = BTreeMap::from([
        ("HOME".to_owned(), scratch.display().to_string()),
        ("TMPDIR".to_owned(), scratch.display().to_string()),
        ("PATH".to_owned(), "/usr/bin:/bin".to_owned()),
        ("PYTHONDONTWRITEBYTECODE".to_owned(), "1".to_owned()),
    ]);
    for name in [
        "SSL_CERT_FILE",
        "SSL_CERT_DIR",
        "HTTPS_PROXY",
        "HTTP_PROXY",
        "NO_PROXY",
    ] {
        if let Some(value) = std::env::var_os(name) {
            let value = value
                .into_string()
                .map_err(|_| format!("{name} is not valid UTF-8"))?;
            if matches!(name, "SSL_CERT_FILE" | "SSL_CERT_DIR") {
                let path = fs::canonicalize(&value)
                    .map_err(|error| format!("resolve {name} `{value}`: {error}"))?;
                read_only.push(path);
            }
            environment.insert(name.to_owned(), value);
        }
    }
    if let Some(kind) = credential_kind {
        let home = std::env::var_os("HOME").map(PathBuf::from);
        match kind {
            AgentKind::Codex => {
                for name in ["CODEX_API_KEY", "CODEX_ACCESS_TOKEN"] {
                    if let Some(value) = std::env::var_os(name) {
                        environment.insert(
                            name.to_owned(),
                            value
                                .into_string()
                                .map_err(|_| format!("{name} is not valid UTF-8"))?,
                        );
                    }
                }
                let credential_root = std::env::var_os("CODEX_HOME")
                    .map(PathBuf::from)
                    .or_else(|| home.map(|home| home.join(".codex")));
                if let Some(root) = credential_root.filter(|root| root.is_dir()) {
                    let root = fs::canonicalize(root)
                        .map_err(|error| format!("resolve CODEX_HOME: {error}"))?;
                    read_only.push(root.clone());
                    environment.insert("CODEX_HOME".to_owned(), root.display().to_string());
                }
            }
            AgentKind::Omp => {
                let credential_root = std::env::var_os("PI_CODING_AGENT_DIR")
                    .map(PathBuf::from)
                    .or_else(|| home.as_ref().map(|home| home.join(".omp/agent")));
                if network {
                    if let Some(root) = credential_root.filter(|root| root.is_dir()) {
                        let isolated = scratch.join("omp-agent");
                        fs::create_dir_all(&isolated)
                            .map_err(|error| format!("create isolated OMP state: {error}"))?;
                        for name in ["config.yml", "agent.db"] {
                            let source = root.join(name);
                            if source.is_file() {
                                fs::copy(&source, isolated.join(name)).map_err(|error| {
                                    format!("copy isolated OMP state `{name}`: {error}")
                                })?;
                            }
                        }
                        environment.insert(
                            "PI_CODING_AGENT_DIR".to_owned(),
                            isolated.display().to_string(),
                        );
                    }
                    if let Some(home) = home {
                        let natives = home.join(".omp/natives");
                        if natives.is_dir() {
                            read_only.push(
                                fs::canonicalize(&natives).map_err(|error| {
                                    format!("resolve OMP native addons: {error}")
                                })?,
                            );
                            environment.insert("HOME".to_owned(), home.display().to_string());
                        }
                    }
                }
            }
        }
    }
    if network {
        if let Ok(resolver) = fs::canonicalize("/etc/resolv.conf") {
            read_only.push(resolver);
        }
    }
    read_only.push(workspace.to_path_buf());
    let mut writable = vec![scratch.to_path_buf()];
    if let Some(target) = writable_target {
        writable.push(target.to_path_buf());
    }
    if credential_kind == Some(AgentKind::Omp) {
        let argument_bytes = arguments.iter().map(|value| value.len() + 1).sum::<usize>()
            + environment
                .iter()
                .map(|(name, value)| name.len() + value.len() + 2)
                .sum::<usize>();
        let argument_max = unsafe { libc::sysconf(libc::_SC_ARG_MAX) };
        if argument_max <= 0 || argument_bytes.saturating_add(64 * 1024) > argument_max as usize {
            return Err("OMP prompt exceeds the host argument-size limit".to_owned());
        }
    }
    let address_space_bytes = if credential_kind == Some(AgentKind::Omp) {
        128 * 1024 * 1024 * 1024
    } else {
        4 * 1024 * 1024 * 1024
    };
    let writable_bytes = if credential_kind == Some(AgentKind::Omp) {
        512 * 1024 * 1024
    } else {
        64 * 1024 * 1024
    };
    run(&SandboxSpec {
        program: executable.to_path_buf(),
        arguments,
        cwd: workspace.to_path_buf(),
        environment,
        stdin,
        binds: BindMounts {
            read_only,
            writable,
        },
        network: if network {
            NetworkAccess::Enabled
        } else {
            NetworkAccess::Disabled
        },
        limits: ResourceLimits {
            cpu_time: Duration::from_secs(timeout_seconds.into()),
            address_space_bytes,
            process_count: 64,
            open_files: 256,
            file_size_bytes: writable_bytes,
            wall_time: Duration::from_secs(timeout_seconds.into()),
            stream_limit_bytes: 16 * 1024 * 1024,
            writable_bytes,
        },
    })
    .map_err(|error| error.to_string())
}
