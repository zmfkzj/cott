use std::collections::BTreeMap;
use std::io::{self, Read, Write};
use std::os::unix::process::CommandExt;
use std::path::PathBuf;
use std::process::{Command, Stdio};
use std::thread;
use std::time::{Duration, Instant};

#[derive(Clone, Debug)]
pub struct SandboxSpec {
    pub program: PathBuf,
    pub arguments: Vec<String>,
    pub cwd: PathBuf,
    pub environment: BTreeMap<String, String>,
    pub stdin: Vec<u8>,
    pub writable: Vec<PathBuf>,
    pub network: bool,
    pub timeout: Duration,
    pub address_space_bytes: u64,
    pub process_limit: u64,
}

#[derive(Clone, Debug)]
pub struct CompletedProcess {
    pub status: Option<i32>,
    pub timed_out: bool,
    pub stdout: Vec<u8>,
    pub stderr: Vec<u8>,
}

#[derive(Debug)]
pub enum SandboxError {
    Unavailable(String),
    Io(io::Error),
    Timeout,
}
impl std::fmt::Display for SandboxError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Unavailable(message) => f.write_str(message),
            Self::Io(error) => error.fmt(f),
            Self::Timeout => f.write_str("sandbox process timed out"),
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
    if !spec.network {
        command.arg("--unshare-net");
    }
    for path in &spec.writable {
        command.args([
            "--bind",
            path.to_string_lossy().as_ref(),
            path.to_string_lossy().as_ref(),
        ]);
    }
    command.args(["--chdir", spec.cwd.to_string_lossy().as_ref(), "--"]);
    command
        .arg(&spec.program)
        .args(&spec.arguments)
        .current_dir(&spec.cwd)
        .env_clear()
        .envs(&spec.environment)
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    let address_space_bytes = spec.address_space_bytes;
    let _process_limit = spec.process_limit;
    unsafe {
        command.pre_exec(move || {
            if libc::setpgid(0, 0) != 0 {
                return Err(io::Error::last_os_error());
            }
            let memory = libc::rlimit {
                rlim_cur: address_space_bytes,
                rlim_max: address_space_bytes,
            };
            if libc::setrlimit(libc::RLIMIT_AS, &memory) != 0 {
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
    let stdout = thread::spawn(move || {
        let mut bytes = Vec::new();
        let _ = stdout.take(16 * 1024 * 1024 + 1).read_to_end(&mut bytes);
        bytes
    });
    let stderr = thread::spawn(move || {
        let mut bytes = Vec::new();
        let _ = stderr.take(16 * 1024 * 1024 + 1).read_to_end(&mut bytes);
        bytes
    });
    let started = Instant::now();
    let mut timed_out = false;
    let status = loop {
        if let Some(status) = child.try_wait().map_err(SandboxError::Io)? {
            break status.code();
        }
        if started.elapsed() >= spec.timeout {
            timed_out = true;
            child.kill().map_err(SandboxError::Io)?;
            child.wait().map_err(SandboxError::Io)?;
            break None;
        }
        thread::sleep(Duration::from_millis(10));
    };
    let stdout = stdout.join().expect("stdout reader thread");
    let stderr = stderr.join().expect("stderr reader thread");
    if stdout.len() > 16 * 1024 * 1024 || stderr.len() > 16 * 1024 * 1024 {
        return Err(SandboxError::Unavailable(
            "sandbox stream limit exceeded".to_owned(),
        ));
    }
    Ok(CompletedProcess {
        status,
        timed_out,
        stdout,
        stderr,
    })
}
