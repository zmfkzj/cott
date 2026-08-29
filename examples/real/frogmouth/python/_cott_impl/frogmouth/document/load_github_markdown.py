from cott_runtime import Result
from frogmouth.document import load_http_markdown
from frogmouth.document_types import LoadError


def load_github_markdown(repository: str) -> Result[str, LoadError]:
    return load_http_markdown(f"https://raw.githubusercontent.com/{repository}/main/README.md")
