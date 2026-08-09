use std::collections::BTreeMap;
use std::fs::{self, File, OpenOptions};
use std::io::{self, Write};
use std::os::unix::io::AsRawFd;
use std::path::{Component, Path, PathBuf};
use std::time::{SystemTime, UNIX_EPOCH};

use serde::{Deserialize, Serialize};

use crate::hash::sha256_hex;

const JOURNAL_VERSION: u32 = 1;

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
        }
    }
}

impl std::error::Error for TransactionError {}

#[derive(Clone, Debug, Default, Eq, PartialEq)]
pub struct InputSnapshot {
    pub files: BTreeMap<PathBuf, Option<String>>,
}

impl InputSnapshot {
    pub fn capture(
        root: &Path,
        paths: impl IntoIterator<Item = PathBuf>,
    ) -> Result<Self, TransactionError> {
        let mut files = BTreeMap::new();
        for path in paths {
            validate_relative(&path)?;
            files.insert(path.clone(), file_hash(&root.join(path))?);
        }
        Ok(Self { files })
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
        reject_symlink(&lock_path)?;
        let lock = OpenOptions::new()
            .create(true)
            .read(true)
            .write(true)
            .open(&lock_path)
            .map_err(|source| TransactionError::Io {
                operation: "open project lock",
                path: lock_path.clone(),
                source,
            })?;
        let result = unsafe { libc::flock(lock.as_raw_fd(), libc::LOCK_EX | libc::LOCK_NB) };
        if result != 0 {
            return Err(TransactionError::ActiveTransaction(lock_path));
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
        for (path, expected) in &snapshot.files {
            let actual = file_hash(&self.root.join(path))?;
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
        let entries = changes
            .operations
            .iter()
            .map(|operation| journal_entry(&self.root, operation))
            .collect::<Result<Vec<_>, _>>()?;
        let journal = Journal {
            schema_version: JOURNAL_VERSION,
            state: JournalState::Prepared,
            entries,
        };
        write_journal(&directory, &journal)?;
        let mut journal = journal;
        journal.state = JournalState::Applying;
        write_journal(&directory, &journal)?;
        for entry in &journal.entries {
            apply_entry(&self.root, entry)?;
        }
        journal.state = JournalState::Committed;
        write_journal(&directory, &journal)?;
        fs::remove_dir_all(&directory).map_err(|source| TransactionError::Io {
            operation: "remove committed transaction",
            path: directory,
            source,
        })?;
        sync_directory(&self.transactions)?;
        Ok(())
    }
}

#[derive(Clone, Debug, Deserialize, Serialize)]
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
}

#[derive(Clone, Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
struct JournalEntry {
    path: PathBuf,
    before: Option<Vec<u8>>,
    after: Option<Vec<u8>>,
}

fn journal_entry(root: &Path, operation: &Operation) -> Result<JournalEntry, TransactionError> {
    let (path, after) = match operation {
        Operation::Write { path, bytes } => (path, Some(bytes.clone())),
        Operation::Remove { path } => (path, None),
    };
    validate_relative(path)?;
    let target = root.join(path);
    reject_symlink(&target)?;
    let before = match fs::read(&target) {
        Ok(bytes) => Some(bytes),
        Err(source) if source.kind() == io::ErrorKind::NotFound => None,
        Err(source) => {
            return Err(TransactionError::Io {
                operation: "read transaction pre-image",
                path: target,
                source,
            });
        }
    };
    Ok(JournalEntry {
        path: path.clone(),
        before,
        after,
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
    let bytes = fs::read(directory.join("journal.json"))
        .map_err(|_| TransactionError::CorruptJournal(directory.clone()))?;
    let journal: Journal = serde_json::from_slice(&bytes)
        .map_err(|_| TransactionError::CorruptJournal(directory.clone()))?;
    if journal.schema_version != JOURNAL_VERSION {
        return Err(TransactionError::CorruptJournal(directory));
    }
    match journal.state {
        JournalState::Committed => {}
        JournalState::Prepared | JournalState::Applying => {
            for item in journal.entries.iter().rev() {
                restore_entry(root, item)?;
            }
        }
    }
    fs::remove_dir_all(&directory).map_err(|source| TransactionError::Io {
        operation: "remove recovered transaction",
        path: directory,
        source,
    })?;
    sync_directory(transactions)
}

fn apply_entry(root: &Path, entry: &JournalEntry) -> Result<(), TransactionError> {
    write_image(root, &entry.path, entry.after.as_deref())
}
fn restore_entry(root: &Path, entry: &JournalEntry) -> Result<(), TransactionError> {
    write_image(root, &entry.path, entry.before.as_deref())
}

fn write_image(root: &Path, relative: &Path, bytes: Option<&[u8]>) -> Result<(), TransactionError> {
    validate_relative(relative)?;
    let path = root.join(relative);
    reject_symlink(&path)?;
    match bytes {
        Some(bytes) => {
            let parent = path
                .parent()
                .ok_or_else(|| TransactionError::UnsafePath(relative.to_path_buf()))?;
            fs::create_dir_all(parent).map_err(|source| TransactionError::Io {
                operation: "create transaction parent",
                path: parent.to_path_buf(),
                source,
            })?;
            let temporary = path.with_extension(format!("cott-{}", std::process::id()));
            reject_symlink(&temporary)?;
            let mut file = OpenOptions::new()
                .create_new(true)
                .write(true)
                .open(&temporary)
                .map_err(|source| TransactionError::Io {
                    operation: "write transaction post-image",
                    path: temporary.clone(),
                    source,
                })?;
            file.write_all(bytes)
                .and_then(|_| file.sync_all())
                .map_err(|source| TransactionError::Io {
                    operation: "sync transaction post-image",
                    path: temporary.clone(),
                    source,
                })?;
            fs::rename(&temporary, &path).map_err(|source| TransactionError::Io {
                operation: "rename transaction post-image",
                path: path.clone(),
                source,
            })?;
            sync_directory(parent)?;
        }
        None => match fs::remove_file(&path) {
            Ok(()) => {
                if let Some(parent) = path.parent() {
                    sync_directory(parent)?;
                }
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
    let mut file = OpenOptions::new()
        .create(true)
        .truncate(true)
        .write(true)
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
    fs::rename(&temporary, &path).map_err(|source| TransactionError::Io {
        operation: "publish transaction journal",
        path: path.clone(),
        source,
    })?;
    sync_directory(directory)
}

fn file_hash(path: &Path) -> Result<Option<String>, TransactionError> {
    reject_symlink(path)?;
    match fs::read(path) {
        Ok(bytes) => Ok(Some(sha256_hex(&bytes))),
        Err(source) if source.kind() == io::ErrorKind::NotFound => Ok(None),
        Err(source) => Err(TransactionError::Io {
            operation: "hash transaction input",
            path: path.to_path_buf(),
            source,
        }),
    }
}

fn validate_relative(path: &Path) -> Result<(), TransactionError> {
    if path.as_os_str().is_empty()
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

fn reject_symlink(path: &Path) -> Result<(), TransactionError> {
    match fs::symlink_metadata(path) {
        Ok(metadata) if metadata.file_type().is_symlink() => {
            Err(TransactionError::UnsafePath(path.to_path_buf()))
        }
        Ok(_) | Err(_) => Ok(()),
    }
}

fn ensure_directory(path: &Path) -> Result<(), TransactionError> {
    reject_symlink(path)?;
    match fs::metadata(path) {
        Ok(metadata) if metadata.is_dir() => Ok(()),
        Ok(_) => Err(TransactionError::UnsafePath(path.to_path_buf())),
        Err(source) => Err(TransactionError::Io {
            operation: "stat transaction directory",
            path: path.to_path_buf(),
            source,
        }),
    }
}

fn ensure_or_create_directory(path: &Path) -> Result<(), TransactionError> {
    match fs::metadata(path) {
        Ok(metadata) if metadata.is_dir() => reject_symlink(path),
        Ok(_) => Err(TransactionError::UnsafePath(path.to_path_buf())),
        Err(source) if source.kind() == io::ErrorKind::NotFound => {
            fs::create_dir(path).map_err(|source| TransactionError::Io {
                operation: "create transaction directory",
                path: path.to_path_buf(),
                source,
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
