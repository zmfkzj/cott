# trait-protocol

## 예제 목적
이 Cott v0.7 레슨은 트레이트 상속, 선택, 정확한 런타임 뷰, 비동기 상태 소유권을 하나의 `SimpleTask` 구현으로 묶습니다.

## 트레이트 선택과 정확한 타입
- `Summarizable`는 `summary() -> Summarizable.Summary`로 연관 타입 `Summary`를 보존합니다. 공변 `TaskView[+T]`는 이를 `Prioritizable`과 함께 상속하고 `display`에 `T`를 사용합니다. `SimpleTask`는 `TaskView[Str]`를 선택하고 `Summary = Str`를 지정하므로, `Dyn[TaskView[Str]]`는 구조적 대체물이 아니라 정확한 제네릭 트레이트 identity를 가집니다.
- 하나의 impl은 sync와 async 트레이트 슬롯을 섞을 수 없으므로 모든 유효 슬롯은 async입니다. `summary`와 `priority_level`은 절이 결과를 정하는 명시적 메서드입니다(`result == self.title`, `result == self.urgency`). `display`는 `specialize SimpleTask for TaskView[Str]`로 선택되어 `specialized_display`를 거쳐 dispatch되며, 그 세 절(`starts_with(result, "specialized: ")`, `ends_with(result, receiver.title)`, `result.len == receiver.title.len + 13`)이 텍스트를 정확히 정합니다. `category`는 자체 메서드 없이 `result == "default"`를 보장하는 `default_category`를 거쳐 dispatch됩니다. 트레이트 메서드에는 절이 없고, 선택된 free function의 계약이 dispatch된 슬롯의 계약입니다.
- `task_factory() -> Factory[SimpleTask]`는 인스턴스를 만들지 않고 생성된 `SimpleTask` 클래스 자체를 반환합니다. Python `Factory` boundary는 정확히 그 클래스만 받습니다. 앱은 factory를 호출하기 전에 그 identity 검사를 출력합니다.
- `inspect_dyn`은 `Dyn[TaskView[Str]]` 뷰를 통해 메서드를 await합니다. 절은 트레이트 메서드를 호출할 수 없으므로 requirement `DYN_VIEW_RETURNS_SUMMARY`가 결과는 뷰의 `display()`나 `category()`가 아니라 `summary()`라고 규정합니다. 작성된 scenario는 정확한 동적 summary assertion에 이 requirement를 연결합니다.

## 상태와 관찰 가능한 동작
- 컴파일러가 `title`, `urgency`, `lifecycle`, `completion_count`, 초기화, 잠금, wrapper를 소유합니다. 불변식은 비어 있지 않은 제목, 음수가 아닌 긴급도, 음수가 아닌 완료 횟수를 요구하고, `init(title, urgency)`는 호출자가 준 두 필드를 보존합니다.
- `await task.complete()`가 유일한 명시적 async 상태 전이입니다. 이는 `lifecycle`을 `Pending -> Completed`로만 바꾸고, 비리소스 `completion_count`를 `modifies` 아래 증가시키며, `old(self.completion_count)`로 그 증가를 명시합니다. 전이가 리소스 field 갱신을 소유하므로 `modifies`는 의도적으로 그 field를 이름 붙이지 않습니다.
- 앱은 명시적, specialized, default, Dyn, 우선순위, 완료 호출을 모두 await합니다. 두 번째 `await task.complete()`에는 선언된 `Completed -> Completed` 간선이 없으므로 생성된 boundary가 transition 위반을 발생시키며, 예제는 그 오류를 잡거나 숨기지 않습니다.

## Evidence
- bounded runner case는 `init`으로 `SimpleTask`를 만들고 `init`, `summary`, `priority_level`, `complete`의 절과 `display`, `category`를 포함한 모든 슬롯의 불변식을 관찰합니다. Python 후보 생성기는 `default_category`와 `specialized_display`의 트레이트 타입 `receiver` 입력을 만들 수 없으므로, 이 프로젝트에서 두 함수의 `ensures` 절은 `unknown`(관찰되지 않음)으로 남습니다.
- Python과 Kotlin에 동일하게 작성한 `dyn_view_dispatches_summary` scenario는 공개 facade로 `SimpleTask(title: "Launch", urgency: 1)`를 만들고 `task.summary()`를 호출하며, task를 `Dyn[TaskView[Str]]`로 감싼 다음 `inspect_dyn(view)`의 결과가 정확히 `"Launch"`인지 확인합니다. requirement는 마지막 assertion(2번)에 연결됩니다. 앱은 별도로 다른 결과를 내는 특수화된 `display()`와 기본 `category()`도 보여 줍니다.
- `cott verify`는 이 프로젝트와 Kotlin 미러(`examples/kotlin/features/trait-protocol`)에서 이 scenario를 실행하고 snapshot을 인증했습니다. Python은 두 assertion을 모두 `test observation`으로 기록했고, Kotlin runner는 두 assertion과 함께 scenario를 `passed`로 보고했습니다. `cott requirements`는 두 프로젝트 모두 `current` snapshot 기준으로 `DYN_VIEW_RETURNS_SUMMARY`를 `observed`로 보고합니다. 이는 하나의 task 값에 대한 bounded evidence이지 requirement의 증명이 아닙니다. 앱의 `Dyn:` 줄은 별도의 외부 regression이며 Cott scenario evidence는 아닙니다.
