import hashlib
from random import choice


def hash_password(password):
    m = hashlib.md5()
    m.update(password)
    return m.hexdigest()


def make_random_password(
    length=10,
    allowed_chars='abcdefghjkmnpqrstuvwxyzABCDEFGHJKLMNPQRSTUVWXYZ23456789'
):
    "generates a random password with the given length and given allowed_chars"

    # note that default value of allowed_chars does not have "I" or letters
    # that look like it -- just to avoid confusion.

    return ''.join([choice(allowed_chars) for i in range(length)])
