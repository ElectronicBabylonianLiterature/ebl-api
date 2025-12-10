from ebl.tests.factories.fragment import FragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.tests.atf_importer.conftest import (
    setup_and_run_importer,
)

# Add here any ATF text that you want to test for parsing problems.
# Skip the first line of the original atf.
# Try to find a minimal example that reproduces the problem.

TEXT = """#project: hbtin
#atf: use unicode
#atf: use mylines
#atf: lang akk-x-ltebab
#atf: use math
@tablet
@obverse
1.	{e₂}ku-ru-up-pu ša₂ {m}{d}na-na-a-MU DUMU ša₂ {m}ta-nit-tu₄-[{d}60]
#lem: kuruppu[(vegetable)basket//storehouse]N'N$; ša[of]DET; Nanaya-iddin[00]PN; māri[son]N; ša[of]DET; Tanittu-Anu[00]PN

2.	A {m}ŠEŠ-ʾu-u₂-tu ša₂ ina KI{+ti₃} {giš}KIRI₆-MAH ša₂ qe₂-reb UNUG{ki}
#lem: mār[descendant]N; Ahʾutu[1]LN; ša[that]REL; ina[in]PRP; erṣeti[city quarter]N; Kirimahhu[1]QN; ša[that]REL; qereb[within]'PRP; Uruk[1]SN

3.	ša₂ DA {e₂}ku-ru-up-pu ša₂ {f}mu-še-zib-i-tu₄
#lem: ša[that]REL; ṭāh[adjacent to]PRP; kuruppu[(vegetable)basket//storehouse]N'N$; ša[of]DET; Mušezibitu[00]PN$

4.	DUMU.MUNUS ša₂ {m}{d}INANA-ŠEŠ-MU u DA ŠA₃ A.ŠA₃ a-na i-di E₂
#lem: mārti[daughter]N; ša[of]DET; Ištar-ah-iddin[00]PN; u[and]CNJ; ṭāh[adjacent to]PRP; libbi[middle]N; eqli[field]N; ana[for]PRP; idi[rental]N; bīti[house]N

5.	a-na MU.AN.NA 4 GIN₂ KU₃.BABBAR ina IGI {m}{d}60-DIN{+iṭ}
#lem: ana[for]PRP; šatti[year]N; n; šiqil[unit]N; kaspi[silver]N; ina[in]PRP; mahru[front]N$mahar; Anu-uballiṭ[00]PN

6.	DUMU ša₂ {m}ki-din-{d}60 a-hi KU₃.BABBAR ina re-eš MU.AN.NA
#lem: māri[son]N; ša[of]DET; Kidin-Anu[00]PN; ahu[arm//one-half]N$ahi; kaspi[silver]N; ina[in]PRP; rēšu[head//beginning]N$rēš; šatti[year]N

7.	re-eh-tu₄ KU₃.BABBAR ina mi-šil MU.AN.NA ina-an-din
#lem: rēhtu[remainder]N; kaspi[silver]N; ina[in]PRP; mišil[half]NU; šatti[year]N; inandin[give]V

8.	u₂-ru i-ša₂-nu [x] bat-qa ša₂ a-sur-ru-u₂
#lem: ūru[roof]N; +šanû[sluice//seal]V'V$išannu; u; batqu[cut (off)//damage]AJ'N$batqa; ša[of]DET; asurrû[lower course]N

9.	i-ṣab-bat dul#-lu# SIG₄#-HI.A qa-nu-u₂ u {giš}UR₃
#lem: iṣabbat[repair]V; dullu[work]N; libittu[mudbrick]N$libnāti; qanû[reed]N$; u[and]CNJ; +ūru[roof//roof]N'N$ūri

10.	ma-la lib₃-bi ip-pu-uš a-na KU₃.BABBAR a-na muh-hi i-man-nu ina MU.AN.NA
#lem: mala[as much as]PRP; libbi[interior]N; ippuš[do]V; ana[for]PRP; kaspi[silver]N; ana[to]PRP; muhhi[skull]N; +manû[count//charge]V'V$imannu; ina[in]PRP; šatti[year]N

@reverse
1.	3 šu-gar-ru-u₂ ina-an-din ul-tu U₄ 10-KAM₂
#lem: n; šugarrû[(a processed form of dates)]N$; inandin[give]V; ultu[from]PRP; ūm[day]N; n

2.	ša₂ {iti}ŠU MU 8-KAM₂ {m}se-lu-ku LUGAL {e₂}ku#-ru-pu
#lem: ša[of]DET; Duʾuzu[1]MN; šanat[year]N; n; Seleucus[1]RN; šarru[king]N; kuruppu[storehouse]N

3.	MU-MEŠ a-na i-di E₂ a-na MU.AN.NA 4 GIN₂ KU₃.BABBAR
#lem: šū[that]IP; ana[for]PRP; idi[rental]N; bīti[house]N; ana[for]PRP; šatti[year]N; n; šiqil[unit]N; kaspi[silver]N

4.	ina IGI {m}{d}60-DIN{+iṭ} DUMU ša₂ {m}ki-din-{d}60
#lem: ina[in]PRP; mahru[front//front]N'N$mahar; Anu-uballiṭ[00]PN; māri[son]N; ša[of]DET; Kidin-Anu[00]PN

@witnesses
5.	{lu₂}mu-kin₇ {m}{d}60-ŠEŠ-LA₂ DUMU ša₂ {m}ni-din-tu₄-{d}60
#lem: mukīn[witness]N; Anu-ah-tuqqin[00]PN; māru[son]N; ša[of]DET; Nidintu-Anu[00]PN

6.	{m}NIG₂.BA-{d}60 DUMU ša₂ {m}ina-qi₂-bit-{d}60 A-šu₂ {m}la-ba-ši
#lem: Qišti-Anu[00]PN; māru[son]N; ša[of]DET; Ina-qibit-Anu[00]PN; māršu[son]N; Labaši[00]PN

7.	{m}{d}na-na-a-MU DUMU ša₂ {m}ki-din-{d}INANA {m}ša₂-{d}60-iš-šu-u₂
#lem: Nanaya-iddin[00]PN; māru[son]N; ša[of]DET; Kidin-Ištar[00]PN; Ša-Anu-iššu[00]PN

8.	DUMU ša₂ {m}ina-qi₂-bit-{d}60 {m}{d}60-AD-URI₃ DUMU ša₂ {m}{d}60-ŠEŠ-MEŠ-bul-luṭ
#lem: māru[son]N; ša[of]DET; Ina-qibit-Anu[00]PN; Anu-ab-uṣur[00]PN; māru[son]N; ša[of]DET; Anu-ahhe-bulluṭ[00]PN$

@colophon
9.	{m#}u₂-bar {lu₂}UMBISAG DUMU ša₂ {m}šir₃-ki-{d}60 UNUG{ki} {iti}ŠU
#lem: Ubar[00]PN; ṭupšarru[scribe]N; māru[son]N; ša[of]DET; Širki-Anu[00]PN; Uruk[1]SN; Duʾuzu[1]MN

10.	U₄ 5-KAM₂ MU 8-KAM₂ {m}se-lu-ku LUGAL
#lem: ūm[day]N; n; šanat[year]N; n; Seleucus[1]RN; šarru[king]N

$ (sealings)
@top
@column 1
@signature
1.	un-qa
#lem: unqa[ring]N

$ seal = AUWE 19, 0239
2.	[{m}]{d#}60-ŠEŠ-LA₂
#lem: Anu-ah-tuqqin[00]PN

@column 2
@signature
1.	un-qa
#lem: unqa[ring]N

$ seal = AUWE 19, 0899
2.	{m}NIG₂.BA-{d}60
#lem: Qišti-Anu[00]PN

@bottom
@column 1
@signature
1.	un-qa
#lem: unqa[ring]N

$ seal = AUWE 19, 0449
2.	{m}{d}60-AD-URI₃
#lem: Anu-ab-uṣur[00]PN

@column 2
@signature
1.	un-qa
#lem: unqa[ring]N

$ seal = AUWE 19, 0073
2.	{m}{d}na-na-a-MU
#lem: Nanaya-iddin[00]PN

@left
@column 1
@signature
1.	un-qa#*
#lem: unqa[ring]N

$ seal = AUWE 19, 0190
2.	{m}ša₂-{d}60-iš-šu-u₂
#lem: Ša-Anu-iššu[00]PN

@column 2
@signature
1.	ṣu-pur
#lem: ṣupur[nail]N

$ (Fingernail impression)
2.	{m}{d#}60-DIN{+iṭ}
#lem: Anu-uballiṭ[00]PN

# note: all edges collated, 3/28/07, LEP.

@translation labeled en project
@label(o 1-o 6)
A storehouse belonging to Nanaya-iddin, son of Tanittu-[Anu], descendant of Ahʾutu, that is in the Kirimahhu quarter which is in Uruk, which is next to the storehouse of Mušezibitu, daughter of Ištar-ah-iddin, and next to the middle of the field, (is) at the disposal of Anu-uballiṭ, son of Kidin-Anu, for the rental of the house for 4 shekels of silver per year.

@label(o 7-r 4)
He will pay half of the silver at the beginning of the year and the rest of the silver halfway through the year. He will plaster over the roof. He will repair the damage of the damp course. As much work (on) the bricks, the reeds, and the roof as he will do, he will count as a credit.  He will pay 3 (baskets of) @šugarrû dates each year. From the 10th day of the month Duʾuzu, the 8th year Seleucus (is) king, that storehouse (is) at the disposal of Anu-uballiṭ, son of Kidin-Anu, for the rental of the house for 4 shekels of silver per year.

@label(r 5)
Witnesses: Anu-ah-tuqqin, son of Nidintu-Anu

@label(r 6)
Qišti-Anu, son of Ina-qibit-Anu (and) his son, Labaši

@label(r 7-r 8)
Nanaya-iddin, son of Kidin-Ištar; Ša-Anu-iššu, son of Ina-qibit-Anu; Anu-ab-uṣur, son of Anu-ahhe-bulluṭ

@label(r 9-r 10)
Ubar, scribe, son of Širki-Anu. Uruk. Duʾuzu. 5th day. 8th year. Seleucus (is) king.

@label(t.e. i 1-t.e. i 2)
Ring of Anu-ah-tuqqin

@label(t.e. ii 1-t.e. ii 2)
Ring of Qišti-Anu

@label(b.e. i 1-b.e. i 2)
Ring of Anu-ab-uṣur

@label(b.e. ii 1-b.e. ii 2)
Ring of Nanaya-iddin

@label(l.e. i 1-l.e. i 2)
Ring of Ša-Anu-iššu

@label(l.e. ii 1-l.e. ii 2)
Fingernail of Anu-uballiṭ
"""


def test_parse_problematic_text(fragment_repository, tmp_path):
    museum_number = "X.17"
    fragment_repository.create(
        FragmentFactory.build(number=MuseumNumber.of(museum_number))
    )
    atf = f"&P000001 = {museum_number}\n{TEXT}"

    setup_and_run_importer(
        atf,
        tmp_path,
        fragment_repository,
    )
