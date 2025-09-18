import os
import zipfile
import tempfile
import builtins
import pytest
from pymongo import MongoClient
from unittest.mock import patch
from ebl.atf_importer.application.atf_importer import AtfImporter
from ebl.tests.factories.fragment import FragmentFactory, LemmatizedFragmentFactory
from ebl.fragmentarium.domain.fragment_external_numbers import ExternalNumbers
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.fragmentarium.domain.joins import Join, Joins
from ebl.fragmentarium.application.joins_schema import JoinSchema
from ebl.tests.atf_importer.test_glossaries_data import GLOSSARY, QPN_GLOSSARY
from itertools import repeat


@pytest.fixture(autouse=True)
def patched_fragment_updater(fragment_updater):
    with patch(
        "ebl.context.Context.get_fragment_updater",
        return_value=fragment_updater,
    ):
        yield


def create_file(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.touch()
    path.write_text(content)


def setup_and_run_importer(
    atf_string,
    tmp_path,
    database,
    fragment_repository,
    glossaries=None,
):
    if not glossaries:
        glossaries = {"akk": "", "qpn": ""}
    atf_importer = AtfImporter(database, fragment_repository)
    create_file(tmp_path / "import/test.atf", atf_string)
    for key in glossaries.keys():
        create_file(tmp_path / f"import/glossary/{key}.glo", glossaries[key])
    atf_importer.run_importer(
        {
            "input_dir": tmp_path / "import",
            "logdir": tmp_path / "logs",
            "glodir": tmp_path / "import/glossary",
            "author": "Test author",
        }
    )


def check_importing_and_logs(museum_number, fragment_repository, tmp_path, logs=None):
    if logs is None:
        logs = {}
    fragment = fragment_repository.query_by_museum_number(
        MuseumNumber.of(museum_number)
    )
    assert str(fragment.number) == museum_number
    check_logs(tmp_path, museum_number, logs)


def check_logs(tmp_path, museum_number, logs):
    for log_filename in os.listdir(tmp_path / "logs"):
        with open(tmp_path / f"logs/{log_filename}") as logfile:
            logfile_content = logfile.read()
            if log_filename in logs.keys():
                check_custom_logs_content(logs, log_filename, logfile_content)
            elif log_filename == "imported_files.txt":
                assert (
                    f"test.atf successfully imported as {museum_number}"
                    in logfile_content
                )
            else:
                assert logfile_content == ""


def check_custom_logs_content(logs, log_filename, logfile_content):
    if logs[log_filename]:
        for log_segment in logs[log_filename]:
            if len(log_segment) > 0:
                assert log_segment in logfile_content
            else:
                assert log_segment == logfile_content


def check_lemmatization(fragment_repository, museum_number, expected_lemmatization):
    fragment = fragment_repository.query_by_museum_number(
        MuseumNumber.of(museum_number)
    )
    lemmatization = [word.unique_lemma for word in fragment.text.lines[0]._content]
    assert lemmatization == expected_lemmatization


@pytest.fixture
def mock_input(monkeypatch):
    def _set_input_responses(responses):
        responses_iter = iter(responses)
        monkeypatch.setattr(builtins, "input", lambda *args: next(responses_iter))
        return responses_iter

    return _set_input_responses


def test_logger_writes_files(database, fragment_repository, tmp_path):
    museum_number = "BM.1"
    atf = f"&P000001 = {museum_number}\n1'. GU₄ 30 ⸢12⸣ [...]"
    fragment_repository.create(FragmentFactory.build(number=MuseumNumber.of("BM.1")))
    setup_and_run_importer(atf, tmp_path, database, fragment_repository)
    assert os.listdir(tmp_path / "logs") == [
        "imported_files.txt",
        "not_imported_files.txt",
        "error_lines.txt",
        "lemmatization_log.txt",
        "unparsable_lines.txt",
    ]
    check_importing_and_logs(museum_number, fragment_repository, tmp_path)


def test_find_museum_number_by_cdli_number(database, fragment_repository, tmp_path):
    museum_number = "BM.123"
    atf = "&P111111 = XXX\n1'. GU₄ 30 ⸢12⸣ [...]"
    fragment_repository.create(
        FragmentFactory.build(
            number=MuseumNumber.of(museum_number),
            external_numbers=ExternalNumbers(cdli_number="P111111"),
        )
    )
    setup_and_run_importer(atf, tmp_path, database, fragment_repository)
    check_importing_and_logs(museum_number, fragment_repository, tmp_path)


def test_find_museum_number_by_traditional_reference(
    database, fragment_repository, tmp_path
):
    museum_number = "BM.222"
    test_id = "test reference"
    atf = f"&P000001 = {test_id}\n1. GU₄ 30 ⸢12⸣ [...]"
    fragment_repository.create(
        FragmentFactory.build(
            number=MuseumNumber.of(museum_number), traditional_references=[test_id]
        )
    )
    setup_and_run_importer(atf, tmp_path, database, fragment_repository)
    check_importing_and_logs(museum_number, fragment_repository, tmp_path)


def test_museum_number_input_by_user(
    database, fragment_repository, tmp_path, mock_input
):
    museum_number = "BM.2"
    test_id = "test reference"
    atf = f"&P000001 = {test_id}\n1. GU₄ 30 ⸢12⸣ [...]"
    fragment_repository.create(FragmentFactory.build(number=MuseumNumber.of("BM.2")))
    responses = mock_input([museum_number, "end"])
    setup_and_run_importer(atf, tmp_path, database, fragment_repository)
    assert next(responses) == "end"
    check_importing_and_logs(museum_number, fragment_repository, tmp_path)


def test_museum_number_skip_by_user(
    database, fragment_repository, tmp_path, mock_input
):
    responses = mock_input(["skip", "end"])
    atf = "&P000001 = test reference\n1. GU₄ 30 ⸢12⸣ [...]"
    setup_and_run_importer(atf, tmp_path, database, fragment_repository)
    assert next(responses) == "end"
    logs = {
        "imported_files.txt": [""],
        "not_imported_files.txt": [
            "test.atf could not be imported: Museum number not found"
        ],
    }
    check_logs(tmp_path, "", logs)


def test_ask_overwrite_existing_edition(
    database, fragment_repository, tmp_path, mock_input
):
    museum_number = "N.1"
    atf = f"&P000001 = {museum_number}\n1. GU₄ 30 ⸢12⸣ [...]"
    responses = mock_input(["Y", "end"])
    fragment_repository.create(
        LemmatizedFragmentFactory.build(number=MuseumNumber.of(museum_number))
    )
    setup_and_run_importer(atf, tmp_path, database, fragment_repository)
    assert next(responses) == "end"
    check_importing_and_logs(museum_number, fragment_repository, tmp_path)


def test_ask_overwrite_existing_edition_cancel(
    database, fragment_repository, tmp_path, mock_input
):
    museum_number = "N.1"
    atf = f"&P000001 = {museum_number}\n1. GU₄ 30 ⸢12⸣ [...]"
    responses = mock_input(["N", "end"])
    fragment_repository.create(
        LemmatizedFragmentFactory.build(number=MuseumNumber.of(museum_number))
    )
    setup_and_run_importer(atf, tmp_path, database, fragment_repository)
    assert next(responses) == "end"
    with open(tmp_path / "logs/not_imported_files.txt") as logfile:
        assert (
            "test.atf could not be imported: Edition found, importing cancelled by user"
            in logfile.read()
        )


def test_import_fragment_to_lowest_join(
    database, fragment_repository, tmp_path, mock_input
):
    museum_number_join_low = "X.1"
    museum_number_join_high = "X.2"
    atf = f"&P000001 = {museum_number_join_high}\n1. LUGAL [x]"
    for number_1, number_2 in [
        (museum_number_join_low, museum_number_join_high),
        (museum_number_join_high, museum_number_join_low),
    ]:
        fragment = FragmentFactory.build(
            number=MuseumNumber.of(number_1),
            joins=Joins(
                ((Join(MuseumNumber.of(number_2), is_in_fragmentarium=True),),),
            ),
        )
        fragment_repository.create(fragment)

    database["joins"].insert_one(
        {
            "fragments": [
                {
                    **JoinSchema(exclude=["is_in_fragmentarium"]).dump(
                        Join(MuseumNumber.of(museum_number))
                    ),
                    "group": index,
                }
                for index, museum_number in enumerate(
                    [museum_number_join_low, museum_number_join_high]
                )
            ]
        }
    )
    setup_and_run_importer(atf, tmp_path, database, fragment_repository)
    check_importing_and_logs(museum_number_join_low, fragment_repository, tmp_path)


def test_import_fragment_correct_parsing_errors(
    database, fragment_repository, tmp_path, mock_input, capsys
):
    museum_number = "H.2"
    atf = f"&P000001 = {museum_number}\n1. GGG"
    responses = mock_input(["1. GA", "end"])
    fragment_repository.create(
        FragmentFactory.build(number=MuseumNumber.of(museum_number))
    )
    setup_and_run_importer(atf, tmp_path, database, fragment_repository)
    expected_captured = (
        "Error: Invalid transliteration \n"
        "The following text line cannot be parsed:\n"
        "1. GGG\n"
        "Please input the corrected line, then press enter:\n"
    )
    assert next(responses) == "end"
    assert capsys.readouterr().out == expected_captured
    check_importing_and_logs(museum_number, fragment_repository, tmp_path)


def test_lemmatization(fragment_repository, tmp_path):
    client = MongoClient(os.environ["MONGODB_URI"])
    database = client.get_database(os.environ.get("MONGODB_DB"))
    museum_number = "BM.17"
    fragment_repository.create(
        FragmentFactory.build(number=MuseumNumber.of(museum_number))
    )
    atf = (
        f"&P000001 = {museum_number}\n"
        "64. * ina {iti}ZIZ₂ U₄ 14.KAM [AN.KU₁₀] 30 GAR-ma <<ina>> KAN₅-su KU₄ DINGIR GU₇\n"
        "#lem: šumma[if]CNJ; ina[in]PRP; Šabāṭu[Month XI]MN; ūmu[day]N; n; antallû[eclipse]N; Sîn["
        "moon]N; šakānu[take place]V; adru[dark]AV; erēbu[enter]V; ilu["
        "god]N; akālu[eat]V"
    )

    setup_and_run_importer(
        atf,
        tmp_path,
        database,
        fragment_repository,
        {"akk": GLOSSARY, "qpn": QPN_GLOSSARY},
    )
    check_importing_and_logs(museum_number, fragment_repository, tmp_path)
    expected_lemmatization = [
        ("šumma I",),
        ("ina I",),
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
    client = MongoClient(os.environ["MONGODB_URI"])
    database = client.get_database(os.environ.get("MONGODB_DB"))
    museum_number = "BM.89"
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
        database,
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


def test_lemmatization_missing_lemmas(fragment_repository, tmp_path, mock_input):
    client = MongoClient(os.environ["MONGODB_URI"])
    database = client.get_database(os.environ.get("MONGODB_DB"))
    museum_number = "BM.5"
    fragment_repository.create(
        FragmentFactory.build(number=MuseumNumber.of(museum_number))
    )
    atf = f"&P000003 = {museum_number}\n64. * LU2 LUGAL\n#lem: šumma[if]CNJ; awīlu[man]N; šarru[king]N"
    responses = mock_input(["amēlu I", "awīlu I", "", "end"])
    setup_and_run_importer(
        atf,
        tmp_path,
        database,
        fragment_repository,
        {"akk": GLOSSARY, "qpn": QPN_GLOSSARY},
    )
    logs = {
        "lemmatization_log.txt": [
            "Incompatible lemmatization: No eBL word found for lemma 'awīlu' and guideword 'man'",
            "Manual lemmatization: eBL lemma 'awīlu I' entered by user",
            "Incompatible lemmatization: No citation form or guideword (by sense) found in the glossary for 'šarru'",
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
    client = MongoClient(os.environ["MONGODB_URI"])
    database = client.get_database(os.environ.get("MONGODB_DB"))
    museum_number = "BM.17"
    fragment_repository.create(
        FragmentFactory.build(number=MuseumNumber.of(museum_number))
    )
    atf = (
        f"&P000001 = {museum_number}\n"
        "10. AN KI NUNDUN GÍR.TAB UŠ-id ana MÚL SA₄\n"
        "#lem: Ṣalbaṭānu[Mars]CN; erṣētu[area]N'; šaptu[lip]N$; Zuqiqīpu[Scorpio]CN; "
        "emēdu[lean on//be at a stationary point]V'V$nenmudu; "
        "ana[to]PRP; kakkabu[star]N$; nebû[shining//bright]AJ'AJ$"
    )
    responses = mock_input(
        [
            "ṣalbatānu I",
            "erṣetu I",
            "šaptu I",
            "zuqiqīpu I",
            "emēdu I",
            "ana I",
            "kakkabu I",
            "nebû I",
            "end",
        ]
    )
    setup_and_run_importer(
        atf,
        tmp_path,
        database,
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
        ("ṣalbatānu I",),
        ("erṣetu I",),
        ("šaptu I",),
        ("zuqiqīpu I",),
        ("emēdu I",),
        ("ana I",),
        ("kakkabu I",),
        ("nebû I",),
    ]
    check_lemmatization(fragment_repository, museum_number, expected_lemmatization)


# ToDo: Debug
# Works when:
# &X103813 = BM.17
#
# Does not work when:
# &X103813 = AD -381C

ATF = """&X103813 = AD381C
#project: adsd/adart1
#atf: use unicode
#atf: lang akk
#atf: use math
#atf: use legacy
@obverse
1. [MU 23.KÁM {m}...]-šú šá {m}ar-tak-šat-su LUGAL MU-šú SA₄-ú DU₆ 1 [...]
#lem: šattu[year]N; n; u; ša[who]REL; Artaxerxes[Artaxerxes]RN; šarru[king]N; šumšu[name]N; nabû[named]AJ; Tašrītu[Month VII]MN; n; u

2. [...] ana ULÙ u MAR ŠUR UD.DA-su ina KI IGI GE₆ 6 ina ZALÁG dele-bat e S[A₄-šá-ABSIN ...]
#lem: u; ana[to]PRP; šūtu[south]N; u[and]CNJ; amurru[west]N; zanānu[flash]V; ṣētu[bright light]N; ina[on]PRP; erṣētu[ground]N; amāru[see]V; mūšu[night]N; n; ina[in]PRP; nūru[last part of the night]N; Dilbat[Venus]CN; eli[above]PRP; SA₄-šá-ABSIN[α Virginis]CN; u

3. [... GE₆ 9 ... sin] ár MÚL-ár-šá-SUHUR-MÁŠ 2/3 KÙŠ ana SI-šú šá SI GIN [...]
#lem: u; mūšu[night]N; n; u; Sîn[moon]N; warki[behind]PRP; MÚL-ár-šá-SUHUR-MÁŠ[δ Capricorni]CN; n; ammatu[unit]N; ana[to]PRP; qarnu[horn]N$qarnišu; ša[which]REL; ištānu[northern]AJ; alāku[go]V; u

4. [...] ⸢GE₆⸣ 17 ina ZALÁG sin ina IGI ŠUR-GIGIR-šá-SI 1 ⸢2/3⸣ [KÙŠ ...]
#lem: u; mūšu[night]N; n; ina[in]PRP; nūru[last part of the night]N; Sîn[moon]N; ina[in]PRP; pān[front]N; ŠUR-GIGIR-šá-SI[β Tauri]CN$; n; n; ammatu[unit]N; u

5. [...] ⸢x x x x x x⸣ [...]
#lem: u; u; u; u; u; u; u; u

@reverse
1'. [... sin T]ÙR NIGÍN AN ⸢UTAH⸣ ⸢x šamáš? TÙR NIGÍN⸣ ma-diš iq-⸢tur₇⸣ [...]
#lem: u; Sîn[moon]N; tarbaṣa[halo]N; lawi[surrounded (with)]AJ; šamû[rain]N; natāku[drip]V; u; šamšu[sun]N; tarbaṣa[halo]N; lawi[surrounded (with)]AJ; mādiš[very]AV; qatāru[billow]V; u

2'. [... GENNA ... MÚ]L-ár-šá-ALLA-šá-ULÙ 6 SI LÁL ITU BI KI.LAM še-i[m ...]
#lem: u; Kayyamānu[Saturn]CN; u; MÚL-ár-šá-ALLA-šá-ULÙ[δ Cancri]CN; n; ubānu[finger]N; alālu[balance]V; warhu[month]N; šū[that]'DP; mahīru[price (equivalent)]N; šeʾu[barley]N; u

3'. [...] ⸢x⸣ i-nu-šú MÚL.BABBAR ina UR.A dele-bat u GU₄.UD ina GU₄.AN GENNA ina ALLA A[N ...]
#lem: u; u; inūšu[at that time]AV; Kakkabu-peṣû[Jupiter]CN; ina[in//in]PRP'PRP; Nēšu[Leo]CN; Dilbat[Venus]CN; u[and]CNJ; Šihṭu[Mercury]CN; ina[in]PRP; Zappu[Taurus]CN; Kayyamānu[Saturn]CN; ina[in]PRP; Alluttu[Cancer]CN; Ṣalbaṭānu[Mars]CN; u

4'. [...] KUR sa-mi-né-e URU SIG-ú šá KUR ku-up-ru šá ana DÙ [...]
#lem: u; mātu[land]N; Saminê[Saminê]SN$; ālu[city]N; wēdû[famous]AJ; ša[of]DET; mātu[land]N; Kupru[Kupru]GN$; ša[which]REL; ana[for]PRP; epēšu[do//make]V'V$; u

5'. [...] ⸢x⸣ su-un-du KUR ia-a-mu-un-ia-am-mu šá LUGAL ⸢DÙ⸣-u[š ...]
#lem: u; u; X; mātu[land]N; Iamun-Yammu[Ionian Sea (?)]WN$; ša[which]REL; šarru[king]N; epēšu[do]V; u

@top
1. [BAR] 1 24.30 na DIR KALAG-ma sin NU IGI
#lem: Nisannu[Month I]MN; n; n; na₁[sunset to moonset]N; erpetu[cloud]N; dannu[dense]AJ; Sîn[moon]N; ul[not]MOD; amāru[see]V

2. EN.NUN šá gi-né-e šá TA DU₆ EN TIL DIR.ŠE [...]
#lem: naṣāru[observation]'N; ša[which]REL; ginê[regularity]N; ša[which]REL; ištu[from]PRP; Tašrītu[Month VII]MN; adi[until]PRP; qītu[end]N; Addāru_Šanû[(Intercalary) Month XII₂]MN; u


@translation labeled en project

@obverse

@(o 1) [Year 24@sup{?} of ...x]šu who is called king Artaxerxes. Month VII, the 1st (of which followed the 30th of the prededing month); ... [...]

@(o 2) [... a shooting star@sup{?}] flashed to the south-west; ist light was seen on the ground. Night of the 6th, last part of the night, Venus was above α Vir[ginis ...]

@(o 3) [... the moon was] 2/3 cubit behind δ Capricorni, it was set to its northern horn [...]

@(o 4) [...] Night of the 17th, last part of the night, the moon was 1 + x cubits in front of ζ Tauri [...]

@(o 5) [...] ... Night@sup{?} of the 19th@sup{?}, last part of the night, the moon was in front@sup{?} of ... [...]

@reverse

@(r 1') [...] was surrounded by a halo; rain shower. The xth, the sun was surrounded by a halo, it billowed very much. [...]

@(r 2') [...] was balanced 6 fingers [above/below] δ Cancri. That month, the quivalent (of 1 shekel of silver) was: barley, [...]

@(r 3') [... mi]nas. At that time, Jupiter was in Leo; Venus and Mercury were in Taurus;

@(r 4') [...] the land Saminê, a famous city of the land Kupru, which for making [...]

@(r 5') [...]sundu of the land Iamuniammu which the king made [...]

@top

@(t.e. 1) [Month I], the 1st (of which followed the 30th of the preceding month); sunset to moonset: 24° 30'; dense clouds so that I did not see the moon.

@(t.e. 2) Diary from month VII to the end of month XII2 [...]"""

# ToDo:
# Continue from here
# Tasks:
# 1. Fix primed lines in translation (s. test_atf_preprocessor, translation C & atf_indexing_visitor)
# 2. Test & merge the markup additions branch
# 3. Consider a solution for cases like
# "7'. 12 DIR AN ZA GE₆ 13 13 DIR AN ZA GE[₆ ...]\n"
# S. the test below. The issue is with `GE[₆ `.
# The line is parsed as `translation_line`, but should be a parsing error for manual fix.
# This should be tested as well.

def test_manual_lemmatization_extended2(fragment_repository, tmp_path, mock_input):
    client = MongoClient(os.environ["MONGODB_URI"])
    database = client.get_database(os.environ.get("MONGODB_DB"))
    museum_number = "BM.17"
    fragment_repository.create(
        FragmentFactory.build(number=MuseumNumber.of(museum_number))
    )
    atf = (
        f"&P000001 = {museum_number}\n"
        "7'. 12 DIR AN ZA GE₆ 13 13 DIR AN ZA GE[₆ ...]\n"
        "#lem: n; erpetu[cloud]N; šamû[sky]N; ṣabātu[cover (the sky)]V; mūšu[night]N; n; n; erpetu[cloud]N; šamû[sky]N; ṣabātu[cover (the sky)]V; mūšu[night]N; u"
    )
    # atf = ATF
    mock_input(repeat(""))
    setup_and_run_importer(
        atf,
        tmp_path,
        database,
        fragment_repository,
        {"akk": GLOSSARY, "qpn": QPN_GLOSSARY},
    )


# @pytest.mark.skip(reason="heavy test")
def test_atf_importer(fragment_repository, mock_input):
    client = MongoClient(os.environ["MONGODB_URI"])
    database = client.get_database(os.environ.get("MONGODB_DB"))
    atf_importer = AtfImporter(database, fragment_repository)
    archive = zipfile.ZipFile(
        "ebl/tests/atf_importer/test_data3.zip"  # ToDo: Change to "ebl/tests/atf_importer/test_data3.zip"
    )  # ToDo: Check `test_data2`
    mock_input(repeat(""))
    with tempfile.TemporaryDirectory() as tempdir:
        data_path = f"{tempdir}/test_atf_import_data"
        archive.extractall(data_path)
        for museum_number in [
            "BM.32312",
            "VAT.4956",
            "W.20030.142",
            "VAT.5047",
            "VAT.4936",
            "VAT.4924",
            "BM.47735",
            "BM.34634",
            "BM.34638",
            "BM.47725",
            "BM.34987",
            "BM.45816",
            "BM.46009",
            "BM.35377",
            "BM.35195",
            "BM.32333",
            "BM.34642",
            "BM.45673",
            "BM.34792",
            "BM.36622",
            "BM.35212",
            "BM.33759",
            "BM.36036",
        ]:
            fragment_repository.create(
                FragmentFactory.build(number=MuseumNumber.of(museum_number))
            )
        for dir in os.listdir(data_path):
            glossary_path = f"{data_path}/{dir}"  # f"{data_path}"
            atf_dir_path = f"{data_path}/{dir}/00atf"  # f"{data_path}"
            logdir_path = f"{data_path}/logs/{dir}"
            print(f"Testing import of atf data in {atf_dir_path}")
            # print("Running", " ".join(command))
            atf_importer.run_importer(
                {
                    "input_dir": atf_dir_path,
                    "logdir": logdir_path,
                    "glodir": glossary_path,
                    "author": "Test author",
                }
            )


"""
def test_atf_importer(database, fragment_repository):
    # Test bulk import.
    # importer_path = "ebl/atf_importer/application/atf_importer.py"
    atf_importer = AtfImporter(database)
    archive = zipfile.ZipFile("ebl/tests/atf_importer/test_data.zip")
    with tempfile.TemporaryDirectory() as tempdir:
        data_path = f"{tempdir}/test_atf_import_data"
        archive.extractall(data_path)
        for dir in os.listdir(data_path):
            glossary_akk_path = f"{data_path}/{dir}/akk.glo"
            # glossary_qpn_path = f"{data_path}/{dir}/qpn.glo"
            atf_dir_path = f"{data_path}/{dir}/00atf"
            logdir_path = f"{data_path}/logs/{dir}"
            print(f"Testing import of atf data in {atf_dir_path}")
            # print("Running", " ".join(command))
            atf_importer.run_importer(
                {
                    "input_dir": atf_dir_path,
                    "logdir": logdir_path,
                    "glodir": glossary_akk_path,
                    "author": "Test author",
                }
            )

            '''
            command = [
                "python",
                "run",
                importer_path,
                "-i",
                atf_dir_path,
                "-l",
                logdir_path,
                "-g",
                glossary_akk_path,
                "-a",
                "Test author",
            ]
            '''

            # result = subprocess.run(
            #    command,
            #    shell=True,
            #    capture_output=True,
            # )
            # print(result.stdout)
            # self.assertIn("expected out", result.stdout)
            # filenames = [
            #    filename for filename in os.listdir(atf_path) if ".atf" in filename
            # ]
            # for filename in filenames:
            #    print(f"{atf_path}/{filename}")
"""
