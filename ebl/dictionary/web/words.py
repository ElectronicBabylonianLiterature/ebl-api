import falcon

from ebl.dictionary.application.word_schema import WordSchema
from ebl.marshmallowschema import validate
from ebl.users.web.require_scope import require_scope


class WordsResource:
    def __init__(self, dictionary):
        self._dictionary = dictionary

    def on_get(self, _req, resp, object_id):
        resp.media = self._dictionary.find(object_id)

    @falcon.before(require_scope, "write:words")
    @validate(WordSchema())
    def on_post(self, req, resp, object_id):
        word = {**req.media, "_id": object_id}
        self._dictionary.update(word, req.context.user)
        resp.status = falcon.HTTP_NO_CONTENT


class WordsListResource:
    def __init__(self, dictionary):
        self._dictionary = dictionary

    def on_get(self, req, resp):
        resp.media = self._dictionary.list_all_words()
