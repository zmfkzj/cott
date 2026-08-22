use std::path::Path;

use cott::manifest::{ProjectConfig, RuntimeValidation};

const VALID: &str = r#"
[project]
name = "demo"
version = "0.1.0"
source = "src"

[target.python]
source = "python"
generated = "generated/python"
stubs = "generated/stubs"
interpreter = ".venv/bin/python"
type_checker = ".venv/bin/basedpyright"
runtime_validation = "boundary"
"#;

#[test]
fn parses_the_closed_v1_manifest() {
    let manifest =
        ProjectConfig::parse(Path::new("cott.toml"), VALID).expect("manifest should parse");
    assert_eq!(manifest.project.version, "0.1.0");
    assert_eq!(
        manifest.python.runtime_validation,
        RuntimeValidation::Boundary
    );
    assert_eq!(manifest.generator.timeout_seconds, 900);
}

#[test]
fn defaults_external_type_projections() {
    let manifest =
        ProjectConfig::parse(Path::new("cott.toml"), VALID).expect("manifest should parse");
    assert!(manifest.python.external_types.is_empty());
}

#[test]
fn parses_external_type_projections() {
    let manifest = ProjectConfig::parse(
        Path::new("cott.toml"),
        &format!(
            "{VALID}\n[target.python.external_types]\n\"vendor.auth.AccessToken\" = \"vendor_sdk.auth:AccessToken\"\n\"vendor.models.Result\" = \"vendor_sdk.models:Result.Value\"\n"
        ),
    )
    .expect("external type projections should parse");
    assert_eq!(
        manifest
            .python
            .external_types
            .get("vendor.auth.AccessToken"),
        Some(&"vendor_sdk.auth:AccessToken".to_owned())
    );
    assert_eq!(
        manifest.python.external_types.get("vendor.models.Result"),
        Some(&"vendor_sdk.models:Result.Value".to_owned())
    );
}

#[test]
fn keeps_python_target_table_closed() {
    let invalid = format!("{VALID}\nexternal_types = {{}}\nunknown = true\n");
    assert!(ProjectConfig::parse(Path::new("cott.toml"), &invalid).is_err());
}

#[test]
fn requires_quoted_external_type_symbols() {
    let error = ProjectConfig::parse(
        Path::new("config/cott.toml"),
        &format!(
            "{VALID}\n[target.python.external_types]\nvendor.auth.AccessToken = \"vendor_sdk.auth:AccessToken\"\n"
        ),
    )
    .expect_err("dotted external symbols must be quoted TOML keys");
    assert_eq!(error.path, Path::new("config/cott.toml"));
}

#[test]
fn rejects_malformed_external_type_projections() {
    for (symbol, target) in [
        ("Token", "vendor.auth:Token"),
        ("vendor.type.Token", "vendor.auth:Token"),
        ("vendor.auth.Token", ":Token"),
        ("vendor.auth.Token", "vendor.auth:"),
        ("vendor.auth.Token", "vendor.auth:Outer:Token"),
        ("vendor.auth.Token", "vendor.class:Token"),
        ("vendor.auth.Token", "_cott_vendor.auth:Token"),
        ("vendor.auth.Token", "vendor auth:Token"),
        ("vendor.auth.Token", "vendor\\n.auth:Token"),
        ("vendor.auth.Token", "vendor.auth:Token; import os"),
    ] {
        let error = ProjectConfig::parse(
            Path::new("config/cott.toml"),
            &format!("{VALID}\n[target.python.external_types]\n\"{symbol}\" = \"{target}\"\n"),
        )
        .expect_err("malformed external type projection must fail");
        assert_eq!(error.path, Path::new("config/cott.toml"));
        assert!(
            error.message.contains("invalid external type projection"),
            "{symbol} = {target}: {}",
            error.message
        );
    }
}

#[test]
fn rejects_unknown_manifest_fields() {
    let invalid = VALID.replace("source = \"src\"", "source = \"src\"\nentry = \"app.run\"");
    assert!(ProjectConfig::parse(Path::new("cott.toml"), &invalid).is_err());
}

#[test]
fn parses_process_bar_normative_manifest_without_legacy_entry() {
    let path = Path::new("examples/complex/process-bar/cott.toml");
    let text = std::fs::read_to_string(path).expect("process-bar manifest should exist");
    assert!(
        !text
            .lines()
            .any(|line| line.trim_start().starts_with("entry =")),
        "process-bar manifest must not use the legacy entry key"
    );

    let manifest = ProjectConfig::parse(path, &text).expect("manifest should parse");
    assert_eq!(manifest.project.version, "0.1.0");
    assert_eq!(manifest.python.source, "python");
    assert_eq!(manifest.python.generated, "generated/python");
    assert_eq!(manifest.python.stubs, "generated/stubs");
    assert_eq!(
        manifest.python.runtime_validation,
        RuntimeValidation::Boundary
    );
    assert!(!text.contains("[target.python.implementations]"));
    assert!(manifest.python.implementations.is_empty());
    for implementation in [
        "build_output.py",
        "process_bar.py",
        "process_payload_bytes.py",
        "validate_payload.py",
    ] {
        assert!(
            !Path::new("examples/complex/process-bar/python/cott_bindings/foo/bar")
                .join(implementation)
                .exists(),
            "{implementation} must not be manifest-authored"
        );
        assert!(
            Path::new("examples/complex/process-bar/python/_cott_impl/foo/bar")
                .join(implementation)
                .is_file(),
            "{implementation} must be generated durably"
        );
    }
}
