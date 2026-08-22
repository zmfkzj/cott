# opaque-resource

## 예제 목적
이 실행 가능한 예제는 클라이언트 세션 ID를 `HandleBundle` 안에서 불투명하게 유지하고, 외부 타입 및 iterator/generator 경계를 함께 보여 줍니다.

## Cott 표면
- `Opaque["client_session"]`는 `HandleBundle.handle` 안에 중첩됩니다. `wrap_handle`은 `raw_id == 0`일 때만 `HandleError.InvalidHandle`을 반환하고, 그 외에는 `Result[HandleBundle, HandleError]`를 반환합니다. `extract_handle_id`는 이 번들을 받아 양수 ID를 반환합니다.
- `TextBuffer`는 외부 타입입니다. Python 투영은 매니페스트의 `[target.python.external_types]` 테이블에서 지정하며, 이 예제는 외부 객체의 구조적 또는 깊은 런타임 검증을 주장하지 않습니다.
- `iter_lines(TextBuffer) -> Iterator[Str]`는 줄을 지연해서 반환하고 각 줄의 끝 줄바꿈을 제거합니다. 바인딩 경계에서 iterator를 미리 소비하지 않습니다.
- `echo_values(Iterator[Any]) -> Generator[Any, Unknown, U64]`는 모든 입력 `Any`를 yield하고, `Unknown` send 채널로 돌려받은 값은 무시한 뒤 yield한 개수를 `U64`로 반환합니다. 지연 경계의 원소 값은 깊게 검증하지 않습니다.

네 함수 모두 `effects []`를 선언합니다. 선언된 오류는 `wrap_handle`의 `HandleError.InvalidHandle`뿐입니다.

## 예상 출력
```text
Extracted handle id: 42
Lines: alpha,beta
Generated values: first,7
Generator return count: 2
```
