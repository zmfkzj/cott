# fastapi-hello

## Purpose
Shows a minimal FastAPI adapter around a Cott callable with an external request type.

## Key points
- `external type HttpRequest` is a semantic Cott type. `cott.toml` independently projects the exact symbol `"integrations.fastapi_hello.HttpRequest"` to `starlette.requests:Request`.
- `read_root(request: HttpRequest) -> HelloResponse` returns FastAPI's official `"Hello World"` message plus the injected request's `method`.
- `python/app.py` is the FastAPI adapter: it creates `app = FastAPI()`, injects `Request` in its `@app.get("/")` route, and forwards that request through the generated `integrations.fastapi_hello.read_root` facade.
- `python/_cott_impl/integrations/fastapi_hello/read_root.py` is the callable implementation. It accepts the projected `starlette.requests.Request` and returns the generated `HelloResponse`.
- `fastapi[standard]` remains the single production dependency because it provides the documented FastAPI CLI. For development, run `uv run fastapi dev app.py` from `python/`.
