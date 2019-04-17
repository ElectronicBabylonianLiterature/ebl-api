import attr

from ebl.fragmentarium.update_signs import Counter, create_updater
from ebl.tests.factories.fragment import TransliteratedFragmentFactory


def test_update_signs(fragment_repository,
                      sign_list,
                      signs):
    transliterated_fragment = TransliteratedFragmentFactory.build()
    fragment_without_signs = attr.evolve(transliterated_fragment, signs=None)
    for sign in signs:
        sign_list.create(sign)
    number = fragment_repository.create(fragment_without_signs)

    create_updater(sign_list, fragment_repository, Counter)()

    assert fragment_repository.find(number) == transliterated_fragment
