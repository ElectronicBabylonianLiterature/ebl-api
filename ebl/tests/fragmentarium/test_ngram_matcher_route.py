from typing import List
from ebl.common.infrastructure.ngrams import NGRAM_N_VALUES
from ebl.corpus.application.id_schemas import ChapterIdSchema
from ebl.corpus.application.text_repository import TextRepository
from ebl.corpus.domain.chapter import Chapter
from ebl.fragmentarium.application.fragment_repository import FragmentRepository
from ebl.tests.common.ngram_test_support import compute_overlap
from ebl.tests.factories.corpus import ChapterFactory
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
import falcon

SIGNS = ["X BA KU ABZ075", "KI DU ABZ411 BA MA TI\nX MU TA MA UD", "KU ABZ411 MA KI"]


def test_match_fragment_ngrams(
    client,
    fragment_repository: FragmentRepository,
    text_repository: TextRepository,
):
    fragment = TransliteratedFragmentFactory.build()
    fragment_id = fragment_repository.create(fragment)
    chapters: List[Chapter] = [ChapterFactory.build(signs=(signs,)) for signs in SIGNS]

    for chapter in chapters:
        text_repository.create_chapter(chapter)

    result = client.simulate_get(f"/fragments/{fragment_id}/ngrams")

    assert result.status == falcon.HTTP_OK
    assert result.json == sorted(
        (
            {
                **ChapterIdSchema().dump(chapter.id_),
                "overlap": compute_overlap(fragment, chapter, NGRAM_N_VALUES),
            }
            for chapter in chapters
        ),
        key=lambda item: item["overlap"],
        reverse=True,
    )
