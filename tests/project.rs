use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

use cott::project::{discover_sources, load_project};

static NEXT_TEMP_DIR: AtomicU64 = AtomicU64::new(0);

struct TempDir {
    path: PathBuf,
}

impl TempDir {
    fn new() -> Self {
        let mut number = NEXT_TEMP_DIR.fetch_add(1, Ordering::Relaxed);
        loop {
            let path = std::env::temp_dir().join(format!(
                "cott-project-tests-{}-{}",
                std::process::id(),
                number
            ));
            match fs::create_dir(&path) {
                Ok(()) => return Self { path },
                Err(error) if error.kind() == io::ErrorKind::AlreadyExists => number += 1,
                Err(error) => panic!("failed to create temporary directory: {error}"),
            }
        }
    }
}

impl Drop for TempDir {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.path);
    }
}

const VALID_MANIFEST: &str = r#"
[project]
name = "demo"
source = "src"

[target.python]
generated = "generated/python"
entry = "module.function"
"#;

fn manifest(root: &Path, contents: &str) {
    fs::write(root.join("cott.toml"), contents).expect("manifest should be writable");
}

fn valid_project() -> TempDir {
    let temp = TempDir::new();
    manifest(&temp.path, VALID_MANIFEST);
    fs::create_dir_all(temp.path.join("src")).expect("source directory should be writable");
    temp
}

#[test]
fn loads_the_closed_manifest_and_derives_project_paths() {
    let temp = valid_project();
    let project = load_project(&temp.path).expect("valid manifest should load");

    assert_eq!(project.root, temp.path);
    assert_eq!(project.name, "demo");
    assert_eq!(project.source_dir, temp.path.join("src"));
    assert_eq!(project.generated_dir, temp.path.join("generated/python"));
    assert_eq!(
        project.implementation_dir,
        temp.path.join("python/_cott_impl")
    );
    assert_eq!(project.entry, "module.function");
}

#[test]
fn discovers_nested_sources_in_lexical_order() {
    let temp = valid_project();
    fs::create_dir_all(temp.path.join("src/a")).expect("source directory should be writable");
    fs::create_dir_all(temp.path.join("src/b")).expect("source directory should be writable");
    for (path, contents) in [
        ("src/z.cott", "module z\n"),
        ("src/a/second.cott", "module a.second\n"),
        ("src/a/first.cott", "module a.first\n"),
        ("src/b/only.cott", "module b.only\n"),
    ] {
        fs::write(temp.path.join(path), contents).expect("source should be writable");
    }
    fs::write(temp.path.join("src/ignored.txt"), "not a source\n")
        .expect("non-source should be writable");

    let project = load_project(&temp.path).expect("valid manifest should load");
    let sources = discover_sources(&project).expect("source files should be discovered");

    assert_eq!(
        sources
            .iter()
            .map(|source| source.path.clone())
            .collect::<Vec<_>>(),
        vec![
            PathBuf::from("a/first.cott"),
            PathBuf::from("a/second.cott"),
            PathBuf::from("b/only.cott"),
            PathBuf::from("z.cott"),
        ]
    );
}

#[test]
fn rejects_unknown_manifest_fields() {
    let temp = valid_project();
    manifest(
        &temp.path,
        r#"
[project]
name = "demo"
source = "src"
unknown = true

[target.python]
generated = "generated/python"
entry = "module.function"
"#,
    );

    assert!(load_project(&temp.path).is_err());
}

#[test]
fn rejects_missing_manifest_fields() {
    let temp = valid_project();
    manifest(
        &temp.path,
        r#"
[project]
name = "demo"

[target.python]
generated = "generated/python"
entry = "module.function"
"#,
    );

    assert!(load_project(&temp.path).is_err());
}

#[test]
fn rejects_duplicate_manifest_fields() {
    let temp = valid_project();
    manifest(
        &temp.path,
        r#"
[project]
name = "demo"
name = "again"
source = "src"

[target.python]
generated = "generated/python"
entry = "module.function"
"#,
    );

    assert!(load_project(&temp.path).is_err());
}

#[test]
fn rejects_unsafe_and_overlapping_paths() {
    for source in ["", ".", "..", "../src", "/absolute/src"] {
        let temp = valid_project();
        let contents = format!(
            "[project]\nname = \"demo\"\nsource = \"{source}\"\n\n[target.python]\ngenerated = \"generated/python\"\nentry = \"module.function\"\n"
        );
        manifest(&temp.path, &contents);
        assert!(load_project(&temp.path).is_err(), "source path: {source:?}");
    }

    for generated in ["", ".", "..", "../generated", "/absolute/generated"] {
        let temp = valid_project();
        let contents = format!(
            "[project]\nname = \"demo\"\nsource = \"src\"\n\n[target.python]\ngenerated = \"{generated}\"\nentry = \"module.function\"\n"
        );
        manifest(&temp.path, &contents);
        assert!(
            load_project(&temp.path).is_err(),
            "generated path: {generated:?}"
        );
    }

    for (source, generated) in [("build", "build/python"), ("build", "build")] {
        let temp = valid_project();
        let contents = format!(
            "[project]\nname = \"demo\"\nsource = \"{source}\"\n\n[target.python]\ngenerated = \"{generated}\"\nentry = \"module.function\"\n"
        );
        manifest(&temp.path, &contents);
        assert!(
            load_project(&temp.path).is_err(),
            "source/generated paths: {source:?}/{generated:?}"
        );
    }
}

#[test]
fn rejects_an_empty_source_directory() {
    let temp = valid_project();
    let project = load_project(&temp.path).expect("valid manifest should load");

    assert!(discover_sources(&project).is_err());
}

#[cfg(unix)]
fn symlink_file(link: &Path, target: &Path) -> io::Result<()> {
    std::os::unix::fs::symlink(target, link)
}

#[cfg(windows)]
fn symlink_file(link: &Path, target: &Path) -> io::Result<()> {
    std::os::windows::fs::symlink_file(target, link)
}

#[cfg(not(any(unix, windows)))]
fn symlink_file(_link: &Path, _target: &Path) -> io::Result<()> {
    Err(io::Error::new(
        io::ErrorKind::Unsupported,
        "file symlinks are unsupported on this platform",
    ))
}

#[test]
fn rejects_a_source_symlink_when_the_platform_supports_symlinks() {
    let temp = valid_project();
    fs::create_dir_all(temp.path.join("src")).expect("source directory should be writable");
    fs::write(temp.path.join("real.cott"), "module real\n").expect("source should be writable");
    if symlink_file(
        &temp.path.join("src/link.cott"),
        &temp.path.join("real.cott"),
    )
    .is_err()
    {
        return;
    }

    let project = load_project(&temp.path).expect("valid manifest should load");
    assert!(discover_sources(&project).is_err());
}
