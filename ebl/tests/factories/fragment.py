from typing import Tuple
import factory
import factory.fuzzy

from ebl.fragment.folios import Folios, Folio
from ebl.fragment.fragment import Fragment, UncuratedReference
from ebl.text.text import Text


class FragmentFactory(factory.Factory):
    class Meta:
        model = Fragment

    number = factory.Sequence(lambda n: f'X.{n}')
    cdli_number = factory.Sequence(lambda n: f'cdli-{n}')
    bm_id_number = factory.Sequence(lambda n: f'bmId-{n}')
    accession = factory.Sequence(lambda n: f'accession-{n}')
    museum = factory.Faker('word')
    collection = factory.Faker('word')
    publication = factory.Faker('sentence')
    description = factory.Faker('text')
    script = factory.Iterator(['NA', 'NB'])
    folios = Folios((
        Folio('WGL', '1'),
        Folio('XXX', '1')
    ))


class InterestingFragmentFactory(FragmentFactory):
        collection = 'Kuyunjik'
        publication = ''
        joins: Tuple[str, ...] = tuple()
        text = Text()
        uncurated_references = (
            UncuratedReference('7(0)'),
            UncuratedReference('CAD 51', (34, 56)),
            UncuratedReference('7(1)')
        )
