class ExternalMock:
    name = ""

    def register(self, client):
        raise NotImplementedError

    def unregister(self):
        pass
