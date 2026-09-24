pub mod landlock;

use std::collections::{BTreeMap, BTreeSet};
use std::ffi::OsString;
use std::io::{self, Read, Seek, Write};
use std::os::fd::{AsRawFd, FromRawFd};
use std::os::unix::process::CommandExt;
use std::path::{Path, PathBuf};
use std::process::{Command, Stdio};
use std::sync::mpsc;
use std::thread;
use std::time::{Duration, Instant};

use crate::version::is_at_least;
#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum NetworkAccess {
    Disabled,
    IsolatedLoopback,
    Enabled,
}

impl NetworkAccess {
    pub const fn bwrap_arguments(self) -> &'static [&'static str] {
        match self {
            Self::Disabled => &["--unshare-net"],
            // UID 0 is mapped only inside the new user namespace to the invoking
            // host user. Otherwise exec drops CAP_NET_ADMIN before `ip` can raise lo.
            Self::IsolatedLoopback => &[
                "--uid",
                "0",
                "--gid",
                "0",
                "--unshare-net",
                "--cap-add",
                "CAP_NET_ADMIN",
                "--cap-add",
                "CAP_SETPCAP",
            ],
            Self::Enabled => &[],
        }
    }
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

impl CompletedProcess {
    pub const fn outcome(&self) -> SandboxOutcome {
        SandboxOutcome::Exited
    }
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum SandboxOutcome {
    Exited,
    TimedOut,
    StreamLimitExceeded {
        stream: OutputStream,
        limit_bytes: u64,
    },
    WritableLimitExceeded {
        limit_bytes: u64,
    },
    UnsupportedLoopback,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
pub enum OutputStream {
    Stdout,
    Stderr,
}

#[derive(Debug)]
pub enum SandboxError {
    Unavailable(String),
    UnsupportedLoopback,
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

impl SandboxError {
    pub const fn outcome(&self) -> Option<SandboxOutcome> {
        match self {
            Self::UnsupportedLoopback => Some(SandboxOutcome::UnsupportedLoopback),
            Self::Timeout => Some(SandboxOutcome::TimedOut),
            Self::StreamLimitExceeded {
                stream,
                limit_bytes,
            } => Some(SandboxOutcome::StreamLimitExceeded {
                stream: *stream,
                limit_bytes: *limit_bytes,
            }),
            Self::WritableLimitExceeded { limit_bytes } => {
                Some(SandboxOutcome::WritableLimitExceeded {
                    limit_bytes: *limit_bytes,
                })
            }
            Self::Unavailable(_) | Self::Io(_) => None,
        }
    }
}
impl std::fmt::Display for SandboxError {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Unavailable(message) => f.write_str(message),
            Self::UnsupportedLoopback => f.write_str("isolated loopback is unavailable"),
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

const LOOPBACK_SETUP_FAILURE: &str = "cott-sandbox: isolated loopback unavailable";
const SCOPE_GATE: &str = "IFS= read -r cott_scope_gate || exit 126; \
    [ \"$cott_scope_gate\" = cott-scope-ready ] || exit 126; printf 1; exec \"$@\"";
const SCOPE_GATE_TOKEN: &[u8] = b"cott-scope-ready\n";
const SCOPE_ACK_TOKEN: u8 = b'1';
const SCOPE_CLEANUP_TIMEOUT: Duration = Duration::from_secs(1);

pub fn run(spec: &SandboxSpec) -> Result<CompletedProcess, SandboxError> {
    let bwrap = PathBuf::from("/usr/bin/bwrap");
    require_bwrap(&bwrap)?;
    let systemd_run = PathBuf::from("/usr/bin/systemd-run");
    let systemctl = PathBuf::from("/usr/bin/systemctl");
    require_canonical_tool(&systemd_run, "systemd-run")?;
    require_canonical_tool(&systemctl, "systemctl")?;
    if !Path::new("/bin/sh").is_file() {
        return Err(SandboxError::Unavailable(
            "system shell /bin/sh is required for sandbox scope startup".to_owned(),
        ));
    }
    if spec.network == NetworkAccess::IsolatedLoopback {
        require_loopback_setup()?;
    }
    let tasks_max = spec
        .limits
        .process_count
        .checked_add(4)
        .ok_or_else(|| SandboxError::Unavailable("sandbox task limit overflows".to_owned()))?;
    let unit = scope_unit_name()?;
    let launcher_cgroup = process_cgroup(std::process::id()).map_err(|error| {
        SandboxError::Unavailable(format!(
            "inspect sandbox launcher cgroup v2 membership: {error}"
        ))
    })?;
    let manager_environment = user_manager_environment();
    let mut command = Command::new(&systemd_run);
    command
        .args([
            "--user",
            "--scope",
            "--quiet",
            "--collect",
            "--no-ask-password",
            "--expand-environment=no",
        ])
        .arg(format!("--unit={unit}"))
        .arg(format!("--property=TasksMax={tasks_max}"))
        .arg("--property=KillMode=control-group")
        .arg("--")
        .arg("/bin/sh")
        .args(["-c", SCOPE_GATE, "cott-scope-gate"])
        .arg(&bwrap);
    command.args([
        "--unshare-user",
        "--unshare-pid",
        "--unshare-ipc",
        "--unshare-uts",
        "--die-with-parent",
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
    command.arg("--clearenv");
    command.args(spec.network.bwrap_arguments());
    for system_path in ["/bin", "/lib", "/lib64", "/etc"] {
        if PathBuf::from(system_path).exists() {
            command.args(["--dir", system_path, "--ro-bind", system_path, system_path]);
        }
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
    let environment_args = sealed_environment_args(&spec.environment)?;
    let environment_fd = environment_args.as_raw_fd();
    command.args(["--args", &environment_fd.to_string()]);
    command.args(["--chdir", spec.cwd.to_string_lossy().as_ref(), "--"]);
    if spec.network == NetworkAccess::IsolatedLoopback {
        command.args([
            "/bin/sh",
            "-c",
            "if ! /usr/sbin/ip link set lo up; then printf '%s\\n' 'cott-sandbox: isolated loopback unavailable' >&2; exit 125; fi; exec /usr/bin/setpriv --bounding-set=-all --inh-caps=-all --ambient-caps=-all --no-new-privs -- \"$@\"",
            "cott-loopback",
        ]);
    }
    command
        .arg(&spec.program)
        .args(&spec.arguments)
        .current_dir(&spec.cwd)
        .env_clear()
        .envs(
            manager_environment
                .iter()
                .map(|(name, value)| (name, value)),
        )
        .stdin(Stdio::piped())
        .stdout(Stdio::piped())
        .stderr(Stdio::piped());
    let limits = spec.limits.clone();
    unsafe {
        command.pre_exec(move || {
            let flags = libc::fcntl(environment_fd, libc::F_GETFD);
            if flags == -1
                || libc::fcntl(environment_fd, libc::F_SETFD, flags & !libc::FD_CLOEXEC) == -1
            {
                return Err(io::Error::last_os_error());
            }
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
            set(libc::RLIMIT_NOFILE, limits.open_files)?;
            set(libc::RLIMIT_FSIZE, limits.file_size_bytes)?;
            if libc::setsid() == -1 {
                return Err(io::Error::last_os_error());
            }
            Ok(())
        });
    }
    let mut child = command.spawn().map_err(|error| {
        SandboxError::Unavailable(format!("launch sandbox transient scope: {error}"))
    })?;
    drop(environment_args);
    let started = Instant::now();
    let mut scope = TransientScope::new(unit, systemctl, manager_environment);
    let mut stdin = child.stdin.take().expect("piped stdin");
    let (stream_tx, stream_rx) = mpsc::channel();
    let (scope_ack_tx, scope_ack_rx) = mpsc::channel();
    let stdout = child.stdout.take().expect("piped stdout");
    let stdout_limit = spec.limits.stream_limit_bytes;
    let stdout_tx = stream_tx.clone();
    let stdout = thread::spawn(move || {
        let mut stdout = stdout;
        let mut token = [0_u8; 1];
        let acknowledgement = match stdout.read_exact(&mut token) {
            Ok(()) if token[0] == SCOPE_ACK_TOKEN => Ok(()),
            Ok(()) => Err("sandbox scope startup gate sent an invalid acknowledgement".to_owned()),
            Err(error) => Err(format!(
                "sandbox scope startup gate closed without acknowledgement: {error}"
            )),
        };
        let _ = scope_ack_tx.send(acknowledgement);
        let result = drain(stdout, stdout_limit);
        let _ = stdout_tx.send((OutputStream::Stdout, matches!(&result, Ok((_, true)))));
        result
    });
    let stderr = child.stderr.take().expect("piped stderr");
    let stderr_limit = spec.limits.stream_limit_bytes;
    let stderr = thread::spawn(move || {
        let result = drain(stderr, stderr_limit);
        let _ = stream_tx.send((OutputStream::Stderr, matches!(&result, Ok((_, true)))));
        result
    });
    let scope_setup = scope
        .wait_until_ready(
            &mut child,
            tasks_max,
            &started,
            spec.limits.wall_time,
            &launcher_cgroup,
        )
        .and_then(|()| {
            if started.elapsed() >= spec.limits.wall_time {
                return Err(ScopeSetupFailure::TimedOut);
            }
            stdin.write_all(SCOPE_GATE_TOKEN).map_err(|error| {
                ScopeSetupFailure::Unavailable(format!(
                    "release sandbox scope startup gate: {error}"
                ))
            })?;
            wait_for_scope_ack(&scope_ack_rx, &started, spec.limits.wall_time)
        });
    if let Err(failure) = scope_setup {
        drop(stdin);
        let mut cleanup_error = terminate_process_session(&mut child).err();
        if let Err(error) = scope.kill_all() {
            cleanup_error.get_or_insert(error);
        }
        stdout
            .join()
            .map_err(|_| SandboxError::Io(io::Error::other("stdout reader thread panicked")))?
            .map_err(SandboxError::Io)?;
        let stderr = stderr
            .join()
            .map_err(|_| SandboxError::Io(io::Error::other("stderr reader thread panicked")))?
            .map_err(SandboxError::Io)?;
        if let Some(error) = cleanup_error {
            return Err(SandboxError::Io(error));
        }
        return match failure {
            ScopeSetupFailure::TimedOut => Err(SandboxError::Timeout),
            ScopeSetupFailure::Unavailable(reason) => {
                let detail = String::from_utf8_lossy(&stderr.0);
                let detail = detail.trim();
                let message = if detail.is_empty() {
                    reason
                } else {
                    format!("{reason}: {detail}")
                };
                Err(SandboxError::Unavailable(message))
            }
        };
    }
    let input = spec.stdin.clone();
    let stdin = thread::spawn(move || stdin.write_all(&input));
    let mut termination = None;
    let mut child_error = None;
    let status = 'wait: loop {
        while let Ok((stream, exceeded)) = stream_rx.try_recv() {
            if exceeded {
                termination = Some(SandboxOutcome::StreamLimitExceeded {
                    stream,
                    limit_bytes: spec.limits.stream_limit_bytes,
                });
                if let Err(error) = terminate_process_session(&mut child) {
                    child_error = Some(error);
                }
                break 'wait None;
            }
        }
        match child.try_wait() {
            Ok(Some(status)) => {
                if let Err(error) = kill_process_session(child.id()) {
                    child_error = Some(error);
                }
                break status.code();
            }
            Ok(None) => {}
            Err(error) => {
                child_error = Some(error);
                if let Err(error) = terminate_process_session(&mut child) {
                    child_error.get_or_insert(error);
                }
                break None;
            }
        }
        if started.elapsed() >= spec.limits.wall_time {
            termination = Some(SandboxOutcome::TimedOut);
            if let Err(error) = terminate_process_session(&mut child) {
                child_error = Some(error);
            }
            break None;
        }
        thread::sleep(Duration::from_millis(10));
    };
    if let Err(error) = scope.kill_all() {
        child_error.get_or_insert(error);
    }
    let stdin = stdin
        .join()
        .map_err(|_| SandboxError::Io(io::Error::other("stdin writer thread panicked")))?;
    let stdout = stdout
        .join()
        .map_err(|_| SandboxError::Io(io::Error::other("stdout reader thread panicked")))?;
    let stderr = stderr
        .join()
        .map_err(|_| SandboxError::Io(io::Error::other("stderr reader thread panicked")))?;
    let stdout = stdout.map_err(SandboxError::Io)?;
    let stderr = stderr.map_err(SandboxError::Io)?;
    if let Some(error) = child_error {
        return Err(SandboxError::Io(error));
    }
    if let Some(outcome) = termination {
        return Err(match outcome {
            SandboxOutcome::TimedOut => SandboxError::Timeout,
            SandboxOutcome::StreamLimitExceeded {
                stream,
                limit_bytes,
            } => SandboxError::StreamLimitExceeded {
                stream,
                limit_bytes,
            },
            _ => unreachable!("only terminating outcomes are recorded"),
        });
    }
    if is_loopback_setup_failure(status, &stderr.0) {
        return Err(SandboxError::UnsupportedLoopback);
    }
    if is_bwrap_bootstrap_failure(status, &stderr.0) {
        return Err(SandboxError::Unavailable(
            String::from_utf8_lossy(&stderr.0).trim().to_owned(),
        ));
    }
    stdin.map_err(SandboxError::Io)?;
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
    Ok(CompletedProcess {
        status,
        timed_out: false,
        stdout: stdout.0,
        stderr: stderr.0,
    })
}

fn sealed_environment_args(
    environment: &BTreeMap<String, String>,
) -> Result<std::fs::File, SandboxError> {
    let mut arguments = Vec::new();
    for (name, value) in environment {
        if name.is_empty() || name.contains(['=', '\0']) || value.contains('\0') {
            return Err(SandboxError::Io(io::Error::new(
                io::ErrorKind::InvalidInput,
                "invalid sandbox environment entry",
            )));
        }
        arguments.extend_from_slice(b"--setenv\0");
        arguments.extend_from_slice(name.as_bytes());
        arguments.push(0);
        arguments.extend_from_slice(value.as_bytes());
        arguments.push(0);
    }
    // Keep credentials off systemd-run, shell, and bubblewrap command lines.
    let descriptor = unsafe {
        libc::memfd_create(
            c"cott-sandbox-env".as_ptr(),
            libc::MFD_CLOEXEC | libc::MFD_ALLOW_SEALING,
        )
    };
    if descriptor == -1 {
        return Err(SandboxError::Io(io::Error::last_os_error()));
    }
    let mut file = unsafe { std::fs::File::from_raw_fd(descriptor) };
    file.write_all(&arguments).map_err(SandboxError::Io)?;
    file.rewind().map_err(SandboxError::Io)?;
    let seals = libc::F_SEAL_WRITE | libc::F_SEAL_GROW | libc::F_SEAL_SHRINK | libc::F_SEAL_SEAL;
    if unsafe { libc::fcntl(descriptor, libc::F_ADD_SEALS, seals) } == -1 {
        return Err(SandboxError::Io(io::Error::last_os_error()));
    }
    Ok(file)
}
fn scope_unit_name() -> Result<String, SandboxError> {
    let identifier = std::fs::read_to_string("/proc/sys/kernel/random/uuid").map_err(|error| {
        SandboxError::Unavailable(format!("generate sandbox scope identity: {error}"))
    })?;
    let identifier = identifier.trim();
    let valid = identifier.len() == 36
        && identifier
            .bytes()
            .enumerate()
            .all(|(index, byte)| match index {
                8 | 13 | 18 | 23 => byte == b'-',
                _ => byte.is_ascii_hexdigit(),
            });
    if !valid {
        return Err(SandboxError::Unavailable(
            "generate sandbox scope identity: invalid kernel UUID".to_owned(),
        ));
    }
    Ok(format!("cott-sandbox-{identifier}.scope"))
}
fn wait_for_scope_ack(
    acknowledgement: &mpsc::Receiver<Result<(), String>>,
    started: &Instant,
    wall_time: Duration,
) -> Result<(), ScopeSetupFailure> {
    loop {
        match acknowledgement.try_recv() {
            Ok(Ok(())) => return Ok(()),
            Ok(Err(error)) => return Err(ScopeSetupFailure::Unavailable(error)),
            Err(mpsc::TryRecvError::Empty) => {}
            Err(mpsc::TryRecvError::Disconnected) => {
                return Err(ScopeSetupFailure::Unavailable(
                    "sandbox scope startup acknowledgement reader stopped".to_owned(),
                ));
            }
        }
        if started.elapsed() >= wall_time {
            return Err(ScopeSetupFailure::TimedOut);
        }
        thread::sleep(Duration::from_millis(5));
    }
}

fn user_manager_environment() -> Vec<(OsString, OsString)> {
    use std::os::unix::fs::MetadataExt;

    let mut environment = ["DBUS_SESSION_BUS_ADDRESS", "XDG_RUNTIME_DIR"]
        .into_iter()
        .filter_map(|name| std::env::var_os(name).map(|value| (OsString::from(name), value)))
        .collect::<Vec<_>>();
    if environment.is_empty() {
        let uid = unsafe { libc::geteuid() };
        let runtime = PathBuf::from(format!("/run/user/{uid}"));
        if std::fs::symlink_metadata(&runtime).is_ok_and(|metadata| {
            metadata.is_dir() && metadata.uid() == uid && metadata.mode() & 0o077 == 0
        }) {
            environment.push((OsString::from("XDG_RUNTIME_DIR"), runtime.into_os_string()));
        }
    }
    environment
}

fn require_canonical_tool(path: &Path, name: &str) -> Result<(), SandboxError> {
    let canonical = std::fs::canonicalize(path)
        .map_err(|_| SandboxError::Unavailable(format!("{name} {} is required", path.display())))?;
    if canonical != path || !path.is_file() {
        return Err(SandboxError::Unavailable(format!(
            "canonical {name} {} is required",
            path.display()
        )));
    }
    Ok(())
}
enum ScopeSetupFailure {
    TimedOut,
    Unavailable(String),
}

struct TransientScope {
    unit: String,
    systemctl: PathBuf,
    manager_environment: Vec<(OsString, OsString)>,
    cgroup: Option<PathBuf>,
    cleaned: bool,
}

impl TransientScope {
    fn new(
        unit: String,
        systemctl: PathBuf,
        manager_environment: Vec<(OsString, OsString)>,
    ) -> Self {
        Self {
            unit,
            systemctl,
            manager_environment,
            cgroup: None,
            cleaned: false,
        }
    }

    fn wait_until_ready(
        &mut self,
        child: &mut std::process::Child,
        tasks_max: u64,
        started: &Instant,
        wall_time: Duration,
        launcher_cgroup: &Path,
    ) -> Result<(), ScopeSetupFailure> {
        loop {
            if started.elapsed() >= wall_time {
                return Err(ScopeSetupFailure::TimedOut);
            }
            match child.try_wait() {
                Ok(Some(status)) => {
                    return Err(ScopeSetupFailure::Unavailable(format!(
                        "systemd user manager did not establish sandbox scope (status {status})"
                    )));
                }
                Ok(None) => {}
                Err(error) => {
                    return Err(ScopeSetupFailure::Unavailable(format!(
                        "inspect sandbox scope launcher: {error}"
                    )));
                }
            }
            match process_cgroup(child.id()) {
                Ok(path)
                    if path != launcher_cgroup
                        && path
                            .file_name()
                            .and_then(|name| name.to_str())
                            .is_some_and(|name| name == self.unit) =>
                {
                    self.cgroup = Some(path.clone());
                    verify_scope_tasks_max(&path, tasks_max)
                        .map_err(ScopeSetupFailure::Unavailable)?;
                    return Ok(());
                }
                Ok(_) => {}
                Err(error) if error.kind() == io::ErrorKind::NotFound => {}
                Err(error) => {
                    return Err(ScopeSetupFailure::Unavailable(format!(
                        "inspect sandbox scope cgroup: {error}"
                    )));
                }
            }
            thread::sleep(Duration::from_millis(5));
        }
    }

    fn kill_all(&mut self) -> io::Result<()> {
        if self.cleaned {
            return Ok(());
        }
        let Some(cgroup) = &self.cgroup else {
            self.cleaned = true;
            return Ok(());
        };
        if !cgroup_populated(cgroup)? {
            self.cleaned = true;
            return Ok(());
        }
        let status = self.request_kill()?;
        if !status.success() && cgroup_populated(cgroup)? {
            return Err(io::Error::other(format!(
                "systemctl could not kill sandbox scope {} (status {status})",
                self.unit
            )));
        }
        let started = Instant::now();
        while cgroup_populated(cgroup)? {
            if started.elapsed() >= SCOPE_CLEANUP_TIMEOUT {
                return Err(io::Error::new(
                    io::ErrorKind::TimedOut,
                    format!("sandbox scope {} remained populated", self.unit),
                ));
            }
            thread::sleep(Duration::from_millis(5));
        }
        self.cleaned = true;
        Ok(())
    }

    fn request_kill(&self) -> io::Result<std::process::ExitStatus> {
        let mut command = Command::new(&self.systemctl);
        command
            .args([
                "--user",
                "--no-ask-password",
                "kill",
                "--kill-whom=all",
                "--signal=SIGKILL",
            ])
            .arg(&self.unit)
            .env_clear()
            .envs(
                self.manager_environment
                    .iter()
                    .map(|(name, value)| (name, value)),
            )
            .stdin(Stdio::null())
            .stdout(Stdio::null())
            .stderr(Stdio::null());
        let mut child = command.spawn()?;
        let started = Instant::now();
        loop {
            if let Some(status) = child.try_wait()? {
                return Ok(status);
            }
            if started.elapsed() >= SCOPE_CLEANUP_TIMEOUT {
                let _ = child.kill();
                let _ = child.wait();
                return Err(io::Error::new(
                    io::ErrorKind::TimedOut,
                    format!("timed out killing sandbox scope {}", self.unit),
                ));
            }
            thread::sleep(Duration::from_millis(5));
        }
    }
}

impl Drop for TransientScope {
    fn drop(&mut self) {
        let _ = self.kill_all();
    }
}

fn process_cgroup(process_id: u32) -> io::Result<PathBuf> {
    let memberships = std::fs::read_to_string(format!("/proc/{process_id}/cgroup"))?;
    let path = memberships
        .lines()
        .find_map(|line| line.strip_prefix("0::"))
        .ok_or_else(|| io::Error::other("cgroup v2 unified hierarchy is required"))?;
    let relative = path
        .strip_prefix('/')
        .ok_or_else(|| io::Error::other("invalid cgroup v2 membership path"))?;
    let relative = Path::new(relative);
    if !relative
        .components()
        .all(|component| matches!(component, std::path::Component::Normal(_)))
    {
        return Err(io::Error::other("invalid cgroup v2 membership path"));
    }
    Ok(Path::new("/sys/fs/cgroup").join(relative))
}

fn verify_scope_tasks_max(cgroup: &Path, expected: u64) -> Result<(), String> {
    let configured = std::fs::read_to_string(cgroup.join("pids.max"))
        .map_err(|error| format!("sandbox pids controller is unavailable: {error}"))?;
    let configured = configured.trim();
    let actual = configured
        .parse::<u64>()
        .map_err(|_| format!("sandbox scope task limit is invalid: found {configured:?}"))?;
    if actual != expected {
        return Err(format!(
            "sandbox scope task limit is not enforced: expected {expected}, found {actual}"
        ));
    }
    let root = Path::new("/sys/fs/cgroup");
    let mut ancestor = cgroup.parent();
    while let Some(path) = ancestor.filter(|path| path.starts_with(root) && *path != root) {
        let configured = std::fs::read_to_string(path.join("pids.max"))
            .map_err(|error| format!("inspect ancestor pids controller: {error}"))?;
        if configured.trim() != "max" {
            let configured = configured.trim().parse::<u64>().map_err(|_| {
                format!(
                    "inspect ancestor pids controller: invalid limit {:?}",
                    configured.trim()
                )
            })?;
            if configured < expected {
                return Err(format!(
                    "sandbox scope task budget {expected} exceeds ancestor limit {configured}"
                ));
            }
        }
        ancestor = path.parent();
    }
    Ok(())
}

fn cgroup_populated(cgroup: &Path) -> io::Result<bool> {
    cgroup_events_populated(std::fs::read_to_string(cgroup.join("cgroup.events")))
}

fn cgroup_events_populated(events: io::Result<String>) -> io::Result<bool> {
    let events = match events {
        Ok(events) => events,
        // kernfs returns ENODEV when a cgroup disappears after open but before read.
        // Removal is possible only after the scope has become empty.
        Err(error)
            if error.kind() == io::ErrorKind::NotFound
                || error.raw_os_error() == Some(libc::ENODEV) =>
        {
            return Ok(false);
        }
        Err(error) => return Err(error),
    };
    match events
        .lines()
        .find_map(|line| line.strip_prefix("populated "))
    {
        Some("0") => Ok(false),
        Some("1") => Ok(true),
        _ => Err(io::Error::other(
            "cgroup.events has an invalid populated state",
        )),
    }
}

fn require_loopback_setup() -> Result<(), SandboxError> {
    if Path::new("/bin/sh").is_file()
        && Path::new("/usr/sbin/ip").is_file()
        && Path::new("/usr/bin/setpriv").is_file()
    {
        Ok(())
    } else {
        Err(SandboxError::UnsupportedLoopback)
    }
}

fn kill_process_group(process_id: u32) -> io::Result<()> {
    if unsafe { libc::kill(-(process_id as libc::pid_t), libc::SIGKILL) } != 0 {
        let error = io::Error::last_os_error();
        if error.raw_os_error() != Some(libc::ESRCH) {
            return Err(error);
        }
    }
    Ok(())
}
fn terminate_process_session(child: &mut std::process::Child) -> io::Result<()> {
    let termination = kill_process_session(child.id());
    let waited = child.wait().map(|_| ());
    termination.and(waited)
}

fn kill_process_session(session_id: u32) -> io::Result<()> {
    kill_process_group(session_id)?;
    let mut failure = None;
    for entry in std::fs::read_dir("/proc")? {
        let Ok(entry) = entry else { continue };
        let name = entry.file_name();
        if !name.as_encoded_bytes().iter().all(u8::is_ascii_digit) {
            continue;
        }
        let Ok(stat) = std::fs::read_to_string(entry.path().join("stat")) else {
            continue;
        };
        let Some(session) = stat
            .rsplit_once(") ")
            .and_then(|(_, fields)| fields.split_whitespace().nth(3))
            .and_then(|session| session.parse::<u32>().ok())
        else {
            continue;
        };
        if session == session_id {
            let Ok(process_id) = name.to_string_lossy().parse::<libc::pid_t>() else {
                continue;
            };
            if unsafe { libc::kill(process_id, libc::SIGKILL) } != 0 {
                let error = io::Error::last_os_error();
                if error.raw_os_error() != Some(libc::ESRCH) {
                    failure.get_or_insert(error);
                }
            }
        }
    }
    failure.map_or(Ok(()), Err)
}

fn is_loopback_setup_failure(status: Option<i32>, stderr: &[u8]) -> bool {
    status == Some(125)
        && String::from_utf8_lossy(stderr)
            .lines()
            .last()
            .is_some_and(|line| line.trim() == LOOPBACK_SETUP_FAILURE)
}

fn supports_bubblewrap_version(version: &str) -> bool {
    is_at_least(version, (0, 9, 0))
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
    if !output.status.success() || !supports_bubblewrap_version(version) {
        return Err(SandboxError::Unavailable(format!(
            "bubblewrap {version} is unsupported; require >=0.9.0"
        )));
    }
    Ok(())
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn bubblewrap_version_has_no_upper_bound() {
        assert!(supports_bubblewrap_version("0.9.0"));
        assert!(supports_bubblewrap_version("1.0.0"));
        assert!(!supports_bubblewrap_version("0.8.9"));
    }

    #[test]
    fn retired_cgroup_is_empty_but_other_observation_failures_are_not() {
        assert!(
            !cgroup_events_populated(Err(io::Error::from_raw_os_error(libc::ENODEV)))
                .expect("removed open cgroup")
        );
        assert!(
            !cgroup_events_populated(Err(io::Error::from(io::ErrorKind::NotFound)))
                .expect("removed cgroup path")
        );
        assert!(
            cgroup_events_populated(Ok("populated 1\nfrozen 0\n".to_owned())).expect("live cgroup")
        );
        assert!(
            !cgroup_events_populated(Ok("populated 0\nfrozen 0\n".to_owned()))
                .expect("empty cgroup")
        );
        assert_eq!(
            cgroup_events_populated(Err(io::Error::from(io::ErrorKind::PermissionDenied)))
                .expect_err("lack of authority must fail closed")
                .kind(),
            io::ErrorKind::PermissionDenied
        );
        assert!(cgroup_events_populated(Ok("frozen 0\n".to_owned())).is_err());
    }
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
