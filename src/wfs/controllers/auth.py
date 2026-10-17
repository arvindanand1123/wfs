from fastapi import APIRouter

from wfs.controllers.deps import Credentials, unauthenticated
from wfs.models.serializers import TokenSerializer
from wfs.models.state import UnknownKeyError, get_keypair

router = APIRouter(tags=["auth"])


@router.post("/login")
def login(public_key: Credentials):
    try:
        token, expires_in = get_keypair().issue_token(public_key)
    except UnknownKeyError as e:
        raise unauthenticated(str(e)) from e
    return TokenSerializer().serialize(dict(access_token=token, expires_in=expires_in))
