from integrations.fastapi_hello_types import HelloResponse, HttpRequest


def read_root(request: HttpRequest) -> HelloResponse:
    return HelloResponse(message="Hello World", method=request.method)
