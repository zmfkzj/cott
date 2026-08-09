use std::collections::HashSet;
use std::fs;
use std::path::{Path, PathBuf};

use crate::hash::sha256_hex;
use crate::project::Project;
use crate::python::artifact_plan::PythonArtifactPlan;

/// A validated implementation binding and its byte identity.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ResolvedBinding {
    pub module: String,
    pub function: String,
    pub source: PathBuf,
    pub generated_relative: PathBuf,
    pub bytes: Vec<u8>,
    pub sha256: String,
}

/// A stable diagnostic for one expected implementation binding.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct BindingDiagnostic {
    pub path: PathBuf,
    pub message: String,
}

/// Resolution separates absent durable sources from invalid sources so
/// `generate` can supply only truly unresolved functions to an agent.
#[derive(Clone, Debug, Eq, PartialEq)]
pub struct ImplementationResolution {
    pub resolved: Vec<ResolvedBinding>,
    pub unresolved: Vec<UnresolvedBinding>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct UnresolvedBinding {
    pub module: String,
    pub function: String,
    pub source: PathBuf,
}

/// Resolves every canonical planned function to the corresponding Python implementation.
pub fn resolve_bindings(
    project: &Project,
    plan: &PythonArtifactPlan,
) -> Result<Vec<ResolvedBinding>, Vec<BindingDiagnostic>> {
    let resolution = resolve_implementations(project, plan)?;
    if resolution.unresolved.is_empty() {
        Ok(resolution.resolved)
    } else {
        Err(resolution
            .unresolved
            .into_iter()
            .map(|binding| BindingDiagnostic {
                path: binding.source,
                message: "missing implementation binding".to_owned(),
            })
            .collect())
    }
}

pub fn resolve_implementations(
    project: &Project,
    plan: &PythonArtifactPlan,
) -> Result<ImplementationResolution, Vec<BindingDiagnostic>> {
    let mut resolved = Vec::new();
    let mut unresolved = Vec::new();
    let mut diagnostics = Vec::new();
    let local_imports = local_import_roots(project, plan);
    let generated_type_modules = generated_type_modules(plan);
    for callable in plan.callable_functions() {
        let function = callable
            .function
            .rsplit('.')
            .next()
            .unwrap_or(&callable.function)
            .to_owned();
        let mut source = project.implementation_dir.clone();
        let mut generated = PathBuf::from("_cott_impl");
        for segment in callable.module.split('.') {
            source.push(segment);
            generated.push(segment);
        }
        source.push(format!("{function}.py"));
        generated.push(format!("{function}.py"));
        if !source.exists() {
            unresolved.push(UnresolvedBinding {
                module: callable.module,
                function,
                source,
            });
            continue;
        }
        match read_binding(&source, &function, &local_imports, &generated_type_modules) {
            Ok(bytes) => resolved.push(ResolvedBinding {
                module: callable.module,
                function,
                source,
                generated_relative: generated,
                sha256: sha256_hex(&bytes),
                bytes,
            }),
            Err(message) => diagnostics.push(BindingDiagnostic {
                path: source,
                message,
            }),
        }
    }
    if diagnostics.is_empty() {
        Ok(ImplementationResolution {
            resolved,
            unresolved,
        })
    } else {
        Err(diagnostics)
    }
}

pub fn validate_candidate(
    project: &Project,
    plan: &PythonArtifactPlan,
    function: &str,
    bytes: &[u8],
) -> Result<(), String> {
    let source =
        std::str::from_utf8(bytes).map_err(|_| "binding source is not valid UTF-8".to_owned())?;
    let function = function.rsplit('.').next().unwrap_or(function);
    validate_source(
        source,
        function,
        &local_import_roots(project, plan),
        &generated_type_modules(plan),
    )
}

fn local_import_roots(project: &Project, plan: &PythonArtifactPlan) -> HashSet<String> {
    let mut roots = HashSet::from([String::from("_cott_impl"), project.name.clone()]);
    for module in plan.modules() {
        if let Some(root) = module.module.split('.').next() {
            roots.insert(root.to_owned());
        }
    }
    roots
}

fn generated_type_modules(plan: &PythonArtifactPlan) -> HashSet<String> {
    plan.modules()
        .iter()
        .map(|module| format!("{}_types", module.module))
        .collect()
}

fn read_binding(
    path: &Path,
    expected_function: &str,
    local_imports: &HashSet<String>,
    generated_type_modules: &HashSet<String>,
) -> Result<Vec<u8>, String> {
    let metadata = fs::symlink_metadata(path)
        .map_err(|error| format!("missing or unreadable binding: {error}"))?;
    if metadata.file_type().is_symlink() {
        return Err(String::from("binding must be a regular non-symlink file"));
    }
    if !metadata.is_file() {
        return Err(String::from("binding must be a regular non-symlink file"));
    }

    let bytes = fs::read(path).map_err(|error| format!("unable to read binding: {error}"))?;
    let text = std::str::from_utf8(&bytes)
        .map_err(|_| String::from("binding source is not valid UTF-8"))?;
    validate_source(
        text,
        expected_function,
        local_imports,
        generated_type_modules,
    )?;
    Ok(bytes)
}

fn validate_source(
    source: &str,
    expected_function: &str,
    local_imports: &HashSet<String>,
    generated_type_modules: &HashSet<String>,
) -> Result<(), String> {
    let masked = mask_python(source);
    let mut errors = Vec::new();
    let mut add_error = |message: String| {
        if !errors.contains(&message) {
            errors.push(message);
        }
    };

    for token in identifier_tokens(&masked) {
        match token.as_str() {
            "pass" => add_error(String::from("placeholder statement 'pass' is not allowed")),
            "NotImplementedError" => add_error(String::from(
                "placeholder exception 'NotImplementedError' is not allowed",
            )),
            "eval" | "exec" | "compile" => {
                add_error(format!("dynamic operation '{token}' is not allowed"))
            }
            "__import__" | "importlib" | "import_module" => {
                add_error(String::from("dynamic imports are not allowed"))
            }
            "agent" | "agents" => add_error(String::from("agent operations are not allowed")),
            "async" => add_error(String::from("async implementation is not allowed")),
            _ => {}
        }
    }
    if masked.contains("...") {
        add_error(String::from("ellipsis placeholder '...' is not allowed"));
    }
    inspect_imports(
        &masked,
        local_imports,
        generated_type_modules,
        &mut add_error,
    );
    inspect_function_definitions(&masked, expected_function, &mut add_error);

    if errors.is_empty() {
        Ok(())
    } else {
        Err(errors.join("; "))
    }
}

fn inspect_function_definitions(
    source: &str,
    expected_function: &str,
    add_error: &mut impl FnMut(String),
) {
    let lines: Vec<&str> = source.lines().collect();
    let mut expected_count = 0;
    let mut valid_count = 0;
    let mut expected_line = None;

    for (line_number, line) in lines.iter().enumerate() {
        if !line.starts_with("def ") {
            continue;
        }
        let signature = collect_signature(&lines, line_number);
        let name = signature
            .strip_prefix("def ")
            .and_then(|rest| rest.split_once('('))
            .map(|(name, _)| name.trim());
        if name != Some(expected_function) {
            continue;
        }

        expected_count += 1;
        expected_line = Some(line_number);
        if is_zero_argument_signature(&signature, expected_function) {
            valid_count += 1;
        }
    }

    match (expected_count, valid_count) {
        (0, _) => add_error(format!(
            "implementation must define expected function '{expected_function}'"
        )),
        (1, 0) => add_error(format!(
            "function '{expected_function}' must have exactly the signature def {expected_function}() -> ...:"
        )),
        (_, _) if valid_count != 1 => add_error(format!(
            "implementation must define exactly one top-level function '{expected_function}'"
        )),
        _ => {}
    }

    if let Some(line_number) = expected_line {
        let mut previous = line_number;
        while previous > 0 {
            previous -= 1;
            let line = lines[previous].trim();
            if line.is_empty() {
                continue;
            }
            if line.starts_with('@') {
                add_error(format!(
                    "function '{expected_function}' must not be decorated"
                ));
            }
            break;
        }
    }
}

fn collect_signature(lines: &[&str], start: usize) -> String {
    let mut result = String::new();
    let mut depth = 0i32;
    for line in &lines[start..] {
        if !result.is_empty() {
            result.push(' ');
        }
        result.push_str(line.trim());
        for character in line.chars() {
            match character {
                '(' | '[' | '{' => depth += 1,
                ')' | ']' | '}' => depth = (depth - 1).max(0),
                ':' if depth == 0 => return result,
                _ => {}
            }
        }
    }
    result
}

fn is_zero_argument_signature(signature: &str, expected_function: &str) -> bool {
    let Some(rest) = signature.strip_prefix("def ") else {
        return false;
    };
    let Some(open) = rest.find('(') else {
        return false;
    };
    let Some(close) = rest.rfind(')') else {
        return false;
    };
    if rest[..open].trim() != expected_function || !rest[open + 1..close].trim().is_empty() {
        return false;
    }
    let tail = rest[close + 1..].trim();
    let Some(annotation) = tail.strip_prefix("->") else {
        return false;
    };
    let Some(colon) = annotation.find(':') else {
        return false;
    };
    !annotation[..colon].trim().is_empty()
}

fn inspect_imports(
    source: &str,
    local_imports: &HashSet<String>,
    generated_type_modules: &HashSet<String>,
    add_error: &mut impl FnMut(String),
) {
    for line in source.lines() {
        let trimmed = line.trim_start();
        if let Some(rest) = trimmed.strip_prefix("import ") {
            for item in rest.split(',') {
                let module = item.split_whitespace().next().unwrap_or_default();
                inspect_import_target(
                    module,
                    rest,
                    local_imports,
                    generated_type_modules,
                    add_error,
                );
            }
        } else if let Some(rest) = trimmed.strip_prefix("from ") {
            let Some((module, imported)) = rest.split_once(" import ") else {
                continue;
            };
            let module = module.trim();
            inspect_import_target(
                module,
                imported,
                local_imports,
                generated_type_modules,
                add_error,
            );
            if imported.split_whitespace().any(|word| word == "*") {
                add_error(String::from("star imports are not allowed"));
            }
        }
    }
}

fn inspect_import_target(
    module: &str,
    imported: &str,
    local_imports: &HashSet<String>,
    generated_type_modules: &HashSet<String>,
    add_error: &mut impl FnMut(String),
) {
    if module.starts_with('.') {
        add_error(String::from("relative imports are not allowed"));
        return;
    }
    if module.is_empty() || module == "*" {
        add_error(String::from("dynamic imports are not allowed"));
        return;
    }
    if imported.split_whitespace().any(|word| word == "*") {
        add_error(String::from("star imports are not allowed"));
    }
    let root = module.split('.').next().unwrap_or(module);
    if generated_type_modules.contains(module)
        || root == "cott_runtime"
        || stdlib_modules().contains(root)
    {
        return;
    }
    if local_imports.contains(root) {
        add_error(format!("project-local import '{module}' is not allowed"));
    } else {
        add_error(format!(
            "external distribution import '{module}' is not allowed"
        ));
    }
}

fn stdlib_modules() -> HashSet<&'static str> {
    HashSet::from([
        "__future__",
        "abc",
        "array",
        "ast",
        "asyncio",
        "base64",
        "binascii",
        "bisect",
        "builtins",
        "calendar",
        "cmath",
        "codecs",
        "collections",
        "contextlib",
        "copy",
        "csv",
        "dataclasses",
        "datetime",
        "decimal",
        "enum",
        "errno",
        "faulthandler",
        "fnmatch",
        "fractions",
        "functools",
        "gc",
        "getopt",
        "glob",
        "gzip",
        "hashlib",
        "heapq",
        "hmac",
        "html",
        "http",
        "importlib",
        "inspect",
        "io",
        "itertools",
        "json",
        "keyword",
        "logging",
        "math",
        "numbers",
        "operator",
        "os",
        "pathlib",
        "pickle",
        "platform",
        "pprint",
        "random",
        "re",
        "secrets",
        "select",
        "shlex",
        "shutil",
        "signal",
        "site",
        "socket",
        "sqlite3",
        "ssl",
        "stat",
        "statistics",
        "string",
        "struct",
        "subprocess",
        "sys",
        "tempfile",
        "textwrap",
        "threading",
        "time",
        "timeit",
        "token",
        "traceback",
        "types",
        "typing",
        "unicodedata",
        "unittest",
        "urllib",
        "uuid",
        "warnings",
        "weakref",
        "xml",
        "zipfile",
    ])
}

fn identifier_tokens(source: &str) -> Vec<String> {
    let mut tokens = Vec::new();
    let mut current = String::new();
    for character in source.chars() {
        if character == '_' || character.is_ascii_alphanumeric() {
            current.push(character);
        } else if !current.is_empty() {
            tokens.push(std::mem::take(&mut current));
        }
    }
    if !current.is_empty() {
        tokens.push(current);
    }
    tokens
}

fn mask_python(source: &str) -> String {
    let input: Vec<char> = source.chars().collect();
    let mut output = input.clone();
    let mut index = 0;
    let mut quote = None;
    let mut triple = false;
    while index < input.len() {
        if quote.is_none() {
            if input[index] == '#' {
                while index < input.len() && input[index] != '\n' {
                    output[index] = ' ';
                    index += 1;
                }
                continue;
            }
            if input[index] == '\'' || input[index] == '"' {
                quote = Some(input[index]);
                triple = input.get(index + 1) == quote.as_ref()
                    && input.get(index + 2) == quote.as_ref();
                output[index] = ' ';
                if triple {
                    output[index + 1] = ' ';
                    output[index + 2] = ' ';
                    index += 3;
                } else {
                    index += 1;
                }
                continue;
            }
            index += 1;
            continue;
        }

        if input[index] == '\n' {
            if !triple {
                quote = None;
            }
            index += 1;
            continue;
        }
        if input[index] == '\\' && !triple {
            output[index] = ' ';
            if index + 1 < input.len() && input[index + 1] != '\n' {
                output[index + 1] = ' ';
                index += 2;
            } else {
                index += 1;
            }
            continue;
        }
        if input[index] == quote.unwrap() {
            if triple {
                if input.get(index + 1) == quote.as_ref() && input.get(index + 2) == quote.as_ref()
                {
                    output[index] = ' ';
                    output[index + 1] = ' ';
                    output[index + 2] = ' ';
                    index += 3;
                    quote = None;
                    triple = false;
                    continue;
                }
            } else {
                output[index] = ' ';
                index += 1;
                quote = None;
                continue;
            }
        }
        output[index] = ' ';
        index += 1;
    }
    output.into_iter().collect()
}
