import secrets
import string

ALPHABET = string.ascii_letters + string.digits  # a-z, A-Z, 0-9 (62 chars)
CODE_LENGTH = 7


def generate_short_code(length: int = CODE_LENGTH) -> str:
    """Return a random base62 string of the given length."""
    return "".join(secrets.choice(ALPHABET) for _ in range(length))
