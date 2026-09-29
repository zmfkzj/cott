# Differential harness: Python vs Kotlin `real.posting.client`

Calls the verified Python facade `real.posting.client` (`examples/real/posting`) and the Kotlin facade
`real.posting.client` (`generated/library/cott-module.jar` of this project) with identical inputs and answers two
questions per case: do the two implementations **agree**, and does each **meet the contract**?

```bash
python3 examples/kotlin/real/posting/diff/run.py            # everything; exit 0 iff every case passes
```

The command works from any directory. It needs the Python project venv, `kotlinc >= 2.2.10` and a JDK >= 17
(`~/.local/opt/kotlinc/bin` and `~/.local/opt/jdk17/bin` are put in front of `PATH` when they exist). A full run takes
about a minute, most of it two 64 MiB bodies in the Python reference; `--fast` skips them.

| option | effect |
| --- | --- |
| `--python-only` / `--kotlin-only` | run only one half; checks the same expectations (nothing to compare) |
| `--only REGEX` / `--skip REGEX` | select cases by id (repeatable), e.g. `--only 'rfc3986|resolve'` |
| `--only-tag TAG` | select cases carrying a tag (`slow`, `edge`, `ipv6`, `port80`) |
| `--fast` | skip cases tagged `slow` (two 64 MiB bodies at ~22 s each in the Python reference, and a 2 s drip) |
| `--no-edge` | skip cases tagged `edge` (behavior the contract leaves open, see below) |
| `--list` / `--dump-cases FILE` | print the selected ids / write the selected cases as JSON |
| `-v` | per-case timings, untruncated values |
| `--cases FILE` | run a JSON case list instead of the built-in table |
| `--module-jar FILE`, `--coroutines-jar FILE` | other module / coroutines JAR (default: `generated/library/…`, `generated/runtime-libs/…`, else the JAR bundled with `kotlinc`) |
| `--rebuild` | force recompiling `Driver.kt` (normally cached in `build/`, keyed by `Driver.kt`, the JARs and the compiler) |
| `--no-namespace` | do not run the `port80` cases in a private network namespace (see below) |

## Rows

| row | meaning |
| --- | --- |
| `PASS` | both normalized results are equal **and** both meet the case's `expect` |
| `DIFF` | the results differ: both values, the differing paths, which side meets the expectation and the case `note` are shown |
| `FAIL` | the results agree but violate the expectation (so both violate it), or an implementation raised |

A `DIFF` on a case tagged `edge` is a difference in behavior the contract leaves open; the summary counts those
separately. Exit status: `0` every case passes; `1` any DIFF, FAIL, driver error or fixture violation; `2` the harness
itself could not run (missing tool, `Driver.kt` does not compile against the JAR, bad case data); `3` the Kotlin half is
pending because the module JAR does not exist (the Python half still runs and must be clean).

## Where the expected values come from

Every `expect` is derived from the contract text (`src/real/posting/client.cott`) or computed by `oracle.py`, which
transcribes the standards instead of calling any library: RFC 3986 sections 3, 5.2, 5.3 and appendix B (reference
resolution, `remove_dot_segments`, recomposition), Unicode 3.9 Tables 3-7 and 3-8 (maximal-subpart U+FFFD decoding),
the URL-character rule, request-target and Host derivation and origin comparison. `python3 oracle.py` runs its
self-tests: the RFC 3986 section 5.4.1/5.4.2 tables, the two worked examples of 5.2.4, the three examples in the
contract's `send_request` doc, Table 3-8, and 30 000 random byte strings against CPython's decoder (a guard against a
transcription slip, never a source of expectations). No expectation is copied from an implementation's output, and no
case is adjusted to match one.

## Files

| file | role |
| --- | --- |
| `run.py` | orchestrator: starts the fixtures, builds `Driver.kt`, runs both drivers, judges, reports |
| `cases.py` | the case table (about 1 670 cases) with the derivations; `python3 cases.py` prints counts |
| `oracle.py` | the independent oracles and their self-tests |
| `driver.py` | Python half (runs under `examples/real/posting/.venv/bin/python`, `PYTHONPATH=…/generated/python`) |
| `Driver.kt` | Kotlin half (`kotlinc` against the module JAR + coroutines JAR + stdlib, run with `java -cp`) |
| `server.py` | loopback HTTP fixtures; `python3 server.py` starts them by hand and prints the origins |
| `build/` | git-ignored: cached compiled driver JARs (newest 3), raw `*.jsonl` / `*.stderr` of the last run |

Nothing outside `diff/` is written; `generated/` and `kotlin/` are only read.

## How a run works

1. `run.py` starts servers on ephemeral ports: `A`, `B` (a second origin for cross-origin redirects), `N` (must never
   be contacted), `V6` on `[::1]` when that bind works, `127.0.0.1:80` when that bind works, and reserves a bound but
   not listening port `CLOSED` so that connecting to it is refused for the whole run.
2. Both drivers get the same case list and the same variables. Every string in a case may contain `{A}`, `{A_HOST}`,
   `{A_PORT}`, `{B}`, `{B_HOST}`, `{B_PORT}`, `{N}`, `{N_HOST}`, `{CLOSED}`, `{V6}`, `{V6_HOST}`, `{V6_PORT}`; the drivers
   substitute them before calling the facade, and `run.py` turns the ephemeral origins in the results back into
   placeholders, so expectations and results are stable across runs.
3. Each driver makes one unreported warm-up call, then runs the cases one at a time (each on a worker thread with a
   `deadline_s`, default 60 s, so a hung implementation costs one case, not the run) and prints one JSON line per case.
   Python runs first, then Kotlin; the servers see one client at a time and their per-run state is reset in between.
4. **The `port80` cases** (a Host without `:80`, default-port origin comparison) need `127.0.0.1:80`, which an
   unprivileged process cannot bind. When the main pass skips them, `run.py` re-executes itself inside
   `unshare --user --map-root-user --net` (where the port is bindable and `lo` is brought up) for exactly those cases,
   prints that second table and adds a `TOTAL`. Without `unshare` (or with `--no-namespace`) they are listed as skipped
   and the run is not clean. `ipv6` cases run in the main pass when `::1` binds, else they take the same path.

### Normal form (both drivers print exactly this)

```json
{"case":"send_request/get-text","ms":3,"result":{"tag":"Ok","value":{"status":200,"url":"{A}/text","headers":[{"name":"Content-Type","value":"text/plain; charset=utf-8"}],"body":"hello world"}}}
```

* `tag`: `Ok` / `Err` for `Result` returns, `Str` for the plain string of `render_response`, `Violation` for a boundary
  contract violation, `Raise` for anything else the facade raised (`type`, and for `CottContractViolation` its `phase` and
  `clause`).
* **`Violation`** (`{"tag":"Violation","phase":"validation"}`) is an input the ABI rejects before any implementation code
  runs, e.g. a Str holding a lone surrogate: `CottContractViolation` in both runtimes, with `phase == "validation"` and a
  message that does not start with `$.return` (a violation of the implementation's own return value, an `ensures` or an
  `error` clause stays a `Raise`). A `Raise` is an implementation fault and is never a PASS.
* `Ok.value`: `HttpMethod` → `{"variant":"Get"}` or `{"variant":"Custom","name":…}`; `Request` → `{method,url,headers,body,timeout_ms}`;
  `Response` → `{status,url,headers,body}`; headers are `[{name,value}]` in order; `execute` → the string.
* `Err.error` is `{"variant":"InvalidRequest","message_present":true}`. Messages are free text and are **not** compared.
* Cases flagged `body_digest` replace `body` by `{"body_digest":{"utf8_len":N,"sha256":…}}` (hash of the UTF-8 bytes of the
  decoded body); used for the 64 MiB bodies and the read-chunk boundary tests.
* `ms` is informational. A case a driver could not run (malformed data, deadline exceeded) has `driver_error`; that is never a PASS.

The fixture servers never emit `Date` or `Server`, so rendered strings are compared exactly.

## Cases

Each case has `id` (unique, `fn/...`), `fn` and the inputs of that function:

| `fn` | inputs |
| --- | --- |
| `parse_method` | `"source": "get"` |
| `parse_arguments`, `execute` | `"arguments": ["post", "{A}/echo", "body"]` |
| `send_request` | `"request": {"method": "Get" \| {"variant":"Custom","name":"PURGE"}, "url", "headers": [[name, value]…], "body", "timeout_ms"}` |
| `render_response` | `"response": {"status", "url", "headers": [[name, value]…], "body"}` |

Optional: `tags`, `deadline_s`, `body_digest`, `note`, and

* `expect` — assertions over the normalized `result` that **both** sides must meet. Keys are dotted paths (`#` is a
  length, `@json` parses a string as JSON: `value.body.@json.headers.host`); values are compared for equality, except
  `{"$absent": true}` (the key must not exist) and `{"$contains": [...]}` (a string holding every part).
* `ignore` — result paths excluded from the Python/Kotlin comparison because the contract does not define them
  (only the four non-ASCII `Location` cases use it: how header bytes >= 0x80 decode is open).
* An `edge` case has no `expect`: only agreement is checked.

## Fixtures (`server.py`)

Raw HTTP/1.1, one request per connection. The route is the last path segment and parameters are in the query, so
`{A}/dir/redir?status=302&to=../echo` tests relative-Location resolution. `echo` answers JSON with the method, HTTP
version, request target (exactly as received, the request line is never re-parsed), body, and only these request headers
in received order: `Authorization`, `Cookie`, `Proxy-Authorization`, `Host`, `Content-Type`, `X-Keep`, `X-Multi`,
`X-First`, `X-Second`; client defaults (`User-Agent`, `Accept`, …) are deliberately not echoed. Two request headers
change the routing and pass through redirects unchanged:

* `X-Echo: 1` — a path whose last segment names no route (or is empty) is answered like `echo`.
* `X-Mirror: ref=REF` + `X-Mirror-Id` (+ `X-Mirror-At`, default `/b/c/d;p`) — the first request per id at that path is a
  302 with `Location: REF`; every later one answers like `echo`. This mirrors the RFC 3986 base `http://a/b/c/d;p?q`
  on `{A}` (references such as `""`, `#s` or `?q` resolve to the base itself, which a stateless server would loop on).
  These responses carry `X-Target`, the target as received.

The docstring of `server.py` lists every route: plain/unicode/empty bodies, `status?code=`, `binary?hex=`, `charset?cs=`,
`headers`, `redir` (`to`, raw `to_hex`, `nolocation`, `dup`), `chain`, `loop`, `x-out`/`x-bounce`, `drop*` (after the status
line, mid-headers, before/mid body, mid/inside a chunk, mid-terminator), `garbage`, `status-line?hex=`, `bad-header-line`,
`close-delimited`, `chunked`, `chunk-ext`, `chunk-bad-size`, `interim`, `hdr-ows`, `hdr-nonascii`, `slow`, `drip`, `big`.

## What is covered (about 1 670 cases)

* `parse_method`, `parse_arguments`, `render_response`, `execute`: methods in every case pattern, every ASCII character
  alone and after `GET`, every tchar, non-ASCII including the case-folding traps, argument counts, rendering.
* **Rule 1, URL characters:** every character outside the set (the nine printable ones, space, all 33 control
  characters, non-ASCII) and nine malformed `%HH` forms in the path and the fragment (the fragment is never sent but is
  part of the URL); a subset also in the query, userinfo and host; and every valid character verbatim in the path and
  query. All invalid URLs point at server `N`, which must record no connection.
* **Rule 2, request target:** empty path, empty query, `?` inside a fragment, `//` and `///` paths, `%HH`
  verbatim (upper/lower hex, encoded slashes and dots). **Rule 3, Host:** case kept, userinfo neither sent nor used,
  caller `Host` replaces the default and keeps its position, IPv6 brackets, explicit default port.
* **Rule 4, Location:** the RFC 3986 section 5.4.1/5.4.2 tables (all but `//g`, which leaves the server), 61 more
  references from the oracle (empty segments, encoded dots, query/fragment corner cases, absolute and scheme-relative
  forms), base variants (base fragment, empty base path, userinfo, upper-case host), references that resolve to a
  non-http(s) URL or to no host (3xx returned), and Locations with an invalid character or a malformed `%HH` (3xx returned).
* **Rule 5, origins:** port, host name, host case, userinfo, A → B → A round trips, default ports (namespace pass).
* **Rule 6, decoding:** Table 3-8, all 128 single bytes >= 0x80, the boundaries of Table 3-7 for every lead byte
  (second byte just outside, truncation at each length, at the end and before ASCII), BOM and NUL, and multi-byte
  characters across read and chunk boundaries (2-, 3- and 4-byte units at every alignment).
* **Rule 7, failures:** close after the status line, mid-headers, before and inside the body, mid and inside a chunk,
  non-HTTP/1.x status lines, a header line without a colon, refused/unresolvable/TLS-to-plain, read timeout (and per-read
  timeout semantics), and the 64 MiB limit at, and one byte over, in Content-Length and chunked form.
* **Boundary violations:** a lone surrogate in `parse_method`, `parse_arguments`, `render_response` (body, url, header
  name/value), `send_request` (url, body, header, custom method) and `execute`; the Kotlin runtime rejects them and the
  regenerated Python runtime must too.

## Behavior the contract leaves open (`edge` cases: agreement only)

1. `Custom("HEAD")`: sent as `HEAD`; does the client treat the response as body-less or wait for the announced bytes?
2. Dot segments in the *initial* URL (`/a/../echo`): sent as written or normalized? (5.2.4 is stated for Locations.)
3. Two `Location` headers, also when the first is invalid: which one counts?
4. A `Location` spelled `HTTP://…` or `Http://…`: followed? how is `Response.url` spelled?
5. Leading/trailing SP and HTAB around a received header value: trimmed or kept?
6. Received header bytes >= 0x80: decoded as Latin-1 or UTF-8? (The four non-ASCII invalid-`Location` cases ignore
   `Response.headers` for this reason.)
7. Interim 1xx responses (`102 Processing`, `100 Continue`) before the final response.
8. A status line without a reason phrase (`HTTP/1.1 200`).
9. Chunk extensions and trailer fields: ignored, or trailers reported as headers?
10. A non-hexadecimal chunk size.
11. A connection closed after the `0 CRLF` line of a chunked body but before the final empty line.
12. Unusable ports (`:99999`, `:0`, `:abc`, `:0041005`): InvalidRequest or NetworkFailed?
13. A non-ASCII request header value: how it is put on the wire (only CR and LF are rejected).

## Readings of the contract that decide some rows

* An empty `Location:` value carries a Location header whose reference is empty, so it resolves to the base URL
  (`resolve-empty-location-is-the-base`, RFC 3986 section 5.4.1).
* Section 5.2.2 applies `remove_dot_segments` to an absolute or scheme-relative reference too, so `http://h/x/./y/../z`
  becomes `http://h/x/z`.
* `HTTP/1.0 200 OK` is an HTTP/1.x status line (accepted); `HTTP/2 …`, `ICY …`, `HTTP/1.1 abc …` and two- or four-digit
  statuses are NetworkFailed. `!` is a URL character, so `http://exa!mple.invalid/` is a name-resolution failure, not an
  InvalidRequest. A TAB inside a `Location` is a control character: not followed.
* After a followed redirect HEAD stays HEAD as far as the contract shows (`ensures response.body == ""`).

## Not covered

* https → http downgrade refusal, an https default-port Host and Location resolution against an https base: they need a
  TLS listener with a certificate both runtimes trust (possible later with `SSL_CERT_FILE` / `-Djavax.net.ssl.trustStore`
  and an `openssl`-made certificate).
* Connection-attempt timeout (needs an unroutable address), HTTP/2, proxies.
* The RFC 3986 example `//g` (resolves to `http://g`, another host).

## Adding a case

Add it to the matching `group_*` function in `cases.py` (ids are unique and start with `fn/`). Derive `expect` from the
contract text or from `oracle.py`, never from what an implementation returned; if the contract does not say, tag the case
`edge` and add its question to the list above. Check with `python3 run.py --python-only --only 'your/id'`, then run the
full comparison.
