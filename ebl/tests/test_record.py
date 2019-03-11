import datetime
from freezegun import freeze_time
import pytest
from ebl.fragmentarium.record import (
    RecordType,
    RecordEntry,
    Record
)


@pytest.mark.parametrize("old,new,type_", [
    ('', 'new', RecordType.TRANSLITERATION),
    ('old', 'new', RecordType.REVISION),
])
@freeze_time("2018-09-07 15:41:24.032")
def test_add_record(old, new, type_, user):
    expected_entry = RecordEntry(
        user.ebl_name,
        type_,
        datetime.datetime.utcnow().isoformat()
    )
    assert Record().add_entry(old, new, user) == Record((expected_entry,))
