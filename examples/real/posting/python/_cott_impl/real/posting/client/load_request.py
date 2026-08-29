import os
from pathlib import Path

from cott_runtime import CottList, Err, Ok, Result
from real.posting.client_types import Header, HttpMethod, HttpMethod_Delete, HttpMethod_Get, HttpMethod_Head, HttpMethod_Options, HttpMethod_Patch, HttpMethod_Post, HttpMethod_Put, PostingError, PostingError_InvalidRequest, PostingError_InvalidYaml, PostingError_ReadFailed, PostingError_RequestMissing, RequestDocument


def _mapping_parts(line: str) -> tuple[bool, str, str]:
    separator = line.find(":")
    if separator <= 0:
        return (False, "", "")
    key = line[:separator]
    if key.strip() != key or "\t" in key:
        return (False, "", "")
    value = line[separator + 1 :]
    if "\t" in value:
        return (False, "", "")
    return (True, key, value.strip(" "))


def _plain_is_non_string(value: str) -> bool:
    lowered = value.lower()
    if lowered in ("null", "~", "true", "false", "yes", "no", "on", "off", ".nan", ".inf", "+.inf", "-.inf"):
        return True
    compact = value.replace("_", "")
    if compact.startswith(("+", "-")):
        compact = compact[1:]
    lowered_compact = compact.lower()
    if lowered_compact.startswith(("0x", "0o", "0b")) and len(lowered_compact) > 2:
        digits = lowered_compact[2:]
        if lowered_compact.startswith("0x"):
            return all(character in "0123456789abcdef" for character in digits)
        if lowered_compact.startswith("0o"):
            return all(character in "01234567" for character in digits)
        return all(character in "01" for character in digits)
    exponent_parts = compact.replace("E", "e").split("e")
    if len(exponent_parts) <= 2:
        mantissa = exponent_parts[0]
        exponent_valid = True
        if len(exponent_parts) == 2:
            exponent = exponent_parts[1]
            if exponent.startswith(("+", "-")):
                exponent = exponent[1:]
            exponent_valid = exponent != "" and all(character in "0123456789" for character in exponent)
        if mantissa.count(".") <= 1:
            mantissa_digits = mantissa.replace(".", "")
            if mantissa_digits != "" and all(character in "0123456789" for character in mantissa_digits) and exponent_valid:
                return True
    if len(compact) >= 10 and compact[4:5] == "-" and compact[7:8] == "-" and all(character in "0123456789" for character in compact[:4] + compact[5:7] + compact[8:10]):
        if len(compact) == 10:
            return True
        timestamp = compact[10:]
        return timestamp[0] in ("T", "t", " ") and any(character in "0123456789" for character in timestamp[1:]) and all(character in "0123456789:+-.Zz " for character in timestamp[1:])
    return False


def _decode_double_quoted(value: str) -> tuple[bool, str]:
    pieces: list[str] = []
    index = 1
    end = len(value) - 1
    while index < end:
        character = value[index]
        if character == '\"':
            return (False, "")
        if ord(character) < 32:
            return (False, "")
        if character != "\\":
            pieces.append(character)
            index += 1
            continue
        index += 1
        if index >= end:
            return (False, "")
        escape = value[index]
        if escape == '"' or escape == "\\" or escape == "/":
            pieces.append(escape)
            index += 1
            continue
        if escape == "b":
            pieces.append("\b")
            index += 1
            continue
        if escape == "f":
            pieces.append("\f")
            index += 1
            continue
        if escape == "n":
            pieces.append("\n")
            index += 1
            continue
        if escape == "r":
            pieces.append("\r")
            index += 1
            continue
        if escape == "t":
            pieces.append("\t")
            index += 1
            continue
        if escape != "u" or index + 4 >= end:
            return (False, "")
        hexadecimal = value[index + 1 : index + 5]
        if len(hexadecimal) != 4 or not all(character in "0123456789abcdefABCDEF" for character in hexadecimal):
            return (False, "")
        codepoint = int(hexadecimal, 16)
        index += 5
        if 55296 <= codepoint <= 56319:
            if index + 5 >= end or value[index : index + 2] != "\\u":
                return (False, "")
            low_hexadecimal = value[index + 2 : index + 6]
            if len(low_hexadecimal) != 4 or not all(character in "0123456789abcdefABCDEF" for character in low_hexadecimal):
                return (False, "")
            low_codepoint = int(low_hexadecimal, 16)
            if not 56320 <= low_codepoint <= 57343:
                return (False, "")
            codepoint = 65536 + (codepoint - 55296) * 1024 + low_codepoint - 56320
            index += 6
        elif 56320 <= codepoint <= 57343:
            return (False, "")
        pieces.append(chr(codepoint))
    return (True, "".join(pieces))


def _parse_string_scalar(value: str) -> tuple[int, str]:
    if value == "":
        return (2, "")
    if value.startswith('"') or value.endswith('"'):
        if len(value) < 2 or not value.startswith('"') or not value.endswith('"'):
            return (1, "")
        valid, decoded = _decode_double_quoted(value)
        if not valid:
            return (1, "")
        return (0, decoded)
    if value.startswith("'") or value.endswith("'"):
        if len(value) < 2 or not value.startswith("'") or not value.endswith("'"):
            return (1, "")
        pieces: list[str] = []
        index = 1
        end = len(value) - 1
        while index < end:
            character = value[index]
            if ord(character) < 32:
                return (1, "")
            if character != "'":
                pieces.append(character)
                index += 1
                continue
            if index + 1 >= end or value[index + 1] != "'":
                return (1, "")
            pieces.append("'")
            index += 2
        return (0, "".join(pieces))
    if value[0] in "[]{},#&*!|>%@`" or value in ("-", "?", ":", "---", "...") or value.startswith(("- ", "? ", ": ")) or " #" in value or ": " in value:
        return (1, "")
    if any(ord(character) < 32 for character in value):
        return (1, "")
    if _plain_is_non_string(value):
        return (2, "")
    return (0, value)


def _parse_http_method(value: str) -> HttpMethod | None:
    if value == "GET":
        return HttpMethod_Get()
    if value == "POST":
        return HttpMethod_Post()
    if value == "PUT":
        return HttpMethod_Put()
    if value == "PATCH":
        return HttpMethod_Patch()
    if value == "DELETE":
        return HttpMethod_Delete()
    if value == "HEAD":
        return HttpMethod_Head()
    if value == "OPTIONS":
        return HttpMethod_Options()
    return None


def load_request(path: Path) -> Result[RequestDocument, PostingError]:
    if not path.exists() or not path.is_file():
        return Err(error=PostingError_RequestMissing(path=path))
    if not os.access(path, os.R_OK):
        return Err(error=PostingError_ReadFailed(path=path, message="request document is not readable"))

    source = path.read_text(encoding="utf-8", errors="surrogateescape")
    if source.startswith("\ufeff") or any(ord(character) < 32 and character not in "\t\n\r" for character in source):
        return Err(error=PostingError_InvalidYaml(path=path, message="request document contains invalid characters"))
    if any(55296 <= ord(character) <= 57343 for character in source):
        return Err(error=PostingError_InvalidYaml(path=path, message="request document is not valid UTF-8"))

    lines = source.splitlines()
    seen: set[str] = set()
    name: str | None = None
    method_text: str | None = None
    url: str | None = None
    headers: list[Header] = []
    body: str | None = None
    json_body: bool | None = None
    index = 0

    while index < len(lines):
        line = lines[index]
        if line == "":
            index += 1
            continue
        if line[0].isspace():
            return Err(error=PostingError_InvalidYaml(path=path, message=f"unexpected indentation on line {index + 1}"))
        valid_mapping, key, raw_value = _mapping_parts(line)
        if not valid_mapping:
            return Err(error=PostingError_InvalidYaml(path=path, message=f"invalid mapping entry on line {index + 1}"))
        if key in seen:
            return Err(error=PostingError_InvalidRequest(path=path, message=f"duplicate field: {key}"))
        if key not in ("name", "method", "url", "headers", "body", "json"):
            if key == "<<":
                return Err(error=PostingError_InvalidYaml(path=path, message="YAML merge keys are not supported"))
            return Err(error=PostingError_InvalidRequest(path=path, message=f"unknown field: {key}"))
        seen.add(key)
        index += 1

        if key == "headers":
            if raw_value == "[]":
                continue
            if raw_value != "":
                return Err(error=PostingError_InvalidYaml(path=path, message="headers must be a block list or []"))
            found_header = False
            while index < len(lines):
                while index < len(lines) and lines[index] == "":
                    index += 1
                if index >= len(lines) or not lines[index][0].isspace():
                    break
                item_line = lines[index]
                if "\t" in item_line or not item_line.startswith("  - "):
                    return Err(error=PostingError_InvalidYaml(path=path, message=f"invalid header indentation on line {index + 1}"))
                found_header = True
                header_name: str | None = None
                header_value: str | None = None
                item_fields: set[str] = set()
                field_line = item_line[4:]
                index += 1
                while True:
                    valid_field, field_name, field_raw_value = _mapping_parts(field_line)
                    if not valid_field:
                        return Err(error=PostingError_InvalidYaml(path=path, message=f"invalid header mapping near line {index}"))
                    if field_name in item_fields:
                        return Err(error=PostingError_InvalidRequest(path=path, message=f"duplicate header field: {field_name}"))
                    if field_name not in ("name", "value"):
                        return Err(error=PostingError_InvalidRequest(path=path, message=f"unknown header field: {field_name}"))
                    item_fields.add(field_name)
                    scalar_status, scalar = _parse_string_scalar(field_raw_value)
                    if scalar_status == 1:
                        return Err(error=PostingError_InvalidYaml(path=path, message=f"invalid header scalar: {field_name}"))
                    if scalar_status == 2:
                        return Err(error=PostingError_InvalidRequest(path=path, message=f"header field {field_name} must be a string"))
                    if field_name == "name":
                        header_name = scalar
                    else:
                        header_value = scalar
                    if index >= len(lines) or lines[index] == "" or lines[index].startswith("  - ") or not lines[index][0].isspace():
                        break
                    continuation = lines[index]
                    if "\t" in continuation or not continuation.startswith("    ") or continuation.startswith("     "):
                        return Err(error=PostingError_InvalidYaml(path=path, message=f"invalid header indentation on line {index + 1}"))
                    field_line = continuation[4:]
                    index += 1
                if header_name is None or header_value is None or len(item_fields) != 2:
                    return Err(error=PostingError_InvalidRequest(path=path, message="each header requires exactly name and value"))
                headers.append(Header(name=header_name, value=header_value))
            if not found_header:
                return Err(error=PostingError_InvalidRequest(path=path, message="empty headers must be written as []"))
            continue

        if key == "body" and raw_value in ("|", "|-", "|+"):
            body_lines: list[str] = []
            while index < len(lines):
                body_line = lines[index]
                if body_line == "":
                    body_lines.append("")
                    index += 1
                    continue
                if not body_line[0].isspace():
                    break
                if "\t" in body_line[:2] or not body_line.startswith("  "):
                    return Err(error=PostingError_InvalidYaml(path=path, message=f"invalid body indentation on line {index + 1}"))
                body_lines.append(body_line[2:])
                index += 1
            literal = "\n".join(body_lines)
            if raw_value == "|-":
                body = literal.rstrip("\n")
            elif raw_value == "|+":
                if body_lines and (index < len(lines) or source.endswith("\n") or source.endswith("\r")):
                    literal += "\n"
                body = literal
            elif body_lines:
                body = literal.rstrip("\n") + "\n"
            else:
                body = ""
            continue

        if key == "json":
            if raw_value == "true":
                json_body = True
            elif raw_value == "false":
                json_body = False
            else:
                return Err(error=PostingError_InvalidRequest(path=path, message="json must be a boolean"))
            continue

        scalar_status, scalar = _parse_string_scalar(raw_value)
        if scalar_status == 1:
            return Err(error=PostingError_InvalidYaml(path=path, message=f"invalid scalar for field: {key}"))
        if scalar_status == 2:
            return Err(error=PostingError_InvalidRequest(path=path, message=f"field {key} must be a string"))
        if key == "name":
            name = scalar
        elif key == "method":
            method_text = scalar
        elif key == "url":
            url = scalar
        else:
            body = scalar

    missing = [field for field in ("name", "method", "url", "headers", "body", "json") if field not in seen]
    if missing:
        return Err(error=PostingError_InvalidRequest(path=path, message="missing fields: " + ", ".join(missing)))
    if name is None or name == "":
        return Err(error=PostingError_InvalidRequest(path=path, message="name must not be empty"))
    if url is None or url == "":
        return Err(error=PostingError_InvalidRequest(path=path, message="url must not be empty"))
    if method_text is None:
        return Err(error=PostingError_InvalidRequest(path=path, message="method must be a string"))
    method = _parse_http_method(method_text)
    if method is None:
        return Err(error=PostingError_InvalidRequest(path=path, message=f"unsupported HTTP method: {method_text}"))
    if body is None or json_body is None:
        return Err(error=PostingError_InvalidRequest(path=path, message="body and json are required"))

    return Ok(value=RequestDocument(name=name, method=method, url=url, headers=CottList(values=headers), body=body, json_body=json_body))
