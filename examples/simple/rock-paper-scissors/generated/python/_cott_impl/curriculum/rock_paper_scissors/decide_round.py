from curriculum.rock_paper_scissors import user_beats_computer
from curriculum.rock_paper_scissors_types import RoundResult, RoundResult_ComputerWins, RoundResult_Tie, RoundResult_UserWins, RpsMove

def decide_round(user: RpsMove, computer: RpsMove) -> RoundResult:
    if user == computer:
        return RoundResult_Tie()
    if user_beats_computer(user, computer):
        return RoundResult_UserWins()
    return RoundResult_ComputerWins()
