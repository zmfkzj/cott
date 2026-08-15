use cott::formatter::format;
use cott::parser::parse_cst;
use cott::syntax::Cst;

#[test]
fn lossless_formatter_normalizes_newlines_idempotently() {
    let cst = Cst::parse("module demo.core\r\n\r\nfn run() -> I32\r\n").expect("lex");
    let ast = parse_cst(&cst).expect("parse");
    let once = format(&cst, &ast).expect("format");
    let second_cst = Cst::parse(std::str::from_utf8(&once).expect("UTF-8")).expect("lex formatted");
    let twice = format(
        &second_cst,
        &parse_cst(&second_cst).expect("parse formatted"),
    )
    .expect("format formatted");
    assert_eq!(once, twice);
    assert_eq!(once, b"module demo.core\n\nfn run() -> I32\n");
}

fn formatted(source: &str) -> String {
    let cst = Cst::parse(source).expect("lex");
    let ast = parse_cst(&cst).expect("parse");
    String::from_utf8(format(&cst, &ast).expect("format")).expect("UTF-8")
}

#[test]
fn canonicalizes_spacing_indentation_lists_and_comments() {
    let source = "# attached to module\nmodule demo.core # module\n\nuse foo.{B, A,} # use\n\nstruct Card :\n  # attached to field\n  value:I32=1 # field\n\nfn label( ) -> Str:\n  doc \"\"\"\n  # is doc content\n  \"\"\"\n";
    assert_eq!(
        formatted(source),
        "# attached to module\nmodule demo.core  # module\n\nuse foo.{B, A}  # use\n\nstruct Card:\n    # attached to field\n    value: I32 = 1  # field\n\nfn label() -> Str:\n    doc \"\"\"\n    # is doc content\n    \"\"\"\n"
    );
}

#[test]
fn wraps_legal_comma_lists_at_one_hundred_columns() {
    let source = "module demo.core\n\nfn run(first_parameter_with_a_long_name: Result[Option[I64], Option[I64]], second_parameter_with_a_long_name: Result[Option[I64], Option[I64]]) -> Unit\n";
    let output = formatted(source);
    assert!(output.contains(
        "fn run(\n    first_parameter_with_a_long_name: Result[Option[I64], Option[I64]],\n    second_parameter_with_a_long_name: Result[Option[I64], Option[I64]],\n) -> Unit\n"
    ));
    assert_eq!(formatted(&output), output);
}

#[test]
fn formats_rule_declarations_and_clause_actions() {
    let unformatted = "module demo.rules\n\nrule BaseAssignmentRule:\n  doc \"\"\"\n  Base assignment rule.\n  \"\"\"\n  requires line.len > 0\n  ensures Result.Ok(assignment) => assignment.name.len > 0\n  error ParseAssignmentError.MissingEquals\n\nrule StrictAssignmentRule(BaseAssignmentRule):\n  doc \"\"\"\n  Strict assignment rule.\n  \"\"\"\n  override ensures Result.Ok(assignment) => assignment.name.len > 1\n  delete error ParseAssignmentError.MissingEquals\n  ensures Result.Ok(assignment) => assignment.value.len > 0\n  error ParseAssignmentError.EmptyName\n";
    let expected = "module demo.rules\n\nrule BaseAssignmentRule:\n    doc \"\"\"\n    Base assignment rule.\n    \"\"\"\n\n    requires line.len > 0\n\n    ensures Result.Ok(assignment) => assignment.name.len > 0\n\n    error ParseAssignmentError.MissingEquals\n\nrule StrictAssignmentRule(BaseAssignmentRule):\n    doc \"\"\"\n    Strict assignment rule.\n    \"\"\"\n\n    override ensures Result.Ok(assignment) => assignment.name.len > 1\n\n    delete error ParseAssignmentError.MissingEquals\n\n    ensures Result.Ok(assignment) => assignment.value.len > 0\n\n    error ParseAssignmentError.EmptyName\n";
    let output = formatted(unformatted);
    assert_eq!(output, expected);
    assert_eq!(formatted(&output), expected);
}
