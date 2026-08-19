# system-effects

## Purpose
This example uses Cott v0.1 effect declarations to represent file-path inspection and environment-variable formatting as separate system-effect contracts.

## Key points
- `inspect_file_path` declares `Result[Path, SystemError]` and `effects [file.read]`, and defines the `PathNotFound` and `AccessDenied` error forms. The current Python binding returns the received path unchanged as `Ok`.
- `format_env_variable` requires a non-empty variable name, ensures its result length is not shorter than `fallback`, and declares `effects [clock]`.
- The Python implementation uses the fallback string when the environment variable is empty or absent, and also when its value is shorter than the fallback string. The executable example uses `/etc/hosts` and `APP_NAME`.
