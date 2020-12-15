import os
import glob
from pymongo import MongoClient  # pyre-ignore[21]
import logging
import argparse
from ebl.atf_importer.domain.atf_preprocessor import ATFPreprocessor
from ebl.atf_importer.domain.atf_preprocessor_util import Util
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.fragmentarium.application.transliteration_update_factory import (
    TransliterationUpdateFactory,
)
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.web.dtos import parse_museum_number
from ebl.transliteration.domain.lemmatization import Lemmatization, LemmatizationToken
from ebl.app import create_context
from ebl.users.domain.user import ApiUser
from dotenv import load_dotenv  # pyre-ignore[21]
import re

class LemmatizationError(Exception):
    pass


POS_TAGS = [
    "REL",
    "DET",
    "CNJ",
    "MOD",
    "PRP",
    "SBJ",
    "AJ",
    "AV",
    "NU",
    "DP",
    "IP",
    "PP",
    "RP",
    "XP",
    "QP",
    "DN",
    "AN",
    "CN",
    "EN",
    "FN",
    "GN",
    "LN",
    "MN",
    "ON",
    "PN",
    "QN",
    "RN",
    "SN",
    "TN",
    "WN",
    "YN",
    "N",
    "V",
    "J",
]

not_lemmatized = {}
error_lines = []
success = []
failed = []


class ATFImporter:
    def __init__(self):
        logging.basicConfig(level=logging.DEBUG)

        self.logger = logging.getLogger("Atf-Importer")
        self.atf_preprocessor = ATFPreprocessor("../logs")

        self.lemmas_cfforms = None
        self.cfforms_senses = None
        self.cfform_guideword = None

        # connect to eBL-db
        load_dotenv()
        client = MongoClient(os.getenv("MONGODB_URI"))
        db = client.get_database(os.getenv("MONGODB_DB"))
        self.db = db

    @staticmethod
    def get_ebl_transliteration(line):
        parsed_atf = parse_atf_lark(line)
        return parsed_atf

    def get_ebl_lemmata(self, orrac_lemma_tupel, all_unique_lemmas):

        try:
            unique_lemmas = []
            oracc_lemma = None
            oracc_guideword = None

            for pair in orrac_lemma_tupel:
                oracc_lemma = pair[0]
                oracc_guideword = pair[1]

                if "//" in oracc_guideword:
                    oracc_guideword = oracc_guideword.split("//")[0]

                if oracc_guideword == "":
                    if oracc_lemma not in not_lemmatized:
                        not_lemmatized[oracc_lemma] = True
                    self.logger.warning(
                        "Incompatible lemmatization: No guideWord to oracc lemma '"
                        + oracc_lemma
                        + "' present"
                    )

                # if "X" or "u" or "n" then add [] and return
                if oracc_lemma == "X" or oracc_lemma == "u" or oracc_lemma == "n":
                    self.logger.warning(
                        "Oracc lemma was '"
                        + oracc_lemma
                        + "' ->  here no lemmatization"
                    )
                    all_unique_lemmas.append(unique_lemmas)
                    return

                for entry in self.db.get_collection("words").find(
                        {"oraccWords.lemma": oracc_lemma, "oraccWords.guideWord": oracc_guideword}, {"_id"}
                ):
                    if entry["_id"] not in unique_lemmas:
                        unique_lemmas.append(entry["_id"])

                if len(unique_lemmas) == 0:

                    try:
                        citation_form = self.lemmas_cfforms[oracc_lemma]
                        guideword = self.cfform_guideword[citation_form]

                        print(citation_form,guideword)
                        if "//" in guideword:
                            guideword = guideword.split("//")[0]
                        #senses = self.cfforms_senses[citation_form]
                        #if senses is not None and oracc_guideword in senses:
                        for entry in self.db.get_collection("words").find(
                            {"oraccWords.guideWord": guideword,"oraccWords.lemma": citation_form}, {"_id"}
                        ):
                            unique_lemmas.append(entry["_id"])

                        if len(unique_lemmas) == 0:
                            for entry in self.db.get_collection("words").find(
                                {"forms.lemma": [citation_form], "guideWord": guideword}, {"_id"}
                            ):
                                if entry["_id"] not in unique_lemmas:
                                    unique_lemmas.append(entry["_id"])

                            for entry in self.db.get_collection("words").find(
                                    {"lemma": [citation_form], "guideWord": guideword}, {"_id"}
                            ):
                                if entry["_id"] not in unique_lemmas:
                                    unique_lemmas.append(entry["_id"])

                    except Exception:
                        if oracc_lemma not in not_lemmatized:
                            not_lemmatized[oracc_lemma] = True

                            self.logger.warning(
                                "Incompatible lemmatization: No citation form found in the glossary for '"
                                + oracc_lemma
                                + "'"
                            )

            # all attempts to find a ebl lemma failed
            if len(unique_lemmas) == 0:
                if oracc_lemma not in not_lemmatized:
                    not_lemmatized[oracc_lemma] = True
                self.logger.warning(
                    "Incompatible lemmatization: No eBL word found to oracc lemma or guide word ("
                    + oracc_lemma
                    + " : "
                    + oracc_guideword
                    + ")"
                )

            all_unique_lemmas.append(unique_lemmas)

        except Exception as e:
            self.logger.exception(e)

    @staticmethod
    def parse_glossary(path):

        lemmas_cfforms = dict()
        cfforms_senses = dict()
        cfform_guideword = dict()

        with open(path, "r", encoding="utf8") as f:
            for line in f.readlines():

                if line.startswith("@entry"):
                    split = line.split(" ",2)
                    cfform = split[1]
                    p = re.compile(r'\[(.*)\]')
                    matches = p.findall(split[2])
                    guidword = matches[0]
                    guidword = guidword.rstrip("]").lstrip("[")

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
                    if cfform not in cfforms_senses:
                        cfforms_senses[cfform] = [sense.strip()]
                    else:
                        cfforms_senses[cfform].append(sense.strip())
        return lemmas_cfforms, cfforms_senses, cfform_guideword

    @staticmethod
    def insert_translitertions(
        transliteration_factory: TransliterationUpdateFactory,
        updater: FragmentUpdater,
        transliterations,
        museum_number,
    ) -> None:
        converted_transliteration = "\n".join(transliterations)
        transliteration = transliteration_factory.create(converted_transliteration, "")
        user = ApiUser("atf_importer.py")
        updater.update_transliteration(
            parse_museum_number(museum_number), transliteration, user
        )

    @staticmethod
    def insert_lemmatization(updater: FragmentUpdater, lemmatization, museum_number):
        lemmatization = Lemmatization(tuple(lemmatization))
        user = ApiUser("atf_importer.py")
        updater.update_lemmatization(
            parse_museum_number(museum_number), lemmatization, user
        )

    @staticmethod
    def get_museum_number(control_lines):
        for line in control_lines:
            linesplit = line["c_line"].split("=")
            if len(linesplit) > 1:
                return linesplit[-1].strip()

        return None

    @staticmethod
    def get_cdli_number(control_lines):

        for line in control_lines:
            linesplit = line["c_line"].split("=")
            cdli_number = linesplit[0].strip()
            cdli_number = cdli_number.replace("&", "")

            return cdli_number.strip()

        return None

    def get_museum_number_by_cdli_number(self, cdli_number):
        for entry in self.db.get_collection("fragments").find(
            {"cdliNumber": cdli_number}, {"museumNumber"}
        ):
            return entry["_id"]

        return None

    def convert_to_ebl_lines(self, converted_lines, filename):
        result = dict()
        result["transliteration"] = []
        result["lemmatization"] = []
        result["control_lines"] = []
        last_transliteration_line = ""
        last_alter_lemline_at = []
        last_transliteration = []

        for line in converted_lines:

            if line["c_type"] == "control_line":
                result["control_lines"].append(line)

            elif line["c_type"] == "lem_line":

                all_unique_lemmas = []
                lemma_line = []

                for oracc_lemma_tupel in line["c_array"]:
                    # get unique lemmata from ebl database
                    self.get_ebl_lemmata(oracc_lemma_tupel, all_unique_lemmas)

                for alter_pos in last_alter_lemline_at:
                    self.logger.warning(
                        "Adding placeholder to lemma line at position:" + str(alter_pos)
                    )
                    all_unique_lemmas.insert(alter_pos, [])

                # reset lemma altering positions
                last_alter_lemline_at = []

                self.logger.debug(
                    filename + ": transliteration " + str(last_transliteration_line)
                )
                self.logger.debug(
                    "ebl transliteration"
                    + str(last_transliteration)
                    + " "
                    + str(len(last_transliteration))
                )
                self.logger.debug(
                    "all_unique_lemmata "
                    + str(all_unique_lemmas)
                    + " "
                    + str(len(all_unique_lemmas))
                )

                # join oracc_word with ebl unique lemmata
                oracc_word_ebl_lemmas = dict()
                cnt = 0
                if len(last_transliteration) != len(all_unique_lemmas):
                    self.logger.error(
                        "Transiteration and Lemmatization don't have equal length!!"
                    )
                    error_lines.append(
                        filename + ": transliteration " + str(last_transliteration_line)
                    )

                result["last_transliteration"] = last_transliteration
                result["all_unique_lemmas"] = all_unique_lemmas

                for oracc_word in last_transliteration:
                    oracc_word_ebl_lemmas[oracc_word] = all_unique_lemmas[cnt]
                    cnt += 1

                # join ebl transliteration with lemma line:
                ebl_lines = self.get_ebl_transliteration(last_transliteration_line)

                for token in ebl_lines.lines[0].content:
                    unique_lemma = []
                    if token.value in oracc_word_ebl_lemmas:
                        unique_lemma = oracc_word_ebl_lemmas[token.value]

                    if len(unique_lemma) == 0:
                        lemma_line.append(LemmatizationToken(token.value, None))
                    else:
                        lemma_line.append(
                            LemmatizationToken(token.value, tuple(unique_lemma))
                        )
                result["lemmatization"].append(tuple(lemma_line))

            elif line["c_type"] == "text_line":

                    # skip "DIŠ"
                    oracc_words = []
                    for entry in line["c_array"]:
                        if entry != "DIŠ":
                            oracc_words.append(entry)

                    last_transliteration_line = line["c_line"]
                    last_transliteration = oracc_words
                    last_alter_lemline_at = line["c_alter_lemline_at"]
                    result["transliteration"].append(line["c_line"])

            elif line["c_type"] != "empty_line" : # import all other lines
                result["transliteration"].append(line["c_line"])
                result["lemmatization"].append(line["c_line"])





        return result

    def insert_into_db(self, ebl_lines, filename):

        context = create_context()
        transliteration_factory = context.get_transliteration_update_factory()
        updater = context.get_fragment_updater()

        cdli_number = self.get_cdli_number(ebl_lines["control_lines"])
        museum_number = self.get_museum_number_by_cdli_number(cdli_number)

        if museum_number is None:
            self.logger.warning(
                "No museum number to cdli number'"
                + cdli_number
                + "' found. Trying to parse from original file..."
            )
            try:
                museum_number_split = self.get_museum_number(ebl_lines["control_lines"])
                parse_museum_number(museum_number_split.strip())
                museum_number = museum_number_split
            except Exception:
                self.logger.error(
                    "Could not find valid museum number in '" + filename + "'"
                )

        skip = False
        while museum_number is None:
            museum_number_input = input(
                "Please enter a valid museum number (enter 'skip' to skip this file): "
            )
            try:
                if museum_number_input == "skip":
                    skip = True
                    break
                parse_museum_number(museum_number_input)
                museum_number = museum_number_input
                self.logger.info("Museum number '" + museum_number + "' is valid!")
            except Exception:
                pass

        if skip:
            failed.append(filename + " could not be imported: Museum number not found")
            self.logger.error("Museum number not found")
            self.logger.info(
                Util.print_frame('Conversion of "' + filename + '.atf" failed')
            )
            return

        try:

            # insert transliteration
            self.insert_translitertions(
                transliteration_factory,
                updater,
                ebl_lines["transliteration"],
                museum_number,
            )
            # insert lemmatization
            self.insert_lemmatization(
                updater, ebl_lines["lemmatization"], museum_number
            )

            success.append(filename + " successfully imported")
            self.logger.info(
                Util.print_frame('Conversion of "' + filename + '.atf" finished')
            )

        except Exception as e:
            self.logger.error(filename + " could not be imported: " + str(e))
            failed.append(filename + " could not be imported: " + str(e))

    def start(self):

        self.logger.info("Atf-Importer started...")

        # cli arguments

        parser = argparse.ArgumentParser(
            description="Converts ATF-files to eBL-ATF standard."
        )
        parser.add_argument(
            "-i", "--input", required=True, help="path of the input directory"
        )
        parser.add_argument(
            "-l", "--logdir", required=True, help="path of the log files directory"
        )
        parser.add_argument(
            "-g", "--glossary", required=True, help="path to the glossary file"
        )

        args = parser.parse_args()

        # parse glossary
        self.lemmas_cfforms, self.cfforms_senses, self.cfform_guideword = self.parse_glossary(
            args.glossary
        )


        # read atf files from input folder
        for filepath in glob.glob(os.path.join(args.input, "*.atf")):

            with open(filepath, "r"):

                filepath = filepath.replace("\\", "/")

                split = filepath.split("/")
                filename = split[-1]
                filename = filename.split(".")[0]
                # convert all lines
                self.atf_preprocessor = ATFPreprocessor(args.logdir)
                converted_lines = self.atf_preprocessor.convert_lines(
                    filepath, filename
                )

                self.logger.info(
                    Util.print_frame("Formatting to EBL-ATF of " + filename + ".atf")
                )
                ebl_lines = self.convert_to_ebl_lines(converted_lines, filename)
                # insert result into database
                self.logger.info(
                    Util.print_frame(
                        "Inserting converted lines of " + filename + ".atf into db"
                    )
                )
                self.insert_into_db(ebl_lines, filename)

            if args.logdir:

                with open(
                    args.logdir + "not_lemmatized.txt", "w", encoding="utf8"
                ) as outputfile:
                    for key in not_lemmatized:
                        outputfile.write(key + "\n")

                with open(
                    args.logdir + "error_lines.txt", "w", encoding="utf8"
                ) as outputfile:
                    for key in error_lines:
                        outputfile.write(key + "\n")

                with open(
                    args.logdir + "not_imported.txt", "w", encoding="utf8"
                ) as outputfile:
                    for entry in failed:
                        outputfile.write(entry + "\n")

                with open(
                    args.logdir + "imported.txt", "w", encoding="utf8"
                ) as outputfile:
                    for entry in success:
                        outputfile.write(entry + "\n")


if __name__ == "__main__":
    a = ATFImporter()
    a.start()
