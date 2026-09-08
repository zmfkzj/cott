from __future__ import annotations

import argparse
import heapq
import importlib.util
import json
import sys
from collections.abc import Callable
from pathlib import Path
from typing import TypedDict, cast


class Step(TypedDict):
    name: str
    needs: list[str]


class OkOutcome(TypedDict):
    ok: list[str]


class ErrOutcome(TypedDict):
    error: str


Outcome = OkOutcome | ErrOutcome
EvaluateFn = Callable[[list[Step]], Outcome]
CheckFn = Callable[[EvaluateFn], int]


def evaluate(steps: list[Step]) -> Outcome:
    for step in steps:
        if step["name"].strip() == "":
            return {"error": "BlankStepName"}

    names: set[str] = set()
    for step in steps:
        name = step["name"]
        if name in names:
            return {"error": "DuplicateStep"}
        names.add(name)

    needs_of: dict[str, set[str]] = {
        step["name"]: set(step["needs"]) for step in steps
    }

    for step in steps:
        for dependency in needs_of[step["name"]]:
            if dependency not in names:
                return {"error": "UnknownDependency"}

    for step in steps:
        if step["name"] in needs_of[step["name"]]:
            return {"error": "SelfDependency"}

    indegree: dict[str, int] = {}
    dependents: dict[str, list[str]] = {}
    for step in steps:
        name = step["name"]
        indegree[name] = len(needs_of[name])
        dependents[name] = []
    for step in steps:
        name = step["name"]
        for dependency in needs_of[name]:
            dependents[dependency].append(name)

    ready = [name for name in names if indegree[name] == 0]
    heapq.heapify(ready)
    ordered: list[str] = []
    while ready:
        name = heapq.heappop(ready)
        ordered.append(name)
        for dependent in dependents[name]:
            indegree[dependent] -= 1
            if indegree[dependent] == 0:
                heapq.heappush(ready, dependent)

    if len(ordered) != len(steps):
        return {"error": "Cycle"}
    return {"ok": ordered}


def _attr(obj: object, name: str) -> object:
    return cast(object, getattr(obj, name))


def _load_checker(path: Path) -> CheckFn:
    spec = importlib.util.spec_from_file_location("check_semantics", path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    check = _attr(module, "check")
    if not callable(check):
        raise SystemExit(f"cannot import {path}")
    return cast(CheckFn, check)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    cases_opt = parser.add_argument("--cases", required=True)
    parsed: object = parser.parse_args(argv)
    cases = _attr(parsed, cases_opt.dest)
    if not isinstance(cases, str):
        raise SystemExit("--cases must be a path")
    check = _load_checker(Path(cases))
    print(json.dumps({"cases": check(evaluate)}))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
