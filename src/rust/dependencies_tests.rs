use super::*;
use flate2::{Compression, write::GzEncoder};
use std::io::Write;
use std::sync::atomic::{AtomicUsize, Ordering};
static NEXT: AtomicUsize = AtomicUsize::new(0);
struct Temp(PathBuf);
impl Temp {
    fn new() -> Self {
        let p = std::env::temp_dir().join(format!(
            "cott-cargo-deps-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir(&p).unwrap();
        Self(p)
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.0);
    }
}
fn archive(members: &[(&str, &[u8], tar::EntryType)]) -> Vec<u8> {
    let mut tar = Vec::new();
    for (path, data, kind) in members {
        let mut h = tar::Header::new_gnu();
        h.set_size(data.len() as u64);
        h.set_mode(0o644);
        h.set_entry_type(*kind);
        // Raw names deliberately permit hostile traversal fixtures rejected by the reader.
        h.as_mut_bytes()[..100].fill(0);
        h.as_mut_bytes()[..path.len()].copy_from_slice(path.as_bytes());
        h.set_cksum();
        tar.extend_from_slice(h.as_bytes());
        tar.extend_from_slice(data);
        tar.resize(tar.len().next_multiple_of(512), 0);
    }
    tar.resize(tar.len() + 1024, 0);
    let mut gz = GzEncoder::new(Vec::new(), Compression::default());
    gz.write_all(&tar).unwrap();
    gz.finish().unwrap()
}
fn metadata(root: &Path, checksum: &str) -> PackageMetadata {
    PackageMetadata {
        name: "demo".into(),
        version: "0.1.0".into(),
        root: root.into(),
        manifest: parse(b"[package]\nname='demo'\nversion='0.1.0'\n[dependencies]\nuser='1'\n")
            .unwrap(),
        locked: BTreeMap::from([(
            "user".into(),
            Locked {
                version: "1.0.0".into(),
                checksum: Some(checksum.into()),
                path: None,
                dependencies: vec![],
            },
        )]),
        inputs: BTreeMap::new(),
        runtime_package_names: BTreeSet::new(),
        production_packages: BTreeSet::new(),
        frozen: ResolvedDependencies {
            packages: vec![],
            record: Value::Null,
            artifacts: BTreeMap::new(),
            package_trees: BTreeMap::new(),
        },
    }
}
fn registry(temp: &Temp) -> (PackageMetadata, PathBuf) {
    let bytes = archive(&[
        (
            "user-1.0.0/Cargo.toml",
            b"[package]\nname='user'\nversion='1.0.0'\n",
            tar::EntryType::Regular,
        ),
        (
            "user-1.0.0/src/lib.rs",
            b"pub fn value()->u32{7}",
            tar::EntryType::Regular,
        ),
    ]);
    let cache = temp.0.join("cache");
    let dir = cache.join("registry/cache/index.crates.io-fixture");
    fs::create_dir_all(&dir).unwrap();
    fs::write(dir.join("user-1.0.0.crate"), &bytes).unwrap();
    (metadata(&temp.0, &sha256_hex(&bytes)), cache)
}
#[test]
fn archive_rejects_traversal_links_duplicates_and_file_directory_conflicts() {
    for members in [
        vec![(
            "user-1.0.0/../escape",
            b"x".as_slice(),
            tar::EntryType::Regular,
        )],
        vec![("user-1.0.0/link", b"".as_slice(), tar::EntryType::Symlink)],
        vec![
            ("user-1.0.0/x", b"a".as_slice(), tar::EntryType::Regular),
            ("user-1.0.0/x", b"b".as_slice(), tar::EntryType::Regular),
        ],
        vec![
            ("user-1.0.0/x/y", b"a".as_slice(), tar::EntryType::Regular),
            ("user-1.0.0/x", b"b".as_slice(), tar::EntryType::Regular),
        ],
    ] {
        assert!(archive_tree(&archive(&members), "user-1.0.0").is_err());
    }
}
#[test]
fn authenticated_registry_vendor_checksums_and_closed_record_material() {
    let temp = Temp::new();
    let (m, c) = registry(&temp);
    let r = materialize(&m, &c).unwrap();
    assert_eq!(r.packages[0].name, "user");
    assert_eq!(
        r.packages[0].source_identity,
        format!(
            "{REGISTRY}#sha256:{}",
            m.locked["user"].checksum.as_ref().unwrap()
        )
    );
    let check: Value = serde_json::from_slice(
        &r.artifacts[Path::new("rust/vendor/user-1.0.0/.cargo-checksum.json")],
    )
    .unwrap();
    assert_eq!(
        check["files"]["src/lib.rs"],
        sha256_hex(b"pub fn value()->u32{7}")
    );
}
#[test]
fn missing_archive_diagnostic_and_checksum_mismatch() {
    let temp = Temp::new();
    let (mut m, c) = registry(&temp);
    m.locked.get_mut("user").unwrap().checksum = Some("0".repeat(64));
    assert!(
        materialize(&m, &c)
            .unwrap_err()
            .contains("checksum mismatch")
    );
    let e = materialize(&m, &temp.0.join("missing")).unwrap_err();
    assert!(e.contains("user-1.0.0.crate") && e.contains("cargo fetch") && e.contains(REGISTRY));
}
#[test]
fn extracted_cache_tamper_and_frozen_path_tamper_rejected() {
    let temp = Temp::new();
    let (mut m, c) = registry(&temp);
    let extracted = c.join("registry/src/index.crates.io-fixture/user-1.0.0");
    fs::create_dir_all(&extracted).unwrap();
    fs::write(extracted.join("Cargo.toml"), "tampered").unwrap();
    assert!(materialize(&m, &c).unwrap_err().contains("tampered"));
    fs::remove_dir_all(extracted).unwrap();
    let path = temp.0.join("local");
    fs::create_dir(&path).unwrap();
    fs::write(
        path.join("Cargo.toml"),
        "[package]\nname='user'\nversion='1.0.0'\n",
    )
    .unwrap();
    let p = m.locked.get_mut("user").unwrap();
    p.checksum = None;
    p.path = Some(path.clone());
    m.frozen = materialize(&m, &c).unwrap();
    fs::write(path.join("Cargo.toml"), "changed").unwrap();
    assert!(resolve(&m, Some(&c)).unwrap_err().contains("changed"));
}
#[test]
fn declaration_requirements_and_overrides_are_exact() {
    let temp = Temp::new();
    let (m, _) = registry(&temp);
    for req in ["2", "=1.0.1", "1.0.0+build", "1.0.0-beta"] {
        let v = parse(format!("[dependencies]\nuser={req:?}\n").as_bytes()).unwrap();
        assert!(validate_declarations(&v, &m.locked, None).is_err());
    }
    for key in ["patch", "replace", "workspace", "source"] {
        assert!(reject_overrides(&parse(format!("[{key}]\n").as_bytes()).unwrap()).is_err());
    }
    let v = parse(b"[dependencies.user]\ngit='https://example.test/repo'\nversion='1'\n").unwrap();
    assert!(validate_declarations(&v, &m.locked, None).is_err());
}
#[test]
fn production_import_authority_excludes_build_and_dev() {
    let temp = Temp::new();
    let (mut m, c) = registry(&temp);
    m.manifest=parse(b"[package]\nname='demo'\nversion='0.1.0'\n[build-dependencies]\nuser='1'\n[dev-dependencies]\nuser='1'\n").unwrap();
    let r = materialize(&m, &c).unwrap();
    let production = production_closure(&m, &r).unwrap();
    assert!(!production.contains("user"));
}
#[test]
fn path_escape_and_symlinks_are_rejected() {
    let temp = Temp::new();
    let outside = Temp::new();
    assert!(canonical_local(&outside.0, &temp.0).is_err());
    std::os::unix::fs::symlink(&outside.0, temp.0.join("link")).unwrap();
    assert!(canonical_local(&temp.0.join("link"), &temp.0).is_err());
    assert!(read_tree(&temp.0).is_err());
}

#[test]
fn emitted_dependency_record_matches_canonical_publication_bytes() {
    let temp = Temp::new();
    let (mut metadata, cache) = registry(&temp);
    let mut resolved = materialize(&metadata, &cache).unwrap();
    resolved.record = json!({"schema_version":1,"cargo_manifest_hash":digest(b"manifest"),"lockfile_hash":digest(b"lock"),"packages":[{"name":"user","version":"1.0.0","source":"registry","source_identity":resolved.packages[0].source_identity,"content_hash":resolved.packages[0].content_hash,"dependencies":[],"runtime":true}]});
    resolved.artifacts.insert(
        "rust/dependencies.json".into(),
        json_bytes(&resolved.record).unwrap(),
    );
    metadata.frozen = resolved;
    let mut expected = serde_json::to_vec(&initial_record(&metadata)).unwrap();
    expected.push(b'\n');
    assert_eq!(
        emitted_files(&metadata)[Path::new("rust/dependencies.json")],
        expected
    );
    assert_eq!(
        resolve(&metadata, Some(&cache)).unwrap().artifacts[Path::new("rust/dependencies.json")],
        expected
    );
}
