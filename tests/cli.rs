use std::collections::BTreeMap;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::sync::atomic::{AtomicU64, Ordering};

static NEXT_TEMP_DIR: AtomicU64 = AtomicU64::new(0);

struct TempDir {
    path: PathBuf,
}

impl TempDir {
    fn new() -> Self {
        let mut number = NEXT_TEMP_DIR.fetch_add(1, Ordering::Relaxed);
        loop {
            let path = std::env::temp_dir()
                .join(format!("cott-cli-tests-{}-{number}", std::process::id()));
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

fn file_snapshot(root: &Path) -> BTreeMap<PathBuf, Vec<u8>> {
    fn visit(root: &Path, current: &Path, files: &mut BTreeMap<PathBuf, Vec<u8>>) {
        for entry in fs::read_dir(current).expect("snapshot directory should be readable") {
            let entry = entry.expect("snapshot entry should be readable");
            let path = entry.path();
            let relative = path
                .strip_prefix(root)
                .expect("snapshot path should be rooted")
                .to_path_buf();
            if entry
                .file_type()
                .expect("snapshot entry type should be readable")
                .is_dir()
            {
                visit(root, &path, files);
            } else {
                files.insert(
                    relative,
                    fs::read(&path).expect("snapshot file should be readable"),
                );
            }
        }
    }

    let mut files = BTreeMap::new();
    visit(root, root, &mut files);
    files
}

fn install_fake_python_tools(root: &Path) {
    let bin = root.join(".venv/bin");
    fs::create_dir_all(&bin).expect("fake Python tool directory");
    let python = bin.join("python");
    fs::write(
        &python,
        r#"#!/bin/sh
if [ "$1" = "-c" ]; then
  case "$2" in
    *"sysconfig; print(json.dumps"*)
      printf '%s\n' '{"cache_tag":"cpython-314","implementation":"cpython","machine":"x86_64","os":"linux","platform":"linux-x86_64","version":"3.14.6"}'
      exit 0
      ;;
  esac
fi
exec /usr/bin/python3 "$@"
"#,
    )
    .expect("fake Python interpreter");
    let checker = bin.join("basedpyright");
    fs::write(
        &checker,
        "#!/bin/sh\n[ \"$1\" = \"--version\" ] && printf 'basedpyright 1.39.9\\nbased on pyright 1.1.411\\n'\nexit 0\n",
    )
    .expect("fake BasedPyright");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        for executable in [python, checker] {
            fs::set_permissions(executable, fs::Permissions::from_mode(0o755))
                .expect("make fake Python tool executable");
        }
    }
}

const NORMATIVE_MANIFEST: &str = r#"[project]
name = "demo"
version = "0.1.0"
source = "src"

[target.python]
source = "python"
generated = "generated/python"
stubs = "generated/stubs"
interpreter = ".venv/bin/python"
type_checker = ".venv/bin/basedpyright"
runtime_validation = "boundary"

[target.python.implementations]
"app.run" = "cott_bindings.app.run:run"
"#;
const SOURCE: &str = "module app\n\nfn run() -> I32\n";
const BINDING: &str = "from cott_runtime import I32\n\n\ndef run() -> I32:\n    return 7\n";
const TARGET_METADATA: &str = "[project]\nname = \"demo\"\nversion = \"0.1.0\"\nrequires-python = \">=3.14,<3.15\"\ndependencies = []\n";

fn write_target_metadata(root: &Path) {
    fs::create_dir_all(root.join("python")).expect("Python source directory");
    fs::write(root.join("python/pyproject.toml"), TARGET_METADATA)
        .expect("target project metadata should be writable");
}

fn project() -> TempDir {
    let temp = TempDir::new();
    fs::write(temp.path.join("cott.toml"), NORMATIVE_MANIFEST)
        .expect("manifest should be writable");
    fs::create_dir_all(temp.path.join("src")).expect("source directory should be writable");
    fs::write(temp.path.join("src/app.cott"), SOURCE).expect("source should be writable");
    write_target_metadata(&temp.path);
    fs::create_dir_all(temp.path.join("python/cott_bindings/app"))
        .expect("implementation directory should be writable");
    fs::write(temp.path.join("python/cott_bindings/app/run.py"), BINDING)
        .expect("binding should be writable");
    install_fake_python_tools(&temp.path);
    temp
}

fn make_unresolved(project: &TempDir) {
    fs::remove_file(project.path.join("python/cott_bindings/app/run.py"))
        .expect("binding should be removable");
    let manifest = fs::read_to_string(project.path.join("cott.toml")).expect("manifest");
    let manifest = manifest
        .split_once("\n[target.python.implementations]\n")
        .map_or(manifest.as_str(), |(base, _)| base);
    fs::write(project.path.join("cott.toml"), format!("{manifest}\n"))
        .expect("unresolved manifest should be writable");
}

fn method_project() -> TempDir {
    let temp = TempDir::new();
    let manifest = NORMATIVE_MANIFEST
        .split_once("\n[target.python.implementations]\n")
        .expect("normative manifest has implementations")
        .0;
    fs::write(temp.path.join("cott.toml"), format!("{manifest}\n"))
        .expect("manifest should be writable");
    fs::create_dir_all(temp.path.join("src/api")).expect("source directory should be writable");
    fs::write(
        temp.path.join("src/api/service.cott"),
        "module api.service\n\ntrait Reader:\n    fn read(self, amount: I32) -> I32\n\nimpl ReaderState for Reader:\n    state:\n        count: I32 = 0\n    init(count: I32):\n        requires count > 0\n        ensures self.count == count\n    fn read(self, amount: I32) -> I32:\n        ensures result == amount\n",
    )
    .expect("method source should be writable");
    write_target_metadata(&temp.path);
    install_fake_python_tools(&temp.path);
    temp
}

fn normative_project() -> TempDir {
    let temp = TempDir::new();
    fs::write(temp.path.join("cott.toml"), NORMATIVE_MANIFEST)
        .expect("manifest should be writable");
    fs::create_dir_all(temp.path.join("src")).expect("source directory should be writable");
    fs::write(temp.path.join("src/app.cott"), SOURCE).expect("source should be writable");
    write_target_metadata(&temp.path);
    temp
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
fn source_commands_accept_the_normative_manifest_without_entry() {
    let project = normative_project();

    for arguments in [
        &["check", "--format", "json"][..],
        &["fmt"][..],
        &["emit", "ir"][..],
    ] {
        let output = cott(&project.path, arguments);
        assert!(
            output.status.success(),
            "{arguments:?}: {}",
            String::from_utf8_lossy(&output.stderr)
        );
    }
    assert!(project.path.join("generated/ir/app.json").is_file());
}

fn retarget_generation_to_host_python(root: &Path) {
    let script = r#"import hashlib,json,pathlib,platform,sys,sysconfig
p=pathlib.Path("generated/generation.json")
r=json.loads(p.read_bytes())
e=pathlib.Path(sys.executable).resolve()
r["current"]["tools"]["python"]={"cache_tag":sys.implementation.cache_tag,"content_hash":"sha256:"+hashlib.sha256(e.read_bytes()).hexdigest(),"executable":str(e),"implementation":sys.implementation.name,"machine":platform.machine(),"os":sys.platform,"platform":sysconfig.get_platform(),"version":platform.python_version()}
i=dict(r["current"])
for k in ("generation_id","verified","verification","agent_runs"): i.pop(k,None)
r["current"]["generation_id"]="sha256:"+hashlib.sha256(json.dumps(i,ensure_ascii=False,separators=(",",":"),sort_keys=True).encode()+b"\n").hexdigest()
p.write_text(json.dumps(r,ensure_ascii=False,separators=(",",":"),sort_keys=True)+"\n")
"#;
    let output = Command::new("python3")
        .args(["-c", script])
        .current_dir(root)
        .output()
        .expect("host Python should retarget test provenance");
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
}

fn remove_free_function_callable_metadata(root: &Path) {
    let script = r#"import hashlib,json,pathlib
p=pathlib.Path("generated/generation.json")
r=json.loads(p.read_bytes())
i=r["current"]["implementations"][0]
for k in ("kind","concrete","method"): i.pop(k)
c=dict(r["current"])
for k in ("generation_id","verified","verification","agent_runs"): c.pop(k,None)
r["current"]["generation_id"]="sha256:"+hashlib.sha256(json.dumps(c,ensure_ascii=False,separators=(",",":"),sort_keys=True).encode()+b"\n").hexdigest()
p.write_text(json.dumps(r,ensure_ascii=False,separators=(",",":"),sort_keys=True)+"\n")
"#;
    let output = Command::new("python3")
        .args(["-c", script])
        .current_dir(root)
        .output()
        .expect("host Python should write legacy generation provenance");
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
}

#[test]
fn emits_complete_tree_and_verifies_exact_bytes() {
    let project = project();
    let emitted = cott(&project.path, &["emit", "python"]);

    assert!(
        emitted.status.success(),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    assert_eq!(
        String::from_utf8(emitted.stdout).expect("stdout must be UTF-8"),
        "generated/python\n"
    );
    for path in [
        "generated/python/app.py",
        "generated/python/app_types.py",
        "generated/python/cott_runtime/__init__.py",
        "generated/python/_cott_impl/app/run.py",
        "generated/stubs/app.pyi",
        "generated/ir/app.json",
        "generated/generation.json",
    ] {
        assert!(
            project.path.join(path).is_file(),
            "missing generated artifact {path}"
        );
    }
    assert!(!project.path.join("generated/python/__main__.py").exists());

    let verified = cott(&project.path, &["verify"]);
    assert!(
        verified.status.success(),
        "{}",
        String::from_utf8_lossy(&verified.stderr)
    );
    assert_eq!(
        String::from_utf8(verified.stdout).expect("stdout must be UTF-8"),
        "verified generated/python\n"
    );

    fs::write(project.path.join("generated/python/app.py"), "tampered\n")
        .expect("generated artifact should be writable");
    let rejected = cott(&project.path, &["verify"]);
    assert_eq!(rejected.status.code(), Some(4));
    assert!(String::from_utf8_lossy(&rejected.stderr).contains("managed artifact differs"));
}

#[test]
fn verifier_uses_strict_basedpyright_with_compiler_owned_exceptions() {
    let project = project();
    let checker = project.path.join(".venv/bin/basedpyright");
    fs::write(
        &checker,
        r#"#!/bin/sh
if [ "$1" = "--version" ]; then
  printf 'basedpyright 1.39.9\nbased on pyright 1.1.411\n'
  exit 0
fi
config=$(cat "$2")
for setting in '"typeCheckingMode":"strict"' '"reportInvalidTypeVarUse":"none"' '"reportUnknownMemberType":"none"' '"reportUnusedFunction":"none"' '"reportPrivateUsage":"none"'; do
  case "$config" in *"$setting"*) ;; *) printf 'missing BasedPyright setting %s\n' "$setting" >&2; exit 1 ;; esac
done
remaining=$(printf '%s' "$config" | sed 's/"reportInvalidTypeVarUse":"none"//g; s/"reportUnknownMemberType":"none"//g; s/"reportUnusedFunction":"none"//g; s/"reportPrivateUsage":"none"//g')
case "$remaining" in
  *'"report'*':"none"'*)
    printf 'strict BasedPyright diagnostic disabled\n' >&2
    exit 1
    ;;
esac
"#,
    )
    .expect("asserting fake BasedPyright");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&checker, fs::Permissions::from_mode(0o755))
            .expect("make asserting fake BasedPyright executable");
    }

    let emitted = cott(&project.path, &["emit", "python"]);
    assert!(
        emitted.status.success(),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    let verified = cott(&project.path, &["verify"]);
    assert!(
        verified.status.success(),
        "{}",
        String::from_utf8_lossy(&verified.stderr)
    );
}

#[test]
fn emit_rewrites_valid_legacy_free_function_provenance_with_callable_metadata() {
    let project = project();
    let initial = cott(&project.path, &["emit", "python"]);
    assert!(
        initial.status.success(),
        "{}",
        String::from_utf8_lossy(&initial.stderr)
    );
    remove_free_function_callable_metadata(&project.path);

    let legacy: serde_json::Value = serde_json::from_slice(
        &fs::read(project.path.join("generated/generation.json"))
            .expect("legacy generation record"),
    )
    .expect("legacy generation record is JSON");
    let legacy_implementation = &legacy["current"]["implementations"][0];
    assert!(legacy_implementation.get("kind").is_none());
    assert!(legacy_implementation.get("concrete").is_none());
    assert!(legacy_implementation.get("method").is_none());

    let emitted = cott(&project.path, &["emit", "python"]);
    assert!(
        emitted.status.success(),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );

    let rewritten: serde_json::Value = serde_json::from_slice(
        &fs::read(project.path.join("generated/generation.json"))
            .expect("rewritten generation record"),
    )
    .expect("rewritten generation record is JSON");
    let implementation = &rewritten["current"]["implementations"][0];
    assert_eq!(implementation["kind"], "function");
    assert!(implementation["concrete"].is_null());
    assert!(implementation["method"].is_null());
}

#[test]
fn syntax_errors_leave_existing_artifacts_untouched() {
    let project = project();
    fs::create_dir_all(project.path.join("generated/python"))
        .expect("existing artifact directory should be writable");
    let sentinel = project.path.join("generated/sentinel.txt");
    fs::write(&sentinel, "preserve me\n").expect("sentinel should be writable");
    fs::write(project.path.join("src/app.cott"), "module app\n\nfn run(\n")
        .expect("invalid source should be writable");

    let result = cott(&project.path, &["emit", "python"]);

    assert_eq!(result.status.code(), Some(3));
    assert!(String::from_utf8_lossy(&result.stderr).contains("app.cott"));
    assert_eq!(
        fs::read_to_string(sentinel).expect("sentinel should remain"),
        "preserve me\n"
    );
}

#[test]
fn permits_exact_generated_type_imports_in_bindings() {
    let project = project();
    fs::write(
        project.path.join("src/app.cott"),
        "module app\n\nstruct Card:\n    title: Str\n\nfn run() -> Card\n",
    )
    .expect("typed source should be writable");
    fs::write(
        project.path.join("python/cott_bindings/app/run.py"),
        "from app_types import Card\n\n\ndef run() -> Card:\n    return Card(title=\"typed\")\n",
    )
    .expect("typed binding should be writable");

    let emitted = cott(&project.path, &["emit", "python"]);

    assert!(
        emitted.status.success(),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    assert!(project.path.join("generated/python/app_types.py").is_file());
}

#[test]
fn generate_requires_an_agent_only_for_unresolved_callables() {
    let project = project();
    make_unresolved(&project);

    let output = cott(&project.path, &["generate", "--target", "python"]);

    assert_eq!(output.status.code(), Some(2));
    assert!(String::from_utf8_lossy(&output.stderr).contains("requires `--agent codex|omp`"));
}

#[test]
fn generate_promotes_a_sandboxed_omp_function_candidate_with_artifacts() {
    let project = project();
    make_unresolved(&project);
    fs::write(
        project.path.join("cott.toml"),
        format!(
            "{}\n[target.python.external_types]\n\"app.Widget\" = \"io:StringIO\"\n",
            fs::read_to_string(project.path.join("cott.toml")).expect("manifest")
        ),
    )
    .expect("manifest should be writable");
    fs::write(
        project.path.join("src/app.cott"),
        "module app\n\nexternal type Widget\n\nfn run() -> I32\n",
    )
    .expect("source should be writable");
    let tools = project.path.join("tools");
    fs::create_dir(&tools).expect("tool directory");
    let omp = tools.join("omp");
    fs::write(
        &omp,
        r#"#!/bin/sh
if [ "$1" = "--version" ]; then echo omp/17.2.12; exit 0; fi
prompt=
for prompt; do :; done
case "$prompt" in
  *'Symbol: app.run'*) ;;
  *) printf '%s\n' 'missing prompt fragment: Symbol: app.run' "$*" >&2; exit 64 ;;
esac
case "$prompt" in
  *'PYTHON EXTERNAL TYPE PROJECTIONS'*) ;;
  *) printf '%s\n' 'missing prompt fragment: PYTHON EXTERNAL TYPE PROJECTIONS' "$*" >&2; exit 64 ;;
esac
case "$prompt" in
  *'app.Widget = io:StringIO'*) ;;
  *) printf '%s\n' 'missing prompt fragment: app.Widget = io:StringIO' "$*" >&2; exit 64 ;;
esac
case "$prompt" in
  *'For other modules import public generated symbols only through `from app import name` and generated value types only through `from app_types import Type`.'*) ;;
  *) printf '%s\n' 'missing prompt fragment: module facade/type import guidance' "$*" >&2; exit 64 ;;
esac
case "$prompt" in
  *'You MAY additionally define private implementation helpers, private immutable constants, and invariant TypeVars.'*) ;;
  *) printf '%s\n' 'missing prompt fragment: private implementation policy' "$*" >&2; exit 64 ;;
esac
case "$prompt" in
  *'Each constant MUST have a single-leading-underscore name that is neither dunder nor reserved `_cott_`'*) ;;
  *) printf '%s\n' 'missing prompt fragment: private Final constant policy' "$*" >&2; exit 64 ;;
esac
case "$prompt" in
  *'Use contract containers directly: CottList(values=xs), CottSet(values=xs), FrozenMap(values={}), and CottTuple2(first=a, second=b).'*) ;;
  *) printf '%s\n' 'missing prompt fragment: keyword-only contract containers' "$*" >&2; exit 64 ;;
esac
case "$prompt" in
  *'For Result returns import top-level Ok and Err from cott_runtime and return Ok(value=...) or Err(error=...); never use Result.Ok/Result.Err'*) ;;
  *) printf '%s\n' 'missing prompt fragment: top-level result constructors' "$*" >&2; exit 64 ;;
esac
case "$prompt" in
  *'`Unit` is the annotation and `UNIT` is its only value; return `Ok(value=UNIT)` for Result[Unit, E].'*) ;;
  *) printf '%s\n' 'missing prompt fragment: Unit singleton ABI' "$*" >&2; exit 64 ;;
esac
case "$prompt" in
  *'For Option annotations use the top-level `Some(value=...)` and `Nothing()` variants, never `Option.Some` or `Option.Nothing`; narrow an Option with structural `match` before reading a Some payload.'*) ;;
  *) printf '%s\n' 'missing prompt fragment: Option variant ABI' "$*" >&2; exit 64 ;;
esac
case "$prompt" in
  *'`typing.cast` MAY be used only from a concrete external SDK return to its declared external projection when upstream stubs are incompatible; never cast Cott-owned values.'*) ;;
  *) printf '%s\n' 'missing prompt fragment: external projection cast policy' "$*" >&2; exit 64 ;;
esac
case "$prompt" in
  *'Generated payload enum aliases have no members: import and construct top-level `<Enum>_<Variant>` from the exact `app_types` module, never `<Enum>.<Variant>`.'*) ;;
  *) printf '%s\n' 'missing prompt fragment: top-level payload enum variants' "$*" >&2; exit 64 ;;
esac
case "$prompt" in
  *'"external_types"'*) printf '%s\n' 'unexpected prompt fragment: "external_types"' "$*" >&2; exit 64 ;;
esac
case "$prompt" in
  *'EXISTING IMPLEMENTATION'*'VALIDATION FAILURE'*'missing_distribution'*'Fix the existing implementation and change nothing outside the target file.'*)
    printf 'from cott_runtime import I32\n\n\ndef run() -> I32:\n    return 7\n' > implementation.py
    ;;
  *'EXISTING IMPLEMENTATION'*)
    printf '%s\n' 'retry prompt omitted validation feedback' >&2
    exit 64
    ;;
  *)
    printf 'import missing_distribution\nfrom cott_runtime import I32\n\n\ndef run() -> I32:\n    return 7\n' > implementation.py
    ;;
esac
"#,
    )
    .expect("write fake OMP");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&omp, fs::Permissions::from_mode(0o755))
            .expect("make fake OMP executable");
    }
    let path = std::env::join_paths([tools.as_path(), Path::new("/usr/bin"), Path::new("/bin")])
        .expect("PATH");
    let output = Command::new(env!("CARGO_BIN_EXE_cott"))
        .args([
            "generate",
            "--agent",
            "omp",
            "--target",
            "python",
            "--project",
        ])
        .arg(&project.path)
        .env("PATH", path)
        .output()
        .expect("cott should run");
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert_eq!(
        fs::read_to_string(project.path.join("python/_cott_impl/app/run.py"))
            .expect("durable candidate"),
        "from cott_runtime import I32\n\n\ndef run() -> I32:\n    return 7\n"
    );
    assert!(project.path.join("generated/python/app.py").is_file());
}

#[test]
fn generate_agent_prompt_grants_exact_factory_facade_imports() {
    let project = method_project();
    fs::write(
        project.path.join("src/app.cott"),
        "module app\nuse api.service.ReaderState\n\nfn run(factory: Factory[ReaderState]) -> I32\n",
    )
    .expect("Factory source should be writable");
    let tools = project.path.join("tools");
    fs::create_dir(&tools).expect("tool directory");
    let omp = tools.join("omp");
    fs::write(
        &omp,
        r#"#!/bin/sh
if [ "$1" = "--version" ]; then echo omp/17.2.12; exit 0; fi
case "$*" in
  *'Symbol: app.run'*'Exact generated Cott facade modules MAY be imported directly or from their parent package, with an optional alias, for module-qualified access. Import generated value types for annotations through `from module_types import Type`, and do not import any other project-local module.'*'Factory annotations require these exact concrete public-facade imports; do not substitute them or import from `*_types`:'*'from api.service import ReaderState'*'Use each listed `from module import Concrete` line for annotations. The same exact generated facade may also be imported under the general module-import rule when its class object is needed.'*'`Factory[Concrete]` maps to `type[Concrete]`'*'Constructor calls MUST match `Concrete`'\''s inferred Cott init signature.'*'Validation MUST NOT construct or invoke a Factory value.'*)
    printf '%s\n' 'from api.service import ReaderState' 'from cott_runtime import I32' '' '' 'def run(factory: type[ReaderState]) -> I32:' '    return 7' > implementation.py
    ;;
  *) exit 64 ;;
esac
"#,
    )
    .expect("write fake OMP");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&omp, fs::Permissions::from_mode(0o755))
            .expect("make fake OMP executable");
    }
    let path = std::env::join_paths([tools.as_path(), Path::new("/usr/bin"), Path::new("/bin")])
        .expect("PATH");
    let output = Command::new(env!("CARGO_BIN_EXE_cott"))
        .args([
            "generate",
            "app.run",
            "--agent",
            "omp",
            "--target",
            "python",
            "--project",
        ])
        .arg(&project.path)
        .env("PATH", path)
        .output()
        .expect("cott should run");
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
}

#[test]
fn generate_promotes_an_impl_method_helper_without_agent_class_shell() {
    let project = method_project();
    let tools = project.path.join("tools");
    fs::create_dir(&tools).expect("tool directory");
    let omp = tools.join("omp");
    fs::write(
        &omp,
        r#"#!/bin/sh
if [ "$1" = "--version" ]; then echo omp/17.2.12; exit 0; fi
case "$*" in
  *'Symbol: api.service.ReaderState.read'*'You MAY additionally define private implementation helpers, private immutable constants, and invariant TypeVars.'*'Each constant MUST have a single-leading-underscore name that is neither dunder nor reserved `_cott_`'*'The compiler-owned concrete facade class `ReaderState` is absent from `api.service_types`; import it exactly as `from api.service import ReaderState` for the `self` annotation.'*'Generated value-type imports remain `from api.service_types import Type`.'*)
    printf '%s\n' 'from api.service import ReaderState' 'from cott_runtime import I32' '' '' 'def _cott_impl_ReaderState_read(self: ReaderState, amount: I32) -> I32:' '    return amount' > implementation.py
    ;;
  *) exit 64 ;;
esac
"#,
    )
    .expect("write fake OMP");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&omp, fs::Permissions::from_mode(0o755))
            .expect("make fake OMP executable");
    }
    let path = std::env::join_paths([tools.as_path(), Path::new("/usr/bin"), Path::new("/bin")])
        .expect("PATH");
    let output = Command::new(env!("CARGO_BIN_EXE_cott"))
        .args([
            "generate",
            "api.service.ReaderState.read",
            "--agent",
            "omp",
            "--target",
            "python",
            "--project",
        ])
        .arg(&project.path)
        .env("PATH", path)
        .output()
        .expect("cott should run");
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert_eq!(
        fs::read_to_string(
            project
                .path
                .join("python/_cott_impl/api/service/ReaderState/read.py")
        )
        .expect("durable method helper"),
        "from api.service import ReaderState\nfrom cott_runtime import I32\n\n\ndef _cott_impl_ReaderState_read(self: ReaderState, amount: I32) -> I32:\n    return amount\n"
    );
    let record: serde_json::Value = serde_json::from_slice(
        &fs::read(project.path.join("generated/generation.json")).expect("generated method record"),
    )
    .expect("generated method record is JSON");
    let implementation = &record["current"]["implementations"][0];
    assert_eq!(implementation["kind"], "impl_method");
    assert_eq!(implementation["concrete"], "ReaderState");
    assert_eq!(implementation["method"], "read");
    let facade = fs::read_to_string(project.path.join("generated/python/api/service.py"))
        .expect("generated method facade");
    assert!(facade.contains("class ReaderState"));
    assert!(
        !project
            .path
            .join("python/_cott_impl/api/service/read.py")
            .exists()
    );
}

#[test]
fn generate_impl_agent_prompt_grants_exact_factory_facade_imports() {
    let project = method_project();
    fs::write(
        project.path.join("src/models.cott"),
        "module models\n\ntrait Builder:\n    fn build(self, amount: I32) -> I32\n\nimpl FactoryConcrete for Builder:\n    state:\n        count: I32 = 0\n    init(count: I32):\n        requires count > 0\n        ensures self.count == count\n    fn build(self, amount: I32) -> I32:\n        ensures result == amount\n",
    )
    .expect("Factory concrete source should be writable");
    fs::write(
        project.path.join("src/api/service.cott"),
        "module api.service\nuse models.FactoryConcrete\n\ntrait Reader:\n    fn read(self, factory: Factory[FactoryConcrete]) -> I32\n\nimpl ReaderState for Reader:\n    state:\n        count: I32 = 0\n    init(count: I32):\n        requires count > 0\n        ensures self.count == count\n    fn read(self, factory: Factory[FactoryConcrete]) -> I32:\n        ensures result == self.count\n",
    )
    .expect("Factory method source should be writable");
    let tools = project.path.join("tools");
    fs::create_dir(&tools).expect("tool directory");
    let omp = tools.join("omp");
    fs::write(
        &omp,
        r#"#!/bin/sh
if [ "$1" = "--version" ]; then echo omp/17.2.12; exit 0; fi
case "$*" in
  *'Symbol: api.service.ReaderState.read'*'Factory annotations require these exact concrete public-facade imports; do not substitute them or import from `*_types`:'*'from models import FactoryConcrete'*'`Factory[Concrete]` maps to `type[Concrete]`'*)
    printf '%s\n' 'from api.service import ReaderState' 'from models import FactoryConcrete' 'from cott_runtime import I32' '' '' 'def _cott_impl_ReaderState_read(self: ReaderState, factory: type[FactoryConcrete]) -> I32:' '    return self.count' > implementation.py
    ;;
  *) exit 64 ;;
esac
"#,
    )
    .expect("write fake OMP");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&omp, fs::Permissions::from_mode(0o755))
            .expect("make fake OMP executable");
    }
    let path = std::env::join_paths([tools.as_path(), Path::new("/usr/bin"), Path::new("/bin")])
        .expect("PATH");
    let output = Command::new(env!("CARGO_BIN_EXE_cott"))
        .args([
            "generate",
            "api.service.ReaderState.read",
            "--agent",
            "omp",
            "--target",
            "python",
            "--project",
        ])
        .arg(&project.path)
        .env("PATH", path)
        .output()
        .expect("cott should run");
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
}

#[test]
fn generate_scoped_free_function_does_not_run_unrelated_initializers() {
    let project = method_project();
    fs::write(
        project.path.join("src/api/service.cott"),
        "module api.service\n\nfn run() -> I32\n\ntrait Reader:\n    fn read(self) -> I32\n\nimpl ReaderState for Reader:\n    state:\n        count: I32 = 0\n    invariant false\n    init(count: I32):\n        requires count > 0\n    fn read(self) -> I32:\n        ensures result == self.count\n",
    )
    .expect("scoped free-function source should be writable");
    let tools = project.path.join("tools");
    fs::create_dir(&tools).expect("tool directory");
    let omp = tools.join("omp");
    fs::write(
        &omp,
        r#"#!/bin/sh
if [ "$1" = "--version" ]; then echo omp/17.2.12; exit 0; fi
case "$*" in
  *"Symbol: api.service.run"*)
    printf '%s\n' 'from cott_runtime import I32' '' '' 'def run() -> I32:' '    return 7' > implementation.py
    ;;
  *) exit 64 ;;
esac
"#,
    )
    .expect("write fake OMP");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&omp, fs::Permissions::from_mode(0o755))
            .expect("make fake OMP executable");
    }
    let path = std::env::join_paths([tools.as_path(), Path::new("/usr/bin"), Path::new("/bin")])
        .expect("PATH");
    let output = Command::new(env!("CARGO_BIN_EXE_cott"))
        .args([
            "generate",
            "api.service.run",
            "--agent",
            "omp",
            "--target",
            "python",
            "--project",
        ])
        .arg(&project.path)
        .env("PATH", path)
        .output()
        .expect("cott should run");
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
}

#[test]
fn generate_rejects_an_agent_owned_impl_class_shell() {
    let project = method_project();
    let tools = project.path.join("tools");
    fs::create_dir(&tools).expect("tool directory");
    let omp = tools.join("omp");
    fs::write(
        &omp,
        r#"#!/bin/sh
if [ "$1" = "--version" ]; then echo omp/17.2.12; exit 0; fi
printf '%s\n' 'class ReaderState:' '    def read(self, amount: int) -> int:' '        return amount' > implementation.py
"#,
    )
    .expect("write fake OMP");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&omp, fs::Permissions::from_mode(0o755))
            .expect("make fake OMP executable");
    }
    let path = std::env::join_paths([tools.as_path(), Path::new("/usr/bin"), Path::new("/bin")])
        .expect("PATH");
    let output = Command::new(env!("CARGO_BIN_EXE_cott"))
        .args([
            "generate",
            "api.service.ReaderState.read",
            "--agent",
            "omp",
            "--target",
            "python",
            "--project",
        ])
        .arg(&project.path)
        .env("PATH", path)
        .output()
        .expect("cott should run");
    assert_eq!(output.status.code(), Some(5));
    assert!(String::from_utf8_lossy(&output.stderr).contains("agent generation"));
    assert!(
        !project
            .path
            .join("python/_cott_impl/api/service/ReaderState/read.py")
            .exists()
    );
}
#[test]
fn process_bar_generation_records_unresolved_and_verified_transitions() {
    let fixture = Path::new(env!("CARGO_MANIFEST_DIR")).join("examples/complex/process-bar");
    let project = TempDir::new();
    fs::copy(fixture.join("cott.toml"), project.path.join("cott.toml"))
        .expect("process-bar manifest should be copied");
    fs::create_dir_all(project.path.join("src/foo")).expect("fixture source directory");
    fs::copy(
        fixture.join("src/foo/bar.cott"),
        project.path.join("src/foo/bar.cott"),
    )
    .expect("process-bar source should be copied");
    fs::create_dir(project.path.join("python")).expect("target source directory");
    fs::copy(
        fixture.join("python/pyproject.toml"),
        project.path.join("python/pyproject.toml"),
    )
    .expect("target project metadata should be copied");
    install_fake_python_tools(&project.path);

    let emitted = cott(&project.path, &["emit", "python"]);
    assert!(
        emitted.status.success(),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    for implementation in [
        "build_output.py",
        "process_bar.py",
        "process_payload_bytes.py",
        "validate_payload.py",
    ] {
        for root in [
            "python/_cott_impl/foo/bar",
            "generated/python/_cott_impl/foo/bar",
        ] {
            assert!(
                !project.path.join(root).join(implementation).exists(),
                "{implementation} must begin unresolved under {root}"
            );
        }
    }
    let initial: serde_json::Value = serde_json::from_slice(
        &fs::read(project.path.join("generated/generation.json"))
            .expect("initial generation record"),
    )
    .expect("initial generation JSON");
    assert_eq!(initial["current"]["verified"], false);
    assert_eq!(initial["current"]["implementations"], serde_json::json!([]));
    assert_eq!(
        initial["current"]["unresolved"],
        serde_json::json!([
            "foo.bar.build_output",
            "foo.bar.process_bar",
            "foo.bar.process_payload_bytes",
            "foo.bar.validate_payload"
        ])
    );
    assert_eq!(initial["current"]["agent_runs"], serde_json::json!([]));
    assert!(initial["last_verified"].is_null());

    let tools = project.path.join("tools");
    fs::create_dir(&tools).expect("tool directory");
    let omp = tools.join("omp");
    fs::write(
        &omp,
        r#"#!/bin/sh
if [ "$1" = "--version" ]; then
  echo omp/17.2.12
  exit 0
fi
case "$*" in
  *"Symbol: foo.bar.build_output"*)
    printf '%s\n' 'from foo.bar_types import OutputPayload, PayloadFormat, PayloadSize' '' '' 'def build_output(data: bytes, source_size: PayloadSize, format: PayloadFormat) -> OutputPayload:' '    return OutputPayload(data=data, source_size=source_size, format=format)' > implementation.py
    printf '%s\n' 'agent-run=build_output'
    ;;
  *"Symbol: foo.bar.process_bar"*)
    printf '%s\n' 'from cott_runtime import Err, Ok, Result' 'from foo.bar import build_output, process_payload_bytes, validate_payload' 'from foo.bar_types import BarError, BarOptions, InputPayload, OutputPayload' '' '' 'def process_bar(data: InputPayload, options: BarOptions) -> Result[OutputPayload, BarError]:' '    validated = validate_payload(data)' '    if isinstance(validated, Err):' '        return Err(error=validated.error)' '    processed = process_payload_bytes(validated.value.data, options)' '    if isinstance(processed, Err):' '        return Err(error=processed.error)' '    return Ok(' '        value=build_output(' '            processed.value,' '            validated.value.declared_size,' '            validated.value.format,' '        )' '    )' > implementation.py
    printf '%s\n' 'agent-run=process_bar'
    ;;
  *"Symbol: foo.bar.process_payload_bytes"*)
    printf '%s\n' 'from cott_runtime import Ok, Result' 'from foo.bar_types import BarError, BarOptions' '' '' 'def process_payload_bytes(data: bytes, options: BarOptions) -> Result[bytes, BarError]:' '    return Ok(value=data)' > implementation.py
    printf '%s\n' 'agent-run=process_payload_bytes'
    ;;
  *"Symbol: foo.bar.validate_payload"*)
    printf '%s\n' 'from cott_runtime import Err, Ok, Result' 'from foo.bar_types import BarError, BarError_InvalidPayload, InputPayload' '' '' 'def validate_payload(data: InputPayload) -> Result[InputPayload, BarError]:' '    if len(data.data) == 0:' '        return Err(error=BarError_InvalidPayload(reason="empty payload"))' '    return Ok(value=data)' > implementation.py
    printf '%s\n' 'agent-run=validate_payload'
    ;;
  *)
    printf '%s\n' 'unexpected process-bar agent prompt' >&2
    exit 64
    ;;
esac
"#,
    )
    .expect("write fake OMP");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&omp, fs::Permissions::from_mode(0o755))
            .expect("make fake OMP executable");
    }
    let path = std::env::join_paths([tools.as_path(), Path::new("/usr/bin"), Path::new("/bin")])
        .expect("PATH");
    let before_generate = file_snapshot(&project.path);
    let generated_all = Command::new(env!("CARGO_BIN_EXE_cott"))
        .args([
            "generate",
            "--agent",
            "omp",
            "--target",
            "python",
            "--project",
        ])
        .arg(&project.path)
        .env("PATH", &path)
        .output()
        .expect("unscoped generate should run");
    assert!(
        generated_all.status.success(),
        "{}",
        String::from_utf8_lossy(&generated_all.stderr)
    );

    let expected_bindings = [
        (
            "python/_cott_impl/foo/bar/build_output.py",
            "from foo.bar_types import OutputPayload, PayloadFormat, PayloadSize\n\n\ndef build_output(data: bytes, source_size: PayloadSize, format: PayloadFormat) -> OutputPayload:\n    return OutputPayload(data=data, source_size=source_size, format=format)\n",
        ),
        (
            "python/_cott_impl/foo/bar/process_bar.py",
            "from cott_runtime import Err, Ok, Result\nfrom foo.bar import build_output, process_payload_bytes, validate_payload\nfrom foo.bar_types import BarError, BarOptions, InputPayload, OutputPayload\n\n\ndef process_bar(data: InputPayload, options: BarOptions) -> Result[OutputPayload, BarError]:\n    validated = validate_payload(data)\n    if isinstance(validated, Err):\n        return Err(error=validated.error)\n    processed = process_payload_bytes(validated.value.data, options)\n    if isinstance(processed, Err):\n        return Err(error=processed.error)\n    return Ok(\n        value=build_output(\n            processed.value,\n            validated.value.declared_size,\n            validated.value.format,\n        )\n    )\n",
        ),
        (
            "python/_cott_impl/foo/bar/process_payload_bytes.py",
            "from cott_runtime import Ok, Result\nfrom foo.bar_types import BarError, BarOptions\n\n\ndef process_payload_bytes(data: bytes, options: BarOptions) -> Result[bytes, BarError]:\n    return Ok(value=data)\n",
        ),
        (
            "python/_cott_impl/foo/bar/validate_payload.py",
            "from cott_runtime import Err, Ok, Result\nfrom foo.bar_types import BarError, BarError_InvalidPayload, InputPayload\n\n\ndef validate_payload(data: InputPayload) -> Result[InputPayload, BarError]:\n    if len(data.data) == 0:\n        return Err(error=BarError_InvalidPayload(reason=\"empty payload\"))\n    return Ok(value=data)\n",
        ),
    ];
    for (relative, expected) in expected_bindings {
        assert_eq!(
            fs::read_to_string(project.path.join(relative))
                .unwrap_or_else(|error| panic!("durable helper {relative}: {error}")),
            expected
        );
    }

    let generated: serde_json::Value = serde_json::from_slice(
        &fs::read(project.path.join("generated/generation.json"))
            .expect("generated generation record"),
    )
    .expect("generated generation JSON");
    assert_eq!(generated["current"]["verified"], false);
    assert_eq!(generated["current"]["unresolved"], serde_json::json!([]));
    assert_eq!(
        generated["current"]["implementations"]
            .as_array()
            .expect("generated implementations")
            .iter()
            .map(|implementation| {
                (
                    implementation["cott_symbol"].as_str().expect("Cott symbol"),
                    implementation["kind"].as_str().expect("callable kind"),
                    implementation["concrete"].is_null(),
                    implementation["method"].is_null(),
                    implementation["owner"].as_str().expect("owner"),
                )
            })
            .collect::<Vec<_>>(),
        [
            ("foo.bar.build_output", "function", true, true, "agent"),
            ("foo.bar.process_bar", "function", true, true, "agent"),
            (
                "foo.bar.process_payload_bytes",
                "function",
                true,
                true,
                "agent",
            ),
            ("foo.bar.validate_payload", "function", true, true, "agent"),
        ]
    );
    assert!(generated["last_verified"].is_null());
    let agent_runs = generated["current"]["agent_runs"].clone();
    let run_summaries = agent_runs
        .as_array()
        .expect("agent runs")
        .iter()
        .map(|run| {
            serde_json::json!({
                "symbol": run["symbol"],
                "adapter": run["adapter"],
                "adapter_version": run["adapter_version"],
                "status": run["status"],
                "stdout_bytes": run["stdout"]["bytes"],
                "stderr_bytes": run["stderr"]["bytes"],
            })
        })
        .collect::<Vec<_>>();
    assert_eq!(
        serde_json::Value::Array(run_summaries),
        serde_json::json!([
            {
                "symbol": "foo.bar.build_output",
                "adapter": "omp",
                "adapter_version": "17.2.12",
                "status": {
                    "exit_code": 0,
                    "signal": null,
                    "timed_out": false,
                    "cancelled": false
                },
                "stdout_bytes": 23,
                "stderr_bytes": 0
            },
            {
                "symbol": "foo.bar.process_bar",
                "adapter": "omp",
                "adapter_version": "17.2.12",
                "status": {
                    "exit_code": 0,
                    "signal": null,
                    "timed_out": false,
                    "cancelled": false
                },
                "stdout_bytes": 22,
                "stderr_bytes": 0
            },
            {
                "symbol": "foo.bar.process_payload_bytes",
                "adapter": "omp",
                "adapter_version": "17.2.12",
                "status": {
                    "exit_code": 0,
                    "signal": null,
                    "timed_out": false,
                    "cancelled": false
                },
                "stdout_bytes": 32,
                "stderr_bytes": 0
            },
            {
                "symbol": "foo.bar.validate_payload",
                "adapter": "omp",
                "adapter_version": "17.2.12",
                "status": {
                    "exit_code": 0,
                    "signal": null,
                    "timed_out": false,
                    "cancelled": false
                },
                "stdout_bytes": 27,
                "stderr_bytes": 0
            }
        ])
    );

    let after_generate = file_snapshot(&project.path);
    let mut changed = before_generate
        .keys()
        .chain(after_generate.keys())
        .filter(|path| before_generate.get(*path) != after_generate.get(*path))
        .cloned()
        .collect::<std::collections::BTreeSet<_>>();
    let managed = generated["current"]["managed_files"]
        .as_object()
        .expect("managed files");
    let mut expected = managed
        .keys()
        .map(PathBuf::from)
        .collect::<std::collections::BTreeSet<_>>();
    expected.insert(PathBuf::from("generated/generation.json"));
    for implementation in [
        "build_output.py",
        "process_bar.py",
        "process_payload_bytes.py",
        "validate_payload.py",
    ] {
        let implementation = PathBuf::from("python/_cott_impl/foo/bar").join(implementation);
        expected.insert(implementation.clone());
        assert!(changed.remove(&implementation));
    }
    assert!(
        changed.iter().all(|path| expected.contains(path)),
        "unexpected changed files: {changed:?}"
    );

    let verified = cott(&project.path, &["verify"]);
    assert!(
        verified.status.success(),
        "{}",
        String::from_utf8_lossy(&verified.stderr)
    );
    let verified_record: serde_json::Value = serde_json::from_slice(
        &fs::read(project.path.join("generated/generation.json"))
            .expect("verified generation record"),
    )
    .expect("verified generation JSON");
    assert_eq!(verified_record["current"]["verified"], true);
    assert_eq!(verified_record["current"], verified_record["last_verified"]);
    assert_eq!(
        verified_record["current"]["implementations"],
        generated["current"]["implementations"]
    );
    assert_eq!(verified_record["current"]["agent_runs"], agent_runs);

    let diff = cott(&project.path, &["diff"]);
    assert!(
        diff.status.success(),
        "{}",
        String::from_utf8_lossy(&diff.stderr)
    );
    assert_eq!(
        String::from_utf8(diff.stdout).expect("diff output should be UTF-8"),
        "NO CHANGE\n"
    );
}

#[test]
fn generate_promotes_a_sandboxed_codex_candidate_with_artifacts() {
    let project = project();
    make_unresolved(&project);
    let tools = project.path.join("tools");
    fs::create_dir(&tools).expect("tool directory");
    let codex = tools.join("codex");
    fs::write(&codex, "#!/bin/sh\nif [ \"$1\" = \"--version\" ]; then echo codex-cli 0.147.0; exit 0; fi\ncat >/dev/null\nprintf 'from cott_runtime import I32\\n\\n\\ndef run() -> I32:\\n    return 7\\n' > implementation.py\n")
        .expect("write fake Codex");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&codex, fs::Permissions::from_mode(0o755))
            .expect("make fake Codex executable");
    }
    let path = std::env::join_paths([tools.as_path(), Path::new("/usr/bin"), Path::new("/bin")])
        .expect("PATH");
    let output = Command::new(env!("CARGO_BIN_EXE_cott"))
        .args([
            "generate",
            "--agent",
            "codex",
            "--target",
            "python",
            "--project",
        ])
        .arg(&project.path)
        .env("PATH", path)
        .output()
        .expect("cott should run");
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert_eq!(
        fs::read_to_string(project.path.join("python/_cott_impl/app/run.py"))
            .expect("durable candidate"),
        "from cott_runtime import I32\n\n\ndef run() -> I32:\n    return 7\n"
    );
}

#[test]
fn init_scaffolds_a_normative_project_with_supported_uv() {
    let temp = TempDir::new();
    let tools = temp.path.join("tools");
    fs::create_dir(&tools).expect("tool directory");
    let uv = tools.join("uv");
    fs::write(
        &uv,
        r#"#!/bin/sh
if [ "$1" = "--no-config" ]; then shift; fi
case "$1" in
  --version) echo 'uv 0.12.4' ;;
  python)
    managed="$(dirname "$0")/managed"
    if [ "$2" = "dir" ]; then
      mkdir -p "$managed"
      printf '%s\n' '#!/bin/sh' 'echo "cpython 3.14.7"' > "$managed/python"
      chmod +x "$managed/python"
      echo "$managed"
    elif [ "$2" = "find" ]; then
      echo "$managed/python"
    fi
    ;;
  lock)
    touch python/uv.lock
    ;;
  venv|sync)
    mkdir -p "$UV_PROJECT_ENVIRONMENT/bin"
    printf '%s\n' '#!/bin/sh' 'echo "cpython 3.14.7"' > "$UV_PROJECT_ENVIRONMENT/bin/python"
    printf '%s\n' '#!/bin/sh' 'echo "basedpyright 1.40.0"' > "$UV_PROJECT_ENVIRONMENT/bin/basedpyright"
    chmod +x "$UV_PROJECT_ENVIRONMENT/bin/python" "$UV_PROJECT_ENVIRONMENT/bin/basedpyright"
    ;;
esac
"#,
    )
    .expect("write fake uv");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(&uv, fs::Permissions::from_mode(0o755))
            .expect("make fake uv executable");
    }
    let target = temp.path.join("new-app");
    let path = std::env::join_paths([tools.as_path(), Path::new("/usr/bin"), Path::new("/bin")])
        .expect("PATH");
    let output = Command::new(env!("CARGO_BIN_EXE_cott"))
        .args(["init"])
        .arg(&target)
        .env("PATH", path)
        .output()
        .expect("cott should run");
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert!(target.join("src/new_app/main.cott").is_file());
    let manifest = fs::read_to_string(target.join("cott.toml")).expect("manifest");
    assert!(manifest.contains("version = \"0.1.0\""));
    assert!(manifest.contains("runtime_validation = \"boundary\""));
    assert!(manifest.contains("lockfile = \"python/uv.lock\""));
    assert!(target.join("python/uv.lock").is_file());
    let pyproject = fs::read_to_string(target.join("python/pyproject.toml")).expect("pyproject");
    assert!(pyproject.contains("requires-python = \">=3.14.6,<3.15\""));
    assert!(pyproject.contains("basedpyright>=1.39.9"));
    assert_eq!(
        fs::read_to_string(target.join(".gitignore")).expect("gitignore"),
        ".cott/\n.venv/\ngenerated/generation.json\n__pycache__/\n*.py[cod]\n"
    );
}
#[test]
fn json_mode_returns_one_closed_diagnostic_document_with_source_spans() {
    let project = project();
    fs::write(
        project.path.join("src/app.cott"),
        "module app\n\nfn run( -> I32\n",
    )
    .expect("source should be writable");

    let output = cott(&project.path, &["check", "--format", "json"]);
    assert_eq!(output.status.code(), Some(3));
    assert!(output.stderr.is_empty());
    let report: serde_json::Value =
        serde_json::from_slice(&output.stdout).expect("stdout should be one JSON document");
    assert_eq!(report["schema_version"], 1);
    let diagnostic = &report["diagnostics"][0];
    assert_eq!(diagnostic["severity"], "error");
    assert_eq!(diagnostic["span"]["path"], "src/app.cott");
    assert!(diagnostic["span"]["end_byte"].as_u64().is_some());
}

#[test]
fn runs_generated_facade_when_python3_is_available() {
    let probe = match Command::new("python3")
        .args([
            "-c",
            "import pathlib,platform,sys; print(platform.python_version()); print(pathlib.Path(sys.executable).resolve())",
        ])
        .output()
    {
        Ok(output) if output.status.success() => output,
        _ => return,
    };
    let probe = String::from_utf8(probe.stdout).expect("Python probe must be UTF-8");
    let mut lines = probe.lines();
    if lines.next() != Some("3.14.6") {
        return;
    }
    let interpreter = PathBuf::from(lines.next().expect("Python probe executable"));
    let project = project();
    fs::copy(&interpreter, project.path.join(".venv/bin/python"))
        .expect("install matching target Python");
    let emitted = cott(&project.path, &["emit", "python"]);
    assert!(
        emitted.status.success(),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    let output = Command::new(&interpreter)
        .args(["-c", "from app import run; print(run())"])
        .current_dir(project.path.join("generated/python"))
        .output()
        .expect("generated facade should run");

    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert_eq!(
        String::from_utf8(output.stdout).expect("stdout must be UTF-8"),
        "7\n"
    );
    let verified = cott(&project.path, &["verify"]);
    assert!(
        verified.status.success(),
        "{}",
        String::from_utf8_lossy(&verified.stderr)
    );
}
#[test]
fn generated_facades_enforce_contextual_and_exit_contracts() {
    let project = TempDir::new();
    fs::write(
        project.path.join("cott.toml"),
        r#"[project]
name = "contract-e2e"
version = "0.1.0"
source = "src"

[target.python]
source = "python"
generated = "generated/python"
stubs = "generated/stubs"
interpreter = ".venv/bin/python"
type_checker = ".venv/bin/basedpyright"
runtime_validation = "boundary"

[target.python.implementations]
"app.bounded" = "cott_bindings.app.bounded:bounded"
"app.guarded" = "cott_bindings.app.guarded:guarded"
"app.terminate" = "cott_bindings.app.terminate:terminate"
"app.abort" = "cott_bindings.app.abort:abort"
"#,
    )
    .expect("manifest should be writable");
    fs::create_dir_all(project.path.join("src")).expect("source directory should be writable");
    fs::write(
        project.path.join("src/app.cott"),
        r#"module app

enum GateError:
    Rejected

newtype Key(U64)
newtype Labels(List[Str])

struct Boxed:
    value: I32

enum Mixed:
    Empty
    Full(value: I32)

fn bounded(value: F32) -> F32:
    requires value + 0.5 <= 1.0

fn guarded(value: I32) -> Result[I32, GateError]:
    error GateError.Rejected when value < 0

fn terminate(code: I32) -> Never:
    effects [process.exit]

fn abort(code: I32) -> Unit:
    effects [process.exit]
"#,
    )
    .expect("source should be writable");
    fs::create_dir_all(project.path.join("python")).expect("Python source directory");
    fs::write(
        project.path.join("python/pyproject.toml"),
        "[project]\nname = \"contract-e2e\"\nversion = \"0.1.0\"\nrequires-python = \">=3.14,<3.15\"\ndependencies = []\n",
    )
    .expect("target project metadata should be writable");
    let implementations = [
        (
            "bounded",
            "from cott_runtime import F32


def bounded(value: F32) -> F32:
    return value
",
        ),
        (
            "guarded",
            "from app_types import GateError, GateError_Rejected
from cott_runtime import Err, I32, Ok, Result


def guarded(value: I32) -> Result[I32, GateError]:
    if value < 0:
        return Err(error=GateError_Rejected())
    return Ok(value=value)
",
        ),
        (
            "terminate",
            "from typing import Never

from cott_runtime import I32


def terminate(code: I32) -> Never:
    raise SystemExit(code)
",
        ),
        (
            "abort",
            "from cott_runtime import I32, Unit


def abort(code: I32) -> Unit:
    raise SystemExit(code)
",
        ),
    ];
    for (function, source) in implementations {
        let path = project
            .path
            .join("python/cott_bindings/app")
            .join(format!("{function}.py"));
        fs::create_dir_all(path.parent().expect("implementation parent"))
            .expect("implementation directory should be writable");
        fs::write(path, source).expect("implementation should be writable");
    }
    install_fake_python_tools(&project.path);

    let emitted = cott(&project.path, &["emit", "python"]);
    assert!(
        emitted.status.success(),
        "{}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    retarget_generation_to_host_python(&project.path);

    let script = r#"
import json

from app import abort, bounded, guarded, terminate
from cott_runtime import CottContractViolation, Err, Ok
from app_types import Boxed, Key, Labels, Mixed_Empty, Mixed_Full

bounded_value = bounded(0.25)
assert bounded_value == 0.25
guarded_ok = guarded(3)
assert isinstance(guarded_ok, Ok) and guarded_ok.value == 3
guarded_error = guarded(-1)
assert isinstance(guarded_error, Err)
assert type(guarded_error.error).__name__ == "GateError_Rejected"
assert Boxed.__hash__ is None
assert Labels.__hash__ is None
assert Mixed_Full.__hash__ is None
assert isinstance(hash(Key(value=1)), int)
assert isinstance(hash(Mixed_Empty()), int)

try:
    bounded(0.75)
except CottContractViolation as error:
    requires = {
        "symbol": error.symbol,
        "phase": error.phase,
        "span": error.span,
        "expected": error.expected,
        "actual": error.actual,
    }
else:
    raise AssertionError("bounded requires should fail")

try:
    terminate(7)
except SystemExit as error:
    never_exit = error.code
else:
    raise AssertionError("declared Never process.exit should propagate")

try:
    abort(9)
except CottContractViolation as error:
    system_exit_violation = {
        "symbol": error.symbol,
        "phase": error.phase,
        "expected": error.expected,
        "actual": error.actual,
    }
else:
    raise AssertionError("non-Never SystemExit should violate the contract")

print(json.dumps({
    "bounded": bounded_value,
    "guarded_ok": guarded_ok.value,
    "guarded_error": type(guarded_error.error).__name__,
    "requires": requires,
    "never_exit": never_exit,
    "system_exit_violation": system_exit_violation,
}))
"#;
    let output = Command::new("/usr/bin/python3")
        .args(["-c", script])
        .current_dir(project.path.join("generated/python"))
        .output()
        .expect("generated facades should run");
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );

    let report: serde_json::Value =
        serde_json::from_slice(&output.stdout).expect("facade report should be JSON");
    assert_eq!(report["bounded"], 0.25);
    assert_eq!(report["guarded_ok"], 3);
    assert_eq!(report["guarded_error"], "GateError_Rejected");
    let requires = &report["requires"];
    assert_eq!(requires["symbol"], "app.bounded");
    assert_eq!(requires["phase"], "requires");
    assert!(requires["span"].is_object());
    assert!(requires["span"]["start_line"].as_u64().is_some());
    assert_eq!(requires["expected"], "true");
    assert_eq!(requires["actual"], "false");
    assert_eq!(report["never_exit"], 7);
    assert_eq!(report["system_exit_violation"]["symbol"], "app.abort");
    assert_eq!(
        report["system_exit_violation"]["phase"],
        "implementation-call"
    );
    assert_eq!(
        report["system_exit_violation"]["expected"],
        "ordinary return or declared Never process.exit"
    );
    assert_eq!(report["system_exit_violation"]["actual"], "SystemExit");
}
