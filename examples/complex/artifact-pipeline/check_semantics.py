"""Independent artifact-pipeline acceptance.

Finite executable corpus for topological order and error priority. Not `cott
verify`, not compiler proof, and not semantic_coverage. Enumeration covers
labeled graphs of at most 3 nodes; larger DAGs are explicit cases only.
"""

from __future__ import annotations

import argparse
import json
import sys
from itertools import combinations, permutations, product
from pathlib import Path

_ERRORS = (
    "BlankStepName",
    "DuplicateStep",
    "UnknownDependency",
    "SelfDependency",
    "Cycle",
)
_MAX_PERM = 8  # ponytail: n! oracle; explicit expected above this


def expected_order(steps):
    """Bounded permutation oracle. Not Kahn's algorithm."""
    for step in steps:
        if all(
            character in "\t\n\v\f\r \u0085\u00a0\u1680\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a\u2028\u2029\u202f\u205f\u3000"
            for character in step["name"]
        ):
            return {"error": "BlankStepName"}
    names = []
    seen = set()
    for step in steps:
        name = step["name"]
        if name in seen:
            return {"error": "DuplicateStep"}
        seen.add(name)
        names.append(name)
    needs = {step["name"]: set(step["needs"]) for step in steps}
    for deps in needs.values():
        if not deps.issubset(seen):
            return {"error": "UnknownDependency"}
    for name, deps in needs.items():
        if name in deps:
            return {"error": "SelfDependency"}
    if len(names) > _MAX_PERM:
        raise ValueError(f"expected_order permutation cap is {_MAX_PERM} nodes")
    best = None
    for perm in permutations(names):
        pos = {name: index for index, name in enumerate(perm)}
        if all(pos[dep] < pos[name] for name, deps in needs.items() for dep in deps):
            candidate = list(perm)
            if best is None or candidate < best:
                best = candidate
    if best is None:
        return {"error": "Cycle"}
    return {"ok": best}


def _case(name, steps, expected=None):
    return {
        "name": name,
        "steps": steps,
        "expected": expected if expected is not None else expected_order(steps),
    }


def _powerset(labels):
    return [
        combo
        for size in range(len(labels) + 1)
        for combo in combinations(labels, size)
    ]


def _enumerated():
    cases = []
    labels_all = ("a", "b", "c")
    for count in range(4):
        labels = labels_all[:count]
        if count == 0:
            cases.append(_case("enum0:", []))
            continue
        attached_choices = product(_powerset(labels), repeat=count)
        for choice in attached_choices:
            attached = {labels[i]: list(choice[i]) for i in range(count)}
            for order in permutations(labels):
                steps = [{"name": name, "needs": list(attached[name])} for name in order]
                sig = ",".join(
                    f"{name}:{'+'.join(attached[name])}" for name in order
                )
                cases.append(_case(f"enum{count}:{sig}", steps))
    return cases


def _explicit():
    return [
        _case("empty", []),
        _case("unicode-white-space", [{"name": "\u0085\u2007\u202f", "needs": []}]),
        _case("bom-is-not-white-space", [{"name": "\ufeff", "needs": []}]),
        _case("separator-is-not-white-space", [{"name": "\u001c", "needs": []}]),
        _case(
            "shuffled-chain",
            [
                {"name": "c", "needs": ["b"]},
                {"name": "a", "needs": []},
                {"name": "b", "needs": ["a"]},
            ],
        ),
        _case(
            "diamond",
            [
                {"name": "d", "needs": ["b", "c"]},
                {"name": "b", "needs": ["a"]},
                {"name": "c", "needs": ["a"]},
                {"name": "a", "needs": []},
            ],
        ),
        _case(
            "disconnected",
            [
                {"name": "z", "needs": []},
                {"name": "a", "needs": []},
                {"name": "m", "needs": []},
            ],
        ),
        _case(
            "lex-ready-new-node-priority",
            [
                {"name": "m", "needs": []},
                {"name": "z", "needs": []},
                {"name": "a", "needs": ["m"]},
            ],
        ),
        _case(
            "names-preserved-once",
            [
                {"name": "pack", "needs": []},
                {"name": "test", "needs": ["pack"]},
                {"name": "lint", "needs": ["pack"]},
            ],
        ),
        _case("blank-empty", [{"name": "", "needs": []}]),
        _case("blank-spaces", [{"name": "  ", "needs": []}]),
        _case("blank-tabs", [{"name": "\t\n", "needs": []}]),
        _case(
            "name-with-padding-kept",
            [
                {"name": " a", "needs": []},
                {"name": "b", "needs": [" a"]},
            ],
        ),
        _case(
            "duplicate",
            [
                {"name": "a", "needs": []},
                {"name": "a", "needs": ["b"]},
            ],
        ),
        _case("unknown", [{"name": "a", "needs": ["ghost"]}]),
        _case("unknown-empty-dep", [{"name": "a", "needs": [""]}]),
        _case("self", [{"name": "a", "needs": ["a"]}]),
        _case(
            "cycle-2",
            [
                {"name": "a", "needs": ["b"]},
                {"name": "b", "needs": ["a"]},
            ],
        ),
        _case(
            "cycle-3",
            [
                {"name": "a", "needs": ["c"]},
                {"name": "b", "needs": ["a"]},
                {"name": "c", "needs": ["b"]},
            ],
        ),
        _case(
            "precedence-blank",
            [
                {"name": "  ", "needs": ["ghost", "  "]},
                {"name": "  ", "needs": []},
                {"name": "x", "needs": ["y"]},
                {"name": "y", "needs": ["x"]},
            ],
        ),
        _case(
            "precedence-duplicate",
            [
                {"name": "a", "needs": ["ghost"]},
                {"name": "a", "needs": ["a"]},
                {"name": "b", "needs": ["c"]},
                {"name": "c", "needs": ["b"]},
            ],
        ),
        _case(
            "precedence-unknown",
            [
                {"name": "a", "needs": ["a", "ghost"]},
                {"name": "b", "needs": ["c"]},
                {"name": "c", "needs": ["b"]},
            ],
        ),
        _case(
            "precedence-self",
            [
                {"name": "a", "needs": ["a"]},
                {"name": "b", "needs": ["c"]},
                {"name": "c", "needs": ["b"]},
            ],
        ),
        _case(
            "large-dag",
            [
                {"name": "deploy", "needs": ["image"]},
                {"name": "lint", "needs": ["compile"]},
                {"name": "image", "needs": ["bundle"]},
                {"name": "compile", "needs": []},
                {"name": "bundle", "needs": ["lint", "test"]},
                {"name": "test", "needs": ["compile"]},
            ],
        ),
        _case(
            "large-chain",
            [
                {"name": "s5", "needs": ["s4"]},
                {"name": "s1", "needs": []},
                {"name": "s8", "needs": ["s7"]},
                {"name": "s3", "needs": ["s2"]},
                {"name": "s7", "needs": ["s6"]},
                {"name": "s2", "needs": ["s1"]},
                {"name": "s6", "needs": ["s5"]},
                {"name": "s4", "needs": ["s3"]},
            ],
            {"ok": ["s1", "s2", "s3", "s4", "s5", "s6", "s7", "s8"]},
        ),
        _case(
            "large-new-ready",
            [
                {"name": "b", "needs": []},
                {"name": "d", "needs": []},
                {"name": "c", "needs": ["b"]},
                {"name": "a", "needs": ["c"]},
            ],
        ),
    ]


def cases():
    return _enumerated() + _explicit()


def check(evaluate):
    count = 0
    for case in cases():
        steps = [
            {"name": step["name"], "needs": list(step["needs"])} for step in case["steps"]
        ]
        actual = evaluate(steps)
        if actual != case["expected"]:
            raise AssertionError(
                f"{case['name']}: expected {case['expected']!r}, got {actual!r}"
            )
        count += 1
    return count


def _normalize(result):
    tag = type(result).__name__
    if tag == "Ok":
        value = result.value
        ordered = value.ordered_steps if hasattr(value, "ordered_steps") else value
        return {"ok": list(ordered)}
    if tag == "Err":
        name = type(result.error).__name__.removeprefix("ArtifactPipelineError_")
        if name not in _ERRORS:
            raise AssertionError(f"unexpected error variant {name!r}")
        return {"error": name}
    raise AssertionError(f"unexpected result type {tag}")


def _load_project(project):
    generated = Path(project).resolve() / "generated" / "python"
    sys.path.insert(0, str(generated))
    from cott_runtime import CottList, CottSet
    from curriculum.artifact_pipeline import (
        plan_pipeline,
        topologically_order_steps,
    )
    from curriculum.artifact_pipeline_types import BuildStep, Pipeline

    def _steps(raw):
        return CottList(
            values=[
                BuildStep(name=step["name"], needs=CottSet(values=step["needs"]))
                for step in raw
            ]
        )

    def order_eval(raw):
        return _normalize(topologically_order_steps(_steps(raw)))

    def plan_eval(raw):
        return _normalize(plan_pipeline(Pipeline(steps=_steps(raw))))

    return order_eval, plan_eval


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Independent artifact-pipeline acceptance; not cott verify."
    )
    parser.add_argument(
        "--project",
        default=str(Path(__file__).resolve().parent),
    )
    args = parser.parse_args(argv)
    order_eval, plan_eval = _load_project(args.project)
    payload = {
        "topologically_order_steps": check(order_eval),
        "plan_pipeline": check(plan_eval),
    }
    json.dump(payload, sys.stdout)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
