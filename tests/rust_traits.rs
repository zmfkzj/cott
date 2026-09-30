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
                name: "rust_traits".into(),
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
    let origin = format!("cott_impl/{}.rs", symbol.replace('.', "/"));
    RustBinding {
        cott_symbol: symbol.into(),
        target_symbol: format!("{origin}:{}", callable.name),
        source_origin: origin.into(),
        runtime_origin: format!("rust/src/cott_impl/{}.rs", symbol.replace('.', "/")).into(),
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
            "cott-rust-traits-{}-{}",
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
    native_expected(config, plan, bindings, consumer, &[]);
}
fn native_expected(
    config: &RustProjectConfig,
    plan: &RustPlan,
    bindings: &[RustBinding],
    consumer: &str,
    unresolved: &[&str],
) {
    native_with_rejections(config, plan, bindings, consumer, unresolved, &[]);
}
fn native_with_rejections(
    config: &RustProjectConfig,
    plan: &RustPlan,
    bindings: &[RustBinding],
    consumer: &str,
    unresolved: &[&str],
    rejected: &[&str],
) {
    let cargo =
        PathBuf::from(std::env::var_os("COTT_CARGO").expect("native tests require COTT_CARGO"));
    assert!(cargo.is_absolute(), "COTT_CARGO must be absolute");
    let scratch = Scratch::new();
    let emission = emit(config, plan, bindings).unwrap();
    assert_eq!(
        emission
            .unresolved
            .iter()
            .map(String::as_str)
            .collect::<std::collections::BTreeSet<_>>(),
        unresolved.iter().copied().collect()
    );
    for (path, bytes) in emission.files {
        if let Ok(relative) = path.strip_prefix("rust") {
            let destination = scratch.0.join(relative);
            std::fs::create_dir_all(destination.parent().unwrap()).unwrap();
            std::fs::write(destination, bytes).unwrap();
        }
    }
    std::fs::write(scratch.0.join("Cargo.toml"), "[package]\nname=\"rust_traits\"\nversion=\"0.1.0\"\nedition=\"2024\"\n[dependencies]\ntokio={version=\"=1.53.1\",default-features=false,features=[\"rt\",\"rt-multi-thread\",\"sync\",\"time\"]}\n").unwrap();
    std::fs::write(scratch.0.join("src/main.rs"), consumer).unwrap();
    let build = std::process::Command::new(&cargo)
        .current_dir(&scratch.0)
        .args(["build", "--offline"])
        .env("RUSTFLAGS", "-D warnings")
        .env("CARGO_TARGET_DIR", scratch.0.join("target"))
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
    let run = std::process::Command::new(scratch.0.join("target/debug/rust_traits"))
        .output()
        .unwrap();
    assert!(
        run.status.success(),
        "{}",
        String::from_utf8_lossy(&run.stderr)
    );
    for source in rejected {
        std::fs::write(scratch.0.join("src/main.rs"), source).unwrap();
        let rejected = std::process::Command::new(&cargo)
            .current_dir(&scratch.0)
            .args(["check", "--offline"])
            .env("RUSTFLAGS", "-D warnings")
            .env("CARGO_TARGET_DIR", scratch.0.join("target"))
            .env("CARGO_PROFILE_DEV_DEBUG", "0")
            .env("CARGO_INCREMENTAL", "0")
            .output()
            .unwrap();
        assert!(
            !rejected.status.success(),
            "wrong trait instantiation compiled"
        );
        assert!(
            String::from_utf8_lossy(&rejected.stderr).contains("E0277"),
            "{}",
            String::from_utf8_lossy(&rejected.stderr)
        );
    }
}
fn protocol(source: &str) {
    let (config, plan) = fixture(source);
    let bindings = [
        binding(
            &plan,
            "curriculum.trait_protocol.default_category",
            "let _ = receiver; String::from(\"default\")",
        ),
        binding(
            &plan,
            "curriculum.trait_protocol.specialized_display",
            "format!(\"specialized: {}\", &*receiver.get_title())",
        ),
        binding(
            &plan,
            "curriculum.trait_protocol.task_factory",
            "crate::cott_runtime::Factory::constructor()",
        ),
        binding(
            &plan,
            "curriculum.trait_protocol.inspect_dyn",
            "let mut lease = item.acquire().await; lease.summary().await",
        ),
        binding(
            &plan,
            "curriculum.trait_protocol.SimpleTask.summary",
            "receiver.get_title().clone()",
        ),
        binding(
            &plan,
            "curriculum.trait_protocol.SimpleTask.priority_level",
            "*receiver.get_urgency()",
        ),
        binding(
            &plan,
            "curriculum.trait_protocol.SimpleTask.complete",
            "receiver.set_lifecycle(crate::modules::curriculum::trait_protocol::TaskLifecycle::Completed); receiver.update_completion_count(|value| *value += 1); true",
        ),
    ];
    native(
        &config,
        &plan,
        &bindings,
        r#"use rust_traits::{modules::curriculum::trait_protocol::*, cott_runtime};
fn main() {
    let rt = tokio::runtime::Builder::new_current_thread().build().unwrap();
    rt.block_on(async {
        let mut task = SimpleTask::new(String::from("Launch"), 1);
        let summary: <SimpleTask as SummarizableTypes>::Summary = Summarizable::summary(&mut task).await;
        assert_eq!(summary, "Launch");
        assert_eq!(TaskView::display(&mut task).await, "specialized: Launch");
        assert_eq!(TaskView::category(&mut task).await, "default");
        let view: TaskViewValue<String> = cott_runtime::Dyn::new(Box::new(task));
        {
            let mut lease = view.acquire().await;
            let summary: TaskViewSummary = lease.summary().await;
            assert_eq!(summary, "Launch");
            assert_eq!(lease.priority_level().await, 1);
            assert_eq!(lease.display().await, "specialized: Launch");
            assert_eq!(lease.category().await, "default");
        }
        assert_eq!(inspect_dyn(view).await, "Launch");
        let mut task = SimpleTask::new(String::from("Finish"), 0);
        assert!(Completable::complete(&mut task).await);
        assert_eq!(*task.get_completion_count(), 1);
        assert_eq!(*task.get_lifecycle(), TaskLifecycle::Completed);
        let mut constructed = task_factory().create((String::from("Factory"), 2));
        assert_eq!(Summarizable::summary(&mut constructed).await, "Factory");
    });
}"#,
    );
}
#[test]
#[ignore = "requires absolute COTT_CARGO and offline tokio cache"]
fn native_trait_protocol_example() {
    protocol(include_str!(
        "../examples/features/trait-protocol/src/curriculum/trait_protocol.cott"
    ));
}
#[test]
#[ignore = "requires absolute COTT_CARGO and offline tokio cache"]
fn native_kotlin_trait_protocol_example() {
    protocol(include_str!(
        "../examples/kotlin/features/trait-protocol/src/curriculum/trait_protocol.cott"
    ));
}
#[test]
#[ignore = "requires absolute COTT_CARGO and offline tokio cache"]
fn native_closed_associated_types_and_inherited_generics() {
    let (config, plan) = fixture(
        r#"module api.traits

trait HasItem:
    type Item
    fn read(self) -> HasItem.Item
    fn accepts(self, value: HasItem.Item) -> Bool
    fn snapshot(self) -> Tuple[Option[List[HasItem.Item]], HasItem.Item]

trait Parent[T] for HasItem:
    fn echo(self, value: T) -> T

trait Child[T] for Parent[T]:
    fn active(self) -> Bool

impl Text for Child[Str]:
    type Item = Str
    state:
        value: Str
    init(value: Str):
        ensures self.value == value
    fn read(self) -> Str:
        effects []
    fn echo(self, value: Str) -> Str:
        effects []
    fn accepts(self, value: Str) -> Bool:
        effects []
    fn snapshot(self) -> Tuple[Option[List[Str]], Str]:
        effects []
    fn active(self) -> Bool:
        effects []

impl Number for Child[I32]:
    type Item = I32
    state:
        value: I32
    init(value: I32):
        ensures self.value == value
    fn read(self) -> I32:
        effects []
    fn echo(self, value: I32) -> I32:
        effects []
    fn accepts(self, value: I32) -> Bool:
        effects []
    fn snapshot(self) -> Tuple[Option[List[I32]], I32]:
        effects []
    fn active(self) -> Bool:
        effects []

fn keep[T: Child[Str]](value: T) -> T
"#,
    );
    let bindings = [
        binding(
            &plan,
            "api.traits.Text.read",
            "receiver.get_value().clone()",
        ),
        binding(&plan, "api.traits.Text.echo", "let _ = receiver; value"),
        binding(
            &plan,
            "api.traits.Text.accepts",
            "&*receiver.get_value() == &value",
        ),
        binding(&plan, "api.traits.Text.active", "let _ = receiver; true"),
        binding(
            &plan,
            "api.traits.Text.snapshot",
            "let value = receiver.get_value().clone(); (Some(vec![value.clone()]), value)",
        ),
        binding(&plan, "api.traits.Number.read", "*receiver.get_value()"),
        binding(&plan, "api.traits.Number.echo", "let _ = receiver; value"),
        binding(
            &plan,
            "api.traits.Number.accepts",
            "*receiver.get_value() == value",
        ),
        binding(&plan, "api.traits.Number.active", "let _ = receiver; true"),
        binding(
            &plan,
            "api.traits.Number.snapshot",
            "let value = *receiver.get_value(); (Some(vec![value]), value)",
        ),
        binding(&plan, "api.traits.keep", "value"),
    ];
    native_with_rejections(
        &config,
        &plan,
        &bindings,
        r#"use rust_traits::{modules::api::traits::*, cott_runtime};
fn main() {
    let mut text = keep(Text::new(String::from("native")));
    let native: <Text as HasItemTypes>::Item = HasItem::read(&mut text);
    assert_eq!(native, "native");
    let view: ChildValue<String> = cott_runtime::Dyn::new(Box::new(text));
    let mut lease = view.try_acquire();
    assert_eq!(lease.read(), ChildItem::<String>::from(String::from("native")));
    assert_eq!(lease.echo(String::from("echo")), "echo");
    assert!(lease.accepts(ChildItem::<String>::from(String::from("native"))));
    assert!(lease.active());
    let (values, single) = lease.snapshot();
    assert_eq!(single, ChildItem::<String>::from(String::from("native")));
    assert_eq!(values.unwrap().remove(0), ChildItem::<String>::from(String::from("native")));
    let view: ChildValue<i32> = cott_runtime::Dyn::new(Box::new(Number::new(8)));
    let mut lease = view.try_acquire();
    assert_eq!(lease.read(), ChildItem::<i32>::from(8));
    assert_eq!(lease.echo(12), 12);
    assert!(lease.accepts(ChildItem::<i32>::from(8)));
}"#,
        &[],
        &[
            r#"use rust_traits::modules::api::traits::*; fn main(){let _:ChildItem<String> = 7_i32.into();}"#,
            r#"use rust_traits::modules::api::traits::*; fn main(){let _:ChildItem<i32> = String::from("wrong").into();}"#,
        ],
    );
}

#[test]
#[ignore = "requires absolute COTT_CARGO and offline tokio cache"]
fn native_generic_bound_associated_projection() {
    let (config, plan) = fixture(
        r#"module api.projections

trait Source[U]:
    type Item
    fn echo(self, value: U) -> U

trait Consumer[T: Source[Str]]:
    fn item(self, value: T.Item) -> T.Item

impl TextSource for Source[Str]:
    type Item = Str
    state:
        marker: Bool = true
    fn echo(self, value: Str) -> Str:
        effects []

impl Use for Consumer[TextSource]:
    state:
        marker: Bool = true
    fn item(self, value: TextSource.Item) -> TextSource.Item:
        effects []

fn preserve[T: Source[Str]](value: T.Item) -> T.Item
"#,
    );
    let bindings = [
        binding(
            &plan,
            "api.projections.TextSource.echo",
            "let _=receiver; value",
        ),
        binding(&plan, "api.projections.Use.item", "let _=receiver; value"),
        binding(&plan, "api.projections.preserve", "value"),
    ];
    native(
        &config,
        &plan,
        &bindings,
        r#"use rust_traits::{modules::api::projections::*,cott_runtime};
fn main() {
    let native: <TextSource as SourceTypes<String>>::Item = String::from("associated");
    assert_eq!(preserve::<TextSource>(native),"associated");
    let mut owner=Use::new();
    assert_eq!(Consumer::item(&mut owner,String::from("native")),"native");
    let view: ConsumerValue<TextSource>=cott_runtime::Dyn::new(Box::new(owner));
    assert_eq!(view.try_acquire().item(String::from("dynamic")),"dynamic");
}"#,
    );
}

#[test]
#[ignore = "requires absolute COTT_CARGO and offline tokio cache"]
fn native_bounded_associated_metadata_without_implementations() {
    let (config, plan) = fixture(
        r#"module api.metadata

trait Label:
    fn label(self) -> Str

trait Provider:
    type Item: Label
    fn get(self) -> Provider.Item

struct Holder[T: Label]:
    item: T

impl First for Label + Provider:
    type Item = First
    state:
        text: Str = "first"
    fn label(self) -> Str:
        effects []
    fn get(self) -> First:
        effects []

impl Second for Label + Provider:
    type Item = Second
    state:
        text: Str = "second"
    fn label(self) -> Str:
        effects []
    fn get(self) -> Second:
        effects []

"#,
    );
    native_expected(
        &config,
        &plan,
        &[],
        r#"use rust_traits::modules::api::metadata::*;
fn main(){
    let item:<First as ProviderTypes>::Item=First::new();
    let holder=Holder::new(item);
    assert_eq!(&**holder.get_item().get_text(),"first");
    let item:<Second as ProviderTypes>::Item=Second::new();
    let holder=Holder::new(item);
    assert_eq!(&**holder.get_item().get_text(),"second");
}"#,
        &[
            "api.metadata.First.label",
            "api.metadata.Second.label",
            "api.metadata.First.get",
            "api.metadata.Second.get",
        ],
    );
}

#[test]
#[ignore = "requires absolute COTT_CARGO and offline tokio cache"]
fn native_heterogeneous_associated_protocol_payloads_through_dyn() {
    let (config, plan) = fixture(
        r#"module api.streams

trait Items:
    type Item
    fn items(self) -> Iterator[Items.Item]
    fn exchange(self) -> Generator[Items.Item, Items.Item, Items.Item]

trait Stream[T] for Items:
    fn echo(self, value: T) -> T

impl Words for Stream[Str]:
    type Item = Str
    fn echo(self, value: Str) -> Str:
        effects []
    fn items(self) -> Iterator[Str]:
        effects []
    fn exchange(self) -> Generator[Str, Str, Str]:
        effects []

impl Numbers for Stream[I32]:
    type Item = I32
    fn echo(self, value: I32) -> I32:
        effects []
    fn items(self) -> Iterator[I32]:
        effects []
    fn exchange(self) -> Generator[I32, I32, I32]:
        effects []
"#,
    );
    let bindings = [
        binding(&plan, "api.streams.Words.echo", "let _ = receiver; value"),
        binding(&plan, "api.streams.Numbers.echo", "let _ = receiver; value"),
        binding(
            &plan,
            "api.streams.Words.items",
            "let _ = receiver; crate::cott_runtime::IteratorValue::new(vec![String::from(\"first\"),String::from(\"second\")].into_iter())",
        ),
        binding(
            &plan,
            "api.streams.Numbers.items",
            "let _ = receiver; crate::cott_runtime::IteratorValue::new(vec![3,4].into_iter())",
        ),
        binding(
            &plan,
            "api.streams.Words.exchange",
            r#"let _ = receiver; crate::cott_runtime::Generator::from_fn(|request| match request { crate::cott_runtime::GeneratorRequest::Start => crate::cott_runtime::GeneratorStep::Yield(String::from("ready")), crate::cott_runtime::GeneratorRequest::Send(value) => crate::cott_runtime::GeneratorStep::Return(value), _ => crate::cott_runtime::GeneratorStep::Return(String::from("closed")) }, || {})"#,
        ),
        binding(
            &plan,
            "api.streams.Numbers.exchange",
            r#"let _ = receiver; crate::cott_runtime::Generator::from_fn(|request| match request { crate::cott_runtime::GeneratorRequest::Start => crate::cott_runtime::GeneratorStep::Yield(7), crate::cott_runtime::GeneratorRequest::Send(value) => crate::cott_runtime::GeneratorStep::Return(value), _ => crate::cott_runtime::GeneratorStep::Return(0) }, || {})"#,
        ),
    ];
    native_with_rejections(
        &config,
        &plan,
        &bindings,
        r#"use rust_traits::{modules::api::streams::*,cott_runtime::{self,GeneratorStep}};
fn main(){
    let words:StreamValue<String>=cott_runtime::Dyn::new(Box::new(Words::new()));
    let mut words=words.try_acquire();
    let mut items=words.items();
    assert_eq!(items.next(),Some(StreamItem::<String>::from(String::from("first"))));
    assert_eq!(items.next(),Some(StreamItem::<String>::from(String::from("second"))));
    assert_eq!(items.next(),None);
    let generator=words.exchange();
    assert_eq!(generator.start(),GeneratorStep::Yield(StreamItem::<String>::from(String::from("ready"))));
    assert_eq!(generator.send(String::from("done").into()),GeneratorStep::Return(StreamItem::<String>::from(String::from("done"))));
    assert_eq!(generator.return_value(),Some(StreamItem::<String>::from(String::from("done"))));
    let numbers:StreamValue<i32>=cott_runtime::Dyn::new(Box::new(Numbers::new()));
    let mut numbers=numbers.try_acquire();
    let mut items=numbers.items();
    assert_eq!(items.next(),Some(StreamItem::<i32>::from(3)));
    assert_eq!(items.next(),Some(StreamItem::<i32>::from(4)));
    assert_eq!(items.next(),None);
    let generator=numbers.exchange();
    assert_eq!(generator.start(),GeneratorStep::Yield(StreamItem::<i32>::from(7)));
    assert_eq!(generator.send(9.into()),GeneratorStep::Return(StreamItem::<i32>::from(9)));
    assert_eq!(generator.return_value(),Some(StreamItem::<i32>::from(9)));
}"#,
        &[],
        &[
            r#"use rust_traits::modules::api::streams::*; fn main(){let _:StreamItem<String>=3_i32.into();}"#,
        ],
    );
}

#[test]
#[ignore = "requires absolute COTT_CARGO and offline tokio cache"]
fn native_generic_associated_families_preserve_payload_bounds() {
    let (config, plan) = fixture(
        r#"module api.family_bounds

trait Label:
    fn label(self) -> Str

trait Provider:
    type Item: Label
    fn item(self) -> Provider.Item

trait Root[T] for Provider:
    fn echo(self, value: T) -> T

struct Holder[T: Label]:
    value: T

impl Words for Label + Root[Str]:
    type Item = Words
    fn label(self) -> Str:
        effects []
    fn item(self) -> Words:
        effects []
    fn echo(self, value: Str) -> Str:
        effects []

impl Numbers for Label + Root[I32]:
    type Item = Numbers
    fn label(self) -> Str:
        effects []
    fn item(self) -> Numbers:
        effects []
    fn echo(self, value: I32) -> I32:
        effects []
"#,
    );
    let bindings = [
        binding(
            &plan,
            "api.family_bounds.Words.label",
            "let _=receiver; String::from(\"first\")",
        ),
        binding(
            &plan,
            "api.family_bounds.Numbers.label",
            "let _=receiver; String::from(\"second\")",
        ),
        binding(
            &plan,
            "api.family_bounds.Words.item",
            "let _=receiver; crate::modules::api::family_bounds::Words::new()",
        ),
        binding(
            &plan,
            "api.family_bounds.Numbers.item",
            "let _=receiver; crate::modules::api::family_bounds::Numbers::new()",
        ),
        binding(
            &plan,
            "api.family_bounds.Words.echo",
            "let _=receiver; value",
        ),
        binding(
            &plan,
            "api.family_bounds.Numbers.echo",
            "let _=receiver; value",
        ),
    ];
    native_with_rejections(
        &config,
        &plan,
        &bindings,
        r#"use rust_traits::{modules::api::family_bounds::*,cott_runtime};
fn main(){
    let root:RootValue<String>=cott_runtime::Dyn::new(Box::new(Words::new()));
    let mut item=root.try_acquire().item();
    assert_eq!(Label::label(&mut item),"first");
    let holder=Holder::new(item);
    assert_eq!(Label::label(&mut holder.get_value().clone()),"first");
    let root:RootValue<i32>=cott_runtime::Dyn::new(Box::new(Numbers::new()));
    let mut item=root.try_acquire().item();
    assert_eq!(Label::label(&mut item),"second");
}"#,
        &[],
        &[
            r#"use rust_traits::modules::api::family_bounds::*; fn main(){let _:RootItem<String>=Numbers::new().into();}"#,
        ],
    );
}
