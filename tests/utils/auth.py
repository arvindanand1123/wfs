class AuthUtils:
    @classmethod
    def bearer(cls, credential):
        if isinstance(credential, bytes):
            credential = credential.decode()
        # An HTTP header cannot carry the newlines a PEM is written with, so a
        # real client has to flatten it the way this does.
        return dict(Authorization=f"Bearer {' '.join(credential.split())}")
