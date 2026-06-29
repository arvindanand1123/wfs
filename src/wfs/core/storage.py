"""Core storage logic: a thin wrapper around any S3-compatible backend.

Skeleton only. Everything here is backend-agnostic (R2, MinIO, AWS S3, ...) and
driven entirely by wfs.config.Settings, so the rest of the app never talks to
boto3 directly.
"""


class StorageClient:
    """Client for an S3-compatible object store.

    TODO: build a boto3 client from settings and implement
    get_object / put_object / list_objects / delete_object.
    """

    def __init__(self, settings):
        self._settings = settings

    # TODO: def get_object(self, key): ...
    # TODO: def put_object(self, key, data): ...
    # TODO: def list_objects(self, prefix=""): ...
    # TODO: def delete_object(self, key): ...
