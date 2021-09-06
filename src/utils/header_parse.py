def _(n):
    return n.rstrip().lstrip()


class Header:
    def __init__(self, name, value):
        self.name = _(name)
        self.value = _(value)

    def __eq__(self, other):
        return self.value.lower() == other.lower()

    def __str__(self):
        return self.value


class DecoratedHeader(Header):
    def __init__(self, name, value):
        super().__init__(name, value)
        self.decoration = {}
        self.raw_value = value
        self._parse()

    def _parse(self):
        dc = self.value.split(";")
        if len(dc) > 1:
            self.value = dc[0]
        for i, dv in enumerate(dc):
            if i == 0:
                continue
            kv = dv.split("=", 1)
            if len(kv) == 1:
                self.decoration[_(kv[0])] = None
                continue
            elif len(kv) == 0:
                continue
            self.decoration[_(kv[0])] = _(kv[1])

    def __eq__(self, other):
        return self.raw_value.lower() == other.lower()

    def __contains__(self, item):
        return item.lower() in self.decoration


class MultiValueHeader(Header):
    def __init__(self, name, value):
        super().__init__(name, "")
        self.raw_value = value
        self.value = {}
        self._parse(value)

    def _parse(self, value):
        dc = value.split(",")
        for dv in dc:
            cn = _(dv).lower()
            if ";" in dv:
                self.value[cn] = DecoratedHeader(self.name, dv)
                continue
            self.value[cn] = Header(self.name, dv)

    def __eq__(self, other):
        return other.lower() in self.value

    def __contains__(self, item):
        return item.lower() in self.value

    def __str__(self):
        return self.raw_value


class HeaderSet:
    def __init__(self):
        self._headers = {}

    def from_dict(self, headers: dict):
        for kv in headers.items():
            self.add(*kv)

    def add(self, name, value):
        if "," in value:
            self._headers[_(name.lower())] = MultiValueHeader(name, value)
            return
        if ";" in value:
            self._headers[_(name.lower())] = DecoratedHeader(name, value)
            return
        self._headers[_(name.lower())] = Header(name, value)

    def get(self, name):
        name = name.lower()

        if name not in self._headers:
            raise ValueError("Header '%s' not found" % name)

        return self._headers[name]

    def __contains__(self, item):
        return item.lower() in self._headers

    def __getitem__(self, item):
        return self.get(item)
