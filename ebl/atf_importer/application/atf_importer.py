import os
import glob
from pymongo import MongoClient
import logging
import argparse
from ebl.atf_importer.domain.atf_preprocessor import ATF_Preprocessor
from ebl.atf_importer.domain.atf_preprocessor_util import Util
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.fragmentarium.application.transliteration_update_factory import TransliterationUpdateFactory
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.web.dtos import parse_museum_number
from ebl.transliteration.domain.lemmatization import Lemmatization,LemmatizationToken
from ebl.app import create_context
from ebl.users.domain.user import ApiUser
from dotenv import load_dotenv

class LemmatizationError(Exception):
   pass

POS_TAGS  = ["REL" , "DET" , "CNJ" , "MOD" , "PRP" , "SBJ" , "AJ", "AV" , "NU" , "DP" , "IP" , "PP" , "RP" , "XP" , "QP" ,"DN" , "AN" , "CN" , "EN" , "FN" , "GN" , "LN", "MN" , "ON" , "PN" , "QN" , "RN" , "SN" , "TN" , "WN" ,"YN" , "N" , "V" , "J"]

not_lemmatized = {}
error_lines = []
success = []
failed = []

class ATF_Importer:

    def __init__(self):
        logging.basicConfig(level=logging.DEBUG)

        self.logger = logging.getLogger("atf-importer")

        # connect to eBL-db
        load_dotenv()
        client = MongoClient(os.getenv("MONGODB_URI"))
        db = client.get_database(os.getenv("MONGODB_DB"))
        self.db = db

    def get_ebl_transliteration(self,line):
        parsed_atf = parse_atf_lark(line)
        return parsed_atf

    def get_ebl_lemmata(self,orrac_lemma_tupel,all_unique_lemmas,filename):

        try:
            unique_lemmas = []

            for pair in orrac_lemma_tupel:

                oracc_lemma = pair[0]
                oracc_guideword = pair[1]

                if "//" in oracc_guideword:
                    oracc_guideword = oracc_guideword.split("//")[0]

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
                    except Exception as e:
                        if oracc_lemma not in not_lemmatized:
                            not_lemmatized[oracc_lemma] = True

                        self.logger.warning("Incompatible lemmatization: No citation form found in the glossary for '" + oracc_lemma + "'")

            # all attempts to find a ebl lemma failed
            if len(unique_lemmas) == 0:
                if oracc_lemma not in not_lemmatized:
                    not_lemmatized[oracc_lemma] = True
                self.logger.warning("Incompatible lemmatization: No eBL word found to oracc lemma or guide word (" + oracc_lemma + " : " + oracc_guideword + ")")

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

    def insert_translitertions(self,
            transliteration_factory: TransliterationUpdateFactory,
            updater: FragmentUpdater,
            transliterations,
            museum_number
    ) -> None:
        converted_transliteration = "\n".join(transliterations)
        transliteration = transliteration_factory.create(converted_transliteration, "")
        user = ApiUser("atf_importer.py")
        updater.update_transliteration(parse_museum_number(museum_number), transliteration, user)

    def insert_lemmatization(self,updater: FragmentUpdater, lemmatization, museum_number):
        lemmatization = Lemmatization(tuple(lemmatization))
        user = ApiUser("atf_importer.py")
        updater.update_lemmatization(parse_museum_number(museum_number),lemmatization , user)

    def get_museum_number(self,control_lines):
        for line in control_lines:
            linesplit = line['c_line'].split("=")
            if len(linesplit) > 1:
                return linesplit[-1].strip()

        return None

    def get_cdli_number(self,control_lines):

        for line in control_lines:
            linesplit = line['c_line'].split("=")
            cdli_number = linesplit[0].strip()
            cdli_number = cdli_number.replace("&", "")

            return cdli_number.strip()

        return None

    def get_museum_number_by_cdli_number(self, cdli_number):
        for entry in self.db.get_collection('fragments').find({"cdliNumber": cdli_number},{"museumNumber"}):
            return  entry['_id']

        return None

    def convert_to_ebl_lines(self,converted_lines,filename):
        result = dict()
        result['transliteration'] = []
        result['lemmatization'] = []
        result['control_lines'] = []

        for line in converted_lines:

            if line['c_type'] == "control_line":
                result['control_lines'].append(line)

            elif line['c_type'] == "lem_line":

                all_unique_lemmas = []
                lemma_line = []

                self.logger.debug(
                    "last transliteration " + str(last_transliteration) + " " + str(len(last_transliteration)))

                self.logger.debug("lem_line: " + str(line['c_array']) + " length " + str(len(line['c_array'])))

                for oracc_lemma_tupel in line['c_array']:
                    # get unique lemmata from ebl database
                    self.get_ebl_lemmata(oracc_lemma_tupel, all_unique_lemmas, filename)

                for alter_pos in last_alter_lemline_at:
                    self.logger.warning("Adding placeholder to lemma line at position:" + str(alter_pos))
                    all_unique_lemmas.insert(alter_pos, [])

                # reset lemma altering positions
                last_alter_lemline_at = []

                self.logger.debug(filename + ": transliteration " + str(last_transliteration_line))
                self.logger.debug(
                    "ebl transliteration" + str(last_transliteration) + " " + str(len(last_transliteration)))
                self.logger.debug("all_unique_lemmata " + str(all_unique_lemmas) + " " + str(len(all_unique_lemmas)))

                # join oracc_word with ebl unique lemmata
                oracc_word_ebl_lemmas = dict()
                cnt = 0
                if len(last_transliteration) != len(all_unique_lemmas):
                    self.logger.error("ARRAYS DON'T HAVE EQUAL LENGTH!!!")
                    error_lines.append(filename + ": transliteration " + str(last_transliteration_line))

                result['last_transliteration'] = last_transliteration
                result['all_unique_lemmas'] = all_unique_lemmas

                for oracc_word in last_transliteration:
                    oracc_word_ebl_lemmas[oracc_word] = all_unique_lemmas[cnt]
                    cnt += 1

                self.logger.debug("oracc_word_ebl_lemmas: " + str(oracc_word_ebl_lemmas))
                self.logger.debug("----------------------------------------------------------------------")

                # join ebl transliteration with lemma line:
                ebl_lines = self.get_ebl_transliteration(last_transliteration_line)

                for token in ebl_lines.lines[0].content:
                    unique_lemma = []
                    if token.value in oracc_word_ebl_lemmas:
                        unique_lemma = oracc_word_ebl_lemmas[token.value]

                    if len(unique_lemma) == 0:
                        lemma_line.append(LemmatizationToken(token.value, None))
                    else:
                        lemma_line.append(LemmatizationToken(token.value, tuple(unique_lemma)))
                result['lemmatization'].append(tuple(lemma_line))
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
        return result

    def insert_into_db(self,ebl_lines,filename):

        context = create_context()
        transliteration_factory = context.get_transliteration_update_factory()
        updater = context.get_fragment_updater()

        # museum_number = self.get_museum_number(result['control_lines'])
        cdli_number = self.get_cdli_number(ebl_lines['control_lines'])
        museum_number = self.get_museum_number_by_cdli_number(cdli_number)

        if(museum_number is None):
            failed.append(filename + " could not be imported, museum number not found")
            self.logger.error("museum number not found")

            self.logger.info(Util.print_frame("conversion of \"" + filename + ".atf\" failed"))
            return

        # insert transliteration
        self.insert_translitertions(transliteration_factory, updater, ebl_lines['transliteration'], museum_number)
        # insert lemmatization
        self.insert_lemmatization(updater, ebl_lines['lemmatization'], museum_number)

        success.append(filename + " successfully imported")
        self.logger.info(Util.print_frame("conversion of \"" + filename + ".atf\" finished"))



    def start(self):

        self.logger.info("Atf-Importer started...")

        #cli arguments
        parser = argparse.ArgumentParser(description='Converts ATF-files to eBL-ATF standard.')
        parser.add_argument('-i', "--input", required=True,
                            help='path of the input directory')
        parser.add_argument('-o', "--output", required=False,
                            help='path of the output directory')
        parser.add_argument('-g', "--glossary", required=True,
                            help='path to the glossary file')

        args = parser.parse_args()

        # parse glossary
        self.lemmas_cfforms, self.cfforms_senses, self.cfform_guideword = self.parse_glossary(
            args.glossary)

        #read atf files from input folder
        for filepath in glob.glob(os.path.join(args.input, '*.atf')):

            with open(filepath, 'r') as f:

                filepath = filepath.replace("\\","/")

                split = filepath.split("/")
                filename = split[-1]
                filename = filename.split(".")[0]
                # convert all lines
                self.atf_preprocessor = ATF_Preprocessor()
                converted_lines = self.atf_preprocessor.convert_lines(filepath,filename)

                self.logger.info(Util.print_frame("Formatting to EBL-ATF of "+ filename + ".atf"))
                ebl_lines = self.convert_to_ebl_lines(converted_lines,filename)
                # insert result into database
                self.logger.info(Util.print_frame("Inserting converted lines of "+ filename + ".atf into db"))
                self.insert_into_db(ebl_lines,filename)

            with open("../debug/not_lemmatized.txt", "w", encoding='utf8') as outputfile:
                    for key in not_lemmatized:
                        outputfile.write(key + "\n")

            with open("../debug/error_lines.txt", "w", encoding='utf8') as outputfile:
                for key in error_lines:
                    outputfile.write(key + "\n")

            with open("../debug/not_imported.txt", "w", encoding='utf8') as outputfile:
                for entry in failed:
                    outputfile.write(entry + "\n")

            with open("../debug/imported.txt", "w", encoding='utf8') as outputfile:
                for entry in success:
                    outputfile.write(entry+ "\n")

if __name__ == '__main__':
    a = ATF_Importer()
    a.start()
