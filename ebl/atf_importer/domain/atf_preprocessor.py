from typing import Tuple, Optional, List, Dict, Any

from ebl.atf_importer.domain.atf_preprocessor_cdli import CdliReplacements
from ebl.atf_importer.domain.atf_preprocessor_atfc import AtfCReplacements

from ebl.atf_importer.domain.atf_preprocessor_util import Util


class AtfPreprocessor(AtfCReplacements, CdliReplacements):
    def convert_lines(self, file: str, filename: str) -> List[Dict[str, Any]]:
        self.logger.info(Util.print_frame(f'Converting: "{filename}.atf"'))

        lines = self.read_lines(file)
        processed_lines = []
        for line in lines:
            result = self.process_line(line)
            if self.stop_preprocessing:
                break
            processed_lines.append(
                {
                    "c_line": result[0],
                    "c_array": result[1],
                    "c_type": result[2],
                    "c_alter_lemline_at": result[3],
                }
            )

        self.logger.info(Util.print_frame("Preprocessing finished"))
        self.write_unparsable_lines(filename)  # ToDo: replace with normal logging
        return processed_lines

    def process_line(
        self, atf: str
    ) -> Tuple[Optional[str], Optional[List[Any]], Optional[str], Optional[List[Any]]]:
        self.logger.debug(f"Original line: '{atf}'")
        atf = self.preprocess_text(atf.replace("\r", ""))
        original_atf = atf

        try:
            if atf.startswith("#lem"):
                raise Exception("Special handling for #lem lines.")

            return self.check_original_line(atf)
        except Exception:
            if self.style == 1:
                atf = self.do_cdli_replacements(atf)
            elif self.style == 2:
                atf = self.do_atf_c_replacements(atf)
            else:
                atf = self.do_oracc_replacements(atf)
            # ToDo:
            # unused local variable
            # `atf` is not used
            return self.parse_and_convert_line(original_atf)
