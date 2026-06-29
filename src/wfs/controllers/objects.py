"""HTTP routes for object operations (get / put / list / delete).

Skeleton only — handlers should delegate to wfs.core.storage and return
wfs.models.schemas types. Fill these in when the gateway logic is ready.
"""

from fastapi import APIRouter

router = APIRouter(prefix="/objects", tags=["objects"])


# TODO: implement object endpoints, e.g.:
#   @router.get("")           -> list objects
#   @router.get("/{key}")     -> download / stream an object
#   @router.put("/{key}")     -> upload an object
#   @router.delete("/{key}")  -> delete an object
