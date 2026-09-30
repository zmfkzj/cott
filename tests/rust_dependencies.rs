#![allow(dead_code)]
use cott::{hash, manifest, project};
#[path = "../src/rust/dependencies.rs"]
mod dependencies;
use std::{fs, path::PathBuf, process::Command};

#[test]
fn rejects_authored_identity_and_lock_source_mismatches_before_cache_access() {
    let dir = std::env::temp_dir().join(format!("cott-rust-reject-deps-{}", std::process::id()));
    fs::create_dir_all(dir.join("src")).unwrap();
    fs::create_dir(dir.join("rust")).unwrap();
    fs::create_dir(dir.join("metadata")).unwrap();
    struct Cleanup(PathBuf);
    impl Drop for Cleanup {
        fn drop(&mut self) {
            let _ = fs::remove_dir_all(&self.0);
        }
    }
    let _cleanup = Cleanup(dir.clone());
    fs::write(dir.join("cott.toml"),"[project]\nname='demo'\nversion='0.1.0'\nsource='src'\n[target.rust]\nsource='rust'\ngenerated='generated/rust'\nruntime_validation='boundary'\ncargo_manifest='metadata/Cargo.toml'\nlockfile='metadata/Cargo.lock'\n").unwrap();
    fs::write(dir.join("metadata/Cargo.toml"), "").unwrap();
    fs::write(dir.join("metadata/Cargo.lock"), "").unwrap();
    let (config, paths, _) = project::load_rust_config_with_paths(&dir).unwrap();
    for (manifest, lock, expected) in [
        (
            "[package]\nname='wrong'\nversion='0.1.0'\n",
            "version=4\n",
            "name/version",
        ),
        (
            "[package]\nname='demo'\nversion='9.0.0'\n",
            "version=4\n",
            "name/version",
        ),
        (
            "[package]\nname='demo'\nversion='0.1.0'\n[patch.crates-io]\n",
            "version=4\n",
            "patch",
        ),
        (
            "[package]\nname='demo'\nversion='0.1.0'\n[replace]\n",
            "version=4\n",
            "replace",
        ),
        (
            "[package]\nname='demo'\nversion='0.1.0'\n",
            "version=4\n[[package]]\nname='demo'\nversion='0.1.0'\n[[package]]\nname='evil'\nversion='1.0.0'\nsource='git+https://example.test/evil'\n",
            "git",
        ),
        (
            "[package]\nname='demo'\nversion='0.1.0'\n[dependencies]\nmissing='1'\n",
            "version=4\n[[package]]\nname='demo'\nversion='0.1.0'\n",
            "absent",
        ),
    ] {
        fs::write(dir.join("metadata/Cargo.toml"), manifest).unwrap();
        fs::write(dir.join("metadata/Cargo.lock"), lock).unwrap();
        assert!(
            dependencies::load_metadata(&config, &paths)
                .unwrap_err()
                .contains(expected)
        );
    }
}

#[test]
#[ignore = "requires COTT_CARGO and original crates.io archives; never downloads"]
fn native_vendor_build_is_offline_locked_and_runtime_is_unique() {
    let cargo = PathBuf::from(std::env::var_os("COTT_CARGO").expect("COTT_CARGO"));
    assert!(cargo.is_absolute());
    let dir = std::env::temp_dir().join(format!("cott-rust-native-deps-{}", std::process::id()));
    fs::create_dir(&dir).unwrap();
    struct Cleanup(PathBuf);
    impl Drop for Cleanup {
        fn drop(&mut self) {
            let _ = fs::remove_dir_all(&self.0);
        }
    }
    let _cleanup = Cleanup(dir.clone());
    fs::create_dir(dir.join("src")).unwrap();
    fs::create_dir(dir.join("rust")).unwrap();
    fs::write(dir.join("cott.toml"),"[project]\nname='demo'\nversion='0.1.0'\nsource='src'\n[target.rust]\nsource='rust'\ngenerated='generated/rust'\nruntime_validation='boundary'\n").unwrap();
    let (config, paths, _) = project::load_rust_config_with_paths(&dir).unwrap();
    let metadata = dependencies::load_metadata(&config, &paths).unwrap();
    let record = dependencies::initial_record(&metadata);
    assert_eq!(
        record["packages"]
            .as_array()
            .unwrap()
            .iter()
            .map(|p| p["name"].as_str().unwrap())
            .collect::<Vec<_>>(),
        vec!["pin-project-lite", "tokio"]
    );
    let resolved = dependencies::resolve(&metadata, None).unwrap();
    dependencies::validate_frozen_resolution(&metadata, &resolved).unwrap();
    let stage = dir.join("stage");
    fs::create_dir_all(stage.join("src")).unwrap();
    for (path, bytes) in dependencies::emitted_files(&metadata) {
        let destination = stage.join(path.strip_prefix("rust").unwrap());
        fs::create_dir_all(destination.parent().unwrap()).unwrap();
        fs::write(destination, bytes).unwrap();
    }
    fs::write(
        stage.join("Cargo.lock"),
        dependencies::compiler_lock(&metadata, &resolved).unwrap(),
    )
    .unwrap();
    fs::write(stage.join("src/lib.rs"),"pin_project_lite::pin_project! { pub struct Value { value: usize } }\npub fn run() -> usize { tokio::runtime::Builder::new_current_thread().enable_time().build().unwrap().block_on(async { 7 }) }\n").unwrap();
    let output = Command::new(&cargo)
        .args(["build", "--offline", "--locked"])
        .current_dir(&stage)
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    // Merge a separate user registry crate and a local crate with a nondefault lib name
    // into the same compiler-pinned runtime lock.
    let local = dir.join("local");
    fs::create_dir_all(local.join("src")).unwrap();
    fs::write(
        local.join("Cargo.toml"),
        "[package]\nname='local_dep'\nversion='1.0.0'\nedition='2024'\n[lib]\nname='local_lib'\n",
    )
    .unwrap();
    fs::write(local.join("src/lib.rs"), "pub fn value()->usize{9}\n").unwrap();
    let build = dir.join("build-only");
    fs::create_dir_all(build.join("src")).unwrap();
    fs::write(
        build.join("Cargo.toml"),
        "[package]\nname='build_dep'\nversion='1.0.0'\nedition='2024'\n[features]\nmarker=[]\n",
    )
    .unwrap();
    fs::write(build.join("src/lib.rs"), "pub fn build_value()->usize{1}\n").unwrap();
    let meta = dir.join("metadata");
    fs::create_dir(&meta).unwrap();
    fs::write(meta.join("Cargo.toml"),"[package]\nname='demo'\nversion='0.1.0'\nedition='2024'\n[lib]\npath='../rust/lib.rs'\n[dependencies]\nnumber_format={package='itoa',version='=1.0.18'}\nlocal_dep={path='../local',version='=1.0.0'}\n[build-dependencies]\nbuild_dep={path='../build-only',version='1'}\n[features]\ndefault=['build_dep/marker']\n").unwrap();
    fs::write(dir.join("rust/lib.rs"), "").unwrap();
    let lock = Command::new(&cargo)
        .args(["generate-lockfile", "--offline", "--manifest-path"])
        .arg(meta.join("Cargo.toml"))
        .output()
        .unwrap();
    assert!(
        lock.status.success(),
        "{}",
        String::from_utf8_lossy(&lock.stderr)
    );
    fs::write(dir.join("cott.toml"),"[project]\nname='demo'\nversion='0.1.0'\nsource='src'\n[target.rust]\nsource='rust'\ngenerated='generated/rust'\nruntime_validation='boundary'\ncargo_manifest='metadata/Cargo.toml'\nlockfile='metadata/Cargo.lock'\n").unwrap();
    let (config, paths, _) = project::load_rust_config_with_paths(&dir).unwrap();
    let metadata = dependencies::load_metadata(&config, &paths).unwrap();
    assert!(dependencies::runtime_package_names(&metadata).contains("local_lib"));
    assert!(!dependencies::runtime_package_names(&metadata).contains("build_dep"));
    assert!(dependencies::runtime_package_names(&metadata).contains("number_format"));
    assert!(!dependencies::runtime_package_names(&metadata).contains("itoa"));
    let record = dependencies::initial_record(&metadata);
    assert_eq!(
        record["packages"]
            .as_array()
            .unwrap()
            .iter()
            .map(|p| p["name"].as_str().unwrap())
            .collect::<Vec<_>>(),
        vec![
            "build_dep",
            "itoa",
            "local_dep",
            "pin-project-lite",
            "tokio"
        ]
    );
    assert_eq!(record["packages"][0]["runtime"], false);
    let resolved = dependencies::resolve(&metadata, None).unwrap();
    for (path, bytes) in dependencies::emitted_files(&metadata) {
        let destination = stage.join(path.strip_prefix("rust").unwrap());
        fs::create_dir_all(destination.parent().unwrap()).unwrap();
        fs::write(destination, bytes).unwrap();
    }
    fs::write(
        stage.join("Cargo.lock"),
        dependencies::compiler_lock(&metadata, &resolved).unwrap(),
    )
    .unwrap();
    fs::write(stage.join("src/lib.rs"),"pub fn run()->usize {tokio::runtime::Builder::new_current_thread().build().unwrap().block_on(async { let mut buffer=number_format::Buffer::new(); buffer.format(local_lib::value()).parse().unwrap() })}\n").unwrap();
    let output = Command::new(&cargo)
        .args(["build", "--offline", "--locked"])
        .current_dir(&stage)
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
}
