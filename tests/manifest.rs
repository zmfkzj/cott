use std::path::Path;

use cott::manifest::{
    DartProjectConfig, KotlinProjectConfig, MAX_CANDIDATE_LIMIT, MAX_FILESYSTEM_BYTES,
    MAX_FILESYSTEM_FILES, MAX_HTTP_BODY_BYTES, MAX_HTTP_REDIRECTS, MAX_HTTP_REQUESTS,
    MAX_LIFECYCLE_LIMIT, MAX_PROOF_BRANCH_LIMIT, MAX_PROOF_NODE_LIMIT, MAX_SCENARIO_TIMEOUT_MS,
    MAX_TRANSCRIPT_EVENTS, ProjectConfig, RuntimeValidation, TargetLanguage, target_language,
};

const VALID: &str = r#"
[project]
name = "demo"
version = "0.1.0"
source = "src"

[target.python]
source = "python"
generated = "generated/python"
stubs = "generated/stubs"
interpreter = ".venv/bin/python"
type_checker = ".venv/bin/basedpyright"
runtime_validation = "boundary"
"#;

const VALID_KOTLIN: &str = r#"
[project]
name = "demo"
version = "0.1.0"
source = "src"

[target.kotlin]
source = "kotlin-src"
generated = "generated/kotlin"
runtime_validation = "boundary"
classpath = ["libs/runtime.jar"]
compile_only = ["libs/android.jar"]

[target.kotlin.implementations]
"demo.fetch" = "demo.impl.fetch"

[target.kotlin.external_types]
"demo.AndroidContext" = "android.content.Context"
"#;

const VALID_DART: &str = r#"
[project]
name = "demo_app"
version = "0.1.0"
source = "src"

[target.dart]
source = "dart-src"
generated = "generated/dart"
runtime_validation = "boundary"

[target.dart.implementations]
"demo.fetch" = "impl/fetch.dart:_fetch"

[target.dart.external_types]
"demo.Instant" = "dart:core#DateTime"
"demo.Widget" = "package:flutter/widgets.dart#Widget"
"demo.AsyncMemoizer" = "package:async/async.dart#AsyncMemoizer"
"#;

#[test]
fn parses_the_closed_v1_manifest() {
    let manifest =
        ProjectConfig::parse(Path::new("cott.toml"), VALID).expect("manifest should parse");
    assert_eq!(manifest.project.version, "0.1.0");
    assert_eq!(
        manifest.python.runtime_validation,
        RuntimeValidation::Boundary
    );
    assert_eq!(manifest.generator.timeout_seconds, 900);
}

#[test]
fn defaults_verification_budgets() {
    let manifest =
        ProjectConfig::parse(Path::new("cott.toml"), VALID).expect("manifest should parse");
    assert_eq!(manifest.verification.proof_node_limit, 1024);
    assert_eq!(manifest.verification.proof_branch_limit, 256);
    assert_eq!(manifest.verification.candidate_limit, 64);
    assert_eq!(manifest.verification.lifecycle_limit, 3);
}

#[test]
fn defaults_closed_fixture_limits_and_coverage_policy() {
    let manifest =
        ProjectConfig::parse(Path::new("cott.toml"), VALID).expect("manifest should parse");
    assert_eq!(manifest.verification.fixtures.scenario_timeout_ms, 1000);
    assert_eq!(manifest.verification.fixtures.filesystem_bytes, 16_777_216);
    assert_eq!(manifest.verification.fixtures.filesystem_files, 256);
    assert_eq!(manifest.verification.fixtures.http_body_bytes, 1_048_576);
    assert_eq!(manifest.verification.fixtures.http_requests, 64);
    assert_eq!(manifest.verification.fixtures.http_redirects, 8);
    assert_eq!(manifest.verification.fixtures.transcript_events, 1024);
    assert!(manifest.verification.coverage.rules.is_empty());
}

#[test]
fn parses_verification_budget_overrides_through_hard_maxima() {
    let manifest = ProjectConfig::parse(
        Path::new("cott.toml"),
        &format!(
            "{VALID}\n[verification]\nproof_node_limit = {MAX_PROOF_NODE_LIMIT}\nproof_branch_limit = {MAX_PROOF_BRANCH_LIMIT}\ncandidate_limit = {MAX_CANDIDATE_LIMIT}\nlifecycle_limit = {MAX_LIFECYCLE_LIMIT}\n"
        ),
    )
    .expect("verification hard maxima should parse");
    assert_eq!(manifest.verification.proof_node_limit, MAX_PROOF_NODE_LIMIT);
    assert_eq!(
        manifest.verification.proof_branch_limit,
        MAX_PROOF_BRANCH_LIMIT
    );
    assert_eq!(manifest.verification.candidate_limit, MAX_CANDIDATE_LIMIT);
    assert_eq!(manifest.verification.lifecycle_limit, MAX_LIFECYCLE_LIMIT);
}

#[test]
fn rejects_invalid_verification_budgets() {
    for (field, zero, above_maximum) in [
        ("proof_node_limit", 0, MAX_PROOF_NODE_LIMIT + 1),
        ("proof_branch_limit", 0, MAX_PROOF_BRANCH_LIMIT + 1),
        ("candidate_limit", 0, MAX_CANDIDATE_LIMIT + 1),
        ("lifecycle_limit", 0, MAX_LIFECYCLE_LIMIT + 1),
    ] {
        for value in [zero, above_maximum] {
            let error = ProjectConfig::parse(
                Path::new("config/cott.toml"),
                &format!("{VALID}\n[verification]\n{field} = {value}\n"),
            )
            .expect_err("out-of-range verification budget must fail");
            assert_eq!(error.path, Path::new("config/cott.toml"));
            assert!(
                error.message.contains(&format!("verification.{field}")),
                "{}",
                error.message
            );
        }
    }
}

#[test]
fn parses_fixture_limits_through_hard_maxima() {
    let manifest = ProjectConfig::parse(
        Path::new("cott.toml"),
        &format!(
            "{VALID}\n[verification.fixtures]\nscenario_timeout_ms = {MAX_SCENARIO_TIMEOUT_MS}\nfilesystem_bytes = {MAX_FILESYSTEM_BYTES}\nfilesystem_files = {MAX_FILESYSTEM_FILES}\nhttp_body_bytes = {MAX_HTTP_BODY_BYTES}\nhttp_requests = {MAX_HTTP_REQUESTS}\nhttp_redirects = {MAX_HTTP_REDIRECTS}\ntranscript_events = {MAX_TRANSCRIPT_EVENTS}\n"
        ),
    )
    .expect("fixture hard maxima should parse");
    assert_eq!(
        manifest.verification.fixtures.scenario_timeout_ms,
        MAX_SCENARIO_TIMEOUT_MS
    );
    assert_eq!(
        manifest.verification.fixtures.filesystem_bytes,
        MAX_FILESYSTEM_BYTES
    );
    assert_eq!(
        manifest.verification.fixtures.filesystem_files,
        MAX_FILESYSTEM_FILES
    );
    assert_eq!(
        manifest.verification.fixtures.http_body_bytes,
        MAX_HTTP_BODY_BYTES
    );
    assert_eq!(
        manifest.verification.fixtures.http_requests,
        MAX_HTTP_REQUESTS
    );
    assert_eq!(
        manifest.verification.fixtures.http_redirects,
        MAX_HTTP_REDIRECTS
    );
    assert_eq!(
        manifest.verification.fixtures.transcript_events,
        MAX_TRANSCRIPT_EVENTS
    );
}

#[test]
fn rejects_invalid_fixture_limits() {
    for (field, maximum) in [
        ("scenario_timeout_ms", MAX_SCENARIO_TIMEOUT_MS as u64),
        ("filesystem_bytes", MAX_FILESYSTEM_BYTES),
        ("filesystem_files", MAX_FILESYSTEM_FILES as u64),
        ("http_body_bytes", MAX_HTTP_BODY_BYTES),
        ("http_requests", MAX_HTTP_REQUESTS as u64),
        ("http_redirects", MAX_HTTP_REDIRECTS as u64),
        ("transcript_events", MAX_TRANSCRIPT_EVENTS as u64),
    ] {
        for value in [0, maximum + 1] {
            let error = ProjectConfig::parse(
                Path::new("config/cott.toml"),
                &format!("{VALID}\n[verification.fixtures]\n{field} = {value}\n"),
            )
            .expect_err("out-of-range fixture ceiling must fail");
            assert_eq!(error.path, Path::new("config/cott.toml"));
            assert!(
                error
                    .message
                    .contains(&format!("verification.fixtures.{field}")),
                "{}",
                error.message
            );
        }
    }
}

#[test]
fn fixture_manifest_cannot_define_fixture_contents_or_hosts() {
    for field in [
        "root = \"fixtures\"",
        "path = \"/tmp/fixture\"",
        "endpoint = \"https://example.test\"",
        "command = \"python hook.py\"",
        "plugin = \"hook\"",
    ] {
        let error = ProjectConfig::parse(
            Path::new("cott.toml"),
            &format!("{VALID}\n[verification.fixtures]\n{field}\n"),
        )
        .expect_err("fixture contents and hosts must not be configurable");
        assert!(error.message.contains("unknown"), "{}", error.message);
    }
}

#[test]
fn parses_exact_coverage_selectors() {
    let manifest = ProjectConfig::parse(
        Path::new("cott.toml"),
        &format!(
            "{VALID}\n[[verification.coverage.rules]]\nsymbol = \"app.fetch\"\nclauses = [\"ensures:2\", \"error:5\", \"modifies:curriculum.trait_protocol.SimpleTask.completion_count\"]\nallow_unobserved = true\nallow_trust_declaration = true\nallow_unknown = false\n"
        ),
    )
    .expect("exact coverage selectors should parse");
    assert_eq!(manifest.verification.coverage.rules.len(), 1);
    assert_eq!(
        manifest.verification.coverage.rules[0].clauses,
        vec![
            "ensures:2".to_owned(),
            "error:5".to_owned(),
            "modifies:curriculum.trait_protocol.SimpleTask.completion_count".to_owned(),
        ]
    );
    assert!(manifest.verification.coverage.rules[0].allow_unobserved);
    assert!(manifest.verification.coverage.rules[0].allow_trust_declaration);
    assert!(!manifest.verification.coverage.rules[0].allow_unknown);
}

#[test]
fn rejects_invalid_or_duplicate_coverage_selectors() {
    for rule in [
        "symbol = \"app..fetch\"\nclauses = [\"ensures:2\"]",
        "symbol = \"app.fetch\"\nclauses = []",
        "symbol = \"app.fetch\"\nclauses = [\"EnsureS:2\"]",
        "symbol = \"app.fetch\"\nclauses = [\"ensures:02\"]",
        "symbol = \"app.fetch\"\nclauses = [\"modifies:curriculum..completion_count\"]",
        "symbol = \"app.fetch\"\nclauses = [\"error:5\", \"ensures:2\"]",
        "symbol = \"app.fetch\"\nclauses = [\"ensures:2\", \"ensures:2\"]",
        "symbol = \"app.fetch\"\nclauses = [\"ensures:2\"]\nallow_unknown = \"true\"",
    ] {
        ProjectConfig::parse(
            Path::new("cott.toml"),
            &format!("{VALID}\n[[verification.coverage.rules]]\n{rule}\n"),
        )
        .expect_err("invalid coverage rule must fail");
    }
    ProjectConfig::parse(
        Path::new("cott.toml"),
        &format!(
            "{VALID}\n[[verification.coverage.rules]]\nsymbol = \"app.fetch\"\nclauses = [\"ensures:2\"]\n\n[[verification.coverage.rules]]\nsymbol = \"app.fetch\"\nclauses = [\"ensures:2\"]\n"
        ),
    )
    .expect_err("duplicate coverage selections across rules must fail");
}

#[test]
fn keeps_coverage_tables_closed() {
    for rule in [
        "[verification.coverage]\nunknown = true",
        "[[verification.coverage.rules]]\nsymbol = \"app.fetch\"\nclauses = [\"ensures:2\"]\nallow_observed = true",
    ] {
        let error = ProjectConfig::parse(Path::new("cott.toml"), &format!("{VALID}\n{rule}\n"))
            .expect_err("coverage tables must reject unknown fields");
        assert!(error.message.contains("unknown"), "{}", error.message);
    }
}

#[test]
fn keeps_verification_table_closed() {
    let error = ProjectConfig::parse(
        Path::new("cott.toml"),
        &format!("{VALID}\n[verification]\nunknown = 1\n"),
    )
    .expect_err("unknown verification fields must fail");
    assert!(error.message.contains("unknown"), "{}", error.message);
}

#[test]
fn defaults_external_type_projections() {
    let manifest =
        ProjectConfig::parse(Path::new("cott.toml"), VALID).expect("manifest should parse");
    assert!(manifest.python.external_types.is_empty());
}

#[test]
fn parses_external_type_projections() {
    let manifest = ProjectConfig::parse(
        Path::new("cott.toml"),
        &format!(
            "{VALID}\n[target.python.external_types]\n\"vendor.auth.AccessToken\" = \"vendor_sdk.auth:AccessToken\"\n\"vendor.models.Result\" = \"vendor_sdk.models:Result.Value\"\n"
        ),
    )
    .expect("external type projections should parse");
    assert_eq!(
        manifest
            .python
            .external_types
            .get("vendor.auth.AccessToken"),
        Some(&"vendor_sdk.auth:AccessToken".to_owned())
    );
    assert_eq!(
        manifest.python.external_types.get("vendor.models.Result"),
        Some(&"vendor_sdk.models:Result.Value".to_owned())
    );
}

#[test]
fn keeps_python_target_table_closed() {
    let invalid = format!("{VALID}\nexternal_types = {{}}\nunknown = true\n");
    assert!(ProjectConfig::parse(Path::new("cott.toml"), &invalid).is_err());
}

#[test]
fn requires_quoted_external_type_symbols() {
    let error = ProjectConfig::parse(
        Path::new("config/cott.toml"),
        &format!(
            "{VALID}\n[target.python.external_types]\nvendor.auth.AccessToken = \"vendor_sdk.auth:AccessToken\"\n"
        ),
    )
    .expect_err("dotted external symbols must be quoted TOML keys");
    assert_eq!(error.path, Path::new("config/cott.toml"));
}

#[test]
fn rejects_malformed_external_type_projections() {
    for (symbol, target) in [
        ("Token", "vendor.auth:Token"),
        ("vendor.type.Token", "vendor.auth:Token"),
        ("vendor.auth.Token", ":Token"),
        ("vendor.auth.Token", "vendor.auth:"),
        ("vendor.auth.Token", "vendor.auth:Outer:Token"),
        ("vendor.auth.Token", "vendor.class:Token"),
        ("vendor.auth.Token", "_cott_vendor.auth:Token"),
        ("vendor.auth.Token", "vendor auth:Token"),
        ("vendor.auth.Token", "vendor\\n.auth:Token"),
        ("vendor.auth.Token", "vendor.auth:Token; import os"),
    ] {
        let error = ProjectConfig::parse(
            Path::new("config/cott.toml"),
            &format!("{VALID}\n[target.python.external_types]\n\"{symbol}\" = \"{target}\"\n"),
        )
        .expect_err("malformed external type projection must fail");
        assert_eq!(error.path, Path::new("config/cott.toml"));
        assert!(
            error.message.contains("invalid external type projection"),
            "{symbol} = {target}: {}",
            error.message
        );
    }
}

#[test]
fn rejects_unknown_manifest_fields() {
    let invalid = VALID.replace("source = \"src\"", "source = \"src\"\nentry = \"app.run\"");
    assert!(ProjectConfig::parse(Path::new("cott.toml"), &invalid).is_err());
}

#[test]
fn discriminates_one_closed_target_without_python_defaults() {
    assert_eq!(
        target_language(Path::new("cott.toml"), VALID).expect("Python target"),
        TargetLanguage::Python
    );
    assert_eq!(
        target_language(Path::new("cott.toml"), VALID_KOTLIN).expect("Kotlin target"),
        TargetLanguage::Kotlin
    );
    assert_eq!(
        target_language(Path::new("cott.toml"), VALID_DART).expect("Dart target"),
        TargetLanguage::Dart
    );

    let manifest = KotlinProjectConfig::parse(Path::new("cott.toml"), VALID_KOTLIN)
        .expect("Kotlin manifest should parse");
    assert_eq!(manifest.kotlin.classpath, ["libs/runtime.jar"]);
    assert_eq!(manifest.kotlin.compile_only, ["libs/android.jar"]);
    let dart = DartProjectConfig::parse(Path::new("cott.toml"), VALID_DART)
        .expect("Dart manifest should parse");
    assert_eq!(dart.dart.sdk, "dart");
    assert_eq!(dart.dart.runtime_validation, RuntimeValidation::Boundary);
    assert_eq!(
        dart.dart.implementations.get("demo.fetch"),
        Some(&"impl/fetch.dart:_fetch".to_owned())
    );
    assert_eq!(
        dart.dart.external_types.get("demo.Widget"),
        Some(&"package:flutter/widgets.dart#Widget".to_owned())
    );
    assert_eq!(
        dart.dart.external_types.get("demo.AsyncMemoizer"),
        Some(&"package:async/async.dart#AsyncMemoizer".to_owned())
    );
    assert!(dart.dart.pubspec.is_none());
    assert!(dart.dart.lockfile.is_none());
    ProjectConfig::parse(
        Path::new("cott.toml"),
        &VALID.replace("name = \"demo\"", "name = \"Demo\""),
    )
    .expect("Python manifest name behavior must remain unchanged");
    KotlinProjectConfig::parse(
        Path::new("cott.toml"),
        &VALID_KOTLIN.replace("demo.impl.fetch", "demo.when.fetch"),
    )
    .expect("raw Kotlin FQNs may contain identifiers that require source escaping");
    assert!(
        ProjectConfig::parse(Path::new("cott.toml"), VALID_KOTLIN).is_err(),
        "Python API must reject Kotlin"
    );
    assert!(
        KotlinProjectConfig::parse(Path::new("cott.toml"), VALID).is_err(),
        "Kotlin API must reject Python"
    );
    assert!(
        ProjectConfig::parse(Path::new("cott.toml"), VALID_DART).is_err(),
        "Python API must reject Dart"
    );
    assert!(
        KotlinProjectConfig::parse(Path::new("cott.toml"), VALID_DART).is_err(),
        "Kotlin API must reject Dart"
    );
    assert!(
        DartProjectConfig::parse(Path::new("cott.toml"), VALID).is_err(),
        "Dart API must reject Python"
    );
    assert!(
        DartProjectConfig::parse(Path::new("cott.toml"), VALID_KOTLIN).is_err(),
        "Dart API must reject Kotlin"
    );

    let mixed = format!(
        "{VALID}\n[target.kotlin]\nsource = \"kotlin-src\"\ngenerated = \"kotlin-out/kotlin\"\nruntime_validation = \"boundary\"\n"
    );
    assert!(
        target_language(Path::new("cott.toml"), &mixed).is_err(),
        "mixed targets must be rejected"
    );
    let triple = format!(
        "{mixed}\n[target.dart]\nsource = \"dart-src\"\ngenerated = \"generated/dart\"\nruntime_validation = \"boundary\"\n"
    );
    let error = target_language(Path::new("cott.toml"), &triple)
        .expect_err("three targets must be rejected");
    assert!(error.message.contains("exactly one"), "{}", error.message);
    assert!(
        target_language(
            Path::new("cott.toml"),
            &VALID_KOTLIN.replace("[target.kotlin]", "[target.unknown]"),
        )
        .is_err(),
        "unknown targets must be rejected by the closed target table"
    );
}

#[test]
fn validates_dart_metadata_paths_and_pairing() {
    let with_metadata = VALID_DART.replace(
        "runtime_validation = \"boundary\"",
        "runtime_validation = \"boundary\"\npubspec = \"dart-package/pubspec.yaml\"\nlockfile = \"dart-package/pubspec.lock\"",
    );
    let manifest = DartProjectConfig::parse(Path::new("cott.toml"), &with_metadata)
        .expect("paired Dart metadata should parse");
    assert_eq!(
        manifest.dart.pubspec.as_deref(),
        Some("dart-package/pubspec.yaml")
    );
    assert_eq!(
        manifest.dart.lockfile.as_deref(),
        Some("dart-package/pubspec.lock")
    );

    for invalid in [
        VALID_DART.replace(
            "runtime_validation = \"boundary\"",
            "runtime_validation = \"boundary\"\npubspec = \"dart-package/pubspec.yaml\"",
        ),
        VALID_DART.replace(
            "runtime_validation = \"boundary\"",
            "runtime_validation = \"boundary\"\nlockfile = \"dart-package/pubspec.lock\"",
        ),
        VALID_DART.replace(
            "runtime_validation = \"boundary\"",
            "runtime_validation = \"boundary\"\npubspec = \"src/pubspec.yaml\"\nlockfile = \"dart-package/pubspec.lock\"",
        ),
        VALID_DART.replace(
            "runtime_validation = \"boundary\"",
            "runtime_validation = \"boundary\"\npubspec = \"dart-package/pubspec.yaml\"\nlockfile = \"dart-package/pubspec.yaml\"",
        ),
        VALID_DART.replace(
            "runtime_validation = \"boundary\"",
            "runtime_validation = \"boundary\"\npubspec = \"dart-package/pubspec.yaml\"\nlockfile = \"dart-package/../pubspec.lock\"",
        ),
    ] {
        DartProjectConfig::parse(Path::new("cott.toml"), &invalid)
            .expect_err("unsafe or unpaired Dart metadata must fail");
    }
}

#[test]
fn rejects_malformed_dart_target_fields_and_bindings() {
    let invalid_names = [
        "DemoApp",
        "demo-app",
        "demo__app",
        "_demo_app",
        "demo_app_",
        "enum",
    ];
    for name in invalid_names {
        DartProjectConfig::parse(
            Path::new("cott.toml"),
            &VALID_DART.replace("name = \"demo_app\"", &format!("name = \"{name}\"")),
        )
        .expect_err("invalid Dart package name must fail");
    }

    for invalid in [
        VALID_DART.replace("generated/dart", "generated/package"),
        VALID_DART.replace("generated/dart", "build/dart"),
        VALID_DART.replace("source = \"dart-src\"", "source = \".dart_tool/impl\""),
        VALID_DART.replace("source = \"dart-src\"", "source = \"../dart-src\""),
        VALID_DART.replace("source = \"dart-src\"", "source = \"dart-src//impl\""),
        VALID_DART.replace("source = \"src\"", "source = \"src//contracts\""),
        VALID_DART.replace(
            "source = \"dart-src\"",
            "source = \"generated/implementations\"",
        ),
        VALID_DART.replace(
            "runtime_validation = \"boundary\"",
            "runtime_validation = \"boundary\"\nsdk = \"../dart\"",
        ),
        VALID_DART.replace(
            "runtime_validation = \"boundary\"",
            "runtime_validation = \"boundary\"\nsdk = \"/opt//dart\"",
        ),
        VALID_DART.replace("impl/fetch.dart:_fetch", "impl/fetch.txt:_fetch"),
        VALID_DART.replace("impl/fetch.dart:_fetch", "../fetch.dart:_fetch"),
        VALID_DART.replace("impl/fetch.dart:_fetch", "impl/fetch.dart:fetch"),
        VALID_DART.replace("impl/fetch.dart:_fetch", "impl/fetch.dart:_cott_fetch"),
        VALID_DART.replace("impl/fetch.dart:_fetch", "impl/fetch.dart:_fetch:other"),
        VALID_DART.replace("impl/fetch.dart:_fetch", ".dart_tool/fetch.dart:_fetch"),
        VALID_DART.replace(
            "runtime_validation = \"boundary\"",
            "runtime_validation = \"boundary\"\nunknown = true",
        ),
    ] {
        DartProjectConfig::parse(Path::new("cott.toml"), &invalid)
            .expect_err("malformed Dart target field or binding must fail");
    }
}

#[test]
fn rejects_malformed_dart_external_type_uris() {
    for target in [
        "https://example.test/types.dart#DateTime",
        "file:types.dart#DateTime",
        "dart:#DateTime",
        "dart:core#_Private",
        "dart:core#class",
        "dart:core#DateTime#Other",
        "package:flutter#Widget",
        "package:flutter/../widgets.dart#Widget",
        "package:flutter/widgets.txt#Widget",
        "package:flutter/widgets.dart?query#Widget",
    ] {
        let invalid = VALID_DART.replace("dart:core#DateTime", target);
        let error = DartProjectConfig::parse(Path::new("cott.toml"), &invalid)
            .expect_err("malformed Dart external type URI must fail");
        assert!(
            error
                .message
                .contains("invalid Dart external type projection"),
            "{target}: {}",
            error.message
        );
    }
    DartProjectConfig::parse(
        Path::new("cott.toml"),
        &VALID_DART.replace("\"demo.Instant\"", "\"Instant\""),
    )
    .expect_err("external Cott symbols must remain qualified");
}

#[test]
fn rejects_unsafe_or_ambiguous_kotlin_target_paths() {
    for invalid in [
        VALID_KOTLIN.replace("generated/kotlin", "generated/classes"),
        VALID_KOTLIN.replace("libs/runtime.jar", "../runtime.jar"),
        VALID_KOTLIN.replace("libs/runtime.jar", "libs/runtime.zip"),
        VALID_KOTLIN.replace("libs/android.jar", "libs/runtime.jar"),
        VALID_KOTLIN.replace("name = \"demo\"", "name = \"../escape\""),
        VALID_KOTLIN.replace("name = \"demo\"", "name = \"demo/name\""),
        VALID_KOTLIN.replace("name = \"demo\"", "name = \"Demo\""),
        VALID_KOTLIN.replace("name = \"demo\"", "name = \"demo--name\""),
        VALID_KOTLIN.replace("demo.impl.fetch", "demo.impl:fetch"),
        VALID_KOTLIN.replace("android.content.Context", "android.content:Context"),
        VALID_KOTLIN.replace(
            "runtime_validation = \"boundary\"",
            "runtime_validation = \"boundary\"\nunknown = true",
        ),
        VALID_KOTLIN.replace(
            "runtime_validation = \"boundary\"",
            "runtime_validation = \"boundary\"\njvm_target = 21",
        ),
    ] {
        KotlinProjectConfig::parse(Path::new("cott.toml"), &invalid)
            .expect_err("unsafe Kotlin target must fail");
    }
}

#[test]
fn parses_process_bar_normative_manifest_without_legacy_entry() {
    let path = Path::new("examples/complex/process-bar/cott.toml");
    let text = std::fs::read_to_string(path).expect("process-bar manifest should exist");
    assert!(
        !text
            .lines()
            .any(|line| line.trim_start().starts_with("entry =")),
        "process-bar manifest must not use the legacy entry key"
    );

    let manifest = ProjectConfig::parse(path, &text).expect("manifest should parse");
    assert_eq!(manifest.project.version, "0.1.0");
    assert_eq!(manifest.python.source, "python");
    assert_eq!(manifest.python.generated, "generated/python");
    assert_eq!(manifest.python.stubs, "generated/stubs");
    assert_eq!(
        manifest.python.runtime_validation,
        RuntimeValidation::Boundary
    );
    assert!(!text.contains("[target.python.implementations]"));
    assert!(manifest.python.implementations.is_empty());
    for implementation in [
        "build_output.py",
        "process_bar.py",
        "process_payload_bytes.py",
        "validate_payload.py",
    ] {
        assert!(
            !Path::new("examples/complex/process-bar/python/cott_bindings/foo/bar")
                .join(implementation)
                .exists(),
            "{implementation} must not be manifest-authored"
        );
        assert!(
            Path::new("examples/complex/process-bar/python/_cott_impl/foo/bar")
                .join(implementation)
                .is_file(),
            "{implementation} must be generated durably"
        );
    }
}
