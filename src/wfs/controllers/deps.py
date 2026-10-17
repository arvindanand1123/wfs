from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from wfs.models.state import InvalidTokenError, get_keypair

bearer_scheme = HTTPBearer(auto_error=False)


def unauthenticated(detail):
    return HTTPException(status.HTTP_401_UNAUTHORIZED, detail=detail, headers={"WWW-Authenticate": "Bearer"})


def require_credentials(credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)]):
    if credentials is None or not credentials.credentials.strip():
        raise unauthenticated("missing bearer credentials")
    return credentials.credentials


def require_token(token: Annotated[str, Depends(require_credentials)]):
    try:
        return get_keypair().verify_token(token)
    except InvalidTokenError as e:
        raise unauthenticated(str(e)) from e


Credentials = Annotated[str, Depends(require_credentials)]

Claims = Annotated[dict, Depends(require_token)]
