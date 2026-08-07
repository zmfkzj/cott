from curriculum.profile_summary_types import ProfileSummary


def run() -> ProfileSummary:
    return ProfileSummary(display_name="Ada", tag_count=2, has_nickname=True)
