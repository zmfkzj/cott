use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::sync::atomic::{AtomicU64, Ordering};

static NEXT_TEMP_DIR: AtomicU64 = AtomicU64::new(0);

const EXAMPLES: &[(&str, &str, &str)] = &[
    (
        "grammar/boolean-identity",
        "curriculum.boolean_identity",
        "True\n",
    ),
    (
        "grammar/signed-addition",
        "curriculum.signed_addition",
        "5\n",
    ),
    (
        "grammar/positive-counter",
        "curriculum.positive_counter",
        "PositiveCount(value=3)\n",
    ),
    (
        "grammar/named-timestamp",
        "curriculum.named_timestamp",
        "7\n",
    ),
    (
        "grammar/record-echo",
        "curriculum.record_echo",
        "Message(text='hello', sequence=7)\n",
    ),
    (
        "grammar/priority-selection",
        "curriculum.priority_selection",
        "High()\n",
    ),
    (
        "grammar/optional-label",
        "curriculum.optional_label",
        "Some(value='enabled')\n",
    ),
    (
        "grammar/result-division-guard",
        "curriculum.result_division_guard",
        "Err(error=ZeroDivisor())\n",
    ),
    ("grammar/unit-echo", "curriculum.unit_echo", "UNIT\n"),
    (
        "grammar/constant-greeting",
        "curriculum.constant_greeting",
        "hello\n",
    ),
    (
        "simple/normalize-flag",
        "curriculum.normalize_flag",
        "True\n",
    ),
    ("simple/clamp-score", "curriculum.clamp_score", "0.75\n"),
    (
        "simple/increment-count",
        "curriculum.increment_count",
        "42\n",
    ),
    (
        "simple/greeting-length",
        "curriculum.greeting_length",
        "4\n",
    ),
    (
        "simple/byte-count",
        "curriculum.byte_count",
        "ByteCount(data=b'abc', count=3)\n",
    ),
    (
        "simple/nonempty-name",
        "curriculum.nonempty_name",
        "NonemptyName(value='Ada')\n",
    ),
    (
        "simple/default-nickname",
        "curriculum.default_nickname",
        "Nothing()\n",
    ),
    (
        "simple/parity-classification",
        "curriculum.parity_classification",
        "Odd()\n",
    ),
    (
        "simple/checked-subtract",
        "curriculum.checked_subtract",
        "Ok(value=5)\n",
    ),
    (
        "simple/message-sequence",
        "curriculum.message_sequence",
        "Message(text='x', sequence=5)\n",
    ),
    (
        "complex/validated-user-card",
        "curriculum.validated_user_card",
        "Ok(value=UserCard(id=UserId(value=7), name=UserName(value='Ada')))\n",
    ),
    (
        "complex/retry-configuration",
        "curriculum.retry_configuration",
        "RetryConfiguration(attempts=RetryCount(value=3), backoff_ms=250)\n",
    ),
    (
        "complex/order-state-transition",
        "curriculum.order_state_transition",
        "Ok(value=Paid(receipt='r1'))\n",
    ),
    (
        "complex/profile-summary",
        "curriculum.profile_summary",
        "ProfileSummary(display_name='Ada', tag_count=2, has_nickname=True)\n",
    ),
    (
        "complex/transfer-decision",
        "curriculum.transfer_decision",
        "Ok(value=Accepted())\n",
    ),
    (
        "complex/address-validation",
        "curriculum.address_validation",
        "Ok(value=Address(line1='1 Main St', city='Seoul', postal_code='12345'))\n",
    ),
    (
        "complex/contact-preference",
        "curriculum.contact_preference",
        "Email()\n",
    ),
    (
        "complex/subscription-activation",
        "curriculum.subscription_activation",
        "Ok(value=Subscription(id=SubscriptionId(value=42), active=True))\n",
    ),
    (
        "complex/invoice-decision",
        "curriculum.invoice_decision",
        "Rejected(reason='missing tax id')\n",
    ),
    (
        "complex/access-grant",
        "curriculum.access_grant",
        "Ok(value=Granted())\n",
    ),
];

struct TempDir {
    path: PathBuf,
}

impl TempDir {
    fn new() -> Self {
        let mut number = NEXT_TEMP_DIR.fetch_add(1, Ordering::Relaxed);
        loop {
            let path = std::env::temp_dir().join(format!(
                "cott-example-tests-{}-{number}",
                std::process::id()
            ));
            match fs::create_dir(&path) {
                Ok(()) => return Self { path },
                Err(error) if error.kind() == io::ErrorKind::AlreadyExists => number += 1,
                Err(error) => panic!("failed to create temporary directory: {error}"),
            }
        }
    }
}

impl Drop for TempDir {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.path);
    }
}

fn copied_project(example: &str) -> TempDir {
    let temp = TempDir::new();
    let source = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("examples")
        .join(example);
    copy_tree(&source, &temp.path);
    temp
}

fn copy_tree(source: &Path, destination: &Path) {
    fs::create_dir_all(destination).expect("destination should be creatable");
    let entries = fs::read_dir(source).expect("example directory should be readable");
    for entry in entries {
        let entry = entry.expect("example directory entry should be readable");
        let source_path = entry.path();
        let destination_path = destination.join(entry.file_name());
        let metadata =
            fs::symlink_metadata(&source_path).expect("example metadata should be readable");
        if metadata.is_dir() {
            copy_tree(&source_path, &destination_path);
        } else if metadata.is_file() {
            fs::copy(&source_path, &destination_path).expect("example file should be copyable");
        } else {
            panic!(
                "example contains unsupported filesystem entry: {}",
                source_path.display()
            );
        }
    }
}

fn cott(root: &Path, arguments: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_cott"))
        .args(arguments)
        .arg("--project")
        .arg(root)
        .output()
        .expect("cott should run")
}

#[test]
fn every_documented_example_emits_and_verifies() {
    for (example, _, _) in EXAMPLES {
        let project = copied_project(example);
        let emitted = cott(&project.path, &["emit", "python"]);
        assert!(
            emitted.status.success(),
            "{example} failed to emit: {}",
            String::from_utf8_lossy(&emitted.stderr)
        );
        let verified = cott(&project.path, &["verify"]);
        assert!(
            verified.status.success(),
            "{example} failed to verify: {}",
            String::from_utf8_lossy(&verified.stderr)
        );
    }
}

#[test]
fn every_documented_example_runs_when_python3_is_available() {
    let usable_python = Command::new("python3")
        .args([
            "-c",
            "import sys; raise SystemExit(sys.version_info < (3, 10))",
        ])
        .status()
        .is_ok_and(|status| status.success());
    if !usable_python {
        return;
    }

    for (example, module, expected_stdout) in EXAMPLES {
        let project = copied_project(example);
        let emitted = cott(&project.path, &["emit", "python"]);
        assert!(
            emitted.status.success(),
            "{example} failed to emit: {}",
            String::from_utf8_lossy(&emitted.stderr)
        );
        let output = Command::new("python3")
            .args([
                "-c",
                &format!("import importlib; print(importlib.import_module('{module}').run())"),
            ])
            .current_dir(project.path.join("generated/python"))
            .output()
            .expect("generated example should run");
        assert!(
            output.status.success(),
            "{example} failed to run: {}",
            String::from_utf8_lossy(&output.stderr)
        );
        assert_eq!(
            String::from_utf8(output.stdout).expect("example stdout must be UTF-8"),
            *expected_stdout,
            "{example} emitted unexpected stdout"
        );
        let verified = cott(&project.path, &["verify"]);
        assert!(
            verified.status.success(),
            "{example} failed to verify after execution: {}",
            String::from_utf8_lossy(&verified.stderr)
        );
    }
}
