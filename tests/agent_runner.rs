use std::ffi::OsString;
use std::fs;
use std::os::unix::fs::MetadataExt;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::{Arc, Mutex, MutexGuard};

use cott::agent::{AgentKind, AgentRunCandidate, run_agent};
use cott::hash::sha256_hex;

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
            ("ANTHROPIC_API_KEY", "anthropic-secret-api-key".to_owned()),
            (
                "ANTHROPIC_AUTH_TOKEN",
                "anthropic-secret-auth-token".to_owned(),
            ),
            ("ANTHROPIC_BASE_URL", "https://anthropic.invalid".to_owned()),
            ("CLAUDE_CODE_OAUTH_TOKEN", "claude-oauth-token".to_owned()),
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

fn fake_adapter_with_version_probe(workspace: &Path, version_probe: &str, body: &str) -> PathBuf {
    let executable = workspace.join("fake-agent");
    let script =
        format!("#!/bin/sh\nif [ \"$1\" = \"--version\" ]; then\n{version_probe}\nfi\n{body}\n");
    fs::write(&executable, script).expect("write fake agent");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&executable, fs::Permissions::from_mode(0o755))
            .expect("make fake agent executable");
    }
    executable
}

fn fake_adapter(workspace: &Path, version: &str, body: &str) -> PathBuf {
    fake_adapter_with_version_probe(
        workspace,
        &format!("printf '%s\\n' '{version}'\nexit 0"),
        body,
    )
}

fn fake_claude_adapter(workspace: &Path, version: &str, body: &str) -> PathBuf {
    fake_adapter_with_version_probe(
        workspace,
        &format!(
            r#"[ -z "${{ANTHROPIC_API_KEY+x}}" ] || exit 2
printf '%s\n' '{version}'
exit 0"#
        ),
        body,
    )
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

fn claude_capture_body() -> String {
    format!(
        r#"[ "${{ANTHROPIC_API_KEY-}}" = anthropic-secret-api-key ] &&
[ "$CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC" = 1 ] &&
[ "$DISABLE_TELEMETRY" = 1 ] &&
[ "$DISABLE_ERROR_REPORTING" = 1 ] &&
[ -z "${{ANTHROPIC_AUTH_TOKEN+x}}" ] &&
[ -z "${{ANTHROPIC_BASE_URL+x}}" ] &&
[ -z "${{CLAUDE_CODE_OAUTH_TOKEN+x}}" ] || exit 2
{}
printf '%s' '{{"type":"result","subtype":"success","is_error":false,"result":"done"}}'"#,
        capture_body(None)
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
    run_or_skip_with_timeout(kind, executable, workspace, scratch, target, prompt, 10)
}

fn run_or_skip_with_timeout(
    kind: AgentKind,
    executable: PathBuf,
    workspace: &Path,
    scratch: &Path,
    target: &Path,
    prompt: &[u8],
    timeout_seconds: u16,
) -> Option<Result<AgentRunCandidate, String>> {
    let result = run_agent(
        kind,
        executable,
        workspace,
        scratch,
        target,
        prompt.to_vec(),
        timeout_seconds,
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
    let executable = fake_adapter(&workspace, "codex-cli 0.147.1", &capture_body(None));
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
    assert_eq!(candidate.adapter_version, "0.147.1");
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
fn claude_golden_argv_stdin_environment_json_and_provenance() {
    let (_temp, workspace, scratch, target) = fixture();
    let executable = fake_claude_adapter(&workspace, "2.1.89", &claude_capture_body());
    let _lock = _hold_env_lock();
    let _environment = EnvRestore::controlled(&scratch, &executable);
    let prompt = b"claude prompt $(touch sibling.py); ' \" ` \xe2\x98\x83\n";
    let Some(result) = run_or_skip(
        AgentKind::Claude,
        executable.clone(),
        &workspace,
        &scratch,
        &target,
        prompt,
    ) else {
        return;
    };
    let candidate = result.expect("Claude run");
    let expected_args = vec![
        "--bare".to_owned(),
        "--print".to_owned(),
        "--input-format".to_owned(),
        "text".to_owned(),
        "--output-format".to_owned(),
        "json".to_owned(),
        "--permission-mode".to_owned(),
        "dontAsk".to_owned(),
        "--tools".to_owned(),
        "Read,Write".to_owned(),
        "--allowedTools".to_owned(),
        "Read,Write".to_owned(),
        "--disallowedTools".to_owned(),
        "Bash,Edit,Glob,Grep,WebFetch,WebSearch,Task,mcp__*".to_owned(),
        "--no-session-persistence".to_owned(),
    ];
    let expected_names = [
        "ANTHROPIC_API_KEY",
        "CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC",
        "DISABLE_ERROR_REPORTING",
        "DISABLE_TELEMETRY",
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
    assert_eq!(
        candidate.executable,
        fs::canonicalize(&executable).expect("executable path")
    );
    assert_eq!(
        candidate.executable_hash,
        format!(
            "sha256:{}",
            sha256_hex(&fs::read(&executable).expect("executable bytes"))
        )
    );
    assert_eq!(candidate.adapter_version, "2.1.89");
    assert_eq!(
        candidate.prompt_hash,
        format!("sha256:{}", sha256_hex(prompt))
    );
    assert_eq!(
        candidate.stdout,
        br#"{"type":"result","subtype":"success","is_error":false,"result":"done"}"#
    );
    assert_eq!(candidate.exit_code, Some(0));
    assert!(!candidate.timed_out);
    assert!(!workspace.join("sibling.py").exists());
    assert!(
        !candidate
            .implementation
            .windows(b"ANTHROPIC_AUTH_TOKEN".len())
            .any(|window| window == b"ANTHROPIC_AUTH_TOKEN")
    );
    assert!(
        !candidate
            .implementation
            .windows(b"anthropic-secret-api-key".len())
            .any(|window| window == b"anthropic-secret-api-key")
    );
}

#[test]
fn omp_golden_argv_prompt_environment_and_target_write() {
    let (_temp, workspace, scratch, target) = fixture();
    let body = format!(
        "printf isolated > \"$PI_CODING_AGENT_DIR/write-test\"\n{}",
        capture_body(None)
    );
    let executable = fake_adapter(&workspace, "omp/17.2.13", &body);
    let _lock = _hold_env_lock();
    let _environment = EnvRestore::controlled(&scratch, &executable);
    let omp_home = scratch.join("omp-home");
    fs::write(omp_home.join("config.yml"), "model: test\n").expect("OMP config");
    fs::write(omp_home.join("agent.db"), "credentials").expect("OMP credential database");
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
    let prompt_file = fs::canonicalize(&scratch)
        .expect("canonical scratch")
        .join("omp-prompt-0");
    assert_eq!(candidate.adapter_version, "17.2.13");
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
        format!("@{}", prompt_file.display()),
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
    assert_eq!(fs::read(&prompt_file).expect("OMP prompt"), prompt);
    let prompt_metadata = fs::symlink_metadata(&prompt_file).expect("OMP prompt metadata");
    assert!(
        prompt_metadata.is_file()
            && !prompt_metadata.file_type().is_symlink()
            && prompt_metadata.nlink() == 1
    );
    assert_eq!(
        candidate.prompt_hash,
        format!("sha256:{}", sha256_hex(prompt))
    );
    assert!(
        !candidate
            .implementation
            .windows(prompt.len())
            .any(|window| window == prompt)
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
    assert_eq!(
        fs::read_to_string(scratch.join("omp-agent/write-test")).expect("isolated OMP write"),
        "isolated"
    );
    assert!(!omp_home.join("write-test").exists());
}

#[test]
fn omp_large_prompt_uses_file_argv_without_e2big() {
    let (_temp, workspace, scratch, target) = fixture();
    let executable = fake_adapter(&workspace, "omp/17.2.13", &capture_body(None));
    let _lock = _hold_env_lock();
    let _environment = EnvRestore::controlled(&scratch, &executable);
    let prompt = vec![b'x'; 1024 * 1024];
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
    let candidate = result.expect("OMP large-prompt run");
    let prompt_file = fs::canonicalize(&scratch)
        .expect("canonical scratch")
        .join("omp-prompt-0");
    assert_eq!(fs::read(&prompt_file).expect("OMP prompt"), prompt);
    assert_eq!(
        candidate.prompt_hash,
        format!("sha256:{}", sha256_hex(&prompt))
    );
    assert!(
        candidate
            .implementation
            .windows(prompt.len())
            .all(|window| window != prompt)
    );
    assert!(
        candidate
            .implementation
            .windows(format!("@{}", prompt_file.display()).len())
            .any(|window| window == format!("@{}", prompt_file.display()).as_bytes())
    );
}

#[test]
fn normalizes_agent_candidate_to_one_trailing_newline() {
    let (_temp, workspace, scratch, target) = fixture();
    let executable = fake_adapter(
        &workspace,
        "omp/17.2.12",
        "printf 'def run() -> object:\\n    return None\\n\\n' > implementation.py",
    );
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
    assert_eq!(
        result.expect("OMP run").implementation,
        b"def run() -> object:\n    return None\n"
    );
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

#[test]
fn claude_rejects_error_json_result() {
    let (_temp, workspace, scratch, target) = fixture();
    let executable = fake_adapter(
        &workspace,
        "2.1.89",
        "printf implementation > implementation.py\nprintf '%s' '{\"type\":\"result\",\"subtype\":\"error\",\"is_error\":true,\"result\":\"no\"}'",
    );
    let Some(result) = run_or_skip(
        AgentKind::Claude,
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
            .expect_err("Claude error result must fail")
            .contains("claude returned an invalid result")
    );
}

#[test]
fn claude_rejects_malformed_and_multiple_version_tokens() {
    for version in ["2.1", "2.1.89 extra"] {
        let (_temp, workspace, scratch, target) = fixture();
        let executable = fake_adapter(&workspace, version, "exit 0");
        let Some(result) = run_or_skip(
            AgentKind::Claude,
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
                .expect_err("invalid Claude version must fail")
                .contains("unsupported claude version")
        );
    }
}

#[test]
fn claude_rejects_valid_version_with_nonzero_probe_status() {
    let (_temp, workspace, scratch, target) = fixture();
    let executable = fake_adapter_with_version_probe(
        &workspace,
        r#"[ -z "${ANTHROPIC_API_KEY+x}" ] || exit 2
printf '%s\n' '2.1.89'
exit 17"#,
        "exit 0",
    );
    let _lock = _hold_env_lock();
    let _environment = EnvRestore::controlled(&scratch, &executable);
    let Some(result) = run_or_skip(
        AgentKind::Claude,
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
            .expect_err("nonzero Claude version probe must fail")
            .contains("unsupported claude version")
    );
}

#[test]
fn claude_rejects_timed_out_version_probe() {
    let (_temp, workspace, scratch, target) = fixture();
    let executable = fake_adapter_with_version_probe(
        &workspace,
        r#"[ -z "${ANTHROPIC_API_KEY+x}" ] || exit 2
sleep 2"#,
        "exit 0",
    );
    let _lock = _hold_env_lock();
    let _environment = EnvRestore::controlled(&scratch, &executable);
    let Some(result) = run_or_skip_with_timeout(
        AgentKind::Claude,
        executable,
        &workspace,
        &scratch,
        &target,
        b"prompt",
        1,
    ) else {
        return;
    };
    assert!(
        result
            .expect_err("timed out Claude version probe must fail")
            .contains("sandbox process timed out")
    );
}

#[test]
fn claude_rejects_target_replacement_from_retained_descriptor() {
    for (name, initial_contents) in [("empty", ""), ("old", "printf old > implementation.py\n")] {
        let (_temp, workspace, scratch, target) = fixture();
        let body = format!(
            r#"{initial_contents}: > "$TMPDIR/replace-target"
sleep 1
printf '%s' '{{"type":"result","subtype":"success","is_error":false,"result":"done"}}'"#
        );
        let executable = fake_claude_adapter(&workspace, "2.1.89", &body);
        let _lock = _hold_env_lock();
        let _environment = EnvRestore::controlled(&scratch, &executable);
        let cancelled = Arc::new(AtomicBool::new(false));
        let replacement = {
            let cancelled = Arc::clone(&cancelled);
            let trigger = scratch.join("replace-target");
            let target = target.clone();
            std::thread::spawn(move || {
                while !trigger.exists() {
                    if cancelled.load(Ordering::Acquire) {
                        return false;
                    }
                    std::thread::sleep(std::time::Duration::from_millis(1));
                }
                let replacement = target.with_extension("replacement");
                fs::write(&replacement, b"replacement")
                    .and_then(|_| fs::rename(replacement, target))
                    .is_ok()
            })
        };
        let result = run_or_skip(
            AgentKind::Claude,
            executable,
            &workspace,
            &scratch,
            &target,
            b"prompt",
        );
        cancelled.store(true, Ordering::Release);
        let replaced = replacement.join().expect("replacement thread");
        let Some(result) = result else {
            return;
        };
        assert!(replaced, "{name} target was not replaced");
        assert!(
            result
                .expect_err("replaced target must fail")
                .contains("agent candidate must be a regular single-link file")
        );
    }
}

#[cfg(unix)]
#[test]
fn claude_rejects_npm_node_entrypoints() {
    use std::os::unix::fs::PermissionsExt;

    let (_temp, workspace, scratch, target) = fixture();
    let cli_js = workspace.join("cli.js");
    fs::write(&cli_js, "#!/bin/sh\nexit 0\n").expect("write cli.js");
    fs::set_permissions(&cli_js, fs::Permissions::from_mode(0o755))
        .expect("make cli.js executable");
    let result = run_agent(
        AgentKind::Claude,
        cli_js,
        &workspace,
        &scratch,
        &target,
        b"prompt".to_vec(),
        10,
    );
    assert!(
        result
            .expect_err("npm cli.js must fail")
            .contains("official native entrypoint")
    );

    let (_temp, workspace, scratch, target) = fixture();
    let node_script = workspace.join("claude");
    fs::write(&node_script, "#!/usr/bin/env node\n").expect("write node script");
    fs::set_permissions(&node_script, fs::Permissions::from_mode(0o755))
        .expect("make node script executable");
    let result = run_agent(
        AgentKind::Claude,
        node_script,
        &workspace,
        &scratch,
        &target,
        b"prompt".to_vec(),
        10,
    );
    assert!(
        result
            .expect_err("Node script must fail")
            .contains("official native entrypoint")
    );
}
