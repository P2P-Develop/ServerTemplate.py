import datetime
import os
import tarfile


class Type:
    INFO = "INFO"
    WARNING = "WARN"
    SEVERE = "SEVERE"
    ERROR = "ERROR"
    FATAL = "FATAL"
    HINT = "HINT"


class Logger:
    def __init__(self, **kwargs):
        self.name = kwargs["name"]
        self.dir = kwargs["dir"]
        self.count = 1
        self.buffer = []
        self.date = datetime.datetime.now().strftime("%Y%m%d")
        if not os.path.exists(self.dir):
            os.mkdir(self.dir)
        for f in os.listdir("logs"):
            fn, ext = os.path.splitext(f)
            if ext != ".log":
                continue
            if fn.startswith(self.date):
                continue
            self.archive("logs/" + fn + ".log")

    def log(self, message):
        print(message)
        self.buffer.append(message)
        if len(self.buffer) > 5:
            self.commit()
            self.buffer = []

    def commit(self):
        fname = self.dir + "/" + self.date + "." + str(self.count) + ".log"

        if datetime.datetime.now().strftime("%Y%m%d") != self.date:
            self.count = 1
            self.archive(fname)
            self.date = datetime.datetime.now().strftime("%Y%m%d")
            fname = self.dir + "/" + self.date + "." + str(self.count) + ".log"
        with open(fname, "a", encoding="utf-8") as b:
            for buffer in self.buffer:
                b.write(buffer + "\n")
        if os.path.getsize(fname) > 1000000:
            self.archive(fname)
        self.buffer = []

    def archive(self, target):
        with tarfile.open(target + ".tar.gz", "w:gz") as tar:
            tar.add(target, arcname=self.date + "." + str(self.count) + ".log")
        os.remove(target)
        self.count = self.count + 1

    def info(self, name, message):
        self.log(self.format(Type.INFO, name) + message)

    def warn(self, name, message):
        self.log(self.format(Type.WARNING, name) + message)

    def severe(self, name, message):
        self.log(self.format(Type.SEVERE, name) + message)

    def error(self, name, message):
        self.log(self.format(Type.ERROR, name) + message)

    def fatal(self, name, message):
        self.log(self.format(Type.FATAL, name) + message)

    def hint(self, name, message):
        self.log(self.format(Type.HINT, name) + message)

    def input(self, context):
        self.log("> " + context)

    def format(self, name, type):
        return "[" + datetime.datetime.now().strftime("%H:%M:%S") + " " + type + "/" + name + "] "
