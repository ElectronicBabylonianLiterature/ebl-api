from ebl.tests.factories.afo_register import AfoRegisterRecordFactory
from ebl.afo_register.application.afo_register_repository import AfoRegisterRepository


def test_find_by_id(afo_register_repository: AfoRegisterRepository):
    afo_register_record = AfoRegisterRecordFactory.build()
    id = afo_register_repository.create(afo_register_record)
    afo_register_repository.create(AfoRegisterRecordFactory.build())

    assert afo_register_repository.find({"_id": id}) == afo_register_record


def test_find_by_afo_number_and_page(afo_register_repository: AfoRegisterRepository):
    afo_register_record = AfoRegisterRecordFactory.build()
    afo_register_repository.create(afo_register_record)
    afo_register_repository.create(AfoRegisterRecordFactory.build())

    assert (
        afo_register_repository.find(
            {
                "afoNumber": afo_register_record.afo_number,
                "page": afo_register_record.page,
            }
        )
        == afo_register_record
    )


def test_find_by_all_record_parameters(afo_register_repository: AfoRegisterRepository):
    afo_register_record = AfoRegisterRecordFactory.build()
    afo_register_repository.create(afo_register_record)
    afo_register_repository.create(AfoRegisterRecordFactory.build())

    assert (
        afo_register_repository.find(
            {
                "afoNumber": afo_register_record.afo_number,
                "page": afo_register_record.page,
                "text": afo_register_record.text,
                "textNumber": afo_register_record.text_number,
                "linesDiscussed": afo_register_record.lines_discussed,
                "discussedBy": afo_register_record.discussed_by,
                "discussedByNotes": afo_register_record.discussed_by_notes,
            }
        )
        == afo_register_record
    )
