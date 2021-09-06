import hashlib
import os
import secrets
import string


class Token:
    def __init__(self, file, salt=b"P2P-Develop"):
        self.file = file
        self.token = None
        self.salt = salt

    def load(self):
        if not os.path.exists(self.file):
            return False
        with open(self.file, "rb") as r:
            self.token = r.read().decode("utf-8")
        return True

    def get(self):
        return self.token

    def save(self, token):
        with open(self.file, "w") as r:
            r.write(token)

    def generate(self):
        if self.token is not None:
            return self.token

        if os.path.exists(self.file) and self.load():
            return self.token

        token = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(32))
        hash_token = hashlib.blake2b(token.encode("utf-8"), salt=self.salt).hexdigest()

        self.save(hash_token)
        self.token = hash_token

        return token

    def validate(self, token):
        return self.token == hashlib.blake2b(token.encode("utf-8"), salt=self.salt).hexdigest()
