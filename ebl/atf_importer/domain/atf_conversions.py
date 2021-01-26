import re

# pyre-ignore[21]
from lark import Visitor
from lark import lexer


class Convert_Line_Dividers(Visitor):  # pyre-ignore[11]
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
        "á": "a",
        "é": "e",
        "í": "i",
        "ú": "u",
        "Á": "A",
        "É": "E",
        "Ì": "I",
        "Ú": "U",
    }

    def oracc_atf_text_line__logogram_name_part(self, tree):
        assert tree.data == "oracc_atf_text_line__logogram_name_part"
        cnt = 0
        for child in tree.children:

            pattern = re.compile("[ÁÉÍÙ]")
            matches = pattern.search(child)

            if matches is not None:

                match = matches.group(0)
                try:
                    next_char = tree.children[cnt + 1]
                    tree.children[cnt] = self.replacement_chars[match]
                    tree.children[cnt + 1] = next_char + "₃"

                except Exception:
                    tree.children[cnt] = self.replacement_chars[match] + "₂"

            cnt = cnt + 1

    def oracc_atf_text_line__value_name_part(self, tree):
        assert tree.data == "oracc_atf_text_line__value_name_part"
        cnt = 0
        for child in tree.children:

            pattern = re.compile("[áíéú]")
            matches = pattern.search(child)

            if matches is not None:

                match = matches.group(0)
                try:
                    next_char = tree.children[cnt + 1]
                    tree.children[cnt] = self.replacement_chars[match]
                    tree.children[cnt + 1] = next_char + "₃"

                except Exception:
                    tree.children[cnt] = self.replacement_chars[match] + "₂"

            cnt = cnt + 1


class Strip_Signs(Visitor):
    def oracc_atf_text_line__uncertain_sign(self, tree):
        assert tree.data == "oracc_atf_text_line__uncertain_sign"
        if tree.children[0] == "$":
            tree.children[0] = ""


class DFS(Visitor):
    def visit_topdown(self, tree, result):

        if not hasattr(tree, "data"):
            return result

        for child in tree.children:
            if isinstance(child, str) or isinstance(child, int):
                result += child
            result = DFS().visit_topdown(child, result)
        return result


class Line_Serializer(Visitor):
    line = ""

    def text_line(self, tree):
        assert tree.data == "text_line"
        result = DFS().visit_topdown(tree, "")
        self.line += " " + result
        return result

    def dollar_line(self, tree):
        assert tree.data == "dollar_line"
        result = DFS().visit_topdown(tree, "")
        self.line += " " + result
        return result

    def control_line(self, tree):
        assert tree.data == "control_line"
        result = DFS().visit_topdown(tree, "")
        self.line += " " + result
        return result


class Get_Line_Number(Visitor):
    nr = ""

    def oracc_atf_text_line__single_line_number(self, tree):
        assert tree.data == "oracc_atf_text_line__single_line_number"
        result = DFS().visit_topdown(tree, "")
        self.nr += result

        return result


class Get_Words(Visitor):
    wordcounter = 0
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

            if isinstance(child, lexer.Token):
                word += child
            else:
                word += DFS().visit_topdown(child, "")

        self.result.append(word)
        self.wordcounter = self.wordcounter + 1


class Get_Lemma_Values_and_Guidewords(Visitor):
    result = []
    additional_lemmata = False
    oracc_pos_tags = ["oracc_atf_lem_line__e_pos_tag", "oracc_atf_lem_line__pos_tag"]

    def oracc_atf_lem_line__lemma(self, tree):

        assert tree.data == "oracc_atf_lem_line__lemma"
        guide_word = ""
        pos_tag = ""
        i = 0
        cl = len(tree.children)
        lemmata = []
        for child in tree.children:

            # collect additional lemmata and guidwords
            if child.data == "oracc_atf_lem_line__additional_lemmata":

                for a_child in child.children:
                    if hasattr(a_child, "data"):

                        if a_child.data == "oracc_atf_lem_line__additional_lemma":
                            acl = len(a_child.children)
                            j = 0
                            for b_child in a_child.children:
                                additional_lemma_value = ""
                                additional_guide_word = ""
                                additional_pos_tag = ""
                                if b_child.data == "oracc_atf_lem_line__value_part":
                                    additional_lemma_value = DFS().visit_topdown(
                                        b_child, ""
                                    )
                                    if (
                                        acl > 1
                                        and a_child.children[j + 1].data
                                        == "oracc_atf_lem_line__guide_word"
                                    ):
                                        additional_guide_word = DFS().visit_topdown(
                                            a_child.children[j + 1], ""
                                        )
                                if additional_lemma_value != "":
                                    # find pos tag
                                    if (
                                        tree.children[j + 2]
                                        and tree.children[j + 2].data
                                        in self.oracc_pos_tags
                                    ):
                                        additional_pos_tag = DFS().visit_topdown(
                                            tree.children[j + 2], ""
                                        )

                                    lemmata.append(
                                        (
                                            additional_lemma_value,
                                            additional_guide_word,
                                            additional_pos_tag,
                                        )
                                    )

            # find actual lemma and guidewords
            if child.data == "oracc_atf_lem_line__value_part":
                lemma_value = DFS().visit_topdown(child, "")
                if (
                    cl > 1
                    and tree.children[i + 1].data == "oracc_atf_lem_line__guide_word"
                ):
                    guide_word = DFS().visit_topdown(tree.children[i + 1], "")
                    # find pos tag
                    if (
                        tree.children[i + 2]
                        and tree.children[i + 2].data in self.oracc_pos_tags
                    ):
                        pos_tag = DFS().visit_topdown(tree.children[i + 2], "")

                lemmata.append((lemma_value, guide_word, pos_tag))
                self.result.append(lemmata)
            i = i + 1
