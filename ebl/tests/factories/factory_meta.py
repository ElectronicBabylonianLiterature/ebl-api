from typing import TYPE_CHECKING

from factory.base import BaseListFactory, Factory

if TYPE_CHECKING:
    FactoryMeta = Factory.Meta
    ListFactoryMeta = BaseListFactory.Meta
else:
    FactoryMeta = object
    ListFactoryMeta = object
