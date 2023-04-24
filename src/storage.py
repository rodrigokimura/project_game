import shelve


class Storage:
    def store(self, data):
        with shelve.open("db") as d:
            d["save"] = data
        print("Data stored to db file")

    def read(self):
        print("Reading data from db file")
        with shelve.open("db") as d:
            return d["save"]
