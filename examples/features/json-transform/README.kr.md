# json-transform

## 예제 목적
이 v0.7 예제는 비어 있지 않은 문자열 키-값을 `JsonValue` 객체로 감싸고, 문자열 member를 다시 읽어 내며, 유한한 재귀 `JsonChain`을 구성합니다.

## 핵심 포인트
- `JsonValue`는 Cott의 고정 JSON tagged union입니다. 계약 절은 그 variant를 match할 수 없으므로 JSON 형태는 `doc`과 requirement에 적습니다. scenario는 `JsonValue.Object(value: Map("count": JsonValue.Integer(value: 7)))` 같은 닫힌 `JsonValue` literal을 만들고 반환값과 비교할 수 있습니다.
- `wrap_scalar_json`은 `key.len > 0`을 요구하는 명시적 `async fn`입니다. requirement `WRAPPED_OBJECT_HAS_ONE_STRING_MEMBER`는 결과가 `key`를 JSON 문자열 `value`에 대응시키는 member 하나만 가진 JSON 객체라고 규정합니다.
- `extract_string_field`는 동기 함수로 유지되며 `Result[StringField, JsonTransformError]`를 반환합니다. `StringField` receipt가 읽은 member의 이름을 담으므로 `ensures Result.Ok(found) => found.name == field`가 성공값을 요청과 연결하고, `MissingField`는 `field`를 담아야 합니다. 나머지는 `doc`이 정합니다. 정확한 최상위 key 조회, `MissingField`보다 먼저 검사하는 `NotAnObject`, member가 없거나 문자열이 아니면 `MissingField`입니다. 절이 `JsonValue`를 검사할 수 없으므로 두 오류는 조건 없이 선언하고, requirement `SHAPE_FAILURES_ARE_REPORTED`가 그 실패 대응을 담습니다.
- scenario `wrapped_member_round_trips`는 두 facade를 합성합니다. `wrap_scalar_json("greeting", "Hello Cott")`가 정확히 `JsonValue.Object(value: Map("greeting": JsonValue.String(value: "Hello Cott")))`와 같고, `"greeting"`이 `"Hello Cott"`로 다시 읽히며, `"farewell"`은 `MissingField`가 되기를 기대합니다.
- scenario `shape_failures_are_reported`는 JSON 문자열 payload를 넘겨 `NotAnObject`를, `count` member가 JSON 정수인 객체를 넘겨 `MissingField`를 기대합니다. payload는 계약의 `name == field` obligation이 검사합니다.
- `JsonChain`은 생산적인 재귀 열거형입니다. `End`가 `Link(value, next: Option[JsonChain])` 체인을 끝냅니다.
- 실행 예제는 하나의 `asyncio.run(main())`을 사용해 `wrap_scalar_json`을 await한 뒤 `greeting`에서 추출한 `text`를 출력하고, 유한한 `Link` → `End` 체인에서 `Recursive JSON chain: first`를 출력합니다.

## Evidence
- scenario와 bounded runner case가 두 callable의 모든 절을 관찰하며, semantic coverage에 `unobserved`, `unknown`, `trust declaration` 절은 없습니다.
- `WRAPPED_OBJECT_HAS_ONE_STRING_MEMBER`는 한 입력 쌍에 대한 정확한 객체 비교 assertion으로 `observed`입니다. 이는 bounded evidence이며 모든 key와 value를 검사한 것은 아닙니다.
- `SHAPE_FAILURES_ARE_REPORTED`는 `shape_failures_are_reported`로 `observed`입니다. 이 scenario는 객체가 아닌 payload 하나(JSON 문자열)와 문자열이 아닌 member 하나(JSON 정수)만 다룹니다. 다른 비객체 variant와 member type은 scenario로 실행하지 않습니다.
