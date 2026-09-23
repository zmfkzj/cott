package cott_impl.declarations.presentation

internal fun package_label(label: declarations.core.NonEmptyLabel, values: cott_runtime.CottArray<kotlin.UByte, cott_runtime.CottConst_c2c52450381b94ef6ed74457>, raw: cott_runtime.CottBuffer<cott_runtime.CottConst_c2c52450381b94ef6ed74457>): cott_runtime.CottTuple3<kotlin.String, declarations.core.LabelFrame<cott_runtime.CottArray<kotlin.UByte, cott_runtime.CottConst_c2c52450381b94ef6ed74457>>, declarations.core.ByteBlock<cott_runtime.CottConst_c2c52450381b94ef6ed74457>> =
    cott_runtime.CottTuple3(
        label.value,
        declarations.core.LabelFrame(label, values),
        declarations.core.ByteBlock(raw, cott_runtime.CottConst_c2c52450381b94ef6ed74457)
    )
