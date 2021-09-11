import endpoint
from command.command import CommandEntry


class CommandReload(CommandEntry):
    def get_name(self):
        return "reload"

    def get_aliases(self):
        return []

    def exec(self, args):
        self.logger.info("main", "Reloading...")
        endpoint.loader.reload()
        self.logger.info("main", "Reload completed.")
