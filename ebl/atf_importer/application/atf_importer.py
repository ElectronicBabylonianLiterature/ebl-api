import argparse
import glob
import os
import logging
from pymongo import MongoClient
from typing import Any, Dict, List, TypedDict, Optional
from ebl.atf_importer.application.glossary_parser import (
    GlossaryParser,
    GlossaryParserData,
)
from ebl.atf_importer.domain.atf_preprocessor import AtfPreprocessor
from ebl.atf_importer.application.lines_getter import EblLinesGetter
from ebl.atf_importer.application.database_importer import DatabaseImporter
from ebl.atf_importer.application.atf_importer_config import AtfImporterConfig


class AtfImporterArgs(TypedDict):
    input_dir: str
    logdir: str
    glossary_path: str
    author: str
    style: int


class Logger:
    def __init__(self, logdir: Optional[str] = "atf_importer_logs/"):
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger("Atf-Importer")
        self.logdir = logdir
        self.imported: List[str] = []
        self.not_imported: List[str] = []
        self.failed: List[str] = []
        self.error_lines: List[str] = []
        self.success: List[str] = []

    def write_logs(self):
        log_sets = [
            {"filename": "not_lemmatized", "data": self.not_lemmatized},
            {"filename": "error_lines", "data": self.error_lines},
            {"filename": "not_imported", "data": self.failed},
            {"filename": "imported", "data": self.success},
        ]
        for log_data in log_sets:
            self._write_log(log_data["filename"], log_data["data"])

    def _write_log(self, filename: str, data: List[str]) -> None:
        with open(f"{self.logdir}{filename}.txt", "w", encoding="utf8") as outputfile:
            for line in data:
                outputfile.write(line + "\n")


class AtfImporter:
    def __init__(self, database) -> None:
        self.database = database
        self.username: str = ""
        self.setup_logger()
        self.config = AtfImporterConfig().config_data
        self._database_importer = DatabaseImporter(database, self.logger, self.username)
        self.atf_preprocessor = None
        self.glossary_parser = GlossaryParser(self.config)
        self._ebl_lines_getter = None

    def convert_to_ebl_lines(
        self, converted_lines: List[Dict[str, Any]], filename: str
    ) -> Dict[str, List]:
        ebl_lines_getter = getattr(self, "_ebl_lines_getter", None)
        if ebl_lines_getter:
            return ebl_lines_getter.convert_to_ebl_lines(converted_lines, filename)
        else:
            return {}

    def setup_logger(self) -> None:
        self.logger = Logger()

    def setup_lines_getter(self, glossary_path: str) -> None:
        self._ebl_lines_getter = EblLinesGetter(
            self.database, self.config, self.logger, self.parse_glossary(glossary_path)
        )

    def import_into_database(self, ebl_lines: Dict[str, List], filename: str) -> None:
        self._database_importer.import_into_database(ebl_lines, filename)

    def parse_glossary(
        self,
        path: str,
    ) -> GlossaryParserData:
        with open(path, "r", encoding="utf8") as file:
            return self.glossary_parser.parse(file)

    def run_importer(self, args: AtfImporterArgs) -> None:
        self.setup_lines_getter(args["glossary_path"])
        self.username = args["author"]
        self.atf_preprocessor = AtfPreprocessor(args["logdir"], args["style"])
        file_paths = glob.glob(os.path.join(args["input_dir"], "*.atf"))
        self._process_files(file_paths)
        if args["logdir"]:
            self.logger.logdir = args["logdir"]
            self.logger.write_logs()

    def _process_files(self, file_paths: List[str]) -> None:
        for filepath in file_paths:
            self._process_file(filepath)

    def _process_file(self, filepath: str) -> None:
        filename = os.path.basename(filepath).split(".")[0]
        converted_lines = self.atf_preprocessor.convert_lines(filepath, filename)
        ebl_lines = self.convert_to_ebl_lines(converted_lines, filename)
        self.import_into_database(ebl_lines, filename)

    def cli(self) -> None:
        parser = argparse.ArgumentParser(
            description="Converts ATF files to eBL-ATF standard."
        )

        for arg in self.config["CLI_ARGS"]:
            parser.add_argument(*arg["flags"], *arg["kwargs"])

        args = parser.parse_args()
        self.run_importer(
            {
                "input_dir": args.input,
                "logdir": args.logdir,
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
