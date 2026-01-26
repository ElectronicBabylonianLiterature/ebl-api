import logging
from os import PathLike
from typing import Dict, List, Optional, Literal, Union, get_args
from pathlib import Path

LogKey = Literal[
    "unparsable_lines",
    "lemmatization_log",
    "error_lines",
    "not_imported_files",
    "imported_files",
]


class Logger:
    def __init__(self, logdir: Union[PathLike[str], str, None] = None):
        logging.basicConfig(level=logging.DEBUG)
        self.logger = logging.getLogger("Atf-Importer")
        self.logdir = logdir
        self.filepath: Optional[str] = None
        self.log_keys = get_args(LogKey)
        self.data: Dict[str, List[str]] = {key: [] for key in self.log_keys}

    def setLevel(self, level) -> None:
        self.logger.setLevel(level)

    def format_text(self, text: str) -> str:
        if self.filepath:
            return f"{self.filepath}: {text}"
        return text

    def debug(self, text: str) -> None:
        self.logger.debug(self.format_text(text))

    def info(self, text: str, key: Optional[LogKey] = None) -> None:
        text = self.format_text(text)
        self.logger.info(text)
        self._append_to_data(text, key)

    def warning(self, text: str, key: Optional[LogKey] = None) -> None:
        text = self.format_text(text)
        self.logger.warning(text)
        self._append_to_data(text, key)

    def error(self, text: str, key: Optional[LogKey] = None) -> None:
        text = self.format_text(text)
        self.logger.error(text)
        self._append_to_data(text, key)

    def exception(self, text: str, key: Optional[LogKey] = None) -> None:
        text = self.format_text(text)
        self.logger.exception(text)
        self._append_to_data(text, key)

    def write_logs(self) -> None:
        if self.logdir:
            for key in self.log_keys:
                self._write_log(f"{key}.txt", self.data[key])

    def _write_log(self, filename: str, data: List[str]) -> None:
        Path(self.logdir).mkdir(parents=True, exist_ok=True)  # pyre-ignore[6]
        with open(f"{self.logdir}/{filename}", "w", encoding="utf8") as outputfile:
            outputfile.write("\n".join(data))

    def _append_to_data(self, text: str, key: Optional[LogKey] = None) -> None:
        if self.logdir and key:
            self.data[key].append(text)


class LoggerUtil:
    @staticmethod
    def print_frame(s):
        r = "\n"
        r += " +-"

        for _i in range(len(s)):
            r += "-"
        r += "-+\n"
        r += " | " + s + " |\n"
        r += " +-"

        for _ in range(len(s)):
            r += "-"

        r += "-+\n"
        r += "\n"
        return r
