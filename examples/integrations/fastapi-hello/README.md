# fastapi-hello

## Purpose
Shows a minimal FastAPI adapter around a Cott callable with an external request type. Cott owns only the `read_root` module boundary; FastAPI owns routing, request injection and serialization.

## Key points
- `external type HttpRequest` is a semantic Cott type. `cott.toml` independently projects the exact symbol `"integrations.fastapi_hello.HttpRequest"` to `starlette.requests:Request`.
- `read_root(request: HttpRequest) -> HelloResponse` is specified to return FastAPI's official `"Hello World"` message and the HTTP method of `request` exactly as received.
- `python/app.py` is the FastAPI adapter: it creates `app = FastAPI()`, injects `Request` in its `@app.get("/")` route, and forwards that request through the generated `integrations.fastapi_hello.read_root` facade.
- `python/_cott_impl/integrations/fastapi_hello/read_root.py` is the agent-owned implementation of that contract; it is regenerated from the contract, not edited by hand.
- `fastapi[standard]` remains the single production dependency because it provides the documented FastAPI CLI. For development, run `uv run fastapi dev app.py` from `python/`.

## Evidence
- Formally specified: `ensures result.message == "Hello World"`. With `runtime_validation = "boundary"` the facade checks it on every call. `cott verify` records it as `unobserved` because it cannot generate an external `request` input, and no scenario can construct one.
- The method relation cannot be a clause: contracts cannot read fields of an external type. It is the requirement `METHOD_IS_REQUEST_METHOD` (with the assumption that the projected request type exposes its method), which `cott requirements` reports as `unverified`.
- `tests/examples.rs` sends `GET /` through FastAPI's `TestClient` and expects `{"message": "Hello World", "method": "GET"}`. That is an external test, not Cott evidence, and it cannot tell the requested behavior from an implementation that always returns `"GET"`.
- `verified` certifies this snapshot's artifacts, types and runtime checks. It does not establish that the application is correct.
