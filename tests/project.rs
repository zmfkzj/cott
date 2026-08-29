use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::sync::atomic::{AtomicU64, Ordering};

use cott::project::{discover_python_sources, discover_sources_from_paths, load_config_with_paths};
#[cfg(unix)]
use std::ffi::CString;
#[cfg(unix)]
use std::os::unix::ffi::OsStrExt;

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

const NORMATIVE_MANIFEST: &str = r#"
[project]
name = "demo"
version = "0.1.0"
source = "src"

[target.python]
source = "python"
generated = "generated/python"
stubs = "generated/stubs"
lockfile = "uv.lock"
interpreter = ".venv/bin/python"
type_checker = ".venv/bin/basedpyright"
runtime_validation = "boundary"
"#;

fn manifest(root: &Path, contents: &str) {
    fs::write(root.join("cott.toml"), contents).expect("manifest should be writable");
}

fn target_metadata(root: &Path) {
    fs::create_dir_all(root.join("python")).expect("Python source directory");
    fs::write(
        root.join("python/pyproject.toml"),
        "[project]\nname = \"demo\"\nversion = \"0.1.0\"\nrequires-python = \">=3.14,<3.15\"\ndependencies = []\n",
    )
    .expect("target project metadata should be writable");
    fs::write(root.join("uv.lock"), "version = 1\n").expect("lockfile should be writable");
}

fn valid_project() -> TempDir {
    let temp = TempDir::new();
    manifest(&temp.path, NORMATIVE_MANIFEST);
    fs::create_dir_all(temp.path.join("src")).expect("source directory should be writable");
    target_metadata(&temp.path);
    temp
}

#[test]
fn derives_normative_project_paths_from_config() {
    let temp = TempDir::new();
    manifest(&temp.path, NORMATIVE_MANIFEST);
    fs::create_dir_all(temp.path.join("src")).expect("source directory should be writable");
    target_metadata(&temp.path);

    let (config, paths) =
        load_config_with_paths(&temp.path).expect("normative manifest should load");

    assert_eq!(config.project.source, "src");
    assert_eq!(paths.root, temp.path);
    assert_eq!(paths.manifest, temp.path.join("cott.toml"));
    assert_eq!(paths.source_dir, temp.path.join("src"));
    assert_eq!(paths.python_source_dir, temp.path.join("python"));
    assert_eq!(paths.generated_dir, temp.path.join("generated/python"));
    assert_eq!(paths.stubs_dir, temp.path.join("generated/stubs"));
    assert_eq!(paths.lockfile, Some(temp.path.join("uv.lock")));
}

#[test]
fn requires_matching_target_project_metadata() {
    let temp = valid_project();
    fs::remove_file(temp.path.join("python/pyproject.toml")).expect("remove metadata");
    let error = load_config_with_paths(&temp.path).expect_err("missing metadata must fail");
    assert!(error.to_string().contains("target project metadata"));

    target_metadata(&temp.path);
    fs::write(
        temp.path.join("python/pyproject.toml"),
        "[project]\nname = \"other\"\nversion = \"0.1.0\"\nrequires-python = \">=3.14,<3.15\"\ndependencies = []\n",
    )
    .expect("replace metadata");
    let error = load_config_with_paths(&temp.path).expect_err("mismatched metadata must fail");
    assert!(error.to_string().contains("name does not match"));
}

#[test]
fn normative_loader_rejects_entry_as_an_unknown_field() {
    let temp = TempDir::new();
    manifest(
        &temp.path,
        &NORMATIVE_MANIFEST.replace(
            "source = \"python\"",
            "source = \"python\"\nentry = \"app.run\"",
        ),
    );
    fs::create_dir_all(temp.path.join("src")).expect("source directory should be writable");

    let error = load_config_with_paths(&temp.path)
        .expect_err("legacy entry must be rejected by the closed manifest");
    let message = error.to_string();
    assert!(message.contains("unknown field") && message.contains("entry"));
}

#[cfg(unix)]
#[test]
fn normative_loader_rejects_a_non_regular_manifest() {
    let temp = TempDir::new();
    let manifest = temp.path.join("cott.toml");
    let manifest = CString::new(manifest.as_os_str().as_bytes())
        .expect("temporary manifest path should not contain NUL");
    let result = unsafe { libc::mkfifo(manifest.as_ptr(), 0o600) };
    assert_eq!(result, 0, "manifest FIFO should be creatable");

    assert!(load_config_with_paths(&temp.path).is_err());
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

    let (_, paths) = load_config_with_paths(&temp.path).expect("normative manifest should load");
    let sources = discover_sources_from_paths(&paths).expect("source files should be discovered");

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
        &NORMATIVE_MANIFEST.replace("name = \"demo\"", "name = \"demo\"\nunknown = true"),
    );

    assert!(load_config_with_paths(&temp.path).is_err());
}

#[test]
fn rejects_missing_manifest_fields() {
    let temp = valid_project();
    manifest(
        &temp.path,
        &NORMATIVE_MANIFEST.replace("\nsource = \"src\"", ""),
    );

    assert!(load_config_with_paths(&temp.path).is_err());
}

#[test]
fn rejects_duplicate_manifest_fields() {
    let temp = valid_project();
    manifest(
        &temp.path,
        &NORMATIVE_MANIFEST.replace("name = \"demo\"", "name = \"demo\"\nname = \"again\""),
    );

    assert!(load_config_with_paths(&temp.path).is_err());
}

#[test]
fn rejects_unsafe_and_overlapping_paths() {
    for source in ["", ".", "..", "../src", "/absolute/src"] {
        let temp = valid_project();
        let contents =
            NORMATIVE_MANIFEST.replace("source = \"src\"", &format!("source = \"{source}\""));
        manifest(&temp.path, &contents);
        assert!(
            load_config_with_paths(&temp.path).is_err(),
            "source path: {source:?}"
        );
    }

    for generated in ["", ".", "..", "../generated", "/absolute/generated"] {
        let temp = valid_project();
        let contents = NORMATIVE_MANIFEST.replace(
            "generated = \"generated/python\"",
            &format!("generated = \"{generated}\""),
        );
        manifest(&temp.path, &contents);
        assert!(
            load_config_with_paths(&temp.path).is_err(),
            "generated path: {generated:?}"
        );
    }

    for (source, generated) in [("build", "build/python"), ("build", "build")] {
        let temp = valid_project();
        let contents = NORMATIVE_MANIFEST
            .replace("source = \"src\"", &format!("source = \"{source}\""))
            .replace(
                "generated = \"generated/python\"",
                &format!("generated = \"{generated}\""),
            );
        manifest(&temp.path, &contents);
        assert!(
            load_config_with_paths(&temp.path).is_err(),
            "source/generated paths: {source:?}/{generated:?}"
        );
    }
}

#[test]
fn rejects_an_empty_source_directory() {
    let temp = valid_project();
    let (_, paths) = load_config_with_paths(&temp.path).expect("normative manifest should load");

    assert!(discover_sources_from_paths(&paths).is_err());
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
    fs::write(temp.path.join("real.cott"), "module real\n").expect("source should be writable");
    if symlink_file(
        &temp.path.join("src/link.cott"),
        &temp.path.join("real.cott"),
    )
    .is_err()
    {
        return;
    }

    let (_, paths) = load_config_with_paths(&temp.path).expect("normative manifest should load");
    assert!(discover_sources_from_paths(&paths).is_err());
}

#[test]
fn discovers_python_sources_in_lexical_order() {
    let temp = valid_project();
    fs::create_dir_all(temp.path.join("python/app")).expect("package directory");
    fs::write(temp.path.join("python/z.py"), "z = 1\n").expect("Python source");
    fs::write(temp.path.join("python/app/b.py"), "b = 1\n").expect("Python source");
    fs::write(temp.path.join("python/app/a.py"), "a = 1\n").expect("Python source");

    let sources = discover_python_sources(&temp.path.join("python")).expect("safe Python tree");
    assert_eq!(
        sources
            .into_iter()
            .map(|source| source.path)
            .collect::<Vec<_>>(),
        vec![
            PathBuf::from("app/a.py"),
            PathBuf::from("app/b.py"),
            PathBuf::from("z.py"),
        ]
    );
}

#[test]
fn excludes_python_environments_but_rejects_authored_symlinks() {
    let temp = valid_project();
    let python = temp.path.join("python");
    fs::create_dir_all(python.join(".venv/site-packages")).expect("environment directory");
    fs::create_dir(python.join("__pycache__")).expect("cache directory");
    fs::write(
        python.join(".venv/site-packages/bypass.py"),
        "import _cott_impl.secret\n",
    )
    .expect("environment source");
    fs::write(python.join("__pycache__/cached.pyc"), b"not Python").expect("cache bytecode");

    assert!(
        discover_python_sources(&python)
            .expect("environment is outside authored tree")
            .is_empty()
    );
    fs::write(python.join("authored.py"), "x = 1\n").expect("authored source");
    if symlink_file(
        &python.join("authored-link.py"),
        &python.join("authored.py"),
    )
    .is_ok()
    {
        assert!(discover_python_sources(&python).is_err());
    }
}

#[test]
fn rejects_unsafe_python_tree_entries() {
    let temp = valid_project();
    let python = temp.path.join("python");
    fs::write(python.join("app.py"), "x = 1\n").expect("Python source");
    fs::write(python.join("bad.py"), [0xff]).expect("invalid Python source");
    assert!(discover_python_sources(&python).is_err());
    fs::remove_file(python.join("bad.py")).expect("remove invalid source");

    if symlink_file(&python.join("link.py"), &python.join("app.py")).is_ok() {
        assert!(discover_python_sources(&python).is_err());
        fs::remove_file(python.join("link.py")).expect("remove symlink");
    }
    #[cfg(unix)]
    {
        fs::create_dir(python.join("real")).expect("real directory");
        std::os::unix::fs::symlink(python.join("real"), python.join("linked"))
            .expect("directory symlink");
        assert!(discover_python_sources(&python).is_err());
        fs::remove_file(python.join("linked")).expect("remove directory symlink");

        let fifo = CString::new(python.join("pipe.py").as_os_str().as_bytes())
            .expect("temporary FIFO path should not contain NUL");
        assert_eq!(unsafe { libc::mkfifo(fifo.as_ptr(), 0o600) }, 0);
        assert!(discover_python_sources(&python).is_err());
        fs::remove_file(python.join("pipe.py")).expect("remove FIFO");

        fs::hard_link(python.join("app.py"), python.join("linked.py")).expect("hard link");
        assert!(discover_python_sources(&python).is_err());
    }
}
