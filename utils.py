import random
import string


def generate_password(length=16):
    return ''.join(
        random.SystemRandom().choice(string.ascii_uppercase + string.digits)
        for _ in range(length)
    )


def merge_two_dicts(a, b):
    c = a.copy()
    c.update(b)
    return c


def represents_int(s):
    s = s.strip()
    try:
        int(s)
        return True
    except ValueError:
        return False
