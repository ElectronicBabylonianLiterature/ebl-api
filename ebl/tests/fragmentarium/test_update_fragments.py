import builtins
from io import StringIO

import attr

from ebl.fragmentarium.update_fragments import update_fragments
from ebl.tests.factories.fragment import TransliteratedFragmentFactory


def test_update_fragments(
    fragment_repository,
    sign_repository,
    signs,
    transliteration_factory,
    fragment_updater,
    when,
):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragment_without_signs = attr.evolve(transliterated_fragment, signs=None)
    for sign in signs:
        sign_repository.create(sign)
    number = fragment_repository.create(fragment_without_signs)

    file = StringIO()
    when(builtins).open("invalid_fragments.tsv", "w", encoding="utf-8").thenReturn(file)
    update_fragments(fragment_repository, transliteration_factory, fragment_updater)

    assert (
        fragment_repository.query_by_fragment_number(number) == transliterated_fragment
    )
