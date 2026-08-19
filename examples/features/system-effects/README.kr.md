# system-effects

## 예제 목적
Cott v0.1의 효과 선언으로 파일 경로 검사와 환경 변수 형식을 서로 다른 시스템 효과 계약으로 나타내는 예제입니다.

## 핵심 포인트
- `inspect_file_path`는 `Result[Path, SystemError]`와 `effects [file.read]`를 선언하고 `PathNotFound` 및 `AccessDenied` 오류 형식을 정의합니다. 현재 Python 바인딩은 받은 경로를 `Ok`로 그대로 반환합니다.
- `format_env_variable`은 비어 있지 않은 변수명을 요구하고 결과 길이가 `fallback`보다 짧지 않음을 보장하며, `effects [clock]`를 선언합니다.
- Python 구현은 환경 변수가 비어 있거나 없으면 대체 문자열을 쓰고, 값이 대체 문자열보다 짧아도 대체 문자열을 씁니다. 실행 예제는 `/etc/hosts`와 `APP_NAME`을 사용합니다.
