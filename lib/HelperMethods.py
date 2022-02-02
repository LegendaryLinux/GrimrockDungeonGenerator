import random


def generate_id(length: int = 32):
    identifier = ""
    for _ in range(length):
        identifier += chr(random.randint(0, 255))  # ASCII character set has 255 characters
    return identifier
