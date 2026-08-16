# cott

`cott`는 계약 우선(contract-first) DSL을 위한 Rust 컴파일러입니다. 구현 본문이 없는 `.cott` 모듈은 공개 타입, 함수, 계약(contract), 오류를 선언합니다. 컴파일러는 미구현(unresolved)된 Python 함수 구현을 에이전트에 요청하고, 해당 선언을 강제하는 공개 퍼사드(facade)가 포함된 패키지를 생성하여 배포합니다.

`architecture.md`는 규범적인 v0.1 표준 사양서입니다.

## 생성 우선 커리큘럼 (Generation-first curriculum)

저장소에서 유지 관리하는 커리큘럼에는 총 41개의 프로젝트가 있습니다:

1. **Grammar — 9개 프로젝트:** 선언, 타입, 정제 타입(refinements), 집중 계약 학습.
2. **Simple — 16개 프로젝트:** 재사용 가능한 리프(leaf) 함수 및 생성된 퍼사드를 통해 해당 리프를 호출하는 도메인 명명 최종 연산 생성.
3. **Complex — 16개 프로젝트:** 생성된 퍼사드를 통해 조합되는 검증, 변환, 집계 단계 생성.

`grammar/checked-add`만이 유일한 manifest 바인딩 학습 예제입니다. 나머지 40개 커리큘럼 프로젝트에는 `[target.python.implementations]` 테이블이나 `python/cott_bindings/` 소스가 없습니다. 저장소에 커밋되어 있는 `python/_cott_impl/` 구현체와 `generated/` 트리는 `cott generate`로 생성된 산출물이며, 생성된 코드와 provenance(출처 정보)를 직접 검사할 수 있도록 보존되어 있습니다.

아래 명령어는 설치된 `cott` 바이너리를 사용하며 저장소 루트에서 실행합니다. 소스 체크아웃 환경에서는 `cott` 대신 `cargo run --`을 사용할 수 있습니다. 각 예제의 Python 환경은 다음과 같이 프로비저닝할 수 있습니다:

```bash
UV_PROJECT_ENVIRONMENT=examples/<level>/<project>/.venv \
  uv sync --project examples/<level>/<project>/python
```

## 유일한 바인딩 예제: `checked-add`

`checked-add`는 단 하나의 함수를 노출합니다:

```text
checked_add(left: I32, right: I32) -> I64
```

이 예제만 manifest 심볼이 직접 작성된 Python 코드에 어떻게 매핑되는지 보여줍니다:

```text
examples/grammar/checked-add/
├── cott.toml
├── src/curriculum/checked_add.cott
└── python/
    ├── pyproject.toml
    └── cott_bindings/curriculum/checked_add/
        └── checked_add.py
```

```toml
[target.python.implementations]
"curriculum.checked_add.checked_add" = "cott_bindings.curriculum.checked_add.checked_add:checked_add"
```

이 매핑은 소스 모듈과 심볼을 지정합니다. emit 과정에서 해당 소스를 검증하고, 표준 런타임 위치인 `generated/python/_cott_impl/curriculum/checked_add/checked_add.py`로 복사하며, `generated/python/curriculum/checked_add.py`에 퍼사드를 배포합니다.

```bash
project=examples/grammar/checked-add
cott check --project "$project"
cott fmt --check --project "$project"
cott emit python --project "$project"
cott verify --project "$project"
PYTHONPATH="$project/generated/python" "$project/.venv/bin/python" -c \
  'from curriculum.checked_add import checked_add; print(checked_add(2, 3))'
# 5
```

이 프로젝트는 직접 작성된 `cott_bindings` 트리 또는 구현 매핑을 포함하는 유일한 커리큘럼 프로젝트입니다.

## `.cott`로부터 다른 모든 예제 생성

저장소에는 성공적인 각 생성 결과가 보존되어 있습니다:

```text
examples/<level>/<project>/
├── cott.toml
├── src/curriculum/<module>.cott
├── python/
│   ├── pyproject.toml
│   └── _cott_impl/<exact Cott module path>/<function>.py
└── generated/
```

`checked-add`를 제외한 모든 프로젝트에 동일한 생성 우선 시퀀스를 사용합니다:

```bash
cott check --project examples/<level>/<project>
cott fmt --check --project examples/<level>/<project>
cott emit python --project examples/<level>/<project>
cott generate --agent omp --target python --project examples/<level>/<project>
cott verify --project examples/<level>/<project>
```

이 시퀀스는 커밋된 예제들에 대해 멱등(idempotent)합니다. `generate`는 `current.unresolved`에 남아 있는 함수에 대해서만 에이전트를 호출하며, 이미 승인된 durable 구현체는 재사용됩니다.

`cott emit python`은 계획(planning) 단계입니다. 에이전트를 호출하지 않으며 컴파일러 소유의 메타데이터를 출력하고, 누락된 모든 함수를 `current.unresolved`에 기록하며, 미구현 함수는 공개 퍼사드에서 제외합니다. 따라서 성공적인 emit만으로는 아직 배포 가능한 결과가 아닙니다.

`cott generate --agent omp --target python`은 미구현된 각 공개 함수마다 하나의 함수 단위 에이전트 프로세스를 실행합니다. 승인된 구현체는 다음 경로의 durable 소스가 됩니다:

```text
python/_cott_impl/<exact Cott module path>/<function>.py
```

이 파일들은 바인딩으로 직접 작성된 것이 아니라 `cott generate`로 생성된 것이며 검사를 위해 커밋되어 있습니다. 이후의 emission 작업에서도 유지됩니다. 컴파일러는 검증된 공개 모듈을 `generated/python/` 아래에 배포합니다. `cott verify`는 전체 프로젝트 게이트이며, 필요한 모든 함수가 승인된 구현체를 갖춘 후에만 성공합니다.

조합(composition) 시에도 계약을 우회하지 않습니다. 생성된 최종 함수가 생성된 헬퍼를 호출할 경우, 정확한 공개 Cott 퍼사드에서 헬퍼를 import합니다:

```python
from curriculum.alphabetical_file_groups import classify_filename
```

생성된 코드는 다른 구현 파일이나 `_cott_impl`을 직접 import해서는 안 됩니다. 퍼사드를 통과해야만 모든 호출 엣지에서 헬퍼의 provenance, ABI 검증, `requires`, `ensures`, 선언된 오류가 활성 상태로 유지됩니다.

### 생성된 Grammar 리프

`module-export-snapshot`은 `src/curriculum/module_export_snapshot.cott`에 리프 함수 `build_snapshot`을 선언하며, 승인된 생성 구현체는 계약 옆에 유지됩니다.

```bash
project=examples/grammar/module-export-snapshot
cott check --project "$project"
cott fmt --check --project "$project"
cott emit python --project "$project"       # 출력을 갱신하며, durable 구현체는 resolved 상태 유지
cott generate --agent omp --target python --project "$project"
cott verify --project "$project"
PYTHONPATH="$project/generated/python" "$project/.venv/bin/python" -c \
  'from curriculum.module_export_snapshot import build_snapshot; print(build_snapshot(7, 11))'
```

생성을 통해 `python/_cott_impl/curriculum/module_export_snapshot/build_snapshot.py`가 생성되며, 애플리케이션은 `curriculum.module_export_snapshot.build_snapshot`만 호출합니다.

### 생성된 Simple 조합

`alphabetical-file-groups`는 단일 파일 분류기와 수집 연산을 선언합니다:

```text
group_filenames → classify_filename
```

체크아웃에는 함수당 하나의 생성된 `_cott_impl` 파일이 유지됩니다. 생성된 `group_filenames` 구현체는 `curriculum.alphabetical_file_groups`를 통해 `classify_filename`을 호출합니다.

```bash
project=examples/simple/alphabetical-file-groups
cott check --project "$project"
cott fmt --check --project "$project"
cott emit python --project "$project"       # 출력을 갱신하며, 두 구현체 모두 resolved 상태 유지
cott generate --agent omp --target python --project "$project"
cott verify --project "$project"
PYTHONPATH="$project/generated/python" "$project/.venv/bin/python" -c \
  'from cott_runtime import CottList; from curriculum.alphabetical_file_groups import group_filenames; print(group_filenames(CottList(values=["apple.txt", "Ryan.py", "010.txt", "!note"])))'
```

최종 연산은 입력 순서를 보존하고, 각 항목에 대해 검증된 리프 퍼사드를 호출하며, 처음 발생한 선언 오류를 그대로 전파합니다.

### 생성된 Complex 모듈

`page-build`는 세 단계를 선언합니다:

```text
build_page → render_page_html → escape_page_text
```

생성 결과 `python/_cott_impl/curriculum/page_build/` 아래에 세 개의 durable 파일이 생성 및 유지되며, 생성된 중간 및 최종 구현체는 `curriculum.page_build`에서 의존성을 import합니다.

```bash
project=examples/complex/page-build
cott check --project "$project"
cott fmt --check --project "$project"
cott emit python --project "$project"       # 출력을 갱신하며, 세 구현체 모두 resolved 상태 유지
cott generate --agent omp --target python --project "$project"
cott verify --project "$project"
PYTHONPATH="$project/generated/python" "$project/.venv/bin/python" -c \
  "from curriculum.page_build_types import PageSource; from curriculum.page_build import build_page; print(build_page(PageSource(slug='hello-world', title='Hi & Bye', body='first\nsecond')))"
```

`build_page`는 요청 검증, `render_page_html`은 문서 조합, `escape_page_text`는 이스케이프 처리를 담당합니다. 두 조합 엣지 모두 생성된 계약 퍼사드를 통과합니다.

### FastAPI 연동

`examples/integrations/fastapi-hello`는 FastAPI 공식 [First Steps](https://fastapi.tiangolo.com/tutorial/first-steps/) `GET /` 예제를 어댑트합니다. Cott는 타입이 지정된 `HelloResponse`를 선언하고 `read_root`를 생성하며, 4줄짜리 `python/app.py` 어댑터는 해당 검증 퍼사드를 FastAPI에 등록하기만 합니다.

```bash
project=examples/integrations/fastapi-hello
UV_PROJECT_ENVIRONMENT="$project/.venv" UV_PYTHON=3.14.6 uv sync --project "$project/python"
cott verify --project "$project"
PYTHONPATH="$project/generated/python" "$project/.venv/bin/fastapi" dev "$project/python/app.py"
curl http://127.0.0.1:8000/
# {"message":"Hello World"}
```

### 모듈화된 다중 파일 코드 생성

`examples/modular/order-management`는 여러 `.cott` 소스 모듈에 걸친 코드 생성을 보여줍니다:

```text
store.order.calculate_order → store.order.validate_line
                            ↘ store.catalog.find_item
```

1. `src/store/catalog.cott`는 카탈로그 도메인(`Item`, `Catalog`, `CatalogError`, `find_item`)을 선언합니다.
2. `src/store/order.cott`는 카탈로그 타입을 import하고(`use store.catalog.{Catalog, CatalogError, Item}`), 주문 연산(`Order`, `OrderReceipt`, `OrderError`, `validate_line`, `calculate_order`)을 선언합니다.
3. 생성된 `calculate_order` 구현체는 `store.order`에서 `validate_line`을, `store.catalog`에서 `find_item`을 import하여 생성된 계약 퍼사드를 깔끔하게 통과합니다.

```bash
project=examples/modular/order-management
cott check --project "$project"
cott fmt --check --project "$project"
cott emit python --project "$project"
cott generate --agent omp --target python --project "$project"
cott verify --project "$project"
PYTHONPATH="$project/generated/python" python3 "$project/python/app.py"
```

## 전체 프로젝트 인덱스

그래프 표기는 호출자에서 호출 대상 공개 헬퍼 퍼사드를 가리킵니다. `leaf`는 최종 심볼이 해당 프로젝트의 유일한 공개 함수임을 의미합니다. `checked-add`를 제외하고 이 그래프의 모든 함수는 프로젝트의 `.cott` 선언으로부터 생성됩니다.

### Grammar — 9개 프로젝트

| 프로젝트 | 최종 심볼 | 공개 헬퍼 그래프 |
| --- | --- | --- |
| `checked-add` | `checked_add` | leaf |
| `cta-row` | `decode_row` | leaf |
| `fractional-range-values` | `build_bounded_range` | leaf |
| `module-export-snapshot` | `build_snapshot` | leaf |
| `parse-assignment` | `parse_assignment` | leaf |
| `portfolio-cost` | `calculate_portfolio_cost` | leaf |
| `stock-input-validation` | `validate_stock_input` | leaf |
| `validated-stock` | `value_stock` | leaf |
| `stock-record` | `value_stock_record` | `value_stock_record → value_record` |

### Simple — 16개 프로젝트

| 프로젝트 | 최종 심볼 | 공개 헬퍼 그래프 |
| --- | --- | --- |
| `alphabetical-file-groups` | `group_filenames` | `group_filenames → classify_filename` |
| `billing-system` | `calculate_bill` | `calculate_bill → validate_bill_lines` |
| `calculate-age` | `summarize_age` | `summarize_age → calculate_age_days` |
| `calculator` | `calculate` | `calculate → validate_calculation` |
| `compute-iou` | `compute_iou` | `compute_iou → calculate_intersection_union` |
| `currency-converter` | `convert_currency` | `convert_currency → validate_conversion_request` |
| `decimal-binary` | `convert_binary_decimal` | `convert_binary_decimal → decimal_to_binary \| binary_to_decimal` |
| `json-to-csv` | `serialize_csv` | `serialize_csv → escape_csv_field` |
| `numbers-to-words` | `spell_cardinal` | `spell_cardinal → spell_under_thousand` |
| `random-password-generator` | `generate_password` | `generate_password → required_password_draws` |
| `rock-paper-scissors` | `decide_round` | `decide_round → user_beats_computer` |
| `split-file` | `split_lines` | `split_lines → validate_split_request` |
| `textfile-analysis` | `analyze_text` | `analyze_text → extract_casefolded_words` |
| `tic-tac-toe` | `apply_tic_tac_toe_move` | `apply_tic_tac_toe_move → validate_board_state` |
| `unique-words` | `find_unique_words` | `find_unique_words → normalize_words` |
| `website-connectivity` | `classify_websites` | `classify_websites → classify_observation` |

### Complex — 16개 프로젝트

| 프로젝트 | 최종 심볼 | 공개 헬퍼 그래프 |
| --- | --- | --- |
| `archive-request` | `plan_archive` | `plan_archive → canonicalize_archive_url, compose_archive_plan` |
| `artifact-pipeline` | `plan_pipeline` | `plan_pipeline → topologically_order_steps` |
| `backup-plan` | `plan_backup` | `plan_backup → validate_backup_request, classify_backup_paths` |
| `case-ranking` | `rank_cases` | `rank_cases → order_matching_cases → score_case_overlap` |
| `clip-ranges` | `plan_clip_ranges` | `plan_clip_ranges → range_duration_ms` |
| `color-quantization` | `quantize_colors` | `quantize_colors → rank_palette_colors` |
| `expense-split` | `settle_expense` | `settle_expense → calculate_balances, settle_balances` |
| `experiment-ranking` | `rank_experiments` | `rank_experiments → order_run_ids` |
| `flashcard-schedule` | `schedule_review` | `schedule_review → validate_review_ease` |
| `inventory-reorder` | `plan_reorder` | `plan_reorder → available_stock` |
| `move-2048` | `apply_2048_move` | `apply_2048_move → validate_2048_board, merge_move_line` |
| `page-build` | `build_page` | `build_page → render_page_html → escape_page_text` |
| `publication-workflow` | `transition_publication` | `transition_publication → transition_target` |
| `reputation` | `calculate_reputation` | `calculate_reputation → reputation_delta` |
| `roast-analysis` | `analyze_roast_profile` | `analyze_roast_profile → validate_roast_profile, summarize_roast_samples` |
| `track-metadata` | `normalize_track_metadata` | `normalize_track_metadata → trim_track_draft, format_track_metadata` |

## `process-bar`: 전체 생성 집중 검증용 픽스처

`examples/complex/process-bar`는 9/16/16 커리큘럼 개수 산정에서 제외됩니다. 이 예제는 복합 모듈 전체 생성을 위한 집중 통합 픽스처입니다:

```text
process_bar → validate_payload, process_payload_bytes, build_output
```

이 픽스처에는 구현 매핑이나 `cott_bindings` 소스가 없습니다. 4개의 승인된 생성 구현체는 계약 및 컴파일러 소유 출력 트리와 함께 `python/_cott_impl/foo/bar/` 아래에 보존됩니다.

```bash
project=examples/complex/process-bar
cott check --project "$project"
cott fmt --check --project "$project"
cott emit python --project "$project"       # 출력을 갱신하며, 4개 구현체 모두 resolved 상태 유지
cott generate --agent omp --target python --project "$project"
cott verify --project "$project"
```

전체 생성은 unresolved 심볼마다 하나의 함수 단위 에이전트 프로세스를 호출하고 승인된 4개 구현체를 `python/_cott_impl/foo/bar/` 아래에 유지합니다. `process_bar`는 생성된 `foo.bar` 퍼사드를 통해 3개의 헬퍼를 오케스트레이션하며, `process_payload_bytes`에 선언된 네트워크 effect는 호출자에도 그대로 선언됩니다. 이 픽스처는 manifest 바인딩 학습보다는 완전한 unresolved-to-generated 전이 과정을 검증합니다.
