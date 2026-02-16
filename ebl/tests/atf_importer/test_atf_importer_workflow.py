import os
from ebl.tests.factories.fragment import FragmentFactory, LemmatizedFragmentFactory
from ebl.fragmentarium.domain.fragment_external_numbers import ExternalNumbers
from ebl.transliteration.domain.museum_number import MuseumNumber
from ebl.fragmentarium.domain.joins import Join, Joins
from ebl.fragmentarium.application.joins_schema import JoinSchema
from ebl.tests.atf_importer.conftest import (
    setup_and_run_importer,
    check_importing_and_logs,
    check_logs,
)


def test_logger_writes_files(fragment_repository, tmp_path):
    museum_number = "X.1"
    atf = f"&P000001 = {museum_number}\n1'. GU₄ 30 ⸢12⸣ [...]"
    fragment_repository.create(FragmentFactory.build(number=MuseumNumber.of("X.1")))
    setup_and_run_importer(atf, tmp_path, fragment_repository)
    assert set(os.listdir(tmp_path / "logs")) == {
        "imported_files.txt",
        "not_imported_files.txt",
        "error_lines.txt",
        "lemmatization_log.txt",
        "unparsable_lines.txt",
    }
    check_importing_and_logs(museum_number, fragment_repository, tmp_path)


def test_find_museum_number_by_cdli_number(fragment_repository, tmp_path, mock_input):
    museum_number = "X.123"
    atf = "&P111111 = XXX\n1'. GU₄ 30 ⸢12⸣ [...]"
    fragment_repository.create(
        FragmentFactory.build(
            number=MuseumNumber.of(museum_number),
            external_numbers=ExternalNumbers(cdli_number="P111111"),
        )
    )
    mock_input([museum_number, "end"])
    setup_and_run_importer(atf, tmp_path, fragment_repository)
    check_importing_and_logs(museum_number, fragment_repository, tmp_path)


def test_find_museum_number_by_traditional_reference(
    fragment_repository, tmp_path, mock_input
):
    museum_number = "X.222"
    test_id = "test reference"
    atf = f"&P000001 = {test_id}\n1. GU₄ 30 ⸢12⸣ [...]"
    fragment_repository.create(
        FragmentFactory.build(
            number=MuseumNumber.of(museum_number), traditional_references=[test_id]
        )
    )
    mock_input([museum_number, "end"])
    setup_and_run_importer(atf, tmp_path, fragment_repository)
    check_importing_and_logs(museum_number, fragment_repository, tmp_path)


def test_museum_number_input_by_user(fragment_repository, tmp_path, mock_input):
    museum_number = "X.2"
    test_id = "test reference"
    atf = f"&P000001 = {test_id}\n1. GU₄ 30 ⸢12⸣ [...]"
    fragment_repository.create(FragmentFactory.build(number=MuseumNumber.of("X.2")))
    responses = mock_input([museum_number, "end"])
    setup_and_run_importer(atf, tmp_path, fragment_repository)
    assert next(responses) == "end"
    check_importing_and_logs(museum_number, fragment_repository, tmp_path)


def test_museum_number_skip_by_user(fragment_repository, tmp_path, mock_input):
    responses = mock_input(["", "end"])
    atf = "&P000001 = test reference\n1. GU₄ 30 ⸢12⸣ [...]"
    setup_and_run_importer(atf, tmp_path, fragment_repository)
    assert next(responses) == "end"
    logs = {
        "imported_files.txt": [""],
        "not_imported_files.txt": [
            "test.atf could not be imported: Museum number not found"
        ],
    }
    check_logs(tmp_path, "", logs)


def test_ask_overwrite_existing_edition(fragment_repository, tmp_path, mock_input):
    museum_number = "X.1"
    atf = f"&P000001 = {museum_number}\n1. GU₄ 30 ⸢12⸣ [...]"
    responses = mock_input(["Y", "end"])
    fragment_repository.create(
        LemmatizedFragmentFactory.build(number=MuseumNumber.of(museum_number))
    )
    setup_and_run_importer(atf, tmp_path, fragment_repository)
    assert next(responses) == "end"
    check_importing_and_logs(museum_number, fragment_repository, tmp_path)


def test_ask_overwrite_existing_edition_cancel(
    fragment_repository, tmp_path, mock_input
):
    museum_number = "X.1"
    atf = f"&P000001 = {museum_number}\n1. GU₄ 30 ⸢12⸣ [...]"
    responses = mock_input(["N", "end"])
    fragment_repository.create(
        LemmatizedFragmentFactory.build(number=MuseumNumber.of(museum_number))
    )
    setup_and_run_importer(atf, tmp_path, fragment_repository)
    assert next(responses) == "end"
    with open(tmp_path / "logs/not_imported_files.txt") as logfile:
        assert (
            "test.atf could not be imported: Edition found, importing cancelled by user"
            in logfile.read()
        )


def test_import_fragment_to_lowest_join(database, fragment_repository, tmp_path):
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
    setup_and_run_importer(atf, tmp_path, fragment_repository)
    check_importing_and_logs(museum_number_join_low, fragment_repository, tmp_path)


def test_import_fragment_correct_parsing_errors(
    fragment_repository, tmp_path, mock_input, capsys
):
    museum_number = "X.2"
    atf = f"&P000001 = {museum_number}\n1. GGG"
    responses = mock_input(["1. GA", "end"])
    fragment_repository.create(
        FragmentFactory.build(number=MuseumNumber.of(museum_number))
    )
    setup_and_run_importer(atf, tmp_path, fragment_repository)
    expected_captured = (
        "Error: Invalid transliteration\n"
        "The following text line cannot be parsed:\n"
        "1. GGG\n"
        "Please input the corrected line, then press enter:\n"
    )
    assert next(responses) == "end"
    assert capsys.readouterr().out == expected_captured
    check_importing_and_logs(museum_number, fragment_repository, tmp_path)


def test_import_fragment_correct_parsing_errors2(
    fragment_repository, tmp_path, mock_input, capsys
):
    museum_number = "X.2"
    atf = f"&P000001 = {museum_number}\n1. " + "{LÚ}ERÍN{ME[Š]}"
    responses = mock_input(["1. EN", "end"])
    fragment_repository.create(
        FragmentFactory.build(number=MuseumNumber.of(museum_number))
    )
    setup_and_run_importer(atf, tmp_path, fragment_repository)
    expected_captured = (
        "Error: \n"
        "The following text line cannot be parsed:\n"
        "1. {LÚ}ERÍN{ME[Š]}\n"
        "Please input the corrected line, then press enter:\n"
    )
    assert next(responses) == "end"
    assert capsys.readouterr().out == expected_captured
    check_importing_and_logs(museum_number, fragment_repository, tmp_path)
