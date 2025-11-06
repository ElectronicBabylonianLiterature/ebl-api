from typing import Sequence
from ebl.transliteration.domain.labels import Label
from ebl.transliteration.domain.common_transformer import CommonTransformer


class LabelTransformer(CommonTransformer):
    def __init__(self):
        super().__init__()

    def labels(self, children) -> Sequence[Label]:
        return tuple(children)
