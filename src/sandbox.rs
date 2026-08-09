use std::collections::{BTreeMap, BTreeSet};
use std::io::{self, Read, Write};
use std::os::unix::process::CommandExt;
use std::path::{Path, PathBuf};
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
    pub writable_bytes: u64,
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
            writable_bytes: 16 * 1024 * 1024,
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
    WritableLimitExceeded {
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
            Self::WritableLimitExceeded { limit_bytes } => {
                write!(f, "sandbox writable data exceeded {limit_bytes} byte limit")
            }
        }
    }
}
impl std::error::Error for SandboxError {}

pub fn run(spec: &SandboxSpec) -> Result<CompletedProcess, SandboxError> {
    let bwrap = PathBuf::from("/usr/bin/bwrap");
    require_bwrap(&bwrap)?;
    let mut command = Command::new(bwrap);
    command.args([
        "--unshare-user",
        "--unshare-pid",
        "--unshare-ipc",
        "--unshare-uts",
        "--die-with-parent",
        "--new-session",
        "--tmpfs",
        "/",
        "--dir",
        "/tmp",
        "--dir",
        "/usr",
        "--ro-bind",
        "/usr",
        "/usr",
        "--dir",
        "/proc",
        "--proc",
        "/proc",
        "--dir",
        "/dev",
        "--dev",
        "/dev",
    ]);
    for system_path in ["/bin", "/lib", "/lib64", "/etc"] {
        if PathBuf::from(system_path).exists() {
            command.args(["--dir", system_path, "--ro-bind", system_path, system_path]);
        }
    }
    if spec.network == NetworkAccess::Disabled {
        command.arg("--unshare-net");
    }
    let mut directories = BTreeSet::new();
    for path in spec
        .binds
        .read_only
        .iter()
        .chain(&spec.binds.writable)
        .chain(std::iter::once(&spec.cwd))
    {
        let mut parent = path.parent();
        while let Some(path) = parent {
            if path != Path::new("/") {
                directories.insert(path.to_path_buf());
            }
            parent = path.parent();
        }
    }
    let mut directories = directories.into_iter().collect::<Vec<_>>();
    directories.sort_by_key(|path| path.components().count());
    for path in directories {
        command.args(["--dir", path.to_string_lossy().as_ref()]);
    }
    let mut mounts = spec
        .binds
        .writable
        .iter()
        .map(|path| (path, true))
        .chain(spec.binds.read_only.iter().map(|path| (path, false)))
        .collect::<Vec<_>>();
    mounts.sort_by(|(left, _), (right, _)| {
        left.components()
            .count()
            .cmp(&right.components().count())
            .then_with(|| left.cmp(right))
    });
    for (path, writable) in mounts {
        let option = if writable { "--bind" } else { "--ro-bind" };
        command.args([
            option,
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
    let process_limit = current_user_tasks()
        .map_err(SandboxError::Io)?
        .saturating_add(spec.limits.process_count)
        .saturating_add(4);
    let limits = spec.limits.clone();
    unsafe {
        command.pre_exec(move || {
            let set = |resource, value| {
                let limit = libc::rlimit {
                    rlim_cur: value as libc::rlim_t,
                    rlim_max: value as libc::rlim_t,
                };
                if libc::setrlimit(resource, &limit) != 0 {
                    Err(io::Error::last_os_error())
                } else {
                    Ok(())
                }
            };
            set(libc::RLIMIT_CPU, limits.cpu_time.as_secs().max(1))?;
            set(libc::RLIMIT_AS, limits.address_space_bytes)?;
            set(libc::RLIMIT_NPROC, process_limit)?;
            set(libc::RLIMIT_NOFILE, limits.open_files)?;
            set(libc::RLIMIT_FSIZE, limits.file_size_bytes)?;
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
    if writable_usage(&spec.binds.writable).map_err(SandboxError::Io)? > spec.limits.writable_bytes
    {
        return Err(SandboxError::WritableLimitExceeded {
            limit_bytes: spec.limits.writable_bytes,
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

fn require_bwrap(path: &Path) -> Result<(), SandboxError> {
    let canonical = std::fs::canonicalize(path).map_err(|_| {
        SandboxError::Unavailable("bubblewrap /usr/bin/bwrap is required".to_owned())
    })?;
    if canonical != path || !path.is_file() {
        return Err(SandboxError::Unavailable(
            "canonical bubblewrap /usr/bin/bwrap is required".to_owned(),
        ));
    }
    let output = Command::new(path)
        .arg("--version")
        .env_clear()
        .output()
        .map_err(SandboxError::Io)?;
    let version = String::from_utf8_lossy(&output.stdout);
    let Some(version) = version.trim().strip_prefix("bubblewrap ") else {
        return Err(SandboxError::Unavailable(
            "unsupported bubblewrap version output".to_owned(),
        ));
    };
    let mut parts = version.split('.');
    let major = parts.next().and_then(|part| part.parse::<u64>().ok());
    let minor = parts.next().and_then(|part| part.parse::<u64>().ok());
    if !output.status.success() || major != Some(0) || minor.is_none_or(|minor| minor < 9) {
        return Err(SandboxError::Unavailable(format!(
            "bubblewrap {version} is unsupported; require >=0.9.0,<1.0.0"
        )));
    }
    Ok(())
}

fn current_user_tasks() -> io::Result<u64> {
    let uid = unsafe { libc::geteuid() };
    let mut tasks = 0_u64;
    for entry in std::fs::read_dir("/proc")? {
        let Ok(entry) = entry else { continue };
        let name = entry.file_name();
        if !name.as_encoded_bytes().iter().all(u8::is_ascii_digit) {
            continue;
        }
        let Ok(status) = std::fs::read_to_string(entry.path().join("status")) else {
            continue;
        };
        let owned = status.lines().find_map(|line| {
            line.strip_prefix("Uid:")
                .and_then(|uids| uids.split_whitespace().next())
                .and_then(|uid| uid.parse::<u32>().ok())
        }) == Some(uid);
        if owned {
            tasks = tasks.saturating_add(
                std::fs::read_dir(entry.path().join("task"))
                    .map(|entries| entries.count() as u64)
                    .unwrap_or(0),
            );
        }
    }
    Ok(tasks)
}

fn writable_usage(paths: &[PathBuf]) -> io::Result<u64> {
    let mut roots = paths
        .iter()
        .map(std::fs::canonicalize)
        .collect::<io::Result<Vec<_>>>()?;
    roots.sort();
    roots.dedup();
    let mut pending = Vec::new();
    for path in roots {
        if !pending.iter().any(|root: &PathBuf| path.starts_with(root)) {
            pending.push(path);
        }
    }
    let mut total = 0_u64;
    while let Some(path) = pending.pop() {
        let metadata = std::fs::symlink_metadata(&path)?;
        if metadata.file_type().is_symlink() {
            return Err(io::Error::other("sandbox writable tree contains a symlink"));
        }
        if metadata.is_file() {
            total = total.saturating_add(metadata.len());
        } else if metadata.is_dir() {
            for entry in std::fs::read_dir(path)? {
                pending.push(entry?.path());
            }
        }
    }
    Ok(total)
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
