def escape_csv_field(field: str) -> str:
    if ',' not in field and '"' not in field and '\r' not in field and '\n' not in field:
        return field
    return '"' + field.replace('"', '""') + '"'
