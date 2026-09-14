use std::collections::BTreeMap;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::sync::atomic::{AtomicU64, Ordering};

use cott::dart::DartOwner;
use cott::dart::provenance::DartGenerationRecord;
use cott::hash::sha256_hex;

static NEXT_TEMP: AtomicU64 = AtomicU64::new(0);

struct TempDir {
    path: PathBuf,
}

impl TempDir {
    fn new() -> Self {
        let mut id = NEXT_TEMP.fetch_add(1, Ordering::Relaxed);
        loop {
            let path = std::env::temp_dir()
                .join(format!("cott-dart-generation-{}-{id}", std::process::id()));
            match fs::create_dir(&path) {
                Ok(()) => return Self { path },
                Err(error) if error.kind() == io::ErrorKind::AlreadyExists => id += 1,
                Err(error) => panic!("create Dart generation fixture: {error}"),
            }
        }
    }
}

impl Drop for TempDir {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.path);
    }
}

fn project(source: &str, rules: Option<&str>) -> TempDir {
    let temp = TempDir::new();
    fs::create_dir_all(temp.path.join("src")).expect("Cott source directory");
    fs::create_dir_all(temp.path.join("dart")).expect("Dart source directory");
    let generator = if rules.is_some() {
        "\n[generator]\nrules = \"generator.rules\"\n"
    } else {
        ""
    };
    fs::write(
        temp.path.join("cott.toml"),
        format!(
            r#"[project]
name = "generation_fixture"
version = "0.1.0"
source = "src"
{generator}
[target.dart]
source = "dart"
generated = "generated/dart"
sdk = "dart-never-run"
runtime_validation = "boundary"
"#
        ),
    )
    .expect("Dart manifest");
    fs::write(temp.path.join("src/sample.cott"), source).expect("Cott source");
    if let Some(rules) = rules {
        fs::write(temp.path.join("generator.rules"), rules).expect("generator rules");
    }
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
    assert!(output.stderr.is_empty(), "prompt wrote stderr");
    serde_json::from_slice(&output.stdout).expect("Dart prompt JSON")
}

fn generation_record(root: &Path) -> DartGenerationRecord {
    DartGenerationRecord::parse(
        &fs::read(root.join("generated/generation.json")).expect("Dart generation record"),
    )
    .expect("valid Dart generation record")
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
fn prompt_is_provider_free_exact_scoped_and_hashed() {
    let project = project(
        "module sample\n\nfn alpha(value: I32) -> I32\n\nfn beta(value: I32) -> I32\n",
        None,
    );
    let tools = tool_path(&project.path);
    for name in ["dart-never-run", "omp"] {
        write_exec(
            &tools.join(name),
            "#!/bin/sh\necho 'prompt unexpectedly invoked a tool' >&2\nexit 77\n",
        );
    }

    let report = prompt(&project.path, &tools, "sample.alpha");
    let fields = report
        .as_object()
        .expect("prompt report object")
        .keys()
        .map(String::as_str)
        .collect::<std::collections::BTreeSet<_>>();
    assert_eq!(
        fields,
        [
            "context",
            "generation_required",
            "intent_hash",
            "prompt",
            "prompt_hash",
            "symbol",
        ]
        .into_iter()
        .collect()
    );
    assert_eq!(report["symbol"], "sample.alpha");
    assert_eq!(report["generation_required"], true);
    let text = report["prompt"].as_str().expect("prompt text");
    assert!(text.contains("implementation.dart"));
    assert!(text.contains("int _cott_sample_alpha(int value)"));
    assert!(text.contains("package:generation_fixture/cott_runtime.dart"));
    assert!(text.contains("\"name\": \"sample.alpha\""));
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
    assert!(!project.path.join("generated").exists());
}

#[test]
fn source_audit_retry_keeps_frozen_hash_and_checkpoints_original_bytes() {
    let project = project(
        "module sample\n\nfn alpha(value: I32) -> I32\n\nfn beta(value: I32) -> I32\n",
        None,
    );
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
        print('malformed Dart generation prompt', file=sys.stderr)
        raise SystemExit(64)

candidate = section('# Existing candidate', 'dart')
feedback = section('# Actual validation feedback', 'text')
if candidate.strip() == '(none)' and feedback.strip() == '(none)':
    name = 'alpha'
elif 'int alpha(int value)' in candidate and feedback.strip() != '(none)':
    name = '_cott_sample_alpha'
else:
    print('unexpected source-audit attempt state', file=sys.stderr)
    raise SystemExit(65)
source = (
    'int ' + name + '(int value) {\n'
    '  return value + 1;\n'
    '}\n'
    '// cott-test-prompt-json: '
    + json.dumps(prompt, ensure_ascii=False, separators=(',', ':'))
    + '\n'
)
pathlib.Path('implementation.dart').write_text(source, encoding='utf-8')
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
            "dart",
        ],
    );
    assert!(
        generated.status.success(),
        "{}",
        String::from_utf8_lossy(&generated.stderr)
    );
    let source_path = project.path.join("dart/cott_impl/sample/alpha.dart");
    let source = fs::read_to_string(&source_path).expect("checkpointed authored source");
    assert!(source.contains("int _cott_sample_alpha(int value)"));
    let retry_prompt = captured_prompt(&source);
    let rejected = fenced_prompt_section(&retry_prompt, "# Existing candidate", "dart");
    let feedback = fenced_prompt_section(&retry_prompt, "# Actual validation feedback", "text");
    assert!(rejected.contains("int alpha(int value)"));
    assert_eq!(
        captured_prompt(rejected),
        initial["prompt"].as_str().expect("initial frozen prompt")
    );
    assert!(feedback.contains("Dart source audit failed"));

    let record = generation_record(&project.path);
    assert!(!record.current.verified);
    assert!(record.last_verified.is_none());
    assert_eq!(record.current.unresolved, ["sample.beta".to_owned()]);
    assert_eq!(record.current.implementations.len(), 1);
    assert_eq!(record.current.implementations[0].owner, DartOwner::Agent);
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
    assert_eq!(
        record.current.implementations[0].content_hash,
        format!("sha256:{}", sha256_hex(source.as_bytes()))
    );
    let managed = fs::read_to_string(
        project
            .path
            .join("generated/dart/lib/src/cott_impl/sample/alpha.dart"),
    )
    .expect("compiler-owned private part");
    assert!(
        managed.starts_with("part of 'package:generation_fixture/src/wrappers/sample/alpha.dart';")
    );
    assert_ne!(
        sha256_hex(managed.as_bytes()),
        sha256_hex(source.as_bytes()),
        "original authored bytes must not be confused with transformed part bytes"
    );
}

#[test]
fn changed_frozen_rules_require_regeneration_from_the_authenticated_checkpoint() {
    let project = project(
        "module sample\n\nfn alpha(value: I32) -> I32\n\nfn beta(value: I32) -> I32\n",
        Some("Keep the value unchanged.\n"),
    );
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
        print('malformed Dart generation prompt', file=sys.stderr)
        raise SystemExit(64)

candidate = section('# Existing candidate', 'dart')
feedback = section('# Actual validation feedback', 'text')
rules = section('# Project rules', 'text')
if candidate.strip() == '(none)' and 'Keep the value unchanged.' in rules:
    expression = 'value'
elif (
    '_cott_sample_alpha' in candidate
    and 'Use an explicit neutral addition.' in rules
    and feedback.strip() == '(none)'
):
    expression = 'value + 0'
else:
    print('unexpected prompt-derived regeneration state', file=sys.stderr)
    raise SystemExit(65)
source = (
    'int _cott_sample_alpha(int value) {\n'
    '  return ' + expression + ';\n'
    '}\n'
    '// cott-test-prompt-json: '
    + json.dumps(prompt, ensure_ascii=False, separators=(',', ':'))
    + '\n'
)
pathlib.Path('implementation.dart').write_text(source, encoding='utf-8')
"#,
    );

    let initial = prompt(&project.path, &tools, "sample.alpha");
    let first = command(
        &project.path,
        &tools,
        &[
            "generate",
            "sample.alpha",
            "--agent",
            "omp",
            "--target",
            "dart",
        ],
    );
    assert!(
        first.status.success(),
        "{}",
        String::from_utf8_lossy(&first.stderr)
    );
    let source_path = project.path.join("dart/cott_impl/sample/alpha.dart");
    let old_source = fs::read_to_string(&source_path).expect("first authored checkpoint");

    fs::write(
        project.path.join("generator.rules"),
        "Use an explicit neutral addition.\n",
    )
    .expect("change generator rules between invocations");
    let revised = prompt(&project.path, &tools, "sample.alpha");
    assert_eq!(revised["generation_required"], true);
    assert_ne!(revised["intent_hash"], initial["intent_hash"]);
    assert_ne!(revised["prompt_hash"], initial["prompt_hash"]);
    assert_eq!(
        fenced_prompt_section(
            revised["prompt"].as_str().expect("revised prompt"),
            "# Existing candidate",
            "dart"
        ),
        old_source
    );

    let refused = command(
        &project.path,
        &tools,
        &["generate", "sample.alpha", "--target", "dart"],
    );
    assert_eq!(refused.status.code(), Some(2));
    assert_eq!(
        fs::read_to_string(&source_path).expect("source after refused stale reuse"),
        old_source
    );
    let provider = fs::read_to_string(tools.join("omp")).expect("prompt-derived provider");
    write_exec(
        &tools.join("omp"),
        "#!/bin/sh\nif [ \"$1\" = \"--version\" ]; then echo omp/17.2.12; exit 0; fi\necho 'forced provider failure' >&2\nexit 17\n",
    );
    let failed_repair = command(
        &project.path,
        &tools,
        &[
            "generate",
            "sample.alpha",
            "--agent",
            "omp",
            "--target",
            "dart",
        ],
    );
    assert_eq!(failed_repair.status.code(), Some(5));
    assert_eq!(
        fs::read_to_string(&source_path).expect("stale checkpoint after provider failure"),
        old_source
    );
    let pending = generation_record(&project.path);
    assert_eq!(
        pending.current.unresolved,
        ["sample.alpha".to_owned(), "sample.beta".to_owned()]
    );
    assert_eq!(pending.current.implementations.len(), 1);
    assert_eq!(pending.current.agent_runs.len(), 1);
    assert_eq!(
        pending.current.agent_runs[0].prompt_hash,
        initial["prompt_hash"]
            .as_str()
            .expect("old authenticated prompt hash")
    );
    write_exec(&tools.join("omp"), &provider);

    let regenerated = command(
        &project.path,
        &tools,
        &[
            "generate",
            "sample.alpha",
            "--agent",
            "omp",
            "--target",
            "dart",
        ],
    );
    assert!(
        regenerated.status.success(),
        "{}",
        String::from_utf8_lossy(&regenerated.stderr)
    );
    let new_source = fs::read_to_string(&source_path).expect("regenerated authored source");
    assert!(new_source.contains("return value + 0;"));
    assert_ne!(new_source, old_source);
    assert_eq!(
        captured_prompt(&new_source),
        revised["prompt"].as_str().expect("frozen revised prompt")
    );
    let record = generation_record(&project.path);
    assert!(!record.current.verified);
    assert_eq!(record.current.unresolved, ["sample.beta".to_owned()]);
    assert_eq!(
        record.current.agent_runs[0].prompt_hash,
        revised["prompt_hash"]
            .as_str()
            .expect("revised prompt hash")
    );
}

#[test]
fn source_ordered_parallel_waves_finish_the_failed_wave_and_stop_later_work() {
    let project = project(
        "module sample\n\n\
fn zeta(value: I32) -> I32\n\n\
fn alpha(value: I32) -> I32\n\n\
fn gamma(value: I32) -> I32\n\n\
fn delta(value: I32) -> I32\n\n\
fn epsilon(value: I32) -> I32\n",
        None,
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
  *'Selected Cott symbol: sample.epsilon'*) name=epsilon ;;
  *) echo 'unexpected Dart prompt' >&2; exit 64 ;;
esac
printf '%s\n' "int _cott_sample_${name}(int value) {" '  return value;' '}' > implementation.dart
"#,
    );
    let zeta = prompt(&project.path, &tools, "sample.zeta");
    let alpha = prompt(&project.path, &tools, "sample.alpha");
    let delta = prompt(&project.path, &tools, "sample.delta");

    let generated = command(
        &project.path,
        &tools,
        &["generate", "--agent", "omp", "--target", "dart", "-j", "2"],
    );
    assert_eq!(generated.status.code(), Some(5));

    let record = generation_record(&project.path);
    assert_eq!(
        record.current.unresolved,
        ["sample.epsilon".to_owned(), "sample.gamma".to_owned()]
    );
    assert_eq!(
        record
            .current
            .implementations
            .iter()
            .map(|binding| binding.cott_symbol.as_str())
            .collect::<Vec<_>>(),
        ["sample.alpha", "sample.delta", "sample.zeta"]
    );
    let hashes = record
        .current
        .agent_runs
        .iter()
        .map(|run| (run.symbol.as_str(), run.prompt_hash.as_str()))
        .collect::<BTreeMap<_, _>>();
    assert_eq!(
        hashes["sample.zeta"],
        zeta["prompt_hash"].as_str().expect("zeta prompt hash")
    );
    assert_eq!(
        hashes["sample.alpha"],
        alpha["prompt_hash"].as_str().expect("alpha prompt hash")
    );
    assert_eq!(
        hashes["sample.delta"],
        delta["prompt_hash"].as_str().expect("delta prompt hash")
    );
    for name in ["zeta", "alpha", "delta"] {
        assert!(
            project
                .path
                .join(format!("dart/cott_impl/sample/{name}.dart"))
                .exists(),
            "accepted source missing for {name}"
        );
    }
    assert!(
        !project
            .path
            .join("dart/cott_impl/sample/gamma.dart")
            .exists()
    );
    assert!(
        !project
            .path
            .join("dart/cott_impl/sample/epsilon.dart")
            .exists(),
        "a later source-order wave ran after a failure"
    );
    assert!(!record.current.verified);
    assert!(record.last_verified.is_none());
}

#[test]
fn absent_checkpoint_is_regenerable_but_tampered_ownership_fails_closed() {
    let project = project(
        "module sample\n\nfn alpha(value: I32) -> I32\n\nfn beta(value: I32) -> I32\n",
        None,
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
  *'Selected Cott symbol: sample.alpha'*) ;;
  *) echo 'unexpected Dart prompt' >&2; exit 64 ;;
esac
printf '%s\n' 'int _cott_sample_alpha(int value) {' '  return value;' '}' > implementation.dart
"#,
    );
    let generated = command(
        &project.path,
        &tools,
        &[
            "generate",
            "sample.alpha",
            "--agent",
            "omp",
            "--target",
            "dart",
        ],
    );
    assert!(
        generated.status.success(),
        "{}",
        String::from_utf8_lossy(&generated.stderr)
    );
    let source_path = project.path.join("dart/cott_impl/sample/alpha.dart");
    let original = fs::read(&source_path).expect("authenticated authored source");

    fs::remove_file(&source_path).expect("remove authenticated source");
    let absent = prompt(&project.path, &tools, "sample.alpha");
    assert_eq!(absent["generation_required"], true);
    assert_eq!(
        fenced_prompt_section(
            absent["prompt"].as_str().expect("absent-source prompt"),
            "# Existing candidate",
            "dart"
        ),
        "(none)"
    );

    fs::write(
        &source_path,
        "int _cott_sample_alpha(int value) {\n  return value + 1;\n}\n",
    )
    .expect("write unrecorded replacement");
    let tampered = command(
        &project.path,
        &tools,
        &["prompt", "sample.alpha", "--format", "json"],
    );
    assert_eq!(tampered.status.code(), Some(4));
    assert!(tampered.stderr.is_empty());
    let diagnostic = String::from_utf8(tampered.stdout).expect("UTF-8 diagnostic JSON");
    assert!(diagnostic.contains("COTT-D201"), "{diagnostic}");
    assert!(
        diagnostic
            .contains("does not match recorded Dart path, target, content identity, and ownership"),
        "{diagnostic}"
    );
    assert_ne!(
        fs::read(&source_path).expect("tampered source remains"),
        original,
        "failed prompt must not overwrite a tampered source"
    );
}

#[test]
fn whole_target_feedback_keeps_an_authenticated_repairable_checkpoint_unverified() {
    let project = project(
        "module sample\n\nfn alpha(value: I32) -> I32:\n    ensures result == value\n",
        None,
    );
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
        print('malformed Dart generation prompt', file=sys.stderr)
        raise SystemExit(64)

candidate = section('# Existing candidate', 'dart')
feedback = section('# Actual validation feedback', 'text')
if candidate.strip() == '(none)' and feedback.strip() == '(none)':
    expression = 'value'
elif '_cott_sample_alpha' in candidate and 'dart-never-run' in feedback:
    expression = '(value)'
else:
    print('unexpected whole-target retry state', file=sys.stderr)
    raise SystemExit(65)
source = (
    'int _cott_sample_alpha(int value) {\n'
    '  return ' + expression + ';\n'
    '}\n'
    '// cott-test-prompt-json: '
    + json.dumps(prompt, ensure_ascii=False, separators=(',', ':'))
    + '\n'
)
pathlib.Path('implementation.dart').write_text(source, encoding='utf-8')
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
            "dart",
        ],
    );
    assert_eq!(generated.status.code(), Some(5));
    assert!(
        String::from_utf8_lossy(&generated.stderr).contains("dart-never-run"),
        "{}",
        String::from_utf8_lossy(&generated.stderr)
    );

    let source_path = project.path.join("dart/cott_impl/sample/alpha.dart");
    let source = fs::read_to_string(&source_path).expect("repairable pending checkpoint");
    let retry = captured_prompt(&source);
    assert!(
        fenced_prompt_section(&retry, "# Actual validation feedback", "text")
            .contains("dart-never-run")
    );
    assert!(source.contains("return (value);"));

    let record = generation_record(&project.path);
    assert!(!record.current.verified);
    assert!(record.current.verification.is_null());
    assert!(record.last_verified.is_none());
    assert_eq!(record.current.unresolved, ["sample.alpha".to_owned()]);
    assert_eq!(record.current.implementations.len(), 1);
    assert_eq!(record.current.implementations[0].owner, DartOwner::Agent);
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
            .join("generated/dart/lib/src/cott_impl/sample/alpha.dart")
            .exists(),
        "pending source must not leak into the emitted package"
    );
}
