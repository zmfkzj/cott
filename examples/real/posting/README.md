# https://github.com/darrenburns/posting

Clean-room Cott reimplementation of Posting's core HTTP exchange as a one-shot command:
`METHOD URL [BODY]` is parsed, sent once, and the response is printed as text. Posting's
Textual UI, collections, environments, scripting, authentication and saved requests are not
reimplemented. Python only adapts console I/O (`python/posting_cli.py`); the HTTP transport is
the agent-generated `send_request` implementation.

## Run

```bash
project=examples/real/posting
PYTHONPATH="$project/generated/python:$project/python" \
  "$project/.venv/bin/python" "$project/python/posting_cli.py" GET https://example.com
```

Output is the status and final URL, one `NAME: VALUE` line per response header, an empty line
and the UTF-8 body (undecodable bytes become U+FFFD). Errors print to stderr with exit status 2.

## Contract

`src/real/posting/client.cott` specifies:

- `parse_method`: the seven standard methods under ASCII case-insensitive comparison; any other
  HTTP token is kept verbatim as `Custom`; anything else is `InvalidRequest`.
- `parse_arguments`: two or three arguments (otherwise `InvalidArguments`, a formal conditional
  error), an empty default body, no headers and a 30000 ms timeout.
- `send_request`: redirects are followed only for GET and HEAD (at most 10), received 4xx/5xx
  statuses are successful responses, the body is replacement-decoded UTF-8, and
  `InvalidRequest` is decided from the request (zero timeout, a URL not starting with `http://`
  or `https://`, blank header names, and the token rules in `doc`). Transport failures are
  `NetworkFailed`.
- `render_response`: the exact line format above.
- `execute`: the composition root `parse_arguments` → `send_request` → `render_response`, with
  stage errors returned unchanged. Two requirements state this composition.

## Evidence

`cott verify` certifies the current snapshot with `observed=23 trust_declaration=0 unknown=0
unobserved=0` clause observations. Pure scenarios check the case-insensitive parsing of all
seven standard methods, exact `Request` values and exact rendering. Scenarios against the
compiler-owned loopback HTTP fixture check a followed relative redirect and its final URL, a 404
returned as a response, replacement decoding, a dropped connection and a read timeout
(`NetworkFailed`), rejected zero timeouts, non-HTTP URLs and blank header names, and the
composed `execute` output and error propagation. `cott requirements` reports both `execute`
requirements as `observed` for the current snapshot: bounded scenario evidence, not proof.

Not observed by Cott evidence:

- Anything the fixture cannot show: it answers only GET and does not echo requests, so the
  method, headers and body sent on the wire, redirect handling for other methods, HEAD bodies and
  HTTPS are specified in `doc` and clauses but not exercised.
- Token validation beyond the `"GET X"` case, and the header CR/LF rule.
