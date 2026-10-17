import io
import mimetypes

from wfs.drivers.s3 import get_driver

DEFAULT_FILE_TYPE = "application/octet-stream"

DEFAULT_URL_EXPIRY = 3600

DEFAULT_URL_METHOD = "get"

SIGNED_URL_METHODS = dict(get="get_object", put="put_object")


class UnsupportedMethodError(ValueError):
    """Raised when a signed URL is requested for an unsupported HTTP method."""


def guess_file_type(filename):
    file_type, _encoding = mimetypes.guess_type(filename)
    return file_type or DEFAULT_FILE_TYPE


class Object:
    def __init__(self, filename, data=None, file_type=None):
        self.filename = filename
        self.data = data
        self.file_type = file_type or guess_file_type(filename)

    @property
    def key(self):
        return self.filename

    def stream(self):
        if isinstance(self.data, bytes | bytearray | memoryview):
            return io.BytesIO(self.data)
        return self.data

    def __repr__(self):
        return f"Object(filename={self.filename!r}, file_type={self.file_type!r})"

    def push_obj(self):
        driver = get_driver()
        data = self.stream()
        driver.upload_file(self.key, data, content_type=self.file_type)
        return self.key

    def pull_obj(self):
        self.data = get_driver().download_file(self.key)
        return self.data

    def exists(self):
        return get_driver().file_exists(self.key)

    def get_signed_url(self, expires_in=DEFAULT_URL_EXPIRY, method=DEFAULT_URL_METHOD):
        client_method = SIGNED_URL_METHODS.get(str(method).lower())
        if client_method is None:
            raise UnsupportedMethodError(f"unsupported method: {method!r}")
        driver = get_driver()
        return driver.generate_url(self.key, expires_in=expires_in, client_method=client_method)
