//! Behavior of the compiler-owned database fixture helper `src/python/database_fixture.py`.
//! File-backend projection and precise refusals run on host Python. The PostgreSQL lifecycle provisions a real
//! private cluster inside the Linux sandbox without network access:
//! COTT_POSTGRES_BIN=/tmp/cott-pg/root/usr/lib/postgresql/16/bin cargo test --test database_fixture_runtime -- --ignored
use cott::sandbox::{BindMounts, NetworkAccess, ResourceLimits, SandboxSpec, run};
use std::collections::BTreeMap;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::Command;
use std::sync::atomic::{AtomicU64, Ordering};
use std::time::Duration;

const HELPER: &str = include_str!("../src/python/database_fixture.py");
const PRELUDE: &str = r##"
import os, pathlib, sqlite3, subprocess, sys, time, urllib.parse

work = pathlib.Path(sys.argv[1])


def refused(call, phase, needle):
    try:
        call()
    except DatabaseFixtureError as error:
        assert error.phase == phase, (phase, str(error))
        assert needle in str(error), (needle, str(error))
    else:
        raise AssertionError(f"expected a {phase} refusal mentioning {needle!r}")
"##;
const FILE_BACKENDS: &str = r##"
limits = {"scenario_timeout_ms": 1000, "filesystem_bytes": 1 << 20, "filesystem_files": 16}
root = work / "store"
fixture = DatabaseFixture(
    {"kind": "database", "id": "store", "backend": "sqlite", "span": {"start": 0, "end": 9}, "source_order": 2},
    root,
    limits,
)
refused(lambda: fixture.path("app.db"), "path projection", "not started")
fixture.start()
assert root.is_dir() and not root.is_symlink() and root.stat().st_mode & 0o777 == 0o700
database = fixture.path("app.db")
assert database == root / "app.db", database
refused(lambda: fixture.path("cache/../app.db"), "path projection", "not a normalized relative path")
connection = sqlite3.connect(database)
connection.execute("create table item(name text)")
connection.execute("insert into item values ('kept')")
connection.commit()
connection.close()
assert fixture.path("app.db") == database
outside = work / "outside"
outside.mkdir()
(outside / "keep.db").write_bytes(b"outside")
for escape, needle in (
    ("../outside/keep.db", "does not name a file inside"),
    ("cache/../../outside/keep.db", "does not name a file inside"),
    ("..", "does not name a file inside"),
    (".", "does not name a file inside"),
    (str(outside / "keep.db"), "is not a relative"),
    ("", "is not a relative"),
    ("a\0b", "is not a relative"),
    ("a\\b", "is not a relative"),
    (":memory:", "authored `:memory:` input"),
    (7, "must be a string"),
):
    refused(lambda escape=escape: fixture.path(escape), "path projection", needle)
os.symlink(outside, root / "link")
os.symlink(outside / "keep.db", root / "alias.db")
refused(lambda: fixture.path("link"), "path projection", "traverses symlink")
refused(lambda: fixture.path("link/keep.db"), "path projection", "traverses symlink")
refused(lambda: fixture.path("alias.db"), "path projection", "traverses symlink")
(root / "cache").mkdir()
(root / "plain").write_bytes(b"")
refused(lambda: fixture.path("cache"), "path projection", "not a regular file")
refused(lambda: fixture.path("plain/app.db"), "path projection", "traverses non-directory")
refused(lambda: fixture.url("/"), "url projection", "sqlite fixture exposes file paths")
# The closing audit rejects the planted symlinks, and removal never follows them out of the private root.
refused(fixture.close, "cleanup", "contains symlink")
assert not root.exists()
assert (outside / "keep.db").read_bytes() == b"outside"
fixture.close()
refused(lambda: fixture.path("app.db"), "path projection", "not started")
refused(fixture.start, "setup", "fixture is closed")

bounded = DatabaseFixture({"kind": "database", "id": "bounded", "backend": "sqlite"}, work / "bounded", dict(limits, filesystem_bytes=16384))
bounded.start()
connection = sqlite3.connect(bounded.path("large.db"))
connection.execute("create table payload(data blob)")
connection.execute("insert into payload values (zeroblob(65536))")
connection.commit()
connection.close()
refused(bounded.close, "cleanup", "filesystem_bytes limit of 16384")
assert not (work / "bounded").exists()

duck = DatabaseFixture({"kind": "database", "id": "analytics", "backend": "duckdb"}, work / "analytics", limits)
duck.start()
assert duck.path("warehouse.duckdb") == work / "analytics" / "warehouse.duckdb"
refused(lambda: duck.path("../warehouse.duckdb"), "path projection", "does not name a file inside")
refused(lambda: duck.url("/"), "url projection", "duckdb fixture exposes file paths")
duck.close()
assert not (work / "analytics").exists()

replaced = DatabaseFixture({"kind": "database", "id": "replaced", "backend": "sqlite"}, work / "replaced", limits)
replaced.start()
(work / "replaced").rename(work / "owned-original")
(work / "replaced").mkdir()
(work / "replaced" / "kept").write_bytes(b"not fixture-owned")
refused(replaced.close, "cleanup", "identity changed")
assert (work / "replaced" / "kept").read_bytes() == b"not fixture-owned"
assert (work / "owned-original").is_dir()
"##;
const REFUSALS: &str = r##"
limits = {"scenario_timeout_ms": 1000, "filesystem_bytes": 1 << 20, "filesystem_files": 16}
declaration = {"kind": "database", "id": "orders", "backend": "postgres"}
missing = work / "missing"
absent = {"initdb": str(missing / "initdb"), "postgres": str(missing / "postgres"), "share": str(missing / "share")}
unused = work / "unused"
for call, needle in (
    (lambda: DatabaseFixture(dict(declaration, host="db.example"), unused, limits, absent), "unsupported settings 'host'"),
    (lambda: DatabaseFixture(dict(declaration, port=5432, script="drop"), unused, limits, absent), "unsupported settings 'port', 'script'"),
    (lambda: DatabaseFixture({"kind": "database", "id": "orders"}, unused, limits, absent), "missing settings 'backend'"),
    (lambda: DatabaseFixture(dict(declaration, kind="fs"), unused, limits, absent), "kind must be 'database'"),
    (lambda: DatabaseFixture(dict(declaration, backend="mysql"), unused, limits, absent), "backend must be one of sqlite, duckdb, postgres"),
    (lambda: DatabaseFixture(declaration, unused, limits), "requires the host-frozen postgres_toolchain"),
    (lambda: DatabaseFixture(dict(declaration, backend="sqlite"), unused, limits, absent), "applies only to postgres fixtures"),
    (lambda: DatabaseFixture(declaration, unused, limits, dict(absent, psql="/usr/bin/psql")), "exactly the keys initdb, postgres, share"),
    (lambda: DatabaseFixture(declaration, unused, limits, dict(absent, initdb="bin/initdb")), "postgres_toolchain initdb must be an absolute path"),
    (lambda: DatabaseFixture(declaration, "relative/orders", limits, absent), "absolute normalized path"),
    (lambda: DatabaseFixture(declaration, f"{work}/cache/../orders", limits, absent), "absolute normalized path"),
    (lambda: DatabaseFixture(declaration, unused, dict(limits, scenario_timeout_ms=0), absent), "scenario_timeout_ms must be a positive integer"),
    (lambda: DatabaseFixture(declaration, unused, {"filesystem_bytes": 1, "filesystem_files": 1}, absent), "scenario_timeout_ms must be a positive integer"),
):
    refused(call, "configuration", needle)
assert not unused.exists()


def start_refused(root, toolchain, needle):
    fixture = DatabaseFixture(declaration, root, limits, toolchain)
    if os.geteuid() == 0:
        needle = "refuse to run as UID 0"
    refused(fixture.start, "setup", needle)
    assert not root.exists()


start_refused(work / "absent", absent, f"PostgreSQL initdb not found at `{absent['initdb']}`")
tools = work / "tools"
(tools / "bin").mkdir(parents=True)
(tools / "other").mkdir()
for path in (tools / "bin" / "initdb", tools / "bin" / "postgres", tools / "other" / "postgres"):
    path.write_text("#!/bin/sh\nexit 97\n")
    path.chmod(0o755)
(tools / "bin" / "plain").write_text("")
share = tools / "share"
share.mkdir()
toolchain = {"initdb": str(tools / "bin" / "initdb"), "postgres": str(tools / "bin" / "postgres"), "share": str(share)}
start_refused(work / "plain", dict(toolchain, postgres=str(tools / "bin" / "plain")), "is not an executable file")
start_refused(work / "foreign", dict(toolchain, postgres=str(tools / "other" / "postgres")), "is not the backend")
start_refused(work / "unshared", dict(toolchain, share=str(tools / "absent")), "share directory")
start_refused(work / "unbooted", toolchain, "lacks postgres.bki")
(share / "postgres.bki").write_text("")
start_refused(work / ("r" * 120), toolchain, "Unix sockets allow at most 107")
start_refused(work / "absent-parent" / "orders", toolchain, "is not an existing directory")

occupied = work / "occupied"
occupied.mkdir()
(occupied / "kept.db").write_bytes(b"kept")
fixture = DatabaseFixture(dict(declaration, backend="sqlite"), occupied, limits)
refused(fixture.start, "setup", "already exists")
assert (occupied / "kept.db").read_bytes() == b"kept"
"##;
const POSTGRES_PRELUDE: &str = r##"
bin = pathlib.Path(sys.argv[2])
toolchain = {"initdb": str(bin / "initdb"), "postgres": str(bin / "postgres"), "share": sys.argv[3]}
tools = {os.path.realpath(toolchain["initdb"]), os.path.realpath(toolchain["postgres"])}
declaration = {"kind": "database", "id": "orders", "backend": "postgres", "source_order": 0}


def toolchain_processes():
    found = []
    for name in os.listdir("/proc"):
        if name.isdigit():
            try:
                if os.readlink(f"/proc/{name}/exe") in tools:
                    found.append(int(name))
            except OSError:
                pass
    return found
"##;
const POSTGRES_LIFECYCLE: &str = r##"
root = work / "orders"
fixture = DatabaseFixture(declaration, root, {"scenario_timeout_ms": 60000, "filesystem_bytes": 256 << 20, "filesystem_files": 4096}, toolchain)
fixture.start()
url = fixture.url("/")
assert url == "postgresql://cott_fixture@" + urllib.parse.quote(str(root / "socket"), safe="") + ":5432/postgres", url
refused(lambda: fixture.url("/orders"), "url projection", "only route '/'")
refused(lambda: fixture.path("data/postgresql.conf"), "path projection", "url('/')")
assert toolchain_processes()


def psql(*statements):
    arguments = [str(bin / "psql"), url, "-X", "-A", "-t", "-q", "-v", "ON_ERROR_STOP=1"]
    for statement in statements:
        arguments += ["-c", statement]
    environment = {"LD_LIBRARY_PATH": os.environ["LD_LIBRARY_PATH"], "HOME": str(work)}
    return subprocess.run(arguments, capture_output=True, timeout=30, env=environment)


result = psql(
    "select current_user, current_database(), inet_server_addr() is null, current_setting('listen_addresses'), "
    "current_setting('max_connections'), current_setting('autovacuum'), current_setting('max_parallel_workers'), "
    "current_setting('shared_buffers'), current_setting('wal_segment_size')",
    "select bool_and(auth_method = case type when 'local' then 'trust' else 'reject' end), "
    "count(*) filter (where type = 'local') > 0, count(*) filter (where type <> 'local') > 0 from pg_hba_file_rules",
    "create table item(name text)",
    "insert into item values ('kept')",
    "select name from item",
)
assert result.returncode == 0, result.stderr
assert result.stdout.decode().splitlines() == ["cott_fixture|postgres|t||4|off|0|8MB|1MB", "t|t|t", "kept"], result.stdout
fixture.close()
assert not root.exists()
assert toolchain_processes() == [], toolchain_processes()
assert psql("select 1").returncode != 0
refused(lambda: fixture.url("/"), "url projection", "not started")
"##;
const POSTGRES_SETUP_FAILURES: &str = r##"
for timeout, files, needle in (
    (50, 4096, "initdb did not finish within the 50 ms scenario timeout"),
    (60000, 64, "filesystem_files limit of 64"),
):
    root = work / f"orders-{timeout}-{files}"
    limits = {"scenario_timeout_ms": timeout, "filesystem_bytes": 256 << 20, "filesystem_files": files}
    fixture = DatabaseFixture(declaration, root, limits, toolchain)
    started = time.monotonic()
    refused(fixture.start, "setup", needle)
    assert time.monotonic() - started < timeout / 1000 * 2 + 5
    assert not root.exists()
    assert toolchain_processes() == [], toolchain_processes()
    refused(lambda: fixture.url("/"), "url projection", "not started")
"##;
static NEXT_DIR: AtomicU64 = AtomicU64::new(0);

struct Scratch(PathBuf);

impl Scratch {
    fn new() -> Self {
        let mut number = NEXT_DIR.fetch_add(1, Ordering::Relaxed);
        loop {
            let path = std::env::temp_dir().join(format!(
                "cott-database-fixture-{}-{number}",
                std::process::id()
            ));
            match fs::create_dir(&path) {
                Ok(()) => return Self(path),
                Err(error) if error.kind() == io::ErrorKind::AlreadyExists => number += 1,
                Err(error) => panic!("create scratch directory: {error}"),
            }
        }
    }
}

impl Drop for Scratch {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.0);
    }
}

fn str_path(path: &Path) -> String {
    path.to_str().expect("UTF-8 path").to_owned()
}

fn program(cases: &[&str]) -> String {
    let mut program = format!("{HELPER}\n{PRELUDE}");
    for case in cases {
        program.push_str(case);
    }
    program
}

fn host_python(case: &str) {
    if Command::new("python3").arg("--version").output().is_err() {
        return;
    }
    let work = Scratch::new();
    let source = program(&[case]);
    let output = Command::new("python3")
        .args(["-I", "-c", source.as_str()])
        .arg(&work.0)
        .current_dir(&work.0)
        .env("PYTHONDONTWRITEBYTECODE", "1")
        .output()
        .expect("run host Python");
    assert!(
        output.status.success(),
        "stdout:\n{}\nstderr:\n{}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
}

fn postgres_bin() -> PathBuf {
    let bin = PathBuf::from(std::env::var_os("COTT_POSTGRES_BIN").expect(
        "set COTT_POSTGRES_BIN to a relocated PostgreSQL 16 bin directory; PostgreSQL is not installed system-wide",
    ));
    assert!(bin.is_absolute(), "COTT_POSTGRES_BIN must be absolute");
    for name in ["initdb", "postgres", "psql"] {
        assert!(
            bin.join(name).is_file(),
            "missing {}",
            bin.join(name).display()
        );
    }
    bin
}

fn sandboxed_postgres(case: &str) {
    let bin = postgres_bin();
    let prefix = bin
        .ancestors()
        .nth(5)
        .expect("relocated PostgreSQL package root")
        .to_path_buf();
    let share = prefix.join("usr/share/postgresql/16");
    assert!(
        share.join("postgres.bki").is_file(),
        "relocated PostgreSQL share directory missing: {}",
        share.display()
    );
    let work = Scratch::new();
    let result = run(&SandboxSpec {
        program: PathBuf::from("/usr/bin/python3"),
        arguments: vec![
            "-I".into(),
            "-c".into(),
            program(&[POSTGRES_PRELUDE, case]),
            str_path(&work.0),
            str_path(&bin),
            str_path(&share),
        ],
        cwd: work.0.clone(),
        environment: BTreeMap::from([
            ("HOME".into(), str_path(&work.0)),
            ("PATH".into(), "/usr/bin:/bin".into()),
            (
                "LD_LIBRARY_PATH".into(),
                str_path(&prefix.join("usr/lib/x86_64-linux-gnu")),
            ),
            ("PYTHONDONTWRITEBYTECODE".into(), "1".into()),
            ("TMPDIR".into(), str_path(&work.0)),
        ]),
        stdin: Vec::new(),
        binds: BindMounts {
            read_only: vec![prefix],
            writable: vec![work.0.clone()],
        },
        network: NetworkAccess::Disabled,
        limits: ResourceLimits {
            cpu_time: Duration::from_secs(120),
            address_space_bytes: 2 * 1024 * 1024 * 1024,
            process_count: 64,
            open_files: 256,
            file_size_bytes: 16 * 1024 * 1024,
            wall_time: Duration::from_secs(300),
            stream_limit_bytes: 1024 * 1024,
            writable_bytes: 256 * 1024 * 1024,
        },
    })
    .unwrap_or_else(|error| panic!("sandbox refused; no unsandboxed fallback: {error}"));
    assert_eq!(
        result.status,
        Some(0),
        "stdout:\n{}\nstderr:\n{}",
        String::from_utf8_lossy(&result.stdout),
        String::from_utf8_lossy(&result.stderr)
    );
    let leftovers = fs::read_dir(&work.0)
        .expect("read scratch directory")
        .map(|entry| entry.expect("scratch entry").file_name())
        .collect::<Vec<_>>();
    assert!(
        leftovers.is_empty(),
        "fixture left files behind: {leftovers:?}"
    );
}

#[test]
fn file_backends_project_confined_paths_and_enforce_bounds_at_close() {
    host_python(FILE_BACKENDS);
}

#[test]
fn declarations_toolchains_and_roots_are_refused_precisely() {
    host_python(REFUSALS);
}

#[test]
#[ignore = "needs COTT_POSTGRES_BIN (relocated PostgreSQL 16 bin with initdb, postgres, psql) and the Linux sandbox"]
fn postgres_fixture_serves_its_database_on_a_private_socket_and_leaves_nothing() {
    sandboxed_postgres(POSTGRES_LIFECYCLE);
}

#[test]
#[ignore = "needs COTT_POSTGRES_BIN (relocated PostgreSQL 16 bin with initdb, postgres, psql) and the Linux sandbox"]
fn postgres_setup_failures_are_bounded_and_clean_up() {
    sandboxed_postgres(POSTGRES_SETUP_FAILURES);
}

#[test]
#[ignore = "needs COTT_POSTGRES_BIN and the Linux sandbox"]
fn frozen_toolchain_mounts_bootstrap_a_real_private_cluster() {
    let work = Scratch::new();
    let toolchain =
        cott::python::postgres_fixture::PostgresToolchain::discover(&work.0.join("probe"))
            .expect("freeze native fixture toolchain");
    let mut environment = BTreeMap::from([
        ("PYTHONDONTWRITEBYTECODE".to_owned(), "1".to_owned()),
        ("PATH".to_owned(), "/usr/bin:/bin".to_owned()),
    ]);
    if let Some(path) = toolchain.library_path() {
        environment.insert("LD_LIBRARY_PATH".to_owned(), str_path(path));
    }
    let script = format!(
        r#"{HELPER}
import json,sys
root = os.path.join(sys.argv[1], "db")
fixture = DatabaseFixture(
    {{"kind":"database","id":"db","backend":"postgres"}},
    root,
    {{"scenario_timeout_ms":10000,"filesystem_bytes":67108864,"filesystem_files":4096}},
    json.loads(sys.argv[2]),
)
fixture.start()
assert fixture.url("/").startswith("postgresql://cott_fixture@")
fixture.close()
assert not os.path.exists(root)
print("ready and cleaned")
"#
    );
    let mut limits = ResourceLimits::contract_test();
    limits.writable_bytes = 67108864;
    let result = run(&SandboxSpec {
        program: PathBuf::from("/usr/bin/python3"),
        arguments: vec![
            "-I".into(),
            "-c".into(),
            script,
            str_path(&work.0),
            toolchain.request().to_string(),
        ],
        cwd: work.0.clone(),
        environment,
        stdin: Vec::new(),
        binds: BindMounts {
            read_only: toolchain.mounts().to_vec(),
            writable: vec![work.0.clone()],
        },
        network: NetworkAccess::Disabled,
        limits,
    })
    .expect("run with production native mount closure");
    assert_eq!(
        result.status,
        Some(0),
        "{}",
        String::from_utf8_lossy(&result.stderr)
    );
    assert_eq!(result.stdout, b"ready and cleaned\n");
    toolchain
        .revalidate()
        .expect("native fixture closure stays frozen");
}
