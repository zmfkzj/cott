"""Real stdio LSP and CLI comparison; no target toolchain or provider required."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile

binary = sys.argv[1]
with tempfile.TemporaryDirectory(prefix="cott-lsp-wire-") as temp:
    root = Path(temp)
    (root / "src").mkdir()
    (root / "python").mkdir()
    (root / "cott.toml").write_text('''[project]
name = "wire"
version = "0.1.0"
source = "src"
[target.python]
source = "python"
generated = "generated/python"
stubs = "generated/stubs"
interpreter = "python"
type_checker = "basedpyright"
runtime_validation = "boundary"
''')
    (root / "python/pyproject.toml").write_text('[project]\nname="wire"\nversion="0.1.0"\nrequires-python=">=3.14.6,<3.15"\ndependencies=[]\n')
    source = 'module app\n\nfn run(value I32) -> I32\n'
    path = root / "src/app.cott"
    path.write_text(source)
    human = subprocess.run([binary, "check", "--project", temp], capture_output=True, text=True, timeout=20)
    machine = subprocess.run([binary, "check", "--project", temp, "--format", "json"], capture_output=True, text=True, timeout=20)
    assert human.returncode == machine.returncode == 3, (human.stderr, machine.stderr)
    report = json.loads(machine.stdout)
    diagnostic = next(d for d in report["diagnostics"] if d["expected"] == "Colon")
    assert diagnostic["actual"] == 'Name("I32")', diagnostic
    for field in ("expected", "actual", "reason"):
        assert f'  {field}: {diagnostic[field]}' in human.stderr
    assert diagnostic["help"] and f'  help: {diagnostic["help"][0]}' in human.stderr
    assert set(diagnostic) == {"code", "severity", "message", "span", "expected", "actual", "reason", "help", "related", "source_order"}
    process = subprocess.Popen([binary, "lsp"], stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    def send(message):
        data = json.dumps({"jsonrpc": "2.0", **message}).encode()
        process.stdin.write(f"Content-Length: {len(data)}\r\n\r\n".encode() + data)
        process.stdin.flush()
    def receive():
        headers = {}
        while True:
            line = process.stdout.readline()
            assert line, process.stderr.read().decode()
            if line == b"\r\n":
                break
            key, value = line.decode().split(":", 1)
            headers[key.lower()] = value.strip()
        return json.loads(process.stdout.read(int(headers["content-length"])))
    try:
        send({"id": 1, "method": "initialize", "params": {"capabilities": {}}})
        while receive().get("id") != 1:
            pass
        send({"method": "initialized", "params": {}})
        send({"method": "textDocument/didOpen", "params": {"textDocument": {
            "uri": path.as_uri(), "languageId": "cott", "version": 1, "text": source}}})
        while True:
            message = receive()
            if message.get("method") == "textDocument/publishDiagnostics":
                break
        assert message["params"]["uri"] == path.as_uri()
        lsp = next(d for d in message["params"]["diagnostics"] if "  expected: Colon" in d["message"])
        assert lsp["code"] == diagnostic["code"]
        assert lsp["message"].splitlines()[0] == diagnostic["message"]
        for field in ("expected", "actual", "reason"):
            assert f'  {field}: {diagnostic[field]}' in lsp["message"]
        assert lsp["range"]["start"]["line"] == diagnostic["span"]["start_line"] - 1
        assert lsp["range"]["start"]["character"] == diagnostic["span"]["start_column"] - 1
        send({"id": 2, "method": "shutdown", "params": None})
        while receive().get("id") != 2:
            pass
        send({"method": "exit"})
        process.stdin.close()
        process.wait(timeout=10)
    finally:
        if process.poll() is None:
            process.kill()
            process.wait()
print("CLI/JSON/LSP diagnostic code, details and original Cott range agree")
