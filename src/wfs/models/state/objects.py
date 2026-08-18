import io
import mimetypes

from wfs.drivers.s3 import get_driver

DEFAULT_FILE_TYPE = "application/octet-stream"

DEFAULT_URL_EXPIRY = 3600


def guess_file_type(filename):
    file_type, _encoding = mimetypes.guess_type(filename)
    return file_type or DEFAULT_FILE_TYPE


class Object:
    def __init__(self, filename, data, file_type=None):
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

    def get_upload_url(self, expires_in=DEFAULT_URL_EXPIRY):
        driver = get_driver()
        return driver.generate_url(self.key, expires_in=expires_in)
