use std::collections::{BTreeMap, BTreeSet};
use std::ffi::{CString, OsStr, OsString};
use std::fs::{self, File, OpenOptions};
use std::io::{Read, Write};
use std::os::fd::{AsRawFd, FromRawFd};
use std::os::unix::ffi::OsStrExt;
use std::os::unix::fs::{MetadataExt, OpenOptionsExt};
use std::path::{Component, Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use crate::binding::{PythonFileRole, audit_facade_file};
use crate::dart::provenance::DartGenerationRecord;
use crate::kotlin::provenance::KotlinGenerationRecord;
use crate::manifest::{TargetLanguage, normalized_relative_path};
use crate::project::{ProjectPaths, discover_python_sources};
use crate::provenance::GenerationRecord;

pub(crate) fn adapter_files(
    paths: &ProjectPaths,
    record: &GenerationRecord,
) -> Result<BTreeMap<PathBuf, Vec<u8>>, String> {
    let private_roots = private_implementation_roots(paths, record)?;
    let sources = discover_python_sources(&paths.python_source_dir).map_err(|error| {
        format!(
            "cannot discover runtime adapters under {}: {error}",
            paths.python_source_dir.display()
        )
    })?;

    let mut files = BTreeMap::new();
    let mut diagnostics = Vec::new();
    for source in sources {
        if excluded_adapter(&source.path, &private_roots) {
            continue;
        }

        let display = source
            .disk_path
            .strip_prefix(&paths.root)
            .unwrap_or(&source.disk_path)
            .to_path_buf();
        diagnostics.extend(
            audit_facade_file(&display, &source.source, PythonFileRole::Authored)
                .into_iter()
                .map(|diagnostic| {
                    diagnostic.range.map_or_else(
                        || format!("{}: {}", diagnostic.path.display(), diagnostic.message),
                        |range| {
                            format!(
                                "{}:{}-{}: {}",
                                diagnostic.path.display(),
                                range.start,
                                range.end,
                                diagnostic.message
                            )
                        },
                    )
                }),
        );
        files.insert(
            Path::new("python").join(source.path),
            source.source.into_bytes(),
        );
    }

    diagnostics.sort();
    diagnostics.dedup();
    if diagnostics.is_empty() {
        Ok(files)
    } else {
        Err(format!(
            "runtime adapter facade audit failed:\n{}",
            diagnostics.join("\n")
        ))
    }
}

fn private_implementation_roots(
    paths: &ProjectPaths,
    record: &GenerationRecord,
) -> Result<BTreeSet<PathBuf>, String> {
    let configured_source = paths
        .python_source_dir
        .strip_prefix(&paths.root)
        .ok()
        .filter(|path| {
            !path.as_os_str().is_empty()
                && path
                    .components()
                    .all(|component| matches!(component, Component::Normal(_)))
        })
        .ok_or_else(|| {
            format!(
                "configured Python source is not project-relative: {}",
                paths.python_source_dir.display()
            )
        })?;
    let implementations = record
        .current
        .implementations
        .as_array()
        .ok_or("generation implementations must be an array")?;

    let mut roots = BTreeSet::from([PathBuf::from("_cott_impl"), PathBuf::from("cott_bindings")]);
    for (index, implementation) in implementations.iter().enumerate() {
        let source_origin = implementation
            .get("source_origin")
            .and_then(serde_json::Value::as_str)
            .ok_or_else(|| {
                format!("generation implementation at index {index} has no string source_origin")
            })?;
        let origin = normalized_relative_path(source_origin).map_err(|message| {
            format!("invalid implementation source path `{source_origin}`: {message}")
        })?;
        let relative = origin
            .strip_prefix(configured_source)
            .ok()
            .filter(|path| !path.as_os_str().is_empty())
            .ok_or_else(|| {
                format!(
                    "implementation source `{source_origin}` is outside configured Python source {}",
                    configured_source.display()
                )
            })?;
        if relative.extension() != Some(OsStr::new("py")) {
            return Err(format!(
                "implementation source `{source_origin}` is not a Python file"
            ));
        }

        let mut components = relative.components();
        let Some(Component::Normal(root)) = components.next() else {
            return Err(format!(
                "implementation source `{source_origin}` has no private package root"
            ));
        };
        roots.insert(PathBuf::from(root));
    }
    Ok(roots)
}

fn excluded_adapter(path: &Path, private_roots: &BTreeSet<PathBuf>) -> bool {
    if private_roots.iter().any(|root| path.starts_with(root)) {
        return true;
    }

    if path.parent().is_some_and(|parent| {
        parent.components().any(|component| {
            let Component::Normal(name) = component else {
                return true;
            };
            excluded_directory(name)
        })
    }) {
        return true;
    }

    path.file_name()
        .and_then(OsStr::to_str)
        .is_some_and(|name| {
            name.starts_with('.')
                || name == "conftest.py"
                || name.starts_with("test_")
                || name.ends_with("_test.py")
        })
}

fn excluded_directory(name: &OsStr) -> bool {
    name.to_str().is_some_and(|name| {
        name.starts_with('.')
            || matches!(
                name,
                "__pycache__" | "dev" | "development" | "test" | "tests"
            )
    })
}

pub(crate) struct ReplaceContext {
    pub root: PathBuf,
    pub source_dir: PathBuf,
    pub language_source_dir: PathBuf,
    pub artifact_root: PathBuf,
    pub extra_protected: Vec<PathBuf>,
    pub project_name: String,
    pub language: crate::manifest::TargetLanguage,
}

pub(crate) fn require_replaceable(context: &ReplaceContext, target: &Path) -> Result<(), String> {
    if output_overlaps_project(context, target) {
        return Err(
            "deployment output is not a replaceable Cott deployment: overlaps project inputs or managed artifacts"
                .to_owned(),
        );
    }
    let parent = deployment_parent(target)?;
    lock_parent(&parent)?;
    let name = target.file_name().ok_or("deployment output has no name")?;
    let tree = open_directory_at(&parent, name)?;
    require_owner(&tree.metadata().map_err(io_error)?)?;
    let bytes = read_required(&tree, Path::new("generation.json"))?;
    if generation_project_name(context.language, &bytes, &tree)? != context.project_name {
        return Err(
            "deployment output is not a replaceable Cott deployment: generation.json names a different project"
                .to_owned(),
        );
    }
    require_entry(&parent, name, &Identity::of(&tree)?)?;
    recover_replacement(&parent, name, context.language, &context.project_name)?;
    Ok(())
}

pub(crate) fn output_overlaps_project(context: &ReplaceContext, target: &Path) -> bool {
    let identity = [
        context.root.as_path(),
        context.source_dir.as_path(),
        context.language_source_dir.as_path(),
        context.artifact_root.as_path(),
    ];
    if identity.iter().any(|path| path.starts_with(target)) {
        return true;
    }
    let nested = [
        context.source_dir.as_path(),
        context.language_source_dir.as_path(),
        context.artifact_root.as_path(),
    ];
    nested.iter().any(|path| target.starts_with(path))
        || context
            .extra_protected
            .iter()
            .any(|path| target.starts_with(path) || path.starts_with(target))
}

pub(crate) fn sibling_temp(target: &Path, kind: &str) -> Result<PathBuf, String> {
    let parent = target.parent().ok_or("deployment output has no parent")?;
    let nonce = SystemTime::now()
        .duration_since(UNIX_EPOCH)
        .map_err(|error| error.to_string())?
        .as_nanos();
    Ok(parent.join(format!(
        ".cott-deploy-{kind}-{}-{nonce}",
        std::process::id()
    )))
}

pub(crate) fn remove_tree_if_present(path: &Path) -> Result<(), String> {
    match fs::symlink_metadata(path) {
        Ok(metadata) if metadata.is_dir() && !metadata.file_type().is_symlink() => {
            fs::remove_dir_all(path)
                .map_err(|error| format!("remove deployment temporary {}: {error}", path.display()))
        }
        Ok(_) => Err(format!(
            "refusing to remove non-directory deployment path {}",
            path.display()
        )),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(()),
        Err(error) => Err(format!(
            "inspect deployment temporary {}: {error}",
            path.display()
        )),
    }
}

// The deployment parent is the cross-project lock domain: two projects may
// publish to the same output. The project lock alone cannot protect that case.
pub(crate) fn publish_replace(staged: &Path, target: &Path) -> Result<(), String> {
    if staged.parent() != target.parent() || staged == target {
        return Err("replacement requires distinct sibling deployment trees".to_owned());
    }
    let parent = deployment_parent(target)?;
    lock_parent(&parent)?;
    let target_name = target.file_name().ok_or("deployment output has no name")?;
    let staged_name = staged.file_name().ok_or("deployment staging has no name")?;
    let old = open_directory_at(&parent, target_name)?;
    let new = open_directory_at(&parent, staged_name)?;
    let old_id = Identity::of(&old)?;
    let new_id = Identity::of(&new)?;
    require_owner(&old.metadata().map_err(io_error)?)?;
    require_owner(&new.metadata().map_err(io_error)?)?;
    let old_bytes = read_required(&old, Path::new("generation.json"))?;
    let new_bytes = read_required(&new, Path::new("generation.json"))?;
    let (language, name) = deployment_identity(&new_bytes, &new)?;
    if generation_project_name(language, &old_bytes, &old)? != name {
        return Err("deployment output names a different project".to_owned());
    }
    recover_replacement(&parent, target_name, language, &name)?;
    sync_deployment_tree(&new)?;
    let journal_name = journal_name(target_name);
    let exchange_name = OsString::from(format!("{}-tree", journal_name.to_string_lossy()));
    if entry_identity(&parent, &exchange_name)?.is_some() {
        return Err("unowned deployment exchange path already exists".to_owned());
    }
    let journal = ReplacementJournal {
        version: 1,
        parent: Identity::of(&parent)?,
        target: target_name.as_bytes().to_vec(),
        exchange: exchange_name.as_bytes().to_vec(),
        old: old_id,
        new: new_id,
        old_record: crate::hash::sha256_hex(&old_bytes),
        new_record: crate::hash::sha256_hex(&new_bytes),
        project_name: name,
        language: format!("{language:?}"),
    };
    create_marker(&new, &journal)?;
    // Recovery is confined to this one target-derived sibling. The caller's
    // arbitrary staging basename is never recorded as deletion authority.
    require_entry(&parent, staged_name, &journal.new)?;
    rename_at(&parent, staged_name, &exchange_name, libc::RENAME_NOREPLACE)?;
    parent.sync_all().map_err(io_error)?;
    replacement_fault("relocated")?;
    let mut journal_file = create_journal(&parent, &journal_name, &journal)?;
    replacement_fault("prepared")?;
    replacement_fault("staged")?;
    if Identity::of(&deployment_parent(target)?)? != journal.parent {
        return Err("deployment parent was substituted".to_owned());
    }
    verify_record(&parent, target_name, &journal.old_record, &journal)?;
    verify_record(&parent, &exchange_name, &journal.new_record, &journal)?;
    require_entry(&parent, target_name, &journal.old)?;
    require_entry(&parent, &exchange_name, &journal.new)?;
    // Namespace commit: a reader resolving target sees a complete old or new
    // tree, never a missing output. No error after this syscall rolls it back.
    rename_at(&parent, target_name, &exchange_name, libc::RENAME_EXCHANGE)?;
    (|| {
        replacement_fault("exchanged")?;
        // Durable commit. Recovery also infers an exchange preceding this fsync
        // or the E marker from recorded directory identities, not filenames.
        parent.sync_all().map_err(io_error)?;
        append_phase(&mut journal_file, b'E')?;
        replacement_fault("committed")?;
        finish_retirement(&parent, &journal_name, &journal, b"PE", &mut journal_file)
    })()
    .map_err(|error| {
        format!("deployment exchanged; new output retained and recovery required: {error}")
    })
}

fn generation_project_name(
    language: TargetLanguage,
    bytes: &[u8],
    tree: &File,
) -> Result<String, String> {
    match language {
        TargetLanguage::Python => {
            let record = GenerationRecord::parse(bytes)?;
            let runtime = read_required(tree, Path::new("python/cott_runtime/__init__.py"))?;
            let mut recorded =
                record.current.managed_files.iter().filter(|(path, _)| {
                    Path::new(path).ends_with("python/cott_runtime/__init__.py")
                });
            let (path, expected) = recorded
                .next()
                .ok_or("Python deployment has no recorded runtime")?;
            normalized_relative_path(path)?;
            if recorded.next().is_some()
                || *expected != format!("sha256:{}", crate::hash::sha256_hex(&runtime))
            {
                return Err(
                    "Python deployment runtime does not match its generation record".to_owned(),
                );
            }
            // This is an ownership boundary using recorded managed bytes, not a
            // claim of cryptographic author authenticity for a writable record.
            let text = std::str::from_utf8(&runtime).map_err(|error| error.to_string())?;
            let mut names = text
                .lines()
                .filter_map(|line| line.strip_prefix("PROJECT_NAME = "));
            let name = python_string(
                names
                    .next()
                    .ok_or("Python runtime has no project identity")?,
            )?;
            if names.next().is_some() || name.trim().is_empty() {
                return Err("Python runtime has ambiguous project identity".to_owned());
            }
            Ok(name)
        }
        TargetLanguage::Kotlin => Ok(KotlinGenerationRecord::parse(bytes)?.current.project_name),
        TargetLanguage::Dart => Ok(DartGenerationRecord::parse(bytes)?.current.project_name),
    }
}

fn deployment_identity(bytes: &[u8], tree: &File) -> Result<(TargetLanguage, String), String> {
    for language in [
        TargetLanguage::Python,
        TargetLanguage::Kotlin,
        TargetLanguage::Dart,
    ] {
        if let Ok(name) = generation_project_name(language, bytes, tree) {
            return Ok((language, name));
        }
    }
    Err("deployment generation record or managed project identity is invalid".to_owned())
}

fn python_string(literal: &str) -> Result<String, String> {
    let invalid = || "invalid compiler-owned Python project literal".to_owned();
    let mut chars = literal
        .strip_prefix('\'')
        .and_then(|s| s.strip_suffix('\''))
        .ok_or_else(invalid)?
        .chars();
    let mut result = String::new();
    while let Some(ch) = chars.next() {
        result.push(match ch {
            '\\' => match chars.next().ok_or_else(invalid)? {
                '\\' => '\\',
                '\'' => '\'',
                'n' => '\n',
                'r' => '\r',
                't' => '\t',
                'u' => {
                    let mut value = 0;
                    for _ in 0..4 {
                        value = value * 16
                            + chars
                                .next()
                                .and_then(|c| c.to_digit(16))
                                .ok_or_else(invalid)?;
                    }
                    char::from_u32(value).ok_or_else(invalid)?
                }
                _ => return Err(invalid()),
            },
            '\'' | '\n' | '\r' => return Err(invalid()),
            ch => ch,
        });
    }
    Ok(result)
}

#[derive(Clone, Debug, Eq, PartialEq, serde::Deserialize, serde::Serialize)]
#[serde(deny_unknown_fields)]
struct Identity {
    device: u64,
    inode: u64,
    owner: u32,
}

impl Identity {
    fn of(file: &File) -> Result<Self, String> {
        Ok(Self::metadata(&file.metadata().map_err(io_error)?))
    }

    fn metadata(metadata: &fs::Metadata) -> Self {
        Self {
            device: metadata.dev(),
            inode: metadata.ino(),
            owner: metadata.uid(),
        }
    }
}

#[derive(serde::Deserialize, serde::Serialize)]
#[serde(deny_unknown_fields)]
struct ReplacementJournal {
    version: u32,
    parent: Identity,
    target: Vec<u8>,
    exchange: Vec<u8>,
    old: Identity,
    new: Identity,
    old_record: String,
    new_record: String,
    project_name: String,
    language: String,
}

const JOURNAL_LIMIT: u64 = 16 * 1024;
const FILE_LIMIT: u64 = 64 * 1024 * 1024;
const OWNER_MARKER: &str = ".cott-deploy-owner";

fn io_error(error: std::io::Error) -> String {
    format!("deployment filesystem operation: {error}")
}

fn c_name(name: &OsStr) -> Result<CString, String> {
    if name.is_empty() || name == "." || name == ".." || name.as_bytes().contains(&b'/') {
        return Err("unsafe deployment entry name".to_owned());
    }
    CString::new(name.as_bytes()).map_err(|_| "deployment path contains NUL".to_owned())
}

fn open_at(parent: &File, name: &OsStr, flags: i32) -> Result<File, String> {
    let name = c_name(name)?;
    let fd = unsafe {
        libc::openat(
            parent.as_raw_fd(),
            name.as_ptr(),
            flags | libc::O_CLOEXEC | libc::O_NOFOLLOW | libc::O_NONBLOCK,
            0o600,
        )
    };
    if fd < 0 {
        Err(io_error(std::io::Error::last_os_error()))
    } else {
        Ok(unsafe { File::from_raw_fd(fd) })
    }
}

fn open_directory_at(parent: &File, name: &OsStr) -> Result<File, String> {
    open_at(parent, name, libc::O_RDONLY | libc::O_DIRECTORY)
}

fn deployment_parent(target: &Path) -> Result<File, String> {
    if !target.is_absolute() || target.file_name().is_none() {
        return Err("deployment requires a normalized absolute output path".to_owned());
    }
    let mut directory = OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_DIRECTORY | libc::O_NOFOLLOW | libc::O_CLOEXEC)
        .open("/")
        .map_err(io_error)?;
    for component in target
        .parent()
        .ok_or("deployment output has no parent")?
        .components()
    {
        match component {
            Component::RootDir => {}
            Component::Normal(name) => directory = open_directory_at(&directory, name)?,
            _ => return Err("deployment output has an unsafe ancestor".to_owned()),
        }
    }
    Ok(directory)
}

fn lock_parent(parent: &File) -> Result<(), String> {
    loop {
        if unsafe { libc::flock(parent.as_raw_fd(), libc::LOCK_EX) } == 0 {
            return Ok(());
        }
        let error = std::io::Error::last_os_error();
        if error.kind() != std::io::ErrorKind::Interrupted {
            return Err(io_error(error));
        }
    }
}

fn require_owner(metadata: &fs::Metadata) -> Result<(), String> {
    if metadata.uid() != unsafe { libc::geteuid() } {
        return Err("deployment artifact is not owned by the current user".to_owned());
    }
    Ok(())
}

fn descriptor_path(directory: &File) -> PathBuf {
    PathBuf::from(format!("/proc/self/fd/{}", directory.as_raw_fd()))
}

fn entry_identity(parent: &File, name: &OsStr) -> Result<Option<Identity>, String> {
    c_name(name)?;
    match fs::symlink_metadata(descriptor_path(parent).join(name)) {
        Ok(metadata) if metadata.is_dir() && !metadata.file_type().is_symlink() => {
            Ok(Some(Identity::metadata(&metadata)))
        }
        Ok(_) => Err("deployment tree entry is not a no-follow directory".to_owned()),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => Ok(None),
        Err(error) => Err(io_error(error)),
    }
}

fn require_entry(parent: &File, name: &OsStr, identity: &Identity) -> Result<(), String> {
    if entry_identity(parent, name)?.as_ref() != Some(identity) {
        return Err("deployment tree identity changed".to_owned());
    }
    Ok(())
}

fn read_required(tree: &File, path: &Path) -> Result<Vec<u8>, String> {
    let mut directory = tree.try_clone().map_err(io_error)?;
    let mut parts = path.components().peekable();
    while let Some(component) = parts.next() {
        let Component::Normal(name) = component else {
            return Err("unsafe deployment record member".to_owned());
        };
        if parts.peek().is_some() {
            directory = open_directory_at(&directory, name)?;
        } else {
            let mut file = open_at(&directory, name, libc::O_RDONLY)?;
            let bytes = read_single_link(&mut file, FILE_LIMIT)?;
            require_file_entry(&directory, name, &file)?;
            return Ok(bytes);
        }
    }
    Err("empty deployment record member".to_owned())
}

fn read_single_link(file: &mut File, limit: u64) -> Result<Vec<u8>, String> {
    let before = file.metadata().map_err(io_error)?;
    require_owner(&before)?;
    if !before.is_file() || before.nlink() != 1 || before.len() > limit {
        return Err("deployment record is not a bounded regular single-link file".to_owned());
    }
    let mut bytes = Vec::new();
    (&mut *file)
        .take(limit + 1)
        .read_to_end(&mut bytes)
        .map_err(io_error)?;
    let after = file.metadata().map_err(io_error)?;
    if bytes.len() as u64 > limit
        || after.nlink() != 1
        || before.len() != after.len()
        || before.mtime() != after.mtime()
        || before.mtime_nsec() != after.mtime_nsec()
        || before.ctime() != after.ctime()
        || before.ctime_nsec() != after.ctime_nsec()
    {
        return Err("deployment record changed while being read".to_owned());
    }
    Ok(bytes)
}

fn rename_at(parent: &File, source: &OsStr, target: &OsStr, flags: u32) -> Result<(), String> {
    let source = c_name(source)?;
    let target = c_name(target)?;
    if unsafe {
        libc::renameat2(
            parent.as_raw_fd(),
            source.as_ptr(),
            parent.as_raw_fd(),
            target.as_ptr(),
            flags,
        )
    } != 0
    {
        return Err(io_error(std::io::Error::last_os_error()));
    }
    Ok(())
}

fn unlink_at(parent: &File, name: &OsStr, directory: bool) -> Result<(), String> {
    let name = c_name(name)?;
    if unsafe {
        libc::unlinkat(
            parent.as_raw_fd(),
            name.as_ptr(),
            if directory { libc::AT_REMOVEDIR } else { 0 },
        )
    } != 0
    {
        return Err(io_error(std::io::Error::last_os_error()));
    }
    Ok(())
}

fn journal_name(target: &OsStr) -> OsString {
    OsString::from(format!(
        ".cott-deploy-journal-{}",
        crate::hash::sha256_hex(target.as_bytes())
    ))
}

fn create_journal(
    parent: &File,
    name: &OsStr,
    journal: &ReplacementJournal,
) -> Result<File, String> {
    let mut bytes = serde_json::to_vec(journal).map_err(|error| error.to_string())?;
    bytes.extend_from_slice(b"\nP");
    if bytes.len() as u64 > JOURNAL_LIMIT - 2 {
        return Err("deployment journal is too large".to_owned());
    }
    create_owned_file(parent, name, &bytes)
}

fn create_owned_file(parent: &File, name: &OsStr, bytes: &[u8]) -> Result<File, String> {
    // An unnamed inode prevents a crash during journal construction from
    // exposing a partial journal or requiring unsafe prefix-based scavenging.
    let fd = unsafe {
        libc::openat(
            parent.as_raw_fd(),
            c".".as_ptr(),
            libc::O_TMPFILE | libc::O_RDWR | libc::O_CLOEXEC,
            0o600,
        )
    };
    if fd < 0 {
        return Err(io_error(std::io::Error::last_os_error()));
    }
    let mut file = unsafe { File::from_raw_fd(fd) };
    file.write_all(bytes)
        .and_then(|()| file.sync_all())
        .map_err(io_error)?;
    let source =
        CString::new(format!("/proc/self/fd/{}", file.as_raw_fd())).map_err(|e| e.to_string())?;
    let name = c_name(name)?;
    if unsafe {
        libc::linkat(
            libc::AT_FDCWD,
            source.as_ptr(),
            parent.as_raw_fd(),
            name.as_ptr(),
            libc::AT_SYMLINK_FOLLOW,
        )
    } != 0
    {
        return Err(io_error(std::io::Error::last_os_error()));
    }
    parent.sync_all().map_err(io_error)?;
    Ok(file)
}

fn append_phase(file: &mut File, phase: u8) -> Result<(), String> {
    let metadata = file.metadata().map_err(io_error)?;
    require_owner(&metadata)?;
    if !metadata.is_file() || metadata.nlink() != 1 || metadata.len() >= JOURNAL_LIMIT {
        return Err("unsafe deployment journal".to_owned());
    }
    file.write_all(&[phase])
        .and_then(|()| file.sync_all())
        .map_err(io_error)
}

fn recover_replacement(
    parent: &File,
    target: &OsStr,
    language: TargetLanguage,
    project_name: &str,
) -> Result<(), String> {
    let name = journal_name(target);
    let path = descriptor_path(parent).join(&name);
    match fs::symlink_metadata(path) {
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            let exchange = OsString::from(format!("{}-tree", name.to_string_lossy()));
            if entry_identity(parent, &exchange)?.is_none() {
                return Ok(());
            }
            // Relocation may be durable before external journal publication.
            // The exact reserved sibling must carry the independently written
            // ownership marker and still contain the complete recorded tree.
            let tree = open_directory_at(parent, &exchange)?;
            let bytes = marker_bytes(&tree)?;
            let journal: ReplacementJournal =
                serde_json::from_slice(&bytes).map_err(|e| e.to_string())?;
            validate_journal(parent, target, language, project_name, &journal)?;
            require_entry(parent, target, &journal.old)?;
            require_entry(parent, &exchange, &journal.new)?;
            verify_record(parent, target, &journal.old_record, &journal)?;
            verify_record(parent, &exchange, &journal.new_record, &journal)?;
            require_marker(&tree, &journal)?;
            create_journal(parent, &name, &journal)?;
        }
        Err(error) => return Err(io_error(error)),
        Ok(_) => {}
    }
    let mut file = open_at(parent, &name, libc::O_RDWR | libc::O_APPEND)?;
    let metadata = file.metadata().map_err(io_error)?;
    if metadata.mode() & 0o077 != 0 {
        return Err("unsafe deployment journal permissions".to_owned());
    }
    let bytes = read_single_link(&mut file, JOURNAL_LIMIT)?;
    require_file_entry(parent, &name, &file)?;
    let split = bytes
        .iter()
        .position(|b| *b == b'\n')
        .ok_or("incomplete deployment journal")?;
    let journal: ReplacementJournal =
        serde_json::from_slice(&bytes[..split]).map_err(|e| e.to_string())?;
    let phase = &bytes[split + 1..];
    if !matches!(phase, b"P" | b"PA" | b"PE" | b"PEC") {
        return Err("deployment recovery phase is invalid".to_owned());
    }
    validate_journal(parent, target, language, project_name, &journal)?;
    let exchange = OsStr::from_bytes(&journal.exchange);
    match entry_identity(parent, target)? {
        Some(identity) if identity == journal.old && matches!(phase, b"P" | b"PA") => {
            verify_record(parent, target, &journal.old_record, &journal)?;
            if phase == b"P" {
                require_entry(parent, exchange, &journal.new)?;
                let tree = open_directory_at(parent, exchange)?;
                require_marker(&tree, &journal)?;
                verify_record(parent, exchange, &journal.new_record, &journal)?;
                // Persist abort cleanup only after complete stage ownership
                // validation. The marker survives partial member retirement.
                append_phase(&mut file, b'A')?;
            }
            if let Some(identity) = entry_identity(parent, exchange)? {
                if identity != journal.new {
                    return Err("prepared deployment tree was substituted".to_owned());
                }
                remove_owned_tree(parent, exchange, &journal.new, Some(&journal))?;
            }
            parent.sync_all().map_err(io_error)?;
            remove_cleanup_marker(parent, &journal)?;
            require_file_entry(parent, &name, &file)?;
            unlink_at(parent, &name, false)?;
            parent.sync_all().map_err(io_error)
        }
        Some(identity) if identity == journal.new && phase != b"PA" => {
            verify_record(parent, target, &journal.new_record, &journal)?;
            parent.sync_all().map_err(io_error)?;
            if phase == b"P" {
                append_phase(&mut file, b'E')?;
            }
            finish_retirement(
                parent,
                &name,
                &journal,
                if phase == b"P" { b"PE" } else { phase },
                &mut file,
            )
        }
        _ => Err("deployment recovery target was substituted; retained all artifacts".to_owned()),
    }
}

fn validate_journal(
    parent: &File,
    target: &OsStr,
    language: TargetLanguage,
    project_name: &str,
    journal: &ReplacementJournal,
) -> Result<(), String> {
    let exchange = OsStr::from_bytes(&journal.exchange);
    c_name(exchange)?;
    if journal.version != 1
        || journal.parent != Identity::of(parent)?
        || journal.target != target.as_bytes()
        || journal.project_name != project_name
        || journal.language != format!("{language:?}")
        || journal.old.owner != unsafe { libc::geteuid() }
        || journal.new.owner != unsafe { libc::geteuid() }
        || journal.old.device != journal.parent.device
        || journal.new.device != journal.parent.device
        || journal.old == journal.new
        || exchange == target
        || exchange != OsStr::new(&format!("{}-tree", journal_name(target).to_string_lossy()))
    {
        return Err("deployment recovery journal identity or ownership is invalid".to_owned());
    }
    Ok(())
}

fn verify_record(
    parent: &File,
    name: &OsStr,
    expected: &str,
    journal: &ReplacementJournal,
) -> Result<(), String> {
    let tree = open_directory_at(parent, name)?;
    let bytes = read_required(&tree, Path::new("generation.json"))?;
    if crate::hash::sha256_hex(&bytes) != expected {
        return Err("deployment recovery generation record changed".to_owned());
    }
    let (language, name) = deployment_identity(&bytes, &tree)?;
    if name != journal.project_name || format!("{language:?}") != journal.language {
        return Err("deployment recovery record names a different project or target".to_owned());
    }
    Ok(())
}

fn marker_bytes(tree: &File) -> Result<Vec<u8>, String> {
    ownership_bytes(tree, OsStr::new(OWNER_MARKER))
}

fn ownership_bytes(tree: &File, name: &OsStr) -> Result<Vec<u8>, String> {
    let mut file = open_at(tree, name, libc::O_RDONLY)?;
    let metadata = file.metadata().map_err(io_error)?;
    if metadata.mode() & 0o077 != 0 {
        return Err("unsafe deployment ownership marker permissions".to_owned());
    }
    let bytes = read_single_link(&mut file, JOURNAL_LIMIT)?;
    require_file_entry(tree, name, &file)?;
    Ok(bytes)
}

fn create_marker(tree: &File, journal: &ReplacementJournal) -> Result<(), String> {
    let bytes = serde_json::to_vec(journal).map_err(|error| error.to_string())?;
    if bytes.len() as u64 > JOURNAL_LIMIT - 4 {
        return Err("deployment ownership marker is too large".to_owned());
    }
    create_owned_file(tree, OsStr::new(OWNER_MARKER), &bytes)?;
    Ok(())
}

fn require_marker(tree: &File, journal: &ReplacementJournal) -> Result<(), String> {
    let expected = serde_json::to_vec(journal).map_err(|error| error.to_string())?;
    if marker_bytes(tree)? != expected {
        return Err("deployment ownership marker does not match the transaction".to_owned());
    }
    Ok(())
}

fn cleanup_marker_name(journal: &ReplacementJournal) -> OsString {
    OsString::from(format!(
        "{}-owner",
        journal_name(OsStr::from_bytes(&journal.target)).to_string_lossy()
    ))
}

fn require_cleanup_marker(parent: &File, journal: &ReplacementJournal) -> Result<(), String> {
    let expected = serde_json::to_vec(journal).map_err(|error| error.to_string())?;
    if ownership_bytes(parent, &cleanup_marker_name(journal))? != expected {
        return Err(
            "deployment cleanup ownership marker does not match the transaction".to_owned(),
        );
    }
    Ok(())
}

fn remove_cleanup_marker(parent: &File, journal: &ReplacementJournal) -> Result<(), String> {
    let name = cleanup_marker_name(journal);
    match fs::symlink_metadata(descriptor_path(parent).join(&name)) {
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => return Ok(()),
        Err(error) => return Err(io_error(error)),
        Ok(_) => {}
    }
    require_cleanup_marker(parent, journal)?;
    unlink_at(parent, &name, false)?;
    parent.sync_all().map_err(io_error)
}

fn relocate_cleanup_marker(
    tree: &File,
    parent: &File,
    journal: &ReplacementJournal,
) -> Result<(), String> {
    require_marker(tree, journal)?;
    let source = c_name(OsStr::new(OWNER_MARKER))?;
    let destination = c_name(&cleanup_marker_name(journal))?;
    if unsafe {
        libc::renameat2(
            tree.as_raw_fd(),
            source.as_ptr(),
            parent.as_raw_fd(),
            destination.as_ptr(),
            libc::RENAME_NOREPLACE,
        )
    } != 0
    {
        return Err(io_error(std::io::Error::last_os_error()));
    }
    // Retain independent ownership proof outside the now-empty root until its
    // removal is durable. A forged cleanup phase never authorizes even an
    // unrelated empty directory solely from an inode named in a journal.
    tree.sync_all().map_err(io_error)?;
    parent.sync_all().map_err(io_error)
}

fn finish_retirement(
    parent: &File,
    name: &OsStr,
    journal: &ReplacementJournal,
    phase: &[u8],
    file: &mut File,
) -> Result<(), String> {
    let exchange = OsStr::from_bytes(&journal.exchange);
    if phase != b"PEC" {
        let target = OsStr::from_bytes(&journal.target);
        require_entry(parent, target, &journal.new)?;
        require_marker(&open_directory_at(parent, target)?, journal)?;
        require_entry(parent, exchange, &journal.old)?;
        verify_record(parent, exchange, &journal.old_record, journal)?;
        let tree = open_directory_at(parent, exchange)?;
        match fs::symlink_metadata(descriptor_path(&tree).join(OWNER_MARKER)) {
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
                create_marker(&tree, journal)?
            }
            Err(error) => return Err(io_error(error)),
            Ok(_) => require_marker(&tree, journal)?,
        }
        append_phase(file, b'C')?;
    }
    replacement_fault("retiring")?;
    if let Some(identity) = entry_identity(parent, exchange)? {
        if identity != journal.old {
            return Err("retired deployment tree was substituted".to_owned());
        }
        remove_owned_tree(parent, exchange, &journal.old, Some(journal))?;
    }
    parent.sync_all().map_err(io_error)?;
    remove_cleanup_marker(parent, journal)?;
    replacement_fault("retired")?;
    let target = OsStr::from_bytes(&journal.target);
    require_entry(parent, target, &journal.new)?;
    let tree = open_directory_at(parent, target)?;
    match fs::symlink_metadata(descriptor_path(&tree).join(OWNER_MARKER)) {
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {}
        Err(error) => return Err(io_error(error)),
        Ok(_) => {
            require_marker(&tree, journal)?;
            unlink_at(&tree, OsStr::new(OWNER_MARKER), false)?;
            tree.sync_all().map_err(io_error)?;
        }
    }
    require_file_entry(parent, name, file)?;
    unlink_at(parent, name, false)?;
    parent.sync_all().map_err(io_error)
}

fn require_file_entry(parent: &File, name: &OsStr, file: &File) -> Result<(), String> {
    let leaf = fs::symlink_metadata(descriptor_path(parent).join(name)).map_err(io_error)?;
    if !leaf.is_file() || leaf.nlink() != 1 || Identity::metadata(&leaf) != Identity::of(file)? {
        return Err("deployment file identity changed".to_owned());
    }
    Ok(())
}

fn tree_entries(tree: &File) -> Result<Vec<OsString>, String> {
    let mut entries = fs::read_dir(descriptor_path(tree))
        .map_err(io_error)?
        .map(|entry| entry.map(|entry| entry.file_name()).map_err(io_error))
        .collect::<Result<Vec<_>, _>>()?;
    entries.sort();
    Ok(entries)
}

fn sync_deployment_tree(tree: &File) -> Result<(), String> {
    let device = tree.metadata().map_err(io_error)?.dev();
    for name in tree_entries(tree)? {
        let file = open_at(tree, &name, libc::O_RDONLY)?;
        let metadata = file.metadata().map_err(io_error)?;
        require_owner(&metadata)?;
        if metadata.dev() != device {
            return Err("deployment tree crosses a filesystem boundary".to_owned());
        }
        if metadata.is_dir() {
            sync_deployment_tree(&file)?;
        } else if metadata.is_file() && metadata.nlink() == 1 {
            file.sync_all().map_err(io_error)?;
        } else {
            return Err("deployment contains a non-regular or multiply-linked member".to_owned());
        }
    }
    tree.sync_all().map_err(io_error)
}

fn remove_owned_tree(
    parent: &File,
    name: &OsStr,
    identity: &Identity,
    marker: Option<&ReplacementJournal>,
) -> Result<(), String> {
    require_entry(parent, name, identity)?;
    let tree = open_directory_at(parent, name)?;
    if Identity::of(&tree)? != *identity {
        return Err("retired deployment identity changed".to_owned());
    }
    if let Some(journal) = marker {
        match fs::symlink_metadata(descriptor_path(&tree).join(OWNER_MARKER)) {
            Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
                require_cleanup_marker(parent, journal)?;
                if !tree_entries(&tree)?.is_empty() {
                    return Err(
                        "deployment cleanup marker was moved before the tree became empty"
                            .to_owned(),
                    );
                }
            }
            Err(error) => return Err(io_error(error)),
            Ok(_) => require_marker(&tree, journal)?,
        }
    }
    for child in tree_entries(&tree)? {
        if marker.is_some() && child == OsStr::new(OWNER_MARKER) {
            continue;
        }
        let file = open_at(&tree, &child, libc::O_RDONLY)?;
        let metadata = file.metadata().map_err(io_error)?;
        require_owner(&metadata)?;
        if metadata.dev() != identity.device {
            return Err("retired deployment crosses a filesystem boundary".to_owned());
        }
        if metadata.is_dir() {
            remove_owned_tree(&tree, &child, &Identity::metadata(&metadata), None)?;
        } else if metadata.is_file() && metadata.nlink() == 1 {
            let leaf =
                fs::symlink_metadata(descriptor_path(&tree).join(&child)).map_err(io_error)?;
            if Identity::metadata(&leaf) != Identity::metadata(&metadata) {
                return Err("retired deployment member changed".to_owned());
            }
            unlink_at(&tree, &child, false)?;
            replacement_fault("retirement_member")?;
        } else {
            return Err("retired deployment contains an unsafe member".to_owned());
        }
    }
    if let Some(journal) = marker {
        if !tree_entries(&tree)?.is_empty() {
            relocate_cleanup_marker(&tree, parent, journal)?;
            replacement_fault("cleanup_marker")?;
        }
    }
    tree.sync_all().map_err(io_error)?;
    require_entry(parent, name, identity)?;
    unlink_at(parent, name, true)
}

#[cfg(not(test))]
fn replacement_fault(_: &str) -> Result<(), String> {
    Ok(())
}

#[cfg(test)]
thread_local! {
    static REPLACEMENT_FAULT: std::cell::RefCell<Option<&'static str>> = const { std::cell::RefCell::new(None) };
}

#[cfg(test)]
fn replacement_fault(point: &str) -> Result<(), String> {
    if std::env::var("COTT_DEPLOY_TEST_CRASH").ok().as_deref() == Some(point) {
        std::process::exit(86);
    }
    REPLACEMENT_FAULT.with(|fault| {
        if *fault.borrow() == Some(point) {
            *fault.borrow_mut() = None;
            Err(format!("injected deployment failure: {point}"))
        } else {
            Ok(())
        }
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    use crate::provenance::{GenerationCompatibility, GenerationSnapshot, SemanticCoverage};
    use std::sync::atomic::{AtomicBool, AtomicU64, Ordering};

    static NEXT: AtomicU64 = AtomicU64::new(0);

    struct Fixture {
        root: PathBuf,
        target: PathBuf,
        staged: PathBuf,
    }

    impl Fixture {
        fn new() -> Self {
            let root = std::env::temp_dir().join(format!(
                "cott-replacement-{}-{}",
                std::process::id(),
                NEXT.fetch_add(1, Ordering::Relaxed)
            ));
            fs::create_dir(&root).expect("test directory");
            let target = root.join("release");
            let staged = root.join("staged");
            deployment(&target, "demo", b"old");
            deployment(&staged, "demo", b"new");
            Self {
                root,
                target,
                staged,
            }
        }

        fn recover(&self) -> Result<(), String> {
            let parent = deployment_parent(&self.target)?;
            lock_parent(&parent)?;
            recover_replacement(
                &parent,
                self.target.file_name().unwrap(),
                TargetLanguage::Python,
                "demo",
            )
        }

        fn exchange(&self) -> PathBuf {
            self.root.join(format!(
                "{}-tree",
                journal_name(self.target.file_name().unwrap()).to_string_lossy()
            ))
        }

        fn assert_complete(&self, expected: &[u8]) {
            assert_eq!(
                fs::read(self.target.join("payload")).expect("complete deployment"),
                expected
            );
            let tree = File::open(&self.target).expect("deployment tree");
            let bytes = read_required(&tree, Path::new("generation.json")).expect("record");
            assert_eq!(
                deployment_identity(&bytes, &tree)
                    .expect("recorded runtime")
                    .1,
                "demo"
            );
            assert_eq!(
                fs::read(self.target.join("nested/second")).expect("second member"),
                expected
            );
        }
    }

    impl Drop for Fixture {
        fn drop(&mut self) {
            REPLACEMENT_FAULT.with(|fault| *fault.borrow_mut() = None);
            let _ = fs::remove_dir_all(&self.root);
        }
    }

    fn deployment(path: &Path, project: &str, payload: &[u8]) {
        fs::create_dir_all(path.join("python/cott_runtime")).expect("runtime directory");
        fs::create_dir(path.join("nested")).expect("nested directory");
        fs::write(path.join("payload"), payload).expect("payload");
        fs::write(path.join("nested/second"), payload).expect("second member");
        let runtime = crate::python_runtime::render_runtime(project, "0.1.0")
            .remove(Path::new("cott_runtime/__init__.py"))
            .expect("runtime");
        fs::write(path.join("python/cott_runtime/__init__.py"), &runtime).expect("runtime bytes");
        let mut current = GenerationSnapshot {
            generation_id: String::new(),
            verified: false,
            project_version: "0.1.0".to_owned(),
            compatibility: GenerationCompatibility::current(),
            inputs: serde_json::json!({}),
            tools: serde_json::json!({}),
            ir: serde_json::json!({}),
            contract_surface: serde_json::json!({}),
            public_python_symbols: serde_json::json!({}),
            implementations: serde_json::json!([]),
            dependencies: serde_json::json!([]),
            managed_files: BTreeMap::from([(
                "generated/python/cott_runtime/__init__.py".to_owned(),
                format!("sha256:{}", crate::hash::sha256_hex(&runtime)),
            )]),
            unresolved: Vec::new(),
            verification: serde_json::Value::Null,
            semantic_coverage: SemanticCoverage::default(),
            agent_runs: Vec::new(),
        };
        current
            .compute_generation_id()
            .expect("generation identity");
        let record = GenerationRecord {
            schema_version: crate::provenance::GENERATION_SCHEMA_VERSION,
            current,
            last_verified: None,
        };
        fs::write(
            path.join("generation.json"),
            record.canonical_bytes().expect("record"),
        )
        .expect("generation file");
    }

    #[test]
    fn failure_before_exchange_preserves_old_and_after_exchange_preserves_complete_new() {
        for (fault, expected) in [
            ("relocated", b"old"),
            ("prepared", b"old"),
            ("staged", b"old"),
            ("exchanged", b"new"),
            ("committed", b"new"),
            ("retiring", b"new"),
            ("retirement_member", b"new"),
            ("cleanup_marker", b"new"),
            ("retired", b"new"),
        ] {
            let fixture = Fixture::new();
            REPLACEMENT_FAULT.with(|slot| *slot.borrow_mut() = Some(fault));
            assert!(
                publish_replace(&fixture.staged, &fixture.target).is_err(),
                "{fault}"
            );
            fixture.assert_complete(expected);
            fixture.recover().expect("recover interrupted replacement");
            fixture.recover().expect("idempotent recovery");
            fixture.assert_complete(expected);
            assert!(!fixture.exchange().exists());
            assert!(
                !fixture
                    .root
                    .join(journal_name(OsStr::new("release")))
                    .exists()
            );
            assert!(!fixture.target.join(OWNER_MARKER).exists());
            assert!(
                !fixture
                    .root
                    .join(format!(
                        "{}-owner",
                        journal_name(OsStr::new("release")).to_string_lossy()
                    ))
                    .exists()
            );
        }
    }

    // Run in an isolated process so abrupt exit really bypasses destructors and
    // caller cleanup. The environment hook is absent from production binaries.
    #[test]
    #[ignore = "subprocess entry point for replacement crash tests"]
    fn replacement_crash_worker() {
        let root = PathBuf::from(std::env::var_os("COTT_DEPLOY_TEST_ROOT").expect("worker root"));
        publish_replace(&root.join("staged"), &root.join("release")).expect("injected crash");
        panic!("crash point was not reached");
    }

    #[test]
    fn process_crashes_recover_prepared_exchanged_and_partly_retired_trees() {
        for (fault, expected) in [
            ("relocated", b"old"),
            ("prepared", b"old"),
            ("staged", b"old"),
            ("exchanged", b"new"),
            ("committed", b"new"),
            ("retirement_member", b"new"),
            ("cleanup_marker", b"new"),
            ("retired", b"new"),
        ] {
            let fixture = Fixture::new();
            let output = std::process::Command::new(std::env::current_exe().expect("test binary"))
                .args([
                    "--exact",
                    "deploy::tests::replacement_crash_worker",
                    "--ignored",
                    "--nocapture",
                ])
                .env("COTT_DEPLOY_TEST_ROOT", &fixture.root)
                .env("COTT_DEPLOY_TEST_CRASH", fault)
                .output()
                .expect("crashing publisher");
            assert_eq!(
                output.status.code(),
                Some(86),
                "{fault}: {}",
                String::from_utf8_lossy(&output.stderr)
            );
            fixture.assert_complete(expected);
            fixture.recover().expect("recover after process crash");
            fixture.recover().expect("idempotent crash recovery");
            fixture.assert_complete(expected);
        }
    }

    #[test]
    fn continuous_namespace_readers_observe_only_old_or_new_directory() {
        let fixture = Fixture::new();
        let old = fs::metadata(&fixture.target).expect("old identity").ino();
        let new = fs::metadata(&fixture.staged).expect("new identity").ino();
        let done = AtomicBool::new(false);
        let (ready, started) = std::sync::mpsc::channel();
        std::thread::scope(|scope| {
            let reader = scope.spawn(|| {
                assert_eq!(
                    fs::metadata(&fixture.target)
                        .expect("initial deployment")
                        .ino(),
                    old
                );
                ready.send(()).expect("reader started");
                let mut saw_new = false;
                while !done.load(Ordering::Acquire) || !saw_new {
                    let tree = File::open(&fixture.target).expect("output must never disappear");
                    let inode = tree.metadata().expect("directory identity").ino();
                    assert!(
                        inode == old || inode == new,
                        "unpublished tree became visible"
                    );
                    saw_new |= inode == new;
                    std::thread::yield_now();
                }
            });
            started.recv().expect("reader ready");
            publish_replace(&fixture.staged, &fixture.target).expect("atomic replacement");
            done.store(true, Ordering::Release);
            reader.join().expect("reader must see a continuous output");
        });
        fixture.assert_complete(b"new");
    }

    #[test]
    fn recovery_refuses_substituted_retired_tree_and_preserves_unrelated_siblings() {
        let fixture = Fixture::new();
        REPLACEMENT_FAULT.with(|slot| *slot.borrow_mut() = Some("committed"));
        assert!(publish_replace(&fixture.staged, &fixture.target).is_err());
        let retained = fixture.root.join("retained-old");
        fs::rename(fixture.exchange(), &retained).expect("substitute retired tree");
        fs::create_dir(fixture.exchange()).expect("foreign directory");
        fs::write(fixture.exchange().join("foreign"), b"keep").expect("foreign data");
        let unrelated = fixture.root.join(".cott-deploy-unrelated");
        fs::create_dir(&unrelated).expect("unrelated sibling");
        fs::write(unrelated.join("foreign"), b"keep").expect("unrelated data");
        assert!(fixture.recover().is_err());
        fixture.assert_complete(b"new");
        assert_eq!(
            fs::read(fixture.exchange().join("foreign")).unwrap(),
            b"keep"
        );
        assert_eq!(fs::read(unrelated.join("foreign")).unwrap(), b"keep");
        fs::remove_dir_all(fixture.exchange()).expect("remove test substitution");
        fs::rename(retained, fixture.exchange()).expect("restore recorded identity");
        fixture.recover().expect("retry legitimate retirement");
        assert_eq!(fs::read(unrelated.join("foreign")).unwrap(), b"keep");
    }

    #[test]
    fn publication_revalidates_project_identity_after_earlier_preflight() {
        let fixture = Fixture::new();
        let context = ReplaceContext {
            root: fixture.root.join("authoring"),
            source_dir: fixture.root.join("authoring/src"),
            language_source_dir: fixture.root.join("authoring/python"),
            artifact_root: fixture.root.join("authoring/generated"),
            extra_protected: Vec::new(),
            project_name: "demo".to_owned(),
            language: TargetLanguage::Python,
        };
        require_replaceable(&context, &fixture.target).expect("earlier preflight");
        let old = fixture.root.join("old");
        fs::rename(&fixture.target, &old).expect("move validated target");
        deployment(&fixture.target, "foreign", b"foreign");
        assert!(publish_replace(&fixture.staged, &fixture.target).is_err());
        assert_eq!(
            fs::read(fixture.target.join("payload")).unwrap(),
            b"foreign"
        );
        assert_eq!(fs::read(old.join("payload")).unwrap(), b"old");
        assert_eq!(fs::read(fixture.staged.join("payload")).unwrap(), b"new");
    }

    #[test]
    fn recovery_does_not_clean_any_tree_when_the_visible_target_was_substituted() {
        let fixture = Fixture::new();
        REPLACEMENT_FAULT.with(|slot| *slot.borrow_mut() = Some("committed"));
        assert!(publish_replace(&fixture.staged, &fixture.target).is_err());
        let retained = fixture.root.join("retained-new");
        fs::rename(&fixture.target, &retained).expect("move committed deployment");
        deployment(&fixture.target, "foreign", b"foreign");
        assert!(fixture.recover().is_err());
        assert_eq!(
            fs::read(fixture.target.join("payload")).unwrap(),
            b"foreign"
        );
        assert_eq!(
            fs::read(fixture.exchange().join("payload")).unwrap(),
            b"old"
        );
        assert_eq!(fs::read(retained.join("payload")).unwrap(), b"new");
    }

    fn forged_journal(fixture: &Fixture, nominated: &Path, phase: &[u8]) {
        let parent = File::open(&fixture.root).unwrap();
        let target = File::open(&fixture.target).unwrap();
        let foreign = File::open(nominated).unwrap();
        let target_id = Identity::of(&target).unwrap();
        let foreign_id = Identity::of(&foreign).unwrap();
        let record =
            crate::hash::sha256_hex(&fs::read(fixture.target.join("generation.json")).unwrap());
        let exchanged = phase == b"PEC";
        let journal = ReplacementJournal {
            version: 1,
            parent: Identity::of(&parent).unwrap(),
            target: b"release".to_vec(),
            exchange: nominated.file_name().unwrap().as_bytes().to_vec(),
            old: if exchanged {
                foreign_id.clone()
            } else {
                target_id.clone()
            },
            new: if exchanged { target_id } else { foreign_id },
            old_record: record.clone(),
            new_record: record,
            project_name: "demo".to_owned(),
            language: "Python".to_owned(),
        };
        let mut bytes = serde_json::to_vec(&journal).unwrap();
        bytes.push(b'\n');
        bytes.extend_from_slice(phase);
        create_owned_file(&parent, &journal_name(OsStr::new("release")), &bytes)
            .expect("current-user single-link forged journal");
    }

    #[test]
    fn forged_journals_cannot_nominate_unrelated_siblings_or_skip_tree_ownership() {
        for phase in [b"P".as_slice(), b"PA", b"PEC"] {
            for reserved_name in [false, true] {
                let fixture = Fixture::new();
                let source = if reserved_name {
                    fixture.exchange()
                } else {
                    fixture.root.join("source")
                };
                fs::create_dir(&source).unwrap();
                fs::write(source.join("authored.cott"), b"irreplaceable source").unwrap();
                forged_journal(&fixture, &source, phase);
                assert!(
                    fixture.recover().is_err(),
                    "{phase:?}, reserved={reserved_name}"
                );
                assert_eq!(
                    fs::read(source.join("authored.cott")).unwrap(),
                    b"irreplaceable source"
                );
                fixture.assert_complete(b"old");
            }
        }
    }

    #[test]
    fn forged_cleanup_phases_cannot_remove_an_unowned_empty_reserved_directory() {
        for phase in [b"PA".as_slice(), b"PEC"] {
            let fixture = Fixture::new();
            let empty = fixture.exchange();
            fs::create_dir(&empty).unwrap();
            forged_journal(&fixture, &empty, phase);
            assert!(fixture.recover().is_err());
            assert!(empty.is_dir());
            fixture.assert_complete(b"old");
        }
    }

    #[test]
    fn prepared_abort_cleanup_resumes_after_partial_removal_and_checks_record_hash() {
        let fixture = Fixture::new();
        REPLACEMENT_FAULT.with(|slot| *slot.borrow_mut() = Some("prepared"));
        assert!(publish_replace(&fixture.staged, &fixture.target).is_err());
        let record_path = fixture.exchange().join("generation.json");
        let original = fs::read(&record_path).unwrap();
        fs::write(&record_path, b"tampered").unwrap();
        assert!(fixture.recover().is_err());
        assert_eq!(
            fs::read(fixture.exchange().join("payload")).unwrap(),
            b"new"
        );
        fs::write(&record_path, original).unwrap();
        REPLACEMENT_FAULT.with(|slot| *slot.borrow_mut() = Some("retirement_member"));
        assert!(fixture.recover().is_err());
        fixture.assert_complete(b"old");
        fixture.recover().expect("resume authorized partial abort");
        fixture.recover().expect("idempotent abort");
        fixture.assert_complete(b"old");
        assert!(!fixture.exchange().exists());
    }

    #[test]
    fn a_foreign_project_cannot_trigger_pending_recovery() {
        let fixture = Fixture::new();
        REPLACEMENT_FAULT.with(|slot| *slot.borrow_mut() = Some("prepared"));
        assert!(publish_replace(&fixture.staged, &fixture.target).is_err());
        let context = ReplaceContext {
            root: fixture.root.join("authoring"),
            source_dir: fixture.root.join("authoring/src"),
            language_source_dir: fixture.root.join("authoring/python"),
            artifact_root: fixture.root.join("authoring/generated"),
            extra_protected: Vec::new(),
            project_name: "foreign".to_owned(),
            language: TargetLanguage::Python,
        };
        assert!(require_replaceable(&context, &fixture.target).is_err());
        assert_eq!(
            fs::read(fixture.exchange().join("payload")).unwrap(),
            b"new"
        );
        fixture.assert_complete(b"old");
    }
}
