import falcon
from bson.objectid import ObjectId
from bson.errors import InvalidId

class WordsResource:

    def __init__(self, dictionary):
        self.dictionary = dictionary

    def on_get(self, req, resp, object_id):

        try:
            word = self.dictionary.find(ObjectId(object_id))
            word['_id'] = object_id
            resp.media = word
        except (KeyError, InvalidId):
            resp.status = falcon.HTTP_NOT_FOUND
