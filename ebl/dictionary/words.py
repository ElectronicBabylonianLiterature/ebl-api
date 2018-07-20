import json
import falcon
import pydash
from bson.objectid import ObjectId
from bson.errors import InvalidId
from ebl.require_scope import require_scope


class WordsResource:

    def __init__(self, dictionary):
        self._dictionary = dictionary

    @falcon.before(require_scope, 'read:words')
    def on_get(self, _req, resp, object_id):
        try:
            word = self._dictionary.find(ObjectId(object_id))
            resp.media = pydash.defaults({'_id': object_id}, word)
        except (KeyError, InvalidId):
            resp.status = falcon.HTTP_NOT_FOUND

    @falcon.before(require_scope, 'write:words')
    def on_post(self, req, resp, object_id):
        try:
            word = json.loads(req.stream.read())
            word['_id'] = ObjectId(object_id)
            self._dictionary.update(word)
        except (KeyError, InvalidId):
            resp.status = falcon.HTTP_NOT_FOUND
