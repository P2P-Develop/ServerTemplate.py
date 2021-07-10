from abc import ABCMeta, abstractmethod


class CommandEntry(metaclass=ABCMeta):
    def __init__(self, instance):
        self.instance = instance
        self.logger = instance.log

    @abstractmethod
    def getName(self):
        pass

    @abstractmethod
    def getAliases(self):
        pass

    @abstractmethod
    def exec(self, args):
        pass
