# order-management

## 예제 목적

`store.catalog`과 `store.order` 모듈을 분리해, 카탈로그 조회 결과를 주문 계산으로 연결하는 다중 모듈 계약을 보여 줍니다.

## 핵심 포인트

- `store.catalog`은 `Item`, `Catalog`, `CatalogError`와 `find_item`을 제공하며, 비어 있지 않은 SKU를 요구하고 성공 시 요청한 SKU의 항목을 반환합니다.
- `store.order`는 카탈로그 모듈의 `Catalog`, `CatalogError`, `Item`을 가져와 `OrderLine`, `Order`, `OrderReceipt` 및 `validate_line`, `calculate_order`를 구성합니다.
- `calculate_order`는 각 `OrderLine`을 `validate_line`으로 검증한 뒤 `find_item`으로 가격을 조회하고, 카탈로그의 `ItemNotFound`를 `OrderError.ItemUnavailable`으로 감싸 모듈 경계를 넘는 오류를 표현합니다.
- 주문이 비어 있으면 `OrderError.EmptyOrder`를 반환하고, 정상 영수증은 원 주문의 `order_id`를 유지하며 수량과 센트 단위 합계를 계산합니다.
