import factory
import random
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
from ebl.common.domain.provenance_data import build_provenance_records


PROVENANCE_VALUES = [
    f"{record.long_name} ({record.parent})" if record.parent else record.long_name
    for record in build_provenance_records()
]


class NameAttestationFactory(factory.Factory):
    class Meta:
        model = NameAttestation

    value = factory.Faker("word")
    is_broken = factory.Faker("boolean")
    is_uncertain = factory.Faker("boolean")


class ProvenanceAttestationFactory(factory.Factory):
    class Meta:
        model = ProvenanceAttestation

    value = factory.fuzzy.FuzzyChoice(PROVENANCE_VALUES)
    is_broken = factory.Faker("boolean")
    is_uncertain = factory.Faker("boolean")


class IndividualTypeFactory(factory.Factory):
    class Meta:
        model = IndividualTypeAttestation

    value = factory.fuzzy.FuzzyChoice(list(IndividualType))
    is_broken = factory.Faker("boolean")
    is_uncertain = factory.Faker("boolean")


class IndividualAttestationFactory(factory.Factory):
    class Meta:
        model = IndividualAttestation

    name = factory.SubFactory(NameAttestationFactory)
    son_of = factory.SubFactory(NameAttestationFactory)
    grandson_of = factory.SubFactory(NameAttestationFactory)
    family = factory.SubFactory(NameAttestationFactory)
    native_of = factory.SubFactory(ProvenanceAttestationFactory)
    type = factory.SubFactory(IndividualTypeFactory)


class ColophonFactory(factory.Factory):
    class Meta:
        model = Colophon

    colophon_status = factory.fuzzy.FuzzyChoice(list(ColophonStatus))
    colophon_ownership = factory.fuzzy.FuzzyChoice(list(ColophonOwnership))
    colophon_types = factory.List(
        [
            factory.fuzzy.FuzzyChoice(list(ColophonType))
            for _ in range(random.randint(1, 3))
        ]
    )
    original_from = factory.SubFactory(ProvenanceAttestationFactory)
    written_in = factory.SubFactory(ProvenanceAttestationFactory)
    notes_to_scribal_process = factory.Faker("sentence")
    individuals = factory.List(
        [
            factory.SubFactory(IndividualAttestationFactory)
            for _ in range(random.randint(0, 2))
        ]
    )
