import attr
import roman
from ebl.transliteration.domain.genre import Genre


@attr.s(auto_attribs=True, frozen=True)
class TextId:
    genre: Genre
    category: int
    index: int

    def __str__(self) -> str:
        return (
            f"{self.genre.value} {self.category}.{self.index}"
            if self.category < 1
            else f"{self.genre.value} {roman.toRoman(self.category)}.{self.index}"
        )
