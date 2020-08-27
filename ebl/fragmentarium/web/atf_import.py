import falcon  # pyre-ignore
from falcon.media.validators.jsonschema import validate

from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.web.dtos import create_response_dto
from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.transliteration_error import TransliterationError
from ebl.users.web.require_scope import require_scope

from ebl.atf_importer.application.atf_importer import ATF_Importer

class ATF_ImportResource:

    auth = {"auth_disabled": True}

    def __init__(self):
        pass

    def on_get(self, req, resp: falcon.Response) -> None:  # pyre-ignore[11]

        importer = ATF_Importer()
        importer.start()

        resp.media = "XXXXXYYYY"

    #@falcon.before(require_scope, "transliterate:fragments")
    #@validate(TRANSLITERATION_DTO_SCHEMA)
    def on_post(self, req, resp, number):
        try:
            print("XXXX")
            importer = ATF_Importer()
            importer.start()

        except TransliterationError as error:
            resp.status = falcon.HTTP_UNPROCESSABLE_ENTITY
            resp.media = {
                "title": resp.status,
                "description": str(error),
                "errors": error.errors,
            }

    def _create_transliteration(self, media):
        return self._transliteration_factory.create(
            Atf(media["transliteration"]), media["notes"]
        )
