from typing import cast

import attr

from ebl.fragmentarium.application.fragment_schema import FragmentSchema
from ebl.tests.factories.fragment import LemmatizedFragmentFactory
from ebl.tests.transliteration.storage_test_helpers import has_key, stored_dump
from ebl.transliteration.domain.atf_parsers.lark_parser import parse_atf_lark

COLLECTION = "fragments"
NAME_BREAK_ATF = "1. k[u-nu]-uš\n2. ku"


def find_stored_text(database, fragment) -> dict:
    return database[COLLECTION].find_one({"_id": str(fragment.number)})["text"]


def test_created_fragment_omits_default_token_fields(database, fragment_repository):
    fragment = LemmatizedFragmentFactory.build()

    fragment_repository.create(fragment)

    assert has_key(cast(dict, FragmentSchema().dump(fragment))["text"], "erasure")
    assert not has_key(find_stored_text(database, fragment), "erasure")


def test_created_fragment_loads_back_unchanged(fragment_repository):
    fragment = LemmatizedFragmentFactory.build()

    fragment_repository.create(fragment)

    assert fragment_repository.query_by_museum_number(fragment.number) == fragment


def test_updated_transliteration_keeps_only_real_name_breaks(
    database, fragment_repository
):
    fragment = LemmatizedFragmentFactory.build()
    fragment_repository.create(fragment)
    updated = attr.evolve(fragment, text=parse_atf_lark(NAME_BREAK_ATF))

    fragment_repository.update_field("transliteration", updated)

    stored_text = find_stored_text(database, fragment)
    broken_line, plain_line = stored_text["lines"]
    assert stored_text == stored_dump(FragmentSchema(only=["text"]), updated)["text"]
    assert has_key(broken_line, "nameBreaks")
    assert not has_key(plain_line, "nameBreaks")
    assert fragment_repository.query_by_museum_number(fragment.number) == updated
