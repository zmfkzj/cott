import contextlib
import http.server
import asyncio
import collections.abc
import dataclasses
import importlib
import inspect
import itertools
import json
import math
import os
import pathlib
import struct
import threading
import urllib.parse
import sys
import types
import typing

import cott_runtime

_SCENARIO_FIXTURES = {}

OMIT = object()


def local(symbol):
    return symbol.rsplit(".", 1)[-1]

def variant(symbol):
    enumeration, name = symbol.rsplit(".", 2)[-2:]
    return f"{enumeration}_{name}"


def unique(values):
    result = []
    seen = set()
    for value in values:
        key = (type(value), repr(value))
        if key not in seen:
            seen.add(key)
            result.append(value)
    return result


def substitute(annotation, substitutions):
    if isinstance(annotation, typing.TypeVar):
        return substitutions.get(annotation, annotation)
    origin = typing.get_origin(annotation)
    if origin is None:
        return annotation
    args = typing.get_args(annotation)
    replaced = tuple(substitute(arg, substitutions) for arg in args)
    if replaced == args:
        return annotation
    try:
        if origin is typing.Annotated:
            return typing.Annotated[replaced[0], *args[1:]]
        if origin in (typing.Union, types.UnionType):
            return typing.Union[replaced]
        return origin[replaced[0] if len(replaced) == 1 else replaced]
    except (TypeError, AttributeError):
        return annotation


def dyn_name(annotation):
    args = typing.get_args(annotation)
    trait = args[0] if args else None
    return f"Dyn[{getattr(trait, '__name__', repr(trait))}]"


def non_generatable(annotation, substitutions=None):
    annotation = substitute(annotation, substitutions or {})
    if typing.get_origin(annotation) is cott_runtime.Dyn:
        return f"{dyn_name(annotation)} without a compiler-owned initialized concrete case"
    if annotation is typing.Any:
        return "Any"
    if annotation is object:
        return "Unknown"
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)
    target = origin or annotation
    target_name = getattr(target, "__name__", "")
    if inspect.isclass(target) and dataclasses.is_dataclass(target):
        return None
    if target in (list, set, dict) or target_name in {"CottList", "CottSet", "FrozenMap"}:
        return None
    if target_name == "CottArray" and fixed_length(args[1] if len(args) == 2 else None) == 0:
        return None
    if origin is typing.Annotated:
        if any(type(value).__name__ == "CottExternal" for value in args[1:]):
            return "external type"
        return non_generatable(args[0], substitutions)
    if annotation is collections.abc.Iterator or origin is collections.abc.Iterator:
        return "Iterator"
    if annotation is collections.abc.Generator or origin is collections.abc.Generator:
        return "Generator"
    if origin is type:
        return "Factory"
    if origin in (typing.Union, types.UnionType):
        reasons = [non_generatable(value, substitutions) for value in args]
        return next(iter(reasons), None) if reasons and all(reasons) else None
    return next(
        (reason for value in args if (reason := non_generatable(value, substitutions))),
        None,
    )


def input_candidate_reason(function, strategy=None, dyn_values=()):
    hints = callable_hints(function)
    signature = inspect.signature(function)
    strategy = strategy or {}
    for parameter in signature.parameters.values():
        annotation = hints.get(parameter.name, parameter.annotation)
        if typing.get_origin(annotation) is cott_runtime.Dyn and dyn_values:
            continue
        reason = non_generatable(annotation)
        if reason is not None:
            return (
                f"input parameter `{parameter.name}` is {reason} and is not "
                "automatically generated"
            )
        reason = candidate_failure_reason(
            annotation,
            container_length_limit=strategy.get("container_length_limit", 3),
            json_depth_limit=strategy.get("json_depth_limit", 4),
            node_limit=strategy.get("node_limit", 64),
        )
        if reason is not None:
            return f"input parameter `{parameter.name}` {reason}"
    return None

def candidate_failure_reason(
    annotation,
    substitutions=None,
    depth=0,
    container_length_limit=3,
    json_depth_limit=4,
    node_limit=64,
    active_nominals=(),
):
    substitutions = substitutions or {}
    annotation = substitute(annotation, substitutions)
    if depth >= json_depth_limit:
        return f"candidate depth limit ({json_depth_limit}) exhausted"
    if node_limit < 1:
        return f"candidate node limit ({node_limit}) exhausted"
    reason = non_generatable(annotation, substitutions)
    if reason is not None:
        return reason
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)
    if origin is typing.Annotated:
        return candidate_failure_reason(
            args[0], substitutions, depth, container_length_limit, json_depth_limit,
            node_limit, active_nominals,
        )
    if origin in (typing.Union, types.UnionType):
        reasons = [
            candidate_failure_reason(
                argument, substitutions, depth + 1, container_length_limit,
                json_depth_limit, node_limit, active_nominals,
            )
            for argument in args
        ]
        return next(iter(reasons), None) if reasons and all(reasons) else None
    if annotation in (type(None), bool, int, float, str, bytes, cott_runtime.Unit, pathlib.Path):
        return None
    target = origin or annotation
    target_name = getattr(target, "__name__", "")
    if target_name == "CottBuffer":
        length = fixed_length(args[0] if args else None)
        return None if length is not None and length <= container_length_limit else "fixed buffer length exceeds candidate container limit"
    if target_name == "CottArray":
        length = fixed_length(args[1] if len(args) == 2 else None)
        if length is None or length > container_length_limit:
            return "fixed array length exceeds candidate container limit"
        return None if length == 0 else candidate_failure_reason(
            args[0], substitutions, depth + 1, container_length_limit, json_depth_limit,
            (node_limit - 1) // length, active_nominals,
        )
    if target is tuple and len(args) == 2 and args[1] is Ellipsis:
        return None
    if target is tuple:
        return next(
            (
                reason
                for item_type in args
                if (reason := candidate_failure_reason(
                    item_type, substitutions, depth + 1, container_length_limit,
                    json_depth_limit, (node_limit - 1) // max(len(args), 1), active_nominals,
                ))
            ),
            None,
        )
    if target in (list, set, dict) or target_name in {"CottList", "CottSet", "FrozenMap"}:
        return None
    if inspect.isclass(target) and dataclasses.is_dataclass(target):
        key = (target, tuple(map(repr, args)))
        if key in active_nominals:
            return f"required recursive value `{target.__name__}` has no finite candidate"
        parameters = getattr(target, "__parameters__", ())
        nested = dict(substitutions)
        nested.update(zip(parameters, args))
        try:
            hints = typing.get_type_hints(target, include_extras=True)
        except Exception:
            hints = {field.name: field.type for field in dataclasses.fields(target)}
        fields = dataclasses.fields(target)
        child_limit = (node_limit - 1) // max(len(fields), 1)
        if fields and child_limit < 1:
            return f"candidate node limit ({node_limit}) exhausted"
        return next(
            (
                reason
                for field in fields
                if (reason := candidate_failure_reason(
                    hints.get(field.name, field.type), nested, depth + 1,
                    container_length_limit, json_depth_limit, child_limit,
                    (*active_nominals, key),
                ))
            ),
            None,
        )
    return "unsupported input type"

def candidates(
    annotation,
    depth=0,
    substitutions=None,
    container_length_limit=3,
    json_depth_limit=4,
    node_limit=64,
    dyn_values=(),
    active_nominals=(),
):
    substitutions = substitutions or {}
    annotation = substitute(annotation, substitutions)
    if depth >= json_depth_limit or node_limit < 1:
        return []
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)
    if origin is cott_runtime.Dyn:
        trait = args[0] if args else None
        trait_origin = typing.get_origin(trait) or trait
        return unique(
            cott_runtime.Dyn(value=value, trait=trait)
            for value in dyn_values
            if trait_origin in type(value).__dict__.get("_cott_traits", ())
            and trait in type(value).__dict__.get("_cott_trait_specs", ())
        )
    target = origin or annotation
    target_name = getattr(target, "__name__", "")
    if target in (list, set, dict) or target_name in {
        "CottList",
        "CottSet",
        "FrozenMap",
    }:
        child_limit = (node_limit - 1) // max(container_length_limit, 1)
        element_values = (
            candidates(
                args[0], depth + 1, substitutions, container_length_limit, json_depth_limit,
                child_limit, dyn_values, active_nominals,
            )
            if args
            else []
        )
        if target in (dict,) or target_name == "FrozenMap":
            key_values = element_values[:min(1, container_length_limit)]
            value_values = (
                candidates(
                    args[1], depth + 1, substitutions, container_length_limit, json_depth_limit,
                    child_limit, dyn_values, active_nominals,
                )
                if len(args) > 1
                else []
            )
            value_values = value_values[:min(1, container_length_limit)]
            raw = [{}]
            if key_values and value_values:
                raw.append({key_values[0]: value_values[0]})
            if target is dict:
                return raw
            return [target(values=value) for value in raw]
        raw = [
            [],
            element_values[:min(1, container_length_limit)],
            element_values[:container_length_limit],
        ]
        if target is list:
            return raw
        if target is set:
            return [set(value) for value in raw]
        if target is tuple:
            return [tuple(value) for value in raw]
        return [target(values=value) for value in raw]
    if non_generatable(annotation, substitutions) is not None:
        return []
    if origin is typing.Annotated:
        metadata = args[1:]
        integer = next(
            (value for value in metadata if isinstance(value, cott_runtime.CottInt)),
            None,
        )
        if integer is not None:
            minimum = -(1 << (integer.bits - 1)) if integer.sign == "signed" else 0
            maximum = (
                (1 << (integer.bits - 1)) - 1
                if integer.sign == "signed"
                else (1 << integer.bits) - 1
            )
            return unique(
                [minimum, minimum + 1, -1, 0, 1, maximum - 1, maximum]
            )
        floating = next(
            (value for value in metadata if isinstance(value, cott_runtime.CottFloat)),
            None,
        )
        if floating is not None:
            return [-1.0, -0.0, 0.0, 0.5, 1.0]
        return candidates(
            args[0], depth, substitutions, container_length_limit, json_depth_limit,
            node_limit, dyn_values, active_nominals,
        )
    if origin in (typing.Union, types.UnionType):
        return unique(
            value
            for argument in args
            for value in candidates(
                argument, depth + 1, substitutions, container_length_limit, json_depth_limit,
                node_limit, dyn_values, active_nominals,
            )
        )
    if annotation is type(None):
        return [None]
    if annotation is bool:
        return [False, True]
    if annotation is int:
        return [-1, 0, 1, 2, 255]
    if annotation is float:
        return [-1.0, 0.0, 0.5, 1.0, 2.0]
    if annotation is str:
        return ["", "x"]
    if annotation is bytes:
        return [b"", b"x"]
    if annotation is cott_runtime.Unit:
        return [cott_runtime.UNIT]
    if annotation is pathlib.Path:
        return [pathlib.Path("/tmp/cott-contract-path")]
    if target_name == "CottBuffer":
        length = fixed_length(args[0] if args else None)
        if length is None or length > container_length_limit:
            return []
        return unique([
            target(data=b"\x00" * length),
            target(data=b"\xff" * length),
        ])
    if target_name == "CottArray":
        length = fixed_length(args[1] if len(args) == 2 else None)
        if length is None or length > container_length_limit:
            return []
        if length == 0:
            return [target(values=())]
        element_values = candidates(
            args[0], depth + 1, substitutions, container_length_limit, json_depth_limit,
            (node_limit - 1) // max(length, 1), dyn_values, active_nominals,
        ) if args else []
        if length and not element_values:
            return []
        return [
            target(values=() if length == 0 else (value,) * length)
            for value in unique(element_values[:container_length_limit])
        ]
    if target is tuple and len(args) == 2 and args[1] is Ellipsis:
        values = candidates(
            args[0], depth + 1, substitutions, container_length_limit, json_depth_limit,
            (node_limit - 1) // max(container_length_limit, 1), dyn_values, active_nominals,
        )[:container_length_limit]
        return unique([(), *((value,) for value in values), tuple(values)])
    if target is tuple:
        child_limit = (node_limit - 1) // max(len(args), 1)
        pools = [
            candidates(
                item_type, depth + 1, substitutions, container_length_limit, json_depth_limit,
                child_limit, dyn_values, active_nominals,
            )[:container_length_limit]
            for item_type in args
        ]
        if any(not pool for pool in pools):
            return []
        return [tuple(items) for items in itertools.islice(itertools.product(*pools), 16)]

    if target is cott_runtime.Opaque:
        return []
    if inspect.isclass(target) and dataclasses.is_dataclass(target):
        key = (target, tuple(map(repr, args)))
        if key in active_nominals:
            return []
        parameters = getattr(target, "__parameters__", ())
        nested = dict(substitutions)
        nested.update(zip(parameters, args))
        try:
            hints = typing.get_type_hints(target, include_extras=True)
        except Exception:
            hints = {field.name: field.type for field in dataclasses.fields(target)}
        fields = dataclasses.fields(target)
        child_limit = (node_limit - 1) // max(len(fields), 1)
        if fields and child_limit < 1:
            return []
        pools = []
        for field in fields:
            pool = candidates(
                hints.get(field.name, field.type),
                depth + 1,
                nested,
                container_length_limit,
                json_depth_limit,
                child_limit,
                dyn_values,
                (*active_nominals, key),
            )
            if not pool:
                return []
            pools.append(pool[:5])
        values = []
        for combination in itertools.islice(itertools.product(*pools), 16):
            try:
                values.append(target(**dict(zip((field.name for field in fields), combination))))
            except (Exception, SystemExit):
                pass
        return unique(values)
    return []


def fixed_length(annotation):
    if typing.get_origin(annotation) is not typing.Literal:
        return None
    values = typing.get_args(annotation)
    return values[0] if len(values) == 1 and type(values[0]) is int and values[0] >= 0 else None


def decode_json(value):
    if value is None:
        return cott_runtime.JsonNull()
    if type(value) is bool:
        return cott_runtime.JsonBoolean(value=value)
    if type(value) is int:
        return cott_runtime.JsonInteger(value=value)
    if type(value) is float:
        return cott_runtime.JsonFloat(value=value)
    if type(value) is str:
        return cott_runtime.JsonString(value=value)
    if type(value) is list:
        return cott_runtime.JsonArray(
            value=cott_runtime.CottList(values=(decode_json(item) for item in value))
        )
    return cott_runtime.JsonObject(
        value=cott_runtime.FrozenMap(
            values={key: decode_json(item) for key, item in value.items()}
        )
    )


def decode_value(value, module):
    kind = value["kind"]
    if kind == "bool":
        return value["value"]
    if kind == "integer":
        return int(value["value"])
    if kind == "f32":
        return struct.unpack("!f", bytes.fromhex(value["bits"]))[0]
    if kind == "f64":
        return struct.unpack("!d", bytes.fromhex(value["bits"]))[0]
    if kind == "string":
        return value["value"]
    if kind == "bytes":
        return bytes.fromhex(value["value"])
    if kind == "unit":
        return cott_runtime.UNIT
    if kind in ("list", "set"):
        items = [decode_value(item, module) for item in value["items"]]
        cls = cott_runtime.CottList if kind == "list" else cott_runtime.CottSet
        return cls(values=items)
    if kind == "map":
        return cott_runtime.FrozenMap(values={
            decode_value(key, module): decode_value(item, module)
            for key, item in value["entries"]
        })
    if kind == "tuple":
        return tuple(decode_value(item, module) for item in value["items"])
    if kind == "array":
        return cott_runtime.CottArray(
            values=(decode_value(item, module) for item in value["items"])
        )
    if kind == "buffer":
        return cott_runtime.CottBuffer(data=bytes.fromhex(value["hex"]))
    if kind == "option":
        return (
            cott_runtime.Some(value=decode_value(value["value"], module))
            if value["value"] is not None
            else cott_runtime.Nothing()
        )
    if kind == "result":
        decoded = decode_value(value["value"], module)
        return cott_runtime.Ok(value=decoded) if value["ok"] else cott_runtime.Err(error=decoded)
    if kind == "named":
        target = getattr(module, local(value["symbol"]))
        return target(**{
            field["name"]: decode_value(field["value"], module) for field in value["fields"]
        })
    if kind == "enum":
        variant_type = getattr(module, variant(value["variant"]))
        decoded = [decode_value(item, module) for item in value["fields"]]
        return variant_type(**{
            field.name: item for field, item in zip(dataclasses.fields(variant_type), decoded)
        })
    if kind == "json":
        return decode_json(value["value"])
    raise ValueError(f"unsupported canonical value {kind}")


def resolve_symbol(symbol, module):
    name = local(symbol)
    if hasattr(module, name):
        return getattr(module, name)
    if symbol.count(".") >= 2:
        variant_name = variant(symbol)
        if hasattr(module, variant_name):
            return getattr(module, variant_name)
    return getattr(cott_runtime, name)


def normalize_expression(expression, value):
    type_node = expression["type"]
    if type_node.get("kind") == "primitive" and type_node.get("name") == "f32":
        return cott_runtime._cott_normalize_f32(value)
    return value


def evaluate(expression, environment, module, receiver=None, result=None, old=None):
    kind = expression["kind"]
    if kind == "literal":
        return decode_value(expression["value"], module)
    if kind in ("parameter_ref", "binding_ref"):
        return environment[local(expression["symbol"])]
    if kind == "constant_ref":
        return resolve_symbol(expression["symbol"], module)
    if kind == "fixture_path":
        return _SCENARIO_FIXTURES[expression["fixture"]]["path"](expression["path"])
    if kind == "fixture_url":
        return _SCENARIO_FIXTURES[expression["fixture"]]["url"](expression["path"])
    if kind == "enum_singleton_ref":
        return getattr(module, variant(expression["symbol"]))()
    if kind == "self_ref":
        return receiver
    if kind == "result_ref":
        return result
    if kind == "old_state_field":
        return old[local(expression["field"])]
    if kind == "field":
        return getattr(evaluate(expression["base"], environment, module, receiver, result, old), expression["name"])
    if kind == "len":
        return len(evaluate(expression["value"], environment, module, receiver, result, old))
    if kind == "unary":
        value = evaluate(expression["operand"], environment, module, receiver, result, old)
        return normalize_expression(
            expression,
            {
                "not": lambda: not value,
                "plus": lambda: +value,
                "minus": lambda: -value,
            }[expression["op"]](),
        )
    if kind == "binary":
        left = evaluate(expression["left"], environment, module, receiver, result, old)
        if expression["op"] == "or" and left:
            return True
        if expression["op"] == "and" and not left:
            return False
        right = evaluate(expression["right"], environment, module, receiver, result, old)
        value = {
            "or": lambda: bool(right),
            "and": lambda: bool(right),
            "add": lambda: left + right,
            "subtract": lambda: left - right,
            "multiply": lambda: left * right,
            "divide": lambda: left / right,
            "remainder": lambda: cott_runtime._cott_euclidean_mod(left, right),
        }[expression["op"]]()
        return normalize_expression(expression, value)
    if kind == "comparison_chain":
        operations = {
            "equal": lambda a, b: a == b,
            "not_equal": lambda a, b: a != b,
            "less": lambda a, b: a < b,
            "less_equal": lambda a, b: a <= b,
            "greater": lambda a, b: a > b,
            "greater_equal": lambda a, b: a >= b,
        }
        operands = iter(expression["operands"])
        left = evaluate(next(operands), environment, module, receiver, result, old)
        for operator, operand in zip(expression["operators"], operands):
            right = evaluate(operand, environment, module, receiver, result, old)
            if not operations[operator](left, right):
                return False
            left = right
        return True
    raise ValueError(f"unsupported canonical expression {kind}")


def match_pattern(pattern, value, environment, module):
    kind = pattern["kind"]
    if kind == "wildcard":
        return True
    if kind == "binding":
        environment[local(pattern.get("name") or pattern["symbol"])] = value
        return True
    if kind in ("variant", "result_ok", "result_err", "option_some", "option_none", "enum"):
        variants = {
            "result_ok": cott_runtime.Ok,
            "result_err": cott_runtime.Err,
            "option_some": cott_runtime.Some,
            "option_none": cott_runtime.Nothing,
        }
        variant = variants.get(kind) or resolve_symbol(pattern["symbol"], module)
        if type(value) is not variant:
            return False
        for index, nested in enumerate(pattern.get("arguments", ())):
            if variant in (cott_runtime.Ok, cott_runtime.Some):
                field_value = value.value
            elif variant is cott_runtime.Err:
                field_value = value.error
            else:
                field_value = getattr(value, dataclasses.fields(type(value))[index].name)
            if not match_pattern(nested, field_value, environment, module):
                return False
        return True
    raise ValueError(f"unsupported canonical pattern {kind}")


def guard_environment(clause, environment, module, receiver=None, result=None, old=None):
    scoped = dict(environment)
    guard = clause.get("guard")
    if guard is None:
        return True, scoped
    value = evaluate(guard["scrutinee"], scoped, module, receiver, result, old)
    return match_pattern(guard["pattern"], value, scoped, module), scoped

def requires_holds(clause, environment, module, receiver=None, result=None, old=None):
    matched, scoped = guard_environment(clause, environment, module, receiver, result, old)
    return not matched or evaluate(clause["expression"], scoped, module, receiver, result, old)


def condition_matches(clause, environment, module, receiver=None, result=None, old=None):
    matched, scoped = guard_environment(clause, environment, module, receiver, result, old)
    return matched and (
        clause.get("when") is None
        or evaluate(clause["when"], scoped, module, receiver, result, old)
    )


def checked_clause_environment(clause, environment, module, receiver=None, result=None, old=None):
    return guard_environment(clause, environment, module, receiver, result, old)



def callable_hints(function):
    target = function.__init__ if inspect.isclass(function) else function
    return typing.get_type_hints(target, include_extras=True)


def validate_candidate(value, annotation):
    args = typing.get_args(annotation)
    if typing.get_origin(annotation) is tuple and len(args) == 2 and args[1] is Ellipsis and type(value) is tuple:
        return tuple(cott_runtime._cott_validate_abi(item, args[0]) for item in value)
    return cott_runtime._cott_validate_abi(value, annotation)


def invoke_cases(function, strategy=None, dyn_values=()):
    hints = callable_hints(function)
    signature = inspect.signature(function)
    strategy = strategy or {}
    candidate_limit = strategy.get("candidate_limit", 64)
    node_limit = strategy.get("node_limit", 64)
    container_length_limit = strategy.get("container_length_limit", 3)
    json_depth_limit = strategy.get("json_depth_limit", 4)
    pools = []
    for parameter in signature.parameters.values():
        annotation = hints.get(parameter.name, parameter.annotation)
        pool = (
            candidates(
                annotation,
                container_length_limit=container_length_limit,
                json_depth_limit=json_depth_limit,
                node_limit=node_limit,
                dyn_values=dyn_values,
            )
            if annotation is not inspect.Parameter.empty
            else []
        )
        if parameter.default is not inspect.Parameter.empty:
            pool = [OMIT, *pool]
        if parameter.kind is inspect.Parameter.VAR_POSITIONAL:
            pool = [(), *((value,) for value in pool[:3])]
        elif parameter.kind is inspect.Parameter.VAR_KEYWORD:
            pool = [{}, *(({"value": value} for value in pool[:3]))]
        if not pool:
            return []
        pools.append(pool)
    cases = []
    for combination in itertools.islice(itertools.product(*pools), candidate_limit):
        args, kwargs, environment = [], {}, {}
        valid = True
        for parameter, value in zip(signature.parameters.values(), combination):
            if value is OMIT:
                continue
            try:
                annotation = hints.get(parameter.name, parameter.annotation)
                if parameter.kind is inspect.Parameter.VAR_POSITIONAL:
                    normalized = tuple(
                        validate_candidate(item, annotation) for item in value
                    )
                    args.extend(normalized)
                    environment[parameter.name] = normalized
                elif parameter.kind is inspect.Parameter.VAR_KEYWORD:
                    normalized = {
                        key: validate_candidate(item, annotation)
                        for key, item in value.items()
                    }
                    kwargs.update(normalized)
                    environment[parameter.name] = normalized
                else:
                    normalized = validate_candidate(value, annotation)
                    environment[parameter.name] = normalized
                    if parameter.kind in (inspect.Parameter.POSITIONAL_ONLY, inspect.Parameter.POSITIONAL_OR_KEYWORD):
                        args.append(normalized)
                    else:
                        kwargs[parameter.name] = normalized
            except cott_runtime.CottContractViolation:
                valid = False
                break
        if valid:
            cases.append((args, kwargs, environment))
    return cases


def clause_key(clause):
    return f"{clause['kind']}:{clause['clause_id']}"


def impl_clauses(contract, invariants=(), modifies=(), span=None):
    clauses = [
        dict(clause, kind=kind)
        for kind, name in (("ensures", "ensures"), ("error", "errors"), ("requires", "requires"))
        for clause in contract.get(name, ())
    ]
    clauses.extend(
        dict(clause, kind="invariant")
        for clause in invariants
    )
    clauses.extend(
        {"kind": "modifies", "clause_id": field, "fields": list(modifies), "span": span}
        for field in modifies
    )
    return clauses


def concretize(value, substitutions):
    if isinstance(value, dict):
        if value.get("kind") in ("type_parameter", "parameter") and value.get("name") in substitutions:
            return substitutions[value["name"]]
        return {key: concretize(item, substitutions) for key, item in value.items()}
    if isinstance(value, list):
        return [concretize(item, substitutions) for item in value]
    return value


def resolved_impl_methods(module_values, implementation):
    resolved = []
    by_name = {}
    for slot in implementation["selected_methods"]:
        trait_method = slot["trait_method"]
        trait_name, method_name = trait_method.rsplit(".", 1)
        selected = slot["selected"]
        origin = selected.get("origin", selected.get("kind"))
        if origin == "explicit" and local(selected["function"]["symbol"]) != method_name:
            raise AssertionError(f"{implementation['name']}.{method_name}: selected function does not match trait method")
        if origin == "explicit":
            source = next(
                (
                    method for method in implementation["methods"]
                    if local(method["name"]) == method_name
                ),
                None,
            )
            if source is None:
                raise AssertionError(f"{implementation['name']}.{method_name}: missing explicit method")
            method = dict(source)
        elif origin in ("default", "specialization"):
            trait = next(
                (
                    declaration
                    for module_value in module_values
                    for declaration in module_value["declarations"]
                    if declaration["kind"] == "trait" and declaration["name"] == trait_name
                ),
                None,
            )
            if trait is None:
                raise AssertionError(f"{implementation['name']}.{method_name}: missing trait declaration")
            trait_reference = slot.get("trait_ref") or next(
                (
                    reference for reference in implementation["traits"]
                    if reference["kind"] == "named" and reference["name"] == trait_name
                ),
                None,
            )
            if trait_reference is None:
                if trait["generics"]:
                    raise AssertionError(f"{implementation['name']}.{method_name}: invalid trait instantiation")
                substitutions = {}
            elif len(trait["generics"]) != len(trait_reference["args"]):
                raise AssertionError(f"{implementation['name']}.{method_name}: invalid trait instantiation")
            else:
                substitutions = {
                    generic["name"]: argument["type"] if argument["kind"] == "type" else argument["value"]
                    for generic, argument in zip(trait["generics"], trait_reference["args"])
                }
            source = next(
                (method for method in trait["methods"] if local(method["name"]) == method_name),
                None,
            )
            if source is None:
                raise AssertionError(f"{implementation['name']}.{method_name}: missing trait method")
            method = concretize(source, substitutions)
            clauses = method["contract"]["clauses"]
            method["contracts"] = {
                name: [clause for clause in clauses if clause["kind"] == kind]
                for kind, name in (("requires", "requires"), ("ensures", "ensures"), ("error", "errors"))
            }
            method["effects"] = method["contract"]["effects"]
            method["modifies"] = []
        else:
            raise AssertionError(f"{implementation['name']}.{method_name}: unsupported selected implementation")
        method["name"] = method_name
        signature = (
            tuple(
                json.dumps(parameter["type"], sort_keys=True, separators=(",", ":"))
                for parameter in method["parameters"]
            ),
            json.dumps(method["return_type"], sort_keys=True, separators=(",", ":")),
        )
        previous = by_name.get(method_name)
        if previous is not None:
            if previous != (signature, selected):
                raise AssertionError(f"{implementation['name']}.{method_name}: duplicate concrete slot differs")
            continue
        by_name[method_name] = (signature, selected)
        resolved.append(method)
    return resolved


def unexecuted(clauses, strategy, effectful_reason, never_reason):
    observed = {clause_key(clause): 0 for clause in clauses}
    if strategy["classification"] == "pure":
        return observed, None, None
    grade = "trust declaration" if strategy["classification"] == "effectful" else "unobserved"
    return observed, grade, effectful_reason if grade == "trust declaration" else never_reason


def obligation_stats(strategy):
    return {
        obligation["clause_id"]: {
            "eligible_cases": 0,
            "applicable_cases": 0,
            "satisfied_cases": 0,
            "condition_false_cases": 0,
            "first_witness": None,
        }
        for obligation in strategy.get("obligations", ())
    }


def record_contract_observations(
    clauses, observed, stats, environment, module, case_id, *, receiver=None, result=None, old=None
):
    conditional_errors = [
        clause
        for clause in clauses
        if clause["kind"] == "error"
        and (clause.get("guard") is not None or clause.get("when") is not None)
        and condition_matches(clause, environment, module, receiver, result, old)
    ]
    first_conditional_error = min(
        enumerate(conditional_errors),
        key=lambda item: item[1].get("priority")
        if item[1].get("priority") is not None
        else item[0],
        default=(None, None),
    )[1]
    for clause in clauses:
        key = clause_key(clause)
        if clause["kind"] == "requires":
            observed[key] += 1
            continue
        if clause["kind"] == "ensures":
            matched, scoped = checked_clause_environment(
                clause, environment, module, receiver, result, old
            )
            stat = stats.get(key)
            if stat is not None:
                stat["eligible_cases"] += 1
            if not matched:
                if stat is not None:
                    stat["condition_false_cases"] += 1
                continue
            if stat is not None:
                stat["applicable_cases"] += 1
            if not evaluate(clause["expression"], scoped, module, receiver, result, old):
                raise AssertionError(f"ensures clause {key} failed independently")
            observed[key] += 1
            if stat is not None:
                stat["satisfied_cases"] += 1
                stat["first_witness"] = stat["first_witness"] or {"case_id": case_id}
            continue
        if clause["kind"] != "error":
            continue
        matches = (
            type(result) is cott_runtime.Err
            and type(result.error) is resolve_symbol(clause["variant"], module)
        )
        stat = stats.get(key)
        if clause.get("guard") is not None or clause.get("when") is not None:
            if stat is not None:
                stat["eligible_cases"] += 1
            if clause in conditional_errors:
                if stat is not None:
                    stat["applicable_cases"] += 1
                if clause is first_conditional_error:
                    if not matches:
                        raise AssertionError(f"conditional error clause {key} failed independently")
                    observed[key] += 1
                    if stat is not None:
                        stat["satisfied_cases"] += 1
                        stat["first_witness"] = stat["first_witness"] or {"case_id": case_id}
            elif stat is not None:
                stat["condition_false_cases"] += 1
        elif matches:
            observed[key] += 1


async def bounded(awaitable, symbol, action):
    task = asyncio.Task(awaitable, loop=asyncio.get_running_loop())
    try:
        done, pending = await asyncio.wait((task,), timeout=0.1)
    except asyncio.CancelledError:
        task.cancel()
        _, pending = await asyncio.wait((task,), timeout=0.1)
        if pending:
            print(f"{symbol}: cancellation-resistant {action}", file=sys.stderr, flush=True)
            os._exit(1)
        raise
    if not pending:
        return task.result()
    task.cancel()
    _, pending = await asyncio.wait(pending, timeout=0.1)
    if pending:
        print(f"{symbol}: cancellation-resistant {action}", file=sys.stderr, flush=True)
        os._exit(1)
    raise AssertionError(f"{symbol}: {action} timed out")


async def close_protocol(result, symbol):
    close = getattr(result, "aclose", None)
    if not callable(close):
        raise AssertionError(f"{symbol}: protocol result does not support aclose")
    await bounded(invoke_facade(close, (), {}, symbol, "async"), symbol, "protocol close")


async def observe_protocol(result, strategy, hints, symbol):
    kind = strategy["return_kind"]
    if kind == "value":
        return None
    if kind not in ("async_iterator", "async_generator"):
        raise AssertionError(f"{symbol}: unsupported return_kind `{kind}`")
    if not callable(getattr(result, "__anext__", None)):
        raise AssertionError(f"{symbol}: expected {kind} protocol result")
    if kind == "async_generator" and not callable(getattr(result, "asend", None)):
        raise AssertionError(f"{symbol}: expected async_generator protocol result")
    lifecycle = {
        "symbol": symbol,
        "lifecycle_limit": strategy["lifecycle_limit"],
        "lifecycle_steps": 0,
        "lifecycle_sent": False,
        "lifecycle_closed": False,
        "lifecycle_reason": None,
        "operations": [],
    }
    try:
        send_value = OMIT
        if kind == "async_generator":
            send = typing.get_args(hints["return"])
            send = send[1] if len(send) > 1 else type(None)
            values = candidates(
                send,
                container_length_limit=strategy["container_length_limit"],
                json_depth_limit=strategy["json_depth_limit"],
            )
            if values:
                send_value = values[0]
        for step in range(strategy["lifecycle_limit"]):
            sending = kind == "async_generator" and step and send_value is not OMIT
            operation = result.asend if sending else result.__anext__
            args = (send_value,) if sending else ()
            operation_name = "asend" if sending else "anext"
            if sending:
                lifecycle["lifecycle_sent"] = True
            try:
                await bounded(
                    invoke_facade(operation, args, {}, symbol, "async"),
                    symbol,
                    "protocol lifecycle step",
                )
            except StopAsyncIteration:
                lifecycle["operations"].append(
                    {"operation": operation_name, "outcome": "completed"}
                )
                lifecycle["lifecycle_reason"] = "protocol completed"
                break
            lifecycle["operations"].append(
                {"operation": operation_name, "outcome": "yielded"}
            )
            lifecycle["lifecycle_steps"] += 1
        else:
            lifecycle["lifecycle_reason"] = "observation limit reached"
    except asyncio.CancelledError:
        raise
    except cott_runtime.CottContractViolation as error:
        raise AssertionError(f"{symbol}: lazy protocol contract violation: {error}") from error
    finally:
        await close_protocol(result, symbol)
        lifecycle["operations"].append({"operation": "aclose", "outcome": "closed"})
        await close_protocol(result, symbol)
        lifecycle["operations"].append(
            {"operation": "aclose", "outcome": "already_closed"}
        )
        lifecycle["lifecycle_closed"] = True
    return lifecycle




async def invoke_facade(function, args, kwargs, symbol, callable_kind):
    loop = asyncio.get_running_loop()
    before = asyncio.all_tasks()
    created = []
    previous_factory = loop.get_task_factory()
    original_task = asyncio.Task

    def tracked_task(coroutine, *args, **kwargs):
        task = original_task(coroutine, *args, **kwargs)
        created.append(task)
        return task

    def task_factory(loop, coroutine, context=None):
        if previous_factory is None:
            task = (
                original_task(coroutine, loop=loop, context=context)
                if context is not None
                else original_task(coroutine, loop=loop)
            )
        elif context is None:
            task = previous_factory(loop, coroutine)
        else:
            task = previous_factory(loop, coroutine, context=context)
        created.append(task)
        return task

    asyncio.Task = tracked_task
    loop.set_task_factory(task_factory)
    try:
        result = function(*args, **kwargs)
        return await result if callable_kind == "async" else result
    finally:
        try:
            await asyncio.sleep(0)
        finally:
            loop.set_task_factory(previous_factory)
            asyncio.Task = original_task
        created = (set(created) | (asyncio.all_tasks() - before)) - before
        failures = []
        pending = []
        for task in created:
            if task.done():
                if task.cancelled():
                    failures.append("cancelled")
                elif exception := task.exception():
                    failures.append(type(exception).__name__)
            else:
                pending.append(task)
        leaked = len(pending)
        for task in pending:
            task.cancel()
        if pending:
            _, pending = await asyncio.wait(pending, timeout=0.1)
            if pending:
                print(
                    f"{symbol}: cancellation-resistant task leak",
                    file=sys.stderr,
                    flush=True,
                )
                os._exit(1)
        if failures or leaked:
            detail = (
                f"child task failed with {failures[0]}"
                if failures
                else f"leaked {leaked} task(s)"
            )
            raise AssertionError(f"{symbol}: {detail}")


async def run_function(module_value, declaration, strategy):
    symbol = declaration["name"]
    clauses = declaration["contract"]["clauses"]
    observed, grade, reason = unexecuted(
        clauses,
        strategy,
        "effectful function is not automatically executed",
        "Never-returning function is not automatically executed",
    )
    stats = obligation_stats(strategy)
    if grade is not None:
        return observed, grade, reason, None, stats
    callable_kind = strategy["callable_kind"]
    if callable_kind not in ("sync", "async"):
        raise AssertionError(f"{symbol}: unsupported callable_kind `{callable_kind}`")
    module = importlib.import_module(module_value["module"])
    function = getattr(module, local(symbol))
    if hasattr(module, "_cott_set_test_context"):
        module._cott_set_test_context(True)
    valid_cases = 0
    lifecycle = None
    hints = callable_hints(function)
    cases = invoke_cases(function, strategy)
    candidate_reason = input_candidate_reason(function, strategy) if not cases else None
    requirements = [clause for clause in clauses if clause["kind"] == "requires"]
    for args, kwargs, environment in cases:
        try:
            if not all(requires_holds(clause, environment, module) for clause in requirements):
                continue
        except Exception as error:
            raise AssertionError(f"{symbol}: independent requires evaluation failed: {error}") from error
        try:
            result = await invoke_facade(function, args, kwargs, symbol, callable_kind)
        except cott_runtime.CottContractViolation as error:
            raise AssertionError(f"{symbol}: facade contract violation for generated valid case: {error}") from error
        result = cott_runtime._cott_validate_abi(result, hints["return"])
        if lifecycle is None:
            lifecycle = await observe_protocol(result, strategy, hints, symbol)
        elif strategy["return_kind"] != "value":
            await close_protocol(result, symbol)
        record_contract_observations(
            clauses, observed, stats, environment, module, f"case:{valid_cases}", result=result
        )
        valid_cases += 1
    if valid_cases == 0:
        return observed, "unobserved", (
            candidate_reason
            or "no valid input candidate satisfied refinements and requires"
        ), lifecycle, stats
    return observed, "test observation", None, lifecycle, stats


def run_initializer(module, implementation, strategy):
    symbol = strategy["symbol"]
    facade = getattr(module, local(implementation["name"]))
    initializer = implementation.get("init") or {"contracts": {}, "parameters": []}
    clauses = impl_clauses(initializer.get("contracts", {}), implementation.get("invariants", ()))
    observed, grade, reason = unexecuted(
        clauses,
        strategy,
        "effectful initializer is not automatically executed",
        "Never-returning initializer is not automatically executed",
    )
    raw_cases = invoke_cases(facade, strategy)
    candidate_reason = input_candidate_reason(facade, strategy) if not raw_cases else None
    if grade is not None:
        return clauses, observed, grade, reason, raw_cases
    valid_cases = 0
    accepted = []
    requirements = [clause for clause in clauses if clause["kind"] == "requires"]
    for args, kwargs, environment in raw_cases:
        try:
            if not all(requires_holds(clause, environment, module) for clause in requirements):
                continue
        except Exception as error:
            raise AssertionError(f"{symbol}: independent requires evaluation failed: {error}") from error
        try:
            receiver = facade(*args, **kwargs)
        except cott_runtime.CottContractViolation as error:
            raise AssertionError(f"{symbol}: facade contract violation for generated valid case: {error}") from error
        valid_cases += 1
        accepted.append((args, kwargs, environment))
        for clause in clauses:
            clause_id = clause_key(clause)
            if clause["kind"] == "requires":
                observed[clause_id] += 1
            elif clause["kind"] in ("ensures", "invariant"):
                matched, clause_environment = checked_clause_environment(
                    clause, environment, module, receiver=receiver, result=receiver
                )
                if matched:
                    if not evaluate(
                        clause["expression"], clause_environment, module, receiver=receiver, result=receiver
                    ):
                        raise AssertionError(f"{symbol}: {clause['kind']} clause {clause_id} failed independently")
                    observed[clause_id] += 1
    if valid_cases == 0:
        return clauses, observed, "unobserved", (
            candidate_reason
            or "no valid input candidate satisfied refinements and requires"
        ), accepted
    return clauses, observed, "test observation", None, accepted


async def run_method(module, implementation, method, strategy, constructor_cases):
    symbol = strategy["symbol"]
    method_name = local(symbol)
    if strategy["callable_kind"] not in ("sync", "async"):
        raise AssertionError(f"{symbol}: unsupported callable_kind `{strategy['callable_kind']}`")
    facade = getattr(module, local(implementation["name"]))
    clauses = impl_clauses(
        method.get("contracts", {}),
        implementation.get("invariants", ()),
        method.get("modifies", ()),
        method.get("span"),
    )
    observed, grade, reason = unexecuted(
        clauses,
        strategy,
        "effectful method is not automatically executed",
        "Never-returning method is not automatically executed",
    )
    stats = obligation_stats(strategy)
    if grade is not None:
        return clauses, observed, grade, reason, None, stats
    if not constructor_cases:
        return clauses, observed, "unobserved", (
            input_candidate_reason(facade, strategy)
            or "no valid constructor candidate satisfied refinements and requires"
        ), None, stats
    probe = facade(*constructor_cases[0][0], **constructor_cases[0][1])
    bound_method = getattr(probe, method_name)
    cases = invoke_cases(bound_method, strategy, (probe,))
    candidate_reason = input_candidate_reason(bound_method, strategy, (probe,)) if not cases else None
    valid_cases = 0
    lifecycle = None
    requirements = [clause for clause in clauses if clause["kind"] == "requires"]
    state = [local(field["name"]) for field in implementation.get("state", ())]
    permitted = {local(field) for field in method.get("modifies", ())}
    permitted.update(local(transition["field"]) for transition in method.get("transitions", ()))
    for constructor, case in itertools.islice(
        itertools.product(constructor_cases, cases), strategy["candidate_limit"]
    ):
        args, kwargs, _ = constructor
        receiver = facade(*args, **kwargs)
        method_args, method_kwargs, environment = case
        try:
            if not all(
                requires_holds(clause, environment, module, receiver=receiver)
                for clause in requirements
            ):
                continue
        except Exception as error:
            raise AssertionError(f"{symbol}: independent requires evaluation failed: {error}") from error
        old = {field: getattr(receiver, field) for field in state}
        bound_method = getattr(receiver, method_name)
        hints = callable_hints(bound_method)
        try:
            result = await invoke_facade(
                bound_method, method_args, method_kwargs, symbol, strategy["callable_kind"]
            )
        except cott_runtime.CottContractViolation as error:
            raise AssertionError(f"{symbol}: facade contract violation for generated valid case: {error}") from error
        result = cott_runtime._cott_validate_abi(result, hints["return"])
        if lifecycle is None:
            lifecycle = await observe_protocol(result, strategy, hints, symbol)
        elif strategy["return_kind"] != "value":
            await close_protocol(result, symbol)
        record_contract_observations(
            clauses,
            observed,
            stats,
            environment,
            module,
            f"case:{valid_cases}",
            receiver=receiver,
            result=result,
            old=old,
        )
        for clause in clauses:
            key = clause_key(clause)
            if clause["kind"] == "modifies":
                for field in state:
                    if field not in permitted and getattr(receiver, field) is not old[field]:
                        raise AssertionError(f"{symbol}: modifies clause {key} failed independently")
                observed[key] += 1
            elif clause["kind"] == "invariant":
                matched, scoped = checked_clause_environment(
                    clause, environment, module, receiver, result, old
                )
                if matched:
                    if not evaluate(clause["expression"], scoped, module, receiver, result, old):
                        raise AssertionError(f"{symbol}: invariant clause {key} failed independently")
                    observed[key] += 1
        valid_cases += 1
    if valid_cases == 0:
        return clauses, observed, "unobserved", (
            candidate_reason
            or "no valid input candidate satisfied refinements and requires"
        ), lifecycle, stats
    return clauses, observed, "test observation", None, lifecycle, stats


def evidence(symbol, clauses, observed, grade, reason, request, stats=None):
    stats = stats or {}
    entries = []
    for clause in clauses:
        key = clause_key(clause)
        item = {
            "grade": grade if grade != "test observation" or observed[key] else "unobserved",
            "mode": request["runtime_validation"],
            "valid_cases": observed[key],
            "reason": None if observed[key] else reason or "no generated case exercised this conditional clause",
        }
        if key in stats:
            item.update(stats[key])
        entries.append({
            "symbol": symbol,
            "clause_id": key,
            "span": clause["span"],
            "evidence": [item],
        })
    return entries


def fixture_bytes(data, encoding="utf-8"):
    if data["kind"] == "bytes":
        return bytes.fromhex(data["value"])
    return data["value"].encode(encoding)


class FixtureHttpServer:
    def __init__(self, fixtures, limits):
        self.routes = {}
        self.requests = 0
        self.redirects = 0
        self.limits = limits
        for fixture in fixtures:
            if fixture["kind"] != "http":
                continue
            for route in fixture["routes"]:
                outcome = route["outcome"]
                if outcome["kind"] == "response":
                    encoding = outcome["encoding"]
                    try:
                        body = fixture_bytes(outcome["body"], encoding)
                    except (LookupError, UnicodeError) as error:
                        raise AssertionError("invalid HTTP fixture encoding") from error
                    if len(body) > limits["http_body_bytes"]:
                        raise AssertionError("HTTP fixture body exceeds configured limit")
                self.routes[route["path"]] = outcome
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def do_GET(self):
                outer.requests += 1
                if outer.requests > outer.limits["http_requests"]:
                    self.send_error(429)
                    return
                outcome = outer.routes.get(urllib.parse.urlsplit(self.path).path)
                if outcome is None:
                    self.send_error(404)
                    return
                kind = outcome["kind"]
                if kind == "disconnect":
                    self.connection.close()
                    return
                if kind == "delay":
                    threading.Event().wait(outcome["milliseconds"] / 1000)
                    self.send_response(204)
                    self.end_headers()
                    return
                if kind == "redirect":
                    outer.redirects += 1
                    if outer.redirects > outer.limits["http_redirects"]:
                        self.send_error(508)
                        return
                    self.send_response(outcome["status"])
                    self.send_header("Location", outcome["location"])
                    self.end_headers()
                    return
                encoding = outcome["encoding"]
                body = fixture_bytes(outcome["body"], encoding)
                self.send_response(outcome["status"])
                self.send_header("Content-Type", f"text/plain; charset={encoding}")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def start(self):
        self.thread.start()

    @property
    def url(self):
        return f"http://127.0.0.1:{self.server.server_port}"

    def close(self):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=0.1)


def audit_fixture_root(root, limits):
    files = 0
    size = 0
    for path in root.rglob("*"):
        if path.is_symlink():
            raise AssertionError("fixture filesystem contains a symlink")
        if path.is_file():
            files += 1
            size += path.stat().st_size
    if files > limits["filesystem_files"] or size > limits["filesystem_bytes"]:
        raise AssertionError("fixture filesystem exceeds configured limit")


def prepare_scenario_fixtures(scenario, root):
    root.mkdir(parents=True, exist_ok=False)
    fixtures = {}
    failures = {}
    clock = 0
    for fixture in scenario["fixtures"]:
        kind = fixture["kind"]
        if kind == "fs":
            for file in fixture["files"]:
                path = root.joinpath(*file["path"].split("/"))
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_bytes(fixture_bytes(file["data"]))
            fixtures[fixture["id"]] = {
                "path": lambda path: pathlib.Path(path),
                "url": None,
            }
        elif kind == "clock":
            clock = fixture["start_ms"]
        elif kind == "failure":
            failures[fixture["point"]] = {
                "occurrence": fixture["occurrence"],
                "error": fixture["error"],
            }
    audit_fixture_root(root, scenario["limits"])
    return fixtures, failures, clock


def scenario_facade(symbol):
    module_name = symbol.rsplit(".", 1)[0]
    module = importlib.import_module(module_name)
    if hasattr(module, "_cott_set_test_context"):
        module._cott_set_test_context(True)
    return getattr(module, local(symbol)), module


async def await_worker(worker, timeout, symbol):
    return await asyncio.wait_for(asyncio.shield(worker["task"]), timeout=timeout)


async def run_scenario(module_value, strategy, request):
    scenario = strategy["scenario"]
    if len(scenario["steps"]) > 64:
        raise AssertionError(f"{scenario['id']}: step limit exceeds 64")
    if scenario["lifecycle_limit"] > 64:
        raise AssertionError(f"{scenario['id']}: lifecycle limit exceeds 64")
    root_parent = pathlib.Path(request.get("fixture_root", os.environ.get("TMPDIR", ".")))
    root = root_parent / f"scenario-{len(request.get('strategies', ()))}-{scenario['id'].rsplit('.', 1)[-1]}"
    fixtures, failures, clock = prepare_scenario_fixtures(scenario, root)
    has_http = any(fixture["kind"] == "http" for fixture in scenario["fixtures"])
    server = FixtureHttpServer(scenario["fixtures"], scenario["limits"]) if has_http else None
    if server is not None:
        server.start()
    for fixture in scenario["fixtures"]:
        if fixture["kind"] == "http":
            fixtures[fixture["id"]] = {
                "path": None,
                "url": lambda path, base=server.url: f"{base}{path}",
            }
    activate = getattr(cott_runtime, "_cott_fixture_activate", None)
    token_factory = getattr(cott_runtime, "_cott_fixture_runner_token", None)
    transcript = getattr(cott_runtime, "_cott_fixture_transcript", None)
    if not all(callable(value) for value in (activate, token_factory, transcript)):
        if server is not None:
            server.close()
        __import__("shutil").rmtree(root, ignore_errors=True)
        raise AssertionError("fixture runtime adapters are unavailable")
    workers = {}
    values = {}
    trace = []
    assertions = []
    ticks = 0
    global _SCENARIO_FIXTURES
    try:
        with activate(
            token_factory(),
            root=root,
            http_url=server.url if server is not None else None,
            clock=clock,
            failures=failures,
            transcript_limit=scenario["limits"]["transcript_events"],
        ):
            _SCENARIO_FIXTURES = fixtures
            assertion_module = importlib.import_module(module_value["module"])
            for step in scenario["steps"]:
                step_id = step["step_id"]
                kind = step["kind"]
                if kind == "call":
                    function, module = scenario_facade(step["target"])
                    args = [evaluate(argument, values, module) for argument in step["arguments"]]
                    values[local(step["binding"])] = await invoke_facade(
                        function, args, {}, strategy["symbol"], step["callable_kind"]
                    )
                    trace.append({"event_id": f"step:{step_id}", "kind": "call"})
                elif kind == "spawn":
                    if len(workers) >= scenario["lifecycle_limit"]:
                        raise AssertionError(f"{scenario['id']}: worker limit exceeded")
                    function, module = scenario_facade(step["target"])
                    args = [evaluate(argument, values, module) for argument in step["arguments"]]
                    task = asyncio.create_task(function(*args))
                    workers[local(step["worker"])] = {"task": task, "cancelled": False, "awaited": False}
                    trace.append({"event_id": f"step:{step_id}", "kind": "spawn"})
                elif kind == "tick":
                    if ticks >= scenario["lifecycle_limit"]:
                        raise AssertionError(f"{scenario['id']}: lifecycle tick limit exceeded")
                    ticks += 1
                    await asyncio.sleep(0)
                    trace.append({"event_id": f"step:{step_id}", "kind": "tick"})
                elif kind == "cancel":
                    worker = workers.get(local(step["worker"]))
                    if worker is None or worker["awaited"] or worker["cancelled"] or worker["task"].done():
                        raise AssertionError(f"{scenario['id']}: terminal worker cancellation")
                    worker["task"].cancel()
                    worker["cancelled"] = True
                    trace.append({"event_id": f"step:{step_id}", "kind": "cancel"})
                elif kind == "await":
                    worker = workers.get(local(step["worker"]))
                    if worker is None or worker["awaited"]:
                        raise AssertionError(f"{scenario['id']}: terminal worker await")
                    worker["awaited"] = True
                    try:
                        result = await await_worker(
                            worker, scenario["limits"]["scenario_timeout_ms"] / 1000, strategy["symbol"]
                        )
                    except asyncio.CancelledError:
                        if not step["cancelled"]:
                            raise AssertionError(f"{scenario['id']}: worker was cancelled unexpectedly")
                    else:
                        if step["cancelled"]:
                            raise AssertionError(f"{scenario['id']}: expected cancelled worker")
                        values[local(step["result"])] = result
                    trace.append({"event_id": f"step:{step_id}", "kind": "await"})
                elif kind == "assert":
                    if not evaluate(step["expression"], values, assertion_module):
                        raise AssertionError(f"{scenario['id']}: assertion step:{step_id} failed")
                    assertions.append({
                        "assertion_id": f"assert:{step_id}",
                        "span": step["span"],
                        "grade": "test observation",
                    })
                    trace.append({"event_id": f"step:{step_id}", "kind": "assert"})
                else:
                    raise AssertionError(f"{scenario['id']}: unsupported scenario step `{kind}`")
            live = [worker["task"] for worker in workers.values() if not worker["awaited"]]
            if live:
                raise AssertionError(f"{scenario['id']}: leaked live workers")
            audit_fixture_root(root, scenario["limits"])
            events = [
                {"event_id": f"fixture:{index}", "kind": event["kind"]}
                for index, event in enumerate(transcript())
            ]
            return {
                "scenario_id": scenario["id"],
                "grade": "test observation",
                "trace": trace,
                "assertions": assertions,
                "fixtures": events,
            }
    finally:
        _SCENARIO_FIXTURES = {}
        for worker in workers.values():
            if not worker["task"].done():
                worker["task"].cancel()
        pending = [worker["task"] for worker in workers.values() if not worker["task"].done()]
        if pending:
            await asyncio.wait(pending, timeout=0.1)
        if server is not None:
            server.close()
        __import__("shutil").rmtree(root, ignore_errors=True)
async def main():
    request = json.load(__import__("sys").stdin)
    strategies = {strategy["symbol"]: strategy for strategy in request["strategies"]}
    contracts = []
    lifecycle = []
    scenarios = []
    for module_value in request["modules"]:
        for declaration in module_value["declarations"]:
            if declaration["kind"] != "scenario":
                continue
            strategy = strategies.get(declaration["name"])
            if strategy is not None and strategy.get("scenario") is not None:
                scenarios.append(await run_scenario(module_value, strategy, request))
    for module_value in request["modules"]:
        for declaration in module_value["declarations"]:
            if declaration["kind"] == "function":
                strategy = strategies.get(declaration["name"])
                if strategy is None:
                    continue
                observed, grade, reason, observation, stats = await run_function(module_value, declaration, strategy)
                contracts.extend(evidence(declaration["name"], declaration["contract"]["clauses"], observed, grade, reason, request, stats))
                if observation is not None:
                    lifecycle.append(observation)
            elif declaration["kind"] == "impl":
                init_symbol = f"{module_value['module']}.{local(declaration['name'])}.init"
                init_strategy = strategies.get(init_symbol)
                initializer = declaration.get("init") or {"contracts": {}, "parameters": []}
                init_clauses = impl_clauses(initializer.get("contracts", {}), declaration.get("invariants", ()))
                method_strategies = []
                for method in resolved_impl_methods(request["modules"], declaration):
                    symbol = f"{module_value['module']}.{local(declaration['name'])}.{method['name']}"
                    strategy = strategies.get(symbol)
                    if strategy is not None:
                        clauses = impl_clauses(
                            method.get("contracts", {}),
                            declaration.get("invariants", ()),
                            method.get("modifies", ()),
                            method.get("span"),
                        )
                        method_strategies.append((method, symbol, strategy, clauses))
                pure_method_needs_execution = any(
                    strategy["classification"] == "pure"
                    and (bool(clauses) or strategy["return_kind"] != "value")
                    for _, _, strategy, clauses in method_strategies
                )
                needs_execution = pure_method_needs_execution or (
                    not method_strategies
                    and init_strategy is not None
                    and init_strategy["classification"] == "pure"
                    and bool(init_clauses)
                )
                if not needs_execution:
                    if init_strategy is not None:
                        observed, grade, reason = unexecuted(
                            init_clauses,
                            init_strategy,
                            "effectful initializer is not automatically executed",
                            "Never-returning initializer is not automatically executed",
                        )
                        if grade is None:
                            grade = "unobserved"
                            reason = "initializer selected only for an unexecuted effectful method"
                        contracts.extend(evidence(init_symbol, init_clauses, observed, grade, reason, request))
                    for _, symbol, strategy, clauses in method_strategies:
                        observed, grade, reason = unexecuted(
                            clauses,
                            strategy,
                            "effectful method is not automatically executed",
                            "Never-returning method is not automatically executed",
                        )
                        contracts.extend(evidence(symbol, clauses, observed, grade, reason, request, obligation_stats(strategy)))
                    continue
                module = importlib.import_module(module_value["module"])
                if hasattr(module, "_cott_set_test_context"):
                    module._cott_set_test_context(True)
                initializer_cases = invoke_cases(getattr(module, local(declaration["name"])))
                if init_strategy is not None:
                    clauses, observed, grade, reason, initializer_cases = run_initializer(module, declaration, init_strategy)
                    contracts.extend(evidence(init_symbol, clauses, observed, grade, reason, request))
                for method, symbol, strategy, _ in method_strategies:
                    clauses, observed, grade, reason, observation, stats = await run_method(
                        module, declaration, method, strategy, initializer_cases
                    )
                    contracts.extend(evidence(symbol, clauses, observed, grade, reason, request, stats))
                    if observation is not None:
                        lifecycle.append(observation)
    print(json.dumps({"contracts": contracts, "lifecycle": lifecycle, "scenarios": scenarios}, sort_keys=True, separators=(",", ":")))


asyncio.run(main())
