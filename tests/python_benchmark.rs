use std::fs;
use std::process::Command;

#[test]
fn python_boundary_harness_regressions() {
    let root = std::env::temp_dir().join(format!("cott-benchmark-tests-{}", std::process::id()));
    fs::create_dir(&root).unwrap();
    for (relative, bytes) in cott::python_runtime::render_runtime("boundary-benchmark", "0.1.0") {
        let path = root.join(relative);
        fs::create_dir_all(path.parent().unwrap()).unwrap();
        fs::write(path, bytes).unwrap();
    }
    let result = Command::new("python3")
        .args([
            "-m",
            "unittest",
            "discover",
            "-s",
            "benchmarks",
            "-p",
            "test_*.py",
            "-v",
        ])
        .current_dir(env!("CARGO_MANIFEST_DIR"))
        .env("COTT_BENCH_RUNTIME", &root)
        .env("COTT_BENCH_COTT", env!("CARGO_BIN_EXE_cott"))
        .env("PYTHONDONTWRITEBYTECODE", "1")
        .output()
        .unwrap();
    fs::remove_dir_all(root).unwrap();
    assert!(
        result.status.success(),
        "{}\n{}",
        String::from_utf8_lossy(&result.stdout),
        String::from_utf8_lossy(&result.stderr)
    );
}
