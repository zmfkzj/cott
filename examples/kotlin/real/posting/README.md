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
`diff/` (see `diff/README.md`), which calls both public facades with the same 1673 inputs against
local HTTP servers. Expected values come from the contract text and independent RFC 3986 and
Unicode oracles (`diff/oracle.py`), not from either implementation:

```bash
PATH="$HOME/.local/opt/kotlinc/bin:$HOME/.local/opt/jdk17/bin:$PATH" \
  python3 examples/kotlin/real/posting/diff/run.py
```

Last run: 1669 PASS, 4 DIFF, 0 FAIL. Both implementations meet all 1652 contract expectations,
including 20 cases where a lone-surrogate `Str` is rejected at the facade boundary by both
runtimes. The 4 DIFFs are `edge` cases for behavior the contract does not state:

- received header bytes ≥ 0x80: Python decodes UTF-8 with replacement, Kotlin decodes Latin-1;
- interim `102` or `100 Continue` before the final response: Python returns the 1xx as the
  Response, Kotlin skips to the final response;
- a port with leading zeros: Python `NetworkFailed`, Kotlin `InvalidRequest`.

Not covered: https→http downgrade refusal, the https default-port Host and Location resolution
against an https base (need a TLS listener trusted by both runtimes), connection-attempt
timeouts, the RFC 3986 example `//g` (another host), proxies and HTTP/2.
