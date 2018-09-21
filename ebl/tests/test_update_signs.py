import pydash
from ebl.fragmentarium.update_signs import create_updater
from ebl.fragmentarium.update_signs import Counter


def test_update_signs(fragment_repository,
                      sign_list,
                      signs, transliterated_fragment):
    fragment_without_signs = pydash.omit(transliterated_fragment, 'signs')
    for sign in signs:
        sign_list.create(sign)
    number = fragment_repository.create(fragment_without_signs)

    create_updater(sign_list, fragment_repository, Counter)()

    assert fragment_repository.find(number) == transliterated_fragment
