use cott::provenance::{
    GENERATION_SCHEMA_VERSION, GenerationCompatibility, GenerationRecord, GenerationSnapshot,
    RUNTIME_ABI_VERSION,
};

use std::collections::BTreeSet;
use std::fs;
use std::io;
#[cfg(unix)]
use std::os::unix::fs::FileTypeExt;
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
struct RealExample {
    path: &'static str,
    upstream_url: &'static str,
    source_files: &'static [&'static str],
    adapter_files: &'static [&'static str],
}

const REAL_EXAMPLES: &[RealExample] = &[
    RealExample {
        path: "real/yt-dlp",
        upstream_url: "https://github.com/yt-dlp/yt-dlp",
        source_files: &["src/real/yt_dlp.cott"],
        adapter_files: &["python/app.py"],
    },
    RealExample {
        path: "real/harlequin",
        upstream_url: "https://github.com/tconbeer/harlequin",
        source_files: &[
            "src/real/harlequin/catalog.cott",
            "src/real/harlequin/core.cott",
            "src/real/harlequin/render.cott",
        ],
        adapter_files: &["python/harlequin_cli.py"],
    },
    RealExample {
        path: "real/pgcli",
        upstream_url: "https://github.com/dbcli/pgcli",
        source_files: &["src/real/pgcli.cott"],
        adapter_files: &["python/pgcli_cli.py"],
    },
    RealExample {
        path: "real/posting",
        upstream_url: "https://github.com/darrenburns/posting",
        source_files: &["src/real/posting/client.cott"],
        adapter_files: &["python/posting_cli.py"],
    },
    RealExample {
        path: "real/toolong",
        upstream_url: "https://github.com/Textualize/toolong",
        source_files: &["src/real/toolong.cott"],
        adapter_files: &["python/toolong.py"],
    },
    RealExample {
        path: "real/frogmouth",
        upstream_url: "https://github.com/Textualize/frogmouth",
        source_files: &[
            "src/real/frogmouth/document.cott",
            "src/real/frogmouth/model.cott",
            "src/real/frogmouth/navigation.cott",
        ],
        adapter_files: &[
            "python/frogmouth_ui/__init__.py",
            "python/frogmouth_ui/create_browser_app.py",
            "python/frogmouth_ui/run_browser.py",
        ],
    },
];

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
        path: "grammar/assignment-rule",
        module: "curriculum.assignment_rule",
        public_functions: &["validate_access_code"],
        final_symbol: "validate_access_code",
    },
    Example {
        path: "simple/calculator",
        module: "curriculum.calculator",
        public_functions: &["calculate"],
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
        path: "simple/alphabetical-file-groups",
        module: "curriculum.alphabetical_file_groups",
        public_functions: &["classify_filename", "group_filenames"],
        final_symbol: "group_filenames",
    },
    Example {
        path: "complex/artifact-pipeline",
        module: "curriculum.artifact_pipeline",
        public_functions: &["topologically_order_steps", "plan_pipeline"],
        final_symbol: "plan_pipeline",
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
    retarget_copied_generation(&temp.path);
    let path = temp.path.join(".cott");
    if let Err(error) = fs::remove_dir_all(&path) {
        assert_eq!(
            error.kind(),
            io::ErrorKind::NotFound,
            "failed to remove copied transient state {}: {error}",
            path.display()
        );
    }
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
        let name = entry.file_name();
        if matches!(name.to_str(), Some(".venv" | ".cott" | "__pycache__"))
            || name.to_string_lossy().ends_with(".pyc")
        {
            continue;
        }
        let source_path = entry.path();
        let destination_path = destination.join(&name);
        let file_type = entry
            .file_type()
            .expect("example entry type should be readable");
        if file_type.is_symlink() || file_type.is_socket() {
            continue;
        }
        if file_type.is_dir() {
            copy_tree(&source_path, &destination_path);
        } else if file_type.is_file() {
            fs::copy(&source_path, &destination_path).expect("example file should be copyable");
        } else {
            panic!(
                "example contains unsafe filesystem entry: {}",
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

fn implementation_mappings(manifest: &str) -> Vec<&str> {
    let mut in_implementations = false;
    let mut mappings = Vec::new();
    for line in manifest.lines() {
        let line = line.trim();
        if line.starts_with('[') {
            in_implementations = line == "[target.python.implementations]";
        } else if in_implementations && line.starts_with('"') && line.contains('=') {
            mappings.push(line);
        }
    }
    mappings
}

fn binding_source_file(mapping: &str) -> PathBuf {
    let (_, target) = mapping
        .split_once('=')
        .expect("implementation mapping should have a target");
    let (module, _) = target
        .trim()
        .trim_matches('"')
        .split_once(':')
        .expect("implementation target should name a callable");
    PathBuf::from("python/cott_bindings").join(format!(
        "{}.py",
        module
            .strip_prefix("cott_bindings.")
            .expect("implementation target should be a cott_bindings module")
            .replace('.', "/")
    ))
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
    let declarations = ir["declarations"]
        .as_array()
        .expect("IR declarations should be an array");
    for declaration in declarations {
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

fn assert_generation_identity(generation: &serde_json::Value) {
    assert_eq!(generation["schema_version"], 7);
    assert_eq!(
        generation["current"]["compatibility"],
        serde_json::json!({
            "generation_schema": 7,
            "canonical_ir_schema": 8,
            "runtime_abi": 7,
            "contract_strategy_schema": 5,
        })
    );
}

fn assert_generation_metadata(generation: &serde_json::Value) {
    assert_generation_identity(generation);
    assert_eq!(
        generation["current"]["semantic_coverage"],
        serde_json::json!({
            "clauses": [],
            "summary": {"observed": 0, "unobserved": 0, "trust_declaration": 0, "unknown": 0},
            "policy": {"selected": 0, "passed": true, "violations": []},
        })
    );
}

fn update_generation_record(
    root: &Path,
    mut update: impl FnMut(&mut GenerationSnapshot),
) -> Option<Vec<u8>> {
    let generation = root.join("generated/generation.json");
    let original = match fs::read(&generation) {
        Ok(bytes) => bytes,
        Err(error) if error.kind() == io::ErrorKind::NotFound => return None,
        Err(error) => panic!(
            "read copied generation record {}: {error}",
            generation.display()
        ),
    };
    let mut record: GenerationRecord = serde_json::from_slice(&original).unwrap_or_else(|error| {
        panic!(
            "deserialize copied generation record {} without validation: {error}",
            generation.display()
        )
    });
    record.schema_version = GENERATION_SCHEMA_VERSION;
    for snapshot in std::iter::once(&mut record.current).chain(record.last_verified.iter_mut()) {
        update(snapshot);
        snapshot
            .compute_generation_id()
            .expect("recompute copied generation identity");
    }
    let bytes = record
        .canonical_bytes()
        .expect("serialize retargeted generation record");
    fs::write(&generation, bytes).expect("write retargeted generation record");
    Some(original)
}

fn retarget_copied_generation(root: &Path) {
    let retargeted = update_generation_record(root, |snapshot| {
        snapshot.compatibility = GenerationCompatibility::current();
        snapshot
            .tools
            .as_object_mut()
            .expect("copied generation tool evidence must be an object")
            .insert(
                "runtime".to_owned(),
                serde_json::json!({
                    "abi": RUNTIME_ABI_VERSION.to_string(),
                    "version": env!("CARGO_PKG_VERSION"),
                }),
            );
    });
    assert!(
        retargeted.is_some() || !root.join("generated").exists(),
        "copied managed tree lacks generated/generation.json"
    );
}

fn retarget_generation_to_python(root: &Path, python: impl AsRef<Path>) -> Vec<u8> {
    let script = r#"import hashlib,json,pathlib,platform,sys,sysconfig
e=pathlib.Path(sys.executable).resolve()
print(json.dumps({"cache_tag":sys.implementation.cache_tag,"content_hash":"sha256:"+hashlib.sha256(e.read_bytes()).hexdigest(),"executable":str(e),"implementation":sys.implementation.name,"machine":platform.machine(),"os":sys.platform,"platform":sysconfig.get_platform(),"version":platform.python_version()}))
"#;
    let output = Command::new(python.as_ref())
        .args(["-c", script])
        .output()
        .expect("Python should inspect test provenance");
    assert!(
        output.status.success(),
        "{}",
        String::from_utf8_lossy(&output.stderr)
    );
    let python_tools: serde_json::Value =
        serde_json::from_slice(&output.stdout).expect("Python tool evidence should be JSON");
    update_generation_record(root, |snapshot| {
        snapshot
            .tools
            .as_object_mut()
            .expect("generation tool evidence must be an object")
            .insert("python".to_owned(), python_tools.clone());
    })
    .expect("emitted generation record")
}

fn retarget_generation_to_host_python(root: &Path) -> Vec<u8> {
    retarget_generation_to_python(root, "python3")
}

#[test]
fn curriculum_inventory_and_final_symbols_are_exact() {
    assert_eq!(EXAMPLES.len(), 10);
    assert_eq!(
        EXAMPLES
            .iter()
            .filter(|example| example.path.starts_with("grammar/"))
            .count(),
        6
    );
    assert_eq!(
        EXAMPLES
            .iter()
            .filter(|example| example.path.starts_with("simple/"))
            .count(),
        3
    );
    assert_eq!(
        EXAMPLES
            .iter()
            .filter(|example| example.path.starts_with("complex/"))
            .count(),
        1
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
        assert!(
            example.public_functions.contains(&example.final_symbol),
            "{} final symbol is outside its exact public set",
            example.path
        );
    }
}

#[test]
fn real_inventory_has_canonical_origins_and_verified_generated_shape() {
    assert_eq!(REAL_EXAMPLES.len(), 6);
    let expected_paths = REAL_EXAMPLES
        .iter()
        .map(|example| example.path.to_owned())
        .collect::<BTreeSet<String>>();
    let examples_root = Path::new(env!("CARGO_MANIFEST_DIR")).join("examples");
    let on_disk = fs::read_dir(examples_root.join("real"))
        .expect("real example directory should be readable")
        .map(|entry| entry.expect("real example entry should be readable"))
        .filter(|entry| {
            entry
                .file_type()
                .expect("real example type should be readable")
                .is_dir()
        })
        .map(|entry| format!("real/{}", entry.file_name().to_string_lossy()))
        .collect::<BTreeSet<_>>();
    assert_eq!(expected_paths, on_disk, "real example inventory changed");

    for example in REAL_EXAMPLES {
        let project = examples_root.join(example.path);
        let readme =
            fs::read_to_string(project.join("README.md")).expect("real README is readable");
        let mut readme_lines = readme.lines();
        assert_eq!(
            readme_lines.next(),
            Some(format!("# {}", example.upstream_url).as_str()),
            "{} README must lead with its canonical upstream URL",
            example.path
        );
        assert!(
            readme_lines
                .find(|line| !line.trim().is_empty())
                .is_some_and(|line| line.contains("Cott reimplementation")),
            "{} README must immediately identify the Cott reimplementation",
            example.path
        );

        let manifest = fs::read_to_string(project.join("cott.toml"))
            .expect("real project manifest is readable");
        assert!(
            manifest.contains("version = \"0.1.0\""),
            "{} must retain project API version 0.1.0",
            example.path
        );
        let mappings = implementation_mappings(&manifest);
        let binding_root = project.join("python/cott_bindings");
        let expected_mappings = match example.path {
            "real/yt-dlp" => vec![
                "\"real.yt_dlp.transfer_media\" = \"cott_bindings.real.yt_dlp.transfer_media:transfer_media\"",
            ],
            "real/harlequin" => {
                vec!["\"real.harlequin.core.run\" = \"cott_bindings.real.harlequin.core.run:run\""]
            }
            "real/posting" => vec![
                "\"real.posting.client.send_request\" = \"cott_bindings.real.posting.client.send_request:send_request\"",
            ],
            "real/frogmouth" => vec![
                "\"frogmouth.document.load_document\" = \"cott_bindings.frogmouth.document.load_document:load_document\"",
            ],
            _ => Vec::new(),
        };
        assert_eq!(
            mappings, expected_mappings,
            "{} must retain only its essential bindings",
            example.path
        );
        if mappings.is_empty() {
            assert!(
                !binding_root.exists(),
                "{} must not have a cott_bindings source tree",
                example.path
            );
        }

        let source_files = authored_files_below(&project.join("src"))
            .iter()
            .map(|path| {
                path.strip_prefix(&project)
                    .expect("source file should remain within its project")
                    .to_string_lossy()
                    .into_owned()
            })
            .collect::<BTreeSet<_>>();
        assert_eq!(
            source_files,
            example
                .source_files
                .iter()
                .map(|path| (*path).to_owned())
                .collect(),
            "{} source shape changed",
            example.path
        );

        let adapter_files = authored_files_below(&project.join("python"))
            .into_iter()
            .filter(|path| path.extension().is_some_and(|extension| extension == "py"))
            .filter(|path| {
                !path.starts_with(project.join("python/cott_bindings"))
                    && !path.starts_with(project.join("python/_cott_impl"))
            })
            .map(|path| {
                path.strip_prefix(&project)
                    .expect("adapter should remain within its project")
                    .to_string_lossy()
                    .into_owned()
            })
            .collect::<BTreeSet<_>>();
        assert_eq!(
            adapter_files,
            example
                .adapter_files
                .iter()
                .map(|path| (*path).to_owned())
                .collect(),
            "{} adapter shape changed",
            example.path
        );
        for adapter in example.adapter_files {
            let adapter = fs::read_to_string(project.join(adapter)).expect("adapter is readable");
            assert!(
                !adapter.contains("_cott_impl") && !adapter.contains("cott_bindings"),
                "{} adapter must import only public generated facades",
                example.path
            );
        }

        if !mappings.is_empty() {
            let mapped_binding_sources = mappings
                .iter()
                .map(|mapping| binding_source_file(mapping))
                .collect::<BTreeSet<_>>();
            let binding_sources = authored_files_below(&binding_root)
                .into_iter()
                .filter(|path| path.file_name().is_some_and(|name| name != "__init__.py"))
                .map(|path| {
                    path.strip_prefix(&project)
                        .expect("binding source should remain within its project")
                        .to_path_buf()
                })
                .collect::<BTreeSet<_>>();
            assert_eq!(
                binding_sources, mapped_binding_sources,
                "{} binding sources must match its manifest mappings",
                example.path
            );
            for source in mapped_binding_sources {
                assert!(
                    project.join(&source).is_file(),
                    "{} mapped binding source must exist: {}",
                    example.path,
                    source.display()
                );
            }
        }

        let generation_path = project.join("generated/generation.json");
        let bytes = fs::read(&generation_path).expect("real projects need generation metadata");
        let generation: serde_json::Value =
            serde_json::from_slice(&bytes).expect("generation metadata should be JSON");
        GenerationRecord::parse(&bytes).expect("generation metadata must use the current schema");
        assert_generation_identity(&generation);
        assert_eq!(generation["current"]["verified"], true);
        assert_eq!(
            generation["last_verified"]["generation_id"], generation["current"]["generation_id"],
            "{} generated output is stale",
            example.path
        );
        assert_eq!(generation["current"]["project_version"], "0.1.0");
        for tool in ["compiler", "runtime"] {
            assert_eq!(
                generation["current"]["tools"][tool]["version"],
                env!("CARGO_PKG_VERSION"),
                "{} {tool} package version drifted",
                example.path
            );
        }
    }
}

#[test]
fn every_curriculum_example_is_formatted_checked_emitted_and_verified() {
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
        assert_generation_metadata(&generation);
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
fn checked_add_generated_example_runs_when_python3_is_available() {
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

    let project = copied_project("grammar/checked-add");
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
        "checked-add failed to run: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    assert_eq!(
        String::from_utf8(output.stdout).expect("example stdout must be UTF-8"),
        "5\n",
        "checked-add emitted unexpected stdout"
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
fn feature_examples_are_formatted_checked_emitted_verified_and_run() {
    let features: [(&str, &str); 7] = [
        (
            "features/trait-protocol",
            "Factory exact: True\nExplicit: Write Documentation\nSpecialized: specialized: Write Documentation\nDefault: default\nDyn: Write Documentation\nPriority: 2\nCompleted: True\nCompletion count: 1\n",
        ),
        ("features/workflow-scenario", "new result\npublished\n"),
        (
            "features/effects-selection",
            "Compiler-owned fixture scenarios exercise: copy_text, fetch_local, clock_ns, copy_result_is_ok, text_result_is_ok, text_result_text\n",
        ),
        (
            "features/json-transform",
            "Extracted JSON field: Hello Cott\nRecursive JSON chain: first\n",
        ),
        (
            "features/declarations-generics",
            "label=Cott; values=(3, 1, 4, 1); bytes=636f7474\n",
        ),
        (
            "features/contracts-evidence",
            "LabelEvidenceError_Missing()\nLabelEvidenceError_TooShort(actual='ok')\nevidence\n",
        ),
        (
            "features/boundary-protocols",
            "Wrapped raw id: 42\nExtracted handle id: 42\nNarrowed unknown: explicit\nLines: alpha,beta\nGenerator return count: 2\nGenerated values: first,7\nAsync lines: gamma,delta\nAsync iterator completed\nAsync generated values: first,7\nAsync generator completed\nAsync generator closed twice\n",
        ),
    ];
    let usable_python = Command::new("python3")
        .args([
            "-c",
            "import sys; raise SystemExit(sys.version_info < (3, 10))",
        ])
        .status()
        .is_ok_and(|status| status.success());

    for (feature, expected_output) in features {
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
        let generation: serde_json::Value = serde_json::from_slice(
            &fs::read(project.path.join("generated/generation.json"))
                .expect("generation record should be readable"),
        )
        .expect("generation record should be JSON");
        assert_generation_metadata(&generation);

        if feature == "features/workflow-scenario" {
            let workflow = Example {
                path: feature,
                module: "curriculum.workflow_scenario",
                public_functions: &[
                    "apply_search",
                    "begin_save",
                    "begin_search",
                    "flush_save",
                    "request_save",
                    "resolve_search",
                ],
                final_symbol: "flush_save",
            };
            assert_public_projection(&project.path, &workflow, true);
            let ir: serde_json::Value = serde_json::from_slice(
                &fs::read(generated_module_file(
                    &project.path,
                    "ir",
                    workflow.module,
                    ".json",
                ))
                .expect("scenario IR should be readable"),
            )
            .expect("scenario IR should be JSON");
            assert_eq!(
                ir["declarations"]
                    .as_array()
                    .expect("scenario declarations should be an array")
                    .iter()
                    .filter(|declaration| declaration["kind"] == "scenario")
                    .map(|declaration| declaration["public"].as_bool())
                    .collect::<Vec<_>>(),
                [Some(false)]
            );
        }

        if usable_python {
            let generation = retarget_generation_to_host_python(&project.path);
            let output = Command::new("python3")
                .arg(project.path.join("python/app.py"))
                .env("PYTHONPATH", project.path.join("generated/python"))
                .output()
                .expect("feature app.py should run");
            fs::write(project.path.join("generated/generation.json"), generation)
                .expect("restore verified generation record");
            assert!(
                output.status.success(),
                "{feature} app.py failed to run: {}",
                String::from_utf8_lossy(&output.stderr)
            );
            assert_eq!(
                String::from_utf8(output.stdout).expect("output must be UTF-8"),
                expected_output,
                "{feature} output changed"
            );
        }

        let verified = cott(&project.path, &["verify"]);
        assert!(
            verified.status.success(),
            "{feature} failed to verify: {}",
            String::from_utf8_lossy(&verified.stderr)
        );
        if feature == "features/workflow-scenario" {
            let generation: serde_json::Value = serde_json::from_slice(
                &fs::read(project.path.join("generated/generation.json"))
                    .expect("verified generation record should be readable"),
            )
            .expect("verified generation record should be JSON");
            let scenarios = generation["current"]["verification"]["contract_tests"]["scenarios"]
                .as_array()
                .expect("verification should record scenario evidence");
            assert_eq!(scenarios.len(), 1);
            assert_eq!(
                scenarios[0]["scenario_id"],
                "curriculum.workflow_scenario.scenario.latest_result_and_coalesced_save"
            );
            assert_eq!(scenarios[0]["grade"], "test observation");
            assert!(
                scenarios[0]["assertions"]
                    .as_array()
                    .expect("scenario should record assertions")
                    .iter()
                    .all(|assertion| assertion["grade"] == "test observation")
            );
            assert_eq!(
                generation["current"]["semantic_coverage"]["summary"],
                serde_json::json!({
                    "observed": 4,
                    "unobserved": 0,
                    "trust_declaration": 0,
                    "unknown": 0,
                })
            );
        }
        if feature == "features/effects-selection" {
            let generation: serde_json::Value = serde_json::from_slice(
                &fs::read(project.path.join("generated/generation.json"))
                    .expect("verified generation record should be readable"),
            )
            .expect("verified generation record should be JSON");
            let scenarios = generation["current"]["verification"]["contract_tests"]["scenarios"]
                .as_array()
                .expect("verification should record effect scenarios");
            assert_eq!(
                scenarios
                    .iter()
                    .map(|scenario| scenario["scenario_id"].as_str().unwrap())
                    .collect::<Vec<_>>(),
                [
                    "curriculum.effects_selection.scenario.filesystem_copy",
                    "curriculum.effects_selection.scenario.filesystem_replace_failure",
                    "curriculum.effects_selection.scenario.local_http",
                    "curriculum.effects_selection.scenario.deterministic_clock",
                ]
            );
            assert!(
                scenarios
                    .iter()
                    .all(|scenario| scenario["grade"] == "unobserved")
            );
            assert_eq!(
                generation["current"]["semantic_coverage"]["summary"],
                serde_json::json!({
                    "observed": 0,
                    "unobserved": 0,
                    "trust_declaration": 11,
                    "unknown": 2,
                })
            );
        }
    }
}

#[test]
fn fastapi_hello_projects_external_request_through_testclient_when_available() {
    let project = copied_project("integrations/fastapi-hello");
    let verified_generation_bytes = fs::read(project.path.join("generated/generation.json"))
        .expect("copied generation record should be readable");
    let verified_generation: serde_json::Value = serde_json::from_slice(&verified_generation_bytes)
        .expect("copied generation record should be JSON");
    let verified_starlette_installed = verified_generation["current"]["dependencies"]
        .as_array()
        .expect("committed dependencies should be an array")
        .iter()
        .find(|dependency| dependency["name"] == "starlette")
        .expect("committed generation should record Starlette")["installed"]
        .clone();

    for arguments in [["fmt", "--check"].as_slice(), ["check"].as_slice()] {
        let output = cott(&project.path, arguments);
        assert!(
            output.status.success(),
            "integrations/fastapi-hello failed cott {}: {}",
            arguments.join(" "),
            String::from_utf8_lossy(&output.stderr)
        );
    }

    let emitted = cott(&project.path, &["emit", "python"]);
    assert!(
        emitted.status.success(),
        "integrations/fastapi-hello failed cott emit python: {}",
        String::from_utf8_lossy(&emitted.stderr)
    );
    let emitted_generation: serde_json::Value = serde_json::from_slice(
        &fs::read(project.path.join("generated/generation.json"))
            .expect("emitted generation record should be readable"),
    )
    .expect("emitted generation record should be JSON");
    assert_generation_identity(&emitted_generation);
    let starlette = emitted_generation["current"]["dependencies"]
        .as_array()
        .expect("verified dependencies should be an array")
        .iter()
        .find(|dependency| dependency["name"] == "starlette")
        .expect("verified generation should record Starlette");
    assert_eq!(
        starlette["installed"], verified_starlette_installed,
        "emitting Python must preserve Starlette's installed evidence"
    );
    let interpreter = Path::new(env!("CARGO_MANIFEST_DIR"))
        .join("examples/integrations/fastapi-hello/.venv/bin/python");
    let usable_testclient = Command::new(&interpreter)
        .args([
            "-c",
            "import fastapi; from fastapi.testclient import TestClient",
        ])
        .status()
        .is_ok_and(|status| status.success());

    if !usable_testclient {
        return;
    }

    fs::write(
        project.path.join("generated/generation.json"),
        &verified_generation_bytes,
    )
    .expect("restore copied verified generation record");
    let pre_retarget_generation = retarget_generation_to_python(&project.path, &interpreter);
    let retargeted_generation: serde_json::Value = serde_json::from_slice(
        &fs::read(project.path.join("generated/generation.json"))
            .expect("retargeted generation record should be readable"),
    )
    .expect("retargeted generation record should be JSON");
    assert_generation_identity(&retargeted_generation);
    let starlette = retargeted_generation["current"]["dependencies"]
        .as_array()
        .expect("verified dependencies should be an array")
        .iter()
        .find(|dependency| dependency["name"] == "starlette")
        .expect("verified generation should record Starlette");
    let installed = &starlette["installed"];
    assert_eq!(installed["version"], "1.6.0");
    let metadata_hash = Command::new(&interpreter)
        .args([
            "-c",
            "import hashlib, importlib.metadata as md; print('sha256:' + hashlib.sha256(md.distribution('starlette').read_text('METADATA').encode()).hexdigest())",
        ])
        .output()
        .expect("prepared Python should inspect Starlette metadata");
    assert!(metadata_hash.status.success());
    let metadata_hash = String::from_utf8_lossy(&metadata_hash.stdout);
    assert!(metadata_hash.starts_with("sha256:"));
    assert_eq!(installed["metadata_hash"], metadata_hash.trim());
    assert_eq!(installed["imports"], serde_json::json!(["starlette"]));
    assert!(
        installed["origins"]
            .as_array()
            .is_some_and(|origins| !origins.is_empty()),
        "verified Starlette provenance should include regular-file origins"
    );

    let output = Command::new(&interpreter)
        .args([
            "-c",
            concat!(
                "import json\n",
                "from fastapi.testclient import TestClient\n",
                "from app import app\n",
                "response = TestClient(app).get('/')\n",
                "print(json.dumps({'status': response.status_code, 'body': response.json()}))\n",
            ),
        ])
        .current_dir(project.path.join("python"))
        .env("PYTHONPATH", project.path.join("generated/python"))
        .output()
        .expect("FastAPI TestClient should run");
    fs::write(
        project.path.join("generated/generation.json"),
        pre_retarget_generation,
    )
    .expect("restore copied verified generation record");
    assert!(
        output.status.success(),
        "FastAPI external request projection failed: {}",
        String::from_utf8_lossy(&output.stderr)
    );
    let response: serde_json::Value =
        serde_json::from_slice(&output.stdout).expect("FastAPI TestClient response should be JSON");
    assert_eq!(response["status"], 200);
    assert_eq!(
        response["body"],
        serde_json::json!({"message": "Hello World", "method": "GET"})
    );
}
