import falcon

from ebl.dictionary.application.word_schema import (
    WordSchema,
    ProperNounCreationRequestSchema,
)
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


class ProperNounCreationResource:
    def __init__(self, dictionary):
        self._dictionary = dictionary

    @staticmethod
    def _is_valid_created_word_payload(word: object) -> bool:
        if not isinstance(word, dict):
            return False

        lemma = word.get("lemma")
        pos = word.get("pos")
        word_id = word.get("_id")

        return (
            isinstance(word_id, str)
            and isinstance(lemma, list)
            and all(isinstance(lemma_item, str) for lemma_item in lemma)
            and isinstance(pos, list)
            and all(isinstance(pos_item, str) for pos_item in pos)
        )

    @falcon.before(require_scope, "create:proper_nouns")
    @validate(ProperNounCreationRequestSchema())
    def on_post(self, req, resp):
        request_data = ProperNounCreationRequestSchema().load(req.media)
        lemma = request_data["lemma"]
        pos_tags = request_data["pos"]
        word_id = self._dictionary.create_proper_noun(lemma, pos_tags)
        if not isinstance(word_id, str) or not word_id:
            raise falcon.HTTPInternalServerError(
                description="Proper noun creation failed to return a valid word id."
            )
        word = self._dictionary.find(word_id)
        if not self._is_valid_created_word_payload(word):
            raise falcon.HTTPInternalServerError(
                description="Created proper noun could not be retrieved as a valid word."
            )
        resp.media = word
        resp.status = falcon.HTTP_CREATED
