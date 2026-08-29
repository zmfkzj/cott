# contracts-evidence

## 목적
이 dependency-free Cott v0.8 기능 프로젝트는 manifest binding 하나를 종단 간에 검사할 수 있을 만큼 작게 유지합니다. 일반 emission 뒤 다음처럼 실행합니다.

```sh
PYTHONPATH=generated/python .venv/bin/python python/app.py
```

앱은 생성된 `curriculum.contracts_evidence.assess_label` facade를 누락된 label, 짧은 label, 유효한 label로 호출합니다. 생성된 `Missing` 또는 payload를 가진 `TooShort(actual=...)` error를 출력한 뒤 허용된 label을 출력합니다.

## 합성된 계약
- `AcceptedLabel(Str)`에는 `where self.len > 0`가 있습니다. `LabelAssessment`는 직접 `text: Str`를 유지하고 `length: U64`를 기록하며 refined `label: AcceptedLabel`도 유지합니다. invariant는 `text.len == length`와 `text == label.value`를 요구하므로 canonical constructor로 만든 결과의 길이가 오래되었거나 refined label이 다르면 실패합니다.
- `BaselineLabelRule`은 처음에 `Legacy`와 `Missing`을 허용합니다. `RefinedLabelRule`은 `Missing`을 false 조건부 obligation으로 override하고 `Legacy`를 delete하여 rule-level result payload type 없이 독립적인 rule override/delete를 보여줍니다.
- `assess_label`은 `Result[LabelAssessment, LabelEvidenceError]`를 반환하고 `Missing`을 명시적으로 선언하며 request별 절을 추가합니다. 즉 `request.minimum_length > 0`, 성공 결과의 길이 관계, 그리고 조건부 `Option.Some(text)` error obligation입니다. 중첩 `Result.Err(LabelEvidenceError.TooShort(actual))` guard는 `actual.len < request.minimum_length`인 payload 관계를 기록합니다.
- 불변 field path `value.text`와 `request.minimum_length`, 그리고 `.len` 비교는 proof-v2 difference constraint가 지원하는 형태입니다. binding은 staged generated type을 import하고 `Ok(LabelAssessment(text=label, length=len(label), label=AcceptedLabel(value=label)))` 또는 선언된 `Err` variant만 반환합니다. public facade를 우회하거나 verification output을 만들지 않습니다.

## 검사할 evidence
일반 emission은 compiler 소유 artifact를 만듭니다. full verification은 `generated/generation.json`의 artifact snapshot을 인증하며, manifest의 semantic-coverage policy는 finalize된 clause evidence로 별도 gate를 평가합니다.

| 경로 | 정확한 기록 field | 의미 |
| --- | --- | --- |
| `current.verification.limits` | `proof_node_limit`, `proof_branch_limit`, `candidate_limit`, `lifecycle_limit` | 적용된 non-default budget: `257`, `65`, `17`, `5`입니다. |
| `current.verification.contract_proofs` | `algorithm`, `version`, `limits`, `contracts` | 각 proof obligation에는 `kind`, `symbol`, `status`, 선택적 `clauses`, `reason`, `model`이 있습니다. `status`는 실행 주장이 아닌 별도의 static proof 결과(`proved`, `disproved`, `unknown`)입니다. |
| `current.verification.static` | `checker`, `runtime_signatures`, `grade`, `status` | static signature/type-check capability이며 `grade`는 `static proof`입니다. |
| `current.verification.runtime_capability` | `grade`, `sandbox`, `status` | runtime verification capability이며 `grade`는 `runtime check`입니다. |
| `current.verification.contract_tests.contracts[]` | `symbol`, `clause_id`, `span`, `evidence[]` | 모든 clause가 별도 test evidence를 유지합니다. 각 `evidence[]` entry는 `grade`, `mode`, `valid_cases`, `reason`을 가지며, 실제로 실행한 valid case만 `test observation`을 얻습니다. case가 없거나 conditional clause가 실행되지 않으면 이유와 함께 `unobserved`입니다. |
| `current.semantic_coverage` | `clauses`, `summary`, `policy` | canonical clause inventory와 runner evidence를 join한 semantic-policy 결과로 selected-count, pass/fail, violation을 포함합니다. |

`[[verification.coverage.rules]]`는 실제 `curriculum.contracts_evidence.assess_label`의 `ensures:2`, `error:5` clause를 선택합니다. `unobserved`, `trust declaration`, `unknown`은 어느 것도 허용하지 않으며, 유효·누락·짧음·성공 facade case가 선택된 성공 및 조건부-error obligation을 의미 있는 coverage 대상으로 만듭니다.

`trust declaration`도 가능한 clause-evidence grade이지만, `boundary` mode의 순수 `effects []` 예제가 이를 주장하면 안 됩니다. 이는 verifier가 의도적으로 실행하거나 증명하지 않는 선언(예: effectful 작업 또는 off-mode optional check)을 위한 등급입니다. static proof, runtime check, test observation, unobserved, trust declaration을 하나의 “verified” label로 합치지 마세요.
