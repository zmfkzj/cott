//! `cott generate --project <dir>` run from a different working directory
//! that carries its own (decoy) agent context and configuration. The MOCK
//! OMP executable (a shell script, never a provider run) checks, inside the
//! sandbox, that the agent works at the selected project's real path with the
//! selected project's context and the caller's own OMP configuration, that
//! nothing of the invocation directory is visible, and that the project's
//! context is read-only; then it writes the target-specific candidate.
#![allow(dead_code)]

use std::fs;
use std::os::unix::fs::PermissionsExt;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};

/// Marker every failed check prints to stderr.
pub const FAILED: &str = "project-cwd check failed";

pub struct ProjectCwd {
    /// The invocation directory: not the project, with decoy setup.
    pub decoy: PathBuf,
    /// The caller's home (outside the project) with the user OMP config.
    pub home: PathBuf,
    /// PATH directory holding the mock `omp`.
    pub tools: PathBuf,
    pub project: PathBuf,
}

/// Prepare `project` (selected project context), a decoy invocation
/// directory and a home under `outside` (a directory that is neither the
/// project nor inside it), and a mock OMP that writes `candidate` to the
/// workspace-relative `target_file` after its checks pass.
pub fn install(outside: &Path, project: &Path, target_file: &str, candidate: &str) -> ProjectCwd {
    let project = fs::canonicalize(project).expect("canonical project");
    fs::write(project.join("AGENTS.md"), "selected project rules").expect("project context");
    fs::create_dir_all(project.join(".omp")).expect("project OMP directory");
    fs::write(
        project.join(".omp/settings.json"),
        r#"{"project":"selected"}"#,
    )
    .expect("project OMP settings");
    let decoy = outside.join("invocation-directory");
    fs::create_dir_all(&decoy).expect("decoy directory");
    let decoy = fs::canonicalize(decoy).expect("canonical decoy");
    fs::write(decoy.join("AGENTS.md"), "decoy rules").expect("decoy context");
    fs::write(decoy.join("CLAUDE.md"), "decoy memory").expect("decoy memory");
    fs::write(decoy.join("cott.toml"), "this is not a Cott manifest").expect("decoy manifest");
    for directory in [".omp", ".pi", ".codex", ".claude"] {
        fs::create_dir_all(decoy.join(directory)).expect("decoy agent directory");
        fs::write(decoy.join(directory).join("settings.json"), "{}").expect("decoy settings");
    }
    let home = outside.join("caller-home");
    fs::create_dir_all(home.join(".omp/agent")).expect("caller OMP directory");
    fs::write(home.join(".omp/agent/config.yml"), "model: user-default").expect("user OMP config");
    let tools = outside.join("caller-tools");
    fs::create_dir_all(&tools).expect("tool directory");
    let script = r#"#!/bin/sh
if [ "$1" = "--version" ]; then echo omp/17.2.12; exit 0; fi
fail() { printf '%s: %s\n' '@FAILED@' "$1" >&2; exit 64; }
for arg do [ "${previous-}" = --cwd ] && cwd=$arg; previous=$arg; done
[ "${cwd-}" = '@PROJECT@' ] || fail "--cwd ${cwd-}"
[ "$(pwd)" = '@PROJECT@' ] && [ "$PWD" = '@PROJECT@' ] || fail "working directory $(pwd)"
[ "$(cat AGENTS.md)" = 'selected project rules' ] || fail 'selected project AGENTS.md'
[ "$(cat .omp/settings.json)" = '{"project":"selected"}' ] || fail 'selected project .omp'
[ "$(cat "$HOME/.omp/agent/config.yml")" = 'model: user-default' ] || fail 'caller OMP configuration'
for decoy in '@DECOY@' '@DECOY@/AGENTS.md' '@DECOY@/CLAUDE.md' '@DECOY@/.omp' '@DECOY@/.pi' '@DECOY@/.codex' '@DECOY@/.claude' '@DECOY@/cott.toml'; do
  [ ! -e "$decoy" ] || fail "invocation directory entry $decoy visible"
done
if (printf x >> AGENTS.md) 2>/dev/null; then fail 'selected project AGENTS.md writable'; fi
cat > '@TARGET@' <<'COTT_CANDIDATE'
@CANDIDATE@
COTT_CANDIDATE
"#
    .replace("@FAILED@", FAILED)
    .replace("@PROJECT@", &project.display().to_string())
    .replace("@DECOY@", &decoy.display().to_string())
    .replace("@TARGET@", target_file)
    .replace("@CANDIDATE@", candidate.trim_end_matches('\n'));
    let omp = tools.join("omp");
    fs::write(&omp, script).expect("mock OMP");
    fs::set_permissions(&omp, fs::Permissions::from_mode(0o755)).expect("mock OMP permissions");
    ProjectCwd {
        decoy,
        home,
        tools,
        project,
    }
}

impl ProjectCwd {
    /// `cott <arguments> --project <project>` from the decoy directory with
    /// the caller's home and PATH.
    pub fn run(&self, arguments: &[&str]) -> Output {
        let path = std::env::join_paths([
            self.tools.as_path(),
            Path::new("/usr/bin"),
            Path::new("/bin"),
        ])
        .expect("PATH");
        Command::new(env!("CARGO_BIN_EXE_cott"))
            .current_dir(&self.decoy)
            .args(arguments)
            .arg("--project")
            .arg(&self.project)
            .env("PATH", path)
            .env("HOME", &self.home)
            .env("PWD", &self.decoy)
            .env_remove("PI_CODING_AGENT_DIR")
            .env_remove("CODEX_HOME")
            .env_remove("CLAUDE_CONFIG_DIR")
            .output()
            .expect("run cott from the decoy directory")
    }

    /// The decoy and the project's context are unchanged after the run.
    pub fn assert_untouched(&self) {
        assert_eq!(
            fs::read_to_string(self.project.join("AGENTS.md")).expect("project context"),
            "selected project rules"
        );
        assert_eq!(
            fs::read_to_string(self.decoy.join("AGENTS.md")).expect("decoy context"),
            "decoy rules"
        );
        assert_eq!(
            fs::read_to_string(self.decoy.join("cott.toml")).expect("decoy manifest"),
            "this is not a Cott manifest"
        );
        assert!(!self.decoy.join("generated").exists());
    }
}
