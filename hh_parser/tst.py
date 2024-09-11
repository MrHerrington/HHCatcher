class DBManager:
    def __init__(self, lst):
        self.lst = lst

    def __getattribute__(self, item):
        try:
            return sum(object.__getattribute__(self, item))
        except AttributeError:
            return 'bibas'


a = DBManager([1, 2, 3])
a.dct = [1, 2, 3]
print(a.lst)