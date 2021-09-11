from command.command import CommandEntry


class CommandExit(CommandEntry):
    def get_name(self):
        return "exit"

    def get_aliases(self):
        return ["shutdown", "stop", "^C"]

    def exec(self, args):
        self.logger.info("main", "Shutdown...")

        if args.length > 0:
            self.instance.die(args[0])
        else:
            self.instance.die(0)
