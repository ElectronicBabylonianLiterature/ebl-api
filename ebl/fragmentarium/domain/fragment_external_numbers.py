import attr
from typing import Sequence


@attr.s(auto_attribs=True, frozen=True)
class ExternalNumbers:
    cdli_number: str = ""
    bm_id_number: str = ""
    archibab_number: str = ""
    bdtns_number: str = ""
    rsti_number: str = ""
    chicago_isac_number: str = ""
    ur_online_number: str = ""
    hilprecht_jena_number: str = ""
    hilprecht_heidelberg_number: str = ""
    metropolitan_number: str = ""
    pierpont_morgan_number: str = ""
    louvre_number: str = ""
    dublin_tcd_number: str = ""
    cambridge_maa_number: str = ""
    ashmolean_number: str = ""
    alalah_hpm_number: str = ""
    australianinstituteofarchaeology_number: str = ""
    philadelphia_number: str = ""
    achemenet_number: str = ""
    nabucco_number: str = ""
    digitale_keilschrift_bibliothek_number: str = ""
    yale_peabody_number: str = ""
    oracc_numbers: Sequence[str] = ()
    seal_numbers: Sequence[str] = ()


class FragmentExternalNumbers:
    external_numbers: ExternalNumbers = ExternalNumbers()

    def _get_external_number(self, number_type: str) -> str:
        return getattr(self.external_numbers, f"{number_type}_number")

    @property
    def cdli_number(self) -> str:
        return self._get_external_number("cdli")

    @property
    def bm_id_number(self) -> str:
        return self._get_external_number("bm_id")

    @property
    def archibab_number(self) -> str:
        return self._get_external_number("archibab")

    @property
    def bdtns_number(self) -> str:
        return self._get_external_number("bdtns")

    @property
    def rsti_number(self) -> str:
        return self._get_external_number("rsti")

    @property
    def chicago_isac_number(self) -> str:
        return self._get_external_number("chicago_isac")

    @property
    def ur_online_number(self) -> str:
        return self._get_external_number("ur_online")

    @property
    def hilprecht_jena_number(self) -> str:
        return self._get_external_number("hilprecht_jena")

    @property
    def hilprecht_heidelberg_number(self) -> str:
        return self._get_external_number("hilprecht_heidelberg")

    @property
    def yale_peabody_number(self) -> str:
        return self._get_external_number("yale_peabody")

    @property
    def metropolitan_number(self) -> str:
        return self._get_external_number("metropolitan_number")

    @property
    def pierpont_morgan_number(self) -> str:
        return self._get_external_number("pierpont_morgan_number")

    @property
    def louvre_number(self) -> str:
        return self._get_external_number("louvre_number")

    @property
    def dublin_tcd_number(self) -> str:
        return self._get_external_number("dublin_tcd_number")

    @property
    def cambridge_maa_number(self) -> str:
        return self._get_external_number("cambridge_maa_number")

    @property
    def ashmolean_number(self) -> str:
        return self._get_external_number("ashmolean_number")

    @property
    def alalah_hpm_number(self) -> str:
        return self._get_external_number("alalah_hpm_number")

    @property
    def australianinstituteofarchaeology_number(self) -> str:
        return self._get_external_number("australianinstituteofarchaeology_number")

    @property
    def achemenet_number(self) -> str:
        return self._get_external_number("achemenet")

    @property
    def nabucco_number(self) -> str:
        return self._get_external_number("nabucco")

    @property
    def digitale_keilschrift_bibliothek_number(self) -> str:
        return self._get_external_number("digitale_keilschrift_bibliothek_number")

    @property
    def philadelphia_number(self) -> str:
        return self._get_external_number("philadelphia_number")

    @property
    def seal_number(self) -> str:
        return self._get_external_number("seal_number")
