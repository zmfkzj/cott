//! Compiler-owned finite workers, fixture servers, and filesystem audits.
use crate::cott_runtime;
use std::any::Any;
use std::collections::BTreeMap;
use std::future::{Future, poll_fn};
use std::io::{Read, Write};
use std::path::Path;
use std::sync::{
    Arc,
    atomic::{AtomicBool, Ordering},
};
use std::task::Poll;
use std::time::{Duration, Instant};
#[derive(Debug)]
pub struct AssertionFailure;
#[derive(Debug)]
pub struct TimeoutFailure;
#[derive(Debug)]
pub struct LifecycleFailure;
type Panic = Box<dyn Any + Send>;
type Observations = Vec<cott_runtime::PredicateObservation>;
enum Race<T> {
    Completed((Result<T, Panic>, Observations)),
    Cancelled,
}
pub struct Worker<T> {
    scope: cott_runtime::TaskScope,
    token: cott_runtime::CancellationToken,
    receiver: Option<tokio::sync::oneshot::Receiver<(Result<T, Panic>, bool)>>,
    completion: Option<tokio::sync::oneshot::Receiver<(Result<(), Panic>, Observations)>>,
    pub cancellation_observed: bool,
    observations: Observations,
}
impl<T: Send + 'static> Worker<T> {
    pub async fn start<F: Future<Output = T> + Send + 'static>(future: F) -> Self {
        let scope = cott_runtime::TaskScope::default();
        let token = cott_runtime::CancellationToken::default();
        let task_token = token.clone();
        let (tx, rx) = tokio::sync::oneshot::channel();
        let (done_tx, done_rx) = tokio::sync::oneshot::channel();
        scope.spawn(move |_| async move {
            let mut underlying = std::pin::pin!(cott_runtime::__cott_observe_async(future));
            let mut cancellation = std::pin::pin!(task_token.cancelled());
            // The race starts with the worker, not when a caller eventually awaits.
            // An already completed worker cannot be relabelled cancelled later.
            let outcome = poll_fn(|cx| {
                if cancellation.as_mut().poll(cx).is_ready() {
                    return Poll::Ready(Race::Cancelled);
                }
                match underlying.as_mut().poll(cx) {
                    Poll::Ready(value) => Poll::Ready(Race::Completed(value)),
                    Poll::Pending => Poll::Pending,
                }
            })
            .await;
            match outcome {
                Race::Completed((result, observations)) => {
                    let _ = tx.send((result, false));
                    let _ = done_tx.send((Ok(()), observations));
                }
                Race::Cancelled => {
                    let checked = std::panic::catch_unwind(std::panic::AssertUnwindSafe(|| {
                        task_token.check()
                    }));
                    let (error, observed) = match checked {
                        Err(error) => {
                            let observed = error.is::<cott_runtime::CancellationException>();
                            (error, observed)
                        }
                        Ok(()) => (Box::new(LifecycleFailure) as Panic, false),
                    };
                    let _ = tx.send((Err(error), observed));
                    // Keep polling the original future; cancellation is never preemption.
                    let (result, observations) = underlying.await;
                    let _ = done_tx.send((result.map(|_| ()), observations));
                }
            }
        });
        Self {
            scope,
            token,
            receiver: Some(rx),
            completion: Some(done_rx),
            cancellation_observed: false,
            observations: Vec::new(),
        }
    }
    pub fn cancel(&self) {
        self.token.cancel();
    }
    pub async fn result(&mut self) -> Result<T, Panic> {
        let receiver = self
            .receiver
            .take()
            .ok_or_else(|| Box::new(LifecycleFailure) as Panic)?;
        let (result, observed) = receiver
            .await
            .map_err(|_| Box::new(LifecycleFailure) as Panic)?;
        self.cancellation_observed = observed;
        result
    }
    /// Join both the unpreempted underlying future and its structured task scope.
    /// A timeout is failure, never successful cooperative cancellation evidence.
    pub async fn close(&mut self, milliseconds: u64) -> Result<(), Panic> {
        if let Some(receiver) = self.completion.take() {
            let (result, observations) =
                tokio::time::timeout(Duration::from_millis(milliseconds), receiver)
                    .await
                    .map_err(|_| Box::new(TimeoutFailure) as Panic)?
                    .map_err(|_| Box::new(LifecycleFailure) as Panic)?;
            self.observations.extend(observations);
            result?;
        }
        tokio::time::timeout(Duration::from_millis(milliseconds), self.scope.join())
            .await
            .map_err(|_| Box::new(TimeoutFailure) as Panic)?;
        Ok(())
    }
    pub fn take_observations(&mut self) -> Observations {
        std::mem::take(&mut self.observations)
    }
}
#[derive(Clone)]
pub enum Route {
    Response {
        status: u16,
        body: Vec<u8>,
        content_type: Option<String>,
    },
    Redirect {
        status: u16,
        location: String,
    },
    Delay {
        milliseconds: u64,
    },
}
pub struct HttpFixture {
    base_url: String,
    stop: Arc<AtomicBool>,
    thread: Option<std::thread::JoinHandle<Result<(), String>>>,
}
impl HttpFixture {
    pub fn start(
        routes: BTreeMap<String, Route>,
        requests: u32,
        body_bytes: u64,
        redirects: u32,
        transcript: u32,
        timeout_ms: u64,
    ) -> Result<Self, String> {
        let listener = std::net::TcpListener::bind((std::net::Ipv4Addr::LOCALHOST, 0))
            .map_err(|e| e.to_string())?;
        listener.set_nonblocking(true).map_err(|e| e.to_string())?;
        let base_url = format!(
            "http://127.0.0.1:{}",
            listener.local_addr().map_err(|e| e.to_string())?.port()
        );
        let stop = Arc::new(AtomicBool::new(false));
        let signal = stop.clone();
        let thread = std::thread::spawn(move || {
            let mut request_count = 0u32;
            let mut redirect_count = 0u32;
            let mut transcript_count = 0u32;
            while !signal.load(Ordering::Acquire) {
                let (mut stream, _) = match listener.accept() {
                    Ok(value) => value,
                    Err(e) if e.kind() == std::io::ErrorKind::WouldBlock => {
                        std::thread::sleep(Duration::from_millis(1));
                        continue;
                    }
                    Err(e) => return Err(e.to_string()),
                };
                request_count = request_count
                    .checked_add(1)
                    .ok_or("HTTP request count overflow")?;
                transcript_count = transcript_count
                    .checked_add(1)
                    .ok_or("HTTP transcript overflow")?;
                if request_count > requests || transcript_count > transcript {
                    return Err("HTTP fixture request/transcript limit exceeded".into());
                }
                let timeout = Duration::from_millis(timeout_ms.max(1));
                stream
                    .set_read_timeout(Some(timeout))
                    .map_err(|e| e.to_string())?;
                stream
                    .set_write_timeout(Some(timeout))
                    .map_err(|e| e.to_string())?;
                let deadline = Instant::now() + timeout;
                let mut bytes = Vec::new();
                let mut buffer = [0u8; 4096];
                let header_end;
                loop {
                    if bytes.len() > 64 * 1024 || Instant::now() > deadline {
                        return Err("HTTP fixture header/time limit exceeded".into());
                    }
                    let n = stream.read(&mut buffer).map_err(|e| e.to_string())?;
                    if n == 0 {
                        return Err("HTTP fixture request closed before headers".into());
                    }
                    bytes.extend_from_slice(&buffer[..n]);
                    if let Some(end) = bytes.windows(4).position(|w| w == b"\r\n\r\n") {
                        header_end = end + 4;
                        break;
                    }
                }
                let headers = std::str::from_utf8(&bytes[..header_end])
                    .map_err(|_| "HTTP fixture request headers are not UTF-8")?;
                let first = headers
                    .lines()
                    .next()
                    .ok_or("HTTP request has no request line")?;
                let mut parts = first.split_whitespace();
                let method = parts.next().ok_or("HTTP request has no method")?;
                let path = parts
                    .next()
                    .ok_or("HTTP request has no path")?
                    .split('?')
                    .next()
                    .ok_or("HTTP request path missing")?
                    .to_owned();
                let mut content_length = 0usize;
                let mut has_length = false;
                let mut chunked = false;
                for line in headers.lines().skip(1) {
                    if let Some((name, value)) = line.split_once(':') {
                        if name.eq_ignore_ascii_case("content-length") {
                            if has_length {
                                return Err("duplicate HTTP content length".into());
                            }
                            has_length = true;
                            content_length = value
                                .trim()
                                .parse()
                                .map_err(|_| "invalid HTTP content length")?;
                        }
                        if name.eq_ignore_ascii_case("transfer-encoding") {
                            match value.trim() {
                                "identity" => {}
                                "chunked" => chunked = true,
                                _ => {
                                    return Err("unsupported HTTP fixture transfer encoding".into());
                                }
                            }
                        }
                    }
                }
                if content_length as u64 > body_bytes {
                    return Err("HTTP fixture request body limit exceeded".into());
                }
                if chunked && has_length {
                    return Err("ambiguous HTTP fixture body framing".into());
                }
                let head = method == "HEAD";
                {
                    let prefix = std::io::Cursor::new(&bytes[header_end..]);
                    let mut reader = prefix.chain(&mut stream);
                    if chunked {
                        let mut total = 0u64;
                        loop {
                            let line = bounded_http_line(&mut reader, 128, deadline)?;
                            let length = u64::from_str_radix(
                                line.split(';').next().ok_or("chunk size missing")?,
                                16,
                            )
                            .map_err(|_| "invalid HTTP chunk size")?;
                            if length == 0 {
                                let mut trailer_bytes = 0usize;
                                loop {
                                    let trailer = bounded_http_line(&mut reader, 4096, deadline)?;
                                    trailer_bytes = trailer_bytes
                                        .checked_add(trailer.len() + 2)
                                        .ok_or("HTTP trailer overflow")?;
                                    if trailer_bytes > 64 * 1024 {
                                        return Err("HTTP fixture trailer limit exceeded".into());
                                    }
                                    if trailer.is_empty() {
                                        break;
                                    }
                                }
                                break;
                            }
                            total = total
                                .checked_add(length)
                                .ok_or("HTTP chunk byte count overflow")?;
                            if total > body_bytes {
                                return Err("HTTP fixture request body limit exceeded".into());
                            }
                            drain_http_bytes(&mut reader, length, deadline)?;
                            let mut ending = [0u8; 2];
                            reader.read_exact(&mut ending).map_err(|e| e.to_string())?;
                            if ending != *b"\r\n" {
                                return Err("invalid HTTP chunk terminator".into());
                            }
                        }
                    } else {
                        drain_http_bytes(&mut reader, content_length as u64, deadline)?;
                    }
                }
                let (mut status, mut body, mut extra) = (404u16, &[][..], String::new());
                match routes.get(&path) {
                    Some(Route::Response {
                        status: s,
                        body: b,
                        content_type,
                    }) => {
                        status = *s;
                        body = b.as_slice();
                        if body.len() as u64 > body_bytes {
                            return Err("HTTP fixture response body limit exceeded".into());
                        }
                        if let Some(t) = content_type {
                            if t.contains(['\r', '\n']) {
                                return Err("invalid HTTP fixture content type".into());
                            }
                            extra.push_str(&format!("Content-Type: {t}\r\n"));
                        }
                    }
                    Some(Route::Redirect {
                        status: s,
                        location,
                    }) => {
                        redirect_count = redirect_count
                            .checked_add(1)
                            .ok_or("redirect count overflow")?;
                        if redirect_count > redirects {
                            return Err("HTTP fixture redirect limit exceeded".into());
                        }
                        if location.contains(['\r', '\n']) {
                            return Err("invalid HTTP fixture redirect".into());
                        }
                        status = *s;
                        extra.push_str(&format!("Location: {location}\r\n"));
                    }
                    Some(Route::Delay { milliseconds }) => {
                        if *milliseconds > timeout_ms {
                            return Err("HTTP fixture delay exceeds timeout".into());
                        }
                        std::thread::sleep(Duration::from_millis(*milliseconds));
                        status = 204;
                    }
                    None => {}
                }
                let response = format!(
                    "HTTP/1.1 {status} Fixture\r\nContent-Length: {}\r\nConnection: close\r\n{extra}\r\n",
                    body.len()
                );
                stream
                    .write_all(response.as_bytes())
                    .map_err(|e| e.to_string())?;
                if !head {
                    stream.write_all(body).map_err(|e| e.to_string())?;
                }
                stream.flush().map_err(|e| e.to_string())?;
                transcript_count = transcript_count
                    .checked_add(1)
                    .ok_or("transcript overflow")?;
                if transcript_count > transcript {
                    return Err("HTTP fixture transcript limit exceeded".into());
                }
            }
            Ok(())
        });
        Ok(Self {
            base_url,
            stop,
            thread: Some(thread),
        })
    }
    pub fn base_url(&self) -> String {
        self.base_url.clone()
    }
    pub fn close(&mut self) -> Result<(), String> {
        self.stop.store(true, Ordering::Release);
        if let Some(thread) = self.thread.take() {
            thread
                .join()
                .map_err(|_| "HTTP fixture thread panicked".to_owned())??;
        }
        Ok(())
    }
}
impl Drop for HttpFixture {
    fn drop(&mut self) {
        let _ = self.close();
    }
}
pub fn audit_root(root: &Path, file_limit: u32, byte_limit: u64) -> Result<(), String> {
    use std::os::unix::fs::MetadataExt;
    let mut dirs = vec![root.to_path_buf()];
    let mut files = 0u32;
    let mut bytes = 0u64;
    let mut members = 0usize;
    while let Some(dir) = dirs.pop() {
        for entry in std::fs::read_dir(dir).map_err(|e| e.to_string())? {
            let entry = entry.map_err(|e| e.to_string())?;
            members += 1;
            if members > 20_000 {
                return Err("scenario filesystem member limit exceeded".into());
            }
            let m = std::fs::symlink_metadata(entry.path()).map_err(|e| e.to_string())?;
            if m.is_dir() && !m.file_type().is_symlink() {
                dirs.push(entry.path());
            } else if m.is_file() && m.nlink() == 1 {
                files = files.checked_add(1).ok_or("file count overflow")?;
                bytes = bytes
                    .checked_add(m.len())
                    .ok_or("file byte count overflow")?;
                if files > file_limit || bytes > byte_limit {
                    return Err("scenario filesystem limit exceeded".into());
                }
            } else {
                return Err("scenario fixture contains a link or special file".into());
            }
        }
    }
    Ok(())
}

#[allow(clippy::too_many_arguments)]
pub fn emit_scenario(
    evidence: &mut crate::evidence::EvidenceWriter,
    id: &str,
    symbol: &str,
    result: Result<(), Box<dyn Any + Send>>,
    observations: Vec<cott_runtime::PredicateObservation>,
    assertions: u32,
    cancellations: u32,
    cleaned: bool,
    step: Option<u32>,
) -> std::io::Result<()> {
    let status = if result.is_ok() && cleaned {
        "passed"
    } else {
        "failed"
    };
    let mut extra = String::new();
    if let Err(error) = result {
        let (mut failure, mut phase, mut clause, mut error_symbol, mut exception) = (
            "exception",
            "null".to_owned(),
            "null".to_owned(),
            "null".to_owned(),
            "null".to_owned(),
        );
        if let Some(error) = error.downcast_ref::<cott_runtime::ContractViolation>() {
            failure = if error.phase == "cancellation" {
                "cancellation"
            } else {
                "contract"
            };
            phase = crate::evidence::json_quote(&error.phase);
            clause = crate::evidence::json_quote(&error.clause);
            error_symbol = crate::evidence::json_quote(&error.symbol);
        } else if error.is::<AssertionFailure>() {
            failure = "assertion";
        } else if error.is::<TimeoutFailure>() {
            failure = "timeout";
        } else if error.is::<LifecycleFailure>() {
            failure = "lifecycle";
        } else {
            exception = crate::evidence::json_quote("panic");
        }
        extra = format!(
            ",\"failure\":{},\"failed_step\":{},\"phase\":{phase},\"clause\":{clause},\"error_symbol\":{error_symbol},\"exception_type\":{exception}",
            crate::evidence::json_quote(failure),
            step.map(|s| s.to_string()).unwrap_or_else(|| "null".into())
        );
    } else if !cleaned {
        extra=",\"failure\":\"lifecycle\",\"failed_step\":null,\"phase\":null,\"clause\":null,\"error_symbol\":null,\"exception_type\":null".into();
    }
    evidence.event(&format!("{{\"kind\":\"scenario\",\"scenario_id\":{},\"symbol\":{},\"status\":{},\"assertions\":{assertions},\"cancellations\":{cancellations},\"cleaned\":{cleaned},\"observations\":{}{extra}}}",crate::evidence::json_quote(id),crate::evidence::json_quote(symbol),crate::evidence::json_quote(status),crate::observations_json(&observations)))
}

fn bounded_http_line(
    reader: &mut impl Read,
    limit: usize,
    deadline: Instant,
) -> Result<String, String> {
    let mut bytes = Vec::new();
    loop {
        if bytes.len() >= limit || Instant::now() > deadline {
            return Err("HTTP fixture line/time limit exceeded".into());
        }
        let mut byte = [0u8; 1];
        reader.read_exact(&mut byte).map_err(|e| e.to_string())?;
        bytes.push(byte[0]);
        if byte[0] == b'\n' {
            break;
        }
    }
    if !bytes.ends_with(b"\r\n") {
        return Err("invalid HTTP line terminator".into());
    }
    bytes.truncate(bytes.len() - 2);
    String::from_utf8(bytes).map_err(|_| "HTTP fixture line is not UTF-8".into())
}
fn drain_http_bytes(
    reader: &mut impl Read,
    mut remaining: u64,
    deadline: Instant,
) -> Result<(), String> {
    let mut buffer = [0u8; 4096];
    while remaining != 0 {
        if Instant::now() > deadline {
            return Err("HTTP fixture request timeout".into());
        }
        let length = (remaining.min(buffer.len() as u64)) as usize;
        let read = reader
            .read(&mut buffer[..length])
            .map_err(|e| e.to_string())?;
        if read == 0 {
            return Err("truncated HTTP fixture request body".into());
        }
        remaining -= read as u64;
    }
    Ok(())
}
