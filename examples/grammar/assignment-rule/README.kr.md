# assignment-rule

## 예제 목적
접근 코드 검증기에 규칙 절을 합성하고, 재정의하고, 삭제하는 예제입니다.

## 핵심 포인트
- `BaseAccessCodeRule`은 이전 형식과 빈 코드 오류를 선언합니다.
- `StrictAccessCodeRule`은 빈 코드 절을 거짓 조건으로 `override`하고, 이전 형식 절을 `delete`한 뒤 `TooShort`를 추가합니다.
- `validate_access_code`는 합성된 규칙을 적용하고 코드를 다듬은 뒤 네 글자보다 짧은 값을 거부합니다.
