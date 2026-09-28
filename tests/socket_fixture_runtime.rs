use std::collections::BTreeMap;
use std::fs;
use std::path::{Path, PathBuf};
use std::process;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use cott::sandbox::{BindMounts, NetworkAccess, ResourceLimits, SandboxError, SandboxSpec, run};
use serde_json::{Value, json};

const PYTHON3: &str = "/usr/bin/python3";
const FIXTURE: &str = include_str!("../src/python/socket_fixture.py");
// Shared scenario harness. `session_request` follows the control flow of
// real.harlequin.hsql.send_session_request: read HELLO, send REQUEST, collect
// STDOUT until EXIT, and on KeyboardInterrupt open a second connection that sends
// CANCEL after reading HELLO.
const PRELUDE: &str = r##"
import asyncio
import json
import os
import signal
import socket
import stat
import struct
import subprocess
import sys
import threading
import time

ROOT = os.path.join(os.getcwd(), "scenario")
os.mkdir(ROOT)
os.chdir(ROOT)
SOCKET = "hsql/live.sock"
LIMITS = {"scenario_timeout_ms": 5000, "transcript_events": 16}


def frame(tag, payload):
    return struct.pack("!BI", tag, len(payload)) + payload


HELLO = frame(1, b"0.1")
REQUEST = b"select 1;"
RESPONSE = frame(3, b"ok\n") + frame(5, struct.pack("!i", 0))
CANCEL = b"r1"


def config(**overrides):
    value = {
        "kind": "socket",
        "id": "session",
        "path": SOCKET,
        "greeting": HELLO,
        "response": RESPONSE,
        "interrupt_after_request": False,
        "span": {"start": 0, "end": 0},
        "source_order": 0,
    }
    value.update(overrides)
    return value


def read_exact(sock, size):
    data = bytearray()
    while len(data) < size:
        part = sock.recv(size - len(data))
        if not part:
            return None
        data.extend(part)
    return bytes(data)


def read_frame(sock):
    header = read_exact(sock, 5)
    if header is None:
        return None
    tag, length = struct.unpack("!BI", header)
    payload = read_exact(sock, length)
    return None if payload is None else (tag, payload)


def session_request(path=SOCKET, request=REQUEST):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(path)
        try:
            hello = read_frame(sock)
            if hello is None or hello[0] != 1:
                return ["closed"]
            sock.sendall(frame(2, request))
            stdout = bytearray()
            while True:
                reply = read_frame(sock)
                if reply is None:
                    return ["closed"]
                if reply[0] == 3:
                    stdout.extend(reply[1])
                elif reply[0] == 5:
                    return ["exit", stdout.decode(), struct.unpack("!i", reply[1])[0]]
        except KeyboardInterrupt:
            with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as other:
                other.connect(path)
                hello = read_frame(other)
                if hello is not None and hello[0] == 1:
                    other.sendall(frame(7, CANCEL))
            return ["interrupted"]
        except OSError:
            return ["closed"]


def closing(fixture):
    try:
        fixture.close()
    except FramedSocketFixtureError as error:
        return str(error)
    return None


def resources():
    return {"fds": sorted(os.listdir("/proc/self/fd")), "threads": threading.active_count()}


def report(**values):
    print(json.dumps(values, sort_keys=True))
"##;

fn scratch() -> PathBuf {
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .expect("time after epoch")
        .as_nanos();
    let scratch =
        std::env::temp_dir().join(format!("cott-socket-fixture-{}-{nonce}", process::id()));
    fs::create_dir(&scratch).expect("create scratch");
    scratch
}

/// Runs one scenario in a fresh sandboxed interpreter. The fixture only ever
/// signals its own PID, so any SIGINT stays inside that sandboxed process.
fn scenario(name: &str, body: &str) -> Option<Value> {
    if !Path::new(PYTHON3).is_file() {
        eprintln!("skipping {name}: {PYTHON3} is unavailable");
        return None;
    }
    let cwd = scratch();
    let read_only = scratch();
    fs::create_dir(read_only.join("elsewhere")).expect("readonly target");
    std::os::unix::fs::symlink(cwd.join("scenario"), read_only.join("root-link"))
        .expect("readonly root symlink");
    std::os::unix::fs::symlink("elsewhere", read_only.join("link"))
        .expect("readonly child symlink");
    let spec = SandboxSpec {
        program: PathBuf::from(PYTHON3),
        arguments: vec!["-c".to_owned(), format!("{FIXTURE}\n{PRELUDE}\n{body}")],
        cwd: cwd.clone(),
        environment: BTreeMap::from([(
            "FIXTURE_READ_ONLY".to_owned(),
            read_only.display().to_string(),
        )]),
        stdin: Vec::new(),
        binds: BindMounts {
            writable: vec![cwd.clone()],
            read_only: vec![read_only.clone()],
        },
        network: NetworkAccess::Disabled,
        limits: ResourceLimits {
            cpu_time: Duration::from_secs(10),
            address_space_bytes: 1024 * 1024 * 1024,
            process_count: 16,
            open_files: 128,
            file_size_bytes: 16 * 1024 * 1024,
            wall_time: Duration::from_secs(30),
            stream_limit_bytes: 64 * 1024,
            writable_bytes: 16 * 1024 * 1024,
        },
    };
    let result = run(&spec);
    fs::remove_dir_all(&cwd).expect("remove scratch");
    fs::remove_dir_all(&read_only).expect("remove readonly fixture");
    let completed = match result {
        Err(SandboxError::Unavailable(reason)) => {
            eprintln!("skipping {name}: {reason}");
            return None;
        }
        result => result.expect("sandbox must run the socket fixture scenario"),
    };
    let stderr = String::from_utf8_lossy(&completed.stderr);
    assert_eq!(completed.status, Some(0), "{name} failed: {stderr}");
    assert!(stderr.is_empty(), "{name} wrote stderr: {stderr}");
    let stdout = String::from_utf8(completed.stdout).expect("scenario stdout is UTF-8");
    let report = serde_json::from_str(stdout.trim()).expect("scenario prints one JSON object");
    Some(report)
}

fn events(expected: &[(&str, u64)]) -> Value {
    Value::Array(
        expected
            .iter()
            .enumerate()
            .map(|(sequence, (kind, bytes))| {
                json!({"sequence": sequence, "kind": kind, "bytes": bytes})
            })
            .collect(),
    )
}

fn failure<'a>(report: &'a Value, key: &str) -> &'a str {
    report[key]
        .as_str()
        .unwrap_or_else(|| panic!("`{key}` must be a fixture failure: {report}"))
}

// Frame sizes of the harness bytes: HELLO frame, REQUEST frame, RESPONSE frames,
// CANCEL frame.
const HELLO: u64 = 8;
const REQUEST: u64 = 14;
const RESPONSE: u64 = 17;
const CANCEL: u64 = 7;

#[test]
fn normal_exchange_serves_authored_bytes_from_a_private_socket_and_cleans_up() {
    let Some(report) = scenario(
        "normal socket exchange",
        r#"
before = resources()
fixture = FramedSocketFixture(config(), ROOT, LIMITS)
fixture.start()
status = os.lstat(SOCKET)
parent = os.lstat("hsql")
fixture.arm()
try:
    result = session_request()
finally:
    fixture.disarm()
try:
    session_request()
    reconnect = "served"
except ConnectionRefusedError:
    reconnect = "refused"
error = closing(fixture)
report(
    result=result,
    reconnect=reconnect,
    error=error,
    events=fixture.events,
    is_socket=stat.S_ISSOCK(status.st_mode),
    socket_mode=stat.S_IMODE(status.st_mode),
    parent_mode=stat.S_IMODE(parent.st_mode),
    socket_left=os.path.lexists(SOCKET),
    restored=resources() == before,
)
"#,
    ) else {
        return;
    };
    assert_eq!(report["result"], json!(["exit", "ok\n", 0]), "{report}");
    assert_eq!(report["reconnect"], json!("refused"), "{report}");
    assert_eq!(report["error"], Value::Null, "{report}");
    assert_eq!(
        report["events"],
        events(&[
            ("socket.send", HELLO),
            ("socket.receive", REQUEST),
            ("socket.send", RESPONSE),
        ])
    );
    assert_eq!(report["is_socket"], json!(true));
    assert_eq!(report["socket_mode"], json!(0o600));
    assert_eq!(report["parent_mode"], json!(0o700));
    assert_eq!(report["socket_left"], json!(false));
    assert_eq!(report["restored"], json!(true), "leaked resources");
}

#[test]
fn armed_interrupt_raises_keyboard_interrupt_in_the_runner_and_serves_one_cancellation() {
    // Mirrors the contract runner entry that keeps Python's default SIGINT handler.
    let Some(report) = scenario(
        "armed socket interrupt",
        r#"
async def main():
    before = resources()
    fixture = FramedSocketFixture(config(interrupt_after_request=True), ROOT, LIMITS)
    fixture.start()
    fixture.arm()
    try:
        result = session_request()
    finally:
        fixture.disarm()
    error = closing(fixture)
    return {
        "result": result,
        "error": error,
        "events": fixture.events,
        "socket_left": os.path.lexists(SOCKET),
        "restored": resources() == before,
    }


with asyncio.Runner() as runner:
    values = runner.get_loop().run_until_complete(main())
report(handler_preserved=signal.getsignal(signal.SIGINT) is signal.default_int_handler, **values)
"#,
    ) else {
        return;
    };
    assert_eq!(report["result"], json!(["interrupted"]), "{report}");
    assert_eq!(report["error"], Value::Null, "{report}");
    assert_eq!(
        report["events"],
        events(&[
            ("socket.send", HELLO),
            ("socket.receive", REQUEST),
            ("socket.interrupt", 0),
            ("socket.send", HELLO),
            ("socket.receive", CANCEL),
        ])
    );
    assert_eq!(report["handler_preserved"], json!(true));
    assert_eq!(report["socket_left"], json!(false));
    assert_eq!(report["restored"], json!(true), "leaked resources");
}

#[test]
fn asyncio_run_sigint_shim_is_refused_and_no_signal_is_sent() {
    let Some(report) = scenario(
        "asyncio.run SIGINT shim",
        r#"
async def main():
    fixture = FramedSocketFixture(config(interrupt_after_request=True), ROOT, LIMITS)
    fixture.start()
    try:
        fixture.arm()
    except FramedSocketFixtureError as error:
        arm_error = str(error)
    else:
        arm_error = None
    result = session_request()
    return {"arm_error": arm_error, "result": result, "error": closing(fixture), "events": fixture.events}


report(**asyncio.run(main()))
"#,
    ) else {
        return;
    };
    assert!(
        failure(&report, "arm_error").contains("SIGINT handler"),
        "{report}"
    );
    assert_eq!(report["result"], json!(["closed"]), "{report}");
    assert!(failure(&report, "error").contains("disarmed"), "{report}");
    assert_eq!(
        report["events"],
        events(&[("socket.send", HELLO), ("socket.receive", REQUEST)])
    );
}

#[test]
fn disarmed_interrupt_fixture_releases_the_client_without_signalling() {
    let Some(report) = scenario(
        "disarmed socket interrupt",
        r#"
fixture = FramedSocketFixture(config(interrupt_after_request=True), ROOT, LIMITS)
fixture.start()
result = session_request()
report(result=result, error=closing(fixture), events=fixture.events, socket_left=os.path.lexists(SOCKET))
"#,
    ) else {
        return;
    };
    assert_eq!(report["result"], json!(["closed"]), "{report}");
    assert!(failure(&report, "error").contains("disarmed"), "{report}");
    assert_eq!(
        report["events"],
        events(&[("socket.send", HELLO), ("socket.receive", REQUEST)])
    );
    assert_eq!(report["socket_left"], json!(false));
}

#[test]
fn foreign_peer_is_refused_before_greeting_and_never_signals_the_runner() {
    let Some(report) = scenario(
        "foreign socket peer",
        r#"
CHILD = """
import socket, struct, sys
with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
    sock.connect(sys.argv[1])
    try:
        sock.sendall(struct.pack("!BI", 2, 1) + b"x")
        data = sock.recv(64)
    except OSError:
        data = b""
    print("greeting" if data else "closed")
"""
before = resources()
fixture = FramedSocketFixture(config(interrupt_after_request=True), ROOT, LIMITS)
fixture.start()
fixture.arm()
interrupted = False
child = None
try:
    child = subprocess.run(
        [sys.executable, "-c", CHILD, SOCKET], capture_output=True, text=True, timeout=10, check=True
    ).stdout.strip()
except KeyboardInterrupt:
    interrupted = True
finally:
    fixture.disarm()
error = closing(fixture)
report(child=child, interrupted=interrupted, error=error, events=fixture.events, restored=resources() == before)
"#,
    ) else {
        return;
    };
    assert_eq!(report["child"], json!("closed"), "{report}");
    assert_eq!(report["interrupted"], json!(false), "{report}");
    assert!(
        failure(&report, "error").contains("peer is not this contract-runner process"),
        "{report}"
    );
    assert_eq!(report["events"], json!([]));
    assert_eq!(report["restored"], json!(true), "leaked resources");
}

#[test]
fn inbound_frames_are_bounded_at_one_mebibyte_including_the_header() {
    let Some(report) = scenario(
        "socket frame bound",
        r#"
LIMIT = 1 << 20


def announce(path, payload_length, send_payload):
    with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
        sock.connect(path)
        if read_frame(sock) is None:
            return ["closed"]
        sock.sendall(struct.pack("!BI", 2, payload_length))
        if send_payload:
            sock.sendall(bytes(payload_length))
        try:
            reply = read_frame(sock)
        except OSError:
            reply = None
        return ["closed"] if reply is None else ["frame", reply[0]]


largest = FramedSocketFixture(config(path="hsql/largest.sock"), ROOT, LIMITS)
largest.start()
accepted = announce("hsql/largest.sock", LIMIT - 5, True)
accepted_error = closing(largest)
oversized = FramedSocketFixture(config(path="hsql/oversized.sock", interrupt_after_request=True), ROOT, LIMITS)
oversized.start()
oversized.arm()
try:
    rejected = announce("hsql/oversized.sock", LIMIT - 4, False)
finally:
    oversized.disarm()
report(
    accepted=accepted,
    accepted_error=accepted_error,
    accepted_events=largest.events,
    rejected=rejected,
    rejected_error=closing(oversized),
    refused_events=oversized.events,
)
"#,
    ) else {
        return;
    };
    assert_eq!(report["accepted"], json!(["frame", 3]), "{report}");
    assert_eq!(report["accepted_error"], Value::Null, "{report}");
    assert_eq!(
        report["accepted_events"],
        events(&[
            ("socket.send", HELLO),
            ("socket.receive", 1 << 20),
            ("socket.send", RESPONSE),
        ])
    );
    assert_eq!(report["rejected"], json!(["closed"]), "{report}");
    assert!(
        failure(&report, "rejected_error").contains("1 MiB"),
        "{report}"
    );
    assert_eq!(report["refused_events"], events(&[("socket.send", HELLO)]));
}

#[test]
fn setup_rejects_traversal_symlinks_existing_targets_and_shared_parents_without_touching_them() {
    let Some(report) = scenario(
        "socket setup rejection",
        r#"
before = resources()
invalid = {}
for path in ("../escape.sock", "/abs.sock", "hsql/./live.sock", "hsql//live.sock", "hsql/", ""):
    try:
        FramedSocketFixture(config(path=path), ROOT, LIMITS)
    except FramedSocketFixtureError:
        invalid[path] = "rejected"
    else:
        invalid[path] = "accepted"


def refused(path, root=ROOT):
    fixture = FramedSocketFixture(config(path=path), root, LIMITS)
    try:
        fixture.start()
    except FramedSocketFixtureError as error:
        return str(error)
    fixture.close()
    return None


read_only = os.environ["FIXTURE_READ_ONLY"]
root_link = os.path.join(read_only, "root-link")
root_symlink = refused(SOCKET, root_link)
symlink = refused("link/live.sock", read_only)
os.mkdir("taken", 0o700)
with open("taken/live.sock", "wb") as handle:
    handle.write(b"keep")
existing = refused("taken/live.sock")
with open("taken/live.sock", "rb") as handle:
    kept = handle.read().decode()
os.mkdir("shared")
os.chmod("shared", 0o770)
shared = refused("shared/live.sock")
report(
    invalid=invalid,
    root_symlink=root_symlink,
    root_untouched=not os.path.lexists("hsql"),
    symlink=symlink,
    elsewhere=os.listdir(os.path.join(read_only, "elsewhere")),
    existing=existing,
    kept=kept,
    shared=shared,
    shared_entries=os.listdir("shared"),
    restored=resources() == before,
)
"#,
    ) else {
        return;
    };
    assert_eq!(
        report["invalid"],
        json!({
            "../escape.sock": "rejected",
            "/abs.sock": "rejected",
            "hsql/./live.sock": "rejected",
            "hsql//live.sock": "rejected",
            "hsql/": "rejected",
            "": "rejected",
        })
    );
    assert!(
        failure(&report, "root_symlink").contains("non-symlink directory"),
        "{report}"
    );
    assert_eq!(report["root_untouched"], json!(true));
    assert!(failure(&report, "symlink").contains("symlink"), "{report}");
    assert_eq!(report["elsewhere"], json!([]));
    assert!(
        failure(&report, "existing").contains("already exists"),
        "{report}"
    );
    assert_eq!(report["kept"], json!("keep"));
    assert!(
        failure(&report, "shared").contains("writable by group or others"),
        "{report}"
    );
    assert_eq!(report["shared_entries"], json!([]));
    assert_eq!(report["restored"], json!(true), "leaked resources");
}

#[test]
fn close_leaves_a_replaced_socket_path_untouched() {
    let Some(report) = scenario(
        "replaced socket path",
        r#"
before = resources()
fixture = FramedSocketFixture(config(), ROOT, LIMITS)
fixture.start()
os.unlink(SOCKET)
with open(SOCKET, "wb") as handle:
    handle.write(b"replacement")
error = closing(fixture)
with open(SOCKET, "rb") as handle:
    kept = handle.read().decode()
report(error=error, kept=kept, events=fixture.events, restored=resources() == before)
"#,
    ) else {
        return;
    };
    assert!(failure(&report, "error").contains("replaced"), "{report}");
    assert_eq!(report["kept"], json!("replacement"));
    assert_eq!(report["events"], json!([]));
    assert_eq!(report["restored"], json!(true), "leaked resources");
}

#[test]
fn scenario_timeout_and_transcript_limit_release_the_client_and_fail_the_fixture() {
    let Some(report) = scenario(
        "socket fixture limits",
        r#"
timed = FramedSocketFixture(config(path="hsql/timed.sock"), ROOT, {"scenario_timeout_ms": 300, "transcript_events": 16})
timed.start()
started = time.monotonic()
with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as sock:
    sock.connect("hsql/timed.sock")
    greeting = read_frame(sock)
    released = sock.recv(1)
elapsed = time.monotonic() - started
timed_error = closing(timed)
capped = FramedSocketFixture(config(path="hsql/capped.sock"), ROOT, {"scenario_timeout_ms": 5000, "transcript_events": 1})
capped.start()
capped_result = session_request("hsql/capped.sock")
report(
    greeting=greeting is not None,
    released=released.hex(),
    bounded=elapsed < 3,
    timed_error=timed_error,
    timed_events=timed.events,
    capped_result=capped_result,
    capped_error=closing(capped),
    capped_events=capped.events,
)
"#,
    ) else {
        return;
    };
    assert_eq!(report["greeting"], json!(true), "{report}");
    assert_eq!(report["released"], json!(""), "client must see EOF");
    assert_eq!(report["bounded"], json!(true), "{report}");
    assert!(
        failure(&report, "timed_error").contains("scenario_timeout_ms"),
        "{report}"
    );
    assert_eq!(report["timed_events"], events(&[("socket.send", HELLO)]));
    assert_eq!(report["capped_result"], json!(["closed"]), "{report}");
    assert!(
        failure(&report, "capped_error").contains("transcript_events"),
        "{report}"
    );
    assert_eq!(report["capped_events"], events(&[("socket.send", HELLO)]));
}
