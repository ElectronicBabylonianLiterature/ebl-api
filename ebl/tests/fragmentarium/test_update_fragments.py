import attr

from ebl.fragmentarium.update_fragments import update_fragments
from ebl.tests.factories.fragment import TransliteratedFragmentFactory


def test_update_fragments(
    context, signs, when,
):

    fragment_repository = context.fragment_repository
    sign_repository = context.sign_repository
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragment_without_signs = attr.evolve(transliterated_fragment, signs=None)
    for sign in signs:
        sign_repository.of_single(sign)
    number = fragment_repository.of_single(fragment_without_signs)

    update_fragments([number], 0, lambda: context)

    assert (
        fragment_repository.query_by_fragment_number(number) == transliterated_fragment
    )
