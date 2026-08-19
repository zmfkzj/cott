# website-connectivity

## 예제 목적
호출자가 제공한 HTTP 관측값을 검증해 웹사이트의 연결 상태로 분류하는 예제입니다.

## 핵심 포인트
- `WebsiteObservation`과 `WebsiteClassification` 구조체가 URL과 상태 코드를 입력·출력 계약으로 고정합니다.
- 빈 URL은 상태 코드보다 먼저 `EmptyUrl` 오류가 되며, 100~599 밖의 코드는 `InvalidStatusCode`로 반환됩니다.
- Python 구현은 200만 `Working`으로, 나머지 유효 HTTP 상태는 `NotWorking`으로 분류하고 목록 처리에서는 첫 오류와 입력 순서를 보존합니다.
