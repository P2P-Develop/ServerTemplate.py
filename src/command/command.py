from abc import ABCMeta, abstractmethod


class CommandEntry(metaclass=ABCMeta):
    def __init__(self, instance):
        self.instance = instance
        self.logger = instance.log

    @abstractmethod
    def get_name(self):
        pass

    @abstractmethod
    def get_aliases(self):
        pass

    @abstractmethod
    def exec(self, args):
        pass
