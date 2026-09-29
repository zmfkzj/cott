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
| `--rule REGEX` | select cases by rule label (full match, repeatable): `R1`…`R7`, `D1`…`D14`, `D.*`, … (see below) |
| `--only-tag TAG` | select cases carrying a tag (`slow`, `ipv6`, `port80`, `port65535`) |
| `--fast` | skip cases tagged `slow` (two 64 MiB bodies at ~22 s each in the Python reference, and a 2 s drip) |
| `--list` / `--dump-cases FILE` | print the selected ids / write the selected cases as JSON |
| `-v` | per-case timings, untruncated values |
| `--cases FILE` | run a JSON case list instead of the built-in table |
| `--module-jar FILE`, `--coroutines-jar FILE` | other module / coroutines JAR (default: `generated/library/…`, `generated/runtime-libs/…`, else the JAR bundled with `kotlinc`) |
| `--rebuild` | force recompiling `Driver.kt` (normally cached in `build/`, keyed by `Driver.kt`, the JARs and the compiler) |
| `--no-namespace` | do not run the `port80` / `port65535` / `ipv6` cases in a private network namespace (see below) |

## Rows

| row | meaning |
| --- | --- |
| `PASS` | both normalized results are equal **and** both meet the case's `expect` |
| `DIFF` | the results differ: both values, the differing paths, which side violates the contract and the case `note` are shown |
| `FAIL` | the results agree but violate the expectation (so both violate it), or an implementation raised |

Every case has an `expect`, so there is no "agreement only" row: a behavior the contract does not decide has no case (see
"Not decided" below). The summary ends with `not passing by rule`, the count of non-passing cases per rule label, which is
the quickest way to see which decision an implementation misses. Exit status: `0` every case passes; `1` any DIFF, FAIL,
driver error or fixture violation; `2` the harness itself could not run (missing tool, `Driver.kt` does not compile
against the JAR, bad case data); `3` the Kotlin half is pending because the module JAR does not exist (the Python half
still runs and must be clean).

## Where the expected values come from

Every `expect` is derived from the contract text (`src/real/posting/client.cott`, the `send_request` doc) or computed by
`oracle.py`, which transcribes the standards instead of calling any library: RFC 3986 sections 3, 5.2, 5.3 and appendix B
(reference resolution, `remove_dot_segments`, recomposition), Unicode 3.9 Tables 3-7 and 3-8 (maximal-subpart U+FFFD
decoding), the URL-character rule, request target (dot segments removed), Host and port derivation (decimal value, default
port omitted), origin comparison, the received header lines (token names, SP/HTAB trimming, whole-block ASCII / UTF-8 /
ISO-8859-1 decoding of the values) and the chunk-size line. `python3 oracle.py` runs its self-tests: the RFC 3986 section
5.4.1/5.4.2 tables, the two worked examples of 5.2.4, the examples in the contract's `send_request` doc, Table 3-8, the
port, Host, header-line and chunk-size rules by hand, and randomized comparisons of the UTF-8 decoder (lenient and
strict) and of the header-value rule with CPython's codecs (a guard against a transcription slip, never a source of
expectations). No expectation is copied from an implementation's output, and no case is adjusted to match one.

## Files

| file | role |
| --- | --- |
| `run.py` | orchestrator: starts the fixtures, builds `Driver.kt`, runs both drivers, judges, reports |
| `casekit.py` | the case registry, builders and assertion helpers |
| `cases.py` | the contract rules R1–R7 and the general behavior (about 1 650 cases); `python3 cases.py` prints counts by rule |
| `decisions.py` | the decisions D1–D14 (431 cases), one `group_dN` function per decision |
| `oracle.py` | the independent oracles and their self-tests |
| `driver.py` | Python half (runs under `examples/real/posting/.venv/bin/python`, `PYTHONPATH=…/generated/python`) |
| `Driver.kt` | Kotlin half (`kotlinc` against the module JAR + coroutines JAR + stdlib, run with `java -cp`) |
| `server.py` | loopback HTTP fixtures; `python3 server.py` starts them by hand and prints the origins |
| `build/` | git-ignored: cached compiled driver JARs (newest 3), raw `*.jsonl` / `*.stderr` of the last run |

Nothing outside `diff/` is written; `generated/` and `kotlin/` are only read.

## How a run works

1. `run.py` starts servers on ephemeral ports: `A`, `B` (a second origin for cross-origin redirects), `N` (must never
   be contacted), and, when the bind works, `V6` on `[::1]`, `127.0.0.1:80` and `127.0.0.1:65535`; it also reserves a
   bound but not listening port `CLOSED` so that connecting to it is refused for the whole run.
2. Both drivers get the same case list and the same variables. Every string in a case may contain `{A}`, `{A_HOST}`,
   `{A_PORT}`, `{B}`, `{B_HOST}`, `{B_PORT}`, `{N}`, `{N_HOST}`, `{N_PORT}`, `{CLOSED}`, `{CLOSED_PORT}`, `{V6}`, `{V6_HOST}`,
   `{V6_PORT}`; the drivers substitute them before calling the facade, and `run.py` turns the ephemeral origins in the
   results back into placeholders (leading zeros of a port survive: `:0{A_PORT}`), so expectations and results are stable
   across runs. An expected string that contains a placeholder is written in the form a result takes after that
   substitution back (`casekit.canonical`).
3. Each driver makes one unreported warm-up call, then runs the cases one at a time (each on a worker thread with a
   `deadline_s`, default 60 s, so a hung implementation costs one case, not the run) and prints one JSON line per case.
   Python runs first, then Kotlin; the servers see one client at a time and their per-run state is reset in between.
4. **Cases that need a listener the host may not offer** carry a tag: `port80` (127.0.0.1:80 is privileged), `port65535`
   (the port may be taken), `ipv6` (`::1`). When the main pass skips some, `run.py` re-executes itself inside
   `unshare --user --map-root-user --net` (where those ports are free and `lo` is brought up) for exactly those cases,
   prints that second table and adds a `TOTAL`. Without `unshare` (or with `--no-namespace`) they are listed as skipped and
   the run is not clean.

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

Each case has `id` (unique, `fn/...`), `fn`, the inputs of that function, an `expect` and a `rule`:

| `fn` | inputs |
| --- | --- |
| `parse_method` | `"source": "get"` |
| `parse_arguments`, `execute` | `"arguments": ["post", "{A}/echo", "body"]` |
| `send_request` | `"request": {"method": "Get" \| {"variant":"Custom","name":"PURGE"}, "url", "headers": [[name, value]…], "body", "timeout_ms"}` |
| `render_response` | `"response": {"status", "url", "headers": [[name, value]…], "body"}` |

* `expect` — assertions over the normalized `result` that **both** sides must meet. Keys are dotted paths (`#` is a
  length, `@json` parses a string as JSON: `value.body.@json.headers.host`); values are compared for equality, except
  `{"$absent": true}` (the key must not exist) and `{"$contains": [...]}` (a string holding every part).
* `rule` — the label of the contract rule or decision the case exercises; groups set a default, see below.
* Optional: `tags`, `deadline_s`, `body_digest`, `note` (the reason the expectation holds, shown on a DIFF/FAIL).

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

The docstring of `server.py` lists every route. The ones that put exact bytes on the wire, so a case decides every byte
and derives its expectation from the same bytes: `hdr-raw?hex=` (the header lines), `chunk-raw?hex=` (the chunked body),
`status-line?hex=` (the status line), `redir?to_hex=` (a raw Location), and `interim?codes=&ihex=&drop=` (interim responses
with optional raw header bytes), `nobody?code=&framing=` (204/304 announcing a body), `hdr-redirect?to=&hex=` (a redirect
with raw header lines, by default one ISO-8859-1 field), plus the earlier `drop*`, `garbage`, `bad-header-line`,
`close-delimited`, `chunked`, `slow`, `drip`, `big`, `redir` (`dup`, `dup2`, `dupname`), `chain`, `loop`, `x-out`/`x-bounce`.

## Rules and decisions

The `rule` label ties a case to what it tests; `--rule` selects by it and the summary counts failures by it.

| label | what | cases |
| --- | --- | --- |
| `R1` | URL characters (RFC 3986 set, malformed `%HH`) | 355 |
| `R2` / `R3` | request target and Host (query, fragment, `%HH` verbatim, userinfo, caller Host) | 18 / 13 |
| `R4` | Location resolution (RFC 3986 5.2 strict), unresolvable Locations, invalid Location characters | 181 |
| `R5` | origin comparison and the credential rule | 15 |
| `R6` | body decoding (Table 3-7/3-8, BOM, NUL, read/chunk boundaries) | 275 |
| `R7` | NetworkFailed causes, the 64 MiB limit | 35 |
| `D1` | several Location fields are joined with `", "`: never valid, the 3xx is returned | 15 |
| `D2` | a response to wire method exactly `HEAD`, and any 204/304, has no body | 15 |
| `D3` | literal `.`/`..` segments of the request path removed (RFC 3986 5.2.4); `%2E` stays | 38 |
| `D4` | Location scheme case-insensitive, resolved URL lower-case | 15 |
| `D5` | received header values: leading/trailing SP and HTAB removed | 17 |
| `D6` | the values of the final header block decoded as a whole: ASCII, else valid UTF-8, else ISO-8859-1 | 18 |
| `D7` | interim 100 and 102–199 discarded, 101 is NetworkFailed | 16 |
| `D8` | status line `HTTP/1.x SP nnn [SP reason]`, reason may be empty or missing | 23 |
| `D9` | chunk extensions ignored, trailer fields discarded | 15 |
| `D10` | chunk-size line: hexadecimal digits, then nothing, SP/HTAB, or optional SP/HTAB and `;` + ignored extension; anything else is NetworkFailed | 41 |
| `D11` | closed after the last chunk but before the final empty line is NetworkFailed | 8 |
| `D12` | ports: decimal value, leading zeros, empty = default, non-digit or > 65535 = InvalidRequest, 0 = NetworkFailed | 104 |
| `D13` | a request header value above U+007F is InvalidRequest | 22 |
| `D14` | a received header line whose name is not one or more token characters immediately followed by `:` (non-ASCII, `@`, empty, whitespace before the colon, no colon) is NetworkFailed | 84 |
| `methods`, `arguments`, `render`, `execute`, `exchange`, `redirects`, `invalid-request`, `boundary`, `listeners` | general behavior of each function (`boundary` = lone surrogates) | 756 |

`D1`–`D13` were the "edge" behaviors the contract once left open (settled from upstream posting 2.10.0 / httpx 0.28.1 and
written into `client.cott`); `D14` (header field names) and the chunk-size grammar of `D10` were added after the first
cross-check against upstream. The 21 edge cases became contract cases:

| former edge case | now (`send_request/…`) | rule |
| --- | --- | --- |
| `edge-location-two-headers` | `location-fields-two-valid-not-followed` | D1 |
| `edge-location-invalid-first-of-two-headers` | `location-fields-first-invalid-not-followed` | D1 |
| `edge-custom-head-method-response-has-no-body` | `head-custom-head-method-has-no-body` | D2 |
| `edge-initial-url-dot-segments-{dot-segment,dot-dot-segment,mixed}` | `target-dots-{current-segment,parent-after-segment,contract-example}` | D3 |
| `edge-location-{uppercase,mixed-case}-scheme` | `location-scheme-{uppercase,titlecase}-followed` | D4 |
| `edge-response-header-values-with-outer-whitespace` | `response-header-values-trimmed-spaces` / `-tabs` | D5 |
| `edge-response-header-bytes-above-0x7f` | `response-header-block-mixed-latin1-and-utf8-decodes-all-as-latin1` | D6 |
| `edge-interim-102-response-before-final` | `interim-102-then-final` | D7 |
| `edge-expect-100-continue-interim-response` | `interim-100-continue-then-final` | D7 |
| `edge-status-line-without-reason-phrase` | `status-line-accepted-http-1-1-without-reason` | D8 |
| `edge-chunk-extension-and-trailer` | `chunked-extensions-and-trailer` | D9 |
| `edge-chunk-size-not-hexadecimal` | `chunked-size-not-hexadecimal-letters` | D10 |
| `edge-closed-after-last-chunk-line` | `chunked-closed-after-last-chunk-line` | D11 |
| `edge-port-{out-of-range,zero,non-numeric,leading-zeros}` | `port-unusable-above-65535-99999`, `port-zero-zero-is-attempted`, `port-unusable-non-digit-letters`, `port-leading-zeros-one-zero-decimal-value-used` | D12 |
| `edge-request-header-value-non-ascii` | `request-header-value-non-ascii-e-acute` | D13 |

The four non-ASCII-`Location` cases of rule R4 (`location-invalid-non-ascii-*`) now carry `rule` `D6` and an exact
`Response.headers` expectation instead of an ignored one.

Five former `D6` cases changed meaning with `D14`: header names are tokens, so a response with a non-ASCII name is
NetworkFailed (it used to be a block decoded with its names). They moved to rule `D14` and were renamed:

| was (rule D6, `Ok` with decoded names) | now (rule D14, NetworkFailed) |
| --- | --- |
| `response-header-block-utf8-name` | `response-header-name-non-ascii-utf8` |
| `response-header-block-latin1-name` | `response-header-name-non-ascii-latin1` |
| `response-header-block-utf8-name-with-latin1-value` | `response-header-name-non-ascii-utf8-with-latin1-value` |
| `response-header-block-latin1-name-with-utf8-value` | `response-header-name-non-ascii-latin1-with-utf8-value` |
| `response-header-block-non-ascii-in-every-field` | `response-header-name-non-ascii-in-every-field` |

## What is covered (2 079 cases)

* `parse_method`, `parse_arguments`, `render_response`, `execute`: methods in every case pattern, every ASCII character
  alone and after `GET`, every tchar, non-ASCII including the case-folding traps, argument counts, rendering, and the
  decisions through `execute` (interim, trimming, block decoding, a header name that is not a token, ports, dot segments,
  several Location fields).
* **R1:** every character outside the set (the nine printable ones, space, all 33 control characters, non-ASCII) and nine
  malformed `%HH` forms in the path and the fragment; a subset also in the query, userinfo and host; every valid character
  verbatim in the path and query. All invalid URLs point at server `N`, which must record no connection.
* **R2/R3:** empty path, empty query, `?` inside a fragment, `//` and `///` paths, `%HH` verbatim, caller `Host` replaces
  the default and keeps its position, userinfo neither sent nor used, IPv6 brackets.
* **R4:** the RFC 3986 section 5.4.1/5.4.2 tables (all but `//g`), 61 more references from the oracle, base variants,
  references that resolve to a non-http(s) URL or to no host (3xx returned), Locations with an invalid character or a
  malformed `%HH` (3xx returned).
* **R5, R6, R7:** origins and credentials, decoding (all 128 single bytes >= 0x80, the boundaries of Table 3-7 for every
  lead byte, multi-byte characters across read and chunk boundaries), close after the status line / mid-headers / before
  and inside the body / mid and inside a chunk, non-HTTP/1.x status lines, the 64 MiB limit at and one byte over.
* **D1:** two, three, identical, empty, invalid, differently spelled and cross-origin Location fields, for GET and HEAD and
  five statuses, plus a single Location that holds a comma (followed).
* **D2:** `Custom("HEAD")` against Content-Length, chunked, close-delimited, 404 and a redirect; `Custom("head")`,
  `Custom("Head")`, `Custom("hEAD")` are not HEAD (a body is read); 204 and 304 announcing Content-Length or chunked, for
  GET, POST, HEAD and after a redirect.
* **D3:** 34 request paths (leading, inner and trailing `.`/`..`, beyond the root, empty segments, three dots and dot-like
  segments (kept), every percent-encoded spelling of a dot (kept), query and fragment dots (untouched)), plus dots in the
  query after an empty path, POST, a redirect, and `execute`.
* **D4:** `HTTP`, `Http`, `hTTp` (followed; `Response.url` lower-case; same origin keeps headers, other host strips them;
  host case kept), `HTTPS`/`Https` (followed, TLS fails), and `HTTP:g`, `HTTP://`, `hTTp:/g`, `FTP://`, `HTTPX://` (3xx returned).
* **D5/D6:** trimming of spaces, tabs, mixed, only-whitespace values, framing headers, `Location`; NBSP is not trimmed;
  blocks whose values are ASCII, UTF-8 (2/3/4 byte), Latin-1, mixed, with lone continuation bytes, overlong, UTF-8-encoded
  surrogates, above U+10FFFF or truncated sequences; only the final response's block counts (not a redirect's, not an
  interim's).
* **D7:** 102, 100, 103, 199, several, six in a row, after a redirect, for HEAD, `Expect: 100-continue`; 101 alone, with
  Upgrade headers, before or after a 102; an interim response followed by a closed connection.
* **D8:** accepted: no reason, empty reason (with the trailing space), `HTTP/1.0`, 404/599, reasons with spaces and colons;
  rejected: no space before the reason, two spaces, TAB for SP, missing status, lower-case `http`, `HTTP/1`, leading space,
  four/two digit and signed statuses.
* **D9–D11:** nine extension/trailer shapes, chunk data holding CRLF or a terminator-looking `0 CRLF CRLF`, hexadecimal
  digits in either case, leading zeros, 200 one-byte chunks, an empty body. **D10:** 19 rejected size lines (twelve not
  hexadecimal, seven with text after the digits: blanks on both sides, `3 x`, `3 3`, VT, FF, NUL, NBSP), nine accepted
  ones (trailing SP/HTAB, an extension with or without a value, SP/HTAB before the `;`, a space after it, leading
  zeros) — each with data as long as a lenient parser would read — the same forms on the last chunk (four accepted, one
  of them followed by a trailer field; four rejected) and five sizes beyond the body limit. **D11:** eight ways to close
  before the final empty line.
* **D12:** 50 unusable ports (16 above 65535, from 65536 to 44 nines; 18 non-digit spellings including `+80`, `8_0`,
  `%38%30`; 7 with IPv6, https, userinfo, no path or a query; 9 prefixed with the never-contact server's port), port 0,
  leading zeros (up to 28) that must not show in `Host`, userinfo that looks like a port, twelve Locations with an unusable
  port and five with leading zeros, `:080`, `:` (empty), `:65535`, `:65536`.
* **D13:** thirteen non-ASCII values (U+0080, é, U+00FF, U+0100, emoji, U+2028, BOM, NBSP, CJK, U+10FFFF, at either end),
  in `Cookie`, `Authorization` and `Host`, first or second of two, with a body, and beating a connection failure; every
  printable ASCII character in one value passes.
* **D14:** 61 rejected field lines (one through `execute`) and 23 accepted ones, each block with a valid field before and
  after: whitespace before the colon (SP, HTAB, several, an empty value, in `Content-Length`), empty names, a space, TAB,
  control character or DEL inside a name, each of the sixteen delimiters (`"(),/;<=>?@[\]{}`), `@` first, last and alone,
  nine non-ASCII names (UTF-8, Latin-1, a lone continuation byte, `0xFF`, a BOM, NBSP), lines without a colon, lines that
  start with SP/HTAB (obsolete folding), the bad line first or last in the block, in a redirect response, in the final
  response after a valid redirect, in interim 100/102 responses and in a HEAD response; accepted: `!#$%&'*+-.^_`|~` as a
  name, all 77 token characters, each of the fifteen punctuation characters inside a name, digit-only, one-letter and `-`
  names, a name that ends at the first colon (`X:A: v`), delimiters and colons inside values.
* **Boundary violations:** a lone surrogate in `parse_method`, `parse_arguments`, `render_response`, `send_request` and
  `execute` is a `Violation` in both runtimes.

## Readings of the contract that decide some rows

These are interpretations of the contract text; a case that rests on one says so in its `note`.

* An empty `Location:` value is a Location field whose reference is empty: it resolves to the base URL (RFC 3986 5.4.1).
  Section 5.2.2 applies `remove_dot_segments` to an absolute or scheme-relative Location too, so `http://h/x/./y/../z`
  becomes `http://h/x/z`.
* D5 applies to every received header value: a `Location` of `  /echo ` is the valid URL `/echo` (followed), a
  `Content-Length: 2 ` frames a two-byte body. Only SP and HTAB are removed (U+00A0 stays).
* D14: a field line is `token:`; the block decoding of D6 therefore only ever sees values. A line that starts with SP or
  HTAB (an obsolete line fold) has no token before its colon, or no colon at all, so it is NetworkFailed and nothing is
  unfolded (five cases: `response-header-name-space-only-before-colon`, `response-header-line-leading-space-before-name`,
  `…-leading-tab-before-name`, `…-obs-fold-continuation`, `…-obs-fold-tab-continuation`). The fields of a redirect
  response and of an interim response are read like any other, so a bad name there is NetworkFailed too.
* D2: "wire method exactly HEAD" — `Custom("head")` is sent as `head` and is not HEAD.
* D3: RFC 3986 5.2.4 literally, as the contract says ("removed as in RFC 3986 section 5.2.4"): `/a/b/..` is `/a/`,
  `/a/b/.` is `/a/b/`, `/a//../echo` is `/a/echo`, empty segments stay. Upstream httpx uses a simpler normalizer that drops
  the trailing slash (`/a`, `/a/b`), so two cases (`target-dots-trailing-parent`, `target-dots-trailing-current`) are the
  only place where the RFC reading and upstream differ on the request path; every other D3 case agrees with upstream.
* D8: `HTTP/1.x` is `HTTP/1.` plus a digit, case-sensitive; the reason phrase follows exactly one space.
* D10: the size line is hexadecimal digits, then nothing, SP/HTAB, or optional SP/HTAB and `;` with an ignored extension.
  Not accepted: leading whitespace, `0x`, a sign, an underscore, a point, a letter after the digits, any other character
  after SP/HTAB (`3 x`, `3 3`), VT, FF, NUL or NBSP after the digits. A valid size larger than the body limit (or than
  what arrives) cannot complete and is NetworkFailed. Empty or malformed extensions (`3;`) are not tested.
* D12: "a port with a non-digit" includes `+80` and `8_0` (Python's `int()` accepts both). `80:80` is not tested: the
  contract does not say whether the host or the port takes the second colon.
* `HTTP/1.0 200 OK` is an HTTP/1.x status line; `!` is a URL character, so `http://exa!mple.invalid/` is a name-resolution
  failure, not an InvalidRequest; a TAB inside a `Location` is a control character (not followed); after a followed
  redirect HEAD stays HEAD (`ensures response.body == ""`).

## Where the contract differs from upstream httpx

The decision cases were also run through upstream (`httpx.Client(follow_redirects=True)`, httpx 0.28.1, h11 0.16) against
the same fixtures. Nearly all agree; the differences are deliberate and are the only cases upstream would fail:

* Rules older than the decisions: `Response.url` is the URL as given (httpx normalizes it), `Host` keeps its case (httpx
  lower-cases it), URL userinfo is never an `Authorization` and the credential headers follow the contract's rule on
  redirects, a `Custom` method name is sent unchanged (httpx upper-cases it), and a `Location` the contract does not
  follow (invalid characters, another scheme, an unusable port) is returned as a 3xx (httpx percent-encodes it or
  follows it).
* D1: httpx follows the `", "`-joined, percent-encoded value; here that value contains a space and is never valid.
* D3: trailing `/..` and `/.` keep the slash (`/a/`, `/a/b/`); httpx gives `/a`, `/a/b`.
* D10: SP/HTAB before the `;` of an extension (`2 ; a=b`) is accepted here (RFC 9112 BWS); h11 rejects it.
* D12: `+80` and `8_0` are InvalidRequest; httpx parses the port with `int()` and connects to port 80.
* D14: an obsolete line fold is NetworkFailed here; h11 unfolds it (RFC 9112 5.2 lets a client replace the fold by SP).

## Not decided (deliberately not tested)

No case exists for behavior the contract and the decision table leave open: control characters other than CR/LF in a
request header value (U+007F, NUL), trailer fields that are malformed or name framing headers (`Transfer-Encoding` in a
trailer makes h11 fail), an empty or malformed chunk extension (`3;`), `HTTP/1.9`-style minor versions, bytes >= 0x80 in
the reason phrase, a bracketed IPv6 host that is not closed, both `Content-Length` and chunked coding, several
`Content-Length` values, unknown transfer codings, and the RFC 3986 example `//g`.

## Not covered

* https → http downgrade refusal, an https default-port Host and Location resolution against an https base: they need a
  TLS listener with a certificate both runtimes trust (possible later with `SSL_CERT_FILE` / `-Djavax.net.ssl.trustStore`
  and an `openssl`-made certificate).
* Connection-attempt timeout (needs an unroutable address), HTTP/2, proxies.

## Adding a case

Add it to the matching `group_*` function in `cases.py` or `decisions.py` (ids are unique and start with `fn/`; the group
sets the `rule` label, or pass `rule=`). Derive `expect` from the contract text or from `oracle.py`, never from what an
implementation returned; if the contract does not decide the behavior, do not add a case, add the question to "Not
decided" above. Check with `python3 run.py --python-only --only 'your/id'`, then run the full comparison.
