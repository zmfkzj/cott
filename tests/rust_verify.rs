use cott::sandbox::{BindMounts, NetworkAccess, ResourceLimits, SandboxSpec};
use std::{collections::BTreeMap, fs, path::PathBuf, process::Command};
const EVIDENCE_KEY_BYTES: usize = 32;
#[path = "../src/rust/runner_wire.rs"]
mod wire;

#[test]
#[ignore = "requires COTT_CARGO, bubblewrap, systemd user scope, and Landlock ABI >=3"]
fn native_launcher_confines_process_files_network_and_exec_and_drains_secret_pipe() {
    let cargo = PathBuf::from(std::env::var_os("COTT_CARGO").expect("COTT_CARGO"));
    assert!(cargo.is_absolute());
    let rustc = std::env::var_os("COTT_RUSTC")
        .map(PathBuf::from)
        .unwrap_or_else(|| cargo.parent().unwrap().join("rustc"));
    let root = std::env::temp_dir().join(format!("cott-rust-confinement-{}", std::process::id()));
    fs::create_dir(&root).unwrap();
    struct Cleanup(PathBuf);
    impl Drop for Cleanup {
        fn drop(&mut self) {
            let _ = fs::remove_dir_all(&self.0);
        }
    }
    let _cleanup = Cleanup(root.clone());
    let work = root.join("runtime");
    fs::create_dir(&work).unwrap();
    fs::write(
        root.join("evidence.rs"),
        include_bytes!("../src/rust/runner_support.rs"),
    )
    .unwrap();
    fs::write(
        root.join("confinement.rs"),
        include_bytes!("../src/rust/runner_confinement_support.rs"),
    )
    .unwrap();
    let listener = std::net::TcpListener::bind((std::net::Ipv4Addr::LOCALHOST, 0)).unwrap();
    let host_port = listener.local_addr().unwrap().port();
    let source = format!(
        r#"#![deny(unsafe_code)]
#[allow(dead_code)] mod evidence;
#[allow(unsafe_code)] mod confinement;
use std::io::Read;
fn main() {{
    confinement::install().unwrap();
    let mut writer=evidence::EvidenceWriter::from_stdin().unwrap();
    let mut leftover=Vec::new();std::io::stdin().read_to_end(&mut leftover).unwrap();assert!(leftover.is_empty());
    for path in ["/proc/self/mem","/proc/thread-self/mem","/proc/self/environ","/proc/self/cmdline","/proc/self/maps"] {{assert!(std::fs::read(path).is_err(),"procfs opened: {{path}}");}}
    assert!(std::fs::write("/tmp/forbidden-cott-escape",b"escape").is_err());
    let allowed=std::env::current_dir().unwrap().join("allowed.txt");std::fs::write(&allowed,b"scratch").unwrap();assert_eq!(std::fs::read(&allowed).unwrap(),b"scratch");
    assert!(std::process::Command::new("/usr/bin/true").status().is_err(),"child executable escaped confinement");
    assert!(std::process::Command::new("/lib64/ld-linux-x86-64.so.2").arg("/usr/bin/true").status().is_err(),"direct ELF loader escaped seccomp");
    assert_eq!(std::thread::spawn(|| 37).join().unwrap(),37,"thread creation must remain available");
    let address=std::net::SocketAddr::from(([127,0,0,1],{host_port}));assert!(std::net::TcpStream::connect_timeout(&address,std::time::Duration::from_millis(100)).is_err(),"host loopback escaped network namespace");
    writer.event("{{\"kind\":\"done\"}}").unwrap();
}}
"#
    );
    fs::write(root.join("probe.rs"), source).unwrap();
    let binary = root.join("probe");
    let compiled = Command::new(rustc)
        .args(["--edition", "2024", "-D", "warnings"])
        .arg(root.join("probe.rs"))
        .arg("-o")
        .arg(&binary)
        .output()
        .unwrap();
    assert!(
        compiled.status.success(),
        "{}",
        String::from_utf8_lossy(&compiled.stderr)
    );
    let launcher = fs::canonicalize(env!("CARGO_BIN_EXE_cott")).unwrap();
    let specification = cott::sandbox::landlock::ConfinedExec {
        executable: binary.clone(),
        arguments: vec![],
        read_only: vec![binary.clone()],
        writable: vec![work.clone()],
    };
    let key = [0x7b; 32];
    let completed = cott::sandbox::run(&SandboxSpec {
        program: launcher.clone(),
        arguments: vec![
            cott::sandbox::landlock::RUST_EXEC_MODE.into(),
            serde_json::to_string(&specification).unwrap(),
        ],
        cwd: work.clone(),
        environment: BTreeMap::from([
            ("HOME".into(), work.to_string_lossy().into_owned()),
            ("PATH".into(), "/usr/bin:/bin".into()),
            ("LC_ALL".into(), "C.UTF-8".into()),
        ]),
        stdin: key.to_vec(),
        binds: BindMounts {
            read_only: vec![launcher, binary],
            writable: vec![work],
        },
        network: NetworkAccess::Disabled,
        limits: ResourceLimits::contract_test(),
    })
    .unwrap();
    assert_eq!(
        completed.status,
        Some(0),
        "stdout={} stderr={} resources={}",
        String::from_utf8_lossy(&completed.stdout),
        String::from_utf8_lossy(&completed.stderr),
        completed.resources
    );
    assert!(!completed.timed_out);
    assert_eq!(
        wire::parse_events(&completed.stdout, &key).unwrap(),
        vec![serde_json::json!({"kind":"done"})]
    );
    let tampered = String::from_utf8(completed.stdout)
        .unwrap()
        .replace("done", "case");
    assert!(wire::parse_events(tampered.as_bytes(), &key).is_err());
}
