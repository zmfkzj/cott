use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::sync::atomic::{AtomicU64, Ordering};

use cott::hash::sha256_hex;
use cott::kotlin::KotlinOwner;
use cott::kotlin::provenance::KotlinGenerationRecord;

static NEXT_TEMP: AtomicU64 = AtomicU64::new(0);

struct TempDir {
    path: PathBuf,
}

impl TempDir {
    fn new() -> Self {
        let mut id = NEXT_TEMP.fetch_add(1, Ordering::Relaxed);
        loop {
            let path = std::env::temp_dir().join(format!(
                "cott-kotlin-generation-{}-{id}",
                std::process::id()
            ));
            match fs::create_dir(&path) {
                Ok(()) => return Self { path },
                Err(error) if error.kind() == io::ErrorKind::AlreadyExists => id += 1,
                Err(error) => panic!("create Kotlin generation fixture: {error}"),
            }
        }
    }
}

impl Drop for TempDir {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.path);
    }
}

fn project(source: &str) -> TempDir {
    let temp = TempDir::new();
    fs::create_dir_all(temp.path.join("src")).expect("Cott source directory");
    fs::create_dir_all(temp.path.join("kotlin")).expect("Kotlin source directory");
    fs::write(
        temp.path.join("cott.toml"),
        r#"[project]
name = "generation-fixture"
version = "0.1.0"
source = "src"

[target.kotlin]
source = "kotlin"
generated = "generated/kotlin"
compiler = "kotlinc-never-run"
java = "java-never-run"
jvm_target = 17
runtime_validation = "boundary"
"#,
    )
    .expect("Kotlin manifest");
    fs::write(temp.path.join("src/sample.cott"), source).expect("Cott source");
    temp
}

fn write_exec(path: &Path, body: &str) {
    fs::write(path, body).expect("write fixture executable");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        fs::set_permissions(path, fs::Permissions::from_mode(0o755))
            .expect("make fixture executable");
    }
}

fn tool_path(root: &Path) -> PathBuf {
    let tools = root.join("tools");
    fs::create_dir(&tools).expect("tool directory");
    tools
}

fn command(root: &Path, tools: &Path, arguments: &[&str]) -> Output {
    let path = std::env::join_paths([tools, Path::new("/usr/bin"), Path::new("/bin")])
        .expect("fixture PATH");
    Command::new(env!("CARGO_BIN_EXE_cott"))
        .args(arguments)
        .args(["--project"])
        .arg(root)
        .env("PATH", path)
        .output()
        .expect("run cott command")
}

fn prompt(root: &Path, tools: &Path, symbol: &str) -> serde_json::Value {
    let output = command(root, tools, &["prompt", symbol, "--format", "json"]);
    assert!(
        output.status.success(),
        "stdout: {}\nstderr: {}",
        String::from_utf8_lossy(&output.stdout),
        String::from_utf8_lossy(&output.stderr)
    );
    serde_json::from_slice(&output.stdout).expect("Kotlin prompt JSON")
}

fn generation_record(root: &Path) -> KotlinGenerationRecord {
    KotlinGenerationRecord::parse(
        &fs::read(root.join("generated/generation.json")).expect("Kotlin generation record"),
    )
    .expect("valid Kotlin generation record")
}

fn fenced_prompt_section<'a>(prompt: &'a str, heading: &str, language: &str) -> &'a str {
    let opening = format!("{heading}\n```{language}\n");
    prompt
        .split_once(&opening)
        .unwrap_or_else(|| panic!("missing prompt section {heading}"))
        .1
        .split_once("\n```\n")
        .unwrap_or_else(|| panic!("unterminated prompt section {heading}"))
        .0
}

const CAPTURED_PROMPT_PREFIX: &str = "// cott-test-prompt-json: ";

fn captured_prompt(source: &str) -> String {
    let mut captures = source
        .lines()
        .filter_map(|line| line.strip_prefix(CAPTURED_PROMPT_PREFIX));
    let encoded = captures.next().expect("candidate prompt capture comment");
    assert!(
        captures.next().is_none(),
        "candidate contained multiple prompt capture comments"
    );
    serde_json::from_str(encoded).expect("JSON-encoded candidate prompt")
}

#[test]
fn prompt_is_scoped_hashed_and_does_not_invoke_tools() {
    let project = project(
        "module sample\n\nfn alpha[const N: U32](values: Array[I32, N]) -> I32\n\nfn beta(value: I32) -> I32\n",
    );
    let tools = tool_path(&project.path);
    let marker = project.path.join("tool-was-invoked");
    for name in ["kotlinc-never-run", "java-never-run", "omp"] {
        write_exec(
            &tools.join(name),
            &format!(
                "#!/bin/sh\nprintf invoked > '{}'\nexit 77\n",
                marker.display()
            ),
        );
    }

    let report = prompt(&project.path, &tools, "sample.alpha");
    assert_eq!(report["symbol"], "sample.alpha");
    assert_eq!(report["generation_required"], true);
    let text = report["prompt"].as_str().expect("prompt text");
    assert!(text.contains("implementation.kt"));
    assert!(text.contains("alpha"));
    assert!(text.contains("N : cott_runtime.CottConst"));
    assert!(text.contains("_cott_const_N: N"));
    let formal: serde_json::Value = serde_json::from_str(
        text.split_once("```json\n")
            .expect("formal declarations JSON")
            .1
            .split_once("\n```")
            .expect("closed formal declarations JSON")
            .0,
    )
    .expect("valid formal declarations JSON");
    assert!(
        formal["sample"]["declarations"]
            .as_array()
            .expect("selected module declarations")
            .iter()
            .any(|declaration| declaration["name"] == "sample.alpha"),
        "selected callable is missing from formal declarations"
    );
    assert!(
        !text.contains("sample.beta"),
        "unrelated callable leaked into prompt"
    );
    assert_eq!(
        report["prompt_hash"],
        format!("sha256:{}", sha256_hex(text.as_bytes()))
    );
    assert!(
        report["intent_hash"]
            .as_str()
            .is_some_and(|hash| hash.starts_with("sha256:") && hash.len() == 71)
    );
    assert!(!marker.exists(), "prompt invoked a compiler or provider");
    assert!(!project.path.join("generated").exists());
}

#[test]
fn source_retry_uses_real_feedback_and_keeps_the_frozen_initial_hash() {
    let project =
        project("module sample\n\nfn alpha(value: I32) -> I32\n\nfn beta(value: I32) -> I32\n");
    let tools = tool_path(&project.path);
    write_exec(
        &tools.join("omp"),
        r#"#!/usr/bin/python3
import json
import pathlib
import sys

if sys.argv[1:] == ['--version']:
    print('omp/17.2.12')
    raise SystemExit(0)
if not sys.argv[-1].startswith('@'):
    print('missing prompt file', file=sys.stderr)
    raise SystemExit(64)
prompt = pathlib.Path(sys.argv[-1][1:]).read_text(encoding='utf-8')

def section(heading, language):
    opening = heading + '\n```' + language + '\n'
    try:
        return prompt.split(opening, 1)[1].split('\n```\n', 1)[0]
    except IndexError:
        print('malformed generation prompt', file=sys.stderr)
        raise SystemExit(64)

candidate = section('# Existing candidate', 'kotlin')
feedback = section('# Actual validation feedback', 'text')
declaration = next(
    (line.strip() for line in candidate.splitlines() if ' fun alpha(' in line),
    '',
)
if candidate.strip() == '(none)' and feedback.strip() == '(none)':
    visibility = 'public'
    expression = 'value'
elif (
    declaration == 'public fun alpha(value: kotlin.Int): kotlin.Int {'
    and feedback.strip() != '(none)'
):
    visibility = 'internal'
    expression = 'value + 1'
else:
    print('unexpected source-audit attempt state', file=sys.stderr)
    raise SystemExit(65)

source = (
    'package cott_impl.sample\n\n'
    + visibility
    + ' fun alpha(value: kotlin.Int): kotlin.Int {\n'
    + '    return '
    + expression
    + '\n}\n'
    + '// cott-test-prompt-json: '
    + json.dumps(prompt, ensure_ascii=False, separators=(',', ':'))
    + '\n'
)
pathlib.Path('implementation.kt').write_text(source, encoding='utf-8')
"#,
    );
    let initial = prompt(&project.path, &tools, "sample.alpha");

    let generated = command(
        &project.path,
        &tools,
        &[
            "generate",
            "sample.alpha",
            "--agent",
            "omp",
            "--target",
            "kotlin",
        ],
    );
    assert!(
        generated.status.success(),
        "{}",
        String::from_utf8_lossy(&generated.stderr)
    );
    let source_path = project.path.join("kotlin/cott_impl/sample/alpha.kt");
    let source = fs::read_to_string(&source_path).expect("checkpointed source");
    let source_retry = captured_prompt(&source);
    let rejected = fenced_prompt_section(&source_retry, "# Existing candidate", "kotlin");
    let audit_feedback =
        fenced_prompt_section(&source_retry, "# Actual validation feedback", "text");
    assert!(
        rejected.contains("public fun alpha"),
        "source retry did not receive the rejected visibility"
    );
    assert_ne!(
        audit_feedback.trim(),
        "(none)",
        "source retry did not receive the source-audit failure"
    );
    let facade = fs::read_to_string(project.path.join("generated/kotlin/sample/Facade.kt"))
        .expect("partially resolved facade");
    assert!(facade.contains("alpha("));
    assert!(
        !facade.contains("beta("),
        "pending callable leaked into facade"
    );
    assert!(
        source
            .lines()
            .any(|line| { line.trim() == "internal fun alpha(value: kotlin.Int): kotlin.Int {" })
    );
    assert!(
        !source
            .lines()
            .any(|line| { line.trim() == "public fun alpha(value: kotlin.Int): kotlin.Int {" })
    );

    let record = generation_record(&project.path);
    assert!(!record.current.verified);
    assert_eq!(record.current.unresolved, ["sample.beta".to_owned()]);
    assert_eq!(record.current.implementations.len(), 1);
    assert_eq!(
        record.current.implementations[0].cott_symbol,
        "sample.alpha"
    );
    assert_eq!(
        record.current.implementations[0].owner,
        KotlinOwner::Agent,
        "accepted source was not recorded as agent-owned"
    );
    assert_eq!(record.current.agent_runs.len(), 1);
    assert_eq!(
        record.current.agent_runs[0].prompt_hash,
        initial["prompt_hash"]
            .as_str()
            .expect("initial prompt hash")
    );
    assert_eq!(
        record.current.agent_runs[0].implementation_hash,
        format!("sha256:{}", sha256_hex(source.as_bytes()))
    );
    assert!(
        !project
            .path
            .join("generated/library/cott-module.jar")
            .exists(),
        "an incomplete checkpoint must not fabricate compiler evidence"
    );

    write_exec(
        &tools.join("omp"),
        r#"#!/bin/sh
if [ "$1" = "--version" ]; then echo omp/17.2.12; exit 0; fi
last=
for arg; do last=$arg; done
case "$last" in
  @*) prompt=$(cat "${last#@}") || exit 64 ;;
  *) echo 'missing prompt file' >&2; exit 64 ;;
esac
case "$prompt" in
  *'Selected Cott symbol: sample.beta'*) ;;
  *) echo 'targeted validation retry regenerated an out-of-scope callable' >&2; exit 65 ;;
esac
printf '%s\n' 'package cott_impl.sample' '' 'internal fun beta(value: kotlin.Int): kotlin.Int {' '    return value' '}' > implementation.kt
"#,
    );
    let beta_prompt = prompt(&project.path, &tools, "sample.beta");
    let completed = command(
        &project.path,
        &tools,
        &[
            "generate",
            "sample.beta",
            "--agent",
            "omp",
            "--target",
            "kotlin",
        ],
    );
    assert_eq!(completed.status.code(), Some(5));
    let failed_complete = generation_record(&project.path);
    assert_eq!(
        failed_complete.current.unresolved,
        ["sample.alpha".to_owned(), "sample.beta".to_owned()],
        "unattributed whole-target failure must conservatively pend every agent binding"
    );
    let beta_run = failed_complete
        .current
        .agent_runs
        .iter()
        .find(|run| run.symbol == "sample.beta")
        .expect("beta agent run");
    assert_eq!(
        beta_run.prompt_hash,
        beta_prompt["prompt_hash"]
            .as_str()
            .expect("beta initial prompt hash")
    );
    assert_eq!(
        fs::read(&source_path).expect("accepted alpha source after conservative pending"),
        source.as_bytes(),
        "targeted validation repair changed an out-of-scope accepted source"
    );
}

#[test]
fn verifier_failure_feedback_checkpoint_and_stale_docs_require_regeneration() {
    let project =
        project("module sample\n\nfn alpha(value: I32) -> I32:\n    ensures result == value\n");
    let tools = tool_path(&project.path);
    write_exec(
        &tools.join("omp"),
        r#"#!/usr/bin/python3
import json
import pathlib
import sys

if sys.argv[1:] == ['--version']:
    print('omp/17.2.12')
    raise SystemExit(0)
if not sys.argv[-1].startswith('@'):
    print('missing prompt file', file=sys.stderr)
    raise SystemExit(64)
prompt = pathlib.Path(sys.argv[-1][1:]).read_text(encoding='utf-8')

def section(text, heading, language):
    opening = heading + '\n```' + language + '\n'
    try:
        return text.split(opening, 1)[1].split('\n```\n', 1)[0]
    except IndexError:
        print('malformed generation prompt', file=sys.stderr)
        raise SystemExit(64)

def return_line(source):
    return next(
        (line.strip() for line in source.splitlines() if line.strip().startswith('return ')),
        None,
    )

def captured(source):
    prefix = '// cott-test-prompt-json: '
    values = [
        line[len(prefix):]
        for line in source.splitlines()
        if line.startswith(prefix)
    ]
    if len(values) != 1:
        print('candidate prompt capture is not singular', file=sys.stderr)
        raise SystemExit(65)
    return json.loads(values[0])

candidate = section(prompt, '# Existing candidate', 'kotlin')
feedback = section(prompt, '# Actual validation feedback', 'text')
declaration = next(
    (line.strip() for line in candidate.splitlines() if ' fun alpha(' in line),
    '',
)
if candidate.strip() == '(none)' and feedback.strip() == '(none)':
    expression = 'value'
elif (
    declaration == 'internal fun alpha(value: kotlin.Int): kotlin.Int {'
    and feedback.strip() != '(none)'
    and return_line(candidate) == 'return value'
):
    expression = '(value)'
elif (
    declaration == 'internal fun alpha(value: kotlin.Int): kotlin.Int {'
    and feedback.strip() != '(none)'
    and return_line(candidate) == 'return (value)'
):
    prior_candidate = section(
        captured(candidate),
        '# Existing candidate',
        'kotlin',
    )
    if return_line(prior_candidate) != 'return value':
        print('unexpected extra verifier repair', file=sys.stderr)
        raise SystemExit(65)
    expression = '(value)'
else:
    print('unexpected verifier attempt state', file=sys.stderr)
    raise SystemExit(65)

source = (
    'package cott_impl.sample\n\n'
    + 'internal fun alpha(value: kotlin.Int): kotlin.Int {\n'
    + '    return '
    + expression
    + '\n}\n'
    + '// cott-test-prompt-json: '
    + json.dumps(prompt, ensure_ascii=False, separators=(',', ':'))
    + '\n'
)
pathlib.Path('implementation.kt').write_text(source, encoding='utf-8')
"#,
    );
    let initial = prompt(&project.path, &tools, "sample.alpha");

    let generated = command(
        &project.path,
        &tools,
        &[
            "generate",
            "sample.alpha",
            "--agent",
            "omp",
            "--target",
            "kotlin",
        ],
    );
    assert_eq!(generated.status.code(), Some(5));
    let stderr = String::from_utf8_lossy(&generated.stderr);
    assert!(stderr.contains("kotlinc-never-run"), "{stderr}");
    let source_path = project.path.join("kotlin/cott_impl/sample/alpha.kt");
    let old_source = fs::read_to_string(&source_path).expect("verifier-failed source checkpoint");
    let second_retry = captured_prompt(&old_source);
    let second_candidate = fenced_prompt_section(&second_retry, "# Existing candidate", "kotlin");
    let first_retry = captured_prompt(second_candidate);
    let first_candidate = fenced_prompt_section(&first_retry, "# Existing candidate", "kotlin");
    assert_eq!(
        captured_prompt(first_candidate),
        initial["prompt"].as_str().expect("initial prompt text"),
        "initial provider attempt did not receive the frozen prompt"
    );
    for retry in [&first_retry, &second_retry] {
        let feedback = fenced_prompt_section(retry, "# Actual validation feedback", "text");
        assert!(
            feedback.contains("kotlinc-never-run"),
            "verifier retry omitted the configured compiler failure"
        );
    }
    for candidate in [first_candidate, second_candidate, old_source.as_str()] {
        assert!(
            candidate.lines().any(|line| {
                line.trim() == "internal fun alpha(value: kotlin.Int): kotlin.Int {"
            }),
            "verifier repair changed the canonical Kotlin signature"
        );
    }
    assert!(
        first_candidate
            .lines()
            .any(|line| line.trim() == "return value")
    );
    assert!(
        second_candidate
            .lines()
            .any(|line| line.trim() == "return (value)")
    );
    assert!(
        old_source
            .lines()
            .any(|line| line.trim() == "return (value)")
    );
    assert_ne!(
        first_candidate, second_candidate,
        "first verifier repair did not become the next retry candidate"
    );
    assert_ne!(
        second_candidate,
        old_source.as_str(),
        "second verifier retry did not preserve changing authenticated candidate data"
    );

    let record = generation_record(&project.path);
    assert!(!record.current.verified);
    assert_eq!(record.current.unresolved, ["sample.alpha".to_owned()]);
    assert_eq!(record.current.implementations.len(), 1);
    assert_eq!(record.current.agent_runs.len(), 1);
    assert_eq!(
        record.current.agent_runs[0].prompt_hash,
        initial["prompt_hash"]
            .as_str()
            .expect("initial prompt hash")
    );
    assert!(
        !project
            .path
            .join("generated/library/cott-module.jar")
            .exists(),
        "failed real verification must not produce compiler evidence"
    );

    fs::write(
        project.path.join("src/sample.cott"),
        "module sample\n\nfn alpha(value: I32) -> I32:\n    doc \"\"\"New documentation revision for the same formal contract.\"\"\"\n    ensures result == value\n\nfn beta(value: I32) -> I32\n",
    )
    .expect("documentation-only contract revision and unresolved sibling");
    let without_agent = command(
        &project.path,
        &tools,
        &["generate", "sample.alpha", "--target", "kotlin"],
    );
    assert_eq!(
        without_agent.status.code(),
        Some(2),
        "{}",
        String::from_utf8_lossy(&without_agent.stderr)
    );
    assert_eq!(
        fs::read_to_string(&source_path).expect("pending source after refused reuse"),
        old_source,
        "syntax-valid pending source was blindly refreshed after intent changed"
    );

    write_exec(
        &tools.join("omp"),
        r#"#!/usr/bin/python3
import json
import pathlib
import sys

if sys.argv[1:] == ['--version']:
    print('omp/17.2.12')
    raise SystemExit(0)
if not sys.argv[-1].startswith('@'):
    print('missing prompt file', file=sys.stderr)
    raise SystemExit(64)
prompt = pathlib.Path(sys.argv[-1][1:]).read_text(encoding='utf-8')

def section(heading, language):
    opening = heading + '\n```' + language + '\n'
    try:
        return prompt.split(opening, 1)[1].split('\n```\n', 1)[0]
    except IndexError:
        print('malformed generation prompt', file=sys.stderr)
        raise SystemExit(64)

candidate = section('# Existing candidate', 'kotlin')
feedback = section('# Actual validation feedback', 'text')
declaration = next(
    (line.strip() for line in candidate.splitlines() if ' fun alpha(' in line),
    '',
)
if (
    candidate.strip() == '(none)'
    or feedback.strip() != '(none)'
    or declaration != 'internal fun alpha(value: kotlin.Int): kotlin.Int {'
):
    print('unexpected stale-intent regeneration state', file=sys.stderr)
    raise SystemExit(65)

source = (
    'package cott_impl.sample\n\n'
    + 'internal fun alpha(value: kotlin.Int): kotlin.Int {\n'
    + '    return value + 0\n}\n'
    + '// cott-test-prompt-json: '
    + json.dumps(prompt, ensure_ascii=False, separators=(',', ':'))
    + '\n'
)
pathlib.Path('implementation.kt').write_text(source, encoding='utf-8')
"#,
    );
    let revised = prompt(&project.path, &tools, "sample.alpha");
    assert_ne!(revised["prompt_hash"], initial["prompt_hash"]);
    let regenerated = command(
        &project.path,
        &tools,
        &[
            "generate",
            "sample.alpha",
            "--agent",
            "omp",
            "--target",
            "kotlin",
        ],
    );
    assert!(
        regenerated.status.success(),
        "{}",
        String::from_utf8_lossy(&regenerated.stderr)
    );
    let source = fs::read_to_string(&source_path).expect("regenerated current-intent source");
    let captured_revised = captured_prompt(&source);
    assert_eq!(
        captured_revised,
        revised["prompt"].as_str().expect("revised prompt text"),
        "generation did not use the frozen revised prompt"
    );
    assert!(
        captured_revised.contains("New documentation revision"),
        "regeneration prompt omitted the revised current intent"
    );
    assert_eq!(
        fenced_prompt_section(&captured_revised, "# Existing candidate", "kotlin"),
        old_source.as_str(),
        "regeneration prompt omitted the pending source checkpoint"
    );
    assert_ne!(
        source, old_source,
        "current-intent regeneration reused the stale implementation"
    );
    let revised_record = generation_record(&project.path);
    assert!(!revised_record.current.verified);
    assert_eq!(
        revised_record.current.unresolved,
        ["sample.beta".to_owned()]
    );
    assert_eq!(
        revised_record.current.agent_runs[0].prompt_hash,
        revised["prompt_hash"]
            .as_str()
            .expect("revised initial prompt hash")
    );
}

#[test]
fn source_ordered_waves_keep_initial_hashes_and_resume_only_failed_work() {
    let project = project(
        "module sample\n\n\
fn zeta(value: I32) -> I32\n\n\
fn alpha(value: I32) -> I32\n\n\
fn gamma(value: I32) -> I32\n\n\
fn delta(value: I32) -> I32\n",
    );
    let tools = tool_path(&project.path);
    write_exec(
        &tools.join("omp"),
        r#"#!/bin/sh
if [ "$1" = "--version" ]; then echo omp/17.2.12; exit 0; fi
last=
for arg; do last=$arg; done
case "$last" in
  @*) prompt=$(cat "${last#@}") || exit 64 ;;
  *) echo 'missing prompt file' >&2; exit 64 ;;
esac
case "$prompt" in
  *'Selected Cott symbol: sample.zeta'*) name=zeta ;;
  *'Selected Cott symbol: sample.alpha'*) name=alpha ;;
  *'Selected Cott symbol: sample.gamma'*) echo 'forced gamma provider failure' >&2; exit 17 ;;
  *'Selected Cott symbol: sample.delta'*) name=delta ;;
  *) echo 'unexpected Kotlin prompt' >&2; exit 64 ;;
esac
printf '%s\n' 'package cott_impl.sample' '' "internal fun $name(value: kotlin.Int): kotlin.Int {" '    return value' '}' > implementation.kt
"#,
    );
    let zeta = prompt(&project.path, &tools, "sample.zeta");
    let alpha = prompt(&project.path, &tools, "sample.alpha");

    let generated = command(
        &project.path,
        &tools,
        &[
            "generate", "--agent", "omp", "--target", "kotlin", "-j", "1",
        ],
    );
    assert_eq!(generated.status.code(), Some(5));

    let first = generation_record(&project.path);
    assert_eq!(
        first.current.unresolved,
        ["sample.delta".to_owned(), "sample.gamma".to_owned()]
    );
    assert_eq!(
        first
            .current
            .implementations
            .iter()
            .map(|binding| binding.cott_symbol.as_str())
            .collect::<Vec<_>>(),
        ["sample.alpha", "sample.zeta"]
    );
    let first_hashes = first
        .current
        .agent_runs
        .iter()
        .map(|run| (run.symbol.as_str(), run.prompt_hash.as_str()))
        .collect::<std::collections::BTreeMap<_, _>>();
    assert_eq!(
        first_hashes["sample.zeta"],
        zeta["prompt_hash"].as_str().expect("zeta prompt hash")
    );
    assert_eq!(
        first_hashes["sample.alpha"],
        alpha["prompt_hash"].as_str().expect("alpha prompt hash")
    );
    assert!(
        project
            .path
            .join("kotlin/cott_impl/sample/zeta.kt")
            .exists()
    );
    assert!(
        project
            .path
            .join("kotlin/cott_impl/sample/alpha.kt")
            .exists()
    );
    assert!(
        !project
            .path
            .join("kotlin/cott_impl/sample/gamma.kt")
            .exists()
    );
    assert!(
        !project
            .path
            .join("kotlin/cott_impl/sample/delta.kt")
            .exists(),
        "lexical work ordering ran delta before the source-ordered failure"
    );

    write_exec(
        &tools.join("omp"),
        r#"#!/bin/sh
if [ "$1" = "--version" ]; then echo omp/17.2.12; exit 0; fi
last=
for arg; do last=$arg; done
case "$last" in
  @*) prompt=$(cat "${last#@}") || exit 64 ;;
  *) echo 'missing prompt file' >&2; exit 64 ;;
esac
case "$prompt" in
  *'Selected Cott symbol: sample.gamma'*) ;;
  *) echo 'partial resume regenerated an already accepted or unselected callable' >&2; exit 65 ;;
esac
printf '%s\n' 'package cott_impl.sample' '' 'internal fun gamma(value: kotlin.Int): kotlin.Int {' '    return value' '}' > implementation.kt
"#,
    );
    let resumed = command(
        &project.path,
        &tools,
        &[
            "generate",
            "sample.gamma",
            "--agent",
            "omp",
            "--target",
            "kotlin",
        ],
    );
    assert!(
        resumed.status.success(),
        "{}",
        String::from_utf8_lossy(&resumed.stderr)
    );
    let second = generation_record(&project.path);
    assert_eq!(second.current.unresolved, ["sample.delta".to_owned()]);
    assert_eq!(
        second
            .current
            .implementations
            .iter()
            .map(|binding| binding.cott_symbol.as_str())
            .collect::<Vec<_>>(),
        ["sample.alpha", "sample.gamma", "sample.zeta"]
    );
    let second_hashes = second
        .current
        .agent_runs
        .iter()
        .map(|run| (run.symbol.as_str(), run.prompt_hash.as_str()))
        .collect::<std::collections::BTreeMap<_, _>>();
    assert_eq!(
        second_hashes["sample.zeta"],
        zeta["prompt_hash"].as_str().expect("zeta prompt hash")
    );
    assert_eq!(
        second_hashes["sample.alpha"],
        alpha["prompt_hash"].as_str().expect("alpha prompt hash")
    );
    assert!(
        project
            .path
            .join("kotlin/cott_impl/sample/gamma.kt")
            .exists()
    );
    assert!(
        !project
            .path
            .join("kotlin/cott_impl/sample/delta.kt")
            .exists()
    );
    assert!(!second.current.verified);
    assert!(
        !project
            .path
            .join("generated/library/cott-module.jar")
            .exists(),
        "partial generation must not fabricate compiler evidence"
    );
}
