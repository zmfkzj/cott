"""External isolated-process regression program for examples/real/yt-dlp.

This program runs inside Cott's existing Linux sandbox with isolated loopback.
It drives the real public facade (`real.yt_dlp`) and the authored `app.py`
entrypoint against a local 127.0.0.1 HTTP server and scratch directories.
Its output is `external_program_regression` evidence about that one program
tree. It is never Cott scenario evidence and never changes a generation record.
"""

import argparse
import http.server
import json
import os
import subprocess
import sys
import threading
import urllib.parse
from pathlib import Path

EVIDENCE_KIND = "external_program_regression"
MEDIA_PATH = "/media/clip.mp4"
MISSING_PATH = "/media/missing.mp4"
INVALID_URL = "not a url"
FIXTURE_BYTES = b"cott yt-dlp external regression\x00\r\n\xff" + bytes(range(256)) * 3
CLI_TIMEOUT_SECONDS = 90
VERIFIED_SUBJECT = "cott deploy output of the verified examples/real/yt-dlp snapshot"
DEFECT_SUBJECT = (
    "throwaway copy of examples/real/yt-dlp, not example verification: one hand-written defect is "
    "compiler-bound through [target.python.implementations]; the lockfile remains selected, and "
    "every other stage is the example's accepted implementation behind real public facades"
)


class Refusal(Exception):
    pass


class CheckFailure(Exception):
    def __init__(self, reason, detail):
        super().__init__(reason)
        self.reason = reason
        self.detail = detail


def fail(reason, expected, actual):
    raise CheckFailure(reason, f"expected {expected!r}, got {actual!r}"[:600])


class FixtureServer:
    """Loopback media origin; records every request as (method, path)."""

    def __init__(self):
        self.requests = []
        lock = threading.Lock()
        outer = self

        class Handler(http.server.BaseHTTPRequestHandler):
            def log_message(self, *_):
                pass

            def respond(self, body):
                path = urllib.parse.urlsplit(self.path).path
                with lock:
                    outer.requests.append((self.command, path))
                if path == MEDIA_PATH:
                    self.send_response(200)
                    self.send_header("Content-Type", "video/mp4")
                    self.send_header("Content-Length", str(len(FIXTURE_BYTES)))
                    self.end_headers()
                    if body:
                        self.wfile.write(FIXTURE_BYTES)
                    return
                self.send_response(404)
                self.send_header("Content-Length", "0")
                self.end_headers()

            def do_HEAD(self):
                self.respond(False)

            def do_GET(self):
                self.respond(True)

        self.lock = lock
        self.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    @property
    def origin(self):
        return f"http://127.0.0.1:{self.server.server_port}"

    def mark(self):
        with self.lock:
            return len(self.requests)

    def since(self, mark):
        with self.lock:
            return list(self.requests[mark:])

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *_):
        self.server.shutdown()
        self.server.server_close()
        self.thread.join(timeout=1)


def require_isolated_loopback():
    try:
        lines = Path("/proc/net/dev").read_text().splitlines()[2:]
    except OSError as error:
        raise Refusal(f"cannot inspect network namespace: {error}") from error
    interfaces = sorted(line.split(":", 1)[0].strip() for line in lines if ":" in line)
    if interfaces != ["lo"]:
        raise Refusal(f"network namespace is not isolated loopback: {interfaces}")


def require_certified_record(python_root):
    record_path = python_root.parent / "generation.json"
    try:
        record = json.loads(record_path.read_bytes())
        current = record["current"]
        snapshot = record["snapshots"][current]
    except (OSError, ValueError, KeyError, TypeError) as error:
        raise Refusal(f"unreadable generation record {record_path}: {error}") from error
    if snapshot.get("verified") is not True or record.get("last_verified") != current:
        raise Refusal("generation record is not a verified current snapshot")
    if snapshot.get("unresolved"):
        raise Refusal("generation record has unresolved callables")


def tree(directory):
    files = {}
    for path in sorted(directory.rglob("*")):
        relative = path.relative_to(directory).as_posix()
        if path.is_symlink():
            files[relative] = b"<symlink>"
        elif path.is_file():
            files[relative] = path.read_bytes()
        elif path.is_dir() and not any(path.iterdir()):
            files[relative + "/"] = b""
    return files


def item_tuple(item):
    return (item.url, item.id, item.title, item.ext, int(item.playlist_index))


def rendered_line(item):
    url, identifier, title, ext, index = item
    value = {"url": url, "id": identifier, "title": title, "ext": ext, "playlist_index": index}
    return json.dumps(value, ensure_ascii=False, separators=(",", ":"))


class Program:
    def __init__(self, python_root, app, work, server):
        sys.path.insert(0, str(python_root))
        import cott_runtime
        import real.yt_dlp as facade

        self.runtime = cott_runtime
        self.facade = facade
        self.python_root = python_root
        self.app = app
        self.work = work
        self.server = server
        self.media_url = server.origin + MEDIA_PATH
        self.missing_url = server.origin + MISSING_PATH
        self.expected_item = (self.media_url, "clip", "clip.mp4", "mp4", 1)
        self.expected_line = rendered_line(self.expected_item)
        self.counter = 0

    def directory(self, label):
        self.counter += 1
        path = self.work / f"{self.counter:02d}-{label}"
        path.mkdir()
        return path

    def request(self, url, simulation, directory, template):
        """The run contract's CLI defaults with only the stated overrides."""
        f = self.facade
        empty = self.runtime.CottList
        return f.ExecutionRequest(
            inputs=empty(values=[f.CliInput(kind=f.InputKind_Argument(), value=url)]),
            network=f.NetworkPolicy(proxy_mode=f.ProxyMode_Direct(), proxy="", socket_timeout_ms=30000, source_address="", force_ipv4=False, force_ipv6=False, geo_mode=f.GeoBypassMode_Default(), geo_country="", geo_ip_block=""),
            authentication=f.Authentication(kind=f.AuthenticationKind_Anonymous(), username="", password="", netrc_location=Path("."), cookie_file=Path("."), browser="", profile=""),
            playlist=f.PlaylistRequest(mode=f.PlaylistMode_Playlist(), ranges=empty(values=[]), start=0, end=0, items="", reverse=False, random=False),
            live=f.LiveRequest(mode=f.LiveMode_Default(), wait_for_video_ms=0, concurrent_fragments=1),
            video_filter=f.VideoFilterRequest(date_after="", date_before="", min_views=0, max_views=0, age_limit=0, match_filter="", reject_live=False, include_ads=True),
            shortcut=f.ShortcutRequest(kind=f.ShortcutKind_Url(), query="", limit=1),
            formats=f.FormatRequest(selector="", containers=empty(values=[]), sort_fields=empty(values=[]), merge_output_format="", min_file_size=0, max_file_size=104857600, prefer_free_formats=False),
            subtitles=f.SubtitleRequest(mode=f.SubtitleMode_None(), languages=empty(values=[]), formats=empty(values=[]), convert_format="", embed=False),
            thumbnails=f.ThumbnailRequest(write=False, formats=empty(values=[]), convert_format="", embed=False),
            metadata=f.MetadataRequest(write_info_json=False, write_description=False, write_comments=False, write_playlist_metadata=False, embed=False),
            output=f.OutputRequest(template=template, home=directory, temp=Path(".tmp"), output=directory, missing_placeholder="NA", restrict_filenames=False, windows_filenames=False, trim_filename_bytes=0),
            archive=f.ArchiveRequest(path=Path("."), break_on_existing=False, force_write_archive=False),
            fragments=f.FragmentPolicy(concurrent_fragments=1, buffer_size=65536, chunk_size=104857600, rate_limit_bytes_per_second=0, retries=3, fragment_retries=3, file_access_retries=3, continue_download=True, part_files=True),
            post_processing=f.PostProcessRequest(kinds=empty(values=[]), audio_format="", video_format="", sponsorblock_categories=empty(values=[]), external_tool=self.runtime.Nothing()),
            simulation=simulation,
            json_mode=f.JsonMode_Lines(),
            update=f.UpdateRequest(policy=f.UpdatePolicy_Never(), channel="", target=Path(".")),
            presentation=f.PresentationRequest(level=f.LogLevel_Info(), progress=True, newline_progress=False, color=True, dump_pages=False, write_pages=False, log_file=Path(".")),
            workarounds=f.WorkaroundPolicy(certificate=f.CertificatePolicy_Verify(), force_generic_extractor=False, legacy_server_connect=False, extractor_args=empty(values=[])),
        )

    def ok_report(self, result):
        if type(result) is self.runtime.Err:
            fail("unexpected_error", "Ok(ExecutionReport)", repr(result.error))
        return result.value

    def expect_report(self, report, simulated):
        selected = [item_tuple(item) for item in report.selected]
        if selected != [self.expected_item]:
            fail("selected_mismatch", [self.expected_item], selected)
        planned = [item_tuple(item) for item in report.downloads.items]
        if planned != [self.expected_item] or report.downloads.stopped_on_archive is not False:
            fail("plan_mismatch", ([self.expected_item], False), (planned, report.downloads.stopped_on_archive))
        if report.rendered != self.expected_line:
            fail("rendered_mismatch", self.expected_line, report.rendered)
        if report.simulated is not simulated:
            fail("simulated_mismatch", simulated, report.simulated)

    def expect_error(self, result, name, fields):
        if type(result) is self.runtime.Ok:
            fail("unexpected_success", name, repr(result.value)[:300])
        error = result.error
        actual = (type(error).__name__, {key: getattr(error, key, None) for key in fields})
        if actual != (name, fields):
            fail("error_mismatch", (name, fields), actual)

    def expect_files(self, directory, expected):
        actual = tree(directory)
        if sorted(actual) != sorted(expected):
            fail("files_mismatch", sorted(expected), sorted(actual))
        for name, data in expected.items():
            if actual[name] != data:
                fail("bytes_mismatch", f"{name}: {len(data)} fixture bytes", f"{len(actual[name])} other bytes")

    def expect_transfers(self, requests, count):
        transfers = sum(1 for request in requests if request == ("GET", MEDIA_PATH))
        if transfers != count:
            fail("transfer_count" if count else "unexpected_transfer", count, requests)

    def simulate_reports_discovered_media(self):
        directory = self.directory("simulate")
        mark = self.server.mark()
        result = self.facade.execute(self.request(self.media_url, self.facade.SimulationMode_Simulate(), directory, "%(id)s.%(ext)s"))
        requests = self.server.since(mark)
        self.expect_report(self.ok_report(result), True)
        if not any(path == MEDIA_PATH for _, path in requests):
            fail("discovery_not_requested", MEDIA_PATH, requests)
        self.expect_transfers(requests, 0)
        self.expect_files(directory, {})

    def download_writes_fixture_bytes(self):
        directory = self.directory("download")
        mark = self.server.mark()
        result = self.facade.execute(self.request(self.media_url, self.facade.SimulationMode_Download(), directory, "%(id)s.%(ext)s"))
        requests = self.server.since(mark)
        report = self.ok_report(result)
        self.expect_files(directory, {"clip.mp4": FIXTURE_BYTES})
        self.expect_transfers(requests, 1)
        self.expect_report(report, False)

    def invalid_url_is_unsupported(self):
        directory = self.directory("invalid-url")
        mark = self.server.mark()
        result = self.facade.execute(self.request(INVALID_URL, self.facade.SimulationMode_Download(), directory, "%(id)s.%(ext)s"))
        self.expect_error(result, "MediaError_UnsupportedUrl", {})
        requests = self.server.since(mark)
        if requests:
            fail("unexpected_request", [], requests)
        self.expect_files(directory, {})

    def missing_media_reports_http_status(self):
        directory = self.directory("missing-media")
        mark = self.server.mark()
        result = self.facade.execute(self.request(self.missing_url, self.facade.SimulationMode_Download(), directory, "%(id)s.%(ext)s"))
        self.expect_error(result, "MediaError_HttpStatus", {"status": 404})
        if any(method == "GET" for method, _ in self.server.since(mark)):
            fail("unexpected_transfer", "no GET", self.server.since(mark))
        self.expect_files(directory, {})

    def cli(self, directory, argument):
        return subprocess.run(
            [sys.executable, str(self.app), argument],
            cwd=directory,
            env=dict(os.environ),
            stdin=subprocess.DEVNULL,
            capture_output=True,
            timeout=CLI_TIMEOUT_SECONDS,
            check=False,
        )

    def cli_run_downloads_and_prints_report(self):
        directory = self.directory("cli-download")
        mark = self.server.mark()
        completed = self.cli(directory, self.media_url)
        requests = self.server.since(mark)
        if completed.returncode != 0:
            fail("exit_status", 0, (completed.returncode, completed.stderr[-300:]))
        expected_stdout = (self.expected_line + "\n").encode()
        if completed.stdout != expected_stdout:
            fail("stdout_mismatch", expected_stdout, completed.stdout[:600])
        self.expect_files(directory, {"clip.mp4.mp4": FIXTURE_BYTES})
        self.expect_transfers(requests, 1)

    def cli_run_invalid_url_fails(self):
        directory = self.directory("cli-invalid-url")
        mark = self.server.mark()
        completed = self.cli(directory, INVALID_URL)
        if completed.returncode != 1:
            fail("exit_status", 1, (completed.returncode, completed.stdout[:300]))
        if completed.stdout != b"":
            fail("stdout_mismatch", b"", completed.stdout[:600])
        if completed.stderr not in (b"media operation failed", b"media operation failed\n"):
            fail("stderr_mismatch", b"media operation failed\n", completed.stderr[-600:])
        requests = self.server.since(mark)
        if requests:
            fail("unexpected_request", [], requests)
        self.expect_files(directory, {})


CHECKS = [
    ("execute.simulate_reports_discovered_media", "simulate_reports_discovered_media"),
    ("execute.download_writes_fixture_bytes", "download_writes_fixture_bytes"),
    ("execute.invalid_url_is_unsupported", "invalid_url_is_unsupported"),
    ("execute.missing_media_reports_http_status", "missing_media_reports_http_status"),
    ("cli.run_downloads_and_prints_report", "cli_run_downloads_and_prints_report"),
    ("cli.run_invalid_url_fails", "cli_run_invalid_url_fails"),
]


def run_check(identifier, action):
    try:
        action()
    except CheckFailure as failure:
        return {"id": identifier, "passed": False, "reason": failure.reason, "detail": failure.detail}
    except subprocess.TimeoutExpired:
        return {"id": identifier, "passed": False, "reason": "timeout", "detail": f"CLI exceeded {CLI_TIMEOUT_SECONDS}s"}
    except Exception as error:
        reason = "contract_violation" if type(error).__name__ == "CottContractViolation" else "exception"
        return {"id": identifier, "passed": False, "reason": reason, "detail": f"{type(error).__name__}: {error}"[:600]}
    return {"id": identifier, "passed": True, "reason": None, "detail": ""}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--python-root", required=True, type=Path)
    parser.add_argument("--app", required=True, type=Path)
    parser.add_argument("--work", required=True, type=Path)
    parser.add_argument("--subject", required=True)
    arguments = parser.parse_args()
    report = {
        "evidence_kind": EVIDENCE_KIND,
        "cott_scenario_evidence": False,
        "subject": arguments.subject,
        "subject_description": None,
        "verdict": "refused",
        "refusal": None,
        "checks": [],
    }
    try:
        require_isolated_loopback()
        if arguments.subject == "verified-deployment":
            report["subject_description"] = VERIFIED_SUBJECT
            require_certified_record(arguments.python_root)
        elif arguments.subject.startswith("defect-fixture:"):
            report["subject_description"] = DEFECT_SUBJECT
        else:
            raise Refusal(f"unknown subject {arguments.subject!r}")
        with FixtureServer() as server:
            programs = []
            imported = run_check("import.public_facade", lambda: programs.append(Program(arguments.python_root, arguments.app, arguments.work, server)))
            report["checks"] = [imported]
            if programs:
                report["checks"] += [run_check(identifier, getattr(programs[0], method)) for identifier, method in CHECKS]
    except Refusal as refusal:
        report["refusal"] = str(refusal)
        print(json.dumps(report, sort_keys=True), flush=True)
        return 2
    passed = all(check["passed"] for check in report["checks"])
    report["verdict"] = "passed" if passed else "failed"
    print(json.dumps(report, sort_keys=True), flush=True)
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main())
