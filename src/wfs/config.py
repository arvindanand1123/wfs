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
        self.private_key_name = os.getenv("PRIVATE_KEY_NAME", "keys/pk.pem")
        self.public_key_name = os.getenv("PUBLIC_KEY_NAME", "keys/pub.pem")
        self.jwt_issuer = os.getenv("JWT_ISSUER", "wfs")
        self.jwt_ttl = int(os.getenv("JWT_TTL", "3600"))


@cache
def get_settings():
    return Settings()
