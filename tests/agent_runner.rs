use std::fs;
use std::path::PathBuf;
use std::sync::atomic::{AtomicU64, Ordering};

use cott::agent::{AgentKind, run_agent};

static NEXT: AtomicU64 = AtomicU64::new(0);

struct Temp {
    root: PathBuf,
}
impl Temp {
    fn new() -> Self {
        let root = std::env::temp_dir().join(format!(
            "cott-agent-test-{}-{}",
            std::process::id(),
            NEXT.fetch_add(1, Ordering::Relaxed)
        ));
        fs::create_dir(&root).expect("create temporary root");
        Self { root }
    }
}
impl Drop for Temp {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.root);
    }
}

#[test]
fn omp_adapter_accepts_only_the_written_target_file() {
    let temp = Temp::new();
    let workspace = temp.root.join("workspace");
    let scratch = temp.root.join("scratch");
    fs::create_dir(&workspace).expect("workspace");
    fs::create_dir(&scratch).expect("scratch");
    let executable = workspace.join("omp");
    fs::write(&executable, "#!/bin/sh\nif [ \"$1\" = \"--version\" ]; then echo omp/17.2.12; exit 0; fi\nprintf 'def run() -> int:\\n    return 7\\n' > implementation.py\n")
        .expect("write fake OMP");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&executable, fs::Permissions::from_mode(0o755))
            .expect("make fake OMP executable");
    }
    let target = workspace.join("implementation.py");
    let candidate = run_agent(
        AgentKind::Omp,
        executable,
        &workspace,
        &scratch,
        &target,
        b"implement\n".to_vec(),
        10,
    )
    .expect("agent run");
    assert_eq!(candidate.adapter_version, "17.2.12");
    assert_eq!(
        candidate.implementation,
        b"def run() -> int:\n    return 7\n"
    );
}
