from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa

from tests.utils.auth import AuthUtils
from wfs.config import get_settings
from wfs.models.state import get_keypair


def other_public_key():
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    return key.public_key().public_bytes(serialization.Encoding.PEM, serialization.PublicFormat.SubjectPublicKeyInfo)


def test_keys_are_generated_on_startup(client, public_key):
    assert public_key.startswith(b"-----BEGIN PUBLIC KEY-----")
    assert client.mock("s3").read(get_settings().private_key_name).startswith(b"-----BEGIN PRIVATE KEY-----")


def test_login_issues_a_token(client, public_key):
    resp = client.post("/login", headers=AuthUtils.bearer(public_key))

    assert resp.status_code == 200
    assert resp.json()["token_type"] == "bearer"
    assert resp.json()["expires_in"] == get_settings().jwt_ttl
    assert resp.json()["access_token"]


def test_login_rejects_an_unknown_key(client):
    resp = client.post("/login", headers=AuthUtils.bearer(other_public_key()))

    assert resp.status_code == 401


def test_login_requires_credentials(client):
    assert client.post("/login").status_code == 401


def test_restart_reuses_stored_keys(client, public_key, token):
    get_keypair.cache_clear()

    assert client.mock("s3").read(get_settings().public_key_name) == public_key
    assert client.get("/files/get-signed-url", params=dict(filename="a.txt"), headers=AuthUtils.bearer(token)).status_code == 200
