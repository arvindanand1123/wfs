import io
from functools import cache

import boto3
from botocore.config import Config

from wfs.config import get_settings


class S3Driver:
    def __init__(self, settings):
        self._bucket = settings.s3_bucket
        self._client = boto3.client(
            "s3",
            endpoint_url=settings.s3_endpoint_url or None,
            aws_access_key_id=settings.s3_access_key_id or None,
            aws_secret_access_key=settings.s3_secret_access_key or None,
            region_name=settings.s3_region,
            # R2 only accepts SigV4-signed requests.
            config=Config(signature_version="s3v4"),
        )

    def upload_file(self, key, data, content_type=None):
        if isinstance(data, bytes | bytearray):
            data = io.BytesIO(data)
        extra_args = dict()
        if content_type is not None:
            extra_args["ContentType"] = content_type
        self._client.upload_fileobj(data, self._bucket, key, ExtraArgs=extra_args)

    def generate_url(self, key, expires_in=3600):
        return self._client.generate_presigned_url(
            "get_object",
            Params=dict(Bucket=self._bucket, Key=key),
            ExpiresIn=expires_in,
        )


@cache
def get_driver():
    return S3Driver(get_settings())
