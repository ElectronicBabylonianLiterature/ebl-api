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
