# fractional-range-values

## 예제 목적
제약된 실수 단계와 출력 한도를 사용해 유한한 반열린 부동소수점 범위를 구성하는 예제입니다.

## 핵심 포인트
- `PositiveStep`은 0보다 큰 `F64`, `OutputLimit`은 1부터 10000까지의 `U32`를 `where` 제약으로 표현합니다.
- `build_bounded_range`는 비유한 `start`, `stop`, `step`을 먼저 `NonFiniteInput`으로 거부하고, 유한한 입력에서 `start < stop`이면 시작값을 포함하고 끝값을 제외한 `List[F64]`를, `start >= stop`이면 빈 목록을 반환합니다.
- 구현은 매 후보를 `start + index * step`으로 계산하고, 비유한 입력·반올림 뒤 전진하지 않는 단계·한도 초과를 각각 다른 오류로 반환합니다.
