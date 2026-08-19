# trait-protocol

## 예제 목적
이 종단 간 예제는 Cott v0.1의 Protocol/제네릭 함수 학습을 유지하면서, 에이전트가 메서드 본문을 구현하는 Cott 소유의 일반 `SimpleTask` 클래스를 보여 줍니다.

## Protocol과 구체 구현
- `Summarizable`은 `summary() -> Str`, `Prioritizable`은 `priority_level() -> I32`, `Completable`은 `complete()`를 요구합니다. `format_summary[T: Summarizable]`는 요약 Protocol만 받고, `inspect_task[T: Summarizable + Prioritizable]`는 두 읽기 Protocol을 모두 요구합니다.
- `impl SimpleTask for Summarizable + Prioritizable + Completable`는 구체 클래스 계약입니다. Python 애플리케이션이 클래스를 직접 작성하는 대신 `title: Str`, `urgency: I32`, `completed: Bool = false` 상태를 선언합니다.
- 컴파일러가 생성 클래스 셸, 상태, 잠금, 계약 래퍼를 소유합니다. 에이전트는 생성된 메서드 헬퍼 구현만 소유하므로, 애플리케이션 코드는 생성 모듈에서 `SimpleTask`를 import합니다.

## 계약과 관찰 가능한 동작
- 클래스 불변식은 비어 있지 않은 제목과 음수가 아닌 긴급도를 요구합니다. `init(title, urgency)`는 이 사전조건을 반복하고, 초기화 상태가 인수와 일치하며 `completed == false`임을 보장합니다.
- `summary`와 `priority_level`은 순수하고 계약이 있는 읽기 메서드입니다. `complete`도 Cott effect 의미에서 순수하며, `completed`만 수정한다고 선언하고 `old(self.completed)`와 result/수신자 사후조건으로 완료를 설명합니다.
- Python 앱은 생성된 `SimpleTask("Write Documentation", 2)`를 만들고 두 Protocol 소비자에 전달하며, 우선순위를 읽고, 완료 처리한 뒤 결과 값을 출력합니다. 출력은 직접 작성한 Python 구현이 아니라 생성, 제네릭 Protocol 디스패치, 우선순위, 완료 전이를 보여 주기 위한 것입니다.
