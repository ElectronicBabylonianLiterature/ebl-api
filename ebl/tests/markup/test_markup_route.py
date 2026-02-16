import falcon

markup_string = (
    "@bib{RN117@123}"
    "website   the   third   chapter   of   R.   Borger’s "
    "@i{Mesopotamisches Zeichenlexikon} (Alter Orient "
    "und Altes Testament 305. Münster, ²2010). "
    "@url{https://www.hethport.uni-wuerzburg.de/cuneifont/}{Assurbanipal   font}. "
    "contain all glyphs from @i{MesZL}². "
    "Following Borger’s request in @i{MesZL}² p. viii, the very few deviations of "
    '<span   style="color:   #00610F;">different   color</span>.   These '
    "editions,   such   as   the   repeated   paragraph   in   p.   418   (see "
    "@url{https://www.ebl.lmu.de/signs/DIŠ}{here}). "
    "the   digitization   of   his   @i{magnum   opus}   "
    "would   have   made   the   project "
    "The entire @i{MesZL}², not only the third chapter reproduced on this "
    "@url{https://ugarit-verlag.com/en/products/0e8e7ca5d1f5493aa351e3ebc42fb51"
    "4}{this link}"
)

expected = [
    {
        "reference": {
            "id": "RN117",
            "type": "DISCUSSION",
            "pages": "123",
            "notes": "",
            "linesCited": [],
        },
        "type": "BibliographyPart",
    },
    {"text": "website the third chapter of R. Borger’s ", "type": "StringPart"},
    {"text": "Mesopotamisches Zeichenlexikon", "type": "EmphasisPart"},
    {
        "text": " (Alter Orient und Altes Testament 305. Münster, ²2010). ",
        "type": "StringPart",
    },
    {
        "url": "https://www.hethport.uni-wuerzburg.de/cuneifont/",
        "text": "Assurbanipal font",
        "type": "UrlPart",
    },
    {"text": ". contain all glyphs from ", "type": "StringPart"},
    {"text": "MesZL", "type": "EmphasisPart"},
    {"text": "². Following Borger’s request in ", "type": "StringPart"},
    {"text": "MesZL", "type": "EmphasisPart"},
    {
        "text": (
            "² p. viii, the very few deviations of "
            '<span style="color: #00610F;">different color</span>. '
            "These editions, such as the repeated paragraph in p. 418 (see "
        ),
        "type": "StringPart",
    },
    {"url": "https://www.ebl.lmu.de/signs/DIŠ", "text": "here", "type": "UrlPart"},
    {"text": "). the digitization of his ", "type": "StringPart"},
    {"text": "magnum opus", "type": "EmphasisPart"},
    {"text": " would have made the project The entire ", "type": "StringPart"},
    {"text": "MesZL", "type": "EmphasisPart"},
    {"text": "², not only the third chapter reproduced on this ", "type": "StringPart"},
    {
        "url": "https://ugarit-verlag.com/en/products/0e8e7ca5d1f5493aa351e3ebc42fb514",
        "text": "this link",
        "type": "UrlPart",
    },
]


def test_get_markup(client):
    result = client.simulate_get(
        "/markup",
        params={
            "text": markup_string,
        },
    )
    assert result.json == expected
    assert result.status == falcon.HTTP_OK
