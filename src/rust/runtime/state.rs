pub struct ReadField<'a, T>(tokio::sync::RwLockReadGuard<'a, Option<T>>);
impl<'a, T> ReadField<'a, T> {
    pub(crate) fn new(guard: tokio::sync::RwLockReadGuard<'a, Option<T>>) -> Self {
        Self(guard)
    }
}
impl<T> std::ops::Deref for ReadField<'_, T> {
    type Target = T;
    fn deref(&self) -> &T {
        self.0.as_ref().expect("initialized canonical state")
    }
}

#[doc(hidden)]
pub struct StateGate {
    lock: Arc<tokio::sync::Mutex<()>>,
    frozen: bool,
}
impl StateGate {
    pub(crate) fn new(frozen: bool) -> Self {
        Self {
            lock: Arc::new(tokio::sync::Mutex::new(())),
            frozen,
        }
    }
}
#[derive(Clone, Copy)]
struct MutationContext {
    id: usize,
    modifies: &'static [&'static str],
    task: Option<tokio::task::Id>,
}
tokio::task_local! {static MUTATION_CONTEXT:MutationContext;}
thread_local! {static SYNC_MUTATION:std::cell::RefCell<Option<MutationContext>>=const{std::cell::RefCell::new(None)};}
fn mutation_context() -> Option<MutationContext> {
    MUTATION_CONTEXT
        .try_with(|v| *v)
        .ok()
        .or_else(|| SYNC_MUTATION.with(|v| *v.borrow()))
}
#[doc(hidden)]
pub struct StateLease {
    context: MutationContext,
    _guard: Option<tokio::sync::OwnedMutexGuard<()>>,
}
fn nested_lease(id: usize, modifies: &'static [&'static str]) -> Option<StateLease> {
    let parent = mutation_context()?;
    if parent.id != id {
        return None;
    }
    if parent.task != tokio::task::try_id() {
        violation("resource", "guard", "lease crosses task boundary")
    }
    Some(StateLease {
        context: MutationContext {
            id,
            modifies,
            task: parent.task,
        },
        _guard: None,
    })
}
#[doc(hidden)]
pub(crate) fn __cott_state_enter(
    gate: &StateGate,
    id: usize,
    modifies: &'static [&'static str],
) -> StateLease {
    if gate.frozen && !modifies.is_empty() {
        violation("resource", "guard", "immutable old-state snapshot")
    }
    if let Some(lease) = nested_lease(id, modifies) {
        return lease;
    }
    let guard = gate
        .lock
        .clone()
        .try_lock_owned()
        .unwrap_or_else(|_| violation("resource", "guard", "overlapping operation lease"));
    StateLease {
        context: MutationContext {
            id,
            modifies,
            task: tokio::task::try_id(),
        },
        _guard: Some(guard),
    }
}
#[doc(hidden)]
pub(crate) async fn __cott_state_enter_async(
    gate: &StateGate,
    id: usize,
    modifies: &'static [&'static str],
) -> StateLease {
    if gate.frozen && !modifies.is_empty() {
        violation("resource", "guard", "immutable old-state snapshot")
    }
    if let Some(lease) = nested_lease(id, modifies) {
        return lease;
    }
    let guard = gate.lock.clone().lock_owned().await;
    StateLease {
        context: MutationContext {
            id,
            modifies,
            task: tokio::task::try_id(),
        },
        _guard: Some(guard),
    }
}
#[doc(hidden)]
pub(crate) fn __cott_with_state<R>(lease: StateLease, body: impl FnOnce() -> R) -> R {
    struct Restore(Option<MutationContext>);
    impl Drop for Restore {
        fn drop(&mut self) {
            SYNC_MUTATION.with(|v| *v.borrow_mut() = self.0.take());
        }
    }
    let prior = SYNC_MUTATION.with(|v| v.borrow_mut().replace(lease.context));
    let _restore = Restore(prior);
    if MUTATION_CONTEXT.try_with(|_| ()).is_ok() {
        MUTATION_CONTEXT.sync_scope(lease.context, body)
    } else {
        body()
    }
}
#[doc(hidden)]
pub(crate) async fn __cott_with_state_async<F: Future>(lease: StateLease, future: F) -> F::Output {
    MUTATION_CONTEXT.scope(lease.context, future).await
}
#[doc(hidden)]
pub(crate) fn __cott_state_write(id: usize, field: &str) {
    let context =
        mutation_context().unwrap_or_else(|| violation("resource", "mutation", "no active lease"));
    if context.id != id
        || context.task != tokio::task::try_id()
        || !context.modifies.contains(&field)
    {
        violation("resource", "modifies", field)
    }
}

thread_local! {
 static VALIDATING_STATE:std::cell::RefCell<std::collections::BTreeSet<usize>>=const{std::cell::RefCell::new(std::collections::BTreeSet::new())};
 static COMPARING_STATE:std::cell::RefCell<std::collections::BTreeSet<(usize,usize)>>=const{std::cell::RefCell::new(std::collections::BTreeSet::new())};
 static SNAPSHOT_STATE:std::cell::RefCell<Option<std::collections::BTreeMap<usize,Box<dyn std::any::Any>>>>=const{std::cell::RefCell::new(None)};
}
#[doc(hidden)]
pub(crate) fn __cott_validate_state(id: usize, body: impl FnOnce()) {
    if !VALIDATING_STATE.with(|v| v.borrow_mut().insert(id)) {
        return;
    }
    struct Remove(usize);
    impl Drop for Remove {
        fn drop(&mut self) {
            VALIDATING_STATE.with(|v| v.borrow_mut().remove(&self.0));
        }
    }
    let _remove = Remove(id);
    body()
}
#[doc(hidden)]
pub(crate) fn __cott_state_equal(a: usize, b: usize, body: impl FnOnce() -> bool) -> bool {
    if a == b {
        return true;
    }
    if !COMPARING_STATE.with(|v| v.borrow_mut().insert((a, b))) {
        return true;
    }
    struct Remove(usize, usize);
    impl Drop for Remove {
        fn drop(&mut self) {
            COMPARING_STATE.with(|v| v.borrow_mut().remove(&(self.0, self.1)));
        }
    }
    let _remove = Remove(a, b);
    body()
}
#[doc(hidden)]
pub(crate) fn __cott_snapshot_state<T: Clone + 'static>(
    id: usize,
    create: impl FnOnce() -> T,
    fill: impl FnOnce(&T),
) -> T {
    let root = SNAPSHOT_STATE.with(|v| {
        let mut cache = v.borrow_mut();
        if cache.is_none() {
            *cache = Some(std::collections::BTreeMap::new());
            true
        } else {
            false
        }
    });
    struct Clear(bool);
    impl Drop for Clear {
        fn drop(&mut self) {
            if self.0 {
                SNAPSHOT_STATE.with(|v| *v.borrow_mut() = None);
            }
        }
    }
    let _clear = Clear(root);
    if let Some(value) = SNAPSHOT_STATE.with(|v| {
        v.borrow().as_ref().and_then(|c| c.get(&id)).map(|v| {
            v.downcast_ref::<T>()
                .expect("canonical snapshot identity")
                .clone()
        })
    }) {
        return value;
    }
    let value = create();
    SNAPSHOT_STATE.with(|v| {
        v.borrow_mut()
            .as_mut()
            .expect("snapshot context")
            .insert(id, Box::new(value.clone()));
    });
    fill(&value);
    value
}
