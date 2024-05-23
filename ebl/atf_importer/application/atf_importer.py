import argparse
import glob
import os
import json
import logging
from pymongo import MongoClient
from typing import Any, Dict, List, TypedDict, Union, TypedDict, Literal
from ebl.atf_importer.application.glossary_parser import (
    GlossaryParser,
    GlossaryParserData,
)
from ebl.atf_importer.domain.atf_preprocessor import AtfPreprocessor
from ebl.fragmentarium.web.dtos import parse_museum_number
from ebl.atf_importer.application.lines_getter import EblLinesGetter
from ebl.atf_importer.application.database_importer import DatabaseImporter


class AtfImporterConfigData(TypedDict):
    STYLES: Dict[str, int]
    POS_TAGS: List[str]
    NOUN_POS_TAGS: List[str]


class AtfImporterConfig:
    config_data: AtfImporterConfigData
    config_path = "ebl/atf_importer/domain/atf_importer_config.json"

    def __init__(self):
        with open(self.config_path, "r") as file:
            self.config_data: AtfImporterConfigData = json.load(file)

    def __getitem__(
        self, item: Literal["STYLES", "POS_TAGS", "NOUN_POS_TAGS"]
    ) -> Union[Dict[str, int], List[str]]:
        return getattr(self.config_data, item)


class AtfImporterArgs(TypedDict):
    input_dir: str
    log_dir: str
    glossary_path: str
    author: str
    style: int


class AtfImporter:
    def __init__(self, database):
        self.database = database
        self.username: str = ""
        self.logger = self.setup_logger()
        self.config = AtfImporterConfig()
        self._ebl_lines_getter = EblLinesGetter(self.database, self.config, self.logger)
        self._database_importer = DatabaseImporter(database, self.logger, self.username)
        self.atf_preprocessor = None
        self.glossary_parser = GlossaryParser()

    def convert_to_ebl_lines(
        self, converted_lines: List[Dict[str, Any]], filename: str
    ) -> Dict[str, List]:
        return self._ebl_lines_getter.convert_to_ebl_lines(converted_lines, filename)

    def setup_logger(self) -> logging.Logger:
        logging.basicConfig(level=logging.DEBUG)
        return logging.getLogger("Atf-Importer")

    def import_into_database(self, ebl_lines: Dict[str, List], filename: str):
        self._database_importer.import_into_database(ebl_lines, filename)

    def parse_glossary(
        self,
        path: str,
    ) -> GlossaryParserData:
        with open(path, "r", encoding="utf8") as file:
            return self.glossary_parser.parse(file)

    def run_importer(self, args: AtfImporterArgs) -> None:
        self.username = args["author"]
        self.atf_preprocessor = AtfPreprocessor(args["log_dir"], args["style"])
        file_paths = glob.glob(os.path.join(args["input_dir"], "*.atf"))
        self.process_files(file_paths, args["glossary_path"])

    def process_files(self, file_paths: List[str], glossary_path: str) -> None:
        glossary_data = self.parse_glossary(glossary_path)
        for filepath in file_paths:
            self._process_file(filepath, glossary_data)

    def _process_file(
        self,
        filepath: str,
        glossary_data: GlossaryParserData,
    ) -> None:
        # ToDo: Fix
        # `GlossaryParserData` goes nowhere. Should probably go to `lemma_lookup`
        filename = os.path.basename(filepath).split(".")[0]
        converted_lines = self.atf_preprocessor.convert_lines(filepath, filename)
        ebl_lines = self.convert_to_ebl_lines(converted_lines, filename)
        self.import_into_database(ebl_lines, filename)

    def cli(self) -> None:
        parser = argparse.ArgumentParser(
            description="Converts ATF files to eBL-ATF standard."
        )
        parser.add_argument(
            "-i", "--input", required=True, help="Path of the input directory."
        )
        parser.add_argument(
            "-l", "--logdir", required=True, help="Path of the log files directory."
        )
        parser.add_argument(
            "-g", "--glossary", required=True, help="Path to the glossary file."
        )
        parser.add_argument(
            "-a",
            "--author",
            required=False,
            help="Name of the author of the imported fragments.",
        )
        parser.add_argument(
            "-s",
            "--style",
            required=False,
            default="Oracc",
            choices=["Oracc", "Other"],
            help="Specify import style.",
        )

        args = parser.parse_args()
        self.run_importer(
            {
                "input_dir": args.input,
                "log_dir": args.logdir,
                "glossary_path": args.glossary,
                "author": args.author,
                "style": args.style,
            }
        )

    @staticmethod
    def main() -> None:
        client = MongoClient(os.getenv("MONGODB_URI"))
        database = client.get_database(os.getenv("MONGODB_DB"))
        importer = AtfImporter(database)
        importer.cli()


if __name__ == "__main__":
    AtfImporter.main()
