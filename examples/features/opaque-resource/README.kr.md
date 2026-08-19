# opaque-resource

## 예제 목적
Cott v0.1의 태그된 `Opaque["client_session"]` ABI로 원시 연결 ID를 클라이언트 세션 핸들로 구분하는 예제입니다.

## 핵심 포인트
- `wrap_handle`은 `raw_id == 0`일 때 `HandleError.InvalidHandle`을 반환하고, 그 외에는 `client_session` 태그의 불투명 핸들을 `Result` 성공값으로 만듭니다.
- Python 바인딩은 이 타입을 `Opaque[Literal["client_session"]]`로 나타내므로, `extract_handle_id`는 같은 태그의 핸들만 받아 내부 `U64` ID를 꺼냅니다.
- `extract_handle_id`는 결과가 0보다 커야 한다는 `ensures` 계약과 `effects []`를 선언하며, 실행 예제는 ID `42`를 감싼 뒤 다시 출력합니다.
