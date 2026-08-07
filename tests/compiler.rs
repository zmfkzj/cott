use std::path::PathBuf;

use cott::compiler::{SourceFile, parse_project};

#[test]
fn parses_sources_in_input_order_without_project_semantic_checks() {
    let project = parse_project([
        SourceFile::new(
            "disk/first.cott",
            "module declared.first\nuse unresolved.dependency\n",
        ),
        SourceFile::new(
            "disk/second.cott",
            "module declared.second\nuse unrelated.dependency\n",
        ),
    ])
    .expect("valid source files should produce a parsed project");

    assert_eq!(
        project
            .sources
            .iter()
            .map(|source| source.path.clone())
            .collect::<Vec<_>>(),
        vec![
            PathBuf::from("disk/first.cott"),
            PathBuf::from("disk/second.cott")
        ]
    );
    assert_eq!(
        project.sources[0].syntax.module.path.segments,
        ["declared", "first"]
    );
    assert_eq!(
        project.sources[1].syntax.module.path.segments,
        ["declared", "second"]
    );
}

#[test]
fn source_file_constructor_feeds_parse_project() {
    let project = parse_project([SourceFile::new(
        "memory/constructed.cott",
        "module constructed.source\n",
    )])
    .expect("constructed source should produce a parsed project");

    assert_eq!(project.sources.len(), 1);
    assert_eq!(
        project.sources[0].path,
        PathBuf::from("memory/constructed.cott")
    );
    assert_eq!(
        project.sources[0].syntax.module.path.segments,
        ["constructed", "source"]
    );
}

#[test]
fn aggregates_syntax_diagnostics_with_their_source_paths() {
    let errors = parse_project([
        SourceFile::new("broken/first.cott", "module broken.first\n@\n"),
        SourceFile::new("broken/second.cott", "module broken.second\n@\n"),
    ])
    .expect_err("invalid source files should return project diagnostics");

    assert_eq!(
        errors
            .iter()
            .map(|error| error.path.clone())
            .collect::<Vec<_>>(),
        vec![
            PathBuf::from("broken/first.cott"),
            PathBuf::from("broken/second.cott")
        ]
    );
}
