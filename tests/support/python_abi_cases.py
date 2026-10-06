"""Deterministic value/failure observations for runtime differential regression, not verification evidence."""
import dataclasses
import json
import math
import struct
import sys
from typing import Generic, TypeVar, Union

sys.path.insert(0, sys.argv[1])
import cott_runtime as r

T = TypeVar("T")


@dataclasses.dataclass(frozen=True)
class Box(Generic[T]):
    value: T


@dataclasses.dataclass(frozen=True)
class Node:
    child: "Node"


class IntSubclass(int):
    pass


def canonical(value):
    if type(value) is float:
        return {"float64_bits": struct.pack("!d", value).hex()}
    if dataclasses.is_dataclass(value):
        return {"type": type(value).__name__, "fields": {f.name: canonical(getattr(value, f.name)) for f in dataclasses.fields(value)}}
    if isinstance(value, r.CottList):
        return {"type": "CottList", "items": [canonical(item) for item in value]}
    if type(value) is bytes:
        return {"bytes": value.hex()}
    if type(value) is tuple:
        return {"tuple": [canonical(item) for item in value]}
    return value


observations = {}


def observe(name, value, annotation, *, normalize=False, depth=0):
    try:
        validator = r._cott_normalize_f32_abi if normalize else r._cott_validate_abi
        result = validator(value, annotation, path="$.case", _depth=depth)
        observations[name] = {"accepted": canonical(result)}
    except r.CottContractViolation as error:
        observations[name] = {"rejected": str(error), "phase": error.phase,
                              "clause": error.clause, "symbol": error.symbol,
                              "expected": error.expected, "actual": error.actual}


for annotation in (int, r.I8, r.I32, r.U64):
    name = str(annotation)
    for value in (0, -1, 127, 128, 2**31, 2**64 - 1, 2**64, True, 1.0, "1", IntSubclass(1)):
        observe(f"{name}/{type(value).__name__}/{value}", value, annotation)
for annotation, value in ((bool, True), (str, "😀"), (str, "\ud800"), (bytes, b"a"), (float, math.nan)):
    observe(str(annotation), value, annotation)
observe("union-good", 123, Union[str, int])
observe("union-bad", True, Union[str, int])
observe("union-annotated-bad", 128, Union[r.I8, str])
observe("nested", r.CottList(values=(r.CottList(values=(1, 2, 3)),)), r.CottList[r.CottList[r.I32]])
observe("generic", Box(value=r.CottList(values=(123,))), Box[r.CottList[r.I32]])
observe("generic-bad", Box(value=r.CottList(values=(True,))), Box[r.CottList[r.I32]])
box = Box(value=12)
observe("nominal-before-mutation", box, Box[r.I32])
object.__setattr__(box, "value", "tampered")
observe("nominal-after-mutation", box, Box[r.I32])
observe("depth-64", 123, int, depth=64)
observe("depth-65", 123, int, depth=65)
node = Node(child=None)
object.__setattr__(node, "child", node)
observe("cycle", node, Node)
observe("off-f32", r.CottList(values=(1.1,)), r.CottList[r.F32], normalize=True)
observe("off-i32-not-validation", True, r.I32, normalize=True)
assert "rejected" in observations["nominal-after-mutation"]
assert "rejected" in observations["cycle"]
assert "rejected" in observations["depth-65"]
assert "accepted" in observations["depth-64"]
assert observations["union-bad"]["phase"] == "validation"
assert observations["off-f32"]["accepted"]["items"][0]["float64_bits"] == struct.pack("!d", struct.unpack("!f", struct.pack("!f", 1.1))[0]).hex()
print(json.dumps(observations, sort_keys=True, ensure_ascii=True, separators=(",", ":")))
