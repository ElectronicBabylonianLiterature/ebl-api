from marshmallow import Schema, fields, post_load

from ebl.fragment.fragment_info import FragmentInfo


class FragmentInfoSchema(Schema):
    number = fields.String(required=True)
    accession = fields.String(required=True)
    script = fields.String(required=True)
    description = fields.String(required=True)
    editor = fields.String(missing='')
    edition_date = fields.String(data_key='editionDate', missing='')
    matching_lines = fields.List(
        fields.List(fields.String()),
        data_key='matchingLines',
        missing=tuple()
    )

    @post_load
    def make_fragment_info(self, data, **kwargs):
        data['matching_lines'] = tuple(map(tuple, data['matching_lines']))
        return FragmentInfo(**data)
