import random
from typing import cast

import pydash
import factory.fuzzy
from factory.declarations import Iterator, List, Sequence, SubFactory
from factory.faker import Faker
from factory.helpers import make_factory

from ebl.common.domain.period import Period, PeriodModifier
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

TUPLE_FACTORY = "ebl.tests.factories.collections.TupleFactory"


JoinFactory = make_factory(
    Join,
    museum_number=Sequence(
        lambda n: MuseumNumber("M", str(n)) if pydash.is_odd(n) else None
    ),
    is_checked=Faker("boolean"),
    is_envelope=Faker("boolean"),
    joined_by=Faker("word"),
    date=Faker("date"),
    note=Faker("sentence"),
    legacy_data=Faker("sentence"),
    is_in_fragmentarium=Faker("boolean"),
)

ScriptFactory = make_factory(
    Script,
    period=factory.fuzzy.FuzzyChoice(set(Period) - {Period.NONE}),
    period_modifier=factory.fuzzy.FuzzyChoice(set(PeriodModifier)),
    uncertain=Faker("boolean"),
)

YearFactory = make_factory(
    Year,
    value=Faker("word"),
    is_broken=Faker("boolean"),
    is_uncertain=Faker("boolean"),
    is_reconstructed=Faker("boolean"),
    is_emended=Faker("boolean"),
)

MonthFactory = make_factory(
    Month,
    value=Faker("word"),
    is_broken=Faker("boolean"),
    is_uncertain=Faker("boolean"),
    is_intercalary=Faker("boolean"),
)

DayFactory = make_factory(
    Day,
    value=Faker("word"),
    is_broken=Faker("boolean"),
    is_uncertain=Faker("boolean"),
)


def create_date_king(king: King) -> DateKing:
    return cast(
        DateKing,
        DateKingSchema().load(
            {
                "orderGlobal": king.order_global,
                "isBroken": random.choice([True, False]),
                "isUncertain": random.choice([True, False]),
            }
        ),
    )


DateFactory = make_factory(
    Date,
    year=SubFactory(YearFactory),
    month=SubFactory(MonthFactory),
    day=SubFactory(DayFactory),
    king=Iterator(chronology.kings, getter=create_date_king),
    is_seleucid_era=Faker("boolean"),
    ur3_calendar=Iterator(Ur3Calendar),
)

ExternalNumbersFactory = make_factory(
    ExternalNumbers,
    cdli_number=Sequence(lambda n: f"cdli-{n}"),
    bm_id_number=Sequence(lambda n: f"bmId-{n}"),
    archibab_number=Sequence(lambda n: f"archibab-{n}"),
    bdtns_number=Sequence(lambda n: f"bdtns-{n}"),
    rsti_number=Sequence(lambda n: f"rsti-{n}"),
    chicago_isac_number=Sequence(lambda n: f"chicago-isac-number-{n}"),
    ur_online_number=Sequence(lambda n: f"ur-online-{n}"),
    hilprecht_jena_number=Sequence(lambda n: f"hilprecht-jena-{n}"),
    hilprecht_heidelberg_number=Sequence(lambda n: f"hilprecht-heidelberg-{n}"),
    metropolitan_number=Sequence(lambda n: f"metropolitan-number-{n}"),
    pierpont_morgan_number=Sequence(lambda n: f"pierpont-morgan-number-{n}"),
    louvre_number=Sequence(lambda n: f"louvre-number-{n}"),
    ontario_number=Sequence(lambda n: f"ontario-number-{n}"),
    kelsey_number=Sequence(lambda n: f"kelsey-number-{n}"),
    harvard_ham_number=Sequence(lambda n: f"harvard-ham-number-{n}"),
    etcsri_number=Sequence(lambda n: f"etcsri-number-{n}"),
    sketchfab_number=Sequence(lambda n: f"sketchfab-number-{n}"),
    ark_number=Sequence(lambda n: f"ark-number-{n}"),
    dublin_tcd_number=Sequence(lambda n: f"dublin-tcd-number-{n}"),
    cambridge_maa_number=Sequence(lambda n: f"cambridge-maa-number-{n}"),
    ashmolean_number=Sequence(lambda n: f"ashmolean-number-{n}"),
    alalah_hpm_number=Sequence(lambda n: f"alalah-hpm-number-{n}"),
    australianinstituteofarchaeology_number=Sequence(
        lambda n: f"australianinstituteofarchaeology-number-{n}"
    ),
    philadelphia_number=Sequence(lambda n: f"philadelphia-number-{n}"),
    yale_peabody_number=Sequence(lambda n: f"yale-peabody-number-{n}"),
    achemenet_number=Sequence(lambda n: f"achemenet-number-{n}"),
    nabucco_number=Sequence(lambda n: f"nabucco-number-{n}"),
    digitale_keilschrift_bibliothek_number=Sequence(
        lambda n: f"digitale-keilschrift-bibliothek-{n}"
    ),
    oracc_numbers=List([Sequence(lambda n: f"oracc-number-{n}")], TUPLE_FACTORY),
    seal_numbers=List([Sequence(lambda n: f"seal_number-{n}")], TUPLE_FACTORY),
)

FragmentDossierReferenceFactory = make_factory(
    DossierReference,
    dossierId=Faker("word"),
    isUncertain=Faker("boolean"),
)

AcquisitionFactory = make_factory(
    Acquisition,
    description=Faker("sentence"),
    supplier=Faker("word"),
    date=0,
)
