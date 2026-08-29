# effects-selection

## 목적

이 기능 프로젝트는 각 내장 Cott 효과를 type이 지정된 binding에 연결합니다. compiler가 v0.8 scenario identity와 실행 가능한 filesystem, HTTP, clock, failure fixture를 소유하며, manifest는 fixture identity를 선언하지 않습니다.

## 효과 계약

- `read_text`는 compiler-private `cott_runtime._cott_fixture_read` adapter를 통해 UTF-8을 읽습니다. 없는 fixture file은 `InputMissing`이 되고 decoding 및 주입된 fixture failure는 `OperationFailed`가 됩니다.
- `copy_text`는 생성된 `curriculum.effects_selection` 공개 facade를 통해 `read_text`를 호출한 다음 `_cott_fixture_replace`로 atomic replacement를 합니다. failure scenario는 주입된 `file.replace` failure 뒤에도 이전 destination content를 읽을 수 있음을 증명합니다.
- 순수 public `text_result_is_ok`, `text_result_text`, `copy_result_is_ok` facade는 private inspection 없이 finite scenario가 type이 지정된 `Result` outcome을 관찰하게 합니다. scenario는 이 facade를 통해 성공한 정확한 text, copy의 성공 또는 failure, 보존된 destination text를 assert합니다.
- `fetch_local`은 `_cott_fixture_http`만 사용합니다. local scenario는 relative redirect 뒤 UTF-8 decoding, 8-character response, 주입된 `http.read` timeout, 조건부 빈 URL error 거부를 증명합니다.
- `clock_ns`는 `_cott_fixture_now`의 millisecond를 deterministic nanosecond로 변환하고, scenario는 고정된 clock을 두 번 읽습니다.
- `store_and_load` (`database.read`, `database.write`), `sample_index` (`random`), `exit_with_code` (`process.exit`)는 type이 지정된 trust declaration입니다. v0.8에는 이들을 위한 compatible fixture backend가 없으므로 scenario가 실행하지 않습니다.

## 실행

Cott 생성 후 Python project에서 `python app.py`를 실행하면 compiler-owned scenario가 다루는 public facade를 나열합니다. app은 file, server, subprocess, wall-clock observation을 만들지 않습니다. fixture scenario는 compiler의 isolated verification workflow에서만 실행됩니다.

## 선택 범위

`cott.toml`은 모든 public Cott function을 정확한 type의 local binding에 mapping합니다. `copy_text`는 `read_text`로 가는 유일한 호출 경계로 생성된 public facade를 유지하고, 어느 binding도 host path, endpoint, clock을 import하지 않습니다. `_cott_impl` source나 hand-authored generation record는 없습니다.
