use std::path::PathBuf;

use cott::diagnostics::{Diagnostic, DiagnosticReport, SourceMap, SourceSpan, Span};

#[test]
fn report_is_one_json_object_with_source_locations() {
    let mut sources = SourceMap::default();
    let file = sources.add(PathBuf::from("src/demo.cott"), "module demo.core\n".into());
    let mut diagnostic = Diagnostic::new("example", Span::new(0, 6));
    diagnostic.source_span = Some(SourceSpan {
        file,
        start_byte: 0,
        end_byte: 6,
    });
    diagnostic.source_order = 3;
    let bytes = DiagnosticReport {
        diagnostics: vec![diagnostic],
    }
    .canonical_json(&sources)
    .expect("serialize report");
    let value: serde_json::Value = serde_json::from_slice(&bytes).expect("valid JSON");
    assert_eq!(value["schema_version"], 1);
    assert_eq!(value["diagnostics"][0]["span"]["start_column"], 1);
    assert!(bytes.ends_with(b"\n"));
}
