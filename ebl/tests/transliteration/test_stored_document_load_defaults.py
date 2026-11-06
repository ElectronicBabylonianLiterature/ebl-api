import json

import pytest
from marshmallow import Schema

from ebl.corpus.application.schemas import ChapterSchema, TextSchema
from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.tests.factories.corpus import ChapterFactory, TextFactory
from ebl.tests.factories.fragment import (
    LemmatizedFragmentFactory,
    TransliteratedFragmentFactory,
)
from ebl.tests.fragmentarium.stored_line_shapes import sparse_tokens
from ebl.tests.transliteration.storage_test_helpers import stored_dump


def assert_sparse_document_loads_equal(schema: Schema, document: object) -> None:
    stored = stored_dump(schema, document)
    sparse = sparse_tokens(stored)

    assert len(json.dumps(sparse, default=str)) < len(json.dumps(stored, default=str))
    assert schema.load(sparse) == schema.load(stored)


@pytest.mark.parametrize(
    "factory", [TransliteratedFragmentFactory, LemmatizedFragmentFactory]
)
def test_a_sparse_fragment_loads_equal_to_the_stored_fragment(
    factory, seeded_provenance_service
):
    schema = FragmentSchema(context={"provenance_service": seeded_provenance_service})

    assert_sparse_document_loads_equal(schema, factory.build())


def test_a_sparse_chapter_loads_equal_to_the_stored_chapter(seeded_provenance_service):
    schema = ChapterSchema(context={"provenance_service": seeded_provenance_service})

    assert_sparse_document_loads_equal(schema, ChapterFactory.build())


def test_a_sparse_text_loads_equal_to_the_stored_text(seeded_provenance_service):
    schema = TextSchema(context={"provenance_service": seeded_provenance_service})

    assert_sparse_document_loads_equal(schema, TextFactory.build())
