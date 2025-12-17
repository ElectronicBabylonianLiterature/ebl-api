from typing import NewType
from enum import Enum

WordId = NewType("WordId", str)


class WordOrigin(Enum):
    EJ = "EJ"
    EJ_LOWER = "ej"
    CDA = "cda"
    CDA_ADDENDA = "cda/addenda"
    EBL = "ebl"
    ORACC_SAAO = "oracc/saao"
    ORACC_GKAB = "oracc/gkab"
    AFO_REGISTER = "afoRegister"
    SAD = "sad"
    CAIC = "caic"

# ToDo:
# 1. Migrate:
#    A. Database values to enum names:
#       "cda" → "CDA"
#       "cda/addenda" → "CDA_ADDENDA"
#       "ebl" → "EBL"
#       "oracc/saao" → "ORACC_SAAO"
#       "oracc/gkab" → "ORACC_GKAB"
#       "afoRegister" → "AFO_REGISTER"
#       "sad" → "SAD"
#       "caic" → "CAIC"
#    B. Consolidate to EBL:
#       "EJ", "ej", "caic" → "EBL"
# 2. Remove EJ, EJ_LOWER, CAIC from enum after migrating db values to "EBL".
# 3. Replace enum values with all caps once all origins are normalized.
