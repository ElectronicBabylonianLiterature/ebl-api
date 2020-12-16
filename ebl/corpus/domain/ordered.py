from abc import ABC
from enum import auto, Enum, unique


@unique
class Order(Enum):
    PRE = auto()
    POST = auto()


class Ordered(ABC):
    def __init__(self, order: Order):
        self._order = order

    @property
    def is_post_order(self) -> bool:
        return self._order == Order.POST

    @property
    def is_pre_order(self) -> bool:
        return self._order == Order.PRE
