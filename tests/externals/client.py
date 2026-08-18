import inspect
from functools import partial

from fastapi.testclient import TestClient

from tests.externals.s3 import S3Mock
from wfs.main import create_app

REGISTERED_MOCKS = [S3Mock]


class ExternalClient(TestClient):
    def __init__(self, app=None, **kwargs):
        self.mocks = self.setup_mocks()
        app = create_app if app is None else app
        # An ASGI app is itself callable, so callable() cannot tell a built app
        # from a factory.
        if inspect.isroutine(app) or isinstance(app, partial):
            app = app()
        super().__init__(app, **kwargs)

    def setup_mocks(self):
        mocks = dict()
        for mock_cls in REGISTERED_MOCKS:
            instance = mock_cls()
            instance.register(self)
            mocks[instance.name] = instance
        return mocks

    def teardown_mocks(self):
        for instance in reversed(list(self.mocks.values())):
            instance.unregister()
        self.mocks = dict()

    def mock(self, name):
        return self.mocks[name]

    # TestClient.__exit__ overrides httpx's and never calls close(), so both
    # teardown paths have to be hooked separately.

    def __exit__(self, *args):
        try:
            return super().__exit__(*args)
        finally:
            self.teardown_mocks()

    def close(self):
        try:
            super().close()
        finally:
            self.teardown_mocks()
