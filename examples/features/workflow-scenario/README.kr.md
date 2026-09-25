# workflow-scenario

## 목적

이 dependency-free 기능 프로젝트는 불변 search와 save snapshot 위에서 유한 async workflow scenario를 실행합니다. scheduling은 scenario 안(`spawn`, `tick`, `cancel`, `await`)에만 있으며 framework object, widget tree, private implementation import, host clock, sleep, effect를 사용하지 않습니다. 여섯 구현은 모두 agent가 생성하며 manifest에는 binding이 없습니다.

일반 emission 뒤 public 동작은 다음처럼 실행합니다.

```sh
PYTHONPATH=generated/python .venv/bin/python python/app.py
```

앱은 이전 result를 resolve하고 더 새로운 search를 시작한 뒤 새로운 result를 적용합니다. 이어서 같은 public `apply_search` facade에 이전 result를 전달해도 snapshot은 더 새로운 result를 유지합니다. 또한 draft save를 더 새로운 save로 coalesce하고 `new result`와 `published`를 출력합니다.

## 계약

- `SearchSnapshot` invariant: request ID는 양수이고, `Loading`이면 아직 적용된 것이 없으며(`applied_request_id == 0`, 빈 result), `Ready`이면 snapshot 자신의 request가 적용된 상태입니다(`applied_request_id == request_id`). `SearchResult`, `SaveSnapshot`, `SaveReceipt`는 양수 request ID 또는 revision을 요구합니다.
- `begin_search`는 주어진 request ID와 query의 `Loading` snapshot을 반환합니다.
- `resolve_search`만 async facade입니다. result는 request ID와 query를 유지하고 text는 query 뒤에 ` result`를 붙인 값입니다. 계약에는 문자열 연결이 없으므로 clause는 이를 `starts_with`, `ends_with`, `result.len == query.len + 7`로 표현합니다.
- `apply_search`는 request ID와 query를 항상 보존합니다. snapshot의 request에 속한 candidate는 snapshot을 그 result의 `Ready`로 만들고, 다른 candidate는 snapshot을 그대로 반환하므로 이전 result가 더 새로운 request를 덮어쓸 수 없습니다.
- `begin_save`는 첫 request를 queue에 넣습니다. `request_save`는 엄격히 더 새로운 revision일 때만 대기 중인 request를 교체하고, 같거나 더 오래된 revision이면 snapshot을 그대로 반환합니다. `flush_save`는 snapshot의 revision과 text를 가진 `Flushed` receipt를 반환합니다.
- requirement `PENDING_SEARCH_IS_CANCELLABLE`은 clause가 표현하지 못하는 의무를 적습니다. spawn된 resolution은 scheduler의 다음 turn까지 pending이므로 그 전에 cancel하면 cancelled로 끝납니다.

## 증거

`latest_result_and_coalesced_save`는 이전 worker를 await하고, 더 새로운 search를 시작하고, 별도의 pending worker를 cancel·join한 뒤 새 result와 이전 result를 차례로 적용합니다. 최종 snapshot이 request 2, query `new`, result `new result`, `Ready`와 같고, 더 새로운 request와 stale request 뒤의 flush가 revision 2, `published`, `Flushed`를 내는지 assert합니다.

`runtime_validation = "boundary"`이므로 모든 scenario call은 facade clause도 검사하며, bounded automatic candidate가 순수 facade를 실행합니다. 마지막 Python `cott verify`는 scenario를 test observation으로, semantic coverage를 `observed=23`(`unobserved`, `trust_declaration`, `unknown` clause 없음)으로, `PENDING_SEARCH_IS_CANCELLABLE`을 scenario를 통한 `observed`로 기록했습니다. 이는 bounded observation이며 증명이 아닙니다.

`examples/kotlin/features/workflow-scenario`의 Kotlin mirror는 같은 계약을 가지며, 마지막 `cott verify`도 같은 결과(scenario test observation, `observed=23`, requirement `observed`)를 기록했습니다. Kotlin runner는 spawn된 worker를 undispatched로 시작하므로 cancellation requirement를 만족하려면 `resolve_search` 구현이 완료 전에 suspend해야 합니다.
