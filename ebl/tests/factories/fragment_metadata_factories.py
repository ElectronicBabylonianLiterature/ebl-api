import pydash
import factory.fuzzy
import random
from ebl.common.domain.period import Period, PeriodModifier
from ebl.tests.factories.collections import TupleFactory
from ebl.fragmentarium.domain.fragment import (
    Acquisition,
    DossierReference,
    Script,
)

from ebl.fragmentarium.domain.fragment_external_numbers import ExternalNumbers
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.fragmentarium.domain.joins import Join
from ebl.fragmentarium.domain.date import (
    Date,
    Year,
    Month,
    Day,
    DateKing,
    DateKingSchema,
    Ur3Calendar,
)
from ebl.chronology.chronology import chronology, King


class JoinFactory(factory.Factory):
    class Meta:
        model = Join

    museum_number = factory.Sequence(
        lambda n: MuseumNumber("M", str(n)) if pydash.is_odd(n) else None
    )
    is_checked = factory.Faker("boolean")
    is_envelope = factory.Faker("boolean")
    joined_by = factory.Faker("word")
    date = factory.Faker("date")
    note = factory.Faker("sentence")
    legacy_data = factory.Faker("sentence")
    is_in_fragmentarium = factory.Faker("boolean")


class ScriptFactory(factory.Factory):
    class Meta:
        model = Script

    period = factory.fuzzy.FuzzyChoice(set(Period) - {Period.NONE})
    period_modifier = factory.fuzzy.FuzzyChoice(set(PeriodModifier))
    uncertain = factory.Faker("boolean")


class YearFactory(factory.Factory):
    class Meta:
        model = Year

    value = factory.Faker("word")
    is_broken = factory.Faker("boolean")
    is_uncertain = factory.Faker("boolean")
    is_reconstructed = factory.Faker("boolean")
    is_emended = factory.Faker("boolean")


class MonthFactory(factory.Factory):
    class Meta:
        model = Month

    value = factory.Faker("word")
    is_broken = factory.Faker("boolean")
    is_uncertain = factory.Faker("boolean")
    is_intercalary = factory.Faker("boolean")


class DayFactory(factory.Factory):
    class Meta:
        model = Day

    value = factory.Faker("word")
    is_broken = factory.Faker("boolean")
    is_uncertain = factory.Faker("boolean")


def create_date_king(king: King) -> DateKing:
    return DateKingSchema().load(
        {
            "orderGlobal": king.order_global,
            "isBroken": random.choice([True, False]),
            "isUncertain": random.choice([True, False]),
        }
    )


class DateFactory(factory.Factory):
    class Meta:
        model = Date

    year = factory.SubFactory(YearFactory)
    month = factory.SubFactory(MonthFactory)
    day = factory.SubFactory(DayFactory)
    king = factory.Iterator(chronology.kings, getter=create_date_king)
    is_seleucid_era = factory.Faker("boolean")
    ur3_calendar = factory.Iterator(Ur3Calendar)


class ExternalNumbersFactory(factory.Factory):
    class Meta:
        model = ExternalNumbers

    cdli_number = factory.Sequence(lambda n: f"cdli-{n}")
    bm_id_number = factory.Sequence(lambda n: f"bmId-{n}")
    archibab_number = factory.Sequence(lambda n: f"archibab-{n}")
    bdtns_number = factory.Sequence(lambda n: f"bdtns-{n}")
    rsti_number = factory.Sequence(lambda n: f"rsti-{n}")
    chicago_isac_number = factory.Sequence(lambda n: f"chicago-isac-number-{n}")
    ur_online_number = factory.Sequence(lambda n: f"ur-online-{n}")
    hilprecht_jena_number = factory.Sequence(lambda n: f"hilprecht-jena-{n}")
    hilprecht_heidelberg_number = factory.Sequence(
        lambda n: f"hilprecht-heidelberg-{n}"
    )
    metropolitan_number = factory.Sequence(lambda n: f"metropolitan-number-{n}")
    pierpont_morgan_number = factory.Sequence(lambda n: f"pierpont-morgan-number-{n}")
    louvre_number = factory.Sequence(lambda n: f"louvre-number-{n}")
    ontario_number = factory.Sequence(lambda n: f"ontario-number-{n}")
    kelsey_number = factory.Sequence(lambda n: f"kelsey-number-{n}")
    harvard_ham_number = factory.Sequence(lambda n: f"harvard-ham-number-{n}")
    etcsri_number = factory.Sequence(lambda n: f"etcsri-number-{n}")
    sketchfab_number = factory.Sequence(lambda n: f"sketchfab-number-{n}")
    ark_number = factory.Sequence(lambda n: f"ark-number-{n}")
    dublin_tcd_number = factory.Sequence(lambda n: f"dublin-tcd-number-{n}")
    cambridge_maa_number = factory.Sequence(lambda n: f"cambridge-maa-number-{n}")
    ashmolean_number = factory.Sequence(lambda n: f"ashmolean-number-{n}")
    alalah_hpm_number = factory.Sequence(lambda n: f"alalah-hpm-number-{n}")
    australianinstituteofarchaeology_number = factory.Sequence(
        lambda n: f"australianinstituteofarchaeology-number-{n}"
    )
    philadelphia_number = factory.Sequence(lambda n: f"philadelphia-number-{n}")
    yale_peabody_number = factory.Sequence(lambda n: f"yale-peabody-number-{n}")
    achemenet_number = factory.Sequence(lambda n: f"achemenet-number-{n}")
    nabucco_number = factory.Sequence(lambda n: f"nabucco-number-{n}")
    digitale_keilschrift_bibliothek_number = factory.Sequence(
        lambda n: f"digitale-keilschrift-bibliothek-{n}"
    )
    oracc_numbers = factory.List(
        [factory.Sequence(lambda n: f"oracc-number-{n}")], TupleFactory
    )
    seal_numbers = factory.List(
        [factory.Sequence(lambda n: f"seal_number-{n}")], TupleFactory
    )


class FragmentDossierReferenceFactory(factory.Factory):
    class Meta:
        model = DossierReference

    dossierId = factory.Faker("word")
    isUncertain = factory.Faker("boolean")


class AcquisitionFactory(factory.Factory):
    class Meta:
        model = Acquisition

    description = factory.Faker("sentence")
    supplier = factory.Faker("word")
    date = 0
