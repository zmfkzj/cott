import dataclasses
import importlib
import inspect
import itertools
import json
import math
import pathlib
import struct
import types
import typing

import cott_runtime

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


def candidates(annotation, depth=0, substitutions=None):
    substitutions = substitutions or {}
    annotation = substitute(annotation, substitutions)
    if isinstance(annotation, typing.TypeVar) or depth > 4:
        return []
    origin = typing.get_origin(annotation)
    args = typing.get_args(annotation)
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
        return candidates(args[0], depth, substitutions)
    if origin is typing.Literal:
        return list(args)
    if origin in (typing.Union, types.UnionType):
        return unique(
            value
            for argument in args
            for value in candidates(argument, depth + 1, substitutions)
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
    target = origin or annotation
    target_name = getattr(target, "__name__", "")
    if target in (list, set, tuple, dict) or target_name in {
        "CottList",
        "CottSet",
        "FrozenMap",
        "CottTuple2",
    }:
        element_values = candidates(args[0], depth + 1, substitutions) if args else []
        if target in (dict,) or target_name == "FrozenMap":
            key_values = element_values
            value_values = candidates(args[1], depth + 1, substitutions) if len(args) > 1 else []
            raw = [{}]
            if key_values and value_values:
                raw.append({key_values[0]: value_values[0]})
            if target is dict:
                return raw
            return [target(values=value) for value in raw]
        if target_name == "CottTuple2" or target is tuple and len(args) == 2:
            right = candidates(args[1], depth + 1, substitutions)
            return [target(first=a, second=b) for a in element_values[:2] for b in right[:2]]
        raw = [[], element_values[:1], element_values[:3]]
        if target is list:
            return raw
        if target is set:
            return [set(value) for value in raw]
        if target is tuple:
            return [tuple(value) for value in raw]
        return [target(values=value) for value in raw]
    if target is cott_runtime.Opaque:
        return []
    if inspect.isclass(target) and dataclasses.is_dataclass(target):
        parameters = getattr(target, "__parameters__", ())
        nested = dict(substitutions)
        nested.update(zip(parameters, args))
        try:
            hints = typing.get_type_hints(target, include_extras=True)
        except Exception:
            hints = {field.name: field.type for field in dataclasses.fields(target)}
        fields = dataclasses.fields(target)
        pools = []
        for field in fields:
            pool = candidates(hints.get(field.name, field.type), depth + 1, nested)
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
    if kind == "tuple2":
        return cott_runtime.CottTuple2(
            first=decode_value(value["first"], module),
            second=decode_value(value["second"], module),
        )
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
        environment[pattern["name"]] = value
        return True
    if kind == "variant":
        variant = resolve_symbol(pattern["symbol"], module)
        if type(value) is not variant:
            return False
        fields = dataclasses.fields(type(value))
        for index, nested in enumerate(pattern["arguments"]):
            if not match_pattern(nested, getattr(value, fields[index].name), environment, module):
                return False
        return True
    raise ValueError(f"unsupported canonical pattern {kind}")


def callable_hints(function):
    target = function.__init__ if inspect.isclass(function) else function
    return typing.get_type_hints(target, include_extras=True)


def invoke_cases(function):
    hints = callable_hints(function)
    signature = inspect.signature(function)
    pools = []
    for parameter in signature.parameters.values():
        annotation = hints.get(parameter.name, parameter.annotation)
        pool = candidates(annotation) if annotation is not inspect.Parameter.empty else []
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
    for combination in itertools.islice(itertools.product(*pools), 64):
        args, kwargs, environment = [], {}, {}
        valid = True
        for parameter, value in zip(signature.parameters.values(), combination):
            if value is OMIT:
                continue
            try:
                annotation = hints.get(parameter.name, parameter.annotation)
                if parameter.kind is inspect.Parameter.VAR_POSITIONAL:
                    normalized = tuple(
                        cott_runtime._cott_validate_abi(item, annotation) for item in value
                    )
                    args.extend(normalized)
                    environment[parameter.name] = normalized
                elif parameter.kind is inspect.Parameter.VAR_KEYWORD:
                    normalized = {
                        key: cott_runtime._cott_validate_abi(item, annotation)
                        for key, item in value.items()
                    }
                    kwargs.update(normalized)
                    environment[parameter.name] = normalized
                else:
                    normalized = cott_runtime._cott_validate_abi(value, annotation)
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
        {"kind": "invariant", "clause_id": clause["clause_id"], "expression": clause["expression"], "span": clause["span"]}
        for clause in invariants
    )
    clauses.extend(
        {"kind": "modifies", "clause_id": field, "fields": list(modifies), "span": span}
        for field in modifies
    )
    return clauses


def unexecuted(clauses, strategy, effectful_reason, never_reason):
    observed = {clause_key(clause): 0 for clause in clauses}
    if strategy["classification"] == "pure":
        return observed, None, None
    grade = "trust declaration" if strategy["classification"] == "effectful" else "unobserved"
    return observed, grade, effectful_reason if grade == "trust declaration" else never_reason


def run_function(module_value, declaration, strategy):
    symbol = declaration["name"]
    module = importlib.import_module(module_value["module"])
    function = getattr(module, local(symbol))
    if hasattr(module, "_cott_set_test_context"):
        module._cott_set_test_context(True)
    clauses = declaration["contract"]["clauses"]
    observed, grade, reason = unexecuted(
        clauses,
        strategy,
        "effectful function is not automatically executed",
        "Never-returning function is not automatically executed",
    )
    if grade is not None:
        return observed, grade, reason
    valid_cases = 0
    hints = callable_hints(function)
    for args, kwargs, environment in invoke_cases(function):
        requirements = [clause for clause in clauses if clause["kind"] == "requires"]
        try:
            if not all(evaluate(clause["expression"], environment, module) for clause in requirements):
                continue
        except Exception as error:
            raise AssertionError(f"{symbol}: independent requires evaluation failed: {error}") from error
        try:
            result = function(*args, **kwargs)
        except cott_runtime.CottContractViolation as error:
            raise AssertionError(f"{symbol}: facade contract violation for generated valid case: {error}") from error
        result = cott_runtime._cott_validate_abi(result, hints["return"])
        valid_cases += 1
        conditional_error = None
        for clause in clauses:
            if clause["kind"] == "error" and clause.get("when") is not None:
                if evaluate(clause["when"], environment, module, result=result):
                    conditional_error = clause
                    break
        for clause in clauses:
            clause_id = clause_key(clause)
            if clause["kind"] == "requires":
                observed[clause_id] += 1
            elif clause["kind"] == "ensures":
                clause_environment = dict(environment)
                pattern = clause.get("pattern")
                if pattern is None or match_pattern(pattern, result, clause_environment, module):
                    if not evaluate(clause["expression"], clause_environment, module, result=result):
                        raise AssertionError(f"{symbol}: ensures clause {clause_id} failed independently")
                    observed[clause_id] += 1
            elif clause["kind"] == "error":
                variant = resolve_symbol(clause["variant"], module)
                matches = type(result) is cott_runtime.Err and type(result.error) is variant
                if clause is conditional_error and not matches:
                    raise AssertionError(f"{symbol}: conditional error clause {clause_id} failed independently")
                if matches:
                    observed[clause_id] += 1
    if valid_cases == 0:
        return observed, "unobserved", "no valid input candidate satisfied refinements and requires"
    return observed, "test observation", None


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
    raw_cases = invoke_cases(facade)
    if grade is not None:
        return clauses, observed, grade, reason, raw_cases
    valid_cases = 0
    accepted = []
    requirements = [clause for clause in clauses if clause["kind"] == "requires"]
    for args, kwargs, environment in raw_cases:
        try:
            if not all(evaluate(clause["expression"], environment, module) for clause in requirements):
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
                if not evaluate(clause["expression"], environment, module, receiver=receiver, result=receiver):
                    raise AssertionError(f"{symbol}: {clause['kind']} clause {clause_id} failed independently")
                observed[clause_id] += 1
    if valid_cases == 0:
        return clauses, observed, "unobserved", "no valid input candidate satisfied refinements and requires", accepted
    return clauses, observed, "test observation", None, accepted


def run_method(module, implementation, strategy, constructor_cases):
    symbol = strategy["symbol"]
    method_name = local(symbol)
    facade = getattr(module, local(implementation["name"]))
    method = next(value for value in implementation["methods"] if value["name"] == method_name)
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
    if grade is not None:
        return clauses, observed, grade, reason
    if not constructor_cases:
        return clauses, observed, "unobserved", "no valid constructor candidate satisfied refinements and requires"
    probe = facade(*constructor_cases[0][0], **constructor_cases[0][1])
    cases = invoke_cases(getattr(probe, method_name))
    valid_cases = 0
    requirements = [clause for clause in clauses if clause["kind"] == "requires"]
    state = [local(field["name"]) for field in implementation.get("state", ())]
    permitted = {local(field) for field in method.get("modifies", ())}
    for constructor, case in itertools.islice(itertools.product(constructor_cases, cases), 64):
        args, kwargs, init_environment = constructor
        receiver = facade(*args, **kwargs)
        method_args, method_kwargs, environment = case
        try:
            if not all(evaluate(clause["expression"], environment, module, receiver=receiver) for clause in requirements):
                continue
        except Exception as error:
            raise AssertionError(f"{symbol}: independent requires evaluation failed: {error}") from error
        old = {field: getattr(receiver, field) for field in state}
        try:
            result = getattr(receiver, method_name)(*method_args, **method_kwargs)
        except cott_runtime.CottContractViolation as error:
            raise AssertionError(f"{symbol}: facade contract violation for generated valid case: {error}") from error
        result = cott_runtime._cott_validate_abi(result, callable_hints(getattr(receiver, method_name))["return"])
        valid_cases += 1
        conditional_error = next(
            (
                clause for clause in clauses
                if clause["kind"] == "error"
                and clause.get("when") is not None
                and evaluate(clause["when"], environment, module, receiver, result, old)
            ),
            None,
        )
        for clause in clauses:
            clause_id = clause_key(clause)
            if clause["kind"] == "requires":
                observed[clause_id] += 1
            elif clause["kind"] == "ensures":
                clause_environment = dict(environment)
                pattern = clause.get("pattern")
                if pattern is None or match_pattern(pattern, result, clause_environment, module):
                    if not evaluate(clause["expression"], clause_environment, module, receiver, result, old):
                        raise AssertionError(f"{symbol}: ensures clause {clause_id} failed independently")
                    observed[clause_id] += 1
            elif clause["kind"] == "error":
                matches = type(result) is cott_runtime.Err and type(result.error) is resolve_symbol(clause["variant"], module)
                if clause is conditional_error and not matches:
                    raise AssertionError(f"{symbol}: conditional error clause {clause_id} failed independently")
                if matches:
                    observed[clause_id] += 1
            elif clause["kind"] == "modifies":
                for field in state:
                    if field not in permitted and getattr(receiver, field) is not old[field]:
                        raise AssertionError(f"{symbol}: modifies clause {clause_id} failed independently")
                observed[clause_id] += 1
            elif clause["kind"] == "invariant":
                if not evaluate(clause["expression"], environment, module, receiver, result, old):
                    raise AssertionError(f"{symbol}: invariant clause {clause_id} failed independently")
                observed[clause_id] += 1
    if valid_cases == 0:
        return clauses, observed, "unobserved", "no valid input candidate satisfied refinements and requires"
    return clauses, observed, "test observation", None


def evidence(symbol, clauses, observed, grade, reason, request):
    return [{
        "symbol": symbol,
        "clause_id": clause_key(clause),
        "span": clause["span"],
        "evidence": [{
            "grade": grade if grade != "test observation" or observed[clause_key(clause)] else "unobserved",
            "mode": request["runtime_validation"],
            "valid_cases": observed[clause_key(clause)],
            "reason": reason if grade != "test observation" or reason else "no generated case exercised this conditional clause",
        }],
    } for clause in clauses]


def main():
    request = json.load(__import__("sys").stdin)
    strategies = {strategy["symbol"]: strategy for strategy in request["strategies"]}
    contracts = []
    for module_value in request["modules"]:
        for declaration in module_value["declarations"]:
            if declaration["kind"] == "function":
                strategy = strategies.get(declaration["name"])
                if strategy is None:
                    continue
                observed, grade, reason = run_function(module_value, declaration, strategy)
                contracts.extend(evidence(declaration["name"], declaration["contract"]["clauses"], observed, grade, reason, request))
            elif declaration["kind"] == "impl":
                module = importlib.import_module(module_value["module"])
                if hasattr(module, "_cott_set_test_context"):
                    module._cott_set_test_context(True)
                init_symbol = f"{module_value['module']}.{local(declaration['name'])}.init"
                init_strategy = strategies.get(init_symbol)
                initializer_cases = invoke_cases(getattr(module, local(declaration["name"])))
                if init_strategy is not None:
                    clauses, observed, grade, reason, initializer_cases = run_initializer(module, declaration, init_strategy)
                    contracts.extend(evidence(init_symbol, clauses, observed, grade, reason, request))
                for method in declaration["methods"]:
                    symbol = f"{module_value['module']}.{local(declaration['name'])}.{method['name']}"
                    strategy = strategies.get(symbol)
                    if strategy is None:
                        continue
                    clauses, observed, grade, reason = run_method(module, declaration, strategy, initializer_cases)
                    contracts.extend(evidence(symbol, clauses, observed, grade, reason, request))
    print(json.dumps({"contracts": contracts}, sort_keys=True, separators=(",", ":")))


main()
