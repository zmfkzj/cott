# artifact-pipeline

## 예제 목적
빌드 단계 의존성을 검증하고 결정적인 아티팩트 파이프라인 순서 하나로 변환합니다.

## 핵심 포인트
- `topologically_order_steps`는 결과를 닫힌 intrinsic으로 기술합니다. 성공하면 순서는 단계 이름의 순열(`permutation_by`)이고, 모든 의존 단계가 그것을 필요로 하는 단계보다 앞에 옵니다(`dependency_ordered_by`). `errors complete`로 다섯 conditional error가 실패 명세 전체가 되며 우선순위는 빈 이름, 중복 이름, 알 수 없는 의존성, 자기 의존성, 사이클 순입니다. 그 밖의 입력은 모두 성공해야 합니다.
- 동점 처리는 formal clause로 표현할 수 없으므로 requirement `READY_STEPS_IN_NAME_ORDER`가 맡습니다. 준비된 단계 가운데 이름이 Unicode code point 순서로 가장 작은 단계가 다음에 옵니다. scenario `ready_steps_in_name_order`는 입력 순서, FIFO Kahn 큐, 큰 이름 우선이 각각 다른 유효 순서를 내는 입력 하나로 이를 검사합니다.
- `plan_pipeline`은 같은 formal clause를 반복하고, 순서는 공개 `topologically_order_steps` facade에서 받아야 합니다(`PLAN_USES_ORDERING_FACADE`). 연결된 assertion은 plan이 동점 처리된 순서를 담는지 관측합니다. facade 호출 자체는 관측하지 않습니다. 그 호출의 유일한 흔적은 `plan_pipeline` 호출 중에 기록되는 중첩 facade의 clause 관측입니다.
- 오류 scenario는 각각 조건 하나를 첫 번째 적용 조건으로 만들고, 뒤의 조건도 모두 참이 되게 합니다. 조건을 다른 순서로 검사하는 구현은 그 scenario에서 runtime conditional-error 의무를 어깁니다.
- 단계는 `List[BuildStep]`으로 입력 순서를 유지합니다. 각 단계의 `needs`는 `Set[Str]`입니다. 빈 이름은 고정된 25자 Unicode `White_Space` 표의 문자로만 이루어진 이름이며, 타깃의 `strip`/`trim`이 지우는 문자와는 다릅니다. U+FEFF와 U+001C는 유효한 이름입니다.

## 증거
`cott verify`가 현재 snapshot을 인증합니다. semantic coverage는 clause 14개를 모두 `observed`로 기록합니다(unobserved 0, unknown 0, trust declaration 0). 자동 candidate는 성공 clause와 빈 이름 오류에만 도달합니다. 각 함수의 나머지 오류 clause 4개는 scenario가 관측합니다. `topologically_order_steps`는 이 4개 관측을 `plan_pipeline` 안의 중첩 facade 호출을 통해서만 받습니다. `cott requirements`는 두 requirement를 모두 `observed`로 보고합니다. 각각 입력 하나에 근거한 유한한 증거이며 증명이 아닙니다. 이 snapshot에서 두 facade는 아래 독립 corpus도 통과합니다(각 3133 케이스).

## 독립 수용 검사
`check_semantics.py`는 동점 처리까지 포함한 순서 규칙 전체를 검사하는 독립 순열 오라클입니다. `cott verify`, compiler proof, `semantic_coverage`가 아닙니다.

범위는 유한합니다. 노드 3개 이하인 모든 labeled graph와, 더 큰 DAG, Unicode 빈 이름, 오류 우선순위를 다루는 명시 케이스로 구성됩니다. 유효한 위상 정렬이 여럿이면 사전순으로 가장 작은 것을 기대합니다.

```bash
.venv/bin/python check_semantics.py --project .
```

해당 인터프리터에서 컴파일러가 생성하고 검증한 출력이 필요합니다. 공개 facade `topologically_order_steps`와 `plan_pipeline`이 같은 corpus를 통과해야 합니다.
