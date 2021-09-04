class Header:
    def __init__(self, name, value):
        self.name = name
        self.value = value


class DecoratedHeader(Header):
    def __init__(self, name, value):
        super().__init__(name, value)
        self.decoration  = {}
        self._parse()

    def _parse(self):
        dc = self.value.split(";")
        for dv in dc:
            kv = dv.split("=", 1)
            if len(kv) != 2:
                self.decoration = {}
                continue
            self.decoration[kv[0]] = kv[1]


class HeaderParser:
    def __init__(self):
        self._headers = {}

    def from_dict(self, headers: dict):
        for kv in headers.items():
            if ";" in kv[1]:
                self._headers[kv[0].lower()] = DecoratedHeader(*kv)

            self._headers[kv[0].lower()] = Header(*kv)

    def get(self, name):
        name = name.lower()

        if name not in self._headers:
            raise ValueError("Header '%s' not found" % name)

        return self._headers[name]

    def __getitem__(self, item):
        return self.get(item)
