# process-bar

## 예제 목적
바이트 페이로드를 검증하고 순수하게 처리한 뒤 메타데이터를 출력에 보존하는 관찰된 전체 생성 조합을 보여 줍니다.

## 핵심 포인트
- `process_bar`는 구별되는 생성 `foo.bar` facade 그래프를 `validate_payload -> process_payload_bytes -> build_output` 순서로 보존합니다.
- 이 그래프의 모든 함수는 순수합니다. 검증과 선언된 처리 `Err` 값은 변경 없이 전파하며, 빈 페이로드는 `InvalidPayload`가 됩니다.
- `build_output`은 처리된 바이트와 검증된 페이로드의 원래 크기·형식을 받습니다.
