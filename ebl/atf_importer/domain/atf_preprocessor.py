from typing import Tuple, Optional, List, Dict, Any

from ebl.atf_importer.domain.atf_preprocessor_cdli import CdliReplacements
from ebl.atf_importer.domain.atf_preprocessor_util import Util

# ToDo:
# The original code has 3 styles by mistake.
# There should remain only 2: C-ATF (CDLI) and O-ATF (ORACC).

class AtfPreprocessor(CdliReplacements):
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
        return processed_lines

    def process_line(
        self, atf: str
    ) -> Tuple[Optional[str], Optional[List[Any]], Optional[str], Optional[List[Any]]]:
        self.logger.debug(f"Original line: '{atf}'")
        atf_line = self.preprocess_text(atf.replace("\r", ""))
        original_atf_line = atf

        try:
            if atf_line.startswith("#lem"):
                raise Exception("Special handling for #lem lines.")
            if atf_line.startswith("@translation") or atf_line.startswith("@("):
                # ToDo: Handle translations
                # @translation labeled en project
                # @(t.e. 1)
                return self.parse_and_convert_line("")
            return self.check_original_line(atf)
        except Exception:
            # ToDo:
            # Styles should be only 1 (ORACC) and 2 (CDLI) (0 and 1)
            atf_line = self.do_cdli_replacements(atf_line)
            if self.style == 0:
                atf_line = self.do_oracc_replacements(atf_line)
            return self.parse_and_convert_line(atf_line)
