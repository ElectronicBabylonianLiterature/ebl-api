from ebl.fragmentarium.domain.folios import Folio

NAME = "WGL"
NUMBER = "001"
FOLIO = Folio(NAME, NUMBER)


def test_name():
    assert FOLIO.name == NAME


def test_number():
    assert FOLIO.number == NUMBER


def test_file_name():
    assert FOLIO.file_name == f"{NAME}_{NUMBER}.jpg"
