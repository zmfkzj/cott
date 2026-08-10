from curriculum.track_metadata_types import TrackDraft


def trim_track_draft(draft: TrackDraft) -> TrackDraft:
    return TrackDraft(title=draft.title.strip(), artist=draft.artist.strip(), album=draft.album.strip(), track_no=draft.track_no)
