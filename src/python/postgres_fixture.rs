//! Native PostgreSQL toolchain for compiler-owned `database` scenario fixtures.
//!
//! The toolchain is discovered only when a selected scenario declares a
//! `postgres` database fixture. Its executables are pinned to canonical regular
//! files, the installation is probed inside the existing sandbox (no network,
//! no credentials), and every file the fixture can load is frozen by content
//! hash. [`PostgresToolchain::revalidate`] must succeed after the contract run
//! before its report is accepted, so concurrent toolchain drift never certifies.

use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, DirBuilder, OpenOptions};
use std::io::Read;
use std::os::unix::fs::{DirBuilderExt, MetadataExt, OpenOptionsExt};
use std::path::{Path, PathBuf};
use std::time::Duration;

use serde_json::{Value, json};
use sha2::{Digest, Sha256};

use crate::hash::sha256_hex;
use crate::sandbox::{BindMounts, NetworkAccess, ResourceLimits, SandboxSpec, run};

/// Python verification `tools` key holding the fixture toolchain identity.
pub const TOOL_KEY: &str = "postgresql_fixture";
/// Explicit toolchain location: the directory holding `initdb` and `postgres`.
pub const BIN_ENVIRONMENT: &str = "COTT_POSTGRES_BIN";
const REQUIRED_MAJOR: u32 = 16;
/// Host trees the sandbox always binds read-only; files below them are visible
/// without an additional mount.
const SANDBOX_SYSTEM_ROOTS: [&str; 5] = ["/usr", "/bin", "/lib", "/lib64", "/etc"];
/// Directories the dynamic loader searches without `LD_LIBRARY_PATH`.
const DEFAULT_LOADER_ROOTS: [&str; 4] = ["/lib", "/lib64", "/usr/lib", "/usr/lib64"];

/// A frozen PostgreSQL installation usable by the runner's database helper.
#[derive(Debug)]
pub struct PostgresToolchain {
    initdb: PathBuf,
    postgres: PathBuf,
    share: PathBuf,
    pkglib: PathBuf,
    mounts: Vec<PathBuf>,
    library_path: Option<PathBuf>,
    libraries: BTreeMap<String, PathBuf>,
    frozen: Closure,
    identity: Value,
}

/// Content identity of everything the fixture may execute, read or load.
#[derive(Clone, Debug, Eq, PartialEq)]
struct Closure {
    initdb: String,
    postgres: String,
    share: BTreeMap<String, String>,
    modules: BTreeMap<String, String>,
    libraries: BTreeMap<String, String>,
}

impl PostgresToolchain {
    /// Locate, pin, probe and freeze the toolchain. `probe_root` must not exist;
    /// it is created as a private scratch directory and removed before return.
    pub fn discover(probe_root: &Path) -> Result<Self, String> {
        let bin = locate_bin()?;
        DirBuilder::new()
            .mode(0o700)
            .create(probe_root)
            .map_err(|error| format!("create PostgreSQL fixture probe scratch: {error}"))?;
        let result = Self::discover_in(&bin, probe_root);
        let cleanup = fs::remove_dir_all(probe_root)
            .map_err(|error| format!("remove PostgreSQL fixture probe scratch: {error}"));
        let toolchain = result?;
        cleanup?;
        Ok(toolchain)
    }

    fn discover_in(bin: &Path, probe_root: &Path) -> Result<Self, String> {
        require_private_directory(bin, "PostgreSQL bin directory")?;
        let initdb = pinned_executable(bin, "initdb")?;
        let postgres = pinned_executable(bin, "postgres")?;
        let pg_config = pinned_executable(bin, "pg_config")?;

        let configured = probe(
            &pg_config,
            &[
                "--version",
                "--bindir",
                "--sharedir",
                "--pkglibdir",
                "--libdir",
            ],
            None,
            &visible_mounts([pg_config.as_path()]),
            probe_root,
        )?;
        let configured = PgConfig::parse(&configured)?;
        if configured.bindir != bin {
            return Err(format!(
                "PostgreSQL pg_config reports bindir {} for the installation pinned at {}",
                configured.bindir.display(),
                bin.display()
            ));
        }
        let share = configured.sharedir.clone();
        require_private_directory(&share, "PostgreSQL share directory")?;
        let bki = share.join("postgres.bki");
        if !fs::symlink_metadata(&bki).is_ok_and(|metadata| metadata.is_file()) {
            return Err(format!(
                "PostgreSQL share directory {} lacks a regular postgres.bki",
                share.display()
            ));
        }
        let pkglib = configured.pkglibdir.clone();
        require_private_directory(&pkglib, "PostgreSQL pkglibdir")?;

        let executables = [initdb.as_path(), postgres.as_path()];
        let library_path = if default_loader_directory(&configured.libdir) {
            None
        } else {
            require_private_directory(&configured.libdir, "PostgreSQL libdir")?;
            Some(configured.libdir.clone())
        };
        let mut trace_mounts = visible_mounts(executables);
        if let Some(libdir) = &library_path
            && !sandbox_visible(libdir)
        {
            trace_mounts.push(libdir.clone());
        }
        let traced = trace(
            &executables,
            library_path.as_deref(),
            &trace_mounts,
            probe_root,
        )?;
        if traced.values().any(LoaderTrace::has_missing) {
            return Err(format!(
                "PostgreSQL executables need libraries the loader cannot find: {}",
                missing_names(&traced)
            ));
        }
        let mut libraries = BTreeMap::<String, PathBuf>::new();
        for trace in traced.values() {
            merge_libraries(&mut libraries, trace)?;
        }
        let loader = libraries
            .iter()
            .find(|(name, _)| name.starts_with("ld-linux") || name.starts_with("ld-musl"))
            .map(|(_, path)| path.clone())
            .ok_or("PostgreSQL loader trace omitted its native ELF interpreter")?;
        if !sandbox_visible(&pkglib) {
            trace_mounts.push(pkglib.clone());
        }
        for module in module_files(&pkglib)? {
            let module = pkglib.join(module);
            let module_path = module
                .to_str()
                .ok_or("PostgreSQL module path is not UTF-8")?;
            let output = probe(
                &loader,
                &["--list", module_path],
                library_path.as_deref(),
                &trace_mounts,
                probe_root,
            )?;
            // A shared server module with no DT_NEEDED entries is still
            // content-hashed, but the loader reports no dependency closure.
            if output.trim() == "statically linked" {
                continue;
            }
            let traced = LoaderTrace::parse(&output)?;
            if traced.has_missing() {
                return Err(format!(
                    "PostgreSQL module {} has unresolved native dependencies",
                    module.display()
                ));
            }
            merge_libraries(&mut libraries, &traced)?;
        }

        let mut mounts = Vec::new();
        for path in [&initdb, &postgres] {
            if !sandbox_visible(path) {
                mounts.push(path.clone());
            }
        }
        if !sandbox_visible(&pkglib) {
            mounts.extend(
                module_files(&pkglib)?
                    .into_iter()
                    .map(|name| pkglib.join(name)),
            );
        }
        if !sandbox_visible(&share) {
            mounts.push(share.clone());
        }
        for path in libraries.values() {
            if !sandbox_visible(path) {
                mounts.push(path.clone());
            }
        }
        mounts.sort();
        mounts.dedup();

        let frozen = Closure::collect(&initdb, &postgres, &share, &pkglib, &libraries)?;

        let version = probe(
            &postgres,
            &["--version"],
            library_path.as_deref(),
            &mounts,
            probe_root,
        )?;
        let version = single_line(&version, "postgres --version")?;
        if version.strip_prefix("postgres (PostgreSQL) ") != Some(configured.release.as_str()) {
            return Err(format!(
                "PostgreSQL postgres reports `{version}`, not the pg_config release `{}`",
                configured.release
            ));
        }
        let data = probe_root.join("show");
        let data_argument = data.to_string_lossy().into_owned();
        let shown = sandboxed(
            &initdb,
            &["--show", "-D", &data_argument],
            probe_environment(library_path.as_deref(), false),
            &mounts,
            probe_root,
        )?;
        if shown.status != Some(0) || shown.timed_out {
            return Err(format!(
                "PostgreSQL initdb --show failed with {:?}: {}",
                shown.status,
                String::from_utf8_lossy(&shown.stderr).trim()
            ));
        }
        if fs::symlink_metadata(&data).is_ok() {
            return Err("PostgreSQL initdb --show created a data directory".to_owned());
        }
        // initdb prints its human-readable ownership banner on stdout and the
        // --show key/value diagnostics on stderr.
        let shown = InitdbSettings::parse(
            std::str::from_utf8(&shown.stderr)
                .map_err(|_| "initdb --show metadata is not UTF-8")?,
        )?;
        if shown.version != configured.release {
            return Err(format!(
                "PostgreSQL initdb reports version `{}`, not the pg_config release `{}`",
                shown.version, configured.release
            ));
        }
        if shown.bindir != bin || shown.share != share {
            return Err(
                "PostgreSQL initdb resolves a bindir or share directory other than pg_config"
                    .to_owned(),
            );
        }

        let identity = frozen.identity(&configured);
        Ok(Self {
            initdb,
            postgres,
            share,
            pkglib,
            mounts,
            library_path,
            libraries,
            frozen,
            identity,
        })
    }

    /// Exact `request.postgres_toolchain` value for the contract runner.
    pub fn request(&self) -> Value {
        json!({
            "initdb": self.initdb.to_string_lossy(),
            "postgres": self.postgres.to_string_lossy(),
            "share": self.share.to_string_lossy(),
        })
    }

    /// Read-only binds the runner sandbox needs; never `/` or a whole tree.
    pub fn mounts(&self) -> &[PathBuf] {
        &self.mounts
    }

    /// `LD_LIBRARY_PATH` for the recorded loader closure, when it is relocated.
    pub fn library_path(&self) -> Option<&Path> {
        self.library_path.as_deref()
    }

    /// Host-path-free identity recorded under Python `tools.postgresql_fixture`.
    pub fn identity(&self) -> &Value {
        &self.identity
    }

    /// Re-pin and re-hash the frozen closure after the run.
    pub fn revalidate(&self) -> Result<(), String> {
        let bin = self
            .initdb
            .parent()
            .ok_or("PostgreSQL initdb has no bin directory")?;
        require_private_directory(bin, "PostgreSQL bin directory")?;
        for (path, name) in [(&self.initdb, "initdb"), (&self.postgres, "postgres")] {
            if &pinned_executable(bin, name)? != path {
                return Err(format!(
                    "PostgreSQL fixture toolchain changed during verification: {name} moved"
                ));
            }
        }
        let current = Closure::collect(
            &self.initdb,
            &self.postgres,
            &self.share,
            &self.pkglib,
            &self.libraries,
        )?;
        match self.frozen.drift(&current) {
            None => Ok(()),
            Some(part) => Err(format!(
                "PostgreSQL fixture toolchain changed during verification: {part}"
            )),
        }
    }
}

impl Closure {
    fn collect(
        initdb: &Path,
        postgres: &Path,
        share: &Path,
        pkglib: &Path,
        libraries: &BTreeMap<String, PathBuf>,
    ) -> Result<Self, String> {
        let mut share_files = BTreeMap::new();
        hash_tree(share, share, &mut share_files)?;
        let modules = module_files(pkglib)?
            .into_iter()
            .map(|name| Ok((name.clone(), hash_regular(&pkglib.join(name))?)))
            .collect::<Result<BTreeMap<_, _>, String>>()?;
        let libraries = libraries
            .iter()
            .map(|(name, path)| {
                let canonical = fs::canonicalize(path)
                    .map_err(|error| format!("resolve PostgreSQL library {name}: {error}"))?;
                Ok((name.clone(), hash_regular(&canonical)?))
            })
            .collect::<Result<BTreeMap<_, _>, String>>()?;
        Ok(Self {
            initdb: hash_regular(initdb)?,
            postgres: hash_regular(postgres)?,
            share: share_files,
            modules,
            libraries,
        })
    }

    fn drift(&self, current: &Self) -> Option<&'static str> {
        if self.initdb != current.initdb {
            Some("initdb")
        } else if self.postgres != current.postgres {
            Some("postgres")
        } else if self.share != current.share {
            Some("share directory")
        } else if self.modules != current.modules {
            Some("server modules")
        } else if self.libraries != current.libraries {
            Some("loader closure")
        } else {
            None
        }
    }

    fn identity(&self, configured: &PgConfig) -> Value {
        json!({
            "initdb": self.initdb,
            "libraries": map_digest(&self.libraries),
            "modules": map_digest(&self.modules),
            "postgres": self.postgres,
            "release": format!("PostgreSQL {}", configured.release),
            "share": map_digest(&self.share),
            "version": configured.version,
        })
    }
}

#[derive(Debug)]
struct PgConfig {
    release: String,
    version: String,
    bindir: PathBuf,
    sharedir: PathBuf,
    pkglibdir: PathBuf,
    libdir: PathBuf,
}

impl PgConfig {
    fn parse(output: &str) -> Result<Self, String> {
        let lines = output.lines().collect::<Vec<_>>();
        let [release, bindir, sharedir, pkglibdir, libdir] = lines.as_slice() else {
            return Err("PostgreSQL pg_config returned an unexpected report shape".to_owned());
        };
        let release = release
            .strip_prefix("PostgreSQL ")
            .ok_or("PostgreSQL pg_config --version is not a PostgreSQL release")?;
        let version = release_version(release)?;
        Ok(Self {
            release: release.to_owned(),
            version,
            bindir: canonical_directory(bindir, "pg_config bindir")?,
            sharedir: canonical_directory(sharedir, "pg_config sharedir")?,
            pkglibdir: canonical_directory(pkglibdir, "pg_config pkglibdir")?,
            libdir: canonical_directory(libdir, "pg_config libdir")?,
        })
    }
}

#[derive(Debug)]
struct InitdbSettings {
    version: String,
    bindir: PathBuf,
    share: PathBuf,
}

impl InitdbSettings {
    fn parse(output: &str) -> Result<Self, String> {
        let setting = |name: &str| {
            let prefix = format!("{name}=");
            let mut values = output.lines().filter_map(|line| line.strip_prefix(&prefix));
            match (values.next(), values.next()) {
                (Some(value), None) => Ok(value),
                _ => Err(format!("PostgreSQL initdb --show omitted a single {name}")),
            }
        };
        Ok(Self {
            version: setting("VERSION")?.to_owned(),
            bindir: canonical_directory(setting("PGPATH")?, "initdb PGPATH")?,
            share: canonical_directory(setting("share_path")?, "initdb share_path")?,
        })
    }
}

/// Resolved and unresolved `DT_NEEDED` closure reported by the dynamic loader.
#[derive(Debug, Default, Eq, PartialEq)]
struct LoaderTrace {
    resolved: BTreeMap<String, PathBuf>,
    missing: BTreeSet<String>,
}

impl LoaderTrace {
    fn parse(output: &str) -> Result<Self, String> {
        let mut trace = Self::default();
        for line in output
            .lines()
            .map(str::trim)
            .filter(|line| !line.is_empty())
        {
            if let Some((name, target)) = line.split_once(" => ") {
                if target.trim() == "not found" {
                    trace.missing.insert(name.to_owned());
                    continue;
                }
                let path = loaded_path(target)?;
                if trace.resolved.insert(name.to_owned(), path).is_some() {
                    return Err(format!("dynamic loader listed {name} twice"));
                }
            } else if line.starts_with('/') {
                let path = loaded_path(line)?;
                let name = path
                    .file_name()
                    .and_then(|name| name.to_str())
                    .ok_or("dynamic loader interpreter has no file name")?
                    .to_owned();
                trace.resolved.insert(name, path);
            } else if line.contains(" (0x") && !line.contains('/') {
                // Kernel-provided vDSO: not a file.
            } else {
                return Err(format!("unrecognized dynamic loader trace line `{line}`"));
            }
        }
        if trace.resolved.is_empty() && trace.missing.is_empty() {
            return Err("dynamic loader trace listed no libraries".to_owned());
        }
        Ok(trace)
    }

    fn has_missing(&self) -> bool {
        !self.missing.is_empty()
    }
}

fn loaded_path(target: &str) -> Result<PathBuf, String> {
    let path = target
        .rsplit_once(" (0x")
        .map_or(target, |(path, _)| path)
        .trim();
    let path = PathBuf::from(path);
    if path.is_absolute() {
        Ok(path)
    } else {
        Err(format!(
            "dynamic loader resolved a relative library path `{}`",
            path.display()
        ))
    }
}

fn missing_names(traces: &BTreeMap<PathBuf, LoaderTrace>) -> String {
    traces
        .values()
        .flat_map(|trace| trace.missing.iter().map(String::as_str))
        .collect::<BTreeSet<_>>()
        .into_iter()
        .collect::<Vec<_>>()
        .join(", ")
}

fn locate_bin() -> Result<PathBuf, String> {
    if let Some(explicit) = std::env::var_os(BIN_ENVIRONMENT) {
        let path = PathBuf::from(&explicit);
        if explicit.is_empty() || !path.is_absolute() {
            return Err(format!("{BIN_ENVIRONMENT} must be an absolute directory"));
        }
        let canonical = fs::canonicalize(&path)
            .map_err(|error| format!("resolve {BIN_ENVIRONMENT} {}: {error}", path.display()))?;
        if !canonical.is_dir() {
            return Err(format!(
                "{BIN_ENVIRONMENT} {} is not a directory",
                path.display()
            ));
        }
        return Ok(canonical);
    }
    let search = std::env::var_os("PATH").unwrap_or_default();
    for entry in std::env::split_paths(&search) {
        // Relative or empty PATH entries depend on the caller's cwd; never trusted.
        if !entry.is_absolute() {
            continue;
        }
        let candidate = entry.join("initdb");
        if !fs::metadata(&candidate).is_ok_and(|metadata| metadata.is_file()) {
            continue;
        }
        let canonical = fs::canonicalize(&candidate)
            .map_err(|error| format!("resolve {}: {error}", candidate.display()))?;
        return canonical
            .parent()
            .map(Path::to_path_buf)
            .ok_or_else(|| format!("{} has no parent directory", canonical.display()));
    }
    Err(format!(
        "a postgres database fixture requires a native PostgreSQL {REQUIRED_MAJOR} \
         installation: set {BIN_ENVIRONMENT} or put its initdb on an absolute PATH entry"
    ))
}

fn trusted_owner(uid: u32) -> bool {
    // SAFETY: geteuid has no preconditions and cannot fail.
    uid == 0 || uid == unsafe { libc::geteuid() }
}

fn require_private_directory(path: &Path, label: &str) -> Result<(), String> {
    let metadata = fs::symlink_metadata(path)
        .map_err(|error| format!("inspect {label} {}: {error}", path.display()))?;
    if !metadata.is_dir() {
        return Err(format!("{label} {} is not a directory", path.display()));
    }
    if metadata.mode() & 0o022 != 0 || !trusted_owner(metadata.uid()) {
        return Err(format!(
            "{label} {} is writable by others or has an untrusted owner",
            path.display()
        ));
    }
    Ok(())
}

/// A canonical, native (ELF), executable, non-shared-writable regular file.
fn pinned_executable(bin: &Path, name: &str) -> Result<PathBuf, String> {
    let path = bin.join(name);
    let metadata = fs::symlink_metadata(&path)
        .map_err(|error| format!("PostgreSQL {name} not found at {}: {error}", path.display()))?;
    if !metadata.is_file() {
        return Err(format!(
            "PostgreSQL {name} at {} is not a canonical regular file",
            path.display()
        ));
    }
    if metadata.mode() & 0o111 == 0 {
        return Err(format!(
            "PostgreSQL {name} at {} is not executable",
            path.display()
        ));
    }
    if metadata.mode() & 0o022 != 0 || !trusted_owner(metadata.uid()) {
        return Err(format!(
            "PostgreSQL {name} at {} is writable by others or has an untrusted owner",
            path.display()
        ));
    }
    let mut magic = [0u8; 4];
    open_regular(&path)?
        .read_exact(&mut magic)
        .map_err(|error| format!("read PostgreSQL {name} header: {error}"))?;
    if &magic != b"\x7fELF" {
        return Err(format!(
            "PostgreSQL {name} at {} is not a native executable",
            path.display()
        ));
    }
    Ok(path)
}

fn canonical_directory(reported: &str, label: &str) -> Result<PathBuf, String> {
    let path = Path::new(reported);
    if !path.is_absolute() {
        return Err(format!("PostgreSQL {label} `{reported}` is not absolute"));
    }
    let canonical = fs::canonicalize(path)
        .map_err(|error| format!("resolve PostgreSQL {label} {reported}: {error}"))?;
    if !canonical.is_dir() {
        return Err(format!("PostgreSQL {label} {reported} is not a directory"));
    }
    Ok(canonical)
}

fn release_version(release: &str) -> Result<String, String> {
    let version = release.split_whitespace().next().unwrap_or_default();
    let (major, minor) = version
        .split_once('.')
        .ok_or_else(|| format!("PostgreSQL release `{release}` has no major.minor version"))?;
    let numeric = |part: &str| !part.is_empty() && part.bytes().all(|byte| byte.is_ascii_digit());
    if !numeric(major) || !numeric(minor) {
        return Err(format!(
            "PostgreSQL release `{release}` is not a final major.minor release"
        ));
    }
    if major.parse::<u32>().ok() != Some(REQUIRED_MAJOR) {
        return Err(format!(
            "database fixtures require PostgreSQL {REQUIRED_MAJOR}.x, found {version}"
        ));
    }
    Ok(version.to_owned())
}

fn sandbox_visible(path: &Path) -> bool {
    SANDBOX_SYSTEM_ROOTS
        .iter()
        .any(|root| path.starts_with(root))
}

fn default_loader_directory(path: &Path) -> bool {
    DEFAULT_LOADER_ROOTS.iter().any(|root| {
        path == Path::new(root)
            || path
                .parent()
                .is_some_and(|parent| parent == Path::new(root) && multiarch(path))
    })
}

fn multiarch(path: &Path) -> bool {
    path.file_name()
        .and_then(|name| name.to_str())
        .is_some_and(|name| name.ends_with("-linux-gnu") || name.ends_with("-linux-musl"))
}

fn visible_mounts<'a>(paths: impl IntoIterator<Item = &'a Path>) -> Vec<PathBuf> {
    paths
        .into_iter()
        .filter(|path| !sandbox_visible(path))
        .map(Path::to_path_buf)
        .collect()
}

/// Bootstrap requires Snowball dictionaries and the default plpgsql language.
/// Arbitrary extension modules and host-sized LLVM JIT workers are not enabled.
fn module_files(pkglib: &Path) -> Result<Vec<String>, String> {
    let mut modules = Vec::new();
    for entry in fs::read_dir(pkglib)
        .map_err(|error| format!("list PostgreSQL pkglibdir {}: {error}", pkglib.display()))?
    {
        let entry = entry.map_err(|error| format!("list PostgreSQL pkglibdir: {error}"))?;
        let Some(name) = entry.file_name().to_str().map(str::to_owned) else {
            return Err("PostgreSQL pkglibdir contains a non-UTF-8 name".to_owned());
        };
        if !matches!(name.as_str(), "plpgsql.so" | "dict_snowball.so") {
            continue;
        }
        let file_type = entry
            .file_type()
            .map_err(|error| format!("inspect PostgreSQL module {name}: {error}"))?;
        if !file_type.is_file() {
            return Err(format!("PostgreSQL module {name} is not a regular file"));
        }
        modules.push(name);
    }
    modules.sort();
    Ok(modules)
}

fn merge_libraries(
    libraries: &mut BTreeMap<String, PathBuf>,
    trace: &LoaderTrace,
) -> Result<(), String> {
    for (name, path) in &trace.resolved {
        if let Some(previous) = libraries.insert(name.clone(), path.clone())
            && &previous != path
        {
            return Err(format!(
                "PostgreSQL loader resolves {name} to different files"
            ));
        }
    }
    Ok(())
}

fn hash_tree(
    root: &Path,
    directory: &Path,
    files: &mut BTreeMap<String, String>,
) -> Result<(), String> {
    for entry in fs::read_dir(directory)
        .map_err(|error| format!("list PostgreSQL share {}: {error}", directory.display()))?
    {
        let entry = entry.map_err(|error| format!("list PostgreSQL share: {error}"))?;
        let path = entry.path();
        let file_type = entry
            .file_type()
            .map_err(|error| format!("inspect {}: {error}", path.display()))?;
        if file_type.is_dir() {
            hash_tree(root, &path, files)?;
        } else if file_type.is_file() {
            let relative = path
                .strip_prefix(root)
                .ok()
                .and_then(Path::to_str)
                .ok_or_else(|| format!("PostgreSQL share entry {} is not UTF-8", path.display()))?
                .to_owned();
            files.insert(relative, hash_regular(&path)?);
        } else {
            return Err(format!(
                "PostgreSQL share entry {} is not a regular file or directory",
                path.display()
            ));
        }
    }
    Ok(())
}

fn open_regular(path: &Path) -> Result<fs::File, String> {
    let file = OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_NOFOLLOW | libc::O_NONBLOCK | libc::O_CLOEXEC)
        .open(path)
        .map_err(|error| format!("open PostgreSQL toolchain file {}: {error}", path.display()))?;
    let metadata = file
        .metadata()
        .map_err(|error| format!("stat PostgreSQL toolchain file {}: {error}", path.display()))?;
    if !metadata.is_file() {
        return Err(format!(
            "PostgreSQL toolchain file {} is not a regular file",
            path.display()
        ));
    }
    Ok(file)
}

fn hash_regular(path: &Path) -> Result<String, String> {
    let mut file = open_regular(path)?;
    let mut digest = Sha256::new();
    let mut buffer = [0u8; 64 * 1024];
    loop {
        let read = file.read(&mut buffer).map_err(|error| {
            format!("hash PostgreSQL toolchain file {}: {error}", path.display())
        })?;
        if read == 0 {
            break;
        }
        digest.update(&buffer[..read]);
    }
    Ok(format!("sha256:{:x}", digest.finalize()))
}

fn map_digest(map: &BTreeMap<String, String>) -> String {
    let bytes = serde_json::to_vec(map).expect("string map serializes");
    format!("sha256:{}", sha256_hex(&bytes))
}

fn probe_limits() -> ResourceLimits {
    ResourceLimits {
        cpu_time: Duration::from_secs(10),
        address_space_bytes: 1024 * 1024 * 1024,
        process_count: 8,
        open_files: 64,
        file_size_bytes: 1024 * 1024,
        wall_time: Duration::from_secs(20),
        stream_limit_bytes: 1024 * 1024,
        writable_bytes: 1024 * 1024,
    }
}

fn probe_environment(library_path: Option<&Path>, trace: bool) -> BTreeMap<String, String> {
    let mut environment = BTreeMap::from([
        ("LANG".to_owned(), "C".to_owned()),
        ("LC_ALL".to_owned(), "C".to_owned()),
        ("PATH".to_owned(), "/usr/bin:/bin".to_owned()),
        ("TZ".to_owned(), "UTC".to_owned()),
    ]);
    if let Some(library_path) = library_path {
        environment.insert(
            "LD_LIBRARY_PATH".to_owned(),
            library_path.to_string_lossy().into_owned(),
        );
    }
    if trace {
        environment.insert("LD_TRACE_LOADED_OBJECTS".to_owned(), "1".to_owned());
    }
    environment
}

fn sandboxed(
    program: &Path,
    arguments: &[&str],
    environment: BTreeMap<String, String>,
    mounts: &[PathBuf],
    probe_root: &Path,
) -> Result<crate::sandbox::CompletedProcess, String> {
    run(&SandboxSpec {
        program: program.to_path_buf(),
        arguments: arguments
            .iter()
            .map(|argument| (*argument).to_owned())
            .collect(),
        cwd: probe_root.to_path_buf(),
        environment,
        stdin: Vec::new(),
        binds: BindMounts {
            read_only: mounts.to_vec(),
            writable: vec![probe_root.to_path_buf()],
        },
        network: NetworkAccess::Disabled,
        limits: probe_limits(),
    })
    .map_err(|error| format!("PostgreSQL fixture toolchain probe unavailable: {error}"))
}

fn probe(
    program: &Path,
    arguments: &[&str],
    library_path: Option<&Path>,
    mounts: &[PathBuf],
    probe_root: &Path,
) -> Result<String, String> {
    let completed = sandboxed(
        program,
        arguments,
        probe_environment(library_path, false),
        mounts,
        probe_root,
    )?;
    let label = format!(
        "{} {}",
        program.file_name().unwrap_or_default().to_string_lossy(),
        arguments.join(" ")
    );
    if completed.status != Some(0) || completed.timed_out {
        return Err(format!(
            "PostgreSQL probe `{label}` failed with {:?}: {}",
            completed.status,
            String::from_utf8_lossy(&completed.stderr).trim()
        ));
    }
    String::from_utf8(completed.stdout)
        .map_err(|_| format!("PostgreSQL probe `{label}` wrote non-UTF-8 output"))
}

fn trace(
    executables: &[&Path],
    library_path: Option<&Path>,
    mounts: &[PathBuf],
    probe_root: &Path,
) -> Result<BTreeMap<PathBuf, LoaderTrace>, String> {
    let mut traces = BTreeMap::new();
    for executable in executables {
        let completed = sandboxed(
            executable,
            &[],
            probe_environment(library_path, true),
            mounts,
            probe_root,
        )?;
        let output = String::from_utf8(completed.stdout)
            .map_err(|_| "dynamic loader trace wrote non-UTF-8 output".to_owned())?;
        let trace = LoaderTrace::parse(&output)?;
        if completed.timed_out || (completed.status != Some(0) && !trace.has_missing()) {
            return Err(format!(
                "dynamic loader trace of {} failed with {:?}: {}",
                executable.display(),
                completed.status,
                String::from_utf8_lossy(&completed.stderr).trim()
            ));
        }
        traces.insert(executable.to_path_buf(), trace);
    }
    Ok(traces)
}

fn single_line<'a>(output: &'a str, label: &str) -> Result<&'a str, String> {
    let mut lines = output.lines();
    match (lines.next(), lines.next()) {
        (Some(line), None) => Ok(line),
        _ => Err(format!("{label} did not print exactly one line")),
    }
}

#[cfg(test)]
mod tests {
    use super::*;

    #[test]
    fn loader_trace_separates_resolved_missing_interpreter_and_vdso() {
        let trace = LoaderTrace::parse(
            "\tlinux-vdso.so.1 (0x00007ffcaa81a000)\n\
             \tlibpq.so.5 => /opt/pg/lib/libpq.so.5 (0x0000781156b1b000)\n\
             \tlibicuuc.so.74 => not found\n\
             \t/lib64/ld-linux-x86-64.so.2 (0x0000781156b98000)\n",
        )
        .expect("trace parses");
        assert_eq!(
            trace.resolved,
            BTreeMap::from([
                (
                    "ld-linux-x86-64.so.2".to_owned(),
                    PathBuf::from("/lib64/ld-linux-x86-64.so.2")
                ),
                (
                    "libpq.so.5".to_owned(),
                    PathBuf::from("/opt/pg/lib/libpq.so.5")
                ),
            ])
        );
        assert_eq!(trace.missing, BTreeSet::from(["libicuuc.so.74".to_owned()]));
    }

    #[test]
    fn loader_trace_rejects_relative_duplicate_and_unknown_lines() {
        assert!(LoaderTrace::parse("\tlibpq.so.5 => lib/libpq.so.5 (0x1)\n").is_err());
        assert!(
            LoaderTrace::parse(
                "\tlibpq.so.5 => /a/libpq.so.5 (0x1)\n\tlibpq.so.5 => /b/libpq.so.5 (0x2)\n"
            )
            .is_err()
        );
        assert!(LoaderTrace::parse("\tstatically linked\n").is_err());
        assert!(LoaderTrace::parse("").is_err());
    }

    #[test]
    fn only_final_postgresql_16_releases_are_accepted() {
        assert_eq!(
            release_version("16.15 (Ubuntu 16.15-0ubuntu0.24.04.1)").as_deref(),
            Ok("16.15")
        );
        assert_eq!(release_version("16.0").as_deref(), Ok("16.0"));
        for rejected in ["15.8", "17.2 (Debian)", "16beta1", "16", "16.x", ""] {
            assert!(release_version(rejected).is_err(), "{rejected} accepted");
        }
    }

    #[test]
    fn pg_config_report_must_have_exact_shape_and_release_prefix() {
        let root = std::env::temp_dir();
        let root = root.to_string_lossy();
        let report = format!("PostgreSQL 16.15 (Ubuntu)\n{root}\n{root}\n{root}\n{root}\n");
        let parsed = PgConfig::parse(&report).expect("pg_config parses");
        assert_eq!(parsed.version, "16.15");
        assert_eq!(parsed.release, "16.15 (Ubuntu)");
        assert!(PgConfig::parse(&format!("PostgreSQL 16.15\n{root}\n{root}\n{root}\n")).is_err());
        assert!(
            PgConfig::parse(&format!(
                "EnterpriseDB 16.15\n{root}\n{root}\n{root}\n{root}\n"
            ))
            .is_err()
        );
        assert!(
            PgConfig::parse(&format!(
                "PostgreSQL 16.15\nrelative\n{root}\n{root}\n{root}\n"
            ))
            .is_err()
        );
    }

    #[test]
    fn initdb_show_requires_single_settings() {
        let root = std::env::temp_dir();
        let root = root.to_string_lossy();
        let shown = InitdbSettings::parse(&format!(
            "The files belonging to this database system will be owned by user \"u\".\n\n\
             VERSION=16.15 (Ubuntu)\nPGDATA=/x\nshare_path={root}\nPGPATH={root}\n"
        ))
        .expect("initdb settings parse");
        assert_eq!(shown.version, "16.15 (Ubuntu)");
        assert!(
            InitdbSettings::parse(&format!(
                "VERSION=16.15\nshare_path={root}\nshare_path={root}\nPGPATH={root}\n"
            ))
            .is_err()
        );
        assert!(InitdbSettings::parse(&format!("VERSION=16.15\nPGPATH={root}\n")).is_err());
    }

    #[test]
    fn only_system_roots_are_implicitly_visible_and_default_searched() {
        assert!(sandbox_visible(Path::new(
            "/usr/lib/postgresql/16/bin/initdb"
        )));
        assert!(sandbox_visible(Path::new(
            "/lib/x86_64-linux-gnu/libc.so.6"
        )));
        assert!(!sandbox_visible(Path::new(
            "/tmp/cott-pg/root/usr/lib/postgresql/16/bin"
        )));
        assert!(!sandbox_visible(Path::new("/usrx/lib")));
        assert!(default_loader_directory(Path::new(
            "/usr/lib/x86_64-linux-gnu"
        )));
        assert!(default_loader_directory(Path::new("/lib64")));
        assert!(!default_loader_directory(Path::new("/usr/local/pgsql/lib")));
        assert!(!default_loader_directory(Path::new(
            "/tmp/cott-pg/root/usr/lib/x86_64-linux-gnu"
        )));
    }

    #[test]
    fn frozen_closure_names_the_drifted_part_and_identity_has_no_paths() {
        let frozen = Closure {
            initdb: "sha256:1".to_owned(),
            postgres: "sha256:2".to_owned(),
            share: BTreeMap::from([("postgres.bki".to_owned(), "sha256:3".to_owned())]),
            modules: BTreeMap::from([("plpgsql.so".to_owned(), "sha256:4".to_owned())]),
            libraries: BTreeMap::from([("libpq.so.5".to_owned(), "sha256:5".to_owned())]),
        };
        assert_eq!(frozen.drift(&frozen.clone()), None);
        let mut added = frozen.clone();
        added
            .share
            .insert("extension/new.sql".to_owned(), "sha256:6".to_owned());
        assert_eq!(frozen.drift(&added), Some("share directory"));
        let mut swapped = frozen.clone();
        swapped
            .libraries
            .insert("libpq.so.5".to_owned(), "sha256:7".to_owned());
        assert_eq!(frozen.drift(&swapped), Some("loader closure"));

        let root = std::env::temp_dir();
        let root = root.to_string_lossy();
        let configured = PgConfig::parse(&format!(
            "PostgreSQL 16.15 (Ubuntu)\n{root}\n{root}\n{root}\n{root}\n"
        ))
        .expect("pg_config parses");
        let identity = frozen.identity(&configured);
        assert_eq!(identity["version"], "16.15");
        assert_eq!(identity["release"], "PostgreSQL 16.15 (Ubuntu)");
        assert!(!identity.to_string().contains(root.as_ref()));
        assert_eq!(identity.as_object().map(serde_json::Map::len), Some(7));
    }
}
