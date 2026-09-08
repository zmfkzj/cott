#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import time
import zipfile
from pathlib import Path

from ai_generation_protocol import MODEL, REQUIREMENTS, THINKING, direct_prompt
from contract_value import (
    COMMAND_TIMEOUT,
    Infra,
    ROOT,
    as_text,
    clip,
    copy_venv,
    hashed,
    median,
    require,
    sha256_file,
)

SOURCE = ROOT / "examples/complex/artifact-pipeline"
PROTOCOL = Path(__file__).resolve().parent / "ai_generation_protocol.py"
PROVIDER, _, MODEL_NAME = MODEL.partition("/")
COTT_USAGE_REASON = (
    "Cott native OMP adapter provenance records durations and stream digests only; "
    "token usage is not retained and is not inferred from characters or direct-arm usage"
)
RETRY_RE = re.compile(r"retry (\d+)/2")
GEN_TIMEOUT = COMMAND_TIMEOUT * 4  # ponytail: outer bound; native per-run already 900s
CAVEATS = (
    "One task (artifact-pipeline); N paired trials is not a broad capability claim.",
    "Direct is one OMP invocation; Cott may natively retry each callable up to 2 times.",
    "Same model, thinking, and OMP tools (read,grep,glob,edit,write).",
    "Generation walltime is separate from postverify and independent semantic acceptance.",
    "Cott token usage is unavailable from native provenance; direct cost is estimated not billing.",
)
SKIPPED = {
    "ok": False,
    "returncode": None,
    "seconds": 0.0,
    "stdout": "",
    "timed_out": False,
    "infrastructure": False,
}


def run(argv, *, cwd=None, env=None, timeout=COMMAND_TIMEOUT):
    started = time.perf_counter()
    try:
        done = subprocess.run(
            argv, input="", capture_output=True, cwd=cwd, env=env, timeout=timeout,
            encoding="utf-8", errors="replace",
        )
    except subprocess.TimeoutExpired as error:
        return _cmd(False, None, time.perf_counter() - started, error.stdout,
                    error.stderr or f"timeout after {timeout}s", argv, True, False)
    except OSError as error:
        return _cmd(False, None, time.perf_counter() - started, "", error, argv, False, True)
    return _cmd(done.returncode == 0, done.returncode, time.perf_counter() - started,
                done.stdout, done.stderr, argv, False, False)


def _cmd(ok, code, seconds, stdout, stderr, argv, timed_out, infrastructure):
    return {
        "ok": ok, "returncode": code, "seconds": seconds, "stdout": as_text(stdout),
        "stderr": as_text(stderr), "argv": list(argv), "timed_out": timed_out,
        "infrastructure": infrastructure,
    }


def resolve_state(arg):
    if arg:
        return Path(arg).expanduser().resolve()
    env = os.environ.get("PI_CODING_AGENT_DIR")
    return Path(env).expanduser().resolve() if env else Path.home() / ".omp" / "agent"


def omp_env(state):
    env = os.environ.copy()
    env["PI_CODING_AGENT_DIR"] = str(state)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    return env


def copy_state(src, dst):
    dst.mkdir(parents=True, exist_ok=True)
    os.chmod(dst, 0o700)
    copied = False
    cfg = src / "config.yml"
    if cfg.is_file():
        shutil.copy2(cfg, dst / "config.yml")
        copied = True
    db = src / "agent.db"
    if db.is_file():
        source = sqlite3.connect(f"file:{db}?mode=ro", uri=True)
        try:
            dest = sqlite3.connect(dst / "agent.db")
            try:
                source.backup(dest)
            finally:
                dest.close()
        finally:
            source.close()
        copied = True
    if not copied:
        raise Infra(f"no config.yml or agent.db in {src}")

def configure_state(omp, state):
    sets = (
        ("modelRoles", json.dumps({"default": f"{MODEL}:{THINKING}"}, separators=(",", ":"))),
        ("defaultThinkingLevel", THINKING),
        ("retry.modelFallback", "false"),
        ("prewalk.enabled", "false"),
        ("startup.checkUpdate", "false"),
        ("advisor.enabled", "false"),
        ("externalThinking", "false"),
    )
    env = omp_env(state)
    for key, value in sets:
        result = run([omp, "config", "set", key, value], env=env, timeout=60)
        if not result["ok"]:
            raise Infra(f"omp config set {key} failed: {clip(result['stderr'] or result['stdout'])}")


def write_cott_project(dst):
    shutil.copytree(SOURCE / "src", dst / "src")
    shutil.copy2(SOURCE / "cott.toml", dst / "cott.toml")
    python = dst / "python"
    python.mkdir()
    shutil.copy2(SOURCE / "python/pyproject.toml", python / "pyproject.toml")
    shutil.copy2(SOURCE / "python/uv.lock", python / "uv.lock")
    copy_venv(SOURCE / ".venv", dst / ".venv")
    rules = (SOURCE / "GENERATOR_RULES.txt").read_text(encoding="utf-8").rstrip()
    (dst / "GENERATOR_RULES.txt").write_text(rules + "\n\n" + REQUIREMENTS + "\n", encoding="utf-8")


def summarize(result):
    return {k: clip(result[k]) if k in {"stdout", "stderr"} else result[k]
            for k in ("ok", "returncode", "seconds", "timed_out", "infrastructure", "stdout", "stderr", "argv")}


def cott_runs(project):
    path = project / "generated" / "generation.json"
    if not path.is_file():
        return None
    try:
        runs = (json.loads(path.read_text(encoding="utf-8")).get("current") or {}).get("agent_runs") or []
    except json.JSONDecodeError:
        return None
    keys = ("symbol", "duration_ms", "status", "stdout", "stderr", "adapter", "adapter_version",
            "prompt_hash", "implementation_hash", "argv_template", "executable", "executable_hash")
    return [{k: run.get(k) for k in keys} for run in runs]


def json_events(text):
    text = as_text(text).strip()
    if text.startswith("["):
        try:
            data = json.loads(text)
            if isinstance(data, list):
                yield from (x for x in data if isinstance(x, dict))
                return
        except json.JSONDecodeError:
            pass
    for line in text.splitlines():
        line = line.strip()
        if not line.startswith("{"):
            continue
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(item, dict):
            yield item


def direct_usage(stdout):
    matched, unmatched = [], []
    for event in json_events(stdout):
        if event.get("type") != "message_end":
            continue
        message = event.get("message") or {}
        if message.get("role") != "assistant":
            continue
        usage = message.get("usage") if isinstance(message.get("usage"), dict) else None
        row = {"provider": message.get("provider"), "model": message.get("model"), "usage": usage}
        if row["provider"] == PROVIDER and row["model"] == MODEL_NAME and usage is not None:
            matched.append(row)
        else:
            unmatched.append(row)
    empty = {k: None for k in ("input", "output", "cacheRead", "cacheWrite", "totalTokens", "cost_estimated", "provider", "model")}
    total = len(matched) + len(unmatched)
    if not total or unmatched:
        reason = ("unmatched assistant message_end" if unmatched else
                  "no assistant message_end with matching provider/model/usage")
        return {**empty, "ok": False, "message_end_count": total, "reason": reason,
                "evidence": unmatched or clip(stdout, 1500)}
    def fold(key):
        acc = 0
        for row in matched:
            if key not in row["usage"] or row["usage"][key] is None:
                return None
            acc += int(row["usage"][key])
        return acc
    totals = {k: fold(k) for k in ("input", "output", "cacheRead", "cacheWrite", "totalTokens")}
    cost = 0.0
    for row in matched:
        item = row["usage"].get("cost")
        if not isinstance(item, dict) or item.get("total") is None:
            cost = None
            break
        cost += float(item["total"])
    return {"ok": True, **totals, "cost_estimated": cost, "cost_note": "priced cost estimated not billing",
            "provider": PROVIDER, "model": MODEL_NAME, "message_end_count": total,
            "reason": None, "evidence": None}


def semantics(arm, project):
    result = run([sys.executable, str(PROTOCOL), "--arm", arm, "--project", str(project)])
    elapsed = result["seconds"]
    if result["timed_out"] or result["infrastructure"]:
        return {"ok": False, "counts": None, "seconds": elapsed,
                "error": clip(result["stderr"] or result["stdout"] or "verifier failed")}
    try:
        counts = json.loads((result["stdout"] or "").strip() or "null")
    except json.JSONDecodeError:
        counts = None
    if not isinstance(counts, dict):
        return {"ok": False, "counts": None, "seconds": elapsed,
                "error": f"malformed verifier JSON: {clip(result['stdout'] or result['stderr'])}"}
    if "ok" in counts:
        ok = bool(counts["ok"])
    elif "semantic_ok" in counts or "type_ok" in counts:
        ok = bool(counts.get("semantic_ok")) and bool(counts.get("type_ok"))
    else:
        ok = result["ok"]
    return {"ok": ok, "counts": counts, "seconds": elapsed, "error": None}

def pack_times(rows, seconds_key, ok_key):
    grab = lambda pred: [row[seconds_key] for row in rows if pred(row) and row.get(seconds_key) is not None]
    all_ = grab(lambda row: True)
    ok = grab(lambda row: row.get(ok_key))
    fail = grab(lambda row: not row.get(ok_key))
    return {"samples": all_, "median": median(all_), "success_samples": ok, "success_median": median(ok),
            "failure_samples": fail, "failure_median": median(fail)}


def keep(arts, arc, path):
    if path.is_file():
        arts.append((arc, path))


def dump(arts, arc, path, text):
    path.write_text(as_text(text), encoding="utf-8")
    arts.append((arc, path))


def keep_tree(arts, prefix, root):
    if not root.is_dir():
        return
    for path in root.rglob("*"):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        if any(part == "__pycache__" for part in rel.parts) or path.suffix == ".pyc":
            continue
        keep(arts, f"{prefix}/{rel.as_posix()}", path)

def outcome(arm, gen, post, sem, extra):
    row = {
        "arm": arm, "generation": summarize(gen), "postverify": summarize(post), "semantic": sem,
        "generation_ok": gen["ok"], "postverify_ok": post["ok"], "semantic_ok": sem["ok"],
        "end_to_end_ok": bool(gen["ok"] and post["ok"] and sem["ok"]),
        "generation_seconds": gen["seconds"], "postverify_seconds": post["seconds"],
        "semantic_seconds": sem["seconds"],
    }
    row.update(extra)
    return row


def skip_cmd(reason):
    return {**SKIPPED, "stderr": reason, "argv": []}


def main(argv=None):
    parser = argparse.ArgumentParser()
    parser.add_argument("--cott", required=True)
    parser.add_argument("--agent-state")
    parser.add_argument("--repeat", type=int, default=3)
    parser.add_argument("--jobs", type=int, default=3)
    parser.add_argument("--output", required=True)
    args = parser.parse_args(argv)
    if not 1 <= args.jobs <= 3:
        print("error: --jobs must be 1..3", file=sys.stderr)
        return 2
    if args.repeat < 1:
        print("error: --repeat must be >= 1", file=sys.stderr)
        return 2
    raw = Path(args.cott).expanduser()
    cott = raw.resolve() if raw.is_file() else Path(shutil.which(args.cott) or raw)
    output = Path(args.output)
    if not output.is_absolute():
        output = Path.cwd() / output
    omp = shutil.which("omp")
    try:
        require(cott, "cott binary")
        if not omp:
            raise Infra("missing omp on PATH")
        require(SOURCE / "cott.toml", "artifact-pipeline manifest")
        require(SOURCE / "src/curriculum/artifact_pipeline.cott", "contract")
        require(SOURCE / "python/pyproject.toml", "pyproject")
        require(SOURCE / "python/uv.lock", "lockfile")
        require(SOURCE / ".venv/bin/python", "pinned interpreter")
        require(SOURCE / ".venv/bin/basedpyright", "pinned type checker")
        require(SOURCE / "GENERATOR_RULES.txt", "generator rules")
        require(SOURCE / "check_semantics.py", "shared cases")
        user_state = resolve_state(args.agent_state)
        require(user_state, "omp agent state")
    except Infra as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    prompt_text = direct_prompt()
    pyright = str(SOURCE / ".venv/bin/basedpyright")
    tmp = Path(tempfile.mkdtemp(prefix="cott-ai-gen-"))
    arts, trials, fatal = [], [], []
    try:
        template = tmp / "omp-template"
        copy_state(user_state, template)
        configure_state(omp, template)
        for index in range(args.repeat):
            order = ("cott", "direct") if index % 2 == 0 else ("direct", "cott")
            pair = {"index": index, "order": list(order), "arms": {}}
            for arm in order:
                prefix = f"trial{index}/{arm}"
                arm_state = tmp / f"t{index}-{arm}-state"
                copy_state(template, arm_state)
                env = omp_env(arm_state)
                if arm == "cott":
                    project = tmp / f"t{index}-cott"
                    write_cott_project(project)
                    keep(arts, f"{prefix}/cott.toml", project / "cott.toml")
                    keep(arts, f"{prefix}/GENERATOR_RULES.txt", project / "GENERATOR_RULES.txt")
                    gen = run(
                        [str(cott), "generate", "--agent", "omp", "--target", "python",
                         "-j", str(args.jobs), "--project", str(project)],
                        env=env, timeout=GEN_TIMEOUT,
                    )
                    facade = project / "generated/python/curriculum/artifact_pipeline.py"
                    post = (run([str(cott), "verify", "--project", str(project)], env=env)
                            if (project / "generated").is_dir() else skip_cmd("skipped: no generated/"))
                    sem = semantics("cott", project) if facade.is_file() else {
                        "ok": False, "counts": None, "seconds": 0.0, "error": "missing generated facade"}
                    dump(arts, f"{prefix}/stdout.txt", tmp / f"t{index}-cott-stdout.txt", gen["stdout"])
                    dump(arts, f"{prefix}/stderr.txt", tmp / f"t{index}-cott-stderr.txt", gen["stderr"])
                    keep_tree(arts, f"{prefix}/src", project / "src")
                    keep_tree(arts, f"{prefix}/python", project / "python")
                    keep_tree(arts, f"{prefix}/generated", project / "generated")
                    retries = [int(n) for n in RETRY_RE.findall(gen["stderr"])]
                    extra = {
                        "agent_runs": cott_runs(project),
                        "retries": {
                            "events": retries,
                            "count": len(retries),
                            "limit_per_callable": 2,
                            "label": "native generate [i/n] retry k/2 `symbol` (max 2 retries / 3 attempts)",
                        },
                        "usage": {
                            "input": None, "output": None, "cacheRead": None, "cacheWrite": None,
                            "totalTokens": None, "cost_estimated": None, "reason": COTT_USAGE_REASON,
                        },
                    }
                else:
                    project = tmp / f"t{index}-direct"
                    project.mkdir()
                    overlay = tmp / f"t{index}-overlay.yaml"
                    overlay.write_text("startup:\n  checkUpdate: false\n", encoding="utf-8")
                    prompt = tmp / f"t{index}-direct-prompt.txt"
                    prompt.write_text(prompt_text, encoding="utf-8")
                    keep(arts, f"{prefix}/prompt.txt", prompt)
                    gen = run(
                        [omp, "-p", "--mode", "json", "--cwd", str(project),
                         "--no-session", "--no-rules", "--no-skills", "--no-extensions",
                         "--no-lsp", "--no-pty", "--no-title", "--tools", "read,grep,glob,edit,write",
                         "--approval-mode", "yolo", "--max-time", f"{COMMAND_TIMEOUT}s",
                         "--config", str(overlay), f"@{prompt}"],
                        env=env, timeout=GEN_TIMEOUT,
                    )
                    pipeline = project / "pipeline.py"
                    post = (run([pyright, "--level", "error", str(pipeline)], cwd=project)
                            if pipeline.is_file() else skip_cmd("skipped: no pipeline.py"))
                    sem = semantics("direct", project) if pipeline.is_file() else {
                        "ok": False, "counts": None, "seconds": 0.0, "error": "missing pipeline.py"}
                    dump(arts, f"{prefix}/stdout.txt", tmp / f"t{index}-direct-stdout.txt", gen["stdout"])
                    dump(arts, f"{prefix}/stderr.txt", tmp / f"t{index}-direct-stderr.txt", gen["stderr"])
                    keep(arts, f"{prefix}/pipeline.py", pipeline)
                    extra = {"agent_runs": None, "retries": None, "usage": direct_usage(gen["stdout"])}
                if gen["infrastructure"]:
                    fatal.append(f"trial {index} {arm}: {clip(gen['stderr'])}")
                elif arm == "direct" and gen["ok"] and not extra["usage"]["ok"]:
                    fatal.append(f"trial {index} direct: {extra['usage']['reason']}")
                pair["arms"][arm] = outcome(arm, gen, post, sem, extra)
            trials.append(pair)

        n = args.repeat
        summary = {}
        for arm in ("cott", "direct"):
            rows = [pair["arms"][arm] for pair in trials]
            gen_ok = sum(1 for row in rows if row["generation_ok"])
            post_ok = sum(1 for row in rows if row["postverify_ok"])
            sem_ok = sum(1 for row in rows if row["semantic_ok"])
            e2e = sum(1 for row in rows if row["end_to_end_ok"])
            summary[arm] = {
                "trials": n, "generation_ok": gen_ok, "generation_fraction": gen_ok / n,
                "postverify_ok": post_ok, "postverify_fraction": post_ok / n,
                "semantic_ok": sem_ok, "semantic_fraction": sem_ok / n,
                "end_to_end_ok": e2e, "end_to_end_fraction": e2e / n,
                "generation_seconds": pack_times(rows, "generation_seconds", "generation_ok"),
                "postverify_seconds": pack_times(rows, "postverify_seconds", "postverify_ok"),
                "semantic_seconds": pack_times(rows, "semantic_seconds", "semantic_ok"),
            }
        zpath = output.with_suffix(".zip")
        results = {
            "task": "artifact-pipeline", "model": MODEL, "thinking": THINKING,
            "provider": PROVIDER, "model_name": MODEL_NAME,
            "sample_size": n, "jobs": args.jobs, "caveats": list(CAVEATS),
            "model_settings": {
                "modelRoles": {"default": f"{MODEL}:{THINKING}"},
                "defaultThinkingLevel": THINKING,
                "retry.modelFallback": False,
            },
            "identity": {
                "scripts": {
                    "ai_generation": hashed(Path(__file__).resolve()),
                    "ai_generation_protocol": hashed(Path(__file__).resolve().parent / "ai_generation_protocol.py"),
                    "check_semantics": hashed(SOURCE / "check_semantics.py"),
                },
                "cott": {"executable": str(cott), "content_hash": sha256_file(cott) if cott.is_file() else None},
            },
            "summary": summary, "trials": trials, "artifacts_zip": str(zpath),
        }
        output.parent.mkdir(parents=True, exist_ok=True)
        payload = json.dumps(results, indent=2) + "\n"
        with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("results.json", payload)
            for arc, path in arts:
                if path.is_file():
                    zf.write(path, arc)
        output.write_text(payload, encoding="utf-8")
    except Infra as error:
        print(f"error: {error}", file=sys.stderr)
        return 1
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    if fatal:
        print("error: " + " | ".join(fatal), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
