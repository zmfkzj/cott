# workflow-scenario

## 목적

이 dependency-free Cott v0.8 기능 프로젝트는 manifest-bound Python facade를 통해 불변 public search와 save snapshot을 모델링합니다. scheduling은 유한 scenario 안에만 두며 framework object, widget tree, private implementation import, host clock, sleep, effect를 사용하지 않습니다.

일반 emission 뒤 public 동작은 다음처럼 실행합니다.

```sh
PYTHONPATH=generated/python .venv/bin/python python/app.py
```

앱은 이전 result를 resolve하고 더 새로운 search를 시작한 뒤 새로운 result를 적용합니다. 이어서 같은 public `apply_search` facade에 이전 result를 전달해도 반환 snapshot이 더 새로운 result를 유지함을 보입니다. 또한 queued draft를 더 새로운 save request로 바꾸고 flushed public receipt를 출력합니다.

## 도메인과 scenario

- `SearchSnapshot`과 `SearchResult`는 typed request ID, query text, public result state를 보관합니다. struct invariant는 양수 request ID를 요구하고 applied ID가 snapshot request ID보다 크지 않게 하며 compiler-owned canonical constructor가 이를 강제합니다.
- `SearchStatus`와 `SaveStatus`는 mutable controller 없이 loading, ready, queued, flushed state를 명시합니다.
- `latest_result_and_coalesced_save`는 이전 worker를 시작하고 await한 다음 새 worker를 시작합니다. 별도의 pending worker는 cancel하고 join합니다. 새 result를 적용한 뒤 public field로 이전 result를 적용해도 덮어쓸 수 없음을 증명합니다. save sequence는 `request_save`와 `flush_save` value만으로 coalescing을 관찰합니다.
- `resolve_search`만 async facade입니다. 나머지 facade는 모두 순수 synchronous transformation이며, 각 manifest entry는 정확히 하나의 typed top-level binding을 가리킵니다. manifest에는 authored identity가 없습니다.

이 프로젝트에는 generated artifact나 verification record를 작성하지 않습니다.
