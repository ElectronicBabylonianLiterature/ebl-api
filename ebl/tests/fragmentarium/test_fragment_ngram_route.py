import pytest
from ebl.tests.factories.fragment import TransliteratedFragmentFactory
from ebl.tests.common.ngram_test_support import ngrams_from_signs, N_VALUES
import falcon

from ebl.transliteration.application.museum_number_schema import MuseumNumberSchema


@pytest.mark.parametrize(
    "N",
    N_VALUES,
)
@pytest.mark.parametrize("pre_generate_ngrams", [True, False])
def test_update_fragment_ngrams(
    client, fragmentarium, fragment_ngram_repository, N, pre_generate_ngrams
):
    fragment = TransliteratedFragmentFactory.build()
    fragment_id = fragmentarium.create(fragment)

    if pre_generate_ngrams:
        number = MuseumNumberSchema().dump(fragment.number)
        fragment_ngram_repository.update_ngrams(number, N)

    result = client.simulate_get(f"/fragments/{fragment_id}/ngrams", params={"n": N})

    assert result.status == falcon.HTTP_OK
    assert {tuple(ngram) for ngram in result.json} == ngrams_from_signs(
        fragment.signs, N
    )
