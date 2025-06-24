import json
from typing import Dict, List, TypedDict, Union, Literal, Optional


class CliArgKwargs(TypedDict, total=False):
    required: bool
    help: str
    default: Optional[str]
    choices: Optional[List[str]]


class CliArgument(TypedDict):
    flags: List[str]
    kwargs: CliArgKwargs


class AtfImporterConfigData(TypedDict):
    STYLES: Dict[int, str]
    POS_TAGS: List[str]
    NOUN_POS_TAGS: List[str]
    CLI_ARGS: List[CliArgument]


class AtfImporterConfig:
    config_data: AtfImporterConfigData
    config_path = "ebl/atf_importer/domain/atf_importer_config.json"

    def __init__(self):
        with open(self.config_path, "r") as file:
            self.config_data: AtfImporterConfigData = json.load(file)

    def __getitem__(
        self, item: Literal["STYLES", "POS_TAGS", "NOUN_POS_TAGS", "CLI_ARGS"]
    ) -> Union[Dict[str, int], List[str]]:
        return getattr(self.config_data, item)
