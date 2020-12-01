
import codecs
import traceback
import re
from ebl.atf_importer.domain.atf_conversions import\
    Convert_Line_Dividers,\
    Convert_Line_Joiner,\
    Convert_Legacy_Grammar_Signs,\
    Strip_Signs,\
    Get_Lemma_Values_and_Guidewords,\
    Get_Words,Line_Serializer

from ebl.atf_importer.domain.atf_preprocessor_util import Util
from lark import Lark
import logging

class ATF_Preprocessor:

    def __init__(self):
        self.EBL_PARSER = Lark.open("../../transliteration/domain/ebl_atf.lark", maybe_placeholders=True, rel_to=__file__)
        self.ORACC_PARSER = Lark.open("lark-oracc/oracc_atf.lark", maybe_placeholders=True, rel_to=__file__)
        self.logger = logging.getLogger("atf-preprocessor")
        self.logger.setLevel(10)
        self.skip_next_lem_line = False
        self.unparseable_lines = []
        self.unused_lines = ["oracc_atf_at_line__object_with_status",
                                  "oracc_atf_at_line__surface_with_status",
                                  "oracc_atf_at_line__discourse",
                                  "dollar_line",
                                  "note_line",
                                  "control_line",
                                  "empty_line"
                                  ]
        self.stop_preprocessing = False

    def get_empty_conversion(self,tree):
        line_serializer = Line_Serializer()
        line_serializer.visit_topdown(tree)
        converted_line = line_serializer.line.strip(" ")
        return converted_line, None, tree.data, None

    def process_line(self,atf):
        self.logger.debug("original line: '"+atf+"'")

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

            self.debug.info("line successfully parsed, no conversion needed")
            self.debug.info("----------------------------------------------------------------------")
            return atf,converted_line_array,tree.data,[]

        except Exception :

            atf = re.sub("([\[<])([\*:])(.*)", r"\1 \2\3", atf) # convert [* => [  <* => < *
            atf = re.sub("(\*)([\]>])(.*)", r"\1 \2\3", atf) # convert *] => * ]  ?

            atf = atf.replace("\t", " ") # convert tabs to spaces
            atf = ' '.join(atf.split()) # remove multiple spaces

            try:
                tree = self.ORACC_PARSER.parse(atf)
                self.logger.debug("converting " + tree.data)

                #self.logger.debug((tree.pretty()))

                if tree.data == "lem_line":

                    if self.skip_next_lem_line:
                        self.logger.warning("skipping lem line")
                        self.skip_next_lem_line = False
                        return None,None,"lem_line",None


                    lemmas_and_guidewords_serializer = Get_Lemma_Values_and_Guidewords()
                    lemmas_and_guidewords_serializer.result = []
                    lemmas_and_guidewords_serializer.visit(tree)
                    lemmas_and_guidewords_array = lemmas_and_guidewords_serializer.result
                    self.logger.debug("----------------------------------------------------------------------")
                    return atf,lemmas_and_guidewords_array,tree.data,[]


                elif tree.data == "text_line":
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
                    try:
                        self.EBL_PARSER.parse(converted_line)
                        self.logger.debug('successfully parsed converted line')
                        self.logger.debug(converted_line)
                        self.logger.debug("----------------------------------------------------------------------")

                        return converted_line,converted_line_array,tree.data,words_serializer.alter_lemline_at

                    except Exception as e:
                        self.logger.error("could not parse converted line")
                        self.logger.error(traceback.format_exc())

                    self.logger.debug("converted line as " + tree.data + " --> '" + converted_line + "'")

                elif "translation" in tree.data:
                    self.stop_preprocessing = True
                    return self.get_empty_conversion(tree)

                else:
                    for line in self.unused_lines:
                        if tree.data == line:
                           return self.get_empty_conversion(tree)

            except Exception as e:

                error = "could not convert line"
                self.logger.error(error+": "+atf)
                self.logger.error(traceback.format_exc())
                self.unparseable_lines.append(atf)
                return None,None,None,None


    def convert_lines(self,file,filename):
        self.logger.info(Util.print_frame("converting: \""+filename+".atf\""))

        with codecs.open(file, 'r', encoding='utf8') as f:
            atf_ = f.read()

        lines = atf_.split("\n")

        processed_lines = []
        for line in lines:
            c_line,c_array,c_type,c_alter_lemline_at = self.process_line(line)

            if self.stop_preprocessing:
                break

            if c_line != None:
                processed_lines.append({"c_line":c_line,"c_array":c_array,"c_type":c_type,"c_alter_lemline_at":c_alter_lemline_at})
            elif (c_type is None and c_line is None):
                self.skip_next_lem_line = True

        self.logger.info(Util.print_frame("preprocessing finished"))

        with open("../debug/unparseable_lines.txt", "w", encoding='utf8') as outputfile:
            for key in self.unparseable_lines:
                outputfile.write(key + "\n")

        return processed_lines


