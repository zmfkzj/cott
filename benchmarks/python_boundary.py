#!/usr/bin/env python3
"""Paired Python boundary measurements. No provider calls, fake pins, or certification shortcuts.

Default: fresh authored binding fixtures, real emit/verify, authenticated facade.
--component-runtime: explicitly isolated ABI-checker experiment; NO facade/certification claim.
Run with the interpreter being measured. See benchmarks/README.md for scopes and limits.
"""
from __future__ import annotations

import argparse
import cProfile
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import platform
import pstats
import statistics
import subprocess
import sys
import tempfile
import time
import tracemalloc

ROOT = Path(__file__).resolve().parents[1]
MODES = ("boundary", "test-only", "off")
ARMS = ("direct-unchecked", "direct-checked", "facade")


def digest(data):
    return hashlib.sha256(data).hexdigest()


def file_identity(path):
    path = Path(path).resolve()
    return {"path": str(path), "sha256": digest(path.read_bytes()), "bytes": path.stat().st_size}


def environment():
    # Never serialize the ambient environment (it can contain provider credentials).
    return {**os.environ, "PYTHONHASHSEED": "0", "PYTHONDONTWRITEBYTECODE": "1"}


def summary(values):
    return {"samples": values, "median": statistics.median(values), "min": min(values),
            "max": max(values), "stdev": statistics.stdev(values) if len(values) > 1 else 0.0}


def load_file(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def fixture_sources(depth):
    """Fixed identity algorithm: only nesting changes. Both direct arms load these exact bytes."""
    ty, py = "I32", "I32"
    for _ in range(depth):
        ty, py = f"List[{ty}]", f"CottList[{py}]"
    return {
        "src/bench.cott": (
            f"module bench\n\nfn echo(items: {ty}) -> {ty}:\n"
            "    requires items.len >= 0\n    ensures result == items\n"
        ),
        "python/cott_bindings/algorithm.py": (
            "from cott_runtime import CottList, I32\n\n\n"
            f"def echo(items: {py}) -> {py}:\n    return items\n"
        ),
        "python/pyproject.toml": (
            '[project]\nname = "boundary-benchmark"\nversion = "0.1.0"\n'
            'requires-python = ">=3.14.6,<3.15"\ndependencies = []\n'
        ),
    }


def write_fixture(root, depth, mode, checker):
    sources = fixture_sources(depth)
    sources["cott.toml"] = (
        '[project]\nname = "boundary-benchmark"\nversion = "0.1.0"\nsource = "src"\n\n'
        '[target.python]\nsource = "python"\ngenerated = "generated/python"\n'
        'stubs = "generated/stubs"\n'
        'interpreter = ".tools/python"\ntype_checker = ".tools/basedpyright"\n'
        f'runtime_validation = "{mode}"\n\n[target.python.implementations]\n'
        '"bench.echo" = "cott_bindings.algorithm:echo"\n'
    )
    root.mkdir()
    (root / ".tools").mkdir()
    (root / ".tools/python").symlink_to(Path(sys.executable).resolve())
    import shutil
    checker_path = shutil.which(checker)
    if checker_path:
        (root / ".tools/basedpyright").symlink_to(Path(checker_path).absolute())
    for relative, content in sources.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return {key: digest(value.encode()) for key, value in sources.items()}


def tool_run(argv, cwd=None):
    start = time.perf_counter_ns()
    try:
        done = subprocess.run(argv, cwd=cwd, env=environment(), capture_output=True, text=True,
                              timeout=900, input="")
        # Only our fixed compiler/tool commands, not providers or credential commands.
        return {"argv": list(map(str, argv)), "returncode": done.returncode,
                "seconds": (time.perf_counter_ns() - start) / 1e9,
                "stdout": done.stdout, "stderr": done.stderr}
    except (OSError, subprocess.TimeoutExpired) as error:
        return {"argv": list(map(str, argv)), "returncode": None,
                "seconds": (time.perf_counter_ns() - start) / 1e9, "error": str(error)}


def verified_snapshot(root):
    # Inspection only. The compiler and runtime are the authorities; do not manufacture evidence.
    wire = json.loads((root / "generated/generation.json").read_text())
    current = wire["snapshots"][wire["current"]]
    if not current["verified"] or wire["current"] != wire["last_verified"]:
        raise ValueError("real verify did not certify the current snapshot")
    return {"current": wire["current"], "last_verified": wire["last_verified"],
            "tools": current["tools"], "generation_id": current["generation_id"]}


def input_description(size, depth):
    # Unique leaves avoid benchmarking traversal memo hits on repeated integer objects.
    value = list(range(1000, 1000 + size))
    for _ in range(depth - 1):
        value = [value]
    return value


def workload(runtime, size, depth):
    annotation = runtime.I32
    for _ in range(depth):
        annotation = runtime.CottList[annotation]
    value = runtime.CottList(values=range(1000, 1000 + size))
    for _ in range(depth - 1):
        value = runtime.CottList(values=(value,))
    return annotation, value


def checked_call(runtime, algorithm, annotation, mode, test_context):
    """Same value normalization and two predicates as the emitted fixed fixture, not provenance.

    test-only normalizes inputs even in test context; output validation/predicates are conditional.
    This is deliberately not an alternate public Cott facade or observer/evidence implementation.
    """
    check = mode == "boundary" or (mode == "test-only" and test_context)

    def invoke(items):
        items = (runtime._cott_validate_abi if mode == "boundary" else
                 runtime._cott_normalize_f32_abi)(items, annotation, path="$.items")
        if check and not len(items) >= 0:
            raise AssertionError("echo requires len(items) >= 0")
        result = algorithm(items)
        result = (runtime._cott_validate_abi if check else
                  runtime._cott_normalize_f32_abi)(result, annotation, path="$.return")
        if check and not result == items:
            raise AssertionError("echo ensures result == items")
        return result
    return invoke


def correctness(runtime, checked, annotation, good, mode, test_context):
    assert checked(good) == good
    invalid = runtime.CottList(values=("not an integer",))
    # Malformed shape is rejected for any supported depth when validation is active.
    if mode == "boundary" or (mode == "test-only" and test_context):
        try:
            checked(invalid)
        except runtime.CottContractViolation as error:
            assert error.phase == "validation", (error.phase, str(error))
        else:
            raise AssertionError("checked path accepted malformed input")
    return {"valid_equal": True, "invalid_rejected": mode == "boundary" or
            (mode == "test-only" and test_context)}


def worker(config):
    started = time.perf_counter_ns()
    sys.path.insert(0, config["runtime"])
    if config.get("project"):
        sys.path.insert(1, str(Path(config["project"]) / "python"))
    import cott_runtime as runtime
    if config.get("project"):
        project = Path(config["project"])
        algorithm = load_file(project / "python/cott_bindings/algorithm.py", "benchmark_algorithm").echo
    else:
        # Same fixed algorithm as fixture_sources. Isolated checker only, never a facade.
        def algorithm(items):
            return items
    if config["arm"] == "facade":
        import bench
        if config["mode"] == "test-only":
            bench._cott_set_test_context(config["test_context"])
        call = bench.echo
    else:
        call = algorithm
    annotation, value = workload(runtime, config["size"], config["depth"])
    checked = checked_call(runtime, algorithm, annotation, config["mode"], config["test_context"])
    if config["arm"] == "direct-checked":
        call = checked
    setup_ns = time.perf_counter_ns() - started
    first_start = time.perf_counter_ns()
    first = call(value)
    first_ns = time.perf_counter_ns() - first_start
    assert first == value
    if config.get("phase") == "cold":
        return {"setup_ns": setup_ns, "first_call_ns": first_ns, "correctness": {"valid_equal": True}}
    correctness_result = ({"valid_equal": True, "invalid_rejected": None}
                          if config["arm"] == "direct-unchecked" else
                          correctness(runtime, call, annotation, value, config["mode"], config["test_context"]))
    for _ in range(3):
        assert call(value) == value
    start = time.perf_counter_ns()
    for _ in range(config["loops"]):
        result = call(value)
    elapsed = time.perf_counter_ns() - start
    assert result == value
    # Separate untimed run: tracemalloc measures traced Python allocations, not RSS or total churn.
    tracemalloc.start()
    before, _ = tracemalloc.get_traced_memory()
    tracemalloc.reset_peak()
    result = call(value)
    retained, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    profile = []
    if config.get("profile") and config["arm"] == "direct-checked":
        profiler = cProfile.Profile()
        profiler.enable()
        for _ in range(config["loops"]):
            checked(value)
        profiler.disable()
        for (filename, line, name), (primitive, calls, total, cumulative, _) in sorted(
                pstats.Stats(profiler).stats.items(), key=lambda pair: pair[1][3], reverse=True)[:20]:
            profile.append({"file": Path(filename).name, "line": line, "symbol": name,
                            "calls": calls, "self_seconds": total, "cumulative_seconds": cumulative})
    return {"setup_ns": setup_ns, "first_call_ns": first_ns,
            "warm_ns_per_call": elapsed / config["loops"], "loops": config["loops"],
            "traced_peak_bytes": peak - before, "traced_retained_bytes": retained - before,
            "correctness": correctness_result, "profile": profile,
            "interpreter": {"executable": sys.executable, "version": sys.version,
                            "cache_tag": sys.implementation.cache_tag}}


def measure(config, repeat):
    samples = []
    for _ in range(repeat):
        cold = tool_run([sys.executable, str(Path(__file__).resolve()), "--worker",
                         json.dumps({**config, "phase": "cold"})])
        result = tool_run([sys.executable, str(Path(__file__).resolve()), "--worker", json.dumps(config)])
        if cold["returncode"] != 0 or result["returncode"] != 0:
            raise RuntimeError(f"worker failed: {cold if cold['returncode'] != 0 else result}")
        sample = json.loads(result["stdout"])
        sample["cold_process_seconds"] = cold["seconds"]
        sample["cold"] = json.loads(cold["stdout"])
        samples.append(sample)
    return {**config, "input_sha256": digest(json.dumps(input_description(config["size"], config["depth"])).encode()),
            "provenance": "authenticated Cott facade" if config["arm"] == "facade" else "none",
            "raw": samples, "summary": {key: summary([s[key] for s in samples]) for key in
                ("cold_process_seconds", "setup_ns", "first_call_ns", "warm_ns_per_call",
                 "traced_peak_bytes", "traced_retained_bytes")}}


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--worker", help=argparse.SUPPRESS)
    parser.add_argument("--cott", help="absolute compiler path; mandatory for facade runs")
    parser.add_argument("--type-checker", default="basedpyright")
    parser.add_argument("--component-runtime", type=Path,
                        help="explicit non-certified ABI checker scope; no facade/tool timings")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--label", default="current")
    parser.add_argument("--sizes", type=int, nargs="+", default=[4, 128])
    parser.add_argument("--depths", type=int, nargs="+", default=[1, 3])
    parser.add_argument("--modes", choices=MODES, nargs="+", default=["boundary"])
    parser.add_argument("--repeat", type=int, default=5)
    parser.add_argument("--loops", type=int, default=25)
    parser.add_argument("--profile", action="store_true")
    args = parser.parse_args(argv)
    if args.worker:
        return args
    if not args.output or (not args.component_runtime and not args.cott):
        parser.error("--output and either --cott or --component-runtime are required")
    if args.component_runtime and args.cott:
        parser.error("component and certified facade scopes must be separate runs")
    if not 1 <= args.repeat <= 100 or not 1 <= args.loops <= 100000:
        parser.error("repeat must be 1..100 and loops 1..100000")
    if any(n < 0 or n > 100000 for n in args.sizes) or any(d < 1 or d > 16 for d in args.depths):
        parser.error("sizes must be 0..100000 and depths 1..16")
    if args.output.exists():
        parser.error("output already exists; retain historical runs, choose a fresh path")
    return args


def main(argv=None):
    args = parse_args(argv)
    if args.worker:
        print(json.dumps(worker(json.loads(args.worker))))
        return 0
    component = args.component_runtime is not None
    result = {
        "schema_version": 1, "label": args.label, "scope": "component-only; NOT verified/facade" if component else "verified-facade-requested",
        "identity": {"head": tool_run(["git", "rev-parse", "HEAD"], ROOT)["stdout"].strip(),
                     "python": {**file_identity(sys.executable), "version": sys.version, "platform": platform.platform()},
                     "target_python_compatible": (3, 14, 6) <= sys.version_info[:3] < (3, 15, 0),
                     "target_requirements": "CPython >=3.14.6,<3.15; BasedPyright >=1.39.9 for real verify",
                     "cpu_count": os.cpu_count(),
                     "scripts": {Path(__file__).name: file_identity(Path(__file__))},
                     "workspace_sources_at_measurement": {p.name: file_identity(p) for p in
                                                          (ROOT / "src/python_runtime.rs", ROOT / "src/python_emit.rs")},
                     "source_identity_note": "Measured runtime bytes/compiler-export are recorded per row; workspace sources may differ from an older compiled baseline.",
                     "settings": {k: v for k, v in vars(args).items() if k not in ("worker", "output")},
                     "model": None, "generation": "not run: authored fixed-algorithm binding, no model required"},
        "limits": ["Synthetic identity algorithm, not application throughput or developer productivity.",
                   "Direct-checked reuses Cott value validators and identical predicates; no provenance guarantee.",
                   "Cold process includes startup/import/input construction; first-call is reported separately.",
                   "Warm excludes correctness/profile/tracemalloc; fixed hash seed 0, sequential processes.",
                   "tracemalloc peak/retained is one untimed call; excludes native allocations/RSS and total allocation count.",
                   "test-only context toggle is for measurement only, never runner observation/certification evidence."],
        "tool_costs": [], "rows": [], "blockers": [],
    }
    if not component:
        result["identity"]["compiler"] = file_identity(args.cott)
        result["identity"]["compiler_version"] = tool_run([args.cott, "--version"])
        result["identity"]["type_checker_version"] = tool_run([args.type_checker, "--version"])
    try:
        with tempfile.TemporaryDirectory(prefix="cott-boundary-benchmark-") as temp:
            for depth in dict.fromkeys(args.depths):
                for mode in dict.fromkeys(args.modes):
                    project = None
                    if component:
                        runtime = args.component_runtime.resolve()
                    else:
                        project = Path(temp) / f"{mode}-{depth}"
                        sources = write_fixture(project, depth, mode, args.type_checker)
                        costs = {"mode": mode, "depth": depth, "sources": sources, "generate": {"status": "not-run", "model": None}}
                        result["tool_costs"].append(costs)
                        costs["emit"] = tool_run([args.cott, "emit", "python", "--project", str(project)])
                        if costs["emit"]["returncode"] != 0:
                            result["blockers"].append({"stage": "emit", "mode": mode, "depth": depth})
                            continue
                        costs["verify"] = tool_run([args.cott, "verify", "--project", str(project)])
                        if costs["verify"]["returncode"] != 0:
                            result["blockers"].append({"stage": "verify", "mode": mode, "depth": depth})
                            continue
                        costs["snapshot"] = verified_snapshot(project)
                        runtime = project / "generated/python"
                    runtime_id = file_identity(runtime / "cott_runtime/__init__.py")
                    export = runtime / "benchmark-export.json"
                    runtime_id["compiler_export"] = json.loads(export.read_text()) if export.exists() else None
                    runtime_id["package_bytes"] = sum(p.stat().st_size for p in (runtime / "cott_runtime").rglob("*.py"))
                    for context in ([False, True] if mode == "test-only" else [False]):
                        for size in dict.fromkeys(args.sizes):
                            for arm in (ARMS[:2] if component else ARMS):
                                row = measure({"project": str(project) if project else None, "runtime": str(runtime),
                                               "arm": arm, "mode": mode, "test_context": context,
                                               "size": size, "depth": depth, "loops": args.loops,
                                               "profile": args.profile}, args.repeat)
                                row["runtime_identity"] = runtime_id
                                result["rows"].append(row)
    except (OSError, RuntimeError, ValueError, KeyError) as error:
        result["blockers"].append({"stage": "measurement", "error": str(error)})
    result["status"] = "blocked" if result["blockers"] else "measured"
    args.output.parent.mkdir(parents=True, exist_ok=True)
    # Exclusive create protects existing historical reports even against an intervening run.
    with args.output.open("x", encoding="utf-8") as out:
        json.dump(result, out, indent=2, default=str)
        out.write("\n")
    print(f"{result['status']}: {args.output} ({len(result['rows'])} rows)")
    return 1 if result["blockers"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
