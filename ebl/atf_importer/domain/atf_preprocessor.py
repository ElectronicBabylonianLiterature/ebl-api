import codecs
import traceback
import re

from ebl.atf_importer.domain.atf_conversions import (
    Convert_Line_Dividers,
    Convert_Line_Joiner,
    Convert_Legacy_Grammar_Signs,
    Strip_Signs,
    Get_Lemma_Values_and_Guidewords,
    Get_Words,
    Line_Serializer,
)

from ebl.atf_importer.domain.atf_preprocessor_util import Util
from lark import Lark  # pyre-ignore[21]
import logging


class ATFPreprocessor:
    def __init__(self, logdir):
        self.EBL_PARSER = Lark.open(
            "../../transliteration/domain/ebl_atf.lark",
            maybe_placeholders=True,
            rel_to=__file__,
        )
        self.ORACC_PARSER = Lark.open(
            "lark-oracc/oracc_atf.lark", maybe_placeholders=True, rel_to=__file__
        )
        self.logger = logging.getLogger("Atf-Preprocessor")
        self.logger.setLevel(10)
        self.skip_next_lem_line = False
        self.unparseable_lines = []
        self.unused_lines = [
            "oracc_atf_at_line__object_with_status",
            "oracc_atf_at_line__surface_with_status",
            "oracc_atf_at_line__discourse",
            "oracc_atf_at_line__column",
            "dollar_line",
            "note_line",
            "control_line",
            "empty_line",
        ]
        self.stop_preprocessing = False
        self.logdir = logdir

    def get_empty_conversion(self, tree):
        line_serializer = Line_Serializer()
        line_serializer.visit_topdown(tree)
        converted_line = line_serializer.line.strip(" ")
        return converted_line, None, tree.data, None

    def convert_textline(self, tree):
        Convert_Line_Dividers().visit(tree)
        Convert_Line_Joiner().visit(tree)

        Convert_Legacy_Grammar_Signs().visit(tree)

        Strip_Signs().visit(tree)

        line_serializer = Line_Serializer()
        line_serializer.visit_topdown(tree)
        converted_line = line_serializer.line.strip(" ")

        words_serializer = Get_Words()
        words_serializer.result = []
        words_serializer.alter_lemline_at = []

        words_serializer.visit_topdown(tree)
        converted_line_array = words_serializer.result
        return converted_line, converted_line_array, words_serializer.alter_lemline_at

    def process_line(self, atf):
        self.logger.debug("Original line: '" + atf + "'")
        original_atf = atf

        try:
            if atf.startswith("#lem"):
                raise Exception

            # try to parse line with ebl-parser
            self.EBL_PARSER.parse(atf)

            # words serializer oracc parser
            tree = self.ORACC_PARSER.parse(atf)
            words_serializer = Get_Words()
            words_serializer.result = []
            words_serializer.visit_topdown(tree)
            converted_line_array = words_serializer.result

            self.logger.info("Line successfully parsed, no conversion needed")
            self.logger.debug(
                "Parsed line as "
                + tree.data
            )
            self.logger.info(
                "----------------------------------------------------------------------"
            )
            return atf, converted_line_array, tree.data, []

        except Exception:

            atf = re.sub(
                "([\[<])([\*:])(.*)", r"\1 \2\3", atf
            )  # convert [* => [  <* => < *
            atf = re.sub("(\*)([\]>])(.*)", r"\1 \2\3", atf)  # convert *] => * ]  ?

            atf = atf.replace("\t", " ")  # convert tabs to spaces
            atf = " ".join(atf.split())  # remove multiple spaces

            try:
                converted_line = ""
                tree = self.ORACC_PARSER.parse(atf)
                self.logger.debug("Converting " + tree.data)

                #self.logger.debug((tree.pretty()))

                if tree.data == "lem_line":

                    if self.skip_next_lem_line:
                        self.logger.warning("Skipping lem line")
                        self.skip_next_lem_line = False
                        return None, None, "lem_line", None

                    lemmas_and_guidewords_serializer = Get_Lemma_Values_and_Guidewords()
                    lemmas_and_guidewords_serializer.result = []
                    lemmas_and_guidewords_serializer.visit(tree)
                    lemmas_and_guidewords_array = (
                        lemmas_and_guidewords_serializer.result
                    )
                    self.logger.debug(
                        "Converted line as "
                        + tree.data
                        + " --> '"
                        + str(lemmas_and_guidewords_array)
                        + "'"
                    )
                    self.logger.debug(
                        "----------------------------------------------------------------------"
                    )

                    return atf, lemmas_and_guidewords_array, tree.data, []

                elif tree.data == "text_line":
                    converted_line, converted_line_array, alter_lemline_at = self.convert_textline(
                        tree
                    )

                    try:
                        self.EBL_PARSER.parse(converted_line)
                        self.logger.debug("Successfully parsed converted line")
                        self.logger.debug(converted_line)
                        self.logger.debug(
                            "Converted line as "
                            + tree.data
                            + " --> '"
                            + converted_line
                            + "'"
                        )
                        self.logger.debug(
                            "----------------------------------------------------------------------"
                        )

                        return (
                            converted_line,
                            converted_line_array,
                            tree.data,
                            alter_lemline_at,
                        )

                    except Exception as e:
                        self.logger.error(traceback.format_exc())
                        self.logger.error("Could not parse converted line")
                        self.unparseable_lines.append(original_atf)
                        return None, None, None, None

                else:
                    for line in self.unused_lines:
                        if tree.data == line:
                            return self.get_empty_conversion(tree)

            except Exception as e:

                error = "Could not convert line"
                self.logger.error(error + ": " + atf)
                self.logger.error(traceback.format_exc())

                if "translation" in atf:
                    self.stop_preprocessing = True

                self.unparseable_lines.append(original_atf)
                return None, None, None, None

    def convert_lines(self, file, filename):
        self.logger.info(Util.print_frame('Converting: "' + filename + '.atf"'))

        with codecs.open(file, "r", encoding="utf8") as f:
            atf_ = f.read()

        lines = atf_.split("\n")

        processed_lines = []
        for line in lines:
            c_line, c_array, c_type, c_alter_lemline_at = self.process_line(line)

            if self.stop_preprocessing:
                break

            if c_line != None:
                processed_lines.append(
                    {
                        "c_line": c_line,
                        "c_array": c_array,
                        "c_type": c_type,
                        "c_alter_lemline_at": c_alter_lemline_at,
                    }
                )
            elif c_type is None and c_line is None:
                self.skip_next_lem_line = True

        self.logger.info(Util.print_frame("Preprocessing finished"))

        with open(
            self.logdir + "unparseable_lines_" + filename + ".txt", "w", encoding="utf8"
        ) as outputfile:
            for key in self.unparseable_lines:
                outputfile.write(key + "\n")

        return processed_lines
