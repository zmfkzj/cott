def spell_catalog_label(label: str) -> str:
    if label == "" or label != label.strip() or any(c in label for c in '.*?"'):
        return '"' + label.replace('"', '""') + '"'
    return label
