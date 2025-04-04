import falcon

from ebl.dictionary.application.word_repository import WordRepository
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.web.dtos import create_response_dto, parse_museum_number
from ebl.users.web.require_scope import require_scope
from falcon.media.validators.jsonschema import validate

LINE_INDEX = "^[0-9]+$"
TOKEN_INDEX = "^[0-9]+$"
LEMMA_ID = "string"

LINE_ANNOTATION_SCHEMA = {
    "type": "object",
    "patternProperties": {
        LINE_INDEX: {
            "type": "object",
            "patternProperties": {
                TOKEN_INDEX: {"type": "array", "items": {"type": LEMMA_ID}}
            },
            "additionalProperties": False,
        }
    },
    "additionalProperties": False,
}


def cast_int_keys(data):
    if not isinstance(data, dict):
        return data
    return {int(key): cast_int_keys(value) for key, value in data.items()}


class LemmaAnnotationResource:
    def __init__(self, updater: FragmentUpdater):
        self._updater = updater

    @falcon.before(require_scope, "lemmatize:fragments")
    @validate(LINE_ANNOTATION_SCHEMA)
    def on_post(self, req, resp, number):
        user = req.context.user
        updated_fragment, has_photo = self._updater.update_lemma_annotation(
            parse_museum_number(number),
            cast_int_keys(req.media),
            user,
        )
        resp.media = create_response_dto(updated_fragment, user, has_photo)


class AutofillLemmasResource:
    def __init__(
        self,
        fragment_repository: FragmentRepository,
        word_repository: WordRepository,
    ):
        self._fragment_repository = fragment_repository
        self._word_repository = word_repository

    def _collect_words(self, suggestions: dict) -> dict:
        words = self._word_repository.query_by_ids(
            list(
                {
                    lemma_id
                    for unique_lemma in suggestions.values()
                    for lemma_id in unique_lemma
                }
            )
        )
        return {word["_id"]: word for word in words}

    @falcon.before(require_scope, "lemmatize:fragments")
    def on_get(self, req, resp, number: str):
        museum_number = parse_museum_number(number)
        suggestions = self._fragment_repository.collect_lemmas(museum_number)
        words = self._collect_words(suggestions)

        resp.media = {
            key: [words[lemma] for lemma in unique_lemma]
            for key, unique_lemma in suggestions.items()
        }
