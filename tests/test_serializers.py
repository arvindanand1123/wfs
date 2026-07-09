import pytest

from tests.utils.time import TimeUtils
from wfs.models.serializers import F, ObjectSerializer, ValidationError


def test_null():
    assert F.string(null=True).deserialize(None) is None
    with pytest.raises(ValidationError):
        F.string().deserialize(None)


def test_default():
    d = F.dict(tags=F.array(F.string(), default=list))
    assert d.deserialize(dict()) == dict(tags=[])


def test_read_only():
    d = F.dict(name=F.string(), etag=F.string(read_only=True))
    assert d.deserialize(dict(name="x", etag="abc")) == dict(name="x")


def test_write_only():
    d = F.dict(name=F.string(), secret=F.string(write_only=True))
    assert d.serialize(dict(name="x", secret="shh")) == dict(name="x")


def test_string():
    s = F.string()
    assert s.serialize("hi") == "hi"
    assert s.deserialize("hi") == "hi"

    assert s.serialize(1) == "1"
    with pytest.raises(ValidationError):
        F.string().deserialize(1)


def test_integer():
    i = F.integer()
    assert i.serialize(1) == 1
    assert i.deserialize(1) == 1

    assert i.serialize("1") == 1
    with pytest.raises(ValidationError):
        F.integer().deserialize(True)


def test_float():
    f = F.float()
    assert f.serialize(1.1) == 1.1
    assert f.deserialize(1.1) == 1.1

    assert f.deserialize(1) == 1.0
    with pytest.raises(ValidationError):
        F.float().deserialize(True)


def test_boolean():
    b = F.boolean()
    assert b.deserialize("true") is True
    assert b.deserialize("No") is False
    assert b.deserialize(1) is True
    assert b.deserialize(0) is False
    assert b.deserialize(True) is True
    with pytest.raises(ValidationError):
        b.deserialize("maybe")


def test_array():
    a = F.array(F.string())
    assert a.deserialize(["a", "b"]) == ["a", "b"]
    with pytest.raises(ValidationError):
        a.deserialize(["a", 1])


def test_dict():
    d = F.dict(name=F.string(), nick=F.string(null=True, required=False))
    assert d.deserialize(dict(name="x")) == dict(name="x", nick=None)
    with pytest.raises(ValidationError):
        d.deserialize(dict())


def test_dict_nested():
    d = F.dict(meta=F.dict(etag=F.string(null=True)))
    assert d.deserialize(dict(meta=dict(etag=None))) == dict(meta=dict(etag=None))


def test_serialize_reads_object():
    class Obj:
        key = "a.txt"
        size = 3

    d = F.dict(key=F.string(), size=F.integer())
    assert d.serialize(Obj()) == dict(key="a.txt", size=3)


def test_non_base_serializer():
    o = ObjectSerializer()
    now = TimeUtils.now(as_string=True)
    data = dict(key="a", size=0, etag="b", last_modified=now)

    assert o.deserialize(data) == dict(key="a", size=0)
    assert o.serialize(data) == dict(key="a", size=0, etag="b", last_modified=now)
