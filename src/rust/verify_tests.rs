use super::*;
fn plan() -> RustPlan {
    let parsed=crate::compiler::parse_project([crate::compiler::SourceFile::new("demo/main.cott","module demo.main\n\nfn echo(value: I32) -> I32:\n    requires value >= 0\n    ensures result == value\n")]).unwrap();
    let hir = crate::hir::lower(Path::new("src"), parsed).unwrap();
    RustPlan::from_ir(&crate::ir::render(&hir).unwrap()).unwrap()
}
fn program() -> RunnerProgram {
    RunnerProgram {
        source: String::new(),
        file_name: "main.rs",
        expected_cases: BTreeMap::from([("demo.main.echo".into(), 1)]),
        expected_cancellations: BTreeSet::new(),
        expected_scenarios: BTreeMap::new(),
        unavailable: BTreeMap::new(),
        support: BTreeMap::new(),
        needs_loopback: false,
    }
}
fn observation(symbol: &str, clause: &str, passed: bool) -> Value {
    json!({"symbol":symbol,"clause":clause,"phase":clause.split(':').next().unwrap(),"status":if passed{"passed"}else{"failed"},"passed":passed,"reason":null,"applicable":true})
}
fn passed_case() -> Value {
    json!({"kind":"case","symbol":"demo.main.echo","case":0,"status":"passed","phase":null,"clause":null,"error_symbol":null,"observations":[observation("demo.main.echo","requires:0",true),observation("demo.main.echo","ensures:1",true)]})
}
fn strategies(plan: &RustPlan) -> Vec<ContractTestStrategy> {
    derive_strategies(&plan.ir, &crate::manifest::VerificationConfig::default()).unwrap()
}
#[test]
fn accepts_stable_toolchain_interval_and_rejects_mismatch_and_approximations() {
    for v in ["1.85.0", "1.96.0", "1.999.0"] {
        assert!(validate_versions(v, v).is_ok());
    }
    for (c, r) in [
        ("1.84.9", "1.84.9"),
        ("2.0.0", "2.0.0"),
        ("1.96.0", "1.95.0"),
        ("1.96.0-nightly", "1.96.0-nightly"),
        ("1.96.0+build", "1.96.0+build"),
        ("1.96", "1.96"),
    ] {
        assert!(validate_versions(c, r).is_err());
    }
}
#[test]
fn closed_inventory_rejects_unknown_duplicate_missing_and_out_of_range_cases() {
    let plan = plan();
    let strategies = strategies(&plan);
    let program = program();
    let case = passed_case();
    assert!(
        evidence::validate_events(
            &plan,
            &program,
            &strategies,
            &[case.clone(), json!({"kind":"done"})]
        )
        .is_ok()
    );
    for events in [
        vec![case.clone()],
        vec![json!({"kind":"done"}), case.clone()],
        vec![case.clone(), case.clone(), json!({"kind":"done"})],
        vec![json!({"kind":"done"})],
    ] {
        assert!(evidence::validate_events(&plan, &program, &strategies, &events).is_err());
    }
    for (field, value) in [
        ("case", json!(1)),
        ("symbol", json!("demo.main.unknown")),
        ("extra", json!(true)),
    ] {
        let mut invalid = case.clone();
        invalid[field] = value;
        assert!(
            evidence::validate_events(
                &plan,
                &program,
                &strategies,
                &[invalid, json!({"kind":"done"})]
            )
            .is_err()
        );
    }
}
#[test]
fn passed_status_requires_consistent_known_runtime_observations() {
    let plan = plan();
    let strategies = strategies(&plan);
    for invalid_observation in [
        observation("demo.main.echo", "requires:0", false),
        observation("demo.main.forged", "requires:0", true),
        observation("demo.main.echo", "ensures:999", true),
    ] {
        let mut case = passed_case();
        case["observations"] = json!([invalid_observation]);
        assert!(
            evidence::validate_events(
                &plan,
                &program(),
                &strategies,
                &[case, json!({"kind":"done"})]
            )
            .is_err()
        );
    }
}
#[test]
fn ineligible_status_requires_actual_failed_requires_observation() {
    let plan = plan();
    let strategies = strategies(&plan);
    let mut case = passed_case();
    case["status"] = json!("ineligible");
    case["phase"] = json!("requires");
    case["clause"] = json!("requires:0");
    case["error_symbol"] = json!("demo.main.echo");
    assert!(
        evidence::validate_events(
            &plan,
            &program(),
            &strategies,
            &[case.clone(), json!({"kind":"done"})]
        )
        .is_err()
    );
    case["observations"] = json!([observation("demo.main.echo", "requires:0", false)]);
    assert!(
        evidence::validate_events(
            &plan,
            &program(),
            &strategies,
            &[case, json!({"kind":"done"})]
        )
        .is_ok()
    );
}
#[test]
fn coverage_does_not_bless_unobserved_or_rejected_invocations() {
    let plan = plan();
    let strategies = strategies(&plan);
    let mut case = passed_case();
    case["observations"] = json!([observation("demo.main.echo", "requires:0", true)]);
    assert!(
        evidence::contract_report(
            &plan,
            &strategies,
            &program(),
            &[case, json!({"kind":"done"})]
        )
        .is_err()
    );
}

#[test]
#[ignore = "requires COTT_CARGO and the real native sandbox"]
fn native_toolchain_probe_records_consistent_release_commit_host_and_bytes() {
    let cargo = PathBuf::from(std::env::var_os("COTT_CARGO").expect("COTT_CARGO"));
    assert!(cargo.is_absolute());
    let rustc = std::env::var_os("COTT_RUSTC")
        .map(PathBuf::from)
        .unwrap_or_else(|| cargo.parent().unwrap().join("rustc"));
    let root = scratch_directory().unwrap();
    fs::create_dir(root.join("src")).unwrap();
    fs::create_dir(root.join("rust")).unwrap();
    fs::write(root.join("cott.toml"),format!("[project]\nname='probe'\nversion='0.1.0'\nsource='src'\n[target.rust]\nsource='rust'\ngenerated='generated/rust'\nruntime_validation='boundary'\ncargo={:?}\nrustc={:?}\n",cargo.to_string_lossy(),rustc.to_string_lossy())).unwrap();
    let (config, paths, _) = crate::project::load_rust_config_with_paths(&root).unwrap();
    let result = probe(&config, &paths);
    let tools = finish_scratch(root, result).unwrap();
    let cargo = text_field(&tools["cargo"], "release");
    let rustc = text_field(&tools["rustc"], "release");
    assert_eq!(cargo, rustc);
    validate_versions(cargo, rustc).unwrap();
}
fn text_field<'a>(value: &'a Value, key: &str) -> &'a str {
    value[key].as_str().unwrap()
}

#[test]
fn compiler_output_hardlinks_freeze_without_weakening_authored_input_checks() {
    let root = scratch_directory().unwrap();
    let target = root.join("target");
    fs::create_dir(&target).unwrap();
    let output = target.join("runner");
    fs::write(&output, b"compiler-created original").unwrap();
    fs::set_permissions(&output, fs::Permissions::from_mode(0o700)).unwrap();
    fs::hard_link(&output, target.join("runner-deps")).unwrap();
    assert!(read_regular(&output, "authored input").is_err());
    let frozen = freeze_compiler_output(&output, &target.join("frozen"), &root, true).unwrap();
    assert_eq!(fs::metadata(&frozen).unwrap().nlink(), 1);
    fs::write(&output, b"changed original output").unwrap();
    assert_eq!(
        read_regular(&frozen, "frozen execution").unwrap(),
        b"compiler-created original"
    );
    std::os::unix::fs::symlink(&frozen, target.join("symlink")).unwrap();
    assert!(
        freeze_compiler_output(
            &target.join("symlink"),
            &target.join("rejected"),
            &root,
            true
        )
        .is_err()
    );
    finish_scratch(root, Ok(())).unwrap();
}
