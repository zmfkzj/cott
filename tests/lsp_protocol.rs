use std::process::Command;

#[test]
fn cli_and_stdio_lsp_preserve_diagnostic_details_and_source() {
    let output = Command::new("timeout")
        .args([
            "40",
            "python3",
            "tests/support/lsp_protocol.py",
            env!("CARGO_BIN_EXE_cott"),
        ])
        .current_dir(env!("CARGO_MANIFEST_DIR"))
        .env("PYTHONDONTWRITEBYTECODE", "1")
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}\n{}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
}
