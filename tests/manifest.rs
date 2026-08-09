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
