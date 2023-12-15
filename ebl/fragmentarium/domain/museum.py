import attr


@attr.s
class Museum:
    museumName: str = attr.ib()
    city: str = attr.ib()
    country: str = attr.ib()
    url: str = attr.ib()

    def __init__(self, museumName="", city="", country="", url=""):
        self.museumName = museumName
        self.city = city
        self.country = country
        self.url = url
