class MongoFragmentarium(object):

    def __init__(self, database):
        self.database = database

    def create(self, fragment):
        return self.database.words.insert_one(fragment).inserted_id

    def find(self, number):
        word = self.database.words.find_one({'_id': number})

        if word is None:
            raise KeyError
        else:
            return word
