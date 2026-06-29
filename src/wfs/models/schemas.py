"""Response shapes for the API.

No pydantic — plain classes with custom serializers. Each model exposes a
serialize() method that returns a plain dict for JSON responses.
"""


class ObjectMeta:
    """Metadata describing a stored object."""

    def __init__(self, key, size, etag=None, last_modified=None):
        self.key = key
        self.size = size
        self.etag = etag
        self.last_modified = last_modified

    def serialize(self):
        return {
            "key": self.key,
            "size": self.size,
            "etag": self.etag,
            "last_modified": self.last_modified,
        }


# TODO: add models + serializers as controllers are implemented.
