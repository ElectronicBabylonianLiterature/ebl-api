from ebl.common.domain.named_enum import NamedEnum


class ManuscriptType(NamedEnum):
    LIBRARY = ("Library", "")
    SCHOOL = ("School", "Sch")
    VARIA = ("Varia", "Var")
    AMULET = ("Amulet", "Amu")
    COMMENTARY = ("Commentary", "Com")
    QUOTATION = ("Quotation", "Quo")
    EXCERPT = ("Excerpt", "Ex")
    PARALLEL = ("Parallel", "Par")
    MULTICOLUMN = ("Multi-column tablet", "MultCol")
    COLLECTIVE = ("Collective tablet", "Coll")
    STUDENT_TEACHER = ("Student-teacher tablet", "StuTea")
    SCHOOL_LENTIL = ("School lentis", "SchLen")
    PRISM = ("Prisms", "Prism")
    UNCERTAIN = ("Uncertain", "Unc")
    NONE = ("None", "")
