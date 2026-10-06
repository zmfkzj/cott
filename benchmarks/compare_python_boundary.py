#!/usr/bin/env python3
"""Compare compatible current-run reports; overlapping ranges are not a speedup claim."""
import argparse
import json
from pathlib import Path


def compare(before, after):
    if before["status"] != "measured" or after["status"] != "measured":
        raise ValueError("cannot compare blocked or incomplete runs")
    if before["scope"] != after["scope"]:
        raise ValueError("cannot compare component and facade scopes")
    for field in ("sha256", "version", "platform"):
        if before["identity"]["python"][field] != after["identity"]["python"][field]:
            raise ValueError(f"different interpreter/host: {field}")
    if before["identity"]["scripts"]["python_boundary.py"]["sha256"] != after["identity"]["scripts"]["python_boundary.py"]["sha256"]:
        raise ValueError("measurement harness changed; rerun both arms")
    def key(row):
        return tuple(row[k] for k in ("arm", "mode", "test_context", "size", "depth", "loops", "input_sha256"))
    old = {key(row): row for row in before["rows"]}
    new = {key(row): row for row in after["rows"]}
    if old.keys() != new.keys() or not old:
        raise ValueError("workloads/check levels differ or are empty")
    rows = []
    for identity, row in old.items():
        other = new[identity]
        fields = {k: row[k] for k in ("arm", "mode", "test_context", "size", "depth")}
        fields["metrics"] = {}
        for name in row["summary"]:
            b, a = row["summary"][name], other["summary"][name]
            fields["metrics"][name] = {
                "before_median": b["median"], "after_median": a["median"],
                "before_range": [b["min"], b["max"]], "after_range": [a["min"], a["max"]],
                "median_change_percent": 100 * (a["median"] / b["median"] - 1) if b["median"] else None,
                "ranges_overlap": not (a["max"] < b["min"] or b["max"] < a["min"]),
            }
        fields["runtime_package_bytes"] = {"before": row["runtime_identity"]["package_bytes"],
                                             "after": other["runtime_identity"]["package_bytes"]}
        rows.append(fields)
    return {"schema_version": 1, "scope": before["scope"], "rows": rows,
            "limits": ["Range separation is descriptive, not a statistical significance test.",
                       "Sequential unpaired runs; host scheduling/thermal state are uncontrolled.",
                       "No certification, application-throughput or developer-productivity inference."]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("before", type=Path)
    parser.add_argument("after", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    result = compare(json.loads(args.before.read_text()), json.loads(args.after.read_text()))
    result["reports"] = {"before": str(args.before), "after": str(args.after)}
    with args.output.open("x") as out:
        json.dump(result, out, indent=2)
        out.write("\n")


if __name__ == "__main__":
    main()
