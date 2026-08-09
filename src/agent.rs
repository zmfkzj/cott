use std::collections::{BTreeMap, BTreeSet};
use std::fs;
use std::os::unix::fs::MetadataExt;
use std::path::{Path, PathBuf};
use std::time::Duration;

use crate::hash::sha256_hex;
use crate::sandbox::{BindMounts, NetworkAccess, ResourceLimits, SandboxSpec, run};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum AgentKind {
    Codex,
    Omp,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct AdapterSpec {
    pub executable_name: &'static str,
    pub exact_version: &'static str,
    pub version_argv: &'static [&'static str],
    pub argv_template: &'static [&'static str],
    pub prompt_on_stdin: bool,
}

pub const CODEX: AdapterSpec = AdapterSpec {
    executable_name: "codex",
    exact_version: "0.147.0",
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
    exact_version: "17.2.12",
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
}

pub fn render_prompt(
    symbol: &str,
    selected_ir: &[u8],
    docs: &str,
    type_declarations: &str,
    bound_symbols: &str,
    existing: Option<&[u8]>,
    rules: Option<&[u8]>,
    write_path: &Path,
) -> Result<Vec<u8>, String> {
    if rules.is_some_and(|rules| rules.len() > 1024 * 1024) || selected_ir.len() > 1024 * 1024 {
        return Err("agent prompt input exceeds 1 MiB".to_owned());
    }
    let mut prompt = format!("COTT_AGENT_PROMPT_V1\n\nTARGET\nSymbol: {symbol}\nWrite path: {}\n\nCANONICAL IR\n{}\n\nDOCS CONTRACTS EFFECTS\n{docs}\n\nRELEVANT TYPES\n{type_declarations}\n\nBOUND SYMBOLS IMPORT RULES\n{bound_symbols}\n", write_path.display(), String::from_utf8_lossy(selected_ir)).into_bytes();
    if let Some(existing) = existing {
        prompt.extend_from_slice(b"\nEXISTING IMPLEMENTATION\n");
        prompt.extend_from_slice(existing);
        prompt.push(b'\n');
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
    let sandbox_executable = workspace.join(".cott-agent-executable");
    fs::copy(&executable, &sandbox_executable).map_err(|error| {
        format!(
            "copy {} executable into workspace: {error}",
            spec.executable_name
        )
    })?;
    fs::set_permissions(
        &sandbox_executable,
        fs::metadata(&executable)
            .map_err(|error| format!("stat {} executable: {error}", spec.executable_name))?
            .permissions(),
    )
    .map_err(|error| {
        format!(
            "set copied {} executable mode: {error}",
            spec.executable_name
        )
    })?;
    let allowed_workspace_paths = fs::read_dir(workspace)
        .map_err(|error| format!("read agent workspace: {error}"))?
        .map(|entry| entry.map(|entry| entry.path()))
        .collect::<Result<BTreeSet<_>, _>>()
        .map_err(|error| format!("read agent workspace entry: {error}"))?;
    let version = run_process(
        &sandbox_executable,
        spec.version_argv.iter().map(ToString::to_string).collect(),
        workspace,
        scratch,
        Vec::new(),
        false,
        Some(kind),
        timeout_seconds,
    )?;
    let version_text = String::from_utf8_lossy(&version.stdout).trim().to_owned();
    let valid_version = match kind {
        AgentKind::Codex => version_text == "codex-cli 0.147.0" || version_text == "codex 0.147.0",
        AgentKind::Omp => version_text == "omp/17.2.12",
    };
    if !valid_version {
        return Err(format!(
            "unsupported {} version `{version_text}` (exit {:?}): {}",
            spec.executable_name,
            version.status,
            String::from_utf8_lossy(&version.stderr).trim()
        ));
    }
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
    let completed = run_process(
        &sandbox_executable,
        arguments,
        workspace,
        scratch,
        stdin,
        true,
        Some(kind),
        timeout_seconds,
    )?;
    for entry in
        fs::read_dir(workspace).map_err(|error| format!("read agent workspace: {error}"))?
    {
        let entry = entry.map_err(|error| format!("read agent workspace entry: {error}"))?;
        if !allowed_workspace_paths.contains(&entry.path()) && entry.path() != target {
            return Err(format!(
                "agent modified an unauthorized workspace path: {}",
                entry.path().display()
            ));
        }
    }
    if completed.timed_out || completed.status != Some(0) {
        return Err(format!("{} failed", spec.executable_name));
    }
    let metadata = fs::symlink_metadata(target)
        .map_err(|error| format!("agent did not write target {}: {error}", target.display()))?;
    if metadata.file_type().is_symlink() || !metadata.is_file() || metadata.nlink() != 1 {
        return Err("agent candidate must be a regular single-link file".to_owned());
    }
    if metadata.len() > 1024 * 1024 {
        return Err("agent implementation exceeds 1 MiB".to_owned());
    }
    let implementation = fs::read(target)
        .map_err(|error| format!("read agent target {}: {error}", target.display()))?;
    Ok(AgentRunCandidate {
        implementation,
        executable: executable.clone(),
        executable_hash: format!(
            "sha256:{}",
            sha256_hex(&fs::read(&executable).map_err(|error| error.to_string())?)
        ),
        adapter_version: spec.exact_version.to_owned(),
        prompt_hash: format!("sha256:{}", sha256_hex(&prompt)),
        stdout: completed.stdout,
        stderr: completed.stderr,
        exit_code: completed.status,
        timed_out: completed.timed_out,
    })
}

fn run_process(
    executable: &Path,
    arguments: Vec<String>,
    workspace: &Path,
    scratch: &Path,
    stdin: Vec<u8>,
    network: bool,
    credential_kind: Option<AgentKind>,
    timeout_seconds: u16,
) -> Result<crate::sandbox::CompletedProcess, String> {
    let mut environment = BTreeMap::from([
        ("HOME".to_owned(), scratch.display().to_string()),
        ("TMPDIR".to_owned(), scratch.display().to_string()),
        ("PATH".to_owned(), "/usr/bin:/bin".to_owned()),
        ("PYTHONDONTWRITEBYTECODE".to_owned(), "1".to_owned()),
    ]);
    if let Some(kind) = credential_kind {
        let home = std::env::var_os("HOME").map(PathBuf::from);
        match kind {
            AgentKind::Codex => {
                let credential_root = std::env::var_os("CODEX_HOME")
                    .map(PathBuf::from)
                    .or_else(|| home.map(|home| home.join(".codex")));
                if let Some(root) = credential_root.filter(|root| root.is_dir()) {
                    environment.insert("CODEX_HOME".to_owned(), root.display().to_string());
                }
            }
            AgentKind::Omp => {
                let credential_root = std::env::var_os("PI_CODING_AGENT_DIR")
                    .map(PathBuf::from)
                    .or_else(|| home.map(|home| home.join(".omp/agent")));
                if let Some(root) = credential_root.filter(|root| root.is_dir()) {
                    environment
                        .insert("PI_CODING_AGENT_DIR".to_owned(), root.display().to_string());
                }
            }
        }
    }
    run(&SandboxSpec {
        program: executable.to_path_buf(),
        arguments,
        cwd: workspace.to_path_buf(),
        environment,
        stdin,
        binds: BindMounts {
            read_only: Vec::new(),
            writable: vec![workspace.to_path_buf(), scratch.to_path_buf()],
        },
        network: if network {
            NetworkAccess::Enabled
        } else {
            NetworkAccess::Disabled
        },
        limits: ResourceLimits {
            cpu_time: Duration::from_secs(timeout_seconds.into()),
            address_space_bytes: 4 * 1024 * 1024 * 1024,
            process_count: 64,
            open_files: 256,
            file_size_bytes: 64 * 1024 * 1024,
            wall_time: Duration::from_secs(timeout_seconds.into()),
            stream_limit_bytes: 16 * 1024 * 1024,
        },
    })
    .map_err(|error| error.to_string())
}
