use cott::compiler::{SourceFile, parse_project};
use cott::hir::lower;
use cott::ir::render;
use cott::manifest::{
    GeneratorConfig, ProjectMetadata, RuntimeValidation, RustProjectConfig, RustTarget,
    VerificationConfig,
};
use cott::rust::emit::{emit, implementation_signature};
use cott::rust::{RustBinding, RustOwner, RustPlan};
use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

struct Scratch(PathBuf);
impl Scratch {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!("cott-rust-consts-{}", std::process::id()));
        std::fs::create_dir(&path).unwrap();
        Self(path)
    }
}
impl Drop for Scratch {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.0).unwrap();
    }
}

#[test]
#[ignore = "requires absolute COTT_CARGO and offline tokio cache"]
fn native_const_expressions_preserve_dimension_and_nominal_identity() {
    let cargo =
        PathBuf::from(std::env::var_os("COTT_CARGO").expect("native tests require COTT_CARGO"));
    assert!(cargo.is_absolute(), "COTT_CARGO must be absolute");
    let source = r#"module api.consts

const THREE: U64 = 3
const RAW: Buffer[THREE] = Buffer("010203")

enum Failure:
    Bad

struct Foo[T, const N: U64]:
    values: Array[T, N]

struct Defaults:
    values: Array[U8, THREE] = Array(1, 2, 3)
    raw: Buffer[THREE] = Buffer("010203")

fn keep[T, const N: U64](value: Array[T, N+1]) -> Array[T, N+1]
fn nominal[T, const N: U64](value: Foo[T, N+1]) -> Foo[T, N+1]
fn closed(value: Array[U8, THREE]) -> Array[U8, THREE]
fn binary[const N: U64](value: Array[U8, ((N*2)-2)/2%4]) -> Array[U8, ((N*2)-2)/2%4]
fn buffer(value: Buffer[THREE]) -> Buffer[THREE]:
    requires value == RAW
    ensures result == RAW
fn fallible[const N: U64]() -> Result[Foo[U8, N+1], Failure]
"#;
    let parsed = parse_project([SourceFile::new("src/api/consts.cott", source)]).unwrap();
    let hir = lower(Path::new("src"), parsed).unwrap();
    let plan = RustPlan::from_ir(&render(&hir).unwrap()).unwrap();
    let config = RustProjectConfig {
        project: ProjectMetadata {
            name: "rust_consts".into(),
            version: "0.1.0".into(),
            source: "src".into(),
        },
        rust: RustTarget {
            source: "rust".into(),
            generated: "generated/rust".into(),
            cargo: "cargo".into(),
            rustc: "rustc".into(),
            runtime_validation: RuntimeValidation::Boundary,
            cargo_manifest: None,
            lockfile: None,
            implementations: BTreeMap::new(),
            external_types: BTreeMap::new(),
        },
        effects: BTreeMap::new(),
        generator: GeneratorConfig::default(),
        verification: VerificationConfig::default(),
    };
    let bindings = plan
        .callables()
        .iter()
        .map(|callable| {
            let body = if callable.name == "fallible" {
                "Err(crate::modules::api::consts::Failure::Bad)"
            } else {
                "value"
            };
            let bytes = format!(
                "{} {{ {body} }}\n",
                implementation_signature(&plan, callable).unwrap()
            )
            .into_bytes();
            let origin = format!("cott_impl/{}.rs", callable.symbol.replace('.', "/"));
            RustBinding {
                cott_symbol: callable.symbol.clone(),
                target_symbol: format!("{origin}:{}", callable.name),
                source_origin: origin.into(),
                runtime_origin: format!(
                    "rust/src/cott_impl/{}.rs",
                    callable.symbol.replace('.', "/")
                )
                .into(),
                content_hash: format!("sha256:{}", cott::hash::sha256_hex(&bytes)),
                bytes,
                owner: RustOwner::Agent,
            }
        })
        .collect::<Vec<_>>();
    let emission = emit(&config, &plan, &bindings).unwrap();
    assert!(emission.unresolved.is_empty(), "{:?}", emission.unresolved);
    let scratch = Scratch::new();
    for (path, bytes) in emission.files {
        if let Ok(relative) = path.strip_prefix("rust") {
            let destination = scratch.0.join(relative);
            std::fs::create_dir_all(destination.parent().unwrap()).unwrap();
            std::fs::write(destination, bytes).unwrap();
        }
    }
    std::fs::write(scratch.0.join("Cargo.toml"), "[package]\nname=\"rust_consts\"\nversion=\"0.1.0\"\nedition=\"2024\"\n[dependencies]\ntokio={version=\"=1.53.1\",default-features=false,features=[\"rt\",\"rt-multi-thread\",\"sync\",\"time\"]}\n").unwrap();
    std::fs::write(scratch.0.join("src/main.rs"), r#"use rust_consts::{modules::api::consts::*, cott_runtime::*};
fn main() {
    type Three = Add<ConstU64<2>, ConstU64<1>, 64>;
    let array: Array<u8, Three> = keep::<u8, ConstU64<2>>(Array::new(vec![1, 2, 3]));
    assert_eq!(array.as_slice(), &[1, 2, 3]);
    let foo: Foo<u8, Three> = nominal::<u8, ConstU64<2>>(Foo::new(array));
    assert_eq!(foo.get_values().as_slice(), &[1, 2, 3]);
    let reference: Array<u8, ConstU64<{THREE}>> = closed(Array::new(vec![4, 5, 6]));
    assert_eq!(reference.as_slice(), &[4, 5, 6]);
    assert_eq!(buffer(Buffer::new(vec![1,2,3])).as_slice(), &[1,2,3]);
    let defaults = Defaults::new(None, None);
    assert_eq!(defaults.get_values().as_slice(), &[1, 2, 3]);
    assert_eq!(defaults.get_raw().as_slice(), &[1, 2, 3]);
    let calculated = binary::<ConstU64<3>>(Array::new(vec![8, 9]));
    assert_eq!(calculated.as_slice(), &[8, 9]);
    assert!(matches!(fallible::<ConstU64<{u64::MAX}>>(), Err(Failure::Bad)));
    for size in [0, 2, 4] {
        let error = std::panic::catch_unwind(|| Array::<u8, Three>::new(vec![0; size])).unwrap_err();
        assert!(error.downcast_ref::<ContractViolation>().is_some());
    }
    assert_eq!(<Add<ConstU8<254>, ConstU8<1>, 8> as ConstValue>::value(), 255);
    assert_eq!(<Subtract<ConstU16<1>, ConstU16<1>, 16> as ConstValue>::value(), 0);
    assert_eq!(<Multiply<ConstU32<65535>, ConstU32<65537>, 32> as ConstValue>::value(), u32::MAX as u64);
    assert_eq!(<Remainder<ConstU64<{u64::MAX}>, ConstU64<2>, 64> as ConstValue>::value(), 1);
    let invalid: [fn() -> u64; 6] = [
        <Add<ConstU8<255>, ConstU8<1>, 8> as ConstValue>::value,
        <Subtract<ConstU64<0>, ConstU64<1>, 64> as ConstValue>::value,
        <Divide<ConstU64<1>, ConstU64<0>, 64> as ConstValue>::value,
        <Remainder<ConstU64<1>, ConstU64<0>, 64> as ConstValue>::value,
        <Multiply<ConstU64<{u64::MAX}>, ConstU64<2>, 64> as ConstValue>::value,
        <Subtract<Add<ConstU8<255>, ConstU8<1>, 8>, ConstU8<1>, 8> as ConstValue>::value,
    ];
    for expression in invalid {
        let error = std::panic::catch_unwind(expression).unwrap_err();
        assert!(error.downcast_ref::<ContractViolation>().is_some());
    }
}"#).unwrap();
    let build = std::process::Command::new(cargo)
        .current_dir(&scratch.0)
        .args(["build", "--offline"])
        .env_remove("CARGO_TARGET_DIR")
        .env_remove("CARGO_ENCODED_RUSTFLAGS")
        .env("RUSTFLAGS", "-D warnings")
        .env("CARGO_PROFILE_DEV_DEBUG", "0")
        .env("CARGO_PROFILE_TEST_DEBUG", "0")
        .env("CARGO_INCREMENTAL", "0")
        .output()
        .unwrap();
    assert!(
        build.status.success(),
        "{}",
        String::from_utf8_lossy(&build.stderr)
    );
    let run = std::process::Command::new(scratch.0.join("target/debug/rust_consts"))
        .output()
        .unwrap();
    assert!(
        run.status.success(),
        "{}",
        String::from_utf8_lossy(&run.stderr)
    );
    std::fs::write(scratch.0.join("src/main.rs"), "use rust_consts::{modules::api::consts::*, cott_runtime::*};\nfn main() { let _ = keep::<u8, ConstU8<2>>(Array::new(vec![1,2,3])); }\n").unwrap();
    let wrong_width = std::process::Command::new(std::env::var_os("COTT_CARGO").unwrap())
        .current_dir(&scratch.0)
        .args(["build", "--offline"])
        .env_remove("CARGO_TARGET_DIR")
        .env_remove("CARGO_ENCODED_RUSTFLAGS")
        .env("RUSTFLAGS", "-D warnings")
        .env("CARGO_PROFILE_DEV_DEBUG", "0")
        .env("CARGO_PROFILE_TEST_DEBUG", "0")
        .env("CARGO_INCREMENTAL", "0")
        .output()
        .unwrap();
    assert!(
        !wrong_width.status.success(),
        "U8 dimension accepted as canonical U64 parameter"
    );
    assert!(
        String::from_utf8_lossy(&wrong_width.stderr).contains("E0277"),
        "{}",
        String::from_utf8_lossy(&wrong_width.stderr)
    );
}
