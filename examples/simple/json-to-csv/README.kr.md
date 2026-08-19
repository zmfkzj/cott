# json-to-csv

## 예제 목적
이름·나이·출생연도 레코드를 안전한 CSV 텍스트로 직렬화하는 예제입니다.

## 핵심 포인트
- `CsvRecord`의 `name`, `age`, `birthyear` 필드를 고정된 헤더와 같은 순서로 출력합니다.
- 쉼표, 큰따옴표, CR, LF가 있는 필드는 큰따옴표로 감싸고 내부 큰따옴표는 두 번 써 CSV 경계를 보존합니다.
- Python 구현은 빈 입력에도 정확히 `name,age,birthyear\r\n`을 반환하며, 모든 레코드 끝에 CRLF를 붙입니다.
