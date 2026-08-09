use std::collections::BTreeMap;
use std::io::{self, Read, Write};
use std::os::unix::process::CommandExt;
use std::path::PathBuf;
use std::process::{Command, Stdio};
use std::thread;
use std::time::{Duration, Instant};

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum NetworkAccess {
    Disabled,
    Enabled,
}

#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub struct BindMounts {
    pub read_only: Vec<PathBuf>,
    pub writable: Vec<PathBuf>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ResourceLimits {
    pub cpu_time: Duration,
    pub address_space_bytes: u64,
    pub process_count: u64,
    pub open_files: u64,
    pub file_size_bytes: u64,
    pub wall_time: Duration,
    pub stream_limit_bytes: u64,
}

impl ResourceLimits {
    pub const fn contract_test() -> Self {
        Self {
            cpu_time: Duration::from_secs(30),
            address_space_bytes: 1024 * 1024 * 1024,
            process_count: 16,
            open_files: 128,
            file_size_bytes: 16 * 1024 * 1024,
            wall_time: Duration::from_secs(30),
            stream_limit_bytes: 1024 * 1024,
        }
    }
}

#[derive(Clone, Debug)]
pub struct SandboxSpec {
    pub program: PathBuf,
    pub arguments: Vec<String>,
    pub cwd: PathBuf,
    pub environment: BTreeMap<String, String>,
    pub stdin: Vec<u8>,
    pub binds: BindMounts,
    pub network: NetworkAccess,
    pub limits: ResourceLimits,
}

#[derive(Clone, Debug)]
pub struct CompletedProcess {
    pub status: Option<i32>,
    pub timed_out: bool,
    pub stdout: Vec<u8>,
    pub stderr: Vec<u8>,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum OutputStream {
    Stdout,
    Stderr,
}

#[derive(Debug)]
pub enum SandboxError {
    Unavailable(String),
    Io(io::Error),
    Timeout,
    StreamLimitExceeded {
        stream: OutputStream,
        limit_bytes: u64,
    },
}
impl std::fmt::Display for SandboxError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Unavailable(message) => f.write_str(message),
            Self::Io(error) => error.fmt(f),
            Self::Timeout => f.write_str("sandbox process timed out"),
            Self::StreamLimitExceeded {
                stream,
                limit_bytes,
            } => write!(
                f,
                "sandbox {stream:?} stream exceeded {limit_bytes} byte limit"
            ),
        }
    }
}
impl std::error::Error for SandboxError {}

pub fn run(spec: &SandboxSpec) -> Result<CompletedProcess, SandboxError> {
    let bwrap = PathBuf::from("/usr/bin/bwrap");
    if !bwrap.is_file() {
        return Err(SandboxError::Unavailable(
            "bubblewrap /usr/bin/bwrap is required".to_owned(),
        ));
    }
    let prlimit = PathBuf::from("/usr/bin/prlimit");
    if !prlimit.is_file() {
        return Err(SandboxError::Unavailable(
            "prlimit /usr/bin/prlimit is required for sandbox resource limits".to_owned(),
        ));
    }
    let mut command = Command::new(bwrap);
    command.args([
        "--unshare-user",
        "--unshare-pid",
        "--unshare-ipc",
        "--unshare-uts",
        "--die-with-parent",
        "--new-session",
        "--ro-bind",
        "/",
        "/",
        "--proc",
        "/proc",
        "--dev",
        "/dev",
        "--tmpfs",
        "/tmp",
    ]);
    if spec.network == NetworkAccess::Disabled {
        command.arg("--unshare-net");
    }
    for path in &spec.binds.read_only {
        command.args([
            "--ro-bind",
            path.to_string_lossy().as_ref(),
            path.to_string_lossy().as_ref(),
        ]);
    }
    for path in &spec.binds.writable {
        command.args([
            "--bind",
            path.to_string_lossy().as_ref(),
            path.to_string_lossy().as_ref(),
        ]);
    }
    command.args(["--chdir", spec.cwd.to_string_lossy().as_ref(), "--"]);
    command
        .arg(&prlimit)
        .arg(format!(
            "--cpu={}:{}",
            spec.limits.cpu_time.as_secs().max(1),
            spec.limits.cpu_time.as_secs().max(1)
        ))
        .arg(format!(
            "--as={}:{}",
            spec.limits.address_space_bytes, spec.limits.address_space_bytes
        ))
        .arg(format!(
            "--nproc={}:{}",
            spec.limits.process_count, spec.limits.process_count
        ))
        .arg(format!(
            "--nofile={}:{}",
            spec.limits.open_files, spec.limits.open_files
        ))
        .arg(format!(
            "--fsize={}:{}",
            spec.limits.file_size_bytes, spec.limits.file_size_bytes
        ))
        .arg("--")
        .arg(&spec.program)
        .args(&spec.arguments)
        .current_dir(&spec.cwd)
        .env_clear()
        .envs(&spec.environment)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    unsafe {
        command.pre_exec(|| {
            if libc::setpgid(0, 0) != 0 {
                return Err(io::Error::last_os_error());
            }
            Ok(())
        });
    }
    let mut child = command.spawn().map_err(SandboxError::Io)?;
    child
        .stdin
        .take()
        .expect("piped stdin")
        .write_all(&spec.stdin)
        .map_err(SandboxError::Io)?;
    let stdout = child.stdout.take().expect("piped stdout");
    let stderr = child.stderr.take().expect("piped stderr");
    let stdout_limit = spec.limits.stream_limit_bytes;
    let stderr_limit = spec.limits.stream_limit_bytes;
    let stdout = thread::spawn(move || drain(stdout, stdout_limit));
    let stderr = thread::spawn(move || drain(stderr, stderr_limit));
    let started = Instant::now();
    let mut timed_out = false;
    let status = loop {
        if let Some(status) = child.try_wait().map_err(SandboxError::Io)? {
            break status.code();
        }
        if started.elapsed() >= spec.limits.wall_time {
            timed_out = true;
            child.kill().map_err(SandboxError::Io)?;
            child.wait().map_err(SandboxError::Io)?;
            break None;
        }
        thread::sleep(Duration::from_millis(10));
    };
    let stdout = stdout
        .join()
        .map_err(|_| SandboxError::Io(io::Error::other("stdout reader thread panicked")))?
        .map_err(SandboxError::Io)?;
    let stderr = stderr
        .join()
        .map_err(|_| SandboxError::Io(io::Error::other("stderr reader thread panicked")))?
        .map_err(SandboxError::Io)?;
    if stdout.1 {
        return Err(SandboxError::StreamLimitExceeded {
            stream: OutputStream::Stdout,
            limit_bytes: spec.limits.stream_limit_bytes,
        });
    }
    if stderr.1 {
        return Err(SandboxError::StreamLimitExceeded {
            stream: OutputStream::Stderr,
            limit_bytes: spec.limits.stream_limit_bytes,
        });
    }
    if is_bwrap_bootstrap_failure(status, &stderr.0) {
        return Err(SandboxError::Unavailable(
            String::from_utf8_lossy(&stderr.0).trim().to_owned(),
        ));
    }
    Ok(CompletedProcess {
        status,
        timed_out,
        stdout: stdout.0,
        stderr: stderr.0,
    })
}

fn is_bwrap_bootstrap_failure(status: Option<i32>, stderr: &[u8]) -> bool {
    let message = String::from_utf8_lossy(stderr);
    let mut lines = message.lines();
    let first = lines.next().unwrap_or_default().trim();
    status == Some(1)
        && lines.all(|line| line.trim().is_empty())
        && (first.starts_with("bwrap: Creating new namespace failed:")
            || first.starts_with("bwrap: setting up uid map:")
            || first.starts_with("bwrap: setting up gid map:"))
}

fn drain<R: Read>(reader: R, limit: u64) -> io::Result<(Vec<u8>, bool)> {
    let mut bytes = Vec::new();
    reader
        .take(limit.saturating_add(1))
        .read_to_end(&mut bytes)?;
    let exceeded = bytes.len() as u64 > limit;
    Ok((bytes, exceeded))
}
