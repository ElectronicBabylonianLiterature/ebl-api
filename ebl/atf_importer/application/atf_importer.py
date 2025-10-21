from ebl.app import create_context
from ebl.context import Context
from ebl.transliteration.domain.text import Text
from ebl.atf_importer.application.logger import Logger, LoggerUtil
from ebl.atf_importer.application.atf_importer_config import AtfImporterConfig
from ebl.atf_importer.application.database_importer import DatabaseImporter
from ebl.atf_importer.application.lines_getter import EblLinesGetter
from ebl.atf_importer.domain.legacy_atf_converter import LegacyAtfConverter
from ebl.atf_importer.application.glossary import GlossaryParser, Glossary
from typing import Any, Dict, List, TypedDict
from pymongo import MongoClient
import attr
import argparse
import glob
import os
os.environ["EBL_AI_API"] = ""


class AtfImporterArgs(TypedDict):
    input_dir: str
    logdir: str
    glodir: str
    author: str


class AtfImporter:
    logger: Any = None
    database_importer: Any = None

    def __init__(self, database, fragment_repository) -> None:
        self.database = database
        self.username: str = ""
        self.config = AtfImporterConfig().config_data
        self.atf_converter = None
        self.glossary_parser = GlossaryParser()
        self.glossary = Glossary(entries=[])
        self.ebl_lines_getter = None
        self.fragment_repository = fragment_repository

    def convert_to_ebl_lines(
        self,
        converted_lines: List[Dict[str, Any]],
        filename: str,
    ) -> Dict[str, List]:
        ebl_lines_getter = getattr(self, "ebl_lines_getter", None)
        if ebl_lines_getter:
            return ebl_lines_getter.convert_to_ebl_lines(converted_lines, filename)
        else:
            return {}

    def setup_importer(self, args: AtfImporterArgs) -> None:
        self.username = args["author"]
        self.logger = Logger(args["logdir"])
        self.logger.info("Atf-Importer")
        self.database_importer = DatabaseImporter(
            self.database, self.fragment_repository, self.logger, self.username
        )
        self.glossary = self.glossary_parser.load_glossaries(args["glodir"])
        self.atf_converter = LegacyAtfConverter(
            self.database, self.config, self.logger, self.glossary
        )
        self.ebl_lines_getter = EblLinesGetter(
            self.database, self.config, self.logger, self.glossary, self.atf_converter
        )

    def run_importer(self, args: AtfImporterArgs) -> None:
        self.setup_importer(args)
        file_paths = glob.glob(os.path.join(args["input_dir"], "*.atf"))
        for filepath in file_paths:
            self.logger.filepath = filepath
            self.process_file(filepath, args)
        self.logger.filepath = None
        self.logger.write_logs()

    def process_file(self, filepath: str, args: AtfImporterArgs) -> None:
        filename = os.path.basename(filepath).split(".")[0]
        self.logger.info(LoggerUtil.print_frame(f"Importing {filename}.atf"))
        converted_lines, text = self.atf_converter.convert_lines_from_path(
            filepath, filename
        )
        self.logger.info(
            LoggerUtil.print_frame(f"Formatting to eBL-ATF of {filename}.atf")
        )
        data = self.convert_to_ebl_lines(converted_lines, filename)
        control_lines = data["control_lines"]
        text = attr.evolve(text, lines=data["transliteration"])
        self.logger.info(
            LoggerUtil.print_frame(
                f"Importing converted lines of {filename}.atf into db"
            )
        )
        self.import_into_database(text, control_lines, filename)

    def import_into_database(
        self, text: Text, control_lines: List, filename: str
    ) -> None:
        try:
            self.database_importer.import_into_database(
                text, control_lines, filename)
        except Exception as e:
            self.logger.exception(f"Error while importing into database: {e}")

    def cli(self) -> None:
        parser = argparse.ArgumentParser(
            description="Converts ATF files to eBL-ATF standard."
        )

        for arg in self.config["CLI_ARGS"]:
            parser.add_argument(*arg["flags"], **arg["kwargs"])

        args = parser.parse_args()
        self.run_importer(
            {
                "input_dir": args.input,
                "logdir": args.logdir,
                "glodir": args.glodir,
                "author": args.author,
            }
        )

    @staticmethod
    def main() -> None:
        client = MongoClient(os.getenv("MONGODB_URI"))
        database = client.get_database(os.getenv("MONGODB_DB"))
        importer = AtfImporter(database, Context.fragment_repository)
        importer.cli()


if __name__ == "__main__":
    Context = create_context()
    AtfImporter.main()
