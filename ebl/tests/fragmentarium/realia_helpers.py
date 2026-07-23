from typing import Sequence

from ebl.fragmentarium.domain.named_entity import RealiaAnnotationSpan
from ebl.realia.infrastructure.realia_schemas import RealiaEntrySchema
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.tests.factories.realia import RealiaEntryFactory


def store_realia(realia_repository, realia_id: str, lemma: str, type_) -> None:
    entry = RealiaEntryFactory.build(
        id=lemma,
        realia_id=realia_id,
        type=type_,
        related_terms=(),
        references=(),
        reallexikon=(),
    )
    realia_repository._realia_collection.insert_one(RealiaEntrySchema().dump(entry))


def create_realia_fragment(
    fragmentarium, realia_spans: Sequence[RealiaAnnotationSpan], **kwargs
):
    fragment = TransliteratedFragmentFactory.build(**kwargs).set_token_ids()
    fragment = fragment.set_named_entities([], realia_spans)
    fragmentarium.create(fragment)
    return fragment
