import logging
from typing import Dict, List, Optional, Literal, get_args

LogKey = Literal[
    "not_lemmatized_lines",
    "error_lines",
    "not_imported_files",  # failed
    "imported_files",  # success
]

# ToDo: Continue from here. Check if all the logging the original
# code was preserved. Original variables:
# not_lemmatized = {}
# error_lines = []
# success = []
# failed = []


class Logger:
    def __init__(self, logdir: Optional[str] = None):
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger("Atf-Importer")
        self.logdir = logdir
        self.log_keys = get_args(LogKey)
        self.data: Dict[str, List[str]] = {key: [] for key in self.log_keys}

    def setLevel(self, level) -> None:
        self.logger.setLevel(level)

    def debug(self, text: str) -> None:
        self.logger.debug(text)

    def success(self, text: str, key: Optional[LogKey] = None) -> None:
        self.logger.success(text)
        self._append_to_data(text, key)

    def info(self, text: str, key: Optional[LogKey] = None) -> None:
        self.logger.info(text)
        self._append_to_data(text, key)

    def warning(self, text: str, key: Optional[LogKey] = None) -> None:
        self.logger.warning(text)
        self._append_to_data(text, key)

    def error(self, text: str, key: Optional[LogKey] = None) -> None:
        self.logger.error(text)
        self._append_to_data(text, key)

    def exception(self, text: str, key: Optional[LogKey] = None) -> None:
        self.logger.exception(text)
        self._append_to_data(text, key)

    def write_logs(self) -> None:
        if self.logdir:
            for key in self.log_keys:
                self._write_log(f"{key}.txt", self.data[key])

    def _write_log(self, filename: str, data: List[str]) -> None:
        with open(f"{self.logdir}{filename}", "w", encoding="utf8") as outputfile:
            for line in data:
                outputfile.write(line + "\n")

    def _append_to_data(self, text: str, key: Optional[LogKey] = None) -> None:
        if self.logdir and key:
            self.data[key].append(text)
