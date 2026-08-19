# module-export-snapshot

## 예제 목적
같은 이름 계열의 모듈 입력을 구조체 필드로 독립적으로 보존하는 반환값 계약 예제입니다.

## 핵심 포인트
- `ModuleSnapshot`은 `exported_x`와 `module_x`라는 별개의 `I64` 필드를 가지며, `build_snapshot`도 같은 두 입력을 받습니다.
- 두 `ensures`는 반환 필드가 대응하는 입력과 각각 같음을 선언하여 교차 대입이나 값 변환을 금지합니다.
- Python 구현은 두 인수를 `ModuleSnapshot(exported_x=..., module_x=...)`에 그대로 전달하므로 모든 `I64` 경계값과 같은 입력값도 보존합니다.
