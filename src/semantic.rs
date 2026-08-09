use std::collections::{BTreeMap, BTreeSet, HashMap, HashSet};
use std::path::{Component, Path, PathBuf};

use crate::ast::{
    self, ClauseKind, ConstExpr, Declaration, Expr, ExprKind, FunctionBody, LiteralKind,
    TypeArgKind,
};
use crate::compiler::{ParsedProject, ParsedSource, ProjectDiagnostic};
use crate::diagnostics::{Diagnostic, Span};

/// A canonical module identity.
#[derive(Clone, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct ModuleId {
    pub segments: Vec<String>,
}

impl ModuleId {
    pub fn new(segments: Vec<String>) -> Self {
        Self { segments }
    }

    pub fn as_string(&self) -> String {
        self.segments.join(".")
    }
}

/// A canonical declaration identity.
#[derive(Clone, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub struct SymbolId {
    pub module: ModuleId,
    pub name: String,
}

impl SymbolId {
    pub fn new(module: ModuleId, name: impl Into<String>) -> Self {
        Self {
            module,
            name: name.into(),
        }
    }

    pub fn as_string(&self) -> String {
        if self.module.segments.is_empty() {
            self.name.clone()
        } else {
            format!("{}.{}", self.module.as_string(), self.name)
        }
    }
}

/// The primitive types accepted by the constrained semantic profile.
#[derive(Clone, Copy, Debug, Eq, Hash, Ord, PartialEq, PartialOrd)]
pub enum PrimitiveType {
    Bool,
    I8,
    I16,
    I32,
    I64,
    U8,
    U16,
    U32,
    U64,
    F64,
    Str,
    Bytes,
    Unit,
}

/// A closed, alias-free type representation.
#[derive(Clone, Debug, Eq, Hash, PartialEq)]
pub enum ResolvedType {
    Primitive(PrimitiveType),
    Named(SymbolId),
    Option(Box<ResolvedType>),
    Result {
        ok: Box<ResolvedType>,
        error: SymbolId,
    },
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SemanticDoc {
    pub span: Span,
    pub text: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SemanticImport {
    pub span: Span,
    pub symbol: SymbolId,
    pub name: String,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SemanticField {
    pub span: Span,
    pub name: String,
    pub ty: ResolvedType,
    pub default: Option<SemanticValue>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SemanticParameter {
    pub span: Span,
    pub name: String,
    pub ty: ResolvedType,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SemanticVariant {
    pub id: SymbolId,
    pub span: Span,
    pub name: String,
    pub parameters: Vec<SemanticParameter>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SemanticAlias {
    pub id: SymbolId,
    pub span: Span,
    pub doc: Option<SemanticDoc>,
    pub target: ResolvedType,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SemanticNewtype {
    pub id: SymbolId,
    pub span: Span,
    pub doc: Option<SemanticDoc>,
    pub underlying: ResolvedType,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SemanticStruct {
    pub id: SymbolId,
    pub span: Span,
    pub doc: Option<SemanticDoc>,
    pub fields: Vec<SemanticField>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SemanticEnum {
    pub id: SymbolId,
    pub span: Span,
    pub doc: Option<SemanticDoc>,
    pub variants: Vec<SemanticVariant>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SemanticConst {
    pub id: SymbolId,
    pub span: Span,
    pub doc: Option<SemanticDoc>,
    pub ty: ResolvedType,
    pub value: SemanticValue,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SemanticFunction {
    pub id: SymbolId,
    pub span: Span,
    pub doc: Option<SemanticDoc>,
    pub parameters: Vec<SemanticParameter>,
    pub return_type: ResolvedType,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub enum SemanticDeclaration {
    Alias(SemanticAlias),
    Newtype(SemanticNewtype),
    Struct(SemanticStruct),
    Enum(SemanticEnum),
    Const(SemanticConst),
    Function(SemanticFunction),
}

impl SemanticDeclaration {
    pub fn id(&self) -> &SymbolId {
        match self {
            Self::Alias(v) => &v.id,
            Self::Newtype(v) => &v.id,
            Self::Struct(v) => &v.id,
            Self::Enum(v) => &v.id,
            Self::Const(v) => &v.id,
            Self::Function(v) => &v.id,
        }
    }

    pub fn span(&self) -> &Span {
        match self {
            Self::Alias(v) => &v.span,
            Self::Newtype(v) => &v.span,
            Self::Struct(v) => &v.span,
            Self::Enum(v) => &v.span,
            Self::Const(v) => &v.span,
            Self::Function(v) => &v.span,
        }
    }
}

/// A typed literal retained for a constant or field default.
#[derive(Clone, Debug, Eq, PartialEq)]
pub enum SemanticValue {
    Bool(bool),
    Integer(String),
    Float(String),
    String(String),
    Unit,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SemanticModule {
    pub source: PathBuf,
    pub id: ModuleId,
    pub imports: Vec<SemanticImport>,
    pub declarations: Vec<SemanticDeclaration>,
}

#[derive(Clone, Debug, Eq, PartialEq)]
pub struct SemanticProject {
    pub modules: Vec<SemanticModule>,
}

#[derive(Clone)]
struct ModuleInput {
    source_index: usize,
    source: PathBuf,
    id: ModuleId,
    file: ast::File,
}

#[derive(Clone, Copy, Debug, Eq, PartialEq)]
enum DeclKind {
    Alias,
    Newtype,
    Struct,
    Enum,
    Const,
    Function,
}

impl DeclKind {
    fn is_type(self) -> bool {
        matches!(
            self,
            Self::Alias | Self::Newtype | Self::Struct | Self::Enum
        )
    }
}

#[derive(Clone)]
struct DeclInfo {
    module_index: usize,
    declaration_index: usize,
    kind: DeclKind,
    span: Span,
}

#[derive(Clone)]
struct PendingDiagnostic {
    source_index: usize,
    sequence: usize,
    diagnostic: ProjectDiagnostic,
}

struct Diagnostics {
    values: Vec<PendingDiagnostic>,
    sequence: usize,
}

impl Diagnostics {
    fn new() -> Self {
        Self {
            values: Vec::new(),
            sequence: 0,
        }
    }

    fn push(&mut self, source: &ModuleInput, span: Span, message: impl Into<String>) {
        self.values.push(PendingDiagnostic {
            source_index: source.source_index,
            sequence: self.sequence,
            diagnostic: ProjectDiagnostic {
                path: source.source.clone(),
                diagnostic: Diagnostic::new(message, span),
            },
        });
        self.sequence += 1;
    }

    fn finish(mut self) -> Vec<ProjectDiagnostic> {
        self.values.sort_by(|a, b| {
            (
                a.source_index,
                a.diagnostic.diagnostic.span.start,
                a.diagnostic.diagnostic.span.end,
                a.sequence,
            )
                .cmp(&(
                    b.source_index,
                    b.diagnostic.diagnostic.span.start,
                    b.diagnostic.diagnostic.span.end,
                    b.sequence,
                ))
        });
        self.values
            .into_iter()
            .map(|pending| pending.diagnostic)
            .collect()
    }
}

struct Analyzer {
    source_root: PathBuf,
    modules: Vec<ModuleInput>,
    module_by_id: BTreeMap<ModuleId, usize>,
    declarations: BTreeMap<SymbolId, DeclInfo>,
    imports: Vec<BTreeMap<String, SymbolId>>,
    module_dependencies: Vec<BTreeSet<usize>>,
    declaration_dependencies: BTreeMap<SymbolId, BTreeSet<SymbolId>>,
    diagnostics: Diagnostics,
    resolving: HashSet<SymbolId>,
}

/// Validate parsed syntax and project relationships without constructing the
/// legacy semantic snapshot. HIR uses this only for shared diagnostics.
pub(crate) fn validate_parsed_project(
    source_root: &Path,
    parsed: &ParsedProject,
) -> Result<(), Vec<ProjectDiagnostic>> {
    let mut analyzer = Analyzer::new(source_root, parsed.clone());
    analyzer.validate_only()
}

pub fn analyze_project(
    source_root: &Path,
    parsed: ParsedProject,
) -> Result<SemanticProject, Vec<ProjectDiagnostic>> {
    let mut analyzer = Analyzer::new(source_root, parsed);
    analyzer.analyze()
}

impl Analyzer {
    fn new(source_root: &Path, parsed: ParsedProject) -> Self {
        let mut diagnostics = Diagnostics::new();
        let mut modules = Vec::new();
        for (source_index, ParsedSource { path, syntax, .. }) in
            parsed.sources.into_iter().enumerate()
        {
            match module_path(source_root, &path) {
                Ok(segments) => {
                    let source = ModuleInput {
                        source_index,
                        source: path,
                        id: ModuleId::new(segments.clone()),
                        file: syntax,
                    };
                    if source.file.module.path.segments != segments {
                        diagnostics.push(
                            &source,
                            source.file.module.path.span.clone(),
                            format!(
                                "module declaration `{}` does not match source path module `{}`",
                                source.file.module.path.segments.join("."),
                                segments.join(".")
                            ),
                        );
                    }
                    modules.push(source);
                }
                Err(message) => {
                    let span = syntax.module.span.clone();
                    let source = ModuleInput {
                        source_index,
                        source: path,
                        id: ModuleId::new(Vec::new()),
                        file: syntax,
                    };
                    diagnostics.push(&source, span, message);
                    modules.push(source);
                }
            }
        }
        Self {
            source_root: source_root.to_path_buf(),
            modules,
            module_by_id: BTreeMap::new(),
            declarations: BTreeMap::new(),
            imports: Vec::new(),
            module_dependencies: Vec::new(),
            declaration_dependencies: BTreeMap::new(),
            diagnostics,
            resolving: HashSet::new(),
        }
    }
    fn validate_only(&mut self) -> Result<(), Vec<ProjectDiagnostic>> {
        if self.modules.is_empty() {
            return Err(vec![ProjectDiagnostic {
                path: self.source_root.clone(),
                diagnostic: Diagnostic::new("project contains no parsed sources", Span::new(0, 0)),
            }]);
        }
        self.index_modules();
        self.index_declarations();
        self.validate_imports();
        self.validate_module_cycles();
        self.validate_declaration_shapes();
        self.validate_declaration_cycles();
        if self.diagnostics.values.is_empty() {
            Ok(())
        } else {
            Err(std::mem::replace(&mut self.diagnostics, Diagnostics::new()).finish())
        }
    }

    fn analyze(&mut self) -> Result<SemanticProject, Vec<ProjectDiagnostic>> {
        if self.modules.is_empty() {
            return Err(vec![ProjectDiagnostic {
                path: self.source_root.clone(),
                diagnostic: Diagnostic::new("project contains no parsed sources", Span::new(0, 0)),
            }]);
        }
        self.index_modules();
        self.index_declarations();
        self.validate_imports();
        self.validate_module_cycles();
        self.validate_declaration_shapes();
        self.validate_declaration_cycles();
        if !self.diagnostics.values.is_empty() {
            return Err(std::mem::replace(&mut self.diagnostics, Diagnostics::new()).finish());
        }

        let mut modules = Vec::with_capacity(self.modules.len());
        for module_index in 0..self.modules.len() {
            let module = self.lower_module(module_index);
            modules.push(module);
        }
        if !self.diagnostics.values.is_empty() {
            return Err(std::mem::replace(&mut self.diagnostics, Diagnostics::new()).finish());
        }
        Ok(SemanticProject { modules })
    }

    fn index_modules(&mut self) {
        self.module_dependencies = vec![BTreeSet::new(); self.modules.len()];
        self.imports = vec![BTreeMap::new(); self.modules.len()];
        let modules = self.modules.clone();
        for (index, module) in modules.iter().enumerate() {
            if module.id.segments.is_empty() {
                continue;
            }
            if let Some(previous) = self.module_by_id.insert(module.id.clone(), index) {
                self.diagnostics.push(
                    module,
                    module.file.module.span.clone(),
                    format!(
                        "duplicate module `{}` (already defined by source {})",
                        module.id.as_string(),
                        previous + 1
                    ),
                );
            }
            if module
                .id
                .segments
                .iter()
                .any(|segment| !valid_snake(segment))
            {
                self.diagnostics.push(
                    module,
                    module.file.module.path.span.clone(),
                    "module path segments must use snake_case",
                );
            }
        }
        let ids: Vec<(usize, ModuleId)> = modules
            .iter()
            .enumerate()
            .filter(|(_, module)| !module.id.segments.is_empty())
            .map(|(i, module)| (i, module.id.clone()))
            .collect();
        for (i, left) in &ids {
            for (j, right) in &ids {
                if i == j || left == right {
                    continue;
                }
                if is_module_prefix(left, right) {
                    let module = &modules[*j];
                    self.diagnostics.push(
                        module,
                        module.file.module.path.span.clone(),
                        format!(
                            "module `{}` is a strict prefix of `{}`",
                            left.as_string(),
                            right.as_string()
                        ),
                    );
                }
            }
        }
    }

    fn index_declarations(&mut self) {
        let modules = self.modules.clone();
        for (module_index, module) in modules.iter().enumerate() {
            for (declaration_index, declaration) in module.file.declarations.iter().enumerate() {
                let (name, kind) = match declaration {
                    Declaration::Alias(value) => (&value.name, DeclKind::Alias),
                    Declaration::Newtype(value) => (&value.name, DeclKind::Newtype),
                    Declaration::Struct(value) => (&value.name, DeclKind::Struct),
                    Declaration::Enum(value) => (&value.name, DeclKind::Enum),
                    Declaration::Trait(value) => (&value.name, DeclKind::Function),
                    Declaration::Const(value) => (&value.name, DeclKind::Const),
                    Declaration::Function(value) => (&value.name, DeclKind::Function),
                };
                let symbol = SymbolId::new(module.id.clone(), name.clone());
                let span = declaration.span().clone();
                if self.declarations.contains_key(&symbol) {
                    self.diagnostics.push(
                        module,
                        span,
                        format!("duplicate declaration `{}`", symbol.as_string()),
                    );
                } else {
                    self.declarations.insert(
                        symbol,
                        DeclInfo {
                            module_index,
                            declaration_index,
                            kind,
                            span,
                        },
                    );
                }
                self.validate_decl_name(module, name, kind, declaration.span().clone());
            }
        }
    }

    fn validate_decl_name(&mut self, module: &ModuleInput, name: &str, kind: DeclKind, span: Span) {
        let valid = match kind {
            DeclKind::Alias | DeclKind::Newtype | DeclKind::Struct | DeclKind::Enum => {
                valid_type_name(name)
            }
            DeclKind::Const => valid_const_name(name),
            DeclKind::Function => valid_snake(name),
        };
        if !valid {
            self.diagnostics.push(
                module,
                span.clone(),
                format!("invalid name `{name}` for declaration"),
            );
        }
        if primitive_name(name).is_some() || matches!(name, "Option" | "Result") {
            self.diagnostics.push(
                module,
                span,
                format!("declaration `{name}` collides with a prelude type"),
            );
        }
    }

    fn validate_imports(&mut self) {
        for module_index in 0..self.modules.len() {
            let module = self.modules[module_index].clone();
            let mut first_declaration = None;
            for declaration in &module.file.declarations {
                first_declaration = Some(declaration.span().start);
                break;
            }
            for use_decl in &module.file.uses {
                if let Some(first) = first_declaration {
                    if use_decl.span.start > first {
                        self.diagnostics.push(
                            &module,
                            use_decl.span.clone(),
                            "imports must form one contiguous block immediately after the module declaration",
                        );
                    }
                }
                let segments = &use_decl.path.segments;
                match &use_decl.names {
                    None => {
                        if segments.len() < 2 {
                            self.diagnostics.push(
                                &module,
                                use_decl.span.clone(),
                                "a single import must name a public type declaration",
                            );
                            continue;
                        }
                        let module_id = ModuleId::new(segments[..segments.len() - 1].to_vec());
                        let name = segments.last().cloned().unwrap_or_default();
                        self.add_import(
                            module_index,
                            &module,
                            use_decl.span.clone(),
                            module_id,
                            name,
                        );
                    }
                    Some(names) => {
                        if segments.is_empty() || names.is_empty() {
                            self.diagnostics.push(
                                &module,
                                use_decl.span.clone(),
                                "grouped imports require a module prefix and at least one name",
                            );
                            continue;
                        }
                        let module_id = ModuleId::new(segments.clone());
                        for name in names {
                            self.add_import(
                                module_index,
                                &module,
                                use_decl.span.clone(),
                                module_id.clone(),
                                name.clone(),
                            );
                        }
                    }
                }
            }
        }
    }

    fn add_import(
        &mut self,
        module_index: usize,
        module: &ModuleInput,
        span: Span,
        target_module: ModuleId,
        name: String,
    ) {
        let Some(&target_module_index) = self.module_by_id.get(&target_module) else {
            self.diagnostics.push(
                module,
                span,
                format!("unknown imported module `{}`", target_module.as_string()),
            );
            return;
        };
        self.module_dependencies[module_index].insert(target_module_index);
        let target = SymbolId::new(target_module.clone(), name.clone());
        let Some(info) = self.declarations.get(&target).cloned() else {
            self.diagnostics.push(
                module,
                span,
                format!("unknown imported declaration `{}`", target.as_string()),
            );
            return;
        };
        if !info.kind.is_type() {
            self.diagnostics.push(
                module,
                span,
                format!(
                    "import `{}` does not name a public type declaration",
                    target.as_string()
                ),
            );
            return;
        }
        if let Some(previous) = self.imports[module_index].get(&name) {
            if previous != &target {
                self.diagnostics
                    .push(module, span, format!("ambiguous imported name `{name}`"));
            } else {
                self.diagnostics.push(
                    module,
                    span,
                    format!("duplicate import `{}`", target.as_string()),
                );
            }
            return;
        }
        if self
            .declarations
            .contains_key(&SymbolId::new(module.id.clone(), name.clone()))
        {
            self.diagnostics.push(
                module,
                span,
                format!("import `{name}` collides with a local declaration"),
            );
            return;
        }
        self.imports[module_index].insert(name, target);
    }

    fn validate_module_cycles(&mut self) {
        let mut state = vec![0u8; self.modules.len()];
        let mut stack = Vec::new();
        for index in 0..self.modules.len() {
            self.visit_module(index, &mut state, &mut stack);
        }
    }

    fn visit_module(&mut self, index: usize, state: &mut [u8], stack: &mut Vec<usize>) {
        if state[index] == 2 {
            return;
        }
        if state[index] == 1 {
            if let Some(module) = self.modules.get(index).cloned() {
                self.diagnostics.push(
                    &module,
                    module.file.module.span.clone(),
                    "cyclic module import/reference dependency",
                );
            }
            return;
        }
        state[index] = 1;
        stack.push(index);
        let deps: Vec<usize> = self.module_dependencies[index].iter().copied().collect();
        for dep in deps {
            self.visit_module(dep, state, stack);
        }
        stack.pop();
        state[index] = 2;
    }

    fn validate_declaration_shapes(&mut self) {
        for module_index in 0..self.modules.len() {
            let module = self.modules[module_index].clone();
            for declaration in &module.file.declarations {
                match declaration {
                    Declaration::Alias(value) => {
                        self.validate_generics(&module, module_index, &[], &value.target);
                        self.collect_type_dependencies(module_index, &value.target, &value.span);
                    }
                    Declaration::Newtype(value) => {
                        self.collect_type_dependencies(
                            module_index,
                            &value.underlying,
                            &value.span,
                        );
                        if let Some(refinement) = &value.where_clause {
                            self.validate_expression(module_index, refinement, &module);
                        }
                    }
                    Declaration::Struct(value) => {
                        self.validate_generic_list(&module, module_index, &value.generics);
                        let mut names = BTreeSet::new();
                        for field in &value.fields {
                            if !valid_snake(&field.name) {
                                self.diagnostics.push(
                                    &module,
                                    field.span.clone(),
                                    format!("invalid field name `{}`", field.name),
                                );
                            }
                            if !names.insert(field.name.clone()) {
                                self.diagnostics.push(
                                    &module,
                                    field.span.clone(),
                                    format!("duplicate field `{}`", field.name),
                                );
                            }
                            self.collect_type_dependencies(module_index, &field.ty, &field.span);
                            if let Some(default) = &field.default {
                                let ty = self.resolve_type(module_index, &field.ty);
                                self.resolve_const_expr(module_index, default, &ty);
                            }
                        }
                    }
                    Declaration::Enum(value) => {
                        self.validate_generic_list(&module, module_index, &value.generics);
                        let mut names = BTreeSet::new();
                        for variant in &value.variants {
                            if !valid_type_name(&variant.name) {
                                self.diagnostics.push(
                                    &module,
                                    variant.span.clone(),
                                    format!("invalid enum variant name `{}`", variant.name),
                                );
                            }
                            if !names.insert(variant.name.clone()) {
                                self.diagnostics.push(
                                    &module,
                                    variant.span.clone(),
                                    format!("duplicate enum variant `{}`", variant.name),
                                );
                            }
                            let mut parameter_names = BTreeSet::new();
                            for parameter in &variant.parameters {
                                if !valid_snake(&parameter.name) {
                                    self.diagnostics.push(
                                        &module,
                                        parameter.span.clone(),
                                        format!(
                                            "invalid variant parameter name `{}`",
                                            parameter.name
                                        ),
                                    );
                                }
                                if !parameter_names.insert(parameter.name.clone()) {
                                    self.diagnostics.push(
                                        &module,
                                        parameter.span.clone(),
                                        format!("duplicate variant parameter `{}`", parameter.name),
                                    );
                                }
                                self.collect_type_dependencies(
                                    module_index,
                                    &parameter.ty,
                                    &parameter.span,
                                );
                            }
                        }
                    }
                    Declaration::Trait(value) => {
                        self.validate_generic_list(&module, module_index, &value.generics);
                        for method in &value.methods {
                            for parameter in &method.parameters {
                                self.collect_type_dependencies(
                                    module_index,
                                    &parameter.ty,
                                    &parameter.span,
                                );
                            }
                            self.collect_type_dependencies(
                                module_index,
                                &method.return_type,
                                &method.span,
                            );
                        }
                    }
                    Declaration::Const(value) => {
                        self.collect_type_dependencies(module_index, &value.ty, &value.span);
                        let ty = self.resolve_type(module_index, &value.ty);
                        self.resolve_const_expr(module_index, &value.value, &ty);
                    }
                    Declaration::Function(value) => {
                        let mut names = BTreeSet::new();
                        for parameter in &value.parameters {
                            if !valid_snake(&parameter.name) {
                                self.diagnostics.push(
                                    &module,
                                    parameter.span.clone(),
                                    format!("invalid parameter name `{}`", parameter.name),
                                );
                            }
                            if !names.insert(parameter.name.clone()) {
                                self.diagnostics.push(
                                    &module,
                                    parameter.span.clone(),
                                    format!("duplicate parameter `{}`", parameter.name),
                                );
                            }
                            self.collect_type_dependencies(
                                module_index,
                                &parameter.ty,
                                &parameter.span,
                            );
                        }
                        self.collect_type_dependencies(
                            module_index,
                            &value.return_type,
                            &value.span,
                        );
                        if let FunctionBody::Clauses { clauses, .. } = &value.body {
                            for clause in clauses {
                                match &clause.kind {
                                    ClauseKind::Documentation(_) => {}
                                    ClauseKind::Requires { condition }
                                    | ClauseKind::Ensures { condition, .. } => {
                                        self.validate_expression(module_index, condition, &module);
                                    }
                                    ClauseKind::Error { error, when } => {
                                        let enum_path = if error.segments.len() >= 2 {
                                            ast::QualifiedName::new(
                                                error.span.clone(),
                                                error.segments[..error.segments.len() - 1].to_vec(),
                                            )
                                        } else {
                                            error.clone()
                                        };
                                        let Some(symbol) = self.resolve_reference(
                                            module_index,
                                            &enum_path,
                                            &clause.span,
                                            true,
                                        ) else {
                                            continue;
                                        };
                                        if !self.is_enum(&symbol) {
                                            self.diagnostics.push(
                                                &module,
                                                error.span.clone(),
                                                "error clause must name an enum variant",
                                            );
                                        }
                                        if let Some(when) = when {
                                            self.validate_expression(module_index, when, &module);
                                        }
                                    }
                                    ClauseKind::Effects { effects } => {
                                        for effect in effects {
                                            if effect.segments.is_empty() {
                                                self.diagnostics.push(
                                                    &module,
                                                    effect.span.clone(),
                                                    "effect name cannot be empty",
                                                );
                                            }
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    }

    fn validate_generic_list(
        &mut self,
        module: &ModuleInput,
        module_index: usize,
        generics: &[ast::GenericParam],
    ) {
        let mut names = BTreeSet::new();
        for generic in generics {
            if !names.insert(generic.name.clone()) {
                self.diagnostics.push(
                    module,
                    generic.span.clone(),
                    format!("duplicate generic parameter `{}`", generic.name),
                );
            }
            for bound in &generic.bounds {
                self.collect_type_dependencies(module_index, bound, &generic.span);
            }
        }
    }

    fn validate_generics(
        &mut self,
        _module: &ModuleInput,
        module_index: usize,
        _generics: &[ast::GenericParam],
        ty: &ast::Type,
    ) {
        self.collect_type_dependencies(module_index, ty, &ty.span);
    }
    fn validate_expression(
        &mut self,
        module_index: usize,
        expression: &Expr,
        module: &ModuleInput,
    ) {
        match &expression.kind {
            ExprKind::Literal(_) => {}
            ExprKind::Parenthesized(inner) => self.validate_expression(module_index, inner, module),
            ExprKind::Unary { operand, .. } => {
                self.validate_expression(module_index, operand, module)
            }
            ExprKind::Binary { left, right, .. } => {
                self.validate_expression(module_index, left, module);
                self.validate_expression(module_index, right, module);
            }
            ExprKind::Comparison { first, rest } => {
                self.validate_expression(module_index, first, module);
                for (_, value) in rest {
                    self.validate_expression(module_index, value, module);
                }
            }
            ExprKind::Name(path) => {
                self.resolve_reference(module_index, path, &expression.span, false);
            }
            ExprKind::Field { base, .. } => self.validate_expression(module_index, base, module),
            ExprKind::Unit => {
                self.diagnostics.push(
                    module,
                    expression.span.clone(),
                    "contract condition must be boolean",
                );
            }
        }
    }
    fn collect_type_dependencies(&mut self, module_index: usize, ty: &ast::Type, span: &Span) {
        let Some(symbol) = self.resolve_reference(module_index, &ty.path, span, false) else {
            for argument in &ty.arguments {
                if let TypeArgKind::Type(inner) = &argument.kind {
                    self.collect_type_dependencies(module_index, inner, &argument.span);
                }
            }
            return;
        };
        if let Some(target_module_index) =
            self.declarations.get(&symbol).map(|info| info.module_index)
        {
            self.declaration_dependencies
                .entry(symbol.clone())
                .or_default();
            let current = self.current_decl_for_span(module_index, span);
            if let Some(current) = current {
                self.declaration_dependencies
                    .entry(current)
                    .or_default()
                    .insert(symbol.clone());
            }
            if target_module_index != module_index {
                self.module_dependencies[module_index].insert(target_module_index);
            }
        }
        for argument in &ty.arguments {
            if let TypeArgKind::Type(inner) = &argument.kind {
                self.collect_type_dependencies(module_index, inner, &argument.span);
            }
        }
    }

    fn current_decl_for_span(&self, module_index: usize, span: &Span) -> Option<SymbolId> {
        self.modules[module_index]
            .file
            .declarations
            .iter()
            .find(|decl| decl.span().start <= span.start && decl.span().end >= span.end)
            .and_then(|decl| {
                let name = match decl {
                    Declaration::Alias(v) => &v.name,
                    Declaration::Newtype(v) => &v.name,
                    Declaration::Struct(v) => &v.name,
                    Declaration::Enum(v) => &v.name,
                    Declaration::Trait(v) => &v.name,
                    Declaration::Const(v) => &v.name,
                    Declaration::Function(v) => &v.name,
                };
                Some(SymbolId::new(
                    self.modules[module_index].id.clone(),
                    name.clone(),
                ))
            })
    }

    fn resolve_reference(
        &mut self,
        module_index: usize,
        path: &ast::QualifiedName,
        span: &Span,
        report: bool,
    ) -> Option<SymbolId> {
        let name = path.segments.last()?.clone();
        let symbol = if path.segments.len() == 1 {
            self.imports
                .get(module_index)
                .and_then(|imports| imports.get(&name).cloned())
                .or_else(|| {
                    let local = SymbolId::new(self.modules[module_index].id.clone(), name.clone());
                    self.declarations.contains_key(&local).then_some(local)
                })
        } else {
            let target_module = ModuleId::new(path.segments[..path.segments.len() - 1].to_vec());
            let candidate = SymbolId::new(target_module, name.clone());
            self.declarations
                .contains_key(&candidate)
                .then_some(candidate)
        };
        if symbol.is_none() && report {
            self.diagnostics.push(
                &self.modules[module_index],
                span.clone(),
                format!("unknown type or declaration `{}`", path.segments.join(".")),
            );
        }
        symbol
    }

    fn validate_declaration_cycles(&mut self) {
        let keys: Vec<SymbolId> = self
            .declarations
            .iter()
            .filter_map(|(symbol, info)| info.kind.is_type().then_some(symbol.clone()))
            .collect();
        let mut state = HashMap::<SymbolId, u8>::new();
        for key in keys {
            self.visit_declaration(&key, &mut state);
        }
    }

    fn visit_declaration(&mut self, symbol: &SymbolId, state: &mut HashMap<SymbolId, u8>) {
        if state.get(symbol).copied() == Some(2) {
            return;
        }
        if state.get(symbol).copied() == Some(1) {
            if let Some(info) = self.declarations.get(symbol) {
                let module = self.modules[info.module_index].clone();
                self.diagnostics.push(
                    &module,
                    info.span.clone(),
                    format!("cyclic type reference involving `{}`", symbol.as_string()),
                );
            }
            return;
        }
        state.insert(symbol.clone(), 1);
        let deps: Vec<SymbolId> = self
            .declaration_dependencies
            .get(symbol)
            .map(|set| set.iter().cloned().collect())
            .unwrap_or_default();
        for dependency in deps {
            if self
                .declarations
                .get(&dependency)
                .map(|info| info.kind.is_type())
                .unwrap_or(false)
            {
                self.visit_declaration(&dependency, state);
            }
        }
        state.insert(symbol.clone(), 2);
    }

    fn lower_module(&mut self, module_index: usize) -> SemanticModule {
        let module = self.modules[module_index].clone();
        let imports = self.imports[module_index]
            .iter()
            .map(|(name, symbol)| SemanticImport {
                span: module
                    .file
                    .uses
                    .iter()
                    .find(|use_decl| use_decl.path.segments.last() == Some(name))
                    .map(|use_decl| use_decl.span.clone())
                    .unwrap_or_else(|| module.file.module.span.clone()),
                symbol: symbol.clone(),
                name: name.clone(),
            })
            .collect();
        let declarations = module
            .file
            .declarations
            .iter()
            .map(|declaration| self.lower_declaration(module_index, declaration))
            .collect();
        SemanticModule {
            source: module.source,
            id: module.id,
            imports,
            declarations,
        }
    }

    fn lower_declaration(
        &mut self,
        module_index: usize,
        declaration: &Declaration,
    ) -> SemanticDeclaration {
        let module = self.modules[module_index].clone();
        match declaration {
            Declaration::Alias(value) => SemanticDeclaration::Alias(SemanticAlias {
                id: SymbolId::new(module.id.clone(), value.name.clone()),
                span: value.span.clone(),
                doc: value.doc.as_ref().map(doc),
                target: self.resolve_type(module_index, &value.target),
            }),
            Declaration::Newtype(value) => SemanticDeclaration::Newtype(SemanticNewtype {
                id: SymbolId::new(module.id.clone(), value.name.clone()),
                span: value.span.clone(),
                doc: value.doc.as_ref().map(doc),
                underlying: self.resolve_type(module_index, &value.underlying),
            }),
            Declaration::Struct(value) => {
                let fields = value
                    .fields
                    .iter()
                    .map(|field| SemanticField {
                        span: field.span.clone(),
                        name: field.name.clone(),
                        ty: self.resolve_type(module_index, &field.ty),
                        default: field.default.as_ref().and_then(|default| {
                            let ty = self.resolve_type(module_index, &field.ty);
                            self.resolve_const_expr(module_index, default, &ty)
                        }),
                    })
                    .collect();
                SemanticDeclaration::Struct(SemanticStruct {
                    id: SymbolId::new(module.id.clone(), value.name.clone()),
                    span: value.span.clone(),
                    doc: value.doc.as_ref().map(doc),
                    fields,
                })
            }
            Declaration::Enum(value) => {
                let enum_id = SymbolId::new(module.id.clone(), value.name.clone());
                let variants = value
                    .variants
                    .iter()
                    .map(|variant| SemanticVariant {
                        id: SymbolId::new(
                            enum_id.module.clone(),
                            format!("{}.{}", enum_id.name, variant.name),
                        ),
                        span: variant.span.clone(),
                        name: variant.name.clone(),
                        parameters: variant
                            .parameters
                            .iter()
                            .map(|parameter| SemanticParameter {
                                span: parameter.span.clone(),
                                name: parameter.name.clone(),
                                ty: self.resolve_type(module_index, &parameter.ty),
                            })
                            .collect(),
                    })
                    .collect();
                SemanticDeclaration::Enum(SemanticEnum {
                    id: enum_id,
                    span: value.span.clone(),
                    doc: value.doc.as_ref().map(doc),
                    variants,
                })
            }
            Declaration::Const(value) => {
                let ty = self.resolve_type(module_index, &value.ty);
                let semantic_value = self
                    .resolve_const_expr(module_index, &value.value, &ty)
                    .unwrap_or(SemanticValue::Unit);
                SemanticDeclaration::Const(SemanticConst {
                    id: SymbolId::new(module.id.clone(), value.name.clone()),
                    span: value.span.clone(),
                    doc: value.doc.as_ref().map(doc),
                    ty,
                    value: semantic_value,
                })
            }
            Declaration::Function(value) => SemanticDeclaration::Function(SemanticFunction {
                id: SymbolId::new(module.id.clone(), value.name.clone()),
                span: value.span.clone(),
                doc: None,
                parameters: value
                    .parameters
                    .iter()
                    .map(|parameter| SemanticParameter {
                        span: parameter.span.clone(),
                        name: parameter.name.clone(),
                        ty: self.resolve_type(module_index, &parameter.ty),
                    })
                    .collect(),
                return_type: self.resolve_type(module_index, &value.return_type),
            }),
            Declaration::Trait(value) => SemanticDeclaration::Function(SemanticFunction {
                id: SymbolId::new(module.id.clone(), value.name.clone()),
                span: value.span.clone(),
                doc: value.doc.as_ref().map(doc),
                parameters: Vec::new(),
                return_type: ResolvedType::Primitive(PrimitiveType::Unit),
            }),
        }
    }

    fn resolve_type(&mut self, module_index: usize, ty: &ast::Type) -> ResolvedType {
        let name = ty.path.segments.last().cloned().unwrap_or_default();
        if ty.path.segments.len() == 1 {
            if let Some(primitive) = primitive_name(&name) {
                self.check_arity(module_index, ty, 0, &name);
                return ResolvedType::Primitive(primitive);
            }
            if matches!(name.as_str(), "F32" | "JsonValue" | "Never") {
                self.check_arity(module_index, ty, 0, &name);
                return ResolvedType::Primitive(PrimitiveType::Unit);
            }
            if matches!(name.as_str(), "List" | "Set" | "Option") {
                self.check_arity(module_index, ty, 1, &name);
                if let Some(inner) = ty.arguments.first().and_then(type_argument) {
                    let _ = self.resolve_type(module_index, inner);
                }
                return ResolvedType::Primitive(PrimitiveType::Unit);
            }
            if name == "Map" || name == "Tuple2" {
                self.check_arity(module_index, ty, 2, &name);
                for argument in &ty.arguments {
                    if let Some(inner) = type_argument(argument) {
                        let _ = self.resolve_type(module_index, inner);
                    }
                }
                return ResolvedType::Primitive(PrimitiveType::Unit);
            }
            if name == "Result" {
                self.check_arity(module_index, ty, 2, "Result");
                let ok = ty
                    .arguments
                    .first()
                    .and_then(type_argument)
                    .map(|inner| self.resolve_type(module_index, inner))
                    .unwrap_or(ResolvedType::Primitive(PrimitiveType::Unit));
                let error_type = ty
                    .arguments
                    .get(1)
                    .and_then(type_argument)
                    .map(|inner| self.resolve_type(module_index, inner));
                let error_symbol = error_type.as_ref().and_then(|resolved| match resolved {
                    ResolvedType::Named(symbol) => Some(symbol.clone()),
                    _ => None,
                });
                if error_symbol
                    .as_ref()
                    .map(|symbol| !self.is_enum(symbol))
                    .unwrap_or(true)
                {
                    self.diagnostics.push(
                        &self.modules[module_index],
                        ty.span.clone(),
                        "Result error type must resolve to an enum declaration",
                    );
                }
                return ResolvedType::Result {
                    ok: Box::new(ok),
                    error: error_symbol
                        .unwrap_or_else(|| SymbolId::new(ModuleId::new(Vec::new()), "<error>")),
                };
            }
        }
        let Some(symbol) = self.resolve_reference(module_index, &ty.path, &ty.span, true) else {
            return ResolvedType::Primitive(PrimitiveType::Unit);
        };
        self.check_arity(module_index, ty, 0, &symbol.as_string());
        let Some(info) = self.declarations.get(&symbol).cloned() else {
            return ResolvedType::Primitive(PrimitiveType::Unit);
        };
        if !info.kind.is_type() {
            self.diagnostics.push(
                &self.modules[module_index],
                ty.span.clone(),
                format!("`{}` is not a type declaration", symbol.as_string()),
            );
            return ResolvedType::Primitive(PrimitiveType::Unit);
        }
        if info.kind == DeclKind::Alias {
            if !self.resolving.insert(symbol.clone()) {
                return ResolvedType::Primitive(PrimitiveType::Unit);
            }
            let target =
                match &self.modules[info.module_index].file.declarations[info.declaration_index] {
                    Declaration::Alias(alias) => Some(alias.target.clone()),
                    _ => None,
                };
            let target = target
                .map(|target| self.resolve_type(info.module_index, &target))
                .unwrap_or(ResolvedType::Primitive(PrimitiveType::Unit));
            self.resolving.remove(&symbol);
            target
        } else {
            ResolvedType::Named(symbol)
        }
    }

    fn check_arity(&mut self, module_index: usize, ty: &ast::Type, expected: usize, name: &str) {
        if ty.arguments.len() != expected {
            self.diagnostics.push(
                &self.modules[module_index],
                ty.span.clone(),
                format!(
                    "type constructor `{name}` expects {expected} argument(s), got {}",
                    ty.arguments.len()
                ),
            );
        }
        for argument in &ty.arguments {
            if !matches!(&argument.kind, TypeArgKind::Type(_)) {
                self.diagnostics.push(
                    &self.modules[module_index],
                    argument.span.clone(),
                    "string type arguments are unsupported in the constrained profile",
                );
            }
        }
    }

    fn is_enum(&self, symbol: &SymbolId) -> bool {
        self.declarations
            .get(symbol)
            .map(|info| {
                if info.kind == DeclKind::Enum {
                    true
                } else if info.kind == DeclKind::Alias {
                    match &self.modules[info.module_index].file.declarations[info.declaration_index]
                    {
                        Declaration::Alias(alias) => {
                            self.type_is_enum(info.module_index, &alias.target, &mut HashSet::new())
                        }
                        _ => false,
                    }
                } else {
                    false
                }
            })
            .unwrap_or(false)
    }

    fn type_is_enum(
        &self,
        module_index: usize,
        ty: &ast::Type,
        seen: &mut HashSet<SymbolId>,
    ) -> bool {
        let Some(path_name) = ty.path.segments.last() else {
            return false;
        };
        if ty.path.segments.len() == 1 && matches!(path_name.as_str(), "Option" | "Result") {
            return false;
        }
        let symbol = if ty.path.segments.len() == 1 {
            self.imports[module_index]
                .get(path_name)
                .cloned()
                .or_else(|| {
                    let local =
                        SymbolId::new(self.modules[module_index].id.clone(), path_name.clone());
                    self.declarations.contains_key(&local).then_some(local)
                })
        } else {
            let candidate = SymbolId::new(
                ModuleId::new(ty.path.segments[..ty.path.segments.len() - 1].to_vec()),
                path_name.clone(),
            );
            self.declarations
                .contains_key(&candidate)
                .then_some(candidate)
        };
        let Some(symbol) = symbol else {
            return false;
        };
        if !seen.insert(symbol.clone()) {
            return false;
        }
        let Some(info) = self.declarations.get(&symbol) else {
            return false;
        };
        if info.kind == DeclKind::Enum {
            return true;
        }
        if info.kind == DeclKind::Alias {
            if let Declaration::Alias(alias) =
                &self.modules[info.module_index].file.declarations[info.declaration_index]
            {
                return self.type_is_enum(info.module_index, &alias.target, seen);
            }
        }
        false
    }

    fn resolve_const_expr(
        &mut self,
        module_index: usize,
        value: &ConstExpr,
        expected: &ResolvedType,
    ) -> Option<SemanticValue> {
        match value {
            ConstExpr::Expression(expr) => self.resolve_literal_expr(module_index, expr, expected),
            ConstExpr::Constructor { span, .. } => {
                self.diagnostics.push(
                    &self.modules[module_index],
                    span.clone(),
                    "constructors are unsupported in literal constants",
                );
                None
            }
        }
    }

    fn resolve_literal_expr(
        &mut self,
        module_index: usize,
        expression: &Expr,
        expected: &ResolvedType,
    ) -> Option<SemanticValue> {
        match &expression.kind {
            ExprKind::Literal(literal) => match (&literal.kind, expected) {
                (LiteralKind::Bool(value), ResolvedType::Primitive(PrimitiveType::Bool)) => {
                    Some(SemanticValue::Bool(*value))
                }
                (LiteralKind::Integer(value), ResolvedType::Primitive(primitive))
                    if primitive.is_integer() =>
                {
                    let parsed = value.parse::<i128>().ok();
                    if parsed.is_none() || !primitive.integer_contains(parsed.unwrap()) {
                        self.diagnostics.push(
                            &self.modules[module_index],
                            literal.span.clone(),
                            format!("integer literal is out of range for {primitive:?}"),
                        );
                        None
                    } else {
                        Some(SemanticValue::Integer(value.clone()))
                    }
                }
                (LiteralKind::Float(value), ResolvedType::Primitive(PrimitiveType::F64)) => {
                    if value
                        .parse::<f64>()
                        .ok()
                        .filter(|number| number.is_finite())
                        .is_none()
                    {
                        self.diagnostics.push(
                            &self.modules[module_index],
                            literal.span.clone(),
                            "float literal must be a finite F64 value",
                        );
                        None
                    } else {
                        Some(SemanticValue::Float(value.clone()))
                    }
                }
                (LiteralKind::String(value), ResolvedType::Primitive(PrimitiveType::Str)) => {
                    Some(SemanticValue::String(value.clone()))
                }
                _ => {
                    self.diagnostics.push(
                        &self.modules[module_index],
                        literal.span.clone(),
                        "constant literal does not match its declared type",
                    );
                    None
                }
            },
            ExprKind::Unit if matches!(expected, ResolvedType::Primitive(PrimitiveType::Unit)) => {
                Some(SemanticValue::Unit)
            }
            ExprKind::Parenthesized(inner) => {
                self.resolve_literal_expr(module_index, inner, expected)
            }
            _ => {
                self.diagnostics.push(
                    &self.modules[module_index],
                    expression.span.clone(),
                    "constants must be typed literals",
                );
                None
            }
        }
    }
}

fn module_path(root: &Path, source: &Path) -> Result<Vec<String>, String> {
    let relative = if source.is_absolute() {
        source
            .strip_prefix(root)
            .map_err(|_| "source path is outside the supplied source root".to_owned())?
    } else if !root.as_os_str().is_empty() {
        source.strip_prefix(root).unwrap_or(source)
    } else {
        source
    };
    let mut components = Vec::new();
    for component in relative.components() {
        match component {
            Component::Normal(value) => components.push(value.to_string_lossy().into_owned()),
            Component::CurDir => return Err("source path contains `.`".to_owned()),
            Component::ParentDir => return Err("source path contains `..`".to_owned()),
            Component::RootDir | Component::Prefix(_) => {
                return Err("source path must be relative to the supplied source root".to_owned());
            }
        }
    }
    let Some(filename) = components.pop() else {
        return Err("source path must name a `.cott` file".to_owned());
    };
    if !filename.ends_with(".cott") || filename == ".cott" {
        return Err("source path must name a `.cott` file".to_owned());
    }
    let stem = filename.trim_end_matches(".cott");
    if stem.is_empty() {
        return Err("source path must name a nonempty `.cott` file".to_owned());
    }
    components.push(stem.to_owned());
    Ok(components)
}

fn is_module_prefix(prefix: &ModuleId, value: &ModuleId) -> bool {
    prefix.segments.len() < value.segments.len()
        && prefix
            .segments
            .iter()
            .zip(&value.segments)
            .all(|(left, right)| left == right)
}

fn valid_snake(value: &str) -> bool {
    let mut chars = value.chars();
    let Some(first) = chars.next() else {
        return false;
    };
    (first == '_' || first.is_ascii_lowercase())
        && chars.all(|ch| ch == '_' || ch.is_ascii_lowercase() || ch.is_ascii_digit())
        && value != "_"
}

fn valid_type_name(value: &str) -> bool {
    let mut chars = value.chars();
    let Some(first) = chars.next() else {
        return false;
    };
    first.is_ascii_uppercase() && chars.all(|ch| ch.is_ascii_alphanumeric())
}

fn valid_const_name(value: &str) -> bool {
    let mut chars = value.chars();
    let Some(first) = chars.next() else {
        return false;
    };
    (first.is_ascii_uppercase() || first == '_')
        && chars.all(|ch| ch == '_' || ch.is_ascii_uppercase() || ch.is_ascii_digit())
        && value != "_"
}

fn primitive_name(name: &str) -> Option<PrimitiveType> {
    Some(match name {
        "Bool" => PrimitiveType::Bool,
        "I8" => PrimitiveType::I8,
        "I16" => PrimitiveType::I16,
        "I32" => PrimitiveType::I32,
        "I64" => PrimitiveType::I64,
        "U8" => PrimitiveType::U8,
        "U16" => PrimitiveType::U16,
        "U32" => PrimitiveType::U32,
        "U64" => PrimitiveType::U64,
        "F64" => PrimitiveType::F64,
        "Str" => PrimitiveType::Str,
        "Bytes" => PrimitiveType::Bytes,
        "Unit" => PrimitiveType::Unit,
        _ => return None,
    })
}

fn type_argument(argument: &ast::TypeArg) -> Option<&ast::Type> {
    match &argument.kind {
        TypeArgKind::Type(ty) => Some(ty),
        TypeArgKind::String(_) => None,
    }
}

fn doc(value: &ast::DocBlock) -> SemanticDoc {
    SemanticDoc {
        span: value.span.clone(),
        text: value.text.clone(),
    }
}

impl PrimitiveType {
    fn is_integer(self) -> bool {
        matches!(
            self,
            Self::I8
                | Self::I16
                | Self::I32
                | Self::I64
                | Self::U8
                | Self::U16
                | Self::U32
                | Self::U64
        )
    }

    fn integer_contains(self, value: i128) -> bool {
        match self {
            Self::I8 => (-128..=127).contains(&value),
            Self::I16 => (-32_768..=32_767).contains(&value),
            Self::I32 => (-2_147_483_648..=2_147_483_647).contains(&value),
            Self::I64 => (-9_223_372_036_854_775_808..=9_223_372_036_854_775_807).contains(&value),
            Self::U8 => (0..=255).contains(&value),
            Self::U16 => (0..=65_535).contains(&value),
            Self::U32 => (0..=4_294_967_295).contains(&value),
            Self::U64 => (0..=18_446_744_073_709_551_615).contains(&value),
            _ => false,
        }
    }
}
