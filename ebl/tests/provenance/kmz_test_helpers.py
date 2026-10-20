from pathlib import Path

from ebl.provenance.domain.provenance_model import ProvenanceRecord
from scripts.kmz.models import KmlPlacemark
from scripts.kmz.parser import parse_kml_bytes

POINT = {"latitude": 35.0, "longitude": 43.0}
POINT_XML = "<Point><coordinates>43,35,0</coordinates></Point>"
POLYGON_XML = (
    "<Polygon><outerBoundaryIs><LinearRing>"
    "<coordinates>43,35 44,35 44,36 43,35</coordinates>"
    "</LinearRing></outerBoundaryIs></Polygon>"
)


def record(name: str = "Assur", identifier: str = "ASSUR") -> ProvenanceRecord:
    return ProvenanceRecord(identifier, name, identifier)


def placemark(name: str = "Assur", geometry: str = POINT_XML) -> KmlPlacemark:
    return parse_kml_bytes(kml_bytes(name, geometry)).placemarks[0]


def kml_bytes(name: str = "Assur", geometry: str = POINT_XML) -> bytes:
    return (
        '<kml xmlns="http://www.opengis.net/kml/2.2"><Document><Placemark>'
        f"<name>{name}</name>{geometry}</Placemark></Document></kml>"
    ).encode()


def write_kml(path: Path) -> Path:
    path.write_bytes(kml_bytes(geometry=POINT_XML + POLYGON_XML))
    return path
