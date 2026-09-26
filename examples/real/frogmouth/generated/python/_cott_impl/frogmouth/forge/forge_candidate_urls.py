from cott_runtime import CottList, Some
from frogmouth.model_types import Forge, ForgeRequest, Forge_BitBucket, Forge_GitHub, Forge_GitLab


def _forge_url(forge: Forge, owner: str, repository: str, branch: str, file: str) -> str:
    if isinstance(forge, Forge_GitHub):
        return f"https://raw.githubusercontent.com/{owner}/{repository}/{branch}/{file}"
    if isinstance(forge, Forge_GitLab):
        return f"https://gitlab.com/{owner}/{repository}/-/raw/{branch}/{file}"
    if isinstance(forge, Forge_BitBucket):
        return f"https://bitbucket.org/{owner}/{repository}/raw/{branch}/{file}"
    return f"https://codeberg.org/{owner}/{repository}/raw//branch/{branch}/{file}"


def forge_candidate_urls(forge: Forge, request: ForgeRequest) -> CottList[str]:
    branches: list[str] = [request.branch.value] if isinstance(request.branch, Some) else ["main", "master"]
    file: str = request.file.value if isinstance(request.file, Some) else "README.md"
    return CottList(values=[_forge_url(forge, request.owner, request.repository, branch, file) for branch in branches])
