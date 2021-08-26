import os

from command.command import CommandEntry
from server import ep


class CommandLoad(CommandEntry):
    def getName(self):
        return "load"

    def getAliases(self):
        return []

    def exec(self, args):
        if len(args) < 1:
            self.logger.error("main", "Argument required: \n"
                                      "\tUsage: load <path>")
            return
        self.logger.info("main", "Loading endpoints...")
        path = " ".join(args)
        if not os.path.exists(path):
            self.logger.error("main", "Path not found.")
            return
        ep.loader.load()
        self.logger.info("main", "Endpoints loaded.")