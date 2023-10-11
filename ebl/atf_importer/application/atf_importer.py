import argparse
import glob
import logging
import os
import re

from pymongo import MongoClient

from ebl.app import create_context
from ebl.atf_importer.domain.atf_preprocessor import ATFPreprocessor
from ebl.atf_importer.domain.atf_preprocessor_util import Util
from ebl.fragmentarium.application.fragment_updater import FragmentUpdater
from ebl.fragmentarium.application.transliteration_update_factory import (
    TransliterationUpdateFactory,
)
from ebl.fragmentarium.web.dtos import parse_museum_number
from ebl.lemmatization.domain.lemmatization import Lemmatization, LemmatizationToken
from ebl.transliteration.domain.atf import Atf
from ebl.transliteration.domain.lark_parser import parse_atf_lark
from ebl.users.domain.user import AtfImporterUser


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

NOUN_POS_TAGS = [
    "AN",
    "CN",
    "DN",
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
]

STYLES = {"Oracc ATF": 0, "Oracc C-ATF": 1, "CDLI": 2}

not_lemmatized = {}
error_lines = []
success = []
failed = []


class ATFImporter:
    def __init__(self, db):
        logging.basicConfig(level=logging.DEBUG)

        self.logger = logging.getLogger("Atf-Importer")
        self.atf_preprocessor = ATFPreprocessor("../logs", "oracc")

        self.lemgwpos_cf = None
        self.forms_senses = None
        self.lemposgw_cfgw = None
        self.db = db
        self.username = None

    @staticmethod
    def get_ebl_transliteration(line):
        return parse_atf_lark(line)

    def get_ebl_lemmata(self, orrac_lemma_tupel, all_unique_lemmas):
        try:
            oracc_lemma = None
            oracc_guideword = None
            oracc_pos_tag = None

            unique_lemmas = []
            for ol_tuple in orrac_lemma_tupel:
                oracc_lemma = ol_tuple[0]
                oracc_guideword = ol_tuple[1]
                oracc_pos_tag = ol_tuple[2]

                oracc_lemma = oracc_lemma.strip()
                oracc_guideword = oracc_guideword.strip().rstrip("]").lstrip("[")

                if "//" in oracc_guideword:
                    oracc_guideword = oracc_guideword.split("//")[0]

                if oracc_guideword == "":
                    if oracc_lemma not in not_lemmatized:
                        not_lemmatized[oracc_lemma] = True
                    self.logger.warning(
                        "Incompatible lemmatization: "
                        f"No guideWord to oracc lemma '{oracc_lemma}' present"
                    )

                # if "X" or "u" or "n" then add [] and return
                if oracc_lemma in ["X", "u", "n"]:
                    self.logger.warning(
                        f"Oracc lemma was '{oracc_lemma}' ->  here no lemmatization"
                    )
                    all_unique_lemmas.append(unique_lemmas)
                    return

                if oracc_lemma[0] == "+":
                    oracc_lemma = oracc_lemma[1:]

                    # replace "ʾ","'" to match db query
                    oracc_lemma = oracc_lemma.replace("ʾ", "'")

                    for entry in self.db.get_collection("words").find(
                        {
                            "oraccWords.lemma": oracc_lemma,
                            "oraccWords.guideWord": oracc_guideword,
                        },
                        {"_id"},
                    ):
                        if entry["_id"] not in unique_lemmas:
                            unique_lemmas.append(entry["_id"])

                    if not unique_lemmas:
                        for entry in self.db.get_collection("words").find(
                            {
                                "forms.lemma": [oracc_lemma],
                                "guideWord": oracc_guideword,
                            },
                            {"_id"},
                        ):
                            if entry["_id"] not in unique_lemmas:
                                unique_lemmas.append(entry["_id"])

                        for entry in self.db.get_collection("words").find(
                            {"lemma": [oracc_lemma], "guideWord": oracc_guideword},
                            {"_id"},
                        ):
                            if entry["_id"] not in unique_lemmas:
                                unique_lemmas.append(entry["_id"])

                else:
                    try:
                        gloss_cf_gw = self.lemposgw_cfgw[
                            oracc_lemma + oracc_pos_tag + oracc_guideword
                        ]
                        if gloss_cf_gw is not None:
                            citation_form = gloss_cf_gw[0]
                            guideword = gloss_cf_gw[1]

                            if "//" in guideword:
                                guideword = guideword.split("//")[0]

                            unique_lemmas.extend(
                                entry["_id"]
                                for entry in self.db.get_collection("words").find(
                                    {
                                        "oraccWords.lemma": citation_form,
                                        "oraccWords.guideWord": guideword,
                                    },
                                    {"_id"},
                                )
                            )
                            if not unique_lemmas:
                                for entry in self.db.get_collection("words").find(
                                    {
                                        "forms.lemma": [citation_form],
                                        "guideWord": guideword,
                                    },
                                    {"_id"},
                                ):
                                    if entry["_id"] not in unique_lemmas:
                                        unique_lemmas.append(entry["_id"])

                                for entry in self.db.get_collection("words").find(
                                    {"lemma": [citation_form], "guideWord": guideword},
                                    {"_id"},
                                ):
                                    if entry["_id"] not in unique_lemmas:
                                        unique_lemmas.append(entry["_id"])

                    except Exception:
                        if oracc_lemma not in not_lemmatized:
                            not_lemmatized[oracc_lemma] = True

                            self.logger.warning(
                                "Incompatible lemmatization: No citation "
                                "form or guideword (by sense) found in the "
                                f"glossary for '{oracc_lemma}'"
                            )

            # set as noun
            if not unique_lemmas and oracc_pos_tag in NOUN_POS_TAGS:
                unique_lemmas.extend(
                    entry["_id"]
                    for entry in self.db.get_collection("words").find(
                        {"oraccWords.lemma": oracc_lemma}, {"_id"}
                    )
                )
            # all attempts to find a ebl lemma failed
            if not unique_lemmas:
                if oracc_lemma not in not_lemmatized:
                    not_lemmatized[oracc_lemma] = True
                self.logger.warning(
                    "Incompatible lemmatization: No eBL word found to oracc lemma or "
                    f"guide word ({oracc_lemma} : {oracc_guideword})"
                )

            all_unique_lemmas.append(unique_lemmas)

        except Exception as e:
            self.logger.exception(e)

    @staticmethod
    def parse_glossary(path):
        lemgwpos_cf = {}
        forms_senses = {}
        lemposgw_cfgw = {}

        with open(path, "r", encoding="utf8") as f:
            for line in f:
                if line.startswith("@entry"):
                    lemmas = []
                    split = line.split(" ", 2)
                    cfform = split[1]
                    cfform = cfform.replace("ʾ", "'")
                    cfform = cfform.strip()

                    p = re.compile(r"\[(.*)\] (.*)")
                    matches = p.findall(split[2])
                    guideword = matches[0][0]
                    guideword = guideword.rstrip("]").lstrip("[")

                    pos_tag = matches[0][1]

                if line.startswith("@form"):
                    split = line.split(" ")
                    lemma = split[2].lstrip("$").rstrip("\n")
                    lemmas.append(lemma)
                    # lemgwpos_cf[lemma+guideword+pos_tag] = cfform.strip()
                    lemgwpos_cf[lemma + pos_tag] = cfform.strip()

                if line.startswith("@sense"):
                    split = line.split(" ", 2)

                    for s in split:
                        if s in POS_TAGS:
                            pos_tag = s
                    split2 = line.split(pos_tag)
                    sense = split2[1].rstrip("\n")

                    for lem in lemmas:
                        if lem not in forms_senses:
                            forms_senses[lem] = [pos_tag + sense.strip()]
                        else:
                            forms_senses[lem].append(pos_tag + sense.strip())

                        lemposgw_cfgw[lem + pos_tag + sense.strip()] = (
                            cfform,
                            guideword,
                        )

        return lemgwpos_cf, forms_senses, lemposgw_cfgw

    def insert_translitertions(
        self,
        transliteration_factory: TransliterationUpdateFactory,
        updater: FragmentUpdater,
        transliterations,
        museum_number,
    ) -> None:
        converted_transliteration = "\n".join(transliterations)
        transliteration = transliteration_factory.create(Atf(converted_transliteration))
        user = AtfImporterUser(self.username)
        updater.update_transliteration(
            parse_museum_number(museum_number), transliteration, user
        )

    def insert_lemmatization(
        self, updater: FragmentUpdater, lemmatization, museum_number
    ):
        lemmatization = Lemmatization(tuple(lemmatization))
        user = AtfImporterUser(self.username)
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
            {"externalNumbers.cdliNumber": cdli_number}, {"museumNumber"}
        ):
            return entry["_id"]

        return None

    def convert_to_ebl_lines(
        self, converted_lines, filename, test=False, test_lemmata=None
    ):
        if test_lemmata is None:
            test_lemmata = []
        last_transliteration_line = ""
        last_alter_lemline_at = []
        last_transliteration = []

        result = {"transliteration": [], "lemmatization": [], "control_lines": []}
        for line in converted_lines:
            if line["c_type"] == "control_line":
                result["control_lines"].append(line)

            elif line["c_type"] == "lem_line":
                all_unique_lemmas = []
                lemma_line = []
                if not test:
                    for oracc_lemma_tupel in line["c_array"]:
                        # get unique lemmata from ebl database
                        self.get_ebl_lemmata(oracc_lemma_tupel, all_unique_lemmas)
                else:
                    all_unique_lemmas = test_lemmata

                for alter_pos in last_alter_lemline_at:
                    self.logger.warning(
                        f"Adding placeholder to lemma line at position:{str(alter_pos)}"
                    )
                    all_unique_lemmas.insert(alter_pos, [])

                # reset lemma altering positions
                last_alter_lemline_at = []

                self.logger.debug(
                    f"{filename}: transliteration {str(last_transliteration_line)}"
                )
                self.logger.debug(
                    f"ebl transliteration{str(last_transliteration)} "
                    f"{len(last_transliteration)}"
                )
                self.logger.debug(
                    f"all_unique_lemmata {str(all_unique_lemmas)} {len(all_unique_lemmas)}"
                )

                # join oracc_word with ebl unique lemmata
                oracc_word_ebl_lemmas = {}
                if len(last_transliteration) != len(all_unique_lemmas):
                    self.logger.error(
                        "Transiteration and Lemmatization don't have equal length!!"
                    )
                    error_lines.append(
                        f"{filename}: transliteration {str(last_transliteration_line)}"
                    )

                result["last_transliteration"] = last_transliteration
                result["all_unique_lemmas"] = all_unique_lemmas

                oracc_words = []
                for cnt, oracc_word in enumerate(last_transliteration):
                    oracc_word_ebl_lemmas[cnt] = all_unique_lemmas[cnt]
                    oracc_words.append(oracc_word)
                # join ebl transliteration with lemma line:
                ebl_lines = self.get_ebl_transliteration(last_transliteration_line)

                word_cnt = 0
                for token in ebl_lines.lines[0].content:
                    unique_lemma = []
                    if token.value in oracc_words:
                        unique_lemma = oracc_word_ebl_lemmas[word_cnt]
                        word_cnt += 1

                    if len(unique_lemma) == 0:
                        lemma_line.append(LemmatizationToken(token.value, None))
                    else:
                        lemma_line.append(
                            LemmatizationToken(token.value, tuple(unique_lemma))
                        )
                result["lemmatization"].append(tuple(lemma_line))

            elif line["c_type"] == "text_line":
                # skip "DIŠ"
                oracc_words = [entry for entry in line["c_array"] if entry != "DIŠ"]
                last_transliteration_line = line["c_line"]
                last_transliteration = oracc_words
                last_alter_lemline_at = line["c_alter_lemline_at"]
                result["transliteration"].append(last_transliteration_line)
            elif line["c_type"] != "empty_line":  # import all other lines
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
                + "' found. Trying to parse from the original file..."
            )
            try:
                museum_number_split = self.get_museum_number(ebl_lines["control_lines"])
                parse_museum_number(museum_number_split.strip())
                museum_number = museum_number_split
            except Exception:
                self.logger.error(f"Could not find a valid museum number in '{filename}'")

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
                self.logger.info(f"Museum number '{museum_number}' is valid!")
            except Exception:
                pass

        if skip:
            failed.append(f"{filename} could not be imported: Museum number not found")
            self.logger.error("Museum number not found")
            self.logger.info(Util.print_frame(f'Conversion of "{filename}.atf" failed'))
            return

        if not document_has_property("fragments", "text.lines.0"):
            try:
                # Insert transliteration
                self.insert_translitertions(
                    transliteration_factory,
                    updater,
                    ebl_lines["transliteration"],
                    museum_number,
                )
                # Insert lemmatization
                self.insert_lemmatization(
                    updater, ebl_lines["lemmatization"], museum_number
                )

                success.append(f"{filename} successfully imported")
                self.logger.info(
                    Util.print_frame(
                        'Conversion of "'
                        + filename
                        + '.atf" finished (museum number "'
                        + museum_number
                        + '")'
                    )
                )
            except (Exception, Exception) as e:
                self.logger.error(f"{filename} could not be imported: {str(e)}")
                failed.append(f"{filename} could not be imported: {str(e)}")

    def start(self):
        self.logger.info("Atf-Importer started...")

        # cli arguments

        parser = argparse.ArgumentParser(
            description="Converts ATF-files to eBL-ATF standard."
        )
        parser.add_argument(
            "-i", "--input", required=True, help="Path of the input directory."
        )
        parser.add_argument(
            "-l", "--logdir", required=True, help="Path of the log files directory."
        )
        parser.add_argument(
            "-g", "--glossary", required=True, help="Path to the glossary file."
        )

        parser.add_argument(
            "-a",
            "--author",
            required=False,
            help="Name of the author of the imported fragements. \nIf not specified a "
            "name needs to be entered manually for every fragment.",
        )

        parser.add_argument(
            "-s",
            "--style",
            required=False,
            help="Specify import style by entering one of the following: |Oracc "
            "ATF|Oracc C-ATF|CDLI"
            "If omitted defaulting to oracc.",
        )

        args = parser.parse_args()

        self.username = args.author

        style = STYLES[args.style] if args.style in STYLES else 0
        import_style = "Oracc ATF" if args.style is None else args.style
        # parse glossary
        self.lemgwpos_cf, self.forms_senses, self.lemposgw_cfgw = self.parse_glossary(
            args.glossary
        )

        # read atf files from input folder
        for filepath in glob.glob(os.path.join(args.input, "*.atf")):
            with open(filepath, "r"):
                filepath = filepath.replace("\\", "/")

                split = filepath.split("/")
                filename = split[-1]
                filename = filename.split(".")[0]

                self.logger.info(
                    Util.print_frame(f"Importing {filename}.atf as: {import_style}")
                )
                if args.author is None:
                    self.username = input(
                        f"Please enter the fragments author to import {filename}: "
                    )
                # convert all lines
                self.atf_preprocessor = ATFPreprocessor(args.logdir, style)
                converted_lines = self.atf_preprocessor.convert_lines(
                    filepath, filename
                )

                self.logger.info(
                    Util.print_frame(f"Formatting to EBL-ATF of {filename}.atf")
                )
                ebl_lines = self.convert_to_ebl_lines(converted_lines, filename)
                # insert result into database
                self.logger.info(
                    Util.print_frame(
                        f"Inserting converted lines of {filename}.atf into db"
                    )
                )
                self.insert_into_db(ebl_lines, filename)

            if args.logdir:
                with open(
                    f"{args.logdir}not_lemmatized.txt", "w", encoding="utf8"
                ) as outputfile:
                    for key in not_lemmatized:
                        outputfile.write(key + "\n")

                with open(
                    f"{args.logdir}error_lines.txt", "w", encoding="utf8"
                ) as outputfile:
                    for key in error_lines:
                        outputfile.write(key + "\n")

                with open(
                    f"{args.logdir}not_imported.txt", "w", encoding="utf8"
                ) as outputfile:
                    for entry in failed:
                        outputfile.write(entry + "\n")

                with open(
                    f"{args.logdir}imported.txt", "w", encoding="utf8"
                ) as outputfile:
                    for entry in success:
                        outputfile.write(entry + "\n")


if __name__ == "__main__":
    # connect to eBL-db
    client = MongoClient(os.getenv("MONGODB_URI"))
    db = client.get_database(os.getenv("MONGODB_DB"))
    a = ATFImporter(db)
    a.start()
