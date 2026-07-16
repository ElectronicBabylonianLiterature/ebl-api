from collections import Counter
from typing import Dict, List, Sequence, Type, cast

from falcon import Request, Response, before
from marshmallow import Schema, ValidationError

from ebl.errors import DataError
from ebl.fragmentarium.application.fragment_finder import FragmentFinder
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.application.named_entity_schema import (
    EntityAnnotationSpanSchema,
    NamedEntitySchema,
    RealiaAnnotationSpanSchema,
    RealiaEntitySchema,
)
from ebl.fragmentarium.domain.fragment import Fragment
from ebl.fragmentarium.domain.named_entity import (
    AnnotationSpan,
    EntityAnnotationSpan,
    RealiaAnnotationSpan,
    deduplicate_spans,
)
from ebl.fragmentarium.web.dtos import FragmentDtoFactory, parse_museum_number
from ebl.realia.application.realia_repository import RealiaRepository
from ebl.users.web.require_scope import require_scope

NAMED_ENTITIES_KEY = "namedEntities"
REALIA_KEY = "realia"


class NamedEntityResource:
    def __init__(
        self,
        finder: FragmentFinder,
        updater: FragmentUpdater,
        realia_repository: RealiaRepository,
        dto_factory: FragmentDtoFactory,
    ):
        self._finder = finder
        self._updater = updater
        self._realia_repository = realia_repository
        self._dto_factory = dto_factory

    def _create_spans(
        self, entities: Sequence, entity_schema: Type[Schema], word_ids: Dict[str, list]
    ) -> List[dict]:
        return [
            {
                **cast(dict, entity_schema().dump(entity)),
                "span": word_ids.get(entity.id, []),
            }
            for entity in entities
        ]

    def _word_ids_by_annotation(self, fragment: Fragment) -> Dict[str, list]:
        word_ids: Dict[str, list] = {}
        for word in fragment.words:
            for entity_id in [*word.named_entities, *word.realia]:
                word_ids.setdefault(entity_id, []).append(word.id_)
        return word_ids

    def _load(self, data, schema: Type[Schema], key: str) -> List:
        try:
            return cast(List, schema().load(data.get(key, []), many=True))
        except ValidationError as error:
            raise DataError(f"Invalid '{key}': {error.messages}") from error

    def _validate_unique_ids(self, annotations: Sequence[AnnotationSpan]) -> None:
        counts = Counter(annotation.id for annotation in annotations)
        duplicates = sorted(id_ for id_, count in counts.items() if count > 1)
        if duplicates:
            raise DataError(
                f"Conflicting annotation ids: {', '.join(duplicates)}. "
                "Each annotation must have a unique id."
            )

    def _validate_realia_ids(self, spans: Sequence[RealiaAnnotationSpan]) -> None:
        requested = {span.realia_id for span in spans}
        if not requested:
            return
        found = {
            entry.realia_id
            for entry in self._realia_repository.find_by_realia_ids(sorted(requested))
        }
        missing = sorted(requested - found)
        if missing:
            raise DataError(f"Unknown realiaId: {', '.join(missing)}.")

    def on_get(self, req: Request, resp: Response, number: str):
        fragment, _ = self._finder.find(parse_museum_number(number))
        word_ids = self._word_ids_by_annotation(fragment)
        resp.media = {
            NAMED_ENTITIES_KEY: self._create_spans(
                fragment.named_entities, NamedEntitySchema, word_ids
            ),
            REALIA_KEY: self._create_spans(
                fragment.realia, RealiaEntitySchema, word_ids
            ),
        }

    @before(require_scope, "transliterate:fragments")
    def on_post(self, req: Request, resp: Response, number: str) -> None:
        user = req.context["user"]
        entity_spans: List[EntityAnnotationSpan] = deduplicate_spans(
            self._load(req.media, EntityAnnotationSpanSchema, NAMED_ENTITIES_KEY)
        )
        realia_spans: List[RealiaAnnotationSpan] = deduplicate_spans(
            self._load(req.media, RealiaAnnotationSpanSchema, REALIA_KEY)
        )

        self._validate_unique_ids([*entity_spans, *realia_spans])
        self._validate_realia_ids(realia_spans)

        updated_fragment, has_photo = self._updater.update_named_entities(
            parse_museum_number(number), entity_spans, realia_spans, user
        )
        resp.media = self._dto_factory.create(updated_fragment, user, has_photo)
