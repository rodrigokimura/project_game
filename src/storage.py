import shelve

from log import log


class Storage:
    def store(self, data):
        with shelve.open("db") as d:
            d["save"] = data
        log("Data stored to db file")

    def read(self):
        log("Reading data from db file")
        with shelve.open("db") as d:
            return d["save"]
