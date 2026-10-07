//! MOCK Pi installation for tests: a fake `node` launcher plus a fake
//! `node_modules/@earendil-works/pi-coding-agent` package whose
//! `dist/bundle/cli.js` is `tests/fixtures/pi/mock_pi_cli.py`. It reproduces
//! Pi's package identity, version probes, and JSONL protocol; it is never a
//! real provider run.
#![allow(dead_code)]

use std::fs;
use std::os::unix::fs::{PermissionsExt, symlink};
use std::path::{Path, PathBuf};

pub const MOCK_CLI: &str = include_str!("../fixtures/pi/mock_pi_cli.py");

pub struct MockPi {
    /// Canonical `dist/bundle/cli.js` entrypoint.
    pub cli: PathBuf,
    /// Directory holding the fake `node` and a `pi` symlink to `cli`.
    pub bin: PathBuf,
    pub package: PathBuf,
}

/// Install a mock Pi package under `root`. `config` becomes `mock.json`; its
/// `probe_version` defaults to `version`.
pub fn install(
    root: &Path,
    version: &str,
    node_version: &str,
    mut config: serde_json::Value,
) -> MockPi {
    let package = root.join("pi-install/node_modules/@earendil-works/pi-coding-agent");
    fs::create_dir_all(package.join("dist/bundle")).expect("mock Pi package");
    fs::write(
        package.join("package.json"),
        serde_json::json!({
            "name": "@earendil-works/pi-coding-agent",
            "version": version,
            "type": "module",
            "bin": {"pi": "dist/bundle/cli.js"},
            "engines": {"node": ">=22.19.0"},
        })
        .to_string(),
    )
    .expect("mock Pi package metadata");
    if config.get("probe_version").is_none() {
        config["probe_version"] = serde_json::json!(version);
    }
    fs::write(package.join("dist/bundle/mock.json"), config.to_string()).expect("mock Pi config");
    let cli = package.join("dist/bundle/cli.js");
    fs::write(&cli, MOCK_CLI).expect("mock Pi entrypoint");
    fs::set_permissions(&cli, fs::Permissions::from_mode(0o755)).expect("entrypoint permissions");
    let bin = root.join("pi-bin");
    fs::create_dir_all(&bin).expect("mock Pi bin");
    let node = bin.join("node");
    fs::write(
        &node,
        format!(
            "#!/bin/sh\nif [ \"$1\" = --version ]; then echo {node_version}; exit 0; fi\nexec /usr/bin/python3 \"$@\"\n"
        ),
    )
    .expect("mock node");
    fs::set_permissions(&node, fs::Permissions::from_mode(0o755)).expect("node permissions");
    symlink(&cli, bin.join("pi")).expect("pi launcher link");
    MockPi {
        cli: fs::canonicalize(&cli).expect("canonical mock entrypoint"),
        bin,
        package,
    }
}

/// Rewrite `mock.json` of an installed mock.
pub fn configure(mock: &MockPi, config: serde_json::Value) {
    fs::write(
        mock.package.join("dist/bundle/mock.json"),
        config.to_string(),
    )
    .expect("mock Pi config");
}
