from typing import Mapping, Union

from ebl.transliteration_search.domain.sign import SignName, Value
from ebl.transliteration_search.domain.standardization import Standardization

SignKey = Union[Value, SignName]
SignMap = Mapping[SignKey, Standardization]
