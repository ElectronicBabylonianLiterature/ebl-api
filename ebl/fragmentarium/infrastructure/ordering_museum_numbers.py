import operator
import re
from typing import Sequence, Tuple, Optional, Callable

import attr
import pydash

from ebl.errors import NotFoundError
from ebl.fragmentarium.application.museum_number_schema import MuseumNumberSchema
from ebl.fragmentarium.domain.museum_number import MuseumNumber

ORDER = [
    ("^k$", 0),
    ("^sm$", 1),
    ("^dt$", 2),
    ("^rm$", 3),
    (r"^rm\-ii$", 4),
    (r"^\d*$", 5),
    ("^bm$", 6),
    ("^cbs$", 7),
    ("^um$", 8),
    ("^n$", 9),
    (r"^[abcdefghijlmopqrstuvwxyz]$|^((?!^\d*$).)*$", 10),
]
ORDER_SIZE = len(ORDER)


@attr.attrs(auto_attribs=True, frozen=True)
class OrderingMuseumNumbers:
    museum_number: MuseumNumber
    prefix: str
    retrieve_all_museum_numbers_by_prefix: Callable[[str], Sequence[dict]]

    def get_order_element_by_prefix(self, prefix: str) -> Tuple[str, int]:
        for order_elem in ORDER:
            regex, order_number = order_elem
            if re.match(regex, prefix.lower()):
                return regex, order_number
        raise ValueError("Prefix doesn't match any of the expected Prefixes")

    def get_adjacent_prefix(self, prefix: str, counter: int) -> str:
        regex, order_number = self.get_order_element_by_prefix(prefix)
        return ORDER[(order_number + counter) % ORDER_SIZE][0]

    def _is_order_reverted(
        self, order_number: int, adjacent_order_number: int, prev_or_next: int
    ):
        return (
            adjacent_order_number < order_number
            if prev_or_next == 1
            else adjacent_order_number > order_number
        )

    def find_adjacent_museum_number_from_list(
        self, museum_number: MuseumNumber, cursor, revert_order=False
    ):
        comp = operator.lt if not revert_order else operator.gt
        current_prev = None
        current_next = None
        for current_cursor in cursor:
            current_museum_number = MuseumNumberSchema().load(
                current_cursor["museumNumber"]
            )
            if comp(current_museum_number, museum_number) and (
                not current_prev or current_museum_number > current_prev
            ):
                current_prev = current_museum_number
            if comp(museum_number, current_museum_number) and (
                not current_next or current_museum_number < current_next
            ):
                current_next = current_museum_number
        return current_prev, current_next

    def iterate_until_found(
        self,
        adjacent_museum_number: Optional[MuseumNumber],
        counter: int,
    ) -> MuseumNumber:
        _, order_number = self.get_order_element_by_prefix(self.prefix)
        for i in range(ORDER_SIZE):
            if not adjacent_museum_number:
                regex_query = self.get_adjacent_prefix(self.prefix, (i + 1) * counter)
                current_query_order = pydash.find_index(
                    ORDER, lambda x: x[0] == regex_query
                )
                is_reverted = self._is_order_reverted(
                    order_number, current_query_order, counter
                )

                museum_numbers_by_prefix = self.retrieve_all_museum_numbers_by_prefix(
                    regex_query
                )
                adjacent_museum_number = self.find_adjacent_museum_number_from_list(
                    self.museum_number, museum_numbers_by_prefix, is_reverted
                )[0 if counter == -1 else 1]
            else:
                return adjacent_museum_number
        raise NotFoundError("Could not retrieve any fragments")
