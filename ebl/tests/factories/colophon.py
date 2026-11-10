import random
from factory.declarations import List, SubFactory
from factory.faker import Faker
from factory.fuzzy import FuzzyChoice
from factory.helpers import make_factory
from ebl.fragmentarium.domain.colophon import (
    ColophonStatus,
    ColophonType,
    NameAttestation,
    ProvenanceAttestation,
    IndividualAttestation,
    Colophon,
    IndividualType,
    ColophonOwnership,
    IndividualTypeAttestation,
)
from ebl.tests.factories.provenance import build_provenance_records


PROVENANCE_VALUES = [
    f"{record.long_name} ({record.parent})" if record.parent else record.long_name
    for record in build_provenance_records()
]


NameAttestationFactory = make_factory(
    NameAttestation,
    value=Faker("word"),
    is_broken=Faker("boolean"),
    is_uncertain=Faker("boolean"),
)

ProvenanceAttestationFactory = make_factory(
    ProvenanceAttestation,
    value=FuzzyChoice(PROVENANCE_VALUES),
    is_broken=Faker("boolean"),
    is_uncertain=Faker("boolean"),
)

IndividualTypeFactory = make_factory(
    IndividualTypeAttestation,
    value=FuzzyChoice(list(IndividualType)),
    is_broken=Faker("boolean"),
    is_uncertain=Faker("boolean"),
)
IndividualTypeFactory.__name__ = "IndividualTypeFactory"

IndividualAttestationFactory = make_factory(
    IndividualAttestation,
    name=SubFactory(NameAttestationFactory),
    son_of=SubFactory(NameAttestationFactory),
    grandson_of=SubFactory(NameAttestationFactory),
    family=SubFactory(NameAttestationFactory),
    native_of=SubFactory(ProvenanceAttestationFactory),
    type=SubFactory(IndividualTypeFactory),
)

ColophonFactory = make_factory(
    Colophon,
    colophon_status=FuzzyChoice(list(ColophonStatus)),
    colophon_ownership=FuzzyChoice(list(ColophonOwnership)),
    colophon_types=List(
        [FuzzyChoice(list(ColophonType)) for _ in range(random.randint(1, 3))]
    ),
    original_from=SubFactory(ProvenanceAttestationFactory),
    written_in=SubFactory(ProvenanceAttestationFactory),
    notes_to_scribal_process=Faker("sentence"),
    individuals=List(
        [SubFactory(IndividualAttestationFactory) for _ in range(random.randint(0, 2))]
    ),
)
