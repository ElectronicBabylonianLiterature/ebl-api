from typing import Protocol

import falcon

from ebl.users.domain.user import User


class UserContext(Protocol):
    user: User


class UserRequest(falcon.Request):
    context: UserContext
