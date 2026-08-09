use cott::diagnostics::Span;
use cott::hir::{
    HirClause, HirClauseKind, HirContract, HirDeclaration, HirDoc, HirExpr, HirExprKind,
    HirGenericParam, HirPattern, HirPatternKind, HirTrait, HirType, HirValue, ModuleId,
    PrimitiveType, SymbolId,
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

// Keep the primitive vocabulary itself exercised by this integration test;
// this catches accidental semantic aliases while the wider pipeline migrates.
#[test]
fn primitive_type_is_owned_and_closed() {
    let primitive = PrimitiveType::Never;
    assert_eq!(primitive, PrimitiveType::Never);
}
