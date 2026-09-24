# artifact-pipeline

## 예제 목적
빌드 단계 의존성을 검증하고 실행 가능한 아티팩트 파이프라인 순서로 변환합니다.

## 핵심 포인트
- `plan_pipeline`은 생성된 `curriculum.artifact_pipeline.topologically_order_steps` facade를 호출하고 위상 정렬 오류를 변경 없이 전파합니다.
- 파이프라인 단계는 `List[BuildStep]`으로 입력 순서를 유지하고, 각 단계는 고유한 의존성을 `Set[Str]`에 저장합니다.
- 빈 단계 이름과 중복 이름을 알 수 없는 의존성·자기 의존성·사이클보다 먼저 거부합니다. 준비된 단계는 사전순으로 선택합니다.

## 독립 수용 검사
계약은 `errors complete`를 명시적으로 선택한다. 정상 입력은 성공해야 하고 조건부 오류는 선언 순서의 우선순위를 지킨다. 닫힌 술어가 이름의 중복 횟수 보존, 의존 순서, 그래프 오류를 검사한다. 중첩 값 scenario는 public builder 없이 정상 체인·사이클·겹치는 오류 조건을 실행한다. `check_semantics.py`는 문서가 요구하는 사전식 동점 처리까지 검사하는 독립 순열 오라클로 유지한다. `cott verify`, compiler proof, `semantic_coverage`와는 별개다.

범위는 유한하다. 노드 3개 이하인 모든 labeled graph와, 더 큰 DAG·오류 우선순위는 명시 케이스만 둔다. 준비된 단계의 동점은 사전순으로 가장 작은 유효 위상 정렬이다.

빈 이름은 타깃의 `strip`/`trim`이 아니라 고정된 Unicode `White_Space` 25개 문자로 정의한다. U+FEFF와 U+001C는 빈 이름이 아니다. 독립 corpus에 이 경계값을 포함한다.

`cott requirements --project . --format json`은 선언된 검사 연결, 실제 유한 범위 관측, 미검증 요구사항을 구분한다. 연결된 scenario의 성공은 증거이며 요구사항 전체의 증명이 아니다.

```bash
.venv/bin/python check_semantics.py --project .
```

해당 인터프리터에서 컴파일러가 생성·검증한 출력이 필요하다. 공개 facade `topologically_order_steps`와 `plan_pipeline`이 같은 corpus를 통과해야 한다. `plan_pipeline`은 정렬 오류를 그대로 전파해야 한다.
