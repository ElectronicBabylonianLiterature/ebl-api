from typing import Tuple

import factory

from ebl.dictionary.domain.word import WordId
from ebl.fragmentarium.domain.folios import Folio, Folios
from ebl.fragmentarium.domain.fragment import Fragment, UncuratedReference
from ebl.tests.factories.record import RecordFactory
from ebl.transliteration.domain.atf import Flag
from ebl.transliteration.domain.line import TextLine
from ebl.transliteration.domain.text import Text
from ebl.transliteration.domain.token import BrokenAway, Word, \
    UnknownNumberOfSigns, Tabulation, CommentaryProtocol, Divider, Column


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


class TransliteratedFragmentFactory(FragmentFactory):
    text = Text((
        TextLine("1'.", (
            Column(),
            Tabulation('($___$)'),
            Word('[...-ku]-nu-ši'),
            BrokenAway('['),
            UnknownNumberOfSigns('...'),
            BrokenAway(']'),
            Column(2),
            Divider(':', ('@v',), (Flag.DAMAGE,)),
            CommentaryProtocol('!qt'),
        )),
        TextLine("2'.", (
            BrokenAway('['),
            UnknownNumberOfSigns('...'),
            BrokenAway(']'),
            Word('GI₆'),
            Word('ana'),
            Word('u₄-š[u'),
            UnknownNumberOfSigns('...'),
            BrokenAway(']'),
        )),
        TextLine("3'.", (
            BrokenAway('['),
            UnknownNumberOfSigns('...'),
            Word('k]i-du'),
            Word('u'),
            Word('ba-ma-t[i'),
            UnknownNumberOfSigns('...'),
            BrokenAway(']'),
        )),
        TextLine("6'.", (
            BrokenAway('['),
            UnknownNumberOfSigns('...'),
            BrokenAway(']'),
            Word('x'),
            Word('mu'),
            Word('ta-ma-tu₂')
        )),
        TextLine("7'.", (
            Word('šu/|BI×IS|'),
        ))
    ))
    signs = (
        'KU ABZ075 ABZ207a\\u002F207b\\u0020X ABZ377n1\n'
        'MI DIŠ UD ŠU\n'
        'KI DU ABZ411 BA MA TI\n'
        'X MU TA MA UD\n'
        'ŠU/|BI×IS|'
    )
    folios = Folios((
        Folio('WGL', '3'),
        Folio('XXX', '3')
    ))
    record = factory.SubFactory(RecordFactory)


class LemmatizedFragmentFactory(TransliteratedFragmentFactory):
    text = Text((
            TextLine("1'.", (
                Column(),
                Tabulation('($___$)'),
                Word('[...-ku]-nu-ši'),
                BrokenAway('['),
                UnknownNumberOfSigns('...'),
                BrokenAway(']'),
                Column(2),
                Divider(':', ('@v',), (Flag.DAMAGE,)),
                CommentaryProtocol('!qt'),
            )),
            TextLine("2'.", (
                BrokenAway('['),
                UnknownNumberOfSigns('...'),
                Word('GI₆', unique_lemma=(WordId('ginâ I'),)),
                Word('ana', unique_lemma=(WordId('ana I'),)),
                Word('u₄-š[u', unique_lemma=(WordId("ūsu I"),)),
                UnknownNumberOfSigns('...'),
                BrokenAway(']'),
            )),
            TextLine("3'.", (
                BrokenAway('['),
                UnknownNumberOfSigns('...'),
                Word('k]i-du', unique_lemma=(WordId('kīdu I'),)),
                Word('u', unique_lemma=(WordId('u I'),)),
                Word('ba-ma-t[i', unique_lemma=(WordId('bamātu I'),)),
                UnknownNumberOfSigns('...'),
                BrokenAway(']'),
            )),
            TextLine("6'.", (
                BrokenAway('['),
                UnknownNumberOfSigns('...'),
                BrokenAway(']'),
                Word('x'),
                Word('mu', unique_lemma=(WordId('mu I'),)),
                Word('ta-ma-tu₂', unique_lemma=(WordId('tamalāku I'),))
            )),
            TextLine("7'.", (
                Word('šu/|BI×IS|'),
            ))
        ))
