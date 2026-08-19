import atexit
import os
from functools import cache
from unittest import mock
from uuid import uuid4

import boto3
from moto.server import ThreadedMotoServer

from tests.externals.base import ExternalMock
from wfs.config import get_settings
from wfs.drivers.s3 import get_driver

CREDENTIALS = dict(aws_access_key_id="testing", aws_secret_access_key="testing", region_name="us-east-1")


@cache
def _endpoint():
    server = ThreadedMotoServer(ip_address="127.0.0.1", port=0, verbose=False)
    server.start()
    atexit.register(server.stop)
    host, port = server.get_host_and_port()
    return f"http://{host}:{port}"


class S3Mock(ExternalMock):
    name = "s3"

    def __init__(self):
        self.bucket = f"wfs-test-{uuid4().hex[:12]}"
        self.endpoint = None
        self.boto = None
        self._env = None

    def register(self, client):
        self.endpoint = _endpoint()
        self._env = mock.patch.dict(
            os.environ,
            dict(
                S3_ENDPOINT_URL=self.endpoint,
                S3_ACCESS_KEY_ID=CREDENTIALS["aws_access_key_id"],
                S3_SECRET_ACCESS_KEY=CREDENTIALS["aws_secret_access_key"],
                S3_REGION=CREDENTIALS["region_name"],
                S3_BUCKET=self.bucket,
            ),
        )
        self._env.start()
        self._clear_caches()
        self.boto = boto3.client("s3", endpoint_url=self.endpoint, **CREDENTIALS)
        self.boto.create_bucket(Bucket=self.bucket)

    def unregister(self):
        if self._env is not None:
            self._env.stop()
            self._env = None
        self._clear_caches()

    def read(self, key):
        return self.get(key)["Body"].read()

    def content_type(self, key):
        return self.get(key)["ContentType"]

    def keys(self):
        listing = self.boto.list_objects_v2(Bucket=self.bucket)
        return [item["Key"] for item in listing.get("Contents", [])]

    def get(self, key):
        return self.boto.get_object(Bucket=self.bucket, Key=key)

    @staticmethod
    def _clear_caches():
        # get_settings and get_driver are lru_cache'd, so a driver built under
        # one test's env would otherwise outlive it.
        get_settings.cache_clear()
        get_driver.cache_clear()
