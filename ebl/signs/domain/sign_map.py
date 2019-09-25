from typing import Mapping, Union

from ebl.signs.domain.sign import SignName, Value
from ebl.signs.domain.standardization import Standardization

SignKey = Union[Value, SignName]
SignMap = Mapping[SignKey, Standardization]
