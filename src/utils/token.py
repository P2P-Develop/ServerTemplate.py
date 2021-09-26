import os

from secrets import token_bytes
from blake3 import blake3


class Token:
    def __init__(self, file):
        self.file = file
        self.token = None

    @property
    def loaded(self):
        if not os.path.exists(self.file):
            return False
        with open(self.file, "rb") as r:
            self.token = r.read().decode("utf-8")
        return True

    def save(self, token):
        with open(self.file, "w") as r:
            r.write(token)

    def generate(self):
        if self.token is not None:
            return self.token

        if os.path.exists(self.file) and self.loaded:
            return self.token

        token = token_bytes(32)

        hash_token = blake3(token).hexdigest()

        self.save(hash_token)

        self.token = hash_token

        return hash_token

    def validate(self, token):
        return self.token == blake3(token).hexdigest()
