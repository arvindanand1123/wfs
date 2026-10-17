from fastapi import APIRouter, Depends, HTTPException, status

from wfs.controllers.deps import require_token
from wfs.models.serializers import SignedUrlSerializer
from wfs.models.state import DEFAULT_URL_EXPIRY, DEFAULT_URL_METHOD, Object, UnsupportedMethodError

router = APIRouter(prefix="/files", tags=["files"], dependencies=[Depends(require_token)])

MAX_URL_EXPIRY = 604800


@router.get("/get-signed-url")
def get_signed_url(filename: str, method: str = DEFAULT_URL_METHOD, expires_in: int = DEFAULT_URL_EXPIRY):
    if not filename.strip():
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail="filename may not be empty")
    if not 0 < expires_in <= MAX_URL_EXPIRY:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=f"expires_in must be between 1 and {MAX_URL_EXPIRY}")
    try:
        url = Object(filename).get_signed_url(expires_in=expires_in, method=method)
    except UnsupportedMethodError as e:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_CONTENT, detail=str(e)) from e
    return SignedUrlSerializer().serialize(dict(filename=filename, method=method.upper(), url=url, expires_in=expires_in))
