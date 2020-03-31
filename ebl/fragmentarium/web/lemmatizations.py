import falcon  # pyre-ignore
from falcon.media.validators.jsonschema import validate

from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.transliteration.domain.lemmatization import Lemmatization
from ebl.users.web.require_scope import require_scope

LEMMATIZATION_DTO_SCHEMA = {
    "type": "object",
    "properties": {
        "lemmatization": {
            "type": "array",
            "items": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "value": {"type": "string"},
                        "uniqueLemma": {"type": "array", "items": {"type": "string"},},
                    },
                    "required": ["value"],
                },
            },
        }
    },
    "required": ["lemmatization"],
}


class LemmatizationResource:
    def __init__(self, updater: FragmentUpdater):
        self._updater = updater

    @falcon.before(require_scope, "lemmatize:fragments")
    @validate(LEMMATIZATION_DTO_SCHEMA)
    def on_post(self, req, resp, number):
        user = req.context.user
        updated_fragment, has_photo = self._updater.update_lemmatization(
            number, Lemmatization.from_list(req.media["lemmatization"]), user
        )
        resp.media = create_response_dto(updated_fragment, user, has_photo)
