use std::collections::BTreeMap;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::sync::atomic::{AtomicU64, Ordering};

use flate2::Compression;
use flate2::write::GzEncoder;
use tar::{Builder, EntryType, Header};

#[path = "support/snapshot.rs"]
mod snapshot_wire;

static NEXT_TEMP: AtomicU64 = AtomicU64::new(0);

struct TempDir {
    path: PathBuf,
}

impl TempDir {
    fn new(label: &str) -> Self {
        let mut number = NEXT_TEMP.fetch_add(1, Ordering::Relaxed);
        loop {
            let path = std::env::temp_dir().join(format!(
                "cott-dart-dependencies-{label}-{}-{number}",
                std::process::id()
            ));
            match fs::create_dir(&path) {
                Ok(()) => return Self { path },
                Err(error) if error.kind() == io::ErrorKind::AlreadyExists => number += 1,
                Err(error) => panic!("create Dart dependency fixture: {error}"),
            }
        }
    }
}

impl Drop for TempDir {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.path);
    }
}

struct Fixture {
    temp: TempDir,
    cache: PathBuf,
}

impl Fixture {
    fn new(label: &str) -> Self {
        Self::with_sdk(label, "missing-dart")
    }

    fn with_sdk(label: &str, sdk: &str) -> Self {
        let temp = TempDir::new(label);
        fs::create_dir_all(temp.path.join("src/demo")).expect("Cott source directory");
        fs::create_dir(temp.path.join("dart")).expect("Dart source directory");
        fs::create_dir(temp.path.join("dart_package")).expect("Dart metadata directory");
        let cache = temp.path.join("pub-cache");
        fs::create_dir(&cache).expect("PUB_CACHE directory");
        fs::create_dir(temp.path.join("home")).expect("isolated home");
        fs::write(
            temp.path.join("cott.toml"),
            format!(
                r#"[project]
name = "demo"
version = "0.1.0"
source = "src"

[target.dart]
source = "dart"
generated = "generated/dart"
sdk = {sdk:?}
runtime_validation = "boundary"
pubspec = "dart_package/pubspec.yaml"
lockfile = "dart_package/pubspec.lock"
"#
            ),
        )
        .expect("Dart manifest");
        fs::write(temp.path.join("src/demo/main.cott"), "module demo.main\n").expect("Cott source");
        Self { temp, cache }
    }

    fn write_metadata(&self, dependencies: &str, lock_entries: &str) {
        fs::write(
            self.temp.path.join("dart_package/pubspec.yaml"),
            format!(
                "name: demo\nversion: 0.1.0\nenvironment:\n  sdk: '>=3.13.3 <4.0.0'\ndependencies:\n{dependencies}"
            ),
        )
        .expect("Dart pubspec");
        fs::write(
            self.temp.path.join("dart_package/pubspec.lock"),
            format!("packages:\n{lock_entries}sdks:\n  dart: '>=3.13.3 <4.0.0'\n"),
        )
        .expect("Dart lockfile");
    }

    fn run(&self, arguments: &[&str]) -> Output {
        Command::new(env!("CARGO_BIN_EXE_cott"))
            .args(arguments)
            .args(["--project"])
            .arg(&self.temp.path)
            .env_clear()
            .env("HOME", self.temp.path.join("home"))
            .env("PUB_CACHE", &self.cache)
            .output()
            .expect("cott should run")
    }

    fn path(&self) -> &Path {
        &self.temp.path
    }

    fn install_path_package(&self, relative: &str, name: &str, version: &str, dependencies: &str) {
        let root = self.temp.path.join(relative);
        fs::create_dir_all(root.join("lib")).expect("path package library directory");
        fs::write(
            root.join("pubspec.yaml"),
            package_pubspec(name, version, dependencies),
        )
        .expect("path package pubspec");
        fs::write(
            root.join("lib").join(format!("{name}.dart")),
            format!("String {name}Value = {name:?};\n"),
        )
        .expect("path package library");
    }

    fn install_hosted_package(&self, name: &str, version: &str, dependencies: &str) -> String {
        let files = package_files(name, version, dependencies);
        let archive = regular_archive(&files);
        self.write_archive(name, version, &archive);
        self.write_extracted(name, version, &files);
        cott::hash::sha256_hex(&archive)
    }

    fn write_archive(&self, name: &str, version: &str, bytes: &[u8]) {
        let directory = self.cache.join("hosted-archives/pub.dev");
        fs::create_dir_all(&directory).expect("hosted archive directory");
        fs::write(directory.join(format!("{name}-{version}.tar.gz")), bytes)
            .expect("hosted archive");
    }

    fn write_extracted(&self, name: &str, version: &str, files: &BTreeMap<String, Vec<u8>>) {
        let root = self
            .cache
            .join("hosted/pub.dev")
            .join(format!("{name}-{version}"));
        for (relative, bytes) in files {
            let path = root.join(relative);
            fs::create_dir_all(path.parent().expect("package member parent"))
                .expect("extracted package directory");
            fs::write(path, bytes).expect("extracted package member");
        }
    }
}

fn package_pubspec(name: &str, version: &str, dependencies: &str) -> Vec<u8> {
    format!(
        "name: {name}\nversion: {version}\nenvironment:\n  sdk: '>=3.13.3 <4.0.0'\n{dependencies}"
    )
    .into_bytes()
}

fn package_files(name: &str, version: &str, dependencies: &str) -> BTreeMap<String, Vec<u8>> {
    BTreeMap::from([
        (
            "pubspec.yaml".to_owned(),
            package_pubspec(name, version, dependencies),
        ),
        (
            format!("lib/{name}.dart"),
            format!("String {name}Value = {name:?};\n").into_bytes(),
        ),
        ("LICENSE".to_owned(), b"fixture license\n".to_vec()),
    ])
}

fn append_file(builder: &mut Builder<GzEncoder<Vec<u8>>>, path: &str, bytes: &[u8]) {
    let mut header = Header::new_gnu();
    header.set_size(bytes.len() as u64);
    header.set_mode(0o644);
    header.set_cksum();
    builder
        .append_data(&mut header, path, bytes)
        .expect("append archive member");
}

fn finish_archive(builder: Builder<GzEncoder<Vec<u8>>>) -> Vec<u8> {
    builder
        .into_inner()
        .expect("finish tar archive")
        .finish()
        .expect("finish gzip archive")
}

fn regular_archive(files: &BTreeMap<String, Vec<u8>>) -> Vec<u8> {
    let mut builder = Builder::new(GzEncoder::new(Vec::new(), Compression::default()));
    for (path, bytes) in files {
        append_file(&mut builder, path, bytes);
    }
    finish_archive(builder)
}

fn link_archive(files: &BTreeMap<String, Vec<u8>>) -> Vec<u8> {
    let mut builder = Builder::new(GzEncoder::new(Vec::new(), Compression::default()));
    for (path, bytes) in files {
        append_file(&mut builder, path, bytes);
    }
    let mut header = Header::new_gnu();
    header.set_entry_type(EntryType::Symlink);
    header.set_size(0);
    header.set_mode(0o777);
    header.set_path("lib/linked.dart").expect("link path");
    header
        .set_link_name("target.dart")
        .expect("archive link target");
    header.set_cksum();
    builder
        .append(&header, io::empty())
        .expect("append archive link");
    finish_archive(builder)
}

fn duplicate_archive(files: &BTreeMap<String, Vec<u8>>) -> Vec<u8> {
    let mut builder = Builder::new(GzEncoder::new(Vec::new(), Compression::default()));
    for (path, bytes) in files {
        append_file(&mut builder, path, bytes);
    }
    append_file(&mut builder, "lib/repeated.dart", b"const value = 1;\n");
    append_file(&mut builder, "lib/repeated.dart", b"const value = 2;\n");
    finish_archive(builder)
}

fn hosted_entry(name: &str, version: &str, digest: &str, ownership: &str) -> String {
    format!(
        "  {name}:\n    dependency: {ownership}\n    description:\n      name: {name}\n      sha256: '{digest}'\n      url: https://pub.dev\n    source: hosted\n    version: {version}\n"
    )
}

fn path_entry(name: &str, version: &str, path: &str, ownership: &str) -> String {
    format!(
        "  {name}:\n    dependency: {ownership}\n    description:\n      path: {path}\n      relative: true\n    source: path\n    version: {version}\n"
    )
}

fn stderr(output: &Output) -> String {
    String::from_utf8_lossy(&output.stderr).into_owned()
}

fn assert_rejected(output: Output, expected: &str) {
    assert_eq!(output.status.code(), Some(4), "{}", stderr(&output));
    assert!(
        stderr(&output).contains(expected),
        "expected {expected:?} in {}",
        stderr(&output)
    );
}

#[test]
fn edited_extracted_hosted_cache_is_rejected_despite_unchanged_sidecar() {
    let fixture = Fixture::new("edited-cache");
    let digest = fixture.install_hosted_package("helper", "1.0.0", "");
    let sidecar = fixture.cache.join("hosted-hashes/pub.dev");
    fs::create_dir_all(&sidecar).expect("obsolete sidecar directory");
    fs::write(sidecar.join("helper-1.0.0.sha256"), format!("{digest}\n"))
        .expect("unchanged SDK sidecar");
    fs::write(
        fixture
            .cache
            .join("hosted/pub.dev/helper-1.0.0/lib/helper.dart"),
        "String helperValue = 'tampered';\n",
    )
    .expect("tampered extracted member");
    fixture.write_metadata(
        "  helper: ^1.0.0\n",
        &hosted_entry("helper", "1.0.0", &digest, "direct main"),
    );

    assert_rejected(
        fixture.run(&["emit", "dart"]),
        "disagrees with authenticated archive",
    );
}

#[test]
fn missing_hosted_archive_reports_required_path_and_locked_identity() {
    let fixture = Fixture::new("missing-archive");
    let digest = "a".repeat(64);
    fixture.write_metadata(
        "  helper: 1.0.0\n",
        &hosted_entry("helper", "1.0.0", &digest, "direct main"),
    );

    let output = fixture.run(&["emit", "dart"]);
    assert_eq!(output.status.code(), Some(4), "{}", stderr(&output));
    let error = stderr(&output);
    assert!(error.contains("hosted-archives/pub.dev/helper-1.0.0.tar.gz"));
    assert!(error.contains(&format!("https://pub.dev#sha256:{digest}")));
}

#[test]
fn hosted_archive_hash_mismatch_is_rejected_from_compressed_bytes() {
    let fixture = Fixture::new("archive-hash");
    let actual = fixture.install_hosted_package("helper", "1.0.0", "");
    let required = if actual.starts_with('0') {
        "1".repeat(64)
    } else {
        "0".repeat(64)
    };
    fixture.write_metadata(
        "  helper: 1.0.0\n",
        &hosted_entry("helper", "1.0.0", &required, "direct main"),
    );

    let output = fixture.run(&["emit", "dart"]);
    assert_rejected(output, "hosted archive hash mismatch");
}

#[test]
fn hosted_archives_reject_links_and_duplicate_members() {
    for (label, archive, expected) in [
        (
            "archive-link",
            link_archive(&package_files("helper", "1.0.0", "")),
            "link or special member",
        ),
        (
            "archive-duplicate",
            duplicate_archive(&package_files("helper", "1.0.0", "")),
            "duplicates member",
        ),
    ] {
        let fixture = Fixture::new(label);
        let digest = cott::hash::sha256_hex(&archive);
        fixture.write_archive("helper", "1.0.0", &archive);
        fixture.write_metadata(
            "  helper: 1.0.0\n",
            &hosted_entry("helper", "1.0.0", &digest, "direct main"),
        );
        assert_rejected(fixture.run(&["emit", "dart"]), expected);
    }
}

#[test]
fn root_dependency_source_kind_and_path_substitution_are_rejected() {
    let path_for_hosted = Fixture::new("declared-hosted-locked-path");
    path_for_hosted.install_path_package("packages/helper", "helper", "1.0.0", "");
    path_for_hosted.write_metadata(
        "  helper: 1.0.0\n",
        &path_entry("helper", "1.0.0", "../packages/helper", "direct main"),
    );
    assert_rejected(
        path_for_hosted.run(&["emit", "dart"]),
        "declares hosted dependency `helper`, but pubspec.lock selects a path source",
    );

    let hosted_for_path = Fixture::new("declared-path-locked-hosted");
    hosted_for_path.install_path_package("packages/helper", "helper", "1.0.0", "");
    hosted_for_path.write_metadata(
        "  helper:\n    path: ../packages/helper\n",
        &hosted_entry("helper", "1.0.0", &"b".repeat(64), "direct main"),
    );
    assert_rejected(
        hosted_for_path.run(&["emit", "dart"]),
        "declares path dependency `helper`, but pubspec.lock selects a hosted source",
    );

    let substituted = Fixture::new("substituted-root-path");
    substituted.install_path_package("packages/approved", "helper", "1.0.0", "");
    substituted.install_path_package("packages/other", "helper", "1.0.0", "");
    substituted.write_metadata(
        "  helper:\n    path: ../packages/approved\n",
        &path_entry("helper", "1.0.0", "../packages/other", "direct main"),
    );
    assert_rejected(
        substituted.run(&["emit", "dart"]),
        "declares path dependency `helper`",
    );
}

#[test]
fn hosted_registry_and_package_name_substitution_are_rejected() {
    let registry = Fixture::new("registry-substitution");
    registry.write_metadata(
        "  helper:\n    hosted: https://packages.example\n    version: 1.0.0\n",
        &hosted_entry("helper", "1.0.0", &"c".repeat(64), "direct main"),
    );
    assert_rejected(
        registry.run(&["emit", "dart"]),
        "pubspec.lock selects `https://pub.dev`",
    );

    let name = Fixture::new("name-substitution");
    name.write_metadata(
        "  helper:\n    hosted:\n      name: other\n      url: https://pub.dev\n    version: 1.0.0\n",
        &hosted_entry("helper", "1.0.0", &"d".repeat(64), "direct main"),
    );
    assert_rejected(
        name.run(&["emit", "dart"]),
        "substitutes registry package name `other`",
    );
}

#[test]
fn transitive_path_substitution_is_resolved_from_declaring_package() {
    let fixture = Fixture::new("transitive-path-substitution");
    fixture.install_path_package(
        "packages/a",
        "a",
        "1.0.0",
        "dependencies:\n  b:\n    path: ../approved_b\n",
    );
    fixture.install_path_package("packages/approved_b", "b", "1.0.0", "");
    fixture.install_path_package("packages/other_b", "b", "1.0.0", "");
    fixture.write_metadata(
        "  a:\n    path: ../packages/a\n",
        &(path_entry("a", "1.0.0", "../packages/a", "direct main")
            + &path_entry("b", "1.0.0", "../packages/other_b", "transitive")),
    );

    assert_rejected(
        fixture.run(&["emit", "dart"]),
        "locked Dart package `a` declares path dependency `b`",
    );
}

#[test]
fn release_constraints_do_not_admit_prereleases_or_different_builds() {
    for (label, constraint, version) in [
        ("exact-prerelease", "1.0.0", "1.0.0-dev.1"),
        ("caret-prerelease", "^1.0.0", "1.0.0-dev.1"),
        ("exact-build", "1.0.0+1", "1.0.0+2"),
    ] {
        let fixture = Fixture::new(label);
        fixture.write_metadata(
            &format!("  helper: '{constraint}'\n"),
            &hosted_entry("helper", version, &"e".repeat(64), "direct main"),
        );
        assert_rejected(fixture.run(&["emit", "dart"]), "does not satisfy");
    }
}

#[test]
fn prerelease_and_build_ranges_use_full_pub_version_ordering() {
    let fixture = Fixture::new("full-version-ordering");
    let prerelease = fixture.install_hosted_package("prerelease", "1.0.0-dev.3", "");
    let built = fixture.install_hosted_package("built", "1.0.0+2", "");
    fixture.write_metadata(
        "  prerelease: '>=1.0.0-dev.2 <1.0.0'\n  built: '>1.0.0+1 <=1.0.0+3'\n",
        &(hosted_entry("prerelease", "1.0.0-dev.3", &prerelease, "direct main")
            + &hosted_entry("built", "1.0.0+2", &built, "direct main")),
    );

    let output = fixture.run(&["emit", "dart"]);
    assert!(output.status.success(), "{}", stderr(&output));
    let generation = snapshot_wire::read(
        &fs::read(fixture.path().join("generated/generation.json"))
            .expect("Dart generation record"),
    );
    let packages = generation["current"]["dependencies"]["packages"]
        .as_array()
        .expect("dependency packages");
    assert!(
        packages
            .iter()
            .any(|package| package["version"] == "1.0.0-dev.3")
    );
    assert!(
        packages
            .iter()
            .any(|package| package["version"] == "1.0.0+2")
    );
}

fn mixed_closure_fixture(label: &str, sdk: &str) -> Fixture {
    let fixture = Fixture::with_sdk(label, sdk);
    let mut hosted_files = package_files("hosted_b", "2.0.0+1", "");
    hosted_files.insert(
        "lib/hosted_b.dart".to_owned(),
        b"int adjust(int value) => value + 1;\n".to_vec(),
    );
    let hosted_archive = regular_archive(&hosted_files);
    fixture.write_archive("hosted_b", "2.0.0+1", &hosted_archive);
    fixture.write_extracted("hosted_b", "2.0.0+1", &hosted_files);
    let hosted_digest = cott::hash::sha256_hex(&hosted_archive);
    fixture.install_path_package(
        "packages/path_a",
        "path_a",
        "1.0.0",
        "dependencies:\n  hosted_b: ^2.0.0\n",
    );
    fs::write(
        fixture.path().join("packages/path_a/lib/path_a.dart"),
        "import 'package:hosted_b/hosted_b.dart' as hosted_b;\n\nint adjust(int value) => hosted_b.adjust(value) + 1;\n",
    )
    .expect("path package library");
    fixture.write_metadata(
        "  path_a:\n    path: ../packages/path_a\n",
        &(path_entry("path_a", "1.0.0", "../packages/path_a", "direct main")
            + &hosted_entry("hosted_b", "2.0.0+1", &hosted_digest, "transitive")),
    );
    fs::write(
        fixture.path().join("src/demo/main.cott"),
        "module demo.main\n\nfn adjust(value: I32) -> I32:\n    requires value >= 0\n    requires value < 100\n    ensures result == value + 2\n",
    )
    .expect("dependency-backed Cott callable");
    let manifest_path = fixture.path().join("cott.toml");
    let manifest = fs::read_to_string(&manifest_path).expect("Dart manifest");
    fs::write(
        manifest_path,
        format!(
            "{manifest}\n[target.dart.implementations]\n\"demo.main.adjust\" = \"bindings/adjust.dart:_adjust\"\n"
        ),
    )
    .expect("dependency-backed manifest binding");
    fs::create_dir_all(fixture.path().join("dart/bindings")).expect("Dart binding directory");
    fs::write(
        fixture.path().join("dart/bindings/adjust.dart"),
        "import 'package:path_a/path_a.dart' as path_a;\n\nint _adjust(int value) {\n  return path_a.adjust(value);\n}\n",
    )
    .expect("dependency-backed Dart binding");
    fixture
}

#[test]
fn authenticated_hosted_and_project_path_closure_has_portable_identity() {
    let fixture = mixed_closure_fixture("portable-closure", "missing-dart");
    let output = fixture.run(&["emit", "dart"]);
    assert!(output.status.success(), "{}", stderr(&output));
    let generation = snapshot_wire::read(
        &fs::read(fixture.path().join("generated/generation.json"))
            .expect("Dart generation record"),
    );
    let packages = generation["current"]["dependencies"]["packages"]
        .as_array()
        .expect("dependency packages");
    let path_package = packages
        .iter()
        .find(|package| package["name"] == "path_a")
        .expect("path package");
    assert_eq!(path_package["source"], "path");
    assert_eq!(path_package["source_identity"], "packages/path_a");
    let hosted_package = packages
        .iter()
        .find(|package| package["name"] == "hosted_b")
        .expect("hosted package");
    assert_eq!(hosted_package["source"], "hosted");
    assert!(
        hosted_package["source_identity"]
            .as_str()
            .is_some_and(|identity| identity.starts_with("https://pub.dev#sha256:"))
    );
    assert!(
        !generation
            .to_string()
            .contains(fixture.cache.to_string_lossy().as_ref())
    );
}

#[test]
#[ignore = "requires COTT_DART and exercises native offline pub vendoring"]
fn authenticated_hosted_and_path_closure_vendors_for_native_verification() {
    let sdk = std::env::var("COTT_DART").expect("COTT_DART must name the Dart executable");
    let fixture = mixed_closure_fixture("native-vendoring", &sdk);
    let emitted = fixture.run(&["emit", "dart"]);
    assert!(emitted.status.success(), "{}", stderr(&emitted));
    let verified = fixture.run(&["verify"]);
    assert!(verified.status.success(), "{}", stderr(&verified));
    let generation = snapshot_wire::read(
        &fs::read(fixture.path().join("generated/generation.json"))
            .expect("verified generation record"),
    );
    let clauses = generation["current"]["semantic_coverage"]["clauses"]
        .as_array()
        .expect("semantic clauses")
        .iter()
        .filter(|clause| {
            clause["symbol"] == "demo.main.adjust"
                && clause["clause_id"]
                    .as_str()
                    .is_some_and(|id| id.starts_with("ensures:"))
        })
        .collect::<Vec<_>>();
    assert_eq!(clauses.len(), 1, "dependency-backed ensures inventory");
    assert!(
        clauses[0]["evidence"].as_array().is_some_and(|evidence| {
            evidence
                .iter()
                .any(|entry| entry["status"] == "passed" && entry["positive_applicable"] == true)
        }),
        "the dependency-backed ensures clause must have positive applicable runtime evidence"
    );
    assert!(
        generation["current"]["verification"]["contract_tests"]["cases"]
            .as_array()
            .expect("contract runner cases")
            .iter()
            .any(|case| case["symbol"] == "demo.main.adjust" && case["status"] == "passed"),
        "the public dependency-backed callable must execute successfully"
    );
    assert!(
        fixture
            .path()
            .join("generated/dart/vendor/path_a/lib/path_a.dart")
            .is_file()
    );
    assert!(
        fixture
            .path()
            .join("generated/dart/vendor/hosted_b/lib/hosted_b.dart")
            .is_file()
    );
}
