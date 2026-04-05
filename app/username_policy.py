import re

from better_profanity import profanity


USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{3,15}$")

profanity.load_censor_words()


def validate_username_policy(username: str) -> None:
    if not USERNAME_PATTERN.fullmatch(username):
        raise ValueError("Username must be 3-15 characters and use only letters, numbers, or underscores.")

    if profanity.contains_profanity(username):
        raise ValueError("Username cannot contain explicit language.")
