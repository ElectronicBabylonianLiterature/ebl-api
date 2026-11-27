"""Recodings of MesZL Kapitel II for Borger Akkadian v0.9.14.

v0.9.14 gives 14 more of Borger's drawings their own private-use code points
(U+1000CF–U+1000DC). The Kapitel II text marks some of them with placeholders
(``⟦098a⟧``) and writes others as ordinary signs; these rules put Borger's
glyph in their place. Each rule names the entries it applies to (or all) and
how often its passage is expected, so that a changed source is reported
rather than silently mis-recoded. The rules are idempotent: once a passage is
recoded it is no longer found.
"""

from typing import Mapping, Optional, Sequence

import attr


@attr.s(auto_attribs=True, frozen=True)
class Kap2Recoding:
    mes_zl: str
    old: str
    new: str
    expected: int
    entries: Optional[Sequence[str]] = None


SA6 = "\U000122b7"
NA2 = "\U0001223f"

KAP2_RECODINGS: Sequence[Kap2Recoding] = (
    # New glyphs
    Kap2Recoding("98a", "⟦098a⟧", "\U001000cf", 3),
    Kap2Recoding("113a", "⟦113a⟧", "\U001000d0", 1),
    Kap2Recoding("113b", "⟦113b⟧", "\U001000d0", 2),
    Kap2Recoding("561a", "⟦561a⟧", "\U001000d1", 2),
    Kap2Recoding("571a", f"{SA6}{NA2}", f"\U001000d2{NA2}", 3),
    Kap2Recoding("150v2", "150\t𒄽, auch 𒄽 u.ä.", "150\t𒄽, auch \U001000d3 u.ä.", 1),
    # Borger's drawing of amaš is the whole sign, DÀG/DAG included.
    Kap2Recoding("688a", "𒎎⟦688a⟧", "\U001000d4", 1),
    Kap2Recoding("688a", "𒁖⟦688a⟧", "\U001000d4", 1),
    Kap2Recoding(
        "Deimel 63b",
        "Deimel n63b aufgeführte Zeichen 𒋺",
        "Deimel n63b aufgeführte Zeichen \U001000d5",
        1,
        ("106",),
    ),
    # Borger's one-glyph drawings of sign sequences
    Kap2Recoding("464d", "𒉺𒄸𒁺", "\U001000d7", 1, ("464",)),
    Kap2Recoding("464f", "𒉺𒁺", "\U001000d8", 1, ("464",)),
    Kap2Recoding("464g", "𒉺𒁼", "\U001000d9", 1, ("464",)),
    Kap2Recoding("464h", "𒉺𒁽", "\U001000da", 1, ("464",)),
    Kap2Recoding("464i", "𒉺𒀠", "\U001000db", 1, ("464",)),
    Kap2Recoding("721a", "𒇯𒊺𒊬", "\U001000dc", 1, ("721",)),
)


@attr.s(auto_attribs=True, frozen=True)
class Kap2RecodingReport:
    recoding: Kap2Recoding
    found: int

    @property
    def is_expected(self) -> bool:
        return self.found in (0, self.recoding.expected)


def recode_kap2(
    entries: Mapping[str, str],
    recodings: Sequence[Kap2Recoding] = KAP2_RECODINGS,
) -> tuple[dict[str, str], list[Kap2RecodingReport]]:
    """Recoded entries and, for each rule, how often its passage was found.

    A rule whose passage is found neither 0 times (already recoded or absent)
    nor the expected number of times is reported and not applied.
    """
    recoded = dict(entries)
    reports = []
    for recoding in recodings:
        keys = [
            key for key in recoded if not recoding.entries or key in recoding.entries
        ]
        found = sum(recoded[key].count(recoding.old) for key in keys)
        report = Kap2RecodingReport(recoding, found)
        if found and report.is_expected:
            for key in keys:
                recoded[key] = recoded[key].replace(recoding.old, recoding.new)
        reports.append(report)
    return recoded, reports
