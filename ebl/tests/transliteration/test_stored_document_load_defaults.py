import json
from typing import Any, Dict, Type, cast

import pytest
from factory.base import Factory
from marshmallow import Schema

from ebl.corpus.application.schemas import ChapterSchema, TextSchema
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.provenance.application.provenance_service import ProvenanceService
from ebl.tests.factories.corpus import ChapterFactory, TextFactory
from ebl.tests.factories.fragment import (
    LemmatizedFragmentFactory,
    TransliteratedFragmentFactory,
)
from ebl.tests.fragmentarium.stored_line_shapes import sparse_tokens
from ebl.tests.transliteration.storage_test_helpers import stored_dump


def assert_sparse_document_loads_equal(schema: Schema, document: object) -> None:
    full = cast(Dict[str, Any], schema.dump(document))
    stored = stored_dump(schema, document)

    assert stored == sparse_tokens(full)
    assert len(json.dumps(stored, default=str)) < len(json.dumps(full, default=str))
    assert schema.load(stored) == schema.load(full)


@pytest.mark.parametrize(
    "factory", [TransliteratedFragmentFactory, LemmatizedFragmentFactory]
)
def test_a_stored_fragment_is_sparse_and_loads_equal_to_the_full_fragment(
    factory: Type[Factory], seeded_provenance_service: ProvenanceService
) -> None:
    schema = FragmentSchema(context={"provenance_service": seeded_provenance_service})

    assert_sparse_document_loads_equal(schema, factory.build())


def test_a_stored_chapter_is_sparse_and_loads_equal_to_the_full_chapter(
    seeded_provenance_service: ProvenanceService,
) -> None:
    schema = ChapterSchema(context={"provenance_service": seeded_provenance_service})

    assert_sparse_document_loads_equal(schema, ChapterFactory.build())


def test_a_stored_text_is_sparse_and_loads_equal_to_the_full_text(
    seeded_provenance_service: ProvenanceService,
) -> None:
    schema = TextSchema(context={"provenance_service": seeded_provenance_service})

    assert_sparse_document_loads_equal(schema, TextFactory.build())
