#!/usr/bin/env python3
"""Shared AI-generation protocol for artifact-pipeline.

Cott Result types vs direct tagged dicts are adapted only in validate();
that glue is evaluation-only and must not appear in model prompts.
Business errors are tagged outcomes, not Python exceptions.
"""
from __future__ import annotations

import argparse
import importlib.util
import json
import sys
from pathlib import Path

MODEL = "openai-codex/gpt-5.6-sol"
THINKING = "high"
CHECKER = (
    Path(__file__).resolve().parent.parent
    / "examples/complex/artifact-pipeline/check_semantics.py"
)

REQUIREMENTS = """
Validate and order build steps. Same business rules for both public functions.

Names are case-sensitive and otherwise unmodified. A name is blank iff
name.strip()==''. Whitespace-only names are blank; do not strip non-blank names.

Each step's needs is a set: duplicate dependency strings are ignored.

Error precedence (first match wins): BlankStepName, DuplicateStep,
UnknownDependency, SelfDependency, Cycle.
- BlankStepName: any step name is blank.
- DuplicateStep: two steps share the same name.
- UnknownDependency: a need is not equal to any step name.
- SelfDependency: a step lists its own name in needs.
- Cycle: no valid total order remains.

Empty input succeeds with an empty order. Success returns every step name
exactly once.

Deterministic order: repeatedly emit the lexicographically smallest name among
currently ready steps (all needs already emitted). Newly ready steps join the
ready set immediately and compete by the same lexical rule.

plan_pipeline must call public topologically_order_steps on the pipeline steps
and propagate that error unchanged; on success wrap the order as ordered_steps.
""".strip()


def direct_prompt() -> str:
    return (
        "Write only a complete stdlib pipeline.py. No tests, extras, or other files.\n"
        "Required public ABI with typing.TypedDict / Literal / union annotations:\n"
        "  ErrorName = Literal['BlankStepName','DuplicateStep','UnknownDependency',"
        "'SelfDependency','Cycle']\n"
        "  class Step(TypedDict): name: str; needs: list[str]\n"
        "  class Pipeline(TypedDict): steps: list[Step]\n"
        "  def topologically_order_steps(steps: list[Step]) -> OrderResult\n"
        "  def plan_pipeline(pipeline: Pipeline) -> PlanResult\n"
        "  OrderResult is {'ok': list[str]} | {'error': ErrorName}\n"
        "  PlanResult is {'ok': {'ordered_steps': list[str]}} | {'error': ErrorName}\n"
        "Return those tagged dicts for business outcomes; do not raise them.\n"
        "Do not emit Cott runtime types or evaluation adapters.\n"
        f"{REQUIREMENTS}"
    )


def _load(path: Path, name: str):
    path = Path(path).resolve()
    if not path.is_file():
        raise FileNotFoundError(f"missing {name}: {path}")
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise ImportError(f"cannot import {path}")
    mod = importlib.util.module_from_spec(spec)
    sys.modules[name] = mod
    spec.loader.exec_module(mod)
    return mod


def _direct_norm(result, *, plan: bool):
    if not isinstance(result, dict):
        raise AssertionError(f"expected dict result, got {type(result).__name__}")
    if result.keys() == {"error"}:
        name = result["error"]
        if name not in (
            "BlankStepName",
            "DuplicateStep",
            "UnknownDependency",
            "SelfDependency",
            "Cycle",
        ):
            raise AssertionError(f"error must be declared ErrorName, got {name!r}")
        return {"error": name}
    if result.keys() == {"ok"}:
        ok = result["ok"]
        if plan:
            if not isinstance(ok, dict) or ok.keys() != {"ordered_steps"}:
                raise AssertionError(
                    f"plan ok must be {{'ordered_steps': list[str]}}, got {ok!r}"
                )
            ok = ok["ordered_steps"]
        if not isinstance(ok, list) or not all(isinstance(name, str) for name in ok):
            raise AssertionError(f"order must be list[str], got {ok!r}")
        return {"ok": ok}
    raise AssertionError(f"result must be {{'ok':...}} or {{'error':...}}, got {result!r}")


def _direct_evals(project: Path):
    mod = _load(Path(project) / "pipeline.py", "pipeline")
    for attr in ("Step", "Pipeline", "topologically_order_steps", "plan_pipeline"):
        if not hasattr(mod, attr):
            raise AttributeError(f"pipeline.py missing public {attr}")
    Step, Pipeline = mod.Step, mod.Pipeline

    def steps_of(raw):
        return [Step(name=s["name"], needs=list(s["needs"])) for s in raw]

    def order_eval(raw):
        return _direct_norm(mod.topologically_order_steps(steps_of(raw)), plan=False)

    def plan_eval(raw):
        return _direct_norm(
            mod.plan_pipeline(Pipeline(steps=steps_of(raw))), plan=True
        )

    return order_eval, plan_eval


def validate(arm: str, project: Path) -> dict:
    checker = _load(CHECKER, "check_semantics")
    project = Path(project)
    if arm == "cott":
        order_eval, plan_eval = checker._load_project(project)
    elif arm == "direct":
        order_eval, plan_eval = _direct_evals(project)
    else:
        raise ValueError(f"unknown arm {arm!r}; use cott or direct")
    return {
        "topologically_order_steps": checker.check(order_eval),
        "plan_pipeline": checker.check(plan_eval),
    }


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(
        description="Independent AI-generation acceptance; oracle stays in the checker."
    )
    parser.add_argument("--arm", required=True, choices=("cott", "direct"))
    parser.add_argument("--project", required=True)
    args = parser.parse_args(argv)
    json.dump(validate(args.arm, Path(args.project)), sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
