from ebl.fragmentarium.domain.fragment_metadata import Acquisition


def test_acquisition_of():
    assert Acquisition.of(
        {"description": "purchase", "supplier": "gallery", "date": 1925}
    ) == Acquisition(description="purchase", supplier="gallery", date=1925)


def test_acquisition_of_defaults():
    assert Acquisition.of({}) == Acquisition()
