use std::cmp::Ordering;
use std::collections::{BTreeMap, BTreeSet};
use std::fs::{self, OpenOptions};
use std::io::{self, Read};
use std::os::unix::fs::{MetadataExt, OpenOptionsExt};
use std::path::{Component, Path, PathBuf};
use std::sync::Arc;

use flate2::read::MultiGzDecoder;
use serde::Deserialize;
use serde_json::{Value, json};
use serde_yaml_ng::{Mapping, Value as YamlValue};
use sha2::{Digest as _, Sha256};
use tar::Archive;

use crate::hash::sha256_hex;
use crate::manifest::DartProjectConfig;
use crate::project::DartPaths;

const MAX_PACKAGES: usize = 256;
const MAX_PACKAGE_FILES: usize = 20_000;
const MAX_PACKAGE_BYTES: u64 = 256 * 1024 * 1024;
const MAX_ARCHIVE_EXPANDED_BYTES: u64 = 512 * 1024 * 1024;
const MAX_METADATA_BYTES: usize = 4 * 1024 * 1024;

#[derive(Clone, Debug)]
pub(crate) struct PackageMetadata {
    pubspec_path: Option<PathBuf>,
    lockfile_path: Option<PathBuf>,
    pubspec_bytes: Option<Vec<u8>>,
    lockfile_bytes: Option<Vec<u8>>,
    managed_files: BTreeMap<PathBuf, Vec<u8>>,
    dependency_inputs: BTreeMap<PathBuf, Vec<u8>>,
    initial_record: Value,
    initial_artifact_hashes: BTreeMap<PathBuf, String>,
    project_root: PathBuf,
    direct_dependencies: BTreeSet<String>,
    runtime_package_names: BTreeSet<String>,
    locked: BTreeMap<String, LockedPackage>,
    hosted_packages: BTreeMap<String, FrozenHostedPackage>,
}

#[derive(Clone, Debug)]
struct LockedPackage {
    name: String,
    version: String,
    source: LockedSource,
    source_identity: String,
}

#[derive(Clone, Debug)]
enum LockedSource {
    Hosted {
        registry: String,
        archive_sha256: String,
    },
    Path {
        absolute: PathBuf,
    },
}

#[derive(Clone, Debug)]
struct FrozenHostedPackage {
    archive_path: PathBuf,
    archive_bytes: Arc<[u8]>,
    tree: Arc<BTreeMap<PathBuf, Vec<u8>>>,
}

#[derive(Clone, Debug)]
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

#[derive(Debug, Deserialize)]
struct RawPubspec {
    name: String,
    version: String,
    environment: BTreeMap<String, YamlValue>,
    #[serde(default)]
    dependencies: BTreeMap<String, YamlValue>,
    #[serde(default)]
    dev_dependencies: BTreeMap<String, YamlValue>,
    #[serde(default)]
    dependency_overrides: BTreeMap<String, YamlValue>,
    #[serde(default)]
    flutter: Option<YamlValue>,
}

#[derive(Debug, Deserialize)]
struct RawLock {
    packages: BTreeMap<String, RawLockedPackage>,
    #[serde(default)]
    sdks: BTreeMap<String, YamlValue>,
}

#[derive(Debug, Deserialize)]
struct RawLockedPackage {
    dependency: String,
    description: YamlValue,
    source: String,
    version: String,
}

pub(crate) fn load_metadata(
    config: &DartProjectConfig,
    paths: &DartPaths,
) -> Result<PackageMetadata, String> {
    match (&paths.pubspec, &paths.lockfile) {
        (None, None) => dependency_free_metadata(config, paths),
        (Some(pubspec), Some(lockfile)) => load_authored_metadata(config, paths, pubspec, lockfile),
        _ => Err(
            "target.dart.pubspec and target.dart.lockfile must be configured together".to_owned(),
        ),
    }
}

pub(crate) fn emitted_files(metadata: &PackageMetadata) -> BTreeMap<PathBuf, Vec<u8>> {
    metadata.managed_files.clone()
}

pub(crate) fn metadata_inputs(metadata: &PackageMetadata) -> BTreeMap<PathBuf, Vec<u8>> {
    let mut inputs = metadata.dependency_inputs.clone();
    if let (Some(path), Some(bytes)) = (&metadata.pubspec_path, &metadata.pubspec_bytes) {
        inputs.insert(path.clone(), bytes.clone());
    }
    if let (Some(path), Some(bytes)) = (&metadata.lockfile_path, &metadata.lockfile_bytes) {
        inputs.insert(path.clone(), bytes.clone());
    }
    inputs
}

pub(crate) fn initial_record(metadata: &PackageMetadata) -> Value {
    metadata.initial_record.clone()
}

/// Returns the authenticated production/transitive package closure frozen at load.
pub(crate) fn runtime_package_names(metadata: &PackageMetadata) -> &BTreeSet<String> {
    &metadata.runtime_package_names
}

pub(crate) fn validate_frozen_resolution(
    metadata: &PackageMetadata,
    resolved: &ResolvedDependencies,
) -> Result<(), String> {
    if resolved.record != metadata.initial_record {
        return Err("Dart locked dependency identity changed after metadata was frozen".to_owned());
    }
    let hashes = resolution_artifact_hashes(resolved);
    if hashes != metadata.initial_artifact_hashes {
        return Err("Dart dependency material changed after metadata was frozen".to_owned());
    }
    Ok(())
}

pub(crate) fn resolve(
    metadata: &PackageMetadata,
    pub_cache: Option<&Path>,
) -> Result<ResolvedDependencies, String> {
    resolve_internal(metadata, pub_cache, false).map(|(resolved, _)| resolved)
}

fn resolve_internal(
    metadata: &PackageMetadata,
    pub_cache: Option<&Path>,
    freeze_hosted: bool,
) -> Result<(ResolvedDependencies, BTreeMap<String, FrozenHostedPackage>), String> {
    if metadata.locked.is_empty() {
        return Ok((
            ResolvedDependencies {
                packages: Vec::new(),
                record: metadata.initial_record.clone(),
                artifacts: BTreeMap::from([(
                    PathBuf::from("dart/dependencies.json"),
                    canonical_json(&metadata.initial_record)?,
                )]),
                package_trees: BTreeMap::new(),
            },
            BTreeMap::new(),
        ));
    }

    let mut runtime = metadata.direct_dependencies.clone();
    let mut pending = runtime.iter().cloned().collect::<Vec<_>>();
    let mut candidates = BTreeMap::new();
    let mut frozen_hosted = BTreeMap::new();
    while let Some(name) = pending.pop() {
        if candidates.contains_key(&name) {
            continue;
        }
        let package = metadata.locked.get(&name).ok_or_else(|| {
            format!("runtime Dart dependency `{name}` is absent from pubspec.lock")
        })?;
        let (root, tree) = match &package.source {
            LockedSource::Path { absolute } => (
                absolute.clone(),
                Arc::new(read_package_tree(absolute, &package.name)?),
            ),
            LockedSource::Hosted { registry, .. } => {
                let required = hosted_archive_relative(registry, &package.name, &package.version)?;
                let cache = pub_cache.ok_or_else(|| {
                    format!(
                        "Dart offline dependency `{}` {} ({}) requires its locked archive at $PUB_CACHE/{}; PUB_CACHE must be an absolute canonical directory",
                        package.name,
                        package.version,
                        package.source_identity,
                        required.display()
                    )
                })?;
                let (frozen, root) = if freeze_hosted {
                    load_hosted_package(cache, package)?
                } else {
                    let frozen = metadata.hosted_packages.get(&package.name).ok_or_else(|| {
                        format!(
                            "Dart hosted package `{}` was not frozen from its authenticated archive",
                            package.name
                        )
                    })?;
                    let root = revalidate_hosted_package(cache, package, frozen)?;
                    (frozen.clone(), root)
                };
                let tree = frozen.tree.clone();
                if frozen_hosted.insert(package.name.clone(), frozen).is_some() {
                    return Err(format!(
                        "duplicate frozen Dart hosted package `{}`",
                        package.name
                    ));
                }
                (root, tree)
            }
        };
        let pubspec = tree
            .get(Path::new("pubspec.yaml"))
            .ok_or_else(|| format!("locked Dart package `{}` has no pubspec.yaml", package.name))?;
        let parsed: RawPubspec = serde_yaml_ng::from_slice(pubspec).map_err(|error| {
            format!(
                "invalid locked Dart package `{}` pubspec.yaml: {error}",
                package.name
            )
        })?;
        validate_resolved_pubspec(package, &parsed)?;
        if !parsed.dependency_overrides.is_empty() {
            return Err(format!(
                "locked Dart package `{}` uses dependency_overrides, which cannot be verified",
                package.name
            ));
        }
        if parsed.flutter.is_some() {
            return Err(format!(
                "locked Dart package `{}` requires Flutter metadata; standalone Dart verification cannot provide dart:ui",
                package.name
            ));
        }
        let mut dependencies = Vec::new();
        for (dependency, specification) in &parsed.dependencies {
            validate_dependency_name(dependency)?;
            if sdk_dependency(specification)? {
                return Err(format!(
                    "locked Dart package `{}` has SDK dependency `{dependency}`; Flutter/plugin SDK dependencies are outside the standalone Dart verifier",
                    package.name
                ));
            }
            let locked_dependency = metadata.locked.get(dependency).ok_or_else(|| {
                format!(
                    "locked Dart package `{}` depends on `{dependency}`, which is absent from pubspec.lock",
                    package.name
                )
            })?;
            validate_dependency_declaration(
                &metadata.project_root,
                &root,
                &format!("locked Dart package `{}`", package.name),
                dependency,
                specification,
                locked_dependency,
            )?;
            dependencies.push(dependency.clone());
        }
        dependencies.sort();
        dependencies.dedup();
        for dependency in &dependencies {
            if runtime.insert(dependency.clone()) {
                pending.push(dependency.clone());
            }
        }
        let content_hash = tree_hash(tree.as_ref());
        candidates.insert(
            package.name.clone(),
            (package.clone(), root, tree, dependencies, content_hash),
        );
    }

    let mut packages = Vec::new();
    let mut artifacts = BTreeMap::new();
    let mut package_trees = BTreeMap::new();
    for name in &runtime {
        let (locked, root, tree, dependencies, content_hash) = candidates
            .get(name)
            .ok_or_else(|| format!("runtime Dart dependency `{name}` is not locked"))?;
        for dependency in dependencies {
            if !runtime.contains(dependency) {
                return Err(format!(
                    "runtime Dart dependency `{name}` reaches non-runtime package `{dependency}`"
                ));
            }
        }
        let normalized_pubspec = rewrite_package_pubspec(
            tree.get(Path::new("pubspec.yaml"))
                .expect("validated package pubspec"),
            dependencies,
        )?;
        for (relative, bytes) in tree.iter() {
            if relative == Path::new("pubspec.yaml") || !deployable_package_member(relative) {
                continue;
            }
            artifacts.insert(
                PathBuf::from("dart/vendor").join(name).join(relative),
                bytes.clone(),
            );
        }
        artifacts.insert(
            PathBuf::from("dart/vendor").join(name).join("pubspec.yaml"),
            normalized_pubspec,
        );
        package_trees.insert(name.clone(), tree.clone());
        packages.push(ResolvedPackage {
            name: name.clone(),
            version: locked.version.clone(),
            source: match &locked.source {
                LockedSource::Hosted { .. } => "hosted",
                LockedSource::Path { .. } => "path",
            },
            source_identity: locked.source_identity.clone(),
            content_hash: content_hash.clone(),
            dependencies: dependencies.clone(),
            root: root.clone(),
        });
    }
    packages.sort_by(|left, right| left.name.cmp(&right.name));

    let record = dependency_record(
        metadata.pubspec_bytes.as_deref(),
        metadata.lockfile_bytes.as_deref(),
        packages.iter().map(package_record).collect(),
    );
    artifacts.insert(
        PathBuf::from("dart/dependencies.json"),
        canonical_json(&record)?,
    );
    Ok((
        ResolvedDependencies {
            packages,
            record,
            artifacts,
            package_trees,
        },
        frozen_hosted,
    ))
}

pub(crate) fn compiler_lock(
    metadata: &PackageMetadata,
    resolved: &ResolvedDependencies,
) -> Result<Vec<u8>, String> {
    let mut packages = Mapping::new();
    for package in &resolved.packages {
        let mut description = Mapping::new();
        description.insert(
            YamlValue::String("path".to_owned()),
            YamlValue::String(format!("vendor/{}", package.name)),
        );
        description.insert(
            YamlValue::String("relative".to_owned()),
            YamlValue::Bool(true),
        );
        let mut entry = Mapping::new();
        entry.insert(
            YamlValue::String("dependency".to_owned()),
            YamlValue::String(
                if metadata.direct_dependencies.contains(&package.name) {
                    "direct main"
                } else {
                    "transitive"
                }
                .to_owned(),
            ),
        );
        entry.insert(
            YamlValue::String("description".to_owned()),
            YamlValue::Mapping(description),
        );
        entry.insert(
            YamlValue::String("source".to_owned()),
            YamlValue::String("path".to_owned()),
        );
        entry.insert(
            YamlValue::String("version".to_owned()),
            YamlValue::String(package.version.clone()),
        );
        packages.insert(
            YamlValue::String(package.name.clone()),
            YamlValue::Mapping(entry),
        );
    }
    let mut sdks = Mapping::new();
    sdks.insert(
        YamlValue::String("dart".to_owned()),
        YamlValue::String(">=3.13.3 <4.0.0".to_owned()),
    );
    let mut lock = Mapping::new();
    lock.insert(
        YamlValue::String("packages".to_owned()),
        YamlValue::Mapping(packages),
    );
    lock.insert(
        YamlValue::String("sdks".to_owned()),
        YamlValue::Mapping(sdks),
    );
    serialize_yaml(&YamlValue::Mapping(lock), "compiler-owned Dart lockfile")
}

fn dependency_free_metadata(
    config: &DartProjectConfig,
    paths: &DartPaths,
) -> Result<PackageMetadata, String> {
    let pubspec = format!(
        "name: {}\nversion: {}\npublish_to: none\nenvironment:\n  sdk: '>=3.13.3 <4.0.0'\n",
        config.project.name, config.project.version
    )
    .into_bytes();
    let mut metadata = PackageMetadata {
        pubspec_path: None,
        lockfile_path: None,
        pubspec_bytes: None,
        lockfile_bytes: None,
        managed_files: BTreeMap::from([(PathBuf::from("dart/pubspec.yaml"), pubspec)]),
        dependency_inputs: BTreeMap::new(),
        initial_record: dependency_record(None, None, Vec::new()),
        initial_artifact_hashes: BTreeMap::new(),
        project_root: paths.root.clone(),
        direct_dependencies: BTreeSet::new(),
        runtime_package_names: BTreeSet::new(),
        locked: BTreeMap::new(),
        hosted_packages: BTreeMap::new(),
    };
    let resolved = resolve(&metadata, None)?;
    metadata.initial_artifact_hashes = resolution_artifact_hashes(&resolved);
    Ok(metadata)
}

fn load_authored_metadata(
    config: &DartProjectConfig,
    paths: &DartPaths,
    pubspec: &Path,
    lockfile: &Path,
) -> Result<PackageMetadata, String> {
    let pubspec_bytes = read_regular_leaf(pubspec, "target.dart.pubspec")?;
    let lockfile_bytes = read_regular_leaf(lockfile, "target.dart.lockfile")?;
    if pubspec_bytes.len() > MAX_METADATA_BYTES || lockfile_bytes.len() > MAX_METADATA_BYTES {
        return Err(format!(
            "Dart package metadata exceeds {MAX_METADATA_BYTES} bytes per file"
        ));
    }
    let raw_pubspec: RawPubspec = serde_yaml_ng::from_slice(&pubspec_bytes)
        .map_err(|error| format!("invalid Dart pubspec {}: {error}", pubspec.display()))?;
    validate_root_pubspec(config, &raw_pubspec)?;
    let raw_lock: RawLock = serde_yaml_ng::from_slice(&lockfile_bytes)
        .map_err(|error| format!("invalid Dart lockfile {}: {error}", lockfile.display()))?;
    validate_lock_sdk(&raw_lock)?;
    if raw_lock.packages.len() > MAX_PACKAGES {
        return Err(format!(
            "Dart lockfile package limit exceeded ({} > {MAX_PACKAGES})",
            raw_lock.packages.len()
        ));
    }

    let direct_dependencies = raw_pubspec
        .dependencies
        .keys()
        .cloned()
        .collect::<BTreeSet<_>>();
    let dev_dependencies = raw_pubspec
        .dev_dependencies
        .keys()
        .cloned()
        .collect::<BTreeSet<_>>();
    if let Some(duplicate) = direct_dependencies.intersection(&dev_dependencies).next() {
        return Err(format!(
            "Dart dependency `{duplicate}` is declared as both a runtime and development dependency"
        ));
    }
    let metadata_directory = pubspec
        .parent()
        .ok_or("target.dart.pubspec has no parent directory")?;
    let mut locked = BTreeMap::new();
    for (name, package) in raw_lock.packages {
        validate_dependency_name(&name)?;
        if name == config.project.name {
            return Err(format!(
                "Dart dependency `{name}` collides with the root package ownership"
            ));
        }
        validate_version(
            &package.version,
            &format!("locked package `{name}` version"),
        )?;
        let expected_ownership = if direct_dependencies.contains(&name) {
            "direct main"
        } else if dev_dependencies.contains(&name) {
            "direct dev"
        } else {
            "transitive"
        };
        if package.dependency != expected_ownership {
            return Err(format!(
                "Dart lockfile ownership for `{name}` is `{}` but root metadata requires `{expected_ownership}`",
                package.dependency
            ));
        }
        let (source, source_identity) = locked_source(
            paths,
            metadata_directory,
            &name,
            &package.source,
            &package.description,
        )?;
        if locked
            .insert(
                name.clone(),
                LockedPackage {
                    name: name.clone(),
                    version: package.version.clone(),
                    source,
                    source_identity: source_identity.clone(),
                },
            )
            .is_some()
        {
            return Err(format!("duplicate Dart lockfile package `{name}`"));
        }
    }
    for (dependency, specification) in raw_pubspec
        .dependencies
        .iter()
        .chain(&raw_pubspec.dev_dependencies)
    {
        let package = locked
            .get(dependency)
            .ok_or_else(|| format!("Dart dependency `{dependency}` is absent from pubspec.lock"))?;
        validate_dependency_declaration(
            &paths.root,
            metadata_directory,
            "root Dart package",
            dependency,
            specification,
            package,
        )?;
    }

    let relative_pubspec = project_relative(&paths.root, pubspec, "target.dart.pubspec")?;
    let relative_lockfile = project_relative(&paths.root, lockfile, "target.dart.lockfile")?;
    let managed_pubspec = rewrite_root_pubspec(&pubspec_bytes, &direct_dependencies)?;
    let mut metadata = PackageMetadata {
        pubspec_path: Some(relative_pubspec),
        lockfile_path: Some(relative_lockfile),
        pubspec_bytes: Some(pubspec_bytes),
        lockfile_bytes: Some(lockfile_bytes),
        managed_files: BTreeMap::from([(PathBuf::from("dart/pubspec.yaml"), managed_pubspec)]),
        dependency_inputs: BTreeMap::new(),
        initial_record: dependency_record(None, None, Vec::new()),
        initial_artifact_hashes: BTreeMap::new(),
        project_root: paths.root.clone(),
        direct_dependencies,
        runtime_package_names: BTreeSet::new(),
        locked,
        hosted_packages: BTreeMap::new(),
    };
    let pub_cache = configured_pub_cache()?;
    let (resolved, hosted_packages) = resolve_internal(&metadata, pub_cache.as_deref(), true)?;
    metadata.runtime_package_names = resolved
        .packages
        .iter()
        .map(|package| package.name.clone())
        .collect();
    metadata.hosted_packages = hosted_packages;
    let managed_lock = compiler_lock(&metadata, &resolved)?;
    metadata
        .managed_files
        .insert(PathBuf::from("dart/pubspec.lock"), managed_lock);
    metadata.initial_record = resolved.record.clone();
    metadata.initial_artifact_hashes = resolution_artifact_hashes(&resolved);
    metadata.dependency_inputs = project_dependency_inputs(paths, &resolved)?;
    Ok(metadata)
}

fn project_dependency_inputs(
    paths: &DartPaths,
    resolved: &ResolvedDependencies,
) -> Result<BTreeMap<PathBuf, Vec<u8>>, String> {
    let mut inputs = BTreeMap::new();
    for package in resolved
        .packages
        .iter()
        .filter(|package| package.source == "path")
    {
        let root = package.root.strip_prefix(&paths.root).map_err(|_| {
            format!(
                "resolved Dart path package `{}` escaped the project root",
                package.name
            )
        })?;
        if !safe_relative(root) {
            return Err(format!(
                "resolved Dart path package `{}` has an unsafe project identity",
                package.name
            ));
        }
        let tree = resolved.package_trees.get(&package.name).ok_or_else(|| {
            format!(
                "resolved Dart path package `{}` has no frozen input tree",
                package.name
            )
        })?;
        for (relative, bytes) in tree.iter() {
            let path = root.join(relative);
            if inputs.insert(path.clone(), bytes.clone()).is_some() {
                return Err(format!(
                    "Dart path package input ownership collides at {}",
                    path.display()
                ));
            }
        }
    }
    Ok(inputs)
}

fn validate_root_pubspec(config: &DartProjectConfig, pubspec: &RawPubspec) -> Result<(), String> {
    if pubspec.name != config.project.name {
        return Err(format!(
            "Dart pubspec package name `{}` does not match project.name `{}`",
            pubspec.name, config.project.name
        ));
    }
    if pubspec.version != config.project.version {
        return Err(format!(
            "Dart pubspec version `{}` does not match project.version `{}`",
            pubspec.version, config.project.version
        ));
    }
    validate_version(&pubspec.version, "Dart pubspec version")?;
    if !pubspec.dependency_overrides.is_empty() {
        return Err(
            "Dart pubspec dependency_overrides are not allowed in a locked target".to_owned(),
        );
    }
    if pubspec.flutter.is_some() {
        return Err(
            "Flutter package metadata is outside standalone Dart target verification".to_owned(),
        );
    }
    let sdk = pubspec
        .environment
        .get("sdk")
        .and_then(YamlValue::as_str)
        .ok_or("Dart pubspec environment.sdk must be a string")?;
    validate_sdk_constraint(sdk)?;
    for (name, specification) in pubspec.dependencies.iter().chain(&pubspec.dev_dependencies) {
        validate_dependency_name(name)?;
        if sdk_dependency(specification)? {
            return Err(format!(
                "Dart dependency `{name}` requires an SDK package; Flutter/plugin dependencies are outside standalone Dart verification"
            ));
        }
        validate_declared_source(name, specification)?;
    }
    Ok(())
}

fn validate_lock_sdk(lock: &RawLock) -> Result<(), String> {
    let sdk = lock
        .sdks
        .get("dart")
        .and_then(YamlValue::as_str)
        .ok_or("Dart lockfile omits sdks.dart")?;
    validate_sdk_constraint(sdk)
}

fn validate_sdk_constraint(value: &str) -> Result<(), String> {
    let required = parse_version("3.13.3").expect("compiler SDK version is valid");
    let excluded = parse_version("4.0.0").expect("excluded SDK version is valid");
    let valid = parse_constraint(value)
        .is_ok_and(|constraint| constraint.allows(&required) && !constraint.allows(&excluded));
    if valid {
        Ok(())
    } else {
        Err(format!(
            "Dart SDK constraint `{}` must admit 3.13.3 and exclude 4.0.0",
            value.trim()
        ))
    }
}

fn locked_source(
    paths: &DartPaths,
    metadata_directory: &Path,
    name: &str,
    source: &str,
    description: &YamlValue,
) -> Result<(LockedSource, String), String> {
    let description = description
        .as_mapping()
        .ok_or_else(|| format!("Dart lockfile package `{name}` description is not a mapping"))?;
    match source {
        "hosted" => {
            let locked_name = mapping_string(description, "name", name)?;
            if locked_name != name {
                return Err(format!(
                    "Dart lockfile package `{name}` description.name is `{locked_name}`"
                ));
            }
            if !mapping_has_only(description, &["name", "url", "sha256"]) {
                return Err(format!(
                    "Dart lockfile hosted package `{name}` has ambiguous source identity"
                ));
            }
            let registry = mapping_string(description, "url", name)?;
            let registry = canonical_registry(registry)?;
            let archive = mapping_string(description, "sha256", name)?.to_ascii_lowercase();
            validate_sha256(&archive, &format!("Dart lockfile package `{name}` archive"))?;
            Ok((
                LockedSource::Hosted {
                    registry: registry.clone(),
                    archive_sha256: archive.clone(),
                },
                format!("{registry}#sha256:{archive}"),
            ))
        }
        "path" => {
            if !mapping_has_only(description, &["path", "relative"]) {
                return Err(format!(
                    "Dart lockfile path package `{name}` has ambiguous source identity"
                ));
            }
            if !mapping_bool(description, "relative", name)? {
                return Err(format!(
                    "Dart path package `{name}` must use a relative project-local source"
                ));
            }
            let configured = mapping_string(description, "path", name)?;
            let absolute = normalize_contained_path(&paths.root, metadata_directory, configured)?;
            let project_relative = absolute
                .strip_prefix(&paths.root)
                .map_err(|_| format!("Dart path package `{name}` escaped the project root"))?
                .to_path_buf();
            let identity = slash_path(&project_relative)?;
            Ok((LockedSource::Path { absolute }, identity))
        }
        "git" => Err(format!(
            "Dart lockfile package `{name}` uses git source, which is not a closed dependency"
        )),
        other => Err(format!(
            "Dart lockfile package `{name}` uses unsupported source `{other}`"
        )),
    }
}

fn validate_resolved_pubspec(package: &LockedPackage, pubspec: &RawPubspec) -> Result<(), String> {
    if pubspec.name != package.name || pubspec.version != package.version {
        return Err(format!(
            "locked Dart package `{}` identity disagrees with its pubspec ({} {})",
            package.name, pubspec.name, pubspec.version
        ));
    }
    validate_sdk_constraint(
        pubspec
            .environment
            .get("sdk")
            .and_then(YamlValue::as_str)
            .ok_or_else(|| {
                format!(
                    "locked Dart package `{}` has no environment.sdk",
                    package.name
                )
            })?,
    )
}

fn rewrite_root_pubspec(bytes: &[u8], dependencies: &BTreeSet<String>) -> Result<Vec<u8>, String> {
    let mut document: YamlValue = serde_yaml_ng::from_slice(bytes)
        .map_err(|error| format!("parse frozen Dart pubspec for normalization: {error}"))?;
    let mapping = document
        .as_mapping_mut()
        .ok_or("Dart pubspec document is not a mapping")?;
    mapping.remove(YamlValue::String("dev_dependencies".to_owned()));
    mapping.remove(YamlValue::String("dependency_overrides".to_owned()));
    mapping.remove(YamlValue::String("flutter".to_owned()));
    mapping.insert(
        YamlValue::String("publish_to".to_owned()),
        YamlValue::String("none".to_owned()),
    );
    let mut rewritten = Mapping::new();
    for dependency in dependencies {
        rewritten.insert(
            YamlValue::String(dependency.clone()),
            YamlValue::Mapping(Mapping::from_iter([(
                YamlValue::String("path".to_owned()),
                YamlValue::String(format!("vendor/{dependency}")),
            )])),
        );
    }
    mapping.insert(
        YamlValue::String("dependencies".to_owned()),
        YamlValue::Mapping(rewritten),
    );
    serialize_yaml(&document, "normalized Dart pubspec")
}

fn rewrite_package_pubspec(bytes: &[u8], dependencies: &[String]) -> Result<Vec<u8>, String> {
    let mut document: YamlValue = serde_yaml_ng::from_slice(bytes)
        .map_err(|error| format!("parse locked Dart package pubspec: {error}"))?;
    let mapping = document
        .as_mapping_mut()
        .ok_or("locked Dart package pubspec is not a mapping")?;
    mapping.remove(YamlValue::String("dev_dependencies".to_owned()));
    mapping.remove(YamlValue::String("dependency_overrides".to_owned()));
    mapping.remove(YamlValue::String("flutter".to_owned()));
    mapping.insert(
        YamlValue::String("publish_to".to_owned()),
        YamlValue::String("none".to_owned()),
    );
    let mut rewritten = Mapping::new();
    for dependency in dependencies {
        rewritten.insert(
            YamlValue::String(dependency.clone()),
            YamlValue::Mapping(Mapping::from_iter([(
                YamlValue::String("path".to_owned()),
                YamlValue::String(format!("../{dependency}")),
            )])),
        );
    }
    mapping.insert(
        YamlValue::String("dependencies".to_owned()),
        YamlValue::Mapping(rewritten),
    );
    serialize_yaml(&document, "normalized vendored Dart pubspec")
}

fn serialize_yaml(value: &YamlValue, label: &str) -> Result<Vec<u8>, String> {
    let mut rendered =
        serde_yaml_ng::to_string(value).map_err(|error| format!("serialize {label}: {error}"))?;
    if !rendered.ends_with('\n') {
        rendered.push('\n');
    }
    Ok(rendered.into_bytes())
}

#[derive(Debug)]
enum DeclaredSource {
    Hosted { registry: String },
    Path { configured: String },
}

#[derive(Debug)]
struct DeclaredDependency {
    source: DeclaredSource,
    constraint: Option<String>,
}

fn validate_declared_source(name: &str, value: &YamlValue) -> Result<(), String> {
    let declaration = parse_declared_dependency(name, value)?;
    if let Some(constraint) = declaration.constraint {
        parse_constraint(&constraint).map_err(|error| {
            format!(
                "Dart dependency `{name}` has invalid version constraint `{constraint}`: {error}"
            )
        })?;
    }
    Ok(())
}

fn parse_declared_dependency(name: &str, value: &YamlValue) -> Result<DeclaredDependency, String> {
    match value {
        YamlValue::Null => Ok(DeclaredDependency {
            source: DeclaredSource::Hosted {
                registry: "https://pub.dev".to_owned(),
            },
            constraint: None,
        }),
        YamlValue::String(constraint) => Ok(DeclaredDependency {
            source: DeclaredSource::Hosted {
                registry: "https://pub.dev".to_owned(),
            },
            constraint: Some(constraint.clone()),
        }),
        YamlValue::Mapping(mapping)
            if mapping.contains_key(YamlValue::String("path".to_owned())) =>
        {
            if mapping.len() != 1 {
                return Err(format!(
                    "Dart path dependency `{name}` has overridden provenance"
                ));
            }
            let configured = mapping
                .get(YamlValue::String("path".to_owned()))
                .and_then(YamlValue::as_str)
                .ok_or_else(|| format!("Dart path dependency `{name}` path is not a string"))?;
            Ok(DeclaredDependency {
                source: DeclaredSource::Path {
                    configured: configured.to_owned(),
                },
                constraint: None,
            })
        }
        YamlValue::Mapping(mapping)
            if mapping.contains_key(YamlValue::String("hosted".to_owned())) =>
        {
            if !mapping_has_only(mapping, &["hosted", "version"]) {
                return Err(format!(
                    "Dart hosted dependency `{name}` has ambiguous provenance"
                ));
            }
            let hosted = mapping
                .get(YamlValue::String("hosted".to_owned()))
                .expect("hosted key presence checked");
            let registry = match hosted {
                YamlValue::String(registry) => canonical_registry(registry)?,
                YamlValue::Mapping(hosted) => {
                    if !mapping_has_only(hosted, &["name", "url"]) {
                        return Err(format!(
                            "Dart hosted dependency `{name}` has ambiguous registry identity"
                        ));
                    }
                    let declared_name = hosted
                        .get(YamlValue::String("name".to_owned()))
                        .and_then(YamlValue::as_str)
                        .ok_or_else(|| {
                            format!("Dart hosted dependency `{name}` has no string hosted.name")
                        })?;
                    if declared_name != name {
                        return Err(format!(
                            "Dart hosted dependency `{name}` substitutes registry package name `{declared_name}`"
                        ));
                    }
                    let url = hosted
                        .get(YamlValue::String("url".to_owned()))
                        .and_then(YamlValue::as_str)
                        .ok_or_else(|| {
                            format!("Dart hosted dependency `{name}` has no string hosted.url")
                        })?;
                    canonical_registry(url)?
                }
                _ => {
                    return Err(format!(
                        "Dart hosted dependency `{name}` registry is not a string or name/url mapping"
                    ));
                }
            };
            let constraint = mapping
                .get(YamlValue::String("version".to_owned()))
                .map(|value| {
                    value.as_str().map(str::to_owned).ok_or_else(|| {
                        format!("Dart hosted dependency `{name}` version is not a string")
                    })
                })
                .transpose()?;
            Ok(DeclaredDependency {
                source: DeclaredSource::Hosted { registry },
                constraint,
            })
        }
        YamlValue::Mapping(mapping)
            if mapping.contains_key(YamlValue::String("git".to_owned())) =>
        {
            Err(format!(
                "Dart dependency `{name}` uses unbounded git provenance"
            ))
        }
        _ => Err(format!(
            "Dart dependency `{name}` has an unsupported source declaration"
        )),
    }
}

fn validate_dependency_declaration(
    project_root: &Path,
    declaring_directory: &Path,
    declaring_label: &str,
    name: &str,
    specification: &YamlValue,
    locked: &LockedPackage,
) -> Result<(), String> {
    let declaration = parse_declared_dependency(name, specification)?;
    match (&declaration.source, &locked.source) {
        (
            DeclaredSource::Hosted { registry },
            LockedSource::Hosted {
                registry: selected, ..
            },
        ) if registry == selected => {}
        (
            DeclaredSource::Hosted { registry },
            LockedSource::Hosted {
                registry: selected, ..
            },
        ) => {
            return Err(format!(
                "{declaring_label} declares hosted dependency `{name}` from `{registry}`, but pubspec.lock selects `{selected}`"
            ));
        }
        (DeclaredSource::Hosted { .. }, LockedSource::Path { .. }) => {
            return Err(format!(
                "{declaring_label} declares hosted dependency `{name}`, but pubspec.lock selects a path source"
            ));
        }
        (DeclaredSource::Path { .. }, LockedSource::Hosted { .. }) => {
            return Err(format!(
                "{declaring_label} declares path dependency `{name}`, but pubspec.lock selects a hosted source"
            ));
        }
        (DeclaredSource::Path { configured }, LockedSource::Path { absolute: selected }) => {
            let declared =
                normalize_contained_path(project_root, declaring_directory, configured).map_err(
                    |error| {
                        format!(
                            "{declaring_label} has invalid project-local path for dependency `{name}`: {error}"
                        )
                    },
                )?;
            if &declared != selected {
                return Err(format!(
                    "{declaring_label} declares path dependency `{name}` at {}, but pubspec.lock selects {}",
                    declared.display(),
                    selected.display()
                ));
            }
        }
    }
    if let Some(constraint) = declaration.constraint {
        validate_dependency_constraint(name, &constraint, &locked.version)?;
    }
    Ok(())
}

fn validate_dependency_constraint(
    name: &str,
    constraint: &str,
    locked_version: &str,
) -> Result<(), String> {
    let locked = parse_version(locked_version).ok_or_else(|| {
        format!("Dart dependency `{name}` has invalid locked version `{locked_version}`")
    })?;
    let satisfied = parse_constraint(constraint)
        .map_err(|error| {
            format!(
                "Dart dependency `{name}` has invalid version constraint `{constraint}`: {error}"
            )
        })?
        .allows(&locked);
    if satisfied {
        Ok(())
    } else {
        Err(format!(
            "Dart dependency `{name}` locked version `{locked_version}` does not satisfy `{constraint}`"
        ))
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
struct Decimal(String);

impl Ord for Decimal {
    fn cmp(&self, other: &Self) -> Ordering {
        self.0
            .len()
            .cmp(&other.0.len())
            .then_with(|| self.0.cmp(&other.0))
    }
}

impl PartialOrd for Decimal {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

#[derive(Clone, Debug, Eq, Ord, PartialEq, PartialOrd)]
enum VersionIdentifier {
    Numeric(Decimal),
    Text(String),
}

#[derive(Clone, Debug, Eq, PartialEq)]
struct PubVersion {
    major: Decimal,
    minor: Decimal,
    patch: Decimal,
    prerelease: Vec<VersionIdentifier>,
    build: Vec<VersionIdentifier>,
}

impl PubVersion {
    fn is_prerelease(&self) -> bool {
        !self.prerelease.is_empty()
    }

    fn same_core(&self, other: &Self) -> bool {
        self.major == other.major && self.minor == other.minor && self.patch == other.patch
    }

    fn first_prerelease(&self) -> Self {
        Self {
            major: self.major.clone(),
            minor: self.minor.clone(),
            patch: self.patch.clone(),
            prerelease: vec![VersionIdentifier::Numeric(decimal("0"))],
            build: Vec::new(),
        }
    }

    fn next_breaking(&self) -> Self {
        if self.major.0 != "0" {
            Self {
                major: increment_decimal(&self.major),
                minor: decimal("0"),
                patch: decimal("0"),
                prerelease: Vec::new(),
                build: Vec::new(),
            }
        } else {
            Self {
                major: decimal("0"),
                minor: increment_decimal(&self.minor),
                patch: decimal("0"),
                prerelease: Vec::new(),
                build: Vec::new(),
            }
        }
    }
}

impl Ord for PubVersion {
    fn cmp(&self, other: &Self) -> Ordering {
        self.major
            .cmp(&other.major)
            .then_with(|| self.minor.cmp(&other.minor))
            .then_with(|| self.patch.cmp(&other.patch))
            .then_with(
                || match (self.prerelease.is_empty(), other.prerelease.is_empty()) {
                    (true, false) => Ordering::Greater,
                    (false, true) => Ordering::Less,
                    _ => self.prerelease.cmp(&other.prerelease),
                },
            )
            .then_with(|| self.build.cmp(&other.build))
    }
}

impl PartialOrd for PubVersion {
    fn partial_cmp(&self, other: &Self) -> Option<Ordering> {
        Some(self.cmp(other))
    }
}

#[derive(Debug)]
struct VersionConstraint {
    min: Option<PubVersion>,
    include_min: bool,
    max: Option<PubVersion>,
    include_max: bool,
    empty: bool,
}

impl VersionConstraint {
    fn allows(&self, version: &PubVersion) -> bool {
        if self.empty {
            return false;
        }
        if let Some(minimum) = &self.min
            && (version < minimum || (!self.include_min && version == minimum))
        {
            return false;
        }
        if let Some(maximum) = &self.max
            && (version > maximum || (!self.include_max && version == maximum))
        {
            return false;
        }
        true
    }
}

fn parse_constraint(value: &str) -> Result<VersionConstraint, String> {
    let mut remaining = value.trim();
    if remaining == "any" {
        return Ok(VersionConstraint {
            min: None,
            include_min: false,
            max: None,
            include_max: false,
            empty: false,
        });
    }
    if remaining.is_empty() {
        return Err("constraint is empty".to_owned());
    }
    if let Some(after_caret) = remaining.strip_prefix('^') {
        remaining = after_caret.trim_start();
        let (minimum, consumed) = parse_version_prefix(remaining)
            .ok_or_else(|| "caret operator is not followed by a version".to_owned())?;
        if !remaining[consumed..].trim().is_empty() {
            return Err("caret constraints cannot be combined with other constraints".to_owned());
        }
        let maximum = minimum.next_breaking().first_prerelease();
        return Ok(VersionConstraint {
            min: Some(minimum),
            include_min: true,
            max: Some(maximum),
            include_max: false,
            empty: false,
        });
    }

    let mut constraint = VersionConstraint {
        min: None,
        include_min: false,
        max: None,
        include_max: false,
        empty: false,
    };
    while !remaining.trim_start().is_empty() {
        remaining = remaining.trim_start();
        let (operator, rest) = if let Some(rest) = remaining.strip_prefix("<=") {
            ("<=", rest)
        } else if let Some(rest) = remaining.strip_prefix(">=") {
            (">=", rest)
        } else if let Some(rest) = remaining.strip_prefix('<') {
            ("<", rest)
        } else if let Some(rest) = remaining.strip_prefix('>') {
            (">", rest)
        } else {
            ("=", remaining)
        };
        let rest = rest.trim_start();
        let (version, consumed) = parse_version_prefix(rest)
            .ok_or_else(|| format!("`{operator}` is not followed by a version"))?;
        remaining = &rest[consumed..];
        match operator {
            ">=" => tighten_min(&mut constraint, version, true),
            ">" => tighten_min(&mut constraint, version, false),
            "<=" => tighten_max(&mut constraint, version, true),
            "<" => tighten_max(&mut constraint, version, false),
            "=" => {
                tighten_min(&mut constraint, version.clone(), true);
                tighten_max(&mut constraint, version, true);
            }
            _ => unreachable!(),
        }
    }

    if let (Some(minimum), Some(maximum)) = (&constraint.min, &constraint.max) {
        constraint.empty = minimum > maximum
            || (minimum == maximum && !(constraint.include_min && constraint.include_max));
    }
    if !constraint.empty
        && !constraint.include_max
        && let Some(maximum) = &constraint.max
        && !maximum.is_prerelease()
        && maximum.build.is_empty()
        && constraint
            .min
            .as_ref()
            .is_none_or(|minimum| !minimum.is_prerelease() || !minimum.same_core(maximum))
    {
        constraint.max = Some(maximum.first_prerelease());
    }
    Ok(constraint)
}

fn tighten_min(constraint: &mut VersionConstraint, version: PubVersion, inclusive: bool) {
    match &constraint.min {
        None => {
            constraint.min = Some(version);
            constraint.include_min = inclusive;
        }
        Some(current) if version > *current => {
            constraint.min = Some(version);
            constraint.include_min = inclusive;
        }
        Some(current) if version == *current && !inclusive => {
            constraint.include_min = false;
        }
        _ => {}
    }
}

fn tighten_max(constraint: &mut VersionConstraint, version: PubVersion, inclusive: bool) {
    match &constraint.max {
        None => {
            constraint.max = Some(version);
            constraint.include_max = inclusive;
        }
        Some(current) if version < *current => {
            constraint.max = Some(version);
            constraint.include_max = inclusive;
        }
        Some(current) if version == *current && !inclusive => {
            constraint.include_max = false;
        }
        _ => {}
    }
}

fn sdk_dependency(value: &YamlValue) -> Result<bool, String> {
    Ok(value
        .as_mapping()
        .and_then(|mapping| mapping.get(YamlValue::String("sdk".to_owned())))
        .is_some())
}

fn canonical_registry(value: &str) -> Result<String, String> {
    let rest = value
        .strip_prefix("https://")
        .ok_or_else(|| format!("hosted Dart registry `{value}` is not a canonical HTTPS URL"))?;
    let authority = rest.split('/').next().unwrap_or_default();
    if authority.is_empty()
        || authority != authority.to_ascii_lowercase()
        || !authority.bytes().all(|byte| {
            byte.is_ascii_lowercase() || byte.is_ascii_digit() || matches!(byte, b'.' | b'-' | b':')
        })
        || value.contains('#')
        || value.contains('?')
        || value.contains('@')
        || value.contains('\\')
        || value.chars().any(char::is_whitespace)
        || value.ends_with('/')
        || rest.split('/').any(|segment| matches!(segment, "." | ".."))
    {
        return Err(format!(
            "hosted Dart registry `{value}` is not a canonical HTTPS URL"
        ));
    }
    Ok(value.to_owned())
}

fn hosted_package_root(
    cache: &Path,
    registry: &str,
    name: &str,
    version: &str,
) -> Result<PathBuf, String> {
    let canonical_cache = fs::canonicalize(cache)
        .map_err(|error| format!("canonicalize PUB_CACHE {}: {error}", cache.display()))?;
    let candidate = canonical_cache
        .join("hosted")
        .join(registry_cache_key(registry)?)
        .join(format!("{name}-{version}"));
    let canonical = fs::canonicalize(&candidate).map_err(|error| {
        format!(
            "Dart offline cache is missing locked package `{name}` {version} at {}: {error}",
            candidate.display()
        )
    })?;
    if !canonical.starts_with(&canonical_cache) || canonical != candidate {
        return Err(format!(
            "Dart cached package `{name}` has non-canonical ownership"
        ));
    }
    Ok(canonical)
}
fn resolution_artifact_hashes(resolved: &ResolvedDependencies) -> BTreeMap<PathBuf, String> {
    resolved
        .artifacts
        .iter()
        .map(|(path, bytes)| (path.clone(), format!("sha256:{}", sha256_hex(bytes))))
        .collect()
}

fn registry_cache_key(registry: &str) -> Result<String, String> {
    let host = registry
        .strip_prefix("https://")
        .ok_or("hosted Dart registry is not HTTPS")?;
    Ok(if host == "pub.dev" {
        "pub.dev".to_owned()
    } else {
        host.replace('%', "%25").replace('/', "%2F")
    })
}

fn hosted_archive_relative(registry: &str, name: &str, version: &str) -> Result<PathBuf, String> {
    Ok(PathBuf::from("hosted-archives")
        .join(registry_cache_key(registry)?)
        .join(format!("{name}-{version}.tar.gz")))
}

fn hosted_archive_path(cache: &Path, package: &LockedPackage) -> Result<PathBuf, String> {
    let LockedSource::Hosted { registry, .. } = &package.source else {
        return Err(format!(
            "Dart path package `{}` has no hosted archive",
            package.name
        ));
    };
    let canonical_cache = fs::canonicalize(cache)
        .map_err(|error| format!("canonicalize PUB_CACHE {}: {error}", cache.display()))?;
    let required = canonical_cache.join(hosted_archive_relative(
        registry,
        &package.name,
        &package.version,
    )?);
    let canonical = fs::canonicalize(&required).map_err(|error| {
        format!(
            "Dart offline hosted archive for locked package `{}` {} ({}) is required at {}: {error}",
            package.name,
            package.version,
            package.source_identity,
            required.display()
        )
    })?;
    if canonical != required || !canonical.starts_with(&canonical_cache) {
        return Err(format!(
            "Dart offline hosted archive for locked package `{}` {} ({}) has non-canonical ownership at {}",
            package.name,
            package.version,
            package.source_identity,
            required.display()
        ));
    }
    Ok(required)
}

fn load_hosted_package(
    cache: &Path,
    package: &LockedPackage,
) -> Result<(FrozenHostedPackage, PathBuf), String> {
    let LockedSource::Hosted {
        registry,
        archive_sha256,
    } = &package.source
    else {
        return Err(format!("Dart package `{}` is not hosted", package.name));
    };
    let archive_path = hosted_archive_path(cache, package)?;
    let archive_bytes = read_regular_leaf(&archive_path, "Dart hosted package archive")?;
    let actual_sha256 = sha256_hex(&archive_bytes);
    if &actual_sha256 != archive_sha256 {
        return Err(format!(
            "Dart hosted archive hash mismatch for locked package `{}` {} from `{registry}` at {}: lock requires sha256:{archive_sha256}, actual compressed bytes are sha256:{actual_sha256}",
            package.name,
            package.version,
            archive_path.display()
        ));
    }
    let tree = read_hosted_archive_tree(&archive_bytes, &package.name)?;
    let root = hosted_package_root(cache, registry, &package.name, &package.version)?;
    let extracted = read_package_tree(&root, &package.name)?;
    if extracted != tree {
        return Err(format!(
            "Dart extracted hosted cache for locked package `{}` {} at {} disagrees with authenticated archive {}; restore the extracted package from the locked archive",
            package.name,
            package.version,
            root.display(),
            archive_path.display()
        ));
    }
    Ok((
        FrozenHostedPackage {
            archive_path,
            archive_bytes: Arc::from(archive_bytes),
            tree: Arc::new(tree),
        },
        root,
    ))
}

fn revalidate_hosted_package(
    cache: &Path,
    package: &LockedPackage,
    frozen: &FrozenHostedPackage,
) -> Result<PathBuf, String> {
    let LockedSource::Hosted {
        registry,
        archive_sha256,
    } = &package.source
    else {
        return Err(format!("Dart package `{}` is not hosted", package.name));
    };
    let archive_path = hosted_archive_path(cache, package)?;
    if archive_path != frozen.archive_path {
        return Err(format!(
            "PUB_CACHE changed after Dart hosted package `{}` was frozen",
            package.name
        ));
    }
    let archive_bytes = read_regular_leaf(&archive_path, "Dart hosted package archive")?;
    let actual_sha256 = sha256_hex(&archive_bytes);
    if &actual_sha256 != archive_sha256 || archive_bytes.as_slice() != frozen.archive_bytes.as_ref()
    {
        return Err(format!(
            "Dart hosted archive changed after locked package `{}` {} was frozen at {}: lock requires sha256:{archive_sha256}, actual compressed bytes are sha256:{actual_sha256}",
            package.name,
            package.version,
            archive_path.display()
        ));
    }
    let root = hosted_package_root(cache, registry, &package.name, &package.version)?;
    let extracted = read_package_tree(&root, &package.name)?;
    if &extracted != frozen.tree.as_ref() {
        return Err(format!(
            "Dart extracted hosted cache for locked package `{}` {} at {} was modified after authentication against {}; restore the extracted package from the locked archive",
            package.name,
            package.version,
            root.display(),
            archive_path.display()
        ));
    }
    Ok(root)
}

fn read_hosted_archive_tree(
    archive_bytes: &[u8],
    package: &str,
) -> Result<BTreeMap<PathBuf, Vec<u8>>, String> {
    let decoder = MultiGzDecoder::new(archive_bytes);
    let limited = decoder.take(MAX_ARCHIVE_EXPANDED_BYTES + 1);
    let mut archive = Archive::new(limited);
    let mut files = BTreeMap::new();
    let mut members = BTreeSet::new();
    let mut regular_files = BTreeSet::new();
    let mut required_directories = BTreeSet::new();
    let mut total = 0u64;
    let entries = archive
        .entries()
        .map_err(|error| format!("inspect authenticated Dart archive for `{package}`: {error}"))?;
    for entry in entries {
        let mut entry = entry.map_err(|error| {
            format!("read authenticated Dart archive entry for `{package}`: {error}")
        })?;
        if members.len() >= MAX_PACKAGE_FILES * 2 {
            return Err(format!(
                "authenticated Dart archive for `{package}` exceeds {} members",
                MAX_PACKAGE_FILES * 2
            ));
        }
        let path_bytes = entry.path_bytes();
        let path_text = std::str::from_utf8(&path_bytes).map_err(|_| {
            format!("authenticated Dart archive for `{package}` contains a non-UTF-8 path")
        })?;
        if path_text.contains('\\') {
            return Err(format!(
                "authenticated Dart archive for `{package}` contains a non-portable path `{path_text}`"
            ));
        }
        let relative = PathBuf::from(path_text);
        if !safe_relative(&relative) {
            return Err(format!(
                "authenticated Dart archive for `{package}` contains unsafe path `{path_text}`"
            ));
        }
        if !members.insert(relative.clone()) {
            return Err(format!(
                "authenticated Dart archive for `{package}` duplicates member `{}`",
                relative.display()
            ));
        }
        for ancestor in relative.ancestors().skip(1) {
            if ancestor.as_os_str().is_empty() {
                break;
            }
            if regular_files.contains(ancestor) {
                return Err(format!(
                    "authenticated Dart archive for `{package}` places `{}` beneath file `{}`",
                    relative.display(),
                    ancestor.display()
                ));
            }
            required_directories.insert(ancestor.to_path_buf());
        }

        let entry_type = entry.header().entry_type();
        if entry_type.is_dir() {
            if entry.size() != 0 {
                return Err(format!(
                    "authenticated Dart archive for `{package}` has data in directory `{}`",
                    relative.display()
                ));
            }
            continue;
        }
        if !entry_type.is_file() {
            return Err(format!(
                "authenticated Dart archive for `{package}` contains link or special member `{}`",
                relative.display()
            ));
        }
        if required_directories.contains(&relative) {
            return Err(format!(
                "authenticated Dart archive for `{package}` replaces directory `{}` with a file",
                relative.display()
            ));
        }
        regular_files.insert(relative.clone());
        let size = entry.size();
        total = total.checked_add(size).ok_or_else(|| {
            format!("authenticated Dart archive for `{package}` has overflowing file sizes")
        })?;
        if total > MAX_PACKAGE_BYTES {
            return Err(format!(
                "authenticated Dart archive for `{package}` exceeds {MAX_PACKAGE_BYTES} file bytes"
            ));
        }
        let mut bytes = Vec::with_capacity(size as usize);
        entry.read_to_end(&mut bytes).map_err(|error| {
            format!(
                "read authenticated Dart archive member `{}` for `{package}`: {error}",
                relative.display()
            )
        })?;
        if bytes.len() as u64 != size {
            return Err(format!(
                "authenticated Dart archive member `{}` for `{package}` is truncated",
                relative.display()
            ));
        }
        if !ignored_package_member(&relative) {
            if files.len() >= MAX_PACKAGE_FILES {
                return Err(format!(
                    "authenticated Dart archive for `{package}` exceeds {MAX_PACKAGE_FILES} files"
                ));
            }
            files.insert(relative, bytes);
        }
    }
    let mut limited = archive.into_inner();
    io::copy(&mut limited, &mut io::sink())
        .map_err(|error| format!("finish authenticated Dart archive for `{package}`: {error}"))?;
    if limited.limit() == 0 {
        return Err(format!(
            "authenticated Dart archive for `{package}` exceeds {MAX_ARCHIVE_EXPANDED_BYTES} expanded bytes"
        ));
    }
    Ok(files)
}
fn ignored_package_member(path: &Path) -> bool {
    path.components().any(|component| {
        let Component::Normal(name) = component else {
            return false;
        };
        matches!(name.to_str(), Some(".dart_tool" | "build" | ".git"))
    })
}
fn read_package_tree(root: &Path, package: &str) -> Result<BTreeMap<PathBuf, Vec<u8>>, String> {
    let metadata = fs::symlink_metadata(root).map_err(|error| {
        format!(
            "stat Dart package `{package}` root {}: {error}",
            root.display()
        )
    })?;
    if metadata.file_type().is_symlink() || !metadata.is_dir() {
        return Err(format!(
            "Dart package `{package}` root is not a real directory"
        ));
    }
    let mut files = BTreeMap::new();
    let mut pending = vec![(root.to_path_buf(), PathBuf::new())];
    let mut total = 0u64;
    let mut members = 0usize;
    while let Some((directory, relative_directory)) = pending.pop() {
        let mut entries = fs::read_dir(&directory)
            .map_err(|error| format!("read Dart package `{package}` directory: {error}"))?
            .collect::<Result<Vec<_>, _>>()
            .map_err(|error| format!("read Dart package `{package}` entry: {error}"))?;
        entries.sort_by_key(fs::DirEntry::file_name);
        for entry in entries {
            members = members.saturating_add(1);
            if members > MAX_PACKAGE_FILES * 2 {
                return Err(format!(
                    "Dart package material exceeds {} filesystem members",
                    MAX_PACKAGE_FILES * 2
                ));
            }
            let name = entry.file_name();
            let name = name
                .to_str()
                .ok_or_else(|| format!("Dart package `{package}` contains a non-UTF-8 path"))?;
            if matches!(name, ".dart_tool" | "build" | ".git") {
                continue;
            }
            let relative = relative_directory.join(name);
            if !safe_relative(&relative) {
                return Err(format!("Dart package `{package}` contains an unsafe path"));
            }
            let path = entry.path();
            let metadata = fs::symlink_metadata(&path)
                .map_err(|error| format!("stat Dart package `{package}` member: {error}"))?;
            if metadata.file_type().is_symlink() {
                return Err(format!(
                    "Dart package `{package}` contains symlink {}",
                    relative.display()
                ));
            }
            if metadata.is_dir() {
                pending.push((path, relative));
            } else if metadata.is_file() && metadata.nlink() == 1 {
                let bytes = read_regular_leaf(&path, "Dart package member")?;
                total = total.saturating_add(bytes.len() as u64);
                if total > MAX_PACKAGE_BYTES {
                    return Err(format!(
                        "Dart package material exceeds {MAX_PACKAGE_BYTES} bytes"
                    ));
                }
                if files.insert(relative, bytes).is_some() || files.len() > MAX_PACKAGE_FILES {
                    return Err(format!(
                        "Dart package material exceeds {MAX_PACKAGE_FILES} files"
                    ));
                }
            } else {
                return Err(format!(
                    "Dart package `{package}` member {} is not a single-link regular file",
                    relative.display()
                ));
            }
        }
    }
    Ok(files)
}

fn deployable_package_member(path: &Path) -> bool {
    path.starts_with("lib")
        || path
            .file_name()
            .and_then(|name| name.to_str())
            .is_some_and(|name| name == "LICENSE" || name.starts_with("LICENSE."))
}

fn tree_hash(files: &BTreeMap<PathBuf, Vec<u8>>) -> String {
    let mut digest = Sha256::new();
    digest.update(b"cott.dart.package-tree.v1\0");
    for (path, bytes) in files {
        let path = path.to_string_lossy();
        digest.update((path.len() as u64).to_be_bytes());
        digest.update(path.as_bytes());
        digest.update((bytes.len() as u64).to_be_bytes());
        digest.update(bytes);
    }
    format!("sha256:{:x}", digest.finalize())
}

fn dependency_record(
    pubspec: Option<&[u8]>,
    lockfile: Option<&[u8]>,
    packages: Vec<Value>,
) -> Value {
    json!({
        "schema_version": 1,
        "pubspec_hash": pubspec.map(|bytes| format!("sha256:{}", sha256_hex(bytes))),
        "lockfile_hash": lockfile.map(|bytes| format!("sha256:{}", sha256_hex(bytes))),
        "packages": packages,
    })
}

fn package_record(package: &ResolvedPackage) -> Value {
    json!({
        "name": package.name,
        "version": package.version,
        "source": package.source,
        "source_identity": package.source_identity,
        "content_hash": package.content_hash,
        "dependencies": package.dependencies,
        "runtime": true,
    })
}

fn canonical_json(value: &Value) -> Result<Vec<u8>, String> {
    let mut bytes = serde_json::to_vec(value)
        .map_err(|error| format!("serialize Dart dependency record: {error}"))?;
    bytes.push(b'\n');
    Ok(bytes)
}

fn read_regular_leaf(path: &Path, label: &str) -> Result<Vec<u8>, String> {
    let mut file = OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_NOFOLLOW | libc::O_NONBLOCK | libc::O_CLOEXEC)
        .open(path)
        .map_err(|error| format!("open {label} {}: {error}", path.display()))?;
    let metadata = file
        .metadata()
        .map_err(|error| format!("stat {label} {}: {error}", path.display()))?;
    if !metadata.is_file() || metadata.nlink() != 1 {
        return Err(format!(
            "{label} must be a single-link regular file: {}",
            path.display()
        ));
    }
    if metadata.len() > MAX_PACKAGE_BYTES {
        return Err(format!(
            "{label} exceeds the {MAX_PACKAGE_BYTES}-byte input limit: {}",
            path.display()
        ));
    }
    let mut bytes = Vec::new();
    file.read_to_end(&mut bytes)
        .map_err(|error| format!("read {label} {}: {error}", path.display()))?;
    Ok(bytes)
}

fn normalize_contained_path(root: &Path, base: &Path, value: &str) -> Result<PathBuf, String> {
    if value.is_empty()
        || value.contains('\\')
        || value.contains('\0')
        || Path::new(value).is_absolute()
    {
        return Err("Dart path dependency must be a relative UTF-8 path".to_owned());
    }
    let root = fs::canonicalize(root)
        .map_err(|error| format!("canonicalize Dart project root: {error}"))?;
    let canonical_base = fs::canonicalize(base)
        .map_err(|error| format!("canonicalize Dart metadata directory: {error}"))?;
    if canonical_base != base || !canonical_base.starts_with(&root) {
        return Err("Dart metadata directory has non-canonical ownership".to_owned());
    }
    let mut candidate = canonical_base;
    for component in Path::new(value).components() {
        match component {
            Component::CurDir => {}
            Component::ParentDir => {
                if !candidate.pop() || !candidate.starts_with(&root) {
                    return Err(format!(
                        "Dart path dependency escaped project root: {value}"
                    ));
                }
            }
            Component::Normal(segment) => {
                candidate.push(segment);
                let metadata = fs::symlink_metadata(&candidate).map_err(|error| {
                    format!(
                        "stat Dart path dependency component {}: {error}",
                        candidate.display()
                    )
                })?;
                if metadata.file_type().is_symlink() {
                    return Err(format!(
                        "Dart path dependency contains a symlink: {}",
                        candidate.display()
                    ));
                }
            }
            Component::Prefix(_) | Component::RootDir => {
                return Err("Dart path dependency must be relative".to_owned());
            }
        }
    }
    if candidate == root || !candidate.starts_with(&root) {
        return Err(format!(
            "Dart path dependency escaped project root: {value}"
        ));
    }
    Ok(candidate)
}

fn project_relative(root: &Path, path: &Path, label: &str) -> Result<PathBuf, String> {
    path.strip_prefix(root)
        .map(Path::to_path_buf)
        .map_err(|_| format!("{label} escaped the Dart project root"))
        .and_then(|path| {
            if safe_relative(&path) {
                Ok(path)
            } else {
                Err(format!("{label} is not project-relative"))
            }
        })
}

fn safe_relative(path: &Path) -> bool {
    !path.as_os_str().is_empty()
        && path.is_relative()
        && path
            .components()
            .all(|component| matches!(component, Component::Normal(_)))
}

fn slash_path(path: &Path) -> Result<String, String> {
    let mut output = String::new();
    for component in path.components() {
        let Component::Normal(segment) = component else {
            return Err("Dart dependency identity path is not normalized".to_owned());
        };
        let segment = segment
            .to_str()
            .ok_or("Dart dependency identity path is not UTF-8")?;
        if !output.is_empty() {
            output.push('/');
        }
        output.push_str(segment);
    }
    if output.is_empty() {
        Err("Dart dependency identity path is empty".to_owned())
    } else {
        Ok(output)
    }
}

fn configured_pub_cache() -> Result<Option<PathBuf>, String> {
    let Some(value) = std::env::var_os("PUB_CACHE") else {
        return Ok(None);
    };
    let path = PathBuf::from(value);
    if !path.is_absolute() {
        return Err("PUB_CACHE must be an absolute path for locked Dart dependencies".to_owned());
    }
    let canonical = fs::canonicalize(&path)
        .map_err(|error| format!("canonicalize PUB_CACHE {}: {error}", path.display()))?;
    if canonical != path || !canonical.is_dir() {
        return Err("PUB_CACHE must name a canonical real directory".to_owned());
    }
    Ok(Some(canonical))
}

fn mapping_has_only(mapping: &Mapping, allowed: &[&str]) -> bool {
    mapping.keys().all(|key| {
        key.as_str()
            .is_some_and(|key| allowed.iter().any(|allowed| key == *allowed))
    })
}

fn mapping_string<'a>(mapping: &'a Mapping, key: &str, package: &str) -> Result<&'a str, String> {
    mapping
        .get(YamlValue::String(key.to_owned()))
        .and_then(YamlValue::as_str)
        .ok_or_else(|| {
            format!("Dart lockfile package `{package}` description.{key} is not a string")
        })
}

fn mapping_bool(mapping: &Mapping, key: &str, package: &str) -> Result<bool, String> {
    mapping
        .get(YamlValue::String(key.to_owned()))
        .and_then(YamlValue::as_bool)
        .ok_or_else(|| {
            format!("Dart lockfile package `{package}` description.{key} is not a boolean")
        })
}

fn validate_sha256(value: &str, label: &str) -> Result<(), String> {
    if value.len() == 64 && value.bytes().all(|byte| byte.is_ascii_hexdigit()) {
        Ok(())
    } else {
        Err(format!("{label} is not a SHA-256 digest"))
    }
}

fn validate_dependency_name(name: &str) -> Result<(), String> {
    if name.is_empty()
        || !name
            .bytes()
            .next()
            .is_some_and(|byte| byte.is_ascii_lowercase())
        || !name
            .bytes()
            .all(|byte| byte.is_ascii_lowercase() || byte.is_ascii_digit() || byte == b'_')
    {
        Err(format!("invalid Dart package name `{name}`"))
    } else {
        Ok(())
    }
}

fn validate_version(value: &str, label: &str) -> Result<(), String> {
    parse_version(value)
        .map(|_| ())
        .ok_or_else(|| format!("{label} is not an exact semantic version"))
}

fn parse_version(value: &str) -> Option<PubVersion> {
    let (version, consumed) = parse_version_prefix(value)?;
    (consumed == value.len()).then_some(version)
}

fn parse_version_prefix(value: &str) -> Option<(PubVersion, usize)> {
    let bytes = value.as_bytes();
    let mut cursor = 0;
    let major = take_decimal(bytes, &mut cursor)?;
    take_byte(bytes, &mut cursor, b'.')?;
    let minor = take_decimal(bytes, &mut cursor)?;
    take_byte(bytes, &mut cursor, b'.')?;
    let patch = take_decimal(bytes, &mut cursor)?;
    let prerelease = if bytes.get(cursor) == Some(&b'-') {
        cursor += 1;
        take_identifiers(bytes, &mut cursor)?
    } else {
        Vec::new()
    };
    let build = if bytes.get(cursor) == Some(&b'+') {
        cursor += 1;
        take_identifiers(bytes, &mut cursor)?
    } else {
        Vec::new()
    };
    Some((
        PubVersion {
            major,
            minor,
            patch,
            prerelease,
            build,
        },
        cursor,
    ))
}

fn take_decimal(bytes: &[u8], cursor: &mut usize) -> Option<Decimal> {
    let start = *cursor;
    while bytes.get(*cursor).is_some_and(u8::is_ascii_digit) {
        *cursor += 1;
    }
    (*cursor > start).then(|| {
        decimal(
            std::str::from_utf8(&bytes[start..*cursor])
                .expect("ASCII decimal digits are valid UTF-8"),
        )
    })
}

fn take_byte(bytes: &[u8], cursor: &mut usize, expected: u8) -> Option<()> {
    if bytes.get(*cursor) == Some(&expected) {
        *cursor += 1;
        Some(())
    } else {
        None
    }
}

fn take_identifiers(bytes: &[u8], cursor: &mut usize) -> Option<Vec<VersionIdentifier>> {
    let mut identifiers = Vec::new();
    loop {
        let start = *cursor;
        while bytes
            .get(*cursor)
            .is_some_and(|byte| byte.is_ascii_alphanumeric() || *byte == b'-')
        {
            *cursor += 1;
        }
        if *cursor == start {
            return None;
        }
        let identifier = std::str::from_utf8(&bytes[start..*cursor])
            .expect("ASCII semantic-version identifier is valid UTF-8");
        identifiers.push(if identifier.bytes().all(|byte| byte.is_ascii_digit()) {
            VersionIdentifier::Numeric(decimal(identifier))
        } else {
            VersionIdentifier::Text(identifier.to_owned())
        });
        if bytes.get(*cursor) != Some(&b'.') {
            break;
        }
        *cursor += 1;
    }
    Some(identifiers)
}

fn decimal(value: &str) -> Decimal {
    let normalized = value.trim_start_matches('0');
    Decimal(if normalized.is_empty() {
        "0".to_owned()
    } else {
        normalized.to_owned()
    })
}

fn increment_decimal(value: &Decimal) -> Decimal {
    let mut digits = value.0.as_bytes().to_vec();
    for digit in digits.iter_mut().rev() {
        if *digit < b'9' {
            *digit += 1;
            return Decimal(String::from_utf8(digits).expect("decimal digits are UTF-8"));
        }
        *digit = b'0';
    }
    digits.insert(0, b'1');
    Decimal(String::from_utf8(digits).expect("decimal digits are UTF-8"))
}
