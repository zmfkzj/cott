# https://github.com/darrenburns/posting

Kotlin/JVM generation of the same Cott contract as `examples/real/posting`:
`src/real/posting/client.cott` is byte-identical to the Python project's contract. All five
callables (`parse_method`, `parse_arguments`, `send_request`, `render_response`, `execute`) are
agent-generated with `omp` and `anthropic/claude-sonnet-5-5` under `kotlin/cott_impl/`.
`send_request` uses `java.net.Socket`/`SSLSocketFactory` with a hand-written HTTP/1.1 client
(`HttpURLConnection` cannot send PATCH or custom methods; `java.net.http.HttpClient` rejects
`Host` and `Content-Length`), a hand-written RFC 3986 §5.2 Location resolver
(`java.net.URI.resolve` implements RFC 2396) and a hand-written UTF-8 decoder (`String(bytes,
UTF_8)` emits one U+FFFD for `ED A0 80` where Unicode maximal-subpart replacement needs three);
`generator.rules` records that decided design.

## Evidence

`cott verify` certifies the snapshot with `observed=11 unknown=12`. The Kotlin runner does not
execute effectful callables, so the 8 `send_request` and 4 `execute` clauses are `unknown`
("effectful callable requires an enforceable canonical scenario") and the HTTP fixture scenarios
are not observed. The coverage policy is the Python project's strict policy except that those two
rules allow `unknown`/`unobserved`; the pure callables stay strict.

Behavioral equivalence with the Python implementation is checked by the differential harness in
`diff/` (see `diff/README.md`), which calls both public facades with the same 2079 inputs against
local HTTP servers. Expected values come from the contract text and independent RFC 3986 and
Unicode oracles (`diff/oracle.py`), not from either implementation:

```bash
PATH="$HOME/.local/opt/kotlinc/bin:$HOME/.local/opt/jdk17/bin:$PATH" \
  python3 examples/kotlin/real/posting/diff/run.py
```

Last run: 2079 PASS, 0 DIFF, 0 FAIL; every case carries a contract expectation and both
implementations meet all of them, including lone-surrogate `Str` rejection at the facade boundary.

The transport details the contract used to leave open (several Location fields, `HEAD`/204/304
bodies, dot segments in the request target, Location scheme case, header whitespace and byte
decoding, interim 1xx, status-line and chunk framing, ports, non-ASCII request header values,
header field names) were decided from upstream posting 2.10.0 on httpx 0.28.1 / h11 0.16.0,
observed against the harness fixtures. Where upstream conflicts with a rule the contract already
pinned, or with RFC 3986/9112, the contract keeps its rule; `diff/README.md` lists each deviation
from httpx.

Not covered: https→http downgrade refusal, the https default-port Host and Location resolution
against an https base (need a TLS listener trusted by both runtimes), connection-attempt
timeouts, the RFC 3986 example `//g` (another host), proxies and HTTP/2.
