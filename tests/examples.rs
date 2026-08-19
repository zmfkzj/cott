use std::collections::BTreeSet;
use std::fs;
use std::io;
use std::path::{Path, PathBuf};
use std::process::{Command, Output};
use std::sync::atomic::{AtomicU64, Ordering};

static NEXT_TEMP_DIR: AtomicU64 = AtomicU64::new(0);

struct Example {
    path: &'static str,
    module: &'static str,
    public_functions: &'static [&'static str],
    final_symbol: &'static str,
}

const EXAMPLES: &[Example] = &[
    Example {
        path: "grammar/portfolio-cost",
        module: "curriculum.portfolio_cost",
        public_functions: &["calculate_portfolio_cost"],
        final_symbol: "calculate_portfolio_cost",
    },
    Example {
        path: "grammar/cta-row",
        module: "curriculum.cta_row",
        public_functions: &["decode_row"],
        final_symbol: "decode_row",
    },
    Example {
        path: "grammar/validated-stock",
        module: "curriculum.validated_stock",
        public_functions: &["value_stock"],
        final_symbol: "value_stock",
    },
    Example {
        path: "grammar/stock-input-validation",
        module: "curriculum.stock_input_validation",
        public_functions: &["validate_stock_input"],
        final_symbol: "validate_stock_input",
    },
    Example {
        path: "grammar/parse-assignment",
        module: "curriculum.parse_assignment",
        public_functions: &["parse_assignment"],
        final_symbol: "parse_assignment",
    },
    Example {
        path: "grammar/stock-record",
        module: "curriculum.stock_record",
        public_functions: &["value_record", "value_stock_record"],
        final_symbol: "value_stock_record",
    },
    Example {
        path: "grammar/checked-add",
        module: "curriculum.checked_add",
        public_functions: &["checked_add"],
        final_symbol: "checked_add",
    },
    Example {
        path: "grammar/fractional-range-values",
        module: "curriculum.fractional_range_values",
        public_functions: &["build_bounded_range"],
        final_symbol: "build_bounded_range",
    },
    Example {
        path: "grammar/module-export-snapshot",
        module: "curriculum.module_export_snapshot",
        public_functions: &["build_snapshot"],
        final_symbol: "build_snapshot",
    },
    Example {
        path: "grammar/assignment-rule",
        module: "curriculum.assignment_rule",
        public_functions: &["parse_assignment"],
        final_symbol: "parse_assignment",
    },
    Example {
        path: "simple/calculate-age",
        module: "curriculum.calculate_age",
        public_functions: &["calculate_age_days", "summarize_age"],
        final_symbol: "summarize_age",
    },
    Example {
        path: "simple/calculator",
        module: "curriculum.calculator",
        public_functions: &["validate_calculation", "calculate"],
        final_symbol: "calculate",
    },
    Example {
        path: "simple/decimal-binary",
        module: "curriculum.decimal_binary",
        public_functions: &[
            "decimal_to_binary",
            "binary_to_decimal",
            "convert_binary_decimal",
        ],
        final_symbol: "convert_binary_decimal",
    },
    Example {
        path: "simple/textfile-analysis",
        module: "curriculum.textfile_analysis",
        public_functions: &["extract_casefolded_words", "analyze_text"],
        final_symbol: "analyze_text",
    },
    Example {
        path: "simple/compute-iou",
        module: "curriculum.compute_iou",
        public_functions: &["calculate_intersection_union", "compute_iou"],
        final_symbol: "compute_iou",
    },
    Example {
        path: "simple/numbers-to-words",
        module: "curriculum.numbers_to_words",
        public_functions: &["spell_under_thousand", "spell_cardinal"],
        final_symbol: "spell_cardinal",
    },
    Example {
        path: "simple/rock-paper-scissors",
        module: "curriculum.rock_paper_scissors",
        public_functions: &["user_beats_computer", "decide_round"],
        final_symbol: "decide_round",
    },
    Example {
        path: "simple/tic-tac-toe",
        module: "curriculum.tic_tac_toe",
        public_functions: &["validate_board_state", "apply_tic_tac_toe_move"],
        final_symbol: "apply_tic_tac_toe_move",
    },
    Example {
        path: "simple/random-password-generator",
        module: "curriculum.random_password",
        public_functions: &["required_password_draws", "generate_password"],
        final_symbol: "generate_password",
    },
    Example {
        path: "simple/unique-words",
        module: "curriculum.unique_words",
        public_functions: &["normalize_words", "find_unique_words"],
        final_symbol: "find_unique_words",
    },
    Example {
        path: "simple/split-file",
        module: "curriculum.split_file",
        public_functions: &["validate_split_request", "split_lines"],
        final_symbol: "split_lines",
    },
    Example {
        path: "simple/currency-converter",
        module: "curriculum.currency_converter",
        public_functions: &["validate_conversion_request", "convert_currency"],
        final_symbol: "convert_currency",
    },
    Example {
        path: "simple/json-to-csv",
        module: "curriculum.json_to_csv",
        public_functions: &["escape_csv_field", "serialize_csv"],
        final_symbol: "serialize_csv",
    },
    Example {
        path: "simple/alphabetical-file-groups",
        module: "curriculum.alphabetical_file_groups",
        public_functions: &["classify_filename", "group_filenames"],
        final_symbol: "group_filenames",
    },
    Example {
        path: "simple/billing-system",
        module: "curriculum.billing_system",
        public_functions: &["validate_bill_lines", "calculate_bill"],
        final_symbol: "calculate_bill",
    },
    Example {
        path: "simple/website-connectivity",
        module: "curriculum.website_connectivity",
        public_functions: &["classify_observation", "classify_websites"],
        final_symbol: "classify_websites",
    },
    Example {
        path: "complex/archive-request",
        module: "curriculum.archive_request",
        public_functions: &[
            "canonicalize_archive_url",
            "compose_archive_plan",
            "plan_archive",
        ],
        final_symbol: "plan_archive",
    },
    Example {
        path: "complex/track-metadata",
        module: "curriculum.track_metadata",
        public_functions: &[
            "trim_track_draft",
            "format_track_metadata",
            "normalize_track_metadata",
        ],
        final_symbol: "normalize_track_metadata",
    },
    Example {
        path: "complex/clip-ranges",
        module: "curriculum.clip_ranges",
        public_functions: &["range_duration_ms", "plan_clip_ranges"],
        final_symbol: "plan_clip_ranges",
    },
    Example {
        path: "complex/experiment-ranking",
        module: "curriculum.experiment_ranking",
        public_functions: &["order_run_ids", "rank_experiments"],
        final_symbol: "rank_experiments",
    },
    Example {
        path: "complex/color-quantization",
        module: "curriculum.color_quantization",
        public_functions: &["rank_palette_colors", "quantize_colors"],
        final_symbol: "quantize_colors",
    },
    Example {
        path: "complex/move-2048",
        module: "curriculum.move_2048",
        public_functions: &["validate_2048_board", "merge_move_line", "apply_2048_move"],
        final_symbol: "apply_2048_move",
    },
    Example {
        path: "complex/backup-plan",
        module: "curriculum.backup_plan",
        public_functions: &[
            "validate_backup_request",
            "classify_backup_paths",
            "plan_backup",
        ],
        final_symbol: "plan_backup",
    },
    Example {
        path: "complex/expense-split",
        module: "curriculum.expense_split",
        public_functions: &["calculate_balances", "settle_balances", "settle_expense"],
        final_symbol: "settle_expense",
    },
    Example {
        path: "complex/reputation",
        module: "curriculum.reputation",
        public_functions: &["reputation_delta", "calculate_reputation"],
        final_symbol: "calculate_reputation",
    },
    Example {
        path: "complex/flashcard-schedule",
        module: "curriculum.flashcard_schedule",
        public_functions: &["validate_review_ease", "schedule_review"],
        final_symbol: "schedule_review",
    },
    Example {
        path: "complex/roast-analysis",
        module: "curriculum.roast_analysis",
        public_functions: &[
            "validate_roast_profile",
            "summarize_roast_samples",
            "analyze_roast_profile",
        ],
        final_symbol: "analyze_roast_profile",
    },
    Example {
        path: "complex/publication-workflow",
        module: "curriculum.publication_workflow",
        public_functions: &["transition_target", "transition_publication"],
        final_symbol: "transition_publication",
    },
    Example {
        path: "complex/inventory-reorder",
        module: "curriculum.inventory_reorder",
        public_functions: &["available_stock", "plan_reorder"],
        final_symbol: "plan_reorder",
    },
    Example {
        path: "complex/page-build",
        module: "curriculum.page_build",
        public_functions: &["escape_page_text", "render_page_html", "build_page"],
        final_symbol: "build_page",
    },
    Example {
        path: "complex/artifact-pipeline",
        module: "curriculum.artifact_pipeline",
        public_functions: &["topologically_order_steps", "plan_pipeline"],
        final_symbol: "plan_pipeline",
    },
    Example {
        path: "complex/case-ranking",
        module: "curriculum.case_ranking",
        public_functions: &["score_case_overlap", "order_matching_cases", "rank_cases"],
        final_symbol: "rank_cases",
    },
];

struct TempDir {
    path: PathBuf,
}

impl TempDir {
    fn new() -> Self {
        let mut number = NEXT_TEMP_DIR.fetch_add(1, Ordering::Relaxed);
        loop {
            let path = std::env::temp_dir().join(format!(
                "cott-example-tests-{}-{number}",
                std::process::id()
            ));
            match fs::create_dir(&path) {
                Ok(()) => return Self { path },
                Err(error) if error.kind() == io::ErrorKind::AlreadyExists => number += 1,
                Err(error) => panic!("failed to create temporary directory: {error}"),
            }
        }
    }
}

impl Drop for TempDir {
    fn drop(&mut self) {
        let _ = fs::remove_dir_all(&self.path);
    }
}

fn copied_project(example: &str) -> TempDir {
    let temp = TempDir::new();
    let source = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("examples")
        .join(example);
    copy_tree(&source, &temp.path);
    install_fake_python_tools(&temp.path);
    temp
}

fn install_fake_python_tools(root: &Path) {
    let bin = root.join(".venv/bin");
    fs::create_dir_all(&bin).expect("fake Python tool directory");
    let python = bin.join("python");
    fs::write(
        &python,
        r#"#!/bin/sh
if [ "$1" = "-c" ]; then
  case "$2" in
    *"sysconfig; print(json.dumps"*)
      printf '%s\n' '{"cache_tag":"cpython-314","implementation":"cpython","machine":"x86_64","os":"linux","platform":"linux-x86_64","version":"3.14.6"}'
      exit 0
      ;;
  esac
fi
exec /usr/bin/python3 "$@"
"#,
    )
    .expect("fake Python interpreter");
    let checker = bin.join("basedpyright");
    fs::write(
        &checker,
        "#!/bin/sh\n[ \"$1\" = \"--version\" ] && printf 'basedpyright 1.39.9\\nbased on pyright 1.1.411\\n'\nexit 0\n",
    )
    .expect("fake BasedPyright");
    #[cfg(unix)]
    {
        use std::os::unix::fs::PermissionsExt;
        for executable in [python, checker] {
            fs::set_permissions(executable, fs::Permissions::from_mode(0o755))
                .expect("make fake Python tool executable");
        }
    }
}

fn copy_tree(source: &Path, destination: &Path) {
    fs::create_dir_all(destination).expect("destination should be creatable");
    let entries = fs::read_dir(source).expect("example directory should be readable");
    for entry in entries {
        let entry = entry.expect("example directory entry should be readable");
        let source_path = entry.path();
        let destination_path = destination.join(entry.file_name());
        let metadata =
            fs::symlink_metadata(&source_path).expect("example metadata should be readable");
        if metadata.is_dir() {
            copy_tree(&source_path, &destination_path);
        } else if metadata.is_file() {
            fs::copy(&source_path, &destination_path).expect("example file should be copyable");
        } else {
            panic!(
                "example contains unsupported filesystem entry: {}",
                source_path.display()
            );
        }
    }
}

fn authored_files_below(root: &Path) -> Vec<PathBuf> {
    if !root.exists() {
        return Vec::new();
    }
    let mut files = Vec::new();
    for entry in fs::read_dir(root).expect("authored source directory should be readable") {
        let entry = entry.expect("authored source entry should be readable");
        let path = entry.path();
        if entry
            .file_type()
            .expect("authored source entry type should be readable")
            .is_dir()
        {
            files.extend(authored_files_below(&path));
        } else {
            files.push(path);
        }
    }
    files.sort();
    files
}

fn cott(root: &Path, arguments: &[&str]) -> Output {
    Command::new(env!("CARGO_BIN_EXE_cott"))
        .args(arguments)
        .arg("--project")
        .arg(root)
        .output()
        .expect("cott should run")
}

fn generated_module_file(root: &Path, directory: &str, module: &str, suffix: &str) -> PathBuf {
    let mut path = root.join("generated").join(directory);
    let mut segments = module.split('.').collect::<Vec<_>>();
    let name = segments.pop().expect("example module must have a name");
    path.extend(segments);
    path.join(format!("{name}{suffix}"))
}

fn python_all(path: &Path) -> Vec<String> {
    let source = fs::read_to_string(path).expect("generated Python module should be readable");
    let projection = source
        .lines()
        .find_map(|line| line.strip_prefix("__all__ = "))
        .expect("generated Python module should declare __all__");
    serde_json::from_str(projection).expect("generated __all__ should be a JSON string array")
}

fn assert_public_projection(root: &Path, example: &Example, implementations_generated: bool) {
    let ir_path = generated_module_file(root, "ir", example.module, ".json");
    let ir: serde_json::Value =
        serde_json::from_slice(&fs::read(ir_path).expect("emitted IR should be readable"))
            .expect("emitted IR should be JSON");
    assert_eq!(
        ir["module"], example.module,
        "{} emitted wrong module",
        example.path
    );

    let mut functions = Vec::new();
    let mut type_and_constant_exports = Vec::new();
    for declaration in ir["declarations"]
        .as_array()
        .expect("IR declarations should be an array")
    {
        if declaration["public"] != true {
            continue;
        }
        let qualified_name = declaration["name"]
            .as_str()
            .expect("public declaration should have a name");
        let name = qualified_name
            .rsplit('.')
            .next()
            .expect("public declaration should have a local name");
        if declaration["kind"] == "function" {
            functions.push(name.to_owned());
            continue;
        }

        type_and_constant_exports.push(name.to_owned());
        if declaration["kind"] == "enum" {
            type_and_constant_exports.extend(
                declaration["variants"]
                    .as_array()
                    .expect("enum variants should be an array")
                    .iter()
                    .map(|variant| {
                        format!(
                            "{name}_{}",
                            variant["name"]
                                .as_str()
                                .expect("enum variant should have a name")
                        )
                    }),
            );
        }
    }
    functions.sort();
    type_and_constant_exports.sort();

    let mut expected_functions = example
        .public_functions
        .iter()
        .map(|function| (*function).to_owned())
        .collect::<Vec<_>>();
    expected_functions.sort();
    assert_eq!(
        functions, expected_functions,
        "{} emitted the wrong public function set",
        example.path
    );
    assert!(
        functions
            .iter()
            .any(|function| function.as_str() == example.final_symbol),
        "{} does not export its final symbol {}",
        example.path,
        example.final_symbol
    );
    let mut facade_functions = python_all(&generated_module_file(
        root,
        "python",
        example.module,
        ".py",
    ));
    facade_functions.retain(|export| !type_and_constant_exports.contains(export));
    facade_functions.sort();
    let expected_facade_functions = if implementations_generated {
        expected_functions
    } else {
        Vec::new()
    };
    assert_eq!(
        facade_functions, expected_facade_functions,
        "{} facade exports do not match its generated implementations",
        example.path
    );
    assert_eq!(
        python_all(&generated_module_file(
            root,
            "python",
            example.module,
            "_types.py"
        )),
        type_and_constant_exports,
        "{} type and constant exports changed",
        example.path
    );
}

fn retarget_generation_to_host_python(root: &Path) -> Vec<u8> {
    let generation = root.join("generated/generation.json");
    let original = fs::read(&generation).expect("generation record");
    let script = r#"import hashlib,json,pathlib,platform,sys,sysconfig
p=pathlib.Path("generated/generation.json")
r=json.loads(p.read_bytes())
e=pathlib.Path(sys.executable).resolve()
r["current"]["tools"]["python"]={"cache_tag":sys.implementation.cache_tag,"content_hash":"sha256:"+hashlib.sha256(e.read_bytes()).hexdigest(),"executable":str(e),"implementation":sys.implementation.name,"machine":platform.machine(),"os":sys.platform,"platform":sysconfig.get_platform(),"version":platform.python_version()}
i=dict(r["current"])
for k in ("generation_id","verified","verification","agent_runs"): i.pop(k,None)
r["current"]["generation_id"]="sha256:"+hashlib.sha256(json.dumps(i,ensure_ascii=False,separators=(",",":"),sort_keys=True).encode()+b"\n").hexdigest()
p.write_text(json.dumps(r,ensure_ascii=False,separators=(",",":"),sort_keys=True)+"\n")
"#;
    let output = Command::new("python3")
        .args(["-c", script])
        .current_dir(root)
        .output()
        .expect("host Python should retarget test provenance");
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    original
}

#[test]
fn curriculum_inventory_and_final_symbols_are_exact() {
    assert_eq!(EXAMPLES.len(), 42);
    assert_eq!(
        EXAMPLES
            .iter()
            .filter(|example| example.path.starts_with("grammar/"))
            .count(),
        10
    );
    assert_eq!(
        EXAMPLES
            .iter()
            .filter(|example| example.path.starts_with("simple/"))
            .count(),
        16
    );
    assert_eq!(
        EXAMPLES
            .iter()
            .filter(|example| example.path.starts_with("complex/"))
            .count(),
        16
    );

    let paths = EXAMPLES
        .iter()
        .map(|example| example.path.to_owned())
        .collect::<BTreeSet<_>>();
    assert_eq!(
        paths.len(),
        EXAMPLES.len(),
        "curriculum paths must be unique"
    );
    let examples_root = Path::new(env!("CARGO_MANIFEST_DIR")).join("examples");
    let mut on_disk = BTreeSet::new();
    for category in ["grammar", "simple", "complex"] {
        for entry in
            fs::read_dir(examples_root.join(category)).expect("example category should be readable")
        {
            let entry = entry.expect("example entry should be readable");
            if entry
                .file_type()
                .expect("example entry type should be readable")
                .is_dir()
            {
                on_disk.insert(format!(
                    "{category}/{}",
                    entry.file_name().to_string_lossy()
                ));
            }
        }
    }
    on_disk.remove("complex/process-bar");
    assert_eq!(paths, on_disk, "curriculum inventory changed");
    for example in EXAMPLES {
        assert_ne!(example.path, "complex/process-bar");
        assert!(
            !example.public_functions.contains(&"run"),
            "{} exports run",
            example.path
        );
        assert!(
            example.public_functions.contains(&example.final_symbol),
            "{} final symbol is outside its exact public set",
            example.path
        );
    }
}

#[test]
fn every_documented_example_emits_and_verifies() {
    for example in EXAMPLES {
        let project = copied_project(example.path);
        let checked_add = example.path == "grammar/checked-add";
        let cott_bindings = authored_files_below(&project.path.join("python/cott_bindings"));
        let durable_implementations = authored_files_below(&project.path.join("python/_cott_impl"));

        if checked_add {
            assert_eq!(
                cott_bindings,
                [project
                    .path
                    .join("python/cott_bindings/curriculum/checked_add/checked_add.py")]
            );
            assert!(durable_implementations.is_empty());
        } else {
            assert!(
                cott_bindings.is_empty(),
                "{} has authored cott_bindings sources: {cott_bindings:?}",
                example.path
            );
            let module_path = example.module.replace('.', "/");
            let mut expected = example
                .public_functions
                .iter()
                .map(|function| {
                    project
                        .path
                        .join("python/_cott_impl")
                        .join(&module_path)
                        .join(format!("{function}.py"))
                })
                .collect::<Vec<_>>();
            expected.sort();
            assert_eq!(
                durable_implementations, expected,
                "{} has the wrong generated implementation set",
                example.path
            );
        }

        let formatted = cott(&project.path, &["fmt", "--check"]);
        assert!(
            formatted.status.success(),
            "{} failed cott fmt --check: {}",
            example.path,
            String::from_utf8_lossy(&formatted.stderr)
        );
        let checked = cott(&project.path, &["check"]);
        assert!(
            checked.status.success(),
            "{} failed cott check: {}",
            example.path,
            String::from_utf8_lossy(&checked.stderr)
        );
        let emitted = cott(&project.path, &["emit", "python"]);
        assert!(
            emitted.status.success(),
            "{} failed to emit: {}",
            example.path,
            String::from_utf8_lossy(&emitted.stderr)
        );
        assert_public_projection(&project.path, example, true);

        let generation: serde_json::Value = serde_json::from_slice(
            &fs::read(project.path.join("generated/generation.json"))
                .expect("generation record should be readable"),
        )
        .expect("generation record should be JSON");
        let implementations = generation["current"]["implementations"]
            .as_array()
            .expect("implementations should be an array");
        assert_eq!(implementations.len(), example.public_functions.len());
        let expected_symbols = example
            .public_functions
            .iter()
            .map(|function| format!("{}.{}", example.module, function))
            .collect::<BTreeSet<_>>();
        let implementation_symbols = implementations
            .iter()
            .map(|implementation| {
                implementation["cott_symbol"]
                    .as_str()
                    .expect("implementation should name its Cott symbol")
                    .to_owned()
            })
            .collect::<BTreeSet<_>>();
        assert_eq!(implementation_symbols, expected_symbols);
        assert_eq!(generation["current"]["unresolved"], serde_json::json!([]));

        if checked_add {
            assert_eq!(generation["current"]["agent_runs"], serde_json::json!([]));
            assert_eq!(implementations[0]["owner"], "manifest");
            assert_eq!(
                implementations[0]["source_origin"],
                "python/cott_bindings/curriculum/checked_add/checked_add.py"
            );
        } else {
            assert!(
                implementations
                    .iter()
                    .all(|implementation| implementation["owner"] == "agent")
            );
            let agent_symbols = generation["current"]["agent_runs"]
                .as_array()
                .expect("agent_runs should be an array")
                .iter()
                .map(|run| {
                    run["symbol"]
                        .as_str()
                        .expect("agent run should name its Cott symbol")
                        .to_owned()
                })
                .collect::<BTreeSet<_>>();
            assert_eq!(agent_symbols, expected_symbols);
        }

        let verified = cott(&project.path, &["verify"]);
        assert!(
            verified.status.success(),
            "{} failed to verify: {}",
            example.path,
            String::from_utf8_lossy(&verified.stderr)
        );
    }
}

#[test]
fn every_documented_example_runs_when_python3_is_available() {
    let usable_python = Command::new("python3")
        .args([
            "-c",
            "import sys; raise SystemExit(sys.version_info < (3, 10))",
        ])
        .status()
        .is_ok_and(|status| status.success());
    if !usable_python {
        return;
    }

    let example = EXAMPLES
        .iter()
        .find(|example| example.path == "grammar/checked-add")
        .expect("checked-add should be in the curriculum");
    let project = copied_project(example.path);
    let emitted = cott(&project.path, &["emit", "python"]);
    assert!(
        emitted.status.success(),
        "{} failed to emit: {}",
        example.path,
        String::from_utf8_lossy(&emitted.stderr)
    );
    let generation = retarget_generation_to_host_python(&project.path);
    let output = Command::new("python3")
        .args([
            "-c",
            "from curriculum.checked_add import checked_add; print(checked_add(2, 3))",
        ])
        .current_dir(project.path.join("generated/python"))
        .output()
        .expect("generated checked-add example should run");
    fs::write(project.path.join("generated/generation.json"), generation)
        .expect("restore verified generation record");
    assert!(
        output.status.success(),
        "{} failed to run: {}",
        example.path,
        String::from_utf8_lossy(&output.stderr)
    );
    assert_eq!(
        String::from_utf8(output.stdout).expect("example stdout must be UTF-8"),
        "5\n",
        "{} emitted unexpected stdout",
        example.path
    );
    let verified = cott(&project.path, &["verify"]);
    assert!(
        verified.status.success(),
        "{} failed to verify after execution: {}",
        example.path,
        String::from_utf8_lossy(&verified.stderr)
    );
}
#[test]
fn modular_order_management_example_emits_verifies_and_runs() {
    let project = copied_project("modular/order-management");

    let formatted = cott(&project.path, &["fmt", "--check"]);
    assert!(
        formatted.status.success(),
        "modular/order-management failed cott fmt --check: {}",
        String::from_utf8_lossy(&formatted.stderr)
    );
    let checked = cott(&project.path, &["check"]);
    assert!(
        checked.status.success(),
        "modular/order-management failed cott check: {}",
        String::from_utf8_lossy(&checked.stderr)
    );
    let emitted = cott(&project.path, &["emit", "python"]);
    assert!(
        emitted.status.success(),
        "modular/order-management failed to emit: {}",
        String::from_utf8_lossy(&emitted.stderr)
    );

    let generation: serde_json::Value = serde_json::from_slice(
        &fs::read(project.path.join("generated/generation.json"))
            .expect("generation record should be readable"),
    )
    .expect("generation record should be JSON");

    let implementations = generation["current"]["implementations"]
        .as_array()
        .expect("implementations should be an array");
    assert_eq!(implementations.len(), 3);
    assert_eq!(generation["current"]["unresolved"], serde_json::json!([]));

    let verified = cott(&project.path, &["verify"]);
    assert!(
        verified.status.success(),
        "modular/order-management failed to verify: {}",
        String::from_utf8_lossy(&verified.stderr)
    );

    let usable_python = Command::new("python3")
        .args([
            "-c",
            "import sys; raise SystemExit(sys.version_info < (3, 10))",
        ])
        .status()
        .is_ok_and(|status| status.success());
    if usable_python {
        let generation = retarget_generation_to_host_python(&project.path);
        let output = Command::new("python3")
            .arg(project.path.join("python/app.py"))
            .env("PYTHONPATH", project.path.join("generated/python"))
            .output()
            .expect("modular order-management app.py should run");
        fs::write(project.path.join("generated/generation.json"), generation)
            .expect("restore verified generation record");
        assert!(
            output.status.success(),
            "app.py failed to run: {}",
            String::from_utf8_lossy(&output.stderr)
        );
        let stdout = String::from_utf8(output.stdout).expect("example stdout must be UTF-8");
        assert!(stdout.contains("Catalog lookup: Honeycrisp Apple ($1.50)"));
        assert!(stdout.contains("Order ORD-2026-001: 6 items, total $30.00"));
    }
}

#[test]
fn feature_examples_emit_and_check() {
    let features: [(&str, &[&str]); 5] = [
        (
            "features/trait-protocol",
            &[
                "Write Documentation (urgency: 2)",
                "[2] Write Documentation (urgency: 2)",
                "Priority: 2",
                "Completed: True",
            ],
        ),
        ("features/opaque-resource", &["Extracted handle id: 42"]),
        (
            "features/json-transform",
            &["Extracted JSON field: Hello Cott"],
        ),
        ("features/pair-tuple", &["Swapped pair: (20, 10)"]),
        ("features/system-effects", &["Inspected path: /etc/hosts"]),
    ];
    let usable_python = Command::new("python3")
        .args([
            "-c",
            "import sys; raise SystemExit(sys.version_info < (3, 10))",
        ])
        .status()
        .is_ok_and(|status| status.success());

    for (feature, expected_outputs) in features {
        let project = copied_project(feature);
        let formatted = cott(&project.path, &["fmt", "--check"]);
        assert!(
            formatted.status.success(),
            "{feature} failed cott fmt --check: {}",
            String::from_utf8_lossy(&formatted.stderr)
        );
        let checked = cott(&project.path, &["check"]);
        assert!(
            checked.status.success(),
            "{feature} failed cott check: {}",
            String::from_utf8_lossy(&checked.stderr)
        );
        let emitted = cott(&project.path, &["emit", "python"]);
        assert!(
            emitted.status.success(),
            "{feature} failed to emit: {}",
            String::from_utf8_lossy(&emitted.stderr)
        );

        if usable_python {
            let generation = retarget_generation_to_host_python(&project.path);
            let output = Command::new("python3")
                .arg(project.path.join("python/app.py"))
                .env("PYTHONPATH", project.path.join("generated/python"))
                .output()
                .expect("feature app.py should run");
            assert!(
                output.status.success(),
                "{feature} app.py failed to run: {}",
                String::from_utf8_lossy(&output.stderr)
            );
            let stdout = String::from_utf8(output.stdout).expect("output must be UTF-8");
            for &expected_output in expected_outputs {
                assert!(
                    stdout.contains(expected_output),
                    "{feature} output did not contain {expected_output}: {stdout}"
                );
            }
            if feature == "features/trait-protocol" {
                let generated = Command::new("python3")
                    .args([
                        "-c",
                        concat!(
                            "from curriculum.trait_protocol import SimpleTask, format_summary, inspect_task\n",
                            "task = SimpleTask('Write Documentation', 2)\n",
                            "assert format_summary(task) == 'Write Documentation (urgency: 2)'\n",
                            "assert inspect_task(task) == '[2] Write Documentation (urgency: 2)'\n",
                            "assert task.priority_level() == 2\n",
                            "assert task.complete() is True\n",
                            "assert task.completed is True\n",
                        ),
                    ])
                    .env("PYTHONPATH", project.path.join("generated/python"))
                    .output()
                    .expect("generated SimpleTask should run");
                assert!(
                    generated.status.success(),
                    "generated SimpleTask behavior failed: {}",
                    String::from_utf8_lossy(&generated.stderr)
                );
            }
            fs::write(project.path.join("generated/generation.json"), generation)
                .expect("restore verified generation record");
        }
    }
}
