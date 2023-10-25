import factory
from ebl.afo_register.domain.afo_register_record import AfoRegisterRecord
from faker import Faker

PUBLICATIONS = ["StOr", "Al.T.", "OECT", "VS", "STT", "CCT", "CM", "CST", "SAAB"]

fake = Faker()


def get_afo_number() -> str:
    return f"AfO {fake.random_int(min=10, max=52)}"


def get_page() -> str:
    return str(fake.random_int(min=1, max=700))


def get_text() -> str:
    return f"{fake.random_element(elements=PUBLICATIONS)}, {fake.random_int(min=1, max=40)}"


def get_text_number() -> str:
    return f"Nr. {fake.random_int(min=1, max=300)}"


def get_lines_discussed() -> str:
    return f"{fake.random_int(min=1, max=40)}f."


def get_discussed_by() -> str:
    return (
        f"{fake.last_name()}, "
        f"{fake.random_element(elements=PUBLICATIONS)}, "
        f"{fake.random_int(min=1, max=40)}, "
        f"{fake.random_int(min=1, max=50)}"
    )


class AfoRegisterRecordFactory(factory.Factory):
    class Meta:
        model = AfoRegisterRecord

    afo_number = factory.LazyAttribute(lambda obj: get_afo_number())
    page = factory.LazyAttribute(lambda obj: get_page())
    text = factory.LazyAttribute(lambda obj: get_text())
    text_number = factory.LazyAttribute(lambda obj: get_text_number())
    lines_discussed = factory.LazyAttribute(lambda obj: get_lines_discussed())
    discussed_by = factory.LazyAttribute(lambda obj: get_discussed_by())
    discussed_by_notes = factory.Faker("sentence")
