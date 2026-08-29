# boundary-protocols

## 예제 목적
이 실행 가능한 boundary 모드 증거 예제는 클라이언트 세션 identity를 opaque로 유지하고, 외부 Python 타입 하나를 투영하며, 동기·비동기 protocol lifecycle을 실제로 구동합니다.

## Cott 표면
- `HandleBundle.handle`은 정확히 `Opaque["client_session"]`입니다. `wrap_handle`은 0만 거부하고 성공 시 허용된 0이 아닌 raw ID를 `HandleBundle.raw_id`로 노출하며, `extract_handle_id`는 opaque identity를 unwrap하는 명시적 target-side adaptation입니다.
- `TextBuffer`는 semantic external Cott type이며, `[target.python.external_types]`의 `"curriculum.boundary_protocols.TextBuffer" = "io:StringIO"`으로만 투영됩니다.
- `adapt_unknown(Any) -> Unknown`은 동적 경계를 의도적으로 넘습니다. 앱은 dictionary 값을 읽기 전에 `isinstance`로 반환된 `Unknown`을 명시적으로 narrow합니다.
- `iter_lines`와 `echo_values`는 동기 `Iterator` 및 `Generator[Any, Unknown, U64]` protocol을 유지합니다. generator는 완료 뒤 yield한 개수를 반환합니다.
- `async_lines`는 `AsyncIterator[Str]`을 받아 그대로 반환하고, `echo_async`는 `AsyncGenerator[Any, Unknown]`을 받아 그대로 반환합니다. binding은 caller가 제공한 protocol object의 identity `async def` wrapper입니다.

모든 함수는 `effects []`를 선언하며, 선언된 오류는 `HandleError.InvalidHandle` 하나입니다.

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
