# boundary-protocols

## 예제 목적
이 실행 가능한 boundary 모드 예제는 클라이언트 세션 identity를 opaque로 유지하고, 외부 Python 타입 하나를 투영하며, 동기·비동기 protocol lifecycle을 실제로 구동합니다.

## Cott 표면
- `ConnectionId`는 `where self > 0`로 refinement한 `U64` newtype이므로 0인 ID는 만들 수 없습니다. `HandleBundle.handle`은 정확히 `Opaque["client_session"]`이고, 계약 `doc`은 그 payload를 ID의 `U64` 값으로 고정합니다. `wrap_handle`은 bundle을 만들고(`ensures result.raw_id == raw_id`), `extract_handle_id`는 payload를 다시 `ConnectionId`로 읽는 명시적 target-side adaptation입니다.
- `TextBuffer`는 semantic external Cott type이며, `[target.python.external_types]`의 `"curriculum.boundary_protocols.TextBuffer" = "io:StringIO"`으로만 투영됩니다.
- `adapt_unknown(Any) -> Unknown`은 동적 경계를 의도적으로 넘고 값을 그대로 반환합니다. 앱은 dictionary 값을 읽기 전에 `isinstance`로 반환된 `Unknown`을 명시적으로 narrow합니다.
- `iter_lines`와 `echo_values`는 동기 `Iterator` 및 `Generator[Any, Unknown, U64]` protocol을 유지합니다. `doc`은 줄(LF, CR, CRLF로 끝나며 terminator는 제외)과 generator 반환값(yield한 값의 개수)을 정의합니다.
- `async_lines`는 `AsyncIterator[Str]`을, `echo_async`는 `AsyncGenerator[Any, Unknown]`을 받아 반환합니다. 둘 다 caller의 protocol object를 그대로 돌려줍니다.

모든 함수는 `effects []`를 선언합니다.

## 증거
- scenario `handle_round_trips_id`는 `wrap_handle(ConnectionId(42))`의 결과를 `extract_handle_id`에 넘기고 같은 ID가 돌아오는지 확인합니다. requirement `HANDLE_ROUND_TRIPS_ID`의 연결된 검사입니다. ID 하나에 대한 반환값을 관찰할 뿐, 구현이 어느 field를 읽었는지는 관찰하지 않습니다.
- contract runner는 opaque, external, protocol 입력을 만들 수 없고 이 callable의 lifecycle 관찰도 기록하지 않습니다. requirement `RETURNS_SAME_VALUE`, `YIELDS_LINES_LAZILY`, `ECHOES_EACH_VALUE_ONCE`, `RETURNS_SUPPLIED_ITERATOR`, `RETURNS_SUPPLIED_GENERATOR`는 `unverified`로 남습니다.
- 아래 앱 출력은 저장소 테스트 `tests/examples.rs`가 확인합니다. 이는 프로그램 회귀 검사이지 Cott 증거가 아닙니다.

## 예상 출력
```text
Wrapped raw id: 42
Extracted handle id: 42
Narrowed unknown: explicit
Lines: alpha,beta
Generator return count: 2
Generated values: first,7
Async lines: gamma,delta
Async iterator completed
Async generated values: first,7
Async generator completed
Async generator closed twice
```

앱은 `runtime_validation = "boundary"` 설정에서 `__anext__`, `asend`를 명시적으로 호출하고, `StopAsyncIteration`을 관찰하며, `aclose`를 두 번 호출합니다.
