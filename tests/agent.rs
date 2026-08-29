use std::collections::BTreeMap;

use std::path::Path;

use cott::hash::sha256_hex;

use cott::agent::{
    AgentKind, CODEX, OMP, ShadowFacet, adapter, has_normative_modal, parse_domain_rules,
    render_prompt, scan_doc_candidates, sentence_has_facet,
};
use cott::python::artifact_plan::{PythonCallable, PythonCallableKind};

#[test]
fn adapter_contracts_have_minimum_versions_and_exact_argv() {
    assert_eq!(adapter(AgentKind::Codex), &CODEX);
    assert_eq!(adapter(AgentKind::Omp), &OMP);
    assert_eq!(CODEX.executable_name, "codex");
    assert_eq!(CODEX.minimum_version, "0.147.0");
    assert_eq!(CODEX.version_argv, &["--version"]);
    assert_eq!(
        CODEX.argv_template,
        &[
            "exec",
            "--strict-config",
            "--ephemeral",
            "--ignore-user-config",
            "--ignore-rules",
            "--skip-git-repo-check",
            "--sandbox",
            "workspace-write",
            "--color",
            "never",
            "--cd",
            "<workspace>",
            "-",
        ]
    );
    assert!(CODEX.prompt_on_stdin);
    assert_eq!(OMP.executable_name, "omp");
    assert_eq!(OMP.minimum_version, "17.2.12");
    assert_eq!(OMP.version_argv, &["--version"]);
    assert_eq!(
        OMP.argv_template,
        &[
            "-p",
            "--cwd",
            "<workspace>",
            "--no-session",
            "--no-rules",
            "--no-skills",
            "--no-extensions",
            "--no-lsp",
            "--no-pty",
            "--no-title",
            "--tools",
            "read,grep,glob,edit,write",
            "--approval-mode",
            "yolo",
            "--max-time",
            "<seconds>s",
            "--config",
            "<overlay>",
            "<prompt>",
        ]
    );
    assert!(!OMP.prompt_on_stdin);
}

#[test]
fn prompt_has_fixed_sections_and_final_instruction() {
    let callable = PythonCallable {
        module: "app".to_owned(),
        cott_symbol: "app.run".to_owned(),
        name: "run".to_owned(),
        kind: PythonCallableKind::Function,
        declaration: serde_json::json!({}),
        owner: None,
    };
    let external_types = BTreeMap::from([
        ("app.Widget".to_owned(), "vendor.models:Widget".to_owned()),
        ("app.Alpha".to_owned(), "vendor.models:Alpha".to_owned()),
    ]);
    let generated_type_import_rule = "For other modules import public generated symbols only through `from app import name` and generated value types only through `from app_types import Type`.";
    let prompt = render_prompt(
        &callable,
        br#"{"module":"app"}"#,
        "docs",
        generated_type_import_rule,
        &external_types,
        "bound",
        None,
        None,
        Path::new("python/_cott_impl/app/run.py"),
    )
    .expect("prompt");
    let unmapped = render_prompt(
        &callable,
        br#"{"module":"app"}"#,
        "docs",
        generated_type_import_rule,
        &BTreeMap::new(),
        "bound",
        None,
        None,
        Path::new("python/_cott_impl/app/run.py"),
    )
    .expect("prompt");
    assert_ne!(sha256_hex(&prompt), sha256_hex(&unmapped));
    let text = String::from_utf8(prompt).expect("UTF-8 prompt");
    assert!(text.starts_with("COTT_AGENT_PROMPT_V1\n\nTARGET\n"));
    assert!(text.contains("Symbol: app.run"));
    assert!(text.contains("Define exactly one canonical top-level function `run`."));
    assert!(text.contains(
        "You MAY additionally define private implementation helpers, private immutable constants, and invariant TypeVars. Each helper MUST be an undecorated, synchronous, fully annotated top-level function whose name starts with a single `_` but is neither dunder nor reserved `_cott_`; function names MUST be unique. Each constant MUST have a single-leading-underscore name that is neither dunder nor reserved `_cott_`, and be a literal `Final[bool|int|float|str|bytes]` value. Do not define classes, public helpers, mutable globals, decorators, async functions, variadic parameters, parameter defaults, or other executable top-level assignments."
    ));
    assert!(text.contains("CANONICAL IR\n{\"module\":\"app\"}\n\nDOCS CONTRACTS EFFECTS"));
    assert!(!text.contains("\"external_types\""));
    assert!(text.contains(
        "RELEVANT TYPES\nFor other modules import public generated symbols only through `from app import name` and generated value types only through `from app_types import Type`.\n\nPYTHON EXTERNAL TYPE PROJECTIONS\napp.Alpha = vendor.models:Alpha\napp.Widget = vendor.models:Widget\n\nBOUND SYMBOLS IMPORT RULES"
    ));
    assert!(text.contains(
        "Use external declarations through their exact public generated aliases; their projected public APIs MAY be called when the contract requires it. Do not reconstruct external paths, use dynamic imports or reflection, or inspect and coerce external values merely to validate a contract."
    ));
    assert!(text.contains(
        "FACTORY TYPE MODEL\n`Factory[Concrete]` maps to `type[Concrete]`: it is the exact compiler-generated `Concrete` class object, never an instance, subclass, or arbitrary callable. Constructor calls MUST match `Concrete`'s inferred Cott init signature. Validation MUST NOT construct or invoke a Factory value."
    ));
    assert!(text.contains(
        "`Dyn[Trait]` is a nominal runtime wrapper: import `Dyn` only from `cott_runtime`, construct it only as `Dyn(value=<compiler-generated concrete>, trait=<exact Trait Protocol>)`, and invoke a trait method only as `dyn.value.method(...)`; never substitute structural values or inspect either wrapper or value."
    ));
    assert!(text.contains(
        "EFFECT CALLS\nCall Cott functions only by their exact imported facade name. Do not alias, store, return, pass, rebind, or shadow a Cott callable"
    ));
    assert!(text.contains(
        "PRIVATE RUNTIME EFFECT ADAPTERS\nThe only private runtime effect adapters are `cott_runtime._cott_fixture_read`, `cott_runtime._cott_fixture_write`, `cott_runtime._cott_fixture_replace`, `cott_runtime._cott_fixture_http`, and `cott_runtime._cott_fixture_now`. They MAY be used only when the contract is targeted by a compatible declared scenario with an active fixture. Otherwise, an effectful callable MUST NOT invent an adapter name or authority; follow ordinary declared-effect implementation rules and leave it as trust evidence. Do not emulate an effect with stdlib I/O, inspect adapter internals, dynamically import an adapter, or retain an adapter value."
    ));
    assert!(text.contains(
        "SCENARIOS\nScenario fixtures and steps are runner-owned. Scenario calls are facade-only"
    ));
    assert!(text.contains(
        "Standard ABI aliases, including integer widths, are annotations and MUST NOT be called. Construct result values only with top-level `cott_runtime.Ok(...)`/`cott_runtime.Err(...)`, never `Result.Ok`/`Result.Err`. Generated payload enum aliases have no members; import and construct top-level `<Enum>_<Variant>` classes from the exact generated `*_types` module, never `<Enum>.<Variant>`."
    ));
    assert!(text.contains(
        "Generated structs are exact keyword-only dataclasses and MUST be constructed as `Struct(field=...)`; never synthesize `<Struct>_<Variant>`."
    ));
    assert!(
        text.ends_with(
            "If the contract must change, report that and leave the target unresolved.\n"
        )
    );
}

#[test]
fn async_prompt_requires_the_exact_definition_and_awaits() {
    let prompt = render_prompt(
        &PythonCallable {
            module: "app".to_owned(),
            cott_symbol: "app.fetch".to_owned(),
            name: "fetch".to_owned(),
            kind: PythonCallableKind::AsyncFunction,
            declaration: serde_json::json!({}),
            owner: None,
        },
        br#"{"module":"app"}"#,
        "docs",
        "types",
        &BTreeMap::new(),
        "bound",
        None,
        None,
        Path::new("python/_cott_impl/app/fetch.py"),
    )
    .expect("async prompt");
    let text = String::from_utf8(prompt).expect("UTF-8 prompt");
    assert!(text.contains("canonical undecorated top-level `async def` function `fetch`"));
    assert!(text.contains("Await every call to an async Cott facade"));
    assert!(text.contains("additional async functions"));
}

#[test]
fn async_method_prompt_requires_the_exact_private_async_helper() {
    let prompt = render_prompt(
        &PythonCallable {
            module: "app".to_owned(),
            cott_symbol: "app.Reader.fetch".to_owned(),
            name: "fetch".to_owned(),
            kind: PythonCallableKind::AsyncImplMethod {
                concrete: "Reader".to_owned(),
            },
            declaration: serde_json::json!({}),
            owner: Some(serde_json::json!({})),
        },
        br#"{"module":"app"}"#,
        "docs",
        "types",
        &BTreeMap::new(),
        "bound",
        None,
        None,
        Path::new("python/_cott_impl/app/Reader/fetch.py"),
    )
    .expect("async method prompt");
    let text = String::from_utf8(prompt).expect("UTF-8 prompt");
    assert!(
        text.contains("canonical private top-level `async def` function `_cott_impl_Reader_fetch`")
    );
    assert!(text.contains("additional async functions"));
    assert!(text.contains("Await every call to an async Cott facade or sibling method"));
    assert!(text.contains("asyncio.TaskGroup"));
}

#[test]
fn method_prompt_allows_private_helpers_and_constants() {
    let prompt = render_prompt(
        &PythonCallable {
            module: "foo.bar".to_owned(),
            cott_symbol: "foo.bar.Reader.read".to_owned(),
            name: "read".to_owned(),
            kind: PythonCallableKind::ImplMethod {
                concrete: "Reader".to_owned(),
            },
            declaration: serde_json::json!({}),
            owner: Some(serde_json::json!({})),
        },
        br#"{"module":"foo.bar"}"#,
        "docs",
        "The compiler-owned concrete facade class `Reader` is absent from `foo.bar_types`; import it exactly as `from foo.bar import Reader` for the `self` annotation. Generated value-type imports remain `from foo.bar_types import Type`.",
        &BTreeMap::new(),
        "bound",
        None,
        None,
        Path::new("python/_cott_impl/foo/bar/Reader/read.py"),
    )
    .expect("prompt");
    let text = String::from_utf8(prompt).expect("UTF-8 prompt");
    assert!(text.contains("Symbol: foo.bar.Reader.read"));
    assert!(
        text.contains("exactly one canonical private top-level function `_cott_impl_Reader_read`")
    );
    assert!(text.contains(
        "You MAY additionally define private implementation helpers, private immutable constants, and invariant TypeVars. Each helper MUST be an undecorated, synchronous, fully annotated top-level function whose name starts with a single `_` but is neither dunder nor reserved `_cott_`; function names MUST be unique. Each constant MUST have a single-leading-underscore name that is neither dunder nor reserved `_cott_`, and be a literal `Final[bool|int|float|str|bytes]` value. Do not define classes, public helpers, mutable globals, decorators, async functions, variadic parameters, parameter defaults, or other executable top-level assignments."
    ));
    assert!(text.contains(
        "The compiler-owned concrete facade class `Reader` is absent from `foo.bar_types`; import it exactly as `from foo.bar import Reader` for the `self` annotation. Generated value-type imports remain `from foo.bar_types import Type`."
    ));
}

#[test]
fn specialization_prompt_is_rejected_as_compiler_owned() {
    let error = render_prompt(
        &PythonCallable {
            module: "app".to_owned(),
            cott_symbol: "app.Reader.fetch".to_owned(),
            name: "fetch".to_owned(),
            kind: PythonCallableKind::AsyncImplMethod {
                concrete: "Reader".to_owned(),
            },
            declaration: serde_json::json!({"selected": {"origin": "specialization"}}),
            owner: Some(serde_json::json!({})),
        },
        br#"{"module":"app"}"#,
        "docs",
        "types",
        &BTreeMap::new(),
        "bound",
        None,
        None,
        Path::new("python/_cott_impl/app/Reader/fetch.py"),
    )
    .expect_err("specialization target is compiler-owned");
    assert_eq!(
        error,
        "compiler-owned specialization implementation method `app.Reader.fetch` must not be sent to an agent"
    );
}

#[test]
fn domain_rules_are_normalized_with_exact_payload_spans_and_source_order() {
    let rules = b"ordinary guidance\ncott-domain app.fetch return: return this value\ncott-domain app.fetch limit: at most ten bytes\ncott-domain app.fetch error: reject \xc3\xa9\ncott-domain app.fetch atomicity: all-or-nothing write\ncott-domain app.Reader.close cleanup: delete temporary files\n";
    let parsed = parse_domain_rules(Path::new("generator.rules"), rules);

    assert!(parsed.diagnostics.is_empty());
    assert_eq!(parsed.path.as_path(), Path::new("generator.rules"));
    assert_eq!(
        parsed
            .rules
            .iter()
            .map(|rule| rule.facet)
            .collect::<Vec<_>>(),
        vec![
            ShadowFacet::Return,
            ShadowFacet::Limit,
            ShadowFacet::Error,
            ShadowFacet::Atomicity,
            ShadowFacet::Cleanup,
        ]
    );
    assert_eq!(parsed.rules[0].symbol, "app.fetch");
    assert_eq!(parsed.rules[0].payload, "return this value");
    assert_eq!(parsed.rules[0].source_order, b"ordinary guidance\n".len());
    assert_eq!(
        &rules[parsed.rules[1].payload_span.start..parsed.rules[1].payload_span.end],
        b"at most ten bytes"
    );
    assert_eq!(parsed.rules[2].payload, "reject é");
    assert_eq!(
        &rules[parsed.rules[2].payload_span.start..parsed.rules[2].payload_span.end],
        "reject é".as_bytes()
    );
    assert_eq!(
        &rules[parsed.rules[4].payload_span.start..parsed.rules[4].payload_span.end],
        b"delete temporary files"
    );
}

#[test]
fn malformed_or_duplicate_domain_rules_are_diagnostics_not_prose() {
    let rules = b"cott-domain app.fetch unknown: text\n\
cott-domain app.fetch return: first\n\
cott-domain app.fetch return: second\n\
cott-domain fetch return: text\n\
cott-domain app.fetch limit : text\n\
cott-domain app.fetch error:\n\
cott-domain app.fetch cleanup: text\r\n\
cott-domain app.fetch atomicity: \xff\n";
    let parsed = parse_domain_rules(Path::new("generator.rules"), rules);

    assert_eq!(parsed.rules.len(), 1);
    assert_eq!(parsed.rules[0].payload, "first");
    assert_eq!(parsed.diagnostics.len(), 7);
    assert!(
        parsed
            .diagnostics
            .iter()
            .all(|diagnostic| diagnostic.code == "COTT-K001")
    );
    assert!(
        parsed
            .diagnostics
            .iter()
            .any(|diagnostic| diagnostic.message.contains("unknown facet"))
    );
    assert!(
        parsed
            .diagnostics
            .iter()
            .any(|diagnostic| diagnostic.message.contains("duplicate"))
    );
    assert!(
        parsed
            .diagnostics
            .iter()
            .any(|diagnostic| diagnostic.message.contains("valid UTF-8"))
    );
    assert!(
        parsed
            .diagnostics
            .windows(2)
            .all(|pair| pair[0].source_order < pair[1].source_order)
    );
    assert!(parsed.diagnostics.iter().any(|diagnostic| {
        diagnostic.message.contains("LF line endings")
            && &rules[diagnostic.span.start..diagnostic.span.end]
                == b"cott-domain app.fetch cleanup: text\r"
    }));
}

#[test]
fn ordinary_rule_prose_is_ignored_and_prompt_bytes_are_unchanged() {
    let rules = b"Must return safely.\nordinary cott-domain-like prose\ncott-domain app.fetch return: exact \xff bytes\n";
    let parsed = parse_domain_rules(Path::new("generator.rules"), rules);
    assert!(parsed.rules.is_empty());
    assert_eq!(parsed.diagnostics.len(), 1);

    let callable = PythonCallable {
        module: "app".to_owned(),
        cott_symbol: "app.run".to_owned(),
        name: "run".to_owned(),
        kind: PythonCallableKind::Function,
        declaration: serde_json::json!({}),
        owner: None,
    };
    let prompt = render_prompt(
        &callable,
        br#"{"module":"app"}"#,
        "docs",
        "types",
        &BTreeMap::new(),
        "bound",
        None,
        Some(rules),
        Path::new("python/_cott_impl/app/run.py"),
    )
    .expect("prompt");
    let marker = b"\nPROJECT RULES\n";
    let start = prompt
        .windows(marker.len())
        .position(|window| window == marker)
        .expect("rules marker")
        + marker.len();
    assert_eq!(&prompt[start..start + rules.len()], rules);
}

#[test]
fn doc_scanner_requires_closed_ascii_modal_and_facet_pairs() {
    let doc = "é\nMust return the result.\nMust atomically clean up temporary files!\nMustard returns no duty.\nThe timeout is noted.\nMust proceed.";
    let candidates = scan_doc_candidates(doc);
    assert_eq!(
        candidates
            .iter()
            .map(|candidate| candidate.facet)
            .collect::<Vec<_>>(),
        vec![
            ShadowFacet::Return,
            ShadowFacet::Atomicity,
            ShadowFacet::Cleanup
        ]
    );
    assert_eq!(candidates[0].span.start, "é\n".len());
    assert_eq!(
        &doc.as_bytes()[candidates[1].span.start..candidates[1].span.end],
        b"Must atomically clean up temporary files!"
    );
    assert!(has_normative_modal("REQUIRED TO return a result"));
    assert!(has_normative_modal("must not fail"));
    assert!(!has_normative_modal("mustard returns"));
    assert!(sentence_has_facet("at least one byte", ShadowFacet::Limit));
    assert!(!sentence_has_facet("returning later", ShadowFacet::Return));
}
