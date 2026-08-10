from curriculum.track_metadata_types import TrackDraft, TrackMetadata


def format_track_metadata(draft: TrackDraft) -> TrackMetadata:
    return TrackMetadata(display=f"{draft.artist} — {draft.title}", sort_key=f"{draft.artist.lower()}\x00{draft.album.lower()}\x00{draft.track_no:04d}")
