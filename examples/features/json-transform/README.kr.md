# json-transform

## 예제 목적
Cott v0.1의 `JsonValue` ABI로 문자열 키-값을 JSON 객체로 감싸고, 객체에서 문자열 필드를 안전하게 꺼내는 예제입니다.

## 핵심 포인트
- `wrap_scalar_json`은 `effects []` 계약으로 `JsonValue`를 반환하며, Python 바인딩은 `FrozenMap` 안의 `JsonString`으로 JSON 객체를 구성합니다.
- `extract_string_field`는 JSON 객체가 아니면 `NotAnObject`, 필드가 없거나 문자열이 아니면 필드명을 담은 `MissingField`를 `Result` 오류로 반환합니다.
- 실행 예제는 `{"greeting": "Hello Cott"}`를 만들고 `greeting`을 추출해 성공값을 출력합니다.
