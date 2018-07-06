import json
import falcon
import pydash
from bson.objectid import ObjectId
from bson.errors import InvalidId


class WordsResource:

    def __init__(self, dictionary):
        self.dictionary = dictionary

    def on_get(self, _req, resp, object_id):
        try:
            word = self.dictionary.find(ObjectId(object_id))
            resp.media = pydash.defaults({'_id': object_id}, word)
        except (KeyError, InvalidId):
            resp.status = falcon.HTTP_NOT_FOUND

    def on_post(self, req, resp, object_id):
        try:
            word = json.loads(req.stream.read())
            word['_id'] = ObjectId(object_id)
            self.dictionary.update(word)
        except (KeyError, InvalidId):
            resp.status = falcon.HTTP_NOT_FOUND
