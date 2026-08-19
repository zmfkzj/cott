# stock-input-validation

## 예제 목적
`where` 제약이 있는 `newtype`을 원시 주식 입력 검증과 구조체 생성에 연결하는 예제입니다.

## 핵심 포인트
- `StockName`, `Shares`, `Price`는 각각 비어 있지 않은 문자열, 0 이상 정수, 0 이상 실수를 `where`로 나타냅니다.
- 성공 시 `validate_stock_input`은 세 명목 타입으로 구성된 `StockInput`을 반환합니다.
- 구현은 빈 이름, 음수 주식 수, NaN·무한 가격, 음수 가격 순으로 첫 오류를 반환하며 공백만 있는 이름과 음의 0 가격은 허용합니다.
