use std::path::Path;

use cott::agent::render_prompt;

#[test]
fn prompt_has_fixed_sections_and_final_instruction() {
    let prompt = render_prompt(
        "foo.bar.run",
        br#"{"module":"foo.bar"}"#,
        "docs",
        "types",
        "bound",
        None,
        None,
        Path::new("python/_cott_impl/foo/bar/run.py"),
    )
    .expect("prompt");
    let text = String::from_utf8(prompt).expect("UTF-8 prompt");
    assert!(text.starts_with("COTT_AGENT_PROMPT_V1\n\nTARGET\n"));
    assert!(text.contains("CANONICAL IR\n{\"module\":\"foo.bar\"}"));
    assert!(
        text.ends_with(
            "If the contract must change, report that and leave the target unresolved.\n"
        )
    );
}
