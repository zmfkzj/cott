# declarations-generics

## 예제 목적
이 실행 가능한 v0.7 기능 예제는 manifest-bound Python 구현을 통해 고정 폭 레이블 프레임과 원시 바이트를 묶습니다.

## 핵심 포인트
- `core.cott`는 `Label` 별칭, `LABEL_BYTES` `U64` 상수, refinement가 적용된 명목 `NonEmptyLabel` 타입, 그리고 `ByteBlock[const N: U64]` 버퍼 래퍼를 정의합니다. 앱은 facade를 호출하기 전에 이 newtype을 생성합니다.
- `LabelFrame[+T]`는 `value: T` 필드에서 `T`를 양의 위치에만 사용하는 공변 선언입니다. `package_label`은 고정 크기 `Array[U8, 4]` payload로 이를 구체화합니다.
- `presentation.cott`는 `use`로 이 공개 심볼을 가져오고, literal 고정 크기 `Array[U8, 4]` 및 `Buffer[4]` 공개 타입을 사용하며, `requires values.len == LABEL_BYTES`로 `LABEL_BYTES`를 관찰 가능하게 유지합니다. 별칭 값, 공변 `LabelFrame[Array[U8, 4]]`, `ByteBlock[4]` 원시 바이트를 담은 heterogeneous `Tuple`을 반환합니다.
