from typing import List
from falcon import Request, Response, before


from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.application.named_entity_schema import (
    EntityAnnotationSpanSchema,
    NamedEntitySchema,
)
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.web.dtos import create_response_dto, parse_museum_number
from ebl.marshmallowschema import validate
from ebl.transliteration.domain.word_tokens import AbstractWord
from ebl.users.web.require_scope import require_scope


class NamedEntityResource:
    def __init__(self, finder: FragmentFinder, updater: FragmentUpdater):
        self._finder = finder
        self._updater = updater

    def _create_annotation_spans(self, fragment: Fragment) -> List[dict]:
        annotation_spans = {
            entity.id: {**NamedEntitySchema().dump(entity), "span": []}
            for entity in fragment.named_entities
        }
        for line in fragment.text.text_lines:
            for token in line.content:
                if isinstance(token, AbstractWord) and token.id_:
                    for entity_id in token.named_entities:
                        annotation_spans[entity_id]["span"].append(token.id_)

        return list(annotation_spans.values())

    @validate(None, EntityAnnotationSpanSchema(many=True))
    def on_get(self, req: Request, resp: Response, number: str):
        fragment, _ = self._finder.find(parse_museum_number(number))
        resp.media = (
            self._create_annotation_spans(fragment) if fragment.named_entities else []
        )

    @before(require_scope, "transliterate:fragments")
    def on_post(self, req: Request, resp: Response, number: str) -> None:
        user = req.context.user
        data = req.media["annotations"]
        annotations = EntityAnnotationSpanSchema().load(data, many=True)

        updated_fragment, has_photo = self._updater.update_named_entities(
            parse_museum_number(number),
            annotations,
            user,
        )
        resp.media = create_response_dto(updated_fragment, user, has_photo)
