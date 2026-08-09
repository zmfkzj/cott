use std::ffi::OsString;
use std::fs;
use std::os::unix::fs::MetadataExt;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};
use std::sync::{Mutex, MutexGuard};

use cott::agent::{AgentKind, AgentRunCandidate, run_agent};

static NEXT: AtomicU64 = AtomicU64::new(0);
static ENV_LOCK: Mutex<()> = Mutex::new(());

struct Temp {
    root: PathBuf,
}
impl Temp {
    fn new() -> Self {
        let root = std::env::temp_dir().join(format!(
            "cott-agent-test-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir(&root).expect("create temporary root");
        Self { root }
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.root);
    }
}

struct EnvRestore {
    saved: Vec<(&'static str, Option<OsString>)>,
}
impl EnvRestore {
    fn controlled(scratch: &Path, executable: &Path) -> Self {
        let cert_dir = scratch.join("certs");
        let codex_home = scratch.join("codex-home");
        let omp_home = scratch.join("omp-home");
        fs::create_dir(&cert_dir).expect("cert directory");
        fs::create_dir(&codex_home).expect("Codex home");
        fs::create_dir(&omp_home).expect("OMP home");
        let values = [
            ("HOME", scratch.display().to_string()),
            ("SSL_CERT_FILE", executable.display().to_string()),
            ("SSL_CERT_DIR", cert_dir.display().to_string()),
            ("HTTPS_PROXY", "https://proxy.invalid".to_owned()),
            ("HTTP_PROXY", "http://proxy.invalid".to_owned()),
            ("NO_PROXY", "localhost".to_owned()),
            ("CODEX_API_KEY", "codex-secret-api-key".to_owned()),
            ("CODEX_ACCESS_TOKEN", "codex-secret-access-token".to_owned()),
            ("CODEX_HOME", codex_home.display().to_string()),
            ("PI_CODING_AGENT_DIR", omp_home.display().to_string()),
        ];
        let mut saved = Vec::with_capacity(values.len());
        for (name, value) in values {
            saved.push((name, std::env::var_os(name)));
            unsafe { std::env::set_var(name, value) };
        }
        Self { saved }
    }
}
impl Drop for EnvRestore {
    fn drop(&mut self) {
        for (name, value) in self.saved.drain(..).rev() {
            unsafe {
                if let Some(value) = value {
                    std::env::set_var(name, value);
                } else {
                    std::env::remove_var(name);
                }
            }
        }
    }
}

fn fixture() -> (Temp, PathBuf, PathBuf, PathBuf) {
    let temp = Temp::new();
    let workspace = temp.root.join("workspace");
    let scratch = temp.root.join("scratch");
    fs::create_dir(&workspace).expect("workspace");
    fs::create_dir(&scratch).expect("scratch");
    (
        temp,
        workspace.clone(),
        scratch,
        workspace.join("implementation.py"),
    )
}

fn fake_adapter(workspace: &Path, version: &str, body: &str) -> PathBuf {
    let executable = workspace.join("fake-agent");
    let script = format!(
        "#!/bin/sh\nif [ \"$1\" = \"--version\" ]; then printf '%s\\n' '{version}'; exit 0; fi\n{body}\n"
    );
    fs::write(&executable, script).expect("write fake agent");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&executable, fs::Permissions::from_mode(0o755))
            .expect("make fake agent executable");
    }
    executable
}

fn capture_body(exit: Option<i32>) -> String {
    let status = exit.map_or_else(String::new, |code| format!("exit {code}"));
    format!(
        r#"unset PWD
{{
printf 'argv\n'
for arg do printf '<%s>\n' "$arg"; done
printf 'stdin\n'
cat
printf '\nenv\n'
/usr/bin/env | while IFS='=' read -r name value; do printf '%s\n' "$name"; done | sort
}} > implementation.py
printf blocked > sibling.py 2>/dev/null || true
{status}"#
    )
}

fn expected_capture(args: &[String], stdin: &[u8], env_names: &[&str]) -> Vec<u8> {
    let mut output = String::from("argv\n");
    for arg in args {
        output.push('<');
        output.push_str(arg);
        output.push_str(">\n");
    }
    output.push_str("stdin\n");
    output.push_str(&String::from_utf8_lossy(stdin));
    output.push_str("\nenv\n");
    for name in env_names {
        output.push_str(name);
        output.push('\n');
    }
    output.into_bytes()
}

fn run_or_skip(
    kind: AgentKind,
    executable: PathBuf,
    workspace: &Path,
    scratch: &Path,
    target: &Path,
    prompt: &[u8],
) -> Option<Result<AgentRunCandidate, String>> {
    let result = run_agent(
        kind,
        executable,
        workspace,
        scratch,
        target,
        prompt.to_vec(),
        10,
    );
    if matches!(
        &result,
        Err(error) if error.contains("bubblewrap") || error.contains("bwrap:")
    ) {
        None
    } else {
        Some(result)
    }
}

fn _hold_env_lock() -> MutexGuard<'static, ()> {
    ENV_LOCK
        .lock()
        .unwrap_or_else(std::sync::PoisonError::into_inner)
}

#[test]
fn codex_golden_argv_stdin_environment_and_target_write() {
    let (_temp, workspace, scratch, target) = fixture();
    let executable = fake_adapter(&workspace, "codex-cli 0.147.0", &capture_body(None));
    let _lock = _hold_env_lock();
    let _environment = EnvRestore::controlled(&scratch, &executable);
    let prompt = b"codex prompt $(touch sibling.py)\n";
    let Some(result) = run_or_skip(
        AgentKind::Codex,
        executable,
        &workspace,
        &scratch,
        &target,
        prompt,
    ) else {
        return;
    };
    let candidate = result.expect("Codex run");
    let expected_args = vec![
        "exec".to_owned(),
        "--strict-config".to_owned(),
        "--ephemeral".to_owned(),
        "--ignore-user-config".to_owned(),
        "--ignore-rules".to_owned(),
        "--skip-git-repo-check".to_owned(),
        "--sandbox".to_owned(),
        "workspace-write".to_owned(),
        "--color".to_owned(),
        "never".to_owned(),
        "--cd".to_owned(),
        workspace.display().to_string(),
        "-".to_owned(),
    ];
    let expected_names = [
        "CODEX_ACCESS_TOKEN",
        "CODEX_API_KEY",
        "CODEX_HOME",
        "HOME",
        "HTTPS_PROXY",
        "HTTP_PROXY",
        "NO_PROXY",
        "PATH",
        "PYTHONDONTWRITEBYTECODE",
        "SSL_CERT_DIR",
        "SSL_CERT_FILE",
        "TMPDIR",
    ];
    assert_eq!(
        candidate.implementation,
        expected_capture(&expected_args, prompt, &expected_names)
    );
    assert_eq!(
        candidate.environment_names,
        expected_names
            .iter()
            .map(|name| (*name).to_owned())
            .collect::<Vec<_>>()
    );
    assert!(
        !candidate
            .implementation
            .windows(b"codex-secret-api-key".len())
            .any(|window| window == b"codex-secret-api-key")
    );
    assert!(
        !candidate
            .implementation
            .windows(b"codex-secret-access-token".len())
            .any(|window| window == b"codex-secret-access-token")
    );
    let metadata = fs::symlink_metadata(&target).expect("target metadata");
    assert!(metadata.is_file() && !metadata.file_type().is_symlink() && metadata.nlink() == 1);
    assert!(!workspace.join("sibling.py").exists());
}

#[test]
fn omp_golden_argv_prompt_environment_and_target_write() {
    let (_temp, workspace, scratch, target) = fixture();
    let executable = fake_adapter(&workspace, "omp/17.2.12", &capture_body(None));
    let _lock = _hold_env_lock();
    let _environment = EnvRestore::controlled(&scratch, &executable);
    let prompt = b"omp prompt $(touch sibling.py)";
    let Some(result) = run_or_skip(
        AgentKind::Omp,
        executable,
        &workspace,
        &scratch,
        &target,
        prompt,
    ) else {
        return;
    };
    let candidate = result.expect("OMP run");
    let expected_args = vec![
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
        "10s".to_owned(),
        "--config".to_owned(),
        scratch.join("omp.yaml").display().to_string(),
        String::from_utf8(prompt.to_vec()).expect("prompt UTF-8"),
    ];
    let expected_names = [
        "HOME",
        "HTTPS_PROXY",
        "HTTP_PROXY",
        "NO_PROXY",
        "PATH",
        "PI_CODING_AGENT_DIR",
        "PYTHONDONTWRITEBYTECODE",
        "SSL_CERT_DIR",
        "SSL_CERT_FILE",
        "TMPDIR",
    ];
    assert_eq!(
        candidate.implementation,
        expected_capture(&expected_args, &[], &expected_names)
    );
    assert_eq!(
        candidate.environment_names,
        expected_names
            .iter()
            .map(|name| (*name).to_owned())
            .collect::<Vec<_>>()
    );
    assert!(
        !candidate
            .implementation
            .windows(b"codex-secret-api-key".len())
            .any(|window| window == b"codex-secret-api-key")
    );
    assert!(
        !candidate
            .implementation
            .windows(b"codex-secret-access-token".len())
            .any(|window| window == b"codex-secret-access-token")
    );
    let metadata = fs::symlink_metadata(&target).expect("target metadata");
    assert!(metadata.is_file() && !metadata.file_type().is_symlink() && metadata.nlink() == 1);
    assert!(!workspace.join("sibling.py").exists());
}

#[test]
fn version_mismatch_is_a_failure() {
    let (_temp, workspace, scratch, target) = fixture();
    let executable = fake_adapter(&workspace, "omp/17.2.11", "exit 0");
    let _lock = _hold_env_lock();
    let _environment = EnvRestore::controlled(&scratch, &executable);
    let Some(result) = run_or_skip(
        AgentKind::Omp,
        executable,
        &workspace,
        &scratch,
        &target,
        b"prompt",
    ) else {
        return;
    };
    assert!(
        result
            .expect_err("version mismatch must fail")
            .contains("unsupported omp version")
    );
}

#[test]
fn nonzero_exit_is_a_failure() {
    let (_temp, workspace, scratch, target) = fixture();
    let executable = fake_adapter(&workspace, "omp/17.2.12", &capture_body(Some(17)));
    let _lock = _hold_env_lock();
    let _environment = EnvRestore::controlled(&scratch, &executable);
    let Some(result) = run_or_skip(
        AgentKind::Omp,
        executable,
        &workspace,
        &scratch,
        &target,
        b"prompt",
    ) else {
        return;
    };
    assert!(
        result
            .expect_err("nonzero exit must fail")
            .contains("omp failed")
    );
}

#[test]
fn zero_exit_without_target_write_is_a_failure() {
    let (_temp, workspace, scratch, target) = fixture();
    let executable = fake_adapter(&workspace, "omp/17.2.12", "exit 0");
    let _lock = _hold_env_lock();
    let _environment = EnvRestore::controlled(&scratch, &executable);
    let Some(result) = run_or_skip(
        AgentKind::Omp,
        executable,
        &workspace,
        &scratch,
        &target,
        b"prompt",
    ) else {
        return;
    };
    assert!(
        result
            .expect_err("no target write must fail")
            .contains("did not write target")
    );
}

#[test]
fn omp_prompt_over_argument_limit_is_rejected_before_execution() {
    let (_temp, workspace, scratch, target) = fixture();
    let executable = fake_adapter(&workspace, "omp/17.2.12", "exit 0");
    let _lock = _hold_env_lock();
    let _environment = EnvRestore::controlled(&scratch, &executable);
    let prompt = vec![b'x'; 16 * 1024 * 1024];
    let Some(result) = run_or_skip(
        AgentKind::Omp,
        executable,
        &workspace,
        &scratch,
        &target,
        &prompt,
    ) else {
        return;
    };
    assert!(
        result
            .expect_err("oversized OMP prompt must fail")
            .contains("argument-size limit")
    );
}

#[cfg(unix)]
#[test]
fn preexisting_hardlink_target_is_rejected() {
    let (_temp, workspace, scratch, target) = fixture();
    let other = workspace.join("other.py");
    fs::write(&other, b"existing").expect("other file");
    fs::hard_link(&other, &target).expect("hard link target");
    let executable = fake_adapter(&workspace, "omp/17.2.12", "exit 0");
    let result = run_agent(
        AgentKind::Omp,
        executable,
        &workspace,
        &scratch,
        &target,
        b"prompt".to_vec(),
        10,
    );
    assert!(
        result
            .expect_err("hardlink target must fail")
            .contains("create isolated agent target")
    );
}

#[cfg(unix)]
#[test]
fn preexisting_symlink_target_is_rejected() {
    use std::os::unix::fs::symlink;

    let (_temp, workspace, scratch, target) = fixture();
    let other = workspace.join("other.py");
    fs::write(&other, b"existing").expect("other file");
    symlink(&other, &target).expect("symlink target");
    let executable = fake_adapter(&workspace, "omp/17.2.12", "exit 0");
    let result = run_agent(
        AgentKind::Omp,
        executable,
        &workspace,
        &scratch,
        &target,
        b"prompt".to_vec(),
        10,
    );
    assert!(
        result
            .expect_err("symlink target must fail")
            .contains("create isolated agent target")
    );
}
