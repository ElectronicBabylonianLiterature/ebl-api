from typing import NewType
from enum import Enum

WordId = NewType("WordId", str)


class WordOrigin(Enum):
    CDA = "CDA"
    CDA_ADDENDA = "CDA_ADDENDA"
    EBL = "EBL"
    ORACC_SAAO = "ORACC_SAAO"
    ORACC_GKAB = "ORACC_GKAB"
    AFO_REGISTER = "AFO_REGISTER"
    SAD = "SAD"
    CAIC = "CAIC"
