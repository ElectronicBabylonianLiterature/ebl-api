import pytest
from ebl.fragmentarium.application.cropped_sign_image import (
    CroppedSign,
    CroppedSignSchema,
)
from ebl.fragmentarium.domain.fragment import Script


@pytest.mark.parametrize(
    "cropped_sign,serialized",
    [
        (
            CroppedSign("image id", Script(), "label"),
            {
                "imageId": "image id",
                "script": {
                    "period": "None",
                    "periodModifier": "None",
                    "uncertain": False,
                },
                "label": "label",
            },
        ),
    ],
)
def test_schema(cropped_sign, serialized):
    assert CroppedSignSchema().load(serialized) == cropped_sign
    assert CroppedSignSchema().dump(cropped_sign) == serialized
