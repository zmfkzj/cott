# declarations-generics

## 예제 목적
이 실행 가능한 기능 예제는 에이전트가 생성한 Python 구현을 통해 고정 폭 레이블 프레임과 원시 바이트를 묶습니다.

## 핵심 포인트
- `core.cott`는 `Label` 별칭, `LABEL_BYTES` `U64` 상수, refinement가 적용된 명목 `NonEmptyLabel` 타입, 그리고 `ByteBlock[const N: U64]` 버퍼 래퍼를 정의합니다. 앱은 facade를 호출하기 전에 이 newtype을 생성합니다.
- `LabelFrame[+T]`는 `value: T` 필드에서 `T`를 양의 위치에만 사용하는 공변 선언입니다. `package_label`은 고정 크기 `Array[U8, LABEL_BYTES]` payload로 이를 구체화합니다.
- `presentation.cott`는 `use`로 이 공개 심볼을 가져오고, 가져온 상수를 공개 타입의 폭으로 사용합니다: `Array[U8, LABEL_BYTES]`, `Buffer[LABEL_BYTES]`, `ByteBlock[LABEL_BYTES]`. 타입이 길이를 고정하므로 길이 사전 조건은 필요 없습니다. 레이블 텍스트, 공변 `LabelFrame[Array[U8, LABEL_BYTES]]`, `ByteBlock[LABEL_BYTES]` 원시 바이트를 담은 heterogeneous `Tuple`을 반환합니다.
- 계약은 tuple을 인덱싱할 수 없으므로 출력 관계는 requirement `RETURNS_INPUTS_UNCHANGED`로 둡니다. tuple은 레이블 텍스트, `LabelFrame(label, values)`, `ByteBlock(raw)`를 그대로 담습니다. scenario `package_label_keeps_inputs`가 입력 하나에 대해 tuple 전체를 비교하며 연결된 검사입니다.
