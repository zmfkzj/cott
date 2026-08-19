# random-password-generator

## 예제 목적
외부 난수 대신 제공된 정수 draw 목록으로 재현 가능한 암호를 만드는 예제입니다.

## 핵심 포인트
- 길이는 1~128로 제한하고, `required_password_draws`가 생성에 필요한 정확한 draw 수 `2n + floor(n / 2) - 1`을 계산합니다.
- Python 구현은 문자·숫자·특수문자 수를 길이에서 결정한 뒤, 각 draw의 모듈로 문자 집합을 선택하고 Fisher-Yates 셔플을 적용합니다.
- 길이 오류는 draw 길이보다 먼저 `InvalidLength`로, 부족한 draw는 인덱싱 전에 `InsufficientDraws`로 `Result`에 담습니다.
