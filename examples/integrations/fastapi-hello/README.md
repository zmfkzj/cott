# fastapi-hello

## Purpose
Shows the boundary that connects the `HelloResponse` declared with Cott and the root GET handler to the `/` route of a FastAPI application.

## Key points
- The Cott source's `@get("/") fn read_root() -> HelloResponse` specifies in its contract that `message` is always `"Hello World"`.
- The durable Python binding `app.py` creates `FastAPI()` and registers the imported handler as an actual FastAPI route with `app.get("/")(read_root)`.
- The durable implementation `python/_cott_impl/integrations/fastapi_hello/read_root.py` imports the generated `integrations.fastapi_hello_types.HelloResponse` and returns `HelloResponse(message="Hello World")`.
- `cott.toml` separates the locations of Python generated artifacts and stubs, and sets runtime validation to `boundary`.
