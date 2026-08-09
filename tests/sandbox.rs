use std::collections::BTreeMap;
use std::path::PathBuf;
use std::time::Duration;

use cott::sandbox::{
    BindMounts, NetworkAccess, OutputStream, ResourceLimits, SandboxError, SandboxSpec, run,
};

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
}

#[test]
fn output_over_limit_is_failure() {
    let cwd = std::env::current_dir().expect("current directory");
    let result = run(&SandboxSpec {
        program: PathBuf::from("/usr/bin/printf"),
        arguments: vec!["0123456789".to_owned()],
        cwd,
        environment: BTreeMap::new(),
        stdin: Vec::new(),
        binds: BindMounts::default(),
        network: NetworkAccess::Disabled,
        limits: ResourceLimits {
            cpu_time: Duration::from_secs(2),
            address_space_bytes: 128 * 1024 * 1024,
            process_count: 16,
            open_files: 128,
            file_size_bytes: 16 * 1024 * 1024,
            wall_time: Duration::from_secs(2),
            stream_limit_bytes: 8,
            writable_bytes: 1024 * 1024,
        },
    });
    match result {
        Err(SandboxError::Unavailable(_)) => {}
        Err(SandboxError::StreamLimitExceeded {
            stream: OutputStream::Stdout | OutputStream::Stderr,
            limit_bytes: 8,
        }) => {}
        other => panic!("expected containment skip or stream-limit failure, got {other:?}"),
    }
}
