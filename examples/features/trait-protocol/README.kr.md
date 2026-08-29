# trait-protocol

## 예제 목적
이 Cott v0.7 레슨은 트레이트 상속, 선택, 정확한 런타임 뷰, 비동기 상태 소유권을 하나의 `SimpleTask` 구현으로 묶습니다.

## 트레이트 선택과 정확한 타입
- `Summarizable`는 `summary() -> Summarizable.Summary`로 연관 타입 `Summary`를 보존합니다. 공변 `TaskView[+T]`는 이를 `Prioritizable`과 함께 상속하고 `display`에 `T`를 사용합니다. `SimpleTask`는 `TaskView[Str]`를 선택하고 `Summary = Str`를 지정하므로, `Dyn[TaskView[Str]]`는 구조적 대체물이 아니라 정확한 제네릭 트레이트 identity를 가집니다.
- 하나의 impl은 sync와 async 트레이트 슬롯을 섞을 수 없으므로 모든 유효 슬롯은 async입니다. `summary`와 `priority_level`은 명시적인 에이전트 헬퍼입니다. `display`는 `specialize SimpleTask for TaskView[Str]`로 선택되어 `specialized_display`를 거쳐 dispatch되고, `category`는 헬퍼 없이 검증된 `default_category` facade를 거쳐 dispatch됩니다. 애플리케이션 출력은 세 경로를 각각 표시합니다.
- `task_factory() -> Factory[SimpleTask]`는 인스턴스를 만들지 않고 정확히 생성된 `SimpleTask` 클래스 객체를 반환합니다. 앱은 factory를 호출하기 전에 그 identity 검사를 출력합니다.

## 상태와 관찰 가능한 동작
- 컴파일러가 `title`, `urgency`, `lifecycle`, `completion_count`, 초기화, 잠금, wrapper를 소유합니다. 불변식은 비어 있지 않은 제목, 음수가 아닌 긴급도, 음수가 아닌 완료 횟수를 요구하고, `init(title, urgency)`는 호출자가 준 두 필드를 보존합니다.
- `await task.complete()`가 유일한 명시적 async 상태 전이입니다. 이는 `lifecycle`을 `Pending -> Completed`로만 바꾸고, 비리소스 `completion_count`를 `modifies` 아래 증가시키며, `old(self.completion_count)`로 그 증가를 증명합니다. 전이가 리소스 field 갱신을 소유하므로 `modifies`는 의도적으로 그 field를 이름 붙이지 않습니다.
- 앱은 명시적, specialized, default, Dyn, 우선순위, 완료 호출을 모두 await합니다. 두 번째 `await task.complete()`에는 선언된 `Completed -> Completed` 간선이 없으므로 생성된 boundary가 transition 위반을 발생시키며, 예제는 그 오류를 잡거나 숨기지 않습니다.
