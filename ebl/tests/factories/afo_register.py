from factory.base import Factory
from factory.declarations import LazyAttribute, Sequence
from factory.faker import Faker
from ebl.tests.factories.factory_meta import FactoryMeta
from ebl.afo_register.domain.afo_register_record import (
    AfoRegisterRecord,
    AfoRegisterRecordSuggestion,
)
import faker
from natsort import natsorted

PUBLICATIONS = ["StOr", "Al.T.", "OECT", "VS", "STT", "CCT", "CM", "CST", "SAAB"]

fake = faker.Faker()


def get_afo_number() -> str:
    return f"AfO {fake.random_int(min=10, max=52)}"


def get_page() -> str:
    return str(fake.random_int(min=1, max=700))


def get_text() -> str:
    return f"{fake.random_element(elements=PUBLICATIONS)}, {fake.random_int(min=1, max=40)}"


def get_text_number() -> str:
    return f"Nr. {fake.random_int(min=1, max=300)}"


def get_text_numbers() -> list[str]:
    return [get_text_number() for _ in range(0, fake.random_int(min=1, max=15))]


def get_lines_discussed() -> str:
    return f"{fake.random_int(min=1, max=40)}f."


def get_discussed_by() -> str:
    return (
        f"{fake.last_name()}, "
        f"{fake.random_element(elements=PUBLICATIONS)}, "
        f"{fake.random_int(min=1, max=40)}, "
        f"{fake.random_int(min=1, max=50)}"
    )


class AfoRegisterRecordFactory(Factory):
    class Meta(FactoryMeta):
        model = AfoRegisterRecord

    afo_number = LazyAttribute(lambda obj: get_afo_number())
    page = LazyAttribute(lambda obj: get_page())
    text = LazyAttribute(lambda obj: get_text())
    text_number = Sequence(lambda n: f"Nr. {n}")
    lines_discussed = LazyAttribute(lambda obj: get_lines_discussed())
    discussed_by = LazyAttribute(lambda obj: get_discussed_by())
    discussed_by_notes = Faker("sentence")


class AfoRegisterRecordSuggestionFactory(Factory):
    class Meta(FactoryMeta):
        model = AfoRegisterRecordSuggestion

    text = LazyAttribute(lambda obj: get_text())
    text_numbers = LazyAttribute(lambda obj: natsorted(get_text_numbers()))
