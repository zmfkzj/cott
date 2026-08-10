from curriculum.rock_paper_scissors_types import RpsMove, RpsMove_Paper, RpsMove_Rock, RpsMove_Scissors


def user_beats_computer(user: RpsMove, computer: RpsMove) -> bool:
    if isinstance(user, RpsMove_Rock):
        return isinstance(computer, RpsMove_Scissors)
    if isinstance(user, RpsMove_Paper):
        return isinstance(computer, RpsMove_Rock)
    return isinstance(computer, RpsMove_Paper)
