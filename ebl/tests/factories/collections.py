# pylint: disable=R0903
import factory


class TupleFactory(factory.BaseListFactory):
    class Meta:
        model = tuple
