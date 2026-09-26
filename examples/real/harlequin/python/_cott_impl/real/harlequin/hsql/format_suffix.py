def format_suffix(format: str) -> str:
    match format:
        case "table" | "vertical":
            return ".txt"
        case "markdown" | "md":
            return ".md"
        case "csv":
            return ".csv"
        case "tsv":
            return ".tsv"
        case "json":
            return ".json"
        case "jsonl":
            return ".jsonl"
        case "ndjson":
            return ".ndjson"
        case "parquet":
            return ".parquet"
        case "orc":
            return ".orc"
        case "feather":
            return ".feather"
        case "arrow":
            return ".arrow"
        case _:
            return ""
