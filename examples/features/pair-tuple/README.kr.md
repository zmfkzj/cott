# pair-tuple

## 예제 목적
Cott v0.2의 가변 길이 `Tuple` ABI와 제네릭 타입 매개변수를 사용해 좌표 쌍을 만들고 두 원소의 순서를 바꾸는 예제입니다.

## 핵심 포인트
- `make_coordinate_pair`는 두 `I32`를 `Tuple[I32, I32]`로 만들며, Python 바인딩에서는 불변 native `tuple[I32, I32]` ABI로 표현됩니다.
- `swap_pair[A, B]`는 `Tuple[A, B]`를 `Tuple[B, A]`로 바꾸며 positional indexing으로 서로 다른 두 타입의 순서를 보존합니다.
- 두 함수 모두 `effects []`를 선언하며, 실행 예제는 `(10, 20)`과 교환된 `(20, 10)`을 출력합니다.
