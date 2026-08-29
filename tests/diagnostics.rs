use std::path::PathBuf;

use cott::diagnostics::{
    Diagnostic, DiagnosticReport, RelatedDiagnostic, Severity, SourceMap, SourceSpan, Span, code,
};

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

#[test]
fn shadow_specification_warning_preserves_utf8_source_location_and_schema() {
    let mut sources = SourceMap::default();
    let file = sources.add(
        PathBuf::from("generator.rules"),
        "é\ncott-domain app.fetch return: exact result\n".into(),
    );
    let payload = "é\ncott-domain app.fetch return: ".len();
    let mut diagnostic = Diagnostic::warning(
        code::SHADOW_SPECIFICATION,
        "possible shadow specification: return duty is stated in generator rules but has no formal evidence",
        Span::new(payload, payload + "exact result".len()),
    );
    diagnostic.source_span = Some(SourceSpan {
        file,
        start_byte: payload,
        end_byte: payload + "exact result".len(),
    });
    diagnostic.reason = Some(
        "natural-language recognition is conservative and is not proof of equivalence".to_owned(),
    );
    diagnostic.help.push("add an ensures relation".to_owned());
    diagnostic.source_order = 7;
    diagnostic.related.push(RelatedDiagnostic {
        message: "callable declaration".to_owned(),
        span: Some(SourceSpan {
            file,
            start_byte: "é\n".len(),
            end_byte: "é\ncott-domain".len(),
        }),
    });
    assert_eq!(diagnostic.severity, Severity::Warning);
    let bytes = DiagnosticReport {
        diagnostics: vec![diagnostic],
    }
    .canonical_json(&sources)
    .expect("serialize report");
    let value: serde_json::Value = serde_json::from_slice(&bytes).expect("valid JSON");
    let warning = &value["diagnostics"][0];
    assert_eq!(warning["code"], "COTT-K101");
    assert_eq!(warning["severity"], "warning");
    assert_eq!(warning["span"]["start_byte"], payload);
    assert_eq!(warning["span"]["start_line"], 2);
    assert_eq!(warning["span"]["start_column"], 31);
    assert_eq!(
        warning["reason"],
        "natural-language recognition is conservative and is not proof of equivalence"
    );
    assert_eq!(
        warning["help"],
        serde_json::json!(["add an ensures relation"])
    );
    assert_eq!(value["schema_version"], 1);
    assert_eq!(warning["related"][0]["message"], "callable declaration");
    assert_eq!(warning["related"][0]["span"]["start_line"], 2);
    assert_eq!(warning["source_order"], 7);
    assert_eq!(warning["actual"], serde_json::Value::Null);
    assert_eq!(warning["expected"], serde_json::Value::Null);
}
