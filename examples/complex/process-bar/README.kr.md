# process-bar

## 예제 목적
`foo.bar`의 전체 agent 생성 fixture입니다. 바이트 페이로드를 검증하고, 바이트를 순수 처리 단계에 통과시킨 뒤, 페이로드 메타데이터를 보존하는 출력을 만듭니다. `tests/cli.rs`는 고정 구현을 쓰는 가짜 agent로 이 계약을 실행합니다. 이 프로젝트에는 실제 agent가 생성한 출력이 들어 있습니다.

## 핵심 포인트
- `process_bar`가 도메인 이름을 가진 연산입니다. requirement `STAGES_COMPOSE_THROUGH_FACADES`가 root를 명시합니다. 공개 `validate_payload`, `process_payload_bytes`, `build_output` facade를 이 순서로 호출하고, 각 단계의 결과를 다음 단계로 넘기며, 첫 `Err`는 뒤 단계를 호출하지 않고 그대로 반환합니다.
- formal clause가 `InvalidPayload` reason 문구를 뺀 모든 결과를 정합니다. `validate_payload`는 페이로드에 바이트가 없을 때에만 `InvalidPayload`를 반환하고, 그 밖에는 페이로드를 그대로 반환합니다. `process_payload_bytes`는 조건 없는 `errors complete`를 선언하므로 반드시 성공하고 입력 바이트를 반환해야 하며, options는 결과를 바꾸지 않습니다. `build_output`은 세 인자를 그대로 담습니다. `process_bar`는 `errors complete`를 선언합니다. 빈 바이트이면 `InvalidPayload`를, 그 밖에는 입력 바이트와 `declared_size`, `format`을 담은 출력을 반환합니다.
- `declared_size`는 호출자가 준 메타데이터입니다. 출력으로 전달될 뿐 바이트 수와 비교하지 않습니다.
- scenario `process_bar_composes_stages`는 공개 facade로 root를 두 번 실행합니다. 2바이트 페이로드(`Bytes("6869")`)는 정확히 그 출력을 만들어야 하고, 빈 페이로드는 `InvalidPayload`를 반환해야 합니다. `STAGES_COMPOSE_THROUGH_FACADES`는 이 scenario에 연결되지만, scenario가 관측하는 것은 root의 결과뿐입니다. `process_bar`가 실제로 다른 facade를 호출하는지는 관측하지 못하므로, 같은 결과를 내는 단일 `process_bar` 구현도 검증을 통과합니다.

## 증거
`cott verify`가 현재 snapshot을 인증합니다. semantic coverage는 clause 12개를 모두 `observed`로 기록합니다(unobserved 0, unknown 0, trust declaration 0). 관측은 유한한 자동 candidate와 scenario 하나에서 나오며 전수 검사가 아닙니다. `cott requirements`는 연결된 scenario의 assertion 두 개가 모두 성립했으므로 `STAGES_COMPOSE_THROUGH_FACADES`를 `observed`로 보고합니다. 이 상태는 관측된 두 결과에만 해당하며, requirement가 말하는 facade 호출과 호출 순서는 여전히 검사되지 않습니다.
