use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

use cott::agent::{
    AGENT_NOT_INHERITED, AgentKind, CLAUDE, CODEX, OMP, PI, PI_MINIMUM_NODE_VERSION,
    PI_UNSUPPORTED_MAJOR, PROJECT_RESOURCES, PiStreamSummary, ShadowFacet, adapter,
    has_normative_modal, parse_domain_rules, pi_max_prompt_bytes, render_prompt,
    scan_doc_candidates, sentence_has_facet, valid_model, validate_pi_json_stream,
};
use cott::binding::{BindingOwner, ResolvedBinding};
use cott::compiler::{SourceFile, parse_project};
use cott::hash::sha256_hex;
use cott::hir::lower;
use cott::ir::render;
use cott::python::artifact_plan::{PythonArtifactPlan, PythonCallable, PythonCallableKind};
use serde_json::json;

#[test]
fn adapter_contracts_have_minimum_versions_and_exact_argv() {
    assert_eq!(adapter(AgentKind::Codex), &CODEX);
    assert_eq!(adapter(AgentKind::Omp), &OMP);
    assert_eq!(adapter(AgentKind::Claude), &CLAUDE);
    assert_eq!(CODEX.executable_name, "codex");
    assert_eq!(CODEX.minimum_version, "0.147.0");
    assert_eq!(CODEX.version_argv, &["--version"]);
    assert_eq!(
        CODEX.argv_template,
        &[
            "exec",
            "--ephemeral",
            "--skip-git-repo-check",
            "--color",
            "never",
            "--cd",
            "<workspace>",
            "-",
        ]
    );
    assert!(CODEX.prompt_on_stdin);
    assert_eq!(CLAUDE.executable_name, "claude");
    assert_eq!(CLAUDE.minimum_version, "2.1.89");
    assert_eq!(CLAUDE.version_argv, &["--version"]);
    assert_eq!(
        CLAUDE.argv_template,
        &[
            "--print",
            "--input-format",
            "text",
            "--output-format",
            "json",
            "--no-session-persistence",
        ]
    );
    // The caller's Claude Code settings, login, hooks, plugins, MCP servers
    // and tools apply: no minimal mode and no tool restriction.
    for removed in [
        "--bare",
        "--tools",
        "--allowedTools",
        "--disallowedTools",
        "dontAsk",
        // The caller's own permission mode and rules apply.
        "--permission-mode",
        "--dangerously-skip-permissions",
    ] {
        assert!(!CLAUDE.argv_template.contains(&removed), "{removed}");
    }
    assert!(CLAUDE.prompt_on_stdin);
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
            "--no-pty",
            "--no-title",
            "--max-time",
            "<seconds>s",
            "@<prompt-file>",
        ]
    );
    for removed in [
        "--no-rules",
        "--no-skills",
        "--no-extensions",
        "--no-lsp",
        "--tools",
        "--config",
        // The caller's own tool approval policy applies.
        "--approval-mode",
        "--auto-approve",
    ] {
        assert!(!OMP.argv_template.contains(&removed), "{removed}");
    }
    for removed in [
        "--strict-config",
        "--ignore-user-config",
        "--ignore-rules",
        // The caller's own sandbox and approval policy apply.
        "--sandbox",
        "--full-auto",
        "--dangerously-bypass-approvals-and-sandbox",
    ] {
        assert!(!CODEX.argv_template.contains(&removed), "{removed}");
    }
    assert!(!OMP.prompt_on_stdin);
}

fn function_callable(symbol: &str) -> PythonCallable {
    let (module, name) = symbol.rsplit_once('.').expect("dotted symbol");
    PythonCallable {
        module: module.to_owned(),
        cott_symbol: symbol.to_owned(),
        name: name.to_owned(),
        kind: PythonCallableKind::Function,
        declaration: json!({}),
        owner: None,
    }
}

fn render_text(
    callable: &PythonCallable,
    surface: &serde_json::Value,
    rules: &[u8],
    references: &[ResolvedBinding],
    external_types: &BTreeMap<String, String>,
    existing: Option<&[u8]>,
    feedback: Option<&str>,
) -> String {
    let context = cott::intent::context(surface, &callable.cott_symbol, rules).expect("context");
    String::from_utf8(
        render_prompt(
            callable,
            &context,
            references,
            external_types,
            existing,
            feedback,
            Path::new("implementation.py"),
        )
        .expect("prompt"),
    )
    .expect("utf-8 prompt")
}

fn resolved_binding(symbol: &str, body: &str) -> ResolvedBinding {
    let (module, function) = symbol.rsplit_once('.').expect("dotted symbol");
    ResolvedBinding {
        module: module.to_owned(),
        function: function.to_owned(),
        cott_symbol: symbol.to_owned(),
        kind: PythonCallableKind::Function,
        implementation_module: module.to_owned(),
        implementation_function: function.to_owned(),
        owner: BindingOwner::Agent,
        source: PathBuf::from("/host/secret/abs.py"),
        generated_relative: PathBuf::from("python/_cott_impl/x.py"),
        bytes: body.as_bytes().to_vec(),
        sha256: format!("sha256:{}", sha256_hex(body.as_bytes())),
    }
}

fn section<'a>(text: &'a str, name: &str) -> &'a str {
    let header = format!("{name}\n");
    let start = text
        .find(&header)
        .unwrap_or_else(|| panic!("missing section {name}"))
        + header.len();
    let rest = &text[start..];
    let mut end = rest.len();
    for other in [
        "AUTHORITY",
        "CURRENT INTENT",
        "FORMAL DECLARATIONS",
        "PROJECT RULES",
        "REFERENCE IMPLEMENTATIONS",
        "PYTHON OUTPUT RULES",
        "VALIDATION FEEDBACK",
    ] {
        if other == name {
            continue;
        }
        if let Some(index) = rest.find(&format!("\n{other}\n")) {
            end = end.min(index);
        }
    }
    &rest[..end]
}

fn compiled_surface(source: &str) -> serde_json::Value {
    let parsed = parse_project([SourceFile::new("src/api/service.cott", source)])
        .expect("source must parse");
    let lowered = lower(Path::new("src"), parsed).expect("source must lower");
    let ir = render(&lowered).expect("source must render");
    PythonArtifactPlan::from_ir(&ir)
        .expect("IR must project")
        .contract_surface()
}

fn selected_names(context: &serde_json::Value) -> Vec<&str> {
    context["declarations"]
        .as_object()
        .expect("modules")
        .values()
        .flat_map(|module| {
            module["declarations"]
                .as_array()
                .expect("decls")
                .iter()
                .map(|declaration| declaration["name"].as_str().expect("name"))
        })
        .collect()
}

#[test]
fn prompt_scopes_intent_against_unrelated_input() {
    let surface = json!({
        "app": {"declarations": [
            {
                "kind": "function",
                "name": "app.run",
                "public": true,
                "doc": "Run the selected job. Delegate to helper.",
                "parameters": [{"name": "handle", "type": {"kind": "named", "name": "app.Handle", "args": []}}],
                "return_type": {"kind": "named", "name": "app.Widget", "args": []},
                "contract": {"clauses": [
                    {
                        "clause_id": 0,
                        "kind": "requires",
                        "guard": null,
                        "expression": {
                            "kind": "comparison_chain",
                            "operands": [
                                {"kind": "constant_ref", "symbol": "app.LIMIT", "reference": {"kind": "constant", "symbol": "app.LIMIT"}, "type": {"kind": "primitive", "name": "u64"}},
                                {"kind": "literal", "value": {"kind": "integer", "value": "0"}, "reference": null, "type": {"kind": "primitive", "name": "u64"}}
                            ],
                            "operators": ["greater"],
                            "reference": null,
                            "type": {"kind": "primitive", "name": "bool"}
                        }
                    },
                    {
                        "clause_id": 1,
                        "kind": "ensures",
                        "guard": null,
                        "expression": {"kind": "literal", "value": {"kind": "bool", "value": true}, "reference": null, "type": {"kind": "primitive", "name": "bool"}}
                    }
                ]}
            },
            {
                "kind": "function",
                "name": "app.helper",
                "public": true,
                "doc": "Helper docs.",
                "parameters": [],
                "return_type": {"kind": "primitive", "name": "i32"},
                "contract": {"clauses": []}
            },
            {
                "kind": "function",
                "name": "app.other",
                "public": true,
                "doc": "Unrelated docs.",
                "parameters": [],
                "return_type": {"kind": "primitive", "name": "i32"},
                "contract": {"clauses": []}
            },
            {"kind": "struct", "name": "app.Widget", "public": true, "doc": null, "fields": []},
            {"kind": "struct", "name": "app.Noise", "public": true, "doc": null, "fields": []},
            {"kind": "const", "name": "app.LIMIT", "public": true, "type": {"kind": "primitive", "name": "u64"}, "value": {"kind": "integer", "value": "4"}},
            {"kind": "external_type", "name": "app.Handle", "public": true, "doc": null},
            {"kind": "external_type", "name": "app.UnusedExt", "public": true, "doc": null},
            {"kind": "scenario", "name": "app.RunCase", "public": true, "target": "app.run", "steps": [], "doc": null},
            {"kind": "scenario", "name": "app.OtherCase", "public": true, "target": "app.other", "steps": [], "doc": null}
        ]}
    });
    let rules = b"shared guidance\ncott-domain app.run return: keep going\ncott-domain app.other return: leak me\n";
    let references = [
        resolved_binding("app.helper", "HELPER_BODY_UNIQUE\n"),
        resolved_binding("app.other", "OTHER_BODY_LEAK\n"),
        resolved_binding("app.run", "TARGET_BODY_SHOULD_NOT_APPEAR\n"),
    ];
    let external_types = BTreeMap::from([
        ("app.Handle".to_owned(), "vendor.models:Handle".to_owned()),
        (
            "app.UnusedExt".to_owned(),
            "vendor.models:Unused".to_owned(),
        ),
        ("app.Alpha".to_owned(), "vendor.models:Alpha".to_owned()),
    ]);
    let text = render_text(
        &function_callable("app.run"),
        &surface,
        rules,
        &references,
        &external_types,
        None,
        None,
    );
    for heading in [
        "AUTHORITY",
        "CURRENT INTENT",
        "FORMAL DECLARATIONS",
        "PROJECT RULES",
        "REFERENCE IMPLEMENTATIONS",
        "PYTHON OUTPUT RULES",
    ] {
        assert!(text.contains(&format!("{heading}\n")), "{heading}");
    }
    assert!(!text.contains("VALIDATION FEEDBACK"));
    assert!(text.contains("Symbol: app.run"));
    assert!(text.contains("Write path: implementation.py"));
    assert!(!text.contains("/tmp/host-secret"));
    assert!(!text.contains("/host/secret"));

    let intent = section(&text, "CURRENT INTENT");
    assert!(intent.contains("app.run (target)"));
    assert!(intent.contains("Run the selected job."));
    assert!(intent.contains("Helper docs."));
    assert!(!intent.contains("Unrelated docs."));
    assert!(!intent.contains("HELPER_BODY_UNIQUE"));

    let formal = section(&text, "FORMAL DECLARATIONS");
    assert!(formal.contains("app.run"));
    assert!(formal.contains("app.helper"));
    assert!(formal.contains("app.Widget"));
    assert!(formal.contains("app.LIMIT"));
    assert!(formal.contains("app.Handle"));
    assert!(formal.contains("app.RunCase"));
    assert!(formal.contains("\"ensures\""));
    assert!(!formal.contains("app.other"));
    assert!(!formal.contains("app.Noise"));
    assert!(!formal.contains("app.UnusedExt"));
    assert!(!formal.contains("app.OtherCase"));
    assert!(!formal.contains("Run the selected job."));
    assert!(!formal.contains("Helper docs."));
    assert!(!formal.contains("\"doc\""));
    let project = section(&text, "PROJECT RULES");
    assert!(project.contains("shared guidance"));
    assert!(project.contains("keep going"));
    assert!(!project.contains("leak me"));

    let references = section(&text, "REFERENCE IMPLEMENTATIONS");
    assert!(references.contains("## app.helper"));
    assert!(references.contains("HELPER_BODY_UNIQUE"));
    assert!(!references.contains("OTHER_BODY_LEAK"));
    assert!(!references.contains("TARGET_BODY_SHOULD_NOT_APPEAR"));
    assert!(!references.contains("/host/secret"));

    let output = section(&text, "PYTHON OUTPUT RULES");
    assert!(output.contains("canonical top-level function `run`"));
    assert!(output.contains("app.Handle = vendor.models:Handle"));
    assert!(output.contains("from app import helper"));
    assert!(output.contains("from app_types import Handle, LIMIT, Widget"));
    assert!(output.contains("module alias"));
    assert!(output.contains("dynamic import"));
    assert!(!output.contains("vendor.models:Unused"));
    assert!(!output.contains("vendor.models:Alpha"));
    assert!(!output.contains("Factory["));
    assert!(!output.contains("Dyn["));
    assert!(output.contains("_cott_fixture_"));
    // The exact runtime message lets agents select host I/O without project rules restating it.
    assert!(output.contains("`.message` is exactly `\"fixture adapters are inactive\"`"));
    assert!(output.contains(
        "host standard-library I/O only when that call raises the inactive-adapter violation"
    ));
    assert!(output.contains("__cause__` is the original `OSError`"));
    assert!(!output.contains("CottArray(values="));
}

#[test]
fn intent_doc_identifiers_select_named_types_constants_rules_and_enums() {
    let surface = json!({
        "app": {"declarations": [
            {
                "kind": "function",
                "name": "app.run",
                "public": true,
                "doc": "Use Widget, LIMIT, Valid, and Status.Ready.",
                "parameters": [],
                "return_type": {"kind": "primitive", "name": "unit", "doc": "No value."},
                "contract": {"clauses": []}
            },
            {"kind": "function", "name": "app.other", "public": true, "doc": null, "parameters": [], "return_type": {"kind": "primitive", "name": "unit"}, "contract": {"clauses": []}},
            {"kind": "struct", "name": "app.Widget", "public": true, "doc": "A widget.", "fields": []},
            {"kind": "const", "name": "app.LIMIT", "public": true, "type": {"kind": "primitive", "name": "u64"}, "value": {"kind": "integer", "value": "4"}},
            {"kind": "rule", "name": "app.Valid", "public": true, "base": null, "contract": {"clauses": []}, "doc": null},
            {"kind": "enum", "name": "app.Status", "public": true, "doc": null, "variants": [{"name": "Ready", "symbol": "app.Status.Ready", "fields": []}]}
        ]}
    });
    let context = cott::intent::context(&surface, "app.run", b"").expect("context");
    let names = context["declarations"]["app"]["declarations"]
        .as_array()
        .expect("decls")
        .iter()
        .map(|declaration| declaration["name"].as_str().expect("name"))
        .collect::<Vec<_>>();
    assert!(names.contains(&"app.run"));
    assert!(names.contains(&"app.Widget"));
    assert!(names.contains(&"app.LIMIT"));
    assert!(names.contains(&"app.Valid"));
    assert!(names.contains(&"app.Status"));
    assert!(!names.contains(&"app.other"));
    let before = context.clone();
    let text = String::from_utf8(
        render_prompt(
            &function_callable("app.run"),
            &context,
            &[],
            &BTreeMap::new(),
            None,
            None,
            Path::new("implementation.py"),
        )
        .expect("prompt"),
    )
    .expect("utf-8 prompt");
    assert_eq!(context, before);
    let formal = section(&text, "FORMAL DECLARATIONS");
    assert!(formal.contains("app.Widget"));
    assert!(formal.contains("app.LIMIT"));
    assert!(formal.contains("app.Valid"));
    assert!(formal.contains("app.Status"));
    assert!(!formal.contains("app.other"));
    assert!(!formal.contains("A widget."));
    assert!(!formal.contains("No value."));
    assert!(!formal.contains("\"doc\""));
    let intent = section(&text, "CURRENT INTENT");
    assert!(intent.contains("A widget."));
    assert!(intent.contains("app.Widget"));
    assert!(intent.contains("No value."));
    assert!(intent.contains("app.run (target) type:"));
    let output = section(&text, "PYTHON OUTPUT RULES");
    assert!(output.contains("UNIT"));
    assert!(!output.contains("Option.Some"));
}

#[test]
fn scoped_rule_identifiers_join_the_intent_closure() {
    let surface = json!({
        "app": {"declarations": [
            {
                "kind": "function",
                "name": "app.run",
                "public": true,
                "doc": "Run it.",
                "parameters": [],
                "return_type": {"kind": "primitive", "name": "unit"},
                "contract": {"clauses": []}
            },
            {
                "kind": "function",
                "name": "app.helper",
                "public": true,
                "doc": "Helper docs.",
                "parameters": [],
                "return_type": {"kind": "primitive", "name": "unit"},
                "contract": {"clauses": []}
            },
            {
                "kind": "function",
                "name": "app.other",
                "public": true,
                "doc": "Unrelated docs.",
                "parameters": [],
                "return_type": {"kind": "primitive", "name": "unit"},
                "contract": {"clauses": []}
            },
            {"kind": "struct", "name": "app.Widget", "public": true, "doc": "A widget.", "fields": []},
            {"kind": "const", "name": "app.LIMIT", "public": true, "type": {"kind": "primitive", "name": "u64"}, "value": {"kind": "integer", "value": "4"}},
            {"kind": "struct", "name": "app.Noise", "public": true, "doc": null, "fields": []},
            {
                "kind": "function",
                "name": "app.unused",
                "public": true,
                "doc": "Unused docs.",
                "parameters": [],
                "return_type": {"kind": "primitive", "name": "unit"},
                "contract": {"clauses": []}
            }
        ]}
    });
    let rules = b"shared guidance\ncott-domain app.run return: helper builds Widget with LIMIT\ncott-domain app.other return: leak Noise unused\n";
    let context = cott::intent::context(&surface, "app.run", rules).expect("context");
    let names = context["declarations"]["app"]["declarations"]
        .as_array()
        .expect("decls")
        .iter()
        .map(|declaration| declaration["name"].as_str().expect("name"))
        .collect::<Vec<_>>();
    assert!(names.contains(&"app.run"));
    assert!(names.contains(&"app.helper"));
    assert!(names.contains(&"app.Widget"));
    assert!(names.contains(&"app.LIMIT"));
    assert!(!names.contains(&"app.other"));
    assert!(!names.contains(&"app.Noise"));
    assert!(!names.contains(&"app.unused"));
    let project = context["project_rules"].as_str().expect("rules");
    assert!(project.contains("shared guidance"));
    assert!(project.contains("helper builds Widget with LIMIT"));
    assert!(!project.contains("leak Noise unused"));
    let text = render_text(
        &function_callable("app.run"),
        &surface,
        rules,
        &[
            resolved_binding("app.helper", "HELPER_BODY_UNIQUE\n"),
            resolved_binding("app.unused", "UNUSED_BODY_LEAK\n"),
            resolved_binding("app.other", "OTHER_BODY_LEAK\n"),
        ],
        &BTreeMap::new(),
        None,
        None,
    );
    let references = section(&text, "REFERENCE IMPLEMENTATIONS");
    assert!(references.contains("HELPER_BODY_UNIQUE"));
    assert!(!references.contains("UNUSED_BODY_LEAK"));
    assert!(!references.contains("OTHER_BODY_LEAK"));
    assert!(!section(&text, "FORMAL DECLARATIONS").contains("app.Noise"));
    assert!(!section(&text, "FORMAL DECLARATIONS").contains("app.unused"));
    assert!(!section(&text, "FORMAL DECLARATIONS").contains("app.other"));

    let hashes = cott::intent::fingerprints(&surface, rules).expect("hashes");
    let mut helper_doc = surface.clone();
    helper_doc["app"]["declarations"][1]["doc"] = json!("Changed helper.");
    let helper_hashes = cott::intent::fingerprints(&helper_doc, rules).expect("helper hashes");
    assert_ne!(hashes["app.run"], helper_hashes["app.run"]);
    assert_eq!(hashes["app.other"], helper_hashes["app.other"]);

    let mut widget = surface.clone();
    widget["app"]["declarations"][3]["fields"] =
        json!([{"name": "n", "type": {"kind": "primitive", "name": "i32"}}]);
    let widget_hashes = cott::intent::fingerprints(&widget, rules).expect("widget hashes");
    assert_ne!(hashes["app.run"], widget_hashes["app.run"]);
    assert_eq!(hashes["app.other"], widget_hashes["app.other"]);

    let mut other_doc = surface.clone();
    other_doc["app"]["declarations"][2]["doc"] = json!("Changed other.");
    let other_hashes = cott::intent::fingerprints(&other_doc, rules).expect("other hashes");
    assert_eq!(hashes["app.run"], other_hashes["app.run"]);
    assert_ne!(hashes["app.other"], other_hashes["app.other"]);

    let mut noise = surface.clone();
    noise["app"]["declarations"][5]["fields"] =
        json!([{"name": "n", "type": {"kind": "primitive", "name": "i32"}}]);
    let noise_hashes = cott::intent::fingerprints(&noise, rules).expect("noise hashes");
    assert_eq!(hashes["app.run"], noise_hashes["app.run"]);

    let mut unused_doc = surface.clone();
    unused_doc["app"]["declarations"][6]["doc"] = json!("Changed unused.");
    let unused_hashes = cott::intent::fingerprints(&unused_doc, rules).expect("unused hashes");
    assert_eq!(hashes["app.run"], unused_hashes["app.run"]);
    assert_ne!(hashes["app.unused"], unused_hashes["app.unused"]);
}

#[test]
fn chained_scoped_rule_identifiers_reach_a_fixed_point() {
    let surface = json!({
        "app": {"declarations": [
            {
                "kind": "function",
                "name": "app.run",
                "public": true,
                "doc": null,
                "parameters": [],
                "return_type": {"kind": "primitive", "name": "unit"},
                "contract": {"clauses": []}
            },
            {
                "kind": "function",
                "name": "app.mid",
                "public": true,
                "doc": null,
                "parameters": [],
                "return_type": {"kind": "primitive", "name": "unit"},
                "contract": {"clauses": []}
            },
            {
                "kind": "function",
                "name": "app.leaf",
                "public": true,
                "doc": null,
                "parameters": [],
                "return_type": {"kind": "primitive", "name": "unit"},
                "contract": {"clauses": []}
            },
            {
                "kind": "function",
                "name": "app.other",
                "public": true,
                "doc": "Unrelated docs.",
                "parameters": [],
                "return_type": {"kind": "primitive", "name": "unit"},
                "contract": {"clauses": []}
            }
        ]}
    });
    let rules = b"shared guidance\ncott-domain app.run return: call mid\ncott-domain app.mid return: call leaf\ncott-domain app.leaf return: see run\ncott-domain app.other return: leak me\n";
    let context = cott::intent::context(&surface, "app.run", rules).expect("context");
    let names = context["declarations"]["app"]["declarations"]
        .as_array()
        .expect("decls")
        .iter()
        .map(|declaration| declaration["name"].as_str().expect("name"))
        .collect::<Vec<_>>();
    assert!(names.contains(&"app.run"));
    assert!(names.contains(&"app.mid"));
    assert!(names.contains(&"app.leaf"));
    assert!(!names.contains(&"app.other"));
    let project = context["project_rules"].as_str().expect("rules");
    assert!(project.contains("call mid"));
    assert!(project.contains("call leaf"));
    assert!(project.contains("see run"));
    assert!(!project.contains("leak me"));
    let hashes = cott::intent::fingerprints(&surface, rules).expect("hashes");
    let mut leaf_doc = surface.clone();
    leaf_doc["app"]["declarations"][2]["doc"] = json!("Changed leaf.");
    let leaf_hashes = cott::intent::fingerprints(&leaf_doc, rules).expect("leaf hashes");
    assert_ne!(hashes["app.run"], leaf_hashes["app.run"]);
    assert_ne!(hashes["app.mid"], leaf_hashes["app.mid"]);
    assert_eq!(hashes["app.other"], leaf_hashes["app.other"]);
}

#[test]
fn simple_scalar_prompt_omits_irrelevant_abi_chapters() {
    let surface = json!({
        "app": {"declarations": [
            {
                "kind": "function",
                "name": "app.run",
                "public": true,
                "doc": null,
                "parameters": [],
                "return_type": {"kind": "primitive", "name": "i32"},
                "contract": {"clauses": []}
            }
        ]}
    });
    let text = render_text(
        &function_callable("app.run"),
        &surface,
        b"",
        &[],
        &BTreeMap::new(),
        None,
        None,
    );
    let output = section(&text, "PYTHON OUTPUT RULES");
    assert!(output.contains("Numeric ABI aliases are plain int/float"));
    assert!(output.contains("dynamic import"));
    assert!(output.contains("reflection"));
    assert!(output.contains("dynamic compilation"));
    assert!(output.contains("suppression"));
    assert!(output.contains("standard library"));
    assert!(output.contains("lock-selected"));
    assert!(!output.contains("Factory["));
    assert!(!output.contains("Dyn["));
    assert!(!output.contains("_cott_fixture_"));
    assert!(!output.contains("CottArray"));
    assert!(!output.contains("CottBuffer"));
    assert!(!output.contains("Iterator and Generator"));
    assert!(!output.contains("Scenario fixtures"));
    assert!(!output.contains("`Unit`"));
}

#[test]
fn selected_types_enable_matching_abi_guidance() {
    let surface = json!({
        "app": {"declarations": [
            {
                "kind": "function",
                "name": "app.run",
                "public": true,
                "doc": null,
                "parameters": [
                    {"name": "factory", "type": {"kind": "factory", "instance": {"kind": "named", "name": "lib.Worker", "args": []}}},
                    {"name": "dyn", "type": {"kind": "dyn", "trait": {"kind": "named", "name": "app.Able", "args": []}}},
                    {"name": "thing", "type": {"kind": "named", "name": "lib.Thing", "args": []}}
                ],
                "return_type": {"kind": "array", "item": {"kind": "primitive", "name": "u8"}, "length": {"kind": "value", "value": "4"}},
                "contract": {"clauses": []}
            },
            {"kind": "trait", "name": "app.Able", "public": true, "doc": null, "methods": []},
            {"kind": "scenario", "name": "app.RunCase", "public": true, "target": "app.run", "steps": [], "doc": null}
        ]},
        "lib": {"declarations": [
            {"kind": "impl", "name": "lib.Worker", "public": true, "doc": null, "selected_methods": [], "methods": []},
            {"kind": "struct", "name": "lib.Thing", "public": true, "doc": "A lib thing.", "fields": []}
        ]}
    });
    let text = render_text(
        &function_callable("app.run"),
        &surface,
        b"",
        &[],
        &BTreeMap::new(),
        None,
        None,
    );
    let output = section(&text, "PYTHON OUTPUT RULES");
    assert!(output.contains("Factory[Concrete]"));
    assert!(output.contains("from lib import Worker"));
    assert!(output.contains("from lib_types import Thing"));
    assert!(output.contains("Dyn[Trait]"));
    assert!(output.contains("CottArray(values="));
    assert!(output.contains("_cott_fixture_"));
    let formal = section(&text, "FORMAL DECLARATIONS");
    assert!(formal.contains("app.Able"));
    assert!(formal.contains("lib.Worker"));
    assert!(formal.contains("lib.Thing"));
    assert!(formal.contains("app.RunCase"));
    assert!(!formal.contains("A lib thing."));
    assert!(section(&text, "CURRENT INTENT").contains("lib.Thing"));
    assert!(section(&text, "CURRENT INTENT").contains("A lib thing."));
}

#[test]
fn async_and_impl_ownership_are_explicit() {
    let async_surface = json!({
        "app": {"declarations": [
            {
                "kind": "function",
                "name": "app.fetch",
                "public": true,
                "doc": null,
                "parameters": [],
                "return_type": {"kind": "primitive", "name": "i32"},
                "contract": {"clauses": []}
            }
        ]}
    });
    let mut async_callable = function_callable("app.fetch");
    async_callable.kind = PythonCallableKind::AsyncFunction;
    let async_text = render_text(
        &async_callable,
        &async_surface,
        b"",
        &[],
        &BTreeMap::new(),
        None,
        None,
    );
    let async_output = section(&async_text, "PYTHON OUTPUT RULES");
    assert!(async_output.contains("canonical undecorated top-level `async def` function `fetch`"));
    assert!(async_output.contains("Await every call to an async Cott facade"));
    assert!(async_output.contains("additional async functions"));
    assert!(async_output.contains("asyncio.TaskGroup"));

    let impl_surface = json!({
        "foo.bar": {"declarations": [
            {
                "kind": "impl",
                "name": "foo.bar.Reader",
                "public": true,
                "doc": null,
                "init": {"contracts": {"doc": "Build the reader."}, "parameters": []},
                "selected_methods": [{
                    "trait_method": "foo.bar.Readable.read",
                    "selected": {"origin": "explicit"},
                    "callable_kind": "sync"
                }],
                "methods": [{"name": "read", "doc": "Read bytes."}]
            }
        ]}
    });
    let impl_callable = PythonCallable {
        module: "foo.bar".to_owned(),
        cott_symbol: "foo.bar.Reader.read".to_owned(),
        name: "read".to_owned(),
        kind: PythonCallableKind::ImplMethod {
            concrete: "Reader".to_owned(),
        },
        declaration: json!({}),
        owner: Some(json!({})),
    };
    let impl_text = render_text(
        &impl_callable,
        &impl_surface,
        b"",
        &[],
        &BTreeMap::new(),
        None,
        None,
    );
    assert!(section(&impl_text, "CURRENT INTENT").contains("foo.bar.Reader.read (target)"));
    assert!(section(&impl_text, "CURRENT INTENT").contains("foo.bar.Reader.init"));
    assert!(section(&impl_text, "CURRENT INTENT").contains("Build the reader."));
    assert!(section(&impl_text, "CURRENT INTENT").contains("Read bytes."));
    assert!(!section(&impl_text, "FORMAL DECLARATIONS").contains("Build the reader."));
    assert!(!section(&impl_text, "FORMAL DECLARATIONS").contains("Read bytes."));
    let impl_output = section(&impl_text, "PYTHON OUTPUT RULES");
    assert!(impl_output.contains("canonical private top-level function `_cott_impl_Reader_read`"));
    assert!(impl_output.contains("self: Reader"));
    assert!(impl_output.contains("from `foo.bar`"));
    assert!(impl_output.contains("from foo.bar import Reader"));
    let mut async_impl = impl_callable.clone();
    async_impl.kind = PythonCallableKind::AsyncImplMethod {
        concrete: "Reader".to_owned(),
    };
    async_impl.cott_symbol = "foo.bar.Reader.read".to_owned();
    let async_impl_text = render_text(
        &async_impl,
        &impl_surface,
        b"",
        &[],
        &BTreeMap::new(),
        None,
        None,
    );
    let async_impl_output = section(&async_impl_text, "PYTHON OUTPUT RULES");
    assert!(
        async_impl_output
            .contains("canonical private top-level `async def` function `_cott_impl_Reader_read`")
    );
    assert!(async_impl_output.contains("asyncio.TaskGroup"));
    assert!(
        async_impl_output.contains("Await every call to an async Cott facade or sibling method")
    );
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
            declaration: json!({"selected": {"origin": "specialization"}}),
            owner: Some(json!({})),
        },
        &json!({}),
        &[],
        &BTreeMap::new(),
        None,
        None,
        Path::new("implementation.py"),
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
fn ordinary_rule_prose_is_ignored_by_the_domain_parser() {
    let rules = b"Must return safely.\nordinary cott-domain-like prose\ncott-domain app.fetch return: exact \xff bytes\n";
    let parsed = parse_domain_rules(Path::new("generator.rules"), rules);
    assert!(parsed.rules.is_empty());
    assert_eq!(parsed.diagnostics.len(), 1);
}

#[test]
fn retry_feedback_is_not_a_project_rule_and_existing_is_a_reference() {
    let surface = json!({
        "app": {"declarations": [
            {
                "kind": "function",
                "name": "app.run",
                "public": true,
                "doc": "Run the selected job.",
                "parameters": [],
                "return_type": {"kind": "primitive", "name": "i32"},
                "contract": {"clauses": []}
            }
        ]}
    });
    let text = render_text(
        &function_callable("app.run"),
        &surface,
        b"shared guidance\n",
        &[],
        &BTreeMap::new(),
        Some(b"PREVIOUS_CANDIDATE\n"),
        Some("type error: missing return\n"),
    );
    assert!(section(&text, "PROJECT RULES").contains("shared guidance"));
    assert!(!section(&text, "PROJECT RULES").contains("type error"));
    assert!(!section(&text, "CURRENT INTENT").contains("PREVIOUS_CANDIDATE"));
    let references = section(&text, "REFERENCE IMPLEMENTATIONS");
    assert!(references.contains("## app.run (existing)"));
    assert!(references.contains("PREVIOUS_CANDIDATE"));
    let feedback = section(&text, "VALIDATION FEEDBACK");
    assert!(feedback.contains("type error: missing return"));
    assert!(feedback.contains("do not add business requirements"));
}

#[test]
fn malformed_context_utf8_and_size_are_rejected() {
    let callable = function_callable("app.run");
    let write_path = Path::new("implementation.py");
    let err = render_prompt(
        &callable,
        &json!(null),
        &[],
        &BTreeMap::new(),
        None,
        None,
        write_path,
    )
    .expect_err("null context");
    assert!(err.contains("intent context must be an object"));

    let err = render_prompt(
        &callable,
        &json!({"symbol": "app.other", "declarations": {}, "project_rules": ""}),
        &[],
        &BTreeMap::new(),
        None,
        None,
        write_path,
    )
    .expect_err("symbol mismatch");
    assert!(err.contains("does not match callable"));

    let err = render_prompt(
        &callable,
        &json!({"symbol": "app.run", "declarations": {}, "project_rules": ""}),
        &[],
        &BTreeMap::new(),
        Some(&[0xff]),
        None,
        write_path,
    )
    .expect_err("non utf-8 existing");
    assert!(err.contains("UTF-8"));

    let huge = vec![b'x'; 1024 * 1024 + 1];
    let err = render_prompt(
        &callable,
        &json!({"symbol": "app.run", "declarations": {}, "project_rules": ""}),
        &[],
        &BTreeMap::new(),
        Some(&huge),
        None,
        write_path,
    )
    .expect_err("oversized existing");
    assert!(err.contains("1 MiB"));

    let surface = json!({
        "app": {"declarations": [
            {
                "kind": "function",
                "name": "app.run",
                "public": true,
                "doc": "Delegate to helper.",
                "parameters": [],
                "return_type": {"kind": "primitive", "name": "i32"},
                "contract": {"clauses": []}
            },
            {
                "kind": "function",
                "name": "app.helper",
                "public": true,
                "doc": null,
                "parameters": [],
                "return_type": {"kind": "primitive", "name": "i32"},
                "contract": {"clauses": []}
            }
        ]}
    });
    let context = cott::intent::context(&surface, "app.run", b"").expect("context");
    let huge_ref = resolved_binding("app.helper", "y");
    let mut huge_ref = huge_ref;
    huge_ref.bytes = huge;
    let err = render_prompt(
        &callable,
        &context,
        &[huge_ref],
        &BTreeMap::new(),
        None,
        None,
        write_path,
    )
    .expect_err("oversized reference");
    assert!(err.contains("1 MiB"));

    let mut unrelated = resolved_binding("app.other", "UNRELATED_OVERSIZE_BODY\n");
    unrelated.bytes = vec![b'x'; 1024 * 1024 + 1];
    let kept = String::from_utf8(
        render_prompt(
            &callable,
            &context,
            &[unrelated],
            &BTreeMap::new(),
            None,
            None,
            write_path,
        )
        .expect("unrelated oversize excluded"),
    )
    .expect("utf-8");
    assert!(!kept.contains("UNRELATED_OVERSIZE_BODY"));
    assert!(kept.contains("FORMAL DECLARATIONS"));

    let mut invalid = resolved_binding("app.other", "x");
    invalid.bytes = vec![0xff];
    render_prompt(
        &callable,
        &context,
        &[invalid],
        &BTreeMap::new(),
        None,
        None,
        write_path,
    )
    .expect("unrelated non-utf8 excluded");
}

#[test]
fn aggregate_prompt_budget_preserves_individually_bounded_references() {
    let references = (0..9)
        .map(|index| {
            let mut binding = resolved_binding(&format!("app.helper{index}"), "");
            binding.bytes = vec![b'x'; 1024 * 1024];
            binding
        })
        .collect::<Vec<_>>();
    let helpers = (0..9)
        .map(|index| format!("app.helper{index}"))
        .collect::<Vec<_>>();
    let mut declarations = vec![json!({
        "kind": "function", "name": "app.run", "public": true,
        "doc": format!("Delegate to {}.", helpers.join(", ")),
        "parameters": [], "return_type": {"kind":"primitive","name":"i32"},
        "contract": {"clauses":[]}
    })];
    declarations.extend(helpers.iter().map(|name| {
        json!({
            "kind":"function", "name":name, "public":true, "doc":null,
            "parameters":[], "return_type":{"kind":"primitive","name":"i32"},
            "contract":{"clauses":[]}
        })
    }));
    let context = cott::intent::context(
        &json!({"app":{"declarations":declarations}}),
        "app.run",
        b"",
    )
    .expect("scoped helper context");
    let callable = function_callable("app.run");
    let accepted = render_prompt(
        &callable,
        &context,
        &references[..2],
        &BTreeMap::new(),
        None,
        None,
        Path::new("implementation.py"),
    )
    .expect("aggregate prompt may exceed individual input ceiling");
    assert!(accepted.len() > 2 * 1024 * 1024);
    let error = render_prompt(
        &callable,
        &context,
        &references,
        &BTreeMap::new(),
        None,
        None,
        Path::new("implementation.py"),
    )
    .expect_err("aggregate prompt remains bounded");
    assert!(error.contains("rendered agent prompt exceeds"), "{error}");
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

#[test]
fn named_trait_without_dyn_omits_dyn_wrapper_guidance() {
    let surface = json!({
        "app": {"declarations": [
            {
                "kind": "function",
                "name": "app.run",
                "public": true,
                "doc": null,
                "parameters": [{"name": "able", "type": {"kind": "named", "name": "app.Able", "args": []}}],
                "return_type": {"kind": "primitive", "name": "i32"},
                "contract": {"clauses": []}
            },
            {"kind": "trait", "name": "app.Able", "public": true, "doc": null, "methods": []}
        ]}
    });
    let text = render_text(
        &function_callable("app.run"),
        &surface,
        b"",
        &[],
        &BTreeMap::new(),
        None,
        None,
    );
    let output = section(&text, "PYTHON OUTPUT RULES");
    assert!(!output.contains("Dyn["));
    assert!(output.contains("from app_types import Able"));
    assert!(section(&text, "FORMAL DECLARATIONS").contains("app.Able"));
}

#[test]
fn contract_constant_ref_selects_limit_and_invalidates_on_limit_only() {
    let original = r#"module api.service

doc """Cap the selected result."""
const LIMIT: I32 = 4

doc """Unrelated noise constant."""
const NOISE: I32 = 1

fn run() -> I32:
    ensures result <= LIMIT

fn other() -> Unit

trait Reader:
    fn read(self, amount: I32) -> I32

impl ReaderState for Reader:
    fn read(self, amount: I32) -> I32:
        ensures result <= LIMIT
"#;
    let surface = compiled_surface(original);
    let context = cott::intent::context(&surface, "api.service.run", b"").expect("context");
    let names = selected_names(&context);
    assert!(names.contains(&"api.service.run"));
    assert!(names.contains(&"api.service.LIMIT"));
    assert!(!names.contains(&"api.service.NOISE"));
    assert!(!names.contains(&"api.service.other"));
    let limit = context["declarations"]["api.service"]["declarations"]
        .as_array()
        .expect("decls")
        .iter()
        .find(|declaration| declaration["name"] == "api.service.LIMIT")
        .expect("LIMIT");
    assert_eq!(limit["value"]["kind"], "integer");
    assert_eq!(limit["value"]["value"], "4");
    let run = context["declarations"]["api.service"]["declarations"]
        .as_array()
        .expect("decls")
        .iter()
        .find(|declaration| declaration["name"] == "api.service.run")
        .expect("run");
    let run_json = serde_json::to_string(run).expect("run json");
    assert!(run_json.contains(r#""kind":"constant_ref""#));
    assert!(run_json.contains(r#""kind":"constant""#));
    assert!(run_json.contains("api.service.LIMIT"));
    let text = render_text(
        &function_callable("api.service.run"),
        &surface,
        b"",
        &[],
        &BTreeMap::new(),
        None,
        None,
    );
    let intent = section(&text, "CURRENT INTENT");
    assert!(intent.contains("Cap the selected result."));
    assert!(!intent.contains("Unrelated noise constant."));
    let formal = section(&text, "FORMAL DECLARATIONS");
    assert!(formal.contains("api.service.LIMIT"));
    assert!(formal.contains("constant_ref"));
    assert!(!formal.contains("api.service.NOISE"));
    assert!(!formal.contains("Cap the selected result."));

    let method_context =
        cott::intent::context(&surface, "api.service.ReaderState.read", b"").expect("method");
    let method_names = selected_names(&method_context);
    assert!(method_names.contains(&"api.service.LIMIT"));
    assert!(!method_names.contains(&"api.service.NOISE"));

    let hashes = cott::intent::fingerprints(&surface, b"").expect("hashes");
    let limit_value_hashes = cott::intent::fingerprints(
        &compiled_surface(&original.replace("const LIMIT: I32 = 4", "const LIMIT: I32 = 8")),
        b"",
    )
    .expect("limit value hashes");
    assert_ne!(
        hashes["api.service.run"],
        limit_value_hashes["api.service.run"]
    );
    assert_ne!(
        hashes["api.service.ReaderState.read"],
        limit_value_hashes["api.service.ReaderState.read"]
    );
    assert_eq!(
        hashes["api.service.other"],
        limit_value_hashes["api.service.other"]
    );

    let limit_doc_hashes = cott::intent::fingerprints(
        &compiled_surface(
            &original.replace("Cap the selected result.", "Changed limit documentation."),
        ),
        b"",
    )
    .expect("limit doc hashes");
    assert_ne!(
        hashes["api.service.run"],
        limit_doc_hashes["api.service.run"]
    );
    assert_ne!(
        hashes["api.service.ReaderState.read"],
        limit_doc_hashes["api.service.ReaderState.read"]
    );
    assert_eq!(
        hashes["api.service.other"],
        limit_doc_hashes["api.service.other"]
    );

    let noise_hashes = cott::intent::fingerprints(
        &compiled_surface(&original.replace("const NOISE: I32 = 1", "const NOISE: I32 = 9")),
        b"",
    )
    .expect("noise hashes");
    assert_eq!(hashes["api.service.run"], noise_hashes["api.service.run"]);
    assert_eq!(
        hashes["api.service.ReaderState.read"],
        noise_hashes["api.service.ReaderState.read"]
    );
    assert_eq!(
        hashes["api.service.other"],
        noise_hashes["api.service.other"]
    );
}

#[test]
fn applied_rule_metadata_selects_child_and_base_docs() {
    let original = r#"module api.service

rule Base:
    doc """Require a boolean gate."""
    requires true

rule Child(Base):
    doc """Inherit parent obligations."""
    override requires false

rule Unrelated:
    doc """Ignore this extra rule."""
    requires true

fn run() -> Unit:
    doc """
    Return a bounded value.
    """
    rule Child

fn other() -> Unit
"#;
    let surface = compiled_surface(original);
    let context = cott::intent::context(&surface, "api.service.run", b"").expect("context");
    let names = selected_names(&context);
    assert!(names.contains(&"api.service.run"));
    assert!(names.contains(&"api.service.Child"));
    assert!(names.contains(&"api.service.Base"));
    assert!(!names.contains(&"api.service.Unrelated"));
    assert!(!names.contains(&"api.service.other"));
    let text = render_text(
        &function_callable("api.service.run"),
        &surface,
        b"",
        &[],
        &BTreeMap::new(),
        None,
        None,
    );
    let intent = section(&text, "CURRENT INTENT");
    assert!(intent.contains("Return a bounded value."));
    assert!(intent.contains("Inherit parent obligations."));
    assert!(intent.contains("Require a boolean gate."));
    assert!(!intent.contains("Ignore this extra rule."));
    let formal = section(&text, "FORMAL DECLARATIONS");
    assert!(formal.contains("api.service.Child"));
    assert!(formal.contains("api.service.Base"));
    assert!(!formal.contains("api.service.Unrelated"));
    assert!(!formal.contains("Inherit parent obligations."));
    assert!(!formal.contains("Require a boolean gate."));

    let hashes = cott::intent::fingerprints(&surface, b"").expect("hashes");
    let child_doc_hashes = cott::intent::fingerprints(
        &compiled_surface(&original.replace(
            "Inherit parent obligations.",
            "Changed child documentation.",
        )),
        b"",
    )
    .expect("child doc hashes");
    assert_ne!(
        hashes["api.service.run"],
        child_doc_hashes["api.service.run"]
    );
    assert_eq!(
        hashes["api.service.other"],
        child_doc_hashes["api.service.other"]
    );

    let base_doc_hashes = cott::intent::fingerprints(
        &compiled_surface(
            &original.replace("Require a boolean gate.", "Changed base documentation."),
        ),
        b"",
    )
    .expect("base doc hashes");
    assert_ne!(
        hashes["api.service.run"],
        base_doc_hashes["api.service.run"]
    );
    assert_eq!(
        hashes["api.service.other"],
        base_doc_hashes["api.service.other"]
    );

    let unrelated_doc_hashes = cott::intent::fingerprints(
        &compiled_surface(&original.replace(
            "Ignore this extra rule.",
            "Changed unrelated documentation.",
        )),
        b"",
    )
    .expect("unrelated doc hashes");
    assert_eq!(
        hashes["api.service.run"],
        unrelated_doc_hashes["api.service.run"]
    );
    assert_eq!(
        hashes["api.service.other"],
        unrelated_doc_hashes["api.service.other"]
    );
}

#[test]
fn valid_model_accepts_ordinary_names_and_rejects_malformed_ones() {
    for model in [
        "gpt-5-codex",
        "gpt-5-codex high",
        "claude-opus-5-5",
        "omp/17.2.13",
        "a",
    ] {
        assert!(valid_model(model), "{model:?} should be accepted");
    }
    for model in [
        "",
        " gpt-5",
        "gpt-5 ",
        " gpt-5 ",
        "-gpt-5",
        "gpt-5\n",
        "gpt-5\t",
        "gpt\u{0}5",
    ] {
        assert!(!valid_model(model), "{model:?} should be rejected");
    }
}

#[test]
fn pi_adapter_contract_is_an_independent_json_mode_cli() {
    assert_eq!(adapter(AgentKind::Pi), &PI);
    assert_eq!(PI.executable_name, "pi");
    assert_eq!(PI.minimum_version, "1.0.4");
    assert_eq!(PI_UNSUPPORTED_MAJOR, 2);
    assert_eq!(PI_MINIMUM_NODE_VERSION, "22.19.0");
    assert_eq!(PI.version_argv, &["--version"]);
    assert_eq!(
        PI.argv_template,
        &["--mode", "json", "--no-session", "--", "<prompt>"]
    );
    assert!(!PI.prompt_on_stdin);
    // One argv element carries at most MAX_ARG_STRLEN - 1 bytes (32 pages).
    let page = usize::try_from(unsafe { libc::sysconf(libc::_SC_PAGESIZE) }).expect("page size");
    assert_eq!(pi_max_prompt_bytes(), 32 * page - 1);
    assert_ne!(adapter(AgentKind::Pi), adapter(AgentKind::Omp));
}

#[test]
fn agents_inherit_the_caller_environment_except_cott_and_parent_session_markers() {
    // Configuration and credential variables are inherited unchanged; only
    // the variables cott sets and markers of a parent agent session are not.
    assert_eq!(
        AGENT_NOT_INHERITED,
        [
            "CLAUDECODE",
            "CLAUDE_CODE_ENTRYPOINT",
            "CODEX_SANDBOX",
            "CODEX_SANDBOX_NETWORK_DISABLED",
            "HOME",
            "OLDPWD",
            "PI_MODEL",
            "PI_PROVIDER",
            "PI_REASONING_LEVEL",
            "PI_SESSION_FILE",
            "PI_SESSION_ID",
            "PWD",
            "SHLVL",
            "TMPDIR",
            "_",
        ]
    );
    for configuration in [
        "PI_CODING_AGENT_DIR",
        "CODEX_HOME",
        "CLAUDE_CONFIG_DIR",
        "OPENAI_API_KEY",
        "ANTHROPIC_API_KEY",
        "CLIPROXYAPI_API_KEY",
        "PATH",
        "HTTPS_PROXY",
    ] {
        assert!(
            !AGENT_NOT_INHERITED.contains(&configuration),
            "{configuration}"
        );
    }
    assert_eq!(
        PROJECT_RESOURCES,
        [
            ".agent",
            ".agents",
            ".claude",
            ".clinerules",
            ".codex",
            ".cursor",
            ".cursorrules",
            ".gemini",
            ".github/copilot-instructions.md",
            ".github/instructions",
            ".mcp.json",
            ".omp",
            ".opencode",
            ".pi",
            ".vscode/mcp.json",
            ".windsurf",
            ".windsurfrules",
            "AGENTS.MD",
            "AGENTS.md",
            "AGENTS.override.md",
            "CLAUDE.MD",
            "CLAUDE.local.md",
            "CLAUDE.md",
            "mcp.json",
            "opencode.json",
            "opencode.jsonc",
        ]
    );
}

// Real Pi 1.0.4 `--mode json` stdout captured from the installed CLI against a
// local mock OpenAI-compatible endpoint (no real provider, no credential);
// absolute paths were replaced with `/workspace` and `/pi`.
const REAL_PI_SUCCESS: &str = include_str!("fixtures/pi/real-1.0.4-success.jsonl");
const REAL_PI_PROVIDER_ERROR: &str = include_str!("fixtures/pi/real-1.0.4-provider-error.jsonl");
const REAL_PI_PROMPT: &str = include_str!("fixtures/pi/real-1.0.4-prompt.txt");
fn validate_real(stream: &str) -> Result<PiStreamSummary, String> {
    validate_pi_json_stream(
        stream.as_bytes(),
        &[Path::new("/workspace")],
        REAL_PI_PROMPT,
    )
}

#[test]
fn pi_stream_reports_the_models_that_answered_without_a_requested_provider() {
    let probe = "cott-probe/probe-model".to_owned();
    assert_eq!(
        validate_real(REAL_PI_SUCCESS).expect("real Pi success transcript"),
        PiStreamSummary {
            models: vec![probe.clone()],
            final_model: probe.clone(),
        }
    );
    // The caller's default model, a pattern or an extension provider decide
    // the attribution; it is reported, never compared with a request.
    let routed = edit_stream(REAL_PI_SUCCESS, |records| {
        let at = position(records, "message_end");
        records[at]["message"]["provider"] = serde_json::json!("cliproxyapi");
        records[at]["message"]["model"] = serde_json::json!("gpt-6.1-sol");
    });
    let summary = validate_real(&routed).expect("extension provider answer");
    assert_eq!(summary.final_model, "cliproxyapi/gpt-6.1-sol");
    assert_eq!(
        summary.models,
        [probe, "cliproxyapi/gpt-6.1-sol".to_owned()]
    );
}

#[test]
fn pi_stream_accepts_user_tools_and_extension_follow_up_messages() {
    let user_tool = edit_stream(REAL_PI_SUCCESS, |records| {
        let at = position(records, "turn_end");
        records.insert(
            at,
            serde_json::json!({"type": "tool_execution_end", "toolCallId": "x", "toolName": "codegraph_search", "result": {}, "isError": false}),
        );
        records.insert(
            at,
            serde_json::json!({"type": "tool_execution_start", "toolCallId": "x", "toolName": "codegraph_search", "args": {}}),
        );
    });
    validate_real(&user_tool).expect("tools of the caller's setup are not restricted");
    let bash = edit_stream(REAL_PI_SUCCESS, |records| {
        let at = position(records, "turn_end");
        records.insert(
            at,
            serde_json::json!({"type": "tool_execution_end", "toolCallId": "y", "toolName": "bash", "result": {}, "isError": false}),
        );
    });
    validate_real(&bash).expect("executed bash is the caller's own tool choice");
    let follow_up = edit_stream(REAL_PI_SUCCESS, |records| {
        let at = position(records, "turn_end");
        records.insert(
            at,
            serde_json::json!({"type": "message_end", "message": {"role": "user", "content": [{"type": "text", "text": "extension follow-up"}]}}),
        );
    });
    validate_real(&follow_up).expect("a later user message comes from an extension");
}

fn edit_stream(stream: &str, edit: impl FnOnce(&mut Vec<serde_json::Value>)) -> String {
    let mut records = stream
        .lines()
        .map(|line| serde_json::from_str(line).expect("fixture record"))
        .collect::<Vec<serde_json::Value>>();
    edit(&mut records);
    records.iter().map(|record| format!("{record}\n")).collect()
}

fn position(records: &[serde_json::Value], kind: &str) -> usize {
    records
        .iter()
        .rposition(|record| record["type"] == kind)
        .unwrap_or_else(|| panic!("fixture lacks {kind}"))
}

#[test]
fn pi_stream_accepts_real_multi_turn_tool_use_and_exact_prompt() {
    assert_eq!(
        REAL_PI_PROMPT,
        "  \n\tLeading/trailing whitespace, 'single' \"double\" `tick` $(touch x) \\ 한글 ✓ — write implementation.py\n\n  "
    );
    validate_real(REAL_PI_SUCCESS).expect("real Pi success transcript");
    validate_real(&REAL_PI_SUCCESS.replace('\n', "\r\n")).expect("CRLF framing is documented");
    validate_real(&edit_stream(REAL_PI_SUCCESS, |_| {})).expect("re-serialized transcript");
    let refused_tool = edit_stream(REAL_PI_SUCCESS, |records| {
        let at = position(records, "turn_end");
        records.insert(
            at,
            serde_json::json!({"type": "tool_execution_end", "toolCallId": "x", "toolName": "bash", "result": {}, "isError": true}),
        );
    });
    validate_real(&refused_tool).expect("a refused unknown tool was not executed");
}

#[test]
fn pi_stream_rejects_real_exit_zero_provider_error() {
    let error = validate_real(REAL_PI_PROVIDER_ERROR).expect_err("real Pi provider error");
    assert!(
        error
            .contains("final assistant message from `cott-probe/probe-model` stopped with `error`"),
        "{error}"
    );
}

#[test]
fn pi_stream_rejects_contaminated_incomplete_conflicting_and_mismatched_records() {
    let cases: Vec<(&str, String, &str)> = vec![
        ("empty", String::new(), "complete JSONL record"),
        (
            "unterminated",
            REAL_PI_SUCCESS.trim_end().to_owned(),
            "complete JSONL record",
        ),
        (
            "prefix",
            format!("Warning: noise\n{REAL_PI_SUCCESS}"),
            "line 1 is not a JSON object",
        ),
        (
            "blank",
            REAL_PI_SUCCESS.replacen('\n', "\n\n", 1),
            "line 2 is not a JSON object",
        ),
        (
            "array",
            format!("[]\n{REAL_PI_SUCCESS}"),
            "line 1 is not a JSON object",
        ),
        (
            "untyped",
            edit_stream(REAL_PI_SUCCESS, |records| {
                records.insert(1, serde_json::json!({"kind": "x"}))
            }),
            "line 2 has no string `type`",
        ),
        (
            "unsettled",
            edit_stream(REAL_PI_SUCCESS, |records| {
                records.pop();
            }),
            "does not end with `agent_settled`",
        ),
        (
            "early-settled",
            edit_stream(REAL_PI_SUCCESS, |records| {
                records.insert(2, serde_json::json!({"type": "agent_settled"}))
            }),
            "settles before the stream ends",
        ),
        (
            "second-header",
            edit_stream(REAL_PI_SUCCESS, |records| {
                let header = records[0].clone();
                records.insert(1, header);
            }),
            "repeats the session header",
        ),
        (
            "header-version",
            edit_stream(REAL_PI_SUCCESS, |records| {
                records[0]["version"] = serde_json::json!(2)
            }),
            "version 3 session header",
        ),
        (
            "header-cwd",
            edit_stream(REAL_PI_SUCCESS, |records| {
                records[0]["cwd"] = serde_json::json!("/elsewhere")
            }),
            "session header cwd is not the isolated workspace",
        ),
        (
            "no-agent-end",
            edit_stream(REAL_PI_SUCCESS, |records| {
                let at = position(records, "agent_end");
                records.remove(at);
            }),
            "unbalanced",
        ),
        (
            "retrying",
            edit_stream(REAL_PI_SUCCESS, |records| {
                let at = position(records, "agent_end");
                records[at]["willRetry"] = serde_json::json!(true);
            }),
            "still schedules a retry",
        ),
        (
            "aborted",
            edit_stream(REAL_PI_SUCCESS, |records| {
                let at = position(records, "message_end");
                records[at]["message"]["stopReason"] = serde_json::json!("aborted");
            }),
            "stopped with `aborted`",
        ),
        (
            "unknown-stop",
            edit_stream(REAL_PI_SUCCESS, |records| {
                let at = position(records, "message_end");
                records[at]["message"]["stopReason"] = serde_json::json!("done");
            }),
            "no valid `stopReason`",
        ),
        (
            "unattributed",
            edit_stream(REAL_PI_SUCCESS, |records| {
                let at = position(records, "message_end");
                records[at]["message"]["provider"] = serde_json::json!("");
            }),
            "assistant message has no `provider`",
        ),
        (
            "altered-prompt",
            REAL_PI_SUCCESS.replace("Leading/trailing", "Leading trailing"),
            "user message differs from the exact prompt",
        ),
        (
            "no-user",
            edit_stream(REAL_PI_SUCCESS, |records| {
                records.retain(|record| record["message"]["role"] != "user");
            }),
            "no user message carries the prompt",
        ),
        (
            "unknown-event",
            edit_stream(REAL_PI_SUCCESS, |records| {
                records.insert(2, serde_json::json!({"type": "extension_error"}))
            }),
            "unsupported event `extension_error`",
        ),
        (
            "bash-output",
            edit_stream(REAL_PI_SUCCESS, |records| {
                records.insert(2, serde_json::json!({"type": "bash_execution_update"}))
            }),
            "unsupported event `bash_execution_update`",
        ),
        (
            "unnamed-tool",
            edit_stream(REAL_PI_SUCCESS, |records| {
                let at = position(records, "turn_end");
                records.insert(
                    at,
                    serde_json::json!({"type": "tool_execution_start", "toolCallId": "x"}),
                );
            }),
            "tool event lacks `toolName`",
        ),
        (
            "failed-retry",
            edit_stream(REAL_PI_SUCCESS, |records| {
                records.insert(
                    2,
                    serde_json::json!({"type": "auto_retry_end", "success": false, "attempt": 3}),
                );
            }),
            "failed automatic retry",
        ),
    ];
    for (case, stream, expected) in cases {
        let error = validate_real(&stream).expect_err(case);
        assert!(error.contains(expected), "{case}: {error}");
    }
    let error = validate_pi_json_stream(
        REAL_PI_SUCCESS.as_bytes(),
        &[Path::new("/workspace")],
        REAL_PI_PROMPT.trim(),
    )
    .expect_err("trimmed prompt");
    assert!(error.contains("differs from the exact prompt"), "{error}");
}
