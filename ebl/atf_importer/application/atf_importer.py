
import os
import glob
import unittest
import json
from pymongo import MongoClient
import logging

from ebl.atf_importer.domain.atf_preprocessor import ATF_Preprocessor
from ebl.atf_importer.domain.atf_preprocessor_util import Util
from ebl.transliteration.domain.lark_parser import parse_atf_lark

from ebl.transliteration.domain.text_line import TextLine

from dotenv import load_dotenv



class LemmatizationError(Exception):
   pass

POS_TAGS  = ["REL" , "DET" , "CNJ" , "MOD" , "PRP" , "SBJ" , "AJ", "AV" , "NU" , "DP" , "IP" , "PP" , "RP" , "XP" , "QP" ,"DN" , "AN" , "CN" , "EN" , "FN" , "GN" , "LN", "MN" , "ON" , "PN" , "QN" , "RN" , "SN" , "TN" , "WN" ,"YN" , "N" , "V" , "J"]

not_lemmatized = {}
error_lines = []

class TestConverter(unittest.TestCase):

    # Generic Line Test case for problematic text lines
    def test_lines(self):
        atf_preprocessor = ATF_Preprocessor()

        converted_line,c_array,type=atf_preprocessor.process_line("1. [*] AN#.GE₆ GAR-ma U₄ ŠU₂{+up} * AN.GE₆ GAR-ma {d}IŠKUR KA-šu₂ ŠUB{+di} * AN.GE₆")
        self.assertTrue(converted_line == "1. [ DIŠ ] AN#.GE₆ GAR-ma U₄ ŠU₂{+up} DIŠ AN.GE₆ GAR-ma {d}IŠKUR KA-šu₂ ŠUB{+di} DIŠ AN.GE₆")

        converted_line,c_array,type=atf_preprocessor.process_line("8. KAR <:> e-ṭe-ri :* KAR : e-ke-mu : LUGAL ina di-bi-ri : LUGAL ina ud-da-a-ta")
        self.assertTrue(converted_line == "8. KAR < :> e-ṭe-ri :* KAR : e-ke-mu : LUGAL ina di-bi-ri : LUGAL ina ud-da-a-ta")

    # Test case for removal of "$" if following sign not a logogram
    def test_following_sign_not_a_logogram(self):
        atf_preprocessor = ATF_Preprocessor()

        converted_line,c_array,type = atf_preprocessor.process_line("5'.	[...] x [...] x-šu₂? : kal : nap-ha-ri : $WA-wa-ru : ia-ar₂-ru",)
        self.assertTrue(converted_line == "5'. [...] x [...] x-šu₂? : kal : nap-ha-ri : WA-wa-ru : ia-ar₂-ru")

    # Test case for conversion of legacy grammar signs
    def test_legacy_grammar(self):
        atf_preprocessor = ATF_Preprocessor()

        converted_line,c_array,type = atf_preprocessor.process_line("57. {mulₓ(AB₂)}GU.LA KI* ŠEG₃ KI*# {kur}NIM.MA{ki} iš-kar* É.GAL : ANŠE.KUR.RA-MEŠ")
        self.assertTrue(converted_line == "57. {mulₓ(AB₂)}GU.LA KI* ŠEG₃ KI*# {kur}NIM.MA{ki} iš-kar* E₂.GAL : ANŠE.KUR.RA-MEŠ")

        converted_line,c_array,type = atf_preprocessor.process_line("57. {mulₓ(AB₂)}GU.LA KI* ŠEG₃ KI*# {kur}NIM.MA{ki} iš-kar* ÁM.GAL : ANŠE.KUR.RA-MEŠ")
        self.assertTrue(converted_line == "57. {mulₓ(AB₂)}GU.LA KI* ŠEG₃ KI*# {kur}NIM.MA{ki} iš-kar* AM₃.GAL : ANŠE.KUR.RA-MEŠ")

    # Test case to test if a lem line is parsed as type "lem_line"
    def test_lemmantization(self):
        atf_preprocessor = ATF_Preprocessor()

        converted_line,c_array,type = atf_preprocessor.process_line(
            "#lem: Sin[1]DN; ina[at]PRP; Nisannu[1]MN; ina[at]PRP; tāmartišu[appearance]N; adir[dark]AJ; ina[in]PRP; aṣîšu[going out]'N; adri[dark]AJ; uṣṣi[go out]V; šarrū[king]N; +šanānu[equal]V$iššannanū-ma")
        self.assertTrue(type == "lem_line")

        converted_line,c_array,type = atf_preprocessor.process_line("#lem: iššannanū-ma[equal]V; +šanānu[equal]V$iššannanū-ma; umma[saying]PRP; +šarru[king]N$; mala[as many]PRP; +šarru[king]N$šarri; +maṣû[correspond]V$imaṣṣû")
        self.assertTrue(type == "lem_line")

        converted_line,c_array,type =  atf_preprocessor.process_line("#lem: +adrūssu[darkly]AV$; īrub[enter]V; +arītu[pregnant (woman)]N$arâtu; ša[of]DET; libbašina[belly]N; ittadûni[contain]V; ina[in]PRP; +Zuqiqīpu[Scorpius]CN$")
        self.assertTrue(type == "lem_line")

        converted_line,c_array,type = atf_preprocessor.process_line("#lem: šatti[year]N; n; +Artaxerxes[]RN$artakšatsu; šar[king]N; pālih[reverent one]N; Nabu[1]DN; lā[not]MOD; itabbal[disappear]V; maʾdiš[greatly]N; lišāqir[value]V")
        self.assertTrue(type == "lem_line")

        converted_line,c_array,type = atf_preprocessor.process_line("#lem: +arāmu[cover]V$īrim-ma; ana[according to]PRP; birṣu[(a luminous phenomenon)]N; itârma[turn]V; adi[until]PRP; šāt[who(m)]DET&urri[daytime]N; illakma[flow]V")
        self.assertTrue(type == "lem_line")

        converted_line,c_array,type = atf_preprocessor.process_line("#lem: u; eššu[new]AJ; u +.")
        self.assertTrue(type == "lem_line")

        converted_line,c_array, type = atf_preprocessor.process_line(
            "#lem: u; ubû[unit]N; n; n; qû[unit]N; ubû[unit]N; +Ištar[]DN$; Ištar[1]DN +.; +saparru[cart]N$; u")
        self.assertTrue(type == "lem_line")

        converted_line,c_array,type = atf_preprocessor.process_line(
            "#lem: !+māru[son]N$; !+māru[son]N$māri; târu[turning back]'N; +našû[lift//carrying]V'N$ +.; u; +narkabtu[chariot]N$narkabta; īmur[see]V; marṣu[patient]N; šū[that]IP; qāt[hand]N; Ištar[1]DN; u")
        self.assertTrue(type == "lem_line")

        converted_line,c_array,type = atf_preprocessor.process_line("#lem: +burmāmu[(an animal)//porcupine?]N$; +burmāmu[(an animal)//porcupine?]N$buriyāmu; ša[whose]REL; +zumru[body]N$zumuršu; kīma[like]PRP; +ṭīmu[yarn]N$ṭime; +eṣēru[draw//mark]V$uṣṣuru +.")
        self.assertTrue(type == "lem_line")

        converted_line,c_array,type = atf_preprocessor.process_line("#lem: u; +appāru[reed-bed]N$")
        self.assertTrue(type == "lem_line")



    # Batch test case to test if lemma lines are parsed as type "lem_line"
    def test_lemmatization_batch(self):
        atf_preprocessor = ATF_Preprocessor()

        lines = atf_preprocessor.convert_lines("../test-files/test_lemma.atf")

        for line in lines:
            self.assertTrue(line['c_type'] == "lem_line")

    # Batch test for cccp files
    def test_cccp(self):
            atf_preprocessor = ATF_Preprocessor()

            lines = atf_preprocessor.convert_lines("../test-files/cccp_3_1_16_test.atf")
            self.assertTrue(len(lines)==259)

            lines = atf_preprocessor.convert_lines("../test-files/cccp_3_1_21_test.atf")
            self.assertTrue(len(lines) == 90) # one invalid line removed


class ATF_Importer:

    def __init__(self):


        self.atf_preprocessor = ATF_Preprocessor()
        self.logger = logging.getLogger("atf-importer")
        self.logger.setLevel(10)


        # parse glossary
        self.lemmas_cfforms, self.cfforms_senses, self.cfform_guideword = self.parse_glossary("/usr/src/ebl/ebl/atf_importer/application/glossary/akk-x-stdbab.glo")

        # connect to eBL-db
        load_dotenv()
        client = MongoClient(os.getenv("MONGODB_URI"))
        db = client.get_database(os.getenv("MONGODB_DB"))
        self.db = db

    def get_ebl_transliteration(self,line):
        parsed_atf = parse_atf_lark(line)
        return parsed_atf

    def get_ebl_lemmata(self,oracc_lemma,oracc_guideword,all_unique_lemmas,filename):

        try:
            unique_lemmas = []

            if oracc_guideword == "":
                if oracc_lemma not in not_lemmatized:
                    not_lemmatized[oracc_lemma] = True
                self.logger.warning("Incompatible lemmatization: No guideWord to oracc lemma '" + oracc_lemma + "' present")

            # if "X" or "u" or "n" then add [] and return
            if oracc_lemma == "X" or oracc_lemma == "u" or oracc_lemma == "n":
                self.logger.warning("Oracc lemma was '"+oracc_lemma+"' ->  here no lemmatization")
                all_unique_lemmas.append(unique_lemmas)
                return



            for entry in self.db.get_collection('words').find({"oraccWords.guideWord": oracc_guideword}, {"_id"}):
                unique_lemmas.append(entry['_id'])

            for entry in self.db.get_collection('words').find({"oraccWords.lemma": oracc_lemma}, {"_id"}):
                if entry['_id'] not in unique_lemmas:
                    unique_lemmas.append(entry['_id'])

            for entry in self.db.get_collection('words').find({"guideWord": oracc_guideword}, {"_id"}):
                if entry['_id'] not in unique_lemmas:
                    unique_lemmas.append(entry['_id'])

            if len(unique_lemmas) == 0:
                try:
                    citation_form = self.lemmas_cfforms[oracc_lemma]
                    guideword = self.cfform_guideword[citation_form]
                    if "//" in guideword:
                        guideword = guideword.split("//")[0]
                    senses = self.cfforms_senses[citation_form]

                    if senses != None and oracc_guideword in senses:

                        for entry in self.db.get_collection('words').find({"oraccWords.guideWord": guideword}, {"_id"}):
                            unique_lemmas.append(entry['_id'])

                        for entry in self.db.get_collection('words').find({"oraccWords.lemma": citation_form}, {"_id"}):
                            if entry['_id'] not in unique_lemmas:
                                unique_lemmas.append(entry['_id'])

                        for entry in self.db.get_collection('words').find({"oraccWords.lemma": oracc_lemma}, {"_id"}):
                            if entry['_id'] not in unique_lemmas:
                                unique_lemmas.append(entry['_id'])

                        for entry in self.db.get_collection('words').find({"guideWord": oracc_guideword}, {"_id"}):
                            if entry['_id'] not in unique_lemmas:
                                unique_lemmas.append(entry['_id'])


                except:
                    if oracc_lemma not in not_lemmatized:
                        not_lemmatized[oracc_lemma] = True

                    self.logger.error("Incompatible lemmatization: No citation form found in the glossary for '" + oracc_lemma + "'")

            # all attempts to find a ebl lemma failed
            if len(unique_lemmas) == 0:
                if oracc_lemma not in not_lemmatized:
                    not_lemmatized[oracc_lemma] = True
                self.logger.error("Incompatible lemmatization: No eBL word found to oracc lemma or guide word (" + oracc_lemma + " : " + oracc_guideword + ")")

            all_unique_lemmas.append(unique_lemmas)

        except Exception as e:
            self.logger.exception(e)



    def parse_glossary(self,path):

        lemmas_cfforms = dict()
        cfforms_senses = dict()
        cfform_guideword = dict()

        with open(path, "r", encoding='utf8') as f:
            for line in f.readlines():

                if line.startswith("@entry"):
                    split = line.split(" ")
                    cfform = split[1]
                    guidword = split[2].rstrip("]").lstrip("[")
                    cfform_guideword[cfform] = guidword

                if line.startswith("@form"):
                    split = line.split(" ")
                    lemma = split[2].lstrip("$").rstrip("\n")
                    lemmas_cfforms[lemma] = cfform.strip()

                if line.startswith("@sense"):
                    split = line.split(" ")

                    for s in split:
                        if s in POS_TAGS:
                            pos_tag = s

                    split2 = line.split(pos_tag)
                    sense = split2[1].rstrip("\n")
                    if not cfform in cfforms_senses:
                        cfforms_senses[cfform] = [sense.strip()]
                    else:
                        cfforms_senses[cfform].append(sense.strip())
        return lemmas_cfforms,cfforms_senses,cfform_guideword

    def start(self):
        self.logger.info("Atf-Importer started...")



        #atf_preprocessor.process_line("#lem: X; attallû[eclipse]N; iššakkan[take place]V; šar[king]N; imâtma[die]V",True)
        #atf_preprocessor.process_line("#lem: mīlū[flood]N; ina[in]PRP; nagbi[source]N; ipparrasū[cut (off)]V; mātu[land]N; ana[according to]PRP; mātu[land]N; +hâqu[go]V$ihâq-ma; šalāmu[peace]N; šakin[displayed]AJ",True)
        #self.atf_preprocessor.process_line("1. [*] AN#.GE₆ GAR-ma U₄ ŠU₂{+up} * AN.GE₆ GAR-ma {d}IŠKUR KA-šu₂ ŠUB{+di} * AN.GE₆")

        # cli arguments
        #parser = argparse.ArgumentParser(description='Converts ATF-files to eBL-ATF standard.')
        #parser.add_argument('-i', "--input", required=True,
                            #help='path of the input directory')
        #parser.add_argument('-o', "--output", required=False,
                            #help='path of the output directory')
        #parser.add_argument('-g', "--glossary", required=True,
                            #help='path to the glossary file')
        #parser.add_argument('-t', "--test", required=False, default=False, action='store_true',
                            #help='runs all unit-tests')
        #parser.add_argument('-v', "--verbose", required=False, default=False, action='store_true',
                            #help='display status messages')

        #args = parser.parse_args()

        #debug = args.verbose


        #read atf files from input folder
        for filepath in glob.glob(os.path.join("/usr/src/ebl/ebl/atf_importer/input/", '*.atf')):

            with open(filepath, 'r') as f:

                # convert all lines
                converted_lines =  self.atf_preprocessor.convert_lines(filepath)

                # write result output
                self.logger.debug(Util.print_frame("writing output"))

                result = dict()
                result['transliteration'] = []
                result['lemmatization'] = []

                split = filepath.split("/")
                filename = split[-1]
                filename = filename.split(".")[0]
                for line in converted_lines:

                    if line['c_type'] == "lem_line":

                        wrong_lemmatization = False
                        all_unique_lemmas = []
                        lemma_line = []

                        self.logger.debug("last transliteration " + str(last_transliteration) + " " + str(len(last_transliteration)))

                        self.logger.debug("lem_line: " + str(line['c_array']) + " length " + str(len(line['c_array'])))

                        for pair in line['c_array'] :

                            oracc_lemma = pair[0]
                            oracc_guideword = pair[1]

                            if "//" in oracc_guideword:
                                oracc_guideword = oracc_guideword.split("//")[0]

                            # get unique lemmata from ebl database
                            self.get_ebl_lemmata(oracc_lemma,oracc_guideword,all_unique_lemmas,filename)

                        for alter_pos in last_alter_lemline_at:
                            self.logger.warning("Adding placeholder to lemma line at position:"+str(alter_pos))
                            all_unique_lemmas.insert(alter_pos,[])

                        # reset lemma altering positions
                        last_alter_lemline_at = []

                        self.logger.debug(filename+": transliteration " + str(last_transliteration_line))
                        self.logger.debug("ebl transliteration" + str(last_transliteration) + " " + str(len(last_transliteration)))
                        self.logger.debug("all_unique_lemmata " + str(all_unique_lemmas) + " " + str(len(all_unique_lemmas)))

                        # join oracc_word with ebl unique lemmata
                        oracc_word_ebl_lemmas = dict()
                        cnt = 0
                        if len(last_transliteration) != len(all_unique_lemmas):
                            self.logger.error("ARRAYS DON'T HAVE EQUAL LENGTH!!!")
                            error_lines.append(filename+": transliteration " + str(last_transliteration_line))

                        for oracc_word in last_transliteration:
                            oracc_word_ebl_lemmas[oracc_word] = all_unique_lemmas[cnt]
                            cnt += 1

                        self.logger.debug("oracc_word_ebl_lemmas: " + str(oracc_word_ebl_lemmas))
                        self.logger.debug("----------------------------------------------------------------------")

                        # join ebl transliteration with lemma line:
                        ebl_lines = self.get_ebl_transliteration(last_transliteration_line)


                        for token in ebl_lines.lines[0].content:

                            unique_lemma = []
                            if token.clean_value in oracc_word_ebl_lemmas:
                                unique_lemma = oracc_word_ebl_lemmas[token.clean_value]

                            lemma_line.append({"value": token.clean_value, "uniqueLemma": unique_lemma })


                        result['lemmatization'].append(lemma_line)

                    else:

                        if line['c_type'] == "text_line":

                            # skip "DIŠ"
                            oracc_words = []
                            for entry in line['c_array']:
                                if entry != "DIŠ":
                                    oracc_words.append(entry)

                            last_transliteration_line = line['c_line']
                            last_transliteration = oracc_words
                            last_alter_lemline_at = line['c_alter_lemline_at']

                        result['transliteration'].append(line['c_line'])


                json_string = json.dumps(result, ensure_ascii=False).encode('utf8')
                with open("/usr/src/ebl/ebl/atf_importer/output/" + filename+".json", "w", encoding='utf8') as outputfile:
                    json.dump(result,outputfile,ensure_ascii=False)

            with open("/usr/src/ebl/ebl/atf_importer/debug/not_lemmatized.txt", "w", encoding='utf8') as outputfile:
                    for key in not_lemmatized:
                        outputfile.write(key + "\n")

            with open("/usr/src/ebl/ebl/atf_importer/debug/error_lines.txt", "w", encoding='utf8') as outputfile:
                for key in error_lines:
                    outputfile.write(key + "\n")

                self.logger.debug(Util.print_frame("conversion of "+filename+" finished"))


