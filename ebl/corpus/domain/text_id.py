import attr
import roman  # pyre-ignore[21]


@attr.s(auto_attribs=True, frozen=True)
class TextId:
    category: int
    index: int

    def __str__(self) -> str:
        return (
            f"{self.category}.{self.index}"
            if self.category < 1
            else f"{roman.toRoman(self.category)}.{self.index}"
        )
