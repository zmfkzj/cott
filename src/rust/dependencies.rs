//! Frozen Cargo authority: original archive checksums authenticate bounded trees, never
//! mutable extracted-cache checksum sidecars. Loading and resolving never invoke Cargo
//! or download. The compiler owns an exact registry lock, offline vendor configuration,
//! and relocated local dependency manifests. Only production library names grant imports;
//! build/dev packages remain authenticated in the closed record without that authority.
//! Cargo lock formats 3/4 are accepted; the closed record requires one version per name.
//! Runtime pins below were confirmed with Cargo's resolver for rt/rt-multi-thread/sync/time.

use crate::hash::sha256_hex;
use crate::manifest::RustProjectConfig;
use crate::project::RustPaths;
use flate2::read::MultiGzDecoder;
use serde_json::{Value, json};
use sha2::{Digest, Sha256};
use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, OpenOptions};
use std::io::{self, Read};
use std::os::unix::fs::{MetadataExt, OpenOptionsExt};
use std::path::{Component, Path, PathBuf};
use std::sync::Arc;

const REGISTRY: &str = "registry+https://github.com/rust-lang/crates.io-index";
const MAX_BYTES: u64 = 256 * 1024 * 1024;
const MAX_FILES: usize = 20_000;
const RUNTIME: &[(&str, &str, &str)] = &[
    (
        "pin-project-lite",
        "0.2.17",
        "a89322df9ebe1c1578d689c92318e070967d1042b512afbe49518723f4e6d5cd",
    ),
    (
        "tokio",
        "1.53.1",
        "202caea871b69668250d242070849eb495be178ed697a3e98aebce5bc81a0bed",
    ),
];
const CONFIG: &[u8] = b"[source.crates-io]\nreplace-with = \"cott-vendor\"\n[source.cott-vendor]\ndirectory = \"vendor\"\n[net]\noffline = true\n";

#[derive(Clone, Debug)]
pub(crate) struct PackageMetadata {
    name: String,
    version: String,
    root: PathBuf,
    manifest: toml::Value,
    locked: BTreeMap<String, Locked>,
    inputs: BTreeMap<PathBuf, Vec<u8>>,
    runtime_package_names: BTreeSet<String>,
    production_packages: BTreeSet<String>,
    frozen: ResolvedDependencies,
}
#[derive(Clone, Debug)]
struct Locked {
    version: String,
    checksum: Option<String>,
    path: Option<PathBuf>,
    dependencies: Vec<String>,
}
#[derive(Clone, Debug, Eq, PartialEq)]
pub(crate) struct ResolvedPackage {
    pub name: String,
    pub version: String,
    pub source: &'static str,
    pub source_identity: String,
    pub content_hash: String,
    pub dependencies: Vec<String>,
    pub root: PathBuf,
}
#[derive(Clone, Debug)]
pub(crate) struct ResolvedDependencies {
    pub packages: Vec<ResolvedPackage>,
    pub record: Value,
    pub artifacts: BTreeMap<PathBuf, Vec<u8>>,
    package_trees: BTreeMap<String, Arc<BTreeMap<PathBuf, Vec<u8>>>>,
}
fn parse(bytes: &[u8]) -> Result<toml::Value, String> {
    std::str::from_utf8(bytes)
        .map_err(|e| e.to_string())?
        .parse()
        .map_err(|e: toml::de::Error| e.to_string())
}
fn text<'a>(v: &'a toml::Value, key: &str) -> Result<&'a str, String> {
    v.get(key)
        .and_then(toml::Value::as_str)
        .ok_or_else(|| format!("Cargo metadata requires string `{key}`"))
}
fn version(value: &str) -> Result<semver::Version, String> {
    let v = semver::Version::parse(value).map_err(|e| e.to_string())?;
    if !v.pre.is_empty() || !v.build.is_empty() {
        return Err(format!(
            "Cargo prerelease/build version `{value}` is not supported"
        ));
    }
    Ok(v)
}
fn reject_overrides(v: &toml::Value) -> Result<(), String> {
    for key in ["patch", "replace", "workspace", "source"] {
        if v.get(key).is_some() {
            return Err(format!("Cargo `{key}` overrides/workspaces are forbidden"));
        }
    }
    if v.get("package").and_then(|p| p.get("workspace")).is_some() {
        return Err("Cargo workspace inheritance is forbidden".into());
    }
    Ok(())
}
fn sections(v: &toml::Value) -> Vec<(&str, &toml::map::Map<String, toml::Value>)> {
    let mut result = Vec::new();
    for kind in ["dependencies", "build-dependencies", "dev-dependencies"] {
        if let Some(t) = v.get(kind).and_then(toml::Value::as_table) {
            result.push((kind, t));
        }
    }
    if let Some(targets) = v.get("target").and_then(toml::Value::as_table) {
        for target in targets.values() {
            for kind in ["dependencies", "build-dependencies", "dev-dependencies"] {
                if let Some(t) = target.get(kind).and_then(toml::Value::as_table) {
                    result.push((kind, t));
                }
            }
        }
    }
    result
}
fn dep_name<'a>(alias: &'a str, d: &'a toml::Value) -> &'a str {
    d.get("package")
        .and_then(toml::Value::as_str)
        .unwrap_or(alias)
}
fn default_cache() -> Result<PathBuf, String> {
    std::env::var_os("CARGO_HOME")
        .map(PathBuf::from)
        .or_else(|| std::env::var_os("HOME").map(|h| PathBuf::from(h).join(".cargo")))
        .ok_or_else(|| "CARGO_HOME or HOME is required for offline Cargo archives".into())
}
pub(crate) fn load_metadata(
    config: &RustProjectConfig,
    paths: &RustPaths,
) -> Result<PackageMetadata, String> {
    let name = config.project.name.clone();
    let ver = config.project.version.clone();
    version(&ver)?;
    let mut inputs = BTreeMap::new();
    let (manifest, lock_bytes) = match (&paths.cargo_manifest, &paths.lockfile) {
        (None, None) => (
            parse(format!("[package]\nname={name:?}\nversion={ver:?}\n").as_bytes())?,
            None,
        ),
        (Some(m), Some(l)) => {
            let mb = read_file(m, 4 * 1024 * 1024)?;
            let lb = read_file(l, 4 * 1024 * 1024)?;
            inputs.insert(m.clone(), mb.clone());
            inputs.insert(l.clone(), lb.clone());
            (parse(&mb)?, Some(lb))
        }
        _ => {
            return Err(
                "target.rust.cargo_manifest and lockfile must be configured together".into(),
            );
        }
    };
    reject_overrides(&manifest)?;
    let package = manifest
        .get("package")
        .ok_or("Cargo.toml requires [package]")?;
    if text(package, "name")? != name || text(package, "version")? != ver {
        return Err("Cargo package name/version must equal the Cott project".into());
    }
    // A project-local Cargo config could silently replace the locked registry.
    let mut dir = paths
        .cargo_manifest
        .as_ref()
        .and_then(|p| p.parent())
        .unwrap_or(&paths.root);
    loop {
        for config in [".cargo/config", ".cargo/config.toml"] {
            if dir.join(config).exists() {
                return Err(format!(
                    "Cargo source/config overrides are forbidden: {}",
                    dir.join(config).display()
                ));
            }
        }
        if dir == paths.root {
            break;
        }
        dir = dir.parent().ok_or("Cargo manifest is outside project")?;
    }
    let mut locked = BTreeMap::new();
    let mut root_edges = None;
    if let Some(bytes) = &lock_bytes {
        let lock = parse(bytes)?;
        if !matches!(
            lock.get("version").and_then(toml::Value::as_integer),
            Some(3 | 4)
        ) {
            return Err("Cargo.lock must use version 3 or 4".into());
        }
        for p in lock
            .get("package")
            .and_then(toml::Value::as_array)
            .ok_or("Cargo.lock requires packages")?
        {
            let n = text(p, "name")?.to_owned();
            if n.is_empty()
                || n.len() > 64
                || n.as_bytes()[0].is_ascii_digit()
                || !n
                    .bytes()
                    .all(|b| b.is_ascii_alphanumeric() || matches!(b, b'_' | b'-'))
            {
                return Err(format!("invalid Cargo dependency package name `{n}`"));
            }
            let v = text(p, "version")?.to_owned();
            version(&v)?;
            let checksum = match p.get("source") {
                Some(s) if s.as_str() == Some(REGISTRY) => {
                    let c = text(p, "checksum")?;
                    if c.len() != 64
                        || !c
                            .bytes()
                            .all(|b| b.is_ascii_hexdigit() && !b.is_ascii_uppercase())
                    {
                        return Err(format!("invalid Cargo checksum for `{n}`"));
                    }
                    Some(c.to_owned())
                }
                Some(_) => {
                    return Err(format!(
                        "Cargo dependency `{n}` must use crates.io or a project-local path; git and alternate registries are forbidden"
                    ));
                }
                None => None,
            };
            let mut dependencies = Vec::new();
            if let Some(ds) = p.get("dependencies").and_then(toml::Value::as_array) {
                for d in ds {
                    dependencies.push(
                        d.as_str()
                            .ok_or("invalid Cargo.lock dependency")?
                            .to_owned(),
                    );
                }
            }
            if locked
                .insert(
                    n.clone(),
                    Locked {
                        version: v,
                        checksum,
                        path: None,
                        dependencies,
                    },
                )
                .is_some()
            {
                return Err(format!("Cargo.lock must contain a single version of `{n}`"));
            }
            if locked.len() > 256 {
                return Err("Cargo.lock exceeds 256 packages".into());
            }
        }
        let root = locked
            .remove(&name)
            .ok_or("Cott project package is missing from Cargo.lock")?;
        if root.version != ver || root.checksum.is_some() {
            return Err("Cargo.lock root name/version/source mismatch".into());
        }
        root_edges = Some(
            root.dependencies
                .iter()
                .map(|d| d.split_whitespace().next().unwrap_or("").to_owned())
                .collect::<Vec<_>>(),
        );
    }
    let declaring_dir = paths
        .cargo_manifest
        .as_ref()
        .and_then(|p| p.parent())
        .unwrap_or(&paths.root);
    discover_paths(
        &manifest,
        declaring_dir,
        &paths.root,
        &mut locked,
        &mut inputs,
        &mut BTreeSet::new(),
    )?;
    validate_declarations(&manifest, &locked, root_edges.as_ref())?;
    validate_declarations(&manifest, &locked, None)?;
    if let Some(edges) = &root_edges {
        let declared = sections(&manifest)
            .into_iter()
            .flat_map(|(_, ds)| ds.iter().map(|(a, d)| dep_name(a, d).to_owned()))
            .collect::<BTreeSet<_>>();
        if edges.iter().any(|d| !declared.contains(d)) {
            return Err("Cargo.lock root dependencies disagree with declared requirements".into());
        }
    }
    for (n, v, c) in RUNTIME {
        if let Some(old) = locked.get(*n) {
            if old.version != *v || old.checksum.as_deref() != Some(*c) {
                return Err(format!(
                    "Cargo runtime dependency `{n}` must be exactly {v} with pinned checksum {c}"
                ));
            }
        } else {
            locked.insert(
                (*n).into(),
                Locked {
                    version: (*v).into(),
                    checksum: Some((*c).into()),
                    path: None,
                    dependencies: if *n == "tokio" {
                        vec!["pin-project-lite".into()]
                    } else {
                        vec![]
                    },
                },
            );
        }
    }
    for (name, p) in &locked {
        for edge in &p.dependencies {
            let mut parts = edge.split_whitespace();
            let dependency = parts.next().ok_or("empty Cargo lock edge")?;
            let target = locked
                .get(dependency)
                .ok_or_else(|| format!("Cargo.lock edge `{name}` -> `{edge}` is not closed"))?;
            if let Some(v) = parts.next() {
                if v != target.version {
                    return Err(format!(
                        "Cargo.lock edge `{edge}` has a mismatched locked version"
                    ));
                }
                if let Some(source) = parts.next() {
                    if source != format!("({REGISTRY})") || target.checksum.is_none() {
                        return Err(format!("Cargo.lock edge `{edge}` has a mismatched source"));
                    }
                }
                if parts.next().is_some() {
                    return Err("invalid Cargo lock edge".into());
                }
            }
        }
    }
    for p in locked.values_mut() {
        p.dependencies = p
            .dependencies
            .iter()
            .map(|s| s.split_whitespace().next().unwrap_or("").to_owned())
            .collect();
        p.dependencies.sort();
        p.dependencies.dedup();
    }
    for (n, p) in &locked {
        for d in &p.dependencies {
            if !locked.contains_key(d) || d == n {
                return Err(format!(
                    "Cargo.lock dependency edge `{n}` -> `{d}` is not closed"
                ));
            }
        }
    }
    let empty = ResolvedDependencies {
        packages: vec![],
        record: Value::Null,
        artifacts: BTreeMap::new(),
        package_trees: BTreeMap::new(),
    };
    let mut metadata = PackageMetadata {
        name,
        version: ver,
        root: paths.root.clone(),
        manifest,
        locked,
        inputs,
        runtime_package_names: BTreeSet::new(),
        production_packages: BTreeSet::new(),
        frozen: empty,
    };
    let cache = default_cache()?;
    let mut resolved = materialize(&metadata, &cache)?;
    validate_declarations(&metadata.manifest, &metadata.locked, None)?;
    for (n, tree) in &resolved.package_trees {
        let m = parse(
            tree.get(Path::new("Cargo.toml"))
                .ok_or_else(|| format!("Cargo dependency `{n}` has no Cargo.toml"))?,
        )?;
        reject_overrides(&m)?;
        let p = m.get("package").ok_or("dependency requires [package]")?;
        if text(p, "name")? != n || text(p, "version")? != metadata.locked[n].version {
            return Err(format!("Cargo archive/path identity mismatch for `{n}`"));
        }
        validate_declarations(&m, &metadata.locked, Some(&metadata.locked[n].dependencies))?;
    }
    let production = production_closure(&metadata, &resolved)?;
    metadata.production_packages = production.clone();
    metadata.runtime_package_names = production
        .iter()
        .map(|n| {
            let m = parse(&resolved.package_trees[n][Path::new("Cargo.toml")])?;
            Ok(m.get("lib")
                .and_then(|l| l.get("name"))
                .and_then(toml::Value::as_str)
                .unwrap_or(n)
                .replace('-', "_"))
        })
        .collect::<Result<_, String>>()?;
    for (kind, dependencies) in sections(&metadata.manifest) {
        if kind != "dependencies" {
            continue;
        }
        for (alias, declaration) in dependencies {
            let package = dep_name(alias, declaration);
            if alias == package || !production.contains(package) {
                continue;
            }
            if package == "tokio" {
                return Err("the compiler-owned tokio runtime dependency cannot be renamed".into());
            }
            let manifest = parse(&resolved.package_trees[package][Path::new("Cargo.toml")])?;
            let library = manifest
                .get("lib")
                .and_then(|v| v.get("name"))
                .and_then(toml::Value::as_str)
                .unwrap_or(package)
                .replace('-', "_");
            metadata.runtime_package_names.remove(&library);
            metadata
                .runtime_package_names
                .insert(alias.replace('-', "_"));
        }
    }
    let manifest_bytes = generated_manifest(&metadata, false)?;
    let lock = lock_bytes_generated(&metadata)?;
    let authored_manifest = paths
        .cargo_manifest
        .as_ref()
        .and_then(|p| metadata.inputs.get(p));
    let packages = resolved.packages.iter().map(|p|json!({"name":p.name,"version":p.version,"source":p.source,"source_identity":p.source_identity,"content_hash":p.content_hash,"dependencies":p.dependencies,"runtime":production.contains(&p.name)})).collect::<Vec<_>>();
    resolved.record = json!({"schema_version":1,"cargo_manifest_hash":digest(authored_manifest.map(Vec::as_slice).unwrap_or(&manifest_bytes)),"lockfile_hash":digest(lock_bytes.as_deref().unwrap_or(&lock)),"packages":packages});
    resolved
        .artifacts
        .insert("rust/Cargo.toml".into(), manifest_bytes);
    resolved.artifacts.insert("rust/Cargo.lock".into(), lock);
    resolved.artifacts.insert(
        "rust/dependencies.json".into(),
        json_bytes(&resolved.record)?,
    );
    resolved
        .artifacts
        .insert("rust/.cargo/config.toml".into(), CONFIG.to_vec());
    metadata.frozen = resolved;
    Ok(metadata)
}
fn discover_paths(
    m: &toml::Value,
    dir: &Path,
    root: &Path,
    locked: &mut BTreeMap<String, Locked>,
    inputs: &mut BTreeMap<PathBuf, Vec<u8>>,
    seen: &mut BTreeSet<PathBuf>,
) -> Result<(), String> {
    reject_overrides(m)?;
    for (_, deps) in sections(m) {
        for (alias, d) in deps {
            for forbidden in ["git", "registry", "registry-index", "workspace"] {
                if d.get(forbidden).is_some() {
                    return Err(format!(
                        "Cargo dependency `{alias}` uses forbidden `{forbidden}`"
                    ));
                }
            }
            if let Some(path) = d.get("path").and_then(toml::Value::as_str) {
                let abs = canonical_local(&dir.join(path), root)?;
                let name = dep_name(alias, d);
                let p = locked.get_mut(name).ok_or_else(|| {
                    format!("declared Cargo dependency `{name}` absent from lock")
                })?;
                if p.checksum.is_some() {
                    return Err(format!("Cargo path/registry source mismatch for `{name}`"));
                }
                if p.path.as_ref().is_some_and(|old| old != &abs) {
                    return Err(format!("conflicting paths for Cargo dependency `{name}`"));
                }
                p.path = Some(abs.clone());
                if seen.insert(abs.clone()) {
                    let bytes = read_file(&abs.join("Cargo.toml"), 4 * 1024 * 1024)?;
                    inputs.insert(abs.join("Cargo.toml"), bytes.clone());
                    discover_paths(&parse(&bytes)?, &abs, root, locked, inputs, seen)?;
                }
            }
        }
    }
    Ok(())
}
fn canonical_local(path: &Path, root: &Path) -> Result<PathBuf, String> {
    let abs = fs::canonicalize(path).map_err(|e| format!("Cargo path {}: {e}", path.display()))?;
    if !abs.starts_with(root) || abs == root {
        return Err(format!("Cargo path {} escapes project", path.display()));
    }
    let mut cur = root.to_path_buf();
    for c in path
        .strip_prefix(root)
        .map_err(|_| "Cargo path escapes project")?
        .components()
    {
        match c {
            Component::Normal(n) => cur.push(n),
            Component::ParentDir => {
                cur.pop();
            }
            Component::CurDir => {}
            _ => return Err("invalid Cargo path".into()),
        }
        if fs::symlink_metadata(&cur)
            .map_err(|e| e.to_string())?
            .file_type()
            .is_symlink()
        {
            return Err("Cargo path contains symlink".into());
        }
        if !cur.starts_with(root) {
            return Err("Cargo path escapes project".into());
        }
    }
    Ok(abs)
}
fn validate_declarations(
    m: &toml::Value,
    locked: &BTreeMap<String, Locked>,
    edges: Option<&Vec<String>>,
) -> Result<(), String> {
    for (kind, deps) in sections(m) {
        for (alias, d) in deps {
            if kind == "dev-dependencies" && edges.is_some() {
                continue;
            }
            let name = dep_name(alias, d);
            let optional = d.get("optional").and_then(toml::Value::as_bool) == Some(true);
            let present = edges
                .map(|e| e.iter().any(|n| n == name))
                .unwrap_or_else(|| locked.contains_key(name));
            if !present {
                if optional {
                    continue;
                }
                return Err(format!(
                    "declared Cargo dependency `{name}` is absent from locked dependencies"
                ));
            }
            let p = locked
                .get(name)
                .ok_or_else(|| format!("Cargo dependency `{name}` absent from lock"))?;
            if let Some(req) = d
                .as_str()
                .or_else(|| d.get("version").and_then(toml::Value::as_str))
            {
                let r = semver::VersionReq::parse(req)
                    .map_err(|e| format!("Cargo requirement `{req}`: {e}"))?;
                if r.comparators.iter().any(|c| !c.pre.is_empty()) || req.contains('+') {
                    return Err("Cargo prerelease/build requirements are forbidden".into());
                }
                if !r.matches(&version(&p.version)?) {
                    return Err(format!(
                        "declared Cargo requirement `{name}` {req} disagrees with locked {}",
                        p.version
                    ));
                }
            } else if d.get("path").is_none() {
                return Err(format!("Cargo dependency `{name}` has no version/path"));
            }
            if d.get("git").is_some() || d.get("registry").is_some() || d.get("workspace").is_some()
            {
                return Err(format!("unsupported Cargo source for `{name}`"));
            }
            if d.get("path").is_some() != p.path.is_some() {
                return Err(format!(
                    "declared Cargo source for `{name}` disagrees with lock"
                ));
            }
        }
    }
    Ok(())
}
fn production_closure(
    metadata: &PackageMetadata,
    resolved: &ResolvedDependencies,
) -> Result<BTreeSet<String>, String> {
    // Track feature unification separately from the full (including build/dev) lock closure.
    let mut pending = vec![(
        metadata.name.clone(),
        BTreeSet::from(["default".to_owned()]),
    )];
    let mut features: BTreeMap<String, BTreeSet<String>> = BTreeMap::new();
    let mut production = BTreeSet::new();
    while let Some((name, requested)) = pending.pop() {
        let old = features.entry(name.clone()).or_default();
        let first = old.is_empty();
        let before = old.len();
        old.extend(requested);
        if !first && before == old.len() {
            continue;
        }
        let m = if name == metadata.name {
            metadata.manifest.clone()
        } else {
            parse(&resolved.package_trees[&name][Path::new("Cargo.toml")])?
        };
        let mut active = old.clone();
        let mut todo = active.iter().cloned().collect::<Vec<_>>();
        while let Some(f) = todo.pop() {
            if let Some(ds) = m
                .get("features")
                .and_then(|v| v.get(&f))
                .and_then(toml::Value::as_array)
            {
                for d in ds {
                    let d = d.as_str().ok_or("invalid Cargo feature")?;
                    if active.insert(d.into()) {
                        todo.push(d.into());
                    }
                }
            }
        }
        for (kind, deps) in sections(&m) {
            if kind != "dependencies" {
                continue;
            }
            for (alias, d) in deps {
                let n = dep_name(alias, d);
                let activated = d.get("optional").and_then(toml::Value::as_bool) != Some(true)
                    || active.contains(alias)
                    || active.contains(&format!("dep:{alias}"))
                    || active.iter().any(|f| f.starts_with(&format!("{alias}/")));
                if !activated || !metadata.locked.contains_key(n) {
                    continue;
                }
                let mut fs = BTreeSet::new();
                if d.get("default-features").and_then(toml::Value::as_bool) != Some(false) {
                    fs.insert("default".into());
                }
                if let Some(values) = d.get("features").and_then(toml::Value::as_array) {
                    for f in values {
                        fs.insert(f.as_str().ok_or("invalid dependency feature")?.into());
                    }
                }
                for f in &active {
                    if let Some((dep, feature)) = f.split_once('/') {
                        if dep.trim_end_matches('?') == alias {
                            fs.insert(feature.into());
                        }
                    }
                }
                // A sentinel ensures featureless crates are visited once.
                fs.insert("__cott_visit".into());
                production.insert(n.into());
                pending.push((n.into(), fs));
            }
        }
    }
    production.insert("tokio".into());
    production.insert("pin-project-lite".into());
    Ok(production)
}
fn materialize(metadata: &PackageMetadata, cache: &Path) -> Result<ResolvedDependencies, String> {
    let mut packages = Vec::new();
    let mut trees = BTreeMap::new();
    let mut artifacts = BTreeMap::new();
    for (name, p) in &metadata.locked {
        let (root, tree, source, identity) = if let Some(c) = &p.checksum {
            let archive = archive_path(cache, name, &p.version)?;
            let bytes = read_file(&archive, MAX_BYTES)?;
            if sha256_hex(&bytes) != *c {
                return Err(format!(
                    "Cargo archive checksum mismatch for `{name}` {} at {}: lock requires sha256:{c}",
                    p.version,
                    archive.display()
                ));
            }
            let tree = archive_tree(&bytes, &format!("{name}-{}", p.version))?;
            let index = archive
                .parent()
                .and_then(Path::file_name)
                .ok_or("invalid Cargo cache")?;
            let extracted = cache
                .join("registry/src")
                .join(index)
                .join(format!("{name}-{}", p.version));
            if extracted.exists() {
                let mut actual = read_tree(&extracted)?;
                actual.remove(Path::new(".cargo-ok"));
                actual.remove(Path::new(".cargo-checksum.json"));
                if actual != tree {
                    return Err(format!(
                        "Cargo extracted tree for `{name}` was tampered: {}",
                        extracted.display()
                    ));
                }
            }
            (
                extracted,
                tree,
                "registry",
                format!("{REGISTRY}#sha256:{c}"),
            )
        } else {
            let root = p.path.clone().ok_or_else(|| {
                format!("Cargo lock package `{name}` has no authenticated project-local path")
            })?;
            let tree = read_tree(&root)?;
            let identity = root
                .strip_prefix(&metadata.root)
                .map_err(|_| "Cargo path escape")?
                .to_str()
                .ok_or("non-UTF8 Cargo path")?
                .to_owned();
            (root, tree, "path", identity)
        };
        let content_hash = tree_hash(&tree);
        let destination = if source == "registry" {
            PathBuf::from(format!("rust/vendor/{name}-{}", p.version))
        } else {
            PathBuf::from(format!("rust/deps/{name}"))
        };
        let staged = if source == "path" {
            rewrite_path_manifest(&tree, metadata)?
        } else {
            tree.clone()
        };
        for (path, bytes) in &staged {
            artifacts.insert(destination.join(path), bytes.clone());
        }
        if source == "registry" {
            let files = tree
                .iter()
                .map(|(p, b)| (p.to_string_lossy().into_owned(), sha256_hex(b)))
                .collect::<BTreeMap<_, _>>();
            artifacts.insert(
                destination.join(".cargo-checksum.json"),
                json_bytes(&json!({"files":files,"package":p.checksum}))?,
            );
        }
        packages.push(ResolvedPackage {
            name: name.clone(),
            version: p.version.clone(),
            source,
            source_identity: identity,
            content_hash,
            dependencies: p.dependencies.clone(),
            root,
        });
        trees.insert(name.clone(), Arc::new(tree));
    }
    Ok(ResolvedDependencies {
        packages,
        record: Value::Null,
        artifacts,
        package_trees: trees,
    })
}
fn archive_path(cache: &Path, name: &str, ver: &str) -> Result<PathBuf, String> {
    let base = cache.join("registry/cache");
    let expected = format!("{name}-{ver}.crate");
    let mut matches = Vec::new();
    if let Ok(entries) = fs::read_dir(&base) {
        for entry in entries {
            let entry = entry.map_err(|e| e.to_string())?;
            if entry
                .file_name()
                .to_str()
                .is_some_and(|n| n.starts_with("index.crates.io-"))
            {
                let p = entry.path().join(&expected);
                if p.exists() {
                    matches.push(p);
                }
            }
        }
    }
    matches.sort();
    matches.into_iter().next().ok_or_else(||format!("missing original Cargo archive for locked `{name}` {ver} ({REGISTRY}); expected {}/index.crates.io-*/{expected}; prepare with cargo fetch (verify never downloads)",base.display()))
}
fn safe_relative(path: &Path) -> bool {
    !path.as_os_str().is_empty()
        && path.to_str().is_some_and(|s| !s.contains('\\'))
        && path.components().all(|c| matches!(c, Component::Normal(_)))
}
fn read_file(path: &Path, max: u64) -> Result<Vec<u8>, String> {
    let mut file = OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_NOFOLLOW | libc::O_NONBLOCK)
        .open(path)
        .map_err(|e| format!("read {}: {e}", path.display()))?;
    let m = file.metadata().map_err(|e| e.to_string())?;
    if !m.is_file() || m.nlink() != 1 || m.len() > max {
        return Err(format!(
            "{} is not bounded single-link regular material",
            path.display()
        ));
    }
    let mut bytes = Vec::new();
    file.by_ref()
        .take(max + 1)
        .read_to_end(&mut bytes)
        .map_err(|e| e.to_string())?;
    if bytes.len() as u64 > max {
        return Err("Cargo file exceeds size limit".into());
    }
    Ok(bytes)
}
fn read_tree(root: &Path) -> Result<BTreeMap<PathBuf, Vec<u8>>, String> {
    let mut files = BTreeMap::new();
    let mut pending = vec![PathBuf::new()];
    let mut total = 0u64;
    let mut count = 0;
    while let Some(rel) = pending.pop() {
        let dir = root.join(&rel);
        let m = fs::symlink_metadata(&dir).map_err(|e| e.to_string())?;
        if !m.is_dir() || m.file_type().is_symlink() {
            return Err("Cargo tree contains symlink/non-directory".into());
        }
        for entry in fs::read_dir(dir).map_err(|e| e.to_string())? {
            let entry = entry.map_err(|e| e.to_string())?;
            count += 1;
            if count > MAX_FILES * 2 {
                return Err("Cargo tree exceeds member limit".into());
            }
            let path = rel.join(entry.file_name());
            if !safe_relative(&path) {
                return Err("unsafe Cargo tree path".into());
            }
            if matches!(entry.file_name().to_str(), Some(".git" | "target")) {
                continue;
            }
            let m = fs::symlink_metadata(entry.path()).map_err(|e| e.to_string())?;
            if m.is_dir() && !m.file_type().is_symlink() {
                pending.push(path);
            } else {
                let bytes = read_file(&entry.path(), MAX_BYTES)?;
                total += bytes.len() as u64;
                if total > MAX_BYTES || files.len() >= MAX_FILES {
                    return Err("Cargo tree exceeds material limits".into());
                }
                files.insert(path, bytes);
            }
        }
    }
    Ok(files)
}
fn archive_tree(bytes: &[u8], prefix: &str) -> Result<BTreeMap<PathBuf, Vec<u8>>, String> {
    let mut archive = tar::Archive::new(MultiGzDecoder::new(bytes).take(MAX_BYTES * 2 + 1));
    let mut files = BTreeMap::new();
    let mut members = BTreeSet::new();
    let mut dirs = BTreeSet::new();
    let mut regular = BTreeSet::new();
    let mut total = 0u64;
    for entry in archive.entries().map_err(|e| e.to_string())? {
        let mut e = entry.map_err(|e| e.to_string())?;
        let raw = e.path_bytes();
        let s = std::str::from_utf8(&raw).map_err(|_| "non-UTF8 Cargo archive path")?;
        let path = PathBuf::from(s.trim_end_matches('/'));
        if !safe_relative(&path) || !path.starts_with(prefix) {
            return Err(format!("unsafe Cargo archive path `{s}`"));
        }
        if !members.insert(path.clone()) {
            return Err(format!("duplicate Cargo archive member `{s}`"));
        }
        if members.len() > MAX_FILES * 2 {
            return Err("Cargo archive exceeds member limit".into());
        }
        for ancestor in path.ancestors().skip(1) {
            if regular.contains(ancestor) {
                return Err("Cargo archive places member beneath file".into());
            }
            dirs.insert(ancestor.to_path_buf());
        }
        if e.header().entry_type().is_dir() {
            if e.size() != 0 {
                return Err("Cargo archive directory has data".into());
            }
            continue;
        }
        if !e.header().entry_type().is_file() {
            return Err(format!(
                "Cargo archive link/special member `{s}` is forbidden"
            ));
        }
        if dirs.contains(&path) {
            return Err("Cargo archive file replaces directory".into());
        }
        regular.insert(path.clone());
        total = total
            .checked_add(e.size())
            .ok_or("Cargo archive size overflow")?;
        if total > MAX_BYTES || files.len() >= MAX_FILES {
            return Err("Cargo archive exceeds material limits".into());
        }
        let size = e.size();
        let mut data = Vec::new();
        e.read_to_end(&mut data).map_err(|e| e.to_string())?;
        if data.len() as u64 != size {
            return Err("truncated Cargo archive".into());
        }
        let relative = path
            .strip_prefix(prefix)
            .map_err(|_| "invalid Cargo archive prefix")?
            .to_path_buf();
        if !safe_relative(&relative) {
            return Err("invalid Cargo archive root file".into());
        }
        files.insert(relative, data);
    }
    let mut limited = archive.into_inner();
    io::copy(&mut limited, &mut io::sink()).map_err(|e| e.to_string())?;
    if limited.limit() == 0 {
        return Err("Cargo archive exceeds expansion limit".into());
    }
    Ok(files)
}
fn tree_hash(tree: &BTreeMap<PathBuf, Vec<u8>>) -> String {
    let mut h = Sha256::new();
    h.update(b"cott.rust.package-tree.v1\0");
    for (p, b) in tree {
        let p = p.to_string_lossy();
        h.update((p.len() as u64).to_be_bytes());
        h.update(p.as_bytes());
        h.update((b.len() as u64).to_be_bytes());
        h.update(b);
    }
    format!("sha256:{:x}", h.finalize())
}
fn digest(bytes: &[u8]) -> String {
    format!("sha256:{}", sha256_hex(bytes))
}
fn json_bytes(v: &Value) -> Result<Vec<u8>, String> {
    let mut bytes = serde_json::to_vec(v).map_err(|e| e.to_string())?;
    bytes.push(b'\n');
    Ok(bytes)
}
fn rewrite_path_manifest(
    tree: &BTreeMap<PathBuf, Vec<u8>>,
    metadata: &PackageMetadata,
) -> Result<BTreeMap<PathBuf, Vec<u8>>, String> {
    let mut tree = tree.clone();
    let mut m = parse(
        tree.get(Path::new("Cargo.toml"))
            .ok_or("path dependency requires Cargo.toml")?,
    )?;
    fn rewrite(m: &mut toml::Value, locked: &BTreeMap<String, Locked>) {
        for key in ["dependencies", "build-dependencies", "dev-dependencies"] {
            if let Some(ds) = m.get_mut(key).and_then(toml::Value::as_table_mut) {
                for (alias, d) in ds {
                    let n = dep_name(alias, d).to_owned();
                    if let Some(table) = d.as_table_mut() {
                        if table.contains_key("path")
                            && locked.get(&n).is_some_and(|p| p.path.is_some())
                        {
                            table.insert("path".into(), toml::Value::String(format!("../{n}")));
                        }
                    }
                }
            }
        }
        if let Some(ts) = m.get_mut("target").and_then(toml::Value::as_table_mut) {
            for (_, t) in ts.iter_mut() {
                rewrite(t, locked);
            }
        }
    }
    rewrite(&mut m, &metadata.locked);
    tree.insert(
        "Cargo.toml".into(),
        toml::to_string(&m).map_err(|e| e.to_string())?.into_bytes(),
    );
    Ok(tree)
}
fn generated_manifest(metadata: &PackageMetadata, deploy: bool) -> Result<Vec<u8>, String> {
    let mut m = parse(
        format!(
            "[package]\nname={:?}\nversion={:?}\nedition=\"2024\"\npublish=false\n",
            metadata.name, metadata.version
        )
        .as_bytes(),
    )?;
    // Retain solver-only declarations: features may reference build/dev dependencies.
    // They do not grant authored implementations import authority, and the generated
    // root has no authored build script or tests.
    for key in [
        "dependencies",
        "build-dependencies",
        "dev-dependencies",
        "target",
    ] {
        if let Some(value) = metadata.manifest.get(key) {
            m.as_table_mut().unwrap().insert(key.into(), value.clone());
        }
    }
    if let Some(fs) = metadata.manifest.get("features") {
        m.as_table_mut()
            .unwrap()
            .insert("features".into(), fs.clone());
    }
    fn pin(m: &mut toml::Value, locked: &BTreeMap<String, Locked>) -> Result<(), String> {
        for key in ["dependencies", "build-dependencies", "dev-dependencies"] {
            if let Some(ds) = m.get_mut(key).and_then(toml::Value::as_table_mut) {
                for (alias, d) in ds {
                    let n = dep_name(alias, d).to_owned();
                    let p = locked
                        .get(&n)
                        .ok_or_else(|| format!("missing locked dependency `{n}`"))?;
                    if d.is_str() {
                        *d = toml::Value::Table(toml::map::Map::new());
                    }
                    let table = d.as_table_mut().ok_or("invalid dependency declaration")?;
                    table.insert(
                        "version".into(),
                        toml::Value::String(format!("={}", p.version)),
                    );
                    if p.path.is_some() {
                        table.insert("path".into(), toml::Value::String(format!("deps/{n}")));
                    }
                }
            }
        }
        if let Some(ts) = m.get_mut("target").and_then(toml::Value::as_table_mut) {
            for (_, t) in ts.iter_mut() {
                pin(t, locked)?;
            }
        }
        Ok(())
    }
    pin(&mut m, &metadata.locked)?;
    let directly_named = sections(&m)
        .into_iter()
        .filter(|(kind, _)| *kind == "dependencies")
        .flat_map(|(_, ds)| ds.iter().map(|(a, d)| dep_name(a, d).to_owned()))
        .collect::<BTreeSet<_>>();
    for name in &metadata.production_packages {
        if directly_named.contains(name) {
            continue;
        }
        let package = &metadata.locked[name];
        let mut dependency = toml::map::Map::new();
        dependency.insert(
            "version".into(),
            toml::Value::String(format!("={}", package.version)),
        );
        dependency.insert("default-features".into(), toml::Value::Boolean(false));
        if package.path.is_some() {
            dependency.insert("path".into(), toml::Value::String(format!("deps/{name}")));
        }
        m.as_table_mut()
            .unwrap()
            .entry("dependencies")
            .or_insert_with(|| toml::Value::Table(toml::map::Map::new()))
            .as_table_mut()
            .unwrap()
            .insert(name.clone(), toml::Value::Table(dependency));
    }
    let deps = m
        .as_table_mut()
        .unwrap()
        .entry("dependencies")
        .or_insert_with(|| toml::Value::Table(toml::map::Map::new()))
        .as_table_mut()
        .unwrap();
    // Preserve user tokio features while adding the compiler-required runtime features.
    let mut tokio = deps
        .remove("tokio")
        .unwrap_or_else(|| toml::Value::Table(toml::map::Map::new()));
    let t = tokio.as_table_mut().ok_or("invalid tokio declaration")?;
    t.insert("version".into(), toml::Value::String("=1.53.1".into()));
    t.entry("default-features")
        .or_insert(toml::Value::Boolean(false));
    let fs = t
        .entry("features")
        .or_insert_with(|| toml::Value::Array(vec![]))
        .as_array_mut()
        .ok_or("invalid tokio features")?;
    for f in ["rt", "rt-multi-thread", "sync", "time"] {
        if !fs.iter().any(|v| v.as_str() == Some(f)) {
            fs.push(toml::Value::String(f.into()));
        }
    }
    t.remove("optional");
    deps.insert("tokio".into(), tokio);
    if !deploy {
        m.as_table_mut().unwrap().insert(
            "workspace".into(),
            toml::Value::Table(toml::map::Map::new()),
        );
    }
    toml::to_string(&m)
        .map(String::into_bytes)
        .map_err(|e| e.to_string())
}
fn lock_bytes_generated(m: &PackageMetadata) -> Result<Vec<u8>, String> {
    let mut root_deps = m.production_packages.clone();
    root_deps.insert("tokio".into());
    for (_, ds) in sections(&m.manifest) {
        for (alias, d) in ds {
            root_deps.insert(dep_name(alias, d).into());
        }
    }
    let mut packages = vec![json!({"name":m.name,"version":m.version,"dependencies":root_deps})];
    for (n, p) in &m.locked {
        let mut package = json!({"name":n,"version":p.version});
        if !p.dependencies.is_empty() {
            package["dependencies"] = json!(p.dependencies);
        }
        if let Some(c) = &p.checksum {
            package["source"] = json!(REGISTRY);
            package["checksum"] = json!(c);
        }
        packages.push(package);
    }
    let value: toml::Value = serde_json::from_value(json!({"version":4,"package":packages}))
        .map_err(|e| e.to_string())?;
    toml::to_string(&value)
        .map(String::into_bytes)
        .map_err(|e| e.to_string())
}
pub(crate) fn emitted_files(metadata: &PackageMetadata) -> BTreeMap<PathBuf, Vec<u8>> {
    metadata.frozen.artifacts.clone()
}
pub(crate) fn metadata_inputs(metadata: &PackageMetadata) -> BTreeMap<PathBuf, Vec<u8>> {
    let mut result = metadata.inputs.clone();
    for (n, p) in &metadata.locked {
        if let Some(root) = &p.path {
            for (path, bytes) in metadata.frozen.package_trees[n].iter() {
                result.insert(root.join(path), bytes.clone());
            }
        }
    }
    result
}
pub(crate) fn initial_record(metadata: &PackageMetadata) -> Value {
    metadata.frozen.record.clone()
}
pub(crate) fn runtime_package_names(metadata: &PackageMetadata) -> &BTreeSet<String> {
    &metadata.runtime_package_names
}
pub(crate) fn validate_frozen_resolution(
    metadata: &PackageMetadata,
    resolved: &ResolvedDependencies,
) -> Result<(), String> {
    if resolved.record != metadata.frozen.record
        || resolved.artifacts != metadata.frozen.artifacts
        || resolved.package_trees != metadata.frozen.package_trees
        || resolved.packages != metadata.frozen.packages
    {
        return Err("Rust frozen dependency identity/material changed".into());
    }
    Ok(())
}
pub(crate) fn resolve(
    metadata: &PackageMetadata,
    cargo_cache: Option<&Path>,
) -> Result<ResolvedDependencies, String> {
    let cache = cargo_cache
        .map(Path::to_path_buf)
        .map(Ok)
        .unwrap_or_else(default_cache)?;
    let actual = materialize(metadata, &cache)?;
    if actual.package_trees != metadata.frozen.package_trees {
        return Err("Rust dependency tree changed after metadata was frozen".into());
    }
    Ok(metadata.frozen.clone())
}
pub(crate) fn compiler_lock(
    metadata: &PackageMetadata,
    resolved: &ResolvedDependencies,
) -> Result<Vec<u8>, String> {
    validate_frozen_resolution(metadata, resolved)?;
    lock_bytes_generated(metadata)
}

#[cfg(test)]
#[path = "dependencies_tests.rs"]
mod tests;
