use super::*;

type MethodEffects = BTreeMap<String, BTreeSet<String>>;

#[derive(Default)]
pub(super) struct MethodIndex {
    pub paths: BTreeMap<String, BTreeSet<String>>,
    types: BTreeMap<String, MethodEffects>,
    traits: BTreeSet<String>,
    dynamic: MethodEffects,
}
fn rust_path(symbol: &str) -> String {
    format!(
        "crate::modules::{}",
        symbol
            .split('.')
            .map(rust_identifier)
            .collect::<Vec<_>>()
            .join("::")
    )
}
fn merge(target: &mut MethodEffects, name: &str, source: &BTreeSet<String>) {
    target
        .entry(name.to_owned())
        .or_default()
        .extend(source.iter().cloned());
}
impl MethodIndex {
    pub fn new(plan: &RustPlan, context: &serde_json::Value, selected: &BTreeSet<String>) -> Self {
        let mut result = Self::default();
        let functions: BTreeMap<_, _> = plan
            .callables()
            .iter()
            .filter(|c| c.owner.is_none())
            .map(|c| ((c.module.as_str(), c.name.as_str()), &c.declaration))
            .collect();
        let mut reachable = BTreeMap::<&str, BTreeSet<String>>::new();
        for callable in plan.callables() {
            let mut authority = effects(&callable.declaration);
            if let Some(function) = callable.declaration.pointer("/selected/function") {
                if let (Some(module), Some(name)) = (
                    function.get("module").and_then(serde_json::Value::as_str),
                    function.get("symbol").and_then(serde_json::Value::as_str),
                ) {
                    if let Some(function) = functions.get(&(module, name)) {
                        authority.extend(effects(function));
                    }
                }
            }
            if let Some(method) = callable
                .declaration
                .get("trait_method")
                .and_then(serde_json::Value::as_str)
            {
                reachable
                    .entry(method)
                    .or_default()
                    .extend(authority.iter().cloned());
            }
            let Some(owner) = callable
                .owner
                .as_ref()
                .and_then(|owner| owner.get("name"))
                .and_then(serde_json::Value::as_str)
            else {
                continue;
            };
            if selected.contains(owner) {
                merge(
                    result.types.entry(rust_path(owner)).or_default(),
                    &rust_identifier(&callable.name),
                    &authority,
                );
                result
                    .paths
                    .entry(rust_path(&callable.symbol))
                    .or_default()
                    .extend(authority.iter().cloned());
            }
        }
        result.add_traits(context, &reachable);
        result
    }
    fn add_traits(
        &mut self,
        value: &serde_json::Value,
        reachable: &BTreeMap<&str, BTreeSet<String>>,
    ) {
        match value {
            serde_json::Value::Object(object) => {
                if object.get("kind").and_then(serde_json::Value::as_str) == Some("trait") {
                    if let Some(owner) = object.get("name").and_then(serde_json::Value::as_str) {
                        let mut methods = MethodEffects::new();
                        for method in object
                            .get("methods")
                            .and_then(serde_json::Value::as_array)
                            .into_iter()
                            .flatten()
                        {
                            let Some(symbol) =
                                method.get("name").and_then(serde_json::Value::as_str)
                            else {
                                continue;
                            };
                            let leaf = rust_identifier(symbol.rsplit('.').next().unwrap_or(symbol));
                            let mut authority = effects(method);
                            // A dynamic/bare trait value may reach any compiler-known implementation.
                            // Concrete selected method and selected default-function effects, not just
                            // the abstract signature, therefore constrain the caller.
                            if let Some(concrete) = reachable.get(symbol) {
                                authority.extend(concrete.iter().cloned());
                            }
                            self.paths
                                .entry(format!("{}::{leaf}", rust_path(owner)))
                                .or_default()
                                .extend(authority.iter().cloned());
                            if symbol.contains('.') {
                                self.paths
                                    .entry(rust_path(symbol))
                                    .or_default()
                                    .extend(authority.iter().cloned());
                            }
                            merge(&mut methods, &leaf, &authority);
                            merge(&mut self.dynamic, &leaf, &authority);
                        }
                        let path = rust_path(owner);
                        self.traits.insert(path.clone());
                        self.types.insert(format!("{path}Value"), methods.clone());
                        self.types.insert(path, methods);
                    }
                }
                for child in object.values() {
                    self.add_traits(child, reachable);
                }
            }
            serde_json::Value::Array(array) => {
                for child in array {
                    self.add_traits(child, reachable);
                }
            }
            _ => {}
        }
    }
    fn typed_method(
        &self,
        node: Node<'_>,
        member: &str,
        source: &str,
        aliases: &BTreeMap<String, String>,
    ) -> Option<&BTreeSet<String>> {
        match node.kind() {
            "reference_type" => {
                return self.typed_method(
                    node.child_by_field_name("type")?,
                    member,
                    source,
                    aliases,
                );
            }
            "generic_type" => {
                return self.typed_method(
                    node.child_by_field_name("type")?,
                    member,
                    source,
                    aliases,
                );
            }
            "dynamic_type" | "bounded_type" => {
                return children(node)
                    .into_iter()
                    .find_map(|child| self.typed_method(child, member, source, aliases));
            }
            _ => {}
        }
        let path = resolve(&reference_path(node, source)?, aliases);
        if path.starts_with("crate::cott_runtime::trait_values::TraitDispatch_") {
            return self.dynamic.get(member);
        }
        if let Some(methods) = self.types.get(&path) {
            return methods.get(member);
        }
        // A generic receiver is authorized only by a selected native Cott trait bound,
        // never by the spelling of a type parameter or a third-party trait.
        if node.kind() == "type_identifier" {
            let mut ancestor = node.parent();
            while let Some(parent) = ancestor {
                if parent.kind() == "function_item" {
                    for item in children(parent)
                        .into_iter()
                        .filter(|n| n.kind() == "type_parameters")
                    {
                        for parameter in children(item) {
                            if parameter
                                .child_by_field_name("name")
                                .is_some_and(|name| text(name, source) == path)
                            {
                                if let Some(bounds) = parameter.child_by_field_name("bounds") {
                                    for bound in children(bounds) {
                                        if let Some(bound) = reference_path(bound, source) {
                                            let bound = resolve(&bound, aliases);
                                            if self.traits.contains(&bound) {
                                                return self.types.get(&bound)?.get(member);
                                            }
                                        }
                                    }
                                }
                                return None;
                            }
                        }
                    }
                    return None;
                }
                ancestor = parent.parent();
            }
        }
        None
    }
    fn receiver_method(
        &self,
        receiver: Node<'_>,
        member: &str,
        source: &str,
        aliases: &BTreeMap<String, String>,
    ) -> Option<&BTreeSet<String>> {
        match receiver.kind() {
            "reference_expression" => self.receiver_method(
                receiver.child_by_field_name("value")?,
                member,
                source,
                aliases,
            ),
            "parenthesized_expression" => {
                self.receiver_method(*children(receiver).first()?, member, source, aliases)
            }
            "identifier" => {
                let declaration = task_scope::binding_declaration(receiver, source)?;
                if let Some(ty) = declaration.child_by_field_name("type") {
                    return self.typed_method(ty, member, source, aliases);
                }
                self.receiver_method(
                    declaration.child_by_field_name("value")?,
                    member,
                    source,
                    aliases,
                )
            }
            "call_expression" => {
                let path = resolve(
                    &reference_path(receiver.child_by_field_name("function")?, source)?,
                    aliases,
                );
                let owner = path.strip_suffix("::new")?;
                self.types.get(owner)?.get(member)
            }
            _ => None,
        }
    }
    pub fn member_effects(
        &self,
        member: Node<'_>,
        source: &str,
        aliases: &BTreeMap<String, String>,
    ) -> Option<&BTreeSet<String>> {
        let field = member.parent().filter(|n| n.kind() == "field_expression")?;
        if field.child_by_field_name("field")?.id() != member.id() {
            return None;
        }
        self.receiver_method(
            field.child_by_field_name("value")?,
            text(member, source),
            source,
            aliases,
        )
    }
}
