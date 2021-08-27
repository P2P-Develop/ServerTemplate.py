import route
from command.command import CommandEntry


class CommandReload(CommandEntry):
    def getName(self):
        return "reload"

    def getAliases(self):
        return []

    def exec(self, args):
        self.logger.info("main", "Reloading...")
        route.loader.reload()
        self.logger.info("main", "Reload completed.")
