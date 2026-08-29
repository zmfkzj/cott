from integrations.fastapi_hello import HttpRequest
from integrations.fastapi_hello_types import HelloResponse


def read_root(request: HttpRequest) -> HelloResponse:
    """Return FastAPI's official `Hello World` message and the injected request method."""
    return HelloResponse(message="Hello World", method=request.method)
