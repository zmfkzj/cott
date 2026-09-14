package examples.features.declarations_generics

import cott_runtime.CottArray
import cott_runtime.CottBuffer
import cott_runtime.CottConst_c2c52450381b94ef6ed74457
import declarations.core.NonEmptyLabel
import declarations.presentation.package_label

private fun ByteArray.hex(): String =
    joinToString(separator = "") { byte ->
        (byte.toInt() and 0xff).toString(16).padStart(2, '0')
    }

public fun main(): Unit {
    val dimension = CottConst_c2c52450381b94ef6ed74457
    val packaged = package_label(
        NonEmptyLabel("Cott"),
        CottArray(listOf(3.toUByte(), 1.toUByte(), 4.toUByte(), 1.toUByte()), dimension),
        CottBuffer("cott".encodeToByteArray(), dimension),
    )
    println(
        "label=${packaged.item0}; values=${packaged.item1.value.toList()}; " +
            "bytes=${packaged.item2.raw.toByteArray().hex()}",
    )
}
