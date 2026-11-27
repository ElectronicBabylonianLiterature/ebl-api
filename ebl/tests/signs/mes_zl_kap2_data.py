from ebl.signs.domain.mes_zl_kap2 import MesZlKap2Entry

FIRST = MesZlKap2Entry("579", "579\tFirst entry.")
SECOND = MesZlKap2Entry("580", "580\tSecond entry.")
PRIMED = MesZlKap2Entry("214′", "214′\tPrimed entry.")
SHARED = MesZlKap2Entry("115", "115\tShared entry.")

ALIASES = {SHARED.number: ["115a", "115b"]}

DOCUMENTS = [
    {"_id": entry.number, "text": entry.text, "aliases": ALIASES.get(entry.number, [])}
    for entry in (FIRST, SECOND, PRIMED, SHARED)
]
