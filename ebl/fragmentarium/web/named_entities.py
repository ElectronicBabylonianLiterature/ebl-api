from typing import List
from falcon import Request, Response

from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.application.named_entity_schema import (
    EntityAnnotationSpan,
    EntityAnnotationSpanSchema,
    NamedEntitySchema,
)
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.web.dtos import parse_museum_number
from ebl.marshmallowschema import validate
from ebl.transliteration.domain.word_tokens import AbstractWord


class NamedEntityResource:
    def __init__(self, finder: FragmentFinder):
        self._finder = finder

    def _create_annotation_spans(
        self, fragment: Fragment
    ) -> List[EntityAnnotationSpan]:
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
