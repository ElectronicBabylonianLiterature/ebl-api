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


def test_find_by_quoted_text_number_matches_exactly(
    afo_register_repository: AfoRegisterRepository,
):
    afo_register_record = AfoRegisterRecordFactory.build(text_number="Nr. 5")
    afo_register_repository.create(afo_register_record)
    afo_register_repository.create(AfoRegisterRecordFactory.build(text_number="Nr. 50"))

    assert afo_register_repository.search({"textNumber": '"Nr. 5"'}) == [
        afo_register_record
    ]


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


def test_search_by_texts_and_numbers_with_space_in_text_number(
    afo_register_repository: AfoRegisterRepository,
):
    record = AfoRegisterRecordFactory.build(text="OrNS", text_number="59, 17")
    afo_register_repository.create(record)

    assert afo_register_repository.search_by_texts_and_numbers(["OrNS 59, 17"]) == [
        record
    ]


def test_search_by_texts_and_numbers_with_spaces_in_both_fields(
    afo_register_repository: AfoRegisterRepository,
):
    record = AfoRegisterRecordFactory.build(text="*Bīt mēseri*", text_number="59, 17")
    afo_register_repository.create(record)

    assert afo_register_repository.search_by_texts_and_numbers(
        ["*Bīt mēseri* 59, 17"]
    ) == [record]


def test_search_by_texts_and_numbers_ignores_partial_matches(
    afo_register_repository: AfoRegisterRepository,
):
    afo_register_repository.create(
        AfoRegisterRecordFactory.build(text="A B", text_number="C")
    )

    assert afo_register_repository.search_by_texts_and_numbers(["A B C D"]) == []


def test_search_by_texts_and_numbers_batches_spaced_and_unspaced(
    afo_register_repository: AfoRegisterRepository,
):
    spaced_record = AfoRegisterRecordFactory.build(text="OrNS", text_number="59, 17")
    unspaced_record = AfoRegisterRecordFactory.build(
        text="AfO", text_number="17,257ff."
    )
    unmatched_record = AfoRegisterRecordFactory.build(text="OrNS", text_number="59, 26")
    afo_register_repository.create(spaced_record)
    afo_register_repository.create(unspaced_record)
    afo_register_repository.create(unmatched_record)

    results = afo_register_repository.search_by_texts_and_numbers(
        ["OrNS 59, 17", "AfO 17,257ff."]
    )

    assert len(results) == 2
    assert spaced_record in results
    assert unspaced_record in results


def test_search_by_texts_and_numbers_without_queries(
    afo_register_repository: AfoRegisterRepository,
):
    afo_register_repository.create(AfoRegisterRecordFactory.build())

    assert afo_register_repository.search_by_texts_and_numbers([]) == []


def test_search_by_texts_and_numbers_without_splittable_query(
    afo_register_repository: AfoRegisterRepository,
):
    afo_register_repository.create(
        AfoRegisterRecordFactory.build(text="OrNS", text_number="59, 17")
    )

    assert afo_register_repository.search_by_texts_and_numbers(["OrNS"]) == []


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
