import sqlite3


def _flatmap(dic):
    val = []
    for d in dic.keys():
        val.append(d)
        val.append(dic[d])
    return val


def _gen_qs(length, join=", "):
    dac = ""

    for ignored in range(0, length):
        if dac != "":
            dac += join
        dac += "?"
    return dac


def _gen_qas(data):
    fn = ""
    for sn in range(0, len(data)):
        if fn != "":
            fn += " AND "
        else:
            fn += "?=?"
    return fn


def prepare(query, data):
    qs = query
    count = 0
    for d in data:
        count += 1
        dn = str(d)
        if isinstance(d, str) and count % 2 == 0:
            dn = "'" + dn.replace("\\", "\\\\").replace("'", "\\'") + "'"
        qs = qs.replace("?", dn, 1)
    return qs


class DataBase:

    def __init__(self, path):
        self.connection = sqlite3.connect(path, check_same_thread=False)

    def __del__(self):
        self.connection.close()

    def exists(self, table, data):
        return self.count(table, data) > 0

    def execute(self, query, data=None):
        if data is not None:
            cu = self.connection.cursor()
            cu.execute(query, data)
            cu.close()
        else:
            cu = self.connection.cursor()
            cu.execute(query)
            cu.close()
        self.connection.commit()

    def _get_base(self, base, data=None):
        if data is not None and isinstance(data, dict):
            base += " WHERE "
            base += _gen_qas(data)
            data = _flatmap(data)
        elif data is not None and isinstance(data, list):
            pass
        else:
            data = []

        cu = self.connection.cursor()
        cu.execute(prepare(base, data))
        return cu

    def get_all(self, table, data=None):
        cu = self._get_base("SELECT * FROM " + table, data)
        da = cu.fetchall()
        cu.close()
        return da

    def get_one(self, table, data=None):
        cu = self._get_base("SELECT * FROM " + table, data)
        da = cu.fetchone()
        cu.close()
        return da

    def count(self, table, data=None):
        cu = self._get_base("SELECT count(*) FROM " + table, data)
        da = cu.fetchone()[0]
        cu.close()
        return da

    def count_null(self, table, column):
        cu = self._get_base("SELECT count(*) FROM " + table + " WHERE ? IS NULL", [column])
        da = cu.fetchone()[0]
        cu.close()
        return da

    def count_nonnull(self, table, column):
        cu = self._get_base("SELECT count(*) FROM " + table + " WHERE ? IS NOT NULL", [column])
        da = cu.fetchone()[0]
        cu.close()
        return da

    def _interact(self, base, data, suffix=")", join=", "):
        base += _gen_qs(len(data), join) + suffix
        cu = self.connection.cursor()
        cu.execute(base, data)
        cu.close()

    def insert(self, table, data):
        base = f"INSERT INTO {table} VALUES ("
        self._interact(base, data)

    def upsert(self, table, data):
        base = f"INSERT OR REPLACE INTO {table} VALUES ("
        self._interact(base, data)

    def delete(self, table, data):
        base = f"DELETE FROM {table} WHERE "
        d = _flatmap(data)
        self._interact(base, d, "", "=")

    def update(self, table, where, data):
        base = f"UPDATE {table} SET " + _gen_qs(len(where), "=") + " WHERE "
        d = _flatmap(where)
        d.append(_flatmap(data))
        self._interact(base, d, "", "=")

    def commit(self):
        self.connection.commit()
