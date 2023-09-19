import pytest
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema
from ebl.tests.common.ngram_test_support import ngrams_from_signs, N_VALUES


@pytest.mark.parametrize(
    "N",
    N_VALUES,
)
@pytest.mark.parametrize(
    "N_NEW",
    N_VALUES,
)
def test_update_fragment_ngrams(
    fragment_repository, fragment_ngram_repository, N, N_NEW
):
    fragment = TransliteratedFragmentFactory.build()
    number = MuseumNumberSchema().dump(fragment.number)
    fragment_id = fragment_repository.create(fragment)

    assert not fragment_ngram_repository._ngrams.exists({"_id": fragment_id})

    fragment_ngram_repository.update_ngrams(number, N)
    ngrams = ngrams_from_signs(fragment.signs, N)
    assert fragment_ngram_repository.get_ngrams(fragment_id) == ngrams

    fragment_ngram_repository.update_ngrams(number, N_NEW)
    ngrams = ngrams_from_signs(fragment.signs, N_NEW)
    assert fragment_ngram_repository.get_ngrams(fragment_id) == ngrams
