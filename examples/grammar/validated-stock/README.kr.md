# validated-stock

## 예제 목적
범위가 검증된 명목 타입을 입력 경계에 두고, 이후 계산의 오류 도메인을 오버플로 하나로 좁히는 예제입니다.

## 핵심 포인트
- `StockName`, `Shares`, `Price`의 `where` 제약은 각각 비어 있지 않은 이름, 0 이상 주식 수, 유한한 binary64 최대값 이하의 가격을 표현합니다.
- `Stock`은 이 세 `newtype`으로만 구성되며, 생성자 검증 실패는 `value_stock`의 `ValuationError`가 아닌 계약 위반입니다.
- `value_stock`은 주식 수와 가격을 한 번 곱하고, 무한대가 되면 `Overflow`, 아니면 0 이상 최대 binary64 이하의 값을 반환합니다.
