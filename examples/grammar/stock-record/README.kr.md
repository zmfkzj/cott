# stock-record

## 예제 목적
유효한 입력을 요구하는 계산 함수와 원시 레코드를 검증해 그 함수에 위임하는 함수를 분리해 보여 주는 예제입니다.

## 핵심 포인트
- `value_record`는 음수가 아닌 주식 수와 가격을 `requires`로 요구하므로, 위반은 `Result`가 아니라 호출자의 계약 오류입니다. 곱이 유한하지 않으면 `ValuationOverflow`를 반환하고, 성공 값이 유한하고 음수가 아님(`0.0 <= value <= MAX_F64`)을 형식 절로 선언합니다.
- `value_stock_record`는 검증을 우선순위 순서의 조건부 오류로 선언합니다. 빈 이름의 `EmptyName`, `NegativeShares`, NaN 또는 무한대 가격의 `NonFinitePrice`, 그다음 `NegativePrice`입니다. `I64`와 `F64`의 곱은 절로 쓸 수 없으므로 `ValuationOverflow`는 무조건 오류로 남습니다.
- `doc`과 requirement가 위임을 선언합니다. 유효한 레코드는 공개 `value_record` facade를 호출해 평가하고 그 결과를 그대로 반환합니다. 시나리오는 구체적인 레코드와 오버플로하는 레코드에서 `value_record`를 관찰하고, 두 경우 모두 `value_stock_record`가 같은 결과를 반환함을, 그리고 처음 적용되는 조건이 `NegativePrice`인 레코드를 관찰합니다. 두 requirement는 이 입력들에 대해 `observed`입니다.
- 검증되지 않은 것: Cott는 결과가 같다는 것만 관찰할 뿐 구현이 실제로 facade를 호출하는지는 관찰하지 않습니다. 시나리오는 NaN이나 무한대 가격을 만들 수 없으므로 `NonFinitePrice` 조건은 semantic coverage에서 `unknown`으로 남으며, 실제 호출에서 facade 런타임 검사로만 강제됩니다.
