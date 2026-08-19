# parse-assignment

## 예제 목적
성공 조건과 명시적 오류를 갖는 `Result` 파싱 계약을 선언하는 예제입니다.

## 핵심 포인트
- `ensures`는 성공한 `Assignment`의 `name` 길이가 0보다 크도록 보장하고, `MissingEquals`와 `EmptyName`을 함수 오류로 선언합니다.
- 구현은 첫 `=`만 구분자로 사용하고 이름과 값의 앞뒤 공백만 제거하므로, 이후의 `=`와 필드 내부 공백은 보존됩니다.
- 구분자가 없으면 `MissingEquals`, 다듬은 이름이 비면 `EmptyName`을 반환하며 빈 값 자체는 유효합니다.
