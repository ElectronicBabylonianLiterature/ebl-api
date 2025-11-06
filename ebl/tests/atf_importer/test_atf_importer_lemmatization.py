from itertools import repeat
from ebl.tests.factories.fragment import FragmentFactory
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.tests.atf_importer.test_glossaries_data import GLOSSARY, QPN_GLOSSARY
from ebl.transliteration.domain.text import (
    SurfaceAtLine,
    ColumnAtLine,
    TextLine,
    TranslationLine,
)
from ebl.tests.atf_importer.conftest import (
    setup_and_run_importer,
    check_importing_and_logs,
    check_lemmatization,
)


def test_lemmatization(fragment_repository, tmp_path):
    museum_number = "X.17"
    fragment_repository.create(
        FragmentFactory.build(number=MuseumNumber.of(museum_number))
    )
    atf = (
        f"&P000001 = {museum_number}\n"
        "64. [...] * ina [...] {iti}ZIZ₂ U₄ 14.KAM [AN.KU₁₀] 30 GAR-ma <<ina>> KAN₅-su KU₄ DINGIR GU₇\n"
        "#lem: u; šumma[if]CNJ; ina[in]PRP; u; Šabāṭu[Month XI]MN; ūmu[day]N; n; antallû[eclipse]N; Sîn["
        "moon]N; šakānu[take place]V; adru[dark]AV; erēbu[enter]V; ilu["
        "god]N; akālu[eat]V"
    )

    setup_and_run_importer(
        atf,
        tmp_path,
        fragment_repository,
        {"akk": GLOSSARY, "qpn": QPN_GLOSSARY},
    )
    check_importing_and_logs(museum_number, fragment_repository, tmp_path)
    expected_lemmatization = [
        (),
        ("šumma I",),
        ("ina I",),
        (),
        ("Šabāṭu I",),
        ("ūmu I",),
        (),
        ("antalû I",),
        ("Sîn I",),
        ("šakānu I",),
        (),
        ("adru I",),
        ("erēbu I",),
        ("ilu I",),
        ("akālu I",),
    ]
    check_lemmatization(fragment_repository, museum_number, expected_lemmatization)


def test_lemmatization_with_removal(fragment_repository, tmp_path):
    museum_number = "X.89"
    fragment_repository.create(
        FragmentFactory.build(number=MuseumNumber.of(museum_number))
    )
    atf = (
        f"&P000001 = {museum_number}\n"
        "64. * <<ina>> ina <<{iti}ZIZ₂ A U₄>> <<A>> {<<iti>>.iti}<<A>>.ZIZ₂.<<A>> U₄ 14.KAM\n"
        "#lem: šumma[if]CNJ; ina[in]PRP; Šabāṭu[Month XI]MN; ūmu[day]N; n"
    )
    setup_and_run_importer(
        atf,
        tmp_path,
        fragment_repository,
        {"akk": GLOSSARY, "qpn": QPN_GLOSSARY},
    )
    check_importing_and_logs(museum_number, fragment_repository, tmp_path)
    expected_lemmatization = [
        ("šumma I",),
        (),
        ("ina I",),
        (),
        (),
        (),
        (),
        ("Šabāṭu I",),
        ("ūmu I",),
        (),
    ]
    check_lemmatization(fragment_repository, museum_number, expected_lemmatization)


def test_lemmatization_with_removal2(fragment_repository, tmp_path, mock_input):
    museum_number = "X.819"
    fragment_repository.create(
        FragmentFactory.build(number=MuseumNumber.of(museum_number))
    )
    atf = f"&P000001 = {museum_number}\n14. 1 KUŠ₃ <<x>> MULₓ(AB₂)\n#lem: n; ammatu[unit]N; kakkabu[star]N"
    responses = mock_input(["ammatu I", "kakkabu I", "end"])
    setup_and_run_importer(
        atf,
        tmp_path,
        fragment_repository,
        {"akk": GLOSSARY, "qpn": QPN_GLOSSARY},
    )
    logs = {
        "lemmatization_log.txt": [
            "Incompatible lemmatization: No citation form and guideword (by sense) found in the glossary for 'ammatu'",
            "Incompatible lemmatization: No eBL word found for lemma 'ammatu' and guideword 'unit'",
            "Manual lemmatization: eBL lemma 'ammatu I' entered by user",
            "Incompatible lemmatization: No citation form and guideword (by sense) found in the glossary for 'kakkabu'",
            "Incompatible lemmatization: No eBL word found for lemma 'kakkabu' and guideword 'star'",
            "Manual lemmatization: eBL lemma 'kakkabu I' entered by user",
        ]
    }
    check_importing_and_logs(museum_number, fragment_repository, tmp_path, logs)
    assert next(responses) == "end"
    expected_lemmatization = [
        (),
        ("ammatu I",),
        (),
        ("kakkabu I",),
    ]
    check_lemmatization(fragment_repository, museum_number, expected_lemmatization)


def test_lemmatization_with_tabulation(fragment_repository, tmp_path):
    museum_number = "X.11"
    fragment_repository.create(
        FragmentFactory.build(number=MuseumNumber.of(museum_number))
    )
    atf = f"&P000001 = {museum_number}\n2. ($indented$) ina [...]\n#lem: ina[in]PRP; u"
    setup_and_run_importer(
        atf,
        tmp_path,
        fragment_repository,
        {"akk": GLOSSARY, "qpn": QPN_GLOSSARY},
    )
    check_importing_and_logs(museum_number, fragment_repository, tmp_path)
    expected_lemmatization = [
        ("ina I",),
        (),
    ]
    check_lemmatization(fragment_repository, museum_number, expected_lemmatization)


def test_problematic_lemmatization(fragment_repository, tmp_path):
    museum_number = "X.111"
    fragment_repository.create(
        FragmentFactory.build(number=MuseumNumber.of(museum_number))
    )
    atf = f"&P000001 = {museum_number}\n5. [...] ⸢x⸣ TÙR NIGÍN\n#lem: u; u; tarbaṣa[halo]N; lawi[surrounded (with)]AJ"
    setup_and_run_importer(
        atf,
        tmp_path,
        fragment_repository,
        {"akk": GLOSSARY, "qpn": QPN_GLOSSARY},
    )
    check_importing_and_logs(museum_number, fragment_repository, tmp_path)
    expected_lemmatization = [
        (),
        (),
        ("tarbaṣu I",),
        ("lawû I",),
    ]
    check_lemmatization(fragment_repository, museum_number, expected_lemmatization)


def test_lemmatization_ambiguity(fragment_repository, tmp_path):
    museum_number = "X.899"
    fragment_repository.create(
        FragmentFactory.build(number=MuseumNumber.of(museum_number))
    )
    atf = f"&P000001 = {museum_number}\n8. ŠÚ\n#lem: rabû[set]V$"
    setup_and_run_importer(
        atf,
        tmp_path,
        fragment_repository,
        {"akk": GLOSSARY, "qpn": QPN_GLOSSARY},
    )
    check_importing_and_logs(museum_number, fragment_repository, tmp_path)
    expected_lemmatization = [
        ("rabû III",),
    ]
    check_lemmatization(fragment_repository, museum_number, expected_lemmatization)


def test_lemmatization_missing_lemmas(fragment_repository, tmp_path, mock_input):
    museum_number = "X.5"
    fragment_repository.create(
        FragmentFactory.build(number=MuseumNumber.of(museum_number))
    )
    atf = f"&P000003 = {museum_number}\n64. * LU2 LUGAL\n#lem: šumma[if]CNJ; awīlu[man]N; šarru[king]N"
    responses = mock_input(["amēlu I", "awīlu I", "", "end"])
    setup_and_run_importer(
        atf,
        tmp_path,
        fragment_repository,
        {"akk": GLOSSARY, "qpn": QPN_GLOSSARY},
    )
    logs = {
        "lemmatization_log.txt": [
            "Incompatible lemmatization: No eBL word found for lemma 'awīlu' and guideword 'man'",
            "Manual lemmatization: eBL lemma 'awīlu I' entered by user",
            "Incompatible lemmatization: No citation form and guideword (by sense) found in the glossary for 'šarru'",
            "Incompatible lemmatization: No eBL word found for lemma 'šarru' and guideword 'king'",
        ]
    }
    check_importing_and_logs(museum_number, fragment_repository, tmp_path, logs)
    assert next(responses) == "end"
    expected_lemmatization = [
        ("šumma I",),
        ("awīlu I",),
        (),
    ]
    check_lemmatization(fragment_repository, museum_number, expected_lemmatization)


def test_manual_lemmatization_extended(fragment_repository, tmp_path, mock_input):
    museum_number = "X.17"
    fragment_repository.create(
        FragmentFactory.build(number=MuseumNumber.of(museum_number))
    )
    atf = (
        f"&P000001 = {museum_number}\n"
        "10. EN AN KI NUNDUN GÍR.TAB UŠ-id ana MÚL SA₄ GUR? NIM-a\n"
        "#lem: Bēl[Bēl]DN$; Ṣalbaṭānu[Mars]CN; erṣētu[area]N'; šaptu[lip]N$; Zuqiqīpu[Scorpio]CN; "
        "emēdu[lean on//be at a stationary point]V'V$nenmudu; "
        "ana[to]PRP; kakkabu[star]N$; nebû[shining//bright]AJ'AJ$; "
        "baʾil[bright]AJ; šaqâ[high]AJ"
    )
    responses = mock_input(
        [
            "ṣalbatānu I",
            "erṣetu I",
            "šaptu I",
            "emēdu I",
            "ana I",
            "kakkabu I",
            "nebû I",
            "ba'ālu I",
            "šaqû II",
            "end",
        ]
    )
    setup_and_run_importer(
        atf,
        tmp_path,
        fragment_repository,
        {"akk": GLOSSARY, "qpn": QPN_GLOSSARY},
    )
    check_importing_and_logs(
        museum_number,
        fragment_repository,
        tmp_path,
        logs={"lemmatization_log.txt": None},
    )
    assert next(responses) == "end"
    expected_lemmatization = [
        ("Bel I",),
        ("ṣalbatānu I",),
        ("erṣetu I",),
        ("šaptu I",),
        ("zuqiqīpu I",),
        ("emēdu I",),
        ("ana I",),
        ("kakkabu I",),
        ("nebû I",),
        ("ba'ālu I",),
        ("šaqû II",),
    ]
    check_lemmatization(fragment_repository, museum_number, expected_lemmatization)


def test_lemmatization_tokens_length_mismatch(
    fragment_repository, tmp_path, mock_input
):
    museum_number = "X.99"
    fragment_repository.create(
        FragmentFactory.build(number=MuseumNumber.of(museum_number))
    )
    atf = (
        f"&P000001 = {museum_number}\n"
        "1. [...]⸢x x⸣ ina MÚL\n"
        "#lem: u; u; ina[in]PRP; kakkabu[star]N"
    )
    responses = mock_input(
        ["#lem: u; u; u; ina[in]PRP; kakkabu[star]N", "kakkabu I", "end"]
    )
    setup_and_run_importer(
        atf,
        tmp_path,
        fragment_repository,
        {"akk": GLOSSARY, "qpn": QPN_GLOSSARY},
    )
    logs = {
        "lemmatization_log.txt": [
            "In `test.atf`: The lemmatization of the following line:\n"
            "1. [...] x# x# ina MUL₂\n"
            "does not match its length. Lemmatization:\n"
            "#lem: u; u; ina[in]PRP; kakkabu[star]N",
        ]
    }
    assert next(responses) == "end"
    check_importing_and_logs(museum_number, fragment_repository, tmp_path, logs)
    expected_lemmatization = [
        (),
        (),
        (),
        ("ina I",),
        ("kakkabu I",),
    ]
    check_lemmatization(fragment_repository, museum_number, expected_lemmatization)


def test_lemmatized_and_translated(fragment_repository, tmp_path, mock_input):
    museum_number = "X.17"
    fragment_repository.create(
        FragmentFactory.build(number=MuseumNumber.of(museum_number))
    )
    atf = (
        f"&P000001 = {museum_number}\n"
        "@obverse\n"
        "@column\n"
        "1. [...] sin\n"
        "#lem: u; Sîn[moon]N\n\n"
        "@translation labeled en project\n\n"
        "@obverse\n"
        "@column\n"
        "@(o i 1) [Month I, ...,] the moon."
    )
    mock_input(repeat(""))
    setup_and_run_importer(
        atf,
        tmp_path,
        fragment_repository,
        {"akk": GLOSSARY, "qpn": QPN_GLOSSARY},
    )
    check_importing_and_logs(museum_number, fragment_repository, tmp_path)
    check_lemmatization(fragment_repository, museum_number, [(), ("Sîn I",)])
    fragment = fragment_repository.query_by_museum_number(
        MuseumNumber.of(museum_number)
    )
    expected_types = [SurfaceAtLine, ColumnAtLine, TextLine, TranslationLine]
    assert len(fragment.text.lines) == len(expected_types)
    for line, expected_instance in zip(
        fragment.text.lines,
        expected_types,
    ):
        assert isinstance(line, expected_instance) is True
