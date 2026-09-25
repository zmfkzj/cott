use std::collections::{BTreeMap, BTreeSet};
use std::path::Path;

use serde_json::{Map, Value, json};

use crate::agent::parse_domain_rules;
use crate::hash::sha256_hex;

pub const TOOL_KEY: &str = "cott_intent";

const INTENT_DOMAIN: &str = "cott.intent";
const INTENT_VERSION: u64 = 1;

pub fn context(surface: &Value, symbol: &str, rules: &[u8]) -> Result<Value, String> {
    let index = SurfaceIndex::parse(surface)?;
    let prepared = PreparedRules::parse(rules)?;
    let selected = index.select(symbol, &prepared)?;
    Ok(json!({
        "declarations": selected.declarations,
        "project_rules": prepared.retained(&selected.callables),
        "symbol": symbol,
    }))
}

pub fn fingerprints(surface: &Value, rules: &[u8]) -> Result<BTreeMap<String, String>, String> {
    let index = SurfaceIndex::parse(surface)?;
    let prepared = PreparedRules::parse(rules)?;
    let mut hashes = BTreeMap::new();
    for symbol in index.callables.keys().cloned().collect::<Vec<_>>() {
        let selected = index.select(&symbol, &prepared)?;
        let ctx = json!({
            "declarations": selected.declarations,
            "project_rules": prepared.retained(&selected.callables),
            "symbol": symbol,
        });
        hashes.insert(symbol, fingerprint_context(&ctx)?);
    }
    Ok(hashes)
}

pub fn metadata(hashes: &BTreeMap<String, String>) -> Value {
    json!({
        "hashes": hashes,
        "version": INTENT_VERSION,
    })
}

pub fn recorded_fingerprints(tools: &Value) -> Result<Option<BTreeMap<String, String>>, String> {
    let object = tools
        .as_object()
        .ok_or_else(|| "generation tools must be an object".to_owned())?;
    let Some(intent) = object.get(TOOL_KEY) else {
        return Ok(None);
    };
    let intent = intent
        .as_object()
        .ok_or_else(|| "tools.cott_intent must be an object".to_owned())?;
    if intent.keys().any(|key| key != "hashes" && key != "version") {
        return Err("tools.cott_intent has unsupported fields".to_owned());
    }
    let version = intent
        .get("version")
        .and_then(Value::as_u64)
        .ok_or_else(|| "tools.cott_intent version must be 1".to_owned())?;
    if version != INTENT_VERSION {
        return Err(format!(
            "tools.cott_intent version {version} is unsupported"
        ));
    }
    let hashes = intent
        .get("hashes")
        .and_then(Value::as_object)
        .ok_or_else(|| "tools.cott_intent hashes must be an object".to_owned())?;
    let mut recorded = BTreeMap::new();
    for (symbol, digest) in hashes {
        if symbol.is_empty() {
            return Err("tools.cott_intent hashes contain an empty symbol".to_owned());
        }
        let digest = digest
            .as_str()
            .ok_or_else(|| format!("tools.cott_intent hash for `{symbol}` must be a string"))?;
        if !valid_digest(digest) {
            return Err(format!(
                "tools.cott_intent hash for `{symbol}` is not a sha256 digest"
            ));
        }
        recorded.insert(symbol.clone(), digest.to_owned());
    }
    Ok(Some(recorded))
}

pub(crate) fn fingerprint_context(ctx: &Value) -> Result<String, String> {
    let payload = json!({
        "context": ctx,
        "domain": INTENT_DOMAIN,
    });
    let bytes = serde_json::to_vec(&payload).map_err(|error| error.to_string())?;
    Ok(format!("sha256:{}", sha256_hex(&bytes)))
}

fn valid_digest(value: &str) -> bool {
    let Some(hex) = value.strip_prefix("sha256:") else {
        return false;
    };
    hex.len() == 64
        && hex
            .bytes()
            .all(|byte| matches!(byte, b'0'..=b'9' | b'a'..=b'f'))
}

struct PreparedRules<'a> {
    text: &'a str,
    directives: Vec<(String, Vec<String>)>,
    global_tokens: Vec<String>,
}

impl<'a> PreparedRules<'a> {
    fn parse(rules: &'a [u8]) -> Result<Self, String> {
        let text = std::str::from_utf8(rules)
            .map_err(|_| "generator rules must be valid UTF-8".to_owned())?;
        let parsed = parse_domain_rules(Path::new("generator.rules"), rules);
        if let Some(diagnostic) = parsed.diagnostics.first() {
            return Err(diagnostic.message.clone());
        }
        Ok(Self {
            text,
            directives: parsed
                .rules
                .into_iter()
                .map(|rule| (rule.symbol, identifiers(&rule.payload)))
                .collect(),
            global_tokens: text
                .split_inclusive('\n')
                .filter(|line| {
                    !line
                        .strip_suffix('\n')
                        .unwrap_or(line)
                        .starts_with("cott-domain ")
                })
                .flat_map(identifiers)
                .collect(),
        })
    }

    fn retained(&self, selected: &BTreeSet<String>) -> String {
        let mut kept = String::new();
        for line in self.text.split_inclusive('\n') {
            let content = line.strip_suffix('\n').unwrap_or(line);
            if let Some(rest) = content.strip_prefix("cott-domain ") {
                let symbol = rest.split_whitespace().next().unwrap_or_default();
                if selected.contains(symbol) {
                    kept.push_str(line);
                }
            } else {
                kept.push_str(line);
            }
        }
        kept
    }
}

struct SurfaceIndex {
    modules: BTreeMap<String, Vec<Value>>,
    by_name: BTreeMap<String, (String, usize)>,
    callables: BTreeMap<String, CallableInfo>,
    impl_methods: BTreeMap<String, Vec<String>>,
    local_callables: BTreeMap<String, BTreeMap<String, Vec<String>>>,
    local_decls: BTreeMap<String, BTreeMap<String, Vec<String>>>,
}

struct CallableInfo {
    decl_name: String,
}

struct Selection {
    declarations: Map<String, Value>,
    callables: BTreeSet<String>,
}

impl SurfaceIndex {
    fn parse(surface: &Value) -> Result<Self, String> {
        let modules_in = surface
            .as_object()
            .ok_or_else(|| "contract surface must be an object".to_owned())?;
        let mut modules = BTreeMap::new();
        let mut by_name = BTreeMap::new();
        let mut callables = BTreeMap::new();
        let mut impl_methods = BTreeMap::new();
        let mut local_callables: BTreeMap<String, BTreeMap<String, Vec<String>>> = BTreeMap::new();
        let mut local_decls: BTreeMap<String, BTreeMap<String, Vec<String>>> = BTreeMap::new();
        for (module, body) in modules_in {
            let declarations = body
                .get("declarations")
                .and_then(Value::as_array)
                .ok_or_else(|| {
                    format!("contract surface module `{module}` must have declarations")
                })?;
            let mut stripped = Vec::with_capacity(declarations.len());
            for declaration in declarations {
                let mut declaration = declaration.clone();
                strip_source_metadata(&mut declaration);
                let kind = declaration
                    .get("kind")
                    .and_then(Value::as_str)
                    .ok_or_else(|| format!("declaration in `{module}` is missing kind"))?
                    .to_owned();
                let name = declaration
                    .get("name")
                    .and_then(Value::as_str)
                    .ok_or_else(|| format!("declaration in `{module}` is missing name"))?
                    .to_owned();
                if kind == "requirement" {
                    // Linkage and waivers are verification/report metadata, not intent: adding
                    // evidence links or temporary waivers never invalidates an implementation.
                    // Requirements are selected through their callable, so their local names
                    // never make an unrelated doc token ambiguous.
                    if let Some(object) = declaration.as_object_mut() {
                        object.remove("checked_by");
                        object.remove("waivers");
                    }
                } else {
                    local_decls
                        .entry(module.clone())
                        .or_default()
                        .entry(local_name(&name).to_owned())
                        .or_default()
                        .push(name.clone());
                }
                let index = stripped.len();
                if kind == "function" {
                    record_callable(
                        &mut callables,
                        &mut local_callables,
                        module,
                        &name,
                        name.clone(),
                    );
                } else if kind == "impl" {
                    let methods = explicit_impl_methods(&name, &declaration);
                    for method in &methods {
                        record_callable(
                            &mut callables,
                            &mut local_callables,
                            module,
                            method,
                            name.clone(),
                        );
                    }
                    impl_methods.insert(name.clone(), methods);
                }
                by_name.insert(name, (module.clone(), index));
                stripped.push(declaration);
            }
            modules.insert(module.clone(), stripped);
        }
        Ok(Self {
            modules,
            by_name,
            callables,
            impl_methods,
            local_callables,
            local_decls,
        })
    }

    fn select(&self, symbol: &str, rules: &PreparedRules<'_>) -> Result<Selection, String> {
        let target = self
            .callables
            .get(symbol)
            .ok_or_else(|| format!("unknown callable `{symbol}`"))?;
        let mut selected_decls = BTreeSet::new();
        let mut selected_callables = BTreeSet::new();
        let mut queue = Vec::new();
        self.select_callable(
            symbol,
            &mut selected_decls,
            &mut selected_callables,
            &mut queue,
        );
        for sibling in self
            .impl_methods
            .get(&target.decl_name)
            .into_iter()
            .flatten()
        {
            self.select_callable(
                sibling,
                &mut selected_decls,
                &mut selected_callables,
                &mut queue,
            );
        }
        let target_module = self.module_of_callable(symbol);
        for token in &rules.global_tokens {
            self.resolve_doc_token(
                token,
                target_module,
                &mut selected_decls,
                &mut selected_callables,
                &mut queue,
            );
        }
        let mut used_directives = vec![false; rules.directives.len()];
        loop {
            let before = (selected_decls.len(), selected_callables.len());
            while let Some(name) = queue.pop() {
                let Some(declaration) = self.declaration(&name) else {
                    continue;
                };
                for reference in nominal_references(declaration)? {
                    if self.by_name.contains_key(&reference) {
                        self.select_decl(
                            &reference,
                            &mut selected_decls,
                            &mut selected_callables,
                            &mut queue,
                        );
                    } else {
                        self.select_callable(
                            &reference,
                            &mut selected_decls,
                            &mut selected_callables,
                            &mut queue,
                        );
                    }
                }
                for token in doc_tokens(declaration) {
                    self.resolve_doc_token(
                        &token,
                        self.module_of(&name).unwrap_or(""),
                        &mut selected_decls,
                        &mut selected_callables,
                        &mut queue,
                    );
                }
            }
            for (name, declaration) in self.declarations() {
                let selected = match declaration.get("kind").and_then(Value::as_str) {
                    Some("scenario") => scenario_targets(declaration)
                        .iter()
                        .any(|target| selected_callables.contains(target) || target == symbol),
                    // Normative requirement text is intent of the callable it is tied to.
                    Some("requirement") => declaration
                        .get("callable")
                        .and_then(Value::as_str)
                        .is_some_and(|callable| {
                            callable == symbol || selected_callables.contains(callable)
                        }),
                    _ => false,
                };
                if selected {
                    self.select_decl(
                        name,
                        &mut selected_decls,
                        &mut selected_callables,
                        &mut queue,
                    );
                }
            }
            for (index, (rule_symbol, tokens)) in rules.directives.iter().enumerate() {
                if used_directives[index] || !selected_callables.contains(rule_symbol) {
                    continue;
                }
                used_directives[index] = true;
                let module = self.module_of_callable(rule_symbol);
                for token in tokens {
                    self.resolve_doc_token(
                        token,
                        module,
                        &mut selected_decls,
                        &mut selected_callables,
                        &mut queue,
                    );
                }
            }
            if (selected_decls.len(), selected_callables.len()) == before {
                break;
            }
        }
        let mut declarations = Map::new();
        for (module, module_decls) in &self.modules {
            let selected = module_decls
                .iter()
                .filter(|declaration| {
                    declaration
                        .get("name")
                        .and_then(Value::as_str)
                        .is_some_and(|name| selected_decls.contains(name))
                })
                .cloned()
                .collect::<Vec<_>>();
            if !selected.is_empty() {
                declarations.insert(module.clone(), json!({ "declarations": selected }));
            }
        }
        Ok(Selection {
            declarations,
            callables: selected_callables,
        })
    }

    fn select_callable(
        &self,
        symbol: &str,
        selected_decls: &mut BTreeSet<String>,
        selected_callables: &mut BTreeSet<String>,
        queue: &mut Vec<String>,
    ) {
        let Some(info) = self.callables.get(symbol) else {
            return;
        };
        if !selected_callables.insert(symbol.to_owned()) {
            return;
        }
        self.select_decl(&info.decl_name, selected_decls, selected_callables, queue);
    }

    fn select_decl(
        &self,
        name: &str,
        selected_decls: &mut BTreeSet<String>,
        selected_callables: &mut BTreeSet<String>,
        queue: &mut Vec<String>,
    ) {
        if !self.by_name.contains_key(name) || !selected_decls.insert(name.to_owned()) {
            return;
        }
        queue.push(name.to_owned());
        if let Some(methods) = self.impl_methods.get(name) {
            for method in methods {
                selected_callables.insert(method.clone());
            }
        } else if self.callables.contains_key(name) {
            selected_callables.insert(name.to_owned());
        }
    }

    fn resolve_doc_token(
        &self,
        token: &str,
        module: &str,
        selected_decls: &mut BTreeSet<String>,
        selected_callables: &mut BTreeSet<String>,
        queue: &mut Vec<String>,
    ) {
        if self.select_explicit(token, module, selected_decls, selected_callables, queue) {
            return;
        }
        if let Some((prefix, _)) = token.rsplit_once('.') {
            self.resolve_doc_token(prefix, module, selected_decls, selected_callables, queue);
            return;
        }
        if let Some(candidates) = self
            .local_decls
            .get(module)
            .and_then(|names| names.get(token))
        {
            if let [unique] = candidates.as_slice() {
                self.select_decl(unique, selected_decls, selected_callables, queue);
                return;
            }
        }
        if let Some(candidates) = self
            .local_callables
            .get(module)
            .and_then(|names| names.get(token))
        {
            if let [unique] = candidates.as_slice() {
                self.select_callable(unique, selected_decls, selected_callables, queue);
            }
        }
    }

    fn select_explicit(
        &self,
        token: &str,
        module: &str,
        selected_decls: &mut BTreeSet<String>,
        selected_callables: &mut BTreeSet<String>,
        queue: &mut Vec<String>,
    ) -> bool {
        if self.by_name.contains_key(token) {
            self.select_decl(token, selected_decls, selected_callables, queue);
            return true;
        }
        if self.callables.contains_key(token) {
            self.select_callable(token, selected_decls, selected_callables, queue);
            return true;
        }
        if !module.is_empty()
            && token != module
            && !token
                .strip_prefix(module)
                .is_some_and(|rest| rest.starts_with('.'))
        {
            let qualified = format!("{module}.{token}");
            if self.by_name.contains_key(&qualified) {
                self.select_decl(&qualified, selected_decls, selected_callables, queue);
                return true;
            }
            if self.callables.contains_key(&qualified) {
                self.select_callable(&qualified, selected_decls, selected_callables, queue);
                return true;
            }
        }
        false
    }

    fn declaration(&self, name: &str) -> Option<&Value> {
        let (module, index) = self.by_name.get(name)?;
        self.modules.get(module)?.get(*index)
    }

    fn module_of(&self, name: &str) -> Option<&str> {
        self.by_name.get(name).map(|(module, _)| module.as_str())
    }

    fn module_of_callable(&self, symbol: &str) -> &str {
        self.callables
            .get(symbol)
            .and_then(|info| self.module_of(&info.decl_name))
            .or_else(|| self.module_of(symbol))
            .unwrap_or("")
    }

    fn declarations(&self) -> impl Iterator<Item = (&String, &Value)> {
        self.by_name.iter().filter_map(|(name, (module, index))| {
            Some((name, self.modules.get(module)?.get(*index)?))
        })
    }
}

fn record_callable(
    callables: &mut BTreeMap<String, CallableInfo>,
    local_callables: &mut BTreeMap<String, BTreeMap<String, Vec<String>>>,
    module: &str,
    symbol: &str,
    decl_name: String,
) {
    callables.insert(symbol.to_owned(), CallableInfo { decl_name });
    local_callables
        .entry(module.to_owned())
        .or_default()
        .entry(local_name(symbol).to_owned())
        .or_default()
        .push(symbol.to_owned());
}

fn explicit_impl_methods(impl_name: &str, declaration: &Value) -> Vec<String> {
    declaration
        .get("selected_methods")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
        .filter_map(|slot| {
            let origin = slot
                .get("selected")
                .and_then(Value::as_object)
                .and_then(|selected| selected.get("origin"))
                .and_then(Value::as_str)?;
            if origin != "explicit" {
                return None;
            }
            let method = local_name(slot.get("trait_method")?.as_str()?);
            Some(format!("{impl_name}.{method}"))
        })
        .collect()
}

fn local_name(name: &str) -> &str {
    name.rsplit('.').next().unwrap_or(name)
}

fn nominal_references(value: &Value) -> Result<Vec<String>, String> {
    let mut names = Vec::new();
    walk_nominals(value, &mut names)?;
    Ok(names)
}

fn walk_nominals(value: &Value, names: &mut Vec<String>) -> Result<(), String> {
    match value {
        Value::Array(values) => {
            for value in values {
                walk_nominals(value, names)?;
            }
        }
        Value::Object(object) => {
            if let Some(annotations) = object.get("annotations").and_then(Value::as_array) {
                for annotation in annotations {
                    let Some(annotation) = annotation.as_object() else {
                        continue;
                    };
                    if annotation.get("name").and_then(Value::as_str) == Some("cott.applied_rule") {
                        names.push(applied_rule_argument(annotation)?);
                    }
                }
            }
            match object.get("kind").and_then(Value::as_str) {
                Some("named") => {
                    if let Some(name) = object.get("name").and_then(Value::as_str) {
                        names.push(name.to_owned());
                    }
                }
                Some("reference" | "constant_ref" | "constant") => {
                    if let Some(symbol) = object.get("symbol").and_then(Value::as_str) {
                        names.push(symbol.to_owned());
                    }
                }
                Some("call" | "init" | "method_call" | "spawn") => {
                    if let Some(target) = object.get("target").and_then(Value::as_str) {
                        names.push(target.to_owned());
                    }
                }
                Some("rule") => {
                    if let Some(base) = object.get("base").and_then(Value::as_str) {
                        names.push(base.to_owned());
                    }
                    if let Some(base) = object.get("base_type").and_then(Value::as_str) {
                        names.push(base.to_owned());
                    }
                }
                _ => {}
            }
            for (key, value) in object {
                if key == "annotations" {
                    continue;
                }
                walk_nominals(value, names)?;
            }
        }
        _ => {}
    }
    Ok(())
}

fn applied_rule_argument(annotation: &Map<String, Value>) -> Result<String, String> {
    match annotation.get("argument") {
        Some(Value::String(symbol)) if valid_link_symbol(symbol) => Ok(symbol.clone()),
        _ => Err("cott.applied_rule argument must be a rule FQN string".to_owned()),
    }
}

fn valid_link_symbol(symbol: &str) -> bool {
    identifiers(symbol)
        .first()
        .is_some_and(|token| token == symbol)
}

fn scenario_targets(declaration: &Value) -> Vec<String> {
    let mut targets = Vec::new();
    if let Some(target) = declaration.get("target").and_then(Value::as_str) {
        targets.push(target.to_owned());
    }
    for step in declaration
        .get("steps")
        .and_then(Value::as_array)
        .into_iter()
        .flatten()
    {
        if let Some(target) = step.get("target").and_then(Value::as_str) {
            targets.push(target.to_owned());
        }
    }
    targets
}

fn doc_tokens(value: &Value) -> Vec<String> {
    let mut texts = Vec::new();
    collect_doc_texts(value, &mut texts);
    texts
        .into_iter()
        .flat_map(|text| identifiers(&text))
        .collect()
}

fn collect_doc_texts(value: &Value, texts: &mut Vec<String>) {
    match value {
        Value::Array(values) => {
            for value in values {
                collect_doc_texts(value, texts);
            }
        }
        Value::Object(object) => {
            if object.get("kind").and_then(Value::as_str) == Some("requirement") {
                if let Some(text) = value.pointer("/statement/text").and_then(Value::as_str) {
                    texts.push(text.to_owned());
                }
                for assumption in object
                    .get("assumptions")
                    .and_then(Value::as_array)
                    .into_iter()
                    .flatten()
                    .filter_map(|assumption| assumption.get("text").and_then(Value::as_str))
                {
                    texts.push(assumption.to_owned());
                }
            }
            match object.get("doc") {
                Some(Value::String(text)) => texts.push(text.clone()),
                Some(Value::Object(doc)) => {
                    if let Some(text) = doc.get("text").and_then(Value::as_str) {
                        texts.push(text.to_owned());
                    }
                }
                _ => {}
            }
            for (key, value) in object {
                if key != "doc" {
                    collect_doc_texts(value, texts);
                }
            }
        }
        _ => {}
    }
}

fn identifiers(text: &str) -> Vec<String> {
    let bytes = text.as_bytes();
    let mut index = 0;
    let mut tokens = Vec::new();
    while index < bytes.len() {
        if is_ident_start(bytes[index]) {
            let start = index;
            index += 1;
            while index < bytes.len() && is_ident_continue(bytes[index]) {
                index += 1;
            }
            while index + 1 < bytes.len()
                && bytes[index] == b'.'
                && is_ident_start(bytes[index + 1])
            {
                index += 1;
                while index < bytes.len() && is_ident_continue(bytes[index]) {
                    index += 1;
                }
            }
            tokens.push(text[start..index].to_owned());
        } else {
            index += 1;
        }
    }
    tokens
}

fn is_ident_start(byte: u8) -> bool {
    byte == b'_' || byte.is_ascii_alphabetic()
}

fn is_ident_continue(byte: u8) -> bool {
    byte == b'_' || byte.is_ascii_alphanumeric()
}

fn strip_source_metadata(value: &mut Value) {
    match value {
        Value::Array(values) => {
            for value in values {
                strip_source_metadata(value);
            }
        }
        Value::Object(object) => {
            object.remove("span");
            object.remove("source_order");
            for value in object.values_mut() {
                strip_source_metadata(value);
            }
        }
        _ => {}
    }
}
