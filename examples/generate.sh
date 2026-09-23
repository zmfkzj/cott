#!/usr/bin/env bash
# Generate each manifest-selected target sequentially; only callable jobs run in parallel.
set -euo pipefail
exec python3 - "${BASH_SOURCE[0]}" "$@" <<'PY'
import argparse
import os
from pathlib import Path
import shlex
import shutil
import signal
import subprocess
import sys
import tempfile
import tomllib


parser = argparse.ArgumentParser(
    prog="examples/generate.sh",
    description=(
        "Emit and generate every example sequentially with -j 3. "
        "Targets come from cott.toml: python, kotlin, dart (Rust is not supported). "
        "Requires Python >=3.11, cott, the selected agent, uv for Python, and "
        "the manifest-selected Kotlin/Dart toolchains. No verify/deploy is run."
    ),
    epilog=(
        "COTT_BIN selects the compiler executable (default: cott on PATH). "
        "New Python environments and uv downloads/cache are removed even on failure. "
        "Existing .venv environments are reused unchanged; prepare them beforehand. "
        "Authored sources, lockfiles, generated output, provenance and transaction "
        "state are preserved. Kotlin/Dart SDKs and global caches are not removed."
    ),
)
def model_argument(value):
    if (
        not value
        or value != value.strip()
        or value.startswith("-")
        or any(ord(char) < 32 or 127 <= ord(char) <= 159 for char in value)
    ):
        raise argparse.ArgumentTypeError("model must be a nonempty selector without control characters or surrounding whitespace")
    return value


script = Path(sys.argv[1]).resolve()
parser.add_argument("--agent", choices=("codex", "claude", "omp"), default="omp")
parser.add_argument("--model", type=model_argument, help="provider model selector; omitted uses the agent default")
parser.add_argument("--dry-run", action="store_true", help="list commands without installing or generating")
args = parser.parse_args(sys.argv[2:])


def run(command, *, cwd, env):
    print(f"[{cwd}] {shlex.join(map(str, command))}", flush=True)
    if not args.dry_run:
        subprocess.run(command, cwd=cwd, env=env, check=True)


def projects():
    result = []
    # Never descend into a project's generated output, packages or consumer app.
    for root, directories, files in os.walk(script.parent, followlinks=False):
        directories[:] = sorted(
            name for name in directories
            if not name.startswith(".")
            and name not in {"generated", "build", "dist", "target", "node_modules", "__pycache__"}
            and not (Path(root) / name).is_symlink()
        )
        if "cott.toml" not in files:
            continue
        directories.clear()
        project = Path(root)
        manifest = project / "cott.toml"
        if manifest.is_symlink():
            raise ValueError(f"refusing symlink manifest: {manifest}")
        with manifest.open("rb") as stream:
            config = tomllib.load(stream)
        targets = config.get("target", {})
        if len(targets) != 1 or next(iter(targets)) not in {"python", "kotlin", "dart"}:
            raise ValueError(f"{manifest}: expected one python/kotlin/dart target; Rust is unsupported")
        target = next(iter(targets))
        source = None
        if target == "python":
            settings = targets[target]
            if (settings.get("interpreter"), settings.get("type_checker")) != (
                ".venv/bin/python", ".venv/bin/basedpyright"
            ):
                raise ValueError(f"{manifest}: expected project-local .venv tool paths")
            relative = Path(settings["source"])
            if relative.is_absolute() or ".." in relative.parts:
                raise ValueError(f"{manifest}: unsafe Python source path")
            source = project / relative
            if any(path.is_symlink() for path in [source, *source.parents] if path != project.parent):
                raise ValueError(f"{manifest}: refusing symlink Python source")
            if not (source / "pyproject.toml").is_file() or not (source / "uv.lock").is_file():
                raise ValueError(f"{manifest}: Python generation requires pyproject.toml and uv.lock")
            if (project / ".venv").is_symlink():
                raise ValueError(f"{manifest}: refusing symlink .venv")
        result.append((project, target, source))
    if not result:
        raise ValueError("no example manifests found")
    return sorted(result)


def generate(entries, scratch):
    env = os.environ.copy()
    # uv may download both packages and Python itself; neither belongs in global caches.
    env["UV_CACHE_DIR"] = str(scratch / "uv-cache")
    env["UV_PYTHON_INSTALL_DIR"] = str(scratch / "uv-python")
    env["UV_PYTHON_BIN_DIR"] = str(scratch / "uv-bin")
    compiler = os.environ.get("COTT_BIN", "cott")
    if os.path.dirname(compiler):
        compiler = str(Path(compiler).resolve())
    if not args.dry_run and shutil.which(compiler) is None:
        raise ValueError(f"compiler not found: {compiler}; set COTT_BIN to a built cott executable")
    for index, (project, target, source) in enumerate(entries, 1):
        print(f"\n[{index}/{len(entries)}] {project.relative_to(script.parent)} ({target})", flush=True)
        environment = project / ".venv"
        owns_environment = False
        try:
            if target == "python":
                if environment.exists():
                    if not environment.is_dir():
                        raise ValueError(f"not a directory: {environment}")
                    print(f"Reusing existing environment without sync: {environment}", flush=True)
                else:
                    # Claim ownership before uv starts, so partial failed installs are cleaned too.
                    if not args.dry_run:
                        environment.mkdir()
                        owns_environment = True
                    python_env = env | {"UV_PROJECT_ENVIRONMENT": str(environment)}
                    run(["uv", "sync", "--locked", "--project", str(source)], cwd=project, env=python_env)
            # generate is a no-op for fully bound Kotlin/Dart projects; emit their facades too.
            run([compiler, "emit", target, "--project", str(project)], cwd=project, env=env)
            generation = [
                compiler, "generate", "--agent", args.agent, "--target", target,
                "-j", "3", "--project", str(project),
            ]
            if args.model is not None:
                generation.extend(["--model", args.model])
            run(generation, cwd=project, env=env)
        finally:
            if owns_environment:
                shutil.rmtree(environment)
                print(f"Removed temporary environment: {environment}", flush=True)


def interrupted(signum, frame):
    # subprocess.run kills/waits for its child before unwinding into cleanup.
    raise KeyboardInterrupt


signal.signal(signal.SIGTERM, interrupted)
try:
    entries = projects()
    if args.dry_run:
        generate(entries, Path("/tmp/cott-examples-dry-run"))
    else:
        with tempfile.TemporaryDirectory(prefix="cott-examples-") as temporary:
            generate(entries, Path(temporary))
    print(f"\n{'Planned' if args.dry_run else 'Generated'} {len(entries)} examples.")
except KeyboardInterrupt:
    print("\nGeneration interrupted; temporary packages cleaned up.", file=sys.stderr)
    sys.exit(130)
except subprocess.CalledProcessError as error:
    print(f"\nCommand failed with status {error.returncode}; stopping.", file=sys.stderr)
    sys.exit(error.returncode if error.returncode > 0 else 128 - error.returncode)
except (OSError, ValueError) as error:
    print(f"error: {error}", file=sys.stderr)
    sys.exit(1)
PY
