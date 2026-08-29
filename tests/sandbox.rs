use std::collections::BTreeMap;
use std::fs;
use std::path::PathBuf;
use std::process;
use std::thread;
use std::time::{Duration, SystemTime, UNIX_EPOCH};

use cott::sandbox::{
    BindMounts, NetworkAccess, OutputStream, ResourceLimits, SandboxError, SandboxOutcome,
    SandboxSpec, run,
};

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
fn contract_test_limits_are_fixed() {
    let limits = ResourceLimits::contract_test();
    assert_eq!(limits.cpu_time, Duration::from_secs(30));
    assert_eq!(limits.address_space_bytes, 1024 * 1024 * 1024);
    assert_eq!(limits.process_count, 16);
    assert_eq!(limits.open_files, 128);
    assert_eq!(limits.file_size_bytes, 16 * 1024 * 1024);
    assert_eq!(limits.wall_time, Duration::from_secs(30));
    assert_eq!(limits.stream_limit_bytes, 1024 * 1024);
    assert_eq!(limits.writable_bytes, 16 * 1024 * 1024);
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
