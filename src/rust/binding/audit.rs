use super::*;
use tree_sitter::Node;

mod methods;
mod receiver;
mod task_scope;

pub(super) fn parse_rust(source: &str) -> Result<Tree, String> {
    let mut parser = Parser::new();
    parser
        .set_language(&tree_sitter_rust::LANGUAGE.into())
        .map_err(|e| e.to_string())?;
    let tree = parser
        .parse(source, None)
        .ok_or("unable to parse Rust source")?;
    if tree.root_node().has_error() {
        return Err("invalid Rust implementation syntax".into());
    }
    Ok(tree)
}
fn text<'a>(node: Node<'_>, source: &'a str) -> &'a str {
    &source[node.byte_range()]
}
fn children(node: Node<'_>) -> Vec<Node<'_>> {
    let mut c = node.walk();
    node.named_children(&mut c).collect()
}
fn walk(node: Node<'_>, f: &mut impl FnMut(Node<'_>) -> Result<(), String>) -> Result<(), String> {
    f(node)?;
    let mut cursor = node.walk();
    for child in node.children(&mut cursor) {
        walk(child, f)?;
    }
    Ok(())
}
fn tokens(node: Node<'_>, source: &str, output: &mut Vec<String>) {
    if node.kind().contains("comment") {
        return;
    }
    if node.child_count() == 0 {
        output.push(text(node, source).to_owned());
    } else {
        let mut c = node.walk();
        for n in node.children(&mut c) {
            tokens(n, source, output);
        }
    }
}
fn compact(node: Node<'_>, source: &str) -> String {
    let mut t = Vec::new();
    tokens(node, source, &mut t);
    t.concat()
}

/// Resolve declaration identity without conflating generic instantiation with
/// another callable spelling. Type arguments are still audited independently.
fn reference_path(node: Node<'_>, source: &str) -> Option<String> {
    match node.kind() {
        "generic_type" => reference_path(node.child_by_field_name("type")?, source),
        "generic_function" => reference_path(node.child_by_field_name("function")?, source),
        "bracketed_type" | "qualified_type" => None,
        "scoped_identifier" | "scoped_type_identifier" => {
            let name = node.child_by_field_name("name")?;
            let name = reference_path(name, source)?;
            match node.child_by_field_name("path") {
                Some(path) => Some(format!("{}::{name}", reference_path(path, source)?)),
                None => Some(name),
            }
        }
        _ => Some(compact(node, source)),
    }
}
fn function_name(node: Node<'_>, source: &str) -> Result<String, String> {
    node.child_by_field_name("name")
        .map(|n| text(n, source).to_owned())
        .ok_or_else(|| "Rust function has no name".into())
}
pub(super) fn index_source(tree: &Tree, source: &str) -> Result<SourceIndex, String> {
    Ok(SourceIndex {
        functions: children(tree.root_node())
            .into_iter()
            .filter(|n| n.kind() == "function_item")
            .map(|n| function_name(n, source))
            .collect::<Result<_, _>>()?,
    })
}
pub(super) fn rust_identifier(name: &str) -> String {
    if !name.is_empty() && name.bytes().all(|byte| byte == b'_') {
        return format!("{name}_");
    }
    if ["self", "Self", "super", "crate"].iter().any(|base| {
        name.strip_prefix(base)
            .is_some_and(|suffix| suffix.bytes().all(|b| b == b'_'))
    }) {
        return format!("{name}_");
    }
    if matches!(
        name,
        "as" | "async"
            | "await"
            | "break"
            | "const"
            | "continue"
            | "crate"
            | "dyn"
            | "else"
            | "enum"
            | "extern"
            | "false"
            | "fn"
            | "for"
            | "if"
            | "impl"
            | "in"
            | "let"
            | "loop"
            | "match"
            | "mod"
            | "move"
            | "mut"
            | "pub"
            | "ref"
            | "return"
            | "self"
            | "Self"
            | "static"
            | "struct"
            | "super"
            | "trait"
            | "true"
            | "type"
            | "unsafe"
            | "use"
            | "where"
            | "while"
            | "abstract"
            | "become"
            | "box"
            | "do"
            | "final"
            | "gen"
            | "macro"
            | "override"
            | "priv"
            | "try"
            | "typeof"
            | "unsized"
            | "virtual"
            | "yield"
    ) {
        format!("r#{name}")
    } else {
        name.into()
    }
}
pub(super) fn audit_private_access(root: Node<'_>, source: &str) -> Result<(), String> {
    walk(root, &mut |n| {
        if matches!(
            n.kind(),
            "identifier" | "type_identifier" | "field_identifier"
        ) {
            let name = text(n, source).trim_start_matches("r#");
            if name == "cott_impl" || name.starts_with("__cott") {
                return Err(format!("compiler-private reference `{name}` is forbidden"));
            }
        }
        if n.kind() == "super" {
            return Err("super:: escapes are forbidden".into());
        }
        Ok(())
    })
}
fn effects(declaration: &serde_json::Value) -> BTreeSet<String> {
    declaration
        .get("effects")
        .or_else(|| declaration.get("contract").and_then(|c| c.get("effects")))
        .and_then(serde_json::Value::as_array)
        .into_iter()
        .flatten()
        .filter_map(|e| {
            e.get("key")
                .and_then(serde_json::Value::as_str)
                .or_else(|| e.as_str())
        })
        .map(str::to_owned)
        .collect()
}
fn identities(value: &serde_json::Value, result: &mut BTreeSet<String>) {
    match value {
        serde_json::Value::Object(o) => {
            for k in ["name", "symbol", "target", "trait_method"] {
                if let Some(v) = o.get(k).and_then(serde_json::Value::as_str) {
                    result.insert(v.into());
                }
            }
            for v in o.values() {
                identities(v, result);
            }
        }
        serde_json::Value::Array(a) => {
            for v in a {
                identities(v, result);
            }
        }
        _ => (),
    }
}
fn imports(
    node: Node<'_>,
    source: &str,
    prefix: &str,
    result: &mut BTreeMap<String, String>,
) -> Result<(), String> {
    match node.kind() {
        "scoped_use_list" => {
            let path = node
                .child_by_field_name("path")
                .ok_or("import list has no path")?;
            let prefix = if prefix.is_empty() {
                compact(path, source)
            } else {
                format!("{prefix}::{}", compact(path, source))
            };
            let list = node
                .child_by_field_name("list")
                .ok_or("import list missing")?;
            for child in children(list) {
                imports(child, source, &prefix, result)?;
            }
        }
        "use_list" => {
            for child in children(node) {
                imports(child, source, prefix, result)?;
            }
        }
        "use_as_clause" => {
            let path = node
                .child_by_field_name("path")
                .ok_or("import alias missing path")?;
            let alias = node
                .child_by_field_name("alias")
                .ok_or("import alias missing name")?;
            insert_import(prefix, &compact(path, source), text(alias, source), result)?;
        }
        "use_wildcard" => return Err("wildcard imports are forbidden".into()),
        _ => {
            let path = compact(node, source);
            let alias = if path == "self" && !prefix.is_empty() {
                prefix.rsplit("::").next().unwrap_or(prefix)
            } else {
                path.rsplit("::").next().unwrap_or(&path)
            };
            insert_import(prefix, &path, alias, result)?;
        }
    }
    Ok(())
}
fn insert_import(
    prefix: &str,
    path: &str,
    alias: &str,
    result: &mut BTreeMap<String, String>,
) -> Result<(), String> {
    let prefix = prefix.trim_start_matches("::");
    let path = path.trim_start_matches("::");
    let full = if prefix.is_empty() {
        path.into()
    } else if path == "self" {
        prefix.into()
    } else {
        format!("{prefix}::{path}")
    };
    if matches!(alias, "std" | "core" | "alloc" | "crate") {
        return Err(format!(
            "import alias `{alias}` shadows intrinsic namespace authority"
        ));
    }
    if result.insert(alias.into(), full).is_some() {
        return Err(format!("duplicate import alias `{alias}`"));
    }
    Ok(())
}
fn resolve(path: &str, aliases: &BTreeMap<String, String>) -> String {
    let path = path.trim_start_matches("::");
    let (first, rest) = path.split_once("::").unwrap_or((path, ""));
    aliases
        .get(first)
        .map(|base| {
            if rest.is_empty() {
                base.clone()
            } else {
                format!("{base}::{rest}")
            }
        })
        .unwrap_or_else(|| path.to_owned())
}
fn check_path(
    path: &str,
    allowed: &BTreeSet<String>,
    effects: &BTreeSet<String>,
) -> Result<(), String> {
    let mut parts = path.trim_start_matches("::").split("::");
    let first = parts.next().unwrap_or("");
    let module = parts.next().unwrap_or("");
    if matches!(first, "std" | "core" | "alloc") {
        let safe = matches!(
            module,
            "borrow"
                | "boxed"
                | "cell"
                | "char"
                | "clone"
                | "cmp"
                | "collections"
                | "convert"
                | "default"
                | "error"
                | "fmt"
                | "hash"
                | "iter"
                | "marker"
                | "mem"
                | "num"
                | "ops"
                | "option"
                | "primitive"
                | "rc"
                | "result"
                | "slice"
                | "str"
                | "string"
                | "vec"
                | "path"
                | "time"
                | "f32"
                | "f64"
                | "i8"
                | "i16"
                | "i32"
                | "i64"
                | "u8"
                | "u16"
                | "u32"
                | "u64"
                | "usize"
                | "isize"
        );
        let safe_sync = module == "sync"
            && matches!(
                parts.next(),
                None | Some(
                    "Arc"
                        | "Weak"
                        | "Mutex"
                        | "MutexGuard"
                        | "RwLock"
                        | "RwLockReadGuard"
                        | "RwLockWriteGuard"
                        | "PoisonError"
                        | "LockResult"
                        | "TryLockError"
                        | "TryLockResult"
                        | "atomic"
                )
            );
        let covered = match module {
            "fs" => effects.contains("file.read") || effects.contains("file.write"),
            "io" => {
                effects.contains("file.read")
                    || effects.contains("file.write")
                    || effects.contains("network")
            }
            "net" => effects.contains("network"),
            "random" => effects.contains("random"),
            _ => false,
        };
        if !safe && !safe_sync && !covered {
            return Err(format!(
                "forbidden or effect-uncovered standard API `{path}`"
            ));
        }
    } else if first != "crate" && !allowed.contains(first) {
        return Err(format!(
            "import outside frozen production authority `{path}`"
        ));
    } else if first == "crate" && !matches!(module, "modules" | "cott_runtime") {
        return Err(format!("private crate path `{path}` is forbidden"));
    }
    Ok(())
}

pub(super) fn audit_source(
    plan: &RustPlan,
    callable: &RustCallable,
    allowed: &BTreeSet<String>,
    source: &str,
    tree: &Tree,
    signature: &str,
    target: &str,
    selected_context: Option<&serde_json::Value>,
) -> Result<(), String> {
    let root = tree.root_node();
    audit_private_access(root, source)?;
    let expected_tree = parse_rust(&format!("{signature} {{}}"))?;
    let expected = children(expected_tree.root_node())
        .into_iter()
        .find(|n| n.kind() == "function_item")
        .ok_or("canonical signature is not a function")?;
    let expected_name = function_name(expected, &format!("{signature} {{}}"))?;
    let expected_source = format!("{signature} {{}}");
    let header = |n: Node<'_>, s: &str| -> Result<Vec<String>, String> {
        let body = n
            .child_by_field_name("body")
            .ok_or("function must have a body")?;
        let mut result = Vec::new();
        let mut c = n.walk();
        for child in n.children(&mut c) {
            if child.id() == body.id() {
                break;
            }
            if Some(child.id()) == n.child_by_field_name("name").map(|n| n.id()) {
                result.push("<canonical-name>".into());
            } else {
                tokens(child, s, &mut result);
            }
        }
        Ok(result)
    };
    let mut aliases = BTreeMap::new();
    let mut count = 0;
    for item in children(root) {
        match item.kind() {
            "line_comment" | "block_comment" | "attribute_item" => (),
            "use_declaration" => imports(
                item.child_by_field_name("argument")
                    .ok_or("use declaration missing path")?,
                source,
                "",
                &mut aliases,
            )?,
            "function_item" => {
                let name = function_name(item, source)?;
                if name == target {
                    count += 1;
                    if header(item, source)? != header(expected, &expected_source)? {
                        return Err(format!(
                            "canonical Rust signature mismatch for `{}`; expected {signature}",
                            callable.symbol
                        ));
                    }
                } else if children(item)
                    .iter()
                    .any(|n| n.kind() == "visibility_modifier")
                {
                    return Err("public helpers are forbidden".into());
                }
            }
            _ => {
                return Err(format!(
                    "unsupported top-level Rust item `{}`; only canonical function, private helpers and imports are allowed",
                    item.kind()
                ));
            }
        }
    }
    if count != 1 {
        return Err(format!(
            "expected exactly one canonical function `{target}` (ABI name `{expected_name}`), found {count}"
        ));
    }
    let declared_effects = effects(&callable.declaration);
    let mutable_fields: BTreeSet<_> = callable
        .declaration
        .get("modifies")
        .and_then(serde_json::Value::as_array)
        .into_iter()
        .flatten()
        .filter_map(serde_json::Value::as_str)
        .chain(
            callable
                .declaration
                .get("transitions")
                .and_then(serde_json::Value::as_array)
                .into_iter()
                .flatten()
                .filter_map(|t| t.get("field").and_then(serde_json::Value::as_str)),
        )
        .filter_map(|field| field.rsplit('.').next())
        .collect();
    let owned_context;
    let context = match selected_context {
        Some(context) => context,
        None => {
            owned_context = intent::context(plan.contract_surface(), &callable.symbol, &[])?;
            &owned_context
        }
    };
    if context.get("symbol").and_then(serde_json::Value::as_str) != Some(callable.symbol.as_str()) {
        return Err("Rust audit context does not match canonical callable".into());
    }
    let mut selected = BTreeSet::new();
    identities(context, &mut selected);
    let callable_paths: BTreeMap<_, _> = plan
        .callables()
        .iter()
        .map(|c| {
            (
                format!(
                    "crate::modules::{}",
                    c.symbol
                        .split('.')
                        .map(rust_identifier)
                        .collect::<Vec<_>>()
                        .join("::")
                ),
                c,
            )
        })
        .collect();
    let method_index = methods::MethodIndex::new(plan, context, &selected);
    let mut allowed_reserved = BTreeSet::new();
    walk(expected, &mut |n| {
        if n.kind() == "identifier" {
            allowed_reserved.insert(text(n, &expected_source).to_owned());
        }
        Ok(())
    })?;
    let mut local_types: BTreeSet<String> = [
        "Self", "Option", "Result", "Vec", "String", "Box", "i8", "i16", "i32", "i64", "i128",
        "u8", "u16", "u32", "u64", "u128", "usize", "isize", "f32", "f64", "bool", "char",
    ]
    .into_iter()
    .map(str::to_owned)
    .collect();
    walk(expected, &mut |n| {
        if n.kind() == "type_identifier" {
            local_types.insert(text(n, &expected_source).to_owned());
        }
        Ok(())
    })?;
    for id in &selected {
        if let Some(last) = id.rsplit('.').next() {
            local_types.insert(rust_identifier(last));
        }
    }
    let selected_paths: BTreeSet<_> = selected
        .iter()
        .filter(|id| id.contains('.'))
        .map(|id| {
            format!(
                "crate::modules::{}",
                id.split('.')
                    .map(rust_identifier)
                    .collect::<Vec<_>>()
                    .join("::")
            )
        })
        .collect();
    // Authored value/function binding names are not standard-library capabilities.
    // Keep this distinction lexical; qualified paths and member names still receive the API audit.
    let mut value_bindings = BTreeSet::new();
    walk(root, &mut |node| {
        let binding = match node.kind() {
            "function_item" => node.child_by_field_name("name"),
            "parameter" | "let_declaration" => node.child_by_field_name("pattern"),
            _ => None,
        };
        if let Some(binding) = binding {
            walk(binding, &mut |identifier| {
                if identifier.kind() == "identifier" {
                    value_bindings.insert(text(identifier, source).to_owned());
                }
                Ok(())
            })?;
        }
        Ok(())
    })?;
    let context_path = |path: &str| {
        !path.starts_with("crate::modules::")
            || selected_paths.iter().any(|id| {
                id == path
                    || id
                        .strip_prefix(path)
                        .is_some_and(|rest| rest.starts_with("::"))
                    || path
                        .strip_prefix(id)
                        .is_some_and(|rest| rest.starts_with("::"))
            })
    };
    for (alias, path) in &aliases {
        check_path(path, allowed, &declared_effects)?;
        if callable_paths.contains_key(path) || method_index.paths.contains_key(path) {
            return Err(format!(
                "Cott callable import/alias `{alias}` is forbidden; call its full facade path"
            ));
        }
        if !context_path(path) {
            return Err(format!(
                "facade import `{path}` is outside selected context"
            ));
        }
    }
    if callable.owner.is_some() {
        // Receiver handles retain identity even when their declared fields are mutable.
        // Runtime post-call identity checks are defense in depth, not source authority.
        receiver::audit(root, source, &aliases)?;
    }
    walk(root, &mut |n| {
        let raw = text(n, source);
        match n.kind() {
            "unsafe_block"
            | "extern_modifier"
            | "foreign_mod_item"
            | "macro_definition"
            | "mod_item"
            | "static_item"
            | "struct_item"
            | "enum_item"
            | "union_item"
            | "type_item"
            | "trait_item"
            | "impl_item"
            | "inner_attribute_item" => {
                return Err(format!("forbidden Rust syntax `{}`", n.kind()));
            }
            "use_declaration" if n.parent().map(|parent| parent.kind()) != Some("source_file") => {
                return Err("authored imports must be top-level so their authority cannot be scope-shadowed".into());
            }
            "type_parameter" => {
                if let Some(name) = n.child_by_field_name("name") {
                    if aliases.contains_key(text(name, source)) {
                        return Err("generic parameter shadows imported type authority".into());
                    }
                }
            }
            "attribute_item" => {
                let attr = compact(n, source);
                if !attr.starts_with("#[doc=") {
                    return Err(format!(
                        "compilation-changing or unapproved attribute `{attr}`"
                    ));
                }
            }
            "visibility_modifier" => {
                let owner = n.parent().ok_or("visibility has no owner")?;
                if owner.kind() != "function_item"
                    || function_name(owner, source)? != target
                    || owner.parent().map(|n| n.kind()) != Some("source_file")
                    || compact(n, source) != "pub(crate)"
                {
                    return Err("only canonical pub(crate) visibility is allowed".into());
                }
            }
            "macro_invocation" => {
                let name = n
                    .child_by_field_name("macro")
                    .map(|n| compact(n, source))
                    .unwrap_or_default();
                if !matches!(name.as_str(), "vec" | "format" | "matches")
                    || aliases.contains_key(&name)
                {
                    return Err(format!("unauditable or forbidden Rust macro `{name}!`"));
                }
                // Token trees have no expression AST: reject qualified paths and nested macro expansion,
                // but do not confuse punctuation inside comments and literal contents with code.
                for arguments in children(n).into_iter().filter(|n| n.kind() == "token_tree") {
                    walk(arguments, &mut |token| {
                        if matches!(token.kind(), "::" | "!") {
                            return Err("qualified paths and nested macros in macro token trees are forbidden".into());
                        }
                        Ok(())
                    })?;
                }
            }
            "identifier" | "type_identifier" | "field_identifier" => {
                let name = raw.trim_start_matches("r#");
                if (name.starts_with("cott_") || name.starts_with("__cott"))
                    && name != "cott_runtime"
                    && !allowed_reserved.contains(raw)
                {
                    return Err(format!("compiler-private identifier `{name}` is forbidden"));
                }
                if n.parent().is_some_and(|parent| {
                    matches!(
                        parent.kind(),
                        "scoped_identifier" | "scoped_type_identifier"
                    ) && resolve(&compact(parent, source), &aliases).starts_with("crate::modules::")
                }) {
                    // Nominal declaration identity is checked on the complete path, not its leaf spelling.
                    return Ok(());
                }
                if let Some(authority) = method_index.member_effects(n, source, &aliases) {
                    if !authority.is_subset(&declared_effects) {
                        return Err(format!("Cott method `{raw}` has uncovered effects"));
                    }
                    let mut call = n.parent().and_then(|member| member.parent());
                    if call.is_some_and(|node| node.kind() == "generic_function") {
                        call = call.and_then(|node| node.parent());
                    }
                    if !call.is_some_and(|node| node.kind() == "call_expression") {
                        return Err("Cott methods cannot be aliased or passed as values".into());
                    }
                    return Ok(());
                }
                if value_bindings.contains(raw)
                    && !n.parent().is_some_and(|parent| {
                        matches!(
                            parent.kind(),
                            "scoped_identifier"
                                | "scoped_type_identifier"
                                | "field_expression"
                                | "use_as_clause"
                        )
                    })
                {
                    return Ok(());
                }
                if name == "spawn"
                    && !(signature.contains("async fn")
                        && task_scope::authorized_spawn(n, source, &aliases))
                {
                    return Err("spawn requires a lexically proven TaskScope receiver in a declared async callable".into());
                }
                if matches!(
                    name,
                    "stdin"
                        | "stdout"
                        | "stderr"
                        | "print"
                        | "println"
                        | "eprint"
                        | "eprintln"
                        | "process"
                        | "env"
                        | "exit"
                        | "abort"
                        | "set_hook"
                        | "take_hook"
                        | "catch_unwind"
                        | "panic_any"
                        | "resume_unwind"
                        | "Command"
                        | "Stdio"
                        | "thread"
                        | "block_on"
                        | "spawn_blocking"
                        | "spawn_local"
                        | "spawn_on"
                        | "spawn_blocking_on"
                        | "block_in_place"
                        | "kill"
                        | "kill_pid"
                        | "set_current_dir"
                        | "set_var"
                        | "remove_var"
                        | "System"
                        | "GlobalAlloc"
                        | "ContractViolation"
                        | "StateGate"
                        | "StateLease"
                        | "Fixture"
                        | "PredicateObservation"
                ) {
                    return Err(format!(
                        "process/environment/stdio/control API `{name}` is forbidden"
                    ));
                }
                if matches!(name, "now" | "elapsed") && !declared_effects.contains("clock") {
                    return Err(format!("clock API `{name}` requires declared clock effect"));
                }
                if name == "random" && !declared_effects.contains("random") {
                    return Err("random API requires declared random effect".into());
                }
                if matches!(
                    name,
                    "read"
                        | "read_to_string"
                        | "read_to_end"
                        | "read_dir"
                        | "metadata"
                        | "open"
                        | "canonicalize"
                        | "read_link"
                        | "try_exists"
                        | "modified"
                        | "accessed"
                        | "exists"
                        | "is_file"
                        | "is_dir"
                ) && !declared_effects.contains("file.read")
                    && !declared_effects.contains("network")
                {
                    return Err(format!("read API `{name}` requires declared effect"));
                }
                if matches!(
                    name,
                    "write"
                        | "write_all"
                        | "create"
                        | "create_new"
                        | "create_dir"
                        | "create_dir_all"
                        | "remove_file"
                        | "remove_dir"
                        | "remove_dir_all"
                        | "rename"
                        | "copy"
                        | "hard_link"
                        | "symlink"
                        | "set_permissions"
                        | "set_len"
                        | "set_times"
                        | "truncate"
                        | "append"
                        | "sync_all"
                        | "sync_data"
                ) && !declared_effects.contains("file.write")
                    && !declared_effects.contains("network")
                {
                    return Err(format!("write API `{name}` requires declared effect"));
                }
                if let Some(field) = name
                    .strip_prefix("set_")
                    .or_else(|| name.strip_prefix("update_"))
                    && !mutable_fields.contains(field)
                    && callable.owner.is_some()
                    && n.parent().is_some_and(|member| {
                        member.kind() == "field_expression"
                            && member
                                .child_by_field_name("value")
                                .is_some_and(|receiver| compact(receiver, source) == "receiver")
                    })
                {
                    return Err(format!(
                        "state setter `{name}` is not covered by declared modifies/transitions"
                    ));
                }
            }
            "scoped_identifier" | "scoped_type_identifier" => {
                let Some(reference) = reference_path(n, source) else {
                    if n.kind() == "scoped_type_identifier" {
                        return Ok(());
                    }
                    return Err("trait-qualified callable paths are unauditable; use the direct scoped facade path".into());
                };
                let path = resolve(&reference, &aliases);
                let first = path
                    .trim_start_matches("::")
                    .split("::")
                    .next()
                    .unwrap_or("");
                if !local_types.contains(first) {
                    check_path(&path, allowed, &declared_effects)?;
                }
                if !context_path(&path) {
                    return Err(format!(
                        "facade reference `{path}` is outside selected context"
                    ));
                }
                if path.ends_with("::ReadField::new") {
                    return Err("ReadField constructors are compiler-private".into());
                }
                if path.starts_with("crate::modules::") && !callable_paths.contains_key(&path) {
                    let leaf = path.rsplit("::").next().unwrap_or("");
                    if let Some(field) = leaf
                        .strip_prefix("set_")
                        .or_else(|| leaf.strip_prefix("update_"))
                        && !mutable_fields.contains(field)
                    {
                        return Err(format!(
                            "state setter `{path}` is not covered by declared modifies/transitions"
                        ));
                    }
                }
                if let Some(authority) = method_index.paths.get(&path) {
                    if !authority.is_subset(&declared_effects) {
                        return Err(format!(
                            "Cott trait call `{path}` has uncovered concrete/default effects"
                        ));
                    }
                    let mut call = n.parent();
                    if call.is_some_and(|node| node.kind() == "generic_function") {
                        call = call.and_then(|node| node.parent());
                    }
                    if !call.is_some_and(|node| {
                        node.kind() == "call_expression"
                            && node
                                .child_by_field_name("function")
                                .is_some_and(|function| {
                                    function.byte_range().contains(&n.start_byte())
                                })
                    }) {
                        return Err(
                            "Cott trait methods cannot be aliased or passed as values".into()
                        );
                    }
                }
                if let Some(callee) = callable_paths.get(&path) {
                    if !selected.contains(&callee.symbol) {
                        return Err(format!(
                            "Cott callable `{}` is outside selected context",
                            callee.symbol
                        ));
                    }
                    if !effects(&callee.declaration).is_subset(&declared_effects) {
                        return Err(format!(
                            "Cott call `{}` has uncovered effects",
                            callee.symbol
                        ));
                    }
                    let mut p = n.parent();
                    if p.is_some_and(|n| n.kind() == "generic_function") {
                        p = p.and_then(|n| n.parent());
                    }
                    if !p.is_some_and(|p| {
                        p.kind() == "call_expression"
                            && p.child_by_field_name("function")
                                .is_some_and(|f| f.byte_range().contains(&n.start_byte()))
                    }) {
                        return Err("Cott callables cannot be aliased or passed as values".into());
                    }
                }
            }
            _ => (),
        }
        // unsafe/extern tokens in function modifiers and macro token trees are leaves.
        if matches!(n.kind(), "unsafe" | "extern") {
            return Err(format!("forbidden Rust token `{raw}`"));
        }
        if n.kind() == "async" && !signature.contains("async fn") {
            return Err("async helpers require a declared async callable".into());
        }
        Ok(())
    })
}

pub(super) fn partition(bytes: &[u8]) -> Result<ParsedImplementation, String> {
    let source = std::str::from_utf8(bytes).map_err(|_| "Rust implementation is not UTF-8")?;
    let tree = parse_rust(source)?;
    let mut imports = Vec::new();
    let mut body = String::new();
    let mut offset = 0;
    for item in children(tree.root_node()) {
        match item.kind() {
            "use_declaration" => {
                body.push_str(&source[offset..item.start_byte()]);
                imports.push(text(item, source).into());
                offset = item.end_byte();
            }
            "function_item" | "line_comment" | "block_comment" => {}
            "attribute_item" if compact(item, source).starts_with("#[doc=") => {}
            _ => return Err(format!("unsupported authored Rust item `{}`", item.kind())),
        }
    }
    body.push_str(&source[offset..]);
    Ok(ParsedImplementation { imports, body })
}
