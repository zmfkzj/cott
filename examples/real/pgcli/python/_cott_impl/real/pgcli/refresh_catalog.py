from cott_runtime import Err, Result
from real.pgcli_types import Catalog, CatalogRefreshRequest, ClientError, ClientError_CatalogFailed


def refresh_catalog(request: CatalogRefreshRequest) -> Result[Catalog, ClientError]:
    return Err(
        error=ClientError_CatalogFailed(
            message="catalog refresh requires an unavailable database.read host binding",
        )
    )
