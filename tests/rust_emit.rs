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

fn fixture(source: &str) -> (RustProjectConfig, RustPlan) {
    let module = source
        .lines()
        .find_map(|l| l.strip_prefix("module "))
        .unwrap()
        .split_whitespace()
        .next()
        .unwrap();
    let parsed = parse_project([SourceFile::new(
        format!("src/{}.cott", module.replace('.', "/")),
        source,
    )])
    .unwrap();
    let hir = lower(Path::new("src"), parsed).unwrap();
    let ir = render(&hir).unwrap();
    (
        RustProjectConfig {
            project: ProjectMetadata {
                name: "rust_emit".into(),
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
        },
        RustPlan::from_ir(&ir).unwrap(),
    )
}
fn binding(plan: &RustPlan, symbol: &str, body: &str) -> RustBinding {
    let callable = plan
        .callables()
        .iter()
        .find(|c| c.symbol == symbol)
        .unwrap();
    let bytes = format!(
        "{} {{ {body} }}\n",
        implementation_signature(plan, callable).unwrap()
    )
    .into_bytes();
    RustBinding {
        cott_symbol: symbol.into(),
        target_symbol: format!(
            "cott_impl/{}.rs:{}",
            symbol.replace('.', "/"),
            callable.name
        ),
        source_origin: PathBuf::from(format!("cott_impl/{}.rs", symbol.replace('.', "/"))),
        runtime_origin: PathBuf::from(format!(
            "rust/src/cott_impl/{}.rs",
            symbol.replace('.', "/")
        )),
        content_hash: format!("sha256:{}", cott::hash::sha256_hex(&bytes)),
        bytes,
        owner: RustOwner::Agent,
    }
}
struct Scratch(PathBuf);
impl Scratch {
    fn new() -> Self {
        static NEXT: std::sync::atomic::AtomicUsize = std::sync::atomic::AtomicUsize::new(0);
        let path = std::env::temp_dir().join(format!(
            "cott-rust-abi-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, std::sync::atomic::Ordering::Relaxed)
        ));
        std::fs::create_dir_all(&path).unwrap();
        Self(path)
    }
}
impl Drop for Scratch {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.0).unwrap();
    }
}
fn native(config: &RustProjectConfig, plan: &RustPlan, bindings: &[RustBinding], consumer: &str) {
    let cargo =
        PathBuf::from(std::env::var_os("COTT_CARGO").expect("native tests require COTT_CARGO"));
    assert!(cargo.is_absolute());
    let scratch = Scratch::new();
    let emission = emit(config, plan, bindings).unwrap();
    assert!(emission.unresolved.is_empty());
    for (path, bytes) in emission.files {
        if let Ok(relative) = path.strip_prefix("rust") {
            let path = scratch.0.join(relative);
            std::fs::create_dir_all(path.parent().unwrap()).unwrap();
            std::fs::write(path, bytes).unwrap();
        }
    }
    std::fs::write(scratch.0.join("Cargo.toml"),"[package]\nname=\"rust_emit\"\nversion=\"0.1.0\"\nedition=\"2024\"\n[dependencies]\ntokio={version=\"=1.53.1\",default-features=false,features=[\"rt\",\"rt-multi-thread\",\"sync\",\"time\"]}\n").unwrap();
    std::fs::write(scratch.0.join("src/main.rs"), consumer).unwrap();
    let output = std::process::Command::new(cargo)
        .current_dir(&scratch.0)
        .args(["build", "--offline"])
        .env("RUSTFLAGS", "-D warnings")
        .env("CARGO_PROFILE_DEV_DEBUG", "0")
        .env("CARGO_INCREMENTAL", "0")
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let output = std::process::Command::new(scratch.0.join("target/debug/rust_emit"))
        .output()
        .unwrap();
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
}
#[test]
fn public_symbol_inventory_is_valid_for_partial_publication() {
    let (config, plan) = fixture(
        "module sample\n\nfn zeta() -> I32\nfn alpha() -> I32\nfn gamma() -> I32\nfn delta() -> I32\nfn epsilon() -> I32\n",
    );
    let binding = binding(&plan, "sample.zeta", "1");
    let emission = emit(&config, &plan, &[binding]).unwrap();
    assert_eq!(
        emission.public_symbols["sample"],
        ["alpha", "delta", "epsilon", "gamma", "zeta"]
    );
}
#[test]
#[ignore = "requires absolute COTT_CARGO and offline tokio cache"]
fn native_facades_check_contracts_and_runtime() {
    let (config, plan) = fixture(
        "module api.counter\n\nfn increment(value: I32) -> I32:\n    requires value >= 0\n    ensures result == value + 1\n\nasync fn identity(value: I32) -> I32:\n    ensures result == value\n",
    );
    let bindings = [
        binding(&plan, "api.counter.increment", "value + 1"),
        binding(&plan, "api.counter.identity", "value"),
    ];
    native(
        &config,
        &plan,
        &bindings,
        r#"use rust_emit::{modules::api::counter,cott_runtime};
fn main(){assert_eq!(counter::increment(3),4);let panic=std::panic::catch_unwind(||counter::increment(-1)).unwrap_err();assert!(panic.downcast_ref::<cott_runtime::ContractViolation>().is_some());let rt=tokio::runtime::Builder::new_current_thread().build().unwrap();assert_eq!(rt.block_on(counter::identity(8)),8);assert_eq!(cott_runtime::math_rem(-7,3),2);assert!(cott_runtime::cyclic_by(&[(1,vec![2]),(2,vec![1])],|v|&v.0,|v|&v.1));}"#,
    );
}

#[test]
#[ignore = "requires absolute COTT_CARGO and offline tokio cache"]
fn native_declarations_generics_errors_and_state() {
    let (config, plan) = fixture(
        r#"module api.values

alias Count = I32

newtype Positive(I32)
    where self > 0

struct Pair[T]:
    first: T
    second: T

enum Choice[T]:
    Empty
    Value(value: T)

enum Problem:
    Negative
    Other(code: I32)

trait Counter:
    fn increment(self, amount: I32) -> I32

impl CounterState for Counter:
    state:
        value: I32 = 0
    invariant self.value >= 0
    fn increment(self, amount: I32) -> I32:
        modifies self.value
        ensures result >= 0

fn checked(value: I32) -> Result[I32, Problem]:
    ensures Result.Ok(ok_value) => ok_value >= 0
    errors complete
    error Problem.Negative when value < 0

fn echo[T](value: T) -> T
"#,
    );
    let bindings = [
        binding(
            &plan,
            "api.values.checked",
            "if value < 0 { Err(crate::modules::api::values::Problem::Negative) } else { Ok(value) }",
        ),
        binding(&plan, "api.values.echo", "value"),
        binding(
            &plan,
            "api.values.CounterState.increment",
            "receiver.update_value(|value|*value+=amount); *receiver.get_value()",
        ),
    ];
    native(
        &config,
        &plan,
        &bindings,
        r#"use rust_emit::{modules::api::values::*,cott_runtime};
fn main() {
 let pair=Pair::new(1,2);let copy=pair.copy_with(None,Some(4));assert_eq!(*pair.get_second(),2);assert_eq!(*copy.get_second(),4);
 assert_eq!(echo(String::from("native generic")),"native generic");
 assert_eq!(checked(-1),Err(Problem::Negative));assert_eq!(checked(3),Ok(3));
 let mut state=CounterState::new();cott_runtime::__cott_observe_begin();assert_eq!(Counter::increment(&mut state,2),2);let observations=cott_runtime::__cott_observe_end();assert!(observations.iter().any(|o|o.symbol=="api.values.CounterState.increment"&&o.clause=="invariant:0"&&o.passed));assert!(!observations.iter().any(|o|o.symbol=="api.values.CounterState"&&o.clause=="invariant:0"));
 assert!(std::panic::catch_unwind(||Positive::new(0)).unwrap_err().downcast_ref::<cott_runtime::ContractViolation>().is_some());
 let _choice=Choice::<i32>::Value(7);
}"#,
    );
}

#[test]
#[ignore = "requires absolute COTT_CARGO and offline tokio cache"]
fn native_existing_checked_add_contract_preserves_integer_boundaries() {
    let source = std::fs::read_to_string(
        "examples/kotlin/grammar/checked-add/src/curriculum/checked_add.cott",
    )
    .unwrap();
    let (config, plan) = fixture(&source);
    let implementation = binding(
        &plan,
        "curriculum.checked_add.checked_add",
        "i64::from(left)+i64::from(right)",
    );
    native(
        &config,
        &plan,
        &[implementation],
        r#"use rust_emit::modules::curriculum::checked_add::checked_add;
fn main(){assert_eq!(checked_add(i32::MIN,i32::MIN),-4294967296);assert_eq!(checked_add(i32::MAX,i32::MAX),4294967294);}"#,
    );
}

#[test]
#[ignore = "requires absolute COTT_CARGO and offline tokio cache"]
fn native_existing_stock_record_contract_checks_float_and_error_boundaries() {
    let source = std::fs::read_to_string(
        "examples/kotlin/grammar/stock-record/src/curriculum/stock_record.cott",
    )
    .unwrap();
    let (config, plan) = fixture(&source);
    let bindings = [
        binding(
            &plan,
            "curriculum.stock_record.value_record",
            r#"let value=(*record.get_shares() as f64)* *record.get_price();if value.is_finite(){Ok(value)}else{Err(crate::modules::curriculum::stock_record::StockRecordError::ValuationOverflow)}"#,
        ),
        binding(
            &plan,
            "curriculum.stock_record.value_stock_record",
            r#"use crate::modules::curriculum::stock_record::{StockRecordError,value_record};if record.get_name().is_empty(){Err(StockRecordError::EmptyName)}else if *record.get_shares()<0{Err(StockRecordError::NegativeShares)}else if *record.get_price()<0.0{Err(StockRecordError::NegativePrice)}else{value_record(record)}"#,
        ),
    ];
    native(
        &config,
        &plan,
        &bindings,
        r#"use rust_emit::{modules::curriculum::stock_record::*,cott_runtime};
fn main(){
 assert_eq!(value_stock_record(StockRecord::new("ACME".into(),12,2.5)),Ok(30.0));
 assert_eq!(value_stock_record(StockRecord::new("SHORT".into(),1,-1.0)),Err(StockRecordError::NegativePrice));
 assert_eq!(value_record(StockRecord::new("HUGE".into(),2,1.0e308)),Err(StockRecordError::ValuationOverflow));
 assert!(std::panic::catch_unwind(||StockRecord::new("bad".into(),1,f64::NAN)).unwrap_err().downcast_ref::<cott_runtime::ContractViolation>().is_some());
}"#,
    );
}

#[test]
#[ignore = "requires absolute COTT_CARGO and offline tokio cache"]
fn native_large_tuples_preserve_value_contracts_without_an_arity_cap() {
    for arity in [13, 32] {
        let types = vec!["F64"; arity].join(", ");
        let source = format!(
            "module api.tuples\n\nfn echo(value: Tuple[{types}]) -> Tuple[{types}]:\n    ensures result == value\n"
        );
        let (config, plan) = fixture(&source);
        let implementation = binding(&plan, "api.tuples.echo", "value.clone()");
        let values = (0..arity)
            .map(|i| format!("{}f64", i + 1))
            .collect::<Vec<_>>()
            .join(", ");
        let bad = (0..arity)
            .map(|i| {
                if i == arity - 1 {
                    "f64::NAN".to_owned()
                } else {
                    "1f64".to_owned()
                }
            })
            .collect::<Vec<_>>()
            .join(", ");
        let consumer = format!(
            "use rust_emit::{{cott_runtime,modules::api::tuples::echo}};fn main(){{let value=cott_runtime::Tuple{arity}({values});assert_eq!(echo(value.clone()),value);let panic=std::panic::catch_unwind(||echo(cott_runtime::Tuple{arity}({bad}))).unwrap_err();assert!(panic.downcast_ref::<cott_runtime::ContractViolation>().is_some());}}"
        );
        native(&config, &plan, &[implementation], &consumer);
    }
}

#[test]
#[ignore = "requires absolute COTT_CARGO and offline tokio cache"]
fn native_external_values_use_host_equality_or_opaque_identity() {
    let (mut config, plan) = fixture(
        "module api.host\n\nexternal type Moment\nexternal type Counter\n\nfn same(left: Moment, right: Moment) -> Bool:\n    ensures result == (left == right)\n",
    );
    config
        .rust
        .external_types
        .insert("api.host.Moment".into(), "std::time::SystemTime".into());
    config.rust.external_types.insert(
        "api.host.Counter".into(),
        "std::sync::atomic::AtomicUsize".into(),
    );
    let implementation = binding(&plan, "api.host.same", "left==right");
    native(
        &config,
        &plan,
        &[implementation],
        r#"use rust_emit::modules::api::host::*;
fn main(){let epoch=std::time::SystemTime::UNIX_EPOCH;assert!(same(Moment::from_native(epoch),Moment::from_native(epoch)));assert!(!same(Moment::from_native(epoch),Moment::from_native(epoch+std::time::Duration::from_secs(1))));let one=Counter::from_native(std::sync::atomic::AtomicUsize::new(1));assert_eq!(one,one.clone());assert_ne!(one,Counter::from_native(std::sync::atomic::AtomicUsize::new(1)));}"#,
    );
}

#[test]
#[ignore = "requires absolute COTT_CARGO and offline tokio cache"]
fn native_recursive_nominals_have_finite_boxed_layout_and_checked_values() {
    let (config, plan) = fixture(
        r#"module api.recursive

struct Node:
    value: I32
    next: Option[Node]

enum Tree:
    Leaf(value: F64)
    Branch(children: Tuple[Tree, Tree])

fn head(value: Node) -> I32:
    ensures result == value.value

fn echo(value: Tree) -> Tree:
    ensures result == value
"#,
    );
    let bindings = [
        binding(&plan, "api.recursive.head", "*value.get_value()"),
        binding(&plan, "api.recursive.echo", "value.clone()"),
    ];
    native(
        &config,
        &plan,
        &bindings,
        r#"use rust_emit::{modules::api::recursive::*,cott_runtime};
fn main(){let tail=Node::new(2,None);let root=Node::new(1,Some(tail));assert_eq!(head(root.clone()),1);let copy=root.copy_with(Some(3),None);assert_eq!(*root.get_value(),1);assert_eq!(*copy.get_value(),3);assert_eq!(*copy.get_next().as_ref().unwrap().get_value(),2);let tree=Box::new(Tree::Branch((Box::new(Tree::Leaf(1.0)),Box::new(Tree::Leaf(2.0)))));assert_eq!(echo(tree.clone()),tree);let panic=std::panic::catch_unwind(||echo(Box::new(Tree::Leaf(f64::NAN)))).unwrap_err();assert!(panic.downcast_ref::<cott_runtime::ContractViolation>().is_some());}"#,
    );
}

#[test]
#[ignore = "requires absolute COTT_CARGO and offline tokio cache"]
fn native_concrete_factories_retain_constructor_argument_types_and_defaults() {
    let (config, plan) = fixture(
        r#"module api.factories

trait PairView:
    fn first(self) -> Str

impl PairState for PairView:
    state:
        first: Str
        second: Str = "right"
    init(first: Str):
        ensures self.first == first
        ensures self.second == "right"
    fn first(self) -> Str:
        ensures result == self.first

fn keep(maker: Factory[PairState]) -> Factory[PairState]:
    ensures result == maker
"#,
    );
    let implementations = [
        binding(&plan, "api.factories.keep", "maker.clone()"),
        binding(
            &plan,
            "api.factories.PairState.first",
            "receiver.get_first().clone()",
        ),
    ];
    native(
        &config,
        &plan,
        &implementations,
        r#"use rust_emit::{cott_runtime::Factory,modules::api::factories::*};fn main(){let factory=keep(Factory::<PairState>::constructor());let pair=factory.create(("left".into(),));assert_eq!(pair.get_first().as_str(),"left");assert_eq!(pair.get_second().as_str(),"right");let changed=factory.create(("other".into(),));assert_eq!(changed.get_first().as_str(),"other");assert_eq!(changed.get_second().as_str(),"right");}"#,
    );
}
