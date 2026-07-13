from typing import List, Sequence, cast
from falcon import Request, Response, before
from marshmallow import ValidationError


from ebl.errors import DataError, NotFoundError
from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.application.named_entity_schema import (
    AnnotationEntitySchema,
    AnnotationSpanSchema,
)
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.named_entity import AnnotationSpan, RealiaAnnotationSpan
from ebl.fragmentarium.web.dtos import create_response_dto, parse_museum_number
from ebl.marshmallowschema import validate
from ebl.realia.application.realia_repository import RealiaRepository
from ebl.users.web.require_scope import require_scope


class NamedEntityResource:
    def __init__(
        self,
        finder: FragmentFinder,
        updater: FragmentUpdater,
        realia_repository: RealiaRepository,
    ):
        self._finder = finder
        self._updater = updater
        self._realia_repository = realia_repository

    def _create_annotation_spans(self, fragment: Fragment) -> List[dict]:
        annotation_spans = {
            entity.id: {**cast(dict, AnnotationEntitySchema().dump(entity)), "span": []}
            for entity in fragment.named_entities
        }
        for word in fragment.words:
            for entity_id in word.named_entities:
                annotation_spans[entity_id]["span"].append(word.id_)

        return list(annotation_spans.values())

    def _parse_annotations(self, data) -> List[AnnotationSpan]:
        try:
            return cast(
                List[AnnotationSpan], AnnotationSpanSchema().load(data, many=True)
            )
        except ValidationError as error:
            raise DataError(
                f"Invalid named entity annotations: {error.messages}"
            ) from error

    def _validate_realia_ids(self, annotations: Sequence[AnnotationSpan]) -> None:
        realia_ids = {
            annotation.realia_id
            for annotation in annotations
            if isinstance(annotation, RealiaAnnotationSpan)
        }
        for realia_id in sorted(realia_ids):
            try:
                self._realia_repository.find_by_realia_id(realia_id)
            except NotFoundError as error:
                raise DataError(f"Unknown realiaId '{realia_id}'.") from error

    @validate(None, AnnotationSpanSchema(many=True))
    def on_get(self, req: Request, resp: Response, number: str):
        fragment, _ = self._finder.find(parse_museum_number(number))
        resp.media = (
            self._create_annotation_spans(fragment) if fragment.named_entities else []
        )

    @before(require_scope, "transliterate:fragments")
    def on_post(self, req: Request, resp: Response, number: str) -> None:
        user = req.context["user"]
        annotations = self._parse_annotations(req.media["annotations"])
        self._validate_realia_ids(annotations)

        updated_fragment, has_photo = self._updater.update_named_entities(
            parse_museum_number(number),
            annotations,
            user,
        )
        resp.media = create_response_dto(updated_fragment, user, has_photo)
