use serde_json::{Value, json};

const TRACEABILITY: &[(u8, &[&str])] = &[
    (
        1,
        &["cli::process_bar_generation_records_unresolved_and_verified_transitions"],
    ),
    (
        2,
        &[
            "semantic::rejects_module_path_mismatch",
            "python_emit::rejects_colliding_public_python_symbol_projection",
        ],
    ),
    (
        3,
        &[
            "compiler::aggregates_syntax_diagnostics_with_their_source_paths",
            "diagnostics::report_is_one_json_object_with_source_locations",
        ],
    ),
    (
        4,
        &[
            "ir::checked_in_canonical_ir_schema_is_parseable",
            "hir::direct_lowering_preserves_parsed_owned_structure_and_contracts",
            "architecture_acceptance::wire_identities_are_closed_and_cross_shape_records_are_rejected",
        ],
    ),
    (
        5,
        &["semantic::preserves_cross_module_clause_variant_identity"],
    ),
    (
        6,
        &[
            "python_emit::imports_cross_module_contract_constants",
            "python_emit::emits_complete_deterministic_python_artifact_tree",
        ],
    ),
    (
        7,
        &[
            "python_emit::emits_complete_deterministic_python_artifact_tree",
            "cli::emits_complete_tree_and_verifies_exact_bytes",
        ],
    ),
    (
        8,
        &["python_runtime::generated_runtime_exercises_abi_and_provenance_loader"],
    ),
    (
        9,
        &["python_runtime::generated_runtime_exercises_abi_and_provenance_loader"],
    ),
    (
        10,
        &[
            "python_runtime::generated_runtime_exercises_abi_and_provenance_loader",
            "cli::generated_facades_enforce_contextual_and_exit_contracts",
        ],
    ),
    (
        11,
        &[
            "python_emit::emits_single_and_multiple_generic_trait_bounds",
            "python_emit::disambiguates_same_generic_name_with_different_bounds",
            "semantic::accepts_v02_const_generics_variadic_tuples_and_fixed_containers",
            "semantic::rejects_v02_const_generic_argument_and_fixed_container_errors",
            "semantic::accepts_v03_associated_type_assignment_and_projection_substitution",
            "semantic::rejects_v03_associated_type_duplicates_unknown_ambiguous_and_cyclic_uses",
        ],
    ),
    (
        12,
        &[
            "python_runtime::generated_runtime_exercises_abi_and_provenance_loader",
            "cli::generated_facades_enforce_contextual_and_exit_contracts",
            "semantic::accepts_v02_generalized_match_guards_and_clause_local_bindings",
            "semantic::rejects_v02_match_guard_bindings_outside_their_clause",
        ],
    ),
    (
        13,
        &["cli::generated_facades_enforce_contextual_and_exit_contracts"],
    ),
    (
        14,
        &[
            "hir::lowers_impl_state_contracts_and_old_state_fields",
            "hir::rejects_invalid_impl_state_init_and_trait_method_coverage",
            "semantic::accepts_v02_trait_default_references_and_rejects_invalid_targets",
            "semantic::accepts_v03_resource_graph_and_multiple_resource_field_transitions",
            "semantic::rejects_v03_invalid_resource_graphs_and_transitions",
        ],
    ),
    (
        15,
        &["cli::generated_facades_enforce_contextual_and_exit_contracts"],
    ),
    (
        16,
        &[
            "contract_test::derived_strategy_bytes_are_deterministic_in_module_declaration_order",
            "contract_test::derived_strategy_clause_ids_preserve_source_order",
        ],
    ),
    (
        17,
        &[
            "contract_test::derived_strategy_classifies_pure_effectful_and_never",
            "sandbox::contract_test_limits_are_fixed",
        ],
    ),
    (
        18,
        &[
            "binding::candidate_validation_public_api_uses_only_the_canonical_plan",
            "binding::validates_parameter_names_and_kinds_against_canonical_ir",
        ],
    ),
    (
        19,
        &["hir::rejects_invalid_impl_state_init_and_trait_method_coverage"],
    ),
    (
        20,
        &["binding::accepts_only_import_roots_selected_in_uv_lock"],
    ),
    (
        21,
        &["python_runtime::generated_runtime_exercises_abi_and_provenance_loader"],
    ),
    (
        22,
        &[
            "binding::validates_parameter_names_and_kinds_against_canonical_ir",
            "python_runtime::generated_runtime_exercises_abi_and_provenance_loader",
        ],
    ),
    (
        23,
        &[
            "agent_runner::codex_golden_argv_stdin_environment_and_target_write",
            "agent_runner::omp_golden_argv_prompt_environment_and_target_write",
        ],
    ),
    (
        24,
        &[
            "cli::process_bar_generation_records_unresolved_and_verified_transitions",
            "agent_runner::preexisting_hardlink_target_is_rejected",
            "agent_runner::preexisting_symlink_target_is_rejected",
        ],
    ),
    (
        25,
        &["cli::process_bar_generation_records_unresolved_and_verified_transitions"],
    ),
    (
        26,
        &[
            "binding::reports_unresolved_canonical_planned_function",
            "cli::process_bar_generation_records_unresolved_and_verified_transitions",
        ],
    ),
    (
        27,
        &["cli::process_bar_generation_records_unresolved_and_verified_transitions"],
    ),
    (
        28,
        &[
            "cli::process_bar_generation_records_unresolved_and_verified_transitions",
            "binding::reports_unreferenced_durable_implementations_as_stale",
        ],
    ),
    (
        29,
        &[
            "cli::emits_complete_tree_and_verifies_exact_bytes",
            "cli::process_bar_generation_records_unresolved_and_verified_transitions",
        ],
    ),
    (
        30,
        &[
            "binding::reports_unreferenced_durable_implementations_as_stale",
            "cli::process_bar_generation_records_unresolved_and_verified_transitions",
        ],
    ),
    (
        31,
        &[
            "transaction::tests::every_apply_fault_recovers_to_one_complete_snapshot",
            "transaction::tests::interrupted_rollback_is_idempotent",
        ],
    ),
    (
        32,
        &[
            "command::rejects_duplicate_or_invalid_options",
            "cli::json_mode_returns_one_closed_diagnostic_document_with_source_spans",
        ],
    ),
    (
        33,
        &[
            "cli::process_bar_generation_records_unresolved_and_verified_transitions",
            "examples::every_documented_example_runs_when_python3_is_available",
        ],
    ),
    (
        34,
        &[
            "formatter::lossless_formatter_normalizes_newlines_idempotently",
            "formatter::canonicalizes_spacing_indentation_lists_and_comments",
            "formatter::wraps_legal_comma_lists_at_one_hundred_columns",
            "formatter::formats_v02_const_generics_match_guards_and_trait_defaults",
            "formatter::formats_v03_async_associated_types_and_resource_transitions",
        ],
    ),
    (
        35,
        &[
            "diagnostics::report_is_one_json_object_with_source_locations",
            "cli::json_mode_returns_one_closed_diagnostic_document_with_source_spans",
        ],
    ),
    (
        36,
        &[
            "cli::init_scaffolds_a_normative_project_with_pinned_uv",
            "cli::tests::scaffold_file_and_directory_fsync_faults_leave_no_target",
            "cli::tests::no_replace_publish_fault_and_collision_preserve_foreign_target",
            "cli::tests::publish_parent_fsync_fault_leaves_owned_incomplete_target_then_cleans",
            "cli::tests::temp_cleanup_remove_and_parent_fsync_are_retryable",
            "cli::tests::target_cleanup_remove_and_parent_fsync_are_ownership_checked_and_retryable",
            "cli::tests::final_commit_faults_preserve_exact_ownership_states_and_resume",
        ],
    ),
    (
        37,
        &[
            "ir::checked_in_canonical_ir_schema_is_parseable",
            "cli::emits_complete_tree_and_verifies_exact_bytes",
            "python_runtime::generated_runtime_exercises_abi_and_provenance_loader",
        ],
    ),
    (
        38,
        &[
            "binding::async_impl_methods_are_agent_only_and_require_exact_async_helpers",
            "python_emit::emits_async_impl_methods_with_reentrant_lock_and_finalization",
        ],
    ),
    (
        39,
        &[
            "contract_test::contract_runner_observes_and_closes_pure_async_protocols",
            "contract_test::contract_runner_awaits_async_functions_and_detects_task_leaks",
        ],
    ),
    (
        40,
        &[
            "semantic::lowers_v05_order_independent_inheritance_and_coalesced_diamonds",
            "semantic::lowers_v05_specializations_below_explicit_implementations",
            "semantic::lowers_v05_valid_variance_and_rejects_invalid_polarity",
            "python_runtime::generated_runtime_validates_generic_dyn_exactly",
        ],
    ),
    (
        41,
        &[
            "semantic::accepts_v06_guarded_self_mutual_generic_and_enum_recursion",
            "contract_test::contract_runner_constructs_terminating_recursive_enum_candidates_stably",
            "python_runtime::generated_runtime_exercises_abi_and_provenance_loader",
            "cli::verify_records_no_baseline_implementation_comparison",
            "cli::verify_rejects_disproved_static_requires_without_mutating_generation_record",
            "cli::verify_records_unsupported_static_requires_as_nonfatal_unknown",
        ],
    ),
    (
        42,
        &[
            "python_runtime::generated_runtime_imports_async_protocol_support",
            "contract_test::contract_runner_observes_and_closes_pure_async_protocols",
        ],
    ),
    (
        43,
        &[
            "manifest::defaults_verification_budgets",
            "manifest::parses_verification_budget_overrides_through_hard_maxima",
            "manifest::rejects_invalid_verification_budgets",
            "contract_test::derived_strategy_serializes_verification_limits",
        ],
    ),
    (
        44,
        &[
            "proof::tests::supports_u64_lower_middle_and_upper_bounds",
            "proof::tests::names_recursive_fields_and_lengths",
            "proof::tests::honors_exact_configured_node_and_branch_limits",
        ],
    ),
    (
        45,
        &[
            "cli::verify_records_no_baseline_implementation_comparison",
            "cli::emit_rejects_stale_generation_compatibility_without_mutating_managed_tree",
            "python_runtime::generated_runtime_exercises_abi_and_provenance_loader",
            "architecture_acceptance::wire_identities_are_closed_and_cross_shape_records_are_rejected",
        ],
    ),
];

#[test]
fn all_45_architecture_acceptance_criteria_map_to_named_assertions() {
    assert_eq!(TRACEABILITY.len(), 45);
    for (index, (criterion, assertions)) in TRACEABILITY.iter().enumerate() {
        assert_eq!(*criterion as usize, index + 1);
        assert!(!assertions.is_empty());
        assert!(assertions.iter().all(|name| name.contains("::")));
    }
}

#[test]
fn wire_identities_are_closed_and_cross_shape_records_are_rejected() {
    let generation_schema: Value =
        serde_json::from_str(include_str!("../schemas/generation.schema.json"))
            .expect("generation schema");
    let strategy_schema: Value =
        serde_json::from_str(include_str!("../schemas/contract-test.schema.json"))
            .expect("strategy schema");
    assert_eq!(
        generation_schema["$id"],
        "https://cott.dev/schema/generation/v7"
    );
    assert_eq!(generation_schema["title"], "cott generation record v7");
    assert_eq!(
        generation_schema["properties"]["schema_version"]["const"],
        7
    );
    assert_eq!(
        generation_schema["$defs"]["compatibility"]["required"],
        json!([
            "generation_schema",
            "canonical_ir_schema",
            "runtime_abi",
            "contract_strategy_schema"
        ])
    );
    assert_eq!(
        strategy_schema["$id"],
        "https://cott.dev/schema/contract-test/v5"
    );
    assert_eq!(strategy_schema["title"], "cott contract test strategy v5");
    assert_eq!(strategy_schema["properties"]["schema_version"]["const"], 5);

    let generation = json!({
        "schema_version": 7,
        "current": generation_snapshot(),
        "last_verified": null,
    });
    let generation_validator =
        jsonschema::validator_for(&generation_schema).expect("generation validator");
    assert!(generation_validator.is_valid(&generation));
    let mut legacy_generation = generation.clone();
    legacy_generation["current"]["compatibility"] = json!({
        "generation_schema": 6,
        "canonical_ir_schema": 7,
        "runtime_abi": 6,
    });
    assert!(!generation_validator.is_valid(&legacy_generation));

    let strategy = json!({
        "schema_version": 5,
        "symbol": "app.check",
        "seed": format!("sha256:{}", "0".repeat(64)),
        "proof_node_limit": 1,
        "proof_branch_limit": 1,
        "candidate_limit": 1,
        "node_limit": 64,
        "container_length_limit": 3,
        "json_depth_limit": 4,
        "lifecycle_limit": 1,
        "callable_kind": "sync",
        "return_kind": "value",
        "classification": "pure",
        "clause_ids": [],
        "obligations": [],
        "scenario": {
            "id": "scenario",
            "required_effects": [],
            "fixtures": [],
            "steps": [],
            "lifecycle_limit": 1,
            "limits": {
                "scenario_timeout_ms": 1,
                "filesystem_bytes": 1,
                "filesystem_files": 1,
                "http_body_bytes": 1,
                "http_requests": 1,
                "http_redirects": 1,
                "transcript_events": 1,
            },
        },
    });
    let strategy_validator =
        jsonschema::validator_for(&strategy_schema).expect("strategy validator");
    assert!(strategy_validator.is_valid(&strategy));
    let mut legacy_strategy = strategy.clone();
    legacy_strategy["schema_version"] = json!(4);
    assert!(!strategy_validator.is_valid(&legacy_strategy));
    let mut incomplete_strategy = strategy.clone();
    incomplete_strategy
        .as_object_mut()
        .expect("strategy object")
        .remove("obligations");
    assert!(!strategy_validator.is_valid(&incomplete_strategy));
    let mut fixtureless_strategy = strategy;
    fixtureless_strategy["scenario"]
        .as_object_mut()
        .expect("scenario object")
        .remove("fixtures");
    assert!(!strategy_validator.is_valid(&fixtureless_strategy));
}

fn generation_snapshot() -> Value {
    json!({
        "generation_id": format!("sha256:{}", "0".repeat(64)),
        "verified": false,
        "project_version": "0.1.0",
        "compatibility": {
            "generation_schema": 7,
            "canonical_ir_schema": 8,
            "runtime_abi": 7,
            "contract_strategy_schema": 5,
        },
        "inputs": {},
        "tools": {},
        "ir": {},
        "contract_surface": {},
        "public_python_symbols": {},
        "implementations": [],
        "dependencies": [],
        "managed_files": {},
        "unresolved": [],
        "verification": null,
        "semantic_coverage": {
            "clauses": [],
            "summary": {
                "observed": 0,
                "unobserved": 0,
                "trust_declaration": 0,
                "unknown": 0,
            },
            "policy": {
                "selected": 0,
                "passed": true,
                "violations": [],
            },
        },
        "agent_runs": [],
    })
}
