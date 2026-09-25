# https://github.com/yt-dlp/yt-dlp

A clean-room Cott reimplementation of a direct-media retrieval CLI. Its public
contracts model CLI input, HTTP(S) discovery, selection, transfers, rendering,
post-processing, and updates.
It is not a complete upstream extractor/plugin or command-line compatibility layer:
there are no site-specific extractors, the only extractor is a generic HTTP(S) one,
and the CLI accepts only URLs, `-a`/`--batch-file` and `--config-locations`.

## Run

```sh
project=examples/real/yt-dlp
UV_PROJECT_ENVIRONMENT="$(pwd)/$project/.venv" uv sync --locked --project "$project/python"
cott generate --agent omp --model anthropic/claude-opus-5-5 --target python --project "$project"
cott verify --project "$project"
PYTHONPATH="$project/generated/python:$project/python" "$project/.venv/bin/python" "$project/python/app.py" URL
```

Archives contain this client's plain media ids, one UTF-8 line per entry; they
are not upstream yt-dlp's extractor-key/id archive format. Plugin input is a
declarative text manifest (`extractor:NAME` or `postprocessor:NAME`), never
dynamically imported Python code. Config files are shell-split and parsed with
the same argument grammar as the command line.

## Options this client rejects

The request model carries upstream options that this client cannot honor. They
fail with a declared error instead of being silently ignored:

- `CertificatePolicy.Insecure` (`CertificateFailure`), legacy server connect and
  extractor arguments (`WorkaroundRejected`);
- `Netrc` authentication (`AuthenticationFailed`), cookie-file and browser-cookie
  authentication (`CookieFailure`); only anonymous access and HTTP Basic credentials
  are sent;
- `GeoBypassMode.Country` (`GeoRestricted`); an IP-block bypass is sent as
  `X-Forwarded-For`;
- every video filter (dates, view counts, age limit, match filter, `reject_live`),
  because a media item has no such fields (`InvalidInput`);
- unknown command-line options (`InvalidInput`).

## Updater

The explicit updater API installs the official upstream `yt-dlp` release asset
at the caller's target, not a release of this Cott reimplementation. It verifies
the official HTTPS SHA-256 manifest before descriptor-relative atomic replacement.
`apply_update` returns an `UpdateOutcome`: `Never` yields `Disabled` without I/O,
`Check` yields `Current` or `Available` without writing, and `Apply`, `Nightly` and
`Master` yield `Current` or `Installed`. `execute` does not report the outcome.

## What is specified and what is checked

Formal clauses relate results to inputs where the language can state it: validators
return their input unchanged and state their input-decidable rejections as
conditional errors (`errors complete` where those conditions are the whole failure
specification), shortcut URLs carry the yt-dlp prefixes and the query, extraction
yields exactly one item, planners preserve lengths, error payloads carry the
offending path or query, and `apply_update` outcomes are tied to the policy.
`execute` reports `simulated` from the mode and never plans more items than it
selected, and it declares only errors its stages can return. `resolve_authentication`,
`select_geo_route`, `resolve_live_media` and `select_subtitles` perform no I/O and
declare no effects. Syntax checks such as proxy URLs and IP blocks remain prose in
`doc`.

Scenarios observe the pure stages with exact expected values taken from the docs:
argument and batch parsing, input resolution, shortcut URLs, extractor choice,
the rejected options above with one input per conditional rejection, playlist
range expansion, format filtering and sorting, thumbnail/metadata/subtitle plans,
output-path rendering and sanitization, archive planning, fragment and
post-processing plans, JSON rendering and update channels. Automatic cases never
run effectful functions, so `cott verify` reports the clauses of the effectful
stages as `trust_declaration` or `unknown`, not as observed.

The effectful stages use real files, HTTP and subprocesses, which Cott's scenario
fixtures cannot back without changing the production code, so their duties are
`requirement`s that remain `unverified`: log preparation, config and batch loading,
declarative plugins, HEAD-only discovery, archive round trip, exact transfer bodies,
post-processing order and verified update installation. So are the composition
roots `execute` and `run`, whose `random` and `process.exit` effects have no
scenario fixture backend.

```sh
cott requirements --project examples/real/yt-dlp --format json
cargo test --test yt_dlp_program -- --ignored --nocapture
```

The external program regression deploys the current verified snapshot, then runs
real generated facades and `app.py` with only isolated loopback HTTP and scratch
filesystem access. It checks discovered report content, exact downloaded bytes,
declared failures and CLI output/exit status. Separate compiler-bound, type-valid
defect fixtures reproduce empty reports, wrong content, unjustified errors and
skipped execution. These fixtures are not verified example implementations.
Unavailable sandbox capability fails closed; there is no host-network fallback.
Results are labeled `external_program_regression`, never Cott scenario evidence,
so the `execute` and `run` requirements remain `unverified` in `cott requirements`
even when this independent regression succeeds.
