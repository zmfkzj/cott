use std::path::{Path, PathBuf};

use cott::formatter::format;
use cott::parser::parse_cst;
use cott::syntax::Cst;

fn formatted(source: &str) -> String {
    let cst = Cst::parse(source).expect("lex");
    let ast = parse_cst(&cst).expect("parse");
    String::from_utf8(format(&cst, &ast).expect("format")).expect("UTF-8")
}

#[test]
fn long_unparenthesized_error_condition_formats_to_a_fixed_point() {
    let source = "module demo.core\n\nenum Failure:\n    Invalid\n\nfn check(first_value: I32, second_value: I32, third_value: I32) -> Result[I32, Failure]:\n    error Failure.Invalid when first_value == 1000000 or second_value == 2000000 or third_value == 3000000\n";
    let once = formatted(source);
    assert_eq!(formatted(&once), once);
    assert!(
        once.contains("    error Failure.Invalid when (first_value == 1000000 or second_value == 2000000 or third_value == 3000000)\n"),
        "{once}"
    );
}

#[test]
fn long_guarded_invariant_and_ensures_format_to_a_fixed_point() {
    let source = "module demo.core\n\nenum SearchStatus:\n    Loading\n    Ready\n\nstruct SearchSnapshot:\n    applied_request_id: U64\n    result: Str\n    status: SearchStatus\n\n    invariant self.status matches SearchStatus.Loading => self.applied_request_id == 0 and self.result == \"\"\n\nfn search(snapshot: SearchSnapshot) -> Result[SearchSnapshot, Str]:\n    ensures Result.Ok(next) => next.applied_request_id == snapshot.applied_request_id and next.result == snapshot.result\n";
    let once = formatted(source);
    assert_eq!(formatted(&once), once);
    assert!(
        once.contains("    invariant self.status matches SearchStatus.Loading => (self.applied_request_id == 0 and self.result == \"\")\n"),
        "{once}"
    );
    assert!(
        once.contains("    ensures Result.Ok(next) => (next.applied_request_id == snapshot.applied_request_id and next.result == snapshot.result)\n"),
        "{once}"
    );
}

fn cott_sources(directory: &Path, inside_src: bool, sources: &mut Vec<PathBuf>) {
    let mut entries = std::fs::read_dir(directory)
        .expect("read example directory")
        .map(|entry| entry.expect("example entry").path())
        .collect::<Vec<_>>();
    entries.sort();
    for path in entries {
        let file_type = std::fs::symlink_metadata(&path)
            .expect("example metadata")
            .file_type();
        if file_type.is_dir() {
            let name = path.file_name().and_then(|name| name.to_str());
            if matches!(
                name,
                Some(".venv" | ".cott" | ".gradle" | ".dart_tool" | "build" | "node_modules")
            ) {
                continue;
            }
            cott_sources(&path, inside_src || name == Some("src"), sources);
        } else if file_type.is_file()
            && inside_src
            && path
                .extension()
                .is_some_and(|extension| extension == "cott")
        {
            sources.push(path);
        }
    }
}

#[test]
fn every_example_source_formats_idempotently() {
    let mut sources = Vec::new();
    cott_sources(
        &Path::new(env!("CARGO_MANIFEST_DIR")).join("examples"),
        false,
        &mut sources,
    );
    assert!(!sources.is_empty(), "no example sources found");
    let failures = sources
        .iter()
        .filter(|path| {
            let source = std::fs::read_to_string(path).expect("read example source");
            let once = formatted(&source);
            formatted(&once) != once
        })
        .collect::<Vec<_>>();
    assert!(
        failures.is_empty(),
        "fmt(fmt(x)) != fmt(x) for {failures:#?}"
    );
}
