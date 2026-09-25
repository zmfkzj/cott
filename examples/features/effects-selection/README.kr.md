# effects-selection

## 목적

이 기능 프로젝트는 각 내장 Cott effect를 agent가 구현을 생성하는 typed public function에 선언합니다. compiler가 scenario identity와 실행 가능한 filesystem, HTTP, clock, failure fixture를 모두 소유하며, manifest는 fixture identity도 binding도 선언하지 않습니다. scenario는 pattern assertion으로 result를 관찰하고 그 결과 state를 public facade로 다시 읽습니다.

## 계약

- `read_text`(`file.read`)는 strict UTF-8로 decode한 text와 source path를 묶은 `FileText`를 반환합니다(`file.path == source`). 없는 source는 그 path를 담은 `InputMissing`이고, 그 밖의 read failure와 잘못된 UTF-8은 `OperationFailed`입니다.
- `copy_text`(`file.read`, `file.write`)는 destination과 기록한 UTF-8 byte 수(문자 수가 아님)를 담은 `CopyReceipt`를 반환합니다. `read_text` error는 그대로 반환되고(`InputMissing` payload는 source path) destination은 건드리지 않습니다. requirement `COPY_IS_ATOMIC`은 replacement가 실패하면 `OperationFailed`를 반환하고 이전 destination byte를 유지한다고 적고, `COPY_READS_THROUGH_READ_TEXT`는 source를 public `read_text` facade로만 읽는다고 적습니다.
- `fetch_local`(`network`)은 최종 response의 UTF-8 text와 요청한 URL을 묶은 `PageText`를 반환합니다. redirect를 따라갑니다. 빈 URL은 조건부 `OperationFailed`이고, transport failure, timeout, 200-299 밖의 status, 잘못된 UTF-8은 `OperationFailed`입니다.
- `clock_ns`(`clock`)는 fixture clock을 nanosecond로 읽습니다. fixture는 millisecond로 설정하므로 `start_ms: 17`은 `17000000`으로 읽히고, 읽어도 clock은 진행하지 않습니다.
- `store_and_load`(`database.read`, `database.write`), `sample_index`(`random`), `exit_with_code`(`process.exit`)에는 fixture backend가 없어 어떤 scenario도 호출할 수 없습니다. 이들의 clause(`stored == value`, `requires limit > 0`, `result < limit`)는 trust declaration으로 남고, `value`를 그대로 돌려주거나 항상 index 0을 반환하거나 다른 status로 종료하는 구현을 거부하는 검사가 없습니다. requirement `STORED_VALUE_IS_READ_BACK`, `SAMPLE_IS_SEEDED`, `EXIT_STATUS_IS_CODE`는 `unverified`로 남습니다.

## 증거

- `filesystem_copy`는 `café`를 읽고 복사한 뒤 `bytes_written == 5`(4개 문자가 아닌 UTF-8 byte)를 assert하고 destination을 다시 읽습니다. 이어서 없는 source에서 복사해 `InputMissing`을 assert하고 바뀌지 않은 destination을 다시 읽습니다. 마지막으로 byte `0xff` 하나만 담은 file을 읽어 `OperationFailed`를 assert하므로 느슨한 decoding을 거부합니다.
- `filesystem_replace_failure`는 `file.replace`에 `disk_full` failure를 주입하고 `OperationFailed`를 assert한 뒤 이전 destination text를 다시 읽습니다. `COPY_IS_ATOMIC`에 연결된 검사입니다.
- `local_http`는 relative redirect를 따라 UTF-8 body를 읽고, 주입된 `http.read` timeout에서 error를 assert하며, 빈 URL을 호출해 facade boundary가 조건부 error를 관찰하게 합니다.
- `deterministic_clock`은 clock을 두 번 읽고 두 값이 모두 `17000000`임을 assert합니다.

`runtime_validation = "boundary"`이므로 각 scenario call은 facade clause도 검사합니다. 마지막 Python `cott verify`는 네 scenario를 모두 test observation으로 기록했고, isolated-loopback sandbox가 있었으므로 `local_http`는 `unobserved`가 아닙니다. semantic coverage는 `observed=11 trust_declaration=4`입니다. `read_text`, `copy_text`, `fetch_local`의 모든 clause가 observed이고, `store_and_load`와 `sample_index`의 네 clause는 trust declaration으로 남습니다. requirement는 `COPY_IS_ATOMIC`이 `filesystem_replace_failure`를 통해 `observed`이고 나머지 넷은 `unverified`입니다. observation은 bounded evidence이며 증명이 아닙니다.

`COPY_READS_THROUGH_READ_TEXT`에는 연결된 검사가 없어 `unverified`로 남습니다.

## Kotlin mirror

`examples/kotlin/features/effects-selection`은 같은 계약을 가집니다. Kotlin runner에는 `http`와 `failure` fixture backend가 없으므로 `local_http`와 `filesystem_replace_failure`는 그곳에서 실행되지 않고 `COPY_IS_ATOMIC`은 `unverified`로 남습니다. 마지막 Kotlin `cott verify`는 `filesystem_copy`와 `deterministic_clock`을 통과시키고 semantic coverage `observed=7 unknown=8`을 기록했습니다. `read_text`의 모든 clause와 `copy_text`의 success, `InputMissing` payload, `InputMissing` clause는 observed이고, `copy_text`의 `OperationFailed` allowance와 `fetch_local`, `store_and_load`, `sample_index`의 모든 clause는 `unknown`입니다. Kotlin runner는 실행된 scenario가 닿지 않는 effectful clause를 trust declaration이 아니라 `unknown`으로 보고하기 때문입니다. 다섯 requirement는 모두 그곳에서 `unverified`입니다. Kotlin은 이미 nanosecond를 반환하는 `CottRuntime.fixtureClockNs`로 fixture clock을 읽고, Python adapter는 millisecond를 반환하며 구현이 이를 변환합니다. 계약은 같습니다.

## 실행

생성 후 Python project에서 `python app.py`를 실행하면 fixture scenario가 실행하는 public facade를 나열합니다. app은 file, server, subprocess, wall-clock observation을 만들지 않으며, fixture scenario는 compiler의 isolated verification workflow에서만 실행됩니다.
