# order-management

## 예제 목적

다중 모듈 계약을 보여 줍니다. `store.catalog`은 카탈로그 타입과 조회를 소유하고, `store.order`는 공개 facade를 통해 그 조회를 주문 줄 검증과 조합합니다.

## 핵심 포인트

- `store.catalog`은 `Item`, `Catalog`, `CatalogError`, `find_item`을 소유합니다. `Catalog` invariant(`unique_by(self.items, Item.sku)`)가 SKU를 유일하게 만들어 조회 결과는 하나뿐입니다. `find_item`은 비어 있지 않은 SKU를 요구하고, 그 SKU를 가진 항목을 반환하며, `ItemNotFound`에 요청한 SKU를 담습니다.
- `store.order`는 `OrderLine`(invariant: 비어 있지 않은 SKU), `Order`, `OrderReceipt`, `OrderError`, `validate_line`, `calculate_order`를 소유하고, 카탈로그 모듈의 `Catalog`와 `CatalogError`를 가져옵니다.
- `validate_line`은 `errors complete`를 사용합니다. 수량이 0이 아니면 줄을 그대로 반환하고, 0이면 그 줄의 SKU를 담은 `InvalidQuantity`를 보고합니다.
- `calculate_order`는 조합 루트입니다. formal clause는 빈 주문의 `EmptyOrder`와 영수증의 `order_id`를 다룹니다. 나머지는 requirement가 규정합니다. 검증과 가격 조회는 `validate_line`과 `find_item` facade를 거치고, 줄은 순서대로 처리하되 각 줄을 조회 전에 검증하며, 첫 실패가 결과를 정합니다. 검증 오류는 그대로 전파하고 카탈로그 오류는 `ItemUnavailable(cause)`로 감쌉니다. 합계는 모든 줄을 카탈로그 가격으로 셉니다. `doc`은 센트 단위 합계를 정의하고, `U32` 개수나 `U64` 센트를 넘는 합계는 계약 밖으로 둡니다.

## 증거

- `store.catalog` scenario `lookup_by_sku`는 찾은 항목의 이름과 가격, 그리고 없는 SKU를 확인하며 `RETURNS_CATALOG_ITEM`의 근거입니다.
- 종단 간 scenario는 `store.order`에 있으며 실제 카탈로그 조회를 실행합니다. `receipt_counts_every_line`은 같은 SKU가 반복되는 주문의 합계를 확인하고(`RECEIPT_COUNTS_EVERY_LINE`), `first_failing_line_decides`는 오류 우선순위와 감싼 cause를 확인합니다(`FIRST_FAILING_LINE_DECIDES`).
- `COMPOSES_THROUGH_FACADES`는 `unverified`로 남습니다. 같은 결과를 내는 중복 로직과 facade 호출을 구별할 scenario가 없기 때문입니다.
- `python/app.py`는 카탈로그 조회 하나와 두 줄 주문 영수증을 출력하며, 저장소 테스트 `tests/examples.rs`가 그 출력을 확인합니다. 이는 프로그램 회귀 검사이지 Cott 증거가 아닙니다.
