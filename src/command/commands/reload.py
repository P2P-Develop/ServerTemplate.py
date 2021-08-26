from command.command import CommandEntry
from server import ep


class CommandReload(CommandEntry):
    def getName(self):
        return "reload"

    def getAliases(self):
        return []

    def exec(self, args):
        self.logger.info("main", "Reloading...")
        ep.loader.reload()
        self.logger.info("main", "Reload completed.")
