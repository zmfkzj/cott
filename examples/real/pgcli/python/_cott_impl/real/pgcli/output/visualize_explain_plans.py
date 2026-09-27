from collections.abc import Iterable
import json
import re
import textwrap
from typing import cast

import click
from cott_runtime import Err, Ok, Result, U32
from real.pgcli.output_types import EXPLAIN_NODE_DESCRIPTIONS, FormattedOutput, OutputError, OutputError_Failed


def _bb(text: str) -> str:
    return click.style(text, fg="bright_black")


def _dur(value: float) -> str:
    if value < 1:
        return click.style("<1 ms", fg="green")
    if value < 100:
        return click.style("%.2f ms" % value, fg="green")
    if value < 1000:
        return click.style("%.2f ms" % value, fg="yellow")
    if value < 60000:
        return click.style("%.2f s" % (value / 1000.0), fg="red")
    return click.style("%.2f m" % (value / 60000.0), fg="red")


def _intcomma(value: object) -> str:
    result = value if isinstance(value, str) else str(int(cast(int | float, value)))
    while True:
        updated = re.sub(r"^(-?\d+)(\d{3})", r"\g<1>,\g<2>", result)
        if updated == result:
            return result
        result = updated


def _wrap(text: str, cols: int) -> list[str]:
    if cols == 0:
        return [text]
    return textwrap.wrap(text, cols)


def _map(value: object) -> dict[object, object]:
    if not isinstance(value, dict):
        raise TypeError("plan entry is not an object")
    return cast(dict[object, object], value)


def _children(node: dict[object, object]) -> list[dict[object, object]]:
    value = node.get("Plans", [])
    if not isinstance(value, list):
        raise TypeError("Plans is not a list")
    children = cast(list[object], value)
    for child in children:
        if not isinstance(child, dict):
            raise TypeError("plan entry is not an object")
    return cast(list[dict[object, object]], children)


def _number(node: dict[object, object], key: str) -> float:
    return cast(float, node[key])


def _process(node: dict[object, object], explain: dict[object, object]) -> None:
    factor: float = 0
    direction = "Under"
    plan_rows = _number(node, "Plan Rows")
    actual_rows = _number(node, "Actual Rows")
    if plan_rows != actual_rows:
        if plan_rows != 0:
            factor = actual_rows / plan_rows
        if factor < 10:
            factor = 0
            direction = "Over"
            if actual_rows != 0:
                factor = plan_rows / actual_rows
    duration = _number(node, "Actual Total Time")
    cost = _number(node, "Total Cost")
    children = _children(node)
    for child in children:
        if child["Node Type"] != "CTEScan":
            duration -= _number(child, "Actual Total Time")
            cost -= _number(child, "Total Cost")
    if cost < 0:
        cost = 0
    duration *= _number(node, "Actual Loops")
    node["__factor"] = factor
    node["__direction"] = direction
    node["__duration"] = duration
    node["__cost"] = cost
    for key, value in (("Max Rows", actual_rows), ("Max Cost", cost), ("Max Duration", duration), ("Total Cost", cost)):
        if not explain.get(key) or _number(explain, key) < value:
            explain[key] = value
    for child in children:
        _process(child, explain)


def _outliers(node: dict[object, object], explain: dict[object, object]) -> None:
    node["__costliest"] = node["__cost"] == explain["Max Cost"]
    node["__largest"] = node["Actual Rows"] == explain["Max Rows"]
    node["__slowest"] = node["__duration"] == explain["Max Duration"]
    for child in _children(node):
        _outliers(child, explain)


def _node_lines(node: dict[object, object], explain: dict[object, object], descriptions: dict[object, object], prefix: str, width: int, last: bool, lines: list[str]) -> None:
    lines.append(_bb(prefix) + _bb("│"))
    details_parts = [str(part) for part in (node.get("Scan Direction"), node.get("Strategy")) if part]
    details = _bb(" [" + ", ".join(details_parts) + "]") if details_parts else ""
    tags: list[str] = []
    if node["__slowest"]:
        tags.append(click.style("slowest", fg="white", bg="red"))
    if node["__costliest"]:
        tags.append(click.style("costliest", fg="white", bg="red"))
    if node["__largest"]:
        tags.append(click.style("largest", fg="white", bg="red"))
    if _number(node, "__factor") >= 100:
        tags.append(click.style("bad estimate", fg="white", bg="red"))
    node_type = node["Node Type"]
    lines.append(_bb(prefix) + _bb(("└" if last else "├") + "─⌠") + " " + click.style(str(node_type), fg="white") + details + " " + " ".join(tags))
    prefix2 = prefix + ("  " if last else "│ ")
    p = prefix2 + "│ "
    cols = width - len(p)
    description = descriptions.get(node_type, "Not found : " + str(node_type))
    for line in _wrap(str(description), cols):
        lines.append(_bb(p) + _bb(line))
    duration = _number(node, "__duration")
    cost = _number(node, "__cost")
    if duration:
        lines.append(_bb(p) + "○ Duration: " + _dur(duration) + " (%.0f%%)" % (duration / _number(explain, "Execution Time") * 100))
    lines.append(_bb(p) + "○ Cost: " + _intcomma(cost) + " (%.0f%%)" % (cost / _number(explain, "Total Cost") * 100))
    lines.append(_bb(p) + "○ Rows: " + _intcomma(node["Actual Rows"]))
    q = _bb(p + "  ")
    if node.get("Join Type"):
        lines.append(q + str(node["Join Type"]) + " " + _bb("join"))
    if node.get("Relation Name"):
        lines.append(q + _bb("on") + " " + str(node.get("Schema", "unknown")) + "." + str(node["Relation Name"]))
    if node.get("Index Name"):
        lines.append(q + _bb("using") + " " + str(node["Index Name"]))
    if node.get("Index Condition"):
        lines.append(q + _bb("condition") + " " + str(node["Index Condition"]))
    if node.get("Filter"):
        lines.append(q + _bb("filter") + " " + str(node["Filter"]) + " " + _bb("[-" + _intcomma(node["Rows Removed by Filter"]) + " rows]"))
    if node.get("Hash Condition"):
        lines.append(q + _bb("on") + " " + str(node["Hash Condition"]))
    if node.get("CTE Name"):
        lines.append(q + "CTE " + str(node["CTE Name"]))
    if _number(node, "__factor") != 0:
        lines.append(q + _bb("rows") + " " + str(node["__direction"]) + "estimated " + _bb("by") + " " + "%.2f" % _number(node, "__factor") + "x")
    children = _children(node)
    outputs = node.get("Output", [])
    if outputs:
        if not isinstance(outputs, list):
            raise TypeError("Output is not a list")
        for index, line in enumerate(_wrap(" + ".join(str(output) for output in cast(list[object], outputs)), cols)):
            terminator = ("├►  " if children else "⌡► ") if index == 0 else ("│  " if children else "   ")
            lines.append(_bb(prefix2) + _bb(terminator) + click.style(line, fg="cyan"))
    for index, child in enumerate(children):
        _node_lines(child, explain, descriptions, prefix2, width, index == len(children) - 1, lines)


def _render(plan_json: str, width: int) -> list[str]:
    descriptions = _map(cast(object, json.loads(EXPLAIN_NODE_DESCRIPTIONS)))
    decoded = cast(object, json.loads(plan_json))
    if isinstance(decoded, list):
        elements: Iterable[object] = cast(list[object], decoded)
    elif isinstance(decoded, dict):
        elements = cast(dict[object, object], decoded)
    else:
        elements = cast(Iterable[object], decoded)
    items: list[str] = []
    for element in elements:
        explain = _map(element)
        plan = _map(explain.pop("Plan"))
        _process(plan, explain)
        _outliers(plan, explain)
        lines: list[str] = [
            "○ Total Cost: " + _intcomma(explain["Total Cost"]),
            "○ Planning Time: " + _dur(_number(explain, "Planning Time")),
            "○ Execution Time: " + _dur(_number(explain, "Execution Time")),
            _bb("┬"),
        ]
        _node_lines(plan, explain, descriptions, "", width, len(_children(plan)) == 1, lines)
        items.append("\n".join(lines))
    return items


def visualize_explain_plans(plan_json: str, terminal_width: U32) -> Result[FormattedOutput, OutputError]:
    try:
        items = _render(plan_json, terminal_width)
    except Exception as error:
        return Err[OutputError](error=OutputError_Failed(message=str(error)))
    return Ok(value=FormattedOutput(text="\n".join(items), items=len(items)))
