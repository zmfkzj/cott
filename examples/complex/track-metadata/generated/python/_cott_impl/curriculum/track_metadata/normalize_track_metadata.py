from cott_runtime import Err, Ok, Result
from curriculum.track_metadata import format_track_metadata
from curriculum.track_metadata_types import TrackDraft, TrackMetadata, TrackMetadataError, TrackMetadataError_BlankArtist, TrackMetadataError_BlankTitle, TrackMetadataError_ZeroTrackNumber


def normalize_track_metadata(draft: TrackDraft) -> Result[TrackMetadata, TrackMetadataError]:
    if draft.track_no == 0:
        return Err(error=TrackMetadataError_ZeroTrackNumber())
    normalized_draft = TrackDraft(title=draft.title.strip(), artist=draft.artist.strip(), album=draft.album.strip(), track_no=draft.track_no)
    if normalized_draft.title == "":
        return Err(error=TrackMetadataError_BlankTitle())
    if normalized_draft.artist == "":
        return Err(error=TrackMetadataError_BlankArtist())
    return Ok(value=format_track_metadata(normalized_draft))
