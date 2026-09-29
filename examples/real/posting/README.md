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

Or install the deployed wheel (console script `posting-cott` from `python/pyproject.toml`):

```bash
cott deploy --project examples/real/posting --output /tmp/posting-dist
python3.14 -m venv /tmp/posting-venv
/tmp/posting-venv/bin/pip install /tmp/posting-dist/real_posting-0.1.0-py3-none-any.whl
/tmp/posting-venv/bin/posting-cott GET https://example.com
```

Output is the status and final URL, one `NAME: VALUE` line per response header, an empty line
and the UTF-8 body (undecodable bytes become U+FFFD). Errors print to stderr with exit status 2, including
arguments that are not valid UTF-8; a closed stdout (e.g. `| head`) exits 141 without a traceback.

## Contract

`src/real/posting/client.cott` specifies:

- `parse_method`: the seven standard methods under ASCII case-insensitive comparison; any other
  HTTP token is kept verbatim as `Custom`; anything else is `InvalidRequest`.
- `parse_arguments`: two or three arguments (otherwise `InvalidArguments`, a formal conditional
  error), an empty default body, no headers and a 30000 ms timeout.
- `send_request`: the URL may hold only RFC 3986 characters (anything else, or a `%` without
  two hex digits, is `InvalidRequest` before any connection). The request target keeps the
  path, an even empty query and percent-escapes as written and never the fragment; `Host` is
  the URL host as written plus a non-default port unless the caller supplies one; URL
  userinfo is neither sent nor used. Redirects are followed only for GET and HEAD (at most
  10), resolved by strict RFC 3986 section 5.2 (dot segments, query-only and empty-segment
  cases), and never from `https` to `http` or to a non-http(s) or invalid `Location` (that
  3xx is returned). On a followed cross-origin redirect (scheme and host case-insensitive,
  port after the scheme default) `Authorization`, `Cookie`, `Proxy-Authorization` and `Host`
  are dropped. Received 4xx/5xx statuses are successful responses, the body is limited to
  `MAX_RESPONSE_BODY_BYTES` (64 MiB) and decoded as UTF-8 with one U+FFFD per maximal subpart
  of an ill-formed sequence (BOM and NUL kept). `InvalidRequest` is also decided from the
  request (zero timeout, non-`http(s)` URL or no host, blank or non-token header names, the
  token rules in `doc`). Transport failures, oversized bodies, connections closed before the
  header block ends, before all `Content-Length` bytes or before the final chunk, a response
  without an HTTP/1.x status line and a header line without a colon are `NetworkFailed`
  (no partial `Response`). The credential rule is requirement
  `SEND_REQUEST_STRIPS_CREDENTIALS_ACROSS_ORIGINS`, `unverified`: the fixture cannot observe
  sent headers.
- `render_response`: the exact line format above.
- `execute`: the composition root `parse_arguments` → `send_request` → `render_response`, with
  stage errors returned unchanged. Two requirements state this composition.

## Evidence

`cott verify` certifies the current snapshot with `observed=23 trust_declaration=0 unknown=0
unobserved=0` clause observations. Pure scenarios check the case-insensitive parsing of all
seven standard methods, exact `Request` values and exact rendering. Scenarios against the
compiler-owned loopback HTTP fixture check a followed relative redirect and its final URL, a 404
returned as a response, replacement decoding (including `ED A0 80` becoming three U+FFFD), URLs
with a space, non-ASCII character, `<` or a bad `%` escape rejected before connecting, a dropped
connection and a read timeout
(`NetworkFailed`), rejected zero timeouts, non-HTTP URLs and blank header names, and the
composed `execute` output and error propagation. `cott requirements` reports both `execute`
requirements as `observed` for the current snapshot: bounded scenario evidence, not proof.

The strict coverage policy selects all 23 formal clauses across the five callables.
The latest regeneration and `verify` run passed with `selected=23` and no policy
violations; none of `unobserved`, `trust_declaration` or `unknown` is allowed.
The `execute` argument-count rejection is now exercised by an actual empty-argument
facade call. Static proofs remain separate and cannot satisfy execution coverage.
The non-GET/HEAD postconditions can still hold vacuously in GET scenarios;
bounded observation does not establish every branch or close the gaps below.

Not observed by Cott evidence:

- Anything the fixture cannot show: it answers only GET with absolute redirect locations and
  does not echo requests or truncate bodies, so the method, headers, request target and `Host`
  sent on the wire, relative, dot-segment and query-only `Location` resolution, truncated
  header blocks, `Content-Length` bodies and chunked bodies, redirect handling for other
  methods, HEAD bodies and HTTPS are specified in `doc` but not exercised.
- Token validation beyond the `"GET X"` case, and the header CR/LF rule.

The differential harness of the Kotlin port (`examples/kotlin/real/posting/diff/`) exercises
these behaviors against loopback servers for both implementations (1652 contract expectations,
all met in the last run). That is external regression evidence, not Cott scenario evidence.
