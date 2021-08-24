import shutil
from os import path

import yaml

from command.executor import CommandExecutor
from server import server
from utils.logging import Logger
from utils.token import Token


def loadConfig(fileName):
    with open(fileName, "r", encoding="utf-8") as r:
        return yaml.safe_load(r)


class Main:
    def __init__(self):
        self.log = Logger(name="main", dir="logs")
        self.cmd = CommandExecutor(self)
        self.config = None

    def validateConfig(self, config):
        if config["system"]["bind"] is None or "port" not in config["system"]["bind"]:
            self.log.severe("config", "system.bind.port not found.")
            self.log.hint(
                "config", "Add or uncomment system.bind.port and try again.")
            return False
        clen = 0
        if clen != 0:
            self.log.error("main", str(clen) + " Error(s) found in config.yml")
            return False
        return True

    def console(self):
        cmd = input()
        self.log.input(cmd)
        self.cmd.exec(cmd)
        pass

    def main(self):
        self.log.info("main", "Starting...")
        if not path.exists("config.yml"):
            shutil.copy("resources/config.yml", "config.yml")
            self.log.info(
                "config", "Copied resources/config.yml to ./config.yml .")
            self.log.severe("config", "Please edit config.yml first.")
            self.die(1)

        config = loadConfig("config.yml")
        self.config = config
        if not self.validateConfig(config):
            self.die(1)

        self.log.info("main", "Connecting...")

        token = Token("token.sig")
        if not token.load():
            self.log.warn("main", "Token not found. ")
            self.log.info("auth", "Generating token...")
            self.log.info("auth", "Token generated: " + token.generate())
            self.log.warn(
                "auth", "Make sure to copy this token now. You won't be able to see it again.")

        server.bind(int(config["system"]["bind"]["port"]),
                    self, self.log, token)
        self.log.info("main", "Ready")

        while True:
            self.console()

    def die(self, i):
        self.log.fatal("main", "Application exit with " + str(i))
        self.log.commit()
        exit(i)

    def bindCommands(self):
        from command.commands.general import CommandExit
        from command.commands.gendoc import CommandDoc
        main.cmd.register(CommandExit(self))
        main.cmd.register(CommandDoc(self))


if __name__ == "__main__":
    main = Main()
    main.bindCommands()
    main.main()
