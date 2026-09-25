# fractional-range-values

## 예제 목적
양수 `F64` 단계와 출력 한도라는 제약된 입력으로 유한한 반열린 부동소수점 범위를 구성하는 예제입니다.

## 핵심 포인트
- `PositiveStep`은 0보다 큰 `F64`, `OutputLimit`은 1부터 10000까지의 `U64`를 감싸며, 두 제약 모두 facade 경계에서 검사하는 `where` refinement입니다.
- `build_bounded_range`는 성공한 목록의 길이가 `limit` 이하이고 `start >= stop`일 때에만 비어 있으며, NaN 또는 무한대인 `start`, `stop`, `step`이 `NonFiniteInput`을 반환한다는 것을 형식 절로 선언합니다. `MAX_F64`는 그 조건에 쓰는 가장 큰 유한 binary64 값입니다.
- `doc`은 각 값을 곱셈 뒤 한 번, 덧셈 뒤 한 번 반올림한 `start + index * step`으로 정의합니다. `StepDoesNotAdvance`와 `OutputLimitExceeded`는 모든 후보에 의존하고 절은 후보 전체를 한정할 수 없으므로, `doc`에 서술한 무조건 오류로 남기고 시나리오와 연결된 requirement 두 개로 뒷받침합니다.
- 시나리오는 단계 `0.1`의 정확한 목록(누적 합은 `0.9999999999999999`로 끝나는 11개 값을 반환함), 한도를 정확히 채운 경우와 넘친 경우, 2^53에서 전진하지 않는 단계와 한도 우선순위를 관찰합니다. 두 requirement는 `observed`이며, 이는 이 입력들에 대한 제한된 증거일 뿐 다른 범위에 대한 증명이 아닙니다.
- 검증되지 않은 것: 시나리오는 NaN이나 무한대를 만들 수 없고 자동 후보에도 없으므로 `NonFiniteInput` 절은 semantic coverage에서 `unknown`으로 남으며, 실제 호출에서 facade 런타임 검사로만 강제됩니다.
