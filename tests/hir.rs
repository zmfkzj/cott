use std::path::Path;

use cott::compiler::{SourceFile, parse_project};
use cott::diagnostics::Span;
use cott::hir::{
    HirCallableKind, HirClause, HirClauseKind, HirConstArgument, HirContract, HirDeclaration,
    HirDoc, HirExpr, HirExprKind, HirGenericArg, HirGenericParam, HirPattern, HirPatternKind,
    HirTrait, HirType, HirValue, HirVariance, ModuleId, PrimitiveType, SymbolId, is_assignable,
    lower,
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

    let bounded = HirGenericParam::Type {
        span: at.clone(),
        variance: HirVariance::Invariant,
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
                    guard: None,
                    expression: expression.clone(),
                },
            },
            HirClause {
                clause_id: 11,
                span: at.clone(),
                kind: HirClauseKind::Ensures {
                    guard: None,
                    expression,
                },
            },
        ],
        effects: vec![],
    };
    let trait_decl = HirTrait {
        id: trait_id.clone(),
        span: at.clone(),
        annotations: vec![],
        doc: Some(HirDoc {
            span: at.clone(),
            text: "renders values".into(),
        }),
        generics: vec![bounded],
        parents: vec![],
        closure: vec![],
        methods: vec![],
        associated_types: vec![],
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
            .map(|generic| {
                (
                    generic.name(),
                    match generic {
                        HirGenericParam::Type { source_order, .. }
                        | HirGenericParam::Const { source_order, .. } => *source_order,
                    },
                )
            })
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
        HirClauseKind::Requires { expression, .. }
            if expression.ty == HirType::Primitive(PrimitiveType::Bool)
    ));
    assert!(matches!(
        &function.contract.clauses[1].kind,
        HirClauseKind::Ensures { guard: None, expression }
            if expression.ty == HirType::Primitive(PrimitiveType::Bool)
    ));
    assert!(matches!(
        &function.contract.clauses[2].kind,
        HirClauseKind::Error {
            variant,
            priority: None,
            when: Some(expression),
            ..
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
fn function_result_contract_lowers_to_result_ref() {
    let parsed = parse_project([SourceFile::new(
        "src/result_ref.cott",
        "module result_ref\n\nfn value() -> I32:\n    ensures result == 1\n",
    )])
    .expect("result fixture should parse");
    let project = lower(Path::new("src"), parsed).expect("result fixture should lower");
    let HirDeclaration::Function(function) = &project.modules[0].declarations[0] else {
        panic!("expected function");
    };
    let HirClauseKind::Ensures { expression, .. } = &function.contract.clauses[0].kind else {
        panic!("expected ensures");
    };
    let HirExprKind::ComparisonChain { operands, .. } = &expression.kind else {
        panic!("expected comparison");
    };
    assert!(matches!(operands[0].kind, HirExprKind::ResultRef));
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
        HirClauseKind::Requires { expression, .. }
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
fn impl_state_numeric_comparisons_take_literal_context() {
    let parsed = parse_project([SourceFile::new(
        "src/impl_numeric_context.cott",
        r#"module impl_numeric_context

trait Counter:
    fn check(self) -> F32

impl CounterState for Counter:
    state:
        count: I32 = 0
        ratio: F32 = 0.0
    invariant self.count >= 0
    invariant self.ratio <= 1.0
    fn check(self) -> F32:
        modifies self.count
        ensures result >= 0.0
        ensures old(self.count) >= 0
        ensures old(self.ratio) <= 1.0
"#,
    )])
    .expect("impl numeric context fixture should parse");
    let project =
        lower(Path::new("src"), parsed).expect("impl numeric literals should take context");
    let HirDeclaration::Impl(implementation) = &project.modules[0].declarations[1] else {
        panic!("expected impl");
    };
    let expressions = implementation
        .invariants
        .iter()
        .map(|invariant| &invariant.expression)
        .chain(
            implementation.methods[0]
                .contract
                .clauses
                .iter()
                .filter_map(|clause| {
                    let HirClauseKind::Ensures { expression, .. } = &clause.kind else {
                        return None;
                    };
                    Some(expression)
                }),
        );
    for expression in expressions {
        let HirExprKind::ComparisonChain { operands, .. } = &expression.kind else {
            panic!("expected comparison");
        };
        assert_eq!(expression.ty, HirType::Primitive(PrimitiveType::Bool));
        assert_eq!(operands[0].ty, operands[1].ty);
    }
    assert_eq!(
        implementation.methods[0].modifies[0].as_string(),
        "impl_numeric_context.CounterState.count"
    );
    let old_fields = implementation.methods[0]
        .contract
        .clauses
        .iter()
        .filter_map(|clause| {
            let HirClauseKind::Ensures { expression, .. } = &clause.kind else {
                return None;
            };
            let HirExprKind::ComparisonChain { operands, .. } = &expression.kind else {
                return None;
            };
            let HirExprKind::OldStateField { field } = &operands[0].kind else {
                return None;
            };
            Some(field.as_string())
        })
        .collect::<Vec<_>>();
    assert_eq!(
        old_fields,
        [
            "impl_numeric_context.CounterState.count",
            "impl_numeric_context.CounterState.ratio",
        ]
    );
}

#[test]
fn lowers_option_nothing_state_default_for_any_with_implicit_initializer() {
    let parsed = parse_project([SourceFile::new(
        "src/option_state.cott",
        r#"module option_state

trait Holder:
    fn value(self) -> Option[Any]

impl HolderState for Holder:
    state:
        value: Option[Any] = Option.Nothing
    fn value(self) -> Option[Any]:
        ensures Option.Nothing => true
"#,
    )])
    .expect("Option.Nothing state fixture should parse");
    let project =
        lower(Path::new("src"), parsed).expect("Option.Nothing state fixture should lower");
    let HirDeclaration::Impl(implementation) = &project.modules[0].declarations[1] else {
        panic!("expected impl");
    };
    assert_eq!(implementation.initializer, None);
    assert_eq!(
        implementation.state[0].ty,
        HirType::Option {
            item: Box::new(HirType::Primitive(PrimitiveType::Any)),
        }
    );
    assert_eq!(
        implementation.state[0].default,
        Some(HirValue::Option(None)),
    );
}

#[test]
fn option_nothing_rejects_unit_and_unsupported_forms() {
    let unit = parse_project([SourceFile::new(
        "src/unit.cott",
        "module unit\n\ntrait Holder:\n    fn value(self) -> Option[Any]\n\nimpl HolderState for Holder:\n    state:\n        value: Option[Any] = ()\n    fn value(self) -> Option[Any]:\n        ensures true\n",
    )])
    .expect("Unit fixture should parse");
    let unit_errors = lower(Path::new("src"), unit).expect_err("Unit is not Option.Nothing");
    assert_eq!(
        unit_errors
            .iter()
            .map(|error| error.diagnostic.message.as_str())
            .collect::<Vec<_>>(),
        ["default value does not match its declared type"],
    );

    let wrong_type = parse_project([SourceFile::new(
        "src/wrong_type.cott",
        "module wrong_type\n\nconst VALUE: Unit = Option.Nothing\n",
    )])
    .expect("wrong-type fixture should parse");
    let wrong_type_errors =
        lower(Path::new("src"), wrong_type).expect_err("Option.Nothing requires Option");
    assert_eq!(
        wrong_type_errors
            .iter()
            .map(|error| error.diagnostic.message.as_str())
            .collect::<Vec<_>>(),
        ["Option.Nothing does not match the declared constant type"],
    );

    for source in [
        "module invalid\n\nconst VALUE: Option[Any] = Option.Nothing()\n",
        "module invalid\n\nconst VALUE: Option[Any] = Option.None\n",
    ] {
        let rejected = parse_project([SourceFile::new("src/invalid.cott", source)])
            .map_or(true, |parsed| lower(Path::new("src"), parsed).is_err());
        assert!(
            rejected,
            "unsupported Option form must be rejected:\n{source}"
        );
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
    let HirClauseKind::Requires { expression, .. } = &function.contract.clauses[0].kind else {
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
fn const_generic_argument_expressions_lower_as_hir_const_arguments() {
    let parsed = parse_project([
        SourceFile::new(
            "src/foo/sizes.cott",
            "module foo.sizes\n\nconst THREE: U32 = 3\n",
        ),
        SourceFile::new(
            "src/foo/consumer.cott",
            r#"module foo.consumer
use foo.sizes.{THREE}

const FOUR: U32 = 4

struct Page[T, const N: U32]:
    items: Array[T, N]

struct Batch[const N: U32]:
    page: Page[U8, N]

struct Holder:
    literal: Page[U8, 1 + 2]
    named: Page[U8, FOUR]
    qualified: Page[U8, foo.sizes.THREE]
    arithmetic: Page[U8, FOUR + 1]
"#,
        ),
    ])
    .expect("const argument fixture should parse");
    let project = lower(Path::new("src"), parsed).expect("const arguments should lower");
    let declarations = &project
        .modules
        .iter()
        .find(|module| module.id.as_string() == "foo.consumer")
        .expect("consumer module")
        .declarations;
    let HirDeclaration::Struct(batch) = declarations
        .iter()
        .find(|declaration| declaration.id().as_string() == "foo.consumer.Batch")
        .expect("Batch declaration")
    else {
        panic!("expected Batch struct");
    };
    let HirType::Named { args, .. } = &batch.fields[0].ty else {
        panic!("expected Page instance type");
    };
    assert!(matches!(
        args.get(1),
        Some(HirGenericArg::Const(HirConstArgument::Parameter { name, .. })) if name == "N"
    ));
    let HirDeclaration::Struct(holder) = declarations
        .iter()
        .find(|declaration| declaration.id().as_string() == "foo.consumer.Holder")
        .expect("Holder declaration")
    else {
        panic!("expected Holder struct");
    };
    for (index, field) in holder.fields.iter().enumerate() {
        let HirType::Named { args, .. } = &field.ty else {
            panic!("expected Page instance type");
        };
        if matches!(index, 0 | 3) {
            assert!(matches!(
                args.get(1),
                Some(HirGenericArg::Const(HirConstArgument::Binary { .. }))
            ));
        } else {
            assert!(matches!(args.get(1), Some(HirGenericArg::Const(_))));
        }
    }
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
        let HirClauseKind::Requires { expression, .. } = &clause.kind else {
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
    let HirClauseKind::Requires { expression, .. } = &function.contract.clauses[0].kind else {
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

#[test]
fn expression_first_agent_types_lower_in_every_declarative_position() {
    let parsed = parse_project([SourceFile::new(
        "src/agents.cott",
        r#"module agents

alias Token = Opaque["alias"]
newtype Handle(Opaque["newtype"])

struct Request:
    field: Opaque["field"]
    iterator: Iterator[Any]
    values: List[Opaque["list"]]

enum Response:
    Value(value: Opaque["variant"])

trait Service:
    fn stream(self, input: Opaque["parameter"]) -> Generator[Opaque["yield"], Unknown, Opaque["return"]]

fn inspect(value: Map[Str, Opaque["map-value"]], stream: Iterator[Unknown]) -> Any
"#,
    )])
    .expect("expression-first fixture should parse");
    let project = lower(Path::new("src"), parsed).expect("nested opaque types should lower");
    let declarations = &project.modules[0].declarations;

    let HirDeclaration::Alias(token) = &declarations[0] else {
        panic!("expected opaque alias");
    };
    assert_eq!(
        token.target,
        HirType::Opaque {
            tag: "alias".into()
        }
    );

    let HirDeclaration::Newtype(handle) = &declarations[1] else {
        panic!("expected opaque newtype");
    };
    assert_eq!(
        handle.carrier,
        HirType::Opaque {
            tag: "newtype".into()
        }
    );

    let HirDeclaration::Struct(request) = &declarations[2] else {
        panic!("expected request struct");
    };
    assert_eq!(
        request.fields[0].ty,
        HirType::Opaque {
            tag: "field".into()
        }
    );
    assert_eq!(
        request.fields[1].ty,
        HirType::Iterator {
            item: Box::new(HirType::Primitive(PrimitiveType::Any))
        }
    );
    assert_eq!(
        request.fields[2].ty,
        HirType::List {
            item: Box::new(HirType::Opaque { tag: "list".into() })
        }
    );

    let HirDeclaration::Enum(response) = &declarations[3] else {
        panic!("expected response enum");
    };
    assert_eq!(
        response.variants[0].fields[0].ty,
        HirType::Opaque {
            tag: "variant".into()
        }
    );

    let HirDeclaration::Trait(service) = &declarations[4] else {
        panic!("expected service trait");
    };
    assert_eq!(
        service.methods[0].parameters[0].ty,
        HirType::Opaque {
            tag: "parameter".into()
        }
    );
    assert_eq!(
        service.methods[0].return_type,
        HirType::Generator {
            yield_type: Box::new(HirType::Opaque {
                tag: "yield".into()
            }),
            send_type: Box::new(HirType::Primitive(PrimitiveType::Unknown)),
            return_type: Box::new(HirType::Opaque {
                tag: "return".into()
            }),
        }
    );

    let HirDeclaration::Function(inspect) = &declarations[5] else {
        panic!("expected inspect function");
    };
    assert_eq!(
        inspect.parameters[0].ty,
        HirType::Map {
            key: Box::new(HirType::Primitive(PrimitiveType::Str)),
            value: Box::new(HirType::Opaque {
                tag: "map-value".into()
            }),
        }
    );
    assert_eq!(
        inspect.parameters[1].ty,
        HirType::Iterator {
            item: Box::new(HirType::Primitive(PrimitiveType::Unknown))
        }
    );
    assert_eq!(inspect.return_type, HirType::Primitive(PrimitiveType::Any));
}

#[test]
fn external_types_lower_as_named_symbols_and_imports() {
    let parsed = parse_project([
        SourceFile::new(
            "src/providers.cott",
            r#"module providers

doc """Python remote client"""
external type Remote
"#,
        ),
        SourceFile::new(
            "src/consumers.cott",
            r#"module consumers
use providers.Remote

struct Request:
    remote: Remote

fn forward(remote: Remote) -> Remote

trait RemoteHolder:
    fn current(self) -> Remote

impl StoredRemote for RemoteHolder:
    state:
        remote: Remote
    init(remote: Remote):
        doc """
        Store the projected external value.
        """
    fn current(self) -> Remote:
        doc """
        Return the stored external value.
        """
"#,
        ),
    ])
    .expect("external type fixture should parse");
    let project = lower(Path::new("src"), parsed).expect("external types should lower");

    let provider = &project.modules[0];
    let HirDeclaration::ExternalType(remote) = &provider.declarations[0] else {
        panic!("expected external remote type");
    };
    assert_eq!(remote.id.as_string(), "providers.Remote");
    assert_eq!(
        remote.doc.as_ref().map(|doc| doc.text.as_str()),
        Some("Python remote client")
    );
    assert!(remote.public);
    assert_eq!(remote.source_order, 0);

    let consumer = &project.modules[1];
    assert_eq!(consumer.imports.len(), 1);
    assert_eq!(consumer.imports[0].symbol, remote.id);
    assert_eq!(consumer.imports[0].name, "Remote");
    let remote_type = HirType::Named {
        symbol: remote.id.clone(),
        args: Vec::new(),
    };
    let HirDeclaration::Struct(request) = &consumer.declarations[0] else {
        panic!("expected request struct");
    };
    assert_eq!(request.fields[0].ty, remote_type);
    let HirDeclaration::Function(forward) = &consumer.declarations[1] else {
        panic!("expected forward function");
    };
    assert_eq!(forward.parameters[0].ty, forward.return_type);
    assert_eq!(
        forward.return_type,
        HirType::Named {
            symbol: remote.id.clone(),
            args: Vec::new(),
        }
    );
    let HirDeclaration::Impl(stored) = &consumer.declarations[3] else {
        panic!("expected external state implementation");
    };
    assert_eq!(stored.state[0].ty, remote_type);
}

#[test]
fn rejects_invalid_agent_type_arities_and_opaque_boundaries() {
    for (source, expected) in [
        (
            "module invalid\nstruct Value:\n    item: Iterator[U8, U16]\n",
            "type constructor `Iterator` expects 1 argument(s), got 2",
        ),
        (
            "module invalid\nstruct Value:\n    item: Generator[U8, U16]\n",
            "type constructor `Generator` expects 3 argument(s), got 2",
        ),
        (
            "module invalid\nstruct Value:\n    item: AsyncIterator[U8, U16]\n",
            "type constructor `AsyncIterator` expects 1 argument(s), got 2",
        ),
        (
            "module invalid\nstruct Value:\n    item: AsyncGenerator[U8]\n",
            "type constructor `AsyncGenerator` expects 2 argument(s), got 1",
        ),
        (
            "module invalid\nalias Stream = Iterator[U8]\nasync fn stream() -> Stream\n",
            "async function cannot return Iterator, Generator, or Never",
        ),
        (
            "module invalid\nstruct Value:\n    item: Opaque[\"Invalid\"]\n",
            "Opaque tag must match [a-z][a-z0-9._-]{0,63}",
        ),
        (
            "module invalid\nstruct Value:\n    items: Set[Opaque[\"set\"]]\n",
            "Set item type must be hash-stable",
        ),
        (
            "module invalid\nstruct Value:\n    entries: Map[Opaque[\"map\"], U8]\n",
            "Map key type must be hash-stable",
        ),
    ] {
        let parsed =
            parse_project([SourceFile::new("src/invalid.cott", source)]).expect("fixture parses");
        let errors = lower(Path::new("src"), parsed).expect_err("fixture must be rejected");
        assert_eq!(
            errors
                .iter()
                .map(|error| error.diagnostic.message.as_str())
                .collect::<Vec<_>>(),
            [expected],
            "unexpected diagnostics for:\n{source}"
        );
    }
}

#[test]
fn factory_lowers_only_imported_aliases_of_impl_identities() {
    let parsed = parse_project([
        SourceFile::new(
            "src/contracts.cott",
            r#"module contracts

trait Worker:
    fn work(self) -> Unit

impl WorkerState for Worker:
    fn work(self) -> Unit:
        ensures true

alias WorkerFactory = WorkerState
"#,
        ),
        SourceFile::new(
            "src/api.cott",
            r#"module api
use contracts.{WorkerFactory, WorkerState}

fn create(factory: Factory[WorkerFactory]) -> Factory[WorkerState]
"#,
        ),
    ])
    .expect("Factory aliases should parse");
    let project = lower(Path::new("src"), parsed).expect("Factory impl aliases should lower");
    let HirDeclaration::Function(create) = &project.modules[1].declarations[0] else {
        panic!("expected create function");
    };
    let concrete = HirType::Named {
        symbol: SymbolId::new(ModuleId::new(vec!["contracts".into()]), "WorkerState"),
        args: vec![],
    };
    assert_eq!(
        create.parameters[0].ty,
        HirType::Factory {
            instance: Box::new(concrete.clone()),
        }
    );
    assert_eq!(
        create.return_type,
        HirType::Factory {
            instance: Box::new(concrete),
        }
    );
}

#[test]
fn factory_rejects_non_impl_targets_and_non_value_positions() {
    let parsed = parse_project([SourceFile::new(
        "src/invalid.cott",
        r#"module invalid

external type Remote

struct Record:
    value: U8
trait Contract:
    fn run(self) -> Unit

impl Concrete for Contract:
    state:
        factory: Factory[Concrete] = ()
    fn run(self) -> Unit:
        ensures true

fn reject[T](trait_value: Factory[Contract], record_value: Factory[Record], remote_value: Factory[Remote], parameter_value: Factory[T], generic_value: Factory[Concrete[U8]], arity_value: Factory[Concrete, U8]) -> Unit
"#,
    )])
    .expect("Factory rejection fixture should parse");
    let errors = lower(Path::new("src"), parsed).expect_err("Factory invalid uses must fail");
    let messages = errors
        .iter()
        .map(|error| error.diagnostic.message.as_str())
        .collect::<Vec<_>>();
    assert_eq!(
        messages
            .iter()
            .filter(|message| {
                **message
                    == "Factory instance type must resolve to an impl declaration without type arguments"
            })
            .count(),
        4
    );
    assert!(messages.contains(&"type constructor `invalid.Concrete` expects 0 argument(s), got 1"));
    assert!(messages.contains(&"type constructor `Factory` expects 1 argument(s), got 2"));
    assert!(messages.contains(&"state field type must be a closed immutable cott value type"));
    assert!(messages.contains(&"default value does not match its declared type"));
}

#[test]
fn factory_is_not_hash_stable() {
    let parsed = parse_project([SourceFile::new(
        "src/hash.cott",
        r#"module hash

trait Contract:
    fn run(self) -> Unit

impl Concrete for Contract:
    fn run(self) -> Unit:
        ensures true

fn index(items: Set[Factory[Concrete]], entries: Map[Factory[Concrete], U8]) -> Unit
"#,
    )])
    .expect("Factory hash fixture should parse");
    let errors = lower(Path::new("src"), parsed).expect_err("Factory keys must be rejected");
    assert_eq!(
        errors
            .iter()
            .map(|error| error.diagnostic.message.as_str())
            .collect::<Vec<_>>(),
        [
            "Set item type must be hash-stable",
            "Map key type must be hash-stable",
        ]
    );
}

#[test]
fn factory_is_a_reserved_prelude_type() {
    let parsed = parse_project([SourceFile::new(
        "src/reserved.cott",
        "module reserved\n\nstruct Factory:\n    value: U8\n",
    )])
    .expect("Factory declaration fixture should parse");
    let errors = lower(Path::new("src"), parsed).expect_err("Factory must be reserved");
    assert_eq!(
        errors
            .iter()
            .map(|error| error.diagnostic.message.as_str())
            .collect::<Vec<_>>(),
        ["declaration `Factory` collides with a prelude type"]
    );
}

#[test]
fn lowers_associated_projections_async_identity_and_resource_graph() {
    let parsed = parse_project([SourceFile::new(
        "src/v03.cott",
        r#"module v03

trait Stream:
    type Item
    fn next(self) -> Stream.Item

impl NumberStream for Stream:
    type Item = I32
    fn next(self) -> I32:
        ensures true

resource Door:
    initial Open
    state Open
    state Closed
    terminal Closed
    transition Open -> Closed

async fn fetch() -> I32
"#,
    )])
    .expect("v0.3 fixture must parse");
    let project = lower(Path::new("src"), parsed).expect("v0.3 fixture must lower");
    let declarations = &project.modules[0].declarations;
    let HirDeclaration::Trait(stream) = &declarations[0] else {
        panic!("first declaration must be trait");
    };
    assert_eq!(stream.associated_types[0].id.as_string(), "v03.Stream.Item");
    assert!(matches!(
        stream.methods[0].return_type,
        HirType::AssociatedProjection { ref trait_id, ref name, .. }
            if trait_id.as_string() == "v03.Stream" && name == "Item"
    ));
    let HirDeclaration::Impl(number_stream) = &declarations[1] else {
        panic!("second declaration must be impl");
    };
    assert_eq!(
        number_stream.associated_types[0].ty,
        HirType::Primitive(PrimitiveType::I32)
    );
    let HirDeclaration::Resource(door) = &declarations[2] else {
        panic!("third declaration must be resource");
    };
    assert_eq!(door.initial.as_string(), "v03.Door.Open");
    assert_eq!(door.edges[0].to.as_string(), "v03.Door.Closed");
    let HirDeclaration::Function(fetch) = &declarations[3] else {
        panic!("fourth declaration must be function");
    };
    assert_eq!(fetch.callable_kind, HirCallableKind::Async);
}

#[test]
fn lowers_resource_transitions_in_source_order() {
    let parsed = parse_project([SourceFile::new(
        "src/lifecycle_transitions.cott",
        r#"module lifecycle_transitions

trait Controller:
    fn close(self) -> Unit

resource Door:
    initial Open
    state Open
    state Closed
    terminal Closed
    transition Open -> Closed

impl DoorController for Controller:
    state:
        primary: Door
        backup: Door
        audit: I32 = 0
    init(primary: Door, backup: Door):
        requires true
    fn close(self) -> Unit:
        requires true
        transitions self.primary: Door.Open -> Door.Closed, self.backup: Door.Open -> Door.Closed
        modifies self.audit
        ensures true
"#,
    )])
    .expect("transition fixture must parse");
    let project = lower(Path::new("src"), parsed).expect("transition fixture must lower");
    let HirDeclaration::Impl(controller) = &project.modules[0].declarations[2] else {
        panic!("third declaration must be impl");
    };
    assert_eq!(controller.methods[0].transitions.len(), 2);
    assert!(matches!(
        &controller.state[0].default,
        Some(HirValue::Enum { variant, fields })
            if variant.as_string() == "lifecycle_transitions.Door.Open" && fields.is_empty()
    ));
    assert_eq!(
        controller.methods[0].transitions[0].field.as_string(),
        "lifecycle_transitions.DoorController.primary"
    );
    assert_eq!(
        controller.methods[0].transitions[1].field.as_string(),
        "lifecycle_transitions.DoorController.backup"
    );
}

#[test]
fn lowers_async_protocol_types_and_impl_method_kinds() {
    let parsed = parse_project([SourceFile::new(
        "src/async_protocols.cott",
        r#"module async_protocols

trait Stream:
    async fn next(self) -> AsyncIterator[I32]

impl AsyncStream for Stream:
    async fn next(self) -> AsyncIterator[I32]:
        ensures true

async fn protocol_source() -> AsyncGenerator[I32, Unit]
fn protocols(items: AsyncIterator[I32]) -> AsyncGenerator[I32, Unit]
"#,
    )])
    .expect("async protocol fixture must parse");
    let project = lower(Path::new("src"), parsed).expect("async protocol fixture must lower");
    let declarations = &project.modules[0].declarations;
    let HirDeclaration::Trait(stream) = &declarations[0] else {
        panic!("first declaration must be trait");
    };
    assert_eq!(stream.methods[0].callable_kind, HirCallableKind::Async);
    assert_eq!(
        stream.methods[0].return_type,
        HirType::AsyncIterator {
            item: Box::new(HirType::Primitive(PrimitiveType::I32))
        }
    );
    let HirDeclaration::Impl(implementation) = &declarations[1] else {
        panic!("second declaration must be impl");
    };
    assert_eq!(
        implementation.methods[0].callable_kind,
        HirCallableKind::Async
    );
    assert_eq!(
        implementation.methods[0].return_type,
        HirType::AsyncIterator {
            item: Box::new(HirType::Primitive(PrimitiveType::I32))
        }
    );
    assert_eq!(
        implementation.selected_methods[0].callable_kind,
        HirCallableKind::Async
    );
    let HirDeclaration::Function(protocol_source) = &declarations[2] else {
        panic!("third declaration must be function");
    };
    assert_eq!(protocol_source.callable_kind, HirCallableKind::Async);
    assert_eq!(
        protocol_source.return_type,
        HirType::AsyncGenerator {
            yield_type: Box::new(HirType::Primitive(PrimitiveType::I32)),
            send_type: Box::new(HirType::Primitive(PrimitiveType::Unit)),
        }
    );
    let HirDeclaration::Function(protocols) = &declarations[3] else {
        panic!("fourth declaration must be function");
    };
    assert_eq!(
        protocols.parameters[0].ty,
        HirType::AsyncIterator {
            item: Box::new(HirType::Primitive(PrimitiveType::I32))
        }
    );
    assert_eq!(
        protocols.return_type,
        HirType::AsyncGenerator {
            yield_type: Box::new(HirType::Primitive(PrimitiveType::I32)),
            send_type: Box::new(HirType::Primitive(PrimitiveType::Unit)),
        }
    );
}

#[test]
fn lowers_v7_inherited_trait_closure_and_nominal_dyn_type() {
    let parsed = parse_project([SourceFile::new(
        "src/v05_hir.cott",
        r#"module v05_hir

trait Parent:
    fn read(self) -> I32

trait Child for Parent:
    fn write(self) -> I32

impl Concrete for Child:
    fn read(self) -> I32:
        ensures true
    fn write(self) -> I32:
        ensures true

alias Dynamic = Dyn[Child]
"#,
    )])
    .expect("v0.5 fixture must parse");
    let project = lower(Path::new("src"), parsed).expect("v0.5 fixture must lower");
    let declarations = &project.modules[0].declarations;
    let HirDeclaration::Trait(child) = &declarations[1] else {
        panic!("second declaration must be child trait");
    };
    assert_eq!(child.parents.len(), 1);
    assert_eq!(child.closure.len(), 1);
    assert_eq!(child.methods.len(), 2);
    let HirDeclaration::Alias(dynamic) = &declarations[3] else {
        panic!("fourth declaration must be Dyn alias");
    };
    assert!(matches!(dynamic.target, HirType::Dyn { .. }));
}

#[test]
fn coalesces_equal_multi_trait_method_signatures() {
    let parsed = parse_project([SourceFile::new(
        "src/v05_coalesce.cott",
        r#"module v05_coalesce

trait Reader:
    fn read(self) -> I32

trait Writer:
    fn read(self) -> I32

impl Concrete for Reader + Writer:
    fn read(self) -> I32:
        ensures true
"#,
    )])
    .expect("coalesced method fixture must parse");
    let project = lower(Path::new("src"), parsed).expect("equal methods must coalesce");
    let HirDeclaration::Impl(implementation) = &project.modules[0].declarations[2] else {
        panic!("third declaration must be impl");
    };
    assert_eq!(implementation.selected_methods.len(), 1);
}

#[test]
fn trait_assignability_uses_instantiated_parent_closure() {
    let parsed = parse_project([SourceFile::new(
        "src/v05_assignable.cott",
        r#"module v05_assignable

trait Parent[+T]:
    fn value(self) -> T

trait Child[+T] for Parent[T]:
    fn child(self) -> T
"#,
    )])
    .expect("assignability fixture must parse");
    let project = lower(Path::new("src"), parsed).expect("assignability fixture must lower");
    let HirDeclaration::Trait(parent) = &project.modules[0].declarations[0] else {
        panic!("first declaration must be parent");
    };
    let HirDeclaration::Trait(child) = &project.modules[0].declarations[1] else {
        panic!("second declaration must be child");
    };
    let argument = HirGenericArg::Type(HirType::Primitive(PrimitiveType::I32));
    assert!(is_assignable(
        &HirType::Named {
            symbol: child.id.clone(),
            args: vec![argument.clone()],
        },
        &HirType::Named {
            symbol: parent.id.clone(),
            args: vec![argument],
        },
        &project,
    ));
}

#[test]
fn rejects_diamond_with_conflicting_parent_instantiations() {
    let parsed = parse_project([SourceFile::new(
        "src/v05_diamond_args.cott",
        r#"module v05_diamond_args

trait Root[T]:
    fn value(self) -> T

trait Left for Root[I32]:

trait Right for Root[Bool]:

trait Child for Left + Right:
    fn child(self) -> Unit
"#,
    )])
    .expect("diamond fixture must parse");
    let errors = lower(Path::new("src"), parsed)
        .expect_err("incompatible parent instantiations must reject");
    assert!(errors.iter().any(|error| {
        error
            .diagnostic
            .message
            .contains("trait diamond instantiates")
    }));
}

#[test]
fn rejects_multi_trait_method_parameter_shape_mismatch() {
    let parsed = parse_project([SourceFile::new(
        "src/v05_parameter_shape.cott",
        r#"module v05_parameter_shape

trait Reader:
    fn read(self, value: I32) -> I32

trait Writer:
    fn read(self, amount: I32) -> I32

impl Concrete for Reader + Writer:
    fn read(self, value: I32) -> I32:
        ensures true
"#,
    )])
    .expect("parameter-shape fixture must parse");
    let errors =
        lower(Path::new("src"), parsed).expect_err("different parameter names must not coalesce");
    assert!(errors.iter().any(|error| {
        error
            .diagnostic
            .message
            .contains("incompatible methods with the same name")
    }));
}

#[test]
fn rejects_cyclic_multi_bound_trait_intersection_but_allows_single_bounds() {
    let cyclic = parse_project([SourceFile::new(
        "src/v05_bound_cycle.cott",
        r#"module v05_bound_cycle

trait A[T: B[T] + C]:
    fn a(self) -> T

trait B[T: A[T]]:
    fn b(self) -> T

trait C:
    fn c(self) -> Unit
"#,
    )])
    .expect("cyclic bound fixture must parse");
    let errors =
        lower(Path::new("src"), cyclic).expect_err("cyclic multi-bound intersection must reject");
    assert!(errors.iter().any(|error| {
        error
            .diagnostic
            .message
            .contains("multi-bound generic intersection")
    }));

    let allowed = parse_project([SourceFile::new(
        "src/v05_single_bound_cycle.cott",
        r#"module v05_single_bound_cycle

trait Left[T: Right[T]]:
    fn left(self) -> T

trait Right[T: Left[T]]:
    fn right(self) -> T
"#,
    )])
    .expect("single-bound fixture must parse");
    lower(Path::new("src"), allowed).expect("single-bound cycle remains forward-reference-safe");
}

#[test]
fn lowers_v06_safe_multibound_outside_a_single_bound_cycle() {
    let parsed = parse_project([SourceFile::new(
        "src/v06_safe_bounds.cott",
        r#"module v06_safe_bounds

trait Owner[T: A + B, U: CycleA[U]]:
    fn owner(self) -> Unit
trait A:
    fn a(self) -> Unit
trait B:
    fn b(self) -> Unit
trait CycleA[V: CycleB[V]]:
    fn cycle_a(self) -> Unit
trait CycleB[V: Owner[Any, V]]:
    fn cycle_b(self) -> Unit
"#,
    )])
    .expect("safe multi-bound fixture must parse");

    lower(Path::new("src"), parsed)
        .expect("a T multi-bound unrelated to the U-only cycle must lower");
}

#[test]
fn lowers_v06_generic_recursion_as_symbolic_named_types() {
    let parsed = parse_project([SourceFile::new(
        "src/recursive.cott",
        r#"module recursive

struct Chain[T]:
    value: T
    next: Option[Chain[T]]
"#,
    )])
    .expect("recursive fixture should parse");
    let project = lower(Path::new("src"), parsed).expect("guarded recursion should lower");
    let module = &project.modules[0];
    let HirDeclaration::Struct(chain) = &module.declarations[0] else {
        panic!("expected recursive struct");
    };

    assert_eq!(
        chain.fields[1].ty,
        HirType::Option {
            item: Box::new(HirType::Named {
                symbol: symbol(&module.id, "Chain"),
                args: vec![HirGenericArg::Type(HirType::TypeParameter {
                    name: "T".into(),
                })],
            }),
        }
    );
}

#[test]
fn recursive_nominal_types_are_not_hash_stable_keys() {
    let parsed = parse_project([SourceFile::new(
        "src/recursive_key.cott",
        r#"module recursive_key

struct Node:
    next: Option[Node]

struct Index:
    nodes: Set[Node]
"#,
    )])
    .expect("recursive key fixture should parse");
    let errors = lower(Path::new("src"), parsed).expect_err("recursive nominal key must fail");

    assert!(
        errors
            .iter()
            .any(|error| error.diagnostic.message == "Set item type must be hash-stable")
    );
}
