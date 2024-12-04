"""
import pytest
from ebl.afo_register.domain.afo_register_record import (
    AfoRegisterRecord,
    AfoRegisterRecordSuggestion,
)
from ebl.afo_register.infrastructure.mongo_afo_register_repository import (
    AfoRegisterRecordSchema,
    AfoRegisterRecordSuggestionSchema,
)
from ebl.tests.factories.afo_register import (
    AfoRegisterRecordFactory,
    AfoRegisterRecordSuggestionFactory,
)


@pytest.fixture
def afo_register_record():
    return AfoRegisterRecordFactory.build()


@pytest.fixture
def afo_register_record_suggestion():
    return AfoRegisterRecordSuggestionFactory.build()


def test_afo_register_record_creation(afo_register_record: AfoRegisterRecord) -> None:
    assert afo_register_record.afo_number is not None
    assert afo_register_record.page is not None
    assert afo_register_record.text is not None
    assert afo_register_record.text_number is not None
    assert afo_register_record.lines_discussed is not None
    assert afo_register_record.discussed_by is not None
    assert afo_register_record.discussed_by_notes is not None


def test_afo_register_record_defaults() -> None:
    afo_register_record = AfoRegisterRecord()

    assert afo_register_record.page == ""
    assert afo_register_record.text == ""
    assert afo_register_record.text_number == ""
    assert afo_register_record.lines_discussed == ""
    assert afo_register_record.discussed_by == ""
    assert afo_register_record.discussed_by_notes == ""


def test_afo_register_record_to_dict(afo_register_record: AfoRegisterRecord) -> None:
    assert AfoRegisterRecordSchema().dump(afo_register_record) == {
        "afoNumber": afo_register_record.afo_number,
        "page": afo_register_record.page,
        "text": afo_register_record.text,
        "textNumber": afo_register_record.text_number,
        "linesDiscussed": afo_register_record.lines_discussed,
        "discussedBy": afo_register_record.discussed_by,
        "discussedByNotes": afo_register_record.discussed_by_notes,
    }


def test_afo_register_record_suggestion_to_dict(
    afo_register_record_suggestion: AfoRegisterRecordSuggestion,
) -> None:
    assert AfoRegisterRecordSuggestionSchema().dump(afo_register_record_suggestion) == {
        "text": afo_register_record_suggestion.text,
        "textNumbers": afo_register_record_suggestion.text_numbers,
    }


def test_afo_register_record_from_dict(afo_register_record: AfoRegisterRecord) -> None:
    serialized_data = AfoRegisterRecordSchema().dump(afo_register_record)
    deserialized_object = AfoRegisterRecordSchema().load(serialized_data)

    assert deserialized_object.afo_number == afo_register_record.afo_number
    assert deserialized_object.page == afo_register_record.page
    assert deserialized_object.text == afo_register_record.text
    assert deserialized_object.text_number == afo_register_record.text_number
    assert deserialized_object.lines_discussed == afo_register_record.lines_discussed
    assert deserialized_object.discussed_by == afo_register_record.discussed_by
    assert (
        deserialized_object.discussed_by_notes == afo_register_record.discussed_by_notes
    )


def test_afo_register_record_suggestion_from_dict(
    afo_register_record_suggestion: AfoRegisterRecordSuggestion,
) -> None:
    serialized_data = AfoRegisterRecordSuggestionSchema().dump(
        afo_register_record_suggestion
    )
    deserialized_object = AfoRegisterRecordSuggestionSchema().load(serialized_data)

    assert deserialized_object.text == afo_register_record_suggestion.text
    assert (
        deserialized_object.text_numbers == afo_register_record_suggestion.text_numbers
    )
"""
