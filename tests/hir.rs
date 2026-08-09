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

fn inspect(value: I32, other: I32) -> Result[I32, Failure]:
    doc """inspects values"""
    requires value == other
    ensures value > 0
    error Failure.Bad when value == other
    effects [network, database.write]
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
    assert_eq!(
        function.return_type,
        HirType::Result {
            ok: Box::new(HirType::Primitive(PrimitiveType::I32)),
            error: Box::new(HirType::Named {
                symbol: symbol(&module.id, "Failure"),
                args: Vec::new(),
            }),
        }
    );
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
        [("network", 0), ("database.write", 1)]
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
fn numeric_literals_take_operand_context_and_widths_must_match() {
    let parsed = parse_project([SourceFile::new(
        "src/numeric_context.cott",
        "module numeric_context\n\nnewtype Probability(F32)\n    where 0.0 <= self <= 1.0\n\nfn check(value: F32) -> Unit:\n    requires value + 0.5 <= 1.0\n",
    )])
    .expect("numeric context fixture should parse");
    let project =
        lower(Path::new("src"), parsed).expect("numeric literals should take F32 context");
    let HirDeclaration::Newtype(probability) = &project.modules[0].declarations[0] else {
        panic!("expected newtype");
    };
    let HirExprKind::ComparisonChain { operands, .. } =
        &probability.refinement.as_ref().expect("refinement").kind
    else {
        panic!("expected comparison");
    };
    assert!(
        operands
            .iter()
            .all(|operand| operand.ty == HirType::Primitive(PrimitiveType::F32))
    );

    for source in [
        "module invalid\n\nfn check(left: I32, right: U32) -> Unit:\n    requires left < right\n",
        "module invalid\n\nfn check() -> Unit:\n    requires 1 < 2\n",
        "module invalid\n\nfn check(value: I32) -> Unit:\n    requires value % (1 - 1) == value\n",
    ] {
        let parsed = parse_project([SourceFile::new("src/invalid.cott", source)])
            .expect("invalid semantic fixture should parse");
        assert!(lower(Path::new("src"), parsed).is_err());
    }
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

#[test]
fn path_is_primitive_and_len_is_u64() {
    let parsed = parse_project([SourceFile::new(
        "src/path_contract.cott",
        "module path_contract\n\nfn inspect(path: Path, data: Bytes) -> Unit:\n    requires data.len == data.len\n",
    )])
    .expect("Path and len fixture should parse");
    let project = lower(Path::new("src"), parsed).expect("Path and len fixture should lower");
    let HirDeclaration::Function(function) = &project.modules[0].declarations[0] else {
        panic!("expected inspect function");
    };
    assert_eq!(
        function.parameters[0].ty,
        HirType::Primitive(PrimitiveType::Path)
    );
    let HirClauseKind::Requires { expression } = &function.contract.clauses[0].kind else {
        panic!("expected requires clause");
    };
    let HirExprKind::ComparisonChain { operands, .. } = &expression.kind else {
        panic!("expected comparison chain");
    };
    assert!(operands.iter().all(|operand| {
        operand.ty == HirType::Primitive(PrimitiveType::U64)
            && matches!(operand.kind, HirExprKind::Len { .. })
    }));
}

#[test]
fn set_items_and_map_keys_must_be_hash_stable() {
    let parsed = parse_project([SourceFile::new(
        "src/keys.cott",
        "module keys\n\nstruct Bad:\n    values: Set[F32]\n    entries: Map[List[U8], Str]\n",
    )])
    .expect("key fixture should parse");
    let errors = lower(Path::new("src"), parsed).expect_err("unstable keys must fail");
    let messages = errors
        .iter()
        .map(|error| error.diagnostic.message.as_str())
        .collect::<Vec<_>>();
    assert!(messages.contains(&"Set item type must be hash-stable"));
    assert!(messages.contains(&"Map key type must be hash-stable"));

    let parsed = parse_project([SourceFile::new(
        "src/keys.cott",
        "module keys\n\nstruct Good:\n    values: Set[Path]\n    entries: Map[Tuple[Str, U64], Bool]\n",
    )])
    .expect("stable key fixture should parse");
    lower(Path::new("src"), parsed).expect("stable keys should lower");
}

#[test]
fn qualified_constant_references_form_module_dependencies() {
    let parsed = parse_project([
        SourceFile::new(
            "src/left.cott",
            "module left\n\nconst value: I32 = right.value\n",
        ),
        SourceFile::new(
            "src/right.cott",
            "module right\n\nconst value: I32 = left.value\n",
        ),
    ])
    .expect("qualified cycle fixture should parse");
    let errors = lower(Path::new("src"), parsed).expect_err("qualified cycle must fail");
    assert!(
        errors.iter().any(|error| {
            error.diagnostic.message == "cyclic module import/reference dependency"
        })
    );
}

#[test]
fn acyclic_qualified_constant_reference_lowers_without_import() {
    let parsed = parse_project([
        SourceFile::new(
            "src/provider.cott",
            "module provider\n\nconst value: I32 = 7\n",
        ),
        SourceFile::new(
            "src/consumer.cott",
            "module consumer\n\nconst value: I32 = provider.value\n",
        ),
    ])
    .expect("qualified acyclic fixture should parse");
    lower(Path::new("src"), parsed).expect("qualified acyclic reference should lower");
}

#[test]
fn qualified_dependency_diagnostics_are_deterministic() {
    let diagnostics = || {
        let parsed = parse_project([
            SourceFile::new(
                "src/left.cott",
                "module left\n\nconst value: I32 = right.value\n",
            ),
            SourceFile::new(
                "src/right.cott",
                "module right\n\nconst value: I32 = left.value\n",
            ),
        ])
        .expect("qualified cycle fixture should parse");
        lower(Path::new("src"), parsed)
            .expect_err("qualified cycle must fail")
            .into_iter()
            .map(|error| {
                format!(
                    "{}:{}:{}:{}",
                    error.path.display(),
                    error.diagnostic.message,
                    error.diagnostic.span.start,
                    error.diagnostic.span.end
                )
            })
            .collect::<Vec<_>>()
    };
    assert_eq!(diagnostics(), diagnostics());
}

#[test]
fn len_is_restricted_to_supported_containers() {
    let valid = parse_project([SourceFile::new(
        "src/lengths.cott",
        "module lengths\n\nfn inspect(text: Str, bytes: Bytes, items: List[U8], values: Set[U8], entries: Map[Str, U8]) -> Unit:\n    requires text.len == bytes.len\n    requires items.len == values.len\n    requires entries.len == 0\n",
    )])
    .expect("valid length fixture should parse");
    let project = lower(Path::new("src"), valid).expect("supported lengths should lower");
    let HirDeclaration::Function(function) = &project.modules[0].declarations[0] else {
        panic!("expected inspect function");
    };
    for clause in &function.contract.clauses {
        let HirClauseKind::Requires { expression } = &clause.kind else {
            continue;
        };
        assert_eq!(expression.ty, HirType::Primitive(PrimitiveType::Bool));
    }

    let invalid = parse_project([SourceFile::new(
        "src/lengths.cott",
        "module lengths\n\nfn inspect(count: U64) -> Unit:\n    requires count.len == 0\n",
    )])
    .expect("invalid length fixture should parse");
    let errors = lower(Path::new("src"), invalid).expect_err("numeric length must fail");
    assert!(errors.iter().any(|error| {
        error.diagnostic.message
            == "length is only defined for strings, bytes, lists, sets, and maps"
    }));
}

#[test]
fn newtype_contract_operands_use_carriers_but_signatures_stay_nominal() {
    let parsed = parse_project([SourceFile::new(
        "src/ports.cott",
        "module ports\n\nnewtype Port(U16)\n\nfn check(port: Port) -> Unit:\n    requires port > 0\n",
    )])
    .expect("newtype contract fixture should parse");
    let project = lower(Path::new("src"), parsed).expect("newtype contract should lower");
    let HirDeclaration::Function(function) = &project.modules[0].declarations[1] else {
        panic!("expected check function");
    };
    let port_type = HirType::Named {
        symbol: SymbolId::new(ModuleId::new(vec!["ports".into()]), "Port"),
        args: Vec::new(),
    };
    assert_eq!(function.parameters[0].ty, port_type);
    let HirClauseKind::Requires { expression } = &function.contract.clauses[0].kind else {
        panic!("expected requires clause");
    };
    let HirExprKind::ComparisonChain { operands, .. } = &expression.kind else {
        panic!("expected comparison chain");
    };
    assert!(matches!(
        &operands[0].kind,
        HirExprKind::Field { name, base } if name == "value"
            && matches!(&base.kind, HirExprKind::ParameterRef(_))
    ));
    assert_eq!(operands[0].ty, HirType::Primitive(PrimitiveType::U16));
}

#[test]
fn distinct_numeric_newtypes_compare_through_their_carriers() {
    let parsed = parse_project([SourceFile::new(
        "src/ports.cott",
        "module ports\n\nnewtype Port(U16)\nnewtype OtherPort(U16)\n\nfn check(port: Port, other: OtherPort) -> Unit:\n    requires port > other\n",
    )])
    .expect("newtype carrier fixture should parse");
    lower(Path::new("src"), parsed).expect("compatible carriers should lower");
}
