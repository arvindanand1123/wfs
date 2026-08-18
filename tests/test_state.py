import io
from urllib.parse import parse_qs, urlparse

import httpx

from tests.externals import ExternalClient
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


def test_push_obj_uploads_a_file_like_without_buffering_it(client):
    Object("big.bin", io.BytesIO(b"payload")).push_obj()

    assert client.mock("s3").read("big.bin") == b"payload"


def test_push_obj_falls_back_to_a_binary_content_type(client):
    Object("README", b"no extension").push_obj()

    assert client.mock("s3").content_type("README") == DEFAULT_FILE_TYPE


def test_each_client_gets_an_empty_bucket(client):
    Object("hello.txt", b"hi there").push_obj()
    assert client.mock("s3").keys() == ["hello.txt"]

    with ExternalClient() as second:
        assert second.mock("s3").keys() == []


def test_get_upload_url_serves_the_object_over_http(client):
    obj = Object("hello.txt", b"hi there")
    obj.push_obj()

    resp = httpx.get(obj.get_upload_url())

    assert resp.status_code == 200
    assert resp.content == b"hi there"


def test_get_upload_url_is_signed_with_sigv4_and_the_given_expiry(client):
    url = Object("hello.txt", b"").get_upload_url(expires_in=60)

    query = parse_qs(urlparse(url).query)
    assert query["X-Amz-Algorithm"] == ["AWS4-HMAC-SHA256"]
    assert query["X-Amz-Expires"] == ["60"]
