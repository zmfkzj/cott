# contracts-evidence

## 목적
이 dependency-free Cott v0.8 기능 프로젝트는 순수 함수 하나를 계약과 기록된 evidence까지 종단 간에 검사할 수 있을 만큼 작게 유지합니다. 일반 emission 뒤 다음처럼 실행합니다.

```sh
PYTHONPATH=generated/python .venv/bin/python python/app.py
```

앱은 생성된 `curriculum.contracts_evidence.assess_label` facade를 누락된 label, 짧은 label, 유효한 label로 호출합니다. 생성된 `Missing` 또는 payload를 가진 `TooShort(actual=...)` error를 출력한 뒤 허용된 label을 출력합니다.

## 합성된 계약
- `AcceptedLabel(Str)`에는 `where self.len > 0`가 있습니다. `LabelAssessment`는 직접 `text: Str`를 유지하고 `length: U64`를 기록하며 refined `label: AcceptedLabel`도 유지합니다. invariant는 `text.len == length`와 `text == label.value`를 요구하므로 canonical constructor로 만든 결과의 길이가 오래되었거나 refined label이 다르면 실패합니다.
- `assess_label`은 `request.minimum_length > 0`을 요구하고 `errors complete`를 선언합니다. `request.label`이 `Option.Nothing`이면 정확히 `Missing`, 그다음 제시된 label이 최소 길이보다 짧으면 `TooShort`, 그 밖의 유효한 요청은 모두 `Ok`입니다. 성공 obligation `value.text.len >= request.minimum_length`와 payload obligation `actual.len < request.minimum_length`가 결과를 요청과 연결합니다. 길이는 Unicode scalar 개수인 `.len`입니다.
- `doc`은 절이 열어 둔 부분을 정합니다. `TooShort.actual`과 허용된 `text`는 제시된 label 그대로입니다. 두 scenario가 바로 이것을 검사합니다. `short_label_reports_offered_text`는 최소 3에서 `"ok"`에 대해 `TooShort(actual: "ok")`를, `accepted_label_is_reported_unchanged`는 `text == "evidence"`를 기대합니다.
- rule 합성(`rule`, `override`, `delete`)은 rule을 함수에 실제로 적용하는 `grammar/assignment-rule`에서 다룹니다. rule 절은 `Option` payload를 match하거나 struct field를 읽을 수 없으므로 이 프로젝트는 실패 조건을 함수 자체에 적습니다.

## 검사할 evidence
일반 emission은 compiler 소유 artifact를 만듭니다. full verification은 `generated/generation.json`의 artifact snapshot을 인증하며, manifest의 semantic-coverage policy는 finalize된 clause evidence로 별도 gate를 평가합니다.

| 경로 | 정확한 기록 field | 의미 |
| --- | --- | --- |
| `.snapshots[.current].verification.limits` | `proof_node_limit`, `proof_branch_limit`, `candidate_limit`, `lifecycle_limit` | 적용된 non-default budget: `257`, `65`, `17`, `5`입니다. |
| `.snapshots[.current].verification.contract_proofs` | `algorithm`, `version`, `limits`, `contracts` | 각 proof obligation에는 `kind`, `symbol`, `status`, 선택적 `clauses`, `reason`, `model`이 있습니다. `status`는 실행 주장이 아닌 별도의 static proof 결과(`proved`, `disproved`, `unknown`)입니다. |
| `.snapshots[.current].verification.static` | `checker`, `runtime_signatures`, `grade`, `status` | static signature/type-check capability이며 `grade`는 `static proof`입니다. |
| `.snapshots[.current].verification.runtime_capability` | `grade`, `sandbox`, `status` | runtime verification capability이며 `grade`는 `runtime check`입니다. |
| `.snapshots[.current].verification.contract_tests.contracts[]` | `symbol`, `clause_id`, `span`, `evidence[]` | 모든 clause가 별도 test evidence를 유지합니다. 각 `evidence[]` entry는 `grade`, `mode`, `valid_cases`, `reason`을 가지며, 실제로 실행한 valid case만 `test observation`을 얻습니다. case가 없거나 conditional clause가 실행되지 않으면 이유와 함께 `unobserved`입니다. |
| `.snapshots[.current].verification.contract_tests.scenarios[]` | `scenario_id`, `grade`, `assertions[]` | scenario 실행과 각 assertion의 grade입니다. |
| `.snapshots[.current].semantic_coverage` | `clauses`, `summary`, `policy` | canonical clause inventory와 runner evidence를 join한 semantic-policy 결과로 selected-count, pass/fail, violation을 포함합니다. |

이 경로는 `jq` selector입니다. `current`는 self-contained record의 `snapshots` map에 대한
digest 참조입니다. 예를 들어
`jq '.snapshots[.current].semantic_coverage' generated/generation.json`으로 읽습니다.

`[[verification.coverage.rules]]`는 `curriculum.contracts_evidence.assess_label`의 `ensures:2`(성공), `error:5`(`Missing`), `error:6`(`TooShort`) clause를 선택합니다. `errors complete` 자체가 clause 4입니다. `unobserved`, `trust declaration`, `unknown`은 어느 것도 허용하지 않으므로, bounded runner case나 scenario가 선택된 clause를 각각 실제로 실행하지 않으면 verification이 실패합니다.

`trust declaration`도 가능한 clause-evidence grade이지만, `boundary` mode의 순수 `effects []` 예제가 이를 주장하면 안 됩니다. 이는 verifier가 의도적으로 실행하거나 증명하지 않는 선언(예: effectful 작업 또는 off-mode optional check)을 위한 등급입니다. static proof, runtime check, test observation, unobserved, trust declaration을 하나의 “verified” label로 합치지 마세요. 관찰은 bounded evidence입니다. 실행한 case가 통과했음을 보일 뿐 모든 입력에 대해 성립함을 보이지는 않습니다.
