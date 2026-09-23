use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::process;
use std::thread;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use cott::sandbox::{
    BindMounts, NetworkAccess, OutputStream, ResourceLimits, SandboxError, SandboxOutcome,
    SandboxSpec, run,
};

const PYTHON3: &str = "/usr/bin/python3";
const FIT_THREAD_SCRIPT: &str = r#"
import pathlib
import sys
import threading
import time

root = pathlib.Path(".")
name = sys.argv[1]
worker_count = int(sys.argv[2])
participants = sys.argv[3].split(",")
gate = threading.Event()
started = [threading.Event() for _ in range(worker_count)]
completed = []
completed_lock = threading.Lock()
poll = threading.Event()

def wait_for_barrier(suffix):
    deadline = time.monotonic() + 15
    while not all((root / f"{participant}.{suffix}").is_file() for participant in participants):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise RuntimeError(f"sandbox {suffix} barrier timed out")
        poll.wait(min(0.01, remaining))

def work(index):
    started[index].set()
    if not gate.wait(15):
        return
    with completed_lock:
        completed.append(index)

(root / f"{name}.launched").write_text("")
wait_for_barrier("launched")

workers = []
for index in range(worker_count):
    worker = threading.Thread(target=work, args=(index,))
    worker.start()
    workers.append(worker)

for event in started:
    if not event.wait(5):
        raise RuntimeError("worker did not start")

(root / f"{name}.ready").write_text(str(worker_count))
try:
    wait_for_barrier("ready")
finally:
    gate.set()

for worker in workers:
    worker.join(5)
if any(worker.is_alive() for worker in workers):
    raise RuntimeError("worker did not stop")
if len(completed) != worker_count:
    raise RuntimeError(f"only {len(completed)} of {worker_count} workers executed")
print(f"EXECUTED:{len(completed)}")
"#;
const EXCEED_THREAD_SCRIPT: &str = r#"
import pathlib
import sys
import threading
import time

root = pathlib.Path(".")
name = sys.argv[1]
attempt_count = int(sys.argv[2])
participants = sys.argv[3].split(",")
gate = threading.Event()
workers = []
refused = False
poll = threading.Event()

def wait_for_barrier(suffix):
    deadline = time.monotonic() + 15
    while not all((root / f"{participant}.{suffix}").is_file() for participant in participants):
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise RuntimeError(f"sandbox {suffix} barrier timed out")
        poll.wait(min(0.01, remaining))

def work(started):
    started.set()
    gate.wait(15)

(root / f"{name}.launched").write_text("")
wait_for_barrier("launched")

for _ in range(attempt_count):
    started = threading.Event()
    worker = threading.Thread(target=work, args=(started,))
    try:
        worker.start()
    except RuntimeError as error:
        if "can't start new thread" not in str(error):
            raise
        refused = True
        break
    workers.append(worker)
    if not started.wait(5):
        raise RuntimeError("worker did not start")

if not refused:
    raise RuntimeError(f"all {attempt_count} workers started despite the task limit")

(root / f"{name}.ready").write_text(str(len(workers)))
try:
    wait_for_barrier("ready")
finally:
    gate.set()

for worker in workers:
    worker.join(5)
if any(worker.is_alive() for worker in workers):
    raise RuntimeError("worker did not stop")
print(f"REFUSED:{len(workers)}")
"#;

fn limits(wall_time: Duration, stream_limit_bytes: u64) -> ResourceLimits {
    ResourceLimits {
        cpu_time: Duration::from_secs(2),
        address_space_bytes: 128 * 1024 * 1024,
        process_count: 128,
        open_files: 128,
        file_size_bytes: 16 * 1024 * 1024,
        wall_time,
        stream_limit_bytes,
        writable_bytes: 1024 * 1024,
    }
}

fn task_limits(process_count: u64) -> ResourceLimits {
    ResourceLimits {
        cpu_time: Duration::from_secs(5),
        address_space_bytes: 1024 * 1024 * 1024,
        process_count,
        open_files: 128,
        file_size_bytes: 16 * 1024 * 1024,
        wall_time: Duration::from_secs(20),
        stream_limit_bytes: 4096,
        writable_bytes: 1024 * 1024,
    }
}

fn scratch() -> PathBuf {
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("time after epoch")
        .as_nanos();
    let scratch = std::env::temp_dir().join(format!("cott-sandbox-{}-{nonce}", process::id()));
    fs::create_dir(&scratch).expect("create scratch");
    scratch
}

fn sandbox(
    program: &str,
    arguments: &[&str],
    cwd: PathBuf,
    network: NetworkAccess,
    limits: ResourceLimits,
) -> SandboxSpec {
    let binds = BindMounts {
        writable: vec![cwd.clone()],
        ..BindMounts::default()
    };
    SandboxSpec {
        program: PathBuf::from(program),
        arguments: arguments
            .iter()
            .map(|argument| (*argument).to_owned())
            .collect(),
        cwd,
        environment: BTreeMap::new(),
        stdin: Vec::new(),
        binds,
        network,
        limits,
    }
}

#[test]
fn scope_startup_preserves_binary_stdin_with_many_open_descriptors() {
    let _descriptors = (0..24)
        .map(|_| fs::File::open("/dev/null").expect("hold descriptor"))
        .collect::<Vec<_>>();
    let cwd = scratch();
    let mut spec = sandbox(
        "/bin/cat",
        &[],
        cwd.clone(),
        NetworkAccess::Disabled,
        limits(Duration::from_secs(5), 4096),
    );
    spec.stdin = b"cott-scope-ready\n\0\xff${HOME}\n1\n".to_vec();
    let result = run(&spec);
    fs::remove_dir_all(&cwd).expect("remove scratch");
    let completed = match result {
        Err(SandboxError::Unavailable(reason)) => {
            eprintln!("skipping scope stdin test: {reason}");
            return;
        }
        result => result.expect("sandbox must execute with high descriptor numbers"),
    };
    assert_eq!(completed.status, Some(0), "{completed:?}");
    assert_eq!(completed.stdout, spec.stdin);
    assert!(completed.stderr.is_empty(), "{completed:?}");
}

#[test]
fn sandbox_environment_keeps_secrets_out_of_process_arguments() {
    if !Path::new(PYTHON3).is_file() {
        eprintln!("skipping environment secrecy test: {PYTHON3} is unavailable");
        return;
    }
    let cwd = scratch();
    let mut spec = sandbox(
        PYTHON3,
        &[
            "-c",
            r#"import os, pathlib, sys
secret = os.environ["COTT_TEST_SECRET"].encode()
assert "DBUS_SESSION_BUS_ADDRESS" not in os.environ
assert "XDG_RUNTIME_DIR" not in os.environ
for process in pathlib.Path("/proc").iterdir():
    if process.name.isdigit():
        try:
            arguments = (process / "cmdline").read_bytes()
        except FileNotFoundError:
            continue
        assert secret not in arguments, "secret leaked into process arguments"
sys.stdout.buffer.write(secret)
"#,
        ],
        cwd.clone(),
        NetworkAccess::Disabled,
        limits(Duration::from_secs(5), 4096),
    );
    let secret = "private-token-${HOME}\nvalue";
    spec.environment
        .insert("COTT_TEST_SECRET".to_owned(), secret.to_owned());
    let result = run(&spec);
    fs::remove_dir_all(&cwd).expect("remove scratch");
    let completed = match result {
        Err(SandboxError::Unavailable(reason)) => {
            eprintln!("skipping environment secrecy test: {reason}");
            return;
        }
        result => result.expect("sandbox environment must be available"),
    };
    assert_eq!(completed.status, Some(0), "{completed:?}");
    assert_eq!(completed.stdout, secret.as_bytes());
    assert!(completed.stderr.is_empty(), "{completed:?}");
}

#[test]
fn task_budgets_are_independent_across_concurrent_sandboxes() {
    if !Path::new(PYTHON3).is_file() {
        eprintln!("skipping independent task-budget test: {PYTHON3} is unavailable");
        return;
    }

    let cwd = scratch();
    let mut runs = Vec::new();
    for name in ["first", "second", "third"] {
        let spec = sandbox(
            PYTHON3,
            &["-c", FIT_THREAD_SCRIPT, name, "12", "first,second,third"],
            cwd.clone(),
            NetworkAccess::Disabled,
            task_limits(16),
        );
        runs.push((name, thread::spawn(move || run(&spec))));
    }
    let results = runs
        .into_iter()
        .map(|(name, run)| {
            (
                name,
                run.join()
                    .expect("concurrent sandbox runner must not panic"),
            )
        })
        .collect::<Vec<_>>();
    fs::remove_dir_all(&cwd).expect("remove scratch");

    if results
        .iter()
        .all(|(_, result)| matches!(result, Err(SandboxError::Unavailable(_))))
    {
        let reason = results
            .iter()
            .find_map(|(_, result)| match result {
                Err(SandboxError::Unavailable(reason)) => Some(reason.as_str()),
                _ => None,
            })
            .expect("all sandbox results are unavailable");
        eprintln!("skipping independent task-budget test: {reason}");
        return;
    }

    for (name, result) in results {
        let completed = match result {
            Ok(completed) => completed,
            other => panic!("{name} sandbox did not complete: {other:?}"),
        };
        assert_eq!(
            completed.status,
            Some(0),
            "{name} sandbox failed: {completed:?}"
        );
        assert!(
            completed.stderr.is_empty(),
            "{name} sandbox wrote stderr: {}",
            String::from_utf8_lossy(&completed.stderr)
        );
        assert_eq!(
            String::from_utf8_lossy(&completed.stdout).trim(),
            "EXECUTED:12",
            "{name} sandbox did not execute every worker"
        );
    }
}

#[test]
fn exhausted_task_budget_does_not_affect_a_sibling_sandbox() {
    if !Path::new(PYTHON3).is_file() {
        eprintln!("skipping exhausted task-budget test: {PYTHON3} is unavailable");
        return;
    }

    let cwd = scratch();
    let limited_spec = sandbox(
        PYTHON3,
        &[
            "-c",
            EXCEED_THREAD_SCRIPT,
            "limited",
            "64",
            "limited,sibling",
        ],
        cwd.clone(),
        NetworkAccess::Disabled,
        task_limits(4),
    );
    let sibling_spec = sandbox(
        PYTHON3,
        &["-c", FIT_THREAD_SCRIPT, "sibling", "12", "limited,sibling"],
        cwd.clone(),
        NetworkAccess::Disabled,
        task_limits(16),
    );
    let limited_run = thread::spawn(move || run(&limited_spec));
    let sibling_run = thread::spawn(move || run(&sibling_spec));
    let results = [
        (
            "limited",
            limited_run
                .join()
                .expect("limited sandbox runner must not panic"),
        ),
        (
            "sibling",
            sibling_run
                .join()
                .expect("sibling sandbox runner must not panic"),
        ),
    ];
    fs::remove_dir_all(&cwd).expect("remove scratch");

    if results
        .iter()
        .all(|(_, result)| matches!(result, Err(SandboxError::Unavailable(_))))
    {
        let reason = results
            .iter()
            .find_map(|(_, result)| match result {
                Err(SandboxError::Unavailable(reason)) => Some(reason.as_str()),
                _ => None,
            })
            .expect("all sandbox results are unavailable");
        eprintln!("skipping exhausted task-budget test: {reason}");
        return;
    }

    let [(_, limited), (_, sibling)] = results;
    let limited = match limited {
        Ok(completed) => completed,
        other => panic!("limited sandbox did not complete: {other:?}"),
    };
    assert_eq!(
        limited.status,
        Some(0),
        "limited sandbox failed: {limited:?}"
    );
    assert!(
        limited.stderr.is_empty(),
        "limited sandbox wrote stderr: {}",
        String::from_utf8_lossy(&limited.stderr)
    );
    let limited_output = String::from_utf8_lossy(&limited.stdout);
    let created = limited_output
        .trim()
        .strip_prefix("REFUSED:")
        .expect("limited sandbox must report thread refusal")
        .parse::<usize>()
        .expect("limited sandbox refusal count must be numeric");
    assert!(
        (1..8).contains(&created),
        "limited sandbox created {created} workers before refusal"
    );

    let sibling = match sibling {
        Ok(completed) => completed,
        other => panic!("sibling sandbox did not complete: {other:?}"),
    };
    assert_eq!(
        sibling.status,
        Some(0),
        "sibling sandbox failed: {sibling:?}"
    );
    assert!(
        sibling.stderr.is_empty(),
        "sibling sandbox wrote stderr: {}",
        String::from_utf8_lossy(&sibling.stderr)
    );
    assert_eq!(
        String::from_utf8_lossy(&sibling.stdout).trim(),
        "EXECUTED:12",
        "sibling sandbox did not execute every worker"
    );
}

#[test]
fn network_modes_build_closed_bubblewrap_commands() {
    assert_eq!(NetworkAccess::Disabled.bwrap_arguments(), ["--unshare-net"]);
    assert_eq!(
        NetworkAccess::IsolatedLoopback.bwrap_arguments(),
        ["--unshare-net", "--cap-add", "CAP_NET_ADMIN"]
    );
    assert!(NetworkAccess::Enabled.bwrap_arguments().is_empty());
}

#[test]
fn unavailable_loopback_has_a_stable_outcome() {
    assert_eq!(
        SandboxError::UnsupportedLoopback.outcome(),
        Some(SandboxOutcome::UnsupportedLoopback)
    );
}

#[test]
fn output_over_limit_terminates_the_sandbox() {
    let cwd = scratch();
    let result = run(&sandbox(
        "/usr/bin/printf",
        &["0123456789"],
        cwd.clone(),
        NetworkAccess::Disabled,
        limits(Duration::from_secs(2), 8),
    ));
    fs::remove_dir_all(&cwd).expect("remove scratch");
    match result {
        Err(SandboxError::Unavailable(_)) => {}
        Err(SandboxError::StreamLimitExceeded {
            stream,
            limit_bytes: 8,
        }) => assert_eq!(
            SandboxOutcome::StreamLimitExceeded {
                stream,
                limit_bytes: 8,
            },
            SandboxOutcome::StreamLimitExceeded {
                stream: OutputStream::Stdout,
                limit_bytes: 8,
            }
        ),
        other => panic!("expected containment skip or stream-limit failure, got {other:?}"),
    }
}

#[test]
fn timeout_kills_the_complete_process_group() {
    let cwd = scratch();
    let survivor = cwd.join("survivor");
    let spec = sandbox(
        "/bin/sh",
        &["-c", "(sleep 1; : > survivor) & sleep 10"],
        cwd.clone(),
        NetworkAccess::Disabled,
        limits(Duration::from_millis(50), 1024),
    );
    let result = run(&spec);
    match result {
        Err(SandboxError::Unavailable(_)) => {
            fs::remove_dir_all(&cwd).expect("remove scratch");
            return;
        }
        Err(SandboxError::Timeout) => {}
        other => panic!("expected timeout, got {other:?}"),
    }
    thread::sleep(Duration::from_secs(2));
    assert!(!survivor.exists(), "descendant survived sandbox timeout");
    fs::remove_dir_all(&cwd).expect("remove scratch");
}

#[test]
fn isolated_loopback_is_available_or_reports_unsupported() {
    let cwd = scratch();
    let result = run(&sandbox(
        "/bin/sh",
        &[
            "-c",
            "test -z \"$(/usr/sbin/ip route show default)\" && case \"$(/usr/sbin/ip link show lo)\" in *UP*) exit 0;; *) exit 1;; esac",
        ],
        cwd.clone(),
        NetworkAccess::IsolatedLoopback,
        limits(Duration::from_secs(2), 1024),
    ));
    fs::remove_dir_all(&cwd).expect("remove scratch");
    match result {
        Err(SandboxError::Unavailable(_) | SandboxError::UnsupportedLoopback) => {}
        Ok(completed) => assert_eq!(completed.status, Some(0), "{completed:?}"),
        other => panic!("isolated loopback must not fall back to host networking: {other:?}"),
    }
}

#[test]
fn disabled_network_has_no_external_route() {
    let cwd = scratch();
    let result = run(&sandbox(
        "/bin/sh",
        &["-c", "test -z \"$(/usr/sbin/ip route show default)\""],
        cwd.clone(),
        NetworkAccess::Disabled,
        limits(Duration::from_secs(2), 1024),
    ));
    fs::remove_dir_all(&cwd).expect("remove scratch");
    match result {
        Err(SandboxError::Unavailable(_)) => {}
        Ok(completed) => assert_eq!(completed.status, Some(0), "{completed:?}"),
        other => panic!("disabled network must not retain a host route: {other:?}"),
    }
}
