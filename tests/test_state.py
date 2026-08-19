import io
from urllib.parse import parse_qs, urlparse

import httpx

from wfs.models.state import DEFAULT_FILE_TYPE, Object


def test_file_type():
    assert Object("a/b/report.pdf", b"").file_type == "application/pdf"


def test_unknown_file_type():
    assert Object("blob.q", b"").file_type == DEFAULT_FILE_TYPE


def test_explicit_file_type():
    assert Object("data.txt", b"", file_type="application/json").file_type == "application/json"


def test_push_obj(client):
    Object("hello.txt", b"hi there").push_obj()

    s3 = client.mock("s3")
    assert s3.read("hello.txt") == b"hi there"
    assert s3.content_type("hello.txt") == "text/plain"


def test_push_obj_no_buffering(client):
    Object("big.bin", io.BytesIO(b"payload")).push_obj()

    assert client.mock("s3").read("big.bin") == b"payload"


def test_push_obj_binary_type(client):
    Object("README", b"no extension").push_obj()

    assert client.mock("s3").content_type("README") == DEFAULT_FILE_TYPE


def test_get_upload_url(client):
    obj = Object("hello.txt", b"hi there")
    obj.push_obj()

    url = obj.get_upload_url()
    query = parse_qs(urlparse(url).query)
    assert query["X-Amz-Algorithm"] == ["AWS4-HMAC-SHA256"]

    resp = httpx.get(url)

    assert resp.status_code == 200
    assert resp.content == b"hi there"


def test_get_upload_url_expiry(client):
    url = Object("hello.txt", b"").get_upload_url(expires_in=60)

    query = parse_qs(urlparse(url).query)
    assert query["X-Amz-Expires"] == ["60"]
