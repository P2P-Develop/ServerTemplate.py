import os

import endpoint
from command.command import CommandEntry


class CommandLoad(CommandEntry):
    def get_name(self):
        return "load"

    def get_aliases(self):
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
        endpoint.loader.load(path)
        self.logger.info("main", "Endpoints loaded.")
