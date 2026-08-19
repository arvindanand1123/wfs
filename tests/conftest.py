import pytest

from tests.externals.client import ExternalClient


@pytest.fixture
def client():
    # A returned fixture has no teardown phase, so the mocks' os.environ patch
    # would never be reverted and would follow every later test in the process.
    with ExternalClient() as external_client:
        yield external_client
