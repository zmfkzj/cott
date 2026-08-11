
from integrations.fastapi_hello_types import HelloResponse


def read_root() -> HelloResponse:
    return HelloResponse(message="Hello World")
