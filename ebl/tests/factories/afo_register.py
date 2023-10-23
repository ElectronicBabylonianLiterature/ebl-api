import factory
from ebl.afo_register.domain.afo_register_record import AfoRegisterRecord
from faker import Faker

PUBLICATIONS = ["StOr", "Al.T.", "OECT", "VS", "STT", "CCT", "CM", "CST", "SAAB"]

fake = Faker()


class AfoRegisterRecordFactory(factory.Factory):
    class Meta:
        model = AfoRegisterRecord

    afo_number = f"AfO {fake.random_int(min=10, max=52)}"
    page = str(fake.random_int(min=1, max=700))
    text = f"{fake.random_element(elements=PUBLICATIONS)}, {fake.random_int(min=1, max=40)}"
    text_number = f"Nr. {fake.random_int(min=1, max=300)}"
    lines_discussed = f"{fake.random_int(min=1, max=40)}f."
    discussed_by = (
        f"{fake.last_name()}, "
        f"{fake.random_element(elements=PUBLICATIONS)}, "
        f"{fake.random_int(min=1, max=40)}, "
        f"{fake.random_int(min=1, max=50)}"
    )
    discussed_by_notes = factory.Faker("sentence")
