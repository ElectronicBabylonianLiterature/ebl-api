import pytest

from ebl.atf_importer.domain.atf_preprocessor import ATFPreprocessor


PROBLEMATIC_TEXT_LINES = [
    (
        "1. [*] AN#.GE₆ GAR-ma U₄ ŠU₂{+up} * AN.GE₆ GAR-ma {d}IŠKUR KA-šu₂ ŠUB{"
        "+di} * AN.GE₆",
        "1. [DIŠ] AN#.GE₆ GAR-ma U₄ ŠU₂{+up} DIŠ AN.GE₆ GAR-ma {d}IŠKUR KA-šu₂ "
        "ŠUB{+di} DIŠ AN.GE₆",
    ),
    (
        "8. KAR <:> e-ṭe-ri :* KAR : e-ke-mu : LUGAL ina di-bi-ri : LUGAL ina "
        "ud-da-a-ta",
        "8. KAR < : > e-ṭe-ri :* KAR : e-ke-mu : LUGAL ina di-bi-ri : LUGAL ina "
        "ud-da-a-ta",
    ),
    (
        "14. [...] x (x) še-e-hu $BAD $E₂ $ME : ina GAŠAN-ia₅ {d}SUEN {"
        "d}INANA--<E₂>.AN.NA",
        "14. [...] x (x) še-e-hu BAD E₂ ME : ina GAŠAN-ia₅ {d}SUEN {"
        "d}INANA-<E₂>.AN.NA",
    ),
]


FOLLOWING_SIGN_IS_NOT_A_LOGOGRAM = (
    "5'.	[...] x [...] x-šu₂? : kal : nap-ha-ri : $WA-wa-ru : ia-ar₂-ru",
    "5'. [...] x [...] x-šu₂? : kal : nap-ha-ri : WA-wa-ru : ia-ar₂-ru",
)


LEGACY_GRAMMAR_SIGNS = [
    (
        "57. {mulₓ(AB₂)}GU.LA KI* ŠEG₃ KI*# {kur}NIM.MA{ki} iš-kar* É.GAL : "
        "ANŠE.KUR.RA-MEŠ",
        "57. {mulₓ(AB₂)}GU.LA KI* ŠEG₃ KI*# {kur}NIM.MA{ki} iš-kar* E₂.GAL : "
        "ANŠE.KUR.RA-MEŠ",
    ),
    (
        "57. {mulₓ(AB₂)}GU.LA KI* ŠEG₃ KI*# {kur}NIM.MA{ki} iš-kar* ÁM.GAL : "
        "ANŠE.KUR.RA-MEŠ",
        "57. {mulₓ(AB₂)}GU.LA KI* ŠEG₃ KI*# {kur}NIM.MA{ki} iš-kar* AM₃.GAL : "
        "ANŠE.KUR.RA-MEŠ",
    ),
]


@pytest.mark.parametrize(
    "line,expected",
    [*PROBLEMATIC_TEXT_LINES, FOLLOWING_SIGN_IS_NOT_A_LOGOGRAM, *LEGACY_GRAMMAR_SIGNS],
)
def test_text_lines(line, expected):
    atf_preprocessor = ATFPreprocessor("../logs", 0)

    (
        converted_line,
        c_array,
        c_type,
        c_alter_lemline_at,
    ) = atf_preprocessor.process_line(line)
    assert converted_line == expected


@pytest.mark.parametrize(
    "line",
    [
        "#lem: Sin[1]DN; ina[at]PRP; Nisannu[1]MN; ina[at]PRP; tāmartišu["
        "appearance]N; adir[dark]AJ; ina[in]PRP; "
        "aṣîšu[going out]'N; adri[dark]AJ; uṣṣi[go out]V; šarrū[king]N; "
        "+šanānu["
        "equal]V$iššannanū-ma",
        "#lem: iššannanū-ma[equal]V; +šanānu[equal]V$iššannanū-ma; umma["
        "saying]PRP; +šarru[king]N$; mala[as "
        "many]PRP; +šarru[king]N$šarri; +maṣû[correspond]V$imaṣṣû",
        "#lem: +adrūssu[darkly]AV$; īrub[enter]V; +arītu[pregnant ("
        "woman)]N$arâtu; ša[of]DET; libbašina[belly]N; "
        "ittadûni[contain]V; ina[in]PRP; +Zuqiqīpu[Scorpius]CN$",
        "#lem: šatti[year]N; n; +Artaxerxes[]RN$artakšatsu; šar[king]N; pālih["
        "reverent one]N; Nabu[1]DN; lā["
        "not]MOD; itabbal[disappear]V; maʾdiš[greatly]N; lišāqir[value]V",
        "#lem: +arāmu[cover]V$īrim-ma; ana[according to]PRP; birṣu[(a luminous "
        "phenomenon)]N; itârma[turn]V; adi["
        "until]PRP; šāt[who(m)]DET&urri[daytime]N; illakma[flow]V",
        "#lem: u; eššu[new]AJ; u +.",
        "#lem: u; ubû[unit]N; n; n; qû[unit]N; ubû[unit]N; +Ištar[]DN$; Ištar["
        "1]DN +.; +saparru[cart]N$; u",
        "#lem: !+māru[son]N$; !+māru[son]N$māri; târu[turning back]'N; +našû["
        "lift//carrying]V'N$ +.; u; "
        "+narkabtu[chariot]N$narkabta; īmur[see]V; marṣu[patient]N; šū["
        "that]IP; "
        "qāt[hand]N; Ištar[1]DN; u",
        "#lem: +burmāmu[(an animal)//porcupine?]N$; +burmāmu[(an "
        "animal)//porcupine?]N$buriyāmu; ša[whose]REL; "
        "+zumru[body]N$zumuršu; kīma[like]PRP; +ṭīmu[yarn]N$ṭime; +eṣēru["
        "draw//mark]V$uṣṣuru +.",
        "#lem: u; +appāru[reed-bed]N$",
        "#lem: attallû[eclipse]N; iššakinma[take place]V; enūma[when]SBJ; īrup["
        "cloud over]V; attallû[eclipse]N; "
        "iššakinma[take place]V; Adad[1]DN; +rigmu[voice]N$rigimšu; iddi[utter]V; "
        "attallû[eclipse]N",
        "#lem: iššakinma[take place]V; zunnu[rain]N; +zanānu[rain]V$izannun; "
        "attallû[eclipse]N; iššakinma[take "
        "place]V; berqu[lightning (flash)]N; +barāqu[lighten]V$ibriq; ana[on]PRP; "
        "muhhi[top]N; ummāti[summer]N; "
        "qabi[said]AJ",
        "#lem: +kamāru[pile up]V$ikkammarū; +dâku[kill]V$iddâkū; aššum[because "
        "of]'PRP; +kamāru[pile up//piling "
        "up]V'N$kamāri; X; arhiš[quickly]AV",
        "#lem: hanṭiš[quickly]AV; abūbu[flood]N; lā[not]MOD; mê[water]N; mūtānu["
        "epidemic]N; ubbal[sweep away]V; "
        "+našû[lift]V$inaššâ; aššum[because of]'PRP",
        "#lem: babālu[carrying]'N; +našû[lift//lifting]V'N$; attallû[eclipse]N; "
        "iššakinma[take place]V; erpeti["
        "cloud]N; ana[according to]PRP; libbi[interior]N; erpeti[cloud]N; īrub["
        "enter]V",
        "#lem: ilū[god]N; milik[mood]N; māti[land]N; ikkimū[take away]V; šar["
        "king]N; mātu[land]N; šū[that]IP; "
        "+ūmu[day]N$ūmēšu; +qerbu[near]AJ$qerbi; ina[in]PRP; attallê[eclipse]N",
        "#lem: kakkabi[star]N; ana[according to]PRP; libbi[interior]N; kakkabi["
        "star]N; īrub[enter]V; erpeti["
        "cloud]N; kakkabi[star]N; ikkimū[take away]V; +eṭēru[take away]V$iṭṭerū; "
        "+ekēmu[take away]V$ikkemū",
        "#lem: +eṭēru[take away//taking away]V'N$; +eṭēru[take away//taking "
        "away]V'N$; ekēmu[taking away]'N; "
        "ekēmu[taking away]'N; šar[king]N; ina[in]PRP; dibiri[calamity]N; šar["
        "king]N; ina[in]PRP; +ūdu["
        "distress]N$uddāta",
        "#lem: ittanallak[wander]V; attallû[eclipse]N; iššakinma[take place]V; "
        "ina[in]PRP; erpeti[cloud]N; peṣi["
        "white]AJ; ṣalmu[black]AJ; sāmū[red]AJ; aruqtu[yellow-green]AJ; u["
        "and]CNJ; burruma[multicoloured]AJ",
        "#lem: u[and]CNJ; +duʾʾumu[very dark]AJ$duʾʾum; izzazma[stand]V; u["
        "and]CNJ; namir[bright]AJ; mala[as "
        "many]'REL; iqbû[say]V; ana[on]PRP; muhhi[top]N; bibbū[planet]N",
        "#lem: erpeti[cloud]N; qabi[said]AJ; erpeti[cloud]N; +erû["
        "naked//empty]AJ'AJ$erētu; erpeti[cloud]N; "
        "+sāmu[red]N$sānda",
        "#lem: erpeti[cloud]N; +alludānu[(a meteor. phenomenon)]N$; erpeti["
        "cloud]N; ša[of]DET; mala[as many]'REL; "
        "Šamaš[1]DN; +maṣû[corresponding]AJ$",
        "#lem: šanîš[alternatively]AV; erpeti[cloud]N; ša[of]DET; +kalû["
        "all]AJ$kalla; ūmu[day]N; u[and]CNJ; mūši["
        "night]N; izzazzu[stand]V; erpeti[cloud]N; mala[as many]'REL",
        "#lem: iqbû[say]V; ana[on]PRP; muhhi[top]N; ummāti[summer]N; qabi["
        "said]AJ; ilū[god]N; šar[king]N; "
        "+labāru[be(come) old]V$ulabbarū; ana[according to]PRP; ūmū[day]N; u; u",
        "#lem: ana[on]PRP; muhhi[top]N; mātu[land]N; nadītu[abandoned]AJ; qabi["
        "said]AJ; attallû[eclipse]N; "
        "iššakinma[take place]V; ina[in]PRP; +tarbaṣu[animal stall]N$; illak["
        "flow]V; u[and]CNJ; namir[bright]AJ",
        "#lem: ina[in]PRP; kūṣi[winter]N; ina[from]PRP; šamê[heaven]N; +zakû["
        "pure]AJ$zakūtu; +namir["
        "bright]AJ$namir-ma; +tarbaṣu[animal stall]N$; ana[on]PRP; muhhi[top]N; "
        "šamê[heaven]N",
        "#lem: šamê[heaven]N; zakūtu[pure]AJ; qabi[said]AJ; attallû[eclipse]N; "
        "iššakinma[take place]V; tarbaṣ["
        "animal stall]N; lamima[surrounded]AJ; šarru[king]N; ana[according "
        "to]PRP; u",
        "#lem: +dâku[kill//killing]V'N$; u; u; u; +tarbaṣu[animal stall]N$; "
        "lamima[surrounded]AJ; u; bīt[house]N; "
        "adir[dark]AJ; u; u; +tebû[get up]V$",
        "#lem: u; u; u; u; u; +tebû[get up//getting up]V'N$; +tebû[get "
        "up//getting up]V'N$; +tebû[get up//getting "
        "up]V'N$; šanîš[alternatively]AV; +gapāšu[rise upwards//rising "
        "upwards]V'N$; attallû[eclipse]N; "
        "iššakinma[take place]V",
        "#lem: u; u; u; u; u; illak[flow]V; ramāni[self]N; +ramānu[self]N$remāni; "
        "+arratu[curse]N$; +arratu["
        "curse]N$; u; u; X",
        "#lem: u; u; u; u; u; libbū[from out of]PRP; +šāru[wind]N$; +ṣēlu["
        "rib]N$ṣēli; šāri[wind]N; ṣēlī[rib]N",
        "#lem: +ṣâdu[prowl//prowling]V'N$; ṣâdu[prowling]'N; +lawû["
        "surround//surrounding]V'N$lamû; +lawû["
        "surround//surrounding]V'N$lamû; attallû[eclipse]N; iššakinma[take "
        "place]V; attallû[eclipse]N; šū["
        "that]IP; peṣi[white]AJ",
        "#lem: ṣalmu[black]AJ; sāmū[red]AJ; aruq[yellow-green]AJ; burruma["
        "multicoloured]AJ; ina[in]PRP; erpeti["
        "cloud]N; attallû[eclipse]N; iššakinma[take place]V; šanîš["
        "alternatively]AV; ana[according to]PRP; muhhi["
        "top]N; šikin[appearance]N",
        "#lem: attallû[eclipse]N; qabi[said]AJ; Sin[1]DN; adriš[dimly]AV; uṣṣima["
        "leave]V; idlip[be sleepless]V; "
        "šahluqti[annihilation]N",
        "#lem: māti[land]N; kalāma[all (of it)]N; u; +sahmaštu[rebellion]N$; "
        "adir[dark]AJ; uṣṣima[leave]V; "
        "+dalāpu[stir up//linger on]V'V$idlip; ikūš[be(come) late]V",
        "#lem: Sin[1]DN; adriš[dimly]AV; uṣṣima[leave]V; adi[until]PRP; namāri["
        "be(come) bright]V; izzazzū["
        "stand]V; ina[in]PRP; erpeti[cloud]N; adir[eclipsed]AJ; uṣṣima[leave]V; "
        "šamê[heaven]N; unammarma[ignite]V",
        "#lem: šanîš[alternatively]AV; ina[in]PRP; rēš[start]N; +kūṣu["
        "coldness]N$kūṣi; namir[bright]AJ; adriš["
        "dimly]AV; uṣṣima[leave]V; adriš[dimly]AV; īrub[enter]V",
        "#lem: ina[in]PRP; erpeti[cloud]N; adri[dark]AJ; uṣṣima[leave]V; adri["
        "dark]AJ; irbima[disappear]V; Sin["
        "1]DN; adriš[dimly]AV; īrub[enter]V",
        "#lem: ina[in]PRP; idirtu[misery]N; ina[in]PRP; erpeti[cloud]N; īrubma["
        "enter]V; ina[in]PRP; erpeti["
        "cloud]N; irbima[disappear]V; šanîš[alternatively]AV",
        "#lem: +kayyānu[constant]AJ$; Sin[1]DN; ina[at]PRP; rēšišu[top]N; adir["
        "dark]AJ; mātu[land]N; kiššat["
        "all]N; nišū[people]N",
        "#lem: adi[until]PRP; +ulla[at some time]AV$; +riāhu[remain]V$irihhā; "
        "ina[in]PRP; rēšišu[top]N; ina["
        "on]PRP; rēšišu[top]N; tāmarti[visibility]N",
        "#lem: u; u; u; u; u; u; +riāhu[remain]V$irihhā; +dâku[kill]V$iddakkā",
        "#lem: u; rikis[cosmic bond]N; lumnu[evil]N; naphar[all]N; lumnu[evil]N; "
        "ina[in]PRP; qaraššu[horn]N; "
        "adirma[dark]AJ; ina[in]PRP; qablišu[middle]N",
        "#lem: +gašru[very strong]AJ$gašir; ina[in]PRP; imittišu[right]N; adir["
        "dark]AJ; u; habrat[thick]AJ; "
        "attallû[eclipse]N; iššakinma[take place]V; ina[in]PRP; qablišu[middle]N; "
        "adirma[dark]AJ",
        "#lem: u[and]CNJ; +elēhu[strew]V$īlih; ina[in]PRP; qablišu[middle]N; ina["
        "in]PRP; mišil[half]NU; arhī["
        "month]N; ūmū[day]N; n; attallû[eclipse]N; iššakinma[take place]V",
        "#lem: +elēhu[strew//strewing]V'N$; +elēhu[strew//strewing]V'N$elēhi; "
        "+nawāru[be(come) bright//be(com)ing "
        "bright]V'N$namāru; +nawāru[be(come) bright//be(com)ing "
        "bright]V'N$namāri; adirma[dark]AJ; imitti["
        "right]N; u[and]CNJ; šumēlišu[left]N; namir[bright]AJ",
        "#lem: ana[according to]PRP; attallû[eclipse]N; īṣa[few]AJ; ša[of]DET; "
        "hanṭiš[quickly]AV; namru["
        "bright]AJ; Sin[1]DN; adir[dark]AJ; u[and]CNJ; namru[bright]AJ; +zīmu["
        "face]N$zīmūšu; peṣi[white]AJ; "
        "ilāni[god]N; mātu[land]N; hepi[broken]AJ",
        "#lem: u; u; attallû[eclipse]N; +kakkabu[star]N$; u; irbima[disappear]V; "
        "u; u; u; u; u; u; u; u; u; u",
        "#lem: +dabdû[defeat]N$tabdê; mātu[land]N; iššakkan[take place]V; "
        "+qaddadāniš[bowed down]AV$qaddiš; "
        "+rabû[be big]V$irbi; peṣi[white]AJ; ṣalmu[black]AJ; sāmū[red]AJ; aruq["
        "yellow-green]AJ; burruma["
        "multicoloured]AJ; u[and]CNJ; +duʾʾumu[very dark]AJ$; mala[as many]'REL",
        "#lem: iqbû[say]V; ana[on]PRP; muhhi[top]N; bibbī[planet]N; u[and]CNJ; "
        "erpeti[cloud]N; qabi[said]AJ; Sin["
        "1]DN; adirma[dark]AJ; bāltašu[dignity]N",
        "#lem: +arāmu[cover]V$īrim; attallû[eclipse]N; ina[on]PRP; erpeti["
        "cloud]N; +ṣalmu[black]AJ$ṣalimtu; "
        "raqqatu[thin]AJ; illakma[flow]V; Sin[1]DN; adirma[dark]AJ; +mithāriš[in "
        "the same manner]AV$",
        "#lem: +arāmu[cover]V$īrim-ma; ana[according to]PRP; birṣu[(a luminous "
        "phenomenon)]N; itârma[turn]V; adi["
        "until]PRP; šāt[who(m)]DET&urri[daytime]N; illakma[flow]V",
        "#lem: lemutti[evil]N; mātu[land]N; +mithāriš[in the same manner]AV$; "
        "iššakkan[take place]V; palâ[period "
        "of office]N; mātu[land]N; ina[in]PRP; dabdu[defeat]N; ikkimū[take "
        "away]V; mātu[land]N; bubūt[hunger]N; "
        "dannu[strong]AJ; +amāru[see]V$immar",
        "#lem: attallû[eclipse]N; qatītu[completed]AJ; šakinma[placed]AJ; kīma["
        "according to]PRP; kakkabi[star]N; "
        "+kaṣāru[tie]V$ikaṣṣar-ma; ina[in]PRP; libbi[interior]N; mātitān[all "
        "countries]N; ina[in]PRP; tabdê["
        "defeat]N",
        "#lem: +eṭēru[take away]V$ineṭṭera; iqbi[speak]V; birṣu[(a luminous "
        "phenomenon)]N; kakkabi[star]N; "
        "+birṣu[sheen]N$; birṣu[(a luminous phenomenon)]N",
        "#lem: birṣu[sheen]N; +ezēbu[leave//leaving]V'N$; ezēbi[leaving]'N; Sin["
        "1]DN; adirma[dark]AJ; qimmatsu[(a "
        "feature of the moon)]N; šamê[heaven]N; dalhat[disturbed]AJ",
        "#lem: attallû[eclipse]N; +ešû[confused]AJ$ešītu; +dilhu[disturbed "
        "state]N$dilhi; ina[in]PRP; pān["
        "front]N; šamê[heaven]N; ibaššima[exist]V; niši[people]N; mātu[land]N; "
        "+lemnu[bad]N$lemnīša; +amāru["
        "see]V$immar",
        "#lem: umma[saying]PRP; niši[people]N; mātu[land]N; +zāʾeru["
        "hostile]N$zāʾerēšu; +naṭālu[look]V$inaṭṭal; "
        "Sin[1]DN; ana[to]PRP; arhišu[first day of month]N",
        "#lem: u; u; u; šakin[displayed]AJ; ša[of]DET; adannu[appointed time]N; "
        "ana[to]PRP; adannu[appointed "
        "time]N; attallû[eclipse]N; +šakānu[put]V$iššakkana",
        "#lem: Sin[1]DN; ina[at]PRP; Nisannu[1]MN; ina[at]PRP; tāmartišu["
        "appearance]N; adir[dark]AJ; ina[in]PRP; "
        "aṣîšu[going out]'N; adri[dark]AJ; uṣṣi[go out]V; šarrū[king]N; +šanānu["
        "equal]V$iššannanū-ma",
        "#lem: iššannanū-ma[equal]V; +šanānu[equal]V$iššannanū-ma; umma["
        "saying]PRP; +šarru[king]N$; mala[as "
        "many]PRP; +šarru[king]N$šarri; +maṣû[correspond]V$imaṣṣû",
        "#lem: +šanānu[equal//equaling]V'N$; +šanānu[equal//equaling]V'N$; "
        "+šanānu[equal//equaling]V'N$; kašādu["
        "reaching]'N; ina[in]PRP; Simanu[1]MN; ūmu[day]N; n; attallû[eclipse]N; "
        "iššakinma[take place]V",
        "#lem: +adrūssu[darkly]AV$; īrub[enter]V; +arītu[pregnant ("
        "woman)]N$arâtu; ša[of]DET; libbašina[belly]N; "
        "ittadûni[contain]V; ina[in]PRP; +Zuqiqīpu[Scorpius]CN$; attallû["
        "eclipse]N; iššakinma[take place]V",
        "#lem: ūmu[day]N; n; u[and]CNJ; ūmu[day]N; n; +šuklulū[perfect]AJ$; "
        "šuklulū[perfect]AJ; šanîš["
        "alternatively]AV; šullumu[keeping safe]'N",
        "#lem: ina[in]PRP; Tašritu[1]MN; ūmu[day]N; n; attalli[eclipse]N; Sin["
        "1]DN; iššakkanma[take place]V; "
        "adrūssu[darkly]AV; īrub[enter]V; u",
        "#lem: šamê[heaven]N; ippaṭir[release]V; šar[king]N; +Elam[]GN$; imât["
        "die]N; ina[in]PRP; Gula[1]CN; "
        "attallû[eclipse]N; iššakinma[take place]V",
        "#lem: Gula[1]CN; qaqqar[district]N; zunnu[rain]N; qaqqar[district]N; "
        "+Elam[]GN$; +iškāru[work "
        "assignment]N$iškar; ēkalli[palace]N; sisê[horse]N",
        "#lem: +šamāru[rage]V$ištamar; išassi[cry out]V; aššum[because of]'PRP; "
        "šitmuru[be(com)ing furious]'N; "
        "šasû[shouting]'N",
        "#lem: abūbi[flood]N; mīlu[flood]N; gapšu[swollen]AJ; šar[king]N; +agû["
        "tiara]N$agî; šarru[king]N; dannu["
        "mighty]AJ; ina[in]PRP; Arahsamnu[1]MN",
        "#lem: ūmu[day]N; n; attallû[eclipse]N; šakin[displayed]AJ; adrūssu["
        "darkly]AV; īrub[enter]V; +ikkillu["
        "lamentation]N$; +eli[on]PRP$; māti[land]N; +maqātu[fall]V$imaqqut",
        "#lem: ikkillu[lamentation]N; ikkillu[lamentation]N; šanîš["
        "alternatively]AV; +ašša[because]PRP$; libbānu["
        "inside]N; qaqqar[district]N; +Zappu[Plejades]CN$; u[and]CNJ; +Alû["
        "Taurus]CN$; mūtū[death]N",
        "#lem: ina[in]PRP; Kislimu[1]MN; ūmu[day]N; n; attallû[eclipse]N; "
        "iššakkan[take place]V; adrūssu["
        "darkly]AV; īrub[enter]V; šarru[king]N; šisītu[cry]N; elišu[over]PRP; "
        "+nadû[throw (down)]V$inaddi",
        "#lem: ina[in]PRP; qaqqar[district]N; +Šitaddaru[Orion]CN$; šanîš["
        "alternatively]AV; ana[according to]PRP; "
        "tarṣi[extent]N; +Pabilsag[]CN$; mūtū[death]N",
        "#lem: ina[in]PRP; Šabaṭu[1]MN; ūmu[day]N; n; attalli[eclipse]N; Sin["
        "1]DN; iššakkanma[take place]V; "
        "adrūssu[darkly]AV; īrub[enter]V; ilu[god]N; ikkal[eat]V",
        "#lem: ina[in]PRP; qaqqar[district]N; +Maštabbagalgal[]CN$; mūtū[death]N; "
        "ina[in]PRP; Addaru[1]MN; ūmu["
        "day]N; n; attalli[eclipse]N; Sin[1]DN; iššakkanma[take place]V",
        "#lem: adrūssu[darkly]AV; īrub[enter]V; tašnintu[battle]N; ina[in]PRP; "
        "māti[land]N; ibašši[exist]V; ina["
        "in]PRP; qaqqar[district]N; +Absinnu[Virgo]CN$; u[and]CNJ; +Kayyamānu["
        "Saturn]CN$",
        "#lem: tašnintu[battle]N; +dumqu[goodness]N$; u[and]CNJ; lumnu[evil]N; "
        "ša[that]REL; ina[in]PRP; attallû["
        "eclipse]N; iqbû[say]V; qaqqar[district]N; arhišu[first day of month]N; "
        "ana[towards]PRP; erṣetu[earth]N; "
        "ša[which]REL; ana[for]PRP; mātu[land]N; mihirti[complaint against]N; "
        "hepi[broken]AJ",
        "#lem: ṣâtu[commentary]N; u[and]CNJ; šūt[those of]DET; pî[mouth]N; "
        "+massûtu[call//lecture]N'N$malsûti; "
        "ša[of]DET; +inūma[when]CNJ$enūma; Anum[1]DN; +Ellil[]DN$",
        "#lem: attallû[eclipse]N; iššakinma[take place]V; ūmu[day]N; īrup[cloud "
        "over]V; qati[completed]AJ; "
        "arkišu[after]PRP; ina[in]PRP; Nisannu[1]MN; ūm[day]N; n; attallû["
        "eclipse]N; iššakkan[take place]V",
        "#lem: +ṭuppu[(clay) tablet]N$ṭuppi; +Ipraya[]PN$; aplu[son]N; "
        "+Arad-Baba[]PN$; aplu[son]N; Eṭiru[1]PN; "
        "+šaṭāru[write (down)]V$išṭur; Šabaṭu[1]MN; ūmu[day]N; n",
        "#lem: šatti[year]N; n; +Artaxerxes[]RN$artakšatsu; šar[king]N; pālih["
        "reverent one]N; Nabu[1]DN; lā["
        "not]MOD; itabbal[disappear]V; maʾdiš[greatly]N; lišāqir[value]V",
        "#lem: u; u; u",
        "#lem: X; attallû[eclipse]N; iššakkan[take place]V; šar[king]N; imâtma["
        "die]V",
        "#lem: mātu[land]N; iharrub[be(come) deserted]V; namê[deserted land]N; "
        "nakri[enemy]N; +mahāṣu["
        "beat]V$imahhaṣ",
        "#lem: u; +mahāṣu[beat//beating]V'N$; +mahāṣu[beat//beating]V'N$",
        "#lem: mahāṣu[beating]'N; +ugula[the sign PA]N$; +hehû[the sign GAN]N$; "
        "+mahāṣu[beat//beating]V'N$; "
        "mahāṣu[beating]'N; +mahāṣu[beat//beating]V'N$",
        "#lem: u; +kamāsu[gather in//gathering in]V'N$",
        "#lem: X; attallû[eclipse]N; iššakkan[take place]V; hiṣib[(abundant) "
        "yield]N; tâmti[sea]N; ihalliqma[be "
        "destroyed]V",
        "#lem: u; +appāru[reed-bed]N$; X; +qinnu[nest]N$; iṣṣūru[bird]N; +qanānu["
        "nest]V$iqannunšu",
        "#lem: tâmti[sea]N; appāru[reed-bed]N; +ewû[become]V$immi; qinnu[nest]N; "
        "iṣṣūri[bird]N; +qanānu["
        "nest]V$iqannunšu",
        "#lem: emû[becoming]'N; mašālu[equalling]'N; +qanānu[nest//nesting]V'N$; "
        "+qanānu[nest//nesting]V'N$",
        "#lem: X; attallû[eclipse]N; iššakkan[take place]V; ina[in]PRP; Abu[1]MN; "
        "Adad[1]DN",
        "#lem: rigimšu[voice]N; inaddima[raise]V; ilu[god]N; +akālu[eat]V$ikkal",
        "#lem: arki[after]PRP; šatti[year]N; Adad[1]DN; būli[livestock]N; "
        "irahhiṣ[devastate]V",
        "#lem: Abu[1]MN; arhu[month]N; +šuātu[that//that]IP'AJ$; +šuātu["
        "that//that]IP'AJ$; +šuātu["
        "that//that]IP'AJ$",
        "#lem: X; attallû[eclipse]N; iššakkan[take place]V; zunnū[rain]N; ina["
        "from]PRP; šamê[heaven]N",
        "#lem: mīlū[flood]N; ina[in]PRP; nagbi[source]N; ipparrasū[cut (off)]V; "
        "mātu[land]N; ana[according "
        "to]PRP; mātu[land]N; +hâqu[go]V$ihâq-ma; šalāmu[peace]N; šakin["
        "displayed]AJ",
        "#lem: +hâqu[go//going]V'N$; alāku[going]'N",
        "#lem: u; attallû[eclipse]N; iššakkan[take place]V; u",
        "#lem: u; u; u; u; u; u; u",
        "#lem: u; +patāqu[shape//mould]V$upattiq; +Ea[1]DN$; +pahāru[potter]N$; u",
        "#lem: u; +karpatu[pot]N$karpat; +haṣbu[pottery//potsherd]N$haṣabumma; "
        "+mâtu[die]V$imtūt; +awīlūtu["
        "humanity]N$amēlūtu +.; +ēṣidu[reaper]N$ēṣid; u",
        "#lem: u; +edû[know]V$īde; +ṣalmu[effigy//image]N$ṣalam; +ṭīdu["
        "clay]N$ṭiṭṭi; +awīlūtu[humanity]N$amēlutti "
        "+.; +ṭīdu[clay]N$ṭiṭṭi; +karāṣu[break off]V$iktariṣ; u",
        "#lem: ittadi[throw]V; ina[in]PRP; ṣēri[open country]N +.; ina[in]PRP; "
        "ṣēri[open country]N; +Enkidu[]DN$; "
        "ibtani[create]V; u +.",
        "#lem: u; ašar[place]N; nīqi[offering]N; +mehru[copy//offering]N$mehri "
        "+.; ullânu[there and then]AV; "
        "ašar[place]N; +tēbibtu[purification]N$tēbibti",
        "#lem: u; +talīmu[favourite brother]N$; +qiāpu[("
        "en)trust//entrusting]V'N$qâpu; +talīmu[favourite "
        "brother]N$talīm; +qiāpu[(en)trust//entrusting]V'N$qâpi; tēbibti["
        "purification]N +.",
        "#lem: u; šikaru[beer]N; rēštû[first-class]'AJ; nindabû[(food) "
        "offering]N; ilī[god]N; rabûti[great]AJ; "
        "+qerēbu[approach]V$uqtarrab; u +.",
        "#lem: u; +namerimburrudû[(ritual to remove a curse)]N$namerimburrudi; "
        "māmīti[curse]N; +mala[as much "
        "as//any]PRP'REL$mal; ina[in]PRP; +sakikkû[ailment//(title of omen "
        "series)]N$sakikkî +.",
        "#lem: u; uzabbalma[linger]V; +kâšu[delay//linger]V$ikâšma; +zabālu["
        "carry//lingering]V'N$zubbulu; +kâšu["
        "delay//lingering]V'N$ikâša; +libbū[from out of//meaning]PRP$",
        "#lem: +kabātu[be(come) heavy//be(come) aggravating]V$ikabbitma; +zabālu["
        "carry//lingering]V'N$; +zabālu["
        "carry//lingering]V'N$; ša[of]DET; +murṣu[illness]N$murṣu +.; ubān["
        "finger]N; imittišu[right]N; rabīti["
        "big]AJ; +nakāpu[push//stub]V$ikkip",
        "#lem: u; ubānu[finger]N; +ubānu[finger]N$; +qabru[grave]N$ +.; šahâ["
        "pig]N; ṣalma[black]AJ; īmur[see]V; "
        "marṣu[patient]N; šū[that]IP; imât[die]V; šanîš[alternatively]AV; "
        "+pašāqu[be(come) "
        "narrow//suffer]V$uštapaššaqma; iballuṭ[recover]V +.",
        "#lem: u; dannu[strong]AJ; u; šahû[pig]N; +eṭlu[young man]N$; šahû[pig]N; "
        "u; +šahû[pig]N$; šahû[pig]N; "
        "lēbu[(a disease)]N",
        "#lem: u; šahû[pig]N; ana[to]PRP; qereb[centre]N; +uršu[bedroom]N$urši; "
        "+erēbu[enter]V$īrub; +esertu["
        "confined woman//concubine]N$eserti; u; bīt[house]N; +bēlu["
        "lord//master]N$bēlišu; irrub[enter]V +.",
        "#lem: u; ina[on]PRP; +mēlû[height]N$mēlê; +šaknu[placed//laid]AJ$šakin; "
        "+esertu[confined "
        "woman//concubine]N$aserti; ša[that]REL; qabû[said]AJ; +esēru["
        "confinement]N$esēr; marṣi[patient]N +.",
        "#lem: u; marṣu[patient]N; +dannatu[fortress//distress]N$dannata; īmur["
        "experience]V; iballuṭ[live]V +.; "
        "kī[if]'MOD; dannata[distress]N; lā[not]MOD; īmur[experience]V; imât["
        "die]V +.; šanîš[alternatively]AV; "
        "kī[if]'MOD",
        "#lem: u; +naqdu[one in critical state]N$; ana[within]PRP; n; ūmī[day]N; "
        "kī[if]'MOD; lā[not]MOD; naqdu["
        "one in critical state]N; ana[within]PRP; arhi[month]N; n; imât[die]V +.; "
        "šahâ[pig]N; +burrumu["
        "multicoloured]AJ$burruma; īmur[see]V; ša[of]DET; qabû[said]AJ +.",
        "#lem: +burmāmu[(an animal)//porcupine?]N$; +burmāmu[(an "
        "animal)//porcupine?]N$buriyāmu; ša[whose]REL; "
        "+zumru[body]N$zumuršu; kīma[like]PRP; +ṭīmu[yarn]N$ṭime; +eṣēru["
        "draw//mark]V$uṣṣuru +.",
        "#lem: +aganutillû[dropsy]N$aganutillâ; +warkītu["
        "posterity//future]N$arkât; lā[not]MOD; +bašû["
        "exist//existing]V'N$bašê; aganutillâ[dropsy]N; ša[who]REL; +warkītu["
        "posterity//future]N$arkâtsu; lā["
        "not]MOD; +balāṭu[live//living]V'N$ +.",
        "#lem: aganutillâ[dropsy]N; +makkūru[property]N$makkūr; ilī[god]N; lā["
        "not]MOD; +qatû["
        "finish//ending]V'N$qātû +.; mû[water]N; mê[water]N",
        "#lem: u; +našû[lift//bringing]V'N$; +habû[draw (water)//drawing ("
        "water)]V'N$; ša[of]DET; mê[water]N +.; "
        "+makkūru[property]N$; +makkūru[property]N$ +.; šanîš[alternatively]AV; "
        "+našû[lift//carrying]V'N$; +našû["
        "lift//carrying]V'N$ +.",
        "#lem: u; u; u; u; u; u; u; +zabbilu[bearer]N$zabbil; mê[water]N; ša["
        "who]REL; mê[water]N; ana[to]PRP; "
        "+habû[draw (water)//drawing (water)]V'N$habê +.",
        "#lem: u; u; u; u +.; alpa[ox]N; peṣâ[white]AJ; īmur[see]V; marṣu["
        "patient]N; šū[that]IP; qāt[hand]N; "
        "Ninurta[1]DN +.; ina[in]PRP; +urû[stable//stall]N$urê; alpi[ox]N",
        "#lem: Ninurta[1]DN; u +.; ikkib[taboo]N; Ninurta[1]DN +.; alpa[ox]N; "
        "burruma[multicoloured]AJ; īmur["
        "see]V; marṣu[patient]N; šū[that]IP",
        "#lem: Lamaštu[1]DN; iṣbassu[seize]V +.; u; Lamaštu[1]DN; ummu[fever]N; "
        "mārat[daughter]N; Anu[1]DN; X; "
        "ummu[fever]N +.",
        "#lem: u; +māmītu[oath//curse]N$māmītiša; imât[die]V +.; +šīmtu[fate]N$; "
        "u; +mūtu[death]N$; +raggu["
        "wicked]AJ$; raggu[wicked]AJ; hīpi[broken place]N",
        "#lem: u; raggu[wicked]AJ; imât[die]V +.; +barāmu[be(come) "
        "variegated//be(com)ing multicoloured]V'N$; "
        "+barāmu[be(come) variegated//be(com)ing multicoloured]V'N$; ša[that]REL; "
        "qabû[said]AJ; kīma[like]PRP; "
        "+nimru[leopard]N$nimri; +tukkupu[spotted]AJ$tukkupā",
        "#lem: u +.; +Lamaštu[1]DN$; +isiqtu[engraving]N$; +māmītu["
        "oath//curse]N$; +hursānu[river ordeal]N$ +.",
        "#lem: u; u; u; +māmītu[oath//curse]N$; +hursānu[river ordeal]N$huršān; "
        "+nīšu[life]N$nīš; ilī[god]N",
        "#lem: u; u; +rupuštu[phlegm//spittle]N$rupušti; +rupuštu["
        "phlegm//spittle]N$rupušti",
        "#lem: u; +šūru[bull]N$; +epinnu[(seed) plough]N$",
        "#lem: u; +nekelmû[frown at//frowning at]V'N$; +nekelmû[frown "
        "at//frowning at]V'N$; +īnu[eye]N$; +īnu["
        "eye]N$īni",
        "#lem: u; +nekelmû[frown at//frowning at]V'N$; nekelmû[frowning at]'N; "
        "ša[for]DET; +īnu[eye]N$īnšu",
        "#lem: u; +našāku[bite]V$iššuku; nekelmû[frowning at]'N; amāri[seeing]'N; "
        "ša[concerning]DET; +zêru["
        "hate//hating]V'N$zêri +.",
        "#lem: u; +nakāpu[push//stub]V$ikkipšu; marṣu[patient]N; šū[that]IP; "
        "+naqdu[one in critical "
        "state]N$naqud; lā[not]MOD; +ṭehû[approach]V$iṭehhešu; ša[that]REL; iqbû["
        "say]V; ina[in]PRP; libbi["
        "concern]N; ša[of]DET; alpi[ox]N; +alpu[ox]N$alpi; +eṭemmu[ghost]N$; "
        "+eṭemmu[ghost]N$ +.",
        "#lem: u; īmur[see]V; marṣu[patient]N; šū[that]IP; imât[die]V +.; +qarnu["
        "horn]N$; qarnu[horn]N; qarnu["
        "horn]N; nūr[light]N; qarnu[horn]N; šarūru[brilliance]N",
        "#lem: +libbū[from out of//meaning]PRP$; +šarūru[brilliance]N$šarūrūšu; "
        "+maqātu[fall//fade]V$imqutū +.; "
        "+imēru[donkey]N$; +atānu[she-ass//jenny]N$atāna; +rakābu["
        "ride//mount]V$irkabma; īmur[see]V; marṣu["
        "patient]N; šū[that]IP",
        "#lem: u; u[and]CNJ; šū[him]IP; +kapālu[roll up//intertwine]V$iktappilū "
        "+.; X; imēru[donkey]N; X; lā["
        "not]MOD; +paṭāru[loosen//realising]V'N$napṭuru +.",
        "#lem: u; pānī[face]N; imēri[donkey]N; šanîš[alternatively]AV; pānī["
        "face]N; ṣerri[snake]N +.; qāt[hand]N; "
        "aššat[wife]N; amēli[man]N; libbū[meaning]PRP; ana[to]PRP; aššat[wife]N; "
        "amēli[man]N; iṭhe[approach]V +.",
        "#lem: u; +rahāṣu[trample]V$irhissu; imēru[donkey]N; +rahāṣu["
        "trample]V$irhissu; +rahāṣu["
        "trample//trampling]V'N$; +mahāṣu[beat//beating]V'N$ +.; +mahhû["
        "ecstatic]N$mahhâ; īmur[see]V; qāt[hand]N; "
        "Ninurta[1]DN +.",
        "#lem: +mahhû[ecstatic]N$; +mahhû[ecstatic]N$; +Lugalbaguba[]DN$; "
        "Ninurta[1]DN +.; +šīmtu[fate]N$; murṣu["
        "illness]N; šanîš[alternatively]AV; šīmtu[fate]N",
        "#lem: u; +ulāpu[rag]N$; +ulāpu[rag]N$ulāpa; +sūnu[loin]N$; +ulāpu["
        "rag]N$; +ulāpu[rag]N$ulāpa; +ubānu["
        "finger]N$; ubānu[finger]N",
        "#lem: u; +kamû[bind//binding]V'N$ +.; +ernittu[triumph]N$; +kadru["
        "rearing up//overbearing]AJ$; nekelmû["
        "frowning at]'N +.; ila[god]N; +sahhiru[roaming]AJ$sahhira; +Gazbaba[]DN$",
        "#lem: u; u; u; +šēhu[wind//ecstatic]N$; u; u; u; ina[with]PRP; "
        "+Beletiya[]DN$; Sin[1]DN; +Belet-Eana[]DN$",
        "#lem: u; Gazbaba[1]DN; +qabû[say//speak]V$iqtabi; šanîš["
        "alternatively]AV; +La-tarak[1]DN$La-taraka; "
        "šalšiš[thirdly]AV; +Unaniši[]DN$",
        "#lem: u; Tuʾamu[Twins]'DN; ša[that]REL; qabû[said]AJ; Tuʾamu[Twins]'CN; "
        "ša[that]REL; mehret[opposite "
        "side]N; Šitaddaru[Orion]CN",
        "#lem: izzazzū[stand]V; Lulal[1]DN; u[and]CNJ; La-taraka[1]DN +.; +pessû["
        "lame one//dwarf]N$pessâ; īmur["
        "see]V; qāt[hand]N; Ninurta[1]DN +.",
        "#lem: u; +pessû[lame one//dwarf]N$; +kurû[short one//dwarf]N$ +.; "
        "+pessû[lame one//dwarf]N$; +mišlu["
        "half]NU$; mišil[half]NU",
        "#lem: u; amēlu[man]N; +Šaddaru[]DN$Šaddari; Ninurta[1]DN; +šadaru[("
        "meaning unknown)]N$; mišil[half]NU +.",
        "#lem: u; +sukkuku[deaf one]N$; īmur[see]V; qāt[hand]N; +Nergal[]DN$ +.; "
        "+qaqqaru["
        "ground//region]N$qaqqar; +Ukaduha[Cygnus]CN$; +waldu[born]AJ$alid; "
        "+uqququ[tongue-tied]AJ$uqquq",
        "#lem: +sukkuku[deaf]AJ$ +.; agurra[baked brick]N; īmur[see]V; marṣu["
        "patient]N; imât[die]V +.; +kayyānu["
        "constant//normal]AJ$; šanîš[alternatively]AV; amēlu[man]N; ša[who]REL; "
        "u; +hursānu[river "
        "ordeal]N$hursān; +târu[turn//turn back]V$itūra +.",
        "#lem: u; +târu[turn//turning back]V'N$târu; +târu[turn//turning "
        "back]V'N$târa; šalšiš[thirdly]AV; "
        "+arītu[pregnant one]N$ +.; aplu[son]N; !+māru[son]N$; +karāṣu[break "
        "off//breaking off]V'N$; u +.; šanîš["
        "alternatively]AV",
        "#lem: !+māru[son]N$; !+māru[son]N$māri; târu[turning back]'N; +našû["
        "lift//carrying]V'N$ +.; u; "
        "+narkabtu[chariot]N$narkabta; īmur[see]V; marṣu[patient]N; šū[that]IP; "
        "qāt[hand]N; Ištar[1]DN; u",
        "#lem: +narkabtu[chariot]N$; +Narkabtu[Chariot]CN$; Delebat[Venus]CN +.; "
        "+šanîš["
        "otherwise//alternatively]AV$; +narkabtu[chariot]N$; narkabtu[chariot]N; "
        "u; u",
        "#lem: u; Ištar[1]DN; kakkabī[star]N +.; šanîš[alternatively]AV; "
        "narkabtu[chariot]N; narkabtu[chariot]N; "
        "+Delebat[Venus]CN$; +Delebat[Venus]CN$; u",
        "#lem: u; ubû[unit]N; n; n; qû[unit]N; ubû[unit]N; +Ištar[]DN$; Ištar["
        "1]DN +.; +saparru[cart]N$; u",
        "#lem: +saparru[cart]N$saparri; X; +agālu[donkey]N$agallu; +rakāsu["
        "bind//harnessing]V'N$; u; +rakāsu["
        "bind//harnessing]V'N$; +ereqqu[cart]N$; u",
        "#lem: u; +ariktu[length//(a cart)]N$; ša[whose]REL; +mahrātu[front "
        "part]N$mahrātsu; narkabtu[chariot]N; "
        "u[and]CNJ; +warkatu[rear]N$arkassu; u; u +.",
        "#lem: u; u; hīpi[broken place]N; ša[which]REL; n; +umāmu[animal]N$umāma; "
        "ṣandū[yoked]AJ; u",
        "#lem: u; eššu[new]AJ; u +.",
    ],
)
def test_lemma_line_c_type_is_lem_line(line):
    atf_preprocessor = ATFPreprocessor("../logs", 0)

    (
        converted_line,
        c_array,
        c_type,
        c_alter_lemline_at,
    ) = atf_preprocessor.process_line(line)

    assert c_type == "lem_line"
