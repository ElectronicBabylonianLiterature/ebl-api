import attr
from text.token import Token


@attr.s(frozen=True)
class Erasure(Token):
    def to_dict(self) -> dict:
        return {
            **super().to_dict(),
            'type': 'Erasure'
        }
