use cott::compiler::{SourceFile, parse_project};
use cott::hir::lower_with_effects;
use cott::ir::render;
use cott::manifest::{
    GeneratorConfig, ProjectMetadata, RuntimeValidation, RustProjectConfig, RustTarget,
    VerificationConfig,
};
use cott::rust::{RustPlan, emit::emit};
use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

fn walk(path: &Path, result: &mut Vec<PathBuf>) {
    let mut entries = std::fs::read_dir(path)
        .unwrap()
        .map(|e| e.unwrap().path())
        .collect::<Vec<_>>();
    entries.sort();
    for entry in entries {
        if entry.is_dir() {
            if !matches!(
                entry.file_name().and_then(|s| s.to_str()),
                Some(
                    "generated"
                        | "dist"
                        | "target"
                        | ".cott"
                        | ".venv"
                        | "build"
                        | ".dart_tool"
                        | ".gradle"
                )
            ) {
                walk(&entry, result)
            }
        } else {
            result.push(entry)
        }
    }
}
struct Scratch(PathBuf);
impl Drop for Scratch {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.0).unwrap();
    }
}

#[test]
#[ignore = "requires absolute COTT_CARGO and offline tokio cache"]
fn every_example_contract_project_emits_an_offline_buildable_unresolved_rust_crate() {
    let cargo =
        PathBuf::from(std::env::var_os("COTT_CARGO").expect("absolute COTT_CARGO required"));
    assert!(cargo.is_absolute());
    let root = std::env::temp_dir().join(format!("cott-rust-corpus-{}", std::process::id()));
    std::fs::create_dir(&root).unwrap();
    let scratch = Scratch(root);
    let mut files = Vec::new();
    walk(Path::new("examples"), &mut files);
    let projects = files
        .iter()
        .filter(|p| p.file_name().and_then(|s| s.to_str()) == Some("cott.toml"))
        .map(|p| p.parent().unwrap().to_owned())
        .collect::<Vec<_>>();
    let mut failures = Vec::new();
    let mut count = 0;
    for (index, project) in projects.iter().enumerate() {
        let manifest: toml::Value =
            toml::from_str(&std::fs::read_to_string(project.join("cott.toml")).unwrap()).unwrap();
        let source = manifest["project"]["source"].as_str().unwrap_or("src");
        let source_root = project.join(source);
        if !source_root.is_dir() {
            continue;
        }
        let mut authored = Vec::new();
        walk(&source_root, &mut authored);
        let contracts = authored
            .into_iter()
            .filter(|p| p.extension().and_then(|s| s.to_str()) == Some("cott"))
            .collect::<Vec<_>>();
        if contracts.is_empty() {
            continue;
        }
        count += 1;
        let stage = scratch.0.join(format!("project-{index}"));
        std::fs::create_dir_all(stage.join("contracts")).unwrap();
        let result = (|| -> Result<(), String> {
            let mut sources = Vec::new();
            for path in &contracts {
                let relative = path.strip_prefix(&source_root).unwrap();
                let copied = stage.join("contracts").join(relative);
                std::fs::create_dir_all(copied.parent().unwrap()).map_err(|e| e.to_string())?;
                let bytes = std::fs::read(path).map_err(|e| e.to_string())?;
                std::fs::write(&copied, &bytes).map_err(|e| e.to_string())?;
                sources.push(SourceFile::new(
                    Path::new("contracts").join(relative),
                    String::from_utf8(bytes).map_err(|e| e.to_string())?,
                ));
            }
            let effects = manifest
                .get("effects")
                .and_then(toml::Value::as_table)
                .map(|effects| effects.keys().cloned().collect())
                .unwrap_or_default();
            let parsed = parse_project(sources).map_err(|e| format!("parse: {e:?}"))?;
            let hir = lower_with_effects(Path::new("contracts"), parsed, &effects)
                .map_err(|e| format!("lower: {e:?}"))?;
            let ir = render(&hir).map_err(|e| e.to_string())?;
            let plan = RustPlan::from_ir(&ir)?;
            // The corpus projection tests opaque external declarations, not their target-specific integrations.
            // Every declared external receives a real standard native host type; no implementation is resolved.
            let external_types = plan
                .modules
                .iter()
                .flat_map(|m| &m.declarations)
                .filter(|d| d["kind"] == "external_type")
                .map(|d| {
                    (
                        d["name"].as_str().unwrap().to_owned(),
                        "std::time::SystemTime".to_owned(),
                    )
                })
                .collect();
            let config = RustProjectConfig {
                project: ProjectMetadata {
                    name: "rust_breadth".into(),
                    version: manifest["project"]["version"]
                        .as_str()
                        .unwrap_or("0.1.0")
                        .into(),
                    source: "contracts".into(),
                },
                rust: RustTarget {
                    source: "rust".into(),
                    generated: "generated/rust".into(),
                    cargo: cargo.to_string_lossy().into_owned(),
                    rustc: "rustc".into(),
                    runtime_validation: RuntimeValidation::Boundary,
                    cargo_manifest: None,
                    lockfile: None,
                    implementations: BTreeMap::new(),
                    external_types,
                },
                effects: BTreeMap::new(),
                generator: GeneratorConfig::default(),
                verification: VerificationConfig::default(),
            };
            let emission = emit(&config, &plan, &[])?;
            for (path, bytes) in emission.files {
                if let Ok(relative) = path.strip_prefix("rust") {
                    let destination = stage.join(relative);
                    std::fs::create_dir_all(destination.parent().unwrap())
                        .map_err(|e| e.to_string())?;
                    std::fs::write(destination, bytes).map_err(|e| e.to_string())?;
                }
            }
            std::fs::write(stage.join("Cargo.toml"),format!("[package]\nname=\"rust_breadth\"\nversion={:?}\nedition=\"2024\"\n[dependencies]\ntokio={{version=\"=1.53.1\",default-features=false,features=[\"rt\",\"rt-multi-thread\",\"sync\",\"time\"]}}\n",config.project.version)).map_err(|e|e.to_string())?;
            let output = std::process::Command::new(&cargo)
                .current_dir(&stage)
                .args(["build", "--offline"])
                .env("RUSTFLAGS", "-D warnings")
                .env("CARGO_TARGET_DIR", scratch.0.join("target"))
                .env("CARGO_PROFILE_DEV_DEBUG", "0")
                .env("CARGO_INCREMENTAL", "0")
                .output()
                .map_err(|e| e.to_string())?;
            if !output.status.success() {
                return Err(String::from_utf8_lossy(&output.stderr).into_owned());
            }
            Ok(())
        })();
        match result {
            Ok(()) => println!("RUST_CORPUS PASS {}", project.display()),
            Err(error) => {
                println!("RUST_CORPUS FAIL {} {error}", project.display());
                failures.push((project.clone(), error));
            }
        }
    }
    assert!(count > 0, "no contract projects discovered");
    assert!(
        failures.is_empty(),
        "{}/{} corpus projects failed: {failures:#?}",
        failures.len(),
        count
    );
    println!("RUST_CORPUS TOTAL {count} passed");
}
