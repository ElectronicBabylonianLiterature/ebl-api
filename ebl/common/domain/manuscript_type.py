from ebl.common.domain.named_enum import NamedEnum


class ManuscriptType(NamedEnum):
    LIBRARY = ("Library", "")
    SCHOOL = ("School", "Sch")
    VARIA = ("Varia", "Var")
    AMULET = ("Amulet", "Amu")
    COMMENTARY = ("Commentary", "Com")
    EXCERPT = ("Excerpt", "Ex")
    PARALLEL = ("Parallel", "Par")
    QUOTATION = ("Quotation", "Quo")
    NONE = ("None", "")
