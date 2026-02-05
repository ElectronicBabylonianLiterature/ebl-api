from ebl.common.query.query_schemas import (
    AfORegisterToFragmentQueryResultSchema,
)
from ebl.tests.factories.fragment import (
    FragmentFactory,
)
from ebl.tests.factories.afo_register import AfoRegisterRecordFactory


def test_query_fragmentarium_afo_register(fragment_repository):
    record = AfoRegisterRecordFactory.build()
    record_id = f"{record.text} {record.text_number}"
    fragment = FragmentFactory.build(traditional_references=[record_id])
    fragment_repository.create_many([fragment, FragmentFactory.build()])
    result = fragment_repository.query_by_traditional_references([record_id])
    assert result == AfORegisterToFragmentQueryResultSchema().load(
        {
            "items": [
                {
                    "traditionalReference": record_id,
                    "fragmentNumbers": [str(fragment.number)],
                }
            ]
        }
    )
