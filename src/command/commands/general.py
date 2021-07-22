from command.command import CommandEntry


class CommandExit(CommandEntry):
    def getName(self):
        return "exit"

    def getAliases(self):
        return ["shutdown", "stop", "^C"]

    def exec(self, args):
        self.logger.info("main", "Shutdown...")

        if args.length > 0:
            self.instance.die(args[0])
        else:
            self.instance.die(0)
