use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

use cott::compiler::{SourceFile, parse_project};
use cott::hash::sha256_hex;
use cott::hir::lower;
use cott::ir::render;
use cott::kotlin::emit::emit;
use cott::kotlin::{KotlinBinding, KotlinOwner, KotlinPlan};
use cott::manifest::{
    GeneratorConfig, KotlinProjectConfig, KotlinTarget, ProjectMetadata, RuntimeValidation,
    VerificationConfig,
};

fn fixture_from_source(source: &str) -> (KotlinProjectConfig, KotlinPlan) {
    let module = source
        .lines()
        .find_map(|line| line.strip_prefix("module "))
        .and_then(|module| module.split_whitespace().next())
        .expect("Kotlin emitter fixture should declare a module");
    let source_path = format!("src/{}.cott", module.replace('.', "/"));
    let parsed = parse_project([SourceFile::new(source_path, source)])
        .expect("Kotlin emitter fixture should parse");
    let ir = render(&lower(Path::new("src"), parsed).expect("fixture should lower"))
        .expect("fixture should render canonical IR");
    let plan = KotlinPlan::from_ir(&ir).expect("fixture should project to Kotlin");
    let config = KotlinProjectConfig {
        project: ProjectMetadata {
            name: "demo".to_owned(),
            version: "0.1.0".to_owned(),
            source: "src".to_owned(),
        },
        kotlin: KotlinTarget {
            source: "kotlin".to_owned(),
            generated: "generated/kotlin".to_owned(),
            compiler: "kotlinc".to_owned(),
            java: "java".to_owned(),
            jvm_target: 17,
            runtime_validation: RuntimeValidation::Boundary,
            classpath: Vec::new(),
            compile_only: Vec::new(),
            implementations: BTreeMap::new(),
            external_types: BTreeMap::new(),
        },
        effects: BTreeMap::new(),
        generator: GeneratorConfig::default(),
        verification: VerificationConfig::default(),
    };
    (config, plan)
}

fn fixture() -> (KotlinProjectConfig, KotlinPlan) {
    fixture_from_source("module app\n\nfn run() -> I32\n")
}

#[test]
fn unresolved_callables_remain_part_of_the_public_target_contract() {
    let (config, plan) = fixture();
    let emission =
        emit(&config, &plan, &[]).expect("unresolved plans still emit their types and IR");

    assert_eq!(emission.unresolved, ["app.run"]);
    assert_eq!(emission.public_symbols["app"], ["run"]);
    assert!(
        !emission
            .files
            .contains_key(Path::new("kotlin/cott_impl/app/run.kt"))
    );
}

#[test]
fn exact_binding_and_canonical_ir_bytes_are_emission_authorities() {
    let (config, plan) = fixture();
    let bytes = b"package cott_impl.app\n\ninternal fun run(): kotlin.Int = 7\n".to_vec();
    let binding = KotlinBinding {
        cott_symbol: "app.run".to_owned(),
        target_symbol: "cott_impl.app.run".to_owned(),
        source_origin: PathBuf::from("kotlin/cott_impl/app/run.kt"),
        runtime_origin: PathBuf::from("kotlin/cott_impl/app/run.kt"),
        content_hash: format!("sha256:{}", sha256_hex(&bytes)),
        bytes: bytes.clone(),
        owner: KotlinOwner::Manifest,
    };
    let emission = emit(&config, &plan, &[binding]).expect("resolved plan should emit");

    assert_eq!(emission.unresolved, Vec::<String>::new());
    assert_eq!(emission.public_symbols["app"], ["run"]);
    assert_eq!(
        emission.files[Path::new("kotlin/cott_impl/app/run.kt")],
        bytes
    );
    assert_eq!(
        emission.files[Path::new("ir/app.json")],
        plan.ir.modules[0].bytes
    );
}

#[test]
fn generic_empty_variants_and_recursive_nominals_are_emittable_contract_types() {
    let (config, plan) = fixture_from_source(
        r#"module app

enum Choice[T]:
    Empty
    Value(value: T)

struct Left[T]:
    right: Option[Right[T]]

struct Right[T]:
    left: Option[Left[T]]
"#,
    );
    let emission = emit(&config, &plan, &[])
        .expect("generic empty variants and mutually recursive descriptors should emit");

    assert_eq!(emission.public_symbols["app"], ["Choice", "Left", "Right"]);
    assert!(emission.unresolved.is_empty());
}

#[test]
fn reserved_platform_package_roots_are_rejected() {
    for root in ["java", "javax", "kotlin", "android"] {
        let source = format!("module {root}.collision\n\nstruct Value:\n    item: I32\n");
        let (config, plan) = fixture_from_source(&source);
        emit(&config, &plan, &[]).expect_err("platform package root must be reserved");
    }
}
