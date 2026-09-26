def run_label(selection: str, valid: bool) -> str:
    if selection.strip() != "" and valid:
        return "Run Selection"
    return "Run Query"
