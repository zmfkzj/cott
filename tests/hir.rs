use std::path::Path;

use cott::compiler::{SourceFile, parse_project};
use cott::diagnostics::Span;
use cott::hir::{
    HirClause, HirClauseKind, HirContract, HirDeclaration, HirDoc, HirExpr, HirExprKind,
    HirGenericParam, HirPattern, HirPatternKind, HirTrait, HirType, HirValue, ModuleId,
    PrimitiveType, SymbolId, lower,
};

fn span() -> Span {
    Span::new(0, 1)
}

fn symbol(module: &ModuleId, name: &str) -> SymbolId {
    SymbolId::new(module.clone(), name)
}

#[test]
fn owned_hir_preserves_trait_bounds_types_contract_order_and_pattern_identity() {
    let at = span();
    let module = ModuleId::new(vec!["api".into(), "service".into()]);
    let trait_id = symbol(&module, "Renderable");
    let value_id = symbol(&module, "value");
    let result_id = symbol(&module, "ResultValue");

    let bounded = HirGenericParam {
        span: at.clone(),
        name: "T".into(),
        bounds: vec![HirType::Named {
            symbol: trait_id.clone(),
            args: vec![],
        }],
        source_order: 0,
    };
    let container = HirType::Map {
        key: Box::new(HirType::Primitive(PrimitiveType::Str)),
        value: Box::new(HirType::List {
            item: Box::new(HirType::TypeParameter { name: "T".into() }),
        }),
    };
    let bound_pattern = HirPattern {
        span: at.clone(),
        ty: HirType::Primitive(PrimitiveType::I32),
        kind: HirPatternKind::Binding {
            symbol: value_id.clone(),
            name: "value".into(),
        },
    };
    let expression = HirExpr {
        span: at.clone(),
        ty: HirType::Primitive(PrimitiveType::Bool),
        reference: None,
        kind: HirExprKind::Literal(HirValue::Bool(true)),
    };
    let contract = HirContract {
        clauses: vec![
            HirClause {
                clause_id: 7,
                span: at.clone(),
                kind: HirClauseKind::Requires {
                    expression: expression.clone(),
                },
            },
            HirClause {
                clause_id: 11,
                span: at.clone(),
                kind: HirClauseKind::Ensures {
                    pattern: Some(bound_pattern.clone()),
                    expression,
                },
            },
        ],
        effects: vec![],
    };
    let trait_decl = HirTrait {
        id: trait_id.clone(),
        span: at.clone(),
        doc: Some(HirDoc {
            span: at.clone(),
            text: "renders values".into(),
        }),
        generics: vec![bounded],
        methods: vec![],
        public: true,
        source_order: 0,
    };

    let declarations = vec![HirDeclaration::Trait(trait_decl)];
    assert!(matches!(declarations[0], HirDeclaration::Trait(_)));
    assert_eq!(
        container,
        HirType::Map {
            key: Box::new(HirType::Primitive(PrimitiveType::Str)),
            value: Box::new(HirType::List {
                item: Box::new(HirType::TypeParameter { name: "T".into() }),
            }),
        }
    );
    assert_eq!(
        contract
            .clauses
            .iter()
            .map(|clause| clause.clause_id)
            .collect::<Vec<_>>(),
        vec![7, 11]
    );
    assert_eq!(
        bound_pattern.kind,
        HirPatternKind::Binding {
            symbol: value_id,
            name: "value".into(),
        }
    );
    assert_eq!(result_id.as_string(), "api.service.ResultValue");
}

#[test]
fn direct_lowering_preserves_parsed_owned_structure_and_contracts() {
    let parsed = parse_project([SourceFile::new(
        "src/owned.cott",
        r#"module owned

enum Failure:
    Bad

struct Box[T, U]:
    values: List[T]
    entries: Map[Str, U]

fn inspect(value: I32, other: I32) -> I32:
    doc """inspects values"""
    requires value == other
    ensures value > 0
    error Failure.Bad when value == other
    effects [IO, Log.Write]
"#,
    )])
    .expect("owned fixture should parse");
    let project = lower(Path::new("src"), parsed).expect("owned fixture should lower");
    assert_eq!(project.modules.len(), 1);
    let module = &project.modules[0];
    assert_eq!(module.id.as_string(), "owned");
    assert_eq!(module.source_order, 0);
    assert_eq!(
        module
            .declarations
            .iter()
            .map(|declaration| declaration.id().as_string())
            .collect::<Vec<_>>(),
        ["owned.Failure", "owned.Box", "owned.inspect"]
    );

    let HirDeclaration::Enum(failure) = &module.declarations[0] else {
        panic!("expected failure enum");
    };
    assert_eq!(failure.source_order, 0);
    assert_eq!(failure.variants[0].symbol.as_string(), "owned.Failure.Bad");

    let HirDeclaration::Struct(container) = &module.declarations[1] else {
        panic!("expected generic container");
    };
    assert_eq!(
        container
            .generics
            .iter()
            .map(|generic| (generic.name.as_str(), generic.source_order))
            .collect::<Vec<_>>(),
        [("T", 0), ("U", 1)]
    );
    assert_eq!(
        container
            .fields
            .iter()
            .map(|field| field.source_order)
            .collect::<Vec<_>>(),
        [0, 1]
    );
    assert_eq!(
        container.fields[0].ty,
        HirType::List {
            item: Box::new(HirType::TypeParameter { name: "T".into() })
        }
    );
    assert_eq!(
        container.fields[1].ty,
        HirType::Map {
            key: Box::new(HirType::Primitive(PrimitiveType::Str)),
            value: Box::new(HirType::TypeParameter { name: "U".into() })
        }
    );

    let HirDeclaration::Function(function) = &module.declarations[2] else {
        panic!("expected inspect function");
    };
    assert_eq!(function.source_order, 2);
    assert_eq!(function.id.as_string(), "owned.inspect");
    assert_eq!(
        function
            .parameters
            .iter()
            .map(|parameter| (parameter.name.as_str(), parameter.source_order))
            .collect::<Vec<_>>(),
        [("value", 0), ("other", 1)]
    );
    assert_eq!(
        function.parameters[0].ty,
        HirType::Primitive(PrimitiveType::I32)
    );
    assert_eq!(function.return_type, HirType::Primitive(PrimitiveType::I32));
    assert_eq!(
        function.doc.as_ref().map(|doc| doc.text.as_str()),
        Some("inspects values")
    );
    assert_eq!(
        function
            .contract
            .clauses
            .iter()
            .map(|clause| clause.clause_id)
            .collect::<Vec<_>>(),
        [1, 2, 3]
    );
    assert!(matches!(
        &function.contract.clauses[0].kind,
        HirClauseKind::Requires { expression }
            if expression.ty == HirType::Primitive(PrimitiveType::Bool)
    ));
    assert!(matches!(
        &function.contract.clauses[1].kind,
        HirClauseKind::Ensures { pattern: None, expression }
            if expression.ty == HirType::Primitive(PrimitiveType::Bool)
    ));
    assert!(matches!(
        &function.contract.clauses[2].kind,
        HirClauseKind::Error {
            variant,
            priority: None,
            when: Some(expression),
        } if variant.as_string() == "owned.Failure.Bad"
            && expression.ty == HirType::Primitive(PrimitiveType::Bool)
    ));
    assert_eq!(
        function
            .contract
            .effects
            .iter()
            .map(|effect| (effect.key.as_str(), effect.source_order))
            .collect::<Vec<_>>(),
        [("IO", 0), ("Log.Write", 1)]
    );
}
#[test]
fn direct_lowering_accepts_numeric_comparison_contracts() {
    let parsed = parse_project([SourceFile::new(
        "src/comparison.cott",
        r#"module comparison

fn check(value: I32, other: I32) -> Unit:
    requires value < other
"#,
    )])
    .expect("comparison fixture should parse");
    let project = lower(Path::new("src"), parsed).expect("numeric comparison should lower");
    let HirDeclaration::Function(function) = &project.modules[0].declarations[0] else {
        panic!("expected check function");
    };
    assert!(matches!(
        &function.contract.clauses[0].kind,
        HirClauseKind::Requires { expression }
            if expression.ty == HirType::Primitive(PrimitiveType::Bool)
    ));
}

#[test]
fn direct_lowering_rejects_nonlogical_binary_contracts() {
    let parsed = parse_project([SourceFile::new(
        "src/nonlogical.cott",
        r#"module nonlogical

fn check(flag: Bool) -> Unit:
    requires flag + 1
"#,
    )])
    .expect("nonlogical fixture should parse");
    let errors = lower(Path::new("src"), parsed).expect_err("nonlogical contract must fail");
    assert!(!errors.is_empty());
}

#[test]
fn direct_lowering_rejects_generic_comparison_contracts() {
    let parsed = parse_project([SourceFile::new(
        "src/generic.cott",
        r#"module generic

fn check[T](value: T) -> Unit:
    requires value < value
"#,
    )])
    .expect("generic fixture should parse");
    let errors = lower(Path::new("src"), parsed).expect_err("generic comparison must fail");
    assert!(!errors.is_empty());
}

#[test]
fn primitive_type_is_owned_and_closed() {
    let primitive = PrimitiveType::Never;
    assert_eq!(primitive, PrimitiveType::Never);
}
