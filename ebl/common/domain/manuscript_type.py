from ebl.common.domain.named_enum import NamedEnum


class ManuscriptType(NamedEnum):
    LIBRARY = ("Library", "")
    SCHOOL = ("School", "Sch")
    VARIA = ("Varia", "Var")
    COMMENTARY = ("Commentary", "Com")
    QUOTATION = ("Quotation", "Quo")
    EXCERPT = ("Excerpt", "Ex")
    PARALLEL = ("Parallel", "Par")
    NONE = ("None", "")
