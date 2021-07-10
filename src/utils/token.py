from os import path
import random
import string
import hashlib


class Token:
    def __init__(self, file, salt="P2P-Develop"):
        self.file = file
        self.token = None
        self.salt = salt

    def load(self):
        if not path.exists(self.file):
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
        if path.exists(self.file):
            if self.load():
                return self.token
        token = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        hash = hashlib.md5(token.encode("utf-8") + self.salt.encode()).hexdigest()
        self.save(hash)
        self.token = hash
        return token

    def validate(self, token):
        return self.token == hashlib.md5(token.encode("utf-8") + self.salt.encode()).hexdigest()
