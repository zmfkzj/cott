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
        static NEXT: std::sync::atomic::AtomicUsize = std::sync::atomic::AtomicUsize::new(0);
        let path = std::env::temp_dir().join(format!(
            "cott-rust-runtime-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, std::sync::atomic::Ordering::Relaxed)
        ));
        std::fs::create_dir(&path).unwrap();
        Self(path)
    }
}
impl Drop for Scratch {
    fn drop(&mut self) {
        std::fs::remove_dir_all(&self.0).unwrap();
    }
}
fn native(consumer: &str) {
    let cargo =
        PathBuf::from(std::env::var_os("COTT_CARGO").expect("native tests require COTT_CARGO"));
    assert!(cargo.is_absolute());
    let source = "module api.runtime\n\ntrait Mutator:\n    async fn mutate(self) -> Unit\n\nimpl CounterState for Mutator:\n    state:\n        value: U32 = 0\n    async fn mutate(self) -> Unit:\n        modifies self.value\n";
    let parsed = parse_project([SourceFile::new("src/api/runtime.cott", source)]).unwrap();
    let plan =
        RustPlan::from_ir(&render(&lower(Path::new("src"), parsed).unwrap()).unwrap()).unwrap();
    let config = RustProjectConfig {
        project: ProjectMetadata {
            name: "rust_runtime".into(),
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
    let bindings = plan.callables().iter().map(|callable| {
        let body = "let scope = crate::cott_runtime::TaskScope::default(); let mut child = receiver.clone(); let task = scope.spawn(move |_| async move { child.set_value(1); }); task.result().await; scope.close(false).await;";
        let bytes = format!("{} {{ {body} }}\n", implementation_signature(&plan, callable).unwrap()).into_bytes();
        let origin = format!("cott_impl/{}.rs", callable.symbol.replace('.', "/"));
        RustBinding { cott_symbol: callable.symbol.clone(), target_symbol: format!("{origin}:{}", callable.name), source_origin: origin.into(), runtime_origin: format!("rust/src/cott_impl/{}.rs", callable.symbol.replace('.', "/")).into(), content_hash: format!("sha256:{}", cott::hash::sha256_hex(&bytes)), bytes, owner: RustOwner::Agent }
    }).collect::<Vec<_>>();
    let emission = emit(&config, &plan, &bindings).unwrap();
    assert!(emission.unresolved.is_empty());
    let scratch = Scratch::new();
    for (path, bytes) in emission.files {
        if let Ok(relative) = path.strip_prefix("rust") {
            let destination = scratch.0.join(relative);
            std::fs::create_dir_all(destination.parent().unwrap()).unwrap();
            std::fs::write(destination, bytes).unwrap();
        }
    }
    std::fs::write(scratch.0.join("Cargo.toml"), "[package]\nname=\"rust_runtime\"\nversion=\"0.1.0\"\nedition=\"2024\"\n[dependencies]\ntokio={version=\"=1.53.1\",default-features=false,features=[\"rt\",\"rt-multi-thread\",\"sync\",\"time\"]}\n").unwrap();
    std::fs::write(scratch.0.join("src/main.rs"), consumer).unwrap();
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
    let run = std::process::Command::new(scratch.0.join("target/debug/rust_runtime"))
        .output()
        .unwrap();
    assert!(
        run.status.success(),
        "{}",
        String::from_utf8_lossy(&run.stderr)
    );
}

#[test]
#[ignore = "requires absolute COTT_CARGO and offline tokio cache"]
fn native_tasks_are_typed_cooperative_and_structured() {
    native(
        r#"use rust_runtime::{cott_runtime::*, modules::api::runtime::*};
use std::{future::Future, sync::{Arc, atomic::{AtomicBool, Ordering}}};
async fn caught<F: Future>(future: F) -> Result<F::Output, Box<dyn std::any::Any + Send>> {
    let mut future = std::pin::pin!(future);
    std::future::poll_fn(|cx| match std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| future.as_mut().poll(cx))) {
        Ok(poll) => poll.map(Ok), Err(error) => std::task::Poll::Ready(Err(error)),
    }).await
}
async fn exercise() {
    let scope = TaskScope::default();
    let task = scope.spawn(|_| async { 42u32 });
    assert_eq!(task.result().await, 42);
    assert_eq!(task.clone().result().await, 42);
    task.join().await;
    scope.close(false).await;
    let closed = caught(async { scope.spawn(|_| async {}); }).await.unwrap_err();
    assert!(closed.is::<ContractViolation>());
    scope.close(false).await;

    let scope = TaskScope::default();
    let task = scope.spawn::<(), _, _>(|_| async { std::panic::panic_any(73u32); });
    for _ in 0..2 {
        let failure = caught(task.result()).await.unwrap_err();
        let failure = failure.downcast_ref::<TaskFailure>().unwrap();
        assert!(failure.with_payload(|payload| payload.downcast_ref::<u32>() == Some(&73)));
    }
    assert!(caught(scope.close(false)).await.unwrap_err().is::<TaskFailure>());

    let parent = CancellationToken::default();
    let scope = TaskScope::new(Some(parent.clone()));
    let task = scope.spawn(|token| async move { token.cancelled().await; token.check(); 7u32 });
    parent.cancel_with_reason("parent cancelled");
    parent.cancel_with_reason("replacement reason");
    let failure = caught(task.result()).await.unwrap_err();
    assert_eq!(&*failure.downcast_ref::<CancellationException>().unwrap().reason, "parent cancelled");
    assert!(caught(scope.close(false)).await.unwrap_err().is::<CancellationException>());

    let scope = TaskScope::default();
    let cancelled = scope.spawn(|token| async move { token.cancelled().await; token.check(); 1u32 });
    let unaffected = scope.spawn(|_| async { 2u32 });
    cancelled.cancel();
    assert!(caught(cancelled.result()).await.unwrap_err().is::<CancellationException>());
    assert!(!scope.cancellation_token().is_cancelled());
    assert_eq!(unaffected.result().await, 2);
    assert!(caught(scope.close(false)).await.unwrap_err().is::<CancellationException>());

    let scope = TaskScope::default();
    let failed = scope.spawn::<(), _, _>(|_| async { violation("child", "validation", "child failure"); });
    let (release, pending) = tokio::sync::oneshot::channel();
    let completed = Arc::new(AtomicBool::new(false));
    let marker = completed.clone();
    let successful = scope.spawn(move |_| async move { pending.await.unwrap(); marker.store(true, Ordering::SeqCst); 5u32 });
    for _ in 0..2 { assert!(caught(failed.result()).await.unwrap_err().is::<ContractViolation>()); }
    let mut joined = std::pin::pin!(caught(scope.join()));
    std::future::poll_fn(|cx| {
        assert!(joined.as_mut().poll(cx).is_pending(), "join propagated failure before draining every child");
        std::task::Poll::Ready(())
    }).await;
    release.send(()).unwrap();
    assert!(joined.await.unwrap_err().is::<ContractViolation>());
    assert!(completed.load(Ordering::SeqCst));
    assert_eq!(successful.result().await, 5);
    assert!(caught(scope.close(false)).await.unwrap_err().is::<ContractViolation>());

    let scope = TaskScope::default();
    let started = Arc::new(tokio::sync::Notify::new());
    let ready = started.clone();
    let cleaned = Arc::new(AtomicBool::new(false));
    let cleanup = cleaned.clone();
    let task = scope.spawn(move |token| async move {
        ready.notify_one(); token.cancelled().await;
        cleanup.store(true, Ordering::SeqCst); 9u32
    });
    started.notified().await;
    scope.close(true).await;
    assert!(cleaned.load(Ordering::SeqCst));
    assert_eq!(task.result().await, 9);

    let scope = TaskScope::default();
    let started = Arc::new(tokio::sync::Notify::new());
    let ready = started.clone();
    let cleaned = Arc::new(AtomicBool::new(false));
    let cleanup = cleaned.clone();
    let task = scope.spawn(move |token| async move {
        ready.notify_one(); token.cancelled().await;
        cleanup.store(true, Ordering::SeqCst); 11u32
    });
    started.notified().await;
    drop(scope);
    assert_eq!(task.result().await, 11);
    assert!(cleaned.load(Ordering::SeqCst), "scope drop aborted owned cleanup");

    let scope = TaskScope::default();
    let started = Arc::new(tokio::sync::Notify::new());
    let marker = started.clone();
    let (send, receive) = tokio::sync::oneshot::channel();
    let task = scope.spawn(move |_| async move { marker.notify_one(); receive.await.unwrap() });
    started.notified().await;
    task.cancel();
    scope.cancel();
    send.send(8u32).unwrap();
    assert_eq!(task.result().await, 8, "cancellation cannot preempt a running operation");
    scope.close(false).await;

    let finished = Arc::new(AtomicBool::new(false));
    let marker = finished.clone();
    let failure = caught(TaskScope::run::<(), _, _>(move |scope| async move {
        let started = Arc::new(tokio::sync::Notify::new());
        let ready = started.clone();
        scope.spawn::<(), _, _>(move |token| async move {
            ready.notify_one(); token.cancelled().await;
            marker.store(true, Ordering::SeqCst);
            std::panic::panic_any(2u32);
        });
        started.notified().await;
        std::panic::panic_any(1u32);
    }, None)).await.unwrap_err();
    assert_eq!(failure.downcast_ref::<u32>(), Some(&1));
    assert!(finished.load(Ordering::SeqCst), "body failure escaped before owned children drained");

    let (result, events) = __cott_observe_async(async {
        let scope = TaskScope::default();
        scope.spawn(|_| async { __cott_check("child", "ensures", "child predicate", true); });
        scope.close(false).await;
    }).await;
    result.unwrap();
    assert_eq!(events.len(), 1);
    assert_eq!(events[0].symbol, "child");
    assert!(events[0].passed);

    let mut counter = CounterState::new();
    let failure = caught(Mutator::mutate(&mut counter)).await.unwrap_err();
    assert!(failure.is::<ContractViolation>(), "child task inherited parent mutation authority");
    assert_eq!(*counter.get_value(), 0);

    let lease = Lease::new(1u32);
    let guard = lease.acquire().await;
    let cancellation = CancellationToken::default();
    cancellation.cancel();
    assert!(caught(lease.acquire_with_cancellation(&cancellation)).await.unwrap_err().is::<CancellationException>());
    let cancellation = CancellationToken::default();
    let child_token = cancellation.clone();
    let child_lease = lease.clone();
    let queued = Arc::new(tokio::sync::Notify::new());
    let ready = queued.clone();
    let waiter = tokio::spawn(async move {
        let mut acquire = std::pin::pin!(child_lease.acquire_with_cancellation(&child_token));
        caught(std::future::poll_fn(|cx| match acquire.as_mut().poll(cx) {
            std::task::Poll::Pending => { ready.notify_one(); std::task::Poll::Pending }
            ready => ready,
        })).await.unwrap_err().is::<CancellationException>()
    });
    queued.notified().await;
    cancellation.cancel();
    assert!(waiter.await.unwrap());
    drop(guard);
    *lease.acquire().await = 2;
    assert_eq!(*lease.acquire().await, 2);
}
fn main() {
    tokio::runtime::Builder::new_multi_thread().worker_threads(2).enable_all().build().unwrap().block_on(async {
        tokio::time::timeout(std::time::Duration::from_secs(10), exercise()).await.unwrap();
    });
}"#,
    );
}

#[test]
#[ignore = "requires absolute COTT_CARGO and offline tokio cache"]
fn native_protocols_validate_payloads_and_enforce_lifecycle() {
    native(
        r#"use rust_runtime::cott_runtime::*;
use std::{future::Future, sync::{Arc, atomic::{AtomicBool, AtomicUsize, Ordering}}};
async fn caught<F: Future>(future: F) -> Result<F::Output, Box<dyn std::any::Any + Send>> {
    let mut future = std::pin::pin!(future);
    std::future::poll_fn(|cx| match std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| future.as_mut().poll(cx))) {
        Ok(poll) => poll.map(Ok), Err(error) => std::task::Poll::Ready(Err(error)),
    }).await
}
fn invalid(action: impl FnOnce() + std::panic::UnwindSafe) {
    assert!(std::panic::catch_unwind(action).unwrap_err().is::<ContractViolation>());
}
struct OwnedIterator { values: std::vec::IntoIter<u32>, dropped: Arc<AtomicUsize> }
impl Iterator for OwnedIterator { type Item = u32; fn next(&mut self) -> Option<u32> { self.values.next() } }
impl Drop for OwnedIterator { fn drop(&mut self) { self.dropped.fetch_add(1, Ordering::SeqCst); } }
struct Sequence { values: std::vec::IntoIter<f64>, closed: Arc<AtomicUsize>, calls: Arc<AtomicUsize> }
impl IteratorSource<f64> for Sequence {
    fn next(&mut self) -> Option<f64> { self.calls.fetch_add(1, Ordering::SeqCst); self.values.next() }
    fn close(&mut self) { self.closed.fetch_add(1, Ordering::SeqCst); }
}
struct Machine { value: f64, starts: Arc<AtomicUsize>, closed: Arc<AtomicUsize> }
impl GeneratorProtocol<f64, f64, f64> for Machine {
    fn start(&mut self) -> GeneratorStep<f64,f64> { self.starts.fetch_add(1, Ordering::SeqCst); GeneratorStep::Yield(self.value) }
    fn next(&mut self) -> GeneratorStep<f64,f64> { GeneratorStep::Return(self.value) }
    fn send(&mut self, value: f64) -> GeneratorStep<f64,f64> { self.value += value; GeneratorStep::Yield(self.value) }
    fn raise(&mut self, error: ProtocolError) -> GeneratorStep<f64,f64> {
        assert_eq!(error.downcast_ref::<std::io::Error>().unwrap().kind(), std::io::ErrorKind::Interrupted);
        self.value += 10.0; GeneratorStep::Yield(self.value)
    }
    fn close(&mut self) { self.closed.fetch_add(1, Ordering::SeqCst); }
}
struct ReturnBoundary { returned: bool }
impl GeneratorProtocol<f64, f64, f64> for ReturnBoundary {
    fn start(&mut self) -> GeneratorStep<f64,f64> { GeneratorStep::Yield(f64::NAN) }
    fn next(&mut self) -> GeneratorStep<f64,f64> {
        if self.returned { GeneratorStep::Return(4.0) } else { self.returned = true; GeneratorStep::Return(f64::INFINITY) }
    }
    fn send(&mut self, value: f64) -> GeneratorStep<f64,f64> { GeneratorStep::Yield(value) }
    fn raise(&mut self, _: ProtocolError) -> GeneratorStep<f64,f64> { GeneratorStep::Return(5.0) }
    fn close(&mut self) {}
}
struct ImmediateIterator { values: std::vec::IntoIter<f64>, closed: Arc<AtomicUsize> }
impl AsyncIterator<f64> for ImmediateIterator {
    fn next(&mut self, _: Option<CancellationToken>) -> BoxFuture<'_,Option<f64>> { Box::pin(async move { self.values.next() }) }
    fn close(&mut self, _: Option<CancellationToken>) -> BoxFuture<'_,()> {
        Box::pin(async move { self.values = Vec::new().into_iter(); self.closed.fetch_add(1,Ordering::SeqCst); })
    }
}
struct PendingIterator {
    started: Arc<tokio::sync::Notify>, release: Arc<tokio::sync::Notify>, finished: Arc<AtomicBool>,
    done: bool, closed: Arc<AtomicUsize>,
}
impl AsyncIterator<f64> for PendingIterator {
    fn next(&mut self, _: Option<CancellationToken>) -> BoxFuture<'_, Option<f64>> {
        Box::pin(async move {
            self.started.notify_one(); self.release.notified().await; self.finished.store(true, Ordering::SeqCst);
            if self.done { None } else { self.done = true; Some(3.0) }
        })
    }
    fn close(&mut self, _: Option<CancellationToken>) -> BoxFuture<'_, ()> {
        Box::pin(async move { self.closed.fetch_add(1, Ordering::SeqCst); })
    }
}
struct AsyncMachine { value: f64, starts: Arc<AtomicUsize>, closed: Arc<AtomicUsize> }
impl AsyncGeneratorProtocol<f64,f64> for AsyncMachine {
    fn start(&mut self, _: Option<CancellationToken>) -> BoxFuture<'_, GeneratorStep<f64,()>> {
        Box::pin(async move { self.starts.fetch_add(1, Ordering::SeqCst); GeneratorStep::Yield(self.value) })
    }
    fn next(&mut self, _: Option<CancellationToken>) -> BoxFuture<'_, GeneratorStep<f64,()>> { Box::pin(async { GeneratorStep::Return(()) }) }
    fn send(&mut self, value: f64, _: Option<CancellationToken>) -> BoxFuture<'_, GeneratorStep<f64,()>> {
        Box::pin(async move { self.value += value; GeneratorStep::Yield(self.value) })
    }
    fn raise(&mut self, error: ProtocolError, _: Option<CancellationToken>) -> BoxFuture<'_, GeneratorStep<f64,()>> {
        Box::pin(async move {
            assert_eq!(error.downcast_ref::<std::io::Error>().unwrap().kind(), std::io::ErrorKind::Interrupted);
            self.value += 10.0; GeneratorStep::Yield(self.value)
        })
    }
    fn close(&mut self, _: Option<CancellationToken>) -> BoxFuture<'_, ()> {
        Box::pin(async move { self.closed.fetch_add(1, Ordering::SeqCst); })
    }
}
fn recovery() -> ProtocolError { Box::new(std::io::Error::from(std::io::ErrorKind::Interrupted)) }
async fn exercise() {
    let dropped = Arc::new(AtomicUsize::new(0));
    let mut iterator = IteratorValue::new(OwnedIterator { values: vec![1,2].into_iter(), dropped: dropped.clone() });
    assert_eq!(iterator.next(), Some(1));
    iterator.clone().close();
    assert_eq!(dropped.load(Ordering::SeqCst), 1);
    assert_eq!(iterator.next(), None);
    iterator.close();
    assert_eq!(dropped.load(Ordering::SeqCst), 1);
    let calls = Arc::new(AtomicUsize::new(0));
    let closed = Arc::new(AtomicUsize::new(0));
    let mut iterator = IteratorValue::from_source(Sequence { values: vec![1.0,2.0].into_iter(), closed: closed.clone(), calls: calls.clone() });
    assert_eq!(iterator.next(), Some(1.0));
    assert_eq!(iterator.next(), Some(2.0));
    assert_eq!(iterator.next(), None);
    assert_eq!(iterator.next(), None);
    iterator.close();
    assert_eq!(calls.load(Ordering::SeqCst), 3);
    assert_eq!(closed.load(Ordering::SeqCst), 0);
    let mut invalid_yield = IteratorValue::new(vec![f64::NAN, 2.0].into_iter());
    invalid(std::panic::AssertUnwindSafe(|| { invalid_yield.next(); }));
    assert_eq!(invalid_yield.next(), Some(2.0), "panic must release the operation guard");

    let starts = Arc::new(AtomicUsize::new(0));
    let closed = Arc::new(AtomicUsize::new(0));
    let generator = Generator::new(Machine { value: 1.0, starts: starts.clone(), closed: closed.clone() });
    invalid(std::panic::AssertUnwindSafe(|| { generator.send(2.0); }));
    assert_eq!(generator.return_value(), None);
    assert_eq!(generator.next_step(), GeneratorStep::Yield(1.0));
    invalid(std::panic::AssertUnwindSafe(|| { generator.start(); }));
    invalid(std::panic::AssertUnwindSafe(|| { generator.send(f64::INFINITY); }));
    assert_eq!(generator.send(2.0), GeneratorStep::Yield(3.0));
    assert_eq!(generator.throw_into(recovery()), GeneratorStep::Yield(13.0));
    assert_eq!(generator.next_step(), GeneratorStep::Return(13.0));
    assert_eq!(generator.clone().next_step(), GeneratorStep::Return(13.0));
    assert_eq!(generator.return_value(), Some(13.0));
    invalid(std::panic::AssertUnwindSafe(|| { generator.send(1.0); }));
    invalid(std::panic::AssertUnwindSafe(|| { generator.throw_into(recovery()); }));
    generator.close();
    assert_eq!(starts.load(Ordering::SeqCst), 1);
    assert_eq!(closed.load(Ordering::SeqCst), 0);
    let boundary = Generator::new(ReturnBoundary { returned: false });
    invalid(std::panic::AssertUnwindSafe(|| { boundary.next_step(); }));
    invalid(std::panic::AssertUnwindSafe(|| { boundary.next_step(); }));
    assert_eq!(boundary.return_value(), None);
    assert_eq!(boundary.next_step(), GeneratorStep::Return(4.0));
    let closed = Arc::new(AtomicUsize::new(0));
    let early = Generator::new(Machine { value: 1.0, starts: starts.clone(), closed: closed.clone() });
    early.close(); early.close();
    assert_eq!(closed.load(Ordering::SeqCst), 1);
    invalid(std::panic::AssertUnwindSafe(|| { early.next_step(); }));

    let started = Arc::new(tokio::sync::Notify::new());
    let release = Arc::new(tokio::sync::Notify::new());
    let finished = Arc::new(AtomicBool::new(false));
    let closed = Arc::new(AtomicUsize::new(0));
    let iterator = AsyncIteratorValue::new(PendingIterator { started: started.clone(), release: release.clone(), finished: finished.clone(), done: false, closed: closed.clone() });
    let child = iterator.clone();
    let cancellation = CancellationToken::default();
    let child_cancellation = cancellation.clone();
    let pending = tokio::spawn(async move { caught(child.next_with_cancellation(Some(child_cancellation))).await });
    started.notified().await;
    assert!(caught(iterator.next()).await.unwrap_err().is::<ContractViolation>());
    cancellation.cancel();
    assert!(!finished.load(Ordering::SeqCst));
    release.notify_one();
    assert!(pending.await.unwrap().unwrap_err().is::<CancellationException>());
    assert!(finished.load(Ordering::SeqCst), "cancelled source was preempted rather than cooperatively completed");
    release.notify_one();
    assert_eq!(iterator.next().await, None);
    assert_eq!(iterator.next().await, None);
    iterator.close().await;
    assert_eq!(closed.load(Ordering::SeqCst), 0);
    let closed = Arc::new(AtomicUsize::new(0));
    let early = AsyncIteratorValue::new(PendingIterator { started: started.clone(), release: release.clone(), finished: finished.clone(), done: false, closed: closed.clone() });
    assert!(caught(early.close_with_cancellation(Some(cancellation.clone()))).await.unwrap_err().is::<CancellationException>());
    early.close().await; early.close().await;
    assert_eq!(closed.load(Ordering::SeqCst), 1);
    assert_eq!(early.next().await, None);

    let starts = Arc::new(AtomicUsize::new(0));
    let closed = Arc::new(AtomicUsize::new(0));
    let generator = AsyncGenerator::new(AsyncMachine { value: 1.0, starts: starts.clone(), closed: closed.clone() });
    assert!(caught(generator.send(2.0)).await.unwrap_err().is::<ContractViolation>());
    assert!(caught(generator.start_with_cancellation(Some(cancellation))).await.unwrap_err().is::<CancellationException>());
    assert_eq!(generator.return_value(), None);
    assert_eq!(generator.next().await, GeneratorStep::Yield(1.0));
    assert!(caught(generator.start()).await.unwrap_err().is::<ContractViolation>());
    assert!(caught(generator.send(f64::INFINITY)).await.unwrap_err().is::<ContractViolation>());
    assert_eq!(generator.send(2.0).await, GeneratorStep::Yield(3.0));
    assert_eq!(generator.throw_into(recovery()).await, GeneratorStep::Yield(13.0));
    assert_eq!(generator.next().await, GeneratorStep::Return(()));
    assert_eq!(generator.next().await, GeneratorStep::Return(()));
    assert_eq!(generator.return_value(), Some(()));
    assert!(caught(generator.send(1.0)).await.unwrap_err().is::<ContractViolation>());
    assert!(caught(generator.throw_into(recovery())).await.unwrap_err().is::<ContractViolation>());
    generator.close().await;
    assert_eq!(starts.load(Ordering::SeqCst), 1);
    assert_eq!(closed.load(Ordering::SeqCst), 0);
    let early = AsyncGenerator::new(AsyncMachine { value: 1.0, starts, closed: closed.clone() });
    early.close().await; early.close().await;
    assert_eq!(closed.load(Ordering::SeqCst), 1);
    assert!(caught(early.next()).await.unwrap_err().is::<ContractViolation>());
    let forged = AsyncGenerator::new(AsyncMachine { value: f64::NAN, starts: Arc::new(AtomicUsize::new(0)), closed });
    assert!(caught(forged.start()).await.unwrap_err().is::<ContractViolation>());

    let closed = Arc::new(AtomicUsize::new(0));
    let mut origin = IteratorValue::from_source(Sequence { values: vec![1.0,2.0].into_iter(), closed: closed.clone(), calls: Arc::new(AtomicUsize::new(0)) });
    let mut projected = origin.clone().map(|value| value*2.0);
    let mut second_view = origin.clone().map(|value| value*2.0);
    assert_eq!(projected, origin);
    assert_eq!(projected, second_view);
    assert_eq!(origin.next(), Some(1.0));
    assert_eq!(projected.next(), Some(4.0));
    assert_eq!(origin.next(), None);
    assert_eq!(second_view.next(), None);
    projected.close();
    assert_eq!(closed.load(Ordering::SeqCst), 0);
    let mut calls = 0;
    let mut invalid_projection = IteratorValue::new(vec![1.0,2.0].into_iter()).map(move |value| {
        calls += 1; if calls == 1 { f64::NAN } else { value }
    });
    invalid(std::panic::AssertUnwindSafe(|| { invalid_projection.next(); }));
    assert_eq!(invalid_projection.next(), Some(2.0));

    let starts = Arc::new(AtomicUsize::new(0));
    let closed = Arc::new(AtomicUsize::new(0));
    let origin = Generator::new(Machine { value: 1.0, starts: starts.clone(), closed: closed.clone() });
    let sends = Arc::new(AtomicUsize::new(0));
    let returns = Arc::new(AtomicUsize::new(0));
    let send_count = sends.clone();
    let return_count = returns.clone();
    let projected = origin.clone().map(
        |value| value*2.0,
        move |value: f64| { send_count.fetch_add(1,Ordering::SeqCst); value/2.0 },
        move |value| { return_count.fetch_add(1,Ordering::SeqCst); value+100.0 },
    );
    let second_view = origin.clone().map(|value|value*2.0, |value:f64|value/2.0, |value|value+100.0);
    assert_eq!(projected, origin);
    assert_eq!(projected, second_view);
    invalid(std::panic::AssertUnwindSafe(|| { projected.send(4.0); }));
    assert_eq!(sends.load(Ordering::SeqCst), 0);
    assert_eq!(origin.start(), GeneratorStep::Yield(1.0));
    invalid(std::panic::AssertUnwindSafe(|| { projected.start(); }));
    assert_eq!(projected.send(4.0), GeneratorStep::Yield(6.0));
    let after_start = origin.clone().map(|value|value*2.0, |value:f64|value/2.0, |value|value+100.0);
    assert_eq!(after_start.send(2.0), GeneratorStep::Yield(8.0));
    assert_eq!(origin.next_step(), GeneratorStep::Return(4.0));
    invalid(std::panic::AssertUnwindSafe(|| { projected.send(2.0); }));
    assert_eq!(sends.load(Ordering::SeqCst), 1, "send conversion ran before authoritative source eligibility");
    assert_eq!(projected.return_value(), Some(104.0));
    assert_eq!(projected.next_step(), GeneratorStep::Return(104.0));
    assert_eq!(projected.next_step(), GeneratorStep::Return(104.0));
    assert_eq!(returns.load(Ordering::SeqCst), 1, "mapped completion was recomputed");
    assert_eq!(second_view.return_value(), Some(104.0));
    assert_eq!(starts.load(Ordering::SeqCst), 1);
    projected.close();
    assert_eq!(closed.load(Ordering::SeqCst), 0);
    let closed_origin = Generator::new(Machine { value: 1.0, starts: starts.clone(), closed: closed.clone() });
    let closed_projection = closed_origin.clone().map(|value|value, |value:f64|value, |value|value);
    closed_origin.close();
    invalid(std::panic::AssertUnwindSafe(|| { closed_projection.next_step(); }));
    closed_projection.close();
    assert_eq!(closed.load(Ordering::SeqCst), 1);

    let closed = Arc::new(AtomicUsize::new(0));
    let origin = AsyncIteratorValue::new(ImmediateIterator { values: vec![1.0,2.0].into_iter(), closed: closed.clone() });
    let projected = origin.clone().map(|value|value*2.0);
    let second_view = origin.clone().map(|value|value*2.0);
    assert_eq!(projected, origin);
    assert_eq!(projected, second_view);
    assert_eq!(origin.next().await, Some(1.0));
    assert_eq!(projected.next().await, Some(4.0));
    assert_eq!(origin.next().await, None);
    let cancellation = CancellationToken::default();
    cancellation.cancel();
    projected.close_with_cancellation(Some(cancellation.clone())).await;
    assert_eq!(second_view.next().await, None);
    assert_eq!(closed.load(Ordering::SeqCst), 0);

    let starts = Arc::new(AtomicUsize::new(0));
    let closed = Arc::new(AtomicUsize::new(0));
    let origin = AsyncGenerator::new(AsyncMachine { value:1.0, starts:starts.clone(), closed:closed.clone() });
    let sends = Arc::new(AtomicUsize::new(0));
    let send_count = sends.clone();
    let projected = origin.clone().map(|value|value*2.0, move |value:f64| { send_count.fetch_add(1,Ordering::SeqCst); value/2.0 });
    let second_view = origin.clone().map(|value|value*2.0, |value:f64|value/2.0);
    assert_eq!(projected, origin);
    assert_eq!(projected, second_view);
    assert!(caught(projected.send(4.0)).await.unwrap_err().is::<ContractViolation>());
    assert_eq!(sends.load(Ordering::SeqCst), 0);
    assert_eq!(origin.start().await, GeneratorStep::Yield(1.0));
    assert!(caught(projected.start()).await.unwrap_err().is::<ContractViolation>());
    assert_eq!(projected.send(4.0).await, GeneratorStep::Yield(6.0));
    let after_start = origin.clone().map(|value|value*2.0, |value:f64|value/2.0);
    assert_eq!(after_start.send(2.0).await, GeneratorStep::Yield(8.0));
    assert_eq!(origin.next().await, GeneratorStep::Return(()));
    assert!(caught(projected.send(2.0)).await.unwrap_err().is::<ContractViolation>());
    assert_eq!(sends.load(Ordering::SeqCst), 1);
    assert_eq!(projected.return_value(), Some(()));
    assert_eq!(projected.next().await, GeneratorStep::Return(()));
    assert_eq!(second_view.next().await, GeneratorStep::Return(()));
    projected.close_with_cancellation(Some(cancellation)).await;
    assert_eq!(starts.load(Ordering::SeqCst), 1);
    assert_eq!(closed.load(Ordering::SeqCst), 0);
}
fn main() {
    tokio::runtime::Builder::new_multi_thread().worker_threads(2).enable_all().build().unwrap().block_on(async {
        tokio::time::timeout(std::time::Duration::from_secs(10), exercise()).await.unwrap();
    });
}"#,
    );
}
