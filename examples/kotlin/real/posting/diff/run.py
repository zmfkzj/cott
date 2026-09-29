#!/usr/bin/env python3
"""Differential harness: Python facade vs Kotlin facade of ``real.posting.client``.

Starts the loopback fixture servers (server.py), runs driver.py under the verified Python reference project and
Driver.kt (compiled against cott-module.jar) on identical inputs from the case table (cases.py), normalizes both
result streams, and prints one row per case:

  PASS  both sides return the same normalized result AND both meet the case's contract expectation
  DIFF  the two results differ (both values, the differing paths and which side meets the contract are shown)
  FAIL  the two results agree but violate the expectation, or the implementations raised

    python3 run.py                    # everything; exit 0 iff every case passes
    python3 run.py --python-only      # reference half only; checks the same expectations
    python3 run.py --kotlin-only      # Kotlin half only; checks the same expectations
    python3 run.py --fast --only redirect
    python3 run.py --list

Cases tagged ``port80`` need 127.0.0.1:80.  That port cannot be bound by an unprivileged process, so after the main
pass a second pass re-executes this script inside a private user+network namespace (``unshare --user
--map-root-user --net``), where the port is bindable, for exactly the skipped cases; ``--no-namespace`` disables it.

Exit status: 0 all cases pass; 1 a DIFF, FAIL, driver error or fixture violation; 2 the harness itself could not
run; 3 the Kotlin half is pending (no module JAR) and the Python half is clean.
"""

from __future__ import annotations

import argparse
import copy
import fcntl
import hashlib
import json
import os
import re
import shlex
import shutil
import socket
import struct
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

sys.dont_write_bytecode = True  # keep the tree free of __pycache__

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

from cases import build_cases  # noqa: E402
from oracle import Placeholders  # noqa: E402
from server import Fixtures  # noqa: E402

KOTLIN_PROJECT = HERE.parent
PYTHON_PROJECT = KOTLIN_PROJECT.parents[2] / "real" / "posting"
BUILD = HERE / "build"
KNOWN_FNS = {"parse_method", "parse_arguments", "send_request", "render_response", "execute"}
CAPABILITY_TAGS = {"ipv6", "port80"}  # a case with one of these needs a listener that may be unavailable
KNOWN_TAGS = {"slow", "edge"} | CAPABILITY_TAGS
TOOL_DIRS = [Path.home() / ".local/opt/kotlinc/bin", Path.home() / ".local/opt/jdk17/bin"]
STANDARD_METHODS = {"Get", "Head", "Post", "Put", "Patch", "Delete", "Options"}

USE_COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ


def paint(text: str, code: str) -> str:
    return f"\x1b[{code}m{text}\x1b[0m" if USE_COLOR else text


def log(message: str) -> None:
    print(message, file=sys.stderr, flush=True)


class HarnessError(Exception):
    """The harness could not run (exit status 2)."""


# ---- cases ----------------------------------------------------------------------------------------------------


def _valid_method(method) -> bool:
    if isinstance(method, str):
        return method in STANDARD_METHODS
    if not isinstance(method, dict):
        return False
    variant = method.get("variant")
    return variant in STANDARD_METHODS or (variant == "Custom" and isinstance(method.get("name"), str))


def _check_headers(ident: str, headers) -> None:
    ok = isinstance(headers, list) and all(
        isinstance(pair, list) and len(pair) == 2 and all(isinstance(part, str) for part in pair) for pair in headers
    )
    if not ok:
        raise HarnessError(f"{ident}: headers must be a list of [name, value] string pairs")


def validate_case(case: dict) -> None:
    """Reject malformed case data up front so a typo can never look like a facade result."""
    ident, fn = case["id"], case["fn"]

    def need(container: dict, key: str, kind: type, what: str) -> None:
        value = container.get(key)
        if not isinstance(value, kind) or isinstance(value, bool):
            raise HarnessError(f"{ident}: {what} must be {kind.__name__}")

    if fn == "parse_method":
        need(case, "source", str, "source")
    elif fn in ("parse_arguments", "execute"):
        need(case, "arguments", list, "arguments")
        if not all(isinstance(argument, str) for argument in case["arguments"]):
            raise HarnessError(f"{ident}: arguments must be strings")
    elif fn == "send_request":
        need(case, "request", dict, "request")
        request = case["request"]
        if not _valid_method(request.get("method")):
            raise HarnessError(f"{ident}: bad request.method {request.get('method')!r}")
        need(request, "url", str, "request.url")
        need(request, "body", str, "request.body")
        need(request, "timeout_ms", int, "request.timeout_ms")
        if not 0 <= request["timeout_ms"] <= 0xFFFFFFFF:
            raise HarnessError(f"{ident}: request.timeout_ms is not a U32")
        _check_headers(ident, request.get("headers"))
    elif fn == "render_response":
        need(case, "response", dict, "response")
        response = case["response"]
        need(response, "status", int, "response.status")
        if not 0 <= response["status"] <= 0xFFFF:
            raise HarnessError(f"{ident}: response.status is not a U16")
        need(response, "url", str, "response.url")
        need(response, "body", str, "response.body")
        _check_headers(ident, response.get("headers"))
    if "expect" in case:
        need(case, "expect", dict, "expect")
    if "ignore" in case and not (isinstance(case["ignore"], list) and all(isinstance(path, str) for path in case["ignore"])):
        raise HarnessError(f"{ident}: ignore must be a list of result paths")


def load_cases(path: Path | None) -> list[dict]:
    if path is None:
        cases = build_cases()
    else:
        try:
            cases = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as error:
            raise HarnessError(f"cannot read {path}: {error}") from error
    if not isinstance(cases, list):
        raise HarnessError("expected a list of cases")
    seen: set[str] = set()
    for case in cases:
        ident = case.get("id") if isinstance(case, dict) else None
        if not isinstance(ident, str) or ident in seen:
            raise HarnessError(f"case id missing or duplicated: {ident!r}")
        seen.add(ident)
        if case.get("fn") not in KNOWN_FNS:
            raise HarnessError(f"{ident}: unknown fn {case.get('fn')!r}")
        unknown = set(case.get("tags", ())) - KNOWN_TAGS
        if unknown:
            raise HarnessError(f"{ident}: unknown tags {sorted(unknown)}")
        validate_case(case)
    return cases


def select_cases(cases: list[dict], args: argparse.Namespace) -> list[dict]:
    chosen = []
    for case in cases:
        ident, tags = case["id"], set(case.get("tags", ()))
        if args.only and not any(re.search(pattern, ident) for pattern in args.only):
            continue
        if args.skip and any(re.search(pattern, ident) for pattern in args.skip):
            continue
        if args.only_tag and not tags & set(args.only_tag):
            continue
        if args.fast and "slow" in tags:
            continue
        if args.no_edge and "edge" in tags:
            continue
        chosen.append(case)
    return chosen


# ---- toolchain ------------------------------------------------------------------------------------------------


def tool_path() -> str:
    return os.pathsep.join([str(path) for path in TOOL_DIRS if path.is_dir()] + [os.environ.get("PATH", "")])


def find_tool(name: str) -> str:
    found = shutil.which(name, path=tool_path())
    if found is None:
        raise HarnessError(f"{name} not found; put kotlinc >= 2.2.10 and JDK >= 17 on PATH")
    return found


def sha256_of(*parts: bytes | Path) -> str:
    digest = hashlib.sha256()
    for part in parts:
        digest.update(part.read_bytes() if isinstance(part, Path) else part)
        digest.update(b"\0")
    return digest.hexdigest()


@dataclass
class KotlinRuntime:
    java: str
    classpath: list[Path]
    main_class: str = "posting_diff.DriverKt"


def build_kotlin_driver(module_jar: Path, coroutines_jar: Path | None, force: bool) -> KotlinRuntime:
    kotlinc = find_tool("kotlinc")
    java = find_tool("java")
    home = Path(kotlinc).resolve().parent.parent
    stdlib = home / "lib" / "kotlin-stdlib.jar"
    if not stdlib.is_file():
        raise HarnessError(f"kotlin-stdlib.jar not found next to kotlinc ({stdlib})")
    if coroutines_jar is None:  # the project's published runtime dependency, else the compiler-bundled one it was verified with
        published = KOTLIN_PROJECT / "generated" / "runtime-libs" / "kotlinx-coroutines-core-jvm.jar"
        coroutines_jar = published if published.is_file() else home / "lib" / "kotlinx-coroutines-core-jvm.jar"
    if not coroutines_jar.is_file():
        raise HarnessError(f"coroutines runtime JAR missing: {coroutines_jar}")
    version_file = home / "build.txt"
    compiler_id = version_file.read_text().strip() if version_file.is_file() else Path(kotlinc).resolve().name
    key = sha256_of(HERE / "Driver.kt", module_jar, coroutines_jar, stdlib, compiler_id.encode())[:16]
    BUILD.mkdir(exist_ok=True)
    driver_jar = BUILD / f"driver-{key}.jar"
    if force or not driver_jar.is_file():
        log(f"[kotlin] compiling Driver.kt against {module_jar.name} (cached as {driver_jar.name}) ...")
        started = time.monotonic()
        partial = BUILD / f"driver-{key}.{os.getpid()}.partial.jar"
        classpath = os.pathsep.join(str(path) for path in (module_jar, coroutines_jar, stdlib))
        command = [
            kotlinc, str(HERE / "Driver.kt"), "-no-stdlib", "-no-reflect", "-classpath", classpath,
            "-jvm-target", "17", "-Xjdk-release=17", "-module-name", "posting_diff_driver", "-d", str(partial),
        ]
        env = {**os.environ, "PATH": tool_path()}
        done = subprocess.run(command, env=env, capture_output=True, text=True, check=False)
        if done.returncode != 0 or not partial.is_file():
            partial.unlink(missing_ok=True)
            raise HarnessError(
                "Driver.kt does not compile against the module JAR (the emitted facade may differ from the "
                f"signatures Driver.kt calls):\n{done.stdout}{done.stderr}"
            )
        partial.replace(driver_jar)
        cached = sorted(BUILD.glob("driver-*.jar"), key=lambda path: path.stat().st_mtime, reverse=True)
        for stale in cached[3:]:
            stale.unlink(missing_ok=True)
        log(f"[kotlin] compiled in {time.monotonic() - started:.1f}s")
    return KotlinRuntime(java=java, classpath=[driver_jar, module_jar, coroutines_jar, stdlib])


# ---- running the drivers --------------------------------------------------------------------------------------


def clean_env() -> dict[str, str]:
    env = {key: value for key, value in os.environ.items() if not key.lower().endswith("_proxy")}
    env["PATH"] = tool_path()
    return env


@dataclass
class Half:
    name: str
    records: dict[str, dict] = field(default_factory=dict)
    stray: list[str] = field(default_factory=list)
    stderr: str = ""
    status: int | None = None
    timed_out: bool = False
    seconds: float = 0.0
    never_connections: int = 0
    never_requests: list[str] = field(default_factory=list)


def run_half(name: str, label: str, command: list[str], env: dict[str, str], timeout: float, fixtures: Fixtures, expected: int) -> Half:
    half = Half(name)
    fixtures.reset_stats()
    log(f"[{label}] running {expected} cases ...")
    started = time.monotonic()
    with tempfile.TemporaryDirectory(prefix="posting-diff-") as scratch:
        try:
            done = subprocess.run(command, env=env, cwd=scratch, capture_output=True, timeout=timeout, check=False)
            stdout, stderr, half.status = done.stdout, done.stderr, done.returncode
        except subprocess.TimeoutExpired as error:
            stdout, stderr, half.timed_out = error.stdout or b"", error.stderr or b"", True
    half.seconds = time.monotonic() - started
    half.stderr = stderr.decode("utf-8", errors="replace")
    (BUILD / f"{label}.jsonl").write_bytes(stdout)
    (BUILD / f"{label}.stderr").write_bytes(stderr)
    for line in stdout.decode("utf-8", errors="replace").splitlines():
        try:
            record = json.loads(line)
            half.records[record["case"]] = record
        except (ValueError, KeyError, TypeError):
            half.stray.append(line)
    half.never_connections = fixtures.never.connections
    half.never_requests = list(fixtures.never.requests)
    log(f"[{label}] {len(half.records)}/{expected} results in {half.seconds:.1f}s")
    return half


def python_command(cases_file: Path, vars_file: Path) -> tuple[list[str], dict[str, str]]:
    interpreter = PYTHON_PROJECT / ".venv" / "bin" / "python"
    facade = PYTHON_PROJECT / "generated" / "python"
    if not interpreter.exists() or not facade.is_dir():
        raise HarnessError(f"Python reference project not usable: {interpreter} / {facade}")
    env = clean_env()
    env.update({"PYTHONPATH": str(facade), "PYTHONDONTWRITEBYTECODE": "1", "PYTHONUNBUFFERED": "1"})
    return [str(interpreter), str(HERE / "driver.py"), "--cases", str(cases_file), "--vars", str(vars_file)], env


def kotlin_command(runtime: KotlinRuntime, cases_file: Path, vars_file: Path) -> tuple[list[str], dict[str, str]]:
    options = shlex.split(os.environ.get("POSTING_DIFF_JAVA_OPTS", ""))
    classpath = os.pathsep.join(str(path) for path in runtime.classpath)
    command = [runtime.java, *options, "-cp", classpath, runtime.main_class, "--cases", str(cases_file), "--vars", str(vars_file)]
    return command, clean_env()


# ---- normalized values: comparison and assertions -------------------------------------------------------------


def outcome(half: Half, case_id: str, placeholders: Placeholders):
    """(``result`` or None, note) for one case on one side, with this run's origins turned back into placeholders."""
    record = half.records.get(case_id)
    if record is None:
        return None, "no result emitted" + (" (driver timed out)" if half.timed_out else "")
    if "result" not in record:
        return None, f"driver error: {record.get('driver_error')}"
    return placeholders.abstract(record["result"]), None


def short(value, width: int = 160) -> str:
    text = json.dumps(value, ensure_ascii=False)
    return text if len(text) <= width else text[: width - 3] + "..."


def strip(result, paths: list[str]):
    """A copy of ``result`` with the given dotted paths blanked (the contract leaves them open)."""
    if not paths:
        return result
    out = copy.deepcopy(result)
    for path in paths:
        segments = path.split(".")
        node = out
        try:
            for segment in segments[:-1]:
                node = node[int(segment)] if isinstance(node, list) else node[segment]
            if isinstance(node, list):
                node[int(segments[-1])] = None
            else:
                node.pop(segments[-1], None)
        except (KeyError, IndexError, TypeError, ValueError):
            pass
    return out


def both_json(left: str, right: str):
    if not (left[:1] in "{[" and right[:1] in "{["):
        return None
    try:
        return json.loads(left), json.loads(right)
    except ValueError:
        return None


def differences(left, right, path: str = "result", out: list[str] | None = None, limit: int = 6) -> list[str]:
    """Paths at which two normalized values differ (strings holding JSON are compared structurally)."""
    out = [] if out is None else out
    if len(out) >= limit:
        return out
    if isinstance(left, dict) and isinstance(right, dict):
        if "tag" in left and "tag" in right and left["tag"] != right["tag"]:
            out.append(f"{path}.tag: python={short(left['tag'])} kotlin={short(right['tag'])}")
            return out
        for key in list(left) + [key for key in right if key not in left]:
            if key not in left:
                out.append(f"{path}.{key}: only kotlin has {short(right[key])}")
            elif key not in right:
                out.append(f"{path}.{key}: only python has {short(left[key])}")
            else:
                differences(left[key], right[key], f"{path}.{key}", out, limit)
    elif isinstance(left, list) and isinstance(right, list):
        if len(left) != len(right):
            out.append(f"{path}: length python={len(left)} kotlin={len(right)}")
        for index, (a, b) in enumerate(zip(left, right, strict=False)):
            differences(a, b, f"{path}[{index}]", out, limit)
    elif isinstance(left, str) and isinstance(right, str) and left != right and (parsed := both_json(left, right)):
        differences(parsed[0], parsed[1], f"{path}.@json", out, limit)
    elif left != right or type(left) is not type(right):
        out.append(f"{path}: python={short(left)} kotlin={short(right)}")
    return out[:limit]


def lookup(result, path: str):
    """Walk ``a.b.0.c``; ``#`` is the length, ``@json`` parses a string as JSON."""
    current = result
    for segment in path.split("."):
        if segment == "#":
            current = len(current)
        elif segment == "@json":
            current = json.loads(current)
        elif isinstance(current, list):
            current = current[int(segment)]
        else:
            current = current[segment]
    return current


LOOKUP_ERRORS = (KeyError, IndexError, ValueError, TypeError)


def check_one(result, path: str, wanted) -> str | None:
    """None when one assertion holds, else what is wrong.  ``{"$absent": true}`` and ``{"$contains": [...]}`` are special."""
    if isinstance(wanted, dict) and wanted.get("$absent") is True:
        parent_path, _, last = path.rpartition(".")
        try:
            parent = lookup(result, parent_path) if parent_path else result
        except LOOKUP_ERRORS as error:
            return f"{path}: cannot look up its parent ({type(error).__name__}: {error})"
        if isinstance(parent, dict) and last not in parent:
            return None
        return f"{path}: expected to be absent, found {short(parent.get(last) if isinstance(parent, dict) else parent)}"
    try:
        actual = lookup(result, path)
    except LOOKUP_ERRORS as error:
        return f"{path}: not found ({type(error).__name__}: {error})"
    if isinstance(wanted, dict) and "$contains" in wanted:
        if not isinstance(actual, str):
            return f"{path}: expected a string, got {short(actual)}"
        missing = [part for part in wanted["$contains"] if part not in actual]
        return f"{path}: {short(missing)} not found in {short(actual, 200)}" if missing else None
    return None if actual == wanted else f"{path}: expected {short(wanted)} got {short(actual)}"


def check_assertions(assertions: dict, result) -> list[str]:
    return [problem for path, wanted in assertions.items() if (problem := check_one(result, path, wanted))]


# ---- judging and reporting ------------------------------------------------------------------------------------


def label(case: dict) -> str:
    tags = case.get("tags", ())
    return case["id"] + ("  [" + ",".join(tags) + "]" if tags else "")


def tail(text: str, lines: int = 15) -> str:
    return "\n".join("    | " + line for line in text.strip().splitlines()[-lines:])


@dataclass
class Tally:
    cases: int = 0
    passes: int = 0
    diffs: int = 0
    fails: int = 0
    edge_diffs: int = 0
    contract_cases: int = 0
    python_meets: int = 0
    kotlin_meets: int = 0
    violations: int = 0
    not_passing: list[list[str]] = field(default_factory=list)  # [status, id]
    seconds: dict[str, float] = field(default_factory=dict)

    def clean(self) -> bool:
        return not (self.diffs or self.fails or self.violations)


def judge(case: dict, py, kt) -> tuple[str, list[str], list[str], list[str]]:
    """(status, python problems, kotlin problems, sides that raised) for one case."""
    expect = case.get("expect", {})
    ignore = case.get("ignore", [])
    py_problems = check_assertions(expect, py) if py is not None else []
    kt_problems = check_assertions(expect, kt) if kt is not None else []
    agree = py is not None and kt is not None and strip(py, ignore) == strip(kt, ignore)
    raised = [side for side, result in (("python", py), ("kotlin", kt)) if result is not None and result.get("tag") == "Raise"]
    if not agree:
        return "DIFF", py_problems, kt_problems, raised
    if py_problems or kt_problems or raised:
        return "FAIL", py_problems, kt_problems, raised
    return "PASS", py_problems, kt_problems, raised


def given_inputs(case: dict) -> dict:
    return {key: case[key] for key in ("source", "arguments", "request", "response") if key in case}


def report_single(cases: list[dict], half: Half, placeholders: Placeholders, verbose: bool) -> Tally:
    """One half only (--python-only / --kotlin-only): the expectations are still checked, there is nothing to compare."""
    side = half.name
    tally = Tally(cases=len(cases), seconds={side: half.seconds})
    for case in cases:
        result, note = outcome(half, case["id"], placeholders)
        expect = case.get("expect", {})
        if expect:
            tally.contract_cases += 1
        if result is None:
            tally.diffs += 1
            tally.not_passing.append(["ERROR", case["id"]])
            print(f"{paint('ERROR ', '1;31')} {label(case)}\n        input:  {short(given_inputs(case), 400)}\n        {side}: {note}")
            continue
        problems = check_assertions(expect, result)
        raised = result.get("tag") == "Raise"
        if not problems and expect:
            if side == "python":
                tally.python_meets += 1
            else:
                tally.kotlin_meets += 1
        if problems or raised:
            tally.fails += 1
            tally.not_passing.append(["EXPECT" if problems else "RAISE", case["id"]])
            print(f"{paint('EXPECT' if problems else 'RAISE ', '1;31')} {label(case)}")
            print(f"        input:  {short(given_inputs(case), 400)}")
            print(f"        {side}: {short(result, 100000 if verbose else 400)}")
            for problem in problems:
                print(f"        expectation: {problem}")
            if case.get("note"):
                print(f"        note: {case['note']}")
        else:
            tally.passes += 1
            print(f"{paint('OK    ', '32')} {label(case)}" + (f"  {short(result, 100000)}" if verbose else ""))
    return tally


def report_pair(cases: list[dict], python: Half, kotlin: Half, placeholders: Placeholders, verbose: bool) -> Tally:
    tally = Tally(cases=len(cases), seconds={"python": python.seconds, "kotlin": kotlin.seconds})
    for case in cases:
        ident = case["id"]
        py, py_note = outcome(python, ident, placeholders)
        kt, kt_note = outcome(kotlin, ident, placeholders)
        status, py_problems, kt_problems, raised = judge(case, py, kt)
        if case.get("expect"):
            tally.contract_cases += 1
            tally.python_meets += py is not None and not py_problems
            tally.kotlin_meets += kt is not None and not kt_problems
        if status == "PASS":
            tally.passes += 1
            timing = f"  {python.records[ident].get('ms', '?')}ms/{kotlin.records[ident].get('ms', '?')}ms" if verbose else ""
            print(f"{paint('PASS', '32')}  {label(case)}{timing}")
            continue
        limit = 100000 if verbose else 400
        tally.not_passing.append([status, ident])
        if status == "DIFF":
            tally.diffs += 1
            tally.edge_diffs += "edge" in case.get("tags", ())
        else:
            tally.fails += 1
        print(f"{paint(status, '1;31')}  {label(case)}")
        print(f"        input:  {short(given_inputs(case), limit)}")
        print(f"        python: {py_note or short(py, limit)}")
        if status == "DIFF":
            print(f"        kotlin: {kt_note or short(kt, limit)}")
            if py is not None and kt is not None:
                ignore = case.get("ignore", [])
                for line in differences(strip(py, ignore), strip(kt, ignore)):
                    print(f"        differs: {line}")
        else:
            print("        kotlin: the same")
        if case.get("expect"):
            for side, problems in (("python", py_problems), ("kotlin", kt_problems)):
                if problems:
                    print(f"        {side} violates the contract: {'; '.join(problems[:3])}")
            if not py_problems and not kt_problems and py is not None and kt is not None:
                print("        both meet the contract expectation")
        elif "edge" in case.get("tags", ()):
            print("        edge case: the contract leaves this open (no expectation)")
        for side in raised:
            print(f"        {side} raised (an implementation fault, never a PASS)")
        if case.get("note"):
            print(f"        note: {case['note']}")
    return tally


def report_fixtures(tally: Tally, *halves: Half) -> None:
    for half in halves:
        if half.never_connections:
            tally.violations += 1
            print(f"{paint('VIOLATION', '1;31')} {half.name} half connected {half.never_connections} time(s) to the never-connect "
                  f"server (an InvalidRequest or boundary violation must not attempt a connection): {half.never_requests or 'no request line'}")


def report_process_problems(*halves: Half) -> None:
    for half in halves:
        if half.timed_out or half.status not in (0, None) or half.stray:
            print(f"\n{half.name} process: status={half.status} timed_out={half.timed_out} stray_stdout_lines={len(half.stray)}")
            if half.stray:
                print(tail("\n".join(half.stray)))
            if half.stderr.strip():
                print(f"  {half.name} stderr (tail):\n{tail(half.stderr)}")


def print_summary(title: str, tally: Tally, pair: bool) -> None:
    times = ", ".join(f"{side} {seconds:.1f}s" for side, seconds in tally.seconds.items())
    if pair:
        print(f"\n{title}: {tally.cases} cases: {tally.passes} PASS, {tally.diffs} DIFF, {tally.fails} FAIL  ({times})")
        print(f"         contract: {tally.contract_cases} cases carry an expectation; python meets {tally.python_meets}, kotlin meets {tally.kotlin_meets}")
        if tally.edge_diffs:
            print(f"         {tally.edge_diffs} DIFF row(s) are edge cases: behavior the contract leaves open")
    else:
        side = next(iter(tally.seconds))
        meets = tally.python_meets if side == "python" else tally.kotlin_meets
        print(f"\n{title}: {tally.cases} cases: {tally.passes} OK, {tally.fails} violate their expectation or raised, "
              f"{tally.diffs} driver errors  ({times}); {side} meets {meets} of {tally.contract_cases} expectations")
    if tally.violations:
        print(f"         {tally.violations} fixture violation(s)")
    if tally.not_passing:
        shown = ", ".join(f"{status} {ident}" for status, ident in tally.not_passing[:40])
        more = len(tally.not_passing) - 40
        print(f"         not passing: {shown}" + (f" ... and {more} more" if more > 0 else ""))


NOT_COVERED = [
    "https -> http downgrade refusal, an https default-port Host, and Location resolution against an https base: need a TLS listener with a certificate both runtimes trust",
    "connection *attempt* timeout: needs an unroutable address; the sandbox answers such connects immediately",
    "RFC 3986 example \"//g\" (resolves to http://g, another host); HTTP/2 and proxies",
]


# ---- one pass -------------------------------------------------------------------------------------------------


def execute_pass(args: argparse.Namespace, cases: list[dict], runtime: KotlinRuntime | None, suffix: str) -> tuple[Tally | None, dict[str, list[str]], dict[str, str]]:
    """Start the fixtures, run the runnable cases on both halves, print the table.  Returns (tally, skipped ids by tag, why)."""
    fixtures = Fixtures()
    try:
        available = fixtures.available_tags()
        skipped: dict[str, list[str]] = {}
        runnable = []
        for case in cases:
            missing = [tag for tag in case.get("tags", ()) if tag in CAPABILITY_TAGS and tag not in available]
            if missing:
                skipped.setdefault(missing[0], []).append(case["id"])
            else:
                runnable.append(case)
        if not runnable:
            return None, skipped, dict(fixtures.unavailable)
        variables = fixtures.variables()
        placeholders = Placeholders(variables)
        with tempfile.TemporaryDirectory(prefix="posting-diff-inputs-") as inputs:
            vars_file = Path(inputs) / "vars.json"
            cases_file = Path(inputs) / "cases.json"
            vars_file.write_text(json.dumps(variables, indent=2) + "\n", encoding="utf-8")
            cases_file.write_text(json.dumps(runnable), encoding="utf-8")
            python = kotlin = None
            if not args.kotlin_only:
                command, env = python_command(cases_file, vars_file)
                python = run_half("python", "python" + suffix, command, env, args.driver_timeout, fixtures, len(runnable))
            if runtime is not None:
                command, env = kotlin_command(runtime, cases_file, vars_file)
                kotlin = run_half("kotlin", "kotlin" + suffix, command, env, args.driver_timeout, fixtures, len(runnable))
    finally:
        fixtures.close()
    print()
    if python is not None and kotlin is not None:
        tally = report_pair(runnable, python, kotlin, placeholders, args.verbose)
        report_fixtures(tally, python, kotlin)
        report_process_problems(python, kotlin)
    else:
        half = python if python is not None else kotlin
        assert half is not None
        tally = report_single(runnable, half, placeholders, args.verbose)
        report_fixtures(tally, half)
        report_process_problems(half)
    return tally, skipped, dict(fixtures.unavailable)


def bring_up_loopback() -> None:
    """Inside a fresh network namespace ``lo`` starts down; bring it up (needs CAP_NET_ADMIN over the namespace)."""
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            request = struct.pack("16sH14x", b"lo", 0)
            flags = struct.unpack("16sH14x", fcntl.ioctl(probe, 0x8913, request))[1]  # SIOCGIFFLAGS
            fcntl.ioctl(probe, 0x8914, struct.pack("16sH14x", b"lo", flags | 0x1))  # SIOCSIFFLAGS, IFF_UP
    except OSError as error:
        raise HarnessError(f"cannot bring up the loopback interface (is this a private network namespace?): {error}") from error


def namespace_available() -> str | None:
    unshare = shutil.which("unshare")
    if unshare is None:
        return None
    probe = subprocess.run([unshare, "--user", "--map-root-user", "--net", "true"], capture_output=True, check=False)
    return unshare if probe.returncode == 0 else None


def run_namespace_pass(unshare: str, tags: list[str], python_only: bool) -> dict | None:
    """Re-run this script in a private user+network namespace for the cases the host could not run."""
    with tempfile.TemporaryDirectory(prefix="posting-diff-ns-") as scratch:
        result_file = Path(scratch) / "result.json"
        forwarded = [argument for argument in sys.argv[1:] if argument != "--rebuild"]
        command = [unshare, "--user", "--map-root-user", "--net", sys.executable, str(Path(__file__).resolve()), *forwarded,
                   "--in-namespace", "--result-json", str(result_file)]
        for tag in tags:
            command += ["--only-tag", tag]
        if python_only and "--python-only" not in sys.argv:
            command.append("--python-only")
        print(f"\n{'=' * 24} second pass: private user+network namespace (127.0.0.1:80 is bindable there) {'=' * 24}", flush=True)
        done = subprocess.run(command, check=False)
        if result_file.is_file():
            return json.loads(result_file.read_text(encoding="utf-8"))
        print(f"the namespace pass produced no result (exit status {done.returncode})", file=sys.stderr)
        return None


# ---- main -----------------------------------------------------------------------------------------------------


def main() -> int:
    sys.stdout.reconfigure(errors="backslashreplace")
    sys.stderr.reconfigure(errors="backslashreplace")
    parser = argparse.ArgumentParser(description="Python vs Kotlin differential harness for real.posting.client")
    parser.add_argument("--python-only", action="store_true", help="run only the reference half; checks the same expectations")
    parser.add_argument("--kotlin-only", action="store_true", help="run only the Kotlin half; checks the same expectations")
    parser.add_argument("--only", action="append", metavar="REGEX", help="run cases whose id matches (repeatable)")
    parser.add_argument("--skip", action="append", metavar="REGEX", help="skip cases whose id matches (repeatable)")
    parser.add_argument("--only-tag", action="append", metavar="TAG", help="run cases carrying this tag (repeatable)")
    parser.add_argument("--fast", action="store_true", help="skip cases tagged slow (64 MiB bodies, drip)")
    parser.add_argument("--no-edge", action="store_true", help="skip cases tagged edge (behavior the contract leaves open)")
    parser.add_argument("--list", action="store_true", help="list the selected case ids and exit")
    parser.add_argument("--dump-cases", type=Path, metavar="FILE", help="write the selected cases as JSON and exit")
    parser.add_argument("-v", "--verbose", action="store_true", help="show timings and untruncated values")
    parser.add_argument("--rebuild", action="store_true", help="force recompiling Driver.kt")
    parser.add_argument("--no-namespace", action="store_true", help="do not run the port80 cases in a private network namespace")
    parser.add_argument("--cases", type=Path, default=None, help="a JSON case list instead of the built-in table (cases.py)")
    parser.add_argument("--module-jar", type=Path, default=KOTLIN_PROJECT / "generated" / "library" / "cott-module.jar")
    parser.add_argument("--coroutines-jar", type=Path, default=None,
                        help="default: generated/runtime-libs/kotlinx-coroutines-core-jvm.jar, else the compiler-bundled JAR")
    parser.add_argument("--driver-timeout", type=float, default=1200.0, metavar="SECONDS", help="wall-clock limit per driver process")
    parser.add_argument("--in-namespace", action="store_true", help=argparse.SUPPRESS)
    parser.add_argument("--result-json", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()

    try:
        cases = select_cases(load_cases(args.cases), args)
        if not cases:
            raise HarnessError("no cases selected")
        if args.dump_cases:
            args.dump_cases.write_text(json.dumps(cases, ensure_ascii=True), encoding="ascii")
            print(f"{len(cases)} cases written to {args.dump_cases}")
            return 0
        if args.list:
            for case in cases:
                print(label(case))
            return 0
        if args.in_namespace:
            bring_up_loopback()
        BUILD.mkdir(exist_ok=True)
        if args.python_only and args.kotlin_only:
            raise HarnessError("--python-only and --kotlin-only exclude each other")
        pending = not args.python_only and not args.module_jar.is_file()
        if pending and args.kotlin_only:
            raise HarnessError(f"--kotlin-only needs the module JAR: {args.module_jar} does not exist")
        runtime = None
        if not args.python_only and not pending:
            runtime = build_kotlin_driver(args.module_jar, args.coroutines_jar, args.rebuild)
        tally, skipped, why = execute_pass(args, cases, runtime, "-ns" if args.in_namespace else "")
    except HarnessError as error:
        print(f"harness error: {error}", file=sys.stderr)
        return 2

    pair = runtime is not None and not args.kotlin_only
    title = "Summary" if pair else ("Kotlin half" if args.kotlin_only else "Python half")
    tallies = [tally] if tally is not None else []
    if tally is not None:
        print_summary(title, tally, pair)
    namespace_result = None
    if skipped and not args.in_namespace:
        count = sum(len(ids) for ids in skipped.values())
        reasons = "; ".join(f"{tag}: {why.get(tag, 'unavailable')}" for tag in skipped)
        print(f"\nskipped {count} case(s) needing a listener this host cannot provide ({reasons})")
        unshare = None if args.no_namespace else namespace_available()
        if unshare:
            namespace_result = run_namespace_pass(unshare, sorted(skipped), pending)
        else:
            print("  a private user+network namespace is unavailable"
                  f"{' (--no-namespace)' if args.no_namespace else ''}: run `unshare --user --map-root-user --net "
                  f"{sys.executable} {Path(__file__).resolve()} --in-namespace --only-tag port80` where it works")
            print("  skipped: " + ", ".join(sorted(ident for ids in skipped.values() for ident in ids))[:600])
    if args.result_json is not None:
        args.result_json.write_text(json.dumps({"tally": tally.__dict__ if tally else None}), encoding="utf-8")

    clean = all(t.clean() for t in tallies)
    if namespace_result is not None and namespace_result.get("tally") and tallies:
        second = namespace_result["tally"]
        clean = clean and not (second["diffs"] or second["fails"] or second["violations"])
        print(f"\nTOTAL: {sum(t.cases for t in tallies) + second['cases']} cases in two passes: "
              f"{sum(t.passes for t in tallies) + second['passes']} PASS/OK, "
              f"{sum(t.diffs for t in tallies) + second['diffs']} DIFF/driver errors, "
              f"{sum(t.fails for t in tallies) + second['fails']} FAIL")
    elif namespace_result is not None and namespace_result.get("tally"):
        second = namespace_result["tally"]  # nothing was runnable on the host: the namespace pass is the whole run
        clean = clean and not (second["diffs"] or second["fails"] or second["violations"])
    elif skipped and not args.in_namespace:
        clean = False  # cases that could not run at all are not a pass
    if pending and not args.in_namespace:
        print(f"\nKotlin half PENDING: {args.module_jar} does not exist yet.")
        print(f"Once it exists run: python3 {Path(__file__).resolve()}")
    if not args.in_namespace:
        print("Not covered: " + "; ".join(NOT_COVERED))
    if not clean:
        return 1
    return 3 if pending else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:  # e.g. `run.py --list | head`
        os.dup2(os.open(os.devnull, os.O_WRONLY), sys.stdout.fileno())
        raise SystemExit(141) from None
