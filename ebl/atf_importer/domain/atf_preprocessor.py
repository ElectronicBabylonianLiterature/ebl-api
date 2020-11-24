
import codecs
import re
import traceback
from ebl.atf_importer.domain.atf_preprocessor_util import Util
from lark import Lark
from lark import Visitor
from lark import lexer
import logging

class ConversionError(Exception):
   pass

class ParseError(Exception):
   pass

class Convert_Line_Dividers(Visitor):

  def oracc_atf_text_line__divider(self, tree):
    assert tree.data == "oracc_atf_text_line__divider"
    if tree.children[0] == "*":
        tree.children[0] = "DIŠ"

class Convert_Line_Joiner(Visitor):

  def oracc_atf_text_line__joiner(self, tree):
    assert tree.data == "oracc_atf_text_line__joiner"
    if tree.children[0] == "--":
        tree.children[0] = "-"

class Convert_Legacy_Grammar_Signs(Visitor):

  replacement_chars = {
      "á" : "a",
      "é" : "e",
      "í": "i",
      "ú" : "u",
      "Á" : "A",
      "É" : "E",
      "Ì" : "I",
      "Ú" : "U"
  }

  def oracc_atf_text_line__logogram_name_part(self, tree):
    assert tree.data == "oracc_atf_text_line__logogram_name_part"
    cnt = 0
    for child in tree.children:

        pattern = re.compile("[ÁÉÍÙ]")
        matches = pattern.search(child)

        if (matches != None):

            match = matches.group(0)
            try:
                next_char = tree.children[cnt + 1]
                tree.children[cnt] = self.replacement_chars[match]
                tree.children[cnt + 1] = next_char + "₃"

            except Exception as e:
                tree.children[cnt] = self.replacement_chars[match] + "₂"

        cnt = cnt + 1

  def oracc_atf_text_line__value_name_part(self, tree):
    assert tree.data == "oracc_atf_text_line__value_name_part"
    cnt = 0
    for child in tree.children:

        pattern = re.compile("[áíéú]")
        matches = pattern.search(child)

        if(matches!=None):

           match = matches.group(0)
           try:
               next_char = tree.children[cnt + 1]
               tree.children[cnt] = self.replacement_chars[match]
               tree.children[cnt+1] = next_char+"₃"

           except Exception as e:
               tree.children[cnt] = self.replacement_chars[match]+"₂"



        cnt = cnt + 1

class Strip_Signs(Visitor):

  def oracc_atf_text_line__uncertain_sign(self, tree):
    assert tree.data == "oracc_atf_text_line__uncertain_sign"
    if tree.children[0] == "$":
        tree.children[0] = ""


class DFS(Visitor):
    def visit_topdown(self,tree,result):

        if not hasattr(tree, 'data'):
            return result

        for child in tree.children:
            if isinstance(child, str) or isinstance(child, int):
                result +=child
            result = DFS().visit_topdown(child,result)
        return result

class Line_Serializer(Visitor):
  line = ""

  def text_line(self, tree):
    assert tree.data == "text_line"
    result = DFS().visit_topdown(tree,"")
    self.line+= " " + result
    return result

  def dollar_line(self, tree):
    assert tree.data == "dollar_line"
    result = DFS().visit_topdown(tree,"")
    self.line+= " " + result
    return result

  def control_line(self, tree):
    assert tree.data == "control_line"
    result = DFS().visit_topdown(tree,"")
    self.line+= " " + result
    return result

class Get_Line_Number(Visitor):
  nr = ""

  def oracc_atf_text_line__single_line_number(self, tree):
      assert tree.data == "oracc_atf_text_line__single_line_number"
      result = DFS().visit_topdown(tree, "")
      self.nr += result

      return result


class Get_Words(Visitor):
    wordcounter = 0;
    result = []
    alter_lemline_at = []
    prefix = "oracc"

    removal_open = False

    def oracc_atf_text_line__word(self, tree):
        assert tree.data == "oracc_atf_text_line__word"
        word = ""
        for child in tree.children:
            # try to find positions of removals to add placeholders to subsequent lem line
            if child == "<<" and word == "":
                self.removal_open = True
            if child == ">>" and self.removal_open:
                    self.removal_open = False
                    self.alter_lemline_at.append(self.wordcounter)

            if isinstance(child,lexer.Token):
                 word += child
            else:
                word += DFS().visit_topdown(child,"")



        self.result.append(word)
        self.wordcounter = self.wordcounter+1

class Get_Lemma_Values_and_Guidewords(Visitor):
    result = []
    additional_lemmata = False

    def oracc_atf_lem_line__lemma(self, tree):


        assert tree.data == "oracc_atf_lem_line__lemma"
        guide_word = ""
        i = 0
        cl = len(tree.children)
        lemmata = []
        for child in tree.children:

            # collect additional lemmata and guidwords
            if child.data == "oracc_atf_lem_line__additional_lemmata":

                for a_child in child.children:
                    if hasattr(a_child, 'data'):

                        if a_child.data == "oracc_atf_lem_line__additional_lemma":
                            acl = len(a_child.children)
                            j = 0
                            for b_child in a_child.children:
                                additional_lemma_value = ""
                                additional_guide_word = ""
                                if b_child.data == "oracc_atf_lem_line__value_part":
                                    additional_lemma_value = DFS().visit_topdown(b_child, "")
                                    if acl > 1 and a_child.children[j + 1].data == "oracc_atf_lem_line__guide_word":
                                        additional_guide_word = DFS().visit_topdown(a_child.children[j + 1], "")
                                if(additional_lemma_value!=""): # to be fixed runs too often
                                 lemmata.append((additional_lemma_value,additional_guide_word))

            # find actual lemma and guidewords
            if child.data == "oracc_atf_lem_line__value_part":
                lemma_value = DFS().visit_topdown(child,"")
                if cl>1 and tree.children[i+1].data== "oracc_atf_lem_line__guide_word":
                        guide_word = DFS().visit_topdown(tree.children[i+1],"")
                lemmata.append((lemma_value,guide_word))
                self.result.append(lemmata)
            i = i+1

class ATF_Preprocessor:

    def __init__(self):
        self.EBL_PARSER = Lark.open("../../transliteration/domain/ebl_atf.lark", maybe_placeholders=True, rel_to=__file__)

        self.ORACC_PARSER = Lark.open("lark-oracc/oracc_atf.lark", maybe_placeholders=True, rel_to=__file__)
        self.logger = logging.getLogger("atf-preprocessor")
        self.logger.setLevel(10)
        self.skip_next_lem_line = False

        self.unparseable_lines = []

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
                        #self.logger.error(traceback.print_exc())

                    self.logger.debug("converted line as " + tree.data + " --> '" + converted_line + "'")

                elif "oracc_atf_at_line__object_with_status" in tree.data:
                    line_serializer = Line_Serializer()
                    line_serializer.visit_topdown(tree)
                    converted_line = line_serializer.line.strip(" ")
                    return converted_line, None, tree.data, None

                elif "oracc_atf_at_line__surface_with_status" in tree.data:
                    line_serializer = Line_Serializer()
                    line_serializer.visit_topdown(tree)
                    converted_line = line_serializer.line.strip(" ")
                    return converted_line, None, tree.data, None

                elif "oracc_atf_at_line__discourse" in tree.data:
                    line_serializer = Line_Serializer()
                    line_serializer.visit_topdown(tree)
                    converted_line = line_serializer.line.strip(" ")
                    return converted_line, None, tree.data, None

                elif "dollar_line" in tree.data:
                    line_serializer = Line_Serializer()
                    line_serializer.visit_topdown(tree)
                    converted_line = line_serializer.line.strip(" ")
                    return converted_line, None, tree.data, None

                elif "note_line" in tree.data:
                    line_serializer = Line_Serializer()
                    line_serializer.visit_topdown(tree)
                    converted_line = line_serializer.line.strip(" ")
                    return converted_line, None, tree.data, None

                elif tree.data == "control_line":
                    line_serializer = Line_Serializer()
                    line_serializer.visit_topdown(tree)
                    converted_line = line_serializer.line.strip(" ")
                    return converted_line, None, tree.data, None

                elif tree.data == "empty_line":
                    line_serializer = Line_Serializer()
                    line_serializer.visit_topdown(tree)
                    converted_line = line_serializer.line.strip(" ")
                    return converted_line, None, tree.data, None

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

            if c_line != None:
                processed_lines.append({"c_line":c_line,"c_array":c_array,"c_type":c_type,"c_alter_lemline_at":c_alter_lemline_at})
            elif (c_type is None and c_line is None):
                self.skip_next_lem_line = True

        self.logger.info(Util.print_frame("preprocessing finished"))

        with open("../debug/unparseable_lines.txt", "w", encoding='utf8') as outputfile:
            for key in self.unparseable_lines:
                outputfile.write(key + "\n")

        return processed_lines



