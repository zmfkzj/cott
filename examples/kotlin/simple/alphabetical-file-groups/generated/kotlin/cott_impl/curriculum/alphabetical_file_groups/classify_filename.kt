package cott_impl.curriculum.alphabetical_file_groups

internal fun classify_filename(filename: kotlin.String): cott_runtime.CottResult<curriculum.alphabetical_file_groups.FileMove, curriculum.alphabetical_file_groups.FileGroupError> {
    if (filename.isEmpty()) {
        return cott_runtime.Err(curriculum.alphabetical_file_groups.FileGroupError.EmptyFilename)
    }
    val first = filename.codePointAt(0)
    val folder = if (java.lang.Character.isLetter(first)) _foldLetter(first) else "misc"
    return cott_runtime.Ok(curriculum.alphabetical_file_groups.FileMove(filename, folder))
}

private fun _codePointString(codePoint: kotlin.Int): kotlin.String =
    java.lang.Character.toChars(codePoint).concatToString()

private fun _foldLetter(codePoint: kotlin.Int): kotlin.String = when (codePoint) {
    0x00B5 -> "\u03BC"
    0x00DF, 0x1E9E -> "ss"
    0x0130 -> "i\u0307"
    0x0149 -> "\u02BCn"
    0x017F -> "s"
    0x01F0 -> "j\u030C"
    0x0390, 0x1FD3 -> "\u03B9\u0308\u0301"
    0x03B0, 0x1FE3 -> "\u03C5\u0308\u0301"
    0x03C2 -> "\u03C3"
    0x03D0 -> "\u03B2"
    0x03D1 -> "\u03B8"
    0x03D5 -> "\u03C6"
    0x03D6 -> "\u03C0"
    0x03F0 -> "\u03BA"
    0x03F1 -> "\u03C1"
    0x03F5 -> "\u03B5"
    0x0587 -> "\u0565\u0582"
    in 0x13A0..0x13F5 -> _codePointString(codePoint)
    in 0x13F8..0x13FD -> _codePointString(codePoint - 8)
    in 0xAB70..0xABBF -> _codePointString(codePoint - 0x97D0)
    0x1C80 -> "\u0432"
    0x1C81 -> "\u0434"
    0x1C82 -> "\u043E"
    0x1C83 -> "\u0441"
    0x1C84, 0x1C85 -> "\u0442"
    0x1C86 -> "\u044A"
    0x1C87 -> "\u0463"
    0x1C88 -> "\uA64B"
    0x1E96 -> "h\u0331"
    0x1E97 -> "t\u0308"
    0x1E98 -> "w\u030A"
    0x1E99 -> "y\u030A"
    0x1E9A -> "a\u02BE"
    0x1E9B -> "\u1E61"
    0x1F50 -> "\u03C5\u0313"
    0x1F52 -> "\u03C5\u0313\u0300"
    0x1F54 -> "\u03C5\u0313\u0301"
    0x1F56 -> "\u03C5\u0313\u0342"
    in 0x1F80..0x1F8F -> _codePointString(0x1F00 + (codePoint and 7)) + "\u03B9"
    in 0x1F90..0x1F9F -> _codePointString(0x1F20 + (codePoint and 7)) + "\u03B9"
    in 0x1FA0..0x1FAF -> _codePointString(0x1F60 + (codePoint and 7)) + "\u03B9"
    0x1FB2 -> "\u1F70\u03B9"
    0x1FB3, 0x1FBC -> "\u03B1\u03B9"
    0x1FB4 -> "\u03AC\u03B9"
    0x1FB6 -> "\u03B1\u0342"
    0x1FB7 -> "\u03B1\u0342\u03B9"
    0x1FBE -> "\u03B9"
    0x1FC2 -> "\u1F74\u03B9"
    0x1FC3, 0x1FCC -> "\u03B7\u03B9"
    0x1FC4 -> "\u03AE\u03B9"
    0x1FC6 -> "\u03B7\u0342"
    0x1FC7 -> "\u03B7\u0342\u03B9"
    0x1FD2 -> "\u03B9\u0308\u0300"
    0x1FD6 -> "\u03B9\u0342"
    0x1FD7 -> "\u03B9\u0308\u0342"
    0x1FE2 -> "\u03C5\u0308\u0300"
    0x1FE4 -> "\u03C1\u0313"
    0x1FE6 -> "\u03C5\u0342"
    0x1FE7 -> "\u03C5\u0308\u0342"
    0x1FF2 -> "\u1F7C\u03B9"
    0x1FF3, 0x1FFC -> "\u03C9\u03B9"
    0x1FF4 -> "\u03CE\u03B9"
    0x1FF6 -> "\u03C9\u0342"
    0x1FF7 -> "\u03C9\u0342\u03B9"
    0xFB00 -> "ff"
    0xFB01 -> "fi"
    0xFB02 -> "fl"
    0xFB03 -> "ffi"
    0xFB04 -> "ffl"
    0xFB05, 0xFB06 -> "st"
    0xFB13 -> "\u0574\u0576"
    0xFB14 -> "\u0574\u0565"
    0xFB15 -> "\u0574\u056B"
    0xFB16 -> "\u057E\u0576"
    0xFB17 -> "\u0574\u056D"
    else -> _codePointString(java.lang.Character.toLowerCase(codePoint))
}
