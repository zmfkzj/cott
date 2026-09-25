# assignment-rule

## 예제 목적
접근 코드 검증기에서 기본 규칙을 합성하고 성공 조건을 재정의하며 이전 형식 오류 허용을 삭제합니다.

## 핵심 포인트
- `BaseAccessCodeRule`은 성공 값의 길이가 한 글자 이상이도록 하고 `LegacyFormat`을 허용합니다. `StrictAccessCodeRule`은 성공 길이 조건을 네 글자 이상으로 `override`하고 그 오류 허용을 `delete`합니다.
- `validate_access_code`는 길이가 네 글자 이상이면 입력을 바꾸지 않고 반환합니다. 공백을 다듬지 않습니다. 조건부 오류와 `errors complete`는 빈 입력에 `EmptyCode`, 그 밖의 짧은 입력에 `TooShort`, 나머지 입력에 성공을 요구합니다.
- 시나리오는 빈 코드, 짧은 코드, 이전 형식 접두어가 붙은 코드를 관찰합니다. 별도의 공백 다듬기 동작은 확인하지 않습니다.
