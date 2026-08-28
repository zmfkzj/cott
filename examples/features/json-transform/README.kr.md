# json-transform

## 예제 목적
이 v0.6 예제는 비어 있지 않은 문자열 키-값을 JSON 객체로 감싸고, 문자열 필드를 안전하게 꺼내며, 유한한 재귀 `JsonChain`을 구성합니다.

## 핵심 포인트
- `wrap_scalar_json`은 명시적인 `async fn`이며, await한 반환값은 `JsonValue`입니다. `key.len > 0`이 필요합니다. Python 바인딩은 동기 브리지 없는 정확한 `async def`로서 `FrozenMap` 안의 `JsonString`으로 JSON 객체를 구성합니다.
- `extract_string_field`는 동기 함수로 유지됩니다. JSON 객체가 아니면 `NotAnObject`, 필드가 없거나 문자열이 아니면 필드명을 담은 `MissingField`를 `Result` 오류로 반환합니다.
- `JsonChain`은 생산적인 재귀 열거형입니다. `End`가 `Link(value, next: Option[JsonChain])` 체인을 끝냅니다.
- 실행 예제는 하나의 `asyncio.run(main())`을 사용해 `wrap_scalar_json`을 await한 뒤 `greeting`을 추출하고, `{"greeting": "Hello Cott"}`에서 얻은 기존 성공값을 유지하며, 유한한 `Link` → `End` 체인에서 `Recursive JSON chain: first`를 출력합니다.
