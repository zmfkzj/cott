#!/usr/bin/env python3
"""Bounded native microbenchmark; compiler-owned consumer tests are separate."""
import argparse
import csv
import hashlib
import io
import json
import os
from pathlib import Path
import platform
import statistics
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--rustc", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--indexed", action="store_true")
    parser.add_argument("--repeat", type=int, default=7)
    args = parser.parse_args()
    if not args.rustc.is_absolute() or not 1 <= args.repeat <= 25 or args.output.exists():
        parser.error("absolute rustc, repeat 1..25, and a new output path required")
    report = {
        "scope": "runtime fragment microbenchmark, NOT certified facade",
        "rustc": subprocess.check_output([str(args.rustc), "-Vv"], text=True),
        "host": platform.platform(),
        "source": {"path": str(args.source.resolve()), "sha256": sha(args.source)},
        "harness_sha256": sha(__file__),
        "rust_harness_sha256": sha(ROOT / "benchmarks/rust_collections.rs"),
        "input": "v1: sizes 8/128/2048, key i%(size*3/4), string key-{i:08}",
        "indexed": args.indexed,
        "samples": [],
        "limits": [
            "release opt-level3, one process per sample, no CPU isolation",
            "nanoseconds per full operation (lookup visits all input keys)",
            "allocation count and requested bytes for a separate operation, including owned input clones; not RSS/retained/peak; std allocator counter adds timing overhead",
            "25% duplicate integer/string keys; same inputs and compiler flags; do not generalize to user key types",
        ],
    }
    with tempfile.TemporaryDirectory(prefix="cott-rust-collections-") as temp:
        binary = Path(temp) / "bench"
        command = [str(args.rustc), "--edition=2024", "-C", "opt-level=3",
                   str(ROOT / "benchmarks/rust_collections.rs"), "-o", str(binary)]
        if args.indexed:
            command += ["--cfg", "indexed"]
        build = subprocess.run(command, env={**os.environ, "COTT_COLLECTION_SOURCE": str(args.source.resolve())},
                               capture_output=True, text=True, timeout=60)
        report["build"] = {"argv": command, "returncode": build.returncode, "stderr": build.stderr}
        if build.returncode:
            raise RuntimeError(build.stderr)
        for _ in range(args.repeat):
            run = subprocess.run([str(binary)], capture_output=True, text=True, timeout=120)
            if run.returncode:
                raise RuntimeError(run.stderr)
            report["layout"] = run.stderr.strip()
            report["samples"].append([
                {"key": row[0], "size": int(row[1]), "operation": row[2], "ns": int(row[3]),
                 "allocations": int(row[4]), "requested_bytes": int(row[5])}
                for row in csv.reader(io.StringIO(run.stdout))
            ])
    report["summary"] = []
    for index, original in enumerate(report["samples"][0]):
        row = {key: original[key] for key in ("key", "size", "operation")}
        for field in ("ns", "allocations", "requested_bytes"):
            values = [sample[index][field] for sample in report["samples"]]
            row[field] = {"raw": values, "median": statistics.median(values), "min": min(values), "max": max(values)}
        report["summary"].append(row)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("x") as out:
        json.dump(report, out, indent=2)
        out.write("\n")
    print(args.output)


if __name__ == "__main__":
    main()
