# alphabetical-file-groups

## 예제 목적
파일명의 첫 Unicode 문자에 따라 이동할 폴더를 결정하는 예제입니다.

## 핵심 포인트
- `FileMove`는 원본 파일명을 그대로 유지하면서 계산된 폴더 이름을 함께 반환합니다.
- 빈 파일명은 `EmptyFilename` 오류가 되고, 선두 문자가 글자가 아니면 `misc` 폴더를 선택합니다.
- Python 구현은 선두 글자의 전체 Unicode casefold 결과를 폴더로 쓰고, 여러 파일에서는 입력 순서대로 처리하다 첫 빈 이름 오류를 전파합니다.
