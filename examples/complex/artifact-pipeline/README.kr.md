# artifact-pipeline

## 예제 목적
빌드 단계 의존성을 검증하고 실행 가능한 아티팩트 파이프라인 순서로 변환합니다.

## 핵심 포인트
- `plan_pipeline`은 생성된 `curriculum.artifact_pipeline.topologically_order_steps` facade를 호출하고 위상 정렬 오류를 변경 없이 전파합니다.
- 파이프라인 단계는 `List[BuildStep]`으로 입력 순서를 유지하고, 각 단계는 고유한 의존성을 `Set[Str]`에 저장합니다.
- 빈 단계 이름과 중복 이름을 알 수 없는 의존성·자기 의존성·사이클보다 먼저 거부합니다. 준비된 단계는 사전순으로 선택합니다.

## 독립 수용 검사
`check_semantics.py`는 자체 순열 오라클을 쓰는 실행 가능한 corpus다. Cott DSL은 그래프 값 시나리오 입력이나 보편 그래프 조건을 표현할 수 없으므로 이 스크립트가 수용 검사다. `cott verify`가 아니고, compiler proof도, `semantic_coverage`도 아니다.

범위는 유한하다. 노드 3개 이하인 모든 labeled graph와, 더 큰 DAG·오류 우선순위는 명시 케이스만 둔다. 준비된 단계의 동점은 사전순으로 가장 작은 유효 위상 정렬이다.

```bash
.venv/bin/python check_semantics.py --project .
```

해당 인터프리터에서 컴파일러가 생성·검증한 출력이 필요하다. 공개 facade `topologically_order_steps`와 `plan_pipeline`이 같은 corpus를 통과해야 한다. `plan_pipeline`은 정렬 오류를 그대로 전파해야 한다.
