from typing import Mapping, Union

from ebl.transliteration.domain.sign import SignName, Value
from ebl.transliteration.domain.standardization import Standardization

SignKey = Union[Value, SignName]
SignMap = Mapping[SignKey, Standardization]
