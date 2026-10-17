import base64
import hashlib
import hmac
from datetime import UTC, datetime, timedelta
from functools import cache

import jwt
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from wfs.config import get_settings
from wfs.models.state.objects import Object

JWT_ALGORITHM = "RS256"

KEY_SIZE = 2048

PEM_FILE_TYPE = "application/x-pem-file"

PEM_MARKERS = ("-----BEGIN PUBLIC KEY-----", "-----END PUBLIC KEY-----", "-----BEGIN RSA PUBLIC KEY-----", "-----END RSA PUBLIC KEY-----")


class AuthError(Exception):
    """Base class for authentication failures."""


class UnknownKeyError(AuthError):
    """Raised when a presented public key is not the one this container issues for."""


class InvalidTokenError(AuthError):
    """Raised when a bearer token is missing, malformed, or expired."""


def public_key_der(value):
    """Return the DER encoding of a presented public key, or None if it is not one.

    Accepts a PEM, a base64-wrapped PEM, or a bare base64 body: an HTTP header
    cannot carry the newlines a PEM is normally written with, so clients have to
    mangle it somehow to send it as a bearer credential.
    """
    if isinstance(value, str):
        value = value.encode()
    for candidate in _key_candidates(value.strip()):
        for load in (serialization.load_pem_public_key, serialization.load_der_public_key):
            try:
                key = load(candidate)
            except Exception:
                continue
            return key.public_bytes(serialization.Encoding.DER, serialization.PublicFormat.SubjectPublicKeyInfo)
    return None


def _key_candidates(value):
    yield value
    body = value.decode("utf-8", "ignore")
    for marker in PEM_MARKERS:
        body = body.replace(marker, "")
    body = "".join(body.split())
    try:
        yield base64.b64decode(body, validate=True)
    except (ValueError, base64.binascii.Error):
        return


class KeyPair:
    def __init__(self, private_pem, public_pem):
        self.private_pem = private_pem
        self.public_pem = public_pem

    @classmethod
    def ensure(cls):
        settings = get_settings()
        private = Object(settings.private_key_name, file_type=PEM_FILE_TYPE)
        public = Object(settings.public_key_name, file_type=PEM_FILE_TYPE)
        if not (private.exists() and public.exists()):
            private_pem, public_pem = cls.generate()
            Object(settings.private_key_name, private_pem, file_type=PEM_FILE_TYPE).push_obj()
            Object(settings.public_key_name, public_pem, file_type=PEM_FILE_TYPE).push_obj()
        # Read back rather than trusting what was just written: two containers
        # booting at once both generate, and only the last write survives.
        return cls(private.pull_obj(), public.pull_obj())

    @staticmethod
    def generate():
        key = rsa.generate_private_key(public_exponent=65537, key_size=KEY_SIZE)
        private_pem = key.private_bytes(
            serialization.Encoding.PEM,
            serialization.PrivateFormat.PKCS8,
            serialization.NoEncryption(),
        )
        public_pem = key.public_key().public_bytes(
            serialization.Encoding.PEM,
            serialization.PublicFormat.SubjectPublicKeyInfo,
        )
        return private_pem, public_pem

    @property
    def der(self):
        return public_key_der(self.public_pem)

    @property
    def fingerprint(self):
        return hashlib.sha256(self.der).hexdigest()

    def matches(self, presented):
        der = public_key_der(presented)
        return der is not None and hmac.compare_digest(der, self.der)

    def issue_token(self, presented):
        if not self.matches(presented):
            raise UnknownKeyError("public key is not recognized by this container")
        settings = get_settings()
        issued_at = datetime.now(UTC)
        expires_at = issued_at + timedelta(seconds=settings.jwt_ttl)
        claims = dict(
            iss=settings.jwt_issuer,
            sub=self.fingerprint,
            iat=issued_at,
            exp=expires_at,
        )
        token = jwt.encode(claims, self.private_pem, algorithm=JWT_ALGORITHM)
        return token, settings.jwt_ttl

    def verify_token(self, token):
        settings = get_settings()
        try:
            return jwt.decode(
                token,
                self.public_pem,
                algorithms=[JWT_ALGORITHM],
                issuer=settings.jwt_issuer,
                options=dict(require=["exp", "iat", "iss", "sub"]),
            )
        except jwt.PyJWTError as e:
            raise InvalidTokenError(str(e)) from e


@cache
def get_keypair():
    return KeyPair.ensure()
