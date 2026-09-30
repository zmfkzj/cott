use super::*;

const TYPE: &str = "crate::cott_runtime::TaskScope";

fn scope_type(node: Node<'_>, source: &str, aliases: &BTreeMap<String, String>) -> bool {
    if node.kind() == "reference_type" {
        return node
            .child_by_field_name("type")
            .is_some_and(|n| scope_type(n, source, aliases));
    }
    resolve(&compact(node, source), aliases) == TYPE
}
fn pattern_binds(pattern: Node<'_>, name: &str, source: &str) -> bool {
    if pattern.kind() == "identifier" && text(pattern, source) == name {
        return true;
    }
    children(pattern)
        .into_iter()
        .any(|n| pattern_binds(n, name, source))
}
fn declaration_scope(node: Node<'_>, source: &str, aliases: &BTreeMap<String, String>) -> bool {
    node.child_by_field_name("type")
        .is_some_and(|n| scope_type(n, source, aliases))
        || node
            .child_by_field_name("value")
            .is_some_and(|n| constructor(n, source, aliases))
}
fn constructor(node: Node<'_>, source: &str, aliases: &BTreeMap<String, String>) -> bool {
    node.kind() == "call_expression"
        && node.child_by_field_name("function").is_some_and(|n| {
            resolve(&compact(n, source), aliases) == "crate::cott_runtime::TaskScope::new"
        })
}
pub(super) fn binding_declaration<'tree>(
    identifier: Node<'tree>,
    source: &str,
) -> Option<Node<'tree>> {
    let name = text(identifier, source);
    let mut ancestor = identifier.parent();
    while let Some(node) = ancestor {
        match node.kind() {
            "block" => {
                let declaration = children(node)
                    .into_iter()
                    .filter(|child| {
                        child.kind() == "let_declaration"
                            && child.end_byte() <= identifier.start_byte()
                    })
                    .filter(|child| {
                        child
                            .child_by_field_name("pattern")
                            .is_some_and(|pattern| pattern_binds(pattern, name, source))
                    })
                    .next_back();
                if let Some(declaration) = declaration {
                    return Some(declaration);
                }
            }
            "function_item" | "closure_expression" => {
                if let Some(parameters) = node.child_by_field_name("parameters") {
                    for parameter in children(parameters) {
                        let pattern = parameter
                            .child_by_field_name("pattern")
                            .unwrap_or(parameter);
                        if pattern_binds(pattern, name, source) {
                            return Some(parameter);
                        }
                    }
                }
            }
            "for_expression" | "match_arm" | "let_condition" => {
                if node
                    .child_by_field_name("pattern")
                    .is_some_and(|pattern| pattern_binds(pattern, name, source))
                {
                    return None;
                }
            }
            _ => {}
        }
        ancestor = node.parent();
    }
    None
}
fn expression_scope(node: Node<'_>, source: &str, aliases: &BTreeMap<String, String>) -> bool {
    match node.kind() {
        "identifier" => binding_declaration(node, source)
            .is_some_and(|declaration| declaration_scope(declaration, source, aliases)),
        "reference_expression" => node
            .child_by_field_name("value")
            .is_some_and(|n| expression_scope(n, source, aliases)),
        "parenthesized_expression" => children(node)
            .first()
            .is_some_and(|n| expression_scope(*n, source, aliases)),
        _ => constructor(node, source, aliases),
    }
}

/// A spelling such as `spawn` conveys no authority. Only an actual, lexically
/// unshadowed TaskScope receiver can authorize the runtime's tracked operation.
pub(super) fn authorized_spawn(
    identifier: Node<'_>,
    source: &str,
    aliases: &BTreeMap<String, String>,
) -> bool {
    let Some(parent) = identifier.parent() else {
        return false;
    };
    match parent.kind() {
        "field_expression" => parent
            .child_by_field_name("value")
            .is_some_and(|receiver| expression_scope(receiver, source, aliases)),
        "scoped_identifier"
            if resolve(&compact(parent, source), aliases)
                == "crate::cott_runtime::TaskScope::spawn" =>
        {
            let Some(call) = parent
                .parent()
                .filter(|node| node.kind() == "call_expression")
            else {
                return false;
            };
            call.child_by_field_name("arguments")
                .and_then(|args| children(args).first().copied())
                .is_some_and(|receiver| expression_scope(receiver, source, aliases))
        }
        _ => false,
    }
}
