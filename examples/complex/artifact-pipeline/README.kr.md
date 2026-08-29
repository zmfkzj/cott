# artifact-pipeline

## 예제 목적
빌드 단계 의존성을 검증하고 실행 가능한 아티팩트 파이프라인 순서로 변환합니다.

## 핵심 포인트
- `plan_pipeline`은 생성된 `curriculum.artifact_pipeline.topologically_order_steps` facade를 호출하고 위상 정렬 오류를 변경 없이 전파합니다.
- 파이프라인 단계는 `List[BuildStep]`으로 입력 순서를 유지하고, 각 단계는 고유한 의존성을 `Set[Str]`에 저장합니다.
- 빈 단계 이름과 중복 이름을 알 수 없는 의존성·자기 의존성·사이클보다 먼저 거부합니다. 준비된 단계는 사전순으로 선택합니다.
