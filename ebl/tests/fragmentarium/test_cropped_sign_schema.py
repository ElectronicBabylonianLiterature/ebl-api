import pytest

from ebl.fragmentarium.application.cropped_sign_image import (
    CroppedSign,
    CroppedSignSchema,
)


@pytest.mark.parametrize(
    "cropped_sign,serialized",
    [
        (
            CroppedSign("image id", "label"),
            {
                "imageId": "image id",
                "label": "label",
            },
        ),
    ],
)
def test_schema(cropped_sign, serialized):
    assert CroppedSignSchema().load(serialized) == cropped_sign
    assert CroppedSignSchema().dump(cropped_sign) == serialized
