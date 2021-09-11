class CommandExecutor:
    def __init__(self, instance):
        self.instance = instance
        self.logger = instance.log
        self.commands = {}

    def register(self, clazz):
        self.commands[clazz.get_name()] = clazz
        for alias in clazz.get_aliases():
            self.commands[alias] = clazz

    def exec(self, cmd):
        l = cmd.split(" ")
        if len(l) == 0:
            return
        label = l[0]
        args = l[1:]
        if label not in self.commands:
            self.logger.error(
                "main", "Command not found. Input help for see help.")
            return
        self.commands[label].exec(args)
