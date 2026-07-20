from ebl.tests.factories.afo_register import (
    AfoRegisterRecordFactory,
    AfoRegisterRecordSuggestionFactory,
)
from ebl.afo_register.application.afo_register_repository import AfoRegisterRepository
from natsort import natsorted


def test_find_by_id(afo_register_repository: AfoRegisterRepository):
    afo_register_record = AfoRegisterRecordFactory.build()
    id = afo_register_repository.create(afo_register_record)
    afo_register_repository.create(AfoRegisterRecordFactory.build())

    assert afo_register_repository.search({"_id": id}) == [afo_register_record]


def test_find_by_afo_number_and_page(afo_register_repository: AfoRegisterRepository):
    afo_register_record = AfoRegisterRecordFactory.build()
    afo_register_repository.create(afo_register_record)
    afo_register_repository.create(AfoRegisterRecordFactory.build())

    assert afo_register_repository.search(
        {
            "afoNumber": afo_register_record.afo_number,
            "page": afo_register_record.page,
        }
    ) == [afo_register_record]


def test_find_by_all_record_parameters(afo_register_repository: AfoRegisterRepository):
    afo_register_record = AfoRegisterRecordFactory.build()
    afo_register_repository.create(afo_register_record)
    afo_register_repository.create(AfoRegisterRecordFactory.build())

    assert afo_register_repository.search(
        {
            "afoNumber": afo_register_record.afo_number,
            "page": afo_register_record.page,
            "text": afo_register_record.text,
            "textNumber": afo_register_record.text_number,
            "linesDiscussed": afo_register_record.lines_discussed,
            "discussedBy": afo_register_record.discussed_by,
            "discussedByNotes": afo_register_record.discussed_by_notes,
        }
    ) == [afo_register_record]


def test_search_by_texts_and_numbers(afo_register_repository: AfoRegisterRepository):
    record1 = AfoRegisterRecordFactory.build(text="Text1", text_number="1")
    record2 = AfoRegisterRecordFactory.build(text="Text2", text_number="2")
    record3 = AfoRegisterRecordFactory.build(text="Text3", text_number="3")
    afo_register_repository.create(record1)
    afo_register_repository.create(record2)
    afo_register_repository.create(record3)
    query = ["Text1 1", "Text3 3"]
    results = afo_register_repository.search_by_texts_and_numbers(query)

    assert len(results) == 2
    assert record1 in results
    assert record3 in results


def test_search_by_texts_and_numbers_with_spaces(
    afo_register_repository: AfoRegisterRepository,
):
    record = AfoRegisterRecordFactory.build(text="Text With Space", text_number="4")
    afo_register_repository.create(record)

    results = afo_register_repository.search_by_texts_and_numbers(
        ["  Text With Space   4  "]
    )

    assert results == [record]


def test_create_indexes(database, afo_register_repository: AfoRegisterRepository):
    afo_register_repository.create_indexes()

    index_keys = [
        index["key"] for index in database["afo_register"].index_information().values()
    ]

    assert [("text", 1)] in index_keys
    assert [("textNumber", 1)] in index_keys
    assert [("text", 1), ("textNumber", 1)] in index_keys


def test_find_record_suggestions(afo_register_repository: AfoRegisterRepository):
    afo_register_record = AfoRegisterRecordFactory.build()
    another_afo_register_record = AfoRegisterRecordFactory.build(
        text=afo_register_record.text
    )
    afo_register_repository.create(afo_register_record)
    afo_register_repository.create(another_afo_register_record)
    text_numbers = natsorted(
        [
            afo_register_record.text_number,
            another_afo_register_record.text_number,
        ]
    )
    afo_register_record_suggestion = AfoRegisterRecordSuggestionFactory.build(
        text=afo_register_record.text, text_numbers=text_numbers
    )

    assert afo_register_repository.search_suggestions(
        afo_register_record.text[:-2],
    ) == [afo_register_record_suggestion]
