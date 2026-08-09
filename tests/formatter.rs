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
