use std::fs;
use std::path::PathBuf;
use std::sync::atomic::{AtomicU64, Ordering};

use cott::transaction::{ChangeSet, InputSnapshot, Operation, ProjectSession};

static NEXT: AtomicU64 = AtomicU64::new(0);

struct Temp {
    path: PathBuf,
}
impl Temp {
    fn new() -> Self {
        let path = std::env::temp_dir().join(format!(
            "cott-transaction-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir(&path).unwrap_or_else(|error| panic!("create temp: {error}"));
        Self { path }
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.path);
    }
}

#[test]
fn atomically_applies_a_snapshot_checked_change_set() {
    let temp = Temp::new();
    fs::write(temp.path.join("input"), "before\n").expect("write input");
    let snapshot = InputSnapshot::capture(&temp.path, [PathBuf::from("input")]).expect("snapshot");
    let session = ProjectSession::acquire(&temp.path).expect("session");
    session
        .apply(
            &snapshot,
            &ChangeSet {
                operations: vec![
                    Operation::Write {
                        path: PathBuf::from("input"),
                        bytes: b"after\n".to_vec(),
                    },
                    Operation::Write {
                        path: PathBuf::from("generated/value"),
                        bytes: b"value\n".to_vec(),
                    },
                ],
                generation_record_last: false,
            },
        )
        .expect("apply");
    assert_eq!(
        fs::read_to_string(temp.path.join("input")).expect("read input"),
        "after\n"
    );
    assert_eq!(
        fs::read_to_string(temp.path.join("generated/value")).expect("read value"),
        "value\n"
    );
    assert!(
        fs::read_dir(temp.path.join(".cott/transactions"))
            .expect("journals")
            .next()
            .is_none()
    );
}

#[test]
fn rejects_snapshot_drift_before_writing() {
    let temp = Temp::new();
    fs::write(temp.path.join("input"), "before\n").expect("write input");
    let snapshot = InputSnapshot::capture(&temp.path, [PathBuf::from("input")]).expect("snapshot");
    fs::write(temp.path.join("input"), "changed\n").expect("drift");
    let session = ProjectSession::acquire(&temp.path).expect("session");
    assert!(
        session
            .apply(
                &snapshot,
                &ChangeSet {
                    operations: vec![Operation::Write {
                        path: PathBuf::from("output"),
                        bytes: b"no\n".to_vec()
                    }],
                    generation_record_last: false
                }
            )
            .is_err()
    );
    assert!(!temp.path.join("output").exists());
}

#[test]
fn rejects_hard_linked_inputs_and_lock_files() {
    let temp = Temp::new();
    fs::write(temp.path.join("input"), b"value\n").expect("input");
    fs::hard_link(temp.path.join("input"), temp.path.join("alias")).expect("hard link");
    assert!(
        InputSnapshot::capture(&temp.path, [PathBuf::from("input")]).is_err(),
        "multiply linked input must be rejected"
    );

    fs::remove_file(temp.path.join("alias")).expect("remove alias");
    drop(ProjectSession::acquire(&temp.path).expect("initial session"));
    fs::hard_link(
        temp.path.join(".cott/lock"),
        temp.path.join(".cott/lock-alias"),
    )
    .expect("lock hard link");
    assert!(
        ProjectSession::acquire(&temp.path).is_err(),
        "multiply linked lock must be rejected"
    );
}

#[test]
fn rejects_symlinked_path_components() {
    let temp = Temp::new();
    fs::create_dir(temp.path.join("real")).expect("real directory");
    fs::write(temp.path.join("real/input"), b"value\n").expect("input");
    std::os::unix::fs::symlink("real", temp.path.join("linked")).expect("directory symlink");
    assert!(
        InputSnapshot::capture(&temp.path, [PathBuf::from("linked/input")]).is_err(),
        "symlinked parent must be rejected"
    );
}

#[test]
fn corrupt_or_multiple_journals_are_preserved_for_manual_recovery() {
    let temp = Temp::new();
    drop(ProjectSession::acquire(&temp.path).expect("initial session"));
    let transactions = temp.path.join(".cott/transactions");
    let first = transactions.join("first");
    fs::create_dir(&first).expect("first journal");
    fs::write(first.join("journal.json"), b"not json\n").expect("corrupt journal");
    let bytes = fs::read(first.join("journal.json")).expect("journal bytes");
    assert!(ProjectSession::acquire(&temp.path).is_err());
    assert_eq!(
        fs::read(first.join("journal.json")).expect("preserved journal"),
        bytes
    );

    fs::remove_dir_all(&first).expect("remove corrupt fixture");
    fs::create_dir(transactions.join("one")).expect("journal one");
    fs::create_dir(transactions.join("two")).expect("journal two");
    assert!(ProjectSession::acquire(&temp.path).is_err());
    assert!(transactions.join("one").exists());
    assert!(transactions.join("two").exists());
}
