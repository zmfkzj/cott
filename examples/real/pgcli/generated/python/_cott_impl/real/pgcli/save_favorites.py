from cott_runtime import CottList, Err, Result, Unit
from real.pgcli_types import ClientError, ClientError_FavoriteFailed, Favorite, FavoriteStore


def save_favorites(store: FavoriteStore, favorites: CottList[Favorite]) -> Result[Unit, ClientError]:
    return Err(error=ClientError_FavoriteFailed(name=str(store.path)))
