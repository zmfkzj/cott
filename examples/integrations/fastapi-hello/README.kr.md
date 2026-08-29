# fastapi-hello

## 예제 목적
외부 요청 타입을 사용하는 Cott 호출부 주위의 최소 FastAPI 어댑터를 보여 줍니다.

## 핵심 포인트
- `external type HttpRequest`는 의미론적인 Cott 타입입니다. `cott.toml`은 정확한 심볼 `"integrations.fastapi_hello.HttpRequest"`를 `starlette.requests:Request`로 독립적으로 투영합니다.
- `read_root(request: HttpRequest) -> HelloResponse`는 FastAPI 공식 `"Hello World"` 메시지와 주입된 요청의 `method`를 반환합니다.
- `python/app.py`는 FastAPI 어댑터입니다. `app = FastAPI()`를 만들고 `@app.get("/")` 경로에서 `Request`를 주입한 뒤 생성된 `integrations.fastapi_hello.read_root` facade를 거쳐 요청을 전달합니다.
- `python/_cott_impl/integrations/fastapi_hello/read_root.py`는 호출 가능 구현입니다. 투영된 `starlette.requests.Request`를 받아 생성된 `HelloResponse`를 반환합니다.
- 문서화된 FastAPI CLI를 제공하므로 `fastapi[standard]`는 유일한 production dependency로 유지합니다. 개발 시 `python/`에서 `uv run fastapi dev app.py`를 실행합니다.
