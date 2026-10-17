from urllib.parse import parse_qs, urlparse

import httpx

from tests.utils.auth import AuthUtils
from wfs.controllers.files import MAX_URL_EXPIRY


def signed_url(client, token, filename, **params):
    return client.get("/files/get-signed-url", params=dict(filename=filename, **params), headers=AuthUtils.bearer(token))


def test_signed_url_round_trip(client, token):
    upload = signed_url(client, token, "hello.txt", method="put").json()
    assert upload["method"] == "PUT"
    assert httpx.put(upload["url"], content=b"hi there").status_code == 200
    assert client.mock("s3").read("hello.txt") == b"hi there"

    download = signed_url(client, token, "hello.txt").json()
    assert download["method"] == "GET"
    assert httpx.get(download["url"]).content == b"hi there"


def test_signed_url_expiry(client, token):
    body = signed_url(client, token, "hello.txt", expires_in=60).json()

    assert body["expires_in"] == 60
    assert parse_qs(urlparse(body["url"]).query)["X-Amz-Expires"] == ["60"]


def test_rejects_an_unsupported_method(client, token):
    assert signed_url(client, token, "hello.txt", method="delete").status_code == 422


def test_rejects_an_out_of_range_expiry(client, token):
    assert signed_url(client, token, "hello.txt", expires_in=MAX_URL_EXPIRY + 1).status_code == 422


def test_rejects_an_empty_filename(client, token):
    assert signed_url(client, token, " ").status_code == 422


def test_requires_a_valid_token(client, public_key):
    assert client.get("/files/get-signed-url", params=dict(filename="a.txt")).status_code == 401
    assert signed_url(client, "not-a-token", "a.txt").status_code == 401
    assert signed_url(client, public_key, "a.txt").status_code == 401
