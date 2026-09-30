use super::*;

/// Mutable implementation receivers are identity handles, not replaceable values.
/// Follow explicit mutable reborrows so a local alias cannot evade this boundary.
pub(super) fn audit(
    root: Node<'_>,
    source: &str,
    aliases: &BTreeMap<String, String>,
) -> Result<(), String> {
    let mut receivers = BTreeSet::from(["receiver".to_owned()]);
    let mut functions = BTreeMap::<&str, Vec<Node<'_>>>::new();
    collect_functions(root, source, &mut functions);
    loop {
        let before = receivers.len();
        walk(root, &mut |node| {
            if node.kind() == "let_declaration" {
                if let (Some(pattern), Some(value)) = (
                    node.child_by_field_name("pattern"),
                    node.child_by_field_name("value"),
                ) {
                    if touches(value, source, &receivers) && mutable_alias(value, source) {
                        walk(pattern, &mut |name| {
                            if name.kind() == "identifier" {
                                receivers.insert(text(name, source).to_owned());
                            }
                            Ok(())
                        })?;
                    }
                }
            }
            if node.kind() == "call_expression" {
                if let (Some(function), Some(arguments)) = (
                    node.child_by_field_name("function"),
                    node.child_by_field_name("arguments"),
                ) {
                    if let Some(path) = reference_path(function, source) {
                        if let Some(callees) = functions.get(path.as_str()) {
                            for callee in callees {
                                if let Some(parameters) = callee.child_by_field_name("parameters") {
                                    for (argument, parameter) in
                                        children(arguments).into_iter().zip(children(parameters))
                                    {
                                        if touches(argument, source, &receivers)
                                            && mutable_alias(argument, source)
                                        {
                                            if let Some(pattern) =
                                                parameter.child_by_field_name("pattern")
                                            {
                                                walk(pattern, &mut |name| {
                                                    if name.kind() == "identifier" {
                                                        receivers
                                                            .insert(text(name, source).to_owned());
                                                    }
                                                    Ok(())
                                                })?;
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
            Ok(())
        })?;
        if before == receivers.len() {
            break;
        }
    }
    walk(root, &mut |node| {
        match node.kind() {
            "scoped_identifier" | "identifier" => {
                if let Some(path) = reference_path(node, source).map(|path| resolve(&path, aliases))
                {
                    if [
                        "std::mem::replace",
                        "std::mem::take",
                        "std::mem::swap",
                        "core::mem::replace",
                        "core::mem::take",
                        "core::mem::swap",
                    ]
                    .contains(&path.as_str())
                    {
                        let mut parent = node.parent();
                        if parent.is_some_and(|p| p.kind() == "generic_function") {
                            parent = parent.and_then(|p| p.parent());
                        }
                        let direct_call = parent.is_some_and(|p| {
                            p.kind() == "call_expression"
                                && p.child_by_field_name("function")
                                    .is_some_and(|f| f.byte_range().contains(&node.start_byte()))
                        });
                        let mut ancestor = node.parent();
                        let mut import = false;
                        while let Some(p) = ancestor {
                            if p.kind() == "use_declaration" {
                                import = true;
                                break;
                            }
                            if matches!(p.kind(), "function_item" | "block" | "source_file") {
                                break;
                            }
                            ancestor = p.parent();
                        }
                        if !direct_call && !import {
                            return Err("identity-changing mem functions cannot be aliased or passed as values in an implementation method".into());
                        }
                    }
                }
            }
            "assignment_expression" | "compound_assignment_expr" => {
                if node
                    .child_by_field_name("left")
                    .is_some_and(|left| touches(left, source, &receivers))
                {
                    return Err("implementation receiver identity and stored fields cannot be assigned directly; use declared guarded setters/update".into());
                }
            }
            "call_expression" => {
                if let Some(function) = node.child_by_field_name("function") {
                    let path = reference_path(function, source)
                        .map(|path| resolve(&path, aliases))
                        .unwrap_or_default();
                    let replacement = [
                        "std::mem::replace",
                        "std::mem::take",
                        "std::mem::swap",
                        "core::mem::replace",
                        "core::mem::take",
                        "core::mem::swap",
                    ]
                    .contains(&path.as_str());
                    if replacement
                        && node
                            .child_by_field_name("arguments")
                            .is_some_and(|args| touches(args, source, &receivers))
                    {
                        return Err("mem::replace/take/swap cannot replace or move an implementation receiver or its stored fields".into());
                    }
                    if function.kind() == "field_expression" {
                        if let (Some(value), Some(field)) = (
                            function.child_by_field_name("value"),
                            function.child_by_field_name("field"),
                        ) {
                            if matches!(
                                text(field, source),
                                "take" | "replace" | "swap" | "take_if"
                            ) && touches(value, source, &receivers)
                            {
                                return Err("receiver-field take/replace/swap bypasses declared guarded setters/update".into());
                            }
                        }
                    } else if path.starts_with("Option::")
                        || path.starts_with("std::option::Option::")
                        || path.starts_with("core::option::Option::")
                    {
                        if matches!(
                            path.rsplit("::").next(),
                            Some("take" | "replace" | "take_if")
                        ) && node
                            .child_by_field_name("arguments")
                            .is_some_and(|args| touches(args, source, &receivers))
                        {
                            return Err(
                                "Option field moves cannot bypass receiver guarded setters/update"
                                    .into(),
                            );
                        }
                    }
                }
            }
            _ => {}
        }
        Ok(())
    })
}

fn collect_functions<'tree, 'source>(
    node: Node<'tree>,
    source: &'source str,
    functions: &mut BTreeMap<&'source str, Vec<Node<'tree>>>,
) {
    if node.kind() == "function_item" {
        if let Some(name) = node.child_by_field_name("name") {
            functions.entry(text(name, source)).or_default().push(node);
        }
    }
    for child in children(node) {
        collect_functions(child, source, functions);
    }
}
fn mutable_alias(node: Node<'_>, source: &str) -> bool {
    match node.kind() {
        "identifier" | "field_expression" | "unary_expression" => true,
        "parenthesized_expression" => children(node)
            .first()
            .is_some_and(|child| mutable_alias(*child, source)),
        "reference_expression" => {
            compact(node, source).starts_with("&mut")
                && node
                    .child_by_field_name("value")
                    .is_some_and(|value| mutable_alias(value, source))
        }
        _ => false,
    }
}
fn touches(node: Node<'_>, source: &str, receivers: &BTreeSet<String>) -> bool {
    if node.kind() == "identifier" && receivers.contains(text(node, source)) {
        return true;
    }
    children(node)
        .into_iter()
        .any(|child| touches(child, source, receivers))
}

#[cfg(test)]
mod tests {
    use super::*;
    fn check(body: &str, imports: &BTreeMap<String, String>) -> Result<(), String> {
        let source = format!("fn run(receiver: &mut Owner) {{ {body} }}");
        let tree = parse_rust(&source).unwrap();
        audit(tree.root_node(), &source, imports)
    }
    #[test]
    fn receiver_identity_cannot_be_replaced_through_assignments_reborrows_or_mem_aliases() {
        let imports = BTreeMap::from([
            ("replace".into(), "std::mem::replace".into()),
            ("memory".into(), "core::mem".into()),
        ]);
        for body in [
            "*receiver = Owner::new();",
            "std::mem::replace(receiver, Owner::new());",
            "core::mem::take(&mut *receiver);",
            "std::mem::swap(&mut other, receiver);",
            "replace(receiver, Owner::new());",
            "memory::take(receiver);",
            "let alias = &mut *receiver; *alias = Owner::new();",
            "let alias = receiver; let next = &mut *alias; std::mem::swap(next, &mut other);",
        ] {
            assert!(check(body, &imports).is_err(), "accepted {body}");
        }
    }
    #[test]
    fn guarded_updates_remain_allowed_but_raw_field_moves_are_rejected() {
        for body in [
            "receiver.set_value(1);",
            "receiver.update_value(|value| { *value += 1; });",
            "let value = *receiver.get_value();",
            "std::mem::replace(&mut local, 1);",
            "let cloned = receiver.clone(); cloned.set_value(1);",
        ] {
            check(body, &BTreeMap::new()).unwrap();
        }
        for body in [
            "receiver.value.take();",
            "receiver.value.replace(other);",
            "Option::take(&mut receiver.value);",
            "std::option::Option::replace(&mut receiver.value, other);",
            "let field = &mut receiver.value; field.take();",
            "receiver.value = other;",
        ] {
            assert!(check(body, &BTreeMap::new()).is_err(), "accepted {body}");
        }
    }
    #[test]
    fn helper_parameters_and_function_pointer_aliases_cannot_hide_replacement() {
        let source = "fn run(receiver: &mut Owner) { helper(&mut *receiver); } fn helper(target: &mut Owner) { *target = Owner::new(); }";
        assert!(
            audit(
                parse_rust(source).unwrap().root_node(),
                source,
                &BTreeMap::new()
            )
            .is_err()
        );
        assert!(
            check(
                "fn helper(target: &mut Owner) { std::mem::take(target); } helper(receiver);",
                &BTreeMap::new()
            )
            .is_err()
        );
        assert!(
            check(
                "let swap = core::mem::swap; swap(receiver, &mut other);",
                &BTreeMap::new()
            )
            .is_err()
        );
        let safe = "fn run(receiver: &mut Owner) { helper(receiver); } fn helper(target: &mut Owner) { target.set_value(1); }";
        audit(
            parse_rust(safe).unwrap().root_node(),
            safe,
            &BTreeMap::new(),
        )
        .unwrap();
    }
}
