import attr
import pydash

from ebl.fragment.fragment import Fragment, FragmentNumber, Lines
from ebl.fragment.record import RecordEntry, RecordType


@attr.s(frozen=True, auto_attribs=True)
class FragmentInfo:
    number: FragmentNumber
    accession: str
    script: str
    description: str
    matching_lines: Lines
    editor: str
    edition_date: str

    @staticmethod
    def of(fragment: Fragment,
           matching_lines: Lines = tuple()) -> 'FragmentInfo':
        def is_transliteration(entry: RecordEntry) -> bool:
            return entry.type == RecordType.TRANSLITERATION

        first_transliteration = (
            pydash
            .chain(fragment.record.entries)
            .filter(is_transliteration)
            .sort_by('date')
            .head()
            .value()
        ) or RecordEntry('', RecordType.TRANSLITERATION, '')

        return FragmentInfo(fragment.number,
                            fragment.accession,
                            fragment.script,
                            fragment.description,
                            matching_lines,
                            first_transliteration.user,
                            first_transliteration.date)
