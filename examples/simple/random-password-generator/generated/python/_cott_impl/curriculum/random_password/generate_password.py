from cott_runtime import CottList, Err, I64, Ok, Result
from curriculum.random_password_types import PasswordError, PasswordError_InsufficientDraws, PasswordError_InvalidLength


def generate_password(length: I64, draws: CottList[I64]) -> Result[str, PasswordError]:
    if length < 1 or length > 128:
        return Err(error=PasswordError_InvalidLength())

    letter_count: int = length // 2
    digit_count: int = (3 * length + 9) // 10
    special_count: int = length - letter_count - digit_count
    required_draws: int = 2 * length + letter_count - 1
    if len(draws) < required_draws:
        return Err(error=PasswordError_InsufficientDraws())

    lowercase: str = "abcdefghijklmnopqrstuvwxyz"
    digits: str = "0123456789"
    special_characters: str = "@#$%&*"
    password: list[str] = []
    draw_index: int = 0

    for _ in range(letter_count):
        character: str = lowercase[draws[draw_index] % 26]
        draw_index += 1
        if draws[draw_index] % 2 == 1:
            character = character.upper()
        draw_index += 1
        password.append(character)

    for _ in range(digit_count):
        password.append(digits[draws[draw_index] % 10])
        draw_index += 1

    for _ in range(special_count):
        password.append(special_characters[draws[draw_index] % 6])
        draw_index += 1

    for index in range(length - 1, 0, -1):
        swap_index: int = draws[draw_index] % (index + 1)
        draw_index += 1
        password[index], password[swap_index] = password[swap_index], password[index]

    return Ok(value="".join(password))
