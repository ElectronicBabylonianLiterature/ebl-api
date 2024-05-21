import argparse
import glob
import os
from pymongo import MongoClient
from typing import List, TypedDict

from ebl.atf_importer.application.atf_importer_base import AtfImporterBase
from ebl.atf_importer.application.glossary_parser import (
    GlossaryParser,
    GlossaryParserData,
)
from ebl.atf_importer.domain.atf_preprocessor import AtfPreprocessor


class AtfImporterConfig(TypedDict):
    input_dir: str
    log_dir: str
    glossary_path: str
    author: str
    style: int


class AtfImporter(AtfImporterBase):
    def __init__(self, database):
        super().__init__(database)
        self.atf_preprocessor = None
        self.glossary_parser = GlossaryParser()

    def parse_glossary(
        self,
        path: str,
    ) -> GlossaryParserData:
        with open(path, "r", encoding="utf8") as file:
            return self.glossary_parser.parse(file)

    def run_importer(self, config: AtfImporterConfig) -> None:
        self.username = config["author"]
        self.atf_preprocessor = AtfPreprocessor(config["log_dir"], config["style"])
        file_paths = glob.glob(os.path.join(config["input_dir"], "*.atf"))
        self.process_files(file_paths, config["glossary_path"])

    def process_files(self, file_paths: List[str], glossary_path: str) -> None:
        glossary_data = self.parse_glossary(glossary_path)
        for filepath in file_paths:
            self.process_file(filepath, glossary_data)

    def process_file(
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
