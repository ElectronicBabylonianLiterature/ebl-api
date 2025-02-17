from falcon import Request, Response

from ebl.fragmentarium.web.introductions import IntroductionResource
from ebl.fragmentarium.web.notes import NotesResource
from ebl.fragmentarium.web.transliterations import TransliterationResource


class EditionResource:
    def __init__(
        self,
        transliteration_resource: TransliterationResource,
        notes_resource: NotesResource,
        introduction_resource: IntroductionResource,
    ):
        self._update_resources = {
            "transliteration": transliteration_resource,
            "notes": notes_resource,
            "introduction": introduction_resource,
        }

    def on_post(self, req: Request, resp: Response, number: str) -> None:
        for field, resource in self._update_resources.items():
            if field in req.media:
                resource.on_post(req, resp, number)
