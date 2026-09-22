use std::collections::BTreeMap;
use std::path::{Path, PathBuf};

use cott::agent::{
    AgentKind, CLAUDE, CODEX, OMP, ShadowFacet, adapter, has_normative_modal, parse_domain_rules,
    render_prompt, scan_doc_candidates, sentence_has_facet,
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
    assert_eq!(CLAUDE.executable_name, "claude");
    assert_eq!(CLAUDE.minimum_version, "2.1.89");
    assert_eq!(CLAUDE.version_argv, &["--version"]);
    assert_eq!(
        CLAUDE.argv_template,
        &[
            "--bare",
            "--print",
            "--input-format",
            "text",
            "--output-format",
            "json",
            "--permission-mode",
            "dontAsk",
            "--tools",
            "Read,Write",
            "--allowedTools",
            "Read,Write",
            "--disallowedTools",
            "Bash,Edit,Glob,Grep,WebFetch,WebSearch,Task,mcp__*",
            "--no-session-persistence",
        ]
    );
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
            "@<prompt-file>",
        ]
    );
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
