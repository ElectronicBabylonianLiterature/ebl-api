import base64
import attr
from cairosvg import svg2png
from ebl.signs.infrastructure.mongo_sign_repository import SignDtoSchema
from ebl.transliteration.application.sign_repository import SignRepository


class SignsResource:
    def __init__(self, signs: SignRepository):
        self._signs = signs

    def on_get(self, _req, resp, sign_name):
        sign = self._signs.find(sign_name)
        fosseysBase64 = []
        for fossey in sign.fossey:
            svg = fossey.sign
            if svg != "":
                binary = svg2png(
                    bytestring=svg,
                    output_height=100,
                    parent_width=200,
                    parent_height=200,
                )
                b64 = base64.b64encode(binary).decode("utf-8")
                fosseysBase64.append(attr.evolve(fossey, sign=b64))
            else:
                fosseysBase64.append(fossey)
        attr.evolve(sign, fossey=fosseysBase64)
        resp.media = SignDtoSchema().dump(attr.evolve(sign, fossey=fosseysBase64))


class SignsListResource:
    def __init__(self, signs: SignRepository):
        self.sign_repository = signs

    def on_get(self, req, resp):
        resp.media = self.sign_repository.list_all_signs()


class SignsOrderResource:
    def __init__(self, signs: SignRepository):
        self.sign_repository = signs

    def on_get(self, req, resp, sign_name, sort_era):
        resp.media = self.sign_repository.find_signs_by_order(sign_name, sort_era)


class TransliterationResource:
    def __init__(self, signs: SignRepository):
        self.sign_repository = signs

    def on_get(self, req, resp, line):
        resp.media = self.sign_repository.get_unicode_from_atf(line)
