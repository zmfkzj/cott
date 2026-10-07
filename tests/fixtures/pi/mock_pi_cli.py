#!/usr/bin/env node
# MOCK of the Pi coding-agent CLI (@earendil-works/pi-coding-agent) for cott
# tests. It is NOT Pi and never contacts a provider. The fake `node` launcher
# runs this file with python3; it reproduces the package version probe, Pi's
# agent-directory and default-model resolution, and the `--mode json` JSONL
# event protocol shaped after real Pi 1.0.4 transcripts
# (tests/fixtures/pi/real-1.0.4-*.jsonl). Behaviour comes from mock.json.
import json
import os
import sys
import time

HERE = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(HERE, "mock.json"), encoding="utf-8") as handle:
    CONFIG = json.load(handle)
ARGS = sys.argv[1:]

if ARGS == ["--version"]:
    # The probe must run without credentials or a provider selection.
    if any(name.endswith("_API_KEY") for name in os.environ):
        sys.exit(70)
    print(CONFIG["probe_version"])
    sys.exit(0)


def agent_directory():
    value = os.environ.get("PI_CODING_AGENT_DIR", "")
    if value == "~":
        return os.environ["HOME"]
    if value.startswith("~/"):
        return os.path.join(os.environ["HOME"], value[2:])
    return value or os.path.join(os.environ["HOME"], ".pi", "agent")


def read_text(path):
    try:
        with open(path, encoding="utf-8") as handle:
            return handle.read()
    except OSError:
        return None


SCENARIO = CONFIG.get("scenario", "success")
AGENT_DIR = agent_directory()
SETTINGS = json.loads(read_text(os.path.join(AGENT_DIR, "settings.json")) or "{}")
if "--model" in ARGS:
    selection = ARGS[ARGS.index("--model") + 1]
elif SETTINGS.get("defaultProvider") and SETTINGS.get("defaultModel"):
    # Pi's default model comes from the caller's settings.json.
    selection = SETTINGS["defaultProvider"] + "/" + SETTINGS["defaultModel"]
else:
    sys.stderr.write("No model configured: set defaultProvider/defaultModel or pass --model\n")
    sys.exit(1)
PROVIDER, _, MODEL = selection.partition("/")
PROMPT = ARGS[-1]
STDIN = sys.stdin.read()
try:
    with open("AGENTS.md", "a", encoding="utf-8") as handle:
        handle.write("mock")
    project_write = "written"
except OSError:
    project_write = "blocked"
# Only names, and values of the variables the tests control, are captured.
VALUES = ("HOME", "PATH", "TMPDIR", "PI_CODING_AGENT_DIR", "COTT_TEST_CUSTOM", "OPENAI_API_KEY")
capture = {
    "argv": ARGS,
    "stdin": STDIN,
    # `PWD` (set by the sh launcher) and `LC_CTYPE` (CPython PEP 538 locale
    # coercion) come from the mock's own interpreters, not from cott.
    "environment_names": sorted(name for name in os.environ if name not in ("PWD", "LC_CTYPE")),
    "environment": {name: os.environ[name] for name in VALUES if name in os.environ},
    "cwd": os.getcwd(),
    "cwd_entries": sorted(os.listdir(".")),
    "project_context": read_text("AGENTS.md"),
    "project_write": project_write,
    "agent_dir_entries": sorted(os.listdir(AGENT_DIR)) if os.path.isdir(AGENT_DIR) else None,
    "settings": SETTINGS,
    "visible_host_paths": [path for path in CONFIG.get("host_paths", []) if os.path.exists(path)],
}
if CONFIG.get("refresh_auth"):
    # Like Pi's auth storage: refresh the login in auth.json while holding the
    # proper-lockfile lock directory next to it, and write an extension model
    # cache into the agent directory. The directory identity shows whether
    # the run used the caller's own store.
    lock = os.path.join(AGENT_DIR, "auth.json.lock")
    os.mkdir(lock)
    with open(os.path.join(AGENT_DIR, "auth.json"), "w", encoding="utf-8") as handle:
        handle.write('{"refreshed":true}')
    os.rmdir(lock)
    with open(os.path.join(AGENT_DIR, "models-cache.json"), "w", encoding="utf-8") as handle:
        handle.write("{}")
    identity = os.stat(AGENT_DIR)
    capture["agent_dir_identity"] = [identity.st_dev, identity.st_ino]
with open(os.path.join(os.environ["TMPDIR"], "pi-capture.json"), "w", encoding="utf-8") as handle:
    json.dump(capture, handle, ensure_ascii=False)

if SCENARIO == "sleep":
    time.sleep(60)

wrote = SCENARIO not in ("no-write", "provider-error")
if wrote:
    candidate = CONFIG.get("candidate")
    if candidate is None:
        candidate = eval(CONFIG["candidate_python"], {"prompt": PROMPT, "project_context": capture["project_context"]})
    with open(CONFIG.get("target", "implementation.py"), "w", encoding="utf-8") as handle:
        handle.write(candidate)


def assistant(content, stop_reason):
    return {
        "role": "assistant",
        "content": content,
        "api": "openai-completions",
        "provider": PROVIDER,
        "model": "other-model" if SCENARIO == "routed-model" else MODEL,
        "usage": {"input": 1, "output": 1, "cacheRead": 0, "cacheWrite": 0, "totalTokens": 2},
        "stopReason": stop_reason,
        "timestamp": 2,
    }


user = {"role": "user", "content": [{"type": "text", "text": PROMPT}], "timestamp": 1}
records = [
    {"type": "session", "version": 3, "id": "mock-session", "timestamp": "2026-10-07T00:00:00.000Z", "cwd": os.getcwd()},
    {"type": "agent_start"},
    {"type": "turn_start"},
    {"type": "message_start", "message": user},
    {"type": "message_end", "message": user},
]
if SCENARIO == "provider-error":
    failed = assistant([], "error")
    failed["errorMessage"] = "500: mock failure"
    records += [
        {"type": "message_start", "message": failed},
        {"type": "message_end", "message": failed},
        {"type": "turn_end", "message": failed, "toolResults": []},
    ]
else:
    call = {"type": "toolCall", "id": "call_1", "name": "write", "arguments": {"path": "implementation"}}
    tool_use = assistant([call], "toolUse")
    result = {"role": "toolResult", "toolCallId": "call_1", "toolName": "write", "content": [{"type": "text", "text": "ok"}], "isError": False, "timestamp": 3}
    final = assistant([{"type": "text", "text": "done"}], "length" if SCENARIO == "length" else "stop")
    records += [
        {"type": "message_start", "message": tool_use},
        {"type": "message_end", "message": tool_use},
        {"type": "tool_execution_start", "toolCallId": "call_1", "toolName": "write", "args": call["arguments"]},
        {"type": "tool_execution_end", "toolCallId": "call_1", "toolName": "write", "result": {"content": result["content"]}, "isError": False},
    ]
    if SCENARIO == "user-tools":
        # A built-in tool and an extension tool of the caller's setup.
        records += [
            {"type": "tool_execution_start", "toolCallId": "call_2", "toolName": "bash", "args": {"command": "true"}},
            {"type": "tool_execution_end", "toolCallId": "call_2", "toolName": "bash", "result": {}, "isError": False},
            {"type": "tool_execution_start", "toolCallId": "call_3", "toolName": "codegraph_search", "args": {}},
            {"type": "tool_execution_end", "toolCallId": "call_3", "toolName": "codegraph_search", "result": {}, "isError": False},
        ]
    records += [
        {"type": "message_start", "message": result},
        {"type": "message_end", "message": result},
        {"type": "turn_end", "message": tool_use, "toolResults": [result]},
        {"type": "turn_start"},
        {"type": "message_start", "message": final},
        {"type": "message_end", "message": final},
        {"type": "turn_end", "message": final, "toolResults": []},
    ]
records += [{"type": "agent_end", "messages": [], "willRetry": False}, {"type": "agent_settled"}]
if SCENARIO == "unsettled":
    records.pop()

stream = "".join(json.dumps(record, ensure_ascii=False, separators=(",", ":")) + "\n" for record in records)
if SCENARIO == "contaminated":
    stream = "Warning: not JSON\n" + stream
if SCENARIO == "truncated":
    stream = stream[:-1]
sys.stdout.write(stream)
sys.stdout.flush()
sys.exit(3 if SCENARIO == "exit-3" else 0)
