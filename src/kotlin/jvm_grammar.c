#include "parser.h"
#include <string.h>

// Header/layout pinned to tree-sitter-kotlin-ng 1.1.0 (language ABI 14).
// Kotlin/JVM has no dynamic built-in type. The upstream grammar incorrectly
// steals its soft-keyword spelling from identifier positions (val dynamic = ...).
// Correct token classification, never the source bytes or syntax-tree ranges.
// Initialization is serialized by Rust's LazyLock before any parser sees this.
static TSLanguage jvm_language;
static const TSLanguage *upstream;
static TSSymbol dynamic_symbol;

static bool jvm_keywords(TSLexer *lexer, TSStateId state) {
    bool found = upstream->keyword_lex_fn(lexer, state);
    if (found && lexer->result_symbol == dynamic_symbol) {
        lexer->result_symbol = upstream->keyword_capture_token;
    }
    return found;
}

const void *cott_kotlin_jvm_language(const void *pointer) {
    const TSLanguage *language = pointer;
    if (!language || language->version != 14 || !language->keyword_lex_fn ||
        language->keyword_capture_token >= language->token_count ||
        strcmp(language->symbol_names[language->keyword_capture_token], "identifier") != 0) {
        return NULL;
    }
    TSSymbol symbol = 0;
    for (uint32_t index = 1; index < language->token_count; ++index) {
        if (!language->symbol_metadata[index].named &&
            strcmp(language->symbol_names[index], "dynamic") == 0) {
            symbol = (TSSymbol)index;
            break;
        }
    }
    if (!symbol) return NULL;
    upstream = language;
    dynamic_symbol = symbol;
    jvm_language = *language;
    jvm_language.keyword_lex_fn = jvm_keywords;
    return &jvm_language;
}
