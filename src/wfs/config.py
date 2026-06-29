"""Application settings, read from environment variables.

No pydantic — just plain os.environ. Locally, direnv loads .env into the
environment (see .envrc); in the container, Cloudflare provides the env.
"""

import os
from functools import lru_cache


class Settings:
    def __init__(self):
        # --- Upstream S3-compatible backend ---
        self.s3_endpoint_url = os.getenv("S3_ENDPOINT_URL", "")
        self.s3_access_key_id = os.getenv("S3_ACCESS_KEY_ID", "")
        self.s3_secret_access_key = os.getenv("S3_SECRET_ACCESS_KEY", "")
        self.s3_region = os.getenv("S3_REGION", "auto")
        self.s3_bucket = os.getenv("S3_BUCKET", "")

        # --- App ---
        self.log_level = os.getenv("LOG_LEVEL", "info")


@lru_cache
def get_settings():
    """Cached accessor so settings are read once per process."""
    return Settings()
