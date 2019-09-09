from typing import Tuple

import attr

from ebl.fragment.fragment import Fragment, FragmentNumber

Lines = Tuple[Tuple[str, ...], ...]


@attr.s(frozen=True, auto_attribs=True)
class FragmentInfo:
    number: FragmentNumber
    accession: str
    script: str
    description: str
    matching_lines: Lines

    @staticmethod
    def of(fragment: Fragment,
           matching_lines: Lines = tuple()) -> 'FragmentInfo':
        return FragmentInfo(fragment.number,
                            fragment.accession,
                            fragment.script,
                            fragment.description,
                            matching_lines)
