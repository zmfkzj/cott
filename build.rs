fn main() {
    println!("cargo:rerun-if-changed=src/kotlin/jvm_grammar.c");
    println!("cargo:rerun-if-changed=vendor/kotlin-parser/parser.h");
    cc::Build::new()
        .std("c11")
        .include("vendor/kotlin-parser")
        .file("src/kotlin/jvm_grammar.c")
        .compile("cott_kotlin_jvm_grammar");
}
