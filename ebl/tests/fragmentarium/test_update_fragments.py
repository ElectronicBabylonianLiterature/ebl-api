import attr

from ebl.fragmentarium.update_fragments import update_fragments
from ebl.tests.factories.fragment import TransliteratedFragmentFactory


def test_update_fragments(context, signs, when):
    fragment_repository = context.fragment_repository
    sign_repository = context.sign_repository
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragment_without_signs = attr.evolve(transliterated_fragment, signs=None)
    number = fragment_without_signs.number
    for sign in signs:
        sign_repository.create(sign)
    fragment_repository.create(fragment_without_signs)

    update_fragments([number], 0, lambda: context, False)

    assert fragment_repository.query_by_museum_number(number) == transliterated_fragment


def test_update_fragments_line_to_vec(context, when):
    fragment_repository = context.fragment_repository
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragment_without_signs = attr.evolve(transliterated_fragment, line_to_vec=None)
    fragment_repository.create(fragment_without_signs)
    number = fragment_without_signs.number
    update_fragments([number], 0, lambda: context, True)

    assert fragment_repository.query_by_museum_number(number) == transliterated_fragment
