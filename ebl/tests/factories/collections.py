from factory.base import BaseListFactory

from ebl.tests.factories.factory_meta import ListFactoryMeta


class TupleFactory(BaseListFactory):
    class Meta(ListFactoryMeta):
        model = tuple


TUPLE_FACTORY = f"{TupleFactory.__module__}.{TupleFactory.__qualname__}"
