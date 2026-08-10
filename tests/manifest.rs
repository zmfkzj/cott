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
        for root in ["cott_bindings", "_cott_impl"] {
            assert!(
                !Path::new("examples/complex/process-bar/python")
                    .join(root)
                    .join("foo/bar")
                    .join(implementation)
                    .exists(),
                "{implementation} must begin unresolved under {root}"
            );
        }
    }
}
