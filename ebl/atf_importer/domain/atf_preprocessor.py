
import sys
import codecs
import re
import traceback
from ebl.atf_importer.domain.atf_preprocessor_util import Util
from lark import Lark
from lark import Tree, Transformer, Visitor
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

            except:
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

           except:
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

class Get_Line_Number(Visitor):
  nr = ""

  def oracc_atf_text_line__single_line_number(self, tree):
      assert tree.data == "oracc_atf_text_line__single_line_number"
      result = DFS().visit_topdown(tree, "")
      self.nr += result

      return result


class Get_Words(Visitor):
    result = []
    prefix = "oracc"
    def oracc_atf_text_line__word(self, tree):
        assert tree.data == "oracc_atf_text_line__word"

        word = ""
        for child in tree.children:
            wordpart = DFS().visit_topdown(child,"")
            word += wordpart

        self.result.append(word)


class Get_Lemma_Values_and_Guidewords(Visitor):
    result = []

    def oracc_atf_lem_line__lemma(self, tree):
        assert tree.data == "oracc_atf_lem_line__lemma"
        lemma_value = ""
        guide_word = ""
        i = 0
        cl = len(tree.children)
        for child in tree.children:
            if child.data=="oracc_atf_lem_line__value_part":
                lemma_value = DFS().visit_topdown(child,"")
                if cl>1 :
                    if tree.children[i+1].data== "oracc_atf_lem_line__guide_word":
                        guide_word = DFS().visit_topdown(tree.children[i+1],"")
                self.result.append((lemma_value,guide_word))
            i = i+1

class ATF_Preprocessor:

    def __init__(self):
        pass
        self.EBL_PARSER = Lark.open("lark-ebl/ebl_atf.lark", maybe_placeholders=True, rel_to=__file__)
        self.ORACC_PARSER = Lark.open("lark-oracc/oracc_atf.lark", maybe_placeholders=True, rel_to=__file__)
        self.logger = logging.getLogger("atf-importer")

    def process_line(self,atf):
        self.logger.debug("original line: '"+atf+"'")

        try:

            if atf.startswith("#lem"):
                raise Exception

            # try to parse line with ebl-parser
            tree = self.EBL_PARSER.parse(atf)

            # words serializer oracc parser
            tree = self.ORACC_PARSER.parse(atf)
            words_serializer = Get_Words()
            words_serializer.result = []
            words_serializer.visit_topdown(tree)
            converted_line_array = words_serializer.result

            self.debug.info("line successfully parsed, no conversion needed")
            self.debug.info("----------------------------------------------------------------------")
            return atf,converted_line_array,tree.data

        except Exception :


            atf = re.sub("([\[<])([\*:])(.*)", r"\1 \2\3", atf) # convert [* => [  <* => < *
            atf = re.sub("(\*)([\]>])(.*)", r"\1 \2\3", atf) # convert *] => * ]  ?

            atf = atf.replace("\t", " ") # convert tabs to spaces
            atf = ' '.join(atf.split()) # remove multiple spaces

            try:
                tree = self.ORACC_PARSER.parse(atf)

                self.logger.debug("converting " + tree.data)

                #print(tree.pretty())

                if tree.data == "lem_line":
                    lemmas_and_guidewords_serializer = Get_Lemma_Values_and_Guidewords()
                    lemmas_and_guidewords_serializer.result = []
                    lemmas_and_guidewords_array = lemmas_and_guidewords_serializer.visit(tree)
                    lemmas_and_guidewords_array = lemmas_and_guidewords_serializer.result
                    self.logger.debug("----------------------------------------------------------------------")
                    return None,lemmas_and_guidewords_array,tree.data



                else:
                    Convert_Line_Dividers().visit(tree)
                    Convert_Legacy_Grammar_Signs().visit(tree)

                    Strip_Signs().visit(tree)

                    line_serializer = Line_Serializer()
                    line_serializer.visit_topdown(tree)
                    converted_line = line_serializer.line.strip(" ")


                    words_serializer = Get_Words()
                    words_serializer.result = []
                    words_serializer.visit_topdown(tree)
                    converted_line_array = words_serializer.result

                    try:
                        tree3 = self.EBL_PARSER.parse(converted_line)
                        self.logger.debug('successfully parsed converted line')
                        self.logger.debug(converted_line)
                        self.logger.debug("----------------------------------------------------------------------")

                        return converted_line,converted_line_array,tree.data

                    except Exception as e:
                        self.logger.exception("could not parse converted line")
                        traceback.print_exc(file=sys.stdout)

                    self.logger.debug("converted line as " + tree.data + " --> '" + converted_line + "'")

            except:

                error = "could not convert line"
                self.logger.exception(error+": "+atf)
                traceback.print_exc(file=sys.stdout)

                return(error+": "+atf),None,None



    def convert_lines(self,file):
        self.logger.debug(Util.print_frame("converting: \""+file+"\""))

        with codecs.open(file, 'r', encoding='utf8') as f:
            atf_ = f.read()

        lines = atf_.split("\n")

        processed_lines = []
        for line in lines:
            c_line,c_array,c_type = self.process_line(line)
            processed_lines.append({"c_line":c_line,"c_array":c_array,"c_type":c_type})
        self.logger.debug(Util.print_frame("conversion finished"))

        return processed_lines



