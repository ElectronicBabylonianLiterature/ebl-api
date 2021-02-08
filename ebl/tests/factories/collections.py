import factory  # pyre-ignore


class TupleFactory(factory.BaseListFactory):  # pyre-ignore[11]
    class Meta:
        model = tuple
