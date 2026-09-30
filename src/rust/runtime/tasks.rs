#[derive(Clone, Debug, PartialEq, Eq)]
pub struct CancellationException {
    pub reason: Arc<str>,
}
impl std::fmt::Display for CancellationException {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        write!(f, "cancelled: {}", self.reason)
    }
}
impl std::error::Error for CancellationException {}

#[derive(Default)]
struct CancellationData {
    reason: Option<Arc<str>>,
    children: Vec<std::sync::Weak<CancellationState>>,
}
#[derive(Default)]
struct CancellationState {
    data: std::sync::Mutex<CancellationData>,
    notify: tokio::sync::Notify,
}
#[derive(Clone, Default)]
pub struct CancellationToken(Arc<CancellationState>);
impl CancellationToken {
    pub fn child_token(&self) -> Self {
        let child = Self::default();
        let mut parent = self.0.data.lock().expect("cancellation state");
        if let Some(reason) = &parent.reason {
            child.cancel_with_reason(reason.clone());
        } else {
            parent.children.push(Arc::downgrade(&child.0));
        }
        child
    }
    pub fn cancel(&self) {
        self.cancel_with_reason(Arc::<str>::from("cancelled"));
    }
    pub fn cancel_with_reason(&self, reason: impl Into<Arc<str>>) {
        let reason = reason.into();
        let children = {
            let mut data = self.0.data.lock().expect("cancellation state");
            if data.reason.is_some() {
                return;
            }
            data.reason = Some(reason.clone());
            std::mem::take(&mut data.children)
        };
        self.0.notify.notify_waiters();
        for child in children {
            if let Some(child) = child.upgrade() {
                Self(child).cancel_with_reason(reason.clone());
            }
        }
    }
    pub fn is_cancelled(&self) -> bool {
        self.0
            .data
            .lock()
            .expect("cancellation state")
            .reason
            .is_some()
    }
    pub fn reason(&self) -> Option<Arc<str>> {
        self.0
            .data
            .lock()
            .expect("cancellation state")
            .reason
            .clone()
    }
    pub fn check(&self) {
        if let Some(reason) = self.reason() {
            std::panic::panic_any(CancellationException { reason });
        }
    }
    pub async fn cancelled(&self) {
        loop {
            let mut notified = std::pin::pin!(self.0.notify.notified());
            notified.as_mut().enable();
            if self.is_cancelled() {
                return;
            }
            notified.await;
        }
    }
}

/// Preserves an arbitrary panic payload when multiple task observers inspect the same failure.
#[derive(Clone)]
pub struct TaskFailure(Arc<std::sync::Mutex<Box<dyn std::any::Any + Send>>>);
impl std::fmt::Debug for TaskFailure {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str("TaskFailure")
    }
}
impl TaskFailure {
    pub fn with_payload<R>(&self, inspect: impl FnOnce(&(dyn std::any::Any + Send)) -> R) -> R {
        let payload = self.0.lock().unwrap_or_else(|error| error.into_inner());
        inspect(payload.as_ref())
    }
    fn rethrow(&self) -> ! {
        let payload = self.0.lock().unwrap_or_else(|error| error.into_inner());
        let contract = payload.downcast_ref::<ContractViolation>().cloned();
        let cancellation = payload.downcast_ref::<CancellationException>().cloned();
        drop(payload);
        if let Some(error) = contract {
            std::panic::panic_any(error);
        }
        if let Some(error) = cancellation {
            std::panic::panic_any(error);
        }
        std::panic::panic_any(self.clone());
    }
}
async fn task_catch<F: Future>(future: F) -> Result<F::Output, Box<dyn std::any::Any + Send>> {
    let mut future = std::pin::pin!(future);
    std::future::poll_fn(|cx| {
        match std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| future.as_mut().poll(cx))) {
            Ok(poll) => poll.map(Ok),
            Err(error) => std::task::Poll::Ready(Err(error)),
        }
    })
    .await
}
#[derive(Default)]
struct TaskCompletion {
    done: std::sync::atomic::AtomicBool,
    notify: tokio::sync::Notify,
}
impl TaskCompletion {
    async fn wait(&self) {
        loop {
            let mut notified = std::pin::pin!(self.notify.notified());
            notified.as_mut().enable();
            if self.done.load(std::sync::atomic::Ordering::Acquire) {
                return;
            }
            notified.await;
        }
    }
}
struct TaskState<T> {
    output: std::sync::Mutex<Option<Result<T, TaskFailure>>>,
    completion: Arc<TaskCompletion>,
}
pub struct Task<T> {
    state: Arc<TaskState<T>>,
    token: CancellationToken,
}
impl<T> Clone for Task<T> {
    fn clone(&self) -> Self {
        Self {
            state: self.state.clone(),
            token: self.token.clone(),
        }
    }
}
impl<T> Task<T> {
    pub fn cancel(&self) {
        self.token.cancel_with_reason("task cancelled");
    }
    pub fn cancel_with_reason(&self, reason: impl Into<Arc<str>>) {
        self.token.cancel_with_reason(reason);
    }
    pub fn cancellation_token(&self) -> CancellationToken {
        self.token.clone()
    }
    pub async fn join(&self) {
        self.state.completion.wait().await;
        let failure = self
            .state
            .output
            .lock()
            .expect("task output")
            .as_ref()
            .and_then(|value| value.as_ref().err())
            .cloned();
        if let Some(failure) = failure {
            failure.rethrow();
        }
    }
}
impl<T: Value + Clone> Task<T> {
    pub async fn result(&self) -> T {
        self.state.completion.wait().await;
        let output = self
            .state
            .output
            .lock()
            .expect("task output")
            .as_ref()
            .expect("completed task output")
            .clone();
        match output {
            Ok(value) => value,
            Err(failure) => failure.rethrow(),
        }
    }
}
#[derive(Default)]
struct ScopeData {
    closed: bool,
    tasks: Vec<Arc<TaskCompletion>>,
    failures: Vec<TaskFailure>,
}
struct ScopeState {
    data: std::sync::Mutex<ScopeData>,
    token: CancellationToken,
}
impl Drop for ScopeState {
    fn drop(&mut self) {
        self.token.cancel_with_reason("task scope dropped");
    }
}
#[derive(Clone)]
pub struct TaskScope(Arc<ScopeState>);
impl Default for TaskScope {
    fn default() -> Self {
        Self::new(None)
    }
}
impl TaskScope {
    pub fn new(parent: Option<CancellationToken>) -> Self {
        let token = parent.map_or_else(CancellationToken::default, |token| token.child_token());
        Self(Arc::new(ScopeState {
            data: std::sync::Mutex::new(ScopeData::default()),
            token,
        }))
    }
    pub fn cancellation_token(&self) -> CancellationToken {
        self.0.token.clone()
    }
    pub fn spawn<T, F, Fut>(&self, operation: F) -> Task<T>
    where
        T: Value + Clone + Send + Sync + 'static,
        F: FnOnce(CancellationToken) -> Fut + Send + 'static,
        Fut: Future<Output = T> + Send + 'static,
    {
        let mut data = self.0.data.lock().expect("task scope");
        if data.closed {
            drop(data);
            violation("task", "task-lifecycle", "task scope is closed");
        }
        if tokio::runtime::Handle::try_current().is_err() {
            drop(data);
            violation("task", "task-lifecycle", "spawn requires a Tokio runtime");
        }
        let token = self.0.token.child_token();
        let completion = Arc::new(TaskCompletion::default());
        let state = Arc::new(TaskState {
            output: std::sync::Mutex::new(None),
            completion: completion.clone(),
        });
        data.tasks.push(completion.clone());
        drop(data);
        let ticket = Task {
            state: state.clone(),
            token: token.clone(),
        };
        let scope = Arc::downgrade(&self.0);
        let observer = ASYNC_OBSERVER.try_with(Arc::clone).ok();
        tokio::spawn(async move {
            let operation = async move {
                token.check();
                let value = operation(token).await;
                value.validate();
                value
            };
            // Tokio task locals do not transfer to spawned tasks. Transfer evidence only, not mutation authority.
            let outcome = if let Some(observer) = observer {
                ASYNC_OBSERVER.scope(observer, task_catch(operation)).await
            } else {
                task_catch(operation).await
            };
            let outcome =
                outcome.map_err(|error| TaskFailure(Arc::new(std::sync::Mutex::new(error))));
            if let Err(failure) = &outcome {
                if let Some(scope) = scope.upgrade() {
                    scope
                        .data
                        .lock()
                        .expect("task scope")
                        .failures
                        .push(failure.clone());
                }
            }
            *state.output.lock().expect("task output") = Some(outcome);
            completion
                .done
                .store(true, std::sync::atomic::Ordering::Release);
            completion.notify.notify_waiters();
        });
        ticket
    }
    pub fn cancel(&self) {
        self.0.token.cancel_with_reason("task scope cancelled");
    }
    pub fn cancel_with_reason(&self, reason: impl Into<Arc<str>>) {
        self.0.token.cancel_with_reason(reason);
    }
    pub async fn join(&self) {
        let tasks = self.0.data.lock().expect("task scope").tasks.clone();
        for task in tasks {
            task.wait().await;
        }
        let failure = self
            .0
            .data
            .lock()
            .expect("task scope")
            .failures
            .first()
            .cloned();
        if let Some(failure) = failure {
            failure.rethrow();
        }
    }
    pub async fn close(&self, cancel_owned: bool) {
        {
            let mut data = self.0.data.lock().expect("task scope");
            if data.closed {
                return;
            }
            data.closed = true;
        }
        if cancel_owned {
            self.0.token.cancel_with_reason("task scope closed");
        }
        self.join().await;
    }
    async fn finish(&self) {
        // A dropped/concurrent close future cannot bypass run's structured drain.
        self.0.data.lock().expect("task scope").closed = true;
        self.join().await;
    }
    pub async fn run<T, F, Fut>(body: F, parent: Option<CancellationToken>) -> T
    where
        T: Value,
        F: FnOnce(TaskScope) -> Fut,
        Fut: Future<Output = T>,
    {
        let scope = Self::new(parent);
        let outcome = task_catch(async {
            let value = body(scope.clone()).await;
            value.validate();
            scope.finish().await;
            value
        })
        .await;
        match outcome {
            Ok(value) => value,
            Err(error) => {
                scope.cancel_with_reason("task scope body failed");
                let _ = task_catch(scope.finish()).await;
                std::panic::resume_unwind(error)
            }
        }
    }
}
pub struct Lease<T> {
    inner: Arc<tokio::sync::Mutex<T>>,
}
impl<T> Clone for Lease<T> {
    fn clone(&self) -> Self {
        Self {
            inner: self.inner.clone(),
        }
    }
}
impl<T> Lease<T> {
    pub fn new(value: T) -> Self {
        Self {
            inner: Arc::new(tokio::sync::Mutex::new(value)),
        }
    }
    pub async fn acquire(&self) -> tokio::sync::OwnedMutexGuard<T> {
        self.inner.clone().lock_owned().await
    }
    pub async fn acquire_with_cancellation(
        &self,
        cancellation: &CancellationToken,
    ) -> tokio::sync::OwnedMutexGuard<T> {
        cancellation.check();
        let mut acquired = std::pin::pin!(self.inner.clone().lock_owned());
        let mut cancelled = std::pin::pin!(cancellation.cancelled());
        let lease = std::future::poll_fn(|cx| {
            if cancelled.as_mut().poll(cx).is_ready() {
                cancellation.check();
            }
            acquired.as_mut().poll(cx)
        })
        .await;
        cancellation.check();
        lease
    }
}
