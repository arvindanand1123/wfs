import os
from functools import cache


class Settings:
    def __init__(self):
        self.s3_endpoint_url = os.getenv("S3_ENDPOINT_URL", "")
        self.s3_access_key_id = os.getenv("S3_ACCESS_KEY_ID", "")
        self.s3_secret_access_key = os.getenv("S3_SECRET_ACCESS_KEY", "")
        self.s3_region = os.getenv("S3_REGION", "auto")
        self.s3_bucket = os.getenv("S3_BUCKET", "")
        self.log_level = os.getenv("LOG_LEVEL", "info")


@cache
def get_settings():
    return Settings()
