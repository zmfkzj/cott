//! Compiler-owned component fixture, not an emitted/verified project or a facade.
use std::fs;
use std::path::PathBuf;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = std::env::args_os().skip(1);
    let output = PathBuf::from(
        args.next()
            .ok_or("usage: benchmark-runtime <new-directory>")?,
    );
    if args.next().is_some() {
        return Err("usage: benchmark-runtime <new-directory>".into());
    }
    // Never overwrite an existing runtime, project, or somebody else's measurements.
    fs::create_dir(&output)?;
    let executable = std::env::current_exe()?;
    let identity = serde_json::json!({
        "scope": "compiler-rendered component fixture; not a verified project",
        "compiler_version": env!("CARGO_PKG_VERSION"),
        "exporter_sha256": cott::hash::sha256_hex(&fs::read(executable)?),
        "runtime_source_sha256": cott::hash::sha256_hex(include_bytes!("../src/python_runtime.rs")),
    });
    fs::write(
        output.join("benchmark-export.json"),
        serde_json::to_vec_pretty(&identity)?,
    )?;
    for (relative, bytes) in cott::python_runtime::render_runtime("boundary-benchmark", "0.1.0") {
        let path = output.join(relative);
        fs::create_dir_all(path.parent().ok_or("missing parent")?)?;
        fs::write(path, bytes)?;
    }
    Ok(())
}
