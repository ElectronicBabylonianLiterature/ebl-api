import json
import falcon
import pydash
from bson.objectid import ObjectId
from bson.errors import InvalidId
from ebl.require_scope import require_scope


class WordsResource:

    def __init__(self, dictionary, fetch_user_profile):
        self._dictionary = dictionary
        self._fetch_user_profile = fetch_user_profile

    @falcon.before(require_scope, 'read:words')
    def on_get(self, _req, resp, object_id):
        try:
            word = self._dictionary.find(ObjectId(object_id))
            resp.media = pydash.defaults({'_id': object_id}, word)
        except (KeyError, InvalidId):
            resp.status = falcon.HTTP_NOT_FOUND

    @falcon.before(require_scope, 'write:words')
    def on_post(self, req, resp, object_id):
        user_profile = self._fetch_user_profile(req)
        try:
            word = json.loads(req.stream.read())
            word['_id'] = ObjectId(object_id)
            self._dictionary.update(word, user_profile)
        except (KeyError, InvalidId):
            resp.status = falcon.HTTP_NOT_FOUND
