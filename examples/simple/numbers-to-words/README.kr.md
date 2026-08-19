# numbers-to-words

## 예제 목적
I64 정수를 규칙적인 영어 기수 표기로 바꾸는 예제입니다.

## 핵심 포인트
- `spell_under_thousand`은 0~999만 처리하며 백의 나머지가 있을 때 `and`를 넣는 작은 단위 변환을 분리합니다.
- `spell_cardinal`은 천 단위 그룹을 내림차순으로 순회해 `thousand`부터 `quintillion`까지 필요한 규모만 붙입니다.
- Python 구현은 음수 I64 최솟값도 안전하게 절댓값으로 다루며, 0은 `Zero`, 음수는 `(negative) ` 접두사로 표현합니다.
