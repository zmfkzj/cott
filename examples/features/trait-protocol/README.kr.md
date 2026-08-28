# trait-protocol

## 예제 목적
이 종단 간 Cott v0.6 예제는 에이전트가 구현한 메서드로 상속된 `TaskView` 트레이트를 만족하는 Cott 소유의 일반 `SimpleTask` 클래스를 보여 줍니다.

## Protocol과 구체 구현
- `Summarizable`에는 연관 타입 `Summary`가 있고 `summary() -> Summarizable.Summary`를 요구하며, `SimpleTask`는 `Summary = Str`로 지정합니다. `Prioritizable`은 `priority_level() -> I32`, `Completable`은 `complete()`를 요구합니다. `TaskView`는 `Summarizable + Prioritizable`를 상속하므로 `inspect_task[T: TaskView]`는 이름 있는 읽기 뷰를 요구하고, `format_summary[T: Summarizable]`는 요약 Protocol만 받습니다.
- `SimpleTask`는 `TaskView + Completable`를 구현합니다. `TaskLifecycle`은 초기 상태 `Pending`, 종단 상태 `Completed`, 그리고 선언된 `Pending -> Completed` 간선을 가진 리소스입니다. 이 구현은 Python 애플리케이션이 클래스를 직접 작성하는 대신 `title: Str`, `urgency: I32`, `lifecycle: TaskLifecycle` 상태를 선언합니다.
- 컴파일러가 생성 클래스 셸, 리소스 상태 초기화, 잠금, 계약 래퍼를 소유합니다. 에이전트는 생성된 메서드 헬퍼 구현만 소유하므로, 애플리케이션 코드는 생성 모듈에서 `SimpleTask`를 import합니다.

## 계약과 관찰 가능한 동작
- 클래스 불변식은 비어 있지 않은 제목과 음수가 아닌 긴급도를 요구합니다. `init(title, urgency)`는 이 사전조건을 반복하고 초기화된 제목과 긴급도가 인수와 일치함을 보장합니다. 생략된 `lifecycle` 매개변수에는 리소스 초기 상태 `TaskLifecycle.Pending`가 적용됩니다.
- `summary`와 `priority_level`은 순수하고 계약이 있는 읽기 메서드입니다. `complete`의 필수 `Pending -> Completed` 전이는 `TaskLifecycle.Pending`을 요구하며 `true`를 반환함을 보장합니다. 해당 헬퍼는 생성된 `TaskLifecycle_Completed` 싱글턴을 할당합니다.
- Python 앱은 생성된 `SimpleTask("Write Documentation", 2)`를 만들고 제네릭 소비자에 전달한 뒤, `Dyn(value=task, trait=TaskView)`로 명목상 래핑합니다. `inspect_dyn(Dyn[TaskView]) -> Str`는 정확히 선언된 트레이트 뷰를 받아 요약, 우선순위, 리소스 기반 완료 출력과 함께 `Dyn: Write Documentation (urgency: 2)`를 출력합니다.
