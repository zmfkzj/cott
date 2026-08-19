# portfolio-cost

## 예제 목적
구조체 목록을 순서대로 계산하면서 계약과 오류 도메인으로 포트폴리오 평가를 표현하는 예제입니다.

## 핵심 포인트
- `Holding`은 `I64` 주식 수와 `F64` 가격을 가지며, `calculate_portfolio_cost`는 성공한 총액이 0 이상임을 `ensures`로 선언합니다.
- `PortfolioError`는 음수 주식 수, 비유한 가격, 음수 가격, 합계 오버플로를 구분합니다.
- Python 구현은 목록 순서대로 첫 오류에서 멈추고, 각 곱셈과 누적 덧셈 뒤 비유한 값을 검사해 `TotalOverflow`를 반환합니다.
