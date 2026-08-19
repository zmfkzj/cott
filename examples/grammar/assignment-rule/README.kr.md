# assignment-rule

## 예제 목적
`@rule`의 상속, 계약 재정의, 오류 삭제를 하나의 파싱 함수에 적용하는 예제입니다.

## 핵심 포인트
- `BaseAssignmentRule`은 성공한 `Assignment`의 이름이 비어 있지 않음을 보장하고 `MissingEquals` 오류를 선언합니다.
- `StrictAssignmentRule`은 이름 조건을 길이 2 이상으로 `override`하고, 상속한 `MissingEquals` 오류를 `delete`한 뒤 비어 있지 않은 값 조건과 `EmptyName` 오류를 추가합니다.
- `parse_assignment`는 `rule StrictAssignmentRule`을 사용하며, Python 구현은 첫 `=`로 분리하고 양쪽을 다듬은 뒤 이름이 한 글자 이하이거나 값이 비었을 때 `EmptyName`을 반환합니다.
