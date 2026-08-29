use std::collections::BTreeMap;
use std::fs::{self, File, OpenOptions};
use std::io::{self, Read, Write};
use std::os::unix::fs::{MetadataExt, OpenOptionsExt, PermissionsExt};
use std::os::unix::io::AsRawFd;
use std::path::{Component, Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};

use crate::hash::sha256_hex;

const JOURNAL_VERSION: u32 = 1;
#[cfg(test)]
thread_local! {
    static FAULT: std::cell::RefCell<Option<&'static str>> = const { std::cell::RefCell::new(None) };
}

#[cfg(test)]
fn arm_fault(name: Option<&'static str>) {
    FAULT.with(|fault| *fault.borrow_mut() = name);
}

fn fault(name: &'static str) -> Result<(), TransactionError> {
    #[cfg(test)]
    {
        let hit = FAULT.with(|fault| {
            let mut fault = fault.borrow_mut();
            if fault.as_ref().is_some_and(|target| *target == name) {
                *fault = None;
                true
            } else {
                false
            }
        });
        if hit {
            return Err(TransactionError::InjectedFault(name));
        }
    }
    let _ = name;
    Ok(())
}

#[derive(Debug)]
pub enum TransactionError {
    Io {
        operation: &'static str,
        path: PathBuf,
        source: io::Error,
    },
    UnsafePath(PathBuf),
    SnapshotDrift(PathBuf),
    CorruptJournal(PathBuf),
    ActiveTransaction(PathBuf),
    #[cfg(test)]
    InjectedFault(&'static str),
}

impl std::fmt::Display for TransactionError {
    fn fmt(&self, formatter: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::Io {
                operation,
                path,
                source,
            } => write!(
                formatter,
                "failed to {operation} {}: {source}",
                path.display()
            ),
            Self::UnsafePath(path) => {
                write!(formatter, "unsafe transaction path: {}", path.display())
            }
            Self::SnapshotDrift(path) => write!(
                formatter,
                "project input changed during transaction: {}",
                path.display()
            ),
            Self::CorruptJournal(path) => {
                write!(formatter, "corrupt transaction journal: {}", path.display())
            }
            Self::ActiveTransaction(path) => {
                write!(formatter, "project is locked: {}", path.display())
            }
            #[cfg(test)]
            Self::InjectedFault(name) => write!(formatter, "injected transaction fault: {name}"),
        }
    }
}

impl std::error::Error for TransactionError {}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct FileSnapshot {
    device: u64,
    inode: u64,
    mode: u32,
    size: u64,
    sha256: String,
}

#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub struct InputSnapshot {
    pub files: BTreeMap<PathBuf, Option<FileSnapshot>>,
}

impl InputSnapshot {
    pub fn capture(
        root: &Path,
        paths: impl IntoIterator<Item = PathBuf>,
    ) -> Result<Self, TransactionError> {
        let mut files = BTreeMap::new();
        for path in paths {
            validate_relative(&path)?;
            ensure_same_filesystem(root, &path)?;
            files.insert(path.clone(), snapshot_file(root, &path)?);
        }
        Ok(Self { files })
    }

    pub fn capture_expected(
        root: &Path,
        expected: impl IntoIterator<Item = (PathBuf, String)>,
        extra_paths: impl IntoIterator<Item = PathBuf>,
    ) -> Result<Self, TransactionError> {
        let expected = expected.into_iter().collect::<BTreeMap<_, _>>();
        let mut paths = expected.keys().cloned().collect::<Vec<_>>();
        paths.extend(extra_paths);
        paths.sort();
        paths.dedup();
        let snapshot = Self::capture(root, paths)?;
        for (path, hash) in expected {
            let actual = snapshot
                .files
                .get(&path)
                .and_then(Option::as_ref)
                .map(|file| file.sha256.as_str());
            if actual != Some(hash.strip_prefix("sha256:").unwrap_or(&hash)) {
                return Err(TransactionError::SnapshotDrift(path));
            }
        }
        Ok(snapshot)
    }

    pub fn merge_missing(&mut self, other: Self) {
        for (path, file) in other.files {
            self.files.entry(path).or_insert(file);
        }
    }
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum Operation {
    Write { path: PathBuf, bytes: Vec<u8> },
    Remove { path: PathBuf },
}

#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub struct ChangeSet {
    pub operations: Vec<Operation>,
    pub generation_record_last: bool,
}

pub struct ProjectSession {
    root: PathBuf,
    transactions: PathBuf,
    _lock: File,
}

impl ProjectSession {
    pub fn acquire(root: &Path) -> Result<Self, TransactionError> {
        let root = fs::canonicalize(root).map_err(|source| TransactionError::Io {
            operation: "canonicalize project root",
            path: root.to_path_buf(),
            source,
        })?;
        ensure_directory(&root)?;
        let cott = root.join(".cott");
        ensure_or_create_directory(&cott)?;
        let transactions = cott.join("transactions");
        ensure_or_create_directory(&transactions)?;
        let lock_path = cott.join("lock");
        let lock = OpenOptions::new()
            .create(true)
            .read(true)
            .write(true)
            .mode(0o600)
            .custom_flags(libc::O_CLOEXEC | libc::O_NOFOLLOW)
            .open(&lock_path)
            .map_err(|source| TransactionError::Io {
                operation: "open project lock",
                path: lock_path.clone(),
                source,
            })?;
        require_regular_metadata(
            &lock_path,
            &lock.metadata().map_err(|source| TransactionError::Io {
                operation: "stat project lock",
                path: lock_path.clone(),
                source,
            })?,
        )?;
        loop {
            let result = unsafe { libc::flock(lock.as_raw_fd(), libc::LOCK_EX | libc::LOCK_NB) };
            if result == 0 {
                break;
            }
            let source = io::Error::last_os_error();
            if source.kind() == io::ErrorKind::Interrupted {
                continue;
            }
            if source.raw_os_error() == Some(libc::EWOULDBLOCK) {
                return Err(TransactionError::ActiveTransaction(lock_path));
            }
            return Err(TransactionError::Io {
                operation: "lock project",
                path: lock_path,
                source,
            });
        }
        recover(&root, &transactions)?;
        Ok(Self {
            root,
            transactions,
            _lock: lock,
        })
    }

    pub fn root(&self) -> &Path {
        &self.root
    }

    pub fn apply(
        &self,
        snapshot: &InputSnapshot,
        changes: &ChangeSet,
    ) -> Result<(), TransactionError> {
        match self.apply_transaction(snapshot, changes) {
            Ok(()) => Ok(()),
            #[cfg(test)]
            Err(error @ TransactionError::InjectedFault(_)) => Err(error),
            Err(error) => match recover(&self.root, &self.transactions) {
                Ok(()) => Err(error),
                Err(recovery_error) => Err(recovery_error),
            },
        }
    }

    fn apply_transaction(
        &self,
        snapshot: &InputSnapshot,
        changes: &ChangeSet,
    ) -> Result<(), TransactionError> {
        for (path, expected) in &snapshot.files {
            let actual = snapshot_file(&self.root, path)?;
            if &actual != expected {
                return Err(TransactionError::SnapshotDrift(path.clone()));
            }
        }
        let id = format!(
            "{:x}-{}",
            SystemTime::now()
                .duration_since(UNIX_EPOCH)
                .expect("system clock before epoch")
                .as_nanos(),
            std::process::id()
        );
        let directory = self.transactions.join(id);
        fs::create_dir(&directory).map_err(|source| TransactionError::Io {
            operation: "create transaction",
            path: directory.clone(),
            source,
        })?;
        fs::set_permissions(&directory, fs::Permissions::from_mode(0o755)).map_err(|source| {
            TransactionError::Io {
                operation: "set transaction directory mode",
                path: directory.clone(),
                source,
            }
        })?;
        sync_directory(&self.transactions)?;
        let mut operations = changes.operations.iter().collect::<Vec<_>>();
        if changes.generation_record_last {
            operations.sort_by_key(|operation| {
                let path = match operation {
                    Operation::Write { path, .. } | Operation::Remove { path } => path,
                };
                path.file_name()
                    .is_some_and(|name| name == "generation.json")
            });
        }
        let mut seen = std::collections::BTreeSet::new();
        let entries = operations
            .into_iter()
            .map(|operation| {
                let path = match operation {
                    Operation::Write { path, .. } | Operation::Remove { path } => path,
                };
                if !seen.insert(path.clone()) {
                    return Err(TransactionError::UnsafePath(path.clone()));
                }
                journal_entry(&self.root, operation)
            })
            .collect::<Result<Vec<_>, _>>()?;
        let mut created_directories = Vec::new();
        for entry in &entries {
            created_directories.extend(missing_parent_directories(&self.root, &entry.path)?);
        }
        created_directories.sort();
        created_directories.dedup();
        created_directories.sort_by_key(|path| path.components().count());
        let journal = Journal {
            schema_version: JOURNAL_VERSION,
            state: JournalState::Prepared,
            entries,
            created_directories,
        };
        write_journal(&directory, &journal)?;
        let mut journal = journal;
        journal.state = JournalState::Applying;
        write_journal(&directory, &journal)?;
        for entry in &journal.entries {
            apply_entry(&self.root, &directory, entry)?;
        }
        journal.state = JournalState::Committed;
        write_journal(&directory, &journal)?;
        fs::remove_dir_all(&directory).map_err(|source| TransactionError::Io {
            operation: "remove committed transaction",
            path: directory.clone(),
            source,
        })?;
        fault("cleanup.remove")?;
        sync_directory(&self.transactions)?;
        fault("cleanup.dir_fsync")?;
        Ok(())
    }
}

impl Drop for ProjectSession {
    fn drop(&mut self) {
        unsafe {
            libc::flock(self._lock.as_raw_fd(), libc::LOCK_UN);
        }
    }
}

#[derive(Clone, Copy, Debug, Deserialize, Eq, PartialEq, Serialize)]
#[serde(rename_all = "lowercase")]
enum JournalState {
    Prepared,
    Applying,
    Committed,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct Journal {
    schema_version: u32,
    state: JournalState,
    entries: Vec<JournalEntry>,
    created_directories: Vec<PathBuf>,
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct JournalEntry {
    path: PathBuf,
    before: Option<Vec<u8>>,
    before_hash: Option<String>,
    before_mode: Option<u32>,
    after: Option<Vec<u8>>,
    after_hash: Option<String>,
}

fn journal_entry(root: &Path, operation: &Operation) -> Result<JournalEntry, TransactionError> {
    let (path, after) = match operation {
        Operation::Write { path, bytes } => (path, Some(bytes.clone())),
        Operation::Remove { path } => (path, None),
    };
    validate_relative(path)?;
    ensure_same_filesystem(root, path)?;
    let before = read_regular_file(root, path)?;
    let before_hash = before.as_ref().map(|(bytes, _, _, _)| sha256_hex(bytes));
    let before_mode = before.as_ref().map(|(_, mode, _, _)| *mode);
    let before = before.map(|(bytes, _, _, _)| bytes);
    let after_hash = after.as_deref().map(sha256_hex);
    Ok(JournalEntry {
        path: path.clone(),
        before,
        before_hash,
        before_mode,
        after,
        after_hash,
    })
}

fn recover(root: &Path, transactions: &Path) -> Result<(), TransactionError> {
    let entries = fs::read_dir(transactions).map_err(|source| TransactionError::Io {
        operation: "read transaction directory",
        path: transactions.to_path_buf(),
        source,
    })?;
    let mut journals =
        entries
            .collect::<Result<Vec<_>, _>>()
            .map_err(|source| TransactionError::Io {
                operation: "read transaction entry",
                path: transactions.to_path_buf(),
                source,
            })?;
    journals.sort_by_key(|entry| entry.file_name());
    if journals.len() > 1 {
        return Err(TransactionError::CorruptJournal(transactions.to_path_buf()));
    }
    let Some(entry) = journals.pop() else {
        return Ok(());
    };
    let directory = entry.path();
    ensure_directory(&directory)?;
    let journal_path = directory.join("journal.json");
    let next_path = directory.join("journal.next");
    let path = if journal_path.exists() {
        &journal_path
    } else if next_path.exists() {
        &next_path
    } else if fs::read_dir(&directory)
        .map_err(|_| TransactionError::CorruptJournal(directory.clone()))?
        .next()
        .is_none()
    {
        fs::remove_dir(&directory)
            .map_err(|_| TransactionError::CorruptJournal(directory.clone()))?;
        sync_directory(transactions)?;
        return Ok(());
    } else {
        return Err(TransactionError::CorruptJournal(directory));
    };
    require_regular_single_link(path)?;
    let bytes = fs::read(path).map_err(|_| TransactionError::CorruptJournal(directory.clone()))?;
    let journal: Journal = serde_json::from_slice(&bytes)
        .map_err(|_| TransactionError::CorruptJournal(directory.clone()))?;
    if path == &next_path && journal.state != JournalState::Prepared {
        return Err(TransactionError::CorruptJournal(directory));
    }
    if journal.schema_version != JOURNAL_VERSION {
        return Err(TransactionError::CorruptJournal(directory));
    }
    validate_journal(root, &directory, &journal)?;
    match journal.state {
        JournalState::Committed => {}
        JournalState::Prepared | JournalState::Applying => {
            for item in journal.entries.iter().rev() {
                restore_entry(root, &directory, item)?;
            }
            for relative in journal.created_directories.iter().rev() {
                let path = root.join(relative);
                match fs::remove_dir(&path) {
                    Ok(()) => {
                        fault("rollback.directory_remove")?;
                        sync_directory(
                            path.parent()
                                .ok_or_else(|| TransactionError::UnsafePath(relative.clone()))?,
                        )?;
                        fault("rollback.directory_parent_fsync")?;
                    }
                    Err(source) if source.kind() == io::ErrorKind::NotFound => {}
                    Err(source) if source.kind() == io::ErrorKind::DirectoryNotEmpty => {}
                    Err(source) => {
                        return Err(TransactionError::Io {
                            operation: "remove recovered transaction directory",
                            path,
                            source,
                        });
                    }
                }
            }
        }
    }
    fs::remove_dir_all(&directory).map_err(|source| TransactionError::Io {
        operation: "remove recovered transaction",
        path: directory,
        source,
    })?;
    fault("recovery.cleanup.remove")?;
    sync_directory(transactions)?;
    fault("recovery.cleanup.dir_fsync")
}
fn validate_journal(
    root: &Path,
    directory: &Path,
    journal: &Journal,
) -> Result<(), TransactionError> {
    let mut paths = std::collections::BTreeSet::new();
    let mut image_names = std::collections::BTreeSet::new();
    for entry in &journal.entries {
        validate_relative(&entry.path)?;
        if !paths.insert(&entry.path) {
            return Err(TransactionError::CorruptJournal(directory.to_path_buf()));
        }
        if entry.before.as_deref().map(sha256_hex) != entry.before_hash
            || entry.after.as_deref().map(sha256_hex) != entry.after_hash
            || entry.before.is_some() != entry.before_mode.is_some()
        {
            return Err(TransactionError::CorruptJournal(directory.to_path_buf()));
        }
        image_names.insert(format!(
            "image-{}",
            sha256_hex(entry.path.as_os_str().as_encoded_bytes())
        ));
        let current = read_regular_file(root, &entry.path)?;
        let current_hash = current.as_ref().map(|(bytes, _, _, _)| sha256_hex(bytes));
        let current_mode = current.as_ref().map(|(_, mode, _, _)| *mode);
        let before = current_hash == entry.before_hash && current_mode == entry.before_mode;
        let after =
            current_hash == entry.after_hash && current_mode == entry.after.as_ref().map(|_| 0o644);
        let valid = match journal.state {
            JournalState::Prepared => before,
            JournalState::Applying => before || after,
            JournalState::Committed => after,
        };
        if !valid {
            return Err(TransactionError::CorruptJournal(directory.to_path_buf()));
        }
    }
    let mut directories = std::collections::BTreeSet::new();
    for path in &journal.created_directories {
        validate_relative(path)?;
        if !directories.insert(path) {
            return Err(TransactionError::CorruptJournal(directory.to_path_buf()));
        }
    }
    for entry in fs::read_dir(directory).map_err(|source| TransactionError::Io {
        operation: "read transaction journal contents",
        path: directory.to_path_buf(),
        source,
    })? {
        let entry = entry.map_err(|source| TransactionError::Io {
            operation: "read transaction journal entry",
            path: directory.to_path_buf(),
            source,
        })?;
        let name = entry.file_name().to_string_lossy().into_owned();
        if name != "journal.json" && name != "journal.next" && !image_names.contains(&name) {
            return Err(TransactionError::CorruptJournal(directory.to_path_buf()));
        }
        require_regular_single_link(&entry.path())?;
    }
    Ok(())
}

fn apply_entry(
    root: &Path,
    transaction: &Path,
    entry: &JournalEntry,
) -> Result<(), TransactionError> {
    write_image(
        root,
        transaction,
        &entry.path,
        entry.after.as_deref(),
        0o644,
        false,
    )
}

fn restore_entry(
    root: &Path,
    transaction: &Path,
    entry: &JournalEntry,
) -> Result<(), TransactionError> {
    write_image(
        root,
        transaction,
        &entry.path,
        entry.before.as_deref(),
        entry.before_mode.unwrap_or(0o644),
        true,
    )
}

fn write_image(
    root: &Path,
    transaction: &Path,
    relative: &Path,
    bytes: Option<&[u8]>,
    mode: u32,
    restoring: bool,
) -> Result<(), TransactionError> {
    validate_relative(relative)?;
    validate_target(root, relative)?;
    let path = root.join(relative);
    match bytes {
        Some(bytes) => {
            create_parent_directories(root, relative)?;
            let parent = path
                .parent()
                .ok_or_else(|| TransactionError::UnsafePath(relative.to_path_buf()))?;
            let temporary = transaction.join(format!(
                "image-{}",
                sha256_hex(relative.as_os_str().as_encoded_bytes())
            ));
            if temporary.exists() {
                require_regular_single_link(&temporary)?;
                fs::remove_file(&temporary).map_err(|source| TransactionError::Io {
                    operation: "remove stale transaction image",
                    path: temporary.clone(),
                    source,
                })?;
            }
            let mut file = OpenOptions::new()
                .create_new(true)
                .write(true)
                .mode(0o600)
                .custom_flags(libc::O_CLOEXEC | libc::O_NOFOLLOW)
                .open(&temporary)
                .map_err(|source| TransactionError::Io {
                    operation: "write transaction image",
                    path: temporary.clone(),
                    source,
                })?;
            file.write_all(bytes)
                .and_then(|_| file.set_permissions(fs::Permissions::from_mode(mode)))
                .and_then(|_| file.sync_all())
                .map_err(|source| TransactionError::Io {
                    operation: "sync transaction image",
                    path: temporary.clone(),
                    source,
                })?;
            fault(if restoring {
                "restore.file_fsync"
            } else {
                "apply.file_fsync"
            })?;
            sync_directory(transaction)?;
            fault(if restoring {
                "restore.image_dir_fsync"
            } else {
                "apply.image_dir_fsync"
            })?;
            fs::rename(&temporary, &path).map_err(|source| TransactionError::Io {
                operation: "rename transaction image",
                path: path.clone(),
                source,
            })?;
            if !restoring
                && relative
                    .file_name()
                    .is_some_and(|name| name == "generation.json")
            {
                fault("apply.generation.rename")?;
            }
            fault(if restoring {
                "restore.rename"
            } else {
                "apply.rename"
            })?;
            sync_directory(parent)?;
            fault(if restoring {
                "restore.parent_fsync"
            } else {
                "apply.parent_fsync"
            })?;
        }
        None => match fs::remove_file(&path) {
            Ok(()) => {
                fault(if restoring {
                    "restore.delete"
                } else {
                    "apply.delete"
                })?;
                sync_directory(
                    path.parent()
                        .ok_or_else(|| TransactionError::UnsafePath(relative.to_path_buf()))?,
                )?;
                fault(if restoring {
                    "restore.delete_parent_fsync"
                } else {
                    "apply.delete_parent_fsync"
                })?;
            }
            Err(source) if source.kind() == io::ErrorKind::NotFound => {}
            Err(source) => {
                return Err(TransactionError::Io {
                    operation: "remove transaction image",
                    path,
                    source,
                });
            }
        },
    }
    Ok(())
}

fn write_journal(directory: &Path, journal: &Journal) -> Result<(), TransactionError> {
    let path = directory.join("journal.json");
    let temporary = directory.join("journal.next");
    let mut bytes = serde_json::to_vec(journal).expect("journal serialization is infallible");
    bytes.push(b'\n');
    if temporary.exists() {
        require_regular_single_link(&temporary)?;
        fs::remove_file(&temporary).map_err(|source| TransactionError::Io {
            operation: "remove stale journal image",
            path: temporary.clone(),
            source,
        })?;
    }
    let mut file = OpenOptions::new()
        .create_new(true)
        .write(true)
        .mode(0o600)
        .custom_flags(libc::O_CLOEXEC | libc::O_NOFOLLOW)
        .open(&temporary)
        .map_err(|source| TransactionError::Io {
            operation: "write transaction journal",
            path: temporary.clone(),
            source,
        })?;
    file.write_all(&bytes)
        .and_then(|_| file.sync_all())
        .map_err(|source| TransactionError::Io {
            operation: "sync transaction journal",
            path: temporary.clone(),
            source,
        })?;
    fault(match journal.state {
        JournalState::Prepared => "prepared.file_fsync",
        JournalState::Applying => "applying.file_fsync",
        JournalState::Committed => "committed.file_fsync",
    })?;
    sync_directory(directory)?;
    fault(match journal.state {
        JournalState::Prepared => "prepared.image_dir_fsync",
        JournalState::Applying => "applying.image_dir_fsync",
        JournalState::Committed => "committed.image_dir_fsync",
    })?;
    if path.exists() {
        require_regular_single_link(&path)?;
    }
    fs::rename(&temporary, &path).map_err(|source| TransactionError::Io {
        operation: "publish transaction journal",
        path: path.clone(),
        source,
    })?;
    fault(match journal.state {
        JournalState::Prepared => "prepared.rename",
        JournalState::Applying => "applying.rename",
        JournalState::Committed => "committed.rename",
    })?;
    sync_directory(directory)?;
    fault(match journal.state {
        JournalState::Prepared => "prepared.dir_fsync",
        JournalState::Applying => "applying.dir_fsync",
        JournalState::Committed => "committed.dir_fsync",
    })
}

fn snapshot_file(root: &Path, relative: &Path) -> Result<Option<FileSnapshot>, TransactionError> {
    Ok(
        read_regular_file(root, relative)?.map(|(bytes, mode, device, inode)| FileSnapshot {
            device,
            inode,
            mode,
            size: bytes.len() as u64,
            sha256: sha256_hex(&bytes),
        }),
    )
}

fn ensure_same_filesystem(root: &Path, relative: &Path) -> Result<(), TransactionError> {
    let root_device = fs::symlink_metadata(root)
        .map_err(|source| TransactionError::Io {
            operation: "stat project filesystem",
            path: root.to_path_buf(),
            source,
        })?
        .dev();
    let mut current = root.to_path_buf();
    for component in relative.components() {
        let Component::Normal(component) = component else {
            return Err(TransactionError::UnsafePath(relative.to_path_buf()));
        };
        current.push(component);
        match fs::symlink_metadata(&current) {
            Ok(metadata) if metadata.dev() == root_device => {}
            Ok(_) => return Err(TransactionError::UnsafePath(current)),
            Err(source) if source.kind() == io::ErrorKind::NotFound => break,
            Err(source) => {
                return Err(TransactionError::Io {
                    operation: "inspect target filesystem",
                    path: current,
                    source,
                });
            }
        }
    }
    Ok(())
}

fn read_regular_file(
    root: &Path,
    relative: &Path,
) -> Result<Option<(Vec<u8>, u32, u64, u64)>, TransactionError> {
    validate_relative(relative)?;
    validate_target(root, relative)?;
    let path = root.join(relative);
    let mut file = match OpenOptions::new()
        .read(true)
        .custom_flags(libc::O_CLOEXEC | libc::O_NOFOLLOW)
        .open(&path)
    {
        Ok(file) => file,
        Err(source) if source.kind() == io::ErrorKind::NotFound => return Ok(None),
        Err(source) => {
            return Err(TransactionError::Io {
                operation: "open transaction input",
                path,
                source,
            });
        }
    };
    let before = file.metadata().map_err(|source| TransactionError::Io {
        operation: "stat transaction input",
        path: path.clone(),
        source,
    })?;
    require_regular_metadata(&path, &before)?;
    let mut bytes = Vec::new();
    file.read_to_end(&mut bytes)
        .map_err(|source| TransactionError::Io {
            operation: "read transaction input",
            path: path.clone(),
            source,
        })?;
    let after = file.metadata().map_err(|source| TransactionError::Io {
        operation: "restat transaction input",
        path: path.clone(),
        source,
    })?;
    if before.dev() != after.dev()
        || before.ino() != after.ino()
        || before.len() != after.len()
        || before.mtime() != after.mtime()
        || before.mtime_nsec() != after.mtime_nsec()
    {
        return Err(TransactionError::SnapshotDrift(relative.to_path_buf()));
    }
    let current = fs::symlink_metadata(&path).map_err(|source| TransactionError::Io {
        operation: "restat transaction path",
        path: path.clone(),
        source,
    })?;
    require_regular_metadata(&path, &current)?;
    if current.dev() != before.dev() || current.ino() != before.ino() {
        return Err(TransactionError::SnapshotDrift(relative.to_path_buf()));
    }
    Ok(Some((
        bytes,
        before.mode() & 0o7777,
        before.dev(),
        before.ino(),
    )))
}

fn validate_target(root: &Path, relative: &Path) -> Result<(), TransactionError> {
    let mut current = root.to_path_buf();
    let count = relative.components().count();
    for (index, component) in relative.components().enumerate() {
        let Component::Normal(component) = component else {
            return Err(TransactionError::UnsafePath(relative.to_path_buf()));
        };
        current.push(component);
        match fs::symlink_metadata(&current) {
            Ok(metadata) if index + 1 == count => {
                require_regular_metadata(&current, &metadata)?;
            }
            Ok(metadata) if metadata.is_dir() && !metadata.file_type().is_symlink() => {}
            Ok(_) => return Err(TransactionError::UnsafePath(current)),
            Err(source) if source.kind() == io::ErrorKind::NotFound => return Ok(()),
            Err(source) => {
                return Err(TransactionError::Io {
                    operation: "inspect transaction path",
                    path: current,
                    source,
                });
            }
        }
    }
    Ok(())
}

fn missing_parent_directories(
    root: &Path,
    relative: &Path,
) -> Result<Vec<PathBuf>, TransactionError> {
    let Some(parent) = relative.parent() else {
        return Ok(Vec::new());
    };
    let mut current = root.to_path_buf();
    let mut relative_current = PathBuf::new();
    let mut missing = Vec::new();
    for component in parent.components() {
        let Component::Normal(component) = component else {
            return Err(TransactionError::UnsafePath(relative.to_path_buf()));
        };
        current.push(component);
        relative_current.push(component);
        match fs::symlink_metadata(&current) {
            Ok(metadata) if metadata.is_dir() && !metadata.file_type().is_symlink() => {}
            Ok(_) => return Err(TransactionError::UnsafePath(current)),
            Err(source) if source.kind() == io::ErrorKind::NotFound => {
                missing.push(relative_current.clone());
            }
            Err(source) => {
                return Err(TransactionError::Io {
                    operation: "inspect transaction parent",
                    path: current,
                    source,
                });
            }
        }
    }
    Ok(missing)
}

fn create_parent_directories(root: &Path, relative: &Path) -> Result<(), TransactionError> {
    let Some(parent) = relative.parent() else {
        return Ok(());
    };
    let mut current = root.to_path_buf();
    for component in parent.components() {
        let Component::Normal(component) = component else {
            return Err(TransactionError::UnsafePath(relative.to_path_buf()));
        };
        let containing = current.clone();
        current.push(component);
        match fs::symlink_metadata(&current) {
            Ok(metadata) if metadata.is_dir() && !metadata.file_type().is_symlink() => {}
            Ok(_) => return Err(TransactionError::UnsafePath(current)),
            Err(source) if source.kind() == io::ErrorKind::NotFound => {
                fs::create_dir(&current).map_err(|source| TransactionError::Io {
                    operation: "create transaction parent",
                    path: current.clone(),
                    source,
                })?;
                fs::set_permissions(&current, fs::Permissions::from_mode(0o755)).map_err(
                    |source| TransactionError::Io {
                        operation: "set transaction parent mode",
                        path: current.clone(),
                        source,
                    },
                )?;
                sync_directory(&containing)?;
            }
            Err(source) => {
                return Err(TransactionError::Io {
                    operation: "inspect transaction parent",
                    path: current,
                    source,
                });
            }
        }
    }
    Ok(())
}

fn require_regular_single_link(path: &Path) -> Result<(), TransactionError> {
    let metadata = fs::symlink_metadata(path).map_err(|source| TransactionError::Io {
        operation: "stat transaction file",
        path: path.to_path_buf(),
        source,
    })?;
    require_regular_metadata(path, &metadata)
}

fn require_regular_metadata(path: &Path, metadata: &fs::Metadata) -> Result<(), TransactionError> {
    if metadata.is_file() && !metadata.file_type().is_symlink() && metadata.nlink() == 1 {
        Ok(())
    } else {
        Err(TransactionError::UnsafePath(path.to_path_buf()))
    }
}

fn validate_relative(path: &Path) -> Result<(), TransactionError> {
    if path.as_os_str().is_empty()
        || path.to_str().is_none()
        || path.is_absolute()
        || path
            .components()
            .any(|component| !matches!(component, Component::Normal(_)))
    {
        Err(TransactionError::UnsafePath(path.to_path_buf()))
    } else {
        Ok(())
    }
}

fn ensure_directory(path: &Path) -> Result<(), TransactionError> {
    match fs::symlink_metadata(path) {
        Ok(metadata) if metadata.is_dir() && !metadata.file_type().is_symlink() => Ok(()),
        Ok(_) => Err(TransactionError::UnsafePath(path.to_path_buf())),
        Err(source) => Err(TransactionError::Io {
            operation: "stat transaction directory",
            path: path.to_path_buf(),
            source,
        }),
    }
}

fn ensure_or_create_directory(path: &Path) -> Result<(), TransactionError> {
    match fs::symlink_metadata(path) {
        Ok(metadata) if metadata.is_dir() && !metadata.file_type().is_symlink() => Ok(()),
        Ok(_) => Err(TransactionError::UnsafePath(path.to_path_buf())),
        Err(source) if source.kind() == io::ErrorKind::NotFound => {
            fs::create_dir(path).map_err(|source| TransactionError::Io {
                operation: "create transaction directory",
                path: path.to_path_buf(),
                source,
            })?;
            fs::set_permissions(path, fs::Permissions::from_mode(0o755)).map_err(|source| {
                TransactionError::Io {
                    operation: "set transaction directory mode",
                    path: path.to_path_buf(),
                    source,
                }
            })?;
            sync_directory(path.parent().expect("transaction directory has parent"))
        }
        Err(source) => Err(TransactionError::Io {
            operation: "stat transaction directory",
            path: path.to_path_buf(),
            source,
        }),
    }
}

fn sync_directory(path: &Path) -> Result<(), TransactionError> {
    let directory = File::open(path).map_err(|source| TransactionError::Io {
        operation: "open transaction directory",
        path: path.to_path_buf(),
        source,
    })?;
    directory.sync_all().map_err(|source| TransactionError::Io {
        operation: "sync transaction directory",
        path: path.to_path_buf(),
        source,
    })
}

#[cfg(test)]
mod tests {
    use super::*;
    static NEXT_TEMP: std::sync::atomic::AtomicU64 = std::sync::atomic::AtomicU64::new(0);

    struct Temp(PathBuf);

    impl Temp {
        fn new() -> Self {
            let path = std::env::temp_dir().join(format!(
                "cott-transaction-unit-{}-{}",
                std::process::id(),
                NEXT_TEMP.fetch_add(1, std::sync::atomic::Ordering::Relaxed)
            ));
            fs::create_dir(&path).expect("temporary project");
            Self(path)
        }

        fn path(&self) -> &Path {
            &self.0
        }
    }

    impl Drop for Temp {
        fn drop(&mut self) {
            let _ = fs::remove_dir_all(&self.0);
        }
    }

    fn fixture() -> (Temp, InputSnapshot, ChangeSet) {
        let temp = Temp::new();
        fs::create_dir(temp.path().join("generated")).expect("generated directory");
        fs::write(temp.path().join("value"), b"old\n").expect("old value");
        fs::write(temp.path().join("removed"), b"remove\n").expect("removed value");
        fs::write(
            temp.path().join("generated/generation.json"),
            b"old generation\n",
        )
        .expect("old generation");
        let paths = [
            PathBuf::from("value"),
            PathBuf::from("removed"),
            PathBuf::from("new/child"),
            PathBuf::from("generated/generation.json"),
        ];
        let snapshot = InputSnapshot::capture(temp.path(), paths).expect("snapshot");
        let changes = ChangeSet {
            operations: vec![
                Operation::Write {
                    path: PathBuf::from("generated/generation.json"),
                    bytes: b"new generation\n".to_vec(),
                },
                Operation::Write {
                    path: PathBuf::from("value"),
                    bytes: b"new\n".to_vec(),
                },
                Operation::Write {
                    path: PathBuf::from("new/child"),
                    bytes: b"child\n".to_vec(),
                },
                Operation::Remove {
                    path: PathBuf::from("removed"),
                },
            ],
            generation_record_last: true,
        };
        (temp, snapshot, changes)
    }

    fn is_old(root: &Path) -> bool {
        fs::read(root.join("value")).ok().as_deref() == Some(b"old\n")
            && fs::read(root.join("removed")).ok().as_deref() == Some(b"remove\n")
            && !root.join("new").exists()
            && fs::read(root.join("generated/generation.json"))
                .ok()
                .as_deref()
                == Some(b"old generation\n")
    }

    fn is_new(root: &Path) -> bool {
        fs::read(root.join("value")).ok().as_deref() == Some(b"new\n")
            && !root.join("removed").exists()
            && fs::read(root.join("new/child")).ok().as_deref() == Some(b"child\n")
            && fs::read(root.join("generated/generation.json"))
                .ok()
                .as_deref()
                == Some(b"new generation\n")
    }

    #[test]
    fn every_apply_fault_recovers_to_one_complete_snapshot() {
        let faults = [
            "prepared.file_fsync",
            "prepared.image_dir_fsync",
            "prepared.rename",
            "prepared.dir_fsync",
            "applying.file_fsync",
            "applying.image_dir_fsync",
            "applying.rename",
            "applying.dir_fsync",
            "apply.file_fsync",
            "apply.image_dir_fsync",
            "apply.rename",
            "apply.parent_fsync",
            "apply.delete",
            "apply.delete_parent_fsync",
            "apply.generation.rename",
            "committed.file_fsync",
            "committed.image_dir_fsync",
            "committed.rename",
            "committed.dir_fsync",
            "cleanup.remove",
            "cleanup.dir_fsync",
        ];
        for point in faults {
            let (temp, snapshot, changes) = fixture();
            let session = ProjectSession::acquire(temp.path()).expect("session");
            arm_fault(Some(point));
            assert!(session.apply(&snapshot, &changes).is_err(), "{point}");
            drop(session);
            arm_fault(None);
            drop(ProjectSession::acquire(temp.path()).expect("recovery"));
            assert!(
                is_old(temp.path()) || is_new(temp.path()),
                "mixed snapshot after {point}"
            );
        }
    }

    #[test]
    fn generation_record_is_the_last_managed_rename() {
        let (temp, snapshot, changes) = fixture();
        let session = ProjectSession::acquire(temp.path()).expect("session");
        arm_fault(Some("apply.generation.rename"));
        assert!(session.apply(&snapshot, &changes).is_err());
        assert!(
            is_new(temp.path()),
            "all other operations must precede generation.json"
        );
        drop(session);
        arm_fault(None);
        drop(ProjectSession::acquire(temp.path()).expect("rollback"));
        assert!(is_old(temp.path()));
    }

    #[test]
    fn interrupted_rollback_is_idempotent() {
        let faults = [
            "restore.file_fsync",
            "restore.image_dir_fsync",
            "restore.rename",
            "restore.parent_fsync",
            "restore.delete",
            "restore.delete_parent_fsync",
            "rollback.directory_remove",
            "rollback.directory_parent_fsync",
            "recovery.cleanup.remove",
            "recovery.cleanup.dir_fsync",
        ];
        for point in faults {
            let (temp, snapshot, changes) = fixture();
            let session = ProjectSession::acquire(temp.path()).expect("session");
            arm_fault(Some("committed.file_fsync"));
            assert!(session.apply(&snapshot, &changes).is_err());
            drop(session);

            arm_fault(Some(point));
            assert!(ProjectSession::acquire(temp.path()).is_err(), "{point}");
            arm_fault(None);
            drop(ProjectSession::acquire(temp.path()).expect("second recovery"));
            assert!(is_old(temp.path()), "rollback did not finish after {point}");
        }
    }
}
