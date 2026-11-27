from factory.base import Factory
from factory.declarations import (
    Dict,
    Iterator,
    List,
    SelfAttribute,
    Sequence,
    SubFactory,
    Trait,
)
from factory.faker import Faker
from factory.fuzzy import FuzzyChoice, FuzzyInteger
from ebl.tests.factories.factory_meta import FactoryMeta
import pydash
from ebl.common.domain.period import Period, PeriodModifier
from ebl.common.domain.project import ResearchProject

from ebl.corpus.domain.chapter import Chapter, Classification
from ebl.corpus.domain.manuscript import (
    Manuscript,
    OldSiglum,
)
from ebl.common.domain.manuscript_type import ManuscriptType
from ebl.tests.factories.provenance import DEFAULT_NON_STANDARD_PROVENANCES
from ebl.corpus.domain.record import Author, AuthorRole, Record, Translator
from ebl.corpus.domain.text import ChapterListing, Text
from ebl.fragmentarium.domain.joins import Joins
from ebl.tests.factories.bibliography import ReferenceFactory
from ebl.tests.factories.collections import TUPLE_FACTORY
from ebl.tests.factories.fragment import JoinFactory
from ebl.tests.factories.corpus_lines import LineFactory
from ebl.tests.factories.ids import TextIdFactory
from ebl.transliteration.domain.genre import Genre
from ebl.transliteration.domain.line_number import LineNumber
from ebl.transliteration.domain.markup import StringPart
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.transliteration.domain.sign_tokens import Reading
from ebl.common.domain.stage import Stage
from ebl.transliteration.domain.text import Text as Transliteration
from ebl.transliteration.domain.text_line import TextLine
from ebl.transliteration.domain.translation_line import TranslationLine
from ebl.transliteration.domain.word_tokens import Word
from ebl.corpus.domain.chapter_query import ChapterQueryColophonLines
from ebl.corpus.domain.manuscript_attestation import ManuscriptAttestation
from ebl.corpus.domain.uncertain_fragment_attestation import (
    UncertainFragmentAttestation,
)


class OldSiglumFactory(Factory):
    class Meta(FactoryMeta):
        model = OldSiglum

    siglum = Faker("word")
    reference = SubFactory(ReferenceFactory, with_document=True)


class JoinsFactory(Factory):
    class Meta(FactoryMeta):
        model = Joins

    fragments = List([List([SubFactory(JoinFactory)])])


class ManuscriptFactory(Factory):
    class Meta(FactoryMeta):
        model = Manuscript

    class Params:
        with_joins = Trait(joins=SubFactory(JoinsFactory))
        with_old_sigla = Trait(
            old_sigla=List([SubFactory(OldSiglumFactory)], TUPLE_FACTORY)
        )

    id = Sequence(lambda n: n + 1)
    siglum_disambiguator = Faker("word")
    museum_number = Sequence(
        lambda n: MuseumNumber("M", str(n)) if pydash.is_odd(n) else None
    )
    accession = Sequence(lambda n: f"A.{n}" if pydash.is_even(n) else "")
    period_modifier = FuzzyChoice(PeriodModifier)
    period = FuzzyChoice(set(Period) - {Period.NONE})
    provenance = FuzzyChoice(DEFAULT_NON_STANDARD_PROVENANCES)
    type = FuzzyChoice(set(ManuscriptType) - {ManuscriptType.NONE})
    notes = Faker("sentence")
    colophon = Transliteration.of_iterable(
        [TextLine.of_iterable(LineNumber(1, True), (Word.of([Reading.of_name("ku")]),))]
    )
    unplaced_lines = Transliteration.of_iterable(
        [TextLine.of_iterable(LineNumber(1, True), (Word.of([Reading.of_name("nu")]),))]
    )
    references = List([SubFactory(ReferenceFactory, with_document=True)], TUPLE_FACTORY)


class AuthorFactory(Factory):
    class Meta(FactoryMeta):
        model = Author

    name = Faker("word")
    prefix = Faker("word")
    role = FuzzyChoice(AuthorRole)
    orcid_number = ""


class TranslatorFactory(Factory):
    class Meta(FactoryMeta):
        model = Translator

    name = Faker("word")
    prefix = Faker("word")
    orcid_number = ""
    language = FuzzyChoice(["en", "ar", "de"])


class RecordFactory(Factory):
    class Meta(FactoryMeta):
        model = Record

    authors = List([SubFactory(AuthorFactory)], TUPLE_FACTORY)
    translators = List([SubFactory(TranslatorFactory)], TUPLE_FACTORY)
    publication_date = "2020-05-11T07:46:47.743916"


class ChapterQueryColophonLinesFactory(Factory):
    class Meta(FactoryMeta):
        model = ChapterQueryColophonLines

    colophon_lines_in_query = Dict({})


class ChapterFactory(Factory):
    class Meta(FactoryMeta):
        model = Chapter

    text_id = SubFactory(TextIdFactory)
    classification = FuzzyChoice(Classification)
    stage = FuzzyChoice(Stage)
    version = Faker("word")
    name = Faker("sentence")
    order = Faker("pyint")
    manuscripts = List([SubFactory(ManuscriptFactory, id=1)], TUPLE_FACTORY)
    lines = List([SubFactory(LineFactory, manuscript_id=1)], TUPLE_FACTORY)
    signs = ("KU ABZ075 ABZ207a\\u002F207b\\u0020X\nKU\nABZ075",)
    record = SubFactory(RecordFactory)
    parser_version = ""
    is_filtered_query = False
    colophon_lines_in_query = SubFactory(ChapterQueryColophonLinesFactory)


class ChapterListingFactory(Factory):
    class Meta(FactoryMeta):
        model = ChapterListing

    stage = FuzzyChoice(Stage)
    name = Faker("sentence")
    translation = (TranslationLine((StringPart("foo"),), "en", None),)
    uncertain_fragments = ()


class TextFactory(Factory):
    class Meta(FactoryMeta):
        model = Text

    genre = FuzzyChoice(Genre)
    category = Sequence(lambda n: n % 5000)
    index = Sequence(lambda n: n)
    name = Faker("sentence")
    has_doi = Iterator([True, False])
    number_of_verses = FuzzyInteger(1, 10000)
    approximate_verses = Iterator([True, False])
    intro = Faker("sentence")
    chapters = List([SubFactory(ChapterListingFactory)], TUPLE_FACTORY)
    references = List([SubFactory(ReferenceFactory, with_document=True)], TUPLE_FACTORY)
    projects = (ResearchProject.CAIC,)


class ManuscriptAttestationFactory(Factory):
    class Meta(FactoryMeta):
        model = ManuscriptAttestation

    class Params:
        chapter = SubFactory(ChapterFactory)

    text = SubFactory(TextFactory)
    chapter_id = SelfAttribute("chapter.id_")
    manuscript = SubFactory(ManuscriptFactory)


class UncertainFragmentAttestationFactory(Factory):
    class Meta(FactoryMeta):
        model = UncertainFragmentAttestation

    class Params:
        chapter = SubFactory(ChapterFactory)

    text = SubFactory(TextFactory)
    chapter_id = SelfAttribute("chapter.id_")
