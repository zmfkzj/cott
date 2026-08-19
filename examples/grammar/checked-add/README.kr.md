# checked-add

## 예제 목적
입력보다 넓은 반환 정수형과 결과 범위 계약을 외부 Python 구현에 연결하는 예제입니다.

## 핵심 포인트
- `checked_add`는 두 `I32`를 받아 `I64`를 반환하고, `ensures`로 가능한 정확한 합계 범위 `-4294967296`부터 `4294967294`까지를 선언합니다.
- 이 범위에서는 두 32비트 부호 정수의 합이 `I64`에서 오버플로하지 않으므로 선언된 오류가 없습니다.
- `cott.toml`의 구현 매핑은 함수를 `cott_bindings.curriculum.checked_add.checked_add:checked_add`에 연결하며, Python 바인딩은 두 인수를 그대로 더합니다.
