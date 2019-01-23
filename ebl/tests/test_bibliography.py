from freezegun import freeze_time
import pydash
import pytest
from ebl.errors import NotFoundError, DuplicateError


ENTRY = {
    "id": "Q30000000",
    "title": ("The Synergistic Activity of Thyroid Transcription Factor 1 and "
              "Pax 8 Relies on the Promoter/Enhancer Interplay"),
    "type": "article-journal",
    "DOI": "10.1210/MEND.16.4.0808",
    "issued": {
        "date-parts": [
            [
                2002,
                1,
                1
            ]
        ]
    },
    "PMID": "11923479",
    "volume": "16",
    "page": "837-846",
    "issue": "4",
    "container-title": "Molecular Endocrinology",
    "author": [
        {
            "given": "Stefania",
            "family": "Miccadei",
            "_ordinal": 1
        },
        {
            "given": "Rossana",
            "family": "De Leo",
            "_ordinal": 2
        },
        {
            "given": "Enrico",
            "family": "Zammarchi",
            "_ordinal": 3
        },
        {
            "given": "Pier Giorgio",
            "family": "Natali",
            "_ordinal": 4
        },
        {
            "given": "Donato",
            "family": "Civitareale",
            "_ordinal": 5
        }
    ]
}


MONGO_ENTRY = pydash.map_keys(
    ENTRY,
    lambda _, key: '_id' if key == 'id' else key
)


COLLECTION = 'bibliography'


def test_create(database, bibliography, user):
    bibliography.create(ENTRY, user)

    assert database[COLLECTION].find_one({'_id': ENTRY['id']}) == MONGO_ENTRY


def test_create_duplicate(bibliography, user):
    bibliography.create(ENTRY, user)
    with pytest.raises(DuplicateError):
        bibliography.create(ENTRY, user)


def test_find(database, bibliography):
    database[COLLECTION].insert_one(MONGO_ENTRY)

    assert bibliography.find(ENTRY['id']) == ENTRY


def test_entry_not_found(bibliography):
    with pytest.raises(NotFoundError):
        bibliography.find('not found')


def test_update(bibliography, user):
    updated_entry = pydash.omit({
        **ENTRY,
        'title': 'New Title'
    }, 'PMID')
    bibliography.create(ENTRY, user)
    bibliography.update(updated_entry, user)

    assert bibliography.find(ENTRY['id']) == updated_entry


@freeze_time("2018-09-07 15:41:24.032")
def test_changelog(bibliography,
                   database,
                   user,
                   make_changelog_entry):
    updated_entry = {
        **ENTRY,
        'title': 'New Title'
    }
    bibliography.create(ENTRY, user)
    bibliography.update(updated_entry, user)

    expected_changelog = [
        make_changelog_entry(
            COLLECTION,
            ENTRY['id'],
            {'_id': ENTRY['id']},
            MONGO_ENTRY
        ),
        make_changelog_entry(
            COLLECTION,
            ENTRY['id'],
            MONGO_ENTRY,
            pydash.map_keys(
                updated_entry,
                lambda _, key: ('_id' if key == 'id' else key)
            )
        )
    ]

    assert [change for change in database['changelog'].find(
        {'resource_id': ENTRY['id']},
        {'_id': 0}
    )] == expected_changelog


def test_update_not_found(bibliography, user):
    with pytest.raises(NotFoundError):
        bibliography.update(ENTRY, user)
