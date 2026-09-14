//! Internal, single-threaded filesystem confinement before launching a target VM.
//!
//! Bubblewrap remains responsible for mounts, namespaces, network and resource
//! limits. Landlock additionally denies process-memory files in its live procfs;
//! Dart needs its own maps file during VM startup, not the rest of procfs.

use std::ffi::OsString;
use std::path::PathBuf;

use serde::{Deserialize, Serialize};

pub const EXEC_MODE: &str = "__cott_landlock_exec";

#[derive(Debug, Deserialize, Serialize)]
#[serde(deny_unknown_fields)]
pub struct ConfinedExec {
    pub executable: PathBuf,
    pub arguments: Vec<String>,
    pub read_only: Vec<PathBuf>,
    pub writable: Vec<PathBuf>,
}

/// Recognizes only the compiler's internal launch protocol. It never consumes
/// stdin: the child VM must receive the original one-way evidence-key pipe.
pub fn dispatch(arguments: &[OsString]) -> Option<i32> {
    if arguments
        .get(1)
        .is_none_or(|argument| argument != EXEC_MODE)
    {
        return None;
    }
    let result = (|| {
        if arguments.len() != 3 {
            return Err("invalid confined target launch arguments".to_owned());
        }
        let json = arguments[2]
            .to_str()
            .ok_or("confined target launch specification is not UTF-8")?;
        let spec: ConfinedExec = serde_json::from_str(json)
            .map_err(|error| format!("invalid confined target specification: {error}"))?;
        execute(&spec)
    })();
    match result {
        Ok(never) => match never {},
        Err(error) => {
            eprintln!("error: Dart filesystem confinement: {error}");
            Some(126)
        }
    }
}

#[cfg(not(target_os = "linux"))]
fn execute(_: &ConfinedExec) -> Result<std::convert::Infallible, String> {
    Err("Linux Landlock ABI >=3 is required".to_owned())
}

#[cfg(target_os = "linux")]
fn execute(spec: &ConfinedExec) -> Result<std::convert::Infallible, String> {
    use std::collections::BTreeMap;
    use std::fs::{self, OpenOptions};
    use std::io;
    use std::os::fd::{AsRawFd, FromRawFd, OwnedFd};
    use std::os::unix::fs::OpenOptionsExt;
    use std::os::unix::process::CommandExt;
    use std::path::{Component, Path};
    use std::process::Command;

    const EXECUTE: u64 = 1 << 0;
    const WRITE_FILE: u64 = 1 << 1;
    const READ_FILE: u64 = 1 << 2;
    const READ_DIR: u64 = 1 << 3;
    const TRUNCATE: u64 = 1 << 14;
    const ALL_FILESYSTEM: u64 = (1 << 15) - 1;
    const READ_ONLY: u64 = EXECUTE | READ_FILE | READ_DIR;
    const REGULAR_FILE: u64 = EXECUTE | WRITE_FILE | READ_FILE | TRUNCATE;

    #[repr(C)]
    struct RulesetAttr {
        handled_access_fs: u64,
    }
    #[repr(C, packed)]
    struct PathBeneathAttr {
        allowed_access: u64,
        parent_fd: libc::c_int,
    }

    let tasks = fs::read_dir("/proc/self/task")
        .map_err(|error| format!("inspect launcher threads: {error}"))?
        .collect::<Result<Vec<_>, _>>()
        .map_err(|error| format!("inspect launcher thread: {error}"))?;
    if tasks.len() != 1 {
        return Err("target confinement must precede VM threads".to_owned());
    }
    let abi = unsafe {
        libc::syscall(
            libc::SYS_landlock_create_ruleset,
            std::ptr::null::<RulesetAttr>(),
            0usize,
            1u32,
        )
    };
    if abi < 3 {
        return Err(format!(
            "Landlock ABI >=3 is required (reported {abi}: {})",
            io::Error::last_os_error()
        ));
    }
    let attr = RulesetAttr {
        handled_access_fs: ALL_FILESYSTEM,
    };
    let descriptor = unsafe {
        libc::syscall(
            libc::SYS_landlock_create_ruleset,
            &attr,
            std::mem::size_of::<RulesetAttr>(),
            0u32,
        )
    };
    if descriptor < 0 {
        return Err(format!("create ruleset: {}", io::Error::last_os_error()));
    }
    let ruleset = unsafe { OwnedFd::from_raw_fd(descriptor as libc::c_int) };
    let mut rules = BTreeMap::<PathBuf, u64>::new();
    let mut add_path = |path: &Path, access: u64| -> Result<(), String> {
        if !path.is_absolute()
            || path
                .components()
                .any(|component| matches!(component, Component::ParentDir))
        {
            return Err(format!(
                "confinement path is not absolute and normalized: {}",
                path.display()
            ));
        }
        let path = fs::canonicalize(path)
            .map_err(|error| format!("resolve confinement path {}: {error}", path.display()))?;
        if path == Path::new("/") || path.starts_with("/proc") || path.starts_with("/sys") {
            return Err(format!("unsafe confinement root: {}", path.display()));
        }
        *rules.entry(path).or_default() |= access;
        Ok(())
    };
    for path in ["/usr", "/lib", "/lib64", "/etc"] {
        if Path::new(path).exists() {
            add_path(Path::new(path), READ_ONLY)?;
        }
    }
    add_path(&spec.executable, READ_ONLY)?;
    for path in &spec.read_only {
        add_path(path, READ_ONLY)?;
    }
    for path in &spec.writable {
        add_path(path, ALL_FILESYSTEM)?;
    }
    for path in ["/dev/null", "/dev/zero", "/dev/random", "/dev/urandom"] {
        if Path::new(path).exists() {
            add_path(Path::new(path), READ_FILE | WRITE_FILE)?;
        }
    }
    // This inode remains attached to the same process across exec. No ancestor
    // procfs directory or task/fd/mem file receives an allow rule.
    rules.insert(PathBuf::from("/proc/self/maps"), READ_FILE);
    for (path, requested) in rules {
        let file = OpenOptions::new()
            .read(true)
            .custom_flags(libc::O_PATH | libc::O_CLOEXEC)
            .open(&path)
            .map_err(|error| format!("open confinement rule {}: {error}", path.display()))?;
        let metadata = file
            .metadata()
            .map_err(|error| format!("inspect confinement rule {}: {error}", path.display()))?;
        let allowed_access = if metadata.is_dir() {
            requested
        } else {
            requested & REGULAR_FILE
        };
        let rule = PathBeneathAttr {
            allowed_access,
            parent_fd: file.as_raw_fd(),
        };
        let status = unsafe {
            libc::syscall(
                libc::SYS_landlock_add_rule,
                ruleset.as_raw_fd(),
                1u32,
                &rule,
                0u32,
            )
        };
        if status != 0 {
            return Err(format!(
                "add confinement rule {}: {}",
                path.display(),
                io::Error::last_os_error()
            ));
        }
    }
    if unsafe { libc::prctl(libc::PR_SET_NO_NEW_PRIVS, 1, 0, 0, 0) } != 0 {
        return Err(format!(
            "set no-new-privileges: {}",
            io::Error::last_os_error()
        ));
    }
    if unsafe { libc::syscall(libc::SYS_landlock_restrict_self, ruleset.as_raw_fd(), 0u32) } != 0 {
        return Err(format!("enforce ruleset: {}", io::Error::last_os_error()));
    }
    drop(ruleset);
    let error = Command::new(&spec.executable).args(&spec.arguments).exec();
    Err(format!(
        "execute confined target {}: {error}",
        spec.executable.display()
    ))
}
