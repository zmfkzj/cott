from cott_runtime import CottList, Err, Result
from real.pgcli_types import ClientError, ClientError_FavoriteFailed, Favorite, FavoriteStore


def load_favorites(store: FavoriteStore) -> Result[CottList[Favorite], ClientError]:
    return Err(error=ClientError_FavoriteFailed(name=str(store.path)))
