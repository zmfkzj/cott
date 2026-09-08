#!/usr/bin/env python3
from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import shutil
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
CHECKER = ROOT / "examples/complex/artifact-pipeline/check_semantics.py"
PLAIN = ROOT / "benchmarks/plain_python.py"
PROJECTS = {
    "checked-add": ROOT / "examples/grammar/checked-add",
    "artifact-pipeline": ROOT / "examples/complex/artifact-pipeline",
    "toolong": ROOT / "examples/real/toolong",
}
BIND = {
    "artifact-pipeline": (
        "curriculum.artifact_pipeline.topologically_order_steps",
        "python/_cott_impl/curriculum/artifact_pipeline/topologically_order_steps.py",
        "topologically_order_steps",
    ),
    "toolong": (
        "real.toolong.filter_entries",
        "python/_cott_impl/real/toolong/filter_entries.py",
        "filter_entries",
    ),
}
TOOL_ENTRYPOINTS = frozenset({"python", "python3", "python3.14", "basedpyright"})
SKIP_DIRS = frozenset({".cott", "__pycache__"})
COMMAND_TIMEOUT = 900
HUMAN_UNAVAILABLE = (
    "No operator or reviewer was present. This process applied a predetermined "
    "patch. Do not invent authoring or review time."
)
HUMAN_PROTOCOL = (
    "Stopwatch from the first keystroke of the reverse-lexical requirement "
    "through saving authored files, excluding clone, copy, install, and waiting "
    "on emit/verify. Record a second stopwatch for a human reviewer. Repeat the "
    "same requirement on both the Cott project and ordinary typed Python."
)

MUTANTS = (
    {
        "id": "checked_add_return0",
        "category": "constant_return",
        "project": "checked-add",
        "path": "python/cott_bindings/curriculum/checked_add/checked_add.py",
        "old": "    return left + right",
        "new": "    return 0",
    },
    {
        "id": "topo_reversed_order",
        "category": "reversed_ordering",
        "project": "artifact-pipeline",
        "path": "python/cott_bindings/measurement.py",
        "old": "    return Ok(value=CottList(values=ordered_steps))",
        "new": "    return Ok(value=CottList(values=list(reversed(ordered_steps))))",
    },
    {
        "id": "toolong_ignored_filter",
        "category": "ignored_filter",
        "project": "toolong",
        "path": "python/cott_bindings/measurement.py",
        "old": (
            "from cott_runtime import CottList, Option, Some\n"
            "from real.toolong_types import LogEntry\n"
            "\n"
            "\n"
            "def filter_entries(entries: CottList[LogEntry], contains: Option[str]) -> CottList[LogEntry]:\n"
            "    if isinstance(contains, Some):\n"
            "        needle = contains.value.casefold()\n"
            "        return CottList(values=tuple(entry for entry in entries if needle in entry.text.casefold()))\n"
            "    else:\n"
            "        return entries\n"
        ),
        "source": (
            "from cott_runtime import CottList, Option\n"
            "from real.toolong_types import LogEntry\n"
            "\n"
            "\n"
            "def filter_entries(entries: CottList[LogEntry], contains: Option[str]) -> CottList[LogEntry]:\n"
            "    return entries\n"
        ),
    },
    {
        "id": "topo_unconditional_cycle",
        "category": "unconditional_error",
        "project": "artifact-pipeline",
        "path": "python/cott_bindings/measurement.py",
        "old": (
            "from heapq import heapify, heappop, heappush\n"
            "\n"
            "from cott_runtime import CottList, Err, Ok, Result\n"
            "from curriculum.artifact_pipeline_types import ArtifactPipelineError, ArtifactPipelineError_BlankStepName, ArtifactPipelineError_Cycle, ArtifactPipelineError_DuplicateStep, ArtifactPipelineError_SelfDependency, ArtifactPipelineError_UnknownDependency, BuildStep\n"
            "\n"
            "\n"
            "def topologically_order_steps(steps: CottList[BuildStep]) -> Result[CottList[str], ArtifactPipelineError]:\n"
            "    for step in steps:\n"
            "        if step.name.strip() == \"\":\n"
            "            return Err(error=ArtifactPipelineError_BlankStepName())\n"
            "\n"
            "    names: set[str] = set()\n"
            "    for step in steps:\n"
            "        if step.name in names:\n"
            "            return Err(error=ArtifactPipelineError_DuplicateStep())\n"
            "        names.add(step.name)\n"
            "\n"
            "    for step in steps:\n"
            "        for dependency in step.needs:\n"
            "            if dependency not in names:\n"
            "                return Err(error=ArtifactPipelineError_UnknownDependency())\n"
            "\n"
            "    for step in steps:\n"
            "        if step.name in step.needs:\n"
            "            return Err(error=ArtifactPipelineError_SelfDependency())\n"
            "\n"
            "    indegree: dict[str, int] = {}\n"
            "    dependents: dict[str, list[str]] = {}\n"
            "    for step in steps:\n"
            "        indegree[step.name] = len(step.needs)\n"
            "        dependents[step.name] = []\n"
            "    for step in steps:\n"
            "        for dependency in step.needs:\n"
            "            dependents[dependency].append(step.name)\n"
            "\n"
            "    ready: list[str] = [name for name in names if indegree[name] == 0]\n"
            "    heapify(ready)\n"
            "    ordered_steps: list[str] = []\n"
            "    while ready:\n"
            "        name = heappop(ready)\n"
            "        ordered_steps.append(name)\n"
            "        for dependent in dependents[name]:\n"
            "            indegree[dependent] -= 1\n"
            "            if indegree[dependent] == 0:\n"
            "                heappush(ready, dependent)\n"
            "\n"
            "    if len(ordered_steps) != len(steps):\n"
            "        return Err(error=ArtifactPipelineError_Cycle())\n"
            "    return Ok(value=CottList(values=ordered_steps))\n"
        ),
        "source": (
            "from cott_runtime import CottList, Err, Result\n"
            "from curriculum.artifact_pipeline_types import ArtifactPipelineError, "
            "ArtifactPipelineError_Cycle, BuildStep\n"
            "\n"
            "\n"
            "def topologically_order_steps(steps: CottList[BuildStep]) -> Result[CottList[str], ArtifactPipelineError]:\n"
            "    return Err(error=ArtifactPipelineError_Cycle())\n"
        ),
    },
)

REVERSE_TOPO = (
    "    ready: list[str] = [name for name in names if indegree[name] == 0]\n"
    "    heapify(ready)\n"
    "    ordered_steps: list[str] = []\n"
    "    while ready:\n"
    "        name = heappop(ready)\n"
    "        ordered_steps.append(name)\n"
    "        for dependent in dependents[name]:\n"
    "            indegree[dependent] -= 1\n"
    "            if indegree[dependent] == 0:\n"
    "                heappush(ready, dependent)\n"
)
REVERSE_TOPO_NEW = (
    "    ready: list[str] = [name for name in names if indegree[name] == 0]\n"
    "    ready.sort()\n"
    "    ordered_steps: list[str] = []\n"
    "    while ready:\n"
    "        name = ready.pop()\n"
    "        ordered_steps.append(name)\n"
    "        for dependent in dependents[name]:\n"
    "            indegree[dependent] -= 1\n"
    "            if indegree[dependent] == 0:\n"
    "                ready.append(dependent)\n"
    "                ready.sort()\n"
)
REVERSE_PLAIN = (
    "    ready = [name for name in names if indegree[name] == 0]\n"
    "    heapq.heapify(ready)\n"
    "    ordered: list[str] = []\n"
    "    while ready:\n"
    "        name = heapq.heappop(ready)\n"
    "        ordered.append(name)\n"
    "        for dependent in dependents[name]:\n"
    "            indegree[dependent] -= 1\n"
    "            if indegree[dependent] == 0:\n"
    "                heapq.heappush(ready, dependent)\n"
)
REVERSE_PLAIN_NEW = (
    "    ready = [name for name in names if indegree[name] == 0]\n"
    "    ready.sort()\n"
    "    ordered: list[str] = []\n"
    "    while ready:\n"
    "        name = ready.pop()\n"
    "        ordered.append(name)\n"
    "        for dependent in dependents[name]:\n"
    "            indegree[dependent] -= 1\n"
    "            if indegree[dependent] == 0:\n"
    "                ready.append(dependent)\n"
    "                ready.sort()\n"
)

ENV = os.environ.copy()
ENV["PYTHONDONTWRITEBYTECODE"] = "1"
ENV["PYTHONHASHSEED"] = "0"

HELPER = r"""
import importlib.util
import json
import sys

def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module

checker = load(sys.argv[1], "check_semantics")
mode, target = sys.argv[2], sys.argv[3]
if mode == "--project":
    evaluate, _ = checker._load_project(target)
else:
    evaluate = load(target, "target_eval").evaluate
count = 0
for case in checker.cases():
    steps = [{"name": step["name"], "needs": list(step["needs"])} for step in case["steps"]]
    actual = evaluate(steps)
    expected = case["expected"]
    if actual != expected:
        raise AssertionError(f"{case['name']}: expected {expected!r}, got {actual!r}")
    count += 1
print(json.dumps({"cases": count}, separators=(",", ":")))
"""

WITNESS_ADD = """
from curriculum.checked_add import checked_add
print(checked_add(2, 3))
"""

WITNESS_FILTER = """
from pathlib import Path
from cott_runtime import CottList, Some
from real.toolong import filter_entries
from real.toolong_types import LogEntry
entries = CottList(values=(
    LogEntry(source=Path("a.log"), line=1, text="keep"),
    LogEntry(source=Path("b.log"), line=2, text="skip"),
))
print(len(filter_entries(entries, Some(value="keep"))))
"""


class Infra(Exception):
    pass


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def hashed(path: Path) -> dict:
    return {"path": str(path), "content_hash": sha256_file(path) if path.is_file() else None}


def source_hashes(project: Path) -> dict:
    out = {}
    for name in (
        "cott.toml",
        "generator.rules",
        "GENERATOR_RULES.txt",
        "python/uv.lock",
        "python/pyproject.toml",
        "python/cott_bindings/measurement.py",
    ):
        path = project / name
        if path.is_file():
            out[name] = hashed(path)
    return out


def as_text(value: object) -> str:
    if value is None:
        return ""
    if isinstance(value, bytes):
        return value.decode("utf-8", "replace")
    return str(value)


def clip(text: str, limit: int = 4000) -> str:
    text = as_text(text).replace("\x00", "")
    if len(text) <= limit:
        return text
    return text[: limit - 3] + "..."


def median(values: list[float]) -> float | None:
    if not values:
        return None
    return statistics.median(values)


def replace_once(path: Path, old: str, new: str) -> dict:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise Infra(f"mutation not unique in {path}: matched {text.count(old)}")
    after = text.replace(old, new, 1)
    path.write_text(after, encoding="utf-8")
    return diff_stats(text, after)


def diff_stats(before: str, after: str) -> dict:
    old_lines = before.splitlines()
    new_lines = after.splitlines()
    removed = added = 0
    removed_bytes = added_bytes = 0
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(a=old_lines, b=new_lines).get_opcodes():
        if tag in {"replace", "delete"}:
            chunk = old_lines[i1:i2]
            removed += len(chunk)
            removed_bytes += sum(len(line.encode()) for line in chunk)
        if tag in {"replace", "insert"}:
            chunk = new_lines[j1:j2]
            added += len(chunk)
            added_bytes += sum(len(line.encode()) for line in chunk)
    return {
        "authored_lines_changed": removed + added,
        "authored_bytes_changed": removed_bytes + added_bytes,
    }


def copy_project(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    with os.scandir(src) as entries:
        for entry in entries:
            if entry.name in SKIP_DIRS or entry.name.endswith(".pyc"):
                continue
            source = Path(entry.path)
            dest = dst / entry.name
            if entry.is_symlink():
                dest.symlink_to(os.readlink(source))
            elif entry.is_dir():
                if entry.name == ".venv":
                    copy_venv(source, dest)
                else:
                    copy_project(source, dest)
            elif entry.is_file():
                shutil.copy2(source, dest)


def copy_venv(src: Path, dst: Path) -> None:
    dst.mkdir(parents=True, exist_ok=True)
    is_bin = src.name == "bin"
    with os.scandir(src) as entries:
        for entry in entries:
            if entry.name in SKIP_DIRS or entry.name.endswith(".pyc"):
                continue
            source = Path(entry.path)
            dest = dst / entry.name
            if entry.is_dir(follow_symlinks=False):
                copy_venv(source, dest)
            elif entry.is_symlink():
                dest.symlink_to(os.readlink(source))
            elif entry.is_file():
                if is_bin and entry.name in TOOL_ENTRYPOINTS:
                    shutil.copy2(source, dest)
                else:
                    try:
                        os.link(source, dest)
                    except OSError:
                        shutil.copy2(source, dest)


def timed_cmd(argv: list[str], timeout: int = COMMAND_TIMEOUT) -> dict:
    started = time.perf_counter()
    try:
        completed = subprocess.run(argv, capture_output=True, env=ENV, timeout=timeout)
    except subprocess.TimeoutExpired as error:
        return {
            "ok": False,
            "returncode": None,
            "seconds": time.perf_counter() - started,
            "stdout": as_text(error.stdout),
            "stderr": as_text(error.stderr) or f"timeout after {timeout}s",
            "argv": argv,
            "infrastructure": True,
        }
    except OSError as error:
        return {
            "ok": False,
            "returncode": None,
            "seconds": time.perf_counter() - started,
            "stdout": "",
            "stderr": as_text(error),
            "argv": argv,
            "infrastructure": True,
        }
    return {
        "ok": completed.returncode == 0,
        "returncode": completed.returncode,
        "seconds": time.perf_counter() - started,
        "stdout": as_text(completed.stdout),
        "stderr": as_text(completed.stderr),
        "argv": argv,
        "infrastructure": False,
    }


def cott_cmd(binary: Path, args: list[str], project: Path) -> dict:
    return timed_cmd([str(binary), *args, "--project", str(project)])


def classify(emit: dict, verify: dict | None) -> str:
    if emit.get("infrastructure"):
        return "infrastructure"
    if not emit["ok"]:
        return kind(emit["stderr"] + "\n" + emit["stdout"])
    if verify is None:
        return kind(emit["stderr"] + "\n" + emit["stdout"])
    if verify.get("infrastructure"):
        return "infrastructure"
    if not verify["ok"]:
        return kind(verify["stderr"] + "\n" + verify["stdout"])
    return "survived"


def kind(text: str) -> str:
    low = as_text(text).lower()
    if any(
        needle in low
        for needle in (
            "neither manifest-bound nor backed by matching agent provenance",
            "stale durable agent implementation",
            "generation record does not describe",
            "invalid generation provenance",
            "unresolved implementations",
            "read generation provenance",
            "[phase=provenance]",
            "[phase=facade-import]",
            "[phase=implementation-load]",
            "[symbol=_cott_load]",
        )
    ):
        return "provenance"
    if "facade boundary audit failed" in low or "unexpected private implementation" in low:
        return "audit"
    if "basedpyright" in low or "runtime signature probe" in low:
        return "type"
    if any(
        needle in low
        for needle in (
            "static contract proof disproved",
            "semantic coverage policy failed",
            "ensures clause",
            "cottcontractviolation",
        )
    ):
        return "semantic_reject"
    if "contract test process" in low:
        if "assertionerror" in low or "ensures" in low or "clause" in low:
            return "semantic_reject"
        return "other"
    return "other"


def parse_json_stdout(stdout: str) -> dict | None:
    for line in reversed(as_text(stdout).splitlines()):
        line = line.strip()
        if line.startswith("{") and line.endswith("}"):
            try:
                value = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(value, dict):
                return value
    return None


def coverage_summary(project: Path) -> dict:
    path = project / "generated" / "generation.json"
    record = json.loads(path.read_text(encoding="utf-8"))
    current = record.get("current") or {}
    coverage = current.get("semantic_coverage") or {}
    policy = coverage.get("policy") or {}
    return {
        "summary": coverage.get("summary"),
        "policy": {"selected": policy.get("selected"), "passed": policy.get("passed")},
        "verified": current.get("verified"),
        "note": "cott generation semantic_coverage; not independent acceptance and not compiler proof",
    }


def measure_tree(root: Path) -> dict:
    files = 0
    bytes_ = 0
    lines = 0
    for path in root.rglob("*"):
        if not path.is_file() or path.is_symlink():
            continue
        if any(part in SKIP_DIRS for part in path.parts) or path.suffix == ".pyc":
            continue
        data = path.read_bytes()
        files += 1
        bytes_ += len(data)
        lines += data.count(b"\n")
    return {"files": files, "bytes": bytes_, "lines": lines}


def file_footprint(path: Path) -> dict:
    data = path.read_bytes()
    return {"files": 1, "bytes": len(data), "lines": data.count(b"\n")}


def footprint(project: Path) -> dict:
    source_roots = [
        project / "src",
        project / "python",
        project / "cott.toml",
        project / "generator.rules",
        project / "GENERATOR_RULES.txt",
    ]
    source = {"files": 0, "bytes": 0, "lines": 0}
    for item in source_roots:
        if item.is_file():
            data = item.read_bytes()
            source["files"] += 1
            source["bytes"] += len(data)
            source["lines"] += data.count(b"\n")
        elif item.is_dir():
            part = measure_tree(item)
            for key in source:
                source[key] += part[key]
    managed = (
        measure_tree(project / "generated")
        if (project / "generated").is_dir()
        else {"files": 0, "bytes": 0, "lines": 0}
    )
    return {"source": source, "managed": managed}


def tool_identity(project: Path, cott: Path) -> dict:
    python = project / ".venv/bin/python"
    checker = project / ".venv/bin/basedpyright"
    identity = {
        "cott": {
            "executable": str(cott),
            "content_hash": sha256_file(cott) if cott.is_file() else None,
            "version": None,
        },
        "python": {"executable": str(python.resolve()), "content_hash": None, "probe": None},
        "basedpyright": {"executable": str(checker), "content_hash": None, "version": None},
    }
    version = timed_cmd([str(cott), "--version"], timeout=30)
    identity["cott"]["version"] = (version["stdout"] or version["stderr"]).strip() or None
    if python.exists():
        identity["python"]["content_hash"] = sha256_file(python)
        probe = timed_cmd(
            [
                str(python),
                "-c",
                "import json,platform,sys,sysconfig; print(json.dumps({'implementation':sys.implementation.name,'version':platform.python_version(),'cache_tag':sys.implementation.cache_tag,'os':sys.platform,'machine':platform.machine(),'platform':sysconfig.get_platform()},sort_keys=True,separators=(',',':')))",
            ],
            timeout=30,
        )
        identity["python"]["probe"] = parse_json_stdout(probe["stdout"])
    if checker.exists():
        identity["basedpyright"]["content_hash"] = sha256_file(checker)
        probe = timed_cmd([str(checker), "--version"], timeout=30)
        identity["basedpyright"]["version"] = (probe["stdout"] or probe["stderr"]).strip() or None
    return identity


def select_binding(project: Path, name: str) -> None:
    spec = BIND.get(name)
    if spec is None:
        return
    cott_symbol, durable, function = spec
    src = project / durable
    dest = project / "python/cott_bindings/measurement.py"
    if not src.is_file():
        raise Infra(f"missing durable source {src}")
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)
    src.unlink()
    manifest = project / "cott.toml"
    text = manifest.read_text(encoding="utf-8").rstrip() + "\n"
    mapping = (
        f'\n[target.python.implementations]\n"{cott_symbol}" = '
        f'"cott_bindings.measurement:{function}"\n'
    )
    if f'cott_bindings.measurement:{function}' not in text:
        text += mapping
    manifest.write_text(text, encoding="utf-8")


def run_eval(interpreter: Path, helper: Path, checker: Path, mode: str, target: Path) -> dict:
    result = timed_cmd([str(interpreter), str(helper), str(checker), mode, str(target)])
    text = result["stderr"] + "\n" + result["stdout"]
    payload = parse_json_stdout(result["stdout"]) if result["ok"] else None
    return {**result, "payload": payload, "assertion": "AssertionError" in text}


def facade_eval(interpreter: Path, generated: Path, body: str) -> dict:
    script = f"import sys\nsys.path.insert(0, {str(generated.resolve())!r})\n{body.lstrip()}"
    return timed_cmd([str(interpreter), "-c", script])


def summarize_cmd(result: dict) -> dict:
    summary = {
        "ok": result["ok"],
        "returncode": result["returncode"],
        "seconds": result["seconds"],
        "infrastructure": bool(result.get("infrastructure")),
        "stdout": clip(result.get("stdout", "")),
        "stderr": clip(result.get("stderr", "")),
    }
    if "payload" in result:
        summary["payload"] = result["payload"]
    if "assertion" in result:
        summary["assertion"] = result["assertion"]
    return summary


def repeat_cmd(times: int, fn) -> dict:
    raw = [fn() for _ in range(times)]
    seconds = [item["seconds"] for item in raw]
    oks = [item["ok"] for item in raw]
    return {
        "ok": all(oks),
        "median_seconds": median(seconds),
        "raw_seconds": seconds,
        "runs": [summarize_cmd(item) for item in raw],
    }


def paired_emit_verify(times: int, cott: Path, project: Path) -> tuple[dict, dict]:
    emits = []
    verifies = []
    for _ in range(times):
        emit = cott_cmd(cott, ["emit", "python"], project)
        emits.append(emit)
        if not emit["ok"]:
            break
        verify = cott_cmd(cott, ["verify"], project)
        verifies.append(verify)
        if not verify["ok"]:
            break

    def pack(raw: list[dict], expected: int, require_complete: bool) -> dict:
        seconds = [item["seconds"] for item in raw]
        command_ok = bool(raw) and all(item["ok"] for item in raw)
        return {
            "ok": command_ok and (not require_complete or len(raw) == expected),
            "complete": len(raw) == expected,
            "median_seconds": median(seconds) if seconds else None,
            "raw_seconds": seconds,
            "runs": [summarize_cmd(item) for item in raw],
        }

    emit_pack = pack(emits, times, False)
    verify_pack = pack(verifies, times, True)
    verify_pack["timing"] = "post-emit"
    verify_pack["note"] = (
        "each verify immediately follows its paired emit; not repeated verify without emit"
    )
    return emit_pack, verify_pack


def require(path: Path, label: str) -> Path:
    if not path.exists():
        raise Infra(f"missing {label}: {path}")
    return path


def apply_mutant(path: Path, mutant: dict) -> dict:
    if "source" in mutant:
        before = path.read_text(encoding="utf-8")
        if before != mutant["old"]:
            raise Infra(f"mutation baseline mismatch in {path}")
        path.write_text(mutant["source"], encoding="utf-8")
        return diff_stats(before, mutant["source"])
    return replace_once(path, mutant["old"], mutant["new"])


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cott", required=True)
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    if args.repeat < 1:
        print("error: --repeat must be >= 1", file=sys.stderr)
        return 2
    raw_cott = Path(args.cott).expanduser()
    if raw_cott.is_file():
        cott = raw_cott.resolve()
    else:
        found = shutil.which(args.cott)
        cott = Path(found).resolve() if found else raw_cott
    output = Path(args.output)
    if not output.is_absolute():
        output = Path.cwd() / output

    exit_code = 0
    limits = [
        "Human authoring and review seconds were not observed and are null.",
        "Independent acceptance interprets existing doc semantics; it is not cott verify, semantic_coverage, or compiler proof.",
        "verify-only and verify+acceptance are not equivalent guarantees or costs.",
        "Mutations edit authored implementations on temporary copies, never generated/ bytes.",
        "Agent generate is not invoked. Pinned project .venv tools are used as-is.",
        "Do not claim total productivity from machine timings.",
        "Repeated verify without emit is not mutant measurement. toolong lockfile dependencies make a second verify fail; controls and maintenance use paired emit then verify.",
    ]
    try:
        require(cott, "cott binary")
        require(CHECKER, "shared cases")
        require(PLAIN, "plain Python baseline")
        for name, path in PROJECTS.items():
            require(path / "cott.toml", f"{name} project")
            require(path / ".venv/bin/python", f"{name} interpreter")
            require(path / ".venv/bin/basedpyright", f"{name} type checker")
    except Infra as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    original_footprint = {name: footprint(path) for name, path in PROJECTS.items()}
    results = {
        "sample_size": args.repeat,
        "environment": {name: tool_identity(path, cott) for name, path in PROJECTS.items()},
        "identity": {
            "scripts": {
                "contract_value": hashed(Path(__file__).resolve()),
                "check_semantics": hashed(CHECKER),
                "plain_python": hashed(PLAIN),
                "helper": {
                    "content_hash": "sha256:"
                    + hashlib.sha256(HELPER.lstrip("\n").encode()).hexdigest()
                },
            },
            "sources": {
                "original": {name: source_hashes(path) for name, path in PROJECTS.items()},
            },
        },
        "binding_selection": {
            name: {
                "cott_symbol": cott_symbol,
                "durable_source": durable,
                "function": function,
                "transient_module": "cott_bindings.measurement",
                "transient_path": "python/cott_bindings/measurement.py",
                "manifest_table": "target.python.implementations",
                "scope": "temporary copies only",
                "note": (
                    "durable source is copied to cott_bindings.measurement and unlinked; "
                    "cott.toml mapping is appended when that target is absent"
                ),
            }
            for name, (cott_symbol, durable, function) in BIND.items()
        },
        "footprint": {name: {"original": fp} for name, fp in original_footprint.items()},
        "controls": {},
        "mutants": {},
        "identical_task": {},
        "maintenance": {},
        "repeat_verify_without_emit": {},
        "rejection_counts": {},
        "limits": limits,
        "unavailable": {
            "human_authoring_seconds": HUMAN_UNAVAILABLE,
            "human_review_seconds": HUMAN_UNAVAILABLE,
            "protocol": HUMAN_PROTOCOL,
        },
    }

    with tempfile.TemporaryDirectory(prefix="cott-contract-value-") as tmp:
        tmp_path = Path(tmp)
        helpers = tmp_path / "helpers"
        helpers.mkdir()
        helper = helpers / "check.py"
        helper.write_text(HELPER.lstrip("\n"), encoding="utf-8")
        copies = {}
        try:
            for name, path in PROJECTS.items():
                dest = tmp_path / "controls" / name
                copy_project(path, dest)
                select_binding(dest, name)
                copies[name] = dest

            results["identity"]["sources"]["evaluation_binding"] = {
                name: source_hashes(dest) for name, dest in copies.items()
            }

            for name, dest in copies.items():
                emit_runs, verify_runs = paired_emit_verify(args.repeat, cott, dest)
                if not emit_runs["ok"]:
                    raise Infra(f"{name} control emit failed: {emit_runs['runs'][-1]['stderr']}")
                if not verify_runs["ok"]:
                    raise Infra(f"{name} control verify failed: {verify_runs['runs'][-1]['stderr']}")
                results["controls"][name] = {
                    "emit": emit_runs,
                    "verify": verify_runs,
                    "semantic_coverage": coverage_summary(dest),
                }
                results["footprint"][name] = {
                    "original": original_footprint[name],
                    "evaluation_binding": footprint(dest),
                }

            toolong = copies["toolong"]
            probe_reverify = cott_cmd(cott, ["verify"], toolong)
            known_defect = not probe_reverify["ok"] and (
                "generation record does not describe"
                in (probe_reverify["stderr"] + "\n" + probe_reverify["stdout"])
            )
            results["repeat_verify_without_emit"] = {
                "project": "toolong",
                "note": (
                    "Existing compiler behavior, not a mutant kill: toolong selects "
                    "lockfile=python/uv.lock so emit records lock inventory in "
                    "generation.json dependencies; verify then writes dependencies=[] "
                    "because no imported external deps. comparable_snapshot includes "
                    "dependencies, so a second verify without emit fails. Measurement "
                    "uses independent emit then verify cycles instead of repeat-verify."
                ),
                "emit": results["controls"]["toolong"]["emit"]["runs"][-1],
                "verify": results["controls"]["toolong"]["verify"]["runs"][-1],
                "reverify": summarize_cmd(probe_reverify),
                "known_compiler_defect": known_defect,
            }

            pipeline = copies["artifact-pipeline"]
            interpreter = pipeline / ".venv/bin/python"
            plain_copy = helpers / "plain_python.py"
            shutil.copy2(PLAIN, plain_copy)

            plain_runs = []
            cott_runs = []
            for _ in range(args.repeat):
                plain_run = run_eval(interpreter, helper, CHECKER, "--plain", plain_copy)
                cott_run = run_eval(interpreter, helper, CHECKER, "--project", pipeline)
                if not plain_run["ok"]:
                    raise Infra(f"plain Python check failed: {plain_run['stderr']}")
                if not cott_run["ok"]:
                    raise Infra(f"Cott facade check failed: {cott_run['stderr']}")
                plain_runs.append(plain_run)
                cott_runs.append(cott_run)
            plain_times = [run["seconds"] for run in plain_runs]
            cott_times = [run["seconds"] for run in cott_runs]
            verify_medians = results["controls"]["artifact-pipeline"]["verify"]["raw_seconds"]
            results["identical_task"] = {
                "interpreter": str(interpreter.resolve()),
                "plain_python": {
                    "median_seconds": median(plain_times),
                    "raw_seconds": plain_times,
                    "cases": ((plain_runs[-1].get("payload") or {}).get("cases")),
                },
                "cott_facades": {
                    "median_seconds": median(cott_times),
                    "raw_seconds": cott_times,
                    "cases": ((cott_runs[-1].get("payload") or {}).get("cases")),
                    "note": "same shared cases and same interpreter as plain_python; public facade only",
                },
                "verify_only": {
                    "median_seconds": median(verify_medians),
                    "raw_seconds": verify_medians,
                },
                "verify_plus_acceptance": {
                    "median_seconds": median(
                        [v + a for v, a in zip(verify_medians, cott_times, strict=True)]
                    ),
                    "raw_seconds": [
                        v + a for v, a in zip(verify_medians, cott_times, strict=True)
                    ],
                    "note": "sum of cott verify and independent acceptance; not an equivalent guarantee",
                },
                "acceptance": {
                    "median_seconds": median(cott_times),
                    "raw_seconds": cott_times,
                    "payload": cott_runs[-1].get("payload"),
                    "note": "independent doc-semantic corpus; not semantic_coverage",
                },
            }

            counts = {
                "valid_mutants": 0,
                "semantic_reject": 0,
                "type": 0,
                "audit": 0,
                "provenance": 0,
                "survived": 0,
                "other": 0,
                "infrastructure": 0,
                "unmeasured": 0,
            }
            for mutant in MUTANTS:
                work = tmp_path / "mutants" / mutant["id"]
                copy_project(PROJECTS[mutant["project"]], work)
                select_binding(work, mutant["project"])
                apply_mutant(work / mutant["path"], mutant)
                emit = cott_cmd(cott, ["emit", "python"], work)
                verify = cott_cmd(cott, ["verify"], work) if emit["ok"] else None
                classification = classify(emit, verify)
                certified = emit["ok"] and verify is not None and verify["ok"]
                unmeasured = (not certified) and classification != "semantic_reject"
                if unmeasured:
                    exit_code = 1
                    counts["unmeasured"] += 1
                    counts[classification] = counts.get(classification, 0) + 1
                elif classification == "semantic_reject":
                    counts["valid_mutants"] += 1
                    counts["semantic_reject"] += 1
                else:
                    counts["valid_mutants"] += 1
                    counts["survived"] += 1

                independent = None
                witness = {
                    "mutation": {
                        k: mutant[k] for k in ("old", "new", "source") if k in mutant
                    },
                    "emit_stderr": clip(emit["stderr"]),
                    "verify_stderr": None if verify is None else clip(verify["stderr"]),
                }
                py = work / ".venv/bin/python"
                generated = work / "generated/python"
                if certified and mutant["id"] == "checked_add_return0":
                    observed = facade_eval(py, generated, WITNESS_ADD)
                    got = observed["stdout"].strip()
                    independent = {
                        "via": "public_facade",
                        "caught": observed["ok"] and got == "0",
                        "ok": observed["ok"],
                        "got": got,
                        "stderr": clip(observed["stderr"]),
                        "stdout": clip(observed["stdout"]),
                        "note": "curriculum.checked_add.checked_add(2, 3) via generated facade",
                    }
                    witness["public_facade"] = {"call": "checked_add(2, 3)", "got": got}
                    if not independent["caught"]:
                        exit_code = 1
                elif certified and mutant["id"] == "toolong_ignored_filter":
                    observed = facade_eval(py, generated, WITNESS_FILTER)
                    got = observed["stdout"].strip()
                    independent = {
                        "via": "public_facade",
                        "caught": observed["ok"] and got == "2",
                        "ok": observed["ok"],
                        "got": got,
                        "stderr": clip(observed["stderr"]),
                        "stdout": clip(observed["stdout"]),
                        "note": "real.toolong.filter_entries(LogEntry, Some(value='keep')) via generated facade",
                    }
                    witness["public_facade"] = {
                        "call": "len(filter_entries([keep, skip], Some(value='keep')))",
                        "got": got,
                    }
                    if not independent["caught"]:
                        exit_code = 1
                elif certified and mutant["project"] == "artifact-pipeline":
                    caught = run_eval(py, helper, CHECKER, "--project", work)
                    assertion = caught["assertion"]
                    independent = {
                        "via": "public_facade_checker",
                        "caught": (not caught["ok"]) and assertion,
                        "ok": caught["ok"],
                        "assertion": assertion,
                        "stderr": clip(caught["stderr"]),
                        "stdout": clip(caught["stdout"]),
                        "payload": caught["payload"],
                        "note": "independent doc-semantic check via generated facades; not compiler proof",
                    }
                    if independent["caught"]:
                        witness["public_facade"] = {
                            "stderr": clip(caught["stderr"]),
                            "stdout": clip(caught["stdout"]),
                        }
                    elif not caught["ok"]:
                        exit_code = 1
                        independent["error"] = "expected case AssertionError, not generic failure"
                    else:
                        exit_code = 1
                        independent["error"] = "certified mutant survived independent suite"

                results["mutants"][mutant["id"]] = {
                    "category": mutant["category"],
                    "project": mutant["project"],
                    "source": mutant["path"],
                    "generated_edited": False,
                    "emit": summarize_cmd(emit),
                    "verify": None if verify is None else summarize_cmd(verify),
                    "classification": classification,
                    "semantic_kill": classification == "semantic_reject",
                    "certified": certified,
                    "unmeasured": unmeasured,
                    "semantic_coverage": coverage_summary(work) if certified else None,
                    "independent_acceptance": independent,
                    "witness": witness,
                }

            results["rejection_counts"] = {
                **counts,
                "semantic_kills": counts["semantic_reject"],
            }
            if counts["unmeasured"] or counts["infrastructure"]:
                exit_code = 1

            cott_work = tmp_path / "maintenance" / "cott"
            py_work = tmp_path / "maintenance" / "plain_python.py"
            copy_project(PROJECTS["artifact-pipeline"], cott_work)
            select_binding(cott_work, "artifact-pipeline")
            shutil.copy2(PLAIN, py_work)
            cott_impl = cott_work / "python/cott_bindings/measurement.py"
            cott_src = cott_work / "src/curriculum/artifact_pipeline.cott"
            authored = {"authored_lines_changed": 0, "authored_bytes_changed": 0}
            for path, old, new in (
                (cott_impl, REVERSE_TOPO, REVERSE_TOPO_NEW),
                (cott_impl, "from heapq import heapify, heappop, heappush\n", ""),
                (
                    cott_src,
                    "Ready steps are ordered lexicographically.",
                    "Ready steps are ordered reverse lexicographically.",
                ),
            ):
                stats = replace_once(path, old, new)
                authored["authored_lines_changed"] += stats["authored_lines_changed"]
                authored["authored_bytes_changed"] += stats["authored_bytes_changed"]
            plain_before = py_work.read_text(encoding="utf-8")
            replace_once(py_work, REVERSE_PLAIN, REVERSE_PLAIN_NEW)
            replace_once(py_work, "import heapq\n", "")
            plain_stats = diff_stats(plain_before, py_work.read_text(encoding="utf-8"))
            reverse_checker = helpers / "check_semantics_reverse.py"
            shutil.copy2(CHECKER, reverse_checker)
            oracle_stats = replace_once(
                reverse_checker,
                "            if best is None or candidate < best:\n",
                "            if best is None or candidate > best:\n",
            )
            emit_runs, verify_runs = paired_emit_verify(args.repeat, cott, cott_work)
            cott_ready = emit_runs["ok"] and verify_runs["ok"]
            if not cott_ready:
                exit_code = 1
            cott_reverse = (
                repeat_cmd(
                    args.repeat,
                    lambda: run_eval(
                        interpreter, helper, reverse_checker, "--project", cott_work
                    ),
                )
                if cott_ready
                else None
            )
            if cott_reverse is None or not cott_reverse["ok"]:
                exit_code = 1
            py_check = repeat_cmd(
                args.repeat,
                lambda: run_eval(interpreter, helper, reverse_checker, "--plain", py_work),
            )
            if not py_check["ok"]:
                exit_code = 1
            pyright = pipeline / ".venv/bin/basedpyright"
            pyright_runs = repeat_cmd(
                args.repeat,
                lambda: timed_cmd([str(pyright), "--level", "error", str(py_work)]),
            )
            if not pyright_runs["ok"]:
                exit_code = 1
            plain_e2e = None
            if pyright_runs["raw_seconds"] and py_check["raw_seconds"]:
                plain_e2e_raw = [
                    p + r
                    for p, r in zip(pyright_runs["raw_seconds"], py_check["raw_seconds"], strict=True)
                ]
                plain_e2e = {
                    "median_seconds": median(plain_e2e_raw),
                    "raw_seconds": plain_e2e_raw,
                    "note": "derived component sum of basedpyright --level error and independent reverse-lex check; not a sequential workflow measurement; not cott verify",
                }
            cott_e2e = None
            if cott_ready and cott_reverse is not None:
                cott_e2e_raw = [
                    e + v + r
                    for e, v, r in zip(
                        emit_runs["raw_seconds"],
                        verify_runs["raw_seconds"],
                        cott_reverse["raw_seconds"],
                        strict=True,
                    )
                ]
                cott_e2e = {
                    "median_seconds": median(cott_e2e_raw),
                    "raw_seconds": cott_e2e_raw,
                    "note": "derived component sum of emit, post-emit verify, and independent reverse-lex check; not a sequential workflow measurement; not equivalent to basedpyright --level error",
                }
            results["maintenance"] = {
                "requirement": "reverse_lexical_tie_break",
                "shared_expected_oracle": {
                    **oracle_stats,
                    "note": "actual check_semantics.py temp copy; candidate < best -> candidate > best; large-chain explicit expected unchanged; not billed to Cott or plain Python",
                },
                "cott": {
                    **authored,
                    "emit": emit_runs,
                    "verify": verify_runs,
                    "classification": classify(
                        emit_runs["runs"][-1] if emit_runs["runs"] else {"ok": False, "infrastructure": True, "stderr": "", "stdout": ""},
                        verify_runs["runs"][-1] if verify_runs["runs"] else None,
                    ),
                    "reverse_check": cott_reverse,
                    "end_to_end": cott_e2e,
                    "footprint": footprint(cott_work),
                    "copy_seconds_excluded": True,
                    "human_authoring_seconds": None,
                    "human_review_seconds": None,
                },
                "plain_python": {
                    **plain_stats,
                    "basedpyright": pyright_runs,
                    "reverse_check": py_check,
                    "end_to_end": plain_e2e,
                    "footprint": {"source": file_footprint(py_work), "managed": {"files": 0, "bytes": 0, "lines": 0}},
                    "copy_seconds_excluded": True,
                    "human_authoring_seconds": None,
                    "human_review_seconds": None,
                },
                "human_authoring_seconds": None,
                "human_review_seconds": None,
                "unavailable": results["unavailable"],
            }
        except Infra as error:
            results["infrastructure_error"] = str(error)
            exit_code = 1
            print(f"error: {error}", file=sys.stderr)

        output.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(results, indent=2, sort_keys=True) + "\n"
        tmp_out = output.with_name(output.name + ".tmp")
        tmp_out.write_text(payload, encoding="utf-8")
        tmp_out.replace(output)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
