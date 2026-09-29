#!/usr/bin/env python3
"""Python half of the posting differential harness.

Calls the public facade ``real.posting.client`` for every case in ``--cases`` and prints one
normalized JSON line per case on stdout (see README.md for the normal form).  It must run
under the project interpreter with ``PYTHONPATH=<project>/generated/python``; ``run.py`` does
that.  Diagnostics go to stderr; anything the facade itself prints is diverted to stderr so
the result stream stays clean.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import threading
import time
import traceback

# Reserve the real stdout for result lines before anything else can print to it.
_RESULTS = os.fdopen(os.dup(1), "w", encoding="ascii", newline="\n", buffering=1)
os.dup2(2, 1)

from cott_runtime import CottContractViolation, CottList, Err, Ok  # noqa: E402
from real.posting.client import (  # noqa: E402
    Header,
    HttpMethod_Custom,
    HttpMethod_Delete,
    HttpMethod_Get,
    HttpMethod_Head,
    HttpMethod_Options,
    HttpMethod_Patch,
    HttpMethod_Post,
    HttpMethod_Put,
    PostingError_InvalidArguments,
    PostingError_InvalidRequest,
    PostingError_NetworkFailed,
    Request,
    Response,
    execute,
    parse_arguments,
    parse_method,
    render_response,
    send_request,
)

DEFAULT_DEADLINE_S = 60.0

_STANDARD = {
    "Get": HttpMethod_Get,
    "Head": HttpMethod_Head,
    "Post": HttpMethod_Post,
    "Put": HttpMethod_Put,
    "Patch": HttpMethod_Patch,
    "Delete": HttpMethod_Delete,
    "Options": HttpMethod_Options,
}
_ERRORS = {
    PostingError_InvalidArguments: "InvalidArguments",
    PostingError_InvalidRequest: "InvalidRequest",
    PostingError_NetworkFailed: "NetworkFailed",
}


def resolve(value, variables: dict[str, str]):
    """Replace ``{NAME}`` placeholders in every string of a decoded JSON value."""
    if isinstance(value, str):
        for name, text in variables.items():
            value = value.replace("{" + name + "}", text)
        return value
    if isinstance(value, list):
        return [resolve(item, variables) for item in value]
    if isinstance(value, dict):
        return {key: resolve(item, variables) for key, item in value.items()}
    return value


# ---- building typed inputs ------------------------------------------------------------


def build_method(spec):
    variant, name = (spec, None) if isinstance(spec, str) else (spec["variant"], spec.get("name"))
    if variant == "Custom":
        return HttpMethod_Custom(name=name)
    return _STANDARD[variant]()


def build_headers(pairs) -> CottList:
    return CottList(values=tuple(Header(name=name, value=value) for name, value in pairs))


def build_request(spec) -> Request:
    return Request(
        method=build_method(spec["method"]),
        url=spec["url"],
        headers=build_headers(spec["headers"]),
        body=spec["body"],
        timeout_ms=spec["timeout_ms"],
    )


def build_response(spec) -> Response:
    return Response(
        status=spec["status"],
        url=spec["url"],
        headers=build_headers(spec["headers"]),
        body=spec["body"],
    )


# ---- normalizing outputs --------------------------------------------------------------


def norm_method(method) -> dict:
    if isinstance(method, HttpMethod_Custom):
        return {"variant": "Custom", "name": method.name}
    for variant, cls in _STANDARD.items():
        if isinstance(method, cls):
            return {"variant": variant}
    return {"unexpected_type": type(method).__name__}


def norm_headers(headers) -> list:
    return [{"name": header.name, "value": header.value} for header in headers]


def norm_body(body: str, digest: bool) -> dict:
    if not digest:
        return {"body": body}
    data = body.encode("utf-8", errors="surrogatepass")
    return {"body_digest": {"utf8_len": len(data), "sha256": hashlib.sha256(data).hexdigest()}}


def norm_value(value, digest: bool) -> object:
    if isinstance(value, str):
        return value
    if isinstance(value, Request):
        return {
            "method": norm_method(value.method),
            "url": value.url,
            "headers": norm_headers(value.headers),
            "body": value.body,
            "timeout_ms": int(value.timeout_ms),
        }
    if isinstance(value, Response):
        return {
            "status": int(value.status),
            "url": value.url,
            "headers": norm_headers(value.headers),
            **norm_body(value.body, digest),
        }
    if isinstance(value, (HttpMethod_Custom, *_STANDARD.values())):
        return norm_method(value)
    return {"unexpected_type": type(value).__name__}


def norm_error(error) -> dict:
    variant = next((name for cls, name in _ERRORS.items() if isinstance(error, cls)), None)
    if variant is None:
        return {"unexpected_type": type(error).__name__}
    return {"variant": variant, "message_present": bool(error.message)}


def norm_result(result, digest: bool = False) -> dict:
    if isinstance(result, Ok):
        return {"tag": "Ok", "value": norm_value(result.value, digest)}
    if isinstance(result, Err):
        return {"tag": "Err", "error": norm_error(result.error)}
    if isinstance(result, str):
        return {"tag": "Str", "value": result}
    return {"tag": "Unexpected", "type": type(result).__name__}


def norm_exception(error: BaseException) -> dict:
    """A boundary violation is an input the ABI rejects before any implementation code runs (an unpaired surrogate in a
    Str, say); anything else that is raised, including a violation of the implementation's return value ("$.return"
    paths) or of an ensures/error clause, is a fault of the implementation and stays a Raise."""
    if isinstance(error, CottContractViolation) and error.phase == "validation" and not error.message.startswith("$.return"):
        return {"tag": "Violation", "phase": error.phase}
    out = {"tag": "Raise", "type": type(error).__name__}
    if isinstance(error, CottContractViolation):
        out["phase"] = error.phase
        out["clause"] = error.clause
    return out


# ---- running cases --------------------------------------------------------------------


def prepare(case):
    """Check the case data eagerly and return the thunk that calls the facade.

    A ``KeyError``/``TypeError`` here is a malformed case (driver error); anything raised by the
    thunk, including value-construction violations at the ABI boundary, is a result.
    """
    fn = case["fn"]
    digest = bool(case.get("body_digest"))
    if fn == "parse_method":
        source = case["source"]
        return lambda: norm_result(parse_method(source))
    if fn in ("parse_arguments", "execute"):
        arguments = tuple(case["arguments"])
        call = parse_arguments if fn == "parse_arguments" else execute
        return lambda: norm_result(call(CottList(values=arguments)))
    if fn == "send_request":
        spec = case["request"]
        _require(spec, "method", "url", "headers", "body", "timeout_ms")
        return lambda: norm_result(send_request(build_request(spec)), digest)
    if fn == "render_response":
        spec = case["response"]
        _require(spec, "status", "url", "headers", "body")
        return lambda: norm_result(render_response(build_response(spec)))
    raise ValueError(f"unknown fn {fn!r}")


def _require(spec: dict, *keys: str) -> None:
    missing = [key for key in keys if key not in spec]
    if missing:
        raise KeyError(f"missing {missing}")


class _Outcome:
    result: dict | None = None
    driver_error: str | None = None


def run_case(case, deadline_s: float) -> _Outcome:
    """Run one case in a daemon thread so a hung implementation cannot stall the run."""
    outcome = _Outcome()
    try:
        thunk = prepare(case)
    except (KeyError, TypeError, ValueError) as error:
        outcome.driver_error = "malformed case: " + "".join(traceback.format_exception_only(type(error), error)).strip()
        return outcome

    def work() -> None:
        try:
            outcome.result = thunk()
        except Exception as error:  # noqa: BLE001 - a facade raise is a result, not a driver failure
            outcome.result = norm_exception(error)
            traceback.print_exc(file=sys.stderr)

    thread = threading.Thread(target=work, name=case["id"], daemon=True)
    thread.start()
    thread.join(deadline_s)
    if thread.is_alive():
        outcome = _Outcome()
        outcome.driver_error = f"no result within {deadline_s:g}s (case abandoned)"
    return outcome


def warm_up(variables: dict[str, str]) -> None:
    """Pay one-time import/connection costs before any case is timed."""
    try:
        parse_method("GET")
        send_request(
            Request(
                method=HttpMethod_Get(),
                url=variables["A"] + "/text",
                headers=CottList(values=()),
                body="",
                timeout_ms=10000,
            )
        )
    except Exception:  # noqa: BLE001 - warm-up outcome is irrelevant
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cases", required=True)
    parser.add_argument("--vars", required=True)
    args = parser.parse_args()
    with open(args.cases, encoding="utf-8") as handle:
        cases = json.load(handle)
    with open(args.vars, encoding="utf-8") as handle:
        variables = json.load(handle)
    warm_up(variables)
    for case in cases:
        case = resolve(case, variables)
        started = time.monotonic()
        outcome = run_case(case, float(case.get("deadline_s", DEFAULT_DEADLINE_S)))
        record: dict = {"case": case["id"], "ms": round((time.monotonic() - started) * 1000)}
        if outcome.result is not None:
            record["result"] = outcome.result
        else:
            record["driver_error"] = outcome.driver_error
        _RESULTS.write(json.dumps(record, ensure_ascii=True, separators=(",", ":")) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
