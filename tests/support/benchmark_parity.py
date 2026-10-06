"""Unit regression only: stub loader in memory to compare wrapper predicates, NEVER benchmark it."""
from pathlib import Path
import sys

project, mode, depth = Path(sys.argv[1]), sys.argv[2], int(sys.argv[3])
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "benchmarks"))
import python_boundary as harness
sys.path.insert(0, str(project / "generated/python"))
import cott_runtime as r
import bench

algorithm = harness.load_file(project / "python/cott_bindings/algorithm.py", "unit_algorithm").echo
bench._cott_load = lambda *args, **kwargs: algorithm  # test-only, no file/provenance alteration
annotation, good = harness.workload(r, 2, depth)


def make_value(leaf):
    value = r.CottList(values=(leaf,))
    for _ in range(depth - 1):
        value = r.CottList(values=(value,))
    return value


def outcome(call, value):
    try:
        return ("accepted", call(value))
    except (r.CottContractViolation, AssertionError):
        return ("rejected",)


for context in ((False, True) if mode == "test-only" else (False,)):
    if mode == "test-only":
        bench._cott_set_test_context(context)
    checked = harness.checked_call(r, algorithm, annotation, mode, context)
    for value in (good, make_value(True), make_value("wrong"), make_value(2**32)):
        assert outcome(checked, value) == outcome(bench.echo, value), (mode, context, value)
    saved = algorithm
    algorithm = lambda value: make_value(1)
    checked_bad = harness.checked_call(r, algorithm, annotation, mode, context)
    assert outcome(checked_bad, good) == outcome(bench.echo, good), (mode, context, "postcondition")
    algorithm = saved
