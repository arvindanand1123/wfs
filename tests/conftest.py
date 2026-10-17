import pytest

from tests.externals.client import ExternalClient
from tests.utils.auth import AuthUtils
from wfs.config import get_settings


@pytest.fixture
def client():
    # A returned fixture has no teardown phase, so the mocks' os.environ patch
    # would never be reverted and would follow every later test in the process.
    with ExternalClient() as external_client:
        yield external_client


@pytest.fixture
def public_key(client):
    return client.mock("s3").read(get_settings().public_key_name)


@pytest.fixture
def token(client, public_key):
    return client.post("/login", headers=AuthUtils.bearer(public_key)).json()["access_token"]
