from typing import Sequence

import attr

from ebl.fragmentarium.domain.fragment_info import FragmentInfo


@attr.s(frozen=True, auto_attribs=True)
class FragmentInfosPagination:
    fragment_infos: Sequence[FragmentInfo]
    total_count: int
