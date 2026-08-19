# fastapi-hello

## 예제 목적
Cott로 선언한 `HelloResponse`와 루트 GET 핸들러를 FastAPI 애플리케이션의 `/` 경로에 연결하는 경계를 보여 줍니다.

## 핵심 포인트
- Cott 소스의 `@get("/") fn read_root() -> HelloResponse`는 `message`가 항상 `"Hello World"`임을 계약으로 명시합니다.
- 지속 Python 바인딩 `app.py`는 `FastAPI()`를 만들고 `app.get("/")(read_root)`로 가져온 핸들러를 실제 FastAPI 경로에 등록합니다.
- 지속 구현 `python/_cott_impl/integrations/fastapi_hello/read_root.py`는 생성된 `integrations.fastapi_hello_types.HelloResponse`를 가져와 `HelloResponse(message="Hello World")`를 반환합니다.
- `cott.toml`은 Python 생성물과 스텁의 위치를 분리하고 런타임 검증을 `boundary`로 설정합니다.
