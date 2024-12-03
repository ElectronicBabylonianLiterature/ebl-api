import argparse
import glob
import os
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
from ebl.atf_importer.application.logger import Logger
from ebl.atf_importer.domain.atf_preprocessor_util import Util


class AtfImporterArgs(TypedDict):
    input_dir: str
    logdir: str
    glossary_path: str
    author: str
    style: int = 0


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

    def setup_logger(self, logdir: Optional[str] = None) -> None:
        self.logger = Logger(logdir)

    def setup_lines_getter(self, glossary_path: str) -> None:
        self._ebl_lines_getter = EblLinesGetter(
            self.database, self.config, self.logger, self.parse_glossary(glossary_path)
        )

    def import_into_database(self, ebl_lines: Dict[str, List], filename: str) -> None:
        try:
            self._database_importer.import_into_database(ebl_lines, filename)
        except Exception as e:
            self.logger.exception(e)

    def parse_glossary(
        self,
        path: str,
    ) -> GlossaryParserData:
        with open(path, "r", encoding="utf8") as file:
            return self.glossary_parser.parse(file)

    def run_importer(self, args: AtfImporterArgs) -> None:
        if args["logdir"]:
            self.setup_logger(args["logdir"])
        self.setup_lines_getter(args["glossary_path"])
        self.username = args["author"]
        self.atf_preprocessor = AtfPreprocessor(args["logdir"], args["style"])
        file_paths = glob.glob(os.path.join(args["input_dir"], "*.atf"))
        self._process_files(file_paths, args)
        self.logger.write_logs()

    def _process_files(self, file_paths: List[str], args: AtfImporterArgs) -> None:
        for filepath in file_paths:
            self._process_file(filepath, args)

    def _process_file(self, filepath: str, args: AtfImporterArgs) -> None:
        filename = os.path.basename(filepath).split(".")[0]
        style_name = self.config["STYLES"][str(int(args["style"]) - 1)]
        self.logger.info(Util.print_frame(f"Importing {filename}.atf as: {style_name}"))
        converted_lines = self.atf_preprocessor.convert_lines(filepath, filename)
        self.logger.info(Util.print_frame(f"Formatting to eBL-ATF of {filename}.atf"))
        ebl_lines = self.convert_to_ebl_lines(converted_lines, filename)
        self.logger.info(
            Util.print_frame(f"Importing converted lines of {filename}.atf into db")
        )
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
        importer.logger.info("Atf-Importer")
        importer.cli()


if __name__ == "__main__":
    AtfImporter.main()
