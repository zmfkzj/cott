use std::ffi::OsString;
use std::fs;
use std::os::unix::fs::MetadataExt;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};
use std::sync::{Arc, Mutex, MutexGuard};

use cott::agent::{
    AgentKind, AgentRunCandidate, AgentSelection, CLAUDE, CODEX, OMP, PI, pi_max_prompt_bytes,
    run_agent, run_agent_in_project, valid_model,
};
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
    /// A caller environment fully owned by the test: a fake home (never the
    /// developer's), fake credentials and configuration variables, a custom
    /// variable, and markers of a parent agent session that must not leak.
    fn controlled(scratch: &Path, executable: &Path) -> Self {
        let home = scratch.parent().expect("scratch parent").join("home");
        let cert_dir = home.join("certs");
        let codex_home = home.join(".codex");
        let omp_home = home.join(".omp/agent");
        fs::create_dir_all(&cert_dir).expect("cert directory");
        fs::create_dir_all(&codex_home).expect("Codex home");
        fs::create_dir_all(&omp_home).expect("OMP home");
        let values = [
            ("HOME", home.display().to_string()),
            ("PATH", "/usr/bin:/bin".to_owned()),
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
            ("COTT_TEST_CUSTOM", "custom-value".to_owned()),
            ("CLAUDECODE", "1".to_owned()),
            ("CODEX_SANDBOX_NETWORK_DISABLED", "1".to_owned()),
            ("PI_SESSION_ID", "parent-session".to_owned()),
        ];
        let mut saved = Vec::with_capacity(values.len() + 1);
        for (name, value) in values {
            saved.push((name, std::env::var_os(name)));
            unsafe { std::env::set_var(name, value) };
        }
        saved.push(("CLAUDE_CONFIG_DIR", std::env::var_os("CLAUDE_CONFIG_DIR")));
        unsafe { std::env::remove_var("CLAUDE_CONFIG_DIR") };
        Self { saved }
    }

    fn with_path(mut self, path: &Path) -> Self {
        self.saved.push(("PATH", std::env::var_os("PATH")));
        unsafe { std::env::set_var("PATH", path) };
        self
    }

    fn with_var(mut self, name: &'static str, value: Option<&str>) -> Self {
        self.saved.push((name, std::env::var_os(name)));
        unsafe {
            match value {
                Some(value) => std::env::set_var(name, value),
                None => std::env::remove_var(name),
            }
        }
        self
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

fn bun_omp_fixture(root: &Path) -> (PathBuf, PathBuf, PathBuf) {
    use std::os::unix::fs::{PermissionsExt, symlink};

    let modules = root.join("installation/node_modules");
    let package = modules.join("@oh-my-pi/pi-coding-agent");
    let dependency = modules.join(".store/fixture-data@1/node_modules/fixture-data");
    let runtime_dir = root.join("runtime");
    fs::create_dir_all(package.join("dist")).expect("OMP package");
    fs::create_dir_all(&dependency).expect("dependency");
    fs::create_dir(&runtime_dir).expect("runtime");
    fs::write(
        package.join("package.json"),
        r#"{"name":"@oh-my-pi/pi-coding-agent","bin":{"omp":"dist/cli.js"},"dependencies":{"fixture-data":"1"}}"#,
    )
    .expect("OMP package metadata");
    fs::write(
        dependency.join("package.json"),
        r#"{"name":"fixture-data"}"#,
    )
    .expect("dependency metadata");
    fs::write(dependency.join("version"), "omp/18.2.7\n").expect("dependency version");
    fs::write(dependency.join("candidate"), "generated through Bun\n").expect("dependency content");
    symlink(&dependency, modules.join("fixture-data")).expect("package manager dependency link");
    let unrelated = modules.join("unrelated");
    fs::create_dir(&unrelated).expect("unrelated package");
    fs::write(unrelated.join("secret"), "unrelated package data").expect("unrelated data");
    fs::write(runtime_dir.join("secret"), "outside runtime data").expect("runtime sibling data");
    let bun = runtime_dir.join("bun");
    fs::write(
        &bun,
        "#!/bin/sh\nscript=$1\nshift\nexec /bin/sh \"$script\" \"$@\"\n",
    )
    .expect("Bun-like runtime");
    fs::set_permissions(&bun, fs::Permissions::from_mode(0o755)).expect("runtime permissions");
    let script = package.join("dist/cli.js");
    fs::write(
        &script,
        format!(
            r#"#!/usr/bin/env bun
set -eu
[ ! -e '{unrelated_secret}' ]
if (printf changed > '{dependency}/candidate') 2>/dev/null; then exit 10; fi
if [ "$1" = --version ]; then
    [ ! -e '{runtime_secret}' ]
    [ "$PATH" = /usr/bin:/bin ]
    [ -z "${{ANTHROPIC_API_KEY+x}}" ]
    [ -z "${{PI_CODING_AGENT_DIR+x}}" ]
    printf probed > "$TMPDIR/version-seen"
    cat '{dependency}/version'
    exit 0
fi
[ "$(cat "$TMPDIR/version-seen")" = probed ]
[ "$PATH" = '{runtime_dir}:/usr/bin:/bin' ]
[ "$ANTHROPIC_API_KEY" = anthropic-secret-api-key ]
if (printf changed > sibling.py) 2>/dev/null; then exit 11; fi
if (printf changed > new-file.py) 2>/dev/null; then exit 12; fi
cat '{dependency}/candidate' > implementation.py
"#,
            runtime_secret = runtime_dir.join("secret").display(),
            unrelated_secret = unrelated.join("secret").display(),
            dependency = modules.join("fixture-data").display(),
            runtime_dir = runtime_dir.display(),
        ),
    )
    .expect("OMP entrypoint");
    fs::set_permissions(&script, fs::Permissions::from_mode(0o755)).expect("script permissions");
    (script, runtime_dir, dependency)
}

fn fake_adapter(workspace: &Path, version: &str, body: &str) -> PathBuf {
    fake_adapter_with_version_probe(
        workspace,
        // Version probes never see the caller's credentials or configuration.
        &format!(
            "[ -z \"${{CODEX_API_KEY+x}}${{ANTHROPIC_API_KEY+x}}${{COTT_TEST_CUSTOM+x}}${{CODEX_HOME+x}}\" ] || exit 3\nprintf '%s\\n' '{version}'\nexit 0"
        ),
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

/// Variables whose presence the fake agents report: everything the controlled
/// caller environment sets, cott's own variables, and the overrides that cott
/// must no longer add.
const CAPTURED_NAMES: &str = "ANTHROPIC_API_KEY ANTHROPIC_AUTH_TOKEN ANTHROPIC_BASE_URL CLAUDECODE CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC CLAUDE_CODE_OAUTH_TOKEN CODEX_ACCESS_TOKEN CODEX_API_KEY CODEX_HOME CODEX_SANDBOX_NETWORK_DISABLED COTT_TEST_CUSTOM DISABLE_TELEMETRY HOME HTTPS_PROXY HTTP_PROXY NO_PROXY PATH PI_CODING_AGENT_DIR PI_OFFLINE PI_SESSION_ID PYTHONDONTWRITEBYTECODE SSL_CERT_DIR SSL_CERT_FILE TMPDIR";

/// The caller environment every adapter inherits for generation (in
/// [`CAPTURED_NAMES`] order): no parent-session marker, no forced override.
const INHERITED_NAMES: [&str; 18] = [
    "ANTHROPIC_API_KEY",
    "ANTHROPIC_AUTH_TOKEN",
    "ANTHROPIC_BASE_URL",
    "CLAUDE_CODE_OAUTH_TOKEN",
    "CODEX_ACCESS_TOKEN",
    "CODEX_API_KEY",
    "CODEX_HOME",
    "COTT_TEST_CUSTOM",
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

/// AgentRun records only `PATH` and the variables cott sets.
fn recorded_names() -> Vec<String> {
    ["HOME", "PATH", "PWD", "PYTHONDONTWRITEBYTECODE", "TMPDIR"]
        .into_iter()
        .map(str::to_owned)
        .collect()
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
for name in {CAPTURED_NAMES}; do if eval "[ -n \"\${{${{name}}+x}}\" ]"; then printf '%s\n' "$name"; fi; done
}} > implementation.py
printf blocked > sibling.py 2>/dev/null || true
{status}"#
    )
}

const CLAUDE_RESULT: &str = r#"{"type":"result","subtype":"success","is_error":false,"result":"done","modelUsage":{"claude-test-model":{"inputTokens":1,"outputTokens":1}}}"#;

fn claude_capture_body() -> String {
    format!(
        r#"[ "${{ANTHROPIC_API_KEY-}}" = anthropic-secret-api-key ] &&
[ "${{CLAUDE_CODE_OAUTH_TOKEN-}}" = claude-oauth-token ] &&
[ "${{ANTHROPIC_BASE_URL-}}" = https://anthropic.invalid ] &&
[ -z "${{CLAUDE_CODE_DISABLE_NONESSENTIAL_TRAFFIC+x}}" ] &&
[ -z "${{CLAUDECODE+x}}" ] || exit 2
{}
printf '%s' '{CLAUDE_RESULT}'"#,
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
    run_or_skip_with_model(
        kind,
        None,
        executable,
        workspace,
        scratch,
        target,
        prompt,
        timeout_seconds,
    )
}

fn run_or_skip_with_model(
    kind: AgentKind,
    model: Option<&str>,
    executable: PathBuf,
    workspace: &Path,
    scratch: &Path,
    target: &Path,
    prompt: &[u8],
    timeout_seconds: u16,
) -> Option<Result<AgentRunCandidate, String>> {
    let result = run_agent(
        AgentSelection { kind, model },
        executable,
        workspace,
        scratch,
        target,
        prompt.to_vec(),
        timeout_seconds,
    );
    skip_without_bubblewrap(result)
}

#[allow(clippy::too_many_arguments)]
fn run_or_skip_in_project(
    kind: AgentKind,
    model: Option<&str>,
    project: &Path,
    executable: PathBuf,
    workspace: &Path,
    scratch: &Path,
    target: &Path,
    prompt: &[u8],
    timeout_seconds: u16,
) -> Option<Result<AgentRunCandidate, String>> {
    let result = run_agent_in_project(
        AgentSelection { kind, model },
        Some(project),
        executable,
        workspace,
        scratch,
        target,
        prompt.to_vec(),
        timeout_seconds,
    );
    skip_without_bubblewrap(result)
}

fn skip_without_bubblewrap(
    result: Result<AgentRunCandidate, String>,
) -> Option<Result<AgentRunCandidate, String>> {
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
        "--ephemeral".to_owned(),
        "--skip-git-repo-check".to_owned(),
        "--color".to_owned(),
        "never".to_owned(),
        "--cd".to_owned(),
        workspace.display().to_string(),
        "-".to_owned(),
    ];
    let expected_names = INHERITED_NAMES;
    assert_eq!(
        candidate.implementation,
        expected_capture(&expected_args, prompt, &expected_names)
    );
    assert_eq!(candidate.environment_names, recorded_names());
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
        "--print".to_owned(),
        "--input-format".to_owned(),
        "text".to_owned(),
        "--output-format".to_owned(),
        "json".to_owned(),
        "--no-session-persistence".to_owned(),
    ];
    let expected_names = INHERITED_NAMES;
    assert_eq!(
        candidate.implementation,
        expected_capture(&expected_args, prompt, &expected_names)
    );
    assert_eq!(candidate.environment_names, recorded_names());
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
    assert_eq!(candidate.stdout, CLAUDE_RESULT.as_bytes());
    assert_eq!(candidate.resolved_models, ["claude-test-model"]);
    assert_eq!(candidate.exit_code, Some(0));
    assert!(!candidate.timed_out);
    assert!(!workspace.join("sibling.py").exists());
    assert!(
        !candidate
            .implementation
            .windows(b"anthropic-secret-auth-token".len())
            .any(|window| window == b"anthropic-secret-auth-token")
    );
    assert!(
        !candidate
            .implementation
            .windows(b"anthropic-secret-api-key".len())
            .any(|window| window == b"anthropic-secret-api-key")
    );
}

#[test]
fn omp_bun_package_runs_both_phases_with_only_its_runtime_closure() {
    let (temp, workspace, scratch, target) = fixture();
    let (executable, runtime_dir, dependency) = bun_omp_fixture(&temp.root);
    fs::hard_link(&executable, temp.root.join("linked-agent")).expect("hardlinked entrypoint");
    fs::hard_link(runtime_dir.join("bun"), temp.root.join("linked-bun"))
        .expect("hardlinked runtime");
    fs::write(workspace.join("sibling.py"), "untouched").expect("workspace sibling");
    let entrypoint_bytes = fs::read(&executable).expect("entrypoint bytes");
    let _lock = _hold_env_lock();
    let _environment = EnvRestore::controlled(&scratch, &executable).with_path(Path::new(
        &format!("{}:/usr/bin:/bin", runtime_dir.display()),
    ));
    let Some(result) = run_or_skip(
        AgentKind::Omp,
        executable.clone(),
        &workspace,
        &scratch,
        &target,
        b"generate",
    ) else {
        return;
    };
    let candidate = result.expect("sandboxed Bun OMP");
    assert_eq!(candidate.adapter_version, "18.2.7");
    assert_eq!(candidate.implementation, b"generated through Bun\n");
    assert_eq!(candidate.executable, executable);
    assert_eq!(
        candidate.executable_hash,
        format!("sha256:{}", sha256_hex(&entrypoint_bytes))
    );
    assert_eq!(
        fs::read_to_string(dependency.join("candidate")).expect("dependency"),
        "generated through Bun\n"
    );
    assert_eq!(
        fs::read_to_string(workspace.join("sibling.py")).expect("sibling"),
        "untouched"
    );
    assert!(!workspace.join("new-file.py").exists());
}

#[test]
fn omp_bun_rejects_missing_and_unsafe_runtimes_before_running() {
    use std::os::unix::fs::PermissionsExt;

    let _lock = _hold_env_lock();
    for case in ["missing", "nonexecutable", "directory"] {
        let (temp, workspace, scratch, target) = fixture();
        let (executable, runtime_dir, _) = bun_omp_fixture(&temp.root);
        let bun = runtime_dir.join("bun");
        match case {
            "missing" => fs::remove_file(&bun).expect("remove runtime"),
            "nonexecutable" => fs::set_permissions(&bun, fs::Permissions::from_mode(0o644))
                .expect("nonexecutable runtime"),
            "directory" => {
                fs::remove_file(&bun).expect("remove runtime");
                fs::create_dir(&bun).expect("runtime directory");
            }
            _ => unreachable!(),
        }
        let _environment = EnvRestore::controlled(&scratch, &executable).with_path(Path::new(
            &format!("{}:/usr/bin:/bin", runtime_dir.display()),
        ));
        let error = run_agent(
            AgentSelection {
                kind: AgentKind::Omp,
                model: None,
            },
            executable,
            &workspace,
            &scratch,
            &target,
            b"generate".to_vec(),
            10,
        )
        .expect_err(case);
        assert!(error.contains("OMP Bun runtime"), "{case}: {error}");
        assert!(
            !target.exists(),
            "{case} must fail before the version probe"
        );
    }
}

#[test]
fn omp_bun_rejects_dependency_links_outside_the_installation() {
    use std::os::unix::fs::symlink;

    let (temp, workspace, scratch, target) = fixture();
    let (executable, runtime_dir, dependency) = bun_omp_fixture(&temp.root);
    let outside = temp.root.join("outside/node_modules/fixture-data");
    fs::create_dir_all(outside.parent().expect("outside parent")).expect("outside directory");
    fs::rename(&dependency, &outside).expect("move dependency outside installation");
    let link = temp.root.join("installation/node_modules/fixture-data");
    fs::remove_file(&link).expect("remove package link");
    symlink(outside, &link).expect("escaping dependency link");
    let _lock = _hold_env_lock();
    let _environment = EnvRestore::controlled(&scratch, &executable).with_path(Path::new(
        &format!("{}:/usr/bin:/bin", runtime_dir.display()),
    ));
    let error = run_agent(
        AgentSelection {
            kind: AgentKind::Omp,
            model: None,
        },
        executable,
        &workspace,
        &scratch,
        &target,
        b"generate".to_vec(),
        10,
    )
    .expect_err("escaping package must fail");
    assert!(
        error.contains("unsafe OMP runtime package location"),
        "{error}"
    );
    assert!(!target.exists());
}

#[test]
fn omp_golden_argv_prompt_environment_and_target_write() {
    let (_temp, workspace, scratch, target) = fixture();
    let body = format!(
        "[ \"$(cat \"$PI_CODING_AGENT_DIR/config.yml\")\" = 'model: test' ] || exit 4\nprintf refreshed > \"$PI_CODING_AGENT_DIR/agent.db\" || exit 5\nprintf cached > \"$PI_CODING_AGENT_DIR/model-cache\" || exit 6\nprintf x > \"$HOME/escape\" 2>/dev/null || true\n{}",
        capture_body(None)
    );
    let executable = fake_adapter(&workspace, "omp/17.2.13", &body);
    let _lock = _hold_env_lock();
    let _environment = EnvRestore::controlled(&scratch, &executable);
    let omp_home = scratch
        .parent()
        .expect("scratch parent")
        .join("home/.omp/agent");
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
        "--no-pty".to_owned(),
        "--no-title".to_owned(),
        "--max-time".to_owned(),
        "10s".to_owned(),
        format!("@{}", prompt_file.display()),
    ];
    let expected_names = INHERITED_NAMES;
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
    assert_eq!(candidate.environment_names, recorded_names());
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
    // The caller's agent directory is OMP's own store, shared with the host:
    // OMP's login and cache writes persist as in a normal run, nothing else
    // in it changed, and nothing outside it in the home directory did.
    assert_eq!(
        fs::read_to_string(omp_home.join("agent.db")).expect("OMP credential database"),
        "refreshed"
    );
    assert_eq!(
        fs::read_to_string(omp_home.join("model-cache")).expect("OMP cache"),
        "cached"
    );
    assert_eq!(
        fs::read_to_string(omp_home.join("config.yml")).expect("OMP config"),
        "model: test\n"
    );
    assert!(
        !scratch
            .parent()
            .expect("scratch parent")
            .join("home/escape")
            .exists()
    );
}

/// Dummy OMP model configuration (no real provider, key or endpoint): a
/// custom provider with a base URL, an environment-variable key reference,
/// and a model, with a comment, non-ASCII text and no trailing newline so a
/// rewrite or re-serialisation would change its bytes.
const DUMMY_MODELS_YML: &[u8] = b"# cott test fixture \xe2\x80\x94 not a real provider\nproviders:\n  cott-dummy:\n    baseUrl: https://models.invalid/v1\n    apiKey: COTT_DUMMY_PROVIDER_KEY\n    api: openai-completions\n    models:\n      - id: dummy-model\n        name: \"Dummy \xc3\xa9\"\n        contextWindow: 8192";

/// OMP reads its model configuration from `models.yml` in its agent
/// directory (`PI_CODING_AGENT_DIR`, default `~/.omp/agent`; `models.yaml`
/// is the fallback spelling and a lone `models.json` is migrated to
/// `models.yml` in place). Cott shares that directory with the host instead
/// of copying selected files into an isolated one, so the file the mock OMP
/// finds there is the caller's own, byte for byte, next to `config.yml` and
/// the login database, whether it is a plain file, a dotfile-manager link,
/// a chain of links, a link through a linked directory, or lies in a linked
/// agent directory, and Cott never rewrites it.
#[test]
fn omp_reads_the_callers_models_yml_unchanged_from_its_agent_directory() {
    let body = r#"dir=${PI_CODING_AGENT_DIR:-$HOME/.omp/agent}
[ "$(cat "$dir/config.yml")" = 'defaultModel: cott-dummy/dummy-model' ] || exit 40
[ -f "$dir/agent.db" ] || exit 41
if [ -f "$dir/models.yml" ]; then file=$dir/models.yml
elif [ -f "$dir/models.yaml" ]; then file=$dir/models.yaml
elif [ -f "$dir/models.json" ]; then
  cp "$dir/models.json" "$dir/models.yml.tmp" && mv "$dir/models.yml.tmp" "$dir/models.yml" || exit 43
  file=$dir/models.yml
else exit 42
fi
sha256sum < "$file" | cut -c1-64 > implementation.py"#;
    let expected = format!("{}\n", sha256_hex(DUMMY_MODELS_YML));
    let _lock = _hold_env_lock();
    for case in [
        "PI_CODING_AGENT_DIR",
        "default agent directory",
        "linked agent directory",
        "linked file",
        "chain of links",
        "link through a linked directory",
        "models.yaml",
        "models.json",
    ] {
        let (temp, workspace, scratch, target) = fixture();
        let executable = fake_adapter(&workspace, "omp/17.2.13", body);
        let environment = EnvRestore::controlled(&scratch, &executable);
        let home = temp.root.join("home");
        let (_environment, agent) = match case {
            "PI_CODING_AGENT_DIR" => {
                let agent = temp.root.join("config/omp");
                fs::create_dir_all(&agent).expect("relocated agent directory");
                let value = agent.to_str().expect("UTF-8 path").to_owned();
                (
                    environment.with_var("PI_CODING_AGENT_DIR", Some(value.as_str())),
                    agent,
                )
            }
            "linked agent directory" => {
                let linked = home.join("dotfiles/omp-agent");
                fs::create_dir_all(&linked).expect("linked agent directory");
                fs::remove_dir(home.join(".omp/agent")).expect("replace agent directory");
                std::os::unix::fs::symlink("../dotfiles/omp-agent", home.join(".omp/agent"))
                    .expect("agent directory link");
                (
                    environment.with_var("PI_CODING_AGENT_DIR", None),
                    home.join(".omp/agent"),
                )
            }
            _ => (
                environment.with_var("PI_CODING_AGENT_DIR", None),
                home.join(".omp/agent"),
            ),
        };
        fs::write(
            agent.join("config.yml"),
            "defaultModel: cott-dummy/dummy-model",
        )
        .expect("OMP config");
        fs::write(agent.join("agent.db"), "login").expect("OMP login database");
        let name = match case {
            "models.yaml" => "models.yaml",
            "models.json" => "models.json",
            _ => "models.yml",
        };
        let stored = match case {
            "linked file" => {
                // A GNU Stow style relative link into a dotfiles tree.
                let file = home.join("dotfiles/omp/models.yml");
                fs::create_dir_all(file.parent().expect("dotfiles")).expect("dotfiles");
                std::os::unix::fs::symlink("../../dotfiles/omp/models.yml", agent.join(name))
                    .expect("models.yml link");
                file
            }
            "chain of links" => {
                // A home-manager style chain: the agent directory links into a
                // generated profile tree whose entry links to the stored file.
                let profile = temp.root.join("profile/home-files/.omp/agent/models.yml");
                let file = temp.root.join("store/0123-models.yml");
                fs::create_dir_all(profile.parent().expect("profile")).expect("profile");
                fs::create_dir_all(file.parent().expect("store")).expect("store");
                std::os::unix::fs::symlink(&file, &profile).expect("profile link");
                std::os::unix::fs::symlink(&profile, agent.join(name)).expect("models.yml link");
                file
            }
            "link through a linked directory" => {
                // A relative link into `~/dotfiles`, itself a link to another
                // disk: the path the link names is not the file's own path.
                let file = temp.root.join("data/dotfiles/omp/models.yml");
                fs::create_dir_all(file.parent().expect("data")).expect("data");
                std::os::unix::fs::symlink(temp.root.join("data/dotfiles"), home.join("dotfiles"))
                    .expect("dotfiles link");
                std::os::unix::fs::symlink("../../dotfiles/omp/models.yml", agent.join(name))
                    .expect("models.yml link");
                file
            }
            _ => agent.join(name),
        };
        fs::write(&stored, DUMMY_MODELS_YML).expect("OMP model configuration");
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
        let candidate = result.unwrap_or_else(|error| panic!("{case}: {error}"));
        assert_eq!(
            String::from_utf8(candidate.implementation).expect("digest"),
            expected,
            "{case}: the CLI read the caller's exact model configuration"
        );
        assert_eq!(
            fs::read(&stored).expect("OMP model configuration"),
            DUMMY_MODELS_YML,
            "{case}: never rewritten"
        );
        if case == "models.json" {
            // OMP's own migration writes `models.yml` into the shared store.
            assert_eq!(
                fs::read(agent.join("models.yml")).expect("migrated models.yml"),
                DUMMY_MODELS_YML,
                "{case}"
            );
        }
        if matches!(
            case,
            "linked file" | "chain of links" | "link through a linked directory"
        ) {
            assert!(
                fs::symlink_metadata(agent.join(name))
                    .expect("models.yml link")
                    .file_type()
                    .is_symlink(),
                "{case}: the caller's link is kept"
            );
        }
    }
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
fn codex_runs_at_the_project_path_with_the_callers_configuration_login_and_path_tools() {
    use std::os::unix::fs::{PermissionsExt, symlink};

    let (temp, workspace, scratch, target) = fixture();
    let project = temp.root.join("project");
    fs::create_dir_all(project.join(".codex")).expect("project Codex directory");
    fs::write(project.join("AGENTS.md"), "project rules").expect("project rules");
    fs::write(project.join(".codex/config.toml"), "model = \"project\"\n").expect("project config");
    // The project's own files are neither visible nor writable to the agent.
    fs::write(project.join("source.py"), "project source").expect("project source");
    let project_path = fs::canonicalize(&project).expect("canonical project");
    let installation = temp.root.join("installation");
    fs::create_dir_all(installation.join("bin")).expect("installation bin");
    fs::create_dir_all(installation.join("share")).expect("installation data");
    fs::write(
        installation.join("share/greeting"),
        "hello from the installation",
    )
    .expect("installation data");
    let hello = installation.join("bin/hello");
    fs::write(
        &hello,
        "#!/bin/sh\ncat \"$(dirname \"$(readlink -f \"$0\")\")/../share/greeting\"\n",
    )
    .expect("installed tool");
    fs::set_permissions(&hello, fs::Permissions::from_mode(0o755)).expect("tool permissions");
    let tools = temp.root.join("tools/bin");
    fs::create_dir_all(&tools).expect("PATH directory");
    symlink(&hello, tools.join("hello")).expect("PATH link");
    // Like Codex: work at `--cd`, read the configuration and login in
    // CODEX_HOME, replace auth.json atomically, and append to its own log.
    let body = format!(
        r#"case " $* " in *" --sandbox "*|*" --full-auto "*|*" --dangerously-bypass-approvals-and-sandbox "*) exit 2 ;; esac
for arg do [ "${{previous-}}" = --cd ] && cd_value=$arg; previous=$arg; done
[ "${{cd_value-}}" = '{project}' ] || exit 2
[ "$(pwd)" = '{project}' ] && [ "$PWD" = '{project}' ] || exit 3
[ "$(cat "$CODEX_HOME/config.toml")" = 'model = "user"' ] || exit 4
[ "$(cat AGENTS.md)" = 'project rules' ] || exit 5
[ "$(cat .codex/config.toml)" = 'model = "project"' ] || exit 6
[ "$(hello)" = 'hello from the installation' ] || exit 7
[ ! -e source.py ] || exit 12
printf refreshed > "$CODEX_HOME/auth.json.tmp" && mv "$CODEX_HOME/auth.json.tmp" "$CODEX_HOME/auth.json" || exit 8
mkdir "$CODEX_HOME/log" && printf entry > "$CODEX_HOME/log/codex.log" || exit 10
if (printf x >> AGENTS.md) 2>/dev/null; then exit 11; fi
if (printf x > source.py) 2>/dev/null; then exit 13; fi
printf x > "$HOME/escape" 2>/dev/null || true
printf done > implementation.py"#,
        project = project_path.display()
    );
    let executable = fake_adapter(&workspace, "codex-cli 0.147.1", &body);
    let _lock = _hold_env_lock();
    let path = format!("{}:/usr/bin:/bin", tools.display());
    let _environment = EnvRestore::controlled(&scratch, &executable).with_path(Path::new(&path));
    let home = temp.root.join("home");
    let codex_home = home.join(".codex");
    fs::write(codex_home.join("config.toml"), "model = \"user\"").expect("user config");
    fs::write(codex_home.join("auth.json"), "stale").expect("user login");
    let Some(result) = run_or_skip_in_project(
        AgentKind::Codex,
        None,
        &project,
        executable,
        &workspace,
        &scratch,
        &target,
        b"codex prompt\n",
        10,
    ) else {
        return;
    };
    let candidate = result.expect("Codex run with the caller's setup");
    assert_eq!(candidate.implementation, b"done\n");
    // Codex's own store writes reached the caller's CODEX_HOME as in a normal
    // run: the atomically replaced login and its log. Nothing else changed.
    assert_eq!(
        fs::read_to_string(codex_home.join("auth.json")).expect("login"),
        "refreshed"
    );
    assert_eq!(
        fs::symlink_metadata(codex_home.join("auth.json"))
            .expect("login metadata")
            .nlink(),
        1
    );
    assert!(!codex_home.join("auth.json.tmp").exists());
    assert_eq!(
        fs::read_to_string(codex_home.join("log/codex.log")).expect("log"),
        "entry"
    );
    assert_eq!(
        fs::read_to_string(codex_home.join("config.toml")).expect("config"),
        "model = \"user\""
    );
    assert!(!home.join("escape").exists());
    assert_eq!(
        fs::read_to_string(project.join("AGENTS.md")).expect("project rules"),
        "project rules"
    );
    assert_eq!(
        fs::read_to_string(project.join("source.py")).expect("project source"),
        "project source"
    );
    assert!(!project.join("implementation.py").exists());
    assert_eq!(candidate.environment_names, recorded_names());
}

#[test]
fn credential_stores_must_be_single_link_regular_files_of_the_caller() {
    use std::os::unix::fs::symlink;

    let _lock = _hold_env_lock();
    for case in ["hard link", "symlink"] {
        let (temp, workspace, scratch, target) = fixture();
        let executable = fake_adapter(
            &workspace,
            "codex-cli 0.147.1",
            "printf x > implementation.py",
        );
        let _environment = EnvRestore::controlled(&scratch, &executable);
        let codex_home = temp.root.join("home/.codex");
        if case == "hard link" {
            fs::write(codex_home.join("auth.json"), "login").expect("user login");
            fs::hard_link(codex_home.join("auth.json"), temp.root.join("auth-link"))
                .expect("second link");
        } else {
            fs::write(temp.root.join("auth-elsewhere"), "login").expect("linked login");
            symlink(
                temp.root.join("auth-elsewhere"),
                codex_home.join("auth.json"),
            )
            .expect("login symlink");
        }
        let error = run_agent(
            AgentSelection {
                kind: AgentKind::Codex,
                model: None,
            },
            executable,
            &workspace,
            &scratch,
            &target,
            b"prompt".to_vec(),
            10,
        )
        .expect_err(case);
        assert!(
            error.contains(
                "must be a regular single-link file owned by the caller, not a symlink or hard link"
            ),
            "{case}: {error}"
        );
        assert_eq!(fs::read(&target).expect("untouched target"), b"", "{case}");
    }
}

#[test]
fn configuration_stores_must_be_narrow_and_outside_the_project() {
    let _lock = _hold_env_lock();
    for case in ["home", "project parent", "inside the project"] {
        let (temp, workspace, scratch, target) = fixture();
        let executable = fake_adapter(
            &workspace,
            "codex-cli 0.147.1",
            "printf x > implementation.py",
        );
        let project = temp.root.join("store/project");
        fs::create_dir_all(&project).expect("project");
        let store = match case {
            "home" => temp.root.join("home"),
            "project parent" => temp.root.join("store"),
            // For example a `CODEX_HOME` kept in the project tree: sharing it
            // would make project files (possibly Cott sources or accepted
            // implementations) writable to the agent.
            _ => {
                fs::create_dir_all(project.join("python/.codex")).expect("store in project");
                project.join("python/.codex")
            }
        };
        let _environment = EnvRestore::controlled(&scratch, &executable)
            .with_var("CODEX_HOME", Some(store.to_str().expect("UTF-8 store")));
        let error = run_agent_in_project(
            AgentSelection {
                kind: AgentKind::Codex,
                model: None,
            },
            Some(&project),
            executable,
            &workspace,
            &scratch,
            &target,
            b"prompt".to_vec(),
            10,
        )
        .expect_err(case);
        let expected = match case {
            "home" => {
                "must not be `/`, a system tree, or the home directory or one of its ancestors"
            }
            "project parent" => {
                "contains the caller project; the project is never writable to an agent"
            }
            _ => "is inside the caller project; the project is never writable to an agent",
        };
        assert!(error.contains(expected), "{case}: {error}");
        assert_eq!(fs::read(&target).expect("untouched target"), b"", "{case}");
    }
}

const CODEX_POLICY_OVERRIDES: &str = r#"case " $* " in *" --sandbox "*|*" -s "*|*" --full-auto "*|*" --dangerously-bypass-approvals-and-sandbox "*|*" --ask-for-approval "*|*" -a "*|*" -c "*|*" --config "*|*" --profile "*|*" -p "*) exit 2 ;; esac"#;
const CLAUDE_POLICY_OVERRIDES: &str = r#"case " $* " in *" --permission-mode "*|*" --allowedTools "*|*" --allowed-tools "*|*" --disallowedTools "*|*" --disallowed-tools "*|*" --dangerously-skip-permissions "*|*" --allow-dangerously-skip-permissions "*|*" --tools "*|*" --bare "*|*" --settings "*|*" --setting-sources "*) exit 2 ;; esac"#;
const OMP_POLICY_OVERRIDES: &str = r#"case " $* " in *" --approval-mode "*|*" --auto-approve "*|*" --yolo "*|*" --tools "*) exit 2 ;; esac"#;

/// Cott passes no permission, sandbox or approval override. Each mock applies
/// the caller's own policy from its configuration the way the real CLI's
/// non-interactive mode does: a policy that allows file edits yields the
/// candidate, one that denies them fails once with a precise local-policy
/// reason, the run is never retried with a more permissive policy, and the
/// caller's configuration is never rewritten.
#[test]
fn the_callers_permission_policy_is_never_overridden_or_retried() {
    struct Case {
        name: &'static str,
        kind: AgentKind,
        store: &'static str,
        file: &'static str,
        contents: Option<&'static str>,
        writes: bool,
        reason: &'static str,
    }
    let codex = format!(
        r#"{CODEX_POLICY_OVERRIDES}
printf x >> "$CODEX_HOME/invocations" || exit 3
[ "$(pwd)" = '@PROJECT@' ] || exit 4
if grep -q 'sandbox_mode = "read-only"' "$CODEX_HOME/config.toml" 2>/dev/null; then exit 0; fi
printf done > implementation.py"#
    );
    let claude = format!(
        r#"{CLAUDE_POLICY_OVERRIDES}
printf x >> "$HOME/.claude/invocations" || exit 3
cat > /dev/null
if grep -q -e '"defaultMode":"acceptEdits"' -e '"defaultMode":"bypassPermissions"' "$HOME/.claude/settings.json" 2>/dev/null; then
  printf done > implementation.py
  printf '%s' '@RESULT@'
  exit 0
fi
printf '{{"type":"result","subtype":"success","is_error":false,"result":"blocked","permission_denials":[{{"tool_name":"Write","tool_use_id":"toolu_1","tool_input":{{"file_path":"%s/implementation.py","content":"draft"}}}}]}}' "$(pwd)""#
    )
    .replace("@RESULT@", CLAUDE_RESULT);
    let omp = format!(
        r#"{OMP_POLICY_OVERRIDES}
printf x >> "$PI_CODING_AGENT_DIR/invocations" || exit 3
if grep -q 'approvalMode: always-ask' "$PI_CODING_AGENT_DIR/config.yml" 2>/dev/null; then exit 0; fi
printf done > implementation.py"#
    );
    let codex_reason = "Cott passes no --sandbox or approval flag: the caller's Codex `sandbox_mode`/`permission_profile` and project trust decide";
    let claude_reason = "the caller's Claude Code permission settings denied 1 tool request(s) (Write `@PROJECT@/implementation.py`); Cott passes no --permission-mode or allow rule";
    let omp_reason = "Cott passes no --approval-mode: the caller's OMP `tools.approvalMode`";
    let cases = [
        Case {
            name: "codex without a policy",
            kind: AgentKind::Codex,
            store: ".codex",
            file: "config.toml",
            contents: None,
            writes: true,
            reason: "",
        },
        Case {
            name: "codex workspace-write",
            kind: AgentKind::Codex,
            store: ".codex",
            file: "config.toml",
            contents: Some("sandbox_mode = \"workspace-write\"\n"),
            writes: true,
            reason: "",
        },
        Case {
            name: "codex read-only",
            kind: AgentKind::Codex,
            store: ".codex",
            file: "config.toml",
            contents: Some("sandbox_mode = \"read-only\"\n"),
            writes: false,
            reason: codex_reason,
        },
        Case {
            name: "claude without settings",
            kind: AgentKind::Claude,
            store: ".claude",
            file: "settings.json",
            contents: None,
            writes: false,
            reason: claude_reason,
        },
        Case {
            name: "claude acceptEdits",
            kind: AgentKind::Claude,
            store: ".claude",
            file: "settings.json",
            contents: Some(r#"{"permissions":{"defaultMode":"acceptEdits"}}"#),
            writes: true,
            reason: "",
        },
        Case {
            name: "claude plan",
            kind: AgentKind::Claude,
            store: ".claude",
            file: "settings.json",
            contents: Some(r#"{"permissions":{"defaultMode":"plan"}}"#),
            writes: false,
            reason: claude_reason,
        },
        Case {
            name: "omp default approval",
            kind: AgentKind::Omp,
            store: ".omp/agent",
            file: "config.yml",
            contents: None,
            writes: true,
            reason: "",
        },
        Case {
            name: "omp always-ask",
            kind: AgentKind::Omp,
            store: ".omp/agent",
            file: "config.yml",
            contents: Some("tools:\n  approvalMode: always-ask\n"),
            writes: false,
            reason: omp_reason,
        },
    ];
    let _lock = _hold_env_lock();
    for case in cases {
        let (temp, workspace, scratch, target) = fixture();
        let project = temp.root.join("project");
        fs::create_dir(&project).expect("project");
        let project_path = fs::canonicalize(&project)
            .expect("canonical project")
            .display()
            .to_string();
        let executable = match case.kind {
            AgentKind::Codex => fake_adapter(
                &workspace,
                "codex-cli 0.147.1",
                &codex.replace("@PROJECT@", &project_path),
            ),
            AgentKind::Claude => fake_claude_adapter(&workspace, "2.1.89", &claude),
            AgentKind::Omp => fake_adapter(&workspace, "omp/17.2.13", &omp),
            AgentKind::Pi => unreachable!("Pi has no permission policy"),
        };
        let _environment = EnvRestore::controlled(&scratch, &executable);
        let store = temp.root.join("home").join(case.store);
        fs::create_dir_all(&store).expect("caller configuration directory");
        if let Some(contents) = case.contents {
            fs::write(store.join(case.file), contents).expect("caller policy");
        }
        let Some(result) = run_or_skip_in_project(
            case.kind,
            None,
            &project,
            executable,
            &workspace,
            &scratch,
            &target,
            b"prompt\n",
            10,
        ) else {
            return;
        };
        assert_eq!(
            fs::read_to_string(store.join("invocations")).expect("invocation count"),
            "x",
            "{}: exactly one generation run, never a permissive retry",
            case.name
        );
        if let Some(contents) = case.contents {
            assert_eq!(
                fs::read_to_string(store.join(case.file)).expect("caller policy"),
                contents,
                "{}: the caller's policy is not rewritten",
                case.name
            );
        } else {
            assert!(!store.join(case.file).exists(), "{}", case.name);
        }
        if case.writes {
            let candidate = result.unwrap_or_else(|error| panic!("{}: {error}", case.name));
            assert_eq!(candidate.implementation, b"done\n", "{}", case.name);
        } else {
            let error = result.expect_err(case.name);
            assert!(
                error.contains("agent did not write target"),
                "{}: {error}",
                case.name
            );
            let reason = case.reason.replace("@PROJECT@", &project_path);
            assert!(error.contains(&reason), "{}: {error}", case.name);
            assert_eq!(
                fs::read(&target).expect("untouched target"),
                b"",
                "{}",
                case.name
            );
        }
    }
}

/// The CLIs run at the real project path. Above it they find the project's
/// ancestor context and configuration and the repository root marker that
/// bounds their discovery and keys Codex project trust, all read-only and
/// without the repository's objects, refs, index, configuration or other
/// files; the caller's trust entry for the real repository path applies
/// unchanged.
#[test]
fn ancestors_repository_marker_and_trust_key_are_presented_read_only() {
    let _lock = _hold_env_lock();
    for case in ["repository", "worktree"] {
        let (temp, workspace, scratch, target) = fixture();
        let repository = temp.root.join("repo");
        let project = repository.join("packages/project");
        fs::create_dir_all(&project).expect("project");
        fs::write(project.join("source.py"), "project source").expect("project source");
        fs::write(repository.join("packages/sibling.txt"), "sibling").expect("sibling");
        fs::write(repository.join("secret.txt"), "repository file").expect("repository file");
        fs::write(repository.join("AGENTS.md"), "repository rules").expect("ancestor rules");
        fs::create_dir_all(repository.join(".codex")).expect("ancestor Codex layer");
        fs::write(
            repository.join(".codex/config.toml"),
            "approval_policy = \"never\"",
        )
        .expect("ancestor Codex config");
        fs::create_dir_all(repository.join(".agents/skills/review")).expect("ancestor skills");
        fs::write(
            repository.join(".agents/skills/review/SKILL.md"),
            "review skill",
        )
        .expect("ancestor skill");
        let common = if case == "repository" {
            repository.join(".git")
        } else {
            temp.root.join("main/.git")
        };
        fs::create_dir_all(common.join("objects/ab")).expect("objects");
        fs::create_dir_all(common.join("refs/heads")).expect("refs");
        fs::write(common.join("HEAD"), "ref: refs/heads/main\n").expect("HEAD");
        fs::write(common.join("config"), "[core]\n").expect("git config");
        fs::write(common.join("index"), "index").expect("index");
        fs::write(common.join("objects/ab/cdef"), "object").expect("object");
        fs::write(common.join("refs/heads/main"), "0123").expect("ref");
        let worktree = common.join("worktrees/repo");
        if case == "worktree" {
            fs::create_dir_all(&worktree).expect("worktree git directory");
            fs::write(worktree.join("HEAD"), "ref: refs/heads/feature\n").expect("HEAD");
            fs::write(worktree.join("commondir"), "../..\n").expect("commondir");
            fs::write(worktree.join("index"), "index").expect("worktree index");
            fs::write(
                worktree.join("gitdir"),
                format!("{}\n", repository.join(".git").display()),
            )
            .expect("gitdir");
            fs::write(
                repository.join(".git"),
                "gitdir: ../main/.git/worktrees/repo\n",
            )
            .expect("worktree pointer");
        }
        let repository_path = fs::canonicalize(&repository)
            .expect("canonical repository")
            .display()
            .to_string();
        let project_path = fs::canonicalize(&project)
            .expect("canonical project")
            .display()
            .to_string();
        let common_path = fs::canonicalize(&common)
            .expect("canonical git directory")
            .display()
            .to_string();
        let (markers, checks, hidden) = if case == "repository" {
            (
                "'@COMMON@/HEAD'",
                "[ \"$(cat '@COMMON@/HEAD')\" = 'ref: refs/heads/main' ] || exit 10",
                "'@COMMON@/config' '@COMMON@/index' '@COMMON@/objects' '@COMMON@/refs'",
            )
        } else {
            (
                "'@REPO@/.git' '@COMMON@/HEAD' '@COMMON@/worktrees/repo/HEAD'",
                "[ \"$(cat '@REPO@/.git')\" = 'gitdir: ../main/.git/worktrees/repo' ] && [ \"$(cat '@COMMON@/worktrees/repo/HEAD')\" = 'ref: refs/heads/feature' ] && [ \"$(cat '@COMMON@/worktrees/repo/commondir')\" = '../..' ] && [ -f '@COMMON@/worktrees/repo/gitdir' ] && [ \"$(cat '@COMMON@/HEAD')\" = 'ref: refs/heads/main' ] || exit 10",
                "'@COMMON@/config' '@COMMON@/index' '@COMMON@/objects' '@COMMON@/refs' '@COMMON@/worktrees/repo/index'",
            )
        };
        let body = format!(
            r#"[ "$(pwd)" = '@PROJECT@' ] && [ "$PWD" = '@PROJECT@' ] || exit 3
[ "$(cat '@REPO@/AGENTS.md')" = 'repository rules' ] || exit 4
[ "$(cat '@REPO@/.codex/config.toml')" = 'approval_policy = "never"' ] || exit 5
[ "$(cat '@REPO@/.agents/skills/review/SKILL.md')" = 'review skill' ] || exit 6
grep -qxF '[projects."@REPO@"]' "$CODEX_HOME/config.toml" || exit 7
for hidden in source.py '@REPO@/secret.txt' '@REPO@/packages/sibling.txt' {hidden}; do [ ! -e "$hidden" ] || exit 8; done
{checks}
for readonly in '@REPO@/AGENTS.md' '@REPO@/.codex/config.toml' {markers}; do if (printf x >> "$readonly") 2>/dev/null; then exit 9; fi; done
printf x > '@REPO@/new-file' 2>/dev/null || true
printf done > implementation.py"#
        )
        .replace("@PROJECT@", &project_path)
        .replace("@REPO@", &repository_path)
        .replace("@COMMON@", &common_path);
        let executable = fake_adapter(&workspace, "codex-cli 0.147.1", &body);
        let _environment = EnvRestore::controlled(&scratch, &executable);
        let trust = format!("[projects.\"{repository_path}\"]\ntrust_level = \"trusted\"\n");
        let codex_home = temp.root.join("home/.codex");
        fs::write(codex_home.join("config.toml"), &trust).expect("caller trust entry");
        let Some(result) = run_or_skip_in_project(
            AgentKind::Codex,
            None,
            &project,
            executable,
            &workspace,
            &scratch,
            &target,
            b"prompt\n",
            10,
        ) else {
            return;
        };
        let candidate = result.unwrap_or_else(|error| panic!("{case}: {error}"));
        assert_eq!(candidate.implementation, b"done\n", "{case}");
        assert_eq!(
            fs::read_to_string(codex_home.join("config.toml")).expect("trust entry"),
            trust,
            "{case}"
        );
        assert_eq!(
            fs::read_to_string(common.join("HEAD")).expect("HEAD"),
            "ref: refs/heads/main\n",
            "{case}"
        );
        assert_eq!(
            fs::read_to_string(repository.join("AGENTS.md")).expect("ancestor rules"),
            "repository rules",
            "{case}"
        );
        assert!(!repository.join("new-file").exists(), "{case}");
        assert!(!project.join("implementation.py").exists(), "{case}");
    }
}

/// Run `script` with the host's Python (its `sqlite3` module) and return
/// stdout; the fixtures below use it to act as a concurrent host session.
fn host_python(script: &str, arguments: &[&Path]) -> String {
    let output = std::process::Command::new("python3")
        .arg("-c")
        .arg(script)
        .args(arguments)
        .output()
        .expect("run host python3");
    assert!(
        output.status.success(),
        "host python3 failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    String::from_utf8(output.stdout).expect("UTF-8 host output")
}

fn wait_for(path: &Path) -> bool {
    let deadline = std::time::Instant::now() + std::time::Duration::from_secs(20);
    while !path.exists() {
        if std::time::Instant::now() > deadline {
            return false;
        }
        std::thread::sleep(std::time::Duration::from_millis(10));
    }
    true
}

/// A JSON login store is shared with the host as the directory itself: the
/// CLI in the sandbox sees the host session's lock directory (the
/// `proper-lockfile` convention) and its advisory `flock`, waits until the
/// host releases them, and replaces the login with an atomic `rename` that
/// the host observes on the same device and directory inode.
#[test]
fn json_login_store_updates_atomically_under_locks_shared_with_the_host() {
    use std::os::unix::io::AsRawFd;

    let (temp, workspace, scratch, target) = fixture();
    let body = r#"store=$CODEX_HOME
if mkdir "$store/auth.json.lock" 2>/dev/null; then exit 20; fi
if flock -n -x "$store/auth.flock" true; then exit 21; fi
: > "$store/agent-waiting" || exit 22
i=0
while ! mkdir "$store/auth.json.lock" 2>/dev/null; do i=$((i + 1)); [ "$i" -lt 400 ] || exit 23; sleep 0.05; done
flock -x -w 20 "$store/auth.flock" sh -c 'printf "%s" "{\"tokens\":\"refreshed\"}" > "$1/auth.json.tmp" && mv "$1/auth.json.tmp" "$1/auth.json"' sh "$store" || exit 24
rmdir "$store/auth.json.lock" || exit 25
stat -c '%d:%i' "$store" "$store/auth.json" > implementation.py"#;
    let executable = fake_adapter(&workspace, "codex-cli 0.147.1", body);
    let _lock = _hold_env_lock();
    let _environment = EnvRestore::controlled(&scratch, &executable);
    let store = temp.root.join("home/.codex");
    fs::write(store.join("auth.json"), r#"{"tokens":"stale"}"#).expect("caller login");
    let stale_inode = fs::metadata(store.join("auth.json")).expect("login").ino();
    // A concurrent host session holds both locks.
    fs::create_dir(store.join("auth.json.lock")).expect("host lock directory");
    let flock = fs::File::create(store.join("auth.flock")).expect("host lock file");
    // SAFETY: the descriptor is open for the duration of the call.
    assert_eq!(unsafe { libc::flock(flock.as_raw_fd(), libc::LOCK_EX) }, 0);
    let host = {
        let store = store.clone();
        std::thread::spawn(move || {
            if !wait_for(&store.join("agent-waiting")) {
                return false;
            }
            fs::remove_dir(store.join("auth.json.lock")).expect("release lock directory");
            drop(flock);
            true
        })
    };
    let Some(result) = run_or_skip_with_timeout(
        AgentKind::Codex,
        executable,
        &workspace,
        &scratch,
        &target,
        b"prompt",
        30,
    ) else {
        return;
    };
    assert!(
        host.join().expect("host session"),
        "the agent never waited for the host's locks: {result:?}"
    );
    let candidate = result.expect("login refresh under the host's locks");
    let directory = fs::metadata(&store).expect("store");
    let login = fs::symlink_metadata(store.join("auth.json")).expect("login");
    assert_eq!(
        String::from_utf8(candidate.implementation).expect("identities"),
        format!(
            "{}:{}\n{}:{}\n",
            directory.dev(),
            directory.ino(),
            login.dev(),
            login.ino()
        )
    );
    assert_ne!(
        login.ino(),
        stale_inode,
        "replaced by rename, not rewritten"
    );
    assert!(login.is_file() && login.nlink() == 1);
    assert_eq!(
        fs::read_to_string(store.join("auth.json")).expect("login"),
        r#"{"tokens":"refreshed"}"#
    );
    assert!(!store.join("auth.json.tmp").exists());
    assert!(!store.join("auth.json.lock").exists());
}

const SQLITE_AGENT: &str = r#"python3 - <<'PY' || exit $?
import os, sqlite3, sys, time
store = os.environ["PI_CODING_AGENT_DIR"]
db = os.path.join(store, "agent.db")
c = sqlite3.connect(db, timeout=20, isolation_level=None)
if c.execute("pragma journal_mode").fetchone()[0] != "wal":
    sys.exit(30)
c.execute("insert into t values ('agent', 1, null)")
open(os.path.join(store, "agent-ready"), "w").close()
deadline = time.time() + 20
while not os.path.exists(os.path.join(store, "host-go")):
    if time.time() > deadline:
        sys.exit(31)
    time.sleep(0.01)
if c.execute("select count(*) from t where who = 'host' and n = 1").fetchone()[0] != 1:
    sys.exit(32)
for n in range(2, 52):
    c.execute("insert into t values ('agent', ?, null)", (n,))
stats = " ".join("%d:%d" % (s.st_dev, s.st_ino) for s in (os.stat(db + x) for x in ("", "-wal", "-shm")))
with open("implementation.py", "w") as f:
    f.write(stats)
open(os.path.join(store, "agent-done"), "w").close()
c.close()
PY"#;

const SQLITE_HOST: &str = r#"
import json, os, sqlite3, sys, time
store = sys.argv[1]
db = os.path.join(store, "agent.db")
def wait(name):
    deadline = time.time() + 20
    while not os.path.exists(os.path.join(store, name)):
        if time.time() > deadline:
            print(json.dumps({"timeout": name}))
            sys.exit(0)
        time.sleep(0.01)
wait("agent-ready")
created = [os.path.exists(db + suffix) for suffix in ("-wal", "-shm")]
c = sqlite3.connect(db, timeout=20, isolation_level=None)
seen = c.execute("select count(*) from t where who = 'agent'").fetchone()[0]
c.execute("insert into t values ('host', 1, null)")
open(os.path.join(store, "host-go"), "w").close()
for n in range(2, 52):
    c.execute("insert into t values ('host', ?, null)", (n,))
wait("agent-done")
stats = " ".join("%d:%d" % (s.st_dev, s.st_ino) for s in (os.stat(db + x) for x in ("", "-wal", "-shm")))
c.close()
print(json.dumps({"created": created, "seen": seen, "stats": stats}))
"#;

const SQLITE_CHECK: &str = r#"
import json, sqlite3, sys
c = sqlite3.connect(sys.argv[1])
print(json.dumps({
    "integrity": c.execute("pragma integrity_check").fetchone()[0],
    "journal_mode": c.execute("pragma journal_mode").fetchone()[0],
    "rows": {who: count for who, count in c.execute("select who, count(*) from t group by who")},
}))
"#;

fn sqlite_store(store: &Path, journal_mode: &str) {
    host_python(
        &format!(
            "import sqlite3, sys\nc = sqlite3.connect(sys.argv[1], isolation_level=None)\nc.execute('pragma journal_mode = {journal_mode}')\nc.execute('create table t (who text, n integer, payload blob)')\nc.execute(\"insert into t values ('host', 0, zeroblob(16))\")\nc.close()\n"
        ),
        &[&store.join("agent.db")],
    );
}

fn sqlite_check(store: &Path) -> serde_json::Value {
    serde_json::from_str(&host_python(SQLITE_CHECK, &[&store.join("agent.db")]))
        .expect("SQLite check JSON")
}

/// A second, independent generation run against the same store (fresh
/// workspace and scratch), recording one `rerun` row.
fn sqlite_rerun(root: &Path, name: &str) -> Option<Result<AgentRunCandidate, String>> {
    let workspace = root.join(format!("{name}-workspace"));
    let scratch = root.join(format!("{name}-scratch"));
    fs::create_dir(&workspace).expect("rerun workspace");
    fs::create_dir(&scratch).expect("rerun scratch");
    let executable = fake_adapter(
        &workspace,
        "omp/17.2.13",
        r#"python3 - <<'PY' || exit $?
import os, sqlite3
c = sqlite3.connect(os.path.join(os.environ["PI_CODING_AGENT_DIR"], "agent.db"), timeout=20, isolation_level=None)
c.execute("insert into t values ('rerun', 1, null)")
c.close()
open("implementation.py", "w").write("rerun")
PY"#,
    );
    run_or_skip_with_timeout(
        AgentKind::Omp,
        executable,
        &workspace,
        &scratch,
        &workspace.join("implementation.py"),
        b"prompt",
        30,
    )
}

/// OMP's SQLite store is shared with the host as its directory: the `-wal`
/// and `-shm` files the sandboxed CLI creates during the run are the host's
/// files (same device and inodes, the shared-memory index mapped by both),
/// host and sandbox read each other's commits and write concurrently while
/// both are connected, a rerun works, and the database stays intact.
#[test]
fn sqlite_store_shares_wal_and_shm_with_concurrent_host_connections() {
    let (temp, workspace, scratch, target) = fixture();
    let executable = fake_adapter(&workspace, "omp/17.2.13", SQLITE_AGENT);
    let _lock = _hold_env_lock();
    let _environment = EnvRestore::controlled(&scratch, &executable);
    let store = temp.root.join("home/.omp/agent");
    sqlite_store(&store, "wal");
    assert!(!store.join("agent.db-wal").exists() && !store.join("agent.db-shm").exists());
    let host = std::process::Command::new("python3")
        .arg("-c")
        .arg(SQLITE_HOST)
        .arg(&store)
        .stdout(std::process::Stdio::piped())
        .stderr(std::process::Stdio::piped())
        .spawn()
        .expect("host SQLite session");
    let result = run_or_skip_with_timeout(
        AgentKind::Omp,
        executable,
        &workspace,
        &scratch,
        &target,
        b"prompt",
        60,
    );
    let host = host.wait_with_output().expect("host SQLite session");
    let Some(result) = result else {
        return;
    };
    let candidate = result.expect("OMP run on the shared SQLite store");
    assert!(
        host.status.success(),
        "{}",
        String::from_utf8_lossy(&host.stderr)
    );
    let host: serde_json::Value = serde_json::from_slice(&host.stdout).expect("host JSON");
    assert_eq!(
        host["created"],
        serde_json::json!([true, true]),
        "WAL and shared-memory files created by the sandboxed CLI: {host}"
    );
    assert_eq!(host["seen"], 1, "the host read the sandbox's commit");
    assert_eq!(
        host["stats"].as_str().expect("host identities"),
        String::from_utf8(candidate.implementation)
            .expect("sandbox identities")
            .trim_end(),
        "database, WAL and shared-memory index are the same files"
    );
    let rerun = sqlite_rerun(&temp.root, "rerun")
        .expect("bubblewrap available")
        .expect("rerun on the shared store");
    assert_eq!(rerun.implementation, b"rerun\n");
    let check = sqlite_check(&store);
    assert_eq!(check["integrity"], "ok");
    assert_eq!(check["journal_mode"], "wal");
    assert_eq!(
        check["rows"],
        serde_json::json!({"agent": 51, "host": 52, "rerun": 1})
    );
    for name in ["agent.db", "agent.db-wal", "agent.db-shm"] {
        if let Ok(metadata) = fs::symlink_metadata(store.join(name)) {
            assert!(metadata.is_file() && metadata.nlink() == 1, "{name}");
        }
    }
}

/// A sandboxed CLI killed in the middle of a SQLite write transaction (the
/// run's wall-clock limit) leaves the shared store as SQLite itself would
/// after a crash: a WAL with uncommitted frames or a hot rollback journal.
/// The next run accepts the existing journal files, SQLite recovers, the
/// uncommitted rows are gone and `integrity_check` passes.
#[test]
fn interrupted_sqlite_writer_leaves_a_recoverable_consistent_store() {
    let _lock = _hold_env_lock();
    for journal_mode in ["wal", "delete"] {
        let (temp, workspace, scratch, target) = fixture();
        let executable = fake_adapter(
            &workspace,
            "omp/17.2.13",
            r#"python3 - <<'PY' || exit $?
import os, sqlite3, time
store = os.environ["PI_CODING_AGENT_DIR"]
c = sqlite3.connect(os.path.join(store, "agent.db"), timeout=20, isolation_level=None)
c.execute("pragma cache_size = 2")
c.execute("begin immediate")
for n in range(2000):
    c.execute("insert into t values ('uncommitted', ?, zeroblob(1024))", (n,))
open(os.path.join(store, "agent-in-transaction"), "w").close()
time.sleep(60)
PY"#,
        );
        let _environment = EnvRestore::controlled(&scratch, &executable);
        let store = temp.root.join("home/.omp/agent");
        sqlite_store(&store, journal_mode);
        let Some(result) = run_or_skip_with_timeout(
            AgentKind::Omp,
            executable,
            &workspace,
            &scratch,
            &target,
            b"prompt",
            3,
        ) else {
            return;
        };
        let error = result.expect_err(journal_mode);
        assert!(error.contains("timed out"), "{journal_mode}: {error}");
        assert!(
            store.join("agent-in-transaction").exists(),
            "{journal_mode}: killed inside the transaction: {error}"
        );
        let leftover = if journal_mode == "wal" {
            "agent.db-wal"
        } else {
            "agent.db-journal"
        };
        let metadata =
            fs::symlink_metadata(store.join(leftover)).expect("journal left by the kill");
        assert!(
            metadata.is_file() && metadata.nlink() == 1 && metadata.len() > 0,
            "{journal_mode}"
        );
        let rerun = sqlite_rerun(&temp.root, "rerun")
            .expect("bubblewrap available")
            .unwrap_or_else(|error| panic!("{journal_mode}: rerun after the kill: {error}"));
        assert_eq!(rerun.implementation, b"rerun\n");
        let check = sqlite_check(&store);
        assert_eq!(check["integrity"], "ok", "{journal_mode}");
        assert_eq!(check["journal_mode"], journal_mode);
        assert_eq!(
            check["rows"],
            serde_json::json!({"host": 1, "rerun": 1}),
            "{journal_mode}: uncommitted rows rolled back"
        );
        if journal_mode == "delete" {
            assert!(!store.join("agent.db-journal").exists());
        }
    }
}

/// SQLite companion files are login stores too: a hard-linked database,
/// WAL or journal would let the CLI's writes change another path.
#[test]
fn sqlite_store_files_must_not_be_hard_links() {
    let _lock = _hold_env_lock();
    for name in ["agent.db", "agent.db-wal", "agent.db-journal"] {
        let (temp, workspace, scratch, target) = fixture();
        let executable = fake_adapter(&workspace, "omp/17.2.13", "printf x > implementation.py");
        let _environment = EnvRestore::controlled(&scratch, &executable);
        let store = temp.root.join("home/.omp/agent");
        fs::write(store.join(name), "data").expect("store file");
        fs::hard_link(store.join(name), temp.root.join("elsewhere")).expect("second link");
        let error = run_agent(
            AgentSelection {
                kind: AgentKind::Omp,
                model: None,
            },
            executable,
            &workspace,
            &scratch,
            &target,
            b"prompt".to_vec(),
            10,
        )
        .expect_err(name);
        assert!(
            error.contains("must be a regular single-link file owned by the caller"),
            "{name}: {error}"
        );
        assert_eq!(fs::read(&target).expect("untouched target"), b"", "{name}");
    }
}

#[test]
fn claude_runs_at_the_project_path_with_the_callers_settings_login_and_memory() {
    let (temp, workspace, scratch, target) = fixture();
    let project = temp.root.join("project");
    fs::create_dir_all(project.join(".claude")).expect("project Claude directory");
    fs::write(
        project.join(".claude/settings.json"),
        r#"{"permissions":{}}"#,
    )
    .expect("project settings");
    fs::write(project.join("CLAUDE.md"), "project memory").expect("project memory");
    // Claude Code loads CLAUDE.md from every ancestor of its working directory.
    fs::write(temp.root.join("CLAUDE.md"), "ancestor memory").expect("ancestor memory");
    let project_path = fs::canonicalize(&project).expect("canonical project");
    let body = format!(
        r#"[ "$(pwd)" = '{project}' ] || exit 3
[ "$(cat "$HOME/.claude/settings.json")" = '{{"model":"opus"}}' ] || exit 4
[ "$(cat "$HOME/.claude.json")" = '{{"oauthAccount":{{}}}}' ] || exit 5
[ "$(cat CLAUDE.md)" = 'project memory' ] || exit 6
[ "$(cat ../CLAUDE.md)" = 'ancestor memory' ] || exit 7
[ "$(cat .claude/settings.json)" = '{{"permissions":{{}}}}' ] || exit 8
printf refreshed > "$HOME/.claude/.credentials.json.tmp" && mv "$HOME/.claude/.credentials.json.tmp" "$HOME/.claude/.credentials.json" || exit 9
mkdir -p "$HOME/.claude/statsig" && printf cached > "$HOME/.claude/statsig/cache" || exit 10
if (printf x > "$HOME/.claude.json") 2>/dev/null; then exit 11; fi
if (printf x > ../CLAUDE.md) 2>/dev/null; then exit 12; fi
printf done > implementation.py
printf '%s' '{CLAUDE_RESULT}'"#,
        project = project_path.display()
    );
    let executable = fake_claude_adapter(&workspace, "2.1.89", &body);
    let _lock = _hold_env_lock();
    let _environment = EnvRestore::controlled(&scratch, &executable);
    let home = temp.root.join("home");
    fs::create_dir_all(home.join(".claude")).expect("Claude configuration");
    fs::write(home.join(".claude/settings.json"), r#"{"model":"opus"}"#).expect("settings");
    fs::write(home.join(".claude/.credentials.json"), "stale").expect("login");
    fs::write(home.join(".claude.json"), r#"{"oauthAccount":{}}"#).expect("global state");
    let Some(result) = run_or_skip_in_project(
        AgentKind::Claude,
        None,
        &project,
        executable,
        &workspace,
        &scratch,
        &target,
        b"claude prompt\n",
        10,
    ) else {
        return;
    };
    let candidate = result.expect("Claude run with the caller's setup");
    assert_eq!(candidate.implementation, b"done\n");
    assert_eq!(candidate.resolved_models, ["claude-test-model"]);
    assert_eq!(
        fs::read_to_string(home.join(".claude/.credentials.json")).expect("login"),
        "refreshed"
    );
    assert_eq!(
        fs::read_to_string(home.join(".claude/statsig/cache")).expect("cache"),
        "cached"
    );
    assert_eq!(
        fs::read_to_string(home.join(".claude/settings.json")).expect("settings"),
        r#"{"model":"opus"}"#
    );
    assert_eq!(
        fs::read_to_string(home.join(".claude.json")).expect("global state"),
        r#"{"oauthAccount":{}}"#
    );
    assert_eq!(
        fs::read_to_string(temp.root.join("CLAUDE.md")).expect("ancestor memory"),
        "ancestor memory"
    );
}

fn rejects_model_in_argv(exit_code: i32) -> String {
    format!(
        r#"for arg do
    if [ "$arg" = "--model" ]; then
        exit {exit_code}
    fi
done"#
    )
}

#[test]
fn codex_requested_model_is_inserted_after_exec_and_recorded_in_argv_template() {
    let (_temp, workspace, scratch, target) = fixture();
    let version_probe = format!(
        "{}\nprintf '%s\\n' 'codex-cli 0.147.1'\nexit 0",
        rejects_model_in_argv(9)
    );
    let executable =
        fake_adapter_with_version_probe(&workspace, &version_probe, &capture_body(None));
    let _lock = _hold_env_lock();
    let _environment = EnvRestore::controlled(&scratch, &executable);
    let model = "gpt-5-codex high";
    assert!(valid_model(model));
    let prompt = b"codex prompt\n";
    let Some(result) = run_or_skip_with_model(
        AgentKind::Codex,
        Some(model),
        executable,
        &workspace,
        &scratch,
        &target,
        prompt,
        10,
    ) else {
        return;
    };
    let candidate = result.expect("Codex run with a requested model");
    assert_eq!(candidate.adapter_version, "0.147.1");
    let expected_args = vec![
        "exec".to_owned(),
        "--model".to_owned(),
        model.to_owned(),
        "--ephemeral".to_owned(),
        "--skip-git-repo-check".to_owned(),
        "--color".to_owned(),
        "never".to_owned(),
        "--cd".to_owned(),
        workspace.display().to_string(),
        "-".to_owned(),
    ];
    let expected_names = INHERITED_NAMES;
    assert_eq!(
        candidate.implementation,
        expected_capture(&expected_args, prompt, &expected_names)
    );
    assert_eq!(candidate.environment_names, recorded_names());
    let mut expected_template: Vec<String> = CODEX
        .argv_template
        .iter()
        .map(ToString::to_string)
        .collect();
    expected_template.splice(1..1, ["--model".to_owned(), model.to_owned()]);
    assert_eq!(candidate.argv_template, expected_template);
}

#[test]
fn omp_requested_model_is_inserted_before_flags_and_recorded_in_argv_template() {
    let (_temp, workspace, scratch, target) = fixture();
    let version_probe = format!(
        "{}\nprintf '%s\\n' 'omp/17.2.13'\nexit 0",
        rejects_model_in_argv(9)
    );
    let executable =
        fake_adapter_with_version_probe(&workspace, &version_probe, &capture_body(None));
    let _lock = _hold_env_lock();
    let _environment = EnvRestore::controlled(&scratch, &executable);
    let model = "omp-flagship-2 preview";
    assert!(valid_model(model));
    let prompt = b"omp prompt";
    let Some(result) = run_or_skip_with_model(
        AgentKind::Omp,
        Some(model),
        executable,
        &workspace,
        &scratch,
        &target,
        prompt,
        10,
    ) else {
        return;
    };
    let candidate = result.expect("OMP run with a requested model");
    assert_eq!(candidate.adapter_version, "17.2.13");
    let prompt_file = fs::canonicalize(&scratch)
        .expect("canonical scratch")
        .join("omp-prompt-0");
    let expected_args = vec![
        "--model".to_owned(),
        model.to_owned(),
        "-p".to_owned(),
        "--cwd".to_owned(),
        workspace.display().to_string(),
        "--no-session".to_owned(),
        "--no-pty".to_owned(),
        "--no-title".to_owned(),
        "--max-time".to_owned(),
        "10s".to_owned(),
        format!("@{}", prompt_file.display()),
    ];
    let expected_names = INHERITED_NAMES;
    assert_eq!(
        candidate.implementation,
        expected_capture(&expected_args, &[], &expected_names)
    );
    assert_eq!(candidate.environment_names, recorded_names());
    let mut expected_template: Vec<String> =
        OMP.argv_template.iter().map(ToString::to_string).collect();
    expected_template.splice(0..0, ["--model".to_owned(), model.to_owned()]);
    assert_eq!(candidate.argv_template, expected_template);
}

#[test]
fn claude_requested_model_is_inserted_before_flags_and_recorded_in_argv_template() {
    let (_temp, workspace, scratch, target) = fixture();
    let version_probe = format!(
        "{}\n[ -z \"${{ANTHROPIC_API_KEY+x}}\" ] || exit 2\nprintf '%s\\n' '2.1.89'\nexit 0",
        rejects_model_in_argv(9)
    );
    let executable =
        fake_adapter_with_version_probe(&workspace, &version_probe, &claude_capture_body());
    let _lock = _hold_env_lock();
    let _environment = EnvRestore::controlled(&scratch, &executable);
    let model = "claude-opus-5-5 thinking";
    assert!(valid_model(model));
    let prompt = b"claude prompt\n";
    let Some(result) = run_or_skip_with_model(
        AgentKind::Claude,
        Some(model),
        executable,
        &workspace,
        &scratch,
        &target,
        prompt,
        10,
    ) else {
        return;
    };
    let candidate = result.expect("Claude run with a requested model");
    assert_eq!(candidate.adapter_version, "2.1.89");
    let expected_args = vec![
        "--model".to_owned(),
        model.to_owned(),
        "--print".to_owned(),
        "--input-format".to_owned(),
        "text".to_owned(),
        "--output-format".to_owned(),
        "json".to_owned(),
        "--no-session-persistence".to_owned(),
    ];
    let expected_names = INHERITED_NAMES;
    assert_eq!(
        candidate.implementation,
        expected_capture(&expected_args, prompt, &expected_names)
    );
    assert_eq!(candidate.environment_names, recorded_names());
    let mut expected_template: Vec<String> = CLAUDE
        .argv_template
        .iter()
        .map(ToString::to_string)
        .collect();
    expected_template.splice(0..0, ["--model".to_owned(), model.to_owned()]);
    assert_eq!(candidate.argv_template, expected_template);
}

#[test]
fn invalid_model_fails_before_any_external_command_across_adapters() {
    let (_temp, workspace, scratch, target) = fixture();
    let missing_scratch = scratch.join("does-not-exist");
    let missing_executable = workspace.join("does-not-exist-either");
    for kind in [AgentKind::Codex, AgentKind::Omp, AgentKind::Claude] {
        for model in ["", " gpt-5 ", "gpt\u{0}5", "-gpt-5", "gpt-5\n", "gpt-5\t"] {
            assert!(
                !valid_model(model),
                "{model:?} should be rejected by valid_model"
            );
            let result = run_agent(
                AgentSelection {
                    kind,
                    model: Some(model),
                },
                missing_executable.clone(),
                &workspace,
                &missing_scratch,
                &target,
                b"prompt".to_vec(),
                10,
            );
            let error = result.expect_err(&format!("{kind:?} model {model:?} must be rejected"));
            assert!(
                error.contains("invalid agent model"),
                "{kind:?} {model:?}: {error}"
            );
            assert!(
                !target.exists(),
                "{kind:?} {model:?} must fail before touching the target"
            );
        }
    }
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
        AgentSelection {
            kind: AgentKind::Omp,
            model: None,
        },
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
        AgentSelection {
            kind: AgentKind::Omp,
            model: None,
        },
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
    // Test result validation only after the provider has consumed the prompt;
    // exiting earlier races the sandbox's stdin writer and can return EPIPE.
    let executable = fake_adapter(
        &workspace,
        "2.1.89",
        "cat > /dev/null\nprintf implementation > implementation.py\nprintf '%s' '{\"type\":\"result\",\"subtype\":\"error\",\"is_error\":true,\"result\":\"no\"}'",
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
    let error = result.expect_err("Claude error result must fail");
    assert!(
        error.contains("claude returned an invalid result"),
        "{error}"
    );
}

#[test]
fn claude_rejects_malformed_and_multiple_version_tokens() {
    let _lock = _hold_env_lock();
    for version in ["2.1", "2.1.89 extra"] {
        let (_temp, workspace, scratch, target) = fixture();
        let executable = fake_adapter(&workspace, version, "exit 0");
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
        AgentSelection {
            kind: AgentKind::Claude,
            model: None,
        },
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
        AgentSelection {
            kind: AgentKind::Claude,
            model: None,
        },
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

// ---------------------------------------------------------------------------
// Pi adapter against a MOCK Pi installation (tests/support/mock_pi.rs). These
// runs exercise cott's sandbox, argv, environment, probes, and JSONL
// validation; none of them is a real Pi or provider run.

#[path = "support/mock_pi.rs"]
mod mock_pi;

const PI_PROMPT: &str = "  \n\tExact prompt: 'single' \"double\" `tick` $(touch sibling.py) \\ 한글 ✓ — write implementation.py\n\n  ";
const PI_MODEL: &str = "openai/gpt-test";

fn pi_config(scenario: &str, host_paths: &[&Path]) -> serde_json::Value {
    serde_json::json!({
        "scenario": scenario,
        "candidate": "generated through mock pi\n",
        "host_paths": host_paths.iter().map(|path| path.display().to_string()).collect::<Vec<_>>(),
    })
}

fn run_mock_pi(
    mock: &mock_pi::MockPi,
    model: Option<&str>,
    workspace: &Path,
    scratch: &Path,
    target: &Path,
    prompt: &[u8],
    timeout_seconds: u16,
) -> Option<Result<AgentRunCandidate, String>> {
    run_or_skip_with_model(
        AgentKind::Pi,
        model,
        mock.cli.clone(),
        workspace,
        scratch,
        target,
        prompt,
        timeout_seconds,
    )
}

fn pi_capture(scratch: &Path) -> serde_json::Value {
    serde_json::from_slice(&fs::read(scratch.join("pi-capture.json")).expect("mock Pi capture"))
        .expect("mock Pi capture JSON")
}

#[test]
fn mock_pi_golden_argv_exact_prompt_user_setup_stream_and_provenance() {
    let (temp, workspace, scratch, target) = fixture();
    let host_home = temp.root.join("host-home");
    let host_agent = host_home.join(".pi/agent");
    fs::create_dir_all(host_agent.join("extensions")).expect("host Pi agent directory");
    let local_package = temp.root.join("local-package");
    fs::create_dir_all(&local_package).expect("local Pi package");
    fs::write(local_package.join("index.js"), "export default () => {}").expect("local package");
    let settings = serde_json::json!({
        "packages": ["npm:host-extension", local_package.display().to_string()],
        "defaultProvider": "cliproxyapi",
        "defaultModel": "gpt-6.1-sol",
    })
    .to_string();
    for (name, body) in [
        (
            "auth.json",
            r#"{"cliproxyapi":{"type":"oauth","refresh":"host-refresh-token"}}"#,
        ),
        ("settings.json", settings.as_str()),
        ("models.json", r#"{"providers":{}}"#),
        ("extensions/host.js", "export default () => {}"),
    ] {
        fs::write(host_agent.join(name), body).expect("host Pi customization");
    }
    let project = temp.root.join("project");
    fs::create_dir_all(project.join(".pi")).expect("project Pi directory");
    fs::write(
        project.join(".pi/settings.json"),
        r#"{"packages":["npm:project"]}"#,
    )
    .expect("project Pi settings");
    fs::write(project.join("AGENTS.md"), "project context").expect("project context file");
    let mut config = pi_config(
        "success",
        &[
            &host_agent.join("auth.json"),
            &host_agent.join("settings.json"),
            &host_agent.join("extensions/host.js"),
            &local_package.join("index.js"),
        ],
    );
    config["refresh_auth"] = serde_json::json!(true);
    let mock = mock_pi::install(&temp.root, "1.0.4", "v22.19.0", config);
    let entrypoint = fs::read(&mock.cli).expect("mock entrypoint bytes");
    let _lock = _hold_env_lock();
    let _environment = EnvRestore::controlled(&scratch, &mock.cli)
        .with_path(&mock.bin)
        .with_var("HOME", Some(host_home.to_str().expect("UTF-8 home")))
        .with_var("PI_CODING_AGENT_DIR", None)
        .with_var("OPENAI_API_KEY", Some("openai-secret-api-key"))
        .with_var("GEMINI_API_KEY", Some("gemini-secret-api-key"));
    let Some(result) = run_or_skip_in_project(
        AgentKind::Pi,
        Some(PI_MODEL),
        &project,
        mock.cli.clone(),
        &workspace,
        &scratch,
        &target,
        PI_PROMPT.as_bytes(),
        10,
    ) else {
        return;
    };
    let candidate = result.expect("mock Pi run");
    let scratch = fs::canonicalize(&scratch).expect("canonical scratch");
    let mut expected_argv = vec!["--model".to_owned(), PI_MODEL.to_owned()];
    expected_argv.extend(
        PI.argv_template[..PI.argv_template.len() - 1]
            .iter()
            .map(|arg| (*arg).to_owned()),
    );
    expected_argv.push(PI_PROMPT.to_owned());
    let capture = pi_capture(&scratch);
    assert_eq!(capture["argv"], serde_json::json!(expected_argv));
    assert_eq!(capture["stdin"], "");
    // Pi works at the caller project's own path, where the sandbox presents
    // the isolated workspace.
    assert_eq!(
        capture["cwd"],
        fs::canonicalize(&project)
            .expect("canonical project")
            .display()
            .to_string()
    );
    // The caller's own agent directory, settings, extension, and a
    // settings-named local package are visible where Pi looks for them.
    assert_eq!(
        capture["agent_dir_entries"],
        serde_json::json!(["auth.json", "extensions", "models.json", "settings.json"])
    );
    assert_eq!(
        capture["visible_host_paths"]
            .as_array()
            .expect("paths")
            .len(),
        4
    );
    assert_eq!(capture["settings"]["defaultModel"], "gpt-6.1-sol");
    // The caller project's context and Pi settings, read-only.
    assert_eq!(capture["project_context"], "project context");
    assert_eq!(capture["project_write"], "blocked");
    let entries = capture["cwd_entries"].as_array().expect("cwd entries");
    assert!(
        entries.contains(&serde_json::json!(".pi"))
            && entries.contains(&serde_json::json!("AGENTS.md"))
    );
    let names = capture["environment_names"]
        .as_array()
        .expect("environment names")
        .iter()
        .map(|name| name.as_str().expect("name"))
        .collect::<Vec<_>>();
    for inherited in [
        "OPENAI_API_KEY",
        "GEMINI_API_KEY",
        "COTT_TEST_CUSTOM",
        "CODEX_API_KEY",
        "HTTPS_PROXY",
        "SSL_CERT_FILE",
    ] {
        assert!(names.contains(&inherited), "{inherited} must be inherited");
    }
    for absent in [
        "PI_OFFLINE",
        "PI_SKIP_VERSION_CHECK",
        "PI_TELEMETRY",
        "PI_CODING_AGENT_DIR",
        "PI_SESSION_ID",
        "CLAUDECODE",
        "CODEX_SANDBOX_NETWORK_DISABLED",
    ] {
        assert!(!names.contains(&absent), "{absent} must not be set");
    }
    let environment = capture["environment"].as_object().expect("environment");
    assert_eq!(environment["HOME"], host_home.display().to_string());
    assert_eq!(environment["PATH"], mock.bin.display().to_string());
    assert_eq!(environment["TMPDIR"], scratch.display().to_string());
    assert_eq!(environment["COTT_TEST_CUSTOM"], "custom-value");
    // Pi's own writes went to the caller's agent directory itself (the same
    // device and inode): the refreshed login and the extension cache
    // persisted, the lock directory was released, settings are untouched.
    let host_identity = fs::metadata(&host_agent).expect("host agent directory");
    assert_eq!(
        capture["agent_dir_identity"],
        serde_json::json!([host_identity.dev(), host_identity.ino()])
    );
    assert_eq!(
        fs::read_to_string(host_agent.join("auth.json")).expect("host auth"),
        r#"{"refreshed":true}"#
    );
    assert_eq!(
        fs::read_to_string(host_agent.join("models-cache.json")).expect("extension cache"),
        "{}"
    );
    assert_eq!(
        fs::read_to_string(host_agent.join("settings.json")).expect("host settings"),
        settings
    );
    assert!(!host_agent.join("sessions").exists());
    assert!(!host_agent.join("auth.json.lock").exists());
    assert_eq!(
        fs::read_to_string(project.join("AGENTS.md")).expect("project context"),
        "project context"
    );
    assert_eq!(candidate.implementation, b"generated through mock pi\n");
    assert_eq!(candidate.adapter_version, "1.0.4");
    assert_eq!(candidate.executable, mock.cli);
    assert_eq!(
        candidate.executable_hash,
        format!("sha256:{}", sha256_hex(&entrypoint))
    );
    assert_eq!(
        candidate.prompt_hash,
        format!("sha256:{}", sha256_hex(PI_PROMPT.as_bytes()))
    );
    let mut expected_template = vec!["--model".to_owned(), PI_MODEL.to_owned()];
    expected_template.extend(PI.argv_template.iter().map(|arg| (*arg).to_owned()));
    assert_eq!(candidate.argv_template, expected_template);
    assert_eq!(candidate.environment_names, recorded_names());
    assert_eq!(candidate.resolved_models, [PI_MODEL]);
    assert_eq!(candidate.exit_code, Some(0));
    for secret in [
        "openai-secret-api-key",
        "gemini-secret-api-key",
        "host-refresh-token",
    ] {
        for stream in [
            &candidate.stdout,
            &candidate.stderr,
            &candidate.implementation,
        ] {
            assert!(
                !stream
                    .windows(secret.len())
                    .any(|window| window == secret.as_bytes())
            );
        }
    }
    assert!(!workspace.join("sibling.py").exists());
}

#[test]
fn mock_pi_without_model_uses_the_callers_default_model_and_reports_it() {
    let (temp, workspace, scratch, target) = fixture();
    let agent = temp.root.join("custom-agent");
    fs::create_dir_all(&agent).expect("custom Pi agent directory");
    fs::write(
        agent.join("settings.json"),
        r#"{"defaultProvider":"cliproxyapi","defaultModel":"gpt-6.1-sol"}"#,
    )
    .expect("default model settings");
    let mock = mock_pi::install(&temp.root, "1.0.4", "v22.19.0", pi_config("success", &[]));
    let _lock = _hold_env_lock();
    let _environment = EnvRestore::controlled(&scratch, &mock.cli)
        .with_path(&mock.bin)
        .with_var("PI_CODING_AGENT_DIR", Some(agent.to_str().expect("UTF-8")));
    let Some(result) = run_mock_pi(
        &mock,
        None,
        &workspace,
        &scratch,
        &target,
        PI_PROMPT.as_bytes(),
        10,
    ) else {
        return;
    };
    let candidate = result.expect("mock Pi run with the default model");
    let capture = pi_capture(&fs::canonicalize(&scratch).expect("canonical scratch"));
    let mut expected_argv = PI.argv_template[..PI.argv_template.len() - 1]
        .iter()
        .map(|arg| (*arg).to_owned())
        .collect::<Vec<_>>();
    expected_argv.push(PI_PROMPT.to_owned());
    assert_eq!(capture["argv"], serde_json::json!(expected_argv));
    assert_eq!(
        capture["environment"]["PI_CODING_AGENT_DIR"],
        agent.display().to_string()
    );
    assert_eq!(
        candidate.argv_template,
        PI.argv_template
            .iter()
            .map(|arg| (*arg).to_owned())
            .collect::<Vec<_>>()
    );
    assert_eq!(candidate.resolved_models, ["cliproxyapi/gpt-6.1-sol"]);
}

#[test]
fn mock_pi_accepts_routed_models_and_the_callers_tools() {
    let _lock = _hold_env_lock();
    for (scenario, models) in [
        ("routed-model", ["openai/other-model"]),
        ("user-tools", [PI_MODEL]),
    ] {
        let (temp, workspace, scratch, target) = fixture();
        let mock = mock_pi::install(&temp.root, "1.0.4", "v22.19.0", pi_config(scenario, &[]));
        let _environment = EnvRestore::controlled(&scratch, &mock.cli).with_path(&mock.bin);
        let Some(result) = run_mock_pi(
            &mock,
            Some(PI_MODEL),
            &workspace,
            &scratch,
            &target,
            PI_PROMPT.as_bytes(),
            10,
        ) else {
            return;
        };
        let candidate = result.expect(scenario);
        assert_eq!(candidate.resolved_models, models, "{scenario}");
    }
}

#[test]
fn mock_pi_rejects_unsuccessful_protocol_outcomes_even_with_exit_zero() {
    let _lock = _hold_env_lock();
    for (scenario, model, expected) in [
        (
            "provider-error",
            Some(PI_MODEL),
            "stopped with `error`: 500: mock failure",
        ),
        (
            "contaminated",
            Some(PI_MODEL),
            "line 1 is not a JSON object",
        ),
        (
            "truncated",
            Some(PI_MODEL),
            "does not end with a complete JSONL record",
        ),
        (
            "unsettled",
            Some(PI_MODEL),
            "does not end with `agent_settled`",
        ),
        ("length", Some(PI_MODEL), "stopped with `length`"),
        ("exit-3", Some(PI_MODEL), "pi failed with status Some(3)"),
        ("no-write", Some(PI_MODEL), "agent did not write target"),
        // No `--model` and no configured default: Pi's own failure.
        ("success", None, "No model configured"),
    ] {
        let (temp, workspace, scratch, target) = fixture();
        let mock = mock_pi::install(&temp.root, "1.0.4", "v24.0.0", pi_config(scenario, &[]));
        let _environment = EnvRestore::controlled(&scratch, &mock.cli)
            .with_path(&mock.bin)
            .with_var("OPENAI_API_KEY", Some("openai-secret-api-key"));
        let Some(result) = run_mock_pi(
            &mock,
            model,
            &workspace,
            &scratch,
            &target,
            PI_PROMPT.as_bytes(),
            10,
        ) else {
            return;
        };
        let error = result.expect_err(scenario);
        assert!(error.contains(expected), "{scenario}: {error}");
        assert!(
            !error.contains("openai-secret-api-key"),
            "{scenario}: {error}"
        );
    }
}

#[test]
fn mock_pi_timeout_is_a_failure() {
    let (temp, workspace, scratch, target) = fixture();
    let mock = mock_pi::install(&temp.root, "1.0.4", "v22.19.0", pi_config("sleep", &[]));
    let _lock = _hold_env_lock();
    let _environment = EnvRestore::controlled(&scratch, &mock.cli)
        .with_path(&mock.bin)
        .with_var("OPENAI_API_KEY", Some("openai-secret-api-key"));
    let Some(result) = run_mock_pi(
        &mock,
        Some(PI_MODEL),
        &workspace,
        &scratch,
        &target,
        PI_PROMPT.as_bytes(),
        3,
    ) else {
        return;
    };
    let error = result.expect_err("timeout");
    assert!(error.contains("timed out"), "{error}");
}

#[test]
fn mock_pi_prompt_at_the_argv_limit_is_delivered_exactly() {
    let (temp, workspace, scratch, target) = fixture();
    let mock = mock_pi::install(&temp.root, "1.0.4", "v22.19.0", pi_config("success", &[]));
    let _lock = _hold_env_lock();
    let _environment = EnvRestore::controlled(&scratch, &mock.cli)
        .with_path(&mock.bin)
        .with_var("OPENAI_API_KEY", Some("openai-secret-api-key"));
    let prompt = "x".repeat(pi_max_prompt_bytes());
    let Some(result) = run_mock_pi(
        &mock,
        Some(PI_MODEL),
        &workspace,
        &scratch,
        &target,
        prompt.as_bytes(),
        10,
    ) else {
        return;
    };
    result.expect("prompt at the argv limit");
    let capture = pi_capture(&fs::canonicalize(&scratch).expect("canonical scratch"));
    assert_eq!(
        capture["argv"]
            .as_array()
            .expect("argv")
            .last()
            .expect("prompt"),
        &prompt
    );
}

#[test]
fn pi_rejects_unsupported_installations_and_runtimes() {
    use std::os::unix::fs::symlink;

    let _lock = _hold_env_lock();
    for (case, expected, before_probe) in [
        ("bun-shebang", "official Node package entrypoint", true),
        (
            "package-name",
            "does not match the official package entrypoint",
            true,
        ),
        (
            "bin",
            "does not match the official package entrypoint",
            true,
        ),
        ("unpackaged", "of an installed package", true),
        (
            "escaping-link",
            "Pi package content escapes its package",
            true,
        ),
        ("missing-node", "missing Pi Node runtime on PATH", true),
        ("old-node", "pi requires Node >= 22.19.0", true),
        ("old-pi", "unsupported pi version `1.0.3`", false),
        ("major-2", "unsupported pi version `2.0.0`", false),
        ("probe-mismatch", "unsupported pi version `1.0.5`", false),
    ] {
        let (temp, workspace, scratch, target) = fixture();
        let version = match case {
            "old-pi" => "1.0.3",
            "major-2" => "2.0.0",
            _ => "1.0.4",
        };
        let node = if case == "old-node" {
            "v22.18.0"
        } else {
            "v22.19.0"
        };
        let mut mock = mock_pi::install(&temp.root, version, node, pi_config("success", &[]));
        let metadata = mock.package.join("package.json");
        match case {
            "bun-shebang" => {
                let body = mock_pi::MOCK_CLI.replacen("#!/usr/bin/env node", "#!/usr/bin/env bun", 1);
                fs::write(&mock.cli, body).expect("rewrite shebang");
            }
            "package-name" => fs::write(
                &metadata,
                r#"{"name":"@oh-my-pi/pi-coding-agent","version":"1.0.4","bin":{"pi":"dist/bundle/cli.js"}}"#,
            )
            .expect("foreign package"),
            "bin" => fs::write(
                &metadata,
                r#"{"name":"@earendil-works/pi-coding-agent","version":"1.0.4","bin":{"pi":"dist/cli.js"}}"#,
            )
            .expect("foreign entrypoint"),
            "unpackaged" => {
                let copy = temp.root.join("checkout/pi-coding-agent");
                fs::create_dir_all(copy.join("dist/bundle")).expect("checkout");
                fs::copy(&metadata, copy.join("package.json")).expect("checkout metadata");
                fs::copy(&mock.cli, copy.join("dist/bundle/cli.js")).expect("checkout entrypoint");
                mock.cli = copy.join("dist/bundle/cli.js");
            }
            "escaping-link" => {
                fs::write(temp.root.join("outside-secret"), "secret").expect("outside data");
                symlink(temp.root.join("outside-secret"), mock.package.join("dist/leak"))
                    .expect("escaping link");
            }
            "missing-node" => fs::remove_file(mock.bin.join("node")).expect("remove node"),
            "probe-mismatch" => mock_pi::configure(
                &mock,
                serde_json::json!({"scenario": "success", "candidate": "x\n", "probe_version": "1.0.5"}),
            ),
            _ => {}
        }
        let _environment = EnvRestore::controlled(&scratch, &mock.cli)
            .with_path(&mock.bin)
            .with_var("OPENAI_API_KEY", Some("openai-secret-api-key"));
        let Some(result) = run_mock_pi(
            &mock,
            Some(PI_MODEL),
            &workspace,
            &scratch,
            &target,
            PI_PROMPT.as_bytes(),
            10,
        ) else {
            return;
        };
        let error = result.expect_err(case);
        assert!(error.contains(expected), "{case}: {error}");
        assert!(
            !scratch.join("pi-capture.json").exists(),
            "{case}: mock Pi generation must not run"
        );
        if before_probe {
            assert!(
                !target.exists(),
                "{case} must fail before the Pi version probe"
            );
        }
    }
}

#[test]
fn pi_preconditions_fail_before_any_external_command() {
    let _lock = _hold_env_lock();
    let oversized = vec![b'x'; pi_max_prompt_bytes() + 1];
    for (case, prompt, expected) in [
        ("oversized", oversized.as_slice(), "at most 131071 bytes"),
        ("nul", b"prompt\0tail".as_slice(), "NUL byte"),
        (
            "file-argument",
            b"@prompt.md".as_slice(),
            "must not start with `@` or `/`",
        ),
        (
            "command",
            b"/skill:x".as_slice(),
            "must not start with `@` or `/`",
        ),
        ("empty", b"".as_slice(), "must be nonempty"),
        ("not-utf8", b"prompt \xff".as_slice(), "not valid UTF-8"),
    ] {
        let (temp, workspace, scratch, target) = fixture();
        let mock = mock_pi::install(&temp.root, "1.0.4", "v22.19.0", pi_config("success", &[]));
        let _environment = EnvRestore::controlled(&scratch, &mock.cli)
            .with_path(&mock.bin)
            .with_var("OPENAI_API_KEY", Some("openai-secret-api-key"));
        let error = run_agent(
            AgentSelection {
                kind: AgentKind::Pi,
                model: Some(PI_MODEL),
            },
            mock.cli.clone(),
            &workspace,
            &scratch,
            &target,
            prompt.to_vec(),
            10,
        )
        .expect_err(case);
        assert!(error.contains(expected), "{case}: {error}");
        assert!(!target.exists(), "{case}");
        assert!(!scratch.join("pi-agent").exists(), "{case}: a probe ran");
    }
}

/// REAL installed Pi (not a mock) through cott's adapter with no provider
/// egress: both probes run offline without credentials, then generation runs
/// with a fake caller home (no configuration), a placeholder key and an
/// unreachable HTTPS proxy (Pi installs undici's `EnvHttpProxyAgent`), so the
/// provider request fails locally. Pi 1.0.4 still exits `0`; cott must reject
/// the failed run from its JSONL events.
#[test]
#[ignore = "requires an installed official Pi CLI and Node on PATH"]
fn real_pi_runs_offline_probes_and_rejects_exit_zero_provider_failure() {
    let Some(pi) = std::env::var_os("PATH").and_then(|path| {
        std::env::split_paths(&path)
            .map(|directory| directory.join("pi"))
            .find(|candidate| candidate.exists())
    }) else {
        return;
    };
    let (_temp, workspace, scratch, target) = fixture();
    let _lock = _hold_env_lock();
    let _environment = EnvRestore::controlled(&scratch, &pi)
        .with_var("HTTPS_PROXY", Some("http://127.0.0.1:9"))
        .with_var("HTTP_PROXY", Some("http://127.0.0.1:9"))
        .with_var("NO_PROXY", None)
        .with_var("SSL_CERT_FILE", None)
        .with_var("SSL_CERT_DIR", None)
        .with_var("OPENAI_API_KEY", Some("cott-test-placeholder-not-a-key"));
    let Some(result) = run_or_skip_with_model(
        AgentKind::Pi,
        Some("openai/gpt-4.1-mini"),
        pi,
        &workspace,
        &scratch,
        &target,
        b"  Write implementation.py containing `print(\"ok\")`.\n",
        180,
    ) else {
        return;
    };
    let error = result.expect_err("an unreachable provider is not success");
    // Pi's default automatic retry ends with `auto_retry_end.success: false`;
    // without retries the final assistant message carries `stopReason: "error"`.
    assert!(
        error.starts_with("pi JSON event stream rejected: ")
            && (error.contains("reports a failed automatic retry")
                || error.contains("stopped with `error`")),
        "{error}"
    );
    assert!(!error.contains("cott-test-placeholder-not-a-key"));
}
