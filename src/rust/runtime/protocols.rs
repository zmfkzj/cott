pub type BoxFuture<'a, T> = Pin<Box<dyn Future<Output = T> + Send + 'a>>;

pub type ProtocolError = Box<dyn std::error::Error + Send + Sync + 'static>;
#[derive(Clone, Copy, PartialEq, Eq)]
enum ProtocolState {
    New,
    Active,
    Done,
    Closed,
}
fn protocol_lock<'a, T>(
    lock: &'a std::sync::Mutex<T>,
    phase: &str,
) -> std::sync::MutexGuard<'a, T> {
    match lock.try_lock() {
        Ok(guard) => guard,
        Err(std::sync::TryLockError::Poisoned(error)) => error.into_inner(),
        Err(std::sync::TryLockError::WouldBlock) => {
            violation("protocol", phase, "concurrent protocol operation")
        }
    }
}
fn protocol_cancel(cancellation: &Option<CancellationToken>) {
    if let Some(cancellation) = cancellation {
        cancellation.check();
    }
}

pub trait IteratorSource<T>: Send {
    fn next(&mut self) -> Option<T>;
    fn close(&mut self);
}
struct StandardIterator<I>(Option<I>);
impl<T, I: Iterator<Item = T> + Send> IteratorSource<T> for StandardIterator<I> {
    fn next(&mut self) -> Option<T> {
        self.0.as_mut().and_then(Iterator::next)
    }
    fn close(&mut self) {
        self.0.take();
    }
}
struct IteratorState<T> {
    source: Box<dyn IteratorSource<T>>,
    lifecycle: ProtocolState,
}
struct IteratorNative<T>(Arc<std::sync::Mutex<IteratorState<T>>>);
impl<T> IteratorNative<T> {
    pub fn new<I: Iterator<Item = T> + Send + 'static>(value: I) -> Self {
        Self::from_source(StandardIterator(Some(value)))
    }
    pub fn from_source<I: IteratorSource<T> + 'static>(source: I) -> Self {
        Self(Arc::new(std::sync::Mutex::new(IteratorState {
            source: Box::new(source),
            lifecycle: ProtocolState::New,
        })))
    }
    pub fn close(&self) {
        let mut state = protocol_lock(&self.0, "iterator-lifecycle");
        if matches!(state.lifecycle, ProtocolState::Done | ProtocolState::Closed) {
            return;
        }
        state.source.close();
        state.lifecycle = ProtocolState::Closed;
    }
}
impl<T: Value> IteratorNative<T> {
    fn next_value(&self) -> Option<T> {
        let mut state = protocol_lock(&self.0, "iterator-lifecycle");
        if matches!(state.lifecycle, ProtocolState::Done | ProtocolState::Closed) {
            return None;
        }
        let result = state.source.next();
        if let Some(value) = &result {
            state.lifecycle = ProtocolState::Active;
            value.validate();
        } else {
            state.lifecycle = ProtocolState::Done;
        }
        result
    }
}
impl<T> Clone for IteratorNative<T> {
    fn clone(&self) -> Self {
        Self(self.0.clone())
    }
}
trait IteratorProjection<T>: Send + Sync {
    fn identity(&self) -> usize;
    fn next_value(&self) -> Option<T>;
    fn close(&self);
}
enum IteratorBackend<T> {
    Native(IteratorNative<T>),
    Projection(Arc<dyn IteratorProjection<T>>),
}
pub struct IteratorValue<T>(IteratorBackend<T>);
impl<T> IteratorValue<T> {
    pub fn new<I: Iterator<Item = T> + Send + 'static>(value: I) -> Self {
        Self(IteratorBackend::Native(IteratorNative::new(value)))
    }
    pub fn from_source<I: IteratorSource<T> + 'static>(source: I) -> Self {
        Self(IteratorBackend::Native(IteratorNative::from_source(source)))
    }
    fn identity(&self) -> usize {
        match &self.0 {
            IteratorBackend::Native(source) => Arc::as_ptr(&source.0) as usize,
            IteratorBackend::Projection(source) => source.identity(),
        }
    }
    pub fn close(&self) {
        match &self.0 {
            IteratorBackend::Native(source) => source.close(),
            IteratorBackend::Projection(source) => source.close(),
        }
    }
}
impl<T: Value> IteratorValue<T> {
    fn next_value(&self) -> Option<T> {
        match &self.0 {
            IteratorBackend::Native(source) => source.next_value(),
            IteratorBackend::Projection(source) => source.next_value(),
        }
    }
}
impl<T: Value> Iterator for IteratorValue<T> {
    type Item = T;
    fn next(&mut self) -> Option<T> {
        self.next_value()
    }
}
struct IteratorMap<T, D, F> {
    source: IteratorValue<T>,
    map: std::sync::Mutex<F>,
    marker: std::marker::PhantomData<fn() -> D>,
}
impl<T, D, F> IteratorProjection<D> for IteratorMap<T, D, F>
where
    T: Value + Clone + Send + Sync + 'static,
    D: Value + Clone + Send + Sync + 'static,
    F: FnMut(T) -> D + Send + 'static,
{
    fn identity(&self) -> usize {
        self.source.identity()
    }
    fn next_value(&self) -> Option<D> {
        let mut map = protocol_lock(&self.map, "iterator-lifecycle");
        self.source.next_value().map(|value| {
            let value = map(value);
            value.validate();
            value
        })
    }
    fn close(&self) {
        let _map = protocol_lock(&self.map, "iterator-lifecycle");
        self.source.close();
    }
}
impl<T: Value + Clone + Send + Sync + 'static> IteratorValue<T> {
    pub fn map<D, F>(self, map: F) -> IteratorValue<D>
    where
        D: Value + Clone + Send + Sync + 'static,
        F: FnMut(T) -> D + Send + 'static,
    {
        IteratorValue(IteratorBackend::Projection(Arc::new(IteratorMap {
            source: self,
            map: std::sync::Mutex::new(map),
            marker: std::marker::PhantomData,
        })))
    }
}
impl<T> Clone for IteratorValue<T> {
    fn clone(&self) -> Self {
        Self(match &self.0 {
            IteratorBackend::Native(source) => IteratorBackend::Native(source.clone()),
            IteratorBackend::Projection(source) => IteratorBackend::Projection(source.clone()),
        })
    }
}
impl<T> std::fmt::Debug for IteratorValue<T> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str("IteratorValue")
    }
}
impl<T> PartialEq for IteratorValue<T> {
    fn eq(&self, other: &Self) -> bool {
        self.identity() == other.identity()
    }
}
impl<T> Eq for IteratorValue<T> {}

pub trait AsyncIterator<T>: Send {
    fn next(&mut self, cancellation: Option<CancellationToken>) -> BoxFuture<'_, Option<T>>;
    fn close(&mut self, cancellation: Option<CancellationToken>) -> BoxFuture<'_, ()>;
}
struct AsyncIteratorFunctions<N, C>(N, C);
impl<T, N, C> AsyncIterator<T> for AsyncIteratorFunctions<N, C>
where
    N: FnMut(Option<CancellationToken>) -> BoxFuture<'static, Option<T>> + Send,
    C: FnMut(Option<CancellationToken>) -> BoxFuture<'static, ()> + Send,
{
    fn next(&mut self, cancellation: Option<CancellationToken>) -> BoxFuture<'_, Option<T>> {
        (self.0)(cancellation)
    }
    fn close(&mut self, cancellation: Option<CancellationToken>) -> BoxFuture<'_, ()> {
        (self.1)(cancellation)
    }
}
impl<T> AsyncIteratorValue<T> {
    pub fn from_fn<N, C>(next: N, close: C) -> Self
    where
        N: FnMut(Option<CancellationToken>) -> BoxFuture<'static, Option<T>> + Send + 'static,
        C: FnMut(Option<CancellationToken>) -> BoxFuture<'static, ()> + Send + 'static,
    {
        Self::new(AsyncIteratorFunctions(next, close))
    }
}
struct AsyncIteratorState<T> {
    source: Box<dyn AsyncIterator<T>>,
    lifecycle: ProtocolState,
}
struct AsyncIteratorNative<T>(Arc<tokio::sync::Mutex<AsyncIteratorState<T>>>);
impl<T> AsyncIteratorNative<T> {
    pub fn new<I: AsyncIterator<T> + 'static>(source: I) -> Self {
        Self(Arc::new(tokio::sync::Mutex::new(AsyncIteratorState {
            source: Box::new(source),
            lifecycle: ProtocolState::New,
        })))
    }
    pub async fn close(&self) {
        self.close_with_cancellation(None).await;
    }
    pub async fn close_with_cancellation(&self, cancellation: Option<CancellationToken>) {
        let mut state = self.0.try_lock().unwrap_or_else(|_| {
            violation(
                "protocol",
                "async-lifecycle",
                "concurrent protocol operation",
            )
        });
        if matches!(state.lifecycle, ProtocolState::Done | ProtocolState::Closed) {
            return;
        }
        protocol_cancel(&cancellation);
        state.source.close(cancellation).await;
        state.lifecycle = ProtocolState::Closed;
    }
}
impl<T: Value> AsyncIteratorNative<T> {
    pub async fn next(&self) -> Option<T> {
        self.next_with_cancellation(None).await
    }
    pub async fn next_with_cancellation(
        &self,
        cancellation: Option<CancellationToken>,
    ) -> Option<T> {
        let mut state = self.0.try_lock().unwrap_or_else(|_| {
            violation(
                "protocol",
                "async-lifecycle",
                "concurrent protocol operation",
            )
        });
        protocol_cancel(&cancellation);
        if matches!(state.lifecycle, ProtocolState::Done | ProtocolState::Closed) {
            return None;
        }
        let result = state.source.next(cancellation.clone()).await;
        protocol_cancel(&cancellation);
        if let Some(value) = &result {
            state.lifecycle = ProtocolState::Active;
            value.validate();
        } else {
            state.lifecycle = ProtocolState::Done;
        }
        result
    }
}
impl<T> Clone for AsyncIteratorNative<T> {
    fn clone(&self) -> Self {
        Self(self.0.clone())
    }
}
trait AsyncIteratorProjection<T>: Send + Sync {
    fn identity(&self) -> usize;
    fn next(&self, cancellation: Option<CancellationToken>) -> BoxFuture<'_, Option<T>>;
    fn close(&self, cancellation: Option<CancellationToken>) -> BoxFuture<'_, ()>;
}
enum AsyncIteratorBackend<T> {
    Native(AsyncIteratorNative<T>),
    Projection(Arc<dyn AsyncIteratorProjection<T>>),
}
pub struct AsyncIteratorValue<T>(AsyncIteratorBackend<T>);
impl<T> AsyncIteratorValue<T> {
    pub fn new<I: AsyncIterator<T> + 'static>(source: I) -> Self {
        Self(AsyncIteratorBackend::Native(AsyncIteratorNative::new(
            source,
        )))
    }
    fn identity(&self) -> usize {
        match &self.0 {
            AsyncIteratorBackend::Native(source) => Arc::as_ptr(&source.0) as usize,
            AsyncIteratorBackend::Projection(source) => source.identity(),
        }
    }
    pub async fn close(&self) {
        match &self.0 {
            AsyncIteratorBackend::Native(source) => source.close().await,
            AsyncIteratorBackend::Projection(source) => source.close(None).await,
        }
    }
    pub async fn close_with_cancellation(&self, cancellation: Option<CancellationToken>) {
        match &self.0 {
            AsyncIteratorBackend::Native(source) => {
                source.close_with_cancellation(cancellation).await
            }
            AsyncIteratorBackend::Projection(source) => source.close(cancellation).await,
        }
    }
}
impl<T: Value> AsyncIteratorValue<T> {
    pub async fn next(&self) -> Option<T> {
        match &self.0 {
            AsyncIteratorBackend::Native(source) => source.next().await,
            AsyncIteratorBackend::Projection(source) => source.next(None).await,
        }
    }
    pub async fn next_with_cancellation(
        &self,
        cancellation: Option<CancellationToken>,
    ) -> Option<T> {
        match &self.0 {
            AsyncIteratorBackend::Native(source) => {
                source.next_with_cancellation(cancellation).await
            }
            AsyncIteratorBackend::Projection(source) => source.next(cancellation).await,
        }
    }
}
struct AsyncIteratorMap<T, D, F> {
    source: AsyncIteratorValue<T>,
    map: tokio::sync::Mutex<F>,
    marker: std::marker::PhantomData<fn() -> D>,
}
impl<T, D, F> AsyncIteratorProjection<D> for AsyncIteratorMap<T, D, F>
where
    T: Value + Clone + Send + Sync + 'static,
    D: Value + Clone + Send + Sync + 'static,
    F: FnMut(T) -> D + Send + 'static,
{
    fn identity(&self) -> usize {
        self.source.identity()
    }
    fn next(&self, cancellation: Option<CancellationToken>) -> BoxFuture<'_, Option<D>> {
        Box::pin(async move {
            let mut map = self.map.try_lock().unwrap_or_else(|_| {
                violation(
                    "protocol",
                    "async-lifecycle",
                    "concurrent protocol operation",
                )
            });
            let value = self
                .source
                .next_with_cancellation(cancellation.clone())
                .await
                .map(|value| {
                    let value = map(value);
                    value.validate();
                    value
                });
            protocol_cancel(&cancellation);
            value
        })
    }
    fn close(&self, cancellation: Option<CancellationToken>) -> BoxFuture<'_, ()> {
        Box::pin(async move {
            let _map = self.map.try_lock().unwrap_or_else(|_| {
                violation(
                    "protocol",
                    "async-lifecycle",
                    "concurrent protocol operation",
                )
            });
            self.source.close_with_cancellation(cancellation).await;
        })
    }
}
impl<T: Value + Clone + Send + Sync + 'static> AsyncIteratorValue<T> {
    pub fn map<D, F>(self, map: F) -> AsyncIteratorValue<D>
    where
        D: Value + Clone + Send + Sync + 'static,
        F: FnMut(T) -> D + Send + 'static,
    {
        AsyncIteratorValue(AsyncIteratorBackend::Projection(Arc::new(
            AsyncIteratorMap {
                source: self,
                map: tokio::sync::Mutex::new(map),
                marker: std::marker::PhantomData,
            },
        )))
    }
}
impl<T> Clone for AsyncIteratorValue<T> {
    fn clone(&self) -> Self {
        Self(match &self.0 {
            AsyncIteratorBackend::Native(source) => AsyncIteratorBackend::Native(source.clone()),
            AsyncIteratorBackend::Projection(source) => {
                AsyncIteratorBackend::Projection(source.clone())
            }
        })
    }
}
impl<T> std::fmt::Debug for AsyncIteratorValue<T> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str("AsyncIteratorValue")
    }
}
impl<T> PartialEq for AsyncIteratorValue<T> {
    fn eq(&self, other: &Self) -> bool {
        self.identity() == other.identity()
    }
}
impl<T> Eq for AsyncIteratorValue<T> {}

#[derive(Clone, Debug, PartialEq, Eq)]
pub enum GeneratorStep<Y, R> {
    Yield(Y),
    Return(R),
}
pub trait GeneratorProtocol<Y, S, R>: Send {
    fn start(&mut self) -> GeneratorStep<Y, R>;
    fn next(&mut self) -> GeneratorStep<Y, R>;
    fn send(&mut self, value: S) -> GeneratorStep<Y, R>;
    fn raise(&mut self, error: ProtocolError) -> GeneratorStep<Y, R>;
    fn close(&mut self);
}
#[derive(Debug)]
pub enum GeneratorRequest<S> {
    Start,
    Next,
    Send(S),
    Raise(ProtocolError),
}
struct GeneratorFunctions<F, C>(F, C);
impl<Y, S, R, F, C> GeneratorProtocol<Y, S, R> for GeneratorFunctions<F, C>
where
    F: FnMut(GeneratorRequest<S>) -> GeneratorStep<Y, R> + Send,
    C: FnMut() + Send,
{
    fn start(&mut self) -> GeneratorStep<Y, R> { (self.0)(GeneratorRequest::Start) }
    fn next(&mut self) -> GeneratorStep<Y, R> { (self.0)(GeneratorRequest::Next) }
    fn send(&mut self, value: S) -> GeneratorStep<Y, R> { (self.0)(GeneratorRequest::Send(value)) }
    fn raise(&mut self, error: ProtocolError) -> GeneratorStep<Y, R> { (self.0)(GeneratorRequest::Raise(error)) }
    fn close(&mut self) { (self.1)(); }
}
impl<Y, S, R> Generator<Y, S, R> {
    pub fn from_fn<F, C>(step: F, close: C) -> Self
    where
        F: FnMut(GeneratorRequest<S>) -> GeneratorStep<Y, R> + Send + 'static,
        C: FnMut() + Send + 'static,
    {
        Self::new(GeneratorFunctions(step, close))
    }
}
struct GeneratorState<Y, S, R> {
    source: Box<dyn GeneratorProtocol<Y, S, R>>,
    lifecycle: ProtocolState,
}
struct GeneratorCore<Y, S, R> {
    state: std::sync::Mutex<GeneratorState<Y, S, R>>,
    completion: std::sync::Mutex<Option<R>>,
}
struct GeneratorNative<Y, S, R>(Arc<GeneratorCore<Y, S, R>>);
impl<Y, S, R> GeneratorNative<Y, S, R> {
    pub fn new<G: GeneratorProtocol<Y, S, R> + 'static>(source: G) -> Self {
        Self(Arc::new(GeneratorCore {
            state: std::sync::Mutex::new(GeneratorState {
                source: Box::new(source),
                lifecycle: ProtocolState::New,
            }),
            completion: std::sync::Mutex::new(None),
        }))
    }
    pub fn close(&self) {
        let mut state = protocol_lock(&self.0.state, "generator-lifecycle");
        if matches!(state.lifecycle, ProtocolState::Done | ProtocolState::Closed) {
            return;
        }
        state.source.close();
        state.lifecycle = ProtocolState::Closed;
    }
}
impl<Y: Value, S: Value, R: Value + Clone> GeneratorNative<Y, S, R> {
    fn validate_step(
        &self,
        state: &mut GeneratorState<Y, S, R>,
        step: GeneratorStep<Y, R>,
    ) -> GeneratorStep<Y, R> {
        match &step {
            GeneratorStep::Yield(value) => {
                state.lifecycle = ProtocolState::Active;
                value.validate();
            }
            GeneratorStep::Return(value) => {
                value.validate();
                *self.0.completion.lock().expect("generator completion") = Some(value.clone());
                state.lifecycle = ProtocolState::Done;
            }
        }
        step
    }
    pub fn start(&self) -> GeneratorStep<Y, R> {
        let mut state = protocol_lock(&self.0.state, "generator-lifecycle");
        if state.lifecycle != ProtocolState::New {
            violation(
                "generator",
                "generator-lifecycle",
                "generator has already started",
            );
        }
        let step = state.source.start();
        self.validate_step(&mut state, step)
    }
    pub fn next_step(&self) -> GeneratorStep<Y, R> {
        let mut state = protocol_lock(&self.0.state, "generator-lifecycle");
        if state.lifecycle == ProtocolState::Done {
            return GeneratorStep::Return(self.return_value().expect("generator completion"));
        }
        if state.lifecycle == ProtocolState::Closed {
            violation("generator", "generator-lifecycle", "generator is closed");
        }
        let step = if state.lifecycle == ProtocolState::New {
            state.source.start()
        } else {
            state.source.next()
        };
        self.validate_step(&mut state, step)
    }
    fn send_mapped(&self, make_value: &mut dyn FnMut() -> S) -> GeneratorStep<Y, R> {
        let mut state = protocol_lock(&self.0.state, "generator-lifecycle");
        if state.lifecycle == ProtocolState::New {
            violation(
                "generator",
                "generator-lifecycle",
                "generator must be started before send",
            );
        }
        if matches!(state.lifecycle, ProtocolState::Done | ProtocolState::Closed) {
            violation("generator", "generator-lifecycle", "generator is complete");
        }
        let value = make_value();
        value.validate();
        let step = state.source.send(value);
        self.validate_step(&mut state, step)
    }
    pub fn throw_into(&self, error: ProtocolError) -> GeneratorStep<Y, R> {
        let mut state = protocol_lock(&self.0.state, "generator-lifecycle");
        if matches!(state.lifecycle, ProtocolState::Done | ProtocolState::Closed) {
            violation("generator", "generator-lifecycle", "generator is complete");
        }
        let step = state.source.raise(error);
        self.validate_step(&mut state, step)
    }
    fn completed_step(&self) -> bool {
        let state = protocol_lock(&self.0.state, "generator-lifecycle");
        if state.lifecycle == ProtocolState::Closed {
            violation("generator", "generator-lifecycle", "generator is closed");
        }
        state.lifecycle == ProtocolState::Done
    }
    pub fn return_value(&self) -> Option<R> {
        self.0
            .completion
            .lock()
            .expect("generator completion")
            .clone()
    }
}
impl<Y: Value, S: Value, R: Value + Clone> Iterator for Generator<Y, S, R> {
    type Item = Y;
    fn next(&mut self) -> Option<Y> {
        match self.next_step() {
            GeneratorStep::Yield(value) => Some(value),
            GeneratorStep::Return(_) => None,
        }
    }
}
impl<Y, S, R> Clone for GeneratorNative<Y, S, R> {
    fn clone(&self) -> Self {
        Self(self.0.clone())
    }
}
trait GeneratorProjection<Y, S, R>: Send + Sync {
    fn identity(&self) -> usize;
    fn start(&self) -> GeneratorStep<Y, R>;
    fn next_step(&self) -> GeneratorStep<Y, R>;
    fn completed_step(&self) -> bool;
    fn send_mapped(&self, value: &mut dyn FnMut() -> S) -> GeneratorStep<Y, R>;
    fn throw_into(&self, error: ProtocolError) -> GeneratorStep<Y, R>;
    fn return_value(&self) -> Option<R>;
    fn close(&self);
}
enum GeneratorBackend<Y, S, R> {
    Native(GeneratorNative<Y, S, R>),
    Projection(Arc<dyn GeneratorProjection<Y, S, R>>),
}
pub struct Generator<Y, S, R>(GeneratorBackend<Y, S, R>);
impl<Y, S, R> Generator<Y, S, R> {
    pub fn new<G: GeneratorProtocol<Y, S, R> + 'static>(source: G) -> Self {
        Self(GeneratorBackend::Native(GeneratorNative::new(source)))
    }
    fn identity(&self) -> usize {
        match &self.0 {
            GeneratorBackend::Native(source) => Arc::as_ptr(&source.0) as usize,
            GeneratorBackend::Projection(source) => source.identity(),
        }
    }
    pub fn close(&self) {
        match &self.0 {
            GeneratorBackend::Native(source) => source.close(),
            GeneratorBackend::Projection(source) => source.close(),
        }
    }
}
impl<Y: Value, S: Value, R: Value + Clone> Generator<Y, S, R> {
    pub fn start(&self) -> GeneratorStep<Y, R> {
        match &self.0 {
            GeneratorBackend::Native(source) => source.start(),
            GeneratorBackend::Projection(source) => source.start(),
        }
    }
    pub fn next_step(&self) -> GeneratorStep<Y, R> {
        match &self.0 {
            GeneratorBackend::Native(source) => source.next_step(),
            GeneratorBackend::Projection(source) => source.next_step(),
        }
    }
    fn completed_step(&self) -> bool {
        match &self.0 {
            GeneratorBackend::Native(source) => source.completed_step(),
            GeneratorBackend::Projection(source) => source.completed_step(),
        }
    }
    fn send_mapped(&self, make_value: &mut dyn FnMut() -> S) -> GeneratorStep<Y, R> {
        match &self.0 {
            GeneratorBackend::Native(source) => source.send_mapped(make_value),
            GeneratorBackend::Projection(source) => source.send_mapped(make_value),
        }
    }
    pub fn send(&self, value: S) -> GeneratorStep<Y, R> {
        let mut value = Some(value);
        self.send_mapped(&mut || value.take().expect("single protocol send"))
    }
    pub fn throw_into(&self, error: ProtocolError) -> GeneratorStep<Y, R> {
        match &self.0 {
            GeneratorBackend::Native(source) => source.throw_into(error),
            GeneratorBackend::Projection(source) => source.throw_into(error),
        }
    }
    pub fn return_value(&self) -> Option<R> {
        match &self.0 {
            GeneratorBackend::Native(source) => source.return_value(),
            GeneratorBackend::Projection(source) => source.return_value(),
        }
    }
}
struct GeneratorMaps<FY, FS, FR> {
    yielded: FY,
    sent: FS,
    returned: FR,
}
struct GeneratorMap<Y, S, R, DY, DS, DR, FY, FS, FR> {
    source: Generator<Y, S, R>,
    maps: std::sync::Mutex<GeneratorMaps<FY, FS, FR>>,
    completion: std::sync::Mutex<Option<DR>>,
    marker: std::marker::PhantomData<fn(DY, DS)>,
}
impl<Y, S, R, DY, DS, DR, FY, FS, FR> GeneratorMap<Y, S, R, DY, DS, DR, FY, FS, FR>
where
    DR: Value + Clone,
    FR: FnMut(R) -> DR,
{
    fn completion(&self, value: R, map: &mut FR) -> DR {
        if let Some(value) = self.completion.lock().expect("mapped completion").clone() {
            return value;
        }
        let value = map(value);
        value.validate();
        *self.completion.lock().expect("mapped completion") = Some(value.clone());
        value
    }
}
impl<Y, S, R, DY, DS, DR, FY, FS, FR> GeneratorMap<Y, S, R, DY, DS, DR, FY, FS, FR>
where
    DY: Value,
    DR: Value + Clone,
    FY: FnMut(Y) -> DY,
    FR: FnMut(R) -> DR,
{
    fn step(
        &self,
        step: GeneratorStep<Y, R>,
        maps: &mut GeneratorMaps<FY, FS, FR>,
    ) -> GeneratorStep<DY, DR> {
        match step {
            GeneratorStep::Yield(value) => {
                let value = (maps.yielded)(value);
                value.validate();
                GeneratorStep::Yield(value)
            }
            GeneratorStep::Return(value) => {
                GeneratorStep::Return(self.completion(value, &mut maps.returned))
            }
        }
    }
}
impl<Y, S, R, DY, DS, DR, FY, FS, FR> GeneratorProjection<DY, DS, DR>
    for GeneratorMap<Y, S, R, DY, DS, DR, FY, FS, FR>
where
    Y: Value + Clone + Send + Sync + 'static,
    S: Value + Clone + Send + Sync + 'static,
    R: Value + Clone + Send + Sync + 'static,
    DY: Value + Clone + Send + Sync + 'static,
    DS: Value + Clone + Send + Sync + 'static,
    DR: Value + Clone + Send + Sync + 'static,
    FY: FnMut(Y) -> DY + Send + 'static,
    FS: FnMut(DS) -> S + Send + 'static,
    FR: FnMut(R) -> DR + Send + 'static,
{
    fn identity(&self) -> usize {
        self.source.identity()
    }
    fn start(&self) -> GeneratorStep<DY, DR> {
        let mut maps = protocol_lock(&self.maps, "generator-lifecycle");
        self.step(self.source.start(), &mut maps)
    }
    fn next_step(&self) -> GeneratorStep<DY, DR> {
        let mut maps = protocol_lock(&self.maps, "generator-lifecycle");
        if let Some(value) = self.completion.lock().expect("mapped completion").clone() {
            // Preserve the authoritative operation guard without cloning a source return that would be discarded.
            if self.source.completed_step() {
                return GeneratorStep::Return(value);
            }
        }
        self.step(self.source.next_step(), &mut maps)
    }
    fn completed_step(&self) -> bool {
        let _maps = protocol_lock(&self.maps, "generator-lifecycle");
        self.source.completed_step()
    }
    fn send_mapped(&self, make_value: &mut dyn FnMut() -> DS) -> GeneratorStep<DY, DR> {
        let mut maps = protocol_lock(&self.maps, "generator-lifecycle");
        let step = self.source.send_mapped(&mut || {
            let value = make_value();
            value.validate();
            (maps.sent)(value)
        });
        self.step(step, &mut maps)
    }
    fn throw_into(&self, error: ProtocolError) -> GeneratorStep<DY, DR> {
        let mut maps = protocol_lock(&self.maps, "generator-lifecycle");
        self.step(self.source.throw_into(error), &mut maps)
    }
    fn return_value(&self) -> Option<DR> {
        if let Some(value) = self.completion.lock().expect("mapped completion").clone() {
            return Some(value);
        }
        let value = self.source.return_value()?;
        let mut maps = protocol_lock(&self.maps, "generator-lifecycle");
        Some(self.completion(value, &mut maps.returned))
    }
    fn close(&self) {
        let _maps = protocol_lock(&self.maps, "generator-lifecycle");
        self.source.close();
    }
}
impl<Y, S, R> Generator<Y, S, R>
where
    Y: Value + Clone + Send + Sync + 'static,
    S: Value + Clone + Send + Sync + 'static,
    R: Value + Clone + Send + Sync + 'static,
{
    pub fn map<DY, DS, DR, FY, FS, FR>(
        self,
        yielded: FY,
        sent: FS,
        returned: FR,
    ) -> Generator<DY, DS, DR>
    where
        DY: Value + Clone + Send + Sync + 'static,
        DS: Value + Clone + Send + Sync + 'static,
        DR: Value + Clone + Send + Sync + 'static,
        FY: FnMut(Y) -> DY + Send + 'static,
        FS: FnMut(DS) -> S + Send + 'static,
        FR: FnMut(R) -> DR + Send + 'static,
    {
        Generator(GeneratorBackend::Projection(Arc::new(GeneratorMap {
            source: self,
            maps: std::sync::Mutex::new(GeneratorMaps {
                yielded,
                sent,
                returned,
            }),
            completion: std::sync::Mutex::new(None),
            marker: std::marker::PhantomData,
        })))
    }
}
impl<Y, S, R> Clone for Generator<Y, S, R> {
    fn clone(&self) -> Self {
        Self(match &self.0 {
            GeneratorBackend::Native(source) => GeneratorBackend::Native(source.clone()),
            GeneratorBackend::Projection(source) => GeneratorBackend::Projection(source.clone()),
        })
    }
}
impl<Y, S, R> std::fmt::Debug for Generator<Y, S, R> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str("Generator")
    }
}
impl<Y, S, R> PartialEq for Generator<Y, S, R> {
    fn eq(&self, other: &Self) -> bool {
        self.identity() == other.identity()
    }
}
impl<Y, S, R> Eq for Generator<Y, S, R> {}

pub trait AsyncGeneratorProtocol<Y, S>: Send {
    fn start(
        &mut self,
        cancellation: Option<CancellationToken>,
    ) -> BoxFuture<'_, GeneratorStep<Y, ()>>;
    fn next(
        &mut self,
        cancellation: Option<CancellationToken>,
    ) -> BoxFuture<'_, GeneratorStep<Y, ()>>;
    fn send(
        &mut self,
        value: S,
        cancellation: Option<CancellationToken>,
    ) -> BoxFuture<'_, GeneratorStep<Y, ()>>;
    fn raise(
        &mut self,
        error: ProtocolError,
        cancellation: Option<CancellationToken>,
    ) -> BoxFuture<'_, GeneratorStep<Y, ()>>;
    fn close(&mut self, cancellation: Option<CancellationToken>) -> BoxFuture<'_, ()>;
}
struct AsyncGeneratorFunctions<F, C>(F, C);
impl<Y, S, F, C> AsyncGeneratorProtocol<Y, S> for AsyncGeneratorFunctions<F, C>
where
    F: FnMut(GeneratorRequest<S>, Option<CancellationToken>) -> BoxFuture<'static, GeneratorStep<Y, ()>> + Send,
    C: FnMut(Option<CancellationToken>) -> BoxFuture<'static, ()> + Send,
{
    fn start(&mut self, cancellation: Option<CancellationToken>) -> BoxFuture<'_, GeneratorStep<Y, ()>> { (self.0)(GeneratorRequest::Start, cancellation) }
    fn next(&mut self, cancellation: Option<CancellationToken>) -> BoxFuture<'_, GeneratorStep<Y, ()>> { (self.0)(GeneratorRequest::Next, cancellation) }
    fn send(&mut self, value: S, cancellation: Option<CancellationToken>) -> BoxFuture<'_, GeneratorStep<Y, ()>> { (self.0)(GeneratorRequest::Send(value), cancellation) }
    fn raise(&mut self, error: ProtocolError, cancellation: Option<CancellationToken>) -> BoxFuture<'_, GeneratorStep<Y, ()>> { (self.0)(GeneratorRequest::Raise(error), cancellation) }
    fn close(&mut self, cancellation: Option<CancellationToken>) -> BoxFuture<'_, ()> { (self.1)(cancellation) }
}
impl<Y, S> AsyncGenerator<Y, S> {
    pub fn from_fn<F, C>(step: F, close: C) -> Self
    where
        F: FnMut(GeneratorRequest<S>, Option<CancellationToken>) -> BoxFuture<'static, GeneratorStep<Y, ()>> + Send + 'static,
        C: FnMut(Option<CancellationToken>) -> BoxFuture<'static, ()> + Send + 'static,
    {
        Self::new(AsyncGeneratorFunctions(step, close))
    }
}
struct AsyncGeneratorState<Y, S> {
    source: Box<dyn AsyncGeneratorProtocol<Y, S>>,
    lifecycle: ProtocolState,
}
struct AsyncGeneratorCore<Y, S> {
    state: tokio::sync::Mutex<AsyncGeneratorState<Y, S>>,
    completed: std::sync::atomic::AtomicBool,
}
struct AsyncGeneratorNative<Y, S>(Arc<AsyncGeneratorCore<Y, S>>);
impl<Y, S> AsyncGeneratorNative<Y, S> {
    pub fn new<G: AsyncGeneratorProtocol<Y, S> + 'static>(source: G) -> Self {
        Self(Arc::new(AsyncGeneratorCore {
            state: tokio::sync::Mutex::new(AsyncGeneratorState {
                source: Box::new(source),
                lifecycle: ProtocolState::New,
            }),
            completed: std::sync::atomic::AtomicBool::new(false),
        }))
    }
    pub async fn close(&self) {
        self.close_with_cancellation(None).await;
    }
    pub async fn close_with_cancellation(&self, cancellation: Option<CancellationToken>) {
        let mut state = self.0.state.try_lock().unwrap_or_else(|_| {
            violation(
                "protocol",
                "async-lifecycle",
                "concurrent protocol operation",
            )
        });
        if matches!(state.lifecycle, ProtocolState::Done | ProtocolState::Closed) {
            return;
        }
        protocol_cancel(&cancellation);
        state.source.close(cancellation).await;
        state.lifecycle = ProtocolState::Closed;
    }
    pub fn return_value(&self) -> Option<()> {
        self.0
            .completed
            .load(std::sync::atomic::Ordering::Acquire)
            .then_some(())
    }
}
impl<Y: Value, S: Value> AsyncGeneratorNative<Y, S> {
    fn validate_step(
        &self,
        state: &mut AsyncGeneratorState<Y, S>,
        step: GeneratorStep<Y, ()>,
    ) -> GeneratorStep<Y, ()> {
        match &step {
            GeneratorStep::Yield(value) => {
                state.lifecycle = ProtocolState::Active;
                value.validate();
            }
            GeneratorStep::Return(()) => {
                self.0
                    .completed
                    .store(true, std::sync::atomic::Ordering::Release);
                state.lifecycle = ProtocolState::Done;
            }
        }
        step
    }
    pub async fn start(&self) -> GeneratorStep<Y, ()> {
        self.start_with_cancellation(None).await
    }
    pub async fn start_with_cancellation(
        &self,
        cancellation: Option<CancellationToken>,
    ) -> GeneratorStep<Y, ()> {
        let mut state = self.0.state.try_lock().unwrap_or_else(|_| {
            violation(
                "protocol",
                "async-lifecycle",
                "concurrent protocol operation",
            )
        });
        if state.lifecycle != ProtocolState::New {
            violation(
                "generator",
                "async-lifecycle",
                "async generator has already started",
            );
        }
        protocol_cancel(&cancellation);
        let step = state.source.start(cancellation.clone()).await;
        protocol_cancel(&cancellation);
        self.validate_step(&mut state, step)
    }
    pub async fn next(&self) -> GeneratorStep<Y, ()> {
        self.next_with_cancellation(None).await
    }
    pub async fn next_with_cancellation(
        &self,
        cancellation: Option<CancellationToken>,
    ) -> GeneratorStep<Y, ()> {
        let mut state = self.0.state.try_lock().unwrap_or_else(|_| {
            violation(
                "protocol",
                "async-lifecycle",
                "concurrent protocol operation",
            )
        });
        protocol_cancel(&cancellation);
        if state.lifecycle == ProtocolState::Done {
            return GeneratorStep::Return(());
        }
        if state.lifecycle == ProtocolState::Closed {
            violation("generator", "async-lifecycle", "async generator is closed");
        }
        let step = if state.lifecycle == ProtocolState::New {
            state.source.start(cancellation.clone()).await
        } else {
            state.source.next(cancellation.clone()).await
        };
        protocol_cancel(&cancellation);
        self.validate_step(&mut state, step)
    }
    pub async fn send(&self, value: S) -> GeneratorStep<Y, ()> {
        self.send_with_cancellation(value, None).await
    }
    pub async fn send_with_cancellation(
        &self,
        value: S,
        cancellation: Option<CancellationToken>,
    ) -> GeneratorStep<Y, ()> {
        let mut value = Some(value);
        self.send_mapped(
            &mut || value.take().expect("single protocol send"),
            cancellation,
        )
        .await
    }
    async fn send_mapped<F: FnMut() -> S + ?Sized>(
        &self,
        make_value: &mut F,
        cancellation: Option<CancellationToken>,
    ) -> GeneratorStep<Y, ()> {
        let mut state = self.0.state.try_lock().unwrap_or_else(|_| {
            violation(
                "protocol",
                "async-lifecycle",
                "concurrent protocol operation",
            )
        });
        if state.lifecycle == ProtocolState::New {
            violation(
                "generator",
                "async-lifecycle",
                "async generator must be started before send",
            );
        }
        if matches!(state.lifecycle, ProtocolState::Done | ProtocolState::Closed) {
            violation(
                "generator",
                "async-lifecycle",
                "async generator is complete",
            );
        }
        protocol_cancel(&cancellation);
        let value = make_value();
        value.validate();
        protocol_cancel(&cancellation);
        let step = state.source.send(value, cancellation.clone()).await;
        protocol_cancel(&cancellation);
        self.validate_step(&mut state, step)
    }
    pub async fn throw_into(&self, error: ProtocolError) -> GeneratorStep<Y, ()> {
        self.throw_into_with_cancellation(error, None).await
    }
    pub async fn throw_into_with_cancellation(
        &self,
        error: ProtocolError,
        cancellation: Option<CancellationToken>,
    ) -> GeneratorStep<Y, ()> {
        let mut state = self.0.state.try_lock().unwrap_or_else(|_| {
            violation(
                "protocol",
                "async-lifecycle",
                "concurrent protocol operation",
            )
        });
        if matches!(state.lifecycle, ProtocolState::Done | ProtocolState::Closed) {
            violation(
                "generator",
                "async-lifecycle",
                "async generator is complete",
            );
        }
        protocol_cancel(&cancellation);
        let step = state.source.raise(error, cancellation.clone()).await;
        protocol_cancel(&cancellation);
        self.validate_step(&mut state, step)
    }
}
impl<Y, S> Clone for AsyncGeneratorNative<Y, S> {
    fn clone(&self) -> Self {
        Self(self.0.clone())
    }
}
trait AsyncGeneratorProjection<Y, S>: Send + Sync {
    fn identity(&self) -> usize;
    fn start(&self, cancellation: Option<CancellationToken>)
    -> BoxFuture<'_, GeneratorStep<Y, ()>>;
    fn next(&self, cancellation: Option<CancellationToken>) -> BoxFuture<'_, GeneratorStep<Y, ()>>;
    fn send(
        &self,
        value: S,
        cancellation: Option<CancellationToken>,
    ) -> BoxFuture<'_, GeneratorStep<Y, ()>>;
    fn send_mapped<'a>(
        &'a self,
        value: &'a mut (dyn FnMut() -> S + Send),
        cancellation: Option<CancellationToken>,
    ) -> BoxFuture<'a, GeneratorStep<Y, ()>>;
    fn throw_into(
        &self,
        error: ProtocolError,
        cancellation: Option<CancellationToken>,
    ) -> BoxFuture<'_, GeneratorStep<Y, ()>>;
    fn return_value(&self) -> Option<()>;
    fn close(&self, cancellation: Option<CancellationToken>) -> BoxFuture<'_, ()>;
}
enum AsyncGeneratorBackend<Y, S> {
    Native(AsyncGeneratorNative<Y, S>),
    Projection(Arc<dyn AsyncGeneratorProjection<Y, S>>),
}
pub struct AsyncGenerator<Y, S>(AsyncGeneratorBackend<Y, S>);
impl<Y, S> AsyncGenerator<Y, S> {
    pub fn new<G: AsyncGeneratorProtocol<Y, S> + 'static>(source: G) -> Self {
        Self(AsyncGeneratorBackend::Native(AsyncGeneratorNative::new(
            source,
        )))
    }
    fn identity(&self) -> usize {
        match &self.0 {
            AsyncGeneratorBackend::Native(source) => Arc::as_ptr(&source.0) as usize,
            AsyncGeneratorBackend::Projection(source) => source.identity(),
        }
    }
    pub async fn close(&self) {
        match &self.0 {
            AsyncGeneratorBackend::Native(source) => source.close().await,
            AsyncGeneratorBackend::Projection(source) => source.close(None).await,
        }
    }
    pub async fn close_with_cancellation(&self, cancellation: Option<CancellationToken>) {
        match &self.0 {
            AsyncGeneratorBackend::Native(source) => {
                source.close_with_cancellation(cancellation).await
            }
            AsyncGeneratorBackend::Projection(source) => source.close(cancellation).await,
        }
    }
    pub fn return_value(&self) -> Option<()> {
        match &self.0 {
            AsyncGeneratorBackend::Native(source) => source.return_value(),
            AsyncGeneratorBackend::Projection(source) => source.return_value(),
        }
    }
}
impl<Y: Value, S: Value> AsyncGenerator<Y, S> {
    pub async fn start(&self) -> GeneratorStep<Y, ()> {
        match &self.0 {
            AsyncGeneratorBackend::Native(source) => source.start().await,
            AsyncGeneratorBackend::Projection(source) => source.start(None).await,
        }
    }
    pub async fn start_with_cancellation(
        &self,
        cancellation: Option<CancellationToken>,
    ) -> GeneratorStep<Y, ()> {
        match &self.0 {
            AsyncGeneratorBackend::Native(source) => {
                source.start_with_cancellation(cancellation).await
            }
            AsyncGeneratorBackend::Projection(source) => source.start(cancellation).await,
        }
    }
    pub async fn next(&self) -> GeneratorStep<Y, ()> {
        match &self.0 {
            AsyncGeneratorBackend::Native(source) => source.next().await,
            AsyncGeneratorBackend::Projection(source) => source.next(None).await,
        }
    }
    pub async fn next_with_cancellation(
        &self,
        cancellation: Option<CancellationToken>,
    ) -> GeneratorStep<Y, ()> {
        match &self.0 {
            AsyncGeneratorBackend::Native(source) => {
                source.next_with_cancellation(cancellation).await
            }
            AsyncGeneratorBackend::Projection(source) => source.next(cancellation).await,
        }
    }
    pub async fn send(&self, value: S) -> GeneratorStep<Y, ()> {
        match &self.0 {
            AsyncGeneratorBackend::Native(source) => source.send(value).await,
            AsyncGeneratorBackend::Projection(source) => source.send(value, None).await,
        }
    }
    pub async fn send_with_cancellation(
        &self,
        value: S,
        cancellation: Option<CancellationToken>,
    ) -> GeneratorStep<Y, ()> {
        match &self.0 {
            AsyncGeneratorBackend::Native(source) => {
                source.send_with_cancellation(value, cancellation).await
            }
            AsyncGeneratorBackend::Projection(source) => source.send(value, cancellation).await,
        }
    }
    async fn send_mapped(
        &self,
        make_value: &mut (dyn FnMut() -> S + Send),
        cancellation: Option<CancellationToken>,
    ) -> GeneratorStep<Y, ()> {
        match &self.0 {
            AsyncGeneratorBackend::Native(source) => {
                source.send_mapped(make_value, cancellation).await
            }
            AsyncGeneratorBackend::Projection(source) => {
                source.send_mapped(make_value, cancellation).await
            }
        }
    }
    pub async fn throw_into(&self, error: ProtocolError) -> GeneratorStep<Y, ()> {
        match &self.0 {
            AsyncGeneratorBackend::Native(source) => source.throw_into(error).await,
            AsyncGeneratorBackend::Projection(source) => source.throw_into(error, None).await,
        }
    }
    pub async fn throw_into_with_cancellation(
        &self,
        error: ProtocolError,
        cancellation: Option<CancellationToken>,
    ) -> GeneratorStep<Y, ()> {
        match &self.0 {
            AsyncGeneratorBackend::Native(source) => {
                source
                    .throw_into_with_cancellation(error, cancellation)
                    .await
            }
            AsyncGeneratorBackend::Projection(source) => {
                source.throw_into(error, cancellation).await
            }
        }
    }
}
struct AsyncGeneratorMaps<FY, FS> {
    yielded: FY,
    sent: FS,
}
struct AsyncGeneratorMap<Y, S, DY, DS, FY, FS> {
    source: AsyncGenerator<Y, S>,
    maps: tokio::sync::Mutex<AsyncGeneratorMaps<FY, FS>>,
    marker: std::marker::PhantomData<fn(DY, DS)>,
}
impl<Y, S, DY, DS, FY, FS> AsyncGeneratorMap<Y, S, DY, DS, FY, FS>
where
    DY: Value,
    FY: FnMut(Y) -> DY,
{
    fn step(
        &self,
        step: GeneratorStep<Y, ()>,
        maps: &mut AsyncGeneratorMaps<FY, FS>,
    ) -> GeneratorStep<DY, ()> {
        match step {
            GeneratorStep::Yield(value) => {
                let value = (maps.yielded)(value);
                value.validate();
                GeneratorStep::Yield(value)
            }
            GeneratorStep::Return(()) => GeneratorStep::Return(()),
        }
    }
}
impl<Y, S, DY, DS, FY, FS> AsyncGeneratorProjection<DY, DS>
    for AsyncGeneratorMap<Y, S, DY, DS, FY, FS>
where
    Y: Value + Clone + Send + Sync + 'static,
    S: Value + Clone + Send + Sync + 'static,
    DY: Value + Clone + Send + Sync + 'static,
    DS: Value + Clone + Send + Sync + 'static,
    FY: FnMut(Y) -> DY + Send + 'static,
    FS: FnMut(DS) -> S + Send + 'static,
{
    fn identity(&self) -> usize {
        self.source.identity()
    }
    fn start(
        &self,
        cancellation: Option<CancellationToken>,
    ) -> BoxFuture<'_, GeneratorStep<DY, ()>> {
        Box::pin(async move {
            let mut maps = self.maps.try_lock().unwrap_or_else(|_| {
                violation(
                    "protocol",
                    "async-lifecycle",
                    "concurrent protocol operation",
                )
            });
            let step = self
                .source
                .start_with_cancellation(cancellation.clone())
                .await;
            let step = self.step(step, &mut maps);
            protocol_cancel(&cancellation);
            step
        })
    }
    fn next(
        &self,
        cancellation: Option<CancellationToken>,
    ) -> BoxFuture<'_, GeneratorStep<DY, ()>> {
        Box::pin(async move {
            let mut maps = self.maps.try_lock().unwrap_or_else(|_| {
                violation(
                    "protocol",
                    "async-lifecycle",
                    "concurrent protocol operation",
                )
            });
            let step = self
                .source
                .next_with_cancellation(cancellation.clone())
                .await;
            let step = self.step(step, &mut maps);
            protocol_cancel(&cancellation);
            step
        })
    }
    fn send(
        &self,
        value: DS,
        cancellation: Option<CancellationToken>,
    ) -> BoxFuture<'_, GeneratorStep<DY, ()>> {
        Box::pin(async move {
            let mut value = Some(value);
            self.send_mapped(
                &mut || value.take().expect("single protocol send"),
                cancellation,
            )
            .await
        })
    }
    fn send_mapped<'a>(
        &'a self,
        make_value: &'a mut (dyn FnMut() -> DS + Send),
        cancellation: Option<CancellationToken>,
    ) -> BoxFuture<'a, GeneratorStep<DY, ()>> {
        Box::pin(async move {
            let mut maps = self.maps.try_lock().unwrap_or_else(|_| {
                violation(
                    "protocol",
                    "async-lifecycle",
                    "concurrent protocol operation",
                )
            });
            let step = self
                .source
                .send_mapped(
                    &mut || {
                        let value = make_value();
                        value.validate();
                        (maps.sent)(value)
                    },
                    cancellation.clone(),
                )
                .await;
            let step = self.step(step, &mut maps);
            protocol_cancel(&cancellation);
            step
        })
    }
    fn throw_into(
        &self,
        error: ProtocolError,
        cancellation: Option<CancellationToken>,
    ) -> BoxFuture<'_, GeneratorStep<DY, ()>> {
        Box::pin(async move {
            let mut maps = self.maps.try_lock().unwrap_or_else(|_| {
                violation(
                    "protocol",
                    "async-lifecycle",
                    "concurrent protocol operation",
                )
            });
            let step = self
                .source
                .throw_into_with_cancellation(error, cancellation.clone())
                .await;
            let step = self.step(step, &mut maps);
            protocol_cancel(&cancellation);
            step
        })
    }
    fn return_value(&self) -> Option<()> {
        self.source.return_value()
    }
    fn close(&self, cancellation: Option<CancellationToken>) -> BoxFuture<'_, ()> {
        Box::pin(async move {
            let _maps = self.maps.try_lock().unwrap_or_else(|_| {
                violation(
                    "protocol",
                    "async-lifecycle",
                    "concurrent protocol operation",
                )
            });
            self.source.close_with_cancellation(cancellation).await;
        })
    }
}
impl<Y, S> AsyncGenerator<Y, S>
where
    Y: Value + Clone + Send + Sync + 'static,
    S: Value + Clone + Send + Sync + 'static,
{
    pub fn map<DY, DS, FY, FS>(self, yielded: FY, sent: FS) -> AsyncGenerator<DY, DS>
    where
        DY: Value + Clone + Send + Sync + 'static,
        DS: Value + Clone + Send + Sync + 'static,
        FY: FnMut(Y) -> DY + Send + 'static,
        FS: FnMut(DS) -> S + Send + 'static,
    {
        AsyncGenerator(AsyncGeneratorBackend::Projection(Arc::new(
            AsyncGeneratorMap {
                source: self,
                maps: tokio::sync::Mutex::new(AsyncGeneratorMaps { yielded, sent }),
                marker: std::marker::PhantomData,
            },
        )))
    }
}
impl<Y, S> Clone for AsyncGenerator<Y, S> {
    fn clone(&self) -> Self {
        Self(match &self.0 {
            AsyncGeneratorBackend::Native(source) => AsyncGeneratorBackend::Native(source.clone()),
            AsyncGeneratorBackend::Projection(source) => {
                AsyncGeneratorBackend::Projection(source.clone())
            }
        })
    }
}
impl<Y, S> std::fmt::Debug for AsyncGenerator<Y, S> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str("AsyncGenerator")
    }
}
impl<Y, S> PartialEq for AsyncGenerator<Y, S> {
    fn eq(&self, other: &Self) -> bool {
        self.identity() == other.identity()
    }
}
impl<Y, S> Eq for AsyncGenerator<Y, S> {}

enum FactoryOperation<T: ConstructionArguments> {
    Canonical(fn(T::Arguments) -> T),
    Custom(Arc<dyn Fn(T::Arguments) -> T + Send + Sync>),
}
pub struct Factory<T: ConstructionArguments>(FactoryOperation<T>);
impl<T: ConstructionArguments> Clone for Factory<T> {
    fn clone(&self) -> Self {
        Self(match &self.0 {
            FactoryOperation::Canonical(f) => FactoryOperation::Canonical(*f),
            FactoryOperation::Custom(f) => FactoryOperation::Custom(f.clone()),
        })
    }
}
impl<T: ConstructionArguments + Value> Factory<T> {
    pub fn new<F: Fn(T::Arguments) -> T + Send + Sync + 'static>(value: F) -> Self {
        Self(FactoryOperation::Custom(Arc::new(value)))
    }
    pub fn constructor() -> Self
    where
        T: Constructible,
    {
        Self(FactoryOperation::Canonical(T::construct))
    }
    pub fn create(&self, arguments: T::Arguments) -> T {
        let value = match &self.0 {
            FactoryOperation::Canonical(f) => f(arguments),
            FactoryOperation::Custom(f) => f(arguments),
        };
        value.validate();
        value
    }
}
impl<T: ConstructionArguments> std::fmt::Debug for Factory<T> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str("Factory")
    }
}
impl<T: ConstructionArguments> PartialEq for Factory<T> {
    fn eq(&self, other: &Self) -> bool {
        match (&self.0, &other.0) {
            (FactoryOperation::Canonical(_), FactoryOperation::Canonical(_)) => true,
            (FactoryOperation::Custom(a), FactoryOperation::Custom(b)) => Arc::ptr_eq(a, b),
            _ => false,
        }
    }
}

pub struct Dyn<T: ?Sized>(Arc<tokio::sync::Mutex<Box<T>>>);
impl<T: ?Sized> Dyn<T> {
    pub fn new(value: Box<T>) -> Self {
        Self(Arc::new(tokio::sync::Mutex::new(value)))
    }
    pub async fn acquire(&self) -> tokio::sync::OwnedMutexGuard<Box<T>> {
        self.0.clone().lock_owned().await
    }
    pub fn try_acquire(&self) -> tokio::sync::OwnedMutexGuard<Box<T>> {
        self.0
            .clone()
            .try_lock_owned()
            .unwrap_or_else(|_| violation("dyn", "guard", "overlapping lease"))
    }
}
impl<T: ?Sized> Clone for Dyn<T> {
    fn clone(&self) -> Self {
        Self(self.0.clone())
    }
}
impl<T: ?Sized> std::fmt::Debug for Dyn<T> {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        f.write_str("Dyn")
    }
}
impl<T: ?Sized> PartialEq for Dyn<T> {
    fn eq(&self, other: &Self) -> bool {
        Arc::ptr_eq(&self.0, &other.0)
    }
}
