import os
from argparse import ArgumentParser
import shutil
from os import path

import yaml

import endpoint
from command.executor import CommandExecutor
from server import server
from utils.logging import Logger
from utils.token import Token

from server import handler_base
from server import handler


def load_config(file_name):
    with open(file_name, "r", encoding="utf-8") as r:
        return yaml.safe_load(r)


class Main:
    def __init__(self, arg):
        self.log = Logger(name="main", dir="logs")
        self.cmd = CommandExecutor(self)
        self.config = None

        self.no_req_log = handler.no_req_log = arg.no_request_log
        self.verbose = arg.verbose

    def validate_config(self, config):
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

    def main(self):
        self.log.info("main", "Starting...")
        if not path.exists("config.yml"):
            shutil.copy("resources/config.template.yml", "config.yml")
            self.log.info(
                "config", "Copied resources/config.template.yml to ./config.yml .")
            self.log.severe("config", "Please edit config.yml first.")
            self.die(1)

        config = load_config("config.yml")
        self.config = config
        if not self.validate_config(config):
            self.die(1)

        handler_base.read_limit = config["system"]["request"]["header_readlimit"]
        handler_base.header_limit = config["system"]["request"]["header_limit"]
        handler_base.default_version = config["system"]["request"]["default_protocol"]

        token = Token("token.sig")
        if not token.loaded:
            self.log.warn("main", "Token not found. ")
            self.log.info("auth", "Generating token...")
            self.log.info("auth", "Token generated: " + token.generate())
            self.log.warn(
                "auth", "Make sure to copy this token now. You won't be able to see it again.")

        self.log.info("main", "Binding...")
        server.bind(int(config["system"]["bind"]["port"]),
                    self, token)
        endpoint.loader = endpoint.EPManager()
        self.log.info("main", "Loading endpoints...")
        for route_path in config["system"]["route_paths"]:
            if not os.path.exists(route_path):
                raise FileNotFoundError(route_path + " not found.")
            endpoint.loader.load(route_path)
        self.log.info("main", "%s endpoints loaded." % endpoint.loader.count)
        self.log.info("main", "Ready")
        while True:
            self.console()

    def die(self, i):
        self.log.fatal("main", "Application exit with " + str(i))
        self.log.commit()
        exit(i)

    def bind_commands(self):
        from command.commands.general import CommandExit
        from command.commands.gendoc import CommandDoc
        from command.commands.reload import CommandReload
        from command.commands.load import CommandLoad
        main.cmd.register(CommandExit(self))
        main.cmd.register(CommandDoc(self))
        main.cmd.register(CommandReload(self))
        main.cmd.register(CommandLoad(self))


if __name__ == "__main__":
    parser = ArgumentParser(description="Start server")
    parser.add_argument("-n", "--no-request-log", action="store_true")
    parser.add_argument("-v", "--verbose", action="store_true")
    main = Main(parser.parse_args())
    main.bind_commands()
    main.main()
