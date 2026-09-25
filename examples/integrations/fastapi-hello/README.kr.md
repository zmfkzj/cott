# fastapi-hello

## 예제 목적
외부 요청 타입을 사용하는 Cott 호출부 주위의 최소 FastAPI 어댑터를 보여 줍니다. Cott는 `read_root` 모듈 경계만 소유하며, 라우팅, 요청 주입, 직렬화는 FastAPI가 소유합니다.

## 핵심 포인트
- `external type HttpRequest`는 의미론적인 Cott 타입입니다. `cott.toml`은 정확한 심볼 `"integrations.fastapi_hello.HttpRequest"`를 `starlette.requests:Request`로 독립적으로 투영합니다.
- `read_root(request: HttpRequest) -> HelloResponse`는 FastAPI 공식 `"Hello World"` 메시지와, 받은 그대로의 `request` HTTP 메서드를 반환하도록 명세되어 있습니다.
- `python/app.py`는 FastAPI 어댑터입니다. `app = FastAPI()`를 만들고 `@app.get("/")` 경로에서 `Request`를 주입한 뒤 생성된 `integrations.fastapi_hello.read_root` facade를 거쳐 요청을 전달합니다.
- `python/_cott_impl/integrations/fastapi_hello/read_root.py`는 이 계약의 에이전트 소유 구현입니다. 손으로 수정하지 않고 계약으로부터 다시 생성합니다.
- 문서화된 FastAPI CLI를 제공하므로 `fastapi[standard]`는 유일한 production dependency로 유지합니다. 개발 시 `python/`에서 `uv run fastapi dev app.py`를 실행합니다.

## 검증 근거
- 형식 명세: `ensures result.message == "Hello World"`. `runtime_validation = "boundary"`이므로 facade는 매 호출마다 이를 검사합니다. `cott verify`는 외부 타입 `request` 입력을 생성할 수 없고 어떤 시나리오도 이를 만들 수 없으므로 이 조항을 `unobserved`로 기록합니다.
- 메서드 관계는 조항으로 쓸 수 없습니다. 계약은 외부 타입의 필드를 읽을 수 없기 때문입니다. 이는 요구사항 `METHOD_IS_REQUEST_METHOD`(투영된 요청 타입이 메서드를 노출한다는 가정 포함)이며, `cott requirements`는 이를 `unverified`로 보고합니다.
- `tests/examples.rs`는 FastAPI `TestClient`로 `GET /`를 보내고 `{"message": "Hello World", "method": "GET"}`를 기대합니다. 이는 Cott 근거가 아닌 외부 테스트이며, 항상 `"GET"`을 반환하는 구현과 요구된 동작을 구별하지 못합니다.
- `verified`는 이 스냅숏의 산출물, 타입, 런타임 검사를 인증합니다. 애플리케이션이 올바르다는 것을 확립하지는 않습니다.
