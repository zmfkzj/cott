from fastapi import FastAPI
from integrations.fastapi_hello import HelloResponse, read_root
from starlette.requests import Request

app = FastAPI()


@app.get("/")
def root(request: Request) -> HelloResponse:
    return read_root(request)
