from typing import NewType
import attr

Base64 = NewType("Base64", str)

@attr.s(auto_attribs=True, frozen=True)
class CroppedSignImage:
    sign_id: str
    image: Base64