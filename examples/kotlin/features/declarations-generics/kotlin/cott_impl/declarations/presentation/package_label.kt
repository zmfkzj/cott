package cott_impl.declarations.presentation

internal fun package_label(label: declarations.core.NonEmptyLabel, values: cott_runtime.CottArray<kotlin.UByte, cott_runtime.CottConst_80ab874e99e0bb981db822e3>, raw: cott_runtime.CottBuffer<cott_runtime.CottConst_80ab874e99e0bb981db822e3>): cott_runtime.CottTuple3<kotlin.String, declarations.core.LabelFrame<cott_runtime.CottArray<kotlin.UByte, cott_runtime.CottConst_80ab874e99e0bb981db822e3>>, declarations.core.ByteBlock<cott_runtime.CottConst_80ab874e99e0bb981db822e3>> =
    cott_runtime.CottTuple3(
        label.value,
        declarations.core.LabelFrame(label, values),
        declarations.core.ByteBlock(raw, cott_runtime.CottConst_80ab874e99e0bb981db822e3)
    )
