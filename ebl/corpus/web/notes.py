# class ManuscriptLineDisplaySchema(Schema):
#     old_sigla = fields.Function(
#         lambda line, context: ApiOldSiglumSchema().dump(
#             get_manuscript_field("old_sigla")(line, context), many=True
#         ),
#         data_key="oldSigla",
#     )
#     references = fields.Function(
#         lambda line, context: ApiReferenceSchema().dump(
#             get_manuscript_field("references")(line, context), many=True
#         ),
#     )
#     siglum_disambiguator = fields.Function(
#         get_manuscript_field("siglum_disambiguator"),
#         data_key="siglumDisambiguator",
#     )
#     period_modifier = fields.Function(
#         get_manuscript_field("period_modifier.value"),
#         data_key="periodModifier",
#     )
#     period = fields.Function(
#         get_manuscript_field("period.long_name"),
#     )
#     provenance = fields.Function(
#         get_manuscript_field("provenance.long_name"),
#     )
#     type = fields.Function(
#         get_manuscript_field("type.long_name"),
#     )
#     labels = labels()
#     line = fields.Nested(OneOfLineSchema, required=True)
#     paratext = fields.Nested(OneOfLineSchema, many=True, required=True)

#     full_manuscript = fields.Function(
#         lambda line, context: ApiManuscriptSchema().dump(
#             context["manuscripts"][line.manuscript_id]
#         ),
#         data_key="fullManuscript",
#     )
