use std::ffi::c_void;
use std::sync::LazyLock;

use tree_sitter::Language;

unsafe extern "C" {
    fn cott_kotlin_jvm_language(language: *const c_void) -> *const c_void;
}

static LANGUAGE: LazyLock<Result<Language, String>> = LazyLock::new(|| {
    let upstream: Language = tree_sitter_kotlin_ng::LANGUAGE.into();
    if upstream.abi_version() != 14 {
        return Err("unsupported Kotlin grammar ABI for JVM keyword handling".to_owned());
    }
    // Native grammar tables are static; native Language drop does not free them.
    // LazyLock serializes the C adapter's initialization. Its cloned descriptor
    // is immutable thereafter, retaining all original scanner/parser tables.
    let pointer = unsafe { cott_kotlin_jvm_language(upstream.into_raw().cast()) };
    if pointer.is_null() {
        return Err("Kotlin grammar does not match the pinned JVM adapter".to_owned());
    }
    Ok(unsafe { Language::from_raw(pointer.cast()) })
});

pub(super) fn language() -> Result<&'static Language, String> {
    LANGUAGE.as_ref().map_err(Clone::clone)
}
